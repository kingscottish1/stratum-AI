"""
Clinic orchestrator: entry point for all inbound patient messages.

Routes by intent -> specialist agent:
  booking / reschedule / cancel  -> appointment_agent
  insurance questions            -> insurance_intake_agent
  general questions              -> patient_communication_agent (or LLM reply)
  follow-up tasks                -> follow_up_agent (scheduled)
"""
import logging
from typing import Any, Optional

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent

logger = logging.getLogger("vertical.clinic.orchestrator")

INTENT_KEYWORDS = {
    # cancel/reschedule checked before book so "cancel my appointment"
    # routes correctly even though the message also contains "appointment"
    "cancel": ["cancel", "remove my appointment", "can't make it"],
    "reschedule": ["reschedule", "move my", "change my appointment", "different time"],
    "book": ["book", "schedule", "make an", "slot", "available", "when can", "appointment"],
    "insurance": ["insurance", "coverage", "claim", "deductible", "co-pay", "copay", "benefits"],
    "directions": ["address", "directions", "where are you", "parking"],
    "hours": ["open", "hours", "close"],
    "billing": ["bill", "payment", "charge", "invoice"],
}


class ClinicOrchestrator(BaseAgent):
    def __init__(self, agents: dict[str, BaseAgent], llm: Any = None):
        super().__init__(name="clinic_orchestrator", vertical="medical_dental_clinics", llm=llm)
        self.agents = agents  # {"appointment": ..., "insurance_intake": ..., ...}

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        message = (input_data.get("message") or "").lower()
        intent = self._classify(message)

        if intent == "book" or intent == "reschedule":
            agent = self.agents["appointment"]
        elif intent == "cancel":
            agent = self.agents["appointment"]
            input_data = {**input_data, "action_hint": "cancel"}
        elif intent == "insurance":
            agent = self.agents["insurance_intake"]
        else:
            agent = self.agents.get("general") or self.agents["appointment"]

        logger.info("routing intent=%s -> agent=%s", intent, agent.name)
        result = agent.execute(input_data)
        result["intent"] = intent
        return result

    def classify(self, message: str) -> str:
        """Public intent classifier used by webhook handlers."""
        return self._classify(message)

    def _classify(self, message: str) -> str:
        lowered = message.lower()
        for intent, keywords in INTENT_KEYWORDS.items():
            if any(kw in lowered for kw in keywords):
                return intent
        return "general"

    def schedule_follow_ups(self, pms, window_hours: int = 2) -> list[dict]:
        """Batch job: find no-shows / unbooked plans and dispatch follow_up_agent."""
        tasks = []
        for patient in pms.get_follow_up_candidates(window_hours=window_hours):
            result = self.agents["follow_up"].execute({
                "task_type": patient["task_type"],
                "patient": patient,
                "context": patient.get("context", {}),
            })
            tasks.append({"patient_id": patient.get("id"), "result": result["status"]})
        return tasks
