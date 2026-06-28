import json
from live_contentops import multi_platform_payload_integrity_v6 as integrity

def test_integrity_validation_checks(tmp_path):
    # Test stub segment hash
    manifest = {
        "x_manual_thread": {
            "segment_hashes": ["stub_hash_value"]
        }
    }
    report = integrity.validate_integrity(tmp_path, manifest)
    assert report["payload_integrity_valid"] is False
    assert "stub_segment_hash_detected" in report["blockers"]
