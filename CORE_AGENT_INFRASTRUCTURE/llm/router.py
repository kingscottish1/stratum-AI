"""
Model router — sends cheap work to the fast model, hard work to the quality
model. Model names come from config (BYO-LLM), never hardcoded.

Task tiers:
  fast    — classify, extract, summarize, translate, parse, sentiment
  quality — generate, negotiate, reason, compose, resolve, review
"""
from typing import Any, Optional

FAST_TASKS = {"classify", "extract", "summarize", "sentiment", "translate", "parse"}
QUALITY_TASKS = {"generate", "negotiate", "reason", "compose", "resolve", "review"}


def route(task_type: str) -> str:
    """Return the tier name for a task type."""
    if task_type in QUALITY_TASKS:
        return "quality"
    return "fast"


def model_for_task(task_type: str, fast_model: str, quality_model: str) -> str:
    return quality_model if task_type in QUALITY_TASKS else fast_model


class LLMRouter:
    """Config-driven router (kept for compatibility with agent code)."""

    def __init__(self, fast_model: Optional[str] = None, quality_model: Optional[str] = None):
        from CORE_AGENT_INFRASTRUCTURE.config import get_config

        cfg = get_config()
        self.fast_model = fast_model or cfg.llm_model_fast
        self.quality_model = quality_model or cfg.llm_model_quality

    def decide(self, task_type: str, input_tokens: int = 500) -> dict:
        tier = route(task_type)
        model = self.quality_model if tier == "quality" else self.fast_model
        rate = 0.0025 if tier == "quality" else 0.00015
        return {
            "model": model,
            "tier": tier,
            "estimated_cost_usd": round((input_tokens + 200) / 1000 * rate, 5),
            "task_type": task_type,
        }

    def get_llm(self, task_type: str, providers: dict[str, Any]) -> Any:
        decision = self.decide(task_type)
        return providers.get(decision["model"]) or providers.get(self.fast_model)


router = LLMRouter()
