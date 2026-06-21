"""V5 operator review queue and manual pilot trail contract for ContentOps 0174UY.

Local-only deterministic contract. It prepares a reviewable operator review queue
and manual pilot trail packet referencing the 0174UW manual export packet hash
without posting, scheduling, syncing, reading credentials, or calling platform/provider APIs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0174UY_V5_OPERATOR_REVIEW_QUEUE_AND_MANUAL_PILOT_TRAIL_V0"
CONTRACT_VERSION = "0174UY_V5_OPERATOR_REVIEW_QUEUE_MANUAL_PILOT_TRAIL_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "c6ab726a5762bad55179c77bbafbe379bc38f136"
SOURCE_MANUAL_EXPORT_PACKET_HASH = "277fb7d44b247efc6021f038e362256f746cc039"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0174UY"
PACKET_FILENAME = "v5_operator_review_queue_manual_pilot_trail_contract_packet.json"
RUNBOOK_FILENAME = "v5_operator_review_queue_manual_pilot_trail_contract.md"
AUDIT_FAMILY = "v5_operator_review_queue_manual_pilot_trail_future"


@dataclass(frozen=True)
class ReviewItem:
    item_id: str
    label: str
    status: str
    detail: str
    local_only: bool = True
    manual_review_required: bool = True
    not_public_postable: bool = True
    not_dispatch_ready: bool = True
    no_api: bool = True
    no_credentials: bool = True
    no_scheduler: bool = True
    operator_action_outside_contentops_required: bool = True


@dataclass(frozen=True)
class TrailEntry:
    entry_id: str
    entry_type: str
    label: str
    timestamp_placeholder: str = "local_only_time_placeholder"
    status: str = "verified"


@dataclass(frozen=True)
class EmptyPlaceholder:
    status: str
    value: str
    detail: str


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
    reason: str = "manual_export_pilot_verification_only_no_live_affordance"


@dataclass(frozen=True)
class V5OperatorReviewQueueManualPilotTrailPacket:
    queue_id: str
    task_label: str
    contract_version: str
    source_baseline_commit: str
    source_manual_export_packet_hash: str
    review_items: tuple[ReviewItem, ...]
    item_status_summary: str
    blocked_reasons: tuple[str, ...]
    missing_proofs: tuple[str, ...]
    manual_publish_placeholders: tuple[EmptyPlaceholder, ...]
    local_review_trail_entries: tuple[TrailEntry, ...]
    disabled_live_action_state: DisabledLiveActionState
    safety_flags: dict[str, bool]
    packet_hash: str
    packet_hash_algorithm: str = HASH_ALGORITHM
    next_recommended_task: str = "TASK_CONTENTOPS_0174UZ_MANUAL_PILOT_TRAIL_RECONCILIATION_V0"


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


def build_review_items() -> tuple[ReviewItem, ...]:
    return (
        ReviewItem(
            item_id="item_x_manual_post_draft_review",
            label="X manual post draft review",
            status="manual_review_required",
            detail="Verify X draft copy matches 0174UW local prechecks. Operator must publish manually.",
        ),
        ReviewItem(
            item_id="item_telegram_channel_manual_message_review",
            label="Telegram Channel manual message review",
            status="manual_review_required",
            detail="Verify Telegram message copy matches 0174UW local prechecks. Operator must copy manually.",
        ),
        ReviewItem(
            item_id="item_substack_manual_newsletter_export_review",
            label="Substack manual newsletter/export review",
            status="manual_review_required",
            detail="Verify Substack newsletter draft matches 0174UW local prechecks. Operator must paste manually.",
        ),
        ReviewItem(
            item_id="item_linkedin_manual_post_review",
            label="LinkedIn manual post review",
            status="manual_review_required",
            detail="Verify LinkedIn draft copy matches 0174UW local prechecks. Operator must publish manually.",
        ),
    )


def build_local_review_trail_entries() -> tuple[TrailEntry, ...]:
    return (
        TrailEntry(
            entry_id="trail_created_local_review_item",
            entry_type="created_local_review_item",
            label="Created local review items for X, Telegram, Substack, LinkedIn.",
        ),
        TrailEntry(
            entry_id="trail_checklist_pending",
            entry_type="checklist_pending",
            label="Operator checklist is pending manual verification.",
            status="review",
        ),
        TrailEntry(
            entry_id="trail_manual_publish_url_empty",
            entry_type="manual_publish_url_empty",
            label="Manual publish URL empty — waiting for off-system operator publish.",
            status="review",
        ),
        TrailEntry(
            entry_id="trail_metrics_empty",
            entry_type="metrics_empty",
            label="Manual publish metrics empty — waiting for off-system operator recording.",
            status="review",
        ),
        TrailEntry(
            entry_id="trail_live_dispatch_disabled",
            entry_type="live_dispatch_disabled",
            label="Live dispatch disabled — proof of local-only safety bounds verified.",
        ),
    )


def build_v5_operator_review_queue_manual_pilot_trail_packet() -> V5OperatorReviewQueueManualPilotTrailPacket:
    items = build_review_items()
    trail = build_local_review_trail_entries()
    placeholders = (
        EmptyPlaceholder(
            status="empty_not_recorded",
            value="",
            detail="Manual publish URL must be recorded after operator acts outside ContentOps.",
        ),
        EmptyPlaceholder(
            status="empty_not_recorded",
            value="",
            detail="Manual metrics must be recorded after operator observation outside ContentOps.",
        ),
    )
    safety_flags = {
        "local_only": True,
        "manual_export_only": True,
        "pilot_verification_only": True,
        "env_read": False,
        "dotenv_loaded": False,
        "credential_values_accessed": False,
        "credential_hydrated": False,
        "secret_output_allowed": False,
        "token_hash_or_prefix_suffix_output": False,
        "network_performed": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "scheduler_enabled": False,
        "scraping_performed": False,
        "posting_performed": False,
        "dm_or_reply_automation_allowed": False,
        "ingestion_repo_mutated": False,
        "readiness_cleared": False,
        "public_postable": False,
        "dispatch_ready": False,
    }
    draft = {
        "task_label": TASK_LABEL,
        "contract_version": CONTRACT_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "source_manual_export_packet_hash": SOURCE_MANUAL_EXPORT_PACKET_HASH,
        "review_items": items,
        "item_status_summary": "review_pending_operator_actions",
        "blocked_reasons": (
            "manual_review_required",
            "no_platform_credentials",
            "no_live_dispatch_allowed",
        ),
        "missing_proofs": (
            "operator_checklist_uncompleted",
            "manual_publish_url_unrecorded",
            "manual_metrics_unrecorded",
        ),
        "manual_publish_placeholders": placeholders,
        "local_review_trail_entries": trail,
        "disabled_live_action_state": DisabledLiveActionState("disabled_live_action_0174UY"),
        "safety_flags": safety_flags,
    }
    packet_hash = _digest(draft)
    return V5OperatorReviewQueueManualPilotTrailPacket(
        queue_id="v5_operator_review_queue_" + packet_hash[:24],
        packet_hash=packet_hash,
        **draft,
    )


def render_runbook(packet: V5OperatorReviewQueueManualPilotTrailPacket) -> str:
    lines = [
        "# V5 Operator Review Queue and Manual Pilot Trail Contract",
        "",
        "> [!IMPORTANT]",
        "> Local-only operator review queue and manual pilot trail evidence packet. No posting, scheduling, credentials, APIs, or live dispatch.",
        "",
        f"- **Task Label**: `{packet.task_label}`",
        f"- **Queue ID**: `{packet.queue_id}`",
        f"- **Packet Hash**: `{packet.packet_hash}`",
        f"- **Source 0174UW Manual Export Hash**: `{packet.source_manual_export_packet_hash}`",
        f"- **Item Status Summary**: `{packet.item_status_summary}`",
        "",
        "## Safety Strip",
        "",
        "- Manual Export Only",
        "- No platform API",
        "- No credentials loaded",
        "- No live dispatch",
        "- Operator publishes outside ContentOps",
        "",
        "## Review Items",
        "",
        "| Item ID | Label | Status | Local Only | No API | No Creds |",
        "|---|---|---|---|---|---|",
    ]
    for item in packet.review_items:
        lines.append(
            f"| `{item.item_id}` | {item.label} | `{item.status}` | `{item.local_only}` | `{item.no_api}` | `{item.no_credentials}` |"
        )
    lines.extend([
        "",
        "## Local Review Trail Entries",
        "",
        "| Entry ID | Type | Label | Status |",
        "|---|---|---|---|",
    ])
    for entry in packet.local_review_trail_entries:
        lines.append(
            f"| `{entry.entry_id}` | `{entry.entry_type}` | {entry.label} | `{entry.status}` |"
        )
    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UY")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_v5_operator_review_queue_manual_pilot_trail_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
