"""Canonical plan URLs do not turn source-bound calls into unconditional prose."""
import pytest

from live_contentops.event_article_guard_v1 import (
    CONFLICTS_NOTICE, PUBLIC_NOTICE, PublicOutputError, check_publication_copy,
    compact_reader_conditional_call_text,
)


CALL = {"condition": "price reaches the source zone", "direction": "bearish",
        "market": "gold", "horizon": "the source deadline",
        "invalidation": "above the source level"}
URL = "https://capitalchronicle.substack.com/p/gold-our-bearish-plan"


def copy(body):
    return {"post": f"{body}\n\n{PUBLIC_NOTICE}\n{CONFLICTS_NOTICE}"}


@pytest.mark.parametrize("link", [URL, f"[Full analysis]({URL})", f'<a href="{URL}">Full analysis</a>'])
def test_canonical_slug_keeps_the_complete_conditional_call_valid(link):
    body = compact_reader_conditional_call_text(CALL) + "\nFull analysis: " + link
    result = check_publication_copy(copy(body), conditional_calls=[CALL])
    assert result["conditional_call_count"] == 1


def test_analysis_link_alone_is_not_an_unconditional_call():
    assert check_publication_copy(copy("Full analysis: " + URL))["status"] == "PASS"


@pytest.mark.parametrize("body", [
    "We are bearish on gold. " + URL,
    f"[Our bearish view]({URL})",
    f'<a href="{URL}">Our bearish view</a>',
    "We are bullish on gold. " + URL,
])
def test_visible_unconditional_prose_still_fails(body):
    with pytest.raises(PublicOutputError, match="UNCONDITIONAL_CALL_FORBIDDEN"):
        check_publication_copy(copy(body))


def test_a_link_does_not_replace_the_authored_condition():
    with pytest.raises(PublicOutputError, match="CONDITIONAL_CALL_NOT_IN_AUTHORED_COPY"):
        check_publication_copy(copy(URL), conditional_calls=[CALL])


def test_url_handling_keeps_private_copy_checks():
    body = compact_reader_conditional_call_text(CALL) + "\n" + URL + "\nAccount balance is private."
    with pytest.raises(PublicOutputError, match="PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"):
        check_publication_copy(copy(body), conditional_calls=[CALL])
