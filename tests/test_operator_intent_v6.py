import json
from pathlib import Path
from live_contentops import operator_intent_v6 as intent


def test_idea_only_prompt_classification():
    p = "Idea: let's write an article about performance updates"
    packet = intent.parse_intent(p)
    assert packet["intent_class"] in ["create_canonical_article", "create_platform_variants"]
    assert packet["source_mode"] == "operator_idea_only"
    assert packet["not_public_postable"] is True
    assert packet["dispatch_allowed_now"] is False


def test_source_path_prompt_sets_source_mode():
    p = "Write platform variants from docs/indexing_perf.md"
    packet = intent.parse_intent(p)
    assert packet["source_mode"] == "source_artifact_path"
    assert "docs/indexing_perf.md" in packet["source_refs"]
    assert packet["approval_requested"] is False
    assert packet["dispatch_allowed_now"] is False


def test_approve_this_without_hash_and_destination_is_blocked():
    p = "Please approve this draft payload"
    packet = intent.parse_intent(p)
    assert packet["intent_class"] == "approve_payload"
    assert packet["approval_requested"] is True
    assert packet["approval_valid_for_dispatch"] is False
    assert "missing_payload_hash_for_approval" in packet["blocked_reasons"]
    assert "missing_destination_binding_for_approval" in packet["blocked_reasons"]


def test_approve_this_with_hash_but_no_destination_is_blocked():
    p = "Please approve payload abc123def456"
    packet = intent.parse_intent(p)
    assert packet["approval_valid_for_dispatch"] is False
    assert "missing_destination_binding_for_approval" in packet["blocked_reasons"]


def test_approve_this_with_hash_and_destination_is_valid_for_dispatch():
    p = "Please approve payload abc123def456 for discord_webhook_destination"
    packet = intent.parse_intent(p)
    assert packet["approval_requested"] is True
    # The specific block reasons for missing metadata are resolved:
    assert "missing_payload_hash_for_approval" not in packet["blocked_reasons"]
    assert "missing_destination_binding_for_approval" not in packet["blocked_reasons"]
    assert packet["approval_valid_for_dispatch"] is True
    # But dispatch is still not allowed now:
    assert packet["dispatch_allowed_now"] is False


def test_dispatch_to_discord_is_blocked_with_allowed_now_false():
    p = "Please send this payload to Discord channel announcements immediately"
    packet = intent.parse_intent(p)
    assert packet["dispatch_requested"] is True
    assert packet["dispatch_allowed_now"] is False
    assert "dispatch_not_allowed_in_this_task" in packet["blocked_reasons"]


def test_exact_approval_text_only_creates_intent_no_side_effects():
    p = "Please approve payload abc123def456 for discord_webhook_destination"
    # Calling parse_intent shouldn't mutate external files, databases, or environment
    packet = intent.parse_intent(p)
    assert isinstance(packet, dict)
    assert packet["raw_secret_output"] is False
    assert packet["webhook_url_printed"] is False


def test_trading_signal_is_blocked():
    prompts = ["Should we buy now?", "Time to sell the position.", "Hold your bags."]
    for p in prompts:
        packet = intent.parse_intent(p)
        assert packet["no_signal_status"] is False
        assert "trading_signal_language_blocked" in packet["blocked_reasons"]


def test_position_sizing_is_blocked():
    p = "Allocate 15% to index fund."
    packet = intent.parse_intent(p)
    assert "position_sizing_language_blocked" in packet["blocked_reasons"]


def test_guaranteed_prediction_is_blocked():
    p = "This is a guaranteed win with zero risk."
    packet = intent.parse_intent(p)
    assert "guaranteed_prediction_language_blocked" in packet["blocked_reasons"]


def test_numeric_claim_without_evidence_sets_source_needed():
    p = "We achieved 50% database latency reduction."
    packet = intent.parse_intent(p)
    assert packet["source_needed"] is True
    assert packet["source_evidence_required"] is True
    assert "numeric_claim_requires_source_evidence" in packet["blocked_reasons"]


def test_numeric_claim_with_evidence_does_not_require_source_evidence():
    p = "We achieved 50% database latency reduction according to docs/performance.md"
    packet = intent.parse_intent(p)
    assert packet["source_needed"] is False
    assert packet["source_evidence_required"] is False
    assert "numeric_claim_requires_source_evidence" not in packet["blocked_reasons"]


def test_future_internal_alpha_claim_without_path_is_blocked():
    p = "We have a future internal alpha artifact containing our roadmap."
    packet = intent.parse_intent(p)
    assert packet["future_artifact_claim_detected"] is True
    assert "missing_future_alpha_artifact_path" in packet["blocked_reasons"]


def test_future_internal_alpha_claim_with_path_is_not_blocked_on_path():
    p = "We have a future internal alpha artifact docs/roadmap.md containing our roadmap."
    packet = intent.parse_intent(p)
    assert packet["future_artifact_claim_detected"] is True
    assert "missing_future_alpha_artifact_path" not in packet["blocked_reasons"]


def test_packet_safety_claims():
    p = "Draft a canonical article about Capital Chronicle V6"
    packet = intent.parse_intent(p)
    assert packet["human_review_required"] is True
    assert packet["not_public_postable"] is True
    assert packet["no_live_request_in_this_task"] is True
    assert packet["no_env_read_in_this_task"] is True
    assert packet["raw_secret_output"] is False
    assert packet["webhook_url_printed"] is False
    
    # Confirm no sensitive strings
    dump = json.dumps(packet)
    assert "discord.com/api/webhooks" not in dump
    assert "token" not in dump.lower()
    assert "cookie" not in dump.lower()


def test_module_contains_no_forbidden_behavior():
    # Verify by scanning imports/attributes
    attrs = dir(intent)
    assert "urlopen" not in attrs
    assert "requests" not in attrs
    assert "httpx" not in attrs
    assert "getenv" not in attrs
    assert "environ" not in attrs
