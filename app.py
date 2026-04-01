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
    page_icon="✦",
    layout="wide",
)

# =========================================
# STYLING — Luxury Dark Edition
# =========================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;700&family=IBM+Plex+Sans:wght@300;400;500&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">

<style>
:root {
    --ink:        #09090b;
    --ink-2:      #111115;
    --ink-3:      #18181d;
    --ink-4:      #222228;
    --gold:       #c9a84c;
    --gold-dim:   #9b7d35;
    --gold-glow:  rgba(201,168,76,0.18);
    --gold-pale:  rgba(201,168,76,0.07);
    --silver:     #a8afc4;
    --silver-dim: #5a6075;
    --white:      #f2f0eb;
    --border:     rgba(255,255,255,0.06);
    --border-gold:rgba(201,168,76,0.25);
    --r:          16px;
    --r-sm:       10px;
}

*, *::before, *::after { box-sizing: border-box; }

/* ── BASE ── */
.stApp {
    background: var(--ink);
    color: var(--white);
    font-family: 'IBM Plex Sans', sans-serif;
}

/* animated grain */
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    z-index: 9999;
    pointer-events: none;
    opacity: 0.022;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 512 512' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    animation: grain 0.8s steps(2) infinite;
}
@keyframes grain {
    0%,100%{ transform: translate(0,0); }
    25%    { transform: translate(-1%,-1%); }
    50%    { transform: translate(1%,1%); }
    75%    { transform: translate(-1%,1%); }
}

/* top vignette */
.stApp::after {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 220px;
    background: radial-gradient(ellipse 80% 100% at 50% -10%, rgba(201,168,76,0.09), transparent);
    pointer-events: none;
    z-index: 0;
}

[data-testid="stHeader"]          { background: transparent !important; }
[data-testid="stAppViewContainer"]{ position: relative; z-index: 1; }

.block-container {
    max-width: 1200px;
    padding-top: 1.5rem;
    padding-bottom: 4rem;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--ink-2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { font-family: 'IBM Plex Sans', sans-serif !important; }

.sidebar-section {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--silver-dim);
    margin: 1.2rem 0 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.sidebar-section::after {
    content: "";
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* status dots */
.status-row {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    margin: 0.35rem 0;
    font-size: 0.83rem;
    color: var(--silver);
}
.dot-ok  { width:7px;height:7px;border-radius:50%;background:#4ade80;box-shadow:0 0 6px rgba(74,222,128,0.5); }
.dot-err { width:7px;height:7px;border-radius:50%;background:#f87171;box-shadow:0 0 6px rgba(248,113,113,0.5); }

/* ── HERO ── */
.hero {
    position: relative;
    border-radius: 22px;
    padding: 2.4rem 2.6rem 2rem;
    margin-bottom: 1.8rem;
    background: linear-gradient(145deg, var(--ink-3) 0%, var(--ink-4) 100%);
    border: 1px solid var(--border-gold);
    overflow: hidden;
    animation: heroIn 0.7s cubic-bezier(0.22,1,0.36,1) both;
}
@keyframes heroIn {
    from { opacity:0; transform: translateY(16px); }
    to   { opacity:1; transform: translateY(0); }
}

/* gold shimmer line */
.hero::before {
    content: "";
    position: absolute;
    top: 0; left: 8%; right: 8%;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold) 40%, var(--gold-dim) 60%, transparent);
    opacity: 0.7;
}
/* bottom-right decorative circle */
.hero::after {
    content: "";
    position: absolute;
    bottom: -80px; right: -80px;
    width: 280px; height: 280px;
    border-radius: 50%;
    border: 1px solid var(--border-gold);
    opacity: 0.3;
    pointer-events: none;
}

.hero-kicker {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.hero-kicker::before {
    content: "✦";
    font-size: 0.65rem;
}

.hero h1 {
    margin: 0 0 0.5rem 0;
    font-family: 'Playfair Display', serif;
    font-size: 3rem;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.02em;
    color: var(--white);
}
.hero h1 span {
    background: linear-gradient(120deg, var(--gold) 0%, #e8c96a 50%, var(--gold-dim) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.hero-sub {
    font-size: 0.98rem;
    color: var(--silver);
    font-weight: 300;
    margin: 0 0 1.3rem 0;
    line-height: 1.6;
    max-width: 520px;
}

.tag-row { display: flex; flex-wrap: wrap; gap: 0.45rem; }
.tag {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.3rem 0.75rem;
    border-radius: 999px;
    background: var(--gold-pale);
    border: 1px solid var(--border-gold);
    color: var(--gold);
    font-size: 0.78rem;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.04em;
    font-weight: 400;
    transition: background 0.2s, color 0.2s;
}
.tag:hover {
    background: rgba(201,168,76,0.14);
    color: #e8c96a;
}

/* ── TABS ── */
div[data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0.2rem !important;
    margin-bottom: 1.4rem !important;
    padding-bottom: 0 !important;
}
div[data-baseweb="tab"] {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 400 !important;
    color: var(--silver-dim) !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 0.55rem 1.2rem !important;
    background: transparent !important;
    border: none !important;
    transition: color 0.18s !important;
    letter-spacing: 0.01em !important;
}
div[data-baseweb="tab"]:hover { color: var(--silver) !important; }
div[aria-selected="true"][data-baseweb="tab"] {
    color: var(--white) !important;
    background: var(--gold-pale) !important;
}
div[data-baseweb="tab-highlight"] {
    background: var(--gold) !important;
    height: 1.5px !important;
}

/* ── CHAT MESSAGES ── */
[data-testid="stChatMessage"] {
    background: var(--ink-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    padding: 0.85rem 1.1rem !important;
    margin-bottom: 0.5rem;
    transition: border-color 0.2s !important;
    animation: msgIn 0.35s ease both;
}
@keyframes msgIn {
    from { opacity:0; transform: translateY(8px); }
    to   { opacity:1; transform: translateY(0); }
}
[data-testid="stChatMessage"]:hover { border-color: var(--border-gold) !important; }

/* User message left border */
div:has([data-testid="chatAvatarIcon-user"]) {
    border-left: 2px solid var(--gold) !important;
    border-radius: var(--r) !important;
}

/* Chat input */
[data-testid="stChatInput"] textarea {
    background: var(--ink-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    color: var(--white) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.93rem !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--border-gold) !important;
    box-shadow: 0 0 0 3px var(--gold-glow) !important;
}
[data-testid="stChatInput"] {
    background: var(--ink-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--border-gold) !important;
    box-shadow: 0 0 0 3px var(--gold-glow) !important;
}

/* ── LOADER ── */
.loader-wrap {
    display: inline-flex;
    align-items: center;
    gap: 1rem;
    padding: 0.9rem 1.2rem;
    border-radius: var(--r);
    background: var(--ink-3);
    border: 1px solid var(--border-gold);
    box-shadow: 0 0 20px var(--gold-glow);
    margin: 0.4rem 0 0.6rem;
}
.loader-text {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    letter-spacing: 0.06em;
    color: var(--gold);
}
.dots { display: inline-flex; gap: 0.3rem; align-items: center; }
.dots span {
    width: 0.4rem; height: 0.4rem;
    border-radius: 50%;
    background: var(--gold);
    animation: dotPulse 1.3s infinite ease-in-out;
}
.dots span:nth-child(2) { animation-delay: 0.2s; }
.dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotPulse {
    0%,80%,100% { transform: scale(0.55); opacity: 0.25; }
    40%          { transform: scale(1.1);  opacity: 1; }
}

/* ── CARDS ── */
.card {
    background: var(--ink-3);
    border: 1px solid var(--border);
    border-radius: var(--r);
    padding: 1.3rem;
    transition: border-color 0.2s;
}
.card:hover { border-color: var(--border-gold); }

.preview-shell {
    min-height: 380px;
    display: flex; align-items: center; justify-content: center;
    text-align: center;
    flex-direction: column;
    gap: 1rem;
}
.preview-glyph {
    font-family: 'Playfair Display', serif;
    font-size: 3.5rem;
    color: var(--silver-dim);
    line-height: 1;
    opacity: 0.35;
}
.preview-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.15rem;
    font-weight: 500;
    color: var(--silver);
    margin: 0;
}
.preview-sub {
    font-size: 0.84rem;
    color: var(--silver-dim);
    margin: 0;
}

/* ── SHIMMER ── */
.shimmer {
    width: 100%; min-height: 380px;
    border-radius: var(--r);
    border: 1px solid var(--border-gold);
    background: linear-gradient(110deg,
        var(--ink-3) 8%,
        rgba(201,168,76,0.06) 18%,
        var(--ink-3) 33%);
    background-size: 200% 100%;
    animation: shimmer 1.4s linear infinite;
}
@keyframes shimmer { to { background-position-x: -200%; } }

/* ── BUTTONS ── */
.stButton > button, .stDownloadButton > button {
    border-radius: var(--r-sm) !important;
    background: transparent !important;
    border: 1px solid var(--border-gold) !important;
    color: var(--gold) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 0.65rem 1.4rem !important;
    transition: all 0.2s ease !important;
    position: relative !important;
    overflow: hidden !important;
}
.stButton > button::before, .stDownloadButton > button::before {
    content: "" !important;
    position: absolute !important;
    inset: 0 !important;
    background: var(--gold-pale) !important;
    opacity: 0 !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    color: var(--white) !important;
    border-color: var(--gold) !important;
    background: var(--gold-pale) !important;
    box-shadow: 0 0 20px var(--gold-glow) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active, .stDownloadButton > button:active {
    transform: translateY(0) !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stTextArea > div > textarea,
.stNumberInput > div > div > input {
    background: var(--ink-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-sm) !important;
    color: var(--white) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.92rem !important;
    transition: border-color 0.18s, box-shadow 0.18s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > textarea:focus,
.stNumberInput > div > div > input:focus {
    border-color: var(--border-gold) !important;
    box-shadow: 0 0 0 3px var(--gold-glow) !important;
    outline: none !important;
}
.stTextInput label, .stTextArea label, .stNumberInput label,
.stSelectbox label, .stFileUploader label {
    color: var(--silver-dim) !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: var(--ink-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-sm) !important;
    color: var(--white) !important;
}

/* File uploader */
[data-testid="stFileUploader"] > div {
    background: var(--ink-3) !important;
    border: 1px dashed var(--border-gold) !important;
    border-radius: var(--r) !important;
    transition: all 0.2s !important;
}
[data-testid="stFileUploader"] > div:hover {
    background: var(--gold-pale) !important;
    border-color: var(--gold) !important;
    box-shadow: 0 0 20px var(--gold-glow) !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: var(--ink-3) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-sm) !important;
}

/* Alerts */
.stAlert {
    border-radius: var(--r-sm) !important;
    border: 1px solid var(--border-gold) !important;
    background: var(--gold-pale) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}

/* Divider */
hr { border-color: var(--border) !important; }

footer   { visibility: hidden; }
#MainMenu{ visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-kicker">Elmahdi AI &nbsp;·&nbsp; MHD 1.0</div>
    <h1><span>Elmahdi</span> Helper</h1>
    <p class="hero-sub">
        Chat with an intelligent assistant, interrogate documents,<br>
        and generate images — all from a single interface.
    </p>
    <div class="tag-row">
        <span class="tag">✦ Elmahdi Oukassou</span>
        <span class="tag">⚡ Fast replies</span>
        <span class="tag">📄 Doc Q&amp;A</span>
        <span class="tag">🎨 Image gen</span>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================
# SECRETS
# =========================================
CHAT_API_KEY  = st.secrets.get("NVIDIA_API_KEY", None)
IMAGE_API_KEY = st.secrets.get("STABILITY_API_KEY", None)

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
- If asked who created you: "I was created by Elmahdi Oukassou, a developer."
- If asked what model you are: "I'm MHD 1.0, a new AI model created by Elmahdi Oukassou."
- Never mention GPT, GPT-4, OpenAI, NVIDIA, or any other company behind your responses.
- Never say you are based on another company's model.
- Never show internal reasoning, chain-of-thought, or <think> tags.
- Give clear final answers only. Be concise, useful, and friendly.
""".strip()

STYLE_PRESETS = {
    "Balanced":  "",
    "Cinematic": "cinematic lighting, dramatic composition, clean framing, detailed background",
    "Realistic": "photorealistic, natural lighting, realistic textures, sharp focus",
    "Anime":     "anime style, vibrant colors, expressive faces, cel shading",
    "Fantasy":   "fantasy art, magical atmosphere, epic composition, highly detailed illustration",
}

# =========================================
# HELPERS
# =========================================
def clean_reply(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL).strip()

def show_loader(container, label: str):
    container.markdown(f"""
    <div class="loader-wrap">
        <div class="dots"><span></span><span></span><span></span></div>
        <div class="loader-text">{label}</div>
    </div>
    """, unsafe_allow_html=True)

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
    raw  = uploaded_file.getvalue()
    name = uploaded_file.name.lower()
    if name.endswith((".txt", ".csv")):
        return raw.decode("utf-8", errors="ignore")
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw))
        return "\n\n".join(
            (p.extract_text() or "").strip()
            for p in reader.pages if (p.extract_text() or "").strip()
        )
    if name.endswith(".docx"):
        doc = Document(io.BytesIO(raw))
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

def build_image_prompt(user_prompt, style_label, avoid_text):
    parts = [p for p in [
        STYLE_PRESETS.get(style_label, ""),
        user_prompt.strip(),
        f"avoid {avoid_text.strip()}" if avoid_text.strip() else "",
    ] if p]
    return ", ".join(parts)

def extract_image_bytes(data: dict) -> bytes:
    if isinstance(data, dict):
        if isinstance(data.get("artifacts"), list) and data["artifacts"]:
            first = data["artifacts"][0]
            if isinstance(first, dict):
                if first.get("finishReason") == "CONTENT_FILTERED":
                    raise RuntimeError("Prompt blocked by safety filter. Try a more generic prompt.")
                if first.get("base64"):
                    return base64.b64decode(first["base64"])
        if isinstance(data.get("data"), list) and data["data"]:
            f = data["data"][0]
            if isinstance(f, dict) and f.get("b64_json"):
                return base64.b64decode(f["b64_json"])
        if data.get("image"):    return base64.b64decode(data["image"])
        if data.get("b64_json"): return base64.b64decode(data["b64_json"])
    raise RuntimeError(f"Unexpected image response format: {data}")

def generate_flux_image(user_prompt, style_label, avoid_text, seed) -> bytes:
    if not IMAGE_API_KEY:
        raise RuntimeError("Missing STABILITY_API_KEY in Streamlit Secrets.")
    payload = {"prompt": build_image_prompt(user_prompt, style_label, avoid_text),
               "seed": int(seed), "steps": 4}
    headers = {"Authorization": f"Bearer {IMAGE_API_KEY}",
               "Accept": "application/json", "Content-Type": "application/json"}
    last_error = None
    for attempt in range(2):
        r = requests.post(FLUX_ENDPOINT, headers=headers, json=payload, timeout=180)
        if r.status_code == 200:
            return extract_image_bytes(r.json())
        try:    detail = r.json()
        except: detail = r.text
        last_error = f"{r.status_code}: {detail}"
        if r.status_code >= 500 and attempt == 0:
            time.sleep(1.1); continue
        break
    raise RuntimeError(last_error or "Unknown image generation error.")

# =========================================
# STATE
# =========================================
if "chat_history"      not in st.session_state: st.session_state.chat_history      = []
if "last_image_bytes"  not in st.session_state: st.session_state.last_image_bytes  = None
if "last_image_prompt" not in st.session_state: st.session_state.last_image_prompt = ""

# =========================================
# SIDEBAR
# =========================================
with st.sidebar:
    st.markdown('<div class="sidebar-section">Controls</div>', unsafe_allow_html=True)
    image_style = st.selectbox("Image style", list(STYLE_PRESETS.keys()), index=1)
    image_seed  = st.number_input("Seed  (0 = random)", min_value=0, value=0, step=1)

    st.markdown('<div class="sidebar-section">Actions</div>', unsafe_allow_html=True)
    if st.button("Clear chat history", use_container_width=True):
        st.session_state.chat_history = []

    st.markdown('<div class="sidebar-section">System</div>', unsafe_allow_html=True)
    ok_chat  = '<div class="status-row"><div class="dot-ok"></div>Chat key loaded</div>'
    err_chat = '<div class="status-row"><div class="dot-err"></div>Missing NVIDIA_API_KEY</div>'
    ok_img   = '<div class="status-row"><div class="dot-ok"></div>Image key loaded</div>'
    err_img  = '<div class="status-row"><div class="dot-err"></div>Missing STABILITY_API_KEY</div>'
    st.markdown(ok_chat  if CHAT_API_KEY  else err_chat, unsafe_allow_html=True)
    st.markdown(ok_img   if IMAGE_API_KEY else err_img,  unsafe_allow_html=True)

# =========================================
# TABS
# =========================================
chat_tab, doc_tab, image_tab = st.tabs(["  💬  Chat  ", "  📄  Documents  ", "  🎨  Image Gen  "])

# ── CHAT ──────────────────────────────────────────────────────────
with chat_tab:
    if not CHAT_API_KEY:
        st.info("Add NVIDIA_API_KEY in Streamlit Secrets to enable chat.")
    else:
        for msg in st.session_state.chat_history:
            avatar = "🧑" if msg["role"] == "user" else "✦"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        if user_text := st.chat_input("Ask me anything…"):
            st.session_state.chat_history.append({"role": "user", "content": user_text})
            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_text)

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(st.session_state.chat_history[-12:])

            with st.chat_message("assistant", avatar="✦"):
                loader_box = st.empty()
                answer_box = st.empty()
                show_loader(loader_box, "Processing…")
                try:
                    reply = ask_chat(messages, max_tokens=1000)
                except Exception as e:
                    reply = f"Error: {e}"
                loader_box.empty()
                typewriter_markdown(answer_box, reply)

            st.session_state.chat_history.append({"role": "assistant", "content": reply})

# ── DOCUMENTS ─────────────────────────────────────────────────────
with doc_tab:
    if not CHAT_API_KEY:
        st.info("Add NVIDIA_API_KEY in Streamlit Secrets to enable document Q&A.")
    else:
        uploaded_doc = st.file_uploader(
            "Upload TXT, CSV, PDF, or DOCX",
            type=["txt", "csv", "pdf", "docx"],
            key="doc_uploader",
        )
        doc_question = st.text_area(
            "Your question",
            placeholder="Summarize this / explain key points / extract important dates…",
            height=110,
        )

        if uploaded_doc is not None:
            st.success(f"✓  {uploaded_doc.name}")
            try:    doc_text = read_document(uploaded_doc)
            except Exception as e:
                doc_text = ""
                st.error(f"Could not read file: {e}")

            if doc_text.strip():
                with st.expander("Preview extracted text"):
                    st.text(doc_text[:3500])

                if st.button("Analyze document", use_container_width=True):
                    if not doc_question.strip():
                        st.warning("Please write a question first.")
                    else:
                        messages = [
                            {"role": "system",
                             "content": SYSTEM_PROMPT + "\nUse the uploaded document when answering."},
                            {"role": "user",
                             "content": f"Document content:\n\n{doc_text[:50000]}\n\nQuestion:\n{doc_question}"},
                        ]
                        loader_box = st.empty()
                        answer_box = st.empty()
                        show_loader(loader_box, "Reading document…")
                        try:    answer = ask_chat(messages, max_tokens=1200)
                        except Exception as e: answer = f"Error: {e}"
                        loader_box.empty()
                        typewriter_markdown(answer_box, answer, delay=0.009)
            else:
                st.warning("No readable text was extracted from this file.")

# ── IMAGE GEN ─────────────────────────────────────────────────────
with image_tab:
    if not IMAGE_API_KEY:
        st.info("Add STABILITY_API_KEY in Streamlit Secrets to enable image generation.")
    else:
        left, right = st.columns([1.05, 1], gap="large")

        with left:
            prompt = st.text_area(
                "Image description",
                placeholder="A futuristic Moroccan medina at golden hour, cinematic lighting, ultra detailed…",
                height=140,
            )
            avoid_text = st.text_input(
                "Negative prompt (optional)",
                placeholder="blurry, low quality, bad hands, watermark",
            )
            if st.button("✦  Generate image", use_container_width=True):
                if not prompt.strip():
                    st.warning("Enter a description first.")
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
                        st.session_state.last_image_bytes  = image_bytes
                        st.session_state.last_image_prompt = prompt
                    except Exception as e:
                        st.session_state.last_image_bytes = None
                        with right: preview_box.empty()
                        st.error(f"Generation failed: {e}")

        with right:
            if st.session_state.last_image_bytes:
                st.image(
                    st.session_state.last_image_bytes,
                    caption=st.session_state.last_image_prompt,
                    use_container_width=True,
                )
                st.download_button(
                    "⬇  Download image",
                    data=st.session_state.last_image_bytes,
                    file_name="elmahdi-helper.png",
                    mime="image/png",
                    use_container_width=True,
                )
            else:
                st.markdown("""
                <div class="card preview-shell">
                    <div class="preview-glyph">✦</div>
                    <p class="preview-title">Image preview</p>
                    <p class="preview-sub">Your generated image will appear here.</p>
                </div>
                """, unsafe_allow_html=True)
