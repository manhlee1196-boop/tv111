import os
from google import genai

try:
    import streamlit as st
except Exception:
    st = None


def get_api_key():
    if st is not None:
        try:
            if "GEMINI_API_KEY" in st.secrets:
                return str(st.secrets["GEMINI_API_KEY"])
        except Exception:
            pass
    return os.environ.get("GEMINI_API_KEY", "")


def get_model():
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def get_client(api_key=None):
    api_key = api_key or get_api_key()
    if not api_key:
        raise ValueError("Chưa cấu hình GEMINI_API_KEY.")
    return genai.Client(api_key=api_key)
