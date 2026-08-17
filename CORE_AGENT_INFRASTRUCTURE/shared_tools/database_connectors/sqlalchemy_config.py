"""
SQLAlchemy engine/session factory — ORM layer for the agency's own data
(conversations, metrics, billing) and for read-only access to client DBs.
"""
import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for agency ORM models."""


class SQLAlchemyConfig:
    def __init__(self, url: Optional[str] = None):
        self.url = url or os.getenv(
            "DATABASE_URL", "postgresql+psycopg2://agent:agent@localhost:5432/stratum"
        )
        connect_args = {}
        if self.url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}
        self.engine = create_engine(
            self.url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args=connect_args,
        )
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def init_db(self) -> None:
        Base.metadata.create_all(self.engine)


default_config = SQLAlchemyConfig()
