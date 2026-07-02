# Recruiter Outreach Automation Platform

A personal, $0, always-up tool to automate recruiter outreach: add a recruiter (name, company,
email), pick a template, approve the generated email, and the system schedules + sends it from
your own Gmail at human-looking weekday windows — then tracks replies and follow-ups.

## What it does

- **Add a recruiter** → choose a **template** (e.g. official company / startup / generic) →
  it fills in `{recruiter_name}` / `{company}` and attaches your resume.
- **Approve at add-time** → the draft is queued, you never send anything unreviewed.
- **Scheduled sending** (IST, Mon–Fri, skips public holidays via the `holidays` library):
  - Two windows per day: **9–10 AM** and **2–3 PM**, each send at its own random minute.
  - Added before 9 AM → today 9–10; before 2 PM → today 2–3; after that → next working day 9–10.
- **Reply detection** → polls Gmail for replies on tracked threads (presence only), auto-pauses
  follow-ups, and surfaces the thread in **Needs Review**.
- **Manual labeling** → you mark each reply **Positive** / **Negative** / **Out of Office**.
  - Out of Office → enter the recruiter's return date → follow-up reschedules to then.
- **Follow-ups** → if no reply after 5 working days, a follow-up is queued for approval.

## Architecture (single cloud app — no laptop dependency, no Ollama)

```
CLOUD (always-up free host)         Supabase Postgres        Gmail API (OAuth refresh token)
  FastAPI + APScheduler                 source of truth          send + read (your account)
  + React dashboard
  + /health  (kept awake by free external cron-ping)
```

## Tech stack

| Layer      | Choice                                  |
|------------|-----------------------------------------|
| Backend    | Python · FastAPI · APScheduler          |
| Database   | Supabase (Postgres)                     |
| Email      | Gmail API (OAuth, stored refresh token) |
| Frontend   | React + Tailwind (REST)                 |
| Scheduling | `holidays` (India) + APScheduler        |
| Hosting    | Free cloud host (Railway/Render — TBD)  |

## Repo layout

```
backend/
  app/
    core/        config, db engine (pgbouncer-aware), security (API token)
    models/      pydantic request/response schemas
    routers/     FastAPI route modules (health, tasks, outreach, replies,
                 templates, suppression, stats, export)
    services/    gmail, scheduler, scheduling, outreach, replies,
                 followups, guards (deliverability/safety)
    main.py      FastAPI app wiring + auth + CORS + lifespan
  migrations/    SQL schema (001_init, 002_hardening)
  scripts/       one-off ops: gmail_authorize, seed_templates
  tools/
    lead_finder/ standalone companion: find a company's hiring email
                 (NOT imported by the running app)
frontend/
  src/
    pages/       one component per nav screen: Overview, AddContact,
                 Templates, Suppression, and feature folders Outreach/ and
                 Replies/ (each an index.jsx + its own panels)
    components/  shared UI primitives (ui.jsx, Toast.jsx)
    api.js       REST client (sends X-API-Token)
    App.jsx      shell: sidebar nav + routing between pages
docs/            plan & notes
```

## Scheduling & free-host reality

The in-process APScheduler drives work when the host is always-on. But **free hosts
suspend idle processes**, and a suspended process runs no scheduler — so sends could
miss their windows. To stay correct regardless, point an external cron (cron-job.org)
at `POST /tasks/run` every few minutes: it runs exactly what the scheduler would
(due sends, reply poll, follow-up sweep), token-guarded and idempotent. On an
always-on host you can rely on APScheduler alone; on a free tier, drive it externally.

## Security

All endpoints except `/health` require an `X-API-Token` header matching `API_TOKEN`
(the frontend sends `VITE_API_TOKEN`). Auth is disabled only when `API_TOKEN` is unset
(local dev). Set it before any public deploy — the app can send mail from your Gmail.

## Status

See `docs/PLAN.md` for the phased build order. Foundation + outreach + replies +
follow-ups + dashboard + hardening (caps, suppression, bounce handling, retries,
auth) are implemented.
