"""Consumer checks against the producer's exact numeric policy; isolated fixtures only."""
import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_desk_record_source_v1 import read_export, validate_article_citations
from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker, sha256_of
from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired, NativeDesktopTurn
from tests.test_capital_chronicle_desk_record_source_v1 import FIXTURE, NOW, spec
from tools.product.desk_record_projection_v1 import RECORD_LISTS, iter_fields


def write_export(tmp_path, doc):
    doc["integrity"]["content_sha256"] = sha256_of({k: v for k, v in doc.items() if k != "integrity"})
    path = tmp_path / "controlled-export.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return spec(path)


def dossier(doc):
    return next(row for row in doc["asset_dossiers"] if row["asset_id"] == "USDJPY")


def private_number(doc, rights, value):
    field = next(f for _, f in iter_fields({k: doc[k] for k in RECORD_LISTS})
        if f["rights_class"] == rights and isinstance(f["value"], (int, float)) and not isinstance(f["value"], bool))
    field["value"] = value


@pytest.mark.parametrize("rights", ["MARKET_CONSENSUS_PRIVATE_ONLY", "OPTIONS_GEX_PRIVATE_ONLY", "DEMO_DERIVED_PRIVATE"])
@pytest.mark.parametrize("written", ["2,412.35", "2412.4", "2412.3", "\u22122412.35"])
def test_consumer_refuses_reformatted_private_values_before_creating_source_records(tmp_path, rights, written):
    doc = json.loads(FIXTURE.read_bytes())
    private_number(doc, rights, 2412.35)
    dossier(doc)["headline_analysis"]["value"] = f"The retained level was {written} at the close."
    with pytest.raises(ValueError, match="DESK_EXPORT_REFERENCE_CLOCK_OR_PUBLIC_TEXT_INVALID"):
        read_export(write_export(tmp_path, doc), cutoff_utc=NOW)


@pytest.mark.parametrize("written", ["157.695", "157.70"])
def test_private_prose_numbers_are_refused_at_exact_and_allowed_rounded_precision(tmp_path, written):
    doc = json.loads(FIXTURE.read_bytes())
    doc["decision_records"][0]["rationale"]["value"] = "Entry reference 157.695 on the retained quote."
    dossier(doc)["headline_analysis"]["value"] = f"The level was near {written} during the release."
    with pytest.raises(ValueError, match="REFERENCE_CLOCK_OR_PUBLIC_TEXT"):
        read_export(write_export(tmp_path, doc), cutoff_utc=NOW)


@pytest.mark.parametrize("written", ["0.8R", "0.8 R"])
def test_short_demo_results_stay_private_when_written_as_r_multiples(tmp_path, written):
    doc = json.loads(FIXTURE.read_bytes())
    doc["decision_records"][0]["demo"]["result_r"]["value"] = -0.8
    doc["decision_records"][0]["demo"]["result_r"].pop("missing_cause", None)
    dossier(doc)["headline_analysis"]["value"] = f"The retained trade lost {written}."
    with pytest.raises(ValueError, match="REFERENCE_CLOCK_OR_PUBLIC_TEXT"):
        read_export(write_export(tmp_path, doc), cutoff_utc=NOW)


@pytest.mark.parametrize("private,written", [
    (4.6812, "The Treasury yield was 4.68% on the day."),
    (2412.35, "The index ended near 2412 points."),
    (2412.35, "The release date was 2026-10-30 at 12:30 UTC."),
])
def test_consumer_keeps_producer_permitted_precision_and_clock_distinctions(tmp_path, private, written):
    doc = json.loads(FIXTURE.read_bytes())
    private_number(doc, "DEMO_DERIVED_PRIVATE", private)
    dossier(doc)["headline_analysis"]["value"] = written
    records = read_export(write_export(tmp_path, doc), cutoff_utc=NOW)
    record = next(r for r in records if r["binding"]["record_id"] == "asset:USDJPY")
    assert next(f["value"] for f in record["binding"]["fields"] if f["field_path"] == "/headline_analysis") == written
    assert "open_plans" not in json.dumps(record)


def test_public_official_point_eight_percent_does_not_collide_with_short_private_r_result(tmp_path):
    doc = json.loads(FIXTURE.read_bytes())
    doc["decision_records"][0]["demo"]["result_r"]["value"] = -0.8
    doc["decision_records"][0]["demo"]["result_r"].pop("missing_cause", None)
    dossier(doc)["headline_analysis"]["value"] = "Civilian compensation rose 0.8% in the third quarter."
    records = read_export(write_export(tmp_path, doc), cutoff_utc=NOW)
    text = json.dumps(records)
    assert "0.8%" in text and "result_r" not in text


def test_invalid_private_prose_export_never_enters_existing_native_input(tmp_path):
    doc = json.loads(FIXTURE.read_bytes())
    doc["decision_records"][0]["rationale"]["value"] = "Entry reference 157.695 on the retained quote."
    leak = "CONTROLLED-PRIVATE-NUMBER-LEAK near 157.70"
    dossier(doc)["headline_analysis"]["value"] = leak
    invalid = write_export(tmp_path, doc)
    store = ContentOpsDurableStore(tmp_path / "isolated.sqlite3")
    feed = MainReportFeed(LatestReportDeliveryTracker(store),
        {"desk_record_exports": [invalid, spec()]}, headline_paths=[])
    turn = NativeDesktopTurn(store, run_id="cc043-normalizer-control", output_dir=tmp_path / "article",
        owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as pending:
        feed.opportunity(output_dir=turn.root, cutoff_utc=NOW, run_id=turn.run_id,
            rolling_input={"headlines": []}, llm_invoke=turn)
    assert pending.value.request["stage"] == "select"
    payload = json.dumps(pending.value.request)
    assert "event:US_ECI_20261030" in payload and leak not in payload and "157.70" not in payload
    frozen = json.loads(store.get_outbox_message("native-current-input-" + sha256_of(turn.run_id))["payload"])
    assert frozen["feed_scan"]["gaps"] == [{"state": "MAIN_DESK_EXPORT_UNAVAILABLE_OR_INVALID",
        "cause": "DESK_EXPORT_REFERENCE_CLOCK_OR_PUBLIC_TEXT_INVALID"}]
    assert len(frozen["feed_scan"]["desk_record_sources"]) == 17
    assert all(s not in payload for s in doc["fixture_sentinels"])
    assert not store.list_platform_dispatches()


def test_existing_reviewed_reader_article_retains_all_exact_field_citations():
    evidence = Path(__file__).parent / "evidence/cc-043"
    value = json.loads((evidence / "article.json").read_bytes())
    records = read_export(spec(), cutoff_utc=NOW)
    validation = validate_article_citations(value, records)
    prior = json.loads((evidence / "validation.json").read_bytes())["native_fixture_article"]["field_validation"]
    assert validation == prior and validation["citation_count"] == 20
