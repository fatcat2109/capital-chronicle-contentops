from pathlib import Path

import pytest

from live_contentops import capital_chronicle_ingestion_headline_idea_connector_precheck as u7
from live_contentops import internal_alpha_artifact_intake_content_eligibility_contract as c


def _candidate(candidate_class: str = "headline_surface") -> u7.IngestionArtifactContextCandidate:
    return u7.IngestionArtifactContextCandidate(
        candidate_id="candidate_1",
        candidate_class=candidate_class,
        source_repo_path="A:/readonly/ingestion",
        relative_path="reports/headline.md",
        file_ext=".md",
        size_bytes=12,
        modified_time_epoch=123,
        contentops_use_class="idea_context_only",
        may_generate_content_idea=True,
        may_support_public_claim=False,
        may_clear_dqr=False,
        may_clear_readiness=False,
        may_create_current_truth=False,
        requires_human_review=True,
        required_labels=("context_only",),
        evidence_refs=("reports/headline.md",),
        blocked_reasons=(),
    )


def _manual(**overrides):
    data = {
        "artifact_ref": "artifact.md",
        "artifact_family": "internal_alpha_report",
        "citation_refs": ("citation:1",),
        "limitation_notes": ("Review-only; not current truth.",),
        "declared_readiness_state": "ready_for_review",
        "declared_dqr_state": "context_only_not_cleared",
        "declared_freshness_state": "fresh",
        "declared_source_authority_state": "known_context_source",
        "evidence_refs": ("artifact.md",),
    }
    data.update(overrides)
    return c.build_manual_artifact_intake_packet(data)


def test_build_intake_from_u7_candidate_preserves_boundaries():
    intake = c.build_intake_from_u7_candidate(_candidate())
    assert intake.artifact_family == "headline_context_packet"
    assert intake.can_create_content_idea is True
    assert intake.can_create_editorial_brief_candidate is False
    assert intake.can_support_public_claim is False
    assert intake.can_clear_dqr is False
    assert intake.can_clear_readiness is False
    assert intake.can_create_current_truth is False
    assert intake.public_postable is False
    assert intake.safety_flags["ingestion_repo_mutated"] is False


def test_build_intake_from_headline_context_packet():
    packet = u7.HeadlineIdeaContextPacket(
        "headline_context_1", ("candidate_1",), "topic", "grounded_news_context",
        "source_provided_context_only", "source_context_claim", "summary",
        ("source.md",), ("context only",), False, False, True, True,
        True, False, False, u7.safety_flags(), (), ("source.md",),
    )
    intake = c.build_intake_from_headline_context_packet(packet)
    assert intake.artifact_family == "headline_context_packet"
    assert intake.citation_refs == ("source.md",)
    assert intake.declared_dqr_state == "context_only_not_cleared"


def test_manual_intake_is_deterministic():
    first = _manual()
    second = _manual()
    assert first.artifact_intake_id == second.artifact_intake_id
    assert first.artifact_hash == second.artifact_hash


def test_unknown_artifact_fails_closed():
    assessment = c.assess_content_eligibility(_manual(artifact_family="mystery"))
    assert assessment.eligibility_class == "blocked_unknown_artifact"
    assert "blocked_unknown_artifact" in assessment.blocked_reasons


def test_missing_citations_blocker():
    assessment = c.assess_content_eligibility(_manual(citation_refs=()))
    assert assessment.eligibility_class == "blocked_missing_citations"


def test_missing_limitations_blocker():
    assessment = c.assess_content_eligibility(_manual(limitation_notes=()))
    assert assessment.eligibility_class == "blocked_missing_limitations"


def test_readiness_not_ready_blocker():
    assessment = c.assess_content_eligibility(_manual(declared_readiness_state="not_ready"))
    assert assessment.eligibility_class == "blocked_readiness_not_ready"


def test_unresolved_dqr_blocker():
    assessment = c.assess_content_eligibility(_manual(declared_dqr_state="unresolved"))
    assert assessment.eligibility_class == "blocked_dqr_unresolved"


def test_freshness_unknown_blocker():
    assessment = c.assess_content_eligibility(_manual(declared_freshness_state="unknown"))
    assert assessment.eligibility_class == "blocked_freshness_unknown"


def test_source_authority_unknown_blocker():
    assessment = c.assess_content_eligibility(_manual(declared_source_authority_state="unknown"))
    assert assessment.eligibility_class == "blocked_source_authority_unknown"


def test_advice_or_signal_risk_blocker():
    assessment = c.assess_content_eligibility(_manual(), context_summary="buy signal")
    assert assessment.eligibility_class == "blocked_advice_or_signal_risk"


def test_headline_context_can_be_content_idea_only():
    intake = _manual(
        artifact_family="headline_context_packet",
        declared_readiness_state="not_applicable_context_only",
        declared_freshness_state="not_applicable_context_only",
    )
    assessment = c.assess_content_eligibility(intake)
    assert assessment.eligibility_class == "eligible_for_content_idea_only"


def test_review_ready_artifact_can_be_editorial_brief_candidate_only():
    intake = _manual()
    assessment = c.assess_content_eligibility(intake)
    assert assessment.eligibility_class == "eligible_for_editorial_brief_candidate"
    assert assessment.safety_flags["dqr_cleared"] is False
    assert assessment.safety_flags["readiness_cleared"] is False


def test_report_never_approves_public_claim_or_dispatch():
    assessments = (c.assess_content_eligibility(_manual()),)
    report = c.build_artifact_backed_content_eligibility_report(assessments)
    assert report.approved_for_content_idea is True
    assert report.approved_for_editorial_brief_candidate is True
    assert report.approved_for_public_claim is False
    assert report.approved_for_approval is False
    assert report.approved_for_dispatch is False


def test_idea_seed_remains_review_only():
    intake = _manual()
    assessment = c.assess_content_eligibility(intake)
    report = c.build_artifact_backed_content_eligibility_report((assessment,))
    seed = c.build_artifact_idea_seed_packet(report, (intake,))
    assert seed.can_create_content_idea is True
    assert seed.can_create_editorial_brief_candidate is True
    assert seed.can_create_approval is False
    assert seed.can_dispatch is False
    assert seed.public_postable is False


def test_all_safety_false_flags_false_across_models():
    intake = _manual()
    assessment = c.assess_content_eligibility(intake)
    report = c.build_artifact_backed_content_eligibility_report((assessment,))
    seed = c.build_artifact_idea_seed_packet(report, (intake,))
    for model in (intake, assessment, report, seed):
        assert all(model.safety_flags[flag] is False for flag in c.SAFETY_FALSE_FLAGS)


def test_contract_packet_contains_checksum_and_next_batch():
    packet = c.build_contract_packet()
    assert packet["contract_checksum"]
    assert packet["next_heavy_batch_recommendation"] == c.NEXT_HEAVY_BATCH
    assert packet["eligibility_report"]["approved_for_public_claim"] is False


def test_artifact_writer_locked_to_0174u8(tmp_path):
    with pytest.raises(ValueError, match="0174U8"):
        c.write_artifacts(tmp_path, output_dir=tmp_path / "elsewhere")


def test_artifact_writer_creates_expected_files(tmp_path):
    packet = c.write_artifacts(tmp_path)
    out = tmp_path / c.DOC_REL_DIR
    assert (out / c.PACKET_FILENAME).exists()
    assert (out / c.RUNBOOK_FILENAME).exists()
    assert packet["artifact_scope"] == "docs/automation/0174U8_only"


def test_no_ingestion_repo_mutation_or_live_behavior_in_contract_packet():
    packet = c.build_contract_packet()
    models = packet["intake_packets"] + packet["eligibility_assessments"]
    models += [packet["eligibility_report"], packet["artifact_idea_seed_packet"]]
    for model in models:
        flags = model["safety_flags"]
        assert flags["ingestion_repo_mutated"] is False
        assert flags["network_performed"] is False
        assert flags["provider_api_called"] is False
        assert flags["platform_api_called"] is False
