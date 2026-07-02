"""Best-effort HR / careers email scraper.

Given a company website, it visits the homepage plus likely careers/contact pages,
and extracts email addresses from:
  * mailto: links
  * visible email-pattern text

IMPORTANT — manage expectations:
Most large companies (Zomato, Blinkit, Headout, ...) do NOT publish an HR email on
their site; they route applications through ATS platforms (Greenhouse/Lever/Workday)
with "Apply" buttons instead. Career sites are also often JS-rendered SPAs and/or
behind anti-bot protection. So a "no emails found" result is common and expected,
not a bug. Use this as a helper, not a guarantee.

Usage:
    .venv/bin/python scripts/scraper.py zomato.com blinkit.com headout.com
    .venv/bin/python scripts/scraper.py https://www.headout.com
"""
from __future__ import annotations

import re
import sys
from urllib.parse import urljoin, urlparse

import requests

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# paths likely to carry a contact / careers email
CANDIDATE_PATHS = [
    "",
    "/careers",
    "/career",
    "/jobs",
    "/contact",
    "/contact-us",
    "/about",
    "/about-us",
    "/people",
]

# generic addresses worth surfacing first (HR-ish / general inbox)
PREFERRED_PREFIXES = (
    "careers", "career", "jobs", "hr", "people", "talent", "recruit",
    "hiring", "work", "joinus", "join", "hello", "contact", "info",
)

# junk we never want to report
IGNORE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def _normalize(site: str) -> str:
    site = site.strip()
    if not site.startswith(("http://", "https://")):
        site = "https://" + site
    return site.rstrip("/")


def _domain(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "")


def _clean_emails(text: str, site_domain: str) -> set[str]:
    found = set()
    for raw in EMAIL_RE.findall(text):
        e = raw.strip(".").lower()
        if e.endswith(IGNORE_SUFFIXES):
            continue
        if any(c in e for c in ("@2x", "@3x", "sentry", "example.com")):
            continue
        found.add(e)
    return found


def _fetch(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
        if r.status_code == 200 and "text/html" in r.headers.get("content-type", ""):
            return r.text
    except requests.RequestException:
        pass
    return ""


def scrape(site: str) -> dict:
    base = _normalize(site)
    domain = _domain(base)
    all_emails: set[str] = set()
    pages_hit: list[str] = []

    for path in CANDIDATE_PATHS:
        url = urljoin(base + "/", path.lstrip("/"))
        html = _fetch(url)
        if not html:
            continue
        pages_hit.append(url)
        # mailto: links + raw text
        mailtos = re.findall(r'mailto:([^"\'>?\s]+)', html, re.I)
        all_emails |= _clean_emails(" ".join(mailtos), domain)
        all_emails |= _clean_emails(html, domain)

    # rank: same-domain + preferred prefix first
    def score(e: str) -> tuple:
        local, _, host = e.partition("@")
        same = host.endswith(domain)
        preferred = local.startswith(PREFERRED_PREFIXES)
        return (not same, not preferred, e)  # False sorts first

    ranked = sorted(all_emails, key=score)
    best = next(
        (e for e in ranked
         if e.split("@")[1].endswith(domain)
         and e.split("@")[0].startswith(PREFERRED_PREFIXES)),
        None,
    )

    return {
        "company": domain,
        "pages_scanned": len(pages_hit),
        "best_hr_email": best,
        "all_emails": ranked,
    }


def main(argv: list[str]) -> None:
    if not argv:
        print("usage: scraper.py <site> [<site> ...]")
        return
    for site in argv:
        res = scrape(site)
        print("=" * 60)
        print(f"Company:        {res['company']}")
        print(f"Pages scanned:  {res['pages_scanned']}")
        print(f"Best HR email:  {res['best_hr_email'] or '— none found —'}")
        if res["all_emails"]:
            print("All emails found:")
            for e in res["all_emails"]:
                print(f"  • {e}")
        else:
            print("All emails found: (none — site likely uses an ATS / JS-rendered)")
    print("=" * 60)


if __name__ == "__main__":
    main(sys.argv[1:])
