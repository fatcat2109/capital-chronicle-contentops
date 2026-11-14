"""Current public state, named pricing sources and distinct pre/post-entry levels."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from live_contentops import plan_analysis_pages_v1 as pages, plan_reader_copy_v1 as reader
from live_contentops import plan_status_posts_v1 as posts
from test_plan_analysis_pages_cc432 import source  # noqa: F401

GOLD = Path(__file__).parents[1] / "docs/publisher/CC-549/fixtures/gold-plan-thread-181.json"


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
    raw = json.loads(GOLD.read_bytes())
    terms = reader.thread_terms(raw, level_contract="CC584_V1")
    assert "cancelled" in terms["invalidation"] and "before entry" in terms["invalidation"]
    assert "3,972.6" in terms["invalidation"]
    assert "wrong" in terms["invalidation"] and "after entry" in terms["invalidation"]
    assert "4,004.4" in terms["invalidation"]
    assert "Spot" in terms["invalidation"] and "MGC" in terms["invalidation"]


def test_stored_91_percent_paragraph_needs_a_named_pricing_source():
    stored = json.loads((Path(__file__).parent / "fixtures/cc584/stored-plan-rows.json").read_bytes())
    run = {"source_plan": {"scenario_analysis": {"priced": stored["eurusd_priced_source"]},
           "registered_at_utc": "2026-11-11T16:20:07.062029Z"}, "documents": {}}
    manuscript = {"sections": {"priced_in": stored["eurusd_priced_in"]}}
    with pytest.raises(ValueError, match="PRICED_PERCENTAGE_SOURCE"):
        pages.check_new_page_copy(manuscript, run)


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
    from test_plan_thread_consistency_cc549 import alert_row, authored
    from test_tradingview_plan_overlay_cc459 import captured

    raw = json.loads(GOLD.read_bytes())
    run = json.loads((GOLD.parent / "gold-public-reasoning.json").read_bytes())
    run["source_plan"] = raw
    source = reader.source_packet(raw, run, thread=True, original_probabilities=True, level_contract=reader.LEVEL_CONTRACT)
    manuscript = editorial.bind_manuscript(authored(source), source, raw)
    pages.validate_manuscript(raw, manuscript, run)
    payload, _, _ = pages._assemble(raw, manuscript, run)
    row = {**alert_row(raw), "key": "gold-phase-labels", "level_contract": reader.LEVEL_CONTRACT}
    alert = alerts.compose(row)["text"]
    _, asset = captured("XAUUSD")
    plain = tv.snapshot_asset("XAUUSD", "Bound gold conditions", asset["tradingview_snapshot"], tmp_path)
    marked = overlay.apply(plain, row)
    overlay.validate(marked, row)
    terms = reader.thread_terms(raw, level_contract=reader.LEVEL_CONTRACT)["invalidation"]
    assert terms in alert and terms in payload["body_markdown"] and terms in payload["title"]
    assert marked["plan_overlay"]["source"]["phase_terms"] == terms
    assert marked["plan_overlay"]["source"]["phase_source_sha256"] == posts._sha(raw)
    assert not marked["plan_overlay"]["markers"]  # MGC's stop is never plotted on a spot-price axis.
    changed = deepcopy(row)
    changed["source_plan"]["invalidation_conditions"][0]["threshold"] = 3999
    with pytest.raises(ValueError, match="SOURCE_OR_SCALE_CHANGED"):
        overlay.validate(marked, changed)
