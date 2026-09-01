from __future__ import annotations

from pathlib import Path

from apps.connector.business_brain_connector.state import SyncState


def test_new_checksum_is_not_synced_and_should_retry(tmp_path: Path):
    state = SyncState(tmp_path / "state.json")
    assert state.contains("abc") is False
    assert state.should_retry("abc", max_attempts=3) is True
    assert state.attempts("abc") == 0


def test_mark_synced_persists_across_instances(tmp_path: Path):
    path = tmp_path / "state.json"
    SyncState(path).mark_synced("abc", "sales.csv")

    reloaded = SyncState(path)
    assert reloaded.contains("abc") is True
    assert reloaded.attempts("abc") == 1


def test_mark_failed_increments_attempts_and_records_error(tmp_path: Path):
    state = SyncState(tmp_path / "state.json")
    state.mark_failed("abc", "sales.csv", "connection refused")
    state.mark_failed("abc", "sales.csv", "connection refused")

    assert state.contains("abc") is False
    assert state.attempts("abc") == 2
    assert state.values["abc"]["last_error"] == "connection refused"


def test_should_retry_respects_max_attempts(tmp_path: Path):
    state = SyncState(tmp_path / "state.json")
    state.mark_failed("abc", "sales.csv", "err")
    state.mark_failed("abc", "sales.csv", "err")
    assert state.should_retry("abc", max_attempts=2) is False
    assert state.should_retry("abc", max_attempts=3) is True


def test_synced_checksum_is_not_eligible_for_retry(tmp_path: Path):
    state = SyncState(tmp_path / "state.json")
    state.mark_synced("abc", "sales.csv")
    assert state.should_retry("abc", max_attempts=10) is False


def test_pending_excludes_synced_entries(tmp_path: Path):
    state = SyncState(tmp_path / "state.json")
    state.mark_synced("synced-one", "a.csv")
    state.mark_failed("failed-one", "b.csv", "err")
    assert list(state.pending().keys()) == ["failed-one"]
