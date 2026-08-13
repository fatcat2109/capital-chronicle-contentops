"""Small provider-neutral Visual Asset Discovery seam for the canonical article factory.

Providers discover candidates; only deterministic source-bound rights checks may make a
candidate selectable. Search thumbnails and unknown-rights assets are never delivery media.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image

from live_contentops.article_rich_text_v1 import sanitize_source_text


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


JsonFetcher = Callable[[str], Mapping[str, Any]]
BytesFetcher = Callable[[str], bytes]


def _default_json_fetcher(url: str) -> Mapping[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "CapitalChronicleContentOps/1.0 rights-aware-asset-discovery",
        },
    )
    with urlopen(request, timeout=25) as response:  # noqa: S310 - fixed provider bases
        payload = response.read(2_000_001)
    if not payload or len(payload) > 2_000_000:
        raise RuntimeError("asset_discovery_json_response_size_invalid")
    parsed = json.loads(payload.decode("utf-8"))
    if not isinstance(parsed, Mapping):
        raise RuntimeError("asset_discovery_json_response_not_object")
    return parsed


def _default_bytes_fetcher(url: str) -> bytes:
    request = Request(
        url,
        headers={"User-Agent": "CapitalChronicleContentOps/1.0 visual-ranking-readonly"},
    )
    with urlopen(request, timeout=25) as response:  # noqa: S310 - provider-returned image URL
        payload = response.read(5_000_001)
    if not payload or len(payload) > 5_000_000:
        raise RuntimeError("asset_discovery_thumbnail_size_invalid")
    return payload


def _image_perceptual_hash(payload: bytes) -> str:
    with Image.open(io.BytesIO(payload)) as image:
        gray = image.convert("L").resize((8, 8))
        values = list(gray.getdata())
    average = sum(values) / len(values)
    bits = "".join("1" if value >= average else "0" for value in values)
    return f"{int(bits, 2):016x}"


def _metadata_value(metadata: Mapping[str, Any], key: str) -> str:
    row = metadata.get(key) or {}
    if isinstance(row, Mapping):
        row = row.get("value") or ""
    return sanitize_source_text(str(row or ""), maximum=1000)


def _normalise_license_url(value: str) -> str:
    value = str(value or "").strip()
    if value.startswith("//"):
        return "https:" + value
    return value if value.startswith("https://") else ""


def _rights_from_license(license_name: str) -> str:
    normalized = " ".join(str(license_name or "").upper().replace("_", " ").split())
    if normalized in {"CC0", "PDM"} or "PUBLIC DOMAIN" in normalized or normalized.startswith("PD-"):
        return "PUBLIC_DOMAIN"
    if normalized in {"BY", "BY-SA", "GFDL"} or normalized.startswith("CC BY") or normalized.startswith("CC-BY"):
        if "-NC" in normalized or " NC" in normalized:
            return "UNKNOWN"
        return "OPEN_LICENSED"
    return "UNKNOWN"


def _semantic_scores(*, query: str, title: str, description: str) -> dict[str, float]:
    query_terms = set(_terms(query))
    candidate_terms = set(_terms(f"{title} {description}"))
    overlap = len({value.casefold() for value in query_terms}.intersection(
        {value.casefold() for value in candidate_terms}
    ))
    coverage = overlap / max(1, min(6, len(query_terms)))
    # A dramatic incident image can be superficially relevant to a place or industry while
    # misrepresenting an ordinary contextual story. Keep this deterministic and query-bound:
    # incident imagery remains eligible when the story query itself names the incident.
    incident_terms = {"attack", "collision", "damaged", "explosion", "fire", "wreck"}
    incident_mismatch = bool(
        incident_terms.intersection(value.casefold() for value in candidate_terms)
        and not incident_terms.intersection(value.casefold() for value in query_terms)
    )
    mismatch_penalty = 0.32 if incident_mismatch else 0.0
    return {
        "story_relevance_score": round(max(0.0, min(1.0, 0.42 + coverage * 0.58) - mismatch_penalty), 4),
        "subject_correctness_score": round(max(0.0, min(1.0, 0.45 + coverage * 0.55) - mismatch_penalty), 4),
        "editorial_usefulness_score": round(max(0.0, min(1.0, 0.5 + coverage * 0.45) - mismatch_penalty), 4),
        "composition_score": 0.65,
        "visual_diversity_score": 0.75,
        "contextual_incident_mismatch": incident_mismatch,
    }


def _asset_series_key(title: str) -> str:
    value = re.sub(r"^File:", "", str(title or ""), flags=re.I)
    value = re.sub(r"\(?\s*(?:image|photo)\s*\d+\s+of\s+\d+\s*\)?", "", value, flags=re.I)
    value = re.sub(r"\.(?:jpe?g|png|webp|gif|tiff?)$", "", value, flags=re.I)
    return " ".join(re.findall(r"[a-z0-9]{3,}", value.casefold()))


def build_wikimedia_commons_provider(
    *,
    json_fetcher: JsonFetcher = _default_json_fetcher,
    bytes_fetcher: BytesFetcher = _default_bytes_fetcher,
    candidates_per_query: int = 4,
) -> AssetDiscoveryProvider:
    """Return a real read-only Commons provider with source/license resolution."""
    if not 1 <= int(candidates_per_query) <= 10:
        raise ValueError("wikimedia_candidates_per_query_out_of_bounds")

    def discover(intent: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for query in list(intent.get("queries") or [])[:3]:
            params = {
                "action": "query",
                "format": "json",
                "formatversion": "2",
                "generator": "search",
                "gsrsearch": str(query) + " filetype:bitmap",
                "gsrnamespace": "6",
                "gsrlimit": str(candidates_per_query),
                "prop": "imageinfo|info",
                "inprop": "url",
                "iiprop": "url|size|mime|sha1|extmetadata",
                "iiurlwidth": "640",
            }
            payload = json_fetcher(
                "https://commons.wikimedia.org/w/api.php?" + urlencode(params)
            )
            for page in ((payload.get("query") or {}).get("pages") or []):
                if not isinstance(page, Mapping):
                    continue
                info_rows = page.get("imageinfo") or []
                info = info_rows[0] if info_rows and isinstance(info_rows[0], Mapping) else {}
                original = str(info.get("url") or "")
                source_page = str(page.get("canonicalurl") or page.get("fullurl") or "")
                if not original or original in seen:
                    continue
                seen.add(original)
                metadata = info.get("extmetadata") or {}
                license_name = _metadata_value(metadata, "LicenseShortName")
                usage_terms = _metadata_value(metadata, "UsageTerms")
                creator = _metadata_value(metadata, "Artist") or _metadata_value(metadata, "Credit")
                description = _metadata_value(metadata, "ImageDescription")
                thumbnail = str(info.get("thumburl") or "")
                try:
                    perceptual_hash = _image_perceptual_hash(bytes_fetcher(thumbnail))
                except Exception:
                    perceptual_hash = ""
                rows.append({
                    "visual_intent": str(intent.get("visual_intent") or ""),
                    "query": str(query),
                    "source_page_url": source_page,
                    "original_asset_url": original,
                    "discovery_thumbnail_url": thumbnail,
                    "creator_publisher": creator or "Wikimedia Commons contributor",
                    "reuse_basis": "; ".join(value for value in (license_name, usage_terms) if value),
                    "license_url": _normalise_license_url(
                        _metadata_value(metadata, "LicenseUrl")
                    ),
                    "attribution": creator or _metadata_value(metadata, "Credit") or str(page.get("title") or ""),
                    "width": int(info.get("width") or 0),
                    "height": int(info.get("height") or 0),
                    "candidate_mime_type": str(info.get("mime") or ""),
                    "content_hash": "sha1:" + str(info.get("sha1") or ""),
                    "content_hash_basis": "WIKIMEDIA_ORIGINAL_ASSET_SHA1",
                    "perceptual_hash": perceptual_hash,
                    "perceptual_hash_basis": "DISCOVERY_THUMBNAIL_NOT_DELIVERY_ASSET",
                    "documentary_generated_classification": "DOCUMENTARY",
                    "rights_status": _rights_from_license(license_name),
                    "candidate_title": str(page.get("title") or ""),
                    "asset_series_key": _asset_series_key(str(page.get("title") or "")),
                    "candidate_description": description,
                    **_semantic_scores(
                        query=str(query), title=str(page.get("title") or ""),
                        description=description,
                    ),
                })
        return rows

    return AssetDiscoveryProvider(provider_id="wikimedia_commons", discover=discover)


def build_openverse_provider(
    *,
    json_fetcher: JsonFetcher = _default_json_fetcher,
    bytes_fetcher: BytesFetcher = _default_bytes_fetcher,
    candidates_per_query: int = 4,
) -> AssetDiscoveryProvider:
    """Return a real anonymous Openverse provider; no credential is required."""
    if not 1 <= int(candidates_per_query) <= 10:
        raise ValueError("openverse_candidates_per_query_out_of_bounds")

    def discover(intent: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for query in list(intent.get("queries") or [])[:3]:
            params = urlencode({"q": str(query), "page_size": str(candidates_per_query)})
            payload = json_fetcher("https://api.openverse.org/v1/images/?" + params)
            for raw in payload.get("results") or []:
                if not isinstance(raw, Mapping):
                    continue
                original = str(raw.get("url") or "")
                source_page = str(raw.get("foreign_landing_url") or "")
                if not original or original in seen:
                    continue
                seen.add(original)
                thumbnail = str(raw.get("thumbnail") or "")
                try:
                    thumbnail_bytes = bytes_fetcher(thumbnail)
                    perceptual_hash = _image_perceptual_hash(thumbnail_bytes)
                    thumbnail_hash = hashlib.sha256(thumbnail_bytes).hexdigest()
                except Exception:
                    perceptual_hash = ""
                    thumbnail_hash = ""
                license_code = str(raw.get("license") or "")
                license_version = str(raw.get("license_version") or "")
                license_name = "-".join(value for value in (license_code, license_version) if value)
                title = sanitize_source_text(str(raw.get("title") or ""), maximum=500)
                creator = sanitize_source_text(str(raw.get("creator") or ""), maximum=500)
                identity = json.dumps({
                    "id": raw.get("id"), "source_page_url": source_page,
                    "original_asset_url": original, "provider": raw.get("provider"),
                }, sort_keys=True)
                rows.append({
                    "visual_intent": str(intent.get("visual_intent") or ""),
                    "query": str(query),
                    "source_page_url": source_page,
                    "original_asset_url": original,
                    "discovery_thumbnail_url": thumbnail,
                    "creator_publisher": creator or str(raw.get("provider") or "Openverse source"),
                    "reuse_basis": f"Openverse indexed license {license_name}".strip(),
                    "license_url": _normalise_license_url(str(raw.get("license_url") or "")),
                    "attribution": str(raw.get("attribution") or creator or title),
                    "width": int(raw.get("width") or 0),
                    "height": int(raw.get("height") or 0),
                    "candidate_mime_type": str(raw.get("mimetype") or ""),
                    "content_hash": "source-sha256:" + hashlib.sha256(identity.encode()).hexdigest(),
                    "content_hash_basis": "OPENVERSE_SOURCE_IDENTITY",
                    "discovery_thumbnail_sha256": thumbnail_hash,
                    "perceptual_hash": perceptual_hash,
                    "perceptual_hash_basis": "DISCOVERY_THUMBNAIL_NOT_DELIVERY_ASSET",
                    "documentary_generated_classification": "DOCUMENTARY",
                    "rights_status": _rights_from_license(license_code),
                    "candidate_title": title,
                    "asset_series_key": _asset_series_key(title),
                    "candidate_description": sanitize_source_text(
                        str(raw.get("tags") or ""), maximum=1000
                    ),
                    **_semantic_scores(query=str(query), title=title, description=str(raw.get("tags") or "")),
                })
        return rows

    return AssetDiscoveryProvider(provider_id="openverse", discover=discover)


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
    geography_match = re.search(
        r"\b(?:Strait|Gulf|Sea|Canal|River|Port)\s+of\s+[A-Z][A-Za-z'-]+",
        title,
    )
    geography = geography_match.group(0) if geography_match else ""
    documentary_base = geography or base
    intents: list[dict[str, Any]] = []

    def add(intent: str, queries: Sequence[str], rationale: str) -> None:
        intents.append({
            "visual_intent": intent,
            "queries": [" ".join(str(value).split()) for value in queries if str(value).strip()],
            "editorial_rationale": rationale,
            "rights_required": True,
            "publication_authority": False,
        })

    add(
        "HERO_DOCUMENTARY",
        (
            f"{documentary_base} tanker" if geography else f"{base} official photograph",
            f"{documentary_base} shipping" if geography else f"{base} documentary context",
            f"{documentary_base} documentary photograph",
        ),
        "Show the real institution, place, or infrastructure at the center of the story.",
    )
    if re.search(r"\b(strait|city|country|region|border|route|port|location|geography)\b", context):
        add(
            "LOCATION_CONTEXT",
            (documentary_base, f"{documentary_base} aerial photograph", f"{documentary_base} coastline"),
            "Orient the reader to the real place.",
        )
        add(
            "MAP_GEOGRAPHY",
            (f"{documentary_base} map", f"{documentary_base} shipping map"),
            "Explain the relevant geography.",
        )
    if re.search(r"\b(agency|department|treasury|federal reserve|company|minister|president)\b", context):
        add("PERSON_OR_INSTITUTION_CONTEXT", (f"{base} official building photograph", f"{base} official portrait"), "Identify the responsible institution or person with real media.")
    if re.search(r"\b(tanker|pipeline|refinery|factory|port|infrastructure|grid|facility)\b", context):
        add(
            "INFRASTRUCTURE_CONTEXT",
            (
                f"{documentary_base} oil tanker",
                f"{documentary_base} shipping traffic",
                f"{documentary_base} port infrastructure",
            ),
            "Show the physical mechanism described by the reporting.",
        )
    quantitative = bool(
        evidence.get("governed_data_series")
        or evidence.get("governed_table_rows")
        or re.search(r"\b\d+(?:\.\d+)?%|basis points?|yield|forecast|comparison\b", context)
    )
    if quantitative:
        add("QUANTITATIVE_CHART", (f"{base} governed data chart",), "Show a supported quantitative relationship.")
        add("COMPARISON", (f"{base} latest versus previous comparison",), "Make a supported comparison legible.")
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
    thumbnail = str(candidate.get("discovery_thumbnail_url") or "")
    license_url = str(candidate.get("license_url") or "")
    width = int(candidate.get("width") or 0)
    height = int(candidate.get("height") or 0)
    mime_type = str(candidate.get("candidate_mime_type") or "")
    blockers = list(missing)
    if intent not in VISUAL_INTENTS:
        blockers.append("visual_intent_unknown")
    if rights not in SELECTABLE_RIGHTS:
        blockers.append("rights_not_verified_reusable")
    if not source_page.startswith("https://") or not original.startswith("https://"):
        blockers.append("original_source_resolution_missing")
    if candidate.get("discovery_provider") == "general_image_search_discovery" and source_page == original:
        blockers.append("search_result_thumbnail_not_original_asset")
    if thumbnail and original == thumbnail:
        blockers.append("search_result_thumbnail_not_original_asset")
    if re.search(r"(?:/thumb/|[?&](?:w|width)=\d{1,3}(?:&|$))", original, re.I):
        blockers.append("low_resolution_thumbnail_url")
    if width < 1000 or height < 600:
        blockers.append("candidate_resolution_below_article_floor")
    if mime_type and not mime_type.startswith("image/"):
        blockers.append("candidate_not_raster_image")
    if not re.fullmatch(r"(?:sha1|sha256|source-sha256):[0-9a-fA-F]{16,64}", str(candidate.get("content_hash") or "")):
        blockers.append("content_or_source_hash_invalid")
    if not re.fullmatch(r"[0-9a-fA-F]{16}", str(candidate.get("perceptual_hash") or "")):
        blockers.append("perceptual_hash_invalid")
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
    provider_failures: list[dict[str, str]] = []
    for provider in providers:
        for intent in plan.get("intents") or []:
            try:
                discovered = provider.discover(dict(intent))
            except Exception as exc:
                provider_failures.append({
                    "discovery_provider": provider.provider_id,
                    "visual_intent": str(intent.get("visual_intent") or ""),
                    "failure_class": type(exc).__name__,
                })
                continue
            for raw in discovered:
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
    represented_series: set[str] = set()
    for row in eligible:
        if any(_phash_distance(str(row["perceptual_hash"]), str(item["perceptual_hash"])) <= 4 for item in selected):
            continue
        series_key = str(row.get("asset_series_key") or "")
        if series_key and series_key in represented_series:
            continue
        intent = str(row["visual_intent"])
        if intent in represented_intents and len(eligible) > maximum_selected:
            continue
        selected.append(row)
        represented_intents.add(intent)
        if series_key:
            represented_series.add(series_key)
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
        "provider_failures": provider_failures,
        "rights_gate_deterministic": True,
        "semantic_ranking_grants_rights": False,
        "fixed_visual_quota": False,
        "publication_authority": False,
    }


def discover_visual_assets_for_article(
    article: Mapping[str, Any], *, evidence: Mapping[str, Any] | None = None,
    providers: Sequence[AssetDiscoveryProvider] | None = None,
    maximum_selected: int = 3,
) -> dict[str, Any]:
    """Run the provider-neutral seam with the real credential-free providers by default."""
    plan = build_visual_intent_plan(article, evidence=evidence)
    active_providers = list(providers) if providers is not None else [
        build_wikimedia_commons_provider(),
        build_openverse_provider(),
    ]
    discovery = discover_and_rank_assets(
        plan, providers=active_providers, maximum_selected=maximum_selected
    )
    return {**discovery, "visual_intent_plan": plan}
