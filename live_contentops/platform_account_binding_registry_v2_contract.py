"""Platform account binding registry v2 contract for ContentOps 0174UG.

Deterministic local-only destination identity model. No live/API/provider/network/env/
credential/browser/scheduler/scraping/DM behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops import platform_universe_registry_v2 as universe
from live_contentops import primary_platform_payload_preview_contracts as previews
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UG_PLATFORM_ACCOUNT_BINDING_REGISTRY_V2_CONTRACT_V0"
REGISTRY_VERSION = "0174UG_PLATFORM_ACCOUNT_BINDING_REGISTRY_V2_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "ee309aa9513c81c1ae028935b5b23c8a391ee2ef"
DOC_REL_DIR = Path("docs") / "automation" / "0174UG"
PACKET_FILENAME = "platform_account_binding_registry_v2_contract_packet.json"
RUNBOOK_FILENAME = "platform_account_binding_registry_v2_contract.md"
HASH_ALGORITHM = "sha256"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UH_CREDENTIAL_HANDLE_AND_DOTENV_SECRET_BOUNDARY_V2_CONTRACT_V0"
AUDIT_FAMILY = "platform_account_binding_future"
PLATFORM_IDS = tuple(entry.platform_id for entry in universe.PLATFORMS)


@dataclass(frozen=True)
class PlatformAccountBinding:
    binding_id: str
    platform_id: str
    destination_kind: str
    destination_label_redacted: str
    destination_public_handle_or_slug_redacted: str
    provider_account_ref_redacted: str
    account_role: str
    platform_role: str
    binding_status: str
    live_read_allowed: bool
    live_write_allowed: bool
    public_post_allowed: bool
    credential_handle_required: bool
    credential_handle_id: str
    required_permission_families: tuple[str, ...]
    required_future_gates: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
    binding_hash: str
    binding_hash_algorithm: str


@dataclass(frozen=True)
class AccountBindingRegistryPacket:
    packet_id: str
    registry_version: str
    generated_at_epoch: int
    bindings: tuple[PlatformAccountBinding, ...]
    bindings_by_platform: dict[str, tuple[str, ...]]
    missing_binding_platforms: tuple[str, ...]
    blocked_binding_platforms: tuple[str, ...]
    live_read_allowed_count: int
    live_write_allowed_count: int
    public_post_allowed_count: int
    credential_hydrated_count: int
    platform_api_called_count: int
    wrong_destination_block_count: int
    all_bindings_symbolic_or_blocked: bool
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
    u9_audit_entry_ids: tuple[str, ...]
    u9_audit_entry_families: tuple[str, ...]
    packet_hash: str
    packet_hash_algorithm: str
    next_required_gate: str


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


def _unique(values: Any) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(v) for v in values if v))


def safety_flags() -> dict[str, bool]:
    false_flags = (
        "live_read_allowed", "live_write_allowed", "public_post_allowed",
        "credential_hydrated", "platform_api_called", "provider_api_called",
        "telegram_api_called", "network_performed", "env_read",
        "browser_session_used", "scheduler_enabled", "scraping_performed",
        "dm_or_reply_automation_allowed", "dispatch_ready", "public_postable",
        "autonomous_posting_allowed", "current_truth_promoted", "dqr_cleared",
        "readiness_cleared", "ingestion_repo_mutated", "ui_generated",
    )
    return {**{flag: False for flag in false_flags}, "local_symbolic_binding_only": True, "review_only": True}


def _binding_material(*, platform_id: str, destination_kind: str, account_role: str, platform_role: str, credential_handle_id: str) -> dict[str, str]:
    return {
        "platform_id": platform_id,
        "destination_kind": destination_kind,
        "account_role": account_role,
        "platform_role": platform_role,
        "credential_handle_id": credential_handle_id,
        "registry_version": REGISTRY_VERSION,
    }


def _binding_id(material: dict[str, str]) -> str:
    return "platform_account_binding_" + _digest(material)[:24]


def _make_binding(
    *,
    platform_id: str,
    destination_kind: str,
    account_role: str,
    platform_role: str,
    binding_status: str,
    required_permission_families: tuple[str, ...],
    required_future_gates: tuple[str, ...],
    blocked_reasons: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    credential_handle_id: str | None = None,
) -> PlatformAccountBinding:
    handle = credential_handle_id or f"symbolic_credential_handle:{platform_id}"
    material = _binding_material(platform_id=platform_id, destination_kind=destination_kind, account_role=account_role, platform_role=platform_role, credential_handle_id=handle)
    bid = _binding_id(material)
    hash_basis = {
        **material,
        "binding_status": binding_status,
        "required_permission_families": required_permission_families,
        "required_future_gates": required_future_gates,
        "blocked_reasons": blocked_reasons,
        "evidence_refs": evidence_refs,
    }
    return PlatformAccountBinding(
        binding_id=bid,
        platform_id=platform_id,
        destination_kind=destination_kind,
        destination_label_redacted=f"redacted_destination_label:{platform_id}:{destination_kind}",
        destination_public_handle_or_slug_redacted=f"redacted_public_handle_or_slug:{platform_id}",
        provider_account_ref_redacted=f"redacted_provider_account_ref:{platform_id}",
        account_role=account_role,
        platform_role=platform_role,
        binding_status=binding_status,
        live_read_allowed=False,
        live_write_allowed=False,
        public_post_allowed=False,
        credential_handle_required=True,
        credential_handle_id=handle,
        required_permission_families=required_permission_families,
        required_future_gates=required_future_gates,
        evidence_refs=evidence_refs,
        safety_flags=safety_flags(),
        blocked_reasons=blocked_reasons,
        binding_hash=_digest(hash_basis),
        binding_hash_algorithm=HASH_ALGORITHM,
    )


_BINDING_SPECS = (
    ("x", "user_profile", "brand_channel", "primary_public_velocity", "needs_identity_proof", ("identity_proof", "posting_permission"), ("credential_boundary_future", "permission_scope_gate_future", "platform_preflight_future"), ("x_identity_proof_required", "live_write_gate_closed")),
    ("telegram_remote_operator", "operator_inbox", "operator", "remote_operator", "needs_identity_proof", ("sender_chat_proof",), ("credential_boundary_future", "platform_preflight_future"), ("operator_inbox_chat_proof_required", "not_public_destination", "dispatch_gate_closed")),
    ("telegram_channel_destination", "channel", "brand_channel", "community_channel", "needs_permission_proof", ("bot_admin_permission", "channel_destination_proof"), ("credential_boundary_future", "permission_scope_gate_future", "platform_preflight_future"), ("channel_permission_proof_required", "live_write_gate_closed")),
    ("substack_newsletter", "newsletter_publication", "owned_publication", "owned_longform", "configured_symbolic", ("manual_export_publication_proof",), ("platform_docs_evidence_future", "platform_preflight_future"), ("manual_export_first_no_api", "live_write_gate_closed")),
    ("linkedin", "user_profile", "professional_profile", "professional_credibility", "needs_identity_proof", ("member_profile_identity",), ("credential_boundary_future", "permission_scope_gate_future", "platform_preflight_future"), ("linkedin_member_profile_proof_required", "live_write_gate_closed")),
    ("linkedin", "organization_page", "organization_page", "professional_credibility", "missing_binding", ("organization_page_admin_proof",), ("credential_boundary_future", "permission_scope_gate_future", "platform_preflight_future"), ("linkedin_organization_page_binding_missing", "organization_page_proof_required")),
    ("threads", "user_profile", "expansion_channel", "expansion_social", "needs_identity_proof", ("meta_app_account_proof",), ("credential_boundary_future", "platform_docs_evidence_future", "platform_preflight_future"), ("meta_app_account_proof_required", "live_write_gate_closed")),
    ("instagram", "business_account", "expansion_channel", "expansion_visual", "needs_permission_proof", ("business_or_creator_account_proof", "media_public_url_proof", "app_review_proof"), ("credential_boundary_future", "platform_docs_evidence_future", "permission_scope_gate_future", "platform_preflight_future"), ("instagram_business_creator_proof_required", "media_public_url_gate_closed", "app_review_gate_closed")),
    ("facebook_page", "page", "organization_page", "expansion_social", "needs_permission_proof", ("page_role_proof", "app_review_proof"), ("credential_boundary_future", "platform_docs_evidence_future", "permission_scope_gate_future", "platform_preflight_future"), ("facebook_page_role_proof_required", "app_review_gate_closed")),
    ("tiktok", "creator_account", "video_channel", "later_video", "needs_identity_proof", ("creator_account_proof", "video_publish_scope_proof"), ("credential_boundary_future", "rate_budget_kill_switch_future", "platform_preflight_future"), ("creator_account_video_publish_proof_required", "later_video_gate_closed")),
    ("youtube", "video_channel", "video_channel", "later_video", "needs_permission_proof", ("oauth_channel_proof", "quota_upload_scope_proof"), ("credential_boundary_future", "rate_budget_kill_switch_future", "permission_scope_gate_future", "platform_preflight_future"), ("youtube_oauth_channel_proof_required", "quota_upload_gate_closed", "later_video_gate_closed")),
)


def build_default_bindings() -> tuple[PlatformAccountBinding, ...]:
    universe_ids = set(PLATFORM_IDS)
    bindings = []
    for platform_id, destination_kind, account_role, platform_role, status, perms, gates, blockers in _BINDING_SPECS:
        if platform_id not in universe_ids:
            status = "blocked"
            blockers = tuple(blockers) + ("platform_not_in_universe_registry",)
        refs = (f"docs/automation/0174U1/platform_universe_registry_v2_packet.json", f"binding_spec:{platform_id}:{destination_kind}")
        bindings.append(_make_binding(platform_id=platform_id, destination_kind=destination_kind, account_role=account_role, platform_role=platform_role, binding_status=status, required_permission_families=perms, required_future_gates=gates, blocked_reasons=blockers, evidence_refs=refs))
    return tuple(bindings)


def validate_preview_destination_binding(preview: previews.PlatformPayloadPreview, binding: PlatformAccountBinding) -> PlatformAccountBinding:
    blockers = list(binding.blocked_reasons)
    status = binding.binding_status
    if preview.platform_id != binding.platform_id or preview.destination_binding_id != binding.binding_id:
        blockers.append("wrong_destination_blocked")
        blockers.append("preview_destination_binding_mismatch")
        status = "wrong_destination_blocked"
    return replace(binding, binding_status=status, blocked_reasons=_unique(blockers), safety_flags=safety_flags())


def build_u9_audit_entries(packet_or_bindings: AccountBindingRegistryPacket | tuple[PlatformAccountBinding, ...]) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    bindings = packet_or_bindings.bindings if hasattr(packet_or_bindings, "bindings") else packet_or_bindings
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UG"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, binding in enumerate(bindings, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UG",
            source_model_version=REGISTRY_VERSION,
            payload={
                "id": binding.binding_id,
                "platform_id": binding.platform_id,
                "status": binding.binding_status,
                "source_payload_hash": binding.binding_hash,
                "evidence_refs": binding.evidence_refs,
                "blocked_reasons": binding.blocked_reasons,
                "safety_flags": binding.safety_flags,
            },
            policy=policy,
        )
        entries.append(entry)
        prev = entry.entry_hash
    return tuple(entries)


def build_platform_account_binding_registry_packet(*, bindings: tuple[PlatformAccountBinding, ...] | None = None, mismatch_previews: tuple[previews.PlatformPayloadPreview, ...] = ()) -> AccountBindingRegistryPacket:
    base_bindings = bindings or build_default_bindings()
    by_id = {binding.binding_id: binding for binding in base_bindings}
    updated = dict(by_id)
    for preview in mismatch_previews:
        if preview.destination_binding_id in updated:
            updated[preview.destination_binding_id] = validate_preview_destination_binding(preview, updated[preview.destination_binding_id])
    final_bindings = tuple(updated[b.binding_id] for b in base_bindings)
    bindings_by_platform = {pid: tuple(b.binding_id for b in final_bindings if b.platform_id == pid) for pid in PLATFORM_IDS}
    missing = _unique(b.platform_id for b in final_bindings if b.binding_status == "missing_binding")
    blocked = _unique(b.platform_id for b in final_bindings if b.binding_status in {"wrong_destination_blocked", "blocked"})
    evidence_refs = _unique(ref for b in final_bindings for ref in b.evidence_refs)
    blockers = _unique(reason for b in final_bindings for reason in b.blocked_reasons)
    audit_entries = build_u9_audit_entries(final_bindings)
    draft = {
        "registry_version": REGISTRY_VERSION,
        "generated_at_epoch": 0,
        "bindings": final_bindings,
        "bindings_by_platform": bindings_by_platform,
        "missing_binding_platforms": missing,
        "blocked_binding_platforms": blocked,
        "live_read_allowed_count": sum(1 for b in final_bindings if b.live_read_allowed),
        "live_write_allowed_count": sum(1 for b in final_bindings if b.live_write_allowed),
        "public_post_allowed_count": sum(1 for b in final_bindings if b.public_post_allowed),
        "credential_hydrated_count": sum(1 for b in final_bindings if b.safety_flags.get("credential_hydrated")),
        "platform_api_called_count": sum(1 for b in final_bindings if b.safety_flags.get("platform_api_called")),
        "wrong_destination_block_count": sum(1 for b in final_bindings if b.binding_status == "wrong_destination_blocked"),
        "all_bindings_symbolic_or_blocked": all(b.binding_status in {"configured_symbolic", "missing_binding", "needs_identity_proof", "needs_permission_proof", "wrong_destination_blocked", "blocked"} for b in final_bindings),
        "evidence_refs": evidence_refs,
        "safety_flags": safety_flags(),
        "blocked_reasons": blockers,
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "next_required_gate": NEXT_REQUIRED_GATE,
    }
    packet_hash = _digest(draft)
    return AccountBindingRegistryPacket(
        packet_id="platform_account_binding_registry_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft,
    )


def registry_checksum() -> str:
    return build_platform_account_binding_registry_packet().packet_hash


def render_runbook(packet: AccountBindingRegistryPacket) -> str:
    lines = [
        "# 0174UG Platform Account Binding Registry V2 Contract",
        "",
        f"- task_label: `{TASK_LABEL}`",
        f"- registry_version: `{packet.registry_version}`",
        f"- source_baseline_commit: `{SOURCE_BASELINE_COMMIT}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`",
        f"- next_required_gate: `{packet.next_required_gate}`",
        "",
        "## Binding Coverage",
    ]
    for binding in packet.bindings:
        lines.append(f"- `{binding.platform_id}` / `{binding.destination_kind}` / `{binding.account_role}` / `{binding.binding_status}`")
    lines.extend([
        "",
        "## Required Distinctions",
        "",
        "- `telegram_remote_operator` is an `operator_inbox` binding and is not a public channel destination.",
        "- `telegram_channel_destination` is a `channel` binding for future supervised channel posts.",
        "- `linkedin` includes member/profile symbolic binding and separate organization/page missing proof state.",
        "",
        "## Safety",
        "",
        "- All live read/write/public post flags remain false.",
        "- Credential handles are symbolic only; no credentials are hydrated or read.",
        "- No provider/API/network/env/browser/scheduler/scraping/DM behavior.",
        "- U9 audit family: `platform_account_binding_future`.",
        "- Wrong destination/platform preview binding mismatches fail closed as `wrong_destination_blocked`.",
        "",
        "## Packet Summary",
        "",
        "```json",
        json.dumps({
            "binding_count": len(packet.bindings),
            "platform_count": len(packet.bindings_by_platform),
            "missing_binding_platforms": packet.missing_binding_platforms,
            "blocked_binding_platforms": packet.blocked_binding_platforms,
            "live_read_allowed_count": packet.live_read_allowed_count,
            "live_write_allowed_count": packet.live_write_allowed_count,
            "public_post_allowed_count": packet.public_post_allowed_count,
            "credential_hydrated_count": packet.credential_hydrated_count,
            "platform_api_called_count": packet.platform_api_called_count,
            "wrong_destination_block_count": packet.wrong_destination_block_count,
        }, indent=2, sort_keys=True),
        "```",
        "",
    ])
    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UG")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_platform_account_binding_registry_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "PlatformAccountBinding",
    "AccountBindingRegistryPacket",
    "build_default_bindings",
    "build_platform_account_binding_registry_packet",
    "build_u9_audit_entries",
    "validate_preview_destination_binding",
    "registry_checksum",
    "write_artifacts",
]
