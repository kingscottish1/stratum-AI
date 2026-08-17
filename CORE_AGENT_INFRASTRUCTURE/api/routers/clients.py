"""
Client instances CRUD + per-client data (integrations, workflows, billing,
conversations, audit).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from CORE_AGENT_INFRASTRUCTURE.api.deps import get_current_user, get_db, require_role
from CORE_AGENT_INFRASTRUCTURE.db.models import (AgentRun, AuditLog, BillingRecord,
                                                 Client, Conversation, Integration,
                                                 WorkflowConfig)
from CORE_AGENT_INFRASTRUCTURE.security.audit import record

router = APIRouter(prefix="/clients", tags=["clients"])

VERTICALS = ["medical_dental_clinics", "real_estate_brokerages", "logistics_freight"]


class ClientIn(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    vertical: str
    status: str = "onboarding"
    config_json: dict = {}


class IntegrationIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = "api"
    base_url: str = ""
    api_key: str = ""
    extra_json: dict = {}


class WorkflowPatch(BaseModel):
    enabled: bool | None = None
    mode: str | None = None


class BillingIn(BaseModel):
    month: str
    platform: float = 0
    addons: float = 0
    status: str = "pending"


def _get_client(db: Session, client_id: int, user: dict) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


# --- CRUD ---------------------------------------------------------------------
@router.get("")
def list_clients(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    clients = db.query(Client).order_by(Client.id).all()
    return {"clients": [_client_out(c) for c in clients]}


@router.post("")
def create_client(body: ClientIn, db: Session = Depends(get_db),
                  user: dict = Depends(require_role("owner", "admin"))):
    if body.vertical not in VERTICALS:
        raise HTTPException(status_code=400, detail=f"vertical must be one of {VERTICALS}")
    client = Client(name=body.name, vertical=body.vertical, status=body.status,
                    config_json=body.config_json)
    db.add(client)
    db.flush()
    _seed_workflows(db, client)
    record(db, "client.create", f"client:{client.id}", body.name, user_id=user["id"],
           user_email=user["email"], client_id=client.id)
    return {"client": _client_out(client)}


@router.get("/{client_id}")
def get_client(client_id: int, db: Session = Depends(get_db),
               user: dict = Depends(get_current_user)):
    client = _get_client(db, client_id, user)
    return {"client": _client_out(client)}


@router.patch("/{client_id}")
def update_client(client_id: int, body: dict, db: Session = Depends(get_db),
                  user: dict = Depends(require_role("owner", "admin"))):
    client = _get_client(db, client_id, user)
    for key in ("name", "status", "enabled"):
        if key in body and key != "enabled":
            setattr(client, key, body[key])
    if "enabled" in body:
        client.enabled = bool(body["enabled"])
    if "config_json" in body:
        client.config_json = body["config_json"]
    record(db, "client.update", f"client:{client.id}", str(body)[:500], user_id=user["id"],
           user_email=user["email"], client_id=client.id)
    return {"client": _client_out(client)}


@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db),
                  user: dict = Depends(require_role("owner"))):
    client = _get_client(db, client_id, user)
    record(db, "client.delete", f"client:{client.id}", client.name, user_id=user["id"],
           user_email=user["email"], client_id=client.id)
    db.delete(client)
    return {"status": "deleted"}


# --- integrations (secrets stored ENCRYPTED at rest) ----------------------------
@router.get("/{client_id}/integrations")
def list_integrations(client_id: int, db: Session = Depends(get_db),
                      user: dict = Depends(get_current_user)):
    _get_client(db, client_id, user)
    rows = db.query(Integration).filter(Integration.client_id == client_id).all()
    return {"integrations": [{
        "id": i.id, "name": i.name, "category": i.category, "base_url": i.base_url,
        "status": i.status, "has_key": bool(i.api_key), "created_at": str(i.created_at),
    } for i in rows]}


@router.post("/{client_id}/integrations")
def create_integration(client_id: int, body: IntegrationIn, db: Session = Depends(get_db),
                       user: dict = Depends(require_role("owner", "admin"))):
    _get_client(db, client_id, user)
    if not body.api_key:
        raise HTTPException(status_code=400, detail="api_key is required (stored encrypted)")
    integration = Integration(client_id=client_id, name=body.name, category=body.category,
                              base_url=body.base_url, api_key=body.api_key,  # encrypted by model
                              extra_json=body.extra_json)
    db.add(integration)
    db.flush()
    record(db, "secret.create", f"integration:{integration.id}", body.name,
           user_id=user["id"], user_email=user["email"], client_id=client_id)
    return {"integration": {"id": integration.id, "name": integration.name,
                            "has_key": True}}


@router.delete("/{client_id}/integrations/{integration_id}")
def delete_integration(client_id: int, integration_id: int, db: Session = Depends(get_db),
                       user: dict = Depends(require_role("owner", "admin"))):
    integration = db.get(Integration, integration_id)
    if integration is None or integration.client_id != client_id:
        raise HTTPException(status_code=404, detail="Integration not found")
    record(db, "secret.delete", f"integration:{integration.id}", integration.name,
           user_id=user["id"], user_email=user["email"], client_id=client_id)
    db.delete(integration)
    return {"status": "deleted"}


# --- workflows ---------------------------------------------------------------------
@router.get("/{client_id}/workflows")
def list_workflows(client_id: int, db: Session = Depends(get_db),
                   user: dict = Depends(get_current_user)):
    _get_client(db, client_id, user)
    rows = db.query(WorkflowConfig).filter(WorkflowConfig.client_id == client_id).all()
    return {"workflows": [{
        "id": w.workflow_id, "name": w.name, "description": w.description,
        "enabled": w.enabled, "mode": w.mode,
    } for w in rows]}


@router.patch("/{client_id}/workflows/{workflow_id}")
def update_workflow(client_id: int, workflow_id: str, body: WorkflowPatch,
                    db: Session = Depends(get_db),
                    user: dict = Depends(require_role("owner", "admin"))):
    _get_client(db, client_id, user)
    row = (db.query(WorkflowConfig)
           .filter(WorkflowConfig.client_id == client_id,
                   WorkflowConfig.workflow_id == workflow_id).first())
    if row is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if body.enabled is not None:
        row.enabled = body.enabled
    if body.mode is not None:
        row.mode = body.mode
    record(db, "workflow.update", f"workflow:{workflow_id}",
           f"enabled={row.enabled} mode={row.mode}", user_id=user["id"],
           user_email=user["email"], client_id=client_id)
    return {"workflow": {"id": row.workflow_id, "enabled": row.enabled, "mode": row.mode}}


# --- billing ---------------------------------------------------------------------------
@router.get("/{client_id}/billing")
def list_billing(client_id: int, db: Session = Depends(get_db),
                 user: dict = Depends(get_current_user)):
    _get_client(db, client_id, user)
    rows = db.query(BillingRecord).filter(BillingRecord.client_id == client_id).order_by(BillingRecord.month).all()
    return {"billing": [{"id": b.id, "month": b.month, "platform": b.platform,
                         "addons": b.addons, "total": b.total, "status": b.status} for b in rows]}


@router.post("/{client_id}/billing")
def create_billing(client_id: int, body: BillingIn, db: Session = Depends(get_db),
                   user: dict = Depends(require_role("owner", "admin"))):
    _get_client(db, client_id, user)
    rec = BillingRecord(client_id=client_id, month=body.month, platform=body.platform,
                        addons=body.addons, total=body.platform + body.addons, status=body.status)
    db.add(rec)
    db.flush()
    record(db, "billing.create", f"billing:{rec.id}", body.month, user_id=user["id"],
           user_email=user["email"], client_id=client_id)
    return {"billing": {"id": rec.id, "month": rec.month, "total": rec.total}}


# --- conversations & audit ---------------------------------------------------------------
@router.get("/{client_id}/conversations")
def list_conversations(client_id: int, limit: int = 50, db: Session = Depends(get_db),
                       user: dict = Depends(get_current_user)):
    _get_client(db, client_id, user)
    rows = (db.query(Conversation).filter(Conversation.client_id == client_id)
            .order_by(Conversation.created_at.desc()).limit(min(limit, 200)).all())
    return {"conversations": [{
        "id": c.id, "channel": c.channel, "direction": c.direction, "role": c.role,
        "content": c.content[:500], "agent": c.agent, "created_at": str(c.created_at),
    } for c in rows]}


@router.get("/{client_id}/audit")
def client_audit(client_id: int, limit: int = 100, db: Session = Depends(get_db),
                 user: dict = Depends(require_role("owner", "admin"))):
    _get_client(db, client_id, user)
    rows = (db.query(AuditLog).filter(AuditLog.client_id == client_id)
            .order_by(AuditLog.created_at.desc()).limit(min(limit, 500)).all())
    return {"audit": [{
        "id": a.id, "user_email": a.user_email, "action": a.action,
        "resource": a.resource, "detail": a.detail, "created_at": str(a.created_at),
    } for a in rows]}


@router.get("/{client_id}/runs")
def client_runs(client_id: int, limit: int = 50, db: Session = Depends(get_db),
                user: dict = Depends(get_current_user)):
    _get_client(db, client_id, user)
    rows = (db.query(AgentRun).filter(AgentRun.client_id == client_id)
            .order_by(AgentRun.created_at.desc()).limit(min(limit, 200)).all())
    return {"runs": [{
        "id": r.id, "agent": r.agent, "status": r.status, "elapsed_ms": r.elapsed_ms,
        "llm_model": r.llm_model, "llm_cost_usd": r.llm_cost_usd, "created_at": str(r.created_at),
    } for r in rows]}


# --- helpers --------------------------------------------------------------------------------
def _client_out(client: Client) -> dict:
    return {
        "id": client.id, "name": client.name, "vertical": client.vertical,
        "status": client.status, "enabled": client.enabled,
        "config_json": client.config_json, "created_at": str(client.created_at),
    }


DEFAULT_WORKFLOWS = {
    "medical_dental_clinics": [
        ("booking", "Appointment booking", "Book, reschedule, cancel over SMS/voice"),
        ("reminders", "Reminder cadence", "48h / 24h / 2h nudge"),
        ("insurance", "Insurance intake", "Collect & verify before visit"),
        ("follow_up", "No-show & recall follow-up", "Rebook missed appointments"),
    ],
    "real_estate_brokerages": [
        ("qualification", "Lead qualification", "Score 0-100 + route instantly"),
        ("hot_alerts", "Hot-lead alerts", "Slack + SMS to agent < 5 min"),
        ("matching", "Property matching", "3-5 MLS matches per lead"),
        ("viewings", "Showing booking", "Book viewings on agent calendars"),
        ("nurture", "Nurture sequences", "viewed_3d, offer_nudge, market snapshot"),
    ],
    "logistics_freight": [
        ("invoice_matching", "Invoice matching", "Match every carrier invoice to contract"),
        ("exception_detection", "Exception detection", "Hourly sweep for scan gaps, late risks"),
        ("dispute_resolution", "Dispute automation", "Evidence-backed dispute packages"),
        ("reporting", "Reporting", "Scorecards, spend, dashboards"),
    ],
}


def _seed_workflows(db: Session, client: Client) -> None:
    for workflow_id, name, description in DEFAULT_WORKFLOWS.get(client.vertical, []):
        db.add(WorkflowConfig(client_id=client.id, workflow_id=workflow_id,
                              name=name, description=description))
