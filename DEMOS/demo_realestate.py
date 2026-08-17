"""
Stratum Realty — runnable real estate lead pipeline demo.

Runs the REAL brokerage agents (qualifier, matcher, viewing scheduler,
follow-up, CRM sync) against in-memory mocks.

Run:  python3 DEMOS/run_demo.py realestate
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from DEMOS.mocks import FakeLLM, MockCalendar, MockComms, MockCRM, MockEmailer, MockMLS
from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.brokerage_orchestrator import BrokerageOrchestrator
from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.crm_sync_agent import CRMSyncAgent
from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.follow_up_agent import FollowUpAgent
from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.lead_qualifier_agent import LeadQualifierAgent
from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.property_matcher_agent import PropertyMatcherAgent
from VERTICALS.REAL_ESTATE_BROKERAGES.agent_system.viewing_scheduler_agent import ViewingSchedulerAgent


def build_demo():
    crm = MockCRM()
    mls = MockMLS()
    calendar = MockCalendar()
    comms = MockComms(silent=False)
    emailer = MockEmailer(silent=False)
    llm = FakeLLM()
    agents = {
        "qualifier": LeadQualifierAgent(crm, mls, llm=llm),
        "matcher": PropertyMatcherAgent(mls, comms, emailer, llm=llm),
        "viewings": ViewingSchedulerAgent(calendar, crm, comms, llm=llm),
        "follow_up": FollowUpAgent(crm, mls, comms, llm=llm),
        "crm_sync": CRMSyncAgent(crm, mls, llm=llm),
    }
    return BrokerageOrchestrator(agents, llm=llm), {
        "crm": crm, "mls": mls, "calendar": calendar, "comms": comms, "emailer": emailer,
    }


def run_auto():
    print("=" * 66)
    print("  STRATUM REALTY — lead pipeline demo (no external APIs)")
    print("=" * 66)
    orch, env = build_demo()
    agents = orch.agents
    crm = env["crm"]

    print("\n--- 1. HOT LEAD: qualify → match → book viewing --------------------")
    lead = {"name": "Alex Chen", "first_name": "Alex", "email": "alex.chen@example.com",
            "phone": "+15550102", "area": "Maplewood"}
    message = ("Hi, I'm pre-approved for $650k and looking to buy a 3-bed house "
               "in Maplewood asap")
    q = agents["qualifier"].execute({"lead": lead, "message": message, "channel": "sms"})
    print(f"  Score: {q['result']['score']['total']}/100  tier: {q['result']['tier'].upper()}")
    print(f"  Profile: {q['result']['profile']}")
    lead["id"] = q["result"]["contact_id"]

    m = agents["matcher"].execute({"profile": q["result"]["profile"],
                                   "lead": lead, "channel": "sms"})
    print(f"  Matches sent: {m['result']['count']} (see SMS above)")
    listing = m["result"]["listings"][0]

    v = agents["viewings"].execute({
        "listing": listing, "lead": lead,
        "agent": {"name": "Jennifer", "email": "jennifer@broker.com", "phone": "+15550199"},
    })
    print(f"  Viewing: {v['result']['action']} — {listing['address']}")

    print("\n--- 2. WARM LEAD: nurture routing ----------------------------------")
    lead2 = {"name": "Sam Patel", "first_name": "Sam", "email": "sam.p@example.com",
             "phone": "+15550103"}
    q2 = agents["qualifier"].execute({
        "lead": lead2,
        "message": "Thinking about buying in about 6 months, still need a mortgage pre-approval",
        "channel": "web",
    })
    print(f"  Score: {q2['result']['score']['total']}/100  tier: {q2['result']['tier'].upper()}")
    print(f"  Next action: {q2['result']['action']}")

    print("\n--- 3. CRM SYNC: duplicate detection --------------------------------")
    sync = agents["crm_sync"].execute({
        "task": "dedupe",
        "contacts": [
            {"id": "1", "email": "alex.chen@example.com", "phone": "+15550102"},
            {"id": "2", "email": "alex.chen@example.com", "phone": "+15550199"},
            {"id": "3", "email": "other@example.com", "phone": "+15550177"},
        ],
    })
    print(f"  Duplicates found: {sync['result']['duplicates_found']}")
    for d in sync["result"]["duplicates"]:
        print(f"    ⚠ keep {d['keep']} ← merge {d['merge']} ({d['reason']})")

    print("\n--- 4. FOLLOW-UP: hot-lead thank-you + property nudge ---------------")
    agents["follow_up"].execute({"lead": lead, "step": "hot_lead",
                                 "context": {"listing": listing["address"]}})

    print("\n--- SUMMARY ----------------------------------------------------------")
    print(f"  Contacts in CRM:     {len(crm.contacts)}")
    print(f"  SMS messages sent:   {len(env['comms'].sent)}")
    print(f"  Activities logged:   {len(crm.activities)}")
    print("\n✅ Done. Interactive: python3 DEMOS/run_demo.py realestate --interactive")


def run_interactive():
    print("=" * 66)
    print("  STRATUM REALTY — lead chat (qualifier + matcher)")
    print("=" * 66)
    orch, _ = build_demo()
    print("\nDescribe your buying situation ('quit' to exit).\n")
    while True:
        try:
            message = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if message.lower() in ("quit", "exit"):
            break
        q = orch.agents["qualifier"].execute({
            "lead": {"name": "Demo User", "email": "demo@example.com", "phone": "+15550100"},
            "message": message, "channel": "sms",
        })
        r = q["result"]
        print(f"  AI:  Score {r['score']['total']}/100 ({r['tier'].upper()}) — "
              f"action: {r['action']}")


def main(interactive: bool = False) -> None:
    if interactive:
        run_interactive()
    else:
        run_auto()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stratum Realty demo")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    main(interactive=args.interactive)
