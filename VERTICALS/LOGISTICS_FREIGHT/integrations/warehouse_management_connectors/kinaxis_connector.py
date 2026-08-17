"""
Kinaxis (Maestro) connector — supply chain planning & WMS data.

Used for dwell-time detection, inventory visibility, and shipment
coordination with warehouse schedules.

Env vars: KINAXIS_URL, KINAXIS_API_KEY, KINAXIS_TENANT
"""
import os
from typing import Optional

import requests


class KinaxisConnector:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = (base_url or os.getenv("KINAXIS_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("KINAXIS_API_KEY", "")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
                "X-Tenant": os.getenv("KINAXIS_TENANT", "")}

    def _call(self, method: str, path: str, **kwargs) -> dict:
        resp = requests.request(method, f"{self.base_url}{path}", headers=self._headers(), timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def shipment_warehouse_slots(self, warehouse_id: str, date: str) -> list[dict]:
        return self._call("GET", f"/api/warehouses/{warehouse_id}/slots", params={"date": date}).get("slots", [])

    def inventory_visibility(self, sku: str, warehouse_id: str) -> dict:
        return self._call("GET", f"/api/inventory/{warehouse_id}/{sku}")
