"""
Real-estate follow-up agent: sequences that keep leads warm.

- 5-min hot lead response (when agent unavailable)
- 3-day check-in on viewed properties
- 7-day offer/next-step nudge
- Monthly market snapshots for past clients
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent

logger = logging.getLogger("vertical.realestate.followup")


class FollowUpAgent(BaseAgent):
    def __init__(self, crm, mls, comms, llm):
        super().__init__(name="follow_up_agent", vertical="real_estate_brokerages", llm=llm)
        self.crm = crm
        self.mls = mls
        self.comms = comms

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        lead = input_data.get("lead") or {}
        step = input_data.get("step", "hot_lead")
        phone = lead.get("phone")

        handlers = {
            "hot_lead": self._hot_lead,
            "viewed_3d": self._viewed_3d,
            "offer_nudge": self._offer_nudge,
            "market_snapshot": self._market_snapshot,
        }
        reply = handlers.get(step, self._hot_lead)(lead, input_data.get("context", {}))
        if phone:
            self.comms.send(to=phone, body=reply)
        self.crm.log_activity(lead.get("id", ""), f"Follow-up ({step})", reply[:200])
        return {"status": "success", "result": {"step": step, "sent_to": phone}}

    def _hot_lead(self, lead: dict, ctx: dict) -> str:
        return (
            f"Hi {lead.get('first_name', 'there')}! Thanks for your interest in "
            f"{ctx.get('listing', 'the property')} — I'm lining up details now and "
            "will send you the best options within the hour. Anything specific "
            "you're looking for (schools, commute, yard)?"
        )

    def _viewed_3d(self, lead: dict, ctx: dict) -> str:
        return (
            f"Hi {lead.get('first_name', 'there')}! It's been a few days since you viewed "
            f"{ctx.get('address', 'the property')} — what did you think? I can pull "
            "comparables, run numbers, or book a second look. Just reply!"
        )

    def _offer_nudge(self, lead: dict, ctx: dict) -> str:
        return (
            f"Quick heads-up, {lead.get('first_name', 'there')}: the property at "
            f"{ctx.get('address', '')} just had another offer. If you're still "
            "interested, let's talk strategy today — I'll draft the paperwork for free."
        )

    def _market_snapshot(self, lead: dict, ctx: dict) -> str:
        area = lead.get("area", ctx.get("area", "your area"))
        return (
            f"📊 {area} market update: {ctx.get('median_price', 'n/a')} median price, "
            f"{ctx.get('days_on_market', 'n/a')} days on market, "
            f"{ctx.get('inventory', 'n/a')} active listings. Want a full report "
            "for your home value too?"
        )
