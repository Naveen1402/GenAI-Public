import streamlit as st
import os
from Fileload import INPUT_DIR, seen, save_seen, ensure_schema
from graphviz import Digraph
from email_notify import send_email

# --- Page Config ---
st.set_page_config(page_title="LangGraph Agent Invoice Processor", layout="wide")
st.title("📄 LangGraph Invoice Agent")

# --- Dark Background and CSS Styling ---
st.markdown(
    """
    <style>
    /* Dark background for the app */
    .stApp {
        background-color: #1e1e1e;
        color: #ffffff;
    }
    /* Headers */
    h1, h2, h3 {
        color: #ff99cc;  /* Pinkish header */
    }
    /* File uploader style */
    .css-1r6slb0 {
        background-color: #3399ff;
        color: white;
        border-radius: 10px;
    }
    /* Info/warning/success boxes */
    .stAlert {
        border-radius: 10px;
        padding: 10px;
        color: #ffffff;
        background-color: #333333;
    }
    /* Input text (email) */
    input[type="text"] {
        background-color: #333333 !important;
        color: #ffffff !important;
        border-radius: 5px;
    }
    /* Buttons */
    .stButton>button {
        background-color: #000000 !important;
        color: #ffffff !important;
        border-radius: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Ensure input folder & DB exist ---
ensure_schema()
os.makedirs(INPUT_DIR, exist_ok=True)

# --- Upload Invoice ---
uploaded_file = st.file_uploader("Upload Invoice Image", type=["png", "jpg", "jpeg"])
file_path = None
if uploaded_file is not None:
    file_path = os.path.join(INPUT_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    seen.add(uploaded_file.name)
    save_seen(seen)
    st.success(f"✅ File uploaded: {uploaded_file.name}")

# --- Email input + send button ---
recipient_email = st.text_input("Recipient Email")
if st.button("Send Email"):
    if recipient_email:
        ok = send_email(
            "gbpec.aswal@gmail.com",
            recipient_email,
            "Invoice Processed",
            "Your invoice has been processed successfully."
        )
        if ok:
            st.success(f"📧 Email sent to: {recipient_email}")
        else:
            st.error("❌ Failed to send email. Check server logs.")
    else:
        st.warning("⚠️ Please enter a recipient email first.")

# --- Knowledge graph + invoice preview side by side ---
st.subheader("📊 Processing Pipeline")
col_left, col_right = st.columns([2, 1])  # left: graph, right: invoice

# --- Knowledge Graph ---
with col_left:
    dot = Digraph(graph_attr={"rankdir": "LR"})  # horizontal layout

    # Colored nodes in pink shades
    dot.node("WATCH", "WATCH", style="filled", fillcolor="#ffb3d9")
    dot.node("OCR", "OCR", style="filled", fillcolor="#ff99cc")
    dot.node("CLEAN", "CLEAN", style="filled", fillcolor="#ff66b3")
    dot.node("EXTRACT", "EXTRACT", style="filled", fillcolor="#ff3399")
    dot.node("VALIDATE", "VALIDATE", style="filled", fillcolor="#ff007f")
    dot.node("PERSIST", "PERSIST", style="filled", fillcolor="#e60073")
    dot.node("NOTIFY", "NOTIFY", style="filled", fillcolor="#b3005c")

    edges = [
        ("WATCH", "OCR"),
        ("OCR", "CLEAN"),
        ("CLEAN", "EXTRACT"),
        ("EXTRACT", "VALIDATE"),
        ("VALIDATE", "PERSIST"),
        ("PERSIST", "NOTIFY"),
    ]
    for edge in edges:
        dot.edge(*edge)

    st.graphviz_chart(dot)

# --- Invoice Preview ---
with col_right:
    if file_path:
        st.image(
            file_path,
            caption="Uploaded Invoice",
            width=227  # ≈ 6 cm
        )
