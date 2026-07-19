from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess

import pytest

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import schema_aware_evidence_extraction_v1 as extraction


ROOT = Path(__file__).resolve().parents[1]
CUTOFF = "2026-07-19T12:00:00Z"
REPOSITORY = "fatcat2109/Headline-Raw-data-json"
NEWSROOM_PATH = "docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json"
BLS_PATH = "data/archive/official_sources/bls_public_data_api/fixture/raw_response.json"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def _repo(tmp_path: Path, path: str, artifact: dict) -> tuple[Path, str, bytes]:
    repo = tmp_path / ("repo-" + str(len(list(tmp_path.iterdir()))))
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "Tests")
    target = repo / path
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(artifact, sort_keys=True), encoding="utf-8")
    _git(repo, "add", path)
    _git(repo, "commit", "-m", "fixture")
    commit = _git(repo, "rev-parse", "HEAD")
    consumed = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"], check=True, capture_output=True).stdout
    return repo, commit, consumed


def _candidate(candidate_id: str, *, allowed: bool, relationship: str = "new_phase") -> dict:
    return {
        "candidate_id": candidate_id,
        "evidence_hash": ("a" if allowed else "b") * 64,
        "authority": {"story_decision": "ALLOW" if allowed else "NOT_GRANTED"},
        "claim_permissions": {"decision": "ALLOW" if allowed else "BLOCK", "reporting_allowed": allowed},
        "event_time_utc": "2026-07-19T00:00:00Z",
        "known_at_utc": "2026-07-19T01:00:00Z",
        "source_packet_id": "packet:" + candidate_id,
        "source_packet_logical_hash": ("c" if allowed else "d") * 64,
        "relationship": relationship,
        "eligible": allowed,
        "blockers": [] if allowed else ["story_scoped_reporting_authority_required"],
        "update_chain_id": "chain:" + candidate_id,
        "update_chain_continuity": allowed,
        "distinct_new_event_ref": "event:" + candidate_id if allowed else None,
        "numeric_claims": [],
        "source_documents": [],
    }


def _newsroom_context(tmp_path: Path, rows: list[dict]):
    artifact = {
        "schema_version": "capital_chronicle.newsroom_candidate_pool.v1",
        "producer_version": "newsroom_candidate_pool_v1.1.0",
        "pool_id": "pool:test",
        "cutoff_time_utc": CUTOFF,
        "eligible_candidates": [row for row in rows if row["eligible"]],
        "rejected_candidates": [row for row in rows if not row["eligible"]],
    }
    artifact["logical_hash"] = contracts.logical_hash({key: value for key, value in artifact.items() if key not in {"logical_hash", "pool_id"}})
    repo, commit, consumed = _repo(tmp_path, NEWSROOM_PATH, artifact)
    verifier = adapters.load_trusted_verifier_registry(ROOT)
    receipt = adapters.build_local_git_artifact_receipt(
        git_repository=repo, repository_identity=REPOSITORY, branch="main", commit=commit,
        artifact_path=NEWSROOM_PATH, artifact_schema_version=artifact["schema_version"],
        producer_version=artifact["producer_version"], artifact_cutoff_utc=CUTOFF,
        evidence_refs=(), source_authority_class="official_public_data", registry=verifier,
        verification_time_utc=CUTOFF, branch_authority_ref="refs/heads/main",
    )
    extractor_registry = extraction.load_extractor_registry(ROOT)
    extracted = [extraction.extract_artifact_evidence(
        consumed, receipt=receipt, registry=extractor_registry,
        extractor_id="contentops.newsroom_candidate_extractor", extractor_version="v1",
        selector={"candidate_id": row["candidate_id"]},
        feature_targets=("authority_readiness", "evidence_completeness"),
        decision_cutoff_utc=CUTOFF,
    ) for row in rows]
    records = tuple(value[0] for value in extracted)
    values = tuple(item for value in extracted for item in value[1])
    context = contracts.EvidenceDecisionContextV1(verifier, (receipt,), CUTOFF, extractor_registry, records, values)
    assert not context.validate()
    return consumed, receipt, context, records


def _bls_context(tmp_path: Path):
    artifact = {"status": "REQUEST_SUCCEEDED", "Results": {"series": [{
        "seriesID": "SERIES", "data": [
            {"year": "2026", "period": "M01", "periodName": "January", "value": "1"},
            {"year": "2026", "period": "M02", "periodName": "February", "value": "2"},
        ],
    }]}}
    repo, commit, consumed = _repo(tmp_path, BLS_PATH, artifact)
    verifier = adapters.load_trusted_verifier_registry(ROOT)
    extractor_registry = extraction.load_extractor_registry(ROOT)
    extractor = extractor_registry.resolve("contentops.bls_series_observation_extractor", "v1")
    receipt = adapters.build_local_git_artifact_receipt(
        git_repository=repo, repository_identity=REPOSITORY, branch="main", commit=commit,
        artifact_path=BLS_PATH, artifact_schema_version="external.bls_public_data_response.v1",
        producer_version=extractor.shape_contract_id, artifact_cutoff_utc=CUTOFF,
        evidence_refs=(), source_authority_class="official_public_data", registry=verifier,
        verification_time_utc=CUTOFF, branch_authority_ref="refs/heads/main",
    )
    extracted = [extraction.extract_artifact_evidence(
        consumed, receipt=receipt, registry=extractor_registry,
        extractor_id=extractor.extractor_id, extractor_version="v1",
        selector={"series_id": "SERIES", "year": "2026", "period": period},
        feature_targets=("evidence_completeness",), decision_cutoff_utc=CUTOFF,
    ) for period in ("M01", "M02")]
    records = tuple(value[0] for value in extracted)
    values = tuple(item for value in extracted for item in value[1])
    context = contracts.EvidenceDecisionContextV1(verifier, (receipt,), CUTOFF, extractor_registry, records, values)
    bindings = tuple(adapters.build_receipt_backed_evidence_binding(context, evidence_ref=row.evidence_ref) for row in records)
    return context, records, values, bindings


def _learning_candidate(records, bindings, feature_refs, raw_value=1.0):
    return core.LearningCandidateV2(
        candidate_id="candidate:aggregation", story_id="story:aggregation", cluster_id="cluster:aggregation",
        update_chain_id="chain:aggregation", source_relationship=contracts.EventRelationship.INITIAL_EVENT,
        evidence_state="EXTRACTED", authority_state="AUTHORITY_READY_REPORTING_BLOCKED",
        authority_ready=True, reporting_allowed=False, authority_blockers=(), history_identity_match=False,
        feature_inputs=(core.FeatureInputV1(
            "evidence_completeness", True, contracts.AvailabilityState.AVAILABLE, raw_value,
            evidence_refs=tuple(feature_refs), evidence_scope=contracts.EvidenceScope.FEATURE_SPECIFIC,
        ),),
        evidence_refs=tuple(row.evidence_ref for row in records), governed_evidence_bindings=tuple(bindings),
    )


def test_rejected_newsroom_candidate_and_reporting_permission_cannot_be_upgraded(tmp_path):
    consumed, receipt, context, records = _newsroom_context(tmp_path, [_candidate("rejected", allowed=False)])
    record = records[0]
    assert (record.authority_state, record.permission_state, record.qualification_status) == (
        "BLOCKED", "REPORTING_NOT_ALLOWED", "NOT_QUALIFYING_GOVERNED"
    )
    assert record.evidence_roles == (contracts.EvidenceRole.FEATURE_SUPPORT,)
    with pytest.raises(ValueError, match="caller_authority_upgrade_forbidden"):
        extraction.extract_artifact_evidence(
            consumed, receipt=receipt, registry=context.extractor_registry,
            extractor_id=record.extractor_id, extractor_version=record.extractor_version,
            selector={"candidate_id": "rejected"}, feature_targets=("authority_readiness",),
            decision_cutoff_utc=CUTOFF, authority_state="VERIFIED_GOVERNED",
        )
    with pytest.raises(ValueError, match="caller_permission_upgrade_forbidden"):
        extraction.extract_artifact_evidence(
            consumed, receipt=receipt, registry=context.extractor_registry,
            extractor_id=record.extractor_id, extractor_version=record.extractor_version,
            selector={"candidate_id": "rejected"}, feature_targets=("authority_readiness",),
            decision_cutoff_utc=CUTOFF, permission_state="REPORTING_ALLOWED",
        )


def test_newsroom_semantic_role_is_derived_and_caller_cannot_introduce_another(tmp_path):
    consumed, receipt, context, records = _newsroom_context(tmp_path, [_candidate("allowed-role", allowed=True)])
    assert records[0].evidence_roles == (
        contracts.EvidenceRole.FEATURE_SUPPORT,
        contracts.EvidenceRole.NEW_PHASE,
    )
    with pytest.raises(ValueError, match="caller_evidence_role_addition_forbidden"):
        extraction.extract_artifact_evidence(
            consumed, receipt=receipt, registry=context.extractor_registry,
            extractor_id=records[0].extractor_id, extractor_version=records[0].extractor_version,
            selector={"candidate_id": "allowed-role"}, feature_targets=("authority_readiness",),
            decision_cutoff_utc=CUTOFF,
            evidence_roles=(contracts.EvidenceRole.FEATURE_SUPPORT, contracts.EvidenceRole.MATERIAL_DELTA),
        )
def test_external_context_only_cannot_become_public_claim_allowed(tmp_path):
    context, records, _, _ = _bls_context(tmp_path)
    record = records[0]
    assert record.permission_state == "CONTEXT_ONLY" and record.evidence_roles == (contracts.EvidenceRole.FEATURE_SUPPORT,)
    with pytest.raises(ValueError, match="binding_permission_upgrade_forbidden"):
        adapters.build_receipt_backed_evidence_binding(
            context, evidence_ref=record.evidence_ref, permission_state="PUBLIC_CLAIM_ALLOWED"
        )


@pytest.mark.parametrize("role", [contracts.EvidenceRole.NEW_PHASE, contracts.EvidenceRole.MATERIAL_DELTA])
def test_caller_cannot_add_semantic_role(tmp_path, role):
    context, records, _, _ = _bls_context(tmp_path)
    with pytest.raises(ValueError, match="binding_role_addition_forbidden"):
        adapters.build_receipt_backed_evidence_binding(
            context, evidence_ref=records[0].evidence_ref,
            evidence_roles=(contracts.EvidenceRole.FEATURE_SUPPORT, role),
        )


def test_binding_authority_permission_mismatch_fails(tmp_path):
    _, _, context, records = _newsroom_context(tmp_path, [_candidate("allowed", allowed=True)])
    record = records[0]
    with pytest.raises(ValueError, match="binding_authority_upgrade_forbidden"):
        adapters.build_receipt_backed_evidence_binding(
            context, evidence_ref=record.evidence_ref, authority_state="FIRST_PARTY_VERIFIED",
        )
    binding = adapters.build_receipt_backed_evidence_binding(context, evidence_ref=record.evidence_ref)
    bad = replace(binding, reason_codes=("context_only",), logical_hash="")
    bad = replace(bad, logical_hash=bad.calculated_logical_hash())
    assert "evidence_qualification_reason_mismatch" in contracts.trusted_evidence_blockers(bad, context)


def test_candidate_authority_mismatch_and_caller_only_authority_fail_closed(tmp_path):
    _, _, context, records = _newsroom_context(tmp_path, [_candidate("allowed", allowed=True)])
    binding = adapters.build_receipt_backed_evidence_binding(context, evidence_ref=records[0].evidence_ref)
    candidate = core.LearningCandidateV2(
        candidate_id="candidate:mismatch", story_id="story:mismatch", cluster_id=None, update_chain_id=None,
        source_relationship=contracts.EventRelationship.INITIAL_EVENT, evidence_state="EXTRACTED",
        authority_state="BLOCKED", authority_ready=False, reporting_allowed=False,
        authority_blockers=("caller_only",), history_identity_match=False,
        evidence_refs=(records[0].evidence_ref,), governed_evidence_bindings=(binding,), evidence_context=context,
    )
    with pytest.raises(ValueError, match="candidate_authority_mismatch"):
        core.evaluate_outcome(candidate, adapters.load_foundation_config(ROOT))
    caller_only = replace(candidate, candidate_id="allowed", evidence_refs=(), governed_evidence_bindings=(), authority_state="AUTHORIZED", authority_ready=True, reporting_allowed=True, authority_blockers=())
    with pytest.raises(ValueError, match="candidate_authority_mismatch"):
        core.evaluate_outcome(caller_only, adapters.load_foundation_config(ROOT))


def test_blocking_record_is_not_overridden_by_permissive_record(tmp_path):
    _, _, context, records = _newsroom_context(tmp_path, [
        _candidate("allowed", allowed=True), _candidate("blocked", allowed=False),
    ])
    bindings = tuple(adapters.build_receipt_backed_evidence_binding(context, evidence_ref=row.evidence_ref) for row in records)
    candidate = core.LearningCandidateV2(
        candidate_id="candidate:combined", story_id="story:combined", cluster_id=None, update_chain_id=None,
        source_relationship=contracts.EventRelationship.INITIAL_EVENT, evidence_state="EXTRACTED",
        authority_state="AUTHORIZED", authority_ready=True, reporting_allowed=True, authority_blockers=(),
        history_identity_match=False, evidence_refs=tuple(row.evidence_ref for row in records),
        governed_evidence_bindings=bindings, evidence_context=context,
    )
    derived = core.derive_candidate_authority_v1(candidate, context)
    assert derived.authority_ready is False and derived.reporting_allowed is False
    assert any(value.startswith("evidence_authority_blocked:") for value in derived.authority_blockers)
    with pytest.raises(ValueError, match="candidate_authority_mismatch"):
        core.evaluate_outcome(candidate, adapters.load_foundation_config(ROOT))


def test_exact_single_ref_feature_derivation_passes(tmp_path):
    context, records, _, bindings = _bls_context(tmp_path)
    context = replace(context, extracted_evidence_records=(records[0],), extracted_feature_values=tuple(
        row for row in context.extracted_feature_values if row.evidence_refs == (records[0].evidence_ref,)
    ))
    candidate = _learning_candidate((records[0],), (bindings[0],), (records[0].evidence_ref,))
    candidate = replace(candidate, evidence_context=context)
    rows = core.evaluate_features(candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none"))
    assert next(row for row in rows if row.feature_id == "evidence_completeness").raw_value == 1.0


def test_multi_ref_requires_registered_exact_aggregation_and_subset_fails(tmp_path):
    context, records, values, bindings = _bls_context(tmp_path)
    candidate = replace(_learning_candidate(records, bindings, tuple(row.evidence_ref for row in records)), evidence_context=context)
    with pytest.raises(ValueError, match="feature_aggregation_required"):
        core.evaluate_features(candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none"))
    subset = replace(candidate, feature_inputs=(replace(candidate.feature_inputs[0], evidence_refs=(records[0].evidence_ref,)),))
    with pytest.raises(ValueError, match="feature_evidence_set_mismatch"):
        core.evaluate_features(subset, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none"))

    individual = {
        row.evidence_refs[0]: float(row.value)
        for row in values if row.feature_id == "evidence_completeness"
    }
    draft = contracts.FeatureEvidenceAggregationV1(
        aggregation_id="aggregation:evidence-completeness", aggregation_version="v1",
        feature_id="evidence_completeness", input_evidence_refs=tuple(row.evidence_ref for row in records),
        individual_values=individual, aggregation_rule="ARITHMETIC_MEAN_V1", output_value=1.0,
        logical_hash="",
    )
    aggregation = replace(draft, logical_hash=draft.calculated_logical_hash())
    aggregated_context = replace(context, registered_feature_aggregations=(aggregation,))
    aggregated_candidate = replace(candidate, evidence_context=aggregated_context)
    first = core.evaluate_features(aggregated_candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none"))
    second = core.evaluate_features(aggregated_candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none"))
    assert contracts.logical_hash(first) == contracts.logical_hash(second)
    assert next(row for row in first if row.feature_id == "evidence_completeness").evidence_count == 2
