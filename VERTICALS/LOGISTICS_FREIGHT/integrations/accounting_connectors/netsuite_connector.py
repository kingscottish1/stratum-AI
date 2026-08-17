"""
NetSuite connector — AP automation via SuiteTalk REST Web Services.

Env vars: NETSUITE_ACCOUNT_ID, NETSUITE_CONSUMER_KEY, NETSUITE_CONSUMER_SECRET,
          NETSUITE_TOKEN_ID, NETSUITE_TOKEN_SECRET
"""
import os
from typing import Optional

import requests


class NetSuiteConnector:
    def __init__(self, account_id: Optional[str] = None):
        self.account_id = account_id or os.getenv("NETSUITE_ACCOUNT_ID", "")
        self.base = f"https://{self.account_id}.suitetalk.api.netsuite.com/services/rest"

    def _headers(self) -> dict:
        # OAuth1 signature via requests-oauthlib in production
        return {"Authorization": "OAuth ...", "Content-Type": "application/json", "Prefer": "transient"}

    def _call(self, method: str, path: str, **kwargs) -> dict:
        resp = requests.request(method, f"{self.base}{path}", headers=self._headers(), timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def mark_ready_to_pay(self, bill_id: str, reference: str = "") -> None:
        self._call("POST", f"/record/v1/vendorBill/{bill_id}/!approve")

    def hold_payment(self, bill_id: str, reasons: list[str]) -> None:
        self._call("PATCH", f"/record/v1/vendorBill/{bill_id}",
                   json={"memo": "HELD BY AI: " + "; ".join(reasons)})

    def submit_dispute(self, dispute: dict) -> None:
        self._call("POST", "/record/v1/vendorCredit", json={
            "createdDate": dispute.get("date", ""),
            "memo": dispute.get("reason", ""),
            "total": dispute.get("dispute_amount", 0),
        })

    def invoices_in_period(self, period: str) -> list[dict]:
        return self._call("GET", "/record/v1/vendorBill", params={"q": f"trandate AFTER {period}"}).get("items", [])
