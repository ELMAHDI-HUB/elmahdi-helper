import base64
import io
import os
import re
import tempfile
import time
from textwrap import dedent

import requests
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document

# =========================================
# BRAND LOGO
# =========================================
BRAND_SVG = dedent(
    """
<svg width="112" height="112" viewBox="0 0 112 112" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="brandGrad" x1="10" y1="8" x2="102" y2="104" gradientUnits="userSpaceOnUse">
      <stop stop-color="#5B5CFF"/>
      <stop offset="0.55" stop-color="#12B8FF"/>
      <stop offset="1" stop-color="#2DE2D0"/>
    </linearGradient>
    <filter id="brandShadow" x="-40%" y="-40%" width="180%" height="180%">
      <feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#09162C" flood-opacity="0.45"/>
    </filter>
  </defs>

  <rect x="8" y="8" width="96" height="96" rx="28" fill="url(#brandGrad)" filter="url(#brandShadow)"/>
  <path d="M35 35H74" stroke="white" stroke-width="10" stroke-linecap="round"/>
  <path d="M35 56H67" stroke="white" stroke-width="10" stroke-linecap="round"/>
  <path d="M35 77H74" stroke="white" stroke-width="10" stroke-linecap="round"/>
  <path d="M35 35V77" stroke="white" stroke-width="10" stroke-linecap="round"/>
  <circle cx="82" cy="29" r="6" fill="#E8FBFF"/>
</svg>
"""
).strip()


def ensure_logo_file() -> str:
    path = os.path.join(tempfile.gettempdir(), "elmahdi_helper_logo.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(BRAND_SVG)
    return path


LOGO_FILE = ensure_logo_file()

# =========================================
# CONFIG
# =========================================
CHAT_MODEL = "openai/gpt-oss-120b"
FLUX_ENDPOINT = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.2-klein-4b"

st.set_page_config(
    page_title="ELMAHDI HELPER",
    page_icon="🤖",
    layout="wide",
)

# =========================================
# GLOBAL STYLING
# =========================================
st.markdown(
    dedent(
        """
<style>
    :root {
        --bg1: #050814;
        --bg2: #0c1320;
        --panel: rgba(255,255,255,0.05);
        --panel2: rgba(255,255,255,0.035);
        --border: rgba(255,255,255,0.08);
        --text: #eef5ff;
        --muted: #bfd0ea;
        --muted2: #91a8cb;
        --shadow: 0 20px 60px rgba(0,0,0,0.28);
    }

    .stApp {
        background:
            radial-gradient(circle at 10% 10%, rgba(59, 130, 246, 0.18), transparent 24%),
            radial-gradient(circle at 88% 8%, rgba(168, 85, 247, 0.14), transparent 22%),
            radial-gradient(circle at 50% 100%, rgba(34, 211, 238, 0.10), transparent 30%),
            linear-gradient(180deg, var(--bg1) 0%, var(--bg2) 100%);
        color: var(--text);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: rgba(7, 12, 22, 0.92);
        border-right: 1px solid var(--border);
    }

    .block-container {
        max-width: 1220px;
        padding-top: 1.1rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3 {
        color: #f7fbff;
        letter-spacing: -0.02em;
    }

    .stCaption {
        color: var(--muted2) !important;
    }

    div[data-baseweb="tab-list"] {
        gap: 0.5rem;
        margin-bottom: 0.9rem;
    }

    button[data-baseweb="tab"] {
        border-radius: 14px !important;
        padding: 0.56rem 1rem !important;
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        color: #dbe8ff !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(79,70,229,0.34), rgba(6,182,212,0.24)) !important;
        border-color: rgba(125, 211, 252, 0.22) !important;
        color: white !important;
        box-shadow: 0 12px 24px rgba(79,70,229,0.18);
    }

    .stButton button,
    .stDownloadButton button {
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        background: linear-gradient(135deg, #4f46e5, #06b6d4) !important;
        color: white !important;
        font-weight: 700 !important;
        padding-top: 0.58rem !important;
        padding-bottom: 0.58rem !important;
        box-shadow: 0 14px 28px rgba(79,70,229,0.22);
        transition: transform 0.16s ease, box-shadow 0.16s ease;
    }

    .stButton button:hover,
    .stDownloadButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 18px 34px rgba(79,70,229,0.28);
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input {
        background: rgba(8, 14, 24, 0.82) !important;
        color: #eef5ff !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
    }

    .stTextInput > div > div,
    .stTextArea > div > div,
    .stSelectbox > div > div,
    .stNumberInput > div > div,
    .stFileUploader > div {
        border-radius: 14px !important;
    }

    div[data-baseweb="select"] > div {
        background: rgba(8, 14, 24, 0.82) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        color: #eef5ff !important;
    }

    section[data-testid="stFileUploadDropzone"] {
        background: rgba(8, 14, 24, 0.68) !important;
        border: 1px dashed rgba(125, 211, 252, 0.28) !important;
        border-radius: 18px !important;
    }

    [data-testid="stChatMessage"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.025));
        border: 1px solid rgba(255,255,255,0.065);
        border-radius: 20px;
        padding: 0.55rem 0.8rem;
        box-shadow: 0 10px 28px rgba(0,0,0,0.12);
    }

    div[data-testid="stAlert"] {
        border-radius: 18px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.04);
    }

    pre, code {
        border-radius: 14px !important;
    }

    hr {
        border-color: rgba(255,255,255,0.08) !important;
    }

    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
</style>
"""
    ),
    unsafe_allow_html=True,
)

# =========================================
# HERO BANNER
# =========================================
def render_hero_banner():
    hero_html = dedent(
        """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
    html, body {
        margin: 0;
        padding: 0;
        background: transparent;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #eef5ff;
    }

    * { box-sizing: border-box; }

    .hero {
        position: relative;
        overflow: hidden;
        display: grid;
        grid-template-columns: minmax(0, 1.55fr) minmax(260px, 0.95fr);
        gap: 16px;
        padding: 22px;
        border-radius: 30px;
        border: 1px solid rgba(255,255,255,0.10);
        background:
            radial-gradient(circle at top right, rgba(116, 89, 255, 0.22), transparent 32%),
            linear-gradient(135deg, rgba(40, 86, 200, 0.44), rgba(8, 102, 139, 0.24));
        box-shadow: 0 22px 60px rgba(0,0,0,0.28);
    }

    .hero::after {
        content: "";
        position: absolute;
        right: -50px;
        bottom: -60px;
        width: 220px;
        height: 220px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(45, 226, 208, 0.12), transparent 65%);
        pointer-events: none;
    }

    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: #c7ddff;
        margin-bottom: 12px;
    }

    .eyebrow::before {
        content: "";
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: linear-gradient(135deg, #60a5fa, #22d3ee);
        box-shadow: 0 0 12px rgba(34, 211, 238, 0.55);
    }

    .brand-row {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .logo-wrap {
        width: 88px;
        height: 88px;
        flex: 0 0 auto;
    }

    .title {
        margin: 0;
        font-size: clamp(30px, 4.2vw, 44px);
        line-height: 1.02;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #ffffff;
    }

    .subtitle {
        margin-top: 10px;
        font-size: 16px;
        line-height: 1.65;
        color: #cad9f2;
        max-width: 680px;
    }

    .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 16px;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        padding: 9px 13px;
        border-radius: 999px;
        background: rgba(255,255,255,0.075);
        border: 1px solid rgba(255,255,255,0.09);
        color: #f0f7ff;
        font-size: 13px;
    }

    .side {
        display: grid;
        gap: 12px;
    }

    .mini-card {
        background: linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.03));
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 20px;
        padding: 16px;
        box-shadow: 0 12px 28px rgba(0,0,0,0.16);
    }

    .mini-label {
        color: #bbd6ff;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        margin-bottom: 8px;
    }

    .mini-value {
        color: white;
        font-weight: 700;
        font-size: 18px;
        margin-bottom: 6px;
    }

    .mini-text {
        color: #c9daf4;
        font-size: 14px;
        line-height: 1.55;
    }

    @media (max-width: 860px) {
        .hero {
            grid-template-columns: 1fr;
            padding: 18px;
        }

        .brand-row {
            align-items: flex-start;
        }

        .logo-wrap {
            width: 72px;
            height: 72px;
        }
    }
</style>
</head>
<body>
    <div class="hero">
        <div>
            <div class="eyebrow">ELMAHDI AI • PREMIUM WORKSPACE</div>
            <div class="brand-row">
                <div class="logo-wrap">__SVG__</div>
                <div>
                    <h1 class="title">ELMAHDI HELPER</h1>
                    <div class="subtitle">
                        Smart chat, document Q&amp;A, and image generation in one clean app.
                    </div>
                </div>
            </div>

            <div class="pill-row">
                <span class="pill">Creator: Elmahdi Oukassou</span>
                <span class="pill">Fast replies</span>
                <span class="pill">Document upload</span>
                <span class="pill">Image generator</span>
            </div>
        </div>

        <div class="side">
            <div class="mini-card">
                <div class="mini-label">Brand style</div>
                <div class="mini-value">Modern glass + neon accent</div>
                <div class="mini-text">
                    Clean contrast, strong logo treatment, and a more premium visual identity.
                </div>
            </div>

            <div class="mini-card">
                <div class="mini-label">Built for</div>
                <div class="mini-value">Chat, docs, and images</div>
                <div class="mini-text">
                    Better tabs, better spacing, cleaner inputs, and a more polished overall feel.
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""
    ).replace("__SVG__", BRAND_SVG)

    components.html(hero_html, height=320, scrolling=False)


render_hero_banner()

# =========================================
# SECRETS
# Keep these exact names in Streamlit Secrets:
# NVIDIA_API_KEY   = your chat key
# STABILITY_API_KEY = your second NVIDIA key from the FLUX page
# =========================================
CHAT_API_KEY = st.secrets["NVIDIA_API_KEY"] if "NVIDIA_API_KEY" in st.secrets else None
IMAGE_API_KEY = st.secrets["STABILITY_API_KEY"] if "STABILITY_API_KEY" in st.secrets else None

chat_client = None
if CHAT_API_KEY:
    chat_client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=CHAT_API_KEY,
    )

# =========================================
# PROMPTS / PRESETS
# =========================================
SYSTEM_PROMPT = """
You are ELMAHDI HELPER, a helpful and friendly AI assistant created by Elmahdi Oukassou.

Rules:
- If asked who created you, answer exactly: "I was created by Elmahdi Oukassou, a developer."
- If asked what model you are, who you are, or what AI powers you, answer exactly: "I'm MHD 1.0, a new AI model created by Elmahdi Oukassou."
- Never mention GPT, GPT-4, OpenAI, NVIDIA, or any other company behind your responses.
- Never say you are based on another company's model.
- Never show internal reasoning, chain-of-thought, or <think> tags.
- Give clear final answers only.
- Be concise, useful, and friendly.
""".strip()

STYLE_PRESETS = {
    "Balanced": "",
    "Cinematic": "cinematic lighting, dramatic composition, clean framing, detailed background",
    "Realistic": "photorealistic, natural lighting, realistic textures, sharp focus",
    "Anime": "anime style, vibrant colors, expressive faces, cel shading",
    "Fantasy": "fantasy art, magical atmosphere, epic composition, highly detailed illustration",
}

# =========================================
# HELPERS
# =========================================
def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def clean_reply(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL).strip()


def typewriter_markdown(placeholder, text: str, delay: float = 0.012):
    if not text:
        placeholder.markdown("")
        return

    if len(text) > 1400:
        placeholder.markdown(text)
        return

    parts = re.split(r"(\s+)", text)
    built = ""
    for part in parts:
        built += part
        if part.strip():
            placeholder.markdown(built)
            time.sleep(delay)
    placeholder.markdown(built)


def ask_chat(messages, max_tokens: int = 1000) -> str:
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
    raw = uploaded_file.getvalue()
    name = uploaded_file.name.lower()

    if name.endswith(".txt") or name.endswith(".csv"):
        return raw.decode("utf-8", errors="ignore")

    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw))
        parts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                parts.append(page_text)
        return "\n\n".join(parts)

    if name.endswith(".docx"):
        doc = Document(io.BytesIO(raw))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    return ""


def build_image_prompt(user_prompt: str, style_label: str, avoid_text: str) -> str:
    parts = []
    preset = STYLE_PRESETS.get(style_label, "")
    if preset:
        parts.append(preset)
    parts.append(user_prompt.strip())
    if avoid_text.strip():
        parts.append(f"avoid {avoid_text.strip()}")
    return ", ".join([p for p in parts if p])


def extract_image_bytes(data: dict) -> bytes:
    if isinstance(data, dict):
        if isinstance(data.get("artifacts"), list) and data["artifacts"]:
            first = data["artifacts"][0]

            if isinstance(first, dict):
                if first.get("finishReason") == "CONTENT_FILTERED":
                    raise RuntimeError(
                        "This prompt was blocked by the safety filter. Try a more generic prompt (no real people)."
                    )

                if first.get("base64"):
                    return base64.b64decode(first["base64"])

        if isinstance(data.get("data"), list) and data["data"]:
            first = data["data"][0]
            if isinstance(first, dict) and first.get("b64_json"):
                return base64.b64decode(first["b64_json"])

        if data.get("image"):
            return base64.b64decode(data["image"])

        if data.get("b64_json"):
            return base64.b64decode(data["b64_json"])

    raise RuntimeError(f"Unexpected image response format: {data}")


def generate_flux_image(user_prompt: str, style_label: str, avoid_text: str, seed: int) -> bytes:
    if not IMAGE_API_KEY:
        raise RuntimeError("Missing STABILITY_API_KEY in Streamlit Secrets.")

    payload = {
        "prompt": build_image_prompt(user_prompt, style_label, avoid_text),
        "seed": int(seed),
        "steps": 4,
    }

    headers = {
        "Authorization": f"Bearer {IMAGE_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    last_error = None

    for attempt in range(2):
        response = requests.post(
            FLUX_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=180,
        )

        if response.status_code == 200:
            return extract_image_bytes(response.json())

        try:
            detail = response.json()
        except Exception:
            detail = response.text

        last_error = f"{response.status_code}: {detail}"

        if response.status_code >= 500 and attempt == 0:
            time.sleep(1.1)
            continue

        break

    raise RuntimeError(last_error or "Unknown image generation error.")

# =========================================
# STATE
# =========================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_image_bytes" not in st.session_state:
    st.session_state.last_image_bytes = None

if "last_image_prompt" not in st.session_state:
    st.session_state.last_image_prompt = ""

# =========================================
# FEATURE ROW
# =========================================
f1, f2, f3 = st.columns(3, gap="large")
with f1:
    st.info("💬 **Chat assistant**\n\nCleaner conversation flow with better spacing and contrast.")
with f2:
    st.info("📄 **Document workspace**\n\nUpload files, preview extracted text, and ask focused questions.")
with f3:
    st.info("🎨 **Image studio**\n\nGenerate visuals in a cleaner, more branded workspace.")

# =========================================
# SIDEBAR
# =========================================
with st.sidebar:
    st.image(LOGO_FILE, width=76)
    st.markdown("## ELMAHDI HELPER")
    st.caption("Premium AI workspace for chat, documents, and images.")

    st.divider()

    st.markdown("### Control panel")
    image_style = st.selectbox("Image style", list(STYLE_PRESETS.keys()), index=1)
    image_seed = st.number_input("Image seed (0 = random)", min_value=0, value=0, step=1)

    if st.button("Clear chat history", use_container_width=True):
        st.session_state.chat_history = []
        safe_rerun()

    st.divider()
    st.markdown("### Status")

    if CHAT_API_KEY:
        st.success("Chat key loaded")
    else:
        st.warning("Missing NVIDIA_API_KEY")

    if IMAGE_API_KEY:
        st.success("Image key loaded")
    else:
        st.warning("Missing STABILITY_API_KEY")

# =========================================
# TABS
# =========================================
chat_tab, doc_tab, image_tab = st.tabs(["💬 Chat", "📄 Document Q&A", "🎨 Generate Image"])

# =========================================
# CHAT TAB
# =========================================
with chat_tab:
    st.subheader("Chat assistant")
    st.caption("Ask questions, brainstorm ideas, or get quick help.")

    if not CHAT_API_KEY:
        st.info("Add NVIDIA_API_KEY in Streamlit Secrets to use chat.")
    else:
        for msg in st.session_state.chat_history:
            avatar = "🧑" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        if user_text := st.chat_input("Message ELMAHDI HELPER"):
            st.session_state.chat_history.append({"role": "user", "content": user_text})

            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_text)

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(st.session_state.chat_history[-12:])

            with st.chat_message("assistant", avatar="🤖"):
                answer_box = st.empty()
                try:
                    with st.spinner("Thinking..."):
                        reply = ask_chat(messages, max_tokens=1000)
                except Exception as e:
                    reply = f"Error: {e}"

                typewriter_markdown(answer_box, reply)

            st.session_state.chat_history.append({"role": "assistant", "content": reply})

# =========================================
# DOCUMENT TAB
# =========================================
with doc_tab:
    st.subheader("Document Q&A")
    st.caption("Upload TXT, CSV, PDF, or DOCX and ask questions about the content.")

    if not CHAT_API_KEY:
        st.info("Add NVIDIA_API_KEY in Streamlit Secrets to use document Q&A.")
    else:
        uploaded_doc = st.file_uploader(
            "Upload TXT, CSV, PDF, or DOCX",
            type=["txt", "csv", "pdf", "docx"],
            key="doc_uploader",
        )

        doc_question = st.text_area(
            "What do you want from the document?",
            placeholder="Summarize this / explain the key points / extract important dates",
            height=120,
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
                    st.code(doc_text[:3500], language="text")

                if st.button("Analyze document", use_container_width=True):
                    if not doc_question.strip():
                        st.warning("Write a question first.")
                    else:
                        messages = [
                            {
                                "role": "system",
                                "content": SYSTEM_PROMPT + "\nUse the uploaded document when answering.",
                            },
                            {
                                "role": "user",
                                "content": f"Document content:\n\n{doc_text[:50000]}\n\nQuestion:\n{doc_question}",
                            },
                        ]

                        answer_box = st.empty()
                        try:
                            with st.spinner("Reading document..."):
                                answer = ask_chat(messages, max_tokens=1200)
                        except Exception as e:
                            answer = f"Error: {e}"

                        typewriter_markdown(answer_box, answer, delay=0.009)
            else:
                st.warning("No readable text was extracted from this file.")

# =========================================
# IMAGE TAB
# =========================================
with image_tab:
    st.subheader("Image studio")
    st.caption("Describe what you want, choose a style, and generate an image.")

    if not IMAGE_API_KEY:
        st.info("Add STABILITY_API_KEY in Streamlit Secrets to use image generation.")
    else:
        left, right = st.columns([1.05, 1], gap="large")

        with left:
            prompt = st.text_area(
                "Describe the image you want",
                placeholder="A futuristic Moroccan city at sunset, cinematic lighting, ultra detailed",
                height=140,
            )

            avoid_text = st.text_input(
                "Things to avoid (optional)",
                placeholder="blurry, low quality, bad hands, watermark",
            )

            if st.button("Generate image", use_container_width=True):
                if not prompt.strip():
                    st.warning("Write a prompt first.")
                else:
                    try:
                        with st.spinner("Generating image..."):
                            image_bytes = generate_flux_image(
                                user_prompt=prompt,
                                style_label=image_style,
                                avoid_text=avoid_text,
                                seed=image_seed,
                            )
                        st.session_state.last_image_bytes = image_bytes
                        st.session_state.last_image_prompt = prompt
                    except Exception as e:
                        st.session_state.last_image_bytes = None
                        st.error(f"Image generation failed: {e}")

        with right:
            if st.session_state.last_image_bytes:
                st.image(
                    st.session_state.last_image_bytes,
                    caption=st.session_state.last_image_prompt,
                    use_container_width=True,
                )
                st.download_button(
                    "Download image",
                    data=st.session_state.last_image_bytes,
                    file_name="elmahdi-helper-image.png",
                    mime="image/png",
                    use_container_width=True,
                )
            else:
                p1, p2 = st.columns([1, 4])
                with p1:
                    st.image(LOGO_FILE, width=64)
                with p2:
                    st.markdown("#### Image preview")
                    st.caption("Your generated image will appear here.")
