from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from live_contentops.decision_editorial_feedback_quality_pack_v1 import (
    MAIN_ARTIFACT_BYTES,
    MAIN_ARTIFACT_FILE_SHA256,
    MAIN_PACK_SHA256,
    SCHEMA_VERSION,
    build_decision_editorial_feedback_quality_pack,
    pack_sha256,
    verify_decision_editorial_feedback_quality_pack,
)


ROOT = Path(__file__).resolve().parents[1]
MAIN_CURRENT = (
    ROOT / "tests/fixtures/decision_evidence_prioritization_pack_current_v1.json"
)
MAIN_CLEAN = (
    ROOT
    / "tests/fixtures/decision_evidence_prioritization_pack_clean_synthetic_v1.json"
)
ADJ_RECEIPTS = (
    ROOT / "tests/fixtures/editorial_adjudication_prioritization_pack_receipts_v1.json"
)
TRACE_RECEIPTS = (
    ROOT / "tests/fixtures/editorial_traceability_quality_pack_receipts_v1.json"
)
CASES = ROOT / "tests/fixtures/decision_editorial_feedback_quality_pack_cases_v1.json"
RECEIPTS = (
    ROOT / "tests/fixtures/decision_editorial_feedback_quality_pack_receipts_v1.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _current():
    return deepcopy(_load(MAIN_CURRENT))


def _clean():
    return deepcopy(_load(MAIN_CLEAN))


def _adj(name="exact_merged_main"):
    return deepcopy(_load(ADJ_RECEIPTS)["cases"][name])


def _trace(name="exact_merged_current"):
    return deepcopy(_load(TRACE_RECEIPTS)["cases"][name])


def _trim_clean():
    main = _clean()
    main["decision_candidates"] = [
        row
        for row in main["decision_candidates"]
        if row["candidate_id"] == "decision:replay-a"
    ]
    main["abstention_ledger"] = []
    main["core_admission"]["candidate_ids"] = ["decision:replay-a"]
    main["core_admission"]["count"] = 1
    main["editorial_admission"]["candidate_ids"] = ["decision:replay-a"]
    main["editorial_admission"]["count"] = 1
    main["outcome_links"] = [
        row for row in main["outcome_links"] if row["claim_id"] == "replay-a"
    ]
    main["pack_sha256"] = None
    main["pack_sha256"] = hashlib.sha256(
        json.dumps(
            {k: v for k, v in main.items() if k != "pack_sha256"},
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    return main


def _build(
    main=None,
    adj_name="exact_merged_main",
    trace_name="exact_merged_current",
    artifact=False,
):
    return build_decision_editorial_feedback_quality_pack(
        main or _current(),
        _adj(adj_name),
        traceability_pack=_trace(trace_name),
        artifact_bytes=MAIN_CURRENT.read_bytes() if artifact else None,
    )


def test_exact_main_artifact_and_goal_parent_hashes_bind():
    raw = MAIN_CURRENT.read_bytes()
    assert len(raw) == MAIN_ARTIFACT_BYTES
    assert hashlib.sha256(raw).hexdigest() == MAIN_ARTIFACT_FILE_SHA256
    assert _current()["pack_sha256"] == MAIN_PACK_SHA256
    pack = _build(artifact=True)
    assert pack["schema_version"] == SCHEMA_VERSION
    assert pack["artifact"]["status"] == "SEALED_MATCH"
    assert pack["parent_bindings"]["goal13_main_pack_sha256"] == MAIN_PACK_SHA256
    assert pack["parent_bindings"]["goal13_contentops_pack_sha256"]


def test_all_main_candidates_have_bidirectional_feedback():
    pack = _build(artifact=True)
    assert len(pack["candidate_feedback"]) == len(_current()["decision_candidates"])
    assert {row["claim_id"] for row in pack["candidate_feedback"]} == {
        row["candidate_id"].removeprefix("decision:")
        for row in _current()["decision_candidates"]
    }
    for row in pack["candidate_feedback"]:
        assert row["source_hashes"]
        assert row["main_source_hashes"]
        assert row["contentops_source_hashes"]
        assert row["duplicate_lineage"]
        assert row["authority"] is False


def test_agreement_disagreement_and_authority_boundaries_are_explicit():
    pack = _build()
    assert pack["feedback_disagreements"]
    assert any(
        "DECISION_REASON_DISAGREEMENT" in row["disagreement_reasons"]
        for row in pack["feedback_disagreements"]
    )
    assert all(
        row["main_decision"]
        in {"CORE_ADMITTED", "EDITORIAL_CONTEXT", "ABSTAINED", "QUARANTINED"}
        for row in pack["candidate_feedback"]
    )
    assert pack["outcome_boundary_map"]["performance_claims_created"] is False
    assert pack["outcome_boundary_map"]["forecast_claims_created"] is False


def test_quality_matrix_has_bounded_integer_counts_and_missingness():
    pack = _build()
    assert {row["component"] for row in pack["editorial_quality_matrix"]} == {
        "source_coverage",
        "lineage_completeness",
        "contradiction_handling",
        "abstention_fidelity",
        "exact_proxy_separation",
        "outcome_state_fidelity",
        "derivative_consistency",
        "destination_shadow_consistency",
    }
    for row in pack["editorial_quality_matrix"]:
        assert row["count"] is None or isinstance(row["count"], int)
        assert row["state"] in {"AVAILABLE", "NOT_COMPARABLE"}
        if row["count"] is None:
            assert row["missingness_reason"]


def test_traceability_maps_have_no_orphans_on_synthetic_complete_cycle():
    pack = _build(_trim_clean(), "synthetic_complete", "synthetic_complete")
    assert pack["classification"] == "SHADOW_CONFIRMED"
    assert pack["section_traceability"]["orphan_claim_ids"] == []
    assert pack["eight_derivative_traceability"]["orphan_claim_ids"] == []
    assert pack["quality_counts"]["derivative_count"] == 8
    assert len(pack["destination_shadow_traceability"]["destinations"]) == 8
    assert verify_decision_editorial_feedback_quality_pack(pack)


def test_current_real_is_not_verified_and_quarantines_remain_auditable():
    pack = _build(artifact=True)
    assert pack["classification"] == "NOT_VERIFIED"
    assert (
        "current-real-not-verified"
        in pack["abstention_quarantine_ledger"]["abstained_claim_ids"]
    )
    assert set(pack["abstention_quarantine_ledger"]["quarantined_claim_ids"]) == {
        "replay-contradiction-a",
        "replay-contradiction-b",
    }
    contradiction = [
        row
        for row in pack["candidate_feedback"]
        if row["claim_id"].startswith("replay-contradiction")
    ]
    assert {item for row in contradiction for item in row["source_hashes"]} >= {
        "a" * 64,
        "b" * 64,
    }


@pytest.mark.parametrize(
    "kind",
    [
        "missing_candidate",
        "orphan_draft_section",
        "orphan_derivative",
        "duplicate_payload",
        "contradiction_mismatch",
        "proxy_promotion",
        "stale",
        "future",
        "source_head_mismatch",
        "pack_hash_mismatch",
        "tampered",
        "secret",
        "rights",
        "authority",
        "unknown_write",
    ],
)
def test_feedback_blocker_matrix(kind: str):
    main = _current()
    adj = _adj()
    trace = (
        _trace("synthetic_complete")
        if kind in {"orphan_derivative", "duplicate_payload"}
        else _trace()
    )
    if kind == "missing_candidate":
        main["decision_candidates"] = main["decision_candidates"][:-1]
    elif kind == "orphan_draft_section":
        trace["claim_to_editorial"]["draft_sections"].append(
            {
                "section_id": "orphan",
                "claim_ids": ["missing"],
                "source_hashes": ["a" * 64],
                "evidence_hashes": ["b" * 64],
            }
        )
    elif kind == "orphan_derivative":
        trace["claim_to_derivative"]["packages"][0]["claim_ids"] = ["missing"]
    elif kind == "duplicate_payload":
        trace["claim_to_derivative"]["packages"][1]["payload_sha256"] = trace[
            "claim_to_derivative"
        ]["packages"][0]["payload_sha256"]
    elif kind == "contradiction_mismatch":
        adj["candidate_adjudications"][2]["decision"] = "PRIORITIZED"
    elif kind == "proxy_promotion":
        adj["candidate_adjudications"][-1]["decision"] = "PRIORITIZED"
    elif kind == "stale":
        main["decision_candidates"][1]["freshness"]["state"] = "STALE"
    elif kind == "future":
        main["decision_candidates"][1]["pit_state"] = "PIT_INVALID_FUTURE_KNOWN_AT"
    elif kind == "source_head_mismatch":
        main["parent_bindings"]["main_source"]["head"] = "0" * 40
    elif kind == "pack_hash_mismatch":
        main["pack_sha256"] = "0" * 64
    elif kind == "tampered":
        main["decision_candidates"][0]["claim_identity"]["claim_text"] = "tampered"
    elif kind == "secret":
        main["api_key"] = "Bearer do-not-export-this-value"
    elif kind == "rights":
        main["decision_candidates"][1]["rights"]["internal_analysis_allowed"] = False
    elif kind == "authority":
        main["authority_flags"]["decision_authority"] = True
    elif kind == "unknown_write":
        main["decision_candidates"][0]["unknown_write"] = True
    pack = build_decision_editorial_feedback_quality_pack(
        main, adj, traceability_pack=trace
    )
    assert pack["status"] != "SHADOW_CONFIRMED" or kind == "missing_candidate"
    assert pack["blockers"] or pack["feedback_disagreements"]


def test_outcome_pending_layers_and_interruption_resume_are_preserved():
    pack = _build(_trim_clean(), "interruption_resume", "interruption_resume")
    assert pack["classification"] == "SHADOW_CONFIRMED"
    assert (
        pack["destination_shadow_traceability"]["interruption_resume"]
        == "RESUMABLE_WITHOUT_SEMANTIC_RERUN"
    )
    states = {row["outcome_state"] for row in pack["outcome_boundary_map"]["slots"]}
    assert states <= {"OUTCOME_PENDING", "NOT_COMPARABLE", "NOT_VERIFIED", "OBSERVED"}


def test_repeated_pack_is_deterministic_and_tamper_evident():
    first = _build(_trim_clean(), "synthetic_complete", "synthetic_complete")
    second = _build(_trim_clean(), "synthetic_complete", "synthetic_complete")
    assert first == second
    assert first["pack_sha256"] == pack_sha256(first)
    broken = deepcopy(first)
    broken["quality_counts"]["agreement_count"] = 99
    assert verify_decision_editorial_feedback_quality_pack(broken) is False


def test_fixture_receipts_are_self_hashed_and_deep_matrix_is_present():
    cases = _load(CASES)
    receipts = _load(RECEIPTS)
    assert (
        receipts["schema_version"]
        == "contentops.decision_editorial_feedback_quality_pack.receipts.v1"
    )
    required = {
        "exact_merged_main",
        "fixture_only_fallback",
        "all_candidates_accounted",
        "missing_candidate",
        "orphan_draft_section",
        "orphan_derivative",
        "duplicate_payload",
        "contradiction_mismatch",
        "proxy_promotion",
        "stale",
        "future",
        "source_head_mismatch",
        "pack_hash_mismatch",
        "tampered",
        "secret",
        "rights",
        "authority",
        "unknown_write",
        "current_real_not_verified",
        "complete_synthetic",
        "interruption_resume",
        "deterministic_repeat",
    }
    assert set(cases["cases"]) >= required
    for name, pack in receipts["cases"].items():
        assert pack["pack_sha256"] == pack_sha256(pack)
        assert pack["schema_version"] == SCHEMA_VERSION
