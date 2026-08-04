"""Dispatch outbox candidate contract (LOCAL, NO LIVE-READY STATE)."""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import dispatch_outbox_policy as policy
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XQ_XR_XS_DISPATCH_OUTBOX_CANDIDATE_CONTRACT_V0"
MODEL = "DISPATCH_OUTBOX_CANDIDATE_CONTRACT_0174XQ_XR_XS"
MODEL_VERSION = "0174XQ_XR_XS_DISPATCH_OUTBOX_CANDIDATE_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "2f80831bce881f26e6bff3109a4731aaaad3e167"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XQ_XR_XS")
LEDGER_DIR = os.path.join("docs", "automation", "0174XN_XO_XP")
CHALLENGE_DIR = os.path.join("docs", "automation", "0174XK_XL_XM")
WY_DIR = os.path.join("docs", "automation", "0174WY_WZ_XA")
OUTPUTS = "dispatch_outbox_candidate_fixture_outputs.json"
CONTRACT_PACKET = "dispatch_outbox_candidate_contract_packet.json"
CONTRACT_DOC = "dispatch_outbox_candidate_contract.md"
NEXT_PACKET = "next_dispatch_gate_matrix_contract_packet.json"
NEXT_DOC = "next_dispatch_gate_matrix_contract.md"
NEXT_BATCH_PROMPT = "TASK_CONTENTOPS_0174XT_XU_XV_DISPATCH_GATE_MATRIX_CONTRACT_V0"


def _read_json(repo_root, rel_path):
    p = pathlib.Path(repo_root) / rel_path
    if not p.exists():
        for archive_root in [
            "docs/archive/_repo_cleanup_2026-07-03-pass3",
            "docs/archive/_repo_cleanup_2026-07-03",
            "docs/archive/_repo_cleanup_2026-07-03-pass2",
        ]:
            cand = pathlib.Path(repo_root) / archive_root / rel_path
            if cand.exists():
                p = cand
                break
    return json.loads(p.read_text(encoding="utf-8"))


def load_inputs(repo_root="."):
    return {
        "ledger_contract": _read_json(repo_root, os.path.join(LEDGER_DIR, "approval_ledger_contract_packet.json")),
        "ledger_policy": _read_json(repo_root, os.path.join(LEDGER_DIR, "approval_ledger_policy_packet.json")),
        "responses": _read_json(repo_root, os.path.join(LEDGER_DIR, "approval_response_fixture_inputs.json")),
        "ledger_outputs": _read_json(repo_root, os.path.join(LEDGER_DIR, "approval_ledger_fixture_outputs.json")),
        "next_outbox": _read_json(repo_root, os.path.join(LEDGER_DIR, "next_dispatch_outbox_candidate_contract_packet.json")),
        "challenge_outputs": _read_json(repo_root, os.path.join(CHALLENGE_DIR, "approval_challenge_candidate_fixture_outputs.json")),
        "telegram_registry": _read_json(repo_root, os.path.join(WY_DIR, "telegram_supervised_dispatch_capability_registry_packet.json")),
        "platform_registry": _read_json(repo_root, os.path.join(WY_DIR, "platform_universe_registry_v2_packet.json")),
    }


def audit_hash_material(entry, idempotency_key, status, blocked_reasons, policy_packet):
    return {
        "source_approval_ledger_entry_id": entry.get("ledger_entry_id"),
        "source_challenge_candidate_id": entry.get("source_challenge_candidate_id"),
        "platform": entry.get("platform"),
        "payload_hash": entry.get("payload_hash"),
        "destination_binding_id": entry.get("destination_binding_id"),
        "credential_handle_id": entry.get("credential_handle_id"),
        "idempotency_key": idempotency_key,
        "status": status,
        "blocked_reasons": blocked_reasons,
        "policy_checksum": policy_packet["dispatch_outbox_policy_checksum"],
    }


def compute_audit_hash(entry, idempotency_key, status, blocked_reasons, policy_packet):
    return adapter.compute_checksum(audit_hash_material(entry, idempotency_key, status, blocked_reasons, policy_packet))


def build_record(entry, status, blocked_reasons, duplicate_status, policy_packet):
    idempotency_key = policy.compute_idempotency_key(entry) if entry.get("ledger_entry_id") else None
    eligible = status == "candidate"
    record = {
        "outbox_candidate_id": f"outbox_{entry.get('ledger_entry_id')}_{status}",
        "source_approval_ledger_entry_id": entry.get("ledger_entry_id"),
        "source_challenge_candidate_id": entry.get("source_challenge_candidate_id"),
        "source_payload_id": entry.get("source_payload_id"),
        "source_brief_id": entry.get("source_brief_id"),
        "source_intent_id": entry.get("source_intent_id"),
        "platform": entry.get("platform"),
        "payload_class": entry.get("payload_class"),
        "payload_hash": entry.get("payload_hash"),
        "payload_hash_short": entry.get("payload_hash_short"),
        "destination_binding_id": entry.get("destination_binding_id"),
        "credential_handle_id": entry.get("credential_handle_id"),
        "idempotency_key": idempotency_key,
        "idempotency_key_algorithm": "sha256",
        "dispatch_mode": "dry_run_candidate_only",
        "request_budget": 1,
        "auto_retry_allowed": False,
        "kill_switch_required": True,
        "credential_hydration_allowed": False,
        "platform_api_call_allowed": False,
        "live_dispatch_allowed": False,
        "status": status,
        "blocked_reasons": blocked_reasons,
        "duplicate_suppression_status": duplicate_status,
        "eligible_for_gate_matrix": eligible,
        "valid_for_dispatch": False,
        "can_dispatch": False,
        "provider_api_called": False,
        "platform_api_called": False,
        "live_post_performed": False,
        "evidence_refs": [entry.get("audit_hash")],
        "telegram_dispatch_status": "proven_frozen_no_send" if entry.get("platform") == "telegram" else None,
        "substack_dispatch_status": "manual_export_no_api" if entry.get("platform") == "substack" else None,
        "x_dispatch_status": "dry_run_no_api" if entry.get("platform") == "x" else None,
        **policy.safety_flags(),
    }
    record["audit_hash"] = compute_audit_hash(entry, idempotency_key, status, blocked_reasons, policy_packet)
    policy.validate_no_forbidden_material(record)
    return record


def _duplicate_probe(entry):
    duplicate = copy.deepcopy(entry)
    duplicate["ledger_entry_id"] = entry["ledger_entry_id"]
    return duplicate


def _invalid_probe(entry, field, value, suffix):
    invalid = copy.deepcopy(entry)
    invalid["ledger_entry_id"] = f"{entry['ledger_entry_id']}_{suffix}"
    invalid[field] = value
    return invalid


def build_records(ledger_outputs, policy_packet):
    seen = set()
    records = []
    for entry in ledger_outputs:
        status, reasons, duplicate_status = policy.classify_entry(entry, seen)
        if status == "candidate":
            seen.add(policy.compute_idempotency_key(entry))
        records.append(build_record(entry, status, reasons, duplicate_status, policy_packet))
    approved = next(e for e in ledger_outputs if e.get("eligible_for_outbox_candidate") is True)
    probes = [
        _duplicate_probe(approved),
        _invalid_probe(approved, "payload_hash", None, "missing_payload_hash"),
        _invalid_probe(approved, "destination_binding_id", None, "missing_destination"),
        _invalid_probe(approved, "destination_binding_id", "wrong_symbolic_binding", "wrong_destination"),
        _invalid_probe(approved, "credential_handle_id", None, "missing_credential"),
        _invalid_probe(approved, "credential_handle_id", "wrong_symbolic_credential", "wrong_credential"),
        _invalid_probe(approved, "platform", "linkedin", "unsupported_platform"),
    ]
    for probe in probes:
        status, reasons, duplicate_status = policy.classify_entry(probe, seen)
        if status == "candidate":
            seen.add(policy.compute_idempotency_key(probe))
        records.append(build_record(probe, status, reasons, duplicate_status, policy_packet))
    return records


def counts(records):
    return {
        "active_candidate_count": sum(1 for r in records if r["status"] == "candidate"),
        "blocked_candidate_count": sum(1 for r in records if r["status"] == "blocked"),
        "duplicate_suppressed_count": sum(1 for r in records if r["status"] == "duplicate_suppressed"),
    }


def build_contract_packet(inputs, records, policy_packet):
    c = counts(records)
    active = [r for r in records if r["status"] == "candidate"]
    proof_entry = active[0] if active else records[0]
    proof_source = {
        "platform": proof_entry["platform"],
        "payload_hash": proof_entry["payload_hash"],
        "destination_binding_id": proof_entry["destination_binding_id"],
        "credential_handle_id": proof_entry["credential_handle_id"],
        "ledger_entry_id": proof_entry["source_approval_ledger_entry_id"],
    }
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "approval_ledger_contract_checksum": inputs["ledger_contract"]["approval_ledger_contract_checksum"],
        "approval_ledger_policy_checksum": inputs["ledger_policy"]["approval_ledger_policy_checksum"],
        "next_dispatch_outbox_candidate_contract_checksum": inputs["next_outbox"]["next_dispatch_outbox_candidate_contract_checksum"],
        "telegram_dispatch_registry_checksum": inputs["telegram_registry"]["registry_checksum"],
        "platform_universe_registry_checksum": inputs["platform_registry"]["platform_universe_registry_checksum"],
        "candidate_output_count": len(records),
        **c,
        "idempotency_key_determinism_proof": policy.idempotency_determinism_proof(proof_source),
        "all_request_budget_one": all(r["request_budget"] == 1 for r in records),
        "all_auto_retry_false": all(r["auto_retry_allowed"] is False for r in records),
        "all_credential_hydration_false": all(r["credential_hydration_allowed"] is False for r in records),
        "all_platform_api_call_false": all(r["platform_api_call_allowed"] is False and r["platform_api_called"] is False for r in records),
        "all_live_dispatch_false": all(r["live_dispatch_allowed"] is False for r in records),
        "all_valid_for_dispatch_false": all(r["valid_for_dispatch"] is False for r in records),
        "all_can_dispatch_false": all(r["can_dispatch"] is False for r in records),
        "all_live_ready_state_false": all(r["live_ready_state_created"] is False for r in records),
        "telegram_dispatch_status": "proven_frozen_no_send",
        "substack_dispatch_status": "manual_export_no_api",
        "x_dispatch_status": "dry_run_no_api",
        "status": "pass",
    }
    packet["dispatch_outbox_candidate_fixture_outputs_checksum"] = adapter.compute_checksum(records)
    packet["dispatch_outbox_candidate_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def build_next_packet(contract_packet, policy_packet):
    packet = {
        "task_label": NEXT_BATCH_PROMPT,
        "model": "NEXT_DISPATCH_GATE_MATRIX_CONTRACT_0174XQ_XR_XS",
        "model_version": "0174XQ_XR_XS_NEXT_DISPATCH_GATE_MATRIX_CONTRACT_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "next_batch_prompt": NEXT_BATCH_PROMPT,
        "next_scope": "dispatch_gate_matrix_contract_local_only",
        "allowed_inputs": ["dispatch_outbox_candidate", "idempotency_key", "kill_switch_policy", "request_budget"],
        "forbidden_outputs": ["live_dispatch", "credential_hydration", "platform_api_call", "live_ready_state"],
        "dispatch_outbox_candidate_contract_checksum": contract_packet["dispatch_outbox_candidate_contract_checksum"],
        "dispatch_outbox_policy_checksum": policy_packet["dispatch_outbox_policy_checksum"],
        "dispatch_outbox_candidate_fixture_outputs_checksum": contract_packet["dispatch_outbox_candidate_fixture_outputs_checksum"],
    }
    packet["next_dispatch_gate_matrix_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", "", "> [!IMPORTANT]", "> Local dry-run dispatch outbox candidate contract only. No dispatch, credential hydration, platform/provider call, network, or live-ready state.", ""]
    for key in sorted(packet):
        value = packet[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def _assert_safe_output(repo_root, output_dir):
    root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(output_dir).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    if out != allowed:
        raise ValueError("unsafe_output_path_refused")
    return out


def write_artifacts(repo_root=".", output_dir=None):
    output_dir = output_dir or (pathlib.Path(repo_root) / DOC_REL_DIR)
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    policy_packet = policy.write_artifacts(repo_root)
    inputs = load_inputs(repo_root)
    records = build_records(inputs["ledger_outputs"], policy_packet)
    contract_packet = build_contract_packet(inputs, records, policy_packet)
    next_packet = build_next_packet(contract_packet, policy_packet)
    (out / OUTPUTS).write_text(adapter.serialize(records), encoding="utf-8", newline="\n")
    (out / CONTRACT_PACKET).write_text(adapter.serialize(contract_packet), encoding="utf-8", newline="\n")
    (out / CONTRACT_DOC).write_text(render_doc("Dispatch Outbox Candidate Contract", contract_packet), encoding="utf-8", newline="\n")
    (out / NEXT_PACKET).write_text(adapter.serialize(next_packet), encoding="utf-8", newline="\n")
    (out / NEXT_DOC).write_text(render_doc("Next Dispatch Gate Matrix Contract", next_packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"records": records, "contract_packet": contract_packet, "policy_packet": policy_packet, "next_packet": next_packet})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("DISPATCH_OUTBOX_CANDIDATE_CONTRACT_CHECKSUM", result["contract_packet"]["dispatch_outbox_candidate_contract_checksum"])
    print("DISPATCH_OUTBOX_POLICY_CHECKSUM", result["policy_packet"]["dispatch_outbox_policy_checksum"])
    print("DISPATCH_OUTBOX_CANDIDATE_FIXTURE_OUTPUTS_CHECKSUM", result["contract_packet"]["dispatch_outbox_candidate_fixture_outputs_checksum"])
    print("NEXT_DISPATCH_GATE_MATRIX_CONTRACT_CHECKSUM", result["next_packet"]["next_dispatch_gate_matrix_contract_checksum"])
