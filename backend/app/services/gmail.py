"""Gmail integration: build a credentialed service, send mail with attachment,
and poll a thread for inbound replies.

Auth model: we authorize ONCE locally (see scripts/gmail_authorize.py) to obtain a
refresh token, stored as GMAIL_REFRESH_TOKEN. At runtime the app builds credentials
purely from client_id + client_secret + refresh_token — no browser, no token file —
so it works on a headless cloud host.
"""
from __future__ import annotations

import base64
import mimetypes
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import get_settings

# send + read. readonly is enough to detect replies; we never modify the inbox.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]

TOKEN_URI = "https://oauth2.googleapis.com/token"


def _credentials() -> Credentials:
    s = get_settings()
    if not (s.gmail_client_id and s.gmail_client_secret and s.gmail_refresh_token):
        raise RuntimeError(
            "Gmail not configured: set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET and "
            "GMAIL_REFRESH_TOKEN in .env (run scripts/gmail_authorize.py once)."
        )
    creds = Credentials(
        token=None,
        refresh_token=s.gmail_refresh_token,
        token_uri=TOKEN_URI,
        client_id=s.gmail_client_id,
        client_secret=s.gmail_client_secret,
        scopes=SCOPES,
    )
    creds.refresh(Request())  # exchange refresh token for a fresh access token
    return creds


def get_service():
    return build("gmail", "v1", credentials=_credentials(), cache_discovery=False)


def _build_message(
    *,
    sender: str,
    to: str,
    subject: str,
    body: str,
    attachment_path: str | None,
    in_reply_to: str | None = None,
) -> dict:
    msg = EmailMessage()
    msg["To"] = to
    msg["From"] = sender
    msg["Subject"] = subject
    msg.set_content(body)

    if in_reply_to:  # keep follow-ups in the same Gmail thread
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to

    if attachment_path:
        p = Path(attachment_path)
        if not p.exists():
            raise FileNotFoundError(f"Resume attachment not found: {p}")
        ctype, _ = mimetypes.guess_type(p.name)
        maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
        msg.add_attachment(
            p.read_bytes(), maintype=maintype, subtype=subtype, filename=p.name
        )

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


def send_email(
    *,
    to: str,
    subject: str,
    body: str,
    attachment_path: str | None = None,
    thread_id: str | None = None,
    in_reply_to_message_id: str | None = None,
) -> dict:
    """Send an email. Returns Gmail's response incl. message id and threadId.

    Pass thread_id + in_reply_to_message_id to thread a follow-up onto an existing
    conversation.
    """
    s = get_settings()
    service = get_service()
    message = _build_message(
        sender=s.gmail_sender,
        to=to,
        subject=subject,
        body=body,
        attachment_path=attachment_path,
        in_reply_to=in_reply_to_message_id,
    )
    if thread_id:
        message["threadId"] = thread_id
    sent = service.users().messages().send(userId="me", body=message).execute()
    return sent  # {'id': ..., 'threadId': ..., 'labelIds': [...]}


def get_thread_messages(thread_id: str) -> list[dict]:
    """Return all messages in a Gmail thread (metadata + snippet)."""
    service = get_service()
    thread = (
        service.users()
        .threads()
        .get(userId="me", id=thread_id, format="metadata",
             metadataHeaders=["From", "Subject", "Date", "Message-Id"])
        .execute()
    )
    return thread.get("messages", [])


def find_replies(thread_id: str, exclude_sender: str) -> list[dict]:
    """Return messages in a thread that are NOT from us (i.e. inbound replies).

    Presence detection only — sentiment is labeled manually in the dashboard.
    Each item: {message_id, snippet, from, date}.
    """
    replies: list[dict] = []
    for m in get_thread_messages(thread_id):
        headers = {h["name"].lower(): h["value"] for h in m.get("payload", {}).get("headers", [])}
        sender = headers.get("from", "")
        if exclude_sender.lower() in sender.lower():
            continue  # our own message
        replies.append(
            {
                "message_id": m["id"],
                "snippet": m.get("snippet", ""),
                "from": sender,
                "date": headers.get("date", ""),
            }
        )
    return replies
