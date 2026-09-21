from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path


FIXTURE = Path(__file__).parents[1] / "fixtures" / "golden_sme_distribution.json"


def test_golden_sme_fixture_is_self_consistent():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    revenue = sum(Decimal(str(row["total"])) for row in data["sales"])
    purchase_spend = sum(Decimal(str(row["total"])) for row in data["purchases"])

    assert revenue == Decimal(str(data["expected"]["revenue"]))
    assert purchase_spend == Decimal(str(data["expected"]["purchase_spend"]))

    purchases = {
        row["product"]: Decimal(str(row["quantity"]))
        for row in data["purchases"]
    }
    sales = {
        row["product"]: Decimal(str(row["quantity"]))
        for row in data["sales"]
    }

    for product, expected_units in data["expected"]["inventory_units"].items():
        assert purchases[product] - sales[product] == Decimal(str(expected_units))


def test_golden_sme_fixture_has_stable_business_entities():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert len({row["external_id"] for row in data["customers"]}) == len(data["customers"])
    assert len({row["external_id"] for row in data["suppliers"]}) == len(data["suppliers"])
    assert len({row["sku"] for row in data["products"]}) == len(data["products"])

    assert all(row["invoice_number"] for row in data["sales"])
    assert all(row["invoice_number"] for row in data["purchases"])
    assert all(row["quantity"] > 0 for row in data["sales"] + data["purchases"])
