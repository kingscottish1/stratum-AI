"""
Insurance eligibility verification via a clearinghouse API
(e.g. Stedi, Claim.MD, or the client's existing vendor).

Env vars: INSURANCE_API_URL, INSURANCE_API_KEY, INSURANCE_VENDOR
"""
import os
import logging
from typing import Optional

import requests

logger = logging.getLogger("vertical.clinic.insurance_api")


class InsuranceVerificationAPI:
    def __init__(self, vendor: Optional[str] = None):
        self.vendor = vendor or os.getenv("INSURANCE_VENDOR", "stedi")
        self.api_url = os.getenv("INSURANCE_API_URL", "")
        self.api_key = os.getenv("INSURANCE_API_KEY", "")

    def verify(self, carrier: str, member_id: str, plan_name: str, dob: str) -> dict:
        """Submit an eligibility check; return coverage summary.

        Implementations vary by vendor. Contract for agents:
        {
          "status": "active"|"inactive"|"unknown",
          "plan": str, "effective_date": str, "deductible": float,
          "copay_cleaning": float, "copay_exam": float,
          "annual_maximum": float, "notes": str
        }
        """
        if self.vendor == "mock":
            # Development stub so the whole flow is testable without a vendor
            return {
                "status": "active",
                "plan": plan_name or f"{carrier} PPO",
                "effective_date": "2025-01-01",
                "deductible": 50.0,
                "copay_cleaning": 0.0,
                "copay_exam": 25.0,
                "annual_maximum": 1500.0,
                "notes": "MOCK DATA - replace with real clearinghouse response",
            }

        resp = requests.post(
            f"{self.api_url}/eligibility",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "carrier": carrier,
                "member_id": member_id,
                "plan_name": plan_name,
                "date_of_birth": dob,
            },
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()
