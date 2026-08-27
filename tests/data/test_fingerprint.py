from pathlib import Path

from packages.data.business_brain.ingestion.fingerprint import sha256_file


def test_sha256_file(tmp_path: Path):
    source = tmp_path / "sales.csv"
    source.write_text("invoice,amount\nINV-1,100\n", encoding="utf-8")
    assert len(sha256_file(source)) == 64
    assert sha256_file(source) == sha256_file(source)
