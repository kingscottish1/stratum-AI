"""
Exception resolver: works exception queues automatically — gathering
evidence, drafting dispute/claim packages, and escalating only when
human judgment is truly needed.

Resolves:
  - invoice disputes (overcharge, duplicate, incorrect accessorials)
  - OS&D (overage/shortage/damage) claim packages
  - service failure credits (late pickup/delivery per contract)
  - documentation requests (chasing PODs, rate cons)
"""
import logging
from typing import Any, Optional

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent
from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.error_handling import HandoffRequired

logger = logging.getLogger("vertical.logistics.resolver")


class ExceptionResolverAgent(BaseAgent):
    def __init__(self, tms, accounting, comms, llm):
        super().__init__(name="exception_resolver_agent", vertical="logistics_freight", llm=llm)
        self.tms = tms
        self.accounting = accounting
        self.comms = comms  # email handler

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        exception = input_data.get("exception") or {}
        exc_type = exception.get("type")

        handlers = {
            "missing_pod": self._chase_pod,
            "invoice_dispute": self._build_dispute,
            "osd_claim": self._build_claim,
            "service_failure": self._request_credit,
        }
        handler = handlers.get(exc_type)
        if handler is None:
            raise HandoffRequired(f"No automated path for exception type '{exc_type}'")

        result = handler(exception, input_data.get("context", {}))
        self.tms.mark_exception(exception.get("id"), status=result.get("status", "processed"))
        return {"status": "success", "result": result}

    def _chase_pod(self, exception: dict, ctx: dict) -> dict:
        shipment = self.tms.get_shipment(exception.get("shipment_id"))
        carrier_email = (shipment or {}).get("carrier_email")
        if not carrier_email:
            raise HandoffRequired("No carrier contact for POD chase")
        self.comms.send(
            to=carrier_email,
            subject=f"POD request — {shipment.get('reference', '')}",
            text=(
                f"Hi, per our contract we require the POD for shipment "
                f"{shipment.get('reference', '')} (delivered "
                f"{shipment.get('delivered_at', 'unknown')}). Please send within 24h. Thanks!"
            ),
        )
        return {"status": "pod_requested", "carrier": shipment.get("carrier")}

    def _build_dispute(self, exception: dict, ctx: dict) -> dict:
        invoice = exception.get("invoice") or {}
        evidence = ctx.get("evidence", {})
        dispute = {
            "invoice_id": invoice.get("id"),
            "carrier": invoice.get("carrier"),
            "amount": invoice.get("amount"),
            "dispute_amount": evidence.get("overcharge_amount"),
            "reason": evidence.get("reason", "Rate discrepancy vs contract"),
            "attachments": evidence.get("attachments", []),
        }
        self.accounting.submit_dispute(dispute)
        return {"status": "dispute_submitted", "dispute": dispute}

    def _build_claim(self, exception: dict, ctx: dict) -> dict:
        claim = {
            "shipment": exception.get("shipment_id"),
            "type": exception.get("subtype", "osd"),
            "description": exception.get("reason"),
            "declared_value": ctx.get("declared_value"),
            "photos": ctx.get("photos", []),
            "pods": ctx.get("pods", []),
        }
        self.tms.submit_claim(claim)
        return {"status": "claim_submitted", "claim_id": claim.get("shipment")}

    def _request_credit(self, exception: dict, ctx: dict) -> dict:
        credit = {
            "carrier": ctx.get("carrier"),
            "shipment": exception.get("shipment_id"),
            "type": "service_failure",
            "basis": exception.get("reason"),
            "credit_amount": ctx.get("credit_amount"),
        }
        self.accounting.request_credit(credit)
        return {"status": "credit_requested", "credit": credit}
