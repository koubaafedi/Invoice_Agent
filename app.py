import streamlit as st
import os
import json
from tools import load_data, InvoiceAssistant
import pandas as pd

# Constants
history_file = 'chat_history.json'

# Configure the Streamlit page
st.set_page_config(
    page_title="Assistant de Factures",
    page_icon="📊",
    layout="centered"
)

# Initialize chat history file if it doesn't exist
if not os.path.exists(history_file):
    with open(history_file, 'w') as file:
        json.dump({"messages": []}, file)

# Cache the data loading function
@st.cache_data
def cached_load_data():
    return load_data()

# Load the invoice data
with st.spinner("Loading invoice data..."):
    invoice_df = cached_load_data()

# Initialize chat instance in session state if not already there
if "chat_instance" not in st.session_state:
    st.session_state.chat_instance = InvoiceAssistant(invoice_df)

# Initialize toggle state in session state if not already there
if "toggle_states" not in st.session_state:
    st.session_state.toggle_states = {}

# Sidebar options
st.sidebar.title("Options")

# Add a clear chat button
if st.sidebar.button('Effacer la conversation'):
    # Clear the chat history
    with open(history_file, 'w') as file:
        json.dump({"messages": []}, file)
    
    # Reset the chat instance
    st.session_state.chat_instance = InvoiceAssistant(invoice_df)
    # Reset toggle states
    st.session_state.toggle_states = {}
    st.rerun()

# Display a small header
st.header("Assistant de Factures")

# Display chat messages from history
with open(history_file, 'r') as file:
    data = json.load(file)
    messages = data.get('messages', [])

# Counter for message pairs
message_count = len(messages) // 2

for i in range(message_count):
    user_msg_idx = i * 2
    assistant_msg_idx = i * 2 + 1
    
    # Display user message
    if user_msg_idx < len(messages):
        with st.chat_message("user"):
            st.markdown(messages[user_msg_idx]["content"])
    
    # Display assistant message
    if assistant_msg_idx < len(messages):
        with st.chat_message("assistant"):
            st.markdown(messages[assistant_msg_idx]["content"])
            
            # Add toggle button for pipeline details
            toggle_key = f"toggle_{i}"
            if toggle_key not in st.session_state.toggle_states:
                st.session_state.toggle_states[toggle_key] = False
            
            if st.button("Afficher/Masquer détails du pipeline", key=f"button_{i}"):
                st.session_state.toggle_states[toggle_key] = not st.session_state.toggle_states[toggle_key]
            
            # Show pipeline details if toggled
            if st.session_state.toggle_states[toggle_key] and "pipeline_details" in messages[assistant_msg_idx]:
                details = messages[assistant_msg_idx]["pipeline_details"]
                with st.expander("Détails du pipeline", expanded=True):
                    st.subheader("Prompt d'extraction")
                    st.code(details["extract_prompt"], language="text")
                    
                    st.subheader("Résultat de l'extraction")
                    st.code(details["ids_result"], language="text")
                    
                    st.subheader("Informations sur la facture")
                    st.code(details["invoice_info"], language="text")
                    
                    st.subheader("Prompt de réponse")
                    st.code(details["answer_prompt"], language="text")

# Get user input
user_query = st.chat_input("Posez une question sur les factures...")

# Process the user query
if user_query:
    # Add user message to chat history
    with open(history_file, 'r') as file:
        data = json.load(file)
    
    data['messages'].append({
        "role": "user", 
        "content": user_query
    })
    
    with open(history_file, 'w') as file:
        json.dump(data, file)
    
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
    
    # Add assistant response to chat history
    with open(history_file, 'r') as file:
        data = json.load(file)
    
    data['messages'].append({
        "role": "assistant", 
        "content": full_response,
        "pipeline_details": pipeline_details
    })
    
    with open(history_file, 'w') as file:
        json.dump(data, file)
    
    # Add a new toggle state for this message
    new_toggle_key = f"toggle_{len(data['messages']) // 2 - 1}"
    st.session_state.toggle_states[new_toggle_key] = False
    
    st.rerun()
