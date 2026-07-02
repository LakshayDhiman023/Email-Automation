"""Find a company's likely hiring/HR inbox.

Two-stage, best-effort:
  1) SCRAPE the site for any published careers/contact email (scraper.py).
  2) If none, GUESS common hiring addresses (careers@, hr@, jobs@, talent@, ...)
     and verify each against the domain's mail server via DNS MX + an SMTP RCPT
     probe — i.e. ask the server "would you accept mail for this address?" without
     actually sending anything.

Honest caveats:
  * Many providers (Google Workspace especially) accept ALL addresses or reject
    probes outright, so SMTP verification is often inconclusive — results are
    marked accordingly.
  * Some servers block probing IPs. A "could not verify" is not "doesn't exist".
  * This is a research helper, not a guarantee.

Usage:
    .venv/bin/python scripts/find_hiring_email.py zomato.com blinkit.com headout.com
"""
from __future__ import annotations

import smtplib
import sys
from urllib.parse import urlparse

import dns.resolver  # dnspython

from scraper import scrape  # reuse the scraper

GUESS_PREFIXES = [
    "careers", "career", "jobs", "hr", "talent", "recruiting", "recruitment",
    "hiring", "people", "work", "joinus", "hello", "contact",
]

PROBE_FROM = "outreach-check@example.com"


def domain_of(site: str) -> str:
    if not site.startswith(("http://", "https://")):
        site = "https://" + site
    return urlparse(site).netloc.replace("www.", "")


def mx_host(domain: str) -> str | None:
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=8)
        best = sorted(answers, key=lambda r: r.preference)[0]
        return str(best.exchange).rstrip(".")
    except Exception:
        return None


def smtp_accepts(mx: str, address: str) -> str:
    """Return 'yes' | 'no' | 'unknown' for whether the server accepts the address."""
    try:
        server = smtplib.SMTP(timeout=10)
        server.connect(mx, 25)
        server.helo("example.com")
        server.mail(PROBE_FROM)
        code, _ = server.rcpt(address)
        server.quit()
        if code in (250, 251):
            return "yes"
        if code in (550, 551, 553):
            return "no"
        return "unknown"
    except Exception:
        return "unknown"


def find(site: str) -> dict:
    domain = domain_of(site)

    # stage 1: scrape
    scraped = scrape(site)
    if scraped["best_hr_email"]:
        return {
            "company": domain,
            "method": "scraped",
            "hiring_email": scraped["best_hr_email"],
            "candidates": [],
        }

    # stage 2: guess + verify
    mx = mx_host(domain)
    if not mx:
        return {"company": domain, "method": "no-mx", "hiring_email": None,
                "candidates": []}

    results = []
    accepted = None
    for p in GUESS_PREFIXES:
        addr = f"{p}@{domain}"
        verdict = smtp_accepts(mx, addr)
        results.append((addr, verdict))
        if verdict == "yes" and accepted is None:
            accepted = addr

    return {
        "company": domain,
        "method": "guessed+verified",
        "mx": mx,
        "hiring_email": accepted,
        "candidates": results,
    }


def main(argv: list[str]) -> None:
    if not argv:
        print("usage: find_hiring_email.py <site> [<site> ...]")
        return
    for site in argv:
        r = find(site)
        print("=" * 60)
        print(f"Company:       {r['company']}")
        print(f"Method:        {r['method']}")
        if r.get("mx"):
            print(f"Mail server:   {r['mx']}")
        print(f"Hiring email:  {r['hiring_email'] or '— not confirmed —'}")
        if r["candidates"]:
            print("Guesses (server verdict):")
            for addr, verdict in r["candidates"]:
                mark = {"yes": "✓", "no": "✗", "unknown": "?"}[verdict]
                print(f"  {mark} {addr:32} [{verdict}]")
    print("=" * 60)
    print("Note: '?' = server wouldn't confirm (common with Google Workspace).")


if __name__ == "__main__":
    main(sys.argv[1:])
