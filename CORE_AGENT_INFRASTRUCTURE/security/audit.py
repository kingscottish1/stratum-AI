"""
Audit helpers — every sensitive action is recorded for compliance.
"""
from typing import Optional

from CORE_AGENT_INFRASTRUCTURE.db.models import AuditLog


def record(db, action: str, resource: str = "", detail: str = "",
           user_id: Optional[int] = None, user_email: str = "",
           client_id: Optional[int] = None) -> None:
    db.add(AuditLog(
        user_id=user_id, user_email=user_email, client_id=client_id,
        action=action, resource=resource, detail=detail[:2000],
    ))
