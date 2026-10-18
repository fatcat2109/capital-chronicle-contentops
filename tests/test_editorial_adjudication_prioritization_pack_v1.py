from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
from live_contentops.editorial_adjudication_prioritization_pack_v1 import (
    MAIN_ARTIFACT_BYTES,
    MAIN_ARTIFACT_FILE_SHA256,
    MAIN_EVALUATION_SHA256,
    SCHEMA_VERSION,
    build_editorial_adjudication_prioritization_pack,
    pack_sha256,
    verify_editorial_adjudication_prioritization_pack,
)


ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "tests/fixtures/multi_window_outcome_evaluation_current_v1.json"
CLEAN = ROOT / "tests/fixtures/multi_window_outcome_evaluation_clean_synthetic_v1.json"
CASES = ROOT / "tests/fixtures/editorial_adjudication_prioritization_pack_cases_v1.json"
RECEIPTS = ROOT / "tests/fixtures/editorial_adjudication_prioritization_pack_receipts_v1.json"
TRACE_RECEIPTS = ROOT / "tests/fixtures/editorial_traceability_quality_pack_receipts_v1.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _trace(name: str) -> dict:
    return deepcopy(_load(TRACE_RECEIPTS)["cases"][name])


def _pack(decision: dict | None = None, trace_name: str = "exact_merged_current", *, exact: bool = False) -> dict:
    decision = deepcopy(decision or _load(CURRENT))
    trace = _trace(trace_name)
    return build_editorial_adjudication_prioritization_pack(
        decision,
        trace,
        artifact_bytes=CURRENT.read_bytes() if exact else None,
    )


def _reseal(value: dict) -> dict:
    value["evaluation_sha256"] = None
    value["evaluation_sha256"] = hashlib.sha256(
        json.dumps(
            {key: item for key, item in value.items() if key != "evaluation_sha256"},
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return value


def test_exact_main_artifact_and_parent_bindings_are_sealed():
    raw = CURRENT.read_bytes()
    assert len(raw) == MAIN_ARTIFACT_BYTES
    assert hashlib.sha256(raw).hexdigest() == MAIN_ARTIFACT_FILE_SHA256
    decision = _load(CURRENT)
    assert decision["evaluation_sha256"] == MAIN_EVALUATION_SHA256
    pack = _pack(exact=True)
    assert pack["schema_version"] == SCHEMA_VERSION
    assert pack["source_state"] == "MERGED_MAIN_ARCHIVE"
    assert pack["artifact"]["status"] == "SEALED_MATCH"
    assert pack["main_source"]["requested_contract_schema"] == "CapitalChronicleDecisionEvidencePrioritizationPackV1"
    assert pack["main_source"]["observed_contract_schema"] == "CapitalChronicleOutcomeEvaluationBundleV1"
    assert pack["parent_bindings"]["goal9_reconciliation_sha256"]
    assert pack["parent_bindings"]["goal10_bundle_sha256"]
    assert pack["parent_bindings"]["goal11_quality_ledger_sha256"]
    assert pack["parent_bindings"]["goal12_traceability_pack_sha256"]


def test_every_candidate_has_adjudication_and_lineage():
    pack = _pack(exact=True)
    assert len(pack["candidate_adjudications"]) == 5
    assert {row["decision"] for row in pack["candidate_adjudications"]} == {
        "PRIORITIZED",
        "CONTEXT_ONLY",
        "ABSTAINED",
        "QUARANTINED",
    }
    for row in pack["candidate_adjudications"]:
        assert row["source_hashes"]
        assert row["evidence_hashes"]
        assert row["duplicate_lineage"]
        assert row["exact_proxy_context"]
        assert "pit_state" in row["pit_freshness_rights"]
        assert "freshness" in row["pit_freshness_rights"]
        assert "rights" in row["pit_freshness_rights"]
        assert row["authority"] is False


def test_policy_decisions_preserve_current_proxy_contradiction_and_replay_boundaries():
    pack = _pack()
    by_id = {row["claim_id"]: row for row in pack["candidate_adjudications"]}
    assert by_id["replay-a"]["decision"] == "PRIORITIZED"
    assert by_id["proxy-context"]["decision"] == "CONTEXT_ONLY"
    assert by_id["proxy-context"]["basis_risk_labels"]
    assert by_id["current-real-not-verified"]["decision"] == "ABSTAINED"
    assert by_id["current-real-not-verified"]["decision_reason"] == "CURRENT_REAL_NOT_VERIFIED"
    assert by_id["replay-contradiction-a"]["decision"] == "QUARANTINED"
    assert by_id["replay-contradiction-b"]["decision"] == "QUARANTINED"
    assert by_id["replay-contradiction-a"]["source_hashes"] == ["a" * 64]
    assert by_id["replay-contradiction-b"]["source_hashes"] == ["b" * 64]


def test_priority_matrix_is_integer_bounded_metadata_without_aggregate_score():
    pack = _pack()
    matrix = pack["editorial_priority_matrix"]
    assert matrix["aggregate_score_created"] is False
    assert matrix["audience_score_created"] is False
    assert matrix["forecast_score_created"] is False
    for row in matrix["rows"]:
        for component in row["components"].values():
            value = component["value"]
            assert value is None or (isinstance(value, int) and not isinstance(value, bool))
            assert component["state"] in {"OBSERVED", "NOT_COMPARABLE"}


def test_outcome_boundary_preserves_layers_and_missingness():
    pack = _pack()
    boundary = pack["outcome_boundary_map"]
    assert set(boundary["proof_layers_preserved"]) >= {
        "RETROSPECTIVE_REPLAY",
        "PROSPECTIVE_NATURAL_OBSERVATION",
        "PAPER_SIMULATION",
        "RUNTIME_PROVEN",
        "REALIZED_EXECUTION",
        "PROXY_CONTEXT",
    }
    assert set(row["outcome_state"] for row in boundary["slots"]) <= {
        "OUTCOME_PENDING",
        "NOT_COMPARABLE",
        "NOT_VERIFIED",
        "OBSERVED",
    }
    assert boundary["performance_claims_created"] is False
    assert boundary["forecast_claims_created"] is False
    assert boundary["runtime_claims_created"] is False
    assert boundary["realized_claims_created"] is False


def test_current_real_stays_abstained_and_exact_clean_cycle_is_shadow_confirmed():
    current = _pack(exact=True)
    assert current["classification"] == "NOT_VERIFIED"
    assert current["proof_axes"]["runtime_proven"] is False
    clean = _pack(_load(CLEAN), "synthetic_complete")
    assert clean["classification"] == "SHADOW_CONFIRMED"
    assert len(clean["claim_to_eight_derivatives"]) == 8
    assert {row["destination"] for row in clean["claim_to_eight_derivatives"]} == set(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    assert clean["destination_shadow"]["public_write_performed"] is False
    assert verify_editorial_adjudication_prioritization_pack(clean)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("source_head_mismatch", "SOURCE_HEAD_MISMATCH"),
        ("evaluation_hash_mismatch", "PACKET_HASH_MISMATCH"),
        ("tampered", "PACKET_HASH_MISMATCH"),
        ("secret_marker", "NOT_VERIFIED"),
        ("rights_invalid", "NOT_VERIFIED"),
        ("authority_flag", "AUTHORITY_FLAG"),
        ("unknown_write", "UNKNOWN_WRITE"),
        ("stale", "STALE"),
        ("future", "STALE"),
        ("horizon_unit_mismatch", "NOT_VERIFIED"),
    ],
)
def test_fail_closed_matrix(name: str, expected: str):
    decision = _load(CURRENT)
    if name == "source_head_mismatch":
        decision["parent_bindings"]["main_source"]["head"] = "0" * 40
    elif name == "evaluation_hash_mismatch":
        decision["evaluation_sha256"] = "0" * 64
    elif name == "tampered":
        decision["claim_evaluations"][1]["claim_id"] = "tampered"
    elif name == "secret_marker":
        decision["api_key"] = "Bearer do-not-export-this-value"
    elif name == "rights_invalid":
        decision["claim_evaluations"][1]["evaluation_eligibility"]["blockers"].append("rights_invalid")
    elif name == "authority_flag":
        decision["authority_flags"]["score_authority"] = True
    elif name == "unknown_write":
        decision["claim_evaluations"][0]["unknown_write"] = True
    elif name == "stale":
        decision["claim_evaluations"][1]["evaluation_eligibility"]["blockers"].append("FRESHNESS_STALE_REJECTED")
    elif name == "future":
        decision["claim_evaluations"][1]["evaluation_eligibility"]["blockers"].append("FUTURE_KNOWN_AT_REJECTED")
    elif name == "horizon_unit_mismatch":
        decision["claim_evaluations"][1]["evaluation_eligibility"]["blockers"].append("HORIZON_UNIT_MISMATCH")
    if name not in {"evaluation_hash_mismatch", "tampered"}:
        _reseal(decision)
    pack = _pack(decision)
    assert pack["classification"] == expected
    assert pack["status"] != "SHADOW_CONFIRMED"
    assert pack["blockers"]


def test_draft_article_derivative_mapping_retains_claim_hashes_and_interruption():
    pack = _pack(_load(CLEAN), "interruption_resume")
    assert pack["classification"] == "SHADOW_CONFIRMED"
    assert pack["claim_to_canonical_article"]["claim_ids"] == ["replay-a"]
    assert pack["claim_to_canonical_article"]["source_hashes"]
    for section in pack["claim_to_draft_sections"]:
        assert section["source_hashes"]
        assert section["evidence_hashes"]
    for package in pack["claim_to_eight_derivatives"]:
        assert package["claim_ids"] == ["replay-a"]
        assert package["source_hashes"]
        assert package["evidence_hashes"]
    assert pack["destination_shadow"]["interruption_resume"] == "RESUMABLE_WITHOUT_SEMANTIC_RERUN"


def test_repeated_pack_is_deterministic_and_tamper_evident():
    first = _pack(_load(CLEAN), "synthetic_complete")
    second = _pack(_load(CLEAN), "synthetic_complete")
    assert first == second
    assert first["pack_sha256"] == pack_sha256(first)
    tampered = deepcopy(first)
    tampered["quality_counts"]["counts"]["prioritized_count"] = 99
    assert verify_editorial_adjudication_prioritization_pack(tampered) is False


def test_fixture_matrix_and_receipts_round_trip_exactly():
    cases = _load(CASES)
    receipts = _load(RECEIPTS)
    assert receipts["schema_version"] == "contentops.editorial_adjudication_prioritization_pack.receipts.v1"
    required = {
        "exact_merged_main",
        "synthetic_complete",
        "current_real_not_verified",
        "five_candidate_mixed_windows",
        "duplicate_lineage",
        "contradiction_quarantine",
        "proxy_only_context",
        "horizon_unit_mismatch",
        "stale",
        "future",
        "source_head_mismatch",
        "evaluation_hash_mismatch",
        "tampered",
        "secret_marker",
        "rights_invalid",
        "authority_flag",
        "unknown_write",
        "eight_derivative_shadow",
        "interruption_resume",
        "deterministic_repeat",
    }
    assert set(cases["cases"]) >= required
    for name, expected in receipts["cases"].items():
        assert expected["pack_sha256"] == pack_sha256(expected)
        assert expected["classification"] == cases["cases"][name]["expected_classification"]
