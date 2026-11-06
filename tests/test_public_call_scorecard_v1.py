from copy import deepcopy
import json
import sqlite3

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.public_call_scorecard_v1 import build_scorecard, render_scorecard

AT = "2026-11-06T08:20:00Z"
END = "2026-11-07T00:00:00Z"
CALL = {"condition": "inflation is above the stated threshold", "market": "gold",
        "direction": "bearish", "horizon": "one day", "invalidation": "the prior high is regained"}


@pytest.fixture
def corpus(tmp_path):
    path = tmp_path / "store.sqlite3"
    store = ContentOpsDurableStore(str(path))
    store.create_work_item(story_id="posts", title="Posts", target_surface="MULTI_PLATFORM", work_item_id="posts")
    feed = tmp_path / "published.jsonl"
    feed.write_bytes(b"")
    return store, path, feed


def post(corpus, key, *, plan="plan-one", state="WAITING", status="PUBLISHED", call=None, confirmed=True,
         at=AT, dispatch_status="DISPATCH_CONFIRMED"):
    store, path, _ = corpus
    packet = {"plan_id": plan, "state": state, "at_utc": at,
              "conditional_calls": [deepcopy(CALL if call is None else call)] if state == "WAITING" else []}
    store.register_outbox_message(message_id=key, work_item_id="posts", destination="internal:plan-status-post",
                                  payload=json.dumps(packet), status=status)
    if confirmed:
        store.create_work_item(story_id=key, title="Public post", target_surface="MULTI_PLATFORM", work_item_id=key)
        store.register_outbox_message(message_id=key + "-channel", work_item_id=key, destination="TELEGRAM",
                                      payload="{}", status="SENT")
        with sqlite3.connect(path) as conn:
            conn.execute("INSERT INTO platform_dispatches (dispatch_id,message_id,platform,status,dispatched_at,"
                         "public_object_id,public_object_url) VALUES (?,?,?,?,?,?,?)",
                         (key + "-dispatch", key + "-channel", "TELEGRAM", dispatch_status, at, key,
                          "https://t.me/CapitalChronicle/" + str(len(key))))


def snapshot(corpus, **kwargs):
    return build_scorecard(corpus[0], feed_path=corpus[2], as_of_utc=END, **kwargs)


def test_every_public_call_keeps_original_and_full_denominator(corpus):
    for i, terminal in enumerate(["TRIGGERED", "INVALIDATED", "CANCELLED", "EXPIRED", "VIEW_CHANGED", "WAITING"]):
        post(corpus, f"setup-{i}", plan=f"plan-{i}")
        if terminal != "WAITING":
            post(corpus, f"state-{i}", plan=f"plan-{i}", state=terminal, at="2026-11-06T09:00:00Z")
    result = snapshot(corpus)
    assert result["total_calls"] == 6
    assert result["state_counts"] == {"TRIGGERED": 1, "INVALIDATED": 1, "WITHDRAWN": 2, "NOT_TRIGGERED": 1, "UNRESOLVED": 1}
    assert all(row["call"] == CALL and row["score"] is None for row in result["calls"])
    assert render_scorecard(result).count("If inflation") == 6


def test_partial_distribution_and_removed_posts_stay_in_population(corpus):
    post(corpus, "partial", status="PUBLISHING")
    post(corpus, "removed", plan="removed", dispatch_status="EXTERNAL_REMOVAL_REPORTED_NO_RETRY")
    post(corpus, "queued", plan="queued", status="READY_FOR_PUBLISHER", confirmed=False)
    post(corpus, "ambiguous", plan="ambiguous", status="PUBLISHING", dispatch_status="UNKNOWN_WRITE")
    assert snapshot(corpus)["total_calls"] == 2


def test_repeated_updates_do_not_edit_or_multiply_a_call_and_fills_never_escape(corpus):
    post(corpus, "setup")
    post(corpus, "same-setup")
    post(corpus, "trigger", state="TRIGGERED", at="2026-11-06T09:00:00Z")
    post(corpus, "private-execution", state="FILLED", at="2026-11-06T10:00:00Z")
    result = snapshot(corpus)
    assert result["total_calls"] == 1
    assert result["calls"][0]["state"] == "TRIGGERED"
    assert "FILLED" not in json.dumps(result)
    assert "plan-one" not in json.dumps(result)


def test_changed_wording_retains_both_versions(corpus):
    post(corpus, "first")
    changed = {**CALL, "invalidation": "the weekly high is regained"}
    post(corpus, "changed", call=changed)
    result = snapshot(corpus)
    assert result["total_calls"] == 2
    assert {r["call"]["invalidation"] for r in result["calls"]} == {CALL["invalidation"], changed["invalidation"]}


def test_public_date_is_converted_and_missing_public_clock_is_not_invented(corpus):
    post(corpus, "no-clock", confirmed=False)
    result = snapshot(corpus)
    text = render_scorecard(result)
    assert result["calls"][0]["first_published_at_utc"] is None
    assert "Time not retained" in text
    assert "2026-11-06 19:00:00 ET" in text
    assert "GMT+7" not in text and "UTC" not in text


def test_real_feed_reader_is_consumed_and_source_files_are_unchanged(corpus, monkeypatch):
    from live_contentops import public_call_scorecard_v1 as module
    row = {"conditional_calls": [CALL], "content_id": "substack:123", "published_at_utc": AT,
           "outlets": [{"name": "substack", "url": "https://capitalchronicle.substack.com/p/test"}]}
    observed = []
    def read(path):
        observed.append(path)
        return [deepcopy(row)]
    monkeypatch.setattr(module, "read_records", read)
    before = corpus[2].read_bytes()
    result = snapshot(corpus)
    assert observed == [corpus[2]]
    assert result["total_calls"] == 1 and result["calls"][0]["call"] == CALL
    assert corpus[2].read_bytes() == before


def test_post_event_and_pre_population_calls_do_not_change_as_of_denominator(corpus):
    post(corpus, "current")
    post(corpus, "future", plan="future", at="2026-11-08T08:20:00Z")
    post(corpus, "before", plan="before", at="2026-11-05T08:20:00Z")
    assert snapshot(corpus)["total_calls"] == 1
