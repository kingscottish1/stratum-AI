# MLS Integration Guide

The agency reads listings through your MLS board's RESO Web API (or IDX).

## What we need from you
1. **RESO Web API credentials** — most boards issue via your MLS provider:
   - API key + secret (OAuth2 client credentials)
   - Data dictionary version (e.g. RESO 1.7 / 2.0)
   - Your board's base URL (e.g. `https://api.mlsgrid.com`)
2. Or **IDX feed credentials** (Rets/IDX broker), if your board doesn't
   offer RESO yet.

## Access levels (pick one)
| Level | What we can do | Typical for |
|---|---|---|
| Read-only listings | search + match + alerts | All clients |
| + Lead events | portal lead notifications | Clients with portal spend |
| + Transaction data | prefill forms, pipeline tracking | Closing-assist clients |

## Data handling
- Listings are cached for ≤ 24h to respect MLS data rules.
- We never resell or publish listing data outside your client instance.
- Watermark/branding rules of your MLS apply to our property emails.

## Checklist
- [ ] RESO credentials in secret store
- [ ] Test query returns sample listings (QA)
- [ ] Photo CDN URLs confirmed accessible
- [ ] Listing URL deep-link format confirmed
- [ ] Compliance review passed (board rules)
