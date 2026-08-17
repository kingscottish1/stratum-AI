"""
Shared FastAPI dependencies: DB session, current user, role checks,
demo-mode guard.
"""
from typing import Generator, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from CORE_AGENT_INFRASTRUCTURE.config import get_config
from CORE_AGENT_INFRASTRUCTURE.db.session import db_session
from CORE_AGENT_INFRASTRUCTURE.security.jwt import JWTError, decode_token

bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    with db_session() as session:
        yield session


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    from CORE_AGENT_INFRASTRUCTURE.db.models import User

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or removed")
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role}


def require_role(*roles: str):
    """Dependency factory: require one of the given roles."""

    def checker(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Role '{user['role']}' not allowed; requires one of {roles}")
        return user

    return checker


def demo_only():
    """Guard: endpoints that exist ONLY for demo/testing. 404 in production."""

    def checker() -> None:
        if not get_config().is_demo():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Demo endpoints are disabled outside DEMO_MODE")
    return checker
