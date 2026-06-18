"""Supervised dispatch readiness policy (LOCAL, BLOCKER-FIRST, NO DISPATCH)."""

import copy
import json
import os.path
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from live_contentops import telegram_local_adapter_contract as adapter

TASK_LABEL = "TASK_CONTENTOPS_0174XZ_YA_YB_SUPERVISED_DISPATCH_READINESS_SUMMARY_V0"
MODEL = "SUPERVISED_DISPATCH_READINESS_POLICY_0174XZ_YA_YB"
MODEL_VERSION = "0174XZ_YA_YB_SUPERVISED_DISPATCH_READINESS_POLICY_V1"
SOURCE_BASELINE_COMMIT = "397a9cdbd020bcdf46bbb464ab9752e9be6b1e98"
DOC_REL_DIR = os.path.join("docs", "automation", "0174XZ_YA_YB")
POLICY_PACKET = "supervised_dispatch_readiness_policy_packet.json"
POLICY_DOC = "supervised_dispatch_readiness_policy.md"

READINESS_CLASS = "NOT_READY_FOR_LIVE_DISPATCH"
LOCAL_GOVERNANCE_STATUS = "PASS_DRY_RUN_CHAIN"
LIVE_DISPATCH_STATUS = "BLOCKED"
SUPPORTED_PRIMARY_PLATFORMS = ["x", "telegram", "substack"]
PLATFORM_READINESS = {
    "telegram": "DISPATCH_PROVEN_FROZEN_NO_SEND",
    "x": "DRY_RUN_ONLY_NO_API",
    "substack": "MANUAL_EXPORT_ONLY_NO_API",
}
REQUIRED_FUTURE_GATES = [
    "kill_switch_activation",
    "redacted_audit_packet",
    "manual_fallback_proof",
    "operator_supervision_window",
    "live_dispatch_separate_approval",
]
LIVE_BLOCKERS = [
    "kill switch activation missing",
    "redacted audit packet for real platform response missing",
    "manual fallback proof missing",
    "operator supervision window missing",
    "live dispatch separate approval missing",
    "credential hydration forbidden in current chain",
    "platform API calls forbidden in current chain",
    "provider response not called",
    "request budget used is 0",
    "final URL not verified",
]
DRY_RUN_CAPABILITIES_PROVEN = [
    "remote operator intent ingress fixture accepted",
    "deterministic intent and editorial brief fixtures reconciled",
    "review-only platform payload previews hashed",
    "approval challenge candidate contract created",
    "approval ledger candidate contract created",
    "dispatch outbox candidate contract created",
    "dispatch gate matrix evaluated",
    "redacted dispatch audit dry-run events recorded",
    "payload hash binding preserved through local chain",
]
FORBIDDEN_CAPABILITIES = [
    "autonomous posting",
    "scheduling",
    "autonomous replies",
    "direct messages",
    "scraping",
    "trading or signal behavior",
    "credential hydration",
    "platform API calls",
    "provider API calls",
    "public content generation",
    "live state creation",
    "raw request or response persistence",
    "token logging",
]
FORBIDDEN_READINESS_CLAIMS = [
    "production-ready",
    "live-ready",
    "dispatch-ready",
    "public-postable",
    "ready to send",
]
SAFETY_FLAGS = {
    "is_local_only": True,
    "network_performed": False,
    "telegram_api_called": False,
    "x_api_called": False,
    "substack_api_called": False,
    "platform_api_called": False,
    "provider_api_called": False,
    "llm_provider_api_called": False,
    "env_read": False,
    "dotenv_read": False,
    "credential_read": False,
    "credential_hydration_performed": False,
    "scheduler_enabled": False,
    "live_post_performed": False,
    "autonomous_replies_or_dms": False,
    "scraping_performed": False,
    "public_ready_content_generated": False,
    "platform_dispatch_performed": False,
    "live_ready_state_created": False,
    "raw_request_persisted": False,
    "raw_response_persisted": False,
    "token_logged": False,
}


def safety_flags():
    return copy.deepcopy(SAFETY_FLAGS)


def readiness_values():
    return {
        "readiness_class": READINESS_CLASS,
        "local_governance_status": LOCAL_GOVERNANCE_STATUS,
        "live_dispatch_status": LIVE_DISPATCH_STATUS,
        "supported_primary_platforms": list(SUPPORTED_PRIMARY_PLATFORMS),
        "platform_readiness": copy.deepcopy(PLATFORM_READINESS),
        "required_future_gates": list(REQUIRED_FUTURE_GATES),
        "live_blockers": list(LIVE_BLOCKERS),
        "dry_run_capabilities_proven": list(DRY_RUN_CAPABILITIES_PROVEN),
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES),
    }


def _scalar_strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "forbidden_readiness_claims":
                continue
            yield from _scalar_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _scalar_strings(item)
    elif isinstance(value, str):
        yield value.lower()


def validate_no_forbidden_readiness_claims(value):
    text = " ".join(_scalar_strings(value))
    for claim in FORBIDDEN_READINESS_CLAIMS:
        if claim in text:
            raise ValueError("forbidden_readiness_claim")
    return True


def build_policy_packet():
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        **safety_flags(),
        **readiness_values(),
        "forbidden_readiness_claims": list(FORBIDDEN_READINESS_CLAIMS),
        "summary_must_not_create_live_readiness": True,
        "next_task_must_be_manual_export_or_review_surface": True,
        "status": "pass",
    }
    validate_no_forbidden_readiness_claims(packet)
    packet["supervised_dispatch_readiness_policy_checksum"] = adapter.compute_checksum(packet)
    return packet


def render_doc(title, packet):
    lines = [f"# {title}", "", "> [!IMPORTANT]", "> Blocker-first local readiness policy. Live dispatch remains blocked and no live state is created.", ""]
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
    packet = build_policy_packet()
    (out / POLICY_PACKET).write_text(adapter.serialize(packet), encoding="utf-8", newline="\n")
    (out / POLICY_DOC).write_text(render_doc("Supervised Dispatch Readiness Policy", packet), encoding="utf-8", newline="\n")
    return copy.deepcopy(packet)


if __name__ == "__main__":
    result = write_artifacts(".")
    print("SUPERVISED_DISPATCH_READINESS_POLICY_CHECKSUM", result["supervised_dispatch_readiness_policy_checksum"])
