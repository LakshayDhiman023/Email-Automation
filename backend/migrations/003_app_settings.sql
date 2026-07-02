-- App settings: a single row holding the user-configurable scheduling preferences,
-- so the app isn't hardcoded to one timezone/country. Edited via the Settings page.
-- Idempotent: safe to re-run.

CREATE TABLE IF NOT EXISTS app_settings (
    id             INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),  -- singleton row
    timezone       TEXT        NOT NULL DEFAULT 'Asia/Kolkata',  -- IANA tz, e.g. America/New_York
    -- two daily send windows (HH:MM, 24h, in `timezone`)
    window_a_start TEXT        NOT NULL DEFAULT '09:00',
    window_a_end   TEXT        NOT NULL DEFAULT '10:00',
    window_b_start TEXT        NOT NULL DEFAULT '14:00',
    window_b_end   TEXT        NOT NULL DEFAULT '15:00',
    -- ISO weekday numbers that count as working days (1=Mon … 7=Sun)
    working_days   INT[]       NOT NULL DEFAULT '{1,2,3,4,5}',
    -- follow-up cadence
    followup_after_working_days INT NOT NULL DEFAULT 5,
    -- holiday handling: 'none' | 'country'. When 'country', skip public holidays for
    -- holiday_country (ISO code the `holidays` library understands, e.g. 'IN','US').
    holiday_mode    TEXT       NOT NULL DEFAULT 'none',
    holiday_country TEXT       NOT NULL DEFAULT 'IN',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- seed the singleton row if absent
INSERT INTO app_settings (id) VALUES (1) ON CONFLICT (id) DO NOTHING;
