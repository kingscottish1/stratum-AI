# Clinic Vertical — Client Setup Guide

This guide walks through what happens between *signed contract* and *live
AI receptionist*. Most clinics go live in **7-14 days**.

## Phase 0 — Kickoff (Day 0-1)
- [ ] Intro call: confirm scope (booking + reminders + insurance intake + follow-up)
- [ ] Collect sign-offs: HIPAA BAA, data handling agreement
- [ ] Grant access list (see integration_checklist.md)

## Phase 1 — Integration (Day 1-5)
1. **Calendar/PMS**: we connect Google Calendar (or Dentrix/EagleSoft/Simplicity).
   - Shared calendar for the AI or direct PMS API access.
2. **Phone/SMS**: you port or provide a Twilio number (or we issue one).
3. **Insurance verification**: clearinghouse API credentials (Stedi or existing vendor).
4. **Templates**: we adapt greeting scripts, SMS reminders and intake emails
   to your brand voice (edit files in `templates/`).

## Phase 2 — Training & testing (Day 5-8)
- We replay 50-100 real past booking conversations to tune the agents.
- You get a test phone number; try booking, rescheduling, insurance Q&A.
- You approve the final message wording.

## Phase 3 — Shadow mode (Day 8-10)
- AI handles messages, but all replies are CC'd to your front desk (Slack).
- No appointments are booked without staff approval.

## Phase 4 — Live (Day 10-14)
- AI books appointments in real time (configurable: auto-book or confirm-first).
- Weekly metrics report starts (see dashboard): bookings, no-show rate,
  response time, saved staff hours.

## Ongoing
- Monthly tune-up call; quarterly business review with ROI numbers.
- Changes to hours/services/holdiays: message us on Slack or email support
  (see support_templates/).
