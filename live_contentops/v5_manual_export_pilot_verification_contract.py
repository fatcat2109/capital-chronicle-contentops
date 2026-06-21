"""V5 manual export and pilot verification contract for ContentOps 0174UW.

Local-only deterministic contract. It prepares a reviewable manual export
package and pilot verification packet without posting, scheduling, syncing,
reading credentials, or calling platform/provider APIs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0174UW_V5_MANUAL_EXPORT_AND_PILOT_VERIFICATION_V0"
CONTRACT_VERSION = "0174UW_V5_MANUAL_EXPORT_PILOT_VERIFICATION_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "b043e1be2563945b058648d840da68c46847e1e4"
SOURCE_READ_MODEL_PACKET_HASH = "c853aefbe2574348acd1f708044a893a5372eb89bb28b4cba69ecfe6216ae5fe"
SOURCE_READ_MODEL_PACKET_ID = "local_preflight_bundle_v5_read_model_precheck_packet_d783ae2ac1c153dcb6bf709a"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0174UW"
PACKET_FILENAME = "v5_manual_export_pilot_verification_contract_packet.json"
RUNBOOK_FILENAME = "v5_manual_export_pilot_verification_contract.md"
AUDIT_FAMILY = "v5_manual_export_pilot_verification_future"

REQUIRED_PLATFORM_TARGETS = (
    "x_manual_post_copy",
    "telegram_channel_manual_message_copy",
    "substack_manual_newsletter_export_copy",
    "linkedin_manual_post_copy",
)
FUTURE_EXPANSION_TARGETS = (
    "threads_manual_expansion_copy_future",
    "instagram_manual_expansion_copy_future",
    "facebook_page_manual_expansion_copy_future",
    "tiktok_manual_expansion_copy_future",
    "youtube_manual_expansion_copy_future",
)


@dataclass(frozen=True)
class ManualCopyBlock:
    block_id: str
    platform_target_id: str
    title: str
    copy_text: str
    content_classification: str
    draft_only: bool = True
    manual_export_only: bool = True
    no_fake_live_market_data: bool = True
    no_secrets: bool = True
    no_raw_response_bodies: bool = True


@dataclass(frozen=True)
class PlatformTarget:
    target_id: str
    platform_label: str
    target_class: str
    manual_copy_block_id: str
    status: str
    blocked_reason: str
    manual_only: bool = True
    not_live: bool = True
    not_public_postable_until_operator_action_outside_system: bool = True
    no_api: bool = True
    no_credentials: bool = True
    no_scheduler: bool = True
    public_postable: bool = False
    dispatch_ready: bool = False


@dataclass(frozen=True)
class ChecklistItem:
    item_id: str
    label: str
    status: str
    detail: str


@dataclass(frozen=True)
class ReviewSignaturePlaceholder:
    status: str
    signer_label: str
    signature_value: str
    cryptographic_signature: bool = False
    uses_secret_material: bool = False


@dataclass(frozen=True)
class EmptyPlaceholder:
    status: str
    value: str
    detail: str


@dataclass(frozen=True)
class DisabledLiveDispatchState:
    state_id: str
    live_dispatch_enabled: bool
    publish_enabled: bool
    send_enabled: bool
    schedule_enabled: bool
    connect_account_enabled: bool
    verify_credentials_enabled: bool
    sync_platform_enabled: bool
    reason: str


@dataclass(frozen=True)
class PilotVerificationPacket:
    verification_id: str
    status: str
    checklist_items: tuple[ChecklistItem, ...]
    missing_proofs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    redaction_proof: tuple[str, ...]
    no_live_action_proof: tuple[str, ...]
    u9_audit_references: tuple[str, ...]
    packet_hash: str
    packet_hash_algorithm: str = HASH_ALGORITHM


@dataclass(frozen=True)
class V5ManualExportPilotVerificationPacket:
    export_package_id: str
    task_label: str
    contract_version: str
    source_baseline_commit: str
    source_read_model_packet_id: str
    source_read_model_packet_hash: str
    generated_at_epoch: int
    platform_targets: tuple[PlatformTarget, ...]
    manual_copy_blocks: tuple[ManualCopyBlock, ...]
    evidence_refs: tuple[str, ...]
    operator_review_checklist: tuple[ChecklistItem, ...]
    review_signature_placeholder: ReviewSignaturePlaceholder
    disabled_live_dispatch_state: DisabledLiveDispatchState
    manual_publish_url_placeholder: EmptyPlaceholder
    manual_metrics_placeholder: EmptyPlaceholder
    pilot_verification_status: str
    pilot_verification_packet: PilotVerificationPacket
    safety_flags: dict[str, bool]
    packet_hash: str
    packet_hash_algorithm: str
    next_recommended_task: str


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


def build_manual_copy_blocks() -> tuple[ManualCopyBlock, ...]:
    return (
        ManualCopyBlock(
            block_id="copy_x_manual_post_draft",
            platform_target_id="x_manual_post_copy",
            title="X manual post draft",
            copy_text=(
                "Draft/manual export only: Capital Chronicle pilot note for human review. "
                "Use this block only as a local editorial candidate; verify citations, "
                "limits, timing, and policy outside ContentOps before any manual action."
            ),
            content_classification="draft_manual_copy_no_live_market_data",
        ),
        ManualCopyBlock(
            block_id="copy_telegram_channel_manual_message_draft",
            platform_target_id="telegram_channel_manual_message_copy",
            title="Telegram Channel manual message draft",
            copy_text=(
                "Draft/manual export only: Editorial pilot summary for a controlled channel. "
                "Operator must copy by hand outside ContentOps after human approval. "
                "No bot send, no channel API, no credential use."
            ),
            content_classification="draft_manual_copy_no_channel_send",
        ),
        ManualCopyBlock(
            block_id="copy_substack_manual_newsletter_export_draft",
            platform_target_id="substack_manual_newsletter_export_copy",
            title="Substack manual newsletter/export draft",
            copy_text=(
                "Draft/manual export only: Newsletter body candidate for supervised pilot review. "
                "Operator must paste into Substack manually outside ContentOps. "
                "No Substack API, no subscriber sync, no credential use."
            ),
            content_classification="draft_manual_export_copy_no_substack_api",
        ),
        ManualCopyBlock(
            block_id="copy_linkedin_manual_post_draft",
            platform_target_id="linkedin_manual_post_copy",
            title="LinkedIn manual post draft",
            copy_text=(
                "Draft/manual export only: Professional credibility summary for human review. "
                "Operator must copy/publish manually outside ContentOps after page proof. "
                "No LinkedIn API, no organization-page sync, no credential use."
            ),
            content_classification="draft_manual_copy_no_linkedin_api",
        ),
    )


def build_platform_targets() -> tuple[PlatformTarget, ...]:
    active = (
        ("x_manual_post_copy", "X manual post copy", "active_manual_export_preview", "copy_x_manual_post_draft", "manual_review_required", "x_app_access_gap_and_manual_operator_review_required"),
        ("telegram_channel_manual_message_copy", "Telegram Channel manual message copy", "active_manual_export_preview", "copy_telegram_channel_manual_message_draft", "manual_review_required", "channel_admin_proof_required_and_manual_operator_review_required"),
        ("substack_manual_newsletter_export_copy", "Substack manual newsletter/export copy", "active_manual_export_preview", "copy_substack_manual_newsletter_export_draft", "manual_review_required", "manual_export_only_operator_action_outside_system_required"),
        ("linkedin_manual_post_copy", "LinkedIn manual post copy", "active_manual_export_preview", "copy_linkedin_manual_post_draft", "manual_review_required", "linkedin_organization_page_proof_missing"),
    )
    future = (
        ("threads_manual_expansion_copy_future", "Threads manual expansion copy", "future_manual_expansion", "", "future_gate_blocked", "meta_app_review_closed"),
        ("instagram_manual_expansion_copy_future", "Instagram manual expansion copy", "future_manual_expansion", "", "future_gate_blocked", "meta_app_review_closed"),
        ("facebook_page_manual_expansion_copy_future", "Facebook Page manual expansion copy", "future_manual_expansion", "", "future_gate_blocked", "meta_app_review_closed"),
        ("tiktok_manual_expansion_copy_future", "TikTok manual expansion copy", "future_manual_expansion", "", "future_gate_blocked", "tiktok_app_audit_closed"),
        ("youtube_manual_expansion_copy_future", "YouTube manual expansion copy", "future_manual_expansion", "", "future_gate_blocked", "youtube_oauth_flow_closed"),
    )
    return tuple(
        PlatformTarget(
            target_id=target_id,
            platform_label=label,
            target_class=target_class,
            manual_copy_block_id=copy_id,
            status=status,
            blocked_reason=reason,
        )
        for target_id, label, target_class, copy_id, status, reason in (*active, *future)
    )


def build_operator_review_checklist() -> tuple[ChecklistItem, ...]:
    return (
        ChecklistItem("check_source_packet_hash", "Source 0174UU packet hash referenced", "verified", SOURCE_READ_MODEL_PACKET_HASH),
        ChecklistItem("check_manual_copy_review", "Operator reviews every copy block", "review", "Human review required before off-system copy/publish."),
        ChecklistItem("check_no_credentials", "No credentials loaded", "verified", "No env, dotenv, credential, secret, token, or key material exists in packet."),
        ChecklistItem("check_no_live_dispatch", "No live dispatch path", "verified", "All publish/send/schedule/connect/verify/sync states are disabled."),
        ChecklistItem("check_url_metrics_empty", "URL and metrics placeholders empty", "review", "Manual publish URL and metrics are not recorded yet."),
        ChecklistItem("check_signature_placeholder", "Review signature placeholder only", "review", "Local status placeholder; no cryptographic signing."),
    )


def build_disabled_live_dispatch_state() -> DisabledLiveDispatchState:
    return DisabledLiveDispatchState(
        state_id="disabled_live_dispatch_0174UW",
        live_dispatch_enabled=False,
        publish_enabled=False,
        send_enabled=False,
        schedule_enabled=False,
        connect_account_enabled=False,
        verify_credentials_enabled=False,
        sync_platform_enabled=False,
        reason="manual_export_pilot_verification_only_no_live_affordance",
    )


def build_pilot_verification_packet(checklist: tuple[ChecklistItem, ...]) -> PilotVerificationPacket:
    draft = {
        "verification_id": "pilot_verification_packet_0174UW",
        "status": "blocked_pending_operator_manual_review",
        "checklist_items": checklist,
        "missing_proofs": (
            "operator_manual_review_signature_not_recorded",
            "manual_publish_url_not_recorded",
            "manual_metrics_not_recorded",
            "future_live_dispatch_authorization_not_present",
        ),
        "blocked_reasons": (
            "manual_export_only",
            "no_platform_api",
            "no_credentials_loaded",
            "no_live_dispatch",
            "operator_must_publish_outside_contentops",
        ),
        "redaction_proof": (
            "credential_values_absent",
            "token_slices_absent",
            "secret_hashes_absent",
            "raw_response_bodies_absent",
        ),
        "no_live_action_proof": (
            "publish_enabled_false",
            "send_enabled_false",
            "schedule_enabled_false",
            "connect_account_enabled_false",
            "verify_credentials_enabled_false",
            "sync_platform_enabled_false",
        ),
        "u9_audit_references": (AUDIT_FAMILY, "u9:0174UW:manual_export_pilot_verification:future"),
    }
    return PilotVerificationPacket(
        packet_hash=_digest(draft),
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft,
    )


def build_v5_manual_export_pilot_verification_packet() -> V5ManualExportPilotVerificationPacket:
    targets = build_platform_targets()
    copy_blocks = build_manual_copy_blocks()
    checklist = build_operator_review_checklist()
    verification = build_pilot_verification_packet(checklist)
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
        "source_read_model_packet_id": SOURCE_READ_MODEL_PACKET_ID,
        "source_read_model_packet_hash": SOURCE_READ_MODEL_PACKET_HASH,
        "generated_at_epoch": 0,
        "platform_targets": targets,
        "manual_copy_blocks": copy_blocks,
        "evidence_refs": (
            "docs/automation/0174UU/local_preflight_bundle_v5_read_model_precheck_contract_packet.json",
            "ui/contentops_v5/src/data/preflightBundlePacket.ts",
            "live_contentops/v5_manual_export_pilot_verification_contract.py",
        ),
        "operator_review_checklist": checklist,
        "review_signature_placeholder": ReviewSignaturePlaceholder(
            status="placeholder_not_signed",
            signer_label="operator_review_signature_pending_local_placeholder",
            signature_value="",
        ),
        "disabled_live_dispatch_state": build_disabled_live_dispatch_state(),
        "manual_publish_url_placeholder": EmptyPlaceholder(
            status="empty_not_recorded",
            value="",
            detail="Manual publish URL must be recorded after operator action outside ContentOps.",
        ),
        "manual_metrics_placeholder": EmptyPlaceholder(
            status="empty_not_recorded",
            value="",
            detail="Manual metrics must be recorded after operator observation outside ContentOps.",
        ),
        "pilot_verification_status": "blocked_pending_operator_manual_review",
        "pilot_verification_packet": verification,
        "safety_flags": safety_flags,
        "next_recommended_task": "TASK_CONTENTOPS_0174UX_MANUAL_PILOT_PACKET_BROWSER_QA_AND_OPERATOR_REVIEW_V0",
    }
    packet_hash = _digest(draft)
    return V5ManualExportPilotVerificationPacket(
        export_package_id="v5_manual_export_pilot_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft,
    )


def render_runbook(packet: V5ManualExportPilotVerificationPacket) -> str:
    lines = [
        "# V5 Manual Export and Pilot Verification Contract",
        "",
        "> [!CAUTION]",
        "> Local-only manual export and pilot verification packet. No posting, scheduling, syncing, credentials, platform APIs, or live dispatch.",
        "",
        f"- **Task Label**: `{packet.task_label}`",
        f"- **Export Package ID**: `{packet.export_package_id}`",
        f"- **Packet Hash**: `{packet.packet_hash}`",
        f"- **Source 0174UU Packet Hash**: `{packet.source_read_model_packet_hash}`",
        f"- **Pilot Status**: `{packet.pilot_verification_status}`",
        "",
        "## Safety Strip",
        "",
        "- Manual Export Only",
        "- No platform API",
        "- No credentials loaded",
        "- No live dispatch",
        "- Operator must manually copy/publish outside ContentOps",
        "",
        "## Platform Targets",
        "",
        "| Target | Status | No API | No Credentials | Dispatch Ready | Public Postable |",
        "|---|---|---|---|---|---|",
    ]
    for target in packet.platform_targets:
        lines.append(
            f"| `{target.target_id}` | `{target.status}` | `{target.no_api}` | `{target.no_credentials}` | `{target.dispatch_ready}` | `{target.public_postable}` |"
        )
    lines.extend([
        "",
        "## Manual Copy Blocks",
        "",
    ])
    for block in packet.manual_copy_blocks:
        lines.extend([
            f"### `{block.block_id}`",
            "",
            block.copy_text,
            "",
        ])
    lines.extend([
        "## Pilot Verification Packet",
        "",
        f"- **Verification ID**: `{packet.pilot_verification_packet.verification_id}`",
        f"- **Verification Hash**: `{packet.pilot_verification_packet.packet_hash}`",
        "",
        "### Missing Proofs",
    ])
    for proof in packet.pilot_verification_packet.missing_proofs:
        lines.append(f"- `{proof}`")
    lines.extend(["", "### No-Live Proof"])
    for proof in packet.pilot_verification_packet.no_live_action_proof:
        lines.append(f"- `{proof}`")
    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UW")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_v5_manual_export_pilot_verification_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "ManualCopyBlock",
    "PlatformTarget",
    "ChecklistItem",
    "ReviewSignaturePlaceholder",
    "EmptyPlaceholder",
    "DisabledLiveDispatchState",
    "PilotVerificationPacket",
    "V5ManualExportPilotVerificationPacket",
    "build_v5_manual_export_pilot_verification_packet",
    "write_artifacts",
]
