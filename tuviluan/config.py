from dataclasses import dataclass
import os

try:
    import streamlit as st
except Exception:
    st = None


def get_secret(name: str, default: str = "") -> str:
    """
    Ưu tiên Streamlit Secrets.
    Nếu không có thì lấy Environment Variable.
    """

    # Streamlit Cloud
    if st is not None:
        try:
            value = st.secrets.get(name)

            if value is not None:
                return str(value).strip()
        except Exception:
            pass

    # Local / Environment
    return str(
        os.environ.get(name, default) or ""
    ).strip()


@dataclass(frozen=True)
class Config:
    gemini_api_key: str
    gemini_model: str
    timezone: str = "Asia/Ho_Chi_Minh"


def load_config() -> Config:
    return Config(
        gemini_api_key=get_secret(
            "GEMINI_API_KEY"
        ),

        gemini_model=get_secret(
            "GEMINI_MODEL",
            "gemini-3.6-flash"
        ),

        timezone=get_secret(
            "TZ",
            "Asia/Ho_Chi_Minh"
        ),
    )
