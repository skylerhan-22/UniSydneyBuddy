from pathlib import Path

from unisydneybuddy.state_store import load_json_state, record_snapshot, save_feedback, save_json_state, snapshot_changes


def test_state_and_feedback_persist(tmp_path: Path) -> None:
    database = tmp_path / "app.db"
    save_json_state(database, "weekly", {"week": 2})
    assert load_json_state(database, "weekly", {}) == {"week": 2}
    save_feedback(database, context="weekly", course_code="SIEN6006", language="中文", rating="helpful", comment="clear")


def test_snapshot_history_is_idempotent(tmp_path: Path) -> None:
    database = tmp_path / "app.db"
    snapshot = {"synced_at": "2026-08-16T00:00:00Z", "courses": []}
    assert record_snapshot(database, snapshot) is True
    assert record_snapshot(database, snapshot) is False
    assert snapshot_changes(database, snapshot) == {"added": 0, "changed": 0, "removed": 0}


def test_snapshot_change_baselines_are_isolated_per_user(tmp_path: Path) -> None:
    database = tmp_path / "app.db"
    snapshot = {
        "courses": [
            {"id": 1, "modules": [], "assignments": [{"id": 9, "name": "A1"}], "announcements": []}
        ]
    }
    assert snapshot_changes(database, snapshot, namespace="student-a")["added"] == 1
    assert snapshot_changes(database, snapshot, namespace="student-a")["added"] == 0
    assert snapshot_changes(database, snapshot, namespace="student-b")["added"] == 1
