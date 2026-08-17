"""
HubSpot connector (REST API via requests).

Env vars: HUBSPOT_API_KEY (private app token)
"""
import os
from typing import Optional

import requests

from .crm_base import CRMInterface

API_BASE = "https://api.hubapi.com/crm/v3"


class HubSpotConnector(CRMInterface):
    def __init__(self):
        self.token = os.getenv("HUBSPOT_API_KEY", "")
        if not self.token:
            raise RuntimeError("HUBSPOT_API_KEY is not set")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _search(self, field: str, value: str) -> Optional[dict]:
        resp = requests.post(
            f"{API_BASE}/objects/contacts/search",
            headers=self.headers,
            json={
                "filterGroups": [{"filters": [{"propertyName": field, "operator": "EQ", "value": value}]}],
                "limit": 1,
            },
            timeout=30,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return results[0] if results else None

    def get_contact(self, contact_id: str) -> Optional[dict]:
        resp = requests.get(f"{API_BASE}/objects/contacts/{contact_id}", headers=self.headers, timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    def find_contact(self, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[dict]:
        if email:
            return self._search("email", email)
        if phone:
            return self._search("phone", phone)
        return None

    def create_contact(self, data: dict) -> str:
        resp = requests.post(
            f"{API_BASE}/objects/contacts",
            headers=self.headers,
            json={"properties": data},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def update_contact(self, contact_id: str, data: dict) -> None:
        resp = requests.patch(
            f"{API_BASE}/objects/contacts/{contact_id}",
            headers=self.headers,
            json={"properties": data},
            timeout=30,
        )
        resp.raise_for_status()

    def log_activity(self, contact_id: str, activity_type: str, note: str) -> None:
        # Log via engagements endpoint (legacy) or a note object
        resp = requests.post(
            f"{API_BASE}/objects/notes",
            headers=self.headers,
            json={
                "properties": {"hs_timestamp": None, "hs_note_body": note},
                "associations": [
                    {
                        "to": {"id": contact_id},
                        "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}],
                    }
                ],
            },
            timeout=30,
        )
        if resp.status_code >= 400:
            # non-fatal: activity logging must not break the agent run
            pass

    def create_deal(self, contact_id: str, title: str, stage: str, value: float) -> str:
        resp = requests.post(
            f"{API_BASE}/objects/deals",
            headers=self.headers,
            json={"properties": {"dealname": title, "dealstage": stage, "amount": str(value)}},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["id"]
