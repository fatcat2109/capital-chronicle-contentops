import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    assert callable(module.write_artifacts)
    assert module.TASK_LABEL.startswith("TASK_CONTENTOPS_0174XB_XC_XD")


def _intent_by_source(packet, source_message_id):
    return [i for i in packet["intents"] if i["source_message_id"] == source_message_id][0]


def test_each_supported_intent_class_is_classified():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    classes = {i["intent_class"] for i in module.build_intent_ingress_packet()["intents"]}
    for expected in module.SUPPORTED_INTENT_CLASSES:
        assert expected in classes


def test_approval_like_text_cannot_approve_without_active_challenge():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    intent = _intent_by_source(module.build_intent_ingress_packet(), "msg_003")
    assert intent["intent_class"] == "approve_candidate"
    assert intent["can_create_approval"] is False
    assert "approval_without_active_challenge_forbidden" in intent["blocked_reasons"]
    assert "approval_response_candidate_only" in intent["extracted_forbidden_risk_flags"]


def test_direct_dispatch_language_is_blocked():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    intent = _intent_by_source(module.build_intent_ingress_packet(), "msg_011")
    assert "blocked_direct_dispatch_request" in intent["extracted_forbidden_risk_flags"]
    assert "direct_dispatch_request_forbidden" in intent["blocked_reasons"]
    assert intent["can_dispatch"] is False


def test_trading_signal_advice_language_is_blocked():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    intent = _intent_by_source(module.build_intent_ingress_packet(), "msg_012")
    assert "blocked_signal_or_advice_language" in intent["extracted_forbidden_risk_flags"]
    assert "financial_signal_or_advice_language_forbidden" in intent["blocked_reasons"]
    assert intent["can_create_content_brief"] is False


def test_substack_idea_routes_owned_long_form_manual_export_path():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    intent = _intent_by_source(module.build_intent_ingress_packet(), "msg_001")
    assert intent["intent_class"] == "create_content_from_idea"
    assert intent["extracted_platform_targets"] == ["substack"]
    assert intent["extracted_content_lane"] == "grounded_news_context"
    assert intent["extracted_topic"] == "cpi_macro_regime_shift"
    assert intent["can_create_content_brief"] is True


def test_x_idea_or_revision_routes_short_form_thread_preview_path():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    intent = _intent_by_source(module.build_intent_ingress_packet(), "msg_002")
    assert intent["intent_class"] == "revise_draft"
    assert intent["extracted_platform_targets"] == ["x"]
    assert intent["extracted_content_lane"] == "short_form_preview"
    assert intent["extracted_tone"] == "calmer"


def test_telegram_channel_update_distinct_from_telegram_inbox():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    packet = module.build_intent_ingress_packet()
    assert packet["telegram_channel_update_distinct_from_inbox"] is True


def test_request_preview_and_sources_classes():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    packet = module.build_intent_ingress_packet()
    assert _intent_by_source(packet, "msg_013")["intent_class"] == "request_preview"
    assert _intent_by_source(packet, "msg_014")["intent_class"] == "request_sources"


def test_intent_packet_can_never_approve_or_dispatch():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    packet = module.build_intent_ingress_packet()
    assert packet["all_can_create_approval_false"] is True
    assert packet["all_can_dispatch_false"] is True
    assert all(i["can_create_approval"] is False for i in packet["intents"])
    assert all(i["can_dispatch"] is False for i in packet["intents"])


def test_blocked_proofs_present():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    packet = module.build_intent_ingress_packet()
    assert packet["blocked_direct_dispatch_proof"]
    assert packet["blocked_approval_without_challenge_proof"]
    assert packet["blocked_signal_advice_language_proof"]


def test_no_live_network_env_provider_platform_behavior():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    packet = module.build_intent_ingress_packet()
    for key in [
        "network_performed", "telegram_api_called", "platform_api_called",
        "provider_api_called", "llm_provider_api_called", "credential_read",
        "env_read", "dotenv_read", "scheduler_enabled", "live_post_performed",
        "autonomous_replies_or_dms", "scraping_performed",
        "public_ready_content_generated", "approval_ledger_mutated",
        "dispatch_outbox_mutated",
    ]:
        assert packet[key] is False


def test_next_editorial_workflow_contract():
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    packet = module.build_intent_ingress_packet()
    contract = module.build_next_editorial_workflow_contract(packet)
    assert contract["next_batch_prompt"] == "TASK_CONTENTOPS_0174XE_XF_XG_LLM_INTENT_EDITORIAL_BRIEF_CONTRACT_V0"
    assert contract["next_scope"] == "llm_intent_to_editorial_brief_contract_local_only"
    assert "no_dispatch" in contract["must_preserve"]
    assert contract["intent_ingress_packet_checksum"] == packet["intent_ingress_packet_checksum"]


def test_deterministic_packet_doc_generation_and_unsafe_path_refusal(tmp_path):
    module = importlib.import_module("live_contentops.remote_operator_intent_ingress")
    first = module.write_artifacts(REPO_ROOT)
    second = module.write_artifacts(REPO_ROOT)
    assert first == second
    assert (REPO_ROOT / module.DOC_REL_DIR / module.PACKET_FILENAME).exists()
    assert (REPO_ROOT / module.DOC_REL_DIR / module.DOC_FILENAME).exists()
    assert (REPO_ROOT / module.DOC_REL_DIR / module.NEXT_PACKET_FILENAME).exists()
    assert (REPO_ROOT / module.DOC_REL_DIR / module.NEXT_DOC_FILENAME).exists()
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        module.write_artifacts(REPO_ROOT, tmp_path)
