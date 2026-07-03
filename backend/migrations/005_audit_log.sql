-- Append-only audit trail: who (single operator) did what, when, from where.
-- Written by app_audit.record() alongside each state-changing action; never
-- updated or deleted by the app — that immutability is the point of an audit log.
CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGSERIAL   PRIMARY KEY,
    action      TEXT        NOT NULL,   -- e.g. 'send.approve', 'settings.update'
    entity      TEXT,                   -- e.g. 'send', 'template', 'suppression'
    entity_id   TEXT,                   -- the row's id/email, as text (mixed key types)
    client_ip   TEXT,
    request_id  TEXT,
    detail      JSONB,                  -- small structured context (no PII bodies)
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log (action);
