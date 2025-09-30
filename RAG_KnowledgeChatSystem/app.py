import streamlit as st
from document_loader import load_document
from Text_processor import split_text
from Vector_store import create_faiss_index, retrive_relevant_docs
from RAG_Chain import get_chat_model, ask_chat_model
from config import API_KEY
import time

# Streamlit config
st.set_page_config(
    page_title="📚 Modular RAG Knowledge Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .chat-message { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex; flex-direction: column; }
    .chat-message.user { background-color: #2b313e; color: white; }
    .chat-message.assistant { background-color: #f0f2f6; color: black; }
    .chat-message .timestamp { font-size: 0.8rem; opacity: 0.7; margin-top: 0.5rem; }
    .stButton > button { background-color: #ff4b4b; color: white; border-radius: 0.5rem; border: none; padding: 0.5rem 1rem; font-weight: bold; }
    .stButton > button:hover { background-color: #ff3333; }
</style>
""", unsafe_allow_html=True)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "chat_model" not in st.session_state:
    st.session_state.chat_model = None

# Title
st.markdown("""
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="color: #ff4b4b; font-size: 3rem; margin-bottom: 0.5rem;">📚 Modular Learning Assistant</h1>
    <p style="font-size: 1.2rem; color: #666; margin-bottom: 2rem;">Your Intelligent Knowledge Base Assistant</p>
</div>
""", unsafe_allow_html=True)

# Sidebar for document upload
with st.sidebar:
    st.markdown("### 📁 Document Upload")
    st.markdown("Upload your documents to start chatting!")
    
    uploaded_files = st.file_uploader("Upload files", type=["pdf", "txt", "docx"], accept_multiple_files=True)
    
    if uploaded_files:
        st.success(f"📄 {len(uploaded_files)} document(s) uploaded")
        
        # Process documents
        if st.button("🚀 Process Documents", type="primary"):
            with st.spinner("Processing your documents..."):
                # Extract text
                all_texts = []
                for file in uploaded_files:
                    try:
                        text = load_document(file)
                        all_texts.append(text)
                    except Exception as e:
                        st.error(f"❌ Error reading {file.name}: {e}")
                
                # Split into chunks
                chunks = []
                for text in all_texts:
                    chunks.extend(split_text(text, chunk_size=1000, overlap=200))
                
                # Create FAISS index
                st.session_state.vectorstore = create_faiss_index(chunks)
                
                # Initialize chat model
                st.session_state.chat_model = get_chat_model(EURI_API_KEY)
                
                st.success("✅ Documents processed successfully!")
                st.balloons()

# Main chat interface
st.markdown("### 💬 Chat with Your Knowledge Documents")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        st.caption(message["timestamp"])

# Chat input
if prompt := st.chat_input("Ask about your knowledge documents..."):
    timestamp = time.strftime("%H:%M")
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "timestamp": timestamp
    })

    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(timestamp)

    if st.session_state.vectorstore and st.session_state.chat_model:
        with st.chat_message("assistant"):
            with st.spinner("🔍 Searching documents..."):
                # Retrieve relevant docs
                relevant_docs = retrive_relevant_docs(st.session_state.vectorstore, prompt)
                context = "\n\n".join([doc.page_content for doc in relevant_docs])

                system_prompt = f"""You are RAG based Knowledge model, an intelligent knowledge document assistant. 
Your role is to answer questions strictly based on the provided documents retrieved from the knowledge base. 

Guidelines:
1. Always ground your answers in the retrieved content. 
2. If the information is not available in the documents, clearly state: 
   "The provided documents do not contain information about this." 
3. Do not fabricate or hallucinate information beyond the context. 
4. Use concise, professional, and well-documented accurate language. 
5. If a user’s query could be interpreted in multiple ways, ask clarifying questions before answering. 
6. Do not provide medical advice beyond what is explicitly stated in the documents. 
7. If the documents contain conflicting information, summarize both sides neutrally. 

You must always prioritize factual accuracy and reliability based on the retrieved documents.


                Documents:
                {context}

                User Question: {prompt}

                Answer:"""

                response = ask_chat_model(st.session_state.chat_model, system_prompt)

            st.markdown(response)
            st.caption(timestamp)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": timestamp
            })
    else:
        with st.chat_message("assistant"):
            st.error("⚠️ Please upload and process documents first!")
            st.caption(timestamp)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>🤖 Powered by RAG & LangChain | 📚 Knowledge Document Intelligence</p>
</div>
""", unsafe_allow_html=True)
