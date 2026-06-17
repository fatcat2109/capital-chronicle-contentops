"""Tests for the 0174TV/TW/TX provider doc review + Telegram architecture design.

Deterministic, stdlib-only, offline. These tests assert the LOCAL design layer
on top of the accepted dispatch-gate chain:

  * 0174TV provider documentation review -- official docs are the source of
    truth; fail-closed; performs NO network fetch.
  * 0174TW Telegram capability map -- the supervised single post maps to
    EXACTLY one method (``sendMessage``) with documented params/parse-modes/
    text bound; inbound receiving is not used.
  * 0174TX one-request architecture design -- credential referenced by handle
    only, never hydrated; consumes a real dispatch-authorization candidate and
    re-derives unsafe behavior (R1). The design is NEVER dispatch, live, or a
    credential hydration.

The upstream dispatch-authorization candidate is built through the GENUINE
authority chain (0174ED -> ... -> 0174TL -> 0174TM/TN/TO), never hand-rolled.
"""

import copy

from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import dispatch_outbox_idempotency_contract as outbox
from live_contentops import remote_operator_inbox_intent_review_contract as review
from live_contentops import editorial_preview_supervised_dry_run_contract as ep
from live_contentops import supervised_dispatch_safety_gate_contract as sg
from live_contentops import provider_live_gate_design_contract as pg


# --------------------------------------------------------------------------- #
# Fixtures / helpers -- the genuine 0174ED -> ... -> 0174TO chain
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


def _surface_bodies():
    return {
        ep.SURFACE_TELEGRAM_CHANNEL: "Neutral context summary for telegram.",
        ep.SURFACE_X_POST: "Grounded recap of the CPI print for X.",
        ep.SURFACE_LINKEDIN_POST: "Measured macro context note for LinkedIn.",
        ep.SURFACE_MANUAL_PUBLISH_PACKET: "Manual publish packet neutral summary.",
    }


def _full_dry_run():
    entry = _real_outbox_entry()
    rr = _real_review_approved(entry)
    er = ep.run_editorial_agent(
        rr, entry, editorial_id="editorial_0001",
        editor_operator_id="operator_jim", decided_at_epoch=1900,
        editorial_summary_redacted="Grounded recap of the CPI print.",
        content_lane="grounded_news_context")
    ps = ep.build_platform_preview_set(
        er, entry, preview_set_id="preview_set_0001", built_at_epoch=2000,
        surface_bodies_redacted=_surface_bodies())
    dr = ep.run_supervised_dry_run(
        rr, entry, er, ps, dry_run_id="dry_run_0001",
        operator_id="operator_jim", run_at_epoch=2100)
    assert dr["status"] == ep.Status.PASS
    return entry, rr, er, ps, dr


def _real_candidate_gate():
    """Return a genuine 0174TO gate result that created a candidate."""
    entry, rr, er, ps, dr = _full_dry_run()
    ks = sg.evaluate_kill_switch(
        dr, operator_id="operator_jim", policy_snapshot_id="ks_policy_v1",
        kill_switch_state=sg.KILL_SWITCH_CLEAR,
        current_policy_snapshot_id="ks_policy_v1")
    snap = sg.build_rate_spend_retry_policy_snapshot(
        policy_snapshot_id="rate_policy_v1")
    rp = sg.evaluate_rate_spend_retry_policy(snap, operator_id="operator_jim")
    bundle = sg.build_one_request_dispatch_gate_input_bundle(
        dr, ks, rp,
        operator_id="operator_jim",
        supervised_request_id="supervised_request_0001",
        outbox_entry_id=entry["outbox_entry_id"],
        payload_hash_short=entry["payload_hash_short"],
        payload_hash=entry["payload_hash"],
        idempotency_key_short=entry["idempotency_key_short"],
        idempotency_key=entry["idempotency_key"],
        approval_ledger_entry_id=entry["approval_ledger_entry_id"],
        review_challenge_id="review-chal-1",
        editorial_id="editorial_0001",
        preview_set_id="preview_set_0001")
    gate = sg.run_one_request_dispatch_gate(bundle)
    assert gate["dispatch_gate_outcome_class"] == sg.GATE_CANDIDATE_CREATED
    return gate


def _recorded_doc_review():
    return pg.review_provider_documentation(
        provider=pg.PROVIDER_TELEGRAM, reviewer_operator_id="operator_jim",
        reviewed_at_epoch=2200)


def _built_capability_map(doc_review=None):
    dr = doc_review or _recorded_doc_review()
    return pg.build_telegram_capability_map(
        dr, requested_optional_params=("parse_mode", "disable_notification"),
        requested_parse_mode="HTML", planned_text_length=280)


# --------------------------------------------------------------------------- #
# 0174TV provider documentation review
# --------------------------------------------------------------------------- #
def test_doc_review_recorded_for_official_telegram_docs():
    dr = _recorded_doc_review()
    assert dr["status"] == pg.Status.PASS
    assert dr["provider_doc_review_outcome_class"] == pg.DOC_REVIEW_RECORDED
    assert dr["provider_doc_review_recorded"] is True
    assert dr["doc_source_is_official"] is True
    assert dr["supervised_send_method"] == pg.METHOD_SUPERVISED_SEND
    assert dr["read_only_identity_method"] == pg.METHOD_READ_ONLY_IDENTITY
    assert dr["doc_review_performed_network_fetch"] is False
    assert dr["provider_doc_review_checksum"]


def test_doc_review_unsupported_provider_blocks():
    dr = pg.review_provider_documentation(
        provider="myspace", reviewer_operator_id="operator_jim")
    assert dr["status"] == pg.Status.BLOCKED
    assert pg.BLOCK_PROVIDER_NOT_SUPPORTED in dr["blocked_reasons"]


def test_doc_review_unofficial_source_blocks():
    dr = pg.review_provider_documentation(
        provider=pg.PROVIDER_TELEGRAM, reviewer_operator_id="operator_jim",
        doc_source_url="https://some-random-blog.example/telegram-tips")
    assert dr["status"] == pg.Status.BLOCKED
    assert pg.BLOCK_DOC_SOURCE_NOT_OFFICIAL in dr["blocked_reasons"]


def test_doc_review_missing_reviewer_blocks():
    dr = pg.review_provider_documentation(
        provider=pg.PROVIDER_TELEGRAM, reviewer_operator_id=None)
    assert dr["status"] == pg.Status.BLOCKED
    assert pg.BLOCK_REVIEWER_MISSING in dr["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 0174TW Telegram capability map
# --------------------------------------------------------------------------- #
def test_capability_map_built_for_supervised_send():
    cm = _built_capability_map()
    assert cm["status"] == pg.Status.PASS
    assert cm["capability_map_outcome_class"] == pg.CAPABILITY_MAP_BUILT
    assert cm["supervised_send_method"] == pg.METHOD_SUPERVISED_SEND
    assert cm["required_param_names"] == list(
        pg.SUPERVISED_SEND_REQUIRED_PARAMS)
    assert cm["max_requests_authorized_by_design"] == 1
    assert cm["long_polling_and_webhook_mutually_exclusive"] is True
    assert cm["capability_map_checksum"]


def test_capability_map_blocks_when_doc_review_not_recorded():
    bad = pg.review_provider_documentation(
        provider="myspace", reviewer_operator_id="operator_jim")
    cm = pg.build_telegram_capability_map(bad)
    assert cm["status"] == pg.Status.BLOCKED
    assert pg.BLOCK_DOC_REVIEW_NOT_RECORDED in cm["blocked_reasons"]


def test_capability_map_non_allowlisted_optional_param_blocks():
    dr = _recorded_doc_review()
    cm = pg.build_telegram_capability_map(
        dr, requested_optional_params=("not_a_real_param",))
    assert cm["status"] == pg.Status.BLOCKED
    assert any(r.startswith(pg.BLOCK_OPTIONAL_PARAM_NOT_ALLOWLISTED)
               for r in cm["blocked_reasons"])


def test_capability_map_bad_parse_mode_blocks():
    dr = _recorded_doc_review()
    cm = pg.build_telegram_capability_map(dr, requested_parse_mode="YAML")
    assert cm["status"] == pg.Status.BLOCKED
    assert pg.BLOCK_PARSE_MODE_NOT_ALLOWLISTED in cm["blocked_reasons"]


def test_capability_map_text_length_over_bound_blocks():
    dr = _recorded_doc_review()
    cm = pg.build_telegram_capability_map(dr, planned_text_length=5000)
    assert cm["status"] == pg.Status.BLOCKED
    assert pg.BLOCK_TEXT_LENGTH_OUT_OF_BOUNDS in cm["blocked_reasons"]


def test_capability_map_inbound_receiving_param_blocks():
    dr = _recorded_doc_review()
    cm = pg.build_telegram_capability_map(
        dr, requested_optional_params=("getUpdates",))
    assert cm["status"] == pg.Status.BLOCKED
    assert pg.BLOCK_INBOUND_RECEIVING_USED in cm["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 0174TX one-request architecture design
# --------------------------------------------------------------------------- #
def test_design_recorded_for_full_chain():
    dr = _recorded_doc_review()
    cm = _built_capability_map(dr)
    gate = _real_candidate_gate()
    design = pg.build_provider_live_gate_design(
        dr, cm, gate, credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha",
        payload_hash_short="0123456789abcdef", design_operator_id="operator_jim")
    assert design["status"] == pg.Status.PASS
    assert design["provider_live_gate_design_outcome_class"] == (
        pg.DESIGN_RECORDED)
    assert design["provider_live_gate_design_recorded"] is True
    assert design["requires_operator_live_gate"] is True
    assert design["valid_for_live_execution"] is False
    assert design["design_is_dispatch"] is False
    assert design["design_is_credential_hydration"] is False
    assert design["credential_boundary"]["credential_hydrated"] is False
    assert design["credential_boundary"][
        "credential_referenced_by_handle_only"] is True
    assert design["architecture"]["request_count_authorized_by_design"] == 1
    assert design["provider_live_gate_design_checksum"]


def test_design_missing_credential_handle_blocks():
    dr = _recorded_doc_review()
    cm = _built_capability_map(dr)
    gate = _real_candidate_gate()
    design = pg.build_provider_live_gate_design(
        dr, cm, gate, credential_handle_id=None,
        destination_binding_id="dest_binding_alpha")
    assert design["status"] == pg.Status.BLOCKED
    assert pg.BLOCK_CREDENTIAL_HANDLE_MISSING in design["blocked_reasons"]


def test_design_blocks_when_candidate_not_created():
    dr = _recorded_doc_review()
    cm = _built_capability_map(dr)
    not_candidate = {"dispatch_gate_outcome_class": sg.GATE_BLOCKED}
    design = pg.build_provider_live_gate_design(
        dr, cm, not_candidate, credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha")
    assert design["status"] == pg.Status.BLOCKED
    assert pg.BLOCK_CANDIDATE_NOT_CREATED in design["blocked_reasons"]


def test_design_blocks_when_capability_map_not_built():
    dr = _recorded_doc_review()
    bad_cm = pg.build_telegram_capability_map(dr, requested_parse_mode="YAML")
    gate = _real_candidate_gate()
    design = pg.build_provider_live_gate_design(
        dr, bad_cm, gate, credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha")
    assert design["status"] == pg.Status.BLOCKED
    assert pg.BLOCK_CAPABILITY_MAP_NOT_BUILT in design["blocked_reasons"]


# --------------------------------------------------------------------------- #
# R1 upstream safety-flag revalidation
# --------------------------------------------------------------------------- #
def test_r1_detect_unsafe_behavior_claims_clean_returns_empty():
    dr = _recorded_doc_review()
    assert pg.detect_unsafe_behavior_claims(dr, pg.ARTIFACT_DOC_REVIEW) == []
    assert pg.detect_unsafe_behavior_claims({}, pg.ARTIFACT_CANDIDATE) == []


def test_r1_detect_unsafe_behavior_claims_reports_base_and_flag_suffix():
    reasons = pg.detect_unsafe_behavior_claims(
        {"network_performed": True}, pg.ARTIFACT_CANDIDATE)
    assert pg.BLOCK_CANDIDATE_UNSAFE_BEHAVIOR in reasons
    assert (pg.BLOCK_CANDIDATE_UNSAFE_BEHAVIOR
            + ":network_performed") in reasons


def test_r1_tampered_candidate_telegram_api_called_blocks():
    dr = _recorded_doc_review()
    cm = _built_capability_map(dr)
    gate = _real_candidate_gate()
    tampered = copy.deepcopy(gate)
    tampered["telegram_api_called"] = True
    design = pg.build_provider_live_gate_design(
        dr, cm, tampered, credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha")
    assert design["status"] == pg.Status.BLOCKED
    assert pg.BLOCK_CANDIDATE_UNSAFE_BEHAVIOR in design["blocked_reasons"]


def test_r1_tampered_candidate_credential_hydrated_blocks():
    dr = _recorded_doc_review()
    cm = _built_capability_map(dr)
    gate = _real_candidate_gate()
    tampered = copy.deepcopy(gate)
    tampered["credential_hydrated"] = True
    design = pg.build_provider_live_gate_design(
        dr, cm, tampered, credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha")
    assert design["status"] == pg.Status.BLOCKED
    assert (pg.BLOCK_CANDIDATE_UNSAFE_BEHAVIOR
            + ":credential_hydrated") in design["blocked_reasons"]


def test_r1_tampered_capability_map_live_ready_blocks():
    dr = _recorded_doc_review()
    cm = _built_capability_map(dr)
    gate = _real_candidate_gate()
    tampered_cm = copy.deepcopy(cm)
    tampered_cm["live_ready"] = True
    design = pg.build_provider_live_gate_design(
        dr, tampered_cm, gate, credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha")
    assert design["status"] == pg.Status.BLOCKED
    assert pg.BLOCK_CAPABILITY_MAP_UNSAFE_BEHAVIOR in design["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Fail-closed on forbidden / financial-advice content
# --------------------------------------------------------------------------- #
def test_design_fail_closed_on_forbidden_value():
    dr = _recorded_doc_review()
    cm = _built_capability_map(dr)
    gate = _real_candidate_gate()
    tampered = copy.deepcopy(gate)
    tampered["leak"] = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
    design = pg.build_provider_live_gate_design(
        dr, cm, tampered, credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha")
    assert design["status"] == pg.Status.FAIL_CLOSED
    assert pg.BLOCK_FORBIDDEN_VALUE in design["blocked_reasons"]


def test_design_fail_closed_on_financial_advice():
    dr = _recorded_doc_review()
    cm = _built_capability_map(dr)
    gate = _real_candidate_gate()
    tampered = copy.deepcopy(gate)
    tampered["editorial_note"] = "You should buy now for guaranteed profit."
    design = pg.build_provider_live_gate_design(
        dr, cm, tampered, credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha")
    assert design["status"] == pg.Status.FAIL_CLOSED
    assert pg.BLOCK_FINANCIAL_ADVICE in design["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Module hygiene
# --------------------------------------------------------------------------- #
def test_no_forbidden_imports_or_env_access():
    from pathlib import Path
    src = Path(pg.__file__).read_text(encoding="utf-8")
    for banned in ("import requests", "import httpx", "import aiohttp",
                   "import urllib", "import socket", "import ssl",
                   "import webbrowser", "import subprocess", "import dotenv",
                   "import keyring", "import sqlite3", "import openai",
                   "import anthropic", "import telegram", "import tweepy",
                   "import selenium", "import playwright",
                   "os.environ", "os.getenv"):
        assert banned not in src, banned


def _code_only(path):
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
    code = _code_only(pg.__file__)
    for banned in (".env", "getUpdates", "sendMessage", "bot_token",
                   "oauth", "access_token", "refresh_token"):
        assert banned not in code, banned


def test_module_import_has_no_side_effects(tmp_path):
    import importlib
    before = set(tmp_path.iterdir())
    importlib.reload(pg)
    after = set(tmp_path.iterdir())
    assert before == after


# --------------------------------------------------------------------------- #
# Packet + doc deterministic and leak-free
# --------------------------------------------------------------------------- #
def test_packet_is_clean_and_deterministic():
    p1 = pg.build_packet()
    p2 = pg.build_packet()
    assert p1["checksum_sha256"] == p2["checksum_sha256"]
    assert pg.scan_for_leaks(p1) == []
    assert p1["task_label"] == pg.TASK_LABEL
    assert p1["status"] == pg.Status.PASS
    assert p1["supervised_send_method"] == pg.METHOD_SUPERVISED_SEND


def test_doc_is_clean_and_deterministic():
    d1 = pg.build_doc()
    d2 = pg.build_doc()
    assert d1 == d2
    assert pg.scan_for_leaks(d1) == []
    assert "0174TV/TW/TX" in d1
    assert pg.EXACT_NEXT_TASK_RECOMMENDATION in d1


def test_write_artifacts_writes_two_files(tmp_path):
    paths = pg.write_artifacts(str(tmp_path))
    assert len(paths) == 2
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            content = fh.read()
        assert content
        assert pg.scan_for_leaks(content) == []


def test_safety_flags_present_on_all_objects():
    dr = _recorded_doc_review()
    cm = _built_capability_map(dr)
    gate = _real_candidate_gate()
    design = pg.build_provider_live_gate_design(
        dr, cm, gate, credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha")
    for rec in (dr, cm, design):
        assert rec["credential_hydrated"] is False
        assert rec["network_performed"] is False
        assert rec["llm_behavior"] is False
        assert rec["dispatch_performed"] is False
        assert rec["telegram_api_called"] is False
