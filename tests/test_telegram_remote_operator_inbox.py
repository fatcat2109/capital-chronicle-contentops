import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.telegram_remote_operator_inbox")
    assert callable(module.write_artifacts)
    assert module.TASK_LABEL.startswith("TASK_CONTENTOPS_0174XB_XC_XD")


def test_verified_operator_fixture_passes_sender_chat_binding():
    module = importlib.import_module("live_contentops.telegram_remote_operator_inbox")
    packet = module.build_inbox_packet()
    first = packet["inbound_messages"][0]
    assert first["sender_class"] == "verified_operator"
    assert first["sender_binding_id"] == module.VERIFIED_SENDER_BINDING
    assert first["chat_binding_id"] == module.VERIFIED_CHAT_BINDING
    assert first["trust_status"] == "untrusted_input"


def test_unknown_sender_is_blocked():
    module = importlib.import_module("live_contentops.telegram_remote_operator_inbox")
    packet = module.build_inbox_packet()
    blocked = [m for m in packet["inbound_messages"] if m["message_id"] == "msg_009"][0]
    assert blocked["sender_class"] == "blocked"
    assert blocked["message_class"] == "unknown"
    assert packet["unknown_sender_blocked"] is True


def test_duplicate_message_hash_is_duplicate():
    module = importlib.import_module("live_contentops.telegram_remote_operator_inbox")
    duplicate_messages = [
        {"message_id": "a", "sender_binding_id": module.VERIFIED_SENDER_BINDING, "chat_binding_id": module.VERIFIED_CHAT_BINDING, "raw_text": "What is current status?", "received_at_order": 1},
        {"message_id": "b", "sender_binding_id": module.VERIFIED_SENDER_BINDING, "chat_binding_id": module.VERIFIED_CHAT_BINDING, "raw_text": "What is current status?", "received_at_order": 2},
    ]
    packets = module.build_inbound_packets(duplicate_messages)
    assert packets[0]["replay_status"] == "fresh"
    assert packets[1]["replay_status"] == "duplicate"


def test_stale_message_is_stale():
    module = importlib.import_module("live_contentops.telegram_remote_operator_inbox")
    packets = module.build_inbound_packets(module.default_fixture_messages(), stale_order_before=1)
    assert packets[0]["replay_status"] == "stale"


def test_raw_text_redaction_removes_token_chat_url_values():
    module = importlib.import_module("live_contentops.telegram_remote_operator_inbox")
    redacted = module.redact_text("botTokenSecret123 https://example.com/path chat_id 123456789")
    assert "example.com" not in redacted
    assert "123456789" not in redacted
    assert "botTokenSecret123" not in redacted
    assert "[REDACTED_URL]" in redacted
    assert "[REDACTED_CHAT_LIKE]" in redacted


def test_each_supported_message_class_is_classified():
    module = importlib.import_module("live_contentops.telegram_remote_operator_inbox")
    classes = {m["message_class"] for m in module.build_inbox_packet()["inbound_messages"]}
    for expected in module.SUPPORTED_MESSAGE_CLASSES:
        assert expected in classes


def test_allowed_forbidden_use_lists_exact():
    module = importlib.import_module("live_contentops.telegram_remote_operator_inbox")
    item = module.build_inbox_packet()["inbound_messages"][0]
    assert item["allowed_use"] == ["intent_parsing", "idea_capture", "review_response_candidate"]
    assert item["forbidden_use"] == ["direct_dispatch", "credential_access", "approval_without_challenge", "live_send", "platform_api_call"]


def test_telegram_channel_dispatch_destination_distinct_from_inbox():
    module = importlib.import_module("live_contentops.telegram_remote_operator_inbox")
    packet = module.build_inbox_packet()
    assert packet["telegram_surface"] == "remote_operator_inbox"
    assert packet["telegram_channel_dispatch_surface_status"] == "proven_frozen_distinct_surface"


def test_no_live_network_env_provider_platform_behavior():
    module = importlib.import_module("live_contentops.telegram_remote_operator_inbox")
    packet = module.build_inbox_packet()
    for key in [
        "network_performed", "telegram_api_called", "platform_api_called",
        "provider_api_called", "llm_provider_api_called", "credential_read",
        "env_read", "dotenv_read", "scheduler_enabled", "live_post_performed",
        "autonomous_replies_or_dms", "scraping_performed",
        "public_ready_content_generated", "approval_ledger_mutated",
        "dispatch_outbox_mutated", "attachments_ingested", "voice_notes_ingested",
        "media_ingested",
    ]:
        assert packet[key] is False


def test_deterministic_packet_doc_generation_and_unsafe_path_refusal(tmp_path):
    module = importlib.import_module("live_contentops.telegram_remote_operator_inbox")
    first = module.write_artifacts(REPO_ROOT)
    second = module.write_artifacts(REPO_ROOT)
    assert first == second
    assert (REPO_ROOT / module.DOC_REL_DIR / module.PACKET_FILENAME).exists()
    assert (REPO_ROOT / module.DOC_REL_DIR / module.DOC_FILENAME).exists()
    assert (REPO_ROOT / module.DOC_REL_DIR / module.FIXTURE_FILENAME).exists()
    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        module.write_artifacts(REPO_ROOT, tmp_path)
