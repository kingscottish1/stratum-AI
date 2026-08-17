# Stratum AI — Platform Architecture

## Layer model
```
┌─────────────────────────────────────────────────────────────┐
│  CHANNELS        SMS · WhatsApp · Voice · Email · Webchat    │
│                  (Twilio, SMTP, webhooks)                    │
├─────────────────────────────────────────────────────────────┤
│  API LAYER       FastAPI · JWT auth · webhook dispatch ·     │
│                  rate limiting · metrics · structured logs   │
├─────────────────────────────────────────────────────────────┤
│  ORCHESTRATION   vertical orchestrators route by intent →    │
│                  specialist agents (CrewAI crews on demand)  │
├─────────────────────────────────────────────────────────────┤
│  AGENTS          BaseAgent subclasses per vertical:          │
│                  care / realty / freight suites              │
├─────────────────────────────────────────────────────────────┤
│  TOOLS           calendar, CRM, documents, comms, DB —       │
│                  every connector behind an interface         │
├─────────────────────────────────────────────────────────────┤
│  DATA            Postgres (records) · Redis (memory/queues)  │
│                  · S3/GCS (documents) · Secrets Manager      │
└─────────────────────────────────────────────────────────────┘
```

## Key decisions
1. **One core, many verticals.** All agents extend `BaseAgent`, all
   connectors implement shared interfaces (`CRMInterface`, calendar,
   TMS/ledger contracts). A new vertical = new agent suite + config,
   not a new platform.
2. **LLM routing by task.** ~70-80% of traffic (classify, extract,
   summarize) runs on fast/cheap models; only generation/negotiation uses
   quality models. This is the single biggest margin lever.
3. **Per-client isolation.** Every client gets config.yaml + encrypted
   secrets + customizations.py + metrics. Multi-tenant by process, not by
   shared mutable state.
4. **Degradation over failure.** Rate limits retry with backoff; no-LLM
   fallbacks keep the pipeline running; anything unresolvable escalates to
   a human handoff with full context.
5. **Shadow → live.** Every workflow ships with a shadow mode (AI
   recommends, human approves) so clients adopt with zero risk.

## Request lifecycle (example: clinic booking via SMS)
1. Twilio webhook → API layer (signature verified, rate-limited)
2. Worker pulls job → ClinicOrchestrator classifies intent ("book")
3. AppointmentAgent extracts details → checks Mock/Google Calendar
4. Books event + PMS record → confirmation rendered from templates
5. Outcome logged to metrics + conversation store

## Scalability
- Stateless API/worker pods (K8s + HPA), Redis for queues/memory,
  Postgres for records, S3 for documents. Batch work (replays, reports)
  runs on scheduled workers. Terraform provisions AWS (default) or GCP.
