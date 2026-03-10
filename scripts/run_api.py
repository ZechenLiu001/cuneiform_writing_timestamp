#!/usr/bin/env python3
from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dataclasses import asdict

from core.asr import ASRError, ensure_transcript_segments
from core.models import parse_session_input
from core.processor import process_session
from core.session_log import InMemorySessionLog

LOG = InMemorySessionLog()


class Handler(BaseHTTPRequestHandler):
    server_version = "TimelineDemoHTTP/0.1"

    def _send_json(self, data: dict, status: int = HTTPStatus.OK) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._send_json({"ok": True})
            return

        if path.startswith("/sessions/"):
            session_id = path.split("/")[-1]
            item = LOG.get(session_id)
            if item is None:
                self._send_json({"error": "session_not_found", "session_id": session_id}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json(item)
            return

        self._send_json({"error": "not_found", "path": path}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/process":
            self._send_json({"error": "not_found", "path": path}, status=HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length == 0:
            self._send_json({"error": "empty_body"}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            payload = ensure_transcript_segments(payload)
            session = parse_session_input(payload)
            result = process_session(session)
        except (json.JSONDecodeError, KeyError, TypeError, ValueError, ASRError) as exc:
            self._send_json({"error": "bad_request", "message": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        LOG.save(result)
        self._send_json(asdict(result), status=HTTPStatus.OK)


def run(host: str = "0.0.0.0", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
