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


def brand_logo_html(size: int = 56, show_text: bool = True, compact: bool = False) -> str:
    text_html = (
        """
        <div class="brand-meta">
            <div class="brand-kicker">Elmahdi AI</div>
            <div class="brand-name">ELMAHDI HELPER</div>
        </div>
        """
        if show_text
        else ""
    )

    compact_class = "compact" if compact else ""

    return f"""
    <div class="brand-lockup {compact_class}">
        <div class="brand-logo" style="width:{size}px;height:{size}px;">
            <svg viewBox="0 0 72 72" width="{size}" height="{size}" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <circle cx="54" cy="18" r="7" fill="#7dd3fc" opacity="0.95"/>
                <path d="M24 20H48" stroke="white" stroke-width="7" stroke-linecap="round"/>
                <path d="M24 36H43" stroke="white" stroke-width="7" stroke-linecap="round"/>
                <path d="M24 52H48" stroke="white" stroke-width="7" stroke-linecap="round"/>
                <path d="M24 20V52" stroke="white" stroke-width="7" stroke-linecap="round"/>
            </svg>
        </div>
        {text_html}
    </div>
    """


# =========================================
# STYLING
# =========================================
st.markdown(
    """
    <style>
        :root {
            --bg-1: #050914;
            --bg-2: #0a1220;
            --panel: rgba(255,255,255,0.05);
            --panel-strong: rgba(11, 18, 31, 0.88);
            --border: rgba(255,255,255,0.09);
            --text: #eef5ff;
            --muted: #bfd0ea;
            --muted-2: #8ea6cb;
            --blue: #60a5fa;
            --cyan: #22d3ee;
            --violet: #8b5cf6;
            --shadow: 0 20px 60px rgba(0,0,0,0.28);
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 10%, rgba(96, 165, 250, 0.18), transparent 24%),
                radial-gradient(circle at 88% 6%, rgba(139, 92, 246, 0.16), transparent 22%),
                radial-gradient(circle at 50% 100%, rgba(34, 211, 238, 0.10), transparent 30%),
                linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%);
            color: var(--text);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background: rgba(7, 12, 22, 0.9);
            border-right: 1px solid var(--border);
        }

        .block-container {
            max-width: 1240px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        .brand-side-card,
        .hero,
        .feature-strip,
        [data-testid="stChatMessage"],
        .card {
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        .brand-side-card {
            position: relative;
            overflow: hidden;
            padding: 1rem 1rem 0.9rem 1rem;
            border: 1px solid var(--border);
            border-radius: 22px;
            background: linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.03));
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }

        .brand-side-card::after,
        .hero::after {
            content: "";
            position: absolute;
            inset: auto -15% -35% auto;
            width: 220px;
            height: 220px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(125, 211, 252, 0.18), transparent 60%);
            pointer-events: none;
        }

        .brand-lockup {
            display: flex;
            align-items: center;
            gap: 0.9rem;
        }

        .brand-lockup.compact {
            gap: 0.75rem;
        }

        .brand-logo {
            position: relative;
            flex: 0 0 auto;
            display: grid;
            place-items: center;
            border-radius: 22px;
            background: linear-gradient(135deg, #4338ca 0%, #0ea5e9 55%, #22d3ee 100%);
            box-shadow:
                inset 0 1px 0 rgba(255,255,255,0.18),
                0 18px 35px rgba(37, 99, 235, 0.28);
            border: 1px solid rgba(255,255,255,0.12);
        }

        .brand-logo::before {
            content: "";
            position: absolute;
            inset: 1px;
            border-radius: 21px;
            background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0));
            pointer-events: none;
        }

        .brand-kicker {
            font-size: 0.78rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #b8d6ff;
            margin-bottom: 0.12rem;
        }

        .brand-name {
            color: #ffffff;
            font-weight: 800;
            letter-spacing: 0.02em;
            font-size: 1.02rem;
        }

        .brand-side-card p {
            color: var(--muted);
            font-size: 0.93rem;
            margin: 0.8rem 0 0 0;
            line-height: 1.45;
        }

        .hero {
            position: relative;
            overflow: hidden;
            display: grid;
            grid-template-columns: minmax(0, 1.55fr) minmax(280px, 0.9fr);
            gap: 1rem;
            align-items: stretch;
            background: linear-gradient(135deg, rgba(37, 99, 235, 0.20), rgba(14, 165, 233, 0.10));
            border: 1px solid var(--border);
            border-radius: 28px;
            padding: 1.35rem;
            box-shadow: var(--shadow);
            margin-bottom: 0.95rem;
        }

        .hero-copy {
            position: relative;
            z-index: 1;
        }

        .hero-logo-row {
            margin-bottom: 0.6rem;
        }

        .eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.78rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #c5dbff;
            margin-bottom: 0.6rem;
        }

        .eyebrow::before {
            content: "";
            width: 0.55rem;
            height: 0.55rem;
            border-radius: 999px;
            background: linear-gradient(135deg, var(--blue), var(--cyan));
            box-shadow: 0 0 14px rgba(34, 211, 238, 0.65);
        }

        .hero h1 {
            margin: 0;
            font-size: clamp(2rem, 3vw, 3rem);
            line-height: 1.02;
            color: #f8fbff;
        }

        .hero p {
            margin: 0.72rem 0 0 0;
            color: var(--muted);
            font-size: 1.02rem;
            line-height: 1.6;
            max-width: 700px;
        }

        .pill-row {
            margin-top: 1rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
        }

        .pill {
            display: inline-flex;
            align-items: center;
            gap: 0.42rem;
            padding: 0.46rem 0.82rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.065);
            border: 1px solid rgba(255,255,255,0.08);
            color: #eef5ff;
            font-size: 0.91rem;
        }

        .pill::before {
            content: "✦";
            color: #8be9ff;
            font-size: 0.8rem;
        }

        .hero-side {
            display: grid;
            gap: 0.75rem;
        }

        .hero-mini-card,
        .feature-card,
        .status-item {
            background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 0.95rem 1rem;
            box-shadow: 0 12px 30px rgba(0,0,0,0.16);
        }

        .mini-label {
            color: #b9d3ff;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.35rem;
        }

        .mini-value {
            color: white;
            font-size: 1.06rem;
            font-weight: 700;
            margin-bottom: 0.28rem;
        }

        .mini-meta {
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.5;
        }

        .feature-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 0 0 1rem 0;
        }

        .feature-card h3 {
            margin: 0 0 0.28rem 0;
            color: #f7fbff;
            font-size: 1rem;
        }

        .feature-card p {
            margin: 0;
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.5;
        }

        .feature-icon {
            display: inline-grid;
            place-items: center;
            width: 2.2rem;
            height: 2.2rem;
            border-radius: 14px;
            margin-bottom: 0.7rem;
            font-size: 1.05rem;
            background: linear-gradient(135deg, rgba(79,70,229,0.36), rgba(6,182,212,0.28));
            border: 1px solid rgba(255,255,255,0.08);
        }

        .section-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin: 0.1rem 0 0.85rem 0;
        }

        .section-title h2 {
            margin: 0;
            color: #f7fbff;
            font-size: 1.05rem;
            font-weight: 700;
        }

        .section-title p {
            margin: 0.15rem 0 0 0;
            color: var(--muted-2);
            font-size: 0.92rem;
        }

        div[data-baseweb="tab-list"] {
            gap: 0.55rem;
            margin-bottom: 0.9rem;
        }

        button[data-baseweb="tab"] {
            border-radius: 14px !important;
            padding: 0.55rem 1rem !important;
            background: rgba(255,255,255,0.03) !important;
            border: 1px solid rgba(255,255,255,0.06) !important;
            color: #d7e6ff !important;
            transition: 0.2s ease;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, rgba(79,70,229,0.34), rgba(6,182,212,0.28)) !important;
            border-color: rgba(125, 211, 252, 0.24) !important;
            color: white !important;
            box-shadow: 0 10px 24px rgba(79,70,229,0.18);
        }

        [data-testid="stChatMessage"] {
            background: linear-gradient(180deg, rgba(255,255,255,0.045), rgba(255,255,255,0.028));
            border: 1px solid rgba(255,255,255,0.065);
            border-radius: 20px;
            padding: 0.55rem 0.85rem;
            box-shadow: 0 10px 28px rgba(0,0,0,0.12);
        }

        [data-testid="stChatInput"] {
            background: rgba(8, 14, 24, 0.75);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 18px;
            padding: 0.15rem;
        }

        .loader-wrap {
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.8rem 1rem;
            border-radius: 16px;
            background: rgba(255,255,255,0.045);
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 10px 28px rgba(0,0,0,0.16);
            margin: 0.2rem 0 0.45rem 0;
        }

        .loader-text {
            color: #dce9ff;
            font-size: 0.96rem;
        }

        .dots {
            display: inline-flex;
            gap: 0.3rem;
        }

        .dots span {
            width: 0.5rem;
            height: 0.5rem;
            border-radius: 50%;
            background: linear-gradient(135deg, #60a5fa, #22d3ee);
            animation: blink 1.15s infinite ease-in-out;
        }

        .dots span:nth-child(2) { animation-delay: 0.15s; }
        .dots span:nth-child(3) { animation-delay: 0.3s; }

        @keyframes blink {
            0%, 80%, 100% { transform: scale(0.72); opacity: 0.35; }
            40% { transform: scale(1); opacity: 1; }
        }

        .preview-shell {
            min-height: 380px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: #b9c8e7;
        }

        .shimmer {
            width: 100%;
            min-height: 380px;
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.08);
            background:
                linear-gradient(
                    110deg,
                    rgba(255,255,255,0.04) 8%,
                    rgba(255,255,255,0.10) 18%,
                    rgba(255,255,255,0.04) 33%
                );
            background-size: 200% 100%;
            animation: shimmer 1.2s linear infinite;
        }

        @keyframes shimmer {
            to { background-position-x: -200%; }
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

        [data-testid="stMarkdownContainer"] code {
            color: #d8e7ff;
        }

        .status-stack {
            display: grid;
            gap: 0.65rem;
            margin-top: 0.55rem;
        }

        .status-item {
            padding: 0.75rem 0.85rem;
            border-radius: 16px;
        }

        .status-top {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            color: #f6fbff;
            font-size: 0.93rem;
            font-weight: 600;
            margin-bottom: 0.15rem;
        }

        .status-dot {
            width: 0.62rem;
            height: 0.62rem;
            border-radius: 999px;
            display: inline-block;
        }

        .status-dot.ok {
            background: #22c55e;
            box-shadow: 0 0 14px rgba(34, 197, 94, 0.45);
        }

        .status-dot.off {
            background: #f59e0b;
            box-shadow: 0 0 14px rgba(245, 158, 11, 0.38);
        }

        .status-sub {
            color: var(--muted-2);
            font-size: 0.82rem;
            line-height: 1.45;
        }

        .subtle-note {
            color: var(--muted-2);
            font-size: 0.84rem;
            margin-top: 0.55rem;
        }

        footer { visibility: hidden; }
        #MainMenu { visibility: hidden; }

        @media (max-width: 980px) {
            .hero,
            .feature-strip {
                grid-template-columns: 1fr;
            }

            .hero {
                padding: 1.15rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="hero">
        <div class="hero-copy">
            <div class="eyebrow">Premium AI workspace</div>
            <div class="hero-logo-row">
                {brand_logo_html(size=64, show_text=True)}
            </div>
            <h1>Smart chat, document Q&amp;A, and image generation in one clean app.</h1>
            <p>
                A more polished, modern interface with stronger branding, better contrast,
                cleaner spacing, and a safer glass-style design that still keeps your original app logic intact.
            </p>
            <div class="pill-row">
                <span class="pill">Creator: Elmahdi Oukassou</span>
                <span class="pill">Fast replies</span>
                <span class="pill">Doc upload</span>
                <span class="pill">Image generator</span>
            </div>
        </div>
        <div class="hero-side">
            <div class="hero-mini-card">
                <div class="mini-label">Brand style</div>
                <div class="mini-value">Modern glass + neon accent</div>
                <div class="mini-meta">Inline logo mark, higher readability, and safer visual polish without touching your API flow.</div>
            </div>
            <div class="hero-mini-card">
                <div class="mini-label">Built for</div>
                <div class="mini-value">Chat, docs, and images</div>
                <div class="mini-meta">Tabs, cards, loaders, inputs, and preview areas now feel more consistent across the whole app.</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="feature-strip">
        <div class="feature-card">
            <div class="feature-icon">💬</div>
            <h3>Conversational UI</h3>
            <p>Cleaner chat bubbles, better tab focus, and a smoother input area that feels more premium.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📄</div>
            <h3>Document workspace</h3>
            <p>Sharper uploader styling and a neater text preview so long files feel easier to inspect.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🎨</div>
            <h3>Image studio</h3>
            <p>A more polished preview panel and branded empty state that matches the rest of the interface.</p>
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

        # NVIDIA / Stability format
        if isinstance(data.get("artifacts"), list) and data["artifacts"]:
            first = data["artifacts"][0]

            if isinstance(first, dict):

                # Handle blocked content
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
        f"""
        <div class="brand-side-card">
            {brand_logo_html(size=50, show_text=True, compact=True)}
            <p>
                A branded AI assistant with a cleaner visual system, safer contrast,
                and a stronger identity without changing your core app behavior.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Control panel")
    image_style = st.selectbox("Image style", list(STYLE_PRESETS.keys()), index=1)
    image_seed = st.number_input("Image seed (0 = random)", min_value=0, value=0, step=1)

    if st.button("Clear chat history", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

    st.markdown("---")
    st.markdown("### Status")

    st.markdown(
        f"""
        <div class="status-stack">
            <div class="status-item">
                <div class="status-top">
                    <span class="status-dot {'ok' if CHAT_API_KEY else 'off'}"></span>
                    Chat service
                </div>
                <div class="status-sub">{'Connected and ready' if CHAT_API_KEY else 'Missing NVIDIA_API_KEY'}</div>
            </div>
            <div class="status-item">
                <div class="status-top">
                    <span class="status-dot {'ok' if IMAGE_API_KEY else 'off'}"></span>
                    Image service
                </div>
                <div class="status-sub">{'Connected and ready' if IMAGE_API_KEY else 'Missing STABILITY_API_KEY'}</div>
            </div>
        </div>
        <div class="subtle-note">Tip: keep prompts specific for better image results and clearer document answers.</div>
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
    st.markdown(
        """
        <div class="section-title">
            <div>
                <h2>Chat assistant</h2>
                <p>Ask questions, brainstorm ideas, or get quick help in a cleaner conversation view.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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
    st.markdown(
        """
        <div class="section-title">
            <div>
                <h2>Document Q&amp;A</h2>
                <p>Upload a file, preview extracted text, and ask focused questions about the content.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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
    st.markdown(
        """
        <div class="section-title">
            <div>
                <h2>Image studio</h2>
                <p>Describe your idea, pick a style, and generate images in a cleaner branded workspace.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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
                    <div class="card preview-shell">
                        <div>
                            <h3 style="margin:0 0 0.5rem 0; color:#eef6ff;">Image preview</h3>
                            <p style="margin:0; color:#bfd0ea; line-height:1.6;">
                                Your generated image will appear here with the new branded preview style.
                            </p>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
