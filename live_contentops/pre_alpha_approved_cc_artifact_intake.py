"""Local-only operator-approved Capital Chronicle artifact intake contract (Task 0123).

Deterministic validator for artifacts exported from the core repo.
Never mutates core repo, never connects to external APIs, never creates public-postable content.
"""

import json
import os
import glob
from datetime import datetime

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'pre_alpha_approved_cc_artifact_intake')

def load_fixture_records():
    records = []
    if not os.path.exists(FIXTURES_DIR):
        return records
    for fp in glob.glob(os.path.join(FIXTURES_DIR, "*.json")):
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                records.extend(data)
            elif isinstance(data, dict):
                records.append(data)
    return records

def build_from_fixtures():
    records = load_fixture_records()
    return build_intake_packet(records)

def build_intake_packet(records):
    # Fallback if unmocked in test, just use current time safely
    now = datetime.utcnow()
    packet = {
        "approved_cc_artifact_intake_packet_id": f"cc_intake_{now.strftime('%Y%m%d%H%M%S')}",
        "created_at": now.isoformat() + "Z",
        "source_refs": [],
        "operator_supplied_artifact_records": len(records),
        "accepted_artifact_count": 0,
        "blocked_artifact_count": 0,
        "accepted_artifacts": [],
        "blocked_artifacts": [],
        "hard_boundary_flags": {
            "local_only": True,
            "operator_supplied_artifacts_only": True,
            "approved_artifact_intake_only": True,
            "manual_review_required": True,
            "operator_final_check_required": True,
            "fixture_only": True,
            "public_postable": False,
            "auto_approval": False,
            "auto_publish": False,
            "platform_api_call_allowed_now": False,
            "provider_call_allowed_now": False,
            "network_call_allowed_now": False,
            "scheduler_allowed": False,
            "scraping_allowed": False,
            "automatic_metrics_ingestion_allowed": False,
            "credential_or_env_read_allowed": False,
            "live_execution_allowed_now": False,
            "core_repo_read_allowed_now": False,
            "core_repo_mutation_allowed_now": False
        },
        "safety_audit": {
            "unsafe_flag_count": 0
        },
        "packet_status": "pass"
    }

    FORBIDDEN_TERMS = [
        "buy", "sell", "hold", "position sizing", "execution", "order routing", "guaranteed"
    ]

    for rec in records:
        reasons = []
        is_blocked = False
        
        if rec.get("approval_status") != "approved":
            reasons.append("artifact is not explicitly operator-approved")
        
        if not rec.get("source_artifact_id"):
            reasons.append("source artifact ID is missing")
        
        if not rec.get("freshness"):
            reasons.append("freshness is missing")
        
        if not rec.get("limitations"):
            reasons.append("limitations are missing")
            
        ctype = rec.get("content_type")
        if not ctype or ctype not in ["macro_education", "market_note", "deep_dive", "data_primer"]:
            reasons.append("content type is missing or outside accepted content taxonomy")
            
        dqr = rec.get("dqr_status") or rec.get("data_sufficiency_status", "")
        forecast = rec.get("forecast_readiness_status", "")
        if dqr == "blocked" and "forecast" in forecast.lower():
            reasons.append("DQR/data sufficiency blocks forecast readiness but the artifact implies confident forecast content")
            
        proxy_flags = rec.get("proxy_data_flags", [])
        text_content = json.dumps(rec).lower()
        # To avoid triggering on the JSON keys, just dump the values
        values_content = json.dumps(list(rec.values())).lower()
        
        if "has_proxy" in values_content and not proxy_flags:
            reasons.append("proxy-only data is not labeled")
            
        degraded = rec.get("degraded_data_flags", [])
        missing = rec.get("missing_data_flags", [])
        if "missing" in values_content and not degraded and not missing:
            reasons.append("missing/degraded data is hidden")
            
        if rec.get("raw_vendor_data_included") and rec.get("redistribution_allowed") is True:
            reasons.append("raw vendor data is included for redistribution")
            
        import re
        values_str = str(rec.values()).lower()
        for term in FORBIDDEN_TERMS:
            if re.search(r'\b' + term + r'\b', values_str):
                reasons.append(f"artifact contains financial advice/signal language: {term}")
                
        if rec.get("public_postable") or rec.get("auto_publish") or rec.get("platform_api_payload_generated"):
            reasons.append("artifact implies public-postable or auto-publish or platform API payload")
            
        if reasons:
            is_blocked = True
            
        intake_artifact = {
            "artifact_type": rec.get("artifact_type", "unknown"),
            "source_artifact_id": rec.get("source_artifact_id", "unknown"),
            "source_system": rec.get("source_system", "cc_core"),
            "source_export_timestamp": rec.get("source_export_timestamp", packet["created_at"]),
            "operator_approval_ref": rec.get("operator_approval_ref", "unknown"),
            "approval_status": rec.get("approval_status", "unknown"),
            "content_type": rec.get("content_type", "unknown"),
            "freshness": rec.get("freshness", []),
            "limitations": rec.get("limitations", []),
            "data_sufficiency_status": rec.get("data_sufficiency_status", "unknown"),
            "forecast_readiness_status": rec.get("forecast_readiness_status", "unknown"),
            "dqr_status": rec.get("dqr_status", "unknown"),
            "missing_data_flags": rec.get("missing_data_flags", []),
            "proxy_data_flags": rec.get("proxy_data_flags", []),
            "degraded_data_flags": rec.get("degraded_data_flags", []),
            "raw_vendor_data_included": rec.get("raw_vendor_data_included", False),
            "redistribution_allowed": rec.get("redistribution_allowed", False),
            "public_postable": False,
            "auto_publish": False,
            "platform_api_payload_generated": False,
            "blocked_reasons": reasons,
            "packet_status": "blocked" if is_blocked else "accepted_for_local_contentops_review"
        }
        
        if is_blocked:
            packet["blocked_artifacts"].append(intake_artifact)
        else:
            packet["accepted_artifacts"].append(intake_artifact)
            packet["source_refs"].append(intake_artifact["source_artifact_id"])
            
    packet["accepted_artifact_count"] = len(packet["accepted_artifacts"])
    packet["blocked_artifact_count"] = len(packet["blocked_artifacts"])
    if packet["blocked_artifact_count"] > 0:
        packet["packet_status"] = "blocked"
        
    return packet

def summary():
    return build_from_fixtures()
