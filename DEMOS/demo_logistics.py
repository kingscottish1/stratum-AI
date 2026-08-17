"""
Stratum Freight — runnable logistics demo (invoice matching + exceptions).

Runs the REAL freight agents (document parser, invoice matcher, exception
detector, resolver, reporting) against in-memory mocks.

Run:  python3 DEMOS/run_demo.py logistics
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from DEMOS.mocks import (FakeLLM, MockAccounting, MockComms, MockEmailer,
                         MockRateTables, MockTMS)
from VERTICALS.LOGISTICS_FREIGHT.agent_system.document_parser_agent import DocumentParserAgent
from VERTICALS.LOGISTICS_FREIGHT.agent_system.exception_detector_agent import ExceptionDetectorAgent
from VERTICALS.LOGISTICS_FREIGHT.agent_system.exception_resolver_agent import ExceptionResolverAgent
from VERTICALS.LOGISTICS_FREIGHT.agent_system.invoice_matcher_agent import InvoiceMatcherAgent
from VERTICALS.LOGISTICS_FREIGHT.agent_system.reporting_agent import ReportingAgent

SAMPLES = Path(__file__).resolve().parent / "samples"


def run_auto():
    print("=" * 66)
    print("  STRATUM FREIGHT — AP & exception automation demo (no external APIs)")
    print("=" * 66)

    tms = MockTMS()
    rates = MockRateTables()
    acct = MockAccounting()
    comms = MockComms(silent=True)
    emailer = MockEmailer(silent=False)
    llm = FakeLLM()

    parser = DocumentParserAgent(llm=llm)
    matcher = InvoiceMatcherAgent(tms, rates, acct, llm=None)

    print("\n--- 1. DOCUMENT INGESTION: parse + classify a carrier invoice -------")
    parsed = parser.execute({"file_path": str(SAMPLES / "invoice_001.txt"), "source": "email"})
    doc = parsed["result"]
    print(f"  Type: {doc['document_type']}  (confidence {doc['confidence']})")
    f = doc["fields"]
    print(f"  Fields: invoice={f.get('invoice_number')}  ref={f.get('shipment_reference')}  "
          f"amount=${f.get('amount')}  carrier={f.get('carrier')}")

    print("\n--- 2. INVOICE MATCHING: clean invoice → approved for payment --------")
    clean = {"id": "INV-1", "reference": "SH-1001", "carrier": "FedEx",
             "amount": 1208.0, "accessorials": ["liftgate"], "fuel_surcharge": 90.0}
    r1 = matcher.execute({"invoice": clean})
    print(f"  Status: {r1['result']['status'].upper()}  →  action: {r1['result']['action']}")
    print(f"  Accounting: approved={acct.approved}  held={acct.held}")

    print("\n--- 3. INVOICE MATCHING: overcharge → held with evidence -------------")
    bad = {"id": "INV-2", "reference": "SH-1001", "carrier": "FedEx",
           "amount": 1250.0, "accessorials": ["liftgate"], "fuel_surcharge": 95.0}
    r2 = matcher.execute({"invoice": bad})
    print(f"  Status: {r2['result']['status'].upper()}  →  action: {r2['result']['action']}")
    for reason in r2["result"]["reasons"]:
        print(f"    ⚠ {reason}")

    print("\n--- 4. EXCEPTION DETECTION: delivered but no POD (48h window) --------")
    detector = ExceptionDetectorAgent(tms, llm=None)
    detected = detector.execute({"shipment": tms.get_shipment("SH-1001")})
    for exc in detected["result"]["exceptions"]:
        print(f"  Detected: {exc['type']} ({exc['severity']}) — {exc['reason']}")

    print("\n--- 5. EXCEPTION RESOLUTION: auto POD chase (email to carrier) -------")
    resolver = ExceptionResolverAgent(tms, acct, emailer, llm=None)
    exc = detected["result"]["exceptions"][0]
    r5 = resolver.execute({"exception": exc, "context": {}})
    print(f"  Resolution: {r5['result']['status']}")

    print("\n--- 6. EXCEPTION DETECTION: scan gap (31h silent) --------------------")
    detected2 = detector.execute({"shipment": tms.get_shipment("SH-1002")})
    for exc in detected2["result"]["exceptions"]:
        print(f"  Detected: {exc['type']} ({exc['severity']}) — {exc['reason']}")
    print("  (scan gaps have no automated path → human escalation ticket is raised)")

    print("\n--- 7. REPORTING: exception dashboard --------------------------------")
    rep = ReportingAgent(tms, acct, llm=None)
    r7 = rep.execute({"report_type": "exception_dashboard", "period": "last_week"})
    print(f"  {r7['result']['data']}")

    print("\n--- SUMMARY -----------------------------------------------------------")
    print(f"  Invoices approved for payment: {len(acct.approved)}")
    print(f"  Invoices held with reasons:    {len(acct.held)}")
    print(f"  Exceptions detected:           {len(tms.exceptions)}")
    print(f"  Emails sent:                   {len(emailer.sent)}")
    print("\n✅ Done. Interactive: python3 DEMOS/run_demo.py logistics --interactive")


def run_interactive():
    print("=" * 66)
    print("  STRATUM FREIGHT — try the matcher on your own invoice amount")
    print("=" * 66)
    tms = MockTMS()
    rates = MockRateTables()
    acct = MockAccounting()
    matcher = InvoiceMatcherAgent(tms, rates, acct, llm=None)
    print("\nContracted rate for SH-1001 (Denver → SLC, 53ft): $1,200.00")
    print("Tolerance: ±2%. Enter an invoice amount ('quit' to exit).\n")
    while True:
        try:
            value = input("  Amount $: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if value.lower() in ("quit", "exit"):
            break
        try:
            amount = float(value.replace(",", ""))
        except ValueError:
            print("  Please enter a number.")
            continue
        result = matcher.execute({
            "invoice": {"id": "INV-X", "reference": "SH-1001", "carrier": "FedEx",
                        "amount": amount, "accessorials": ["liftgate"], "fuel_surcharge": 0},
        })
        r = result["result"]
        print(f"  → {r['status'].upper()} / {r['action']}")
        for reason in r.get("reasons", []):
            print(f"    ⚠ {reason}")


def main(interactive: bool = False) -> None:
    if interactive:
        run_interactive()
    else:
        run_auto()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Stratum Freight demo")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    main(interactive=args.interactive)
