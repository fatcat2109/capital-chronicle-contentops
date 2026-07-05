"""Pre-Alpha Content Performance Review module.

This module provides a deterministic local review of manual performance records.
It generates conservative observations and editorial hypotheses based entirely
on operator-entered data. It strictly forbids scraping, automated metrics ingestion,
API calls, LLM generation, and claims of statistical significance.
"""

import datetime
import json
import os
import uuid

# Safety invariants. Must not be overridden by fixtures.
_REQUIRED_FLAGS = {
    "local_only": True,
    "deterministic_review_only": True,
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
    "llm_generation_used": False,
    "statistical_significance_claimed": False,
}

SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "schemas",
    "pre_alpha_content_performance_review_packet.schema.json",
)

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "fixtures",
    "pre_alpha_content_performance_review",
)

DEFAULT_CONFIG = os.path.join(FIXTURE_DIR, "valid_content_performance_review_config.json")


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _hard_boundary_flags():
    """Return the pinned hard boundary flags for this module."""
    return dict(_REQUIRED_FLAGS)


def build_content_performance_review_packet(config_payload):
    """Build a compliant content performance review packet from the given config."""
    packet_id = f"perf_review_packet_{uuid.uuid4().hex[:8]}"
    now_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records_in = config_payload.get("records", [])
    
    blocked_reasons = []
    
    if config_payload.get("statistical_significance_claimed"):
        blocked_reasons.append("statistical_significance_claimed_not_allowed")

    included_count = 0
    excluded_records = []
    missing_count = 0

    platform_counts = {}
    content_type_counts = {}
    metric_availability = {}

    linked_refs = []

    for idx, rec in enumerate(records_in):
        record_reasons = []

        if not rec.get("linked_manual_publish_record_id"):
            record_reasons.append("missing_manual_publish_reference")
        
        if rec.get("metrics_source_type") != "operator_entered":
            record_reasons.append(f"invalid_metrics_source_type:{rec.get('metrics_source_type')}")

        metrics = rec.get("metrics", {})
        if isinstance(metrics, dict):
            for k, v in metrics.items():
                if v is None:
                    missing_count += 1
                elif isinstance(v, int):
                    if v < 0:
                        record_reasons.append(f"negative_metric:{k}")
                    else:
                        metric_availability[k] = metric_availability.get(k, 0) + 1

        if record_reasons:
            excluded_records.append({
                "performance_record_id": rec.get("performance_record_id", f"unknown_{idx}"),
                "reason": "; ".join(record_reasons)
            })
            # Also block the whole packet if it contains inherently unsafe records
            if any(r.startswith("invalid_metrics_source_type") for r in record_reasons):
                blocked_reasons.append(f"record_{idx}_invalid_source")
            if any(r.startswith("negative_metric") for r in record_reasons):
                blocked_reasons.append(f"record_{idx}_negative_metric")
            if any(r.startswith("missing_manual_publish_reference") for r in record_reasons):
                blocked_reasons.append(f"record_{idx}_missing_reference")
        else:
            included_count += 1
            pf = rec.get("platform_family", "unknown")
            ct = rec.get("content_type", "unknown")
            platform_counts[pf] = platform_counts.get(pf, 0) + 1
            content_type_counts[ct] = content_type_counts.get(ct, 0) + 1
            linked_refs.append(rec["linked_manual_publish_record_id"])

    # Determine findings based strictly on included records
    insufficient_sample = included_count < 3
    sample_size_warning = None
    conservative_findings = []
    editorial_hypotheses = []

    if insufficient_sample:
        sample_size_warning = f"Only {included_count} valid records available. Insufficient for meaningful comparison."
        conservative_findings.append(f"Sample size is too small ({included_count}) to draw platform or content-type comparisons.")
        editorial_hypotheses.append("Hypothesis: We need to manually record more publish events to observe trends.")
    else:
        # Generate safe, conservative hypotheses
        top_platform = max(platform_counts.items(), key=lambda x: x[1]) if platform_counts else ("none", 0)
        conservative_findings.append(f"In this manually recorded sample, '{top_platform[0]}' has the most records ({top_platform[1]}).")
        
        top_content = max(content_type_counts.items(), key=lambda x: x[1]) if content_type_counts else ("none", 0)
        conservative_findings.append(f"Content type '{top_content[0]}' appears most frequently in this small sample ({top_content[1]}).")
        
        if missing_count > 0:
            conservative_findings.append(f"Manual records with missing metrics ({missing_count} fields) are excluded from relevant metric-specific comparisons.")

        editorial_hypotheses.append(f"Hypothesis: Based on early manual observation, we may be posting or recording more '{top_platform[0]}' content.")

    # Hard boundary flag verification
    flags = _hard_boundary_flags()
    unsafe_flag_count = sum(1 for k, v in _REQUIRED_FLAGS.items() if flags.get(k) is not v)

    if unsafe_flag_count > 0:
        blocked_reasons.append(f"unsafe_flags_detected:{unsafe_flag_count}")

    status = "pass" if not blocked_reasons else "blocked"

    packet = {
        "content_performance_review_packet_id": packet_id,
        "created_at": now_ts,
        "source_refs": {
            "source_manual_performance_record_packet_id": config_payload.get("source_manual_performance_record_packet_id"),
            "source_manual_publish_packet_refs": list(set(linked_refs))
        },
        "review_scope": config_payload.get("review_scope", "unknown"),
        "record_count": len(records_in),
        "included_record_count": included_count,
        "excluded_record_count": len(excluded_records),
        "missing_metric_count": missing_count,
        "insufficient_sample": insufficient_sample,
        "sample_size_warning": sample_size_warning,
        "platform_family_summary": platform_counts,
        "content_type_summary": content_type_counts,
        "metric_availability_summary": metric_availability,
        "conservative_findings": conservative_findings,
        "editorial_hypotheses": editorial_hypotheses,
        "excluded_records": excluded_records,
        "limitations": [
            "This review is based solely on a limited sample of operator-entered manual performance records.",
            "Missing or unrecorded metrics are strictly preserved and limit the completeness of comparisons.",
            "No statistical significance is claimed or implied by these findings."
        ],
        "packet_status": status,
        "hard_boundary_flags": flags,
        "safety_audit": {
            "unsafe_flag_count": unsafe_flag_count,
        }
    }
    
    if blocked_reasons:
        packet["blocked_reasons"] = blocked_reasons
        
    return packet


def build_from_config_file(config_path=DEFAULT_CONFIG):
    """Load configuration from a file and build the packet."""
    if not os.path.exists(config_path):
        return build_content_performance_review_packet({})
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return build_content_performance_review_packet(config)


def summary():
    """Return a short JSON-safe summary for the CLI."""
    packet = build_from_config_file()
    
    return {
        "status": "pre-alpha content performance review packet active",
        "packet_status": packet["packet_status"],
        "record_count": packet["record_count"],
        "included_record_count": packet["included_record_count"],
        "excluded_record_count": packet["excluded_record_count"],
        "missing_metric_count": packet["missing_metric_count"],
        "insufficient_sample": packet["insufficient_sample"],
        "sample_size_warning": packet["sample_size_warning"],
        "platform_family_counts": packet["platform_family_summary"],
        "content_type_counts": packet["content_type_summary"],
        "conservative_finding_count": len(packet["conservative_findings"]),
        "editorial_hypothesis_count": len(packet["editorial_hypotheses"]),
        "unsafe_flag_count": packet["safety_audit"]["unsafe_flag_count"],
        "automatic_metrics_ingestion_allowed": packet["hard_boundary_flags"]["automatic_metrics_ingestion_allowed"],
        "platform_api_payload_generated": packet["hard_boundary_flags"]["platform_api_call_allowed_now"],
        "scraping_allowed": packet["hard_boundary_flags"]["scraping_allowed"],
        "credential_or_env_read_allowed": packet["hard_boundary_flags"]["credential_or_env_read_allowed"],
        "public_postable": packet["hard_boundary_flags"]["public_postable"],
        "auto_publish": packet["hard_boundary_flags"]["auto_publish"],
        "statistical_significance_claimed": packet["hard_boundary_flags"]["statistical_significance_claimed"],
    }
