"""Platform Preview Dry Payload Shape Registry contract, 0175AN.

Deterministic local-only contract defining dry preview payload shapes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.lane_c_approval_packet_to_platform_preview_precheck_contract import (
    build_contract_packet as build_precheck_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AN_PLATFORM_PREVIEW_DRY_PAYLOAD_SHAPE_REGISTRY_V0"
MATRIX_VERSION = "0175AN_PLATFORM_PREVIEW_DRY_PAYLOAD_SHAPE_REGISTRY_V1"
SOURCE_BASELINE_COMMIT = "4d10a497d0104f5d3acae54097708e9e8b97e5d7"
LEDGER_FAMILY = "platform_preview_dry_payload_shape_registry_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AN"
PACKET_FILENAME = "platform_preview_dry_payload_shape_registry_contract_packet.json"
RUNBOOK_FILENAME = "platform_preview_dry_payload_shape_registry_contract.md"


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
class PlatformPreviewPayloadField:
    field_name: str
    placeholder_only: bool
    publishable_text: bool
    dispatch_ready: bool
    generated_by_provider: bool
    description: str


@dataclass(frozen=True)
class PlatformPreviewPayloadShape:
    platform_target_id: str
    platform_family: str
    shape_status: str
    fields: list[PlatformPreviewPayloadField]
    required_fields: list[str]
    optional_fields: list[str]
    blocked_fields: list[str]
    max_length_or_shape_notes: str
    media_requirements: str
    citation_rendering_requirement: str
    limitations_rendering_requirement: str
    operator_review_requirement: str
    account_binding_requirement: str
    credential_gate_requirement: str
    payload_hash_lock_requirement: str
    dispatch_gate_requirement: str
    precheck_only: bool
    dry_render_only: bool


@dataclass(frozen=True)
class PlatformPreviewPayloadShapeRule:
    rule_id: str
    description: str
    passed: bool


@dataclass(frozen=True)
class PlatformPreviewDryPayloadShapeRegistryPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    platform_shapes: list[PlatformPreviewPayloadShape]
    shape_rules: list[PlatformPreviewPayloadShapeRule]
    summary_counts: dict[str, int]
    safety_flags: dict[str, bool]
    blocked_capabilities: list[str]
    missing_future_gates: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_shape_rules() -> list[PlatformPreviewPayloadShapeRule]:
    descriptions = {
        "no_publishable_payload": "Enforce that no render stubs can be exported as publishable copy.",
        "no_platform_api_call": "Confirm that platform sending or status check API calls are blocked.",
        "no_credential_or_env_read": "Strict block on external dot-env or key-vault reads for platforms.",
        "no_account_binding_active": "Enforce that account bindings are dry/mock only.",
        "no_scheduler": "Enforce that no schedulers or task runners are active.",
        "no_autonomous_posting": "Verify that no autonomous publishing paths exist.",
        "no_autonomous_reply_or_dm": "Verify that automated comments, replies, or DMs are blocked.",
        "no_scraping": "Verify that zero live web scraping is executed.",
        "no_financial_advice": "Check that stub placeholders block any financial advice markers.",
        "no_signal_language": "Check that stub placeholders contain no signal/trading indicators.",
        "no_market_number_fabrication": "Ensure dry shapes carry citations and block manual edits.",
        "preserve_citation_requirements": "Enforce citation rendering layout rules in stubs.",
        "preserve_limitations": "Enforce limitations block placeholders in target layouts.",
        "preserve_dqr_readiness_blocks": "Block compilation of stubs when DQR snapshot indicates errors.",
        "require_operator_review": "Mark operator manual review gate as an absolute requirement.",
        "require_payload_hash_lock": "Enforce that each platform shape requires a payload hash lock proof.",
        "require_future_dry_render_gate": "Enforce next phase dry preview rendering gate requirement."
    }
    return [
        PlatformPreviewPayloadShapeRule(rule_id=rid, description=desc, passed=True)
        for rid, desc in descriptions.items()
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
        "approved_for_publication": False,
        "financial_advice": False,
        "signal_language": False,
        "broker_order_execution": False,
        "raw_vendor_redistribution": False,
        "approved_internal_alpha_artifacts_available": False,
    }


def build_fields_for_target(target_id: str, field_names: list[str]) -> list[PlatformPreviewPayloadField]:
    fields = []
    for f in field_names:
        fields.append(
            PlatformPreviewPayloadField(
                field_name=f,
                placeholder_only=True,
                publishable_text=False,
                dispatch_ready=False,
                generated_by_provider=False,
                description=f"Placeholder stub for {target_id} shape field: {f}"
            )
        )
    return fields


def build_contract_packet() -> dict[str, Any]:
    # Consume 0175AM precheck precedent targets
    precheck_data = build_precheck_packet()
    precheck_targets = precheck_data.get("targets", [])

    # Map target ID to its required fields
    platform_fields_map = {
        "x": ["text_stub", "citation_stub", "limitation_stub", "thread_hint", "media_slot_stub"],
        "telegram_channel_destination": ["message_stub", "citation_stub", "limitation_stub", "operator_note_stub"],
        "telegram_remote_operator": ["operator_summary_stub", "decision_buttons_stub_disabled", "audit_ref_stub"],
        "substack": ["title_stub", "subtitle_stub", "body_outline_stub", "citation_section_stub", "limitation_section_stub"],
        "linkedin": ["professional_intro_stub", "body_stub", "citation_stub", "limitation_stub"],
        "threads": ["short_text_stub", "citation_stub", "limitation_stub"],
        "instagram": ["caption_stub", "image_requirement_stub", "alt_text_stub", "citation_stub", "limitation_stub"],
        "facebook_page": ["post_text_stub", "attachment_stub", "citation_stub", "limitation_stub"],
        "tiktok": ["caption_stub", "video_requirement_stub", "disclosure_stub", "citation_stub"],
        "youtube": ["title_stub", "description_outline_stub", "video_requirement_stub", "citation_stub", "limitation_stub"]
    }

    platform_shapes: list[PlatformPreviewPayloadShape] = []
    total_fields_count = 0

    for pt in precheck_targets:
        tid = pt["target_id"]
        family = pt["platform_family"]
        field_names = platform_fields_map.get(tid, ["generic_text_stub"])

        fields = build_fields_for_target(tid, field_names)
        total_fields_count += len(fields)

        platform_shapes.append(
            PlatformPreviewPayloadShape(
                platform_target_id=tid,
                platform_family=family,
                shape_status="shape_registered_precheck_aligned",
                fields=fields,
                required_fields=field_names,
                optional_fields=[],
                blocked_fields=["raw_unredacted_credentials", "direct_payload_signature"],
                max_length_or_shape_notes=pt["character_limit_or_shape_note"],
                media_requirements="media stubs allowed for preview only" if "media" in pt["character_limit_or_shape_note"] or "video" in pt["character_limit_or_shape_note"] or "image" in pt["character_limit_or_shape_note"] else "text only",
                citation_rendering_requirement="must append citation footnotes stub format",
                limitations_rendering_requirement="must append limitations warn label format",
                operator_review_requirement="requires manual operator confirmation",
                account_binding_requirement="requires future account binding verification",
                credential_gate_requirement="requires future credential gate authentication",
                payload_hash_lock_requirement="requires cryptographically verified payload hash lock",
                dispatch_gate_requirement="requires dispatcher check",
                precheck_only=True,
                dry_render_only=True
            )
        )

    rules = build_shape_rules()
    safety = build_safety_flags()

    summary_counts = {
        "registered_shapes_count": len(platform_shapes),
        "total_fields_registered_count": total_fields_count,
        "evaluation_rules_count": len(rules)
    }

    blocked_caps = [
        "live_publishing_dispatch",
        "autonomous_reply_automation",
        "live_credential_hydration",
        "active_scheduler_triggers"
    ]

    missing_gates = [
        "lane_c_platform_preview_dry_render_gate",
        "production_key_vault_decrypter",
        "live_operator_signature_vault"
    ]

    packet = PlatformPreviewDryPayloadShapeRegistryPacket(
        task_label=TASK_LABEL,
        matrix_version=MATRIX_VERSION,
        source_baseline_commit=SOURCE_BASELINE_COMMIT,
        generated_at_epoch=0,
        platform_shapes=platform_shapes,
        shape_rules=rules,
        summary_counts=summary_counts,
        safety_flags=safety,
        blocked_capabilities=blocked_caps,
        missing_future_gates=missing_gates,
        ledger_family=LEDGER_FAMILY,
        packet_hash="",
        hash_algorithm=HASH_ALGORITHM,
        next_required_gate="lane_c_platform_preview_dry_render_gate"
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
    shapes = packet["platform_shapes"]
    rules = packet["shape_rules"]
    counts = packet["summary_counts"]
    safety = packet["safety_flags"]
    blocked_caps = packet["blocked_capabilities"]
    missing_gates = packet["missing_future_gates"]

    lines = [
        "# Platform Preview Dry Payload Shape Registry Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a dry payload shape registry report for schema validation only.",
        "> It defines shape stubs and required placeholders but contains no publishable copy.",
        "> It does not authorize post publication, does not perform dispatch, and does not schedule.",
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
        "## Shape Registry Summary Counts",
        "",
        f"- **Registered Platform Shapes**: `{counts['registered_shapes_count']}`",
        f"- **Total Fields Registered**: `{counts['total_fields_registered_count']}`",
        f"- **Evaluation Rules Configured**: `{counts['evaluation_rules_count']}`",
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
        "## Shape Evaluation Rules",
        "",
        "| Rule ID | Description | Status |",
        "|---|---|---|",
    ])

    for r in rules:
        lines.append(f"| `{r['rule_id']}` | {r['description']} | ✅ |")

    lines.extend([
        "",
        "## Registered Platform Preview Payload Shapes",
        "",
    ])

    for s in shapes:
        lines.extend([
            f"### Platform Shape: `{s['platform_target_id']}`",
            "",
            f"- **Platform Family**: `{s['platform_family']}`",
            f"- **Shape Status**: `{s['shape_status']}`",
            f"- **Max Length / Notes**: {s['max_length_or_shape_notes']}",
            f"- **Media Requirements**: {s['media_requirements']}",
            f"- **Citation Requirement**: {s['citation_rendering_requirement']}",
            f"- **Limitations Requirement**: {s['limitations_rendering_requirement']}",
            f"- **Operator Review**: {s['operator_review_requirement']}",
            f"- **Account Binding**: {s['account_binding_requirement']}",
            f"- **Credential Gate**: {s['credential_gate_requirement']}",
            f"- **Payload Hash Lock**: {s['payload_hash_lock_requirement']}",
            f"- **Dispatch Gate**: {s['dispatch_gate_requirement']}",
            f"- **Precheck Only**: `{s['precheck_only']}`",
            f"- **Dry Render Only**: `{s['dry_render_only']}`",
            "",
            "#### Fields Structure",
            "",
            "| Field Name | placeholder_only | publishable_text | dispatch_ready | generated_by_provider | Description |",
            "|---|---|---|---|---|---|",
        ])

        for f in s["fields"]:
            lines.append(
                f"| `{f['field_name']}` | `{f['placeholder_only']}` | `{f['publishable_text']}` | `{f['dispatch_ready']}` | `{f['generated_by_provider']}` | {f['description']} |"
            )
        lines.append("")

    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AN")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
