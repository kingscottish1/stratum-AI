# 🏢 Stratum AI — Multi-Stratum AI Platform

> **Built by kingscottishDEV · N.A.S — Nexus Audit Security** — full-stack AI operations platform:
> Stratum Care (clinics) · Stratum Realty (brokerages) · Stratum Freight (logistics).

**Stratum AI** is a complete, production-grade platform: FastAPI backend with
a real database (encrypted at rest), a full single-page frontend, Bring-Your-Own-LLM
provider abstraction, per-client encrypted secrets, JWT auth, audit logging —
and runnable agent suites for three verticals. No secrets are hardcoded anywhere;
everything sensitive comes from `.env` / your secret store.

## ⚡ Quickstart — easiest (install & run scripts)
**Windows:** double-click `install.bat` once, then `run.bat` (or run them from cmd).
**Linux / macOS:** `bash install.sh` once, then `bash run.sh`.

The installer creates a virtual environment, installs dependencies and
generates `.env` with fresh secrets — **DEMO_MODE=ON** so you can test
immediately (demo mode is owner-testing only). `run.bat` / `run.sh` start
the server and open your browser.

Then:
1. Register the **owner** account at http://localhost:8000
2. On the dashboard click **"load demo data"** (demo mode)
3. Open the **Agents console** → pick a client & agent → send a message
4. Optional: bring your own LLM — set `LLM_PROVIDER` + `LLM_API_KEY` in
   `.env`, set `DEMO_MODE=false` for real mode, restart.

Also included: `test.bat` / `test.sh` run the full test suite.

### Manual (exactly what the scripts do)
```bash
pip install -r requirements.txt -r requirements-dev.txt
bash scripts/setup_env.sh        # or: python scripts/generate_env.py
uvicorn CORE_AGENT_INFRASTRUCTURE.api.main:app --reload --port 8000
#    → Frontend:  http://localhost:8000   (register the owner account)
#    → Health:    http://localhost:8000/healthz
#    → API docs:  http://localhost:8000/docs
```

## 🧠 Bring Your Own LLM (plug & play)
No local models required, no vendor lock-in — bring any brain:

| Provider | `LLM_PROVIDER=` | Key needed? |
|---|---|---|
| OpenAI | `openai` | `LLM_API_KEY` |
| Anthropic | `anthropic` | `LLM_API_KEY` |
| Azure OpenAI | `azure` | `LLM_API_KEY` + `LLM_BASE_URL` (deployment URL) |
| OpenRouter | `openrouter` | `LLM_API_KEY` |
| Groq | `groq` | `LLM_API_KEY` |
| Together | `together` | `LLM_API_KEY` |
| Ollama (local) | `ollama` | no key — runs on your machine/GPU |
| Any OpenAI-style endpoint | `openai_compatible` | `LLM_API_KEY` + `LLM_BASE_URL` |

Plus: `LLM_MODEL_FAST` / `LLM_MODEL_QUALITY` for two-tier routing,
`LLM_FALLBACK_PROVIDER` for automatic failover, `LLM_EXTRA_HEADERS` for
custom headers. Adapters live in `CORE_AGENT_INFRASTRUCTURE/llm/providers.py`
(pure HTTP — no vendor SDKs).

## 🔐 Security model
- **No hardcoded secrets anywhere.** All config via environment/secret store
  (`.env.example` documents every variable; `scripts/setup_env.sh` generates keys).
- **Database encrypted at rest:** integration API keys use AES-256-GCM
  (`db/crypto.py`) — plaintext never touches the DB; the API never returns it.
- **Auth:** PBKDF2-HMAC-SHA256 password hashing (600k iterations, salted) +
  stdlib HS256 JWTs with expiry; roles: owner / admin / viewer.
- **Audit trail:** every sensitive action (logins, secret changes, billing,
  deletions) is recorded in `audit_logs` and visible in the UI.
- **Production self-checks:** config validation refuses to boot without
  `DATABASE_URL`, `JWT_SECRET`, `ENCRYPTION_KEY`, `LLM_PROVIDER`(+key).
- **Demo mode is owner-testing only:** `DEMO_MODE=true` gates seed data and
  mock connectors; mocks refuse to load when `STRATUM_ENV=production`.

## 🧱 Stack
Backend: FastAPI + SQLAlchemy 2 + SQLite (dev) / PostgreSQL (prod) ·
Frontend: dependency-free SPA (vanilla JS, served by the API) ·
LLM: BYO-LLM provider layer · Workers: `CORE_AGENT_INFRASTRUCTURE/workers`.

## 📁 Layout
```
stratum-ai/
├── CORE_AGENT_INFRASTRUCTURE/   # Stratum Core engine
│   ├── config.py                # env-driven config, prod validation
│   ├── llm/                     # BYO-LLM providers + factory + router
│   ├── db/                      # models, sessions, AES-256-GCM encryption
│   ├── security/                # hashing, JWT, audit
│   ├── api/                     # routers, deps, webhooks, agent runtime
│   ├── frameworks/              # BaseAgent + LangChain/CrewAI setups
│   ├── shared_tools/            # calendar, CRM, docs, channels, DB connectors
│   └── workers/                 # worker + migrations entrypoints
├── web/                         # full frontend (SPA: dashboard, clients,
│                                #   agents console, integrations, audit…)
├── VERTICALS/                   # Stratum Care / Realty / Freight agents + workflows
├── DEPLOYMENT_INFRASTRUCTURE/   # docker, k8s, terraform, ci_cd, monitoring, security
├── CLIENT_MANAGEMENT/           # onboarding docs, client instances, support
├── DEMOS/                       # gated demo runners (owner testing only)
├── SALES_MARKETING/             # case studies, decks, landing pages, brand kit
├── OPERATIONS/                  # finance, hr, legal, reporting, processes, playbooks
├── tests/                       # pytest suite (crypto, auth, API, agents, LLM)
├── docs/  scripts/              # architecture docs, env/bootstrap scripts
└── .env.example                 # template — copy to .env, fill YOUR values
```

## 🔑 First run (owner setup)
1. `bash scripts/setup_env.sh` → creates `.env` with fresh keys
2. `uvicorn CORE_AGENT_INFRASTRUCTURE.api.main:app --reload --port 8000`
3. Open http://localhost:8000 → **Create account** (first account = owner)
4. Set `DEMO_MODE=true` to load sample clients via the UI (owner testing),
   or create real clients and add their encrypted integration credentials.

## 🧪 Tests
```bash
pytest tests/ -v
```
Covers: AES-256-GCM encryption, JWT, password hashing, config validation,
BYO-LLM provider payloads, full API flows (auth → client → encrypted
integration → workflow toggle → agent run → audit), vertical agents,
webhook signature verification, demo-mode gating.

## ⚠️ Before production
- Set `STRATUM_ENV=production`, `DEMO_MODE=false`, real `DATABASE_URL`
  (PostgreSQL), real `JWT_SECRET` / `ENCRYPTION_KEY` in your secret store.
- Point `LLM_PROVIDER`/`LLM_API_KEY` at your model provider of choice.
- Replace sample data (client_001/002, demo credentials), brand assets,
  and `stratumai.com` placeholders.

© 2026 Stratum AI · Built by **kingscottishDEV · N.A.S**
