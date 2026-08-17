# Clinic Vertical — FAQ

**Q: Does the AI actually book appointments in my calendar?**
Yes. When auto-book is on, confirmed bookings create real calendar events and
PMS records in seconds. You can switch to "confirm-first" mode where a staff
member approves each booking from Slack.

**Q: What happens if a patient asks something weird?**
The orchestrator routes to the best agent; if the AI can't help after two
attempts, it escalates to your front desk with the full conversation context.

**Q: Is this HIPAA compliant?**
The platform is built HIPAA-aware: encryption at rest/in transit, per-client
secrets, full audit logs, and we sign a BAA. Data stays in your region (US/EU).

**Q: Can it handle multiple providers and locations?**
Yes. Slots are checked per provider/location; patients can pick.

**Q: What about no-shows?**
Our reminder cadence (48h/24h/2h) typically cuts no-shows 40-60%. Follow-up
agent rebooks missed appointments automatically.

**Q: Does it replace my front desk?**
No — it absorbs the repetitive 80% (booking, reminders, insurance intake) so
your team handles the human 20%. You control everything via Slack.

**Q: How fast is it live?**
Most clinics go live in 7-14 days (see setup_guide.md).

**Q: What if the AI makes a mistake?**
Every interaction is logged; any message can be replayed. False bookings are
rare (<1% in production runs) and auto-undo is available. We do a weekly
accuracy review with you.
