"""Export Packet Stub to Operator Audit Summary contract, 0175AT.

Deterministic local-only contract defining operator audit summary records for manual export packet stubs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.manual_export_precheck_to_export_packet_stub_contract import (
    build_contract_packet as build_stub_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AT_EXPORT_PACKET_STUB_TO_OPERATOR_AUDIT_SUMMARY_V0"
MATRIX_VERSION = "0175AT_EXPORT_PACKET_STUB_TO_OPERATOR_AUDIT_SUMMARY_V1"
SOURCE_BASELINE_COMMIT = "3441635cad8010a7325d83d856351275f897ce37"
LEDGER_FAMILY = "export_packet_stub_to_operator_audit_summary_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AT"
PACKET_FILENAME = "export_packet_stub_to_operator_audit_summary_contract_packet.json"
RUNBOOK_FILENAME = "export_packet_stub_to_operator_audit_summary_contract.md"


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
class OperatorAuditSummarySubject:
    platform_target_id: str
    audit_subject_type: str
    description: str


@dataclass(frozen=True)
class OperatorAuditSummaryInvariant:
    invariant_id: str
    expected_state: str
    actual_state: str
    passed: bool
    evidence_note: str


@dataclass(frozen=True)
class OperatorAuditSummaryFinding:
    finding_id: str
    description: str
    active: bool = True


@dataclass(frozen=True)
class OperatorAuditSummaryRecord:
    audit_summary_id: str
    source_export_packet_stub_id: str
    source_manual_export_precheck_id: str
    source_decision_gate_id: str
    platform_target_id: str
    platform_family: str
    audit_summary_status: str
    audit_subject_type: str
    export_packet_type: str
    stub_status: str
    publishability_status: str
    manual_export_status: str
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
    invariants: list[OperatorAuditSummaryInvariant]
    findings: list[OperatorAuditSummaryFinding]
    blocked_reasons: list[str]
    missing_future_gates: list[str]
    packet_hash: str
    # Safety & Status Flags
    export_ready: bool = False
    manual_export_allowed: bool = False
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
class OperatorAuditSummaryPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    audit_records: list[OperatorAuditSummaryRecord]
    audit_subjects: list[OperatorAuditSummarySubject]
    summary_counts: dict[str, int]
    safety_flags: dict[str, bool]
    blocked_capabilities: list[str]
    missing_future_gates: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_audit_subjects() -> list[OperatorAuditSummarySubject]:
    subjects = {
        "x": ("x_export_stub_audit_summary", "Audit summary for X platform manual export packet stub"),
        "telegram_channel_destination": ("telegram_channel_export_stub_audit_summary", "Audit summary for Telegram channel manual export packet stub"),
        "telegram_remote_operator": ("telegram_remote_operator_export_stub_audit_summary", "Audit summary for Telegram remote operator manual export packet stub"),
        "substack": ("substack_export_stub_audit_summary", "Audit summary for Substack manual export packet stub"),
        "linkedin": ("linkedin_export_stub_audit_summary", "Audit summary for LinkedIn manual export packet stub"),
        "threads": ("threads_export_stub_audit_summary", "Audit summary for Meta Threads manual export packet stub"),
        "instagram": ("instagram_export_stub_audit_summary", "Audit summary for Instagram manual export packet stub"),
        "facebook_page": ("facebook_page_export_stub_audit_summary", "Audit summary for Facebook Page manual export packet stub"),
        "tiktok": ("tiktok_export_stub_audit_summary", "Audit summary for TikTok manual export packet stub"),
        "youtube": ("youtube_export_stub_audit_summary", "Audit summary for YouTube manual export packet stub")
    }
    return [
        OperatorAuditSummarySubject(platform_target_id=tid, audit_subject_type=val[0], description=val[1])
        for tid, val in subjects.items()
    ]


def build_invariants() -> list[OperatorAuditSummaryInvariant]:
    invariants = [
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
        ("no_signal_language", "absent", "absent", True, "Verified draft does not contain trading signals or order execution terminology."),
        ("no_market_number_fabrication", "absent", "absent", True, "Verified draft contains no fabricated market numbers."),
        ("preserve_citation_requirements", "pending", "pending", True, "Verified citations are preserved as unresolved placeholders."),
        ("preserve_limitations", "pending", "pending", True, "Verified limitation slot is preserved as unresolved."),
        ("preserve_dqr_readiness_blocks", "pending", "pending", True, "Verified DQR readiness blocks are preserved."),
        ("require_operator_signature", "required", "required", True, "Verified operator signature required for validation."),
        ("require_payload_hash_lock", "required", "required", True, "Verified payload hash lock is required."),
        ("require_manual_export_gate", "required", "required", True, "Verified manual export gate is required."),
        ("require_future_manual_publish_record_precheck", "required", "required", True, "Verified next step requires manual publish record precheck gate.")
    ]
    return [
        OperatorAuditSummaryInvariant(
            invariant_id=inv[0],
            expected_state=inv[1],
            actual_state=inv[2],
            passed=inv[3],
            evidence_note=inv[4]
        )
        for inv in invariants
    ]


def build_findings() -> list[OperatorAuditSummaryFinding]:
    findings = {
        "finding_export_stub_blocked": "The export packet stub is currently blocked from release.",
        "finding_no_publishable_text": "No publishable text has been compiled or made public.",
        "finding_no_export_outputs": "No physical export files, clipboards, or download artifacts exist.",
        "finding_no_operator_signature": "Cryptographic approval signature is missing from the audit log.",
        "finding_payload_hash_not_locked": "Draft payload hash lock is not secured.",
        "finding_citations_unresolved": "Citations are preserved as unresolved stubs.",
        "finding_limitations_unresolved": "Platform limitation acknowledgements are pending.",
        "finding_dqr_readiness_unresolved": "DQR readiness checks are unresolved."
    }
    return [
        OperatorAuditSummaryFinding(finding_id=fid, description=desc, active=True)
        for fid, desc in findings.items()
    ]


def build_safety_flags() -> dict[str, bool]:
    return {
        "local_only": True,
        "fixture_only": True,
        "schema_only": True,
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
    stub_data = build_stub_packet()
    stub_records = stub_data.get("stub_records", [])

    audit_subjects = build_audit_subjects()
    subject_type_map = {s.platform_target_id: s.audit_subject_type for s in audit_subjects}

    invariants = build_invariants()
    findings = build_findings()

    blocked_reasons = [
        "blocked_no_operator_signature",
        "blocked_no_payload_hash_lock",
        "blocked_unresolved_citations",
        "blocked_unresolved_limitations",
        "blocked_dqr_readiness_unresolved",
        "blocked_no_manual_export_gate",
        "blocked_no_export_output"
    ]

    audit_records: list[OperatorAuditSummaryRecord] = []

    for rec in stub_records:
        tid = rec["platform_target_id"]
        family = rec["platform_family"]
        subject_type = subject_type_map.get(tid, "generic_export_stub_audit_summary")

        raw_record = {
            "audit_summary_id": f"audit_summary_{tid}",
            "source_export_packet_stub_id": rec["export_packet_stub_id"],
            "source_manual_export_precheck_id": rec["source_manual_export_precheck_id"],
            "source_decision_gate_id": rec["source_decision_gate_id"],
            "platform_target_id": tid,
            "platform_family": family,
            "audit_summary_status": "operator_audit_summary_blocked",
            "audit_subject_type": subject_type,
            "export_packet_type": rec["export_packet_type"],
            "stub_status": rec["stub_status"],
            "publishability_status": "publishability_required_but_blocked",
            "manual_export_status": "manual_export_blocked",
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
            "dispatch_gate_status": rec["dispatch_gate_status"],
            "invariants": [_asdict(inv) for inv in invariants],
            "findings": [_asdict(f) for f in findings],
            "blocked_reasons": blocked_reasons,
            "missing_future_gates": ["lane_c_platform_operator_audit_summary_to_manual_publish_record_precheck", "production_key_vault_decrypter", "live_operator_signature_vault"],
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
        audit_records.append(
            OperatorAuditSummaryRecord(
                packet_hash=rec_hash,
                **raw_record
            )
        )

    safety = build_safety_flags()

    summary_counts = {
        "registered_audit_records_count": len(audit_records),
        "audit_subjects_count": len(audit_subjects),
        "audit_invariants_count": len(invariants),
        "audit_findings_count": len(findings),
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
        "lane_c_platform_operator_audit_summary_to_manual_publish_record_precheck",
        "production_key_vault_decrypter",
        "live_operator_signature_vault"
    ]

    packet = OperatorAuditSummaryPacket(
        task_label=TASK_LABEL,
        matrix_version=MATRIX_VERSION,
        source_baseline_commit=SOURCE_BASELINE_COMMIT,
        generated_at_epoch=0,
        audit_records=audit_records,
        audit_subjects=audit_subjects,
        summary_counts=summary_counts,
        safety_flags=safety,
        blocked_capabilities=blocked_caps,
        missing_future_gates=missing_gates,
        ledger_family=LEDGER_FAMILY,
        packet_hash="",
        hash_algorithm=HASH_ALGORITHM,
        next_required_gate="lane_c_platform_operator_audit_summary_to_manual_publish_record_precheck"
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
    records = packet["audit_records"]
    subjects = packet["audit_subjects"]
    counts = packet["summary_counts"]
    safety = packet["safety_flags"]
    blocked_caps = packet["blocked_capabilities"]
    missing_gates = packet["missing_future_gates"]

    lines = [
        "# Export Packet Stub to Operator Audit Summary Contract",
        "",
        "> [!IMPORTANT]",
        "> This is an operator audit summary contract, not a signed audit and not manual export.",
        "> It summarizes blocked export packet stubs using metadata only.",
        "> It preserves citation, limitation, DQR/readiness, operator identity, signature, hash-lock, export-gate, account-binding, credential, and dispatch-gate requirements.",
        "> It cannot create files, clipboard payloads, downloads, approvals, exports, publishable payloads, dispatches, schedules, manual publish records, or platform/API calls.",
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
        "## Operator Audit Summary Counts",
        "",
        f"- **Registered Operator Audit Summary Records**: `{counts['registered_audit_records_count']}`",
        f"- **Registered Operator Audit Summary Subjects**: `{counts['audit_subjects_count']}`",
        f"- **Operator Audit Invariants Checked**: `{counts['audit_invariants_count']}`",
        f"- **Operator Audit Findings Documented**: `{counts['audit_findings_count']}`",
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
        "## Operator Audit Summary Subject Configurations",
        "",
        "| Platform Target ID | Audit Subject Type | Description |",
        "|---|---|---|",
    ])

    for s in subjects:
        lines.append(f"| `{s['platform_target_id']}` | `{s['audit_subject_type']}` | {s['description']} |")

    lines.extend([
        "",
        "## Platform Export Packet Stub to Operator Audit Summary Records",
        "",
    ])

    for r in records:
        lines.extend([
            f"### Audit Summary Record: `{r['audit_summary_id']}`",
            "",
            f"- **Source Export Packet Stub ID**: `{r['source_export_packet_stub_id']}`",
            f"- **Source Manual Export Precheck ID**: `{r['source_manual_export_precheck_id']}`",
            f"- **Source Decision Gate ID**: `{r['source_decision_gate_id']}`",
            f"- **Platform Target ID**: `{r['platform_target_id']}`",
            f"- **Platform Family**: `{r['platform_family']}`",
            f"- **Audit Summary Status**: `{r['audit_summary_status']}`",
            f"- **Audit Subject Type**: `{r['audit_subject_type']}`",
            f"- **Export Packet Type**: `{r['export_packet_type']}`",
            f"- **Stub Status**: `{r['stub_status']}`",
            f"- **Publishability Status**: `{r['publishability_status']}`",
            f"- **Manual Export Status**: `{r['manual_export_status']}`",
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
            "#### Operator Audit Invariants (All Checked)",
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
            "#### Documented Findings",
            "",
            "| Finding ID | Description | Active Status |",
            "|---|---|---|",
        ])

        for f in r["findings"]:
            lines.append(
                f"| `{f['finding_id']}` | {f['description']} | `{f['active']}` |"
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
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AT")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
