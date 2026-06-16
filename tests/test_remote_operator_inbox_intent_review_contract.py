"""Tests for the 0174TG/TH/TI remote operator inbox + intent + review contract.

Deterministic, stdlib-only, offline. These tests assert the LOCAL authority
chain: 0174TG inbox normalization (fail-closed redaction, surface/identity/chat
binding gates), 0174TH deterministic rule-based intent parsing (no LLM, fail
closed on ambiguity, vague agreement is never approval), and 0174TI review
challenge creation + validation (exact outbox/idempotency/payload-hash binding,
approval is never dispatch).
"""

import hashlib
import json

import pytest

from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import dispatch_outbox_idempotency_contract as outbox
from live_contentops import remote_operator_inbox_intent_review_contract as rc


# --------------------------------------------------------------------------- #
# Fixtures / helpers
# --------------------------------------------------------------------------- #
def _good_inbound(**overrides):
    base = {
        "source_surface_class": rc.SOURCE_SURFACE_CLASS,
        "inbound_message_id": "inbound_msg_0001",
        "received_at_epoch": 1_700_000_000,
        "operator_id": "operator_jim",
        "operator_identity_class": rc.IDENTITY_VERIFIED,
        "chat_binding_id": "chat_binding_alpha",
        "chat_binding_hash": "a" * 64,
        "message_text_redacted": "REVIEW",
        "reply_to_challenge_id": None,
        "linked_outbox_entry_id": None,
        "linked_idempotency_key": None,
    }
    base.update(overrides)
    return base


def _good_outbox_entry(**overrides):
    base = {
        "outbox_schema": "contentops.dispatch_outbox_entry",
        "outbox_entry_id": "outbox_entry_0001",
        "idempotency_key": "f" * 64,
        "payload_hash": "e" * 64,
        "approval_ledger_entry_id": "ledger_entry_0001",
        "platform": "telegram",
        "destination_binding_id": "chat_binding_alpha",
        "credential_handle_id": "cred_handle_alpha",
        "visibility_class": "public",
        "dispatch_intent_class": "supervised_single",
    }
    base.update(overrides)
    return base


def _approve_intent(challenge_id, *, phrase=rc.DEFAULT_APPROVAL_PHRASE,
                    operator_id="operator_jim"):
    """Build an inbox record whose text is the exact approval phrase, parse it."""
    inbound = _good_inbound(
        inbound_message_id="inbound_msg_approve",
        message_text_redacted=phrase,
        reply_to_challenge_id=challenge_id,
        operator_id=operator_id,
    )
    norm = rc.normalize_inbound_envelope(inbound)
    assert norm["status"] == rc.InboxStatus.PASS
    return rc.parse_operator_intent(
        norm["record"], required_approval_phrase=phrase)


# --------------------------------------------------------------------------- #
# 0174TG: inbox normalization
# --------------------------------------------------------------------------- #
def test_inbox_normalizes_valid_envelope():
    res = rc.normalize_inbound_envelope(_good_inbound())
    assert res["status"] == rc.InboxStatus.PASS
    assert res["inbound_status_class"] == rc.INBOX_NORMALIZED
    rec = res["record"]
    assert rec["source_surface_class"] == rc.SOURCE_SURFACE_CLASS
    assert rec["operator_identity_class"] == rc.IDENTITY_VERIFIED
    assert rec["message_provenance_hash"]
    assert rec["record_checksum"]
    assert res["redaction_verified"] is True


def test_inbox_provenance_hash_is_deterministic():
    a = rc.normalize_inbound_envelope(_good_inbound())["record"]
    b = rc.normalize_inbound_envelope(_good_inbound())["record"]
    assert a["message_provenance_hash"] == b["message_provenance_hash"]


def test_inbox_blocks_wrong_surface():
    res = rc.normalize_inbound_envelope(
        _good_inbound(source_surface_class="some_other_surface"))
    assert res["status"] == rc.InboxStatus.BLOCKED
    assert rc.BLOCK_BAD_SURFACE in res["blocked_reasons"]
    assert res["record"] is None


def test_inbox_blocks_unverified_operator():
    res = rc.normalize_inbound_envelope(
        _good_inbound(operator_identity_class=rc.IDENTITY_UNVERIFIED))
    assert res["status"] == rc.InboxStatus.BLOCKED
    assert rc.BLOCK_OPERATOR_NOT_VERIFIED in res["blocked_reasons"]


def test_inbox_blocks_missing_chat_binding():
    res = rc.normalize_inbound_envelope(_good_inbound(chat_binding_id=None))
    assert res["status"] == rc.InboxStatus.BLOCKED
    assert rc.BLOCK_MISSING_CHAT_BINDING in res["blocked_reasons"]


def test_inbox_blocks_missing_required_field():
    res = rc.normalize_inbound_envelope(
        _good_inbound(message_text_redacted=None))
    assert res["status"] == rc.InboxStatus.BLOCKED
    assert any(r.startswith(rc.BLOCK_MISSING_INBOUND_FIELD)
               for r in res["blocked_reasons"])


def test_inbox_expected_operator_mismatch_blocks():
    res = rc.normalize_inbound_envelope(
        _good_inbound(), expected_operator_id="someone_else")
    assert res["status"] == rc.InboxStatus.BLOCKED
    assert rc.BLOCK_OPERATOR_NOT_VERIFIED in res["blocked_reasons"]


def test_inbox_fail_closed_on_forbidden_value():
    # A raw bot token-like value trips the fail-closed scanner.
    bad = _good_inbound(
        message_text_redacted="123456789:AAFakeTelegramBotTokenForTestsOnly0123456789")
    res = rc.normalize_inbound_envelope(bad)
    assert res["status"] == rc.InboxStatus.FAIL_CLOSED
    assert res["inbound_status_class"] == rc.INBOX_FAIL_CLOSED
    assert rc.BLOCK_FORBIDDEN_VALUE in res["blocked_reasons"]
    assert res["record"] is None
    assert res["redaction_verified"] is False


def test_inbox_safety_flags_present():
    res = rc.normalize_inbound_envelope(_good_inbound())
    for flag in ("telegram_api_called", "get_updates_performed",
                 "send_message_performed", "network_performed",
                 "raw_telegram_update_persisted", "credential_hydrated",
                 "llm_behavior", "dispatch_performed"):
        assert res[flag] is False


# --------------------------------------------------------------------------- #
# 0174TG: registry
# --------------------------------------------------------------------------- #
def test_registry_appends_pass_record():
    reg = rc.RemoteOperatorInboxRegistry()
    res = rc.normalize_inbound_envelope(_good_inbound())
    appended = reg.append(res)
    assert reg.record_count() == 1
    assert appended["inbound_message_id"] == "inbound_msg_0001"
    found = reg.find_by_message_id("inbound_msg_0001")
    assert found is not None


def test_registry_rejects_non_pass_result():
    reg = rc.RemoteOperatorInboxRegistry()
    blocked = rc.normalize_inbound_envelope(
        _good_inbound(chat_binding_id=None))
    with pytest.raises(ValueError):
        reg.append(blocked)


def test_registry_records_are_copies():
    reg = rc.RemoteOperatorInboxRegistry()
    reg.append(rc.normalize_inbound_envelope(_good_inbound()))
    snap = reg.records
    snap[0]["operator_id"] = "tampered"
    assert reg.records[0]["operator_id"] == "operator_jim"


# --------------------------------------------------------------------------- #
# 0174TH: intent parser
# --------------------------------------------------------------------------- #
def test_intent_policy_snapshot_shape():
    pol = rc.build_intent_policy_snapshot()
    assert pol["parser_kind"] == "deterministic_rule_based_no_llm"
    assert pol["fails_closed_on_ambiguity"] is True
    assert pol["llm_behavior"] is False


def test_intent_exact_phrase_is_explicit_approve():
    rec = rc.normalize_inbound_envelope(
        _good_inbound(message_text_redacted="APPROVE"))["record"]
    res = rc.parse_operator_intent(rec)
    assert res["intent_class"] == rc.INTENT_EXPLICIT_APPROVE
    assert res["is_explicit_approve"] is True
    assert res["matched_token"] == "APPROVE"


def test_intent_phrase_plus_challenge_id_is_approve():
    rec = rc.normalize_inbound_envelope(
        _good_inbound(message_text_redacted="APPROVE chal_0001"))["record"]
    res = rc.parse_operator_intent(rec, expected_challenge_id="chal_0001")
    assert res["intent_class"] == rc.INTENT_EXPLICIT_APPROVE


def test_intent_vague_agreement_is_not_approval():
    for text in ("ok", "looks good", "lgtm", "sure", "👍", "yes"):
        rec = rc.normalize_inbound_envelope(
            _good_inbound(message_text_redacted=text))["record"]
        res = rc.parse_operator_intent(rec)
        assert res["intent_class"] == rc.INTENT_AMBIGUOUS, text
        assert res["is_explicit_approve"] is False, text


def test_intent_explicit_commands():
    cases = {
        "REVIEW": rc.INTENT_EXPLICIT_REVIEW_REQUEST,
        "REJECT": rc.INTENT_EXPLICIT_REJECT,
        "DENY": rc.INTENT_EXPLICIT_REJECT,
        "EDIT": rc.INTENT_EXPLICIT_EDIT_REQUEST,
        "STATUS": rc.INTENT_STATUS_REQUEST,
        "CANCEL": rc.INTENT_CANCEL_REQUEST,
    }
    for text, expected in cases.items():
        rec = rc.normalize_inbound_envelope(
            _good_inbound(message_text_redacted=text))["record"]
        res = rc.parse_operator_intent(rec)
        assert res["intent_class"] == expected, text


def test_intent_conflicting_commands_are_ambiguous():
    rec = rc.normalize_inbound_envelope(
        _good_inbound(message_text_redacted="REVIEW CANCEL"))["record"]
    res = rc.parse_operator_intent(rec)
    assert res["intent_class"] == rc.INTENT_AMBIGUOUS


def test_intent_partial_approval_is_ambiguous():
    rec = rc.normalize_inbound_envelope(
        _good_inbound(message_text_redacted="i think we should APPROVE this"))[
            "record"]
    res = rc.parse_operator_intent(rec)
    assert res["intent_class"] == rc.INTENT_AMBIGUOUS
    assert res["is_explicit_approve"] is False


def test_intent_never_creates_state():
    rec = rc.normalize_inbound_envelope(
        _good_inbound(message_text_redacted="APPROVE"))["record"]
    res = rc.parse_operator_intent(rec)
    assert res["creates_approval_state"] is False
    assert res["creates_dispatch_state"] is False
    assert res["llm_behavior"] is False
    assert res["network_performed"] is False


def test_intent_preserves_provenance_hash():
    rec = rc.normalize_inbound_envelope(_good_inbound())["record"]
    res = rc.parse_operator_intent(rec)
    assert res["source_message_provenance_hash"] == rec[
        "message_provenance_hash"]


# --------------------------------------------------------------------------- #
# 0174TI: review challenge creation
# --------------------------------------------------------------------------- #
def test_create_challenge_binds_outbox_entry():
    ch = rc.create_review_challenge(
        _good_outbox_entry(), "chal_0001", "operator_jim",
        created_at_epoch=1_700_000_000, expires_at_epoch=1_700_003_600)
    assert ch["challenge_id"] == "chal_0001"
    assert ch["outbox_entry_id"] == "outbox_entry_0001"
    assert ch["idempotency_key"] == "f" * 64
    assert ch["payload_hash"] == "e" * 64
    assert ch["challenge_status"] == rc.CHALLENGE_PENDING
    assert ch["challenge_checksum"]
    assert ch["dispatch_performed"] is False
    assert ch["credential_hydrated"] is False


def test_create_challenge_requires_binding_fields():
    with pytest.raises(ValueError):
        rc.create_review_challenge(
            _good_outbox_entry(payload_hash=None), "chal_x", "operator_jim",
            created_at_epoch=1, expires_at_epoch=2)


def test_create_challenge_fail_closed_on_forbidden():
    bad = _good_outbox_entry(
        destination_binding_id="123456789:AAFakeTelegramBotTokenForTestsOnly0123456789")
    with pytest.raises(ValueError):
        rc.create_review_challenge(
            bad, "chal_x", "operator_jim",
            created_at_epoch=1, expires_at_epoch=2)


# --------------------------------------------------------------------------- #
# 0174TI: review challenge validation
# --------------------------------------------------------------------------- #
def _pending_challenge(**overrides):
    return rc.create_review_challenge(
        _good_outbox_entry(), "chal_0001", "operator_jim",
        created_at_epoch=1_700_000_000, expires_at_epoch=1_700_003_600,
        **overrides)


def test_validation_approves_explicit_approve():
    ch = _pending_challenge()
    intent = _approve_intent("chal_0001")
    res = rc.validate_review_challenge_response(
        ch, intent, _good_outbox_entry(), now_epoch=1_700_000_100,
        responding_operator_id="operator_jim")
    assert res["status"] == rc.InboxStatus.PASS
    assert res["review_outcome_class"] == rc.REVIEW_APPROVED_NOT_DISPATCHED
    assert res["approved_not_dispatched"] is True
    assert res["dispatch_performed"] is False
    assert res["remote_approval_is_dispatch"] is False


def test_validation_blocks_wrong_operator():
    ch = _pending_challenge()
    intent = _approve_intent("chal_0001")
    res = rc.validate_review_challenge_response(
        ch, intent, _good_outbox_entry(), now_epoch=1_700_000_100,
        responding_operator_id="operator_someone_else")
    assert res["review_outcome_class"] == rc.REVIEW_NOT_APPROVED
    assert rc.BLOCK_OPERATOR_MISMATCH in res["blocked_reasons"]


def test_validation_blocks_non_approve_intent():
    ch = _pending_challenge()
    rec = rc.normalize_inbound_envelope(
        _good_inbound(message_text_redacted="REJECT",
                      reply_to_challenge_id="chal_0001"))["record"]
    intent = rc.parse_operator_intent(rec)
    res = rc.validate_review_challenge_response(
        ch, intent, _good_outbox_entry(), now_epoch=1_700_000_100,
        responding_operator_id="operator_jim")
    assert res["review_outcome_class"] == rc.REVIEW_NOT_APPROVED
    assert rc.BLOCK_INTENT_NOT_APPROVE in res["blocked_reasons"]


def test_validation_blocks_expired_challenge():
    ch = _pending_challenge()
    intent = _approve_intent("chal_0001")
    res = rc.validate_review_challenge_response(
        ch, intent, _good_outbox_entry(), now_epoch=1_700_999_999,
        responding_operator_id="operator_jim")
    assert rc.BLOCK_CHALLENGE_EXPIRED in res["blocked_reasons"]


def test_validation_blocks_challenge_id_mismatch():
    ch = _pending_challenge()
    intent = _approve_intent("chal_DIFFERENT")
    res = rc.validate_review_challenge_response(
        ch, intent, _good_outbox_entry(), now_epoch=1_700_000_100,
        responding_operator_id="operator_jim")
    assert rc.BLOCK_CHALLENGE_ID_MISMATCH in res["blocked_reasons"]


def test_validation_blocks_outbox_entry_substitution():
    ch = _pending_challenge()
    intent = _approve_intent("chal_0001")
    substituted = _good_outbox_entry(outbox_entry_id="outbox_entry_EVIL")
    res = rc.validate_review_challenge_response(
        ch, intent, substituted, now_epoch=1_700_000_100,
        responding_operator_id="operator_jim")
    assert rc.BLOCK_OUTBOX_ENTRY_MISMATCH in res["blocked_reasons"]


def test_validation_blocks_payload_hash_substitution():
    ch = _pending_challenge()
    intent = _approve_intent("chal_0001")
    substituted = _good_outbox_entry(payload_hash="d" * 64)
    res = rc.validate_review_challenge_response(
        ch, intent, substituted, now_epoch=1_700_000_100,
        responding_operator_id="operator_jim")
    assert rc.BLOCK_PAYLOAD_HASH_MISMATCH in res["blocked_reasons"]


def test_validation_blocks_idempotency_key_substitution():
    ch = _pending_challenge()
    intent = _approve_intent("chal_0001")
    substituted = _good_outbox_entry(idempotency_key="c" * 64)
    res = rc.validate_review_challenge_response(
        ch, intent, substituted, now_epoch=1_700_000_100,
        responding_operator_id="operator_jim")
    assert rc.BLOCK_IDEMPOTENCY_KEY_MISMATCH in res["blocked_reasons"]


def test_validation_blocks_nonce_mismatch():
    ch = _pending_challenge(one_time_nonce="nonce_correct")
    intent = _approve_intent("chal_0001")
    res = rc.validate_review_challenge_response(
        ch, intent, _good_outbox_entry(), now_epoch=1_700_000_100,
        responding_operator_id="operator_jim",
        provided_nonce="nonce_WRONG")
    assert rc.BLOCK_NONCE_MISMATCH in res["blocked_reasons"]


def test_validation_fail_closed_on_forbidden():
    ch = _pending_challenge()
    intent = _approve_intent("chal_0001")
    bad_entry = _good_outbox_entry(
        destination_binding_id="123456789:AAFakeTelegramBotTokenForTestsOnly0123456789")
    res = rc.validate_review_challenge_response(
        ch, intent, bad_entry, now_epoch=1_700_000_100,
        responding_operator_id="operator_jim")
    assert res["status"] == rc.InboxStatus.FAIL_CLOSED
    assert res["review_outcome_class"] == rc.REVIEW_FAIL_CLOSED
    assert res["forbidden_fields_detected"] is True


# --------------------------------------------------------------------------- #
# 0174TI: registry (dedupe + revocation)
# --------------------------------------------------------------------------- #
def test_challenge_registry_appends_and_dedupes():
    reg = rc.RemoteReviewChallengeRegistry()
    ch = _pending_challenge()
    first = reg.append(ch)
    assert first["appended"] is True
    second = reg.append(ch)
    assert second["appended"] is False
    assert second["duplicate_suppressed"] is True
    assert reg.challenge_count() == 1


def test_challenge_registry_revocation_blocks_later_approval():
    reg = rc.RemoteReviewChallengeRegistry()
    ch = _pending_challenge()
    reg.append(ch)
    reg.revoke("chal_0001", revoked_at_epoch=1_700_000_200,
               operator_id="operator_jim")
    assert reg.current_status("chal_0001") == rc.CHALLENGE_INVALIDATED
    invalidated = reg.current("chal_0001")
    intent = _approve_intent("chal_0001")
    res = rc.validate_review_challenge_response(
        invalidated, intent, _good_outbox_entry(), now_epoch=1_700_000_300,
        responding_operator_id="operator_jim")
    assert res["review_outcome_class"] == rc.REVIEW_NOT_APPROVED
    assert rc.BLOCK_CHALLENGE_NOT_PENDING in res["blocked_reasons"]


def test_challenge_registry_revoke_unknown_raises():
    reg = rc.RemoteReviewChallengeRegistry()
    with pytest.raises(ValueError):
        reg.revoke("nope", revoked_at_epoch=1, operator_id="operator_jim")


# --------------------------------------------------------------------------- #
# Audit + packet + doc
# --------------------------------------------------------------------------- #
def test_redacted_audit_has_no_raw_material():
    ch = _pending_challenge()
    intent = _approve_intent("chal_0001")
    vr = rc.validate_review_challenge_response(
        ch, intent, _good_outbox_entry(), now_epoch=1_700_000_100,
        responding_operator_id="operator_jim")
    audit = rc.build_redacted_review_audit(ch, vr)
    assert audit["no_raw_telegram_update_stored"] is True
    assert audit["no_raw_token_or_webhook_stored"] is True
    assert audit["approved_not_dispatched"] is True
    assert audit["audit_checksum"]
    # The audit itself must pass the redaction scanner.
    assert rc.scan_for_leaks(audit) == []


def test_packet_is_deterministic_and_clean():
    a = rc.build_packet()
    b = rc.build_packet()
    assert a["checksum_sha256"] == b["checksum_sha256"]
    assert a["status"] == rc.InboxStatus.PASS
    assert a["safety_flags"]["autonomous_posting_allowed"] is False
    assert a["safety_flags"]["no_network_performed"] is True
    assert rc.scan_for_leaks(a) == []


def test_doc_mentions_core_invariants():
    doc = rc.build_doc()
    assert "0174TG" in doc
    assert "Autonomous posting is forbidden" in doc
    assert rc.REVIEW_APPROVED_NOT_DISPATCHED in doc


def test_packet_recommends_next_task():
    pkt = rc.build_packet()
    assert pkt["exact_next_task_recommendation"] == (
        rc.EXACT_NEXT_TASK_RECOMMENDATION)

