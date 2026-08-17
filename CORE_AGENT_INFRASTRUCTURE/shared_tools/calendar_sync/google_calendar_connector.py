"""
Google Calendar connector (service-account based).

Env vars required:
  GOOGLE_SERVICE_ACCOUNT_FILE  path to the JSON service-account key
  GOOGLE_CALENDAR_ID           calendar id (e.g. x@group.calendar.google.com)
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
except ImportError:  # pragma: no cover
    service_account = build = None

SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendarConnector:
    def __init__(self, calendar_id: Optional[str] = None, service_account_file: Optional[str] = None):
        if build is None:
            raise RuntimeError("google-api-python-client not installed")
        self.calendar_id = calendar_id or os.getenv("GOOGLE_CALENDAR_ID", "primary")
        sa_file = service_account_file or os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "")
        if not sa_file:
            raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_FILE is not set")
        creds = service_account.Credentials.from_service_account_file(sa_file, scopes=SCOPES)
        self.service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    # -- read ----------------------------------------------------------------
    def list_events(self, time_min: datetime, time_max: datetime) -> list[dict]:
        result = (
            self.service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return result.get("items", [])

    def get_free_slots(
        self, start: datetime, end: datetime, duration_min: int = 30
    ) -> list[dict]:
        """Return available time slots between start and end."""
        events = self.list_events(start, end)
        busy: list[tuple[datetime, datetime]] = []
        for ev in events:
            s = ev["start"].get("dateTime") or ev["start"].get("date")
            e = ev["end"].get("dateTime") or ev["end"].get("date")
            busy.append((datetime.fromisoformat(s), datetime.fromisoformat(e)))

        slots, cursor = [], start
        while cursor + timedelta(minutes=duration_min) <= end:
            occupied = any(s < cursor + timedelta(minutes=duration_min) and e > cursor for s, e in busy)
            if not occupied:
                slots.append({"start": cursor.isoformat(), "end": (cursor + timedelta(minutes=duration_min)).isoformat()})
            cursor += timedelta(minutes=30)
        return slots

    # -- write ---------------------------------------------------------------
    def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        description: str = "",
        attendees: Optional[list[str]] = None,
    ) -> dict:
        body: dict[str, Any] = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start.isoformat(), "timeZone": str(start.tzinfo or timezone.utc)},
            "end": {"dateTime": end.isoformat(), "timeZone": str(end.tzinfo or timezone.utc)},
        }
        if attendees:
            body["attendees"] = [{"email": a} for a in attendees]
        return self.service.events().insert(calendarId=self.calendar_id, body=body).execute()

    def cancel_event(self, event_id: str) -> None:
        self.service.events().delete(calendarId=self.calendar_id, eventId=event_id).execute()
