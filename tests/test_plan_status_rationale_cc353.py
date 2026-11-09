"""Main export -> outbox -> the sole publisher's frozen destination copy."""
from datetime import datetime, timezone
import json
import sys

import pytest

from live_contentops import plan_status_posts_v1 as p
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE, CONFLICTS_NOTICE
from live_contentops.neo_destination_handoff_v1 import _public_url, NeoDestinationHandoff
from test_plan_status_posts_cc306 import main_root, plan, event, write_export, NOW  # noqa: F401
from test_plan_status_publication_cc306 import fake_host, no_real_snapshot  # noqa: F401
from test_publication_coordinator_v1 import _coordinator, _set_mode


def export_plan():
    row = plan("plan_why", "USDJPY", "BEARISH", 158.2, 158.3, invalid=158.65)
    row["scenario_analysis"] = {
        "base_case": {"market_move": "A rally into the range top fades as the dollar weakens.", "probability_pct": 55},
        "main_alternative": {"market_move": "Hot CPI widens the US-Japan rate gap.", "probability_pct": 35},
        "confirmations": "The range top held on three sessions; CFTC COT shows crowded yen longs as of 3 Nov.",
        "invalidation_text": "A close above the range top breaks the range thesis.",
    }
    row.update(mechanism="Falling US yields narrow the rate gap.", priced="A range rather than a breakout.",
               positioning="CFTC COT shows yen longs as of 3 Nov.", driver="US CPI is the next catalyst.",
               zone_reason="Three prior rejections mark the upper shelf.",
               invalidation_reason="A close beyond the shelf reverses the premise.",
               acceptance="The range top holds.", opposite_mechanism="Hot CPI revives dollar demand.",
               target=777777, after_cost_rr=2.9, size=12345, fill=45678, pnl=99887)
    return row


def composed(source=None, state="WAITING", first=True):
    source = source or export_plan()
    row = p._row(plan_id=source["plan_id"], symbol=source["asset_id"], to=state,
                 at_utc=NOW.isoformat(), cause=state, plan=p._built_plan(source, state=state))
    return {"symbol": row["symbol"], "state": state, **p.compose(row, first_plan_post=first)}


@pytest.mark.parametrize("state", ["WAITING", "TRIGGERED"])
def test_rationale_crosses_export_queue_coordinator_and_native_payload(tmp_path, main_root, state):
    folder = write_export(tmp_path / "export", [export_plan()], [event("plan_why", state, NOW.isoformat())])
    store, _, coordinator = _coordinator(tmp_path)
    queued = p.queue_posts(store, folder, now=NOW, main_root=main_root, python=sys.executable)
    assert len(queued["queued"]) == 1 and not queued["rationale_causes"]
    key = queued["queued"][0]["key"]
    row = p._row_payload(store, key)
    package = p.prepare_post(store, key, root=tmp_path / "posts", host=fake_host)
    store.create_work_item(story_id=key, title="Plan", target_surface="MULTI_PLATFORM", work_item_id=key)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    coordinator.register_plan(key, package)
    intents = [json.loads(m["payload"]) for m in store.list_outbox_messages() if m["work_item_id"] == key]
    assert {i["destination_plan"]["destination"] for i in intents} == set(p.POST_DESTINATIONS)
    for intent in intents:
        p.validate_status_post_intent(store, intent)
        d = intent["destination_plan"]["destination"]
        payload = intent["native_payload"]
        parts = [post["text"] for post in payload.get("posts") or []] or [payload["text"]]
        assert all(len(text) <= p.LIMITS[d] for text in parts)
        assert "Capital Chronicle model estimate" in payload["full_text"]
        assert "55%" in payload["full_text"] and "35%" in payload["full_text"]
        assert PUBLIC_NOTICE in payload["full_text"] and CONFLICTS_NOTICE in payload["full_text"]
        assert not any(str(n) in payload["full_text"] for n in (777777, 2.9, 12345, 45678, 99887))
        if d in {"telegram", "discord", "substack_notes"}:
            assert "CFTC COT" in payload["text"] and "Why this zone" in payload["text"]
            assert "Falling US yields narrow the rate gap." in payload["text"]
        assert "https://" not in payload["full_text"]
    assert row["why"]


@pytest.mark.parametrize("private", ["Target: 777777.", "After-cost R:R 2.9.", "Position size: 12345.",
    "Filled at 45678.", "P&L 99887.", "Account 279805139.", "Polymarket probability 65%.",
    "Prediction-market odds 70%.", "Aim for 777777.", "Profit target 777777."])
def test_private_prose_is_removed_but_public_reason_survives(private):
    source = export_plan()
    source["mechanism"] = "Yields narrow the rate gap. " + private
    post = composed(source)
    assert "Yields narrow the rate gap." in post["text"]
    assert private not in post["text"]
    assert all(str(n) not in post["text"] for n in (777777, 12345, 45678, 99887, 279805139))


def test_no_inferred_complement_and_missing_scenario_still_posts_and_counts(tmp_path, main_root):
    source = export_plan()
    source["scenario_analysis"]["main_alternative"]["probability_pct"] = None
    assert "45%" not in composed(source)["text"]
    assert "Main alternative (Capital Chronicle model estimate)" in composed(source)["text"]
    source = plan("plan_why", "USDJPY", "BEARISH", 158.2, 158.3, invalid=158.65)
    folder = write_export(tmp_path / "export", [source], [event("plan_why", "WAITING", NOW.isoformat())])
    store = ContentOpsDurableStore(tmp_path / "store.db")
    result = p.queue_posts(store, folder, now=NOW, main_root=main_root, python=sys.executable)
    assert len(result["queued"]) == 1
    assert result["rationale_causes"] == {"SCENARIO_ANALYSIS_MISSING": 1}
    assert "Why:" not in result["queued"][0]["text"]


def test_later_trigger_keeps_short_status_and_first_trigger_explains():
    assert "Why:" not in composed(state="TRIGGERED", first=False)["text"]
    assert "Why:" in composed(state="TRIGGERED", first=True)["text"]


def test_long_full_text_uses_bounded_parts_with_all_reasons(tmp_path, main_root):
    source = export_plan()
    source["mechanism"] = "Falling US yields narrow the rate gap. " * 80
    folder = write_export(tmp_path / "export", [source], [event("plan_why", "WAITING", NOW.isoformat())])
    store = ContentOpsDurableStore(tmp_path / "store.db")
    q = p.queue_posts(store, folder, now=NOW, main_root=main_root, python=sys.executable)
    key = q["queued"][0]["key"]
    packet = p.prepare_post(store, key, root=tmp_path / "posts", host=fake_host)
    assert packet["continuations"]
    for package in [packet, *packet["continuations"]]:
        work_id = package.get("work_item_id", key)
        parsed = p.validate_status_post_plan(store, work_id, package)
        for d in package["destinations"]:
            assert len(d["payload"]) <= p.LIMITS[d["destination"]] or d["destination"] == "x"
            intent = {"work_item_id": work_id, "plan_status_post": key,
                "plan_status_part": package.get("plan_status_part", 0), "output_dir": package["output_dir"],
                "destination_plan": d, "native_payload": parsed["payloads"][d["destination"]]}
            p.validate_status_post_intent(store, intent)
    full = " ".join(d["payload"].split("\n\n")[0] for package in [packet, *packet["continuations"]]
                    for d in package["destinations"] if d["destination"] == "telegram")
    assert full.count("Falling US yields narrow the rate gap.") == 80


def test_note_url_must_name_our_exact_public_object():
    assert _public_url("substack_notes", "https://substack.com/@deancapitalchronicle/note/c-123", "c-123")
    assert not _public_url("substack_notes", "https://substack.com/@other/note/c-123", "c-123")
    assert not _public_url("substack_notes", "https://substack.com/@deancapitalchronicle/note/c-123", "c-456")


@pytest.mark.parametrize("long", [False, True])
def test_existing_minute_consumer_sends_full_parts_and_issues_both_browser_destinations(tmp_path, main_root, long):
    source = export_plan()
    if long:
        source["mechanism"] = "Falling US yields narrow the rate gap. " * 80
    folder = write_export(tmp_path / "export", [source], [event("plan_why", "WAITING", NOW.isoformat())])
    store, transport, coordinator = _coordinator(tmp_path)
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    queued = p.queue_posts(store, folder, now=NOW, main_root=main_root, python=sys.executable)
    key = queued["queued"][0]["key"]
    root = tmp_path / "posts"
    result = p.publish_ready(store, now=NOW, root=root, host=fake_host,
                           coordinator_for=lambda *a: coordinator)
    assert result["posts"][0]["status"] == "PUBLISHED"
    assert set(transport.publish_calls) == set(p.POST_DESTINATIONS)
    assert store.get_outbox_message(key)["status"] == "PUBLISHED"
    before = list(transport.publish_calls)
    assert p.publish_ready(store, now=NOW, root=root, host=fake_host,
                           coordinator_for=lambda *a: coordinator)["posts"] == []
    assert transport.publish_calls == before
    if long:
        assert transport.publish_calls.count("telegram") > 1


def test_notes_uses_existing_neo_request_and_exact_public_readback():
    value = {"work_item_id": "plan-post", "plan_status_post": "plan-post", "package_identity": "plan-post",
             "canonical_url": None, "native_payload": {"text": "Why: yields narrow. " + PUBLIC_NOTICE},
             "destination_plan": {"payload_hash": "f" * 64}}
    handoff = NeoDestinationHandoff()
    request = handoff.request(destination="substack_notes", action="READBACK", intent=value,
        public_object_id="c-123", public_object_url="https://substack.com/@deancapitalchronicle/note/c-123")
    assert request["expected_identity"] == "@deancapitalchronicle"
    assert request["surface"] == "SUBSTACK_NOTE"
    assert request["content_binding"]["expected_text_segments"] == [value["native_payload"]["text"]]


def test_real_native_composition_queues_note_without_network_or_canonical_article(tmp_path, main_root):
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
    source = export_plan()
    folder = write_export(tmp_path / "export", [source], [event("plan_why", "WAITING", NOW.isoformat())])
    store = ContentOpsDurableStore(tmp_path / "store.db")
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    queued = p.queue_posts(store, folder, now=NOW, main_root=main_root, python=sys.executable)
    key = queued["queued"][0]["key"]
    root = tmp_path / "posts"
    result = p.start_x(store, key, root=root, host=fake_host, now=NOW,
        native_invocation_id="cc353-controlled", destination="substack_notes")
    executor = NativeNeoExecutor(store, operation_id=key, output_dir=root / key / "native-neo",
        native_invocation_id="cc353-controlled", allow_publish=True, identity_at_action=True)
    requests = executor.pending()
    assert any(r["request"]["destination"] == "substack_notes" and r["request"]["action"] == "PUBLISH"
               for r in requests), result
