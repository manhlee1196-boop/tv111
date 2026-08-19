import json
from pathlib import Path

try:
    import streamlit as st
except Exception:
    st = None

BASE_DIR = Path(__file__).resolve().parent


def _cache_data(fn):
    if st is None:
        return fn
    return st.cache_data(ttl=3600)(fn)


@_cache_data
def load_system_prompt():
    prompt_dir = BASE_DIR / "system_prompts"
    if not prompt_dir.exists():
        return "Bạn là trợ lý Tử Vi.", "Thiếu system_prompts."
    sections = []
    for path in sorted(prompt_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            sections.append(f"===== {path.name} =====\n{text}")
    return ("\n\n".join(sections) or "Bạn là trợ lý Tử Vi."), (None if sections else "system_prompts trống.")


@_cache_data
def load_engine_rules():
    path = BASE_DIR / "tu_vi_engine.json"
    if not path.exists():
        return {}, f"Không tìm thấy {path.name}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return {}, f"{path.name} không hợp lệ: {exc}"


@_cache_data
def load_books_reference():
    path = BASE_DIR / "books_cache.json"
    if not path.exists():
        return "", f"Không tìm thấy {path.name}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return (("\n\n".join(map(str, data)) if isinstance(data, list)
                 else json.dumps(data, ensure_ascii=False, indent=2))), None
    except json.JSONDecodeError as exc:
        return "", f"{path.name} không hợp lệ: {exc}"


def load_all_data():
    prompt, e1 = load_system_prompt()
    rules, e2 = load_engine_rules()
    books, e3 = load_books_reference()
    return prompt, rules, books, [x for x in (e1, e2, e3) if x]
