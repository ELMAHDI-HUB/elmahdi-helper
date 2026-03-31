import streamlit as st
from openai import OpenAI
import os

# -------------------- PAGE SETUP --------------------
st.set_page_config(page_title="ELMAHDI HELPER", page_icon="🤖")
st.title("ELMAHDI HELPER 🤖")

# -------------------- API KEY --------------------
API_KEY = st.secrets.get("NVIDIA_API_KEY")

if not API_KEY:
    st.error("Missing NVIDIA_API_KEY")
    st.stop()

# -------------------- CLIENT --------------------
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=API_KEY
)

# -------------------- FILE UPLOAD --------------------
uploaded_file = st.file_uploader(
    "Upload a document",
    type=["txt", "pdf", "docx"]
)

file_content = ""

if uploaded_file is not None:
    st.success(f"Uploaded: {uploaded_file.name}")

    # TXT
    if uploaded_file.type == "text/plain":
        file_content = uploaded_file.read().decode("utf-8")

    # PDF
    elif uploaded_file.type == "application/pdf":
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                file_content += text

    # DOCX
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        import docx
        doc = docx.Document(uploaded_file)
        for para in doc.paragraphs:
            file_content += para.text + "\n"

# -------------------- CHAT HISTORY --------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------- USER INPUT --------------------
user_input = st.chat_input("Type your message...")

if user_input:
    # Show user message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # -------------------- BUILD MESSAGES --------------------
    messages = [
        {
            "role": "system",
            "content": (
                "You are ELMAHDI HELPER, created by developer Elmahdi Oukassou. "
                "You are helpful, friendly, and concise. "
                "Never show reasoning or internal thoughts. Only give final answers."
            )
        }
    ]

    # Add document if uploaded
    if file_content:
        messages.append({
            "role": "user",
            "content": f"Here is a document:\n{file_content}"
        })

    # Add conversation history
    messages.extend(st.session_state.messages)

    # -------------------- API CALL --------------------
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",  # your current model
            messages=messages,
            temperature=0.6,
            max_tokens=512
        )

        reply = response.choices[0].message.content

    except Exception as e:
        reply = f"Error: {e}"

    # -------------------- SHOW RESPONSE --------------------
    st.chat_message("assistant").markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
