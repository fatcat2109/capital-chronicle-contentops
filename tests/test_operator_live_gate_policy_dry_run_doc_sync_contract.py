"""Tests for the 0174TS/TT/TU policy dry-run + checklist packet + doc/state sync.

Deterministic, stdlib-only, offline. These tests assert the LOCAL operator
live-gate policy dry-run + checklist + documentation/state sync layer on top of
the accepted chain:

  * 0174TS operator live-gate policy dry-run -- fail-closed by default; the only
    non-blocked outcome is policy-dry-run-complete-not-live.
  * 0174TT live-gate operator checklist packet -- never approval, never live
    readiness; every item defaults to operator_action_required + checked=False.
  * 0174TU documentation/state sync packet -- records preserved blockers + the
    exact next task; the accepted baseline is for HUMAN audit only.

All upstream objects are built through the GENUINE authority chain
(0174ED -> 0174EE -> 0174TG/TH/TI -> 0174TJ/TK/TL -> 0174TM/TN/TO -> 0174TP/TQ/TR),
never via hand-rolled dicts, so the bindings are real.
"""

import copy

from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import dispatch_outbox_idempotency_contract as outbox
from live_contentops import remote_operator_inbox_intent_review_contract as review
from live_contentops import editorial_preview_supervised_dry_run_contract as ep
from live_contentops import supervised_dispatch_safety_gate_contract as sg
from live_contentops import redacted_immutable_audit_live_gate_review_contract as al
from live_contentops import (
    operator_live_gate_policy_dry_run_doc_sync_contract as ds)


# --------------------------------------------------------------------------- #
# Fixtures / helpers -- the genuine 0174ED -> ... -> 0174TR chain
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
    entry, rr, er, ps, dr = _full_dry_run(variant)
    ks = _clear_kill_switch(dr)
    rp = _clear_rate_policy()
    gate_result = sg.run_one_request_dispatch_gate(
        _bundle(dr, ks, rp, entry, request_id=request_id, variant=variant))
    assert gate_result["dispatch_gate_outcome_class"] == sg.GATE_CANDIDATE_CREATED
    candidate = gate_result["dispatch_authorization_candidate"]
    audit = sg.build_redacted_immutable_dispatch_audit(gate_result, ks, rp)
    return gate_result, candidate, audit, ks, rp


def _decision_chain(request_id="supervised_request_0001",
                    ledger_entry_id="audit_ledger_0001",
                    decision_packet_id="decision_packet_0001",
                    operator_id="operator_jim", variant=""):
    """Return (decision_packet, latest_ledger_entry) via the genuine chain."""
    gr, cand, audit, ks, rp = _gate_chain(request_id, variant)
    ledger = al.RedactedAuditLedger()
    ledger.append(
        gr, cand, audit, operator_id=operator_id,
        ledger_entry_id=ledger_entry_id, created_at_epoch=2200,
        policy_snapshot_id="ks_policy_v1")
    report = ledger.build_integrity_report()
    rev = al.run_operator_live_gate_readiness_review(
        ledger.latest_entry(), report, gr, cand,
        operator_id=operator_id, current_policy_snapshot_id="ks_policy_v1",
        operator_review_id="operator_review_0001" + variant)
    assert rev["readiness_outcome_class"] == al.REVIEW_EVIDENCE_READY
    dp = al.build_live_gate_decision_packet(
        rev, ledger.latest_entry(), cand, operator_id=operator_id,
        decision_packet_id=decision_packet_id)
    assert dp["decision_outcome_class"] == al.DECISION_CREATED
    return dp, ledger.latest_entry()


def _complete_dry_run(operator_id="operator_jim",
                      dry_run_id="policy_dry_run_0001",
                      decision_packet_id="decision_packet_0001",
                      ledger_entry_id="audit_ledger_0001", variant=""):
    dp, entry = _decision_chain(
        decision_packet_id=decision_packet_id, ledger_entry_id=ledger_entry_id,
        operator_id=operator_id, variant=variant)
    dr = ds.run_operator_live_gate_policy_dry_run(
        dp, entry, operator_id=operator_id, policy_snapshot_id="policy_v1",
        dry_run_id=dry_run_id, created_at_epoch=2300)
    return dr, dp, entry


def _complete_checklist(operator_id="operator_jim",
                        checklist_packet_id="checklist_packet_0001",
                        decision_packet_id="decision_packet_0001",
                        variant=""):
    dr, dp, entry = _complete_dry_run(
        operator_id=operator_id, decision_packet_id=decision_packet_id,
        variant=variant)
    cp = ds.build_operator_live_gate_checklist_packet(
        dr, dp, entry, operator_id=operator_id,
        checklist_packet_id=checklist_packet_id)
    return cp, dr, dp, entry


# --------------------------------------------------------------------------- #
# 1. Full chain end-to-end (TS -> TT -> TU)
# --------------------------------------------------------------------------- #
def test_full_chain_dry_run_checklist_doc_sync():
    dr, dp, entry = _complete_dry_run()
    assert dr["policy_dry_run_outcome_class"] == ds.POLICY_DRY_RUN_COMPLETE
    assert dr["policy_dry_run_complete_not_live"] is True
    assert dr["valid_for_live_execution"] is False
    assert dr["live_ready"] is False
    assert dr["all_future_live_gates_unresolved"] is True

    cp = ds.build_operator_live_gate_checklist_packet(
        dr, dp, entry, operator_id="operator_jim",
        checklist_packet_id="checklist_packet_0001")
    assert cp["checklist_outcome_class"] == ds.CHECKLIST_PACKET_CREATED
    assert cp["checklist_is_approval"] is False
    assert cp["checklist_is_live_readiness"] is False

    sp = ds.build_local_documentation_state_sync_packet(
        dr, cp, dp, entry, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    assert sp["doc_sync_outcome_class"] == ds.DOC_SYNC_CREATED
    assert sp["exact_next_task_recommendation"] == (
        ds.EXACT_NEXT_TASK_RECOMMENDATION)
    assert sp["baseline_self_accepted"] is False
    assert sp["accepted_baseline_requires_human_audit"] is True


# --------------------------------------------------------------------------- #
# 2. 0174TS policy dry-run behaviors
# --------------------------------------------------------------------------- #
def test_dry_run_enumerates_all_future_gates_unresolved():
    dr, _, _ = _complete_dry_run()
    gates = {g["gate_id"]: g["gate_status"]
             for g in dr["remaining_future_live_gates"]}
    for gate_id in ds.REMAINING_FUTURE_LIVE_GATES:
        assert gates[gate_id] == ds.REMAINING_GATE_STATUS


def test_dry_run_binds_to_decision_packet_and_ledger_entry():
    dr, dp, entry = _complete_dry_run()
    assert dr["decision_packet_id"] == dp["decision_packet_id"]
    assert dr["ledger_entry_id"] == entry["ledger_entry_id"]
    assert dr["ledger_entry_checksum"] == entry["entry_checksum"]
    assert dr["chain_digest"] == entry["chain_digest"]
    assert dr["editorial_id"] == entry["editorial_id"]
    assert dr["preview_set_id"] == entry["preview_set_id"]


def test_dry_run_blocks_missing_decision_packet():
    _, entry = _decision_chain()
    dr = ds.run_operator_live_gate_policy_dry_run(
        None, entry, operator_id="operator_jim", policy_snapshot_id="policy_v1",
        dry_run_id="policy_dry_run_0001", created_at_epoch=2300)
    assert dr["policy_dry_run_outcome_class"] == ds.POLICY_DRY_RUN_BLOCKED
    assert ds.BLOCK_DRY_RUN_DECISION_PACKET_MISSING in dr["blocked_reasons"]
    assert dr["valid_for_live_execution"] is False


def test_dry_run_blocks_missing_ledger_entry():
    dp, _ = _decision_chain()
    dr = ds.run_operator_live_gate_policy_dry_run(
        dp, None, operator_id="operator_jim", policy_snapshot_id="policy_v1",
        dry_run_id="policy_dry_run_0001", created_at_epoch=2300)
    assert dr["policy_dry_run_outcome_class"] == ds.POLICY_DRY_RUN_BLOCKED
    assert ds.BLOCK_DRY_RUN_LEDGER_ENTRY_MISSING in dr["blocked_reasons"]


def test_dry_run_blocks_ledger_checksum_mismatch():
    dp, entry = _decision_chain()
    tampered = copy.deepcopy(entry)
    tampered["entry_checksum"] = "f" * 64
    dr = ds.run_operator_live_gate_policy_dry_run(
        dp, tampered, operator_id="operator_jim",
        policy_snapshot_id="policy_v1", dry_run_id="policy_dry_run_0001",
        created_at_epoch=2300)
    assert dr["policy_dry_run_outcome_class"] == ds.POLICY_DRY_RUN_BLOCKED
    assert ds.BLOCK_DRY_RUN_LEDGER_CHECKSUM_MISMATCH in dr["blocked_reasons"]


def test_dry_run_blocks_binding_mismatch():
    dp, entry = _decision_chain()
    tampered = copy.deepcopy(entry)
    tampered["editorial_id"] = "editorial_tampered"
    dr = ds.run_operator_live_gate_policy_dry_run(
        dp, tampered, operator_id="operator_jim",
        policy_snapshot_id="policy_v1", dry_run_id="policy_dry_run_0001",
        created_at_epoch=2300)
    assert dr["policy_dry_run_outcome_class"] == ds.POLICY_DRY_RUN_BLOCKED
    assert ds.BLOCK_DRY_RUN_BINDING_MISMATCH in dr["blocked_reasons"]
    assert any(r.startswith(ds.BLOCK_DRY_RUN_BINDING_MISMATCH + ":editorial_id")
               for r in dr["blocked_reasons"])


def test_dry_run_blocks_decision_packet_valid_for_live():
    dp, entry = _decision_chain()
    tampered = copy.deepcopy(dp)
    tampered["valid_for_live_execution"] = True
    dr = ds.run_operator_live_gate_policy_dry_run(
        tampered, entry, operator_id="operator_jim",
        policy_snapshot_id="policy_v1", dry_run_id="policy_dry_run_0001",
        created_at_epoch=2300)
    assert dr["policy_dry_run_outcome_class"] == ds.POLICY_DRY_RUN_BLOCKED
    assert ds.BLOCK_DRY_RUN_DECISION_VALID_FOR_LIVE in dr["blocked_reasons"]


def test_dry_run_blocks_operator_id_mismatch():
    dp, entry = _decision_chain()
    dr = ds.run_operator_live_gate_policy_dry_run(
        dp, entry, operator_id="operator_someone_else",
        policy_snapshot_id="policy_v1", dry_run_id="policy_dry_run_0001",
        created_at_epoch=2300)
    assert dr["policy_dry_run_outcome_class"] == ds.POLICY_DRY_RUN_BLOCKED
    assert ds.BLOCK_DRY_RUN_OPERATOR_ID_MISMATCH in dr["blocked_reasons"]


def test_dry_run_blocks_missing_policy_snapshot_and_dry_run_id():
    dp, entry = _decision_chain()
    dr = ds.run_operator_live_gate_policy_dry_run(
        dp, entry, operator_id="operator_jim", policy_snapshot_id="",
        dry_run_id="", created_at_epoch=2300)
    assert dr["policy_dry_run_outcome_class"] == ds.POLICY_DRY_RUN_BLOCKED
    assert ds.BLOCK_DRY_RUN_POLICY_SNAPSHOT_MISSING in dr["blocked_reasons"]
    assert ds.BLOCK_DRY_RUN_DRY_RUN_ID_MISSING in dr["blocked_reasons"]


def test_dry_run_fail_closed_on_forbidden_value():
    dp, entry = _decision_chain()
    tampered = copy.deepcopy(dp)
    tampered["bot_token"] = "123456:ABCDEF_secret_token_value"
    dr = ds.run_operator_live_gate_policy_dry_run(
        tampered, entry, operator_id="operator_jim",
        policy_snapshot_id="policy_v1", dry_run_id="policy_dry_run_0001",
        created_at_epoch=2300)
    assert dr["policy_dry_run_outcome_class"] == ds.POLICY_DRY_RUN_FAIL_CLOSED
    assert dr["forbidden_fields_detected"] is True
    assert dr["status"] == ds.Status.FAIL_CLOSED


def test_dry_run_blocks_unsafe_decision_packet_flag():
    dp, entry = _decision_chain()
    tampered = copy.deepcopy(dp)
    tampered["network_performed"] = True
    dr = ds.run_operator_live_gate_policy_dry_run(
        tampered, entry, operator_id="operator_jim",
        policy_snapshot_id="policy_v1", dry_run_id="policy_dry_run_0001",
        created_at_epoch=2300)
    assert dr["policy_dry_run_outcome_class"] == ds.POLICY_DRY_RUN_BLOCKED
    assert ds.BLOCK_DRY_RUN_DECISION_PACKET_UNSAFE in dr["blocked_reasons"]
    assert any(r.endswith("network_performed") for r in dr["blocked_reasons"])


def test_dry_run_blocks_unsafe_ledger_entry_flag():
    dp, entry = _decision_chain()
    tampered = copy.deepcopy(entry)
    tampered["credential_hydrated"] = True
    dr = ds.run_operator_live_gate_policy_dry_run(
        dp, tampered, operator_id="operator_jim",
        policy_snapshot_id="policy_v1", dry_run_id="policy_dry_run_0001",
        created_at_epoch=2300)
    assert dr["policy_dry_run_outcome_class"] == ds.POLICY_DRY_RUN_BLOCKED
    assert ds.BLOCK_DRY_RUN_LEDGER_ENTRY_UNSAFE in dr["blocked_reasons"]


def test_dry_run_is_redaction_clean():
    dr, _, _ = _complete_dry_run()
    assert ds.scan_for_leaks(dr) == []


def test_dry_run_integrity_report_pass():
    dr, _, _ = _complete_dry_run()
    report = ds.build_operator_live_gate_policy_dry_run_integrity_report(dr)
    assert report["status"] == ds.Status.PASS
    assert report["policy_dry_run_intact_not_live"] is True
    assert report["recomputed_policy_dry_run_checksum"] == (
        dr["policy_dry_run_checksum"])


def test_dry_run_integrity_report_detects_tamper():
    dr, _, _ = _complete_dry_run()
    tampered = copy.deepcopy(dr)
    tampered["valid_for_live_execution"] = True
    report = ds.build_operator_live_gate_policy_dry_run_integrity_report(
        tampered)
    assert report["status"] == ds.Status.BLOCKED
    assert report["policy_dry_run_intact_not_live"] is False


# --------------------------------------------------------------------------- #
# 3. 0174TT checklist packet behaviors
# --------------------------------------------------------------------------- #
def test_checklist_items_default_to_action_required_unchecked():
    cp, _, _, _ = _complete_checklist()
    assert len(cp["items"]) == len(ds.CHECKLIST_SECTIONS)
    for item in cp["items"]:
        assert item["item_status"] == ds.CHECKLIST_ITEM_STATUS_DEFAULT
        assert item["checked"] is False
        assert item["item_is_approval"] is False
        assert item["item_is_live_readiness"] is False


def test_checklist_blocks_when_dry_run_not_complete():
    dr, dp, entry = _complete_dry_run()
    tampered = copy.deepcopy(dr)
    tampered["policy_dry_run_outcome_class"] = ds.POLICY_DRY_RUN_BLOCKED
    cp = ds.build_operator_live_gate_checklist_packet(
        tampered, dp, entry, operator_id="operator_jim",
        checklist_packet_id="checklist_packet_0001")
    assert cp["checklist_outcome_class"] == ds.CHECKLIST_PACKET_BLOCKED
    assert ds.BLOCK_CHECKLIST_DRY_RUN_NOT_COMPLETE in cp["blocked_reasons"]


def test_checklist_blocks_premarked_item():
    dr, dp, entry = _complete_dry_run()
    premarked = [{"section_id": "identity_and_policy_review",
                  "item_status": "complete", "checked": True}]
    cp = ds.build_operator_live_gate_checklist_packet(
        dr, dp, entry, operator_id="operator_jim",
        checklist_packet_id="checklist_packet_0001", supplied_items=premarked)
    assert cp["checklist_outcome_class"] == ds.CHECKLIST_PACKET_BLOCKED
    assert ds.BLOCK_CHECKLIST_PREMARKED_ITEM in cp["blocked_reasons"]


def test_checklist_blocks_missing_packet_id():
    dr, dp, entry = _complete_dry_run()
    cp = ds.build_operator_live_gate_checklist_packet(
        dr, dp, entry, operator_id="operator_jim", checklist_packet_id="")
    assert cp["checklist_outcome_class"] == ds.CHECKLIST_PACKET_BLOCKED
    assert ds.BLOCK_CHECKLIST_PACKET_ID_MISSING in cp["blocked_reasons"]


def test_checklist_fail_closed_on_forbidden_value():
    dr, dp, entry = _complete_dry_run()
    tampered = copy.deepcopy(dp)
    tampered["webhook_url"] = "https://example.com/hook?token=abc"
    cp = ds.build_operator_live_gate_checklist_packet(
        dr, tampered, entry, operator_id="operator_jim",
        checklist_packet_id="checklist_packet_0001")
    assert cp["checklist_outcome_class"] == ds.CHECKLIST_PACKET_FAIL_CLOSED
    assert cp["forbidden_fields_detected"] is True


def test_checklist_is_redaction_clean():
    cp, _, _, _ = _complete_checklist()
    assert ds.scan_for_leaks(cp) == []


# --------------------------------------------------------------------------- #
# 4. 0174TT checklist registry dedup
# --------------------------------------------------------------------------- #
def test_registry_appends_then_suppresses_duplicate_packet_id():
    cp, _, _, _ = _complete_checklist()
    registry = ds.OperatorChecklistRegistry()
    first = registry.submit(cp)
    assert first["registry_outcome_class"] == ds.CHECKLIST_REGISTRY_APPENDED
    assert first["appended"] is True
    dup = registry.submit(cp)
    assert dup["registry_outcome_class"] == (
        ds.CHECKLIST_REGISTRY_DUPLICATE_PACKET_ID)
    assert dup["appended"] is False
    assert registry.packet_count() == 1


def test_registry_suppresses_duplicate_decision_id():
    cp1, _, _, _ = _complete_checklist(
        checklist_packet_id="checklist_packet_0001",
        decision_packet_id="decision_packet_shared")
    cp2, _, _, _ = _complete_checklist(
        checklist_packet_id="checklist_packet_0002",
        decision_packet_id="decision_packet_shared", variant="x")
    registry = ds.OperatorChecklistRegistry()
    registry.submit(cp1)
    dup = registry.submit(cp2)
    assert dup["registry_outcome_class"] == (
        ds.CHECKLIST_REGISTRY_DUPLICATE_DECISION_ID)
    assert registry.packet_count() == 1


def test_registry_rejects_uncreated_packet():
    dr, dp, entry = _complete_dry_run()
    cp = ds.build_operator_live_gate_checklist_packet(
        dr, dp, entry, operator_id="operator_jim", checklist_packet_id="")
    registry = ds.OperatorChecklistRegistry()
    try:
        registry.submit(cp)
        assert False, "expected ValueError"
    except ValueError:
        pass


# --------------------------------------------------------------------------- #
# 5. 0174TU documentation/state sync behaviors
# --------------------------------------------------------------------------- #
def test_doc_sync_preserves_blockers_and_next_task():
    cp, dr, dp, entry = _complete_checklist()
    sp = ds.build_local_documentation_state_sync_packet(
        dr, cp, dp, entry, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    assert sp["doc_sync_outcome_class"] == ds.DOC_SYNC_CREATED
    for blocker in ds.PRESERVED_BLOCKERS:
        assert blocker in sp["preserved_blockers"]
    assert sp["modifies_current_state_docs"] is False
    assert sp["promotes_authority"] is False
    handoff = sp["next_task_handoff_packet"]
    assert handoff["exact_next_task_recommendation"] == (
        ds.EXACT_NEXT_TASK_RECOMMENDATION)
    assert handoff["baseline_self_accepted"] is False


def test_doc_sync_blocks_when_checklist_not_created():
    cp, dr, dp, entry = _complete_checklist()
    tampered = copy.deepcopy(cp)
    tampered["checklist_outcome_class"] = ds.CHECKLIST_PACKET_BLOCKED
    sp = ds.build_local_documentation_state_sync_packet(
        dr, tampered, dp, entry, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    assert sp["doc_sync_outcome_class"] == ds.DOC_SYNC_BLOCKED
    assert ds.BLOCK_SYNC_CHECKLIST_NOT_CREATED in sp["blocked_reasons"]


def test_doc_sync_blocks_when_checklist_claims_approval():
    cp, dr, dp, entry = _complete_checklist()
    tampered = copy.deepcopy(cp)
    tampered["checklist_is_approval"] = True
    sp = ds.build_local_documentation_state_sync_packet(
        dr, tampered, dp, entry, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    assert sp["doc_sync_outcome_class"] == ds.DOC_SYNC_BLOCKED
    assert ds.BLOCK_SYNC_CHECKLIST_CLAIMS_APPROVAL in sp["blocked_reasons"]


def test_doc_sync_blocks_missing_sync_packet_id():
    cp, dr, dp, entry = _complete_checklist()
    sp = ds.build_local_documentation_state_sync_packet(
        dr, cp, dp, entry, operator_id="operator_jim", sync_packet_id="")
    assert sp["doc_sync_outcome_class"] == ds.DOC_SYNC_BLOCKED
    assert ds.BLOCK_SYNC_SYNC_PACKET_ID_MISSING in sp["blocked_reasons"]


def test_doc_sync_fail_closed_on_forbidden_value():
    cp, dr, dp, entry = _complete_checklist()
    tampered = copy.deepcopy(dp)
    tampered["access_token"] = "ya29.secret_access_token_value_here"
    sp = ds.build_local_documentation_state_sync_packet(
        dr, cp, tampered, entry, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    assert sp["doc_sync_outcome_class"] == ds.DOC_SYNC_FAIL_CLOSED
    assert sp["forbidden_fields_detected"] is True


def test_doc_sync_is_redaction_clean():
    cp, dr, dp, entry = _complete_checklist()
    sp = ds.build_local_documentation_state_sync_packet(
        dr, cp, dp, entry, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    assert ds.scan_for_leaks(sp) == []


def test_doc_sync_integrity_report_pass():
    cp, dr, dp, entry = _complete_checklist()
    sp = ds.build_local_documentation_state_sync_packet(
        dr, cp, dp, entry, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    report = ds.build_documentation_sync_integrity_report(sp)
    assert report["status"] == ds.Status.PASS
    assert report["doc_sync_intact"] is True


# --------------------------------------------------------------------------- #
# 6. Packet / doc / handoff builders + write_artifacts
# --------------------------------------------------------------------------- #
def test_build_packet_is_redaction_clean_and_deterministic():
    p1 = ds.build_packet()
    p2 = ds.build_packet()
    assert p1 == p2
    assert ds.scan_for_leaks(p1) == []
    assert p1["source_baseline_commit"] == ds.SOURCE_BASELINE_COMMIT
    assert p1["exact_next_task_recommendation"] == (
        ds.EXACT_NEXT_TASK_RECOMMENDATION)


def test_build_doc_mentions_outcomes():
    doc = ds.build_doc()
    assert ds.POLICY_DRY_RUN_COMPLETE in doc
    assert ds.CHECKLIST_PACKET_CREATED in doc
    assert ds.DOC_SYNC_CREATED in doc


def test_handoff_packet_is_redaction_clean():
    handoff = ds.build_next_task_handoff_packet()
    assert ds.scan_for_leaks(handoff) == []
    assert handoff["accepted_baseline_requires_human_audit"] is True


def test_write_artifacts_creates_files(tmp_path):
    paths = ds.write_artifacts(str(tmp_path))
    assert len(paths) == 2
    for path in paths:
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
        assert content


# --------------------------------------------------------------------------- #
# 7. R1: checklist (0174TT) revalidates unsafe flags on every input artifact
# --------------------------------------------------------------------------- #
# A tampered decision packet / ledger entry that keeps a clear outcome class +
# valid checksum but flips a live / network / credential / dispatch / readiness
# flag MUST still block the checklist packet. The truth is re-derived directly
# from the flags via detect_unsafe_behavior_claims, never from clear metadata.
def test_checklist_blocks_unsafe_decision_packet_network_performed():
    dr, dp, entry = _complete_dry_run()
    tampered = copy.deepcopy(dp)
    tampered["network_performed"] = True
    cp = ds.build_operator_live_gate_checklist_packet(
        dr, tampered, entry, operator_id="operator_jim",
        checklist_packet_id="checklist_packet_0001")
    assert cp["checklist_outcome_class"] == ds.CHECKLIST_PACKET_BLOCKED
    assert ds.BLOCK_CHECKLIST_DECISION_PACKET_UNSAFE in cp["blocked_reasons"]
    assert any(r.endswith("network_performed") for r in cp["blocked_reasons"])


def test_checklist_blocks_unsafe_decision_packet_valid_for_live():
    dr, dp, entry = _complete_dry_run()
    tampered = copy.deepcopy(dp)
    tampered["valid_for_live_execution"] = True
    cp = ds.build_operator_live_gate_checklist_packet(
        dr, tampered, entry, operator_id="operator_jim",
        checklist_packet_id="checklist_packet_0001")
    assert cp["checklist_outcome_class"] == ds.CHECKLIST_PACKET_BLOCKED
    assert ds.BLOCK_CHECKLIST_DECISION_PACKET_UNSAFE in cp["blocked_reasons"]


def test_checklist_blocks_unsafe_decision_packet_live_ready():
    dr, dp, entry = _complete_dry_run()
    tampered = copy.deepcopy(dp)
    tampered["live_ready"] = True
    cp = ds.build_operator_live_gate_checklist_packet(
        dr, tampered, entry, operator_id="operator_jim",
        checklist_packet_id="checklist_packet_0001")
    assert cp["checklist_outcome_class"] == ds.CHECKLIST_PACKET_BLOCKED
    assert ds.BLOCK_CHECKLIST_DECISION_PACKET_UNSAFE in cp["blocked_reasons"]
    assert any(r.endswith("live_ready") for r in cp["blocked_reasons"])


def test_checklist_blocks_unsafe_ledger_entry_credential_hydrated():
    dr, dp, entry = _complete_dry_run()
    tampered = copy.deepcopy(entry)
    tampered["credential_hydrated"] = True
    cp = ds.build_operator_live_gate_checklist_packet(
        dr, dp, tampered, operator_id="operator_jim",
        checklist_packet_id="checklist_packet_0001")
    assert cp["checklist_outcome_class"] == ds.CHECKLIST_PACKET_BLOCKED
    assert ds.BLOCK_CHECKLIST_LEDGER_ENTRY_UNSAFE in cp["blocked_reasons"]
    assert any(r.endswith("credential_hydrated") for r in cp["blocked_reasons"])


def test_checklist_blocks_unsafe_ledger_entry_telegram_api_called():
    dr, dp, entry = _complete_dry_run()
    tampered = copy.deepcopy(entry)
    tampered["telegram_api_called"] = True
    cp = ds.build_operator_live_gate_checklist_packet(
        dr, dp, tampered, operator_id="operator_jim",
        checklist_packet_id="checklist_packet_0001")
    assert cp["checklist_outcome_class"] == ds.CHECKLIST_PACKET_BLOCKED
    assert ds.BLOCK_CHECKLIST_LEDGER_ENTRY_UNSAFE in cp["blocked_reasons"]
    assert any(r.endswith("telegram_api_called") for r in cp["blocked_reasons"])


# --------------------------------------------------------------------------- #
# 8. R1: doc/state sync (0174TU) revalidates unsafe flags on every input
# --------------------------------------------------------------------------- #
def test_doc_sync_blocks_unsafe_dry_run_telegram_api_called():
    cp, dr, dp, entry = _complete_checklist()
    tampered = copy.deepcopy(dr)
    tampered["telegram_api_called"] = True
    sp = ds.build_local_documentation_state_sync_packet(
        tampered, cp, dp, entry, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    assert sp["doc_sync_outcome_class"] == ds.DOC_SYNC_BLOCKED
    assert ds.BLOCK_SYNC_DRY_RUN_UNSAFE in sp["blocked_reasons"]
    assert any(r.endswith("telegram_api_called") for r in sp["blocked_reasons"])


def test_doc_sync_blocks_unsafe_checklist_live_ready():
    cp, dr, dp, entry = _complete_checklist()
    tampered = copy.deepcopy(cp)
    tampered["live_ready"] = True
    sp = ds.build_local_documentation_state_sync_packet(
        dr, tampered, dp, entry, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    assert sp["doc_sync_outcome_class"] == ds.DOC_SYNC_BLOCKED
    assert ds.BLOCK_SYNC_CHECKLIST_UNSAFE in sp["blocked_reasons"]
    assert any(r.endswith("live_ready") for r in sp["blocked_reasons"])


def test_doc_sync_blocks_unsafe_decision_packet_network_performed():
    cp, dr, dp, entry = _complete_checklist()
    tampered = copy.deepcopy(dp)
    tampered["network_performed"] = True
    sp = ds.build_local_documentation_state_sync_packet(
        dr, cp, tampered, entry, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    assert sp["doc_sync_outcome_class"] == ds.DOC_SYNC_BLOCKED
    assert ds.BLOCK_SYNC_DECISION_PACKET_UNSAFE in sp["blocked_reasons"]
    assert any(r.endswith("network_performed") for r in sp["blocked_reasons"])


def test_doc_sync_blocks_unsafe_decision_packet_valid_for_live():
    cp, dr, dp, entry = _complete_checklist()
    tampered = copy.deepcopy(dp)
    tampered["valid_for_live_execution"] = True
    sp = ds.build_local_documentation_state_sync_packet(
        dr, cp, tampered, entry, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    assert sp["doc_sync_outcome_class"] == ds.DOC_SYNC_BLOCKED
    assert ds.BLOCK_SYNC_DECISION_PACKET_UNSAFE in sp["blocked_reasons"]


def test_doc_sync_blocks_unsafe_ledger_entry_credential_hydrated():
    cp, dr, dp, entry = _complete_checklist()
    tampered = copy.deepcopy(entry)
    tampered["credential_hydrated"] = True
    sp = ds.build_local_documentation_state_sync_packet(
        dr, cp, dp, tampered, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    assert sp["doc_sync_outcome_class"] == ds.DOC_SYNC_BLOCKED
    assert ds.BLOCK_SYNC_LEDGER_ENTRY_UNSAFE in sp["blocked_reasons"]
    assert any(r.endswith("credential_hydrated") for r in sp["blocked_reasons"])


def test_doc_sync_blocks_unsafe_ledger_entry_live_ready():
    cp, dr, dp, entry = _complete_checklist()
    tampered = copy.deepcopy(entry)
    tampered["live_ready"] = True
    sp = ds.build_local_documentation_state_sync_packet(
        dr, cp, dp, tampered, operator_id="operator_jim",
        sync_packet_id="sync_packet_0001")
    assert sp["doc_sync_outcome_class"] == ds.DOC_SYNC_BLOCKED
    assert ds.BLOCK_SYNC_LEDGER_ENTRY_UNSAFE in sp["blocked_reasons"]
    assert any(r.endswith("live_ready") for r in sp["blocked_reasons"])
