"""Tests for the 0174TJ/TK/TL editorial + preview + supervised dry-run contract.

Deterministic, stdlib-only, offline. These tests assert the LOCAL authority
chain extension: 0174TJ editorial agent (consumes a genuine
``remote_review_approved_not_dispatched`` result + the exact 0174EE outbox
entry, fails closed on financial advice, never dispatches), 0174TK platform
preview (local symbolic preview only, never renders live), and 0174TL
supervised dry run (re-proves every cross-binding, never dispatches).

All upstream objects are built through the GENUINE authority chain
(0174ED -> 0174EE -> 0174TG/TH/TI), never via hand-rolled dicts, so the
bindings are real.
"""

import json

import pytest

from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import dispatch_outbox_idempotency_contract as outbox
from live_contentops import remote_operator_inbox_intent_review_contract as review
from live_contentops import editorial_preview_supervised_dry_run_contract as ep


# --------------------------------------------------------------------------- #
# Fixtures / helpers -- the genuine 0174ED -> 0174EE -> 0174TI chain
# --------------------------------------------------------------------------- #
def _payload():
    return approval.canonical_payload_dict(
        platform="telegram",
        payload_text="One CPI print is not a regime shift.",
        destination_binding_id="a" * 64,
        credential_handle_id="b" * 64,
        media_manifest_hash="c" * 64,
        visibility_class="public_default",
        content_lane="grounded_news_context",
        policy_snapshot_id="policy_v1",
        platform_adapter_version="telegram_adapter_v1",
        platform_formatting="default",
        thread_split=None,
        disclosure_class="none",
    )


def _real_outbox_entry():
    """Run the genuine chain to a PASSED preflight and build an outbox entry."""
    payload = _payload()
    ledger = approval.ApprovalLedger()
    ch = approval.create_approval_challenge(
        payload, challenge_id="chal-ee-1", operator_id="operator_jim",
        created_at_epoch=1000, expires_at_epoch=2000)
    entry = approval.record_approval(
        ch, payload, ledger_entry_id="led-ee-1", approved_at_epoch=1500,
        operator_id="operator_jim")
    ledger.append_approval(entry)
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, payload, now_epoch=1600)
    pre = outbox.run_dispatch_preflight(
        payload, entry, vres,
        dispatch_intent_class=outbox.INTENT_SUPERVISED_SINGLE,
        gate_snapshot_class=outbox.GATE_ALLOWS_LOCAL_OUTBOX,
        gate_snapshot_id="gate_v1", operator_id="operator_jim")
    assert pre["status"] == outbox.OutboxStatus.PASS
    return outbox.build_outbox_entry(pre, "outbox_entry_0001",
                                     created_at_epoch=1700)


def _real_review_approved(entry):
    """Build a genuine 0174TI remote_review_approved_not_dispatched result."""
    challenge = review.create_review_challenge(
        entry, challenge_id="review-chal-1", operator_id="operator_jim",
        created_at_epoch=1700, expires_at_epoch=9999)
    inbound = {
        "source_surface_class": review.SOURCE_SURFACE_CLASS,
        "inbound_message_id": "inbound_msg_approve",
        "received_at_epoch": 1_700_000_100,
        "operator_id": "operator_jim",
        "operator_identity_class": review.IDENTITY_VERIFIED,
        "chat_binding_id": "chat_binding_alpha",
        "message_text_redacted": review.DEFAULT_APPROVAL_PHRASE,
        "reply_to_challenge_id": "review-chal-1",
    }
    norm = review.normalize_inbound_envelope(inbound)
    assert norm["status"] == review.InboxStatus.PASS
    intent = review.parse_operator_intent(
        norm["record"], required_approval_phrase=review.DEFAULT_APPROVAL_PHRASE)
    vres = review.validate_review_challenge_response(
        challenge, intent, entry, now_epoch=1800,
        responding_operator_id="operator_jim")
    assert vres["review_outcome_class"] == review.REVIEW_APPROVED_NOT_DISPATCHED
    return vres


def _full_chain():
    """Return (entry, review_result, editorial_record, preview_record)."""
    entry = _real_outbox_entry()
    rr = _real_review_approved(entry)
    er = ep.run_editorial_agent(
        rr, entry, editorial_id="editorial_0001",
        editor_operator_id="operator_jim", decided_at_epoch=1900,
        editorial_summary_redacted="Grounded recap of the CPI print.",
        content_lane="grounded_news_context")
    pr = ep.build_platform_preview(
        er, entry, preview_id="preview_0001", built_at_epoch=2000,
        preview_body_redacted="Neutral context summary for telegram.")
    return entry, rr, er, pr


# --------------------------------------------------------------------------- #
# 0174TJ: editorial agent
# --------------------------------------------------------------------------- #
def test_editorial_approves_valid_review():
    entry = _real_outbox_entry()
    rr = _real_review_approved(entry)
    er = ep.run_editorial_agent(
        rr, entry, editorial_id="editorial_0001",
        editor_operator_id="operator_jim", decided_at_epoch=1900)
    assert er["status"] == ep.Status.PASS
    assert er["editorial_outcome_class"] == ep.EDITORIAL_APPROVED_NOT_DISPATCHED
    assert er["editorial_approved_not_dispatched"] is True
    assert er["payload_hash"] == entry["payload_hash"]
    assert er["idempotency_key"] == entry["idempotency_key"]
    assert er["outbox_entry_id"] == entry["outbox_entry_id"]
    assert er["dispatch_performed"] is False
    assert er["editorial_approval_is_dispatch"] is False
    assert er["record_checksum"]


def test_editorial_blocks_unapproved_review():
    entry = _real_outbox_entry()
    # A review result that is not approved.
    rr = {"review_outcome_class": review.REVIEW_NOT_APPROVED,
          "approved_not_dispatched": False,
          "status": review.InboxStatus.BLOCKED,
          "outbox_entry_id": entry["outbox_entry_id"],
          "payload_hash_short": entry["payload_hash"][:16]}
    er = ep.run_editorial_agent(
        rr, entry, editorial_id="editorial_0001",
        editor_operator_id="operator_jim", decided_at_epoch=1900)
    assert er["status"] == ep.Status.BLOCKED
    assert er["editorial_outcome_class"] == ep.EDITORIAL_NOT_APPROVED
    assert ep.BLOCK_REVIEW_NOT_APPROVED in er["blocked_reasons"]


def test_editorial_fails_closed_on_financial_advice():
    entry = _real_outbox_entry()
    rr = _real_review_approved(entry)
    er = ep.run_editorial_agent(
        rr, entry, editorial_id="editorial_0001",
        editor_operator_id="operator_jim", decided_at_epoch=1900,
        editorial_summary_redacted="You should buy now, guaranteed profit.")
    assert er["status"] == ep.Status.FAIL_CLOSED
    assert er["editorial_outcome_class"] == ep.EDITORIAL_FAIL_CLOSED
    assert er["financial_advice_detected"] is True
    assert ep.BLOCK_EDITORIAL_FINANCIAL_ADVICE in er["blocked_reasons"]


def test_editorial_fails_closed_on_signal_framing():
    entry = _real_outbox_entry()
    rr = _real_review_approved(entry)
    er = ep.run_editorial_agent(
        rr, entry, editorial_id="editorial_0001",
        editor_operator_id="operator_jim", decided_at_epoch=1900,
        editorial_notes_redacted="Strong buy signal with a 50% price target.")
    assert er["status"] == ep.Status.FAIL_CLOSED
    assert er["financial_advice_detected"] is True


def test_editorial_fails_closed_on_forbidden_value():
    entry = _real_outbox_entry()
    rr = _real_review_approved(entry)
    er = ep.run_editorial_agent(
        rr, entry, editorial_id="editorial_0001",
        editor_operator_id="operator_jim", decided_at_epoch=1900,
        editorial_notes_redacted="bot_token=123456789:ABCDEF_ghijklmnop_qrstuvwxyz12345")
    assert er["status"] == ep.Status.FAIL_CLOSED
    assert er["editorial_outcome_class"] == ep.EDITORIAL_FAIL_CLOSED
    assert er["forbidden_fields_detected"] is True


def test_editorial_blocks_disallowed_lane():
    entry = _real_outbox_entry()
    rr = _real_review_approved(entry)
    er = ep.run_editorial_agent(
        rr, entry, editorial_id="editorial_0001",
        editor_operator_id="operator_jim", decided_at_epoch=1900,
        content_lane="trade_signal_lane")
    assert er["status"] == ep.Status.BLOCKED
    assert ep.BLOCK_EDITORIAL_LANE_NOT_ALLOWED in er["blocked_reasons"]


def test_editorial_blocks_synthetic_outbox_entry():
    entry = _real_outbox_entry()
    rr = _real_review_approved(entry)
    synthetic = dict(entry)
    synthetic["model"] = "not_the_real_model"
    er = ep.run_editorial_agent(
        rr, synthetic, editorial_id="editorial_0001",
        editor_operator_id="operator_jim", decided_at_epoch=1900)
    assert er["status"] == ep.Status.BLOCKED
    assert ep.BLOCK_OUTBOX_NOT_AUTHORITY in er["blocked_reasons"]


def test_editorial_blocks_binding_mismatch():
    entry = _real_outbox_entry()
    rr = _real_review_approved(entry)
    # Tamper the review result's bound outbox id.
    rr = dict(rr)
    rr["outbox_entry_id"] = "some_other_entry"
    er = ep.run_editorial_agent(
        rr, entry, editorial_id="editorial_0001",
        editor_operator_id="operator_jim", decided_at_epoch=1900)
    assert er["status"] == ep.Status.BLOCKED
    assert ep.BLOCK_REVIEW_OUTBOX_BINDING_MISMATCH in er["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 0174TK: platform preview
# --------------------------------------------------------------------------- #
def test_preview_builds_from_valid_editorial():
    entry, rr, er, pr = _full_chain()
    assert pr["status"] == ep.Status.PASS
    assert pr["preview_outcome_class"] == ep.PREVIEW_BUILT_NOT_DISPATCHED
    assert pr["preview_built_not_dispatched"] is True
    assert pr["editorial_id"] == er["editorial_id"]
    assert pr["payload_hash"] == entry["payload_hash"]
    assert pr["platform_api_called"] is False
    assert pr["preview_rendered_against_live_platform"] is False
    assert pr["preview_is_platform_posting"] is False
    assert pr["record_checksum"]


def test_preview_blocks_unapproved_editorial():
    entry = _real_outbox_entry()
    rr = _real_review_approved(entry)
    er = ep.run_editorial_agent(
        rr, entry, editorial_id="editorial_0001",
        editor_operator_id="operator_jim", decided_at_epoch=1900,
        content_lane="trade_signal_lane")  # blocked editorial
    pr = ep.build_platform_preview(
        er, entry, preview_id="preview_0001", built_at_epoch=2000)
    assert pr["status"] == ep.Status.BLOCKED
    assert ep.BLOCK_EDITORIAL_NOT_APPROVED in pr["blocked_reasons"]


def test_preview_fails_closed_on_financial_advice():
    entry, rr, er, _ = _full_chain()
    pr = ep.build_platform_preview(
        er, entry, preview_id="preview_0001", built_at_epoch=2000,
        preview_body_redacted="Sell now, this trade signal is risk-free.")
    assert pr["status"] == ep.Status.FAIL_CLOSED
    assert pr["financial_advice_detected"] is True
    assert ep.BLOCK_PREVIEW_FINANCIAL_ADVICE in pr["blocked_reasons"]


def test_preview_fails_closed_on_forbidden_value():
    entry, rr, er, _ = _full_chain()
    pr = ep.build_platform_preview(
        er, entry, preview_id="preview_0001", built_at_epoch=2000,
        preview_body_redacted="visit https://t.me/secretchannel now")
    assert pr["status"] == ep.Status.FAIL_CLOSED
    assert pr["forbidden_fields_detected"] is True


def test_preview_blocks_outbox_mismatch():
    entry, rr, er, _ = _full_chain()
    # A second, different outbox entry id.
    other = dict(entry)
    other["outbox_entry_id"] = "outbox_entry_9999"
    pr = ep.build_platform_preview(
        er, other, preview_id="preview_0001", built_at_epoch=2000)
    assert pr["status"] == ep.Status.BLOCKED
    assert ep.BLOCK_PREVIEW_OUTBOX_MISMATCH in pr["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 0174TL: supervised dry run
# --------------------------------------------------------------------------- #
def test_dry_run_completes_full_chain():
    entry, rr, er, pr = _full_chain()
    dr = ep.run_supervised_dry_run(
        rr, entry, er, pr, dry_run_id="dry_run_0001",
        operator_id="operator_jim", run_at_epoch=2100)
    assert dr["status"] == ep.Status.PASS
    assert dr["dry_run_outcome_class"] == ep.DRY_RUN_COMPLETE_NOT_DISPATCHED
    assert dr["dry_run_complete_not_dispatched"] is True
    assert dr["editorial_id"] == er["editorial_id"]
    assert dr["preview_id"] == pr["preview_id"]
    assert dr["outbox_entry_id"] == entry["outbox_entry_id"]
    assert dr["dispatch_performed"] is False
    assert dr["dry_run_is_dispatch"] is False
    assert dr["ready_for_future_supervised_gate_only"] is True
    assert dr["record_checksum"]


def test_dry_run_blocks_on_payload_hash_substitution():
    entry, rr, er, pr = _full_chain()
    tampered_preview = dict(pr)
    tampered_preview["payload_hash"] = "d" * 64
    dr = ep.run_supervised_dry_run(
        rr, entry, er, tampered_preview, dry_run_id="dry_run_0001",
        operator_id="operator_jim", run_at_epoch=2100)
    assert dr["status"] == ep.Status.BLOCKED
    assert ep.BLOCK_DRY_RUN_PAYLOAD_HASH_MISMATCH in dr["blocked_reasons"]


def test_dry_run_blocks_on_editorial_id_mismatch():
    entry, rr, er, pr = _full_chain()
    tampered_preview = dict(pr)
    tampered_preview["editorial_id"] = "editorial_9999"
    dr = ep.run_supervised_dry_run(
        rr, entry, er, tampered_preview, dry_run_id="dry_run_0001",
        operator_id="operator_jim", run_at_epoch=2100)
    assert dr["status"] == ep.Status.BLOCKED
    assert ep.BLOCK_DRY_RUN_EDITORIAL_ID_MISMATCH in dr["blocked_reasons"]


def test_dry_run_blocks_on_unbuilt_preview():
    entry, rr, er, _ = _full_chain()
    bad_preview = ep.build_platform_preview(
        er, entry, preview_id="preview_0001", built_at_epoch=2000,
        preview_body_redacted="Buy now for guaranteed profit.")  # fail_closed
    dr = ep.run_supervised_dry_run(
        rr, entry, er, bad_preview, dry_run_id="dry_run_0001",
        operator_id="operator_jim", run_at_epoch=2100)
    assert dr["status"] == ep.Status.BLOCKED
    assert ep.BLOCK_DRY_RUN_PREVIEW_NOT_BUILT in dr["blocked_reasons"]


def test_dry_run_fails_closed_on_forbidden_value():
    entry, rr, er, pr = _full_chain()
    tampered = dict(pr)
    tampered["leak"] = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
    dr = ep.run_supervised_dry_run(
        rr, entry, er, tampered, dry_run_id="dry_run_0001",
        operator_id="operator_jim", run_at_epoch=2100)
    assert dr["status"] == ep.Status.FAIL_CLOSED
    assert dr["forbidden_fields_detected"] is True


# --------------------------------------------------------------------------- #
# Determinism, packet, doc, safety
# --------------------------------------------------------------------------- #
def test_chain_is_deterministic():
    a = _full_chain()
    b = _full_chain()
    for ra, rb in zip(a, b):
        assert ra.get("record_checksum") == rb.get("record_checksum") or (
            ra.get("checksum_sha256") == rb.get("checksum_sha256"))


def test_build_packet_is_clean_and_deterministic():
    p1 = ep.build_packet()
    p2 = ep.build_packet()
    assert p1["checksum_sha256"] == p2["checksum_sha256"]
    assert ep.scan_for_leaks(p1) == []
    assert p1["task_label"] == ep.TASK_LABEL
    assert p1["status"] == ep.Status.PASS


def test_build_doc_is_clean():
    doc = ep.build_doc()
    assert ep.scan_for_leaks(doc) == []
    assert "0174TJ/TK/TL" in doc
    assert ep.EXACT_NEXT_TASK_RECOMMENDATION in doc


def test_write_artifacts_writes_two_files(tmp_path):
    paths = ep.write_artifacts(str(tmp_path))
    assert len(paths) == 2
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            content = fh.read()
        assert content
        assert ep.scan_for_leaks(content) == []


def test_no_financial_advice_scanner_flags_known_phrases():
    assert ep.scan_for_financial_advice({"t": "buy now"})
    assert ep.scan_for_financial_advice({"t": "strong sell signal"})
    assert ep.scan_for_financial_advice({"t": "guaranteed profit"})
    assert ep.scan_for_financial_advice({"t": "set a stop-loss"})
    # Clean grounded context passes.
    assert ep.scan_for_financial_advice(
        {"t": "The CPI print came in at 3.1% year over year."}) == []


def test_safety_flags_present_on_all_records():
    entry, rr, er, pr = _full_chain()
    dr = ep.run_supervised_dry_run(
        rr, entry, er, pr, dry_run_id="dry_run_0001",
        operator_id="operator_jim", run_at_epoch=2100)
    for rec in (er, pr, dr):
        assert rec["credential_hydrated"] is False
        assert rec["network_performed"] is False
        assert rec["llm_behavior"] is False
        assert rec["dispatch_performed"] is False
        assert rec["no_financial_advice_emitted"] is True
