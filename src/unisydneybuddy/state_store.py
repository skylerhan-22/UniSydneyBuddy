"""Small local persistence layer for AI results, sync history and feedback."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


def _connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS app_state (key TEXT PRIMARY KEY, value_json TEXT NOT NULL, updated_at TEXT NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, context TEXT NOT NULL, course_code TEXT NOT NULL, language TEXT NOT NULL, rating TEXT NOT NULL, comment TEXT NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS sync_history (snapshot_hash TEXT PRIMARY KEY, synced_at TEXT NOT NULL, recorded_at TEXT NOT NULL, summary_json TEXT NOT NULL)"
    )
    return connection


def load_json_state(path: Path, key: str, default: Any) -> Any:
    with _connect(path) as connection:
        row = connection.execute("SELECT value_json FROM app_state WHERE key = ?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row[0])
    except json.JSONDecodeError:
        return default


def save_json_state(path: Path, key: str, value: Any) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect(path) as connection:
        connection.execute(
            "INSERT INTO app_state(key, value_json, updated_at) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json, updated_at=excluded.updated_at",
            (key, json.dumps(value, ensure_ascii=False), now),
        )


def save_feedback(
    path: Path,
    *,
    context: str,
    course_code: str,
    language: str,
    rating: str,
    comment: str,
) -> None:
    with _connect(path) as connection:
        connection.execute(
            "INSERT INTO feedback(created_at, context, course_code, language, rating, comment) VALUES(?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), context, course_code, language, rating, comment.strip()),
        )


def record_snapshot(path: Path, snapshot: dict) -> bool:
    """Record a snapshot once. Return True only when this is a new sync."""
    raw = json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    summary = {
        "courses": len(snapshot.get("courses", [])),
        "modules": sum(len(course.get("modules", [])) for course in snapshot.get("courses", [])),
        "assignments": sum(len(course.get("assignments", [])) for course in snapshot.get("courses", [])),
        "announcements": sum(len(course.get("announcements", [])) for course in snapshot.get("courses", [])),
    }
    with _connect(path) as connection:
        exists = connection.execute("SELECT 1 FROM sync_history WHERE snapshot_hash = ?", (digest,)).fetchone()
        if exists:
            return False
        connection.execute(
            "INSERT INTO sync_history(snapshot_hash, synced_at, recorded_at, summary_json) VALUES(?,?,?,?)",
            (
                digest,
                snapshot.get("synced_at") or "",
                datetime.now(timezone.utc).isoformat(),
                json.dumps(summary, ensure_ascii=False),
            ),
        )
    return True


def snapshot_changes(path: Path, snapshot: dict, *, namespace: str = "local") -> dict[str, int]:
    """Compare stable content fingerprints with the previous synced snapshot."""
    current: dict[str, str] = {}
    for course in snapshot.get("courses", []):
        course_id = course.get("id")
        for module in course.get("modules", []):
            for item in module.get("items", []):
                value = json.dumps(item, ensure_ascii=False, sort_keys=True)
                current[f"module:{course_id}:{item.get('id')}"] = hashlib.sha256(value.encode()).hexdigest()
        for assignment in course.get("assignments", []):
            value = json.dumps(assignment, ensure_ascii=False, sort_keys=True)
            current[f"assignment:{course_id}:{assignment.get('id')}"] = hashlib.sha256(value.encode()).hexdigest()
        for announcement in course.get("announcements", []):
            value = json.dumps(announcement, ensure_ascii=False, sort_keys=True)
            current[f"announcement:{course_id}:{announcement.get('id')}"] = hashlib.sha256(value.encode()).hexdigest()
    state_key = f"canvas-content-index:{namespace}"
    previous = load_json_state(path, state_key, {})
    changes = {
        "added": sum(key not in previous for key in current),
        "changed": sum(key in previous and previous[key] != value for key, value in current.items()),
        "removed": sum(key not in current for key in previous),
    }
    save_json_state(path, state_key, current)
    return changes
