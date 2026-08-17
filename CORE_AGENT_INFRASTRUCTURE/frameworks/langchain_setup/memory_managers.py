"""
Memory managers for agent conversations.

Supports in-memory buffer (development) and Redis-backed memory
(production, shared across workers).
"""
import json
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage

try:
    import redis
except ImportError:  # pragma: no cover
    redis = None

from .config import settings


class BaseMemory(ABC):
    """Conversation memory interface."""

    @abstractmethod
    def add_message(self, session_id: str, role: str, content: str) -> None: ...

    @abstractmethod
    def get_messages(self, session_id: str, limit: int = 20) -> list[dict]: ...

    @abstractmethod
    def clear(self, session_id: str) -> None: ...


class BufferMemory(BaseMemory):
    """Simple in-process memory, fine for development and tests."""

    def __init__(self, ttl_seconds: int = 24 * 3600):
        self._store: dict[str, list[dict]] = {}
        self.ttl = ttl_seconds

    def add_message(self, session_id: str, role: str, content: str) -> None:
        self._store.setdefault(session_id, []).append(
            {"role": role, "content": content, "ts": time.time()}
        )

    def get_messages(self, session_id: str, limit: int = 20) -> list[dict]:
        msgs = self._store.get(session_id, [])
        return msgs[-limit:]

    def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)


class RedisMemory(BaseMemory):
    """Redis-backed memory shared across workers (production)."""

    KEY_PREFIX = "agent:memory:"

    def __init__(self, url: Optional[str] = None, ttl_seconds: int = 7 * 24 * 3600):
        if redis is None:
            raise RuntimeError("redis package not installed")
        self.client = redis.Redis.from_url(url or settings.redis_url)
        self.ttl = ttl_seconds

    def add_message(self, session_id: str, role: str, content: str) -> None:
        key = self.KEY_PREFIX + session_id
        self.client.rpush(key, json.dumps({"role": role, "content": content}))
        self.client.expire(key, self.ttl)

    def get_messages(self, session_id: str, limit: int = 20) -> list[dict]:
        raw = self.client.lrange(self.KEY_PREFIX + session_id, -limit, -1)
        return [json.loads(m) for m in raw]

    def clear(self, session_id: str) -> None:
        self.client.delete(self.KEY_PREFIX + session_id)


def to_langchain(messages: list[dict]):
    """Convert stored messages into LangChain message objects."""
    out = []
    for m in messages:
        if m["role"] == "system":
            out.append(SystemMessage(content=m["content"]))
        else:
            out.append(HumanMessage(content=m["content"]))
    return out


def new_session_id() -> str:
    return uuid.uuid4().hex


def get_memory() -> BaseMemory:
    """Factory: picks Redis in production, buffer otherwise."""
    if settings.environment == "production":
        return RedisMemory()
    return BufferMemory()
