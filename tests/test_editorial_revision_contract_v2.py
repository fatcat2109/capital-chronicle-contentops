from __future__ import annotations

import hashlib

from live_contentops.editorial_revision_contract_v2 import (
    REVISION_STAGES,
    build_editorial_revision_contract,
)


BODY = "Official data printed 5.0%. The implication remains conditional."


def _packet() -> dict:
    return {
        "numeric_claims": [{"claim_id": "claim-1", "public_claim_allowed": True}],
        "citation_map": {"claim-1": ["https://official.example/release"]},
    }


def _article() -> dict:
    return {"title": "Official data update", "rendered_body": BODY}


def _mappings() -> list[dict]:
    return [
        {"content_unit_id": "sentence-001", "content_unit_type": "fact", "claim_ids": ["claim-1"], "source_urls": ["https://official.example/release"]},
        {"content_unit_id": "sentence-002", "content_unit_type": "limitation", "claim_ids": [], "source_urls": []},
    ]


def _stages(content: str = BODY) -> list[dict]:
    return [
        {
            "stage_id": stage_id,
            "role": role,
            "decision": "PASS_NO_CHANGE",
            "input_content": content,
            "output_content": content,
            "changes": [],
            "unresolved_issues": [],
        }
        for stage_id, role in REVISION_STAGES
    ]


def _contract(*, mappings=None, stages=None, revision_required: bool = True) -> dict:
    revision_input = None if mappings is None and stages is None else {
        "content_unit_mappings": _mappings() if mappings is None else mappings,
        "revision_stages": _stages() if stages is None else stages,
    }
    return build_editorial_revision_contract(
        article=_article(),
        packet=_packet(),
        revision_input=revision_input,
        revision_required=revision_required,
    )


def test_revision_contract_passes_content_bound_public_claim_graph() -> None:
    result = _contract(mappings=_mappings(), stages=_stages())
    expected = hashlib.sha256(BODY.encode("utf-8")).hexdigest()
    assert result["status"] == "PASS"
    assert result["publication_authority"] is False
    assert result["claim_graph"]["content_unit_count"] == 2
    assert result["claim_graph"]["rendered_body_sha256"] == expected
    chain = result["revision_chain"]
    assert chain["revision_stage_count"] == 9
    assert chain["final_output_hash"] == expected
    assert chain["rendered_body_sha256"] == expected
    assert chain["stages"][1]["input_content_sha256"] == chain["stages"][0]["output_content_sha256"]


def test_revision_contract_fails_closed_for_unapproved_or_uncited_claim() -> None:
    mappings = _mappings()
    mappings[0]["claim_ids"] = ["invented"]
    result = _contract(mappings=mappings, stages=_stages())
    assert result["status"] == "BLOCK"
    assert "content_unit_unapproved_claim:sentence-001:invented" in result["blockers"]
    assert "content_unit_claim_missing_citation:sentence-001:invented" in result["blockers"]


def test_revision_contract_rejects_incomplete_stage_chain() -> None:
    result = _contract(mappings=_mappings(), stages=_stages()[:-1])
    assert result["status"] == "BLOCK"
    assert "revision_stage_missing:v8_final_release_candidate" in result["blockers"]
    assert "revision_stage_input_content_missing:v8_final_release_candidate" in result["blockers"]


def test_revision_contract_rejects_broken_content_link() -> None:
    stages = _stages()
    stages[0]["output_content"] = "Intermediate evidence outline."
    result = _contract(mappings=_mappings(), stages=stages)
    assert result["status"] == "BLOCK"
    assert "revision_stage_previous_output_link_broken:v1_evidence_outline" in result["blockers"]


def test_revision_contract_rejects_final_body_mismatch() -> None:
    stages = _stages("A different release candidate.")
    result = _contract(mappings=_mappings(), stages=stages)
    assert result["status"] == "BLOCK"
    assert "revision_chain_final_body_hash_mismatch" in result["blockers"]


def test_revision_contract_is_mandatory_by_default() -> None:
    result = _contract()
    assert result["status"] == "BLOCK"
    assert result["blockers"] == ["editorial_revision_v2_required"]
    assert result["claim_graph"]["content_units"] == []
    assert result["revision_chain"]["stages"] == []


def test_revision_contract_compatibility_noop_requires_explicit_opt_out() -> None:
    result = _contract(revision_required=False)
    assert result["status"] == "NOT_REQUESTED"
    assert result["blockers"] == []
    assert result["publication_authority"] is False
