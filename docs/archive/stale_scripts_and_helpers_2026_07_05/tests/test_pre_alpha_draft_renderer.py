"""Tests for the local-only pre-alpha draft renderer + review queue (Task 0097).

Deterministic, repo-local. No network/provider/LLM/credential access.
"""

import json
import os

from live_contentops import pre_alpha_draft_renderer as r

FIX_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "pre_alpha_draft_renderer")


def _fix(name):
    return os.path.abspath(os.path.join(FIX_DIR, name))


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

def test_schemas_exist_and_load():
    assert isinstance(r.load_rendered_packet_schema(), dict)
    assert isinstance(r.load_review_queue_item_schema(), dict)


# ---------------------------------------------------------------------------
# Valid renders pass and produce review queue items
# ---------------------------------------------------------------------------

def test_valid_build_in_public_render_passes():
    p = r.render_from_input_file(_fix("valid_render_from_build_in_public_packet.json"))
    assert p["guardrail_status"] == "pass", p["blocked_reasons"]
    assert p["blocked_reasons"] == []
    assert len(p["review_queue_items"]) == 1
    item = p["review_queue_items"][0]
    assert item["review_status"] == "needs_manual_review"
    assert item["guardrail_findings"] == []


def test_valid_macro_education_render_passes():
    p = r.render_from_input_file(_fix("valid_render_from_macro_education_packet.json"))
    assert p["guardrail_status"] == "pass", p["blocked_reasons"]
    assert len(p["review_queue_items"]) == 1


def test_valid_render_pins_non_publishing_posture():
    p = r.render_from_input_file(_fix("valid_render_from_build_in_public_packet.json"))
    assert p["manual_review_required"] is True
    assert p["public_postable"] is False
    assert p["platform_publish_allowed_now"] is False
    assert p["live_execution_allowed_now"] is False
    assert p["provider_call_made"] is False
    assert p["network_call_made"] is False


def test_review_queue_item_pins_non_publishing_posture():
    p = r.render_from_input_file(_fix("valid_render_from_build_in_public_packet.json"))
    item = p["review_queue_items"][0]
    assert item["reviewer_required"] is True
    assert item["publish_allowed_now"] is False
    assert item["manual_publish_only"] is True
    assert item["approval_required_for_future_publish"] is True


def test_integration_carries_0096_config_ids():
    p = r.render_from_input_file(_fix("valid_render_from_build_in_public_packet.json"))
    assert p["prompt_pack_id"] == "pp_build_in_public_001"
    assert p["style_profile_id"] == "sp_build_in_public_001"
    assert p["editorial_rubric_id"] == "er_pre_alpha_001"


def test_integration_preserves_source_ids_and_limitations():
    p = r.render_from_input_file(_fix("valid_render_from_build_in_public_packet.json"))
    item = p["review_queue_items"][0]
    assert item["is_general_process_content"] is True
    assert item["limitations"] == ["This is product/process commentary, not a market view."]
    assert item["source_artifact_ids"] == []


def test_determinism_same_input_same_output():
    a = r.render_from_input_file(_fix("valid_render_from_build_in_public_packet.json"))
    b = r.render_from_input_file(_fix("valid_render_from_build_in_public_packet.json"))
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)



# ---------------------------------------------------------------------------
# Invalid renders block (fail closed: no review queue items exposed)
# ---------------------------------------------------------------------------

def test_public_postable_true_blocks():
    p = r.render_from_input_file(_fix("invalid_public_postable_true.json"))
    assert p["guardrail_status"] == "blocked"
    assert p["review_queue_items"] == []
    assert p["draft_candidates"] == []


def test_missing_manual_review_blocks():
    p = r.render_from_input_file(_fix("invalid_missing_manual_review.json"))
    assert p["guardrail_status"] == "blocked"
    assert "editorial_packet_review_required_must_be_true" in p["blocked_reasons"]
    assert p["review_queue_items"] == []


def test_signal_language_render_blocks():
    p = r.render_from_input_file(_fix("invalid_signal_language_render.json"))
    assert p["guardrail_status"] == "blocked"
    assert p["review_queue_items"] == []
    assert any(reason.startswith("draft_blocked:") for reason in p["blocked_reasons"])


def test_prompt_pack_not_validated_blocks():
    p = r.render_from_input_file(_fix("invalid_prompt_pack_not_validated.json"))
    assert p["guardrail_status"] == "blocked"
    assert "prompt_pack_invalid" in p["blocked_reasons"]
    assert p["review_queue_items"] == []


def test_missing_config_blocks_with_not_validated_codes():
    # The public_postable fixture also has null config -> not validated codes.
    p = r.render_from_input_file(_fix("invalid_public_postable_true.json"))
    assert "prompt_pack_not_validated" in p["blocked_reasons"]
    assert "style_profile_not_validated" in p["blocked_reasons"]
    assert "editorial_rubric_not_validated" in p["blocked_reasons"]


def test_blocked_packet_still_pins_safety_flags():
    p = r.render_from_input_file(_fix("invalid_signal_language_render.json"))
    assert p["public_postable"] is False
    assert p["platform_publish_allowed_now"] is False
    assert p["live_execution_allowed_now"] is False
    assert p["provider_call_made"] is False
    assert p["network_call_made"] is False
    assert p["manual_review_required"] is True


# ---------------------------------------------------------------------------
# Summary posture
# ---------------------------------------------------------------------------

def test_summary_posture_is_safe():
    s = r.summary()
    assert s["local_only"] is True
    assert s["renderer_enabled"] is True
    assert s["review_queue_enabled"] is True
    assert s["integrates_with_0095_editorial_packet"] is True
    assert s["integrates_with_0096_prompt_pack"] is True
    assert s["provider_call_made"] is False
    assert s["network_call_made"] is False
    assert s["credential_read"] is False
    assert s["fake_alpha_output"] is False
    assert s["public_postable_output"] is False
    assert s["platform_publish_allowed_now"] is False
    assert s["live_execution_allowed_now"] is False
    assert s["manual_review_required"] is True
