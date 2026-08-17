"""
Appointment booking agent for medical/dental clinics.

Handles the full booking loop over SMS/WhatsApp/webchat:
  1. parse requested service + preferred times
  2. check real calendar availability (Google Calendar / PMS)
  3. book the slot, create the patient record if new
  4. send confirmation with cancellation/reschedule options
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent
from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.error_handling import (
    HandoffRequired,
    ToolError,
)

logger = logging.getLogger("vertical.clinic.appointment")

SERVICES = [
    "cleaning", "checkup", "filling", "root canal", "extraction",
    "orthodontics", "whitening", "new patient exam",
]


class AppointmentAgent(BaseAgent):
    def __init__(self, calendar, pms, comms, llm):
        super().__init__(name="appointment_agent", vertical="medical_dental_clinics", llm=llm)
        self.calendar = calendar    # GoogleCalendarConnector or PMS calendar
        self.pms = pms              # practice management system connector
        self.comms = comms          # TwilioSMS / WhatsAppConnector

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        message = input_data.get("message", "")
        patient = input_data.get("patient") or {}
        channel = input_data.get("channel", "sms")
        phone = patient.get("phone") or input_data.get("reply_to")

        # Cancellation path: find the next upcoming event and free the slot
        if input_data.get("action_hint") == "cancel":
            upcoming = self.calendar.list_events(datetime.now(), datetime.now() + timedelta(days=30))
            if upcoming:
                event = upcoming[0]
                self.calendar.cancel_event(event.get("id"))
                try:
                    self.pms.cancel_appointment(patient_id=patient.get("id"), start=event.get("start"))
                except Exception:  # noqa: BLE001
                    logger.warning("PMS cancel sync failed for %s", patient.get("id"))
                reply = ("You're all set — your appointment has been cancelled. "
                         "Want to book a new one? Just say the word.")
            else:
                reply = "I don't see an upcoming appointment to cancel. Want to book one?"
            if phone:
                self.comms.send(to=phone, body=reply)
            return {
                "status": "success",
                "result": {"action": "cancelled" if upcoming else "nothing_to_cancel"},
                "reply": reply,
            }

        details = self._extract_details(message, patient)
        if not details.get("service"):
            raise HandoffRequired("Could not determine requested service")

        # 1. Availability
        slots = self._find_slots(details, patient)
        if not slots:
            return {
                "status": "success",
                "result": {"action": "ask_alternatives"},
                "reply": "The requested time isn't available. Would any of these work: "
                         + self._format_slots(slots_alt := self._find_slots(details, patient, alt=True))
                         + "? Reply with a number to book.",
            }

        # 2. Book
        selected = slots[0]
        event = self.calendar.create_event(
            summary=f"{details['service'].title()} - {patient.get('name', 'Patient')}",
            start=selected["start"],
            end=selected["end"],
            description=f"Booked by AI agent. Phone: {phone}",
        )

        # 3. Record in PMS
        try:
            self.pms.create_appointment(
                patient_id=patient.get("id"),
                service=details["service"],
                start=selected["start"],
                end=selected["end"],
                source=f"ai_{channel}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("PMS sync failed, calendar booked anyway: %s", exc)

        # 4. Confirm
        start_dt = datetime.fromisoformat(selected["start"])
        confirm = (
            f"✅ Confirmed! {details['service'].title()} on "
            f"{start_dt.strftime('%a %b %-d at %-I:%M %p')}. "
            "Reply CANCEL or RESCHEDULE anytime. We'll text you a reminder 24h before."
        )
        if phone:
            self.comms.send(to=phone, body=confirm)

        return {
            "status": "success",
            "result": {"action": "booked", "event_id": event.get("id")},
            "reply": confirm,
        }

    # -- internals ------------------------------------------------------------
    def _extract_details(self, message: str, patient: dict) -> dict:
        """Extract service + preferred date/time. Uses LLM when available."""
        service = next((s for s in SERVICES if s.lower() in message.lower()), None)
        details = {"service": service}

        if self.llm is not None:
            prompt = (
                "Extract appointment details from this patient message as JSON. "
                'Keys: "service", "preferred_date" (ISO), "preferred_time" (HH:MM), "urgency".\n'
                f"Available services: {json.dumps(SERVICES)}\nMessage: {message}\nJSON only:"
            )
            try:
                raw = self.llm.invoke(prompt)
                content = raw.content if hasattr(raw, "content") else str(raw)
                details.update({k: v for k, v in json.loads(content).items() if v})
            except Exception:  # noqa: BLE001
                logger.warning("LLM extraction failed, using regex fallback")
        return details

    def _find_slots(self, details: dict, patient: dict, alt: bool = False) -> list[dict]:
        """Find the next N open slots for the service duration."""
        start = datetime.now() + timedelta(days=1 if alt else 0)
        end = start + timedelta(days=7)
        duration = 60 if details.get("service") == "new patient exam" else 30
        return self.calendar.get_free_slots(start, end, duration_min=duration)[:3]

    @staticmethod
    def _format_slots(slots: list[dict]) -> str:
        return " | ".join(
            f"{i + 1}) {datetime.fromisoformat(s['start']).strftime('%a %-I:%M %p')}"
            for i, s in enumerate(slots)
        )
