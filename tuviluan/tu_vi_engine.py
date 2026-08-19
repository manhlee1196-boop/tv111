"""
tu_vi_engine.py
Deterministic Vietnamese Tử Vi chart engine for tuviad.

Design:
- tu_vi_engine.json = data/rules
- this module = deterministic calculation
- LLM/OCR must not invent star positions
- Lunar date is the canonical input. Gregorian input can be converted when
  the optional `lunar_python` package is installed.

Reference implementation cross-check:
https://github.com/doanguyen/lasotuvi
Its App.py/AmDuong.py exposes the same core formulas for Tử Vi, Thiên Phủ,
Lộc Tồn, Thái Tuế, Tràng Sinh, Tứ Hóa, Tuần/Triệt, etc.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


CAN = ["Giáp", "Ất", "Bính", "Đinh", "Mậu", "Kỷ", "Canh", "Tân", "Nhâm", "Quý"]
CHI = ["Tý", "Sửu", "Dần", "Mão", "Thìn", "Tị", "Ngọ", "Mùi", "Thân", "Dậu", "Tuất", "Hợi"]

PALACES = [
    "Mệnh", "Phụ Mẫu", "Phúc Đức", "Điền Trạch", "Quan Lộc", "Nô Bộc",
    "Thiên Di", "Tật Ách", "Tài Bạch", "Tử Tức", "Phu Thê", "Huynh Đệ"
]

# 30 Na-Am pairs; each pair covers two consecutive Can-Chi years.
NA_AM_ELEMENTS = [
    "Kim","Kim","Hỏa","Hỏa","Mộc","Mộc","Thổ","Thổ","Kim","Kim",
    "Hỏa","Hỏa","Thủy","Thủy","Thổ","Thổ","Kim","Kim","Mộc","Mộc",
    "Thủy","Thủy","Thổ","Thổ","Hỏa","Hỏa","Mộc","Mộc","Thủy","Thủy"
]

BUREAU_BY_ELEMENT = {
    "Thủy": ("Thủy nhị cục", 2),
    "Mộc": ("Mộc tam cục", 3),
    "Kim": ("Kim tứ cục", 4),
    "Thổ": ("Thổ ngũ cục", 5),
    "Hỏa": ("Hỏa lục cục", 6),
}

TRANG_SINH_START = {
    6: 2,   # Hỏa lục cục -> Dần (0-based)
    4: 5,   # Kim tứ cục -> Tị
    2: 8,   # Thủy nhị cục -> Thân
    5: 8,   # Thổ ngũ cục -> Thân
    3: 11,  # Mộc tam cục -> Hợi
}

# The source implementation uses 1..10 for Heavenly Stems and 1..12
# for Earthly Branches. We use 0-based internally and expose both.
FOUR_TRANSFORMATIONS = {
    "Giáp": {"Hóa Lộc": "Liêm Trinh", "Hóa Quyền": "Phá Quân", "Hóa Khoa": "Vũ Khúc", "Hóa Kỵ": "Thái Dương"},
    "Ất": {"Hóa Lộc": "Thiên Cơ", "Hóa Quyền": "Thiên Lương", "Hóa Khoa": "Tử Vi", "Hóa Kỵ": "Thái Âm"},
    "Bính": {"Hóa Lộc": "Thiên Đồng", "Hóa Quyền": "Thiên Cơ", "Hóa Khoa": "Văn Xương", "Hóa Kỵ": "Liêm Trinh"},
    "Đinh": {"Hóa Lộc": "Thái Âm", "Hóa Quyền": "Thiên Đồng", "Hóa Khoa": "Thiên Cơ", "Hóa Kỵ": "Cự Môn"},
    "Mậu": {"Hóa Lộc": "Tham Lang", "Hóa Quyền": "Thái Âm", "Hóa Khoa": "Hữu Bật", "Hóa Kỵ": "Thiên Cơ"},
    "Kỷ": {"Hóa Lộc": "Vũ Khúc", "Hóa Quyền": "Tham Lang", "Hóa Khoa": "Thiên Lương", "Hóa Kỵ": "Văn Khúc"},
    "Canh": {"Hóa Lộc": "Thái Dương", "Hóa Quyền": "Vũ Khúc", "Hóa Khoa": "Thiên Đồng", "Hóa Kỵ": "Thái Âm"},
    "Tân": {"Hóa Lộc": "Cự Môn", "Hóa Quyền": "Thái Dương", "Hóa Khoa": "Văn Khúc", "Hóa Kỵ": "Văn Xương"},
    "Nhâm": {"Hóa Lộc": "Thiên Lương", "Hóa Quyền": "Tử Vi", "Hóa Khoa": "Thiên Phủ", "Hóa Kỵ": "Vũ Khúc"},
    "Quý": {"Hóa Lộc": "Phá Quân", "Hóa Quyền": "Cự Môn", "Hóa Khoa": "Thái Âm", "Hóa Kỵ": "Tham Lang"},
}

MAIN_STARS = [
    "Tử Vi","Thiên Cơ","Thái Dương","Vũ Khúc","Thiên Đồng","Liêm Trinh",
    "Thiên Phủ","Thái Âm","Tham Lang","Cự Môn","Thiên Tướng","Thiên Lương",
    "Thất Sát","Phá Quân"
]

TRANG_SINH = ["Tràng Sinh","Mộc Dục","Quan Đới","Lâm Quan","Đế Vượng","Suy",
              "Bệnh","Tử","Mộ","Tuyệt","Thai","Dưỡng"]

THAI_TUE_RING = [
    "Thái Tuế","Thiếu Dương","Tang Môn","Thiếu Âm","Quan Phù","Tử Phù",
    "Tuế Phá","Long Đức","Bạch Hổ","Phúc Đức","Điếu Khách","Trực Phù"
]

LOC_TON_RING = [
    "Lộc Tồn","Bác Sỹ","Lực Sỹ","Thanh Long","Tiểu Hao","Tướng Quân",
    "Tấu Thư","Phi Liêm","Hỷ Thần","Bệnh Phù","Đại Hao","Phục Binh"
]

# Additional stars used by the reference App.py.
STAR_GROUP = {
    "Tử Vi":"main","Thiên Cơ":"main","Thái Dương":"main","Vũ Khúc":"main",
    "Thiên Đồng":"main","Liêm Trinh":"main","Thiên Phủ":"main","Thái Âm":"main",
    "Tham Lang":"main","Cự Môn":"main","Thiên Tướng":"main","Thiên Lương":"main",
    "Thất Sát":"main","Phá Quân":"main",
    "Hóa Lộc":"tu_hoa","Hóa Quyền":"tu_hoa","Hóa Khoa":"tu_hoa","Hóa Kỵ":"tu_hoa",
    "Lộc Tồn":"loc_ton","Bác Sỹ":"loc_ton","Lực Sỹ":"loc_ton","Thanh Long":"loc_ton",
    "Tiểu Hao":"loc_ton","Tướng Quân":"loc_ton","Tấu Thư":"loc_ton","Phi Liêm":"loc_ton",
    "Hỷ Thần":"loc_ton","Bệnh Phù":"loc_ton","Đại Hao":"loc_ton","Phục Binh":"loc_ton",
    "Kình Dương":"sat_tinh","Đà La":"sat_tinh","Địa Không":"sat_tinh","Địa Kiếp":"sat_tinh",
    "Hỏa Tinh":"sat_tinh","Linh Tinh":"sat_tinh","Thiên Khốc":"sat_tinh","Thiên Hư":"sat_tinh",
    "Thiên Hình":"sat_tinh","Thiên Riêu":"sat_tinh","Thiên La":"sat_tinh","Địa Võng":"sat_tinh",
}

def mod12(p: int) -> int:
    return p % 12

def shift(p: int, offset: int) -> int:
    return (p + offset) % 12

def normalize_gender(gender: Any) -> str:
    if isinstance(gender, str):
        x = gender.strip().lower()
        if x in {"nam", "male", "m", "1"}:
            return "Nam"
        if x in {"nữ", "nu", "female", "f", "0", "2"}:
            return "Nữ"
    if gender in (1, True):
        return "Nam"
    if gender in (0, 2, False):
        return "Nữ"
    raise ValueError("gender phải là Nam/Nữ hoặc male/female")

def can_index(value: Any) -> int:
    if isinstance(value, int):
        if 0 <= value < 10:
            return value
        if 1 <= value <= 10:
            return value - 1
    s = str(value).strip()
    if s in CAN:
        return CAN.index(s)
    raise ValueError(f"Thiên Can không hợp lệ: {value}")

def chi_index(value: Any) -> int:
    if isinstance(value, int):
        if 0 <= value < 12:
            return value
        if 1 <= value <= 12:
            return value - 1
    s = str(value).strip()
    if s in CHI:
        return CHI.index(s)
    raise ValueError(f"Địa Chi không hợp lệ: {value}")

def year_can_chi(year: int) -> Tuple[str, str]:
    # 4 = Giáp Tý. This is the standard 60-year cycle.
    return CAN[(year - 4) % 10], CHI[(year - 4) % 12]

def nap_am_element(can: str, chi: str) -> str:
    c, b = CAN.index(can), CHI.index(chi)
    cycle = None
    for i in range(60):
        if i % 10 == c and i % 12 == b:
            cycle = i
            break
    if cycle is None:
        raise ValueError("Can-Chi không tạo thành một cặp hợp lệ")
    return NA_AM_ELEMENTS[cycle // 2]

def month_heavenly_stem(year_can: str, lunar_month: int) -> str:
    # Dần month stem:
    # Giáp/Kỷ -> Bính; Ất/Canh -> Mậu; Bính/Tân -> Canh;
    # Đinh/Nhâm -> Nhâm; Mậu/Quý -> Giáp.
    start = {
        "Giáp":"Bính","Kỷ":"Bính",
        "Ất":"Mậu","Canh":"Mậu",
        "Bính":"Canh","Tân":"Canh",
        "Đinh":"Nhâm","Nhâm":"Nhâm",
        "Mậu":"Giáp","Quý":"Giáp",
    }[year_can]
    return CAN[(CAN.index(start) + lunar_month - 1) % 10]

def hour_branch(hour: int, minute: int = 0) -> int:
    # Tý = 23:00-00:59, Sửu=01:00-02:59, ...
    total = hour * 60 + minute
    if total >= 23 * 60:
        return 0
    return ((total + 60) // 120) % 12

def menh_than(lunar_month: int, hour_branch_index: int) -> Tuple[int, int]:
    # Dần is index 2. Mệnh: month forward from Dần, then hour backward.
    menh = mod12(2 + lunar_month - 1 - hour_branch_index)
    than = mod12(2 + lunar_month - 1 + hour_branch_index)
    return menh, than

def palace_names(menh_branch: int) -> List[str]:
    # Start Mệnh at its branch, then assign the 12 palace names forward.
    return [PALACES[i] for i in range(12)]

def direction(gender: str, year_can: str) -> int:
    yang = CAN.index(year_can) % 2 == 0
    # Dương Nam / Âm Nữ thuận; Âm Nam / Dương Nữ nghịch.
    forward = (gender == "Nam" and yang) or (gender == "Nữ" and not yang)
    return 1 if forward else -1

def life_lord(body_branch: int) -> str:
    # Mapping used by lasotuvi's diaChi table.
    return {
        "Tý":"Tham Lang","Sửu":"Cự Môn","Dần":"Lộc Tồn","Mão":"Văn Khúc",
        "Thìn":"Liêm Trinh","Tị":"Vũ Khúc","Ngọ":"Phá Quân","Mùi":"Vũ Khúc",
        "Thân":"Liêm Trinh","Dậu":"Văn Khúc","Tuất":"Lộc Tồn","Hợi":"Cự Môn"
    }[CHI[body_branch]]

def body_lord(year_branch: int) -> str:
    return {
        "Tý":"Hỏa Tinh","Sửu":"Thiên Tướng","Dần":"Thiên Lương","Mão":"Thiên Đồng",
        "Thìn":"Văn Xương","Tị":"Thiên Cơ","Ngọ":"Hỏa Tinh","Mùi":"Thiên Tướng",
        "Thân":"Thiên Lương","Dậu":"Thiên Đồng","Tuất":"Văn Xương","Hợi":"Thiên Cơ"
    }[CHI[year_branch]]

def bureau(menh_branch: int, year_can: str) -> Tuple[str, int]:
    # Exact timCuc logic from lasotuvi/AmDuong.py:
    # canThangGieng=(canNam*2+1)%10; canThangMenh=((menh-3)%12+canThangGieng)%10;
    # then Na-Am(menh branch, month stem) -> bureau element.
    can_n = CAN.index(year_can) + 1
    can_thang_gieng = (can_n * 2 + 1) % 10
    if can_thang_gieng == 0:
        can_thang_gieng = 10
    menh_1 = menh_branch + 1
    can_thang_menh = ((menh_1 - 3) % 12 + can_thang_gieng) % 10
    if can_thang_menh == 0:
        can_thang_menh = 10
    # Match the branch with its derived stem in the 60-cycle. If the pair is
    # not a valid Can-Chi year, use the reference algorithm's Na-Am matrix
    # by searching all compatible 60-cycle entries.
    stem_idx = can_thang_menh - 1
    candidates = [b for b in range(12) if (stem_idx - b) % 2 == 0]
    element = None
    for b in candidates:
        try:
            element = nap_am_element(CAN[stem_idx], CHI[b])
            if b == menh_branch:
                break
        except ValueError:
            pass
    if element is None:
        # Fallback to the standard Cục lookup by Mệnh branch + derived stem.
        # This is only reachable if the input convention is inconsistent.
        raise ValueError("Không xác định được Ngũ hành Cục từ Mệnh và Can tháng")
    return BUREAU_BY_ELEMENT[element]

def tu_vi_position(cuc_so: int, lunar_day: int) -> int:
    # Direct port of timTuVi(), converted from 1-based to 0-based.
    cung_dan_1 = 3
    cuc = cuc_so
    while cuc < lunar_day:
        cuc += cuc_so
        cung_dan_1 += 1
    sai_lech = cuc - lunar_day
    if sai_lech % 2 == 1:
        sai_lech = -sai_lech
    return mod12((cung_dan_1 - 1) + sai_lech)

def add_star(chart: List[Dict[str, Any]], pos: int, name: str, kind: Optional[str] = None):
    if not (0 <= pos < 12):
        raise ValueError(f"Vị trí sao không hợp lệ: {pos}")
    if name not in chart[pos]["stars"]:
        chart[pos]["stars"].append(name)
    if kind:
        chart[pos].setdefault("star_groups", {}).setdefault(kind, []).append(name)

def add_ring(chart, base, names, step=1, direction=1):
    for i, name in enumerate(names):
        add_star(chart, shift(base, direction * i * step), name)

def loc_ton_position(year_can: str) -> int:
    return {
        "Giáp":2, "Ất":3, "Bính":5, "Đinh":6, "Mậu":5,
        "Kỷ":6, "Canh":8, "Tân":9, "Nhâm":11, "Quý":0
    }[year_can]

def thien_ma_position(year_branch: int) -> int:
    # Dần/Ngọ/Tuất -> Thân; Thân/Tý/Thìn -> Dần;
    # Tị/Dậu/Sửu -> Hợi; Hợi/Mão/Mùi -> Tị.
    if year_branch in {2, 6, 10}: return 8
    if year_branch in {8, 0, 4}: return 2
    if year_branch in {3, 7, 11}: return 5
    return 11

def co_than_position(year_branch: int) -> int:
    if year_branch in {11,0,1}: return 2
    if year_branch in {2,3,4}: return 5
    if year_branch in {5,6,7}: return 8
    return 11

def pha_toai_position(year_branch: int) -> int:
    r = (year_branch + 1) % 3
    return {0:5,1:9,2:1}[r]

def thien_khoi_position(year_can: str) -> int:
    return {"Giáp":1,"Ất":0,"Bính":11,"Đinh":9,"Mậu":7,
            "Kỷ":0,"Canh":7,"Tân":6,"Nhâm":5,"Quý":3}[year_can]

def thien_quan_phuc(year_can: str) -> Tuple[int,int]:
    quan = {"Giáp":7,"Ất":4,"Bính":5,"Đinh":2,"Mậu":3,"Kỷ":9,"Canh":11,"Tân":9,"Nhâm":10,"Quý":6}
    phuc = {"Giáp":9,"Ất":8,"Bính":0,"Đinh":11,"Mậu":3,"Kỷ":2,"Canh":6,"Tân":5,"Nhâm":6,"Quý":5}
    return quan[year_can], phuc[year_can]

def hoa_linh(year_branch: int, hour: int, gender: str, year_can: str) -> Tuple[int,int]:
    # Direct translation of timHoaLinh() convention.
    chi1 = year_branch + 1
    if chi1 in [3,7,11]:
        h0,l0 = 2,4
    elif chi1 in [1,5,9]:
        h0,l0 = 3,11
    elif chi1 in [6,10,2]:
        h0,l0 = 11,4
    else:
        h0,l0 = 10,11
    yang = CAN.index(year_can) % 2 == 0
    sign = 1 if ((gender=="Nam") == yang) else -1
    if sign == -1:
        return shift(h0, -hour), shift(l0, hour)
    return shift(h0, hour), shift(l0, -hour)

def xung_pair_tuan(year_can: str, year_branch: int) -> Tuple[int,int]:
    can1 = CAN.index(year_can) + 1
    chi1 = year_branch + 1
    end = (chi1 + (10 - can1)) % 12
    return shift(end, 1), shift(end, 2)

def triet_positions(year_can: str) -> Tuple[int,int]:
    c = CAN.index(year_can) + 1
    if c in [1,6]: return 8,9
    if c in [2,7]: return 6,7
    if c in [3,8]: return 4,5
    if c in [4,9]: return 2,3
    return 0,1

def build_chart(
    lunar_year: int,
    lunar_month: int,
    lunar_day: int,
    hour: int,
    minute: int = 0,
    gender: str = "Nam",
    name: str = "",
    engine_data: Optional[Dict[str,Any]] = None,
    leap_month: bool = False,
) -> Dict[str, Any]:
    """Generate a complete deterministic natal chart from a Vietnamese lunar date."""

    if not 1 <= lunar_month <= 12: raise ValueError("lunar_month phải 1..12")
    if not 1 <= lunar_day <= 30: raise ValueError("lunar_day phải 1..30")
    if not 0 <= hour <= 23: raise ValueError("hour phải 0..23")
    if not 0 <= minute <= 59: raise ValueError("minute phải 0..59")
    gender = normalize_gender(gender)

    year_can, year_branch_name = year_can_chi(lunar_year)
    year_branch = CHI.index(year_branch_name)
    hbranch = hour_branch(hour, minute)

    menh, than = menh_than(lunar_month, hbranch)
    cuc_name, cuc_so = bureau(menh, year_can)
    menh_element = nap_am_element(year_can, year_branch_name)
    dir_sign = direction(gender, year_can)

    chart = []
    for i in range(12):
        branch = mod12(menh + i)
        chart.append({
            "index": i,
            "branch_index": branch,
            "branch": CHI[branch],
            "palace": PALACES[i],
            "is_menh": i == 0,
            "is_than": branch == than,
            "stars": [],
            "star_groups": {},
            "dai_han": None,
            "tieu_han": None,
            "tuan": False,
            "triet": False,
            "four_transformations": [],
        })

    def p(branch_idx: int) -> int:
        return next(x["index"] for x in chart if x["branch_index"] == branch_idx)

    # 14 main stars.
    tv = tu_vi_position(cuc_so, lunar_day)
    add_star(chart, p(tv), "Tử Vi", "main")
    for off, star in [(4,"Liêm Trinh"),(7,"Thiên Đồng"),(8,"Vũ Khúc"),
                      (9,"Thái Dương"),(11,"Thiên Cơ")]:
        add_star(chart, p(shift(tv, off)), star, "main")

    thien_phu = shift(2, 2 - tv)
    for off, star in [(0,"Thiên Phủ"),(1,"Thái Âm"),(2,"Tham Lang"),(3,"Cự Môn"),
                      (4,"Thiên Tướng"),(5,"Thiên Lương"),(6,"Thất Sát"),(10,"Phá Quân")]:
        add_star(chart, p(shift(thien_phu, off)), star, "main")

    # Lộc Tồn ring + Kình/Đà.
    lt = loc_ton_position(year_can)
    for i, star in enumerate(LOC_TON_RING):
        add_star(chart, p(shift(lt, dir_sign * i)), star, "loc_ton")
    add_star(chart, p(shift(lt,-1)), "Đà La", "sat_tinh")
    add_star(chart, p(shift(lt,1)), "Kình Dương", "sat_tinh")

    # Thái Tuế ring.
    for i, star in enumerate(THAI_TUE_RING):
        add_star(chart, p(shift(year_branch,i)), star, "thai_tue")
    add_star(chart, p(shift(year_branch,1)), "Thiên Không", "sat_tinh")
    add_star(chart, p(shift(year_branch,5)), "Nguyệt Đức", "phuc_tinh")
    add_star(chart, p(shift(year_branch,9)), "Thiên Đức", "phuc_tinh")

    # Tràng Sinh.
    ts = TRANG_SINH_START[cuc_so]
    for i, star in enumerate(TRANG_SINH):
        add_star(chart, p(shift(ts, dir_sign*i)), star, "trang_sinh")

    # Địa Không / Địa Kiếp.
    dk = shift(10, hbranch)
    add_star(chart, p(dk), "Địa Kiếp", "sat_tinh")
    add_star(chart, p(shift(11, 11-dk)), "Địa Không", "sat_tinh")

    # Hỏa Tinh / Linh Tinh.
    ht, ltinh = hoa_linh(year_branch, hbranch, gender, year_can)
    add_star(chart, p(ht), "Hỏa Tinh", "sat_tinh")
    add_star(chart, p(ltinh), "Linh Tinh", "sat_tinh")

    # Thiên Mã, Hoa Cái, Kiếp Sát, Đào Hoa.
    tm = thien_ma_position(year_branch)
    add_star(chart,p(tm),"Thiên Mã","thien_ma")
    add_star(chart,p(shift(tm,2)),"Hoa Cái","dao_hoa")
    add_star(chart,p(shift(tm,3)),"Kiếp Sát","sat_tinh")
    add_star(chart,p(shift(tm,7)),"Đào Hoa","dao_hoa")

    # Văn Xương/Khúc, Tả/Hữu, Tam Thai/Bát Tọa.
    van_khuc = shift(4, hbranch - 1)
    van_xuong = shift(1, 1 - van_khuc)
    ta_phu = shift(4, lunar_month - 1)
    huu_bat = shift(1, 1 - ta_phu)
    tam_thai = shift(4, lunar_month + lunar_day - 2)
    bat_toa = shift(1, 1 - tam_thai)
    for pos, star, group in [
        (van_khuc,"Văn Khúc","van_tinh"),(van_xuong,"Văn Xương","van_tinh"),
        (ta_phu,"Tả Phù","phu_tinh"),(huu_bat,"Hữu Bật","phu_tinh"),
        (tam_thai,"Tam Thai","phu_tinh"),(bat_toa,"Bát Tọa","phu_tinh")
    ]:
        add_star(chart,p(pos),star,group)

    # Ân Quang / Thiên Quý, Thai Phụ / Phong Cáo.
    an_quang = shift(van_xuong, lunar_day - 2)
    thien_quy = shift(1, 1 - an_quang)
    thai_phu = shift(van_khuc, 2)
    phong_cao = shift(van_khuc, -2)
    for pos, star, group in [
        (an_quang,"Ân Quang","phuc_tinh"),(thien_quy,"Thiên Quý","phuc_tinh"),
        (thai_phu,"Thai Phụ","van_tinh"),(phong_cao,"Phong Cáo","quyen_tinh")
    ]:
        add_star(chart,p(pos),star,group)

    # Khôi/Viet, Khốc/Hư.
    khoi = thien_khoi_position(year_can)
    viet = shift(4, 4-khoi)
    khoc = shift(6, -year_branch)
    hu = shift(6, year_branch)
    for pos, star, group in [
        (khoi,"Thiên Khôi","quy_tinh"),(viet,"Thiên Việt","quy_tinh"),
        (khoc,"Thiên Khốc","sat_tinh"),(hu,"Thiên Hư","sat_tinh")
    ]:
        add_star(chart,p(pos),star,group)

    # Hồng Loan / Thiên Hỷ.
    hong = shift(3, -year_branch)
    hy = shift(hong,6)
    add_star(chart,p(hong),"Hồng Loan","dao_hoa")
    add_star(chart,p(hy),"Thiên Hỷ","phuc_tinh")

    # Cô Thần / Quả Tú.
    co = co_than_position(year_branch)
    qua = shift(co,-4)
    add_star(chart,p(co),"Cô Thần","am_tinh")
    add_star(chart,p(qua),"Quả Tú","am_tinh")

    # Thiên Quan / Thiên Phúc.
    tq, tf = thien_quan_phuc(year_can)
    add_star(chart,p(tq),"Thiên Quan","phuc_tinh")
    add_star(chart,p(tf),"Thiên Phúc","phuc_tinh")

    # Thiên Hình / Thiên Riêu / Thiên Y.
    th = shift(9, lunar_month - 1)
    tr = shift(th,4)
    add_star(chart,p(th),"Thiên Hình","hinh_tinh")
    add_star(chart,p(tr),"Thiên Riêu","am_tinh")
    add_star(chart,p(tr),"Thiên Y","phuc_tinh")

    # Thiên Tài / Thiên Thọ.
    tai = shift(menh, year_branch)
    tho = shift(than, year_branch)
    add_star(chart,p(tai),"Thiên Tài","phu_tinh")
    add_star(chart,p(tho),"Thiên Thọ","phuc_tinh")

    # Thiên Giải / Địa Giải.
    tg = shift(8, 2*lunar_month - 2)
    dg = shift(ta_phu,3)
    add_star(chart,p(tg),"Thiên Giải","giai_tinh")
    add_star(chart,p(dg),"Địa Giải","giai_tinh")

    # Fixed/structural stars.
    add_star(chart,p(4),"Thiên La","sat_tinh")
    add_star(chart,p(10),"Địa Võng","sat_tinh")
    add_star(chart,p(next(x["index"] for x in chart if x["palace"]=="Nô Bộc")),"Thiên Thương","sat_tinh")
    add_star(chart,p(next(x["index"] for x in chart if x["palace"]=="Tật Ách")),"Thiên Sứ","sat_tinh")
    add_star(chart,p(pha_toai_position(year_branch)),"Phá Toái","sat_tinh")
    add_star(chart,p(shift(year_branch,-lunar_month + hbranch)),"Đẩu Quân","phu_tinh")

    # Lưu Hà / Thiên Trù.
    luu_ha = {"Giáp":9,"Ất":10,"Bính":7,"Đinh":4,"Mậu":5,"Kỷ":6,"Canh":8,"Tân":3,"Nhâm":11,"Quý":2}[year_can]
    thien_tru = {"Giáp":5,"Ất":6,"Bính":0,"Đinh":5,"Mậu":6,"Kỷ":8,"Canh":2,"Tân":6,"Nhâm":9,"Quý":10}[year_can]
    add_star(chart,p(luu_ha),"Lưu Hà","sat_tinh")
    add_star(chart,p(thien_tru),"Thiên Trù","phuc_tinh")

    # Tứ Hóa.
    hoa = FOUR_TRANSFORMATIONS[year_can]
    for trans, star in hoa.items():
        target = p(next(x["branch_index"] for x in chart if star in x["stars"]))
        add_star(chart,target,trans,"tu_hoa")
        chart[target]["four_transformations"].append(trans)

    # Tuần / Triệt.
    tuan1,tuan2 = xung_pair_tuan(year_can,year_branch)
    triet1,triet2 = triet_positions(year_can)
    for pos in (tuan1,tuan2):
        chart[p(pos)]["tuan"] = True
    for pos in (triet1,triet2):
        chart[p(pos)]["triet"] = True

    # Đại hạn: each palace gets a 10-year interval. Start age follows the
    # traditional Cục number; direction follows Dương Nam/Âm Nữ convention.
    for i, c in enumerate(chart):
        start_age = cuc_so + i * 10 if dir_sign == 1 else cuc_so + (11-i)*10
        c["dai_han"] = {
            "start_age": start_age,
            "end_age": start_age + 9,
            "direction": "thuận" if dir_sign == 1 else "nghịch",
        }

    # Tiểu hạn: provide the traditional year-branch starting point.
    khoi_han = shift(10, -3 * year_branch)
    for age in range(1, 121):
        pos = shift(khoi_han, dir_sign * ((age - 1) % 12))
        chart[p(pos)].setdefault("tieu_han_years", []).append(age)

    # Final palace metadata.
    for c in chart:
        c["star_count"] = len(c["stars"])
        c["main_stars"] = [s for s in c["stars"] if s in MAIN_STARS]
        c["good_stars"] = [s for s in c["stars"] if s not in MAIN_STARS and
                           STAR_GROUP.get(s,"") in {"phuc_tinh","quy_tinh","van_tinh","phu_tinh","dao_hoa","loc_ton"}]
        c["bad_stars"] = [s for s in c["stars"] if STAR_GROUP.get(s,"") in {"sat_tinh","am_tinh","hinh_tinh"}]

    result = {
        "schema_version": "2.0",
        "engine": "tuviad_deterministic",
        "input": {
            "name": name,
            "gender": gender,
            "lunar": {
                "year": lunar_year, "month": lunar_month, "day": lunar_day,
                "hour": hour, "minute": minute, "leap_month": leap_month
            }
        },
        "info": {
            "can_nam": year_can,
            "chi_nam": year_branch_name,
            "nam_can_chi": f"{year_can} {year_branch_name}",
            "gio_chi": CHI[hbranch],
            "gio_index": hbranch,
            "am_duong": ("Dương" if CAN.index(year_can) % 2 == 0 else "Âm"),
            "am_duong_gioi_tinh": (
                ("Dương" if CAN.index(year_can) % 2 == 0 else "Âm") + " " + gender
            ),
            "ban_menh_ngu_hanh": menh_element,
            "cuc": cuc_name,
            "cuc_so": cuc_so,
            "menh_branch": CHI[menh],
            "than_branch": CHI[than],
            "chu_menh": life_lord(year_branch),
            "chu_than": body_lord(year_branch),
            "than_cu": next(c["palace"] for c in chart if c["branch_index"] == than),
            "dai_han_direction": "thuận" if dir_sign == 1 else "nghịch",
        },
        "menh": {"palace": "Mệnh", "branch": CHI[menh]},
        "than": {
            "palace": next(c["palace"] for c in chart if c["branch_index"] == than),
            "branch": CHI[than]
        },
        "four_transformations": hoa,
        "tuan": [CHI[tuan1], CHI[tuan2]],
        "triet": [CHI[triet1], CHI[triet2]],
        "palaces": chart,
        "validation": validate_chart({
            "info": {"cuc_so": cuc_so},
            "palaces": chart,
            "four_transformations": hoa
        }),
    }
    return result

def validate_chart(chart: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    palaces = chart.get("palaces", [])
    if len(palaces) != 12:
        errors.append(f"Phải có 12 cung, hiện có {len(palaces)}")
    branches = [p.get("branch") for p in palaces]
    if len(set(branches)) != len(branches):
        errors.append("12 cung bị trùng địa chi")
    main = [s for p in palaces for s in p.get("stars", []) if s in MAIN_STARS]
    if len(main) != 14:
        errors.append(f"Phải có 14 chính tinh, hiện có {len(main)}")
    else:
        missing = sorted(set(MAIN_STARS)-set(main))
        if missing:
            errors.append("Thiếu chính tinh: " + ", ".join(missing))
    if chart.get("four_transformations"):
        for trans, star in chart["four_transformations"].items():
            hits = sum(star in p.get("stars", []) for p in palaces)
            if hits != 1:
                errors.append(f"{trans} -> {star}: xuất hiện {hits} cung")
    return {"valid": not errors, "errors": errors, "warnings": warnings}

def load_engine_data(path: Optional[str] = None) -> Dict[str,Any]:
    if path is None:
        path = str(Path(__file__).with_name("tu_vi_engine.json"))
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Không tìm thấy engine JSON: {p}")
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("tu_vi_engine.json phải là object JSON")
    return data

class TuViEngine:
    """Public API compatible with the existing tuviad engine."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.data = load_engine_data(config_path)
        self._merge_config_rules()

    def _merge_config_rules(self):
        # JSON is authoritative when a rule exists; constants provide a safe
        # fallback for older/partial configs.
        ft = self.data.get("four_transformations", {}).get("rules")
        if isinstance(ft, dict) and all(isinstance(v, dict) for v in ft.values()):
            FOUR_TRANSFORMATIONS.update(ft)

    def calculate(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int = 0,
        gender: str = "Nam",
        name: str = "",
        is_lunar: bool = True,
        leap_month: bool = False,
    ) -> Dict[str,Any]:
        if not is_lunar:
            return self.calculate_solar(year, month, day, hour, minute, gender, name)
        return build_chart(
            lunar_year=year, lunar_month=month, lunar_day=day,
            hour=hour, minute=minute, gender=gender, name=name,
            engine_data=self.data, leap_month=leap_month
        )

    def calculate_solar(self, year, month, day, hour, minute=0, gender="Nam", name=""):
        try:
            from lunar_python import Solar
        except ImportError as exc:
            raise RuntimeError(
                "Gregorian input cần package `lunar_python`. "
                "Cài bằng: pip install lunar-python. "
                "Hoặc truyền is_lunar=True để dùng trực tiếp ngày âm."
            ) from exc
        solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
        lunar = solar.getLunar()
        return self.calculate(
            lunar.getYear(), lunar.getMonth(), lunar.getDay(),
            hour, minute, gender, name, is_lunar=True
        )

    # Backward-compatible methods expected by the old tu_vi_engine.py.
    def compute_four_transformations(self, chart):
        can = chart.get("info", {}).get("can_nam")
        return FOUR_TRANSFORMATIONS.get(can, {})

    def compute_major_cycles(self, chart):
        return [p["dai_han"] for p in chart.get("palaces", [])]

    def compute_minor_cycle(self, chart, age: int):
        for p in chart.get("palaces", []):
            if age in p.get("tieu_han_years", []):
                return {"age": age, "palace": p["palace"], "branch": p["branch"]}
        return None

    def compute_annual_flow(self, chart, target_year: int):
        can, chi = year_can_chi(target_year)
        return {
            "year": target_year,
            "can": can,
            "chi": chi,
            "four_transformations": FOUR_TRANSFORMATIONS[can],
            "thai_tue_branch": chi,
        }

    def generate(self, *args, **kwargs):
        return self.calculate(*args, **kwargs)

# Functional API.
def generate_chart(*args, config_path: Optional[str] = None, **kwargs):
    return TuViEngine(config_path).calculate(*args, **kwargs)

def compute_chart(*args, config_path: Optional[str] = None, **kwargs):
    return generate_chart(*args, config_path=config_path, **kwargs)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Tính lá số Tử Vi deterministic")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument("--day", type=int, required=True)
    parser.add_argument("--hour", type=int, required=True)
    parser.add_argument("--minute", type=int, default=0)
    parser.add_argument("--gender", default="Nam")
    parser.add_argument("--name", default="")
    parser.add_argument("--solar", action="store_true")
    parser.add_argument("--config", default=None)
    args = parser.parse_args()

    engine = TuViEngine(args.config)
    result = engine.calculate(
        args.year, args.month, args.day, args.hour, args.minute,
        args.gender, args.name, is_lunar=not args.solar
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def build_engine_facts(chart, engine_data=None, selected_year=None):
    """Convert normalized birth/chart JSON into deterministic engine facts."""
    engine = TuViEngine()
    birth = chart.get("birth", {})
    required = [birth.get(k) for k in ("year", "month", "day", "hour")]
    if any(v is None for v in required):
        # OCR-only charts without birth data cannot be recalculated.
        return {
            "status": "not_configured",
            "reason": "Thiếu birth.year/month/day/hour; cần ngày giờ sinh để Python tính lại.",
            "source_of_truth": "python_engine",
            "ocr_chart_preserved": chart,
        }

    result = engine.calculate(
        year=int(birth["year"]),
        month=int(birth["month"]),
        day=int(birth["day"]),
        hour=int(birth["hour"]),
        minute=int(birth.get("minute") or 0),
        gender=birth.get("gender") or "Nam",
        name=chart.get("name", ""),
        is_lunar=str(birth.get("calendar", "lunar")).lower() != "solar",
        leap_month=bool(birth.get("leap_month", False)),
    )

    if selected_year is not None:
        result["annual_flow"] = engine.compute_annual_flow(result, int(selected_year))
    result["status"] = "computed"
    result["source_of_truth"] = "python_engine"
    return result
