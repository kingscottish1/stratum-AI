"""
Lead qualifier: scores inbound leads in seconds and routes them to the
right agent or nurture track.

Scoring dimensions:
  - budget vs market (local price bands)
  - timeline (buying/selling intent + when)
  - financing readiness (pre-approval)
  - property type & area match
  - urgency & engagement signals (reply speed, channel)
"""
import json
import logging
from typing import Any

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent
from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.error_handling import ValidationError

logger = logging.getLogger("vertical.realestate.qualifier")

BANDS = [(">= $1.5M", "luxury"), ("$600k-$1.5M", "premium"), ("$300k-$600k", "mid"), ("< $300k", "entry")]


class LeadQualifierAgent(BaseAgent):
    def __init__(self, crm, mls, llm):
        super().__init__(name="lead_qualifier_agent", vertical="real_estate_brokerages", llm=llm)
        self.crm = crm
        self.mls = mls

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        lead = input_data.get("lead") or {}
        message = input_data.get("message", "")
        channel = input_data.get("channel", "web")

        if not lead.get("email") and not lead.get("phone"):
            raise ValidationError("Lead needs email or phone")

        profile = self._profile(message, lead)
        score = self._score(profile, lead, channel)

        outcome = self._route(score)
        contact = self.crm.find_contact(email=lead.get("email"), phone=lead.get("phone"))
        contact_id = contact["id"] if contact else self.crm.create_contact({**lead, **profile})
        self.crm.update_contact(contact_id, {"lead_score": score["total"], "lead_status": outcome["status"]})
        self.crm.log_activity(contact_id, "AI Lead Qualification",
                              json.dumps({"score": score, "profile": profile}))

        return {
            "status": "success",
            "result": {
                "contact_id": contact_id,
                "score": score,
                "tier": score["tier"],
                "profile": profile,
                **outcome,
            },
        }

    # -- internals ------------------------------------------------------------
    def _profile(self, message: str, lead: dict) -> dict:
        if self.llm is None:
            return {
                "intent": "buy" if any(w in message.lower() for w in ["buy", "looking", "interested"]) else "unknown",
                "budget_band": "unknown",
                "area": lead.get("area", ""),
                "timeline": "unknown",
            }
        prompt = (
            "Extract buyer/seller profile from this lead conversation as JSON. "
            'Keys: "intent" (buy|sell|rent|invest|unknown), "budget" (number or null), '
            '"area" (string), "timeline" (asap|1-3mo|3-6mo|6mo+|unknown), '
            '"property_type" (house|condo|townhome|multi|land|unknown), '
            '"financing" (preapproved|cash|need_mortgage|unknown).\n'
            f"Message: {message}\nLead metadata: {json.dumps(lead)}\nJSON only:"
        )
        raw = self.llm.invoke(prompt)
        content = raw.content if hasattr(raw, "content") else str(raw)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"intent": "unknown", "budget": None, "area": "", "timeline": "unknown"}

    def _score(self, profile: dict, lead: dict, channel: str = "web") -> dict:
        s = 0
        s += {"buy": 30, "sell": 25, "invest": 20, "rent": 10, "unknown": 5}.get(profile.get("intent"), 5)
        s += {"asap": 25, "1-3mo": 20, "3-6mo": 15, "6mo+": 8, "unknown": 3}.get(profile.get("timeline"), 3)
        s += {"preapproved": 25, "cash": 30, "need_mortgage": 10, "unknown": 5}.get(profile.get("financing"), 5)
        s += 10 if lead.get("area") or profile.get("area") else 0
        s += 5 if channel in ("phone", "sms") else 0  # faster reply channels
        total = min(s, 100)
        tier = "hot" if total >= 70 else ("warm" if total >= 40 else "cold")
        return {"total": total, "tier": tier, "breakdown": {"intent": s, "timeline": s, "financing": s}}

    def _route(self, score: dict) -> dict:
        if score["tier"] == "hot":
            return {"status": "hot", "action": "instant_agent_alert", "next": "property_matcher"}
        if score["tier"] == "warm":
            return {"status": "warm", "action": "nurture_sequence", "next": "follow_up"}
        return {"status": "cold", "action": "long_nurture", "next": "drip_campaign"}
