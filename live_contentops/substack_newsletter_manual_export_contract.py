"""Substack newsletter manual export contract for ContentOps 0174U3.

Local deterministic manual-export package builder. No live dispatch, network,
provider, credential, env, scheduler, scraping, browser session, or DM behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops import platform_universe_registry_v2 as registry
from live_contentops import primary_platform_payload_preview_contracts as previews

TASK_LABEL = "TASK_CONTENTOPS_0174U3_SUBSTACK_NEWSLETTER_AND_MANUAL_EXPORT_CONTRACT_V0"
MODEL = "contentops.substack_newsletter_manual_export_contract"
MODEL_VERSION = "0174U3_SUBSTACK_NEWSLETTER_MANUAL_EXPORT_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "70c81b97164a30a3266e475af43321c6e799890c"
DOC_REL_DIR = Path("docs") / "automation" / "0174U3"
PACKET_FILENAME = "substack_newsletter_manual_export_contract_packet.json"
RUNBOOK_FILENAME = "substack_newsletter_manual_export_contract.md"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174U4_CONTENT_IDEA_PACKET_AND_LOCAL_INTENT_PARSER_CONTRACT_V0"
SUBSTACK_PLATFORM_ID = "substack_newsletter"
NEWSLETTER_PAYLOAD_CLASS = "substack_newsletter_issue"
LONGFORM_PAYLOAD_CLASS = "substack_longform_post"
ALLOWED_PAYLOAD_CLASSES = (NEWSLETTER_PAYLOAD_CLASS, LONGFORM_PAYLOAD_CLASS)
READY_FOR_MANUAL_REVIEW = "ready_for_manual_review"
BLOCKED = "blocked"
EXPORT_HASH_ALGORITHM = "sha256"
NO_SIGNAL_DISCLAIMER = (
    "This content is educational context only. It is not financial advice, "
    "not a buy/sell/hold recommendation, and not a trading signal."
)
MANUAL_PUBLISH_CHECKLIST = (
    "copy markdown manually",
    "verify title/subtitle",
    "verify citations",
    "verify limitations",
    "verify no-advice/no-signal disclaimer",
    "verify destination publication manually",
    "record final URL manually after publish",
    "record timestamp/operator ref manually",
    "record metrics manually later",
)
FORBIDDEN_STATUS_VALUES = (
    "live_ready",
    "live_publish_ready",
    "published_by_system",
    "system_published",
    "auto_published",
)
FORBIDDEN_SIGNAL_TERMS = previews.FORBIDDEN_SIGNAL_TERMS + (
    "financial advice",
    "recommendation to buy",
    "recommendation to sell",
)
SAFETY_FALSE_FLAGS = (
    "substack_api_called",
    "browser_session_used",
    "session_cookie_used",
    "platform_api_called",
    "provider_api_called",
    "credential_hydrated",
    "env_read",
    "network_performed",
    "scheduler_enabled",
    "autonomous_posting_allowed",
    "scraping_performed",
    "dm_or_reply_automation_allowed",
    "live_dispatch_enabled",
    "dispatch_ready",
    "public_postable",
)
EXPORT_HASH_INPUT_FIELDS = (
    "source_payload_hash",
    "title",
    "subtitle",
    "hook",
    "thesis_or_question",
    "body_sections",
    "source_notes",
    "citation_refs",
    "limitation_notes",
    "no_signal_disclaimer",
    "seo_metadata",
    "cross_platform_derivative_refs",
    "destination_binding_id",
    "manual_export_status",
)


@dataclass(frozen=True)
class SubstackNewsletterIssue:
    issue_id: str
    source_preview_id: str
    source_payload_hash: str
    source_content_id: str
    source_draft_id: str
    platform_id: str
    payload_class_id: str
    issue_type: str
    title: str
    subtitle: str
    hook: str
    thesis_or_question: str
    body_sections: tuple[str, ...]
    source_notes: tuple[str, ...]
    citation_refs: tuple[str, ...]
    limitation_notes: tuple[str, ...]
    no_signal_disclaimer: str
    seo_metadata: dict[str, Any]
    cross_platform_derivative_refs: tuple[str, ...]
    markdown_body: str
    export_hash: str
    export_hash_algorithm: str
    manual_export_status: str
    approval_required: bool
    dispatch_ready: bool
    public_postable: bool
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class SubstackManualExportPackage:
    export_package_id: str
    issue_id: str
    source_payload_hash: str
    markdown_body: str
    markdown_hash: str
    title: str
    subtitle: str
    slug_suggestion: str
    seo_title: str
    seo_description: str
    seo_keywords: tuple[str, ...]
    tags: tuple[str, ...]
    citation_footer: str
    limitation_section: str
    manual_publish_checklist: tuple[str, ...]
    manual_publish_record_required: bool
    exported_at_epoch: int
    operator_identity_ref: str
    destination_binding_id: str
    credential_handle_id: str
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class SubstackExportValidationResult:
    validation_id: str
    issue_id: str
    export_package_id: str
    source_preview_hash_match: bool
    payload_class_allowed: bool
    markdown_export_present: bool
    citations_present_when_required: bool
    limitations_present: bool
    no_signal_pass: bool
    no_advice_pass: bool
    seo_metadata_present: bool
    manual_checklist_present: bool
    no_live_defaults_pass: bool
    validation_status: str
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]


class SubstackManualExportContractError(ValueError):
    """Base Substack manual export contract error."""


class NonSubstackPreviewError(SubstackManualExportContractError):
    """Raised when a preview is not a Substack newsletter preview."""


class UnsupportedSubstackPayloadClassError(SubstackManualExportContractError):
    """Raised when a Substack preview uses unsupported payload class."""


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _digest(data: Any) -> str:
    return sha256(_json(data).encode("utf-8")).hexdigest()


def _safe_tuple(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    return tuple(values or ())


def _safety_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFETY_FALSE_FLAGS} | {"manual_export_only_local_contract": True}


def _contains_forbidden_language(*texts: str) -> bool:
    joined = "\n".join(texts).lower()
    normalized = joined.replace("no-signal", "nosignal")
    tokens = "".join(char if char.isalnum() else " " for char in normalized).split()
    for term in FORBIDDEN_SIGNAL_TERMS:
        if " " in term:
            if term in normalized:
                return True
            continue
        if term in tokens:
            return True
    return False


def _require_substack_preview(preview: previews.PlatformPayloadPreview) -> None:
    if preview.platform_id != SUBSTACK_PLATFORM_ID:
        raise NonSubstackPreviewError(f"non_substack_preview:{preview.platform_id}")
    if preview.payload_class_id not in ALLOWED_PAYLOAD_CLASSES:
        raise UnsupportedSubstackPayloadClassError(f"unsupported_substack_payload_class:{preview.payload_class_id}")
    compat = registry.validate_payload_class_compatibility(preview.platform_id, preview.payload_class_id)
    if not compat["compatible"]:
        raise UnsupportedSubstackPayloadClassError(
            f"incompatible_substack_payload_class:{preview.platform_id}:{preview.payload_class_id}"
        )


def _seo_present(seo_metadata: dict[str, Any]) -> bool:
    return all(seo_metadata.get(key) for key in ("seo_title", "seo_description", "seo_keywords", "slug_suggestion"))


def _manual_checklist_present(checklist: tuple[str, ...]) -> bool:
    return all(item in checklist for item in MANUAL_PUBLISH_CHECKLIST)


def _citation_footer(citation_refs: tuple[str, ...]) -> str:
    return "\n".join(f"- {ref}" for ref in citation_refs)


def _limitation_section(limitation_notes: tuple[str, ...]) -> str:
    return "\n".join(f"- {note}" for note in limitation_notes)


def render_markdown(
    *,
    title: str,
    subtitle: str,
    hook: str,
    thesis_or_question: str,
    body_sections: tuple[str, ...],
    citation_refs: tuple[str, ...],
    limitation_notes: tuple[str, ...],
    no_signal_disclaimer: str,
) -> str:
    lines = [f"# {title}", ""]
    if subtitle:
        lines.extend([f"## {subtitle}", ""])
    if hook:
        lines.extend([f"**Hook:** {hook}", ""])
    if thesis_or_question:
        lines.extend([f"**Thesis / question:** {thesis_or_question}", ""])
    for index, section in enumerate(body_sections, start=1):
        lines.extend([f"## Section {index}", "", section, ""])
    lines.extend(["## Citations", "", _citation_footer(citation_refs) or "- None provided", ""])
    lines.extend(["## Limitations", "", _limitation_section(limitation_notes) or "- None provided", ""])
    lines.extend(["## Disclaimer", "", no_signal_disclaimer, ""])
    return "\n".join(lines)


def compute_markdown_hash(markdown_body: str) -> str:
    return sha256(markdown_body.encode("utf-8")).hexdigest()


def compute_export_hash(material: dict[str, Any]) -> str:
    return _digest({field: material.get(field, "") for field in EXPORT_HASH_INPUT_FIELDS})


def _issue_id(preview: previews.PlatformPayloadPreview, export_hash: str) -> str:
    return "substack_issue_" + _digest({
        "preview_id": preview.preview_id,
        "payload_hash": preview.payload_hash,
        "export_hash": export_hash,
    })[:24]


def build_substack_issue_from_preview(
    preview: previews.PlatformPayloadPreview,
    *,
    issue_type: str,
    title: str | None = None,
    subtitle: str | None = None,
    hook: str = "",
    thesis_or_question: str = "",
    body_sections: tuple[str, ...] | list[str] | None = None,
    source_notes: tuple[str, ...] | list[str] | None = None,
    citation_refs: tuple[str, ...] | list[str] | None = None,
    limitation_notes: tuple[str, ...] | list[str] | None = None,
    seo_metadata: dict[str, Any] | None = None,
    cross_platform_derivative_refs: tuple[str, ...] | list[str] | None = None,
    source_claims_exist: bool = False,
) -> SubstackNewsletterIssue:
    _require_substack_preview(preview)
    if issue_type not in {"newsletter_issue", "longform_post"}:
        raise UnsupportedSubstackPayloadClassError(f"unsupported_issue_type:{issue_type}")
    issue_title = title if title is not None else (preview.title or "Untitled Substack Draft")
    issue_subtitle = subtitle if subtitle is not None else preview.subtitle
    sections = _safe_tuple(body_sections) or (preview.markdown_body or preview.body,)
    citations = _safe_tuple(citation_refs) if citation_refs is not None else preview.citation_refs
    limitations = _safe_tuple(limitation_notes) if limitation_notes is not None else preview.limitation_notes
    seo = dict(seo_metadata or {})
    derivatives = _safe_tuple(cross_platform_derivative_refs)
    notes = _safe_tuple(source_notes)
    markdown_body = render_markdown(
        title=issue_title,
        subtitle=issue_subtitle,
        hook=hook,
        thesis_or_question=thesis_or_question,
        body_sections=sections,
        citation_refs=citations,
        limitation_notes=limitations,
        no_signal_disclaimer=NO_SIGNAL_DISCLAIMER,
    )
    blocked = list(preview.blocked_reasons)
    if source_claims_exist and not citations:
        blocked.append("missing_citation_refs_for_claimed_facts")
    if preview.content_lane in {"grounded_news_context", "future_artifact_backed"} and not limitations:
        blocked.append("missing_limitation_notes_for_grounded_or_artifact_content")
    if not _seo_present(seo):
        blocked.append("missing_seo_metadata")
    if _contains_forbidden_language(issue_title, issue_subtitle, hook, thesis_or_question, *sections):
        blocked.append("forbidden_signal_or_advice_language")
    export_status = READY_FOR_MANUAL_REVIEW if not any(
        reason in blocked for reason in (
            "missing_citation_refs_for_claimed_facts",
            "missing_limitation_notes_for_grounded_or_artifact_content",
            "missing_seo_metadata",
            "forbidden_signal_or_advice_language",
        )
    ) else BLOCKED
    material = {
        "source_payload_hash": preview.payload_hash,
        "title": issue_title,
        "subtitle": issue_subtitle,
        "hook": hook,
        "thesis_or_question": thesis_or_question,
        "body_sections": sections,
        "source_notes": notes,
        "citation_refs": citations,
        "limitation_notes": limitations,
        "no_signal_disclaimer": NO_SIGNAL_DISCLAIMER,
        "seo_metadata": seo,
        "cross_platform_derivative_refs": derivatives,
        "destination_binding_id": preview.destination_binding_id,
        "manual_export_status": export_status,
    }
    export_hash = compute_export_hash(material)
    return SubstackNewsletterIssue(
        issue_id=_issue_id(preview, export_hash),
        source_preview_id=preview.preview_id,
        source_payload_hash=preview.payload_hash,
        source_content_id=preview.source_content_id,
        source_draft_id=preview.source_draft_id,
        platform_id=preview.platform_id,
        payload_class_id=preview.payload_class_id,
        issue_type=issue_type,
        title=issue_title,
        subtitle=issue_subtitle,
        hook=hook,
        thesis_or_question=thesis_or_question,
        body_sections=sections,
        source_notes=notes,
        citation_refs=citations,
        limitation_notes=limitations,
        no_signal_disclaimer=NO_SIGNAL_DISCLAIMER,
        seo_metadata=seo,
        cross_platform_derivative_refs=derivatives,
        markdown_body=markdown_body,
        export_hash=export_hash,
        export_hash_algorithm=EXPORT_HASH_ALGORITHM,
        manual_export_status=export_status,
        approval_required=True,
        dispatch_ready=False,
        public_postable=False,
        evidence_refs=tuple(dict.fromkeys((*preview.evidence_refs, "docs/automation/0174U3/substack_newsletter_manual_export_contract.md"))),
        safety_flags=_safety_flags(),
        blocked_reasons=tuple(dict.fromkeys(blocked)),
    )


def build_substack_newsletter_issue_from_preview(
    preview: previews.PlatformPayloadPreview,
    **kwargs: Any,
) -> SubstackNewsletterIssue:
    if preview.platform_id != SUBSTACK_PLATFORM_ID:
        raise NonSubstackPreviewError(f"non_substack_preview:{preview.platform_id}")
    if preview.payload_class_id != NEWSLETTER_PAYLOAD_CLASS:
        raise UnsupportedSubstackPayloadClassError(f"expected_newsletter_preview:{preview.payload_class_id}")
    return build_substack_issue_from_preview(preview, issue_type="newsletter_issue", **kwargs)


def build_substack_longform_post_from_preview(
    preview: previews.PlatformPayloadPreview,
    **kwargs: Any,
) -> SubstackNewsletterIssue:
    if preview.payload_class_id != LONGFORM_PAYLOAD_CLASS:
        raise UnsupportedSubstackPayloadClassError(f"expected_longform_preview:{preview.payload_class_id}")
    return build_substack_issue_from_preview(preview, issue_type="longform_post", **kwargs)


def _package_id(issue: SubstackNewsletterIssue, markdown_hash: str) -> str:
    return "substack_export_" + _digest({
        "issue_id": issue.issue_id,
        "source_payload_hash": issue.source_payload_hash,
        "markdown_hash": markdown_hash,
    })[:24]


def build_manual_export_package(
    issue: SubstackNewsletterIssue,
    *,
    operator_identity_ref: str = "operator_identity_ref_manual",
    destination_binding_id: str = "symbolic_destination_binding",
    credential_handle_id: str = "symbolic_credential_handle",
    tags: tuple[str, ...] | list[str] | None = None,
    manual_publish_checklist: tuple[str, ...] | list[str] | None = MANUAL_PUBLISH_CHECKLIST,
    exported_at_epoch: int = 0,
) -> SubstackManualExportPackage:
    checklist = _safe_tuple(manual_publish_checklist)
    blocked = list(issue.blocked_reasons)
    if not _manual_checklist_present(checklist):
        blocked.append("missing_manual_publish_checklist")
    if issue.manual_export_status in FORBIDDEN_STATUS_VALUES:
        blocked.append("forbidden_manual_export_status")
    markdown_hash = compute_markdown_hash(issue.markdown_body)
    seo_keywords = tuple(issue.seo_metadata.get("seo_keywords") or ())
    return SubstackManualExportPackage(
        export_package_id=_package_id(issue, markdown_hash),
        issue_id=issue.issue_id,
        source_payload_hash=issue.source_payload_hash,
        markdown_body=issue.markdown_body,
        markdown_hash=markdown_hash,
        title=issue.title,
        subtitle=issue.subtitle,
        slug_suggestion=str(issue.seo_metadata.get("slug_suggestion", "")),
        seo_title=str(issue.seo_metadata.get("seo_title", "")),
        seo_description=str(issue.seo_metadata.get("seo_description", "")),
        seo_keywords=seo_keywords,
        tags=_safe_tuple(tags),
        citation_footer=_citation_footer(issue.citation_refs),
        limitation_section=_limitation_section(issue.limitation_notes),
        manual_publish_checklist=checklist,
        manual_publish_record_required=True,
        exported_at_epoch=exported_at_epoch,
        operator_identity_ref=operator_identity_ref,
        destination_binding_id=destination_binding_id,
        credential_handle_id=credential_handle_id,
        safety_flags=_safety_flags(),
        blocked_reasons=tuple(dict.fromkeys(blocked)),
        evidence_refs=issue.evidence_refs,
    )


def validate_substack_export_package(
    issue: SubstackNewsletterIssue,
    package: SubstackManualExportPackage,
    *,
    source_preview: previews.PlatformPayloadPreview | None = None,
    source_claims_exist: bool = False,
) -> SubstackExportValidationResult:
    source_match = package.source_payload_hash == issue.source_payload_hash
    if source_preview is not None:
        source_match = source_match and source_preview.payload_hash == issue.source_payload_hash
    payload_allowed = issue.platform_id == SUBSTACK_PLATFORM_ID and issue.payload_class_id in ALLOWED_PAYLOAD_CLASSES
    markdown_present = bool(package.markdown_body and package.markdown_hash)
    citations_ok = bool(issue.citation_refs) or not source_claims_exist
    limitations_ok = bool(issue.limitation_notes)
    no_signal = "forbidden_signal_or_advice_language" not in issue.blocked_reasons
    seo_ok = all((package.seo_title, package.seo_description, package.seo_keywords, package.slug_suggestion))
    checklist_ok = _manual_checklist_present(package.manual_publish_checklist)
    no_live = (
        issue.dispatch_ready is False
        and issue.public_postable is False
        and all(issue.safety_flags.get(flag) is False for flag in SAFETY_FALSE_FLAGS)
        and all(package.safety_flags.get(flag) is False for flag in SAFETY_FALSE_FLAGS)
    )
    blocked = list(issue.blocked_reasons) + list(package.blocked_reasons)
    if not source_match:
        blocked.append("source_preview_hash_mismatch")
    if not payload_allowed:
        blocked.append("payload_class_not_allowed")
    if not markdown_present:
        blocked.append("markdown_export_missing")
    if not citations_ok:
        blocked.append("missing_citation_refs_for_claimed_facts")
    if not limitations_ok:
        blocked.append("missing_limitation_notes")
    if not seo_ok:
        blocked.append("missing_seo_metadata")
    if not checklist_ok:
        blocked.append("missing_manual_publish_checklist")
    if not no_live:
        blocked.append("no_live_defaults_failed")
    normalized = tuple(dict.fromkeys(blocked))
    material_blockers = tuple(reason for reason in normalized if reason not in {
        "no_substack_public_publish_api_gate",
        "session_automation_blocked",
        "live_gate_closed",
        "approval_required",
        "dispatch_revalidation_not_built",
    })
    status = BLOCKED if material_blockers or not all((
        source_match,
        payload_allowed,
        markdown_present,
        citations_ok,
        limitations_ok,
        no_signal,
        seo_ok,
        checklist_ok,
        no_live,
    )) else READY_FOR_MANUAL_REVIEW
    validation_id = "substack_validation_" + _digest({
        "issue_id": issue.issue_id,
        "export_package_id": package.export_package_id,
        "status": status,
        "blocked": normalized,
    })[:24]
    return SubstackExportValidationResult(
        validation_id=validation_id,
        issue_id=issue.issue_id,
        export_package_id=package.export_package_id,
        source_preview_hash_match=source_match,
        payload_class_allowed=payload_allowed,
        markdown_export_present=markdown_present,
        citations_present_when_required=citations_ok,
        limitations_present=limitations_ok,
        no_signal_pass=no_signal,
        no_advice_pass=no_signal,
        seo_metadata_present=seo_ok,
        manual_checklist_present=checklist_ok,
        no_live_defaults_pass=no_live,
        validation_status=status,
        blocked_reasons=normalized,
        evidence_refs=tuple(dict.fromkeys((*issue.evidence_refs, *package.evidence_refs))),
    )


def _sample_seo() -> dict[str, Any]:
    return {
        "seo_title": "Why content limits matter before market commentary",
        "seo_description": "A local-only Capital Chronicle process note about citations, limits, and no-signal framing.",
        "seo_keywords": ("content operations", "source trust", "market context"),
        "slug_suggestion": "content-limits-before-market-commentary",
    }


def _sample_preview(payload_class_id: str) -> previews.PlatformPayloadPreview:
    builder = previews.BUILDER_BY_PAYLOAD_CLASS[payload_class_id]
    return builder(
        source_content_id="source_content_0174U3_demo",
        source_draft_id="source_draft_0174U3_demo",
        title="Why limits come before distribution",
        subtitle="A ContentOps process note",
        body="Citations and limitations remain visible before any manual export.",
        markdown_body="Citations and limitations remain visible before any manual export.",
        citation_refs=("source:0174U0",),
        limitation_notes=("local manual export only; not public-ready",),
        content_lane="grounded_news_context",
    )


def build_contract_packet() -> dict[str, Any]:
    preview = _sample_preview(NEWSLETTER_PAYLOAD_CLASS)
    issue = build_substack_newsletter_issue_from_preview(
        preview,
        hook="Manual export stays controlled.",
        thesis_or_question="What must remain visible before a newsletter leaves the local system?",
        body_sections=("Every export preserves citations, limitations, and the no-signal disclaimer.",),
        seo_metadata=_sample_seo(),
        source_claims_exist=True,
    )
    package = build_manual_export_package(issue)
    validation = validate_substack_export_package(issue, package, source_preview=preview, source_claims_exist=True)
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "registry_checksum": registry.registry_checksum(),
        "preview_contract_checksum": previews.preview_contract_checksum(),
        "issue_fields": list(SubstackNewsletterIssue.__dataclass_fields__),
        "export_package_fields": list(SubstackManualExportPackage.__dataclass_fields__),
        "validation_fields": list(SubstackExportValidationResult.__dataclass_fields__),
        "export_hash_input_fields": list(EXPORT_HASH_INPUT_FIELDS),
        "manual_publish_checklist": list(MANUAL_PUBLISH_CHECKLIST),
        "safety_false_flags": list(SAFETY_FALSE_FLAGS),
        "sample_issue": asdict(issue),
        "sample_export_package": asdict(package),
        "sample_validation": asdict(validation),
        "artifact_scope": "docs/automation/0174U3_only",
        "next_heavy_batch_recommendation": NEXT_HEAVY_BATCH,
    }
    packet["substack_manual_export_contract_checksum"] = _digest(packet)
    return packet


def substack_manual_export_contract_checksum() -> str:
    return build_contract_packet()["substack_manual_export_contract_checksum"]


def _assert_safe_output(repo_root: str | Path, output_dir: str | Path | None) -> Path:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174U3")
    return out


def render_runbook(packet: dict[str, Any]) -> str:
    lines = [
        "# 0174U3 Substack Newsletter Manual Export Contract",
        "",
        f"- task_label: `{packet['task_label']}`",
        f"- model_version: `{packet['model_version']}`",
        f"- source_baseline_commit: `{packet['source_baseline_commit']}`",
        f"- registry_checksum: `{packet['registry_checksum']}`",
        f"- preview_contract_checksum: `{packet['preview_contract_checksum']}`",
        f"- substack_manual_export_contract_checksum: `{packet['substack_manual_export_contract_checksum']}`",
        f"- next_heavy_batch_recommendation: `{packet['next_heavy_batch_recommendation']}`",
        "",
        "## Scope",
        "",
        "Manual markdown export only. No Substack API, browser session, cookie, credential hydration, env read, network, scheduler, scraping, DM, or live dispatch behavior.",
        "",
        "## Models",
        "",
        "- `SubstackNewsletterIssue`: source preview, issue content, citations, limitations, SEO, export hash, no-live defaults.",
        "- `SubstackManualExportPackage`: markdown body/hash, SEO fields, manual checklist, symbolic destination/credential refs.",
        "- `SubstackExportValidationResult`: source hash match, payload allow-list, markdown/citation/limitation/SEO/checklist/no-live gates.",
        "",
        "## Hash rules",
        "",
        "Export hash includes source hash, title/subtitle/hook/thesis, body sections, citations, limitations, SEO, cross-platform refs, destination binding, and manual export status.",
        "Markdown hash is SHA-256 over rendered markdown.",
        "",
        "## Manual publish checklist",
        "",
    ]
    for item in packet["manual_publish_checklist"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Safety flags forced false",
        "",
    ])
    for flag in packet["safety_false_flags"]:
        lines.append(f"- `{flag}=false`")
    lines.extend([
        "",
        "## Scope confirmations",
        "",
        "- No UI/dashboard work.",
        "- No ingestion repo mutation.",
        "- No live/API/credential/provider/session/browser/scheduler/scraping/DM behavior.",
        "- Artifact writer is locked to `docs/automation/0174U3`.",
    ])
    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    (out / PACKET_FILENAME).write_text(_json(packet), encoding="utf-8", newline="\n")
    (out / RUNBOOK_FILENAME).write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return packet
