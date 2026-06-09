import streamlit as st
import requests
import os
import base64
import json
import copy
import time
from dotenv import load_dotenv

USERNAME = "admin"
PASSWORD = "admin123"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():

    st.set_page_config(page_title="Login", layout="centered")

    st.markdown("""
    <style>
    body{
    background:linear-gradient(135deg,#667eea,#764ba2);
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🔐 Admin Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        if username == USERNAME and password == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid username or password")


if not st.session_state.logged_in:
    login()
    st.stop()

load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    st.error("API key missing")
    st.stop()

URL = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

HISTORY_FILE = "chat_history.json"

def load_history():

    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                data = json.load(f)

            if isinstance(data, list):
                return data
        except:
            pass

    return []

def save_history(history):

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = load_history()

if "show_upload" not in st.session_state:
    st.session_state.show_upload = False

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "response_times" not in st.session_state:
    st.session_state.response_times = []

if "show_metrics" not in st.session_state:
    st.session_state.show_metrics = False

DOMAINS = {

"📦 Order Support": """
You are a Customer Support Assistant for an online store.
Help customers with:
- Order tracking
- Delivery issues
- Order cancellation
- Order status
Always respond politely and clearly.
""",

"💳 Payment Support": """
You are a Customer Support Assistant helping customers with payment issues.
Help with:
- Payment failures
- Refund requests
- Billing issues
Explain solutions clearly.
""",

"🛍 Product Support": """
You are a Product Support Assistant.
Help customers with:
- Product information
- Product usage
- Product issues
Give helpful and simple explanations.
""",

"🛠 Technical Support": """
You are a Technical Support Assistant.
Help users fix problems with apps or services.
Provide step-by-step troubleshooting solutions.
""",

"📞 General Customer Support": """
You are a professional Customer Support Chatbot.
Be polite, friendly, and helpful.
Assist customers with any service-related queries.
If you don't know something, politely guide the user to contact support.
"""
}

def get_response(prompt, domain, image=None):

    messages = [
        {"role": "system", "content": DOMAINS[domain]}
    ]

    if image:

        img_bytes = image.read()
        img_base64 = base64.b64encode(img_bytes).decode()

        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_base64}"
                    }
                }
            ]
        })

    else:
        messages.append({"role": "user", "content": prompt})

    res = requests.post(
        URL,
        headers=headers,
        json={
            "model": "openai/gpt-4o-mini",
            "messages": messages
        }
    )

    return res.json()["choices"][0]["message"]["content"]

# NEW FUNCTION ADDED

def detect_intent(query):

    messages = [
        {
            "role": "system",
            "content": """
Classify the message into one category:
greeting
support
other

greeting → hi, hello, thanks
support → order, payment, product, technical issues
other → unrelated queries

Reply with only one word.
"""
        },
        {"role": "user", "content": query}
    ]

    res = requests.post(
        URL,
        headers=headers,
        json={
            "model": "openai/gpt-4o-mini",
            "messages": messages,
            "temperature": 0
        }
    )

    return res.json()["choices"][0]["message"]["content"].strip().lower()

st.set_page_config(page_title="Customer Support Chatbot", layout="wide")

st.title("💬 Customer Support Chatbot")

st.markdown(
"🤖 Ask any question related to **orders, payments, products, or technical issues.**"
)

with st.sidebar:

    st.header("📞 Support Category")

    selected_domain = st.selectbox(
        "Choose Support Type",
        list(DOMAINS.keys())
    )

    st.markdown("---")

    if st.button("🆕 New Chat"):

        if st.session_state.messages:
            st.session_state.history.append(copy.deepcopy(st.session_state.messages))
            save_history(st.session_state.history)

        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    st.subheader("📜 History")

    if st.session_state.history:

        for i, chat in enumerate(st.session_state.history):

            if st.button(f"Conversation {i+1}"):

                if isinstance(chat, list):
                    st.session_state.messages = chat

                st.rerun()

    if st.button("🗑 Clear History"):

        st.session_state.history = []
        save_history([])
        st.rerun()

    st.markdown("---")

    if st.button("📊 Show Metrics"):
        st.session_state.show_metrics = not st.session_state.show_metrics

    if st.session_state.show_metrics:

        st.subheader("📊 Chatbot Metrics")

        if st.session_state.response_times:

            avg_time = sum(st.session_state.response_times) / len(st.session_state.response_times)

            st.metric("Avg Response Time", f"{avg_time:.2f} sec")

for msg in st.session_state.messages:

    if not isinstance(msg, dict):
        continue

    if "role" in msg and "content" in msg:

        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

col1, col2 = st.columns([10,1])

with col2:
    if st.button("➕"):
        st.session_state.show_upload = not st.session_state.show_upload

if st.session_state.show_upload:

    file = st.file_uploader(
        "Upload screenshot of issue",
        type=["jpg","png","jpeg"]
    )

    if file:
        st.session_state.uploaded_file = file
        st.image(file, width=120)

user_input = st.chat_input("Ask customer support...")

if user_input:

    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.spinner("Support agent typing..."):

        start = time.time()

        intent = detect_intent(user_input)

        if intent == "greeting":

            reply = "👋 Hello! How can I assist you with orders, payments, products, or technical issues today?"

        elif intent == "support":

            reply = get_response(
                user_input,
                selected_domain,
                st.session_state.uploaded_file
            )

        else:

            reply = "⚠️ I can only assist with customer support queries like orders, payments, product issues, or technical support."

        end = time.time()

        response_time = end - start
        st.session_state.response_times.append(response_time)

    st.session_state.messages.append({
        "role": "assistant",
        "content": reply
    })

    st.caption(f"⏱ Response Time: {response_time:.2f} sec")

    st.session_state.uploaded_file = None
    st.session_state.show_upload = False

    st.rerun()
