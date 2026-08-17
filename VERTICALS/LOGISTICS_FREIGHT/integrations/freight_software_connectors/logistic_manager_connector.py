"""
Logistic Manager (freight management software) connector.

Logistic Manager provides REST APIs for quotes, shipments, carriers and
documents. Adapter normalizes to the agent-facing TMS contract.

Env vars: LOGISTIC_MANAGER_URL, LOGISTIC_MANAGER_TOKEN
"""
import os
from typing import Optional

import requests


class LogisticManagerConnector:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = (base_url or os.getenv("LOGISTIC_MANAGER_URL", "")).rstrip("/")
        self.token = token or os.getenv("LOGISTIC_MANAGER_TOKEN", "")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def _call(self, method: str, path: str, **kwargs) -> dict:
        resp = requests.request(method, f"{self.base_url}{path}", headers=self._headers(), timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def get_shipment(self, reference: str) -> Optional[dict]:
        return self._call("GET", f"/api/shipments/{reference}")

    def get_rate(self, carrier: str, lane: tuple, equipment: Optional[str] = None) -> Optional[dict]:
        return self._call("GET", "/api/rates", params={
            "carrier": carrier, "origin": lane[0], "destination": lane[1], "equipment": equipment,
        })

    def shipments_in_period(self, period: str) -> list[dict]:
        return self._call("GET", "/api/shipments", params={"period": period}).get("shipments", [])

    def create_exception(self, shipment_id: str, exception: dict) -> None:
        self._call("POST", f"/api/shipments/{shipment_id}/exceptions", json=exception)

    def exceptions_in_period(self, period: str) -> list[dict]:
        return self._call("GET", "/api/exceptions", params={"period": period}).get("exceptions", [])
