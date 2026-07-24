from __future__ import annotations

import copy
import importlib
from pathlib import Path

import pytest

from live_contentops.cross_domain_continuous_shadow_v1 import (
    build_continuous_shadow_operation,
)
from live_contentops.universal_governed_registry_v1 import (
    build_exact_evidence_binding,
    derive_claim_authority_permission,
    load_governed_registry_authority,
    logical_hash,
    validate_claim_document_lineage,
    validate_market_evidence_record,
    validate_pool_cross_candidate_lineage,
    validate_profile_execution,
)
from live_contentops.universal_news_candidate_fabric_v2 import (
    build_claim,
    build_pool,
)


ROOT = Path(__file__).parents[1]
UPSTREAM_ROOT = (
    ROOT.parent.parent
    / "Headline Raw data local json"
    / "capital-chronicle-ingestion"
)


@pytest.fixture(scope="module")
def authority():
    return load_governed_registry_authority(repo_root=ROOT)


@pytest.fixture(scope="module")
def operation():
    if not (UPSTREAM_ROOT / ".git").exists():
        pytest.skip("governed upstream worktree unavailable")
    return build_continuous_shadow_operation(
        repo_root=ROOT,
        upstream_root=UPSTREAM_ROOT,
    )


def _final_pool(operation):
    return operation["multi_cutoff_candidate_pools"][-1]


def test_all_registry_git_receipts_and_append_only_baselines_pass(authority):
    assert len(authority.receipts) == 5
    assert all(
        row["status"] == "PASS_EXACT_COMMITTED_BYTES"
        for row in authority.receipts
    )
    assert len(authority.append_only_reports) == 5
    assert all(row["status"] == "PASS" for row in authority.append_only_reports)
    assert authority.authority_packet()["all_registries_verified"] is True
    assert authority.authority_packet()["caller_registry_creation_allowed"] is False


def test_every_registered_implementation_identity_resolves_to_callable(authority):
    identities = {
        str(record["implementation_identity"])
        for registry in authority.registries.values()
        for record in registry["records"]
    }
    for identity in identities:
        module_name, attribute = identity.rsplit(".", 1)
        implementation = getattr(importlib.import_module(module_name), attribute)
        assert callable(implementation), identity


@pytest.mark.parametrize(
    ("authority_class", "permission_state", "message"),
    [
        (
            "OFFICIAL_VERIFIED",
            "CONTEXT_ONLY",
            "governed_claim_authority_chain_required",
        ),
        (
            "CONTEXT_ONLY",
            "REPORTING_ALLOWED",
            "governed_claim_permission_chain_required",
        ),
        (
            "CONTEXT_ONLY",
            "PUBLIC_CLAIM_ALLOWED",
            "governed_claim_permission_chain_required",
        ),
    ],
)
def test_public_claim_builder_rejects_caller_authority_upgrades(
    authority_class, permission_state, message
):
    with pytest.raises(ValueError, match=message):
        build_claim(
            claim_id="claim:caller",
            claim_type="factual_text",
            statement="Caller declaration.",
            structured_payload={},
            source_document_ids=["doc:caller"],
            evidence_refs=["ref:caller"],
            authority_class=authority_class,
            permission_state=permission_state,
            event_time_utc=None,
            published_at_utc=None,
            known_at_utc="2026-07-14T00:00:00Z",
            citations=[
                {
                    "source_document_id": "doc:caller",
                    "url": "https://example.test/caller",
                }
            ],
        )


def test_public_pool_builder_rejects_self_declared_official_registry():
    with pytest.raises(ValueError, match="caller_source_family_authority_forbidden"):
        build_pool(
            candidates=[],
            source_family_records=[
                {
                    "source_family_id": "caller",
                    "authority_class": "OFFICIAL_VERIFIED",
                    "permission_ceiling": "PUBLIC_CLAIM_ALLOWED",
                    "enabled": True,
                }
            ],
            generated_at_utc="2026-07-14T00:00:00Z",
            cutoff_time_utc="2026-07-14T00:00:00Z",
            upstream_binding={},
            category_blockers={},
        )


def test_arbitrary_adapter_cannot_derive_verified_or_reporting_authority(authority):
    binding = build_exact_evidence_binding(
        binding_id="binding:caller",
        accepted_evidence_binding_id="caller",
        evidence_ref="ref:caller",
        source_family_id="caller_family",
        adapter_id="caller_adapter",
        adapter_binding_record_id="caller_record",
        document_id="doc:caller",
        source_native_id="native:caller",
        content_sha256="a" * 64,
        source_native_status="verified",
        evidence_state="exact",
        consumer_permission="PUBLIC_CLAIM_ALLOWED",
        dqr_reporting_allowed=True,
        receipt={"receipt_kind": "git_artifact", "exact_verified": True},
    )
    decision = derive_claim_authority_permission(
        authority=authority,
        claim_type="factual_text",
        evidence_bindings=[binding],
        trusted_evidence_index={"ref:caller": binding},
        requested_authority="OFFICIAL_VERIFIED",
        requested_permission="PUBLIC_CLAIM_ALLOWED",
    )
    assert decision["authority_granted"] is False
    assert decision["derived_authority_class"] == "UNVERIFIED"
    assert decision["derived_permission_state"] == "PERMISSION_BLOCKED"
    assert "evidence_adapter_not_registered" in decision["blockers"]
    assert "evidence_source_family_not_registered" in decision["blockers"]
    assert "caller_authority_upgrade_rejected" in decision["blockers"]
    assert "caller_permission_upgrade_rejected" in decision["blockers"]


def test_v1_authority_is_bound_to_exact_accepted_pool_receipt(operation):
    candidate = next(
        row
        for row in _final_pool(operation)["candidates"]
        if row["evidence_requirement_profile_id"] == "numeric_economic_release"
    )
    assert candidate["authority_state"] == "OFFICIAL_VERIFIED"
    assert candidate["reporting_allowed"] is True
    assert candidate["claim_authority_decisions"]
    for binding in candidate["evidence_bindings"]:
        assert binding["receipt"]["receipt_kind"] == "git_artifact"
        assert binding["receipt"]["exact_verified"] is True
        assert binding["receipt"]["producer_commit"] == (
            "8c63faca0603f81bebfbb68380a0dc4ad51ab87d"
        )


def test_every_real_candidate_has_exact_claim_document_citation_lineage(operation):
    for candidate in _final_pool(operation)["candidates"]:
        report = validate_claim_document_lineage(candidate)
        assert report["status"] == "PASS", report["blockers"]
        assert not report["unconsumed_authority_evidence_refs"]


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda row: row["claims"][0]["source_document_ids"].append("doc:missing"),
            "claim_source_document_missing",
        ),
        (
            lambda row: row["claims"][0]["citations"][0].update(
                {"url": "https://unauthorized.example/"}
            ),
            "citation_url_not_authorized_for_document",
        ),
        (
            lambda row: row["claims"][0]["evidence_refs"].append("ref:missing"),
            "claim_evidence_ref_unresolved",
        ),
        (
            lambda row: row["evidence_bindings"].append(
                copy.deepcopy(row["evidence_bindings"][0])
            ),
            "candidate_evidence_binding_ref_duplicate",
        ),
    ],
)
def test_lineage_mutations_fail_closed(operation, mutation, expected):
    candidate = copy.deepcopy(_final_pool(operation)["candidates"][0])
    mutation(candidate)
    report = validate_claim_document_lineage(candidate)
    assert report["status"] == "FAIL"
    assert any(expected in blocker for blocker in report["blockers"])


def test_cross_candidate_evidence_ref_reuse_fails_closed(operation):
    candidates = copy.deepcopy(_final_pool(operation)["candidates"][:2])
    candidates[1]["evidence_refs"] = [candidates[0]["evidence_refs"][0]]
    blockers = validate_pool_cross_candidate_lineage(candidates)
    assert any(row.startswith("cross_candidate_evidence_ref_reuse:") for row in blockers)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda row: row.update({"evidence_requirement_profile_id": "unknown"}),
            "evidence_profile_not_registered",
        ),
        (
            lambda row: row["capabilities"].update(
                {"claim_capabilities": ["event_occurrence"]}
            ),
            "candidate_capability_claim_type_mismatch",
        ),
        (
            lambda row: row["claims"].append(
                {
                    **copy.deepcopy(row["claims"][0]),
                    "claim_id": "claim:smuggled",
                    "claim_type": "market_reaction",
                }
            ),
            "profile_unsupported_extra_claim_type",
        ),
        (
            lambda row: row.update({"known_at_utc": None}),
            "profile_candidate_field_missing:known_at_utc",
        ),
    ],
)
def test_profile_execution_mutations_fail_closed(operation, authority, mutation, expected):
    candidate = copy.deepcopy(
        next(
            row
            for row in _final_pool(operation)["candidates"]
            if row["evidence_requirement_profile_id"] == "corporate_filing"
        )
    )
    mutation(candidate)
    report = validate_profile_execution(candidate, authority=authority)
    assert report["status"] == "FAIL"
    assert expected in report["blockers"]


def test_registered_optional_numeric_profile_composition_passes(operation, authority):
    candidate = next(
        row
        for row in _final_pool(operation)["candidates"]
        if row["evidence_requirement_profile_id"] == "numeric_economic_release"
    )
    report = validate_profile_execution(candidate, authority=authority)
    assert report["status"] == "PASS"


def test_arbitrary_market_evidence_strings_do_not_satisfy_contract(authority):
    record = {
        "schema_version": "contentops.governed_market_evidence_binding.v1",
        "market_evidence_id": "market:caller",
        "source_family_id": "caller_family",
        "adapter_id": "caller_adapter",
        "adapter_binding_record_id": "caller_record",
        "instrument_id": "instrument:caller",
        "evidence_classification": "EXACT",
        "observation_time_utc": "2026-07-14T00:00:00Z",
        "known_at_utc": "2026-07-14T00:00:00Z",
        "value": 1,
        "unit": "points",
        "evidence_refs": ["arbitrary:string"],
        "document_refs": ["doc:caller"],
    }
    record["logical_hash"] = logical_hash(record)
    blockers = validate_market_evidence_record(
        record,
        authority=authority,
        claim_evidence_refs=["arbitrary:string"],
        event_evidence_refs=[],
    )
    assert "market_evidence_adapter_not_registered" in blockers
    assert "market_evidence_source_family_not_registered" in blockers


def test_event_evidence_cannot_be_reused_as_market_evidence(authority):
    capability = authority.adapter_bindings[
        "contentops.market.governed_observation.v1"
    ]
    record = {
        "schema_version": "contentops.governed_market_evidence_binding.v1",
        "market_evidence_id": "market:verified",
        "source_family_id": capability["source_family_id"],
        "adapter_id": capability["adapter_id"],
        "adapter_binding_record_id": capability["record_id"],
        "instrument_id": "instrument:verified",
        "evidence_classification": "EXACT",
        "observation_time_utc": "2026-07-14T00:00:00Z",
        "known_at_utc": "2026-07-14T00:00:00Z",
        "value": 0,
        "unit": "points",
        "evidence_refs": ["ref:shared"],
        "document_refs": ["doc:market"],
    }
    record["logical_hash"] = logical_hash(record)
    blockers = validate_market_evidence_record(
        record,
        authority=authority,
        claim_evidence_refs=["ref:shared"],
        event_evidence_refs=["ref:shared"],
    )
    assert "market_evidence_reuses_event_evidence" in blockers
