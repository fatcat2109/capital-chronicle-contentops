import importlib
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    assert callable(module.write_artifacts)
    assert module.TASK_LABEL.startswith("TASK_CONTENTOPS_0174XE_XF_XG")


def _brief(packet, source_message_id):
    return [b for b in packet["editorial_briefs"] if b["source_message_id"] == source_message_id][0]


def test_substack_cpi_idea_becomes_grounded_news_context_with_sources():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    brief = _brief(module.build_contract_packet(REPO_ROOT), "msg_001")
    assert brief["content_lane"] == "grounded_news_context"
    assert brief["target_platforms"] == ["substack"]
    assert brief["primary_brand_channel_fit"] == ["substack"]
    assert brief["source_requirement_status"] == "source_needed"
    assert "source_requirement" in brief["source_requirements"]
    assert "manual_markdown_export" in brief["source_requirements"]
    assert brief["topic_summary"] == "CPI print as context, not proof of macro regime shift"


def test_x_hook_revision_routes_to_short_form_thread_preview():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    brief = _brief(module.build_contract_packet(REPO_ROOT), "msg_002")
    assert brief["target_platforms"] == ["x"]
    assert brief["primary_brand_channel_fit"] == ["x"]
    assert "short_form_or_thread_preview_only" in brief["source_requirements"]
    assert "no_posting" in brief["source_requirements"]
    assert brief["tone_mode"] == "calmer"


def test_approval_candidate_stays_blocked_from_approval_creation():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    packet = module.build_contract_packet(REPO_ROOT)
    brief = _brief(packet, "msg_003")
    assert brief["can_create_approval"] is False
    assert "approval_intent_cannot_create_approval" in brief["blocked_reasons"]
    assert packet["blocked_approval_proof"]


def test_direct_dispatch_request_stays_blocked():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    packet = module.build_contract_packet(REPO_ROOT)
    brief = _brief(packet, "msg_011")
    assert brief["can_dispatch"] is False
    assert brief["public_postable"] is False
    assert "direct_dispatch_intent_cannot_create_outbox" in brief["blocked_reasons"]
    assert packet["blocked_direct_dispatch_proof"]


def test_signal_advice_language_blocks_brief_generation():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    packet = module.build_contract_packet(REPO_ROOT)
    brief = _brief(packet, "msg_012")
    assert brief["can_generate_review_draft"] is False
    assert "signal_or_advice_language_blocks_brief_generation" in brief["blocked_reasons"]
    assert packet["blocked_signal_advice_proof"]


def test_unknown_sender_intent_cannot_create_brief():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    brief = _brief(module.build_contract_packet(REPO_ROOT), "msg_009")
    assert brief["can_generate_review_draft"] is False
    assert "sender_not_verified_for_intent_ingress" in brief["blocked_reasons"]
    assert "empty_or_ambiguous_intent_requires_clarification" in brief["blocked_reasons"]


def test_future_artifact_backed_blocked_without_gate():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    packet = module.build_contract_packet(REPO_ROOT)
    brief = _brief(packet, "fixture_future_artifact_demo")
    assert brief["content_lane"] == "blocked_or_unknown"
    assert brief["artifact_backed_allowed"] is False
    assert "future_artifact_backed_without_artifact_intake_gate" in brief["blocked_reasons"]
    assert packet["future_artifact_backed_blocked_proof"]


def test_telegram_channel_update_remains_separate_from_inbox():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    packet = module.build_contract_packet(REPO_ROOT)
    assert packet["telegram_channel_update_distinct_from_inbox"] is True
    brief = _brief(packet, "msg_004")
    assert brief["target_platforms"] == ["telegram"]
    assert "telegram_channel_update_distinct_from_remote_inbox" in brief["source_requirements"]


def test_platform_tier_mapping_matches_registry():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    packet = module.build_contract_packet(REPO_ROOT)
    assert packet["supported_platform_tiers"]["primary_brand_channel_fit"] == ["x", "telegram", "substack"]
    assert packet["supported_platform_tiers"]["secondary_channel_fit"] == ["linkedin"]
    assert packet["supported_platform_tiers"]["expansion_channel_fit"] == ["threads", "instagram", "facebook_page"]


def test_every_brief_has_core_safety_fields():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    packet = module.build_contract_packet(REPO_ROOT)
    assert packet["all_no_financial_advice"] is True
    assert packet["all_no_signal_language"] is True
    assert packet["all_public_postable_false"] is True
    assert packet["all_human_review_required"] is True
    assert all(b["can_create_approval"] is False for b in packet["editorial_briefs"])
    assert all(b["can_dispatch"] is False for b in packet["editorial_briefs"])


def test_no_live_network_env_provider_platform_behavior():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    packet = module.build_contract_packet(REPO_ROOT)
    for key in ["network_performed", "telegram_api_called", "platform_api_called", "provider_api_called", "llm_provider_api_called", "credential_read", "env_read", "dotenv_read", "scheduler_enabled", "live_post_performed", "autonomous_replies_or_dms", "scraping_performed", "public_ready_content_generated", "approval_ledger_mutated", "dispatch_outbox_mutated"]:
        assert packet[key] is False
        for brief in packet["editorial_briefs"]:
            assert brief[key] is False


def test_deterministic_generation_and_unsafe_path_refusal(tmp_path):
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    first = module.write_artifacts(REPO_ROOT)
    second = module.write_artifacts(REPO_ROOT)
    assert first == second
    assert (REPO_ROOT / module.DOC_REL_DIR / module.PACKET_FILENAME).exists()
    assert (REPO_ROOT / module.DOC_REL_DIR / module.DOC_FILENAME).exists()
    assert (REPO_ROOT / module.DOC_REL_DIR / module.FIXTURE_FILENAME).exists()
    assert (REPO_ROOT / module.DOC_REL_DIR / module.NEXT_PACKET_FILENAME).exists()
    assert (REPO_ROOT / module.DOC_REL_DIR / module.NEXT_DOC_FILENAME).exists()
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        module.write_artifacts(REPO_ROOT, tmp_path)


def test_next_variants_contract_preserves_forbidden_outputs():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    result = module.write_artifacts(REPO_ROOT)
    next_packet = result["next_variants_contract"]
    assert next_packet["next_batch_prompt"] == "TASK_CONTENTOPS_0174XH_XI_XJ_IDEA_TO_PRIMARY_PLATFORM_VARIANTS_DRY_RUN_V0"
    assert "dispatch" in next_packet["forbidden_outputs"]
    assert "approval" in next_packet["forbidden_outputs"]
    assert next_packet["llm_provider_api_called"] is False
