"""
Global audit log (owner/admin only).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from CORE_AGENT_INFRASTRUCTURE.api.deps import get_db, require_role
from CORE_AGENT_INFRASTRUCTURE.db.models import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def audit_log(limit: int = 200, db: Session = Depends(get_db),
              user: dict = Depends(require_role("owner", "admin"))):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 1000)).all()
    return {"audit": [{
        "id": a.id, "user_email": a.user_email, "client_id": a.client_id,
        "action": a.action, "resource": a.resource, "detail": a.detail,
        "created_at": str(a.created_at),
    } for a in rows]}
