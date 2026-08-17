"""
Salesforce connector (simple-salesforce).

Env vars: SALESFORCE_USERNAME, SALESFORCE_PASSWORD, SALESFORCE_SECURITY_TOKEN,
          SALESFORCE_DOMAIN (login|test)
"""
import os
from typing import Optional

try:
    from simple_salesforce import Salesforce
except ImportError:  # pragma: no cover
    Salesforce = None

from .crm_base import CRMInterface


class SalesforceConnector(CRMInterface):
    def __init__(self):
        if Salesforce is None:
            raise RuntimeError("simple-salesforce not installed")
        self.sf = Salesforce(
            username=os.getenv("SALESFORCE_USERNAME", ""),
            password=os.getenv("SALESFORCE_PASSWORD", ""),
            security_token=os.getenv("SALESFORCE_SECURITY_TOKEN", ""),
            domain=os.getenv("SALESFORCE_DOMAIN", "login"),
        )

    def get_contact(self, contact_id: str) -> Optional[dict]:
        result = self.sf.Contact.get(contact_id)
        return result if result else None

    def find_contact(self, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[dict]:
        conditions = []
        if email:
            conditions.append(f"Email = '{email}'")
        if phone:
            conditions.append(f"Phone = '{phone}'")
        if not conditions:
            return None
        query = f"SELECT Id, FirstName, LastName, Email, Phone FROM Contact WHERE {' OR '.join(conditions)} LIMIT 1"
        records = self.sf.query(query).get("records", [])
        return records[0] if records else None

    def create_contact(self, data: dict) -> str:
        result = self.sf.Contact.create(data)
        return result["id"]

    def update_contact(self, contact_id: str, data: dict) -> None:
        self.sf.Contact.update(contact_id, data)

    def log_activity(self, contact_id: str, activity_type: str, note: str) -> None:
        self.sf.Task.create({
            "WhoId": contact_id,
            "Subject": activity_type,
            "Description": note,
            "Status": "Completed",
        })

    def create_deal(self, contact_id: str, title: str, stage: str, value: float) -> str:
        result = self.sf.Opportunity.create({
            "Name": title,
            "StageName": stage,
            "Amount": value,
            "AccountId": contact_id,
        })
        return result["id"]
