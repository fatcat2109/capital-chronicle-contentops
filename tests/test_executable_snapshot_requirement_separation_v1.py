from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess

import pytest

import live_contentops.generic_editorial_fabric_v2 as generic_fabric
from live_contentops.freshness_market_state_v2 import evaluate_freshness
from live_contentops.source_capability_registry_v2 import (
    load_source_capability_registry,
    resolve_story_capabilities,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/automation/CONTENTOPS_FAST_SHIP_EXECUTABLE_SNAPSHOT_REQUIREMENT_SEPARATION_V1"
SNAPSHOT_BLOCKERS = {
    "market_sensitive_story_snapshot_stale_or_missing",
    "market_sensitive_story_ingest_stale_or_missing",
}


def _logical_hash(value: dict) -> str:
    core = {key: item for key, item in value.items() if key != "logical_hash"}
    encoded = json.dumps(core, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _git_blob(path: str) -> str:
    return subprocess.run(
        ["git", "hash-object", path],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _packet_without_market_state() -> dict:
    return {
        "schema_version": "capital_chronicle_content_evidence_packet.v2",
        "packet_id": "snapshot-separation-fixture",
        "as_of_utc": "2026-08-01T12:00:00Z",
        "events": [{"event_time_utc": "2026-08-01T11:00:00Z"}],
        "headlines": [],
        "official_source_documents": [],
        "numeric_claims": [],
        "market_snapshots": [],
        "blockers": [],
        "validation_blockers": [],
    }


@pytest.mark.parametrize(
    ("market_sensitive", "snapshot_value", "expected_required", "expected_blocked"),
    [
        (True, True, True, True),
        (True, False, False, False),
        (False, True, True, True),
        (False, False, False, False),
        (True, None, True, True),
    ],
    ids=[
        "sensitive_snapshot_required",
        "sensitive_snapshot_not_required",
        "nonsensitive_snapshot_required",
        "nonsensitive_snapshot_not_required",
        "snapshot_absent_legacy_sensitive_default",
    ],
)
def test_executable_snapshot_requirement_truth_table(
    market_sensitive: bool,
    snapshot_value: bool | None,
    expected_required: bool,
    expected_blocked: bool,
) -> None:
    request = {
        "article_mode": "explainer",
        "market_sensitive": market_sensitive,
        "fresh_material_delta": True,
    }
    if snapshot_value is not None:
        request["market_snapshot_required"] = snapshot_value
    decision = evaluate_freshness(_packet_without_market_state(), request)
    present = SNAPSHOT_BLOCKERS.intersection(decision["blockers"])
    assert decision["market_sensitive"] is market_sensitive
    assert decision["market_snapshot_required"] is expected_required
    assert (present == SNAPSHOT_BLOCKERS) is expected_blocked
    assert decision["decision"] == ("BLOCK" if expected_blocked else "PASS")


def test_market_sensitivity_remains_distinct_for_downgrade_restrictions() -> None:
    packet = _packet_without_market_state()
    packet["blockers"] = ["independent_editorial_blocker"]
    common = {
        "article_mode": "analysis",
        "market_snapshot_required": False,
        "allow_mode_downgrade": True,
        "fresh_material_delta": True,
    }
    sensitive = evaluate_freshness(packet, {**common, "market_sensitive": True})
    nonsensitive = evaluate_freshness(packet, {**common, "market_sensitive": False})
    assert sensitive["decision"] == "BLOCK"
    assert nonsensitive["decision"] == "DOWNGRADE_TO_EXPLAINER"


def test_generic_fabric_flows_resolver_snapshot_policy_into_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = deepcopy(load_source_capability_registry())
    physical = registry["story_types"]["physical_event"]
    physical["market_sensitive"] = True
    physical["market_snapshot_required"] = False
    monkeypatch.setattr(generic_fabric, "load_source_capability_registry", lambda: registry)

    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(_packet_without_market_state()), encoding="utf-8")
    result = generic_fabric.run_generic_prepare_only(
        output_dir=tmp_path / "out",
        evidence_packet_path=packet_path,
        story_request={
            "source_family_id": "usgs_comcat",
            "article_mode": "analysis",
            "fresh_material_delta": True,
            "article_candidate": {},
            "visual_assets": [],
        },
    )
    freshness = json.loads(
        (tmp_path / "out" / "freshness_market_state_decision_v2.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["capabilities"]["market_sensitive"] is True
    assert result["capabilities"]["market_snapshot_required"] is False
    assert freshness["market_sensitive"] is True
    assert freshness["market_snapshot_required"] is False
    assert not SNAPSHOT_BLOCKERS.intersection(freshness["blockers"])


def test_backend_and_committed_v5_readiness_parity_for_current_three_packages() -> None:
    registry = load_source_capability_registry()
    expected = {
        "policy_decision": ("federal_reserve_fomc", True, True),
        "company_sector_event": ("sec_edgar", True, True),
        "physical_event": ("usgs_comcat", False, False),
    }
    records_path = ROOT / (
        "docs/automation/CONTENTOPS_FAST_SHIP_CAPABILITY_POLICY_GENERICITY_AND_"
        "READINESS_RECEIPT_REPAIR_V1/capability_readiness_records.json"
    )
    records = json.loads(records_path.read_text(encoding="utf-8"))["records"]
    for story_type, (source_family, sensitive, snapshot_required) in expected.items():
        capability = resolve_story_capabilities(
            {"source_family_id": source_family}, registry
        )
        assert capability["market_sensitive"] is sensitive
        assert capability["market_snapshot_required"] is snapshot_required
        ui_rows = [row for row in records if row["story_type"] == story_type]
        assert len(ui_rows) == 6
        assert all(row["market_sensitive"] is sensitive for row in ui_rows)
        assert all(
            row["market_snapshot_required"] is snapshot_required for row in ui_rows
        )


def test_snapshot_requirement_evidence_is_hash_bound_and_no_write() -> None:
    truth = json.loads(
        (EVIDENCE / "snapshot_requirement_truth_table.json").read_text(
            encoding="utf-8"
        )
    )
    validation = json.loads(
        (EVIDENCE / "validation_truth.json").read_text(encoding="utf-8")
    )
    manifest = json.loads(
        (EVIDENCE / "final_manifest.json").read_text(encoding="utf-8")
    )
    assert truth["logical_hash"] == _logical_hash(truth)
    assert validation["logical_hash"] == _logical_hash(validation)
    assert manifest["logical_hash"] == _logical_hash(manifest)
    assert truth["starting_commit"] == "bec002937d9de37f31092acb67fc0965d085e85c"
    assert truth["case_count"] == len(truth["cases"]) == 5
    assert all(row["pass"] for row in truth["cases"])
    assert validation["result"] == "PASS"
    assert validation["blocker_count"] == 0
    assert all(validation["checks"].values())
    assert manifest["starting_remote_head"] == truth["starting_commit"]
    assert manifest["canonical_package_evidence"]["unchanged"] is True
    assert manifest["no_write_state"]["publication_authority"] is False
    assert manifest["no_write_state"]["dispatch_authority"] is False
    assert manifest["no_write_state"]["public_write_performed"] is False
    assert manifest["monolithic_repository_suite_run"] is False
    assert manifest["ci_pass_claimed"] is False
    for artifact in manifest["source_blobs"]:
        assert artifact["git_blob_sha1"] == _git_blob(artifact["path"])
    for artifact in manifest["canonical_package_evidence"]["artifacts"]:
        assert artifact["git_blob_sha1"] == _git_blob(artifact["path"])
    for artifact in manifest["output_artifacts"]:
        path = ROOT / artifact["path"]
        assert artifact["byte_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
