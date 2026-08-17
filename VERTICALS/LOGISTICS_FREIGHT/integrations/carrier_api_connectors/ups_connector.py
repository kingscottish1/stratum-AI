"""
UPS API connector — tracking, rates, and shipment creation.

Env vars: UPS_CLIENT_ID, UPS_CLIENT_SECRET, UPS_ACCOUNT_NUMBER
"""
import os
from typing import Optional

import requests


class UPSConnector:
    AUTH_URL = "https://onlinetools.ups.com/security/v1/oauth/token"
    BASE = "https://onlinetools.ups.com/api"

    def __init__(self, client_id: Optional[str] = None, secret: Optional[str] = None, account: Optional[str] = None):
        self.client_id = client_id or os.getenv("UPS_CLIENT_ID", "")
        self.secret = secret or os.getenv("UPS_CLIENT_SECRET", "")
        self.account = account or os.getenv("UPS_ACCOUNT_NUMBER", "")
        self._token: Optional[str] = None

    def _auth(self) -> str:
        if self._token:
            return self._token
        resp = requests.post(
            self.AUTH_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials", "client_id": self.client_id, "client_secret": self.secret},
            timeout=30,
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._auth()}", "Content-Type": "application/json",
                "transId": "agency", "transactionSrc": "stratum-ai"}

    def track(self, tracking_number: str) -> dict:
        resp = requests.get(
            f"{self.BASE}/track/v1/details/{tracking_number}",
            headers=self._headers(),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def rate(self, payload: dict) -> dict:
        resp = requests.post(f"{self.BASE}/rating/v1/Shop", headers=self._headers(), json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
