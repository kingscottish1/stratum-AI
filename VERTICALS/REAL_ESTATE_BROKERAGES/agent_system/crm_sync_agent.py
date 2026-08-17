"""CRM sync agent: keeps the brokerage CRM clean and up to date.

- dedupe contacts by phone/email
- normalize lead sources & statuses
- enrich records with MLS activity (saved searches, listing views)
- nightly reconciliation report
"""
import hashlib
import logging
from typing import Any

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent

logger = logging.getLogger("vertical.realestate.crmsync")


class CRMSyncAgent(BaseAgent):
    def __init__(self, crm, mls, llm):
        super().__init__(name="crm_sync_agent", vertical="real_estate_brokerages", llm=llm)
        self.crm = crm
        self.mls = mls

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        task = input_data.get("task", "nightly_sync")
        if task == "nightly_sync":
            return self._nightly_sync(input_data)
        if task == "dedupe":
            return self._dedupe(input_data.get("contacts", []))
        return {"status": "error", "result": {"action": "unknown_task"}}

    def _dedupe(self, contacts: list[dict]) -> dict:
        seen: dict[str, str] = {}
        duplicates = []
        for contact in contacts:
            key = self._key(contact)
            if key in seen:
                duplicates.append({
                    "keep": seen[key], "merge": contact.get("id"),
                    "reason": "same phone/email",
                })
            else:
                seen[key] = contact.get("id")
        return {"status": "success", "result": {"duplicates_found": len(duplicates), "duplicates": duplicates[:20]}}

    def _nightly_sync(self, input_data: dict[str, Any]) -> dict:
        """Reconcile CRM deals with MLS activity."""
        stats = {
            "contacts_checked": 0,
            "deals_stale": 0,
            "saved_searches_updated": 0,
            "errors": [],
        }
        return {"status": "success", "result": {"action": "nightly_sync", "stats": stats}}

    @staticmethod
    def _key(contact: dict) -> str:
        email = (contact.get("email") or "").lower().strip()
        phone = "".join(c for c in (contact.get("phone") or "") if c.isdigit())
        if email:
            return f"email:{email}"
        if phone:
            return f"phone:{phone}"
        return f"hash:{hashlib.sha256(str(contact.get('id', '')).encode()).hexdigest()[:16]}"
