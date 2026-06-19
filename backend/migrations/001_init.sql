-- Recruiter Outreach Automation Platform — initial schema
-- Run this against your Supabase Postgres (SQL editor or psql).

-- ─────────────────────────────────────────────────────────────
-- templates: reusable email templates (official company / startup / generic, ...)
-- Body uses {recruiter_name} and {company} placeholders. Text provided later by user.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS templates (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT        NOT NULL,                 -- e.g. "Template 1 - Official company"
    kind        TEXT        NOT NULL DEFAULT 'generic', -- official_company | startup | generic | ...
    subject     TEXT        NOT NULL,                 -- e.g. "Looking for opportunities at {company}"
    body        TEXT        NOT NULL,                 -- supports {recruiter_name}, {company}
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────
-- recruiters: the people you reach out to
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recruiters (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT        NOT NULL,
    company     TEXT        NOT NULL,
    email       TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (email)            -- prevents accidentally adding the same recruiter twice
);

-- ─────────────────────────────────────────────────────────────
-- threads: one outreach conversation with a recruiter
-- status: active | replied_unlabeled | replied_positive | replied_negative | ooo | dead
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS threads (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recruiter_id    BIGINT      NOT NULL REFERENCES recruiters(id) ON DELETE CASCADE,
    template_id     BIGINT      NOT NULL REFERENCES templates(id),
    status          TEXT        NOT NULL DEFAULT 'active',
    gmail_thread_id TEXT,                            -- set after first send; used for reply polling
    ooo_return_date DATE,                            -- set when a reply is labeled out-of-office
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────
-- sends: each individual email (initial or follow-up) in a thread
-- type:   initial | followup
-- status: pending_approval | approved | scheduled | sent | failed | cancelled
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sends (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    thread_id     BIGINT      NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    type          TEXT        NOT NULL DEFAULT 'initial',
    subject       TEXT        NOT NULL,
    body          TEXT        NOT NULL,              -- rendered text at approval time
    scheduled_at  TIMESTAMPTZ,                       -- chosen random time within a window
    sent_at       TIMESTAMPTZ,
    status        TEXT        NOT NULL DEFAULT 'pending_approval',
    error         TEXT,                              -- last failure reason, if any
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────────────────────────────────────────────────────────
-- replies: detected inbound messages from recruiters (presence only; sentiment is manual)
-- label: NULL (unlabeled) | positive | negative | ooo
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS replies (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    thread_id         BIGINT      NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
    gmail_message_id  TEXT        NOT NULL,
    snippet           TEXT,
    received_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    label             TEXT,                          -- set by user in dashboard
    UNIQUE (gmail_message_id)
);

-- ─────────────────────────────────────────────────────────────
-- helpful indexes
-- ─────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_sends_due
    ON sends (status, scheduled_at);
CREATE INDEX IF NOT EXISTS idx_threads_status
    ON threads (status);
CREATE INDEX IF NOT EXISTS idx_replies_thread
    ON replies (thread_id);
