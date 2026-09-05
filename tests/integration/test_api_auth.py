"""HTTP-level auth tests.

There are no HTTP-level tests anywhere else in this repo -- everything else
tests the underlying functions directly, never through a real FastAPI
request/response cycle. That's fine for business logic, but auth is
specifically about what happens at the HTTP boundary (headers, status
codes, dependency wiring), so this is the one place that boundary itself
needs a real TestClient rather than a direct function call.

apps.api.app.main imports connect to a real Postgres at module import time
(ensure_schema_compatibility()), which isn't available in this sandbox, so
these tests build a small standalone app mounting the same routers directly
rather than importing apps.api.app.main.
"""
from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.api.routes.agent import router as agent_router
from apps.api.app.api.routes.connectors import router as connectors_router
from apps.api.app.api.routes.kpis import router as kpis_router
from apps.api.app.api.routes.signals import router as signals_router
from packages.shared.database.session import get_db


@pytest.fixture()
def client(db_session):
    app = FastAPI()
    app.include_router(connectors_router, prefix="/api")
    app.include_router(kpis_router, prefix="/api")
    app.include_router(signals_router, prefix="/api")
    app.include_router(agent_router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _register(client, business_id) -> str:
    response = client.post(f"/api/connectors/register/{business_id}")
    assert response.status_code == 200, response.text
    return response.json()["token"]


def test_protected_route_rejects_missing_credential(client, seeder):
    business = seeder.business()
    response = client.get(f"/api/kpis/sales/{business.id}")
    assert response.status_code == 401


def test_protected_route_rejects_garbage_token(client, seeder):
    business = seeder.business()
    response = client.get(
        f"/api/kpis/sales/{business.id}",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


def test_protected_route_accepts_valid_token_for_its_own_business(client, seeder):
    business = seeder.business()
    token = _register(client, business.id)

    response = client.get(
        f"/api/kpis/sales/{business.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_token_for_one_business_cannot_access_another_business(client, seeder):
    business_a = seeder.business("Business A")
    business_b = seeder.business("Business B")
    token_for_a = _register(client, business_a.id)

    response = client.get(
        f"/api/kpis/sales/{business_b.id}",
        headers={"Authorization": f"Bearer {token_for_a}"},
    )
    assert response.status_code == 403


def test_signals_route_is_also_protected(client, seeder):
    business = seeder.business()
    assert client.get(f"/api/signals/{business.id}").status_code == 401
    token = _register(client, business.id)
    response = client.get(f"/api/signals/{business.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_agent_ask_route_is_also_protected(client, seeder):
    business = seeder.business()
    response = client.post(f"/api/agent/{business.id}/ask", json={"question": "How is my business doing?"})
    assert response.status_code == 401

    token = _register(client, business.id)
    response = client.post(
        f"/api/agent/{business.id}/ask",
        json={"question": "How is my business doing?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_nonexistent_business_id_with_no_token_still_requires_auth(client):
    """A well-behaved API shouldn't distinguish 'business doesn't exist'
    from 'you're not authorized' before checking auth -- both should be a
    401 with no credential, not a 404 that leaks whether the ID is real."""
    response = client.get(f"/api/kpis/sales/{uuid4()}")
    assert response.status_code == 401
