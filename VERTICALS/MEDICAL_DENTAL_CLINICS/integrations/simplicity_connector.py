"""
Simplicity (Open Dental) connector — practice management system.

Open Dental provides a REST API on port 9443 when enabled. This connector
targets the common Open Dental endpoints.

Env vars: OPEN_DENTAL_URL (e.g. https://clinic:9443), OPEN_DENTAL_TOKEN
"""
import os
from typing import Optional

import requests


class SimplicityConnector:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None):
        self.base_url = base_url or os.getenv("OPEN_DENTAL_URL", "")
        self.token = token or os.getenv("OPEN_DENTAL_TOKEN", "")

    def _headers(self) -> dict:
        return {"Authorization": self.token, "Content-Type": "application/json"}

    def _call(self, method: str, path: str, payload: Optional[dict] = None) -> dict:
        resp = requests.request(
            method, f"{self.base_url}{path}", headers=self._headers(),
            json=payload if payload else None, timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_patient(self, patient_id: str) -> Optional[dict]:
        return self._call("GET", f"/patients/{patient_id}")

    def create_appointment(self, patient_id: str, service: str, start: str, end: str, source: str = "ai") -> dict:
        return self._call("POST", "/appointments", {
            "patient_id": patient_id, "procedure_code": service,
            "start": start, "end": end, "source": source,
        })

    def get_appointments(self, start: str, end: str) -> list[dict]:
        return self._call("GET", f"/appointments?start={start}&end={end}")
