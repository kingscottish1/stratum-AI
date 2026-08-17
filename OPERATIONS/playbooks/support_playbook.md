# Support Playbook — Stratum AI

## Triage (first 15 minutes)
1. Severity: P1 (down/data loss) → P2 (major broken) → P3 (minor) → P4 (question).
2. Reproduce: client ID, timestamp, transcript/logs, expected vs actual.
3. Classify: config? integration? agent accuracy? infra? billing?

## Response templates
- **Ack (P1)**: "Hi {name} — we're on it. {engineer} is investigating and
  we'll update you every 60 minutes until resolved. Current status: ..."
- **Ack (P2/P3)**: "Thanks — ticket {id} logged at {priority}. Target
  response {window}. Any reproduction steps you can share help us move faster."
- **Resolution**: "Fixed in {version}. Root cause: {cause}. Prevention: {prevention}."

## Common fixes
| Symptom | Likely cause | Fix |
|---|---|---|
| Agent not replying | webhook misconfigured / key rotated | verify Twilio webhook + secrets |
| Slow replies | LLM spike / context bloat | router fallback should engage; check worker replicas |
| Wrong info | prompt version / stale config | replay transcript, check config.yaml, redeploy |
| Integration sync fail | API key expiry / rate limit | rotate key in Secrets Manager, check monitor |
| Booking not in PMS | PMS sync error after calendar book | retry sync job; ticket if persistent |

## Escalation ladder
Support → AI Ops lead → CTO → CEO (P1/client-facing).
P1 page 24/7; P2 within business hours; everything logged in the ticket.

## After the fire
- Post-mortem for P1/P2 within 72h: timeline, root cause, prevention, owner.
- Add the fix to this playbook so it becomes a 5-minute fix next time.
- Update the client's performance_metrics.json notes and the QBR deck.

## Guardrails
- Never promise a fix time you can't keep; commit to update cadence instead.
- Never blame the client's data; say "the model needs more of it" instead.
- Every handoff must include the full transcript — context is the product.
