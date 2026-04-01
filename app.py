import base64
import io
import re
import time

import requests
import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document

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
# STYLING
# =========================================
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap" rel="stylesheet">

    <style>
        /* ---- FOUNDATIONS ---- */
        :root {
            --bg-base:        #07080d;
            --bg-surface:     #0d1019;
            --bg-card:        rgba(255,255,255,0.032);
            --bg-card-hover:  rgba(255,255,255,0.055);
            --border:         rgba(255,255,255,0.065);
            --border-bright:  rgba(255,255,255,0.13);
            --accent-a:       #5b7fff;
            --accent-b:       #00d2b4;
            --accent-c:       #a259ff;
            --text-primary:   #eef3ff;
            --text-secondary: #8b9cc8;
            --text-muted:     #55607a;
            --glow-a:         rgba(91,127,255,0.22);
            --glow-b:         rgba(0,210,180,0.15);
            --radius-lg:      20px;
            --radius-md:      14px;
            --radius-sm:      10px;
        }

        * { font-family: 'DM Sans', sans-serif; }

        .stApp {
            background: var(--bg-base);
            color: var(--text-primary);
        }

        /* Ambient background orbs */
        .stApp::before {
            content: "";
            position: fixed;
            top: -200px;
            left: -150px;
            width: 700px;
            height: 700px;
            background: radial-gradient(circle, rgba(91,127,255,0.13) 0%, transparent 65%);
            pointer-events: none;
            z-index: 0;
            animation: orbFloat 12s ease-in-out infinite alternate;
        }
        .stApp::after {
            content: "";
            position: fixed;
            bottom: -200px;
            right: -100px;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(162,89,255,0.10) 0%, transparent 65%);
            pointer-events: none;
            z-index: 0;
            animation: orbFloat 16s ease-in-out infinite alternate-reverse;
        }
        @keyframes orbFloat {
            from { transform: translate(0, 0) scale(1); }
            to   { transform: translate(30px, 40px) scale(1.08); }
        }

        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stAppViewContainer"] { position: relative; z-index: 1; }

        /* ---- SIDEBAR ---- */
        [data-testid="stSidebar"] {
            background: rgba(10, 12, 22, 0.96) !important;
            border-right: 1px solid var(--border) !important;
            backdrop-filter: blur(18px);
        }
        [data-testid="stSidebar"] * { font-family: 'DM Sans', sans-serif; }
        [data-testid="stSidebar"] h3 {
            font-family: 'Syne', sans-serif;
            font-weight: 700;
            font-size: 0.85rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--text-muted);
            margin-bottom: 0.8rem;
        }
        [data-testid="stSidebar"] .stCaption {
            font-size: 0.82rem;
            color: var(--text-secondary);
        }

        /* ---- LAYOUT ---- */
        .block-container {
            max-width: 1180px;
            padding-top: 1rem;
            padding-bottom: 3rem;
        }

        /* ---- HERO ---- */
        .hero {
            position: relative;
            overflow: hidden;
            border-radius: 26px;
            padding: 2rem 2.2rem 1.8rem;
            margin-bottom: 1.5rem;
            background: linear-gradient(135deg,
                rgba(91,127,255,0.14) 0%,
                rgba(0,210,180,0.07) 50%,
                rgba(162,89,255,0.10) 100%);
            border: 1px solid var(--border-bright);
            box-shadow:
                0 0 0 1px rgba(91,127,255,0.08),
                0 30px 70px rgba(0,0,0,0.4),
                inset 0 1px 0 rgba(255,255,255,0.06);
        }
        /* Noise texture overlay */
        .hero::before {
            content: "";
            position: absolute;
            inset: 0;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
            border-radius: inherit;
            pointer-events: none;
        }
        /* Glowing accent line at top */
        .hero::after {
            content: "";
            position: absolute;
            top: 0; left: 10%; right: 10%;
            height: 1px;
            background: linear-gradient(90deg,
                transparent,
                var(--accent-a) 30%,
                var(--accent-b) 70%,
                transparent);
            opacity: 0.6;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-family: 'Syne', sans-serif;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--accent-b);
            margin-bottom: 0.6rem;
        }
        .eyebrow::before {
            content: "";
            display: inline-block;
            width: 22px; height: 1.5px;
            background: var(--accent-b);
            border-radius: 4px;
        }

        .hero h1 {
            margin: 0 0 0.5rem 0;
            font-family: 'Syne', sans-serif;
            font-size: 2.6rem;
            font-weight: 800;
            line-height: 1;
            letter-spacing: -0.03em;
            background: linear-gradient(135deg, #ffffff 30%, var(--accent-a) 80%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero p {
            margin: 0;
            font-size: 1.05rem;
            color: var(--text-secondary);
            font-weight: 300;
            letter-spacing: 0.01em;
        }

        .pill-row {
            margin-top: 1.1rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .pill {
            display: inline-flex;
            align-items: center;
            padding: 0.35rem 0.85rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            font-size: 0.83rem;
            font-weight: 400;
            letter-spacing: 0.01em;
            transition: all 0.2s;
        }
        .pill:hover {
            background: rgba(91,127,255,0.12);
            border-color: rgba(91,127,255,0.3);
            color: var(--text-primary);
        }

        /* ---- TABS ---- */
        div[data-baseweb="tab-list"] {
            gap: 0.3rem;
            background: transparent !important;
            border-bottom: 1px solid var(--border) !important;
            padding-bottom: 0 !important;
            margin-bottom: 1.2rem;
        }
        div[data-baseweb="tab"] {
            font-family: 'DM Sans', sans-serif !important;
            font-size: 0.9rem !important;
            font-weight: 500 !important;
            color: var(--text-secondary) !important;
            border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
            padding: 0.55rem 1.1rem !important;
            border: 1px solid transparent !important;
            border-bottom: none !important;
            background: transparent !important;
            transition: all 0.18s ease !important;
        }
        div[data-baseweb="tab"]:hover {
            color: var(--text-primary) !important;
            background: rgba(255,255,255,0.04) !important;
        }
        div[aria-selected="true"][data-baseweb="tab"] {
            color: var(--text-primary) !important;
            background: rgba(91,127,255,0.08) !important;
            border-color: var(--border) !important;
            border-bottom: 1px solid var(--bg-base) !important;
        }
        div[data-baseweb="tab-highlight"] {
            background: var(--accent-a) !important;
            height: 2px !important;
        }

        /* ---- CHAT MESSAGES ---- */
        [data-testid="stChatMessage"] {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-lg) !important;
            padding: 0.8rem 1rem !important;
            margin-bottom: 0.4rem;
            transition: background 0.2s;
        }
        [data-testid="stChatMessage"]:hover {
            background: var(--bg-card-hover) !important;
        }
        /* User messages get a subtle left accent */
        [data-testid="stChatMessage"][data-testid*="user"],
        div[class*="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
            border-left: 2px solid var(--accent-a) !important;
        }

        /* Chat input */
        [data-testid="stChatInput"] {
            border-radius: var(--radius-lg) !important;
            background: rgba(255,255,255,0.04) !important;
            border: 1px solid var(--border-bright) !important;
        }
        [data-testid="stChatInput"]:focus-within {
            border-color: var(--accent-a) !important;
            box-shadow: 0 0 0 3px rgba(91,127,255,0.12) !important;
        }

        /* ---- LOADER ---- */
        .loader-wrap {
            display: inline-flex;
            align-items: center;
            gap: 0.9rem;
            padding: 0.85rem 1.1rem;
            border-radius: var(--radius-lg);
            background: var(--bg-card);
            border: 1px solid var(--border);
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            margin: 0.3rem 0 0.6rem 0;
        }
        .loader-text {
            color: var(--text-secondary);
            font-size: 0.9rem;
            letter-spacing: 0.01em;
        }
        .dots { display: inline-flex; gap: 0.28rem; align-items: center; }
        .dots span {
            width: 0.42rem; height: 0.42rem;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--accent-a), var(--accent-b));
            animation: dotBlink 1.2s infinite ease-in-out;
        }
        .dots span:nth-child(2) { animation-delay: 0.18s; }
        .dots span:nth-child(3) { animation-delay: 0.36s; }
        @keyframes dotBlink {
            0%, 80%, 100% { transform: scale(0.6); opacity: 0.3; }
            40%            { transform: scale(1.1); opacity: 1; }
        }

        /* ---- CARDS ---- */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.2rem;
            box-shadow: 0 12px 36px rgba(0,0,0,0.18);
        }
        .preview-shell {
            min-height: 360px;
            display: flex; align-items: center; justify-content: center;
            text-align: center;
            color: var(--text-muted);
        }
        .preview-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.4;
        }
        .preview-title {
            font-family: 'Syne', sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-secondary);
            margin: 0 0 0.4rem 0;
        }
        .preview-sub {
            font-size: 0.87rem;
            color: var(--text-muted);
            margin: 0;
        }

        /* ---- SHIMMER ---- */
        .shimmer {
            width: 100%; min-height: 360px;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border);
            background: linear-gradient(110deg,
                rgba(255,255,255,0.03) 8%,
                rgba(255,255,255,0.08) 18%,
                rgba(255,255,255,0.03) 33%);
            background-size: 200% 100%;
            animation: shimmer 1.3s linear infinite;
        }
        @keyframes shimmer { to { background-position-x: -200%; } }

        /* ---- BUTTONS ---- */
        .stButton > button, .stDownloadButton > button {
            border-radius: var(--radius-md) !important;
            background: linear-gradient(135deg, var(--accent-a), var(--accent-c)) !important;
            border: none !important;
            color: #fff !important;
            font-family: 'DM Sans', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            letter-spacing: 0.02em !important;
            padding: 0.6rem 1.2rem !important;
            box-shadow: 0 4px 18px rgba(91,127,255,0.3) !important;
            transition: all 0.2s ease !important;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 8px 28px rgba(91,127,255,0.45) !important;
            filter: brightness(1.08) !important;
        }
        .stButton > button:active, .stDownloadButton > button:active {
            transform: translateY(0) !important;
        }

        /* ---- INPUTS ---- */
        .stTextInput > div > div > input,
        .stTextArea > div > textarea,
        .stNumberInput > div > div > input {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-md) !important;
            color: var(--text-primary) !important;
            font-family: 'DM Sans', sans-serif !important;
            font-size: 0.93rem !important;
            transition: border-color 0.18s, box-shadow 0.18s !important;
        }
        .stTextInput > div > div > input:focus,
        .stTextArea > div > textarea:focus,
        .stNumberInput > div > div > input:focus {
            border-color: var(--accent-a) !important;
            box-shadow: 0 0 0 3px rgba(91,127,255,0.12) !important;
            outline: none !important;
        }
        .stTextInput label, .stTextArea label, .stNumberInput label,
        .stSelectbox label, .stFileUploader label {
            color: var(--text-secondary) !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.02em !important;
        }

        /* Selectbox */
        .stSelectbox > div > div {
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-md) !important;
            color: var(--text-primary) !important;
        }

        /* File uploader */
        [data-testid="stFileUploader"] > div {
            background: rgba(255,255,255,0.025) !important;
            border: 2px dashed var(--border-bright) !important;
            border-radius: var(--radius-lg) !important;
            transition: all 0.2s !important;
        }
        [data-testid="stFileUploader"] > div:hover {
            border-color: var(--accent-a) !important;
            background: rgba(91,127,255,0.05) !important;
        }

        /* Expander */
        [data-testid="stExpander"] {
            background: var(--bg-card) !important;
            border: 1px solid var(--border) !important;
            border-radius: var(--radius-md) !important;
        }

        /* Alerts / info */
        .stAlert {
            border-radius: var(--radius-md) !important;
            border: 1px solid var(--border-bright) !important;
            background: rgba(91,127,255,0.07) !important;
        }

        /* Divider */
        hr { border-color: var(--border) !important; }

        /* Success */
        [data-testid="stNotification"] {
            background: rgba(0,210,180,0.08) !important;
            border: 1px solid rgba(0,210,180,0.2) !important;
            border-radius: var(--radius-md) !important;
        }

        footer { visibility: hidden; }
        #MainMenu { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Elmahdi AI · v1.0</div>
        <h1>ELMAHDI HELPER 🤖</h1>
        <p>Smart chat, document Q&amp;A, and AI image generation — all in one place.</p>
        <div class="pill-row">
            <span class="pill">✦ Creator: Elmahdi Oukassou</span>
            <span class="pill">⚡ Fast replies</span>
            <span class="pill">📄 Doc upload</span>
            <span class="pill">🎨 Image generator</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================
# SECRETS
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
def clean_reply(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL).strip()


def show_loader(container, label: str):
    container.markdown(
        f"""
        <div class="loader-wrap">
            <div class="dots"><span></span><span></span><span></span></div>
            <div class="loader-text">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
        response = requests.post(FLUX_ENDPOINT, headers=headers, json=payload, timeout=180)
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
# SIDEBAR
# =========================================
with st.sidebar:
    st.markdown("### ⚙ Control Panel")
    image_style = st.selectbox("Image style", list(STYLE_PRESETS.keys()), index=1)
    image_seed = st.number_input("Seed (0 = random)", min_value=0, value=0, step=1)

    st.markdown("---")

    if st.button("🗑 Clear chat history", use_container_width=True):
        st.session_state.chat_history = []

    st.markdown("---")
    st.markdown("### ◉ Status")
    if CHAT_API_KEY:
        st.caption("✅ Chat key loaded")
    else:
        st.caption("❌ Missing NVIDIA_API_KEY")
    if IMAGE_API_KEY:
        st.caption("✅ Image key loaded")
    else:
        st.caption("❌ Missing STABILITY_API_KEY")

# =========================================
# TABS
# =========================================
chat_tab, doc_tab, image_tab = st.tabs(["💬  Chat", "📄  Document Q&A", "🎨  Generate Image"])

# =========================================
# CHAT TAB
# =========================================
with chat_tab:
    if not CHAT_API_KEY:
        st.info("Add NVIDIA_API_KEY in Streamlit Secrets to use chat.")
    else:
        for msg in st.session_state.chat_history:
            avatar = "🧑" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        if user_text := st.chat_input("Message ELMAHDI HELPER…"):
            st.session_state.chat_history.append({"role": "user", "content": user_text})
            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_text)

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(st.session_state.chat_history[-12:])

            with st.chat_message("assistant", avatar="🤖"):
                loader_box = st.empty()
                answer_box = st.empty()
                show_loader(loader_box, "Thinking…")
                try:
                    reply = ask_chat(messages, max_tokens=1000)
                except Exception as e:
                    reply = f"Error: {e}"
                loader_box.empty()
                typewriter_markdown(answer_box, reply)

            st.session_state.chat_history.append({"role": "assistant", "content": reply})

# =========================================
# DOCUMENT TAB
# =========================================
with doc_tab:
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
            st.success(f"✓ Uploaded: {uploaded_doc.name}")

            try:
                doc_text = read_document(uploaded_doc)
            except Exception as e:
                doc_text = ""
                st.error(f"Could not read the file: {e}")

            if doc_text.strip():
                with st.expander("Preview extracted text"):
                    st.text(doc_text[:3500])

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
                        loader_box = st.empty()
                        answer_box = st.empty()
                        show_loader(loader_box, "Reading document…")
                        try:
                            answer = ask_chat(messages, max_tokens=1200)
                        except Exception as e:
                            answer = f"Error: {e}"
                        loader_box.empty()
                        typewriter_markdown(answer_box, answer, delay=0.009)
            else:
                st.warning("No readable text was extracted from this file.")

# =========================================
# IMAGE TAB
# =========================================
with image_tab:
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

            if st.button("✦ Generate image", use_container_width=True):
                if not prompt.strip():
                    st.warning("Write a prompt first.")
                else:
                    with right:
                        preview_box = st.empty()
                        preview_box.markdown('<div class="shimmer"></div>', unsafe_allow_html=True)
                    try:
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
                        with right:
                            preview_box.empty()
                        st.error(f"Image generation failed: {e}")

        with right:
            if st.session_state.last_image_bytes:
                st.image(
                    st.session_state.last_image_bytes,
                    caption=st.session_state.last_image_prompt,
                    use_container_width=True,
                )
                st.download_button(
                    "⬇ Download image",
                    data=st.session_state.last_image_bytes,
                    file_name="elmahdi-helper-image.png",
                    mime="image/png",
                    use_container_width=True,
                )
            else:
                st.markdown(
                    """
                    <div class="card preview-shell">
                        <div>
                            <div class="preview-icon">🎨</div>
                            <p class="preview-title">Preview</p>
                            <p class="preview-sub">Your generated image will appear here.</p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
