"""CC-399 acceptance: the existing outbox consumes Main calls without new analytics."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys

import pytest

from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_plan_status_posts_cc306 import main_root, plan, event  # noqa: F401

NOW = datetime(2026, 11, 10, 8, tzinfo=timezone.utc)


def call(pid, asset="EURUSD", **changes):
    value = plan(pid, asset, "BULLISH", 1.12017, 1.12054, invalid=1.11824,
                 deadline="2026-11-10T15:00:00Z")
    value.update(run_id="morning-run", registered_at_utc="2026-11-10T07:45:00Z",
                 target=1.12406, tick_size=.0001, public_call_id="call_" + pid,
                 reader_reasons=["A weaker dollar supports the idea.", "The entry waits for a pullback."],
                 scenario_analysis={"horizon_end_utc": "2026-11-10T21:00:00Z",
                                    "base_case": {"probability_pct": 55}})
    value.update(changes)
    return value


def write(folder, plans, events, **fields):
    folder.mkdir(parents=True, exist_ok=True)
    status = {"schema": "CapitalChroniclePlanStatusV1", "schema_version": "1.0.0",
              "generated_at_utc": NOW.isoformat(), "plans": plans, "content_hash": "a" * 64,
              "record_summary": {"judged_count": 12, "right_count": 7, "trend_rule_right_count": 5}, **fields}
    (folder / "plan-status.public.json").write_text(json.dumps(status), encoding="utf-8")
    (folder / "plan-transitions.public.json").write_text(json.dumps({
        "schema": "CapitalChroniclePlanTransitionsV1", "schema_version": "1.0.0",
        "generated_at_utc": status["generated_at_utc"], "status_content_hash": "a" * 64,
        "transitions": events}), encoding="utf-8")
    return folder


def queue(store, folder, main_root, **kwargs):
    return posts.queue_posts(store, folder, now=NOW, main_root=main_root, python=sys.executable, **kwargs)


def rows(store):
    return [json.loads(r["payload"]) for r in store.list_outbox_messages(destination=posts.DESTINATION)]


@pytest.fixture
def five(tmp_path, main_root):
    seed = ContentOpsDurableStore(tmp_path / "seed.sqlite")
    copied = tmp_path / "copy.sqlite"
    with sqlite3.connect(seed.db_path) as source, sqlite3.connect(copied) as target:
        source.backup(target)
    store = ContentOpsDurableStore(copied)
    plans = [call(f"id{i:07}") for i in range(5)]
    events = [event(p["plan_id"], "WAITING", p["registered_at_utc"]) for p in plans]
    folder = write(tmp_path / "export", plans, events)
    return store, folder, plans, events


def test_five_plans_make_one_run_and_five_cards_once(five, main_root):
    store, folder, _, _ = five
    first = queue(store, folder, main_root)
    assert first["status"] == "OK"
    payloads = rows(store)
    run = next(r for r in payloads if r["kind"] == "run")
    calls = [r for r in payloads if r["kind"] == "setup"]
    assert len(payloads) == 6 and len(calls) == 5 and len(run["card_keys"]) == 5
    assert "run: 5." in run["text"]
    assert all(r["parent_key"] == run["key"] for r in calls)
    assert queue(store, folder, main_root)["queued"] == []
    assert len(rows(store)) == 6


def test_upgrade_reuses_legacy_shared_work_item_genesis(five, main_root):
    store, folder, _, _ = five
    original = store.create_work_item(story_id=posts.WORK_ITEM_ID, title="Plan status posts (decision 79)",
        target_surface="MULTI_PLATFORM", work_item_id=posts.WORK_ITEM_ID)
    result = queue(store, folder, main_root)
    assert result["status"] == "OK" and len(result["queued"]) == 6
    current = store.get_work_item(posts.WORK_ITEM_ID)
    assert current["created_at"] == original["created_at"] and current["title"] == original["title"]


def test_card_uses_target_tick_real_time_exit_chance_and_three_short_reasons(five, main_root):
    store, folder, _, _ = five
    queue(store, folder, main_root)
    card = next(r for r in rows(store) if r["kind"] == "setup")
    assert "Model target level: 1.1241." in card["text"]
    assert "1.1202–1.1205" in card["text"] and "1.1182" in card["text"]
    assert "Time exit: 10 Nov 16:00 ET" in card["text"]
    assert "Entry window to 10 Nov 10:00 ET" in card["text"]
    assert "55% (Capital Chronicle model estimate)" in card["text"]
    assert "12 calls judged, 7 right; trend rule: 5 right" in card["text"]
    assert len(card["reasons"]) == 2 and all(len(r) <= 200 for r in card["reasons"])
    assert "1.12017" not in card["text"]


def test_fill_and_winning_time_exit_keep_their_own_card_parent(five, main_root):
    store, folder, plans, events = five
    queue(store, folder, main_root)
    original = next(r for r in rows(store) if r["kind"] == "setup")
    store.set_outbox_status(original["key"], "PUBLISHED")
    pid = original["plan_id"]
    raw = next(p for p in plans if p["plan_id"] == pid)
    raw["status"] = "FILLED"
    raw["outcome"] = {"state": "SCORED", "result": "EXPIRED", "outcome_id": "outcome-time",
                      "score": {"plan_id": pid, "asset_id": raw["asset_id"], "outcome_id": "outcome-time",
                                "result": "EXPIRED", "resolved_at_utc": "2026-11-10T07:59:00Z",
                                "direction_correct": True}}
    events.append(event(pid, "FILLED", "2026-11-10T07:50:00Z"))
    write(folder, plans, events)
    queue(store, folder, main_root)
    later = [r for r in rows(store) if r["plan_id"] == pid and r["kind"] in {"update", "result"}]
    assert {r["kind"] for r in later} == {"update", "result"}
    assert all(r["parent_key"] == original["key"] for r in later)
    ending = next(r for r in later if r["kind"] == "result")
    assert "closed at its time exit, on our side of the entry" in ending["text"]
    assert "expired" not in ending["text"].lower() and "Scored calls:" not in ending["text"]


def test_unfilled_ending_is_owed_only_for_a_posted_setup(five, main_root):
    store, folder, plans, events = five
    queue(store, folder, main_root)
    original = next(r for r in rows(store) if r["kind"] == "setup")
    store.set_outbox_status(original["key"], "PUBLISHED")
    raw = next(p for p in plans if p["plan_id"] == original["plan_id"])
    raw["status"] = "EXPIRED"
    raw["outcome"] = {"state": "NOT_SCORED_UNTRIGGERED"}
    events.append(event(raw["plan_id"], "EXPIRED", "2026-11-10T07:59:00Z"))
    never = call("never_seen", status="EXPIRED", registered_at_utc="2026-11-08T00:00:00Z")
    plans.append(never)
    events += [event(never["plan_id"], "WAITING", "2026-11-08T00:00:00Z"),
               event(never["plan_id"], "EXPIRED", "2026-11-10T07:59:00Z")]
    write(folder, plans, events)
    queue(store, folder, main_root)
    endings = [r for r in rows(store) if r["kind"] == "result"]
    assert len(endings) == 1 and "not triggered" in endings[0]["text"]
    assert "our way" not in endings[0]["text"]  # not supplied by Main


def test_main_scorer_supplies_untriggered_direction_without_publisher_inference():
    assert cards.ending_words({"untriggered": True, "direction_correct": True}) == "not triggered; price then went our way"
    assert cards.ending_words({"untriggered": True, "direction_correct": False}) == "not triggered; price then went against us"
    assert cards.ending_words({"triggered_not_traded": True}) == "triggered, not traded"


def test_missing_fields_do_not_hide_available_inputs(five, main_root):
    store, folder, plans, events = five
    for p in plans:
        p.pop("target")
    write(folder, plans, events)
    queue(store, folder, main_root)
    calls = [r for r in rows(store) if r["kind"] == "setup"]
    assert len(calls) == 5 and all("Model target level" not in r["text"] for r in calls)
    assert all("55%" in r["text"] and "Time exit" in r["text"] for r in calls)


def test_mapped_instrument_does_not_borrow_book_target_or_tick():
    p = call("mapped", public_instrument={"name": "Euro FX", "symbol": "6E", "kind": "FUT",
        "direction": "BULLISH", "zone_low": 1.12, "zone_high": 1.121, "invalidation_level": 1.118,
        "entries": []})
    mapped = cards.card_plan(p)
    assert mapped["price_basis"] == "instrument"
    assert mapped["target"] is None and mapped["tick_size"] is None


def test_bad_reason_number_or_length_yields_no_reasons():
    assert cards.checked_reasons(["Support at 9999."], {"mechanism": "Support at 1.1200."}) == []
    assert len(cards.checked_reasons(["a " * 110], {})[0]) <= 200


def test_reasons_use_three_source_lines_and_fixed_glossary_without_a_model():
    raw = call("one", reader_reasons=[], scenario_analysis={
        "mechanism": "DXY weakness supports a rebound.", "priced": "Risk-off sentiment is priced.",
        "positioning": "COT points to crowded positioning.", "driver": "Never the fourth reason."})
    source = cards._reason_source(raw)
    reasons = cards.checked_reasons(cards.source_reasons(raw), source)
    assert len(reasons) == 3
    assert "dollar index" in reasons[0] and "futures positioning report" in reasons[2]
    assert "fourth" not in " ".join(reasons)


def test_rendered_chart_is_bound_to_exact_call_levels_and_source(five, main_root, tmp_path):
    from live_contentops.plan_call_card_media_v1 import render
    from PIL import Image
    store, folder, _, _ = five
    queue(store, folder, main_root)
    card = next(r for r in rows(store) if r["kind"] == "setup")
    asset = render(card, tmp_path / "render")
    assert Image.open(asset["path"]).size == (1440, 1440)
    assert asset["chart_spec"]["source_content_hash"] == "a" * 64
    assert asset["chart_spec"]["price_history"] is False
    assert asset["chart_spec"]["levels"]["target"] == [1.12406]
    assert asset["delivery_only"] and Path(asset["path"]).stat().st_size > 10000


def test_copied_store_five_cards_fill_and_ending_use_sole_coordinator(five, main_root, tmp_path):
    from test_publication_coordinator_v1 import FixtureTransport, _set_mode
    from test_plan_status_publication_cc306 import fake_host
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

    class Recorded(FixtureTransport):
        def __init__(self):
            super().__init__()
            self.intents = []
        def publish(self, *, destination, intent, authorization_context):
            self.publish_calls.append(destination)
            self.intents.append(intent)
            number = str(1000 + len(self.intents))
            if destination == "instagram_business" and intent["native_payload"].get("reuse_run_carousel"):
                number = intent["native_payload"]["carousel_parent_id"]
            return {"status": "SUCCESS", "id": number, "public_url": f"https://example.test/{destination}/{number}"}

    store, folder, plans, events = five
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    runtime = Recorded()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda d: {"readiness_state": "READY_AUTHENTICATED" if d == "substack_notes" else "READY_NON_BROWSER_BINDING"})
    queued = queue(store, folder, main_root)
    result = posts.publish_ready(store, now=NOW, latest_states=queued["latest_states"],
        root=tmp_path / "posts", host=fake_host, coordinator_for=lambda key, folder: coordinator)
    assert len(result["posts"]) == 6, result
    assert all(r["status"] == "PUBLISHED" for r in result["posts"]), result
    assert len(runtime.intents) == 6 * len(cards.DESTINATIONS)
    instagram_card_ids = {cards._reference(store, c["key"], "instagram_business")["public_object_id"]
                          for c in rows(store) if c["kind"] == "setup"}
    assert len(instagram_card_ids) == 1  # all five verified slots belong to one published run object
    run = next(r for r in rows(store) if r["kind"] == "run")
    card = next(r for r in rows(store) if r["kind"] == "setup")
    for destination in ("telegram", "threads", "x", "substack_notes"):
        first = next(i for i in runtime.intents if i["work_item_id"] == card["key"] and i["destination_plan"]["destination"] == destination)
        assert first["native_payload"]["reply_to_id"] == cards._reference(store, run["key"], destination)["public_object_id"]
    again = posts.publish_ready(store, now=NOW, root=tmp_path / "posts", host=fake_host,
                                 coordinator_for=lambda key, folder: coordinator)
    assert again["posts"] == [] and len(runtime.intents) == 6 * len(cards.DESTINATIONS)
    pid = card["plan_id"]
    raw = next(p for p in plans if p["plan_id"] == pid)
    raw["status"] = "FILLED"
    raw["outcome"] = {"state": "SCORED", "result": "EXPIRED", "outcome_id": "outcome-time",
        "score": {"plan_id": pid, "asset_id": raw["asset_id"], "outcome_id": "outcome-time",
                  "result": "EXPIRED", "resolved_at_utc": "2026-11-10T07:59:00Z", "direction_correct": True}}
    events.append(event(pid, "FILLED", "2026-11-10T07:50:00Z"))
    write(folder, plans, events)
    queue(store, folder, main_root)
    ended = posts.publish_ready(store, now=NOW, root=tmp_path / "posts", host=fake_host,
                                coordinator_for=lambda key, folder: coordinator)
    assert len(ended["posts"]) == 2 and all(r["status"] == "PUBLISHED" for r in ended["posts"]), ended
    assert len(runtime.intents) == 8 * len(cards.DESTINATIONS)
    for intent in runtime.intents[6 * len(cards.DESTINATIONS):]:
        destination = intent["destination_plan"]["destination"]
        package = intent["native_payload"]
        assert package["reply_to_id"] == cards._reference(store, card["key"], destination)["public_object_id"]
        if destination == "discord":
            assert package["discord_thread_parent_id"] == cards._reference(store, run["key"], destination)["public_object_id"]
        posts.validate_status_post_intent(store, intent)


def test_unconfirmed_parent_defers_only_its_destination(five, main_root, tmp_path, monkeypatch):
    from test_plan_status_publication_cc306 import fake_host
    store, folder, _, _ = five
    queue(store, folder, main_root)
    card = next(r for r in rows(store) if r["kind"] == "setup")
    monkeypatch.setattr(cards, "_reference", lambda s, k, d: None if d == "discord" else {
        "public_object_id": "12345", "public_object_url": "https://example.test/12345"})
    prepared = posts.prepare_post(store, card["key"], root=tmp_path / "posts", host=fake_host)
    assert {d["destination"] for d in prepared["destinations"]} == set(cards.DESTINATIONS) - {"discord"}
    assert prepared["deferred_destinations"] == [{"destination": "discord", "cause": "CARD_PARENT_NOT_CONFIRMED", "parent_key": card["parent_key"]}]


def test_discord_threads_use_official_bot_route_and_exact_card_reference(monkeypatch):
    from live_contentops import discord_live_adapter_v6 as adapter, live_telemetry_v6
    requests = []
    channel = "1519311669216673802"
    def send(req, **kwargs):
        requests.append(req)
        if "webhooks" in req.full_url:
            value = {"channel_id": channel}
        elif req.get_method() == "GET":
            value = {"id": "12345", "parent_id": channel, "type": 11, "thread_metadata": {"archived": False}}
        else:
            value = {"id": "67890", "channel_id": "12345", "content": "exact ending",
                     "message_reference": {"message_id": "98765"}}
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps(value).encode()
        return Response()
    monkeypatch.setattr(adapter, "read_secret", lambda name: "test-token")
    monkeypatch.setattr(adapter.urllib.request, "urlopen", send)
    monkeypatch.setattr(live_telemetry_v6, "classify_and_record_dispatch", lambda *a, **kw: None)
    result = adapter.execute_discord_post("exact ending", webhook_url="https://discord.com/api/webhooks/1/test",
        thread_parent_id="12345", thread_name="Calls", reply_to_message_id="98765")
    assert result["id"] == "67890"
    post = requests[-1]
    assert post.full_url == "https://discord.com/api/v10/channels/12345/messages"
    assert json.loads(post.data)["message_reference"]["message_id"] == "98765"
    assert len([r for r in requests if r.get_method() == "POST"]) == 1


def test_missing_discord_bot_token_is_definite_no_write(monkeypatch):
    from live_contentops import discord_live_adapter_v6 as adapter
    monkeypatch.setattr(adapter, "read_secret", lambda name: None)
    monkeypatch.setattr(adapter.urllib.request, "urlopen", lambda *a, **kw: pytest.fail("must not send"))
    result = adapter.execute_discord_post("exact", webhook_url="https://discord.com/api/webhooks/1/test",
                                         thread_parent_id="12345")
    assert result["definite_no_write"]
    assert result["reason_code"] == "DISCORD_CALL_THREAD_BOT_TOKEN_UNAVAILABLE"


@pytest.mark.parametrize("destination,field", [("facebook_page", "message"), ("instagram_business", "text")])
def test_own_card_comments_read_back_from_their_exact_parent(monkeypatch, destination, field):
    from live_contentops import facebook_page_adapter_v6 as facebook, instagram_adapter_v6 as instagram
    adapter = facebook if destination == "facebook_page" else instagram
    monkeypatch.setattr(adapter, "_get_json", lambda url, data: {"data": [{"id": "comment-1", field: "exact ending"}]})
    result = cards.readback_own_comment(destination, "comment-1", "our-card-1", "exact ending")
    assert result["verified"] and result["reply_parent_verified"]
    assert not cards.readback_own_comment(destination, "different-comment", "our-card-1", "exact ending")["verified"]


def test_note_request_opens_exact_parent_and_never_creates_an_unrelated_note():
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    parent_url = "https://substack.com/@deancapitalchronicle/note/c-12345"
    payload = {"text": "Our ending. " + cards.NOTICES, "reply_to_id": "c-12345", "reply_to_url": parent_url}
    request = NeoDestinationHandoff().request(destination="substack_notes", action="READBACK",
        intent={"native_payload": payload, "payload": payload["text"], "work_item_id": "card-ending"})
    assert request["entry_url"] == parent_url and request["reply_parent"]["public_object_id"] == "c-12345"
    assert any("Never create a top-level note" in step for step in request["steps"])


def test_instagram_run_creates_one_carousel_and_cards_do_not_publish_again(monkeypatch):
    from live_contentops import instagram_adapter_v6 as adapter
    sent = []
    images = [{"url": f"https://example.test/{i}.jpg", "sha256": adapter.sha256_bytes(b"fixture")} for i in range(5)]
    monkeypatch.setattr(adapter, "_instagram_id", lambda *a: "business-1")
    monkeypatch.setattr(adapter, "_instagram_token", lambda *a: "test-token")
    monkeypatch.setattr(adapter, "read_public_image_bytes", lambda url: b"fixture")
    monkeypatch.setattr(adapter, "_wait_for_instagram_container", lambda **kw: {"ready": True})
    def send(url, payload):
        sent.append((url, payload))
        return {"id": "media-1" if url.endswith("/media_publish") else str(len(sent))}, 100
    monkeypatch.setattr(adapter, "_post_form", send)
    result = adapter.execute_instagram_carousel(caption="This run: five.", images=images)
    assert result["id"] == "media-1"
    assert len([s for s in sent if s[0].endswith("/media_publish")]) == 1
    parent = next(p for _, p in sent if p.get("media_type") == "CAROUSEL")
    assert parent["children"] == "1,2,3,4,5"
    assert len([p for _, p in sent if p.get("is_carousel_item") == "true"]) == 5


def test_carousel_card_readback_checks_own_identity_exact_slot_and_pixels(monkeypatch):
    from live_contentops import instagram_adapter_v6 as adapter
    monkeypatch.setattr(adapter, "_get_json", lambda url, data: {"id": "media-1", "username": "official.capitalchronicle",
        "permalink": "https://www.instagram.com/p/our-run/", "media_type": "CAROUSEL_ALBUM",
        "caption": "This run: five.", "children": {"data": [{"media_url": "https://example.test/0.jpg"},
                                                                   {"media_url": "https://example.test/1.jpg"}]}})
    monkeypatch.setattr(adapter, "read_public_image_bytes", lambda url: url.encode())
    monkeypatch.setattr(adapter, "visual_similarity_to_local_file", lambda data, path: 1 if data.endswith(b"1.jpg") and path == "card-1.jpg" else 0)
    result = adapter.readback_call_carousel(media_id="media-1", expected_images=[{"path": "card-1.jpg", "index": 1}])
    assert result["verified"] and result["carousel_card_slots_verified"] == [1]
    assert not adapter.readback_call_carousel(media_id="media-1", expected_images=[{"path": "card-1.jpg", "index": 0}])["verified"]


def test_watch_ending_does_not_claim_an_open_trade_closed():
    raw = call("open", status="FILLED", outcome={"state": "UNAVAILABLE"})
    export = {"status": {"plans": [raw]}, "transitions": {"transitions": [
        event("open", "FILLED", "2026-11-10T07:50:00Z"), event("open", "VIEW_CHANGED", "2026-11-10T07:59:00Z")]}}
    assert cards._result_rows(export) == []


def test_hit_at_time_exit_uses_time_exit_words_not_a_target_claim():
    assert cards.ending_words({"result": "HIT", "score_basis": "BROKER_TIME_EXIT", "direction_correct": True}) == "closed at its time exit, on our side of the entry"


def test_announced_results_only_pending_unpublished_setup_gets_no_ending(five, main_root):
    store, folder, plans, events = five
    queue(store, folder, main_root)
    raw = plans[0]
    raw.update(status="EXPIRED", outcome={"state": "NOT_SCORED_UNTRIGGERED"})
    events.append(event(raw["plan_id"], "EXPIRED", "2026-11-10T07:59:00Z"))
    write(folder, plans, events)
    result = queue(store, folder, main_root)
    assert not any(r["kind"] == "result" for r in rows(store))
    assert any(r["cause"] == "PLAN_NEVER_ANNOUNCED" for r in result["not_posted"])


def test_cc432_summary_and_confirmed_page_replace_short_reasons(five, main_root):
    store, folder, plans, events = five
    for raw in plans:
        raw["registration_hash"] = "b" * 64
        raw["analysis_publication"] = {"plan_id": raw["plan_id"], "registration_hash": "b" * 64,
            "canonical_url": "https://capitalchronicle.substack.com/p/the-analysis",
            "summary": {"macro": "A weaker dollar is the economic driver.",
                        "fundamental": "The rate differential supports the view.",
                        "technical": "The idea waits for a pullback.",
                        "geopolitical": "No new event is confirmed.",
                        "priced_in": "Positioning leaves room for a reversal.",
                        "scenarios": "The alternative is a stronger dollar.",
                        "desk_process": "The critic challenged the timing; the final view kept a conditional entry."}}
    write(folder, plans, events)
    queue(store, folder, main_root)
    card = next(r for r in rows(store) if r["kind"] == "setup")
    assert "Macro: A weaker dollar" in card["text"]
    assert "How the desk reached its view:" in card["text"]
    assert "Full analysis: https://capitalchronicle.substack.com/p/the-analysis" in card["text"]
    assert "• A weaker dollar supports the idea." not in card["text"]
    for destination, payload in cards.destination_payloads(card, card_id="card").items():
        assert "https://capitalchronicle.substack.com/p/the-analysis" in payload["full_text"]
        if destination == "x":
            assert all(posts._x_length(part["text"]) <= 280 for part in payload["posts"])
        assert len(payload["text"]) <= (500 if destination == "threads" else 4096 if destination == "telegram" else 60000)
        if destination == "telegram" and len(payload["text"]) > 1024:
            assert payload["telegram_text_with_card_preview"]


@pytest.mark.parametrize("fault,cause", [("identity", "CC432_PLAN_BINDING_MISMATCH"),
    ("preview", "CC432_CONFIRMED_ANALYSIS_URL_REQUIRED"), ("private", "CC432_PUBLIC_SUMMARY_FILTER_FAILED")])
def test_cc432_envelope_cannot_mix_plans_preview_hosts_or_private_summary(fault, cause):
    raw = call("one", registration_hash="b" * 64)
    raw["analysis_publication"] = {"plan_id": "one", "registration_hash": "b" * 64,
        "canonical_url": "https://capitalchronicle.substack.com/p/the-analysis", "summary": {"macro": "A weaker dollar supports the view."}}
    if fault == "identity":
        raw["analysis_publication"]["plan_id"] = "another"
    elif fault == "preview":
        raw["analysis_publication"]["canonical_url"] = "https://example.github.io/the-analysis"
    else:
        raw["analysis_publication"]["summary"]["macro"] = "The desk is AI-run by Opus."
    assert cards.analysis_publication(raw) == ({}, cause)
