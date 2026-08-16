from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
from typing import Any


MAX_BODY_BYTES = 12 * 1024 * 1024
_server: ThreadingHTTPServer | None = None
_server_lock = threading.Lock()


def validate_canvas_snapshot(payload: Any) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Canvas snapshot must be a JSON object")
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported Canvas snapshot schema")
    if payload.get("source") != "unisydneybuddy_canvas_connector":
        raise ValueError("Unknown Canvas snapshot source")
    canvas_base = payload.get("canvas_base")
    if canvas_base != "https://canvas.sydney.edu.au":
        raise ValueError("Only canvas.sydney.edu.au is allowed in this prototype")
    courses = payload.get("courses")
    if not isinstance(courses, list) or len(courses) > 30:
        raise ValueError("Canvas snapshot courses must be a list of at most 30 items")
    for course in courses:
        if not isinstance(course, dict) or not isinstance(course.get("id"), int):
            raise ValueError("Every Canvas course must have a numeric id")
        for field in ("modules", "assignments", "announcements"):
            if not isinstance(course.get(field, []), list):
                raise ValueError(f"Canvas course field {field} must be a list")
    return payload


def save_canvas_snapshot(path: Path, payload: dict) -> None:
    validated = validate_canvas_snapshot(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        suffix=".json",
        dir=path.parent,
        delete=False,
    ) as handle:
        json.dump(validated, handle, ensure_ascii=False, indent=2)
        temporary_path = Path(handle.name)
    temporary_path.replace(path)


def load_canvas_snapshot(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return validate_canvas_snapshot(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError):
        return None


def _handler_for(snapshot_path: Path) -> type[BaseHTTPRequestHandler]:
    class CanvasBridgeHandler(BaseHTTPRequestHandler):
        server_version = "UniSydneyBuddyCanvasBridge/0.1"

        def _allowed_origin(self) -> str | None:
            origin = self.headers.get("Origin", "")
            return origin if origin.startswith("chrome-extension://") else None

        def _headers(self, status: int, *, content_type: str = "application/json") -> None:
            self.send_response(status)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            origin = self._allowed_origin()
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

        def do_OPTIONS(self) -> None:  # noqa: N802
            if not self._allowed_origin():
                self._headers(403)
                return
            self._headers(204)

        def do_GET(self) -> None:  # noqa: N802
            if self.path != "/health":
                self._headers(404)
                self.wfile.write(b'{"ok":false}')
                return
            self._headers(200)
            self.wfile.write(b'{"ok":true}')

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/canvas-sync" or not self._allowed_origin():
                self._headers(403)
                self.wfile.write(b'{"ok":false,"error":"forbidden"}')
                return
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                if content_length <= 0 or content_length > MAX_BODY_BYTES:
                    raise ValueError("Invalid request size")
                payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
                save_canvas_snapshot(snapshot_path, payload)
            except (UnicodeDecodeError, json.JSONDecodeError, OSError, ValueError) as exc:
                self._headers(400)
                self.wfile.write(json.dumps({"ok": False, "error": str(exc)}).encode("utf-8"))
                return
            self._headers(200)
            self.wfile.write(b'{"ok":true}')

        def log_message(self, _format: str, *_args: object) -> None:
            return

    return CanvasBridgeHandler


def start_canvas_bridge(snapshot_path: Path, port: int = 8765) -> bool:
    global _server
    with _server_lock:
        if _server is not None:
            return True
        try:
            _server = ThreadingHTTPServer(("127.0.0.1", port), _handler_for(snapshot_path))
        except OSError:
            return False
        thread = threading.Thread(target=_server.serve_forever, name="canvas-bridge", daemon=True)
        thread.start()
        return True
