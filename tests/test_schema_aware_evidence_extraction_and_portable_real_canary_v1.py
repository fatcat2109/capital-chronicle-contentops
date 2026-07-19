from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess

import pytest

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import schema_aware_evidence_extraction_v1 as extraction
from live_contentops import schema_aware_real_canary_v1 as canary


ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = "2026-07-19T02:00:00Z"


def _git(repo: Path, *args: str, env=None) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, env=env).stdout.strip()


def _commit(repo: Path, message: str) -> str:
    env = {**os.environ, "GIT_AUTHOR_DATE": FIXED_TIME, "GIT_COMMITTER_DATE": FIXED_TIME}
    _git(repo, "add", ".", env=env)
    _git(repo, "commit", "-m", message, env=env)
    return _git(repo, "rev-parse", "HEAD")


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "portable-upstream"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "portable-test@example.invalid")
    _git(repo, "config", "user.name", "Portable Test")
    return repo


def _write_json(repo: Path, relative: str, value) -> None:
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _three_family_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = _init_repo(tmp_path)
    _write_json(repo, canary.REAL_EDITORIAL_ARTIFACTS[0]["path"], {
        "status": "REQUEST_SUCCEEDED", "responseTime": 1, "message": [],
        "Results": {"series": [{"seriesID": "CUUR0000SA0", "data": [{"year": "2026", "period": "M04", "periodName": "April", "value": "333.020", "footnotes": [{}]}]}]},
    })
    _write_json(repo, canary.REAL_EDITORIAL_ARTIFACTS[1]["path"], {
        "data": [{"cusip": "912810UU0", "announcemt_date": "2026-06-04", "auction_date": "2026-06-11", "security_type": "Bond", "security_term": "29-Year 11-Month", "auction_format": "Single-Price", "offering_amt": "22000000000", "reopening": "Yes"}],
        "meta": {"count": 1}, "links": {},
    })
    _write_json(repo, canary.REAL_EDITORIAL_ARTIFACTS[2]["path"], {
        "refRates": [{"effectiveDate": "2026-06-04", "type": "SOFR", "percentRate": 3.62, "volumeInBillions": 3147, "revisionIndicator": ""}],
    })
    return repo, _commit(repo, "portable real editorial exports")


def _receipt(repo: Path, commit: str, spec, *, schema=None):
    registry = adapters.load_trusted_verifier_registry(ROOT)
    extractors = extraction.load_extractor_registry(ROOT)
    extractor = extractors.resolve(spec["extractor_id"], "v1")
    return adapters.build_local_git_artifact_receipt(
        git_repository=repo, repository_identity=canary.UPSTREAM_REPOSITORY,
        branch="main", commit=commit, artifact_path=spec["path"],
        artifact_schema_version=schema or spec["artifact_schema_version"],
        producer_version=extractor.shape_contract_id,
        artifact_cutoff_utc=FIXED_TIME, evidence_refs=(),
        source_authority_class="official_public_data", registry=registry,
        verification_time_utc=FIXED_TIME, branch_authority_ref="refs/heads/main",
    )


def _extract(repo: Path, commit: str, spec, **changes):
    consumed = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{spec['path']}"], check=True, capture_output=True).stdout
    receipt = _receipt(repo, commit, spec)
    kwargs = dict(
        receipt=receipt, registry=extraction.load_extractor_registry(ROOT),
        extractor_id=spec["extractor_id"], extractor_version="v1",
        selector=spec["selector"], feature_targets=spec["feature_targets"],
        decision_cutoff_utc=canary.DECISION_CUTOFF_UTC,
    )
    kwargs.update(changes)
    return consumed, receipt, extraction.extract_artifact_evidence(consumed, **kwargs)


def _newsroom_repo(tmp_path: Path, *, corrupt_hash: bool = False) -> tuple[Path, str, dict]:
    repo = _init_repo(tmp_path)
    candidate = {
        "candidate_id": "candidate:portable", "evidence_hash": "a" * 64,
        "authority": {"story_decision": "ALLOW"},
        "claim_permissions": {"decision": "ALLOW", "reporting_allowed": True},
        "event_time_utc": "2026-07-19T00:00:00Z", "known_at_utc": "2026-07-19T01:00:00Z",
        "source_packet_id": "packet:portable", "source_packet_logical_hash": "b" * 64,
        "relationship": "new_phase", "source_documents": [{"published_at_utc": "2026-07-19T00:00:00Z"}],
    }
    artifact = {
        "schema_version": "capital_chronicle.newsroom_candidate_pool.v1",
        "producer_version": "newsroom_candidate_pool_v1.1.0", "pool_id": "pool:portable",
        "cutoff_time_utc": FIXED_TIME, "eligible_candidates": [candidate], "rejected_candidates": [],
    }
    artifact["logical_hash"] = "0" * 64 if corrupt_hash else contracts.logical_hash({key: value for key, value in artifact.items() if key != "pool_id"})
    path = "docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json"
    _write_json(repo, path, artifact)
    return repo, _commit(repo, "newsroom pool"), artifact


def test_arbitrary_ref_is_rejected_when_absent_from_extracted_records(tmp_path):
    repo, commit = _three_family_repo(tmp_path)
    _, receipt, (record, features) = _extract(repo, commit, canary.REAL_EDITORIAL_ARTIFACTS[0])
    context = contracts.EvidenceDecisionContextV1(
        adapters.load_trusted_verifier_registry(ROOT), (receipt,), canary.DECISION_CUTOFF_UTC,
        extraction.load_extractor_registry(ROOT), (record,), features,
    )
    valid = adapters.build_receipt_backed_evidence_binding(
        context, evidence_ref=record.evidence_ref, evidence_roles=record.evidence_roles,
        evidence_scope=record.evidence_scope, target_feature_ids=record.feature_targets,
        as_of_utc=receipt.artifact_cutoff_utc,
    )
    draft = replace(valid, evidence_ref="caller:arbitrary", logical_hash="")
    bad = replace(draft, logical_hash=draft.calculated_logical_hash())
    assert "evidence_ref_absent_from_extracted_records" in contracts.trusted_evidence_blockers(bad, context)


def test_correct_bls_series_period_is_byte_derived(tmp_path):
    repo, commit = _three_family_repo(tmp_path)
    _, _, (record, features) = _extract(repo, commit, canary.REAL_EDITORIAL_ARTIFACTS[0])
    assert record.record_key == "CUUR0000SA0:2026:M04"
    assert record.evidence_ref.startswith("extracted:")
    assert next(row for row in features if row.feature_id == "evidence_completeness").value == 1.0


@pytest.mark.parametrize("selector,reason", [
    ({"series_id": "WRONG", "year": "2026", "period": "M04"}, "bls_series_not_found"),
    ({"series_id": "CUUR0000SA0", "year": "2026", "period": "M99"}, "bls_period_not_found"),
])
def test_wrong_bls_series_or_period_rejected(tmp_path, selector, reason):
    repo, commit = _three_family_repo(tmp_path)
    with pytest.raises(ValueError, match=reason):
        _extract(repo, commit, canary.REAL_EDITORIAL_ARTIFACTS[0], selector=selector)


def test_schema_label_mismatch_rejected(tmp_path):
    repo, commit = _three_family_repo(tmp_path)
    spec = canary.REAL_EDITORIAL_ARTIFACTS[0]
    consumed = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{spec['path']}"], check=True, capture_output=True).stdout
    receipt = _receipt(repo, commit, spec)
    bad = replace(receipt, artifact_schema_version="external.nyfed_reference_rates_response.v1")
    with pytest.raises(ValueError, match="extractor_schema_mismatch"):
        extraction.extract_artifact_evidence(
            consumed, receipt=bad, registry=extraction.load_extractor_registry(ROOT),
            extractor_id=spec["extractor_id"], extractor_version="v1", selector=spec["selector"],
            feature_targets=spec["feature_targets"], decision_cutoff_utc=canary.DECISION_CUTOFF_UTC,
        )


def test_changed_bytes_and_pointer_result_rejected(tmp_path):
    repo, commit = _three_family_repo(tmp_path)
    consumed, receipt, _ = _extract(repo, commit, canary.REAL_EDITORIAL_ARTIFACTS[0])
    with pytest.raises(ValueError, match="extractor_consumed_bytes_receipt_mismatch"):
        extraction.extract_artifact_evidence(
            consumed + b" ", receipt=receipt, registry=extraction.load_extractor_registry(ROOT),
            extractor_id="contentops.bls_series_observation_extractor", extractor_version="v1",
            selector=canary.REAL_EDITORIAL_ARTIFACTS[0]["selector"], feature_targets=("freshness",),
            decision_cutoff_utc=canary.DECISION_CUTOFF_UTC,
        )


def test_missing_required_selected_record_field_rejected(tmp_path):
    repo = _init_repo(tmp_path)
    spec = canary.REAL_EDITORIAL_ARTIFACTS[0]
    _write_json(repo, spec["path"], {
        "status": "REQUEST_SUCCEEDED",
        "Results": {"series": [{"seriesID": "CUUR0000SA0", "data": [{"year": "2026", "period": "M04"}]}]},
    })
    commit = _commit(repo, "missing BLS value")
    with pytest.raises(ValueError, match="extractor_required_fields_missing:value"):
        _extract(repo, commit, spec)


def test_schemaless_artifact_uses_external_shape_contract(tmp_path):
    repo, commit = _three_family_repo(tmp_path)
    _, _, (record, _) = _extract(repo, commit, canary.REAL_EDITORIAL_ARTIFACTS[0])
    assert record.schema_authority == "EXTERNAL_ASSIGNED"
    assert record.internal_logical_hash_verified is None


def test_newsroom_candidate_fields_and_internal_hash_are_proved(tmp_path):
    repo, commit, artifact = _newsroom_repo(tmp_path)
    path = "docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json"
    receipt = adapters.build_local_git_artifact_receipt(
        git_repository=repo, repository_identity=canary.UPSTREAM_REPOSITORY, branch="main", commit=commit,
        artifact_path=path, artifact_schema_version=artifact["schema_version"],
        producer_version=artifact["producer_version"], artifact_cutoff_utc=artifact["cutoff_time_utc"],
        evidence_refs=(), source_authority_class="official_public_data",
        registry=adapters.load_trusted_verifier_registry(ROOT), verification_time_utc=FIXED_TIME,
        branch_authority_ref="refs/heads/main",
    )
    consumed = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"], check=True, capture_output=True).stdout
    record, values = extraction.extract_artifact_evidence(
        consumed, receipt=receipt, registry=extraction.load_extractor_registry(ROOT),
        extractor_id="contentops.newsroom_candidate_extractor", extractor_version="v1",
        selector={"candidate_id": "candidate:portable"},
        feature_targets=("authority_readiness", "evidence_completeness"),
        decision_cutoff_utc=canary.DECISION_CUTOFF_UTC,
        permission_state="REPORTING_ALLOWED",
    )
    assert record.internal_logical_hash_verified is True
    assert {"candidate_id", "evidence_hash", "authority", "claim_permissions", "source_packet_id", "source_packet_logical_hash"}.issubset(record.source_fields_used)
    assert next(row for row in values if row.feature_id == "authority_readiness").value == 1.0


def test_internal_logical_hash_mismatch_rejected(tmp_path):
    repo, commit, artifact = _newsroom_repo(tmp_path, corrupt_hash=True)
    path = "docs/research/newsroom_candidate_pool_v1/CapitalChronicleNewsroomCandidatePoolV1.json"
    receipt = adapters.build_local_git_artifact_receipt(
        git_repository=repo, repository_identity=canary.UPSTREAM_REPOSITORY, branch="main", commit=commit,
        artifact_path=path, artifact_schema_version=artifact["schema_version"], producer_version=artifact["producer_version"],
        artifact_cutoff_utc=artifact["cutoff_time_utc"], evidence_refs=(), source_authority_class="official_public_data",
        registry=adapters.load_trusted_verifier_registry(ROOT), verification_time_utc=FIXED_TIME,
        branch_authority_ref="refs/heads/main",
    )
    consumed = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{path}"], check=True, capture_output=True).stdout
    with pytest.raises(ValueError, match="internal_logical_hash_mismatch"):
        extraction.extract_artifact_evidence(
            consumed, receipt=receipt, registry=extraction.load_extractor_registry(ROOT),
            extractor_id="contentops.newsroom_candidate_extractor", extractor_version="v1",
            selector={"candidate_id": "candidate:portable"}, feature_targets=("authority_readiness",),
            decision_cutoff_utc=canary.DECISION_CUTOFF_UTC,
        )


def test_unsupported_and_disabled_extractors_rejected(tmp_path):
    repo, commit = _three_family_repo(tmp_path)
    spec = canary.REAL_EDITORIAL_ARTIFACTS[0]
    consumed = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{spec['path']}"], check=True, capture_output=True).stdout
    receipt = _receipt(repo, commit, spec)
    base = dict(consumed_bytes=consumed, receipt=receipt, registry=extraction.load_extractor_registry(ROOT), extractor_version="v1", selector=spec["selector"], feature_targets=("freshness",), decision_cutoff_utc=canary.DECISION_CUTOFF_UTC)
    with pytest.raises(ValueError, match="unsupported_extractor"):
        extraction.extract_artifact_evidence(extractor_id="unknown.extractor", **base)
    with pytest.raises(ValueError, match="extractor_disabled"):
        extraction.extract_artifact_evidence(extractor_id="contentops.disabled_legacy_extractor", **base)


def test_feature_values_are_derived_or_unavailable(tmp_path):
    repo, commit = _three_family_repo(tmp_path)
    _, _, (_, bls_values) = _extract(repo, commit, canary.REAL_EDITORIAL_ARTIFACTS[0])
    freshness = next(row for row in bls_values if row.feature_id == "freshness")
    assert freshness.availability == contracts.AvailabilityState.UNAVAILABLE and freshness.value is None
    _, _, (_, rate_values) = _extract(repo, commit, canary.REAL_EDITORIAL_ARTIFACTS[2])
    rate_freshness = next(row for row in rate_values if row.feature_id == "freshness")
    assert rate_freshness.availability == contracts.AvailabilityState.EXPLICIT_ZERO
    assert rate_freshness.value == 0.0


def test_caller_cannot_replace_extracted_feature_value(tmp_path):
    repo, commit = _three_family_repo(tmp_path)
    _, receipt, (record, values) = _extract(repo, commit, canary.REAL_EDITORIAL_ARTIFACTS[0])
    context = contracts.EvidenceDecisionContextV1(
        adapters.load_trusted_verifier_registry(ROOT), (receipt,), canary.DECISION_CUTOFF_UTC,
        extraction.load_extractor_registry(ROOT), (record,), values,
    )
    binding = adapters.build_receipt_backed_evidence_binding(
        context, evidence_ref=record.evidence_ref, evidence_roles=record.evidence_roles,
        evidence_scope=record.evidence_scope, target_feature_ids=record.feature_targets,
        as_of_utc=receipt.artifact_cutoff_utc,
    )
    candidate = core.LearningCandidateV2(
        candidate_id="candidate:override", story_id="story:override", cluster_id="cluster:override",
        update_chain_id="chain:override", source_relationship=contracts.EventRelationship.INITIAL_EVENT,
        evidence_state="EXTRACTED", authority_state="CONTEXT", authority_ready=False,
        reporting_allowed=False, authority_blockers=("no_publication",), history_identity_match=False,
        material_reader_contribution=True,
        feature_inputs=(core.FeatureInputV1(
            "evidence_completeness", True, contracts.AvailabilityState.AVAILABLE, 0.25,
            evidence_refs=(record.evidence_ref,), evidence_scope=record.evidence_scope,
        ),),
        evidence_refs=(record.evidence_ref,), governed_evidence_bindings=(binding,), evidence_context=context,
    )
    with pytest.raises(ValueError, match="caller_feature_value_mismatch"):
        core.evaluate_features(candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none"))


def test_internal_future_timestamp_rejected(tmp_path):
    repo = _init_repo(tmp_path)
    spec = canary.REAL_EDITORIAL_ARTIFACTS[2]
    _write_json(repo, spec["path"], {"refRates": [{"effectiveDate": "2026-07-20", "type": "SOFR", "percentRate": 3.62}]})
    commit = _commit(repo, "future rate")
    future_spec = {**spec, "selector": {"rate_type": "SOFR", "effective_date": "2026-07-20"}}
    with pytest.raises(ValueError, match="internal_future_timestamp"):
        _extract(repo, commit, future_spec)


def test_historical_commit_survives_branch_advancement(tmp_path):
    repo, commit_a = _three_family_repo(tmp_path)
    marker = repo / "later.txt"
    marker.write_text("branch advanced", encoding="utf-8")
    commit_b = _commit(repo, "advance branch")
    receipt = _receipt(repo, commit_a, canary.REAL_EDITORIAL_ARTIFACTS[0])
    assert receipt.producer_commit == commit_a
    assert receipt.branch_head_observed == commit_b
    assert receipt.producer_commit_reachable_from_branch is True


def test_unrelated_branch_commit_rejected(tmp_path):
    repo, _ = _three_family_repo(tmp_path)
    _git(repo, "switch", "--orphan", "unrelated")
    for child in repo.iterdir():
        if child.name != ".git" and child.is_file():
            child.unlink()
    (repo / "unrelated.txt").write_text("unrelated", encoding="utf-8")
    unrelated = _commit(repo, "unrelated history")
    _git(repo, "switch", "main")
    with pytest.raises(ValueError, match="committed_artifact_not_reachable_from_branch"):
        _receipt(repo, unrelated, canary.REAL_EDITORIAL_ARTIFACTS[0])


def test_portable_three_family_canary_is_deterministic(tmp_path):
    repo, commit = _three_family_repo(tmp_path)
    first = canary.run_schema_aware_real_canary(
        repo_root=ROOT, upstream_git_repository=repo, upstream_commit=commit,
        branch_authority_ref="refs/heads/main",
    )
    second = canary.run_schema_aware_real_canary(
        repo_root=ROOT, upstream_git_repository=repo, upstream_commit=commit,
        branch_authority_ref="refs/heads/main",
    )
    assert first == second
    assert first["status"] == "PASS"
    assert first["coverage"]["distinct_artifact_family_count"] == 3
    assert first["coverage"]["internal_access_contracts_counted"] == 0
    assert all(row["evidence_ref"].startswith("extracted:") for row in first["artifact_inventory"])
    assert all(row["publication_disposition"].startswith("NO_PUBLICATION") for row in first["decision_rows"])


def test_no_committed_machine_local_upstream_path():
    paths = (
        ROOT / "tests/test_trusted_evidence_verifier_registry_and_real_multi_topic_canary_v1.py",
        ROOT / "tests/test_schema_aware_evidence_extraction_and_portable_real_canary_v1.py",
        ROOT / "live_contentops/schema_aware_real_canary_v1.py",
    )
    machine_prefix = "C:" + "\\Users\\"
    assert all(machine_prefix not in path.read_text(encoding="utf-8") for path in paths)


def test_v1_tag_unchanged():
    assert _git(ROOT, "rev-parse", "v1.0^{}") == "6983bfb3ef300414b744f3f8f97ca81ff699348b"
