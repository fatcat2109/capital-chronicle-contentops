from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_content_evidence_packet_v3 import (
    validate_content_evidence_packet_v3,
)

from live_contentops.editorial_review_orchestrator_v2 import ROLE_ORDER
from live_contentops.universal_evidence_receipt_verifier_v1 import (
    DBH2_RECEIPT_SCHEMA,
    GIT_RECEIPT_SCHEMA,
    EvidenceReceiptVerificationError,
    EvidenceReceiptVerifierV1,
    VerifiedEvidenceIndexV1,
    verify_runtime_implementation,
)
from live_contentops.governed_upstream_bridge_v1 import GovernedUpstreamBridgeV1
from live_contentops.universal_governed_registry_v1 import (
    build_exact_evidence_binding,
    derive_claim_authority_permission,
    load_governed_registry_authority,
)
from live_contentops.window_incremental_editorial_shadow_v1 import (
    build_window_incremental_editorial_shadow,
    enabled_discovery_routes,
    scan_verified_increment,
)


ROOT = Path(__file__).parents[1]
UPSTREAM_ROOT = (
    ROOT.parent.parent
    / "Headline Raw data local json"
    / "capital-chronicle-ingestion"
)
OBSERVED_UPSTREAM_HEAD = "1700520800e8c847b7446e196c384a43dd2a6a58"


@pytest.fixture(scope="module")
def authority():
    return load_governed_registry_authority(repo_root=ROOT)


@pytest.fixture(scope="module")
def operation():
    if not (UPSTREAM_ROOT / ".git").exists():
        pytest.skip("governed upstream worktree unavailable")
    return build_window_incremental_editorial_shadow(
        repo_root=ROOT,
        upstream_root=UPSTREAM_ROOT,
        observed_upstream_head=OBSERVED_UPSTREAM_HEAD,
    )


def test_discovery_routes_are_append_only_runtime_exact_records(authority):
    routes = enabled_discovery_routes(authority)
    assert len(routes) == 6
    assert all(row["record_id"].endswith(":v4") for row in routes)
    for route in routes:
        implementation = verify_runtime_implementation(
            repo_root=ROOT,
            observed_commit=authority.observed_commit,
            implementation_receipt=route["implementation_receipt"],
            expected_identity=route["implementation_identity"],
        )
        assert callable(implementation)


def test_fabricated_legacy_receipt_cannot_impersonate_verifier(authority):
    adapter = authority.adapter_bindings[
        "contentops.v1_newsroom_candidate_pool_adapter.v1"
    ]
    binding = build_exact_evidence_binding(
        binding_id="binding:forged",
        accepted_evidence_binding_id=adapter["accepted_evidence_binding"],
        evidence_ref="ref:forged",
        source_family_id=adapter["source_family_id"],
        adapter_id=adapter["adapter_id"],
        adapter_binding_record_id=adapter["record_id"],
        document_id="doc:forged",
        source_native_id="native:forged",
        content_sha256="a" * 64,
        source_native_status="eligible",
        evidence_state="exact",
        consumer_permission="PUBLIC_CLAIM_ALLOWED",
        dqr_reporting_allowed=True,
        receipt={"receipt_kind": "git_artifact", "exact_verified": True},
    )
    decision = derive_claim_authority_permission(
        authority=authority,
        claim_type="factual_text",
        evidence_bindings=[binding],
        trusted_evidence_index={"ref:forged": binding},
        requested_authority="OFFICIAL_VERIFIED",
        requested_permission="PUBLIC_CLAIM_ALLOWED",
    )
    assert decision["authority_granted"] is False
    assert decision["derived_authority_class"] == "UNVERIFIED"
    assert decision["derived_permission_state"] == "PERMISSION_BLOCKED"
    assert "trusted_evidence_index_not_verifier_produced" in decision["blockers"]
    assert "evidence_binding_schema_invalid" in decision["blockers"]


def test_verified_index_constructor_and_external_mutation_are_closed():
    with pytest.raises(
        EvidenceReceiptVerificationError,
        match="verified_evidence_index_constructor_forbidden",
    ):
        VerifiedEvidenceIndexV1(object())


def test_runtime_receipt_rejects_invoked_callable_mismatch(authority):
    route = enabled_discovery_routes(authority)[0]
    receipt = copy.deepcopy(route["implementation_receipt"])
    with pytest.raises(
        EvidenceReceiptVerificationError,
        match="implementation_receipt_callable_mismatch",
    ):
        verify_runtime_implementation(
            repo_root=ROOT,
            observed_commit=authority.observed_commit,
            implementation_receipt=receipt,
            expected_identity=(
                "live_contentops.window_incremental_editorial_shadow_v1."
                "adapt_verified_v1_candidate_pool_v2"
            ),
        )


def _real_verifier(authority):
    if not (UPSTREAM_ROOT / ".git").exists():
        pytest.skip("governed upstream worktree unavailable")
    bridge = GovernedUpstreamBridgeV1(
        root=UPSTREAM_ROOT,
        observed_head=OBSERVED_UPSTREAM_HEAD,
    )
    bridge.verify_all_local_artifacts()
    return bridge, EvidenceReceiptVerifierV1(
        authority=authority,
        primary_root=ROOT,
        upstream_root=UPSTREAM_ROOT,
        observed_upstream_head=OBSERVED_UPSTREAM_HEAD,
        bridge=bridge,
    )


def test_dbh2_receipt_rejects_future_known_record(authority):
    bridge, verifier = _real_verifier(authority)
    record = bridge.select_record(
        target_id="DBH2_USGS_SIGNIFICANT_GLOBAL",
        provider_record_type="usgs_event",
        cutoff_utc="2026-07-10T07:30:00Z",
        required_status="reviewed",
    )
    with pytest.raises(
        EvidenceReceiptVerificationError,
        match="dbh2_verified_record_future_known_at",
    ):
        verifier.verify_dbh2_record_binding(
            record=record,
            source_family_id="dbh2_usgs_official_physical_event",
            adapter_id="contentops.dbh2.usgs_event.v1",
            verification_cutoff_utc="2026-07-10T00:30:00Z",
        )


def test_real_dbh2_verifier_rejects_consumer_permission_upgrade(authority):
    bridge, verifier = _real_verifier(authority)
    record = bridge.select_record(
        target_id="DBH2_USGS_SIGNIFICANT_GLOBAL",
        provider_record_type="usgs_event",
        cutoff_utc="2026-07-10T07:30:00Z",
        required_status="reviewed",
    )
    with pytest.raises(
        EvidenceReceiptVerificationError,
        match="dbh2_requested_consumer_permission_mismatch",
    ):
        verifier.verify_dbh2_record_binding(
            record=record,
            source_family_id="dbh2_usgs_official_physical_event",
            adapter_id="contentops.dbh2.usgs_event.v1",
            requested_consumer_permission="PUBLIC_CLAIM_ALLOWED",
        )


def test_real_dbh2_verifier_rejects_dqr_reporting_upgrade(authority):
    bridge, verifier = _real_verifier(authority)
    record = bridge.select_record(
        target_id="DBH2_USGS_SIGNIFICANT_GLOBAL",
        provider_record_type="usgs_event",
        cutoff_utc="2026-07-10T07:30:00Z",
        required_status="reviewed",
    )
    with pytest.raises(
        EvidenceReceiptVerificationError,
        match="dbh2_requested_dqr_reporting_state_mismatch",
    ):
        verifier.verify_dbh2_record_binding(
            record=record,
            source_family_id="dbh2_usgs_official_physical_event",
            adapter_id="contentops.dbh2.usgs_event.v1",
            requested_dqr_reporting_allowed=True,
        )


def test_generic_scanner_contains_no_fixed_target_or_record_identity():
    source = inspect.getsource(scan_verified_increment)
    assert "DBH2_USGS_SIGNIFICANT_GLOBAL" not in source
    assert "DBH2_FEDERAL_REGISTER_SEC" not in source
    assert "stable_record_id =" not in source
    assert "CORRECTION_STABLE_ID" not in source


def test_six_real_days_are_pooled_at_every_five_window_cutoff(operation):
    assert operation["summary"]["history_day_count"] == 6
    assert operation["summary"]["window_count"] == 30
    assert len(operation["candidate_pools"]) == 30
    assert len(operation["window_decisions"]) == 30
    assert all(
        pool["cutoff_time_utc"] == ledger["cutoff_utc"]
        for pool, ledger in zip(
            operation["candidate_pools"],
            operation["window_ledger"],
        )
    )


def test_between_window_entries_are_discovered_at_next_window(operation):
    by_cutoff = {
        row["cutoff_utc"]: row for row in operation["window_ledger"]
    }
    assert by_cutoff["2026-07-10T07:30:00Z"]["new_candidate_count"] == 2
    assert by_cutoff["2026-07-12T13:30:00Z"]["new_candidate_count"] == 2


def test_incremental_cursor_has_no_duplicates_and_updates_reenter(operation):
    discovered = [
        candidate_id
        for row in operation["window_ledger"]
        for candidate_id in row["new_candidate_ids"]
    ]
    assert len(discovered) == len(set(discovered))
    assert operation["summary"]["duplicate_discovery_count"] == 0
    probe = operation["historical_update_probe"]
    assert probe["later_version_reentered"] is True
    assert probe["candidate_relationships"] == ["initial_event", "correction"]
    assert probe["initial_version_id"] != probe["reentered_version_id"]
    assert probe["relationship"]["relation_type"] == "corrects"


def test_every_authority_binding_has_a_typed_verifier_receipt(operation):
    schemas = {
        binding["receipt"]["schema_version"]
        for binding in operation["trusted_evidence_index"].values()
    }
    assert schemas == {DBH2_RECEIPT_SCHEMA, GIT_RECEIPT_SCHEMA}
    assert all(
        binding["verifier_produced"] is True
        for binding in operation["trusted_evidence_index"].values()
    )


def test_context_only_candidates_abstain_from_article_generation(operation):
    abstentions = operation["context_only_abstentions"]
    assert len(abstentions) == operation["summary"][
        "context_only_candidate_count"
    ]
    assert all(
        row["disposition"] == "ABSTAIN_CONTEXT_ONLY_OR_UNAUTHORIZED"
        and row["article"] is None
        and row["publication_authority"] is False
        for row in abstentions
    )


def test_assigned_candidate_handoff_is_v3_lineage_bound_and_holds_without_gates(
    operation,
):
    handoff = operation["editorial_shadow_handoff"]
    packet = handoff["evidence_packet"]
    article = handoff["article"]
    review = handoff["editorial_review"]
    graph = packet["governed_claim_graph"]

    assert handoff["disposition"] == "LOCAL_SHADOW_DRAFT_HELD"
    assert handoff["evidence_packet_contract"] == (
        "V3_GENERIC_WITH_EXACT_V2_COMPATIBILITY_PROJECTION"
    )
    assert packet["validation_blockers"] == []
    assert validate_content_evidence_packet_v3(packet) == []
    assert packet["numeric_claims"] == packet[
        "v2_compatibility_projection"
    ]["numeric_claims"]
    assert packet["provenance"]["evidence_refs"]
    assert set(article["claim_ids_used"]) == set(graph["approved_claim_ids"])
    assert handoff["canonical_role_order"] == list(ROLE_ORDER)
    assert review["role_order"] == list(ROLE_ORDER)
    assert review["status"] == "BLOCK"
    assert review["editorial_disposition"] == "HOLD"
    assert handoff["freshness_decision"]["decision"] == "BLOCK"
    assert handoff["visual_decision"]["status"] == "BLOCK"
    assert "market_sensitive_story_snapshot_stale_or_missing" in review[
        "blockers"
    ]
    assert "fewer_than_three_useful_visuals" in review["blockers"]


def test_v3_packet_schema_and_permission_mutation_fail_closed(operation):
    jsonschema = pytest.importorskip("jsonschema")
    packet = operation["editorial_shadow_handoff"]["evidence_packet"]
    schema = json.loads(
        (ROOT / "schemas/CapitalChronicleContentEvidencePacketV3.schema.json")
        .read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator(schema).validate(packet)

    mutated = copy.deepcopy(packet)
    mutated["governed_claim_graph"]["claims"][0][
        "permission_state"
    ] = "PERMISSION_BLOCKED"
    blockers = validate_content_evidence_packet_v3(mutated)
    assert any("logical_hash_mismatch" in value for value in blockers)
    assert any("approval_decision_mismatch" in value for value in blockers)


def test_context_only_v3_packets_remain_explicit_abstentions(operation):
    for abstention in operation["context_only_abstentions"]:
        packet = abstention["evidence_packet"]
        assert packet["schema_version"] == (
            "capital_chronicle_content_evidence_packet.v3"
        )
        assert packet["v2_compatibility_projection"]["schema_version"] == (
            "capital_chronicle_content_evidence_packet.v2"
        )
        assert packet["generic_claim_permissions"]["decision"] == "BLOCK"
        assert abstention["article"] is None
        assert abstention["editorial_review"] is None


def test_operation_preserves_zero_write_and_advanced_branch_receipt(operation):
    assert operation["observed_upstream_head"] == OBSERVED_UPSTREAM_HEAD
    assert operation["later_observed_upstream_branch_head"] != (
        OBSERVED_UPSTREAM_HEAD
    )
    assert operation["summary"]["publication_count"] == 0
    assert operation["summary"]["public_write_count"] == 0
    assert operation["summary"]["upstream_write_count"] == 0
    assert operation["publication_authority"] is False
    assert operation["network_intake_performed"] is False
    assert operation["credential_read_performed"] is False
