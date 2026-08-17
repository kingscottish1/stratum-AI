"""
Regression guard: booking/cancellation must work with ISO-string slots
(the format real calendar connectors return).
"""
from datetime import datetime

from DEMOS.mocks import FakeLLM, MockCalendar, MockComms, MockPMS
from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.appointment_agent import AppointmentAgent

PATIENT = {"id": "p-1", "name": "Jamie Rivera", "first_name": "Jamie",
           "phone": "+15550101", "email": "jamie@example.com"}


def test_booking_confirms_with_string_slots():
    calendar = MockCalendar()
    pms = MockPMS()
    comms = MockComms(silent=True)
    agent = AppointmentAgent(calendar, pms, comms, llm=FakeLLM())

    result = agent.execute({"message": "Book a cleaning", "patient": PATIENT, "channel": "sms"})
    assert result["status"] == "success"
    assert "Confirmed!" in result.get("reply", "")
    assert calendar.events  # event created
    assert pms.appointments  # PMS record created
    assert comms.sent  # confirmation SMS sent


def test_cancellation_frees_slot():
    calendar = MockCalendar()
    pms = MockPMS()
    comms = MockComms(silent=True)
    agent = AppointmentAgent(calendar, pms, comms, llm=FakeLLM())

    agent.execute({"message": "Book a cleaning", "patient": PATIENT, "channel": "sms"})
    assert len(calendar.events) == 1

    result = agent.execute({"message": "cancel", "action_hint": "cancel",
                            "patient": PATIENT, "channel": "sms"})
    assert result["status"] == "success"
    assert result["result"]["action"] == "cancelled"
    assert calendar.events == []  # slot freed
