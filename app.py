import base64
import io
import re
import time
from textwrap import dedent

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
JSON2VIDEO_MOVIES_URL = "https://api.json2video.com/v2/movies"

st.set_page_config(
    page_title="ELMAHDI HELPER",
    page_icon="🤖",
    layout="wide",
)

# =========================================
# SAFE STYLING
# =========================================
st.markdown(
    dedent(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(59, 130, 246, 0.18), transparent 30%),
                    radial-gradient(circle at top right, rgba(168, 85, 247, 0.14), transparent 28%),
                    linear-gradient(180deg, #060b16 0%, #0c1320 100%);
                color: #eaf2ff;
            }

            [data-testid="stHeader"] {
                background: transparent;
            }

            [data-testid="stSidebar"] {
                background: rgba(10, 15, 25, 0.92);
                border-right: 1px solid rgba(255,255,255,0.07);
            }

            .block-container {
                max-width: 1200px;
                padding-top: 1.1rem;
                padding-bottom: 2rem;
            }

            div[data-baseweb="tab-list"] {
                gap: 0.45rem;
                margin-bottom: 0.85rem;
            }

            button[data-baseweb="tab"] {
                border-radius: 14px !important;
                background: rgba(255,255,255,0.03) !important;
                border: 1px solid rgba(255,255,255,0.07) !important;
                color: #dce9ff !important;
            }

            button[data-baseweb="tab"][aria-selected="true"] {
                background: linear-gradient(135deg, rgba(79,70,229,0.35), rgba(6,182,212,0.25)) !important;
                color: white !important;
                border-color: rgba(255,255,255,0.12) !important;
            }

            .stButton button, .stDownloadButton button {
                border-radius: 16px !important;
                border: 1px solid rgba(255,255,255,0.08) !important;
                background: linear-gradient(135deg, #4f46e5, #06b6d4) !important;
                color: white !important;
                font-weight: 700 !important;
            }

            .stTextInput input,
            .stTextArea textarea,
            .stNumberInput input {
                background: rgba(8, 14, 24, 0.82) !important;
                color: #eef5ff !important;
                border-radius: 14px !important;
                border: 1px solid rgba(255,255,255,0.08) !important;
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
                background: rgba(255,255,255,0.035);
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 18px;
                padding: 0.45rem 0.75rem;
            }

            footer { visibility: hidden; }
            #MainMenu { visibility: hidden; }
        </style>
        """
    ),
    unsafe_allow_html=True,
)

# =========================================
# SECRETS
# =========================================
CHAT_API_KEY = st.secrets["NVIDIA_API_KEY"] if "NVIDIA_API_KEY" in st.secrets else None
IMAGE_API_KEY = st.secrets["STABILITY_API_KEY"] if "STABILITY_API_KEY" in st.secrets else None
VIDEO_API_KEY = st.secrets["JSON2VIDEO_API_KEY"] if "JSON2VIDEO_API_KEY" in st.secrets else None

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

VIDEO_IMAGE_MODELS = {
    "Flux Schnell (fast)": "flux-schnell",
    "Flux Pro (quality)": "flux-pro",
    "Freepik Classic (illustration)": "freepik-classic",
}

VIDEO_FORMATS = {
    "Portrait 1080x1920": {"width": 1080, "height": 1920, "aspect_ratio": "vertical"},
    "Landscape 1920x1080": {"width": 1920, "height": 1080, "aspect_ratio": "horizontal"},
    "Square 1080x1080": {"width": 1080, "height": 1080, "aspect_ratio": "squared"},
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


def parse_response_json(response: requests.Response) -> dict:
    try:
        return response.json()
    except Exception:
        return {"raw": response.text}


def json2video_headers() -> dict:
    if not VIDEO_API_KEY:
        raise RuntimeError("Missing JSON2VIDEO_API_KEY in Streamlit Secrets.")
    return {
        "x-api-key": VIDEO_API_KEY,
        "Content-Type": "application/json",
    }


def build_video_movie(
    image_prompt: str,
    headline: str,
    subtitle: str,
    duration_seconds: int,
    image_model: str,
    format_label: str,
) -> dict:
    fmt = VIDEO_FORMATS[format_label]
    width = fmt["width"]
    height = fmt["height"]
    aspect_ratio = fmt["aspect_ratio"]

    title_size = "84px" if aspect_ratio == "vertical" else "62px"
    subtitle_size = "34px" if aspect_ratio == "vertical" else "28px"
    pan_direction = "top" if aspect_ratio == "vertical" else "right"

    elements = [
        {
            "type": "image",
            "model": image_model,
            "prompt": image_prompt.strip(),
            "aspect-ratio": aspect_ratio,
            "resize": "fill",
            "duration": duration_seconds,
            "zoom": 3,
            "pan": pan_direction,
        }
    ]

    final_headline = (headline or image_prompt).strip()[:120]
    final_subtitle = subtitle.strip()[:220]

    if final_headline:
        elements.append(
            {
                "type": "text",
                "text": final_headline,
                "settings": {
                    "font-family": "Poppins",
                    "font-size": title_size,
                    "font-weight": "800",
                    "font-color": "#FFFFFF",
                    "text-align": "center",
                    "vertical-position": "center",
                    "horizontal-position": "center",
                    "line-height": "1.08",
                    "padding": "18px 26px",
                    "background-color": "rgba(4, 11, 24, 0.42)",
                    "border-radius": "18px",
                    "text-shadow": "0 10px 30px rgba(0,0,0,0.35)",
                },
            }
        )

    if final_subtitle:
        elements.append(
            {
                "type": "text",
                "text": final_subtitle,
                "settings": {
                    "font-family": "Inter",
                    "font-size": subtitle_size,
                    "font-weight": "600",
                    "font-color": "#F6FAFF",
                    "text-align": "center",
                    "vertical-position": "bottom",
                    "horizontal-position": "center",
                    "line-height": "1.35",
                    "padding": "14px 20px",
                    "background-color": "rgba(4, 11, 24, 0.55)",
                    "border-radius": "16px",
                },
            }
        )

    return {
        "resolution": "custom",
        "width": width,
        "height": height,
        "quality": "high",
        "scenes": [
            {
                "duration": duration_seconds,
                "elements": elements,
            }
        ],
    }


def json2video_create_movie(movie_payload: dict) -> dict:
    response = requests.post(
        JSON2VIDEO_MOVIES_URL,
        headers=json2video_headers(),
        json=movie_payload,
        timeout=120,
    )
    data = parse_response_json(response)

    if response.status_code >= 400:
        raise RuntimeError(f"JSON2Video error {response.status_code}: {data}")

    if not data.get("success"):
        raise RuntimeError(data.get("message") or str(data))

    return data


def json2video_get_movie(project_id: str) -> dict:
    response = requests.get(
        JSON2VIDEO_MOVIES_URL,
        headers={"x-api-key": VIDEO_API_KEY},
        params={"project": project_id},
        timeout=60,
    )
    data = parse_response_json(response)

    if response.status_code >= 400:
        raise RuntimeError(f"JSON2Video error {response.status_code}: {data}")

    if not data.get("success"):
        raise RuntimeError(data.get("message") or str(data))

    return data.get("movie", {})


def store_video_state(movie: dict):
    st.session_state.video_status = movie.get("status", "pending")
    st.session_state.video_message = movie.get("message", "")
    st.session_state.video_url = movie.get("url", "") if movie.get("status") == "done" else ""
    st.session_state.video_result = movie


def reset_video_state():
    st.session_state.video_project_id = ""
    st.session_state.video_status = ""
    st.session_state.video_message = ""
    st.session_state.video_url = ""
    st.session_state.video_result = {}


def poll_video_until_ready(project_id: str, max_checks: int = 12, delay_seconds: int = 5):
    status_box = st.empty()
    progress_box = st.progress(0.0)
    last_movie = {}

    for i in range(max_checks):
        last_movie = json2video_get_movie(project_id)
        status = (last_movie.get("status") or "pending").lower()
        status_box.info(f"Render status: {status} ({i + 1}/{max_checks})")
        progress_box.progress((i + 1) / max_checks)

        if status in {"done", "error"}:
            break

        time.sleep(delay_seconds)

    progress_box.empty()
    return last_movie

# =========================================
# STATE
# =========================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_image_bytes" not in st.session_state:
    st.session_state.last_image_bytes = None

if "last_image_prompt" not in st.session_state:
    st.session_state.last_image_prompt = ""

if "video_project_id" not in st.session_state:
    st.session_state.video_project_id = ""

if "video_status" not in st.session_state:
    st.session_state.video_status = ""

if "video_message" not in st.session_state:
    st.session_state.video_message = ""

if "video_url" not in st.session_state:
    st.session_state.video_url = ""

if "video_result" not in st.session_state:
    st.session_state.video_result = {}

# =========================================
# HEADER
# =========================================
st.title("ELMAHDI HELPER")
st.caption("Smart chat, document Q&A, image generation, and short AI video creation in one clean app.")

card1, card2, card3, card4 = st.columns(4)
with card1:
    st.info("**Creator**\n\nElmahdi Oukassou")
with card2:
    st.info("**Chat**\n\nFast replies")
with card3:
    st.info("**Docs**\n\nUpload and analyze")
with card4:
    st.info("**Media**\n\nImages and short videos")

# =========================================
# SIDEBAR
# =========================================
with st.sidebar:
    st.markdown("### Control panel")
    image_style = st.selectbox("Image style", list(STYLE_PRESETS.keys()), index=1)
    image_seed = st.number_input("Image seed (0 = random)", min_value=0, value=0, step=1)

    if st.button("Clear chat history", use_container_width=True):
        st.session_state.chat_history = []
        safe_rerun()

    st.markdown("---")
    st.markdown("### Status")
    st.caption("Chat key loaded" if CHAT_API_KEY else "Missing NVIDIA_API_KEY")
    st.caption("Image key loaded" if IMAGE_API_KEY else "Missing STABILITY_API_KEY")
    st.caption("Video key loaded" if VIDEO_API_KEY else "Missing JSON2VIDEO_API_KEY")

# =========================================
# TABS
# =========================================
chat_tab, doc_tab, image_tab, video_tab = st.tabs(
    ["💬 Chat", "📄 Document Q&A", "🎨 Generate Image", "🎬 Generate Video"]
)

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
                st.info("Your generated image will appear here.")

# =========================================
# VIDEO TAB
# =========================================
with video_tab:
    st.subheader("Short AI video generator")
    st.caption("This tab creates a short video using an AI-generated image background plus text overlay.")

    if not VIDEO_API_KEY:
        st.info("Add JSON2VIDEO_API_KEY in Streamlit Secrets to use video generation.")
    else:
        left, right = st.columns([1.08, 1], gap="large")

        with left:
            video_prompt = st.text_area(
                "Describe the video background",
                placeholder="A futuristic Moroccan city at sunset, neon lights, cinematic, ultra detailed",
                height=140,
            )

            video_headline = st.text_input(
                "Headline text",
                placeholder="Morocco in 2040",
            )

            video_subtitle = st.text_area(
                "Subtitle / caption (optional)",
                placeholder="Technology, culture, and design in one bold vision.",
                height=90,
            )

            video_format_label = st.selectbox(
                "Video format",
                list(VIDEO_FORMATS.keys()),
                index=0,
            )

            video_model_label = st.selectbox(
                "Background AI model",
                list(VIDEO_IMAGE_MODELS.keys()),
                index=0,
            )

            video_duration = st.slider(
                "Video length (seconds)",
                min_value=4,
                max_value=12,
                value=6,
            )

            if st.button("Generate video", use_container_width=True):
                if not video_prompt.strip():
                    st.warning("Write a video prompt first.")
                else:
                    try:
                        movie_payload = build_video_movie(
                            image_prompt=video_prompt,
                            headline=video_headline,
                            subtitle=video_subtitle,
                            duration_seconds=video_duration,
                            image_model=VIDEO_IMAGE_MODELS[video_model_label],
                            format_label=video_format_label,
                        )

                        with st.spinner("Submitting video render..."):
                            created = json2video_create_movie(movie_payload)

                        project_id = created.get("project", "")
                        st.session_state.video_project_id = project_id
                        st.session_state.video_status = "submitted"
                        st.session_state.video_message = ""
                        st.session_state.video_url = ""
                        st.session_state.video_result = {}

                        movie = poll_video_until_ready(project_id, max_checks=12, delay_seconds=5)
                        store_video_state(movie)

                    except Exception as e:
                        st.error(f"Video generation failed: {e}")

        with right:
            st.markdown("#### Video preview")
            if st.session_state.video_project_id:
                st.caption(f"Project ID: {st.session_state.video_project_id}")

                btn1, btn2 = st.columns(2)
                with btn1:
                    if st.button("Refresh video status", use_container_width=True):
                        try:
                            movie = json2video_get_movie(st.session_state.video_project_id)
                            store_video_state(movie)
                        except Exception as e:
                            st.error(f"Could not refresh status: {e}")

                with btn2:
                    if st.button("Reset video", use_container_width=True):
                        reset_video_state()
                        safe_rerun()

            current_status = st.session_state.video_status or "idle"
            st.write(f"Status: **{current_status}**")

            if st.session_state.video_message:
                st.caption(st.session_state.video_message)

            if st.session_state.video_url:
                st.video(st.session_state.video_url)
                st.markdown(f"[Open rendered video]({st.session_state.video_url})")
            else:
                st.info("Your rendered video will appear here after the job finishes.")
