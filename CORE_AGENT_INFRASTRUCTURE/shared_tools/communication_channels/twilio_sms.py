"""
Twilio SMS sender.

Env vars: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
"""
import os
import logging
from typing import Optional

logger = logging.getLogger("stratum.channels.sms")

try:
    from twilio.rest import Client
except ImportError:  # pragma: no cover
    Client = None


class TwilioSMS:
    def __init__(self, from_number: Optional[str] = None):
        if Client is None:
            raise RuntimeError("twilio not installed")
        self.client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        self.from_number = from_number or os.getenv("TWILIO_FROM_NUMBER", "")

    def send(self, to: str, body: str) -> dict:
        """Send an SMS. `to` must be E.164 (+1XXXXXXXXXX)."""
        if len(body) > 1600:
            logger.warning("SMS body exceeds 1600 chars, truncating")
            body = body[:1600]
        message = self.client.messages.create(to=to, from_=self.from_number, body=body)
        logger.info("sms sent to=%s sid=%s", to, message.sid)
        return {"sid": message.sid, "status": message.status, "to": to}

    def send_template(self, to: str, template: str, **kwargs) -> dict:
        """Send an SMS from a template string with {placeholders}."""
        return self.send(to, template.format(**kwargs))
