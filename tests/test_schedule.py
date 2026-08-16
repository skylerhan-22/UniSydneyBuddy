from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_unit_outline_schedule_covers_weeks_one_to_thirteen() -> None:
    schedule = json.loads((ROOT / "data" / "evals" / "qbus6600_schedule.json").read_text(encoding="utf-8"))
    assert [item["week"] for item in schedule["weeks"]] == list(range(1, 14))
    assert all(item["title_en"] and item["title_zh"] for item in schedule["weeks"])


def test_unpublished_tutorials_are_not_invented() -> None:
    schedule = json.loads((ROOT / "data" / "evals" / "qbus6600_schedule.json").read_text(encoding="utf-8"))
    week_12 = next(item for item in schedule["weeks"] if item["week"] == 12)
    week_13 = next(item for item in schedule["weeks"] if item["week"] == 13)
    assert week_12["tutorial"] is None
    assert week_13["tutorial"] is None

