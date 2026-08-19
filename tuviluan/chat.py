import json
from gemini_client import get_client, get_api_key, get_model
from google.genai import types


def ask_chat(question, fact_sheet, analysis_context, chat_history):
    client = get_client(get_api_key())
    history = "\n\n".join(
        f'{m.get("role","user").upper()}: {m.get("content","")}'
        for m in chat_history[-12:]
    )
    prompt = f"""
Bạn đang trả lời câu hỏi về lá số đã được Python kiểm chứng.
FACT SHEET là nguồn sự thật.
Không bịa vị trí sao/cung/công thức.
Nếu thiếu dữ liệu, nói rõ.

FACT SHEET:
{json.dumps(fact_sheet, ensure_ascii=False, indent=2)}

LUẬN GIẢI:
{analysis_context[:50000]}

HỘI THOẠI:
{history}

CÂU HỎI:
{question}
"""
    response = client.models.generate_content(
        model=get_model(), contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=12000),
    )
    if not getattr(response, "text", None):
        raise RuntimeError("Gemini không trả câu trả lời.")
    return response.text
