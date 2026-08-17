"""
Logistics orchestrator: routes inbound documents, runs detection cycles,
and dispatches resolution tasks.

Event flow:
  document arrives (email/API/fax) -> parse -> classify -> route:
    - carrier invoice     -> invoice_matcher -> (discrepancy -> resolver)
    - POD/BOL/rate con    -> ledger attach -> verification
  scheduled detection (hourly) -> exception_detector -> resolver
  scheduled reports -> reporting_agent
"""
import logging
from typing import Any, Optional

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent

logger = logging.getLogger("vertical.logistics.orchestrator")


class LogisticsOrchestrator(BaseAgent):
    def __init__(self, agents: dict[str, BaseAgent], llm: Any = None):
        super().__init__(name="logistics_orchestrator", vertical="logistics_freight", llm=llm)
        self.agents = agents  # {"parser":..., "matcher":..., "detector":..., "resolver":..., "reporting":...}

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        event_type = input_data.get("event_type", "document")

        if event_type == "document":
            return self._on_document(input_data)
        if event_type == "detection_cycle":
            return self._detection_cycle(input_data)
        if event_type == "report":
            return self.agents["reporting"].execute(input_data)
        return {"status": "error", "result": {"action": "unknown_event"}}

    def _on_document(self, input_data: dict) -> dict:
        """Document -> parse -> classify -> route."""
        parsed = self.agents["parser"].execute({
            "file_path": input_data.get("file_path"),
            "file_bytes": input_data.get("file_bytes"),
            "source": input_data.get("source", "email"),
        })
        doc = parsed.get("result", {})
        doc_type = doc.get("document_type", "other")

        route = {
            "carrier_invoice": "matcher",
            "bill_of_lading": "matcher",
            "proof_of_delivery": "matcher",
            "rate_confirmation": "matcher",
        }
        if doc_type in route:
            matched = self.agents[route[doc_type]].execute({
                "invoice": {**doc.get("fields", {}), "reference": doc.get("fields", {}).get("shipment_reference")
                            or doc.get("fields", {}).get("invoice_number")},
            })
            return {"status": "success", "result": {"document_type": doc_type, "handled_by": route[doc_type], **matched.get("result", {})}}

        return {"status": "success", "result": {"document_type": doc_type, "handled_by": "filed", "fields": doc.get("fields")}}

    def _detection_cycle(self, input_data: dict) -> dict:
        """Hourly sweep: check all active shipments for exceptions."""
        shipments = input_data.get("shipments", [])
        detected = []
        for shipment in shipments:
            result = self.agents["detector"].execute({"shipment": shipment})
            exceptions = (result.get("result") or {}).get("exceptions", [])
            detected.extend(exceptions)
            for exc in exceptions:
                resolved = self.agents["resolver"].execute({"exception": exc, "context": shipment.get("context", {})})
                exc["resolution"] = (resolved.get("result") or {}).get("status")
        return {
            "status": "success",
            "result": {"shipments_checked": len(shipments), "exceptions_detected": len(detected), "exceptions": detected},
        }
