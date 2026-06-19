"""Editorial brief and AI writer output contract for ContentOps 0174U5.

Deterministic local-only contract. No provider LLM, live dispatch, network,
platform API, Telegram API, credential/env, scheduler, scraping, DM, approval,
or ingestion mutation behavior.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops import content_idea_intent_parser_contract as intent_contract
from live_contentops import platform_universe_registry_v2 as registry
from live_contentops import primary_platform_payload_preview_contracts as previews

TASK_LABEL = "TASK_CONTENTOPS_0174U5_EDITORIAL_BRIEF_AND_AI_WRITER_OUTPUT_CONTRACT_V0"
MODEL = "contentops.editorial_brief_ai_writer_output_contract"
MODEL_VERSION = "0174U5_EDITORIAL_BRIEF_AI_WRITER_OUTPUT_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "16065fa1953975c4261a923e7467ac3464b09848"
DOC_REL_DIR = Path("docs") / "automation" / "0174U5"
PACKET_FILENAME = "editorial_brief_ai_writer_output_contract_packet.json"
RUNBOOK_FILENAME = "editorial_brief_ai_writer_output_contract.md"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174U6_IDEA_TO_MULTI_PLATFORM_DRAFT_DRY_RUN_CONTRACT_V0"
OUTPUT_HASH_ALGORITHM = "sha256"

WRITER_MODES = (
    "deterministic_fixture",
    "manual_external_llm_paste",
    "provider_future_gate_blocked",
)
ALLOWED_WRITER_MODES = ("deterministic_fixture", "manual_external_llm_paste")
REVIEW_ONLY = "review_only"
VALIDATION_READY = "writer_output_valid_for_local_review"
VALIDATION_BLOCKED = "blocked"
NO_SIGNAL_DISCLAIMER = "Not a trading signal. No buy/sell/hold or price target instruction is provided."
NO_ADVICE_DISCLAIMER = "Educational context only. Not financial advice."

SAFETY_FALSE_FLAGS = (
    "llm_provider_called", "provider_api_called", "platform_api_called", "telegram_api_called",
    "credential_hydrated", "env_read", "network_performed", "scheduler_enabled",
    "autonomous_posting_allowed", "scraping_performed", "dm_or_reply_automation_allowed",
    "live_dispatch_enabled", "dispatch_ready", "public_postable", "approval_granted",
    "ingestion_repo_mutated",
)
FORBIDDEN_CLAIM_TERMS = previews.FORBIDDEN_SIGNAL_TERMS + (
    "financial advice", "long", "short", "model predicts", "recommendation to buy",
    "recommendation to sell", "watch this level",
)


@dataclass(frozen=True)
class EditorialBrief:
    brief_id: str
    source_idea_id: str
    source_intent_id: str
    source_raw_input_id: str
    content_lane: str
    topic_summary: str
    target_platforms: tuple[str, ...]
    target_payload_classes: tuple[str, ...]
    audience_mode: str
    tone_mode: str
    source_requirement_status: str
    claim_risk_class: str
    required_citation_refs: tuple[str, ...]
    required_limitation_notes: tuple[str, ...]
    required_disclaimers: tuple[str, ...]
    forbidden_claims: tuple[str, ...]
    required_no_advice: bool
    required_no_signal: bool
    artifact_backed_allowed: bool
    output_status: str
    human_review_required: bool
    public_postable: bool
    dispatch_ready: bool
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class DraftVariant:
    draft_variant_id: str
    source_writer_output_id: str
    platform_id: str
    payload_class_id: str
    title: str
    subtitle: str
    body: str
    thread_parts: tuple[str, ...]
    markdown_body: str
    citation_refs: tuple[str, ...]
    limitation_notes: tuple[str, ...]
    no_signal_disclaimer: str
    no_advice_disclaimer: str
    platform_fit_status: str
    citation_status: str
    limitation_status: str
    no_signal_status: str
    no_advice_status: str
    review_status: str
    public_postable: bool
    approval_ready: bool
    dispatch_ready: bool
    draft_hash: str
    evidence_refs: tuple[str, ...]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class AIWriterOutputPacket:
    writer_output_id: str
    source_brief_id: str
    writer_mode: str
    title_candidates: tuple[str, ...]
    hook_candidates: tuple[str, ...]
    seo_keywords: tuple[str, ...]
    seo_title: str
    seo_description: str
    platform_fit_notes: dict[str, str]
    draft_variants: tuple[DraftVariant, ...]
    citation_refs_used: tuple[str, ...]
    limitation_notes_preserved: tuple[str, ...]
    disclaimers_preserved: tuple[str, ...]
    forbidden_claims_detected: tuple[str, ...]
    source_hallucination_risk: bool
    public_postable: bool
    approval_ready: bool
    dispatch_ready: bool
    human_review_required: bool
    output_hash: str
    output_hash_algorithm: str
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class AIWriterOutputValidationResult:
    validation_id: str
    source_brief_id: str
    writer_output_id: str
    writer_mode_allowed: bool
    citations_preserved: bool
    limitations_preserved: bool
    disclaimers_preserved: bool
    no_hallucinated_sources: bool
    no_forbidden_claims: bool
    no_signal_pass: bool
    no_advice_pass: bool
    all_drafts_review_only: bool
    approval_not_granted: bool
    dispatch_not_allowed: bool
    public_postable_false: bool
    no_provider_defaults_pass: bool
    validation_status: str
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]


class EditorialBriefAIWriterContractError(ValueError):
    """Base 0174U5 contract error."""


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _digest(data: Any) -> str:
    return sha256(_json(data).encode("utf-8")).hexdigest()


def _safe_tuple(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    return tuple(values or ())


def _safety_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFETY_FALSE_FLAGS} | {"deterministic_local_only": True}


def _asdict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, tuple):
        return [_asdict(item) for item in value]
    if isinstance(value, list):
        return [_asdict(item) for item in value]
    if isinstance(value, dict):
        return {key: _asdict(val) for key, val in value.items()}
    return value


def _dedupe(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _normalize(text: str) -> str:
    return " ".join(text.lower().replace("no-signal", "nosignal").split())


def _tokens(text: str) -> tuple[str, ...]:
    return tuple("".join(ch if ch.isalnum() else " " for ch in _normalize(text)).split())


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    norm = _normalize(text)
    token_set = set(_tokens(text))
    for phrase in phrases:
        phrase_norm = _normalize(phrase)
        if " " in phrase_norm or "-" in phrase_norm:
            if phrase_norm in norm:
                return True
        elif phrase_norm in token_set:
            return True
    return False


def _claim_scan_text(*parts: str) -> str:
    text = "\n".join(part for part in parts if part)
    text = text.replace(NO_ADVICE_DISCLAIMER, "").replace(NO_SIGNAL_DISCLAIMER, "")
    for safe_phrase in ("not a signal", "not trading signal", "not a trading signal"):
        text = text.replace(safe_phrase, "")
    return text


def _detected_forbidden_claims(*parts: str) -> tuple[str, ...]:
    text = _claim_scan_text(*parts)
    return tuple(term for term in FORBIDDEN_CLAIM_TERMS if _contains_any(text, (term,)))


def _platform_payload_pairs(idea: intent_contract.ContentIdeaPacket) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    shapes = idea.requested_output_shapes
    for platform_id in idea.requested_platforms:
        platform = registry.lookup_platform(platform_id)
        shape = next((payload for payload in shapes if payload in platform.payload_classes_supported), "")
        if not shape:
            shape = platform.payload_classes_supported[0]
        pairs.append((platform_id, shape))
    if not pairs:
        pairs.append(("x", "x_short_post"))
    return tuple(pairs)


def _required_citations(idea: intent_contract.ContentIdeaPacket) -> tuple[str, ...]:
    return _safe_tuple(idea.citation_refs)


def _required_limitations(idea: intent_contract.ContentIdeaPacket) -> tuple[str, ...]:
    limitations = list(_safe_tuple(idea.limitation_notes))
    if idea.source_requirement_status == "source_needed" and not limitations:
        limitations.append("source context required before public claims")
    if idea.content_lane == "future_artifact_backed" and not limitations:
        limitations.append("artifact packet required before artifact-backed claims")
    return _dedupe(limitations)


def _brief_blockers(
    idea: intent_contract.ContentIdeaPacket,
    intent: intent_contract.LocalIntentPacket,
) -> tuple[str, ...]:
    blocked = list(idea.blocked_reasons) + list(intent.blocked_reasons)
    if intent.source_idea_id != idea.idea_id:
        blocked.append("intent_idea_mismatch")
    if intent.source_raw_input_id != idea.source_raw_input_id:
        blocked.append("intent_raw_input_mismatch")
    if intent.intent_class in {"approval_like_text_requires_challenge", "unknown"}:
        blocked.append("intent_class_not_allowed_for_editorial_brief")
    if "dispatch_bypass_blocked" in intent.blocked_reasons:
        blocked.append("dispatch_like_intent_not_allowed_for_editorial_brief")
    if idea.claim_risk_class == "advice_or_signal_forbidden":
        blocked.append("advice_or_signal_forbidden_blocks_editorial_brief")
    if idea.source_requirement_status == "artifact_required_future_gate":
        blocked.append("artifact_gate_blocks_editorial_brief")
    if intent.can_create_editorial_brief_candidate is False:
        blocked.append("intent_not_valid_for_editorial_brief_candidate")
    return _dedupe(blocked)


def build_editorial_brief(
    idea: intent_contract.ContentIdeaPacket,
    intent: intent_contract.LocalIntentPacket,
) -> EditorialBrief:
    pairs = _platform_payload_pairs(idea)
    blocked = _brief_blockers(idea, intent)
    citations = _required_citations(idea)
    limitations = _required_limitations(idea)
    material = {
        "idea_id": idea.idea_id,
        "intent_id": intent.intent_id,
        "raw_input_id": idea.source_raw_input_id,
        "platform_payload_pairs": pairs,
        "blocked": blocked,
    }
    return EditorialBrief(
        brief_id="brief_" + _digest(material)[:24],
        source_idea_id=idea.idea_id,
        source_intent_id=intent.intent_id,
        source_raw_input_id=idea.source_raw_input_id,
        content_lane=idea.content_lane,
        topic_summary=idea.topic_summary,
        target_platforms=tuple(platform for platform, _ in pairs),
        target_payload_classes=tuple(payload for _, payload in pairs),
        audience_mode=idea.audience_mode,
        tone_mode=idea.tone_mode,
        source_requirement_status=idea.source_requirement_status,
        claim_risk_class=idea.claim_risk_class,
        required_citation_refs=citations,
        required_limitation_notes=limitations,
        required_disclaimers=(NO_ADVICE_DISCLAIMER, NO_SIGNAL_DISCLAIMER),
        forbidden_claims=FORBIDDEN_CLAIM_TERMS,
        required_no_advice=True,
        required_no_signal=True,
        artifact_backed_allowed=False,
        output_status=REVIEW_ONLY,
        human_review_required=True,
        public_postable=False,
        dispatch_ready=False,
        evidence_refs=_dedupe((*idea.evidence_refs, *intent.evidence_refs, f"{DOC_REL_DIR.as_posix()}/{RUNBOOK_FILENAME}")),
        safety_flags=_safety_flags(),
        blocked_reasons=blocked,
    )


def _draft_hash_material(draft: dict[str, Any]) -> str:
    return _digest(draft)


def _draft_body(brief: EditorialBrief, platform_id: str) -> str:
    source_note = ""
    if brief.required_citation_refs:
        source_note = " Sources: " + ", ".join(brief.required_citation_refs) + "."
    limitation = ""
    if brief.required_limitation_notes:
        limitation = " Limitations: " + "; ".join(brief.required_limitation_notes) + "."
    return (
        f"{brief.topic_summary}\n\n"
        f"Audience: {brief.audience_mode}. Tone: {brief.tone_mode}. "
        f"Platform: {platform_id}.{source_note}{limitation}\n\n"
        f"{NO_ADVICE_DISCLAIMER} {NO_SIGNAL_DISCLAIMER}"
    )


def _make_draft_variant(
    brief: EditorialBrief,
    writer_output_id: str,
    platform_id: str,
    payload_class_id: str,
    title: str,
    hook: str,
    body: str,
) -> DraftVariant:
    thread_parts = (hook, body[:260]) if payload_class_id.endswith("thread") else ()
    markdown_body = body if payload_class_id.startswith("substack_") else ""
    blocked: list[str] = []
    if not registry.validate_payload_class_compatibility(platform_id, payload_class_id)["compatible"]:
        blocked.append("payload_class_not_supported_by_platform")
    material = {
        "brief_id": brief.brief_id,
        "writer_output_id": writer_output_id,
        "platform_id": platform_id,
        "payload_class_id": payload_class_id,
        "title": title,
        "hook": hook,
        "body": body,
        "citation_refs": brief.required_citation_refs,
        "limitations": brief.required_limitation_notes,
    }
    return DraftVariant(
        draft_variant_id="draft_variant_" + _digest(material)[:24],
        source_writer_output_id=writer_output_id,
        platform_id=platform_id,
        payload_class_id=payload_class_id,
        title=title,
        subtitle="Review-only draft candidate",
        body=body,
        thread_parts=thread_parts,
        markdown_body=markdown_body,
        citation_refs=brief.required_citation_refs,
        limitation_notes=brief.required_limitation_notes,
        no_signal_disclaimer=NO_SIGNAL_DISCLAIMER,
        no_advice_disclaimer=NO_ADVICE_DISCLAIMER,
        platform_fit_status="registry_payload_compatible" if not blocked else "blocked",
        citation_status="citations_preserved",
        limitation_status="limitations_preserved",
        no_signal_status="no_signal_disclaimer_preserved",
        no_advice_status="no_advice_disclaimer_preserved",
        review_status=REVIEW_ONLY,
        public_postable=False,
        approval_ready=False,
        dispatch_ready=False,
        draft_hash=_draft_hash_material(material),
        evidence_refs=brief.evidence_refs,
        blocked_reasons=tuple(blocked),
    )


def _build_writer_packet(
    brief: EditorialBrief,
    *,
    writer_mode: str,
    title_candidates: tuple[str, ...],
    hook_candidates: tuple[str, ...],
    seo_keywords: tuple[str, ...],
    seo_title: str,
    seo_description: str,
    platform_fit_notes: dict[str, str],
    draft_inputs: tuple[tuple[str, str, str, str], ...],
) -> AIWriterOutputPacket:
    material_base = {"brief_id": brief.brief_id, "writer_mode": writer_mode, "titles": title_candidates}
    writer_output_id = "writer_output_" + _digest(material_base)[:24]
    drafts = tuple(
        _make_draft_variant(brief, writer_output_id, platform_id, payload_class_id, title, hook_candidates[0] if hook_candidates else "", body)
        for platform_id, payload_class_id, title, body in draft_inputs
    )
    text_parts = list(title_candidates) + list(hook_candidates) + [seo_title, seo_description]
    text_parts.extend(draft.body for draft in drafts)
    detected = _detected_forbidden_claims(*text_parts)
    blocked: list[str] = list(brief.blocked_reasons)
    if writer_mode not in ALLOWED_WRITER_MODES:
        blocked.append("writer_mode_provider_future_gate_blocked")
    if detected:
        blocked.append("forbidden_claim_language_detected")
    if brief.required_citation_refs and not set(brief.required_citation_refs).issubset({ref for d in drafts for ref in d.citation_refs}):
        blocked.append("required_citations_missing")
    if brief.required_limitation_notes and not set(brief.required_limitation_notes).issubset({n for d in drafts for n in d.limitation_notes}):
        blocked.append("required_limitations_missing")
    all_citations = tuple(ref for draft in drafts for ref in draft.citation_refs)
    hallucinated = any(ref not in brief.required_citation_refs for ref in all_citations)
    if hallucinated:
        blocked.append("hallucinated_source_ref_detected")
    if any(draft.blocked_reasons for draft in drafts):
        blocked.append("draft_variant_blocked")
    packet_material = {
        "writer_output_id": writer_output_id,
        "brief_id": brief.brief_id,
        "writer_mode": writer_mode,
        "title_candidates": title_candidates,
        "hook_candidates": hook_candidates,
        "seo_keywords": seo_keywords,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "platform_fit_notes": platform_fit_notes,
        "drafts": [_asdict(draft) for draft in drafts],
    }
    return AIWriterOutputPacket(
        writer_output_id=writer_output_id,
        source_brief_id=brief.brief_id,
        writer_mode=writer_mode,
        title_candidates=title_candidates,
        hook_candidates=hook_candidates,
        seo_keywords=seo_keywords,
        seo_title=seo_title,
        seo_description=seo_description,
        platform_fit_notes=platform_fit_notes,
        draft_variants=drafts,
        citation_refs_used=_dedupe(all_citations),
        limitation_notes_preserved=_dedupe(tuple(note for draft in drafts for note in draft.limitation_notes)),
        disclaimers_preserved=(NO_ADVICE_DISCLAIMER, NO_SIGNAL_DISCLAIMER),
        forbidden_claims_detected=detected,
        source_hallucination_risk=hallucinated,
        public_postable=False,
        approval_ready=False,
        dispatch_ready=False,
        human_review_required=True,
        output_hash=_digest(packet_material),
        output_hash_algorithm=OUTPUT_HASH_ALGORITHM,
        evidence_refs=brief.evidence_refs,
        safety_flags=_safety_flags(),
        blocked_reasons=_dedupe(blocked),
    )


def build_deterministic_fixture_writer_output(brief: EditorialBrief) -> AIWriterOutputPacket:
    title = f"Review brief: {brief.topic_summary[:70]}".strip()
    hook = f"Why this matters: {brief.topic_summary[:120]}".strip()
    draft_inputs = tuple(
        (platform_id, payload_class_id, title, _draft_body(brief, platform_id))
        for platform_id, payload_class_id in zip(brief.target_platforms, brief.target_payload_classes)
    )
    return _build_writer_packet(
        brief,
        writer_mode="deterministic_fixture",
        title_candidates=(title, f"Source-aware note: {brief.content_lane}"),
        hook_candidates=(hook,),
        seo_keywords=("source trust", "editorial review", brief.content_lane),
        seo_title=title[:70],
        seo_description=f"Review-only draft candidate for {brief.topic_summary[:120]}",
        platform_fit_notes={platform: f"registry_fit:{platform}" for platform in brief.target_platforms},
        draft_inputs=draft_inputs,
    )


def build_manual_external_llm_paste_packet(
    brief: EditorialBrief,
    *,
    title_candidates: tuple[str, ...] | list[str],
    hook_candidates: tuple[str, ...] | list[str],
    seo_keywords: tuple[str, ...] | list[str],
    seo_title: str,
    seo_description: str,
    platform_fit_notes: dict[str, str],
    draft_bodies: dict[str, str],
) -> AIWriterOutputPacket:
    draft_inputs = tuple(
        (
            platform_id,
            payload_class_id,
            tuple(title_candidates)[0] if title_candidates else brief.topic_summary[:70],
            draft_bodies.get(platform_id, _draft_body(brief, platform_id)),
        )
        for platform_id, payload_class_id in zip(brief.target_platforms, brief.target_payload_classes)
    )
    return _build_writer_packet(
        brief,
        writer_mode="manual_external_llm_paste",
        title_candidates=_safe_tuple(title_candidates),
        hook_candidates=_safe_tuple(hook_candidates),
        seo_keywords=_safe_tuple(seo_keywords),
        seo_title=seo_title,
        seo_description=seo_description,
        platform_fit_notes=dict(platform_fit_notes),
        draft_inputs=draft_inputs,
    )


def build_provider_future_gate_blocked_packet(brief: EditorialBrief) -> AIWriterOutputPacket:
    return _build_writer_packet(
        brief,
        writer_mode="provider_future_gate_blocked",
        title_candidates=("Provider mode blocked",),
        hook_candidates=("Provider calls are not allowed in 0174U5.",),
        seo_keywords=("blocked",),
        seo_title="Provider mode blocked",
        seo_description="Future provider mode is gated and blocked.",
        platform_fit_notes={platform: f"registry_fit:{platform}" for platform in brief.target_platforms},
        draft_inputs=tuple(
            (platform, payload, "Provider mode blocked", _draft_body(brief, platform))
            for platform, payload in zip(brief.target_platforms, brief.target_payload_classes)
        ),
    )


def _platform_fit_known(packet: AIWriterOutputPacket) -> bool:
    return all(platform_id in registry.PLATFORMS_BY_ID for platform_id in packet.platform_fit_notes)


def _drafts_review_only(packet: AIWriterOutputPacket) -> bool:
    return all(
        draft.review_status == REVIEW_ONLY
        and draft.public_postable is False
        and draft.approval_ready is False
        and draft.dispatch_ready is False
        for draft in packet.draft_variants
    )


def _drafts_compatible(packet: AIWriterOutputPacket) -> bool:
    return all(
        registry.validate_payload_class_compatibility(draft.platform_id, draft.payload_class_id)["compatible"]
        for draft in packet.draft_variants
    )


def validate_ai_writer_output(
    brief: EditorialBrief,
    packet: AIWriterOutputPacket,
) -> AIWriterOutputValidationResult:
    mode_allowed = packet.writer_mode in ALLOWED_WRITER_MODES
    citations_preserved = set(brief.required_citation_refs).issubset(set(packet.citation_refs_used))
    limitations_preserved = set(brief.required_limitation_notes).issubset(set(packet.limitation_notes_preserved))
    disclaimers_preserved = set(brief.required_disclaimers).issubset(set(packet.disclaimers_preserved))
    no_hallucinated = packet.source_hallucination_risk is False and set(packet.citation_refs_used).issubset(set(brief.required_citation_refs))
    no_forbidden = not packet.forbidden_claims_detected
    text = "\n".join(
        list(packet.title_candidates)
        + list(packet.hook_candidates)
        + [packet.seo_title, packet.seo_description]
        + [draft.body for draft in packet.draft_variants]
    )
    scan_text = _claim_scan_text(text)
    no_signal = not _contains_any(scan_text, FORBIDDEN_CLAIM_TERMS)
    no_advice = "financial advice" not in _normalize(scan_text)
    drafts_review = _drafts_review_only(packet) and _drafts_compatible(packet) and _platform_fit_known(packet)
    approval_false = packet.approval_ready is False
    dispatch_false = packet.dispatch_ready is False
    public_false = packet.public_postable is False
    no_provider = all(packet.safety_flags.get(flag) is False for flag in SAFETY_FALSE_FLAGS)
    checks = {
        "writer_mode_not_allowed": mode_allowed,
        "required_citations_missing": citations_preserved,
        "required_limitations_missing": limitations_preserved,
        "required_disclaimers_missing": disclaimers_preserved,
        "hallucinated_source_ref_detected": no_hallucinated,
        "forbidden_claim_language_detected": no_forbidden,
        "signal_language_detected": no_signal,
        "advice_language_detected": no_advice,
        "drafts_not_review_only": drafts_review,
        "approval_ready_true": approval_false,
        "dispatch_ready_true": dispatch_false,
        "public_postable_true": public_false,
        "no_provider_defaults_failed": no_provider,
    }
    blocked = list(brief.blocked_reasons) + list(packet.blocked_reasons)
    blocked.extend(reason for reason, passed in checks.items() if not passed)
    status = VALIDATION_READY if not blocked else VALIDATION_BLOCKED
    material = {"brief_id": brief.brief_id, "writer_output_id": packet.writer_output_id, "checks": checks, "blocked": _dedupe(blocked)}
    return AIWriterOutputValidationResult(
        validation_id="writer_validation_" + _digest(material)[:24],
        source_brief_id=brief.brief_id,
        writer_output_id=packet.writer_output_id,
        writer_mode_allowed=mode_allowed,
        citations_preserved=citations_preserved,
        limitations_preserved=limitations_preserved,
        disclaimers_preserved=disclaimers_preserved,
        no_hallucinated_sources=no_hallucinated,
        no_forbidden_claims=no_forbidden,
        no_signal_pass=no_signal,
        no_advice_pass=no_advice,
        all_drafts_review_only=drafts_review,
        approval_not_granted=approval_false,
        dispatch_not_allowed=dispatch_false,
        public_postable_false=public_false,
        no_provider_defaults_pass=no_provider,
        validation_status=status,
        blocked_reasons=_dedupe(blocked),
        evidence_refs=brief.evidence_refs,
    )


def _sample_inputs() -> tuple[
    intent_contract.RawOperatorInput,
    intent_contract.ContentIdeaPacket,
    intent_contract.LocalIntentPacket,
]:
    raw = intent_contract.build_raw_operator_input(
        "Idea: create a Substack newsletter and X thread about source trust before CPI commentary.",
        source_context_refs=("source:0174U0",),
        evidence_refs=("docs/automation/0174U0/heavy_strategy_recon_report.md",),
    )
    idea = intent_contract.build_content_idea_packet(
        raw,
        citation_refs=("source:0174U0",),
        limitation_notes=("source context required before public claims",),
    )
    intent = intent_contract.parse_local_intent(raw, idea)
    return raw, idea, intent


def build_contract_packet() -> dict[str, Any]:
    raw, idea, intent = _sample_inputs()
    brief = build_editorial_brief(idea, intent)
    output = build_deterministic_fixture_writer_output(brief)
    validation = validate_ai_writer_output(brief, output)
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "writer_modes": WRITER_MODES,
        "allowed_writer_modes": ALLOWED_WRITER_MODES,
        "review_only_status": REVIEW_ONLY,
        "safety_false_flags": SAFETY_FALSE_FLAGS,
        "editorial_brief_fields": tuple(EditorialBrief.__dataclass_fields__),
        "ai_writer_output_fields": tuple(AIWriterOutputPacket.__dataclass_fields__),
        "draft_variant_fields": tuple(DraftVariant.__dataclass_fields__),
        "validation_fields": tuple(AIWriterOutputValidationResult.__dataclass_fields__),
        "sample_raw_input": _asdict(raw),
        "sample_idea_packet": _asdict(idea),
        "sample_intent_packet": _asdict(intent),
        "sample_editorial_brief": _asdict(brief),
        "sample_ai_writer_output": _asdict(output),
        "sample_validation": _asdict(validation),
        "writer_rules": {
            "provider_llm_allowed": False,
            "manual_external_llm_paste_allowed": True,
            "deterministic_fixture_allowed": True,
            "approval_creation_allowed": False,
            "dispatch_allowed": False,
            "public_postable_allowed": False,
            "citations_must_be_preserved": True,
            "limitations_must_be_preserved": True,
            "no_advice_no_signal_disclaimers_required": True,
        },
        "registry_checksum": registry.registry_checksum(),
        "content_idea_intent_parser_model_version": intent_contract.MODEL_VERSION,
        "next_heavy_batch_recommendation": NEXT_HEAVY_BATCH,
        "artifact_scope": "docs/automation/0174U5_only",
    }
    packet["ai_writer_output_contract_checksum"] = _digest(packet)
    return packet


def render_runbook(packet: dict[str, Any]) -> str:
    lines = [
        "# 0174U5 Editorial Brief + AI Writer Output Contract",
        "",
        "Deterministic local-only review contract. No provider LLM call is made.",
        "",
        "## Safety Proof",
        "",
    ]
    for flag in SAFETY_FALSE_FLAGS:
        lines.append(f"- `{flag}`: `False`")
    lines.extend([
        "",
        "## Writer Modes",
        "",
        "- `deterministic_fixture`: allowed local fixture output.",
        "- `manual_external_llm_paste`: allowed paste-only external output validation.",
        "- `provider_future_gate_blocked`: blocked future provider mode.",
        "",
        "## Preservation Rules",
        "",
        "- Citation refs from the brief must be preserved exactly.",
        "- Limitation notes from the brief must be preserved exactly.",
        "- No-advice and no-signal disclaimers must remain present.",
        "- Draft variants remain review-only and not public-postable.",
        "",
        "## Evidence",
        "",
        f"- Contract checksum: `{packet['ai_writer_output_contract_checksum']}`",
        f"- Next heavy batch: `{NEXT_HEAVY_BATCH}`",
    ])
    return "\n".join(lines) + "\n"


def _assert_safe_output(repo_root: str | Path, output_dir: str | Path | None) -> Path:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise EditorialBriefAIWriterContractError("unsafe_output_path_refused")
    return out


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    out = _assert_safe_output(repo_root, output_dir)
    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    (out / PACKET_FILENAME).write_text(_json(_asdict(packet)), encoding="utf-8", newline="\n")
    (out / RUNBOOK_FILENAME).write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet}


if __name__ == "__main__":
    result = write_artifacts(".")
    print("AI_WRITER_OUTPUT_CONTRACT_CHECKSUM", result["packet"]["ai_writer_output_contract_checksum"])
