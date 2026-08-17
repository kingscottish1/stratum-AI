from datetime import datetime, timedelta

from CORE_AGENT_INFRASTRUCTURE.shared_tools.calendar_sync.calendar_utils import (
    merge_busy_windows,
    next_business_day,
    parse_dt,
)


def test_parse_dt():
    assert parse_dt("2026-08-03T10:00:00Z").hour == 10


def test_merge_busy_windows():
    events = [
        {"start": "2026-08-03T09:00:00", "end": "2026-08-03T10:00:00"},
        {"start": "2026-08-03T09:30:00", "end": "2026-08-03T11:00:00"},
        {"start": "2026-08-03T14:00:00", "end": "2026-08-03T15:00:00"},
    ]
    merged = merge_busy_windows(events)
    assert len(merged) == 2
    assert merged[0] == (parse_dt("2026-08-03T09:00:00"), parse_dt("2026-08-03T11:00:00"))


def test_next_business_day():
    # Friday night + 2h lands on Saturday -> rolls to Monday
    friday_late = datetime(2026, 8, 7, 23, 0)
    result = next_business_day(friday_late, min_hours_ahead=2)
    assert result.weekday() == 0
    assert result.date().isoformat() == "2026-08-10"


def test_next_business_day_stays_on_weekday():
    thursday = datetime(2026, 8, 6, 9, 0)
    result = next_business_day(thursday, min_hours_ahead=1)
    assert result.weekday() == 3  # still Thursday
    assert result.date().isoformat() == "2026-08-06"
