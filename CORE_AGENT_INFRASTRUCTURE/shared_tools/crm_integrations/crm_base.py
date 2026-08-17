"""
CRMInterface: common contract implemented by every CRM connector.

Agents should depend on this interface, never on a concrete CRM,
so swapping Salesforce <-> HubSpot is a config change, not a code change.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional


class CRMInterface(ABC):
    """Minimal CRM surface used by agency agents."""

    @abstractmethod
    def get_contact(self, contact_id: str) -> Optional[dict]: ...

    @abstractmethod
    def find_contact(self, email: Optional[str] = None, phone: Optional[str] = None) -> Optional[dict]: ...

    @abstractmethod
    def create_contact(self, data: dict) -> str:
        """Create a contact; returns the new contact id."""

    @abstractmethod
    def update_contact(self, contact_id: str, data: dict) -> None: ...

    @abstractmethod
    def log_activity(self, contact_id: str, activity_type: str, note: str) -> None: ...

    @abstractmethod
    def create_deal(self, contact_id: str, title: str, stage: str, value: float) -> str: ...

    def healthcheck(self) -> dict:
        """Return {'ok': bool, 'detail': str} for monitoring."""
        return {"ok": True, "detail": f"{self.__class__.__name__} reachable"}
