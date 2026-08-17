"""
DHL Express API connector — tracking, rates, shipment creation.

Env vars: DHL_API_KEY, DHL_API_SECRET, DHL_ACCOUNT_NUMBER
"""
import os
from typing import Optional

import requests


class DHLConnector:
    AUTH_URL = "https://api.dhl.com/oauth/token"
    BASE = "https://api.dhl.com"

    def __init__(self, api_key: Optional[str] = None, secret: Optional[str] = None, account: Optional[str] = None):
        self.api_key = api_key or os.getenv("DHL_API_KEY", "")
        self.secret = secret or os.getenv("DHL_API_SECRET", "")
        self.account = account or os.getenv("DHL_ACCOUNT_NUMBER", "")
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
        resp = requests.get(
            f"{self.BASE}/shipments/{tracking_number}?trackingView=all",
            headers=self._headers(), timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def create_shipment(self, payload: dict) -> dict:
        resp = requests.post(f"{self.BASE}/shipments", headers=self._headers(), json=payload, timeout=45)
        resp.raise_for_status()
        return resp.json()
