"""Dispatch gate matrix contract (LOCAL, NO DISPATCH)."""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import dispatch_gate_policy as policy
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XT_XU_XV_DISPATCH_GATE_MATRIX_CONTRACT_V0"
MODEL = "DISPATCH_GATE_MATRIX_CONTRACT_0174XT_XU_XV"
MODEL_VERSION = "0174XT_XU_XV_DISPATCH_GATE_MATRIX_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "bb68a171b5e1aa40c4d9ea9ecefd8f9d40de6aef"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XT_XU_XV")
OUTBOX_DIR = os.path.join("docs", "automation", "0174XQ_XR_XS")
LEDGER_DIR = os.path.join("docs", "automation", "0174XN_XO_XP")
WY_DIR = os.path.join("docs", "automation", "0174WY_WZ_XA")
OUTPUTS = "dispatch_gate_matrix_fixture_outputs.json"
CONTRACT_PACKET = "dispatch_gate_matrix_contract_packet.json"
CONTRACT_DOC = "dispatch_gate_matrix_contract.md"
NEXT_PACKET = "next_dispatch_audit_dry_run_contract_packet.json"
NEXT_DOC = "next_dispatch_audit_dry_run_contract.md"
NEXT_BATCH_PROMPT = "TASK_CONTENTOPS_0174XW_XX_XY_DISPATCH_AUDIT_DRY_RUN_CONTRACT_V0"


def _read_json(repo_root, rel_path):
    return json.loads((pathlib.Path(repo_root) / rel_path).read_text(encoding="utf-8"))


def load_inputs(repo_root="."):
    return {
        "outbox_contract": _read_json(repo_root, os.path.join(OUTBOX_DIR, "dispatch_outbox_candidate_contract_packet.json")),
        "outbox_policy": _read_json(repo_root, os.path.join(OUTBOX_DIR, "dispatch_outbox_policy_packet.json")),
        "outbox_outputs": _read_json(repo_root, os.path.join(OUTBOX_DIR, "dispatch_outbox_candidate_fixture_outputs.json")),
        "next_gate": _read_json(repo_root, os.path.join(OUTBOX_DIR, "next_dispatch_gate_matrix_contract_packet.json")),
        "ledger_contract": _read_json(repo_root, os.path.join(LEDGER_DIR, "approval_ledger_contract_packet.json")),
        "telegram_registry": _read_json(repo_root, os.path.join(WY_DIR, "telegram_supervised_dispatch_capability_registry_packet.json")),
        "platform_registry": _read_json(repo_root, os.path.join(WY_DIR, "platform_universe_registry_v2_packet.json")),
    }


def audit_hash_material(candidate, gate_results, overall_status, policy_packet):
    return {
        "source_outbox_candidate_id": candidate.get("outbox_candidate_id"),
        "source_approval_ledger_entry_id": candidate.get("source_approval_ledger_entry_id"),
        "platform": candidate.get("platform"),
        "payload_hash": candidate.get("payload_hash"),
        "idempotency_key": candidate.get("idempotency_key"),
        "overall_gate_status": overall_status,
        "gate_results": gate_results,
        "policy_checksum": policy_packet["dispatch_gate_policy_checksum"],
    }


def compute_audit_hash(candidate, gate_results, overall_status, policy_packet):
    return adapter.compute_checksum(audit_hash_material(candidate, gate_results, overall_status, policy_packet))


def blocked_reasons(candidate, gate_results, overall_status):
    reasons = list(candidate.get("blocked_reasons", []))
    if overall_status == "local_dry_run_gate_passed_not_live_ready":
        return reasons
    for name, result in gate_results.items():
        status = result.get("status")
        if status == "fail":
            reasons.append(f"{name}_failed")
        if status == "duplicate_suppressed":
            reasons.append("duplicate_suppressed")
    return sorted(set(reasons))


def build_matrix(candidate, policy_packet):
    gate_results = policy.evaluate_gates(candidate)
    overall = policy.overall_status(candidate, gate_results)
    matrix = {
        "gate_matrix_id": f"gate_{candidate.get('outbox_candidate_id')}",
        "source_outbox_candidate_id": candidate.get("outbox_candidate_id"),
        "source_approval_ledger_entry_id": candidate.get("source_approval_ledger_entry_id"),
        "platform": candidate.get("platform"),
        "payload_class": candidate.get("payload_class"),
        "payload_hash": candidate.get("payload_hash"),
        "payload_hash_short": candidate.get("payload_hash_short"),
        "destination_binding_id": candidate.get("destination_binding_id"),
        "credential_handle_id": candidate.get("credential_handle_id"),
        "idempotency_key": candidate.get("idempotency_key"),
        "gate_results": gate_results,
        "overall_gate_status": overall,
        "eligible_for_dispatch_audit_dry_run": overall == "local_dry_run_gate_passed_not_live_ready",
        "valid_for_live_dispatch": False,
        "can_dispatch": False,
        "live_ready_state_created": False,
        "blocked_reasons": blocked_reasons(candidate, gate_results, overall),
        "required_future_gates": policy.required_future_gates(),
        "evidence_refs": list(candidate.get("evidence_refs", [])) + [candidate.get("audit_hash")],
        **policy.safety_flags(),
    }
    matrix["audit_hash"] = compute_audit_hash(candidate, gate_results, overall, policy_packet)
    policy.validate_no_forbidden_material(matrix)
    return matrix


def _probe(candidate, field, value, suffix):
    item = copy.deepcopy(candidate)
    item["outbox_candidate_id"] = f"{candidate['outbox_candidate_id']}_{suffix}"
    item[field] = value
    return item


def build_matrices(outbox_outputs, policy_packet):
    matrices = [build_matrix(candidate, policy_packet) for candidate in outbox_outputs]
    active = next(c for c in outbox_outputs if c.get("status") == "candidate")
    probes = [
        _probe(active, "request_budget", 2, "wrong_request_budget"),
        _probe(active, "auto_retry_allowed", True, "auto_retry_true"),
        _probe(active, "destination_binding_id", "wrong_symbolic_binding", "wrong_destination"),
        _probe(active, "credential_handle_id", "wrong_symbolic_credential", "wrong_credential"),
    ]
    matrices.extend(build_matrix(probe, policy_packet) for probe in probes)
    return matrices


def counts(matrices):
    return {
        "matrix_result_count": len(matrices),
        "local_dry_run_gate_passed_count": sum(1 for m in matrices if m["overall_gate_status"] == "local_dry_run_gate_passed_not_live_ready"),
        "blocked_count": sum(1 for m in matrices if m["overall_gate_status"] == "blocked"),
        "duplicate_suppressed_count": sum(1 for m in matrices if m["overall_gate_status"] == "duplicate_suppressed"),
    }


def platform_capability_gate_statuses(matrices):
    statuses = {}
    for matrix in matrices:
        platform = matrix.get("platform")
        if platform in ["telegram", "x", "substack"]:
            statuses[platform] = matrix["gate_results"]["platform_capability_gate"]["status"]
    return statuses


def build_contract_packet(inputs, matrices, policy_packet):
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "dispatch_outbox_candidate_contract_checksum": inputs["outbox_contract"]["dispatch_outbox_candidate_contract_checksum"],
        "dispatch_outbox_policy_checksum": inputs["outbox_policy"]["dispatch_outbox_policy_checksum"],
        "next_dispatch_gate_matrix_contract_checksum": inputs["next_gate"]["next_dispatch_gate_matrix_contract_checksum"],
        "approval_ledger_contract_checksum": inputs["ledger_contract"]["approval_ledger_contract_checksum"],
        "telegram_dispatch_registry_checksum": inputs["telegram_registry"]["registry_checksum"],
        "platform_universe_registry_checksum": inputs["platform_registry"]["platform_universe_registry_checksum"],
        **counts(matrices),
        "platform_capability_gate_statuses": platform_capability_gate_statuses(matrices),
        "required_future_gates": policy.required_future_gates(),
        "all_valid_for_live_dispatch_false": all(m["valid_for_live_dispatch"] is False for m in matrices),
        "all_can_dispatch_false": all(m["can_dispatch"] is False for m in matrices),
        "all_live_ready_state_false": all(m["live_ready_state_created"] is False for m in matrices),
        "status": "pass",
    }
    packet["dispatch_gate_matrix_fixture_outputs_checksum"] = adapter.compute_checksum(matrices)
    packet["dispatch_gate_matrix_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def build_next_packet(contract_packet, policy_packet):
    packet = {
        "task_label": NEXT_BATCH_PROMPT,
        "model": "NEXT_DISPATCH_AUDIT_DRY_RUN_CONTRACT_0174XT_XU_XV",
        "model_version": "0174XT_XU_XV_NEXT_DISPATCH_AUDIT_DRY_RUN_CONTRACT_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "next_batch_prompt": NEXT_BATCH_PROMPT,
        "next_scope": "dispatch_audit_dry_run_contract_local_only",
        "allowed_inputs": ["dispatch_gate_matrix_result", "required_future_gates", "evidence_refs", "audit_hash"],
        "forbidden_outputs": ["live_dispatch", "credential_hydration", "platform_api_call", "live_ready_state"],
        "dispatch_gate_matrix_contract_checksum": contract_packet["dispatch_gate_matrix_contract_checksum"],
        "dispatch_gate_policy_checksum": policy_packet["dispatch_gate_policy_checksum"],
        "dispatch_gate_matrix_fixture_outputs_checksum": contract_packet["dispatch_gate_matrix_fixture_outputs_checksum"],
    }
    packet["next_dispatch_audit_dry_run_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", "", "> [!IMPORTANT]", "> Local dispatch gate matrix only. No dispatch, approval, credential hydration, platform/provider call, or live-ready state.", ""]
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
    matrices = build_matrices(inputs["outbox_outputs"], policy_packet)
    contract_packet = build_contract_packet(inputs, matrices, policy_packet)
    next_packet = build_next_packet(contract_packet, policy_packet)
    (out / OUTPUTS).write_text(adapter.serialize(matrices), encoding="utf-8", newline="\n")
    (out / CONTRACT_PACKET).write_text(adapter.serialize(contract_packet), encoding="utf-8", newline="\n")
    (out / CONTRACT_DOC).write_text(render_doc("Dispatch Gate Matrix Contract", contract_packet), encoding="utf-8", newline="\n")
    (out / NEXT_PACKET).write_text(adapter.serialize(next_packet), encoding="utf-8", newline="\n")
    (out / NEXT_DOC).write_text(render_doc("Next Dispatch Audit Dry Run Contract", next_packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"matrices": matrices, "contract_packet": contract_packet, "policy_packet": policy_packet, "next_packet": next_packet})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("DISPATCH_GATE_MATRIX_CONTRACT_CHECKSUM", result["contract_packet"]["dispatch_gate_matrix_contract_checksum"])
    print("DISPATCH_GATE_POLICY_CHECKSUM", result["policy_packet"]["dispatch_gate_policy_checksum"])
    print("DISPATCH_GATE_MATRIX_FIXTURE_OUTPUTS_CHECKSUM", result["contract_packet"]["dispatch_gate_matrix_fixture_outputs_checksum"])
    print("NEXT_DISPATCH_AUDIT_DRY_RUN_CONTRACT_CHECKSUM", result["next_packet"]["next_dispatch_audit_dry_run_contract_checksum"])
