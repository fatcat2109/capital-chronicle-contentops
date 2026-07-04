import copy
import json

from live_contentops import discord_payload_hash_approval_gate as gate
from live_contentops import discord_webhook_payload_contract as payload_contract


def render(payload_type="announcement", **overrides):
    kwargs = {
        "payload_id": f"hash_test_{payload_type}",
        "payload_type": payload_type,
        "title": "Safe title",
        "body": "Safe body for operator review.",
        "disclosure": "Educational content only.",
    }
    if payload_type == "substack_drop":
        kwargs["discussion_question"] = "What should we research next?"
    kwargs.update(overrides)
    return payload_contract.render_dry_run(payload_contract.build_payload(**kwargs))


def test_hash_deterministic_for_same_payload():
    payload = render()
    assert gate.compute_payload_hash(payload) == gate.compute_payload_hash(copy.deepcopy(payload))


def test_hash_changes_when_title_changes():
    payload = render()
    changed = copy.deepcopy(payload)
    changed["title"] = "Changed title"
    assert gate.compute_payload_hash(payload) != gate.compute_payload_hash(changed)


def test_hash_changes_when_body_changes():
    payload = render()
    changed = copy.deepcopy(payload)
    changed["body"] = "Changed body."
    assert gate.compute_payload_hash(payload) != gate.compute_payload_hash(changed)


def test_hash_changes_when_destination_binding_changes():
    payload = render()
    changed = copy.deepcopy(payload)
    changed["destination_binding_id"] = "changed_destination_binding"
    assert gate.compute_payload_hash(payload) != gate.compute_payload_hash(changed)


def test_hash_changes_when_credential_handle_changes():
    payload = render()
    changed = copy.deepcopy(payload)
    changed["credential_handle_id"] = "changed_credential_handle"
    assert gate.compute_payload_hash(payload) != gate.compute_payload_hash(changed)


def test_hash_changes_when_discussion_question_changes():
    payload = render("substack_drop")
    changed = copy.deepcopy(payload)
    changed["discussion_question"] = "Changed question?"
    assert gate.compute_payload_hash(payload) != gate.compute_payload_hash(changed)


def test_hash_input_excludes_webhook_url_and_previews():
    payload = render()
    payload["redacted_webhook_json_preview"]["unsafe_extra"] = "https://discord.com/api/webhooks/123/abc"
    payload["human_readable_preview"] += " https://discord.com/api/webhooks/123/abc"
    hash_input = gate.payload_hash_input(payload)
    text = json.dumps(hash_input, sort_keys=True)
    assert "discord.com/api/webhooks" not in text
    assert "redacted_webhook_json_preview" not in text
    assert "human_readable_preview" not in text


def test_hash_input_excludes_token_value_and_metadata_terms():
    payload = render()
    payload["token_value"] = "sk-abcdefghijklmnopqrstuvwxyz123456"
    payload["token_length"] = 32
    payload["token_prefix"] = "sk-"
    payload["token_suffix"] = "3456"
    payload["token_digest"] = "abc"
    payload["token_hash"] = "def"
    hash_input = gate.payload_hash_input(payload)
    text = json.dumps(hash_input, sort_keys=True).lower()
    assert "sk-abcdefghijklmnopqrstuvwxyz123456" not in text
    assert "token_length" not in text
    assert "token_prefix" not in text
    assert "token_suffix" not in text
    assert "token_digest" not in text
    assert "token_hash" not in text


def test_blocked_payload_hashable_but_not_approval_eligible():
    payload = render("substack_drop", discussion_question=None)
    assert payload["validation_status"] == "blocked"
    hash_packet = gate.build_payload_hash_packet(payload)
    approval = gate.build_approval_packet(payload, hash_packet)
    assert len(hash_packet["payload_hash"]) == 64
    assert approval["approval_status"] == "blocked_payload_not_approval_eligible"
    assert approval["valid_for_dispatch"] is False


def test_valid_payload_gets_dry_run_approval_packet():
    payload = render()
    hash_packet = gate.build_payload_hash_packet(payload)
    approval = gate.build_approval_packet(payload, hash_packet)
    assert approval["approval_status"] == "dry_run_review_packet_created"
    assert approval["operator_id"] == "Jim"
    assert approval["approval_scope"] == "dry_run_review_only"
    assert approval["approved_at"] is None


def test_approval_packet_is_not_dispatchable_in_this_task():
    payload = render()
    approval = gate.build_approval_packet(payload, gate.build_payload_hash_packet(payload))
    assert approval["valid_for_outbox"] is False
    assert approval["valid_for_dispatch"] is False
    assert approval["live_write_allowed_now"] is False
    assert approval["approval_required_for_future_dispatch"] is True


def test_send_gate_always_refuses_and_does_not_call_network_or_load_webhook_url():
    payload = render()
    hash_packet = gate.build_payload_hash_packet(payload)
    approval = gate.build_approval_packet(payload, hash_packet)
    decision = gate.evaluate_send_gate(payload, hash_packet, approval, {"schema_version": "discord_environment_contract.v1"})
    assert decision["decision"] == "REFUSE"
    assert decision["reason"] == "live_dispatch_not_authorized_in_this_task"
    assert decision["network_call_attempted"] is False
    assert decision["webhook_url_loaded"] is False
    assert decision["outbox_mutated"] is False
    assert decision["dispatch_success_marked"] is False


def test_audit_event_preview_contains_hash_and_binding_ids_only():
    payload = render()
    hash_packet = gate.build_payload_hash_packet(payload)
    approval = gate.build_approval_packet(payload, hash_packet)
    audit = gate.build_audit_event_preview(payload, hash_packet, approval)
    text = json.dumps(audit, sort_keys=True).lower()
    assert audit["payload_hash"] == hash_packet["payload_hash"]
    assert audit["destination_binding_id"] == payload["destination_binding_id"]
    assert audit["credential_handle_id"] == payload["credential_handle_id"]
    assert audit["response_class"] == "not_attempted"
    assert "discord.com/api/webhooks" not in text
    assert "token_value" not in text
    assert audit["network_call_attempted"] is False


def test_all_six_payload_types_represented_in_generated_packet(tmp_path):
    payload_packet = payload_contract.write_sample_payloads(tmp_path / "sample_payloads.json")
    packet = gate.build_hash_approval_gate_packet(payload_packet, {"schema_version": "discord_environment_contract.v1"})
    payload_types = {item["payload_type"] for item in packet["payload_hashes"]}
    assert payload_types == set(payload_contract.PAYLOAD_TARGETS)
    assert packet["summary"]["hash_count"] == 6
    assert packet["summary"]["approval_packet_count"] == 6


def test_required_send_gate_refusal_decisions_present(tmp_path):
    payload_packet = payload_contract.write_sample_payloads(tmp_path / "sample_payloads.json")
    packet = gate.build_hash_approval_gate_packet(payload_packet)
    decision_types = {item["payload_type"] for item in packet["send_gate_refusal_decisions"]}
    assert set(gate.REQUIRED_DECISION_TYPES).issubset(decision_types)
    assert all(item["decision"] == "REFUSE" for item in packet["send_gate_refusal_decisions"])
    assert all(item["network_call_attempted"] is False for item in packet["send_gate_refusal_decisions"])


def test_generated_packet_has_no_webhook_url_or_token_material(tmp_path):
    payload_packet = payload_contract.write_sample_payloads(tmp_path / "sample_payloads.json")
    packet = gate.build_hash_approval_gate_packet(payload_packet)
    text = json.dumps(packet, sort_keys=True).lower()
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    assert "token_value" not in text
    assert "token_length" not in text
    assert "token_prefix" not in text
    assert "token_suffix" not in text
    assert "token_digest" not in text
    assert "token_hash" not in text
    assert packet["live_write_allowed_now"] is False
    assert packet["network_call_attempted"] is False
    assert packet["webhook_url_loaded"] is False
