# Exception Types Guide

Everything the exception system watches, and what happens next.

## Detection rules
| Exception | Rule | Severity | Default action |
|---|---|---|---|
| missed_pickup | pickup appointment passed, no pickup status | high | Alert ops + carrier follow-up |
| missed_delivery | delivery appointment passed, not delivered | high | Alert ops + customer comms |
| scan_gap | no status scan for > 24h | medium | Carrier check-in email |
| dwell_time | stopped at a node > threshold (config) | medium | Warehouse inquiry |
| late_risk | ETA slips > 4h past committed | medium | Customer notice + expedite offer |
| temperature | reefer temp outside band (via telematics) | high | Immediate alert + protocol |
| missing_pod | delivered but no POD within 48h | low | Auto POD chase email |
| document_gap | rate con/BOL missing for pending shipment | low | Auto request to broker/carrier |

## Dispute & claim types
| Type | Trigger | Package |
|---|---|---|
| Overcharge | invoiced > contracted + 2% | rate con + invoice + lane history |
| Duplicate invoice | same reference + amount within 30 days | both invoices + payment status |
| Unauthorized accessorial | billed accessorial not on BOL | BOL + rate con + contract addendum |
| Service failure | late pickup/delivery per contract | tracking + appointment records |
| OS&D | overage/shortage/damage at delivery | POD annotations + photos + BOL |

## Escalation matrix
- **Auto-resolve** (low severity, < auto limit): AI acts, logs everything.
- **Alert + wait** (medium): AI prepares the package, human clicks send.
- **Human only** (high severity, > auto limit, claims > threshold): Slack +
  email alert with prepared context.

## KPIs tracked
- Detection latency (event → detection)
- Auto-resolution rate
- Dispute recovery $ and recovery rate
- Repeat-exception rate per carrier (feeds the scorecard)
