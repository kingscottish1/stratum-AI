from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.clinic_orchestrator import ClinicOrchestrator


def _orchestrator():
    return ClinicOrchestrator(agents={}, llm=None)


def test_intent_classification():
    orch = _orchestrator()
    assert orch.classify("Can I book a cleaning this week?") == "book"
    assert orch.classify("Cancel my appointment") == "cancel"
    assert orch.classify("What are your hours?") == "hours"
    assert orch.classify("Do you take Delta Dental insurance?") == "insurance"
    assert orch.classify("Where are you located?") == "directions"
    assert orch.classify("Thanks!") == "general"
