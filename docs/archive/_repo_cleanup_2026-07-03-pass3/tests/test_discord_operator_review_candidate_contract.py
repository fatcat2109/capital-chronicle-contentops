import copy
import json

from live_contentops import discord_approval_ledger_outbox_contract as outbox
from live_contentops import discord_operator_review_candidate_contract as review
from live_contentops import discord_payload_hash_approval_gate as gate
from live_contentops import discord_webhook_payload_contract as payload_contract


def sample_outbox_packet():
    payload_packet = payload_contract.write_sample_payloads("docs/automation/DISCORD_WEBHOOK_PAYLOAD_CONTRACT/sample_payloads.json")
    hash_packet = gate.build_hash_approval_gate_packet(payload_packet)
    return outbox.build_approval_ledger_outbox_packet(hash_packet, "docs/automation/DISCORD_PAYLOAD_HASH_APPROVAL_GATE/hash_approval_gate_packet.json")


def sample_candidate_packet():
    return review.build_operator_review_candidate_packet(sample_outbox_packet(), "docs/automation/DISCORD_APPROVAL_LEDGER_OUTBOX/approval_ledger_outbox_packet.json")


def first_entry():
    return sample_outbox_packet()["outbox_entries"][0]


def test_review_records_are_built_for_4_outbox_entries():
    packet = sample_candidate_packet()
    assert len(packet["review_records"]) == 4
    assert packet["summary"]["review_record_count"] == 4


def test_review_records_preserve_exact_payload_hash_binding_and_credential():
    outbox_packet = sample_outbox_packet()
    packet = review.build_operator_review_candidate_packet(outbox_packet)
    by_outbox = {entry["outbox_entry_id"]: entry for entry in outbox_packet["outbox_entries"]}
    for record in packet["review_records"]:
        source = by_outbox[record["source_outbox_entry_id"]]
        assert record["payload_hash"] == source["payload_hash"]
        assert record["destination_binding_id"] == source["destination_binding_id"]
        assert record["credential_handle_id"] == source["credential_handle_id"]


def test_only_pass_non_dispatchable_entries_become_candidate_ready():
    entry = first_entry()
    record = review.build_review_record(entry)
    candidate = review.build_dispatch_candidate(record, entry)
    assert record["dispatch_candidate_allowed"] is True
    assert candidate["candidate_status"] == review.CANDIDATE_READY


def test_failed_revalidation_blocks_candidate():
    entry = copy.deepcopy(first_entry())
    entry["revalidation_status"] = "blocked_payload_hash_mismatch"
    record = review.build_review_record(entry)
    candidate = review.build_dispatch_candidate(record, entry)
    assert record["dispatch_candidate_allowed"] is False
    assert candidate["candidate_status"] == review.BLOCKED_REVIEW


def test_send_gate_decision_other_than_refuse_blocks_candidate():
    entry = copy.deepcopy(first_entry())
    entry["send_gate_decision"] = "ALLOW"
    record = review.build_review_record(entry)
    candidate = review.build_dispatch_candidate(record, entry)
    assert "blocked_send_gate_not_refuse" in candidate["blockers"]
    assert candidate["candidate_status"] == review.BLOCKED_REVIEW


def test_eligible_for_dispatch_true_blocks_candidate_in_this_task():
    entry = copy.deepcopy(first_entry())
    entry["eligible_for_dispatch"] = True
    record = review.build_review_record(entry)
    candidate = review.build_dispatch_candidate(record, entry)
    assert "blocked_eligible_for_dispatch_not_false" in candidate["blockers"]
    assert candidate["candidate_status"] == review.BLOCKED_REVIEW


def test_live_write_allowed_now_true_blocks_candidate_in_this_task():
    entry = copy.deepcopy(first_entry())
    entry["live_write_allowed_now"] = True
    record = review.build_review_record(entry)
    candidate = review.build_dispatch_candidate(record, entry)
    assert "blocked_live_write_allowed_now_not_false" in candidate["blockers"]
    assert candidate["candidate_status"] == review.BLOCKED_REVIEW


def test_dispatch_candidates_are_never_valid_or_dispatchable_in_this_task():
    packet = sample_candidate_packet()
    for candidate in packet["dispatch_candidates"]:
        assert candidate["valid_for_dispatch"] is False
        assert candidate["current_task_dispatchable"] is False
        assert candidate["live_write_allowed_now"] is False
        assert candidate["network_call_attempted"] is False
        assert candidate["webhook_url_loaded"] is False


def test_future_live_task_and_explicit_operator_live_approval_required():
    packet = sample_candidate_packet()
    for candidate in packet["dispatch_candidates"]:
        assert candidate["future_live_task_required"] is True
        assert candidate["explicit_operator_live_approval_required"] is True


def test_endpoint_family_method_request_budget_remain_null_and_allowlists_empty():
    packet = sample_candidate_packet()
    for candidate in packet["dispatch_candidates"]:
        assert candidate["endpoint_family"] is None
        assert candidate["method"] is None
        assert candidate["request_budget"] is None
        assert candidate["host_allowlist"] == []
        assert candidate["path_family_allowlist"] == []


def test_generated_packet_contains_no_webhook_url_or_token_terms():
    packet = sample_candidate_packet()
    text = json.dumps(packet, sort_keys=True).lower()
    assert "discord.com/api/webhooks" not in text
    assert "discordapp.com/api/webhooks" not in text
    for term in ["token_value", "token_length", "token_prefix", "token_suffix", "token_digest", "token_hash"]:
        assert term not in text
    assert packet["network_call_attempted"] is False
    assert packet["webhook_url_loaded"] is False
    assert packet["endpoint_url_loaded"] is False


def test_generated_summary_contains_no_webhook_url_and_non_dispatchable_state():
    packet = sample_candidate_packet()
    summary = review.render_operator_review_summary(packet)
    lower = summary.lower()
    assert "discord.com/api/webhooks" not in lower
    assert "discordapp.com/api/webhooks" not in lower
    assert "current_task_dispatchable=false" in summary
    assert "no live send happened" in lower


def test_secret_like_material_blocks_candidate():
    entry = copy.deepcopy(first_entry())
    entry["unsafe_debug"] = "discord.com/api/webhooks/unsafe"
    record = review.build_review_record(entry)
    candidate = review.build_dispatch_candidate(record, entry)
    assert candidate["candidate_status"] == review.BLOCKED_SECRET
