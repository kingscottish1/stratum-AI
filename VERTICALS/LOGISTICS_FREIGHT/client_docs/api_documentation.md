# Logistics Vertical — API Documentation

The logistics agents expose a REST API per client instance.

## Base URL
`https://api.stratumai.com/v1/clients/{client_id}/logistics`

## Auth
Bearer token (JWT) issued per client instance with scopes:
`documents:ingest`, `invoices:read`, `invoices:write`, `reports:read`.

## Endpoints

### Ingest a document
`POST /documents`
```
Content-Type: multipart/form-data
file: <pdf or image>
source: email | api | fax | edi
```
Response: `{document_id, document_type, confidence, fields}`

### List exceptions
`GET /exceptions?severity=high&from=2026-07-01&to=2026-08-01`
Response: `[{id, type, severity, shipment_reference, reason, detected_at, status}]`

### Resolve an exception (human override)
`POST /exceptions/{id}/resolve`
```
{ "resolution": "credit_requested", "note": "Carrier agreed via phone" }
```

### Invoices
`GET /invoices?status=held` — list held invoices with reasons
`POST /invoices/{id}/release` — approve payment after human review

### Reports
`GET /reports/weekly_carrier_scorecard?period=last_week` — JSON or ?format=pdf

## Webhooks (outbound)
- `exception.created` — new high-severity exception
- `invoice.held` — invoice held with reasons
- `dispute.resolved` — recovery recorded
- `report.ready` — scheduled report available

## Rate limits
- 60 req/min per token (ingest: 10/min)
- Webhook retries: exponential backoff, max 5 attempts

## Error codes
| Code | Meaning |
|---|---|
| 400 | Malformed payload |
| 401 | Invalid/expired token |
| 403 | Scope missing |
| 404 | Resource not found |
| 409 | Duplicate document (idempotency key) |
| 429 | Rate limited |
| 500 | Internal error (retry with backoff) |
