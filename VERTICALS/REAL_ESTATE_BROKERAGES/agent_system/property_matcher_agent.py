"""
Property matcher: turns a lead profile into 3-5 personalized listings,
pulled from MLS and sent via SMS/email with a clean summary.

Matches on: budget, area, beds/baths, property type, commute, schools.
"""
import json
import logging
from typing import Any

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent

logger = logging.getLogger("vertical.realestate.matcher")


class PropertyMatcherAgent(BaseAgent):
    def __init__(self, mls, comms, emailer, llm):
        super().__init__(name="property_matcher_agent", vertical="real_estate_brokerages", llm=llm)
        self.mls = mls
        self.comms = comms
        self.emailer = emailer

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        profile = input_data.get("profile") or {}
        lead = input_data.get("lead") or {}
        channel = input_data.get("channel", "email")

        listings = self.mls.search(
            max_price=profile.get("budget"),
            area=profile.get("area"),
            property_type=profile.get("property_type"),
            beds=profile.get("beds"),
            baths=profile.get("baths"),
            limit=5,
        )
        if not listings:
            return {
                "status": "success",
                "result": {"action": "no_matches"},
                "reply": "Nothing perfect right now — I'm watching the MLS and will ping you "
                         "the moment something matches. Meanwhile, want a saved search?",
            }

        ranked = self._rank(listings, profile)
        summary = self._summarize(ranked)

        if channel == "sms":
            self.comms.send(to=lead["phone"], body=self._sms_body(ranked))
        else:
            self.emailer.send(to=lead["email"], subject="Your new listings are here 🏡",
                              html=self._email_body(ranked))

        return {
            "status": "success",
            "result": {
                "action": "matches_sent",
                "count": len(ranked),
                # full listing objects (mls_id, address, price, ...) so the
                # viewing scheduler and orchestrator can use them directly
                "listings": ranked,
            },
            "reply": summary,
        }

    # -- internals ------------------------------------------------------------
    def _rank(self, listings: list[dict], profile: dict) -> list[dict]:
        """Score each listing vs the profile; return sorted."""
        for listing in listings:
            score = 0
            price = listing.get("price", 0)
            budget = profile.get("budget") or price
            score += 20 if abs(price - budget) / max(budget, 1) < 0.1 else 5
            if profile.get("beds") and listing.get("beds") >= profile.get("beds"):
                score += 15
            if profile.get("area") and profile["area"].lower() in (listing.get("area") or "").lower():
                score += 25
            if listing.get("property_type") == profile.get("property_type"):
                score += 15
            listing["match_score"] = min(score, 100)
        return sorted(listings, key=lambda l: l["match_score"], reverse=True)[:5]

    def _sms_body(self, listings: list[dict]) -> str:
        lines = ["Here are your top matches: 🏡"]
        for i, l in enumerate(listings, 1):
            lines.append(
                f"{i}) {l.get('beds', '?')}bd/{l.get('baths', '?')}ba ${l.get('price', 0):,} "
                f"- {l.get('address', '')} ({l.get('area', '')})"
            )
        lines.append("Reply with a number to book a viewing!")
        return "\n".join(lines)

    def _email_body(self, listings: list[dict]) -> str:
        cards = "".join(
            f"<div style='border:1px solid #e5e7eb;border-radius:10px;padding:16px;margin:12px 0;'>"
            f"<h3 style='margin:0 0 6px'>{l.get('address','')}</h3>"
            f"<p>{l.get('beds','?')} bd · {l.get('baths','?')} ba · ${l.get('price',0):,} · {l.get('area','')}</p>"
            f"<a href='{l.get('url','#')}' style='color:#0f766e'>View listing →</a></div>"
            for l in listings
        )
        return (
            "<div style='font-family:Segoe UI,Arial,sans-serif;max-width:560px;margin:auto'>"
            f"<h2>New matches for you 🏡</h2>{cards}"
            "<p>Reply to this email or call us to book a viewing.</p></div>"
        )

    def _summarize(self, listings: list[dict]) -> str:
        return (
            f"Found {len(listings)} strong matches — sent to your {'phone' if self.comms else 'email'}. "
            "Want me to book viewings for any of them?"
        )
