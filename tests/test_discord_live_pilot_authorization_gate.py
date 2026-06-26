import copy
import json
from pathlib import Path

from live_contentops import discord_approval_ledger_outbox_contract as outbox
from live_contentops import discord_live_pilot_authorization_gate as gate
from live_contentops import discord_operator_review_candidate_contract as review
from live_contentops import discord_payload_hash_approval_gate as hash_gate
from live_contentops import discord_webhook_payload_contract as payload_contract


def candidate_packet():
    payload_packet = payload_contract.write_sample_payloads("docs/automation/DISCORD_WEBHOOK_PAYLOAD_CONTRACT/sample_payloads.json")
    hash_packet = hash_gate.build_hash_approval_gate_packet(payload_packet)
    outbox_packet = outbox.build_approval_ledger_outbox_packet(hash_packet)
    return review.build_operator_review_candidate_packet(outbox_packet)


def gate_packet():
    return gate.build_live_pilot_authorization_gate_packet(candidate_packet(), gate.build_official_docs_lock())


def test_docs_lock_endpoint_family_method_path_template():
    docs = gate.build_official_docs_lock()
    assert docs["endpoint_family"] == "discord_execute_webhook"
    assert docs["method"] == "POST"
    assert docs["path_template"] == "/api/webhooks/{webhook.id}/{webhook.token}"
    assert docs["docs_confidence"] == "verified_from_official_docs"


def test_docs_lock_stores_no_actual_webhook_id_token_url():
    docs = gate.build_official_docs_lock()
    assert docs["raw_webhook_url_stored"] is False
    assert docs["webhook_id_stored"] is False
    assert docs["webhook_token_stored"] is False
    text = json.dumps(docs, sort_keys=True).lower()
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text


def test_candidate_selection_chooses_announcement_candidate():
    selected = gate.select_announcement_candidate(candidate_packet())
    assert selected["payload_type"] == "announcement"
    assert selected["target_name"] == "announcements"


def test_operator_private_candidate_is_not_selected_for_first_live_pilot():
    packet = candidate_packet()
    selected = gate.select_announcement_candidate(packet)
    assert selected["target_name"] != "operator_private"
    assert selected["payload_type"] != "operator_private_summary"


def test_credential_binding_maps_announcement_handle_without_loading_env_value():
    selected = gate.select_announcement_candidate(candidate_packet())
    binding = gate.build_credential_binding_plan(selected)
    assert binding["credential_handle_id"] == "discord_announcements_webhook_01"
    assert binding["destination_binding_id"] == "discord_announcements_capital_chronicle_01"
    assert binding["env_key_name"] == "DISCORD_ANNOUNCEMENTS_WEBHOOK_URL"
    assert binding["env_value_loaded"] is False
    assert binding["webhook_url_loaded"] is False
    assert binding["webhook_id_loaded"] is False
    assert binding["webhook_token_loaded"] is False


def test_live_gate_budget_timeout_wait_and_dispatch_flags():
    packet = gate_packet()
    assert packet["request_budget_max"] == 1
    assert packet["retry_budget_max"] == 0
    assert packet["timeout_seconds"] == 10
    assert packet["wait_query_param"] is False
    assert packet["webhook_url_hydration_allowed_now"] is False
    assert packet["network_dispatch_allowed_now"] is False
    assert packet["current_task_dispatchable"] is False
    assert packet["live_write_allowed_now"] is False


def test_future_phrase_and_kill_switch_are_required_but_not_read():
    packet = gate_packet()
    assert packet["operator_authorization_phrase_required"] == "AUTHORIZE_DISCORD_WEBHOOK_TEST_SEND_NOW"
    assert packet["kill_switch_required"] is True
    assert packet["kill_switch_env_key"] == "CONTENTOPS_LIVE_DISPATCH_KILL_SWITCH"
    assert packet["kill_switch_required_value"] == "ALLOW_DISCORD_TEST_SEND"
    assert packet["kill_switch_read_in_this_task"] is False


def test_request_plan_has_no_loaded_credential_or_webhook_material():
    plan = gate_packet()["request_plan"]
    assert plan["credential_value_loaded"] is False
    assert plan["webhook_url_loaded"] is False
    assert plan["webhook_id_loaded"] is False
    assert plan["webhook_token_loaded"] is False
    assert plan["headers_output"] is False
    assert plan["response_body_output"] is False
    assert plan["expected_response_class"] == "not_attempted_in_this_task"
    assert plan["current_task_network_call_attempted"] is False


def test_generated_packet_contains_no_webhook_url_or_token_terms():
    packet = gate_packet()
    text = json.dumps(packet, sort_keys=True).lower()
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    for term in ["token_value", "token_length", "token_prefix", "token_suffix", "token_digest", "token_hash"]:
        assert term not in text
    assert packet["network_call_attempted"] is False
    assert packet["webhook_url_loaded"] is False
    assert packet["endpoint_url_loaded"] is False


def test_generated_brief_contains_no_webhook_url_and_says_no_live_send_happened():
    brief = gate.render_operator_brief(gate_packet())
    lower = brief.lower()
    assert "discord.com/api/webhooks" not in lower
    assert "discordapp.com/api/webhooks" not in lower
    assert "no live send happened" in lower
    assert "current_task_dispatchable=false" in brief


def test_module_does_not_import_network_or_dispatch_libraries():
    source = Path("live_contentops/discord_live_pilot_authorization_gate.py").read_text(encoding="utf-8")
    for forbidden in ["import requests", "import httpx", "import urllib", "import socket", "from urllib", "from socket"]:
        assert forbidden not in source


def test_blocked_when_announcement_candidate_missing():
    packet = candidate_packet()
    packet["dispatch_candidates"] = [c for c in packet["dispatch_candidates"] if c["payload_type"] != "announcement"]
    try:
        gate.select_announcement_candidate(packet)
    except ValueError as exc:
        assert gate.BLOCKED_ANNOUNCEMENT_CANDIDATE_MISSING in str(exc)
    else:
        raise AssertionError("announcement candidate should be required")


def test_candidate_mismatch_blocks_gate_ready_status():
    packet = candidate_packet()
    selected = gate.select_announcement_candidate(packet)
    selected["credential_handle_id"] = "wrong_handle"
    result = gate.build_live_pilot_authorization_gate_packet(packet, gate.build_official_docs_lock())
    assert result["future_live_task_ready_status"] == "blocked_pre_live_gate_failed"
    assert gate.BLOCKED_CREDENTIAL_BINDING_MISMATCH in result["blockers"]
