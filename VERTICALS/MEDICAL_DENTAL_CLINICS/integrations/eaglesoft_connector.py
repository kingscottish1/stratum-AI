"""
EagleSoft (Patterson) connector — practice management system.

EagleSoft has a proprietary SDK; wrap the client's available surface
(REST bridge, DB views, or file export) behind this interface.

Env vars: EAGLESOFT_API_URL, EAGLESOFT_API_KEY
"""
import os
from typing import Optional

import requests


class EagleSoftConnector:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or os.getenv("EAGLESOFT_API_URL", "")
        self.api_key = api_key or os.getenv("EAGLESOFT_API_KEY", "")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _call(self, method: str, path: str, payload: Optional[dict] = None) -> dict:
        resp = requests.request(
            method, f"{self.base_url}{path}", headers=self._headers(),
            json=payload if payload else None, timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_patient(self, patient_id: str) -> Optional[dict]:
        return self._call("GET", f"/patients/{patient_id}")

    def find_patient_by_phone(self, phone: str) -> Optional[dict]:
        return self._call("GET", f"/patients?phone={phone}")

    def create_appointment(self, patient_id: str, service: str, start: str, end: str, source: str = "ai") -> dict:
        return self._call("POST", "/appointments", {
            "patient_id": patient_id, "service": service,
            "start": start, "end": end, "source": source,
        })

    def get_appointments(self, start: str, end: str) -> list[dict]:
        return self._call("GET", f"/appointments?start={start}&end={end}")

    def cancel_appointment(self, appointment_id: str) -> None:
        self._call("DELETE", f"/appointments/{appointment_id}")
