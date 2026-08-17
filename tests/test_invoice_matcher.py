from DEMOS.mocks import MockAccounting, MockRateTables, MockTMS
from VERTICALS.LOGISTICS_FREIGHT.agent_system.invoice_matcher_agent import InvoiceMatcherAgent


def _matcher():
    return InvoiceMatcherAgent(MockTMS(), MockRateTables(), MockAccounting(), llm=None)


def test_clean_match_approves():
    m = _matcher()
    result = m.execute({
        "invoice": {"id": "INV-1", "reference": "SH-1001", "carrier": "FedEx",
                    "amount": 1208.0, "accessorials": ["liftgate"], "fuel_surcharge": 90.0},
    })
    assert result["result"]["status"] == "match"
    assert result["result"]["action"] == "pay"
    assert "INV-1" in m.accounting.approved


def test_overcharge_held_with_reasons():
    m = _matcher()
    result = m.execute({
        "invoice": {"id": "INV-2", "reference": "SH-1001", "carrier": "FedEx",
                    "amount": 1250.0, "accessorials": ["liftgate"], "fuel_surcharge": 95.0},
    })
    assert result["result"]["status"] == "discrepancy"
    assert result["result"]["action"] == "hold"
    assert any("Amount" in r for r in result["result"]["reasons"])
    assert m.accounting.held[0]["id"] == "INV-2"


def test_unmatched_reference_held():
    m = _matcher()
    result = m.execute({"invoice": {"id": "INV-9", "reference": "SH-NOPE", "amount": 1.0}})
    assert result["result"]["status"] == "unmatched"
    assert result["result"]["action"] == "hold"


def test_unauthorized_accessorial_flagged():
    m = _matcher()
    result = m.execute({
        "invoice": {"id": "INV-3", "reference": "SH-1001", "carrier": "FedEx",
                    "amount": 1208.0, "accessorials": ["liftgate", "residential_delivery"],
                    "fuel_surcharge": 90.0},
    })
    assert any("Unauthorized accessorials" in r for r in result["result"]["reasons"])
