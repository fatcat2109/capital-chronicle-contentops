"""Capability-driven story requirements; source adapters remain replaceable."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

DEFAULT_PATH = Path("docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/source_evidence_capability_registry_v2.json")
VALID_ARTICLE_MODES = frozenset(
    {
        "analysis",
        "correction",
        "data_release",
        "deep_analysis",
        "explainer",
        "live_update",
        "market_move",
        "policy_decision",
        "retrospective",
        "scenario_outlook",
        "straight_news",
    }
)


def load_source_capability_registry(path: str | Path = DEFAULT_PATH) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if value.get("schema_version") != "contentops.source_evidence_capability_registry.v2":
        raise ValueError("source_capability_registry_version_invalid")
    return value


def resolve_story_capabilities(request: Mapping[str, Any], registry: Mapping[str, Any]) -> dict[str, Any]:
    story_type = str(request.get("story_type") or "")
    story_types = registry.get("story_types") or {}
    row = story_types.get(story_type)
    source_family_id = str(request.get("source_family_id") or "")
    if not isinstance(row, Mapping) and source_family_id:
        matches = [
            (candidate_type, candidate)
            for candidate_type, candidate in story_types.items()
            if isinstance(candidate, Mapping)
            and source_family_id in (candidate.get("source_family_ids") or [])
        ]
        if len(matches) == 1:
            story_type, row = matches[0]
        elif len(matches) > 1:
            return {
                "status": "BLOCK",
                "story_type": story_type,
                "source_family_id": source_family_id,
                "blockers": ["ambiguous_source_family_capability"],
            }
    if not isinstance(row, Mapping):
        return {
            "status": "BLOCK",
            "story_type": story_type,
            "source_family_id": source_family_id,
            "blockers": ["unsupported_story_type"],
        }
    requested_mode = str(request.get("article_mode") or "")
    mode_blockers: list[str] = []
    if requested_mode and requested_mode not in VALID_ARTICLE_MODES:
        mode_blockers.append("caller_article_mode_invalid")
    base_configured_mode = str(row.get("article_mode") or "")
    mode_profiles = row.get("article_mode_profiles") or {}
    if not isinstance(mode_profiles, Mapping):
        mode_blockers.append("registry_article_mode_profiles_invalid")
        mode_profiles = {}
    resolved_row = dict(row)
    mode_profile_used = False
    if requested_mode and mode_profiles:
        profile = mode_profiles.get(requested_mode)
        if not isinstance(profile, Mapping) and requested_mode != base_configured_mode:
            mode_blockers.append("article_mode_unsupported_for_story_type")
        elif isinstance(profile, Mapping):
            resolved_row.update(profile)
            resolved_row["article_mode"] = requested_mode
            mode_profile_used = True
    configured_mode = str(resolved_row.get("article_mode") or "")
    if configured_mode and configured_mode not in VALID_ARTICLE_MODES:
        mode_blockers.append("registry_article_mode_invalid")
    if (
        configured_mode
        and requested_mode
        and requested_mode != configured_mode
        and not mode_profile_used
    ):
        mode_blockers.append("article_mode_mismatch_with_capability")
    effective_mode = configured_mode or requested_mode
    if not effective_mode:
        mode_blockers.append("article_mode_unresolved")
    market_context_required = bool(resolved_row.get("market_context_required"))
    capital_chronicle_authority_required = bool(
        resolved_row.get(
            "capital_chronicle_authority_required", market_context_required
        )
    )
    return {
        "status": "PASS" if not mode_blockers else "BLOCK",
        "story_type": story_type,
        "source_family_id": source_family_id,
        "required_evidence_capabilities": list(resolved_row.get("required_evidence_capabilities") or []),
        "market_context_required": market_context_required,
        "capital_chronicle_authority_required": capital_chronicle_authority_required,
        "market_sensitive": bool(
            resolved_row.get(
                "market_sensitive",
                resolved_row.get("market_snapshot_required", market_context_required),
            )
        ),
        "market_snapshot_required": bool(
            resolved_row.get("market_snapshot_required", market_context_required)
        ),
        "article_mode": effective_mode,
        "article_mode_source": (
            "story_type_article_mode_profile"
            if mode_profile_used
            else "registry" if configured_mode else "caller" if requested_mode else "unresolved"
        ),
        "freshness_policy": resolved_row.get("freshness_policy"),
        "freshness_requirements": dict(resolved_row.get("freshness_requirements") or {}),
        "visual_roles": list(resolved_row.get("visual_roles") or []),
        "visual_policy": resolved_row.get("visual_policy", "long_form_article"),
        "visual_requirements": dict(resolved_row.get("visual_requirements") or {}),
        "source_adapter_families": list(resolved_row.get("source_adapter_families") or []),
        "blockers": mode_blockers,
    }


def resolve_platform_visual_expectation(
    *,
    platform_id: str,
    content_surface: str,
    variant_mode: str,
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    platform = (registry.get("platform_visual_expectations") or {}).get(platform_id)
    rules = list(platform.get("rules") or []) if isinstance(platform, Mapping) else []
    matches = [
        rule
        for rule in rules
        if isinstance(rule, Mapping)
        and str(rule.get("content_surface") or "") == content_surface
        and str(rule.get("variant_mode") or "") == variant_mode
    ]
    rule = dict(matches[0]) if len(matches) == 1 else {}
    effective_visual_mode = str(rule.get("effective_visual_mode") or "")
    policy = str(rule.get("policy") or "")
    minimum_visual_count = rule.get("minimum_visual_count")
    valid_minimum = (
        isinstance(minimum_visual_count, int)
        and not isinstance(minimum_visual_count, bool)
        and minimum_visual_count >= 0
    )
    malformed = (
        len(matches) == 1
        and (
            not effective_visual_mode
            or not policy
            or not valid_minimum
            or (effective_visual_mode != "text_only" and minimum_visual_count == 0)
        )
    )
    if len(matches) != 1 or malformed:
        blocker = (
            "ambiguous_platform_visual_mode"
            if len(matches) > 1
            else "malformed_platform_visual_policy"
            if malformed
            else "unsupported_platform_visual_mode"
        )
        return {
            "status": "BLOCK",
            "platform_id": platform_id,
            "content_surface": content_surface,
            "variant_mode": variant_mode,
            "effective_visual_mode": "fail_closed_visual_required",
            "policy": "fail_closed_unregistered_visual_mode",
            "minimum_visual_count": 1,
            "requires_lead_visual": False,
            "requires_visual_diversity": False,
            "blockers": [blocker],
        }
    return {
        "status": "PASS",
        "platform_id": platform_id,
        "content_surface": content_surface,
        "variant_mode": variant_mode,
        "effective_visual_mode": effective_visual_mode,
        "policy": policy,
        "minimum_visual_count": minimum_visual_count,
        "requires_lead_visual": bool(rule.get("requires_lead_visual")),
        "requires_visual_diversity": bool(rule.get("requires_visual_diversity")),
        "blockers": [],
    }
