from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from apps.connector.business_brain_connector.__main__ import main


class _RegisterServer:
    def __init__(self, response: tuple[int, dict]):
        self.response = response
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
                status, payload = outer.response
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())

            def log_message(self, *args):
                pass

        return Handler

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def test_register_writes_a_ready_to_use_config_file(tmp_path):
    config_path = tmp_path / "connector.config.json"
    with _RegisterServer((200, {"connector_id": "c1", "business_id": "biz-1", "token": "tok_xyz"})) as server:
        rc = main([
            "register",
            "--business-id", "biz-1",
            "--source-dir", str(tmp_path / "exports"),
            "--api-base-url", server.base_url,
            "--config", str(config_path),
        ])

    assert rc == 0
    saved = json.loads(config_path.read_text())
    assert saved["business_id"] == "biz-1"
    assert saved["api_token"] == "tok_xyz"
    assert saved["api_base_url"] == server.base_url


def test_register_refuses_to_overwrite_without_force(tmp_path):
    config_path = tmp_path / "connector.config.json"
    config_path.write_text("{}", encoding="utf-8")

    rc = main([
        "register",
        "--business-id", "biz-1",
        "--source-dir", str(tmp_path),
        "--config", str(config_path),
    ])

    assert rc == 1
    assert config_path.read_text() == "{}"  # untouched


def test_register_reports_failure_from_the_server(tmp_path):
    config_path = tmp_path / "connector.config.json"
    with _RegisterServer((401, {"detail": "A valid connector registration key is required"})) as server:
        rc = main([
            "register",
            "--business-id", "biz-1",
            "--source-dir", str(tmp_path),
            "--api-base-url", server.base_url,
            "--config", str(config_path),
        ])

    assert rc == 1
    assert not config_path.exists()


def test_old_style_invocation_with_no_subcommand_still_works(tmp_path):
    """Backward compatibility: `python -m business_brain_connector --config x`
    (no subcommand) must still resolve to `run`, not fail argument parsing."""
    missing_config = tmp_path / "missing.json"
    rc = main(["--config", str(missing_config)])
    assert rc == 1  # config not found -- but it got there via the `run` path, not an argparse error
