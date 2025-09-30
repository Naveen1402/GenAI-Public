import re
from agents.code_generator import generate_code_via_llm

def static_checks(code: str) -> list:
    """Run basic static checks for ITK (C++) and SOA (Java) code."""
    issues = []

    # Generic checks
    if "TODO" in code:
        issues.append("❗ Found TODO in code, might be incomplete.")
    if "print(" in code or "System.out.println" in code:
        issues.append("⚠️ Debug prints detected. Remove for production.")

    # ITK (C++)
    if "#include" not in code and "tc_str" in code:
        issues.append("❗ ITK code seems incomplete (missing #include headers).")
    if "ITK_init_module" not in code and "ITEM_create" in code:
        issues.append("⚠️ ITK module init missing — code may not run properly.")

    # SOA (Java)
    if "import com.teamcenter.soa.client" not in code and "ServiceData" in code:
        issues.append("❗ SOA code missing Teamcenter imports.")
    if "Session" not in code and "ModelObject" in code:
        issues.append("⚠️ No session handling detected — connection might fail.")

    if not issues:
        issues.append("✅ No obvious static issues found.")
    return issues

def review_code(code: str, deep: bool = True) -> str:
    """
    Runs static checks + optional LLM review for deeper insights.
    """
    static_results = static_checks(code)
    review_report = "### Static Analysis\n" + "\n".join(static_results)

    if deep:
        try:
            messages = [
                {"role": "system", "content": "You are a Teamcenter ITK & SOA code reviewer."},
                {"role": "user", "content": f"Review this code for best practices and errors:\n\n{code}"}
            ]
            ai_feedback = generate_code_via_llm(messages, model="gpt-4.1-nano")
            review_report += "\n\n### AI Review\n" + ai_feedback
        except Exception as e:
            review_report += f"\n\n⚠️ AI review failed: {str(e)}"

    return review_report
