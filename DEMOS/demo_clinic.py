"""
Stratum Care — runnable clinic agent suite demo.

Runs the REAL clinic agents (appointment, insurance intake, reminders,
follow-up) against in-memory mocks. No external APIs, no API keys.

Run:  python3 DEMOS/run_demo.py clinic            (scripted scenario)
      python3 DEMOS/run_demo.py clinic --interactive   (chat with it)
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from DEMOS.mocks import (FakeLLM, MockCalendar, MockComms, MockEmailer,
                         MockInsuranceAPI, MockPMS)
from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.appointment_agent import AppointmentAgent
from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.clinic_orchestrator import ClinicOrchestrator
from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.follow_up_agent import FollowUpAgent
from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.insurance_intake_agent import InsuranceIntakeAgent
from VERTICALS.MEDICAL_DENTAL_CLINICS.agent_system.patient_communication_agent import PatientCommunicationAgent

PATIENT = {
    "id": "p-101", "name": "Jamie Rivera", "first_name": "Jamie",
    "phone": "+15550101", "email": "jamie@example.com",
}


def build_demo():
    calendar = MockCalendar()
    pms = MockPMS()
    comms = MockComms(silent=False)
    emailer = MockEmailer(silent=False)
    llm = FakeLLM()
    agents = {
        "appointment": AppointmentAgent(calendar, pms, comms, llm=llm),
        "insurance_intake": InsuranceIntakeAgent(pms, MockInsuranceAPI(), comms, llm=llm),
        "patient_communication": PatientCommunicationAgent(calendar, comms, emailer, llm=llm),
        "follow_up": FollowUpAgent(pms, calendar, comms, llm=llm),
    }
    return ClinicOrchestrator(agents, llm=llm), {
        "calendar": calendar, "pms": pms, "comms": comms, "emailer": emailer,
    }


def banner():
    print("=" * 66)
    print("  STRATUM CARE — clinic agent suite (runnable demo, no external APIs)")
    print("=" * 66)


def run_auto():
    banner()
    orch, env = build_demo()
    comms = env["comms"]

    print("\n--- 1. BOOKING: patient asks for an appointment ------------------")
    result = orch.execute({"message": "Hi! Can I book a cleaning this week?",
                           "patient": PATIENT, "channel": "sms", "session": {}})
    print(f"  🗣 Patient: Hi! Can I book a cleaning this week?")
    print(f"  🤖 Agent:   {result.get('reply', '')}")

    print("\n--- 2. CANCELLATION: patient changes their mind -------------------")
    result = orch.execute({"message": "Actually, cancel my appointment please",
                           "patient": PATIENT, "channel": "sms", "session": {}})
    print(f"  🗣 Patient: Actually, cancel my appointment please")
    print(f"  🤖 Agent:   {result.get('reply', '')}")

    print("\n--- 3. REBOOK (so we have an appointment for reminders) -----------")
    result = orch.execute({"message": "Let's rebook — a cleaning on Wednesday if possible",
                           "patient": PATIENT, "channel": "sms", "session": {}})
    print(f"  🗣 Patient: Let's rebook — a cleaning on Wednesday if possible")
    print(f"  🤖 Agent:   {result.get('reply', '')}")

    print("\n--- 4. INSURANCE INTAKE: 4 fields collected one at a time ---------")
    intake = orch.agents["insurance_intake"]
    session = {}
    for answer in ["Delta Dental", "DX-772-441", "PPO Plus", "03/15/1990"]:
        result = intake.execute({"message": answer, "patient": PATIENT,
                                 "channel": "sms", "session": session})
        session = result.get("session") or session
        print(f"  🗣 Patient: {answer}")
        print(f"  🤖 Agent:   {result.get('reply', '')}")

    print("\n--- 5. REMINDERS: 48h reminder (SMS + email) — scheduled job ------")
    appt = env["pms"].appointments[-1]
    orch.agents["patient_communication"].execute({
        "task": "reminder_48h", "patient": PATIENT,
        "appointment": {"start": appt["start"], "service": appt["service"],
                        "clinic_name": "Acme Dental", "address": "12 Main St, Denver",
                        "clinic_phone": "+17205550123"},
    })

    print("\n--- 6. FOLLOW-UP: no-show rebooking offer -------------------------")
    orch.agents["follow_up"].execute({
        "task_type": "no_show", "patient": PATIENT,
        "context": {"appointment": {"service": "cleaning", "date": "2 days ago"}},
    })

    print("\n--- SUMMARY --------------------------------------------------------")
    print(f"  SMS messages sent:            {len(comms.sent)}")
    print(f"  Emails sent:                  {len(env['emailer'].sent)}")
    print(f"  Appointments in mock calendar:{len(env['calendar'].events)}")
    print(f"  Insurance saved for patient:  {'p-101' in env['pms'].saved_insurance}")
    print("\n✅ Done. Interactive mode:  python3 DEMOS/run_demo.py clinic --interactive")


def run_interactive():
    banner()
    orch, _ = build_demo()
    print("\nYou are Jamie Rivera. Type a message ('quit' to exit).\n")
    session = {}
    while True:
        try:
            message = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if message.lower() in ("quit", "exit"):
            break
        result = orch.execute({"message": message, "patient": PATIENT,
                               "channel": "sms", "session": session})
        session = result.get("session") or session
        print(f"  AI:  {result.get('reply', '')}")


def main(interactive: bool = False) -> None:
    if interactive:
        run_interactive()
    else:
        run_auto()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stratum Care demo")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    main(interactive=args.interactive)
