from langchain.text_splitter import RecursiveCharacterTextSplitter

""" ecursiveCharacterTextSplitter is used to split long text into smaller chunks in a smart and hierarchical way, respecting sentences, paragraphs, or other boundaries.
LLMs (like GPT) have a maximum token limit. Splitting text ensures large documents can be processed in pieces."""

def split_text(text, chunk_size=600, overlap=120):
    """Split text into chunks"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=overlap
    )
    return text_splitter.split_text(text)
