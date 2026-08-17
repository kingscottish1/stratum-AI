# Support Troubleshooting Guide

## 1. Agent not responding to messages
- Check instance health: `GET /healthz` → expect `{"status":"ok"}`
- Check worker queue depth (Redis): `LLEN stratum:webhooks`
- Check LLM provider status + API key validity
- Verify webhook still configured (Twilio console → Messaging → Webhooks)

## 2. Slow responses (>10s)
- LLM latency spike? Router should auto-fallback to fast model
- Large conversation context? Context truncation enabled by default
- Worker saturation? Increase replicas (`kubectl scale deploy/agent-worker`)

## 3. Wrong information in replies
- Pull the transcript: every conversation is logged with full payloads
- Check the agent version + prompt template version at that timestamp
- Replay the transcript against current config to verify fix

## 4. Integration sync failures
- CRM/PMS API key expired or rotated → re-store in secrets
- Webhook signature mismatch → verify shared secret matches
- Rate limits → check integration health in monitoring dashboard

## 5. Billing discrepancies
- Reference billing_record.xlsx per client
- Verify MRR tier + add-ons vs SOW; adjust next invoice

## Always capture
Client ID · timestamp · expected vs actual · logs (kubectl logs / Grafana) ·
screenshots · whether reproducible.
