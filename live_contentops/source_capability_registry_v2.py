"""Capability-driven story requirements; source adapters remain replaceable."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

DEFAULT_PATH = Path("docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/source_evidence_capability_registry_v2.json")


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
    configured_mode = str(row.get("article_mode") or "analysis")
    requested_mode = str(request.get("article_mode") or "")
    mode_blockers = (
        ["article_mode_mismatch_with_capability"]
        if requested_mode and requested_mode != configured_mode
        else []
    )
    return {
        "status": "PASS" if not mode_blockers else "BLOCK",
        "story_type": story_type,
        "source_family_id": source_family_id,
        "required_evidence_capabilities": list(row.get("required_evidence_capabilities") or []),
        "market_context_required": bool(row.get("market_context_required")),
        "market_snapshot_required": bool(
            row.get("market_snapshot_required", row.get("market_context_required"))
        ),
        "article_mode": configured_mode,
        "freshness_policy": row.get("freshness_policy"),
        "freshness_requirements": dict(row.get("freshness_requirements") or {}),
        "visual_roles": list(row.get("visual_roles") or []),
        "visual_policy": row.get("visual_policy", "long_form_article"),
        "visual_requirements": dict(row.get("visual_requirements") or {}),
        "source_adapter_families": list(row.get("source_adapter_families") or []),
        "blockers": mode_blockers,
    }
