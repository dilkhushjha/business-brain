from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from apps.connector.business_brain_connector.uploader import (
    UploadError,
    register_connector,
    send_heartbeat,
)


class _ScriptedServer:
    """A tiny local HTTP server that returns a scripted sequence of
    responses, one per request, and records what it received."""

    def __init__(self, responses: list[tuple[int, dict]]):
        self.responses = list(responses)
        self.requests: list[dict] = []
        handler = self._make_handler()
        self.server = HTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}"

    def _make_handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                self.rfile.read(length)
                outer.requests.append({"path": self.path, "headers": dict(self.headers.items())})
                status, payload = outer.responses.pop(0) if outer.responses else (500, {"detail": "no scripted response"})
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode("utf-8"))

            def log_message(self, *args):
                pass

        return Handler

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def test_register_connector_sends_registration_key_header():
    with _ScriptedServer([(200, {"connector_id": "c1", "business_id": "biz-1", "token": "tok_abc"})]) as server:
        result = register_connector("biz-1", server.base_url, registration_key="secret-key")

    assert result["token"] == "tok_abc"
    assert server.requests[0]["path"] == "/connectors/register/biz-1"
    assert server.requests[0]["headers"]["X-Connector-Registration-Key"] == "secret-key"


def test_register_connector_without_key_omits_header():
    with _ScriptedServer([(200, {"connector_id": "c1", "business_id": "biz-1", "token": "tok_abc"})]) as server:
        register_connector("biz-1", server.base_url)
    assert "X-Connector-Registration-Key" not in server.requests[0]["headers"]


def test_register_connector_raises_on_rejection():
    with _ScriptedServer([(401, {"detail": "A valid connector registration key is required"})]) as server:
        with pytest.raises(UploadError, match="HTTP 401"):
            register_connector("biz-1", server.base_url)


def test_send_heartbeat_uses_bearer_token():
    with _ScriptedServer([(200, {"status": "connected"})]) as server:
        result = send_heartbeat(server.base_url, "tok_abc")

    assert result["status"] == "connected"
    assert server.requests[0]["path"] == "/connectors/heartbeat"
    assert server.requests[0]["headers"]["Authorization"] == "Bearer tok_abc"


def test_send_heartbeat_without_token_raises_before_network_call():
    with pytest.raises(UploadError, match="token is required"):
        send_heartbeat("http://127.0.0.1:1", "")


def test_send_heartbeat_raises_on_server_error():
    with _ScriptedServer([(500, {"detail": "boom"})]) as server:
        with pytest.raises(UploadError, match="HTTP 500"):
            send_heartbeat(server.base_url, "tok_abc")
