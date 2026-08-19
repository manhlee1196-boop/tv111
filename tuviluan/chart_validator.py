EXPECTED_BRANCHES = {"Tý","Sửu","Dần","Mão","Thìn","Tị","Ngọ","Mùi","Thân","Dậu","Tuất","Hợi"}
EXPECTED_PALACES = {"Mệnh","Phụ Mẫu","Phúc Đức","Điền Trạch","Quan Lộc","Nô Bộc",
                    "Thiên Di","Tật Ách","Tài Bạch","Tử Tức","Phu Thê","Huynh Đệ"}


def validate_chart(chart, engine_data=None):
    errors, warnings = [], []
    engine_data = engine_data or {}
    palaces = chart.get("palaces", {})
    if not isinstance(palaces, dict):
        return {"valid": False, "errors": ["palaces phải là object."], "warnings": []}

    missing = EXPECTED_PALACES - set(palaces)
    extra = set(palaces) - EXPECTED_PALACES
    if missing:
        errors.append("Thiếu cung: " + ", ".join(sorted(missing)))
    if extra:
        warnings.append("Cung ngoài danh mục: " + ", ".join(sorted(extra)))

    branches = []
    known_stars = set(engine_data.get("stars", {}).keys())
    for palace_name, palace in palaces.items():
        branch = palace.get("branch")
        if branch and branch not in EXPECTED_BRANCHES:
            errors.append(f"{palace_name}: địa chi không hợp lệ: {branch}")
        if branch:
            branches.append(branch)
        for bucket in ("main_stars", "secondary_stars", "bad_stars", "good_stars"):
            for star in palace.get(bucket, []):
                if known_stars and star not in known_stars:
                    warnings.append(f"{palace_name}: sao chưa có trong engine: {star}")

    if len(branches) == 12 and len(set(branches)) != 12:
        errors.append("12 cung phải có 12 địa chi khác nhau.")

    birth = chart.get("birth", {})
    if birth:
        for key in ("year", "month", "day", "hour"):
            if birth.get(key) is None:
                warnings.append(f"Thiếu birth.{key}; không thể tính lại toàn bộ lá số.")

    for item in chart.get("uncertain_items", []):
        warnings.append(f"Chưa chắc chắn: {item}")

    return {"valid": not errors, "errors": errors, "warnings": warnings}
