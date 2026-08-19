import json
import logging

from google.genai import types
from google.genai.errors import APIError

from gemini_client import (
    get_client,
    get_model,
)


logger = logging.getLogger(__name__)


def generate_analysis(
    fact_sheet,
    system_prompt,
    books_text,
    selected_year,
    user_note="",
):

    client = get_client()
    model = get_model()

    fact_json = json.dumps(
        fact_sheet,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
Bạn là chuyên gia luận giải Tử Vi Đẩu Số.

QUY TẮC:

1. FACT SHEET do Python Engine tạo
   là nguồn sự thật duy nhất.

2. Không được thay đổi vị trí sao.

3. Không được tự tính lại cung.

4. Không được thay đổi Tứ Hóa.

5. Không được bịa dữ liệu.

6. Nếu dữ liệu thiếu phải nói rõ.

7. Chỉ diễn giải dữ liệu đã có.

NĂM LUẬN:
{selected_year}

SYSTEM:
{system_prompt[:12000]}

FACT SHEET:
{fact_json[:40000]}

TÀI LIỆU:
{books_text[:10000]}

GHI CHÚ:
{user_note}

Hãy trình bày:

# 1. Kiểm tra dữ liệu

# 2. Tổng quan Mệnh - Thân - Cục

# 3. 12 cung

# 4. Chính tinh

# 5. Phụ tinh quan trọng

# 6. Tứ Hóa

# 7. Tam hợp và xung chiếu

# 8. Đại vận

# 9. Tiểu vận / lưu niên

# 10. Tổng kết

Không tự tạo dữ liệu ngoài FACT SHEET.
"""

    try:

        response = client.models.generate_content(

            model=model,

            contents=prompt,

            config=types.GenerateContentConfig(

                # QUAN TRỌNG:
                # Gemini 3.6 không dùng temperature
                max_output_tokens=12000,

            ),
        )

        text = getattr(
            response,
            "text",
            None
        )

        if not text:
            raise RuntimeError(
                "Gemini không trả về nội dung."
            )

        return text

    except APIError as exc:

        status = getattr(
            exc,
            "status_code",
            None
        )

        logger.exception(
            "Gemini API error: %s",
            exc
        )

        if status == 400:

            raise RuntimeError(
                "Gemini trả HTTP 400.\n\n"
                "Kiểm tra:\n"
                "• GEMINI_MODEL\n"
                "• temperature/top_p/top_k\n"
                "• kích thước prompt\n"
                "• request configuration\n\n"
                f"Model: {model}\n"
                f"Chi tiết: {exc}"
            ) from exc

        if status in (401, 403):

            raise RuntimeError(
                "GEMINI_API_KEY không hợp lệ "
                "hoặc API key không có quyền sử dụng model.\n\n"
                f"Model: {model}"
            ) from exc

        if status == 404:

            raise RuntimeError(
                f"Không tìm thấy model: {model}\n\n"
                "Hãy dùng:\n"
                "gemini-3.6-flash"
            ) from exc

        if status == 429:

            raise RuntimeError(
                "Gemini API đang giới hạn quota/rate limit."
            ) from exc

        raise RuntimeError(
            f"Gemini API error {status}: {exc}"
        ) from exc

    except Exception as exc:

        logger.exception(
            "Unexpected Gemini error"
        )

        raise RuntimeError(
            f"Lỗi Gemini: {exc}"
        ) from exc
