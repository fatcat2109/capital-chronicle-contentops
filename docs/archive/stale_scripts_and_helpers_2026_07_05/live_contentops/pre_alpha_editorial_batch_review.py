"""Local-only pre-alpha editorial batch review packet generator (Task 0105).

Deterministic, repo-local. Consumes the 0103 seed library / editorial calendar
and the 0096 prompt-pack / style-profile / editorial-rubric config bundle and
produces a single reviewable operator BATCH containing:

    * review queue items for SAFE planned seeds (via 0095 engine + 0097 renderer)
    * a preserved blocked-content report for unsafe seeds (never dropped)

This is a REVIEW WORKBENCH only. It does NOT approve, export, publish, schedule,
post, ingest metrics, or call any provider/network/platform/LLM. It NEVER reads
environment secret files, NEVER creates approval / manual-export / content-ledger
objects, and NEVER produces public-postable or publish-ready output.

The batch packet fails closed (packet_status="blocked") if any hard-boundary
flag is unsafe or any child rendered packet reports a blocked guardrail status.
Blocked seeds are always surfaced with their guardrail reasons.
"""

import json
import os

from live_contentops.pre_alpha_content_engine import (
    STATIC_TIMESTAMP,
    build_editorial_packet,
)
from live_contentops.pre_alpha_draft_renderer import render_review_packet
from live_contentops import pre_alpha_seed_library as seed_lib

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
BATCH_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_editorial_batch_review_packet.schema.json"
)

FIXTURE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "pre_alpha_editorial_batch_review"
)
DEFAULT_CONFIG = os.path.join(FIXTURE_DIR, "valid_batch_config.json")

# Hard-boundary flags pinned on every batch packet, independent of input.
# Each must hold its required value or the packet fails closed.
_REQUIRED_FLAGS = {
    "local_only": True,
    "fixture_only": True,
    "manual_review_required": True,
    "reviewer_required": True,
    "auto_approval": False,
    "public_postable": False,
    "approval_packet_created": False,
    "manual_export_packet_created": False,
    "content_ledger_publish_status_changed": False,
    "provider_call_allowed_now": False,
    "network_call_allowed_now": False,
    "platform_api_call_allowed_now": False,
    "scheduler_allowed": False,
    "metrics_ingestion_allowed": False,
    "live_execution_allowed_now": False,
    "credential_or_env_read_allowed": False,
}


def load_batch_schema():
    with open(os.path.abspath(BATCH_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def _hard_boundary_flags():
    """Return a fresh copy of the pinned hard-boundary flags."""
    return dict(_REQUIRED_FLAGS)


def _audit_flags(flags):
    """Return safety violations: any pinned flag missing or holding wrong value."""
    violations = []
    for flag, expected in _REQUIRED_FLAGS.items():
        if flag not in flags:
            violations.append("missing_flag:%s" % flag)
        elif flags[flag] is not expected:
            violations.append("%s=%r" % (flag, flags[flag]))
    return violations


def load_config(config_path=None):
    """Load the 0096 config bundle (prompt pack / style / rubric) from disk."""
    target = config_path or DEFAULT_CONFIG
    with open(os.path.abspath(target), "r", encoding="utf-8") as f:
        return json.load(f)



def build_batch_review_packet(library, config, planning_window=None,
                              batch_review_packet_id=None,
                              source_refs=None):
    """Build a deterministic editorial batch review packet.

    Safe (valid) seeds are run through the 0095 engine and 0097 renderer to
    produce review queue items. Blocked seeds are preserved in
    blocked_content_report with their guardrail reasons. Nothing is approved,
    exported, published, scheduled, or sent. Safety flags are always pinned.

    Fails closed (packet_status="blocked") when any hard-boundary flag is unsafe
    or any safe-seed render reports a blocked guardrail status.
    """
    blocked_reasons = []

    prompt_pack = config.get("prompt_pack") if isinstance(config, dict) else None
    style_profile = config.get("style_profile") if isinstance(config, dict) else None
    editorial_rubric = config.get("editorial_rubric") if isinstance(config, dict) else None

    lib_result = seed_lib.validate_library(library)
    plan = seed_lib.build_calendar_plan(library, planning_window=planning_window)

    seeds = library.get("seeds") if isinstance(library, dict) else []
    seeds = seeds or []

    planned_items = plan.get("planned_items") or []
    by_seed_id = {}
    for idx, item in enumerate(planned_items):
        by_seed_id[item.get("seed_id") or ("seed_index_%d" % idx)] = item

    selected_safe_seed_ids = []
    blocked_seed_ids = []
    blocked_content_report = []
    rendered_packets = []
    review_queue_items = []

    for idx, seed in enumerate(seeds):
        sid = seed.get("seed_id") if isinstance(seed, dict) else None
        key = sid or ("seed_index_%d" % idx)
        plan_item = by_seed_id.get(key, {})
        is_safe = plan_item.get("review_status") == "needs_manual_review"

        if not is_safe:
            blocked_seed_ids.append(sid)
            blocked_content_report.append({
                "seed_id": sid,
                "content_zone": plan_item.get("content_zone")
                if plan_item else (seed.get("content_zone") if isinstance(seed, dict) else None),
                "blocked_reasons": list(plan_item.get("blocked_reasons") or []),
            })
            continue

        # Safe seed: build the editorial packet and render review queue items.
        editorial_packet = build_editorial_packet(seed)
        rendered = render_review_packet(
            editorial_packet, prompt_pack, style_profile, editorial_rubric
        )
        rendered_packets.append(rendered)

        if rendered.get("guardrail_status") != "pass":
            # A seed the calendar called safe but that fails at render time is a
            # real guardrail event: record it as blocked, never silently keep it.
            blocked_seed_ids.append(sid)
            reasons = list(rendered.get("blocked_reasons") or ["rendered_packet_blocked"])
            blocked_content_report.append({
                "seed_id": sid,
                "content_zone": plan_item.get("content_zone"),
                "blocked_reasons": ["render:%s" % r for r in reasons],
            })
            blocked_reasons.append("safe_seed_render_blocked:%s" % sid)
            continue

        selected_safe_seed_ids.append(sid)
        for item in (rendered.get("review_queue_items") or []):
            review_queue_items.append(item)

    # Any review queue item that itself reports a blocked review status is a
    # hard fail-closed condition.
    for item in review_queue_items:
        if item.get("review_status") != "needs_manual_review":
            blocked_reasons.append(
                "review_item_blocked:%s" % item.get("review_queue_item_id")
            )

    flags = _hard_boundary_flags()
    flag_violations = _audit_flags(flags)
    if flag_violations:
        blocked_reasons.extend("safety:%s" % v for v in flag_violations)

    if not lib_result.get("valid"):
        blocked_reasons.extend("library:%s" % e for e in lib_result.get("errors") or [])

    safety_audit = {
        "violations": flag_violations,
        "unsafe_flag_count": len(flag_violations),
    }

    packet_status = "pass" if not blocked_reasons else "blocked"

    safe_count = plan.get("safe_item_count", 0)
    blocked_count = plan.get("blocked_item_count", 0)

    return {
        "batch_review_packet_id": batch_review_packet_id
        or "batch_%s" % (library.get("library_id") if isinstance(library, dict) else "unknown"),
        "created_at": STATIC_TIMESTAMP,
        "source_refs": list(source_refs or []),
        "planning_window": plan.get("planning_window"),
        "seed_library_summary": {
            "library_id": plan.get("source_library_id"),
            "total_seeds": len(seeds),
            "safe_seed_count": safe_count,
            "blocked_seed_count": blocked_count,
        },
        "calendar_plan_summary": {
            "calendar_plan_id": plan.get("calendar_plan_id"),
            "planned_item_count": len(planned_items),
            "safe_item_count": safe_count,
            "blocked_item_count": blocked_count,
        },
        "selected_safe_seed_ids": selected_safe_seed_ids,
        "blocked_seed_ids": blocked_seed_ids,
        "blocked_content_report": blocked_content_report,
        "rendered_packets": rendered_packets,
        "review_queue_items": review_queue_items,
        "operator_review_checklist": _operator_review_checklist(
            len(selected_safe_seed_ids), len(blocked_seed_ids)
        ),
        "hard_boundary_flags": flags,
        "safety_audit": safety_audit,
        "blocked_reasons": blocked_reasons,
        "packet_status": packet_status,
    }


def _operator_review_checklist(safe_count, blocked_count):
    """Deterministic MANUAL operator review checklist (review-only)."""
    items = [
        "Manually review each of the %d safe review-queue item(s) before any draft work." % safe_count,
        "Confirm every item is general/process or has source artifact IDs.",
        "Confirm no buy/sell/hold, targets, position sizing, or signal framing.",
        "Confirm market notes carry limitations, freshness, and educational-only posture.",
    ]
    if blocked_count > 0:
        items.append(
            "Resolve or retire %d blocked seed(s); guardrail reasons are recorded, not dropped." % blocked_count
        )
    items.append("No approval, export, publish, schedule, or send is performed by this workbench.")
    items.append("All publishing remains manual and human-reviewed.")
    return items


def build_batch_review_packet_from_files(library_path=None, config_path=None,
                                         planning_window=None):
    """Build the batch packet from local fixture files. Local file read only."""
    lib_path = library_path or seed_lib.DEFAULT_LIBRARY
    with open(os.path.abspath(lib_path), "r", encoding="utf-8") as f:
        library = json.load(f)
    config = load_config(config_path)
    return build_batch_review_packet(
        library, config, planning_window=planning_window,
        source_refs=[
            os.path.basename(os.path.abspath(lib_path)),
            os.path.basename(os.path.abspath(config_path or DEFAULT_CONFIG)),
        ],
    )


def summary(library_path=None, config_path=None):
    """Deterministic local capability summary for the CLI. Fixture read only."""
    out = {
        "status": "pre-alpha editorial batch review packet active",
        "local_only": True,
        "fixture_only": True,
        "design_only": True,
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read": False,
        "fake_alpha_output": False,
        "public_postable_output": False,
        "approval_packet_created": False,
        "manual_export_packet_created": False,
        "content_ledger_publish_status_changed": False,
        "platform_api_call_allowed_now": False,
        "live_execution_allowed_now": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
        "manual_review_required": True,
        "reviewer_required": True,
        "auto_approval": False,
    }
    try:
        packet = build_batch_review_packet_from_files(library_path, config_path)
        out["packet_status"] = packet.get("packet_status")
        out["total_seeds"] = packet["seed_library_summary"]["total_seeds"]
        out["selected_safe_seed_count"] = len(packet.get("selected_safe_seed_ids") or [])
        out["blocked_seed_count"] = len(packet.get("blocked_seed_ids") or [])
        out["rendered_packet_count"] = len(packet.get("rendered_packets") or [])
        out["review_queue_item_count"] = len(packet.get("review_queue_items") or [])
        out["unsafe_flag_count"] = packet["safety_audit"]["unsafe_flag_count"]
    except Exception:
        out["packet_status"] = "unavailable"
    return out

