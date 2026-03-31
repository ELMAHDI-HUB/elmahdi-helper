import io
import re
import requests
import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document

# -----------------------------
# CONFIG
# -----------------------------
CHAT_MODEL = "openai/gpt-oss-120b"

st.set_page_config(page_title="ELMAHDI HELPER", page_icon="🤖", layout="wide")
st.title("ELMAHDI HELPER 🤖")
st.caption("Chat • Document Q&A • Image generation")

# -----------------------------
# SECRETS
# -----------------------------
NVIDIA_API_KEY = st.secrets["NVIDIA_API_KEY"] if "NVIDIA_API_KEY" in st.secrets else None
STABILITY_API_KEY = st.secrets["STABILITY_API_KEY"] if "STABILITY_API_KEY" in st.secrets else None

chat_client = None
if NVIDIA_API_KEY:
    chat_client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NVIDIA_API_KEY
    )

# -----------------------------
# HELPERS
# -----------------------------
SYSTEM_PROMPT = """
You are ELMAHDI HELPER, a helpful and friendly AI assistant created by Elmahdi Oukassou.

Rules:
- If asked who created you, answer: "I was created by Elmahdi Oukassou, a developer."
- Do not mention OpenAI, NVIDIA, or any other company as your creator.
- Never show internal reasoning, chain-of-thought, or <think> tags.
- Give clean, final answers.
- Be concise and helpful.
""".strip()


def clean_reply(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()


def ask_chat(messages, max_tokens=1000):
    if chat_client is None:
        raise RuntimeError("Missing NVIDIA_API_KEY")
    response = chat_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.6,
        top_p=0.7,
        max_tokens=max_tokens,
        stream=False,
    )
    return clean_reply(response.choices[0].message.content)


def read_document(uploaded_file) -> str:
    filename = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()

    if filename.endswith(".txt") or filename.endswith(".csv"):
        return raw.decode("utf-8", errors="ignore")

    if filename.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw))
        parts = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
        return "\n\n".join(parts)

    if filename.endswith(".docx"):
        doc = Document(io.BytesIO(raw))
        return "\n".join(p.text for p in doc.paragraphs)

    return ""


def generate_image(prompt: str, negative_prompt: str = "", aspect_ratio: str = "1:1") -> bytes:
    if not STABILITY_API_KEY:
        raise RuntimeError("Missing STABILITY_API_KEY")

    url = "https://api.stability.ai/v2beta/stable-image/generate/core"
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "image/*",
    }

    # multipart/form-data
    files = {
        "prompt": (None, prompt),
        "output_format": (None, "png"),
        "aspect_ratio": (None, aspect_ratio),
    }

    if negative_prompt.strip():
        files["negative_prompt"] = (None, negative_prompt.strip())

    response = requests.post(url, headers=headers, files=files, timeout=180)

    if response.status_code != 200:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(f"{response.status_code}: {detail}")

    return response.content


# -----------------------------
# SESSION STATE
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------
# UI
# -----------------------------
tab_chat, tab_doc, tab_image = st.tabs(
    ["💬 Chat", "📄 Document Q&A", "🎨 Generate Image"]
)

# -----------------------------
# CHAT TAB
# -----------------------------
with tab_chat:
    if not NVIDIA_API_KEY:
        st.warning("Add NVIDIA_API_KEY in Streamlit Secrets to use chat.")
    else:
        for msg in st.session_state.chat_history:
            avatar = "🧑" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        user_input = st.chat_input("Type your message...")

        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_input)

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(st.session_state.chat_history[-12:])  # keep recent history

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    try:
                        reply = ask_chat(messages, max_tokens=1000)
                    except Exception as e:
                        reply = f"Error: {e}"
                st.markdown(reply)

            st.session_state.chat_history.append({"role": "assistant", "content": reply})

# -----------------------------
# DOCUMENT TAB
# -----------------------------
with tab_doc:
    if not NVIDIA_API_KEY:
        st.warning("Add NVIDIA_API_KEY in Streamlit Secrets to use document Q&A.")
    else:
        uploaded_doc = st.file_uploader(
            "Upload a TXT, CSV, PDF, or DOCX file",
            type=["txt", "csv", "pdf", "docx"],
            key="doc_uploader",
        )

        doc_question = st.text_input(
            "Ask something about the document",
            placeholder="Summarize this / what are the key points / extract dates",
            key="doc_question",
        )

        if uploaded_doc is not None:
            st.success(f"Uploaded: {uploaded_doc.name}")

            try:
                doc_text = read_document(uploaded_doc)
            except Exception as e:
                doc_text = ""
                st.error(f"Could not read the file: {e}")

            if doc_text.strip():
                with st.expander("Preview extracted text"):
                    st.text(doc_text[:3500])

                if st.button("Analyze document", key="analyze_document_button"):
                    if not doc_question.strip():
                        st.warning("Type a question first.")
                    else:
                        doc_messages = [
                            {
                                "role": "system",
                                "content": SYSTEM_PROMPT + "\nUse the uploaded document when answering.",
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"Document content:\n\n{doc_text[:50000]}\n\n"
                                    f"Question:\n{doc_question}"
                                ),
                            },
                        ]

                        with st.spinner("Reading document..."):
                            try:
                                answer = ask_chat(doc_messages, max_tokens=1200)
                                st.markdown("### Answer")
                                st.write(answer)
                            except Exception as e:
                                st.error(f"Error: {e}")
            else:
                st.warning("No readable text was extracted from this file.")

# -----------------------------
# IMAGE GENERATION TAB
# -----------------------------
with tab_image:
    if not STABILITY_API_KEY:
        st.warning("Add STABILITY_API_KEY in Streamlit Secrets to generate images.")
    else:
        prompt = st.text_area(
            "Describe the image you want",
            placeholder="A futuristic Moroccan city at sunset, cinematic lighting, highly detailed",
            height=120,
            key="image_prompt",
        )

        negative_prompt = st.text_input(
            "Negative prompt (optional)",
            placeholder="blurry, low quality, distorted, extra fingers",
            key="negative_prompt",
        )

        aspect_ratio = st.selectbox(
            "Aspect ratio",
            ["1:1", "16:9", "9:16", "4:3", "3:2"],
            index=0,
            key="aspect_ratio",
        )

        if st.button("Generate image", key="generate_image_button"):
            if not prompt.strip():
                st.warning("Write a prompt first.")
            else:
                with st.spinner("Generating image..."):
                    try:
                        image_bytes = generate_image(prompt, negative_prompt, aspect_ratio)
                        st.image(image_bytes, caption="Generated image", use_container_width=True)
                        st.download_button(
                            "Download image",
                            data=image_bytes,
                            file_name="elmahdi-helper-image.png",
                            mime="image/png",
                        )
                    except Exception as e:
                        st.error(f"Image generation failed: {e}")
