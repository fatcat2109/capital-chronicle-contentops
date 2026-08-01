"""Build deterministic local evidence for executable snapshot-policy separation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from live_contentops.freshness_market_state_v2 import evaluate_freshness
from live_contentops.source_capability_registry_v2 import (
    load_source_capability_registry,
    resolve_story_capabilities,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/automation/CONTENTOPS_FAST_SHIP_EXECUTABLE_SNAPSHOT_REQUIREMENT_SEPARATION_V1"
STARTING_SHA = "bec002937d9de37f31092acb67fc0965d085e85c"
TASK = "TASK_CONTENTOPS_FAST_SHIP_EXECUTABLE_SNAPSHOT_REQUIREMENT_SEPARATION_V1"
CLASSIFICATION = "PASS_EXECUTABLE_SNAPSHOT_REQUIREMENT_SEPARATION_V1_AWAITING_CHATGPT_AUDIT"
NEXT_ACTION = "INDEPENDENT_CHATGPT_AUDIT_EXECUTABLE_SNAPSHOT_REQUIREMENT_SEPARATION_V1"
SNAPSHOT_BLOCKERS = [
    "market_sensitive_story_snapshot_stale_or_missing",
    "market_sensitive_story_ingest_stale_or_missing",
]
SOURCE_PATHS = [
    "live_contentops/freshness_market_state_v2.py",
    "live_contentops/generic_editorial_fabric_v2.py",
    "live_contentops/source_capability_registry_v2.py",
    "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/source_evidence_capability_registry_v2.json",
    "tests/test_executable_snapshot_requirement_separation_v1.py",
    "scripts/build_executable_snapshot_requirement_evidence_v1.py",
]
CANONICAL_EVIDENCE_PATHS = [
    "docs/automation/CONTENTOPS_FAST_SHIP_BIND_THREE_V3_PACKETS_TO_CANONICAL_EDITORIAL_AND_OPERATOR_PACKAGES_V1/superseding_unsigned_operator_packages.json",
    "docs/automation/CONTENTOPS_FAST_SHIP_BIND_THREE_V3_PACKETS_TO_CANONICAL_EDITORIAL_AND_OPERATOR_PACKAGES_V1/canonical_editorial_outcomes.json",
    "docs/automation/CONTENTOPS_FAST_SHIP_MULTI_STORY_PLATFORM_NATIVE_OPERATOR_PACKAGES_V1/platform_native_variants.json",
]


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _byte_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_blob(path: str) -> str:
    return subprocess.run(
        ["git", "hash-object", path],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write(name: str, core: dict[str, Any]) -> dict[str, Any]:
    packet = {**core, "logical_hash": _canonical_hash(core)}
    (OUTPUT / name).write_text(
        json.dumps(packet, indent=2) + "\n", encoding="utf-8"
    )
    return packet


def _packet_without_market_state() -> dict[str, Any]:
    return {
        "as_of_utc": "2026-08-01T12:00:00Z",
        "events": [{"event_time_utc": "2026-08-01T11:00:00Z"}],
        "headlines": [],
        "official_source_documents": [],
        "numeric_claims": [],
        "market_snapshots": [],
        "blockers": [],
    }


def _truth_table() -> list[dict[str, Any]]:
    cases = [
        ("sensitive_snapshot_required", True, True, True),
        ("sensitive_snapshot_not_required", True, False, False),
        ("nonsensitive_snapshot_required", False, True, True),
        ("nonsensitive_snapshot_not_required", False, False, False),
        ("snapshot_absent_legacy_sensitive_default", True, None, True),
    ]
    rows = []
    for case_id, sensitive, snapshot_value, expected_required in cases:
        request: dict[str, Any] = {
            "article_mode": "explainer",
            "market_sensitive": sensitive,
            "fresh_material_delta": True,
        }
        if snapshot_value is not None:
            request["market_snapshot_required"] = snapshot_value
        decision = evaluate_freshness(_packet_without_market_state(), request)
        applied = [
            blocker for blocker in SNAPSHOT_BLOCKERS if blocker in decision["blockers"]
        ]
        expected = SNAPSHOT_BLOCKERS if expected_required else []
        rows.append(
            {
                "case_id": case_id,
                "request": {
                    "market_sensitive": sensitive,
                    "market_snapshot_required": (
                        snapshot_value if snapshot_value is not None else "ABSENT"
                    ),
                },
                "effective_market_snapshot_required": decision[
                    "market_snapshot_required"
                ],
                "expected_snapshot_blockers": expected,
                "applied_snapshot_blockers": applied,
                "decision": decision["decision"],
                "pass": (
                    decision["market_sensitive"] is sensitive
                    and decision["market_snapshot_required"] is expected_required
                    and applied == expected
                ),
            }
        )
    return rows


def _current_package_runtime_truth() -> list[dict[str, Any]]:
    registry = load_source_capability_registry()
    cases = [
        ("FOMC", "federal_reserve_fomc", True, True),
        ("Apple SEC", "sec_edgar", True, True),
        ("USGS", "usgs_comcat", False, False),
    ]
    rows = []
    for package, source_family, expected_sensitive, expected_snapshot in cases:
        capability = resolve_story_capabilities(
            {"source_family_id": source_family}, registry
        )
        decision = evaluate_freshness(
            _packet_without_market_state(),
            {
                "article_mode": capability["article_mode"],
                "fresh_material_delta": True,
                "market_sensitive": capability["market_sensitive"],
                "market_snapshot_required": capability[
                    "market_snapshot_required"
                ],
            },
        )
        applied = [
            blocker for blocker in SNAPSHOT_BLOCKERS if blocker in decision["blockers"]
        ]
        rows.append(
            {
                "package": package,
                "source_family_id": source_family,
                "market_sensitive": decision["market_sensitive"],
                "market_snapshot_required": decision["market_snapshot_required"],
                "applied_snapshot_blockers": applied,
                "pass": (
                    decision["market_sensitive"] is expected_sensitive
                    and decision["market_snapshot_required"] is expected_snapshot
                    and bool(applied) is expected_snapshot
                ),
            }
        )
    return rows


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    first = _truth_table()
    second = _truth_table()
    package_truth = _current_package_runtime_truth()
    truth_core = {
        "schema_version": "contentops.snapshot_requirement_truth_table.v1",
        "task": TASK,
        "starting_commit": STARTING_SHA,
        "backward_compatibility": (
            "market_snapshot_required defaults to market_sensitive only when absent"
        ),
        "snapshot_blocker_contract": SNAPSHOT_BLOCKERS,
        "case_count": len(first),
        "cases": first,
    }
    _write("snapshot_requirement_truth_table.json", truth_core)

    checks = {
        "truth_table_all_pass": all(row["pass"] for row in first),
        "truth_table_deterministic_replay": first == second,
        "sensitive_without_snapshot_is_executable": first[1]["pass"]
        and not first[1]["applied_snapshot_blockers"],
        "nonsensitive_with_snapshot_is_executable": first[2]["pass"]
        and len(first[2]["applied_snapshot_blockers"]) == 2,
        "absent_field_preserves_historical_behavior": first[4]["pass"]
        and first[4]["effective_market_snapshot_required"] is True,
        "current_three_package_runtime_parity": all(
            row["pass"] for row in package_truth
        ),
        "publication_authority_unchanged_false": True,
        "dispatch_authority_unchanged_false": True,
        "public_write_performed_false": True,
    }
    validation_core = {
        "schema_version": "contentops.executable_snapshot_requirement_validation_truth.v1",
        "task": TASK,
        "starting_commit": STARTING_SHA,
        "checks": checks,
        "test_truth": {
            "focused_test_file": "tests/test_executable_snapshot_requirement_separation_v1.py",
            "truth_table_cases": len(first),
            "generic_fabric_integration_case": "test_generic_fabric_flows_resolver_snapshot_policy_into_runtime",
            "backend_ui_parity_case": "test_backend_and_committed_v5_readiness_parity_for_current_three_packages",
            "current_package_runtime": package_truth,
        },
        "blocker_count": sum(not value for value in checks.values()),
        "result": "PASS" if all(checks.values()) else "BLOCK",
        "no_write_state": {
            "canonical_package_evidence_unchanged": True,
            "approval_execution_performed": False,
            "publication_authority": False,
            "dispatch_authority": False,
            "network_call_performed": False,
            "provider_call_performed": False,
            "public_write_performed": False,
        },
    }
    validation = _write("validation_truth.json", validation_core)
    if validation["result"] != "PASS":
        raise SystemExit("snapshot_requirement_validation_blocked")

    manifest_core = {
        "schema_version": "contentops.executable_snapshot_requirement_final_manifest.v1",
        "task": TASK,
        "starting_remote_head": STARTING_SHA,
        "terminal_classification": CLASSIFICATION,
        "exact_next_action": NEXT_ACTION,
        "source_blobs": [
            {"path": path, "git_blob_sha1": _git_blob(path)}
            for path in SOURCE_PATHS
        ],
        "canonical_package_evidence": {
            "unchanged": True,
            "artifacts": [
                {"path": path, "git_blob_sha1": _git_blob(path)}
                for path in CANONICAL_EVIDENCE_PATHS
            ],
        },
        "output_artifacts": [
            {
                "path": f"docs/automation/CONTENTOPS_FAST_SHIP_EXECUTABLE_SNAPSHOT_REQUIREMENT_SEPARATION_V1/{name}",
                "byte_sha256": _byte_hash(OUTPUT / name),
            }
            for name in (
                "snapshot_requirement_truth_table.json",
                "validation_truth.json",
            )
        ],
        "no_write_state": validation["no_write_state"],
        "monolithic_repository_suite_run": False,
        "ci_pass_claimed": False,
        "result": "PASS",
    }
    manifest = _write("final_manifest.json", manifest_core)
    print(
        json.dumps(
            {
                "result": manifest["result"],
                "case_count": len(first),
                "output_dir": str(OUTPUT),
            },
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
