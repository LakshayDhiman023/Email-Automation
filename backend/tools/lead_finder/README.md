# Lead finder (companion tool)

Standalone helpers for finding a company's likely hiring/HR email address *before*
you add them as a contact in the outreach app. These are **not** imported by the
FastAPI app or the scheduler — run them by hand.

- `scraper.py` — visits a company site (homepage + likely careers/contact pages) and
  extracts published email addresses.
- `find_hiring_email.py` — uses `scraper.py`, and if nothing is published, falls back
  to guessing common inboxes (careers@, hr@, jobs@, talent@, …).

## Run

```bash
cd backend/tools/lead_finder
python find_hiring_email.py <company-website-url>
```

Output is best-effort — always eyeball an address before emailing it (a wrong guess
bounces, which the app will then auto-suppress).
