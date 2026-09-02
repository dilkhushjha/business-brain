from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from apps.connector.business_brain_connector.config import ConnectorConfig
from apps.connector.business_brain_connector.fingerprint import fingerprint
from apps.connector.business_brain_connector.state import SyncState
from apps.connector.business_brain_connector.sync import sync_file


class _FlakyServer:
    """Fails the first `fail_times` requests, then succeeds."""

    def __init__(self, fail_times: int):
        self.fail_times = fail_times
        self.request_count = 0
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
                outer.request_count += 1
                if outer.request_count <= outer.fail_times:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(b'{"detail": "temporary failure"}')
                else:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(json.dumps({"run_id": "ok"}).encode())

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
    path.write_text("data", encoding="utf-8")
    return path


@pytest.fixture()
def state(tmp_path: Path) -> SyncState:
    return SyncState(tmp_path / "state.json")


def _config(base_url: str, source_dir: Path, **overrides) -> ConnectorConfig:
    defaults = dict(
        business_id="biz-1",
        source_dir=str(source_dir),
        api_base_url=base_url,
        api_token="test-connector-token",
        max_upload_retries=3,
        retry_backoff_seconds=0.01,
    )
    defaults.update(overrides)
    return ConnectorConfig(**defaults)


def test_successful_sync_marks_state(source_file, state):
    with _FlakyServer(fail_times=0) as server:
        config = _config(server.base_url, source_file.parent)
        assert sync_file(source_file, config, state) is True
    assert state.contains(fingerprint(source_file))


def test_already_synced_file_is_skipped_without_network_call(source_file, state):
    with _FlakyServer(fail_times=0) as server:
        config = _config(server.base_url, source_file.parent)
        sync_file(source_file, config, state)
        assert server.request_count == 1
        # Second call must not hit the network again.
        assert sync_file(source_file, config, state) is True
        assert server.request_count == 1


def test_failed_upload_is_retried_and_eventually_succeeds(source_file, state):
    with _FlakyServer(fail_times=2) as server:
        config = _config(server.base_url, source_file.parent)
        assert sync_file(source_file, config, state) is False
        assert sync_file(source_file, config, state) is False
        assert sync_file(source_file, config, state) is True
    checksum = fingerprint(source_file)
    assert state.contains(checksum)
    assert state.attempts(checksum) == 3


def test_gives_up_after_max_retries(source_file, state):
    with _FlakyServer(fail_times=100) as server:
        config = _config(server.base_url, source_file.parent, max_upload_retries=2)
        assert sync_file(source_file, config, state) is False
        assert sync_file(source_file, config, state) is False
        assert server.request_count == 2
        # Third call should not even attempt the network -- budget exhausted.
        assert sync_file(source_file, config, state) is False
        assert server.request_count == 2


def test_missing_api_token_fails_without_a_network_call(source_file, state):
    with _FlakyServer(fail_times=0) as server:
        config = _config(server.base_url, source_file.parent, api_token=None)
        assert sync_file(source_file, config, state) is False
        assert server.request_count == 0
    checksum = fingerprint(source_file)
    assert "token is required" in state.values[checksum]["last_error"]
