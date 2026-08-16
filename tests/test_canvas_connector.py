from __future__ import annotations

import json
from pathlib import Path

import pytest

from unisydneybuddy.canvas_bridge import load_canvas_snapshot, save_canvas_snapshot, validate_canvas_snapshot


ROOT = Path(__file__).resolve().parents[1]


def snapshot() -> dict:
    return {
        "schema_version": 1,
        "source": "unisydneybuddy_canvas_connector",
        "canvas_base": "https://canvas.sydney.edu.au",
        "synced_at": "2026-08-16T04:00:00.000Z",
        "courses": [
            {
                "id": 123,
                "name": "Test Course",
                "course_code": "TEST1000",
                "modules": [],
                "assignments": [],
                "announcements": [],
            }
        ],
    }


def test_canvas_snapshot_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "canvas_snapshot.json"
    save_canvas_snapshot(path, snapshot())
    assert load_canvas_snapshot(path) == snapshot()


def test_canvas_snapshot_rejects_other_domains_and_sources() -> None:
    wrong_domain = snapshot()
    wrong_domain["canvas_base"] = "https://example.com"
    with pytest.raises(ValueError):
        validate_canvas_snapshot(wrong_domain)
    wrong_source = snapshot()
    wrong_source["source"] = "unknown"
    with pytest.raises(ValueError):
        validate_canvas_snapshot(wrong_source)


def test_extension_is_read_only_and_scoped_to_sydney_canvas() -> None:
    manifest = json.loads((ROOT / "canvas_connector" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 3
    assert "https://canvas.sydney.edu.au/*" in manifest["host_permissions"]
    assert all(permission not in manifest["permissions"] for permission in ["cookies", "downloads", "webRequest"])
    content_script = (ROOT / "canvas_connector" / "canvas-content.js").read_text(encoding="utf-8")
    assert 'method: "POST"' not in content_script
    assert 'method: "PUT"' not in content_script
    assert 'method: "DELETE"' not in content_script
    assert "/modules" in content_script
    assert "/assignments" in content_script
    assert "/announcements" in content_script
