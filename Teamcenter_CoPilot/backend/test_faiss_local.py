# backend/test_faiss_local.py
from pathlib import Path
from PyPDF2 import PdfReader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings
import shutil

# Paths
BASE_DIR = Path(__file__).resolve().parents[0]
GTAC_PATH = BASE_DIR / "data" / "gtac"
INDEX_PATH = BASE_DIR / "data" / "gtac_faiss_index"

# Embeddings
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

# Step 1: Load PDFs
def load_local_pdfs():
    docs = []
    for file in GTAC_PATH.glob("*.pdf"):
        reader = PdfReader(str(file))
        text = "".join([page.extract_text() or "" for page in reader.pages])
        if text.strip():
            docs.append({"source": file.name, "text": text})
    return docs

docs = load_local_pdfs()
print(f"Found {len(docs)} PDFs")

# Step 2: Build FAISS index
texts = []
metadatas = []
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

for doc in docs:
    chunks = [c for c in splitter.split_text(doc["text"]) if c.strip()]
    if chunks:
        texts.extend(chunks)
        metadatas.extend([{"source": doc["source"]}] * len(chunks))
    print(f"File {doc['source']} -> {len(chunks)} chunks")

if INDEX_PATH.exists():
    shutil.rmtree(INDEX_PATH)
INDEX_PATH.mkdir(parents=True, exist_ok=True)

vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
vectorstore.save_local(str(INDEX_PATH))
print(f"✅ FAISS index built with {len(texts)} chunks")

# Step 3: Query the FAISS index
vs = FAISS.load_local(str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True)
query = "Attach BOM to item revision"
results = vs.similarity_search(query, k=3)

print(f"\nTop {len(results)} results for query: '{query}'\n")
for r in results:
    print(r.metadata["source"], "->", r.page_content[:500], "\n---\n")
