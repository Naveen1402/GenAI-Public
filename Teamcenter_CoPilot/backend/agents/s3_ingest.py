# backend/agents/s3_ingest.py
import os
import boto3
import hashlib
import time
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings

# -------------------------
# Load ENV
# -------------------------
load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_PREFIX = os.getenv("S3_PREFIX", "PLM/")

# Local paths
TMP_FOLDER = os.path.abspath("backend/data/tmp_pdfs")
INDEX_PATH = os.path.abspath("backend/data/faiss_index")

# Initialize S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION,
)

# Embeddings
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")


# -------------------------
# Utils for Upload
# -------------------------
def file_hash(filepath):
    """Generate md5 hash for duplicate detection."""
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def file_exists_in_s3(filename, s3_folder):
    """Check if file exists in S3 folder by comparing ETag."""
    try:
        obj = s3.head_object(Bucket=S3_BUCKET_NAME, Key=f"{S3_PREFIX}{s3_folder}/{filename}")
        etag = obj["ETag"].strip('"')
        md5_hash = file_hash(os.path.join(TMP_FOLDER, filename))
        return etag == md5_hash
    except Exception:
        return False


def upload_to_s3(filepath, department: str):
    """Upload file to department folder in S3 if not duplicate."""
    filename = os.path.basename(filepath)
    md5_hash = file_hash(filepath)
    s3_key = f"{S3_PREFIX}{department}/{filename}"

    # Check duplicate
    try:
        obj = s3.head_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        etag = obj["ETag"].strip('"')
        if etag == md5_hash:
            print(f"⚠️ Skipping duplicate: {filename}")
            return False
    except Exception:
        pass

    s3.upload_file(filepath, S3_BUCKET_NAME, s3_key)
    print(f"✅ Uploaded: {filename} → s3://{S3_BUCKET_NAME}/{s3_key}")
    return True


# -------------------------
# FAISS Index
# -------------------------
def build_faiss_index(department: str, progress_callback=None):
    """
    Build department-specific FAISS index from S3 PDFs.
    progress_callback: callable(progress: float) for Streamlit progress bar
    """
    dept_prefix = f"{S3_PREFIX}{department}/"
    local_folder = os.path.join(TMP_FOLDER, department)
    os.makedirs(local_folder, exist_ok=True)

    # Fetch PDFs
    response = s3.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=dept_prefix)
    if "Contents" not in response:
        return False

    pdfs = []
    for obj in response["Contents"]:
        key = obj["Key"]
        if key.lower().endswith(".pdf"):
            local_path = os.path.join(local_folder, os.path.basename(key))
            s3.download_file(S3_BUCKET_NAME, key, local_path)
            pdfs.append(local_path)

    if not pdfs:
        return False

    all_chunks = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    total_pdfs = len(pdfs)

    for i, pdf in enumerate(pdfs):
        loader = PyPDFLoader(pdf)
        docs = loader.load()
        total_chunks_in_pdf = sum(len(splitter.split_text(d.page_content)) for d in docs)
        processed_chunks = 0

        for d in docs:
            chunks = splitter.split_text(d.page_content)
            for chunk in chunks:
                if chunk.strip():
                    all_chunks.append(chunk)
                processed_chunks += 1
                # Update progress per chunk
                if progress_callback and total_chunks_in_pdf > 0:
                    progress_callback((i + processed_chunks / total_chunks_in_pdf) / total_pdfs * 0.9)

    if not all_chunks:
        return False

    # Save FAISS index per department
    index_path_dept = os.path.join(INDEX_PATH, department)
    os.makedirs(index_path_dept, exist_ok=True)
    vectorstore = FAISS.from_texts(all_chunks, embeddings)
    vectorstore.save_local(index_path_dept)

    if progress_callback:
        progress_callback(1.0)

    print(f"✅ FAISS index built for {department}: {len(all_chunks)} chunks")
    return True


def query_faiss(prompt: str, department: str, k=3):
    """Query department-specific FAISS index."""
    index_path_dept = os.path.join(INDEX_PATH, department)
    if not os.path.exists(index_path_dept):
        return []  # No data for this dept

    vectorstore = FAISS.load_local(index_path_dept, embeddings, allow_dangerous_deserialization=True)
    return vectorstore.similarity_search(str(prompt), k=k)
