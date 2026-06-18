"""Manual export review surface contract (LOCAL, OPERATOR REVIEW, NO DISPATCH)."""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import manual_export_review_policy as policy
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174YC_YD_YE_MANUAL_EXPORT_REVIEW_SURFACE_CONTRACT_V0"
MODEL = "MANUAL_EXPORT_REVIEW_SURFACE_CONTRACT_0174YC_YD_YE"
MODEL_VERSION = "0174YC_YD_YE_MANUAL_EXPORT_REVIEW_SURFACE_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "ca2e8c01327984fd90524e790406621a2668202d"
DOC_REL_DIR = os.path.join("docs", "automation", "0174YC_YD_YE")
SURFACE_PACKET = "manual_export_review_surface_packet.json"
SURFACE_DOC = "manual_export_review_surface.md"
FIXTURE_OUTPUTS = "manual_export_review_fixture_outputs.json"
NEXT_PACKET = "next_cockpit_read_model_contract_packet.json"
NEXT_DOC = "next_cockpit_read_model_contract.md"
NEXT_BATCH_PROMPT = "TASK_CONTENTOPS_0174YF_YG_YH_COCKPIT_READ_MODEL_CONTRACT_V0"

PATHS = {
    "readiness_summary": os.path.join("docs", "automation", "0174XZ_YA_YB", "supervised_dispatch_readiness_summary_packet.json"),
    "readiness_policy": os.path.join("docs", "automation", "0174XZ_YA_YB", "supervised_dispatch_readiness_policy_packet.json"),
    "chain_reconciliation": os.path.join("docs", "automation", "0174XZ_YA_YB", "full_dry_run_chain_reconciliation_packet.json"),
    "next_manual_export": os.path.join("docs", "automation", "0174XZ_YA_YB", "next_manual_export_review_surface_contract_packet.json"),
    "audit_contract": os.path.join("docs", "automation", "0174XW_XX_XY", "dispatch_audit_dry_run_contract_packet.json"),
    "audit_outputs": os.path.join("docs", "automation", "0174XW_XX_XY", "dispatch_audit_dry_run_fixture_outputs.json"),
    "platform_variants": os.path.join("docs", "automation", "0174XH_XI_XJ", "platform_variant_fixture_outputs.json"),
    "platform_registry": os.path.join("docs", "automation", "0174WY_WZ_XA", "platform_universe_registry_v2_packet.json"),
}


def _read_json(repo_root, rel_path):
    return json.loads((pathlib.Path(repo_root) / rel_path).read_text(encoding="utf-8"))


def load_inputs(repo_root="."):
    return {name: _read_json(repo_root, rel_path) for name, rel_path in PATHS.items()}


def _audit_index(audit_outputs):
    index = {}
    for event in audit_outputs:
        payload_hash = event.get("payload_hash")
        if payload_hash and payload_hash not in index:
            index[payload_hash] = event
    return index


def _base_entry(payload, audit_event):
    return {
        "surface_item_id": f"manual_export_review_{payload['payload_id']}",
        "payload_id": payload["payload_id"],
        "platform": payload["platform"],
        "payload_class": payload["payload_class"],
        "payload_hash": payload["payload_hash"],
        "payload_hash_short": payload["payload_hash"][:12],
        "audit_hash": audit_event.get("audit_hash") if audit_event else None,
        "review_only_payload": True,
        "manual_export_status": policy.MANUAL_EXPORT_STATUS,
        "can_dispatch": False,
        "public_postable": False,
        "human_review_required": True,
        "no_financial_advice": True,
        "no_signal_language": True,
        "live_ready_state_created": False,
        "source_notes": list(payload.get("source_notes", [])),
        "limitations": list(payload.get("limitations", [])),
        "evidence_refs": list(payload.get("evidence_refs", [])) + ([audit_event.get("audit_hash")] if audit_event and audit_event.get("audit_hash") else []),
        **policy.safety_flags(),
    }


def _substack_entry(payload, audit_event):
    entry = _base_entry(payload, audit_event)
    manual = payload.get("manual_export", {})
    entry.update({
        "surface_status": "primary_manual_export_review",
        "operator_action": "copy_markdown_for_substack",
        "title": payload.get("title", ""),
        "subtitle": payload.get("subtitle", ""),
        "markdown_body": manual.get("markdown_body") or payload.get("body", ""),
        "seo_metadata": copy.deepcopy(payload.get("seo_metadata", {})),
        "no_signal_disclaimer": manual.get("no_signal_disclaimer", "Review-only context. No financial advice, trade signal, price target, or recommendation."),
        "manual_export": {
            "format": "markdown",
            "copy_allowed_for_operator_review": True,
            "platform_api_called": False,
            "publish_later_recording_only": True,
        },
    })
    return entry


def _x_entry(payload, audit_event):
    entry = _base_entry(payload, audit_event)
    thread_parts = list(payload.get("thread_parts", []))
    entry.update({
        "surface_status": "preview_only_no_api",
        "operator_action": "inspect_x_thread_preview" if thread_parts else "inspect_x_short_preview",
        "short_post_preview": payload.get("body", "") if payload.get("payload_class") == "x_short_post" else "",
        "thread_preview": thread_parts,
        "manual_export": {},
        "preview_only": True,
    })
    return entry


def _telegram_entry(payload, audit_event):
    entry = _base_entry(payload, audit_event)
    payload_class = payload.get("payload_class")
    entry.update({
        "surface_status": "operator_review_preview_only" if payload_class == "telegram_operator_review_message" else "channel_update_preview_only",
        "operator_action": "inspect_telegram_channel_update_preview",
        "operator_review_message_preview": payload.get("body", "") if payload_class == "telegram_operator_review_message" else "",
        "channel_update_preview": payload.get("body", "") if payload_class == "telegram_channel_update" else "",
        "telegram_review_and_channel_distinct": True,
        "manual_export": {},
        "preview_only": True,
    })
    return entry


def build_fixture_outputs(inputs):
    audit_by_hash = _audit_index(inputs["audit_outputs"])
    outputs = []
    for payload in inputs["platform_variants"]:
        platform_name = payload.get("platform")
        if platform_name not in policy.PLATFORMS:
            continue
        audit_event = audit_by_hash.get(payload.get("payload_hash"))
        if platform_name == "substack":
            item = _substack_entry(payload, audit_event)
        elif platform_name == "x":
            item = _x_entry(payload, audit_event)
        elif platform_name == "telegram":
            item = _telegram_entry(payload, audit_event)
        else:
            continue
        policy.validate_no_forbidden_readiness_claims(item)
        policy.validate_no_forbidden_material(item)
        outputs.append(item)
    return outputs


def _platform_counts(outputs):
    return {platform_name: sum(1 for item in outputs if item["platform"] == platform_name) for platform_name in policy.PLATFORMS}


def _platform_payload_hashes(outputs):
    return {platform_name: [item["payload_hash"] for item in outputs if item["platform"] == platform_name] for platform_name in policy.PLATFORMS}


def build_surface_packet(inputs, policy_packet, fixture_outputs):
    readiness = inputs["readiness_summary"]
    audit_hashes = [event["audit_hash"] for event in inputs["audit_outputs"] if event.get("audit_hash")]
    payload_hashes = [item["payload_hash"] for item in fixture_outputs]
    packet = {
        "surface_id": "manual_export_review_surface_0174YC_YD_YE",
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "source_readiness_summary_id": readiness["readiness_summary_id"],
        "readiness_class": policy.READINESS_CLASS,
        "local_governance_status": policy.LOCAL_GOVERNANCE_STATUS,
        "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
        "manual_export_status": policy.MANUAL_EXPORT_STATUS,
        "platforms": list(policy.PLATFORMS),
        "platform_surface_statuses": copy.deepcopy(policy.PLATFORM_SURFACE_STATUSES),
        "platform_payload_counts": _platform_counts(fixture_outputs),
        "primary_manual_exports": [item for item in fixture_outputs if item["platform"] == "substack"],
        "review_only_payloads": fixture_outputs,
        "blocked_live_dispatch_reasons": list(readiness["live_blockers"]),
        "required_future_gates": list(readiness["required_future_gates"]),
        "operator_actions": list(policy.OPERATOR_ACTIONS),
        "forbidden_actions": list(policy.FORBIDDEN_ACTIONS),
        "payload_hashes": payload_hashes,
        "platform_payload_hashes": _platform_payload_hashes(fixture_outputs),
        "audit_hashes": audit_hashes,
        "source_notes": sorted({note for item in fixture_outputs for note in item.get("source_notes", [])}),
        "limitations": sorted({limit for item in fixture_outputs for limit in item.get("limitations", [])}),
        "no_financial_advice": True,
        "no_signal_language": True,
        "public_postable": False,
        "human_review_required": True,
        "can_dispatch": False,
        "live_ready_state_created": False,
        "evidence_refs": list(readiness["evidence_refs"]) + [inputs["chain_reconciliation"]["full_dry_run_chain_reconciliation_checksum"], policy_packet["manual_export_review_policy_checksum"]],
        "upstream_checksums": {
            "supervised_dispatch_readiness_summary_checksum": readiness["supervised_dispatch_readiness_summary_checksum"],
            "supervised_dispatch_readiness_policy_checksum": inputs["readiness_policy"]["supervised_dispatch_readiness_policy_checksum"],
            "full_dry_run_chain_reconciliation_checksum": inputs["chain_reconciliation"]["full_dry_run_chain_reconciliation_checksum"],
            "next_manual_export_review_surface_contract_checksum": inputs["next_manual_export"]["next_manual_export_review_surface_contract_checksum"],
            "dispatch_audit_dry_run_contract_checksum": inputs["audit_contract"]["dispatch_audit_dry_run_contract_checksum"],
            "dispatch_audit_dry_run_fixture_outputs_checksum": inputs["audit_contract"]["dispatch_audit_dry_run_fixture_outputs_checksum"],
            "platform_universe_registry_checksum": inputs["platform_registry"]["platform_universe_registry_checksum"],
        },
        "forbidden_readiness_claim_proof": "pass_no_forbidden_readiness_claims_in_surface",
        "no_forbidden_material_proof": "pass_no_raw_credential_token_chat_id_raw_destination_env_secret_path_live_url",
        "status": "pass",
    }
    policy.validate_no_forbidden_readiness_claims(packet)
    policy.validate_no_forbidden_material(packet)
    packet["manual_export_review_fixture_outputs_checksum"] = adapter.compute_checksum(fixture_outputs)
    packet["manual_export_review_surface_checksum"] = adapter.compute_checksum(packet)
    return packet


def build_next_packet(surface_packet, policy_packet):
    packet = {
        "task_label": NEXT_BATCH_PROMPT,
        "model": "NEXT_COCKPIT_READ_MODEL_CONTRACT_0174YC_YD_YE",
        "model_version": "0174YC_YD_YE_NEXT_COCKPIT_READ_MODEL_CONTRACT_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "next_batch_prompt": NEXT_BATCH_PROMPT,
        "next_scope": "cockpit_read_model_local_only_operator_review",
        "allowed_inputs": ["manual_export_review_surface", "manual_export_review_fixture_outputs", "readiness_summary", "audit_hashes", "payload_hashes"],
        "forbidden_outputs": ["live_dispatch", "credential_hydration", "platform_api_call", "provider_api_call", "scheduler", "live_state_creation"],
        "readiness_class": policy.READINESS_CLASS,
        "manual_export_status": policy.MANUAL_EXPORT_STATUS,
        "live_dispatch_status": policy.LIVE_DISPATCH_STATUS,
        "manual_export_review_surface_checksum": surface_packet["manual_export_review_surface_checksum"],
        "manual_export_review_policy_checksum": policy_packet["manual_export_review_policy_checksum"],
        "manual_export_review_fixture_outputs_checksum": surface_packet["manual_export_review_fixture_outputs_checksum"],
        "cockpit_must_be_read_model_only": True,
        "status": "pass",
    }
    policy.validate_no_forbidden_readiness_claims(packet)
    policy.validate_no_forbidden_material(packet)
    packet["next_cockpit_read_model_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", "", "> [!IMPORTANT]", "> Operator review surface only. Manual export review is available; live dispatch remains blocked.", ""]
    for key in sorted(packet):
        value = packet[key]
        if key in {"primary_manual_exports", "review_only_payloads"}:
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
    surface_packet = build_surface_packet(inputs, policy_packet, fixture_outputs)
    next_packet = build_next_packet(surface_packet, policy_packet)
    (out / SURFACE_PACKET).write_text(adapter.serialize(surface_packet), encoding="utf-8", newline="\n")
    (out / SURFACE_DOC).write_text(render_doc("Manual Export Review Surface", surface_packet), encoding="utf-8", newline="\n")
    (out / FIXTURE_OUTPUTS).write_text(adapter.serialize(fixture_outputs), encoding="utf-8", newline="\n")
    (out / NEXT_PACKET).write_text(adapter.serialize(next_packet), encoding="utf-8", newline="\n")
    (out / NEXT_DOC).write_text(render_doc("Next Cockpit Read Model Contract", next_packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"surface": surface_packet, "policy": policy_packet, "fixture_outputs": fixture_outputs, "next_packet": next_packet})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("MANUAL_EXPORT_REVIEW_SURFACE_CHECKSUM", result["surface"]["manual_export_review_surface_checksum"])
    print("MANUAL_EXPORT_REVIEW_POLICY_CHECKSUM", result["policy"]["manual_export_review_policy_checksum"])
    print("MANUAL_EXPORT_REVIEW_FIXTURE_OUTPUTS_CHECKSUM", result["surface"]["manual_export_review_fixture_outputs_checksum"])
    print("NEXT_COCKPIT_READ_MODEL_CONTRACT_CHECKSUM", result["next_packet"]["next_cockpit_read_model_contract_checksum"])
