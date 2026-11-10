"""Jim's scan answers, 10 Nov 2026 (item 3): X's own rules bind. Non-API automation of x.com "results in permanent
suspension" (X developer guidelines, read 9 Nov 2026), so no write to X goes through the Neo browser route."""
from __future__ import annotations

from pathlib import Path

import pytest

from live_contentops import neo_destination_handoff_v1 as handoff
from live_contentops.publication_coordinator_v1 import DEFINITE_NO_WRITE, normalize_dispatch_result


def never_called(request):
    raise AssertionError("an X write must never reach a browser request")


def test_platform_prohibitions_apply_to_neo_only():
    assert handoff.NON_API_AUTOMATION_PROHIBITED == {
        "x": "X_NON_API_AUTOMATION_PROHIBITED",
        "linkedin": "LINKEDIN_NON_API_AUTOMATION_PROHIBITED",
        "linkedin_company": "LINKEDIN_NON_API_AUTOMATION_PROHIBITED",
        "youtube": "YOUTUBE_NON_API_AUTOMATION_PROHIBITED",
        "instagram_business": "INSTAGRAM_NON_API_AUTOMATION_PROHIBITED",
    }
    for destination in ("substack", "substack_notes"):
        assert handoff._prohibited_write(destination) is None


@pytest.mark.parametrize("action", ["publish", "amend_existing"])
def test_an_x_write_is_a_definite_no_write_before_any_request(action):
    neo = handoff.NeoDestinationHandoff(native_executor=never_called)
    neo.request = lambda **kw: pytest.fail("no request is built for an X write")
    kwargs = {"destination": "x", "intent": {"work_item_id": "w"}, "authorization_context": {}}
    if action == "amend_existing":
        kwargs.update(public_object_id="1", public_object_url="https://x.com/Capitalnicle/status/1")
    result = getattr(neo, action)(**kwargs)
    assert result == {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True,
                      "reason_code": "X_NON_API_AUTOMATION_PROHIBITED", "public_write_performed": False}


def test_the_coordinator_records_the_refusal_as_a_definite_no_write():
    refused = handoff._prohibited_write("x")
    result = normalize_dispatch_result(refused, destination="x", surface="X_THREAD", transport_type="BROWSEROS_NEO_MCP")
    assert result["status"] == DEFINITE_NO_WRITE


def test_the_repository_contract_tells_every_agent():
    text = (Path(__file__).parents[1] / "AGENTS.md").read_text(encoding="utf-8")
    assert "## No posting on X through a browser" in text and "X_NON_API_AUTOMATION_PROHIBITED" in text
