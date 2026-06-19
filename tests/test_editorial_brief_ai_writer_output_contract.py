from dataclasses import replace

import pytest

from live_contentops import content_idea_intent_parser_contract as parser
from live_contentops import editorial_brief_ai_writer_output_contract as contract


def build_ready_brief(text="Idea: create a Substack newsletter and X thread about source trust before CPI commentary."):
    raw = parser.build_raw_operator_input(
        text,
        source_context_refs=("source:0174U0",),
        evidence_refs=("docs/automation/0174U0/heavy_strategy_recon_report.md",),
    )
    idea = parser.build_content_idea_packet(
        raw,
        citation_refs=("source:0174U0",),
        limitation_notes=("source context required before public claims",),
    )
    intent = parser.parse_local_intent(raw, idea)
    return contract.build_editorial_brief(idea, intent), idea, intent


def assert_safety_false(flags):
    for flag in contract.SAFETY_FALSE_FLAGS:
        assert flags[flag] is False
    assert flags["deterministic_local_only"] is True


def test_valid_idea_intent_builds_review_only_editorial_brief():
    brief, idea, intent = build_ready_brief()

    assert brief.brief_id.startswith("brief_")
    assert brief.source_idea_id == idea.idea_id
    assert brief.source_intent_id == intent.intent_id
    assert brief.target_platforms == ("substack_newsletter", "x")
    assert brief.target_payload_classes == ("substack_newsletter_issue", "x_thread")
    assert brief.human_review_required is True
    assert brief.public_postable is False
    assert brief.dispatch_ready is False
    assert brief.blocked_reasons == ()
    assert_safety_false(brief.safety_flags)


def test_approval_like_intent_blocks_editorial_brief():
    raw = parser.build_raw_operator_input("Approve this X thread about process limits")
    idea = parser.build_content_idea_packet(raw)
    intent = parser.parse_local_intent(raw, idea)
    brief = contract.build_editorial_brief(idea, intent)

    assert "approval_bypass_blocked" in brief.blocked_reasons
    assert "intent_class_not_allowed_for_editorial_brief" in brief.blocked_reasons


def test_dispatch_like_intent_blocks_editorial_brief():
    raw = parser.build_raw_operator_input("Post now this X thread about process limits")
    idea = parser.build_content_idea_packet(raw)
    intent = parser.parse_local_intent(raw, idea)
    brief = contract.build_editorial_brief(idea, intent)

    assert "dispatch_bypass_blocked" in brief.blocked_reasons
    assert "dispatch_like_intent_not_allowed_for_editorial_brief" in brief.blocked_reasons


def test_forbidden_signal_language_blocks_editorial_brief():
    raw = parser.build_raw_operator_input("Create X post with a buy signal and price target")
    idea = parser.build_content_idea_packet(raw)
    intent = parser.parse_local_intent(raw, idea)
    brief = contract.build_editorial_brief(idea, intent)

    assert "advice_or_signal_forbidden_blocks_editorial_brief" in brief.blocked_reasons


def test_artifact_gate_blocks_editorial_brief():
    raw = parser.build_raw_operator_input("Internal alpha artifact DQR readiness report for Substack")
    idea = parser.build_content_idea_packet(raw)
    intent = parser.parse_local_intent(raw, idea)
    brief = contract.build_editorial_brief(idea, intent)

    assert "artifact_gate_blocks_editorial_brief" in brief.blocked_reasons


def test_deterministic_fixture_writer_output_validates():
    brief, _, _ = build_ready_brief()
    output = contract.build_deterministic_fixture_writer_output(brief)
    validation = contract.validate_ai_writer_output(brief, output)

    assert output.writer_mode == "deterministic_fixture"
    assert output.output_hash_algorithm == contract.OUTPUT_HASH_ALGORITHM
    assert output.public_postable is False
    assert output.approval_ready is False
    assert output.dispatch_ready is False
    assert validation.validation_status == contract.VALIDATION_READY
    assert validation.no_provider_defaults_pass is True
    assert_safety_false(output.safety_flags)


def test_manual_external_llm_paste_validates_when_preserved():
    brief, _, _ = build_ready_brief()
    output = contract.build_manual_external_llm_paste_packet(
        brief,
        title_candidates=("Source trust before CPI commentary",),
        hook_candidates=("Treat CPI as context, not a signal.",),
        seo_keywords=("source trust", "CPI context"),
        seo_title="Source trust before CPI commentary",
        seo_description="Review-only education draft preserving sources and limitations.",
        platform_fit_notes={platform: f"registry_fit:{platform}" for platform in brief.target_platforms},
        draft_bodies={platform: contract._draft_body(brief, platform) for platform in brief.target_platforms},
    )
    validation = contract.validate_ai_writer_output(brief, output)

    assert output.writer_mode == "manual_external_llm_paste"
    assert validation.validation_status == contract.VALIDATION_READY


def test_provider_future_gate_mode_blocks():
    brief, _, _ = build_ready_brief()
    output = contract.build_provider_future_gate_blocked_packet(brief)
    validation = contract.validate_ai_writer_output(brief, output)

    assert "writer_mode_provider_future_gate_blocked" in validation.blocked_reasons
    assert validation.writer_mode_allowed is False


def test_missing_citations_block_when_required():
    brief, _, _ = build_ready_brief()
    output = contract.build_deterministic_fixture_writer_output(brief)
    draft = replace(output.draft_variants[0], citation_refs=())
    output = replace(output, draft_variants=(draft, *output.draft_variants[1:]), citation_refs_used=())
    validation = contract.validate_ai_writer_output(brief, output)

    assert "required_citations_missing" in validation.blocked_reasons


def test_missing_limitations_block_when_required():
    brief, _, _ = build_ready_brief()
    output = contract.build_deterministic_fixture_writer_output(brief)
    output = replace(output, limitation_notes_preserved=())
    validation = contract.validate_ai_writer_output(brief, output)

    assert "required_limitations_missing" in validation.blocked_reasons


def test_missing_disclaimers_block():
    brief, _, _ = build_ready_brief()
    output = contract.build_deterministic_fixture_writer_output(brief)
    output = replace(output, disclaimers_preserved=())
    validation = contract.validate_ai_writer_output(brief, output)

    assert "required_disclaimers_missing" in validation.blocked_reasons


def test_hallucinated_citation_ref_blocks():
    brief, _, _ = build_ready_brief()
    output = contract.build_deterministic_fixture_writer_output(brief)
    output = replace(output, citation_refs_used=("source:0174U0", "source:fake"), source_hallucination_risk=True)
    validation = contract.validate_ai_writer_output(brief, output)

    assert "hallucinated_source_ref_detected" in validation.blocked_reasons


def test_forbidden_claim_language_blocks():
    brief, _, _ = build_ready_brief()
    output = contract.build_manual_external_llm_paste_packet(
        brief,
        title_candidates=("Buy this setup",),
        hook_candidates=("This is a trading signal.",),
        seo_keywords=("signal",),
        seo_title="Buy this setup",
        seo_description="Price target included.",
        platform_fit_notes={platform: f"registry_fit:{platform}" for platform in brief.target_platforms},
        draft_bodies={platform: "Buy now. " + contract._draft_body(brief, platform) for platform in brief.target_platforms},
    )
    validation = contract.validate_ai_writer_output(brief, output)

    assert "forbidden_claim_language_detected" in validation.blocked_reasons


def test_draft_variants_remain_review_only_and_compatible():
    brief, _, _ = build_ready_brief()
    output = contract.build_deterministic_fixture_writer_output(brief)

    assert all(draft.review_status == contract.REVIEW_ONLY for draft in output.draft_variants)
    assert all(draft.public_postable is False for draft in output.draft_variants)
    assert all(draft.approval_ready is False for draft in output.draft_variants)
    assert all(draft.dispatch_ready is False for draft in output.draft_variants)
    assert contract.validate_ai_writer_output(brief, output).all_drafts_review_only is True


def test_output_hash_is_deterministic_and_changes_on_material_changes():
    brief, _, _ = build_ready_brief()
    first = contract.build_deterministic_fixture_writer_output(brief)
    second = contract.build_deterministic_fixture_writer_output(brief)
    changed = contract.build_manual_external_llm_paste_packet(
        brief,
        title_candidates=("Changed title",),
        hook_candidates=("Treat CPI as context, not a signal.",),
        seo_keywords=("source trust",),
        seo_title="Changed title",
        seo_description="Review-only education draft preserving sources and limitations.",
        platform_fit_notes={platform: f"registry_fit:{platform}" for platform in brief.target_platforms},
        draft_bodies={platform: contract._draft_body(brief, platform) for platform in brief.target_platforms},
    )

    assert first.output_hash == second.output_hash
    assert first.output_hash != changed.output_hash


def test_platform_fit_notes_use_registry_platform_ids():
    brief, _, _ = build_ready_brief()
    output = contract.build_deterministic_fixture_writer_output(brief)

    assert set(output.platform_fit_notes) == set(brief.target_platforms)
    assert contract.validate_ai_writer_output(brief, output).all_drafts_review_only is True


def test_no_provider_api_network_env_or_dispatch_flags():
    brief, _, _ = build_ready_brief()
    output = contract.build_deterministic_fixture_writer_output(brief)

    assert_safety_false(brief.safety_flags)
    assert_safety_false(output.safety_flags)


def test_artifact_writer_only_allows_0174u5_path(tmp_path):
    with pytest.raises(contract.EditorialBriefAIWriterContractError):
        contract.write_artifacts(".", tmp_path)
