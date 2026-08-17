"""
LLMFactory — the plug-and-play brain.

Builds a ready-to-use ChatLLM from config only:
  LLM_PROVIDER=... LLM_API_KEY=... LLM_BASE_URL=... LLM_MODEL_FAST=...
  LLM_MODEL_QUALITY=... LLM_FALLBACK_PROVIDER=... LLM_EXTRA_HEADERS=...

Every agent in the platform calls `.invoke(prompt, temperature=...)` and
gets back an object with `.content` — same shape for every provider.
"""
import json
import logging
import time
from types import SimpleNamespace
from typing import Optional

from CORE_AGENT_INFRASTRUCTURE.config import AppConfig, get_config
from CORE_AGENT_INFRASTRUCTURE.llm.providers import LLMError, LLMProvider, build_provider

logger = logging.getLogger("stratum.llm")


class ChatLLM:
    """Provider-agnostic facade used by all agents."""

    def __init__(self, provider: LLMProvider, fast_model: str, quality_model: str,
                 fallback: Optional[LLMProvider] = None, max_tokens: int = 2048,
                 extra_headers: Optional[dict] = None):
        self.provider = provider
        self.fallback = fallback
        self.fast_model = fast_model
        self.quality_model = quality_model
        self.max_tokens = max_tokens
        self.extra_headers = extra_headers or {}
        self.last_model: str = ""
        self.last_cost_estimate: float = 0.0

    # -- call surface used by agents ------------------------------------------------
    def invoke(self, prompt: str, temperature: float = 0.2, model: Optional[str] = None,
               system: Optional[str] = None, **kwargs):
        """One-shot prompt -> response object with `.content`."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        content = self.complete(messages, temperature=temperature, model=model)
        return SimpleNamespace(content=content)

    def complete(self, messages: list[dict], temperature: float = 0.2,
                 model: Optional[str] = None) -> str:
        """Chat completion with automatic fallback to the second provider."""
        chosen = model or self.fast_model
        self.last_model = chosen
        started = time.monotonic()
        try:
            reply = self.provider.complete(messages, model=chosen, temperature=temperature,
                                           max_tokens=self.max_tokens)
        except LLMError as exc:
            if self.fallback is not None:
                logger.warning("primary LLM failed (%s), falling back to %s", exc, self.fallback.name)
                reply = self.fallback.complete(messages, model=chosen, temperature=temperature,
                                               max_tokens=self.max_tokens)
            else:
                raise
        self.last_cost_estimate = _estimate_cost(self.last_model, messages, reply)
        logger.debug("llm model=%s latency=%.2fs cost~$%.5f",
                     chosen, time.monotonic() - started, self.last_cost_estimate)
        return reply

    def fast(self) -> str:
        return self.fast_model

    def quality(self) -> str:
        return self.quality_model


def _estimate_cost(model: str, messages: list[dict], reply: str) -> float:
    """Rough per-1k-token cost estimate for margin tracking (fast/quality tiers)."""
    tokens = sum(len(m.get("content", "")) for m in messages) // 4 + len(reply) // 4
    if any(k in model for k in ("mini", "haiku", "flash", "8b", "7b", "13b", "70b", "llama")):
        rate = 0.00015
    else:
        rate = 0.0025
    return round(tokens / 1000 * rate, 6)


def parse_extra_headers(raw: str) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        logger.warning("LLM_EXTRA_HEADERS is not valid JSON; ignoring")
        return {}


def build_llm(cfg: Optional[AppConfig] = None) -> ChatLLM:
    """Build the ChatLLM from config — the ONLY way the app creates an LLM."""
    cfg = cfg or get_config()
    headers = parse_extra_headers(cfg.llm_extra_headers)
    primary = build_provider(
        cfg.llm_provider,
        api_key=cfg.llm_api_key,
        base_url=cfg.llm_base_url,
        timeout=cfg.llm_timeout,
        extra_headers=headers,
    )
    if not primary.api_key and primary.requires_key:
        raise LLMError(
            f"LLM provider '{cfg.llm_provider}' requires LLM_API_KEY — "
            "set it in .env or your secret store (bring your own key)."
        )
    fallback = None
    if cfg.llm_fallback_provider:
        fallback = build_provider(
            cfg.llm_fallback_provider,
            api_key=cfg.llm_api_key,
            base_url=cfg.llm_base_url,
            timeout=cfg.llm_timeout,
            extra_headers=headers,
        )
    return ChatLLM(
        provider=primary,
        fallback=fallback,
        fast_model=cfg.llm_model_fast,
        quality_model=cfg.llm_model_quality,
        max_tokens=cfg.llm_max_tokens,
        extra_headers=headers,
    )
