"""
Insurance intake agent: collects and validates patient insurance details
before the appointment so the front desk never chases paperwork.

Flow: ask for carrier -> member id -> group/plan -> DOB -> verify via
insurance API (or queue for manual verification) -> store in PMS.
"""
import logging
from typing import Any

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent
from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.error_handling import HandoffRequired

logger = logging.getLogger("vertical.clinic.insurance")

REQUIRED_FIELDS = [
    ("carrier", "What insurance company are you with? (e.g. Delta Dental, Cigna)"),
    ("member_id", "What's your member ID? (it's on the front of your card)"),
    ("plan_name", "What's the plan name or group number?"),
    ("dob", "What's your date of birth? (MM/DD/YYYY)"),
]


class InsuranceIntakeAgent(BaseAgent):
    def __init__(self, pms, verification_api, comms, llm):
        super().__init__(name="insurance_intake_agent", vertical="medical_dental_clinics", llm=llm)
        self.pms = pms
        self.verification_api = verification_api
        self.comms = comms

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        patient = input_data.get("patient") or {}
        message = input_data.get("message", "")
        session = input_data.get("session") or {}

        # Merge previously collected fields
        collected = dict(session.get("insurance", {}))
        collected.update(self._parse_answer(message, collected))

        missing = [f for f, _ in REQUIRED_FIELDS if not collected.get(f)]
        if missing:
            field, prompt = next((f, p) for f, p in REQUIRED_FIELDS if f in missing)
            return {
                "status": "success",
                "result": {"action": "ask", "next_field": field, "collected": collected},
                "reply": prompt,
                "session": {"insurance": collected},
            }

        # All fields collected -> verify
        try:
            verification = self.verification_api.verify(
                carrier=collected["carrier"],
                member_id=collected["member_id"],
                plan_name=collected.get("plan_name", ""),
                dob=collected["dob"],
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Insurance verification failed, queueing manual: %s", exc)
            self.pms.queue_insurance_verification(patient.get("id"), collected)
            return {
                "status": "success",
                "result": {"action": "queued_manual_verification"},
                "reply": "Thanks! We've noted your insurance details and will confirm "
                         "coverage before your visit. Anything else I can help with?",
            }

        self.pms.save_insurance(patient.get("id"), {**collected, "verified": verification})
        reply = (
            f"Great news — your {collected['carrier']} plan is verified for this visit. "
            "We'll handle the claim submission. See you at your appointment!"
        )
        if patient.get("phone"):
            self.comms.send(to=patient["phone"], body=reply)
        return {"status": "success", "result": {"action": "verified"}, "reply": reply}

    def _parse_answer(self, message: str, collected: dict) -> dict:
        """Route a free-text answer to the next unanswered field."""
        for field, _ in REQUIRED_FIELDS:
            if not collected.get(field):
                return {field: message.strip()}
        return {}
