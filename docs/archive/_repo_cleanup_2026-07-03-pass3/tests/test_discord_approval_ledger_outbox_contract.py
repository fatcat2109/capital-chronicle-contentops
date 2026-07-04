import copy
import json

from live_contentops import discord_approval_ledger_outbox_contract as ledger
from live_contentops import discord_payload_hash_approval_gate as gate
from live_contentops import discord_webhook_payload_contract as payload_contract


def sample_hash_approval_packet():
    payload_packet = payload_contract.write_sample_payloads("docs/automation/DISCORD_WEBHOOK_PAYLOAD_CONTRACT/sample_payloads.json")
    return gate.build_hash_approval_gate_packet(payload_packet)


def test_ledger_produces_6_records_from_6_approval_packets():
    packet = sample_hash_approval_packet()
    records = ledger.build_ledger_records(packet)
    assert len(packet["approval_packets"]) == 6
    assert len(records) == 6
    assert all(item["ledger_append_only"] is True for item in records)


def test_ledger_is_deterministic_for_same_input():
    packet = sample_hash_approval_packet()
    first = ledger.build_ledger_records(packet)
    second = ledger.build_ledger_records(copy.deepcopy(packet))
    assert first == second


def test_blocked_approval_packet_is_not_dispatch_eligible():
    payload = payload_contract.render_dry_run(payload_contract.build_payload(
        payload_id="blocked_substack",
        payload_type="substack_drop",
        title="Safe title",
        body="Safe body",
        disclosure="Educational content only.",
    ))
    hash_packet = gate.build_payload_hash_packet(payload)
    approval = gate.build_approval_packet(payload, hash_packet)
    record = ledger.build_ledger_record(approval)
    assert record["ledger_entry_status"] == "blocked_not_recorded_for_dispatch"
    assert record["valid_for_dispatch"] is False
    assert record["dispatch_authorization_status"] == "not_authorized_in_this_task"


def test_no_ledger_record_has_valid_for_dispatch_or_dispatch_approval():
    records = ledger.build_ledger_records(sample_hash_approval_packet())
    assert all(item["valid_for_dispatch"] is False for item in records)
    assert all(item["dispatch_authorization_status"] == "not_authorized_in_this_task" for item in records)
    assert all(item["approved_at"] is None for item in records)


def test_outbox_produces_required_entries():
    packet = sample_hash_approval_packet()
    records = ledger.build_ledger_records(packet)
    entries = ledger.build_outbox_entries(records, ledger.hash_packets_by_payload_id(packet))
    payload_types = {item["payload_type"] for item in entries}
    assert set(ledger.REQUIRED_OUTBOX_PAYLOAD_TYPES).issubset(payload_types)
    assert len(entries) == 4


def test_every_outbox_entry_non_dispatchable_refused_no_network_no_webhook_load():
    packet = ledger.build_approval_ledger_outbox_packet(sample_hash_approval_packet())
    for entry in packet["outbox_entries"]:
        assert entry["eligible_for_dispatch"] is False
        assert entry["send_gate_decision"] == "REFUSE"
        assert entry["network_call_attempted"] is False
        assert entry["webhook_url_loaded"] is False
        assert entry["live_write_allowed_now"] is False
        assert entry["dispatch_attempt_count"] == 0
        assert entry["auto_retry_allowed"] is False


def test_idempotency_key_deterministic_for_same_fields():
    key1 = ledger.idempotency_key("a" * 64, "dest", "cred", "announcement", "announcements")
    key2 = ledger.idempotency_key("a" * 64, "dest", "cred", "announcement", "announcements")
    assert key1 == key2
    assert len(key1) == 64


def test_idempotency_key_changes_when_payload_hash_changes():
    key1 = ledger.idempotency_key("a" * 64, "dest", "cred", "announcement", "announcements")
    key2 = ledger.idempotency_key("b" * 64, "dest", "cred", "announcement", "announcements")
    assert key1 != key2


def test_duplicate_suppression_key_deterministic():
    key1 = ledger.duplicate_suppression_key("a" * 64, "announcements", "dest")
    key2 = ledger.duplicate_suppression_key("a" * 64, "announcements", "dest")
    assert key1 == key2
    assert len(key1) == 64


def first_record_entry_hash_packet():
    packet = sample_hash_approval_packet()
    records = ledger.build_ledger_records(packet)
    hash_map = ledger.hash_packets_by_payload_id(packet)
    record = next(item for item in records if item["payload_type"] == "announcement")
    entry = ledger.build_outbox_entry(record, hash_map[record["payload_id"]])
    return record, entry, hash_map[record["payload_id"]]


def test_revalidation_passes_only_as_pass_non_dispatchable_for_exact_match():
    record, entry, hash_packet = first_record_entry_hash_packet()
    result = ledger.revalidate_outbox_entry(record, entry, hash_packet)
    assert result["revalidation_status"] == "pass_non_dispatchable"
    assert result["eligible_for_dispatch"] is False
    assert result["blockers"] == []


def test_revalidation_blocks_destination_mismatch():
    record, entry, hash_packet = first_record_entry_hash_packet()
    changed = copy.deepcopy(entry)
    changed["destination_binding_id"] = "different_destination"
    result = ledger.revalidate_outbox_entry(record, changed, hash_packet)
    assert result["revalidation_status"] == "blocked_destination_mismatch"


def test_revalidation_blocks_credential_handle_mismatch():
    record, entry, hash_packet = first_record_entry_hash_packet()
    changed = copy.deepcopy(entry)
    changed["credential_handle_id"] = "different_credential"
    result = ledger.revalidate_outbox_entry(record, changed, hash_packet)
    assert result["revalidation_status"] == "blocked_credential_handle_mismatch"


def test_revalidation_blocks_payload_hash_mismatch():
    record, entry, hash_packet = first_record_entry_hash_packet()
    changed = copy.deepcopy(entry)
    changed["payload_hash"] = "b" * 64
    result = ledger.revalidate_outbox_entry(record, changed, hash_packet)
    assert result["revalidation_status"] == "blocked_payload_hash_mismatch"


def test_audit_event_preview_contains_only_hash_and_binding_identifiers():
    record, entry, _hash_packet = first_record_entry_hash_packet()
    audit = entry["audit_event_preview"]
    text = json.dumps(audit, sort_keys=True).lower()
    assert audit["payload_hash"] == record["payload_hash"]
    assert audit["destination_binding_id"] == record["destination_binding_id"]
    assert audit["credential_handle_id"] == record["credential_handle_id"]
    assert audit["send_gate_decision"] == "REFUSE"
    assert audit["response_class"] == "not_attempted"
    assert "discord.com/api/webhooks" not in text
    assert "token_value" not in text
    assert "token_length" not in text
    assert "token_prefix" not in text
    assert "token_suffix" not in text
    assert "token_digest" not in text
    assert "token_hash" not in text


def test_generated_packet_contains_no_webhook_url_or_token_terms():
    packet = ledger.build_approval_ledger_outbox_packet(sample_hash_approval_packet())
    text = json.dumps(packet, sort_keys=True).lower()
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    assert "token_value" not in text
    assert "token_length" not in text
    assert "token_prefix" not in text
    assert "token_suffix" not in text
    assert "token_digest" not in text
    assert "token_hash" not in text
    assert packet["network_call_attempted"] is False
    assert packet["webhook_url_loaded"] is False
    assert packet["live_write_allowed_now"] is False
