from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from unisydneybuddy.canvas_bridge import MAX_BODY_BYTES, save_canvas_snapshot  # noqa: E402


STORE = Path(os.environ.get("CANVAS_SYNC_STORE", ROOT / "data" / "sync"))
TOKEN = re.compile(r"^[A-Za-z0-9_-]{16,80}$")


def snapshot_path(sync_id: str) -> Path:
    if not TOKEN.fullmatch(sync_id):
        raise ValueError("Invalid sync id")
    return STORE / f"{sync_id}.json"


class Handler(BaseHTTPRequestHandler):
    def _send_headers(self, status: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        origin = self.headers.get("Origin", "")
        if origin.startswith("chrome-extension://"):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def sync_id(self) -> str:
        return parse_qs(urlparse(self.path).query).get("sync_id", [""])[0]

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send_headers(204)

    def do_GET(self) -> None:  # noqa: N802
        route = urlparse(self.path).path
        if route == "/health":
            self._send_headers(200)
            self.wfile.write(b'{"ok":true}')
            return
        if route != "/canvas-snapshot":
            self._send_headers(404)
            return
        try:
            path = snapshot_path(self.sync_id())
            body = path.read_bytes()
        except (ValueError, OSError):
            self._send_headers(404)
            self.wfile.write(b'{"ok":false,"error":"snapshot_not_found"}')
            return
        self._send_headers(200)
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/canvas-sync" or not self.headers.get("Origin", "").startswith("chrome-extension://"):
            self._send_headers(403)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > MAX_BODY_BYTES:
                raise ValueError("Invalid request size")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            save_canvas_snapshot(snapshot_path(self.sync_id()), payload)
        except (ValueError, OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self._send_headers(400)
            self.wfile.write(json.dumps({"ok": False, "error": str(exc)}).encode())
            return
        self._send_headers(200)
        self.wfile.write(b'{"ok":true}')

    def log_message(self, _format: str, *_args: object) -> None:
        return


if __name__ == "__main__":
    STORE.mkdir(parents=True, exist_ok=True)
    port = int(os.environ.get("PORT", "8765"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
