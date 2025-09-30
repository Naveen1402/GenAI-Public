# backend/main.py
import os
import threading
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

# ensure package imports work
from agents.code_generator import generate_code
from agents.s3_ingest import start_watcher  # 👈 Import watcher

load_dotenv()

app = FastAPI(title="Teamcenter Code Assistant API")


class PromptRequest(BaseModel):
    prompt: str


@app.post("/generate")
def generate_endpoint(req: PromptRequest):
    try:
        result = generate_code(req.prompt)
        return result
    except Exception as e:
        return {
            "code": "",
            "template_used": None,
            "llm_used": True,
            "review_feedback": "",
            "debug_info": f"Server error: {e}"
        }


# ---------------------------
# Background Watcher Integration
# ---------------------------
@app.on_event("startup")
def startup_event():
    """Start S3 watcher in background when FastAPI launches."""
    watcher_thread = threading.Thread(target=start_watcher, daemon=True)
    watcher_thread.start()
    print("✅ S3 Watcher started in background.")
