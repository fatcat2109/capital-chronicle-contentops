from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from live_contentops import universal_evidence_receipt_verifier_v1 as verifier_module
from live_contentops.editorial_review_orchestrator_v2 import ROLE_ORDER
from live_contentops.governed_upstream_bridge_v1 import GitArtifactReceipt
from live_contentops.nonnumeric_story_authority_consumer_v1 import (
    ADAPTER_ID,
    AUTHORIZED_CLAIM_IDS,
    SOURCE_FAMILY_ID,
    UPSTREAM_PACKET_PATH,
    UPSTREAM_PRODUCER_COMMIT,
    build_nonnumeric_story_candidate_v1,
    build_nonnumeric_story_shadow_packet_v1,
)
from live_contentops.universal_evidence_receipt_verifier_v1 import (
    EvidenceReceiptVerificationError,
    EvidenceReceiptVerifierV1,
)
from live_contentops.universal_governed_registry_v1 import load_governed_registry_authority


ROOT = Path(__file__).parents[1]
EXPECTED_PACKET_ID = "cc-nonnumeric-f93c722c9c8f46741bb8"
EXPECTED_DOCUMENT_SHA256 = (
    "63641fe4cec40cad1834708798b51ca38de3739f16756123de1dd8eaafe74f30"
)
EXPECTED_CLAIMS = [
    {
        "claim_id": "claim-bfca0e50bb4f64d0",
        "claim_type": "official_regulatory_action",
        "contains_numeric_assertion": False,
        "interpretation_allowed": False,
        "reporting_allowed": True,
        "source_field": "selected_raw_record.abstract",
        "text": (
            "The OCC, Board, FDIC, NCUA, CFPB, FHFA, CFTC, SEC, and Treasury "
            "are publishing a final joint rule to establish data standards to "
            "promote interoperability of financial regulatory data across these agencies."
        ),
    },
    {
        "claim_id": "claim-1936ed019eb6602d",
        "claim_type": "official_regulatory_limitation",
        "contains_numeric_assertion": False,
        "interpretation_allowed": False,
        "reporting_allowed": True,
        "source_field": "selected_raw_record.abstract",
        "text": (
            "At the effective date, the joint rule will not change any reporting "
            "requirements without further action by the agencies."
        ),
    },
]


def _packet() -> dict[str, object]:
    packet: dict[str, object] = {
        "claims": copy.deepcopy(EXPECTED_CLAIMS),
        "consumer_permissions": {
            "authorized_claim_ids": list(AUTHORIZED_CLAIM_IDS),
            "consumer_class": "contentops_publication",
            "decision": "PASS_STORY_SCOPED_NONNUMERIC_REPORTING",
            "derived_from_verifier": True,
            "dispatch_allowed": False,
            "exact_story_only": True,
            "financial_advice_allowed": False,
            "forecast_allowed": False,
            "global_dqr_override": False,
            "numeric_reporting_allowed": False,
            "reporting_allowed": True,
            "source_family_wide_authority": False,
            "trading_allowed": False,
        },
        "generated_at_utc": "2026-07-12T16:18:42.619968+00:00",
        "lineage": {
            "is_corrected": False,
            "is_current_version": True,
            "is_superseded": False,
            "is_withdrawn": False,
            "relationship_count": 0,
            "relationships": [],
        },
        "ofac_boundary": {
            "promotion_allowed": False,
            "reporting_authority": False,
            "status": "context_only_current_snapshot_not_history",
        },
        "packet_id": EXPECTED_PACKET_ID,
        "protected_state": {
            "analyzer_authority_changed": False,
            "current_canonical_authority_changed": False,
            "global_dqr_override": False,
            "global_dqr_status": "BLOCKED",
            "protected_state_mutation_count": 0,
            "source_family_promoted": False,
        },
        "public_use_scope": {
            "attribution_required": True,
            "basis": "official_federal_register_and_govinfo_public_record",
            "copyright_ownership_adjudicated": False,
            "decision": "PASS_OFFICIAL_PUBLIC_RECORD_FACTUAL_REPORTING",
            "scope": "quote_or_paraphrase_packet_claims_with_official_source_attribution",
        },
        "schema_version": "capital_chronicle.nonnumeric_story_scoped_reporting_authority.v1",
        "selected_story": {
            "authorized_public_use_url": "https://www.govinfo.gov/content/pkg/FR-2026-06-25/pdf/2026-12787.pdf",
            "candidate_only": True,
            "canonical_url": "https://www.federalregister.gov/documents/2026/06/25/2026-12787/financial-data-transparency-act-joint-data-standards",
            "content_sha256": EXPECTED_DOCUMENT_SHA256,
            "current_canonical_apply": False,
            "document_type": "Rule",
            "exact_numeric_authority": False,
            "numeric_boundary": "numeric_text_not_numeric_truth",
            "official_family": "federal_register",
            "provider": "Federal Register",
            "provider_record_id": "2026-12787",
            "provider_record_type": "federal_register_document",
            "stable_record_id": "cf9b73452130757eb3552a87bf86bf6d8bc5531c263d4d7dabad7a1169345d09",
            "target_id": "DBH2_FEDERAL_REGISTER_FED_SYSTEM",
            "title": "Financial Data Transparency Act Joint Data Standards",
            "version_id": "a6554c195bb3e7840fb66fbe986cd0f23f0a85a320d8ef4ddf8ce7346b116701",
        },
        "source_receipt": {
            "parquet_sha256": "e2792c34a09e46426d09ac8708592b4e123267ac7a295c85e90a1b0f739bd62f",
            "raw_hash_verified": True,
            "raw_manifest_id": "f59dcfa634f4aab184e60869d5718519071310139e92a8a0afe65355f7083415",
            "raw_manifest_ref": "docs/research/database_foundation/public_free_event_text_entity_history_v1/DBH2_RAW_MANIFEST_INDEX_V1.json",
            "raw_retrieved_at_utc": "2026-07-12T16:18:42.619968+00:00",
            "raw_sha256": "5bb10637207641d5b562909f0a115e873fc75bb1a250a375586bad837a29cf2a",
        },
        "task_id": "TASK_DATABASE_NONNUMERIC_STORY_SCOPED_REPORTING_AUTHORITY_V1",
        "terminal_status": "PASS_NONNUMERIC_STORY_SCOPED_REPORTING_AUTHORITY_V1_AWAITING_CHATGPT_AUDIT",
        "timestamps": {
            "event_at": "2026-06-25",
            "event_precision": "DAY",
            "known_at_precision": "MICROSECOND",
            "known_at_utc": "2026-07-12T16:18:42.619968+00:00",
            "provider_updated_at": "2026-06-25",
            "published_at": "2026-06-25",
            "published_precision": "DAY",
            "revision_precision": "DAY",
        },
        "verifier": {
            "blockers": [],
            "checks": {
                "claims_exact_and_attributed": True,
                "claims_strictly_nonnumeric": True,
            },
            "status": "PASS",
        },
    }
    packet["logical_hash"] = verifier_module._logical_hash(packet)
    return packet


def _exact_git_receipt(content: bytes) -> GitArtifactReceipt:
    return GitArtifactReceipt(
        repository="fatcat2109/Headline-Raw-data-json",
        branch="main",
        observed_head="observed-upstream-head",
        producer_commit=UPSTREAM_PRODUCER_COMMIT,
        artifact_path=UPSTREAM_PACKET_PATH,
        git_blob_sha1="git-blob-sha1",
        byte_sha256=verifier_module.sha256(content).hexdigest(),
        byte_length=len(content),
    )


@pytest.fixture
def verifier(monkeypatch):
    authority = load_governed_registry_authority(repo_root=ROOT)
    packet = _packet()
    content = json.dumps(packet, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def fake_read_git_artifact(**kwargs):
        assert kwargs["artifact_path"] == UPSTREAM_PACKET_PATH
        assert kwargs["producer_commit"] == UPSTREAM_PRODUCER_COMMIT
        return content, _exact_git_receipt(content)

    monkeypatch.setattr(verifier_module, "read_git_artifact", fake_read_git_artifact)
    monkeypatch.setattr(verifier_module, "_verify_origin", lambda *args: None)
    instance = EvidenceReceiptVerifierV1(
        authority=authority,
        primary_root=ROOT,
        upstream_root=ROOT,
        observed_upstream_head="observed-upstream-head",
        bridge=SimpleNamespace(branch="main"),
    )
    return instance, packet


def _verify(verifier):
    return verifier.verify_nonnumeric_story_authority_bindings(
        artifact_path=UPSTREAM_PACKET_PATH,
        producer_commit=UPSTREAM_PRODUCER_COMMIT,
        source_family_id=SOURCE_FAMILY_ID,
        adapter_id=ADAPTER_ID,
        requested_claim_ids=AUTHORIZED_CLAIM_IDS,
        requested_consumer_permission="PUBLIC_CLAIM_ALLOWED",
        requested_dqr_reporting_allowed=True,
    )


def test_exact_git_receipt_binds_packet_identity_and_claim_set(verifier):
    instance, packet = verifier
    bindings = _verify(instance)

    assert len(bindings) == 2
    assert tuple(row["receipt"]["authorized_claim_ids"] for row in bindings) == (
        list(AUTHORIZED_CLAIM_IDS),
        list(AUTHORIZED_CLAIM_IDS),
    )
    assert all(row["verifier_produced"] is True for row in bindings)
    assert all(row["receipt"]["verified_from_exact_git_bytes"] is True for row in bindings)
    assert all(row["receipt"]["packet_id"] == packet["packet_id"] for row in bindings)
    assert all(row["receipt"]["producer_commit"] == UPSTREAM_PRODUCER_COMMIT for row in bindings)
    assert all(row["receipt"]["artifact_path"] == UPSTREAM_PACKET_PATH for row in bindings)
    assert all(row["receipt"]["packet_logical_hash"] == packet["logical_hash"] for row in bindings)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("claims", [{"claim_id": "claim-forged"}], "nonnumeric_story_exact_claim_set_mismatch"),
        ("protected_state", {"global_dqr_override": True}, "nonnumeric_story_protected_state_mismatch"),
        (
            "consumer_permissions",
            {"reporting_allowed": True, "numeric_reporting_allowed": True},
            "nonnumeric_story_consumer_permission_mismatch",
        ),
        ("lineage", {"is_corrected": True}, "nonnumeric_story_current_lineage_mismatch"),
    ],
)
def test_packet_mutations_fail_closed_at_the_mutated_authority_boundary(
    verifier, monkeypatch, field, value, expected
):
    instance, packet = verifier
    mutated = copy.deepcopy(packet)
    mutated[field] = value
    mutated["logical_hash"] = verifier_module._logical_hash(
        {key: item for key, item in mutated.items() if key != "logical_hash"}
    )
    content = json.dumps(mutated, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def mutated_read(**kwargs):
        return content, _exact_git_receipt(content)

    monkeypatch.setattr(verifier_module, "read_git_artifact", mutated_read)
    with pytest.raises(EvidenceReceiptVerificationError, match=expected):
        _verify(instance)


def test_requested_permission_escalation_and_dqr_override_are_rejected(verifier):
    instance, _ = verifier
    with pytest.raises(
        EvidenceReceiptVerificationError,
        match="nonnumeric_story_requested_consumer_permission_mismatch",
    ):
        instance.verify_nonnumeric_story_authority_bindings(
            artifact_path=UPSTREAM_PACKET_PATH,
            producer_commit=UPSTREAM_PRODUCER_COMMIT,
            source_family_id=SOURCE_FAMILY_ID,
            adapter_id=ADAPTER_ID,
            requested_claim_ids=AUTHORIZED_CLAIM_IDS,
            requested_consumer_permission="REPORTING_ALLOWED",
        )
    with pytest.raises(
        EvidenceReceiptVerificationError,
        match="nonnumeric_story_requested_dqr_reporting_state_mismatch",
    ):
        instance.verify_nonnumeric_story_authority_bindings(
            artifact_path=UPSTREAM_PACKET_PATH,
            producer_commit=UPSTREAM_PRODUCER_COMMIT,
            source_family_id=SOURCE_FAMILY_ID,
            adapter_id=ADAPTER_ID,
            requested_claim_ids=AUTHORIZED_CLAIM_IDS,
            requested_consumer_permission="PUBLIC_CLAIM_ALLOWED",
            requested_dqr_reporting_allowed=False,
        )


def test_consumer_projects_verifier_permissions_without_global_promotion(verifier):
    instance, _ = verifier
    candidate, validation = build_nonnumeric_story_candidate_v1(
        authority=instance.authority,
        verifier=instance,
        cutoff_utc="2026-07-12T16:18:42.619968+00:00",
    )

    assert validation["status"] == "PASS"
    assert candidate["authority_state"] == "OFFICIAL_VERIFIED"
    assert candidate["reporting_allowed"] is True
    assert candidate["publication_authority"] is False
    assert candidate["public_write_allowed"] is False
    assert candidate["global_dqr_override"] is False
    assert candidate["dispatch_allowed"] is False
    assert candidate["numeric_claims"] == []
    assert candidate["limitations"][-3:] == [
        "global_dqr_remains_blocked",
        "ofac_context_only",
        "candidate_grants_no_publication_authority",
    ]
    assert [claim["claim_id"] for claim in candidate["claims"]] == list(AUTHORIZED_CLAIM_IDS)
    assert [claim["claim_type"] for claim in candidate["claims"]] == [
        "legal_or_regulatory_action",
        "factual_text",
    ]
    assert all(claim["permission_state"] == "PUBLIC_CLAIM_ALLOWED" for claim in candidate["claims"])


def test_canonical_shadow_executes_all_roles_and_preserves_protected_state(verifier):
    instance, _ = verifier
    result = build_nonnumeric_story_shadow_packet_v1(
        authority=instance.authority,
        verifier=instance,
        generated_at_utc="2026-07-12T16:18:42.619968+00:00",
    )
    handoff = result["handoff"]
    review = handoff["editorial_review"]

    assert tuple(handoff["canonical_role_order"]) == ROLE_ORDER
    assert tuple(review["role_order"]) == ROLE_ORDER
    assert [row["role"] for row in review["roles"]] == list(ROLE_ORDER)
    assert handoff["publication_authority"] is False
    assert handoff["public_write_performed"] is False
    assert result["global_dqr_status"] == "BLOCKED"
    assert result["global_dqr_override"] is False
    assert result["ofac_context_only"] is True
    assert result["numeric_reporting_allowed"] is False
    assert result["interpretation_allowed"] is False
    assert result["dispatch_allowed"] is False
    assert handoff["evidence_packet"]["governed_claim_graph"]["approved_claim_ids"] == list(
        AUTHORIZED_CLAIM_IDS
    )
    assert handoff["article"]["claim_ids_used"] == list(AUTHORIZED_CLAIM_IDS)
    assert handoff["article"]["numeric_claims_from_llm"] is False
