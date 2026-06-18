"""Cockpit read model contract (LOCAL, READ-MODEL ONLY, NO DISPATCH)."""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import cockpit_read_model_policy as policy
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174YF_YG_YH_COCKPIT_READ_MODEL_CONTRACT_V0"
MODEL = "COCKPIT_READ_MODEL_CONTRACT_0174YF_YG_YH"
MODEL_VERSION = "0174YF_YG_YH_COCKPIT_READ_MODEL_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "ab91f3e7b2773b33301e7c05f5042196c762fd12"
DOC_REL_DIR = os.path.join("docs", "automation", "0174YF_YG_YH")
READ_MODEL_PACKET = "cockpit_read_model_packet.json"
READ_MODEL_DOC = "cockpit_read_model.md"
FIXTURE_OUTPUTS = "cockpit_read_model_fixture_outputs.json"
NEXT_PACKET = "next_static_cockpit_surface_contract_packet.json"
NEXT_DOC = "next_static_cockpit_surface_contract.md"
NEXT_BATCH_PROMPT = "TASK_CONTENTOPS_0174YI_YJ_YK_STATIC_COCKPIT_SURFACE_CONTRACT_V0"

PATHS = {
    "manual_surface": os.path.join("docs", "automation", "0174YC_YD_YE", "manual_export_review_surface_packet.json"),
    "manual_policy": os.path.join("docs", "automation", "0174YC_YD_YE", "manual_export_review_policy_packet.json"),
    "manual_outputs": os.path.join("docs", "automation", "0174YC_YD_YE", "manual_export_review_fixture_outputs.json"),
    "next_cockpit": os.path.join("docs", "automation", "0174YC_YD_YE", "next_cockpit_read_model_contract_packet.json"),
    "readiness": os.path.join("docs", "automation", "0174XZ_YA_YB", "supervised_dispatch_readiness_summary_packet.json"),
    "chain": os.path.join("docs", "automation", "0174XZ_YA_YB", "full_dry_run_chain_reconciliation_packet.json"),
    "audit_contract": os.path.join("docs", "automation", "0174XW_XX_XY", "dispatch_audit_dry_run_contract_packet.json"),
    "audit_outputs": os.path.join("docs", "automation", "0174XW_XX_XY", "dispatch_audit_dry_run_fixture_outputs.json"),
    "platform_registry": os.path.join("docs", "automation", "0174WY_WZ_XA", "platform_universe_registry_v2_packet.json"),
}

UPSTREAM_CHECKSUM_SOURCES = {
    "manual_export_review_surface_checksum": "manual_surface",
    "manual_export_review_policy_checksum": "manual_policy",
    "manual_export_review_fixture_outputs_checksum": "manual_surface",
    "next_cockpit_read_model_contract_checksum": "next_cockpit",
    "supervised_dispatch_readiness_summary_checksum": "readiness",
    "full_dry_run_chain_reconciliation_checksum": "chain",
    "dispatch_audit_dry_run_contract_checksum": "audit_contract",
    "dispatch_audit_dry_run_fixture_outputs_checksum": "audit_contract",
    "platform_universe_registry_checksum": "platform_registry",
}


def _read_json(repo_root, rel_path):
    return json.loads((pathlib.Path(repo_root) / rel_path).read_text(encoding="utf-8"))


def load_inputs(repo_root="."):
    return {name: _read_json(repo_root, rel_path) for name, rel_path in PATHS.items()}


def _audit_by_payload_hash(audit_outputs):
    index = {}
    for event in audit_outputs:
        payload_hash = event.get("payload_hash")
        if payload_hash and payload_hash not in index:
            index[payload_hash] = event
    return index


def _queue_item(surface_item, audit_event=None):
    payload_hash = surface_item["payload_hash"]
    item = {
        "item_id": f"cockpit_read_model_{surface_item['surface_item_id']}",
        "platform": surface_item["platform"],
        "payload_class": surface_item["payload_class"],
        "payload_hash": payload_hash,
        "payload_hash_short": surface_item.get("payload_hash_short", payload_hash[:12]),
        "review_status": surface_item.get("surface_status", "review_only"),
        "allowed_operator_action": surface_item.get("operator_action", "hold"),
        "forbidden_operator_actions": list(policy.FORBIDDEN_ACTIONS),
        "source_surface_item_id": surface_item.get("surface_item_id"),
        "source_payload_id": surface_item.get("payload_id"),
        "source_brief_id": surface_item.get("source_brief_id"),
        "source_intent_id": surface_item.get("source_intent_id"),
        "source_audit_event_id": audit_event.get("audit_event_id") if audit_event else None,
        "source_gate_matrix_id": audit_event.get("gate_matrix_result_id") if audit_event else None,
        "source_ledger_entry_id": audit_event.get("approval_ledger_entry_id") if audit_event else None,
        "source_notes": list(surface_item.get("source_notes", [])),
        "limitations": list(surface_item.get("limitations", [])),
        "evidence_refs": list(surface_item.get("evidence_refs", [])),
        "can_dispatch": False,
        "public_postable": False,
        "human_review_required": True,
        "no_financial_advice": True,
        "no_signal_language": True,
    }
    if audit_event and audit_event.get("audit_hash") and audit_event["audit_hash"] not in item["evidence_refs"]:
        item["evidence_refs"].append(audit_event["audit_hash"])
    policy.validate_no_forbidden_readiness_claims(item)
    policy.validate_no_forbidden_material(item)
    return item


def build_fixture_outputs(inputs):
    audit_by_hash = _audit_by_payload_hash(inputs["audit_outputs"])
    outputs = []
    for surface_item in inputs["manual_outputs"]:
        outputs.append(_queue_item(surface_item, audit_by_hash.get(surface_item.get("payload_hash"))))
    return outputs


def _upstream_checksums(inputs, policy_packet):
    checksums = {"cockpit_read_model_policy_checksum": policy_packet["cockpit_read_model_policy_checksum"]}
    for checksum_key, source_name in UPSTREAM_CHECKSUM_SOURCES.items():
        checksums[checksum_key] = inputs[source_name][checksum_key]
    return checksums


def _evidence_index(inputs, policy_packet):
    checksums = _upstream_checksums(inputs, policy_packet)
    return [
        {"stage": stage, "checksum": checksum}
        for stage, checksum in sorted(checksums.items())
    ]


def _payload_hash_index(queue_items):
    index = []
    for item in queue_items:
        index.append({
            "platform": item["platform"],
            "payload_class": item["payload_class"],
            "payload_hash": item["payload_hash"],
            "payload_hash_short": item["payload_hash_short"],
            "item_id": item["item_id"],
        })
    return index


def _audit_hash_index(inputs):
    return [
        {
            "audit_hash": event["audit_hash"],
            "payload_hash": event.get("payload_hash"),
            "platform": event.get("platform"),
            "payload_class": event.get("payload_class"),
        }
        for event in inputs["audit_outputs"]
        if event.get("audit_hash")
    ]


def _platform_counts(items):
    return {platform_name: sum(1 for item in items if item["platform"] == platform_name) for platform_name in policy.PLATFORMS}


def _action_counts(items):
    counts = {action: 0 for action in policy.ALLOWED_ACTIONS}
    for item in items:
        action = item["allowed_operator_action"]
        counts[action] = counts.get(action, 0) + 1
    return counts


def _blocked_live_dispatch_queue(readiness):
    blockers = list(readiness.get("live_blockers", []))
    rows = []
    for gate in policy.REQUIRED_FUTURE_GATES:
        rows.append({
            "blocker_id": f"blocked_live_dispatch_{gate}",
            "required_future_gate": gate,
            "status": "BLOCKED",
            "reason": next((b for b in blockers if gate.replace("_", " ")[:12] in b), "future gate missing"),
            "allowed_operator_action": "hold",
            "forbidden_operator_actions": list(policy.FORBIDDEN_ACTIONS),
            "can_dispatch": False,
            "public_postable": False,
            "human_review_required": True,
        })
    return rows


def build_read_model_packet(inputs, policy_packet, queue_items):
    readiness = inputs["readiness"]
    chain = inputs["chain"]
    manual_surface = inputs["manual_surface"]
    audit_contract = inputs["audit_contract"]
    manual_export_queue = [item for item in queue_items if item["platform"] == "substack"]
    x_preview_queue = [item for item in queue_items if item["platform"] == "x"]
    telegram_preview_queue = [item for item in queue_items if item["platform"] == "telegram"]
    blocked_queue = _blocked_live_dispatch_queue(readiness)
    evidence_index = _evidence_index(inputs, policy_packet)
    payload_hash_index = _payload_hash_index(queue_items)
    audit_hash_index = _audit_hash_index(inputs)
    packet = {
        "cockpit_read_model_id": "cockpit_read_model_0174YF_YG_YH",
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "readiness_class": policy.READINESS_CLASS,
        "local_governance_status": policy.LOCAL_GOVERNANCE_STATUS,
        "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
        "manual_export_status": policy.MANUAL_EXPORT_STATUS,
        "platform_statuses": copy.deepcopy(policy.PLATFORM_STATUSES),
        "operator_summary": {
            "first_safe_action": "review manual export queue, then inspect preview queues",
            "reviewable_now_count": len(queue_items),
            "blocked_live_dispatch_count": len(blocked_queue),
            "next_builder_task": NEXT_BATCH_PROMPT,
        },
        "blocker_summary": {
            "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
            "blocked_reasons": list(manual_surface.get("blocked_live_dispatch_reasons", readiness.get("live_blockers", []))),
            "required_future_gates": list(policy.REQUIRED_FUTURE_GATES),
        },
        "allowed_actions": list(policy.ALLOWED_ACTIONS),
        "forbidden_actions": list(policy.FORBIDDEN_ACTIONS),
        "current_review_queue": queue_items,
        "manual_export_queue": manual_export_queue,
        "x_preview_queue": x_preview_queue,
        "telegram_preview_queue": telegram_preview_queue,
        "blocked_live_dispatch_queue": blocked_queue,
        "audit_dry_run_summary": {
            "audit_event_count": len(inputs["audit_outputs"]),
            "dispatch_audit_dry_run_contract_checksum": audit_contract["dispatch_audit_dry_run_contract_checksum"],
            "dispatch_audit_dry_run_fixture_outputs_checksum": audit_contract["dispatch_audit_dry_run_fixture_outputs_checksum"],
            "request_budget_used": 0,
        },
        "chain_reconciliation_summary": {
            "full_dry_run_chain_reconciliation_checksum": chain["full_dry_run_chain_reconciliation_checksum"],
            "status": chain.get("status", "pass"),
            "readiness_class": policy.READINESS_CLASS,
        },
        "required_future_gates": list(policy.REQUIRED_FUTURE_GATES),
        "evidence_index": evidence_index,
        "payload_hash_index": payload_hash_index,
        "audit_hash_index": audit_hash_index,
        "platform_counts": _platform_counts(queue_items),
        "action_counts": _action_counts(queue_items),
        "no_live_behavior_proof": {
            **policy.safety_flags(),
            "proof": "pass_no_live_env_network_platform_provider_behavior",
        },
        "next_operator_action": "review manual export queue or open static cockpit surface preview",
        "next_builder_task": NEXT_BATCH_PROMPT,
        "public_postable": False,
        "can_dispatch": False,
        "live_ready_state_created": False,
        "evidence_refs": [entry["checksum"] for entry in evidence_index] + list(manual_surface.get("evidence_refs", [])),
        "no_forbidden_readiness_claim_proof": "pass_no_forbidden_readiness_claims_in_cockpit_read_model",
        "payload_hash_index_proof": "pass_hashes_only_no_raw_credential_token_destination_env_path_live_url_provider_output",
        "protected_output_path": os.path.join(DOC_REL_DIR),
        "status": "pass",
    }
    policy.validate_no_forbidden_readiness_claims(packet)
    policy.validate_no_forbidden_material(payload_hash_index)
    policy.validate_no_forbidden_material(packet)
    packet["cockpit_read_model_fixture_outputs_checksum"] = adapter.compute_checksum(queue_items)
    packet["cockpit_read_model_checksum"] = adapter.compute_checksum(packet)
    return packet


def build_next_packet(read_model_packet, policy_packet):
    packet = {
        "task_label": NEXT_BATCH_PROMPT,
        "model": "NEXT_STATIC_COCKPIT_SURFACE_CONTRACT_0174YF_YG_YH",
        "model_version": "0174YF_YG_YH_NEXT_STATIC_COCKPIT_SURFACE_CONTRACT_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "next_batch_prompt": NEXT_BATCH_PROMPT,
        "next_scope": "static_cockpit_surface_local_only_no_live_behavior",
        "allowed_inputs": ["cockpit_read_model_packet", "cockpit_read_model_fixture_outputs", "cockpit_read_model_policy_packet"],
        "forbidden_outputs": ["live_dispatch", "credential_hydration", "platform_api_call", "provider_api_call", "scheduler", "live_state_creation"],
        "readiness_class": policy.READINESS_CLASS,
        "manual_export_status": policy.MANUAL_EXPORT_STATUS,
        "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
        "cockpit_read_model_checksum": read_model_packet["cockpit_read_model_checksum"],
        "cockpit_read_model_policy_checksum": policy_packet["cockpit_read_model_policy_checksum"],
        "cockpit_read_model_fixture_outputs_checksum": read_model_packet["cockpit_read_model_fixture_outputs_checksum"],
        "static_surface_must_be_local_only": True,
        "status": "pass",
    }
    policy.validate_no_forbidden_readiness_claims(packet)
    policy.validate_no_forbidden_material(packet)
    packet["next_static_cockpit_surface_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", "", "> [!IMPORTANT]", "> Cockpit read model only. Review queues are local; live dispatch remains blocked.", ""]
    for key in sorted(packet):
        value = packet[key]
        if key in {"current_review_queue", "manual_export_queue", "x_preview_queue", "telegram_preview_queue", "blocked_live_dispatch_queue", "payload_hash_index", "audit_hash_index"}:
            value = f"{len(value)} items"
        elif isinstance(value, (dict, list)):
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
    fixture_outputs = build_fixture_outputs(inputs)
    read_model_packet = build_read_model_packet(inputs, policy_packet, fixture_outputs)
    next_packet = build_next_packet(read_model_packet, policy_packet)
    (out / READ_MODEL_PACKET).write_text(adapter.serialize(read_model_packet), encoding="utf-8", newline="\n")
    (out / READ_MODEL_DOC).write_text(render_doc("Cockpit Read Model", read_model_packet), encoding="utf-8", newline="\n")
    (out / FIXTURE_OUTPUTS).write_text(adapter.serialize(fixture_outputs), encoding="utf-8", newline="\n")
    (out / NEXT_PACKET).write_text(adapter.serialize(next_packet), encoding="utf-8", newline="\n")
    (out / NEXT_DOC).write_text(render_doc("Next Static Cockpit Surface Contract", next_packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"read_model": read_model_packet, "policy": policy_packet, "fixture_outputs": fixture_outputs, "next_packet": next_packet})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("COCKPIT_READ_MODEL_CHECKSUM", result["read_model"]["cockpit_read_model_checksum"])
    print("COCKPIT_READ_MODEL_POLICY_CHECKSUM", result["policy"]["cockpit_read_model_policy_checksum"])
    print("COCKPIT_READ_MODEL_FIXTURE_OUTPUTS_CHECKSUM", result["read_model"]["cockpit_read_model_fixture_outputs_checksum"])
    print("NEXT_STATIC_COCKPIT_SURFACE_CONTRACT_CHECKSUM", result["next_packet"]["next_static_cockpit_surface_contract_checksum"])
