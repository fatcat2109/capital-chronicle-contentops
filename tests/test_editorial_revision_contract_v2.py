from __future__ import annotations

import hashlib

from live_contentops.editorial_revision_contract_v2 import (
    REVISION_STAGES,
    build_editorial_revision_contract,
)


BODY = "Official data printed 5.0%. The implication remains conditional."


def _packet() -> dict:
    return {
        "numeric_claims": [{
            "claim_id": "claim-1",
            "public_claim_allowed": True,
            "source_authority": "exact_official_public",
            "authority_scope": "official_release",
            "source_url": "https://official.example/release",
            "observation_time_utc": "2026-07-13T00:00:00Z",
            "known_at_utc": "2026-07-13T01:00:00Z",
        }],
        "citation_map": {"claim-1": ["https://official.example/release"]},
        "governed_contract": {"mode": "story_scoped_publication_evidence_v1"},
    }


def _article() -> dict:
    return {"title": "Official data update", "rendered_body": BODY}


def _mappings() -> list[dict]:
    return [
        {
            "content_unit_id": "sentence-001",
            "content_unit_type": "fact",
            "claim_ids": ["claim-1"],
            "source_urls": ["https://official.example/release"],
            "authority_class": "exact_official_public",
            "exact_proxy_context": "official_release",
            "inference_class": "none",
            "citation_rendering": "inline_source_link",
            "public_use_allowed": True,
            "observation_time_utc": "2026-07-13T00:00:00Z",
            "known_at_utc": "2026-07-13T01:00:00Z",
        },
        {
            "content_unit_id": "sentence-002",
            "content_unit_type": "limitation",
            "claim_ids": [],
            "source_urls": [],
        },
    ]


def _stages(content: str = BODY) -> list[dict]:
    return [
        {
            "stage_id": stage_id,
            "role": role,
            "decision": "PASS_NO_CHANGE",
            "input_content": content,
            "output_content": content,
            "structured_diff": [],
            "issues_addressed": [],
            "issues_introduced": [],
            "unresolved_issues": [],
            "model_or_rule_version": "contentops.editorial_revision_contract.v2",
            "deterministic_timestamp_utc": f"2026-07-13T{index:02d}:00:00Z",
        }
        for index, (stage_id, role) in enumerate(REVISION_STAGES)
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


def test_revision_contract_rejects_implicit_factual_authority_fields() -> None:
    mappings = _mappings()
    for field in ("authority_class", "exact_proxy_context", "inference_class", "citation_rendering", "public_use_allowed"):
        mappings[0].pop(field)
    result = _contract(mappings=mappings, stages=_stages())
    assert result["status"] == "BLOCK"
    assert "factual_content_unit_explicit_authority_class_required:sentence-001" in result["blockers"]
    assert "factual_content_unit_public_use_not_allowed:sentence-001" in result["blockers"]


def test_revision_contract_rejects_source_url_outside_claim_authority() -> None:
    mappings = _mappings()
    mappings[0]["source_urls"] = ["https://unapproved.example/post"]
    result = _contract(mappings=mappings, stages=_stages())
    assert result["status"] == "BLOCK"
    assert "content_unit_source_url_not_authorized:sentence-001:https://unapproved.example/post" in result["blockers"]


def test_revision_contract_rejects_pass_no_change_with_changed_output() -> None:
    stages = _stages()
    stages[0]["output_content"] = "Changed output."
    stages[1]["input_content"] = "Changed output."
    result = _contract(mappings=_mappings(), stages=stages)
    assert result["status"] == "BLOCK"
    assert "revision_stage_pass_no_change_hash_mismatch:v0_assignment_brief" in result["blockers"]


def test_revision_contract_rejects_revise_without_structured_diff() -> None:
    stages = _stages()
    stages[0]["decision"] = "REVISE"
    result = _contract(mappings=_mappings(), stages=stages)
    assert result["status"] == "BLOCK"
    assert "revision_stage_revise_requires_change_and_diff:v0_assignment_brief" in result["blockers"]
