# Logistics Vertical — Client Setup Guide

Go-live target: **2-4 weeks** (data-heavy vertical — integration depth matters).

## Phase 0 — Discovery (Day 0-3)
- Map document flows: what arrives, where, in what format (email/EDI/fax/portal)
- Map the exception landscape: which exceptions cost the most today
- Confirm TMS + accounting stack and access levels

## Phase 1 — Integrations (Day 3-12)
1. **TMS**: TMW, 4Front, Logistic Manager (or client middleware) — shipments,
   orders, exceptions.
2. **Accounting**: QuickBooks / Sage Intacct / NetSuite — bills, holds, disputes.
3. **Carrier APIs**: FedEx/UPS/DHL for tracking and rate checks (as needed).
4. **Email ingestion**: dedicated inbox or label routing for documents.

## Phase 2 — Calibration (Day 12-18)
- We replay 200+ historical invoices through the matcher; tune tolerance and
  rate-table sync.
- Exception rules calibrated to your service contracts (late thresholds,
  POD windows).
- Compliance review of auto-dispute limits with your AP manager.

## Phase 3 — Shadow → Live (Day 18-28)
- Shadow: matcher runs in "advise only" — team sees recommendations, AI holds
  nothing.
- Live: auto-match + auto-hold for invoices; auto-resolution for low-severity
  exceptions; high-severity always alerts a human.
- Weekly reviews for first month; monthly scorecard after.

## Ongoing
- Rate table maintenance handled by AI (rate cons parsed automatically).
- Quarterly ROI review: disputes recovered, hours saved, late fees avoided.
