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


