"""Manual Export Precheck to Export Packet Stub contract, 0175AS.

Deterministic local-only contract defining export packet stubs for platform manual copy workflows.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.operator_decision_gate_to_manual_export_precheck_contract import (
    build_contract_packet as build_precheck_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AS_MANUAL_EXPORT_PRECHECK_TO_EXPORT_PACKET_STUB_V0"
MATRIX_VERSION = "0175AS_MANUAL_EXPORT_PRECHECK_TO_EXPORT_PACKET_STUB_V1"
SOURCE_BASELINE_COMMIT = "c6ad0bcf016e1a5396aaab52f334b176e26f5c58"
LEDGER_FAMILY = "manual_export_precheck_to_export_packet_stub_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AS"
PACKET_FILENAME = "manual_export_precheck_to_export_packet_stub_contract_packet.json"
RUNBOOK_FILENAME = "manual_export_precheck_to_export_packet_stub_contract.md"


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
class ManualExportPacketStubTarget:
    platform_target_id: str
    export_packet_type: str
    description: str


@dataclass(frozen=True)
class ManualExportPacketStubField:
    field_name: str
    placeholder_value: str
    placeholder_only: bool = True
    export_file_ready: bool = False
    clipboard_ready: bool = False
    download_ready: bool = False
    publishable_text: bool = False
    platform_ready: bool = False
    dispatch_ready: bool = False
    contains_market_number: bool = False
    contains_financial_advice: bool = False
    contains_signal_language: bool = False
    requires_human_rewrite: bool = True


@dataclass(frozen=True)
class ManualExportPacketStubLock:
    lock_id: str
    description: str
    active: bool = True


@dataclass(frozen=True)
class ManualExportPacketStubRecord:
    export_packet_stub_id: str
    source_manual_export_precheck_id: str
    source_decision_gate_id: str
    platform_target_id: str
    platform_family: str
    stub_status: str
    export_target_type: str
    export_packet_type: str
    fields: list[ManualExportPacketStubField]
    locks: list[ManualExportPacketStubLock]
    blocked_reasons: list[str]
    missing_future_gates: list[str]
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
class ManualExportPacketStubContractPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    stub_records: list[ManualExportPacketStubRecord]
    stub_targets: list[ManualExportPacketStubTarget]
    summary_counts: dict[str, int]
    safety_flags: dict[str, bool]
    blocked_capabilities: list[str]
    missing_future_gates: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_stub_targets() -> list[ManualExportPacketStubTarget]:
    targets = {
        "x": ("x_manual_copy_packet_stub", "Manual copy packet stub for X platform"),
        "telegram_channel_destination": ("telegram_channel_manual_copy_packet_stub", "Manual copy packet stub for Telegram channel"),
        "telegram_remote_operator": ("telegram_remote_operator_review_log_packet_stub", "Telegram remote operator review log packet stub"),
        "substack": ("substack_manual_markdown_packet_stub", "Manual markdown newsletter packet stub for Substack"),
        "linkedin": ("linkedin_manual_copy_packet_stub", "Manual copy packet stub for LinkedIn professional update"),
        "threads": ("threads_manual_copy_packet_stub", "Manual copy packet stub for Meta Threads"),
        "instagram": ("instagram_caption_media_manual_packet_stub", "Instagram caption and media manual copy packet stub"),
        "facebook_page": ("facebook_page_manual_copy_packet_stub", "Manual copy packet stub for Facebook Page"),
        "tiktok": ("tiktok_caption_video_manual_packet_stub", "TikTok caption and video manual copy packet stub"),
        "youtube": ("youtube_metadata_manual_packet_stub", "YouTube metadata and description outline manual copy packet stub")
    }
    return [
        ManualExportPacketStubTarget(platform_target_id=tid, export_packet_type=val[0], description=val[1])
        for tid, val in targets.items()
    ]


def build_fields_for_target(platform_target_id: str) -> list[ManualExportPacketStubField]:
    field_mappings = {
        "x": ["body_stub", "citation_stub", "limitation_stub", "manual_copy_instruction_stub"],
        "telegram_channel_destination": ["message_stub", "citation_stub", "limitation_stub", "manual_copy_instruction_stub"],
        "telegram_remote_operator": ["operator_log_stub", "audit_ref_stub", "decision_summary_stub"],
        "substack": ["title_stub", "subtitle_stub", "body_markdown_stub", "citation_section_stub", "limitation_section_stub"],
        "linkedin": ["professional_intro_stub", "body_stub", "citation_stub", "limitation_stub"],
        "threads": ["short_text_stub", "citation_stub", "limitation_stub"],
        "instagram": ["caption_stub", "media_requirement_stub", "alt_text_stub", "citation_stub", "limitation_stub"],
        "facebook_page": ["post_text_stub", "attachment_stub", "citation_stub", "limitation_stub"],
        "tiktok": ["caption_stub", "video_requirement_stub", "disclosure_stub", "citation_stub"],
        "youtube": ["title_stub", "description_outline_stub", "video_requirement_stub", "citation_stub", "limitation_stub"]
    }
    
    names = field_mappings.get(platform_target_id, [])
    return [
        ManualExportPacketStubField(
            field_name=name,
            placeholder_value=f"[EXPORT_PACKET_STUB_ONLY: {platform_target_id}.{name}]"
        )
        for name in names
    ]


def build_stub_locks() -> list[ManualExportPacketStubLock]:
    lock_ids = [
        "lock_no_operator_signature",
        "lock_no_payload_hash_lock",
        "lock_unresolved_citations",
        "lock_unresolved_limitations",
        "lock_dqr_readiness_unresolved",
        "lock_no_manual_export_gate",
        "lock_no_export_file_writer",
        "lock_no_clipboard_writer",
        "lock_no_download_artifact_writer",
        "lock_no_dispatch_gate"
    ]
    descriptions = {
        "lock_no_operator_signature": "Cryptographic operator signature required but missing.",
        "lock_no_payload_hash_lock": "Payload hash lock is not secured.",
        "lock_unresolved_citations": "Citation clearance check unresolved.",
        "lock_unresolved_limitations": "Limitation acknowledgement gate unresolved.",
        "lock_dqr_readiness_unresolved": "DQR publishing readiness gate unresolved.",
        "lock_no_manual_export_gate": "Manual export gate required but locked.",
        "lock_no_export_file_writer": "Direct export file writer disabled.",
        "lock_no_clipboard_writer": "Direct clipboard payload writer disabled.",
        "lock_no_download_artifact_writer": "Direct download artifact writer disabled.",
        "lock_no_dispatch_gate": "Platform publishing dispatch gate required but locked."
    }
    return [
        ManualExportPacketStubLock(lock_id=lid, description=descriptions[lid], active=True)
        for lid in lock_ids
    ]


def build_safety_flags() -> dict[str, bool]:
    return {
        "local_only": True,
        "fixture_only": True,
        "schema_only": True,
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
    precheck_data = build_precheck_packet()
    precheck_records = precheck_data.get("precheck_records", [])

    stub_targets = build_stub_targets()
    packet_type_map = {t.platform_target_id: t.export_packet_type for t in stub_targets}

    locks = build_stub_locks()
    lock_ids = [l.lock_id for l in locks]

    stub_records: list[ManualExportPacketStubRecord] = []

    for rec in precheck_records:
        tid = rec["platform_target_id"]
        family = rec["platform_family"]
        packet_type = packet_type_map.get(tid, "generic_manual_copy_packet_stub")
        fields = build_fields_for_target(tid)

        raw_record = {
            "export_packet_stub_id": f"export_packet_stub_{tid}",
            "source_manual_export_precheck_id": rec["manual_export_precheck_id"],
            "source_decision_gate_id": rec["source_decision_gate_id"],
            "platform_target_id": tid,
            "platform_family": family,
            "stub_status": "export_packet_stub_blocked",
            "export_target_type": rec["export_target_type"],
            "export_packet_type": packet_type,
            "fields": [_asdict(f) for f in fields],
            "locks": [_asdict(l) for l in locks],
            "blocked_reasons": lock_ids,
            "missing_future_gates": ["lane_c_platform_export_packet_stub_to_operator_audit_summary", "production_key_vault_decrypter", "live_operator_signature_vault"],
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
            # Safety & Status Flags
            "manual_export_allowed": False,
            "export_ready": False,
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
        stub_records.append(
            ManualExportPacketStubRecord(
                packet_hash=rec_hash,
                **raw_record
            )
        )

    safety = build_safety_flags()

    summary_counts = {
        "registered_stub_records_count": len(stub_records),
        "stub_targets_count": len(stub_targets),
        "stub_locks_count": len(locks),
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
        "lane_c_platform_export_packet_stub_to_operator_audit_summary",
        "production_key_vault_decrypter",
        "live_operator_signature_vault"
    ]

    packet = ManualExportPacketStubContractPacket(
        task_label=TASK_LABEL,
        matrix_version=MATRIX_VERSION,
        source_baseline_commit=SOURCE_BASELINE_COMMIT,
        generated_at_epoch=0,
        stub_records=stub_records,
        stub_targets=stub_targets,
        summary_counts=summary_counts,
        safety_flags=safety,
        blocked_capabilities=blocked_caps,
        missing_future_gates=missing_gates,
        ledger_family=LEDGER_FAMILY,
        packet_hash="",
        hash_algorithm=HASH_ALGORITHM,
        next_required_gate="lane_c_platform_export_packet_stub_to_operator_audit_summary"
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
    records = packet["stub_records"]
    targets = packet["stub_targets"]
    counts = packet["summary_counts"]
    safety = packet["safety_flags"]
    blocked_caps = packet["blocked_capabilities"]
    missing_gates = packet["missing_future_gates"]

    lines = [
        "# Manual Export Precheck to Export Packet Stub Contract",
        "",
        "> [!IMPORTANT]",
        "> This is an export packet stub contract, not manual export.",
        "> It creates blocked stub metadata and non-public placeholders only.",
        "> It preserves citation, limitation, DQR/readiness, operator identity, signature, hash-lock, export-gate, account-binding, credential, and dispatch-gate requirements.",
        "> It cannot create files, clipboard payloads, downloads, approvals, exports, publishable payloads, dispatches, schedules, or platform/API calls.",
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
        "## Export Packet Stub Summary Counts",
        "",
        f"- **Registered Export Packet Stub Records**: `{counts['registered_stub_records_count']}`",
        f"- **Registered Export Packet Stub Targets**: `{counts['stub_targets_count']}`",
        f"- **Export Packet Stub Locks Configured**: `{counts['stub_locks_count']}`",
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
        "## Export Packet Stub Target Configurations",
        "",
        "| Platform Target ID | Export Packet Type | Description |",
        "|---|---|---|",
    ])

    for t in targets:
        lines.append(f"| `{t['platform_target_id']}` | `{t['export_packet_type']}` | {t['description']} |")

    lines.extend([
        "",
        "## Platform Manual Export Precheck to Export Packet Stub Records",
        "",
    ])

    for r in records:
        lines.extend([
            f"### Export Packet Stub Record: `{r['export_packet_stub_id']}`",
            "",
            f"- **Source Manual Export Precheck ID**: `{r['source_manual_export_precheck_id']}`",
            f"- **Source Decision Gate ID**: `{r['source_decision_gate_id']}`",
            f"- **Platform Target ID**: `{r['platform_target_id']}`",
            f"- **Platform Family**: `{r['platform_family']}`",
            f"- **Stub Status**: `{r['stub_status']}`",
            f"- **Export Target Type**: `{r['export_target_type']}`",
            f"- **Export Packet Type**: `{r['export_packet_type']}`",
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
            "#### Export Packet Fields (Placeholder Only)",
            "",
            "| Field Name | Placeholder Value | Placeholder Only | Export File Ready | Clipboard Ready | Requires Rewrite |",
            "|---|---|---|---|---|---|",
        ])

        for f in r["fields"]:
            lines.append(
                f"| `{f['field_name']}` | `{f['placeholder_value']}` | `{f['placeholder_only']}` | `{f['export_file_ready']}` | `{f['clipboard_ready']}` | `{f['requires_human_rewrite']}` |"
            )

        lines.extend([
            "",
            "#### Export Packet Locks (All Active)",
            "",
            "| Lock ID | Description | Active Status |",
            "|---|---|---|",
        ])

        for lk in r["locks"]:
            lines.append(
                f"| `{lk['lock_id']}` | {lk['description']} | `{lk['active']}` |"
            )

        lines.extend([
            "",
            "#### Export Packet Locks (Active)",
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
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AS")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
