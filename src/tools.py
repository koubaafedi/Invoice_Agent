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
    # Use an absolute path that works in Docker
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    invoice_path = os.path.join(base_path, 'data', 'invoice_dataset.csv')
    order_path = os.path.join(base_path, 'data', 'order_dataset.csv')
    
    invoice_df = pd.read_csv(invoice_path)
    order_df = pd.read_csv(order_path)
    
    return invoice_df, order_df

def extract_ids_prompt(question, previous_invoice_ids, previous_order_ids):
    previous_context_instruction = ""
    if previous_invoice_ids or previous_order_ids:
        previous_info = []
        if previous_invoice_ids:
            previous_info.append(f"factures : '{previous_invoice_ids}'")
        if previous_order_ids:
            previous_info.append(f"commandes : '{previous_order_ids}'")
            
        previous_context = ", ".join(previous_info)
        
        previous_context_instruction = f"""Sachant que vous avez précédemment identifié les numéros suivants : {previous_context}.
Si la question actuelle se réfère à ces mêmes éléments, et qu'aucun nouveau numéro n'est explicitement mentionné, veuillez répondre par le mot clé 'CONTINUER'.
Signaux de nouvelle requête (non exhaustif):
- Mention explicite de 'nouvelle facture', 'autre facture', 'nouvelle commande', 'autre commande'.
- Présence d'un format de numéro différent.
- Question clairement hors du contexte des items précédents."""

    return f"""Veuillez extraire tous les numéros de facture ('FAC-' suivi de quatre chiffres, entre FAC-0001 et FAC-1000) 
ET/OU tous les numéros de commande ('COM-' suivi de quatre chiffres, entre COM-0001 et COM-1000) mentionnés dans cette question: "{question}".
Gérez les mentions informelles et les erreurs de frappe.
Si une plage est indiquée, extrayez tous les numéros pertinents.

Format de sortie JSON (sans autres explications):
{{
  "invoices": ["FAC-XXXX", "FAC-YYYY"] ou [] si aucune facture,
  "orders": ["COM-XXXX", "COM-YYYY"] ou [] si aucune commande,
  "continue": true ou false (true seulement si la question se réfère aux items précédents sans en mentionner de nouveaux)
}}

Exemples d'extraction:
- 'la première facture' -> {{"invoices": ["FAC-0001"], "orders": [], "continue": false}}
- 'la première commande' -> {{"invoices": [], "orders": ["COM-0001"], "continue": false}}
- 'montant de la facture FAC-0001 et commande COM-0001' -> {{"invoices": ["FAC-0001"], "orders": ["COM-0001"], "continue": false}}
- 'détails sur la facture précédente' (avec contexte précédent) -> {{"invoices": [], "orders": [], "continue": true}}
{previous_context_instruction}"""

def get_invoice_information(invoice_ids, invoice_df):
    prompt_injection = ""
    
    for key in invoice_ids:
        matching_invoice = invoice_df[invoice_df["Numéro de Facture"].str.upper() == key.upper()]
        
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

def get_order_information(order_ids, order_df):
    prompt_injection = ""
    
    for key in order_ids:
        matching_order = order_df[order_df["Numéro de Commande"].str.upper() == key.upper()]
        
        if not matching_order.empty:
            prompt_injection += f"Données de commande numéro: {key} \n"
            for column, value in matching_order.iloc[0].items():
                if column == "Numéro de Commande":
                    continue
                if pd.notna(value):
                    prompt_injection += f"  {column}: {value}\n"
        else:
            prompt_injection += f"Avertissement : Le numéro de commande '{key}' n'a pas été trouvé.\n"
    
    return prompt_injection

def answer_based_on_info_prompt(question, combined_info):    
    return f"""Vous êtes un assistant IA expert en analyse de factures et de commandes. Votre rôle est de répondre aux questions posées, en utilisant exclusivement les données fournies.
**Question:** 
{question}
**Données Fournies:**
{combined_info}

Répondez à la question de manière très concise et précise, en utilisant uniquement les données fournies ci-dessus.
N'utilisez aucune connaissance externe et ne faites pas d'hypothèses.
Si la question nécessite des calculs, assurez-vous d'être précis et présentez les étapes importantes clairement.

Informations sur les factures:
- Statuts de paiement : ["Payé", "Non Payé", "En Retard", "Partiellement Payé"]  
- Modes de paiement : ["Carte de Crédit", "Virement Bancaire", "Chèque", "Espèces", "PayPal"]  
- Les champs "Date de Paiement" et "Mode de Paiement" sont renseignés uniquement si le statut est "Payé".  

Informations sur les commandes:
- Statuts de commande : ["Livré", "En cours", "En attente", "Annulé"]
- Modes d'expédition : ["Standard", "Express", "Premium", "Économique"]
- Les champs "Date de Livraison" sont renseignés uniquement si le statut n'est pas "Annulé".

Notez que chaque commande (COM-XXXX) est associée à une facture (FAC-XXXX) avec le même numéro (par exemple, COM-0001 correspond à FAC-0001).

Si ces champs sont absents, cela signifie que le paiement ou la livraison n'est pas finalisé.
Ne dites jamais que les données sont insuffisantes. Indiquez simplement que le paiement ou la livraison n'est pas encore finalisé.
Si une date est demandée, donnez la dans un format clair, comme le jour/mois/année."""

# Modified invoice and order assistant implementation with multi-turn chat and streaming
class InvoiceAssistant:
    def __init__(self, invoice_df, order_df):
        self.invoice_df = invoice_df
        self.order_df = order_df
        self.chat = client.chats.create(model="gemini-2.0-flash")
        self.session_id = str(uuid.uuid4())
        
        # Context tracking
        self.current_invoice_ids = []
        self.current_order_ids = []
        
        # Send initial system context to set up the assistant's role
        system_prompt = """Vous êtes un assistant IA expert en analyse de factures et commandes d'entreprise.
Votre rôle est d'aider l'utilisateur à obtenir des informations précises sur les factures et les commandes,
en utilisant exclusivement les données fournies par le système.

Vous pouvez répondre à des questions concernant:
- Les détails spécifiques d'une facture ou d'une commande (montant, date, statut, etc.)
- Les relations entre factures et commandes (chaque facture FAC-XXXX a une commande associée COM-XXXX)
- Les comparaisons entre plusieurs factures/commandes
- Les calculs simples sur les données fournies

Utilisez uniquement les données fournies et restez factuel. N'utilisez aucune connaissance externe et ne faites pas d'hypothèses.
Soyez concis et précis dans vos réponses.

Informations sur les factures:
- Statuts de paiement valides : "Payé", "Non Payé", "En Retard", "Partiellement Payé".
- Modes de paiement valides : "Carte de Crédit", "Virement Bancaire", "Chèque", "Espèces", "PayPal".

Informations sur les commandes:
- Statuts de commande : "Livré", "En cours", "En attente", "Annulé"
- Modes d'expédition : "Standard", "Express", "Premium", "Économique"

Si des informations comme la date ou le mode de paiement/livraison ne sont pas fournies, cela signifie que le processus n'est pas encore finalisé.
Ne dites jamais que les données sont insuffisantes. Indiquez simplement que le paiement ou la livraison n'est pas encore finalisé.
Si une date est demandée, donnez la dans un format clair, comme le jour/mois/année."""
        init_response = self.chat.send_message(system_prompt)
    
    def process_query_with_stream(self, question):
        # Extract IDs (both invoice and order)
        extract_prompt = extract_ids_prompt(question, 
                                            ','.join(self.current_invoice_ids) if self.current_invoice_ids else None,
                                            ','.join(self.current_order_ids) if self.current_order_ids else None)
        ids_response = self.chat.send_message(extract_prompt).text.strip()
        
        try:
            # Parse the JSON response
            import json
            ids_result = json.loads(ids_response)
            
            invoice_ids = ids_result.get('invoices', [])
            order_ids = ids_result.get('orders', [])
            continue_previous = ids_result.get('continue', False)
            
            # Handle continuation with previous context
            if continue_previous and (self.current_invoice_ids or self.current_order_ids):
                invoice_ids = self.current_invoice_ids
                order_ids = self.current_order_ids
            else:
                # Update current context
                self.current_invoice_ids = invoice_ids
                self.current_order_ids = order_ids
                
            # Get information for both invoice and order IDs
            invoice_info = get_invoice_information(invoice_ids, self.invoice_df) if invoice_ids else ""
            order_info = get_order_information(order_ids, self.order_df) if order_ids else ""
            
            # If neither invoice nor order info was found, provide a default message
            if not invoice_info and not order_info:
                combined_info = "Aucun numéro de facture ou de commande trouvé dans la question."
                if continue_previous:
                    combined_info = "Pas de contexte précédent disponible."
            else:
                combined_info = invoice_info + "\n" + order_info if invoice_info and order_info else invoice_info or order_info
            
        except Exception as e:
            # Handle parsing errors
            invoice_ids = []
            order_ids = []
            combined_info = f"Erreur lors de l'extraction des numéros: {str(e)}"
        
        # Prepare the answer prompt
        answer_prompt = answer_based_on_info_prompt(question, combined_info)
        
        # Send the message to the Gemini chat with streaming
        response_stream = self.chat.send_message_stream(answer_prompt)
        
        # Store pipeline details
        pipeline_details = {
            "extract_prompt": extract_prompt,
            "ids_result": ids_response,
            "combined_info": combined_info,
            "answer_prompt": answer_prompt
        }
        
        full_response = ""
        # Yield chunks of text as they become available
        for chunk in response_stream:
            if chunk.text:
                full_response += chunk.text
                yield chunk.text, pipeline_details
