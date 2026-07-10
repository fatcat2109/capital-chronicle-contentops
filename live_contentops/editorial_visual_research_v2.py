"""Provider-neutral visual discovery, rights, diversity, and chart-method gates."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Protocol, Sequence


class VisualResearchProvider(Protocol):
    def build_request(self, query: str) -> Mapping[str, Any]: ...


class GoogleImageSearchGroundingProvider:
    """Build current Gemini Interactions API discovery requests; performs no call."""
    def __init__(self, model: str = "gemini-3.1-flash-image") -> None:
        self.model = model

    def build_request(self, query: str) -> dict[str, Any]:
        return {
            "api_family": "gemini_interactions_api",
            "model": self.model,
            "input": query,
            "tools": [{"type": "google_search", "search_types": ["web_search", "image_search"]}],
            "required_response_evidence": ["url_citation", "google_search_result.search_suggestions", "containing_page_url", "direct_image_url"],
            "usage_boundary": "discovery_only_not_provenance_or_reuse_permission",
            "credential_value_read": False,
            "network_call_made": False,
        }


def validate_visual_candidate(candidate: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    required = ("asset_id", "role", "modality", "source_page_url", "publisher", "publication_date", "rights_status", "caption", "alt_text", "width", "height", "sha256", "article_section")
    blockers.extend(f"missing:{key}" for key in required if candidate.get(key) in (None, ""))
    if candidate.get("is_logo") or candidate.get("is_avatar") or candidate.get("is_thumbnail"):
        blockers.append("branding_or_thumbnail_not_editorial_visual")
    if candidate.get("is_synthetic") or candidate.get("is_manipulated"):
        blockers.append("synthetic_or_manipulated_candidate_rejected")
    if int(candidate.get("width") or 0) < 800 or int(candidate.get("height") or 0) < 450:
        blockers.append("dimensions_below_editorial_threshold")
    if str(candidate.get("rights_status") or "") not in {"public_domain", "official_press_reuse", "licensed", "capital_chronicle_owned", "fair_use_excerpt_operator_review"}:
        blockers.append("reuse_rights_unverified")
    if not candidate.get("relevance_rationale"):
        blockers.append("relevance_not_established")
    if candidate.get("recency_required") and candidate.get("recency_status") != "fresh":
        blockers.append("time_sensitive_visual_not_fresh")
    return blockers


def validate_chart_methodology(asset: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    metadata = dict(asset.get("quantitative_method") or {})
    if asset.get("modality") not in {"chart", "time_series"}:
        return blockers
    for key in ("metric_definition", "units", "frequency", "sample_window", "transformation_owner"):
        if not metadata.get(key):
            blockers.append(f"chart_method_missing:{key}")
    label = str(asset.get("chart_title") or asset.get("caption") or "").casefold()
    method = str(metadata.get("calculation") or "").casefold()
    if "realized volatility" in label and not ("standard deviation" in method and metadata.get("annualization_factor")):
        blockers.append("realized_volatility_definition_or_annualization_invalid")
    if "average absolute" in method and "volatility" in label:
        blockers.append("average_absolute_move_mislabeled_as_volatility")
    if metadata.get("partial_period") and not any(term in label for term in ("ytd", "through ", "partial")):
        blockers.append("partial_period_not_explicitly_labeled")
    return blockers


def evaluate_visual_composition(
    assets: Sequence[Mapping[str, Any]], *, editorial_exception: str | None = None, story_type: str | None = None
) -> dict[str, Any]:
    blockers: list[str] = []
    if len(assets) < 3 and not editorial_exception:
        blockers.append("fewer_than_three_useful_visuals")
    dimensions = {str(row.get("evidence_dimension") or "") for row in assets if row.get("evidence_dimension")}
    modalities = {str(row.get("modality") or "") for row in assets if row.get("modality")}
    if len(dimensions) < 2 and len(modalities) < 2:
        blockers.append("insufficient_visual_evidence_diversity")
    if story_type in {"geopolitical_event", "supply_chain_event"} and not modalities.intersection({"official_photo", "map", "infrastructure_context", "contextual_image"}):
        blockers.append("physical_or_geopolitical_story_requires_contextual_nonprice_visual")
    if story_type == "data_release" and assets and modalities <= {"chart", "time_series"} and len(dimensions) < 3:
        blockers.append("all_chart_data_release_requires_three_distinct_evidence_dimensions")
    series_counts: dict[str, int] = {}
    for asset in assets:
        blockers.extend(f"{asset.get('asset_id')}:{item}" for item in validate_visual_candidate(asset))
        blockers.extend(f"{asset.get('asset_id')}:{item}" for item in validate_chart_methodology(asset))
        for series_id in asset.get("underlying_series_ids") or []:
            series_counts[str(series_id)] = series_counts.get(str(series_id), 0) + 1
    for series_id, count in series_counts.items():
        if count > 2:
            blockers.append(f"underlying_series_overused:{series_id}:{count}")
    lead = next((row for row in assets if row.get("role") == "lead_contextual"), None)
    if not lead:
        blockers.append("lead_visual_missing")
    elif not lead.get("supports_headline"):
        blockers.append("lead_visual_does_not_support_headline")
    hashes = [str(row.get("perceptual_hash") or row.get("sha256") or "") for row in assets]
    if len([value for value in hashes if value]) != len(set(value for value in hashes if value)):
        blockers.append("duplicate_visual_hash")
    return {
        "schema_version": "contentops.visual_composition_decision.v2",
        "status": "PASS" if not blockers else "BLOCK",
        "asset_count": len(assets),
        "evidence_dimensions": sorted(dimensions),
        "modalities": sorted(modalities),
        "underlying_series_counts": series_counts,
        "editorial_exception": editorial_exception,
        "story_type": story_type,
        "blockers": list(dict.fromkeys(blockers)),
        "decision_hash": hashlib.sha256(json.dumps(blockers, sort_keys=True).encode()).hexdigest(),
    }
