# Client Instances

One folder per client. Each contains the full runtime config, encrypted
secrets, deployment status, customizations and billing record.

## Creating a new client
1. Copy `_TEMPLATE_new_client/` → `client_00X_clientname/`
2. Fill `config.yaml` (vertical, integrations, tuning knobs)
3. Create `secrets.env` from the vertical's env template, then encrypt:
   `sops -e secrets.env > secrets.env.enc` (commit only the .enc)
4. Run onboarding checklist → update `deployment_status.md`
5. Add the client row to `../clients_database.xlsx`

## Security rules
- **Never commit plaintext secrets.** `secrets.env` here is a placeholder;
  real values live in AWS Secrets Manager / SOPS-encrypted files.
- Custom code goes in `customizations.py` (reviewed in PRs).
- Every instance has its own API keys; rotate on offboarding.

## Folders
| client_001_acme_dental | Dental clinic (US, 2 locations) — booking + insurance intake |
| client_002_remax_denver | Real estate brokerage (Denver, 8 agents) — lead pipeline |
