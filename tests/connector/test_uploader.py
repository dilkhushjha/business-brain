from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from apps.connector.business_brain_connector.uploader import UploadError, upload_file


class _ScriptedServer:
    """A tiny local HTTP server that returns a scripted sequence of
    responses, one per request, and records what it received. Lets tests
    exercise the real multipart wire format without hitting the network."""

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
                body = self.rfile.read(length)
                outer.requests.append(
                    {
                        "path": self.path,
                        "headers": dict(self.headers.items()),
                        "body_len": len(body),
                    }
                )
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


@pytest.fixture()
def source_file(tmp_path: Path) -> Path:
    path = tmp_path / "sales.csv"
    path.write_text("Bill Date,Party Name,Qty,Rate,Net Amount\n27-08-2026,ABC,10,20,200\n", encoding="utf-8")
    return path


def test_successful_upload_returns_result(source_file):
    with _ScriptedServer([(200, {"run_id": "abc123", "sales_created": 1})]) as server:
        result = upload_file(source_file, "biz-1", server.base_url, api_token="secret-token")

    assert result.status_code == 200
    assert result.already_imported is False
    assert result.response_body["run_id"] == "abc123"
    assert server.requests[0]["path"] == "/ingestion/import/biz-1"
    assert server.requests[0]["headers"]["Authorization"] == "Bearer secret-token"
    assert "multipart/form-data" in server.requests[0]["headers"]["Content-Type"]


def test_upload_without_token_omits_auth_header(source_file):
    with _ScriptedServer([(200, {"run_id": "abc123"})]) as server:
        upload_file(source_file, "biz-1", server.base_url)
    assert "Authorization" not in server.requests[0]["headers"]


def test_conflict_is_treated_as_already_imported(source_file):
    with _ScriptedServer([(409, {"detail": "This source file was already imported"})]) as server:
        result = upload_file(source_file, "biz-1", server.base_url)

    assert result.status_code == 409
    assert result.already_imported is True


def test_server_error_raises_upload_error(source_file):
    with _ScriptedServer([(500, {"detail": "boom"})]) as server:
        with pytest.raises(UploadError, match="HTTP 500"):
            upload_file(source_file, "biz-1", server.base_url)


def test_connection_failure_raises_upload_error(source_file):
    with pytest.raises(UploadError, match="Connection error"):
        upload_file(source_file, "biz-1", "http://127.0.0.1:1", timeout=1.0)
