import numpy as np
import easyocr

try:
    import streamlit as st
except Exception:
    st = None


def _reader():
    if st is not None:
        return st.cache_resource(lambda: easyocr.Reader(["vi", "en"], gpu=False))()
    return easyocr.Reader(["vi", "en"], gpu=False)


def extract_text_from_cungs(cropped_dict):
    reader = _reader()
    result = {}
    for branch, image in cropped_dict.items():
        texts = reader.readtext(np.array(image), detail=0, paragraph=False)
        result[branch] = [str(x).strip() for x in texts if str(x).strip()]
    return result
