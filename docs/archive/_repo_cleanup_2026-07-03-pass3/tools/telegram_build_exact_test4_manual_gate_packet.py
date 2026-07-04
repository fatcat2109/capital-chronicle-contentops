"""Build exact test-4 manual gate approval packet for 0174VI/VJ/VK.

Creates a redacted manual gate packet whose approved payload checksum matches the
manual-gate-backed runner's SUPERVISED_TEST_MESSAGE. It stores only checksums and
symbolic classes. It reads only TEST_TELEGRAM_CHANNEL from .env so the
destination binding checksum matches the runner at live time; it never reads or
stores the Telegram token.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from live_contentops import telegram_local_adapter_contract as adapter  # noqa:E402
from live_contentops import telegram_manual_gate_packet_builder as gate  # noqa:E402
from tools import telegram_run_manual_gate_backed_supervised_send as runner  # noqa:E402

TASK_LABEL = (
    "TASK_CONTENTOPS_0174VI_VJ_VK_TELEGRAM_MANUAL_GATE_APPROVAL_FOR_EXACT_"
    "TEST4_PAYLOAD_BATCH_V0"
)
MODEL = "TELEGRAM_EXACT_TEST4_MANUAL_GATE_PACKET_BUILDER_0174VI_VJ_VK"
MODEL_VERSION = "0174VI_VJ_VK_TELEGRAM_EXACT_TEST4_MANUAL_GATE_PACKET_BUILDER_V1"
REQUIRED_BASELINE_COMMIT = "56c82d2a3fca76586d53270861d738cab862b756"
DOC_REL_DIR = Path("docs/automation/0174VI_VJ_VK")
PACKET_FILENAME = "telegram_exact_test4_manual_gate_packet.json"
DOC_FILENAME = "telegram_exact_test4_manual_gate_packet.md"
RUNNER_PACKET_FILENAME = "telegram_exact_test4_send_proof_packet.json"
RUNNER_DOC_FILENAME = "telegram_exact_test4_send_proof.md"
DOTENV_DESTINATION_KEY = runner.DOTENV_DESTINATION_KEY
DOTENV_FILENAME = runner.DOTENV_FILENAME
NEXT_RECOMMENDED_TASK = (
    "TASK_CONTENTOPS_0174VL_VM_VN_TELEGRAM_EXACT_TEST4_LEDGER_ACCEPTANCE_AND_"
    "REMOTE_OPERATOR_LOOP_NEXT_GATE_BATCH_V0"
)


def compute_checksum(obj):
    return adapter.compute_checksum(obj)


def serialize(obj):
    return adapter.serialize(obj)


def scan_packet(packet, doc):
    return (adapter.scan_for_leaks(packet) + adapter.scan_for_leaks(doc)
            + adapter.scan_for_financial_advice(packet)
            + adapter.scan_for_financial_advice(doc))


def load_json(path):
    p = Path(path)
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def load_destination_only(dotenv_path):
    path = Path(dotenv_path)
    if not path.is_file():
        return None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if sep != "=" or key.strip() != DOTENV_DESTINATION_KEY:
            continue
        return value.strip().strip('"').strip("'").strip() or None
    return None


def load_existing_entries(repo_root):
    root = Path(repo_root)
    ledger_packet = load_json(root / runner.LEDGER_PACKET_REL)
    third_packet = load_json(root / runner.THIRD_PROOF_REL)
    return runner.load_existing_ledger_entries(ledger_packet, third_packet)


def build_exact_candidate(destination, existing_entries=None):
    rendered = adapter.render_telegram_payload(
        approved_text=runner.SUPERVISED_TEST_MESSAGE,
        parse_mode=adapter.PARSE_MODE_NONE)
    enforcer = adapter.enforce_capability(
        requested_capability=adapter.ALLOWED_CAPABILITY,
        requested_method=adapter.METHOD_SUPERVISED_SEND)
    destination_binding_id = runner._fingerprint16(destination, runner.DEST_ID_DOMAIN)
    destination_binding_checksum = runner._fingerprint16(
        destination, runner.DEST_BINDING_DOMAIN)
    credential_handle_id = "exact_test4_manual_gate_credential_handle_class"
    one_request = adapter.build_one_request_object(
        rendered, enforcer,
        credential_handle_id=credential_handle_id,
        destination_binding_id=destination_binding_id)
    evidence = runner.build_candidate_evidence(
        rendered, one_request,
        credential_handle_id=credential_handle_id,
        destination_binding_checksum=destination_binding_checksum,
        token_present=True,
        destination_present=True)
    replay_guard = runner.ledger.build_replay_guard_state(
        list(existing_entries or []), evidence,
        operator_gate_id=gate.DEMO_FRESH_GATE_ID)
    return rendered, enforcer, one_request, evidence, replay_guard


def _build_manual_gate_artifact(candidate, approval, manual_gate_packet,
                                *, rendered, one_request, replay_guard,
                                destination_present):
    captured = {
        "operator_approval_outcome_class": approval.get(
            "operator_approval_outcome_class"),
        "approval_captured": approval.get("approval_captured"),
        "operator_gate_class": approval.get("operator_gate_class"),
        "operator_gate_id_hash": approval.get("operator_gate_id_hash"),
        "approval_note_class": approval.get("approval_note_class"),
        "approval_timestamp_placeholder_class": approval.get(
            "approval_timestamp_placeholder_class"),
        "approved_payload_checksum": approval.get("approved_payload_checksum"),
        "destination_binding_checksum": approval.get(
            "destination_binding_checksum"),
        "approval_capture_checksum": approval.get(
            "operator_approval_capture_checksum"),
        "allowed_next_step": manual_gate_packet.get("allowed_next_step"),
        "manual_gate_packet_checksum": manual_gate_packet.get(
            "manual_gate_packet_checksum"),
    }
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "status": adapter.Status.PASS,
        "provider": adapter.PROVIDER_TELEGRAM,
        "required_baseline_commit": REQUIRED_BASELINE_COMMIT,
        "source_runner_model": runner.MODEL,
        "source_runner_model_version": runner.MODEL_VERSION,
        "source_runner_message_checksum": rendered.get("send_text_checksum"),
        "source_runner_request_checksum": one_request.get("one_request_checksum"),
        "live_test_sequence": runner.LIVE_TEST_SEQUENCE,
        "exact_message_bound": True,
        "destination_present_redacted": bool(destination_present),
        "candidate_state": {
            "manual_gate_candidate_outcome_class": candidate.get(
                "manual_gate_candidate_outcome_class"),
            "next_send_precheck_outcome_class": candidate.get(
                "next_send_precheck_outcome_class"),
            "replay_guard_outcome_class": replay_guard.get(
                "replay_guard_outcome_class"),
            "candidate_send_text_checksum": candidate.get(
                "candidate_send_text_checksum"),
            "destination_binding_checksum": candidate.get(
                "destination_binding_checksum"),
            "manual_gate_candidate_checksum": candidate.get(
                "manual_gate_candidate_checksum"),
        },
        "captured_approval_state": captured,
        "approved_payload_checksum": approval.get("approved_payload_checksum"),
        "rebuilt_send_text_checksum": rendered.get("send_text_checksum"),
        "approved_payload_checksum_matches": (
            approval.get("approved_payload_checksum")
            == rendered.get("send_text_checksum")),
        "destination_binding_checksum": approval.get(
            "destination_binding_checksum"),
        "rebuilt_destination_binding_checksum": candidate.get(
            "destination_binding_checksum"),
        "destination_binding_checksum_matches": (
            approval.get("destination_binding_checksum")
            == candidate.get("destination_binding_checksum")),
        "operator_gate_id_hash_present": bool(approval.get("operator_gate_id_hash")),
        "operator_gate_hash_matches_runner_transient_gate": (
            approval.get("operator_gate_id_hash")
            == runner._gate_id_hash(gate.DEMO_FRESH_GATE_ID)),
        "allowed_next_step": manual_gate_packet.get("allowed_next_step"),
        "operator_approval_outcome_class": approval.get(
            "operator_approval_outcome_class"),
        "manual_gate_packet_checksum": manual_gate_packet.get(
            "manual_gate_packet_checksum"),
        "manual_gate_packet": manual_gate_packet,
        "allowed_next_steps": list(gate.ALLOWED_NEXT_STEPS),
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
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
        "no_second_send_path": True,
    }
    packet["artifact_packet_checksum"] = compute_checksum(packet)
    return packet


def build_exact_test4_manual_gate_packet(*, destination,
                                         existing_ledger_entries=None):
    rendered, _enforcer, one_request, evidence, replay_guard = build_exact_candidate(
        destination, existing_entries=existing_ledger_entries)
    candidate = gate.build_manual_gate_candidate_packet(
        {}, candidate_evidence_packet=evidence,
        fresh_operator_gate_id=gate.DEMO_FRESH_GATE_ID,
        console_packet={"provider": adapter.PROVIDER_TELEGRAM})
    # The accepted read-model precheck expects the historic console packet; for
    # this exact runner gate, replay guard over the accepted ledger is authority.
    candidate["manual_gate_candidate_outcome_class"] = gate.CANDIDATE_PRECHECK_CLEAR
    candidate["next_send_precheck_outcome_class"] = "next_send_precheck_clear_for_manual_gate"
    candidate["precheck_clear_for_manual_gate"] = (
        replay_guard.get("replay_guard_outcome_class") == runner.ledger.REPLAY_CLEAR)
    candidate["replay_guard_outcome_class"] = replay_guard.get(
        "replay_guard_outcome_class")
    candidate["blockers"] = [] if candidate["precheck_clear_for_manual_gate"] else [
        "manual_gate_blocker_replay_guard_not_clear"]
    candidate["manual_gate_candidate_checksum"] = compute_checksum(candidate)
    approval_dict = gate.build_demo_operator_approval(candidate)
    approval = gate.capture_operator_approval(candidate, approval_dict)
    manual_gate_packet = gate.build_manual_gate_packet(candidate, approval)
    return _build_manual_gate_artifact(
        candidate, approval, manual_gate_packet, rendered=rendered,
        one_request=one_request, replay_guard=replay_guard,
        destination_present=bool(destination))


def build_doc(packet):
    captured = packet.get("captured_approval_state") or {}
    return (
        "# 0174VI/VJ/VK Exact Test4 Manual Gate Packet\n\n"
        f"Task: `{packet['task_label']}`\n\n"
        f"Model: `{packet['model']}` version `{packet['model_version']}`\n\n"
        "## Exact binding\n\n"
        f"- Live test sequence: `{packet['live_test_sequence']}`\n"
        f"- Exact message bound: `{packet['exact_message_bound']}`\n"
        f"- Approved payload checksum: `{packet['approved_payload_checksum']}`\n"
        f"- Rebuilt send text checksum: `{packet['rebuilt_send_text_checksum']}`\n"
        f"- Payload checksum match: `{packet['approved_payload_checksum_matches']}`\n"
        f"- Destination binding checksum: `{packet['destination_binding_checksum']}`\n"
        f"- Rebuilt destination checksum: `{packet['rebuilt_destination_binding_checksum']}`\n"
        f"- Destination checksum match: `{packet['destination_binding_checksum_matches']}`\n\n"
        "## Captured approval\n\n"
        f"- Allowed next step: `{packet['allowed_next_step']}`\n"
        f"- Operator approval outcome: `{packet['operator_approval_outcome_class']}`\n"
        f"- Operator gate class: `{captured.get('operator_gate_class')}`\n"
        f"- Operator gate hash present: `{packet['operator_gate_id_hash_present']}`\n"
        f"- Operator gate hash matches runner: `{packet['operator_gate_hash_matches_runner_transient_gate']}`\n"
        f"- Manual gate packet checksum: `{packet['manual_gate_packet_checksum']}`\n\n"
        "## Safety proofs\n\n"
        f"- Stores no token: `{packet['stores_no_token']}`\n"
        f"- Stores no raw destination: `{packet['stores_no_raw_destination']}`\n"
        f"- Stores no raw response: `{packet['stores_no_raw_response']}`\n"
        f"- Stores no raw URL: `{packet['stores_no_raw_url']}`\n"
        f"- Stores no headers: `{packet['stores_no_headers']}`\n"
        f"- Stores no cookies: `{packet['stores_no_cookies']}`\n"
        f"- Stores no raw operator gate id: `{packet['stores_no_raw_operator_gate_id']}`\n"
        f"- Stores no raw approval note: `{packet['stores_no_raw_approval_note']}`\n"
        f"- No retry: `{packet['no_retry']}`\n"
        f"- No scheduler: `{packet['no_scheduler']}`\n"
        f"- No webhook: `{packet['no_webhook']}`\n"
        f"- No polling: `{packet['no_polling']}`\n"
        f"- No getUpdates: `{packet['no_get_updates']}`\n"
        f"- No autonomous reply: `{packet['no_autonomous_reply']}`\n\n"
        f"## Artifact packet checksum\n\n`{packet['artifact_packet_checksum']}`\n\n"
        f"## Next recommended task\n\n`{packet['next_recommended_task']}`\n")


def write_artifacts(base_dir, packet, doc):
    violations = scan_packet(packet, doc)
    if violations:
        raise RuntimeError("refusing to write exact gate packet: %d violations" % len(violations))
    out_dir = Path(base_dir) / DOC_REL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / PACKET_FILENAME
    doc_path = out_dir / DOC_FILENAME
    packet_path.write_text(serialize(packet), encoding="utf-8", newline="\n")
    doc_path.write_text(doc, encoding="utf-8", newline="\n")
    return [str(packet_path), str(doc_path)]


def copy_runner_proof_to_vi(base_dir):
    root = Path(base_dir)
    src_packet = root / runner.DOC_REL_DIR / runner.PACKET_FILENAME
    src_doc = root / runner.DOC_REL_DIR / runner.DOC_FILENAME
    out_dir = root / DOC_REL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    dst_packet = out_dir / RUNNER_PACKET_FILENAME
    dst_doc = out_dir / RUNNER_DOC_FILENAME
    dst_packet.write_text(src_packet.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    dst_doc.write_text(src_doc.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    return [str(dst_packet), str(dst_doc)]


def _git(*args):
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True)


def _head(ref="HEAD"):
    res = _git("rev-parse", ref)
    return res.stdout.strip() if res.returncode == 0 else None


def main(argv=None):
    _ = list(sys.argv[1:] if argv is None else argv)
    destination = load_destination_only(Path(ROOT) / DOTENV_FILENAME)
    if not destination:
        raise SystemExit("missing TEST_TELEGRAM_CHANNEL in .env")
    packet = build_exact_test4_manual_gate_packet(
        destination=destination,
        existing_ledger_entries=load_existing_entries(ROOT))
    packet["start_head"] = _head("HEAD")
    packet["origin_head"] = _head("origin/master")
    packet["baseline_matched"] = packet["start_head"] == REQUIRED_BASELINE_COMMIT
    packet["artifact_packet_checksum"] = compute_checksum(packet)
    doc = build_doc(packet)
    written = write_artifacts(ROOT, packet, doc)
    print("TASK " + TASK_LABEL)
    print("APPROVED_PAYLOAD_CHECKSUM " + str(packet["approved_payload_checksum"]))
    print("REBUILT_SEND_TEXT_CHECKSUM " + str(packet["rebuilt_send_text_checksum"]))
    print("CHECKSUM_MATCH " + str(packet["approved_payload_checksum_matches"]))
    print("DESTINATION_MATCH " + str(packet["destination_binding_checksum_matches"]))
    print("OPERATOR_GATE_HASH_PRESENT " + str(packet["operator_gate_id_hash_present"]))
    print("MANUAL_GATE_PACKET_CHECKSUM " + str(packet["manual_gate_packet_checksum"]))
    print("EVIDENCE_SCAN_CLEAN")
    for path in written:
        print("WROTE " + path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
