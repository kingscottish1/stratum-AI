import asyncio
import hashlib
import hmac
import json
import os

from CORE_AGENT_INFRASTRUCTURE.api.webhooks import handle_webhook

AUTH_TOKEN = "test-auth-token"


def _twilio_request(body: dict, sig_override: str | None = None):
    raw = json.dumps(body).encode()
    url = "https://api.stratumai.com/v1/webhooks/twilio"
    expected = hmac.new(AUTH_TOKEN.encode(), (url + raw.decode()).encode(), hashlib.sha256).hexdigest()
    headers = {
        "x-twilio-signature": sig_override or expected,
        "x-forwarded-proto": "https",
        "host": "api.stratumai.com",
        "x-original-uri": "/v1/webhooks/twilio",
    }
    return raw, headers


def test_valid_twilio_webhook_accepted(monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", AUTH_TOKEN)
    raw, headers = _twilio_request({"Body": "Book a cleaning", "From": "+15550101",
                                    "To": "+17205550123", "Channel": "sms",
                                    "MessageSid": "SM123"})
    result = asyncio.run(handle_webhook("twilio", raw, headers))
    assert result["status"] == "accepted"
    assert result["event_id"] == "SM123"
    assert result["event"]["channel"] == "sms"
    assert result["event"]["from"] == "+15550101"


def test_invalid_signature_rejected(monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", AUTH_TOKEN)
    raw, headers = _twilio_request({"Body": "hi"}, sig_override="0" * 40)
    result = asyncio.run(handle_webhook("twilio", raw, headers))
    assert result["status"] == "rejected"


def test_unknown_provider_ignored():
    result = asyncio.run(handle_webhook("nope", b"{}", {}))
    assert result["status"] == "ignored"
