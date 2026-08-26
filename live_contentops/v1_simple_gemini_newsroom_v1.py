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
    ROLE_ARTICLE_WRITING,
    ROLE_EDITORIAL_REVISION,
    ROLE_NEWSROOM_ASSIGNMENT,
    routed_llm_invocation,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
    RetryBudget,
)
from live_contentops.public_secondary_evidence_loader_v1 import (
    BoundedPublicSecondaryEvidenceLoader,
)

SCHEMA_VERSION = "contentops.v1_simple_gemini_newsroom.v1"
SELECTION_SCHEMA_VERSION = "contentops.v1_simple_gemini_selection.v1"
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
MAX_PROVIDER_ATTEMPTS_PER_LOGICAL_INVOCATION = 2
MAX_REVISION_ROUNDS = 1

_SELECTION_STATUS_SELECT = "SELECT_STORY"
_SELECTION_STATUS_ABSTAIN = "ABSTAIN"
_VALID_CLAIM_KINDS = frozenset({"FACT", "NUMBER", "QUOTE", "CAUSALITY"})
_SOURCE_MARKER_RE = re.compile(r"\[\[SOURCE:(SOURCE_[1-4])\]\]")
_URL_RE = re.compile(r"https?://", re.IGNORECASE)

LlmInvoke = Callable[..., tuple[dict[str, Any], dict[str, Any]]]
EvidenceLoader = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class SimpleGeminiNewsroomError(RuntimeError):
    """Fail-closed simple-runtime error with a stable code and safe details."""

    def __init__(self, code: str, details: Sequence[str] | None = None) -> None:
        self.code = str(code)
        self.details = sorted({str(value) for value in details or [] if str(value)})
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


def _validate_selection_text(
    text: str, *, candidate_ids: set[str]
) -> tuple[bool, str | None, Any, str | None]:
    try:
        value = json.loads(str(text or ""))
    except json.JSONDecodeError:
        return False, "structured_output_malformed", None, "selection_json_invalid"
    if not isinstance(value, Mapping):
        return False, "structured_output_schema_invalid", None, "selection_object_required"
    allowed = {
        "schema_version",
        "status",
        "selected_candidate_id",
        "article_mode",
        "selection_rationale",
        "research_queries",
        "public_write_attempted",
    }
    if set(value) - allowed:
        return False, "structured_output_schema_invalid", None, "selection_unknown_fields"
    if value.get("schema_version") != SELECTION_SCHEMA_VERSION:
        return False, "structured_output_schema_invalid", None, "selection_schema_version_invalid"
    if value.get("public_write_attempted") is not False:
        return False, "publication_authority_failure", None, "selection_public_write_forbidden"
    status = str(value.get("status") or "")
    if status == _SELECTION_STATUS_ABSTAIN:
        if not str(value.get("selection_rationale") or "").strip():
            return False, "structured_output_schema_invalid", None, "abstain_rationale_required"
        return True, None, dict(value), None
    if status != _SELECTION_STATUS_SELECT:
        return False, "structured_output_schema_invalid", None, "selection_status_invalid"
    selected = str(value.get("selected_candidate_id") or "")
    mode = str(value.get("article_mode") or "")
    queries = value.get("research_queries")
    if selected not in candidate_ids:
        return False, "malformed_business_input", None, "selected_candidate_not_governed"
    if mode not in ARTICLE_MODES:
        return False, "structured_output_schema_invalid", None, "article_mode_invalid"
    if not isinstance(queries, list) or not 1 <= len(queries) <= 3:
        return False, "structured_output_schema_invalid", None, "research_query_count_invalid"
    cleaned = [" ".join(str(item or "").split()) for item in queries]
    if any(len(item) < 6 or len(item) > 180 or _URL_RE.search(item) for item in cleaned):
        return False, "structured_output_schema_invalid", None, "research_query_invalid"
    result = dict(value)
    result["research_queries"] = cleaned
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
        max_fallback_transitions=1,
        max_same_model_retries=0,
        max_structured_output_repair_attempts=0,
        max_cumulative_retry_sleep_seconds=0.0,
        wall_clock_budget_seconds=180.0,
        per_model_max_attempts=(1, 1),
    )


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
        raise SimpleGeminiNewsroomError(
            "gemini_logical_invocation_blocked",
            [
                str(role_task_id),
                str(summary.get("terminal_disposition") or "UNKNOWN"),
                str(summary.get("budget_exhausted_reason") or ""),
            ],
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
    contract = {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "status": "SELECT_STORY or ABSTAIN",
        "selected_candidate_id": "exact candidate_id when SELECT_STORY",
        "article_mode": list(ARTICLE_MODES),
        "selection_rationale": "short reason",
        "research_queries": ["1 to 3 query texts, never URLs"],
        "public_write_attempted": False,
    }
    return (
        "Choose at most one genuinely useful current Capital Chronicle story from GOVERNED_INPUT. "
        "Do not require evidence-ready/sourceability/readiness/media/SEO perfection before selection. "
        "Avoid exact published-memory duplicates and filler. If nothing is useful, ABSTAIN. "
        "For SELECT_STORY return one to three short research query texts that can locate reputable "
        "public reporting for the selected story. No tools, no URLs, no factual/numeric/publication authority. "
        "Do not select a proprietary Capital Chronicle forecast/probability/scenario/regime claim. "
        "Return strict JSON only using OUTPUT_CONTRACT.\nOUTPUT_CONTRACT:\n"
        + json.dumps(contract, sort_keys=True, ensure_ascii=False)
        + "\nGOVERNED_INPUT:\n"
        + json.dumps(governed, sort_keys=True, ensure_ascii=False)
    )


def _evidence_request(candidate: Mapping[str, Any], selection: Mapping[str, Any]) -> dict[str, Any]:
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
    material = {
        "candidate_id": candidate["candidate_id"],
        "headline_id": candidate["headline_id"],
        "article_mode": selection["article_mode"],
        "research_queries": list(selection["research_queries"]),
    }
    return {
        "cluster_id": candidate["candidate_id"],
        "headline_ids": [candidate["headline_id"]],
        "request_logical_hash": _hash(material),
        "story_evidence_scope_id": candidate["candidate_id"],
        "story_type": "selected_current_news",
        "requested_article_mode": selection["article_mode"],
        "effective_article_mode": selection["article_mode"],
        "required_evidence_capabilities": [
            "credible_event_confirmation",
            "basic_attributed_facts",
        ],
        "evidence_enrichment_context": {"requested": True},
        "story_context": {
            "leaf_summaries": [candidate["headline_text"]],
            "grounded_research_queries": list(selection["research_queries"]),
            "public_source_url_bindings": bindings,
        },
    }


def _default_evidence_loader(cutoff_utc: str) -> EvidenceLoader:
    return BoundedPublicSecondaryEvidenceLoader(
        evaluation_as_of_utc=cutoff_utc,
        max_requests=MAX_SOURCE_REQUESTS,
        max_requests_per_candidate=MAX_SOURCE_REQUESTS,
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
        "Write one useful concise Capital Chronicle article from GOVERNED_INPUT and SOURCE_PACK only. "
        "Do not browse or invent URLs. Do not expand factual scope beyond retrieved source bytes. "
        "Every non-heading body paragraph must contain at least one exact [[SOURCE:SOURCE_N]] marker. "
        "Every material fact, number, quotation, or causal assertion in title, dek, or body must have a binding. "
        "The exact title and exact dek must each appear as a claim_text binding. support_excerpt must be an exact "
        "substring of the cited SOURCE_PACK text. Use no proprietary Capital Chronicle numeric/forecast/scenario/"
        "probability/regime claim in this reset lane. Source timestamps are hints only; retrieved source provenance "
        "remains deterministic authority. Zero media is valid. Return strict JSON only.\nOUTPUT_CONTRACT:\n"
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
        "Revise the prior article once using only the same governed candidate and SOURCE_PACK. "
        "Fix exactly the deterministic blockers, do not add a source or expand factual scope, and return the complete strict object. "
        "Every body paragraph remains source-marker bound. Zero public write.\nBLOCKERS:\n"
        + json.dumps(list(blockers), sort_keys=True)
        + "\nPRIOR_OUTPUT:\n"
        + json.dumps(dict(prior), sort_keys=True, ensure_ascii=False)
        + "\nGOVERNED_INPUT:\n"
        + json.dumps(dict(governed), sort_keys=True, ensure_ascii=False)
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
    """Run one zero-write, one-article V1 opportunity through the simple Gemini path."""
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

    selection_governed = {
        "cutoff_utc": cutoff_utc,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "published_memory": [
            {
                "title": _memory_field(row, "title"),
                "story_identity": _memory_field(row, "story_identity"),
                "update_chain_identity": _memory_field(row, "update_chain_identity"),
            }
            for row in published_memory[-100:]
        ],
        "capital_chronicle_context_present": bool(capital_chronicle_context),
        "capital_chronicle_proprietary_claims_authorized_in_this_lane": False,
    }
    candidate_ids = {row["candidate_id"] for row in candidates}
    selection, selection_receipt = _invoke(
        llm_invoke=llm_invoke,
        role_task_id=ROLE_NEWSROOM_ASSIGNMENT,
        logical_invocation_id=f"{run_id}:select",
        prompt=_selection_prompt(selection_governed),
        governed_input=selection_governed,
        validator=lambda text: _validate_selection_text(text, candidate_ids=candidate_ids),
    )
    selection_artifact = {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "selection": selection,
        "router_receipt": selection_receipt,
        "candidate_packet_hash": _hash(candidates),
        "public_write_performed": False,
    }
    _write_json(root / "simple_gemini_selection_v1.json", selection_artifact)
    if selection.get("status") == _SELECTION_STATUS_ABSTAIN:
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "classification": "NO_PUBLICATION",
            "exact_next_blocker": "GEMINI_COORDINATOR_ABSTAINED_NO_USEFUL_STORY",
            "selection": selection,
            "ordering": ORDERING,
            "qualified_article_count": 0,
            "derivative_intent_count": 0,
            "logical_model_invocation_count": 1,
            "codex_runtime_model_call_count": 0,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
        }
        _write_json(root / "simple_gemini_newsroom_receipt_v1.json", receipt)
        return receipt

    selected = next(
        row for row in candidates if row["candidate_id"] == selection["selected_candidate_id"]
    )
    request = _evidence_request(selected, selection)
    loader = evidence_loader or _default_evidence_loader(cutoff_utc)
    evidence = dict(loader(request) or {})
    provenance = dict(evidence.get("provenance") or {})
    request_count = int(
        provenance.get("request_count_for_call")
        or provenance.get("request_count_for_candidate")
        or provenance.get("request_count")
        or 0
    )
    if request_count > MAX_SOURCE_REQUESTS:
        raise SimpleGeminiNewsroomError("selected_story_source_request_budget_exceeded")
    documents = [
        dict(row)
        for row in evidence.get("evidence_documents") or []
        if isinstance(row, Mapping) and row.get("public_claim_allowed") is True
    ][:MAX_SOURCE_DOCUMENTS]
    source_pack = _source_pack(documents)
    evidence_artifact = {
        "schema_version": "contentops.v1_simple_selected_story_evidence.v1",
        "selected_candidate_id": selected["candidate_id"],
        "request": request,
        "status": evidence.get("status"),
        "blockers": list(evidence.get("blockers") or []),
        "source_pack": source_pack,
        "provenance": provenance,
        "request_count": request_count,
        "request_limit": MAX_SOURCE_REQUESTS,
        "model_calls_before_writer": 1,
        "codex_runtime_model_calls_before_writer": 0,
        "public_write_performed": False,
    }
    _write_json(root / "simple_gemini_evidence_v1.json", evidence_artifact)
    if evidence.get("status") != "PASS" or not source_pack:
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "classification": "NO_PUBLICATION",
            "exact_next_blocker": "SELECTED_STORY_SOURCE_RETRIEVAL_BLOCKED",
            "selection": selection,
            "source_blockers": list(evidence.get("blockers") or []),
            "source_request_count": request_count,
            "ordering": ORDERING,
            "qualified_article_count": 0,
            "derivative_intent_count": 0,
            "logical_model_invocation_count": 1,
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
        "article_mode": selection["article_mode"],
        "selection_rationale": selection.get("selection_rationale"),
        "source_pack": source_pack,
        "capital_chronicle_context": dict(capital_chronicle_context or {}),
        "capital_chronicle_proprietary_claims_authorized_in_this_lane": False,
        "source_marker_contract": "every non-heading body paragraph uses [[SOURCE:SOURCE_N]]",
    }
    worker_output, worker_receipt = _invoke(
        llm_invoke=llm_invoke,
        role_task_id=ROLE_ARTICLE_WRITING,
        logical_invocation_id=f"{run_id}:write",
        prompt=_worker_prompt(writer_governed),
        governed_input=writer_governed,
        validator=_validate_worker_text,
    )
    revision_receipt: dict[str, Any] | None = None
    revision_performed = False
    try:
        article, validation = _validate_article_against_source_pack(worker_output, source_pack)
    except SimpleGeminiNewsroomError as first_error:
        if first_error.code != "deterministic_article_validation_failed":
            raise
        revised_output, revision_receipt = _invoke(
            llm_invoke=llm_invoke,
            role_task_id=ROLE_EDITORIAL_REVISION,
            logical_invocation_id=f"{run_id}:revise",
            prompt=_revision_prompt(writer_governed, worker_output, first_error.details),
            governed_input={
                **writer_governed,
                "prior_output_hash": _hash(worker_output),
                "validation_blockers": first_error.details,
            },
            validator=_validate_worker_text,
        )
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
                "exact_next_blocker": "SINGLE_GEMINI_REVISION_EXHAUSTED",
                "selection": selection,
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
        "resolved_article_mode": selection["article_mode"],
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
        resolved_article_mode=selection["article_mode"],
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
        "ordering": ORDERING,
        "selection": selection,
        "selected_candidate": selected,
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
