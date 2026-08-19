import json
import os
from google import genai
from google.genai import types

SCHEMA_DESCRIPTION = r"""
{
  "birth": {
    "calendar": "solar|lunar",
    "year": 0,
    "month": 0,
    "day": 0,
    "hour": 0,
    "minute": 0,
    "leap_month": false,
    "gender": "Nam|Nữ"
  },
  "palaces": {
    "Mệnh": {"branch": null, "main_stars": [], "secondary_stars": [], "bad_stars": [], "good_stars": [], "transformations": [], "markers": []}
  },
  "uncertain_items": []
}
"""


def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1]
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
    return json.loads(text.strip())


def normalize_ocr_with_gemini(ocr_text, system_prompt, engine_data):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Thiếu GEMINI_API_KEY.")

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    client = genai.Client(api_key=api_key)
    prompt = f"""
Bạn chỉ làm nhiệm vụ OCR -> JSON có cấu trúc.
Không luận giải. Không tự tính vị trí sao.
Không bịa dữ liệu.
Nếu OCR không chắc, đưa vào uncertain_items.
Nếu ảnh không có ngày sinh/giờ sinh, giữ null.
Địa chi của ô OCR chỉ là nhãn vị trí ảnh, không tự biến thành cung nếu không có bằng chứng.

SCHEMA:
{SCHEMA_DESCRIPTION}

ENGINE STAR CATALOG:
{json.dumps(engine_data.get("stars", {}), ensure_ascii=False)[:45000]}

OCR:
{json.dumps(ocr_text, ensure_ascii=False, indent=2)}

SYSTEM:
{system_prompt[:10000]}
"""
    response = client.models.generate_content(
        model=model, contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0, max_output_tokens=12000, response_mime_type="application/json"
        ),
    )
    if not getattr(response, "text", None):
        raise RuntimeError("Gemini không trả JSON.")
    return _extract_json(response.text)
