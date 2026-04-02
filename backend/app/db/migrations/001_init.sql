-- RevSight Database Schema
-- Run with: psql $DATABASE_URL -f 001_init.sql

-- ─── Users (Sales Reps / Managers) ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    role        TEXT CHECK (role IN ('ae', 'sdr', 'manager', 'cro')) DEFAULT 'ae',
    region      TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Accounts (Companies) ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS accounts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    domain      TEXT,
    industry    TEXT,
    arr_segment TEXT CHECK (arr_segment IN ('SMB', 'Mid-Market', 'Enterprise')),
    owner_id    UUID REFERENCES users(id),
    region      TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Contacts ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id      UUID REFERENCES accounts(id) ON DELETE CASCADE,
    email           TEXT NOT NULL,
    full_name       TEXT,
    title           TEXT,
    lifecycle_stage TEXT CHECK (lifecycle_stage IN (
                        'lead', 'mql', 'sql', 'sal', 'opportunity', 'customer', 'churned'
                    )),
    lead_source     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Opportunities (Pipeline Core) ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS opportunities (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id        UUID REFERENCES accounts(id) ON DELETE CASCADE,
    contact_id        UUID REFERENCES contacts(id),
    owner_id          UUID REFERENCES users(id),
    name              TEXT NOT NULL,
    stage_name        TEXT CHECK (stage_name IN (
                          'Discovery', 'Demo', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost'
                      )),
    arr               NUMERIC(12, 2),
    probability       SMALLINT CHECK (probability BETWEEN 0 AND 100),
    forecast_category TEXT CHECK (forecast_category IN ('Pipeline', 'Best Case', 'Commit', 'Closed')),
    close_date        DATE,
    quarter           TEXT,    -- e.g. Q3-2026
    region            TEXT,    -- NA, EMEA, APAC
    segment           TEXT,    -- Enterprise, SMB, Mid-Market
    scenario_id       TEXT,    -- na_healthy, emea_undercovered, apac_dataquality
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Pipeline Stage History (for velocity / aging analytics) ────────────────
CREATE TABLE IF NOT EXISTS pipeline_stage_history (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    from_stage     TEXT,
    to_stage       TEXT NOT NULL,
    changed_at     TIMESTAMPTZ DEFAULT NOW(),
    changed_by     UUID REFERENCES users(id)
);

-- ─── Activities ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS activities (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE,
    contact_id     UUID REFERENCES contacts(id),
    type           TEXT CHECK (type IN ('call', 'email', 'meeting', 'note', 'task')),
    outcome        TEXT,
    duration_mins  INTEGER,
    occurred_at    TIMESTAMPTZ,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Run Tracking (Audit Trail) ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS runs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    persona     TEXT,
    quarter     TEXT,
    region      TEXT,
    segment     TEXT,
    scenario_id TEXT,
    status      TEXT CHECK (status IN ('pending', 'running', 'done', 'failed')) DEFAULT 'pending',
    report_json JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- ─── Agent Step Logs ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_steps (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id      UUID REFERENCES runs(id) ON DELETE CASCADE,
    agent_name  TEXT NOT NULL,
    input_hash  TEXT,
    output_hash TEXT,
    duration_ms INTEGER,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Audit Actions ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_actions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id       UUID REFERENCES runs(id) ON DELETE CASCADE,
    action_type  TEXT NOT NULL,
    payload      JSONB,
    status       TEXT CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
    reviewed_by  TEXT,
    reviewed_at  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Materialized View for AI Agent Queries ──────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_pipeline_metrics AS
SELECT
    o.scenario_id,
    o.quarter,
    o.region,
    o.segment,
    o.stage_name,
    o.forecast_category,
    DATE_TRUNC('month', o.close_date)                               AS close_month,
    COUNT(*)                                                        AS deal_count,
    SUM(o.arr)                                                      AS total_arr,
    AVG(o.probability)                                              AS avg_probability,
    AVG(EXTRACT(EPOCH FROM (NOW() - o.created_at)) / 86400)         AS avg_age_days,
    SUM(CASE WHEN o.close_date IS NULL THEN 1 ELSE 0 END)           AS missing_close_dates
FROM opportunities o
WHERE o.stage_name NOT IN ('Closed Won', 'Closed Lost')
GROUP BY 1, 2, 3, 4, 5, 6, 7;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_pipeline_metrics
    ON mv_pipeline_metrics (scenario_id, quarter, region, segment, stage_name, forecast_category, close_month);

-- ─── Indexes ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_opportunities_scenario ON opportunities (scenario_id, quarter, region, segment);
CREATE INDEX IF NOT EXISTS idx_opportunities_stage    ON opportunities (stage_name);
CREATE INDEX IF NOT EXISTS idx_activities_opportunity ON activities (opportunity_id);
CREATE INDEX IF NOT EXISTS idx_runs_status            ON runs (status, created_at DESC);
