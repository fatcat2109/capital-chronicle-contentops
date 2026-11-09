"""The real native writer consumes the event brief, preserving frozen requests."""
import json

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired, NativeDesktopTurn


@pytest.mark.parametrize("kind,expected", [
    ("EVENT_PREVIEW", ("what_is_priced", "pre_event_range", "branch_confirmation")),
    ("EVENT_REVIEW", ("what_moved_when", "scenario_match")),
])
def test_live_native_writer_request_consumes_frame_and_replays_exactly(tmp_path, kind, expected):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run = "event-frame-test"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Test", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    args = dict(logical_invocation_id=run + ":write", prompt="Author the source-bound article.",
                governed_input={"article_type": kind},
                validator=lambda raw: (True, None, json.loads(raw), None))
    with pytest.raises(DesktopInputRequired) as first:
        turn(**args)
    prompt = first.value.request["prompt"]
    assert "CC107_EVENT_RESOLUTION_FRAME" in prompt
    assert all(section in prompt for section in expected)
    assert "New York time" in prompt
    assert "Do not route to the site" in prompt
    if kind == "EVENT_REVIEW":
        assert "Retrospective analysis, written on " in prompt
        assert "(ET)" in prompt and "CC333_REVIEW_WRITING_CLOCK" in prompt
        assert "outside `event_article_packet.copy`" in prompt
    with pytest.raises(DesktopInputRequired) as resumed:
        turn(**args)
    assert resumed.value.request["request_sha256"] == first.value.request["request_sha256"]
    assert resumed.value.request["prompt"] == prompt


def test_preparation_event_tag_selects_brief_but_source_prose_does_not():
    from live_contentops.event_article_guard_v1 import event_writer_guidance
    assert "pre_event_range" in event_writer_guidance({"selected_candidate": {
        "candidate_catalyst_tags": ["EVENT_PREVIEW", "bls-emsit-20261106"]}})
    assert event_writer_guidance({"source_pack": [{"text": "EVENT_PREVIEW"}]}) == ""
    assert "branch_confirmation" in event_writer_guidance({"source_pack": [{
        "preview_preparation": {"event_id": "bls-emsit-20261106"},
        "source_reuse_constraints": {"article_types": ["EVENT_PREVIEW"]}}]})


def test_native_brief_replay_preserves_issued_bytes_when_template_changes(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    run = "issued-event-brief"
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="Test", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    args = dict(logical_invocation_id=run + ":write", prompt="Author the exact sources.",
                governed_input={"article_type": "EVENT_REVIEW"},
                validator=lambda raw: (True, None, json.loads(raw), None))
    with pytest.raises(DesktopInputRequired) as issued:
        turn(**args)
    monkeypatch.setattr("live_contentops.event_article_guard_v1.event_writer_guidance",
                        lambda _: "\nCC107_EVENT_RESOLUTION_FRAME\nChanged future instructions.")
    with pytest.raises(DesktopInputRequired) as replayed:
        turn(**args)
    assert replayed.value.request == issued.value.request


@pytest.mark.parametrize("instant,expected", [
    ("2026-11-07T02:00:00+00:00", "6 November 2026 (ET)"),
    ("2026-07-01T02:00:00+00:00", "30 June 2026 (ET)"),
])
def test_review_request_dates_the_writing_clock_in_et(monkeypatch, instant, expected):
    from datetime import datetime
    from live_contentops import event_article_guard_v1 as guard
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat(instant).astimezone(tz)
    monkeypatch.setattr(guard, "datetime", Clock)
    text = guard.event_writer_guidance({"article_type": "EVENT_REVIEW"})
    assert "Retrospective analysis, written on " + expected in text
