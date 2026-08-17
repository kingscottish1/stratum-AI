# Stratum AI — Runnable Demos

The whole platform is demoable **without any API keys or external services**:
the demos run the real agent code against in-memory mocks (see `mocks.py`),
including a rule-based `FakeLLM` so LLM-dependent paths still execute.

## Quick start
```bash
python3 DEMOS/run_demo.py all                # all three verticals, scripted
python3 DEMOS/run_demo.py clinic             # clinic suite (booking, cancel,
                                             #   insurance, reminders, follow-up)
python3 DEMOS/run_demo.py realestate         # lead pipeline (qualify → match → viewing)
python3 DEMOS/run_demo.py logistics          # invoice matching + exception resolution
python3 DEMOS/run_demo.py clinic --interactive   # chat with the clinic agents
python3 DEMOS/run_demo.py logistics --interactive # try invoice amounts vs contract
```

## What each demo proves
- **Clinic** — a patient books and cancels; insurance intake collects 4 fields
  conversationally; 48h reminders fire over SMS + email; no-show follow-up
  offers rebooking slots. Calendar events and PMS records are created/kept in sync.
- **Real estate** — a hot lead is scored 95/100, matched to MLS listings and
  a showing is booked on the agent calendar; a warm lead enters nurture; the
  CRM dedupe catches duplicate contacts.
- **Logistics** — a carrier invoice is parsed and classified, a clean invoice
  is approved for payment, an overcharge is held with reasons, a missing-POD
  exception auto-triggers a carrier email, and the exception dashboard
  aggregates everything.

## Mocks (`mocks.py`)
`MockCalendar`, `MockPMS`, `MockCRM`, `MockMLS`, `MockTMS`, `MockRateTables`,
`MockAccounting`, `MockComms`, `MockEmailer`, `MockInsuranceAPI`, `FakeLLM`.
They implement the same interfaces the real connectors do — the demos are
exercising production code paths, not test doubles of the agents.

## Sample documents
`DEMOS/samples/*.txt` — sample invoice / bill-of-lading text used by the
logistics document parser (swap in real PDFs; the parser handles both).
