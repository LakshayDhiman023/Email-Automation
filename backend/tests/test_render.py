"""Template rendering: substitution, unknown-variable handling, optional-line dropping."""
from app.services.outreach import extract_variables, render


def test_extract_variables_unique_first_seen_order():
    assert extract_variables("Apply for {role} at {company}",
                             "Hi {name}, the {role} role. {job_link}") == [
        "role", "company", "name", "job_link",
    ]


def test_extract_handles_empty_and_none():
    assert extract_variables("", None or "") == []


def test_render_substitutes_all_provided():
    s, b = render("Application for {role} at {company}",
                  "Hi {name}, about {role}.",
                  {"role": "SDE 1", "company": "Acme", "name": "Mohit"})
    assert s == "Application for SDE 1 at Acme"
    assert b == "Hi Mohit, about SDE 1."


def test_render_leaves_unknown_placeholders_intact():
    s, b = render("Hi {mystery}", "Body {mystery}", {})
    assert s == "Hi {mystery}"
    assert b == "Body {mystery}"


def test_render_drops_body_line_when_optional_value_blank():
    body = "Hi {name},\nJob ID: {job_id}\nLink: {job_link}\nThanks."
    _, b = render("s", body, {"name": "Sam", "job_id": "", "job_link": ""})
    assert b == "Hi Sam,\nThanks."


def test_render_keeps_line_when_optional_value_filled():
    body = "Hi {name},\nJob ID: {job_id}\nThanks."
    _, b = render("s", body, {"name": "Sam", "job_id": "REQ-7"})
    assert "Job ID: REQ-7" in b


def test_render_blank_value_in_subject_just_disappears():
    s, _ = render("Role {role} {job_id}", "", {"role": "SDE", "job_id": ""})
    assert s == "Role SDE "
