from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_courses() -> dict:
    return json.loads((ROOT / "data" / "evals" / "remaining_courses.json").read_text(encoding="utf-8"))


def test_remaining_course_catalog_is_complete() -> None:
    courses = load_courses()
    assert set(courses) == {"MKTG6018", "MKTG6104", "SIEN6006"}
    for course in courses.values():
        assert len(course["weeks"]) == 13
        assert [week["week"] for week in course["weeks"]] == list(range(1, 14))
        assert sum(item["weight"] for item in course["assessments"]) == 100
        assert any(item["mode"] == "group" for item in course["assessments"])
        assert course["sources"]


def test_unknown_team_sizes_are_preserved() -> None:
    courses = load_courses()
    mktg6104_group = next(item for item in courses["MKTG6104"]["assessments"] if item["mode"] == "group")
    mktg6018_group = next(item for item in courses["MKTG6018"]["assessments"] if item["mode"] == "group")
    sien6006_group = next(item for item in courses["SIEN6006"]["assessments"] if item["mode"] == "group")
    assert mktg6104_group["team_size"] == {"min": 4, "max": 6}
    assert mktg6018_group["team_size"] is None
    assert sien6006_group["team_size"] is None


def test_detailed_week_data_only_uses_observed_canvas_content() -> None:
    courses = load_courses()
    assert set(courses["MKTG6018"]["detailed_weeks"]) == {"1", "2"}
    assert set(courses["MKTG6104"]["detailed_weeks"]) == {"1", "2"}
    assert set(courses["SIEN6006"]["detailed_weeks"]) == {"1", "2"}
