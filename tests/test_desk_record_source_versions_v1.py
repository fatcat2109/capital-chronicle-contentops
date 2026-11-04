"""Versioned Main exports reach the existing editorial request with exact values."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_desk_record_source_v1 import read_export, desk_evidence
from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker, sha256_of
from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired

FIXTURE = Path(__file__).parent / "fixtures/desk_record_export_v1/desk_record_export_v1.fixture.json"
NOW = "2026-10-30T16:00:00Z"


def versioned_doc(version):
    doc = json.loads(FIXTURE.read_bytes())
    doc["schema_version"] = version
    if version in {"1.2.0", "1.3.0"}:
        for record in doc["decision_records"]:
            for key in ("condition", "trigger", "invalidation_level"):
                record[key] = {**copy.deepcopy(record["invalidation"]), "value": None,
                               "missing_cause": "SYNTHETIC_VERSION_COMPATIBILITY_TEST"}
    if version == "1.3.0":
        record = doc["decision_records"][0]
        record["call"] = {**record["call"], "value": "OPEN", "visibility": "private",
                          "rights_class": "DEMO_DERIVED_PRIVATE",
                          "use_label": "PRIVATE_RESEARCH_AND_DEMO_DECISIONS_ONLY_NEVER_PUBLIC"}
        for dossier in doc["asset_dossiers"]:
            for plan in dossier["open_plans"]:
                plan["planned_exit_at_utc"] = {**copy.deepcopy(plan["status"]), "value": None,
                                              "missing_cause": "SYNTHETIC_VERSION_COMPATIBILITY_TEST"}
    return doc


def write_export(tmp_path, doc):
    doc["integrity"]["content_sha256"] = sha256_of({k: v for k, v in doc.items() if k != "integrity"})
    path = tmp_path / "export.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "allow_fixture_private_preview": True}


@pytest.mark.parametrize("version", ["1.0.0", "1.1.0", "1.2.0", "1.3.0"])
def test_supported_export_reaches_native_selection_with_exact_public_fields(tmp_path, version):
    doc = versioned_doc(version)
    spec = write_export(tmp_path, doc)
    store = ContentOpsDurableStore(tmp_path / "copy.sqlite3")
    feed = MainReportFeed(LatestReportDeliveryTracker(store), {"desk_record_exports": [spec]}, headline_paths=[])
    turn = NativeDesktopTurn(store, run_id="version-" + version, output_dir=tmp_path / "article",
                             owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as pending:
        feed.opportunity(output_dir=tmp_path / "article", cutoff_utc=NOW, run_id=turn.run_id,
                         rolling_input={"headlines": []}, llm_invoke=turn)
    request = json.dumps(pending.value.request)
    assert "event:US_ECI_20261030" in request
    assert all(str(sentinel) not in request for sentinel in doc["fixture_sentinels"])
    frozen = json.loads(store.get_outbox_message("native-current-input-" + sha256_of(turn.run_id))["payload"])
    records = frozen["feed_scan"]["desk_record_sources"]
    actual = next(f for r in records for f in r["binding"]["fields"]
                  if f["citation"].endswith("/measures/eci_civilian_compensation_12m_nsa/actual"))
    assert actual["value"] == 3.4 and actual["display"] == "3.4" and actual["decimals"] == 1
    assert all(f["rights_class"] != "DEMO_DERIVED_PRIVATE" for r in records for f in r["binding"]["fields"])


@pytest.mark.parametrize("version", ["0.9.0", "1.4.0", "2.0.0"])
def test_unknown_schema_is_named_without_falling_back_to_another_contract(tmp_path, version):
    with pytest.raises(ValueError, match="DESK_EXPORT_SCHEMA_VERSION_UNSUPPORTED"):
        read_export(write_export(tmp_path, versioned_doc(version)), cutoff_utc=NOW)


def test_new_version_does_not_accept_unknown_fields_or_future_bytes(tmp_path):
    doc = versioned_doc("1.3.0")
    doc["invented_field"] = "invalid"
    with pytest.raises(ValueError, match="DESK_EXPORT_SCHEMA_INVALID"):
        read_export(write_export(tmp_path, doc), cutoff_utc=NOW)
    doc.pop("invented_field")
    with pytest.raises(ValueError, match="DESK_EXPORT_AFTER_CUTOFF"):
        read_export(write_export(tmp_path, doc), cutoff_utc="2026-10-29T16:00:00Z")


def test_published_report_event_field_joins_existing_dated_evidence(tmp_path):
    doc = versioned_doc("1.1.0")
    report = doc["reports"][0]
    field = report["title"]
    private = {"rights_class": "INTERNAL_PROVENANCE", "visibility": "private", "use_label": "INTERNAL_ONLY",
               "source_ids": [], "value": "synthetic compatibility test"}
    report.update(report_type="EVENT_REVIEW", standfirst={**field, "value": "Dated compensation review"},
                  event_id={**field, "value": "US_ECI_20261030"},
                  declared_rights_class=private, publisher_seal=private, conditional_calls=private,
                  published_at_utc=report["generated_at_utc"],
                  outlets=[{"name": {**field, "value": "substack"},
                            "url": {**field, "value": "https://example.com/p/compatibility-test"}}])
    records = read_export(write_export(tmp_path, doc), cutoff_utc=NOW)
    selected = next(r for r in records if r["binding"]["record_id"] == report["record_id"])
    assert selected["binding"]["event_ids"] == ["US_ECI_20261030"]
    evidence = desk_evidence(records, {"headline_ids": [selected["headline_id"]]})
    assert evidence["evidence_documents"][0]["desk_record_binding"]["record_id"] == report["record_id"]
    assert "asset:USDJPY" in {d["desk_record_binding"]["record_id"] for d in evidence["evidence_documents"]}
