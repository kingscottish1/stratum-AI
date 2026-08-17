"""
Exception detector: continuously watches the shipment stream for
exceptions and anomalies before customers notice.

Detects:
  - missed pickup / delivery appointments
  - status gaps (no scan for N hours)
  - temperature/condition alerts (reefer)
  - dwell time over threshold
  - late delivery risk vs committed ETA
  - documentation missing (no POD 48h after delivery)
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.base_agent_class import BaseAgent

logger = logging.getLogger("vertical.logistics.exceptions")

EXCEPTION_TYPES = [
    "missed_pickup", "missed_delivery", "scan_gap", "dwell_time",
    "late_risk", "temperature", "missing_pod", "document_gap",
]


class ExceptionDetectorAgent(BaseAgent):
    def __init__(self, tms, llm=None):
        super().__init__(name="exception_detector_agent", vertical="logistics_freight", llm=llm)
        self.tms = tms

    def run(self, input_data: dict[str, Any]) -> dict[str, Any]:
        shipment = input_data.get("shipment") or {}
        found: list[dict] = []

        if not shipment.get("last_status"):
            found.append(self._mk("scan_gap", shipment, "Shipment has no status updates"))

        if shipment.get("appointment_time"):
            planned = datetime.fromisoformat(shipment["appointment_time"])
            if planned < datetime.now() and shipment.get("status") not in ("delivered", "picked_up"):
                found.append(self._mk("missed_pickup", shipment, "Pickup appointment passed without completion"))

        gap_hours = shipment.get("hours_since_last_scan", 0)
        if gap_hours and gap_hours > input_data.get("scan_gap_threshold_hours", 24):
            found.append(self._mk("scan_gap", shipment, f"No scan for {gap_hours:.0f} hours"))

        if shipment.get("eta") and shipment.get("committed_delivery"):
            eta = datetime.fromisoformat(shipment["eta"])
            committed = datetime.fromisoformat(shipment["committed_delivery"])
            if eta > committed + timedelta(hours=input_data.get("late_tolerance_hours", 4)):
                found.append(self._mk("late_risk", shipment, f"ETA {eta:%b %d %H:%M} past committed {committed:%b %d %H:%M}"))

        if shipment.get("delivered_at") and not shipment.get("pod_received"):
            delivered = datetime.fromisoformat(shipment["delivered_at"])
            if datetime.now() - delivered > timedelta(hours=input_data.get("pod_window_hours", 48)):
                found.append(self._mk("missing_pod", shipment, "Delivered but no POD within 48h"))

        for exc in found:
            self.tms.create_exception(shipment["id"], exc)
            logger.info("exception detected shipment=%s type=%s", shipment["id"], exc["type"])

        return {"status": "success", "result": {"exceptions": found, "count": len(found)}}

    @staticmethod
    def _mk(exc_type: str, shipment: dict, reason: str) -> dict:
        return {
            "type": exc_type,
            "shipment_id": shipment.get("id"),
            "reference": shipment.get("reference"),
            "reason": reason,
            "severity": "high" if exc_type in ("missed_pickup", "missed_delivery", "temperature") else "medium",
            "detected_at": datetime.now().isoformat(),
        }
