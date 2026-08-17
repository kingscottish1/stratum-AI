"""
Generic real-estate CRM connector (LionDesk, kvCORE, Real Geeks, etc.).

Most real-estate CRMs expose a REST API with the same shape:
contacts, deals/pipelines, activities. This adapter implements the
CRMInterface against that common shape; configure the base URL and
endpoint paths per the vendor.

Env vars: RE_CRM_BASE_URL, RE_CRM_API_KEY
"""
import os
from typing import Optional

import requests

from CORE_AGENT_INFRASTRUCTURE.shared_tools.crm_integrations.crm_base import CRMInterface


class RealEstateCRM(CRMInterface):
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = (base_url or os.getenv("RE_CRM_BASE_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("RE_CRM_API_KEY", "")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _call(self, method: str, path: str, **kwargs) -> dict:
        resp = requests.request(method, f"{self.base_url}{path}",
                                headers=self._headers(), timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def find_contact(self, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[dict]:
        if not email and not phone:
            return None
        q = email or phone
        data = self._call("GET", "/contacts/search", params={"q": q, "limit": 1})
        contacts = data.get("contacts", data.get("data", []))
        return contacts[0] if contacts else None

    def create_contact(self, data: dict) -> str:
        result = self._call("POST", "/contacts", json=data)
        return str(result.get("id", result.get("contact_id", "")))

    def update_contact(self, contact_id: str, data: dict) -> None:
        self._call("PUT", f"/contacts/{contact_id}", json=data)

    def log_activity(self, contact_id: str, activity_type: str, note: str) -> None:
        self._call("POST", f"/contacts/{contact_id}/activities",
                   json={"type": activity_type, "note": note})

    def create_deal(self, contact_id: str, title: str, stage: str, value: float) -> str:
        result = self._call("POST", "/deals",
                            json={"contact_id": contact_id, "title": title,
                                  "stage": stage, "value": value})
        return str(result.get("id", ""))

    def get_contact(self, contact_id: str) -> Optional[dict]:
        try:
            return self._call("GET", f"/contacts/{contact_id}")
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                return None
            raise
