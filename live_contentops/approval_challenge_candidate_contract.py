"""Approval challenge candidate contract (LOCAL, NOT APPROVAL LEDGER)."""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import approval_challenge_policy as policy
from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XK_XL_XM_APPROVAL_CHALLENGE_CANDIDATE_CONTRACT_V0"
MODEL = "APPROVAL_CHALLENGE_CANDIDATE_CONTRACT_0174XK_XL_XM"
MODEL_VERSION = "0174XK_XL_XM_APPROVAL_CHALLENGE_CANDIDATE_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "1f7d2f96d468cbc0d88091f5e7d94201222c3c69"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XK_XL_XM")
SOURCE_FIXTURE = os.path.join("docs", "automation", "0174XH_XI_XJ", "platform_variant_fixture_outputs.json")
SOURCE_RUN_PACKET = os.path.join("docs", "automation", "0174XH_XI_XJ", "primary_platform_variant_dry_run_packet.json")
CONTRACT_PACKET = "approval_challenge_candidate_contract_packet.json"
CONTRACT_DOC = "approval_challenge_candidate_contract.md"
FIXTURE_OUTPUTS = "approval_challenge_candidate_fixture_outputs.json"
NEXT_PACKET = "next_approval_ledger_contract_packet.json"
NEXT_DOC = "next_approval_ledger_contract.md"
NEXT_BATCH_PROMPT = "TASK_CONTENTOPS_0174XN_XO_XP_APPROVAL_LEDGER_CONTRACT_V0"


def load_payloads(repo_root="."):
    path = pathlib.Path(repo_root) / SOURCE_FIXTURE
    return json.loads(path.read_text(encoding="utf-8"))


def load_run_packet(repo_root="."):
    path = pathlib.Path(repo_root) / SOURCE_RUN_PACKET
    return json.loads(path.read_text(encoding="utf-8"))


def blocked_brief_ids(run_packet):
    keys = [
        "blocked_direct_dispatch_proof",
        "blocked_approval_candidate_proof",
        "blocked_signal_advice_proof",
        "blocked_future_artifact_proof",
    ]
    out = set()
    for key in keys:
        out.update(run_packet.get(key, []))
    return out


def destination_summary(payload):
    platform = payload["platform"]
    pclass = payload["payload_class"]
    if platform == "telegram" and pclass == "telegram_operator_review_message":
        role = "remote_operator_inbox_future_review_surface"
    elif platform == "telegram":
        role = "telegram_channel_dispatch_destination_proven_frozen"
    elif platform == "substack":
        role = "substack_manual_markdown_export_review_surface"
    elif platform == "x":
        role = "x_review_only_public_discussion_preview_surface"
    else:
        role = "unknown_review_surface"
    return f"redacted:{platform}:{role}:symbolic_fixture_only"


def challenge_channel(payload):
    if payload["platform"] == "telegram" and payload["payload_class"] == "telegram_operator_review_message":
        return "telegram_future"
    return "local_ui_fixture"


def build_challenge_text(candidate):
    lines = [
        "Approval challenge candidate (review-only).",
        f"Platform: {candidate['platform']}",
        f"Payload class: {candidate['payload_class']}",
        f"Payload hash short: {candidate['payload_hash_short']}",
        f"Destination: {candidate['destination_summary_redacted']}",
        "Status: review-only; approval not recorded; dispatch not allowed.",
        "Limitations:",
    ]
    lines.extend([f"- {item}" for item in candidate["limitations"]])
    lines.extend([
        "Allowed responses:",
        candidate["approval_phrase_required"],
        candidate["rejection_phrase_required"],
        candidate["edit_phrase_allowed"],
        candidate["hold_phrase_allowed"],
    ])
    return "\n".join(lines)


def build_candidate(payload):
    short = policy.hash_short(payload["payload_hash"])
    phrases = policy.allowed_response_phrases(payload["payload_hash"])
    candidate = {
        "challenge_candidate_id": f"challenge_{payload['payload_id']}_{short}",
        "source_payload_id": payload["payload_id"],
        "source_brief_id": payload["source_brief_id"],
        "source_intent_id": payload["source_intent_id"],
        "platform": payload["platform"],
        "payload_class": payload["payload_class"],
        "payload_hash": payload["payload_hash"],
        "payload_hash_short": short,
        "destination_summary_redacted": destination_summary(payload),
        "destination_binding_id": "symbolic_fixture_only",
        "credential_handle_id": "symbolic_fixture_only",
        "visibility_class": "approval_challenge_candidate_review_only",
        "challenge_channel": challenge_channel(payload),
        **phrases,
        "expires_policy": "future_required_not_active",
        "one_time_nonce_policy": "future_required_not_active",
        "limitations": list(payload.get("limitations", [])),
        "source_notes": list(payload.get("source_notes", [])),
        "no_financial_advice": True,
        "no_signal_language": True,
        "approval_required": True,
        "can_record_approval": False,
        "can_dispatch": False,
        "can_create_outbox": False,
        "public_postable": False,
        "human_review_required": True,
        "evidence_refs": list(payload.get("evidence_refs", [])),
        "blocked_reasons": [],
        "manual_export": copy.deepcopy(payload.get("manual_export", {})),
        "platform_warnings": list(payload.get("platform_warnings", [])),
        "platform_formatting_metadata": copy.deepcopy(payload.get("platform_formatting_metadata", {})),
        **policy.safety_flags(),
    }
    candidate["challenge_text"] = build_challenge_text(candidate)
    policy.validate_no_forbidden_material(candidate)
    return candidate


def build_candidates(payloads, run_packet):
    blocked = blocked_brief_ids(run_packet)
    return [build_candidate(p) for p in payloads if policy.can_create_candidate(p, blocked)]


def build_contract_packet(payloads, candidates, run_packet):
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "source_payload_count": len(payloads),
        "generated_candidate_count": len(candidates),
        "supported_platforms": sorted({c["platform"] for c in candidates}),
        "supported_payload_classes": sorted({c["payload_class"] for c in candidates}),
        "blocked_direct_dispatch_proof": run_packet.get("blocked_direct_dispatch_proof", []),
        "blocked_approval_candidate_proof": run_packet.get("blocked_approval_candidate_proof", []),
        "blocked_signal_advice_proof": run_packet.get("blocked_signal_advice_proof", []),
        "blocked_future_artifact_proof": run_packet.get("blocked_future_artifact_proof", []),
        "all_can_record_approval_false": all(c["can_record_approval"] is False for c in candidates),
        "all_can_dispatch_false": all(c["can_dispatch"] is False for c in candidates),
        "all_can_create_outbox_false": all(c["can_create_outbox"] is False for c in candidates),
        "all_public_postable_false": all(c["public_postable"] is False for c in candidates),
        "all_human_review_required_true": all(c["human_review_required"] is True for c in candidates),
        "all_hash_short_derived": all(c["payload_hash_short"] == c["payload_hash"][:12] for c in candidates),
        "telegram_dispatch_status": "proven_frozen_no_send",
        "telegram_roles_distinct": True,
        "substack_manual_export_preserved": all(c["manual_export"] for c in candidates if c["platform"] == "substack"),
        "x_short_thread_split_preserved": {c["payload_class"] for c in candidates if c["platform"] == "x"} == {"x_short_post", "x_thread"},
        "status": "pass",
    }
    packet["approval_challenge_candidate_fixture_outputs_checksum"] = adapter.compute_checksum(candidates)
    packet["approval_challenge_candidate_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def build_next_packet(contract_packet, policy_packet):
    packet = {
        "task_label": "TASK_CONTENTOPS_0174XN_XO_XP_APPROVAL_LEDGER_CONTRACT_V0",
        "model": "NEXT_APPROVAL_LEDGER_CONTRACT_0174XK_XL_XM",
        "model_version": "0174XK_XL_XM_NEXT_APPROVAL_LEDGER_CONTRACT_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **policy.safety_flags(),
        "next_batch_prompt": NEXT_BATCH_PROMPT,
        "next_scope": "approval_ledger_contract_local_only",
        "allowed_inputs": ["approval_challenge_candidate", "payload_hash_short", "explicit_operator_response_fixture"],
        "forbidden_outputs": ["live_dispatch", "platform_api_call", "credential_access", "autonomous_approval"],
        "approval_challenge_candidate_contract_checksum": contract_packet["approval_challenge_candidate_contract_checksum"],
        "approval_challenge_policy_checksum": policy_packet["approval_challenge_policy_checksum"],
        "approval_challenge_candidate_fixture_outputs_checksum": contract_packet["approval_challenge_candidate_fixture_outputs_checksum"],
    }
    packet["next_approval_ledger_contract_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", ""]
    lines.append("> [!IMPORTANT]")
    lines.append("> Local candidate construction only. No approval, ledger mutation, outbox mutation, dispatch, platform/provider call, network, or credential/env read.")
    lines.append("")
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
    payloads = load_payloads(repo_root)
    run_packet = load_run_packet(repo_root)
    candidates = build_candidates(payloads, run_packet)
    contract_packet = build_contract_packet(payloads, candidates, run_packet)
    next_packet = build_next_packet(contract_packet, policy_packet)
    (out / FIXTURE_OUTPUTS).write_text(adapter.serialize(candidates), encoding="utf-8", newline="\n")
    (out / CONTRACT_PACKET).write_text(adapter.serialize(contract_packet), encoding="utf-8", newline="\n")
    (out / CONTRACT_DOC).write_text(render_doc("Approval Challenge Candidate Contract", contract_packet), encoding="utf-8", newline="\n")
    (out / NEXT_PACKET).write_text(adapter.serialize(next_packet), encoding="utf-8", newline="\n")
    (out / NEXT_DOC).write_text(render_doc("Next Approval Ledger Contract", next_packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"candidates": candidates, "contract_packet": contract_packet, "policy_packet": policy_packet, "next_packet": next_packet})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("APPROVAL_CHALLENGE_CANDIDATE_CONTRACT_CHECKSUM", result["contract_packet"]["approval_challenge_candidate_contract_checksum"])
    print("APPROVAL_CHALLENGE_POLICY_CHECKSUM", result["policy_packet"]["approval_challenge_policy_checksum"])
    print("APPROVAL_CHALLENGE_CANDIDATE_FIXTURE_OUTPUTS_CHECKSUM", result["contract_packet"]["approval_challenge_candidate_fixture_outputs_checksum"])
    print("NEXT_APPROVAL_LEDGER_CONTRACT_CHECKSUM", result["next_packet"]["next_approval_ledger_contract_checksum"])
