"""
TMW (TruckMate by Trimble) connector — TMS for trucking fleets.

TMW exposes REST endpoints for orders, shipments, stops, and billing.
This adapter normalizes the pieces the agents need.

Env vars: TMW_API_URL, TMW_API_KEY, TMW_ORGANIZATION_ID
"""
import os
from typing import Optional

import requests


class TMWConnector:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = (base_url or os.getenv("TMW_API_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("TMW_API_KEY", "")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _call(self, method: str, path: str, **kwargs) -> dict:
        resp = requests.request(method, f"{self.base_url}{path}", headers=self._headers(), timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    # -- TMS surface used by agents -------------------------------------------
    def get_shipment(self, reference: str) -> Optional[dict]:
        return self._call("GET", f"/orders?reference={reference}")

    def shipments_in_period(self, period: str) -> list[dict]:
        return self._call("GET", "/orders", params={"period": period}).get("orders", [])

    def create_exception(self, shipment_id: str, exception: dict) -> None:
        self._call("POST", f"/orders/{shipment_id}/exceptions", json=exception)

    def mark_exception(self, exception_id: str, status: str) -> None:
        self._call("PATCH", f"/exceptions/{exception_id}", json={"status": status})

    def submit_claim(self, claim: dict) -> None:
        self._call("POST", "/claims", json=claim)

    def spend_by_lane(self, period: str) -> list[dict]:
        return self._call("GET", "/analytics/spend-by-lane", params={"period": period}).get("lanes", [])

    def spend_by_mode(self, period: str) -> list[dict]:
        return self._call("GET", "/analytics/spend-by-mode", params={"period": period}).get("modes", [])

    def exceptions_in_period(self, period: str) -> list[dict]:
        return self._call("GET", "/exceptions", params={"period": period}).get("exceptions", [])
