"""Operator Decision Gate to Manual Export Precheck contract, 0175AR.

Deterministic local-only contract defining manual export prechecks for platforms.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.platform_review_bundle_operator_decision_gate_contract import (
    build_contract_packet as build_decision_gate_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AR_OPERATOR_DECISION_GATE_TO_MANUAL_EXPORT_PRECHECK_V0"
MATRIX_VERSION = "0175AR_OPERATOR_DECISION_GATE_TO_MANUAL_EXPORT_PRECHECK_V1"
SOURCE_BASELINE_COMMIT = "68a7e425d229d7876fdfa1f37a65f3ef8c388849"
LEDGER_FAMILY = "operator_decision_gate_to_manual_export_precheck_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AR"
PACKET_FILENAME = "operator_decision_gate_to_manual_export_precheck_contract_packet.json"
RUNBOOK_FILENAME = "operator_decision_gate_to_manual_export_precheck_contract.md"


def _asdict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, tuple):
        return [_asdict(v) for v in value]
    if isinstance(value, list):
        return [_asdict(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _asdict(v) for k, v in value.items()}
    return value


def _json(value: Any) -> str:
    return json.dumps(_asdict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _digest(value: Any) -> str:
    return sha256(_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ManualExportPrecheckTarget:
    platform_target_id: str
    export_target_type: str
    description: str


@dataclass(frozen=True)
class ManualExportPrecheckRule:
    rule_id: str
    description: str
    passed: bool = True


@dataclass(frozen=True)
class ManualExportPrecheckEvidenceRequirement:
    requirement_id: str
    description: str
    satisfied: bool = False


@dataclass(frozen=True)
class ManualExportPrecheckRecord:
    manual_export_precheck_id: str
    source_decision_gate_id: str
    source_bundle_item_id: str
    platform_target_id: str
    platform_family: str
    precheck_status: str
    export_target_type: str
    export_ready: bool
    manual_export_allowed: bool
    export_file_created: bool
    clipboard_payload_created: bool
    download_artifact_created: bool
    publishable_payload_created: bool
    platform_payload_created: bool
    operator_identity_status: str
    operator_signature_status: str
    payload_hash_lock_status: str
    citation_status: str
    limitation_status: str
    dqr_status: str
    readiness_status: str
    current_truth_status: str
    account_binding_status: str
    credential_gate_status: str
    manual_export_gate_status: str
    dispatch_gate_status: str
    precheck_rules: list[ManualExportPrecheckRule]
    evidence_requirements: list[ManualExportPrecheckEvidenceRequirement]
    blocked_reasons: list[str]
    missing_future_gates: list[str]
    packet_hash: str
    # Safety & Status Flags
    public_postable: bool = False
    publishable_text: bool = False
    platform_ready: bool = False
    dispatch_ready: bool = False
    approval_granted: bool = False
    approved_for_publication: bool = False
    operator_identity_bound: bool = False
    operator_signature_present: bool = False
    payload_hash_locked: bool = False
    account_binding_active: bool = False
    credential_values_loaded: bool = False
    platform_api_called: bool = False
    scheduler_enabled: bool = False


@dataclass(frozen=True)
class ManualExportPrecheckPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    precheck_records: list[ManualExportPrecheckRecord]
    precheck_targets: list[ManualExportPrecheckTarget]
    summary_counts: dict[str, int]
    safety_flags: dict[str, bool]
    blocked_capabilities: list[str]
    missing_future_gates: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_precheck_targets() -> list[ManualExportPrecheckTarget]:
    targets = {
        "x": ("x_manual_copy_precheck", "Precheck for manual copy to X platform"),
        "telegram_channel_destination": ("telegram_channel_manual_copy_precheck", "Precheck for manual copy to Telegram channel"),
        "telegram_remote_operator": ("telegram_remote_operator_review_log_precheck", "Precheck for Telegram operator remote log"),
        "substack": ("substack_manual_markdown_precheck", "Precheck for manual copy of Substack markdown copy"),
        "linkedin": ("linkedin_manual_copy_precheck", "Precheck for manual copy to LinkedIn professional network"),
        "threads": ("threads_manual_copy_precheck", "Precheck for manual copy to Meta Threads"),
        "instagram": ("instagram_caption_media_manual_precheck", "Precheck for manual copy of Instagram media caption"),
        "facebook_page": ("facebook_page_manual_copy_precheck", "Precheck for manual copy to Facebook page"),
        "tiktok": ("tiktok_caption_video_manual_precheck", "Precheck for manual copy of TikTok video caption"),
        "youtube": ("youtube_metadata_manual_precheck", "Precheck for manual copy of YouTube metadata descriptions")
    }
    return [
        ManualExportPrecheckTarget(platform_target_id=tid, export_target_type=val[0], description=val[1])
        for tid, val in targets.items()
    ]


def build_precheck_rules() -> list[ManualExportPrecheckRule]:
    rule_ids = [
        "no_export_file_created",
        "no_clipboard_payload_created",
        "no_download_artifact_created",
        "no_publishable_payload_created",
        "no_platform_payload_created",
        "no_platform_api_call",
        "no_credential_or_env_read",
        "no_account_binding_active",
        "no_scheduler",
        "no_autonomous_posting",
        "no_autonomous_reply_or_dm",
        "no_scraping",
        "no_financial_advice",
        "no_signal_language",
        "no_market_number_fabrication",
        "preserve_citation_requirements",
        "preserve_limitations",
        "preserve_dqr_readiness_blocks",
        "require_operator_signature",
        "require_payload_hash_lock",
        "require_manual_export_gate"
    ]
    descriptions = {rid: f"Enforce rule: {rid.replace('_', ' ')}" for rid in rule_ids}
    return [
        ManualExportPrecheckRule(rule_id=rid, description=descriptions[rid], passed=True)
        for rid in rule_ids
    ]


def build_evidence_requirements() -> list[ManualExportPrecheckEvidenceRequirement]:
    requirements = {
        "evidence_operator_identity_verified": "Verify operator identity matches key binding registry.",
        "evidence_approval_signature_verified": "Verify cryptographic approval signature matches operator key.",
        "evidence_payload_hash_lock_confirmed": "Verify payload hash lock matches draft variant snapshot.",
        "evidence_citation_clearance_verified": "Verify citation references are validated.",
        "evidence_limitation_ack_verified": "Verify limitation acknowledgement is logged.",
        "evidence_manual_export_gate_cleared": "Verify operator manual export gate is cleared."
    }
    return [
        ManualExportPrecheckEvidenceRequirement(requirement_id=rid, description=desc, satisfied=False)
        for rid, desc in requirements.items()
    ]


def build_safety_flags() -> dict[str, bool]:
    return {
        "local_only": True,
        "fixture_only": True,
        "schema_only": True,
        "manual_export_precheck_only": True,
        "decision_gate_only": True,
        "network_performed": False,
        "env_read": False,
        "credential_values_loaded": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "account_binding_active": False,
        "scheduler_enabled": False,
        "autonomous_posting": False,
        "autonomous_reply_or_dm": False,
        "scraping": False,
        "ingestion_repo_mutated": False,
        "dqr_cleared_by_contentops": False,
        "readiness_cleared_by_contentops": False,
        "current_truth_promoted": False,
        "public_postable": False,
        "dispatch_ready": False,
        "platform_payload_created": False,
        "publishable_payload_created": False,
        "export_ready": False,
        "manual_export_allowed": False,
        "export_file_created": False,
        "clipboard_payload_created": False,
        "download_artifact_created": False,
        "approval_granted": False,
        "approved_for_publication": False,
        "operator_approval_granted": False,
        "operator_identity_bound": False,
        "operator_signature_present": False,
        "payload_hash_locked": False,
        "financial_advice": False,
        "signal_language": False,
        "broker_order_execution": False,
        "raw_vendor_redistribution": False,
        "approved_internal_alpha_artifacts_available": False,
        "publishable_text": False,
        "platform_ready": False,
    }


def build_contract_packet() -> dict[str, Any]:
    # Consume 0175AQ operator decision gate precedent
    decision_gate_data = build_decision_gate_packet()
    gate_records = decision_gate_data.get("decision_gate_records", [])

    precheck_targets = build_precheck_targets()
    target_type_map = {t.platform_target_id: t.export_target_type for t in precheck_targets}

    rules = build_precheck_rules()
    evidence_reqs = build_evidence_requirements()

    blocked_reasons = [
        "blocked_no_operator_signature",
        "blocked_no_payload_hash_lock",
        "blocked_unresolved_citations",
        "blocked_unresolved_limitations",
        "blocked_dqr_readiness_unresolved",
        "blocked_no_export_gate",
        "blocked_no_publishable_payload"
    ]

    precheck_records: list[ManualExportPrecheckRecord] = []

    for rec in gate_records:
        tid = rec["platform_target_id"]
        family = rec["platform_family"]
        target_type = target_type_map.get(tid, "generic_manual_copy_precheck")

        raw_record = {
            "manual_export_precheck_id": f"manual_export_precheck_{tid}",
            "source_decision_gate_id": rec["decision_gate_id"],
            "source_bundle_item_id": rec["source_bundle_item_id"],
            "platform_target_id": tid,
            "platform_family": family,
            "precheck_status": "manual_export_precheck_blocked",
            "export_target_type": target_type,
            "export_ready": False,
            "manual_export_allowed": False,
            "export_file_created": False,
            "clipboard_payload_created": False,
            "download_artifact_created": False,
            "publishable_payload_created": False,
            "platform_payload_created": False,
            "operator_identity_status": rec["operator_identity_status"],
            "operator_signature_status": rec["operator_signature_status"],
            "payload_hash_lock_status": rec["payload_hash_lock_status"],
            "citation_status": rec["citation_status"],
            "limitation_status": rec["limitation_status"],
            "dqr_status": rec["dqr_status"],
            "readiness_status": rec["readiness_status"],
            "current_truth_status": rec["current_truth_status"],
            "account_binding_status": rec["account_binding_status"],
            "credential_gate_status": rec["credential_gate_status"],
            "manual_export_gate_status": "manual_export_gate_required_but_locked",
            "dispatch_gate_status": rec["dispatch_gate_status"],
            "precheck_rules": [_asdict(r) for r in rules],
            "evidence_requirements": [_asdict(er) for er in evidence_reqs],
            "blocked_reasons": blocked_reasons,
            "missing_future_gates": ["lane_c_platform_manual_export_precheck_to_export_packet_gate", "production_key_vault_decrypter", "live_operator_signature_vault"],
            # Safety & Status Flags
            "public_postable": False,
            "publishable_text": False,
            "platform_ready": False,
            "dispatch_ready": False,
            "approval_granted": False,
            "approved_for_publication": False,
            "operator_identity_bound": False,
            "operator_signature_present": False,
            "payload_hash_locked": False,
            "account_binding_active": False,
            "credential_values_loaded": False,
            "platform_api_called": False,
            "scheduler_enabled": False,
        }

        rec_hash = _digest(raw_record)
        precheck_records.append(
            ManualExportPrecheckRecord(
                packet_hash=rec_hash,
                **raw_record
            )
        )

    safety = build_safety_flags()

    summary_counts = {
        "registered_precheck_records_count": len(precheck_records),
        "precheck_targets_count": len(precheck_targets),
        "precheck_rules_count": len(rules),
        "evidence_requirements_count": len(evidence_reqs),
        "safety_flags_count": len(safety)
    }

    blocked_caps = [
        "live_publishing_dispatch",
        "autonomous_reply_automation",
        "live_credential_hydration",
        "active_scheduler_triggers",
        "manual_review_export"
    ]

    missing_gates = [
        "lane_c_platform_manual_export_precheck_to_export_packet_gate",
        "production_key_vault_decrypter",
        "live_operator_signature_vault"
    ]

    packet = ManualExportPrecheckPacket(
        task_label=TASK_LABEL,
        matrix_version=MATRIX_VERSION,
        source_baseline_commit=SOURCE_BASELINE_COMMIT,
        generated_at_epoch=0,
        precheck_records=precheck_records,
        precheck_targets=precheck_targets,
        summary_counts=summary_counts,
        safety_flags=safety,
        blocked_capabilities=blocked_caps,
        missing_future_gates=missing_gates,
        ledger_family=LEDGER_FAMILY,
        packet_hash="",
        hash_algorithm=HASH_ALGORITHM,
        next_required_gate="lane_c_platform_manual_export_precheck_to_export_packet_gate"
    )

    raw_packet = _asdict(packet)
    raw_packet.pop("packet_hash")
    packet_hash = _digest(raw_packet)

    final_packet = {
        "packet_hash": packet_hash,
        **raw_packet
    }
    return final_packet


def render_runbook(packet: dict[str, Any]) -> str:
    records = packet["precheck_records"]
    targets = packet["precheck_targets"]
    counts = packet["summary_counts"]
    safety = packet["safety_flags"]
    blocked_caps = packet["blocked_capabilities"]
    missing_gates = packet["missing_future_gates"]

    lines = [
        "# Operator Decision Gate to Manual Export Precheck Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a manual export precheck contract report for schema validation only.",
        "> It defines blocked precheck records and does not perform manual exports, approvals, or publications.",
        "> It cannot create export files, clipboard payloads, downloads, dispatches, schedules, or platform API calls.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Matrix Version**: `{packet['matrix_version']}`",
        f"- **Source Baseline Commit**: `{packet['source_baseline_commit']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        f"- **Next Required Gate**: `{packet['next_required_gate']}`",
        "",
        "## Invariant Validation Safety Flags",
        "",
        "| Invariant Flag | Required State | Status |",
        "|---|---|---|",
    ]

    for k, v in safety.items():
        lines.append(f"| `{k}` | `{v}` | ✅ |")

    lines.extend([
        "",
        "## Precheck Summary Counts",
        "",
        f"- **Registered Precheck Records**: `{counts['registered_precheck_records_count']}`",
        f"- **Registered Precheck Targets**: `{counts['precheck_targets_count']}`",
        f"- **Precheck Rules Configured**: `{counts['precheck_rules_count']}`",
        f"- **Evidence Requirements Defined**: `{counts['evidence_requirements_count']}`",
        "",
        "## Blocked Capabilities & Missing Gates",
        "",
        "### Blocked Capabilities",
    ])

    for bc in blocked_caps:
        lines.append(f"- `{bc}`")

    lines.extend([
        "",
        "### Missing Future Gates",
    ])

    for mg in missing_gates:
        lines.append(f"- `{mg}`")

    lines.extend([
        "",
        "## Precheck Target Configurations",
        "",
        "| Platform Target ID | Export Target Type | Description |",
        "|---|---|---|",
    ])

    for t in targets:
        lines.append(f"| `{t['platform_target_id']}` | `{t['export_target_type']}` | {t['description']} |")

    lines.extend([
        "",
        "## Platform Operator Decision Gate to Manual Export Precheck Records",
        "",
    ])

    for r in records:
        lines.extend([
            f"### Precheck Record: `{r['manual_export_precheck_id']}`",
            "",
            f"- **Source Decision Gate ID**: `{r['source_decision_gate_id']}`",
            f"- **Source Bundle Item ID**: `{r['source_bundle_item_id']}`",
            f"- **Platform Target ID**: `{r['platform_target_id']}`",
            f"- **Platform Family**: `{r['platform_family']}`",
            f"- **Precheck Status**: `{r['precheck_status']}`",
            f"- **Export Target Type**: `{r['export_target_type']}`",
            f"- **Export Ready**: `{r['export_ready']}`",
            f"- **Manual Export Allowed**: `{r['manual_export_allowed']}`",
            f"- **Export File Created**: `{r['export_file_created']}`",
            f"- **Clipboard Payload Created**: `{r['clipboard_payload_created']}`",
            f"- **Download Artifact Created**: `{r['download_artifact_created']}`",
            f"- **Publishable Payload Created**: `{r['publishable_payload_created']}`",
            f"- **Platform Payload Created**: `{r['platform_payload_created']}`",
            f"- **Operator Identity Status**: `{r['operator_identity_status']}`",
            f"- **Operator Signature Status**: `{r['operator_signature_status']}`",
            f"- **Payload Hash Lock**: `{r['payload_hash_lock_status']}`",
            f"- **Citation Status**: `{r['citation_status']}`",
            f"- **Limitation Status**: `{r['limitation_status']}`",
            f"- **DQR Status**: `{r['dqr_status']}`",
            f"- **Readiness Status**: `{r['readiness_status']}`",
            f"- **Current Truth Status**: `{r['current_truth_status']}`",
            f"- **Account Binding**: `{r['account_binding_status']}`",
            f"- **Credential Gate**: `{r['credential_gate_status']}`",
            f"- **Manual Export Gate**: `{r['manual_export_gate_status']}`",
            f"- **Dispatch Gate**: `{r['dispatch_gate_status']}`",
            "",
            "#### Safety Invariants Status",
            "",
            f"- **Public Postable**: `{r['public_postable']}`",
            f"- **Publishable Text**: `{r['publishable_text']}`",
            f"- **Platform Ready**: `{r['platform_ready']}`",
            f"- **Dispatch Ready**: `{r['dispatch_ready']}`",
            f"- **Approval Granted**: `{r['approval_granted']}`",
            f"- **Approved for Publication**: `{r['approved_for_publication']}`",
            f"- **Operator Identity Bound**: `{r['operator_identity_bound']}`",
            f"- **Operator Signature Present**: `{r['operator_signature_present']}`",
            f"- **Payload Hash Locked**: `{r['payload_hash_locked']}`",
            "",
            "#### Precheck Evaluation Rules (All Enforced)",
            "",
            "| Rule ID | Description | Passed Status |",
            "|---|---|---|",
        ])

        for rule in r["precheck_rules"]:
            lines.append(
                f"| `{rule['rule_id']}` | {rule['description']} | `{rule['passed']}` |"
            )

        lines.extend([
            "",
            "#### Evidence Requirements (Pending)",
            "",
            "| Requirement ID | Description | Satisfied |",
            "|---|---|---|",
        ])

        for er in r["evidence_requirements"]:
            lines.append(
                f"| `{er['requirement_id']}` | {er['description']} | `{er['satisfied']}` |"
            )

        lines.extend([
            "",
            "#### Blocked Reasons (Active)",
            "",
        ])

        for br in r["blocked_reasons"]:
            lines.append(f"- `{br}`")
        lines.append("")

    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AR")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
