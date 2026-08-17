"""
Real-estate calendar sync: two-way agent calendars <-> showing events.

Uses the shared Google Calendar / Outlook connectors; adds brokerage
specifics: team calendars, listing-based event titles, buffer time.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from CORE_AGENT_INFRASTRUCTURE.shared_tools.calendar_sync.calendar_utils import merge_busy_windows

logger = logging.getLogger("vertical.realestate.calendar")


class BrokerCalendarSync:
    def __init__(self, connector, buffer_minutes: int = 15):
        self.connector = connector  # GoogleCalendarConnector or OutlookConnector
        self.buffer = buffer_minutes

    def agent_free_slots(
        self, agent: dict, start: datetime, end: datetime, duration_min: int = 45
    ) -> list[dict]:
        """Free slots across an agent's calendars, with travel buffer."""
        events = self.connector.list_events(start, end)
        busy = merge_busy_windows(events)
        # add buffer around busy windows
        busy = [(s - timedelta(minutes=self.buffer), e + timedelta(minutes=self.buffer)) for s, e in busy]

        slots, cursor = [], start
        step = timedelta(minutes=30)
        while cursor + timedelta(minutes=duration_min) <= end:
            occupied = any(s < cursor + timedelta(minutes=duration_min) and e > cursor for s, e in busy)
            hour = cursor.hour
            if not occupied and 9 <= hour < 18 and cursor.weekday() < 5:
                slots.append({"start": cursor.isoformat(),
                              "end": (cursor + timedelta(minutes=duration_min)).isoformat()})
            cursor += step
        return slots

    def book_showing(self, agent: dict, listing: dict, lead: dict, slot: dict) -> dict:
        event = self.connector.create_event(
            summary=f"Showing: {listing.get('address', 'property')}",
            start=datetime.fromisoformat(slot["start"]),
            end=datetime.fromisoformat(slot["end"]),
            description=f"Client: {lead.get('name', '')} {lead.get('phone', '')} "
                        f"MLS# {listing.get('mls_id', '')}",
            attendees=[agent.get("email")],
        )
        logger.info("showing booked agent=%s listing=%s", agent.get("name"), listing.get("mls_id"))
        return event
