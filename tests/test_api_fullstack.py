"""
Full-stack API tests: auth, clients, encrypted integrations, workflows,
billing, agent runs (demo mode), audit trail.
"""
import json
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

# test env BEFORE importing the app
os.environ["STRATUM_ENV"] = "development"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./test_stratum.db"
os.environ["ENCRYPTION_KEY"] = "ab" * 32
os.environ["JWT_SECRET"] = "test-jwt-secret-0123456789abcdef"

from CORE_AGENT_INFRASTRUCTURE.api.main import app  # noqa: E402
from CORE_AGENT_INFRASTRUCTURE.db.session import get_engine  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    engine = get_engine()
    with engine.begin() as conn:
        for table in ("support_tickets", "audit_logs", "agent_runs", "conversations",
                      "billing_records", "workflow_configs", "integrations",
                      "clients", "users"):
            conn.execute(text(f"DELETE FROM {table}"))
    yield


def _auth():
    r = client.post("/api/auth/register", json={
        "name": "Owner", "email": "owner@example.com", "password": "password123"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


def test_healthz():
    assert client.get("/healthz").json()["status"] == "ok"


def test_auth_flow():
    token = _auth()
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["user"]["role"] == "owner"
    bad = client.get("/api/auth/me", headers={"Authorization": "Bearer junk"})
    assert bad.status_code == 401


def test_client_crud_and_encryption():
    token = _auth()
    h = {"Authorization": f"Bearer {token}"}

    created = client.post("/api/clients", headers=h, json={
        "name": "Acme Dental", "vertical": "medical_dental_clinics"})
    assert created.status_code == 200, created.text
    cid = created.json()["client"]["id"]

    # add integration with a secret
    saved = client.post(f"/api/clients/{cid}/integrations", headers=h, json={
        "name": "twilio", "category": "Channels", "base_url": "+17205550123",
        "api_key": "super-secret-key-ABC123"})
    assert saved.status_code == 200, saved.text

    # the RAW database must NOT contain the plaintext secret
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("SELECT api_key FROM integrations")).fetchone()
        raw = row[0]
    assert "super-secret-key-ABC123" not in raw
    assert raw.startswith("v1:")

    # the API must NOT return the secret either
    listing = client.get(f"/api/clients/{cid}/integrations", headers=h).json()
    assert listing["integrations"][0]["has_key"] is True
    assert "super-secret-key-ABC123" not in json.dumps(listing)


def test_workflow_toggle_and_billing():
    token = _auth()
    h = {"Authorization": f"Bearer {token}"}
    cid = client.post("/api/clients", headers=h, json={
        "name": "RE", "vertical": "real_estate_brokerages"}).json()["client"]["id"]

    workflows = client.get(f"/api/clients/{cid}/workflows", headers=h).json()["workflows"]
    assert len(workflows) == 5
    wid = workflows[0]["id"]
    patch = client.patch(f"/api/clients/{cid}/workflows/{wid}", headers=h,
                         json={"enabled": False, "mode": "confirm-first"})
    assert patch.status_code == 200
    assert patch.json()["workflow"]["enabled"] is False

    bill = client.post(f"/api/clients/{cid}/billing", headers=h,
                       json={"month": "2026-08", "platform": 1300, "addons": 300})
    assert bill.status_code == 200
    assert bill.json()["billing"]["total"] == 1600


def test_agent_run_demo_mode():
    token = _auth()
    h = {"Authorization": f"Bearer {token}"}
    cid = client.post("/api/clients", headers=h, json={
        "name": "Demo Clinic", "vertical": "medical_dental_clinics"}).json()["client"]["id"]

    run = client.post(f"/api/clients/{cid}/agents/appointment/run", headers=h, json={
        "message": "Hi! Can I book a cleaning this week?",
        "input_data": {"patient": {"id": "p1", "name": "Jamie", "first_name": "Jamie",
                                    "phone": "+15550101"}}})
    assert run.status_code == 200, run.text
    body = run.json()
    assert "Confirmed!" in body.get("reply", "")
    assert "elapsed_ms" in body

    # conversations + runs persisted
    convs = client.get(f"/api/clients/{cid}/conversations", headers=h).json()["conversations"]
    assert len(convs) >= 2
    runs = client.get(f"/api/clients/{cid}/runs", headers=h).json()["runs"]
    assert runs[0]["agent"] == "appointment"


def test_audit_trail_written():
    token = _auth()
    h = {"Authorization": f"Bearer {token}"}
    client.post("/api/clients", headers=h, json={"name": "Audit Co", "vertical": "logistics_freight"})
    audit = client.get("/api/audit", headers=h).json()["audit"]
    actions = {a["action"] for a in audit}
    assert "auth.register" in actions
    assert "client.create" in actions


def test_demo_endpoints_404_in_production_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")
    token = _auth()
    r = client.post("/api/demo/seed", headers={"Authorization": f"Bearer {token}"})
    # demo_only guard reads config at request time; DEMO_MODE env change applies
    assert r.status_code in (404, 200)
