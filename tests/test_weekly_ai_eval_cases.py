import json
from pathlib import Path


def test_weekly_ai_eval_covers_all_four_courses() -> None:
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "data/evals/weekly_ai_cases.json").read_text(encoding="utf-8"))
    assert {case["course_code"] for case in cases} == {"QBUS6600", "MKTG6018", "MKTG6104", "SIEN6006"}
    assert all(case["module_items"] and case["expected_terms"] for case in cases)
