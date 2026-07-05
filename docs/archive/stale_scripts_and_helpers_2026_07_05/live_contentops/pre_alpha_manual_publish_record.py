"""Local-only pre-alpha manual publish RECORD packet generator (Task 0108).

Deterministic, repo-local. Consumes a 0107 manual export batch packet plus
operator-supplied manual records and advances eligible CLEAN export packets to
content-ledger lifecycle_status="manually_published" ONLY when an explicit,
valid manual record is supplied (non-empty manual_publish_url + timestamp).

This is MANUAL RECORDKEEPING ONLY, performed AFTER an operator has externally
copy/pasted and published content by hand. It NEVER posts, schedules, sends,
calls a platform / provider / LLM / network, scrapes, ingests metrics
automatically, reads environment secret files, auto-publishes, or INFERS that
publication happened. Metrics are operator-supplied (fixture) only and may be
null; they are never fetched.

The packet fails closed (packet_status="blocked") if any hard-boundary flag is
unsafe, any source export packet is unsafe, a record references an unknown /
blocked export, a record is missing required fields, a duplicate record targets
the same export, or any metric appears fetched/inferred rather than supplied.
"""

import json
import os

from live_contentops.pre_alpha_content_engine import STATIC_TIMESTAMP
from live_contentops.pre_alpha_manual_export import build_ledger_entry

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
RECORD_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_manual_publish_record_packet.schema.json"
)

FIXTURE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "fixtures", "pre_alpha_manual_publish_record"
)
DEFAULT_CONFIG = os.path.join(FIXTURE_DIR, "operator_safe_default_config.json")

# Hard-boundary flags pinned on every record packet, independent of input.
_REQUIRED_FLAGS = {
    "local_only": True,
    "fixture_only": True,
    "manual_recordkeeping_only": True,
    "platform_api_call_allowed_now": False,
    "provider_call_allowed_now": False,
    "network_call_allowed_now": False,
    "scheduler_allowed": False,
    "automatic_metrics_ingestion_allowed": False,
    "scraping_allowed": False,
    "credential_or_env_read_allowed": False,
    "live_execution_allowed_now": False,
    "auto_publish": False,
    "manual_operator_record_required": True,
}

# Fields a manual record must NOT carry: anything implying platform posting or
# automatic metric retrieval. Their presence fails the record closed.
_FORBIDDEN_RECORD_KEYS = (
    "platform_api_payload",
    "platform_api_call",
    "scheduled_post",
    "schedule_at",
    "auto_post",
    "fetched_metrics",
    "scraped_metrics",
    "metrics_fetch",
    "provider_call",
    "network_call",
)

_OPERATOR_AUDIT_CHECKLIST = [
    "Only record a publish AFTER you manually posted the content yourself.",
    "manual_publish_url must be the real URL you copied from the platform.",
    "manual_publish_timestamp must be the time you actually published.",
    "manual_metrics, if present, must be hand-entered; this system never fetches them.",
    "Missing records correctly stay export_prepared / not_recorded.",
    "This system never posts, schedules, scrapes, or calls a platform API.",
]


def load_record_schema():
    with open(os.path.abspath(RECORD_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(config_path=None):
    """Load the 0108 record config. Local file read only."""
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


def _eligible_export_packets(export_batch_packet):
    """Return clean, non-blocked manual export packets keyed by export id.

    An export packet is eligible only when it is prepared-for-review with no
    blocked_reasons and manual_copy_ready intact.
    """
    eligible = {}
    for ep in export_batch_packet.get("manual_export_packets") or []:
        if not isinstance(ep, dict):
            continue
        if ep.get("export_status") != "prepared_for_operator_review":
            continue
        if ep.get("blocked_reasons"):
            continue
        if ep.get("manual_copy_ready") is not True:
            continue
        ep_id = ep.get("manual_export_packet_id")
        if ep_id:
            eligible[ep_id] = ep
    return eligible


def _validate_manual_record(record, eligible, seen_ids):
    """Validate one operator-supplied manual record.

    Returns (status, reason): "recorded" if valid and may advance the ledger to
    manually_published; "blocked" if invalid / duplicate / targets an
    unknown-or-blocked export.
    """
    if not isinstance(record, dict):
        return "blocked", "record_not_object"

    ep_id = record.get("manual_export_packet_id")
    if not ep_id:
        return "blocked", "missing_manual_export_packet_id"
    if ep_id not in eligible:
        return "blocked", "references_unknown_or_blocked_export_packet"
    if ep_id in seen_ids:
        return "blocked", "duplicate_record_for_export_packet"

    url = record.get("manual_publish_url")
    if not (isinstance(url, str) and url.strip() != ""):
        return "blocked", "missing_manual_publish_url"
    ts = record.get("manual_publish_timestamp")
    if not (isinstance(ts, str) and ts.strip() != ""):
        return "blocked", "missing_manual_publish_timestamp"

    metrics = record.get("manual_metrics")
    if metrics is not None and not isinstance(metrics, dict):
        return "blocked", "manual_metrics_must_be_object_or_null"

    for key in _FORBIDDEN_RECORD_KEYS:
        if key in record:
            return "blocked", "forbidden_record_field:%s" % key

    return "recorded", "ok"


def build_manual_publish_record_packet(export_batch_packet,
                                       manual_records=None,
                                       manual_publish_record_packet_id=None,
                                       source_refs=None):
    """Build a deterministic manual publish record packet from a 0107 packet.

    Only explicit, valid operator-supplied manual records advance an eligible
    clean export packet's content-ledger entry to manually_published. Eligible
    exports with no record stay export_prepared in not_recorded_export_report.
    Invalid/duplicate/unknown-targeting records go to blocked_record_report.
    Nothing is posted, scheduled, scraped, or fetched.
    """
    blocked_reasons = []

    if not isinstance(export_batch_packet, dict):
        export_batch_packet = {}
    records = list(manual_records or [])

    eligible = _eligible_export_packets(export_batch_packet)

    manual_records_out = []
    updated_ledger_entries = []
    blocked_record_report = []
    recorded_ids = set()

    for record in records:
        status, reason = _validate_manual_record(record, eligible, recorded_ids)
        ep_id = (
            record.get("manual_export_packet_id")
            if isinstance(record, dict) else None
        )
        if status == "recorded":
            recorded_ids.add(ep_id)
            export_packet = eligible[ep_id]
            manual_record = {
                "manual_publish_url": record.get("manual_publish_url"),
                "manual_publish_timestamp": record.get("manual_publish_timestamp"),
                "manual_metrics": record.get("manual_metrics"),
            }
            ledger_entry = build_ledger_entry(export_packet, manual_record)
            updated_ledger_entries.append(ledger_entry)
            manual_records_out.append({
                "manual_export_packet_id": ep_id,
                "approval_packet_id": export_packet.get("approval_packet_id"),
                "draft_id": export_packet.get("draft_id"),
                "platform_family": export_packet.get("platform_family"),
                "content_type": export_packet.get("content_type"),
                "manual_publish_url": record.get("manual_publish_url"),
                "manual_publish_timestamp": record.get("manual_publish_timestamp"),
                "manual_metrics": record.get("manual_metrics"),
                "record_status": "recorded",
            })
            # Defense in depth: a recorded ledger must reach manually_published.
            if ledger_entry.get("lifecycle_status") != "manually_published":
                blocked_reasons.append(
                    "recorded_ledger_not_manually_published:%s" % ep_id
                )
        else:
            blocked_record_report.append({
                "manual_export_packet_id": ep_id,
                "record_status": "blocked",
                "reason": reason,
            })
            blocked_reasons.append(
                "blocked_record:%s:%s" % (ep_id or "unknown", reason)
            )

    # Eligible exports with no recorded publish stay export_prepared.
    not_recorded_report = []
    for ep_id, ep in eligible.items():
        if ep_id not in recorded_ids:
            ledger_entry = build_ledger_entry(ep)  # no record -> export_prepared
            updated_ledger_entries.append(ledger_entry)
            not_recorded_report.append({
                "manual_export_packet_id": ep_id,
                "approval_packet_id": ep.get("approval_packet_id"),
                "draft_id": ep.get("draft_id"),
                "platform_family": ep.get("platform_family"),
                "content_type": ep.get("content_type"),
                "lifecycle_status": ledger_entry.get("lifecycle_status"),
                "reason": "no_manual_record_supplied",
            })

    if export_batch_packet.get("packet_status") == "blocked":
        blocked_reasons.append("source_manual_export_batch_packet_blocked")

    flags = _hard_boundary_flags()
    flag_violations = _audit_flags(flags)
    if flag_violations:
        blocked_reasons.extend("safety:%s" % v for v in flag_violations)

    safety_audit = {
        "violations": flag_violations,
        "unsafe_flag_count": len(flag_violations),
        "automatic_metrics_ingestion_count": 0,
    }

    packet_status = "pass" if not blocked_reasons else "blocked"

    src_id = export_batch_packet.get("manual_export_batch_packet_id")

    return {
        "manual_publish_record_packet_id": manual_publish_record_packet_id
        or "publish_record_%s" % (src_id or "unknown"),
        "created_at": STATIC_TIMESTAMP,
        "source_refs": list(source_refs or []),
        "source_manual_export_batch_packet_id": src_id,
        "eligible_export_packet_count": len(eligible),
        "manual_record_count": len(records),
        "recorded_publish_count": len(manual_records_out),
        "not_recorded_count": len(not_recorded_report),
        "blocked_record_count": len(blocked_record_report),
        "manual_records": manual_records_out,
        "updated_content_ledger_entries": updated_ledger_entries,
        "not_recorded_export_report": not_recorded_report,
        "blocked_record_report": blocked_record_report,
        "operator_audit_checklist": list(_OPERATOR_AUDIT_CHECKLIST),
        "hard_boundary_flags": flags,
        "safety_audit": safety_audit,
        "blocked_reasons": blocked_reasons,
        "packet_status": packet_status,
    }


def build_from_config(config):
    """Build the record packet from an in-memory 0108 config bundle.

    Expected keys:
        * export_batch_packet: a 0107 manual export batch packet
        * manual_records: list of operator-supplied manual records (optional)
    """
    if not isinstance(config, dict):
        config = {}
    export_batch_packet = config.get("export_batch_packet") or {}
    return build_manual_publish_record_packet(
        export_batch_packet,
        manual_records=list(config.get("manual_records") or []),
        source_refs=list(config.get("source_refs") or []),
    )


def build_from_config_file(config_path=None):
    """Build the record packet from a local config fixture.

    If the config only references the 0107 export batch (no inline packet),
    build the 0107 packet from its own default fixture first. Local reads only.
    """
    config = load_config(config_path)
    if not config.get("export_batch_packet"):
        from live_contentops import pre_alpha_manual_export_batch
        config["export_batch_packet"] = (
            pre_alpha_manual_export_batch.build_from_config_file()
        )
    if not config.get("source_refs"):
        config["source_refs"] = [
            os.path.basename(os.path.abspath(config_path or DEFAULT_CONFIG)),
        ]
    return build_from_config(config)


def summary(config_path=None):
    """Deterministic local capability summary for the CLI. Fixture read only."""
    out = {
        "status": "pre-alpha manual publish record packet active",
        "local_only": True,
        "fixture_only": True,
        "manual_recordkeeping_only": True,
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read": False,
        "scraping_allowed": False,
        "automatic_metrics_ingestion_allowed": False,
        "platform_api_call_allowed_now": False,
        "scheduler_allowed": False,
        "auto_publish": False,
        "live_execution_allowed_now": False,
        "manual_operator_record_required": True,
    }
    try:
        packet = build_from_config_file(config_path)
        out["packet_status"] = packet.get("packet_status")
        out["eligible_export_packet_count"] = packet.get("eligible_export_packet_count")
        out["manual_record_count"] = packet.get("manual_record_count")
        out["recorded_publish_count"] = packet.get("recorded_publish_count")
        out["not_recorded_count"] = packet.get("not_recorded_count")
        out["blocked_record_count"] = packet.get("blocked_record_count")
        out["updated_ledger_entry_count"] = len(
            packet.get("updated_content_ledger_entries") or []
        )
        out["automatic_metrics_ingestion_count"] = packet["safety_audit"][
            "automatic_metrics_ingestion_count"
        ]
        out["unsafe_flag_count"] = packet["safety_audit"]["unsafe_flag_count"]
    except Exception:
        out["packet_status"] = "unavailable"
    return out
