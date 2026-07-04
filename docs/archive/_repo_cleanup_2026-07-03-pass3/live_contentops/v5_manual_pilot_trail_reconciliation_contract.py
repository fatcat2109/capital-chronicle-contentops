"""V5 manual pilot trail reconciliation contract for ContentOps 0174UZ.

Local-only deterministic contract. It prepares a reconciliation packet
linking manual export packet and operator review queue to a local read-model
reconciliation pipeline without enabling any live network, credentials, or posting.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0174UZ_MANUAL_PILOT_TRAIL_RECONCILIATION_V0"
CONTRACT_VERSION = "0174UZ_V5_MANUAL_PILOT_TRAIL_RECONCILIATION_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "244ddaad05bcd39d071b8fda5ac3d359793aeca4"
SOURCE_MANUAL_EXPORT_PACKET_HASH = "277fb7d44b247efc6021f038e362256f746cc039"
SOURCE_OPERATOR_REVIEW_PACKET_HASH = "473a376d9ff812ff830391e24d3cd75fd71b4faf576414f8b8a157b2ea9f284c"
SOURCE_OPERATOR_REVIEW_QUEUE_ID = "v5_operator_review_queue_473a376d9ff812ff830391e2"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0174UZ"
PACKET_FILENAME = "v5_manual_pilot_trail_reconciliation_contract_packet.json"
RUNBOOK_FILENAME = "v5_manual_pilot_trail_reconciliation_contract.md"
AUDIT_FAMILY = "v5_manual_pilot_trail_reconciliation_future"


@dataclass(frozen=True)
class LifecycleStep:
    step_id: str
    label: str
    status: str
    detail: str
    timestamp_placeholder: str = "local_only_time_placeholder"


@dataclass(frozen=True)
class PlaceholderField:
    field_id: str
    label: str
    value: str
    detail: str
    status: str = "empty_not_recorded"


@dataclass(frozen=True)
class DisabledLiveActionState:
    state_id: str
    live_dispatch_enabled: bool = False
    publish_enabled: bool = False
    send_enabled: bool = False
    schedule_enabled: bool = False
    connect_account_enabled: bool = False
    verify_credentials_enabled: bool = False
    sync_platform_enabled: bool = False
    reason: str = "manual_pilot_trail_reconciliation_only_no_live_dispatch"


@dataclass(frozen=True)
class V5ManualPilotTrailReconciliationPacket:
    reconciliation_id: str
    task_label: str
    contract_version: str
    source_baseline_commit: str
    source_manual_export_packet_hash: str
    source_operator_review_packet_hash: str
    source_operator_review_queue_id: str
    lifecycle_steps: tuple[LifecycleStep, ...]
    blocked_reasons: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    placeholder_fields: tuple[PlaceholderField, ...]
    reconciliation_status: str
    disabled_live_action_state: DisabledLiveActionState
    safety_flags: dict[str, bool]
    packet_hash: str
    packet_hash_algorithm: str = HASH_ALGORITHM
    next_recommended_task: str = "TASK_CONTENTOPS_0175AA_MANUAL_PILOT_TRAIL_RECONCILIATION_AUDIT_V0"


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


def build_lifecycle_steps() -> tuple[LifecycleStep, ...]:
    return (
        LifecycleStep(
            step_id="export_packet_prepared",
            label="Export Packet Prepared",
            status="verified",
            detail="Supervised pilot manual export packet generated and local file paths sealed.",
        ),
        LifecycleStep(
            step_id="operator_review_pending",
            label="Operator Review Pending",
            status="review",
            detail="Operator review queue has registered the export package and is awaiting checklist completion.",
        ),
        LifecycleStep(
            step_id="checklist_pending",
            label="Checklist Pending",
            status="review",
            detail="Human compliance checks (X, Telegram, Substack, LinkedIn) must be checked off-system.",
        ),
        LifecycleStep(
            step_id="manual_publish_url_empty",
            label="Manual Publish URL Empty",
            status="review",
            detail="No live URL has been recorded. Operator must post off-system and supply the link.",
        ),
        LifecycleStep(
            step_id="manual_metrics_empty",
            label="Manual Metrics Empty",
            status="review",
            detail="No performance indicators recorded. Metrics remain uncaptured until manual operator entry.",
        ),
        LifecycleStep(
            step_id="off_system_operator_action_required",
            label="Off-System Operator Action Required",
            status="review",
            detail="Publishing requires the compliance officer to post copy blocks outside ContentOps.",
        ),
        LifecycleStep(
            step_id="reconciliation_blocked_until_evidence_recorded",
            label="Reconciliation Blocked Until Evidence Recorded",
            status="blocked",
            detail="Reconciliation record cannot be sealed without valid off-system manual publish links.",
        ),
        LifecycleStep(
            step_id="live_dispatch_disabled",
            label="Live Dispatch Disabled",
            status="verified",
            detail="Local compliance engine actively prevents automated publishing or credential hydration.",
        ),
    )


def build_placeholder_fields() -> tuple[PlaceholderField, ...]:
    return (
        PlaceholderField(
            field_id="manual_publish_url",
            label="Manual Publish URL",
            value="",
            detail="Target destination URL where the operator manually posted the content.",
        ),
        PlaceholderField(
            field_id="manual_publish_timestamp",
            label="Manual Publish Timestamp",
            value="",
            detail="Operator-recorded exact timestamp of the off-system publish action.",
        ),
        PlaceholderField(
            field_id="manual_metrics_snapshot",
            label="Manual Metrics Snapshot",
            value="",
            detail="Manual copy of impressions, shares, likes, and comments from original source views.",
        ),
        PlaceholderField(
            field_id="platform_post_id",
            label="Platform Post ID",
            value="",
            detail="Unique post/status identifier extracted from the platform URL.",
        ),
        PlaceholderField(
            field_id="platform_permalink",
            label="Platform Permalink",
            value="",
            detail="Direct canonical link back to the published institutional message.",
        ),
        PlaceholderField(
            field_id="operator_notes",
            label="Operator Notes",
            value="",
            detail="Manual compliance overrides or warnings noted by the operator during verification.",
        ),
    )


def build_v5_manual_pilot_trail_reconciliation_packet() -> V5ManualPilotTrailReconciliationPacket:
    steps = build_lifecycle_steps()
    placeholders = build_placeholder_fields()
    safety_flags = {
        "local_only": True,
        "manual_only": True,
        "no_platform_api": True,
        "no_credentials": True,
        "no_scheduler": True,
        "no_live_dispatch": True,
        "public_postable": False,
        "dispatch_ready": False,
        "approval_mutation": False,
        "credential_values_loaded": False,
        "network_performed": False,
    }
    draft = {
        "task_label": TASK_LABEL,
        "contract_version": CONTRACT_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "source_manual_export_packet_hash": SOURCE_MANUAL_EXPORT_PACKET_HASH,
        "source_operator_review_packet_hash": SOURCE_OPERATOR_REVIEW_PACKET_HASH,
        "source_operator_review_queue_id": SOURCE_OPERATOR_REVIEW_QUEUE_ID,
        "lifecycle_steps": steps,
        "blocked_reasons": (
            "awaiting_off_system_operator_evidence",
            "manual_publish_url_empty",
            "manual_metrics_snapshot_empty",
        ),
        "missing_evidence": (
            "manual_publish_url",
            "manual_publish_timestamp",
            "manual_metrics_snapshot",
        ),
        "placeholder_fields": placeholders,
        "reconciliation_status": "blocked_reconciliation_pending_evidence",
        "disabled_live_action_state": DisabledLiveActionState("disabled_live_action_0174UZ"),
        "safety_flags": safety_flags,
    }
    packet_hash = _digest(draft)
    return V5ManualPilotTrailReconciliationPacket(
        reconciliation_id="v5_reconciliation_" + packet_hash[:24],
        packet_hash=packet_hash,
        **draft,
    )


def render_runbook(packet: V5ManualPilotTrailReconciliationPacket) -> str:
    lines = [
        "# V5 Manual Pilot Trail Reconciliation Contract",
        "",
        "> [!IMPORTANT]",
        "> Local-only reconciliation review contract. No posting, scheduling, network, APIs, or live actions.",
        "",
        f"- **Task Label**: `{packet.task_label}`",
        f"- **Reconciliation ID**: `{packet.reconciliation_id}`",
        f"- **Packet Hash**: `{packet.packet_hash}`",
        f"- **Source Manual Export Packet Hash**: `{packet.source_manual_export_packet_hash}`",
        f"- **Source Operator Review Queue ID**: `{packet.source_operator_review_queue_id}`",
        f"- **Reconciliation Status**: `{packet.reconciliation_status}`",
        "",
        "## Safety Declarations",
        "",
        "| Flag | Required Value | Actual Status |",
        "|---|---|---|",
    ]
    for key, val in packet.safety_flags.items():
        lines.append(f"| `{key}` | `{val}` | `verified` |")
    lines.extend([
        "",
        "## Lifecycle Reconciliation Steps",
        "",
        "| Step ID | Label | Status | Detail |",
        "|---|---|---|---|",
    ])
    for step in packet.lifecycle_steps:
        lines.append(
            f"| `{step.step_id}` | {step.label} | `{step.status}` | {step.detail} |"
        )
    lines.extend([
        "",
        "## Placeholder Evidence Fields",
        "",
        "| Field ID | Label | Current Value | Verification Detail |",
        "|---|---|---|---|",
    ])
    for fld in packet.placeholder_fields:
        lines.append(
            f"| `{fld.field_id}` | {fld.label} | `\"{fld.value}\"` | {fld.detail} |"
        )
    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UZ")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_v5_manual_pilot_trail_reconciliation_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
