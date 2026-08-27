"""Simple Gemini-first V1 newsroom runtime.

This is the current low-complexity V1 editorial path. It deliberately does not run the
legacy evidence-ready candidate pool, Codex Desktop worker handoff, daily deficit catch-up
loop, or publication coordinator. One bounded Gemini selection chooses a useful current
headline, deterministic public retrieval acquires only that story's source bytes, one
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

from live_contentops.credential_redaction_policy import redact_text
from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
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

SCHEMA_VERSION = "contentops.v1_simple_gemini_newsroom.v2"
SELECTION_SCHEMA_VERSION = "contentops.v1_simple_gemini_selection.v2"
ARTICLE_SCHEMA_VERSION = "contentops.v1_simple_gemini_article.v1"
VALIDATION_SCHEMA_VERSION = "contentops.v1_simple_gemini_validation.v1"
DERIVATIVE_INTENTS_SCHEMA_VERSION = "contentops.v1_simple_derivative_intents.v1"

ORDERING = (
    "GEMINI_SELECT_THEN_BOUNDED_DETERMINISTIC_RETRIEVAL_THEN_"
    "GEMINI_WRITE_THEN_DETERMINISTIC_VALIDATE"
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
_SOURCE_MARKER_RE = re.compile(r"\[\[SOURCE:(SOURCE_[1-4])\]\]")
_URL_RE = re.compile(r"https?://", re.IGNORECASE)

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


def _memory_field(row: Any, key: str) -> str:
    if isinstance(row, Mapping):
        return str(row.get(key) or "")
    return str(getattr(row, key, "") or "")


def _candidate_packet(
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
        result.append(
            {
                "candidate_id": story_identity,
                "story_identity": story_identity,
                "headline_id": headline_id,
                "headline_text": text,
                "source_timestamp_utc": str(row.get("source_timestamp_utc") or ""),
                "source_account": _headline_account(row),
                "source_url": _headline_url(row),
            }
        )
        if len(result) >= MAX_SELECTION_CANDIDATES:
            break
    return result


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
        "Published-memory duplicates were filtered deterministically before this call. If nothing is useful, ABSTAIN. "
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
    if source_url.startswith("https://"):
        bindings.append(
            {
                "headline_id": candidate["headline_id"],
                "url": source_url,
                "source_timestamp_utc": candidate.get("source_timestamp_utc"),
            }
        )
    research_queries = list(plan_entry["research_queries"])
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
            "credible_event_confirmation",
            "basic_attributed_facts",
        ],
        "evidence_enrichment_context": {"requested": True},
        "story_context": {
            "leaf_summaries": [candidate["headline_text"]],
            "grounded_research_queries": research_queries,
            "planned_research_query_count": len(research_queries),
            "planned_research_query_set_sha256": _hash(research_queries),
            "locator_query_policy": "ORDERED_QUERY_PLAN_BOUNDED_BY_SHARED_RESOLVER_LEDGER",
            "public_source_url_bindings": bindings,
        },
    }


def _default_evidence_loader(cutoff_utc: str) -> EvidenceLoader:
    return SimpleFirstPartyAwareEvidenceResolver(
        evaluation_as_of_utc=cutoff_utc,
        max_requests=MAX_SOURCE_REQUESTS,
        timeout_seconds=12.0,
    )


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
        "Do not browse or invent URLs. Do not expand factual scope beyond retrieved source bytes. "
        "Every non-heading body paragraph must contain at least one exact [[SOURCE:SOURCE_N]] marker. "
        "Every material fact, number, quotation, or causal assertion in title, dek, or body must have a binding. "
        "The exact title and exact dek must each appear as a claim_text binding. support_excerpt must be an exact "
        "substring of the cited SOURCE_PACK text. Every claim_text and support_excerpt must be at least eight "
        "characters and must not be a bare label, symbol, or isolated number. Use no proprietary Capital Chronicle numeric/forecast/scenario/"
        "probability/regime claim in this reset lane. Source timestamps are hints only; retrieved source provenance "
        "remains deterministic authority. Zero media is valid. This call has no publication tools and must not claim "
        "a publication attempt: public_write_attempted MUST be the JSON boolean false, never true or a string. "
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


def _validate_article_against_source_pack(
    worker_output: Mapping[str, Any], source_pack: Sequence[Mapping[str, Any]]
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
    title = str(article.get("title") or "").strip()
    dek = str(article.get("dek") or "").strip()
    bound_claim_texts = {_normal(row.get("claim_text")) for row in claims}
    if _normal(title) not in bound_claim_texts:
        blockers.append("title_material_binding_missing")
    if _normal(dek) not in bound_claim_texts:
        blockers.append("dek_material_binding_missing")
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


def run_v1_simple_gemini_newsroom(
    *,
    output_dir: str | Path,
    cutoff_utc: str,
    rolling_input: Mapping[str, Any] | None = None,
    published_memory: Sequence[Any] = (),
    capital_chronicle_context: Mapping[str, Any] | None = None,
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
    candidates = _candidate_packet(rolling_input, published_memory)
    if not candidates:
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "classification": "NO_PUBLICATION",
            "run_id": run_id,
            "cutoff_utc": cutoff_utc,
            "candidate_count": 0,
            "candidate_limit": MAX_SELECTION_CANDIDATES,
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
        "published_memory_summary": memory_summary,
        "capital_chronicle_context_present": bool(capital_chronicle_context),
        "capital_chronicle_proprietary_claims_authorized_in_this_lane": False,
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
    loader = evidence_loader or _default_evidence_loader(cutoff_utc)
    request_count = 0
    candidate_attempt_history: list[dict[str, Any]] = []
    evidence_attempts: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    selected_plan_entry: dict[str, Any] | None = None
    source_pack: list[dict[str, Any]] = []
    for plan_index, plan_entry_value in enumerate(plan, start=1):
        plan_entry = dict(plan_entry_value)
        plan_entry.setdefault("plan_position", plan_index)
        plan_entry.setdefault("plan_role", "PRIMARY" if plan_index == 1 else "FALLBACK")
        candidate = candidate_by_id[str(plan_entry["candidate_id"])]
        if request_count >= MAX_SOURCE_REQUESTS:
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
        request = _evidence_request(candidate, plan_entry)
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
        status = (
            "SOURCE_QUALIFIED"
            if evidence.get("status") == "PASS" and candidate_source_pack
            else "SOURCE_BLOCKED"
        )
        blockers = _safe_source_blockers(evidence.get("blockers") or [])
        if status == "SOURCE_BLOCKED" and not blockers:
            blockers = ["accepted_source_pack_empty"]
        history = {
            "plan_position": plan_index,
            "plan_role": plan_entry["plan_role"],
            "candidate_id": candidate["candidate_id"],
            "article_mode": plan_entry["article_mode"],
            "selection_rationale": plan_entry["selection_rationale"],
            "research_queries": list(plan_entry["research_queries"]),
            "status": status,
            "blockers": blockers,
            "source_request_count_for_attempt": for_call,
            "source_request_count_total": request_count,
            "accepted_source_count": len(candidate_source_pack),
            "accepted_source_urls": [row["url"] for row in candidate_source_pack],
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
                "provenance": provenance,
            }
        )
        if status == "SOURCE_QUALIFIED":
            selected = candidate
            selected_plan_entry = plan_entry
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
        "request_count": request_count,
        "request_limit": MAX_SOURCE_REQUESTS,
        "model_calls_before_writer": 1,
        "codex_runtime_model_calls_before_writer": 0,
        "public_write_performed": False,
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
        }
        _write_json(root / "simple_gemini_newsroom_receipt_v1.json", receipt)
        return receipt

    writer_governed = {
        "cutoff_utc": cutoff_utc,
        "selected_candidate": selected,
        "article_mode": selected_plan_entry["article_mode"],
        "selection_rationale": selected_plan_entry["selection_rationale"],
        "source_pack": source_pack,
        "capital_chronicle_context": dict(capital_chronicle_context or {}),
        "capital_chronicle_proprietary_claims_authorized_in_this_lane": False,
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
    try:
        article, validation = _validate_article_against_source_pack(worker_output, source_pack)
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
        worker_output = revised_output
        try:
            article, validation = _validate_article_against_source_pack(
                worker_output, source_pack
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
        "public_write_performed": False,
    }
    _write_json(root / "article_manifest_v1.json", article_manifest)
    validation_artifact = {
        **validation,
        "worker_router_receipt": worker_receipt,
        "revision_router_receipt": revision_receipt,
        "revision_performed": revision_performed,
        "maximum_revision_rounds": MAX_REVISION_ROUNDS,
    }
    _write_json(root / "simple_gemini_validation_v1.json", validation_artifact)

    article_identity = _text_hash(str(article["substack_body_markdown"]))
    intents = [
        {
            "destination": str(destination),
            "dispatch_state": "UNDISPATCHED",
            "article_identity": article_identity,
            "payload_state": "DEFERRED_UNTIL_CANONICAL_SUBSTACK_URL",
            "payload_sha256": None,
        }
        for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
    ]
    intents_artifact = {
        "schema_version": DERIVATIVE_INTENTS_SCHEMA_VERSION,
        "article_identity": article_identity,
        "intent_count": len(intents),
        "intents": intents,
        "canonical_substack_url_required_before_payload_materialization": True,
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
    )
    persist_qualified_article_record(root, record)

    receipt = {
        "schema_version": SCHEMA_VERSION,
        "classification": "PASS_V1_SIMPLE_GEMINI_ZERO_WRITE_ARTICLE",
        "run_id": run_id,
        "cutoff_utc": cutoff_utc,
        "candidate_count": len(candidates),
        "candidate_limit": MAX_SELECTION_CANDIDATES,
        "admitted_candidate_count": len(plan),
        "ordering": ORDERING,
        "selection": selection,
        "selected_candidate": selected,
        "selected_plan_entry": selected_plan_entry,
        "candidate_attempt_history": candidate_attempt_history,
        "source_request_count": request_count,
        "source_request_limit": MAX_SOURCE_REQUESTS,
        "accepted_source_count": len(source_pack),
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
        "qualified_record_path": str(root / "qualified_article_record_v1.json"),
        "publication_coordinator_remains_sole_public_write_owner": True,
        "public_write_performed": False,
        "provider_publication_writes": 0,
        "unknown_write_count": 0,
    }
    _write_json(root / "simple_gemini_newsroom_receipt_v1.json", receipt)
    return receipt
