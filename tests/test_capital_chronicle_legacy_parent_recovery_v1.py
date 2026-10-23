"""Exact public Main Goal27 wires, plus explicitly altered negative controls."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    LatestReportDeliveryTracker, canonical_bytes, sha256_of, validate_latest_report_bytes,
)
from live_contentops.capital_chronicle_public_manifest_v1 import PublicMainFileSource
from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
from live_contentops.capital_chronicle_legacy_parent_recovery_v1 import recover_pinned_parent, recovery_binding
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

PROOF = Path(__file__).resolve().parents[1] / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal29"
NOW = "2026-10-21T00:00:00Z"


def source():
    pointer = json.loads((PROOF / "provider_resume_binding.json").read_bytes())
    pointer["public_export_root"] = str(PROOF / "main_public_handoff/public-handoff")
    src = PublicMainFileSource(pointer)
    src.refresh(cutoff_utc=NOW)
    return pointer, src


def validate(bundle):
    return validate_latest_report_bytes(bundle["envelope"], expected_cutoff_utc=NOW,
        envelope_schema_bytes=bundle["envelope_schema"], producer_binding=bundle["binding"],
        public_export_bytes=bundle["public_export"], allow_lineage_only=True)


@pytest.mark.parametrize("asset,version", [("UKOIL", 3), ("XNGUSD", 4)])
def test_only_exact_legacy_bytes_recover_as_ancestry(asset, version):
    _, src = source()
    spec = next(e for e in src.manifest["entries"] if e["asset_id"] == asset and e["report_version"] == version)
    bundle = src.bundle(spec)
    original = deepcopy(bundle)
    failed = validate(bundle)
    assert failed["status"] == "BLOCKED" and "SEALED_HASH_MISMATCH" in failed["blockers"]
    recovered = recover_pinned_parent(bundle, failed, cutoff_utc=NOW)
    assert recovered["status"] == "ADMITTED" and recovered["lineage_only"] is True
    assert recovered["claims"] == recovered["horizon_blocks"] == []
    assert recovered["withdrawal_only"] is False
    assert recovered["source_report_sha256"] == spec["report_sha256"]
    assert recovered["raw_sha256"] == failed["raw_sha256"]
    assert recovered["lineage_recovery"]["editorial_claim_credit"] == 0
    assert bundle == original
    for field in ("envelope", "public_export", "envelope_schema"):
        changed = deepcopy(bundle)
        changed[field] += b" "
        assert recover_pinned_parent(changed, failed, cutoff_utc=NOW) is None
    for field in ("producer_commit", "manifest_sha256"):
        changed = deepcopy(bundle)
        changed["binding"][field] = "0" * len(changed["binding"][field])
        assert recover_pinned_parent(changed, failed, cutoff_utc=NOW) is None
    changed = deepcopy(bundle)
    changed["binding"]["legacy_parent_recovery"]["pin"]["report_sha256"] = "f" * 64
    assert recover_pinned_parent(changed, failed, cutoff_utc=NOW) is None
    # A modified authority/rights/schema defect cannot be smuggled in via the grant.
    for transform in (lambda e: e.update(publication_authority=True),
                      lambda e: e["public_safe_claims"][0].update(rights_state="PRIVATE"),
                      lambda e: e.update(version="unsupported")):
        changed = deepcopy(bundle)
        envelope = json.loads(changed["envelope"])
        transform(envelope)
        changed["envelope"] = canonical_bytes(envelope)
        assert recover_pinned_parent(changed, validate(changed), cutoff_utc=NOW) is None


def test_recovery_is_opt_in_and_not_a_generic_manifest_or_parent_bypass():
    pointer, src = source()
    spec = src.manifest["entries"][0]
    raw = src._read("manifests/" + src.manifest["manifest_sha256"] + ".json")
    assert recovery_binding(pointer, src.manifest, spec, raw) is None
    parent = next(e for e in src.manifest["entries"] if e["asset_id"] == "UKOIL" and e["report_version"] == 3)
    assert recovery_binding({**pointer, "legacy_parent_recovery": "disabled"}, src.manifest, parent, raw) is None
    with pytest.raises(ValueError, match="SOURCE_UNPINNED"):
        recovery_binding({**pointer, "producer_commit": "0" * 40}, src.manifest, parent, raw)
    changed = deepcopy(src.manifest)
    changed["latest_by_asset"]["UKOIL"]["parent_report_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="CHILD_UNPINNED"):
        recovery_binding(pointer, changed, parent, raw)


def test_cold_feed_admits_three_latest_and_replays_without_duplicate_receipts(tmp_path, monkeypatch):
    pointer, _ = source()
    tracker = LatestReportDeliveryTracker(ContentOpsDurableStore(tmp_path / "disposable.sqlite3"))
    feed = MainReportFeed(tracker, pointer, headline_paths=[])
    scan = feed.poll(cutoff_utc=NOW)
    assert not scan["gaps"]
    assert {(r["report_id"], r["report_version"]) for r in feed.pending()} == {
        ("asset-report:UKOIL", 4), ("asset-report:USOIL", 6), ("asset-report:XNGUSD", 5)}
    receipts = tracker.receipts()
    parents = [r for r in receipts if r.get("lineage_recovery")]
    assert len(parents) == 2 and all(r["status"] == "LINEAGE_ONLY_NOOP" and not r["claims"] for r in parents)
    for parent in parents:
        assert any(r["receipt_id"] == parent["lineage_recovery"]["original_failure_receipt_id"]
            and r["status"] == "BLOCKED" for r in receipts)
    from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
    summary = report_workspace_projection(tracker.store.list_outbox_messages())["main_admission_summary"]
    assert {r["report_id"]: r["report_version"] for r in summary} == {
        "asset-report:UKOIL": 4, "asset-report:USOIL": 6, "asset-report:XNGUSD": 5}
    assert sum(r["claims"] for r in summary) == 49
    assert sum(r["native_public_excerpts"] for r in summary) == 46
    assert all(r["independent_native_runtime_verified"] is False for r in summary)
    monkeypatch.setattr(feed.source, "bundle", lambda *_: pytest.fail("Unchanged immutable bundle reread"))
    assert feed.poll(cutoff_utc=NOW)["new_events"] == 0
    assert tracker.receipts() == receipts


def test_recovery_does_not_override_existing_tracker_hash_conflict(tmp_path):
    _, src = source()
    spec = next(e for e in src.manifest["entries"] if e["asset_id"] == "UKOIL" and e["report_version"] == 3)
    bundle = src.bundle(spec)
    recovered = recover_pinned_parent(bundle, validate(bundle), cutoff_utc=NOW)
    tracker = LatestReportDeliveryTracker(ContentOpsDurableStore(tmp_path / "conflict.sqlite3"))
    # Controlled conflicting prior identity, never factual or production evidence.
    conflicting = {**deepcopy(recovered), "report_version": 2, "source_report_sha256": "f" * 64,
        "raw_sha256": "e" * 64, "parent_report_id": None, "parent_report_sha256": None,
        "change_kind": "NEW_REPORT"}
    assert tracker.consume(conflicting, receipt_id="controlled-prior")["status"] == "LINEAGE_ONLY_NOOP"
    assert tracker.consume(recovered, receipt_id="exact-legacy-parent")["status"] == "LINEAGE_HASH_CONFLICT"
    assert all(not r["claims"] for r in tracker.receipts())


@pytest.mark.parametrize("asset", ["UKOIL", "XNGUSD", "USOIL"])
def test_native_public_provenance_is_exact_attestation_not_runtime_proof(asset):
    _, src = source()
    bundle = src.bundle(src.manifest["latest_by_asset"][asset])
    admitted = validate(bundle)
    assert admitted["status"] == "ADMITTED"
    if asset == "USOIL":
        assert admitted["native_public_lineage"] is None and len(admitted["claims"]) == 1
        return
    native = admitted["native_public_lineage"]
    assert native["permitted_excerpt_count"] == 23
    assert native["consumer_exact_public_bindings_verified"] is True
    assert native["independent_native_runtime_verified"] is False
    assert native["private_worker_artifacts_read"] is False
    for field in ("claim_id", "claim_hash", "text_sha256", "evidence_refs"):
        changed = deepcopy(bundle)
        public = json.loads(changed["public_export"])
        lineage = public["latest_reports"][0]["native_public_lineage"]
        lineage["excerpts"][0][field] = [] if field == "evidence_refs" else "0" * 64
        lineage["lineage_sha256"] = sha256_of({k: v for k, v in lineage.items() if k != "lineage_sha256"})
        public["projection_sha256"] = sha256_of({k: v for k, v in public.items() if k != "projection_sha256"})
        changed["public_export"] = canonical_bytes(public)
        changed["binding"]["public_report_raw_sha256"] = hashlib.sha256(changed["public_export"]).hexdigest()
        assert "PUBLIC_NATIVE_LINEAGE_BINDING_INVALID" in validate(changed)["blockers"]


@pytest.mark.parametrize("field,value", [("role_proof_sha256", []), ("critical_review", []), ("excerpts", [None])])
def test_malformed_optional_native_lineage_fails_closed(field, value):
    from live_contentops.capital_chronicle_public_native_lineage_v1 import interpret_public_native_lineage
    _, src = source()
    bundle = src.bundle(src.manifest["latest_by_asset"]["UKOIL"])
    public, envelope = json.loads(bundle["public_export"]), json.loads(bundle["envelope"])
    row = public["latest_reports"][0]
    row["native_public_lineage"][field] = value
    native = row["native_public_lineage"]
    native["lineage_sha256"] = sha256_of({k: v for k, v in native.items() if k != "lineage_sha256"})
    with pytest.raises(ValueError, match="PUBLIC_NATIVE_LINEAGE_BINDING_INVALID"):
        interpret_public_native_lineage(row, envelope)
