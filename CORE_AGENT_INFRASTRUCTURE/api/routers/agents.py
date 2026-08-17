"""
Agent execution API — runs a real vertical agent for a client instance.

Demo mode: mock connectors (owner testing only).
Production: real connectors wired from encrypted integration records;
           refuses to run if credentials are missing.
"""
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from CORE_AGENT_INFRASTRUCTURE.api.agent_runtime import AgentRuntimeError, build_suite
from CORE_AGENT_INFRASTRUCTURE.api.deps import get_current_user, get_db
from CORE_AGENT_INFRASTRUCTURE.db.models import AgentRun, Client, Conversation, Integration

router = APIRouter(prefix="/clients/{client_id}/agents", tags=["agents"])

AGENT_NAMES = {
    "medical_dental_clinics": ["appointment", "insurance_intake", "follow_up",
                               "patient_communication", "clinic_orchestrator"],
    "real_estate_brokerages": ["lead_qualifier", "property_matcher", "viewing_scheduler",
                               "follow_up", "crm_sync", "brokerage_orchestrator"],
    "logistics_freight": ["document_parser", "invoice_matcher", "exception_detector",
                          "exception_resolver", "reporting", "logistics_orchestrator"],
}


class RunIn(BaseModel):
    message: str = ""
    input_data: dict = {}


@router.get("")
def list_agents(client_id: int, db: Session = Depends(get_db),
                user: dict = Depends(get_current_user)):
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"agents": AGENT_NAMES.get(client.vertical, [])}


@router.post("/{agent_name}/run")
def run_agent(client_id: int, agent_name: str, body: RunIn,
              db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    if not client.enabled:
        raise HTTPException(status_code=409, detail="Client instance is disabled")

    integrations = db.query(Integration).filter(Integration.client_id == client_id).all()
    integration_data = [{
        "name": i.name, "category": i.category, "base_url": i.base_url,
        "api_key": i.api_key,  # decrypted by the EncryptedText column type
        "extra_json": i.extra_json or {},
    } for i in integrations]

    started = time.monotonic()
    try:
        orchestrator, env = build_suite(client.vertical, integration_data, client.config_json or {})
        agent = getattr(orchestrator.agents, "get", lambda name, default=None: None)(agent_name) or orchestrator
        payload = {"message": body.message, **body.input_data,
                   "lead": body.input_data.get("lead", {}),
                   "patient": body.input_data.get("patient", {})}
        result = agent.execute(payload)
    except AgentRuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Agent failed: {exc}") from exc

    elapsed_ms = int((time.monotonic() - started) * 1000)
    llm_model = getattr(getattr(orchestrator, "llm", None), "last_model", "")
    llm_cost = getattr(getattr(orchestrator, "llm", None), "last_cost_estimate", 0.0)

    db.add(AgentRun(client_id=client_id, vertical=client.vertical, agent=agent_name,
                    status=result.get("status", "success"), error_type=result.get("error", ""),
                    elapsed_ms=elapsed_ms, llm_model=llm_model, llm_cost_usd=llm_cost,
                    meta_json={"reply": str(result.get("reply", ""))[:300]}))
    if body.message:
        db.add(Conversation(client_id=client_id, channel="api", direction="inbound",
                            role="user", content=body.message[:2000], agent=agent_name))
        db.add(Conversation(client_id=client_id, channel="api", direction="outbound",
                            role="assistant", content=str(result.get("reply", ""))[:2000],
                            agent=agent_name))

    result["elapsed_ms"] = elapsed_ms
    result["llm_model"] = llm_model
    result["llm_cost_usd"] = llm_cost
    return result
