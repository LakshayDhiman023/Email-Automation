"""One-time local Gmail authorization → prints a refresh token.

Run this ONCE on your own machine:

    cd backend
    .venv/bin/python scripts/gmail_authorize.py

It opens your browser, you click "Allow" (accept the unverified-app warning — it's
your own app), and it prints a GMAIL_REFRESH_TOKEN. Paste that into backend/.env.
After that the cloud app sends mail forever without any browser.

Needs GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET set in backend/.env first.
"""
import os
import sys

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

# keep in sync with app/services/gmail.py SCOPES
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def main() -> None:
    load_dotenv()
    client_id = os.getenv("GMAIL_CLIENT_ID")
    client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    if not client_id or not client_secret:
        sys.exit("ERROR: set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in backend/.env first.")

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    # access_type=offline + prompt=consent guarantees a refresh token is returned
    creds = flow.run_local_server(
        port=0, access_type="offline", prompt="consent"
    )

    print("\n" + "=" * 64)
    print("SUCCESS — copy this line into backend/.env:\n")
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
    print("=" * 64)


if __name__ == "__main__":
    main()
