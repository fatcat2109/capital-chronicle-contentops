"""Current public state, named pricing sources and distinct pre/post-entry levels."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from live_contentops import plan_analysis_pages_v1 as pages, plan_reader_copy_v1 as reader
from live_contentops import plan_status_posts_v1 as posts
from test_plan_analysis_pages_cc432 import source  # noqa: F401

GOLD = Path(__file__).parents[1] / "docs/publisher/CC-549/fixtures/gold-plan-thread-181.json"


@pytest.fixture
def gold_18_nov():
    # Public Main export for the plan behind the page published on 19 November.
    return {
        "asset_id": "XAUUSD", "direction": "BEARISH",
        "plan_id": "plan_64c0b961e6d621d10de5e9d3",
        "registration_hash": "353955a42d4e3dd7eb8652123554696676f225022c1be512219fc5bbcaf161e3",
        "zone": {"minimum": 3773, "maximum": 3790},
        "invalidation_conditions": [{"field": "high", "operator": "GTE", "threshold": 3833.5}],
        "registered_at_utc": "2026-11-18T07:39:10.617567Z", "entry_deadline_utc": "2026-11-18T10:00:00Z",
        "expires_at_utc": "2026-11-18T10:45:00Z",
        "public_instrument": {"kind": "FUT", "symbol": "MGC", "name": "Micro gold", "direction": "BEARISH",
                              "zone_low": 3772.302882583667, "zone_high": 3789.302882583667,
                              "invalidation_level": 3832.9, "tick_size": 0.1},
    }


def test_november_gold_title_states_the_view_and_uses_the_exported_stop(gold_18_nov):
    terms = reader.thread_terms(gold_18_nov, level_contract=reader.LEVEL_CONTRACT)
    assert terms["title"] == "Gold: bearish at 3,772.3–3,789.3, wrong above 3,832.9"
    assert "3,833.5 before entry" in terms["invalidation"]


def test_title_uses_the_sealed_original_stop_when_mapped_levels_are_incomplete(gold_18_nov):
    raw = {**gold_18_nov, "public_instrument": {"symbol": "MGC"}}
    candidate = {"candidate_id": "cand_macro_gold", "direction": "SHORT",
                 "entry_bounds": raw["zone"], "stop_loss": 3836}
    run = {"documents": {"analysis-native.json": {"native_synthesis": {"candidates": [candidate]}}}}
    terms = reader.page_thread_terms(raw, run, level_contract=reader.LEVEL_CONTRACT)
    assert terms["title"] == "Gold: bearish at 3,773–3,790, wrong above 3,836"
    assert "3,833.5 before entry" in terms["invalidation"]
    assert pages._source_text(run, next(ref for ref in terms["refs"] if ref["pointer"].endswith("/stop_loss"))) == "3836"


def test_november_gold_page_rendered_after_expiry_uses_the_final_status(gold_18_nov, tmp_path, monkeypatch):
    from live_contentops import native_neo_executor_v1 as native, plan_reader_editorial_v1 as editorial
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    from live_contentops.plan_substack_neo_v1 import EXPIRED_CODE_DRAFT_CLOSED
    from live_contentops.publication_coordinator_v1 import (
        CanonicalDestinationTransportRuntimeV1, DurablePublicationCoordinator,
    )
    from test_plan_thread_consistency_cc549 import authored

    raw = {**gold_18_nov, "status": "WAITING", "run_id": "retained-gold", "analysis_result_hash": "retained"}
    current = {**raw, "status": "CLOSED", "status_at_utc": "2026-11-18T18:30:21.138000Z"}
    now = posts._utc("2026-11-19T11:40:00Z")
    run = json.loads((GOLD.parent / "gold-public-reasoning.json").read_bytes())
    run["source_plan"] = raw
    monkeypatch.setattr(pages, "load_run", lambda *a, **k: run)
    monkeypatch.setattr(pages, "_card", lambda *a: None)
    monkeypatch.setattr(posts, "current_public_plan", lambda *a, **k: current)
    source = reader.source_packet(raw, run, thread=True, level_contract=reader.LEVEL_CONTRACT)
    manuscript = editorial.bind_manuscript(authored(source), source, raw)
    manuscript["title"] = "Gold: Spot plan cancelled on high"

    with pytest.raises(ValueError, match="ENTRY_WINDOW_ENDED_REVIEW_REQUIRED"):
        pages.require_current_page({"source_plan": raw}, now=now)
    final = pages.ended_plan_status(raw, current, now=now)
    packet = pages.render(raw, manuscript, output_dir=tmp_path / "page", final_status=final)
    body = packet["native_payload"]["body_markdown"]
    assert "This page was published after the plan ended. The entry window closed Wed 18 Nov, 5:00 AM ET." in body
    assert "Status: closed (updated Wed 18 Nov, 1:30 PM ET)." in body
    assert "waiting for entry" not in body
    assert packet["native_payload"]["title"] == "Gold: bearish at 3,772.3–3,789.3, wrong above 3,832.9"
    assert pages.require_current_page(packet, now=now) == current
    assert "This page was published after the plan ended." in (tmp_path / "page/article.html").read_text(encoding="utf-8")

    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    held = pages.register_page(store, pages.render(raw, manuscript, output_dir=tmp_path / "held"))
    old_bytes = store.get_outbox_message(held["page_id"])["payload"]
    seen = []

    class Executor:
        native_invocation_id = "expiry-test"

        def pending(self):
            return []

        def __call__(self, request):
            seen.append(request)
            screen = request["pending_owner_screen"]
            assert request["action"] == "READBACK"
            assert screen["cancel_on_or_after_utc"] == raw["entry_deadline_utc"]
            return {"status": EXPIRED_CODE_DRAFT_CLOSED, "cancelled_owner_screen": screen,
                    "observed_identity": request["expected_identity"], "request_sha256": request["request_sha256"]}

    executor = Executor()
    transport = CanonicalDestinationTransportRuntimeV1(
        linkedin_transport=object(), neo_transport=NeoDestinationHandoff(native_executor=executor))
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=transport, clock=lambda: now)
    coordinator.register_plan(held["page_id"], held["plan"])
    old_intent, = store.list_outbox_messages(destination="substack")
    ids = coordinator._ids(held["page_id"], held["plan"]["plan_hash"], "substack")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"], platform="substack",
        status="SUBSTACK_DRAFT_AWAITING_OWNER", public_object_id="123")
    screen = {"draft_id": "123", "page_id": "15", "page_url": "https://capitalchronicle.substack.com/publish/post/123",
              "status": "PENDING_JIM_EMAIL_CODE"}
    screen_id = "substack-owner-screen-" + ids["dispatch_id"]
    store.register_outbox_message(message_id=screen_id, work_item_id=held["page_id"], destination="internal:substack-owner-screen",
        payload=json.dumps(screen), status="SUBSTACK_DRAFT_AWAITING_OWNER")
    with pytest.raises(ValueError, match="COPY_REVISION_READBACK_REQUIRED"):
        pages.refresh_ended_page(store, held, now=now)
    monkeypatch.setattr(native, "bind_native_neo_coordinator", lambda *a, **k: (coordinator, executor))

    def unavailable_export():
        assert len(seen) == 1  # The readback runs before the potentially slow Main reader.
        raise OSError("controlled Main export outage")

    rollout = {"store_path": store.db_path, "public_write_authority": False}
    outcome = editorial.run_due(store, unavailable_export, root=tmp_path / "minute", rollout=rollout, now=now)
    assert outcome["pages"][0]["publication"]["publication"]["reconciliation_status"] == EXPIRED_CODE_DRAFT_CLOSED
    assert "controlled Main export outage" in outcome["source_cause"]
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == "DEFINITE_NO_WRITE"
    assert json.loads(store.get_outbox_message(screen_id)["payload"]) == screen
    assert not editorial.run_due(store, unavailable_export, root=tmp_path / "minute", rollout=rollout, now=now)["pages"]
    assert len(seen) == 1

    refreshed = pages.refresh_ended_page(store, held, now=now)
    coordinator.register_plan(refreshed["page_id"], refreshed["plan"])
    native = [json.loads(row["payload"])["native_payload"] for row in store.list_outbox_messages(destination="substack")]
    assert held["plan"]["plan_hash"] != refreshed["plan"]["plan_hash"]
    assert native == [held["native_payload"], packet["native_payload"]]
    prior, = store.list_outbox_messages(destination="internal:plan-analysis-revision")
    assert prior["payload"] == old_bytes
    assert store.get_outbox_message(old_intent["message_id"])["payload"] == old_intent["payload"]


@pytest.mark.parametrize("change", [
    {"status": "WAITING"}, {"status": "FILLED"}, {"status_at_utc": None},
    {"registration_hash": "different"}, {"status_at_utc": "2026-11-19T12:30:00Z"},
])
def test_after_entry_window_only_the_current_exact_terminal_state_can_be_rendered(gold_18_nov, change):
    current = {**gold_18_nov, "status": "CLOSED", "status_at_utc": "2026-11-18T18:30:21.138000Z", **change}
    with pytest.raises(ValueError, match="FINAL_STATUS_REQUIRED_AFTER_ENTRY_WINDOW"):
        pages.ended_plan_status(gold_18_nov, current, now=posts._utc("2026-11-19T11:40:00Z"))


@pytest.mark.parametrize("change,cause", [
    ({"status": "EXPIRED"}, "STATE_CHANGED"),
    ({"last_price": 3875}, "MOVED_PAST"),
    ({"last_price_at_utc": "2026-11-12T12:00:00Z"}, "QUOTE_STALE"),
])
def test_final_page_write_reads_existing_public_state_again(tmp_path, monkeypatch, change, cause):
    raw = json.loads(GOLD.read_bytes())
    raw.update(status="WAITING", last_price=3959, last_quote=None, last_price_at_utc="2026-11-12T16:31:30Z")
    current = {**raw, **change}
    folder = tmp_path / "export"
    folder.mkdir()
    (folder / "plan-status.public.json").write_text(json.dumps({
        "generated_at_utc": "2026-11-12T16:32:00Z", "plans": [current]}), encoding="utf-8")
    monkeypatch.setattr(posts, "EXPORT_DIR", folder)
    monkeypatch.setattr(posts, "read_export", lambda export_dir: {
        "status": json.loads((export_dir / "plan-status.public.json").read_bytes())})
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return posts._utc("2026-11-12T16:32:05Z")
    monkeypatch.setattr(pages, "datetime", Clock)
    packet = {"source_plan": raw, "plan": {"plan_hash": "hash"}, "media_assets": [],
              "native_payload": {"body_markdown": "Our conditional view."}, "manuscript": {}}
    monkeypatch.setattr(pages, "validate_plan", lambda *a: packet)
    class Store:
        def get_outbox_message(self, key):
            return {"payload": json.dumps(packet)}
    intent = {"work_item_id": "page", "native_payload": packet["native_payload"], "plan_hash": "hash",
              "destination_plan": {"substack_delivery_mode": "WEB_ONLY"}}
    with pytest.raises(ValueError, match=cause):
        pages.validate_intent(Store(), intent)


@pytest.mark.parametrize("text,cause", [
    ("Markets price a 55% chance of a rate increase.", "PRICED_PERCENTAGE_SOURCE"),
    ("Polymarket prices a 55% chance of a rate increase.", "PREDICTION_MARKET"),
    ("The supplied historical review gives a 55% chance.", "PIPELINE_WORDING"),
    ("The analyst's comparison gives a 55% chance.", "PIPELINE_WORDING"),
])
def test_new_page_render_refuses_the_observed_copy_defects(source, tmp_path, text, cause):
    root, _, plan, manuscript = source
    paragraph = manuscript["sections"]["priced_in"]["paragraphs"][0]
    paragraph["text"] = text
    manuscript["sections"]["priced_in"]["summary"] = text
    with pytest.raises(ValueError, match=cause):
        pages.render(plan, manuscript, run_root=root, output_dir=tmp_path / "page")


def test_new_gold_thread_explicitly_distinguishes_cancel_and_after_entry_stop():
    from live_contentops import plan_state_alerts_v1 as alerts
    from test_plan_thread_consistency_cc549 import alert_row
    raw = json.loads(GOLD.read_bytes())
    text = alerts.compose({**alert_row(raw), "level_contract": "CC584_V1"})["text"]
    assert "cancelled" in text and "before entry" in text
    assert "3,972.6" in text
    assert "wrong" in text and "after entry" in text
    assert "4,004.4" in text
    assert "Spot" in text and "MGC" in text


@pytest.mark.parametrize("state", ["WAITING", "TRIGGERED", "FILLED"])
def test_new_alert_waits_for_the_owners_entry_state_before_claiming_a_fill(state):
    from live_contentops import plan_state_alerts_v1 as alerts
    from test_plan_thread_consistency_cc549 import alert_row

    raw = json.loads(GOLD.read_bytes())
    row = {**alert_row(raw), "state": state, "level_contract": reader.LEVEL_CONTRACT}
    text = alerts.compose(row)["text"]
    if state == "WAITING":
        assert "armed, waiting for price to trade at 3,954.4" in text
        assert "entry filled" not in text and "position is open" not in text
    else:
        assert "armed, waiting" not in text
        assert "An entry filled; the position is open." in text


def test_current_matching_plan_and_quote_are_used_for_a_fresh_page(monkeypatch):
    raw = json.loads(GOLD.read_bytes())
    raw.update(status="WAITING")
    current = {**raw, "last_price": 3959, "last_quote": None, "last_price_at_utc": "2026-11-12T16:31:30Z"}
    calls = []
    def observe(plan_id, **options):
        calls.append((plan_id, options))
        return current
    monkeypatch.setattr(posts, "current_public_plan", observe)
    now = posts._utc("2026-11-12T16:32:05Z")
    assert pages.require_current_page({"source_plan": raw}, now=now) is current
    assert calls == [(raw["plan_id"], {"registration_hash": raw["registration_hash"], "now": now})]


def test_dated_page_update_uses_main_quote_and_rechecks_state_before_write(monkeypatch):
    from test_plan_thread_consistency_cc549 import authored
    from live_contentops import plan_reader_editorial_v1 as editorial

    raw = json.loads(GOLD.read_bytes())
    raw.update(status="WAITING")
    at = posts._utc(raw["registered_at_utc"]) + timedelta(minutes=3)
    quote_at = (at - timedelta(seconds=30)).isoformat()
    quote = {"price": 3948.123, "instrument": raw["asset_id"], "quoted_at_utc": quote_at,
             "known_at_utc": quote_at, "source_hash": "a" * 64}
    current = {**raw, "last_quote": quote}
    monkeypatch.setattr(posts, "current_public_plan", lambda *a, **k: current)
    update = pages.market_update(raw, current, now=at)
    assert update == quote
    run = json.loads((GOLD.parent / "gold-public-reasoning.json").read_bytes())
    run["source_plan"] = raw
    source = reader.source_packet(raw, run, thread=True, level_contract=reader.LEVEL_CONTRACT)
    manuscript = editorial.bind_manuscript(authored(source), source, raw)
    packet, _, _ = pages._assemble(raw, manuscript, run, market_update=update)
    body = packet["body_markdown"]
    assert "Since we fixed the plan, Gold was below the original entry zone." in body
    assert "Our quote at " + reader.et(quote_at) + " was 3,948.123." in body
    assert body.index("Our quote at") < body.index("## What is priced in")
    assert pages.require_current_page({"source_plan": raw, "market_update": update}, now=at) == current

    with pytest.raises(ValueError, match="DATED_UPDATE_NO_LONGER_CURRENT"):
        pages.require_current_page({"source_plan": raw, "market_update": {**update, "price": 3900}}, now=at)
    current["last_quote"] = {**quote, "quoted_at_utc": at.isoformat(), "known_at_utc": at.isoformat(),
                            "price": 3959, "source_hash": "b" * 64}
    with pytest.raises(ValueError, match="DATED_UPDATE_NO_LONGER_CURRENT"):
        pages.require_current_page({"source_plan": raw, "market_update": update}, now=at)
    current["status"] = "EXPIRED"
    with pytest.raises(ValueError, match="STATE_CHANGED"):
        pages.require_current_page({"source_plan": raw, "market_update": update}, now=at)


@pytest.mark.parametrize("old_price,current_price", [(3959, 3948.123), (3948.123, 3959), (3959, 3959.5)])
def test_same_state_quote_crossing_reaches_the_first_canonical_send(old_price, current_price, tmp_path, monkeypatch):
    from types import SimpleNamespace

    from live_contentops import llm_operator_control_v1, native_desktop_publication_v1, native_neo_executor_v1
    from live_contentops import plan_reader_editorial_v1 as editorial
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from test_plan_thread_consistency_cc549 import authored

    raw = json.loads(GOLD.read_bytes())
    raw["status"] = "WAITING"
    prepared_at = posts._utc(raw["registered_at_utc"]) + timedelta(minutes=3)
    now = prepared_at + timedelta(minutes=1)

    def with_quote(price, at, source_hash):
        return {**raw, "last_quote": {"price": price, "instrument": raw["asset_id"],
            "quoted_at_utc": at.isoformat(), "known_at_utc": at.isoformat(), "source_hash": source_hash}}

    previous = with_quote(old_price, prepared_at, "a" * 64)
    current = with_quote(current_price, now, "b" * 64)
    run = json.loads((GOLD.parent / "gold-public-reasoning.json").read_bytes())
    run["source_plan"] = raw
    source = reader.source_packet(raw, run, thread=True)
    manuscript = editorial.bind_manuscript(authored(source), source, raw)
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    monkeypatch.setattr(pages, "load_run", lambda *a, **k: run)
    monkeypatch.setattr(pages, "_card", lambda *a: None)
    monkeypatch.setattr(pages, "datetime", SimpleNamespace(now=lambda tz: now))
    monkeypatch.setattr(posts, "current_public_plan", lambda *a, **k: current)
    monkeypatch.setattr(native_desktop_publication_v1, "live_publication_policy", lambda rollout: None)
    monkeypatch.setattr(llm_operator_control_v1, "assert_llm_operator_execution_enabled", lambda: None)

    held = pages.register_page(store, pages.render(raw, manuscript, output_dir=tmp_path / "page",
        **pages.current_page_options(raw, previous, now=prepared_at)))
    held_bytes = store.get_outbox_message(held["page_id"])["payload"]
    sent = []

    class Coordinator:
        def publish_plan(self, page_id, plan):
            assert self.recovery_scope["plan"] == plan
            packet = pages.validate_plan(store, page_id, plan)
            assert pages.require_current_page(packet, now=now) == current
            sent.append(packet)
            return {"status": "DISPATCH_CONFIRMED"}

    monkeypatch.setattr(native_neo_executor_v1, "bind_native_neo_coordinator",
                        lambda *a, **k: (Coordinator(), SimpleNamespace(pending=lambda: [])))
    outcome = pages.continue_page(store, held, invocation_id="same-state-quote-test",
                                  rollout={"store_path": store.db_path})
    assert outcome["publication"]["status"] == "DISPATCH_CONFIRMED"
    packet, = sent
    assert packet["source_plan"] == held["source_plan"]
    assert packet["native_payload"]["title"] == held["native_payload"]["title"]
    body = packet["native_payload"]["body_markdown"]
    revisions = store.list_outbox_messages(destination="internal:plan-analysis-revision")
    if current_price == 3948.123:
        assert packet["market_update"] == current["last_quote"]
        assert "Our quote at " + reader.et(now.isoformat()) + " was 3,948.123." in body
    else:
        assert not packet.get("market_update")
        assert "Since we fixed the plan" not in body
    if current_price == 3959.5:
        assert packet == held
        assert revisions == []
    else:
        original, = revisions
        assert original["payload"] == held_bytes


def test_stored_91_percent_paragraph_needs_a_named_pricing_source():
    stored = json.loads((Path(__file__).parent / "fixtures/cc584/stored-plan-rows.json").read_bytes())
    run = {"source_plan": {"scenario_analysis": {"priced": stored["eurusd_priced_source"]},
           "registered_at_utc": "2026-11-11T16:20:07.062029Z"}, "documents": {}}
    manuscript = {"sections": {"priced_in": stored["eurusd_priced_in"]}}
    with pytest.raises(ValueError, match="PRICED_PERCENTAGE_SOURCE"):
        pages.check_new_page_copy(manuscript, run)


@pytest.mark.parametrize("percentage", ["55%", "55 percent", "55 per cent"])
def test_pricing_source_cannot_be_invented_in_writer_metadata(source, percentage):
    root, _, plan, manuscript = source
    section = manuscript["sections"]["priced_in"]
    paragraph = section["paragraphs"][0]
    paragraph.update(text=f"CME FedWatch prices a {percentage} chance of a rate increase.",
                     source_name="CME FedWatch", source_locator="CME FedWatch")
    section["summary"] = paragraph["text"]
    with pytest.raises(ValueError, match="PRICED_PERCENTAGE_SOURCE"):
        pages.check_new_page_copy(manuscript, pages.load_run(plan, run_root=root))


@pytest.mark.parametrize("text,cause", [
    ("The analyst's comparison supports gold.", "PIPELINE_WORDING"),
    ("Markets price a 55 percent chance.", "PRICED_PERCENTAGE_SOURCE"),
    ("Polymarket prices a 55% chance.", "PREDICTION_MARKET"),
])
def test_new_social_variants_share_page_claim_checks(text, cause):
    source = {"level_contract": reader.LEVEL_CONTRACT,
              "sources": [{"id": "s0", "text": "Our view has a 55% chance.", "layer": "priced_in"}]}
    with pytest.raises(ValueError, match=cause):
        reader.validate_fields({"hook": {"text": text, "source_ids": ["s0"]}}, source)


def test_named_futures_pricing_is_usable_when_its_attribution_is_bound(source, tmp_path):
    root, folder, plan, manuscript = source
    document = json.loads((folder / "options-context.json").read_bytes())
    document["pricing"] = "CME FedWatch prices a 55% chance of a rate increase."
    (folder / "options-context.json").write_text(json.dumps(document), encoding="utf-8")
    section = manuscript["sections"]["priced_in"]
    section["paragraphs"] = [{"text": document["pricing"], "refs": [{"file": "options-context.json", "pointer": "/pricing"}],
        "rights": "SINGLE_ATTRIBUTED_FACT", "source_name": "CME FedWatch"}]
    section["summary"] = document["pricing"]
    packet = pages.render(plan, manuscript, run_root=root, output_dir=tmp_path / "page")
    assert document["pricing"] in packet["native_payload"]["body_markdown"]


def test_new_page_alert_and_chart_use_the_same_bound_phase_labels(tmp_path, monkeypatch):
    from live_contentops import plan_call_cards_v1 as cards, plan_state_alerts_v1 as alerts
    from live_contentops import plan_reader_editorial_v1 as editorial, tradingview_plan_overlay_v1 as overlay
    from live_contentops import tradingview_snapshot_v1 as tv
    from live_contentops import publication_image_contract_v1 as image
    from test_plan_thread_consistency_cc549 import alert_row, authored
    from test_tradingview_plan_overlay_cc459 import captured

    raw = json.loads(GOLD.read_bytes())
    run = json.loads((GOLD.parent / "gold-public-reasoning.json").read_bytes())
    run["source_plan"] = raw
    source = reader.source_packet(raw, run, thread=True, original_probabilities=True, level_contract=reader.LEVEL_CONTRACT)
    manuscript = editorial.bind_manuscript(authored(source), source, raw)
    pages.validate_manuscript(raw, manuscript, run)
    payload, _, _ = pages._assemble(raw, manuscript, run)
    row = {**alert_row(raw), "key": "gold-phase-labels", "level_contract": reader.LEVEL_CONTRACT,
           "schema_version": posts.SCHEMA, "format": 4}
    alert = alerts.compose(row)["text"]
    _, asset = captured("XAUUSD")
    snap = asset["tradingview_snapshot"]
    snap = image.bind_scale("XAUUSD", snap, quote={"market": "XAUUSD", "instrument": "XAUUSD", "price": 4047.473,
        "quoted_at_utc": snap["captured_at_utc"], "known_at_utc": snap["captured_at_utc"],
        "source_path": "controlled-gold-price.json", "source_sha256": "a" * 64, "price_basis": "plan_feed"})
    plain = tv.snapshot_asset("XAUUSD", "Bound gold conditions", snap, tmp_path)
    marked = overlay.apply(plain, row)
    overlay.validate(marked, row)
    terms = reader.thread_terms(raw, level_contract=reader.LEVEL_CONTRACT)["invalidation"]
    assert terms in alert and terms in payload["body_markdown"]
    assert payload["title"] == "Gold: bearish at 3,954.4, wrong above 4,004.4"
    assert marked["plan_overlay"]["source"]["phase_terms"] == terms
    assert marked["plan_overlay"]["source"]["phase_source_sha256"] == posts._sha(raw)
    assert not marked["plan_overlay"]["markers"]  # MGC's stop is never plotted on a spot-price axis.
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    store.create_work_item(story_id=posts.WORK_ITEM_ID, work_item_id=posts.WORK_ITEM_ID,
                          title="Source-bound gold chart", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(message_id=row["key"], work_item_id=posts.WORK_ITEM_ID,
        destination=posts.DESTINATION, payload=json.dumps(row), status=posts.READY)
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None,
        clock=lambda: posts._utc("2026-11-14T06:00:00Z"))
    intent = {"plan_status_post": row["key"], "media_assets": [marked]}
    assert image.validate_write(coordinator, intent, "telegram")["first_image_type"] == "TRADINGVIEW_MARKET_CHART"
    with pytest.raises(ValueError, match="PRICE_BASIS_MISMATCH"):
        image.validate_write(coordinator, {**intent, "media_assets": [plain]}, "telegram")
    changed = deepcopy(row)
    changed["source_plan"]["invalidation_conditions"][0]["threshold"] = 3999
    with pytest.raises(ValueError, match="SOURCE_OR_SCALE_CHANGED"):
        overlay.validate(marked, changed)


def test_new_phase_labels_reach_x_without_an_impossible_writer_length_gate():
    raw = json.loads(GOLD.read_bytes())
    run = json.loads((GOLD.parent / "gold-public-reasoning.json").read_bytes())
    run["source_plan"] = raw
    source = reader.source_packet(raw, run, thread=True, original_probabilities=True, level_contract=reader.LEVEL_CONTRACT)
    rationale = next(s for s in source["sources"] if s["ref"]["pointer"].endswith("/rationale"))
    text = "Inflation repricing weighs on gold."
    source["sources"].append({"id": "controlled-force", "layer": "macro", "text": text})
    fields = {"hook": {"text": text, "source_ids": ["controlled-force"]},
              "points": [{"layer": "macro", "text": text, "source_ids": ["controlled-force"]}],
              "scenario_main": {"text": "Main (55%): repricing weighs on gold.", "source_ids": [rationale["id"]]}}
    if source["scenario_analysis"].get("main_alternative", {}).get("probability_pct") is not None:
        alternative = source["scenario_analysis"]["main_alternative"]["probability_pct"]
        source["sources"].append({"id": "controlled-alt", "text": f"Alternative ({alternative}%): gold rebounds.", "layer": "scenarios"})
        fields["scenario_alt"] = {"text": f"Alternative ({alternative}%): gold rebounds.", "source_ids": ["controlled-alt"]}
    row = {"kind": "setup", "thread_contract": reader.THREAD_CONTRACT, "level_contract": reader.LEVEL_CONTRACT,
           "source_plan": raw, "reader_fields": fields, "reader_source": source,
           "analysis_publication": {"canonical_url": "https://capitalchronicle.substack.com/p/gold-plan"}}
    row.update(reader.attach_call(row))
    payload = reader.payloads(row, "chart", chart_credit=True)["x"]
    assert all(posts._x_length(part["text"]) <= 280 for part in payload["posts"])
    assert payload["posts"][0]["media_asset_ids"] == ["chart"]
    assert "https://capitalchronicle.substack.com/p/gold-plan" in payload["posts"][1]["text"]
    assert payload["posts"][2]["text"].startswith("Macro: " + text)
    text = payload["full_text"]
    assert reader.thread_terms(raw, level_contract=reader.LEVEL_CONTRACT)["invalidation"] + "." in text
    for clock in reader.thread_terms(raw, level_contract=reader.LEVEL_CONTRACT)["clocks"]:
        assert clock in text
