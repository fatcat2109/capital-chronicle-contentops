"""Small provider-neutral Visual Asset Discovery seam for the canonical article factory.

Providers discover candidates; only deterministic source-bound rights checks may make a
candidate selectable. Search thumbnails and unknown-rights assets are never delivery media.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence


SCHEMA_VERSION = "contentops.visual_asset_discovery.v1"
VISUAL_INTENTS = frozenset({
    "HERO_DOCUMENTARY",
    "LOCATION_CONTEXT",
    "PERSON_OR_INSTITUTION_CONTEXT",
    "INFRASTRUCTURE_CONTEXT",
    "MAP_GEOGRAPHY",
    "QUANTITATIVE_CHART",
    "COMPARISON",
    "TIMELINE",
    "SOURCE_DOCUMENT",
    "CONCEPTUAL_ILLUSTRATION",
})
DISCOVERY_PRIORITY = (
    "first_party_official",
    "wikimedia_commons",
    "openverse",
    "general_image_search_discovery",
    "licensed_contextual_library",
    "generated_conceptual_illustration",
)
SELECTABLE_RIGHTS = frozenset({
    "FIRST_PARTY_REUSABLE", "PUBLIC_DOMAIN", "OPEN_LICENSED", "LICENSED_REUSE",
})
REQUIRED_CANDIDATE_FIELDS = (
    "visual_intent", "discovery_provider", "query", "source_page_url",
    "original_asset_url", "creator_publisher", "reuse_basis", "attribution", "width",
    "height", "content_hash", "perceptual_hash", "documentary_generated_classification",
    "rights_status",
)


@dataclass(frozen=True)
class AssetDiscoveryProvider:
    provider_id: str
    discover: Callable[[Mapping[str, Any]], Sequence[Mapping[str, Any]]]


def _terms(value: str) -> list[str]:
    stop = {"the", "and", "with", "from", "that", "this", "into", "after", "latest"}
    return [
        term for term in re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", str(value or ""))
        if term.casefold() not in stop
    ]


def build_visual_intent_plan(
    article: Mapping[str, Any], *, evidence: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Build narrow story-specific search intents; this grants no rights or factual authority."""
    evidence = dict(evidence or {})
    title = " ".join(str(article.get("title") or "").split())
    body = str(article.get("substack_body_markdown") or "")
    context = f"{title} {body}".casefold()
    entities = [str(value) for value in article.get("entities_topics") or [] if str(value).strip()]
    key_terms = list(dict.fromkeys(_terms(title)[:8] + entities[:4]))
    base = " ".join(key_terms[:6]) or "article context"
    intents: list[dict[str, Any]] = []

    def add(intent: str, suffixes: Sequence[str], rationale: str) -> None:
        intents.append({
            "visual_intent": intent,
            "queries": [f"{base} {suffix}".strip() for suffix in suffixes],
            "editorial_rationale": rationale,
            "rights_required": True,
            "publication_authority": False,
        })

    add(
        "HERO_DOCUMENTARY",
        ("official photograph", "documentary context", "site:commons.wikimedia.org"),
        "Show the real institution, place, or infrastructure at the center of the story.",
    )
    if re.search(r"\b(strait|city|country|region|border|route|port|location|geography)\b", context):
        add("LOCATION_CONTEXT", ("location photograph", "aerial documentary"), "Orient the reader to the real place.")
        add("MAP_GEOGRAPHY", ("official map", "geographic chokepoint map"), "Explain the relevant geography.")
    if re.search(r"\b(agency|department|treasury|federal reserve|company|minister|president)\b", context):
        add("PERSON_OR_INSTITUTION_CONTEXT", ("official building photograph", "official portrait"), "Identify the responsible institution or person with real media.")
    if re.search(r"\b(tanker|pipeline|refinery|factory|port|infrastructure|grid|facility)\b", context):
        add("INFRASTRUCTURE_CONTEXT", ("infrastructure documentary photo", "official facility photograph"), "Show the physical mechanism described by the reporting.")
    quantitative = bool(
        evidence.get("governed_data_series")
        or evidence.get("governed_table_rows")
        or re.search(r"\b\d+(?:\.\d+)?%|basis points?|yield|forecast|comparison\b", context)
    )
    if quantitative:
        add("QUANTITATIVE_CHART", ("governed data chart",), "Show a supported quantitative relationship.")
        add("COMPARISON", ("latest versus previous comparison",), "Make a supported comparison legible.")
    return {
        "schema_version": SCHEMA_VERSION,
        "article_identity": hashlib.sha256(json.dumps(dict(article), sort_keys=True, default=str).encode()).hexdigest(),
        "intents": intents,
        "provider_priority": list(DISCOVERY_PRIORITY),
        "semantic_model_may_grant_rights": False,
        "unknown_rights_disposition": "REJECT",
        "publication_authority": False,
    }

def validate_asset_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_CANDIDATE_FIELDS if candidate.get(field) in (None, "")]
    intent = str(candidate.get("visual_intent") or "")
    rights = str(candidate.get("rights_status") or "")
    source_page = str(candidate.get("source_page_url") or "")
    original = str(candidate.get("original_asset_url") or "")
    license_url = str(candidate.get("license_url") or "")
    width = int(candidate.get("width") or 0)
    height = int(candidate.get("height") or 0)
    blockers = list(missing)
    if intent not in VISUAL_INTENTS:
        blockers.append("visual_intent_unknown")
    if rights not in SELECTABLE_RIGHTS:
        blockers.append("rights_not_verified_reusable")
    if not source_page.startswith("https://") or not original.startswith("https://"):
        blockers.append("original_source_resolution_missing")
    if candidate.get("discovery_provider") == "general_image_search_discovery" and source_page == original:
        blockers.append("search_result_thumbnail_not_original_asset")
    if re.search(r"(?:/thumb/|[?&](?:w|width)=\d{1,3}(?:&|$))", original, re.I):
        blockers.append("low_resolution_thumbnail_url")
    if width < 1000 or height < 600:
        blockers.append("candidate_resolution_below_article_floor")
    if rights in {"OPEN_LICENSED", "LICENSED_REUSE"} and not license_url.startswith("https://"):
        blockers.append("license_url_required")
    classification = str(candidate.get("documentary_generated_classification") or "")
    if classification not in {"DOCUMENTARY", "CONTEXTUAL", "DATA_GRAPHIC", "CONCEPTUAL_GENERATED"}:
        blockers.append("documentary_generated_classification_invalid")
    if classification == "CONCEPTUAL_GENERATED" and intent in {
        "HERO_DOCUMENTARY", "LOCATION_CONTEXT", "PERSON_OR_INSTITUTION_CONTEXT",
        "INFRASTRUCTURE_CONTEXT",
    }:
        blockers.append("generated_media_cannot_substitute_for_documentary_intent")
    blockers = list(dict.fromkeys(blockers))
    return {
        "status": "PASS" if not blockers else "REJECTED",
        "blockers": blockers,
        "rights_verified": not any("rights" in value or "license" in value for value in blockers),
        "search_thumbnail_publishable": False,
        "publication_authority": False,
    }


def _phash_distance(left: str, right: str) -> int:
    try:
        return (int(left, 16) ^ int(right, 16)).bit_count()
    except ValueError:
        return 10_000


def discover_and_rank_assets(
    plan: Mapping[str, Any], *, providers: Sequence[AssetDiscoveryProvider], maximum_selected: int = 3
) -> dict[str, Any]:
    """Discover, rights-resolve, rank and deduplicate candidates without external writes."""
    rows: list[dict[str, Any]] = []
    for provider in providers:
        for intent in plan.get("intents") or []:
            for raw in provider.discover(dict(intent)):
                candidate = {**dict(raw), "discovery_provider": provider.provider_id}
                validation = validate_asset_candidate(candidate)
                score = round(sum(float(candidate.get(field) or 0) for field in (
                    "story_relevance_score", "subject_correctness_score", "editorial_usefulness_score",
                    "composition_score", "visual_diversity_score",
                )) / 5, 4)
                rows.append({**candidate, "validation": validation, "ranking_score": score})
    eligible = sorted(
        (row for row in rows if row["validation"]["status"] == "PASS"),
        key=lambda row: (-float(row["ranking_score"]), DISCOVERY_PRIORITY.index(str(row["discovery_provider"])) if str(row["discovery_provider"]) in DISCOVERY_PRIORITY else 99),
    )
    selected: list[dict[str, Any]] = []
    represented_intents: set[str] = set()
    for row in eligible:
        if any(_phash_distance(str(row["perceptual_hash"]), str(item["perceptual_hash"])) <= 4 for item in selected):
            continue
        intent = str(row["visual_intent"])
        if intent in represented_intents and len(eligible) > maximum_selected:
            continue
        selected.append(row)
        represented_intents.add(intent)
        if len(selected) >= maximum_selected:
            break
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS" if selected else "NO_PURPOSEFUL_RIGHTS_CLEARED_ASSET",
        "candidate_count": len(rows),
        "eligible_count": len(eligible),
        "selected_count": len(selected),
        "candidates": rows,
        "selected_assets": selected,
        "rights_gate_deterministic": True,
        "semantic_ranking_grants_rights": False,
        "fixed_visual_quota": False,
        "publication_authority": False,
    }
