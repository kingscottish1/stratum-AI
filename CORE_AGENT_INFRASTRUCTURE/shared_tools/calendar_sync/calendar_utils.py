"""
Calendar helpers shared by all connectors: parsing, formatting, slot math.
"""
from datetime import datetime, timedelta


def parse_dt(value: str) -> datetime:
    """Parse ISO datetime strings produced by Google/Outlook APIs."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def format_human(start: datetime, tz_name: str = "UTC") -> str:
    """Human friendly: 'Mon, Aug 3 at 10:30 AM'."""
    tz_start = start.astimezone()
    return tz_start.strftime("%a, %b %-d at %I:%M %p")


def slots_overlap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def merge_busy_windows(events: list[dict]) -> list[tuple[datetime, datetime]]:
    """Merge overlapping busy windows into non-overlapping intervals."""
    windows = sorted(
        (parse_dt(e["start"]), parse_dt(e["end"])) for e in events if e.get("start") and e.get("end")
    )
    merged: list[tuple[datetime, datetime]] = []
    for start, end in windows:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def next_business_day(start: datetime, min_hours_ahead: int = 24) -> datetime:
    """Next weekday at least min_hours_ahead from now (used for reminders)."""
    candidate = start + timedelta(hours=min_hours_ahead)
    while candidate.weekday() >= 5:  # skip weekends
        candidate += timedelta(days=1)
    return candidate
