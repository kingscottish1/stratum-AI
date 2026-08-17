"""
Manhattan Associates (WMS) connector — warehouse execution data.

Provides shipment status, dwell times and dock scheduling for the
exception detector's warehouse-related checks.

Env vars: MANHATTAN_URL, MANHATTAN_CLIENT_ID, MANHATTAN_CLIENT_SECRET
"""
import os
from typing import Optional

import requests


class ManhattanConnector:
    def __init__(self, base_url: Optional[str] = None, client_id: Optional[str] = None,
                 client_secret: Optional[str] = None):
        self.base_url = (base_url or os.getenv("MANHATTAN_URL", "")).rstrip("/")
        self.client_id = client_id or os.getenv("MANHATTAN_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("MANHATTAN_CLIENT_SECRET", "")
        self._token: Optional[str] = None

    def _auth(self) -> str:
        if self._token:
            return self._token
        resp = requests.post(
            f"{self.base_url}/oauth/token",
            data={"grant_type": "client_credentials", "client_id": self.client_id,
                  "client_secret": self.client_secret},
            timeout=30,
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._auth()}", "Content-Type": "application/json"}

    def shipment_dwell(self, shipment_id: str) -> dict:
        """Dwell time breakdown per warehouse node."""
        resp = requests.get(f"{self.base_url}/shipments/{shipment_id}/dwell",
                            headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def dock_schedule(self, warehouse_id: str, date: str) -> list[dict]:
        resp = requests.get(f"{self.base_url}/warehouses/{warehouse_id}/dock-schedule",
                            headers=self._headers(), params={"date": date}, timeout=30)
        resp.raise_for_status()
        return resp.json().get("appointments", [])
