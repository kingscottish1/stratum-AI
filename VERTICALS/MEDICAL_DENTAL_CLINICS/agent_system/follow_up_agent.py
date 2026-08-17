"""
Follow-up agent: chases missed appointments, unscheduled treatment plans,
and outstanding recall lists — automatically, with human-friendly copy.

Triggers:
  - no-show after an appointment (reschedule offer)
  - treatment plan not booked within X days
  - recall list patients due for checkup
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent

logger = logging.getLogger("vertical.clinic.followup")


class FollowUpAgent(BaseAgent):
    def __init__(self, pms, calendar, comms, llm):
        super().__init__(name="follow_up_agent", vertical="medical_dental_clinics", llm=llm)
        self.pms = pms
        self.calendar = calendar
        self.comms = comms

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        task_type = input_data.get("task_type", "no_show")
        patient = input_data.get("patient") or {}
        phone = patient.get("phone")

        handlers = {
            "no_show": self._handle_no_show,
            "treatment_plan": self._handle_treatment_plan,
            "recall": self._handle_recall,
        }
        result = handlers.get(task_type, self._handle_no_show)(patient, input_data.get("context", {}))

        if phone and result.get("reply"):
            self.comms.send(to=phone, body=result["reply"])
        return {"status": "success", "result": {**result, "patient_id": patient.get("id")}}

    # -- handlers -------------------------------------------------------------
    def _handle_no_show(self, patient: dict, ctx: dict) -> dict:
        missed = ctx.get("appointment", {})
        reschedule = self._offer_slots(patient, missed)
        return {
            "action": "reschedule_offer",
            "reply": (
                f"Hi {patient.get('first_name', 'there')} — we missed you at your "
                f"{missed.get('service', 'appointment')} on {missed.get('date', 'the other day')}. "
                "No worries, life happens! Want to grab a new slot? "
                + reschedule +
                " Just reply with a number."
            ),
        }

    def _handle_treatment_plan(self, patient: dict, ctx: dict) -> dict:
        plan = ctx.get("plan", {})
        return {
            "action": "plan_followup",
            "reply": (
                f"Hi {patient.get('first_name', 'there')} — your treatment plan "
                f"({plan.get('name', '')}, est. {plan.get('estimate', '')}) is still open. "
                "Would you like to book the next step? Reply BOOK and we'll find a time."
            ),
        }

    def _handle_recall(self, patient: dict, ctx: dict) -> dict:
        return {
            "action": "recall",
            "reply": (
                f"Hi {patient.get('first_name', 'there')} — it's been 6 months since your last "
                "checkup! Your teeth miss you 😄 Reply BOOK to schedule your cleaning."
            ),
        }

    def _offer_slots(self, patient: dict, missed: dict) -> str:
        start = datetime.now() + timedelta(days=1)
        slots = self.calendar.get_free_slots(start, start + timedelta(days=7), duration_min=30)[:3]
        return " | ".join(
            f"{i + 1}) {datetime.fromisoformat(s['start']).strftime('%a %-I:%M %p')}"
            for i, s in enumerate(slots)
        )
