"""Local-only pre-alpha content seed library and editorial calendar (Task 0103).

Deterministic, repo-local. Loads a content SEED LIBRARY from disk, validates
each seed against the 0095 content-engine guardrails (reused as a single source
of truth), and deterministically sequences SAFE/reviewable seeds into an
editorial calendar plan. Blocked seeds are preserved as blocked items, never
silently dropped.

This module performs NO network/search/provider/LLM/platform/credential access.
It NEVER posts, NEVER fetches, NEVER reads `.env`, NEVER schedules live, NEVER
ingests metrics, and NEVER produces public-postable or publish-ready output.
Every planned item defaults to not_published / manual_only with null metrics.
"""

import json
import os

from live_contentops.pre_alpha_content_engine import (
    STATIC_TIMESTAMP,
    validate_seed,
)

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
LIBRARY_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "pre_alpha_content_seed_library.schema.json")
CALENDAR_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "pre_alpha_editorial_calendar_plan.schema.json")

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures", "pre_alpha_seed_library")

ALLOWED_CONTENT_ZONES = {
    "macro_education",
    "build_in_public",
    "product_update",
    "data_sufficiency",
    "forecast_readiness",
    "failure_forensics",
    "general_process",
}

ALLOWED_CADENCES = {"daily", "weekly", "biweekly", "monthly", "adhoc"}


def load_library_schema():
    with open(os.path.abspath(LIBRARY_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def load_calendar_schema():
    with open(os.path.abspath(CALENDAR_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def validate_library(library):
    """Return {"valid": bool, "errors": [...], "seed_results": {seed_id: result}}.

    Deterministic. Top-level errors block the whole library; per-seed results
    record which seeds are safe (valid) and which are blocked. Blocked seeds are
    NOT dropped here; callers preserve them as blocked items.
    """
    errors = []
    seed_results = {}

    if not isinstance(library, dict):
        return {"valid": False, "errors": ["library_not_object"], "seed_results": {}}

    if not library.get("library_id"):
        errors.append("missing_field:library_id")

    seeds = library.get("seeds")
    if not isinstance(seeds, list) or not seeds:
        errors.append("missing_or_empty_seeds")
        seeds = []

    seen_ids = set()
    for idx, seed in enumerate(seeds):
        sid = seed.get("seed_id") if isinstance(seed, dict) else None
        key = sid or ("seed_index_%d" % idx)
        if sid and sid in seen_ids:
            errors.append("duplicate_seed_id:%s" % sid)
        if sid:
            seen_ids.add(sid)

        zone = seed.get("content_zone") if isinstance(seed, dict) else None
        seed_errors = []
        if zone is None:
            seed_errors.append("missing_field:content_zone")
        elif zone not in ALLOWED_CONTENT_ZONES:
            seed_errors.append("content_zone_not_allowed")

        # Reuse the 0095 guardrail validator as the single source of truth.
        engine_result = validate_seed(seed)
        seed_errors.extend(engine_result.get("errors") or [])

        seed_results[key] = {
            "valid": len(seed_errors) == 0,
            "errors": seed_errors,
            "content_zone": zone,
        }

    return {"valid": len(errors) == 0, "errors": errors, "seed_results": seed_results}


def validate_library_file(path):
    with open(os.path.abspath(path), "r", encoding="utf-8") as f:
        library = json.load(f)
    return validate_library(library)



def build_calendar_plan(library, planning_window=None, calendar_plan_id=None):
    """Deterministically sequence SAFE seeds into an editorial calendar plan.

    Safe (valid) seeds become planned items with review_status
    "needs_manual_review" and publish_status "manual_only". Blocked seeds are
    preserved as planned items with review_status "blocked" and recorded
    blocked_reasons, plus mirrored into blocked_items. Nothing is auto-published:
    publish/url/timestamp/metrics stay non-live / null. Ordering follows the
    library's seed order for determinism.
    """
    lib_result = validate_library(library)
    seeds = library.get("seeds") if isinstance(library, dict) else []
    seeds = seeds or []

    window = planning_window or {
        "start_date": "2026-01-05",
        "end_date": "2026-02-02",
        "cadence": "weekly",
    }

    planned_items = []
    blocked_items = []
    for idx, seed in enumerate(seeds):
        sid = seed.get("seed_id") if isinstance(seed, dict) else None
        key = sid or ("seed_index_%d" % idx)
        sresult = lib_result["seed_results"].get(key, {"valid": False, "errors": ["unknown_seed"]})
        is_safe = sresult.get("valid")

        item = {
            "planned_item_id": "plan_item_%s" % (sid or "unknown_%d" % idx),
            "seed_id": sid,
            "content_zone": seed.get("content_zone") if isinstance(seed, dict) else None,
            "content_type": seed.get("content_type") if isinstance(seed, dict) else None,
            "intended_platforms": list(seed.get("intended_platforms") or []) if isinstance(seed, dict) else [],
            "slot_index": idx,
            "intended_day_or_slot": "slot_%d" % idx,
            "review_status": "needs_manual_review" if is_safe else "blocked",
            "publish_status": "manual_only" if is_safe else "not_published",
            "blocked_reasons": [] if is_safe else list(sresult.get("errors") or []),
            "manual_publish_url": None,
            "manual_publish_timestamp": None,
            "manual_metrics": None,
        }
        planned_items.append(item)
        if not is_safe:
            blocked_items.append(item)

    return {
        "calendar_plan_id": calendar_plan_id or "cal_%s" % (library.get("library_id") if isinstance(library, dict) else "unknown"),
        "created_at": STATIC_TIMESTAMP,
        "source_library_id": library.get("library_id") if isinstance(library, dict) else None,
        "planning_window": window,
        "planned_items": planned_items,
        "blocked_items": blocked_items,
        "library_valid": lib_result["valid"],
        "library_errors": lib_result["errors"],
        "safe_item_count": sum(1 for i in planned_items if i["review_status"] == "needs_manual_review"),
        "blocked_item_count": len(blocked_items),
        "local_only": True,
        "manual_publish_only": True,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
    }


def build_calendar_plan_from_file(path, planning_window=None):
    with open(os.path.abspath(path), "r", encoding="utf-8") as f:
        library = json.load(f)
    return build_calendar_plan(library, planning_window=planning_window)


DEFAULT_LIBRARY = os.path.join(FIXTURE_DIR, "valid_seed_library_with_one_blocked.json")


def summary():
    """Deterministic local capability summary for the CLI. Fixture read only."""
    out = {
        "status": "pre-alpha content seed library and editorial calendar active",
        "local_only": True,
        "fixture_only": True,
        "design_only": True,
        "supported_content_zones": sorted(ALLOWED_CONTENT_ZONES),
        "supported_cadences": sorted(ALLOWED_CADENCES),
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read": False,
        "fake_alpha_output": False,
        "public_postable_output": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
        "manual_review_required": True,
        "auto_approval": False,
    }
    try:
        plan = build_calendar_plan_from_file(DEFAULT_LIBRARY)
        out["default_library_id"] = plan.get("source_library_id")
        out["default_safe_item_count"] = plan.get("safe_item_count")
        out["default_blocked_item_count"] = plan.get("blocked_item_count")
    except Exception:
        out["default_library_id"] = "unavailable"
    return out

