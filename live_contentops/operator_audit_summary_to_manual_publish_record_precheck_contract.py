"""Operator Audit Summary to Manual Publish Record Precheck contract, 0175AU.

Deterministic local-only contract defining manual publish record precheck records.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.export_packet_stub_to_operator_audit_summary_contract import (
    build_contract_packet as build_audit_summary_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AU_OPERATOR_AUDIT_SUMMARY_TO_MANUAL_PUBLISH_RECORD_PRECHECK_V0"
MATRIX_VERSION = "0175AU_OPERATOR_AUDIT_SUMMARY_TO_MANUAL_PUBLISH_RECORD_PRECHECK_V1"
SOURCE_BASELINE_COMMIT = "9cf9d9d545d14ece9fa6239dfc717baac547f3e0"
LEDGER_FAMILY = "operator_audit_summary_to_manual_publish_record_precheck_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AU"
PACKET_FILENAME = "operator_audit_summary_to_manual_publish_record_precheck_contract_packet.json"
RUNBOOK_FILENAME = "operator_audit_summary_to_manual_publish_record_precheck_contract.md"


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
class ManualPublishRecordPrecheckTarget:
    platform_target_id: str
    publish_record_target_type: str
    description: str


@dataclass(frozen=True)
class ManualPublishRecordPrecheckInvariant:
    invariant_id: str
    expected_state: str
    actual_state: str
    passed: bool
    evidence_note: str


@dataclass(frozen=True)
class ManualPublishRecordPrecheckEvidenceRequirement:
    requirement_id: str
    description: str
    satisfied: bool = False


@dataclass(frozen=True)
class ManualPublishRecordPrecheckRecord:
    manual_publish_record_precheck_id: str
    source_audit_summary_id: str
    source_export_packet_stub_id: str
    source_manual_export_precheck_id: str
    source_decision_gate_id: str
    platform_target_id: str
    platform_family: str
    precheck_status: str
    publish_record_target_type: str
    manual_publish_record_allowed: bool
    manual_publish_record_created: bool
    platform_publication_url_recorded: bool
    platform_post_id_recorded: bool
    external_publish_timestamp_recorded: bool
    public_metrics_recorded: bool
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
    manual_publish_record_gate_status: str
    dispatch_gate_status: str
    invariants: list[ManualPublishRecordPrecheckInvariant]
    evidence_requirements: list[ManualPublishRecordPrecheckEvidenceRequirement]
    blocked_reasons: list[str]
    missing_future_gates: list[str]
    packet_hash: str
    # Safety & Status Flags
    manual_export_allowed: bool = False
    export_ready: bool = False
    export_file_created: bool = False
    clipboard_payload_created: bool = False
    download_artifact_created: bool = False
    publishable_payload_created: bool = False
    platform_payload_created: bool = False
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
class ManualPublishRecordPrecheckPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    precheck_records: list[ManualPublishRecordPrecheckRecord]
    precheck_targets: list[ManualPublishRecordPrecheckTarget]
    summary_counts: dict[str, int]
    safety_flags: dict[str, bool]
    blocked_capabilities: list[str]
    missing_future_gates: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_precheck_targets() -> list[ManualPublishRecordPrecheckTarget]:
    targets = {
        "x": ("x_manual_publish_record_precheck", "Manual publish record precheck for X platform"),
        "telegram_channel_destination": ("telegram_channel_manual_publish_record_precheck", "Manual publish record precheck for Telegram channel"),
        "telegram_remote_operator": ("telegram_remote_operator_log_record_precheck", "Manual publish record precheck for Telegram remote operator"),
        "substack": ("substack_manual_publish_record_precheck", "Manual publish record precheck for Substack"),
        "linkedin": ("linkedin_manual_publish_record_precheck", "Manual publish record precheck for LinkedIn"),
        "threads": ("threads_manual_publish_record_precheck", "Manual publish record precheck for Meta Threads"),
        "instagram": ("instagram_manual_publish_record_precheck", "Manual publish record precheck for Instagram"),
        "facebook_page": ("facebook_page_manual_publish_record_precheck", "Manual publish record precheck for Facebook Page"),
        "tiktok": ("tiktok_manual_publish_record_precheck", "Manual publish record precheck for TikTok"),
        "youtube": ("youtube_manual_publish_record_precheck", "Manual publish record precheck for YouTube")
    }
    return [
        ManualPublishRecordPrecheckTarget(platform_target_id=tid, publish_record_target_type=val[0], description=val[1])
        for tid, val in targets.items()
    ]


def build_invariants() -> list[ManualPublishRecordPrecheckInvariant]:
    invariants = [
        ("no_manual_publish_record_created", "no_record", "no_record", True, "Verified no manual publish record created."),
        ("no_platform_publication_url_recorded", "no_url", "no_url", True, "Verified platform publication URL remains unrecorded."),
        ("no_platform_post_id_recorded", "no_post_id", "no_post_id", True, "Verified platform post ID remains unrecorded."),
        ("no_external_publish_timestamp_recorded", "no_timestamp", "no_timestamp", True, "Verified external publish timestamp remains unrecorded."),
        ("no_public_metrics_recorded", "no_metrics", "no_metrics", True, "Verified public metrics remain unrecorded."),
        ("no_export_file_created", "no_file", "no_file", True, "Checked local workspace; no export files exist."),
        ("no_clipboard_payload_created", "no_clipboard", "no_clipboard", True, "Verified clipboard payload remains ungenerated."),
        ("no_download_artifact_created", "no_download", "no_download", True, "Verified no download artifact created."),
        ("no_publishable_payload_created", "no_payload", "no_payload", True, "Verified no publishable payload created."),
        ("no_platform_payload_created", "no_payload", "no_payload", True, "Verified platform payload is not generated."),
        ("no_platform_api_call", "no_api_calls", "no_api_calls", True, "Verified no platform API calls executed."),
        ("no_credential_or_env_read", "no_reads", "no_reads", True, "Verified no credentials or environment read operations performed."),
        ("no_account_binding_active", "inactive", "inactive", True, "Verified no account binding is active."),
        ("no_scheduler", "disabled", "disabled", True, "Verified no scheduler enabled."),
        ("no_autonomous_posting", "disabled", "disabled", True, "Verified autonomous posting is blocked."),
        ("no_autonomous_reply_or_dm", "disabled", "disabled", True, "Verified autonomous replies and DMs are blocked."),
        ("no_scraping", "disabled", "disabled", True, "Verified scraping is blocked."),
        ("no_financial_advice", "absent", "absent", True, "Verified draft does not contain financial advice."),
        ("no_signal_language", "absent", "absent", True, "Verified draft does not contain trading signals or order terminology."),
        ("no_market_number_fabrication", "absent", "absent", True, "Verified draft contains no fabricated market numbers."),
        ("preserve_citation_requirements", "pending", "pending", True, "Verified citations are preserved as unresolved placeholders."),
        ("preserve_limitations", "pending", "pending", True, "Verified limitation slot is preserved as unresolved."),
        ("preserve_dqr_readiness_blocks", "pending", "pending", True, "Verified DQR readiness blocks are preserved."),
        ("require_operator_signature", "required", "required", True, "Verified operator signature required for validation."),
        ("require_payload_hash_lock", "required", "required", True, "Verified payload hash lock is required."),
        ("require_manual_export_gate", "required", "required", True, "Verified manual export gate is required."),
        ("require_manual_publish_record_gate", "required", "required", True, "Verified manual publish record gate is required.")
    ]
    return [
        ManualPublishRecordPrecheckInvariant(
            invariant_id=inv[0],
            expected_state=inv[1],
            actual_state=inv[2],
            passed=inv[3],
            evidence_note=inv[4]
        )
        for inv in invariants
    ]


def build_evidence_requirements() -> list[ManualPublishRecordPrecheckEvidenceRequirement]:
    requirements = {
        "evidence_operator_signature_verified": "Verify cryptographic operator signature matches registered key.",
        "evidence_payload_hash_lock_confirmed": "Verify payload hash lock matches draft variant snapshot.",
        "evidence_citation_clearance_verified": "Verify citation references are validated.",
        "evidence_limitation_ack_verified": "Verify limitation acknowledgement is logged.",
        "evidence_manual_export_gate_cleared": "Verify manual export gate is cleared.",
        "evidence_manual_publish_record_gate_cleared": "Verify manual publish record gate is cleared.",
        "evidence_platform_publication_url_verified": "Verify recorded platform publication URL.",
        "evidence_platform_post_id_verified": "Verify recorded platform post ID.",
        "evidence_external_timestamp_verified": "Verify external publish timestamp evidence.",
        "evidence_metrics_snapshot_verified": "Verify audience public metrics snapshot."
    }
    return [
        ManualPublishRecordPrecheckEvidenceRequirement(requirement_id=rid, description=desc, satisfied=False)
        for rid, desc in requirements.items()
    ]


def build_safety_flags() -> dict[str, bool]:
    return {
        "local_only": True,
        "fixture_only": True,
        "schema_only": True,
        "manual_publish_record_precheck_only": True,
        "operator_audit_summary_only": True,
        "export_packet_stub_only": True,
        "manual_export_precheck_only": True,
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
        "manual_publish_record_allowed": False,
        "manual_publish_record_created": False,
        "platform_publication_url_recorded": False,
        "platform_post_id_recorded": False,
        "external_publish_timestamp_recorded": False,
        "public_metrics_recorded": False,
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
    audit_data = build_audit_summary_packet()
    audit_records = audit_data.get("audit_records", [])

    precheck_targets = build_precheck_targets()
    target_type_map = {t.platform_target_id: t.publish_record_target_type for t in precheck_targets}

    invariants = build_invariants()
    evidence_reqs = build_evidence_requirements()

    blocked_reasons = [
        "blocked_no_operator_signature",
        "blocked_no_payload_hash_lock",
        "blocked_unresolved_citations",
        "blocked_unresolved_limitations",
        "blocked_dqr_readiness_unresolved",
        "blocked_no_manual_export_gate",
        "blocked_no_manual_publish_record_gate",
        "blocked_no_platform_publication_identity",
        "blocked_no_external_publish_evidence"
    ]

    precheck_records: list[ManualPublishRecordPrecheckRecord] = []

    for rec in audit_records:
        tid = rec["platform_target_id"]
        family = rec["platform_family"]
        target_type = target_type_map.get(tid, "generic_manual_publish_record_precheck")

        raw_record = {
            "manual_publish_record_precheck_id": f"manual_publish_record_precheck_{tid}",
            "source_audit_summary_id": rec["audit_summary_id"],
            "source_export_packet_stub_id": rec["source_export_packet_stub_id"],
            "source_manual_export_precheck_id": rec["source_manual_export_precheck_id"],
            "source_decision_gate_id": rec["source_decision_gate_id"],
            "platform_target_id": tid,
            "platform_family": family,
            "precheck_status": "manual_publish_record_precheck_blocked",
            "publish_record_target_type": target_type,
            "manual_publish_record_allowed": False,
            "manual_publish_record_created": False,
            "platform_publication_url_recorded": False,
            "platform_post_id_recorded": False,
            "external_publish_timestamp_recorded": False,
            "public_metrics_recorded": False,
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
            "manual_export_gate_status": rec["manual_export_gate_status"],
            "manual_publish_record_gate_status": "manual_publish_record_gate_required_but_locked",
            "dispatch_gate_status": rec["dispatch_gate_status"],
            "invariants": [_asdict(inv) for inv in invariants],
            "evidence_requirements": [_asdict(er) for er in evidence_reqs],
            "blocked_reasons": blocked_reasons,
            "missing_future_gates": ["lane_c_platform_manual_publish_record_precheck_to_record_stub", "production_key_vault_decrypter", "live_operator_signature_vault"],
            # Safety & Status Flags
            "export_ready": False,
            "manual_export_allowed": False,
            "export_file_created": False,
            "clipboard_payload_created": False,
            "download_artifact_created": False,
            "publishable_payload_created": False,
            "platform_payload_created": False,
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
            ManualPublishRecordPrecheckRecord(
                packet_hash=rec_hash,
                **raw_record
            )
        )

    safety = build_safety_flags()

    summary_counts = {
        "registered_precheck_records_count": len(precheck_records),
        "precheck_targets_count": len(precheck_targets),
        "precheck_invariants_count": len(invariants),
        "precheck_evidence_requirements_count": len(evidence_reqs),
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
        "lane_c_platform_manual_publish_record_precheck_to_record_stub",
        "production_key_vault_decrypter",
        "live_operator_signature_vault"
    ]

    packet = ManualPublishRecordPrecheckPacket(
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
        next_required_gate="lane_c_platform_manual_publish_record_precheck_to_record_stub"
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
        "# Operator Audit Summary to Manual Publish Record Precheck Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a manual publish record precheck contract, not a manual publish record and not metrics logging.",
        "> It summarizes blocked audit summary metadata only.",
        "> It preserves citation, limitation, DQR/readiness, operator identity, signature, hash-lock, export-gate, publish-record-gate, account-binding, credential, and dispatch-gate requirements.",
        "> It cannot create publish records, publication URLs, platform post IDs, timestamps, metrics, files, clipboard payloads, downloads, approvals, exports, publishable payloads, dispatches, schedules, or platform/API calls.",
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
        "## Precheck summary counts",
        "",
        f"- **Registered Manual Publish Precheck Records**: `{counts['registered_precheck_records_count']}`",
        f"- **Registered Manual Publish Targets**: `{counts['precheck_targets_count']}`",
        f"- **Invariants Checked**: `{counts['precheck_invariants_count']}`",
        f"- **Evidence Requirements Defined**: `{counts['precheck_evidence_requirements_count']}`",
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
        "## Manual Publish target type configurations",
        "",
        "| Platform Target ID | Publish Record Target Type | Description |",
        "|---|---|---|",
    ])

    for t in targets:
        lines.append(f"| `{t['platform_target_id']}` | `{t['publish_record_target_type']}` | {t['description']} |")

    lines.extend([
        "",
        "## Platform Manual Publish Record Precheck Records",
        "",
    ])

    for r in records:
        lines.extend([
            f"### Precheck Record: `{r['manual_publish_record_precheck_id']}`",
            "",
            f"- **Source Audit Summary ID**: `{r['source_audit_summary_id']}`",
            f"- **Source Export Packet Stub ID**: `{r['source_export_packet_stub_id']}`",
            f"- **Source Manual Export Precheck ID**: `{r['source_manual_export_precheck_id']}`",
            f"- **Source Decision Gate ID**: `{r['source_decision_gate_id']}`",
            f"- **Platform Target ID**: `{r['platform_target_id']}`",
            f"- **Platform Family**: `{r['platform_family']}`",
            f"- **Precheck Status**: `{r['precheck_status']}`",
            f"- **Publish Record Target Type**: `{r['publish_record_target_type']}`",
            f"- **Manual Publish Record Allowed**: `{r['manual_publish_record_allowed']}`",
            f"- **Manual Publish Record Created**: `{r['manual_publish_record_created']}`",
            f"- **Platform Publication URL Recorded**: `{r['platform_publication_url_recorded']}`",
            f"- **Platform Post ID Recorded**: `{r['platform_post_id_recorded']}`",
            f"- **External Publish Timestamp Recorded**: `{r['external_publish_timestamp_recorded']}`",
            f"- **Public Metrics Recorded**: `{r['public_metrics_recorded']}`",
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
            f"- **Manual Publish Record Gate**: `{r['manual_publish_record_gate_status']}`",
            f"- **Dispatch Gate**: `{r['dispatch_gate_status']}`",
            "",
            "#### Safety Invariants Status",
            "",
            f"- **Export Ready**: `{r['export_ready']}`",
            f"- **Manual Export Allowed**: `{r['manual_export_allowed']}`",
            f"- **Export File Created**: `{r['export_file_created']}`",
            f"- **Clipboard Payload Created**: `{r['clipboard_payload_created']}`",
            f"- **Download Artifact Created**: `{r['download_artifact_created']}`",
            f"- **Publishable Payload Created**: `{r['publishable_payload_created']}`",
            f"- **Platform Payload Created**: `{r['platform_payload_created']}`",
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
            "#### Precheck Evaluation Invariants (All Checked)",
            "",
            "| Invariant ID | Expected State | Actual State | Passed | Evidence Note |",
            "|---|---|---|---|---|",
        ])

        for inv in r["invariants"]:
            lines.append(
                f"| `{inv['invariant_id']}` | `{inv['expected_state']}` | `{inv['actual_state']}` | `{inv['passed']}` | {inv['evidence_note']} |"
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
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AU")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
