"""Supervised dispatch readiness summary (LOCAL, NOT READY, NO DISPATCH)."""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import supervised_dispatch_readiness_policy as policy
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XZ_YA_YB_SUPERVISED_DISPATCH_READINESS_SUMMARY_V0"
MODEL = "SUPERVISED_DISPATCH_READINESS_SUMMARY_0174XZ_YA_YB"
MODEL_VERSION = "0174XZ_YA_YB_SUPERVISED_DISPATCH_READINESS_SUMMARY_V1"
SOURCE_BASELINE_COMMIT = "397a9cdbd020bcdf46bbb464ab9752e9be6b1e98"
CHAIN_START_COMMIT = "e77acd9f74b9ce2e65e569b6bf576e3896c1333e"
CHAIN_FINAL_COMMIT = SOURCE_BASELINE_COMMIT
DOC_REL_DIR = os.path.join("docs", "automation", "0174XZ_YA_YB")
SUMMARY_PACKET = "supervised_dispatch_readiness_summary_packet.json"
SUMMARY_DOC = "supervised_dispatch_readiness_summary.md"
RECON_PACKET = "full_dry_run_chain_reconciliation_packet.json"
RECON_DOC = "full_dry_run_chain_reconciliation.md"
NEXT_PACKET = "next_manual_export_review_surface_contract_packet.json"
NEXT_DOC = "next_manual_export_review_surface_contract.md"
NEXT_BATCH_PROMPT = "TASK_CONTENTOPS_0174YC_YD_YE_MANUAL_EXPORT_REVIEW_SURFACE_CONTRACT_V0"

PATHS = {
    "dispatch_audit_contract": os.path.join("docs", "automation", "0174XW_XX_XY", "dispatch_audit_dry_run_contract_packet.json"),
    "dispatch_audit_policy": os.path.join("docs", "automation", "0174XW_XX_XY", "dispatch_audit_policy_packet.json"),
    "dispatch_audit_outputs": os.path.join("docs", "automation", "0174XW_XX_XY", "dispatch_audit_dry_run_fixture_outputs.json"),
    "next_readiness": os.path.join("docs", "automation", "0174XW_XX_XY", "next_supervised_dispatch_readiness_summary_packet.json"),
    "dispatch_gate": os.path.join("docs", "automation", "0174XT_XU_XV", "dispatch_gate_matrix_contract_packet.json"),
    "dispatch_outbox": os.path.join("docs", "automation", "0174XQ_XR_XS", "dispatch_outbox_candidate_contract_packet.json"),
    "approval_ledger": os.path.join("docs", "automation", "0174XN_XO_XP", "approval_ledger_contract_packet.json"),
    "approval_challenge": os.path.join("docs", "automation", "0174XK_XL_XM", "approval_challenge_candidate_contract_packet.json"),
    "platform_variant": os.path.join("docs", "automation", "0174XH_XI_XJ", "primary_platform_variant_dry_run_packet.json"),
    "editorial_brief": os.path.join("docs", "automation", "0174XE_XF_XG", "llm_intent_editorial_brief_contract_packet.json"),
    "intent_ingress": os.path.join("docs", "automation", "0174XB_XC_XD", "remote_operator_intent_ingress_packet.json"),
    "platform_registry": os.path.join("docs", "automation", "0174WY_WZ_XA", "platform_universe_registry_v2_packet.json"),
    "telegram_registry": os.path.join("docs", "automation", "0174WY_WZ_XA", "telegram_supervised_dispatch_capability_registry_packet.json"),
}

STAGE_ORDER = [
    "remote_operator_intent_ingress",
    "llm_intent_editorial_brief",
    "primary_platform_variant_dry_run",
    "approval_challenge_candidate",
    "approval_ledger",
    "dispatch_outbox_candidate",
    "dispatch_gate_matrix",
    "dispatch_audit_dry_run",
    "supervised_dispatch_readiness_summary",
]


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


def _first_checksum(packet, keys):
    for key in keys:
        if key in packet:
            return packet[key]
    raise KeyError(keys[0])


def load_inputs(repo_root="."):
    return {name: _read_json(repo_root, rel_path) for name, rel_path in PATHS.items()}


def no_live_behavior_proof(audit_contract, audit_policy, audit_outputs):
    flag_keys = [
        "network_performed",
        "telegram_api_called",
        "x_api_called",
        "substack_api_called",
        "platform_api_called",
        "provider_api_called",
        "llm_provider_api_called",
        "env_read",
        "dotenv_read",
        "credential_read",
        "credential_hydration_performed",
        "scheduler_enabled",
        "live_post_performed",
        "autonomous_replies_or_dms",
        "scraping_performed",
        "public_ready_content_generated",
        "platform_dispatch_performed",
        "live_ready_state_created",
        "raw_request_persisted",
        "raw_response_persisted",
        "token_logged",
    ]
    proof = {key: audit_contract.get(key) is False and audit_policy.get(key) is False and all(event.get(key) is False for event in audit_outputs) for key in flag_keys}
    proof["all_false"] = all(proof.values())
    proof["provider_response_class_values"] = audit_contract["provider_response_class_values"]
    proof["request_budget_used_values"] = audit_contract["request_budget_used_values"]
    proof["all_final_url_verified_null"] = audit_contract["all_final_url_verified_null"]
    return proof


def checksum_refs(inputs):
    return {
        "platform_universe_registry_checksum": inputs["platform_registry"]["platform_universe_registry_checksum"],
        "telegram_dispatch_registry_checksum": inputs["telegram_registry"]["registry_checksum"],
        "remote_inbox_checksum": _first_checksum(inputs["intent_ingress"], ["remote_inbox_checksum", "remote_operator_inbox_checksum", "operator_inbox_checksum", "fixture_messages_checksum", "inbox_packet_checksum"]),
        "intent_ingress_checksum": _first_checksum(inputs["intent_ingress"], ["remote_operator_intent_ingress_checksum", "intent_ingress_checksum", "intent_ingress_packet_checksum"]),
        "editorial_brief_checksum": _first_checksum(inputs["editorial_brief"], ["llm_intent_editorial_brief_contract_checksum", "editorial_brief_checksum", "editorial_brief_contract_checksum"]),
        "platform_variant_checksum": _first_checksum(inputs["platform_variant"], ["primary_platform_variant_dry_run_checksum", "platform_variant_checksum", "primary_variant_dry_run_checksum"]),
        "approval_challenge_checksum": _first_checksum(inputs["approval_challenge"], ["approval_challenge_candidate_contract_checksum", "approval_challenge_checksum"]),
        "approval_ledger_checksum": inputs["approval_ledger"]["approval_ledger_contract_checksum"],
        "dispatch_outbox_candidate_checksum": inputs["dispatch_outbox"]["dispatch_outbox_candidate_contract_checksum"],
        "dispatch_gate_matrix_checksum": inputs["dispatch_gate"]["dispatch_gate_matrix_contract_checksum"],
        "dispatch_audit_dry_run_checksum": inputs["dispatch_audit_contract"]["dispatch_audit_dry_run_contract_checksum"],
    }


def build_reconciliation(inputs, policy_packet):
    refs = checksum_refs(inputs)
    stages = [
        {"stage": "remote_operator_intent_ingress", "status": "local_fixture_ingested", "checksum": refs["intent_ingress_checksum"]},
        {"stage": "llm_intent_editorial_brief", "status": "deterministic_fixture_contract", "checksum": refs["editorial_brief_checksum"]},
        {"stage": "primary_platform_variant_dry_run", "status": "review_only_payload_previews", "checksum": refs["platform_variant_checksum"]},
        {"stage": "approval_challenge_candidate", "status": "operator_review_candidate_only", "checksum": refs["approval_challenge_checksum"]},
        {"stage": "approval_ledger", "status": "local_approval_semantics_only", "checksum": refs["approval_ledger_checksum"]},
        {"stage": "dispatch_outbox_candidate", "status": "candidate_only_no_dispatch", "checksum": refs["dispatch_outbox_candidate_checksum"]},
        {"stage": "dispatch_gate_matrix", "status": "gate_matrix_evaluated_not_live", "checksum": refs["dispatch_gate_matrix_checksum"]},
        {"stage": "dispatch_audit_dry_run", "status": "redacted_audit_dry_run_not_called", "checksum": refs["dispatch_audit_dry_run_checksum"]},
        {"stage": "supervised_dispatch_readiness_summary", "status": policy.READINESS_CLASS, "checksum": policy_packet["supervised_dispatch_readiness_policy_checksum"]},
    ]
    packet = {
        "task_label": TASK_LABEL,
        "model": "FULL_DRY_RUN_CHAIN_RECONCILIATION_0174XZ_YA_YB",
        "model_version": "0174XZ_YA_YB_FULL_DRY_RUN_CHAIN_RECONCILIATION_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "chain_start_commit": CHAIN_START_COMMIT,
        "chain_final_commit": CHAIN_FINAL_COMMIT,
        "current_baseline_commit": SOURCE_BASELINE_COMMIT,
        "stage_order": list(STAGE_ORDER),
        "stages": stages,
        "stage_count": len(stages),
        "readiness_class": policy.READINESS_CLASS,
        "local_governance_status": policy.LOCAL_GOVERNANCE_STATUS,
        "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
        "status": "pass",
    }
    packet["full_dry_run_chain_reconciliation_checksum"] = adapter.compute_checksum(packet)
    return packet


def build_summary(inputs, policy_packet, reconciliation):
    refs = checksum_refs(inputs)
    audit_outputs = inputs["dispatch_audit_outputs"]
    proof = no_live_behavior_proof(inputs["dispatch_audit_contract"], inputs["dispatch_audit_policy"], audit_outputs)
    summary = {
        "readiness_summary_id": "supervised_dispatch_readiness_summary_0174XZ_YA_YB",
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "chain_start_commit": CHAIN_START_COMMIT,
        "chain_final_commit": CHAIN_FINAL_COMMIT,
        "current_baseline_commit": SOURCE_BASELINE_COMMIT,
        **refs,
        "supervised_dispatch_readiness_policy_checksum": policy_packet["supervised_dispatch_readiness_policy_checksum"],
        "full_dry_run_chain_reconciliation_checksum": reconciliation["full_dry_run_chain_reconciliation_checksum"],
        "readiness_class": policy.READINESS_CLASS,
        "local_governance_status": policy.LOCAL_GOVERNANCE_STATUS,
        "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
        "supported_primary_platforms": list(policy.SUPPORTED_PRIMARY_PLATFORMS),
        "dry_run_capabilities_proven": list(policy.DRY_RUN_CAPABILITIES_PROVEN),
        "live_blockers": list(policy.LIVE_BLOCKERS),
        "required_future_gates": list(policy.REQUIRED_FUTURE_GATES),
        "forbidden_capabilities": list(policy.FORBIDDEN_CAPABILITIES),
        "platform_readiness": copy.deepcopy(policy.PLATFORM_READINESS),
        "no_live_behavior_proof": proof,
        "forbidden_readiness_claim_proof": "pass_no_ready_live_ready_dispatch_ready_public_postable_claims",
        "evidence_refs": [event["audit_hash"] for event in audit_outputs] + [reconciliation["full_dry_run_chain_reconciliation_checksum"]],
        "status": "pass",
    }
    policy.validate_no_forbidden_readiness_claims(summary)
    summary["audit_hash"] = adapter.compute_checksum({k: v for k, v in summary.items() if k != "audit_hash"})
    summary["supervised_dispatch_readiness_summary_checksum"] = adapter.compute_checksum(summary)
    return summary


def build_next_packet(summary, policy_packet):
    packet = {
        "task_label": NEXT_BATCH_PROMPT,
        "model": "NEXT_MANUAL_EXPORT_REVIEW_SURFACE_CONTRACT_0174XZ_YA_YB",
        "model_version": "0174XZ_YA_YB_NEXT_MANUAL_EXPORT_REVIEW_SURFACE_CONTRACT_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "next_batch_prompt": NEXT_BATCH_PROMPT,
        "next_scope": "manual_export_review_surface_or_cockpit_read_model_local_only",
        "allowed_direction": "manual_export_review_surface_or_cockpit_read_model",
        "forbidden_direction": "live_dispatch",
        "allowed_inputs": ["readiness_summary", "full_dry_run_chain_reconciliation", "redacted_audit_events", "manual_export_preview"],
        "forbidden_outputs": ["live_dispatch", "credential_hydration", "platform_api_call", "provider_api_call", "scheduler", "live_ready_state", "public_postable_content"],
        "supervised_dispatch_readiness_summary_checksum": summary["supervised_dispatch_readiness_summary_checksum"],
        "supervised_dispatch_readiness_policy_checksum": policy_packet["supervised_dispatch_readiness_policy_checksum"],
        "readiness_class": policy.READINESS_CLASS,
        "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
        "manual_export_review_surface_must_remain_local_only": True,
    }
    policy.validate_no_forbidden_readiness_claims(packet)
    packet["next_manual_export_review_surface_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", "", "> [!IMPORTANT]", "> Blocker-first local surface. Live dispatch remains blocked; next step is manual export/review surface or cockpit read model, not live dispatch.", ""]
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
    reconciliation = build_reconciliation(inputs, policy_packet)
    summary = build_summary(inputs, policy_packet, reconciliation)
    next_packet = build_next_packet(summary, policy_packet)
    (out / SUMMARY_PACKET).write_text(adapter.serialize(summary), encoding="utf-8", newline="\n")
    (out / SUMMARY_DOC).write_text(render_doc("Supervised Dispatch Readiness Summary", summary), encoding="utf-8", newline="\n")
    (out / RECON_PACKET).write_text(adapter.serialize(reconciliation), encoding="utf-8", newline="\n")
    (out / RECON_DOC).write_text(render_doc("Full Dry-Run Chain Reconciliation", reconciliation), encoding="utf-8", newline="\n")
    (out / NEXT_PACKET).write_text(adapter.serialize(next_packet), encoding="utf-8", newline="\n")
    (out / NEXT_DOC).write_text(render_doc("Next Manual Export Review Surface Contract", next_packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"summary": summary, "policy_packet": policy_packet, "reconciliation": reconciliation, "next_packet": next_packet})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("SUPERVISED_DISPATCH_READINESS_SUMMARY_CHECKSUM", result["summary"]["supervised_dispatch_readiness_summary_checksum"])
    print("SUPERVISED_DISPATCH_READINESS_POLICY_CHECKSUM", result["policy_packet"]["supervised_dispatch_readiness_policy_checksum"])
    print("FULL_DRY_RUN_CHAIN_RECONCILIATION_CHECKSUM", result["reconciliation"]["full_dry_run_chain_reconciliation_checksum"])
    print("NEXT_MANUAL_EXPORT_REVIEW_SURFACE_CONTRACT_CHECKSUM", result["next_packet"]["next_manual_export_review_surface_contract_checksum"])
