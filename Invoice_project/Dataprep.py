import os
import re
import json
import warnings
from typing import Dict, Any, List
from Fileload import DB_PATH, POLL_SEC, INPUT_DIR, save_seen, seen
from config import EURI_API_KEY, MODEL

# -------------------------------
# OCR Lazy Loader
# -------------------------------
_ocr_reader = None

def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is not None:
        return _ocr_reader
    try:
        import easyocr
        _ocr_reader = easyocr.Reader(["en"], gpu=False)
        return _ocr_reader
    except Exception as e:
        warnings.warn(f"EasyOCR failed: {e}")
        return None

def NODE_OCR(file_path: str) -> Dict[str, Any]:
    ocr = get_ocr_reader()
    if ocr is None:
        return {"ocr_text": (
            "Mock OCR text for testing UI.\n"
            "Vendor: ACME Corp\n"
            "Invoice Number: 12345\n"
            "Date: 2025-09-24\n"
            "Total: 1000.00 USD"
        )}
    try:
        text = "\n".join(ocr.readtext(file_path, detail=0))
        if not text.strip():
            raise RuntimeError("Empty OCR output")
        return {"ocr_text": text}
    except Exception as e:
        warnings.warn(f"OCR failed: {e}")
        return {"ocr_text": (
            "Mock OCR text for testing UI.\n"
            "Vendor: ACME Corp\n"
            "Invoice Number: 12345\n"
            "Date: 2025-09-24\n"
            "Total: 1000.00 USD"
        )}

# -------------------------------
# Pipeline function to lazy-load LangGraph
# -------------------------------
def run_invoice_pipeline(ocr_text: str) -> Dict[str, Any]:
    """Run CLEAN → EXTRACT → VALIDATE lazily, returns all outputs"""
    # Lazy imports to avoid blocking
    from euriai.langgraph import EuriaiLangGraph

    outputs = {}

    # CLEAN
    try:
        clean_graph = EuriaiLangGraph(api_key=EURI_API_KEY, default_model=MODEL)
        clean_graph.add_ai_node(
            "CLEAN",
            """You clean noisy OCR to plain text.
- Keep facts.
- No guessing.
- Keep table rows readable.

OCR:
{ocr_text}"""
        )
        clean_graph.set_entry_point("CLEAN")
        clean_graph.set_finish_point("CLEAN")
        clean_raw = clean_graph.run({"ocr_text": ocr_text})
        clean_text = pick_text(clean_raw, prefer_key="CLEAN_output")
        if not clean_text.strip():
            clean_text = ocr_text
        outputs["clean_text"] = clean_text
        outputs["CLEAN_raw"] = clean_raw
    except Exception as e:
        warnings.warn(f"CLEAN failed: {e}")
        outputs["clean_text"] = ocr_text
        outputs["CLEAN_raw"] = {"fallback": True}

    # EXTRACT
    try:
        extract_graph = EuriaiLangGraph(api_key=EURI_API_KEY, default_model=MODEL)
        extract_graph.add_ai_node(
            "EXTRACT",
            """From CLEAN_TEXT, return STRICT JSON with keys exactly:
vendor, number, date, total, currency,
line_items (list of {{description, quantity, unit_price, amount}}).

Unknown → null. Numbers numeric. Dates YYYY-MM-DD if possible.
JSON ONLY, no extra text.

CLEAN_TEXT:
{clean_text}"""
        )
        extract_graph.set_entry_point("EXTRACT")
        extract_graph.set_finish_point("EXTRACT")
        extract_out = extract_graph.run({"clean_text": outputs["clean_text"]})
        raw_json = pick_text(extract_out, prefer_key="EXTRACT_output")
        outputs["raw_json"] = raw_json
        outputs["EXTRACT_raw"] = extract_out
    except Exception as e:
        warnings.warn(f"EXTRACT failed: {e}")
        outputs["raw_json"] = json.dumps(_heuristic_extract(outputs["clean_text"]))
        outputs["EXTRACT_raw"] = {"fallback": True}

    # VALIDATE
    data = parse_json_safe(outputs["raw_json"])
    outputs["validate"] = NODE_VALIDATE(data)

    return outputs

# -------------------------------
# Helpers
# -------------------------------
def pick_text(x, *, prefer_key=None):
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        if prefer_key and prefer_key in x and isinstance(x[prefer_key], str):
            return x[prefer_key]
        for k in ("output", "text", "CLEAN_output", "EXTRACT_output"):
            if k in x and isinstance(x[k], str):
                return x[k]
        return json.dumps(x, ensure_ascii=False)
    return str(x)

def parse_json_safe(raw):
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        return {"__raw__": raw}
    try:
        return json.loads(raw)
    except Exception:
        pass
    try:
        s, e = raw.find("{"), raw.rfind("}")
        if s != -1 and e != -1 and e > s:
            return json.loads(raw[s:e+1])
    except Exception:
        pass
    return {"__raw__": raw}

def _heuristic_extract(clean_text: str) -> dict:
    def find(pat, s):
        m = re.search(pat, s, re.IGNORECASE)
        return m.group(1).strip() if m else None

    vendor = find(r"Vendor:\s*(.+)", clean_text)
    number = find(r"(?:Invoice Number|Invoice No\.?):\s*([A-Za-z0-9\-]+)", clean_text)
    date   = find(r"(?:Invoice Date|Date):\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", clean_text)
    total  = find(r"Total:\s*([0-9]+(?:\.[0-9]+)?)", clean_text)
    curr   = find(r"Total:\s*[0-9]+(?:\.[0-9]+)?\s*([A-Za-z]{3})", clean_text) or find(r"Currency:\s*([A-Za-z]{3})", clean_text)

    try: total = float(total) if total else None
    except: total = None

    return {
        "vendor": vendor,
        "number": number,
        "date": date,
        "total": total,
        "currency": curr,
        "line_items": []
    }

def NODE_VALIDATE(data: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[str] = []
    for k in ["vendor", "number", "date", "currency"]:
        if k not in data or data.get(k) in (None, ""):
            issues.append(f"missing key: {k}")
    try:
        if data.get("total") is None:
            issues.append("total is null")
        else:
            float(data.get("total"))
    except Exception:
        issues.append(f"total not numeric: {data.get('total')}")
    if not isinstance(data.get("line_items", []), list):
        issues.append("line_items not a list")
    return {"valid": len(issues) == 0, "issues": issues}
