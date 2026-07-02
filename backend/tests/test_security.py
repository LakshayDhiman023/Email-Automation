"""Pins the OWASP-hardening behavior: token throttle + header-injection rejection."""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core import security
from app.models.schemas import ContactCreate, SendEdit, TemplateCreate


@pytest.fixture(autouse=True)
def _reset_throttle():
    security._failures.clear()
    yield
    security._failures.clear()


def _verify(token):
    security.verify_shared_token(None, token, "secret", header_name="X-API-Token")


def test_correct_token_passes():
    _verify("secret")


def test_wrong_token_401():
    with pytest.raises(HTTPException) as e:
        _verify("nope")
    assert e.value.status_code == 401


def test_brute_force_throttled_to_429():
    for _ in range(security._MAX_FAILURES):
        with pytest.raises(HTTPException):
            _verify("nope")
    # even the CORRECT token is refused while the IP is throttled
    with pytest.raises(HTTPException) as e:
        _verify("secret")
    assert e.value.status_code == 429


def test_template_subject_rejects_newline():
    with pytest.raises(ValidationError):
        TemplateCreate(name="t", subject="hi\nBcc: evil@x.com", body="b")


def test_send_edit_subject_rejects_newline():
    with pytest.raises(ValidationError):
        SendEdit(subject="hi\r\nX-Injected: 1")


def test_contact_variable_rejects_newline_and_oversize():
    base = dict(company="Acme", email="a@b.com", template_id=1)
    with pytest.raises(ValidationError):
        ContactCreate(**base, variables={"role": "x\ny"})
    with pytest.raises(ValidationError):
        ContactCreate(**base, variables={"role": "x" * 2001})
    ContactCreate(**base, variables={"role": "Engineer"})  # sane input passes
