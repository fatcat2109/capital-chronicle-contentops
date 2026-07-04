"""Tests for the 0174UE/UF/UG Telegram read-only identity pilot.

Every test uses an injected/mock transport and an injected ``env_reader`` -- NO
real network call and NO real environment read is ever performed here.
"""

import json

import pytest

from live_contentops import telegram_read_only_identity_pilot as pilot


GATE_ID = "operator_gate_0174ue_test"
# A plausible-shaped FAKE token used ONLY in-memory via an injected env_reader.
# It is never written to disk and never committed (the env-hygiene + leak guards
# additionally assert no secret-like values land in tracked files).
FAKE_TOKEN = "123456789:" + ("A" * 35)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _exploding_env_reader(name):
    raise AssertionError(
        "env_reader must NOT be called in dry-run mode (read %r)" % name)


def _exploding_transport():
    raise AssertionError("transport must NOT be called when network is forbidden")


def _ok_transport():
    return (True, 200, {"has_id": True, "has_username": True})


def _provider_error_transport():
    return (False, 401, {"has_id": False, "has_username": False})


def _raising_transport():
    raise OSError("simulated network failure")


def _built_plan(**kw):
    params = dict(operator_gate_id=GATE_ID, operator_live_read_only_enabled=True)
    params.update(kw)
    return pilot.build_identity_pilot_request_plan(**params)


def _ok_proof():
    return pilot.hydrate_telegram_credential_handle(
        operator_gate_id=GATE_ID, operator_live_read_only_enabled=True,
        env_reader=lambda name: FAKE_TOKEN)


# --------------------------------------------------------------------------- #
# Request plan
# --------------------------------------------------------------------------- #
def test_plan_built_dry_run_by_default():
    plan = pilot.build_identity_pilot_request_plan(operator_gate_id=GATE_ID)
    assert plan["request_plan_outcome_class"] == pilot.PLAN_BUILT
    assert plan["mode"] == "dry_run_only"
    assert plan["operator_live_read_only_enabled"] is False
    assert plan["token_hydration_declared"] is False
    assert plan["request_budget"] == 1
    assert plan["requested_method"] == "getMe"


def test_plan_live_mode_declares_hydration():
    plan = _built_plan()
    assert plan["request_plan_outcome_class"] == pilot.PLAN_BUILT
    assert plan["mode"] == "live_read_only"
    assert plan["token_hydration_declared"] is True


def test_plan_blocks_missing_operator_gate_id():
    plan = pilot.build_identity_pilot_request_plan(operator_gate_id="")
    assert plan["request_plan_outcome_class"] == pilot.PLAN_BLOCKED
    assert pilot.BLOCK_OPERATOR_GATE_ID_MISSING in plan["blocked_reasons"]


def test_plan_blocks_sendmessage_method():
    plan = pilot.build_identity_pilot_request_plan(
        operator_gate_id=GATE_ID, requested_method="sendMessage")
    assert plan["request_plan_outcome_class"] == pilot.PLAN_BLOCKED
    assert pilot.BLOCK_FORBIDDEN_METHOD_REQUESTED in plan["blocked_reasons"]
    assert pilot.BLOCK_METHOD_NOT_GET_ME in plan["blocked_reasons"]


@pytest.mark.parametrize("method", ["getUpdates", "setWebhook"])
def test_plan_blocks_inbound_methods(method):
    plan = pilot.build_identity_pilot_request_plan(
        operator_gate_id=GATE_ID, requested_method=method)
    assert plan["request_plan_outcome_class"] == pilot.PLAN_BLOCKED
    assert pilot.BLOCK_FORBIDDEN_METHOD_REQUESTED in plan["blocked_reasons"]


def test_plan_blocks_wrong_host():
    plan = pilot.build_identity_pilot_request_plan(
        operator_gate_id=GATE_ID, requested_host="https://evil.example.com")
    assert pilot.BLOCK_HOST_NOT_ALLOWED in plan["blocked_reasons"]


def test_plan_blocks_budget_greater_than_one():
    plan = pilot.build_identity_pilot_request_plan(
        operator_gate_id=GATE_ID, request_budget=2)
    assert pilot.BLOCK_BUDGET_NOT_ONE in plan["blocked_reasons"]


@pytest.mark.parametrize("timeout", [0, -1, 31, 9.5, "10"])
def test_plan_blocks_invalid_timeout(timeout):
    plan = pilot.build_identity_pilot_request_plan(
        operator_gate_id=GATE_ID, timeout_seconds=timeout)
    assert pilot.BLOCK_TIMEOUT_INVALID in plan["blocked_reasons"]


def test_plan_blocks_retry_scheduler_webhook_polling():
    plan = pilot.build_identity_pilot_request_plan(
        operator_gate_id=GATE_ID, auto_retry=True, scheduler=True,
        webhook=True, polling=True)
    for reason in (pilot.BLOCK_RETRY_REQUESTED, pilot.BLOCK_SCHEDULER_REQUESTED,
                   pilot.BLOCK_WEBHOOK_REQUESTED, pilot.BLOCK_POLLING_REQUESTED):
        assert reason in plan["blocked_reasons"]


# --------------------------------------------------------------------------- #
# Credential hydration boundary
# --------------------------------------------------------------------------- #
def test_hydration_dry_run_does_not_read_env():
    proof = pilot.hydrate_telegram_credential_handle(
        operator_gate_id=GATE_ID, operator_live_read_only_enabled=False,
        env_reader=_exploding_env_reader)
    assert proof["credential_proof_outcome_class"] == \
        pilot.CREDENTIAL_PROOF_NOT_HYDRATED
    assert proof["env_read_performed"] is False
    assert proof["credential_hydrated"] is False
    assert pilot.BLOCK_LIVE_NOT_ENABLED in proof["blocked_reasons"]


def test_hydration_blocks_missing_gate_id_without_env_read():
    proof = pilot.hydrate_telegram_credential_handle(
        operator_gate_id="", operator_live_read_only_enabled=True,
        env_reader=_exploding_env_reader)
    assert proof["credential_proof_outcome_class"] == \
        pilot.CREDENTIAL_PROOF_BLOCKED
    assert pilot.BLOCK_OPERATOR_GATE_ID_MISSING in proof["blocked_reasons"]


def test_hydration_reads_only_the_one_allowed_var():
    seen = []

    def reader(name):
        seen.append(name)
        return FAKE_TOKEN

    proof = pilot.hydrate_telegram_credential_handle(
        operator_gate_id=GATE_ID, operator_live_read_only_enabled=True,
        env_reader=reader)
    assert seen == [pilot.ALLOWED_ENV_VAR]
    assert proof["credential_proof_outcome_class"] == pilot.CREDENTIAL_PROOF_OK
    assert proof["only_one_env_var_read"] is True


def test_hydration_missing_var_blocks_credential_missing():
    proof = pilot.hydrate_telegram_credential_handle(
        operator_gate_id=GATE_ID, operator_live_read_only_enabled=True,
        env_reader=lambda name: None)
    assert proof["credential_proof_outcome_class"] == \
        pilot.CREDENTIAL_PROOF_BLOCKED
    assert pilot.BLOCK_CREDENTIAL_MISSING in proof["blocked_reasons"]


def test_hydration_suspicious_shape_blocks_with_redacted_reason():
    proof = pilot.hydrate_telegram_credential_handle(
        operator_gate_id=GATE_ID, operator_live_read_only_enabled=True,
        env_reader=lambda name: "not-a-real-token")
    assert proof["credential_proof_outcome_class"] == \
        pilot.CREDENTIAL_PROOF_BLOCKED
    assert pilot.BLOCK_CREDENTIAL_SUSPICIOUS_SHAPE in proof["blocked_reasons"]
    # The suspicious value must NOT appear anywhere in the proof.
    assert "not-a-real-token" not in pilot.serialize(proof)


def test_hydration_never_returns_or_persists_token():
    proof = _ok_proof()
    blob = pilot.serialize(proof)
    assert FAKE_TOKEN not in blob
    assert proof["token_returned"] is False
    assert proof["token_logged"] is False
    assert proof["token_persisted"] is False
    # Only a fingerprint handle + length class survive.
    assert proof["credential_handle_id"] \
        and len(proof["credential_handle_id"]) == 16
    assert proof["token_length_class"].startswith("len_class_")
    assert proof["reads_dotenv_file"] is False
    assert proof["scans_arbitrary_env"] is False


# --------------------------------------------------------------------------- #
# Execution: dry-run default
# --------------------------------------------------------------------------- #
def test_execute_dry_run_does_no_network():
    plan = pilot.build_identity_pilot_request_plan(operator_gate_id=GATE_ID)
    proof = pilot.hydrate_telegram_credential_handle(operator_gate_id=GATE_ID)
    result = pilot.execute_read_only_identity_pilot(
        plan, proof, operator_live_read_only_enabled=False,
        http_transport=_exploding_transport)
    assert result["identity_proof_outcome_class"] == pilot.PILOT_NOT_RUN_DRY_RUN
    assert result["network_performed"] is False
    assert result["read_only_request_performed"] is False
    assert result["identity_pilot_not_run"] is True


def test_execute_live_blocks_when_plan_not_built():
    bad_plan = pilot.build_identity_pilot_request_plan(
        operator_gate_id=GATE_ID, request_budget=5)
    proof = _ok_proof()
    result = pilot.execute_read_only_identity_pilot(
        bad_plan, proof, operator_live_read_only_enabled=True,
        http_transport=_exploding_transport)
    assert result["identity_proof_outcome_class"] == pilot.PILOT_BLOCKED
    assert pilot.BLOCK_PLAN_NOT_BUILT in result["blocked_reasons"]
    assert result["network_performed"] is False


def test_execute_live_blocks_when_credential_not_ok():
    plan = _built_plan()
    bad_proof = pilot.hydrate_telegram_credential_handle(
        operator_gate_id=GATE_ID, operator_live_read_only_enabled=True,
        env_reader=lambda name: None)
    result = pilot.execute_read_only_identity_pilot(
        plan, bad_proof, operator_live_read_only_enabled=True,
        http_transport=_exploding_transport)
    assert result["identity_proof_outcome_class"] == pilot.PILOT_BLOCKED
    assert pilot.BLOCK_CREDENTIAL_PROOF_NOT_OK in result["blocked_reasons"]
    assert result["network_performed"] is False


# --------------------------------------------------------------------------- #
# Execution: mocked live getMe
# --------------------------------------------------------------------------- #
def test_execute_live_success_redacted_proof():
    plan = _built_plan()
    proof = _ok_proof()
    result = pilot.execute_read_only_identity_pilot(
        plan, proof, operator_live_read_only_enabled=True,
        http_transport=_ok_transport)
    assert result["identity_proof_outcome_class"] == pilot.PILOT_OK
    assert result["getme_ok"] is True
    assert result["network_performed"] is True
    assert result["read_only_request_performed"] is True
    assert result["response_status_class"] == pilot.RESPONSE_STATUS_OK_CLASS
    assert result["bot_identity_redacted_class"] == \
        pilot.BOT_IDENTITY_PRESENT_CLASS
    assert result["bot_username_redacted_class"] == \
        pilot.BOT_USERNAME_PRESENT_CLASS
    # No raw response material is stored.
    assert result["stores_raw_response_body"] is False
    assert result["stores_raw_bot_id"] is False
    assert result["stores_raw_username"] is False


def test_execute_live_provider_error_redacted_proof():
    plan = _built_plan()
    proof = _ok_proof()
    result = pilot.execute_read_only_identity_pilot(
        plan, proof, operator_live_read_only_enabled=True,
        http_transport=_provider_error_transport)
    assert result["identity_proof_outcome_class"] == pilot.PILOT_PROVIDER_ERROR
    assert result["getme_ok"] is False
    assert result["network_performed"] is True
    assert result["response_status_class"] == pilot.RESPONSE_STATUS_ERROR_CLASS
    assert result["provider_status_code_class"] == \
        pilot.PROVIDER_CODE_CLIENT_ERROR_CLASS


def test_execute_live_network_exception_fails_closed():
    plan = _built_plan()
    proof = _ok_proof()
    result = pilot.execute_read_only_identity_pilot(
        plan, proof, operator_live_read_only_enabled=True,
        http_transport=_raising_transport)
    assert result["identity_proof_outcome_class"] == pilot.PILOT_NETWORK_BLOCKED
    assert result["getme_ok"] is False
    assert result["read_only_request_performed"] is True
    assert result["response_status_class"] == pilot.RESPONSE_STATUS_ERROR_CLASS


def test_execute_performs_exactly_one_request():
    plan = _built_plan()
    proof = _ok_proof()
    calls = {"n": 0}

    def counting_transport():
        calls["n"] += 1
        return (True, 200, {"has_id": True, "has_username": True})

    pilot.execute_read_only_identity_pilot(
        plan, proof, operator_live_read_only_enabled=True,
        http_transport=counting_transport)
    assert calls["n"] == 1


# --------------------------------------------------------------------------- #
# Identity proof + audit redaction
# --------------------------------------------------------------------------- #
def test_identity_proof_is_leak_free():
    plan = _built_plan()
    proof = _ok_proof()
    result = pilot.execute_read_only_identity_pilot(
        plan, proof, operator_live_read_only_enabled=True,
        http_transport=_ok_transport)
    assert pilot.scan_for_leaks(result) == []
    assert FAKE_TOKEN not in pilot.serialize(result)


def test_audit_packet_stores_no_secrets():
    plan = _built_plan()
    proof = _ok_proof()
    identity = pilot.execute_read_only_identity_pilot(
        plan, proof, operator_live_read_only_enabled=True,
        http_transport=_ok_transport)
    audit = pilot.build_identity_pilot_audit_packet(
        plan, proof, identity, budget_used=1)
    assert audit["audit_outcome_class"] == pilot.AUDIT_RECORDED
    assert audit["stores_token"] is False
    assert audit["stores_raw_response"] is False
    assert audit["stores_raw_url"] is False
    assert audit["stores_headers"] is False
    assert audit["stores_cookies"] is False
    assert audit["budget_used"] == 1
    assert audit["credential_handle_id"] == proof["credential_handle_id"]
    assert audit["request_plan_checksum"] == plan["request_plan_checksum"]
    assert audit["identity_proof_checksum"] == identity["identity_proof_checksum"]
    blob = pilot.serialize(audit)
    assert FAKE_TOKEN not in blob
    assert pilot.scan_for_leaks(audit) == []


def test_no_posting_or_reply_flags_anywhere():
    plan = _built_plan()
    proof = _ok_proof()
    identity = pilot.execute_read_only_identity_pilot(
        plan, proof, operator_live_read_only_enabled=True,
        http_transport=_ok_transport)
    audit = pilot.build_identity_pilot_audit_packet(plan, proof, identity)
    for obj in (plan, proof, identity, audit):
        assert obj["sendmessage_performed"] is False
        assert obj["posting_performed"] is False
        assert obj["autonomous_reply_performed"] is False
        assert obj["scheduler_enabled"] is False
        assert obj["auto_retry_allowed"] is False
        assert obj["webhook_registered"] is False
        assert obj["polling_enabled"] is False
        assert obj["valid_for_live_execution"] is False


# --------------------------------------------------------------------------- #
# Packet + doc determinism + leak-freedom
# --------------------------------------------------------------------------- #
def test_packet_is_deterministic_and_leak_free():
    p1 = pilot.build_packet()
    p2 = pilot.build_packet()
    assert p1 == p2
    assert p1["checksum_sha256"] == p2["checksum_sha256"]
    assert pilot.scan_for_leaks(p1) == []
    assert "sendMessage" in p1["forbidden_methods"]
    assert p1["allowed_method"] == "getMe"
    assert p1["default_mode"] == "dry_run_only"


def test_doc_is_deterministic_and_mentions_no_sendmessage():
    d1 = pilot.build_doc()
    d2 = pilot.build_doc()
    assert d1 == d2
    assert "getMe" in d1
    assert "no_sendmessage_anywhere" in d1


def test_packet_json_roundtrips():
    blob = pilot.serialize(pilot.build_packet())
    loaded = json.loads(blob)
    assert loaded["allowed_env_var_name"] == pilot.ALLOWED_ENV_VAR


# --------------------------------------------------------------------------- #
# Forbidden-value fail-closed
# --------------------------------------------------------------------------- #
def test_execute_fail_closed_on_forbidden_value_in_inputs():
    # A tampered plan carrying a forbidden chat-id-like field must fail closed.
    tampered_plan = dict(_built_plan())
    tampered_plan["chat_id"] = "-1001234567890"
    result = pilot.execute_read_only_identity_pilot(
        tampered_plan, _ok_proof(), operator_live_read_only_enabled=True,
        http_transport=_exploding_transport)
    assert result["identity_proof_outcome_class"] == pilot.PILOT_FAIL_CLOSED
    assert pilot.BLOCK_FORBIDDEN_VALUE in result["blocked_reasons"]
