# ✉ Mailflow

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-Vite-61DAFB?logo=react&logoColor=white)
![Postgres](https://img.shields.io/badge/Supabase-Postgres-3ECF8E?logo=supabase&logoColor=white)
![License](https://img.shields.io/badge/license-TBD-lightgrey)

A free, self-hostable email-outreach automation tool. Clone it, connect your own
Supabase database and Gmail account, and it sends personalized, template-driven
emails **as you** — with every single email reviewed and approved by a human
before it leaves. Built for job hunts, cold outreach, and similar one-person
campaigns; not a bulk mailer, not multi-tenant SaaS.

## What it does

- **Dynamic templates** — write a subject/body with any `{variable}` you want
  (`{role}`, `{hr_name}`, anything). The compose screen auto-generates one input
  per variable, plus a live preview that is byte-for-byte what will actually send.
- **Human-in-the-loop always** — every email sits in `pending_approval` until you
  approve it. Edit the draft, cancel it, or close the whole thread at any point.
- **Configurable scheduling** — your timezone, two daily send windows, working
  days, and optional country-holiday skipping, all set from the Settings page
  (no hardcoded region). Follow-ups queue automatically after N working days.
- **Reply handling** — polls Gmail for replies on tracked threads and surfaces
  them in Needs Review; label each **Positive / Negative / Out of Office** (OOO
  reschedules the follow-up to the stated return date). Bounces auto-suppress.
- **Deliverability guardrails** — rolling 24h send cap, per-contact cooldown
  (overridable), a hard suppression list, retry with an audit trail, and
  one-open-thread-per-contact so you never double-email someone.
- **Pipeline board** — a read-only kanban of every thread by lifecycle stage,
  with full-text search across name/company/email.
- **Onboarding checklist** — a live progress card on Overview that tracks real
  setup state (Gmail connected, identity set, first template, first send) and
  disappears once you're fully set up.
- **GDPR-style erasure** — permanently delete a contact and everything derived
  from them (threads/sends/replies) on request, distinct from suppression alone.
- **Audit trail** — every approval, cancellation, suppression change, and
  settings update is recorded in an append-only log with who/when/from-where.
- **CSV export & metrics** — reply rate / bounce rate per distinct recipient,
  and a full outreach CSV export, both gated behind their own tokens.

## Architecture

```
Browser (React/Vite)  →  FastAPI (/api/v1/*)  →  Supabase Postgres
                              │                    (pgbouncer pooled)
                              └──→ Gmail API (OAuth refresh token; send + read)

APScheduler drives sends/replies/follow-ups in-process. Free hosts suspend
idle processes, so an external cron (e.g. cron-job.org) can hit
POST /api/v1/tasks/run on a schedule to keep the pipeline correct even when
the host was asleep — idempotent and safe to overlap with APScheduler.
```

## Tech stack

| Layer      | Choice                                                    |
|------------|------------------------------------------------------------|
| Backend    | Python 3.12 · FastAPI · APScheduler · SQLAlchemy (text SQL) |
| Database   | Supabase (Postgres), pgbouncer transaction pooling          |
| Email      | Gmail API (OAuth, stored refresh token)                     |
| Frontend   | React + Vite + Tailwind CSS                                 |
| Scheduling | `pytz` + `holidays` (country-configurable) + APScheduler    |
| CI         | GitHub Actions — ruff + pytest (w/ coverage), eslint + build |

## Repo layout

```
backend/
  app/
    core/        settings, DB engine (pgbouncer-aware), structured logging,
                 auth (token + per-IP throttle)
    models/      pydantic request/response schemas
    routers/     templates, outreach (contacts/sends/threads/search), replies,
                 stats, suppression, settings, audit, privacy (GDPR erasure),
                 export, tasks, health — all versioned under /api/v1
    services/    outreach (render/schedule/dispatch), scheduling, replies
                 (Gmail polling), followups, guards (safety rails), gmail
                 (API wrapper), app_settings (config cache), audit
    main.py      FastAPI app wiring: auth, CORS, security headers, /api/v1
  migrations/    SQL schema, applied in order via scripts/migrate.py
  scripts/       one-off ops: gmail_authorize, seed_templates, migrate
  tests/         pytest suite (DB-free via a pinned settings cache)
  tools/
    lead_finder/ standalone companion script — not imported by the running app
frontend/
  src/
    pages/       Overview, AddContact (compose), Board (pipeline kanban),
                 Templates, Suppression, Settings, and feature folders
                 Outreach/ and Replies/
    components/  shared UI primitives (ui.jsx, Toast.jsx, icons.jsx)
    api.js       REST client (X-API-Token, /api/v1 base)
    App.jsx      shell: sidebar nav + routing between pages
docs/
  VISION.txt       mission, principles, roadmap
  AI_BRIEF.txt     context for external AI tools to propose new features
  artifact.html    UI/UX mockups, reviewed before anything gets built
  exploration.html feature-lab feasibility studies
.github/workflows/ CI: lint + test + build on every push
Makefile           one-command workflow: install/migrate/seed/backend/
                   frontend/test/lint/build/check
```

## Development

```
make install   # backend venv + frontend deps
make migrate   # apply pending DB migrations
make seed      # example templates
make backend   # run the API (port 8000)
make frontend  # run the dashboard (port 5173)
make check     # everything CI runs: lint + test + build
```

## Security

Every route under `/api/v1` (except `/health`) requires an `X-API-Token` header
matching `API_TOKEN`, compared in constant time with a per-IP failed-attempt
throttle. Auth is disabled only when `API_TOKEN` is unset (local dev) — set it
before any public deploy, since the app can send mail from your Gmail. Also
in place: security headers, a request body size cap, interactive docs disabled
in production, header-injection rejection on user input, and a fail-closed,
header-only-token CSV export.

## Status

Working product, actively developed. See `docs/VISION.txt` for the roadmap
and principles behind design decisions, and `docs/PLAN.md` for build history.
