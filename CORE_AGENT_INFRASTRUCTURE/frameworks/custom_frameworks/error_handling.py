"""
Error taxonomy, retry logic and graceful degradation for all agents.

Guiding principles:
  1. Never crash the message pipeline on a recoverable error.
  2. Retry transient failures (rate limits, 5xx) with exponential backoff.
  3. Always leave a human-usable fallback path (handoff ticket).
"""
import functools
import logging
import random
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger("stratum.errors")

T = TypeVar("T")


# --- Exception taxonomy ------------------------------------------------------
class AgencyError(Exception):
    """Base class for all agency runtime errors."""


class ToolError(AgencyError):
    """An external tool/integration failed."""


class LLMError(AgencyError):
    """An LLM call failed or returned unusable output."""


class RateLimitError(AgencyError):
    """External API rate limit hit; retry with backoff."""


class ValidationError(AgencyError):
    """Input data failed schema validation."""


class ConfigurationError(AgencyError):
    """Missing or invalid configuration / secret."""


class HandoffRequired(AgencyError):
    """Raised when the agent must escalate to a human (explicit handoff)."""


# --- Retry decorator ----------------------------------------------------------
def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_on: tuple[type[Exception], ...] = (RateLimitError, ToolError, TimeoutError),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Retry a function with exponential backoff + jitter."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            attempt = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except retry_on as exc:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    delay *= 0.5 + random.random()  # jitter
                    logger.warning(
                        "retrying %s (attempt %s/%s) after %.1fs: %s",
                        func.__name__, attempt, max_attempts, delay, exc,
                    )
                    time.sleep(delay)

        return wrapper

    return decorator


# --- Safe-call helper -----------------------------------------------------------
def safe_call(func: Callable[..., T], fallback: Any = None, **kwargs: Any) -> T | Any:
    """Call a function; return `fallback` instead of raising."""
    try:
        return func(**kwargs)
    except Exception as exc:  # noqa: BLE001
        logger.warning("safe_call(%s) failed, returning fallback: %s", func.__name__, exc)
        return fallback


def error_payload(exc: Exception, agent_name: str) -> dict[str, Any]:
    """Standard error dict used in agent outputs."""
    return {
        "status": "error",
        "agent": agent_name,
        "error_type": exc.__class__.__name__,
        "error": str(exc),
        "action": "retry" if isinstance(exc, (RateLimitError, ToolError)) else "handoff",
    }
