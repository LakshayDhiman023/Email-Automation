# Build Plan

Single fully-cloud app. No Ollama, no laptop dependency. All $0.

## Decisions (locked)

| Area            | Decision |
|-----------------|----------|
| Runtime         | Cloud host (Railway vs Render — decided at deploy time) |
| Database        | Supabase Postgres |
| Email           | Gmail API via OAuth (stored refresh token; consent done once locally) |
| Frontend        | React + Tailwind → REST |
| Templates       | First-class records (Template 1/2/3: official company / startup / generic). Text provided by user later. |
| Approval        | At add-time |
| Send windows    | 9–10 AM and 2–3 PM IST, each send a random minute in window |
| Working days    | Mon–Fri, skip India public holidays (`holidays` lib) |
| Slot rule       | <9AM→today 9–10; 9AM–<2PM→today 2–3; after→next working day 9–10; weekend/holiday rolls forward |
| Batch timing    | Each contact its own random minute |
| Missed window   | Auto-reschedule to next valid window |
| Volume cap      | None (risk acknowledged) |
| Reply handling  | Detect presence only → auto-pause follow-up → user labels positive/negative/ooo |
| OOO             | User enters recruiter return date → follow-up reschedules to that date's next valid window |
| Follow-up text  | Placeholder "Following up on my application." — **user WILL replace; remind at Phase 6** |
| Follow-up timing| 5 working days with no detected reply |

## Phases

1. **Foundation** ✅ — repo, schema (incl. `templates`), FastAPI skeleton, `/health`, config, db.
2. **Gmail OAuth** — local consent → refresh token; send-with-attachment; reply polling helper.
3. **Scheduling engine** — slot logic, `holidays`, APScheduler jobs, catch-up on startup.
4. **Outreach core** — templates CRUD, add contact → render → approve → schedule → send → log.
5. **Reply detection + labeling** — poll Gmail, auto-pause follow-ups, manual label, OOO return-date.
6. **Follow-up engine** — 5-working-day rule (← remind user for real follow-up text).
7. **React dashboard** — all sections wired to REST.
8. **Hardening + deploy** — pick host, set keep-alive cron-ping, secrets, retries.

## Dashboard sections (Phase 7)
Add Contact · Templates · Pending Approvals · Scheduled Queue · Sent Log ·
Needs Review · Attention (positive) · Dead Threads · Analytics

## Known risks
- No volume cap → spam-pattern risk if scaled.
- Supabase free tier pauses after ~1 week idle (used most days → fine).
- Gmail OAuth one-time manual setup.
