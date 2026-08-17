"""
ZipForm (zipLogix) connector — transaction forms automation.

Used by the deal closure workflow: pre-fill listing/offer contracts from
CRM + MLS data and stage them for e-signature.

Env vars: ZIPFORM_API_KEY, ZIPFORM_ACCOUNT_ID, ZIPFORM_ENDPOINT
"""
import os
from typing import Optional

import requests


class ZipFormConnector:
    def __init__(self, api_key: Optional[str] = None, account_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("ZIPFORM_API_KEY", "")
        self.account_id = account_id or os.getenv("ZIPFORM_ACCOUNT_ID", "")
        self.endpoint = os.getenv("ZIPFORM_ENDPOINT", "https://api.zipform.com/v1")

    def prefill_offer_form(self, form_type: str, transaction: dict) -> dict:
        """Create a form with data prefilled; returns form id + signing URL."""
        resp = requests.post(
            f"{self.endpoint}/forms/prefill",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"form_type": form_type, "account_id": self.account_id, "data": transaction},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_signing_status(self, form_id: str) -> str:
        resp = requests.get(
            f"{self.endpoint}/forms/{form_id}",
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("status", "unknown")

    def send_for_signature(self, form_id: str, parties: list[dict]) -> dict:
        resp = requests.post(
            f"{self.endpoint}/forms/{form_id}/sign",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"parties": parties},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
