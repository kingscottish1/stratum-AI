"""
QuickBooks Online connector — invoices, bills, payments.

Env vars: QB_CLIENT_ID, QB_CLIENT_SECRET, QB_REALM_ID, QB_ACCESS_TOKEN,
          QB_REFRESH_TOKEN
"""
import os
from typing import Optional

import requests


class QuickBooksConnector:
    BASE = "https://quickbooks.api.intuit.com/v3/company"

    def __init__(self, realm_id: Optional[str] = None, access_token: Optional[str] = None):
        self.realm_id = realm_id or os.getenv("QB_REALM_ID", "")
        self.access_token = access_token or os.getenv("QB_ACCESS_TOKEN", "")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _call(self, method: str, path: str, **kwargs) -> dict:
        resp = requests.request(method, f"{self.BASE}/{self.realm_id}{path}", headers=self._headers(), timeout=30, **kwargs)
        resp.raise_for_status()
        return resp.json()

    def mark_ready_to_pay(self, bill_id: str, reference: str = "") -> None:
        self._call("POST", f"/bill/{bill_id}", json={"Id": bill_id, "sparse": True})

    def hold_payment(self, bill_id: str, reasons: list[str]) -> None:
        # attach a note so the dispute is documented for AP staff
        self._call("POST", f"/bill/{bill_id}", json={
            "Id": bill_id, "sparse": True,
            "PrivateNote": "HELD BY AI: " + "; ".join(reasons),
        })

    def submit_dispute(self, dispute: dict) -> None:
        # QBO has no native dispute object; log as vendor credit memo request
        self._call("POST", "/creditmemo", json={
            "TxnDate": dispute.get("date", ""),
            "Line": [{"Amount": dispute.get("dispute_amount", 0),
                      "DetailType": "AccountBasedExpenseLineDetail"}],
        })

    def request_credit(self, credit: dict) -> None:
        self._call("POST", "/vendorcredit", json={"Line": [{"Amount": credit.get("credit_amount", 0)}]})

    def invoices_in_period(self, period: str) -> list[dict]:
        return self._call("GET", "/query", params={"query": f"SELECT * FROM Bill WHERE TxnDate >= '{period}'"}).get("QueryResponse", {}).get("Bill", [])
