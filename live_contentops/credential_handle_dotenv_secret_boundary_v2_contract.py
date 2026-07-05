"""Credential handle + dotenv secret boundary v2 contract for ContentOps 0174UH.

Deterministic local-only policy model. No real .env reads, credential hydration,
secret inspection, platform/provider API calls, network, browser, scheduler,
scraping, DM/reply automation, or UI behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from live_contentops import platform_account_binding_registry_v2_contract as bindings
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UH_CREDENTIAL_HANDLE_AND_DOTENV_SECRET_BOUNDARY_V2_CONTRACT_V0"
MODEL_VERSION = "0174UH_CREDENTIAL_HANDLE_DOTENV_SECRET_BOUNDARY_V2_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "af510f61ace36a2705eee8c5845c02ec6966d00e"
DOC_REL_DIR = Path("docs") / "automation" / "0174UH"
PACKET_FILENAME = "credential_handle_dotenv_secret_boundary_v2_contract_packet.json"
RUNBOOK_FILENAME = "credential_handle_dotenv_secret_boundary_v2_contract.md"
HASH_ALGORITHM = "sha256"
AUDIT_FAMILY = "credential_boundary_future"
NEXT_REQUIRED_GATE = "TASK_CONTENTOPS_0174UI_OFFICIAL_PLATFORM_DOCS_EVIDENCE_PACKET_MATRIX_V0"

LOCAL_CONTRACT_MODE = "local_contract_no_env"
APPROVED_READ_MODE = "approved_live_read_only_env_allowed"
APPROVED_WRITE_MODE = "approved_live_write_env_allowed"
APPROVED_PROVIDER_MODE = "approved_provider_llm_env_allowed"
MANUAL_EXPORT_MODE = "manual_export_no_env"
APPROVED_ENV_MODES = (APPROVED_READ_MODE, APPROVED_WRITE_MODE, APPROVED_PROVIDER_MODE)
ALLOWED_TASK_MODES = (LOCAL_CONTRACT_MODE, *APPROVED_ENV_MODES, MANUAL_EXPORT_MODE)

SECRET_SHAPED_RE = re.compile(
    r"(?i)(\d{6,}:[A-Za-z0-9_-]{30,}|bearer\s+[A-Za-z0-9._-]{8,}|token\s*[:=]\s*\S+|api[_-]?key\s*[:=]\s*\S+|client_secret\s*[:=]\s*\S+|password\s*[:=]\s*\S+|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)


@dataclass(frozen=True)
class CredentialHandle:
    credential_handle_id: str
    platform_id: str
    binding_id: str
    credential_kind: str
    secret_storage_ref_redacted: str
    dotenv_key_names: tuple[str, ...]
    required_scopes: tuple[str, ...]
    allowed_task_modes: tuple[str, ...]
    hydration_status: str
    dotenv_auto_load_allowed: bool
    runtime_secret_use_allowed: bool
    secret_display_allowed: bool
    secret_hash_display_allowed: bool
    secret_logging_allowed: bool
    secret_commit_allowed: bool
    evidence_secret_values_redacted: bool
    redaction_policy_id: str
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
    handle_hash: str
    handle_hash_algorithm: str


@dataclass(frozen=True)
class CredentialBoundaryPolicy:
    policy_id: str
    policy_version: str
    applies_to_platforms: tuple[str, ...]
    allowed_only_when_task_explicitly_approved: bool
    dotenv_auto_load_library_allowed: bool
    runtime_secret_use_allowed_in_approved_tasks: bool
    secret_values_must_never_be_printed: bool
    secret_values_must_never_be_logged: bool
    secret_values_must_never_be_hashed_for_display: bool
    secret_values_must_never_be_committed: bool
    secret_values_must_never_be_screenshotted: bool
    evidence_may_report_key_names: bool
    evidence_may_report_presence: bool
    evidence_may_report_scopes: bool
    evidence_may_report_endpoint_family: bool
    evidence_may_report_request_budget: bool
    evidence_may_report_redaction_status: bool
    failure_mode: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
    policy_hash: str


@dataclass(frozen=True)
class CredentialBoundaryPacket:
    packet_id: str
    policy: CredentialBoundaryPolicy
    credential_handles: tuple[CredentialHandle, ...]
    handles_by_platform: dict[str, tuple[str, ...]]
    dotenv_auto_load_allowed_count: int
    runtime_secret_use_allowed_count: int
    secret_display_allowed_count: int
    secret_logging_allowed_count: int
    secret_commit_allowed_count: int
    credential_hydrated_count: int
    env_read_count: int
    platform_api_called_count: int
    provider_api_called_count: int
    network_performed_count: int
    blocked_handle_count: int
    u9_audit_entry_ids: tuple[str, ...]
    u9_audit_entry_families: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
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
        "secret_display_allowed", "secret_hash_display_allowed",
        "secret_logging_allowed", "secret_commit_allowed",
        "secret_screenshot_allowed", "real_env_file_read", "real_secret_value_seen",
    )
    return {**{flag: False for flag in false_flags}, "local_symbolic_policy_only": True, "review_only": True}


def build_credential_boundary_policy() -> CredentialBoundaryPolicy:
    base = {
        "policy_id": "credential_boundary_policy_0174UH_v2",
        "policy_version": MODEL_VERSION,
        "applies_to_platforms": bindings.PLATFORM_IDS,
        "allowed_only_when_task_explicitly_approved": True,
        "dotenv_auto_load_library_allowed": True,
        "runtime_secret_use_allowed_in_approved_tasks": True,
        "secret_values_must_never_be_printed": True,
        "secret_values_must_never_be_logged": True,
        "secret_values_must_never_be_hashed_for_display": True,
        "secret_values_must_never_be_committed": True,
        "secret_values_must_never_be_screenshotted": True,
        "evidence_may_report_key_names": True,
        "evidence_may_report_presence": True,
        "evidence_may_report_scopes": True,
        "evidence_may_report_endpoint_family": True,
        "evidence_may_report_request_budget": True,
        "evidence_may_report_redaction_status": True,
        "failure_mode": (
            "fail_closed_missing_env", "fail_closed_scope_mismatch",
            "fail_closed_unapproved_task", "fail_closed_secret_output_detected",
        ),
        "evidence_refs": (
            "docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md#credential-env-readiness-policy",
            "docs/automation/0174UG/platform_account_binding_registry_v2_contract_packet.json",
            "docs/automation/0174U9/redacted_immutable_audit_ledger_v2_contract_packet.json",
        ),
        "safety_flags": safety_flags(),
        "blocked_reasons": ("local_contract_no_env", "no_real_secret_values", "future_explicit_approval_required"),
    }
    return CredentialBoundaryPolicy(policy_hash=_digest(base), **base)


_HANDLE_SPECS = {
    "x": ("oauth_client", ("X_CLIENT_ID", "X_CLIENT_SECRET", "X_ACCESS_TOKEN", "X_REFRESH_TOKEN"), ("tweet.read", "tweet.write", "users.read", "offline.access"), (APPROVED_READ_MODE, APPROVED_WRITE_MODE), ("x_oauth_app_review_required", "x_scopes_symbolic_only")),
    "telegram_remote_operator": ("bot_token", ("TELEGRAM_BOT_TOKEN", "TELEGRAM_OPERATOR_CHAT_ID"), ("getMe", "sendMessage:operator_inbox"), (APPROVED_READ_MODE, APPROVED_WRITE_MODE), ("operator_inbox_chat_id_presence_only", "telegram_operator_not_public_destination")),
    "telegram_channel_destination": ("bot_token", ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL_ID"), ("getMe", "sendMessage:channel", "administrator:can_post_messages"), (APPROVED_READ_MODE, APPROVED_WRITE_MODE), ("telegram_channel_admin_scope_symbolic_only", "channel_destination_proof_required")),
    "substack_newsletter": ("manual_export_no_api", (), ("manual_export_publication_proof",), (MANUAL_EXPORT_MODE,), ("manual_export_no_api", "official_api_not_approved")),
    "linkedin": ("oauth_client", ("LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_REFRESH_TOKEN"), ("openid", "profile", "w_member_social", "organization_admin_symbolic"), (APPROVED_READ_MODE, APPROVED_WRITE_MODE), ("linkedin_oauth_symbolic_only", "linkedin_app_review_scope_required")),
    "threads": ("oauth_client", ("META_APP_ID", "META_APP_SECRET", "THREADS_ACCESS_TOKEN", "THREADS_REFRESH_TOKEN"), ("threads_basic", "threads_content_publish"), (APPROVED_READ_MODE, APPROVED_WRITE_MODE), ("meta_app_review_required", "threads_scopes_symbolic_only")),
    "instagram": ("oauth_client", ("META_APP_ID", "META_APP_SECRET", "INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_BUSINESS_ACCOUNT_ID"), ("instagram_basic", "instagram_content_publish", "pages_show_list"), (APPROVED_READ_MODE, APPROVED_WRITE_MODE), ("instagram_business_or_creator_required", "meta_app_review_required")),
    "facebook_page": ("oauth_client", ("META_APP_ID", "META_APP_SECRET", "FACEBOOK_PAGE_ACCESS_TOKEN", "FACEBOOK_PAGE_ID"), ("pages_read_engagement", "pages_manage_posts", "pages_show_list"), (APPROVED_READ_MODE, APPROVED_WRITE_MODE), ("facebook_page_role_required", "meta_app_review_required")),
    "tiktok": ("oauth_client", ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN", "TIKTOK_REFRESH_TOKEN"), ("user.info.basic", "video.publish", "video.upload"), (APPROVED_READ_MODE, APPROVED_WRITE_MODE), ("tiktok_app_review_scope_required", "rate_budget_gate_required")),
    "youtube": ("oauth_client", ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "YOUTUBE_ACCESS_TOKEN", "YOUTUBE_REFRESH_TOKEN"), ("youtube.readonly", "youtube.upload"), (APPROVED_READ_MODE, APPROVED_WRITE_MODE), ("youtube_oauth_consent_required", "quota_budget_gate_required")),
}


def _binding_id_for_platform(platform_id: str) -> str:
    packet = bindings.build_platform_account_binding_registry_packet()
    ids = packet.bindings_by_platform[platform_id]
    return ids[0]


def _make_handle(platform_id: str, binding_id: str, kind: str, keys: tuple[str, ...], scopes: tuple[str, ...], modes: tuple[str, ...], blockers: tuple[str, ...]) -> CredentialHandle:
    forbidden = kind == "session_cookie_forbidden"
    env_allowed = any(mode in APPROVED_ENV_MODES for mode in modes) and not forbidden and kind != "manual_export_no_api"
    runtime_allowed = env_allowed
    hydration = "forbidden" if forbidden else ("symbolic_only" if kind in {"manual_export_no_api", "not_required_yet"} else "allowed_future_hydration")
    all_blockers = tuple(blockers) + (("session_cookie_forbidden_for_platform_automation",) if forbidden else ())
    material = {
        "platform_id": platform_id,
        "binding_id": binding_id,
        "credential_kind": kind,
        "dotenv_key_names": keys,
        "required_scopes": scopes,
        "allowed_task_modes": modes,
        "hydration_status": hydration,
        "redaction_policy_id": "redaction_policy_0174U9_v2",
        "model_version": MODEL_VERSION,
    }
    handle_hash = _digest(material)
    return CredentialHandle(
        credential_handle_id=f"symbolic_credential_handle:{platform_id}",
        platform_id=platform_id,
        binding_id=binding_id,
        credential_kind=kind,
        secret_storage_ref_redacted=f"redacted_secret_storage_ref:{platform_id}",
        dotenv_key_names=keys,
        required_scopes=scopes,
        allowed_task_modes=modes,
        hydration_status=hydration,
        dotenv_auto_load_allowed=env_allowed,
        runtime_secret_use_allowed=runtime_allowed,
        secret_display_allowed=False,
        secret_hash_display_allowed=False,
        secret_logging_allowed=False,
        secret_commit_allowed=False,
        evidence_secret_values_redacted=True,
        redaction_policy_id="redaction_policy_0174U9_v2",
        evidence_refs=(f"credential_handle_spec:{platform_id}", "docs/automation/0174UG/platform_account_binding_registry_v2_contract_packet.json"),
        safety_flags=safety_flags(),
        blocked_reasons=tuple(dict.fromkeys(all_blockers)),
        handle_hash=handle_hash,
        handle_hash_algorithm=HASH_ALGORITHM,
    )


LEGACY_MAP = {
    "x_profile": "x",
    "telegram_remote_operator_inbox": "telegram_remote_operator",
    "linkedin_member_profile": "linkedin",
    "threads_profile": "threads",
    "instagram_professional_account": "instagram",
    "facebook_page_text_link_post": "facebook_page",
    "tiktok_account": "tiktok",
    "youtube_channel": "youtube",
}


def build_default_credential_handles() -> tuple[CredentialHandle, ...]:
    handles = []
    for platform_id in bindings.PLATFORM_IDS:
        legacy_id = LEGACY_MAP.get(platform_id, platform_id)
        kind, keys, scopes, modes, blockers = _HANDLE_SPECS[legacy_id]
        handles.append(_make_handle(platform_id, _binding_id_for_platform(platform_id), kind, keys, scopes, modes, blockers))
    return tuple(handles)



def build_forbidden_session_cookie_handle(platform_id: str = "x") -> CredentialHandle:
    return _make_handle(platform_id, _binding_id_for_platform(platform_id), "session_cookie_forbidden", ("SESSION_COOKIE_FORBIDDEN",), ("forbidden_session_cookie",), (LOCAL_CONTRACT_MODE,), ("session_cookies_never_allowed",))


def evaluate_task_mode(handle: CredentialHandle, task_mode: str, approved: bool, granted_scopes: tuple[str, ...] = ()) -> CredentialHandle:
    blockers = list(handle.blocked_reasons)
    hydration = handle.hydration_status
    env_allowed = handle.dotenv_auto_load_allowed
    runtime_allowed = handle.runtime_secret_use_allowed
    if task_mode not in handle.allowed_task_modes or task_mode not in APPROVED_ENV_MODES or not approved:
        blockers.append("fail_closed_unapproved_task")
        env_allowed = False
        runtime_allowed = False
        hydration = "blocked"
    missing = tuple(scope for scope in handle.required_scopes if scope not in granted_scopes)
    if task_mode in APPROVED_ENV_MODES and approved and missing:
        blockers.append("fail_closed_scope_mismatch")
        env_allowed = False
        runtime_allowed = False
        hydration = "blocked"
    return replace(handle, dotenv_auto_load_allowed=env_allowed, runtime_secret_use_allowed=runtime_allowed, hydration_status=hydration, blocked_reasons=_unique(blockers), safety_flags=safety_flags())


def detect_secret_shaped_output(text: str) -> tuple[bool, str]:
    if SECRET_SHAPED_RE.search(text):
        return True, "fail_closed_secret_output_detected"
    return False, "pass"



def _audit_safe_safety_flags(flags: dict[str, bool]) -> dict[str, bool]:
    forbidden_key_terms = ("secret", "real_secret")
    return {key: value for key, value in flags.items() if not any(term in key.lower() for term in forbidden_key_terms)}


def build_u9_audit_entries(packet_or_handles: CredentialBoundaryPacket | tuple[CredentialHandle, ...]) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    handles = packet_or_handles.credential_handles if hasattr(packet_or_handles, "credential_handles") else packet_or_handles
    policy = audit.build_redaction_policy(("policy:0174U9", "policy:0174UH"))
    entries = []
    prev = audit.GENESIS_HASH
    for seq, handle in enumerate(handles, start=1):
        entry = audit.build_redacted_ledger_entry(
            entry_sequence=seq,
            previous_entry_hash=prev,
            entry_family=AUDIT_FAMILY,
            source_model="0174UH",
            source_model_version=MODEL_VERSION,
            payload={
                "id": handle.credential_handle_id,
                "platform_id": handle.platform_id,
                "status": handle.hydration_status,
                "source_payload_hash": handle.handle_hash,
                "evidence_refs": handle.evidence_refs,
                "blocked_reasons": handle.blocked_reasons,
                "safety_flags": _audit_safe_safety_flags(handle.safety_flags),
            },
            policy=policy,
        )
        entries.append(entry)
        prev = entry.entry_hash
    return tuple(entries)


def build_credential_boundary_packet(handles: tuple[CredentialHandle, ...] | None = None) -> CredentialBoundaryPacket:
    policy = build_credential_boundary_policy()
    credential_handles = handles or build_default_credential_handles()
    by_platform = {pid: tuple(h.credential_handle_id for h in credential_handles if h.platform_id == pid) for pid in bindings.PLATFORM_IDS}
    audit_entries = build_u9_audit_entries(credential_handles)
    blockers = _unique(reason for h in credential_handles for reason in h.blocked_reasons)
    evidence_refs = _unique(ref for h in credential_handles for ref in h.evidence_refs)
    draft = {
        "policy": policy,
        "credential_handles": credential_handles,
        "handles_by_platform": by_platform,
        "dotenv_auto_load_allowed_count": sum(1 for h in credential_handles if h.dotenv_auto_load_allowed),
        "runtime_secret_use_allowed_count": sum(1 for h in credential_handles if h.runtime_secret_use_allowed),
        "secret_display_allowed_count": sum(1 for h in credential_handles if h.secret_display_allowed),
        "secret_logging_allowed_count": sum(1 for h in credential_handles if h.secret_logging_allowed),
        "secret_commit_allowed_count": sum(1 for h in credential_handles if h.secret_commit_allowed),
        "credential_hydrated_count": sum(1 for h in credential_handles if h.safety_flags.get("credential_hydrated")),
        "env_read_count": sum(1 for h in credential_handles if h.safety_flags.get("env_read")),
        "platform_api_called_count": sum(1 for h in credential_handles if h.safety_flags.get("platform_api_called")),
        "provider_api_called_count": sum(1 for h in credential_handles if h.safety_flags.get("provider_api_called")),
        "network_performed_count": sum(1 for h in credential_handles if h.safety_flags.get("network_performed")),
        "blocked_handle_count": sum(1 for h in credential_handles if h.hydration_status in {"forbidden", "missing_policy", "blocked"}),
        "u9_audit_entry_ids": tuple(e.ledger_entry_id for e in audit_entries),
        "u9_audit_entry_families": tuple(e.entry_family for e in audit_entries),
        "evidence_refs": evidence_refs,
        "safety_flags": safety_flags(),
        "blocked_reasons": blockers,
        "next_required_gate": NEXT_REQUIRED_GATE,
    }
    packet_hash = _digest(draft)
    return CredentialBoundaryPacket(packet_id="credential_boundary_packet_" + packet_hash[:24], packet_hash=packet_hash, packet_hash_algorithm=HASH_ALGORITHM, **draft)


def render_runbook(packet: CredentialBoundaryPacket) -> str:
    lines = [
        "# 0174UH Credential Handle + Dotenv Secret Boundary V2 Contract",
        "",
        f"- task_label: `{TASK_LABEL}`",
        f"- model_version: `{MODEL_VERSION}`",
        f"- source_baseline_commit: `{SOURCE_BASELINE_COMMIT}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`",
        f"- next_required_gate: `{packet.next_required_gate}`",
        "",
        "## Handle Coverage",
    ]
    for handle in packet.credential_handles:
        lines.append(f"- `{handle.platform_id}` / `{handle.credential_kind}` / `{handle.hydration_status}` / `{handle.credential_handle_id}`")
    lines.extend([
        "",
        "## Boundary Rules",
        "",
        "- `.env` auto-load is modeled only for explicitly approved future live/API/provider modes.",
        "- This contract does not read `.env`, hydrate credentials, call APIs, or perform network requests.",
        "- Secret display, logging, hash-for-display, commit, and screenshot are always forbidden.",
        "- Evidence may report key names, presence, scopes, endpoint family, request budget, and redaction status only.",
        "- Session cookies are forbidden for platform automation.",
        "- Substack remains manual export / no API.",
        "- U9 audit family: `credential_boundary_future`.",
        "",
        "## Packet Summary",
        "",
        "```json",
        json.dumps({
            "handle_count": len(packet.credential_handles),
            "platform_count": len(packet.handles_by_platform),
            "dotenv_auto_load_allowed_count": packet.dotenv_auto_load_allowed_count,
            "runtime_secret_use_allowed_count": packet.runtime_secret_use_allowed_count,
            "credential_hydrated_count": packet.credential_hydrated_count,
            "env_read_count": packet.env_read_count,
            "platform_api_called_count": packet.platform_api_called_count,
            "provider_api_called_count": packet.provider_api_called_count,
            "network_performed_count": packet.network_performed_count,
            "secret_display_allowed_count": packet.secret_display_allowed_count,
            "secret_logging_allowed_count": packet.secret_logging_allowed_count,
            "secret_commit_allowed_count": packet.secret_commit_allowed_count,
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
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UH")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_credential_boundary_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


__all__ = [
    "CredentialHandle", "CredentialBoundaryPolicy", "CredentialBoundaryPacket",
    "build_credential_boundary_policy", "build_default_credential_handles",
    "build_forbidden_session_cookie_handle", "evaluate_task_mode",
    "detect_secret_shaped_output", "build_u9_audit_entries",
    "build_credential_boundary_packet", "render_runbook", "write_artifacts",
]
