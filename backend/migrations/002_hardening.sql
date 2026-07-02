-- Recruiter Outreach Automation Platform — hardening migration (Phase 8)
-- Adds deliverability + safety features surfaced by real cold-outreach failure modes:
-- daily caps, bounce handling, suppression/opt-out, send audit log, read signal.
-- Idempotent: safe to re-run.

-- ─────────────────────────────────────────────────────────────
-- suppression_list: addresses we must NEVER email (opt-out / bounced / dead lead).
-- Enforced at add-contact time AND again right before each send.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS suppression_list (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email       TEXT        NOT NULL,
    reason      TEXT        NOT NULL DEFAULT 'manual',  -- manual | bounced | negative | complaint
    note        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (email)
);

-- ─────────────────────────────────────────────────────────────
-- send_events: append-only audit trail for every attempt on a send.
-- Lets us see the full history (queued -> retry -> sent/failed/bounced) instead of
-- only the last error on the sends row.
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS send_events (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    send_id     BIGINT      NOT NULL REFERENCES sends(id) ON DELETE CASCADE,
    event       TEXT        NOT NULL,                    -- attempt | sent | failed | bounced | retry | skipped
    detail      TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_send_events_send ON send_events (send_id);

-- ─────────────────────────────────────────────────────────────
-- sends: retry bookkeeping so a transient Gmail hiccup doesn't permanently fail a send.
--   attempts         = how many times we've tried to dispatch this send.
--   gmail_message_id = Message-Id of what we sent (threading + read-state).
--   updated_at       = last state change; used to detect orphaned 'sending' rows
--                      (process died mid-send) without racing genuine in-flight sends.
-- ─────────────────────────────────────────────────────────────
ALTER TABLE sends ADD COLUMN IF NOT EXISTS attempts     INT NOT NULL DEFAULT 0;
ALTER TABLE sends ADD COLUMN IF NOT EXISTS gmail_message_id TEXT;
ALTER TABLE sends ADD COLUMN IF NOT EXISTS updated_at   TIMESTAMPTZ NOT NULL DEFAULT now();

-- ─────────────────────────────────────────────────────────────
-- recruiters: remember when we last emailed them (global cooldown across threads).
-- ─────────────────────────────────────────────────────────────
ALTER TABLE recruiters ADD COLUMN IF NOT EXISTS last_contacted_at TIMESTAMPTZ;

-- threads.status gains 'bounced' (delivery failed; follow-ups halted). No schema
-- change needed for that — status is free-text — but noted here for the reader.

-- helpful index for the daily-cap rolling count
CREATE INDEX IF NOT EXISTS idx_sends_sent_at ON sends (sent_at) WHERE sent_at IS NOT NULL;
