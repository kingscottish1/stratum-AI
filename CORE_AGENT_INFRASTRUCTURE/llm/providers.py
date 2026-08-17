"""
BYO-LLM providers — plug in ANY brain by config, no code changes.

All adapters speak plain HTTP (requests), so no vendor SDKs are required.
Each provider implements `complete(messages, model, temperature, max_tokens)`.

Supported out of the box:
  openai             — OpenAI Chat Completions
  openai_compatible  — ANY endpoint exposing OpenAI-style /chat/completions
                       (Groq, Together, vLLM, LM Studio, LocalAI, ...)
  azure              — Azure OpenAI (api-version query param)
  openrouter         — OpenRouter (model routing across vendors)
  groq               — Groq (fast open models)
  together           — Together AI
  anthropic          — Anthropic Messages API
  ollama             — local models, no key required
"""
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

import requests

logger = logging.getLogger("stratum.llm")


class LLMError(RuntimeError):
    pass


class LLMProvider(ABC):
    name = "base"

    def __init__(self, api_key: str = "", base_url: str = "", timeout: int = 60,
                 extra_headers: Optional[dict] = None):
        self.api_key = api_key
        self.base_url = (base_url or self.default_base_url).rstrip("/")
        self.timeout = timeout
        self.extra_headers = extra_headers or {}

    @property
    def default_base_url(self) -> str:
        return ""

    @property
    def requires_key(self) -> bool:
        return True

    @abstractmethod
    def complete(self, messages: list[dict], model: str, temperature: float = 0.2,
                 max_tokens: int = 1024) -> str:
        """Return the assistant reply text for the given chat messages."""

    def _post(self, url: str, headers: dict, payload: dict) -> dict:
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except requests.RequestException as exc:
            raise LLMError(f"{self.name} unreachable: {exc}") from exc
        if resp.status_code >= 400:
            raise LLMError(f"{self.name} HTTP {resp.status_code}: {resp.text[:300]}")
        return resp.json()


# --- OpenAI + any OpenAI-compatible endpoint -----------------------------------
class OpenAICompatibleProvider(LLMProvider):
    """Generic adapter for OpenAI-style /chat/completions endpoints."""

    name = "openai_compatible"
    default_base_url = "https://api.openai.com/v1"

    def __init__(self, api_key: str = "", base_url: str = "", timeout: int = 60,
                 extra_headers: Optional[dict] = None, chat_path: str = "/chat/completions"):
        super().__init__(api_key, base_url, timeout, extra_headers)
        self.chat_path = chat_path

    def complete(self, messages, model, temperature=0.2, max_tokens=1024) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            **self.extra_headers,
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = self._post(self.base_url + self.chat_path, headers, payload)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected response shape from {self.name}: {str(data)[:200]}") from exc


class OpenAIProvider(OpenAICompatibleProvider):
    name = "openai"
    default_base_url = "https://api.openai.com/v1"


class OpenRouterProvider(OpenAICompatibleProvider):
    name = "openrouter"
    default_base_url = "https://openrouter.ai/api/v1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # OpenRouter likes referer headers for rankings
        self.extra_headers.setdefault("HTTP-Referer", "https://stratumai.com")
        self.extra_headers.setdefault("X-Title", "Stratum AI")


class GroqProvider(OpenAICompatibleProvider):
    name = "groq"
    default_base_url = "https://api.groq.com/openai/v1"


class TogetherProvider(OpenAICompatibleProvider):
    name = "together"
    default_base_url = "https://api.together.xyz/v1"


class AzureOpenAIProvider(OpenAICompatibleProvider):
    """Azure OpenAI: base_url = https://<resource>.openai.azure.com/openai/deployments/<deploy>
    plus ?api-version=2024-06-01 (appended automatically).
    """

    name = "azure"

    def __init__(self, *args, api_version: str = "2024-06-01", **kwargs):
        super().__init__(*args, **kwargs)
        self.api_version = api_version

    def complete(self, messages, model, temperature=0.2, max_tokens=1024) -> str:
        headers = {"Content-Type": "application/json", "api-key": self.api_key, **self.extra_headers}
        payload = {
            "model": model, "messages": messages,
            "temperature": temperature, "max_tokens": max_tokens,
        }
        sep = "&" if "?" in self.base_url else "?"
        url = f"{self.base_url}{sep}api-version={self.api_version}"
        data = self._post(url, headers, payload)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError(f"Unexpected response shape from azure: {str(data)[:200]}") from exc


# --- Anthropic -------------------------------------------------------------------
class AnthropicProvider(LLMProvider):
    name = "anthropic"
    default_base_url = "https://api.anthropic.com/v1"

    @property
    def requires_key(self) -> bool:
        return True

    def complete(self, messages, model, temperature=0.2, max_tokens=1024) -> str:
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        chat = [{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"]
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            **self.extra_headers,
        }
        payload = {"model": model, "messages": chat, "max_tokens": max_tokens,
                   "temperature": temperature}
        if system:
            payload["system"] = system
        data = self._post(self.base_url + "/messages", headers, payload)
        try:
            return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        except (KeyError, TypeError) as exc:
            raise LLMError(f"Unexpected response shape from anthropic: {str(data)[:200]}") from exc


# --- Ollama (local models — bring your own GPU) -------------------------------------
class OllamaProvider(LLMProvider):
    name = "ollama"
    default_base_url = "http://localhost:11434"

    @property
    def requires_key(self) -> bool:
        return False

    def complete(self, messages, model, temperature=0.2, max_tokens=1024) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        data = self._post(self.base_url + "/api/chat", {"Content-Type": "application/json"}, payload)
        try:
            return data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMError(f"Unexpected response shape from ollama: {str(data)[:200]}") from exc


# --- Registry -------------------------------------------------------------------------
PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "openai_compatible": OpenAICompatibleProvider,
    "azure": AzureOpenAIProvider,
    "openrouter": OpenRouterProvider,
    "groq": GroqProvider,
    "together": TogetherProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}


def build_provider(provider: str, api_key: str = "", base_url: str = "",
                   timeout: int = 60, extra_headers: Optional[dict] = None) -> LLMProvider:
    cls = PROVIDER_REGISTRY.get(provider)
    if cls is None:
        raise LLMError(
            f"Unknown LLM_PROVIDER '{provider}'. Supported: "
            + ", ".join(sorted(PROVIDER_REGISTRY))
        )
    return cls(api_key=api_key, base_url=base_url, timeout=timeout, extra_headers=extra_headers)
