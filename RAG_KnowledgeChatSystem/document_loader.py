from pypdf import PdfReader
import docx

def load_document(file):
    """Load text from PDF, TXT, or DOCX"""
    text = ""

    if file.type == "application/pdf":
        pdf_reader = PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""

    elif file.type == "text/plain":
        text = file.read().decode("utf-8")

    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"

    else:
        raise ValueError("Unsupported file format")

    return text.strip()
