"""Platform Preview Dry Render Packet contract, 0175AO.

Deterministic local-only contract defining dry preview render packets.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.platform_preview_dry_payload_shape_registry_contract import (
    build_contract_packet as build_shape_registry_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AO_PLATFORM_PREVIEW_DRY_RENDER_PACKET_V0"
MATRIX_VERSION = "0175AO_PLATFORM_PREVIEW_DRY_RENDER_PACKET_V1"
SOURCE_BASELINE_COMMIT = "f57a23fb61a550d9528c1984d8e758e7f00ab265"
LEDGER_FAMILY = "platform_preview_dry_render_packet_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AO"
PACKET_FILENAME = "platform_preview_dry_render_packet_contract_packet.json"
RUNBOOK_FILENAME = "platform_preview_dry_render_packet_contract.md"


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
class PlatformPreviewDryRenderField:
    field_name: str
    placeholder_value: str
    placeholder_only: bool
    publishable_text: bool
    platform_ready: bool
    dispatch_ready: bool
    generated_by_provider: bool
    requires_human_rewrite: bool
    contains_market_number: bool
    contains_financial_advice: bool
    contains_signal_language: bool


@dataclass(frozen=True)
class PlatformPreviewDryRenderSurface:
    surface_type: str
    rendering_notes: str


@dataclass(frozen=True)
class PlatformPreviewDryRenderBlocker:
    blocker_id: str
    description: str
    active: bool


@dataclass(frozen=True)
class PlatformPreviewDryRenderRecord:
    render_id: str
    platform_target_id: str
    platform_family: str
    source_shape_id: str
    render_status: str
    preview_surface_type: str
    field_renders: list[PlatformPreviewDryRenderField]
    watermark: str
    blocker_banner: str
    citation_slot_status: str
    limitation_slot_status: str
    operator_review_status: str
    account_binding_status: str
    credential_gate_status: str
    payload_hash_lock_status: str
    dispatch_gate_status: str
    publishability_status: str
    blocked_reasons: list[str]
    missing_future_gates: list[str]
    packet_hash: str
    # Safety & Status Flags
    placeholder_only: bool = True
    publishable_text: bool = False
    platform_ready: bool = False
    dispatch_ready: bool = False
    platform_payload_created: bool = False
    publishable_payload_created: bool = False
    export_ready: bool = False
    operator_review_required: bool = True
    account_binding_active: bool = False
    credential_values_loaded: bool = False
    platform_api_called: bool = False
    scheduler_enabled: bool = False
    approved_for_publication: bool = False


@dataclass(frozen=True)
class PlatformPreviewDryRenderPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    platform_shapes: list[dict[str, Any]]
    render_records: list[PlatformPreviewDryRenderRecord]
    global_blockers: list[PlatformPreviewDryRenderBlocker]
    summary_counts: dict[str, int]
    safety_flags: dict[str, bool]
    blocked_capabilities: list[str]
    missing_future_gates: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_dry_render_blockers() -> list[PlatformPreviewDryRenderBlocker]:
    blockers = {
        "blocked_no_operator_review": "Operator review gate is required but pending.",
        "blocked_no_account_binding": "Account binding is required but inactive.",
        "blocked_no_credential_gate": "Credential gate authentication is required but pending.",
        "blocked_no_payload_hash_lock": "Payload hash lock verification is required but pending.",
        "blocked_dqr_readiness_unresolved": "DQR and publish readiness checks are unresolved.",
        "blocked_not_public_postable": "Candidate is not marked public postable.",
        "blocked_no_dispatch_gate": "Dispatch gate has not cleared the post.",
        "blocked_no_platform_api_authorization": "Platform API is not authorized (local contract dry run)."
    }
    return [
        PlatformPreviewDryRenderBlocker(blocker_id=bid, description=desc, active=True)
        for bid, desc in blockers.items()
    ]


def build_safety_flags() -> dict[str, bool]:
    return {
        "local_only": True,
        "fixture_only": True,
        "schema_only": True,
        "dry_render_only": True,
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
        "approved_for_publication": False,
        "financial_advice": False,
        "signal_language": False,
        "broker_order_execution": False,
        "raw_vendor_redistribution": False,
        "approved_internal_alpha_artifacts_available": False,
    }


def build_contract_packet() -> dict[str, Any]:
    # Consume 0175AN shape registry precedent
    shape_data = build_shape_registry_packet()
    platform_shapes = shape_data.get("platform_shapes", [])

    platform_surface_map = {
        "x": "x_thread_stub_surface",
        "telegram_channel_destination": "telegram_channel_stub_surface",
        "telegram_remote_operator": "telegram_remote_operator_stub_surface",
        "substack": "substack_outline_stub_surface",
        "linkedin": "linkedin_feed_stub_surface",
        "threads": "threads_stub_surface",
        "instagram": "instagram_caption_media_stub_surface",
        "facebook_page": "facebook_page_stub_surface",
        "tiktok": "tiktok_caption_video_stub_surface",
        "youtube": "youtube_metadata_video_stub_surface"
    }

    render_records: list[PlatformPreviewDryRenderRecord] = []
    total_fields_count = 0

    blockers = build_dry_render_blockers()
    blocked_ids = [b.blocker_id for b in blockers]

    for shape in platform_shapes:
        tid = shape["platform_target_id"]
        family = shape["platform_family"]
        surface = platform_surface_map.get(tid, "unknown_surface")

        field_renders: list[PlatformPreviewDryRenderField] = []
        for field in shape["fields"]:
            fname = field["field_name"]
            field_renders.append(
                PlatformPreviewDryRenderField(
                    field_name=fname,
                    placeholder_value=f"[DRY_RENDER_PLACEHOLDER_ONLY: {tid}.{fname}]",
                    placeholder_only=True,
                    publishable_text=False,
                    platform_ready=False,
                    dispatch_ready=False,
                    generated_by_provider=False,
                    requires_human_rewrite=True,
                    contains_market_number=False,
                    contains_financial_advice=False,
                    contains_signal_language=False
                )
            )
        total_fields_count += len(field_renders)

        raw_record = {
            "render_id": f"dry_render_{tid}",
            "platform_target_id": tid,
            "platform_family": family,
            "source_shape_id": f"shape_{tid}",
            "render_status": "dry_render_blocked",
            "preview_surface_type": surface,
            "field_renders": [_asdict(fr) for fr in field_renders],
            "watermark": "[DRY_RENDER_WATERMARK_NON_PUBLISHABLE_SCHEMA_ONLY]",
            "blocker_banner": f"[DRY_RENDER_BLOCKER_BANNER: ACTIVE_BLOCKERS_PREVENT_PUBLICATION: {', '.join(blocked_ids)}]",
            "citation_slot_status": "citation_rendering_required_but_pending",
            "limitation_slot_status": "limitation_rendering_required_but_pending",
            "operator_review_status": "review_required_but_pending",
            "account_binding_status": "binding_required_but_inactive",
            "credential_gate_status": "credential_required_but_locked",
            "payload_hash_lock_status": "hash_lock_required_but_pending",
            "dispatch_gate_status": "dispatch_gate_required_but_locked",
            "publishability_status": "non_publishable_dry_render",
            "blocked_reasons": blocked_ids,
            "missing_future_gates": ["lane_c_platform_preview_dry_render_to_review_bundle_gate"],
            "placeholder_only": True,
            "publishable_text": False,
            "platform_ready": False,
            "dispatch_ready": False,
            "platform_payload_created": False,
            "publishable_payload_created": False,
            "export_ready": False,
            "operator_review_required": True,
            "account_binding_active": False,
            "credential_values_loaded": False,
            "platform_api_called": False,
            "scheduler_enabled": False,
            "approved_for_publication": False,
        }

        rec_hash = _digest(raw_record)
        render_records.append(
            PlatformPreviewDryRenderRecord(
                packet_hash=rec_hash,
                **raw_record
            )
        )

    safety = build_safety_flags()

    summary_counts = {
        "registered_shapes_count": len(platform_shapes),
        "registered_renders_count": len(render_records),
        "total_fields_rendered_count": total_fields_count,
        "evaluation_rules_count": len(shape_data.get("shape_rules", [])),
        "global_blockers_count": len(blockers)
    }

    blocked_caps = [
        "live_publishing_dispatch",
        "autonomous_reply_automation",
        "live_credential_hydration",
        "active_scheduler_triggers"
    ]

    missing_gates = [
        "lane_c_platform_preview_dry_render_to_review_bundle_gate",
        "production_key_vault_decrypter",
        "live_operator_signature_vault"
    ]

    packet = PlatformPreviewDryRenderPacket(
        task_label=TASK_LABEL,
        matrix_version=MATRIX_VERSION,
        source_baseline_commit=SOURCE_BASELINE_COMMIT,
        generated_at_epoch=0,
        platform_shapes=platform_shapes,
        render_records=render_records,
        global_blockers=blockers,
        summary_counts=summary_counts,
        safety_flags=safety,
        blocked_capabilities=blocked_caps,
        missing_future_gates=missing_gates,
        ledger_family=LEDGER_FAMILY,
        packet_hash="",
        hash_algorithm=HASH_ALGORITHM,
        next_required_gate="lane_c_platform_preview_dry_render_to_review_bundle_gate"
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
    renders = packet["render_records"]
    blockers = packet["global_blockers"]
    counts = packet["summary_counts"]
    safety = packet["safety_flags"]
    blocked_caps = packet["blocked_capabilities"]
    missing_gates = packet["missing_future_gates"]

    lines = [
        "# Platform Preview Dry Render Packet Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a platform preview dry render report for human inspection only.",
        "> It renders placeholders and active blockers but contains no publishable copy.",
        "> It does not compile live platform payloads, does not perform dispatch, and does not schedule posts.",
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
        "## Dry Render Summary Counts",
        "",
        f"- **Registered Platform Shapes**: `{counts['registered_shapes_count']}`",
        f"- **Registered Dry Renders**: `{counts['registered_renders_count']}`",
        f"- **Total Fields Rendered**: `{counts['total_fields_rendered_count']}`",
        f"- **Global Blocker Evaluators**: `{counts['global_blockers_count']}`",
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
        "## Global Dry Render Blocker Status",
        "",
        "| Blocker ID | Description | Active Status |",
        "|---|---|---|",
    ])

    for b in blockers:
        lines.append(f"| `{b['blocker_id']}` | {b['description']} | ✅ Active |")

    lines.extend([
        "",
        "## Registered Platform Preview Dry Renders",
        "",
    ])

    for r in renders:
        lines.extend([
            f"### Render Record: `{r['render_id']}`",
            "",
            f"- **Platform Target ID**: `{r['platform_target_id']}`",
            f"- **Platform Family**: `{r['platform_family']}`",
            f"- **Source Shape ID**: `{r['source_shape_id']}`",
            f"- **Render Status**: `{r['render_status']}`",
            f"- **Preview Surface Type**: `{r['preview_surface_type']}`",
            f"- **Watermark**: `{r['watermark']}`",
            f"- **Blocker Banner**: `{r['blocker_banner']}`",
            f"- **Citation Slot Status**: `{r['citation_slot_status']}`",
            f"- **Limitation Slot Status**: `{r['limitation_slot_status']}`",
            f"- **Operator Review**: `{r['operator_review_status']}`",
            f"- **Account Binding**: `{r['account_binding_status']}`",
            f"- **Credential Gate**: `{r['credential_gate_status']}`",
            f"- **Payload Hash Lock**: `{r['payload_hash_lock_status']}`",
            f"- **Dispatch Gate**: `{r['dispatch_gate_status']}`",
            f"- **Publishability Status**: `{r['publishability_status']}`",
            "",
            "#### Field Renders",
            "",
            "| Field Name | Placeholder Value | placeholder_only | publishable_text | platform_ready | dispatch_ready |",
            "|---|---|---|---|---|---|",
        ])

        for f in r["field_renders"]:
            lines.append(
                f"| `{f['field_name']}` | `{f['placeholder_value']}` | `{f['placeholder_only']}` | `{f['publishable_text']}` | `{f['platform_ready']}` | `{f['dispatch_ready']}` |"
            )
        lines.append("")

    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AO")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
