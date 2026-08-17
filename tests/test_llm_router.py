from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.llm_router import LLMRouter


def test_fast_task_uses_fast_model():
    router = LLMRouter(fast_model="gpt-4o-mini", quality_model="gpt-4o")
    decision = router.decide("classify")
    assert decision.model == "gpt-4o-mini"
    assert decision.tier == "fast"


def test_quality_task_uses_quality_model():
    router = LLMRouter(fast_model="gpt-4o-mini", quality_model="gpt-4o")
    decision = router.decide("negotiate")
    assert decision.model == "gpt-4o"
    assert decision.tier == "quality"


def test_cost_estimate():
    router = LLMRouter()
    cheap = router.estimate_cost("gpt-4o-mini", input_tokens=1000, output_tokens=1000)
    pricey = router.estimate_cost("gpt-4o", input_tokens=1000, output_tokens=1000)
    assert cheap > 0
    assert cheap < pricey
