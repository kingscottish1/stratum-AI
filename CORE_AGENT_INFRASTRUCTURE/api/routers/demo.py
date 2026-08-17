"""
Demo-only endpoints (404 in production) — seed data for owner testing.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from CORE_AGENT_INFRASTRUCTURE.api.deps import demo_only, get_current_user, get_db
from CORE_AGENT_INFRASTRUCTURE.db.models import BillingRecord, Client, Conversation, Integration
from CORE_AGENT_INFRASTRUCTURE.security.audit import record

router = APIRouter(prefix="/demo", tags=["demo"], dependencies=[Depends(demo_only)])

SAMPLE_CLIENTS = [
    ("Acme Dental", "medical_dental_clinics", "live",
     {"clinic_name": "Acme Dental", "tone": "warm_professional", "timezone": "America/Denver"}),
    ("Remax Denver", "real_estate_brokerages", "live",
     {"brokerage_name": "Remax Denver", "hot_lead_threshold": 70, "timezone": "America/Denver"}),
    ("Summit Freight Co.", "logistics_freight", "onboarding",
     {"tms_provider": "tmw", "accounting_provider": "quickbooks"}),
]

SAMPLE_INTEGRATIONS = [
    ("google_calendar", "Calendar", "https://www.googleapis.com/calendar/v3", "demo-key-calendar-0001"),
    ("twilio", "Channels", "+17205550123", "demo-key-twilio-0002"),
    ("follow_up_boss", "CRM", "https://api.followupboss.com/v1", "demo-key-fub-0003"),
    ("mls", "MLS", "https://api.mlsgrid.com", "demo-key-mls-0004"),
    ("tmw", "TMS", "https://tmw.example.com", "demo-key-tmw-0005"),
    ("quickbooks", "Accounting", "https://quickbooks.api.intuit.com", "demo-key-qb-0006"),
]


@router.post("/seed")
def seed(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """Load demo clients so the owner can test the whole flow."""
    if db.query(Client).count() > 0:
        return {"status": "skipped", "detail": "clients already exist"}

    from CORE_AGENT_INFRASTRUCTURE.api.routers.clients import _seed_workflows

    for name, vertical, status, config in SAMPLE_CLIENTS:
        client = Client(name=name, vertical=vertical, status=status, config_json=config)
        db.add(client)
        db.flush()
        _seed_workflows(db, client)

        # attach demo integrations for the first two clients (secrets ENCRYPTED at rest)
        if vertical == "medical_dental_clinics":
            picks = [SAMPLE_INTEGRATIONS[0], SAMPLE_INTEGRATIONS[1]]
        elif vertical == "real_estate_brokerages":
            picks = [SAMPLE_INTEGRATIONS[2], SAMPLE_INTEGRATIONS[3]]
        else:
            picks = [SAMPLE_INTEGRATIONS[4], SAMPLE_INTEGRATIONS[5]]
        for name_i, category, base_url, key in picks:
            db.add(Integration(client_id=client.id, name=name_i, category=category,
                               base_url=base_url, api_key=key))

        db.add(BillingRecord(client_id=client.id, month="2026-08", platform=1300,
                             addons=300, total=1600, status="pending"))
        db.add(Conversation(client_id=client.id, channel="sms", direction="inbound",
                            role="user", content="Hi! Can I book a cleaning this week?",
                            agent="appointment"))
        db.add(Conversation(client_id=client.id, channel="sms", direction="outbound",
                            role="assistant",
                            content="✅ Confirmed! Cleaning on Mon Aug 3 at 9:00 AM.",
                            agent="appointment"))

    record(db, "demo.seed", "clients", "demo data loaded", user_id=user["id"], user_email=user["email"])
    return {"status": "seeded", "clients": [c[0] for c in SAMPLE_CLIENTS]}
