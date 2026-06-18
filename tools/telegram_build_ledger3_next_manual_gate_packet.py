"""Build ledger-3 next manual gate packet for supervised Telegram test 5.

Local-only deterministic builder for 0174VO/VP/VQ. It consumes the accepted
remote operator loop state at ledger count 3, builds a redacted candidate for
live test sequence 5, verifies next-gate precheck through the remote-loop state
model, captures symbolic operator approval, and writes scanner-clean artifacts.
It never reads .env, credentials, or network resources and never dispatches.
"""

import json
import os.path
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from live_contentops import telegram_local_adapter_contract as adapter
from live_contentops import telegram_manual_gate_packet_builder as gate
from live_contentops import telegram_remote_operator_loop_state as loop

TASK_LABEL = (
    "TASK_CONTENTOPS_0174VO_VP_VQ_TELEGRAM_REMOTE_OPERATOR_LOOP_NEXT_MANUAL_"
    "GATE_PACKET_FROM_LEDGER3_BATCH_V0"
)
MODEL = "TELEGRAM_LEDGER3_NEXT_MANUAL_GATE_PACKET_BUILDER_0174VO_VP_VQ"
MODEL_VERSION = "0174VO_VP_VQ_TELEGRAM_LEDGER3_NEXT_MANUAL_GATE_PACKET_BUILDER_V1"
SOURCE_BASELINE_COMMIT = "8ab64cb2c3f839343d13a33d4794e1244d90ba78"
DOC_REL_DIR = os.path.join("docs", "automation", "0174VO_VP_VQ")
MANUAL_GATE_PACKET_FILENAME = "telegram_ledger3_next_manual_gate_packet.json"
MANUAL_GATE_DOC_FILENAME = "telegram_ledger3_next_manual_gate_packet.md"
BUILDER_PACKET_FILENAME = "telegram_ledger3_next_manual_gate_packet_builder_packet.json"
BUILDER_DOC_FILENAME = "telegram_ledger3_next_manual_gate_packet_builder.md"
REMOTE_LOOP_PACKET_REL = os.path.join(
    "docs", "automation", "0174VL_VM_VN", "telegram_remote_operator_loop_state_packet.json")

TEST5_MESSAGE = (
    "Capital Chronicle ContentOps live-gate test 5: ledger-3 remote-loop "
    "manual gate candidate. No market advice."
)
LIVE_TEST_SEQUENCE = 5
DEFAULT_OPERATOR_GATE_ID = "ledger3_next_manual_gate_transient_local_gate_v1"
SYMBOLIC_CREDENTIAL_HANDLE = "ledger3_next_manual_gate_credential_handle_class"
NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174VR_VS_VT_TELEGRAM_LEDGER3_MANUAL_GATE_BACKED_FIFTH_"
    "SUPERVISED_SEND_RUNNER_BATCH_V0"
)

LEDGER3_SOURCE_OK = "ledger3_source_ok"
LEDGER3_SOURCE_MISSING = "ledger3_source_blocked_missing_state"
LEDGER3_SOURCE_UNRECONCILED = "ledger3_source_blocked_unreconciled"
LEDGER3_SOURCE_WRONG_COUNT = "ledger3_source_blocked_wrong_ledger_count"
LEDGER3_SOURCE_MISSING_MANIFEST = "ledger3_source_blocked_missing_manifest"
LEDGER3_SOURCE_FAIL_CLOSED = "ledger3_source_fail_closed_forbidden_value"


def serialize(obj):
    return adapter.serialize(obj)


def compute_checksum(obj):
    return adapter.compute_checksum(obj)


def scan(obj):
    return adapter.scan_for_leaks(obj) + adapter.scan_for_financial_advice(obj)


def scan_artifact(packet, doc):
    return scan(packet) + scan(doc)


def _safety_flags():
    return {
        "network_performed": False,
        "platform_api_called": False,
        "telegram_api_called": False,
        "credential_hydrated": False,
        "credential_read": False,
        "env_read": False,
        "dotenv_read": False,
        "sendmessage_executed": False,
        "dispatch_performed": False,
        "scheduler_enabled": False,
        "auto_retry_allowed": False,
        "autonomous_reply_performed": False,
        "webhook_or_polling_enabled": False,
        "live_ready": False,
        "auto_send_ready": False,
        "valid_for_live_execution": False,
        "is_local_only": True,
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
        "no_financial_advice_emitted": True,
    }


def validate_remote_loop_state_for_next_gate(remote_loop_state_packet):
    packet = remote_loop_state_packet or {}
    state = packet.get("remote_loop_state") or {}
    forbidden = bool(scan(packet))
    if forbidden:
        outcome = LEDGER3_SOURCE_FAIL_CLOSED
    elif not packet:
        outcome = LEDGER3_SOURCE_MISSING
    elif (packet.get("reconciliation_outcome_class") != loop.RECONCILE_OK
          or state.get("reconciled") is not True):
        outcome = LEDGER3_SOURCE_UNRECONCILED
    elif packet.get("current_ledger_count") != 3 or state.get("last_successful_send_sequence") != 4:
        outcome = LEDGER3_SOURCE_WRONG_COUNT
    elif not (packet.get("new_ledger_manifest_checksum") and state.get("remote_loop_state_checksum")):
        outcome = LEDGER3_SOURCE_MISSING_MANIFEST
    else:
        outcome = LEDGER3_SOURCE_OK
    blockers = [] if outcome == LEDGER3_SOURCE_OK else [outcome]
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": adapter.Status.PASS if outcome == LEDGER3_SOURCE_OK else adapter.Status.BLOCKED,
        "provider": packet.get("provider") or adapter.PROVIDER_TELEGRAM,
        "ledger3_source_validation_outcome_class": outcome,
        "source_valid": outcome == LEDGER3_SOURCE_OK,
        "blocker_stack": blockers,
        "source_current_ledger_count": packet.get("current_ledger_count"),
        "source_last_successful_send_sequence": state.get("last_successful_send_sequence"),
        "source_current_ledger_manifest_checksum": packet.get("new_ledger_manifest_checksum"),
        "source_remote_loop_state_checksum": state.get("remote_loop_state_checksum"),
        "forbidden_fields_detected": forbidden,
        **_safety_flags(),
    }
    result["ledger3_source_validation_checksum"] = compute_checksum(result)
    return result


def build_ledger3_next_candidate_evidence(remote_loop_state_packet):
    packet = remote_loop_state_packet or {}
    state = packet.get("remote_loop_state") or {}
    rendered = adapter.render_telegram_payload(
        approved_text=TEST5_MESSAGE,
        parse_mode=adapter.PARSE_MODE_NONE)
    enforcer = adapter.enforce_capability(
        requested_capability=adapter.ALLOWED_CAPABILITY,
        requested_method=adapter.METHOD_SUPERVISED_SEND)
    destination_binding_checksum = (
        (state.get("accepted_ledger_entry") or {}).get("destination_binding_checksum")
        or compute_checksum({
            "kind": "ledger3_next_destination_binding_checksum",
            "source_remote_loop_state_checksum": state.get("remote_loop_state_checksum"),
            "source_current_ledger_manifest_checksum": packet.get("new_ledger_manifest_checksum"),
            "destination_binding_class": "same_redacted_test_channel_binding_class",
        })[:16])
    destination_binding_id = compute_checksum({
        "kind": "ledger3_next_destination_binding_id",
        "source": destination_binding_checksum,
    })[:16]
    one_request = adapter.build_one_request_object(
        rendered, enforcer,
        credential_handle_id=SYMBOLIC_CREDENTIAL_HANDLE,
        destination_binding_id=destination_binding_id)
    evidence = {
        "task_label": TASK_LABEL,
        "provider": adapter.PROVIDER_TELEGRAM,
        "method_name": adapter.METHOD_SUPERVISED_SEND,
        "live_test_sequence": LIVE_TEST_SEQUENCE,
        "source_remote_loop_state_checksum": state.get("remote_loop_state_checksum"),
        "source_current_ledger_manifest_checksum": packet.get("new_ledger_manifest_checksum"),
        "source_current_ledger_count": packet.get("current_ledger_count"),
        "previous_successful_send_sequence": state.get("last_successful_send_sequence"),
        "candidate_text_class": "ledger3_test5_message_class",
        "destination_binding_checksum": destination_binding_checksum,
        "destination_binding_id_class": "redacted_destination_binding_id_class",
        "credential_handle_id": SYMBOLIC_CREDENTIAL_HANDLE,
        "send_text_checksum": rendered.get("send_text_checksum"),
        "request_checksum": one_request.get("one_request_checksum"),
        "response_checksum": compute_checksum({"kind": "test5_response_pending_placeholder"}),
        "response_shape_checksum": compute_checksum({"kind": "test5_response_shape_pending_placeholder"}),
        "send_outcome_class": "candidate_pending_manual_gate_send_outcome_class",
        "send_succeeded": False,
        "request_budget_used": 0,
        "redacted_message_id_class": "redacted_message_id_absent_pending_send_class",
        **_safety_flags(),
    }
    evidence["evidence_checksum"] = compute_checksum(evidence)
    return evidence


def _remote_loop_state(remote_loop_state_packet):
    return (remote_loop_state_packet or {}).get("remote_loop_state") or {}


def _approval_for(candidate_packet, operator_gate_id):
    return {
        "approved": True,
        "operator_gate_id": operator_gate_id,
        "approval_note_class": gate.DEFAULT_NOTE_CLASS,
        "approval_timestamp_placeholder_class": gate.DEFAULT_TIMESTAMP_CLASS,
        "approved_payload_checksum": candidate_packet.get("approved_payload_checksum_expected"),
        "destination_binding_checksum": candidate_packet.get("destination_binding_checksum"),
    }


def build_ledger3_next_manual_gate_packet(remote_loop_state_packet, operator_gate_id=None):
    gate_id = operator_gate_id
    source_validation = validate_remote_loop_state_for_next_gate(remote_loop_state_packet)
    candidate_evidence = build_ledger3_next_candidate_evidence(remote_loop_state_packet)
    precheck = loop.build_next_gate_precheck_state(
        _remote_loop_state(remote_loop_state_packet), candidate_evidence,
        fresh_operator_gate_id=gate_id)
    candidate = gate.build_manual_gate_candidate_packet(
        {}, candidate_evidence_packet=candidate_evidence,
        fresh_operator_gate_id=gate_id,
        console_packet={"provider": adapter.PROVIDER_TELEGRAM})
    blockers = []
    if source_validation.get("source_valid") is not True:
        blockers.append("manual_gate_blocker_ledger3_source_not_valid")
    if not gate_id:
        blockers.append("manual_gate_blocker_missing_fresh_operator_gate")
    if precheck.get("next_gate_outcome_class") != loop.NEXT_CLEAR:
        blockers.append("manual_gate_blocker_next_gate_precheck_not_clear")
    clear = not blockers
    candidate["manual_gate_candidate_outcome_class"] = (
        gate.CANDIDATE_PRECHECK_CLEAR if clear else gate.CANDIDATE_BLOCKED)
    candidate["next_send_precheck_outcome_class"] = precheck.get("next_gate_outcome_class")
    candidate["precheck_clear_for_manual_gate"] = clear
    candidate["replay_guard_outcome_class"] = precheck.get("replay_guard_outcome_class")
    candidate["blockers"] = blockers
    candidate["live_test_sequence"] = LIVE_TEST_SEQUENCE
    candidate["source_remote_loop_state_checksum"] = (
        source_validation.get("source_remote_loop_state_checksum"))
    candidate["source_current_ledger_manifest_checksum"] = (
        source_validation.get("source_current_ledger_manifest_checksum"))
    candidate["source_current_ledger_count"] = source_validation.get(
        "source_current_ledger_count")
    candidate["manual_gate_candidate_checksum"] = compute_checksum(candidate)
    approval = gate.capture_operator_approval(
        candidate, _approval_for(candidate, gate_id) if clear else None)
    manual_gate_packet = gate.build_manual_gate_packet(candidate, approval)
    manual_gate_packet["task_label"] = TASK_LABEL
    manual_gate_packet["model"] = MODEL
    manual_gate_packet["model_version"] = MODEL_VERSION
    manual_gate_packet["live_test_sequence"] = LIVE_TEST_SEQUENCE
    manual_gate_packet["source_remote_loop_state_checksum"] = candidate[
        "source_remote_loop_state_checksum"]
    manual_gate_packet["source_current_ledger_manifest_checksum"] = candidate[
        "source_current_ledger_manifest_checksum"]
    manual_gate_packet["source_current_ledger_count"] = candidate[
        "source_current_ledger_count"]
    manual_gate_packet["next_gate_precheck_checksum"] = precheck.get(
        "next_gate_precheck_checksum")
    manual_gate_packet["candidate_evidence_checksum"] = candidate_evidence.get(
        "evidence_checksum")
    manual_gate_packet["manual_gate_packet_checksum"] = compute_checksum(manual_gate_packet)
    result = {
        "source_validation": source_validation,
        "candidate_evidence": candidate_evidence,
        "next_gate_precheck": precheck,
        "manual_gate_candidate": candidate,
        "captured_approval": approval,
        "manual_gate_packet": manual_gate_packet,
        "status": adapter.Status.PASS if clear else adapter.Status.BLOCKED,
        **_safety_flags(),
    }
    result["builder_result_checksum"] = compute_checksum(result)
    return result


def build_builder_artifact_packet(remote_loop_state_packet, operator_gate_id=None):
    result = build_ledger3_next_manual_gate_packet(
        remote_loop_state_packet, operator_gate_id=operator_gate_id or DEFAULT_OPERATOR_GATE_ID)
    source_validation = result["source_validation"]
    evidence = result["candidate_evidence"]
    precheck = result["next_gate_precheck"]
    approval = result["captured_approval"]
    manual = result["manual_gate_packet"]
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": result.get("status"),
        "provider": adapter.PROVIDER_TELEGRAM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "source_validation_outcome_class": source_validation.get(
            "ledger3_source_validation_outcome_class"),
        "source_remote_loop_state_checksum": source_validation.get(
            "source_remote_loop_state_checksum"),
        "source_current_ledger_manifest_checksum": source_validation.get(
            "source_current_ledger_manifest_checksum"),
        "source_current_ledger_count": source_validation.get("source_current_ledger_count"),
        "test5_message_checksum": evidence.get("send_text_checksum"),
        "candidate_evidence_checksum": evidence.get("evidence_checksum"),
        "next_gate_precheck_outcome_class": precheck.get("next_gate_outcome_class"),
        "next_gate_precheck_checksum": precheck.get("next_gate_precheck_checksum"),
        "manual_gate_packet_checksum": manual.get("manual_gate_packet_checksum"),
        "captured_approval_checksum": approval.get("operator_approval_capture_checksum"),
        "approved_payload_checksum": approval.get("approved_payload_checksum"),
        "destination_binding_checksum": approval.get("destination_binding_checksum"),
        "allowed_next_step": manual.get("allowed_next_step"),
        "operator_approval_outcome_class": approval.get("operator_approval_outcome_class"),
        "live_test_sequence": LIVE_TEST_SEQUENCE,
        "manual_gate_packet_ref": MANUAL_GATE_PACKET_FILENAME,
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        **_safety_flags(),
    }
    packet["artifact_packet_checksum"] = compute_checksum(packet)
    return packet, result


def build_manual_gate_doc(manual_gate_packet):
    p = manual_gate_packet or {}
    return (
        "# 0174VO/VP/VQ Ledger-3 Next Manual Gate Packet\n\n"
        f"Task: `{p.get('task_label')}`\n\n"
        f"Model: `{p.get('model')}` version `{p.get('model_version')}`\n\n"
        "## Manual gate packet\n\n"
        f"- Live test sequence: `{p.get('live_test_sequence')}`\n"
        f"- Allowed next step: `{p.get('allowed_next_step')}`\n"
        f"- Operator approval outcome: `{p.get('operator_approval_outcome_class')}`\n"
        f"- Approved payload checksum: `{p.get('approved_payload_checksum')}`\n"
        f"- Destination binding checksum: `{p.get('destination_binding_checksum')}`\n"
        f"- Source remote loop state checksum: `{p.get('source_remote_loop_state_checksum')}`\n"
        f"- Source ledger count: `{p.get('source_current_ledger_count')}`\n"
        f"- Manual gate packet checksum: `{p.get('manual_gate_packet_checksum')}`\n\n"
        "## Safety\n\n"
        f"- Network performed: `{p.get('network_performed')}`\n"
        f"- sendMessage executed: `{p.get('sendmessage_executed')}`\n"
        f"- Stores no token: `{p.get('stores_no_token')}`\n"
        f"- Stores no raw destination: `{p.get('stores_no_raw_destination')}`\n")


def build_builder_doc(packet):
    return (
        "# 0174VO/VP/VQ Ledger-3 Next Manual Gate Packet Builder\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        "## Source validation\n\n"
        f"- Outcome: `{packet['source_validation_outcome_class']}`\n"
        f"- Source ledger count: `{packet['source_current_ledger_count']}`\n"
        f"- Source remote loop checksum: `{packet['source_remote_loop_state_checksum']}`\n"
        f"- Source ledger manifest checksum: `{packet['source_current_ledger_manifest_checksum']}`\n\n"
        "## Candidate + gate\n\n"
        f"- Test-5 message checksum: `{packet['test5_message_checksum']}`\n"
        f"- Candidate evidence checksum: `{packet['candidate_evidence_checksum']}`\n"
        f"- Next-gate outcome: `{packet['next_gate_precheck_outcome_class']}`\n"
        f"- Next-gate precheck checksum: `{packet['next_gate_precheck_checksum']}`\n"
        f"- Captured approval checksum: `{packet['captured_approval_checksum']}`\n"
        f"- Manual gate packet checksum: `{packet['manual_gate_packet_checksum']}`\n"
        f"- Allowed next step: `{packet['allowed_next_step']}`\n\n"
        "## Safety\n\n"
        f"- Network performed: `{packet['network_performed']}`\n"
        f"- Telegram API called: `{packet['telegram_api_called']}`\n"
        f"- Credential read: `{packet['credential_read']}`\n"
        f"- Env read: `{packet['env_read']}`\n"
        f"- sendMessage executed: `{packet['sendmessage_executed']}`\n"
        f"- Stores no token: `{packet['stores_no_token']}`\n"
        f"- Stores no raw destination: `{packet['stores_no_raw_destination']}`\n"
        f"- Stores no raw response: `{packet['stores_no_raw_response']}`\n"
        f"- Stores no raw URL: `{packet['stores_no_raw_url']}`\n"
        f"- Stores no headers: `{packet['stores_no_headers']}`\n"
        f"- Stores no cookies: `{packet['stores_no_cookies']}`\n"
        f"- Stores no raw gate id: `{packet['stores_no_raw_operator_gate_id']}`\n"
        f"- Stores no raw approval note: `{packet['stores_no_raw_approval_note']}`\n\n"
        f"## Artifact checksum\n\n`{packet['artifact_packet_checksum']}`\n\n"
        f"## Next recommended task\n\n`{packet['next_recommended_task']}`\n")


def load_packet(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def write_artifacts(base_dir, builder_packet, builder_doc, manual_packet, manual_doc):
    violations = (scan_artifact(builder_packet, builder_doc)
                  + scan_artifact(manual_packet, manual_doc))
    if violations:
        raise RuntimeError(
            "refusing to write ledger3 manual gate artifacts: scan found %d violation(s)" % len(violations))
    out_dir = os.path.join(base_dir, DOC_REL_DIR)
    os.makedirs(out_dir, exist_ok=True)
    paths = [
        (os.path.join(out_dir, MANUAL_GATE_PACKET_FILENAME), serialize(manual_packet)),
        (os.path.join(out_dir, MANUAL_GATE_DOC_FILENAME), manual_doc),
        (os.path.join(out_dir, BUILDER_PACKET_FILENAME), serialize(builder_packet)),
        (os.path.join(out_dir, BUILDER_DOC_FILENAME), builder_doc),
    ]
    for path, content in paths:
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    return [path for path, _content in paths]


def _git_head(ref="HEAD"):
    res = subprocess.run(["git", "rev-parse", ref], cwd=ROOT,
                         capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else None


def main(argv=None):
    remote_packet = load_packet(os.path.join(ROOT, REMOTE_LOOP_PACKET_REL))
    builder_packet, result = build_builder_artifact_packet(
        remote_packet, operator_gate_id=DEFAULT_OPERATOR_GATE_ID)
    builder_packet["start_head"] = _git_head("HEAD")
    builder_packet["origin_head"] = _git_head("origin/master")
    builder_packet["baseline_matched"] = builder_packet["start_head"] == SOURCE_BASELINE_COMMIT
    builder_packet["artifact_packet_checksum"] = compute_checksum(builder_packet)
    builder_doc = build_builder_doc(builder_packet)
    manual_packet = result["manual_gate_packet"]
    manual_doc = build_manual_gate_doc(manual_packet)
    written = write_artifacts(ROOT, builder_packet, builder_doc, manual_packet, manual_doc)
    print("TASK " + TASK_LABEL)
    print("SOURCE_VALIDATION " + str(builder_packet["source_validation_outcome_class"]))
    print("SOURCE_LEDGER_COUNT " + str(builder_packet["source_current_ledger_count"]))
    print("SOURCE_REMOTE_LOOP_STATE_CHECKSUM " + str(builder_packet["source_remote_loop_state_checksum"]))
    print("CANDIDATE_EVIDENCE_CHECKSUM " + str(builder_packet["candidate_evidence_checksum"]))
    print("NEXT_GATE_PRECHECK " + str(builder_packet["next_gate_precheck_outcome_class"]))
    print("MANUAL_GATE_PACKET_CHECKSUM " + str(builder_packet["manual_gate_packet_checksum"]))
    print("APPROVED_PAYLOAD_CHECKSUM " + str(builder_packet["approved_payload_checksum"]))
    print("DESTINATION_BINDING_CHECKSUM " + str(builder_packet["destination_binding_checksum"]))
    print("EVIDENCE_SCAN_CLEAN")
    for path in written:
        print("WROTE " + path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
