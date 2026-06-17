"""Tests for the 0174UB/UC/UD Telegram transport boundary + single-send harness.

Deterministic, stdlib-only, offline. These tests assert the transport-boundary
DESIGN layer on top of the accepted Telegram core chain:

  * 0174UB TelegramCredentialBoundaryGate -- symbolic, declared-not-hydrated.
  * 0174UC TelegramReadOnlyIdentityCheckDesign (getMe, future-only, not run) +
    TelegramSingleSendExecutionHarnessDesign (exact future order, one send).
  * 0174UD PostRequestAuditDesign (future-only) + readiness classifier.

The built one-request object is produced through the GENUINE adapter helpers
(0174TY/TZ/UA), never hand-rolled.
"""

import copy

from live_contentops import telegram_local_adapter_contract as adapter
from live_contentops import telegram_transport_boundary_contract as tb


# --------------------------------------------------------------------------- #
# Fixtures -- genuine adapter chain
# --------------------------------------------------------------------------- #
def _ok_rendered():
    return adapter.render_telegram_payload(
        approved_text="One CPI print is not a regime shift.",
        preview_text="One CPI print is not a regime shift.",
        parse_mode="HTML", content_lane="grounded_news_context")


def _allowed_enforcer():
    return adapter.enforce_capability(requested_optional_params=("parse_mode",))


def _built_request():
    return adapter.build_one_request_object(
        _ok_rendered(), _allowed_enforcer(),
        credential_handle_id="cred_handle_alpha",
        destination_binding_id="dest_binding_alpha",
        optional_params=("parse_mode",), request_id="req_0001")


def _payload_hash():
    return _built_request()["request_descriptor"]["send_text_checksum"]


def _boundary():
    return tb.declare_credential_boundary(
        operator_gate_id="operator_gate_alpha",
        credential_handle_id="cred_handle_alpha")


def _identity():
    return tb.design_read_only_identity_check(
        operator_gate_id="operator_gate_alpha")


def _harness(boundary=None, identity=None, request=None, phash=None):
    cb = boundary or _boundary()
    ic = identity or _identity()
    ro = request or _built_request()
    h = phash or ro["request_descriptor"]["send_text_checksum"]
    return tb.design_single_send_harness(
        cb, ic, ro, operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding=h)


# --------------------------------------------------------------------------- #
# 0174UB TelegramCredentialBoundaryGate
# --------------------------------------------------------------------------- #
def test_boundary_declared_not_hydrated():
    cb = _boundary()
    assert cb["status"] == tb.Status.PASS
    assert cb["credential_boundary_outcome_class"] == tb.BOUNDARY_DECLARED
    assert cb["credential_boundary_declared"] is True
    assert cb["credential_hydrated"] is False
    assert cb["future_hydration_step_declared"] is True
    assert cb["credential_boundary_checksum"]


def test_boundary_reads_no_env_keyring_files():
    cb = _boundary()
    assert cb["reads_env"] is False
    assert cb["reads_dotenv_file"] is False
    assert cb["reads_keyring"] is False
    assert cb["reads_credential_file"] is False
    assert cb["reads_browser_session"] is False


def test_boundary_stores_no_secret_material():
    cb = _boundary()
    for key in ("stores_token", "stores_bot_token", "stores_header",
                "stores_cookie", "stores_url_with_token", "stores_raw_chat_id",
                "stores_username", "stores_webhook_url"):
        assert cb[key] is False


def test_boundary_missing_operator_gate_id_blocks():
    cb = tb.declare_credential_boundary(
        operator_gate_id=None, credential_handle_id="cred_handle_alpha")
    assert cb["status"] == tb.Status.BLOCKED
    assert tb.BLOCK_OPERATOR_GATE_ID_MISSING in cb["blocked_reasons"]


def test_boundary_missing_credential_handle_blocks():
    cb = tb.declare_credential_boundary(
        operator_gate_id="operator_gate_alpha", credential_handle_id=None)
    assert cb["status"] == tb.Status.BLOCKED
    assert tb.BLOCK_CREDENTIAL_HANDLE_MISSING in cb["blocked_reasons"]


def test_boundary_forbidden_token_fail_closed():
    cb = tb.declare_credential_boundary(
        operator_gate_id="operator_gate_alpha",
        credential_handle_id="ghp_abcdefghijklmnopqrstuvwxyz0123456789")
    assert cb["status"] == tb.Status.FAIL_CLOSED
    assert tb.BLOCK_FORBIDDEN_VALUE in cb["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 0174UC TelegramReadOnlyIdentityCheckDesign
# --------------------------------------------------------------------------- #
def test_identity_check_is_get_me_symbolic_only_not_run():
    ic = _identity()
    assert ic["status"] == tb.Status.PASS
    assert ic["identity_outcome_class"] == tb.IDENTITY_DECLARED
    assert ic["identity_method_name"] == adapter.METHOD_READ_ONLY_IDENTITY
    assert ic["identity_method_name"] == "getMe"
    assert ic["identity_method_is_read_only"] is True
    assert ic["identity_check_not_run"] is True
    assert ic["identity_check_performed"] is False
    assert ic["network_performed"] is False


def test_identity_expected_proof_shape_stores_no_response():
    ic = _identity()
    shape = ic["expected_identity_proof_shape"]
    assert shape["identity_check_not_run"] is True
    assert shape["identity_check_future_operator_gate_required"] is True
    assert shape["bot_identity_redacted_class"] in tb.BOT_IDENTITY_CLASSES
    assert shape["provider_status_code_class"] in tb.PROVIDER_CODE_CLASSES
    assert shape["response_checksum"] is None
    assert ic["stores_raw_provider_response"] is False


def test_identity_missing_operator_gate_id_blocks():
    ic = tb.design_read_only_identity_check(operator_gate_id=None)
    assert ic["status"] == tb.Status.BLOCKED
    assert tb.BLOCK_OPERATOR_GATE_ID_MISSING in ic["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 0174UC TelegramSingleSendExecutionHarnessDesign
# --------------------------------------------------------------------------- #
def test_harness_design_built_for_full_local_chain():
    h = _harness()
    assert h["status"] == tb.Status.PASS
    assert h["harness_outcome_class"] == tb.HARNESS_BUILT
    assert h["single_send_harness_design_built"] is True
    assert h["is_future_only_design"] is True
    assert h["live_ready"] is False
    assert h["valid_for_live_execution"] is False
    assert h["harness_checksum"]


def test_harness_declares_exact_future_execution_order():
    h = _harness()
    assert h["future_execution_order"] == [
        "hydrate_credential_handle_once",
        "run_read_only_identity_check_once",
        "confirm_approved_payload_hash_binding",
        "execute_exactly_one_send",
        "record_redacted_response_shape",
        "append_immutable_post_request_audit",
    ]


def test_harness_authorizes_exactly_one_send_but_performs_none():
    h = _harness()
    assert h["authorizes_exactly_one_future_send"] is True
    assert h["future_send_count_authorized"] == 1
    assert h["send_performed"] is False
    assert h["identity_check_performed"] is False


def test_harness_no_automation():
    h = _harness()
    assert h["auto_retry_allowed"] is False
    assert h["scheduler_enabled"] is False
    assert h["polling_enabled"] is False
    assert h["webhook_registered"] is False
    assert h["reply_automation_enabled"] is False


def test_harness_missing_credential_boundary_blocks():
    bad_cb = tb.declare_credential_boundary(
        operator_gate_id=None, credential_handle_id="cred_handle_alpha")
    h = tb.design_single_send_harness(
        bad_cb, _identity(), _built_request(),
        operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding=_payload_hash())
    assert h["status"] == tb.Status.BLOCKED
    assert tb.BLOCK_BOUNDARY_NOT_DECLARED in h["blocked_reasons"]


def test_harness_missing_identity_design_blocks():
    bad_ic = tb.design_read_only_identity_check(operator_gate_id=None)
    h = tb.design_single_send_harness(
        _boundary(), bad_ic, _built_request(),
        operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding=_payload_hash())
    assert h["status"] == tb.Status.BLOCKED
    assert tb.BLOCK_IDENTITY_DESIGN_MISSING in h["blocked_reasons"]


def test_harness_missing_request_object_blocks():
    bad_ro = adapter.build_one_request_object(
        _ok_rendered(), _allowed_enforcer(), credential_handle_id=None,
        destination_binding_id="dest_binding_alpha")
    h = tb.design_single_send_harness(
        _boundary(), _identity(), bad_ro,
        operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding=_payload_hash())
    assert h["status"] == tb.Status.BLOCKED
    assert tb.BLOCK_REQUEST_OBJECT_NOT_BUILT in h["blocked_reasons"]


def test_harness_missing_operator_gate_id_blocks():
    h = tb.design_single_send_harness(
        _boundary(), _identity(), _built_request(),
        operator_gate_id=None, approved_payload_hash_binding=_payload_hash())
    assert h["status"] == tb.Status.BLOCKED
    assert tb.BLOCK_OPERATOR_GATE_ID_MISSING in h["blocked_reasons"]


def test_harness_missing_payload_hash_binding_blocks():
    h = tb.design_single_send_harness(
        _boundary(), _identity(), _built_request(),
        operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding=None)
    assert h["status"] == tb.Status.BLOCKED
    assert tb.BLOCK_PAYLOAD_HASH_BINDING_MISSING in h["blocked_reasons"]


def test_harness_payload_hash_mismatch_blocks():
    h = tb.design_single_send_harness(
        _boundary(), _identity(), _built_request(),
        operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding="f" * 64)
    assert h["status"] == tb.Status.BLOCKED
    assert tb.BLOCK_PAYLOAD_HASH_MISMATCH in h["blocked_reasons"]


def test_harness_forbidden_value_fail_closed():
    h = tb.design_single_send_harness(
        _boundary(), _identity(), _built_request(),
        operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding="ghp_abcdefghijklmnopqrstuvwxyz0123456789")
    assert h["status"] == tb.Status.FAIL_CLOSED
    assert tb.BLOCK_FORBIDDEN_VALUE in h["blocked_reasons"]


# --------------------------------------------------------------------------- #
# 0174UD PostRequestAuditDesign
# --------------------------------------------------------------------------- #
def test_audit_design_stores_no_raw_material():
    au = tb.design_post_request_audit(
        operator_gate_id="operator_gate_alpha",
        request_checksum="a" * 64, response_checksum="b" * 64,
        provider_status_class=adapter.RESPONSE_STATUS_OK_CLASS,
        redacted_message_id_class=adapter.MESSAGE_ID_PRESENT_CLASS)
    assert au["status"] == tb.Status.PASS
    assert au["audit_outcome_class"] == tb.AUDIT_DESIGNED
    assert au["is_future_only_shape"] is True
    for key in ("stores_raw_provider_response", "stores_header",
                "stores_cookie", "stores_token", "stores_raw_chat_id",
                "stores_url"):
        assert au[key] is False
    assert au["timestamp_placeholder_class"] == tb.TIMESTAMP_PLACEHOLDER_CLASS
    assert au["audit_checksum"]


def test_audit_design_coerces_unknown_classes():
    au = tb.design_post_request_audit(
        operator_gate_id="operator_gate_alpha",
        provider_status_class="raw_200_status",
        redacted_message_id_class="999888")
    assert au["provider_status_class"] == adapter.RESPONSE_STATUS_UNKNOWN_CLASS
    assert au["redacted_message_id_class"] == adapter.MESSAGE_ID_ABSENT_CLASS


def test_audit_design_forbidden_value_fail_closed():
    au = tb.design_post_request_audit(
        operator_gate_id="ghp_abcdefghijklmnopqrstuvwxyz0123456789")
    assert au["status"] == tb.Status.FAIL_CLOSED
    assert au["audit_outcome_class"] == tb.AUDIT_FAIL_CLOSED


# --------------------------------------------------------------------------- #
# 0174UD Transport-harness readiness classifier
# --------------------------------------------------------------------------- #
def test_transport_harness_ready_not_live_for_full_chain():
    cb = _boundary()
    ic = _identity()
    ro = _built_request()
    hd = tb.design_single_send_harness(
        cb, ic, ro, operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding=ro["request_descriptor"]["send_text_checksum"])
    res = tb.classify_transport_harness_design_readiness(cb, ic, ro, hd)
    assert res["status"] == tb.Status.PASS
    assert res["transport_harness_readiness_outcome_class"] == tb.READINESS_READY
    assert res["telegram_transport_harness_design_ready_not_live"] is True
    assert res["requires_operator_live_gate"] is True
    assert res["valid_for_live_execution"] is False
    assert res["live_ready"] is False


def test_transport_harness_blocks_when_harness_not_built():
    cb = _boundary()
    ic = _identity()
    ro = _built_request()
    bad_hd = tb.design_single_send_harness(
        cb, ic, ro, operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding="f" * 64)
    res = tb.classify_transport_harness_design_readiness(cb, ic, ro, bad_hd)
    assert res["status"] == tb.Status.BLOCKED
    assert tb.BLOCK_HARNESS_NOT_BUILT in res["blocked_reasons"]


def test_transport_harness_fail_closed_on_forbidden():
    cb = _boundary()
    ic = _identity()
    ro = _built_request()
    hd = tb.design_single_send_harness(
        cb, ic, ro, operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding=ro["request_descriptor"]["send_text_checksum"])
    tampered = copy.deepcopy(hd)
    tampered["leak"] = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
    res = tb.classify_transport_harness_design_readiness(cb, ic, ro, tampered)
    assert res["status"] == tb.Status.FAIL_CLOSED
    assert tb.BLOCK_FORBIDDEN_VALUE in res["blocked_reasons"]


# --------------------------------------------------------------------------- #
# R1 upstream safety-flag revalidation
# --------------------------------------------------------------------------- #
def test_r1_clean_artifacts_return_empty():
    assert tb.detect_unsafe_behavior_claims(_boundary(),
                                            tb.ARTIFACT_BOUNDARY) == []
    assert tb.detect_unsafe_behavior_claims({}, tb.ARTIFACT_HARNESS) == []


def test_r1_tampered_request_network_performed_blocks_harness():
    tampered = copy.deepcopy(_built_request())
    tampered["network_performed"] = True
    h = tb.design_single_send_harness(
        _boundary(), _identity(), tampered,
        operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding=_payload_hash())
    assert h["status"] == tb.Status.BLOCKED
    assert (tb.BLOCK_REQUEST_UNSAFE_BEHAVIOR
            + ":network_performed") in h["blocked_reasons"]


def test_r1_tampered_boundary_credential_hydrated_blocks_harness():
    tampered = copy.deepcopy(_boundary())
    tampered["credential_hydrated"] = True
    h = tb.design_single_send_harness(
        tampered, _identity(), _built_request(),
        operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding=_payload_hash())
    assert h["status"] == tb.Status.BLOCKED
    assert (tb.BLOCK_BOUNDARY_UNSAFE_BEHAVIOR
            + ":credential_hydrated") in h["blocked_reasons"]
    # The bare boundary-unsafe class is also present.
    assert tb.BLOCK_BOUNDARY_UNSAFE_BEHAVIOR in h["blocked_reasons"]


def test_r1_tampered_boundary_credential_hydrated_blocks_readiness():
    cb = copy.deepcopy(_boundary())
    cb["credential_hydrated"] = True
    ic = _identity()
    ro = _built_request()
    # Build a clean harness first, then classify with tampered boundary.
    hd = tb.design_single_send_harness(
        _boundary(), ic, ro, operator_gate_id="operator_gate_alpha",
        approved_payload_hash_binding=ro["request_descriptor"]["send_text_checksum"])
    res = tb.classify_transport_harness_design_readiness(cb, ic, ro, hd)
    assert res["status"] == tb.Status.BLOCKED
    assert tb.BLOCK_BOUNDARY_UNSAFE_BEHAVIOR in res["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Inbound-receiving / reply automation still absent
# --------------------------------------------------------------------------- #
def test_inbound_methods_still_absent():
    h = _harness()
    assert h["inbound_methods_not_used"] == list(adapter.INBOUND_METHODS_NOT_USED)
    assert "getUpdates" in h["inbound_methods_not_used"]
    assert "setWebhook" in h["inbound_methods_not_used"]
    assert h["reply_automation_enabled"] is False


# --------------------------------------------------------------------------- #
# Module hygiene
# --------------------------------------------------------------------------- #
def test_no_forbidden_imports_or_env_access():
    import re
    from pathlib import Path
    src = Path(tb.__file__).read_text(encoding="utf-8")
    # Word-boundary import checks so a legitimate local module import
    # (telegram_local_adapter_contract) is not mistaken for the telegram SDK.
    for mod in ("requests", "httpx", "aiohttp", "urllib", "socket", "ssl",
                "webbrowser", "subprocess", "dotenv", "keyring", "sqlite3",
                "openai", "anthropic", "telegram", "tweepy", "selenium",
                "playwright"):
        assert not re.search(r"\bimport " + mod + r"\b", src), mod
    for attr in ("os.environ", "os.getenv"):
        assert attr not in src, attr


def _code_only(path):
    import io
    import tokenize
    from pathlib import Path
    src = Path(path).read_text(encoding="utf-8")
    # Skip string + comment tokens. On Python 3.12+ f-strings tokenize into
    # FSTRING_START/MIDDLE/END, so skip those too (descriptive doc prose).
    skip = {tokenize.STRING, tokenize.COMMENT}
    for name in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END"):
        if hasattr(tokenize, name):
            skip.add(getattr(tokenize, name))
    out = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in skip:
                continue
            out.append(tok.string)
    except tokenize.TokenError:
        return src
    return " ".join(out)


def test_no_network_or_credential_access_strings():
    code = _code_only(tb.__file__)
    for banned in (".env", "getUpdates", "sendMessage", "getMe", "bot_token",
                   "oauth", "access_token", "refresh_token"):
        assert banned not in code, banned


def test_module_import_has_no_side_effects(tmp_path):
    import importlib
    before = set(tmp_path.iterdir())
    importlib.reload(tb)
    after = set(tmp_path.iterdir())
    assert before == after


# --------------------------------------------------------------------------- #
# Packet + doc deterministic and leak-free
# --------------------------------------------------------------------------- #
def test_packet_is_clean_and_deterministic():
    p1 = tb.build_packet()
    p2 = tb.build_packet()
    assert p1["checksum_sha256"] == p2["checksum_sha256"]
    assert tb.scan_for_leaks(p1) == []
    assert p1["task_label"] == tb.TASK_LABEL
    assert p1["status"] == tb.Status.PASS


def test_doc_is_clean_and_deterministic():
    d1 = tb.build_doc()
    d2 = tb.build_doc()
    assert d1 == d2
    assert tb.scan_for_leaks(d1) == []
    assert "0174UB/UC/UD" in d1
    assert tb.EXACT_NEXT_TASK_RECOMMENDATION in d1


def test_write_artifacts_writes_two_files(tmp_path):
    paths = tb.write_artifacts(str(tmp_path))
    assert len(paths) == 2
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            content = fh.read()
        assert content
        assert tb.scan_for_leaks(content) == []


def test_safety_flags_present_on_all_objects():
    cb = _boundary()
    ic = _identity()
    ro = _built_request()
    hd = _harness(boundary=cb, identity=ic, request=ro)
    au = tb.design_post_request_audit(operator_gate_id="operator_gate_alpha")
    res = tb.classify_transport_harness_design_readiness(cb, ic, ro, hd)
    for rec in (cb, ic, hd, au, res):
        assert rec["credential_hydrated"] is False
        assert rec["network_performed"] is False
        assert rec["telegram_api_called"] is False
        assert rec["identity_check_performed"] is False
        assert rec["live_ready"] is False
        assert rec["valid_for_live_execution"] is False
