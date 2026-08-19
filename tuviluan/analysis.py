import json
from gemini_client import get_client, get_api_key, get_model
from google.genai import types


def generate_analysis(fact_sheet, system_prompt, books_text, selected_year, user_note=""):
    client = get_client(get_api_key())
    prompt = f"""
Bạn là hệ thống luận giải Tử Vi Đẩu Số.
FACT SHEET do Python engine tạo là nguồn sự thật duy nhất.
Không thay đổi cung, địa chi, sao, Tứ Hóa hay vận.
Nếu dữ liệu thiếu, nói rõ thiếu dữ liệu.
Không tự tạo nguồn sách.

NĂM LUẬN: {selected_year}

SYSTEM:
{system_prompt[:18000]}

FACT SHEET:
{json.dumps(fact_sheet, ensure_ascii=False, indent=2)}

BOOKS:
{books_text[:40000]}

Ghi chú:
{user_note}

Trình bày:
I. Kiểm tra dữ liệu
II. Tổng quan Mệnh/Thân
III. 12 cung
IV. Tam hợp/Xung chiếu
V. Đại vận
VI. Tiểu vận/Lưu niên
VII. Kết luận
"""
    response = client.models.generate_content(
        model=get_model(), contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=30000),
    )
    if not getattr(response, "text", None):
        raise RuntimeError("Gemini không trả nội dung.")
    return response.text
