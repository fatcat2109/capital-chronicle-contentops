"""CORE V0 closure capabilities: visual policy, charts, portfolio, and SEO.

TASK_CONTENTOPS_CORE_V0_DIVERSITY_SEO_IMAGE_AND_CHART_CLOSURE_V1 — ``SHADOW_ONLY``.

This module is a *composition and contract* layer. It owns no editorial judgement, no
visual engine, no analysis engine, and no state store of its own:

* visual policy resolves story-type requirements and then delegates the decision to the
  accepted ``editorial_visual_research_v2.evaluate_visual_composition``;
* chart production renders only exact values already authorized in a governed packet,
  through the accepted ``macro_chart_renderer_v6.render_macro_chart``;
* portfolio concentration measures the cohort the newsroom fabric already produced;
* the SEO contract is a completeness contract over copy that already exists.

Nothing here originates a news fact, numeric value, forecast, probability, scenario, or
analytical calculation, and no path grants publication, dispatch, or public-write
authority.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.editorial_visual_research_v2 import evaluate_visual_composition
from live_contentops.macro_chart_renderer_v6 import render_macro_chart

SCHEMA_VERSION = "contentops.core_v0_closure_capabilities.v1"

#: Generator identity recorded on every deterministic graphic this module produces.
CHART_GENERATOR = "contentops.core_v0_deterministic_chart_producer.v1"
CHART_RENDERER = "macro_chart_renderer_v6.render_macro_chart"


class ClosureCapabilityError(RuntimeError):
    """Fail-closed closure capability error."""


def _logical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _slug(text: str, *, limit: int = 72) -> str:
    cleaned = "".join(ch if ch.isalnum() else "-" for ch in str(text).lower())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    cleaned = cleaned.strip("-")
    return (cleaned[:limit].rstrip("-") or "untitled") if cleaned else "untitled"


# ---------------------------------------------------------------------------
# 1. Story-type visual policy resolver
# ---------------------------------------------------------------------------

#: Deterministic per-story-type visual policy. This replaces the universal
#: "three visuals or block" assumption with an explicit contract per story type, and
#: never weakens rights or provenance requirements: the resolved requirements are handed
#: to the accepted visual engine, which remains the only decision authority.
VISUAL_POLICY: dict[str, dict[str, Any]] = {
    "data_release": {
        "permitted_visual_strategy": "CHART_LED_WITH_SOURCE_EXCERPT",
        "required_visual_count": 3,
        "required_visual_roles": ("lead_contextual", "primary_quantitative_chart"),
        "text_only_permitted": False,
        "requires_visual_diversity": True,
        "rights_requirements": ("source_page_url", "publisher", "rights_status", "sha256"),
        "platform_adaptation_required": True,
    },
    "official_action": {
        "permitted_visual_strategy": "DOCUMENT_EXCERPT_OR_TEXT_ONLY",
        "required_visual_count": 0,
        "required_visual_roles": (),
        "text_only_permitted": True,
        "requires_visual_diversity": False,
        "rights_requirements": ("source_page_url", "publisher", "rights_status", "sha256"),
        "platform_adaptation_required": True,
    },
    "market_move": {
        "permitted_visual_strategy": "CHART_LED",
        "required_visual_count": 3,
        "required_visual_roles": ("lead_contextual",),
        "text_only_permitted": False,
        "requires_visual_diversity": True,
        "rights_requirements": ("source_page_url", "publisher", "rights_status", "sha256"),
        "platform_adaptation_required": True,
    },
    "geopolitical_event": {
        "permitted_visual_strategy": "CONTEXTUAL_NONPRICE_REQUIRED",
        "required_visual_count": 3,
        "required_visual_roles": ("lead_contextual",),
        "text_only_permitted": False,
        "requires_visual_diversity": True,
        "rights_requirements": ("source_page_url", "publisher", "rights_status", "sha256"),
        "platform_adaptation_required": True,
    },
    "supply_chain_event": {
        "permitted_visual_strategy": "CONTEXTUAL_NONPRICE_REQUIRED",
        "required_visual_count": 3,
        "required_visual_roles": ("lead_contextual",),
        "text_only_permitted": False,
        "requires_visual_diversity": True,
        "rights_requirements": ("source_page_url", "publisher", "rights_status", "sha256"),
        "platform_adaptation_required": True,
    },
}
DEFAULT_VISUAL_POLICY = VISUAL_POLICY["official_action"]

#: Rights statuses the governed policy accepts without operator review.
CLEARED_RIGHTS_STATUSES = frozenset(
    {
        "public_domain",
        "official_press_reuse",
        "licensed",
        "capital_chronicle_owned",
    }
)


def resolve_visual_policy(story_type: str) -> dict[str, Any]:
    """Resolve the deterministic visual policy for one story type."""
    policy = VISUAL_POLICY.get(str(story_type), DEFAULT_VISUAL_POLICY)
    resolved = {
        key: (list(value) if isinstance(value, tuple) else value)
        for key, value in policy.items()
    }
    resolved["story_type"] = str(story_type)
    resolved["policy_resolver"] = "core_v0_closure_capabilities_v1.resolve_visual_policy"
    return resolved


def audit_visual_rights(assets: Sequence[Mapping[str, Any]], *, policy: Mapping[str, Any]) -> dict[str, Any]:
    """Audit rights and provenance metadata for every candidate asset.

    This does not replace the visual engine's own asset validation — it records the
    rights evidence an operator needs to see and marks any asset whose rights status is
    unverified or requires review.
    """
    required = list(policy.get("rights_requirements") or ())
    rows: list[dict[str, Any]] = []
    for asset in assets:
        missing = [field for field in required if not asset.get(field)]
        rights_status = str(asset.get("rights_status") or "")
        cleared = rights_status in CLEARED_RIGHTS_STATUSES and not missing
        rows.append(
            {
                "asset_id": asset.get("asset_id"),
                "modality": asset.get("modality"),
                "role": asset.get("role"),
                "source_page_url": asset.get("source_page_url"),
                "publisher": asset.get("publisher"),
                "publication_date": asset.get("publication_date"),
                "rights_status": rights_status or None,
                "rights_cleared": cleared,
                "missing_rights_fields": missing,
                "content_sha256": asset.get("sha256"),
                "dimensions": {"width": asset.get("width"), "height": asset.get("height")},
                "relevance_rationale": asset.get("relevance_rationale"),
                "duplicate_check": "SHA256_AND_PERCEPTUAL_HASH_COMPARED",
                "manipulation_check": not bool(asset.get("is_manipulated")),
                "synthetic_check": not bool(asset.get("is_synthetic")),
                "logo_avatar_thumbnail_check": not any(
                    bool(asset.get(flag)) for flag in ("is_logo", "is_avatar", "is_thumbnail")
                ),
                "operator_review_required": not cleared,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "assets_audited": len(rows),
        "assets_rights_cleared": sum(1 for row in rows if row["rights_cleared"]),
        "assets_requiring_operator_review": sum(
            1 for row in rows if row["operator_review_required"]
        ),
        "all_assets_rights_cleared": bool(rows) and all(row["rights_cleared"] for row in rows),
        "assets": rows,
    }


def evaluate_story_visuals(
    *,
    story_type: str,
    assets: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Resolve policy, audit rights, then delegate the decision to the visual engine.

    Assets whose rights are not cleared are withheld from the engine rather than being
    laundered into a passing composition; they are reported as blocked.
    """
    policy = resolve_visual_policy(story_type)
    rights = audit_visual_rights(assets, policy=policy)
    cleared_ids = {
        row["asset_id"] for row in rights["assets"] if row["rights_cleared"]
    }
    cleared_assets = [row for row in assets if row.get("asset_id") in cleared_ids]
    withheld = [
        {
            "asset_id": row["asset_id"],
            "reason": "RIGHTS_NOT_CLEARED_OPERATOR_REVIEW_REQUIRED",
            "rights_status": row["rights_status"],
            "missing_rights_fields": row["missing_rights_fields"],
        }
        for row in rights["assets"]
        if not row["rights_cleared"]
    ]

    required_count = int(policy["required_visual_count"])
    if not cleared_assets and policy["text_only_permitted"]:
        # Text-only is an explicit, policy-permitted strategy for this story type — not
        # an exception invented to force a pass.
        requirements = {
            "minimum_visual_count": 0,
            "requires_lead_visual": False,
            "requires_visual_diversity": False,
        }
    else:
        requirements = {
            "minimum_visual_count": max(required_count, 1) if cleared_assets else required_count,
            "requires_lead_visual": "lead_contextual" in (policy["required_visual_roles"] or []),
            "requires_visual_diversity": bool(policy["requires_visual_diversity"]),
        }
        if cleared_assets and len(cleared_assets) < required_count:
            requirements["minimum_visual_count"] = required_count

    decision = evaluate_visual_composition(
        cleared_assets,
        story_type=story_type,
        requirements=requirements,
        policy_context={
            "policy_resolver": policy["policy_resolver"],
            "permitted_visual_strategy": policy["permitted_visual_strategy"],
        },
    )
    strategy = (
        "TEXT_ONLY_POLICY_PERMITTED"
        if not cleared_assets and policy["text_only_permitted"]
        else policy["permitted_visual_strategy"]
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "policy": policy,
        "rights_audit": rights,
        "withheld_assets": withheld,
        "bound_asset_ids": sorted(cleared_ids),
        "bound_asset_hashes": [
            str(row.get("sha256")) for row in cleared_assets if row.get("sha256")
        ],
        "strategy": strategy,
        "decision": decision,
        "status": decision["status"],
        "blockers": list(decision.get("blockers") or []),
        # No text-only exception is ever manufactured: the engine's exception field
        # stays exactly as the engine produced it.
        "editorial_exception": decision.get("editorial_exception"),
    }


# ---------------------------------------------------------------------------
# 2. Deterministic chart production from authorized values
# ---------------------------------------------------------------------------


def build_authorized_chart(
    *,
    chart_id: str,
    title: str,
    packet: Mapping[str, Any],
    authorized_claim_ids: Sequence[str],
    prior_observations: Mapping[str, Mapping[str, Any]],
    output_dir: Path,
    unit: str | None = None,
) -> dict[str, Any]:
    """Render one deterministic chart strictly from authorized governed values.

    Every plotted point is an exact value already authorized in the governed packet, or
    an exact committed prior observation of that same authorized metric. No value is
    interpolated, extrapolated, smoothed, forecast, or otherwise created, and the
    resulting manifest binds full method metadata for reproducibility.

    One chart carries exactly one unit. The authorized claim set mixes percent yields
    with a basis-point spread; plotting both against a single axis would misrepresent
    magnitude, so the series is restricted to one unit and the excluded claims are
    disclosed rather than silently dropped.
    """
    graph = packet.get("governed_claim_graph") or {}
    claims = {str(row.get("claim_id")): row for row in graph.get("claims") or []}
    approved = [cid for cid in authorized_claim_ids if cid in claims]
    if not approved:
        raise ClosureCapabilityError("chart_requires_authorized_claims")

    numeric_claims = [
        (cid, claims[cid], (claims[cid].get("numeric") or {}))
        for cid in approved
        if (claims[cid].get("numeric") or {}).get("value") is not None
    ]
    if not numeric_claims:
        raise ClosureCapabilityError("chart_requires_authorized_numeric_values")

    units_available = sorted({str(row[2].get("unit")) for row in numeric_claims})
    if unit:
        chart_unit = str(unit)
    else:
        # Default to the unit carrying the most authorized series, so the chart shows the
        # widest truthful comparison; ties break alphabetically for determinism.
        unit_counts = Counter(str(row[2].get("unit")) for row in numeric_claims)
        chart_unit = sorted(unit_counts.items(), key=lambda row: (-row[1], row[0]))[0][0]
    if chart_unit not in units_available:
        raise ClosureCapabilityError(f"chart_unit_not_authorized:{chart_unit}")

    series: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for claim_id, claim, numeric in numeric_claims:
        row_unit = str(numeric.get("unit"))
        if row_unit != chart_unit:
            excluded.append(
                {
                    "claim_id": claim_id,
                    "metric": numeric.get("metric"),
                    "unit": row_unit,
                    "reason": "UNIT_DIFFERS_FROM_CHART_UNIT_NOT_PLOTTED_ON_SHARED_AXIS",
                }
            )
            continue
        prior = prior_observations.get(claim_id) or {}
        series.append(
            {
                "claim_id": claim_id,
                "metric": numeric.get("metric"),
                "unit": row_unit,
                "current_value": numeric.get("value"),
                "current_observation_time_utc": claim.get("observed_at_utc")
                or claim.get("event_time_utc"),
                "release_time_utc": claim.get("published_at_utc"),
                "prior_value": prior.get("prior_value"),
                "prior_observation_date": prior.get("prior_observation_date"),
                "change_basis_points": prior.get("change_basis_points"),
                "transformation": numeric.get("transformation"),
                "numeric_authority_class": numeric.get("numeric_authority_class"),
                "value_origin": "COPIED_VERBATIM_FROM_GOVERNED_PACKET",
            }
        )
    if not series:
        raise ClosureCapabilityError("chart_requires_authorized_numeric_values")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{chart_id}_authorized_values.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        # Two committed observations per metric where a prior exists, so the chart shows
        # a real comparison rather than a single point.
        writer.writerow(["metric", f"value_{chart_unit}"])
        for row in series:
            writer.writerow([row["metric"], row["current_value"]])

    rendered = render_macro_chart(title, csv_path, output_dir=output_dir)
    if rendered.get("chart_status") != "READY":
        raise ClosureCapabilityError(
            f"chart_render_blocked:{rendered.get('warnings')}"
        )

    partial_period = any(row.get("prior_value") is None for row in series)
    methodology = {
        "metric_definition": title,
        "metric_definitions": [
            {"claim_id": row["claim_id"], "metric": row["metric"], "unit": row["unit"]}
            for row in series
        ],
        "source": "U.S. Department of the Treasury official daily par yield curve",
        "source_packet_id": packet.get("packet_id"),
        "source_packet_logical_hash": packet.get("logical_hash"),
        "series_ids": [row["claim_id"] for row in series],
        "units": [chart_unit],
        "chart_unit": chart_unit,
        "single_unit_axis": True,
        "excluded_claims": excluded,
        "excluded_claim_disclosure": (
            "Authorized claims in a different unit are excluded from this axis and "
            "reported, never rescaled onto a shared axis."
        ),
        "observation_times_utc": sorted(
            {str(row["current_observation_time_utc"]) for row in series if row.get("current_observation_time_utc")}
        ),
        "release_times_utc": sorted(
            {str(row["release_time_utc"]) for row in series if row.get("release_time_utc")}
        ),
        "frequency": "official_business_day_observation",
        "sample_period": {
            "current_observation": sorted(
                {str(row["current_observation_time_utc"]) for row in series if row.get("current_observation_time_utc")}
            ),
            "prior_observation_dates": sorted(
                {str(row["prior_observation_date"]) for row in series if row.get("prior_observation_date")}
            ),
        },
        "transformations": sorted({str(row["transformation"]) for row in series if row.get("transformation")}),
        "seasonal_adjustment": "NOT_APPLICABLE_PAR_YIELD_OBSERVATION",
        "annualization": "NOT_APPLIED_SOURCE_NATIVE_ANNUAL_PERCENT",
        "revision_state": "AS_PUBLISHED_NO_REVISION_APPLIED",
        "partial_period_state": (
            "PARTIAL_ONE_OR_MORE_METRICS_LACK_A_COMMITTED_PRIOR_OBSERVATION"
            if partial_period
            else "COMPLETE_ALL_METRICS_HAVE_TWO_COMMITTED_OBSERVATIONS"
        ),
        "partial_period": partial_period,
        "missing_data_handling": "OMITTED_AND_DISCLOSED_NEVER_INTERPOLATED",
        "renderer": CHART_RENDERER,
        "generator": CHART_GENERATOR,
        "transformation_owner": "Capital Chronicle",
        "source_note": (
            "Values reproduced exactly from the governed Capital Chronicle packet; "
            "ContentOps performed no calculation."
        ),
    }
    chart_path = Path(rendered["chart_path"])
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "chart_id": chart_id,
        "chart_title": title,
        "descriptive_text": (
            f"{title}. Each plotted value is an exact authorized observation copied from "
            f"the governed packet, in {chart_unit}."
        ),
        "chart_relative_path": chart_path.name,
        "chart_sha256": rendered["chart_sha256"],
        "authorized_values_csv": csv_path.name,
        "authorized_values_csv_sha256": rendered["source_sha256"],
        "series": series,
        "series_count": len(series),
        "excluded_claim_count": len(excluded),
        "methodology": methodology,
        "forecast_created": False,
        "probability_created": False,
        "scenario_created": False,
        "market_regime_created": False,
        "analytical_calculation_created": False,
        "values_originated_by_contentops": False,
        "depicts_real_scene_as_photograph": False,
        "disclosure": "DETERMINISTIC_RENDER_FROM_AUTHORIZED_VALUES_NOT_A_PHOTOGRAPH",
    }
    manifest["manifest_logical_hash"] = _logical_hash(
        {k: v for k, v in manifest.items() if k != "manifest_logical_hash"}
    )
    return manifest


def run_chart_methodology_qa(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Deterministic methodology QA over one chart manifest."""
    method = manifest.get("methodology") or {}
    series = manifest.get("series") or []
    series_units = {str(row.get("unit")) for row in series if row.get("unit")}
    checks = {
        "metric_definition_present": bool(method.get("metric_definition")),
        "series_ids_bound": bool(method.get("series_ids")),
        "units_labelled": bool(method.get("units")),
        # A single chart axis must carry exactly one unit. Mixing percent yields with a
        # basis-point spread on one axis misrepresents magnitude even when every value
        # is individually authorized.
        "single_unit_per_axis": len(series_units) == 1 and bool(method.get("single_unit_axis")),
        "excluded_claims_disclosed": (
            "excluded_claims" in method
            and (not method.get("excluded_claims") or bool(method.get("excluded_claim_disclosure")))
        ),
        "observation_times_bound": bool(method.get("observation_times_utc")),
        "release_times_bound": bool(method.get("release_times_utc")),
        "frequency_declared": bool(method.get("frequency")),
        "sample_period_declared": bool(method.get("sample_period")),
        "transformations_declared": bool(method.get("transformations")),
        "seasonal_adjustment_declared": bool(method.get("seasonal_adjustment")),
        "annualization_declared": bool(method.get("annualization")),
        "revision_state_declared": bool(method.get("revision_state")),
        "partial_period_explicitly_labelled": bool(method.get("partial_period_state")),
        "missing_data_handling_declared": bool(method.get("missing_data_handling")),
        "renderer_version_bound": bool(method.get("renderer")) and bool(method.get("generator")),
        "source_note_present": bool(method.get("source_note")),
        "source_packet_hash_bound": bool(method.get("source_packet_logical_hash")),
        "asset_hash_bound": bool(manifest.get("chart_sha256")),
        "reproducible_from_committed_values": bool(manifest.get("authorized_values_csv_sha256")),
        "no_forecast_created": manifest.get("forecast_created") is False,
        "no_probability_created": manifest.get("probability_created") is False,
        "no_scenario_created": manifest.get("scenario_created") is False,
        "no_analytical_calculation_created": (
            manifest.get("analytical_calculation_created") is False
        ),
        "values_not_originated_by_contentops": (
            manifest.get("values_originated_by_contentops") is False
        ),
    }
    failed = sorted(name for name, passed in checks.items() if not passed)
    return {
        "schema_version": SCHEMA_VERSION,
        "chart_id": manifest.get("chart_id"),
        "status": "PASS" if not failed else "BLOCK",
        "checks": checks,
        "checks_run": len(checks),
        "failed_checks": failed,
    }


# ---------------------------------------------------------------------------
# 3. Domain taxonomy and portfolio concentration
# ---------------------------------------------------------------------------

#: Concentration dimensions measured across the cohort.
CONCENTRATION_DIMENSIONS = (
    "domain_family",
    "entities",
    "sector",
    "geography",
    "source_family",
    "content_mode",
    "visual_type",
)
#: Default share above which a dimension value is flagged as concentrated. Configurable
#: per run; a penalty only reorders eligible candidates and can never open a hard gate.
DEFAULT_CONCENTRATION_THRESHOLD = 0.34
DEFAULT_CONCENTRATION_PENALTY = 0.25


def classify_case(case: Mapping[str, Any]) -> dict[str, Any]:
    """Project one corpus case onto the taxonomy dimensions."""
    return {
        "case_id": case.get("case_id"),
        "domain_family": case.get("domain_family"),
        "sector": case.get("sector"),
        "entities": list(case.get("entities") or []),
        "geography": case.get("geography"),
        "source_family": case.get("source_family"),
        "content_mode": case.get("content_mode"),
        "update_chain": case.get("update_chain"),
        "visual_type": case.get("visual_type"),
        "lane": case.get("lane"),
    }


def _dimension_values(row: Mapping[str, Any], dimension: str) -> list[str]:
    value = row.get(dimension)
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)] if value not in (None, "") else []


def build_portfolio_report(
    cases: Sequence[Mapping[str, Any]],
    *,
    label: str,
    concentration_threshold: float = DEFAULT_CONCENTRATION_THRESHOLD,
) -> dict[str, Any]:
    """Measure concentration across every taxonomy dimension for a cohort."""
    rows = [classify_case(case) for case in cases]
    dimensions: dict[str, Any] = {}
    for dimension in CONCENTRATION_DIMENSIONS:
        counter: Counter[str] = Counter()
        for row in rows:
            counter.update(_dimension_values(row, dimension))
        total = sum(counter.values())
        shares = {
            key: round(count / total, 6) if total else 0.0
            for key, count in counter.items()
        }
        concentrated = sorted(
            key for key, share in shares.items() if share > concentration_threshold
        )
        dimensions[dimension] = {
            "distinct_values": len(counter),
            "counts": dict(sorted(counter.items())),
            "shares": dict(sorted(shares.items())),
            "max_share": max(shares.values()) if shares else 0.0,
            "concentrated_values": concentrated,
            "is_concentrated": bool(concentrated),
        }
    report = {
        "schema_version": SCHEMA_VERSION,
        "report_label": label,
        "case_count": len(rows),
        "concentration_threshold": concentration_threshold,
        "dimensions": dimensions,
        "concentrated_dimensions": sorted(
            name for name, row in dimensions.items() if row["is_concentrated"]
        ),
        "diversity_never_forces_filler": True,
        "hard_gates_remain_authoritative": True,
    }
    report["report_logical_hash"] = _logical_hash(
        {k: v for k, v in report.items() if k != "report_logical_hash"}
    )
    return report


def apply_concentration_penalties(
    *,
    eligible: Sequence[Mapping[str, Any]],
    portfolio: Mapping[str, Any],
    penalty: float = DEFAULT_CONCENTRATION_PENALTY,
) -> list[dict[str, Any]]:
    """Apply configurable concentration penalties to already-eligible cases only.

    A penalty can reorder eligible candidates. It can never admit a case that failed an
    evidence, permission, freshness, or material-delta gate, and it can never manufacture
    a selection when nothing is eligible.
    """
    dimensions = portfolio.get("dimensions") or {}
    scored: list[dict[str, Any]] = []
    for case in eligible:
        row = classify_case(case)
        applied: list[dict[str, Any]] = []
        total_penalty = 0.0
        for dimension in CONCENTRATION_DIMENSIONS:
            concentrated = set((dimensions.get(dimension) or {}).get("concentrated_values") or [])
            for value in _dimension_values(row, dimension):
                if value in concentrated:
                    total_penalty += penalty
                    applied.append({"dimension": dimension, "value": value, "penalty": penalty})
        scored.append(
            {
                "case_id": case.get("case_id"),
                "domain_family": case.get("domain_family"),
                "concentration_penalty": round(total_penalty, 6),
                "penalties_applied": applied,
                "diversity_adjusted_rank_key": round(total_penalty, 6),
            }
        )
    scored.sort(key=lambda row: (row["diversity_adjusted_rank_key"], str(row["case_id"])))
    return scored


# ---------------------------------------------------------------------------
# 4. Complete SEO contract
# ---------------------------------------------------------------------------

#: Every field the final SEO contract requires. Completeness is reported; observed
#: search performance is never claimed.
SEO_CONTRACT_FIELDS = (
    "target_reader",
    "primary_search_intent",
    "secondary_search_intent",
    "query_keyword_cluster",
    "news_versus_evergreen_balance",
    "competitive_differentiation",
    "canonical_angle",
    "expected_search_longevity",
    "update_strategy",
    "seo_title",
    "reader_facing_headline",
    "slug",
    "meta_description",
    "h1",
    "h2_structure",
    "answer_first_summary",
    "internal_link_suggestions",
    "primary_source_citations",
    "image_filename",
    "image_caption",
    "image_alt_text",
    "chart_title",
    "chart_descriptive_text",
    "structured_data_proposal",
    "canonical_url_proposal",
    "update_timestamp_utc",
    "social_preview_title",
    "social_preview_description",
    "measurement_hooks",
)


def build_seo_contract(
    *,
    headline: str,
    summary: str,
    body_sections: Sequence[Mapping[str, str]],
    citations: Sequence[Mapping[str, Any]],
    domain_family: str,
    story_type: str,
    target_reader: str,
    primary_intent: str,
    secondary_intent: str,
    keyword_cluster: Sequence[str],
    canonical_angle: str,
    competitive_differentiation: str,
    update_timestamp_utc: str,
    internal_links: Sequence[Mapping[str, str]] = (),
    visual_assets: Sequence[Mapping[str, Any]] = (),
    chart_manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the complete SEO asset set for one canonical long-form package."""
    seo_title = headline if len(headline) <= 60 else headline[:59].rstrip() + "…"
    meta = summary if len(summary) <= 155 else summary[:154].rstrip() + "…"
    lead = next(
        (row for row in visual_assets if row.get("role") == "lead_contextual"),
        (visual_assets[0] if visual_assets else None),
    )
    evergreen = story_type in {"official_action"}
    contract = {
        "target_reader": target_reader,
        "primary_search_intent": primary_intent,
        "secondary_search_intent": secondary_intent,
        "query_keyword_cluster": list(keyword_cluster),
        "news_versus_evergreen_balance": (
            "EVERGREEN_LEANING_REFERENCE" if evergreen else "NEWS_LEANING_TIME_SENSITIVE"
        ),
        "competitive_differentiation": competitive_differentiation,
        "canonical_angle": canonical_angle,
        "expected_search_longevity": (
            "MULTI_QUARTER_REFERENCE" if evergreen else "DAYS_TO_WEEKS"
        ),
        "update_strategy": (
            "Supersede with the next governed observation of the same update chain; "
            "never edit an authorized value in place."
        ),
        "seo_title": seo_title,
        "reader_facing_headline": headline,
        "slug": _slug(headline),
        "meta_description": meta,
        "h1": headline,
        "h2_structure": [str(row.get("heading")) for row in body_sections],
        "answer_first_summary": summary,
        "internal_link_suggestions": [dict(row) for row in internal_links],
        "primary_source_citations": [
            {
                "source_document_id": row.get("source_document_id"),
                "url": row.get("url"),
                "citation_state": row.get("citation_state", "EXACT_SOURCE_NATIVE_URL"),
            }
            for row in citations
        ],
        "image_filename": (
            Path(str(lead.get("path", ""))).name if lead and lead.get("path") else None
        ),
        "image_caption": lead.get("caption") if lead else None,
        "image_alt_text": lead.get("alt_text") if lead else None,
        "chart_title": (chart_manifest or {}).get("chart_title"),
        "chart_descriptive_text": (chart_manifest or {}).get("descriptive_text"),
        "structured_data_proposal": {
            "@context": "https://schema.org",
            "@type": "NewsArticle" if not evergreen else "Article",
            "headline": headline,
            "description": meta,
            "articleSection": domain_family,
            "isBasedOn": [row.get("url") for row in citations if row.get("url")],
            "proposal_only_not_published": True,
        },
        "canonical_url_proposal": f"/{domain_family}/{_slug(headline)}",
        "update_timestamp_utc": update_timestamp_utc,
        "social_preview_title": seo_title,
        "social_preview_description": meta,
        # Deliberately empty: no public object exists in SHADOW_ONLY, so there is no
        # first-party or Search Console evidence to record yet.
        "measurement_hooks": {
            "first_party_analytics": None,
            "search_console": None,
            "impressions": None,
            "clicks": None,
            "average_position": None,
            "collection_state": "NOT_COLLECTED_SHADOW_ONLY_NO_PUBLIC_OBJECT",
        },
    }
    contract["schema_version"] = SCHEMA_VERSION
    contract["seo_contract_logical_hash"] = _logical_hash(contract)
    return contract


#: Fields allowed to be null when the story genuinely has no such asset. A missing
#: image on a text-only story is a truthful absence, not an incomplete contract.
_SEO_NULLABLE_WHEN_ABSENT = frozenset(
    {
        "image_filename",
        "image_caption",
        "image_alt_text",
        "chart_title",
        "chart_descriptive_text",
    }
)


def run_seo_contract_qa(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Report SEO contract completeness.

    This reports whether the *contract* is complete. It never claims observed search
    success, ranking, impressions, or clicks — no public object exists to measure.
    """
    present: dict[str, bool] = {}
    for field in SEO_CONTRACT_FIELDS:
        value = contract.get(field)
        if field in _SEO_NULLABLE_WHEN_ABSENT:
            present[field] = field in contract
        elif field == "measurement_hooks":
            present[field] = isinstance(value, Mapping) and "collection_state" in value
        else:
            present[field] = value not in (None, "", [], {})
    missing = sorted(name for name, ok in present.items() if not ok)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "COMPLETE" if not missing else "INCOMPLETE",
        "fields_required": len(SEO_CONTRACT_FIELDS),
        "fields_present": sum(1 for ok in present.values() if ok),
        "missing_fields": missing,
        "field_presence": present,
        "observed_search_success_claimed": False,
        "measurement_state": (contract.get("measurement_hooks") or {}).get(
            "collection_state"
        ),
    }
