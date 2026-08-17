"""
WhatsApp Business API via Twilio.

Env vars: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM
"""
import os
import logging
from typing import Optional

logger = logging.getLogger("stratum.channels.whatsapp")

try:
    from twilio.rest import Client
except ImportError:  # pragma: no cover
    Client = None


class WhatsAppConnector:
    def __init__(self, from_number: Optional[str] = None):
        if Client is None:
            raise RuntimeError("twilio not installed")
        self.client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        self.from_number = from_number or os.getenv("TWILIO_WHATSAPP_FROM", "")

    def send(self, to: str, body: str) -> dict:
        """Send a WhatsApp message. `to` in E.164; may require template for new chats."""
        message = self.client.messages.create(
            to=f"whatsapp:{to}",
            from_=f"whatsapp:{self.from_number}",
            body=body,
        )
        logger.info("whatsapp sent to=%s sid=%s", to, message.sid)
        return {"sid": message.sid, "status": message.status}

    def send_media(self, to: str, media_url: str, body: str = "") -> dict:
        message = self.client.messages.create(
            to=f"whatsapp:{to}",
            from_=f"whatsapp:{self.from_number}",
            body=body,
            media_url=[media_url],
        )
        return {"sid": message.sid, "status": message.status}
