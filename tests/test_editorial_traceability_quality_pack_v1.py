from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
from live_contentops.editorial_traceability_quality_pack_v1 import (
    MAIN_LEDGER_BYTES,
    MAIN_LEDGER_FILE_SHA256,
    MAIN_LEDGER_SHA256,
    build_editorial_traceability_quality_pack,
    pack_sha256,
    verify_editorial_traceability_quality_pack,
)


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "tests/fixtures/multi_window_quality_replay_ledger_current_v1.json"
LEDGER_CASES = ROOT / "tests/fixtures/multi_window_quality_replay_ledger_cases_v1.json"
V1_RECEIPTS = ROOT / "tests/fixtures/multi_window_newsroom_cycle_receipts_v1.json"
V2_RECEIPTS = ROOT / "tests/fixtures/multi_window_newsroom_cycle_v2_receipts_v1.json"
PACK_CASES = ROOT / "tests/fixtures/editorial_traceability_quality_pack_cases_v1.json"
PACK_RECEIPTS = ROOT / "tests/fixtures/editorial_traceability_quality_pack_receipts_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ledger() -> dict:
    return _load(LEDGER)


def _v1(name: str = "healthy") -> dict:
    return deepcopy(_load(V1_RECEIPTS)["cases"][name])


def _v2(name: str = "healthy") -> dict:
    return deepcopy(_load(V2_RECEIPTS)["cases"][name])


def _packages(receipt: dict, *, count: int = 8) -> list[dict]:
    destinations = list(receipt.get("derivative_shadow", {}).get("destinations") or V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    return [
        {
            "destination": destination,
            "payload_sha256": f"{index + 1:064x}",
            "status": "SHADOW_READY",
            "public_write_performed": False,
        }
        for index, destination in enumerate(destinations[:count])
    ]


def _rehash(value: dict) -> dict:
    value["ledger_sha256"] = None
    value["ledger_sha256"] = hashlib.sha256(
        json.dumps(
            {key: item for key, item in value.items() if key != "ledger_sha256"},
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return value


def _complete_ledger() -> dict:
    ledger = _ledger()
    rows = [row for row in ledger["claim_ledger"] if row["claim_id"] == "replay-a"]
    ledger["claim_ledger"] = rows
    for stage in ledger["replay_matrix"]:
        stage["claim_ids"] = [] if stage["stage_id"] == "CONTRADICTION_QUARANTINED" else ["replay-a"]
        stage["window_ids"] = [] if not stage["claim_ids"] else ["RECENT_REPLAY"]
        stage["eligible_count"] = len(stage["claim_ids"])
        stage["blocked_count"] = 0
        stage["evidence_hashes"] = rows[0]["evidence_hashes"] if stage["claim_ids"] else []
        stage["unsupported_dimensions"] = rows[0]["unsupported_dimensions"] if stage["claim_ids"] else []
    ledger["outcome_slots"] = [slot for slot in ledger["outcome_slots"] if slot["claim_id"] == "replay-a"]
    ledger["quality_summary"] = {
        "classification": "NONE",
        "quality_state": "CLEAR",
        "reasons": [],
        "exact_blocker": None,
        "exact_next_action": "Continue deterministic review; no runtime or publication promotion.",
        "counts": {
            "window_count": 3,
            "window_claim_counts": {"CURRENT_REAL": 0, "RECENT_REPLAY": 1, "PROXY_CONTEXT": 0},
            "retained_claim_count": 1,
            "core_admitted_count": 1,
            "editorial_admitted_count": 1,
            "quarantined_count": 0,
            "excluded_count": 0,
            "duplicate_group_count": 1,
            "outcome_pending_count": 1,
        },
        "quality_class_counts": {"EXACT_CORE_ELIGIBLE": 1},
        "unsupported_dimensions": rows[0]["unsupported_dimensions"],
    }
    return _rehash(ledger)


def _build(
    ledger: dict | None = None,
    *,
    v1_name: str = "healthy",
    v2_name: str = "healthy",
    exact_artifact: bool = False,
    package_count: int = 8,
) -> dict:
    v2 = _v2(v2_name)
    return build_editorial_traceability_quality_pack(
        ledger or _ledger(),
        v2,
        newsroom_receipt_v1=_v1(v1_name),
        derivative_packages=_packages(v2, count=package_count),
        artifact_bytes=LEDGER.read_bytes() if exact_artifact else None,
    )


def test_exact_main_ledger_bytes_and_hash_are_bound():
    raw = LEDGER.read_bytes()
    assert len(raw) == MAIN_LEDGER_BYTES
    assert hashlib.sha256(raw).hexdigest() == MAIN_LEDGER_FILE_SHA256
    ledger = _ledger()
    assert ledger["ledger_sha256"] == MAIN_LEDGER_SHA256
    pack = _build(v1_name="current_real", v2_name="current_real", exact_artifact=True, package_count=0)
    assert pack["source_state"] == "MERGED_MAIN_ARCHIVE"
    assert pack["artifact"]["status"] == "SEALED_MATCH"
    assert pack["classification"] == "NOT_VERIFIED"
    assert pack["main_source"]["ledger_sha256"] == MAIN_LEDGER_SHA256


def test_synthetic_complete_ledger_reaches_shadow_pack_without_promotion():
    pack = _build(_complete_ledger())
    assert pack["classification"] == "SHADOW_CONFIRMED"
    assert pack["status"] == "SHADOW_CONFIRMED"
    assert pack["quality_counts"]["derivative_count"] == 8
    assert len(pack["claim_to_derivative"]["packages"]) == 8
    assert pack["proof_axes"]["runtime_proven"] is False
    assert pack["proof_axes"]["publicly_proven"] is False
    assert verify_editorial_traceability_quality_pack(pack)


def test_current_real_preserves_facts_and_abstains():
    pack = _build(v1_name="current_real", v2_name="current_real", exact_artifact=True, package_count=0)
    assert pack["classification"] == "NOT_VERIFIED"
    assert "current-real-not-verified" in pack["claim_to_editorial"]["abstained_claim_ids"]
    trace = next(row for row in pack["claim_traceability"] if row["claim_id"] == "current-real-not-verified")
    assert trace["decision"] == "ABSTAINED"
    assert trace["source_hashes"]
    assert "CURRENT_REAL_NOT_VERIFIED" in trace["decision_reasons"]
    assert pack["host_facts"]["current_real"]["store"]["integrity_check"] == "ok"


def test_replay_proxy_duplicate_and_contradiction_lineage_survive():
    pack = _build()
    replay = next(row for row in pack["claim_traceability"] if row["claim_id"] == "replay-a")
    proxy = next(row for row in pack["claim_traceability"] if row["claim_id"] == "proxy-context")
    contradiction = next(row for row in pack["claim_traceability"] if row["claim_id"] == "replay-contradiction-a")
    assert replay["decision"] == "SELECTED"
    assert replay["dedupe"]["duplicate_claim_ids"] == ["replay-a", "replay-duplicate"]
    assert proxy["decision"] == "CONTEXT_ONLY"
    assert proxy["exact_proxy_context"]["state"] == "PROXY"
    assert contradiction["decision"] == "QUARANTINED"
    assert contradiction["conflict_label"] == "CONFLICT_PRESENT"
    assert set(pack["claim_to_editorial"]["context_only_claim_ids"]) == {"proxy-context"}
    for row in pack["claim_to_editorial"]["draft_sections"]:
        assert row["source_hashes"]
        assert row["evidence_hashes"]


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("stale", "STALE"),
        ("future", "STALE"),
        ("source_head_mismatch", "SOURCE_HEAD_MISMATCH"),
        ("ledger_hash_mismatch", "PACKET_HASH_MISMATCH"),
        ("tampered", "PACKET_HASH_MISMATCH"),
        ("authority_flag", "AUTHORITY_FLAG"),
        ("unknown_write", "UNKNOWN_WRITE"),
        ("secret_marker", "NOT_VERIFIED"),
        ("rights_invalid", "NOT_VERIFIED"),
    ],
)
def test_fail_closed_quality_matrix(name: str, expected: str):
    cases = {
        "stale": lambda b: b["claim_ledger"][1]["freshness"].update({"state": "STALE"}),
        "future": lambda b: b["claim_ledger"][1].update({"pit_state": "PIT_INVALID_FUTURE_KNOWN_AT"}),
        "source_head_mismatch": lambda b: b["bundle_binding"]["main_source"].update({"head": "0" * 40}),
        "ledger_hash_mismatch": lambda b: b.update({"ledger_sha256": "0" * 64}),
        "tampered": lambda b: b["claim_ledger"][1].update({"claim": "tampered"}),
        "authority_flag": lambda b: b["authority_flags"].update({"decision_authority": True}),
        "unknown_write": lambda b: b["claim_ledger"][0].update({"unknown_write": True}),
        "secret_marker": lambda b: b.update({"api_key": "Bearer do-not-export-this-value"}),
        "rights_invalid": lambda b: b["claim_ledger"][1]["rights"].update({"internal_analysis_allowed": False}),
    }
    ledger = _ledger()
    cases[name](ledger)
    if name not in {"ledger_hash_mismatch", "tampered"}:
        _rehash(ledger)
    pack = _build(ledger, package_count=8)
    assert pack["classification"] == expected
    assert pack["status"] != "SHADOW_CONFIRMED"
    assert pack["blockers"]


def test_derivative_consistency_and_interruption_resume_are_preserved():
    bad = _build(_complete_ledger(), package_count=7)
    assert bad["classification"] == "NOT_VERIFIED"
    assert "derivative_count_or_destination_mismatch" in bad["blockers"]
    interrupted = _build(_complete_ledger(), v2_name="interruption_resume")
    assert interrupted["classification"] == "SHADOW_CONFIRMED"
    assert interrupted["claim_to_derivative"]["interruption_resume"] == "RESUMABLE_WITHOUT_SEMANTIC_RERUN"
    for package in interrupted["claim_to_derivative"]["packages"]:
        assert package["claim_ids"] == ["replay-a"]
        assert package["source_hashes"] == [
            "46b265fe695ffdac11ca77c9c8d10ddab405f9e47852a117c22db3f5aeb6a792",
            "d054ac8d439cfc69127eef58d7360c362fafeb8aa7b00caba05f061b3b61c870",
        ]


def test_outcomes_are_pending_or_not_comparable_and_never_performance_claims():
    pack = _build()
    assert all(row["outcome_status"] == "OUTCOME_PENDING" for row in pack["outcome_evaluation"]["claims"])
    assert all(row["evaluation_status"] == "NOT_COMPARABLE" for row in pack["outcome_evaluation"]["claims"])
    assert pack["outcome_evaluation"]["performance_claims_created"] is False
    assert pack["outcome_evaluation"]["forecast_claims_created"] is False
    assert pack["outcome_evaluation"]["runtime_claims_created"] is False
    assert pack["outcome_evaluation"]["public_claims_created"] is False


def test_pack_hash_is_repeated_deterministic_and_tamper_evident():
    first = _build(_complete_ledger())
    second = _build(_complete_ledger())
    assert first == second
    assert first["pack_sha256"] == pack_sha256(first)
    tampered = deepcopy(first)
    tampered["quality_counts"]["selected_count"] = 99
    assert verify_editorial_traceability_quality_pack(tampered) is False


def test_fixture_matrix_and_receipts_round_trip_exactly():
    cases = _load(PACK_CASES)
    receipts = _load(PACK_RECEIPTS)
    assert set(cases["cases"]) >= {
        "exact_merged_current",
        "synthetic_complete",
        "current_real_not_verified",
        "replay_proxy_context",
        "duplicate_collapse",
        "contradiction_quarantine",
        "stale",
        "future",
        "source_head_mismatch",
        "ledger_hash_mismatch",
        "tampered",
        "secret_marker",
        "rights_invalid",
        "authority_flag",
        "unknown_write",
        "eight_derivative_consistency",
        "interruption_resume",
    }
    assert receipts["schema_version"] == "contentops.editorial_traceability_quality_pack.receipts.v1"
    for name, expected in receipts["cases"].items():
        assert expected["pack_sha256"] == pack_sha256(expected)
        assert expected["classification"] == cases["cases"][name]["expected_classification"]
        spec = cases["cases"][name]
        v2 = _v2(spec.get("v2_name", "healthy"))
        actual = build_editorial_traceability_quality_pack(
            spec["ledger"],
            v2,
            newsroom_receipt_v1=_v1(spec.get("v1_name", "healthy")),
            derivative_packages=_packages(v2, count=spec.get("package_count", 8)),
            artifact_bytes=LEDGER.read_bytes() if spec.get("exact_artifact") else None,
        )
        assert actual == expected
