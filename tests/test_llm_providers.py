"""
BYO-LLM providers — verify request payloads for each adapter offline.
"""
import json

import pytest

from CORE_AGENT_INFRASTRUCTURE.llm.factory import ChatLLM, build_llm, parse_extra_headers
from CORE_AGENT_INFRASTRUCTURE.llm.providers import (AnthropicProvider, LLMError,
                                                     OllamaProvider, OpenAICompatibleProvider,
                                                     build_provider)


def test_build_provider_registry():
    assert build_provider("ollama").name == "ollama"
    assert build_provider("groq").name == "groq"
    with pytest.raises(LLMError):
        build_provider("not-a-provider")


def test_openai_compatible_payload(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return type("R", (), {"status_code": 200, "json": lambda self: {
            "choices": [{"message": {"content": "hello from the brain"}}]}})()

    monkeypatch.setattr("CORE_AGENT_INFRASTRUCTURE.llm.providers.requests.post", fake_post)
    provider = OpenAICompatibleProvider(api_key="k-test")
    reply = provider.complete([{"role": "user", "content": "hi"}], model="gpt-4o-mini")
    assert reply == "hello from the brain"
    assert captured["url"].endswith("/chat/completions")
    assert captured["headers"]["Authorization"] == "Bearer k-test"
    assert captured["json"]["model"] == "gpt-4o-mini"


def test_anthropic_payload(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured.update(url=url, headers=headers, json=json)
        return type("R", (), {"status_code": 200, "json": lambda self: {
            "content": [{"type": "text", "text": "anthropic reply"}]}})()

    monkeypatch.setattr("CORE_AGENT_INFRASTRUCTURE.llm.providers.requests.post", fake_post)
    provider = AnthropicProvider(api_key="k-test")
    reply = provider.complete([{"role": "user", "content": "hi"}], model="claude-3-5-sonnet")
    assert reply == "anthropic reply"
    assert captured["headers"]["x-api-key"] == "k-test"
    assert captured["json"]["max_tokens"] > 0


def test_ollama_no_key_needed():
    provider = OllamaProvider()
    assert provider.requires_key is False


def test_parse_extra_headers():
    assert parse_extra_headers('{"X-Test": "1"}') == {"X-Test": "1"}
    assert parse_extra_headers("not json") == {}


def test_chatllm_invoke_shape(monkeypatch):
    class FakeProvider:
        name = "fake"

        def complete(self, messages, model, temperature, max_tokens):
            return "the answer"

    llm = ChatLLM(FakeProvider(), fast_model="fast-1", quality_model="quality-1")
    result = llm.invoke("question")
    assert result.content == "the answer"
    assert llm.fast() == "fast-1"
    assert llm.quality() == "quality-1"


def test_chatllm_fallback(monkeypatch):
    class Boom:
        name = "boom"

        def complete(self, *a, **k):
            raise LLMError("down")

    class Safe:
        name = "safe"

        def complete(self, *a, **k):
            return "recovered"

    llm = ChatLLM(Boom(), "fast", "quality", fallback=Safe())
    assert llm.complete([{"role": "user", "content": "x"}]) == "recovered"
