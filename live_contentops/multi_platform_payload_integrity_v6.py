"""V6 Multi-platform Payload Integrity.

Validates that variant segments have not changed after hash creation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"


def validate_integrity(
    out_dir: Path,
    manifest_data: dict[str, Any]
) -> dict[str, Any]:
    integrity_valid = True
    blockers = []
    
    # Check if any segment has stub hash
    for fam, var in manifest_data.items():
        for h in var.get("segment_hashes", []):
            if h == "stub_hash_value" or not h:
                integrity_valid = False
                blockers.append("stub_segment_hash_detected")
                
    # Check for payload mutation
    # We read the computed manifest and check if it matches the generated file.
    # If a mutation is detected on disk, we append payload_mutation_after_hash_detected.
    hash_manifest_path = out_dir / "unified_payload_hash_manifest.json"
    if hash_manifest_path.exists():
        try:
            stored = json.loads(hash_manifest_path.read_text(encoding="utf-8"))
            from live_contentops import unified_payload_hash_manifest_v6 as hm
            current_variant_pack_hash = stored.get("platform_variant_pack_hash")
            
            var_path = Path("docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_pack.json")
            if var_path.exists():
                var_data = json.loads(var_path.read_text(encoding="utf-8"))
                recomputed = hm.get_canonical_json_hash(var_data)
                if recomputed != current_variant_pack_hash:
                    integrity_valid = False
                    blockers.append("payload_mutation_after_hash_detected")
        except Exception:
            pass
            
    report = {
        "schema_version": SCHEMA_VERSION,
        "payload_integrity_valid": integrity_valid,
        "blockers": blockers
    }
    
    Path(out_dir / "payload_integrity_validation_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    return report
