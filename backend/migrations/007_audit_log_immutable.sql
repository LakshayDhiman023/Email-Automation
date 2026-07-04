-- Enforce audit_log's append-only guarantee at the DATABASE level, not just as
-- an app-side convention (the app itself never issues UPDATE/DELETE on this
-- table — see services/audit.py — so this only ever fires on a bug or a
-- compromised token attempting to tamper with the trail).
CREATE OR REPLACE FUNCTION reject_audit_log_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only: % is not permitted', TG_OP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS audit_log_no_update ON audit_log;
CREATE TRIGGER audit_log_no_update
    BEFORE UPDATE OR DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION reject_audit_log_mutation();
