"""Regression guard: viewing booking with ISO-string slots."""
from DEMOS.mocks import MockCalendar, MockComms, MockCRM
from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.viewing_scheduler_agent import ViewingSchedulerAgent

LISTING = {"mls_id": "M1001", "address": "412 Oakwood Lane", "price": 585000,
           "beds": 3, "baths": 2, "area": "Maplewood"}
LEAD = {"id": "1", "name": "Alex Chen", "phone": "+15550102"}
AGENT = {"name": "Jennifer", "phone": "+15550199", "email": "j@broker.com"}


def test_viewing_booked_and_confirmed():
    calendar = MockCalendar()
    crm = MockCRM()
    comms = MockComms(silent=True)
    scheduler = ViewingSchedulerAgent(calendar, crm, comms, llm=None)

    result = scheduler.execute({"listing": LISTING, "lead": LEAD, "agent": AGENT})
    assert result["status"] == "success"
    assert result["result"]["action"] == "booked"
    assert calendar.events
    assert len(comms.sent) == 2  # client + agent notified
    assert crm.activities
