# GDPR & Data Protection Playbook

## Roles
- **Agency** = Processor (we process client data under the client's
  instructions, per DPA).
- **Client** = Controller (owns the data; we sign their DPA or provide ours).

## What we process
- Patient/lead/customer contact data (via CRM, calendars, channels)
- Business documents (invoices, PODs, contracts) for logistics clients
- Conversation content (SMS/email/voice transcripts) for tuning & QA

## Requirements we meet
- **Lawful basis**: processing under contract + legitimate interest;
  documented per client.
- **DPA**: signed with every client (see client contract template).
- **Data minimization**: we only pull the fields the workflow needs.
- **Retention**: transcripts 90 days default, then archived/anonymized
  (configurable per client contract).
- **Sub-processors**: OpenAI/Anthropic, Twilio, AWS/GCP — listed in DPA;
  EU transfer mechanisms (SCCs) in place where applicable.
- **DSARs**: automated pipeline — any subject access / erasure request
  fulfilled within 30 days (logged, tracked, reported to client).
- **Breach process**: notify client within 72h of confirmed breach
  (see incident_escalation_process.md).
- **EU clients**: data residency option (eu-central-1 / europe-west1);
  no US data egress without DPA + SCCs.

## Checklist at onboarding
- [ ] DPA signed
- [ ] Data inventory sheet completed (what/where/retention)
- [ ] Sub-processor list shared
- [ ] DSAR contact named
- [ ] Retention configured per contract
