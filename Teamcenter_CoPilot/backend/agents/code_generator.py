

# backend/agents/code_generator.py
import os
import json
import requests
from agents.s3_ingest import query_faiss  # FAISS/S3 query
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

# Setup Jinja2 environment for templates
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "../templates")
env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))

# Your Euron API key (stored in env)
EURON_API_KEY = os.getenv("OPENAI_API_KEY")


def generate_code(prompt: str) -> str:
    """
    Main code generation function:
    1. Check if a template exists → use Jinja2 template
    2. Otherwise → query FAISS (S3 PDFs) + fallback to Euron LLM
    """
    prompt_lower = prompt.lower()

    # --- Template-based generation ---
    if "create item" in prompt_lower:
        template = env.get_template("itk_create_item.cpp.j2")
        return template.render(item_type="Item", rev="A")

    elif "upload dataset" in prompt_lower:
        template = env.get_template("soa_upload_dataset.java.j2")
        return template.render(
            item_id="ITEM001",
            dataset_name="ExamplePDF",
            file_path="/path/to/file.pdf"
        )

    # --- Otherwise fallback to LLM with FAISS context ---
    return generate_code_via_llm(prompt)


def generate_code_via_llm(prompt: str, model="gpt-4.1-nano", department=None) -> str:
    """
    Calls Euron LLM API with optional department-based FAISS context.
    If no FAISS results for department → prepend warning message.
    """
    if not EURON_API_KEY:
        raise RuntimeError("EURON_API_KEY not set in environment")

    context_passages = []

    # Query FAISS for department if provided
    if department:
        try:
            passages = query_faiss(prompt, department=department, k=3)
            context_passages = [p.page_content for p in passages]
        except Exception as e:
            print(f"⚠️ FAISS query failed: {e}")

    # Build context string
    context_text = "\n\n".join(context_passages) if context_passages else ""

    # Prepare system prompt
    if context_text:
        system_prompt = f"""
You are a Teamcenter code assistant. Use only the references below.
Context from {department} department FAISS/S3 PDFs:
{context_text}

User request: {prompt}
"""
    else:
        system_prompt = f"""
**Data does not belong to you and below answer is based on Open source LLM**
User request: {prompt}
"""

    # Prepare messages for Euron LLM
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    # Call Euron LLM API
    url = "https://api.euron.one/api/v1/euri/chat/completions"
    headers = {
        "Authorization": f"Bearer {EURON_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 2000
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ Euron LLM call failed: {e}")
        return f"Error generating response: {e}"
