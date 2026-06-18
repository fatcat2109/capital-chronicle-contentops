import importlib
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.editorial_brief_policy")
    assert callable(module.write_artifacts)
    assert module.TASK_LABEL.startswith("TASK_CONTENTOPS_0174XE_XF_XG")


def test_platform_tier_mapping_matches_registry():
    module = importlib.import_module("live_contentops.editorial_brief_policy")
    packet = module.build_policy_packet()
    assert packet["supported_platform_tiers"]["primary_brand_channel_fit"] == ["x", "telegram", "substack"]
    assert packet["supported_platform_tiers"]["secondary_channel_fit"] == ["linkedin"]
    assert packet["supported_platform_tiers"]["expansion_channel_fit"] == ["threads", "instagram", "facebook_page"]
    assert module.platform_tier_for("substack") == "primary_brand_channel_fit"
    assert module.platform_tier_for("linkedin") == "secondary_channel_fit"
    assert module.platform_tier_for("instagram") == "expansion_channel_fit"


def test_policy_rules_include_required_constraints():
    module = importlib.import_module("live_contentops.editorial_brief_policy")
    rules = module.build_policy_packet()["policy_rules"]
    assert rules["substack"] == "owned_long_form_authority_manual_export_path"
    assert rules["x"] == "short_form_thread_preview_only_not_posting"
    assert rules["telegram"] == "channel_update_distinct_from_remote_inbox"
    assert rules["linkedin"] == "secondary_professional_credibility_review_gated"
    assert rules["future_artifact_backed"] == "blocked_without_artifact_intake_gate"
    assert rules["grounded_news_context"] == "news_hook_never_signal"


def test_future_artifact_gate_blocking():
    module = importlib.import_module("live_contentops.editorial_brief_policy")
    intent = {"extracted_content_lane": "future_artifact_backed", "extracted_platform_targets": ["substack"], "blocked_reasons": [], "extracted_forbidden_risk_flags": [], "intent_class": "create_content_from_idea", "can_create_content_brief": True}
    result = module.policy_for_intent(intent)
    assert "future_artifact_backed_without_artifact_intake_gate" in result["blocked_reasons"]
    assert result["artifact_backed_allowed"] is False


def test_approval_direct_dispatch_signal_policies_block():
    module = importlib.import_module("live_contentops.editorial_brief_policy")
    intent = {"extracted_content_lane": "pre_alpha_general_process", "extracted_platform_targets": [], "blocked_reasons": [], "extracted_forbidden_risk_flags": ["approval_response_candidate_only", "blocked_direct_dispatch_request", "blocked_signal_or_advice_language"], "intent_class": "approve_candidate", "can_create_content_brief": False}
    result = module.policy_for_intent(intent)
    assert "approval_intent_cannot_create_approval" in result["blocked_reasons"]
    assert "direct_dispatch_intent_cannot_create_outbox" in result["blocked_reasons"]
    assert "signal_or_advice_language_blocks_brief_generation" in result["blocked_reasons"]
    assert result["can_generate_review_draft"] is False


def test_policy_safety_invariants():
    module = importlib.import_module("live_contentops.editorial_brief_policy")
    packet = module.build_policy_packet()
    assert packet["no_financial_advice_always"] is True
    assert packet["no_signal_language_always"] is True
    assert packet["can_create_approval_always_false"] is True
    assert packet["can_dispatch_always_false"] is True
    assert packet["public_postable_always_false"] is True
    assert packet["human_review_required_always"] is True


def test_no_live_network_env_provider_platform_behavior():
    module = importlib.import_module("live_contentops.editorial_brief_policy")
    packet = module.build_policy_packet()
    for key in ["network_performed", "telegram_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "credential_read", "env_read", "dotenv_read", "scheduler_enabled", "live_post_performed", "autonomous_replies_or_dms", "scraping_performed", "public_ready_content_generated", "approval_ledger_mutated", "dispatch_outbox_mutated"]:
        assert packet[key] is False


def test_deterministic_generation_and_unsafe_path_refusal(tmp_path):
    module = importlib.import_module("live_contentops.editorial_brief_policy")
    first = module.write_artifacts(REPO_ROOT)
    second = module.write_artifacts(REPO_ROOT)
    assert first == second
    assert (REPO_ROOT / module.DOC_REL_DIR / module.PACKET_FILENAME).exists()
    assert (REPO_ROOT / module.DOC_REL_DIR / module.DOC_FILENAME).exists()
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        module.write_artifacts(REPO_ROOT, tmp_path)
