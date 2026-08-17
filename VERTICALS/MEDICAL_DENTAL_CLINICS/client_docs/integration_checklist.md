# Clinic Integration Checklist

Use this during onboarding to track every integration point.

## Calendar
- [ ] Google Calendar shared (service account) OR
- [ ] Dentrix eServices credentials OR
- [ ] EagleSoft API credentials OR
- [ ] Open Dental REST (port 9443) credentials
- [ ] Clinic hours + holidays configured
- [ ] Appointment types + durations mapped (cleaning=30m, new patient=60m...)
- [ ] Providers/rooms assigned

## Communication
- [ ] Twilio number purchased & configured (SMS + WhatsApp)
- [ ] SMS templates approved by clinic owner
- [ ] Email sending verified (SPF/DKIM for clinic domain)
- [ ] Voice greeting script approved
- [ ] Slack channel for handoffs created

## Insurance
- [ ] Clearinghouse account active (Stedi / Claim.MD / other)
- [ ] API credentials in secrets store
- [ ] Copay/deductible table loaded for top 10 carriers

## PMS data
- [ ] Patient export (or API) for matching phone -> patient
- [ ] Duplicate record policy agreed
- [ ] Appointment sync direction agreed (calendar <-> PMS)

## Compliance
- [ ] HIPAA BAA signed
- [ ] Audit logging enabled
- [ ] Data retention policy agreed
- [ ] Staff training on AI escalation (who gets handoff alerts)

## Sign-off
- [ ] Test scenarios passed (see setup_guide Phase 2)
- [ ] Client approved go-live date
