#!/usr/bin/env python3
import json
import streamlit as st

from config import load_config
from session_state import init_session_state, reset_session_state
from data_loader import load_all_data
from image_processing import crop_12_cung, uploaded_file_to_image
from ocr import extract_text_from_cungs
from chart_normalizer import normalize_ocr_with_gemini
from chart_validator import validate_chart
from tu_vi_engine import build_engine_facts, TuViEngine
from fact_sheet import build_fact_sheet
from analysis import generate_analysis
from chat import ask_chat

st.set_page_config(page_title="Tử Vi Đẩu Số", page_icon="☯️", layout="wide")
config = load_config()
init_session_state()
system_prompt, engine_data, books_text, load_errors = load_all_data()

st.title("☯️ Tử Vi Đẩu Số — Deterministic Python Engine")

with st.sidebar:
    st.header("⚙️ Hệ thống")
    st.caption(f"Gemini: {config.gemini_model}")
    for err in load_errors:
        st.warning(err)
    if st.button("Xóa phiên"):
        reset_session_state()
        st.rerun()

tab1, tab2, tab3 = st.tabs(["📸 OCR lá số", "🧮 Tạo lá số từ ngày sinh", "🔮 Luận giải"])

with tab1:
    uploaded = st.file_uploader("Ảnh lá số", type=["jpg","jpeg","png","webp"])
    selected_year = st.number_input("Năm cần luận", 1950, 2050, 2026)
    if uploaded:
        image, err = uploaded_file_to_image(uploaded)
        if err:
            st.error(err)
        else:
            st.session_state["current_image"] = image
            st.session_state["current_image_name"] = uploaded.name
            st.image(image, use_container_width=True)
            if st.button("1. Crop + OCR", type="primary"):
                crops = crop_12_cung(image)
                st.session_state["cropped_dict"] = crops
                st.session_state["ocr_text"] = extract_text_from_cungs(crops)
            if st.session_state["ocr_text"]:
                st.json(st.session_state["ocr_text"])
            if st.button("2. OCR → JSON bằng Gemini"):
                if not config.gemini_api_key:
                    st.error("Thiếu GEMINI_API_KEY.")
                else:
                    chart = normalize_ocr_with_gemini(
                        st.session_state["ocr_text"], system_prompt, engine_data
                    )
                    st.session_state["chart_data"] = chart
                    st.session_state["validation"] = validate_chart(chart, engine_data)
            if st.session_state["chart_data"]:
                st.json(st.session_state["chart_data"])
                st.json(st.session_state["validation"])
                if st.button("3. Chạy Python Engine"):
                    facts = build_engine_facts(
                        st.session_state["chart_data"], engine_data, int(selected_year)
                    )
                    st.session_state["computed_chart"] = facts
                    st.session_state["fact_sheet"] = build_fact_sheet(
                        st.session_state["chart_data"], facts,
                        st.session_state["validation"], int(selected_year)
                    )
                    st.success("Đã tính lại bằng Python engine.")

with tab2:
    st.subheader("Tạo lá số trực tiếp — không cần OCR")
    c1, c2, c3, c4 = st.columns(4)
    y = c1.number_input("Năm âm", 1900, 2100, 1990)
    m = c2.number_input("Tháng âm", 1, 12, 5)
    d = c3.number_input("Ngày âm", 1, 30, 15)
    h = c4.number_input("Giờ", 0, 23, 8)
    gender = st.selectbox("Giới tính", ["Nam", "Nữ"])
    minute = st.number_input("Phút", 0, 59, 30)
    solar = st.checkbox("Input là dương lịch")
    if st.button("Tính lá số", type="primary"):
        engine = TuViEngine()
        facts = engine.calculate(
            y, m, d, h, minute, gender=gender,
            is_lunar=not solar
        )
        st.session_state["computed_chart"] = facts
        st.session_state["fact_sheet"] = build_fact_sheet(
            {}, facts, facts["validation"], int(selected_year)
        )
        st.json(facts)

with tab3:
    if st.session_state["fact_sheet"]:
        if st.button("Viết luận giải", type="primary"):
            if not config.gemini_api_key:
                st.error("Thiếu GEMINI_API_KEY.")
            else:
                st.session_state["analysis_result"] = generate_analysis(
                    st.session_state["fact_sheet"], system_prompt,
                    books_text, int(selected_year),
                    "Ưu tiên tuyệt đối dữ liệu Python."
                )
        if st.session_state["analysis_result"]:
            st.markdown(st.session_state["analysis_result"])
            st.download_button(
                "Tải TXT", st.session_state["analysis_result"],
                file_name="luan_giai_tu_vi.txt", mime="text/plain"
            )
        st.divider()
        st.subheader("💬 Chat")
        for msg in st.session_state["chat_messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        q = st.chat_input("Hỏi về lá số...")
        if q:
            st.session_state["chat_messages"].append({"role":"user","content":q})
            answer = ask_chat(
                q, st.session_state["fact_sheet"],
                st.session_state["analysis_result"],
                st.session_state["chat_messages"]
            )
            st.session_state["chat_messages"].append({"role":"assistant","content":answer})
            st.rerun()
    else:
        st.info("Hãy tạo lá số ở tab 1 hoặc tab 2 trước.")
