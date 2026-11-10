#!/usr/bin/env python3
"""Small authenticated OpenAI-compatible gateway for a local llama.cpp server.

The gateway deliberately binds to loopback only. External clients reach it through
an SSH tunnel, so the model server is never exposed directly to the network.
"""

from __future__ import annotations

import hmac
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


UPSTREAM = os.environ.get("GEMMA_UPSTREAM_URL", "http://127.0.0.1:18080").rstrip("/")
API_KEY = os.environ.get("GEMMA_API_KEY", "")
MAX_BODY_BYTES = int(os.environ.get("GEMMA_MAX_BODY_BYTES", str(64 * 1024 * 1024)))

ROUTES = {
    "/health": ("GET", "/health", False),
    "/v1/models": ("GET", "/v1/models", True),
    "/v1/chat/completions": ("POST", "/v1/chat/completions", True),
    "/v1/responses": ("POST", "/v1/responses", True),
}


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False) + "\n").encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "codex-gemma-gateway/1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, status: int, value: Any) -> None:
        body = json_bytes(value)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        if not API_KEY:
            return False
        supplied = self.headers.get("Authorization", "")
        if supplied.startswith("Bearer "):
            supplied = supplied[7:]
        supplied = supplied or self.headers.get("X-API-Key", "")
        return hmac.compare_digest(supplied.encode("utf-8"), API_KEY.encode("utf-8"))

    def _read_body(self) -> bytes | None:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            self._send_json(411, {"error": {"message": "Content-Length is required"}})
            return None
        try:
            length = int(raw_length)
        except ValueError:
            self._send_json(400, {"error": {"message": "invalid Content-Length"}})
            return None
        if length < 0 or length > MAX_BODY_BYTES:
            self._send_json(413, {"error": {"message": "request body is too large"}})
            return None
        return self.rfile.read(length)

    def _proxy(self, method: str, upstream_path: str, body: bytes | None) -> None:
        headers = {
            "Content-Type": self.headers.get("Content-Type", "application/json"),
            "Accept": self.headers.get("Accept", "application/json"),
            "User-Agent": "codex-gemma-gateway/1",
        }
        if "Authorization" in self.headers:
            headers["Authorization"] = self.headers["Authorization"]
        request = urllib.request.Request(
            UPSTREAM + upstream_path,
            data=body,
            headers=headers,
            method=method,
        )
        try:
            response = urllib.request.urlopen(request, timeout=600)
        except urllib.error.HTTPError as exc:
            response_body = exc.read()
            self.send_response(exc.code)
            self.send_header("Content-Type", exc.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(response_body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(response_body)
            return
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            self._send_json(502, {"error": {"message": f"upstream unavailable: {exc}"}})
            return

        with response:
            self.send_response(response.status)
            self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
            self.send_header("Transfer-Encoding", "chunked")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(f"{len(chunk):X}\r\n".encode("ascii"))
                    self.wfile.write(chunk)
                    self.wfile.write(b"\r\n")
                    self.wfile.flush()
                self.wfile.write(b"0\r\n\r\n")
            except (BrokenPipeError, ConnectionResetError):
                self.close_connection = True

    def _dispatch(self, method: str) -> None:
        route = ROUTES.get(self.path)
        if route is None:
            self._send_json(404, {"error": {"message": "unknown API endpoint"}})
            return
        allowed_method, upstream_path, needs_auth = route
        if method != allowed_method:
            self.send_response(405)
            self.send_header("Allow", allowed_method)
            self.end_headers()
            return
        if needs_auth and not self._authorized():
            self._send_json(401, {"error": {"message": "missing or invalid Bearer API key"}})
            return
        body = self._read_body() if method == "POST" else None
        if body is None and method == "POST":
            return
        self._proxy(method, upstream_path, body)

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")


def main() -> int:
    if not API_KEY:
        print("GEMMA_API_KEY must be set", file=sys.stderr)
        return 2
    host = os.environ.get("GEMMA_BIND_HOST", "127.0.0.1")
    port = int(os.environ.get("GEMMA_BIND_PORT", "18081"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"codex-gemma-gateway listening on http://{host}:{port} -> {UPSTREAM}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
