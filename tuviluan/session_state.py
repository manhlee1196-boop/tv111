import streamlit as st

DEFAULTS = {
    "analysis_result": "",
    "chat_messages": [],
    "current_image": None,
    "current_image_name": "",
    "cropped_dict": {},
    "ocr_text": {},
    "chart_data": {},
    "computed_chart": {},
    "validation": {},
    "fact_sheet": {},
}


def init_session_state():
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value


def reset_session_state():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value.copy() if isinstance(value, (dict, list)) else value
