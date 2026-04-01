import base64
import io
import re
import time

import requests
import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document

# ---------------------------------
# CONFIG
# ---------------------------------
CHAT_MODEL = "openai/gpt-oss-120b"
IMAGE_ENDPOINT = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.2-klein-4b"

st.set_page_config(
    page_title="ELMAHDI HELPER",
    page_icon="🤖",
    layout="wide",
)

# ---------------------------------
# STYLING
# ---------------------------------
st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(76, 29, 149, 0.22), transparent 35%),
                radial-gradient(circle at top right, rgba(14, 165, 233, 0.18), transparent 30%),
                linear-gradient(180deg, #050816 0%, #0b1220 100%);
            color: #e5eefb;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background: rgba(10, 15, 28, 0.92);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        .hero {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.22), rgba(14, 165, 233, 0.14));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 24px;
            padding: 1.35rem 1.4rem;
            margin-bottom: 1rem;
            box-shadow: 0 20px 60px rgba(0,0,0,0.24);
        }

        .hero h1 {
            margin: 0;
            font-size: 2.2rem;
            line-height: 1.1;
            color: #f8fbff;
        }

        .hero p {
            margin: 0.5rem 0 0 0;
            color: #bfd0ea;
            font-size: 1rem;
        }

        .pill-row {
            margin-top: 0.95rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .pill {
            display: inline-block;
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            color: #e6eef9;
            font-size: 0.9rem;
        }

        .soft-card {
            background: rgba(255,255,255,0.045);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 1rem 1rem 0.9rem 1rem;
            box-shadow: 0 12px 40px rgba(0,0,0,0.16);
        }

        div[data-baseweb="tab-list"] {
            gap: 0.45rem;
            margin-bottom: 0.75rem;
        }

        div[data-baseweb="tab"] {
            border-radius: 12px;
            padding: 0.45rem 0.9rem;
            background: rgba(255,255,255,0.03);
        }

        button[kind="primary"], .stDownloadButton button, .stButton button {
            border-radius: 14px !important;
            border: 1px solid rgba(255,255,255,0.08) !important;
            background: linear-gradient(135deg, #4f46e5, #0ea5e9) !important;
            color: white !important;
            font-weight: 600 !important;
        }

        .stTextInput > div > div,
        .stTextArea textarea,
        .stSelectbox > div > div,
        .stNumberInput > div > div,
        .stFileUploader > div {
            border-radius: 14px !important;
        }

        [data-testid="stChatMessage"] {
            background: rgba(255,255,255,0.035);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 18px;
            padding: 0.45rem 0.75rem;
        }

        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>ELMAHDI HELPER 🤖</h1>
        <p>Smart chat, document Q&amp;A, and NVIDIA image generation in one clean app.</p>
        <div class="pill-row">
            <span class="pill">Creator: Elmahdi Oukassou</span>
            <span class="pill">Chat: GPT-OSS-120B</span>
            <span class="pill">Images: FLUX.2-klein-4b</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------
# SECRETS
# Keep these names exactly as you already have them:
# NVIDIA_API_KEY = your chat key
# STABILITY_API_KEY = your SECOND NVIDIA key from the FLUX.2 page
# ---------------------------------
CHAT_API_KEY = st.secrets["NVIDIA_API_KEY"] if "NVIDIA_API_KEY" in st.secrets else None
IMAGE_API_KEY = st.secrets["STABILITY_API_KEY"] if "STABILITY_API_KEY" in st.secrets else None

chat_client = None
if CHAT_API_KEY:
    chat_client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=CHAT_API_KEY,
    )

# ---------------------------------
# APP TEXT
# ---------------------------------
SYSTEM_PROMPT = """
You are ELMAHDI HELPER, a helpful and friendly AI assistant created by Elmahdi Oukassou.

Rules:
- If asked who created you, answer: "I was created by Elmahdi Oukassou, a developer."
- Never show chain-of-thought, internal reasoning, or <think> tags.
- Give clean, final answers only.
- Be concise, useful, and friendly.
""".strip()

STYLE_PRESETS = {
    "Balanced": "",
    "Cinematic": "cinematic lighting, dramatic composition, film still, rich shadows, detailed background",
    "Realistic": "photorealistic, natural lighting, realistic skin texture, sharp focus, ultra detailed",
    "Anime": "anime style, cel shading, vibrant colors, expressive faces, detailed background",
    "Fantasy": "fantasy art, magical atmosphere, epic composition, highly detailed illustration",
}

# ---------------------------------
# HELPERS
# ---------------------------------
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
    raw = uploaded_file.getvalue()
    filename = uploaded_file.name.lower()

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
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    return ""


def extract_image_bytes_from_json(data: dict) -> bytes:
    candidates = []

    if isinstance(data, dict):
        if data.get("image"):
            candidates.append(data["image"])
        if data.get("b64_json"):
            candidates.append(data["b64_json"])

        if isinstance(data.get("artifacts"), list) and data["artifacts"]:
            first = data["artifacts"][0]
            if isinstance(first, dict):
                if first.get("base64"):
                    candidates.append(first["base64"])
                if first.get("b64_json"):
                    candidates.append(first["b64_json"])
                if first.get("image"):
                    candidates.append(first["image"])

        if isinstance(data.get("data"), list) and data["data"]:
            first = data["data"][0]
            if isinstance(first, dict):
                if first.get("b64_json"):
                    candidates.append(first["b64_json"])
                if first.get("image"):
                    candidates.append(first["image"])

    for item in candidates:
        if item:
            if item.startswith("data:image"):
                item = item.split(",", 1)[1]
            return base64.b64decode(item)

    raise RuntimeError(f"Unexpected image response format: {data}")


def generate_flux_image(user_prompt: str, style_label: str, avoid_text: str, seed: int) -> bytes:
    if not IMAGE_API_KEY:
        raise RuntimeError("Missing STABILITY_API_KEY in Streamlit Secrets.")

    style_prefix = STYLE_PRESETS.get(style_label, "")
    prompt = user_prompt.strip()
    if style_prefix:
        prompt = f"{style_prefix}, {prompt}"
    if avoid_text.strip():
        prompt = f"{prompt}. Avoid: {avoid_text.strip()}"

    payload = {
        "mode": "Image Generation",
        "prompt": prompt,
        "height": 1024,
        "width": 1024,
        "cfg_scale": 0,
        "samples": 1,
        "seed": int(seed),
        "steps": 4,
        "image": None,
    }

    headers = {
        "Authorization": f"Bearer {IMAGE_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    last_error = None

    for attempt in range(2):
        response = requests.post(
            IMAGE_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=180,
        )

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "").lower()
            if content_type.startswith("image/"):
                return response.content

            data = response.json()
            return extract_image_bytes_from_json(data)

        try:
            detail = response.json()
        except Exception:
            detail = response.text

        last_error = f"{response.status_code}: {detail}"

        # retry once for temporary backend errors
        if response.status_code >= 500 and attempt == 0:
            time.sleep(1.2)
            continue

        break

    raise RuntimeError(last_error or "Unknown image generation error.")


# ---------------------------------
# SESSION STATE
# ---------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_image_bytes" not in st.session_state:
    st.session_state.last_image_bytes = None

if "last_image_prompt" not in st.session_state:
    st.session_state.last_image_prompt = ""

# ---------------------------------
# SIDEBAR
# ---------------------------------
with st.sidebar:
    st.markdown("### App status")
    if CHAT_API_KEY:
        st.success("Chat key loaded")
    else:
        st.warning("Missing NVIDIA_API_KEY")

    if IMAGE_API_KEY:
        st.success("Image key loaded")
    else:
        st.warning("Missing STABILITY_API_KEY")

    st.markdown("### Image settings")
    image_style = st.selectbox("Style preset", list(STYLE_PRESETS.keys()), index=1)
    image_seed = st.number_input("Seed (0 = random)", min_value=0, value=0, step=1)

    if st.button("Clear chat history", use_container_width=True):
        st.session_state.chat_history = []

    st.markdown("---")
    st.caption("Tip: keep document files reasonably small for faster answers.")

# ---------------------------------
# TABS
# ---------------------------------
chat_tab, doc_tab, image_tab = st.tabs(["💬 Chat", "📄 Document Q&A", "🎨 Generate Image"])

# ---------------------------------
# CHAT TAB
# ---------------------------------
with chat_tab:
    if not CHAT_API_KEY:
        st.info("Add NVIDIA_API_KEY in Streamlit Secrets to use chat.")
    else:
        for msg in st.session_state.chat_history:
            avatar = "🧑" if msg["role"] == "user" else "🤖"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask anything..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.chat_message("user", avatar="🧑"):
                st.markdown(prompt)

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

# ---------------------------------
# DOCUMENT TAB
# ---------------------------------
with doc_tab:
    if not CHAT_API_KEY:
        st.info("Add NVIDIA_API_KEY in Streamlit Secrets to use document Q&A.")
    else:
        uploaded_doc = st.file_uploader(
            "Upload a TXT, CSV, PDF, or DOCX file",
            type=["txt", "csv", "pdf", "docx"],
            key="doc_uploader",
        )

        doc_question = st.text_area(
            "What do you want from the document?",
            placeholder="Summarize this / what are the main points / extract dates / explain this simply",
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

                        with st.spinner("Reading document..."):
                            try:
                                answer = ask_chat(messages, max_tokens=1200)
                                st.markdown("### Answer")
                                st.write(answer)
                            except Exception as e:
                                st.error(f"Error: {e}")
            else:
                st.warning("No readable text was extracted from this file.")

# ---------------------------------
# IMAGE TAB
# ---------------------------------
with image_tab:
    if not IMAGE_API_KEY:
        st.info("Add STABILITY_API_KEY in Streamlit Secrets to use image generation.")
    else:
        left, right = st.columns([1, 1.1], gap="large")

        with left:
            prompt = st.text_area(
                "Describe the image you want",
                placeholder="A futuristic Moroccan city at sunset, cinematic lighting, ultra detailed",
                height=140,
            )

            avoid_text = st.text_input(
                "Things to avoid (optional)",
                placeholder="blurry, distorted hands, watermark, low quality",
            )

            st.caption("This version uses FLUX.2-klein-4b at 1024×1024 for stability.")

            if st.button("Generate image", use_container_width=True):
                if not prompt.strip():
                    st.warning("Write a prompt first.")
                else:
                    with st.spinner("Generating image..."):
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
                            st.error(f"Image generation failed: {e}")

        with right:
            if st.session_state.last_image_bytes:
                st.image(
                    st.session_state.last_image_bytes,
                    caption=f"Prompt: {st.session_state.last_image_prompt}",
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
                    <div class="soft-card">
                        <h4 style="margin-top:0;">Preview</h4>
                        <p style="color:#bfd0ea; margin-bottom:0;">
                            Your generated image will appear here after you click <b>Generate image</b>.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
)
