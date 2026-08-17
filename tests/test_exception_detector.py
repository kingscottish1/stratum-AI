from datetime import datetime, timedelta

from DEMOS.mocks import MockTMS
from VERTICALS.LOGISTICS_FREIGHT.agent_system.exception_detector_agent import ExceptionDetectorAgent


def test_missing_pod_detected():
    tms = MockTMS()
    detector = ExceptionDetectorAgent(tms, llm=None)
    result = detector.execute({"shipment": tms.get_shipment("SH-1001")})
    types = [e["type"] for e in result["result"]["exceptions"]]
    assert "missing_pod" in types
    assert tms.exceptions  # persisted to the TMS


def test_scan_gap_detected():
    tms = MockTMS()
    detector = ExceptionDetectorAgent(tms, llm=None)
    result = detector.execute({"shipment": tms.get_shipment("SH-1002")})
    types = [e["type"] for e in result["result"]["exceptions"]]
    assert "scan_gap" in types


def test_healthy_shipment_no_exceptions():
    tms = MockTMS()
    detector = ExceptionDetectorAgent(tms, llm=None)
    now = datetime.now()
    healthy = {
        "id": "SH-OK", "reference": "SH-OK", "last_status": "in_transit",
        "hours_since_last_scan": 1,
        "eta": (now + timedelta(hours=2)).isoformat(),
        "committed_delivery": (now + timedelta(hours=6)).isoformat(),
        "appointment_time": (now + timedelta(hours=1)).isoformat(),
    }
    result = detector.execute({"shipment": healthy})
    assert result["result"]["exceptions"] == []
