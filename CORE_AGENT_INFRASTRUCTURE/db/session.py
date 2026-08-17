"""
SQLAlchemy engine/session — database URL comes ONLY from config/env.
Production default: PostgreSQL. Demo/dev default: SQLite file.
"""
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from CORE_AGENT_INFRASTRUCTURE.config import get_config

logger = logging.getLogger("stratum.db")

_engine = None
_session_factory: Optional[sessionmaker] = None


def get_engine():
    global _engine, _session_factory
    if _engine is not None:
        return _engine
    cfg = get_config()
    connect_args = {}
    if cfg.database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    _engine = create_engine(
        cfg.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        connect_args=connect_args,
    )
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False, autoflush=False)
    return _engine


def init_db() -> None:
    """Create all tables (idempotent). Use migrations for prod schema changes."""
    from CORE_AGENT_INFRASTRUCTURE.db import models  # noqa: F401  (register models)
    from CORE_AGENT_INFRASTRUCTURE.db.base import Base

    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("database ready: %s", get_config().database_url.split(":", 1)[0] + "://")


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context-managed session with commit/rollback handling."""
    get_engine()
    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def healthcheck() -> dict:
    try:
        get_engine().connect()
        return {"ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
