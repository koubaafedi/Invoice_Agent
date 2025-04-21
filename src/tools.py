import pandas as pd
import re
import os
from dotenv import load_dotenv
from google import genai
import uuid

# Load environment variables
load_dotenv()

# Initialize Google Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def load_data():
    return pd.read_csv('../data/invoice_dataset.csv')

def extract_invoice_ids_prompt(question, previous_invoice_ids):
    previous_context_instruction = ""
    if previous_invoice_ids:
        previous_context_instruction = f"""Sachant que vous avez précédemment identifié les numéros de facture suivants : '{previous_invoice_ids}'.
Si la question actuelle se réfère à ces mêmes factures, et qu'aucun nouveau numéro de facture n'est explicitement mentionné, veuillez répondre par le mot clé 'CONTINUER'.
Signaux de nouvelle requête (non exhaustif):
- Mention explicite de 'nouvelle facture', 'autre facture'.
- Présence d'un format de numéro de facture différent.
- Question clairement hors du contexte des factures précédentes."""

    return f"""Veuillez extraire tous les numéros de facture ('FAC-' suivi de quatre chiffres, entre FAC-0001 et FAC-1000) mentionnés dans ce question: "{question}".
Gérez les mentions informelles et les erreurs de frappe.
Si une plage est indiquée, extrayez tous les numéros pertinents.
Format de sortie:
- Nouveaux numéros: 'FAC-XXXX,FAC-YYYY'. 
- Aucun nouveau numéro trouvé et question se réfère aux précédentes: 'CONTINUER'
- Aucun numéro trouvé dans une nouvelle requête: 'AUCUN'
- N'incluez aucune description ou contexte supplémentaire.
Exemples d'extraction:
- 'la première facture' -> 'FAC-0001'
- 'la dernière facture' -> 'FAC-1000'
- "les 5 premières factures" -> 'FAC-0001,FAC-0002,FAC-0003,FAC-0004,FAC-0005'
- "les 5 dernières factures" -> 'FAC-0996,FAC-0997,FAC-0998,FAC-0999,FAC-1000'
- "montant de la facture FAC-0001 et FAC-0005" -> 'FAC-0001,FAC-0005'
{previous_context_instruction}"""

def get_invoice_information(invoice_ids_str, invoice_df):
    invoice_id_matches = re.findall(r'FAC-\d{4}', invoice_ids_str, re.IGNORECASE)
    clean_keys = [id.strip().upper() for id in invoice_id_matches]
    prompt_injection = ""
    
    for key in clean_keys:
        matching_invoice = invoice_df[invoice_df["Numéro de Facture"].str.upper() == key]
        
        if not matching_invoice.empty:
            prompt_injection += f"Données de facture numéro: {key} \n"
            for column, value in matching_invoice.iloc[0].items():
                if column == "Numéro de Facture":
                    continue
                if pd.notna(value):
                    prompt_injection += f"  {column}: {value}\n"
        else:
            prompt_injection += f"Avertissement : Le numéro de facture '{key}' n'a pas été trouvé.\n"
    
    return prompt_injection

def answer_based_on_info_prompt(question, invoice_info):
    return f"""Vous êtes un assistant IA expert en analyse de factures. Votre rôle est de répondre aux questions posées sur les factures, en utilisant exclusivement les données fournies.
**Question:** 
{question}
**Données Fournies:**
{invoice_info}

Répondez à la question de manière très concise et précise, en utilisant uniquement les données fournies ci-dessus.
N'utilisez aucune connaissance externe et ne faites pas d'hypothèses.
Si la question nécessite des calculs, assurez-vous d'être précis et présentez les étapes importantes clairement.
Statuts de paiement : ["Payé", "Non Payé", "En Retard", "Partiellement Payé"]  
Modes de paiement : ["Carte de Crédit", "Virement Bancaire", "Chèque", "Espèces", "PayPal"]  
Les champs "Date de Paiement" et "Mode de Paiement" sont renseignés uniquement si le statut est "Payé".  
Si ces champs sont absents, cela signifie que le paiement n'est pas finalisé.  
Ne dites jamais que les données sont insuffisantes. Indiquez simplement que le paiement n'est pas encore finalisé.
Si une date est demandée, donnez la dans un format clair, comme le jour/mois/année."""

# Modified invoice graph implementation with multi-turn chat and streaming
class InvoiceAssistant:
    def __init__(self, invoice_df):
        self.invoice_df = invoice_df
        self.chat = client.chats.create(model="gemini-2.0-flash")
        self.session_id = str(uuid.uuid4())
        
        # Send initial system context to set up the assistant's role
        system_prompt = """Vous êtes un assistant IA expert en analyse de factures d'entreprise.
Votre rôle est d'aider l'utilisateur à obtenir des informations précises sur les factures,
en utilisant exclusivement les données fournies par le système.

Vous pouvez répondre à des questions concernant:
- Les détails spécifiques d'une facture (montant, date, statut, etc.)
- Les comparaisons entre plusieurs factures
- Les calculs simples sur les données de factures

Utilisez uniquement les données fournies et restez factuel. N'utilisez aucune connaissance externe et ne faites pas d'hypothèses.
Soyez concis et précis dans vos réponses.
Statuts de paiement valides : "Payé", "Non Payé", "En Retard", "Partiellement Payé".
Modes de paiement valides : "Carte de Crédit", "Virement Bancaire", "Chèque", "Espèces", "PayPal".
Si le statut de paiement est "Payé", les informations sur la date et le mode de paiement peuvent être disponibles.
Si la date ou le mode de paiement ne sont pas fournis pour une facture, cela signifie que le paiement n'est pas encore finalisé.
Ne dites jamais que les données sont insuffisantes. Indiquez simplement que le paiement n'est pas encore finalisé.
Si une date est demandée, donnez la dans un format clair, comme le jour/mois/année.
Si la question nécessite des calculs, assurez-vous d'être précis et présentez les étapes importantes clairement."""
        init_response = self.chat.send_message(system_prompt)
        self.current_invoice_ids = None
    
    def process_query_with_stream(self, question):
        # Extract invoice IDs
        extract_prompt = extract_invoice_ids_prompt(question, self.current_invoice_ids)
        ids_result = self.chat.send_message(extract_prompt).text.rstrip()
        
        if ids_result.upper() == "CONTINUER" and self.current_invoice_ids:
            invoice_info = get_invoice_information(self.current_invoice_ids, self.invoice_df)
        elif ids_result.upper() == "AUCUN":
            self.current_invoice_ids = None
            invoice_info = "Aucun numéro de facture trouvé dans la question."
        else:
            self.current_invoice_ids = ids_result
            invoice_info = get_invoice_information(ids_result, self.invoice_df)
        # Prepare the answer prompt
        answer_prompt = answer_based_on_info_prompt(question, invoice_info)
        
        # Send the message to the Gemini chat with streaming
        response_stream = self.chat.send_message_stream(answer_prompt)
        
        # Store pipeline details
        pipeline_details = {
            "extract_prompt": extract_prompt,
            "ids_result": ids_result,
            "invoice_info": invoice_info,
            "answer_prompt": answer_prompt
        }
        
        full_response = ""
        # Yield chunks of text as they become available
        for chunk in response_stream:
            if chunk.text:
                full_response += chunk.text
                yield chunk.text, pipeline_details
