from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlalchemy import select, text

from apps.api.app.api.routes.auth import router as auth_router
from apps.api.app.api.routes.payments import router as payments_router
from apps.api.app.api.routes.receivables import router as receivables_router
from apps.api.app.api.routes.payables import router as payables_router
from packages.shared.database.models import PaymentModel
from packages.shared.database.session import get_db


def _client(db_session):
    app = FastAPI()
    for router in (auth_router, payments_router, receivables_router, payables_router):
        app.include_router(router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _token(client, db_session, business_id):
    username = f"payment_{uuid4().hex[:10]}"
    password = "StrongPassword!123"
    user_id = uuid4()
    db_session.execute(
        text("INSERT INTO users (id, username, email, password_hash) VALUES (:id,:username,:email,:hash)"),
        {"id": str(user_id), "username": username, "email": f"{username}@example.com", "hash": PasswordHash.recommended().hash(password)},
    )
    db_session.execute(
        text("INSERT INTO user_businesses (user_id, business_id, role) VALUES (:user_id,:business_id,'owner')"),
        {"user_id": str(user_id), "business_id": str(business_id)},
    )
    db_session.commit()
    response = client.post("/api/auth/login", json={"identifier": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_customer_payment_reduces_receivable_and_creates_payment(db_session, seeder):
    business = seeder.business("Payment Business")
    customer = seeder.customer(business.id, "Gamma Industries")
    sale = seeder.sale(business.id, customer_id=customer.id, total_amount=5000, paid_amount=0, invoice_number="SPS0601")
    client = _client(db_session)
    token = _token(client, db_session, business.id)
    headers = {"Authorization": f"Bearer {token}"}

    before = client.get(f"/api/receivables/{business.id}/summary", headers=headers)
    assert before.status_code == 200, before.text
    assert before.json()["outstanding"] == 5000.0

    response = client.post(
        f"/api/payments/{business.id}/customer",
        headers=headers,
        json={"customer_name":"Gamma Industries","amount":2000,"payment_date":"2026-09-20","reference":"SPS0601-P1","invoice_number":"SPS0601"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["invoice_number"] == "SPS0601"
    assert payload["payment_amount"] == 2000.0
    assert payload["remaining_receivable"] == 3000.0
    db_session.refresh(sale)
    assert float(sale.paid_amount) == 2000.0
    payment = db_session.scalar(select(PaymentModel).where(PaymentModel.sale_id == sale.id))
    assert payment is not None
    assert float(payment.amount) == 2000.0
    assert payment.direction == "in"
    after = client.get(f"/api/receivables/{business.id}/summary", headers=headers)
    assert after.status_code == 200, after.text
    assert after.json()["outstanding"] == 3000.0


def test_customer_payment_rejects_overpayment(db_session, seeder):
    business = seeder.business("Payment Validation Business")
    customer = seeder.customer(business.id, "Gamma Industries")
    seeder.sale(business.id, customer_id=customer.id, total_amount=5000, paid_amount=0, invoice_number="SPS0602")
    client = _client(db_session)
    token = _token(client, db_session, business.id)
    response = client.post(f"/api/payments/{business.id}/customer", headers={"Authorization": f"Bearer {token}"}, json={"customer_name":"Gamma Industries","amount":5001,"payment_date":"2026-09-20","invoice_number":"SPS0602"})
    assert response.status_code == 400
    assert "exceeds invoice outstanding" in response.json()["detail"]


def test_customer_payment_requires_auth(db_session, seeder):
    business = seeder.business("Protected Payment Business")
    client = _client(db_session)
    response = client.post(f"/api/payments/{business.id}/customer", json={"amount":100,"payment_date":"2026-09-20","invoice_number":"MISSING"})
    assert response.status_code == 401


def test_supplier_payment_reduces_payable_and_creates_payment(db_session, seeder):
    business = seeder.business("Supplier Payment Business")
    supplier = seeder.supplier(business.id, "Gamma Components")
    purchase = seeder.purchase(business.id, supplier_id=supplier.id, total_amount=10000, paid_amount=0, invoice_number="SPP0601")
    client = _client(db_session)
    token = _token(client, db_session, business.id)
    headers = {"Authorization": f"Bearer {token}"}

    before = client.get(f"/api/payables/{business.id}/summary", headers=headers)
    assert before.status_code == 200, before.text
    assert before.json()["outstanding"] == 10000.0

    response = client.post(
        f"/api/payments/{business.id}/supplier",
        headers=headers,
        json={"supplier_name":"Gamma Components","amount":4000,"payment_date":"2026-09-20","reference":"SPP0601-P1","invoice_number":"SPP0601"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["invoice_number"] == "SPP0601"
    assert payload["payment_amount"] == 4000.0
    assert payload["remaining_payable"] == 6000.0
    assert payload["direction"] == "out"
    db_session.refresh(purchase)
    assert float(purchase.paid_amount) == 4000.0
    payment = db_session.scalar(select(PaymentModel).where(PaymentModel.purchase_id == purchase.id))
    assert payment is not None
    assert float(payment.amount) == 4000.0
    assert payment.direction == "out"
    after = client.get(f"/api/payables/{business.id}/summary", headers=headers)
    assert after.status_code == 200, after.text
    assert after.json()["outstanding"] == 6000.0


def test_supplier_payment_rejects_overpayment(db_session, seeder):
    business = seeder.business("Supplier Payment Validation Business")
    supplier = seeder.supplier(business.id, "Gamma Components")
    seeder.purchase(business.id, supplier_id=supplier.id, total_amount=5000, paid_amount=0, invoice_number="SPP0602")
    client = _client(db_session)
    token = _token(client, db_session, business.id)
    response = client.post(f"/api/payments/{business.id}/supplier", headers={"Authorization": f"Bearer {token}"}, json={"supplier_name":"Gamma Components","amount":5001,"payment_date":"2026-09-20","invoice_number":"SPP0602"})
    assert response.status_code == 400
    assert "exceeds invoice outstanding" in response.json()["detail"]
