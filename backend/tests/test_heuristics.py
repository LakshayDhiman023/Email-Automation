"""Send-retry classification, bounce detection, and follow-up content rules."""
from app.services.followups import build_followup_content
from app.services.gmail import _looks_like_bounce
from app.services.outreach import _is_retryable


def test_transient_errors_are_retryable():
    assert _is_retryable(Exception("HttpError 503 service unavailable"))
    assert _is_retryable(Exception("Rate Limit Exceeded"))
    assert _is_retryable(Exception("connection reset by peer"))


def test_permanent_errors_are_not_retryable():
    assert not _is_retryable(Exception("400 invalid recipient"))
    assert not _is_retryable(Exception("resume attachment not found"))


def test_mailer_daemon_is_a_bounce():
    assert _looks_like_bounce(
        "Mail Delivery Subsystem <mailer-daemon@googlemail.com>",
        "Delivery Status Notification (Failure)")
    assert _looks_like_bounce("postmaster@x.com", "Undeliverable: your message")


def test_normal_reply_is_not_a_bounce():
    assert not _looks_like_bounce("Jane HR <jane@acme.com>", "Re: Application")



def test_followup_subject_gets_re_prefix_exactly_once():
    subject, _ = build_followup_content("Application for SDE at Acme")
    assert subject == "Re: Application for SDE at Acme"
    again, _ = build_followup_content(subject)
    assert again == subject  # no "Re: Re:"


def test_followup_body_uses_name_and_signature_placeholders():
    _, body = build_followup_content("anything")
    assert "{name}" in body and "{signature}" in body
