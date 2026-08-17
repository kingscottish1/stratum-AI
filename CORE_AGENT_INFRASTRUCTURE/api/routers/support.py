"""
Support tickets.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from CORE_AGENT_INFRASTRUCTURE.api.deps import get_current_user, get_db, require_role
from CORE_AGENT_INFRASTRUCTURE.db.models import Client, SupportTicket
from CORE_AGENT_INFRASTRUCTURE.security.audit import record

router = APIRouter(prefix="/support", tags=["support"])


class TicketIn(BaseModel):
    client_id: int
    subject: str
    priority: str = "P3"
    description: str = ""


@router.get("")
def list_tickets(limit: int = 100, db: Session = Depends(get_db),
                 user: dict = Depends(get_current_user)):
    rows = db.query(SupportTicket).order_by(SupportTicket.created_at.desc()).limit(min(limit, 500)).all()
    return {"tickets": [{"id": t.id, "client_id": t.client_id, "subject": t.subject,
                         "priority": t.priority, "status": t.status,
                         "created_at": str(t.created_at)} for t in rows]}


@router.post("")
def create_ticket(body: TicketIn, db: Session = Depends(get_db),
                  user: dict = Depends(get_current_user)):
    client = db.get(Client, body.client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    ticket = SupportTicket(client_id=body.client_id, subject=body.subject,
                           priority=body.priority, description=body.description)
    db.add(ticket)
    db.flush()
    record(db, "support.create", f"ticket:{ticket.id}", body.subject, user_id=user["id"],
           user_email=user["email"], client_id=body.client_id)
    return {"ticket": {"id": ticket.id, "subject": ticket.subject, "priority": ticket.priority}}
