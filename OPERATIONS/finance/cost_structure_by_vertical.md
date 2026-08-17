# Cost Structure by Vertical (summary — full math in xlsx)

## Medical/Dental (per client/mo)
- Infrastructure: $60-120 · LLM: $40-90 · Twilio: $30-80
- Insurance API: $50-150 · Support/tuning: $250-400
- **Total: $430-840** vs $750-1,800 platform fee

## Real Estate (per client/mo)
- Infrastructure: $60-120 · LLM: $50-110 · Twilio/email: $40-90
- MLS fees: $50-150 · CRM: $0-100 · Support: $300-450
- **Total: $500-1,020** vs $1,000-2,500 platform fee

## Logistics (per client/mo)
- Infrastructure: $120-250 · LLM (doc-heavy): $150-400 · Doc infra: $50-120
- Carrier APIs: $50-150 · Support/data: $450-700
- **Total: $820-1,620** vs $2,000-4,500 platform fee

## Biggest risk line item
LLM tokens (logistics especially). Mitigations: token caching, prompt
compression, batch off-peak processing, per-client token budgets with
alerts at 80%.
