"""
Invoice matcher: matches carrier invoices against the shipment ledger and
rate confirmations, flagging discrepancies before payment.

Match dimensions:
  - shipment reference / PRO number
  - contracted rate vs invoiced amount
  - accessorials billed vs authorized
  - fuel surcharge calculation vs contract formula
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent
from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.error_handling import ValidationError

logger = logging.getLogger("vertical.logistics.invoicematch")

MATCH_TOLERANCE_PCT = 2.0  # allow 2% variance before flagging


@dataclass
class MatchResult:
    status: str  # match | discrepancy | unmatched
    variance_pct: float = 0.0
    reasons: list[str] = field(default_factory=list)
    action: str = "pay"  # pay | hold | investigate


class InvoiceMatcherAgent(BaseAgent):
    def __init__(self, ledger, rate_tables, accounting, llm=None):
        super().__init__(name="invoice_matcher_agent", vertical="logistics_freight", llm=llm)
        self.ledger = ledger          # shipment ledger (TMS)
        self.rate_tables = rate_tables  # contracted rates
        self.accounting = accounting  # QuickBooks / Sage / NetSuite connector

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        invoice = input_data.get("invoice") or {}
        if not invoice.get("reference"):
            raise ValidationError("Invoice missing shipment reference")

        shipment = self.ledger.get_shipment(invoice["reference"])
        if shipment is None:
            return {
                "status": "success",
                "result": {
                    "status": "unmatched",
                    "action": "hold",
                    "reasons": [f"No shipment found for {invoice['reference']}"],
                },
            }

        result = self._match(invoice, shipment)
        if result.status == "match":
            self.accounting.mark_ready_to_pay(invoice.get("id"), reference=shipment["id"])
        else:
            self.accounting.hold_payment(invoice.get("id"), reasons=result.reasons)

        logger.info("invoice=%s status=%s variance=%.1f%%", invoice.get("id"), result.status, result.variance_pct)
        return {"status": "success", "result": result.__dict__}

    def _match(self, invoice: dict, shipment: dict) -> MatchResult:
        reasons: list[str] = []
        contracted = self.rate_tables.get_rate(
            carrier=invoice.get("carrier"),
            lane=(shipment.get("origin"), shipment.get("destination")),
            equipment=shipment.get("equipment"),
        )

        # 1. amount vs contracted
        if contracted and invoice.get("amount"):
            variance = (invoice["amount"] - contracted["total"]) / contracted["total"] * 100
            if abs(variance) > MATCH_TOLERANCE_PCT:
                reasons.append(
                    f"Amount ${invoice['amount']:,.2f} vs contracted "
                    f"${contracted['total']:,.2f} ({variance:+.1f}%)"
                )
        else:
            reasons.append("No contracted rate on file for this lane")

        # 2. accessorials
        unauthorized = set(invoice.get("accessorials", [])) - set(shipment.get("authorized_accessorials", []))
        if unauthorized:
            reasons.append(f"Unauthorized accessorials: {', '.join(unauthorized)}")

        # 3. fuel surcharge sanity (bounded check)
        base_fuel = invoice.get("fuel_surcharge", 0)
        est_fuel = (invoice.get("amount", 0) or 0) * 0.10
        if base_fuel > est_fuel * 1.5 and est_fuel > 0:
            reasons.append(f"Fuel surcharge ${base_fuel:,.2f} looks high (est. ~${est_fuel:,.2f})")

        if not reasons:
            return MatchResult(status="match", variance_pct=0.0)
        return MatchResult(
            status="discrepancy",
            variance_pct=round((invoice.get("amount", 0) - (contracted or {}).get("total", 0)) / max((contracted or {}).get("total", 1), 1) * 100, 2),
            reasons=reasons,
            action="hold",
        )
