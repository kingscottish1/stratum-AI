"""
Agent runtime resolver.

Builds a vertical agent suite for a client instance:
  - DEMO_MODE=true  → in-memory mock connectors (testing only)
  - DEMO_MODE=false → REAL connectors wired from the client's encrypted
                      integration records; refuses to run with missing
                      credentials (nothing fake in production).

This is the seam between the REST API and the vertical agent code.
"""
import logging
from typing import Any, Optional

from CORE_AGENT_INFRASTRUCTURE.config import get_config
from CORE_AGENT_INFRASTRUCTURE.frameworks.custom_frameworks.error_handling import ConfigurationError

logger = logging.getLogger("stratum.runtime")


class AgentRuntimeError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Vertical suite builders — demo path (mocks)
# ---------------------------------------------------------------------------
def _demo_suite(vertical: str) -> Any:
    """Build the suite with in-memory mocks. DEMO ONLY — hard-fails in prod."""
    if get_config().is_production():
        raise AgentRuntimeError("Mock connectors are disabled in production (DEMO_MODE must be true)")

    from DEMOS.mocks import (FakeLLM, MockAccounting, MockCalendar, MockComms,
                             MockCRM, MockEmailer, MockInsuranceAPI, MockMLS,
                             MockPMS, MockRateTables, MockTMS)

    llm = FakeLLM()

    if vertical == "medical_dental_clinics":
        from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.appointment_agent import AppointmentAgent
        from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.clinic_orchestrator import ClinicOrchestrator
        from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.follow_up_agent import FollowUpAgent
        from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.insurance_intake_agent import InsuranceIntakeAgent
        from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.patient_communication_agent import PatientCommunicationAgent

        calendar, pms, comms, emailer = MockCalendar(), MockPMS(), MockComms(silent=True), MockEmailer(silent=True)
        agents = {
            "appointment": AppointmentAgent(calendar, pms, comms, llm=llm),
            "insurance_intake": InsuranceIntakeAgent(pms, MockInsuranceAPI(), comms, llm=llm),
            "patient_communication": PatientCommunicationAgent(calendar, comms, emailer, llm=llm),
            "follow_up": FollowUpAgent(pms, calendar, comms, llm=llm),
        }
        return ClinicOrchestrator(agents, llm=llm), {"calendar": calendar, "pms": pms, "comms": comms}

    if vertical == "real_estate_brokerages":
        from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.brokerage_orchestrator import BrokerageOrchestrator
        from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.crm_sync_agent import CRMSyncAgent
        from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.follow_up_agent import FollowUpAgent
        from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.lead_qualifier_agent import LeadQualifierAgent
        from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.property_matcher_agent import PropertyMatcherAgent
        from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.viewing_scheduler_agent import ViewingSchedulerAgent

        crm, mls, calendar, comms, emailer = MockCRM(), MockMLS(), MockCalendar(), MockComms(silent=True), MockEmailer(silent=True)
        agents = {
            "qualifier": LeadQualifierAgent(crm, mls, llm=llm),
            "matcher": PropertyMatcherAgent(mls, comms, emailer, llm=llm),
            "viewings": ViewingSchedulerAgent(calendar, crm, comms, llm=llm),
            "follow_up": FollowUpAgent(crm, mls, comms, llm=llm),
            "crm_sync": CRMSyncAgent(crm, mls, llm=llm),
        }
        return BrokerageOrchestrator(agents, llm=llm), {"crm": crm, "mls": mls, "calendar": calendar, "comms": comms}

    if vertical == "logistics_freight":
        from VERTICALS.LOGISTICS_FREIGHT.agent_system.document_parser_agent import DocumentParserAgent
        from VERTICALS.LOGISTICS_FREIGHT.agent_system.exception_detector_agent import ExceptionDetectorAgent
        from VERTICALS.LOGISTICS_FREIGHT.agent_system.exception_resolver_agent import ExceptionResolverAgent
        from VERTICALS.LOGISTICS_FREIGHT.agent_system.invoice_matcher_agent import InvoiceMatcherAgent
        from VERTICALS.LOGISTICS_FREIGHT.agent_system.logistics_orchestrator import LogisticsOrchestrator
        from VERTICALS.LOGISTICS_FREIGHT.agent_system.reporting_agent import ReportingAgent

        tms, rates, acct, comms, emailer = MockTMS(), MockRateTables(), MockAccounting(), MockComms(silent=True), MockEmailer(silent=True)
        agents = {
            "parser": DocumentParserAgent(llm=llm),
            "matcher": InvoiceMatcherAgent(tms, rates, acct, llm=None),
            "detector": ExceptionDetectorAgent(tms, llm=None),
            "resolver": ExceptionResolverAgent(tms, acct, emailer, llm=None),
            "reporting": ReportingAgent(tms, acct, llm=None),
        }
        return LogisticsOrchestrator(agents, llm=llm), {"tms": tms, "acct": acct}

    raise AgentRuntimeError(f"Unknown vertical: {vertical}")


# ---------------------------------------------------------------------------
# Vertical suite builders — production path (REAL connectors)
# ---------------------------------------------------------------------------
def _production_suite(vertical: str, integrations: list[dict], config: dict) -> Any:
    """Wire real connectors from encrypted integration records.

    Each integration row (name, category, base_url, decrypted api_key)
    maps to the connector class for that vertical. If a required
    credential is missing, we refuse to run rather than silently fake it.
    """
    from CORE_AGENT_INFRASTRUCTURE.llm.factory import build_llm

    llm = build_llm()
    by_name = {i["name"].lower(): i for i in integrations}

    def require(name: str) -> dict:
        if name not in by_name:
            raise AgentRuntimeError(
                f"Integration '{name}' is not configured for this client. "
                "Add its API credentials in Integrations first."
            )
        return by_name[name]

    if vertical == "medical_dental_clinics":
        from CORE_AGENT_INFRASTRUCTURE.shared_tools.calendar_sync.google_calendar_connector import GoogleCalendarConnector
        from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.appointment_agent import AppointmentAgent
        from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.clinic_orchestrator import ClinicOrchestrator
        from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.follow_up_agent import FollowUpAgent
        from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.insurance_intake_agent import InsuranceIntakeAgent
        from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.patient_communication_agent import PatientCommunicationAgent

        cal = require("google_calendar")
        sms = require("twilio")
        calendar = GoogleCalendarConnector(calendar_id=config.get("calendar_id", ""))
        comms = _twilio_comms(sms)
        agents = {
            "appointment": AppointmentAgent(calendar, None, comms, llm=llm),
            "insurance_intake": InsuranceIntakeAgent(None, None, comms, llm=llm),
            "patient_communication": PatientCommunicationAgent(calendar, comms, None, llm=llm),
            "follow_up": FollowUpAgent(None, calendar, comms, llm=llm),
        }
        return ClinicOrchestrator(agents, llm=llm), {}

    if vertical == "real_estate_brokerages":
        from CORE_AGENT_INFRASTRUCTURE.shared_tools.calendar_sync.google_calendar_connector import GoogleCalendarConnector
        from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.brokerage_orchestrator import BrokerageOrchestrator
        from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.crm_sync_agent import CRMSyncAgent
        from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.follow_up_agent import FollowUpAgent
        from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.lead_qualifier_agent import LeadQualifierAgent
        from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.property_matcher_agent import PropertyMatcherAgent
        from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.viewing_scheduler_agent import ViewingSchedulerAgent
        from VERTICALS.REAL_ESTATE_BROKERAGES.integrations.crm_integrations.follow_crm import FollowUpBossCRM
        from VERTICALS.REAL_ESTATE_BROKERAGES.integrations.mls_connector import MLSConnector

        crm_i = require("follow_up_boss")
        mls_i = require("mls")
        crm = FollowUpBossCRM(api_key=crm_i["api_key"])
        mls = MLSConnector()
        calendar = GoogleCalendarConnector()
        comms = _twilio_comms(require("twilio"))
        agents = {
            "qualifier": LeadQualifierAgent(crm, mls, llm=llm),
            "matcher": PropertyMatcherAgent(mls, comms, None, llm=llm),
            "viewings": ViewingSchedulerAgent(calendar, crm, comms, llm=llm),
            "follow_up": FollowUpAgent(crm, mls, comms, llm=llm),
            "crm_sync": CRMSyncAgent(crm, mls, llm=llm),
        }
        return BrokerageOrchestrator(agents, llm=llm), {}

    if vertical == "logistics_freight":
        from VERTICALS.LOGISTICS_FREIGHT.agent_system.document_parser_agent import DocumentParserAgent
        from VERTICALS.LOGISTICS_FREIGHT.agent_system.exception_detector_agent import ExceptionDetectorAgent
        from VERTICALS.LOGISTICS_FREIGHT.agent_system.exception_resolver_agent import ExceptionResolverAgent
        from VERTICALS.LOGISTICS_FREIGHT.agent_system.invoice_matcher_agent import InvoiceMatcherAgent
        from VERTICALS.LOGISTICS_FREIGHT.agent_system.logistics_orchestrator import LogisticsOrchestrator
        from VERTICALS.LOGISTICS_FREIGHT.agent_system.reporting_agent import ReportingAgent
        from VERTICALS.LOGISTICS_FREIGHT.integrations.accounting_connectors.quickbooks_connector import QuickBooksConnector
        from VERTICALS.LOGISTICS_FREIGHT.integrations.freight_software_connectors.tmw_connector import TMWConnector

        tms_i = require("tmw")
        acct_i = require("quickbooks")
        tms = TMWConnector(base_url=tms_i.get("base_url") or "", api_key=tms_i["api_key"])
        acct = QuickBooksConnector()
        emailer = None
        agents = {
            "parser": DocumentParserAgent(llm=llm),
            "matcher": InvoiceMatcherAgent(tms, None, acct, llm=llm),
            "detector": ExceptionDetectorAgent(tms, llm=llm),
            "resolver": ExceptionResolverAgent(tms, acct, emailer, llm=llm),
            "reporting": ReportingAgent(tms, acct, llm=llm),
        }
        return LogisticsOrchestrator(agents, llm=llm), {}

    raise AgentRuntimeError(f"Unknown vertical: {vertical}")


def _twilio_comms(integration: dict):
    """Build a Twilio SMS sender from an encrypted integration record."""
    import os

    from CORE_AGENT_INFRASTRUCTURE.shared_tools.communication_channels.twilio_sms import TwilioSMS

    os.environ["TWILIO_ACCOUNT_SID"] = integration.get("extra_json", {}).get("account_sid", "")
    os.environ["TWILIO_AUTH_TOKEN"] = integration["api_key"]
    os.environ["TWILIO_FROM_NUMBER"] = integration.get("base_url") or ""
    return TwilioSMS()


def build_suite(vertical: str, integrations: list[dict], config: dict, demo: Optional[bool] = None) -> Any:
    """Entry point: returns (orchestrator, env) for a client instance."""
    use_demo = get_config().is_demo() if demo is None else demo
    if use_demo:
        logger.info("building DEMO suite for vertical=%s", vertical)
        return _demo_suite(vertical)
    logger.info("building PRODUCTION suite for vertical=%s (integrations=%d)", vertical, len(integrations))
    return _production_suite(vertical, integrations, config)
