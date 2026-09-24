from __future__ import annotations

from datetime import date, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.api.routes.agent import router as agent_router
from apps.api.app.api.routes.auth import router as auth_router
from apps.api.app.api.routes.ingestion import router as ingestion_router
from apps.api.app.api.routes.kpis import router as kpis_router
from apps.api.app.api.routes.signals import router as signals_router
from packages.shared.database.session import get_db


def _client(db_session):
    app = FastAPI()
    for router in (auth_router, ingestion_router, kpis_router, signals_router, agent_router):
        app.include_router(router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _register(client: TestClient) -> tuple[str, str]:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "goldenpath",
            "email": "goldenpath@example.com",
            "password": "StrongPassword!123",
            "business_name": "Golden Path Distribution",
            "industry": "distribution",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    return payload["access_token"], payload["user"]["business"]["id"]


def test_complete_golden_path_from_csv_to_business_brain(db_session):
    client = _client(db_session)
    token, business_id = _register(client)
    headers = {"Authorization": f"Bearer {token}"}

    today = date.today()
    historical = (today - timedelta(days=50)).strftime("%d-%m-%Y")
    recent_purchase = (today - timedelta(days=10)).strftime("%d-%m-%Y")
    recent_sale = (today - timedelta(days=5)).strftime("%d-%m-%Y")

    historical_purchase = (
        "Bill Date,Supplier Name,Item Name,Qty,Rate,Net Amount,Invoice No\n"
        f"{historical},Prime Cables,HDMI Cable 2M,10,40,400,P-HIST-001\n"
    )
    recent_purchase_csv = (
        "Bill Date,Supplier Name,Item Name,Qty,Rate,Net Amount,Invoice No\n"
        f"{recent_purchase},Prime Cables,HDMI Cable 2M,150,80,12000,P-CUR-001\n"
    )
    sale_csv = (
        "Bill Date,Party Name,Item Name,Qty,Rate,Net Amount,Cost Price,Invoice No\n"
        f"{recent_sale},Alpha Traders,HDMI Cable 2M,60,75,4500,80,S-CUR-001\n"
    )

    first_purchase = client.post(
        f"/api/ingestion/import-purchases/{business_id}",
        headers=headers,
        files={"files": ("historical_purchase.csv", historical_purchase.encode(), "text/csv")},
    )
    assert first_purchase.status_code == 200, first_purchase.text
    assert first_purchase.json()["purchases_created"] == 1

    second_purchase = client.post(
        f"/api/ingestion/import-purchases/{business_id}",
        headers=headers,
        files={"files": ("recent_purchase.csv", recent_purchase_csv.encode(), "text/csv")},
    )
    assert second_purchase.status_code == 200, second_purchase.text
    assert second_purchase.json()["purchases_created"] == 1

    sale_import = client.post(
        f"/api/ingestion/import/{business_id}",
        headers=headers,
        files={"files": ("sale.csv", sale_csv.encode(), "text/csv")},
    )
    assert sale_import.status_code == 200, sale_import.text
    assert sale_import.json()["sales_created"] == 1

    kpis = client.get(f"/api/kpis/sales/{business_id}", headers=headers)
    assert kpis.status_code == 200, kpis.text
    kpi_map = {item["name"]: item for item in kpis.json()}
    assert kpi_map["total_revenue"]["value"] == "4500.00"
    assert kpi_map["total_invoice_count"]["value"] == "1"

    signals = client.get(f"/api/signals/{business_id}", headers=headers)
    assert signals.status_code == 200, signals.text
    signal_codes = {item["code"] for item in signals.json()}
    assert "PRODUCT_MARGIN_DETERIORATION" in signal_codes
    assert "SUPPLIER_PRICE_INCREASE" in signal_codes

    answer = client.post(
        f"/api/agent/{business_id}/ask",
        headers=headers,
        json={"question": "Why is my margin under pressure?"},
    )
    assert answer.status_code == 200, answer.text
    payload = answer.json()

    assert payload["confidence"] == "grounded"
    assert payload["intent"] == "root_cause"
    assert "HDMI Cable 2M" in payload["answer"]
    assert "MARGIN_PRESSURE" in {
        str(item.get("code"))
        for item in payload["signals"]
        if isinstance(item, dict)
    } or any(
        "MARGIN_PRESSURE" in str(item.get("situation_code"))
        for item in payload.get("situation_history", [])
        if isinstance(item, dict)
    ) or "cross-domain business situation" in payload["answer"].lower()

    assert any(
        item.get("code") == "INVESTIGATE_MARGIN_PRESSURE"
        for item in payload.get("decision_actions", [])
        if isinstance(item, dict)
    )
