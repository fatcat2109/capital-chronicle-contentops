"""The gold thread's retained inputs flow into one new, source-bound thread."""
from copy import deepcopy
from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_reader_editorial_v1 as editorial
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_plan_status_posts_cc306 import event, main_root  # noqa: F401
from test_plan_call_cards_cc399 import controlled_tradingview, write, rows  # noqa: F401
from test_plan_analysis_pages_cc432 import source  # noqa: F401
from test_plan_analysis_distribution_cc435 import confirm
from test_plan_status_publication_cc306 import fake_host


FIXTURES = Path(__file__).parents[1] / "docs/publisher/CC-549/fixtures"


@pytest.fixture
def single_pass_run(source):
    root, folder, plan, _ = source
    result = json.loads((folder / "desktop-manual-result.json").read_bytes())
    result["native_synthesis"]["candidates"][0]["candidate_id"] = "cand_macro_eurusd"
    result.update(primary_analysis={}, critical_review={})
    for name in ("analysis-native.json", "desktop-manual-result.json"):
        (folder / name).write_text(json.dumps(result), encoding="utf-8")
    plan["analysis_result_hash"] = pages.sha256_of(result)
    freeze = json.loads((folder / "final-decision-freeze.json").read_bytes())
    freeze["qualitative_result_hash"] = plan["analysis_result_hash"]
    (folder / "final-decision-freeze.json").write_text(json.dumps(freeze), encoding="utf-8")
    for name in ("role-pack.json", "role-evidence.json", "primary-native.json",
                 "critical-native.json", "owner-native.json"):
        (folder / name).unlink()
    return root, folder, plan


def test_single_pass_original_analysis_reaches_the_real_page_writer(single_pass_run, tmp_path):
    root, folder, plan = single_pass_run
    calls = []

    def writer(prompt, **options):
        calls.append(prompt)
        assert "Base chance 55%; support 1.12; alternative 35%." in prompt
        assert "analysis-native.json" in prompt
        return {"status": "FAILED", "cause": "CONTROLLED_WRITER_STOP"}

    result = editorial.prepare_page(plan, output_dir=tmp_path / "page", run_root=root, call=writer)
    assert result["status"] == "PAGE_TEXT_UNAVAILABLE"
    assert result["cause"] == "CONTROLLED_WRITER_STOP"
    assert len(calls) == 1
    run = pages.load_run(plan, run_root=root)
    packet = reader.source_packet(plan, run)
    rationale = next(s for s in packet["sources"] if s["ref"]["pointer"].endswith("/rationale"))
    assert rationale["ref"]["file"] == "analysis-native.json"
    assert pages._source_text(run, rationale["ref"]) == rationale["text"]
    assert run["manifest"]["analysis-native.json"]["path"] == str(folder / "analysis-native.json")
    assert "role-pack.json" not in run["manifest"]
    assert "role-evidence.json" not in run["manifest"]


@pytest.mark.parametrize("document,reason", [
    ("desktop-manual-result.json", "PLAN_ANALYSIS_RESULT_HASH_MISMATCH"),
    ("final-decision-freeze.json", "PLAN_ANALYSIS_FREEZE_RESULT_MISMATCH"),
])
def test_single_pass_keeps_exact_result_and_freeze_binding(single_pass_run, document, reason):
    root, folder, plan = single_pass_run
    path = folder / document
    value = json.loads(path.read_bytes())
    if document == "final-decision-freeze.json":
        value["qualitative_result_hash"] = "wrong"
    else:
        value["changed"] = True
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match=reason):
        pages.load_run(plan, run_root=root)


@pytest.fixture
def gold():
    raw = json.loads((FIXTURES / "gold-plan-thread-181.json").read_bytes())
    run = json.loads((FIXTURES / "gold-public-reasoning.json").read_bytes())
    run["source_plan"] = raw
    return raw, run


def alert_row(raw):
    terms = reader.thread_terms(raw)
    return {"kind": "setup", "state": "WAITING", "symbol": raw["asset_id"],
            "levels": cards.card_plan(raw), "instrument_title": terms["market"],
            "at_utc": raw["registered_at_utc"], "registered_at_utc": raw["registered_at_utc"],
            "entry_deadline_utc": terms["entry_deadline_utc"], "time_exit_utc": terms["time_exit_utc"],
            "source_plan": raw, "source_plan_registration": raw["registration_hash"],
            "state_alert_contract": alerts.CONTRACT, "state_alert_source_sha256": posts._sha(raw),
            "thread_contract": reader.THREAD_CONTRACT, "price_basis": terms["price_basis"]}


def authored(source):
    # Retained findings, deliberately presented as a controlled writer return.
    # No model call, new market analysis or production store is used by a test.
    rationale = next(s for s in source["sources"] if s["ref"]["pointer"].endswith("/rationale"))
    text = "We see inflation repricing weighing on gold."
    return {"title": "A controlled writer return", "subtitle": "The case and its countercase.",
            "introduction": "We see a conditional plan.", "sections": {key: {
                "paragraphs": [{"text": text, "source_ids": [rationale["id"]]}], "summary": text}
                for key, _ in pages.READER_SECTIONS}}


def test_gold_alert_reply_and_page_share_exact_levels_clocks_and_voice(gold):
    raw, run = gold
    source = reader.source_packet(raw, run, thread=True, original_probabilities=True)
    manuscript = editorial.bind_manuscript(authored(source), source, raw)
    pages.validate_manuscript(raw, manuscript, run)
    payload, _, _ = pages._assemble(raw, manuscript, run)
    packet = {"native_payload": payload, "source_plan": raw, "manuscript": manuscript,
              "summary": {key: value["summary"] for key, value in manuscript["sections"].items()}}
    first = cards.compose(alert_row(raw))["text"]
    reply = pages.structured_summary(packet, "telegram", "https://capitalchronicle.substack.com/p/gold-controlled-replay")
    invalidation = "Spot close above 3,972.6; MGC invalidation above 4,004.4"
    for text in (first, reply, payload["title"]):
        assert invalidation in text
        reader.check_thread_text(text)
    for text in (first, reply, payload["body_markdown"]):
        assert "Entry can start until Fri 13 Nov, 1:00 AM ET." in text
        assert "Filled positions close by Fri 13 Nov, 8:15 AM ET." in text
        assert "Ends " not in text
    assert "price trades at 3,954.4" in first
    assert "Target level: 3,876.4." in first
    assert "3,954–3,964" not in first
    assert "4004 invalidation" not in payload["title"]
    assert "Use first person." not in editorial.GUIDANCE


def test_each_public_level_and_clock_has_its_own_export_field(gold):
    raw, run = gold
    source = reader.source_packet(raw, run, thread=True)
    terms = source["thread_terms"]
    for ref in terms["refs"]:
        assert any(s["ref"] == ref and s["text"] == pages._source_text(run, ref) for s in source["sources"])
    assert {"file": "plan-export", "pointer": "/invalidation_conditions/0/threshold"} in terms["refs"]
    assert pages._source_text(run, {"file": "plan-export", "pointer": "/public_instrument/entries/0/zone_low",
                                   "transform": "PUBLIC_TICK"}) == "3,954.4"


@pytest.mark.parametrize("text", [
    "I watch gold's inflation repricing.", "I'm watching gold.", "My view is conditional.",
    "The supplied historical review did not establish a dependable advantage.",
    "We leave the provided rebound alternative unquantified.",
    "The pack points to a rebound.", "The review given points to a rebound.",
])
def test_observed_voice_and_process_defects_are_refused(text):
    with pytest.raises(ValueError, match="CC549_"):
        reader.check_thread_text(text)


@pytest.mark.parametrize("text", ["We track the CPI repricing.", "We watch for short covering."])
def test_empty_force_summary_is_omitted_from_actual_reply(gold, text):
    raw, run = gold
    source = reader.source_packet(raw, run, thread=True)
    value = authored(source)
    value["sections"]["macro"]["summary"] = text
    manuscript = editorial.bind_manuscript(value, source, raw)
    assert manuscript["sections"]["macro"]["summary"] == ""
    packet = {"native_payload": {"title": manuscript["title"]}, "source_plan": raw, "manuscript": manuscript,
              "summary": {key: section["summary"] for key, section in manuscript["sections"].items()}}
    reply = pages.structured_summary(packet, "telegram", "https://capitalchronicle.substack.com/p/gold-controlled-replay")
    assert "Macro:" not in reply
    assert text not in reply


def test_unmapped_prices_name_gold_and_never_name_mgc(gold):
    raw, _ = gold
    raw["public_instrument"] = {"name": "Micro gold", "symbol": "MGC", "kind": "FUT", "contract_month": "2026-12"}
    first = alerts.compose(alert_row(raw))["text"]
    assert "Gold" in first and "Spot close above 3,972.6" in first
    assert "MGC" not in first and "Micro gold" not in first
    assert "3,954–3,964" in first


def test_expired_update_distinguishes_entry_window_from_position_horizon(gold):
    raw, _ = gold
    row = alert_row(raw)
    row.update(kind="expired", state="EXPIRED", at_utc=raw["entry_deadline_utc"])
    text = alerts.compose(row)["text"]
    assert "the entry window ended" in text and "the position closed" not in text
    assert "1:00 AM ET" in text and "8:15 AM ET" in text


def test_existing_issued_alert_and_page_keep_their_original_composer(gold):
    raw, _ = gold
    row = alert_row(raw)
    row.pop("thread_contract")
    assert "Entry valid until " in alerts.compose(row)["text"]
    old = json.loads((FIXTURES / "gold-page-stored.json").read_bytes())
    packet = {"native_payload": {"title": old["manuscript"]["title"]},
              "manuscript": old["manuscript"], "summary": old["summary"]}
    assert "supplied" in pages.structured_summary(packet, "telegram", "https://capitalchronicle.substack.com/p/gold-original")


@pytest.fixture
def long_alert(gold, tmp_path, main_root):
    raw, _ = gold
    raw.update(
        asset_id="BTCUSD", status="WAITING", registered_at_utc="2026-11-17T16:43:13Z",
        not_before_utc="2026-11-17T16:43:13Z", entry_deadline_utc="2026-11-17T19:30:00Z",
        expires_at_utc="2026-11-17T19:30:00Z", time_exit_utc="2026-11-18T18:30:00Z",
        invalidation_conditions=[{"field": "high", "operator": "GTE", "threshold": 66450}],
    )
    raw["public_instrument"].update(
        name="Micro Bitcoin", symbol="MBT", exchange="CME", contract_month="2026-11",
        entries=[{"kind": "LIMIT", "zone_low": 63885, "zone_high": 65160}],
        zone_low=63885, zone_high=65160, invalidation_level=66415, target_level=61115, tick_size=5,
    )
    now = posts._utc(raw["registered_at_utc"]) + timedelta(minutes=1)
    folder = write(tmp_path / "export", [raw], [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])],
                   generated_at_utc=now.isoformat())
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    posts.queue_posts(store, folder, now=now, main_root=main_root)
    queued, = rows(store)
    return store, folder, now, queued


def test_long_plan_preview_renders_the_same_terms_as_the_chart_thread(long_alert, main_root):
    store, folder, now, queued = long_alert
    key = queued["key"]
    frozen = store.get_outbox_message(key)["payload"]

    result = posts.queue_posts(store, folder, now=now, main_root=main_root, dry_run=True, render_all=True)
    assert result["status"] == "OK"
    preview, = result["rendered_posts"]
    copies = cards.destination_payloads(
        queued, card_id="dry-run-" + key, chart_credit=True, complete_levels=True,
    )
    assert set(copies) == set(cards.DESTINATIONS)
    for destination, payload in copies.items():
        parts = [payload["text"], *payload.get("reply_texts", [])]
        assert payload["full_text"] == "\n\n".join(parts), destination
        for notice in (posts.PUBLIC_NOTICE, posts.CONFLICTS_NOTICE):
            assert sum(part.count(notice) for part in parts) == 1, destination
        assert payload["text"].count(posts.CHART_CREDIT) == 1, destination

    chart_thread = copies["threads"]
    assert preview["destinations"]["threads"] == chart_thread
    assert chart_thread["reply_texts"]  # A real split is needed to catch the repeated footer.
    assert chart_thread["root_text"].count(cards.NOTICES) == 1
    assert all(len(text) <= 500 for text in [chart_thread["root_text"], *chart_thread["reply_texts"]])
    for phrase in ("63,885–65,160", "at or above 66,450 before entry", "above 66,415 after entry",
                   "Entry can start until Tue 17 Nov, 2:30 PM ET.", "Filled positions close by Wed 18 Nov, 1:30 PM ET."):
        assert phrase in chart_thread["full_text"]
    assert store.get_outbox_message(key)["payload"] == frozen


@pytest.mark.parametrize("issued_destination", ["discord", "threads", "threads_ready"])
def test_threads_notice_layout_respects_an_existing_intent(long_alert, tmp_path, monkeypatch, issued_destination):
    from test_minute_consumer_cc515 import dispatch

    store, _, now, queued = long_alert
    key = queued["key"]
    # Reproduce a retained row created before either layer-copy contract.
    queued = {field: value for field, value in queued.items()
              if field not in {"analysis_copy_contract", "analysis_layer_quotes", "analysis_layer_gaps", "analysis_link"}}
    queued.update(alerts.compose(queued))
    store.finalize_outbox_payload_before_dispatch(message_id=key, payload=json.dumps(queued), status=posts.READY)

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz) if tz else now.replace(tzinfo=None)

    monkeypatch.setattr(cards, "datetime", Clock)
    options = {"root": tmp_path / "posts", "destinations": ("threads",), "host": fake_host}
    initial = cards.prepare_post(store, key, **options)
    context_path = Path(initial["output_dir"]) / "run_context_v1.json"
    context = json.loads(context_path.read_bytes())
    context.pop("status_post_threads_single_notice")  # A package prepared before CC-729.
    context_path.write_text(json.dumps(context), encoding="utf-8")
    legacy = cards.destination_payloads(queued, card_id=initial["status_post_card_id"],
        chart_credit=True, complete_levels=True, repeat_threads_notices=True)["threads"]
    assert legacy["full_text"].count(cards.NOTICES) > 1
    store.create_work_item(story_id=key, work_item_id=key, title="Call card", target_surface="MULTI_PLATFORM")
    if issued_destination == "threads_ready":
        ids = cards._dispatch_ids(key, "threads")
        store.register_outbox_message(message_id=ids["message_id"], work_item_id=key,
            destination="threads", payload=json.dumps(legacy), status="READY")
    else:
        dispatch(store, queued, issued_destination, "UNKNOWN_WRITE")

    plan = cards.prepare_post(store, key, **options)
    checked = posts.validate_status_post_plan(store, key, plan)["payloads"]["threads"]
    if issued_destination.startswith("threads"):
        assert checked == legacy
    else:
        assert checked["full_text"] == initial["destinations"][0]["payload"]
        assert checked["full_text"].count(cards.NOTICES) == 1


def test_live_queue_freezes_thread_terms_for_later_page_and_state(gold, tmp_path, main_root, monkeypatch):
    raw, _ = gold
    raw["status"] = "WAITING"
    now = posts._utc(raw["registered_at_utc"]) + timedelta(minutes=1)
    folder = write(tmp_path / "export", [raw], [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])],
                   generated_at_utc=now.isoformat())
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    posts.queue_posts(store, folder, now=now, main_root=main_root)
    first, = rows(store)
    assert first["thread_contract"] == reader.THREAD_CONTRACT
    assert "MGC invalidation above 4,004.4" in first["text"]
    frozen = store.get_outbox_message(first["key"])["payload"]
    later = deepcopy(raw)
    later["public_instrument"]["invalidation_level"] = 4999
    later["status"] = "FILLED"
    at = now + timedelta(minutes=1)
    folder = write(folder, [later], [event(raw["plan_id"], "WAITING", raw["registered_at_utc"]),
                                   event(raw["plan_id"], "FILLED", at.isoformat())], generated_at_utc=at.isoformat())
    posts.queue_posts(store, folder, now=at, main_root=main_root)
    child = next(row for row in rows(store) if row["kind"] == "update")
    assert "4,004.4" in child["text"] and "4,999" not in child["text"]
    alerts.validate(child)
    assert store.get_outbox_message(first["key"])["payload"] == frozen
    seen = []
    def prepare(plan, **options):
        seen.append(plan)
        return {"status": "PAGE_TEXT_UNAVAILABLE", "cause": "CONTROLLED_WRITER_FAILURE"}
    monkeypatch.setattr(editorial, "prepare_page", prepare)
    editorial.run_due(store, {"status": {"plans": [later]}}, root=tmp_path / "pages", rollout={}, now=at, publish=False)
    assert seen[0] == first["source_plan"]


@pytest.mark.parametrize("fills_during_writing", [False, True])
@pytest.mark.parametrize("status_post_reply", [False, True])
def test_filled_gold_reaches_the_canonical_page_and_its_exact_telegram_parent(
        gold, tmp_path, main_root, monkeypatch, fills_during_writing, status_post_reply):
    from live_contentops import llm_operator_control_v1, native_desktop_publication_v1, native_neo_executor_v1

    raw, reasoning = gold
    reasoning["folder"] = tmp_path / "runs" / "requests" / "retained-gold"
    raw.update(status="WAITING", status_at_utc=raw["registered_at_utc"])
    registered = posts._utc(raw["registered_at_utc"])
    filled_at = registered + timedelta(minutes=1)
    now = filled_at + timedelta(minutes=2)
    folder = write(tmp_path / "export", [raw], [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])],
                   generated_at_utc=registered.isoformat())
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    posts.queue_posts(store, folder, now=registered, main_root=main_root)
    first, = rows(store)
    first["level_contract"] = reader.LEVEL_CONTRACT
    if not status_post_reply:
        first.pop("analysis_copy_contract", None)
    first.update(alerts.compose(first))
    store.finalize_outbox_payload_before_dispatch(
        message_id=first["key"], payload=json.dumps(first), status=posts.READY)
    frozen = store.get_outbox_message(first["key"])["payload"]
    store.create_work_item(story_id=first["key"], work_item_id=first["key"], title="Gold setup",
                           target_surface="MULTI_PLATFORM")
    confirm(store, first["key"], sha256(("plan-status-post:" + first["key"]).encode()).hexdigest(),
            "telegram", "901", "https://t.me/CapitalChronicle/901")
    waiting = {**raw, "last_quote": None, "last_price": 3959, "last_price_at_utc": registered.isoformat()}
    current = {**waiting, "status": "FILLED", "status_at_utc": filled_at.isoformat(),
               "last_price_at_utc": filled_at.isoformat(),
               "public_instrument": {**raw["public_instrument"], "invalidation_level": 4999}}
    canonical = "https://capitalchronicle.substack.com/p/gold-filled-replay"
    monkeypatch.setattr(pages, "load_run", lambda *args, **kwargs: reasoning)
    monkeypatch.setattr(pages, "_card", lambda *args: None)
    monkeypatch.setattr(pages, "datetime", SimpleNamespace(now=lambda tz: now))
    monkeypatch.setattr(posts, "current_public_plan", lambda *args, **options: current)
    monkeypatch.setattr(native_desktop_publication_v1, "live_publication_policy", lambda rollout: None)
    monkeypatch.setattr(llm_operator_control_v1, "assert_llm_operator_execution_enabled", lambda: None)

    def prepare(plan, *, output_dir, call, **options):
        assert plan == first["source_plan"]
        source = reader.source_packet(plan, reasoning, thread=True, level_contract=reader.LEVEL_CONTRACT)
        manuscript = editorial.bind_manuscript(authored(source), source, plan)
        return {"status": "PREPARED", "packet": pages.render(plan, manuscript, output_dir=output_dir, **options)}

    class Coordinator:
        def publish_plan(self, page_id, plan):
            assert self.recovery_scope["plan"] == plan
            packet = pages.validate_plan(store, page_id, plan)
            assert pages.require_current_page(packet, now=now) == current
            confirm(store, page_id, plan["plan_hash"], "substack", "replay", canonical)

    monkeypatch.setattr(editorial, "prepare_page", prepare)
    monkeypatch.setattr(native_neo_executor_v1, "bind_native_neo_coordinator",
                        lambda *args, **options: (Coordinator(), SimpleNamespace(pending=lambda: [])))
    export = {"status": {"plans": [waiting if fills_during_writing else current]}}
    result = editorial.run_due(store, export, root=tmp_path / "pages",
                               rollout={"store_path": store.db_path}, now=now)
    observed, = result["pages"]
    assert observed.get("publication", {}).get("canonical_url") == canonical, observed
    packet = editorial.publication_packet(store, raw)
    assert packet["source_plan"] == first["source_plan"]
    assert packet["active_status"] == {"status": "FILLED", "status_at_utc": filled_at.isoformat()}
    page = packet["native_payload"]
    assert "Status: in position (updated " + reader.et(filled_at.isoformat()) in page["body_markdown"]
    assert "waiting for entry" not in page["body_markdown"]
    prior = store.list_outbox_messages(destination="internal:plan-analysis-revision")
    if fills_during_writing:
        original, = prior
        assert "Status: waiting for entry" in json.loads(original["payload"])["native_payload"]["body_markdown"]
    else:
        assert prior == []
    reply = pages.register_link(store, packet, original_key=first["key"], destination="telegram")
    assert reply.get("status_post_reply", False) == status_post_reply
    assert reply["summary_version"] == 3
    assert reply["native_payload"]["reply_to_id"] == "901"
    assert reply["canonical_url"] == canonical
    reply_text = reply["native_payload"]["text"]
    assert canonical in reply_text
    assert pages.validate_link_plan(store, reply["link_id"], reply["plan"]) == reply
    assert "wrong above 4,004.4" in page["title"]
    for text in (first["text"], page["body_markdown"], reply_text):
        assert "Spot plan cancelled on close above 3,972.6 before entry" in text
        assert "MGC plan wrong above 4,004.4 after entry" in text
        assert "Entry can start until Fri 13 Nov, 1:00 AM ET." in text
        assert "Filled positions close by Fri 13 Nov, 8:15 AM ET." in text
        assert "4,999" not in text
        reader.check_thread_text(text)
    assert store.get_outbox_message(first["key"])["payload"] == frozen


def test_minute_page_slice_uses_later_quote_and_skips_the_stale_plan(gold, tmp_path, monkeypatch):
    raw, _ = gold
    raw["status"] = "WAITING"
    raw_at = posts._utc(raw["registered_at_utc"])
    at = raw_at + timedelta(minutes=3)
    quoted_at = (at - timedelta(seconds=30)).isoformat()
    quote = {"price": 3948.123, "instrument": raw["asset_id"], "quoted_at_utc": quoted_at,
             "known_at_utc": quoted_at, "source_hash": "a" * 64}
    current = {**raw, "last_quote": quote}
    stale = {**current, "plan_id": "older-quote", "last_quote": {**quote,
             "quoted_at_utc": (at - timedelta(hours=2)).isoformat()}}
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    seen = []

    def prepare(plan, **options):
        seen.append((plan["plan_id"], options["market_update"]))
        return {"status": "PAGE_TEXT_UNAVAILABLE", "cause": "CONTROLLED_WRITER_FAILURE"}

    monkeypatch.setattr(editorial, "prepare_page", prepare)
    result = editorial.run_due(store, {"status": {"plans": [stale, current]}},
                               root=tmp_path / "pages", rollout={}, now=at)
    assert seen == [(raw["plan_id"], quote)]
    assert result["waiting_for_current_quote"] == [
        {"plan_id": stale["plan_id"], "cause": "PLAN_ANALYSIS_QUOTE_STALE_REVIEW_REQUIRED"}]
    with store.get_read_only_connection() as conn:
        lease = conn.execute("SELECT acquired_at, expires_at FROM leases WHERE lease_key=?",
                             ("cc466-plan-page-editorial",)).fetchone()
    assert posts._utc(lease["expires_at"]) - posts._utc(lease["acquired_at"]) == timedelta(minutes=5)


def test_later_exported_result_reaches_the_frozen_thread(gold, tmp_path, main_root):
    raw, _ = gold
    raw.update(status="WAITING")
    raw.pop("outcome", None)
    now = posts._utc(raw["registered_at_utc"]) + timedelta(minutes=1)
    events = [event(raw["plan_id"], "WAITING", raw["registered_at_utc"])]
    folder = write(tmp_path / "export", [raw], events, generated_at_utc=now.isoformat())
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    posts.queue_posts(store, folder, now=now, main_root=main_root)
    first, = rows(store)
    store.set_outbox_status(first["key"], "PUBLISHED")
    frozen = store.get_outbox_message(first["key"])["payload"]
    later = deepcopy(raw)
    at = now + timedelta(minutes=1)
    later.update(status="CLOSED", outcome={"state": "SCORED", "result": "HIT", "outcome_id": "gold-result",
        "score": {"plan_id": raw["plan_id"], "asset_id": raw["asset_id"], "outcome_id": "gold-result",
                  "result": "HIT", "resolved_at_utc": at.isoformat(), "result_r": 1.2}})
    later["public_instrument"]["invalidation_level"] = 4999
    events += [event(raw["plan_id"], "FILLED", now.isoformat()), event(raw["plan_id"], "CLOSED", at.isoformat())]
    write(folder, [later], events, generated_at_utc=at.isoformat())
    posts.queue_posts(store, folder, now=at, main_root=main_root)
    ending = next(row for row in rows(store) if row["kind"] == "result")
    assert "Result: +1.2R." in ending["text"]
    assert "4,004.4" in ending["text"] and "4,999" not in ending["text"]
    assert ending["source_plan"] == first["source_plan"]
    assert store.get_outbox_message(first["key"])["payload"] == frozen
    alerts.validate(ending)
    altered = deepcopy(ending)
    altered["outcome_source_plan"]["outcome"]["score"]["result_r"] = 9
    with pytest.raises(ValueError, match="PLAN_ALERT_OUTCOME_SOURCE_BYTES_CHANGED"):
        alerts.validate(altered)
