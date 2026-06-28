import json
from pathlib import Path
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


def test_mutation_after_hash_detected(tmp_path):
    manifest = {
        "x_manual_thread": {
            "segment_hashes": ["a" * 64]
        }
    }
    # Create a mock hash manifest
    hash_manifest_data = {
        "platform_variant_pack_hash": "different_hash_value"
    }
    hash_manifest_path = tmp_path / "unified_payload_hash_manifest.json"
    hash_manifest_path.write_text(json.dumps(hash_manifest_data), encoding="utf-8")
    
    # We expect that if the variant pack is recomputed and does not match, a mutation is detected.
    # Since docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_pack.json exists,
    # the validator will read it, compute its hash, and compare it to "different_hash_value".
    # Because "different_hash_value" is definitely wrong, it will mismatch and trigger the blocker.
    report = integrity.validate_integrity(tmp_path, manifest)
    assert report["payload_integrity_valid"] is False
    assert "payload_mutation_after_hash_detected" in report["blockers"]
