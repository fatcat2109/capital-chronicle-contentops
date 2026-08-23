"""Targeted governed evidence receipts for ranked rolling-X stories."""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit

from live_contentops.cc_evidence_bridge_v2 import (
    build_evidence_packet_from_cc_root,
    validate_evidence_packet,
)
from live_contentops.cc_publication_authority_v1 import (
    PUBLICATION_PACKET_AVAILABLE,
    build_publication_authorized_projection,
    resolve_publication_authority,
    validate_projection_for_consumer,
)
from live_contentops.freshness_market_state_v2 import evaluate_freshness
from live_contentops.claim_evidence_contract_v1 import (
    build_claim_evidence_contract,
    build_minimum_trustworthy_evidence_packet,
    requires_enhanced_evidence_review,
    summarize_evidence_substance,
)
from live_contentops.source_capability_registry_v2 import (
    effective_rolling_x_capability_registry,
    product_mode_evidence_depth,
    resolve_story_capabilities,
)

PUBLICATION_AUTHORIZED = "PASS_PUBLICATION_AUTHORIZED"
MARKET_CAPABILITIES = frozenset({"current_market_snapshot", "prior_close"})
EVIDENCE_LOADER_BUDGET_BLOCKERS = frozenset({
    "official_source_request_budget_exhausted",
    "public_source_request_budget_exhausted",
    "public_source_candidate_request_budget_exhausted",
})
TRUSTED_PROFESSIONAL_FEED_HANDLES = frozenset({"financialjuice"})
WEEK_AHEAD_PRODUCT_MODE = "WEEK_AHEAD_OR_WATCH"
WEEK_AHEAD_REQUIRED_CAPABILITIES = frozenset({
    "official_schedule",
    "scheduled_event_identity",
    "scheduled_event_date_time",
})
CODEX_SOURCE_DISCOVERY_SCHEMA_VERSION = "contentops.codex_source_discovery_urls.v1"
CODEX_SOURCE_DISCOVERY_TRIGGER_REASONS = frozenset(
    {"NO_VIABLE_DETERMINISTIC_PATH", "BOUNDED_ACCESS_FAILURE"}
)
_DISCOVERY_FAILURE_MARKERS = (
    "401",
    "403",
    "404",
    "access",
    "budget",
    "dead_link",
    "evidence_documents_missing",
    "exact_official_source_url_unavailable",
    "paywall",
    "public_source_unavailable",
    "waf",
)


def validate_codex_source_discovery_contract(
    contract: Mapping[str, Any], *, request: Mapping[str, Any]
) -> dict[str, Any]:
    """Accept URL locators only; model/search text can never enter evidence."""
    allowed_keys = {
        "schema_version",
        "story_identity",
        "headline_ids",
        "trigger_reason",
        "prior_blockers",
        "candidate_urls",
        "search_call_id",
        "searched_at_utc",
        "search_snippets_included",
        "model_summaries_included",
        "candidate_urls_are_evidence",
        "factual_or_numeric_authority_granted",
        "publication_authority_granted",
    }
    extra = sorted(set(contract).difference(allowed_keys))
    if extra:
        raise ValueError("codex_source_discovery_untrusted_fields:" + ",".join(extra))
    if contract.get("schema_version") != CODEX_SOURCE_DISCOVERY_SCHEMA_VERSION:
        raise ValueError("codex_source_discovery_schema_invalid")
    if str(contract.get("story_identity") or "") != str(
        request.get("cluster_id") or ""
    ):
        raise ValueError("codex_source_discovery_story_identity_mismatch")
    if sorted(str(value) for value in contract.get("headline_ids") or []) != sorted(
        str(value) for value in request.get("headline_ids") or []
    ):
        raise ValueError("codex_source_discovery_headline_identity_mismatch")
    trigger_reason = str(contract.get("trigger_reason") or "")
    if trigger_reason not in CODEX_SOURCE_DISCOVERY_TRIGGER_REASONS:
        raise ValueError("codex_source_discovery_trigger_invalid")
    prior_blockers = [str(value) for value in contract.get("prior_blockers") or []]
    blocker_text = " ".join(prior_blockers).casefold()
    if not prior_blockers or not any(
        marker in blocker_text for marker in _DISCOVERY_FAILURE_MARKERS
    ):
        raise ValueError("codex_source_discovery_prior_failure_unproven")
    if (
        contract.get("search_snippets_included") is not False
        or contract.get("model_summaries_included") is not False
        or contract.get("candidate_urls_are_evidence") is not False
        or contract.get("factual_or_numeric_authority_granted") is not False
        or contract.get("publication_authority_granted") is not False
    ):
        raise ValueError("codex_source_discovery_authority_contract_invalid")

    from live_contentops.official_primary_evidence_loader_v1 import (
        OFFICIAL_HOSTS_BY_FAMILY,
    )
    from live_contentops.public_secondary_evidence_loader_v1 import (
        REPUTABLE_SECONDARY_HOSTS,
    )

    official_hosts = {
        host
        for family_hosts in OFFICIAL_HOSTS_BY_FAMILY.values()
        for host in family_hosts
    }
    candidate_urls = list(
        dict.fromkeys(str(value) for value in contract.get("candidate_urls") or [])
    )
    if not 1 <= len(candidate_urls) <= 4:
        raise ValueError("codex_source_discovery_candidate_count_invalid")
    normalized_candidates: list[dict[str, str]] = []
    for url in candidate_urls:
        parsed = urlsplit(url)
        host = str(parsed.hostname or "").casefold()
        if (
            parsed.scheme != "https"
            or not host
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in {None, 443}
        ):
            raise ValueError("codex_source_discovery_public_https_identity_invalid")
        source_class = (
            "REGISTERED_OFFICIAL_PRIMARY"
            if host in official_hosts
            else "REPUTABLE_PUBLIC_SECONDARY"
            if host in REPUTABLE_SECONDARY_HOSTS
            else ""
        )
        if not source_class:
            raise ValueError("codex_source_discovery_host_policy_rejected")
        normalized_candidates.append(
            {"url": url, "host": host, "source_class": source_class}
        )
    normalized = {
        "schema_version": CODEX_SOURCE_DISCOVERY_SCHEMA_VERSION,
        "story_identity": str(contract.get("story_identity") or ""),
        "headline_ids": sorted(
            str(value) for value in contract.get("headline_ids") or []
        ),
        "trigger_reason": trigger_reason,
        "prior_blockers": sorted(set(prior_blockers)),
        "search_call_id": str(contract.get("search_call_id") or ""),
        "searched_at_utc": str(contract.get("searched_at_utc") or ""),
        "candidates": normalized_candidates,
        "candidate_urls_are_evidence": False,
        "deterministic_live_retrieval_required": True,
        "search_snippet_or_model_summary_authority": False,
        "factual_or_numeric_authority_granted": False,
        "publication_authority_granted": False,
    }
    normalized["discovery_contract_sha256"] = sha256(
        json.dumps(
            normalized, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()
    return normalized


def _apply_codex_source_discovery(
    request: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    contract = request.get("codex_source_discovery")
    if contract is None:
        return dict(request), None
    if not isinstance(contract, Mapping):
        raise ValueError("codex_source_discovery_contract_not_object")
    receipt = validate_codex_source_discovery_contract(contract, request=request)
    context = dict(request.get("story_context") or {})
    headline_id = str((request.get("headline_ids") or [""])[0])
    public_bindings = [
        dict(row)
        for row in context.get("public_source_url_bindings") or []
        if isinstance(row, Mapping)
    ]
    official_bindings = [
        dict(row)
        for row in context.get("official_source_url_bindings") or []
        if isinstance(row, Mapping)
    ]
    discovered_public: list[dict[str, Any]] = []
    discovered_official: list[dict[str, Any]] = []
    for candidate in receipt["candidates"]:
        binding = {
            "headline_id": headline_id,
            "url": candidate["url"],
            "codex_discovery_contract_sha256": receipt[
                "discovery_contract_sha256"
            ],
            "locator_only": True,
            "locator_grants_factual_or_numeric_authority": False,
        }
        if candidate["source_class"] == "REGISTERED_OFFICIAL_PRIMARY":
            discovered_official.append(binding)
        else:
            discovered_public.append(binding)
    context["public_source_url_bindings"] = discovered_public + public_bindings
    context["official_source_url_bindings"] = discovered_official + official_bindings
    context["public_source_urls"] = list(
        dict.fromkeys(
            [row["url"] for row in discovered_public]
            + [str(value) for value in context.get("public_source_urls") or []]
        )
    )
    context["official_source_urls"] = list(
        dict.fromkeys(
            [row["url"] for row in discovered_official]
            + [str(value) for value in context.get("official_source_urls") or []]
        )
    )
    return {**dict(request), "story_context": context}, receipt


def _with_cc_authority_evidence(
    receipt: Mapping[str, Any],
    *,
    packet: Mapping[str, Any] | None,
    resolution: Mapping[str, Any],
    consume_projection: bool,
) -> dict[str, Any]:
    result = dict(receipt)
    projection: dict[str, Any] = {}
    projection_blockers: list[str] = []
    if resolution.get("state") == PUBLICATION_PACKET_AVAILABLE and packet is not None:
        try:
            projection = build_publication_authorized_projection(packet, resolution)
            projection_blockers = validate_projection_for_consumer(
                projection, consumer="v1_article"
            )
        except ValueError as exc:
            projection_blockers = [str(exc)]
    consumed = bool(consume_projection and projection and not projection_blockers)
    result["capital_chronicle_publication_authority"] = dict(resolution)
    result["publication_authorized_cc_projection"] = projection if consumed else {}
    result["cc_authority_utilization"] = {
        "packet_discovered": packet is not None,
        "packet_selected": resolution.get("packet_id") if packet is not None else None,
        "authority_class": resolution.get("authority_class"),
        "packet_sha256": resolution.get("packet_sha256"),
        "authorized_claim_count_available": len(projection.get("exact_numeric_claims") or []),
        "authorized_series_count_available": len(projection.get("exact_time_series") or {}),
        "authorized_chart_count_available": len(projection.get("exact_chart_inputs") or []),
        "authorized_claim_count_consumed": (
            len(projection.get("exact_numeric_claims") or []) if consumed else 0
        ),
        "authorized_series_count_consumed": (
            len(projection.get("exact_time_series") or {}) if consumed else 0
        ),
        "authorized_chart_count_consumed": (
            len(projection.get("exact_chart_inputs") or []) if consumed else 0
        ),
        "zero_use_reason": (
            None
            if consumed
            else "PUBLICATION_AUTHORIZED_CC_NOT_REQUIRED_BY_EFFECTIVE_STORY_CAPABILITY"
            if resolution.get("state") == PUBLICATION_PACKET_AVAILABLE
            else (resolution.get("reason_codes") or ["PUBLICATION_PACKET_NOT_AVAILABLE"])[0]
        ),
        "projection_validation_blockers": projection_blockers,
        "values_regenerated_or_repaired": False,
        "llm_numeric_authority": False,
    }
    return result


def _restrict_grounded_packet_to_documents(
    packet: Mapping[str, Any], documents: list[dict[str, Any]]
) -> dict[str, Any]:
    """Keep model research facts only when every bound source survived hard filtering."""
    from live_contentops.grounded_news_research_v1 import _statement_supported

    allowed_document_ids = {
        str(row.get("document_id") or row.get("evidence_id") or "")
        for row in documents
    } - {""}
    sources = [
        dict(row)
        for row in packet.get("sources") or []
        if isinstance(row, Mapping)
        and str(row.get("evidence_document_id") or "") in allowed_document_ids
    ]
    allowed_refs = {str(row.get("source_ref") or "") for row in sources} - {""}
    documents_by_id = {
        str(row.get("document_id") or row.get("evidence_id") or ""): row
        for row in documents
    }
    documents_by_ref = {
        str(row.get("source_ref") or ""): documents_by_id[
            str(row.get("evidence_document_id") or "")
        ]
        for row in sources
        if str(row.get("evidence_document_id") or "") in documents_by_id
    }
    facts: list[dict[str, Any]] = []
    for row in packet.get("confirmed_facts") or []:
        if not isinstance(row, Mapping):
            continue
        refs = {str(value) for value in row.get("source_refs") or []} - {""}
        surviving_refs = sorted(refs.intersection(allowed_refs))
        surviving_documents = [
            documents_by_ref[ref]
            for ref in surviving_refs
            if ref in documents_by_ref
        ]
        if surviving_documents and _statement_supported(
            str(row.get("factual_statement") or ""), surviving_documents
        ):
            facts.append({**dict(row), "source_refs": surviving_refs})
    numeric = [
        dict(row)
        for row in packet.get("attributed_numeric_facts") or []
        if isinstance(row, Mapping)
        and str(row.get("source_ref") or "") in allowed_refs
    ]
    result = dict(packet)
    result["sources"] = sources
    result["confirmed_facts"] = facts
    result["attributed_numeric_facts"] = numeric
    result["post_filter_accepted_evidence_document_ids"] = sorted(
        allowed_document_ids
    )
    result["post_filter_removed_fact_count"] = max(
        0, len(list(packet.get("confirmed_facts") or [])) - len(facts)
    )
    if facts:
        result["core_factual_proposition"] = str(
            facts[0].get("factual_statement") or ""
        )
        result["research_status"] = "PASS"
    else:
        result["core_factual_proposition"] = ""
        result["research_status"] = "BLOCKED"
    unhashed = {key: value for key, value in result.items() if key != "research_logical_hash"}
    result["research_logical_hash"] = sha256(
        json.dumps(unhashed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return result


def _deterministic_official_schedule_facts(
    documents: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Revalidate exact extracted schedule rows against their accepted official bytes."""
    facts: list[dict[str, Any]] = []
    blockers: list[str] = []
    for document in documents:
        rows = document.get("scheduled_event_rows")
        if not isinstance(rows, list) or not rows:
            continue
        document_id = str(document.get("document_id") or document.get("evidence_id") or "")
        content_hash = str(
            document.get("canonical_content_sha256")
            or document.get("content_sha256")
            or document.get("raw_sha256")
            or ""
        )
        authority = str(document.get("source_authority_class") or "")
        source_text = " ".join(
            re.sub(
                r"<[^>]+>",
                " ",
                html.unescape(str(document.get("canonical_content_text") or "")),
            ).split()
        )
        for index, raw in enumerate(rows):
            if not isinstance(raw, Mapping):
                blockers.append(f"official_schedule_row_{index}_not_object")
                continue
            row = dict(raw)
            date_text = " ".join(str(row.get("date_text") or "").split())
            time_text = " ".join(str(row.get("time_text") or "").split())
            event_name = " ".join(str(row.get("event_name") or "").split())
            exact_text = f"{date_text} {time_text} — {event_name}"
            exact_hash = sha256(exact_text.encode("utf-8")).hexdigest()
            valid = bool(
                authority == "official_public_primary_source"
                and document.get("public_claim_allowed") is True
                and document_id
                and content_hash
                and date_text
                and time_text
                and event_name
                and str(row.get("source_text") or "") == exact_text
                and str(row.get("source_text_sha256") or "") == exact_hash
                and str(row.get("evidence_document_id") or "") == document_id
                and str(row.get("source_content_sha256") or "") == content_hash
                and all(value in source_text for value in (date_text, time_text, event_name))
                and list(row.get("inferred_fields") or []) == []
                and row.get("llm_factual_or_numeric_authority") is False
                and row.get("publication_authority") is False
            )
            if not valid:
                blockers.append(f"official_schedule_row_{index}_binding_invalid")
                continue
            grounded_ref = str(document.get("grounded_source_ref") or "")
            facts.append({
                "fact_id": "schedule-" + exact_hash[:20],
                "factual_statement": exact_text,
                "source_refs": [grounded_ref] if grounded_ref else [],
                "evidence_document_id": document_id,
                "source_content_sha256": content_hash,
                "schedule_row_id": row.get("schedule_row_id"),
                "source_text_sha256": exact_hash,
                "event_name": event_name,
                "date_text": date_text,
                "time_text": time_text,
                "period_or_edition_label": row.get("period_or_edition_label"),
                "confidence_class": "HIGH",
                "direct_or_inferred": "DIRECT",
                "attribution_required": False,
                "binding_method": "DETERMINISTIC_EXACT_OFFICIAL_SCHEDULE_ROW",
                "llm_factual_or_numeric_authority": False,
                "publication_authority": False,
            })
    return facts, blockers


def _merge_deterministic_schedule_facts(
    packet: Mapping[str, Any], facts: list[dict[str, Any]]
) -> dict[str, Any]:
    """Keep exact official schedule facts even when model synthesis omitted them."""
    result = dict(packet)
    bound_facts = [dict(row) for row in facts if row.get("source_refs")]
    existing = [
        dict(row) for row in result.get("confirmed_facts") or [] if isinstance(row, Mapping)
    ]
    existing_statements = {
        str(row.get("factual_statement") or "").casefold() for row in existing
    }
    deterministic_missing_from_model = [
        row
        for row in bound_facts
        if str(row.get("factual_statement") or "").casefold() not in existing_statements
    ]
    result["confirmed_facts"] = [*bound_facts, *[
        row
        for row in existing
        if str(row.get("factual_statement") or "").casefold()
        not in {
            str(fact.get("factual_statement") or "").casefold()
            for fact in bound_facts
        }
    ]]
    result["deterministic_official_schedule_facts"] = bound_facts
    result["model_omitted_deterministic_schedule_fact_count"] = max(
        int(result.get("model_omitted_deterministic_schedule_fact_count") or 0),
        len(deterministic_missing_from_model),
    )
    if bound_facts:
        result["core_factual_proposition"] = bound_facts[0]["factual_statement"]
        result["core_proposition_source_refs"] = list(bound_facts[0]["source_refs"])
        result["suggested_article_mode"] = WEEK_AHEAD_PRODUCT_MODE
        result["week_ahead_mode_preservation_basis"] = (
            "EXACT_DETERMINISTIC_OFFICIAL_SCHEDULE_FACTS"
        )
    return result


def _minimum_or_enhanced_evidence(
    request: Mapping[str, Any], documents: list[dict[str, Any]]
) -> tuple[bool, dict[str, Any], dict[str, Any]]:
    """Apply compact ordinary evidence or the enhanced high-risk claim contract."""
    if requires_enhanced_evidence_review(request):
        contract = build_claim_evidence_contract(request, documents)
        return contract.get("status") == "PASS", {}, contract
    packet = build_minimum_trustworthy_evidence_packet(request, documents)
    return packet.get("status") == "PASS", packet, {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sanitized_evidence_loader_error(prefix: str, exc: Exception) -> str:
    """Preserve stable budget truth while redacting arbitrary exception text."""
    exact = str(exc).strip()
    if exact in EVIDENCE_LOADER_BUDGET_BLOCKERS:
        return exact
    return prefix + ":" + type(exc).__name__


def _exact_bound_official_families(
    request: Mapping[str, Any],
    official_hosts_by_family: Mapping[str, Any],
) -> set[str]:
    """Authorize optional official acquisition only from exact headline-bound allowlisted hosts."""
    context = request.get("story_context")
    context = context if isinstance(context, Mapping) else {}
    headline_ids = {str(value) for value in (request.get("headline_ids") or [])}
    hosts: set[str] = set()
    for row in context.get("official_source_url_bindings") or []:
        if not isinstance(row, Mapping):
            continue
        if str(row.get("headline_id") or "") not in headline_ids:
            continue
        try:
            parsed = urlsplit(str(row.get("url") or ""))
        except ValueError:
            continue
        if parsed.scheme != "https" or parsed.username or parsed.password:
            continue
        host = str(parsed.hostname or "").casefold()
        if host:
            hosts.add(host)
    return {
        str(family)
        for family, allowed_hosts in official_hosts_by_family.items()
        if hosts.intersection({str(host).casefold() for host in allowed_hosts})
    }


def _blocked_receipt(
    request: Mapping[str, Any],
    blockers: list[str],
    *,
    documents: list[dict[str, Any]] | None = None,
    supplied: list[str] | None = None,
    evidence_acquisition_provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": "BLOCKED",
        "cluster_id": request.get("cluster_id"),
        "headline_ids": list(request.get("headline_ids") or []),
        "provided_evidence_capabilities": sorted(set(supplied or [])),
        "evidence_documents": list(documents or []),
        "capital_chronicle_authority_verified": False,
        "numeric_evidence_required": bool(
            request.get(
                "capital_chronicle_numeric_or_analytical_authority_required"
            )
        ),
        "blockers": sorted(set(blockers)),
        "publication_authority": False,
        "editorial_mode_contract": dict(
            request.get("editorial_mode_contract") or {}
        ),
        "evidence_acquisition_provenance": dict(evidence_acquisition_provenance or {}),
    }


def _exact_binding_blockers(
    packet: Mapping[str, Any], request: Mapping[str, Any]
) -> list[str]:
    binding = packet.get("rolling_x_story_binding")
    if not isinstance(binding, Mapping):
        return ["governed_rolling_x_story_binding_missing"]
    blockers = []
    if str(binding.get("cluster_id") or "") != str(request.get("cluster_id") or ""):
        blockers.append("governed_evidence_cluster_binding_mismatch")
    if [str(value) for value in (binding.get("headline_ids") or [])] != [
        str(value) for value in (request.get("headline_ids") or [])
    ]:
        blockers.append("governed_evidence_headline_binding_mismatch")
    if str(binding.get("request_logical_hash") or "") != str(
        request.get("request_logical_hash") or ""
    ):
        blockers.append("governed_evidence_request_hash_mismatch")
    return blockers


def _document_receipts(
    packet: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    freshness_state: str,
    official_primary_required: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    documents: list[dict[str, Any]] = []
    blockers: list[str] = []
    binding = dict(packet.get("rolling_x_story_binding") or {})
    provenance = dict(packet.get("provenance") or {})
    packet_hash = (
        packet.get("logical_hash")
        or packet.get("content_sha256")
        or (packet.get("governed_contract") or {}).get("upstream_packet_sha256")
        or (provenance.get("publication_packet") or {}).get("sha256")
    )
    known_at = (
        provenance.get("retrieved_at_utc")
        or packet.get("generated_at_utc")
        or packet.get("as_of_utc")
    )
    for index, raw in enumerate(packet.get("official_source_documents") or []):
        if not isinstance(raw, Mapping):
            continue
        row = dict(raw)
        source_url = row.get("source_url") or row.get("data_url")
        source_identity = row.get("publisher") or row.get("source_id")
        authority_class = row.get("source_authority_class") or row.get(
            "authority_class"
        )
        content_hash = (
            row.get("raw_sha256")
            or row.get("content_sha256")
            or row.get("canonical_content_sha256")
            or packet_hash
        )
        missing = []
        if not source_url:
            missing.append("source_url")
        if not source_identity:
            missing.append("source_identity")
        if not authority_class:
            missing.append("source_authority_class")
        elif official_primary_required and (
            authority_class != "official_public_primary_source"
        ):
            missing.append("official_primary_source_authority")
        if not known_at:
            missing.append("known_at_utc")
        if not content_hash:
            missing.append("content_sha256")
        if row.get("public_claim_allowed") is not True:
            missing.append("public_claim_permission")
        if missing:
            blockers.extend(
                f"official_evidence_document_{index}_missing:{field}"
                for field in missing
            )
            continue
        documents.append(
            {
                **row,
                "source_url": source_url,
                "source_identity": source_identity,
                "source_authority_class": authority_class,
                "known_at_utc": known_at,
                "content_sha256": content_hash,
                "cluster_id": binding.get("cluster_id"),
                "headline_ids": list(binding.get("headline_ids") or []),
                "request_logical_hash": binding.get("request_logical_hash"),
                "permission_state": "PUBLIC_CLAIM_ALLOWED",
                "freshness_state": freshness_state,
                "source_artifact_ref": row.get("source_artifact_ref")
                or f"packet:{packet.get('packet_id')}#official_source_documents/{index}",
            }
        )
    return documents, blockers


def _market_capabilities(packet: Mapping[str, Any]) -> tuple[set[str], list[str]]:
    supplied: set[str] = set()
    blockers: list[str] = []
    claims = [
        row
        for row in (packet.get("numeric_claims") or [])
        if isinstance(row, Mapping)
        and row.get("public_claim_allowed") is True
        and row.get("llm_numeric_authority") is False
        and row.get("source_artifact_ref")
        and row.get("observation_time_utc")
        and row.get("value") is not None
    ]
    snapshots = [
        row
        for row in (packet.get("market_snapshots") or [])
        if isinstance(row, Mapping)
    ]
    if claims and snapshots:
        supplied.add("current_market_snapshot")
    else:
        blockers.append("governed_current_market_snapshot_missing")
    if any(
        row.get("prior_close") is not None or row.get("prior_value") is not None
        for row in claims
    ):
        supplied.add("prior_close")
    else:
        blockers.append("governed_prior_close_missing")
    return supplied, blockers


def _official_freshness_blockers(
    documents: list[Mapping[str, Any]], *, evaluation_as_of_utc: str, max_age_hours: float
) -> list[str]:
    try:
        cutoff = datetime.fromisoformat(evaluation_as_of_utc.replace("Z", "+00:00"))
    except ValueError:
        return ["official_evidence_evaluation_time_invalid"]
    blockers = []
    for index, row in enumerate(documents):
        value = (
            row.get("professional_feed_published_at_utc")
            or row.get("published_at_utc")
            or row.get("event_time_utc")
        )
        try:
            observed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            blockers.append(f"official_evidence_document_{index}_published_time_invalid")
            continue
        age_hours = (cutoff - observed).total_seconds() / 3600.0
        if age_hours < 0 or age_hours > max_age_hours:
            blockers.append(f"official_evidence_document_{index}_stale_or_future")
    return blockers


def _bind_professional_feed_freshness(
    documents: list[dict[str, Any]], request: Mapping[str, Any]
) -> None:
    """Bind an exact reputable feed timestamp to its source URL for freshness only.

    The feed text remains discovery-only and grants no factual or publication authority. The
    accepted document bytes still supply every emitted claim.
    """
    context = request.get("story_context")
    context = context if isinstance(context, Mapping) else {}
    bindings = [
        row
        for row in (context.get("public_source_url_bindings") or [])
        if isinstance(row, Mapping)
        and str(row.get("feed_publisher_handle") or "").casefold()
        in TRUSTED_PROFESSIONAL_FEED_HANDLES
        and str(row.get("feed_source_platform") or "")
        == "x_cdp_list_latest_tweets_timeline"
        and str(row.get("feed_published_at_utc") or "")
    ]
    for document in documents:
        source_url = str(document.get("source_url") or "").rstrip("/")
        match = next(
            (
                row
                for row in bindings
                if str(row.get("url") or "").rstrip("/") == source_url
            ),
            None,
        )
        if match is None:
            continue
        document["professional_feed_published_at_utc"] = str(
            match["feed_published_at_utc"]
        )
        document["freshness_timestamp_source"] = "EXACT_BOUND_PROFESSIONAL_FEED"
        document["professional_feed_publisher_handle"] = str(
            match["feed_publisher_handle"]
        )
        document["professional_feed_grants_factual_authority"] = False


class RollingXTargetedEvidenceAdapter:
    """Translate exact governed packets into the existing rolling-X receipt contract."""

    def __init__(
        self,
        *,
        capital_chronicle_root: str | Path | None = None,
        evaluation_as_of_utc: str | None = None,
        packet_loader: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        official_evidence_loader: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        public_secondary_loader: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
        grounded_researcher: Any = None,
        capability_registry: Mapping[str, Any] | None = None,
        source_route_health: Any = None,
    ) -> None:
        self._root = Path(capital_chronicle_root) if capital_chronicle_root else None
        self._evaluation_as_of_utc = evaluation_as_of_utc or _utc_now()
        self._packet_loader = packet_loader
        injected_acquisition_boundary = any(
            value is not None
            for value in (packet_loader, official_evidence_loader, public_secondary_loader)
        )
        if official_evidence_loader is None:
            from live_contentops.official_primary_evidence_loader_v1 import (
                BoundedOfficialPrimaryEvidenceLoader,
            )

            official_evidence_loader = BoundedOfficialPrimaryEvidenceLoader(
                evaluation_as_of_utc=self._evaluation_as_of_utc
            )
        self._official_evidence_loader = official_evidence_loader
        if public_secondary_loader is None:
            from live_contentops.public_secondary_evidence_loader_v1 import (
                BoundedPublicSecondaryEvidenceLoader,
            )

            public_secondary_loader = BoundedPublicSecondaryEvidenceLoader(
                evaluation_as_of_utc=self._evaluation_as_of_utc,
                source_route_health=source_route_health,
            )
        self._public_secondary_loader = public_secondary_loader
        if grounded_researcher is None and not injected_acquisition_boundary:
            from live_contentops.grounded_news_research_v1 import GroundedNewsResearchV1

            grounded_researcher = GroundedNewsResearchV1(
                evaluation_as_of_utc=self._evaluation_as_of_utc,
                public_retriever=self._public_secondary_loader,
            )
        self._grounded_researcher = grounded_researcher
        self._registry = effective_rolling_x_capability_registry(
            capability_registry
        )
        self._load_error: str | None = None

    def source_route_health_snapshot(self) -> dict[str, Any]:
        snapshot = getattr(self._public_secondary_loader, "source_route_health_snapshot", None)
        return dict(snapshot()) if callable(snapshot) else {}

    def _run_grounded_research(
        self,
        request: Mapping[str, Any],
        documents: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if self._grounded_researcher is None:
            return None
        try:
            raw = self._grounded_researcher(
                request, initial_documents=list(documents)
            )
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            return {
                "status": "BLOCKED",
                "blockers": [
                    _sanitized_evidence_loader_error(
                        "grounded_research_unavailable", exc
                    )
                ],
                "evidence_documents": list(documents),
                "publication_authority": False,
            }
        if not isinstance(raw, Mapping):
            return {
                "status": "BLOCKED",
                "blockers": ["grounded_research_result_not_object"],
                "evidence_documents": list(documents),
                "publication_authority": False,
            }
        return dict(raw)

    def _load_packet(self, request: Mapping[str, Any]) -> dict[str, Any] | None:
        # Packet selection is story-bound. Do not cache one story's packet across the rolling
        # candidate walk now that compatible successor files may coexist in the governed folder.
        self._load_error = None
        if self._packet_loader is not None:
            try:
                raw = self._packet_loader(request)
            except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
                self._load_error = (
                    "capital_chronicle_evidence_packet_unavailable:"
                    + type(exc).__name__
                )
                return None
            if not isinstance(raw, Mapping):
                self._load_error = "capital_chronicle_evidence_packet_not_object"
                return None
            return dict(raw)
        try:
            if self._root is not None:
                raw = build_evidence_packet_from_cc_root(
                    self._root,
                    as_of_utc=self._evaluation_as_of_utc,
                    story_binding={
                        "cluster_id": request.get("cluster_id"),
                        "headline_ids": list(request.get("headline_ids") or []),
                        "request_logical_hash": request.get("request_logical_hash"),
                    },
                )
            else:
                self._load_error = "capital_chronicle_evidence_root_not_bound"
                return None
            if not isinstance(raw, Mapping):
                self._load_error = "capital_chronicle_evidence_packet_not_object"
                return None
            return dict(raw)
        except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
            self._load_error = (
                "capital_chronicle_evidence_packet_unavailable:"
                + type(exc).__name__
            )
        return None

    def __call__(self, request: Mapping[str, Any]) -> dict[str, Any]:
        if request.get("x_content_is_discovery_and_ranking_only") is not True:
            return _blocked_receipt(
                request, ["x_discovery_only_contract_missing"]
            )
        try:
            request, codex_discovery_receipt = _apply_codex_source_discovery(
                request
            )
        except ValueError as exc:
            return _blocked_receipt(request, [str(exc)])
        story_type = str(request.get("story_type") or "")
        capability = resolve_story_capabilities(
            {
                "story_type": story_type,
                "article_mode": str(request.get("article_mode") or ""),
                "product_article_mode": str(
                    request.get("effective_article_mode")
                    or request.get("resolved_article_mode")
                    or ""
                ),
            },
            self._registry,
        )
        request = {
            **dict(request),
            "editorial_mode_contract": dict(
                capability.get("editorial_mode_contract") or {}
            ),
        }
        blockers = list(capability.get("blockers") or [])
        required = [
            str(value)
            for value in request.get("required_evidence_capabilities") or []
        ]
        if required != list(capability.get("required_evidence_capabilities") or []):
            blockers.append("evidence_request_capability_registry_mismatch")
        families = set(capability.get("source_adapter_families") or [])
        if not families or families != set(
            request.get("source_adapter_families") or families
        ):
            blockers.append("evidence_request_source_adapter_registry_mismatch")
        if blockers:
            return _blocked_receipt(request, blockers)

        families = set(capability.get("source_adapter_families") or [])
        cc_families = {"capital_chronicle_market_state", "capital_chronicle_database"}
        packet = (
            self._load_packet(request)
            if self._root is not None
            or (
                self._packet_loader is not None
                and bool(families.intersection(cc_families))
            )
            else None
        )
        authority_resolution = resolve_publication_authority(
            packet,
            story_binding={
                "cluster_id": request.get("cluster_id"),
                "headline_ids": list(request.get("headline_ids") or []),
                "request_logical_hash": request.get("request_logical_hash"),
            },
        )
        if not families.intersection(cc_families):
            from live_contentops.official_primary_evidence_loader_v1 import (
                OFFICIAL_HOSTS_BY_FAMILY,
                SUPPORTED_FAMILIES,
            )
            from live_contentops.official_primary_source_locator_v1 import (
                routed_official_locator_families,
            )

            documents: list[dict[str, Any]] = []
            supplied: set[str] = set()
            diagnostics: dict[str, Any] = {}
            if codex_discovery_receipt is not None:
                diagnostics["codex_source_discovery"] = dict(
                    codex_discovery_receipt
                )
            registry_official_families = families.intersection(SUPPORTED_FAMILIES)
            exact_bound_official_families = _exact_bound_official_families(
                request, OFFICIAL_HOSTS_BY_FAMILY
            )
            context_routed_official_families = set(
                routed_official_locator_families(request)
            )
            official_families = sorted(
                registry_official_families
                .union(exact_bound_official_families)
                .union(context_routed_official_families)
            )
            if official_families:
                official_request = {
                    **dict(request),
                    "source_adapter_families": official_families,
                    # Acquisition verifies every capability found in the bytes.  Sufficiency is
                    # applied below against the effective mode, not inside the transport.
                    "required_evidence_capabilities": [],
                }
                try:
                    official_raw = self._official_evidence_loader(official_request)
                    official = dict(official_raw) if isinstance(official_raw, Mapping) else {}
                except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
                    official = {"status": "BLOCKED", "blockers": [
                        _sanitized_evidence_loader_error(
                            "official_source_evidence_unavailable", exc
                        )
                    ]}
                diagnostics["official"] = {
                    "status": official.get("status"),
                    "blockers": list(official.get("blockers") or []),
                    "provenance": dict(official.get("provenance") or {}),
                    "registry_authorized_families": sorted(registry_official_families),
                    "exact_bound_host_authorized_families": sorted(
                        exact_bound_official_families
                    ),
                    "exact_context_routed_families": sorted(
                        context_routed_official_families
                    ),
                    "context_routing_grants_authority": False,
                }
                if official.get("official_source_documents"):
                    # Rebind the transport packet to the exact effective-mode request.
                    official["rolling_x_story_binding"] = {
                        "cluster_id": request.get("cluster_id"),
                        "headline_ids": list(request.get("headline_ids") or []),
                        "request_logical_hash": request.get("request_logical_hash"),
                    }
                    official_documents, official_document_blockers = _document_receipts(
                        official,
                        request,
                        freshness_state="FRESH_CURRENT_OPERATOR_READINESS",
                        official_primary_required=True,
                    )
                    documents.extend(official_documents)
                    if not official_documents:
                        diagnostics["official"]["document_blockers"] = official_document_blockers
                        # An optional official locator/index that cannot bind public claims is
                        # excluded, not promoted and not allowed to poison a separately valid
                        # grounded public packet. If no other source succeeds, the ordinary
                        # required-capability/minimum-packet gates below still fail closed.
                        discovery_index_only = all(
                            bool(row.get("discovery_only_source_index"))
                            for row in official.get("official_source_documents") or []
                            if isinstance(row, Mapping)
                        )
                        blockers.extend(
                            blocker
                            for blocker in official_document_blockers
                            if not (
                                discovery_index_only
                                and blocker.endswith("missing:public_claim_permission")
                            )
                        )
                    supplied.update(
                        str(value)
                        for value in (official.get("provided_evidence_capabilities") or [])
                    )

            # Do not let a stale official page suppress enrichment. Freshness is applied before
            # the depth decision, then again after secondary acquisition so every acquired row
            # still passes the same point-in-time boundary.
            freshness_requirements = capability.get("freshness_requirements") or {}
            _bind_professional_feed_freshness(documents, request)
            pre_enrichment_fresh_documents: list[dict[str, Any]] = []
            pre_enrichment_freshness_exclusions: list[dict[str, Any]] = []
            for document in documents:
                findings = _official_freshness_blockers(
                    [document],
                    evaluation_as_of_utc=self._evaluation_as_of_utc,
                    max_age_hours=float(freshness_requirements.get("max_age_hours") or 36.0),
                )
                if findings:
                    pre_enrichment_freshness_exclusions.append(
                        {
                            "document_id": document.get("document_id"),
                            "findings": findings,
                            "disposition": "EXCLUDED_BEFORE_DEPTH_ENRICHMENT",
                        }
                    )
                else:
                    pre_enrichment_fresh_documents.append(document)
            documents = pre_enrichment_fresh_documents

            # Cheap deterministic public acquisition precedes any grounded model call. The same
            # story-scoped loader/cache is reused by grounded research, so successful reads are
            # not repeated and deterministic unreachability cannot burn an expensive call.
            secondary_preflight_attempted = False
            if "public_secondary" in families:
                secondary_preflight_attempted = True
                pre_secondary_depth = summarize_evidence_substance(request, documents)
                secondary_needed = not bool(
                    pre_secondary_depth.get("enough_for_useful_article")
                )
                if secondary_needed:
                    secondary_request = {
                        **dict(request),
                        "evidence_enrichment_context": {
                            "requested": bool(documents)
                            or bool(pre_enrichment_freshness_exclusions),
                            "reason": "ELIGIBLE_EVIDENCE_TOO_THIN_FOR_USEFUL_ARTICLE"
                            if documents or pre_enrichment_freshness_exclusions
                            else "MINIMUM_PUBLIC_EVIDENCE_ACQUISITION",
                            "existing_evidence_substance": pre_secondary_depth,
                            "additional_source_is_eligibility_requirement": False,
                        },
                    }
                    try:
                        secondary_raw = self._public_secondary_loader(secondary_request)
                        secondary = (
                            dict(secondary_raw) if isinstance(secondary_raw, Mapping) else {}
                        )
                    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
                        secondary = {
                            "status": "BLOCKED",
                            "blockers": [
                                _sanitized_evidence_loader_error(
                                    "public_secondary_evidence_unavailable", exc
                                )
                            ],
                        }
                else:
                    secondary = {
                        "status": "NOT_NEEDED_EVIDENCE_DEPTH_SUFFICIENT",
                        "blockers": [],
                        "evidence_documents": [],
                        "provided_evidence_capabilities": [],
                        "provenance": {"request_count": 0},
                    }
                diagnostics["public_secondary"] = {
                    "status": secondary.get("status"),
                    "blockers": list(secondary.get("blockers") or []),
                    "provenance": dict(secondary.get("provenance") or {}),
                    "enrichment_requested": bool(
                        documents or pre_enrichment_freshness_exclusions
                    )
                    and secondary_needed,
                    "pre_acquisition_substance": pre_secondary_depth,
                }
                binding_blockers = _exact_binding_blockers(secondary, request)
                if not binding_blockers:
                    known_at = (secondary.get("provenance") or {}).get(
                        "retrieved_at_utc"
                    )
                    for row in secondary.get("evidence_documents") or []:
                        if not isinstance(row, Mapping):
                            continue
                        document = dict(row)
                        if (
                            document.get("source_url")
                            and document.get("source_identity")
                            and document.get("source_authority_class")
                            == "reputable_secondary_source"
                            and document.get("public_claim_allowed") is True
                            and document.get("canonical_content_sha256")
                            and known_at
                        ):
                            document.update(
                                {
                                    "known_at_utc": known_at,
                                    "cluster_id": request.get("cluster_id"),
                                    "headline_ids": list(
                                        request.get("headline_ids") or []
                                    ),
                                    "request_logical_hash": request.get(
                                        "request_logical_hash"
                                    ),
                                    "permission_state": "PUBLIC_CLAIM_ALLOWED",
                                    "freshness_state": "FRESH_CURRENT_OPERATOR_READINESS",
                                }
                            )
                            documents.append(document)
                    supplied.update(
                        str(value)
                        for value in (
                            secondary.get("provided_evidence_capabilities") or []
                        )
                    )
                else:
                    diagnostics["public_secondary"]["binding_blockers"] = binding_blockers

            if not documents:
                deterministic_blockers = sorted(
                    {
                        str(value)
                        for value in list(blockers)
                        + [
                            item
                            for lane in ("official", "public_secondary")
                            for item in (
                                (diagnostics.get(lane) or {}).get("blockers") or []
                            )
                        ]
                        + [
                            finding
                            for row in pre_enrichment_freshness_exclusions
                            for finding in row.get("findings") or []
                        ]
                        if str(value)
                    }
                )
                if "evidence_documents_missing" not in deterministic_blockers:
                    deterministic_blockers.append("evidence_documents_missing")
                    deterministic_blockers.sort()
                trigger = (
                    "SOURCE_DISCOVERY_REQUIRED"
                    if codex_discovery_receipt is None
                    else "AUTONOMOUS_SOURCE_DISCOVERY_EXHAUSTED"
                )
                receipt = _blocked_receipt(
                    request,
                    deterministic_blockers + [trigger],
                    documents=[],
                    supplied=sorted(supplied),
                    evidence_acquisition_provenance=diagnostics,
                )
                receipt["source_discovery_handshake"] = {
                    "status": trigger,
                    "story_identity": request.get("cluster_id"),
                    "headline_ids": list(request.get("headline_ids") or []),
                    "prior_blockers": deterministic_blockers,
                    "same_candidate_resume_required": True,
                    "grounded_research_calls_before_discovery": 0,
                    "search_snippet_or_model_summary_authority": False,
                    "publication_authority": False,
                }
                return _with_cc_authority_evidence(
                    receipt,
                    packet=packet,
                    resolution=authority_resolution,
                    consume_projection=False,
                )

            grounded = self._run_grounded_research(request, documents)
            grounded_attempted = grounded is not None
            grounded_packet: dict[str, Any] = {}
            grounded_minimum_packet: dict[str, Any] = {}
            grounded_claim_contract: dict[str, Any] = {}
            grounded_evidence_substance: dict[str, Any] = {}
            grounded_latest_state_closure: dict[str, Any] = {}
            if grounded is not None:
                diagnostics["grounded_research"] = {
                    "status": grounded.get("status"),
                    "blockers": list(grounded.get("blockers") or []),
                    "research_calls": int(grounded.get("research_calls") or 0),
                    "public_retrieval_requests": int(
                        grounded.get("public_retrieval_requests") or 0
                    ),
                    "elapsed_seconds": grounded.get("elapsed_seconds"),
                    "telemetry": list(grounded.get("telemetry") or []),
                    "grounding_mode": (
                        (grounded.get("research_packet") or {}).get(
                            "grounding_mode"
                        )
                    ),
                    "retrieval_result": dict(grounded.get("retrieval_result") or {}),
                    "infrastructure_failure_class": grounded.get(
                        "infrastructure_failure_class"
                    ),
                    "global_infrastructure_exhausted": bool(
                        grounded.get("global_infrastructure_exhausted")
                    ),
                    "latest_event_state_closure": dict(
                        grounded.get("latest_event_state_closure") or {}
                    ),
                }
                grounded_packet = dict(grounded.get("research_packet") or {})
                grounded_minimum_packet = dict(
                    grounded.get("minimum_trustworthy_evidence_packet") or {}
                )
                grounded_claim_contract = dict(
                    grounded.get("claim_evidence_contract") or {}
                )
                grounded_evidence_substance = dict(
                    grounded.get("evidence_substance") or {}
                )
                grounded_latest_state_closure = dict(
                    grounded.get("latest_event_state_closure") or {}
                )
                if grounded.get("status") == "PASS":
                    documents = [
                        dict(row)
                        for row in grounded.get("evidence_documents") or []
                        if isinstance(row, Mapping)
                    ]
                    requested_mode = str(
                        request.get("effective_article_mode")
                        or request.get("resolved_article_mode")
                        or ""
                    )
                    if requested_mode == WEEK_AHEAD_PRODUCT_MODE:
                        schedule_facts, _schedule_fact_blockers = (
                            _deterministic_official_schedule_facts(documents)
                        )
                        if schedule_facts:
                            grounded_packet = _merge_deterministic_schedule_facts(
                                grounded_packet, schedule_facts
                            )
                    supplied.update(
                        {"credible_event_confirmation", "basic_attributed_facts"}
                    )
                    suggested_mode = str(
                        grounded_packet.get("suggested_article_mode") or ""
                    )
                    if product_mode_evidence_depth(
                        requested_mode
                    ) > product_mode_evidence_depth(suggested_mode):
                        blockers.append(
                            "grounded_research_recommends_article_mode_downgrade:"
                            + suggested_mode
                        )
                else:
                    blockers.extend(
                        str(value)
                        for value in grounded.get("blockers") or [
                            "grounded_research_blocked"
                        ]
                    )

            if (
                "public_secondary" in families
                and not grounded_attempted
                and not secondary_preflight_attempted
            ):
                pre_secondary_depth = summarize_evidence_substance(request, documents)
                secondary_needed = not bool(
                    pre_secondary_depth.get("enough_for_useful_article")
                )
                if secondary_needed:
                    secondary_request = {
                        **dict(request),
                        "evidence_enrichment_context": {
                            "requested": bool(documents)
                            or bool(pre_enrichment_freshness_exclusions),
                            "reason": "ELIGIBLE_EVIDENCE_TOO_THIN_FOR_USEFUL_ARTICLE"
                            if documents or pre_enrichment_freshness_exclusions
                            else "MINIMUM_PUBLIC_EVIDENCE_ACQUISITION",
                            "existing_evidence_substance": pre_secondary_depth,
                            "additional_source_is_eligibility_requirement": False,
                        },
                    }
                    try:
                        secondary_raw = self._public_secondary_loader(secondary_request)
                        secondary = dict(secondary_raw) if isinstance(secondary_raw, Mapping) else {}
                    except (FileNotFoundError, RuntimeError, ValueError, OSError) as exc:
                        secondary = {"status": "BLOCKED", "blockers": [
                            _sanitized_evidence_loader_error(
                                "public_secondary_evidence_unavailable", exc
                            )
                        ]}
                else:
                    secondary = {
                        "status": "NOT_NEEDED_EVIDENCE_DEPTH_SUFFICIENT",
                        "blockers": [],
                        "evidence_documents": [],
                        "provided_evidence_capabilities": [],
                        "provenance": {"request_count": 0},
                    }
                diagnostics["public_secondary"] = {
                    "status": secondary.get("status"),
                    "blockers": list(secondary.get("blockers") or []),
                    "provenance": dict(secondary.get("provenance") or {}),
                    "enrichment_requested": bool(
                        documents or pre_enrichment_freshness_exclusions
                    )
                    and secondary_needed,
                    "pre_acquisition_substance": pre_secondary_depth,
                }
                binding_blockers = _exact_binding_blockers(secondary, request)
                if not binding_blockers:
                    known_at = (secondary.get("provenance") or {}).get("retrieved_at_utc")
                    for row in secondary.get("evidence_documents") or []:
                        if not isinstance(row, Mapping):
                            continue
                        document = dict(row)
                        if (
                            document.get("source_url")
                            and document.get("source_identity")
                            and document.get("source_authority_class") == "reputable_secondary_source"
                            and document.get("public_claim_allowed") is True
                            and document.get("canonical_content_sha256")
                            and known_at
                        ):
                            document.update(
                                {
                                    "known_at_utc": known_at,
                                    "cluster_id": request.get("cluster_id"),
                                    "headline_ids": list(request.get("headline_ids") or []),
                                    "request_logical_hash": request.get("request_logical_hash"),
                                    "permission_state": "PUBLIC_CLAIM_ALLOWED",
                                    "freshness_state": "FRESH_CURRENT_OPERATOR_READINESS",
                                }
                            )
                            documents.append(document)
                    supplied.update(
                        str(value)
                        for value in (secondary.get("provided_evidence_capabilities") or [])
                    )
                else:
                    diagnostics["public_secondary"]["binding_blockers"] = binding_blockers

            _bind_professional_feed_freshness(documents, request)
            fresh_documents: list[dict[str, Any]] = []
            freshness_exclusions: list[dict[str, Any]] = []
            for document in documents:
                findings = _official_freshness_blockers(
                    [document],
                    evaluation_as_of_utc=self._evaluation_as_of_utc,
                    max_age_hours=float(freshness_requirements.get("max_age_hours") or 36.0),
                )
                if findings:
                    freshness_exclusions.append(
                        {
                            "document_id": document.get("document_id"),
                            "findings": findings,
                            "disposition": "EXCLUDED_NOT_A_WHOLE_STORY_VETO",
                        }
                    )
                else:
                    fresh_documents.append(document)
            documents = fresh_documents
            all_freshness_exclusions = (
                pre_enrichment_freshness_exclusions + freshness_exclusions
            )
            if all_freshness_exclusions:
                diagnostics["freshness_exclusions"] = all_freshness_exclusions
                if not documents:
                    blockers.extend(
                        finding
                        for row in all_freshness_exclusions
                        for finding in row["findings"]
                    )
            requested_mode = str(
                request.get("effective_article_mode")
                or request.get("resolved_article_mode")
                or ""
            )
            deterministic_schedule_facts: list[dict[str, Any]] = []
            if requested_mode == WEEK_AHEAD_PRODUCT_MODE:
                deterministic_schedule_facts, schedule_fact_blockers = (
                    _deterministic_official_schedule_facts(documents)
                )
                blockers.extend(schedule_fact_blockers)
                if deterministic_schedule_facts:
                    supplied.update(WEEK_AHEAD_REQUIRED_CAPABILITIES)
                    if any(
                        row.get("period_or_edition_label")
                        for row in deterministic_schedule_facts
                    ):
                        supplied.add("scheduled_period_or_edition_label")
                    if grounded_packet:
                        grounded_packet = _merge_deterministic_schedule_facts(
                            grounded_packet, deterministic_schedule_facts
                        )
                else:
                    supplied.difference_update(WEEK_AHEAD_REQUIRED_CAPABILITIES)
                    supplied.discard("scheduled_period_or_edition_label")
                    blockers.append("deterministic_official_schedule_fact_binding_missing")
            evidence_sufficient, ordinary_packet, claim_contract = (
                _minimum_or_enhanced_evidence(request, documents)
            )
            if grounded_packet:
                grounded_packet = _restrict_grounded_packet_to_documents(
                    grounded_packet, documents
                )
                grounded_fact_request = {
                    **dict(request),
                    "story_context": {
                        **dict(request.get("story_context") or {}),
                        "leaf_summaries": [
                            str(row.get("factual_statement") or "")
                            for row in grounded_packet.get("confirmed_facts") or []
                            if isinstance(row, Mapping)
                        ],
                    },
                }
                evidence_sufficient, ordinary_packet, claim_contract = (
                    _minimum_or_enhanced_evidence(
                        grounded_fact_request, documents
                    )
                )
                evidence_sufficient = bool(
                    evidence_sufficient
                    and grounded is not None
                    and grounded.get("status") == "PASS"
                    and grounded_packet.get("research_status") == "PASS"
                )
                if grounded_packet.get("research_status") != "PASS":
                    blockers.append(
                        "grounded_research_facts_removed_by_hard_evidence_filter"
                    )
            evidence_substance = (
                grounded_evidence_substance
                or summarize_evidence_substance(request, documents)
            )
            diagnostics["evidence_substance"] = evidence_substance
            if evidence_sufficient:
                supplied.update({"credible_event_confirmation", "basic_attributed_facts"})
            else:
                blockers.append("minimum_trustworthy_evidence_missing")
            if not documents:
                blockers.append("evidence_documents_missing")
            for missing in sorted(set(required) - supplied):
                blockers.append(f"required_evidence_capability_missing:{missing}")
            if blockers:
                receipt = _blocked_receipt(
                    request,
                    blockers,
                    documents=documents,
                    supplied=sorted(supplied),
                    evidence_acquisition_provenance=diagnostics,
                )
                if ordinary_packet:
                    receipt["minimum_trustworthy_evidence_packet"] = ordinary_packet
                if claim_contract:
                    receipt["claim_evidence_contract"] = claim_contract
                if grounded_packet:
                    receipt["grounded_research_packet"] = grounded_packet
                    receipt["cc_context_bundle"] = dict(
                        grounded_packet.get("cc_context") or {}
                    )
                receipt["evidence_substance"] = evidence_substance
                receipt["deterministic_official_schedule_facts"] = (
                    deterministic_schedule_facts
                )
                receipt["latest_event_state_closure"] = (
                    grounded_latest_state_closure
                )
                return _with_cc_authority_evidence(
                    receipt,
                    packet=packet,
                    resolution=authority_resolution,
                    consume_projection=False,
                )
            return _with_cc_authority_evidence({
                "status": "PASS",
                "cluster_id": request.get("cluster_id"),
                "headline_ids": list(request.get("headline_ids") or []),
                "provided_evidence_capabilities": sorted(supplied),
                "evidence_documents": documents,
                **(
                    {"minimum_trustworthy_evidence_packet": ordinary_packet}
                    if ordinary_packet
                    else {"claim_evidence_contract": claim_contract}
                ),
                "evidence_review_tier": "ORDINARY_MINIMUM" if ordinary_packet else "ENHANCED",
                "evidence_substance": evidence_substance,
                "latest_event_state_closure": grounded_latest_state_closure,
                "grounded_research_packet": grounded_packet,
                "deterministic_official_schedule_facts": (
                    deterministic_schedule_facts
                ),
                "cc_context_bundle": dict(
                    grounded_packet.get("cc_context") or {}
                ),
                "unsupported_claims_removed": int(claim_contract.get("omitted_claim_count") or 0),
                "capital_chronicle_authority_verified": False,
                "numeric_evidence_required": False,
                "blockers": [],
                "publication_authority": False,
                "editorial_mode_contract": dict(
                    request.get("editorial_mode_contract") or {}
                ),
                "evidence_acquisition_provenance": diagnostics,
            }, packet=packet, resolution=authority_resolution, consume_projection=False)

        if packet is None:
            return _with_cc_authority_evidence(
                _blocked_receipt(
                    request,
                    [
                        self._load_error
                        or (
                            "capital_chronicle_evidence_root_not_bound"
                            if self._root is None
                            else "capital_chronicle_evidence_packet_unavailable"
                        )
                    ],
                ),
                packet=None,
                resolution=authority_resolution,
                consume_projection=False,
            )
        blockers.extend(validate_evidence_packet(packet))
        if packet.get("status") != PUBLICATION_AUTHORIZED:
            blockers.append("governed_packet_not_publication_authorized")
        permissions = packet.get("public_claim_permissions") or {}
        if (
            permissions.get("decision") != "ALLOW"
            or permissions.get("reporting_allowed") is not True
        ):
            blockers.append("governed_reporting_permission_not_granted")
        if permissions.get("llm_numeric_authority") is not False:
            blockers.append("governed_llm_numeric_authority_invalid")
        blockers.extend(_exact_binding_blockers(packet, request))

        freshness_request = {
            "article_mode": capability.get("article_mode"),
            "market_sensitive": bool(capability.get("market_sensitive")),
            "market_snapshot_required": bool(
                capability.get("market_snapshot_required")
            ),
            "fresh_material_delta": bool(
                (packet.get("publication_assignment") or {}).get(
                    "fresh_material_delta"
                )
                or (packet.get("assignment") or {}).get("fresh_material_delta")
            ),
            "readiness_evaluation_basis": "CURRENT_OPERATOR_READINESS",
            "operator_evaluation_as_of_utc": self._evaluation_as_of_utc,
        }
        freshness = evaluate_freshness(packet, freshness_request)
        if freshness.get("decision") != "PASS":
            blockers.extend(freshness.get("blockers") or [])
        freshness_state = (
            "FRESH_CURRENT_OPERATOR_READINESS"
            if freshness.get("decision") == "PASS"
            else "STALE_OR_MISSING"
        )
        authority_resolution = resolve_publication_authority(
            packet,
            story_binding={
                "cluster_id": request.get("cluster_id"),
                "headline_ids": list(request.get("headline_ids") or []),
                "request_logical_hash": request.get("request_logical_hash"),
            },
            current_readiness_blockers=(
                list(freshness.get("blockers") or [])
                if freshness.get("decision") != "PASS"
                else []
            ),
        )
        documents, document_blockers = _document_receipts(
            packet, request, freshness_state=freshness_state
        )
        blockers.extend(document_blockers)
        research_request = {
            **dict(request),
            "capital_chronicle_authority_verified_for_research": bool(
                packet.get("status") == PUBLICATION_AUTHORIZED
                and permissions.get("decision") == "ALLOW"
                and permissions.get("reporting_allowed") is True
                and not _exact_binding_blockers(packet, request)
            ),
        }
        grounded = self._run_grounded_research(research_request, documents)
        grounded_packet: dict[str, Any] = {}
        grounded_minimum_packet: dict[str, Any] = {}
        grounded_claim_contract: dict[str, Any] = {}
        grounded_evidence_substance: dict[str, Any] = {}
        grounded_latest_state_closure: dict[str, Any] = {}
        grounded_diagnostics: dict[str, Any] = {}
        if grounded is not None:
            grounded_diagnostics = {
                "status": grounded.get("status"),
                "blockers": list(grounded.get("blockers") or []),
                "research_calls": int(grounded.get("research_calls") or 0),
                "public_retrieval_requests": int(
                    grounded.get("public_retrieval_requests") or 0
                ),
                "elapsed_seconds": grounded.get("elapsed_seconds"),
                "telemetry": list(grounded.get("telemetry") or []),
                "latest_event_state_closure": dict(
                    grounded.get("latest_event_state_closure") or {}
                ),
            }
            grounded_packet = dict(grounded.get("research_packet") or {})
            grounded_minimum_packet = dict(
                grounded.get("minimum_trustworthy_evidence_packet") or {}
            )
            grounded_claim_contract = dict(
                grounded.get("claim_evidence_contract") or {}
            )
            grounded_evidence_substance = dict(
                grounded.get("evidence_substance") or {}
            )
            grounded_latest_state_closure = dict(
                grounded.get("latest_event_state_closure") or {}
            )
            if grounded.get("status") == "PASS":
                documents = [
                    dict(row)
                    for row in grounded.get("evidence_documents") or []
                    if isinstance(row, Mapping)
                ]
                suggested_mode = str(
                    grounded_packet.get("suggested_article_mode") or ""
                )
                requested_mode = str(
                    request.get("effective_article_mode")
                    or request.get("resolved_article_mode")
                    or ""
                )
                if product_mode_evidence_depth(
                    requested_mode
                ) > product_mode_evidence_depth(suggested_mode):
                    blockers.append(
                        "grounded_research_recommends_article_mode_downgrade:"
                        + suggested_mode
                    )
            else:
                blockers.extend(
                    str(value)
                    for value in grounded.get("blockers") or [
                        "grounded_research_blocked"
                    ]
                )
        evidence_sufficient, ordinary_packet, claim_contract = (
            _minimum_or_enhanced_evidence(request, documents)
        )
        if grounded_packet:
            ordinary_packet = grounded_minimum_packet
            claim_contract = grounded_claim_contract
            evidence_sufficient = bool(
                grounded is not None and grounded.get("status") == "PASS"
            )
        if not evidence_sufficient:
            blockers.append("minimum_trustworthy_evidence_missing")

        declared_supplied = set(
            str(value)
            for value in packet.get("provided_evidence_capabilities") or []
        )
        supplied = declared_supplied - MARKET_CAPABILITIES - {"catalyst_evidence"}
        market_supplied, market_blockers = _market_capabilities(packet)
        if "capital_chronicle_market_state" in families:
            supplied.update(market_supplied)
            blockers.extend(
                blocker
                for blocker in market_blockers
                if any(capability in required for capability in MARKET_CAPABILITIES)
            )
        elif MARKET_CAPABILITIES.intersection(required):
            blockers.append("capital_chronicle_market_state_adapter_unavailable")
        if "official_catalyst" in families:
            if documents:
                supplied.add("catalyst_evidence")
            elif "catalyst_evidence" in required:
                blockers.append("governed_official_catalyst_evidence_missing")
        supplied.update(
            capability
            for capability in required
            if capability not in MARKET_CAPABILITIES
            and capability != "catalyst_evidence"
            and capability in set(
                packet.get("provided_evidence_capabilities") or []
            )
            and documents
        )
        if evidence_sufficient:
            supplied.update({"credible_event_confirmation", "basic_attributed_facts"})

        for missing in sorted(set(required) - supplied):
            blockers.append(f"required_evidence_capability_missing:{missing}")
        market_required = bool(
            request.get(
                "capital_chronicle_numeric_or_analytical_authority_required"
            )
        )
        authority_verified = bool(
            market_required
            and not blockers
            and set(required).issubset(supplied)
            and MARKET_CAPABILITIES.intersection(required).issubset(supplied)
        )
        if market_required and not authority_verified:
            blockers.append("capital_chronicle_authority_not_verified")
        if blockers:
            receipt = _blocked_receipt(
                request,
                blockers,
                documents=documents,
                supplied=sorted(supplied.intersection(required)),
            )
            if ordinary_packet:
                receipt["minimum_trustworthy_evidence_packet"] = ordinary_packet
            if claim_contract:
                receipt["claim_evidence_contract"] = claim_contract
            if grounded_packet:
                receipt["grounded_research_packet"] = grounded_packet
                receipt["cc_context_bundle"] = dict(
                    grounded_packet.get("cc_context") or {}
                )
                receipt["evidence_acquisition_provenance"] = {
                    "grounded_research": grounded_diagnostics
                }
            receipt["latest_event_state_closure"] = grounded_latest_state_closure
            return _with_cc_authority_evidence(
                receipt,
                packet=packet,
                resolution=authority_resolution,
                consume_projection=False,
            )
        return _with_cc_authority_evidence({
            "status": "PASS",
            "cluster_id": request.get("cluster_id"),
            "headline_ids": list(request.get("headline_ids") or []),
            "provided_evidence_capabilities": sorted(
                supplied.intersection(required)
            ),
            "evidence_documents": documents,
            **(
                {"minimum_trustworthy_evidence_packet": ordinary_packet}
                if ordinary_packet
                else {"claim_evidence_contract": claim_contract}
            ),
            "evidence_review_tier": "ORDINARY_MINIMUM" if ordinary_packet else "ENHANCED",
            "evidence_substance": (
                grounded_evidence_substance
                or summarize_evidence_substance(request, documents)
            ),
            "latest_event_state_closure": grounded_latest_state_closure,
            "grounded_research_packet": grounded_packet,
            "cc_context_bundle": dict(
                grounded_packet.get("cc_context") or {}
            ),
            "evidence_acquisition_provenance": {
                "grounded_research": grounded_diagnostics
            },
            "unsupported_claims_removed": int(claim_contract.get("omitted_claim_count") or 0),
            "capital_chronicle_authority_verified": authority_verified,
            "numeric_evidence_required": market_required,
            "blockers": [],
            "publication_authority": False,
            "editorial_mode_contract": dict(
                request.get("editorial_mode_contract") or {}
            ),
            "governed_packet_id": packet.get("packet_id"),
            "freshness_decision": freshness,
        }, packet=packet, resolution=authority_resolution, consume_projection=True)
