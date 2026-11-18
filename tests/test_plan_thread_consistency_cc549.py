"""The gold thread's retained inputs flow into one new, source-bound thread."""
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_reader_editorial_v1 as editorial
from live_contentops import plan_state_alerts_v1 as alerts
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_plan_status_posts_cc306 import event, main_root  # noqa: F401
from test_plan_call_cards_cc399 import write, rows
from test_plan_analysis_pages_cc432 import source  # noqa: F401


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


def test_long_plan_preview_renders_the_same_terms_as_the_chart_thread(gold, tmp_path, main_root):
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
    key = queued["key"]
    frozen = store.get_outbox_message(key)["payload"]

    result = posts.queue_posts(store, folder, now=now, main_root=main_root, dry_run=True, render_all=True)
    assert result["status"] == "OK"
    preview, = result["rendered_posts"]
    chart_thread = cards.destination_payloads(
        queued, card_id="dry-run-" + key, chart_credit=True, complete_levels=True,
    )["threads"]
    assert preview["destinations"]["threads"] == chart_thread
    assert all(len(text) <= 500 for text in [chart_thread["root_text"], *chart_thread["reply_texts"]])
    for phrase in ("63,885–65,160", "at or above 66,450 before entry", "above 66,415 after entry",
                   "Entry can start until Tue 17 Nov, 2:30 PM ET.", "Filled positions close by Wed 18 Nov, 1:30 PM ET."):
        assert phrase in chart_thread["full_text"]
    assert store.get_outbox_message(key)["payload"] == frozen


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
