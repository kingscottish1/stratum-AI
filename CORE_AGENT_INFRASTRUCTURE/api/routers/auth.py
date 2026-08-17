"""
Auth: register (first user = owner), login, me. JWT in Authorization header.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from CORE_AGENT_INFRASTRUCTURE.api.deps import get_current_user, get_db
from CORE_AGENT_INFRASTRUCTURE.config import get_config
from CORE_AGENT_INFRASTRUCTURE.db.models import User
from CORE_AGENT_INFRASTRUCTURE.security.audit import record
from CORE_AGENT_INFRASTRUCTURE.security.hashing import hash_password, verify_password
from CORE_AGENT_INFRASTRUCTURE.security.jwt import create_token

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    is_first = db.query(User).count() == 0
    role = "owner" if is_first else "viewer"
    if not is_first and not get_config().is_demo():
        raise HTTPException(
            status_code=403,
            detail="Registration is closed — an owner must invite team members.",
        )
    user = User(name=body.name, email=body.email.lower(),
                password_hash=hash_password(body.password), role=role)
    db.add(user)
    db.flush()
    record(db, "auth.register", "user", body.email.lower(), user_id=user.id, user_email=user.email)
    token = create_token(user.id, user.email, user.role)
    return {"token": token, "user": {"id": user.id, "name": user.name,
                                      "email": user.email, "role": user.role}}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if user is None or not verify_password(body.password, user.password_hash):
        record(db, "auth.login_failed", "user", body.email.lower())
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    record(db, "auth.login", "user", body.email.lower(), user_id=user.id, user_email=user.email)
    token = create_token(user.id, user.email, user.role)
    return {"token": token, "user": {"id": user.id, "name": user.name,
                                      "email": user.email, "role": user.role}}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return {"user": user}
