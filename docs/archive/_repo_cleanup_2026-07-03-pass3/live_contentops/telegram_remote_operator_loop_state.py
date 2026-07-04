"""Telegram remote operator loop state after exact test4 send.

Task 0174VL/VM/VN. Promotes the accepted exact-test4 manual-gate-backed
send proof into a local-only operator truth model and builds deterministic next
gate precheck state. Import has no side effects. No network, no env, no
credentials, no Telegram call, no sendMessage execution.
"""

import json
import os.path
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from live_contentops import telegram_local_adapter_contract as adapter
from live_contentops import telegram_supervised_send_outcome_ledger as ledger

TASK_LABEL = (
    "TASK_CONTENTOPS_0174VL_VM_VN_TELEGRAM_EXACT_TEST4_LEDGER_ACCEPTANCE_AND_"
    "REMOTE_OPERATOR_LOOP_NEXT_GATE_BATCH_V0"
)
MODEL = "TELEGRAM_REMOTE_OPERATOR_LOOP_STATE_0174VL_VM_VN"
MODEL_VERSION = "0174VL_VM_VN_TELEGRAM_REMOTE_OPERATOR_LOOP_STATE_V1"
SOURCE_BASELINE_COMMIT = "9e8b66b495ea98aca1120ef5158c3793f1d0b3bc"
DOC_REL_DIR = os.path.join("docs", "automation", "0174VL_VM_VN")
PACKET_FILENAME = "telegram_remote_operator_loop_state_packet.json"
DOC_FILENAME = "telegram_remote_operator_loop_state.md"

EXACT_PROOF_REL = os.path.join(
    "docs", "automation", "0174VI_VJ_VK", "telegram_exact_test4_send_proof_packet.json")
EXACT_GATE_REL = os.path.join(
    "docs", "automation", "0174VI_VJ_VK", "telegram_exact_test4_manual_gate_packet.json")
LEDGER_PACKET_REL = os.path.join(
    "docs", "automation", "0174UN_UO_UP", "telegram_supervised_send_outcome_ledger_packet.json")
THIRD_PROOF_REL = os.path.join(
    "docs", "automation", "0174UQ_UR_US", "telegram_ledger_guarded_supervised_send_proof_packet.json")

RECONCILE_OK = "remote_loop_reconciliation_ok_ledger_advanced_to_3"
RECONCILE_MISSING = "remote_loop_reconciliation_blocked_missing_exact_test4_proof"
RECONCILE_SEND_NOT_SUCCEEDED = "remote_loop_reconciliation_blocked_send_not_succeeded"
RECONCILE_GATE_NOT_REVALIDATED = "remote_loop_reconciliation_blocked_manual_gate_not_revalidated"
RECONCILE_LEDGER_NOT_ADVANCED = "remote_loop_reconciliation_blocked_ledger_not_advanced"
RECONCILE_MANIFEST_NOT_ADVANCED = "remote_loop_reconciliation_blocked_manifest_not_advanced"
RECONCILE_FAIL_CLOSED = "remote_loop_reconciliation_fail_closed_forbidden_value"

NEXT_WAITING = "next_gate_waiting_for_candidate"
NEXT_BLOCKED_EXACT = "next_gate_blocked_exact_replay"
NEXT_REQUIRES_FRESH_GATE = "next_gate_requires_fresh_operator_gate"
NEXT_CLEAR = "next_gate_clear_for_manual_gate_packet_builder"
NEXT_BLOCKED_UNRECONCILED = "next_gate_blocked_unreconciled_remote_loop"
NEXT_FAIL_CLOSED = "next_gate_fail_closed_forbidden_value"

TRUTH_CLASS = "remote_loop_truth_ledger_count_3_exact_test4_accepted"
NEXT_ALLOWED_ACTION = "prepare_next_manual_gate_candidate"
NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174VO_VP_VQ_TELEGRAM_REMOTE_OPERATOR_LOOP_NEXT_MANUAL_"
    "GATE_PACKET_FROM_LEDGER3_BATCH_V0"
)


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


def _proof_to_evidence(proof):
    p = proof or {}
    ev = {
        "task_label": p.get("task_label"),
        "provider": p.get("provider") or adapter.PROVIDER_TELEGRAM,
        "method_name": p.get("method_name") or adapter.METHOD_SUPERVISED_SEND,
        "live_test_sequence": p.get("live_test_sequence"),
        "credential_source_class": "operator_local_dotenv_file",
        "destination_source_class": "operator_local_dotenv_test_channel",
        "destination_binding_checksum": p.get("destination_binding_checksum"),
        "credential_handle_id": p.get("credential_handle_id"),
        "send_text_checksum": p.get("rebuilt_send_text_checksum") or p.get("approved_payload_checksum"),
        "request_checksum": p.get("request_checksum") or p.get("candidate_evidence_checksum"),
        "response_checksum": p.get("response_checksum"),
        "response_shape_checksum": p.get("response_shape_checksum"),
        "send_outcome_class": p.get("send_outcome_class"),
        "send_succeeded": p.get("send_succeeded"),
        "provider_status_code_class": p.get("provider_status_code_class"),
        "response_status_class": p.get("response_status_class"),
        "redacted_message_id_class": p.get("redacted_message_id_class"),
        "request_budget_used": p.get("request_budget_used"),
    }
    ev["evidence_checksum"] = p.get("final_evidence_checksum") or compute_checksum(ev)
    return ev


def _entry_from_proof(proof):
    ev = _proof_to_evidence(proof)
    entry = ledger.build_ledger_entry(ev, operator_gate_id="exact_test4_operator_gate")
    p = proof or {}
    entry["ledger_entry_checksum"] = p.get("new_ledger_entry_checksum")
    entry["exact_run_replay_key"] = p.get("exact_run_replay_key") or entry.get("exact_run_replay_key")
    entry["stable_payload_replay_key"] = p.get("stable_payload_replay_key") or entry.get("stable_payload_replay_key")
    entry["operator_gate_id"] = None
    entry["operator_gate_id_hash_present"] = bool(p.get("operator_gate_id_hash_present"))
    entry["operator_gate_class"] = p.get("operator_gate_class")
    return entry


def reconcile_exact_test4_send_proof(exact_test4_send_proof, previous_loop_state=None):
    p = exact_test4_send_proof or {}
    blockers = []
    forbidden = bool(scan(p))
    if forbidden:
        outcome = RECONCILE_FAIL_CLOSED
    elif not p:
        outcome = RECONCILE_MISSING
    elif p.get("real_send_attempted") is not True or p.get("send_succeeded") is not True:
        outcome = RECONCILE_SEND_NOT_SUCCEEDED
    elif p.get("manual_gate_revalidated") is not True:
        outcome = RECONCILE_GATE_NOT_REVALIDATED
    elif not (p.get("ledger_appended") is True and p.get("ledger_entry_count_before") == 2
              and p.get("ledger_entry_count") == 3 and p.get("request_budget_used") == 1):
        outcome = RECONCILE_LEDGER_NOT_ADVANCED
    elif not (p.get("old_ledger_manifest_checksum") and p.get("new_ledger_manifest_checksum")
              and p.get("old_ledger_manifest_checksum") != p.get("new_ledger_manifest_checksum")):
        outcome = RECONCILE_MANIFEST_NOT_ADVANCED
    elif not (p.get("response_checksum") and p.get("response_shape_checksum")):
        outcome = RECONCILE_LEDGER_NOT_ADVANCED
    else:
        outcome = RECONCILE_OK
    if outcome != RECONCILE_OK:
        blockers.append(outcome)
    result = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": adapter.Status.PASS if outcome == RECONCILE_OK else adapter.Status.BLOCKED,
        "provider": p.get("provider") or adapter.PROVIDER_TELEGRAM,
        "reconciliation_outcome_class": outcome,
        "reconciled": outcome == RECONCILE_OK,
        "blocker_stack": blockers,
        "exact_test4_proof_checksum": p.get("evidence_checksum") or compute_checksum(p) if p else None,
        "previous_loop_state_checksum": (previous_loop_state or {}).get("remote_loop_state_checksum"),
        "ledger_entry_count_before": p.get("ledger_entry_count_before"),
        "ledger_entry_count": p.get("ledger_entry_count"),
        "old_ledger_manifest_checksum": p.get("old_ledger_manifest_checksum"),
        "new_ledger_manifest_checksum": p.get("new_ledger_manifest_checksum"),
        "new_ledger_entry_checksum": p.get("new_ledger_entry_checksum"),
        "response_checksum": p.get("response_checksum"),
        "response_shape_checksum": p.get("response_shape_checksum"),
        "forbidden_fields_detected": forbidden,
        **_safety_flags(),
    }
    result["reconciliation_checksum"] = compute_checksum(result)
    return result


def build_remote_operator_loop_state(exact_test4_send_proof, exact_test4_gate_packet,
                                     previous_ledger_packet=None,
                                     previous_success_proofs=None):
    proof = exact_test4_send_proof or {}
    gate_packet = exact_test4_gate_packet or {}
    reconciliation = reconcile_exact_test4_send_proof(proof)
    reconciled = reconciliation.get("reconciled") is True
    entry = _entry_from_proof(proof) if proof else {}
    previous_entry_checksum = proof.get("previous_ledger_entry_checksum")
    audit_refs = {
        "exact_test4_send_proof_checksum": proof.get("evidence_checksum") or compute_checksum(proof) if proof else None,
        "exact_test4_gate_artifact_checksum": gate_packet.get("artifact_packet_checksum"),
        "exact_test4_manual_gate_packet_checksum": proof.get("manual_gate_packet_checksum"),
        "previous_ledger_packet_checksum": (previous_ledger_packet or {}).get(
            "ledger_packet_checksum") or (previous_ledger_packet or {}).get("artifact_packet_checksum"),
        "previous_success_proof_count": len(previous_success_proofs or []),
    }
    state = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": adapter.Status.PASS if reconciled else adapter.Status.BLOCKED,
        "provider": proof.get("provider") or adapter.PROVIDER_TELEGRAM,
        "reconciliation_outcome_class": reconciliation.get("reconciliation_outcome_class"),
        "reconciled": reconciled,
        "current_ledger_count": proof.get("ledger_entry_count") if reconciled else None,
        "current_ledger_manifest_checksum": proof.get("new_ledger_manifest_checksum"),
        "previous_ledger_manifest_checksum": proof.get("old_ledger_manifest_checksum"),
        "current_ledger_entry_checksum": proof.get("new_ledger_entry_checksum"),
        "previous_ledger_entry_checksum": previous_entry_checksum,
        "last_successful_send_sequence": proof.get("live_test_sequence") if reconciled else None,
        "last_successful_send_outcome_class": proof.get("send_outcome_class"),
        "last_response_checksum": proof.get("response_checksum"),
        "last_response_shape_checksum": proof.get("response_shape_checksum"),
        "last_manual_gate_packet_checksum": proof.get("manual_gate_packet_checksum"),
        "last_manual_gate_revalidated": proof.get("manual_gate_revalidated"),
        "last_operator_approval_outcome_class": proof.get("operator_approval_outcome_class"),
        "current_stable_payload_replay_key": entry.get("stable_payload_replay_key"),
        "current_exact_run_replay_key": entry.get("exact_run_replay_key"),
        "replay_guard_current_truth_class": TRUTH_CLASS if reconciled else "remote_loop_truth_unreconciled",
        "next_allowed_action": NEXT_ALLOWED_ACTION if reconciled else "reconcile_remote_loop_before_next_gate",
        "blocker_stack": reconciliation.get("blocker_stack"),
        "audit_refs": audit_refs,
        "accepted_ledger_entry": entry,
        "reconciliation_checksum": reconciliation.get("reconciliation_checksum"),
        **_safety_flags(),
    }
    state["remote_loop_state_checksum"] = compute_checksum(state)
    return state


def _entries_from_loop_state(remote_loop_state):
    s = remote_loop_state or {}
    entry = s.get("accepted_ledger_entry") or {}
    return [entry] if entry.get("ledger_entry_checksum") else []


def build_next_gate_precheck_state(remote_loop_state, candidate_evidence_packet=None,
                                   fresh_operator_gate_id=None):
    s = remote_loop_state or {}
    candidate = candidate_evidence_packet or None
    forbidden = bool(scan(s)) or (candidate is not None and bool(scan(candidate)))
    if forbidden:
        outcome = NEXT_FAIL_CLOSED
        guard_state = {}
        blockers = [NEXT_FAIL_CLOSED]
    elif s.get("reconciled") is not True:
        outcome = NEXT_BLOCKED_UNRECONCILED
        guard_state = {}
        blockers = [NEXT_BLOCKED_UNRECONCILED]
    elif candidate is None:
        outcome = NEXT_WAITING
        guard_state = {}
        blockers = []
    else:
        guard_state = ledger.build_replay_guard_state(
            _entries_from_loop_state(s), candidate,
            operator_gate_id=fresh_operator_gate_id)
        guard_outcome = guard_state.get("replay_guard_outcome_class")
        if guard_outcome == ledger.REPLAY_BLOCKED_EXACT:
            outcome = NEXT_BLOCKED_EXACT
        elif guard_outcome == ledger.REPLAY_REQUIRES_FRESH_GATE:
            outcome = NEXT_REQUIRES_FRESH_GATE
        elif guard_outcome == ledger.REPLAY_CLEAR:
            outcome = NEXT_CLEAR
        elif guard_outcome == ledger.REPLAY_FAIL_CLOSED:
            outcome = NEXT_FAIL_CLOSED
        else:
            outcome = NEXT_BLOCKED_UNRECONCILED
        blockers = [] if outcome in (NEXT_WAITING, NEXT_CLEAR) else [outcome]
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": adapter.Status.PASS if outcome == NEXT_CLEAR else (
            adapter.Status.FAIL_CLOSED if outcome == NEXT_FAIL_CLOSED else adapter.Status.BLOCKED),
        "provider": s.get("provider") or adapter.PROVIDER_TELEGRAM,
        "next_gate_outcome_class": outcome,
        "candidate_present": candidate is not None,
        "fresh_operator_gate_present": bool(fresh_operator_gate_id),
        "remote_loop_reconciled": s.get("reconciled") is True,
        "remote_loop_state_checksum": s.get("remote_loop_state_checksum"),
        "replay_guard_outcome_class": guard_state.get("replay_guard_outcome_class"),
        "exact_run_replay_key": guard_state.get("exact_run_replay_key"),
        "stable_payload_replay_key": guard_state.get("stable_payload_replay_key"),
        "blocker_stack": blockers,
        "classified_live_ready": False,
        "classified_auto_send_ready": False,
        "requires_manual_gate_packet_builder": outcome == NEXT_CLEAR,
        **_safety_flags(),
    }
    packet["next_gate_precheck_checksum"] = compute_checksum(packet)
    return packet


def _candidate_from_proof(proof, *, sequence=None, response_suffix=None):
    p = proof or {}
    ev = _proof_to_evidence(p)
    if sequence is not None:
        ev["live_test_sequence"] = sequence
    if response_suffix:
        ev["response_checksum"] = compute_checksum({
            "kind": "new_candidate_response_placeholder",
            "suffix": response_suffix,
            "source": ev.get("response_checksum"),
        })
    ev["evidence_checksum"] = compute_checksum(ev)
    return ev


def _new_payload_candidate_from_proof(proof):
    ev = _candidate_from_proof(proof, sequence=5, response_suffix="new_payload")
    ev["send_text_checksum"] = compute_checksum({
        "kind": "remote_loop_new_payload_example",
        "source": ev.get("send_text_checksum"),
    })
    ev["evidence_checksum"] = compute_checksum(ev)
    return ev


def build_artifact_packet(exact_test4_send_proof, exact_test4_gate_packet,
                          previous_ledger_packet=None, previous_success_proofs=None):
    proof = exact_test4_send_proof or {}
    state = build_remote_operator_loop_state(
        proof, exact_test4_gate_packet,
        previous_ledger_packet=previous_ledger_packet,
        previous_success_proofs=previous_success_proofs)
    exact_replay_candidate = _candidate_from_proof(proof)
    same_payload_candidate = _candidate_from_proof(proof, sequence=5, response_suffix="same_payload")
    new_payload_candidate = _new_payload_candidate_from_proof(proof)
    examples = {
        "no_candidate": build_next_gate_precheck_state(state),
        "exact_replay": build_next_gate_precheck_state(
            state, exact_replay_candidate, fresh_operator_gate_id="exact_test4_operator_gate"),
        "same_payload_without_gate": build_next_gate_precheck_state(
            state, same_payload_candidate, fresh_operator_gate_id=None),
        "same_payload_with_fresh_gate": build_next_gate_precheck_state(
            state, same_payload_candidate, fresh_operator_gate_id="fresh_next_gate"),
        "new_payload_with_fresh_gate": build_next_gate_precheck_state(
            state, new_payload_candidate, fresh_operator_gate_id="fresh_next_gate"),
    }
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": adapter.Status.PASS,
        "provider": proof.get("provider") or adapter.PROVIDER_TELEGRAM,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "exact_test4_proof_checksum": proof.get("evidence_checksum") or compute_checksum(proof) if proof else None,
        "exact_test4_gate_checksum": (exact_test4_gate_packet or {}).get("artifact_packet_checksum"),
        "reconciliation_outcome_class": state.get("reconciliation_outcome_class"),
        "current_ledger_count": state.get("current_ledger_count"),
        "last_successful_send_sequence": state.get("last_successful_send_sequence"),
        "last_response_checksum": state.get("last_response_checksum"),
        "old_ledger_manifest_checksum": state.get("previous_ledger_manifest_checksum"),
        "new_ledger_manifest_checksum": state.get("current_ledger_manifest_checksum"),
        "remote_loop_state": state,
        "next_gate_examples": examples,
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        **_safety_flags(),
    }
    packet["artifact_packet_checksum"] = compute_checksum(packet)
    return packet


def build_artifact_doc(packet):
    state = packet.get("remote_loop_state") or {}
    examples = packet.get("next_gate_examples") or {}
    def ex(name):
        return (examples.get(name) or {}).get("next_gate_outcome_class")
    return (
        "# 0174VL/VM/VN Telegram Remote Operator Loop State\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        "## Reconciliation\n\n"
        f"- Outcome: `{packet['reconciliation_outcome_class']}`\n"
        f"- Current ledger count: `{packet['current_ledger_count']}`\n"
        f"- Last successful send sequence: `{packet['last_successful_send_sequence']}`\n"
        f"- Old manifest checksum: `{packet['old_ledger_manifest_checksum']}`\n"
        f"- New manifest checksum: `{packet['new_ledger_manifest_checksum']}`\n"
        f"- Remote loop state checksum: `{state.get('remote_loop_state_checksum')}`\n"
        f"- Last response checksum: `{packet['last_response_checksum']}`\n\n"
        "## Next gate examples\n\n"
        f"- No candidate: `{ex('no_candidate')}`\n"
        f"- Exact replay: `{ex('exact_replay')}`\n"
        f"- Same payload without gate: `{ex('same_payload_without_gate')}`\n"
        f"- Same payload with fresh gate: `{ex('same_payload_with_fresh_gate')}`\n"
        f"- New payload with fresh gate: `{ex('new_payload_with_fresh_gate')}`\n\n"
        "## Safety proofs\n\n"
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


def load_packet(packet_path):
    try:
        with open(packet_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def build_artifact_from_repo(repo_root):
    root = os.path.abspath(repo_root)
    exact_proof = load_packet(os.path.join(root, EXACT_PROOF_REL))
    exact_gate = load_packet(os.path.join(root, EXACT_GATE_REL))
    previous_ledger = load_packet(os.path.join(root, LEDGER_PACKET_REL))
    third_proof = load_packet(os.path.join(root, THIRD_PROOF_REL))
    return build_artifact_packet(
        exact_proof, exact_gate,
        previous_ledger_packet=previous_ledger,
        previous_success_proofs=[third_proof])


def write_artifacts(base_dir, packet, doc):
    violations = scan_artifact(packet, doc)
    if violations:
        raise RuntimeError(
            "refusing to write remote loop artifacts: scan found %d violation(s)" % len(violations))
    out_dir = os.path.join(base_dir, DOC_REL_DIR)
    os.makedirs(out_dir, exist_ok=True)
    packet_path = os.path.join(out_dir, PACKET_FILENAME)
    doc_path = os.path.join(out_dir, DOC_FILENAME)
    with open(packet_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(serialize(packet))
    with open(doc_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(doc)
    return [packet_path, doc_path]


def _repo_root_from_module():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def main(argv=None):
    root = _repo_root_from_module()
    packet = build_artifact_from_repo(root)
    doc = build_artifact_doc(packet)
    written = write_artifacts(root, packet, doc)
    print("TASK " + TASK_LABEL)
    print("RECONCILIATION " + str(packet["reconciliation_outcome_class"]))
    print("CURRENT_LEDGER_COUNT " + str(packet["current_ledger_count"]))
    print("LAST_SUCCESSFUL_SEND_SEQUENCE " + str(packet["last_successful_send_sequence"]))
    print("REMOTE_LOOP_STATE_CHECKSUM " + str(packet["remote_loop_state"].get("remote_loop_state_checksum")))
    for name, state in sorted((packet.get("next_gate_examples") or {}).items()):
        print("NEXT_GATE " + name + " " + str(state.get("next_gate_outcome_class")))
    print("EVIDENCE_SCAN_CLEAN")
    for path in written:
        print("WROTE " + path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
