-- Attachment is a per-template choice: a job application wants the resume attached,
-- a sales intro does not. Default TRUE keeps existing behavior for existing rows.
ALTER TABLE templates ADD COLUMN IF NOT EXISTS attach_resume BOOLEAN NOT NULL DEFAULT TRUE;
