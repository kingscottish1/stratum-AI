"""
Webhook dispatch: verify signatures, normalize events, enqueue to worker.

Supported providers: twilio, slack, hubspot, calendly.
"""
import hashlib
import hmac
import json
import logging
import os
from typing import Any, Callable

logger = logging.getLogger("stratum.webhooks")

PROVIDERS: dict[str, Callable[[bytes, dict], dict]] = {}


def register_provider(name: str, verifier: Callable[[bytes, dict], dict]) -> None:
    PROVIDERS[name] = verifier


def _verify_twilio(raw: bytes, headers: dict) -> dict:
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
    signature = headers.get("x-twilio-signature", "")
    url = headers.get("x-forwarded-proto", "https") + "://" + headers.get("host", "") + headers.get("x-original-uri", "")
    expected = hmac.new(auth_token.encode(), (url + raw.decode()).encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise PermissionError("Invalid Twilio signature")
    payload = json.loads(raw)
    return {
        "provider": "twilio",
        "channel": "whatsapp" if payload.get("Channel") == "whatsapp" else "sms",
        "from": payload.get("From", "").replace("whatsapp:", ""),
        "to": payload.get("To", "").replace("whatsapp:", ""),
        "body": payload.get("Body", ""),
        "message_sid": payload.get("MessageSid"),
    }


register_provider("twilio", _verify_twilio)


def _verify_slack(raw: bytes, headers: dict) -> dict:
    signing_secret = os.getenv("SLACK_SIGNING_SECRET", "")
    ts = headers.get("x-slack-request-timestamp", "")
    signature = headers.get("x-slack-signature", "")
    base = f"v0:{ts}:{raw.decode()}"
    expected = "v0=" + hmac.new(signing_secret.encode(), base.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise PermissionError("Invalid Slack signature")
    payload = json.loads(raw)
    event = payload.get("event", {})
    return {
        "provider": "slack",
        "event": event.get("type"),
        "channel": event.get("channel"),
        "text": event.get("text", ""),
        "user": event.get("user"),
    }


register_provider("slack", _verify_slack)


def _verify_hubspot(raw: bytes, headers: dict) -> dict:
    secret = os.getenv("HUBSPOT_CLIENT_SECRET", "")
    signature = headers.get("x-hubspot-signature", "")
    expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise PermissionError("Invalid HubSpot signature")
    payload = json.loads(raw)
    first = payload[0] if isinstance(payload, list) and payload else payload
    return {
        "provider": "hubspot",
        "event": first.get("subscriptionType"),
        "object_id": first.get("objectId"),
        "portal_id": first.get("portalId"),
    }


register_provider("hubspot", _verify_hubspot)


def _verify_calendly(raw: bytes, headers: dict) -> dict:
    secret = os.getenv("CALENDLY_WEBHOOK_SECRET", "")
    signature = headers.get("x-hub-signature-256", "")
    expected = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise PermissionError("Invalid Calendly signature")
    payload = json.loads(raw)
    return {
        "provider": "calendly",
        "event": payload.get("event"),
        "invitee": payload.get("payload", {}).get("email"),
        "uri": payload.get("payload", {}).get("uri"),
    }


register_provider("calendly", _verify_calendly)


async def handle_webhook(provider: str, raw: bytes, headers: dict) -> dict:
    if provider not in PROVIDERS:
        logger.warning("unknown webhook provider: %s", provider)
        return {"status": "ignored", "reason": "unknown_provider"}
    try:
        event = PROVIDERS[provider](raw, headers)
    except PermissionError as exc:
        logger.warning("webhook signature failure: %s", exc)
        return {"status": "rejected", "reason": "bad_signature"}
    logger.info("webhook accepted provider=%s", provider)
    return {"status": "accepted", "event": event, "event_id": event.get("message_sid", "n/a")}
