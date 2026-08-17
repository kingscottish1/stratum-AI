"""
FedEx API connector — tracking, rates and shipment creation.

Env vars: FEDEX_API_KEY, FEDEX_SECRET_KEY, FEDEX_ACCOUNT_NUMBER
"""
import os
from typing import Optional

import requests


class FedExConnector:
    AUTH_URL = "https://apis.fedex.com/oauth/token"
    BASE = "https://apis.fedex.com"

    def __init__(self, api_key: Optional[str] = None, secret: Optional[str] = None, account: Optional[str] = None):
        self.api_key = api_key or os.getenv("FEDEX_API_KEY", "")
        self.secret = secret or os.getenv("FEDEX_SECRET_KEY", "")
        self.account = account or os.getenv("FEDEX_ACCOUNT_NUMBER", "")
        self._token: Optional[str] = None

    def _auth(self) -> str:
        if self._token:
            return self._token
        resp = requests.post(
            self.AUTH_URL,
            data={"grant_type": "client_credentials", "client_id": self.api_key, "client_secret": self.secret},
            timeout=30,
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._auth()}", "Content-Type": "application/json"}

    def track(self, tracking_number: str) -> dict:
        resp = requests.post(
            f"{self.BASE}/track/v1/trackingnumbers",
            headers=self._headers(),
            json={"trackingInfo": [{"trackingNumberInfo": {"trackingNumber": tracking_number}}]},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def create_shipment(self, payload: dict) -> dict:
        """Create a shipment (rate + ship). See FedEx Ship API docs."""
        resp = requests.post(f"{self.BASE}/ship/v1/shipments", headers=self._headers(), json=payload, timeout=45)
        resp.raise_for_status()
        return resp.json()
