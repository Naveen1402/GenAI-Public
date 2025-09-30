# frontend/app.py
import streamlit as st
from orchestrator import orchestrate_request
from agents.s3_ingest import upload_to_s3, build_faiss_index
import os

st.set_page_config(page_title="Teamcenter CoPilot", layout="wide")
st.title("Teamcenter CoPilot")

DEPARTMENTS = ["Admin", "Development", "Engineering", "Quality"]

# -----------------------------
# Sidebar: Upload PDF to S3
# -----------------------------
st.sidebar.header("Upload PDF to AWS by Department")
uploaded_file = st.sidebar.file_uploader("Choose a PDF", type="pdf")
upload_dept = st.sidebar.selectbox("Select Department", DEPARTMENTS)

if uploaded_file:
    tmp_path = os.path.join("/tmp", uploaded_file.name)
    with open(tmp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    uploaded = upload_to_s3(tmp_path, upload_dept)
    if uploaded:
        st.sidebar.success(f"✅ Uploaded {uploaded_file.name} to {upload_dept}")
        
        st.sidebar.info("🔄 Rebuilding FAISS index...")
        progress_bar = st.sidebar.progress(0)

        def progress_callback(progress):
            progress_bar.progress(min(progress, 1.0))

        build_faiss_index(upload_dept, progress_callback=progress_callback)
        st.sidebar.success("✅ FAISS index rebuilt successfully")
    else:
        st.sidebar.warning(f"⚠️ {uploaded_file.name} already exists in {upload_dept}")

# -----------------------------
# Main area: Prompt & Response
# -----------------------------
selected_dept_query = st.selectbox("Your Department", DEPARTMENTS)
prompt = st.text_area("Enter your request:", height=120)

if st.button("Generate"):
    if prompt:
        with st.spinner("Processing your request..."):
            result = orchestrate_request(prompt, department=selected_dept_query)

        if result["type"] == "code":
            st.subheader("Generated Code")
            st.code(result["code"], language=result["debug"].get("detected_language", "cpp"))
            
            st.subheader("Code Review Feedback")
            st.write(result["review"])
        else:
            st.subheader("Answer")
            st.write(result["answer"])
        
        st.subheader("Debug Info")
        st.json(result["debug"])
