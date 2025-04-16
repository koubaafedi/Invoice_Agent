import streamlit as st
import os
import json
from tools import load_data, create_invoice_graph

# Constants
history_file = 'history.json'

# Configure the Streamlit page
st.set_page_config(
    page_title="Assistant de Requêtes de Factures",
    page_icon="📊",
    layout="wide"
)

# Initialize history.json if it doesn't exist
if not os.path.exists(history_file):
    with open(history_file, 'w') as file:
        db = {'chat_history': []}
        json.dump(db, file)

# Cache the data loading function
@st.cache_data
def cached_load_data():
    return load_data()

# Load the invoice data
with st.spinner("Loading invoice data..."):
    invoice_df = cached_load_data()

# Create the LangGraph inference pipeline
graph = create_invoice_graph(invoice_df)

# Add a clear chat button to the sidebar
st.sidebar.title("Options")
if st.sidebar.button('Effacer la conversation'):
    # Clear chat history in history.json
    with open(history_file, 'r') as file:
        db = json.load(file)
    db['chat_history'] = []
    with open(history_file, 'w') as file:
        json.dump(db, file)
    # Clear chat messages in session state
    if 'messages' in st.session_state:
        st.session_state.messages = []
    st.rerun()

# Initialize or load chat history
if "messages" not in st.session_state:
    # Load chat history from history.json
    with open(history_file, 'r') as file:
        db = json.load(file)
    st.session_state.messages = db.get('chat_history', [])

# Display a small header
st.header("Assistant de Requêtes de Factures")

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
user_query = st.chat_input("Posez une question sur les factures...")

# Process the user query
if user_query:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # Process and display assistant response with loading spinner
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Run the question through the graph
        result = None
        for step in graph.stream(
            {"question": user_query}, stream_mode="updates"
        ):
            if "answer_based_on_info" in step and "answer" in step["answer_based_on_info"]:
                result = step["answer_based_on_info"]["answer"]
                # Could display partial results here if needed
        
        # Display the final response
        message_placeholder.markdown(result)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": result})
    
    # Save chat history to history.json
    with open(history_file, 'r') as file:
        db = json.load(file)
    db['chat_history'] = st.session_state.messages
    with open(history_file, 'w') as file:
        json.dump(db, file)
