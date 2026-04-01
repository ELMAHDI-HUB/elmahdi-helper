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
    <style>
        :root {
            --bg-1: #050816;
            --bg-2: #0a1120;
            --surface: rgba(12, 18, 34, 0.68);
            --surface-2: rgba(255, 255, 255, 0.045);
            --surface-3: rgba(255, 255, 255, 0.07);
            --border: rgba(255, 255, 255, 0.08);
            --text-main: #eef5ff;
            --text-soft: #bfd0ea;
            --text-dim: #8ea4c9;
            --blue: #5ea7ff;
            --cyan: #39d5ff;
            --violet: #9b7bff;
            --shadow-lg: 0 26px 70px rgba(0, 0, 0, 0.34);
            --shadow-md: 0 18px 42px rgba(0, 0, 0, 0.24);
        }

        .stApp {
            background:
                radial-gradient(circle at 10% 10%, rgba(62, 131, 255, 0.18), transparent 28%),
                radial-gradient(circle at 92% 10%, rgba(162, 93, 255, 0.16), transparent 25%),
                radial-gradient(circle at 50% 120%, rgba(34, 211, 238, 0.12), transparent 26%),
                linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 50%, #07101c 100%);
            color: var(--text-main);
            position: relative;
            overflow-x: hidden;
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image:
                linear-gradient(rgba(255,255,255,0.026) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.026) 1px, transparent 1px);
            background-size: 46px 46px;
            mask-image: linear-gradient(180deg, rgba(255,255,255,0.28), transparent 78%);
            opacity: 0.28;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(9, 14, 28, 0.96), rgba(8, 13, 24, 0.9));
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
        }

        .block-container {
            max-width: 1240px;
            padding-top: 1.15rem;
            padding-bottom: 2.4rem;
        }

        .hero {
            position: relative;
            overflow: hidden;
            padding: 1.6rem;
            border-radius: 30px;
            border: 1px solid rgba(255,255,255,0.09);
            background:
                linear-gradient(135deg, rgba(22, 56, 119, 0.74), rgba(15, 89, 123, 0.52) 45%, rgba(64, 28, 115, 0.52) 100%);
            box-shadow: var(--shadow-lg);
            backdrop-filter: blur(14px);
            margin-bottom: 1.2rem;
            isolation: isolate;
        }

        .hero::before {
            content: "";
            position: absolute;
            inset: -32% auto auto -10%;
            width: 320px;
            height: 320px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(255,255,255,0.2), transparent 58%);
            pointer-events: none;
            z-index: -1;
        }

        .hero::after {
            content: "";
            position: absolute;
            right: -90px;
            top: -60px;
            width: 280px;
            height: 280px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(34, 211, 238, 0.2), transparent 62%);
            pointer-events: none;
            z-index: -1;
        }

        .hero-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.45fr) minmax(300px, 0.9fr);
            gap: 1.1rem;
            align-items: stretch;
        }

        .hero-kicker {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.46rem 0.78rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.14);
            color: #dceaff;
            font-size: 0.82rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.8rem;
            width: fit-content;
        }

        .hero h1 {
            margin: 0;
            font-size: clamp(2.15rem, 5vw, 3.4rem);
            line-height: 0.98;
            letter-spacing: -0.04em;
            color: #fbfdff;
        }

        .hero p {
            margin: 0.88rem 0 0 0;
            max-width: 760px;
            color: #d6e5ff;
            font-size: 1.03rem;
            line-height: 1.72;
        }

        .pill-row {
            margin-top: 1rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.58rem;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.5rem 0.86rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            color: #eef6ff;
            font-size: 0.92rem;
            backdrop-filter: blur(10px);
        }

        .hero-stack {
            display: grid;
            gap: 0.85rem;
            align-content: center;
        }

        .hero-stat-card {
            border-radius: 22px;
            padding: 1rem 1.05rem;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            box-shadow: 0 16px 36px rgba(4, 10, 24, 0.2);
            backdrop-filter: blur(14px);
        }

        .hero-stat-label {
            font-size: 0.8rem;
            color: #d5e4ff;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }

        .hero-stat-value {
            font-size: 1.02rem;
            color: #ffffff;
            font-weight: 700;
            line-height: 1.45;
        }

        .hero-stat-sub {
            margin-top: 0.28rem;
            font-size: 0.9rem;
            color: #c3d7f7;
            line-height: 1.45;
        }

        .section-intro {
            margin: 0.2rem 0 1rem 0;
            padding: 1.05rem 1.12rem;
            border-radius: 22px;
            background: var(--surface);
            border: 1px solid var(--border);
            box-shadow: var(--shadow-md);
            backdrop-filter: blur(14px);
        }

        .section-kicker {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            color: #91b7ff;
            margin-bottom: 0.32rem;
        }

        .section-title {
            margin: 0;
            font-size: 1.22rem;
            color: #f8fbff;
            line-height: 1.2;
        }

        .section-text {
            margin: 0.46rem 0 0 0;
            color: var(--text-soft);
            font-size: 0.98rem;
            line-height: 1.64;
        }

        .sidebar-card {
            padding: 1rem;
            border-radius: 20px;
            background: rgba(255,255,255,0.045);
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: var(--shadow-md);
            margin-bottom: 1rem;
        }

        .sidebar-card h3 {
            margin: 0 0 0.35rem 0;
            color: #f4f8ff;
            font-size: 1rem;
        }

        .sidebar-card p {
            margin: 0;
            color: var(--text-soft);
            font-size: 0.92rem;
            line-height: 1.6;
        }

        .status-stack {
            display: grid;
            gap: 0.6rem;
        }

        .status-pill {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.6rem;
            padding: 0.72rem 0.86rem;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.045);
            color: #edf5ff;
            font-size: 0.92rem;
        }

        .status-pill span:last-child {
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            padding: 0.24rem 0.5rem;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.08);
        }

        .status-pill.ok span:last-child {
            background: rgba(52, 211, 153, 0.14);
            color: #95ffcf;
        }

        .status-pill.warn span:last-child {
            background: rgba(251, 191, 36, 0.14);
            color: #ffe08a;
        }

        div[data-baseweb="tab-list"] {
            gap: 0.55rem;
            padding: 0.48rem;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 18px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
            margin-bottom: 0.95rem;
        }

        button[role="tab"] {
            border-radius: 14px !important;
            padding: 0.58rem 1rem !important;
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid transparent !important;
            color: #cfe0fb !important;
            transition: all 0.22s ease !important;
        }

        button[role="tab"]:hover {
            color: #ffffff !important;
            border-color: rgba(255,255,255,0.08) !important;
            transform: translateY(-1px);
        }

        button[role="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.95), rgba(6, 182, 212, 0.9)) !important;
            color: white !important;
            box-shadow: 0 10px 24px rgba(10, 26, 60, 0.34);
        }

        .stButton button,
        .stDownloadButton button {
            border-radius: 16px !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            background: linear-gradient(135deg, #5b4df0, #06b6d4) !important;
            color: white !important;
            font-weight: 700 !important;
            padding-top: 0.7rem !important;
            padding-bottom: 0.7rem !important;
            box-shadow: 0 18px 34px rgba(10, 26, 60, 0.3) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease !important;
        }

        .stButton button:hover,
        .stDownloadButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 22px 36px rgba(10, 26, 60, 0.4) !important;
        }

        .stTextInput > div > div > input,
        .stNumberInput input,
        .stTextArea textarea,
        div[data-baseweb="select"] > div,
        .stFileUploader > div {
            border-radius: 16px !important;
            border: 1px solid rgba(255,255,255,0.09) !important;
            background: rgba(255,255,255,0.045) !important;
            color: var(--text-main) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
        }

        .stTextInput > div > div > input,
        .stNumberInput input,
        .stTextArea textarea {
            padding-top: 0.16rem !important;
            padding-bottom: 0.16rem !important;
        }

        .stTextArea textarea {
            line-height: 1.6 !important;
        }

        .stTextInput > div > div > input:focus,
        .stNumberInput input:focus,
        .stTextArea textarea:focus {
            border-color: rgba(94, 167, 255, 0.5) !important;
            box-shadow: 0 0 0 1px rgba(94, 167, 255, 0.35) !important;
        }

        .stTextInput label,
        .stTextArea label,
        .stSelectbox label,
        .stNumberInput label,
        .stFileUploader label {
            color: #dbe8ff !important;
            font-weight: 600 !important;
        }

        div[data-testid="stFileUploaderDropzone"] {
            border: 1px dashed rgba(122, 182, 255, 0.4) !important;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.015)) !important;
            border-radius: 20px !important;
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }

        div[data-testid="stFileUploaderDropzone"] * {
            color: #dbe8ff !important;
        }

        [data-testid="stChatMessage"] {
            background: rgba(255,255,255,0.038);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 22px;
            padding: 0.65rem 0.85rem;
            box-shadow: 0 16px 36px rgba(0,0,0,0.15);
            backdrop-filter: blur(10px);
            margin-bottom: 0.55rem;
        }

        [data-testid="stChatInput"] {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 0.2rem 0.35rem;
            box-shadow: 0 12px 28px rgba(0,0,0,0.18);
        }

        [data-testid="stChatInput"] textarea {
            color: #eef5ff !important;
        }

        .loader-wrap {
            display: inline-flex;
            align-items: center;
            gap: 0.8rem;
            padding: 0.82rem 1rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 12px 28px rgba(0,0,0,0.16);
            margin: 0.25rem 0 0.45rem 0;
        }

        .loader-text {
            color: #dce9ff;
            font-size: 0.96rem;
        }

        .dots {
            display: inline-flex;
            gap: 0.32rem;
        }

        .dots span {
            width: 0.52rem;
            height: 0.52rem;
            border-radius: 50%;
            background: linear-gradient(135deg, #60a5fa, #22d3ee);
            animation: blink 1.15s infinite ease-in-out;
            box-shadow: 0 0 18px rgba(96, 165, 250, 0.35);
        }

        .dots span:nth-child(2) { animation-delay: 0.15s; }
        .dots span:nth-child(3) { animation-delay: 0.3s; }

        @keyframes blink {
            0%, 80%, 100% { transform: scale(0.72); opacity: 0.38; }
            40% { transform: scale(1); opacity: 1; }
        }

        .preview-shell {
            min-height: 395px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: #b9c8e7;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: var(--shadow-md);
            backdrop-filter: blur(12px);
        }

        .preview-icon {
            width: 78px;
            height: 78px;
            border-radius: 22px;
            margin: 0 auto 0.85rem auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2rem;
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.26), rgba(6, 182, 212, 0.22));
            border: 1px solid rgba(255,255,255,0.08);
        }

        .shimmer {
            width: 100%;
            min-height: 395px;
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.08);
            background:
                linear-gradient(
                    110deg,
                    rgba(255,255,255,0.04) 10%,
                    rgba(255,255,255,0.12) 18%,
                    rgba(255,255,255,0.04) 33%
                );
            background-size: 200% 100%;
            animation: shimmer 1.15s linear infinite;
            box-shadow: var(--shadow-md);
        }

        @keyframes shimmer {
            to { background-position-x: -200%; }
        }

        .stImage img {
            border-radius: 24px !important;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 22px 44px rgba(0,0,0,0.26);
        }

        [data-testid="stExpander"] {
            border: 1px solid rgba(255,255,255,0.08) !important;
            border-radius: 18px !important;
            background: rgba(255,255,255,0.035) !important;
        }

        [data-testid="stAlert"] {
            border-radius: 16px !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
        }

        .stCodeBlock,
        pre,
        code {
            border-radius: 16px !important;
        }

        footer { visibility: hidden; }
        #MainMenu { visibility: hidden; }

        @media (max-width: 980px) {
            .hero-grid {
                grid-template-columns: 1fr;
            }

            .hero {
                padding: 1.28rem;
            }

            .hero h1 {
                font-size: 2.4rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="hero-grid">
            <div>
                <div class="hero-kicker">Elmahdi AI Experience</div>
                <h1>ELMAHDI HELPER 🤖</h1>
                <p>Smart chat, document Q&amp;A, and image generation in one elegant workspace designed to feel faster, clearer, and more premium.</p>
                <div class="pill-row">
                    <span class="pill">Creator: Elmahdi Oukassou</span>
                    <span class="pill">Fast replies</span>
                    <span class="pill">Doc upload</span>
                    <span class="pill">Image generator</span>
                </div>
            </div>
            <div class="hero-stack">
                <div class="hero-stat-card">
                    <div class="hero-stat-label">Workspace</div>
                    <div class="hero-stat-value">Chat • Documents • Images</div>
                    <div class="hero-stat-sub">Everything stays in one clean interface with a stronger visual hierarchy.</div>
                </div>
                <div class="hero-stat-card">
                    <div class="hero-stat-label">Design feel</div>
                    <div class="hero-stat-value">Glassmorphism + neon depth</div>
                    <div class="hero-stat-sub">Sharper contrast, softer surfaces, and more polished interactions.</div>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

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

    # Avoid making huge answers painfully slow
    if len(text) > 1400:
        placeholder.markdown(text)
        return

    parts = re.split(r"(\\s+)", text)
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
        return "\\n\\n".join(parts)

    if name.endswith(".docx"):
        doc = Document(io.BytesIO(raw))
        return "\\n".join(paragraph.text for paragraph in doc.paragraphs)

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

        # NVIDIA / Stability format
        if isinstance(data.get("artifacts"), list) and data["artifacts"]:
            first = data["artifacts"][0]

            if isinstance(first, dict):

                # 🚨 Handle blocked content
                if first.get("finishReason") == "CONTENT_FILTERED":
                    raise RuntimeError(
                        "This prompt was blocked by the safety filter. Try a more generic prompt (no real people)."
                    )

                if first.get("base64"):
                    return base64.b64decode(first["base64"])

        # OpenAI-like format
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

        # Retry once for temporary backend errors
        if response.status_code >= 500 and attempt == 0:
            time.sleep(1.1)
            continue

        break

    raise RuntimeError(last_error or "Unknown image generation error.")



def section_intro(kicker: str, title: str, text: str):
    st.markdown(
        f"""
        <div class="section-intro">
            <div class="section-kicker">{kicker}</div>
            <h2 class="section-title">{title}</h2>
            <p class="section-text">{text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
    st.markdown(
        """
        <div class="sidebar-card">
            <h3>Control panel</h3>
            <p>Tune the image generator, manage your session, and keep the app workspace clean.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    image_style = st.selectbox("Image style", list(STYLE_PRESETS.keys()), index=1)
    image_seed = st.number_input("Image seed (0 = random)", min_value=0, value=0, step=1)

    if st.button("Clear chat history", use_container_width=True):
        st.session_state.chat_history = []

    st.markdown("### Status")
    st.markdown(
        f"""
        <div class="status-stack">
            <div class="status-pill {'ok' if CHAT_API_KEY else 'warn'}">
                <span>Chat access</span>
                <span>{'Ready' if CHAT_API_KEY else 'Missing key'}</span>
            </div>
            <div class="status-pill {'ok' if IMAGE_API_KEY else 'warn'}">
                <span>Image access</span>
                <span>{'Ready' if IMAGE_API_KEY else 'Missing key'}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================
# TABS
# =========================================
chat_tab, doc_tab, image_tab = st.tabs(["💬 Chat", "📄 Document Q&A", "🎨 Generate Image"])

# =========================================
# CHAT TAB
# =========================================
with chat_tab:
    section_intro(
        "Conversation",
        "Chat with ELMAHDI HELPER",
        "Your original chat flow stays the same. This update only improves the visual experience with cleaner message cards, richer spacing, and a more polished input area.",
    )

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
                loader_box = st.empty()
                answer_box = st.empty()
                show_loader(loader_box, "Thinking...")

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
    section_intro(
        "Document Q&A",
        "Upload a file and ask focused questions",
        "The logic is unchanged. The workspace is simply cleaner and easier to scan while reviewing extracted text and generated answers.",
    )

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
                    st.text(doc_text[:3500])

                if st.button("Analyze document", use_container_width=True):
                    if not doc_question.strip():
                        st.warning("Write a question first.")
                    else:
                        messages = [
                            {
                                "role": "system",
                                "content": SYSTEM_PROMPT + "\\nUse the uploaded document when answering.",
                            },
                            {
                                "role": "user",
                                "content": f"Document content:\\n\\n{doc_text[:50000]}\\n\\nQuestion:\\n{doc_question}",
                            },
                        ]

                        loader_box = st.empty()
                        answer_box = st.empty()
                        show_loader(loader_box, "Reading document...")

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
    section_intro(
        "Image Studio",
        "Generate visuals with a more premium preview area",
        "Your prompt flow, style preset, seed handling, and download behavior remain intact. Only the presentation has been upgraded.",
    )

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
                    "Download image",
                    data=st.session_state.last_image_bytes,
                    file_name="elmahdi-helper-image.png",
                    mime="image/png",
                    use_container_width=True,
                )
            else:
                st.markdown(
                    """
                    <div class="preview-shell">
                        <div>
                            <div class="preview-icon">🎨</div>
                            <h3 style="margin:0 0 0.5rem 0; color:#eef6ff;">Preview</h3>
                            <p style="margin:0; color:#bfd0ea; line-height:1.65; max-width:340px;">
                                Your generated image will appear here in a cleaner showcase panel.
                            </p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
    )
