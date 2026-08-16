from io import BytesIO
import importlib.util
import json
from pathlib import Path


SYNC_API_PATH = Path(__file__).resolve().parents[1] / "scripts" / "sync_api.py"
spec = importlib.util.spec_from_file_location("unisydneybuddy_sync_api", SYNC_API_PATH)
assert spec and spec.loader
sync_api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_api)


def test_remote_sync_round_trip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(sync_api, "STORE", tmp_path)
    sync_id = "student_private_token_1234"
    snapshot = {
        "schema_version": 1,
        "source": "unisydneybuddy_canvas_connector",
        "canvas_base": "https://canvas.sydney.edu.au",
        "synced_at": "2026-08-16T00:00:00Z",
        "courses": [],
    }
    raw = json.dumps(snapshot).encode("utf-8")
    handler = object.__new__(sync_api.Handler)
    handler.path = f"/canvas-sync?sync_id={sync_id}"
    handler.headers = {"Content-Length": str(len(raw)), "Origin": "chrome-extension://test-extension"}
    handler.rfile = BytesIO(raw)
    handler.wfile = BytesIO()
    statuses: list[int] = []
    handler._send_headers = statuses.append
    handler.do_POST()

    assert statuses == [200]
    assert json.loads(handler.wfile.getvalue()) == {"ok": True}
    assert json.loads(sync_api.snapshot_path(sync_id).read_text(encoding="utf-8")) == snapshot
