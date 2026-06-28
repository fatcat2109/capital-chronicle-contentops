"""Test LLM summary safety validator rules."""
from __future__ import annotations

from live_contentops import llm_summary_safety_validator_v6 as validator


def test_validation_clean():
    intake = {"dispatch_allowed_now": False}
    contract = {"summarizer_instruction": "Clean instruction"}
    summary = {
        "model_output_claimed": False,
        "model_name": None,
        "high_signal_feedback_themes": "Clean themes"
    }
    ideas = [{"public_url_verified": False, "allowed_for_publication": False}]
    backlog = [{"public_url_verified": False, "allowed_for_publication": False}]
    unsafe = {"unsafe_advice_snapshots_count": 0}

    report, blockers = validator.validate_summary_artifacts(
        intake, contract, summary, ideas, backlog, unsafe
    )

    assert report["validation_status"] == "PASSED"
    assert len(blockers) == 0


def test_validation_with_provider_calls():
    intake = {"llm_provider_call_performed": True}
    contract = {"summarizer_instruction": "Clean instruction"}
    summary = {
        "model_output_claimed": True,
        "model_name": "gpt-4",
        "high_signal_feedback_themes": "Clean themes"
    }
    ideas = [{"public_url_verified": False}]
    backlog = []
    unsafe = {"unsafe_advice_snapshots_count": 0}

    report, blockers = validator.validate_summary_artifacts(
        intake, contract, summary, ideas, backlog, unsafe
    )

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "live_provider_call_detected" in blockers
    assert "fake_model_output_claim_detected" in blockers


def test_validation_with_leaks_and_unsafe():
    intake = {}
    contract = {"summarizer_instruction": "Send details to admin@site.com or check private DM."}
    summary = {
        "model_output_claimed": False,
        "model_name": None
    }
    ideas = [{"public_url_verified": True}]
    backlog = []
    unsafe = {"unsafe_advice_snapshots_count": 1}

    report, blockers = validator.validate_summary_artifacts(
        intake, contract, summary, ideas, backlog, unsafe
    )

    assert report["validation_status"] == "FAILED_WITH_BLOCKERS"
    assert "private_or_secret_material_detected" in blockers
    assert "dm_or_private_message_detected" in blockers
    assert "fake_public_result_detected" in blockers
    assert "unsafe_financial_advice_request_detected" in blockers
