"""Daily Notes reach the real coordinator once; sources and media stay exact."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import substack_daily_note_v1 as notes
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
from test_plan_analysis_pages_cc432 import source  # noqa: F401
from test_plan_analysis_distribution_cc435 import confirm
from test_tradingview_snapshot_cc314 import FIXTURE


@pytest.fixture
def ready(source, tmp_path):
    root, folder, plan, manuscript = source
    now = datetime.now(timezone.utc)
    date = now.astimezone(notes.ET).strftime("%d %b").lstrip("0")
    fact = f"US yields reached 5% on {date}; higher rates weigh on the euro."
    view = "We are bearish only below 1.12."
    end = "Above 1.12 we are wrong."
    rationale = fact + " " + view + " " + end
    result = {"native_synthesis": {"candidates": [{"rationale": rationale}]}}
    for name in ("owner-native.json", "desktop-manual-result.json"):
        (folder / name).write_bytes(canonical_bytes(result))
    plan["analysis_result_hash"] = sha256_of(result)
    freeze = json.loads((folder / "final-decision-freeze.json").read_bytes())
    freeze.update(qualitative_result_hash=sha256_of(result), frozen_at_utc=now.isoformat())
    (folder / "final-decision-freeze.json").write_bytes(canonical_bytes(freeze))
    capture = canonical_bytes({"known_at_utc": (now - timedelta(minutes=2)).isoformat()})
    (folder / "capture.json").write_bytes(capture)
    (folder / "role-pack.json").write_bytes(canonical_bytes({"sources": {
        "capture.json": {"sha256": sha256(capture).hexdigest(), "bytes": len(capture)}}}))
    for section in manuscript["sections"].values():
        section["paragraphs"][0]["text"] = rationale
        section["summary"] = view
    packet = pages.render(plan, manuscript, run_root=root, output_dir=tmp_path / "page")
    snap = {"path": str(FIXTURE), "sha256": sha256(FIXTURE.read_bytes()).hexdigest(),
            "tv_symbol": tv.SYMBOLS["EURUSD"], "interval": "240", "interval_label": "4h",
            "chart_url": tv.chart_url(tv.SYMBOLS["EURUSD"], "240"), "captured_at_utc": now.isoformat()}
    packet["media_assets"] = [tv.snapshot_asset("EURUSD", "Euro", snap, tmp_path / "chart")]
    store = ContentOpsDurableStore(tmp_path / "notes.sqlite3")
    page = pages.register_page(store, packet)
    confirm(store, page["page_id"], page["plan"]["plan_hash"], "substack", "123",
            "https://capitalchronicle.substack.com/p/original-analysis")
    authored = {"page_id": page["page_id"], "sentences": [
        {"text": fact, "section": "macro", "source_excerpt": fact, "fact_date": date},
        {"text": view, "section": "scenarios", "source_excerpt": view},
        {"text": end, "section": "technical", "source_excerpt": end}], "view": view, "invalidation": end}
    return store, page, authored, now


def test_daily_note_reaches_real_coordinator_and_native_image_binding_once(ready, tmp_path):
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    store, page, authored, now = ready
    value = notes.register_note(store, page, authored, now=now, output_root=tmp_path / "notes")
    again = notes.register_note(store, page, {"invalid": "new copy"}, now=now, output_root=tmp_path / "notes")
    assert again == value
    coordinator = Coordinator(store=store, transport_runtime=None, published_content_path=tmp_path / "published.jsonl")
    coordinator.register_plan(value["link_id"], value["plan"])
    coordinator.register_plan(value["link_id"], value["plan"])
    messages = store.list_outbox_messages(work_item_id=value["link_id"], destination="substack_notes")
    assert len(messages) == 1
    intent = json.loads(messages[0]["payload"])
    assert intent["native_payload"] == value["native_payload"]
    assert intent["media_assets"] == value["media_assets"]
    assert "published_content_export" not in intent
    pages.validate_link_intent(store, intent)
    request = NeoDestinationHandoff().request(destination="substack_notes", action="READBACK", intent=intent)
    assert request["expected_identity"] == "@capitalchronicle"
    assert request["native_payload"]["media_asset_ids"] == [page["media_assets"][0]["asset_id"]]
    assert Path(value["media_assets"][0]["path"]).parent == tmp_path / "notes" / notes.day_at(now) / "media"
    assert notes.validate_note(store, value) == value


def test_installed_minute_consumer_prepares_one_note_and_reuses_frozen_writer(ready, tmp_path):
    store, page, authored, now = ready
    calls = []
    def writer(prompt, **kwargs):
        calls.append(kwargs)
        assert "PUBLIC MAIN ANALYSES" in prompt and "400 characters" in prompt
        assert kwargs["writer"] is True
        return authored, {"configured_model": "gpt-6.1-sol", "configured_effort": "max"}
    first = notes.run_due(store, output_root=tmp_path / "notes", now=now, writer=writer, publish=False)
    assert first["state"] == "NOTE_PREPARED"
    second = notes.run_due(store, output_root=tmp_path / "notes", now=now, writer=writer, publish=False)
    assert second == first and len(calls) == 1
    script = Path(__file__).resolve().parents[1] / "scripts/plan_status_posts.py"
    assert 'result["substack_daily_note"] = daily_note(store' in script.read_text(encoding="utf-8")


@pytest.mark.parametrize("mutation,cause", [
    ("number", "NOTE_NUMBER_UNBOUND"), ("date", "NOTE_DATED_FIGURE_UNBOUND"),
    ("technical", "NOTE_MUST_LEAD"), ("ellipsis", "NOTE_COMPLETE_SHORT_SENTENCE|NOTE_SHAPE"),
    ("source", "NOTE_SENTENCE_SOURCE_UNBOUND"), ("model", "NOTE_INTERNAL_TERM"),
])
def test_wrong_public_copy_is_refused_before_registration(ready, tmp_path, mutation, cause):
    store, page, authored, now = ready
    value = deepcopy(authored)
    if mutation == "number": value["sentences"][0]["text"] = value["sentences"][0]["text"].replace("5%", "7%")
    if mutation == "date": value["sentences"][0]["fact_date"] = "1 Jan"
    if mutation == "technical": value["sentences"][0]["section"] = "technical"
    if mutation == "ellipsis": value["sentences"][0]["text"] += "…"
    if mutation == "source": value["sentences"][0]["source_excerpt"] = "Not in the analysis."
    if mutation == "model": value["sentences"][0]["text"] += " Our model."
    with pytest.raises(ValueError, match=cause):
        notes.register_note(store, page, value, now=now, output_root=tmp_path / "notes")
    assert not store.get_outbox_message(notes.identity(notes.day_at(now)))


def test_old_capture_cannot_be_refreshed_by_a_new_page_or_chart(ready, tmp_path):
    store, page, authored, now = ready
    with pytest.raises(ValueError, match="NOTE_DATA_CUTOFF_EXPIRED"):
        notes.register_note(store, page, authored, now=now + timedelta(hours=2), output_root=tmp_path / "notes")


def test_confirmed_note_keeps_readback_available_after_the_day_ends(ready, tmp_path):
    store, page, authored, now = ready
    value = notes.register_note(store, page, authored, now=now, output_root=tmp_path / "notes")
    # Registration/reconciliation can still read original bytes after expiry.
    assert pages.validate_link_plan(store, value["link_id"], value["plan"]) == value
    with pytest.raises(ValueError, match="NOTE_DATA_CUTOFF_EXPIRED"):
        notes.validate_note(store, value, now=now + timedelta(days=2))


def test_actual_capture_bytes_are_bound_and_unknown_capitals_never_gate(ready, tmp_path):
    store, page, authored, now = ready
    copy = deepcopy(authored)
    copy["sentences"][0]["text"] = "HICP is the focus. " + copy["sentences"][0]["text"]
    assert notes.validate_copy(copy, page).startswith("HICP")
    spec = notes.capture_clock(page)
    Path(spec["path"]).write_text('{"known_at_utc":"2099-01-01T00:00:00Z"}')
    with pytest.raises(ValueError, match="NOTE_SOURCE_CAPTURE_CHANGED"):
        notes.register_note(store, page, authored, now=now, output_root=tmp_path / "notes")


@pytest.mark.parametrize("at,day", [("2026-11-12T00:30:00Z", "2026-11-11"),
                                  ("2026-07-12T04:01:00Z", "2026-07-12")])
def test_daily_identity_uses_new_york_date_with_dst(at, day):
    assert notes.day_at(at) == day
