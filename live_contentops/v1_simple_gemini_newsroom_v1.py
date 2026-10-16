"""Simple Gemini-first V1 newsroom runtime.

This is the current low-complexity V1 editorial path. It deliberately does not run the
legacy evidence-ready candidate pool, Codex Desktop worker handoff, daily deficit catch-up
loop, or publication coordinator. One bounded Gemini selection chooses a useful current
headline, deterministic public retrieval (with bounded browser-rendered recovery after an
eligible exact-source failure) acquires only that story's source record, one
bounded Gemini writer produces a source-bound article, and deterministic validation checks
all cited material against the already-retrieved bytes. One bounded Gemini revision is the
only semantic retry.

The module never performs a public write. It persists one qualified zero-write article
record plus exactly eight undispatched derivative intents. The existing durable publication
coordinator remains the sole public-write owner in a separately authorized later phase.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlsplit

from live_contentops.browser_rendered_source_recovery_v1 import (
    BrowserOSNeoRenderedSourceRecovery,
)
from live_contentops.capital_chronicle_institutional_edge_v1 import (
    build_institutional_edge_editorial_packet,
    validate_institutional_edge_packet,
)
from live_contentops.credential_redaction_policy import redact_text
from live_contentops.destination_transport_registry_v1 import (
    REGISTRY_VERSION,
    V1_QUALITY_PROBATION_POLICY_ID,
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
    registration_for_destination,
)
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_glob
from live_contentops.llm_first_validate_after_v1 import ARTICLE_MODES
from live_contentops.newsroom_assignment_scheduler_v1 import (
    load_rolling_x_headline_sidecars,
)
from live_contentops.newsroom_production_day_v1 import (
    build_current_zero_write_qualified_article_record,
    newsroom_production_day_id,
    persist_qualified_article_record,
)
from live_contentops.preselection_intelligence_v1 import (
    rank_simple_headline_candidate_universe,
)
from live_contentops.public_secondary_evidence_loader_v1 import (
    REPUTABLE_SECONDARY_HOSTS,
)
from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_V1_SIMPLE_ARTICLE_WRITING,
    ROLE_V1_SIMPLE_EDITORIAL_REVISION,
    ROLE_V1_SIMPLE_SELECTION,
    routed_llm_invocation,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
    RetryBudget,
)
from live_contentops.v1_simple_evidence_resolver_v1 import (
    SimpleFirstPartyAwareEvidenceResolver,
)
from live_contentops.v1_simple_epistemic_state_v1 import (
    canonical_x_report_document,
    candidate_report_provenance,
    validate_epistemic_state,
)

SCHEMA_VERSION = "contentops.v1_simple_gemini_newsroom.v5"
SELECTION_SCHEMA_VERSION = "contentops.v1_simple_gemini_selection.v2"
ARTICLE_SCHEMA_VERSION = "contentops.v1_simple_gemini_article.v1"
VALIDATION_SCHEMA_VERSION = "contentops.v1_simple_gemini_validation.v1"
DERIVATIVE_INTENTS_SCHEMA_VERSION = "contentops.v1_simple_derivative_intents.v2"
NATIVE_PREVIEWS_SCHEMA_VERSION = "contentops.v1_simple_native_derivative_previews.v1"
PUBLICATION_BRIDGE_SCHEMA_VERSION = "contentops.v1_simple_publication_bridge.v1"

ORDERING = (
    "DETERMINISTIC_SOURCEABILITY_PRESELECTION_THEN_GEMINI_SELECT_THEN_"
    "PROVENANCE_AWARE_BOUNDED_HTTP_THEN_BROWSER_RENDERED_RECOVERY_THEN_"
    "EPISTEMIC_STATE_THEN_GEMINI_WRITE_THEN_DETERMINISTIC_VALIDATE"
)
MAX_SELECTION_CANDIDATES = 32
MAX_SOURCE_REQUESTS = 6
MAX_SOURCE_DOCUMENTS = 4
MAX_SOURCE_TEXT_CHARS = 12_000
MAX_LOGICAL_MODEL_INVOCATIONS = 3
MAX_PROVIDER_ATTEMPTS_PER_LOGICAL_INVOCATION = 1
MAX_REVISION_ROUNDS = 1
MAX_ADMITTED_CANDIDATES = 3

_SELECTION_STATUS_SELECT = "SELECT_CANDIDATE_PLAN"
_SELECTION_STATUS_ABSTAIN = "ABSTAIN"
_VALID_CLAIM_KINDS = frozenset({"FACT", "NUMBER", "QUOTE", "CAUSALITY"})
_PUBLIC_METADATA_FIELDS = (
    "title",
    "dek",
    "search_title",
    "meta_description",
    "social_hook",
)
_NEWS_PEG_TOPIC_GROUPS = (
    frozenset({"earnings", "results", "revenue", "margin", "quarter", "quarterly"}),
    frozenset({"financing", "capital", "mou", "mous", "platform", "platforms"}),
    frozenset({"pce", "inflation", "income", "outlays", "spending", "price"}),
    frozenset({"imf", "chile", "credit", "fcl", "arrangement"}),
)
_NEWS_PEG_STOPWORDS = frozenset({
    "about", "after", "amid", "and", "despite", "from", "future", "into", "more",
    "nvidia", "says", "than", "that", "the", "this", "through", "today", "with",
})
_RISKY_TEMPORAL_PATTERNS = (
    re.compile(r"\bannounc(?:ed|ement)\s+(?:came\s+)?alongside\b", re.IGNORECASE),
    re.compile(r"\bcame\s+alongside\b", re.IGNORECASE),
    re.compile(r"\btoday\s+announced\b", re.IGNORECASE),
    re.compile(r"\bnewly\s+announced\b", re.IGNORECASE),
    re.compile(
        r"\bnew\s+(?:deal|fund|initiative|partnership|platform|arrangement)\b",
        re.IGNORECASE,
    ),
)
_SOURCE_MARKER_RE = re.compile(r"\[\[SOURCE:(SOURCE_[1-4])\]\]")
_URL_RE = re.compile(r"https?://", re.IGNORECASE)
_EXPLICIT_CC_INFERENCE_RE = re.compile(
    r"\bCapital Chronicle(?:'s)?\s+(?:view|analysis|interpretation|inference)\b|"
    r"\bCapital Chronicle\s+(?:views|infers|interprets)\b",
    re.IGNORECASE,
)
_RESERVED_CC_NUMERIC_AUTHORITY_RE = re.compile(
    r"\bCapital Chronicle(?:'s)?\s+(?:forecast|probabilit(?:y|ies)|scenario|"
    r"regime|valuation|price target|base case)\b|"
    r"\bCapital Chronicle\s+(?:assigns|calculates|estimates|forecasts|projects)\b"
    r"[^.!?\n]{0,100}(?:\d+(?:\.\d+)?\s*%|\bprobabilit(?:y|ies)\b|"
    r"\bvaluation\b|\bprice target\b)",
    re.IGNORECASE,
)

_SIMPLE_MODE_BEHAVIOR = {
    "BREAKING_BRIEF": "fast useful implication after the supported event; never a headline rewrite",
    "FOLLOW_UP_UPDATE": "lead with the material supported delta; never recycle the prior story",
    "STANDARD_NEWS_ANALYSIS": "early thesis, mechanism, consequence, counter-case, and watch condition",
    "CAPITAL_CHRONICLE_VIEW": "explicit defensible Capital Chronicle qualitative house thesis",
    "WHAT_THE_MARKET_IS_MISSING": "strongest supported overlooked variable or consensus challenge",
    "EVERGREEN_EXPLAINER": "plain-English orientation followed by institutional depth",
    "DATA_OR_DOCUMENT_LENS": "surface a non-obvious supported source or document finding",
    "WEEK_AHEAD_OR_WATCH": "useful conditional watchpoints; never calendar filler",
}

LlmInvoke = Callable[..., tuple[dict[str, Any], dict[str, Any]]]
EvidenceLoader = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class SimpleGeminiNewsroomError(RuntimeError):
    """Fail-closed simple-runtime error with a stable code and safe details."""

    def __init__(
        self,
        code: str,
        details: Sequence[str] | None = None,
        *,
        diagnostics: Mapping[str, Any] | None = None,
    ) -> None:
        self.code = str(code)
        self.details = sorted({str(value) for value in details or [] if str(value)})
        self.diagnostics = dict(diagnostics or {})
        message = self.code + (":" + ";".join(self.details) if self.details else "")
        super().__init__(message)


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _text_hash(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def _normal(value: Any) -> str:
    return " ".join(str(value or "").split()).casefold()


def _iso_utc(value: Any) -> str:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise SimpleGeminiNewsroomError("timestamp_timezone_required")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    payload = json.dumps(dict(value), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != payload:
            raise SimpleGeminiNewsroomError(
                "immutable_runtime_artifact_identity_conflict", [path.name]
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _headline_text(row: Mapping[str, Any]) -> str:
    external = row.get("external_content")
    external = external if isinstance(external, Mapping) else {}
    return str(row.get("headline_text") or external.get("headline_text") or "").strip()


def _headline_url(row: Mapping[str, Any]) -> str:
    external = row.get("external_content")
    external = external if isinstance(external, Mapping) else {}
    return str(row.get("source_url") or external.get("url_or_source_ref") or "").strip()


def _headline_account(row: Mapping[str, Any]) -> str:
    external = row.get("external_content")
    external = external if isinstance(external, Mapping) else {}
    return str(row.get("source_account") or external.get("author_handle") or "").strip()


def _safe_https_locator(value: Any) -> str:
    url = str(value or "").strip()
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        return ""
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
    ):
        return ""
    return url


def _memory_field(row: Any, key: str) -> str:
    if isinstance(row, Mapping):
        return str(row.get(key) or "")
    return str(getattr(row, key, "") or "")


def _candidate_universe(
    rolling_input: Mapping[str, Any], published_memory: Sequence[Any]
) -> list[dict[str, Any]]:
    published_titles = {
        _normal(_memory_field(row, "title"))
        for row in published_memory
        if _normal(_memory_field(row, "title"))
    }
    published_story_ids = {
        _memory_field(row, "story_identity")
        for row in published_memory
        if _memory_field(row, "story_identity")
    }
    published_headline_ids = {
        _memory_field(row, "headline_id")
        for row in published_memory
        if _memory_field(row, "headline_id")
    }
    rows = [dict(row) for row in rolling_input.get("headlines") or [] if isinstance(row, Mapping)]
    rows.sort(
        key=lambda row: (
            str(row.get("source_timestamp_utc") or ""),
            str(row.get("headline_id") or ""),
        ),
        reverse=True,
    )
    seen_titles: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        headline_id = str(row.get("headline_id") or "").strip()
        text = _headline_text(row)
        normalized = _normal(text)
        if not headline_id or len(normalized) < 12:
            continue
        story_identity = "simple-story-" + _text_hash(normalized)[:24]
        if (
            headline_id in published_headline_ids
            or story_identity in published_story_ids
            or normalized in published_titles
            or normalized in seen_titles
        ):
            continue
        seen_titles.add(normalized)
        external = row.get("external_content")
        external = external if isinstance(external, Mapping) else {}
        source_url = _safe_https_locator(_headline_url(row))
        parsed_source = urlsplit(source_url)
        source_host = str(parsed_source.hostname or "").casefold()
        official_urls = list(
            dict.fromkeys(
                safe_url
                for value in (
                    list(row.get("official_source_urls") or [])
                    + list(external.get("official_source_urls") or [])
                )
                if (safe_url := _safe_https_locator(value))
            )
        )
        public_urls = list(official_urls)
        safe_source_url = _safe_https_locator(source_url)
        if (
            safe_source_url
            and parsed_source.scheme == "https"
            and source_host
            and source_host not in {"x.com", "www.x.com", "t.co", "www.t.co"}
            and safe_source_url not in public_urls
        ):
            public_urls.append(safe_source_url)
        result.append({
            "candidate_id": story_identity,
            "story_identity": story_identity,
            "headline_id": headline_id,
            "headline_text": text,
            "source_timestamp_utc": str(row.get("source_timestamp_utc") or ""),
            "source_account": _headline_account(row),
            "source_url": source_url,
            "official_source_urls": official_urls,
            "public_source_urls": public_urls,
            "follow_up_data_need_candidates": list(
                external.get("follow_up_data_need_candidates") or []
            ),
            "source_platform": str(external.get("source_platform") or ""),
            "canonical_x_list_provenance": dict(
                external.get("canonical_x_list_provenance") or {}
            )
            if isinstance(external.get("canonical_x_list_provenance"), Mapping)
            else {},
        })
    return result


def _selection_candidate(row: Mapping[str, Any]) -> dict[str, Any]:
    candidate = {
        key: row.get(key)
        for key in (
            "candidate_id",
            "story_identity",
            "headline_id",
            "headline_text",
            "source_timestamp_utc",
            "source_account",
            "source_url",
            "official_source_urls",
            "public_source_urls",
            "source_platform",
            "canonical_x_list_provenance",
        )
    }
    sourceability = row.get("sourceability_work_order")
    sourceability = sourceability if isinstance(sourceability, Mapping) else {}
    candidate["sourceability_route_hint"] = {
        "canonical_x_zero_get_route_available": bool(
            sourceability.get("canonical_x_zero_get_route_available")
        ),
        "known_official_path": bool(sourceability.get("known_official_path")),
        "reputable_public_secondary_path": bool(
            sourceability.get("reputable_public_secondary_path")
        ),
        "expected_route_request_cost_class": str(
            sourceability.get("expected_route_request_cost_class") or "UNKNOWN"
        ),
        "known_access_risk": bool(
            sourceability.get("known_paywall_waf_or_dead_link_risk")
        ),
        "routing_hint_grants_factual_or_publication_authority": False,
    }
    return candidate


def _candidate_packet_and_preselection(
    rolling_input: Mapping[str, Any],
    published_memory: Sequence[Any],
    *,
    source_route_health: Mapping[str, Any] | None = None,
    attempted_candidate_ids: Sequence[str] = (),
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    attempted = {str(value) for value in attempted_candidate_ids if str(value)}
    unfiltered_universe = _candidate_universe(rolling_input, published_memory)
    universe_candidate_ids = {
        str(row.get("candidate_id") or "") for row in unfiltered_universe
    }
    excluded = attempted.intersection(universe_candidate_ids)
    universe = [
        row
        for row in unfiltered_universe
        if str(row.get("candidate_id") or "") not in excluded
    ]
    ranked = rank_simple_headline_candidate_universe(
        universe,
        max_candidates=MAX_SELECTION_CANDIDATES,
        source_route_health=source_route_health,
    )
    candidates = [
        _selection_candidate(row)
        for row in ranked["ranked_candidates"][:MAX_SELECTION_CANDIDATES]
    ]
    evidence = dict(ranked["evidence"])
    evidence.update(
        {
            "full_eligible_deduped_universe_count": len(unfiltered_universe),
            "eligible_deduped_universe_count_after_same_day_retry_suppression": len(
                universe
            ),
            "same_production_day_source_blocked_candidate_exclusion_count": len(
                excluded
            ),
            "same_production_day_source_blocked_candidate_exclusion_sha256": _hash(
                sorted(excluded)
            ),
            "same_production_day_candidate_retry_suppression_grants_authority": False,
        }
    )
    return candidates, evidence


def _candidate_packet(
    rolling_input: Mapping[str, Any],
    published_memory: Sequence[Any],
    *,
    source_route_health: Mapping[str, Any] | None = None,
    attempted_candidate_ids: Sequence[str] = (),
) -> list[dict[str, Any]]:
    candidates, _evidence = _candidate_packet_and_preselection(
        rolling_input,
        published_memory,
        source_route_health=source_route_health,
        attempted_candidate_ids=attempted_candidate_ids,
    )
    return candidates


def _published_memory_summary(published_memory: Sequence[Any]) -> dict[str, Any]:
    titles = sorted(
        {_normal(_memory_field(row, "title")) for row in published_memory}
        - {""}
    )
    story_ids = sorted(
        {_memory_field(row, "story_identity") for row in published_memory}
        - {""}
    )
    update_chain_ids = sorted(
        {_memory_field(row, "update_chain_identity") for row in published_memory}
        - {""}
    )
    return {
        "article_count": len(published_memory),
        "unique_title_count": len(titles),
        "story_identity_count": len(story_ids),
        "update_chain_identity_count": len(update_chain_ids),
        "title_set_sha256": _hash(titles),
        "story_identity_set_sha256": _hash(story_ids),
        "update_chain_identity_set_sha256": _hash(update_chain_ids),
        "candidate_filtering_performed_before_model": True,
        "full_published_corpus_in_prompt": False,
    }


def _validate_selection_text(
    text: str, *, candidate_ids: set[str]
) -> tuple[bool, str | None, Any, str | None]:
    try:
        value = json.loads(str(text or ""))
    except json.JSONDecodeError:
        return False, "structured_output_malformed", None, "selection_json_invalid"
    if not isinstance(value, Mapping):
        return False, "structured_output_schema_invalid", None, "selection_object_required"
    required = {
        "schema_version",
        "status",
        "ordered_candidate_plan",
        "selection_summary",
        "public_write_attempted",
    }
    if set(value) != required:
        return False, "structured_output_schema_invalid", None, "selection_top_level_fields_invalid"
    if value.get("schema_version") != SELECTION_SCHEMA_VERSION:
        return False, "structured_output_schema_invalid", None, "selection_schema_version_invalid"
    if value.get("public_write_attempted") is not False:
        return False, "publication_authority_failure", None, "selection_public_write_forbidden"
    status = str(value.get("status") or "")
    plan = value.get("ordered_candidate_plan")
    summary = str(value.get("selection_summary") or "").strip()
    if not isinstance(plan, list):
        return False, "structured_output_schema_invalid", None, "ordered_candidate_plan_list_required"
    if not summary:
        return False, "structured_output_schema_invalid", None, "selection_summary_required"
    if status == _SELECTION_STATUS_ABSTAIN:
        if plan:
            return False, "structured_output_schema_invalid", None, "abstain_candidate_plan_must_be_empty"
        return True, None, dict(value), None
    if status != _SELECTION_STATUS_SELECT:
        return False, "structured_output_schema_invalid", None, "selection_status_invalid"
    if not 1 <= len(plan) <= MAX_ADMITTED_CANDIDATES:
        return False, "structured_output_schema_invalid", None, "ordered_candidate_plan_count_invalid"
    cleaned_plan: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    plan_fields = {
        "candidate_id",
        "article_mode",
        "selection_rationale",
        "research_queries",
    }
    for position, raw in enumerate(plan, start=1):
        if not isinstance(raw, Mapping) or set(raw) != plan_fields:
            return False, "structured_output_schema_invalid", None, "candidate_plan_entry_fields_invalid"
        candidate_id = str(raw.get("candidate_id") or "")
        if candidate_id not in candidate_ids:
            return False, "malformed_business_input", None, "candidate_plan_id_not_governed"
        if candidate_id in seen_ids:
            return False, "malformed_business_input", None, "candidate_plan_id_duplicate"
        seen_ids.add(candidate_id)
        mode = raw.get("article_mode")
        if not isinstance(mode, str) or mode not in ARTICLE_MODES:
            return False, "structured_output_schema_invalid", None, "article_mode_scalar_invalid"
        rationale = str(raw.get("selection_rationale") or "").strip()
        if len(rationale) < 8:
            return False, "structured_output_schema_invalid", None, "candidate_rationale_required"
        queries = raw.get("research_queries")
        if not isinstance(queries, list) or not 1 <= len(queries) <= 3:
            return False, "structured_output_schema_invalid", None, "research_query_count_invalid"
        cleaned = [" ".join(str(item or "").split()) for item in queries]
        if any(len(item) < 6 or len(item) > 180 or _URL_RE.search(item) for item in cleaned):
            return False, "structured_output_schema_invalid", None, "research_query_invalid"
        cleaned_plan.append(
            {
                "candidate_id": candidate_id,
                "article_mode": mode,
                "selection_rationale": rationale,
                "research_queries": cleaned,
                "plan_position": position,
                "plan_role": "PRIMARY" if position == 1 else "FALLBACK",
            }
        )
    result = dict(value)
    result["ordered_candidate_plan"] = cleaned_plan
    return True, None, result, None


def _required_article_fields(article: Mapping[str, Any]) -> list[str]:
    fields = (
        "title",
        "dek",
        "search_title",
        "meta_description",
        "social_hook",
        "substack_body_markdown",
    )
    return [field for field in fields if not str(article.get(field) or "").strip()]


def _validate_worker_text(text: str) -> tuple[bool, str | None, Any, str | None]:
    try:
        value = json.loads(str(text or ""))
    except json.JSONDecodeError:
        return False, "structured_output_malformed", None, "worker_json_invalid"
    if not isinstance(value, Mapping):
        return False, "structured_output_schema_invalid", None, "worker_object_required"
    if set(value) != {
        "schema_version",
        "article",
        "cited_sources",
        "material_claim_bindings",
        "public_write_attempted",
    }:
        return False, "structured_output_schema_invalid", None, "worker_top_level_fields_invalid"
    if value.get("schema_version") != ARTICLE_SCHEMA_VERSION:
        return False, "structured_output_schema_invalid", None, "worker_schema_version_invalid"
    if value.get("public_write_attempted") is not False:
        return False, "publication_authority_failure", None, "worker_public_write_forbidden"
    article = value.get("article")
    sources = value.get("cited_sources")
    claims = value.get("material_claim_bindings")
    if not isinstance(article, Mapping) or _required_article_fields(article):
        return False, "structured_output_schema_invalid", None, "article_required_fields_missing"
    if not isinstance(sources, list) or not 1 <= len(sources) <= 3:
        return False, "structured_output_schema_invalid", None, "cited_source_count_invalid"
    if not isinstance(claims, list) or not claims:
        return False, "structured_output_schema_invalid", None, "material_claim_bindings_missing"
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, Mapping):
            return False, "structured_output_schema_invalid", None, "cited_source_object_required"
        if set(source) != {"source_id", "url", "publisher", "published_at_utc"}:
            return False, "structured_output_schema_invalid", None, "cited_source_fields_invalid"
        if str(source.get("source_id") or "") != f"SOURCE_{index}":
            return False, "structured_output_schema_invalid", None, "cited_source_order_invalid"
        if not str(source.get("url") or "").startswith("https://"):
            return False, "structured_output_schema_invalid", None, "cited_source_https_required"
    for claim in claims:
        if not isinstance(claim, Mapping):
            return False, "structured_output_schema_invalid", None, "claim_object_required"
        if set(claim) != {
            "claim_id",
            "claim_text",
            "claim_kind",
            "source_id",
            "support_excerpt",
            "attribution_required",
        }:
            return False, "structured_output_schema_invalid", None, "claim_fields_invalid"
        if str(claim.get("claim_kind") or "") not in _VALID_CLAIM_KINDS:
            return False, "structured_output_schema_invalid", None, "claim_kind_invalid"
        if not isinstance(claim.get("attribution_required"), bool):
            return False, "structured_output_schema_invalid", None, "claim_attribution_flag_invalid"
        if len(str(claim.get("claim_text") or "").strip()) < 8:
            return False, "structured_output_schema_invalid", None, "claim_text_too_short"
        if len(str(claim.get("support_excerpt") or "").strip()) < 8:
            return False, "structured_output_schema_invalid", None, "claim_excerpt_too_short"
    return True, None, dict(value), None


def _bounded_budget(logical_invocation_id: str) -> RetryBudget:
    return RetryBudget(
        logical_invocation_id=logical_invocation_id,
        max_total_provider_attempts=MAX_PROVIDER_ATTEMPTS_PER_LOGICAL_INVOCATION,
        max_fallback_transitions=0,
        max_same_model_retries=0,
        max_structured_output_repair_attempts=0,
        max_cumulative_retry_sleep_seconds=0.0,
        wall_clock_budget_seconds=180.0,
        per_model_max_attempts=(1,),
    )


def _safe_attempt_diagnostic(attempt: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "attempt_index": int(attempt.get("attempt_number_global") or 0),
        "requested_model": attempt.get("requested_model"),
        "resolved_model": attempt.get("resolved_model"),
        "failure_class": attempt.get("failure_class"),
        "provider_status_class": attempt.get("provider_status_class"),
        "validator_reason": attempt.get("structured_validation_diagnostic_code"),
        "accepted": str(attempt.get("disposition") or "") == "accepted",
    }
    if isinstance(attempt.get("usage"), Mapping):
        result["usage"] = dict(attempt["usage"])
    if isinstance(attempt.get("cost"), Mapping):
        result["cost"] = dict(attempt["cost"])
    return result


def _safe_router_receipt(summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": str(summary.get("schema_version") or ""),
        "logical_invocation_id": summary.get("logical_invocation_id"),
        "role_task_id": summary.get("role_task_id"),
        "terminal_disposition": summary.get("terminal_disposition"),
        "selected_model": summary.get("selected_model"),
        "models_attempted_in_order": list(summary.get("models_attempted_in_order") or []),
        "total_attempts": int(summary.get("total_attempts") or 0),
        "total_fallback_transitions": int(summary.get("total_fallback_transitions") or 0),
        "total_usage": dict(summary.get("total_usage") or {}),
        "total_cost": dict(summary.get("total_cost") or {}),
        "model_identity_provider_verifiable": summary.get("model_identity_provider_verifiable"),
        "attempt_diagnostics": [
            _safe_attempt_diagnostic(row)
            for row in summary.get("attempts") or []
            if isinstance(row, Mapping)
        ],
        "budget_exhausted_reason": summary.get("budget_exhausted_reason"),
        "public_write_attempted": False,
    }


def _default_llm_invoke(
    *,
    role_task_id: str,
    logical_invocation_id: str,
    prompt: str,
    governed_input: Mapping[str, Any],
    validator: Callable[[str], tuple[bool, str | None, Any, str | None]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    summary = routed_llm_invocation(
        prompt=prompt,
        role_task_id=role_task_id,
        logical_invocation_id=logical_invocation_id,
        governed_input=governed_input,
        prompt_template="v1_simple_gemini_newsroom",
        prompt_version="v1",
        validator=validator,
        budget=_bounded_budget(logical_invocation_id),
        timeout_seconds=180.0,
    )
    if summary.get("terminal_disposition") != ACCEPTED or not isinstance(
        summary.get("output"), Mapping
    ):
        safe_receipt = _safe_router_receipt(summary)
        raise SimpleGeminiNewsroomError(
            "gemini_logical_invocation_blocked",
            [
                str(role_task_id),
                str(summary.get("terminal_disposition") or "UNKNOWN"),
                str(summary.get("budget_exhausted_reason") or ""),
            ],
            diagnostics={"router_receipt": safe_receipt},
        )
    return dict(summary["output"]), _safe_router_receipt(summary)


def _invoke(
    *,
    llm_invoke: LlmInvoke | None,
    role_task_id: str,
    logical_invocation_id: str,
    prompt: str,
    governed_input: Mapping[str, Any],
    validator: Callable[[str], tuple[bool, str | None, Any, str | None]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    caller = llm_invoke or _default_llm_invoke
    output, receipt = caller(
        role_task_id=role_task_id,
        logical_invocation_id=logical_invocation_id,
        prompt=prompt,
        governed_input=governed_input,
        validator=validator,
    )
    if not isinstance(output, Mapping) or not isinstance(receipt, Mapping):
        raise SimpleGeminiNewsroomError("llm_invoke_contract_invalid")
    return dict(output), dict(receipt)


def _institutional_edge_mode_guide() -> dict[str, dict[str, Any]]:
    """Project the current Institutional Edge mode map for the Simple selector."""
    result: dict[str, dict[str, Any]] = {}
    for mode in ARTICLE_MODES:
        packet = build_institutional_edge_editorial_packet(
            article_mode=mode,
            structured_data_supported=False,
        )
        blockers = validate_institutional_edge_packet(packet)
        if blockers:
            raise SimpleGeminiNewsroomError(
                "institutional_edge_editorial_packet_invalid", blockers
            )
        result[mode] = {
            "institutional_edge_mode": packet["article_mode"],
            "mode_expectations": list(packet["mode_expectations"]),
            "simple_mode_behavior": _SIMPLE_MODE_BEHAVIOR[mode],
            "explicit_qualitative_inference_required": mode
            in {"CAPITAL_CHRONICLE_VIEW", "WHAT_THE_MARKET_IS_MISSING"},
            "grants_factual_authority": False,
            "grants_numeric_authority": False,
        }
    return result


def _institutional_edge_writer_packet(
    *, article_mode: str, source_pack: Sequence[Mapping[str, Any]]
) -> dict[str, Any]:
    packet = build_institutional_edge_editorial_packet(
        article_mode=article_mode,
        accepted_evidence_packet={
            "evidence_documents": [dict(row) for row in source_pack]
        },
        structured_data_supported=False,
    )
    blockers = validate_institutional_edge_packet(packet)
    if blockers:
        raise SimpleGeminiNewsroomError(
            "institutional_edge_editorial_packet_invalid", blockers
        )
    return packet


def _selection_prompt(governed: Mapping[str, Any]) -> str:
    select_contract = {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "status": _SELECTION_STATUS_SELECT,
        "ordered_candidate_plan": [
            {
                "candidate_id": "copy one exact candidate_id from GOVERNED_INPUT",
                "article_mode": "exactly one of: " + " | ".join(ARTICLE_MODES),
                "selection_rationale": "why this candidate is independently worth an article",
                "research_queries": ["1 to 3 query texts, never URLs"],
            }
        ],
        "selection_summary": "short explanation of the ordered useful-candidate plan",
        "public_write_attempted": False,
    }
    abstain_contract = {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "status": _SELECTION_STATUS_ABSTAIN,
        "ordered_candidate_plan": [],
        "selection_summary": "specific reason no candidate is genuinely useful",
        "public_write_attempted": False,
    }
    return (
        "Return exactly one JSON object. Do not use markdown, code fences, commentary, prefixes, or suffixes. "
        "Use exactly the five top-level keys shown in one OUTPUT_CONTRACT variant and preserve their JSON types. "
        "Choose one primary genuinely useful current Capital Chronicle story and at most two ordered fallback "
        "stories from GOVERNED_INPUT. Every fallback must be independently worth an article, not filler. "
        "Do not require evidence-ready/sourceability/readiness/media/SEO perfection before selection. "
        "The sourceability_route_hint is deterministic routing-only context, never factual or publication authority. "
        "When stories are independently similarly useful, prefer the one with the shorter governed route and lower known access risk. "
        "If you return three candidates and GOVERNED_INPUT contains an independently useful candidate whose "
        "sourceability_route_hint.canonical_x_zero_get_route_available is true, include at least one such candidate in the plan; "
        "this route-diversity rule prevents all three choices from sharing the same retrieval failure. "
        "Never select a weak story merely because its route is easier. "
        "Published-memory duplicates were filtered deterministically before this call. If nothing is useful, ABSTAIN. "
        "Use institutional_edge_mode_guide to choose the mode the story genuinely warrants. Prefer the strongest "
        "defensible tension over generic recap, and prioritize a proposition that can explain why the reader should care now. "
        "Do not force a house view or market-missing mode when the headline does not support one. "
        "For every admitted candidate return one to three short research query texts that can locate reputable "
        "public reporting for that story. No tools, no URLs, no factual/numeric/publication authority. "
        "Do not select a proprietary Capital Chronicle forecast/probability/scenario/regime claim. "
        "Copy every candidate_id byte-for-byte from GOVERNED_INPUT and use one scalar article_mode string per entry. "
        "Do not repeat a candidate ID. Return strict JSON only using OUTPUT_CONTRACT.\nOUTPUT_CONTRACT:\n"
        + "SELECT_CANDIDATE_PLAN_CONTRACT:\n"
        + json.dumps(select_contract, sort_keys=True, ensure_ascii=False)
        + "\nABSTAIN_CONTRACT:\n"
        + json.dumps(abstain_contract, sort_keys=True, ensure_ascii=False)
        + "\nGOVERNED_INPUT:\n"
        + json.dumps(governed, sort_keys=True, ensure_ascii=False)
    )


def _evidence_request(candidate: Mapping[str, Any], plan_entry: Mapping[str, Any]) -> dict[str, Any]:
    bindings: list[dict[str, Any]] = []
    source_url = str(candidate.get("source_url") or "")
    candidate_urls = list(
        dict.fromkeys(
            safe_url
            for key in ("official_source_urls", "public_source_urls")
            for value in candidate.get(key) or []
            if (safe_url := _safe_https_locator(value))
        )
    )
    source_host = str(urlsplit(source_url).hostname or "").casefold()
    safe_source_url = _safe_https_locator(source_url)
    if (
        safe_source_url
        and source_host not in {"x.com", "www.x.com", "t.co", "www.t.co"}
        and safe_source_url not in candidate_urls
    ):
        candidate_urls.append(safe_source_url)
    for url in candidate_urls:
        bindings.append(
            {
                "headline_id": candidate["headline_id"],
                "url": url,
                "source_timestamp_utc": candidate.get("source_timestamp_utc"),
            }
        )
    research_queries = list(plan_entry["research_queries"])
    report_provenance = candidate_report_provenance(candidate)
    material = {
        "candidate_id": candidate["candidate_id"],
        "headline_id": candidate["headline_id"],
        "article_mode": plan_entry["article_mode"],
        "research_queries": research_queries,
    }
    return {
        "cluster_id": candidate["candidate_id"],
        "headline_ids": [candidate["headline_id"]],
        "request_logical_hash": _hash(material),
        "story_evidence_scope_id": candidate["candidate_id"],
        "story_type": "selected_current_news",
        "requested_article_mode": plan_entry["article_mode"],
        "effective_article_mode": plan_entry["article_mode"],
        "required_evidence_capabilities": [
            "credible_report_or_event_confirmation",
            "basic_attributed_facts",
        ],
        "evidence_enrichment_context": {"requested": True},
        "story_context": {
            "leaf_summaries": [candidate["headline_text"]],
            "candidate_source_timestamp_utc": candidate.get("source_timestamp_utc"),
            "candidate_source_account": candidate.get("source_account"),
            "candidate_source_url": candidate.get("source_url"),
            "report_provenance": report_provenance,
            "grounded_research_queries": research_queries,
            "planned_research_query_count": len(research_queries),
            "planned_research_query_set_sha256": _hash(research_queries),
            "locator_query_policy": "ORDERED_QUERY_PLAN_BOUNDED_BY_SHARED_RESOLVER_LEDGER",
            "public_source_url_bindings": bindings,
            "candidate_packet_locators_grant_factual_authority": False,
        },
    }


def _default_evidence_loader(
    cutoff_utc: str,
    *,
    source_route_health: Mapping[str, Any] | None = None,
) -> EvidenceLoader:
    rendered_recovery = BrowserOSNeoRenderedSourceRecovery(
        allowed_hosts=REPUTABLE_SECONDARY_HOSTS,
    )
    return SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=cutoff_utc,
        max_requests=MAX_SOURCE_REQUESTS,
        timeout_seconds=12.0,
        rendered_source_get=rendered_recovery,
        source_route_health=source_route_health,
    )


def _updated_source_route_health(loader: Any) -> dict[str, Any]:
    snapshot = getattr(loader, "source_route_health_snapshot", None)
    if not callable(snapshot):
        return {}
    try:
        value = snapshot()
    except (OSError, TypeError, ValueError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _source_pack(documents: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    pack: list[dict[str, Any]] = []
    for document in documents[:MAX_SOURCE_DOCUMENTS]:
        url = str(document.get("reader_source_url") or document.get("source_url") or "")
        text = str(document.get("canonical_content_text") or "")
        if not url.startswith("https://") or len(text.strip()) < 40:
            continue
        source_id = f"SOURCE_{len(pack) + 1}"
        pack.append(
            {
                "source_id": source_id,
                "url": url,
                "publisher": str(
                    document.get("publisher")
                    or document.get("source_identity")
                    or urlsplit(url).hostname
                    or ""
                ),
                "published_at_utc": str(document.get("published_at_utc") or ""),
                "published_at_source": str(document.get("published_at_source") or ""),
                "document_id": str(document.get("document_id") or ""),
                "source_identity": str(document.get("source_identity") or ""),
                "source_authority_class": str(
                    document.get("source_authority_class") or ""
                ),
                "retrieval_method": str(document.get("retrieval_method") or ""),
                "canonical_resolution_status": str(
                    document.get("canonical_resolution_status") or ""
                ),
                "browser_rendered_acquisition": dict(
                    document.get("browser_rendered_acquisition") or {}
                )
                if isinstance(document.get("browser_rendered_acquisition"), Mapping)
                else None,
                "secondary_listing_only": bool(
                    document.get("secondary_listing_only")
                ),
                "report_truth_only": bool(document.get("report_truth_only")),
                "canonical_content_sha256": str(
                    document.get("canonical_content_sha256") or _text_hash(text)
                ),
                "canonical_content_text": text[:MAX_SOURCE_TEXT_CHARS],
            }
        )
    return pack


def _worker_prompt(governed: Mapping[str, Any]) -> str:
    contract = {
        "schema_version": ARTICLE_SCHEMA_VERSION,
        "article": {
            "title": "string",
            "dek": "string",
            "search_title": "string",
            "meta_description": "string",
            "social_hook": "string",
            "substack_body_markdown": "string",
        },
        "cited_sources": [
            {
                "source_id": "SOURCE_1..SOURCE_3 in order",
                "url": "exact URL from SOURCE_PACK",
                "publisher": "publisher",
                "published_at_utc": "locator hint copied from SOURCE_PACK",
            }
        ],
        "material_claim_bindings": [
            {
                "claim_id": "stable id",
                "claim_text": "exact public-copy text",
                "claim_kind": "FACT|NUMBER|QUOTE|CAUSALITY",
                "source_id": "SOURCE_N",
                "support_excerpt": "exact substring from SOURCE_PACK content",
                "attribution_required": True,
            }
        ],
        "public_write_attempted": False,
    }
    return (
        "Return exactly one JSON object with exactly the five top-level keys shown in OUTPUT_CONTRACT. "
        "Do not use markdown code fences, commentary, prefixes, or suffixes outside the JSON object. "
        "Write one useful concise Capital Chronicle article from GOVERNED_INPUT and SOURCE_PACK only. "
        "Treat epistemic_state as an immutable deterministic contract. Distinguish REPORT TRUTH from EVENT TRUTH: "
        "report_proposition is supported, while event_proposition may remain unconfirmed. Include the exact "
        "reader_visible_epistemic_label prominently in the dek and opening paragraph. For UNCONFIRMED or RELAYED "
        "content, keep the named publisher or relay attribution in the title and dek, state the reporting status "
        "in the first paragraph, and never silently rewrite 'Publisher reports X' as 'X happened'. Any mechanism, "
        "When epistemic_state.evidence_basis is TRUSTED_RELAY_ATTRIBUTED_REPORT, the retrieved record proves only "
        "the relay's words: title, dek, and opening must name @relay_source_identity and say it is citing "
        "primary_reporting_publisher. Never write 'Publisher reports/says X' because the original publisher report "
        "was not separately resolved. "
        "winner/loser, market implication, criticism, or consequence that depends on X must be explicitly "
        "conditional, using 'If the report is accurate', 'If confirmed', or equivalent. Do not call material a "
        "leak, rumor, or internal-source report unless epistemic_state.origin_character says so. "
        "Follow institutional_edge_editorial_packet and its exact mode expectations. Lead with the strongest defensible "
        "tension and explain why the reader should care now. Make title, dek, and social_hook compelling, proposition-led, "
        "and no broader than the final supported article truth. In analytical modes, include a real counter-case or exact "
        "condition that would challenge the thesis when appropriate. Criticism or contrarian framing is welcome only when "
        "the retrieved record supports its factual premises. For CAPITAL_CHRONICLE_VIEW, explicitly label the qualitative "
        "house inference as Capital Chronicle's view, interpretation, analysis, or inference. For "
        "WHAT_THE_MARKET_IS_MISSING, explicitly label the supported overlooked-variable inference the same way. "
        "Do not browse or invent URLs. Do not expand factual scope beyond retrieved source bytes. "
        "Every non-heading body paragraph must contain at least one exact [[SOURCE:SOURCE_N]] marker. "
        "The selected_candidate is the article's current news peg. Title and dek must primarily represent that "
        "selected current event; do not pivot to another highlight found in SOURCE_PACK. Older/background source "
        "highlights may use only temporally neutral wording unless exact retrieved bytes establish their date. Do "
        "not infer simultaneity merely because facts appear in the same document. Phrases such as announced alongside, "
        "came alongside, today announced, newly announced, new, or equivalent temporal claims require exact source-byte "
        "support. If the selected candidate is earnings, keep the article earnings-led. Prefer narrowing to the current "
        "proved peg over adding optional background. Every material fact, number, quotation, or causal assertion in title, "
        "dek, search_title, meta_description, social_hook, or body must have a binding. The exact title, dek, search_title, "
        "meta_description, and social_hook must each appear as a claim_text binding. Public metadata must use source-faithful "
        "terminology; never substitute financing platforms with a fund unless exact retrieved bytes say fund. "
        "support_excerpt must be an exact "
        "substring of the cited SOURCE_PACK text. Every claim_text and support_excerpt must be at least eight "
        "characters and must not be a bare label, symbol, or isolated number. Use no proprietary Capital Chronicle numeric/forecast/scenario/"
        "probability/regime/valuation/base-case claim in this reset lane. A qualitative Capital Chronicle inference does "
        "not create numeric authority and must remain distinguishable from observed fact. Source timestamps are hints only; retrieved source provenance "
        "remains deterministic authority. Zero media is valid. This call has no publication tools and must not claim "
        "a publication attempt: public_write_attempted MUST be the JSON boolean false, never true or a string. "
        "When epistemic_state.event_confirmation_state is not CONFIRMED, every material claim about the underlying "
        "event must set attribution_required to true. "
        "Return strict JSON only.\nOUTPUT_CONTRACT:\n"
        + json.dumps(contract, sort_keys=True, ensure_ascii=False)
        + "\nGOVERNED_INPUT:\n"
        + json.dumps(governed, sort_keys=True, ensure_ascii=False)
    )


def _public_copy(article: Mapping[str, Any]) -> str:
    return "\n".join(
        str(article.get(key) or "")
        for key in (
            "title",
            "dek",
            "search_title",
            "meta_description",
            "social_hook",
            "substack_body_markdown",
        )
    )


def _normalize_relay_attribution(
    worker_output: Mapping[str, Any],
    epistemic_state: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], int]:
    """Normalize only forbidden original-publisher impersonation grammar.

    The accepted relay document proves the relay's captured words, not the cited publisher's
    original report.  This mechanical transform changes neither proposition nor evidence; the
    normal deterministic validator still decides whether the complete article is admissible.
    """
    result = dict(worker_output)
    state = epistemic_state if isinstance(epistemic_state, Mapping) else {}
    if state.get("evidence_basis") != "TRUSTED_RELAY_ATTRIBUTED_REPORT":
        return result, 0
    relay = str(state.get("relay_source_identity") or "").strip().lstrip("@")
    publisher = str(state.get("primary_reporting_publisher") or "").strip()
    if not relay or not publisher:
        return result, 0
    pattern = re.compile(
        rf"\b{re.escape(publisher)}\s+(reports?|reported|says|said)\b",
        re.IGNORECASE,
    )
    replacement_prefix = f"@{relay}, citing {publisher}, "
    count = 0

    def normalize(value: Any) -> Any:
        nonlocal count
        if not isinstance(value, str):
            return value
        value, replacements = pattern.subn(
            lambda match: replacement_prefix + match.group(1), value
        )
        count += replacements
        return value

    article = result.get("article")
    if isinstance(article, Mapping):
        result["article"] = {
            key: normalize(value) for key, value in dict(article).items()
        }
    bindings = []
    for row in result.get("material_claim_bindings") or []:
        if not isinstance(row, Mapping):
            bindings.append(row)
            continue
        normalized = dict(row)
        normalized["claim_text"] = normalize(normalized.get("claim_text"))
        bindings.append(normalized)
    if bindings or "material_claim_bindings" in result:
        result["material_claim_bindings"] = bindings
    return result, count


def _strip_duplicate_leading_h1(article: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(article)
    body = str(result.get("substack_body_markdown") or "")
    lines = body.splitlines()
    if lines and lines[0].startswith("# ") and _normal(lines[0][2:]) == _normal(result.get("title")):
        remaining = lines[1:]
        while remaining and not remaining[0].strip():
            remaining.pop(0)
        result["substack_body_markdown"] = "\n".join(remaining)
    return result


def _paragraph_marker_blockers(body: str, valid_source_ids: set[str]) -> list[str]:
    blockers: list[str] = []
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", str(body or "")) if part.strip()]
    for index, paragraph in enumerate(paragraphs, start=1):
        if all(line.lstrip().startswith("#") for line in paragraph.splitlines() if line.strip()):
            continue
        markers = set(_SOURCE_MARKER_RE.findall(paragraph))
        if not markers:
            blockers.append(f"unbound_body_paragraph:{index}")
        elif not markers.issubset(valid_source_ids):
            blockers.append(f"unknown_source_marker_in_paragraph:{index}")
    return blockers


def _peg_terms(value: Any) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-z][a-z0-9'-]{2,}", _normal(value))
        if term not in _NEWS_PEG_STOPWORDS and not term.startswith("http")
    }


def _selected_news_peg_blockers(
    article: Mapping[str, Any], selected_candidate: Mapping[str, Any] | None
) -> list[str]:
    if not isinstance(selected_candidate, Mapping):
        return []
    headline = str(selected_candidate.get("headline_text") or "")
    lead = " ".join(
        str(article.get(field) or "") for field in ("title", "dek")
    )
    headline_terms = _peg_terms(headline)
    lead_terms = _peg_terms(lead)
    triggered_groups = [
        group for group in _NEWS_PEG_TOPIC_GROUPS if headline_terms.intersection(group)
    ]
    if triggered_groups and not any(lead_terms.intersection(group) for group in triggered_groups):
        return ["selected_current_news_peg_topic_missing_from_title_dek"]
    if not triggered_groups and len(headline_terms.intersection(lead_terms)) < 2:
        return ["selected_current_news_peg_alignment_insufficient"]
    return []


def _public_copy_integrity_blockers(
    article: Mapping[str, Any], cited_documents: Mapping[str, Mapping[str, Any]]
) -> list[str]:
    public_copy = _public_copy(article)
    source_text = "\n".join(
        str(document.get("canonical_content_text") or "")
        for document in cited_documents.values()
    )
    normalized_source = _normal(source_text)
    blockers: list[str] = []
    for pattern in _RISKY_TEMPORAL_PATTERNS:
        for match in pattern.finditer(public_copy):
            phrase = _normal(match.group(0))
            if phrase and phrase not in normalized_source:
                blockers.append(
                    "unsupported_temporal_newness_or_simultaneity:"
                    + _text_hash(phrase)[:16]
                )
    for field in _PUBLIC_METADATA_FIELDS:
        value = str(article.get(field) or "")
        if re.search(r"\bfunds?\b", value, re.IGNORECASE) and not re.search(
            r"\bfunds?\b", source_text, re.IGNORECASE
        ):
            blockers.append(f"public_metadata_terminology_not_in_source:{field}:fund")
    return blockers


def _editorial_growth_edge_blockers(
    article: Mapping[str, Any], *, article_mode: str | None
) -> list[str]:
    mode = str(article_mode or "").upper()
    public_copy = _public_copy(article)
    blockers: list[str] = []
    if mode in {"CAPITAL_CHRONICLE_VIEW", "WHAT_THE_MARKET_IS_MISSING"}:
        if not _EXPLICIT_CC_INFERENCE_RE.search(public_copy):
            blockers.append("house_mode_qualitative_inference_not_explicitly_labeled")
    if _RESERVED_CC_NUMERIC_AUTHORITY_RE.search(public_copy):
        blockers.append("capital_chronicle_reserved_numeric_authority_unavailable")
    return blockers


def _first_body_paragraph(body: str) -> str:
    for paragraph in re.split(r"\n\s*\n", str(body or "")):
        cleaned = " ".join(
            line.strip()
            for line in paragraph.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        if cleaned:
            return _SOURCE_MARKER_RE.sub("", cleaned).strip()
    return ""


def _epistemic_copy_blockers(
    article: Mapping[str, Any],
    claims: Sequence[Mapping[str, Any]],
    epistemic_state: Mapping[str, Any] | None,
) -> list[str]:
    if not isinstance(epistemic_state, Mapping) or not epistemic_state:
        return []
    blockers = list(validate_epistemic_state(epistemic_state))
    if blockers:
        return blockers
    state = str(epistemic_state.get("event_confirmation_state") or "")
    origin = str(epistemic_state.get("origin_character") or "")
    publisher = str(epistemic_state.get("primary_reporting_publisher") or "")
    relay = str(epistemic_state.get("relay_source_identity") or "")
    label = str(epistemic_state.get("reader_visible_epistemic_label") or "")
    title = str(article.get("title") or "")
    dek = str(article.get("dek") or "")
    first = _first_body_paragraph(str(article.get("substack_body_markdown") or ""))
    public_copy = _SOURCE_MARKER_RE.sub("", _public_copy(article))
    public_normal = _normal(public_copy)
    attribution_tokens = {
        value
        for value in (
            _normal(publisher),
            _normal(publisher).replace("the ", "", 1),
            _normal(relay),
            "unconfirmed",
            "reported",
            "reports",
            "according to",
        )
        if value
    }
    if state != "CONFIRMED":
        if not any(token in _normal(title) for token in attribution_tokens):
            blockers.append("epistemic_title_attribution_or_uncertainty_missing")
        if label.casefold() not in dek.casefold() and not any(
            token in _normal(dek) for token in attribution_tokens
        ):
            blockers.append("epistemic_dek_attribution_or_label_missing")
        if label.casefold() not in first.casefold() and not any(
            token in _normal(first) for token in attribution_tokens
        ):
            blockers.append("epistemic_opening_reporting_state_missing")
        if any(
            claim.get("attribution_required") is not True
            for claim in claims
            if isinstance(claim, Mapping)
        ):
            blockers.append("epistemic_unconfirmed_material_claim_attribution_missing")
        event_terms = _peg_terms(epistemic_state.get("event_proposition"))
        for field in _PUBLIC_METADATA_FIELDS:
            value = str(article.get(field) or "")
            if len(event_terms.intersection(_peg_terms(value))) >= 2 and not any(
                token in _normal(value) for token in attribution_tokens
            ):
                blockers.append(f"epistemic_certainty_inflation:{field}")
        for index, paragraph in enumerate(
            re.split(r"\n\s*\n", str(article.get("substack_body_markdown") or "")),
            start=1,
        ):
            clean = _SOURCE_MARKER_RE.sub("", paragraph)
            if len(event_terms.intersection(_peg_terms(clean))) < 2:
                continue
            conditional = re.search(
                r"\b(?:if|would|could|may|might|reported|reports|according\s+to|unconfirmed)\b",
                clean,
                re.IGNORECASE,
            )
            if conditional is None and not any(
                token in _normal(clean) for token in attribution_tokens
            ):
                blockers.append(f"epistemic_event_asserted_as_confirmed:{index}")
    if str(epistemic_state.get("evidence_basis") or "") == (
        "TRUSTED_RELAY_ATTRIBUTED_REPORT"
    ):
        relay_token = _normal(relay)
        if not relay_token or any(
            relay_token not in _normal(value)
            for value in (title, dek, first)
        ):
            blockers.append("epistemic_relay_identity_not_prominent")
        if publisher and re.search(
            rf"\b{re.escape(publisher)}\s+(?:reports?|reported|says|said)\b",
            public_copy,
            re.IGNORECASE,
        ):
            blockers.append("epistemic_relay_impersonates_original_publisher")
    if origin != "LEAK" and re.search(r"\b(?:leak|leaked)\b", public_normal):
        blockers.append("epistemic_unsupported_leak_label")
    if origin != "RUMOR" and re.search(r"\b(?:rumou?r|market chatter)\b", public_normal):
        blockers.append("epistemic_unsupported_rumor_label")
    if origin != "ANONYMOUS_OR_INTERNAL_SOURCES" and re.search(
        r"\b(?:anonymous|internal sources?|people familiar|sources? familiar)\b",
        public_normal,
    ):
        blockers.append("epistemic_unsupported_internal_source_label")
    return sorted(set(blockers))


def _validate_article_against_source_pack(
    worker_output: Mapping[str, Any],
    source_pack: Sequence[Mapping[str, Any]],
    *,
    selected_candidate: Mapping[str, Any] | None = None,
    article_mode: str | None = None,
    epistemic_state: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    article = _strip_duplicate_leading_h1(dict(worker_output.get("article") or {}))
    sources = [dict(row) for row in worker_output.get("cited_sources") or [] if isinstance(row, Mapping)]
    claims = [dict(row) for row in worker_output.get("material_claim_bindings") or [] if isinstance(row, Mapping)]
    available_by_url = {str(row.get("url") or ""): dict(row) for row in source_pack}
    cited_by_id: dict[str, dict[str, Any]] = {}
    blockers: list[str] = []
    for index, source in enumerate(sources, start=1):
        source_id = str(source.get("source_id") or "")
        url = str(source.get("url") or "")
        if source_id != f"SOURCE_{index}":
            blockers.append(f"source_marker_order_invalid:{source_id}")
            continue
        available = available_by_url.get(url)
        if available is None:
            blockers.append(f"source_not_in_retrieved_pack:{source_id}")
            continue
        cited_by_id[source_id] = available
    public_copy_normal = _normal(_public_copy(article))
    supported: list[dict[str, Any]] = []
    for claim in claims:
        claim_id = str(claim.get("claim_id") or "UNKNOWN")
        claim_text = str(claim.get("claim_text") or "").strip()
        source_id = str(claim.get("source_id") or "")
        excerpt = str(claim.get("support_excerpt") or "").strip()
        document = cited_by_id.get(source_id)
        if len(claim_text) < 8 or _normal(claim_text) not in public_copy_normal:
            blockers.append(f"material_claim_not_in_public_copy:{claim_id}")
            continue
        if str(claim.get("claim_kind") or "") not in _VALID_CLAIM_KINDS:
            blockers.append(f"material_claim_kind_invalid:{claim_id}")
            continue
        if document is None or len(excerpt) < 8 or _normal(excerpt) not in _normal(
            document.get("canonical_content_text")
        ):
            blockers.append(f"material_claim_excerpt_not_verified:{claim_id}")
            continue
        supported.append(
            {
                "claim_id": claim_id,
                "claim_text": claim_text,
                "claim_kind": str(claim.get("claim_kind") or "FACT"),
                "source_id": source_id,
                "document_id": document.get("document_id"),
                "support_status": "SUPPORTED_EXACT_RETRIEVED_SOURCE_BYTES",
                "attribution_required": bool(claim.get("attribution_required")),
                "support_excerpt_sha256": _text_hash(excerpt),
            }
        )
    bound_claim_texts = {_normal(row.get("claim_text")) for row in claims}
    for field in _PUBLIC_METADATA_FIELDS:
        if _normal(article.get(field)) not in bound_claim_texts:
            blockers.append(f"{field}_material_binding_missing")
    blockers.extend(_selected_news_peg_blockers(article, selected_candidate))
    blockers.extend(_public_copy_integrity_blockers(article, cited_by_id))
    blockers.extend(
        _editorial_growth_edge_blockers(article, article_mode=article_mode)
    )
    blockers.extend(_epistemic_copy_blockers(article, claims, epistemic_state))
    blockers.extend(
        _paragraph_marker_blockers(
            str(article.get("substack_body_markdown") or ""), set(cited_by_id)
        )
    )
    if blockers:
        raise SimpleGeminiNewsroomError("deterministic_article_validation_failed", blockers)
    return article, {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "status": "PASS",
        "ordering": ORDERING,
        "supported_material_claim_count": len(supported),
        "unsupported_material_claim_count": 0,
        "supported_material_claims": supported,
        "cited_source_count": len(cited_by_id),
        "source_urls": [str(row.get("url") or "") for row in sources],
        "source_timestamps_are_model_authority": False,
        "source_bytes_precede_writer": True,
        "epistemic_state": dict(epistemic_state or {}),
        "report_truth_validated_separately_from_event_truth": bool(
            epistemic_state
        ),
        "public_write_performed": False,
        "unknown_write_detected": False,
    }


def _revision_prompt(
    governed: Mapping[str, Any], prior: Mapping[str, Any], blockers: Sequence[str]
) -> str:
    return (
        "Return exactly one JSON object with no markdown fence, commentary, prefix, or suffix. "
        "Revise the prior article once using only the same governed candidate and SOURCE_PACK. "
        "Fix exactly the deterministic blockers, do not add a source or expand factual scope, and return the complete strict object. "
        "Preserve the same Institutional Edge mode expectations, labeled qualitative inference contract, reader consequence, "
        "and real counter-case/watch condition where the selected mode warrants them. "
        "Preserve the selected candidate as the current news peg and the exact binding requirement for all five public "
        "metadata fields. Remove unsupported newness, simultaneity, or inflated terminology rather than expanding sources. "
        "Preserve epistemic_state exactly: retain the reader-visible label and attribution, never upgrade report truth "
        "to event truth, keep dependent analysis conditional, and remove unsupported leak/rumor/internal-source wording. "
        "For epistemic_relay_impersonates_original_publisher, replace every 'Publisher reports/says' construction with "
        "'@relay_source_identity, citing Publisher, reports' and keep @relay_source_identity prominent in title, dek, and opening. "
        "Every body paragraph remains source-marker bound. Zero public write. public_write_attempted MUST be the JSON "
        "boolean false because this call has no publication tools.\nBLOCKERS:\n"
        + json.dumps(list(blockers), sort_keys=True)
        + "\nPRIOR_OUTPUT:\n"
        + json.dumps(dict(prior), sort_keys=True, ensure_ascii=False)
        + "\nGOVERNED_INPUT:\n"
        + json.dumps(dict(governed), sort_keys=True, ensure_ascii=False)
    )


def _blocked_router_receipt(exc: SimpleGeminiNewsroomError) -> dict[str, Any]:
    receipt = exc.diagnostics.get("router_receipt")
    return dict(receipt) if isinstance(receipt, Mapping) else {}


def _source_count_after_call(
    provenance: Mapping[str, Any], *, previous_total: int
) -> tuple[int, int]:
    if provenance.get("request_count_for_call") is not None:
        for_call = int(provenance.get("request_count_for_call") or 0)
        total = previous_total + for_call
        reported_total = provenance.get("request_count_total")
        if reported_total is not None:
            total = max(total, int(reported_total or 0))
    elif provenance.get("request_count_total") is not None:
        total = int(provenance.get("request_count_total") or 0)
        for_call = max(0, total - previous_total)
    elif provenance.get("request_count_for_candidate") is not None:
        for_call = int(provenance.get("request_count_for_candidate") or 0)
        total = previous_total + for_call
    else:
        total = max(previous_total, int(provenance.get("request_count") or 0))
        for_call = max(0, total - previous_total)
    if for_call < 0 or total < previous_total:
        raise SimpleGeminiNewsroomError("source_request_accounting_invalid")
    return for_call, total


def _safe_source_blockers(values: Sequence[Any]) -> list[str]:
    return sorted(
        {
            redact_text(str(value))[:500]
            for value in values
            if str(value).strip()
        }
    )


def _reader_safe_native_article(
    article: Mapping[str, Any],
    *,
    article_mode: str,
    epistemic_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Adapt only final validated article truth to the existing native compiler."""
    body = _SOURCE_MARKER_RE.sub("", str(article.get("substack_body_markdown") or ""))
    body = re.sub(r"(?m)^#{1,6}\s+", "", body)
    title = str(article.get("title") or "")
    label = str((epistemic_state or {}).get("reader_visible_epistemic_label") or "")
    if label and label.casefold() not in title.casefold():
        title = f"{label} | {title}"
    result = {
        "title": title,
        "subtitle": str(article.get("dek") or ""),
        "social_hook": str(article.get("social_hook") or ""),
        "effective_article_mode": str(article_mode),
        "substack_body_markdown": body,
    }
    if (epistemic_state or {}).get("event_confirmation_state") == "UNCONFIRMED":
        result.update(
            {
                "social_mechanism_summary": (
                    "The report has not been independently confirmed."
                ),
                "social_policy_summary": (
                    "Any implications remain conditional on verification."
                ),
                "social_cross_asset_summary": (
                    "Independent confirmation or denial is the next watch point."
                ),
            }
        )
    return result


def _native_preview_bundle(
    *,
    article: Mapping[str, Any],
    article_mode: str,
    article_identity: str,
    epistemic_state: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    from live_contentops.eight_platform_substack_first_pipeline_v1 import (
        build_native_derivative_payloads,
    )

    pending_url = (
        "https://capitalchronicle.substack.com/p/pending-publication-"
        + article_identity[:16]
    )
    compiler_article = _reader_safe_native_article(
        article,
        article_mode=article_mode,
        epistemic_state=epistemic_state,
    )
    payloads = build_native_derivative_payloads(
        article=compiler_article,
        selection={},
        canonical_url=pending_url,
        media_asset_ids=(),
    )
    expected = set(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    if len(payloads) != 8 or set(payloads) != expected:
        raise SimpleGeminiNewsroomError(
            "exact_eight_native_preview_package_contract_failed"
        )
    quality_blockers: list[str] = []
    for destination in ("x", "threads"):
        payload = dict(payloads.get(destination) or {})
        metrics = dict(payload.get("quality_metrics") or {})
        limit = int(payload.get("platform_limit") or 0)
        posts = list(payload.get("posts") or [])
        thread_texts = [str(payload.get("root_text") or "")]
        thread_texts.extend(str(value) for value in payload.get("reply_texts") or [])
        thread_texts.extend(str(row.get("text") or "") for row in posts)
        if metrics.get("sentence_boundary_pass") is not True:
            quality_blockers.append(f"{destination}:sentence_boundary_pass")
        if metrics.get("orphan_fragment_count") != 0:
            quality_blockers.append(f"{destination}:orphan_fragment_count")
        if metrics.get("hard_character_slicing_used") is not False:
            quality_blockers.append(f"{destination}:hard_character_slicing_used")
        if limit <= 0 or any(len(value) > limit for value in thread_texts):
            quality_blockers.append(f"{destination}:platform_limit")
    if quality_blockers:
        raise SimpleGeminiNewsroomError(
            "native_preview_quality_contract_failed",
            quality_blockers,
        )
    label = str((epistemic_state or {}).get("reader_visible_epistemic_label") or "")

    def unqualified_confirmed_assertion(text: str) -> bool:
        for match in re.finditer(r"\bconfirmed\b", text, re.IGNORECASE):
            prefix = text[max(0, match.start() - 80) : match.start()]
            if re.search(
                r"\b(?:not|never|if|unless|until|awaiting|pending|without)\b[^.!?\n]{0,60}$",
                prefix,
                re.IGNORECASE,
            ):
                continue
            return True
        return False

    for destination, payload in payloads.items():
        visible = "\n".join(
            str(value)
            for key, value in dict(payload).items()
            if key in {"text", "full_text", "root_text"}
        )
        if label and label.casefold() not in visible.casefold():
            raise SimpleGeminiNewsroomError(
                "native_preview_epistemic_state_missing", [destination]
            )
        if (
            (epistemic_state or {}).get("event_confirmation_state") == "UNCONFIRMED"
            and unqualified_confirmed_assertion(visible)
        ):
            raise SimpleGeminiNewsroomError(
                "native_preview_epistemic_certainty_inflation", [destination]
            )
    intents = [
        {
            "destination": destination,
            "dispatch_state": "UNDISPATCHED",
            "article_identity": article_identity,
            "payload_state": "PREVIEW_ONLY_PENDING_CANONICAL_URL",
            "payload_sha256": _hash(payloads[destination]),
            "native_payload": dict(payloads[destination]),
            "canonical_url_state": "PENDING_NON_DISPATCHABLE",
            "rematerialization_after_real_substack_url_required": True,
            "epistemic_state": dict(epistemic_state or {}),
        }
        for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
    ]
    bundle = {
        "schema_version": NATIVE_PREVIEWS_SCHEMA_VERSION,
        "article_identity": article_identity,
        "final_validated_article_public_copy_sha256": _text_hash(
            _public_copy(article)
        ),
        "compiler_input_sha256": _hash(compiler_article),
        "canonical_url": pending_url,
        "canonical_url_state": "PENDING_NON_DISPATCHABLE",
        "rematerialization_after_real_substack_url_required": True,
        "epistemic_state": dict(epistemic_state or {}),
        "every_preview_preserves_epistemic_state": bool(epistemic_state),
        "package_count": len(payloads),
        "packages": payloads,
        "dispatch_state": "PREVIEW_ONLY_UNDISPATCHED",
        "public_write_performed": False,
        "provider_publication_writes": 0,
        "publication_coordinator_dispatch_count": 0,
        "unknown_write_count": 0,
    }
    return bundle, intents


def _build_simple_publication_lifecycle_plan(
    *,
    run_id: str,
    output_dir: Path,
    selected_candidate: Mapping[str, Any],
    selected_plan_entry: Mapping[str, Any],
    article: Mapping[str, Any],
    article_identity: str,
    native_previews: Mapping[str, Any],
    qualified_record: Mapping[str, Any],
    epistemic_state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Adapt one qualified Simple result to the existing durable coordinator contract.

    The plan deliberately contains no publisher/readback callable.  Derivative preview bytes
    remain pending and non-dispatchable; the coordinator's existing ``finalize_intent`` seam
    recompiles them only after strict Substack readback supplies a real canonical URL.
    """
    compiler_article = _reader_safe_native_article(
        article,
        article_mode=str(selected_plan_entry.get("article_mode") or ""),
        epistemic_state=epistemic_state,
    )
    context = {
        "schema_version": "contentops.simple_durable_run_context.v1",
        "run_id": run_id,
        "selection": dict(selected_candidate),
        "article": compiler_article,
        "media": {"assets": [], "delivery_only_assets": []},
        "epistemic_state": dict(epistemic_state or {}),
        "article_identity": article_identity,
        "article_content_sha256": _text_hash(_public_copy(article)),
        "compiler_input_sha256": _hash(compiler_article),
        "accepted_evidence_ids": list(
            qualified_record.get("accepted_evidence_ids") or []
        ),
        "accepted_evidence_sha256": str(
            qualified_record.get("accepted_evidence_sha256") or ""
        ),
        "public_write_performed": False,
    }
    _write_json(output_dir / "run_context_v1.json", context)

    preview_packages = dict(native_previews.get("packages") or {})
    destinations: list[dict[str, Any]] = []
    for destination in V1_REQUIRED_PUBLICATION_DESTINATIONS:
        registration = registration_for_destination(destination)
        preview_payload = preview_packages.get(destination)
        destinations.append(
            {
                "destination": destination,
                "platform": registration.platform,
                "surface": registration.surface,
                "transport_type": registration.transport_type,
                "transport_registry_version": REGISTRY_VERSION,
                "adapter": registration.adapter,
                "payload_hash": (
                    article_identity
                    if destination == "substack"
                    else _hash(preview_payload or {})
                ),
                "payload_hash_kind": (
                    "QUALIFIED_SIMPLE_ARTICLE_IDENTITY"
                    if destination == "substack"
                    else "PRE_CANONICAL_URL_TEMPLATE"
                ),
                "canonical_url": None,
                "canonical_url_dependency": registration.canonical_url_dependency,
                "canonical_url_state": (
                    "CANONICAL_SUBSTACK_TO_BE_ESTABLISHED"
                    if destination == "substack"
                    else "PENDING_NON_DISPATCHABLE"
                ),
                "expected_destination_identity": registration.expected_identity,
                "readiness_state": "JIT_VERIFICATION_REQUIRED",
                "text_only_supported": registration.text_only_supported,
                "delivery_media_required": registration.delivery_media_required,
                "rematerialization_after_real_substack_url_required": (
                    destination != "substack"
                ),
            }
        )

    package_identity = _hash(
        {
            "article_identity": article_identity,
            "article_content_sha256": context["article_content_sha256"],
            "compiler_input_sha256": context["compiler_input_sha256"],
            "epistemic_state": dict(epistemic_state or {}),
            "required_derivative_destinations": list(
                V1_REQUIRED_DERIVATIVE_DESTINATIONS
            ),
        }
    )
    plan_core = {
        "schema_version": "contentops.publication_plan.v1",
        "bridge_schema_version": PUBLICATION_BRIDGE_SCHEMA_VERSION,
        "run_id": run_id,
        "story_identity": str(selected_candidate.get("story_identity") or ""),
        "update_chain_identity": str(selected_candidate.get("story_identity") or ""),
        "resolved_article_mode": str(selected_plan_entry.get("article_mode") or ""),
        "editorial_classification": "QUALIFIED_SIMPLE_GEMINI_ARTICLE",
        "article_identity": article_identity,
        "article_content_sha256": context["article_content_sha256"],
        "compiler_input_sha256": context["compiler_input_sha256"],
        "accepted_evidence_ids": list(context["accepted_evidence_ids"]),
        "accepted_evidence_sha256": context["accepted_evidence_sha256"],
        "source_provenance_binding_preserved": True,
        "epistemic_state": dict(epistemic_state or {}),
        "publication_window": {"window_identity": run_id},
        "package_identity": package_identity,
        "output_dir": str(output_dir.resolve()),
        "artifact_refs": {
            "article_manifest": "article_manifest_v1.json",
            "qualified_article_record": "qualified_article_record_v1.json",
            "native_derivative_previews": "native_derivative_previews_v1.json",
            "derivative_intents": "derivative_intents_v1.json",
            "epistemic_state": (
                "simple_epistemic_state_v1.json" if epistemic_state else None
            ),
        },
        "quality_probation_policy_id": V1_QUALITY_PROBATION_POLICY_ID,
        "full_v1_distribution_required": True,
        "required_publication_destinations": list(
            V1_REQUIRED_PUBLICATION_DESTINATIONS
        ),
        "required_derivative_destinations": list(
            V1_REQUIRED_DERIVATIVE_DESTINATIONS
        ),
        "destinations": destinations,
        "skipped_derivative_destinations": [],
        "pre_substack_blockers": [],
        "transaction_readiness": "CANONICAL_READY_DERIVATIVES_DEFERRED",
        "transport_registry_version": REGISTRY_VERSION,
        "policy_mode_version": "AUTONOMOUS_DEFAULT:contentops.operating_mode.v1",
        "substack_first_dependency": True,
        "canonical_url_before_state": "PENDING_NON_DISPATCHABLE",
        "derivative_rematerialization_owner": (
            "CanonicalDestinationTransportRuntimeV1.finalize_intent"
        ),
        "bridge_model_call_count": 0,
        "bridge_source_get_count": 0,
        "adapter_callables_persisted": False,
        "secrets_persisted": False,
    }
    return {**plan_core, "plan_hash": _hash(plan_core)}


def run_v1_simple_gemini_newsroom(
    *,
    output_dir: str | Path,
    cutoff_utc: str,
    rolling_input: Mapping[str, Any] | None = None,
    published_memory: Sequence[Any] = (),
    capital_chronicle_context: Mapping[str, Any] | None = None,
    source_route_health: Mapping[str, Any] | None = None,
    attempted_candidate_ids: Sequence[str] = (),
    llm_invoke: LlmInvoke | None = None,
    evidence_loader: EvidenceLoader | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run one zero-write V1 opportunity through one bounded Simple-Gemini plan."""
    cutoff_utc = _iso_utc(cutoff_utc)
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    run_id = str(run_id or root.name)
    if rolling_input is None:
        rolling_input = load_rolling_x_headline_sidecars(
            cutoff_utc=cutoff_utc,
            sidecar_glob=canonical_headline_sidecar_glob(),
            window_hours=24.0,
        )
    candidates, sourceability_preselection = _candidate_packet_and_preselection(
        rolling_input,
        published_memory,
        source_route_health=source_route_health,
        attempted_candidate_ids=attempted_candidate_ids,
    )
    sourceability_path = root / "simple_sourceability_preselection_v1.json"
    _write_json(sourceability_path, sourceability_preselection)
    sourceability_summary = {
        "artifact_path": str(sourceability_path),
        "full_eligible_deduped_universe_count": sourceability_preselection[
            "full_eligible_deduped_universe_count"
        ],
        "ranking_order_changed": sourceability_preselection[
            "ranking_order_changed"
        ],
        "candidate_ids_entering_top_packet": list(
            sourceability_preselection["candidate_ids_entering_top_packet"]
        ),
        "candidate_ids_leaving_top_packet": list(
            sourceability_preselection["candidate_ids_leaving_top_packet"]
        ),
        "source_route_health_reused": sourceability_preselection[
            "source_route_health_reused"
        ],
        "same_production_day_source_blocked_candidate_exclusion_count": (
            sourceability_preselection[
                "same_production_day_source_blocked_candidate_exclusion_count"
            ]
        ),
        "same_production_day_source_blocked_candidate_exclusion_sha256": (
            sourceability_preselection[
                "same_production_day_source_blocked_candidate_exclusion_sha256"
            ]
        ),
        "same_production_day_candidate_retry_suppression_grants_authority": False,
        "model_or_provider_calls": 0,
        "network_gets": 0,
        "authority_granted": False,
    }
    if not candidates:
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "classification": "NO_PUBLICATION",
            "run_id": run_id,
            "cutoff_utc": cutoff_utc,
            "candidate_count": 0,
            "candidate_limit": MAX_SELECTION_CANDIDATES,
            "sourceability_preselection": sourceability_summary,
            "exact_next_blocker": "NO_USEFUL_CURRENT_HEADLINE_CANDIDATES",
            "ordering": ORDERING,
            "qualified_article_count": 0,
            "derivative_intent_count": 0,
            "logical_model_invocation_count": 0,
            "codex_runtime_model_call_count": 0,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
        }
        _write_json(root / "simple_gemini_newsroom_receipt_v1.json", receipt)
        return receipt

    memory_summary = _published_memory_summary(published_memory)
    selection_governed = {
        "cutoff_utc": cutoff_utc,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "candidate_packet_ordering": (
            "DETERMINISTIC_SOURCEABILITY_AWARE_WORK_ORDER_ONLY"
        ),
        "candidate_packet_ordering_grants_source_or_factual_authority": False,
        "published_memory_summary": memory_summary,
        "capital_chronicle_context_present": bool(capital_chronicle_context),
        "capital_chronicle_proprietary_claims_authorized_in_this_lane": False,
        "institutional_edge_mode_guide": _institutional_edge_mode_guide(),
    }
    candidate_ids = {row["candidate_id"] for row in candidates}
    try:
        selection, selection_receipt = _invoke(
            llm_invoke=llm_invoke,
            role_task_id=ROLE_V1_SIMPLE_SELECTION,
            logical_invocation_id=f"{run_id}:select",
            prompt=_selection_prompt(selection_governed),
            governed_input=selection_governed,
            validator=lambda text: _validate_selection_text(
                text, candidate_ids=candidate_ids
            ),
        )
    except SimpleGeminiNewsroomError as exc:
        if exc.code != "gemini_logical_invocation_blocked":
            raise
        blocked = _blocked_router_receipt(exc)
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "classification": "NO_PUBLICATION",
            "run_id": run_id,
            "cutoff_utc": cutoff_utc,
            "candidate_count": len(candidates),
            "candidate_limit": MAX_SELECTION_CANDIDATES,
            "exact_next_blocker": "GEMINI_SELECTION_LOGICAL_INVOCATION_BLOCKED",
            "blocked_logical_invocation": blocked,
            "published_memory_summary": memory_summary,
            "ordering": ORDERING,
            "qualified_article_count": 0,
            "derivative_intent_count": 0,
            "logical_model_invocation_count": 1,
            "model_receipts": [blocked] if blocked else [],
            "codex_runtime_model_call_count": 0,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
        }
        _write_json(root / "simple_gemini_newsroom_receipt_v1.json", receipt)
        return receipt
    selection_artifact = {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "selection": selection,
        "router_receipt": selection_receipt,
        "candidate_packet_hash": _hash(candidates),
        "candidate_count": len(candidates),
        "candidate_limit": MAX_SELECTION_CANDIDATES,
        "sourceability_preselection": sourceability_summary,
        "published_memory_summary": memory_summary,
        "public_write_performed": False,
    }
    _write_json(root / "simple_gemini_selection_v1.json", selection_artifact)
    if selection.get("status") == _SELECTION_STATUS_ABSTAIN:
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "classification": "NO_PUBLICATION",
            "run_id": run_id,
            "cutoff_utc": cutoff_utc,
            "candidate_count": len(candidates),
            "candidate_limit": MAX_SELECTION_CANDIDATES,
            "admitted_candidate_count": 0,
            "exact_next_blocker": "GEMINI_COORDINATOR_ABSTAINED_NO_USEFUL_STORY",
            "selection": selection,
            "ordering": ORDERING,
            "qualified_article_count": 0,
            "derivative_intent_count": 0,
            "logical_model_invocation_count": 1,
            "provider_attempt_count": int(selection_receipt.get("total_attempts") or 1),
            "model_receipts": [selection_receipt],
            "codex_runtime_model_call_count": 0,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
        }
        _write_json(root / "simple_gemini_newsroom_receipt_v1.json", receipt)
        return receipt

    candidate_by_id = {row["candidate_id"]: row for row in candidates}
    plan = list(selection["ordered_candidate_plan"])
    loader = evidence_loader or _default_evidence_loader(
        cutoff_utc,
        source_route_health=source_route_health,
    )
    request_count = 0
    candidate_attempt_history: list[dict[str, Any]] = []
    evidence_attempts: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    selected_plan_entry: dict[str, Any] | None = None
    selected_epistemic_state: dict[str, Any] | None = None
    source_pack: list[dict[str, Any]] = []
    for plan_index, plan_entry_value in enumerate(plan, start=1):
        plan_entry = dict(plan_entry_value)
        plan_entry.setdefault("plan_position", plan_index)
        plan_entry.setdefault("plan_role", "PRIMARY" if plan_index == 1 else "FALLBACK")
        candidate = candidate_by_id[str(plan_entry["candidate_id"])]
        request = _evidence_request(candidate, plan_entry)
        zero_request_document, _zero_request_blockers = canonical_x_report_document(
            request
        )
        if request_count >= MAX_SOURCE_REQUESTS and zero_request_document is None:
            candidate_attempt_history.append(
                {
                    "plan_position": plan_index,
                    "plan_role": plan_entry["plan_role"],
                    "candidate_id": candidate["candidate_id"],
                    "article_mode": plan_entry["article_mode"],
                    "status": "NOT_ATTEMPTED_SHARED_SOURCE_BUDGET_EXHAUSTED",
                    "blockers": ["shared_source_request_budget_exhausted"],
                    "source_request_count_for_attempt": 0,
                    "source_request_count_total": request_count,
                    "accepted_source_count": 0,
                }
            )
            continue
        request["remaining_admitted_candidate_count"] = len(plan) - plan_index
        try:
            evidence = dict(loader(request) or {})
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            evidence = {
                "status": "BLOCKED",
                "blockers": [redact_text(str(exc) or type(exc).__name__)],
                "evidence_documents": [],
                "provenance": {"request_count_for_call": 0},
            }
        provenance = dict(evidence.get("provenance") or {})
        for_call, request_count = _source_count_after_call(
            provenance, previous_total=request_count
        )
        if request_count > MAX_SOURCE_REQUESTS:
            raise SimpleGeminiNewsroomError(
                "shared_source_request_budget_exceeded",
                [f"observed={request_count}", f"limit={MAX_SOURCE_REQUESTS}"],
            )
        documents = [
            dict(row)
            for row in evidence.get("evidence_documents") or []
            if isinstance(row, Mapping) and row.get("public_claim_allowed") is True
        ][:MAX_SOURCE_DOCUMENTS]
        candidate_source_pack = _source_pack(documents)
        candidate_epistemic_state = (
            dict(evidence.get("epistemic_state") or {})
            if isinstance(evidence.get("epistemic_state"), Mapping)
            else {}
        )
        epistemic_blockers = (
            validate_epistemic_state(candidate_epistemic_state)
            if candidate_epistemic_state
            else []
        )
        basis = str(candidate_epistemic_state.get("evidence_basis") or "")
        if basis in {
            "TRUSTED_RELAY_ATTRIBUTED_REPORT",
            "TRUSTED_MARKET_RUMOR",
        } and plan_entry.get("article_mode") != "BREAKING_BRIEF":
            plan_entry["model_selected_article_mode"] = plan_entry[
                "article_mode"
            ]
            plan_entry["article_mode"] = "BREAKING_BRIEF"
            plan_entry["deterministic_mode_cap_reason"] = (
                "RELAY_OR_RUMOR_ONLY_EVIDENCE_DEPTH"
            )
            plan_entry["deterministic_mode_cap_uses_model_call"] = False
        status = (
            "SOURCE_QUALIFIED"
            if evidence.get("status") == "PASS"
            and candidate_source_pack
            and not epistemic_blockers
            else "SOURCE_BLOCKED"
        )
        blockers = _safe_source_blockers(
            [*(evidence.get("blockers") or []), *epistemic_blockers]
        )
        if status == "SOURCE_BLOCKED" and not blockers:
            blockers = ["accepted_source_pack_empty"]
        history = {
            "plan_position": plan_index,
            "plan_role": plan_entry["plan_role"],
            "candidate_id": candidate["candidate_id"],
            "article_mode": plan_entry["article_mode"],
            "model_selected_article_mode": plan_entry.get(
                "model_selected_article_mode", plan_entry["article_mode"]
            ),
            "deterministic_mode_cap_reason": plan_entry.get(
                "deterministic_mode_cap_reason"
            ),
            "selection_rationale": plan_entry["selection_rationale"],
            "research_queries": list(plan_entry["research_queries"]),
            "status": status,
            "blockers": blockers,
            "source_request_count_for_attempt": for_call,
            "source_request_count_total": request_count,
            "accepted_source_count": len(candidate_source_pack),
            "accepted_source_urls": [row["url"] for row in candidate_source_pack],
            "epistemic_state": candidate_epistemic_state,
            "source_route_history": [
                dict(row)
                for row in provenance.get("route_history") or []
                if isinstance(row, Mapping)
            ],
        }
        candidate_attempt_history.append(history)
        evidence_attempts.append(
            {
                **history,
                "request": request,
                "source_pack": candidate_source_pack,
                "epistemic_state": candidate_epistemic_state,
                "provenance": provenance,
            }
        )
        if status == "SOURCE_QUALIFIED":
            selected = candidate
            selected_plan_entry = plan_entry
            selected_epistemic_state = candidate_epistemic_state or None
            source_pack = candidate_source_pack
            break
    evidence_artifact = {
        "schema_version": "contentops.v1_simple_candidate_source_walk.v1",
        "status": "PASS" if selected is not None else "BLOCKED",
        "admitted_candidate_count": len(plan),
        "candidate_attempt_history": candidate_attempt_history,
        "evidence_attempts": evidence_attempts,
        "selected_candidate_id": selected["candidate_id"] if selected else None,
        "selected_source_pack": source_pack,
        "selected_epistemic_state": dict(selected_epistemic_state or {}),
        "request_count": request_count,
        "request_limit": MAX_SOURCE_REQUESTS,
        "model_calls_before_writer": 1,
        "codex_runtime_model_calls_before_writer": 0,
        "public_write_performed": False,
        "updated_source_route_health": _updated_source_route_health(loader),
    }
    _write_json(root / "simple_gemini_evidence_v1.json", evidence_artifact)
    if selected is None or selected_plan_entry is None or not source_pack:
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "classification": "NO_PUBLICATION",
            "run_id": run_id,
            "cutoff_utc": cutoff_utc,
            "candidate_count": len(candidates),
            "candidate_limit": MAX_SELECTION_CANDIDATES,
            "admitted_candidate_count": len(plan),
            "exact_next_blocker": "ALL_ADMITTED_CANDIDATES_SOURCE_RETRIEVAL_BLOCKED",
            "sourceability_preselection": sourceability_summary,
            "selection": selection,
            "candidate_attempt_history": candidate_attempt_history,
            "source_request_count": request_count,
            "ordering": ORDERING,
            "qualified_article_count": 0,
            "derivative_intent_count": 0,
            "logical_model_invocation_count": 1,
            "provider_attempt_count": int(selection_receipt.get("total_attempts") or 1),
            "model_receipts": [selection_receipt],
            "codex_runtime_model_call_count": 0,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
            "updated_source_route_health": _updated_source_route_health(loader),
        }
        _write_json(root / "simple_gemini_newsroom_receipt_v1.json", receipt)
        return receipt

    if selected_epistemic_state is not None:
        _write_json(
            root / "simple_epistemic_state_v1.json",
            selected_epistemic_state,
        )

    editorial_packet = _institutional_edge_writer_packet(
        article_mode=str(selected_plan_entry["article_mode"]),
        source_pack=source_pack,
    )
    _write_json(
        root / "simple_gemini_editorial_edge_v1.json",
        {
            "schema_version": "contentops.v1_simple_editorial_edge_adaptation.v1",
            "selected_product_mode": selected_plan_entry["article_mode"],
            "institutional_edge_editorial_packet": editorial_packet,
            "capital_chronicle_proprietary_claims_authorized_in_this_lane": False,
            "public_write_performed": False,
        },
    )
    writer_governed = {
        "cutoff_utc": cutoff_utc,
        "selected_candidate": selected,
        "article_mode": selected_plan_entry["article_mode"],
        "selection_rationale": selected_plan_entry["selection_rationale"],
        "source_pack": source_pack,
        "epistemic_state": dict(selected_epistemic_state or {}),
        "report_truth": (
            (selected_epistemic_state or {}).get("report_proposition")
        ),
        "event_truth": {
            "proposition": (selected_epistemic_state or {}).get(
                "event_proposition"
            ),
            "confirmation_state": (selected_epistemic_state or {}).get(
                "event_confirmation_state"
            ),
            "may_be_stated_as_confirmed": (selected_epistemic_state or {}).get(
                "underlying_event_may_be_stated_as_confirmed"
            ),
        },
        "analysis_boundaries": {
            "dependent_analysis_must_be_conditional": (
                (selected_epistemic_state or {}).get(
                    "analysis_must_be_conditional"
                )
            ),
            "capital_chronicle_proprietary_numeric_authority": False,
        },
        "capital_chronicle_context": dict(capital_chronicle_context or {}),
        "capital_chronicle_proprietary_claims_authorized_in_this_lane": False,
        "institutional_edge_editorial_packet": editorial_packet,
        "source_marker_contract": "every non-heading body paragraph uses [[SOURCE:SOURCE_N]]",
    }
    try:
        worker_output, worker_receipt = _invoke(
            llm_invoke=llm_invoke,
            role_task_id=ROLE_V1_SIMPLE_ARTICLE_WRITING,
            logical_invocation_id=f"{run_id}:write",
            prompt=_worker_prompt(writer_governed),
            governed_input=writer_governed,
            validator=_validate_worker_text,
        )
    except SimpleGeminiNewsroomError as exc:
        if exc.code != "gemini_logical_invocation_blocked":
            raise
        blocked = _blocked_router_receipt(exc)
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "classification": "NO_PUBLICATION",
            "run_id": run_id,
            "cutoff_utc": cutoff_utc,
            "candidate_count": len(candidates),
            "candidate_limit": MAX_SELECTION_CANDIDATES,
            "admitted_candidate_count": len(plan),
            "exact_next_blocker": "GEMINI_WRITER_LOGICAL_INVOCATION_BLOCKED",
            "selection": selection,
            "selected_candidate": selected,
            "candidate_attempt_history": candidate_attempt_history,
            "source_request_count": request_count,
            "blocked_logical_invocation": blocked,
            "model_receipts": [selection_receipt, *([blocked] if blocked else [])],
            "logical_model_invocation_count": 2,
            "codex_runtime_model_call_count": 0,
            "qualified_article_count": 0,
            "derivative_intent_count": 0,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
        }
        _write_json(root / "simple_gemini_newsroom_receipt_v1.json", receipt)
        return receipt
    revision_receipt: dict[str, Any] | None = None
    revision_performed = False
    worker_output, relay_normalization_count = _normalize_relay_attribution(
        worker_output, selected_epistemic_state
    )
    try:
        article, validation = _validate_article_against_source_pack(
            worker_output,
            source_pack,
            selected_candidate=selected,
            article_mode=str(selected_plan_entry["article_mode"]),
            epistemic_state=selected_epistemic_state,
        )
    except SimpleGeminiNewsroomError as first_error:
        if first_error.code != "deterministic_article_validation_failed":
            raise
        try:
            revised_output, revision_receipt = _invoke(
                llm_invoke=llm_invoke,
                role_task_id=ROLE_V1_SIMPLE_EDITORIAL_REVISION,
                logical_invocation_id=f"{run_id}:revise",
                prompt=_revision_prompt(writer_governed, worker_output, first_error.details),
                governed_input={
                    **writer_governed,
                    "prior_output_hash": _hash(worker_output),
                    "validation_blockers": first_error.details,
                },
                validator=_validate_worker_text,
            )
        except SimpleGeminiNewsroomError as exc:
            if exc.code != "gemini_logical_invocation_blocked":
                raise
            blocked = _blocked_router_receipt(exc)
            receipt = {
                "schema_version": SCHEMA_VERSION,
                "classification": "NO_PUBLICATION",
                "run_id": run_id,
                "cutoff_utc": cutoff_utc,
                "candidate_count": len(candidates),
                "candidate_limit": MAX_SELECTION_CANDIDATES,
                "admitted_candidate_count": len(plan),
                "exact_next_blocker": "GEMINI_REVISION_LOGICAL_INVOCATION_BLOCKED",
                "selection": selection,
                "selected_candidate": selected,
                "candidate_attempt_history": candidate_attempt_history,
                "source_request_count": request_count,
                "validation_blockers": first_error.details,
                "blocked_logical_invocation": blocked,
                "model_receipts": [selection_receipt, worker_receipt, *([blocked] if blocked else [])],
                "logical_model_invocation_count": 3,
                "codex_runtime_model_call_count": 0,
                "qualified_article_count": 0,
                "derivative_intent_count": 0,
                "public_write_performed": False,
                "provider_publication_writes": 0,
                "unknown_write_count": 0,
            }
            _write_json(root / "simple_gemini_newsroom_receipt_v1.json", receipt)
            return receipt
        revision_performed = True
        worker_output, revised_normalization_count = _normalize_relay_attribution(
            revised_output, selected_epistemic_state
        )
        relay_normalization_count += revised_normalization_count
        try:
            article, validation = _validate_article_against_source_pack(
                worker_output,
                source_pack,
                selected_candidate=selected,
                article_mode=str(selected_plan_entry["article_mode"]),
                epistemic_state=selected_epistemic_state,
            )
        except SimpleGeminiNewsroomError as second_error:
            receipt = {
                "schema_version": SCHEMA_VERSION,
                "classification": "NO_PUBLICATION",
                "run_id": run_id,
                "cutoff_utc": cutoff_utc,
                "candidate_count": len(candidates),
                "candidate_limit": MAX_SELECTION_CANDIDATES,
                "admitted_candidate_count": len(plan),
                "exact_next_blocker": "SINGLE_GEMINI_REVISION_EXHAUSTED",
                "selection": selection,
                "candidate_attempt_history": candidate_attempt_history,
                "validation_blockers": second_error.details,
                "source_request_count": request_count,
                "ordering": ORDERING,
                "logical_model_invocation_count": 3,
                "codex_runtime_model_call_count": 0,
                "qualified_article_count": 0,
                "derivative_intent_count": 0,
                "public_write_performed": False,
                "provider_publication_writes": 0,
                "unknown_write_count": 0,
                "deterministic_relay_attribution_normalization_count": (
                    relay_normalization_count
                ),
            }
            _write_json(root / "simple_gemini_newsroom_receipt_v1.json", receipt)
            return receipt

    article_manifest = {
        "schema_version": "contentops.v1_simple_article_manifest.v1",
        **article,
        "resolved_article_mode": selected_plan_entry["article_mode"],
        "story_identity": selected["story_identity"],
        "update_chain_identity": selected["story_identity"],
        "source_document_ids": [row["document_id"] for row in source_pack],
        "epistemic_state": dict(selected_epistemic_state or {}),
        "public_write_performed": False,
    }
    _write_json(root / "article_manifest_v1.json", article_manifest)
    validation_artifact = {
        **validation,
        "worker_router_receipt": worker_receipt,
        "revision_router_receipt": revision_receipt,
        "revision_performed": revision_performed,
        "maximum_revision_rounds": MAX_REVISION_ROUNDS,
        "epistemic_state": dict(selected_epistemic_state or {}),
    }
    _write_json(root / "simple_gemini_validation_v1.json", validation_artifact)

    article_identity = _text_hash(str(article["substack_body_markdown"]))
    try:
        native_previews, intents = _native_preview_bundle(
            article=article,
            article_mode=str(selected_plan_entry["article_mode"]),
            article_identity=article_identity,
            epistemic_state=selected_epistemic_state,
        )
    except SimpleGeminiNewsroomError as exc:
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "classification": "NO_PUBLICATION",
            "run_id": run_id,
            "cutoff_utc": cutoff_utc,
            "candidate_count": len(candidates),
            "candidate_limit": MAX_SELECTION_CANDIDATES,
            "admitted_candidate_count": len(plan),
            "exact_next_blocker": "NATIVE_DERIVATIVE_COMPILATION_BLOCKED",
            "validation_blockers": [exc.code, *exc.details],
            "candidate_attempt_history": candidate_attempt_history,
            "source_request_count": request_count,
            "logical_model_invocation_count": 2 + int(revision_performed),
            "codex_runtime_model_call_count": 0,
            "qualified_article_count": 0,
            "derivative_intent_count": 0,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
            "deterministic_relay_attribution_normalization_count": (
                relay_normalization_count
            ),
        }
        _write_json(root / "simple_gemini_newsroom_receipt_v1.json", receipt)
        return receipt
    _write_json(root / "native_derivative_previews_v1.json", native_previews)
    intents_artifact = {
        "schema_version": DERIVATIVE_INTENTS_SCHEMA_VERSION,
        "article_identity": article_identity,
        "intent_count": len(intents),
        "intents": intents,
        "canonical_substack_url_required_before_dispatch_materialization": True,
        "native_preview_package_path": str(
            root / "native_derivative_previews_v1.json"
        ),
        "preview_payloads_require_real_substack_url_rematerialization": True,
        "epistemic_state": dict(selected_epistemic_state or {}),
        "public_write_performed": False,
    }
    if len(intents) != 8 or {row["destination"] for row in intents} != set(
        V1_REQUIRED_DERIVATIVE_DESTINATIONS
    ):
        raise SimpleGeminiNewsroomError("exact_eight_derivative_intent_contract_failed")
    _write_json(root / "derivative_intents_v1.json", intents_artifact)

    accepted_documents = [
        {
            "document_id": row["document_id"],
            "source_url": row["url"],
            "canonical_content_sha256": row["canonical_content_sha256"],
            "published_at_utc": row["published_at_utc"],
            "published_at_source": row["published_at_source"],
        }
        for row in source_pack
    ]
    model_receipts = [selection_receipt, worker_receipt]
    if revision_receipt is not None:
        model_receipts.append(revision_receipt)
    record = build_current_zero_write_qualified_article_record(
        production_day_id=newsroom_production_day_id(cutoff_utc),
        parent_window_id=run_id,
        attempt_run_id=run_id,
        article=article_manifest,
        story_identity=selected["story_identity"],
        update_chain_identity=selected["story_identity"],
        resolved_article_mode=selected_plan_entry["article_mode"],
        accepted_evidence_documents=accepted_documents,
        editorial_provider="9router",
        editorial_model=str(worker_receipt.get("selected_model") or "9router-gemini"),
        editorial_reasoning_effort="HIGH",
        logical_model_invocation_count=len(model_receipts),
        derivative_package_intents=intents,
        epistemic_state=selected_epistemic_state,
    )
    persist_qualified_article_record(root, record)
    publication_lifecycle_plan = _build_simple_publication_lifecycle_plan(
        run_id=run_id,
        output_dir=root,
        selected_candidate=selected,
        selected_plan_entry=selected_plan_entry,
        article=article,
        article_identity=article_identity,
        native_previews=native_previews,
        qualified_record=record,
        epistemic_state=selected_epistemic_state,
    )

    receipt = {
        "schema_version": SCHEMA_VERSION,
        "classification": "PASS_V1_SIMPLE_GEMINI_ZERO_WRITE_ARTICLE",
        "run_id": run_id,
        "cutoff_utc": cutoff_utc,
        "candidate_count": len(candidates),
        "candidate_limit": MAX_SELECTION_CANDIDATES,
        "admitted_candidate_count": len(plan),
        "sourceability_preselection": sourceability_summary,
        "ordering": ORDERING,
        "selection": selection,
        "selected_candidate": selected,
        "selected_plan_entry": selected_plan_entry,
        "candidate_attempt_history": candidate_attempt_history,
        "source_request_count": request_count,
        "source_request_limit": MAX_SOURCE_REQUESTS,
        "accepted_source_count": len(source_pack),
        "epistemic_state": dict(selected_epistemic_state or {}),
        "supported_material_claim_count": validation["supported_material_claim_count"],
        "revision_performed": revision_performed,
        "logical_model_invocation_count": len(model_receipts),
        "logical_model_invocation_limit": MAX_LOGICAL_MODEL_INVOCATIONS,
        "provider_attempt_count": sum(int(row.get("total_attempts") or 1) for row in model_receipts),
        "model_receipts": model_receipts,
        "codex_runtime_model_call_count": 0,
        "qualified_article_count": 1,
        "derivative_intent_count": 8,
        "article_identity": article_identity,
        "article_path": str(root / "article_manifest_v1.json"),
        "native_derivative_preview_path": str(
            root / "native_derivative_previews_v1.json"
        ),
        "qualified_record_path": str(root / "qualified_article_record_v1.json"),
        "publication_lifecycle_plan": publication_lifecycle_plan,
        "publication_bridge_model_call_count": 0,
        "publication_bridge_source_get_count": 0,
        "publication_coordinator_remains_sole_public_write_owner": True,
        "public_write_performed": False,
        "provider_publication_writes": 0,
        "unknown_write_count": 0,
        "deterministic_relay_attribution_normalization_count": (
            relay_normalization_count
        ),
        "updated_source_route_health": _updated_source_route_health(loader),
    }
    _write_json(root / "simple_gemini_newsroom_receipt_v1.json", receipt)
    return receipt
