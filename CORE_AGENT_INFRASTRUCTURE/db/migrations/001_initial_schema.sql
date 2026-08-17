-- Stratum AI — initial schema (PostgreSQL)
-- Applied via: python -m CORE_AGENT_INFRASTRUCTURE.workers.migrate (or psql)

CREATE TABLE IF NOT EXISTS client_instances (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    vertical      TEXT NOT NULL,
    environment   TEXT NOT NULL DEFAULT 'production',
    status        TEXT NOT NULL DEFAULT 'onboarding',
    go_live_date  DATE,
    config        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS conversations (
    id            BIGSERIAL PRIMARY KEY,
    client_id     TEXT NOT NULL REFERENCES client_instances(id),
    channel       TEXT NOT NULL,
    session_id    TEXT NOT NULL,
    direction     TEXT NOT NULL,             -- inbound | outbound
    role          TEXT NOT NULL,             -- user | assistant | system
    content       TEXT NOT NULL,
    agent         TEXT,
    meta          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_conversations_client_ts
    ON conversations (client_id, created_at DESC);

CREATE TABLE IF NOT EXISTS agent_runs (
    id            BIGSERIAL PRIMARY KEY,
    client_id     TEXT NOT NULL REFERENCES client_instances(id),
    vertical      TEXT NOT NULL,
    agent         TEXT NOT NULL,
    status        TEXT NOT NULL,
    error_type    TEXT,
    elapsed_ms    INTEGER,
    llm_model     TEXT,
    llm_cost_usd  NUMERIC(10, 6) DEFAULT 0,
    meta          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_agent_runs_client_ts
    ON agent_runs (client_id, created_at DESC);

CREATE TABLE IF NOT EXISTS invoices (
    id            TEXT PRIMARY KEY,
    client_id     TEXT NOT NULL REFERENCES client_instances(id),
    reference     TEXT NOT NULL,
    carrier       TEXT,
    amount        NUMERIC(12, 2),
    status        TEXT NOT NULL DEFAULT 'pending',  -- approved | held | disputed
    reasons       JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS exceptions (
    id            TEXT PRIMARY KEY,
    client_id     TEXT NOT NULL REFERENCES client_instances(id),
    shipment_id   TEXT,
    type          TEXT NOT NULL,
    severity      TEXT NOT NULL,
    reason        TEXT,
    status        TEXT NOT NULL DEFAULT 'open',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS support_tickets (
    id            TEXT PRIMARY KEY,
    client_id     TEXT NOT NULL REFERENCES client_instances(id),
    subject       TEXT NOT NULL,
    priority      TEXT NOT NULL DEFAULT 'P3',
    description   TEXT,
    status        TEXT NOT NULL DEFAULT 'new',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
