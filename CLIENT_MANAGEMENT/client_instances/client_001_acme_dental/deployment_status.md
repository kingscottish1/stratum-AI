# Deployment Status — Acme Dental

| Stage | Status | Date |
|---|---|---|
| Contract signed | ✅ | 2026-04-28 |
| Access received | ✅ | 2026-05-02 |
| Integration built | ✅ | 2026-05-08 |
| Historical replay | ✅ | 2026-05-10 |
| Shadow mode | ✅ | 2026-05-12 |
| **LIVE** | ✅ | 2026-05-15 |

## Current environment
- Vertical: medical_dental_clinics
- Cloud: AWS us-east-1 (EKS)
- Instances: api + 2 workers
- Monitoring: Grafana /stratum/clients/client_001

## Launch log
- 2026-05-15: go-live with auto-book on, 2 locations, voice AI receptionist
- 2026-06-12: insurance intake module enabled (Stedi)
- 2026-07-01: recall campaign enabled; no-show rate 21% → 9%
