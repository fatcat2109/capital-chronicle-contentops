import pytest
from live_contentops import pre_alpha_approved_cc_artifact_intake
import jsonschema
import json
import os

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'schemas', 'pre_alpha_approved_cc_artifact_intake_packet.schema.json')

def test_approved_cc_artifact_intake_summary_validates_against_schema():
    packet = pre_alpha_approved_cc_artifact_intake.summary()
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    jsonschema.validate(instance=packet, schema=schema)

def test_approved_cc_artifact_intake_blocks_unsafe_artifacts():
    packet = pre_alpha_approved_cc_artifact_intake.summary()
    
    # We loaded 10 fixtures. Only 1 is completely clean.
    assert packet["accepted_artifact_count"] == 1
    assert packet["blocked_artifact_count"] == 9
    assert packet["packet_status"] == "blocked"
    
    blocked_reasons = [item for sublist in [a["blocked_reasons"] for a in packet["blocked_artifacts"]] for item in sublist]
    
    assert "artifact is not explicitly operator-approved" in blocked_reasons
    assert "source artifact ID is missing" in blocked_reasons
    assert "freshness is missing" in blocked_reasons
    assert "limitations are missing" in blocked_reasons
    assert "DQR/data sufficiency blocks forecast readiness but the artifact implies confident forecast content" in blocked_reasons
    assert "proxy-only data is not labeled" in blocked_reasons
    assert "missing/degraded data is hidden" in blocked_reasons
    assert "raw vendor data is included for redistribution" in blocked_reasons
    assert "artifact contains financial advice/signal language: buy" in blocked_reasons
    assert "artifact implies public-postable or auto-publish or platform API payload" in blocked_reasons

def test_approved_cc_artifact_intake_preserves_hard_boundaries():
    packet = pre_alpha_approved_cc_artifact_intake.summary()
    flags = packet["hard_boundary_flags"]
    assert flags["local_only"] is True
    assert flags["public_postable"] is False
    assert flags["auto_publish"] is False
    assert flags["platform_api_call_allowed_now"] is False
    assert flags["core_repo_mutation_allowed_now"] is False
    assert packet["safety_audit"]["unsafe_flag_count"] == 0
