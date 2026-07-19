from dataclasses import replace
from pathlib import Path
import subprocess

import pytest

from live_contentops import adaptive_learning_adapters_v2 as adapters
from live_contentops import adaptive_learning_core_v2 as core
from live_contentops import content_intelligence_contracts_v2 as contracts
from live_contentops import trusted_evidence_real_canary_v1 as canary
from live_contentops import trusted_evidence_canary_evidence_v1 as evidence_builder


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_GIT = Path(r"C:\Users\bullw\.codex\upstream-readonly\headline-raw-data-json-hardening.git")


def _context(*refs: str, cutoff: str = "2026-07-19T01:22:00Z"):
    return adapters.build_synthetic_validation_context(refs, decision_cutoff_utc=cutoff, repo_root=ROOT)


def _binding(
    context, ref="evidence:trusted", *, role=contracts.EvidenceRole.FEATURE_SUPPORT,
    scope=contracts.EvidenceScope.FEATURE_SPECIFIC, targets=("freshness",),
    authority="VERIFIED_GOVERNED", permission="REPORTING_ALLOWED",
):
    return adapters.build_receipt_backed_evidence_binding(
        context, evidence_ref=ref, evidence_roles=(role,), evidence_scope=scope,
        authority_state=authority, permission_state=permission,
        target_feature_ids=targets,
    )


def _candidate(context, binding, *, item=None, relationship=contracts.EventRelationship.INITIAL_EVENT, **changes):
    candidate = core.LearningCandidateV2(
        candidate_id="trusted:candidate", story_id="trusted:story",
        cluster_id="trusted:cluster", update_chain_id="trusted:chain",
        source_relationship=relationship, evidence_state="TRUSTED_EVIDENCE",
        authority_state="AUTHORIZED", authority_ready=True, reporting_allowed=True,
        authority_blockers=(), history_identity_match=False,
        material_reader_contribution=True,
        feature_inputs=(item,) if item else (),
        evidence_refs=(binding.evidence_ref,), governed_evidence_bindings=(binding,),
        evidence_context=context,
    )
    return replace(candidate, **changes)


def _rehash_binding(binding, **changes):
    draft = replace(binding, **changes, logical_hash="")
    return replace(draft, logical_hash=draft.calculated_logical_hash())


def _narrow_context(context, **record_changes):
    record = replace(context.verifier_registry.records[0], **record_changes)
    registry_draft = contracts.TrustedVerifierRegistryV1(
        "trusted-evidence-registry-test", (record,), "",
    )
    registry = replace(registry_draft, registry_logical_hash=registry_draft.calculated_logical_hash())
    old_receipt = context.producer_receipts[0]
    receipt_draft = replace(
        old_receipt, registry_version=registry.registry_version,
        registry_logical_hash=registry.registry_logical_hash, logical_hash="",
    )
    receipt = replace(receipt_draft, logical_hash=receipt_draft.calculated_logical_hash())
    return contracts.EvidenceDecisionContextV1(registry, (receipt,), context.decision_cutoff_utc)


def _rebind_to_context(binding, context):
    receipt = context.producer_receipts[0]
    return _rehash_binding(
        binding, producer_receipt_id=receipt.receipt_id,
        producer_receipt_logical_hash=receipt.logical_hash,
        producer_artifact_binding_hash=receipt.consumed_byte_sha256,
        verifier_id=receipt.verifier_id, verifier_version=receipt.verifier_version,
    )


def test_registry_is_committed_versioned_hash_bound_and_enabled():
    registry = adapters.load_trusted_verifier_registry(ROOT)
    assert registry.validate() == ()
    assert registry.registry_version == "trusted-evidence-registry-1.0.0"
    assert registry.registry_logical_hash == registry.calculated_logical_hash()
    assert any(row.enabled for row in registry.records)
    assert any(not row.enabled for row in registry.records)


@pytest.mark.parametrize("mutation,reason", [
    ({"verifier_id": "unknown.verifier"}, "unknown_verifier_id_version"),
    ({"verifier_version": "v999"}, "unknown_verifier_id_version"),
    ({"producer_receipt_id": "producer_receipt:missing"}, "producer_receipt_missing"),
    ({"producer_receipt_logical_hash": "0" * 64}, "producer_receipt_hash_mismatch"),
    ({"producer_artifact_binding_hash": "f" * 64}, "producer_byte_hash_mismatch"),
])
def test_unknown_verifier_and_receipt_mutations_are_rejected(mutation, reason):
    context = _context("evidence:trusted")
    binding = _rehash_binding(_binding(context), **mutation)
    assert reason in contracts.trusted_evidence_blockers(binding, context)
    outcome = core.evaluate_outcome(
        _candidate(
            context, binding, relationship=contracts.EventRelationship.MATERIAL_UPDATE,
            governed_material_delta=True, material_delta_evidence_ref=binding.evidence_ref,
        ), adapters.load_foundation_config(ROOT),
    )
    assert "GOVERNED_MATERIAL_UPDATE" not in outcome.actionable_outcomes


def test_disabled_verifier_is_rejected():
    context = _context("evidence:trusted")
    disabled = context.verifier_registry.records[1]
    binding = _rehash_binding(
        _binding(context), verifier_id=disabled.verifier_id,
        verifier_version=disabled.verifier_version,
    )
    blockers = contracts.trusted_evidence_blockers(binding, context)
    assert "trusted_verifier_disabled" in blockers or "producer_receipt_verifier_mismatch" in blockers


@pytest.mark.parametrize("record_change,binding_change,reason", [
    ({"allowed_authority_states": ("OFFICIAL_VERIFIED",)}, {"authority_state": "VERIFIED_GOVERNED"}, "evidence_authority_state_not_allowed"),
    ({"allowed_permission_states": ("CONTEXT_ONLY",)}, {"permission_state": "REPORTING_ALLOWED"}, "evidence_permission_state_not_allowed"),
    ({"allowed_evidence_roles": (contracts.EvidenceRole.CONFIRMATION,)}, {}, "evidence_role_not_allowed"),
    ({"allowed_evidence_scopes": (contracts.EvidenceScope.CANDIDATE_WIDE,)}, {}, "evidence_scope_not_allowed"),
])
def test_registry_disallowed_state_permission_role_and_scope_fail_closed(record_change, binding_change, reason):
    original = _context("evidence:trusted")
    context = _narrow_context(original, **record_change)
    binding = _rebind_to_context(_rehash_binding(_binding(original), **binding_change), context)
    assert reason in contracts.trusted_evidence_blockers(binding, context)


def test_registry_hash_mismatch_is_rejected_by_decision_context():
    context = _context("evidence:trusted")
    bad_registry = replace(context.verifier_registry, registry_logical_hash="0" * 64)
    bad = replace(context, verifier_registry=bad_registry)
    assert "registry_logical_hash_mismatch" in bad.validate()
    bad_receipt = replace(context.producer_receipts[0], logical_hash="0" * 64)
    assert "producer_receipt_logical_hash_mismatch" in bad_receipt.validate()
    bad_derivation = replace(
        context.producer_receipts[0],
        evidence_ref_derivations={"evidence:trusted": "0" * 64},
    )
    assert any(value.startswith("producer_receipt_evidence_ref_derivation_mismatch") for value in bad_derivation.validate())


def test_receipt_builder_rejects_wrong_repo_path_commit_schema_and_authority_class():
    registry = adapters.load_trusted_verifier_registry(ROOT)
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    path = adapters.CONFIG_REL_PATH.as_posix()
    data = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{path}"], check=True, capture_output=True).stdout
    blob = subprocess.run(["git", "-C", str(ROOT), "rev-parse", f"{commit}:{path}"], check=True, capture_output=True, text=True).stdout.strip()
    base = dict(
        registry=registry, verifier_id="contentops.exact_git_artifact_verifier", verifier_version="v1",
        repository="fatcat2109/capital-chronicle-contentops", branch="master", producer_commit=commit,
        artifact_path=path, expected_git_blob_sha1=blob,
        artifact_schema_version="contentops.adaptive_learning_config.v1", producer_version="test-v1",
        artifact_cutoff_utc="2026-07-19T00:09:38Z", evidence_refs=("evidence:trusted",),
        source_authority_class="governed_synthetic_validation",
        resolved_repository="fatcat2109/capital-chronicle-contentops", resolved_branch="master",
        resolved_commit=commit, resolved_artifact_path=path,
    )
    cases = (
        ({"resolved_repository": "wrong/repo"}, "producer_repository_identity_mismatch"),
        ({"resolved_artifact_path": "wrong.json"}, "producer_artifact_path_identity_mismatch"),
        ({"resolved_commit": "0" * 40}, "producer_commit_identity_mismatch"),
        ({"artifact_schema_version": "unknown.schema"}, "verifier_artifact_schema_not_allowed"),
        ({"source_authority_class": "unknown_class"}, "verifier_source_authority_class_not_allowed"),
    )
    for changes, expected in cases:
        with pytest.raises(ValueError, match=expected):
            contracts.build_verified_producer_artifact_receipt_v1(data, **{**base, **changes})

    exact = contracts.build_verified_producer_artifact_receipt_v1(data, **base)
    assert exact.validate() == () and exact.git_blob_sha1 == blob
    with pytest.raises(ValueError, match="producer_git_blob_mismatch"):
        contracts.build_verified_producer_artifact_receipt_v1(data + b"\n", **base)
    with pytest.raises(ValueError, match="producer_git_blob_mismatch"):
        contracts.build_verified_producer_artifact_receipt_v1(data, **{**base, "expected_git_blob_sha1": "0" * 40})
    with pytest.raises(ValueError, match="producer_artifact_logical_hash_mismatch"):
        contracts.build_verified_producer_artifact_receipt_v1(data, **{**base, "declared_artifact_logical_hash": "0" * 64})


def test_random_sha_shaped_value_cannot_replace_verified_receipt():
    context = _context("evidence:trusted")
    binding = _rehash_binding(_binding(context), producer_artifact_binding_hash="a" * 64)
    assert "producer_byte_hash_mismatch" in contracts.trusted_evidence_blockers(binding, context)


def test_evidence_ref_absent_from_receipt_is_rejected():
    context = _context("evidence:trusted")
    binding = _rehash_binding(_binding(context), evidence_ref="evidence:absent")
    assert "evidence_ref_absent_from_producer_receipt" in contracts.trusted_evidence_blockers(binding, context)


def test_point_in_time_rejects_future_evidence_and_future_producer_cutoff():
    context = _context("evidence:trusted")
    future_binding = _rehash_binding(_binding(context), as_of_utc="2026-07-20T00:00:00Z")
    assert "future_evidence_as_of" in contracts.trusted_evidence_blockers(future_binding, context)
    receipt = context.producer_receipts[0]
    future_receipt_draft = replace(receipt, artifact_cutoff_utc="2026-07-20T00:00:00Z", logical_hash="")
    future_receipt = replace(future_receipt_draft, logical_hash=future_receipt_draft.calculated_logical_hash())
    assert any(value.startswith("future_producer_receipt") for value in replace(context, producer_receipts=(future_receipt,)).validate())

    record = contracts.build_evidence_reference_v1(
        evidence_ref="evidence:trusted", authority_state="VERIFIED_GOVERNED",
        permission_state="REPORTING_ALLOWED", evidence_roles=(contracts.EvidenceRole.FEATURE_SUPPORT,),
        evidence_scope=contracts.EvidenceScope.FEATURE_SPECIFIC,
        producer_artifact_binding_hash=receipt.consumed_byte_sha256,
        producer_receipt_id=receipt.receipt_id,
        producer_receipt_logical_hash=receipt.logical_hash,
        target_feature_ids=("freshness",), verifier_id=receipt.verifier_id,
        verifier_version=receipt.verifier_version,
        as_of_utc="2026-07-19T01:00:00Z", observed_at_utc="2026-07-19T01:10:00Z",
        source_authority_class=receipt.source_authority_class,
    )
    assert "observed_after_evidence_as_of" in contracts.trusted_evidence_blockers(record, context)


def test_feature_specific_requires_exact_target_and_reports_receipt_provenance():
    context = _context("evidence:trusted")
    item = core.FeatureInputV1(
        "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
        evidence_refs=("evidence:trusted",), evidence_scope=contracts.EvidenceScope.FEATURE_SPECIFIC,
    )
    valid = _candidate(context, _binding(context), item=item)
    row = next(row for row in core.evaluate_features(valid, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none")) if row.feature_id == "freshness")
    assert row.contribution == pytest.approx(0.8)
    assert row.target_feature_id == "freshness"
    assert row.producer_receipt_ids and row.verifier_id_versions
    wrong = _candidate(context, _binding(context, targets=("novelty",)), item=item)
    blocked = next(row for row in core.evaluate_features(wrong, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none")) if row.feature_id == "freshness")
    assert blocked.contribution is None
    assert "feature_target_mismatch" in blocked.evidence_exclusion_reasons["evidence:trusted"]


def test_explicit_confirmation_evidence_cannot_support_freshness():
    context = _context("evidence:trusted")
    item = core.FeatureInputV1(
        "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
        evidence_refs=("evidence:trusted",), evidence_scope=contracts.EvidenceScope.FEATURE_SPECIFIC,
    )
    binding = _binding(context, role=contracts.EvidenceRole.CONFIRMATION)
    row = next(row for row in core.evaluate_features(_candidate(context, binding, item=item), adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none")) if row.feature_id == "freshness")
    assert row.evidence_count == 0
    assert "feature_support_role_missing" in row.evidence_exclusion_reasons["evidence:trusted"]


def test_candidate_wide_reuse_requires_registry_permission():
    context = _context("evidence:trusted")
    item = core.FeatureInputV1(
        "freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8,
        evidence_scope=contracts.EvidenceScope.CANDIDATE_WIDE,
    )
    binding = _binding(context, scope=contracts.EvidenceScope.CANDIDATE_WIDE, targets=())
    valid = _candidate(context, binding, item=item)
    assert next(row for row in core.evaluate_features(valid, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none")) if row.feature_id == "freshness").evidence_count == 1
    narrowed = _narrow_context(context, candidate_wide_reuse_allowed=False)
    narrowed_binding = _rebind_to_context(binding, narrowed)
    blocked = _candidate(narrowed, narrowed_binding, item=item)
    row = next(row for row in core.evaluate_features(blocked, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none")) if row.feature_id == "freshness")
    assert row.evidence_count == 0
    assert "candidate_wide_reuse_not_allowed" in row.evidence_exclusion_reasons["evidence:trusted"]


@pytest.mark.parametrize("availability,value,expected_count", [
    (contracts.AvailabilityState.AVAILABLE, 5.0, 1),
    (contracts.AvailabilityState.EXPLICIT_ZERO, 0.0, 1),
    (contracts.AvailabilityState.UNAVAILABLE, None, 0),
])
def test_performance_scope_resolves_actual_observation_and_preserves_zero(availability, value, expected_count):
    ref = "observation:actual"
    context = _context(ref)
    binding = _binding(context, ref, scope=contracts.EvidenceScope.PERFORMANCE_OBSERVATION, targets=())
    item = core.FeatureInputV1(
        "performance_evidence_availability", True, contracts.AvailabilityState.AVAILABLE, 1.0,
        evidence_refs=(ref,), evidence_scope=contracts.EvidenceScope.PERFORMANCE_OBSERVATION,
    )
    observation = contracts.PerformanceObservationV1(
        ref, "content:1", "story:1", "chain:1", "variant:1", "views", value,
        availability,
        contracts.MetricAuthorityClass.FIRST_PARTY_WEB_ANALYTICS if value is not None else contracts.MetricAuthorityClass.UNAVAILABLE,
        observed_at_utc="2026-07-19T00:30:00Z" if value is not None else None,
        unavailable_reason="not_available" if value is None else None,
    )
    candidate = _candidate(context, binding, item=item)
    row = next(row for row in core.evaluate_features(candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("observations", (observation,))) if row.feature_id == item.feature_id)
    assert row.evidence_count == expected_count


def test_fake_and_future_performance_observations_do_not_contribute():
    ref = "observation:fake"
    context = _context(ref)
    binding = _binding(context, ref, scope=contracts.EvidenceScope.PERFORMANCE_OBSERVATION, targets=())
    item = core.FeatureInputV1("performance_evidence_availability", True, contracts.AvailabilityState.AVAILABLE, 1.0, evidence_refs=(ref,), evidence_scope=contracts.EvidenceScope.PERFORMANCE_OBSERVATION)
    candidate = _candidate(context, binding, item=item)
    missing = next(row for row in core.evaluate_features(candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none")) if row.feature_id == item.feature_id)
    assert missing.evidence_count == 0
    future = contracts.PerformanceObservationV1(ref, "content:1", "story:1", "chain:1", "variant:1", "views", 1.0, contracts.AvailabilityState.AVAILABLE, contracts.MetricAuthorityClass.FIRST_PARTY_WEB_ANALYTICS, observed_at_utc="2026-07-20T00:00:00Z")
    row = next(row for row in core.evaluate_features(candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("future", (future,))) if row.feature_id == item.feature_id)
    assert row.evidence_count == 0
    assert "future_performance_observation" in row.evidence_exclusion_reasons[ref]


def test_content_history_scope_resolves_actual_version_at_cutoff_and_rejects_fake_or_future():
    ref = "article-version:actual"
    context = _context(ref)
    binding = _binding(context, ref, scope=contracts.EvidenceScope.CONTENT_HISTORY, targets=())
    item = core.FeatureInputV1("freshness", True, contracts.AvailabilityState.AVAILABLE, 0.8, evidence_refs=(ref,), evidence_scope=contracts.EvidenceScope.CONTENT_HISTORY)
    candidate = _candidate(context, binding, item=item)
    version = contracts.ArticleVersionV1(ref, "GOVERNED", "a" * 64, True, created_at_utc="2026-07-19T00:30:00Z")
    history = contracts.PublishedContentHistoryV1("history", (contracts.PublishedContentItemV1("content:1", "story:1", None, None, None, article_versions=(version,), current_article_version_id=ref),))
    row = next(row for row in core.evaluate_features(candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none"), history) if row.feature_id == "freshness")
    assert row.evidence_count == 1 and row.resolved_evidence_types == ("content_history_article_version",)
    fake = replace(item, evidence_refs=("article-version:fake",))
    fake_context = _context("article-version:fake")
    fake_candidate = _candidate(fake_context, _binding(fake_context, "article-version:fake", scope=contracts.EvidenceScope.CONTENT_HISTORY, targets=()), item=fake)
    fake_row = next(row for row in core.evaluate_features(fake_candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none"), history) if row.feature_id == "freshness")
    assert fake_row.evidence_count == 0
    future_version = replace(version, created_at_utc="2026-07-20T00:00:00Z")
    future_history = replace(history, items=(replace(history.items[0], article_versions=(future_version,)),))
    future_row = next(row for row in core.evaluate_features(candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none"), future_history) if row.feature_id == "freshness")
    assert future_row.evidence_count == 0

    superseded_new = replace(
        future_version, current=True, supersedes_article_version_id="article-version:old",
    )
    old = contracts.ArticleVersionV1("article-version:old", "GOVERNED", "b" * 64, False, created_at_utc="2026-07-18T00:00:00Z")
    superseded_history = replace(
        history,
        items=(replace(history.items[0], article_versions=(old, superseded_new), current_article_version_id=ref),),
    )
    superseded_row = next(row for row in core.evaluate_features(candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none"), superseded_history) if row.feature_id == "freshness")
    assert superseded_row.evidence_count == 0


def test_derived_capability_scope_uses_only_validated_dimensions():
    context = _context("evidence:trusted")
    binding = _binding(context)
    candidate = replace(
        _candidate(context, binding),
        capabilities=contracts.CapabilityDimensionsV1(source_family_ids=("source:a", "source:b")),
    )
    row = next(row for row in core.evaluate_features(candidate, adapters.load_foundation_config(ROOT), contracts.PerformanceObservationSetV1("none")) if row.feature_id == "source_diversity")
    assert row.evidence_count == 1
    assert row.evidence_refs[0].startswith("derived-capability:source_diversity:")
    assert row.producer_receipt_ids == ()


def test_governed_outcome_requires_trusted_receipt_and_emits_nonempty_lineage():
    ref = "evidence:delta"
    context = _context(ref)
    binding = _binding(context, ref, role=contracts.EvidenceRole.MATERIAL_DELTA, scope=contracts.EvidenceScope.CANDIDATE_WIDE, targets=())
    candidate = _candidate(context, binding, relationship=contracts.EventRelationship.MATERIAL_UPDATE, governed_material_delta=True, material_delta_evidence_ref=ref)
    outcome = core.evaluate_outcome(candidate, adapters.load_foundation_config(ROOT))
    assert "GOVERNED_MATERIAL_UPDATE" in outcome.actionable_outcomes
    assert outcome.qualifying_governed_evidence_refs == (ref,)
    assert outcome.complete_evidence_lineage


def test_real_multi_topic_canary_uses_three_exact_committed_artifacts_and_no_synthetic_count():
    report = canary.run_real_multi_topic_canary(repo_root=ROOT, upstream_git_dir=UPSTREAM_GIT)
    assert report["status"] == "PASS"
    assert report["coverage"]["distinct_story_count"] >= 3
    assert report["coverage"]["distinct_topic_count"] >= 3
    assert report["coverage"]["distinct_artifact_family_count"] >= 3
    assert report["coverage"]["distinct_modality_count"] >= 2
    assert report["coverage"]["numeric_present"] and report["coverage"]["nonnumeric_present"]
    assert report["coverage"]["synthetic_artifacts_counted"] == 0
    assert all(row["commit"] == canary.UPSTREAM_HEAD and row["git_blob_sha1"] and row["byte_sha256"] for row in report["artifact_inventory"])
    assert all(row["contributing_features"] for row in report["decision_rows"])
    assert report["publication_authority_granted"] is False


def test_real_canary_is_deterministic():
    first = canary.run_real_multi_topic_canary(repo_root=ROOT, upstream_git_dir=UPSTREAM_GIT)
    second = canary.run_real_multi_topic_canary(repo_root=ROOT, upstream_git_dir=UPSTREAM_GIT)
    assert contracts.canonical_json(first) == contracts.canonical_json(second)


def test_evidence_manifest_hashes_every_required_nonself_report(tmp_path):
    summary = {"schema_version": "test", "status": "PASS"}
    manifest = evidence_builder.generate_evidence(
        repo_root=ROOT, upstream_git_dir=UPSTREAM_GIT,
        test_summary=summary,
        changed_protected_paths={"schema_version": "test", "status": "PASS"},
        compatibility_report={"schema_version": "test", "status": "PASS"},
        safety_report={"schema_version": "test", "status": "PASS"},
        output_dir=tmp_path,
    )
    assert manifest["status"] == "PASS"
    assert set(manifest["artifact_byte_sha256"]) == set(evidence_builder.REQUIRED_REPORTS)
    for name, digest in manifest["artifact_byte_sha256"].items():
        assert contracts.sha256((tmp_path / name).read_bytes()).hexdigest() == digest
