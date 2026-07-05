"""Local-only deterministic end-to-end pre-alpha pipeline demo (Task 0101).

Chains the accepted 0095-0099 pre-alpha pipeline from a safe fixture seed to a
content ledger entry, producing a single reviewable demo packet that records
every stage:

    seed
      -> editorial packet            (0095 pre_alpha_content_engine)
      -> rendered draft / review queue (0097 pre_alpha_draft_renderer)
      -> manual review decision / approval packet (0098 pre_alpha_manual_review)
      -> manual export packet         (0099 pre_alpha_manual_export)
      -> content ledger entry         (0099 pre_alpha_manual_export)

This module performs NO network/search/provider/LLM/platform/credential access.
It NEVER posts, NEVER fetches, NEVER reads `.env`, NEVER auto-approves, NEVER
produces public-postable or publish-ready output, and NEVER emits financial
advice / signal / execution language or fake Capital Chronicle alpha output.

The demo packet is reviewable evidence only. Every stage preserves the pinned
non-publishing / non-live / no-provider / no-network / no-scheduler / no-metrics
posture. If any stage blocks, the demo packet fails closed and surfaces the
blocked reasons.
"""

import json
import os

from live_contentops.pre_alpha_content_engine import (
    STATIC_TIMESTAMP,
    build_editorial_packet,
)
from live_contentops.pre_alpha_prompt_pack import (
    validate_prompt_pack,
    validate_style_profile,
    validate_editorial_rubric,
)
from live_contentops.pre_alpha_draft_renderer import render_review_packet
from live_contentops.pre_alpha_manual_review import build_approval_packet
from live_contentops.pre_alpha_manual_export import (
    build_export_packet,
    build_ledger_entry,
)

FIXTURE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "pre_alpha_pipeline_demo"
)
DEFAULT_DEMO_INPUT = os.path.join(
    FIXTURE_DIR, "valid_end_to_end_demo_input.json"
)

# Demo decisions are MANUAL human review placeholders. They never auto-approve.
_REVIEWER_PLACEHOLDER = "operator_review_placeholder"


def _build_demo_decision(review_item):
    """Construct a deterministic MANUAL approve decision for a review item.

    This represents a human operator approving a clean review-queue item for
    future MANUAL publish prep only. It is NOT auto-approval: the decision is an
    explicit, recorded human-review placeholder, and it is still re-validated
    against the review item (and re-scanned downstream) before any approval is
    granted. If the review item is itself blocked, approval fails closed.
    """
    return {
        "review_decision_id": "decision_%s" % review_item.get("review_queue_item_id"),
        "review_queue_item_id": review_item.get("review_queue_item_id"),
        "reviewer_id_placeholder": _REVIEWER_PLACEHOLDER,
        "decision": "approve_manual_publish_prep",
        "decision_reason": "Clean general/process content; approved for manual publish prep only.",
        "required_revision_notes": [],
        "unresolved_guardrail_findings": [],
        "approved_platform_family": review_item.get("platform_family"),
        "approval_scope": "manual_publish_prep_only",
        "reviewer_required": True,
        "auto_approval": False,
        "manual_publish_only": True,
        "publish_allowed_now": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "review_timestamp": STATIC_TIMESTAMP,
    }



# Safety flags that must remain pinned across every stage of the demo.
_REQUIRED_FALSE_FLAGS = [
    "public_postable",
    "publish_allowed_now",
    "platform_publish_allowed_now",
    "live_execution_allowed_now",
    "provider_call_made",
    "network_call_made",
    "platform_api_call_allowed",
    "scheduler_allowed",
    "metrics_ingestion_allowed",
]


def _collect_safety_flags(stage_name, obj):
    """Return the subset of pinned no-publish/no-live flags present on a stage."""
    found = {}
    if isinstance(obj, dict):
        for flag in _REQUIRED_FALSE_FLAGS:
            if flag in obj:
                found[flag] = obj[flag]
    return {"stage": stage_name, "flags": found}


def run_demo(seed):
    """Run the full local pipeline on a safe seed and return a demo packet.

    Records every stage output plus a deterministic safety audit. NEVER posts,
    fetches, or grants live capability. If any stage blocks, demo_status is
    "blocked" and blocked_reasons are surfaced; the demo still records the
    stages reached so it is reviewable evidence.
    """
    blocked_reasons = []
    stages = {}

    # Stage 1: editorial packet (0095). Validates the seed internally and fails
    # closed (guardrail_status="blocked") on unsafe input rather than raising.
    editorial_packet = build_editorial_packet(seed)
    stages["editorial_packet"] = editorial_packet
    if editorial_packet.get("guardrail_status") != "pass":
        for r in editorial_packet.get("blocked_reasons") or ["editorial_packet_blocked"]:
            blocked_reasons.append("editorial_packet:%s" % r)

    # Config (0096): deterministic local prompt pack / style / rubric carried on
    # the seed. They are validated; the renderer re-validates them too.
    prompt_pack = seed.get("prompt_pack") if isinstance(seed, dict) else None
    style_profile = seed.get("style_profile") if isinstance(seed, dict) else None
    editorial_rubric = seed.get("editorial_rubric") if isinstance(seed, dict) else None
    for label, validator, obj in (
        ("prompt_pack", validate_prompt_pack, prompt_pack),
        ("style_profile", validate_style_profile, style_profile),
        ("editorial_rubric", validate_editorial_rubric, editorial_rubric),
    ):
        v = validator(obj) if obj is not None else {"valid": False, "errors": ["missing"]}
        if not v.get("valid"):
            for e in v.get("errors") or ["invalid"]:
                blocked_reasons.append("%s:%s" % (label, e))

    # Stage 2: rendered draft / review queue (0097).
    rendered_packet = render_review_packet(
        editorial_packet, prompt_pack, style_profile, editorial_rubric
    )
    stages["rendered_packet"] = rendered_packet
    if rendered_packet.get("guardrail_status") != "pass":
        for r in rendered_packet.get("blocked_reasons") or ["rendered_packet_blocked"]:
            blocked_reasons.append("rendered_packet:%s" % r)

    review_items = list(rendered_packet.get("review_queue_items") or [])
    stages["review_queue_items"] = review_items

    # Fail closed but still return the reached stages.
    if blocked_reasons or not review_items:
        if not review_items and not blocked_reasons:
            blocked_reasons.append("no_review_queue_items")
        return _assemble_demo_packet(seed, stages, [], blocked_reasons)

    # Stages 3-5: drive each review item through review -> approval -> export ->
    # ledger. Proves the full path per draft candidate.
    item_traces = []
    for review_item in review_items:
        trace = _run_item(rendered_packet, review_item)
        item_traces.append(trace)
        blocked_reasons.extend(trace.get("blocked_reasons") or [])

    return _assemble_demo_packet(seed, stages, item_traces, blocked_reasons)


def _run_item(rendered_packet, review_item):
    """Drive one review-queue item through review, approval, export, ledger."""
    local_blocked = []

    decision = _build_demo_decision(review_item)
    approval_packet = build_approval_packet(
        rendered_packet.get("rendered_packet_id"), review_item, decision
    )
    if approval_packet.get("approval_status") != "approved_manual_publish_prep":
        for r in approval_packet.get("blocked_reasons") or ["approval_not_clean"]:
            local_blocked.append("approval:%s" % r)

    export_packet = build_export_packet(approval_packet)
    if export_packet.get("export_status") != "prepared_for_operator_review":
        for r in export_packet.get("blocked_reasons") or ["export_blocked"]:
            local_blocked.append("export:%s" % r)

    # No manual_record supplied: ledger MUST stay at export_prepared with null
    # url/timestamp/metrics. Evidence that nothing is ever auto-published.
    ledger_entry = build_ledger_entry(export_packet, manual_record=None)

    return {
        "review_queue_item_id": review_item.get("review_queue_item_id"),
        "draft_id": review_item.get("draft_id"),
        "platform_family": review_item.get("platform_family"),
        "decision": decision,
        "approval_packet": approval_packet,
        "export_packet": export_packet,
        "ledger_entry": ledger_entry,
        "blocked_reasons": local_blocked,
    }


def _assemble_demo_packet(seed, stages, item_traces, blocked_reasons):
    """Assemble the final reviewable demo packet with a deterministic safety audit."""
    editorial_packet = stages.get("editorial_packet") or {}
    rendered_packet = stages.get("rendered_packet") or {}
    review_items = stages.get("review_queue_items") or []

    # Which stages were actually reached (reviewable evidence of the flow).
    stages_reached = ["seed", "editorial_packet"]
    if rendered_packet:
        stages_reached.append("rendered_packet")
    if review_items:
        stages_reached.append("review_queue")
    if item_traces:
        if any(t.get("approval_packet") for t in item_traces):
            stages_reached.append("approval_packet")
        if any(t.get("export_packet") for t in item_traces):
            stages_reached.append("manual_export_packet")
        if any(t.get("ledger_entry") for t in item_traces):
            stages_reached.append("content_ledger_entry")

    # Deterministic safety audit: collect pinned flags present on each stage.
    safety_audit = [
        _collect_safety_flags("editorial_packet", editorial_packet),
        _collect_safety_flags("rendered_packet", rendered_packet),
    ]
    for trace in item_traces:
        safety_audit.append(
            _collect_safety_flags("approval_packet:%s" % trace.get("draft_id"),
                                  trace.get("approval_packet"))
        )
        safety_audit.append(
            _collect_safety_flags("export_packet:%s" % trace.get("draft_id"),
                                  trace.get("export_packet"))
        )

    # Any pinned flag that is present but not False is a hard safety violation.
    safety_violations = []
    for entry in safety_audit:
        for flag, value in entry["flags"].items():
            if value is not False:
                safety_violations.append("%s.%s=%r" % (entry["stage"], flag, value))

    # The ledger must never auto-advance to manually_published in the demo.
    for trace in item_traces:
        ledger = trace.get("ledger_entry") or {}
        if ledger.get("lifecycle_status") == "manually_published":
            safety_violations.append(
                "ledger:%s.lifecycle_status=manually_published" % trace.get("draft_id")
            )
        for nullf in ("manual_publish_url", "manual_publish_timestamp", "manual_metrics"):
            if ledger.get(nullf) is not None:
                safety_violations.append("ledger:%s.%s_not_null" % (trace.get("draft_id"), nullf))

    if safety_violations:
        blocked_reasons = list(blocked_reasons) + ["safety_violation:%s" % v for v in safety_violations]

    demo_status = "pass" if not blocked_reasons else "blocked"

    seed_id = seed.get("seed_id") if isinstance(seed, dict) else None

    return {
        "demo_packet_id": "demo_%s" % (seed_id or "unknown"),
        "created_at": STATIC_TIMESTAMP,
        "demo_status": demo_status,
        "local_only": True,
        "fixture_only": True,
        "seed": seed,
        "stages": {
            "editorial_packet": editorial_packet,
            "rendered_packet": rendered_packet,
            "review_queue_items": review_items,
            "item_traces": item_traces,
        },
        "stages_reached": stages_reached,
        "safety_audit": safety_audit,
        "safety_violations": safety_violations,
        "blocked_reasons": blocked_reasons,
        # Demo-level pinned posture (independent of any input).
        "public_postable": False,
        "publish_allowed_now": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "provider_call_made": False,
        "network_call_made": False,
        "platform_api_call_allowed": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
        "manual_review_required": True,
        "final_operator_check_required": True,
    }


def run_demo_from_file(path=None):
    """Run the demo from a local fixture seed file. Local file read only."""
    target = path or DEFAULT_DEMO_INPUT
    with open(os.path.abspath(target), "r", encoding="utf-8") as f:
        seed = json.load(f)
    return run_demo(seed)


def summary():
    """Deterministic local capability summary for the CLI. Fixture read only."""
    out = {
        "status": "pre-alpha end-to-end local demo packet active",
        "local_only": True,
        "fixture_only": True,
        "design_only": True,
        "stages": [
            "seed",
            "editorial_packet",
            "rendered_packet",
            "review_queue",
            "approval_packet",
            "manual_export_packet",
            "content_ledger_entry",
        ],
        "integrates_0095_to_0099": True,
        "public_postable": False,
        "publish_allowed_now": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "provider_call_made": False,
        "network_call_made": False,
        "platform_api_call_allowed": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
        "manual_review_required": True,
        "auto_approval": False,
        "fake_alpha_output": False,
        "credential_read": False,
    }
    # Reflect the actual default demo result so the summary is real evidence.
    try:
        demo = run_demo_from_file()
        out["default_demo_status"] = demo.get("demo_status")
        out["default_demo_stages_reached"] = demo.get("stages_reached")
        out["default_demo_safety_violations"] = demo.get("safety_violations")
    except Exception:
        out["default_demo_status"] = "unavailable"
    return out
