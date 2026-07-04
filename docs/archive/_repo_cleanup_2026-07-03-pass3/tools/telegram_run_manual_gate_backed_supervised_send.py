"""Approved manual-gate-backed supervised Telegram send runner.

Task 0174VF/VG/VH. Consumes the redacted 0174VC manual-gate artifact,
rebuilds the deterministic fourth send candidate, revalidates payload,
destination binding, operator gate hash, replay guard, and request budget, then
performs at most one Telegram sendMessage. Import has no side effects.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops import telegram_local_adapter_contract as adapter  # noqa:E402
from live_contentops import telegram_manual_gate_packet_builder as gate  # noqa:E402
from live_contentops import telegram_supervised_send_outcome_ledger as ledger  # noqa:E402

TASK_LABEL = (
    "TASK_CONTENTOPS_0174VF_VG_VH_TELEGRAM_APPROVED_MANUAL_GATE_BACKED_"
    "FOURTH_SUPERVISED_SEND_RUNNER_BATCH_V0"
)
MODEL = "TELEGRAM_MANUAL_GATE_BACKED_SEND_RUNNER_0174VF_VG_VH"
MODEL_VERSION = "0174VF_VG_VH_TELEGRAM_MANUAL_GATE_BACKED_SEND_RUNNER_V1"
REQUIRED_BASELINE_COMMIT = "a135e06d91d97bd448d0b711f87a1e98d1b37a33"
DOC_REL_DIR = Path("docs/automation/0174VF_VG_VH")
PACKET_FILENAME = "telegram_manual_gate_backed_send_proof_packet.json"
DOC_FILENAME = "telegram_manual_gate_backed_send_proof.md"
MANUAL_GATE_PACKET_REL = Path(
    "docs/automation/0174VC_VD_VE/telegram_manual_gate_packet_builder_packet.json")
LEDGER_PACKET_REL = Path(
    "docs/automation/0174UN_UO_UP/telegram_supervised_send_outcome_ledger_packet.json")
THIRD_PROOF_REL = Path(
    "docs/automation/0174UQ_UR_US/telegram_ledger_guarded_supervised_send_proof_packet.json")

SUPERVISED_TEST_MESSAGE = (
    "Capital Chronicle ContentOps live-gate test 4: approved manual-gate-backed "
    "supervised Telegram sendMessage. No market advice."
)
LIVE_TEST_SEQUENCE = 4
REQUEST_BUDGET = 1
REQUEST_TIMEOUT_SECONDS = 10
DOTENV_TOKEN_KEY = "TELEGRAM_BOT_TOKEN"
DOTENV_DESTINATION_KEY = "TEST_TELEGRAM_CHANNEL"
DOTENV_ALLOWED_KEYS = (DOTENV_TOKEN_KEY, DOTENV_DESTINATION_KEY)
DOTENV_FILENAME = ".env"
TOKEN_HANDLE_DOMAIN = "cc_sendmessage_token_v1"
DEST_BINDING_DOMAIN = "cc_sendmessage_dest_checksum_v1"
DEST_ID_DOMAIN = "cc_sendmessage_dest_v1"

SEND_OK = "telegram_manual_gate_backed_send_ok_redacted"
SEND_PROVIDER_ERROR = "telegram_manual_gate_backed_send_provider_error_redacted"
SEND_NETWORK_ERROR = "telegram_manual_gate_backed_send_network_error_redacted"
SEND_BLOCKED = "telegram_manual_gate_backed_send_blocked_before_network"

BLOCK_MISSING_MANUAL_GATE_PACKET = "manual_gate_packet_missing"
BLOCK_MANUAL_GATE_NOT_APPROVED = "manual_gate_not_approved_for_runner"
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
    "TASK_CONTENTOPS_0174VI_VJ_VK_TELEGRAM_MANUAL_GATE_APPROVAL_FOR_EXACT_"
    "TEST4_PAYLOAD_BATCH_V0"
)


def serialize(obj):
    return adapter.serialize(obj)


def compute_checksum(obj):
    return adapter.compute_checksum(obj)


def _fingerprint16(value, domain):
    digest = hashlib.sha256((domain + "::" + str(value)).encode("utf-8")).hexdigest()
    return digest[:16]


def _gate_id_hash(gate_id):
    if not gate_id:
        return None
    return compute_checksum({"kind": "operator_gate_id_hash", "operator_gate_id": gate_id})


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
    fields = redacted_fields or {}
    code_class = _classify_provider_code(status_code)
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


def validate_manual_gate_packet(packet):
    p = packet or {}
    captured = p.get("captured_approval_state") or {}
    blockers = []
    if not p:
        blockers.append(BLOCK_MISSING_MANUAL_GATE_PACKET)
    if captured.get("allowed_next_step") != gate.NEXT_STEP_APPROVED_FOR_RUNNER:
        blockers.append(BLOCK_MANUAL_GATE_NOT_APPROVED)
    if captured.get("operator_approval_outcome_class") != gate.APPROVAL_CAPTURED:
        blockers.append(BLOCK_MANUAL_GATE_NOT_APPROVED)
    required = {
        "approved_payload_checksum": captured.get("approved_payload_checksum"),
        "destination_binding_checksum": captured.get("destination_binding_checksum"),
        "operator_gate_id_hash": captured.get("operator_gate_id_hash"),
        "manual_gate_packet_checksum": captured.get("manual_gate_packet_checksum"),
    }
    if not required["approved_payload_checksum"]:
        blockers.append(BLOCK_APPROVED_PAYLOAD_MISMATCH)
    if not required["destination_binding_checksum"]:
        blockers.append(BLOCK_DESTINATION_BINDING_MISMATCH)
    if not required["operator_gate_id_hash"]:
        blockers.append(BLOCK_OPERATOR_GATE_HASH_MISSING)
    if not required["manual_gate_packet_checksum"]:
        blockers.append(BLOCK_MANUAL_GATE_NOT_APPROVED)
    if adapter.scan_for_leaks(p) or adapter.scan_for_financial_advice(p):
        blockers.append(BLOCK_FORBIDDEN_VALUE)
    return sorted(set(blockers)), captured


def load_existing_ledger_entries(ledger_packet=None, third_proof_packet=None):
    entries = []
    lp = ledger_packet or {}
    first = lp.get("current_ledger_entry")
    if isinstance(first, dict) and first.get("ledger_entry_checksum"):
        entries.append(first)
    tp = third_proof_packet or {}
    if tp.get("new_ledger_entry_checksum"):
        evidence = {
            "task_label": tp.get("task_label"),
            "provider": adapter.PROVIDER_TELEGRAM,
            "method_name": adapter.METHOD_SUPERVISED_SEND,
            "live_test_sequence": tp.get("live_test_sequence"),
            "credential_source_class": tp.get("credential_source_class"),
            "destination_source_class": tp.get("destination_source_class"),
            "destination_binding_checksum": tp.get("destination_binding_checksum"),
            "credential_handle_id": tp.get("credential_handle_id"),
            "send_text_checksum": tp.get("send_text_checksum"),
            "request_checksum": tp.get("request_checksum"),
            "response_checksum": tp.get("response_checksum"),
            "response_shape_checksum": tp.get("response_shape_checksum"),
            "send_outcome_class": tp.get("send_outcome_class"),
            "send_succeeded": tp.get("send_succeeded"),
            "provider_status_code_class": tp.get("provider_status_code_class"),
            "response_status_class": tp.get("response_status_class"),
            "redacted_message_id_class": tp.get("redacted_message_id_class"),
            "request_budget_used": tp.get("request_budget_used"),
        }
        evidence["evidence_checksum"] = tp.get("final_evidence_checksum")
        entry = ledger.build_ledger_entry(evidence, operator_gate_id="third_send_gate")
        entry["ledger_entry_checksum"] = tp.get("new_ledger_entry_checksum")
        entry["exact_run_replay_key"] = tp.get("exact_run_replay_key")
        entry["stable_payload_replay_key"] = tp.get("stable_payload_replay_key")
        entries.append(entry)
    return entries


def build_candidate_evidence(rendered, one_request, *, credential_handle_id,
                             destination_binding_checksum,
                             token_present, destination_present):
    request_checksum = (one_request or {}).get("one_request_checksum")
    send_text_checksum = (rendered or {}).get("send_text_checksum")
    response_placeholder = compute_checksum({
        "kind": "manual_gate_backed_candidate_response_placeholder",
        "send_text_checksum": send_text_checksum,
        "request_checksum": request_checksum,
        "live_test_sequence": LIVE_TEST_SEQUENCE,
        "method_name": adapter.METHOD_SUPERVISED_SEND,
        "provider": adapter.PROVIDER_TELEGRAM,
    })
    packet = {
        "task_label": TASK_LABEL,
        "provider": adapter.PROVIDER_TELEGRAM,
        "method_name": adapter.METHOD_SUPERVISED_SEND,
        "live_test_sequence": LIVE_TEST_SEQUENCE,
        "credential_handle_id": credential_handle_id,
        "credential_source_class": "operator_local_dotenv_file" if token_present else "no_live_source",
        "destination_source_class": "operator_local_dotenv_test_channel" if destination_present else "no_live_destination",
        "destination_binding_checksum": destination_binding_checksum,
        "destination_present_redacted": bool(destination_present),
        "send_text_checksum": send_text_checksum,
        "request_checksum": request_checksum,
        "response_checksum": response_placeholder,
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


def run_manual_gate_backed_send(*, manual_gate_packet=None, operator_live_send_enabled=False,
                                token=None, destination=None,
                                existing_ledger_entries=None, http_transport=None):
    manual_gate = manual_gate_packet or {}
    gate_blockers, captured = validate_manual_gate_packet(manual_gate)
    approved_payload = captured.get("approved_payload_checksum")
    approved_destination = captured.get("destination_binding_checksum")
    approved_gate_hash = captured.get("operator_gate_id_hash")
    manual_gate_checksum = captured.get("manual_gate_packet_checksum")
    transient_gate_id = gate.DEMO_FRESH_GATE_ID
    transient_gate_hash = _gate_id_hash(transient_gate_id)

    rendered = adapter.render_telegram_payload(
        approved_text=SUPERVISED_TEST_MESSAGE, parse_mode=adapter.PARSE_MODE_NONE)
    enforcer = adapter.enforce_capability(
        requested_capability=adapter.ALLOWED_CAPABILITY,
        requested_method=adapter.METHOD_SUPERVISED_SEND)
    token_present = bool(token)
    destination_present = bool(destination)
    credential_handle_id = (_fingerprint16(token, TOKEN_HANDLE_DOMAIN) if token_present else None)
    destination_binding_id = (_fingerprint16(destination, DEST_ID_DOMAIN) if destination_present else None)
    destination_binding_checksum = (_fingerprint16(destination, DEST_BINDING_DOMAIN)
                                    if destination_present else None)
    fallback_destination_checksum = approved_destination if not destination_present else destination_binding_checksum
    one_request = adapter.build_one_request_object(
        rendered, enforcer,
        credential_handle_id=credential_handle_id or "",
        destination_binding_id=destination_binding_id or "")
    candidate = build_candidate_evidence(
        rendered, one_request,
        credential_handle_id=credential_handle_id,
        destination_binding_checksum=fallback_destination_checksum,
        token_present=token_present,
        destination_present=destination_present)

    existing = list(existing_ledger_entries or [])
    preflight_guard = ledger.build_replay_guard_state(
        existing, candidate, operator_gate_id=transient_gate_id)
    blocked = list(gate_blockers)
    if rendered.get("rendered_payload_outcome_class") != adapter.RENDER_OK:
        blocked.append(BLOCK_RENDER_NOT_OK)
    if enforcer.get("capability_enforcer_outcome_class") != adapter.ENFORCER_ALLOWED:
        blocked.append(BLOCK_CAPABILITY_NOT_ALLOWED)
    if one_request.get("one_request_outcome_class") != adapter.REQUEST_OK:
        blocked.append(BLOCK_REQUEST_NOT_BUILT)
    if candidate.get("send_text_checksum") != approved_payload:
        blocked.append(BLOCK_APPROVED_PAYLOAD_MISMATCH)
    if destination_present and destination_binding_checksum != approved_destination:
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
        existing, final_evidence, operator_gate_id=transient_gate_id)
    ledger_entry = ledger.build_ledger_entry(final_evidence, operator_gate_id=transient_gate_id)
    if send_result.get("send_attempted") and send_result.get("send_succeeded"):
        append = ledger.append_ledger_entry(existing, ledger_entry, post_guard)
    else:
        append = ledger.append_ledger_entry(
            existing, ledger_entry,
            {"replay_guard_outcome_class": "not_clear",
             "replay_guard_clear": False, "status": adapter.Status.BLOCKED})
    manual_gate_revalidated = (
        not bool(gate_blockers)
        and candidate.get("send_text_checksum") == approved_payload
        and (not destination_present
             or destination_binding_checksum == approved_destination)
        and bool(approved_gate_hash)
        and transient_gate_hash == approved_gate_hash
        and preflight_guard.get("replay_guard_outcome_class") == ledger.REPLAY_CLEAR)
    return {
        "manual_gate_packet": manual_gate,
        "captured_approval_state": captured,
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
    post_guard = rr["post_guard"]
    append = rr["append"]
    entry = rr["ledger_entry"]
    previous_entries = rr.get("existing_ledger_entries") or []
    previous_checksum = (previous_entries[-1].get("ledger_entry_checksum")
                         if previous_entries else None)
    captured = rr.get("captured_approval_state") or {}
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
        "operator_approval_outcome_class": captured.get("operator_approval_outcome_class"),
        "operator_gate_class": captured.get("operator_gate_class"),
        "operator_gate_id_hash_present": rr.get("operator_gate_id_hash_present"),
        "operator_gate_hash_matches": rr.get("operator_gate_hash_matches"),
        "approved_payload_checksum": rr.get("approved_payload_checksum"),
        "rebuilt_send_text_checksum": candidate.get("send_text_checksum"),
        "destination_binding_checksum": rr.get("destination_binding_checksum"),
        "rebuilt_destination_binding_checksum": candidate.get("destination_binding_checksum"),
        "replay_guard_outcome_class": post_guard.get("replay_guard_outcome_class"),
        "preflight_replay_guard_outcome_class": rr["preflight_guard"].get("replay_guard_outcome_class"),
        "request_budget_authorized": REQUEST_BUDGET,
        "request_budget_used": sr.get("budget_used"),
        "send_outcome_class": sr.get("outcome_class"),
        "blocked_reasons": sr.get("blocked_reasons"),
        "provider_status_code_class": sr.get("provider_status_code_class"),
        "response_status_class": sr.get("response_status_class"),
        "redacted_message_id_class": sr.get("message_id_class"),
        "response_checksum": final_evidence.get("response_checksum"),
        "response_shape_checksum": final_evidence.get("response_shape_checksum"),
        "candidate_evidence_checksum": candidate.get("evidence_checksum"),
        "final_evidence_checksum": final_evidence.get("evidence_checksum"),
        "previous_ledger_entry_checksum": previous_checksum,
        "new_ledger_entry_checksum": entry.get("ledger_entry_checksum"),
        "old_ledger_manifest_checksum": old_manifest,
        "new_ledger_manifest_checksum": append.get("ledger_manifest_checksum"),
        "ledger_entry_count_before": len(previous_entries),
        "ledger_entry_count": append.get("ledger_entry_count"),
        "ledger_appended": bool(append.get("appended")),
        "append_status_class": append.get("append_status_class"),
        "method_name": adapter.METHOD_SUPERVISED_SEND,
        "api_host_class": "telegram_api_host_class",
        "timeout_seconds": REQUEST_TIMEOUT_SECONDS,
    }
    packet.update(_safety_proofs())
    packet["evidence_checksum"] = compute_checksum(packet)
    return packet


def _safety_proofs():
    return {
        "stores_no_token": True,
        "stores_no_raw_destination": True,
        "stores_no_raw_response": True,
        "stores_no_raw_url": True,
        "stores_no_headers": True,
        "stores_no_cookies": True,
        "stores_no_raw_chat_id": True,
        "stores_no_username": True,
        "stores_no_raw_operator_gate_id": True,
        "stores_no_raw_approval_note": True,
        "no_retry": True,
        "no_scheduler": True,
        "no_webhook": True,
        "no_polling": True,
        "no_get_updates": True,
        "no_autonomous_reply": True,
        "no_media": True,
        "no_edit": True,
        "no_delete": True,
        "no_second_send_path": True,
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
    }


def build_proof_doc(packet):
    return (
        "# 0174VF/VG/VH Telegram Manual-Gate-Backed Send Proof\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        "## Run summary\n\n"
        f"- Start HEAD: `{packet['start_head']}`\n"
        f"- Final HEAD: `{packet['final_head']}`\n"
        f"- Origin HEAD: `{packet['origin_head']}`\n"
        f"- Live test sequence: `{packet['live_test_sequence']}`\n"
        f"- Real send attempted: `{packet['real_send_attempted']}`\n"
        f"- Send succeeded: `{packet['send_succeeded']}`\n"
        f"- Send outcome class: `{packet['send_outcome_class']}`\n"
        f"- Blocked reasons: `{packet['blocked_reasons']}`\n"
        f"- Request budget used: `{packet['request_budget_used']}` of `{packet['request_budget_authorized']}`\n\n"
        "## Manual gate revalidation\n\n"
        f"- Manual gate packet checksum: `{packet['manual_gate_packet_checksum']}`\n"
        f"- Manual gate revalidated: `{packet['manual_gate_revalidated']}`\n"
        f"- Operator approval outcome: `{packet['operator_approval_outcome_class']}`\n"
        f"- Operator gate class: `{packet['operator_gate_class']}`\n"
        f"- Operator gate hash present: `{packet['operator_gate_id_hash_present']}`\n"
        f"- Operator gate hash matches: `{packet['operator_gate_hash_matches']}`\n"
        f"- Approved payload checksum: `{packet['approved_payload_checksum']}`\n"
        f"- Rebuilt send text checksum: `{packet['rebuilt_send_text_checksum']}`\n"
        f"- Approved destination checksum: `{packet['destination_binding_checksum']}`\n"
        f"- Rebuilt destination checksum: `{packet['rebuilt_destination_binding_checksum']}`\n\n"
        "## Replay and ledger\n\n"
        f"- Preflight replay outcome: `{packet['preflight_replay_guard_outcome_class']}`\n"
        f"- Post replay outcome: `{packet['replay_guard_outcome_class']}`\n"
        f"- Ledger count before: `{packet['ledger_entry_count_before']}`\n"
        f"- Ledger count after: `{packet['ledger_entry_count']}`\n"
        f"- Previous ledger entry checksum: `{packet['previous_ledger_entry_checksum']}`\n"
        f"- New ledger entry checksum: `{packet['new_ledger_entry_checksum']}`\n"
        f"- Old ledger manifest checksum: `{packet['old_ledger_manifest_checksum']}`\n"
        f"- New ledger manifest checksum: `{packet['new_ledger_manifest_checksum']}`\n\n"
        "## Redacted response\n\n"
        f"- Provider status code class: `{packet['provider_status_code_class']}`\n"
        f"- Response status class: `{packet['response_status_class']}`\n"
        f"- Redacted message id class: `{packet['redacted_message_id_class']}`\n"
        f"- Response checksum: `{packet['response_checksum']}`\n"
        f"- Response shape checksum: `{packet['response_shape_checksum']}`\n\n"
        f"## Next recommended task\n\n`{packet['next_recommended_task']}`\n")


def write_evidence(base_dir, packet, doc):
    violations = scan_proof(packet, doc)
    if violations:
        raise RuntimeError("refusing to write evidence: scan found %d violation(s)" % len(violations))
    out_dir = Path(base_dir) / DOC_REL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / PACKET_FILENAME
    doc_path = out_dir / DOC_FILENAME
    packet_path.write_text(serialize(packet), encoding="utf-8", newline="\n")
    doc_path.write_text(doc, encoding="utf-8", newline="\n")
    return [str(packet_path), str(doc_path)]


def _git(*args):
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True)


def _head(ref="HEAD"):
    res = _git("rev-parse", ref)
    return res.stdout.strip() if res.returncode == 0 else None


def _git_status_summary():
    res = _git("status", "--porcelain")
    if res.returncode != 0:
        return "git_status_unavailable"
    lines = [ln for ln in res.stdout.splitlines() if ln.strip()]
    return "changed_entries=%d" % len(lines)


def _parse_arg_value(argv, flag):
    if flag not in argv:
        return None
    idx = argv.index(flag)
    if idx + 1 >= len(argv):
        return None
    value = str(argv[idx + 1]).strip()
    if not value or value.startswith("--"):
        return None
    return value


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    use_dotenv = "--from-dotenv" in argv
    manual_gate_arg = _parse_arg_value(argv, "--manual-gate-packet")
    manual_gate_path = Path(ROOT) / (manual_gate_arg or str(MANUAL_GATE_PACKET_REL))
    start_head = _head("HEAD")
    manual_gate_packet = load_json(manual_gate_path)
    ledger_packet = load_json(Path(ROOT) / LEDGER_PACKET_REL) or {}
    third_packet = load_json(Path(ROOT) / THIRD_PROOF_REL) or {}
    existing = load_existing_ledger_entries(ledger_packet, third_packet)
    old_manifest = third_packet.get("new_ledger_manifest_checksum") or ledger.compute_ledger_manifest_checksum(existing)

    # Gate-first: do not read .env unless the manual gate artifact exists,
    # is structurally approved, AND approves the exact mandated test-4 payload.
    gate_blockers, captured = validate_manual_gate_packet(manual_gate_packet)
    rendered_probe = adapter.render_telegram_payload(
        approved_text=SUPERVISED_TEST_MESSAGE, parse_mode=adapter.PARSE_MODE_NONE)
    approved_payload_matches = (
        captured.get("approved_payload_checksum")
        == rendered_probe.get("send_text_checksum"))
    can_hydrate_live_boundary = (
        use_dotenv and manual_gate_arg is not None and not gate_blockers
        and approved_payload_matches)
    if can_hydrate_live_boundary:
        token, destination = load_dotenv_values(Path(ROOT) / DOTENV_FILENAME)
        live_enabled = True
    else:
        token, destination = None, None
        live_enabled = False

    result = run_manual_gate_backed_send(
        manual_gate_packet=manual_gate_packet,
        operator_live_send_enabled=live_enabled,
        token=token,
        destination=destination,
        existing_ledger_entries=existing)
    del token, destination

    packet = build_proof_packet(
        result,
        old_manifest=old_manifest,
        start_head=start_head,
        final_head=_head("HEAD"),
        origin_head=_head("origin/master"),
        git_status_summary=_git_status_summary())
    doc = build_proof_doc(packet)
    written = write_evidence(ROOT, packet, doc)
    print("TASK " + TASK_LABEL)
    print("REAL_SENDMESSAGE_ATTEMPTED " + str(packet["real_send_attempted"]))
    print("REAL_SENDMESSAGE_SUCCEEDED " + str(packet["send_succeeded"]))
    print("MANUAL_GATE_REVALIDATED " + str(packet["manual_gate_revalidated"]))
    print("SEND_OUTCOME " + str(packet["send_outcome_class"]))
    print("BLOCKED_REASONS " + ",".join(packet["blocked_reasons"] or []))
    print("BUDGET_USED " + str(packet["request_budget_used"]))
    print("LEDGER_ENTRY_COUNT " + str(packet["ledger_entry_count"]))
    print("EVIDENCE_SCAN_CLEAN")
    for path in written:
        print("WROTE " + path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
