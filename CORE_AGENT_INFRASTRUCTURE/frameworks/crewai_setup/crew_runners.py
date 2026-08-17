"""
Crew execution helpers: run crews safely with retries, timeouts and logging.
"""
import logging
import time
from typing import Any, Callable

from .crews_orchestration import create_crew

logger = logging.getLogger("stratum.crews")


def run_crew(
    agent_names: list[str],
    task_names: list[str],
    inputs: dict[str, Any],
    crew_name: str = "generic",
    max_retries: int = 2,
) -> Any:
    """Run a crew with retry-on-failure semantics."""
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 2):
        try:
            crew = create_crew(agent_names, task_names, name=crew_name)
            logger.info("Running crew=%s attempt=%s inputs=%s", crew_name, attempt, list(inputs))
            result = crew.kickoff(inputs=inputs)
            logger.info("Crew %s finished on attempt %s", crew_name, attempt)
            return result
        except Exception as exc:  # noqa: BLE001 - crew failures are logged & retried
            last_error = exc
            logger.warning("Crew %s failed (attempt %s): %s", crew_name, attempt, exc)
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Crew {crew_name} failed after {max_retries + 1} attempts") from last_error


def run_crew_with_hooks(
    crew_name: str,
    inputs: dict[str, Any],
    on_success: Callable[[Any], None],
    on_failure: Callable[[Exception], None],
) -> None:
    """Run a crew and call success/failure hooks (used by orchestrators)."""
    try:
        result = run_crew(crew_name=crew_name, inputs=inputs)
        on_success(result)
    except Exception as exc:  # noqa: BLE001
        on_failure(exc)
