"""Versioned brand, editorial-persona, and founder-led distribution identities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

DEFAULT_REGISTRY_PATH = Path("docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/distribution_identity_persona_registry_v2.json")


def load_identity_registry(path: str | Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if value.get("schema_version") != "contentops.distribution_identity_persona_registry.v2":
        raise ValueError("identity_registry_schema_version_invalid")
    return value


def verify_distribution_identity(platform: str, observed_identity: str, registry: Mapping[str, Any]) -> dict[str, Any]:
    row = (registry.get("destinations") or {}).get(platform)
    if not isinstance(row, Mapping):
        return {"status": "BLOCK", "reason": "platform_identity_not_registered"}
    approved = {str(value).casefold() for value in row.get("approved_visible_identities") or []}
    matched = observed_identity.casefold() in approved
    return {
        "status": "PASS" if matched else "BLOCK_WRONG_ACCOUNT_OR_PERSONA",
        "platform": platform,
        "observed_identity": observed_identity,
        "identity_class": row.get("identity_class"),
        "approved": matched,
    }


def validate_fresh_run_action(
    *, platform: str, fresh_run: bool, action: str, story_id: str, existing_story_id: str | None = None, parent_id: str | None = None
) -> dict[str, Any]:
    blockers: list[str] = []
    if platform == "linkedin" and fresh_run and action.startswith("edit") and existing_story_id != story_id:
        blockers.append("fresh_linkedin_story_cannot_edit_historical_activity")
    if platform == "threads" and action == "reply" and not str(parent_id or "").strip():
        blockers.append("threads_reply_requires_nonempty_parent_id")
    return {"status": "PASS" if not blockers else "BLOCK", "blockers": blockers}
