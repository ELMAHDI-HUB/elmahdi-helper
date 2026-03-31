import base64
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
IMAGE_ENDPOINT = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium"

st.set_page_config(page_title="ELMAHDI HELPER", page_icon="🤖", layout="wide")
st.title("ELMAHDI HELPER 🤖")
st.caption("Chat • Document Q&A • Image generation")

# -----------------------------
# SECRETS
# Keep these names exactly as you already have them in Streamlit:
# NVIDIA_API_KEY   -> your NVIDIA chat key
# STABILITY_API_KEY -> your second NVIDIA key for the NVIDIA-hosted SD3 image endpoint
# -----------------------------
NVIDIA_API_KEY = st.secrets["NVIDIA_API_KEY"] if "NVIDIA_API_KEY" in st.secrets else None
STABILITY_API_KEY = st.secrets["STABILITY_API_KEY"] if "STABILITY_API_KEY" in st.secrets else None

chat_client = None
if NVIDIA_API_KEY:
    chat_client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NVIDIA_API_KEY,
    )

# -----------------------------
# HELPERS
# -----------------------------
SYSTEM_PROMPT = """
You are ELMAHDI HELPER, a helpful and friendly AI assistant created by Elmahdi Oukassou.

Rules:
- If asked who created you, answer: "I was created by Elmahdi Oukassou, a developer."
- Never show chain-of-thought, internal reasoning, or <think> tags.
- Give clean, final answers only.
- Be concise and helpful.
""".strip()


def clean_reply(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()


def ask_chat(messages, max_tokens=1000) -> str:
    if chat_client is None:
        raise RuntimeError("Missing NVIDIA_API_KEY in Streamlit Secrets.")

    response = chat_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.6,
        top_p=0.7,
        max_tokens=max_tokens,
        stream=False,
    )
    return clean_reply(response.choices[0].message.content or "")


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
        raise RuntimeError("Missing STABILITY_API_KEY in Streamlit Secrets.")

    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
        "mode": "text-to-image",
        "model": "sd3",
        "aspect_ratio": aspect_ratio,
        "output_format": "jpeg",
        "cfg_scale": 5,
        "steps": 30,
        "seed": 0,
    }

    if negative_prompt.strip():
        payload["negative_prompt"] = negative_prompt.strip()

    response = requests.post(IMAGE_ENDPOINT, headers=headers, json=payload, timeout=180)

    if response.status_code != 200:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(f"{response.status_code}: {detail}")

    data = response.json()

    if "image" not in data:
        raise RuntimeError(f"Unexpected response format: {data}")

    return base64.b64decode(data["image"])


# -----------------------------
# SESSION STATE
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------
# UI TABS
# -----------------------------
chat_tab, doc_tab, image_tab = st.tabs(
    ["💬 Chat", "📄 Document Q&A", "🎨 Generate Image"]
)

# -----------------------------
# CHAT TAB
# -----------------------------
with chat_tab:
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
            messages.extend(st.session_state.chat_history[-12:])

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
with doc_tab:
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
                        messages = [
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
                                answer = ask_chat(messages, max_tokens=1200)
                                st.markdown("### Answer")
                                st.write(answer)
                            except Exception as e:
                                st.error(f"Error: {e}")
            else:
                st.warning("No readable text was extracted from this file.")

# -----------------------------
# IMAGE GENERATION TAB
# -----------------------------
with image_tab:
    if not STABILITY_API_KEY:
        st.warning("Add STABILITY_API_KEY in Streamlit Secrets to use image generation.")
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
            ["1:1", "16:9", "9:16"],
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
                            file_name="elmahdi-helper-image.jpg",
                            mime="image/jpeg",
                        )
                    except Exception as e:
                        st.error(f"Image generation failed: {e}")
