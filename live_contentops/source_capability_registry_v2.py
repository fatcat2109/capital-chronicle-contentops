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
    row = (registry.get("story_types") or {}).get(story_type)
    if not isinstance(row, Mapping):
        return {"status": "BLOCK", "story_type": story_type, "blockers": ["unsupported_story_type"]}
    return {
        "status": "PASS",
        "story_type": story_type,
        "required_evidence_capabilities": list(row.get("required_evidence_capabilities") or []),
        "market_context_required": bool(row.get("market_context_required")),
        "freshness_policy": row.get("freshness_policy"),
        "visual_roles": list(row.get("visual_roles") or []),
        "source_adapter_families": list(row.get("source_adapter_families") or []),
    }
