"""Hourly synthetic sales + purchase generator and importer for local demos.

Run once:
    python -m scripts.hourly_demo --business-id <UUID> --once

Run continuously (one batch per hour):
    python -m scripts.hourly_demo --business-id <UUID>

This intentionally uses the same CSV preparation and persistence pipeline as
the API, but runs locally against DATABASE_URL. It is a development/demo tool,
not a production scheduler or a source of real business data.
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import random
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from packages.data.business_brain.ingestion.orchestrator import prepare_file
from packages.data.business_brain.ingestion.persistence import persist_ingestion_run
from packages.data.business_brain.ingestion.purchase_repository import persist_purchases
from packages.data.business_brain.ingestion.repository import persist_sales
from packages.shared.database.models import BusinessModel
from packages.shared.database.session import SessionLocal

LOGGER = logging.getLogger("business_brain.hourly_demo")
DATA_DIR = Path(os.getenv("BB_DEMO_DATA_DIR", "data/hourly_demo"))
PRODUCTS = (
    ("HDMI Cable 2M", "Prime Cables", 40.0, 75.0),
    ("USB-C Cable 1M", "Metro Components", 55.0, 95.0),
    ("CAT6 LAN Cable", "Prime Cables", 30.0, 58.0),
    ("USB-A Adapter", "Metro Components", 22.0, 45.0),
)
CUSTOMERS = ("Alpha Traders", "Beta Retail", "City Electronics", "North Star Stores")


@dataclass(frozen=True)
class GeneratedBatch:
    purchase_csv: Path
    sales_csv: Path
    purchase_rows: int
    sales_rows: int
    batch_id: str


def generate_batch(output_dir: Path = DATA_DIR, *, now: datetime | None = None,
                   rng: random.Random | None = None) -> GeneratedBatch:
    """Generate related purchase/sales CSVs with unique hourly invoice IDs."""
    now = now or datetime.now().astimezone()
    rng = rng or random.Random()
    stamp = now.strftime("%Y%m%dT%H%M%S")
    batch_id = f"DEMO-{stamp}-{rng.randrange(1000, 9999)}"
    output_dir.mkdir(parents=True, exist_ok=True)
    purchase_path = output_dir / f"{batch_id}-purchases.csv"
    sales_path = output_dir / f"{batch_id}-sales.csv"
    purchase_fields = ["invoice_number", "transaction_date", "supplier_name",
                       "product_name", "quantity", "unit_price", "total_amount"]
    sales_fields = ["invoice_number", "transaction_date", "customer_name",
                    "product_name", "quantity", "unit_price", "total_amount"]

    purchase_rows: list[dict[str, str]] = []
    sales_rows: list[dict[str, str]] = []
    transaction_date = now.date().isoformat()
    for index, (product, supplier, base_cost, sell_price) in enumerate(PRODUCTS, start=1):
        # A modest stochastic cost change makes trend detection possible over
        # repeated runs without ever making a sale exceed its purchase quantity.
        cost = round(base_cost * rng.uniform(0.96, 1.18), 2)
        purchased = rng.randint(18, 45)
        sold = rng.randint(5, min(14, purchased))
        purchase_rows.append({
            "invoice_number": f"{batch_id}-P-{index}",
            "transaction_date": transaction_date,
            "supplier_name": supplier,
            "product_name": product,
            "quantity": str(purchased),
            "unit_price": f"{cost:.2f}",
            "total_amount": f"{purchased * cost:.2f}",
        })
        sales_rows.append({
            "invoice_number": f"{batch_id}-S-{index}",
            "transaction_date": transaction_date,
            "customer_name": rng.choice(CUSTOMERS),
            "product_name": product,
            "quantity": str(sold),
            "unit_price": f"{sell_price:.2f}",
            "total_amount": f"{sold * sell_price:.2f}",
        })

    for path, fields, rows in (
        (purchase_path, purchase_fields, purchase_rows),
        (sales_path, sales_fields, sales_rows),
    ):
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    return GeneratedBatch(purchase_path, sales_path, len(purchase_rows),
                          len(sales_rows), batch_id)


def import_batch(business_id: UUID, batch: GeneratedBatch) -> dict[str, object]:
    """Import both generated CSVs atomically through canonical ingestion."""
    with SessionLocal() as db:
        business = db.execute(
            select(BusinessModel).where(BusinessModel.id == business_id)
        ).scalar_one_or_none()
        if business is None:
            raise ValueError(f"Business not found: {business_id}")

        purchase_result, purchase_prepared = prepare_file(
            batch.purchase_csv, source_name=batch.purchase_csv.name
        )
        sales_result, sales_prepared = prepare_file(
            batch.sales_csv, source_name=batch.sales_csv.name
        )
        if purchase_result.rows_rejected or sales_result.rows_rejected:
            raise ValueError(
                "Generated CSV failed validation: "
                f"purchases rejected={purchase_result.rows_rejected}, "
                f"sales rejected={sales_result.rows_rejected}"
            )

        try:
            purchase_run = persist_ingestion_run(db, business_id, purchase_result)
            sales_run = persist_ingestion_run(db, business_id, sales_result)
            purchases = persist_purchases(
                db, business_id, [row.values for row in purchase_prepared]
            )
            sales = persist_sales(db, business_id, [row.values for row in sales_prepared])
            db.commit()
        except Exception:
            db.rollback()
            raise

        return {
            "batch_id": batch.batch_id,
            "purchase_file": batch.purchase_csv.name,
            "sales_file": batch.sales_csv.name,
            "purchase_invoices_created": purchases["created"],
            "sales_invoices_created": sales["created"],
            "purchase_run_id": str(purchase_run.id),
            "sales_run_id": str(sales_run.id),
        }


def run_forever(business_id: UUID, *, interval_seconds: int = 3600,
                output_dir: Path = DATA_DIR, run_immediately: bool = True) -> None:
    if interval_seconds < 1:
        raise ValueError("interval_seconds must be positive")
    while True:
        if run_immediately:
            try:
                batch = generate_batch(output_dir)
                result = import_batch(business_id, batch)
                LOGGER.info("Imported hourly demo batch: %s", result)
            except Exception:
                LOGGER.exception("Hourly demo batch failed; next run remains scheduled")
        run_immediately = True
        time.sleep(interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--business-id", default=os.getenv("BB_DEMO_BUSINESS_ID"))
    parser.add_argument("--interval-seconds", type=int, default=3600)
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--once", action="store_true", help="Generate and import one batch, then exit")
    parser.add_argument("--no-immediate-run", action="store_true",
                        help="Wait one interval before the first batch")
    args = parser.parse_args()
    if not args.business_id:
        parser.error("provide --business-id or set BB_DEMO_BUSINESS_ID")
    business_id = UUID(args.business_id)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if args.once:
        batch = generate_batch(args.output_dir)
        print(import_batch(business_id, batch))
        return
    run_forever(business_id, interval_seconds=args.interval_seconds,
                output_dir=args.output_dir, run_immediately=not args.no_immediate_run)


if __name__ == "__main__":
    main()
