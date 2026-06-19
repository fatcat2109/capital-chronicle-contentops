"""Primary platform payload preview contracts for ContentOps 0174U2.

Local deterministic preview packet builder. No live dispatch, network,
provider, credential, env, scheduler, scraping, or DM behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops import platform_universe_registry_v2 as registry

TASK_LABEL = "TASK_CONTENTOPS_0174U2_PRIMARY_PLATFORM_PAYLOAD_PREVIEW_CONTRACTS_V0"
MODEL = "contentops.primary_platform_payload_preview_contracts"
MODEL_VERSION = "0174U2_PRIMARY_PLATFORM_PAYLOAD_PREVIEW_CONTRACTS_V1"
SOURCE_BASELINE_COMMIT = "b377d9a2abb9177f9b24e312e0991cfc5238695b"
DOC_REL_DIR = Path("docs") / "automation" / "0174U2"
PACKET_FILENAME = "primary_platform_payload_preview_contracts_packet.json"
RUNBOOK_FILENAME = "primary_platform_payload_preview_contracts.md"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174U3_SUBSTACK_NEWSLETTER_AND_MANUAL_EXPORT_CONTRACT_V0"
HASH_INPUT_FIELDS = (
    "platform_id",
    "payload_class_id",
    "destination_binding_id",
    "credential_handle_id",
    "title",
    "subtitle",
    "body",
    "thread_parts",
    "markdown_body",
    "media_manifest_id",
    "visibility_class",
    "disclosure_class",
    "citation_refs",
    "limitation_notes",
)
FORBIDDEN_SIGNAL_TERMS = (
    "buy",
    "sell",
    "hold",
    "price target",
    "trading signal",
    "signal",
    "entry point",
    "exit point",
    "guaranteed returns",
    "our model predicts",
)


@dataclass(frozen=True)
class PlatformPayloadPreview:
    preview_id: str
    source_content_id: str
    source_draft_id: str
    platform_id: str
    platform_family: str
    payload_class_id: str
    destination_binding_id: str
    credential_handle_id: str
    content_lane: str
    title: str
    subtitle: str
    body: str
    thread_parts: tuple[str, ...]
    markdown_body: str
    media_manifest_id: str
    media_shape: str
    visibility_class: str
    disclosure_class: str
    citation_refs: tuple[str, ...]
    limitation_notes: tuple[str, ...]
    no_signal_required: bool
    no_advice_required: bool
    source_citation_required_when_claimed: bool
    platform_constraints_status: str
    platform_warnings: tuple[str, ...]
    payload_hash: str
    payload_hash_algorithm: str
    approval_required: bool
    dispatch_ready: bool
    public_postable: bool
    manual_export_supported: bool
    preview_supported: bool
    safety_flags: dict[str, bool]
    evidence_refs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class PayloadPreviewValidationResult:
    validation_id: str
    preview_id: str
    platform_id: str
    payload_class_id: str
    registry_platform_match: bool
    registry_payload_match: bool
    payload_class_compatible: bool
    body_shape_valid: bool
    citation_requirements_satisfied: bool
    limitation_requirements_satisfied: bool
    no_signal_pass: bool
    no_advice_pass: bool
    no_live_defaults_pass: bool
    validation_status: str
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]


class PayloadPreviewContractError(ValueError):
    """Base preview contract error."""


class UnsupportedPlatformError(PayloadPreviewContractError):
    """Raised when platform lookup fails closed."""


class UnsupportedPayloadClassError(PayloadPreviewContractError):
    """Raised when payload class lookup fails closed."""


class IncompatiblePayloadClassError(PayloadPreviewContractError):
    """Raised when platform and payload class cannot pair."""


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _digest(data: dict[str, Any]) -> str:
    return sha256(_json(data).encode("utf-8")).hexdigest()


def _safe_tuple(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    return tuple(values or ())


def _lookup_platform(platform_id: str) -> registry.PlatformRegistryEntry:
    try:
        return registry.lookup_platform(platform_id)
    except registry.UnsupportedPlatformError as exc:
        raise UnsupportedPlatformError(f"unsupported_platform:{platform_id}") from exc


def _lookup_payload(payload_class_id: str) -> registry.PayloadClassEntry:
    try:
        return registry.lookup_payload_class(payload_class_id)
    except registry.UnsupportedPayloadClassError as exc:
        raise UnsupportedPayloadClassError(f"unsupported_payload_class:{payload_class_id}") from exc


def _require_compatible(platform_id: str, payload_class_id: str) -> tuple[registry.PlatformRegistryEntry, registry.PayloadClassEntry]:
    platform = _lookup_platform(platform_id)
    payload = _lookup_payload(payload_class_id)
    compat = registry.validate_payload_class_compatibility(platform_id, payload_class_id)
    if not compat["compatible"]:
        raise IncompatiblePayloadClassError(f"incompatible_payload_class:{platform_id}:{payload_class_id}")
    return platform, payload


def _contains_forbidden_language(*texts: str) -> bool:
    joined = "\n".join(texts).lower()
    return any(term in joined for term in FORBIDDEN_SIGNAL_TERMS)


def _safety_flags(platform: registry.PlatformRegistryEntry) -> dict[str, bool]:
    flags = dict(platform.safety_flags)
    for key in registry.NO_LIVE_DEFAULTS:
        flags[key] = False
    flags["preview_only_local_contract"] = True
    flags["manual_export_or_preview_only"] = bool(platform.safety_flags.get("manual_export_or_preview_only"))
    flags["future_supervised_dispatch_possible"] = bool(platform.safety_flags.get("future_supervised_dispatch_possible"))
    return flags


def _hash_material(kwargs: dict[str, Any]) -> dict[str, Any]:
    return {field: kwargs.get(field, "") for field in HASH_INPUT_FIELDS}


def compute_payload_hash(kwargs: dict[str, Any]) -> str:
    return _digest(_hash_material(kwargs))


def _preview_id(kwargs: dict[str, Any], payload_hash: str) -> str:
    return "preview_" + _digest({
        "source_content_id": kwargs["source_content_id"],
        "source_draft_id": kwargs["source_draft_id"],
        "platform_id": kwargs["platform_id"],
        "payload_class_id": kwargs["payload_class_id"],
        "payload_hash": payload_hash,
    })[:24]


def build_platform_payload_preview(
    *,
    source_content_id: str,
    source_draft_id: str,
    platform_id: str,
    payload_class_id: str,
    destination_binding_id: str = "symbolic_destination_binding",
    credential_handle_id: str = "symbolic_credential_handle",
    content_lane: str = "pre_alpha_process",
    title: str = "",
    subtitle: str = "",
    body: str = "",
    thread_parts: tuple[str, ...] | list[str] | None = None,
    markdown_body: str = "",
    media_manifest_id: str = "",
    visibility_class: str = "review_only_payload_preview",
    disclosure_class: str = "not_public_ready",
    citation_refs: tuple[str, ...] | list[str] | None = None,
    limitation_notes: tuple[str, ...] | list[str] | None = None,
    source_claims_exist: bool = False,
) -> PlatformPayloadPreview:
    platform, payload = _require_compatible(platform_id, payload_class_id)
    kwargs = {
        "source_content_id": source_content_id,
        "source_draft_id": source_draft_id,
        "platform_id": platform_id,
        "payload_class_id": payload_class_id,
        "destination_binding_id": destination_binding_id,
        "credential_handle_id": credential_handle_id,
        "title": title,
        "subtitle": subtitle,
        "body": body,
        "thread_parts": _safe_tuple(thread_parts),
        "markdown_body": markdown_body,
        "media_manifest_id": media_manifest_id,
        "visibility_class": visibility_class,
        "disclosure_class": disclosure_class,
        "citation_refs": _safe_tuple(citation_refs),
        "limitation_notes": _safe_tuple(limitation_notes),
    }
    blocked = list(platform.blocked_reasons) + list(payload.blocked_reasons)
    if source_claims_exist and not kwargs["citation_refs"]:
        blocked.append("missing_citation_refs_for_claimed_facts")
    if content_lane in {"grounded_news_context", "future_artifact_backed"} and not kwargs["limitation_notes"]:
        blocked.append("missing_limitation_notes_for_grounded_or_artifact_content")
    if _contains_forbidden_language(body, markdown_body, title, subtitle, *kwargs["thread_parts"]):
        blocked.append("forbidden_signal_or_advice_language")
    if platform_id in {"tiktok", "youtube"}:
        blocked.append("video_future_gate")
    if platform_id == "telegram_remote_operator":
        blocked.append("review_control_only_not_public_channel")
    payload_hash = compute_payload_hash(kwargs)
    return PlatformPayloadPreview(
        preview_id=_preview_id({**kwargs, "source_content_id": source_content_id, "source_draft_id": source_draft_id}, payload_hash),
        source_content_id=source_content_id,
        source_draft_id=source_draft_id,
        platform_id=platform.platform_id,
        platform_family=platform.platform_family,
        payload_class_id=payload.payload_class_id,
        destination_binding_id=destination_binding_id,
        credential_handle_id=credential_handle_id,
        content_lane=content_lane,
        title=title,
        subtitle=subtitle,
        body=body,
        thread_parts=kwargs["thread_parts"],
        markdown_body=markdown_body,
        media_manifest_id=media_manifest_id,
        media_shape=payload.media_shape,
        visibility_class=visibility_class,
        disclosure_class=disclosure_class,
        citation_refs=kwargs["citation_refs"],
        limitation_notes=kwargs["limitation_notes"],
        no_signal_required=payload.no_signal_required,
        no_advice_required=payload.no_advice_required,
        source_citation_required_when_claimed=payload.source_citation_required_when_claimed,
        platform_constraints_status="blocked_by_default" if blocked else "review_only_preview_valid",
        platform_warnings=tuple(platform.soft_guidelines),
        payload_hash=payload_hash,
        payload_hash_algorithm="sha256",
        approval_required=payload.approval_required,
        dispatch_ready=False,
        public_postable=False,
        manual_export_supported=payload.manual_export_supported or platform.manual_export_supported,
        preview_supported=platform.preview_supported,
        safety_flags=_safety_flags(platform),
        evidence_refs=tuple(dict.fromkeys((*platform.evidence_refs, *payload.evidence_refs))),
        blocked_reasons=tuple(dict.fromkeys(blocked)),
    )


def validate_platform_payload_preview(preview: PlatformPayloadPreview) -> PayloadPreviewValidationResult:
    platform = _lookup_platform(preview.platform_id)
    payload = _lookup_payload(preview.payload_class_id)
    compat = registry.validate_payload_class_compatibility(preview.platform_id, preview.payload_class_id)
    text_ok = bool(preview.body or preview.thread_parts or preview.markdown_body or preview.media_manifest_id)
    citation_ok = "missing_citation_refs_for_claimed_facts" not in preview.blocked_reasons
    limits_ok = "missing_limitation_notes_for_grounded_or_artifact_content" not in preview.blocked_reasons
    no_signal = "forbidden_signal_or_advice_language" not in preview.blocked_reasons
    false_flags = all(preview.safety_flags.get(key) is False for key in registry.NO_LIVE_DEFAULTS)
    no_live = false_flags and preview.dispatch_ready is False and preview.public_postable is False
    blockers = tuple(reason for reason in preview.blocked_reasons if reason not in {"live_gate_closed", "approval_required", "dispatch_revalidation_not_built"})
    status = "blocked" if blockers or not (text_ok and citation_ok and limits_ok and no_signal and no_live) else "review_only_preview_valid"
    validation_id = "validation_" + _digest({"preview_id": preview.preview_id, "payload_hash": preview.payload_hash, "status": status})[:24]
    return PayloadPreviewValidationResult(
        validation_id=validation_id,
        preview_id=preview.preview_id,
        platform_id=preview.platform_id,
        payload_class_id=preview.payload_class_id,
        registry_platform_match=platform.platform_id == preview.platform_id,
        registry_payload_match=payload.payload_class_id == preview.payload_class_id,
        payload_class_compatible=compat["compatible"],
        body_shape_valid=text_ok,
        citation_requirements_satisfied=citation_ok,
        limitation_requirements_satisfied=limits_ok,
        no_signal_pass=no_signal,
        no_advice_pass=no_signal,
        no_live_defaults_pass=no_live,
        validation_status=status,
        blocked_reasons=preview.blocked_reasons,
        evidence_refs=preview.evidence_refs,
    )


def _builder(platform_id: str, payload_class_id: str, **kwargs: Any) -> PlatformPayloadPreview:
    return build_platform_payload_preview(platform_id=platform_id, payload_class_id=payload_class_id, **kwargs)


def build_x_short_post_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("x", "x_short_post", **kwargs)


def build_x_thread_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("x", "x_thread", **kwargs)


def build_telegram_channel_update_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("telegram_channel_destination", "telegram_channel_update", **kwargs)


def build_telegram_operator_review_message_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("telegram_remote_operator", "telegram_operator_review_message", **kwargs)


def build_substack_newsletter_issue_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("substack_newsletter", "substack_newsletter_issue", **kwargs)


def build_substack_longform_post_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("substack_newsletter", "substack_longform_post", **kwargs)


def build_linkedin_professional_post_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("linkedin", "linkedin_professional_post", **kwargs)


def build_threads_short_post_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("threads", "threads_short_post", **kwargs)


def build_instagram_caption_asset_packet_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("instagram", "instagram_caption_asset_packet", **kwargs)


def build_instagram_carousel_script_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("instagram", "instagram_carousel_script", **kwargs)


def build_facebook_page_post_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("facebook_page", "facebook_page_post", **kwargs)


def build_tiktok_video_metadata_packet_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("tiktok", "tiktok_video_metadata_packet", **kwargs)


def build_youtube_video_metadata_packet_preview(**kwargs: Any) -> PlatformPayloadPreview:
    return _builder("youtube", "youtube_video_metadata_packet", **kwargs)


def _sample_kwargs() -> dict[str, Any]:
    return {
        "source_content_id": "source_content_0174U2_demo",
        "source_draft_id": "source_draft_0174U2_demo",
        "body": "Process note: limitations stay visible before any public preview.",
        "markdown_body": "## Process note\n\nLimitations stay visible before any public preview.",
        "citation_refs": ("source:0174U0",),
        "limitation_notes": ("local preview only; not public-ready",),
        "media_manifest_id": "media_manifest_symbolic",
    }


BUILDER_BY_PAYLOAD_CLASS = {
    "x_short_post": build_x_short_post_preview,
    "x_thread": build_x_thread_preview,
    "telegram_channel_update": build_telegram_channel_update_preview,
    "telegram_operator_review_message": build_telegram_operator_review_message_preview,
    "substack_newsletter_issue": build_substack_newsletter_issue_preview,
    "substack_longform_post": build_substack_longform_post_preview,
    "linkedin_professional_post": build_linkedin_professional_post_preview,
    "threads_short_post": build_threads_short_post_preview,
    "instagram_caption_asset_packet": build_instagram_caption_asset_packet_preview,
    "instagram_carousel_script": build_instagram_carousel_script_preview,
    "facebook_page_post": build_facebook_page_post_preview,
    "tiktok_video_metadata_packet": build_tiktok_video_metadata_packet_preview,
    "youtube_video_metadata_packet": build_youtube_video_metadata_packet_preview,
}


def build_contract_packet() -> dict[str, Any]:
    samples = [asdict(builder(**_sample_kwargs())) for builder in BUILDER_BY_PAYLOAD_CLASS.values()]
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "registry_checksum": registry.registry_checksum(),
        "preview_fields": list(PlatformPayloadPreview.__dataclass_fields__),
        "validation_fields": list(PayloadPreviewValidationResult.__dataclass_fields__),
        "hash_input_fields": list(HASH_INPUT_FIELDS),
        "builder_payload_classes": sorted(BUILDER_BY_PAYLOAD_CLASS),
        "sample_previews": samples,
        "no_live_defaults": dict(registry.NO_LIVE_DEFAULTS),
        "artifact_scope": "docs/automation/0174U2_only",
        "next_heavy_batch_recommendation": NEXT_HEAVY_BATCH,
    }
    packet["preview_contract_checksum"] = _digest(packet)
    return packet


def preview_contract_checksum() -> str:
    return build_contract_packet()["preview_contract_checksum"]


def _assert_safe_output(repo_root: str | Path, output_dir: str | Path | None) -> Path:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174U2")
    return out


def render_runbook(packet: dict[str, Any]) -> str:
    lines = [
        "# 0174U2 Primary Platform Payload Preview Contracts",
        "",
        f"- task_label: `{packet['task_label']}`",
        f"- model_version: `{packet['model_version']}`",
        f"- source_baseline_commit: `{packet['source_baseline_commit']}`",
        f"- registry_checksum: `{packet['registry_checksum']}`",
        f"- preview_contract_checksum: `{packet['preview_contract_checksum']}`",
        f"- next_heavy_batch_recommendation: `{packet['next_heavy_batch_recommendation']}`",
        "",
        "## Builder coverage",
    ]
    for payload_class_id in packet["builder_payload_classes"]:
        lines.append(f"- `{payload_class_id}`")
    lines.extend([
        "",
        "## Hash rules",
        "",
        "Payload hashes include platform, payload class, symbolic destination binding, symbolic credential handle, text fields, media manifest, citations, limitations, visibility, and disclosure.",
        "",
        "## No-live rules",
        "",
        "Dispatch and public-postable defaults stay false. Platform/API/provider/credential/env/scheduler/scraping/DM behavior stays false.",
        "",
        "## Scope confirmations",
        "",
        "- No UI/dashboard work.",
        "- No ingestion repo mutation.",
        "- No live/API/credential/provider/scheduler/scraping/DM behavior.",
        "- Artifact writer is locked to `docs/automation/0174U2`.",
    ])
    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    (out / PACKET_FILENAME).write_text(_json(packet), encoding="utf-8", newline="\n")
    (out / RUNBOOK_FILENAME).write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return packet
