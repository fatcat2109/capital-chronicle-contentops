"""Main outcomes reach the existing coordinator exactly once, without inferred scores."""
# ruff: noqa: F401, F811
# pytest imports and injects the named fixtures from the existing status-post tests.
from datetime import timedelta
import json
import sys

import pytest

from live_contentops import plan_status_posts_v1 as posts
from test_plan_status_posts_cc306 import NOW, event, main_root, plan, write_export
from test_plan_status_publication_cc306 import fake_host, no_real_snapshot
from test_publication_coordinator_v1 import FixtureTransport, _coordinator, _set_mode


@pytest.fixture(autouse=True)
def every_result_posts(monkeypatch):
    """Decision 106 makes result posts selective; these tests cover the full result machinery."""
    monkeypatch.setattr(posts, "RESULT_POSTS_SELECTIVE", False)


def source(tmp_path, result="STOPPED", *, correction=None, state="SCORED", count=2):
    p = plan("plan_gold", "XAUUSD", "BEARISH", 4070, 4085, invalid=4100)
    p["status"] = "FILLED" if state == "SCORED" else "EXPIRED"
    score = {"plan_id": p["plan_id"], "asset_id": "XAUUSD", "result": result,
             "outcome_id": "outcome_new" if correction else "outcome_first",
             "resolved_at_utc": "2026-11-05T12:20:00Z", "corrects_outcome_id": correction,
             "content_hash": "s" * 64, "score_basis": "PRIVATE_EXECUTION_DETAIL",
             "comment": "alpha track record 100% performance"}
    p["outcome"] = {"state": state, "result": result if state == "SCORED" else None,
                    "outcome_id": score["outcome_id"] if state == "SCORED" else None,
                    "score": score if state == "SCORED" else None}
    folder = write_export(tmp_path / "export", [p],
                          [event(p["plan_id"], p["status"], "2026-11-05T12:20:00Z")])
    path = folder / "plan-status.public.json"
    status = json.loads(path.read_bytes())
    status["scored_call_count"] = count
    path.write_text(json.dumps(status), encoding="utf-8")
    return folder


def queue(store, folder, main_root, **kw):
    return posts.queue_posts(store, folder, now=NOW, main_root=main_root, python=sys.executable, **kw)


@pytest.mark.parametrize("result", ["HIT", "STOPPED", "EXPIRED"])
def test_explicit_result_count_and_notices_use_no_free_text(tmp_path, main_root, result):
    folder = source(tmp_path, result)
    row = next(r for r in posts.read_transitions(folder, main_root=main_root) if r["to"] == "RESULT")
    text = posts.compose(row)["text"]
    assert f"plan result — {result.lower()} at Thu 5 Nov, 07:20 ET" in text
    assert "Scored calls: 2." in text
    assert posts.PUBLIC_NOTICE in text and posts.CONFLICTS_NOTICE in text
    assert not any(w in text.lower() for w in ("alpha", "track record", "performance", "100%", "execution", "https://", "target"))


def test_repeat_refresh_and_new_count_preserve_one_result_and_frozen_bytes(tmp_path, main_root):
    store, _, _ = _coordinator(tmp_path)
    folder = source(tmp_path)
    first = queue(store, folder, main_root)
    result = next(q for q in first["queued"] if q["state"] == "RESULT")
    before = store.get_outbox_message(result["key"])["payload"]
    source(tmp_path, count=3)
    second = queue(store, folder, main_root)
    assert not second["queued"]
    assert store.get_outbox_message(result["key"])["payload"] == before


def test_correction_is_a_new_post_and_original_never_changes(tmp_path, main_root):
    store, _, _ = _coordinator(tmp_path)
    first = queue(store, source(tmp_path), main_root)["queued"]
    original = next(q for q in first if q["state"] == "RESULT")
    before = store.get_outbox_message(original["key"])["payload"]
    correction = queue(store, source(tmp_path, "HIT", correction="outcome_first"), main_root)["queued"]
    assert len(correction) == 1 and correction[0]["key"] != original["key"]
    assert correction[0]["text"].startswith("Correction — Gold: plan result — hit")
    assert store.get_outbox_message(original["key"])["payload"] == before


@pytest.mark.parametrize("state", ["PENDING", "UNAVAILABLE"])
def test_no_result_is_inferred_for_pending_or_unavailable_outcomes(tmp_path, main_root, state):
    folder = source(tmp_path, state=state)
    assert not [r for r in posts.read_transitions(folder, main_root=main_root) if r["to"] == "RESULT"]


def test_explicit_untriggered_expiry_replaces_status_and_does_not_increase_count(tmp_path, main_root):
    store, _, _ = _coordinator(tmp_path)
    folder = source(tmp_path, state="NOT_SCORED_UNTRIGGERED")
    store.create_work_item(story_id=posts.WORK_ITEM_ID, title="Plan status posts (decision 79)", target_surface="MULTI_PLATFORM",
                          work_item_id=posts.WORK_ITEM_ID)
    store.register_outbox_message(message_id="announced", work_item_id=posts.WORK_ITEM_ID,
                                  destination=posts.DESTINATION, status="PUBLISHED",
                                  payload=json.dumps({"plan_id": "plan_gold", "state": "WAITING"}))
    queued = queue(store, folder, main_root)["queued"]
    assert len(queued) == 1 and queued[0]["state"] == "RESULT"
    assert "not scored. Scored calls: 2." in queued[0]["text"]


@pytest.mark.parametrize("count", [None, True, -1])
def test_missing_or_invalid_count_is_not_fabricated(tmp_path, main_root, count):
    store, _, _ = _coordinator(tmp_path)
    result = queue(store, source(tmp_path, count=count), main_root)
    assert result == {"status": "EXPORT_UNREADABLE", "cause": "PLAN_RESULT_SCORED_COUNT_INVALID"}


def test_old_scored_results_reach_all_three_live_consumers_once(tmp_path, main_root, no_real_snapshot):
    store, transport, coordinator = _coordinator(tmp_path, runtime=FixtureTransport())
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    folder = source(tmp_path)
    later = NOW + timedelta(days=4)
    queued = posts.queue_posts(store, folder, now=later, main_root=main_root, python=sys.executable)
    key = next(q["key"] for q in queued["queued"] if q["state"] == "RESULT")
    root = tmp_path / "posts"
    first = posts.publish_ready(store, now=later, root=root, host=fake_host,
                                coordinator_for=lambda key, folder: coordinator,
                                snapshot=lambda *a: pytest.fail("result must not capture later prices"))
    assert first["posts"] == [{"key": key, "status": "PUBLISHED", "per_destination":
                               {d: "DISPATCH_CONFIRMED" for d in posts.API_DESTINATIONS}}]
    assert sorted(transport.publish_calls) == sorted(posts.API_DESTINATIONS)
    assert not posts.publish_ready(store, now=later, root=root, host=fake_host,
                                   coordinator_for=lambda key, folder: coordinator)["posts"]
    payload = json.loads(store.get_outbox_message(key)["payload"])
    assert set(posts.destination_payloads(payload, card_id="card")) == set(posts.API_DESTINATIONS)
    assert (root / key / "run_context_v1.json").exists()
