import streamlit as st
import os
import json
from tools import load_data, InvoiceAssistant

# Constants - use absolute path
history_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'chat_history.json')

# Configure the Streamlit page
st.set_page_config(
    page_title="Assistant de Factures et Commandes",
    page_icon="📊",
    layout="centered"
)

# Initialize chat history file if it doesn't exist
if not os.path.exists(history_file):
    # Ensure directory exists
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    with open(history_file, 'w') as file:
        json.dump({"interactions": []}, file)

# Cache the data loading function
@st.cache_data
def cached_load_data():
    return load_data()

# Load the data
with st.spinner("Chargement des données de factures et commandes..."):
    invoice_df, order_df = cached_load_data()

# Initialize chat instance in session state if not already there
if "chat_instance" not in st.session_state:
    st.session_state.chat_instance = InvoiceAssistant(invoice_df, order_df)

# Initialize toggle state in session state if not already there
if "toggle_states" not in st.session_state:
    st.session_state.toggle_states = {}

# Sidebar options
st.sidebar.title("Options")

# Add a clear chat button
if st.sidebar.button('Effacer la conversation'):
    # Clear the chat history
    with open(history_file, 'w') as file:
        json.dump({"interactions": []}, file)
    
    # Reset the chat instance
    st.session_state.chat_instance = InvoiceAssistant(invoice_df, order_df)
    # Reset toggle states
    st.session_state.toggle_states = {}
    st.rerun()

# Display a small header
st.header("Assistant de Factures et Commandes")

# Display chat messages from history
with open(history_file, 'r') as file:
    data = json.load(file)
    interactions = data.get('interactions', [])

# Display each interaction (user query + assistant response)
for i, interaction in enumerate(interactions):
    # Display user message
    with st.chat_message("user"):
        st.markdown(interaction["user_query"])
    
    # Display assistant message
    with st.chat_message("assistant"):
        st.markdown(interaction["assistant_response"])
        
        # Add toggle button for pipeline details
        toggle_key = f"toggle_{i}"
        if toggle_key not in st.session_state.toggle_states:
            st.session_state.toggle_states[toggle_key] = False
        
        if st.button("Afficher/Masquer détails du pipeline", key=f"button_{i}"):
            st.session_state.toggle_states[toggle_key] = not st.session_state.toggle_states[toggle_key]
        
        # Show pipeline details if toggled
        if st.session_state.toggle_states[toggle_key]:
            with st.expander("Détails du pipeline", expanded=True):
                st.subheader("Prompt d'extraction")
                st.code(interaction["extract_prompt"], language="text")
                
                st.subheader("Résultat de l'extraction")
                st.code(interaction["ids_result"], language="text")
                
                st.subheader("Informations extraites")
                st.code(interaction["combined_info"], language="text")
                
                st.subheader("Prompt de réponse")
                st.code(interaction["answer_prompt"], language="text")

# Get user input
user_query = st.chat_input("Posez une question sur les factures ou les commandes...")

# Process the user query
if user_query:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # Process and display assistant response with streaming
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        pipeline_details = {}
        
        # Process the question through the system with streaming
        for chunk_data in st.session_state.chat_instance.process_query_with_stream(user_query):
            if isinstance(chunk_data, tuple) and len(chunk_data) == 2:
                chunk, details = chunk_data
                pipeline_details = details
            else:
                chunk = chunk_data  # Fallback for backward compatibility
                
            if chunk:
                full_response += chunk
                message_placeholder.markdown(full_response + " ")
        
        # Display the final response
        message_placeholder.markdown(full_response)
    
    # Add the complete interaction to chat history
    with open(history_file, 'r') as file:
        data = json.load(file)
    
    # Create a new interaction entry with all pipeline details
    new_interaction = {
        "user_query": user_query,
        "extract_prompt": pipeline_details.get("extract_prompt", ""),
        "ids_result": pipeline_details.get("ids_result", ""),
        "combined_info": pipeline_details.get("combined_info", ""),
        "answer_prompt": pipeline_details.get("answer_prompt", ""),
        "assistant_response": full_response
    }
    
    # Add the new interaction to the history
    data['interactions'].append(new_interaction)
    
    with open(history_file, 'w') as file:
        json.dump(data, file)
    
    # Add a new toggle state for this interaction
    new_toggle_key = f"toggle_{len(data['interactions']) - 1}"
    st.session_state.toggle_states[new_toggle_key] = False
    
    st.rerun()
