"""
Brokerage orchestrator: routes every inbound lead through the pipeline.

  inbound -> qualify -> (hot: alert agent + match properties + schedule)
                    -> (warm: nurture + property alerts)
                    -> (cold: drip)

Also exposes the nightly batch jobs (CRM sync, follow-up queues).
"""
import logging
from typing import Any

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent

logger = logging.getLogger("vertical.realestate.orchestrator")


class BrokerageOrchestrator(BaseAgent):
    def __init__(self, agents: dict[str, BaseAgent], llm: Any = None):
        super().__init__(name="brokerage_orchestrator", vertical="real_estate_brokerages", llm=llm)
        self.agents = agents  # {"qualifier":..., "matcher":..., "viewings":..., "follow_up":..., "crm_sync":...}

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        pipeline = input_data.get("pipeline", "inbound_lead")

        if pipeline == "inbound_lead":
            return self._inbound_lead(input_data)
        if pipeline == "nightly":
            return self._nightly(input_data)
        if pipeline == "follow_up":
            return self.agents["follow_up"].execute(input_data)
        return {"status": "error", "result": {"action": "unknown_pipeline"}}

    def _inbound_lead(self, input_data: dict) -> dict:
        """Full inbound flow: qualify -> route -> act."""
        qualified = self.agents["qualifier"].execute({
            "lead": input_data.get("lead"),
            "message": input_data.get("message", ""),
            "channel": input_data.get("channel", "web"),
        })
        outcome = qualified.get("result", {})
        tier = outcome.get("tier")

        if tier == "hot":
            matches = self.agents["matcher"].execute({
                "profile": outcome.get("profile", {}),
                "lead": input_data.get("lead"),
                "channel": input_data.get("channel", "sms"),
            })
            self.agents["viewings"].execute({
                "lead": input_data.get("lead"),
                "preferred_time": input_data.get("preferred_time"),
                "listing": (matches.get("result") or {}).get("listings", [{}])[0],
            })
            return {"status": "success", "result": {"tier": tier, "pipeline": "full_flow"}, "agent_alert": True}

        if tier == "warm":
            self.agents["follow_up"].execute({
                "lead": input_data.get("lead"),
                "step": "hot_lead",
                "context": {"listing": input_data.get("message", "")[:80]},
            })
            return {"status": "success", "result": {"tier": tier, "pipeline": "nurture"}}

        return {"status": "success", "result": {"tier": tier, "pipeline": "drip"}}

    def _nightly(self, input_data: dict) -> dict:
        """Nightly batch: CRM sync + follow-up queue dispatch."""
        sync = self.agents["crm_sync"].execute({"task": "nightly_sync"})
        follow_ups = []
        for lead in input_data.get("follow_up_queue", []):
            r = self.agents["follow_up"].execute({"lead": lead, "step": lead.get("step", "viewed_3d")})
            follow_ups.append({"lead": lead.get("id"), "status": r["status"]})
        return {
            "status": "success",
            "result": {"crm_sync": sync.get("result", {}), "follow_ups": follow_ups},
        }
