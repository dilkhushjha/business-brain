from pathlib import Path

from packages.data.business_brain.ingestion.orchestrator import prepare_file
from packages.data.business_brain.quality.report import build_quality_report


def test_prepare_csv(tmp_path: Path):
    path = tmp_path / "sales.csv"
    path.write_text(
        "Party Name,Invoice No,Bill Date,Qty,Rate,Total\n"
        "ABC Electricals,INV-1,27/08/2026,2,100,200\n"
        "XYZ Electricals,INV-2,28/08/2026,three,100,300\n",
        encoding="utf-8",
    )
    result, rows = prepare_file(path)
    assert result.rows_read == 2
    assert result.rows_accepted == 1
    assert result.rows_rejected == 1
    assert rows[0].values["customer_name"] == "ABC Electricals"
    report = build_quality_report(result)
    assert report.score == 50.0
