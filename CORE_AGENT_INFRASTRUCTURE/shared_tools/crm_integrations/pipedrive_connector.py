"""
Pipedrive connector (REST API).

Env vars: PIPEDRIVE_API_TOKEN, PIPEDRIVE_API_DOMAIN (e.g. company.pipedrive.com)
"""
import os
from typing import Optional

import requests

from .crm_base import CRMInterface


class PipedriveConnector(CRMInterface):
    def __init__(self):
        self.token = os.getenv("PIPEDRIVE_API_TOKEN", "")
        self.domain = os.getenv("PIPEDRIVE_API_DOMAIN", "api.pipedrive.com")
        self.base = f"https://{self.domain}/v1"

    def _params(self, **extra) -> dict:
        return {"api_token": self.token, **extra}

    def get_contact(self, contact_id: str) -> Optional[dict]:
        resp = requests.get(f"{self.base}/persons/{contact_id}", params=self._params(), timeout=30)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json().get("data")

    def find_contact(self, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[dict]:
        if not email and not phone:
            return None
        term = email or phone
        resp = requests.get(
            f"{self.base}/persons/search",
            params=self._params(term=term, limit=1),
            timeout=30,
        )
        resp.raise_for_status()
        items = resp.json().get("data", {}).get("items", [])
        return items[0]["item"] if items else None

    def create_contact(self, data: dict) -> str:
        resp = requests.post(
            f"{self.base}/persons",
            params=self._params(),
            json={"name": data.get("name", "Unknown"), **data},
            timeout=30,
        )
        resp.raise_for_status()
        return str(resp.json()["data"]["id"])

    def update_contact(self, contact_id: str, data: dict) -> None:
        requests.put(f"{self.base}/persons/{contact_id}", params=self._params(), json=data, timeout=30)

    def log_activity(self, contact_id: str, activity_type: str, note: str) -> None:
        requests.post(
            f"{self.base}/activities",
            params=self._params(),
            json={"subject": activity_type, "note": note, "person_id": contact_id},
            timeout=30,
        )

    def create_deal(self, contact_id: str, title: str, stage: str, value: float) -> str:
        resp = requests.post(
            f"{self.base}/deals",
            params=self._params(),
            json={"title": title, "stage_id": stage, "value": value, "person_id": contact_id},
            timeout=30,
        )
        resp.raise_for_status()
        return str(resp.json()["data"]["id"])
