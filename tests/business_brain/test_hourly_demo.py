import csv
import random
from datetime import datetime
from pathlib import Path

from scripts.hourly_demo import generate_batch


def test_hourly_demo_generates_related_sales_and_purchase_csvs(tmp_path: Path):
    batch = generate_batch(
        tmp_path,
        now=datetime(2026, 9, 28, 10, 0, 0),
        rng=random.Random(7),
    )

    with batch.purchase_csv.open(newline="", encoding="utf-8") as stream:
        purchases = list(csv.DictReader(stream))
    with batch.sales_csv.open(newline="", encoding="utf-8") as stream:
        sales = list(csv.DictReader(stream))

    assert len(purchases) == len(sales) == 4
    purchase_by_product = {row["product_name"]: row for row in purchases}
    sales_by_product = {row["product_name"]: row for row in sales}
    assert purchase_by_product.keys() == sales_by_product.keys()

    for product, purchase in purchase_by_product.items():
        sale = sales_by_product[product]
        assert int(purchase["quantity"]) >= int(sale["quantity"])
        assert float(purchase["total_amount"]) == round(
            int(purchase["quantity"]) * float(purchase["unit_price"]), 2
        )
        assert float(sale["total_amount"]) == round(
            int(sale["quantity"]) * float(sale["unit_price"]), 2
        )
        assert purchase["transaction_date"] == sale["transaction_date"] == "2026-09-28"

    assert len({row["invoice_number"] for row in purchases + sales}) == 8
    assert batch.purchase_csv.exists()
    assert batch.sales_csv.exists()
