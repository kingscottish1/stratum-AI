"""
Clinic-specific calendar facade.

Decides between Google Calendar and the PMS calendar based on config.
Agents talk to this facade, never to connectors directly.
"""
import logging
from typing import Any, Optional

logger = logging.getLogger("vertical.clinic.calendar")


class ClinicCalendar:
    """Unified calendar interface for the clinic vertical."""

    def __init__(self, primary: Any, fallback: Any = None, mode: str = "google"):
        self.primary = primary          # GoogleCalendarConnector
        self.fallback = fallback        # PMS calendar (Dentrix/EagleSoft/Simplicity)
        self.mode = mode                # "google" | "pms" | "dual"

    def get_free_slots(self, start, end, duration_min: int = 30) -> list[dict]:
        if self.mode in ("google", "dual"):
            return self.primary.get_free_slots(start, end, duration_min)
        if self.fallback is not None:
            # PMS-based availability
            appointments = self.fallback.get_appointments(start.isoformat(), end.isoformat())
            busy = [(a["start"], a["end"]) for a in appointments]
            slots = []
            cursor = start
            while cursor + __import__("datetime").timedelta(minutes=duration_min) <= end:
                occupied = any(s < cursor + __import__("datetime").timedelta(minutes=duration_min) and e > cursor for s, e in busy)
                if not occupied:
                    slots.append({"start": cursor.isoformat(), "end": (cursor + __import__("datetime").timedelta(minutes=duration_min)).isoformat()})
                cursor += __import__("datetime").timedelta(minutes=30)
            return slots[:3]
        raise RuntimeError("No calendar backend configured")

    def create_event(self, summary: str, start, end, description: str = "", attendees: Optional[list] = None) -> dict:
        if self.mode in ("google", "dual"):
            return self.primary.create_event(summary, start, end, description, attendees)
        if self.fallback is not None:
            return self.fallback.create_appointment("", summary, start.isoformat(), end.isoformat())
        raise RuntimeError("No calendar backend configured")
