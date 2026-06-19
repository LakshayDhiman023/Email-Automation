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
    core/        config, settings, db connection
    models/      pydantic + table models
    routers/     FastAPI route modules
    services/    gmail, scheduler, templates, outreach logic
    main.py      FastAPI app + /health
  migrations/    SQL schema
frontend/        React dashboard (Phase 7)
docs/            plan & notes
```

## Status

Phase 1 (foundation) in progress. See `docs/PLAN.md` for the full phased build order.
