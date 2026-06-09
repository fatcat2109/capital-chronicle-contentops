"""Local-only pre-alpha manual decision batch packet generator (Task 0106).

Deterministic, repo-local. Consumes a 0105 editorial batch review packet and
prepares a MANUAL operator decision record for every review queue item, then
runs each supplied human-placeholder decision through the 0098 validation /
approval-packet builder.

This is a MANUAL DECISION WORKBENCH only. It NEVER auto-approves, NEVER applies a
default approve-all, NEVER exports, NEVER creates content-ledger objects, NEVER
publishes / schedules / posts, NEVER calls any provider / network / platform /
LLM, and NEVER reads environment secret files. It NEVER produces public-postable
or publish-ready output and NEVER emits fake Capital Chronicle alpha output.

Approval here means ready for future MANUAL publish prep only, under 0098
semantics. Records with unresolved guardrail findings cannot become approved.
Blocked / invalid decisions are always surfaced, never dropped.

The packet fails closed (packet_status="blocked") if any hard-boundary flag is
unsafe or any decision implies publish / export / platform readiness.
"""

import json
import os

from live_contentops.pre_alpha_content_engine import STATIC_TIMESTAMP
from live_contentops.pre_alpha_manual_review import (
    build_approval_packet,
    validate_decision,
)

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
BATCH_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_manual_decision_batch_packet.schema.json"
)

FIXTURE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "pre_alpha_manual_decision_batch"
)
DEFAULT_CONFIG = os.path.join(FIXTURE_DIR, "valid_manual_decision_batch_config.json")

# Hard-boundary flags pinned on every batch packet, independent of input.
_REQUIRED_FLAGS = {
    "local_only": True,
    "fixture_only": True,
    "manual_review_required": True,
    "reviewer_required": True,
    "auto_approval": False,
    "public_postable": False,
    "manual_export_packet_created": False,
    "content_ledger_created": False,
    "content_ledger_publish_status_changed": False,
    "provider_call_allowed_now": False,
    "network_call_allowed_now": False,
    "platform_api_call_allowed_now": False,
    "scheduler_allowed": False,
    "metrics_ingestion_allowed": False,
    "live_execution_allowed_now": False,
    "credential_or_env_read_allowed": False,
}

# A decision record that did NOT resolve into a clean approval / revision /
# rejection (e.g. invalid decision, approval over unresolved findings) is a
# blocked record.
_BLOCKED_STATUSES = {"blocked"}


def load_batch_schema():
    with open(os.path.abspath(BATCH_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def _hard_boundary_flags():
    return dict(_REQUIRED_FLAGS)


def _audit_flags(flags):
    violations = []
    for flag, expected in _REQUIRED_FLAGS.items():
        if flag not in flags:
            violations.append("missing_flag:%s" % flag)
        elif flags[flag] is not expected:
            violations.append("%s=%r" % (flag, flags[flag]))
    return violations


def load_config(config_path=None):
    """Load the 0106 decision batch config (review items + manual decisions)."""
    target = config_path or DEFAULT_CONFIG
    with open(os.path.abspath(target), "r", encoding="utf-8") as f:
        return json.load(f)



def _decision_record(review_item, decision):
    """Build one deterministic decision record for a review queue item.

    Runs the supplied MANUAL decision through 0098 validation against the review
    item. There is NO default decision: a missing decision is recorded as a
    blocked record (never an implicit approve).
    """
    rqid = review_item.get("review_queue_item_id") if isinstance(review_item, dict) else None

    if not isinstance(decision, dict):
        # No human decision supplied for this item: record as blocked, never
        # auto-approve and never drop the item.
        return {
            "review_queue_item_id": rqid,
            "draft_id": review_item.get("draft_id") if isinstance(review_item, dict) else None,
            "platform_family": review_item.get("platform_family") if isinstance(review_item, dict) else None,
            "content_type": review_item.get("content_type") if isinstance(review_item, dict) else None,
            "proposed_decision": "none",
            "reviewer_id_placeholder": None,
            "decision_reason": "no_manual_decision_supplied",
            "unresolved_guardrail_findings": [],
            "required_revision_notes": [],
            "manual_publish_only": True,
            "auto_approval": False,
            "reviewer_required": True,
            "publish_allowed_now": False,
            "platform_publish_allowed_now": False,
            "live_execution_allowed_now": False,
            "decision_status": "blocked",
            "blocked_reasons": ["no_manual_decision_supplied"],
        }

    blocked_reasons = []
    proposed = decision.get("decision")
    v = validate_decision(decision, review_item)
    if not v["valid"]:
        blocked_reasons.extend(v["errors"])

    # Resolve the decision status. A clean approval is the only path to an
    # approved status; everything else is revision / rejected / blocked.
    if blocked_reasons:
        decision_status = "blocked"
    elif proposed == "approve_manual_publish_prep":
        decision_status = "approved_manual_publish_prep"
    elif proposed == "request_revision":
        decision_status = "revision_requested"
    elif proposed == "reject":
        decision_status = "rejected"
    else:
        decision_status = "blocked"
        blocked_reasons.append("decision_value_not_allowed")

    return {
        "review_queue_item_id": rqid,
        "draft_id": review_item.get("draft_id"),
        "platform_family": review_item.get("platform_family"),
        "content_type": review_item.get("content_type"),
        "proposed_decision": proposed or "none",
        "reviewer_id_placeholder": decision.get("reviewer_id_placeholder"),
        "decision_reason": str(decision.get("decision_reason") or ""),
        "unresolved_guardrail_findings": list(decision.get("unresolved_guardrail_findings") or []),
        "required_revision_notes": list(decision.get("required_revision_notes") or []),
        "manual_publish_only": True,
        "auto_approval": False,
        "reviewer_required": True,
        "publish_allowed_now": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "decision_status": decision_status,
        "blocked_reasons": blocked_reasons,
    }


def build_manual_decision_batch_packet(batch_review_packet, decisions_by_item=None,
                                       manual_decision_batch_packet_id=None,
                                       source_refs=None):
    """Build a deterministic manual decision batch packet.

    For every review queue item in the 0105 batch review packet, build exactly
    one decision record using the supplied MANUAL decision (keyed by
    review_queue_item_id). Clean approvals also produce a 0098 approval packet.
    Blocked / invalid decisions are surfaced in blocked_decision_records.

    Nothing is auto-approved, exported, published, scheduled, or sent. No
    content-ledger object is created. Safety flags are always pinned and the
    packet fails closed on any unsafe condition.
    """
    decisions_by_item = decisions_by_item or {}
    blocked_reasons = []

    if not isinstance(batch_review_packet, dict):
        batch_review_packet = {}

    review_items = batch_review_packet.get("review_queue_items") or []
    rendered_packet_id = None
    rendered = batch_review_packet.get("rendered_packets") or []
    if rendered and isinstance(rendered[0], dict):
        rendered_packet_id = rendered[0].get("rendered_packet_id")

    decision_records = []
    approval_packets = []
    blocked_decision_records = []
    approved_count = 0
    revision_requested_count = 0
    rejected_count = 0

    for item in review_items:
        rqid = item.get("review_queue_item_id") if isinstance(item, dict) else None
        decision = decisions_by_item.get(rqid)
        record = _decision_record(item, decision)
        decision_records.append(record)

        status = record["decision_status"]
        if status == "approved_manual_publish_prep":
            approved_count += 1
            # A clean approval also produces a 0098 approval packet so the
            # operator can carry it into future MANUAL publish prep. This is
            # NOT export and NOT publish: the approval packet stays non-public.
            ap = build_approval_packet(rendered_packet_id, item, decision)
            approval_packets.append(ap)
            if ap.get("blocked_reasons"):
                # Defense in depth: if the 0098 builder itself blocked, the
                # record must not be counted as a clean approval.
                blocked_reasons.append(
                    "approval_packet_blocked:%s" % rqid
                )
        elif status == "revision_requested":
            revision_requested_count += 1
        elif status == "rejected":
            rejected_count += 1
        else:
            blocked_decision_records.append(record)
            blocked_reasons.append("decision_blocked:%s" % rqid)

    # If the source batch review packet was itself blocked, that must surface.
    if batch_review_packet.get("packet_status") == "blocked":
        blocked_reasons.append("source_batch_review_packet_blocked")

    flags = _hard_boundary_flags()
    flag_violations = _audit_flags(flags)
    if flag_violations:
        blocked_reasons.extend("safety:%s" % v for v in flag_violations)

    safety_audit = {
        "violations": flag_violations,
        "unsafe_flag_count": len(flag_violations),
    }

    packet_status = "pass" if not blocked_reasons else "blocked"

    src_id = batch_review_packet.get("batch_review_packet_id")

    return {
        "manual_decision_batch_packet_id": manual_decision_batch_packet_id
        or "decision_%s" % (src_id or "unknown"),
        "created_at": STATIC_TIMESTAMP,
        "source_refs": list(source_refs or []),
        "source_batch_review_packet_id": src_id,
        "review_queue_item_count": len(review_items),
        "decision_records": decision_records,
        "approval_packets": approval_packets,
        "blocked_decision_records": blocked_decision_records,
        "operator_decision_summary": {
            "approved_count": approved_count,
            "revision_requested_count": revision_requested_count,
            "rejected_count": rejected_count,
            "blocked_count": len(blocked_decision_records),
        },
        "hard_boundary_flags": flags,
        "safety_audit": safety_audit,
        "blocked_reasons": blocked_reasons,
        "packet_status": packet_status,
    }


def build_from_config(config):
    """Build the batch packet from an in-memory 0106 config bundle.

    Expected keys:
        * batch_review_packet: a 0105 editorial batch review packet
        * decisions: list of manual decision objects (each carries its own
          review_queue_item_id used to key it to a review item)
    """
    if not isinstance(config, dict):
        config = {}
    batch_review_packet = config.get("batch_review_packet") or {}
    decisions = config.get("decisions") or []
    by_item = {}
    for d in decisions:
        if isinstance(d, dict) and d.get("review_queue_item_id"):
            by_item[d["review_queue_item_id"]] = d
    return build_manual_decision_batch_packet(
        batch_review_packet,
        decisions_by_item=by_item,
        source_refs=list(config.get("source_refs") or []),
    )


def build_from_config_file(config_path=None):
    """Build the batch packet from a local config fixture. Local file read only."""
    config = load_config(config_path)
    if not config.get("source_refs"):
        config["source_refs"] = [
            os.path.basename(os.path.abspath(config_path or DEFAULT_CONFIG)),
        ]
    return build_from_config(config)


def summary(config_path=None):
    """Deterministic local capability summary for the CLI. Fixture read only."""
    out = {
        "status": "pre-alpha manual decision batch packet active",
        "local_only": True,
        "fixture_only": True,
        "design_only": True,
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read": False,
        "fake_alpha_output": False,
        "public_postable_output": False,
        "auto_approval": False,
        "manual_export_packet_created": False,
        "content_ledger_created": False,
        "content_ledger_publish_status_changed": False,
        "platform_api_call_allowed_now": False,
        "live_execution_allowed_now": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
        "manual_review_required": True,
        "reviewer_required": True,
    }
    try:
        packet = build_from_config_file(config_path)
        s = packet["operator_decision_summary"]
        out["packet_status"] = packet.get("packet_status")
        out["review_queue_item_count"] = packet.get("review_queue_item_count")
        out["decision_record_count"] = len(packet.get("decision_records") or [])
        out["approval_packet_count"] = len(packet.get("approval_packets") or [])
        out["blocked_decision_count"] = s["blocked_count"]
        out["revision_requested_count"] = s["revision_requested_count"]
        out["rejected_count"] = s["rejected_count"]
        out["unsafe_flag_count"] = packet["safety_audit"]["unsafe_flag_count"]
    except Exception:
        out["packet_status"] = "unavailable"
    return out
