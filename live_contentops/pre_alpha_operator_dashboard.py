"""Local-only pre-alpha ContentOps operator dashboard / packet (Task 0104).

Aggregates the deterministic state of the pre-alpha content system from existing
local fixtures and modules into a single review-only operator control-plane
packet:

    seed library status        (0103 pre_alpha_seed_library)
    editorial calendar status  (0103 pre_alpha_seed_library)
    blocked seed reasons        (0103 pre_alpha_seed_library)
    pipeline demo status        (0101 pre_alpha_pipeline_demo)
    manual export / ledger posture (0099 pre_alpha_manual_export, static)

This module performs NO network/search/provider/LLM/platform/credential access.
It NEVER posts, NEVER fetches, NEVER reads `.env`, NEVER schedules live, NEVER
ingests metrics, and NEVER produces public-postable or publish-ready output.

It is an operator-control artifact only: not a web UI, not a publisher, not a
scheduler, not metrics ingestion, not LLM/provider execution. Blocked seeds are
ALWAYS surfaced with reasons, never dropped. The packet fails closed
(packet_status="blocked") if any hard-boundary flag is unsafe or any child
summary indicates an unsafe publish/network/provider/platform/live state.
"""

import json
import os

from live_contentops.pre_alpha_content_engine import STATIC_TIMESTAMP
from live_contentops import pre_alpha_seed_library as seed_lib
from live_contentops import pre_alpha_pipeline_demo as demo

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
DASHBOARD_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_operator_dashboard_packet.schema.json"
)

# Hard-boundary flags pinned on every dashboard packet, independent of input.
# Each must hold its required value or the packet fails closed.
_REQUIRED_FLAGS = {
    "local_only": True,
    "fixture_only": True,
    "manual_review_required": True,
    "auto_approval": False,
    "public_postable": False,
    "provider_call_allowed_now": False,
    "network_call_allowed_now": False,
    "platform_api_call_allowed_now": False,
    "scheduler_allowed": False,
    "metrics_ingestion_allowed": False,
    "live_execution_allowed_now": False,
    "credential_or_env_read_allowed": False,
}


def load_dashboard_schema():
    with open(os.path.abspath(DASHBOARD_SCHEMA_PATH), "r", encoding="utf-8") as f:
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


def build_dashboard_packet(library_path=None, demo_path=None):
    """Build a deterministic operator dashboard packet from local fixtures.

    Reads only local fixture/schema files. Surfaces safe/blocked seed counts,
    blocked reasons (never dropped), editorial calendar posture, pipeline demo
    status, and manual export/ledger posture. Fails closed if any hard-boundary
    flag is unsafe or any child summary indicates an unsafe state.
    """
    blocked_reasons = []

    lib_path = library_path or seed_lib.DEFAULT_LIBRARY
    plan = seed_lib.build_calendar_plan_from_file(lib_path)
    lib_result = seed_lib.validate_library_file(lib_path)

    total_seeds = len(plan.get("planned_items") or [])
    safe_count = plan.get("safe_item_count", 0)
    blocked_count = plan.get("blocked_item_count", 0)

    # Blocked seeds are ALWAYS surfaced with reasons, never dropped.
    blocked_items = [
        {
            "seed_id": item.get("seed_id"),
            "content_zone": item.get("content_zone"),
            "blocked_reasons": list(item.get("blocked_reasons") or []),
        }
        for item in (plan.get("blocked_items") or [])
    ]

    # Pipeline demo (0101): reflect the real default demo result as evidence.
    demo_result = demo.run_demo_from_file(demo_path)
    demo_status = demo_result.get("demo_status")
    demo_violations = list(demo_result.get("safety_violations") or [])
    if demo_violations:
        blocked_reasons.extend("pipeline_demo:%s" % v for v in demo_violations)

    seed_library_summary = {
        "library_id": plan.get("source_library_id"),
        "total_seeds": total_seeds,
        "safe_seed_count": safe_count,
        "blocked_seed_count": blocked_count,
        "supported_content_zones": sorted(seed_lib.ALLOWED_CONTENT_ZONES),
    }

    editorial_calendar_summary = {
        "calendar_plan_id": plan.get("calendar_plan_id"),
        "planned_item_count": total_seeds,
        "safe_item_count": safe_count,
        "blocked_item_count": blocked_count,
        "manual_review_queue_count": safe_count,
    }

    blocked_content_summary = {
        "blocked_item_count": blocked_count,
        "blocked_items": blocked_items,
    }

    pipeline_demo_summary = {
        "demo_status": demo_status,
        "stages_reached": list(demo_result.get("stages_reached") or []),
        "safety_violations": demo_violations,
    }

    # Manual export / ledger posture (0099): static, non-publishing.
    manual_export_ledger_summary = {
        "manual_publish_only": True,
        "auto_publish_allowed": False,
    }

    operator_next_actions = _operator_next_actions(
        safe_count, blocked_count, blocked_items, demo_status
    )

    flags = _hard_boundary_flags()
    flag_violations = _audit_flags(flags)

    # Cross-check child summaries cannot imply unsafe publish/live state.
    if manual_export_ledger_summary["auto_publish_allowed"] is not False:
        flag_violations.append("manual_export_ledger:auto_publish_allowed")
    if not manual_export_ledger_summary["manual_publish_only"]:
        flag_violations.append("manual_export_ledger:not_manual_publish_only")
    if demo_status not in ("pass", "blocked"):
        flag_violations.append("pipeline_demo:unknown_status:%s" % demo_status)

    if flag_violations:
        blocked_reasons.extend("safety:%s" % v for v in flag_violations)

    safety_audit = {
        "violations": flag_violations,
        "unsafe_flag_count": len(flag_violations),
    }

    packet_status = "pass" if not blocked_reasons else "blocked"

    return {
        "dashboard_packet_id": "dashboard_%s" % (plan.get("source_library_id") or "unknown"),
        "created_at": STATIC_TIMESTAMP,
        "source_refs": [
            os.path.basename(os.path.abspath(lib_path)),
            os.path.basename(os.path.abspath(demo_path or demo.DEFAULT_DEMO_INPUT)),
        ],
        "repo_posture": {
            "mode": "pre_alpha_local_only",
            "phase": "pre_alpha_content_development",
        },
        "seed_library_summary": seed_library_summary,
        "editorial_calendar_summary": editorial_calendar_summary,
        "blocked_content_summary": blocked_content_summary,
        "pipeline_demo_summary": pipeline_demo_summary,
        "manual_export_ledger_summary": manual_export_ledger_summary,
        "operator_next_actions": operator_next_actions,
        "hard_boundary_flags": flags,
        "safety_audit": safety_audit,
        "blocked_reasons": blocked_reasons,
        "packet_status": packet_status,
        "library_valid": lib_result.get("valid"),
    }

def _operator_next_actions(safe_count, blocked_count, blocked_items, demo_status):
    """Deterministic suggested MANUAL operator actions (review-only)."""
    actions = []
    if safe_count > 0:
        actions.append(
            "Manually review %d safe seed(s) in the editorial calendar before any draft work." % safe_count
        )
    if blocked_count > 0:
        zones = sorted({b.get("content_zone") for b in blocked_items if b.get("content_zone")})
        actions.append(
            "Resolve or retire %d blocked seed(s) (zones: %s); guardrail reasons are recorded." % (
                blocked_count, ", ".join(zones) or "n/a"
            )
        )
    if demo_status == "pass":
        actions.append(
            "Pipeline demo passes end to end; no live action is permitted, manual review remains required."
        )
    else:
        actions.append(
            "Pipeline demo is blocked; inspect safety_violations before proceeding."
        )
    actions.append("All publishing remains manual and human-reviewed; no automation is enabled.")
    return actions


def summary(library_path=None, demo_path=None):
    """Deterministic local capability summary for the CLI. Fixture read only."""
    out = {
        "status": "pre-alpha operator dashboard packet active",
        "local_only": True,
        "fixture_only": True,
        "design_only": True,
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read": False,
        "fake_alpha_output": False,
        "public_postable_output": False,
        "platform_api_call_allowed_now": False,
        "live_execution_allowed_now": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
        "manual_review_required": True,
        "auto_approval": False,
    }
    try:
        packet = build_dashboard_packet(library_path, demo_path)
        out["packet_status"] = packet.get("packet_status")
        out["total_seeds"] = packet["seed_library_summary"]["total_seeds"]
        out["safe_seed_count"] = packet["seed_library_summary"]["safe_seed_count"]
        out["blocked_seed_count"] = packet["seed_library_summary"]["blocked_seed_count"]
        out["pipeline_demo_status"] = packet["pipeline_demo_summary"]["demo_status"]
        out["unsafe_flag_count"] = packet["safety_audit"]["unsafe_flag_count"]
    except Exception:
        out["packet_status"] = "unavailable"
    return out
