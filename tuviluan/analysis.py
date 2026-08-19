import json
import logging

from google.genai import types
from google.genai.errors import APIError

from gemini_client import get_client, get_api_key, get_model


logger = logging.getLogger(__name__)


def _safe_error(exc):
    """
    Lấy thông tin lỗi nhưng không in API key / secret.
    """
    status = getattr(exc, "status_code", None)
    message = str(exc)

    for secret in [
        get_api_key(),
    ]:
        if secret:
            message = message.replace(secret, "***")

    return status, message


def generate_analysis(
    fact_sheet,
    system_prompt,
    books_text,
    selected_year,
    user_note="",
):
    client = get_client(get_api_key())
    model = get_model()

    # Không gửi toàn bộ dữ liệu thô quá lớn vào một request.
    fact_json = json.dumps(
        fact_sheet,
        ensure_ascii=False,
        indent=2,
    )

    prompt = f"""
Bạn là chuyên gia luận giải Tử Vi Đẩu Số.

QUY TẮC QUAN TRỌNG:
1. FACT SHEET do Python Engine tạo là nguồn sự thật duy nhất.
2. Không được tự thay đổi vị trí sao.
3. Không được tự tính lại cung.
4. Không được tự thay đổi Tứ Hóa.
5. Không được bịa dữ liệu.
6. Nếu dữ liệu thiếu, phải nói rõ.
7. Đây là nội dung tham khảo văn hóa/truyền thống, không phải kết luận chắc chắn.

NĂM LUẬN:
{selected_year}

SYSTEM:
{system_prompt[:12000]}

FACT SHEET:
{fact_json[:30000]}

TÀI LIỆU THAM KHẢO:
{books_text[:12000]}

GHI CHÚ:
{user_note}

Hãy luận giải theo cấu trúc:

# 1. Kiểm tra dữ liệu
- Ngày giờ sinh
- Mệnh
- Thân
- Cục
- Tính hợp lệ của lá số

# 2. Tổng quan
- Mệnh
- Thân
- Cục
- Chính tinh

# 3. 12 cung
Mỗi cung:
- Chính tinh
- Phụ tinh quan trọng
- Ý nghĩa truyền thống

# 4. Tam hợp và xung chiếu

# 5. Đại vận

# 6. Tiểu vận / lưu niên nếu có dữ liệu

# 7. Tổng kết

Không được tạo thêm dữ liệu không có trong FACT SHEET.
"""

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=12000,
            ),
        )

        text = getattr(response, "text", None)

        if not text:
            raise RuntimeError(
                "Gemini trả về response nhưng không có text."
            )

        return text

    except APIError as exc:
        status, message = _safe_error(exc)

        logger.exception(
            "Gemini API error. status=%s message=%s",
            status,
            message,
        )

        if status == 400:
            raise RuntimeError(
                "Gemini từ chối request (HTTP 400).\n\n"
                "Nguyên nhân thường gặp:\n"
                "- model không hợp lệ\n"
                "- request quá lớn\n"
                "- tham số generation không được model hỗ trợ\n"
                "- nội dung request bị từ chối\n\n"
                f"Model hiện tại: {model}\n"
                f"Chi tiết: {message}"
            ) from exc

        if status == 401 or status == 403:
            raise RuntimeError(
                "Gemini API Key không hợp lệ hoặc không có quyền "
                f"sử dụng model '{model}'.\n\n"
                f"Chi tiết: {message}"
            ) from exc

        if status == 404:
            raise RuntimeError(
                f"Không tìm thấy Gemini model '{model}'.\n\n"
                "Hãy kiểm tra GEMINI_MODEL."
            ) from exc

        if status == 429:
            raise RuntimeError(
                "Gemini API đang giới hạn quota/rate limit.\n"
                "Hãy thử lại sau hoặc kiểm tra quota."
            ) from exc

        if status and status >= 500:
            raise RuntimeError(
                "Gemini server đang gặp lỗi tạm thời.\n"
                "Hãy thử lại sau."
            ) from exc

        raise RuntimeError(
            f"Gemini API lỗi HTTP {status}: {message}"
        ) from exc

    except Exception as exc:
        logger.exception("Unexpected Gemini error")

        raise RuntimeError(
            f"Lỗi khi gọi Gemini: {exc}"
        ) from exc
