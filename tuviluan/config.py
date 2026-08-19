from dataclasses import dataclass
import os

try:
    import streamlit as st
except Exception:
    st = None


def get_secret(name: str, default: str = "") -> str:
    if st is not None:
        try:
            if name in st.secrets:
                return str(st.secrets[name])
        except Exception:
            pass
    return str(os.environ.get(name, default) or "")


@dataclass(frozen=True)
class Config:
    gemini_api_key: str
    gemini_model: str
    timezone: str = "Asia/Ho_Chi_Minh"


def load_config() -> Config:
    return Config(
        gemini_api_key=get_secret("GEMINI_API_KEY"),
        gemini_model=get_secret("GEMINI_MODEL", "gemini-2.5-flash"),
        timezone=get_secret("TZ", "Asia/Ho_Chi_Minh"),
    )
