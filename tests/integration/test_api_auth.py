"""HTTP-level authentication and authorization tests."""
from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlalchemy import text

import pytest

from apps.api.app.api.routes.agent import router as agent_router
from apps.api.app.api.routes.auth import router as auth_router
from apps.api.app.api.routes.connectors import router as connectors_router
from apps.api.app.api.routes.kpis import router as kpis_router
from apps.api.app.api.routes.discounts import router as discounts_router
from apps.api.app.api.routes.expenses import router as expenses_router
from apps.api.app.api.routes.ingestion import router as ingestion_router
from apps.api.app.api.routes.inventory import router as inventory_router
from apps.api.app.api.routes.payables import router as payables_router
from apps.api.app.api.routes.signals import router as signals_router
from apps.api.app.api.routes.supplier_risk import router as supplier_risk_router
from packages.shared.database.session import get_db


@pytest.fixture()
def client(db_session):
    app = FastAPI()
    for router in (
        auth_router, connectors_router, kpis_router, signals_router, agent_router,
        payables_router, discounts_router, expenses_router, ingestion_router,
        inventory_router, supplier_risk_router,
    ):
        app.include_router(router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _user_token(client, db_session, business_id) -> str:
    username = f"user_{uuid4().hex[:10]}"
    password = "TestPassword!123"
    user_id = uuid4()
    db_session.execute(
        text("INSERT INTO users (id, username, email, password_hash) VALUES (:id,:username,:email,:hash)"),
        {
            "id": user_id.hex,
            "username": username,
            "email": f"{username}@example.com",
            "hash": PasswordHash.recommended().hash(password),
        },
    )
    db_session.execute(
        text("INSERT INTO user_businesses (user_id, business_id, role) VALUES (:user_id,:business_id,'owner')"),
        {"user_id": user_id.hex, "business_id": business_id.hex},
    )
    db_session.commit()
    response = client.post("/api/auth/login", json={"identifier": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _connector_token(client, business_id) -> str:
    response = client.post(f"/api/connectors/register/{business_id}")
    assert response.status_code == 200, response.text
    return response.json()["token"]


def test_user_registration_and_me(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newowner",
            "email": "newowner@example.com",
            "password": "StrongPassword!123",
            "business_name": "New Electricals",
            "industry": "distribution",
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["access_token"]
    assert data["user"]["username"] == "newowner"
    assert data["user"]["business"]["name"] == "New Electricals"

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me.status_code == 200
    assert me.json()["business"]["name"] == "New Electricals"


def test_login_accepts_username_email_and_phone(client):
    password = "StrongPassword!123"
    client.post("/api/auth/register", json={
        "username": "loginuser", "email": "login@example.com", "phone": "+919999999999",
        "password": password, "business_name": "Login Business", "industry": "retail",
    })
    for identifier in ("loginuser", "login@example.com", "+919999999999"):
        response = client.post("/api/auth/login", json={"identifier": identifier, "password": password})
        assert response.status_code == 200, response.text
        assert response.json()["user"]["username"] == "loginuser"


def test_login_rejects_invalid_password(client):
    client.post("/api/auth/register", json={
        "username": "invalidpw", "email": "invalidpw@example.com",
        "password": "StrongPassword!123", "business_name": "Test Business", "industry": "retail",
    })
    response = client.post("/api/auth/login", json={"identifier": "invalidpw", "password": "wrong-password"})
    assert response.status_code == 401


def test_connector_registration_still_creates_machine_token(client, db_session, seeder):
    business = seeder.business("Acme Electricals", "distribution")
    response = client.post(f"/api/connectors/register/{business.id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["business_id"] == str(business.id)
    assert data["token"]

    heartbeat = client.post("/api/connectors/heartbeat", headers={"Authorization": f"Bearer {data['token']}"})
    assert heartbeat.status_code == 200
    assert heartbeat.json()["business_id"] == str(business.id)

    user_token = _user_token(client, db_session, business.id)
    kpis = client.get(f"/api/kpis/sales/{business.id}", headers={"Authorization": f"Bearer {user_token}"})
    assert kpis.status_code == 200


def test_connector_token_cannot_be_used_as_human_dashboard_auth(client, seeder):
    business = seeder.business()
    connector_token = _connector_token(client, business.id)
    response = client.get(f"/api/kpis/sales/{business.id}", headers={"Authorization": f"Bearer {connector_token}"})
    assert response.status_code == 401


def test_protected_route_rejects_missing_credential(client, seeder):
    business = seeder.business()
    assert client.get(f"/api/kpis/sales/{business.id}").status_code == 401


def test_protected_route_rejects_garbage_token(client, seeder):
    business = seeder.business()
    response = client.get(f"/api/kpis/sales/{business.id}", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_user_can_access_its_business(client, db_session, seeder):
    business = seeder.business()
    token = _user_token(client, db_session, business.id)
    response = client.get(f"/api/kpis/sales/{business.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_user_cannot_access_another_business(client, db_session, seeder):
    business_a = seeder.business("Business A")
    business_b = seeder.business("Business B")
    token_for_a = _user_token(client, db_session, business_a.id)
    response = client.get(f"/api/kpis/sales/{business_b.id}", headers={"Authorization": f"Bearer {token_for_a}"})
    assert response.status_code == 403


def test_nonexistent_business_without_token_still_requires_auth(client):
    assert client.get(f"/api/kpis/sales/{uuid4()}").status_code == 401


@pytest.mark.parametrize("path", [
    "signals/{business_id}",
    "payables/{business_id}/summary",
    "discounts/{business_id}/anomalies",
    "expenses/{business_id}/summary",
    "inventory/{business_id}/stock-risk",
    "inventory/{business_id}/demand-spikes",
    "inventory/{business_id}/dead-stock",
    "supplier-risk/{business_id}/concentration",
])
def test_dashboard_routes_require_user_auth(client, db_session, seeder, path):
    business = seeder.business()
    route = path.format(business_id=business.id)
    assert client.get(f"/api/{route}").status_code == 401
    token = _user_token(client, db_session, business.id)
    response = client.get(f"/api/{route}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_agent_route_requires_user_auth(client, db_session, seeder):
    business = seeder.business()
    assert client.post(f"/api/agent/{business.id}/ask", json={"question": "How is my business doing?"}).status_code == 401
    token = _user_token(client, db_session, business.id)
    response = client.post(
        f"/api/agent/{business.id}/ask",
        json={"question": "How is my business doing?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_import_route_requires_user_auth(client, seeder):
    business = seeder.business()
    csv_bytes = b"Date,Ledger,Amount\n01-01-2026,Rent,1000\n"
    response = client.post(
        f"/api/ingestion/import-expenses/{business.id}",
        files={"file": ("expenses.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 401


def test_sales_import_persists_new_and_reimported_invoices(client, seeder):
    """Regression test for the dashboard symptom where an accepted import did not change KPIs."""
    business = seeder.business("Import Regression Business")
    register = client.post("/api/auth/register", json={
        "username": f"import_{uuid4().hex[:10]}",
        "email": f"import_{uuid4().hex[:10]}@example.com",
        "password": "StrongPassword!123",
        "business_name": "Import Regression Business",
        "industry": "distribution",
    })
    assert register.status_code == 200, register.text
    token = register.json()["access_token"]
    business_id = register.json()["user"]["business"]["id"]

    first = b"invoice no,date,party name,stock item,qty,rate,amount\nREG001,2026-09-01,Alpha,Network Cable,1,1000,1000\n"
    second = b"invoice_number,transaction_date,customer_name,item_name,quantity,unit_price,total_amount\nREG002,2026-09-02,Beta,USB Connector,1,2500,2500\n"

    headers = {"Authorization": f"Bearer {token}"}
    r1 = client.post(f"/api/ingestion/record-run/{business_id}", headers=headers, files={"files": ("test.csv", first, "text/csv")})
    assert r1.status_code == 200, r1.text
    assert r1.json()["sales_created"] == 1
    assert r1.json()["total_revenue_after_import"] == "1000.00"
    assert r1.json()["total_invoice_count_after_import"] == 1

    r2 = client.post(f"/api/ingestion/record-run/{business_id}", headers=headers, files={"files": ("test.csv", second, "text/csv")})
    assert r2.status_code == 200, r2.text
    assert r2.json()["sales_created"] == 1
    assert r2.json()["total_revenue_after_import"] == "3500.00"
    assert r2.json()["total_invoice_count_after_import"] == 2

    kpis = client.get(f"/api/kpis/sales/{business_id}", headers=headers)
    assert kpis.status_code == 200, kpis.text
    payload = {item["name"]: item for item in kpis.json()}
    assert payload["total_revenue"]["value"] == "3500.00"
    assert payload["total_invoice_count"]["value"] == "2"
