import base64 import io import re import time

import requests import streamlit as st from openai import OpenAI from PyPDF2 import PdfReader from docx import Document

=========================================

CONFIG

=========================================

CHAT_MODEL = "openai/gpt-oss-120b" FLUX_ENDPOINT = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.2-klein-4b"

st.set_page_config( page_title="ELMAHDI HELPER", page_icon="🤖", layout="wide", )

=========================================

SAFE MODERN UI

=========================================

st.markdown( """ <style> :root { --bg-1: #07111f; --bg-2: #0b1728; --panel: rgba(10, 18, 32, 0.78); --panel-strong: rgba(14, 24, 42, 0.92); --stroke: rgba(255,255,255,0.08); --text: #edf4ff; --muted: #a9bddb; --blue: #5aa9ff; --cyan: #49d6ff; --violet: #8b7dff; --shadow: 0 18px 50px rgba(0,0,0,0.28); }

.stApp {
        color: var(--text);
        background:
            radial-gradient(circle at 0% 0%, rgba(90,169,255,0.16), transparent 28%),
            radial-gradient(circle at 100% 0%, rgba(139,125,255,0.14), transparent 26%),
            radial-gradient(circle at 50% 100%, rgba(73,214,255,0.10), transparent 22%),
            linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(8,14,25,0.96), rgba(11,19,33,0.96));
        border-right: 1px solid var(--stroke);
    }

    .block-container {
        max-width: 1220px;
        padding-top: 1.1rem;
        padding-bottom: 2rem;
    }

    .hero {
        position: relative;
        overflow: hidden;
        padding: 1.45rem 1.45rem 1.2rem 1.45rem;
        border-radius: 28px;
        margin-bottom: 1rem;
        background:
            linear-gradient(135deg, rgba(90,169,255,0.16), rgba(139,125,255,0.10)),
            rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.09);
        box-shadow: var(--shadow);
        backdrop-filter: blur(12px);
    }

    .hero::before {
        content: "";
        position: absolute;
        right: -90px;
        top: -90px;
        width: 220px;
        height: 220px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(73,214,255,0.20), transparent 65%);
        pointer-events: none;
    }

    .eyebrow {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        font-size: 0.77rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #c7d7f5;
        margin-bottom: 0.55rem;
        padding: 0.38rem 0.72rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.08);
        width: fit-content;
    }

    .hero h1 {
        margin: 0;
        font-size: 2.45rem;
        line-height: 1.02;
        color: #f7fbff;
        letter-spacing: -0.03em;
    }

    .hero p {
        margin: 0.72rem 0 0 0;
        max-width: 760px;
        color: var(--muted);
        font-size: 1.01rem;
        line-height: 1.55;
    }

    .pill-row {
        margin-top: 1rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.6rem;
    }

    .pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.46rem 0.82rem;
        border-radius: 999px;
        font-size: 0.9rem;
        color: #f0f6ff;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
    }

    .soft-card {
        background: var(--panel);
        border: 1px solid var(--stroke);
        border-radius: 24px;
        padding: 1rem;
        box-shadow: var(--shadow);
        backdrop-filter: blur(12px);
    }

    div[data-baseweb="tab-list"] {
        gap: 0.55rem;
        margin: 0 0 0.8rem 0;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 18px;
        padding: 0.35rem;
    }

    div[data-baseweb="tab"] {
        height: auto !important;
        border-radius: 14px;
        padding: 0.55rem 0.95rem;
        background: transparent;
    }

    button[role="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(79,70,229,0.95), rgba(6,182,212,0.92)) !important;
        color: white !important;
        box-shadow: 0 10px 25px rgba(37,99,235,0.24);
    }

    [data-testid="stChatMessage"] {
        background: rgba(255,255,255,0.035);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 20px;
        padding: 0.55rem 0.85rem;
        box-shadow: 0 8px 22px rgba(0,0,0,0.12);
    }

    [data-testid="stChatInput"] {
        background: transparent;
    }

    .loader-wrap {
        display: inline-flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.8rem 1rem;
        border-radius: 18px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 10px 26px rgba(0,0,0,0.14);
        margin: 0.15rem 0 0.45rem 0;
    }

    .loader-text {
        color: #dbe9ff;
        font-size: 0.96rem;
    }

    .dots {
        display: inline-flex;
        gap: 0.3rem;
    }

    .dots span {
        width: 0.52rem;
        height: 0.52rem;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--blue), var(--cyan));
        animation: pulseDot 1.15s infinite ease-in-out;
    }

    .dots span:nth-child(2) { animation-delay: 0.14s; }
    .dots span:nth-child(3) { animation-delay: 0.28s; }

    @keyframes pulseDot {
        0%, 80%, 100% { transform: scale(0.72); opacity: 0.35; }
        40% { transform: scale(1); opacity: 1; }
    }

    .preview-shell {
        min-height: 380px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        color: var(--muted);
        background: var(--panel);
        border: 1px solid var(--stroke);
        border-radius: 24px;
        box-shadow: var(--shadow);
        padding: 1.2rem;
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
        background-size: 220% 100%;
        animation: shimmer 1.25s linear infinite;
    }

    @keyframes shimmer {
        to { background-position-x: -220%; }
    }

    .stButton button,
    .stDownloadButton button {
        border-radius: 16px !important;
        border: 1px solid rgba(255,255,255,0.07) !important;
        background: linear-gradient(135deg, #4f46e5, #0891b2) !important;
        color: white !important;
        font-weight: 700 !important;
        padding-top: 0.58rem !important;
        padding-bottom: 0.58rem !important;
        box-shadow: 0 14px 24px rgba(37,99,235,0.20);
    }

    .stButton button:hover,
    .stDownloadButton button:hover {
        filter: brightness(1.04);
        transform: translateY(-1px);
    }

    .stTextInput > div > div,
    .stTextArea textarea,
    .stSelectbox > div > div,
    .stNumberInput > div > div,
    .stFileUploader > div,
    div[data-baseweb="select"] > div {
        background: rgba(255,255,255,0.04) !important;
        color: var(--text) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 16px !important;
    }

    .stTextArea textarea {
        min-height: 120px;
    }

    .metric-strip {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 0.95rem 0 0.25rem 0;
    }

    .metric-box {
        padding: 0.9rem 1rem;
        border-radius: 20px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.07);
    }

    .metric-box b {
        display: block;
        font-size: 1rem;
        color: #f7fbff;
        margin-bottom: 0.18rem;
    }

    .metric-box span {
        color: var(--muted);
        font-size: 0.9rem;
    }

    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }

    @media (max-width: 900px) {
        .hero h1 {
            font-size: 1.95rem;
        }

        .metric-strip {
            grid-template-columns: 1fr;
        }
    }
</style>
""",
unsafe_allow_html=True,

)

st.markdown( """ <div class="hero"> <div class="eyebrow">Elmahdi AI • polished interface</div> <h1>ELMAHDI HELPER 🤖</h1> <p>Smart chat, document Q&A, and image generation in one sleek interface with a cleaner, safer layout.</p> <div class="pill-row"> <span class="pill">Creator: Elmahdi Oukassou</span> <span class="pill">Fast replies</span> <span class="pill">Doc upload</span> <span class="pill">Image generator</span> </div> <div class="metric-strip"> <div class="metric-box"><b>Chat</b><span>Modern message bubbles and smoother loading states</span></div> <div class="metric-box"><b>Documents</b><span>Cleaner analysis section with safer spacing</span></div> <div class="metric-box"><b>Images</b><span>Improved preview panel without risky full-screen tricks</span></div> </div> </div> """, unsafe_allow_html=True, )

=========================================

SECRETS

Keep these exact names in Streamlit Secrets:

NVIDIA_API_KEY   = your chat key

STABILITY_API_KEY = your second NVIDIA key from the FLUX page

=========================================

CHAT_API_KEY = st.secrets["NVIDIA_API_KEY"] if "NVIDIA_API_KEY" in st.secrets else None IMAGE_API_KEY = st.secrets["STABILITY_API_KEY"] if "STABILITY_API_KEY" in st.secrets else None

chat_client = None if CHAT_API_KEY: chat_client = OpenAI( base_url="https://integrate.api.nvidia.com/v1", api_key=CHAT_API_KEY, )

=========================================

PROMPTS / PRESETS

=========================================

SYSTEM_PROMPT = """ You are ELMAHDI HELPER, a helpful and friendly AI assistant created by Elmahdi Oukassou.

Rules:

If asked who created you, answer exactly: "I was created by Elmahdi Oukassou, a developer."

If asked what model you are, who you are, or what AI powers you, answer exactly: "I'm MHD 1.0, a new AI model created by Elmahdi Oukassou."

Never mention GPT, GPT-4, OpenAI, NVIDIA, or any other company behind your responses.

Never say you are based on another company's model.

Never show internal reasoning, chain-of-thought, or <think> tags.

Give clear final answers only.

Be concise, useful, and friendly. """.strip()


STYLE_PRESETS = { "Balanced": "", "Cinematic": "cinematic lighting, dramatic composition, clean framing, detailed background", "Realistic": "photorealistic, natural lighting, realistic textures, sharp focus", "Anime": "anime style, vibrant colors, expressive faces, cel shading", "Fantasy": "fantasy art, magical atmosphere, epic composition, highly detailed illustration", }

=========================================

HELPERS

=========================================

def clean_reply(text: str) -> str: if not text: return "" return re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL).strip()

def show_loader(container, label: str): container.markdown( f""" <div class="loader-wrap"> <div class="dots"><span></span><span></span><span></span></div> <div class="loader-text">{label}</div> </div> """, unsafe_allow_html=True, )

def typewriter_markdown(placeholder, text: str, delay: float = 0.012): if not text: placeholder.markdown("") return

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

def ask_chat(messages, max_tokens: int = 1000) -> str: if chat_client is None: raise RuntimeError("Missing NVIDIA_API_KEY in Streamlit Secrets.")

response = chat_client.chat.completions.create(
    model=CHAT_MODEL,
    messages=messages,
    temperature=0.6,
    top_p=0.7,
    max_tokens=max_tokens,
    stream=False,
)
return clean_reply(response.choices[0].message.content or "")

def read_document(uploaded_file) -> str: raw = uploaded_file.getvalue() name = uploaded_file.name.lower()

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

def build_image_prompt(user_prompt: str, style_label: str, avoid_text: str) -> str: parts = [] preset = STYLE_PRESETS.get(style_label, "") if preset: parts.append(preset) parts.append(user_prompt.strip()) if avoid_text.strip(): parts.append(f"avoid {avoid_text.strip()}") return ", ".join([p for p in parts if p])

def extract_image_bytes(data: dict) -> bytes: if isinstance(data, dict): if isinstance(data.get("artifacts"), list) and data["artifacts"]: first = data["artifacts"][0] if isinstance(first, dict): if first.get("finishReason") == "CONTENT_FILTERED": raise RuntimeError( "This prompt was blocked by the safety filter. Try a more generic prompt (no real people)." ) if first.get("base64"): return base64.b64decode(first["base64"])

if isinstance(data.get("data"), list) and data["data"]:
        first = data["data"][0]
        if isinstance(first, dict) and first.get("b64_json"):
            return base64.b64decode(first["b64_json"])

    if data.get("image"):
        return base64.b64decode(data["image"])

    if data.get("b64_json"):
        return base64.b64decode(data["b64_json"])

raise RuntimeError(f"Unexpected image response format: {data}")

def generate_flux_image(user_prompt: str, style_label: str, avoid_text: str, seed: int) -> bytes: if not IMAGE_API_KEY: raise RuntimeError("Missing STABILITY_API_KEY in Streamlit Secrets.")

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

=========================================

STATE

=========================================

if "chat_history" not in st.session_state: st.session_state.chat_history = []

if "last_image_bytes" not in st.session_state: st.session_state.last_image_bytes = None

if "last_image_prompt" not in st.session_state: st.session_state.last_image_prompt = ""

=========================================

SIDEBAR

=========================================

with st.sidebar: st.markdown("### Control panel") st.caption("Tuned for a cleaner look without changing app behavior.")

image_style = st.selectbox("Image style", list(STYLE_PRESETS.keys()), index=1)
image_seed = st.number_input("Image seed (0 = random)", min_value=0, value=0, step=1)

if st.button("Clear chat history", use_container_width=True):
    st.session_state.chat_history = []

st.markdown("---")
st.markdown("### Status")
st.caption("Chat key loaded" if CHAT_API_KEY else "Missing NVIDIA_API_KEY")
st.caption("Image key loaded" if IMAGE_API_KEY else "Missing STABILITY_API_KEY")

=========================================

TABS

=========================================

chat_tab, doc_tab, image_tab = st.tabs(["💬 Chat", "📄 Document Q&A", "🎨 Generate Image"])

=========================================

CHAT TAB

=========================================

with chat_tab: st.markdown('<div class="soft-card">', unsafe_allow_html=True)

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

st.markdown('</div>', unsafe_allow_html=True)

=========================================

DOCUMENT TAB

=========================================

with doc_tab: st.markdown('<div class="soft-card">', unsafe_allow_html=True)

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

st.markdown('</div>', unsafe_allow_html=True)

=========================================

IMAGE TAB

=========================================

with image_tab: st.markdown('<div class="soft-card">', unsafe_allow_html=True)

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
                        <h3 style="margin:0 0 0.5rem 0; color:#eef6ff;">Preview</h3>
                        <p style="margin:0; color:#bfd0ea; line-height:1.6;">
                            Your generated image will appear here.
                        </p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown('</div>', unsafe_allow_html=True)
