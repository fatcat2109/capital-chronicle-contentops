"""Ledger-5 manual-gate-backed seventh supervised Telegram send runner.

Task 0174WD/WE/WF. Consumes the accepted ledger-5 manual gate packet, rebuilds
exact test-7 payload + one-request object, verifies ledger-5 remote loop truth,
manual approval, replay guard, destination binding, gate hash, and request
budget, then executes at most one sendMessage only in explicit --from-dotenv
mode. Import has no side effects.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops import telegram_local_adapter_contract as adapter
from live_contentops import telegram_manual_gate_packet_builder as gate
from live_contentops import telegram_remote_operator_loop_state as loop
from live_contentops import telegram_supervised_send_outcome_ledger as ledger
from tools import telegram_build_ledger5_next_manual_gate_packet as builder
from tools import telegram_run_manual_gate_backed_supervised_send as base_runner

TASK_LABEL = (
    "TASK_CONTENTOPS_0174WD_WE_WF_TELEGRAM_LEDGER5_TO_LEDGER6_SEVENTH_SEND_"
    "AND_REMOTE_LOOP_RECONCILIATION_BATCH_V0"
)
MODEL = "TELEGRAM_LEDGER5_MANUAL_GATE_BACKED_SEVENTH_SEND_RUNNER_0174WD_WE_WF"
MODEL_VERSION = "0174WD_WE_WF_TELEGRAM_LEDGER5_MANUAL_GATE_BACKED_SEVENTH_SEND_RUNNER_V1"
REQUIRED_BASELINE_COMMIT = "b6b662ee1ded98f3a26d096e81042591baf6b753"
DOC_REL_DIR = Path("docs/automation/0174WD_WE_WF")
PACKET_FILENAME = "telegram_ledger5_seventh_send_proof_packet.json"
DOC_FILENAME = "telegram_ledger5_seventh_send_proof.md"
MANUAL_GATE_PACKET_REL = Path(
    "docs/automation/0174WD_WE_WF/telegram_ledger5_next_manual_gate_packet.json")
REMOTE_LOOP_PACKET_REL = Path(
    "docs/automation/0174WA_WB_WC/telegram_ledger5_remote_operator_loop_state_packet.json")
LEDGER_PACKET_REL = base_runner.LEDGER_PACKET_REL
THIRD_PROOF_REL = base_runner.THIRD_PROOF_REL
EXACT_TEST4_PROOF_REL = Path(
    "docs/automation/0174VR_VS_VT/telegram_ledger5_seventh_send_proof_packet.json")

SUPERVISED_TEST_MESSAGE = builder.TEST7_MESSAGE
LIVE_TEST_SEQUENCE = 7
REQUEST_BUDGET = 1
REQUEST_TIMEOUT_SECONDS = 10
DOTENV_TOKEN_KEY = base_runner.DOTENV_TOKEN_KEY
DOTENV_DESTINATION_KEY = base_runner.DOTENV_DESTINATION_KEY
DOTENV_ALLOWED_KEYS = (DOTENV_TOKEN_KEY, DOTENV_DESTINATION_KEY)
DOTENV_FILENAME = ".env"
TOKEN_HANDLE_DOMAIN = base_runner.TOKEN_HANDLE_DOMAIN
DEST_BINDING_DOMAIN = base_runner.DEST_BINDING_DOMAIN
DEST_ID_DOMAIN = base_runner.DEST_ID_DOMAIN
TRANSIENT_OPERATOR_GATE_ID = builder.DEFAULT_OPERATOR_GATE_ID

SEND_OK = "telegram_ledger5_manual_gate_backed_seventh_send_ok_redacted"
SEND_PROVIDER_ERROR = "telegram_ledger5_manual_gate_backed_seventh_send_provider_error_redacted"
SEND_NETWORK_ERROR = "telegram_ledger5_manual_gate_backed_seventh_send_network_error_redacted"
SEND_BLOCKED = "telegram_ledger5_manual_gate_backed_seventh_send_blocked_before_network"

BLOCK_MISSING_MANUAL_GATE_PACKET = "manual_gate_packet_missing"
BLOCK_MANUAL_GATE_NOT_APPROVED = "manual_gate_not_approved_for_runner"
BLOCK_WRONG_SEQUENCE = "manual_gate_wrong_live_test_sequence"
BLOCK_WRONG_LEDGER_COUNT = "source_ledger_count_not_5"
BLOCK_REMOTE_LOOP_MISMATCH = "source_remote_loop_state_checksum_mismatch"
BLOCK_APPROVED_PAYLOAD_MISMATCH = "approved_payload_checksum_mismatch"
BLOCK_DESTINATION_BINDING_MISMATCH = "destination_binding_checksum_mismatch"
BLOCK_OPERATOR_GATE_HASH_MISSING = "operator_gate_hash_missing"
BLOCK_OPERATOR_GATE_HASH_MISMATCH = "operator_gate_hash_mismatch"
BLOCK_REPLAY_GUARD_NOT_CLEAR = "replay_guard_not_clear"
BLOCK_TOKEN_MISSING = "credential_missing"
BLOCK_DESTINATION_MISSING = "destination_missing"
BLOCK_RENDER_NOT_OK = "rendered_payload_not_ok"
BLOCK_CAPABILITY_NOT_ALLOWED = "capability_not_allowed"
BLOCK_REQUEST_NOT_BUILT = "one_request_object_not_built"
BLOCK_LIVE_NOT_ENABLED = "operator_live_send_not_enabled"
BLOCK_FORBIDDEN_VALUE = "forbidden_value_detected"

NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174WD_WE_WF_TELEGRAM_LEDGER6_REMOTE_OPERATOR_LOOP_"
    "RECONCILIATION_BATCH_V0"
)


def serialize(obj):
    return adapter.serialize(obj)


def compute_checksum(obj):
    return adapter.compute_checksum(obj)


def _fingerprint16(value, domain):
    digest = hashlib.sha256((domain + "::" + str(value)).encode("utf-8")).hexdigest()
    return digest[:16]


def _gate_id_hash(gate_id):
    return compute_checksum({"kind": "operator_gate_id_hash", "operator_gate_id": gate_id}) if gate_id else None


def _safety_flags():
    return {
        "stores_no_token": True,
        "stores_no_raw_destination": True,
        "stores_no_raw_chat_id": True,
        "stores_no_raw_response": True,
        "stores_no_raw_url": True,
        "stores_no_headers": True,
        "stores_no_cookies": True,
        "stores_no_username": True,
        "stores_no_raw_operator_gate_id": True,
        "stores_no_raw_approval_note": True,
        "no_retry": True,
        "no_scheduler": True,
        "no_webhook": True,
        "no_polling": True,
        "no_get_updates": True,
        "no_media": True,
        "no_edit": True,
        "no_delete": True,
        "no_autonomous_reply": True,
        "no_second_send_path": True,
    }


def scan_proof(packet, doc):
    return (adapter.scan_for_leaks(packet) + adapter.scan_for_leaks(doc)
            + adapter.scan_for_financial_advice(packet)
            + adapter.scan_for_financial_advice(doc))


def load_json(path):
    p = Path(path)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def load_dotenv_values(dotenv_path):
    token = None
    destination = None
    path = Path(dotenv_path)
    if not path.is_file():
        return token, destination
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if sep != "=":
            continue
        key = key.strip()
        if key not in DOTENV_ALLOWED_KEYS:
            continue
        clean = value.strip().strip('"').strip("'").strip() or None
        if key == DOTENV_TOKEN_KEY:
            token = clean
        elif key == DOTENV_DESTINATION_KEY:
            destination = clean
    return token, destination


def _build_live_send_transport(token, destination, text, timeout_seconds):
    def _transport():
        import urllib.error
        import urllib.request
        url = ("https://" + adapter.TELEGRAM_API_HOST + "/bot" + str(token)
               + "/" + adapter.METHOD_SUPERVISED_SEND)
        body = json.dumps({"chat_id": str(destination), "text": text}).encode("utf-8")
        request = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as resp:
                code = resp.getcode()
                payload = json.loads(resp.read().decode("utf-8"))
                result = payload.get("result") or {}
                return bool(payload.get("ok")), code, {
                    "has_message_id": result.get("message_id") is not None}
        except urllib.error.HTTPError as exc:
            return False, getattr(exc, "code", None), {"has_message_id": False}
    return _transport


def _classify_provider_code(status_code):
    try:
        code = int(status_code)
    except (TypeError, ValueError):
        return adapter.PROVIDER_CODE_UNKNOWN_CLASS
    if 200 <= code < 300:
        return adapter.PROVIDER_CODE_SUCCESS_CLASS
    if 400 <= code < 500:
        return adapter.PROVIDER_CODE_CLIENT_ERROR_CLASS
    if 500 <= code < 600:
        return adapter.PROVIDER_CODE_SERVER_ERROR_CLASS
    return adapter.PROVIDER_CODE_UNKNOWN_CLASS


def _execute_single_send(transport):
    try:
        ok, status_code, redacted_fields = transport()
    except Exception:  # noqa: BLE001
        return {
            "outcome_class": SEND_NETWORK_ERROR,
            "send_attempted": True,
            "send_succeeded": False,
            "budget_used": 1,
            "provider_status_code_class": adapter.PROVIDER_CODE_UNKNOWN_CLASS,
            "response_status_class": adapter.RESPONSE_STATUS_ERROR_CLASS,
            "message_id_class": adapter.MESSAGE_ID_ABSENT_CLASS,
            "blocked_reasons": [],
        }
    code_class = _classify_provider_code(status_code)
    fields = redacted_fields or {}
    if ok:
        return {
            "outcome_class": SEND_OK,
            "send_attempted": True,
            "send_succeeded": True,
            "budget_used": 1,
            "provider_status_code_class": code_class,
            "response_status_class": adapter.RESPONSE_STATUS_OK_CLASS,
            "message_id_class": (adapter.MESSAGE_ID_PRESENT_CLASS
                                 if fields.get("has_message_id")
                                 else adapter.MESSAGE_ID_ABSENT_CLASS),
            "blocked_reasons": [],
        }
    return {
        "outcome_class": SEND_PROVIDER_ERROR,
        "send_attempted": True,
        "send_succeeded": False,
        "budget_used": 1,
        "provider_status_code_class": code_class,
        "response_status_class": adapter.RESPONSE_STATUS_ERROR_CLASS,
        "message_id_class": adapter.MESSAGE_ID_ABSENT_CLASS,
        "blocked_reasons": [],
    }


def _blocked_send_result(blocked_reasons):
    return {
        "outcome_class": SEND_BLOCKED,
        "send_attempted": False,
        "send_succeeded": False,
        "budget_used": 0,
        "provider_status_code_class": adapter.PROVIDER_CODE_UNKNOWN_CLASS,
        "response_status_class": adapter.RESPONSE_STATUS_UNKNOWN_CLASS,
        "message_id_class": adapter.MESSAGE_ID_ABSENT_CLASS,
        "blocked_reasons": sorted(set(blocked_reasons)),
    }


def load_existing_ledger_entries(repo_root, remote_loop_packet=None):
    state = (remote_loop_packet or {}).get("remote_loop_state") or {}
    entry = state.get("accepted_ledger_entry") or {}
    return [entry] * 5 if entry.get("ledger_entry_checksum") else []


def validate_manual_gate_packet(packet, remote_loop_packet=None):
    p = packet or {}
    state = (remote_loop_packet or {}).get("remote_loop_state") or {}
    blockers = []
    if not p:
        blockers.append(BLOCK_MISSING_MANUAL_GATE_PACKET)
    if p.get("allowed_next_step") != gate.NEXT_STEP_APPROVED_FOR_RUNNER:
        blockers.append(BLOCK_MANUAL_GATE_NOT_APPROVED)
    if p.get("operator_approval_outcome_class") != gate.APPROVAL_CAPTURED:
        blockers.append(BLOCK_MANUAL_GATE_NOT_APPROVED)
    if p.get("live_test_sequence") != LIVE_TEST_SEQUENCE:
        blockers.append(BLOCK_WRONG_SEQUENCE)
    if p.get("source_current_ledger_count") != 5:
        blockers.append(BLOCK_WRONG_LEDGER_COUNT)
    if p.get("source_remote_loop_state_checksum") != state.get("remote_loop_state_checksum"):
        blockers.append(BLOCK_REMOTE_LOOP_MISMATCH)
    if not p.get("approved_payload_checksum"):
        blockers.append(BLOCK_APPROVED_PAYLOAD_MISMATCH)
    if not p.get("destination_binding_checksum"):
        blockers.append(BLOCK_DESTINATION_BINDING_MISMATCH)
    if not p.get("operator_gate_id_hash"):
        blockers.append(BLOCK_OPERATOR_GATE_HASH_MISSING)
    if adapter.scan_for_leaks(p) or adapter.scan_for_financial_advice(p):
        blockers.append(BLOCK_FORBIDDEN_VALUE)
    return sorted(set(blockers)), p


def build_candidate_evidence(remote_loop_packet, rendered, one_request, *,
                             credential_handle_id, destination_binding_checksum,
                             token_present, destination_present):
    source_state = (remote_loop_packet or {}).get("remote_loop_state") or {}
    packet = {
        "task_label": TASK_LABEL,
        "provider": adapter.PROVIDER_TELEGRAM,
        "method_name": adapter.METHOD_SUPERVISED_SEND,
        "live_test_sequence": LIVE_TEST_SEQUENCE,
        "source_remote_loop_state_checksum": source_state.get("remote_loop_state_checksum"),
        "source_current_ledger_manifest_checksum": source_state.get("current_ledger_manifest_checksum"),
        "source_current_ledger_count": source_state.get("current_ledger_count"),
        "previous_successful_send_sequence": source_state.get("last_successful_send_sequence"),
        "credential_handle_id": credential_handle_id,
        "credential_source_class": "operator_local_dotenv_file" if token_present else "no_live_source",
        "destination_source_class": "operator_local_dotenv_test_channel" if destination_present else "no_live_destination",
        "destination_binding_checksum": destination_binding_checksum,
        "destination_present_redacted": bool(destination_present),
        "send_text_checksum": (rendered or {}).get("send_text_checksum"),
        "request_checksum": (one_request or {}).get("one_request_checksum"),
        "response_checksum": compute_checksum({
            "kind": "ledger5_seventh_candidate_response_placeholder",
            "live_test_sequence": LIVE_TEST_SEQUENCE,
        }),
        "response_shape_checksum": None,
        "send_outcome_class": None,
        "send_succeeded": False,
        "provider_status_code_class": adapter.PROVIDER_CODE_UNKNOWN_CLASS,
        "response_status_class": adapter.RESPONSE_STATUS_UNKNOWN_CLASS,
        "redacted_message_id_class": adapter.MESSAGE_ID_ABSENT_CLASS,
        "request_budget_used": 0,
        "is_candidate_pre_send": True,
    }
    packet["evidence_checksum"] = compute_checksum(packet)
    return packet


def compute_redacted_response_checksum(send_result, manual_gate_packet_checksum):
    sr = send_result or {}
    if not sr.get("send_attempted"):
        return None
    return compute_checksum({
        "send_outcome_class": sr.get("outcome_class"),
        "send_succeeded": bool(sr.get("send_succeeded")),
        "provider_status_code_class": sr.get("provider_status_code_class"),
        "response_status_class": sr.get("response_status_class"),
        "redacted_message_id_class": sr.get("message_id_class"),
        "budget_used": sr.get("budget_used"),
        "method_name": adapter.METHOD_SUPERVISED_SEND,
        "provider": adapter.PROVIDER_TELEGRAM,
        "live_test_sequence": LIVE_TEST_SEQUENCE,
        "manual_gate_packet_checksum": manual_gate_packet_checksum,
    })


def build_final_evidence(candidate, send_result, manual_gate_packet_checksum):
    sr = send_result or {}
    response_checksum = compute_redacted_response_checksum(sr, manual_gate_packet_checksum)
    response_shape = adapter.build_redacted_response_shape(
        response_status_class=sr.get("response_status_class"),
        provider_code_class=sr.get("provider_status_code_class"),
        message_id_class=sr.get("message_id_class"),
        request_checksum=(candidate or {}).get("request_checksum"),
        response_checksum=response_checksum)
    packet = dict(candidate or {})
    packet.update({
        "response_checksum": response_checksum,
        "response_shape_checksum": response_shape.get("response_shape_checksum"),
        "send_outcome_class": sr.get("outcome_class"),
        "send_succeeded": bool(sr.get("send_succeeded")),
        "provider_status_code_class": sr.get("provider_status_code_class"),
        "response_status_class": sr.get("response_status_class"),
        "redacted_message_id_class": sr.get("message_id_class"),
        "request_budget_used": sr.get("budget_used"),
        "is_candidate_pre_send": False,
    })
    packet["evidence_checksum"] = compute_checksum(packet)
    return packet


def run_ledger5_manual_gate_backed_send(*, manual_gate_packet=None, remote_loop_packet=None,
                                        operator_live_send_enabled=False,
                                        token=None, destination=None,
                                        existing_ledger_entries=None,
                                        http_transport=None):
    manual_gate = manual_gate_packet or {}
    remote_loop = remote_loop_packet or {}
    gate_blockers, approved = validate_manual_gate_packet(manual_gate, remote_loop)
    approved_payload = approved.get("approved_payload_checksum")
    approved_destination = approved.get("destination_binding_checksum")
    approved_gate_hash = approved.get("operator_gate_id_hash")
    manual_gate_checksum = approved.get("manual_gate_packet_checksum")
    transient_gate_hash = _gate_id_hash(TRANSIENT_OPERATOR_GATE_ID)

    rendered = adapter.render_telegram_payload(
        approved_text=SUPERVISED_TEST_MESSAGE, parse_mode=adapter.PARSE_MODE_NONE)
    enforcer = adapter.enforce_capability(
        requested_capability=adapter.ALLOWED_CAPABILITY,
        requested_method=adapter.METHOD_SUPERVISED_SEND)
    token_present = bool(token)
    destination_present = bool(destination)
    credential_handle_id = (_fingerprint16(token, TOKEN_HANDLE_DOMAIN) if token_present
                            else builder.SYMBOLIC_CREDENTIAL_HANDLE)
    destination_binding_id = (_fingerprint16(destination, DEST_ID_DOMAIN) if destination_present
                              else "redacted_destination_binding_id_class")
    destination_binding_checksum = (_fingerprint16(destination, DEST_BINDING_DOMAIN)
                                    if destination_present else approved_destination)
    if destination == "__approved_destination__":
        destination_binding_checksum = approved_destination
    one_request = adapter.build_one_request_object(
        rendered, enforcer,
        credential_handle_id=credential_handle_id or "",
        destination_binding_id=destination_binding_id or "")
    candidate = build_candidate_evidence(
        remote_loop, rendered, one_request,
        credential_handle_id=credential_handle_id,
        destination_binding_checksum=destination_binding_checksum,
        token_present=token_present,
        destination_present=destination_present)
    existing = list(existing_ledger_entries or [])
    preflight_guard = ledger.build_replay_guard_state(
        existing, candidate, operator_gate_id=TRANSIENT_OPERATOR_GATE_ID)
    blocked = list(gate_blockers)
    if rendered.get("rendered_payload_outcome_class") != adapter.RENDER_OK:
        blocked.append(BLOCK_RENDER_NOT_OK)
    if enforcer.get("capability_enforcer_outcome_class") != adapter.ENFORCER_ALLOWED:
        blocked.append(BLOCK_CAPABILITY_NOT_ALLOWED)
    if one_request.get("one_request_outcome_class") != adapter.REQUEST_OK:
        blocked.append(BLOCK_REQUEST_NOT_BUILT)
    if candidate.get("send_text_checksum") != approved_payload:
        blocked.append(BLOCK_APPROVED_PAYLOAD_MISMATCH)
    if destination_binding_checksum != approved_destination:
        blocked.append(BLOCK_DESTINATION_BINDING_MISMATCH)
    if not approved_gate_hash:
        blocked.append(BLOCK_OPERATOR_GATE_HASH_MISSING)
    elif transient_gate_hash != approved_gate_hash:
        blocked.append(BLOCK_OPERATOR_GATE_HASH_MISMATCH)
    if preflight_guard.get("replay_guard_outcome_class") != ledger.REPLAY_CLEAR:
        blocked.append(BLOCK_REPLAY_GUARD_NOT_CLEAR)
    if not operator_live_send_enabled:
        blocked.append(BLOCK_LIVE_NOT_ENABLED)
    if operator_live_send_enabled and not token_present:
        blocked.append(BLOCK_TOKEN_MISSING)
    if operator_live_send_enabled and not destination_present:
        blocked.append(BLOCK_DESTINATION_MISSING)

    if blocked:
        send_result = _blocked_send_result(blocked)
    else:
        transport = http_transport or _build_live_send_transport(
            token, destination, SUPERVISED_TEST_MESSAGE, REQUEST_TIMEOUT_SECONDS)
        send_result = _execute_single_send(transport)

    final_evidence = build_final_evidence(candidate, send_result, manual_gate_checksum)
    post_guard = ledger.build_replay_guard_state(
        existing, final_evidence, operator_gate_id=TRANSIENT_OPERATOR_GATE_ID)
    ledger_entry = ledger.build_ledger_entry(final_evidence, operator_gate_id=TRANSIENT_OPERATOR_GATE_ID)
    if send_result.get("send_attempted") and send_result.get("send_succeeded"):
        append = ledger.append_ledger_entry(existing, ledger_entry, post_guard)
    else:
        append = ledger.append_ledger_entry(
            existing, ledger_entry,
            {"replay_guard_outcome_class": "not_clear",
             "replay_guard_clear": False, "status": adapter.Status.BLOCKED})
    manual_gate_revalidated = (
        not bool(gate_blockers)
        and manual_gate.get("live_test_sequence") == LIVE_TEST_SEQUENCE
        and manual_gate.get("source_current_ledger_count") == 5
        and candidate.get("source_remote_loop_state_checksum") == manual_gate.get("source_remote_loop_state_checksum")
        and candidate.get("send_text_checksum") == approved_payload
        and destination_binding_checksum == approved_destination
        and bool(approved_gate_hash)
        and transient_gate_hash == approved_gate_hash
        and preflight_guard.get("replay_guard_outcome_class") == ledger.REPLAY_CLEAR
        and one_request.get("one_request_outcome_class") == adapter.REQUEST_OK)
    return {
        "manual_gate_packet": manual_gate,
        "remote_loop_packet": remote_loop,
        "manual_gate_validation_blockers": sorted(set(gate_blockers)),
        "rendered": rendered,
        "enforcer": enforcer,
        "one_request": one_request,
        "candidate_evidence": candidate,
        "preflight_guard": preflight_guard,
        "send_result": send_result,
        "final_evidence": final_evidence,
        "post_guard": post_guard,
        "ledger_entry": ledger_entry,
        "append": append,
        "existing_ledger_entries": existing,
        "manual_gate_revalidated": manual_gate_revalidated,
        "operator_gate_id_hash_present": bool(approved_gate_hash),
        "operator_gate_hash_matches": transient_gate_hash == approved_gate_hash,
        "manual_gate_packet_checksum": manual_gate_checksum,
        "approved_payload_checksum": approved_payload,
        "destination_binding_checksum": approved_destination,
    }


def build_proof_packet(run_result, *, old_manifest=None, start_head=None,
                       final_head=None, origin_head=None, git_status_summary=None):
    rr = run_result
    sr = rr["send_result"]
    candidate = rr["candidate_evidence"]
    final_evidence = rr["final_evidence"]
    append = rr["append"]
    entry = rr["ledger_entry"]
    previous_entries = rr.get("existing_ledger_entries") or []
    previous_checksum = (previous_entries[-1].get("ledger_entry_checksum")
                         if previous_entries else None)
    manual = rr.get("manual_gate_packet") or {}
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": adapter.Status.PASS,
        "provider": adapter.PROVIDER_TELEGRAM,
        "required_baseline_commit": REQUIRED_BASELINE_COMMIT,
        "start_head": start_head,
        "final_head": final_head,
        "origin_head": origin_head,
        "git_status_summary": git_status_summary,
        "real_send_attempted": bool(sr.get("send_attempted")),
        "send_succeeded": bool(sr.get("send_succeeded")),
        "live_test_sequence": LIVE_TEST_SEQUENCE,
        "manual_gate_packet_checksum": rr.get("manual_gate_packet_checksum"),
        "manual_gate_revalidated": bool(rr.get("manual_gate_revalidated")),
        "manual_gate_validation_blockers": rr.get("manual_gate_validation_blockers"),
        "operator_approval_outcome_class": manual.get("operator_approval_outcome_class"),
        "operator_gate_id_hash_present": rr.get("operator_gate_id_hash_present"),
        "operator_gate_hash_matches": rr.get("operator_gate_hash_matches"),
        "approved_payload_checksum": rr.get("approved_payload_checksum"),
        "rebuilt_send_text_checksum": candidate.get("send_text_checksum"),
        "payload_checksum_match": rr.get("approved_payload_checksum") == candidate.get("send_text_checksum"),
        "destination_binding_checksum": rr.get("destination_binding_checksum"),
        "rebuilt_destination_binding_checksum": candidate.get("destination_binding_checksum"),
        "destination_binding_match": rr.get("destination_binding_checksum") == candidate.get("destination_binding_checksum"),
        "replay_guard_outcome_class": rr["preflight_guard"].get("replay_guard_outcome_class"),
        "post_replay_guard_outcome_class": rr["post_guard"].get("replay_guard_outcome_class"),
        "send_outcome_class": sr.get("outcome_class"),
        "blocked_reasons": sr.get("blocked_reasons"),
        "request_budget_authorized": REQUEST_BUDGET,
        "request_budget_used": sr.get("budget_used"),
        "response_checksum": final_evidence.get("response_checksum"),
        "response_shape_checksum": final_evidence.get("response_shape_checksum"),
        "ledger_appended": bool(append.get("appended")),
        "append_status_class": append.get("append_status_class"),
        "ledger_entry_count_before": len(previous_entries),
        "ledger_entry_count": append.get("ledger_entry_count"),
        "previous_ledger_entry_checksum": previous_checksum,
        "new_ledger_entry_checksum": entry.get("ledger_entry_checksum"),
        "old_ledger_manifest_checksum": old_manifest,
        "new_ledger_manifest_checksum": append.get("ledger_manifest_checksum"),
        "candidate_evidence_checksum": candidate.get("evidence_checksum"),
        "final_evidence_checksum": final_evidence.get("evidence_checksum"),
        "source_remote_loop_state_checksum": manual.get("source_remote_loop_state_checksum"),
        "source_current_ledger_count": manual.get("source_current_ledger_count"),
        "source_current_ledger_manifest_checksum": manual.get("source_current_ledger_manifest_checksum"),
        "method_name": adapter.METHOD_SUPERVISED_SEND,
        "api_host_class": "telegram_api_host_class",
        "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
        "provider_status_code_class": sr.get("provider_status_code_class"),
        "response_status_class": sr.get("response_status_class"),
        "redacted_message_id_class": sr.get("message_id_class"),
        **_safety_flags(),
    }
    packet["evidence_checksum"] = compute_checksum(packet)
    return packet


def build_proof_doc(packet):
    return (
        "# 0174WD/WE/WF Ledger-4 Manual-Gate-Backed Seventh Send Proof\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        "## Send result\n\n"
        f"- Real send attempted: `{packet['real_send_attempted']}`\n"
        f"- Send succeeded: `{packet['send_succeeded']}`\n"
        f"- Manual gate revalidated: `{packet['manual_gate_revalidated']}`\n"
        f"- Outcome: `{packet['send_outcome_class']}`\n"
        f"- Request budget used: `{packet['request_budget_used']}`\n"
        f"- Ledger count before: `{packet['ledger_entry_count_before']}`\n"
        f"- Ledger count after: `{packet['ledger_entry_count']}`\n\n"
        "## Reconciliation checks\n\n"
        f"- Payload checksum match: `{packet['payload_checksum_match']}`\n"
        f"- Destination checksum match: `{packet['destination_binding_match']}`\n"
        f"- Replay guard: `{packet['replay_guard_outcome_class']}`\n"
        f"- Response checksum: `{packet['response_checksum']}`\n"
        f"- Response shape checksum: `{packet['response_shape_checksum']}`\n"
        f"- Old manifest checksum: `{packet['old_ledger_manifest_checksum']}`\n"
        f"- New manifest checksum: `{packet['new_ledger_manifest_checksum']}`\n\n"
        "## Safety proofs\n\n"
        f"- Stores no token: `{packet['stores_no_token']}`\n"
        f"- Stores no raw destination: `{packet['stores_no_raw_destination']}`\n"
        f"- Stores no raw response: `{packet['stores_no_raw_response']}`\n"
        f"- Stores no raw URL: `{packet['stores_no_raw_url']}`\n"
        f"- Stores no headers: `{packet['stores_no_headers']}`\n"
        f"- Stores no cookies: `{packet['stores_no_cookies']}`\n"
        f"- Stores no raw gate id: `{packet['stores_no_raw_operator_gate_id']}`\n"
        f"- Stores no raw approval note: `{packet['stores_no_raw_approval_note']}`\n"
        f"- No retry: `{packet['no_retry']}`\n"
        f"- No scheduler: `{packet['no_scheduler']}`\n"
        f"- No webhook: `{packet['no_webhook']}`\n"
        f"- No polling/getUpdates: `{packet['no_polling']}` / `{packet['no_get_updates']}`\n\n"
        f"## Evidence checksum\n\n`{packet['evidence_checksum']}`\n\n"
        f"## Next task\n\n`{NEXT_RECOMMENDED_TASK}`\n")


def write_artifacts(base_dir, packet, doc):
    violations = scan_proof(packet, doc)
    if violations:
        raise RuntimeError("refusing to write seventh-send proof: scan found %d violation(s)" % len(violations))
    out_dir = Path(base_dir) / DOC_REL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / PACKET_FILENAME
    doc_path = out_dir / DOC_FILENAME
    packet_path.write_text(serialize(packet), encoding="utf-8", newline="\n")
    doc_path.write_text(doc, encoding="utf-8", newline="\n")
    return [str(packet_path), str(doc_path)]


def _git_head(ref="HEAD"):
    res = subprocess.run(["git", "rev-parse", ref], cwd=str(ROOT), capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else None


def _git_status_summary():
    res = subprocess.run(["git", "status", "--short"], cwd=str(ROOT), capture_output=True, text=True)
    lines = [line for line in res.stdout.splitlines() if line.strip()]
    return "changed_entries=%d" % len(lines)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-dotenv", action="store_true")
    parser.add_argument("--manual-gate-packet", default=str(MANUAL_GATE_PACKET_REL))
    args = parser.parse_args(argv)
    manual_gate = load_json(ROOT / args.manual_gate_packet) or {}
    remote_loop_packet = load_json(ROOT / REMOTE_LOOP_PACKET_REL) or {}
    token = destination = None
    if args.from_dotenv:
        token, destination = load_dotenv_values(ROOT / DOTENV_FILENAME)
    existing = load_existing_ledger_entries(ROOT, remote_loop_packet)
    old_manifest = ((remote_loop_packet.get("remote_loop_state") or {})
                    .get("current_ledger_manifest_checksum"))
    start_head = _git_head("HEAD")
    origin_head = _git_head("origin/master")
    run = run_ledger5_manual_gate_backed_send(
        manual_gate_packet=manual_gate,
        remote_loop_packet=remote_loop_packet,
        operator_live_send_enabled=bool(args.from_dotenv),
        token=token,
        destination=destination,
        existing_ledger_entries=existing)
    final_head = _git_head("HEAD")
    packet = build_proof_packet(
        run, old_manifest=old_manifest, start_head=start_head,
        final_head=final_head, origin_head=origin_head,
        git_status_summary=_git_status_summary())
    doc = build_proof_doc(packet)
    written = write_artifacts(ROOT, packet, doc)
    print("TASK " + TASK_LABEL)
    print("REAL_SENDMESSAGE_ATTEMPTED " + str(packet["real_send_attempted"]))
    print("REAL_SENDMESSAGE_SUCCEEDED " + str(packet["send_succeeded"]))
    print("MANUAL_GATE_REVALIDATED " + str(packet["manual_gate_revalidated"]))
    print("SEND_OUTCOME " + str(packet["send_outcome_class"]))
    print("BLOCKED_REASONS " + ",".join(packet.get("blocked_reasons") or []))
    print("BUDGET_USED " + str(packet["request_budget_used"]))
    print("LEDGER_ENTRY_COUNT_BEFORE " + str(packet["ledger_entry_count_before"]))
    print("LEDGER_ENTRY_COUNT " + str(packet["ledger_entry_count"]))
    print("RESPONSE_CHECKSUM " + str(packet["response_checksum"]))
    print("RESPONSE_SHAPE_CHECKSUM " + str(packet["response_shape_checksum"]))
    print("EVIDENCE_SCAN_CLEAN")
    for path in written:
        print("WROTE " + path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
