"""Tests for the 0174TY/TZ/UA Telegram local adapter + one-request builder.

Deterministic, stdlib-only, offline. These tests assert the LOCAL adapter layer
on top of the accepted design chain:

  * 0174TY TelegramRenderedPayload -- approved text in, length/parse-mode
    validated, preview/send separated, fail-closed on financial/forbidden.
  * 0174TZ TelegramOneRequestObject + TelegramAdapterCapabilityEnforcer --
    exactly one future request, no URL/token/raw chat id, text-only path.
  * 0174UA RedactedTelegramResponseShape + readiness classifier -- future-only
    redacted shape, never live.

The upstream provider live-gate design is built through the GENUINE authority
chain (0174ED -> ... -> 0174TO -> 0174TV/TW/TX), never hand-rolled.
"""

import copy

from live_contentops import approval_ledger_payload_hash_contract as approval
from live_contentops import dispatch_outbox_idempotency_contract as outbox
from live_contentops import remote_operator_inbox_intent_review_contract as review
from live_contentops import editorial_preview_supervised_dry_run_contract as ep
from live_contentops import supervised_dispatch_safety_gate_contract as sg
from live_contentops import provider_live_gate_design_contract as pg
from live_contentops import telegram_local_adapter_contract as ad


# --------------------------------------------------------------------------- #
# Fixtures -- genuine 0174ED -> ... -> 0174TX chain
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


def _real_candidate_gate():
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


def _recorded_design():
    dr = pg.review_provider_documentation(
        provider=pg.PROVIDER_TELEGRAM, reviewer_operator_id="operator_jim",
        reviewed_at_epoch=2200)
    cm = pg.build_telegram_capability_map(
        dr, requested_optional_params=("parse_mode",),
        requested_parse_mode="HTML", planned_text_length=280)
    gate = _real_candidate_gate()
    return pg.build_provider_live_gate_design(
        dr, cm, gate, credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha",
        payload_hash_short="0123456789abcdef", design_operator_id="operator_jim")


# Adapter helpers.
def _ok_rendered():
    return ad.render_telegram_payload(
        approved_text="One CPI print is not a regime shift.",
        preview_text="One CPI print is not a regime shift.",
        parse_mode="HTML", content_lane="grounded_news_context")


def _allowed_enforcer():
    return ad.enforce_capability(
        requested_optional_params=("parse_mode",))


def _built_request(rendered=None, enforcer=None):
    rp = rendered or _ok_rendered()
    en = enforcer or _allowed_enforcer()
    return ad.build_one_request_object(
        rp, en, credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha",
        optional_params=("parse_mode",), request_id="req_0001")


# --------------------------------------------------------------------------- #
# 0174TY TelegramRenderedPayload
# --------------------------------------------------------------------------- #
def test_rendered_payload_ok_and_not_live():
    rp = _ok_rendered()
    assert rp["status"] == ad.Status.PASS
    assert rp["rendered_payload_outcome_class"] == ad.RENDER_OK
    assert rp["rendered_payload_ok"] is True
    assert rp["preview_and_send_separated"] is True
    assert rp["live_ready"] is False
    assert rp["send_text_length"] == len(rp["send_text"])
    assert rp["rendered_payload_checksum"]


def test_rendered_payload_empty_text_blocks():
    rp = ad.render_telegram_payload(approved_text="", parse_mode="none")
    assert rp["status"] == ad.Status.BLOCKED
    assert ad.BLOCK_TEXT_EMPTY in rp["blocked_reasons"]


def test_rendered_payload_too_long_blocks():
    rp = ad.render_telegram_payload(
        approved_text="x" * (ad.TELEGRAM_MAX_TEXT_LENGTH + 1), parse_mode="none")
    assert rp["status"] == ad.Status.BLOCKED
    assert ad.BLOCK_TEXT_LENGTH_OUT_OF_BOUNDS in rp["blocked_reasons"]


def test_rendered_payload_bad_parse_mode_blocks():
    rp = ad.render_telegram_payload(
        approved_text="Neutral macro context.", parse_mode="YAML")
    assert rp["status"] == ad.Status.BLOCKED
    assert ad.BLOCK_PARSE_MODE_NOT_ALLOWLISTED in rp["blocked_reasons"]


def test_rendered_payload_parse_mode_none_ok():
    rp = ad.render_telegram_payload(
        approved_text="Neutral macro context.", parse_mode="none")
    assert rp["status"] == ad.Status.PASS


def test_rendered_payload_financial_advice_fail_closed():
    rp = ad.render_telegram_payload(
        approved_text="You should buy now for guaranteed profit.",
        parse_mode="none")
    assert rp["status"] == ad.Status.FAIL_CLOSED
    assert ad.BLOCK_FINANCIAL_ADVICE in rp["blocked_reasons"]


def test_rendered_payload_forbidden_token_fail_closed():
    rp = ad.render_telegram_payload(
        approved_text="leak ghp_abcdefghijklmnopqrstuvwxyz0123456789",
        parse_mode="none")
    assert rp["status"] == ad.Status.FAIL_CLOSED
    assert ad.BLOCK_FORBIDDEN_VALUE in rp["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 0174TZ TelegramAdapterCapabilityEnforcer
# --------------------------------------------------------------------------- #
def test_enforcer_allows_text_one_request_path():
    en = _allowed_enforcer()
    assert en["status"] == ad.Status.PASS
    assert en["capability_enforcer_outcome_class"] == ad.ENFORCER_ALLOWED
    assert en["capability_allowed"] is True
    assert en["live_ready"] is False


def test_enforcer_unsupported_method_blocks():
    en = ad.enforce_capability(requested_method="editMessageText")
    assert en["status"] == ad.Status.BLOCKED
    assert ad.BLOCK_METHOD_NOT_SUPERVISED_SEND in en["blocked_reasons"]


def test_enforcer_inbound_receiving_blocks():
    for method in ad.INBOUND_METHODS_NOT_USED:
        en = ad.enforce_capability(requested_method=method)
        assert en["status"] == ad.Status.BLOCKED
        assert ad.BLOCK_INBOUND_RECEIVING_USED in en["blocked_reasons"]


def test_enforcer_media_edit_delete_reply_automation_blocks():
    for cls in ("media_send", "message_edit", "message_delete",
                "reply_automation"):
        en = ad.enforce_capability(requested_automation_classes=(cls,))
        assert en["status"] == ad.Status.BLOCKED
        assert any(r.startswith(ad.BLOCK_AUTOMATION_REJECTED)
                   for r in en["blocked_reasons"])


def test_enforcer_non_allowlisted_optional_param_blocks():
    en = ad.enforce_capability(requested_optional_params=("not_a_real_param",))
    assert en["status"] == ad.Status.BLOCKED
    assert any(r.startswith(ad.BLOCK_OPTIONAL_PARAM_NOT_ALLOWLISTED)
               for r in en["blocked_reasons"])


def test_enforcer_wrong_capability_blocks():
    en = ad.enforce_capability(requested_capability="bulk_broadcast")
    assert en["status"] == ad.Status.BLOCKED
    assert ad.BLOCK_CAPABILITY_NOT_ALLOWED in en["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 0174TZ TelegramOneRequestObject
# --------------------------------------------------------------------------- #
def test_one_request_object_built_single_request_no_secrets():
    ro = _built_request()
    assert ro["status"] == ad.Status.PASS
    assert ro["one_request_outcome_class"] == ad.REQUEST_OK
    assert ro["one_request_built"] is True
    assert ro["request_count_authorized"] == 1
    d = ro["request_descriptor"]
    assert d["contains_url_with_token"] is False
    assert d["contains_token_value"] is False
    assert d["contains_raw_chat_id"] is False
    assert d["auto_retry_allowed"] is False
    assert d["scheduler_enabled"] is False
    assert d["webhook_registered"] is False
    assert d["polling_enabled"] is False
    assert d["credential_referenced_by_handle_only"] is True
    assert d["destination_referenced_by_binding_only"] is True
    assert ro["one_request_checksum"]


def test_one_request_credential_and_destination_remain_symbolic():
    ro = _built_request()
    assert ro["credential_handle_id"] == "cred_handle_alpha"
    assert ro["destination_binding_id"] == "dest_binding_alpha"
    assert ro["no_raw_credential_stored"] is True
    # No raw URL/token strings present anywhere in the serialized object.
    blob = ad.serialize(ro)
    assert "https://" not in blob
    assert "/bot" not in blob


def test_one_request_blocks_when_rendered_not_ok():
    bad_rp = ad.render_telegram_payload(approved_text="", parse_mode="none")
    ro = ad.build_one_request_object(
        bad_rp, _allowed_enforcer(), credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha")
    assert ro["status"] == ad.Status.BLOCKED
    assert ad.BLOCK_RENDERED_PAYLOAD_NOT_OK in ro["blocked_reasons"]


def test_one_request_blocks_when_enforcer_not_allowed():
    bad_en = ad.enforce_capability(requested_method="editMessageText")
    ro = ad.build_one_request_object(
        _ok_rendered(), bad_en, credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha")
    assert ro["status"] == ad.Status.BLOCKED
    assert ad.BLOCK_CAPABILITY_NOT_ENFORCED in ro["blocked_reasons"]


def test_one_request_missing_credential_handle_blocks():
    ro = ad.build_one_request_object(
        _ok_rendered(), _allowed_enforcer(), credential_handle_id=None,
        destination_binding_id="dest_binding_alpha")
    assert ro["status"] == ad.Status.BLOCKED
    assert ad.BLOCK_CREDENTIAL_HANDLE_MISSING in ro["blocked_reasons"]


def test_one_request_missing_destination_binding_blocks():
    ro = ad.build_one_request_object(
        _ok_rendered(), _allowed_enforcer(),
        credential_handle_id="cred_handle_alpha", destination_binding_id=None)
    assert ro["status"] == ad.Status.BLOCKED
    assert ad.BLOCK_DESTINATION_BINDING_MISSING in ro["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 0174UA RedactedTelegramResponseShape
# --------------------------------------------------------------------------- #
def test_response_shape_stores_no_raw_provider_response():
    rs = ad.build_redacted_response_shape(
        response_status_class=ad.RESPONSE_STATUS_OK_CLASS,
        provider_code_class=ad.PROVIDER_CODE_SUCCESS_CLASS,
        message_id_class=ad.MESSAGE_ID_PRESENT_CLASS,
        request_checksum="a" * 64, response_checksum="b" * 64)
    assert rs["status"] == ad.Status.PASS
    assert rs["is_future_only_shape"] is True
    assert rs["stores_raw_provider_response"] is False
    assert rs["stores_raw_chat_id"] is False
    assert rs["stores_raw_token"] is False
    assert rs["stores_raw_url"] is False
    assert rs["stores_headers"] is False
    assert rs["stores_cookies"] is False
    assert rs["response_shape_checksum"]


def test_response_shape_coerces_unknown_classes():
    rs = ad.build_redacted_response_shape(
        response_status_class="raw_garbage",
        provider_code_class="200_OK_RAW",
        message_id_class="12345678")
    assert rs["response_status_class"] == ad.RESPONSE_STATUS_UNKNOWN_CLASS
    assert rs["provider_code_class"] == ad.PROVIDER_CODE_UNKNOWN_CLASS
    assert rs["redacted_message_id_class"] == ad.MESSAGE_ID_ABSENT_CLASS


# --------------------------------------------------------------------------- #
# 0174UA Local adapter readiness classifier
# --------------------------------------------------------------------------- #
def test_adapter_ready_not_live_for_full_local_chain():
    rp = _ok_rendered()
    en = _allowed_enforcer()
    ro = _built_request(rp, en)
    dz = _recorded_design()
    res = ad.classify_local_adapter_readiness(
        rp, en, ro, provider_live_gate_design=dz)
    assert res["status"] == ad.Status.PASS
    assert res["adapter_readiness_outcome_class"] == ad.ADAPTER_READY
    assert res["telegram_local_adapter_ready_not_live"] is True
    assert res["requires_operator_live_gate"] is True
    assert res["valid_for_live_execution"] is False
    assert res["live_ready"] is False
    assert "live_ready" not in res["adapter_readiness_outcome_class"]


def test_adapter_blocks_when_request_not_built():
    rp = _ok_rendered()
    en = _allowed_enforcer()
    bad_ro = ad.build_one_request_object(
        rp, en, credential_handle_id=None,
        destination_binding_id="dest_binding_alpha")
    res = ad.classify_local_adapter_readiness(rp, en, bad_ro)
    assert res["status"] == ad.Status.BLOCKED
    assert ad.BLOCK_REQUEST_OBJECT_NOT_BUILT in res["blocked_reasons"]


def test_adapter_fail_closed_on_forbidden():
    rp = _ok_rendered()
    en = _allowed_enforcer()
    ro = _built_request(rp, en)
    tampered = copy.deepcopy(ro)
    tampered["leak"] = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
    res = ad.classify_local_adapter_readiness(rp, en, tampered)
    assert res["status"] == ad.Status.FAIL_CLOSED
    assert ad.BLOCK_FORBIDDEN_VALUE in res["blocked_reasons"]


# --------------------------------------------------------------------------- #
# R1 upstream safety-flag revalidation
# --------------------------------------------------------------------------- #
def test_r1_detect_unsafe_behavior_claims_clean_returns_empty():
    assert ad.detect_unsafe_behavior_claims(_ok_rendered(),
                                            ad.ARTIFACT_RENDERED) == []
    assert ad.detect_unsafe_behavior_claims({}, ad.ARTIFACT_REQUEST) == []


def test_r1_tampered_rendered_live_ready_blocks_request():
    rp = _ok_rendered()
    tampered = copy.deepcopy(rp)
    tampered["live_ready"] = True
    ro = ad.build_one_request_object(
        tampered, _allowed_enforcer(),
        credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha")
    assert ro["status"] == ad.Status.BLOCKED
    assert ad.BLOCK_RENDERED_UNSAFE_BEHAVIOR in ro["blocked_reasons"]


def test_r1_tampered_request_network_performed_blocks_readiness():
    rp = _ok_rendered()
    en = _allowed_enforcer()
    ro = _built_request(rp, en)
    tampered = copy.deepcopy(ro)
    tampered["network_performed"] = True
    res = ad.classify_local_adapter_readiness(rp, en, tampered)
    assert res["status"] == ad.Status.BLOCKED
    assert (ad.BLOCK_REQUEST_UNSAFE_BEHAVIOR
            + ":network_performed") in res["blocked_reasons"]


def test_r1_tampered_design_telegram_api_called_blocks_readiness():
    rp = _ok_rendered()
    en = _allowed_enforcer()
    ro = _built_request(rp, en)
    dz = _recorded_design()
    tampered = copy.deepcopy(dz)
    tampered["telegram_api_called"] = True
    res = ad.classify_local_adapter_readiness(
        rp, en, ro, provider_live_gate_design=tampered)
    assert res["status"] == ad.Status.BLOCKED
    assert ad.BLOCK_DESIGN_UNSAFE_BEHAVIOR in res["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Module hygiene
# --------------------------------------------------------------------------- #
def test_no_forbidden_imports_or_env_access():
    from pathlib import Path
    src = Path(ad.__file__).read_text(encoding="utf-8")
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
    code = _code_only(ad.__file__)
    for banned in (".env", "getUpdates", "sendMessage", "bot_token",
                   "oauth", "access_token", "refresh_token"):
        assert banned not in code, banned


def test_module_import_has_no_side_effects(tmp_path):
    import importlib
    before = set(tmp_path.iterdir())
    importlib.reload(ad)
    after = set(tmp_path.iterdir())
    assert before == after


# --------------------------------------------------------------------------- #
# Packet + doc deterministic and leak-free
# --------------------------------------------------------------------------- #
def test_packet_is_clean_and_deterministic():
    p1 = ad.build_packet()
    p2 = ad.build_packet()
    assert p1["checksum_sha256"] == p2["checksum_sha256"]
    assert ad.scan_for_leaks(p1) == []
    assert p1["task_label"] == ad.TASK_LABEL
    assert p1["status"] == ad.Status.PASS


def test_doc_is_clean_and_deterministic():
    d1 = ad.build_doc()
    d2 = ad.build_doc()
    assert d1 == d2
    assert ad.scan_for_leaks(d1) == []
    assert "0174TY/TZ/UA" in d1
    assert ad.EXACT_NEXT_TASK_RECOMMENDATION in d1


def test_write_artifacts_writes_two_files(tmp_path):
    paths = ad.write_artifacts(str(tmp_path))
    assert len(paths) == 2
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            content = fh.read()
        assert content
        assert ad.scan_for_leaks(content) == []


def test_safety_flags_present_on_all_objects():
    rp = _ok_rendered()
    en = _allowed_enforcer()
    ro = _built_request(rp, en)
    rs = ad.build_redacted_response_shape()
    res = ad.classify_local_adapter_readiness(rp, en, ro)
    for rec in (rp, en, ro, rs, res):
        assert rec["credential_hydrated"] is False
        assert rec["network_performed"] is False
        assert rec["llm_behavior"] is False
        assert rec["dispatch_performed"] is False
        assert rec["telegram_api_called"] is False
        assert rec["live_ready"] is False
