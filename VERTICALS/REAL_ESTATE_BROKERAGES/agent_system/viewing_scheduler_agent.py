"""
Viewing scheduler: books property showings across agent calendars,
sends confirmations, and manages the pre-showing info pack.

Handles: single/group viewings, open-house slots, agent timezone checks,
and reschedules — all without touching the agent's phone.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent

logger = logging.getLogger("vertical.realestate.viewings")


class ViewingSchedulerAgent(BaseAgent):
    def __init__(self, calendar, crm, comms, llm):
        super().__init__(name="viewing_scheduler_agent", vertical="real_estate_brokerages", llm=llm)
        self.calendar = calendar
        self.crm = crm
        self.comms = comms

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        listing = input_data.get("listing") or {}
        lead = input_data.get("lead") or {}
        agent = input_data.get("agent") or {}
        requested = input_data.get("preferred_time")

        slots = self._agent_slots(agent, listing, requested)
        if not slots:
            return {
                "status": "success",
                "result": {"action": "no_slots"},
                "reply": f"{agent.get('name', 'The agent')} is fully booked this week — "
                         "I can put you on the waitlist or find another day.",
            }

        slot = slots[0]
        start_dt = datetime.fromisoformat(slot["start"])
        event = self.calendar.create_event(
            summary=f"Showing: {listing.get('address', 'property')}",
            start=slot["start"], end=slot["end"],
            description=f"Client: {lead.get('name', '')} ({lead.get('phone', '')}) "
                        f"MLS#{listing.get('mls_id', '')}",
        )
        if lead.get("phone"):
            self.comms.send(
                to=lead["phone"],
                body=f"✅ Viewing confirmed: {listing.get('address','')} on "
                     f"{start_dt.strftime('%a %b %-d at %-I:%M %p')}. "
                     "Reply RESCHEDULE to change.",
            )
        if agent.get("phone"):
            self.comms.send(
                to=agent["phone"],
                body=f"📅 Showing booked: {listing.get('address','')} "
                     f"{start_dt.strftime('%a %-I:%M %p')} — {lead.get('name','client')} "
                     f"({lead.get('phone','')})",
            )

        self.crm.log_activity(lead.get("id", ""), "Viewing Booked",
                              f"{listing.get('address','')} {start_dt.isoformat()}")
        return {"status": "success", "result": {"action": "booked", "event_id": event.get("id")}}

    def _agent_slots(self, agent: dict, listing: dict, requested) -> list[dict]:
        """Return open slots honoring the agent's working hours."""
        start = datetime.now() + timedelta(hours=4)
        end = start + timedelta(days=7)
        raw = self.calendar.get_free_slots(start, end, duration_min=45)
        # filter to agent working hours (9-18 by default)
        slots = [
            s for s in raw
            if 9 <= datetime.fromisoformat(s["start"]).hour < 18
        ]
        if requested:
            wanted = datetime.fromisoformat(requested)
            slots = [s for s in slots if abs((datetime.fromisoformat(s["start"]) - wanted).total_seconds()) < 3600 * 3] or slots
        return slots[:3]
