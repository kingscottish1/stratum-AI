# Client Onboarding Checklist

One checklist per client. Owner: Onboarding Manager. Target: 14 days.

## Stage 1 — Contract & Kickoff (Days 0-2)
- [ ] NDA signed (nda_template.docx)
- [ ] SOW signed (sow_template.docx) — scope, fees, timelines, SLAs
- [ ] Kickoff call held; decision-makers + technical contact identified
- [ ] Requirements discovery completed (integration_discovery_template.xlsx)
- [ ] Client folder created under client_instances/ from _TEMPLATE_new_client/
- [ ] Billing record initialized (billing_record.xlsx)

## Stage 2 — Access & Integrations (Days 2-7)
- [ ] Vertical integration checklist completed (VERTICALS/*/client_docs/integration_checklist.md)
- [ ] All API credentials received and stored ENCRYPTED (sops) in secrets.env
- [ ] Test environment access confirmed
- [ ] Data migration/export mapped (history for tuning)
- [ ] Webhooks configured (channels: sms/whatsapp/email/webhook)
- [ ] Compliance forms (HIPAA BAA / GDPR DPA) signed where applicable

## Stage 3 — Configuration & Tuning (Days 7-10)
- [ ] config.yaml reviewed + approved by client
- [ ] Prompt templates customized to client's brand voice
- [ ] Message copy approved by client (SMS/email/voice)
- [ ] Historical replay done (50-100 conversations) — accuracy report shared
- [ ] Test scenarios passed (client team + agency QA)

## Stage 4 — Shadow & Go-Live (Days 10-14)
- [ ] Shadow mode enabled (AI advises, human approves) — 48h min
- [ ] Go-live decision meeting with client
- [ ] Production secrets rotated + deployed
- [ ] Monitoring alerts configured for the instance
- [ ] Client trained on dashboard + Slack channel
- [ ] First weekly metrics report scheduled
- [ ] deployment_status.md updated to LIVE

## Stage 5 — Post-launch (Days 15-30)
- [ ] Day-7 health check call
- [ ] Day-30 business review: metrics vs baseline
- [ ] Handover to account manager (support_templates/sla_agreement.md)
