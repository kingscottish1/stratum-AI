# Deployment Status — Remax Denver

| Stage | Status | Date |
|---|---|---|
| Contract signed | ✅ | 2026-05-30 |
| Access received | ✅ | 2026-06-05 |
| Integration built | ✅ | 2026-06-12 |
| Historical replay | ✅ | 2026-06-15 |
| Shadow mode | ✅ | 2026-06-18 |
| **LIVE** | ✅ | 2026-06-20 |

## Current environment
- Vertical: real_estate_brokerages
- Cloud: AWS us-east-1 (EKS)
- Instances: api + 1 worker
- Monitoring: Grafana /stratum/clients/client_002

## Launch log
- 2026-06-20: go-live; hot-lead alert < 5 min, viewings auto-booked
- 2026-07-08: sequence v2 (viewed_3d + offer_nudge) enabled
- 2026-07-22: ZipForm prefill pilot with 3 agents
