# backend/agents/gtac_rag.py
import os
import shutil
from pathlib import Path
from PyPDF2 import PdfReader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings

# Base paths
BASE_DIR = Path(__file__).resolve().parents[1]  # backend/
GTAC_PATH = BASE_DIR / "data" / "gtac"         # Local PDFs folder
INDEX_PATH = BASE_DIR / "data" / "gtac_index"  # FAISS index path

# Embeddings
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")


def load_gtac_docs():
    """Load PDFs from local GTAC_PATH folder."""
    docs = []
    if not GTAC_PATH.exists():
        print("GTAC path does not exist:", GTAC_PATH)
        return docs

    for file in sorted(os.listdir(GTAC_PATH)):
        if file.lower().endswith(".pdf"):
            fp = GTAC_PATH / file
            try:
                reader = PdfReader(str(fp))
                text = "".join([page.extract_text() or "" for page in reader.pages])
                if text.strip():
                    docs.append({"source": file, "text": text})
                else:
                    print(f"Skipping {file}: no extractable text (maybe scanned).")
            except Exception as e:
                print(f"Error reading {file}: {e}")

    print(f"Found {len(docs)} GTAC documents.")
    return docs


def build_gtac_index():
    """Build FAISS index from local GTAC PDFs."""
    docs = load_gtac_docs()
    if not docs:
        raise ValueError("No GTAC PDFs with extractable text found in: " + str(GTAC_PATH))

    texts = []
    metadatas = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

    for doc in docs:
        chunks = [c for c in splitter.split_text(doc["text"]) if c.strip()]
        if chunks:
            texts.extend(chunks)
            metadatas.extend([{"source": doc["source"]}] * len(chunks))

    if not texts:
        raise ValueError("No text chunks to build GTAC FAISS index!")

    # Ensure folder exists (remove old index if any)
    if INDEX_PATH.exists():
        shutil.rmtree(INDEX_PATH)
    INDEX_PATH.mkdir(parents=True, exist_ok=True)

    vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
    vectorstore.save_local(str(INDEX_PATH))
    print(f"✅ GTAC index built from {len(docs)} PDFs and {len(texts)} chunks.")


def load_gtac_index(force_rebuild: bool = False):
    """Load FAISS index from local GTAC PDFs. Rebuild if missing or forced."""
    if force_rebuild or not INDEX_PATH.exists():
        print("FAISS index missing or force rebuild requested.")
        build_gtac_index()

    try:
        return FAISS.load_local(str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        print("Failed to load FAISS index:", e)
        print("Rebuilding index...")
        build_gtac_index()
        return FAISS.load_local(str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True)


def query_gtac(query: str, k: int = 3, force_rebuild: bool = False):
    """Query FAISS index for top-k similar chunks from local GTAC PDFs."""
    vs = load_gtac_index(force_rebuild=force_rebuild)
    return vs.similarity_search(query, k=k)


# -------------------------
# Usage (uncomment to test locally)
# -------------------------
# build_gtac_index()
# results = query_gtac("Attach BOM to item revision", k=3)
# for r in results:
#     print(r.metadata["source"], "->", r.page_content[:500])
