"""Content idea packet and local intent parser contract for ContentOps 0174U4.

Deterministic local-only parser. No LLM provider, live dispatch, network,
platform API, credential/env, scheduler, scraping, DM, or ingestion mutation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from live_contentops import platform_universe_registry_v2 as registry
from live_contentops import primary_platform_payload_preview_contracts as previews
from live_contentops import substack_newsletter_manual_export_contract as substack

TASK_LABEL = "TASK_CONTENTOPS_0174U4_CONTENT_IDEA_PACKET_AND_LOCAL_INTENT_PARSER_CONTRACT_V0"
MODEL = "contentops.content_idea_intent_parser_contract"
MODEL_VERSION = "0174U4_CONTENT_IDEA_INTENT_PARSER_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "c6da4ece3068c3726b8491e0ccfeabe8cf5a3a89"
DOC_REL_DIR = Path("docs") / "automation" / "0174U4"
PACKET_FILENAME = "content_idea_intent_parser_contract_packet.json"
RUNBOOK_FILENAME = "content_idea_intent_parser_contract.md"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174U5_EDITORIAL_BRIEF_AND_AI_WRITER_OUTPUT_CONTRACT_V0"
PARSER_MODE = "deterministic_local_only"
PARSER_VERSION = MODEL_VERSION

SOURCE_CHANNEL_CLASSES = (
    "local_ui",
    "telegram_remote_operator_inbox",
    "manual_import",
    "future_ingestion_context",
)
CONTENT_LANES = (
    "pre_alpha_general_process",
    "grounded_news_context",
    "future_artifact_backed",
    "unknown_or_blocked",
)
SOURCE_REQUIREMENT_STATUSES = (
    "not_required_for_process",
    "source_needed",
    "source_provided_context_only",
    "artifact_required_future_gate",
    "blocked_missing_source",
)
CLAIM_RISK_CLASSES = (
    "process_claim_low_risk",
    "source_context_claim",
    "market_context_claim_review_required",
    "artifact_backed_claim_requires_packet",
    "forecast_adjacent_claim_high_risk",
    "advice_or_signal_forbidden",
)
INTENT_CLASSES = (
    "create_content_from_idea",
    "revise_draft",
    "request_platform_preview",
    "request_substack_export",
    "approval_like_text_requires_challenge",
    "reject_or_hold",
    "status_query",
    "manual_metric_note",
    "source_note",
    "unknown",
)
CONFIDENCE_CLASSES = ("deterministic_exact", "deterministic_inferred", "ambiguous", "blocked")
READINESS_STATES = ("idea_ready_for_review", "source_needed", "artifact_gate_blocked", "blocked", "clarification_required")
VALIDATION_READY = "intent_valid_for_local_review"
VALIDATION_BLOCKED = "blocked"

SAFETY_FALSE_FLAGS = (
    "llm_provider_called", "platform_api_called", "telegram_api_called", "provider_api_called",
    "credential_hydrated", "env_read", "network_performed", "scheduler_enabled",
    "autonomous_posting_allowed", "scraping_performed", "dm_or_reply_automation_allowed",
    "live_dispatch_enabled", "dispatch_ready", "public_postable", "ingestion_repo_mutated",
)

PLATFORM_ALIASES = {
    "x": "x", "twitter": "x", "tweet": "x",
    "telegram": "telegram_channel_destination", "telegram channel": "telegram_channel_destination",
    "telegram destination": "telegram_channel_destination", "telegram remote": "telegram_remote_operator",
    "telegram operator": "telegram_remote_operator", "operator inbox": "telegram_remote_operator",
    "remote operator": "telegram_remote_operator", "substack": "substack_newsletter",
    "newsletter": "substack_newsletter", "linkedin": "linkedin", "threads": "threads",
    "instagram": "instagram", "facebook": "facebook_page", "facebook page": "facebook_page",
    "tiktok": "tiktok", "tik tok": "tiktok", "youtube": "youtube", "shorts": "youtube",
}
OUTPUT_SHAPE_BY_HINT = {
    "thread": ("x_thread",), "tweet": ("x_short_post",), "post": (),
    "newsletter": ("substack_newsletter_issue",), "longform": ("substack_longform_post",),
    "substack": ("substack_newsletter_issue",), "carousel": ("instagram_carousel_script",),
    "caption": ("instagram_caption_asset_packet",), "video": ("tiktok_video_metadata_packet", "youtube_video_metadata_packet"),
}
PROCESS_TERMS = ("process", "build", "source trust", "data sufficiency", "trust before forecast", "limits", "limitations")
NEWS_TERMS = ("news", "headline", "cpi", "payrolls", "fed", "inflation", "macro", "market", "markets")
ARTIFACT_TERMS = ("artifact", "dqr", "readiness", "internal alpha", "internal-alpha", "report", "forecast readiness")
APPROVAL_TERMS = ("approve", "approved", "approval", "greenlight", "go ahead", "ship it")
DISPATCH_TERMS = ("publish", "send", "post now", "auto post", "schedule", "dispatch", "send now")
MANUAL_METRIC_TERMS = ("manual metric", "metric note", "metrics note", "record metric", "manual metrics")
STATUS_QUERY_TERMS = ("status", "what is state", "where are we", "progress", "queue status")
SOURCE_NOTE_TERMS = ("source note", "citation", "source:", "official source", "context only")
REVISION_TERMS = ("revise", "rewrite", "edit draft", "tighten", "change draft")
REJECT_TERMS = ("reject", "hold", "pause", "block this", "do not use")
FORBIDDEN_SIGNAL_TERMS = previews.FORBIDDEN_SIGNAL_TERMS + (
    "financial advice", "long", "short", "watch this level", "model predicts",
    "recommendation to buy", "recommendation to sell",
)
UNSUPPORTED_PLATFORM_TERMS = ("reddit", "discord", "mastodon", "bluesky", "snapchat", "pinterest")
REDACTION_PATTERNS = (
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b(?:\+?\d[\d .-]{7,}\d)\b"),
    re.compile(r"\b(?:token|api[_-]?key|secret|password)\s*[:=]\s*\S+", re.IGNORECASE),
)

@dataclass(frozen=True)
class RawOperatorInput:
    raw_input_id: str
    source_channel_class: str
    received_at_epoch: int
    operator_identity_ref: str
    raw_text_redacted: str
    raw_text_hash: str
    attachment_manifest_hash: str
    source_context_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]

@dataclass(frozen=True)
class ContentIdeaPacket:
    idea_id: str
    source_raw_input_id: str
    source_channel_class: str
    created_at_epoch: int
    operator_identity_ref: str
    original_text_hash: str
    topic_summary: str
    requested_platforms: tuple[str, ...]
    content_lane: str
    source_requirement_status: str
    claim_risk_class: str
    market_sensitivity: str
    audience_mode: str
    tone_mode: str
    requested_output_shapes: tuple[str, ...]
    source_context_refs: tuple[str, ...]
    citation_refs: tuple[str, ...]
    limitation_notes: tuple[str, ...]
    no_financial_advice: bool
    no_signal_language: bool
    artifact_backed_claims_allowed: bool
    human_review_required: bool
    public_postable: bool
    readiness_state: str
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
@dataclass(frozen=True)
class LocalIntentPacket:
    intent_id: str
    source_raw_input_id: str
    source_idea_id: str
    parser_mode: str
    parser_version: str
    intent_class: str
    confidence_class: str
    extracted_platform_targets: tuple[str, ...]
    extracted_content_lane: str
    extracted_topic: str
    extracted_audience_mode: str
    extracted_tone_mode: str
    extracted_constraints: tuple[str, ...]
    extracted_forbidden_risk_flags: tuple[str, ...]
    requires_clarification: bool
    clarification_question: str
    can_create_content_idea: bool
    can_create_editorial_brief_candidate: bool
    can_create_approval: bool
    can_dispatch: bool
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]

@dataclass(frozen=True)
class IntentValidationResult:
    validation_id: str
    source_intent_id: str
    idea_id: str
    parser_mode_allowed: bool
    platform_targets_known: bool
    content_lane_known: bool
    source_requirements_satisfied_for_current_stage: bool
    forbidden_language_clear: bool
    approval_bypass_blocked: bool
    dispatch_bypass_blocked: bool
    public_postable_false: bool
    no_live_defaults_pass: bool
    validation_status: str
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]

class ContentIdeaIntentParserError(ValueError):
    """Base content idea/intent parser contract error."""

class UnsupportedSourceChannelClassError(ContentIdeaIntentParserError):
    """Raised when raw operator input source channel is unknown."""

def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

def _digest(data: Any) -> str:
    return sha256(_json(data).encode("utf-8")).hexdigest()

def _text_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()

def _safe_tuple(values: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    return tuple(values or ())

def _safety_flags() -> dict[str, bool]:
    return {flag: False for flag in SAFETY_FALSE_FLAGS} | {"deterministic_local_only": True}

def _redact(text: str) -> str:
    redacted = text
    for pattern in REDACTION_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted

def _normalize(text: str) -> str:
    return " ".join(text.lower().replace("no-signal", "nosignal").split())

def _tokens(text: str) -> tuple[str, ...]:
    return tuple("".join(ch if ch.isalnum() else " " for ch in _normalize(text)).split())

def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    norm = _normalize(text)
    token_set = set(_tokens(text))
    for phrase in phrases:
        if " " in phrase or "-" in phrase or ":" in phrase:
            if phrase in norm:
                return True
        elif phrase in token_set:
            return True
    return False
def _dedupe(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))

def _contains_forbidden_language(text: str) -> bool:
    return _contains_any(text, FORBIDDEN_SIGNAL_TERMS)

def _alias_present(norm: str, tokens: set[str], alias: str) -> bool:
    if " " in alias:
        return alias in norm
    return alias in tokens


def extract_platform_targets(text: str) -> tuple[str, ...]:
    norm = _normalize(text)
    token_set = set(_tokens(text))
    found: list[str] = []
    for alias, platform_id in sorted(PLATFORM_ALIASES.items(), key=lambda item: -len(item[0])):
        if _alias_present(norm, token_set, alias):
            if platform_id == "telegram_channel_destination" and any(
                marker in norm for marker in ("telegram remote", "telegram operator", "operator inbox", "remote operator")
            ):
                continue
            found.append(platform_id)
    return _dedupe(found)

def extract_unsupported_platforms(text: str) -> tuple[str, ...]:
    norm = _normalize(text)
    return tuple(term for term in UNSUPPORTED_PLATFORM_TERMS if term in norm)

def extract_output_shapes(text: str, platforms: tuple[str, ...]) -> tuple[str, ...]:
    norm = _normalize(text)
    shapes: list[str] = []
    for hint, mapped in OUTPUT_SHAPE_BY_HINT.items():
        if hint in norm:
            shapes.extend(mapped)
    if "x" in platforms and "thread" in norm:
        shapes.append("x_thread")
    if "x" in platforms and not any(shape.startswith("x_") for shape in shapes):
        shapes.append("x_short_post")
    if "substack_newsletter" in platforms and not any(shape.startswith("substack_") for shape in shapes):
        shapes.append("substack_newsletter_issue")
    if "telegram_channel_destination" in platforms:
        shapes.append("telegram_channel_update")
    if "telegram_remote_operator" in platforms:
        shapes.append("telegram_operator_review_message")
    if "linkedin" in platforms:
        shapes.append("linkedin_professional_post")
    if "threads" in platforms:
        shapes.append("threads_short_post")
    if "facebook_page" in platforms:
        shapes.append("facebook_page_post")
    if "instagram" in platforms and not any(shape.startswith("instagram_") for shape in shapes):
        shapes.append("instagram_caption_asset_packet")
    if "tiktok" in platforms:
        shapes.append("tiktok_video_metadata_packet")
    if "youtube" in platforms:
        shapes.append("youtube_video_metadata_packet")
    return _dedupe(shapes)

def classify_lane(text: str) -> tuple[str, str, str, str, list[str]]:
    blocked: list[str] = []
    if _contains_forbidden_language(text):
        blocked.append("forbidden_signal_or_advice_language")
        return "unknown_or_blocked", "blocked_missing_source", "advice_or_signal_forbidden", "high", blocked
    if _contains_any(text, ARTIFACT_TERMS):
        blocked.append("artifact_required_future_gate")
        return "future_artifact_backed", "artifact_required_future_gate", "artifact_backed_claim_requires_packet", "medium", blocked
    if _contains_any(text, NEWS_TERMS):
        return "grounded_news_context", "source_needed", "market_context_claim_review_required", "medium", blocked
    if _contains_any(text, PROCESS_TERMS) or text.strip():
        return "pre_alpha_general_process", "not_required_for_process", "process_claim_low_risk", "low", blocked
    blocked.append("empty_or_unknown_input")
    return "unknown_or_blocked", "blocked_missing_source", "source_context_claim", "unknown", blocked

def _topic_summary(text: str) -> str:
    redacted = _redact(text).strip()
    for prefix in ("Idea:", "idea:", "Draft:", "draft:", "Note:", "note:"):
        if redacted.startswith(prefix):
            redacted = redacted[len(prefix):].strip()
    return redacted[:180] or "Unknown operator intent"
def _audience_mode(text: str) -> str:
    norm = _normalize(text)
    if "operator" in norm or "internal" in norm:
        return "operator_internal"
    if "professional" in norm or "linkedin" in norm:
        return "professional_credibility"
    if "public" in norm or "audience" in norm:
        return "public_educational"
    return "general_operator_review"

def _tone_mode(text: str) -> str:
    norm = _normalize(text)
    if "sharp" in norm:
        return "sharp_credible"
    if "calm" in norm:
        return "calm_explanatory"
    if "professional" in norm:
        return "professional"
    return "credible_plainspoken"

def build_raw_operator_input(
    raw_text: str,
    *,
    source_channel_class: str = "local_ui",
    received_at_epoch: int = 0,
    operator_identity_ref: str = "operator_identity_ref_local",
    attachment_manifest_hash: str = "",
    source_context_refs: tuple[str, ...] | list[str] | None = None,
    evidence_refs: tuple[str, ...] | list[str] | None = None,
) -> RawOperatorInput:
    if source_channel_class not in SOURCE_CHANNEL_CLASSES:
        raise UnsupportedSourceChannelClassError(f"unsupported_source_channel_class:{source_channel_class}")
    redacted = _redact(raw_text)
    blocked: list[str] = []
    if source_channel_class == "future_ingestion_context":
        blocked.append("future_ingestion_context_schema_placeholder_only")
    material = {
        "source_channel_class": source_channel_class,
        "received_at_epoch": received_at_epoch,
        "operator_identity_ref": operator_identity_ref,
        "raw_text_hash": _text_hash(raw_text),
        "attachment_manifest_hash": attachment_manifest_hash,
        "source_context_refs": _safe_tuple(source_context_refs),
    }
    return RawOperatorInput(
        raw_input_id="raw_input_" + _digest(material)[:24],
        source_channel_class=source_channel_class,
        received_at_epoch=received_at_epoch,
        operator_identity_ref=operator_identity_ref,
        raw_text_redacted=redacted,
        raw_text_hash=_text_hash(raw_text),
        attachment_manifest_hash=attachment_manifest_hash,
        source_context_refs=_safe_tuple(source_context_refs),
        evidence_refs=_safe_tuple(evidence_refs) or ("docs/automation/0174U4/content_idea_intent_parser_contract.md",),
        safety_flags=_safety_flags(),
        blocked_reasons=tuple(blocked),
    )

def build_content_idea_packet(
    raw: RawOperatorInput,
    *,
    citation_refs: tuple[str, ...] | list[str] | None = None,
    limitation_notes: tuple[str, ...] | list[str] | None = None,
) -> ContentIdeaPacket:
    text = raw.raw_text_redacted
    platforms = extract_platform_targets(text)
    unsupported = extract_unsupported_platforms(text)
    shapes = extract_output_shapes(text, platforms)
    lane, source_status, risk, sensitivity, blocked = classify_lane(text)
    blocked.extend(raw.blocked_reasons)
    blocked.extend(f"unknown_platform_target:{term}" for term in unsupported)
    if source_status == "artifact_required_future_gate":
        blocked.append("artifact_backed_claims_not_allowed_until_future_gate")
    if not text.strip() or (not platforms and lane == "unknown_or_blocked"):
        blocked.append("clarification_required")
    readiness = "idea_ready_for_review"
    if source_status == "source_needed":
        readiness = "source_needed"
    if source_status == "artifact_required_future_gate":
        readiness = "artifact_gate_blocked"
    if any(reason.startswith("unknown_platform_target") for reason in blocked) or risk == "advice_or_signal_forbidden":
        readiness = "blocked"
    citations = _safe_tuple(citation_refs)
    limitations = _safe_tuple(limitation_notes)
    material = {
        "raw_input_id": raw.raw_input_id,
        "text_hash": raw.raw_text_hash,
        "platforms": platforms,
        "lane": lane,
        "source_status": source_status,
        "risk": risk,
    }
    return ContentIdeaPacket(
        idea_id="idea_" + _digest(material)[:24],
        source_raw_input_id=raw.raw_input_id,
        source_channel_class=raw.source_channel_class,
        created_at_epoch=raw.received_at_epoch,
        operator_identity_ref=raw.operator_identity_ref,
        original_text_hash=raw.raw_text_hash,
        topic_summary=_topic_summary(text),
        requested_platforms=platforms,
        content_lane=lane,
        source_requirement_status=source_status,
        claim_risk_class=risk,
        market_sensitivity=sensitivity,
        audience_mode=_audience_mode(text),
        tone_mode=_tone_mode(text),
        requested_output_shapes=shapes,
        source_context_refs=raw.source_context_refs,
        citation_refs=citations,
        limitation_notes=limitations,
        no_financial_advice=risk != "advice_or_signal_forbidden",
        no_signal_language=risk != "advice_or_signal_forbidden",
        artifact_backed_claims_allowed=False,
        human_review_required=True,
        public_postable=False,
        readiness_state=readiness,
        blocked_reasons=_dedupe(blocked),
        evidence_refs=_dedupe((*raw.evidence_refs, "docs/automation/0174U4/content_idea_intent_parser_contract.md")),
        safety_flags=_safety_flags(),
    )

def _intent_class(text: str, idea: ContentIdeaPacket) -> tuple[str, str, list[str]]:
    blocked: list[str] = []
    if idea.claim_risk_class == "advice_or_signal_forbidden":
        return "unknown", "blocked", ["forbidden_signal_or_advice_language"]
    if _contains_any(text, APPROVAL_TERMS):
        return "approval_like_text_requires_challenge", "blocked", ["approval_like_text_requires_challenge"]
    if _contains_any(text, MANUAL_METRIC_TERMS):
        return "manual_metric_note", "deterministic_exact", blocked
    if _contains_any(text, STATUS_QUERY_TERMS) and not _contains_any(text, PROCESS_TERMS + NEWS_TERMS + ARTIFACT_TERMS):
        return "status_query", "deterministic_exact", blocked
    if _contains_any(text, SOURCE_NOTE_TERMS):
        return "source_note", "deterministic_exact", blocked
    if _contains_any(text, REJECT_TERMS):
        return "reject_or_hold", "deterministic_exact", blocked
    if _contains_any(text, REVISION_TERMS):
        return "revise_draft", "deterministic_inferred", blocked
    if "preview" in _normalize(text):
        return "request_platform_preview", "deterministic_inferred", blocked
    if "export" in _normalize(text) or "substack" in idea.requested_platforms:
        return "request_substack_export", "deterministic_inferred", blocked
    if idea.topic_summary and "clarification_required" not in idea.blocked_reasons:
        return "create_content_from_idea", "deterministic_inferred", blocked
    return "unknown", "ambiguous", ["clarification_required"]
def parse_local_intent(raw: RawOperatorInput, idea: ContentIdeaPacket | None = None) -> LocalIntentPacket:
    idea_packet = idea or build_content_idea_packet(raw)
    text = raw.raw_text_redacted
    intent_class, confidence, intent_blockers = _intent_class(text, idea_packet)
    blocked = list(idea_packet.blocked_reasons) + intent_blockers
    dispatch_requested = _contains_any(text, DISPATCH_TERMS)
    if dispatch_requested:
        blocked.append("dispatch_bypass_blocked")
    if intent_class == "approval_like_text_requires_challenge":
        blocked.append("approval_bypass_blocked")
    requires_clarification = confidence == "ambiguous" or "clarification_required" in blocked
    clarification = "Clarify desired topic, platform target, and source context before drafting." if requires_clarification else ""
    can_create = intent_class in {"create_content_from_idea", "request_platform_preview", "request_substack_export"}
    can_brief = can_create and idea_packet.claim_risk_class != "advice_or_signal_forbidden"
    can_approval = False
    can_dispatch = False
    material = {
        "raw_input_id": raw.raw_input_id,
        "idea_id": idea_packet.idea_id,
        "intent_class": intent_class,
        "blocked": _dedupe(blocked),
    }
    return LocalIntentPacket(
        intent_id="intent_" + _digest(material)[:24],
        source_raw_input_id=raw.raw_input_id,
        source_idea_id=idea_packet.idea_id,
        parser_mode=PARSER_MODE,
        parser_version=PARSER_VERSION,
        intent_class=intent_class,
        confidence_class=confidence if not blocked else ("blocked" if any("forbidden" in b or "bypass" in b for b in blocked) else confidence),
        extracted_platform_targets=idea_packet.requested_platforms,
        extracted_content_lane=idea_packet.content_lane,
        extracted_topic=idea_packet.topic_summary,
        extracted_audience_mode=idea_packet.audience_mode,
        extracted_tone_mode=idea_packet.tone_mode,
        extracted_constraints=idea_packet.limitation_notes,
        extracted_forbidden_risk_flags=tuple(reason for reason in _dedupe(blocked) if "forbidden" in reason or "bypass" in reason),
        requires_clarification=requires_clarification,
        clarification_question=clarification,
        can_create_content_idea=can_create,
        can_create_editorial_brief_candidate=can_brief and not requires_clarification,
        can_create_approval=can_approval,
        can_dispatch=can_dispatch,
        blocked_reasons=_dedupe(blocked),
        evidence_refs=idea_packet.evidence_refs,
        safety_flags=_safety_flags(),
    )

def validate_intent_packet(idea: ContentIdeaPacket, intent: LocalIntentPacket) -> IntentValidationResult:
    parser_ok = intent.parser_mode == PARSER_MODE
    platform_ok = all(platform in registry.PLATFORMS_BY_ID for platform in intent.extracted_platform_targets)
    lane_ok = idea.content_lane in CONTENT_LANES and idea.content_lane != "unknown_or_blocked"
    source_ok = idea.source_requirement_status in {"not_required_for_process", "source_needed", "source_provided_context_only"}
    forbidden_clear = idea.claim_risk_class != "advice_or_signal_forbidden" and not intent.extracted_forbidden_risk_flags
    approval_blocked = intent.can_create_approval is False
    dispatch_blocked = intent.can_dispatch is False
    public_false = idea.public_postable is False and intent.safety_flags.get("public_postable") is False
    no_live = all(intent.safety_flags.get(flag) is False for flag in SAFETY_FALSE_FLAGS) and all(
        idea.safety_flags.get(flag) is False for flag in SAFETY_FALSE_FLAGS
    )
    blocked = list(idea.blocked_reasons) + list(intent.blocked_reasons)
    if not parser_ok:
        blocked.append("parser_mode_not_allowed")
    if not platform_ok:
        blocked.append("unknown_platform_target")
    if not lane_ok:
        blocked.append("content_lane_unknown_or_blocked")
    if not source_ok:
        blocked.append("source_requirement_not_satisfied_for_current_stage")
    if not forbidden_clear:
        blocked.append("forbidden_language_not_clear")
    if intent.can_create_approval:
        blocked.append("approval_bypass_not_blocked")
    if intent.can_dispatch:
        blocked.append("dispatch_bypass_not_blocked")
    if not public_false:
        blocked.append("public_postable_must_remain_false")
    if not no_live:
        blocked.append("no_live_defaults_failed")
    status = VALIDATION_READY if not blocked or set(blocked) <= {"source_needed"} else VALIDATION_BLOCKED
    material = {
        "intent_id": intent.intent_id,
        "idea_id": idea.idea_id,
        "checks": [parser_ok, platform_ok, lane_ok, source_ok, forbidden_clear, approval_blocked, dispatch_blocked, public_false, no_live],
        "blocked": _dedupe(blocked),
    }
    return IntentValidationResult(
        validation_id="intent_validation_" + _digest(material)[:24],
        source_intent_id=intent.intent_id,
        idea_id=idea.idea_id,
        parser_mode_allowed=parser_ok,
        platform_targets_known=platform_ok,
        content_lane_known=lane_ok,
        source_requirements_satisfied_for_current_stage=source_ok,
        forbidden_language_clear=forbidden_clear,
        approval_bypass_blocked=approval_blocked,
        dispatch_bypass_blocked=dispatch_blocked,
        public_postable_false=public_false,
        no_live_defaults_pass=no_live,
        validation_status=status,
        blocked_reasons=_dedupe(blocked),
        evidence_refs=idea.evidence_refs,
    )

def _asdict(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    return obj

def _checksum_or_none(fn: Any) -> str:
    try:
        return fn()
    except Exception:
        return "unavailable"

def build_contract_packet() -> dict[str, Any]:
    raw = build_raw_operator_input(
        "Idea: create a Substack newsletter and X thread about source trust before CPI commentary.",
        source_channel_class="local_ui",
        source_context_refs=("source:0174U0",),
        evidence_refs=(
            "docs/automation/0174U0/heavy_strategy_recon_report.md",
            "docs/automation/0174U4/content_idea_intent_parser_contract.md",
        ),
    )
    idea = build_content_idea_packet(raw, limitation_notes=("source context required before public claims",))
    intent = parse_local_intent(raw, idea)
    validation = validate_intent_packet(idea, intent)
    packet = {
        "task_label": TASK_LABEL,
        "model": MODEL,
        "model_version": MODEL_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "artifact_scope": "docs/automation/0174U4_only",
        "parser_mode": PARSER_MODE,
        "source_channel_classes": SOURCE_CHANNEL_CLASSES,
        "content_lanes": CONTENT_LANES,
        "source_requirement_statuses": SOURCE_REQUIREMENT_STATUSES,
        "claim_risk_classes": CLAIM_RISK_CLASSES,
        "intent_classes": INTENT_CLASSES,
        "confidence_classes": CONFIDENCE_CLASSES,
        "readiness_states": READINESS_STATES,
        "platform_aliases": PLATFORM_ALIASES,
        "safety_false_flags": SAFETY_FALSE_FLAGS,
        "registry_checksum": _checksum_or_none(registry.registry_checksum),
        "preview_contract_checksum": _checksum_or_none(getattr(previews, "preview_contract_checksum", lambda: "unavailable")),
        "substack_manual_export_contract_checksum": _checksum_or_none(getattr(substack, "substack_manual_export_contract_checksum", lambda: "unavailable")),
        "raw_operator_input_fields": tuple(RawOperatorInput.__dataclass_fields__),
        "content_idea_packet_fields": tuple(ContentIdeaPacket.__dataclass_fields__),
        "local_intent_packet_fields": tuple(LocalIntentPacket.__dataclass_fields__),
        "intent_validation_fields": tuple(IntentValidationResult.__dataclass_fields__),
        "sample_raw_input": _asdict(raw),
        "sample_idea_packet": _asdict(idea),
        "sample_intent_packet": _asdict(intent),
        "sample_validation": _asdict(validation),
        "parser_rules": {
            "local_only": True,
            "llm_provider_allowed": False,
            "platform_api_allowed": False,
            "credential_or_env_read_allowed": False,
            "ingestion_repo_mutation_allowed": False,
            "telegram_default_role": "telegram_channel_destination_unless_operator_or_inbox_terms_present",
            "approval_text_requires_challenge": True,
            "dispatch_text_never_dispatches": True,
            "unknown_platforms_fail_closed": True,
        },
        "next_heavy_batch_recommendation": NEXT_HEAVY_BATCH,
    }
    return packet

def _runbook_markdown(packet: dict[str, Any]) -> str:
    return "\n".join((
        "# 0174U4 Content Idea Packet and Local Intent Parser Contract",
        "",
        f"Task: `{TASK_LABEL}`",
        f"Model: `{MODEL_VERSION}`",
        "",
        "## Scope",
        "",
        "Deterministic local-only parser for operator text. It creates review-only",
        "ContentIdeaPacket and LocalIntentPacket records. It never calls LLM providers,",
        "platform APIs, Telegram APIs, credentials, env, schedulers, scraping, DM flows,",
        "or ingestion repo mutation paths.",
        "",
        "## Core contract",
        "",
        "- raw operator input is redacted and hash-bound;",
        "- platform targets map to registry-known IDs;",
        "- text lanes map to process, grounded-news, or future-artifact gates;",
        "- approval-like text requires challenge;",
        "- dispatch-like text is blocked;",
        "- public postable and dispatch-ready remain false;",
        "- human review remains required.",
        "",
        "## Sample IDs",
        "",
        f"- raw input: `{packet['sample_raw_input']['raw_input_id']}`",
        f"- idea: `{packet['sample_idea_packet']['idea_id']}`",
        f"- intent: `{packet['sample_intent_packet']['intent_id']}`",
        f"- validation: `{packet['sample_validation']['validation_id']}`",
        "",
        "## Safety flags",
        "",
        "All live/provider/platform/credential/scheduler/scraping/dispatch flags stay false.",
        "",
        "## Next heavy batch",
        "",
        f"`{NEXT_HEAVY_BATCH}`",
        "",
    ))

def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> tuple[Path, Path]:
    root = Path(repo_root)
    target = Path(output_dir) if output_dir is not None else root / DOC_REL_DIR
    target.mkdir(parents=True, exist_ok=True)
    if target.resolve() != (root / DOC_REL_DIR).resolve():
        raise ContentIdeaIntentParserError("artifact_output_must_be_docs_automation_0174U4")
    packet = build_contract_packet()
    packet_path = target / PACKET_FILENAME
    runbook_path = target / RUNBOOK_FILENAME
    packet_path.write_text(_json(packet), encoding="utf-8")
    runbook_path.write_text(_runbook_markdown(packet), encoding="utf-8")
    return packet_path, runbook_path

__all__ = [
    "RawOperatorInput", "ContentIdeaPacket", "LocalIntentPacket", "IntentValidationResult",
    "build_raw_operator_input", "build_content_idea_packet", "parse_local_intent",
    "validate_intent_packet", "build_contract_packet", "write_artifacts",
]
