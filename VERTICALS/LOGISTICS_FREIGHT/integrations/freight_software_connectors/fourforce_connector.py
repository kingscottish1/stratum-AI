"""
4Front / transportation management middleware connector.

Some clients run freight operations on 4Front-style TMS/middleware stacks.
This adapter wraps the client-specific endpoints behind the same TMS
interface the agents expect (see tmw_connector.py for the contract).

Env vars: FOURFORCE_API_URL, FOURFORCE_API_KEY
"""
import os
from typing import Optional

import requests


class FourForceConnector:
    """Generic REST wrapper; endpoint map set per client instance."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = (base_url or os.getenv("FOURFORCE_API_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("FOURFORCE_API_KEY", "")
        # per-client endpoint map, filled during onboarding
        self.endpoints = {
            "shipment": "/shipments",
            "exceptions": "/exceptions",
            "claims": "/claims",
            "spend_by_lane": "/analytics/spend/lane",
            "spend_by_mode": "/analytics/spend/mode",
        }

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _call(self, method: str, path: str, **kwargs) -> dict:
        resp = requests.request(method, f"{self.base_url}{path}", headers=self._headers(), timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def get_shipment(self, reference: str) -> Optional[dict]:
        return self._call("GET", f"{self.endpoints['shipment']}?reference={reference}")

    def create_exception(self, shipment_id: str, exception: dict) -> None:
        self._call("POST", self.endpoints["exceptions"], json={**exception, "shipment_id": shipment_id})

    def submit_claim(self, claim: dict) -> None:
        self._call("POST", self.endpoints["claims"], json=claim)
