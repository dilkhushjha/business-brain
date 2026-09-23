"""Business onboarding and tenant-isolation tests."""

from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.app.api.routes.auth import router as auth_router
from apps.api.app.api.routes.businesses import router as businesses_router
from packages.shared.database.session import get_db


def _client(db_session) -> TestClient:
    app = FastAPI()
    app.include_router(auth_router, prefix="/api")
    app.include_router(businesses_router, prefix="/api")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _register(client: TestClient, username: str, business_name: str) -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "StrongPassword!123",
            "business_name": business_name,
            "industry": "distribution",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_business_onboarding_lists_and_creates_businesses(db_session):
    client = _client(db_session)
    session = _register(client, f"owner_{uuid4().hex[:8]}", "First Business")
    token = session["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    listed = client.get("/api/businesses", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["businesses"]) == 1
    assert listed.json()["businesses"][0]["name"] == "First Business"

    created = client.post(
        "/api/businesses",
        headers=headers,
        json={"name": "Second Business", "industry": "retail"},
    )
    assert created.status_code == 201, created.text
    second = created.json()
    assert second["name"] == "Second Business"
    assert second["industry"] == "retail"
    assert second["role"] == "owner"

    listed_again = client.get("/api/businesses", headers=headers)
    assert listed_again.status_code == 200
    assert {item["name"] for item in listed_again.json()["businesses"]} == {
        "First Business",
        "Second Business",
    }


def test_business_profile_can_be_updated(db_session):
    client = _client(db_session)
    session = _register(client, f"profile_{uuid4().hex[:8]}", "Old Name")
    token = session["access_token"]
    business_id = session["user"]["business"]["id"]

    response = client.patch(
        f"/api/businesses/{business_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "New Name", "industry": "retail"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "New Name"
    assert response.json()["industry"] == "retail"


def test_business_profile_is_tenant_scoped(db_session):
    client = _client(db_session)
    first = _register(client, f"first_{uuid4().hex[:8]}", "First")
    second = _register(client, f"second_{uuid4().hex[:8]}", "Second")

    response = client.patch(
        f"/api/businesses/{second['user']['business']['id']}",
        headers={"Authorization": f"Bearer {first['access_token']}"},
        json={"name": "Should Not Change"},
    )
    assert response.status_code == 404

    listed = client.get(
        "/api/businesses",
        headers={"Authorization": f"Bearer {first['access_token']}"},
    )
    assert listed.status_code == 200
    assert [item["name"] for item in listed.json()["businesses"]] == ["First"]


def test_business_onboarding_requires_auth(db_session):
    client = _client(db_session)
    assert client.get("/api/businesses").status_code == 401
    assert client.post(
        "/api/businesses",
        json={"name": "No Auth", "industry": "retail"},
    ).status_code == 401
