"""
LLMRouter: route each call to the cheapest model that can do the job.

Strategy:
  - classification / extraction / summarization  -> fast_model
  - generation / negotiation / complex reasoning -> quality_model
  - fallback: if quality model fails, degrade gracefully (or vice versa)

This is one of the agency's biggest margin levers: ~70-80% of traffic
can run on fast/cheap models.
"""
import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger("stratum.llm_router")

FAST_TASKS = {"classify", "extract", "summarize", "sentiment", "translate", "parse"}
QUALITY_TASKS = {"generate", "negotiate", "reason", "compose", "resolve", "review"}


@dataclass
class RoutingDecision:
    model: str
    tier: str
    estimated_cost_usd: float
    task_type: str


class LLMRouter:
    """Routes LLM calls based on task type and remaining budget."""

    # rough per-1k-token costs (input) used for budget tracking
    MODEL_COSTS = {
        "gpt-4o-mini": 0.00015,
        "gpt-4o": 0.0025,
        "claude-3-5-haiku": 0.0008,
        "claude-3-5-sonnet": 0.003,
    }

    def __init__(self, fast_model: str = "gpt-4o-mini", quality_model: str = "gpt-4o"):
        self.fast_model = fast_model
        self.quality_model = quality_model

    def decide(self, task_type: str, input_tokens: int = 500) -> RoutingDecision:
        if task_type in QUALITY_TASKS:
            model = self.quality_model
            tier = "quality"
        elif task_type in FAST_TASKS:
            model = self.fast_model
            tier = "fast"
        else:
            # unknown -> use fast; orchestrators can override
            model = self.fast_model
            tier = "fast"
        cost = self.estimate_cost(model, input_tokens)
        logger.debug("routed task=%s -> %s (~$%.5f)", task_type, model, cost)
        return RoutingDecision(model=model, tier=tier, estimated_cost_usd=cost, task_type=task_type)

    def estimate_cost(self, model: str, input_tokens: int, output_tokens: int = 200) -> float:
        per_1k = self.MODEL_COSTS.get(model, 0.001)
        return (input_tokens + output_tokens) / 1000 * per_1k

    def get_llm(self, task_type: str, providers: dict[str, Any]) -> Any:
        """Return the right LLM object from the providers dict."""
        decision = self.decide(task_type)
        return providers.get(decision.model) or providers.get(self.fast_model)


router = LLMRouter()
