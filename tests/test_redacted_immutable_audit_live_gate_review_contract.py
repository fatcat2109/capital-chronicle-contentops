"""Tests for the 0174TP/TQ/TR audit ledger + live-gate review + decision packet.

Deterministic, stdlib-only, offline. These tests assert the final LOCAL
evidence + review layer on top of the accepted chain:

  * 0174TP redacted immutable audit ledger -- append-only, redacted,
    checksum-chained; suppresses duplicate ids/candidate-checksums/fingerprints.
  * 0174TQ operator live-gate readiness review -- fail-closed by default; the
    only non-blocked outcome is evidence-ready-not-live.
  * 0174TR live-gate decision packet -- created-not-executable only for an
    evidence-ready review; never live, never execution.

All upstream objects are built through the GENUINE authority chain
(0174ED -> 0174EE -> 0174TG/TH/TI -> 0174TJ/TK/TL -> 0174TM/TN/TO), never via
hand-rolled dicts, so the bindings are real.
"""

import copy

from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import dispatch_outbox_idempotency_contract as outbox
from live_contentops import remote_operator_inbox_intent_review_contract as review
from live_contentops import editorial_preview_supervised_dry_run_contract as ep
from live_contentops import supervised_dispatch_safety_gate_contract as sg
from live_contentops import redacted_immutable_audit_live_gate_review_contract as al


# --------------------------------------------------------------------------- #
# Fixtures / helpers -- the genuine 0174ED -> ... -> 0174TO chain
# --------------------------------------------------------------------------- #
def _payload(variant=""):
    return approval.canonical_payload_dict(
        platform="telegram",
        payload_text="One CPI print is not a regime shift." + variant,
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


def _real_outbox_entry(variant=""):
    payload = _payload(variant)
    ledger = approval.ApprovalLedger()
    ch = approval.create_approval_challenge(
        payload, challenge_id="chal-ee-1" + variant, operator_id="operator_jim",
        created_at_epoch=1000, expires_at_epoch=2000)
    entry = approval.record_approval(
        ch, payload, ledger_entry_id="led-ee-1" + variant,
        approved_at_epoch=1500, operator_id="operator_jim")
    ledger.append_approval(entry)
    vres = approval.validate_approval_for_current_payload(
        ledger, entry, payload, now_epoch=1600)
    pre = outbox.run_dispatch_preflight(
        payload, entry, vres,
        dispatch_intent_class=outbox.INTENT_SUPERVISED_SINGLE,
        gate_snapshot_class=outbox.GATE_ALLOWS_LOCAL_OUTBOX,
        gate_snapshot_id="gate_v1", operator_id="operator_jim")
    assert pre["status"] == outbox.OutboxStatus.PASS
    return outbox.build_outbox_entry(pre, "outbox_entry_0001" + variant,
                                     created_at_epoch=1700)


def _real_review_approved(entry, variant=""):
    challenge = review.create_review_challenge(
        entry, challenge_id="review-chal-1" + variant,
        operator_id="operator_jim", created_at_epoch=1700,
        expires_at_epoch=9999)
    inbound = {
        "source_surface_class": review.SOURCE_SURFACE_CLASS,
        "inbound_message_id": "inbound_msg_approve" + variant,
        "received_at_epoch": 1_700_000_100,
        "operator_id": "operator_jim",
        "operator_identity_class": review.IDENTITY_VERIFIED,
        "chat_binding_id": "chat_binding_alpha",
        "message_text_redacted": review.DEFAULT_APPROVAL_PHRASE,
        "reply_to_challenge_id": "review-chal-1" + variant,
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


def _surface_bodies():
    return {
        ep.SURFACE_TELEGRAM_CHANNEL: "Neutral context summary for telegram.",
        ep.SURFACE_X_POST: "Grounded recap of the CPI print for X.",
        ep.SURFACE_LINKEDIN_POST: "Measured macro context note for LinkedIn.",
        ep.SURFACE_MANUAL_PUBLISH_PACKET: "Manual publish packet neutral summary.",
    }


def _full_dry_run(variant=""):
    entry = _real_outbox_entry(variant)
    rr = _real_review_approved(entry, variant)
    er = ep.run_editorial_agent(
        rr, entry, editorial_id="editorial_0001" + variant,
        editor_operator_id="operator_jim", decided_at_epoch=1900,
        editorial_summary_redacted="Grounded recap of the CPI print.",
        content_lane="grounded_news_context")
    ps = ep.build_platform_preview_set(
        er, entry, preview_set_id="preview_set_0001" + variant,
        built_at_epoch=2000, surface_bodies_redacted=_surface_bodies())
    dr = ep.run_supervised_dry_run(
        rr, entry, er, ps, dry_run_id="dry_run_0001" + variant,
        operator_id="operator_jim", run_at_epoch=2100)
    assert dr["status"] == ep.Status.PASS
    return entry, rr, er, ps, dr


def _clear_kill_switch(dr):
    return sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_v1",
        kill_switch_state=sg.KILL_SWITCH_CLEAR,
        current_policy_snapshot_id="ks_policy_v1")


def _clear_rate_policy():
    snap = sg.build_rate_spend_retry_policy_snapshot(
        policy_snapshot_id="rate_policy_v1")
    return sg.evaluate_rate_spend_retry_policy(snap, operator_id="operator_jim")


def _bundle(dr, ks, rp, entry, *, request_id="supervised_request_0001",
            variant=""):
    return sg.build_one_request_dispatch_gate_input_bundle(
        dr, ks, rp,
        operator_id="operator_jim",
        supervised_request_id=request_id,
        outbox_entry_id=entry["outbox_entry_id"],
        payload_hash_short=entry["payload_hash_short"],
        payload_hash=entry["payload_hash"],
        idempotency_key_short=entry["idempotency_key_short"],
        idempotency_key=entry["idempotency_key"],
        approval_ledger_entry_id=entry["approval_ledger_entry_id"],
        review_challenge_id="review-chal-1" + variant,
        editorial_id="editorial_0001" + variant,
        preview_set_id="preview_set_0001" + variant)


def _gate_chain(request_id="supervised_request_0001", variant=""):
    """Return (gate_result, candidate, audit, ks, rp).

    ``variant`` produces a genuinely distinct authority binding (different
    payload + ids), hence a different idempotency fingerprint. ``request_id``
    alone changes only the request label, NOT the binding fingerprint, so two
    chains with the same ``variant`` but different ``request_id`` deliberately
    share a fingerprint.
    """
    entry, rr, er, ps, dr = _full_dry_run(variant)
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate_result = sg.run_one_request_dispatch_gate(
        _bundle(dr, ks, rp, entry, request_id=request_id, variant=variant))
    assert gate_result["dispatch_gate_outcome_class"] == sg.GATE_CANDIDATE_CREATED
    candidate = gate_result["dispatch_authorization_candidate"]
    audit = sg.build_redacted_immutable_dispatch_audit(gate_result, ks, rp)
    return gate_result, candidate, audit, ks, rp


def _appended_ledger(request_id="supervised_request_0001",
                     ledger_entry_id="audit_ledger_0001",
                     policy_snapshot_id="ks_policy_v1", variant=""):
    gr, cand, audit, ks, rp = _gate_chain(request_id, variant)
    ledger = al.RedactedAuditLedger()
    res = ledger.append(
        gr, cand, audit, operator_id="operator_jim",
        ledger_entry_id=ledger_entry_id, created_at_epoch=2200,
        policy_snapshot_id=policy_snapshot_id)
    return ledger, res, gr, cand, audit


# --------------------------------------------------------------------------- #
# 1. Valid full chain end-to-end
# --------------------------------------------------------------------------- #
def test_full_chain_ledger_review_decision_packet():
    ledger, res, gr, cand, audit = _appended_ledger()
    assert res["status"] == al.Status.PASS
    assert res["ledger_append_outcome_class"] == al.LEDGER_APPENDED
    assert res["appended"] is True

    report = ledger.build_integrity_report()
    assert report["chain_intact"] is True

    rev = al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report, gr, cand,
        operator_id="operator_jim", current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    assert rev["readiness_outcome_class"] == al.REVIEW_EVIDENCE_READY
    assert rev["evidence_ready_not_live"] is True
    assert rev["valid_for_live_execution"] is False
    assert rev["live_ready"] is False

    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["decision_outcome_class"] == al.DECISION_CREATED
    assert dp["decision_packet_created_not_executable"] is True
    assert dp["valid_for_live_execution"] is False
    assert dp["requires_future_operator_live_gate"] is True


# --------------------------------------------------------------------------- #
# 2-11. Ledger append behaviors
# --------------------------------------------------------------------------- #
def test_ledger_entry_stores_symbolic_ids_and_short_hashes_only():
    ledger, res, gr, cand, audit = _appended_ledger()
    entry = res["ledger_entry"]
    assert al.scan_for_leaks(entry) == []
    # payload_hash_short is a 16-char short hash, not a full hash.
    assert len(entry["payload_hash_short"]) == 16
    assert entry["no_raw_credential_stored"] is True


def test_ledger_entry_includes_previous_checksum_and_chain_digest():
    ledger, res, gr, cand, audit = _appended_ledger()
    entry = res["ledger_entry"]
    assert entry["previous_entry_checksum"] == al.GENESIS_PREVIOUS_CHECKSUM
    assert entry["entry_checksum"]
    assert entry["chain_digest"]


def test_second_ledger_append_chains_to_first():
    ledger, res, gr, cand, audit = _appended_ledger()
    first = res["ledger_entry"]
    # A genuinely different second candidate chain (different request id).
    gr2, cand2, audit2, ks2, rp2 = _gate_chain(
        request_id="supervised_request_0002", variant="_v2")
    res2 = ledger.append(
        gr2, cand2, audit2, operator_id="operator_jim",
        ledger_entry_id="audit_ledger_0002", created_at_epoch=2300,
        policy_snapshot_id="ks_policy_v1")
    assert res2["appended"] is True
    second = res2["ledger_entry"]
    assert second["previous_entry_checksum"] == first["entry_checksum"]
    assert second["sequence_index"] == 1
    assert ledger.build_integrity_report()["chain_intact"] is True


def test_duplicate_ledger_entry_id_suppressed():
    ledger, res, gr, cand, audit = _appended_ledger()
    dup = ledger.append(
        gr, cand, audit, operator_id="operator_jim",
        ledger_entry_id="audit_ledger_0001", created_at_epoch=2400,
        policy_snapshot_id="ks_policy_v1")
    assert dup["appended"] is False
    assert dup["duplicate_suppressed"] is True
    assert dup["ledger_append_outcome_class"] == al.LEDGER_DUPLICATE_ENTRY_ID
    assert ledger.entry_count() == 1


def test_duplicate_candidate_checksum_suppressed():
    ledger, res, gr, cand, audit = _appended_ledger()
    # Same candidate, different ledger id -> candidate-checksum suppression.
    dup = ledger.append(
        gr, cand, audit, operator_id="operator_jim",
        ledger_entry_id="audit_ledger_DIFFERENT", created_at_epoch=2400,
        policy_snapshot_id="ks_policy_v1")
    assert dup["appended"] is False
    assert dup["ledger_append_outcome_class"] == (
        al.LEDGER_DUPLICATE_CANDIDATE_CHECKSUM)
    assert ledger.entry_count() == 1


def test_duplicate_idempotency_fingerprint_suppressed():
    # Two distinct candidates (different request ids) but SAME authority
    # binding share an idempotency fingerprint. Force distinct candidate
    # checksums so the fingerprint guard (not the candidate guard) trips.
    gr_a, cand_a, audit_a, ks_a, rp_a = _gate_chain(
        request_id="supervised_request_A")
    gr_b, cand_b, audit_b, ks_b, rp_b = _gate_chain(
        request_id="supervised_request_B")
    assert gr_a["idempotency_fingerprint"] == gr_b["idempotency_fingerprint"]
    assert cand_a["candidate_checksum"] != cand_b["candidate_checksum"]
    ledger = al.RedactedAuditLedger()
    first = ledger.append(
        gr_a, cand_a, audit_a, operator_id="operator_jim",
        ledger_entry_id="audit_ledger_A", created_at_epoch=2200,
        policy_snapshot_id="ks_policy_v1")
    assert first["appended"] is True
    second = ledger.append(
        gr_b, cand_b, audit_b, operator_id="operator_jim",
        ledger_entry_id="audit_ledger_B", created_at_epoch=2300,
        policy_snapshot_id="ks_policy_v1")
    assert second["appended"] is False
    assert second["ledger_append_outcome_class"] == (
        al.LEDGER_DUPLICATE_FINGERPRINT)
    assert ledger.entry_count() == 1


def test_broken_previous_checksum_blocks_integrity_report():
    ledger, res, gr, cand, audit = _appended_ledger()
    gr2, cand2, audit2, ks2, rp2 = _gate_chain(
        request_id="supervised_request_0002", variant="_v2")
    ledger.append(
        gr2, cand2, audit2, operator_id="operator_jim",
        ledger_entry_id="audit_ledger_0002", created_at_epoch=2300,
        policy_snapshot_id="ks_policy_v1")
    entries = ledger.entries
    entries[1]["previous_entry_checksum"] = "deadbeef"
    report = al.build_audit_ledger_integrity_report(entries)
    assert report["chain_intact"] is False
    assert any(r.startswith(al.BLOCK_INTEGRITY_BROKEN_PREVIOUS_LINK)
               for r in report["blocked_reasons"])


def test_tampered_entry_checksum_detected():
    ledger, res, gr, cand, audit = _appended_ledger()
    entries = ledger.entries
    entries[0]["operator_id"] = "operator_eve"  # mutate without re-checksum
    report = al.build_audit_ledger_integrity_report(entries)
    assert report["chain_intact"] is False
    assert any(r.startswith(al.BLOCK_INTEGRITY_ENTRY_CHECKSUM_MISMATCH)
               for r in report["blocked_reasons"])


def test_forbidden_value_fail_closes_ledger_append():
    gr, cand, audit, ks, rp = _gate_chain()
    tampered = copy.deepcopy(gr)
    tampered["leak"] = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
    ledger = al.RedactedAuditLedger()
    res = ledger.append(
        tampered, cand, audit, operator_id="operator_jim",
        ledger_entry_id="audit_ledger_0001", created_at_epoch=2200,
        policy_snapshot_id="ks_policy_v1")
    assert res["status"] == al.Status.FAIL_CLOSED
    assert res["forbidden_fields_detected"] is True
    assert al.BLOCK_LEDGER_FORBIDDEN_VALUE in res["blocked_reasons"]
    assert ledger.entry_count() == 0


def test_candidate_live_executable_blocks_ledger_append():
    gr, cand, audit, ks, rp = _gate_chain()
    tampered = copy.deepcopy(cand)
    tampered["valid_for_live_execution"] = True
    ledger = al.RedactedAuditLedger()
    res = ledger.append(
        gr, tampered, audit, operator_id="operator_jim",
        ledger_entry_id="audit_ledger_0001", created_at_epoch=2200,
        policy_snapshot_id="ks_policy_v1")
    assert res["status"] == al.Status.BLOCKED
    assert al.BLOCK_LEDGER_CANDIDATE_LIVE_EXECUTABLE in res["blocked_reasons"]
    assert ledger.entry_count() == 0


def test_upstream_unsafe_behavior_blocks_ledger_append():
    gr, cand, audit, ks, rp = _gate_chain()
    tampered = copy.deepcopy(cand)
    tampered["network_performed"] = True
    ledger = al.RedactedAuditLedger()
    res = ledger.append(
        gr, tampered, audit, operator_id="operator_jim",
        ledger_entry_id="audit_ledger_0001", created_at_epoch=2200,
        policy_snapshot_id="ks_policy_v1")
    assert res["status"] == al.Status.BLOCKED
    assert any(r.startswith(al.BLOCK_LEDGER_UPSTREAM_UNSAFE_BEHAVIOR)
               for r in res["blocked_reasons"])


# --------------------------------------------------------------------------- #
# 12-20. Readiness review behaviors
# --------------------------------------------------------------------------- #
def test_review_blocked_if_ledger_empty():
    gr, cand, audit, ks, rp = _gate_chain()
    empty_ledger = al.RedactedAuditLedger()
    report = empty_ledger.build_integrity_report()
    rev = al.run_operator_live_gate_readiness_review(
        None, report, gr, cand, operator_id="operator_jim",
        current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    assert rev["readiness_outcome_class"] == al.REVIEW_BLOCKED
    assert al.BLOCK_REVIEW_LEDGER_ENTRY_MISSING in rev["blocked_reasons"]


def test_review_blocked_if_integrity_fails():
    ledger, res, gr, cand, audit = _appended_ledger()
    entries = ledger.entries
    entries[0]["operator_id"] = "operator_eve"
    broken_report = al.build_audit_ledger_integrity_report(entries)
    rev = al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), broken_report, gr, cand,
        operator_id="operator_jim", current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    assert rev["readiness_outcome_class"] == al.REVIEW_BLOCKED
    assert al.BLOCK_REVIEW_INTEGRITY_FAILED in rev["blocked_reasons"]


def test_review_blocked_if_candidate_checksum_mismatch():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    wrong_cand = copy.deepcopy(cand)
    wrong_cand["candidate_checksum"] = "deadbeefdeadbeef"
    rev = al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report, gr, wrong_cand,
        operator_id="operator_jim", current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    assert rev["readiness_outcome_class"] == al.REVIEW_BLOCKED
    assert al.BLOCK_REVIEW_CANDIDATE_CHECKSUM_MISMATCH in rev["blocked_reasons"]


def test_review_blocked_if_audit_fingerprint_mismatch():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    wrong_gr = copy.deepcopy(gr)
    wrong_gr["idempotency_fingerprint"] = "deadbeef_fingerprint"
    rev = al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report, wrong_gr, cand,
        operator_id="operator_jim", current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    assert rev["readiness_outcome_class"] == al.REVIEW_BLOCKED
    assert al.BLOCK_REVIEW_AUDIT_CHECKSUM_MISMATCH in rev["blocked_reasons"]


def test_review_blocked_if_stale_policy_snapshot():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    rev = al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report, gr, cand,
        operator_id="operator_jim",
        current_policy_snapshot_id="ks_policy_NEWER",
        operator_review_id="operator_review_0001")
    assert rev["readiness_outcome_class"] == al.REVIEW_BLOCKED
    assert al.BLOCK_REVIEW_STALE_POLICY_SNAPSHOT in rev["blocked_reasons"]


def test_review_blocked_if_unsafe_flag_present():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    unsafe_cand = copy.deepcopy(cand)
    unsafe_cand["telegram_api_called"] = True
    rev = al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report, gr, unsafe_cand,
        operator_id="operator_jim", current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    assert rev["readiness_outcome_class"] == al.REVIEW_BLOCKED
    assert any(r.startswith(al.BLOCK_REVIEW_CANDIDATE_UNSAFE)
               for r in rev["blocked_reasons"])


def test_review_evidence_ready_still_not_live():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    rev = al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report, gr, cand,
        operator_id="operator_jim", current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    assert rev["readiness_outcome_class"] == al.REVIEW_EVIDENCE_READY
    assert rev["live_ready"] is False
    assert rev["valid_for_live_execution"] is False
    assert rev["dispatch_ready"] is False


def test_review_checklist_symbolic_and_not_approval():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    rev = al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report, gr, cand,
        operator_id="operator_jim", current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    checklist = rev["manual_checklist"]
    assert checklist["checklist_is_approval"] is False
    assert checklist["checklist_is_live_readiness"] is False
    item_ids = [i["item_id"] for i in checklist["items"]]
    assert "live_dispatch_remains_disabled" in item_ids
    for item in checklist["items"]:
        assert item["checked"] is False


def test_review_separates_local_evidence_from_future_live_gate():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    rev = al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report, gr, cand,
        operator_id="operator_jim", current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    em = rev["evidence_map"]
    assert em["local_deterministic_evidence_complete"] is True
    assert em["live_execution_authorized"] is False
    assert em["credential_hydration_authorized"] is False
    assert em["provider_or_api_call_authorized"] is False
    assert em["telegram_or_platform_dispatch_authorized"] is False
    assert em["future_live_or_api_operator_gate_required"] is True


# --------------------------------------------------------------------------- #
# 21-30. Decision packet + registry behaviors
# --------------------------------------------------------------------------- #
def _evidence_ready_review(ledger, gr, cand):
    report = ledger.build_integrity_report()
    return al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report, gr, cand,
        operator_id="operator_jim", current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")


def test_decision_packet_blocked_if_review_blocked():
    ledger, res, gr, cand, audit = _appended_ledger()
    blocked_review = al.run_operator_live_gate_readiness_review(
        None, ledger.build_integrity_report(), gr, cand,
        operator_id="operator_jim", current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    assert blocked_review["readiness_outcome_class"] == al.REVIEW_BLOCKED
    dp = al.build_live_gate_decision_packet(
        blocked_review, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["decision_outcome_class"] == al.DECISION_BLOCKED
    assert al.BLOCK_DECISION_REVIEW_NOT_EVIDENCE_READY in dp["blocked_reasons"]


def test_decision_packet_blocked_if_review_claims_live():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    tampered = copy.deepcopy(rev)
    tampered["valid_for_live_execution"] = True
    dp = al.build_live_gate_decision_packet(
        tampered, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["decision_outcome_class"] == al.DECISION_BLOCKED
    assert al.BLOCK_DECISION_REVIEW_CLAIMS_LIVE in dp["blocked_reasons"]


def test_decision_packet_blocked_if_ledger_checksum_mismatch():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    wrong_entry = copy.deepcopy(ledger.latest_entry())
    wrong_entry["entry_checksum"] = "deadbeefdeadbeef"
    dp = al.build_live_gate_decision_packet(
        rev, wrong_entry, cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["decision_outcome_class"] == al.DECISION_BLOCKED
    assert al.BLOCK_DECISION_LEDGER_CHECKSUM_MISMATCH in dp["blocked_reasons"]


def test_decision_packet_blocked_if_candidate_checksum_mismatch():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    wrong_cand = copy.deepcopy(cand)
    wrong_cand["candidate_checksum"] = "deadbeefdeadbeef"
    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), wrong_cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["decision_outcome_class"] == al.DECISION_BLOCKED
    assert al.BLOCK_DECISION_CANDIDATE_CHECKSUM_MISMATCH in dp["blocked_reasons"]


def test_decision_packet_created_not_executable():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["decision_outcome_class"] == al.DECISION_CREATED
    assert dp["decision_packet_created_not_executable"] is True


def test_decision_packet_sets_all_unsafe_flags_false():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    for flag in ("dispatch_performed", "live_request_performed",
                 "platform_api_called", "telegram_api_called",
                 "credential_hydrated", "llm_behavior", "network_performed",
                 "scheduler_enabled", "auto_retry_allowed"):
        assert dp[flag] is False, flag


def test_decision_packet_valid_for_live_execution_false():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["valid_for_live_execution"] is False


def test_decision_packet_requires_future_operator_live_gate_true():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["requires_future_operator_live_gate"] is True


def test_decision_registry_suppresses_duplicate_packet_id():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    registry = al.LiveGateDecisionPacketRegistry()
    first = registry.submit(dp)
    assert first["appended"] is True
    second = registry.submit(dp)
    assert second["appended"] is False
    assert second["registry_outcome_class"] == al.DECISION_DUPLICATE_PACKET_ID
    assert registry.packet_count() == 1


def test_decision_registry_suppresses_duplicate_candidate_checksum():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    dp_a = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_A")
    # Different packet id, same candidate checksum -> checksum suppression.
    dp_b = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_B")
    registry = al.LiveGateDecisionPacketRegistry()
    assert registry.submit(dp_a)["appended"] is True
    second = registry.submit(dp_b)
    assert second["appended"] is False
    assert second["registry_outcome_class"] == (
        al.DECISION_DUPLICATE_CANDIDATE_CHECKSUM)
    assert registry.packet_count() == 1


# --------------------------------------------------------------------------- #
# 31-34. Packet/doc + module hygiene
# --------------------------------------------------------------------------- #
def test_packet_and_doc_deterministic_and_leak_free():
    p1 = al.build_packet()
    p2 = al.build_packet()
    assert p1["checksum_sha256"] == p2["checksum_sha256"]
    assert al.scan_for_leaks(p1) == []
    d1 = al.build_doc()
    d2 = al.build_doc()
    assert d1 == d2
    assert al.scan_for_leaks(d1) == []
    assert "0174TP/TQ/TR" in d1
    assert al.EXACT_NEXT_TASK_RECOMMENDATION in d1


def test_no_forbidden_imports_or_env_access():
    from pathlib import Path
    src = Path(al.__file__).read_text(encoding="utf-8")
    for banned in ("import requests", "import httpx", "import aiohttp",
                   "import urllib", "import socket", "import ssl",
                   "import webbrowser", "import subprocess", "import dotenv",
                   "import keyring", "import sqlite3", "import openai",
                   "import anthropic", "import telegram", "import tweepy",
                   "import selenium", "import playwright",
                   "os.environ", "os.getenv"):
        assert banned not in src, banned


def _code_only(path):
    """Return module source with string literals + comments removed.

    Network/credential operation strings are forbidden in EXECUTABLE code, but
    the module legitimately documents what it does NOT do in its docstrings and
    comments. Scanning raw source would false-positive on that safety prose, so
    we tokenize and drop STRING and COMMENT tokens first.
    """
    import io
    import tokenize
    from pathlib import Path
    src = Path(path).read_text(encoding="utf-8")
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.STRING, tokenize.COMMENT):
                continue
            out.append(tok.string)
    except tokenize.TokenError:
        return src
    return " ".join(out)


def test_no_network_or_credential_access_strings():
    code = _code_only(al.__file__)
    for banned in (".env", "getUpdates", "sendMessage", "bot_token",
                   "oauth", "access_token", "refresh_token"):
        assert banned not in code, banned


def test_module_import_has_no_side_effects(tmp_path):
    import importlib
    before = set(tmp_path.iterdir())
    importlib.reload(al)
    after = set(tmp_path.iterdir())
    assert before == after


def test_write_artifacts_writes_two_files(tmp_path):
    paths = al.write_artifacts(str(tmp_path))
    assert len(paths) == 2
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            content = fh.read()
        assert content
        assert al.scan_for_leaks(content) == []


def test_safety_flags_present_on_all_objects():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    rev = _evidence_ready_review(ledger, gr, cand)
    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    for rec in (res, report, rev, dp):
        assert rec["credential_hydrated"] is False
        assert rec["network_performed"] is False
        assert rec["llm_behavior"] is False
        assert rec["dispatch_performed"] is False
        assert rec["scheduler_enabled"] is False
        assert rec["auto_retry_allowed"] is False


# --------------------------------------------------------------------------- #
# R1. Input-safety revalidation on readiness review + decision packet
# --------------------------------------------------------------------------- #
def _review_with(ledger, gr, cand, report=None):
    return al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report or ledger.build_integrity_report(),
        gr, cand, operator_id="operator_jim",
        current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")


def test_r1_valid_full_chain_still_passes():
    ledger, res, gr, cand, audit = _appended_ledger()
    assert res["ledger_append_outcome_class"] == al.LEDGER_APPENDED
    rev = _review_with(ledger, gr, cand)
    assert rev["readiness_outcome_class"] == al.REVIEW_EVIDENCE_READY
    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["decision_outcome_class"] == al.DECISION_CREATED


def test_r1_review_blocks_integrity_report_network_while_chain_intact():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    assert report["chain_intact"] is True
    report["network_performed"] = True
    rev = _review_with(ledger, gr, cand, report=report)
    assert rev["readiness_outcome_class"] == al.REVIEW_BLOCKED
    assert al.BLOCK_REVIEW_INTEGRITY_REPORT_UNSAFE in rev["blocked_reasons"]
    assert (al.BLOCK_REVIEW_INTEGRITY_REPORT_UNSAFE + ":network_performed"
            in rev["blocked_reasons"])


def test_r1_review_blocks_integrity_report_platform_api_called():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    report["platform_api_called"] = True
    rev = _review_with(ledger, gr, cand, report=report)
    assert rev["readiness_outcome_class"] == al.REVIEW_BLOCKED
    assert al.BLOCK_REVIEW_INTEGRITY_REPORT_UNSAFE in rev["blocked_reasons"]


def test_r1_review_blocks_integrity_report_live_ready():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    report["live_ready"] = True
    rev = _review_with(ledger, gr, cand, report=report)
    assert rev["readiness_outcome_class"] == al.REVIEW_BLOCKED
    assert al.BLOCK_REVIEW_INTEGRITY_REPORT_UNSAFE in rev["blocked_reasons"]


def test_r1_review_blocks_ledger_entry_network_performed():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    tampered_entry = copy.deepcopy(ledger.latest_entry())
    tampered_entry["network_performed"] = True
    rev = al.run_operator_live_gate_readiness_review(
        tampered_entry, report, gr, cand, operator_id="operator_jim",
        current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    assert rev["readiness_outcome_class"] == al.REVIEW_BLOCKED
    assert al.BLOCK_REVIEW_LEDGER_ENTRY_UNSAFE in rev["blocked_reasons"]


def test_r1_review_blocks_gate_result_telegram_api_called():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    tampered_gr = copy.deepcopy(gr)
    tampered_gr["telegram_api_called"] = True
    rev = al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report, tampered_gr, cand,
        operator_id="operator_jim", current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    assert rev["readiness_outcome_class"] == al.REVIEW_BLOCKED
    assert al.BLOCK_REVIEW_GATE_RESULT_UNSAFE in rev["blocked_reasons"]


def test_r1_review_blocks_candidate_credential_hydrated():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    tampered_cand = copy.deepcopy(cand)
    tampered_cand["credential_hydrated"] = True
    rev = al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report, gr, tampered_cand,
        operator_id="operator_jim", current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001")
    assert rev["readiness_outcome_class"] == al.REVIEW_BLOCKED
    assert al.BLOCK_REVIEW_CANDIDATE_UNSAFE in rev["blocked_reasons"]


def test_r1_review_blocked_reasons_identify_artifact_and_flag():
    ledger, res, gr, cand, audit = _appended_ledger()
    report = ledger.build_integrity_report()
    report["network_performed"] = True
    rev = _review_with(ledger, gr, cand, report=report)
    assert (al.BLOCK_REVIEW_INTEGRITY_REPORT_UNSAFE + ":network_performed"
            in rev["blocked_reasons"])


def test_r1_decision_blocks_review_network_performed():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    tampered = copy.deepcopy(rev)
    tampered["network_performed"] = True
    dp = al.build_live_gate_decision_packet(
        tampered, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["decision_outcome_class"] == al.DECISION_BLOCKED
    assert al.BLOCK_DECISION_REVIEW_UNSAFE in dp["blocked_reasons"]


def test_r1_decision_blocks_review_is_live_readiness():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    tampered = copy.deepcopy(rev)
    tampered["review_is_live_readiness"] = True
    dp = al.build_live_gate_decision_packet(
        tampered, ledger.latest_entry(), cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["decision_outcome_class"] == al.DECISION_BLOCKED
    assert al.BLOCK_DECISION_REVIEW_UNSAFE in dp["blocked_reasons"]


def test_r1_decision_blocks_ledger_entry_platform_api_called():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    tampered_entry = copy.deepcopy(ledger.latest_entry())
    tampered_entry["platform_api_called"] = True
    dp = al.build_live_gate_decision_packet(
        rev, tampered_entry, cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["decision_outcome_class"] == al.DECISION_BLOCKED
    assert al.BLOCK_DECISION_LEDGER_ENTRY_UNSAFE in dp["blocked_reasons"]


def test_r1_decision_blocks_candidate_network_with_unchanged_checksum():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    tampered_cand = copy.deepcopy(cand)
    # Flip an unsafe flag but KEEP the original candidate_checksum field.
    tampered_cand["network_performed"] = True
    assert tampered_cand["candidate_checksum"] == cand["candidate_checksum"]
    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), tampered_cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["decision_outcome_class"] == al.DECISION_BLOCKED
    assert al.BLOCK_DECISION_CANDIDATE_UNSAFE in dp["blocked_reasons"]


def test_r1_decision_blocks_candidate_valid_for_live_with_unchanged_checksum():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    tampered_cand = copy.deepcopy(cand)
    tampered_cand["valid_for_live_execution"] = True
    assert tampered_cand["candidate_checksum"] == cand["candidate_checksum"]
    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), tampered_cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert dp["decision_outcome_class"] == al.DECISION_BLOCKED
    assert al.BLOCK_DECISION_CANDIDATE_UNSAFE in dp["blocked_reasons"]


def test_r1_decision_blocked_reasons_identify_artifact_and_flag():
    ledger, res, gr, cand, audit = _appended_ledger()
    rev = _evidence_ready_review(ledger, gr, cand)
    tampered_cand = copy.deepcopy(cand)
    tampered_cand["network_performed"] = True
    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), tampered_cand, operator_id="operator_jim",
        decision_packet_id="decision_packet_0001")
    assert (al.BLOCK_DECISION_CANDIDATE_UNSAFE + ":network_performed"
            in dp["blocked_reasons"])


def test_r1_packet_and_doc_include_invariants_and_blocked_reasons():
    packet = al.build_packet()
    for inv in (
            "readiness_review_revalidates_all_input_safety_flags",
            "decision_packet_revalidates_all_input_safety_flags",
            "integrity_report_clear_metadata_cannot_hide_unsafe_behavior",
            "candidate_checksum_match_cannot_hide_unsafe_behavior",
            "ledger_entry_checksum_match_cannot_hide_unsafe_behavior",
            "unsafe_input_artifact_blocks_review_or_decision"):
        assert inv in packet["hard_invariants"], inv
    for reason in (
            al.BLOCK_REVIEW_LEDGER_ENTRY_UNSAFE,
            al.BLOCK_REVIEW_INTEGRITY_REPORT_UNSAFE,
            al.BLOCK_REVIEW_GATE_RESULT_UNSAFE,
            al.BLOCK_REVIEW_CANDIDATE_UNSAFE,
            al.BLOCK_DECISION_REVIEW_UNSAFE,
            al.BLOCK_DECISION_LEDGER_ENTRY_UNSAFE,
            al.BLOCK_DECISION_CANDIDATE_UNSAFE):
        assert reason in packet["r1_revalidation_blocked_reasons"], reason
    doc = al.build_doc()
    assert "R1 input safety revalidation" in doc
    assert al.scan_for_leaks(packet) == []
    assert al.scan_for_leaks(doc) == []
