from __future__ import annotations

from live_contentops.editorial_revision_contract_v2 import (
    REVISION_STAGES,
    build_editorial_revision_contract,
)


def _packet() -> dict:
    return {
        "numeric_claims": [{"claim_id": "claim-1", "public_claim_allowed": True}],
        "citation_map": {"claim-1": ["https://official.example/release"]},
    }


def _article() -> dict:
    return {"title": "Official data update", "rendered_body": "Official data printed 5.0%. The implication remains conditional."}


def _stages() -> list[dict]:
    return [
        {"stage_id": stage_id, "role": role, "decision": "PASS_NO_CHANGE", "changes": [], "unresolved_issues": []}
        for stage_id, role in REVISION_STAGES
    ]


def test_revision_contract_passes_hash_linked_public_claim_graph() -> None:
    result = build_editorial_revision_contract(
        article=_article(), packet=_packet(), revision_input={
            "content_unit_mappings": [
                {"content_unit_id": "sentence-001", "content_unit_type": "fact", "claim_ids": ["claim-1"], "source_urls": ["https://official.example/release"]},
                {"content_unit_id": "sentence-002", "content_unit_type": "limitation", "claim_ids": [], "source_urls": []},
            ],
            "revision_stages": _stages(),
        },
    )
    assert result["status"] == "PASS"
    assert result["publication_authority"] is False
    assert result["claim_graph"]["content_unit_count"] == 2
    assert result["revision_chain"]["revision_stage_count"] == 9
    stages = result["revision_chain"]["stages"]
    assert stages[1]["input_hash"] == stages[0]["output_hash"]


def test_revision_contract_fails_closed_for_unapproved_or_uncited_claim() -> None:
    result = build_editorial_revision_contract(
        article=_article(), packet=_packet(), revision_input={
            "content_unit_mappings": [
                {"content_unit_id": "sentence-001", "content_unit_type": "fact", "claim_ids": ["invented"], "source_urls": ["https://official.example/release"]},
                {"content_unit_id": "sentence-002", "content_unit_type": "limitation", "claim_ids": [], "source_urls": []},
            ],
            "revision_stages": _stages(),
        },
    )
    assert result["status"] == "BLOCK"
    assert "content_unit_unapproved_claim:sentence-001:invented" in result["blockers"]
    assert "content_unit_claim_missing_citation:sentence-001:invented" in result["blockers"]


def test_revision_contract_rejects_incomplete_stage_chain() -> None:
    result = build_editorial_revision_contract(
        article=_article(), packet=_packet(), revision_input={
            "content_unit_mappings": [
                {"content_unit_id": "sentence-001", "content_unit_type": "fact", "claim_ids": ["claim-1"], "source_urls": ["https://official.example/release"]},
                {"content_unit_id": "sentence-002", "content_unit_type": "limitation", "claim_ids": [], "source_urls": []},
            ],
            "revision_stages": _stages()[:-1],
        },
    )
    assert result["status"] == "BLOCK"
    assert "revision_stage_missing:v8_final_release_candidate" in result["blockers"]
