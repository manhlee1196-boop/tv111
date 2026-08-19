import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tu_vi_engine import TuViEngine, year_can_chi


def test_year_can_chi():
    assert year_can_chi(1990) == ("Canh", "Ngọ")


def test_complete_chart():
    engine = TuViEngine()
    chart = engine.calculate(1990, 5, 15, 8, 30, "Nam", is_lunar=True)
    assert chart["validation"]["valid"] is True
    assert len(chart["palaces"]) == 12
    assert sum(len(p["main_stars"]) for p in chart["palaces"]) == 14
    assert chart["info"]["menh_branch"]
    assert chart["info"]["than_branch"]
    assert set(chart["four_transformations"]) == {"Hóa Lộc","Hóa Quyền","Hóa Khoa","Hóa Kỵ"}


def test_json_load():
    data = json.loads(Path(__file__).parents[1].joinpath("tu_vi_engine.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "2.0"
    assert len(data["stars"]) >= 100
