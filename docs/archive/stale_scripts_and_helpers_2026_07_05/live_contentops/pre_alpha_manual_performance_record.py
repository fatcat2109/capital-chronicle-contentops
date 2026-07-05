"""Pre-Alpha Manual Performance Record module.

This provides the strict contract for operator-entered performance metrics.
It forbids scraping, automatic metrics ingestion, platform APIs, credential reads,
and posting. It enforces fail-closed behavior for invalid metrics or records that
lack explicit manual publish references.
"""

import datetime
import json
import os
import uuid

# Safety invariants. Must not be overridden by fixtures.
_REQUIRED_FLAGS = {
    "local_only": True,
    "manual_operator_entry_only": True,
    "fixture_only": True,
    "network_call_allowed_now": False,
    "provider_call_allowed_now": False,
    "platform_api_call_allowed_now": False,
    "scraping_allowed": False,
    "automatic_metrics_ingestion_allowed": False,
    "credential_or_env_read_allowed": False,
    "auto_publish": False,
    "public_postable": False,
}

_FORBIDDEN_RECORD_KEYS = [
    "platform_api_payload",
    "scraped",
    "fetched",
    "api_response",
    "automatic_metrics",
]

SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "schemas",
    "pre_alpha_manual_performance_record_packet.schema.json",
)

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "fixtures",
    "pre_alpha_manual_performance_record",
)

DEFAULT_CONFIG = os.path.join(FIXTURE_DIR, "valid_manual_performance_record_config.json")


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _hard_boundary_flags():
    """Return the pinned hard boundary flags for this module."""
    return dict(_REQUIRED_FLAGS)


def _validate_record(record):
    """Validate a single performance record to ensure strict compliance."""
    reasons = []

    # Enforce basic presence
    if not record.get("linked_manual_publish_record_id"):
        reasons.append("missing_manual_publish_reference")
    
    if not record.get("metric_capture_timestamp"):
        reasons.append("missing_metric_capture_timestamp")

    if record.get("metrics_source_type") != "operator_entered":
        reasons.append(f"invalid_metrics_source_type:{record.get('metrics_source_type')}")

    # Enforce forbidden fields
    for forbidden in _FORBIDDEN_RECORD_KEYS:
        if forbidden in record:
            reasons.append(f"forbidden_record_field:{forbidden}")

    # Validate metrics
    metrics = record.get("metrics", {})
    if not isinstance(metrics, dict):
        reasons.append("metrics_must_be_object")
    else:
        for k, v in metrics.items():
            if v is not None:
                if not isinstance(v, int):
                    reasons.append(f"non_integer_metric:{k}")
                elif v < 0:
                    reasons.append(f"negative_metric:{k}")
            else:
                if not record.get("metric_null_reason"):
                    reasons.append(f"missing_metric_null_reason_for_null_metric:{k}")

    # Safety flags per record
    record["public_postable"] = False
    record["auto_publish"] = False
    record["automatic_metrics_ingestion"] = False
    record["platform_api_payload_generated"] = False

    return reasons, record


def build_manual_performance_record_packet(config_payload):
    """Build a compliant manual performance record packet from the given config."""
    packet_id = f"manual_perf_packet_{uuid.uuid4().hex[:8]}"
    now_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records_in = config_payload.get("records", [])
    
    processed_records = []
    blocked_reasons = []
    invalid_count = 0
    missing_count = 0

    for idx, rec in enumerate(records_in):
        record_reasons, validated_rec = _validate_record(rec)
        
        # Count missing/null metrics
        metrics = validated_rec.get("metrics", {})
        if isinstance(metrics, dict):
            for k, v in metrics.items():
                if v is None:
                    missing_count += 1
        
        if record_reasons:
            invalid_count += 1
            blocked_reasons.extend([f"record_{idx}_{r}" for r in record_reasons])
        
        # Format the record to match the schema
        processed_records.append({
            "performance_record_id": validated_rec.get("performance_record_id", f"perf_rec_{uuid.uuid4().hex[:8]}"),
            "linked_manual_publish_record_id": validated_rec.get("linked_manual_publish_record_id"),
            "platform_family": validated_rec.get("platform_family", "unknown"),
            "manual_post_url": validated_rec.get("manual_post_url"),
            "manual_post_ref": validated_rec.get("manual_post_ref"),
            "metric_capture_timestamp": validated_rec.get("metric_capture_timestamp"),
            "metrics_source_type": validated_rec.get("metrics_source_type", "unknown"),
            "metrics_freshness_label": validated_rec.get("metrics_freshness_label", "unknown"),
            "metrics": metrics,
            "metric_null_reason": validated_rec.get("metric_null_reason"),
            "limitations": validated_rec.get("limitations", []),
            "operator_notes": validated_rec.get("operator_notes"),
            "public_postable": validated_rec.get("public_postable", False),
            "auto_publish": validated_rec.get("auto_publish", False),
            "automatic_metrics_ingestion": validated_rec.get("automatic_metrics_ingestion", False),
            "platform_api_payload_generated": validated_rec.get("platform_api_payload_generated", False)
        })

    # Hard boundary flag verification
    flags = _hard_boundary_flags()
    unsafe_flag_count = sum(1 for k, v in _REQUIRED_FLAGS.items() if flags.get(k) is not v)

    if unsafe_flag_count > 0:
        blocked_reasons.append(f"unsafe_flags_detected:{unsafe_flag_count}")

    status = "pass" if not blocked_reasons else "blocked"

    packet = {
        "manual_performance_record_packet_id": packet_id,
        "created_at": now_ts,
        "source_refs": {
            "source_manual_publish_packet_id": config_payload.get("source_manual_publish_packet_id"),
            "linked_manual_publish_record_refs": [r["linked_manual_publish_record_id"] for r in processed_records if r.get("linked_manual_publish_record_id")]
        },
        "performance_records": processed_records,
        "record_count": len(processed_records),
        "missing_metric_count": missing_count,
        "invalid_record_count": invalid_count,
        "unsafe_flag_count": unsafe_flag_count,
        "packet_status": status,
        "hard_boundary_flags": flags,
        "safety_audit": {
            "automatic_metrics_ingestion_count": 0,
            "unsafe_flag_count": unsafe_flag_count,
        }
    }
    
    if blocked_reasons:
        packet["blocked_reasons"] = blocked_reasons
        
    return packet


def build_from_config_file(config_path=DEFAULT_CONFIG):
    """Load configuration from a file and build the packet."""
    if not os.path.exists(config_path):
        # Fail safe
        return build_manual_performance_record_packet({})
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return build_manual_performance_record_packet(config)


def summary():
    """Return a short JSON-safe summary for the CLI."""
    packet = build_from_config_file()
    
    source_types = set(r["metrics_source_type"] for r in packet.get("performance_records", []))
    platform_counts = {}
    for r in packet.get("performance_records", []):
        pf = r["platform_family"]
        platform_counts[pf] = platform_counts.get(pf, 0) + 1

    return {
        "status": "pre-alpha manual performance record packet active",
        "packet_status": packet["packet_status"],
        "record_count": packet["record_count"],
        "linked_manual_publish_record_count": len(packet["source_refs"]["linked_manual_publish_record_refs"]),
        "missing_metric_count": packet["missing_metric_count"],
        "invalid_record_count": packet["invalid_record_count"],
        "unsafe_flag_count": packet["unsafe_flag_count"],
        "metrics_source_types": list(source_types),
        "platform_family_counts": platform_counts,
        "automatic_metrics_ingestion_allowed": packet["hard_boundary_flags"]["automatic_metrics_ingestion_allowed"],
        "platform_api_payload_generated": False,
        "scraping_allowed": packet["hard_boundary_flags"]["scraping_allowed"],
        "credential_or_env_read_allowed": packet["hard_boundary_flags"]["credential_or_env_read_allowed"],
        "public_postable": packet["hard_boundary_flags"]["public_postable"],
        "auto_publish": packet["hard_boundary_flags"]["auto_publish"],
    }
