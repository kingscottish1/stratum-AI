# Changelog

All notable changes to the Stratum AI platform.

## [1.1.0] — 2026-08-03 — Brand kit & sales pitch
- **Brand assets** (`SALES_MARKETING/brand/`): horizontal logo lockup,
  dark logo, app icon, social banner + expanded brand guidelines.
- **Positioning & messaging**: positioning statement, elevator pitches
  (15/30/60-120s), message house per vertical, proof-point bank,
  social media kit.
- **Target market**: ICP profiles for all three verticals (firmographics,
  pains, budget, triggers, channels), market sizing (TAM/SAM/SOM),
  outbound targeting playbook.
- **Sales pitch**: full 15-20 min pitch script, objection handling (10
  objections), generated `company_one_pager.pdf` + `company_master_pitch.pptx`
  (11 slides, branded).

## [1.0.1] — 2026-08-02 — Easy install & run
- Added install.bat / run.bat / test.bat (Windows) and install.sh /
  run.sh / test.sh (Linux/macOS) — one-command install + run with
  auto-generated .env (DEMO_MODE=ON for instant testing).
- Added scripts/generate_env.py cross-platform .env generator.
- App now auto-loads .env from the repo root at startup.

## [1.0.0] — 2026-08-02 — Full-stack release (kingscottishDEV · N.A.S)
- FastAPI backend + SPA frontend, real DB (SQLite/Postgres), JWT auth,
  roles, audit logging.
- AES-256-GCM encryption at rest for integration secrets; no hardcoded
  secrets; production config validation.
- Bring-Your-Own-LLM provider layer (8 providers, fast/quality tiers,
  fallback).
- Demo mode owner-testing only; mocks refuse to load in production.
- 54-test suite covering crypto, auth, API, agents, LLM providers.

## [0.2.0] — 2026-08-02 — Rebrand
- Renamed platform Stratum AI (Care / Realty / Freight; engine Stratum Core).

## [0.1.0] — 2026-07
- Initial scaffold: engine, three verticals, deployment, client management,
  sales & marketing, operations.
