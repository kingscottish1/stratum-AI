from DEMOS.mocks import MockCRM, MockMLS
from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.lead_qualifier_agent import LeadQualifierAgent


def _qualifier():
    return LeadQualifierAgent(MockCRM(), MockMLS(), llm=None)


def test_warm_lead_keyword_scoring():
    q = _qualifier()
    result = q.execute({
        "lead": {"name": "Alex", "email": "alex@example.com", "phone": "+15550102",
                 "area": "Maplewood"},
        "message": "I'm pre-approved and want to buy ASAP in Maplewood",
        "channel": "sms",
    })
    r = result["result"]
    assert r["tier"] in ("hot", "warm")
    assert r["score"]["total"] >= 40
    assert r["contact_id"]


def test_contact_created_and_scored_in_crm():
    crm = MockCRM()
    q = LeadQualifierAgent(crm, MockMLS(), llm=None)
    result = q.execute({
        "lead": {"name": "Sam", "email": "sam@example.com", "phone": "+15550103"},
        "message": "maybe interested sometime", "channel": "web",
    })
    contact = crm.get_contact(result["result"]["contact_id"])
    assert contact is not None
    assert "lead_score" in contact
