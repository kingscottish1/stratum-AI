# Logistics Vertical — FAQ

**Q: Does the AI actually pay invoices?**
No. It *approves* clean invoices for payment and *holds* disputed ones with
reasons. Your AP team (or the accounting system's approval flow) executes
the payment. Auto-dispute submission is capped at a per-client limit.

**Q: What if the AI holds something incorrectly?**
Every hold has a reason and linked evidence. Your team can release any hold
with one click. We calibrate the tolerance (2% default) with your AP team
during onboarding, and we review hold accuracy weekly.

**Q: Which documents can it read?**
PDFs, scanned images (OCR), and text files: invoices, BOLs, PODs, rate
confirmations, exception notices. EDI can be connected separately.

**Q: How do you connect to our TMS?**
TMW, 4Front, Logistic Manager — or any TMS with a REST API. If your TMS has
no API, we connect through its database read replica or file exports.

**Q: Is this going to mess with our accounting audit?**
We keep a complete audit trail: every document, decision, and evidence
attachment is versioned and exportable. The system is built to make audits
*easier* — everything is documented by default.

**Q: What happens when a carrier disputes our dispute?**
The resolver drafts an appeal with new evidence (tracking history, signed
POD, contract clause) and routes it for review.

**Q: How do you price it?**
See costs_margins_logistics.md — implementation + monthly platform fee.
ROI is typically disputes recovered + AP hours saved + late-fee avoidance,
which usually exceeds the fee in month one.

**Q: How long does implementation take?**
2-4 weeks depending on integration depth (TMS + accounting + carrier APIs).
