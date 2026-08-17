# Secrets Management Policy

## Principles
1. **No secrets in git.** Ever. Not even "temporarily".
2. **One secret store per environment** — AWS Secrets Manager (default) or GCP Secret Manager.
3. **Per-client encryption** — each client instance has its own keys so a breach is contained.
4. **Rotation** — secrets are rotated on a schedule (default 90 days) and on personnel changes.

## What counts as a secret
- API keys (OpenAI, Anthropic, Twilio, HubSpot, Salesforce, carrier APIs...)
- Database credentials, JWT signing keys, webhook signing secrets
- Client `secrets.env` files (stored encrypted: `sops -e secrets.env`)

## Tooling

### Local development
```bash
# Encrypt a client secrets file with SOPS + age
sops -e CLIENT_MANAGEMENT/client_instances/client_001_acme_dental/secrets.env \
    > CLIENT_MANAGEMENT/client_instances/client_001_acme_dental/secrets.env.enc

# Decrypt for local work (never commit the decrypted file)
sops -d secrets.env.enc > /tmp/secrets.env
```

### Kubernetes (production)
Use **external-secrets** with AWS Secrets Manager as the provider:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: stratum-secrets
  namespace: stratum
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: SecretStore
  target:
    name: stratum-secrets
  dataFrom:
    - extract:
        key: stratum/production
```

### Rotation checklist
- [ ] Rotate LLM provider keys (OpenAI/Anthropic org-level keys)
- [ ] Rotate channel keys (Twilio, Slack, SendGrid)
- [ ] Rotate CRM keys (HubSpot private apps, Salesforce connected apps)
- [ ] Rotate JWT signing secret (all clients re-issued)
- [ ] Rotate DB passwords (RDS rotation via Secrets Manager)

## Incident response
If a secret is suspected leaked:
1. Rotate the key immediately (no waiting for approval).
2. Open a security incident ticket (see OPERATIONS/processes/incident_escalation_process.md).
3. Audit access logs of the secret store for the last 30 days.
4. Post-mortem within 72h; update this policy if a gap was found.
