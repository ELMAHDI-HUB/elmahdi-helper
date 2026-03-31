import os
import streamlit as st
from openai import OpenAI

# Page config
st.set_page_config(page_title="ELMAHDI HELPER", page_icon="🤖")
st.title("ELMAHDI HELPER 🤖")

# Get API key from environment
API_KEY = os.getenv("NVIDIA_API_KEY")

if not API_KEY:
    st.error("Missing NVIDIA_API_KEY")
    st.stop()

# Create client
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=API_KEY
)

# Chat memory
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"]=="user" else "🤖"):
        st.write(msg["content"])

# Input box
user_input = st.chat_input("Type your message...")

if user_input:
    # Save user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Display user message
    with st.chat_message("user", avatar="🧑"):
        st.write(user_input)

    # System + history
    messages = [
        {
            "role": "system",
            "content": "You are ELMAHDI HELPER. Only give final answers. Never show reasoning, thoughts, or anything inside <think> tags. Be clear and concise."
        }
    ] + st.session_state.messages

    # Generate response
    with st.chat_message("assistant", avatar="🤖"):
        box = st.empty()
        full_reply = ""

        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=messages,
                temperature=0.6,
                top_p=0.7,
                max_tokens=512,
                stream=False
            )

            full_reply = response.choices[0].message.content

            # Remove reasoning if model outputs it
            if "<think>" in full_reply:
                full_reply = full_reply.split("</think>")[-1].strip()

            box.write(full_reply)

        except Exception as e:
            full_reply = f"Error: {e}"
            box.write(full_reply)

    # Save assistant message
    st.session_state.messages.append({"role": "assistant", "content": full_reply})