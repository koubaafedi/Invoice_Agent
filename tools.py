import pandas as pd
import re
import os
from dotenv import load_dotenv
from typing_extensions import TypedDict
from langgraph.graph import START, StateGraph
from google import genai

# Initialize Google Gemini client
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def load_data():
    return pd.read_csv('invoice_dataset.csv')

def generate(prompt):
    model_name = "gemini-2.0-flash"
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    return response.text.rstrip()

class State(TypedDict):
    question: str
    invoice_ids: str
    invoice_info: str
    answer: str

def extract_invoice_ids(state: State):
    prompt = f"""
    Vous êtes un assistant serviable conçu pour extraire les numéros de facture des questions de l'utilisateur.
    Veuillez extraire tous les numéros de facture mentionnés dans la question suivante, même s'ils sont mentionnés de manière informelle ou contiennent des erreurs de frappe.
    Les numéros de facture commencent par 'FAC-' suivi de quatre chiffres, et sont compris entre FAC-0001 et FAC-1000.
    Si une plage de factures est mentionnée  veuillez extraire tous les numéros de facture pertinents, 
    Par exemple:
        - "les 5 premières factures" doit retourner 'FAC-0001,FAC-0002,FAC-0003,FAC-0004,FAC-0005'
        - "les 5 dernières factures" doit retourner 'FAC-0996,FAC-0997,FAC-0998,FAC-0999,FAC-1000'
    Si plusieurs numéros de facture sont présents, séparez-les par des virgules.
    Si aucun numéro de facture n'est trouvé, veuillez répondre par 'AUCUN'.
    N'incluez aucune description ou contexte supplémentaire.

    Question: {state['question']}
    """
    return {"invoice_ids": generate(prompt)}

def get_invoice_information(state: State, invoice_df):
    invoice_ids_str = state["invoice_ids"]
    if invoice_ids_str.upper() == "AUCUN":
        return {"invoice_info": "Aucun numéro de facture trouvé dans la question."}
    else:
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
        
        return {"invoice_info": prompt_injection}

def answer_based_on_info(state: State):
    question = state["question"]
    invoice_info = state["invoice_info"]
    prompt = f"""
    Vous êtes un assistant IA expert en analyse de factures. Votre rôle est de répondre aux questions posées sur les factures, en utilisant exclusivement les données fournies.

    **Question:** {question}

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
    Si une date est demandée, donnez la dans un format clair, comme le jour/mois/année.
    """
    return {'answer': generate(prompt)}

# Build and return the LangGraph 
def create_invoice_graph(invoice_df):
    def get_invoice_info_with_df(state: State):
        return get_invoice_information(state, invoice_df)
    
    # Create and compile the graph
    graph_builder = StateGraph(State).add_sequence(
        [extract_invoice_ids, get_invoice_info_with_df, answer_based_on_info]
    )
    graph_builder.add_edge(START, "extract_invoice_ids")
    return graph_builder.compile()
