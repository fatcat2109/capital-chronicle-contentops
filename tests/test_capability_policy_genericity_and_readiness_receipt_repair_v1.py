from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/automation/CONTENTOPS_FAST_SHIP_CAPABILITY_POLICY_GENERICITY_AND_READINESS_RECEIPT_REPAIR_V1"
REGISTRY = ROOT / "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/source_evidence_capability_registry_v2.json"


def _read(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def _logical_hash(value: dict) -> str:
    core = {key: item for key, item in value.items() if key != "logical_hash"}
    encoded = json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _byte_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_blob(path: Path) -> str:
    return subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_readiness_records_bind_registry_modes_exact_hashes_and_fail_closed_authority():
    packet = _read("capability_readiness_records.json")
    assert packet["logical_hash"] == _logical_hash(packet)
    assert packet["record_count"] == len(packet["records"]) == 18
    assert packet["capability_registry"] == {
        "path": "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/source_evidence_capability_registry_v2.json",
        "git_blob_sha1": _git_blob(REGISTRY),
    }
    for record in packet["records"]:
        assert record["readiness_overlay"] == "DERIVED_READINESS_OVERLAY"
        assert record["capability_registry"] == packet["capability_registry"]
        assert record["effective_article_mode"] == "analysis"
        assert record["canonical_package_evidence"] == {
            "unchanged": True,
            "package_state": "PENDING_OPERATOR_DECISION",
            "editorial_state": "HOLD",
            "recommendation": "REQUEST_REVISION",
        }
        assert record["publication_authority"] is False
        assert record["dispatch_authority"] is False
        assert record["publication_readiness"] == "BLOCK"
        assert record["dispatch_readiness"] == "BLOCK"
        assert record["applicable_gates"]
        assert record["unresolved_blockers"]
        assert set(record["hashes"]) == {
            "package_hash",
            "article_hash",
            "v3_packet_hash",
            "variant_hash",
            "visual_policy_hash",
            "readiness_hash",
        }
        assert all(len(value) == 64 for value in record["hashes"].values())


def test_current_story_and_platform_policy_truth_is_preserved():
    records = _read("capability_readiness_records.json")["records"]
    by_story = {}
    for row in records:
        by_story.setdefault(row["story_id"], []).append(row)
    assert len(by_story) == 3
    usgs = next(rows for rows in by_story.values() if rows[0]["story_type"] == "physical_event")
    assert all(row["market_sensitive"] is False for row in usgs)
    assert all(row["market_snapshot_required"] is False for row in usgs)
    for rows in by_story.values():
        substack = next(row for row in rows if row["platform_id"] == "substack_newsletter")
        assert substack["effective_platform_visual_mode"] == "long_form"
        for row in rows:
            if row["platform_id"] != "substack_newsletter":
                assert row["effective_platform_visual_mode"] == "text_only"
                assert row["variant_mode"] == "dry_run"


def test_validation_truth_and_manifest_hashes_are_exact_and_replayable():
    truth = _read("validation_truth.json")
    manifest = _read("final_manifest.json")
    assert truth["logical_hash"] == _logical_hash(truth)
    assert truth["result"] == "PASS"
    assert truth["blocker_count"] == 0
    assert all(truth["checks"].values())
    assert manifest["logical_hash"] == _logical_hash(manifest)
    assert manifest["starting_remote_head"] == "6de0a8c8fc3cfc510b9ffa0e840e701fabd6e466"
    assert manifest["record_count"] == 18
    assert manifest["publication_authority"] is False
    assert manifest["dispatch_authority"] is False
    assert manifest["public_write_performed"] is False
    assert manifest["monolithic_repository_suite_run"] is False
    assert manifest["ci_pass_claimed"] is False
    assert manifest["capability_registry"]["git_blob_sha1"] == _git_blob(REGISTRY)
    assert manifest["capability_registry"]["byte_sha256"] == _byte_hash(REGISTRY)
    for artifact in manifest["canonical_evidence_unchanged"] + manifest["output_artifacts"]:
        assert artifact["byte_sha256"] == _byte_hash(ROOT / artifact["path"])
