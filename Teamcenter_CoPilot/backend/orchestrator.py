# backend/agents/orchestrator.py
import re
from agents.code_generator import generate_code, generate_code_via_llm
from agents.qa_agent import answer_with_gtac
from agents.code_reviewer import review_code

def detect_language(prompt: str) -> str:
    """Detect ITK C++ or SOA Java."""
    if re.search(r"\bitk\b", prompt.lower()):
        return "cpp"
    elif re.search(r"\bsoa\b", prompt.lower()):
        return "java"
    else:
        return "cpp"

def orchestrate_request(prompt: str, department: str):
    """Main orchestration: code or info based on prompt & department."""
    debug_info = {"prompt": prompt}
    
    # Detect if code request
    is_code_request = bool(re.search(r"\b(itk|soa|bmide|java|c\+\+|tc code)\b", prompt.lower()))
    
    if is_code_request:
        lang = detect_language(prompt)
        debug_info["detected_language"] = lang
        
        try:
            code = generate_code(prompt)
            if code:
                debug_info["source"] = "template"
        except Exception as e:
            code = None
            debug_info["template_error"] = str(e)

        if not code:
            debug_info["source"] = "LLM + GTAC"
            code = answer_with_gtac(prompt, department)
        
        try:
            review_feedback = review_code(code) if code else ""
        except Exception as e:
            review_feedback = f"Code review failed: {str(e)}"
        
        return {"type": "code", "code": code, "review": review_feedback, "debug": debug_info}
    
    else:
        # Simple info
        answer = answer_with_gtac(prompt, department)
        debug_info["source"] = "GTAC + LLM"
        return {"type": "info", "answer": answer, "debug": debug_info}
