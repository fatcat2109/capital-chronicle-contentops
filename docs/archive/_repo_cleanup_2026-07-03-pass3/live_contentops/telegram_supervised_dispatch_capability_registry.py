"""Telegram supervised dispatch capability registry (LOCAL, NOT LIVE).

0174WY/WZ/XA freezes Telegram channel dispatch as a proven supervised
capability. It reads committed redacted evidence only, writes deterministic
packets/docs only when invoked, and never performs Telegram/API/network/env
behavior.
"""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = (
    "TASK_CONTENTOPS_0174WY_WZ_XA_TELEGRAM_DISPATCH_FREEZE_AND_PLATFORM_"
    "UNIVERSE_REGISTRY_V2_PRIMARY_CHANNELS_V0"
)
MODEL = "TELEGRAM_SUPERVISED_DISPATCH_CAPABILITY_REGISTRY_0174WY_WZ_XA"
MODEL_VERSION = "0174WY_WZ_XA_TELEGRAM_SUPERVISED_DISPATCH_CAPABILITY_REGISTRY_V1"
SOURCE_BASELINE_COMMIT = "d0e8d7f0e3c9bf84704cb66c602e75f7b9e8af62"
DOC_REL_DIR = os.path.join("docs", "automation", "0174WY_WZ_XA")

LEDGER12_PACKET_REL = os.path.join(
    "docs", "automation", "0174WV_WW_WX", "telegram_ledger12_remote_operator_loop_state_packet.json")
HARDENING_AUDIT_REL = os.path.join(
    "docs", "automation", "0174WV_WW_WX", "telegram_chain_hardening_audit_packet.json")
ROLLUP_REL = os.path.join(
    "docs", "automation", "0174WV_WW_WX", "telegram_ledger11_to_ledger12_thirteenth_send_rollup_packet.json")
PROOF_REL = os.path.join(
    "docs", "automation", "0174WV_WW_WX", "telegram_ledger11_thirteenth_send_proof_packet.json")

REGISTRY_PACKET = "telegram_supervised_dispatch_capability_registry_packet.json"
REGISTRY_DOC = "telegram_supervised_dispatch_capability_registry.md"
FREEZE_PACKET = "telegram_dispatch_freeze_certificate_packet.json"
FREEZE_DOC = "telegram_dispatch_freeze_certificate.md"
DECISION_PACKET = "telegram_dispatch_stop_treadmill_decision_packet.json"
DECISION_DOC = "telegram_dispatch_stop_treadmill_decision.md"

FUTURE_LIVE_SEND_ALLOWED_FOR = [
    "explicit_regression_test",
    "new_platform_adapter_proof",
    "new_account_or_channel_binding_proof",
    "user_approved_supervised_production_payload",
    "security_or_audit_retest_after_dispatch_path_change",
]
FUTURE_LIVE_SEND_NOT_ALLOWED_FOR = [
    "arbitrary_ledgerN_increment",
    "metadata_stress_testing",
    "proof_of_life_ping",
    "cosmetic_audit_update",
]
NEXT_PRODUCT_WORK = [
    "remote_ingress",
    "intent_parser",
    "editorial_workflow",
    "approval_authority",
    "dispatch_preparation",
    "evidence_cockpit_integration",
]
FORBIDDEN_NEXT_TASK_FRAGMENTS = [
    "LEDGER12_TO_LEDGER13",
    "LEDGERN_TO_LEDGERN_PLUS_1",
    "FOURTEENTH_SEND",
    "LIVE_SEND_RUNNER",
]


def _load_json(repo_root, rel_path):
    return json.loads((pathlib.Path(repo_root) / rel_path).read_text(encoding="utf-8"))


def _assert_safe_output(repo_root, output_dir):
    root = pathlib.Path(repo_root).resolve()
    out = pathlib.Path(output_dir).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    if out != allowed:
        raise ValueError("unsafe_output_path_refused")
    return out


def _secret_flags_ok(*objects):
    forbidden = []
    for obj in objects:
        forbidden.extend(adapter.scan_for_leaks(obj))
        forbidden.extend(adapter.scan_for_financial_advice(obj))
    return not forbidden


def build_registry(repo_root="."):
    ledger12 = _load_json(repo_root, LEDGER12_PACKET_REL)
    audit = _load_json(repo_root, HARDENING_AUDIT_REL)
    rollup = _load_json(repo_root, ROLLUP_REL)
    proof = _load_json(repo_root, PROOF_REL)
    remote = ledger12.get("remote_loop_state", {})

    blockers = []
    if ledger12.get("current_ledger_count") != 12:
        blockers.append("latest_ledger_count_below_12")
    if ledger12.get("last_successful_send_sequence") != 13:
        blockers.append("latest_successful_sequence_below_13")
    if not audit.get("audit_passed"):
        blockers.append("missing_or_failed_chain_hardening_audit")
    if audit.get("latest_ledger_count") != 12:
        blockers.append("audit_missing_latest_ledger12")
    if proof.get("request_budget_used") != 1:
        blockers.append("request_budget_not_one")
    if not proof.get("send_succeeded"):
        blockers.append("latest_dispatch_proof_not_successful")
    if not _secret_flags_ok(ledger12, audit, rollup, proof):
        blockers.append("secret_or_forbidden_output_detected")

    registry = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "is_local_only": True,
        "network_performed": False,
        "env_read": False,
        "dotenv_read": False,
        "credential_read": False,
        "telegram_api_called": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "scheduler_enabled": False,
        "live_post_performed": False,
        "autonomous_reply_or_dm_performed": False,
        "scraping_performed": False,
        "new_live_send_runner_created": False,
        "telegram_channel_dispatch_status": "proven_frozen",
        "latest_accepted_ledger_count": ledger12.get("current_ledger_count"),
        "latest_successful_sequence": ledger12.get("last_successful_send_sequence"),
        "latest_remote_loop_state_checksum": remote.get("remote_loop_state_checksum"),
        "latest_chain_hardening_audit_checksum": audit.get("audit_checksum"),
        "latest_dispatch_proof_checksum": proof.get("evidence_checksum"),
        "next_live_send_allowed": "false_by_default",
        "requires_new_operator_task": True,
        "requires_new_exact_payload_hash": True,
        "requires_new_manual_gate_packet": True,
        "requires_new_outbox_entry": True,
        "requires_regression_reason": True,
        "no_more_ledger_treadmill": True,
        "default_next_task_class": "platform_registry_and_remote_inbox_pipeline",
        "future_live_send_allowed_for": FUTURE_LIVE_SEND_ALLOWED_FOR,
        "future_live_send_not_allowed_for": FUTURE_LIVE_SEND_NOT_ALLOWED_FOR,
        "next_product_work": NEXT_PRODUCT_WORK,
        "refuses_new_ledger_to_ledger_live_send_next_task": True,
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
    }
    registry["registry_checksum"] = adapter.compute_checksum(registry)
    return registry


def build_freeze_certificate(registry):
    cert = {
        "task_label": "TASK_CONTENTOPS_0174WY_WZ_XA_TELEGRAM_DISPATCH_FREEZE_CERTIFICATE_V0",
        "model": "TELEGRAM_DISPATCH_FREEZE_CERTIFICATE_0174WY_WZ_XA",
        "model_version": "0174WY_WZ_XA_TELEGRAM_DISPATCH_FREEZE_CERTIFICATE_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "telegram_channel_dispatch_status": registry["telegram_channel_dispatch_status"],
        "capability_demonstrated": {
            "bot_channel_destination_binding": True,
            "exact_payload_hash_approval": True,
            "manual_gate_capture": True,
            "exactly_one_sendMessage": True,
            "request_budget_used": 1,
            "no_retry": True,
            "ledger_append": True,
            "replay_guard": True,
            "redacted_audit": True,
            "no_token_raw_destination_raw_response_raw_url_header_cookie_raw_gate_id_raw_approval_note": True,
            "multi_send_chain_reconciliation_through_ledger12": True,
        },
        "latest_accepted_ledger_count": registry["latest_accepted_ledger_count"],
        "latest_successful_sequence": registry["latest_successful_sequence"],
        "registry_checksum": registry["registry_checksum"],
        "is_local_only": True,
        "telegram_api_called": False,
        "network_performed": False,
        "env_read": False,
        "dotenv_read": False,
    }
    cert["freeze_certificate_checksum"] = adapter.compute_checksum(cert)
    return cert


def build_stop_treadmill_decision(registry):
    decision = {
        "task_label": "TASK_CONTENTOPS_0174WY_WZ_XA_TELEGRAM_DISPATCH_STOP_TREADMILL_DECISION_V0",
        "model": "TELEGRAM_DISPATCH_STOP_TREADMILL_DECISION_0174WY_WZ_XA",
        "model_version": "0174WY_WZ_XA_TELEGRAM_DISPATCH_STOP_TREADMILL_DECISION_V1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "decision": "freeze_live_send_staircase_and_stop_ledger_treadmill",
        "reasons": [
            "capability_proven",
            "marginal_value_now_low",
            "artifact_bloat_high",
            "context_pulled_away_from_core_product",
        ],
        "next_product_work": NEXT_PRODUCT_WORK,
        "future_live_send_allowed_for": registry["future_live_send_allowed_for"],
        "future_live_send_not_allowed_for": registry["future_live_send_not_allowed_for"],
        "no_more_ledger_treadmill": True,
        "default_next_task_class": registry["default_next_task_class"],
        "registry_checksum": registry["registry_checksum"],
    }
    decision["stop_treadmill_decision_checksum"] = adapter.compute_checksum(decision)
    return decision


def render_doc(title, packet):
    lines = [f"# {title}", ""]
    for key in sorted(packet):
        value = packet[key]
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines) + "\n"


def write_artifacts(repo_root=".", output_dir=None):
    output_dir = output_dir or (pathlib.Path(repo_root) / DOC_REL_DIR)
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    registry = build_registry(repo_root)
    cert = build_freeze_certificate(registry)
    decision = build_stop_treadmill_decision(registry)
    artifacts = [
        (REGISTRY_PACKET, registry),
        (FREEZE_PACKET, cert),
        (DECISION_PACKET, decision),
    ]
    docs = [
        (REGISTRY_DOC, "Telegram Supervised Dispatch Capability Registry", registry),
        (FREEZE_DOC, "Telegram Dispatch Freeze Certificate", cert),
        (DECISION_DOC, "Telegram Dispatch Stop Treadmill Decision", decision),
    ]
    for name, packet in artifacts:
        (out / name).write_text(adapter.serialize(packet), encoding="utf-8", newline="\n")
    for name, title, packet in docs:
        (out / name).write_text(render_doc(title, packet), encoding="utf-8", newline="\n")
    return copy.deepcopy({"registry": registry, "freeze_certificate": cert, "stop_treadmill_decision": decision})


if __name__ == "__main__":
    result = write_artifacts(".")
    print("TELEGRAM_DISPATCH_STATUS", result["registry"]["telegram_channel_dispatch_status"])
    print("LATEST_ACCEPTED_LEDGER_COUNT", result["registry"]["latest_accepted_ledger_count"])
    print("LATEST_SUCCESSFUL_SEQUENCE", result["registry"]["latest_successful_sequence"])
    print("REGISTRY_CHECKSUM", result["registry"]["registry_checksum"])
    print("FREEZE_CERTIFICATE_CHECKSUM", result["freeze_certificate"]["freeze_certificate_checksum"])
    print("STOP_TREADMILL_DECISION_CHECKSUM", result["stop_treadmill_decision"]["stop_treadmill_decision_checksum"])
