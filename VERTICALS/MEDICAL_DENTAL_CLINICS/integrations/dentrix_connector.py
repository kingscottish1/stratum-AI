"""
Dentrix (Henry Schein) connector — practice management system.

Dentrix exposes a proprietary ODBC / eServices API. This module wraps the
pieces agents need (appointment CRUD, patient lookup) behind one interface.
Implement the actual SOAP/ODBC calls per the client's Dentrix version.

Env vars: DENTRIX_ESERVICES_URL, DENTRIX_CLINIC_ID, DENTRIX_API_KEY
"""
import logging
import os
from typing import Optional

logger = logging.getLogger("vertical.clinic.dentrix")


class DentrixConnector:
    def __init__(self, clinic_id: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = os.getenv("DENTRIX_ESERVICES_URL", "")
        self.clinic_id = clinic_id or os.getenv("DENTRIX_CLINIC_ID", "")
        self.api_key = api_key or os.getenv("DENTRIX_API_KEY", "")

    def get_patient(self, patient_id: str) -> Optional[dict]:
        """Fetch a patient record."""
        # TODO: implement per your Dentrix eServices contract
        raise NotImplementedError("Implement Dentrix eServices call")

    def find_patient_by_phone(self, phone: str) -> Optional[dict]:
        raise NotImplementedError("Implement Dentrix eServices call")

    def create_appointment(self, patient_id: str, service: str, start: str, end: str, source: str = "ai") -> dict:
        raise NotImplementedError("Implement Dentrix eServices call")

    def get_appointments(self, start: str, end: str) -> list[dict]:
        raise NotImplementedError("Implement Dentrix eServices call")

    def cancel_appointment(self, appointment_id: str) -> None:
        raise NotImplementedError("Implement Dentrix eServices call")

    def save_insurance(self, patient_id: str, data: dict) -> None:
        raise NotImplementedError("Implement Dentrix eServices call")
