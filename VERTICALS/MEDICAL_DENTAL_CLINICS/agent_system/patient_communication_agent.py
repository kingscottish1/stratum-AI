"""
Patient communication agent: reminders, confirmations, reschedules and
post-visit messages. Uses the clinic's template files (templates/*.txt,
templates/*.html) so the clinic owner controls the wording.

Scheduling:
  - 48h reminder (SMS + email)
  - 24h reminder (SMS)
  - 2h nudge if still unconfirmed
  - post-visit thank-you + review request (24h after)
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent

logger = logging.getLogger("vertical.clinic.comms")

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"


class PatientCommunicationAgent(BaseAgent):
    def __init__(self, calendar, comms, emailer, llm):
        super().__init__(name="patient_communication_agent", vertical="medical_dental_clinics", llm=llm)
        self.calendar = calendar
        self.comms = comms
        self.emailer = emailer

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        task = input_data.get("task", "reminder")
        appointment = input_data.get("appointment", {})
        patient = input_data.get("patient") or {}
        phone = patient.get("phone")
        email = patient.get("email")
        appt_time = appointment.get("start")

        if task == "reminder_48h":
            body = self._render("sms_appointment_reminder.txt", **self._vars(patient, appointment, "48h"))
            if phone:
                self.comms.send(to=phone, body=body)
            if email:
                self.emailer.send(to=email, subject="Your appointment is coming up",
                                  html=self._render("email_intake_form.html", **self._vars(patient, appointment)))
            return {"status": "success", "result": {"sent_to": [p for p in (phone, email) if p]}}

        if task == "reminder_24h":
            body = self._render("sms_appointment_reminder.txt", **self._vars(patient, appointment, "24h"))
            if phone:
                self.comms.send(to=phone, body=body)
            return {"status": "success", "result": {"sent_to": phone}}

        if task == "confirmation":
            body = (
                f"✅ Confirmed: {appointment.get('service', 'your appointment')} "
                f"on {self._fmt(appt_time)}. Reply RESCHEDULE to change it."
            )
            if phone:
                self.comms.send(to=phone, body=body)
            return {"status": "success", "result": {"sent_to": phone}}

        if task == "post_visit":
            body = (
                f"Hi {patient.get('first_name', 'there')}! Thanks for visiting "
                f"{appointment.get('clinic_name', 'our clinic')}. We'd love your feedback: "
                "reply with a rating 1-5, or mention our Google listing if you'd like to leave a review."
            )
            if phone:
                self.comms.send(to=phone, body=body)
            return {"status": "success", "result": {"sent_to": phone}}

        return {"status": "error", "result": {"action": "unknown_task", "task": task}}

    # -- helpers --------------------------------------------------------------
    @staticmethod
    def _fmt(value) -> str:
        return datetime.fromisoformat(value).strftime("%a %b %-d at %-I:%M %p") if value else "TBD"

    @staticmethod
    def _vars(patient: dict, appointment: dict, horizon: str = "") -> dict:
        return {
            "first_name": patient.get("first_name", "there"),
            "clinic_name": appointment.get("clinic_name", "our clinic"),
            "service": appointment.get("service", "appointment"),
            "date_time": PatientCommunicationAgent._fmt(appointment.get("start")),
            "horizon": horizon,
            "address": appointment.get("address", ""),
            "phone": appointment.get("clinic_phone", ""),
        }

    def _render(self, filename: str, **kwargs: Any) -> str:
        template = (TEMPLATE_DIR / filename).read_text(encoding="utf-8")
        for key, value in kwargs.items():
            template = template.replace("{{" + key + "}}", str(value))
        return template
