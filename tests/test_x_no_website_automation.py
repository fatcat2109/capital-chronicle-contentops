"""Decision 112 restores X's existing Neo route; decision 109's other bars remain."""
from pathlib import Path

import pytest

from live_contentops import neo_destination_handoff_v1 as handoff


def test_platform_prohibitions_apply_to_neo_only():
    assert handoff.NON_API_AUTOMATION_PROHIBITED == {
        "linkedin": "LINKEDIN_NON_API_AUTOMATION_PROHIBITED",
        "linkedin_company": "LINKEDIN_NON_API_AUTOMATION_PROHIBITED",
        "youtube": "YOUTUBE_NON_API_AUTOMATION_PROHIBITED",
        "instagram_business": "INSTAGRAM_NON_API_AUTOMATION_PROHIBITED",
    }
    for destination in ("x", "substack", "substack_notes"):
        assert handoff._prohibited_write(destination) is None


@pytest.mark.parametrize("action", ["publish", "amend_existing"])
def test_x_reaches_the_existing_authorized_request_seam(monkeypatch, action):
    adapter = handoff.NeoDestinationHandoff()
    class RequestReached(Exception):
        pass
    def request(**kwargs):
        assert kwargs["destination"] == "x"
        assert kwargs["action"] == ("PUBLISH" if action == "publish" else "EDIT_EXISTING")
        raise RequestReached
    monkeypatch.setattr(adapter, "request", request)
    kwargs = {"destination": "x", "intent": {"work_item_id": "w"}, "authorization_context": {}}
    if action == "amend_existing":
        kwargs.update(public_object_id="1", public_object_url="https://x.com/Capitalnicle/status/1")
    with pytest.raises(RequestReached):
        getattr(adapter, action)(**kwargs)


def test_latest_repository_contract_restores_x_and_keeps_replies_parked():
    text = (Path(__file__).parents[1] / "AGENTS.md").read_text(encoding="utf-8")
    assert "## X posts again as before" in text and "decision 112" in text
    assert "replies stay parked" in text.lower()
