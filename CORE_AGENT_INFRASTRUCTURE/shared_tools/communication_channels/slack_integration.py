"""
Slack notifications via incoming webhooks.

Env vars: SLACK_WEBHOOK_URL
"""
import json
import os
import logging

import requests

logger = logging.getLogger("stratum.channels.slack")


class SlackIntegration:
    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")

    def post(self, text: str, channel: str = "", blocks: list | None = None) -> bool:
        """Post a message to the configured Slack workspace."""
        if not self.webhook_url:
            logger.warning("SLACK_WEBHOOK_URL not set; message dropped")
            return False
        payload: dict = {"text": text}
        if channel:
            payload["channel"] = channel
        if blocks:
            payload["blocks"] = blocks
        resp = requests.post(self.webhook_url, json=payload, timeout=30)
        resp.raise_for_status()
        return True

    def alert_human_handoff(self, customer: str, reason: str, context: str = "") -> bool:
        """Standard alert used when an agent escalates to a human."""
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "⚠️ Human handoff required"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Customer:* {customer}\n*Reason:* {reason}"}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"```{context[:500]}```"}]},
        ]
        return self.post("Human handoff required", blocks=blocks)
