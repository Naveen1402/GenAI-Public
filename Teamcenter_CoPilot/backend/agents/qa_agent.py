# backend/agents/qa_agent.py
from agents.s3_ingest import query_faiss
from agents.code_generator import generate_code_via_llm

def answer_with_gtac(prompt: str, department: str):
    """
    Check department FAISS first.
    If no relevant docs → return security notice + generic LLM answer
    """
    passages = query_faiss(prompt, department, k=3)
    if not passages:
        # No department data → generic response
        generic_notice = "**Data does not belong to you and below answer is based on Open source LLM**"
        messages = [
            {"role": "system", "content": "You are a helpful Teamcenter assistant."},
            {"role": "user", "content": f"{generic_notice}\n\nQuestion: {prompt}"}
        ]
        return generate_code_via_llm(messages)

    # Build context from passages
    context = "\n\n".join([p.page_content for p in passages])
    messages = [
        {"role": "system", "content": "You are a helpful Teamcenter assistant. Answer using retrieved GTAC docs."},
        {"role": "user", "content": f"Question: {prompt}\n\nContext:\n{context}"}
    ]
    return generate_code_via_llm(messages)
