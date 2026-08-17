# Incident & Escalation Process

## Severity definitions
- **P1 Critical** — platform down, data loss, booking/payment systems broken
- **P2 High** — major feature broken with workaround; one client severely degraded
- **P3 Normal** — minor bug, cosmetic, single-user issue
- **P4 Low** — question, enhancement

## Flow
1. **Detect** — monitoring alert OR client report (Slack #stratum-support)
2. **Triage (15 min)** — on-call confirms severity, opens ticket
3. **Fix** — P1: 4h fix target; P2: 24h; P3: 3 business days
4. **Communicate** — P1: status updates every 60 min to affected clients
5. **Post-mortem (72h)** — timeline, root cause, prevention, owner

## On-call
- Rotation: engineers + AI ops; P1 pages: 24/7
- Handoff: written summary + open items in ticket

## Data/security incidents (P1 always)
1. Contain: rotate keys, isolate instance
2. Notify: client within 72h (GDPR); BAA/HIPAA notifications per contract
3. Preserve evidence: logs, access records
4. Post-mortem + policy update (see security/secrets_management.md)

## Escalation ladder
Support → AI Ops lead → CTO → CEO (client-facing, P1 only)

## Post-incident
- Ticket closed with prevention items tracked in the board
- Monthly review of incident trends at the MBR
