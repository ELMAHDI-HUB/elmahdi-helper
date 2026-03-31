import streamlit as st
from openai import OpenAI
import os

# 🔐 Get API key from Streamlit secrets
API_KEY = st.secrets.get("NVIDIA_API_KEY")

if not API_KEY:
    st.error("Missing NVIDIA_API_KEY")
    st.stop()

# 🤖 Initialize client
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=API_KEY
)

# 🎨 Page config
st.set_page_config(page_title="ELMAHDI HELPER", page_icon="🤖")

# 🧠 System message (VERY IMPORTANT)
SYSTEM_PROMPT = """
You are ELMAHDI HELPER, a helpful and friendly AI assistant created by a developer named Elmahdi Oukassou.

Rules:
- When asked who created you, ALWAYS say: "I was created by Elmahdi Oukassou, a developer."
- DO NOT mention OpenAI, NVIDIA, or any other company.
- NEVER show reasoning, thinking, or internal thoughts.
- Always give clean final answers only.
- Be friendly, helpful, and clear.
"""

# 💬 Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# 🏷️ Title
st.title("ELMAHDI HELPER 🤖")

# 💬 Display chat
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# ✏️ User input
user_input = st.chat_input("Type your message...")

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # 🤖 Get AI response
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",  # your new model
            messages=st.session_state.messages,
            temperature=0.6,
            top_p=0.7,
            max_tokens=512,
            stream=False
        )

        reply = response.choices[0].message.content

        # 🧹 Remove reasoning if model leaks it
        if "</think>" in reply:
            reply = reply.split("</think>")[-1].strip()

    except Exception as e:
        reply = f"Error: {e}"

    # Show assistant message
    with st.chat_message("assistant"):
        st.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
