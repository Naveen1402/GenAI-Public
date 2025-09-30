# 🚀 Teamcenter CoPilot – Department-Specific Knowledge Assistant

Teamcenter CoPilot is an **AI-powered assistant** that leverages **department-specific knowledge** stored in **S3 buckets** and **FAISS indexes**.
It ensures **secure, role-based access** to enterprise data by answering user queries only from their department’s documents.
If no relevant knowledge is found, the assistant responds with a **warning message** and falls back to an **open-source LLM** for generic answers.

---

## ✨ Features

* ✅ **Department-specific Querying** – Users can select their department (Admin, Development, Engineering, Quality).
* ✅ **Secure Access Control** – Data isolation per department using **S3 folders** + **FAISS indexes**.
* ✅ **Streamlit Frontend** – Clean, intuitive UI with dropdown for department selection.
* ✅ **Document Uploads** – Upload files directly via UI, stored in correct S3 department folder.
* ✅ **Progress Bar** – Real-time feedback during ingestion.
* ✅ **LLM Integration (Euron API)** – Powered by `gpt-4.1-nano` via Euron.ai.
* ✅ **Fallback Mechanism** – If query doesn’t belong to department →
  **Bold Warning**:

  ```
  Data does not belong to you  
  Below answer is based on Open Source LLM
  ```
* ✅ **Template-based Answers** – For common Teamcenter requests (e.g., create item, upload dataset).

---

## 📂 Project Structure

```
Teamcenter_CoPilot/
│
├── backend/
│   ├── agents/
│   │   ├── code_generator.py     # Euron LLM + FAISS integration
│   │   ├── qa_agent.py           # Query orchestration with department logic
│   │   └── s3_ingest.py          # S3 upload + FAISS indexing
│   ├── orchestrator.py           # Main request orchestration
│   └── app.py                    # Streamlit backend entrypoint
│
├── templates/                    # Jinja2 templates for boilerplate code
│
├── docs/                         # System design + requirement documentation
│
└── README.md                     # This file
```

---

## 🛠️ Tech Stack

* **Frontend**: Streamlit
* **Storage**: AWS S3 (departmental folders)
* **Vector DB**: FAISS (per-department indexes)
* **LLM**: Euron.ai (`gpt-4.1-nano`)
* **Backend**: Python 3.10+
* **Libraries**: boto3, requests, faiss, jinja2

---

## ⚙️ Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/<your-username>/teamcenter-copilot.git
cd teamcenter-copilot
```

### 2️⃣ Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Setup Environment Variables

Create a `.env` file:

```ini
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=your-region
S3_BUCKET=naveenaswal-genai

EURON_API_KEY=your_euron_api_key
```

---

## ▶️ Usage

### Run Streamlit App

```bash
streamlit run backend/app.py
```

### Upload Departmental Documents

* Select your **department** from dropdown.
* Upload files → stored in **S3 under correct folder**.
* Data is automatically indexed into **FAISS**.

### Ask Questions

* Select your department.
* Enter your query.
* System fetches answer from **FAISS index**.
* If not relevant:

  ```
  Data does not belong to you
  Below answer is based on Open Source LLM
  ```

---

## 🔐 Security Model

* Each **department has isolated data** in **S3 folders** and **FAISS indexes**.
* Ensures **data leakage prevention** across departments.
* Queries restricted to **selected department** only.

---

## 🚧 Future Enhancements

* 📊 **Analytics Dashboard** – Track queries per department.
* 🛡️ **SSO Integration** – Auto-detect user’s department from company LDAP/SSO.
* 🧠 **Fine-Tuned Models** – Department-specialized LLM fine-tuning.
* 🔎 **RAG Improvements** – Hybrid search (BM25 + FAISS) for better accuracy.
* 📝 **Version Control** – Keep track of uploaded documents with metadata.
* ☁️ **Multi-Cloud Support** – Azure/GCP buckets in addition to AWS S3.

---

## 👨‍💻 Author

**Naveen Aswal**
PLM & GenAI

---
