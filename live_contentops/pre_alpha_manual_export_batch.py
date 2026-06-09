"""Local-only pre-alpha manual export batch packet generator (Task 0107).

Deterministic, repo-local. Consumes a 0106 manual decision batch packet and
prepares manual-export packets + content-ledger entries for CLEAN 0098 approval
packets only, while preserving revision / rejection / blocked decisions in a
non-export report.

This is MANUAL copy/paste preparation ONLY. It NEVER publishes, schedules,
posts, calls a platform / provider / LLM / network, ingests metrics, reads
environment secret files, or creates any `manually_published` ledger state.
manual_publish_url / manual_publish_timestamp / manual_metrics always stay null
by default; recording an actual manual publish URL is a separate future task.

The packet fails closed (packet_status="blocked") if any hard-boundary flag is
unsafe, any export packet implies publish/platform readiness, any ledger entry
is manually_published, or any manual URL/metrics is non-null.
"""

import json
import os

from live_contentops.pre_alpha_content_engine import STATIC_TIMESTAMP
from live_contentops.pre_alpha_manual_export import (
    build_export_packet,
    build_ledger_entry,
)

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
BATCH_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_manual_export_batch_packet.schema.json"
)

FIXTURE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "pre_alpha_manual_export_batch"
)
DEFAULT_CONFIG = os.path.join(FIXTURE_DIR, "valid_manual_export_batch_config.json")

# Hard-boundary flags pinned on every batch packet, independent of input.
_REQUIRED_FLAGS = {
    "local_only": True,
    "fixture_only": True,
    "manual_review_required": True,
    "final_operator_check_required": True,
    "auto_publish": False,
    "public_postable": False,
    "platform_api_call_allowed_now": False,
    "scheduler_allowed": False,
    "metrics_ingestion_allowed": False,
    "provider_call_allowed_now": False,
    "network_call_allowed_now": False,
    "live_execution_allowed_now": False,
    "credential_or_env_read_allowed": False,
    "manually_published_created": False,
    "manual_publish_url_default_null": True,
    "manual_metrics_default_null": True,
}

_OPERATOR_FINAL_CHECKLIST = [
    "Confirm every export packet's text is accurate before any manual copy.",
    "Confirm limitations / source attribution remain visible.",
    "Manually copy approved text; this system never posts for you.",
    "Recording an actual published URL is a separate future operator task.",
    "Do not treat any export as publish-ready or platform-ready.",
]


def load_batch_schema():
    with open(os.path.abspath(BATCH_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(config_path=None):
    """Load the 0107 export batch config. Local file read only."""
    target = config_path or DEFAULT_CONFIG
    with open(os.path.abspath(target), "r", encoding="utf-8") as f:
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


def _export_packet_unsafe(export_packet):
    """Return violation strings if an export packet implies publish readiness."""
    violations = []
    pinned = {
        "manual_publish_only": True,
        "final_operator_check_required": True,
        "public_postable": False,
        "publish_allowed_now": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "platform_api_call_allowed": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
    }
    for flag, expected in pinned.items():
        if export_packet.get(flag) is not expected:
            violations.append("export_%s=%r" % (flag, export_packet.get(flag)))
    return violations


def _ledger_entry_unsafe(ledger_entry):
    """Return violation strings if a ledger entry advances past export_prepared."""
    violations = []
    lifecycle = ledger_entry.get("lifecycle_status")
    if lifecycle not in ("export_prepared", "blocked"):
        violations.append("ledger_lifecycle_status=%r" % lifecycle)
    if ledger_entry.get("manual_publish_url") is not None:
        violations.append("ledger_manual_publish_url_not_null")
    if ledger_entry.get("manual_publish_timestamp") is not None:
        violations.append("ledger_manual_publish_timestamp_not_null")
    if ledger_entry.get("manual_metrics") is not None:
        violations.append("ledger_manual_metrics_not_null")
    pinned = {
        "public_postable": False,
        "publish_allowed_now": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "scheduler_allowed": False,
    }
    for flag, expected in pinned.items():
        if ledger_entry.get(flag) is not expected:
            violations.append("ledger_%s=%r" % (flag, ledger_entry.get(flag)))
    return violations


def build_manual_export_batch_packet(decision_batch_packet,
                                     manual_export_batch_packet_id=None,
                                     source_refs=None):
    """Build a deterministic manual export batch packet from a 0106 packet.

    Only clean approval packets (approval_status=approved_manual_publish_prep,
    manual_publish_prep_ready=true, no blocked_reasons) become export packets
    and export_prepared content-ledger entries. Revision / rejection / blocked
    decisions are preserved in non_exported_decision_report, never exported.

    Nothing is published, scheduled, posted, or sent. No manually_published
    ledger state is created. Safety flags are pinned and the packet fails closed
    on any unsafe condition.
    """
    blocked_reasons = []

    if not isinstance(decision_batch_packet, dict):
        decision_batch_packet = {}

    decision_records = decision_batch_packet.get("decision_records") or []
    approval_packets = decision_batch_packet.get("approval_packets") or []

    # Index clean approval packets by draft_id for mapping to decision records.
    clean_approvals_by_draft = {}
    for ap in approval_packets:
        if not isinstance(ap, dict):
            continue
        if (
            ap.get("approval_status") == "approved_manual_publish_prep"
            and ap.get("manual_publish_prep_ready") is True
            and not ap.get("blocked_reasons")
        ):
            draft = ap.get("draft_id")
            if draft is not None:
                clean_approvals_by_draft[draft] = ap

    manual_export_packets = []
    content_ledger_entries = []
    non_exported = []
    approved_count = 0
    revision_requested_count = 0
    rejected_count = 0
    blocked_decision_count = 0

    for record in decision_records:
        if not isinstance(record, dict):
            continue
        status = record.get("decision_status")
        rqid = record.get("review_queue_item_id")
        draft = record.get("draft_id")

        if status == "approved_manual_publish_prep":
            approved_count += 1
            approval = clean_approvals_by_draft.get(draft)
            if not isinstance(approval, dict):
                non_exported.append({
                    "review_queue_item_id": rqid,
                    "draft_id": draft,
                    "platform_family": record.get("platform_family"),
                    "content_type": record.get("content_type"),
                    "decision_status": status,
                    "reason": "approved_decision_missing_clean_approval_packet",
                })
                blocked_reasons.append("missing_clean_approval:%s" % rqid)
                continue

            export_packet = build_export_packet(approval)
            ledger_entry = build_ledger_entry(export_packet)

            ep_violations = _export_packet_unsafe(export_packet)
            le_violations = _ledger_entry_unsafe(ledger_entry)
            if export_packet.get("blocked_reasons"):
                blocked_reasons.append("export_packet_blocked:%s" % rqid)
            if ep_violations:
                blocked_reasons.extend("safety:%s" % v for v in ep_violations)
            if le_violations:
                blocked_reasons.extend("safety:%s" % v for v in le_violations)

            manual_export_packets.append(export_packet)
            content_ledger_entries.append(ledger_entry)
        elif status == "revision_requested":
            revision_requested_count += 1
            non_exported.append({
                "review_queue_item_id": rqid,
                "draft_id": draft,
                "platform_family": record.get("platform_family"),
                "content_type": record.get("content_type"),
                "decision_status": status,
                "reason": "revision_requested_not_exported",
            })
        elif status == "rejected":
            rejected_count += 1
            non_exported.append({
                "review_queue_item_id": rqid,
                "draft_id": draft,
                "platform_family": record.get("platform_family"),
                "content_type": record.get("content_type"),
                "decision_status": status,
                "reason": str(record.get("decision_reason") or "rejected_not_exported"),
            })
        else:
            blocked_decision_count += 1
            non_exported.append({
                "review_queue_item_id": rqid,
                "draft_id": draft,
                "platform_family": record.get("platform_family"),
                "content_type": record.get("content_type"),
                "decision_status": status or "blocked",
                "reason": "blocked_decision_not_exported",
            })

    if decision_batch_packet.get("packet_status") == "blocked":
        blocked_reasons.append("source_decision_batch_packet_blocked")

    flags = _hard_boundary_flags()
    flag_violations = _audit_flags(flags)
    if flag_violations:
        blocked_reasons.extend("safety:%s" % v for v in flag_violations)

    for le in content_ledger_entries:
        if le.get("lifecycle_status") == "manually_published":
            blocked_reasons.append("manually_published_ledger_created")

    safety_audit = {
        "violations": flag_violations,
        "unsafe_flag_count": len(flag_violations),
    }

    packet_status = "pass" if not blocked_reasons else "blocked"

    src_id = decision_batch_packet.get("manual_decision_batch_packet_id")

    return {
        "manual_export_batch_packet_id": manual_export_batch_packet_id
        or "export_%s" % (src_id or "unknown"),
        "created_at": STATIC_TIMESTAMP,
        "source_refs": list(source_refs or []),
        "source_manual_decision_batch_packet_id": src_id,
        "approved_decision_count": approved_count,
        "revision_requested_count": revision_requested_count,
        "rejected_count": rejected_count,
        "blocked_decision_count": blocked_decision_count,
        "manual_export_packets": manual_export_packets,
        "content_ledger_entries": content_ledger_entries,
        "non_exported_decision_report": non_exported,
        "operator_final_checklist": list(_OPERATOR_FINAL_CHECKLIST),
        "hard_boundary_flags": flags,
        "safety_audit": safety_audit,
        "blocked_reasons": blocked_reasons,
        "packet_status": packet_status,
    }


def build_from_config(config):
    """Build the export batch packet from an in-memory 0107 config bundle.

    Expected keys:
        * decision_batch_packet: a 0106 manual decision batch packet
    """
    if not isinstance(config, dict):
        config = {}
    decision_batch_packet = config.get("decision_batch_packet") or {}
    return build_manual_export_batch_packet(
        decision_batch_packet,
        source_refs=list(config.get("source_refs") or []),
    )


def build_from_config_file(config_path=None):
    """Build the export batch packet from a local config fixture.

    If the config only references the 0106 decision batch (no inline packet),
    build the 0106 packet from its own default fixture first. Local reads only.
    """
    config = load_config(config_path)
    if not config.get("decision_batch_packet"):
        from live_contentops import pre_alpha_manual_decision_batch
        config["decision_batch_packet"] = (
            pre_alpha_manual_decision_batch.build_from_config_file()
        )
    if not config.get("source_refs"):
        config["source_refs"] = [
            os.path.basename(os.path.abspath(config_path or DEFAULT_CONFIG)),
        ]
    return build_from_config(config)


def summary(config_path=None):
    """Deterministic local capability summary for the CLI. Fixture read only."""
    out = {
        "status": "pre-alpha manual export batch packet active",
        "local_only": True,
        "fixture_only": True,
        "design_only": True,
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read": False,
        "fake_alpha_output": False,
        "public_postable_output": False,
        "auto_publish": False,
        "platform_api_call_allowed_now": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
        "live_execution_allowed_now": False,
        "manually_published_created": False,
        "manual_publish_url_default_null": True,
        "manual_metrics_default_null": True,
        "manual_review_required": True,
        "final_operator_check_required": True,
    }
    try:
        packet = build_from_config_file(config_path)
        ledger = packet.get("content_ledger_entries") or []
        manually_published = sum(
            1 for le in ledger if le.get("lifecycle_status") == "manually_published"
        )
        out["packet_status"] = packet.get("packet_status")
        out["source_decision_record_count"] = len(
            (packet.get("non_exported_decision_report") or [])
        ) + len(packet.get("manual_export_packets") or [])
        out["approved_decision_count"] = packet.get("approved_decision_count")
        out["revision_requested_count"] = packet.get("revision_requested_count")
        out["rejected_count"] = packet.get("rejected_count")
        out["blocked_decision_count"] = packet.get("blocked_decision_count")
        out["manual_export_packet_count"] = len(packet.get("manual_export_packets") or [])
        out["content_ledger_entry_count"] = len(ledger)
        out["manually_published_count"] = manually_published
        out["unsafe_flag_count"] = packet["safety_audit"]["unsafe_flag_count"]
    except Exception:
        out["packet_status"] = "unavailable"
    return out


