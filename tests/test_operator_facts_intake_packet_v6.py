import json
from pathlib import Path
from live_contentops import operator_facts_intake_packet_v6 as intake_lane


def test_required_slots_exist():
    assert len(intake_lane.REQUIRED_SLOT_IDS) == 10
    for slot in [
        "operator_idea_source_ref",
        "topic_statement",
        "factual_claims",
        "source_notes",
        "citation_candidates",
        "supporting_artifacts",
        "limitation_notes",
        "no_signal_disclosure",
        "intended_content_lane",
        "intended_canonical_article_angle"
    ]:
        assert slot in intake_lane.REQUIRED_SLOT_IDS


def test_empty_fixture_validation():
    empty_fixture = {slot: None for slot in intake_lane.REQUIRED_SLOT_IDS}
    report, slots = intake_lane.validate_fixture(empty_fixture)

    assert report["validation_status"] == "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"
    assert report["evidence_complete"] is False
    assert report["operator_idea_source_ref_resolved"] is False
    assert len(slots) == 10
    for s in slots:
        assert s["supplied_value"] is None
        assert s["verified"] is False


def test_unsafe_values_rejection():
    unsafe_fixtures = [
        {"operator_idea_source_ref": "https://discord.com/api/webhooks/123"},
        {"topic_statement": "my_secret_token_123"},
        {"factual_claims": ["some fact", "my sessioncookie string"]},
        {"source_notes": "path/to/.env"},
        {"citation_candidates": ["bearer token"]},
        {"supporting_artifacts": ["authorization header"]},
        {"limitation_notes": "localstorage dump"},
        {"no_signal_disclosure": "sessionstorage value"}
    ]

    for bad_input in unsafe_fixtures:
        fixture = {slot: "safe normal value" for slot in intake_lane.REQUIRED_SLOT_IDS}
        # Override with unsafe input
        fixture.update(bad_input)
        
        report, slots = intake_lane.validate_fixture(fixture)
        assert report["unsafe_values_detected"] is True
        assert report["evidence_complete"] is False
        assert report["validation_status"] in ["FIXTURE_REJECTED_UNSAFE_VALUES", "FIXTURE_INCOMPLETE_MISSING_SLOTS"]


def test_valid_filled_fixture_succeeds():
    valid_fixture = {
        "operator_idea_source_ref": "docs/evidence/verified_report.pdf",
        "topic_statement": "Market analysis of US Treasury movements.",
        "factual_claims": ["Treasury yields shifted by 5bps."],
        "source_notes": "Based on Federal Reserve official H.15 release.",
        "citation_candidates": ["Federal Reserve Board H.15"],
        "supporting_artifacts": ["docs/evidence/fed_h15.pdf"],
        "limitation_notes": "Applies only to June 2026 week 4.",
        "no_signal_disclosure": "This analysis does not contain any trading signal or financial advice.",
        "intended_content_lane": "editorial_brief",
        "intended_canonical_article_angle": "market_summary"
    }

    report, slots = intake_lane.validate_fixture(valid_fixture)
    assert report["unsafe_values_detected"] is False
    assert report["evidence_complete"] is True
    assert report["validation_status"] == "VALIDATION_SUCCESS_READY_FOR_REVIEW"
    assert report["operator_idea_source_ref_resolved"] is True
    
    for s in slots:
        assert s["supplied_value"] is not None
        assert s["verified"] is True
        assert s["unsafe_value_detected"] is False


def test_materialize_operator_facts_intake_defaults(tmp_path):
    # Setup mock preflight intake
    intake_packet = {
        "source_evidence_intake_packet_id": "intake_mock_12345"
    }
    mock_intake_file = tmp_path / "source_evidence_intake_packet.json"
    mock_intake_file.write_text(json.dumps(intake_packet), encoding="utf-8")

    intake_packet, fixture_template, report, slots, ref_snap, blocker_snap = intake_lane.materialize_operator_facts_intake(
        intake_source_path=mock_intake_file
    )

    assert intake_packet["source_evidence_intake_packet_id"] == "intake_mock_12345"
    assert intake_packet["facts_intake_status"] == "AWAITING_OPERATOR_FACTS_AND_EVIDENCE"
    assert intake_packet["fixture_status"] == "EMPTY_TEMPLATE_AWAITING_OPERATOR_INPUT"
    assert intake_packet["evidence_complete"] is False
    assert intake_packet["dispatch_allowed_now"] is False

    assert ref_snap["resolution_status"] == "MISSING_OPERATOR_SUPPLIED_EVIDENCE"
    assert ref_snap["requires_manual_evidence"] is True
    assert ref_snap["operator_idea_source_ref_resolved"] is False

    assert blocker_snap["dispatch_allowed_now"] is False
    assert "operator_idea_source_ref_missing" in blocker_snap["unresolved_blockers"]


def test_webhook_and_secrets_hygiene():
    guide = intake_lane.generate_guide_markdown()
    
    # Assert no actual secret keywords or webhook URLs are present in generated text
    assert "discord.com/api/webhooks" in guide  # Guide explains what is rejected, which is fine
    assert "token" in guide.lower()
    
    # Assert no fake numbers or claims in guide
    assert "$1,000" not in guide
    assert "99.9%" not in guide


def test_no_forbidden_behavior_in_module():
    attrs = dir(intake_lane)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
