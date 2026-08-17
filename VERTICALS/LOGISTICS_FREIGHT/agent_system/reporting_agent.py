"""
Reporting agent: builds the operational and financial reports the
back office used to assemble by hand.

Standard reports:
  - weekly carrier scorecard (on-time %, disputes, cost per shipment)
  - monthly freight spend analysis (lane, mode, carrier)
  - exception dashboard (types, aging, resolution rate)
  - invoice-to-payment cycle (DPO, hold reasons)
"""
import logging
from datetime import datetime
from typing import Any, Optional

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent

logger = logging.getLogger("vertical.logistics.reporting")


class ReportingAgent(BaseAgent):
    def __init__(self, tms, accounting, llm=None):
        super().__init__(name="reporting_agent", vertical="logistics_freight", llm=llm)
        self.tms = tms
        self.accounting = accounting

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        report_type = input_data.get("report_type", "weekly_carrier_scorecard")
        period = input_data.get("period", "last_week")

        builders = {
            "weekly_carrier_scorecard": self._carrier_scorecard,
            "monthly_spend": self._spend_analysis,
            "exception_dashboard": self._exception_dashboard,
            "invoice_cycle": self._invoice_cycle,
        }
        if report_type not in builders:
            return {"status": "error", "result": {"action": "unknown_report"}}

        data = builders[report_type](period, input_data.get("options", {}))
        summary = self._summarize(report_type, data)
        return {"status": "success", "result": {"report_type": report_type, "period": period, "data": data, "summary": summary}}

    def _carrier_scorecard(self, period: str, options: dict) -> dict:
        shipments = self.tms.shipments_in_period(period)
        carriers: dict[str, dict] = {}
        for s in shipments:
            c = carriers.setdefault(s["carrier"], {"shipments": 0, "on_time": 0, "exceptions": 0, "spend": 0.0})
            c["shipments"] += 1
            c["on_time"] += 1 if s.get("on_time") else 0
            c["exceptions"] += len(s.get("exceptions", []))
            c["spend"] += s.get("cost", 0.0)
        for c in carriers.values():
            c["on_time_pct"] = round(c["on_time"] / c["shipments"] * 100, 1) if c["shipments"] else 0
        return {"carriers": carriers}

    def _spend_analysis(self, period: str, options: dict) -> dict:
        return {"lanes": self.tms.spend_by_lane(period), "modes": self.tms.spend_by_mode(period)}

    def _exception_dashboard(self, period: str, options: dict) -> dict:
        exceptions = self.tms.exceptions_in_period(period)
        by_type: dict[str, int] = {}
        aging: dict[str, int] = {"0-24h": 0, "24-72h": 0, "72h+": 0}
        for e in exceptions:
            by_type[e["type"]] = by_type.get(e["type"], 0) + 1
            age_h = (datetime.now() - datetime.fromisoformat(e["detected_at"])).total_seconds() / 3600
            if age_h <= 24:
                aging["0-24h"] += 1
            elif age_h <= 72:
                aging["24-72h"] += 1
            else:
                aging["72h+"] += 1
        return {"by_type": by_type, "aging": aging, "total": len(exceptions)}

    def _invoice_cycle(self, period: str, options: dict) -> dict:
        invoices = self.accounting.invoices_in_period(period)
        held = [i for i in invoices if i.get("status") == "held"]
        return {
            "total_invoices": len(invoices),
            "total_value": sum(i.get("amount", 0) for i in invoices),
            "held": len(held),
            "hold_value": sum(i.get("amount", 0) for i in held),
            "avg_days_to_pay": round(sum(i.get("days_to_pay", 0) for i in invoices) / max(len(invoices), 1), 1),
        }

    def _summarize(self, report_type: str, data: dict) -> str:
        if report_type == "weekly_carrier_scorecard":
            carriers = data["carriers"]
            worst = min(carriers, key=lambda c: carriers[c]["on_time_pct"]) if carriers else "n/a"
            return f"Scorecard: {len(carriers)} carriers tracked; lowest on-time: {worst}."
        return f"{report_type.replace('_', ' ').title()} ready — {data.get('total', 'see data')} records."
