"""
System status — non-sensitive runtime info for the frontend.
"""
from fastapi import APIRouter, Depends

from CORE_AGENT_INFRASTRUCTURE.api.deps import get_current_user
from CORE_AGENT_INFRASTRUCTURE.config import get_config
from CORE_AGENT_INFRASTRUCTURE.db.session import healthcheck
from CORE_AGENT_INFRASTRUCTURE.llm.factory import build_llm

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status")
def status(user: dict = Depends(get_current_user)):
    cfg = get_config()
    llm = None
    llm_error = None
    try:
        llm = build_llm(cfg)
        llm_info = {"provider": llm.provider.name, "fast": llm.fast(), "quality": llm.quality()}
    except Exception as exc:  # noqa: BLE001
        llm_error = str(exc)
        llm_info = None
    return {
        "status": "ok",
        "system": cfg.describe(),
        "llm": llm_info,
        "llm_error": llm_error,
        "db": healthcheck(),
        "built_by": "kingscottishDEV · N.A.S",
    }
