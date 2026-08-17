# Clinic Vertical — Troubleshooting

## Symptom: patient says they booked but no event in calendar
1. Check worker logs: `kubectl logs deploy/clinic-agent -n stratum | grep appointment`
2. Confirm `CALENDAR_MODE` and service account have write access to the calendar.
3. Check Twilio delivery status in the console (message may have failed).

## Symptom: reminders not sending
- Confirm `REMINDER_HOURS` matches the scheduled cron (worker).
- Check SMTP credentials / Twilio number has SMS capability.
- Verify patient phone numbers are E.164 (+1...).

## Symptom: insurance verification "unknown"
- Vendor API down? Check `INSURANCE_VENDOR` and credentials.
- The clearinghouse may not cover that carrier — falls back to manual queue.

## Symptom: AI replies too slow (>10s)
- Check LLM provider status; we fall back to a faster model automatically.
- Large patient context? We cap context per turn.

## Symptom: duplicate patient records
- Phone matching is fuzzy; confirm match rules with the clinic. We dedupe
  by phone + DOB before creating records.

## Symptom: AI booked wrong time
- Slot conflict race (two patients, same slot). We re-check availability at
  booking time; enable "confirm-first" mode to prevent.

## Escalation
- Slack `#stratum-support` or email support@stratumai.com with:
  client ID, timestamp, patient reference, and screenshots/log snippet.
- SLA: P1 (system down) 2h, P2 (degraded) 8h, P3 (question) 24h.
