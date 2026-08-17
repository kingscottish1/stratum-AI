"""
Team users (owner manages roles).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from CORE_AGENT_INFRASTRUCTURE.api.deps import get_db, require_role
from CORE_AGENT_INFRASTRUCTURE.db.models import User
from CORE_AGENT_INFRASTRUCTURE.security.audit import record
from CORE_AGENT_INFRASTRUCTURE.security.hashing import hash_password

router = APIRouter(prefix="/users", tags=["users"])


class UserIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "viewer"


@router.get("")
def list_users(db: Session = Depends(get_db), user: dict = Depends(require_role("owner", "admin"))):
    users = db.query(User).order_by(User.id).all()
    return {"users": [{"id": u.id, "name": u.name, "email": u.email,
                       "role": u.role, "is_active": u.is_active} for u in users]}


@router.post("")
def create_user(body: UserIn, db: Session = Depends(get_db),
                user: dict = Depends(require_role("owner"))):
    if body.role not in ("admin", "viewer"):
        raise HTTPException(status_code=400, detail="role must be admin or viewer")
    existing = db.query(User).filter(User.email == body.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    new_user = User(name=body.name, email=body.email.lower(),
                    password_hash=hash_password(body.password), role=body.role)
    db.add(new_user)
    db.flush()
    record(db, "user.create", f"user:{new_user.id}", body.email.lower(), user_id=user["id"],
           user_email=user["email"])
    return {"user": {"id": new_user.id, "email": new_user.email, "role": new_user.role}}
