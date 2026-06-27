import json
from pathlib import Path
from live_contentops import manual_evidence_fixture_validator_v6 as validator


def test_empty_fixture_status():
    fixture = {}
    status, errors, rejected, unsafe, complete = validator.validate_fixture(fixture)
    assert status == "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"
    assert complete is False
    assert len(errors) > 0


def test_placeholder_fixture_status():
    fixture = {slot: "PLACEHOLDER_REPLACE_BEFORE_REVIEW" for slot in validator.REQUIRED_SLOTS}
    status, errors, rejected, unsafe, complete = validator.validate_fixture(fixture)
    assert status == "EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT"
    assert complete is False


def test_incomplete_fixture_status():
    fixture = {
        "operator_idea_source_ref": "docs/evidence/jim_notes.pdf",
        "topic_statement": "Valid topic statement"
    }
    status, errors, rejected, unsafe, complete = validator.validate_fixture(fixture)
    assert status == "FIXTURE_INCOMPLETE_MISSING_SLOTS"
    assert complete is False
    assert "factual_claims" in errors[0]


def test_filled_safe_fixture_status():
    fixture = {
        "operator_idea_source_ref": "docs/evidence/jim_notes.pdf",
        "topic_statement": "Valid topic",
        "factual_claims": ["claim 1"],
        "source_notes": "verified",
        "citation_candidates": ["citation 1"],
        "supporting_artifacts": ["doc.pdf"],
        "limitation_notes": "none",
        "no_signal_disclosure": "yes",
        "intended_content_lane": "substack",
        "intended_canonical_article_angle": "analysis"
    }
    status, errors, rejected, unsafe, complete = validator.validate_fixture(fixture)
    assert status == "VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW"
    assert complete is True


def test_filled_safe_preflight_fixture_status():
    fixture = {
        "operator_idea_source_ref": "docs/evidence/jim_notes.pdf",
        "topic_statement": "Valid topic",
        "factual_claims": ["claim 1"],
        "source_notes": "verified",
        "citation_candidates": ["citation 1"],
        "supporting_artifacts": ["doc.pdf"],
        "limitation_notes": "none",
        "no_signal_disclosure": "yes",
        "intended_content_lane": "substack",
        "intended_canonical_article_angle": "analysis",
        "ready_for_preflight": True
    }
    status, errors, rejected, unsafe, complete = validator.validate_fixture(fixture)
    assert status == "EVIDENCE_SUBMISSION_READY_FOR_PREFLIGHT_REVIEW"
    assert complete is True


def test_unsafe_fixtures_rejections():
    unsafe_inputs = [
        "https://discord.com/api/webhooks/12345/abcdef",
        "mysecrettoken123",
        "/path/to/.env",
        "session_cookie_abc",
        "bearer_token",
        "authorization_header"
    ]
    
    for val in unsafe_inputs:
        fixture = {
            "operator_idea_source_ref": val,
            "topic_statement": "Valid topic",
            "factual_claims": ["claim 1"],
            "source_notes": "verified",
            "citation_candidates": ["citation 1"],
            "supporting_artifacts": ["doc.pdf"],
            "limitation_notes": "none",
            "no_signal_disclosure": "yes",
            "intended_content_lane": "substack",
            "intended_canonical_article_angle": "analysis"
        }
        status, errors, rejected, unsafe, complete = validator.validate_fixture(fixture)
        assert status == "FIXTURE_REJECTED_UNSAFE_VALUES"
        assert unsafe is True
        assert "operator_idea_source_ref" in rejected
        assert complete is False


def test_next_task_pointer_soft_wording():
    pointer_not_complete = validator.generate_next_task_pointer("EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT")
    assert "recommended next task at time of bundle generation" in pointer_not_complete.lower()
    assert "TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0" in pointer_not_complete
    
    pointer_complete = validator.generate_next_task_pointer("VALIDATION_SUCCESS_READY_FOR_HUMAN_REVIEW")
    assert "recommended next task at time of bundle generation" in pointer_complete.lower()
    assert "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_GATE_LANE_V0" in pointer_complete


def test_no_sensitive_data_in_outputs():
    # Make sure default guides and reports have no webhook/secret patterns
    guide = validator.generate_submission_guide()
    assert "discord.com/api/webhooks" not in guide
    assert "token" not in guide.lower()
    assert "cookie" not in guide.lower()
    
    report = validator.generate_implementation_report("EMPTY_FIXTURE_AWAITING_OPERATOR_INPUT")
    assert "discord.com/api/webhooks" not in report
    assert "token" not in report.lower()


def test_module_contains_no_forbidden_behavior():
    attrs = dir(validator)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
