"""
Follow Up Boss CRM connector — the most common CRM in real estate.

Env vars: FUB_API_KEY, FUB_EMAIL (partner API) or FUB_ACCESS_KEY
"""
import os
from typing import Optional

import requests

from CORE_AGENT_INFRASTRUCTURE.shared_tools.crm_integrations.crm_base import CRMInterface

FUB_BASE = "https://api.followupboss.com/v1"


class FollowUpBossCRM(CRMInterface):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FUB_API_KEY", "")

    def _auth(self) -> tuple[str, str]:
        return (self.api_key, "")  # HTTP basic auth, empty password

    def find_contact(self, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[dict]:
        if not email and not phone:
            return None
        params = {"email": email} if email else {"phone": phone}
        resp = requests.get(f"{FUB_BASE}/people", params=params, auth=self._auth(), timeout=30)
        resp.raise_for_status()
        people = resp.json().get("people", [])
        return people[0] if people else None

    def create_contact(self, data: dict) -> str:
        payload = {"firstName": data.get("first_name", ""), "lastName": data.get("last_name", ""),
                   "emails": [{"value": data.get("email", "")}] if data.get("email") else [],
                   "phones": [{"value": data.get("phone", "")}] if data.get("phone") else []}
        if data.get("source"):
            payload["source"] = data["source"]
        resp = requests.post(f"{FUB_BASE}/people", json=payload, auth=self._auth(), timeout=30)
        resp.raise_for_status()
        return str(resp.json().get("id", ""))

    def update_contact(self, contact_id: str, data: dict) -> None:
        resp = requests.put(f"{FUB_BASE}/people/{contact_id}", json=data, auth=self._auth(), timeout=30)
        resp.raise_for_status()

    def log_activity(self, contact_id: str, activity_type: str, note: str) -> None:
        resp = requests.post(
            f"{FUB_BASE}/events",
            json={"personId": contact_id, "type": activity_type, "message": note, "source": "AI Agency"},
            auth=self._auth(), timeout=30,
        )
        resp.raise_for_status()

    def create_deal(self, contact_id: str, title: str, stage: str, value: float) -> str:
        # FUB tracks deals via custom fields; log as activity instead
        self.log_activity(contact_id, "Deal", f"{title} @ ${value:,.0f} (stage: {stage})")
        return ""

    def get_contact(self, contact_id: str) -> Optional[dict]:
        resp = requests.get(f"{FUB_BASE}/people/{contact_id}", auth=self._auth(), timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
