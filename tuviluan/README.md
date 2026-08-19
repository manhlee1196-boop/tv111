# Tử Vi Đẩu Số — tuviad rebuilt

Kiến trúc mới:

Ảnh → Crop → EasyOCR → Gemini chuẩn hóa → Validator → **Python Engine** → Fact Sheet → Gemini luận giải → Chat

## Nguyên tắc

- Python Engine là nguồn sự thật.
- OCR chỉ là input.
- Gemini chỉ chuẩn hóa và diễn giải.
- Không để Gemini tự tính lại vị trí sao.
- Mọi công thức engine phải nằm trong JSON hoặc code deterministic và có nguồn/ghi chú.
- `uncertain_items` không được coi là facts.

## Cấu trúc

```text
tuviad/
├── app.py
├── config.py
├── data_loader.py
├── image_processing.py
├── ocr.py
├── chart_normalizer.py
├── chart_validator.py
├── tu_vi_engine.py
├── tu_vi_engine.json
├── fact_sheet.py
├── gemini_client.py
├── analysis.py
├── chat.py
├── session_state.py
├── system_prompts/
├── tests/
├── requirements.txt
└── README.md
```

## Cài đặt

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## Chạy engine không cần Gemini

```bash
python tu_vi_engine.py --year 1990 --month 5 --day 15 --hour 8 --minute 30 --gender Nam
```

Mặc định input là lịch âm.

Dương lịch:

```bash
python tu_vi_engine.py --year 1990 --month 5 --day 15 --hour 8 --minute 30 --gender Nam --solar
```

## Chạy giao diện

```bash
streamlit run app.py
```

API key:

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="YOUR_KEY"
$env:GEMINI_MODEL="gemini-2.5-flash"
```

hoặc `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "YOUR_KEY"
GEMINI_MODEL = "gemini-2.5-flash"
```

## Test

```bash
pytest -q
```

## Nguồn đối chiếu

Engine được thiết kế theo hướng deterministic và đối chiếu với các implementation Tử Vi mã nguồn mở. Không trộn các trường phái một cách im lặng; nếu một công thức khác nhau giữa nguồn, phải ghi rõ trong `tu_vi_engine.json`.
