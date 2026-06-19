"""Idea-to-multi-platform draft dry-run contract for ContentOps 0174U6.

Local deterministic orchestrator. No provider, platform API, network,
credential, env, scheduler, scraping, DM, dispatch, approval, or ingestion mutation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops import content_idea_intent_parser_contract as ideas
from live_contentops import editorial_brief_ai_writer_output_contract as writer
from live_contentops import primary_platform_payload_preview_contracts as previews
from live_contentops import substack_newsletter_manual_export_contract as substack

TASK_LABEL = "TASK_CONTENTOPS_0174U6_IDEA_TO_MULTI_PLATFORM_DRAFT_DRY_RUN_CONTRACT_V0"
MODEL_VERSION = "0174U6_IDEA_TO_MULTI_PLATFORM_DRAFT_DRY_RUN_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "54d1ae970dcf6e023d04744e74c5ec71b5540830"
DOC_REL_DIR = Path("docs") / "automation" / "0174U6"
PACKET_FILENAME = "idea_to_multi_platform_draft_dry_run_contract_packet.json"
RUNBOOK_FILENAME = "idea_to_multi_platform_draft_dry_run_contract.md"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174U7_CAPITAL_CHRONICLE_INGESTION_HEADLINE_IDEA_CONNECTOR_PRECHECK_V0"
SAFETY_FALSE_FLAGS = ("llm_provider_called", "provider_api_called", "platform_api_called", "telegram_api_called", "credential_hydrated", "env_read", "network_performed", "scheduler_enabled", "autonomous_posting_allowed", "scraping_performed", "dm_or_reply_automation_allowed", "live_dispatch_enabled", "approval_granted", "dispatch_ready", "public_postable", "ingestion_repo_mutated")
EXPECTED_DRY_RUN_BLOCKERS = ("live_gate_closed", "approval_required", "dispatch_revalidation_not_built", "x_api_gate_closed", "credential_gate_closed", "no_substack_public_publish_api_gate", "session_automation_blocked", "linkedin_oauth_gate_closed", "permission_review_closed", "meta_app_review_closed", "instagram_content_publish_gate_closed", "media_url_gate_closed", "pages_manage_posts_gate_closed", "video_future_gate", "video_future_gate_closed", "tiktok_audit_closed", "youtube_oauth_gate_closed", "telegram_api_gate_closed", "bot_admin_gate_closed", "review_control_only_not_public_channel")


@dataclass(frozen=True)
class MultiPlatformPreviewBundle:
    bundle_id: str; source_writer_output_id: str; previews: tuple[previews.PlatformPayloadPreview, ...]; preview_validations: tuple[previews.PayloadPreviewValidationResult, ...]; payload_hashes: tuple[str, ...]; bundle_hash: str; dispatch_ready: bool; public_postable: bool; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class DryRunReviewPacket:
    review_packet_id: str; source_idea_id: str; source_brief_id: str; source_writer_output_id: str; source_bundle_id: str; substack_export_package_ids: tuple[str, ...]; citation_refs: tuple[str, ...]; limitation_notes: tuple[str, ...]; review_status: str; approval_ready: bool; dispatch_ready: bool; public_postable: bool; safety_flags: dict[str, bool]; blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class DryRunValidationResult:
    validation_id: str; dry_run_id: str; review_only_pass: bool; writer_valid: bool; previews_valid: bool; substack_exports_valid: bool; no_live_defaults_pass: bool; validation_status: str; blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class MultiPlatformDraftDryRunPacket:
    dry_run_id: str; raw_input: ideas.RawOperatorInput; idea_packet: ideas.ContentIdeaPacket; intent_packet: ideas.LocalIntentPacket; editorial_brief: writer.EditorialBrief; writer_output: writer.AIWriterOutputPacket; preview_bundle: MultiPlatformPreviewBundle; substack_exports: tuple[substack.SubstackManualExportPackage, ...]; review_packet: DryRunReviewPacket; validation: DryRunValidationResult; dry_run_hash: str; safety_flags: dict[str, bool]


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _digest(data: Any) -> str:
    return sha256(_json(data).encode("utf-8")).hexdigest()


def _asdict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, tuple):
        return [_asdict(v) for v in value]
    if isinstance(value, dict):
        return {k: _asdict(v) for k, v in value.items()}
    return value


def _safety_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFETY_FALSE_FLAGS} | {"deterministic_local_dry_run_only": True}


def _dedupe(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _hard_blockers(values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    return tuple(reason for reason in _dedupe(values) if reason not in EXPECTED_DRY_RUN_BLOCKERS)


def _preview_from_draft(draft: writer.DraftVariant, brief: writer.EditorialBrief) -> previews.PlatformPayloadPreview:
    body = draft.body.replace(writer.NO_ADVICE_DISCLAIMER, "").replace(writer.NO_SIGNAL_DISCLAIMER, "")
    return previews.build_platform_payload_preview(source_content_id=brief.source_idea_id, source_draft_id=draft.draft_variant_id, platform_id=draft.platform_id, payload_class_id=draft.payload_class_id, content_lane=brief.content_lane, title=draft.title, subtitle=draft.subtitle, body=body, thread_parts=draft.thread_parts, markdown_body=draft.markdown_body.replace(writer.NO_ADVICE_DISCLAIMER, "").replace(writer.NO_SIGNAL_DISCLAIMER, ""), media_manifest_id="symbolic_media_manifest_review_only", citation_refs=draft.citation_refs, limitation_notes=draft.limitation_notes, source_claims_exist=bool(draft.citation_refs))


def build_preview_bundle(brief: writer.EditorialBrief, out: writer.AIWriterOutputPacket) -> MultiPlatformPreviewBundle:
    built = tuple(_preview_from_draft(d, brief) for d in out.draft_variants)
    validations = tuple(previews.validate_platform_payload_preview(p) for p in built)
    blockers = _hard_blockers([r for p in built for r in p.blocked_reasons] + [r for v in validations for r in v.blocked_reasons])
    material = {"writer_output_id": out.writer_output_id, "hashes": [p.payload_hash for p in built], "blockers": blockers}
    h = _digest(material)
    return MultiPlatformPreviewBundle("preview_bundle_" + h[:24], out.writer_output_id, built, validations, tuple(p.payload_hash for p in built), h, False, False, _safety_flags(), blockers)


def build_substack_exports(bundle: MultiPlatformPreviewBundle, out: writer.AIWriterOutputPacket) -> tuple[substack.SubstackManualExportPackage, ...]:
    exports = []
    for p in bundle.previews:
        if p.platform_id == "substack_newsletter":
            issue = substack.build_substack_issue_from_preview(p, issue_type="newsletter_issue", title=p.title, subtitle=p.subtitle, hook=out.hook_candidates[0] if out.hook_candidates else "", thesis_or_question="Review-only editorial dry run", seo_metadata={"seo_title": out.seo_title, "seo_description": out.seo_description, "seo_keywords": out.seo_keywords, "slug_suggestion": "review-only-dry-run"}, cross_platform_derivative_refs=bundle.payload_hashes, source_claims_exist=bool(p.citation_refs))
            exports.append(substack.build_manual_export_package(issue, tags=("review-only", "0174U6")))
    return tuple(exports)


def _review(idea: ideas.ContentIdeaPacket, brief: writer.EditorialBrief, out: writer.AIWriterOutputPacket, bundle: MultiPlatformPreviewBundle, exports: tuple[substack.SubstackManualExportPackage, ...]) -> DryRunReviewPacket:
    blockers = _hard_blockers(list(brief.blocked_reasons) + list(out.blocked_reasons) + list(bundle.blocked_reasons) + [r for e in exports for r in e.blocked_reasons])
    h = _digest({"idea": idea.idea_id, "brief": brief.brief_id, "writer": out.writer_output_id, "bundle": bundle.bundle_id, "blockers": blockers})
    return DryRunReviewPacket("dry_run_review_" + h[:24], idea.idea_id, brief.brief_id, out.writer_output_id, bundle.bundle_id, tuple(e.export_package_id for e in exports), out.citation_refs_used, out.limitation_notes_preserved, "blocked" if blockers else "review_only_ready", False, False, False, _safety_flags(), blockers)


def validate_dry_run(packet: MultiPlatformDraftDryRunPacket) -> DryRunValidationResult:
    blockers = list(packet.review_packet.blocked_reasons)
    writer_valid = not packet.writer_output.blocked_reasons
    previews_valid = all(not _hard_blockers(v.blocked_reasons) for v in packet.preview_bundle.preview_validations)
    exports_valid = all(not _hard_blockers(e.blocked_reasons) for e in packet.substack_exports)
    review_only = not (packet.writer_output.public_postable or packet.writer_output.approval_ready or packet.writer_output.dispatch_ready or packet.preview_bundle.public_postable or packet.preview_bundle.dispatch_ready or packet.review_packet.public_postable or packet.review_packet.approval_ready or packet.review_packet.dispatch_ready)
    no_live = all(packet.safety_flags.get(flag) is False for flag in SAFETY_FALSE_FLAGS)
    if not writer_valid: blockers.append("writer_output_blocked")
    if not previews_valid: blockers.append("preview_bundle_blocked")
    if not exports_valid: blockers.append("substack_export_blocked")
    if not review_only: blockers.append("review_only_invariant_failed")
    if not no_live: blockers.append("no_live_defaults_failed")
    blocked = _dedupe(blockers)
    status = "review_only_dry_run_valid" if not blocked else "blocked"
    h = _digest({"dry_run_id": packet.dry_run_id, "status": status, "blockers": blocked})
    return DryRunValidationResult("dry_run_validation_" + h[:24], packet.dry_run_id, review_only, writer_valid, previews_valid, exports_valid, no_live, status, blocked)


def build_dry_run_from_text(text: str, *, writer_mode: str = "deterministic_fixture", external_title: str = "Manual pasted title", external_body: str = "") -> MultiPlatformDraftDryRunPacket:
    raw = ideas.build_raw_operator_input(text)
    idea = ideas.build_content_idea_packet(raw)
    intent = ideas.parse_local_intent(raw, idea)
    brief = writer.build_editorial_brief(idea, intent)
    if writer_mode == "manual_external_llm_paste":
        body = external_body or f"{brief.topic_summary}\n\n{writer.NO_ADVICE_DISCLAIMER} {writer.NO_SIGNAL_DISCLAIMER}"
        out = writer.build_manual_external_llm_paste_packet(brief, title_candidates=(external_title,), hook_candidates=("Review-only pasted hook",), seo_keywords=(brief.content_lane,), seo_title=external_title[:70], seo_description="Review-only manual paste dry run", platform_fit_notes={p: f"registry_fit:{p}" for p in brief.target_platforms}, draft_bodies={p: body for p in brief.target_platforms})
    elif writer_mode == "deterministic_fixture":
        out = writer.build_deterministic_fixture_writer_output(brief)
    else:
        out = writer.build_provider_future_gate_blocked_packet(brief)
    bundle = build_preview_bundle(brief, out)
    exports = build_substack_exports(bundle, out)
    review = _review(idea, brief, out, bundle, exports)
    h = _digest({"idea": idea.idea_id, "brief": brief.brief_id, "writer": out.output_hash, "bundle": bundle.bundle_hash, "exports": [e.export_package_id for e in exports]})
    draft = MultiPlatformDraftDryRunPacket("dry_run_" + h[:24], raw, idea, intent, brief, out, bundle, exports, review, DryRunValidationResult("pending", "pending", False, False, False, False, False, "pending", ()), h, _safety_flags())
    validation = validate_dry_run(draft)
    return MultiPlatformDraftDryRunPacket(draft.dry_run_id, raw, idea, intent, brief, out, bundle, exports, review, validation, h, _safety_flags())


def build_contract_packet() -> dict[str, Any]:
    sample = build_dry_run_from_text("Draft an X thread and Substack newsletter about source trust during manual review. Limitation: review-only local dry run.")
    packet = {"task_label": TASK_LABEL, "model_version": MODEL_VERSION, "source_baseline_commit": SOURCE_BASELINE_COMMIT, "sample_dry_run": _asdict(sample), "safety_false_flags": list(SAFETY_FALSE_FLAGS), "artifact_scope": "docs/automation/0174U6_only", "next_heavy_batch_recommendation": NEXT_HEAVY_BATCH}
    packet["dry_run_contract_checksum"] = _digest(packet)
    return packet


def render_runbook(packet: dict[str, Any]) -> str:
    return "\n".join(["# 0174U6 Idea-to-Multi-Platform Draft Dry Run Contract", "", f"- task_label: `{packet['task_label']}`", f"- model_version: `{packet['model_version']}`", f"- source_baseline_commit: `{packet['source_baseline_commit']}`", f"- dry_run_contract_checksum: `{packet['dry_run_contract_checksum']}`", f"- next_heavy_batch_recommendation: `{packet['next_heavy_batch_recommendation']}`", "", "## Scope confirmations", "", "- Review-only dry run; no approvals and no dispatch.", "- No provider/platform API, network, env, credential, scheduler, scraping, DM, or ingestion mutation.", "- Artifact writer is locked to `docs/automation/0174U6`."]) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve(); allowed = (root / DOC_REL_DIR).resolve(); out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed: raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174U6")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    (out / PACKET_FILENAME).write_text(_json(packet), encoding="utf-8", newline="\n")
    (out / RUNBOOK_FILENAME).write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return packet
