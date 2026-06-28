"""V6 Unified Payload Hash Manifest.

Computes deterministic, canonical JSON SHA-256 hashes for all V6 payload outputs.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"


def get_canonical_json_hash(obj: Any) -> str:
    """Helper to compute deterministic compact sorted JSON hash with normalized newlines."""
    def normalize_newlines(v: Any) -> Any:
        if isinstance(v, str):
            return v.replace("\r\n", "\n")
        if isinstance(v, dict):
            return {k: normalize_newlines(val) for k, val in v.items()}
        if isinstance(v, (list, tuple)):
            return [normalize_newlines(val) for val in v]
        return v
        
    normalized = normalize_newlines(obj)
    serialized = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def generate_hashes(
    out_dir: Path,
    contract_packet: dict[str, Any],
    manifest_data: dict[str, Any]
) -> None:
    """Computes all required payload and segment hashes, storing them in unified_payload_hash_manifest.json."""
    canonical_article_hash = get_canonical_json_hash(contract_packet.get("canonical_article"))
    seo_packet_hash = get_canonical_json_hash(contract_packet.get("seo_packet"))
    platform_variant_pack_hash = get_canonical_json_hash(contract_packet.get("variant_pack"))
    thread_continuation_pack_hash = get_canonical_json_hash(contract_packet.get("thread_pack"))
    draft_inspector_packet_hash = get_canonical_json_hash(contract_packet.get("draft_inspector"))
    
    per_platform_payload_hashes = {}
    for fam, var in manifest_data.items():
        per_platform_payload_hashes[fam] = get_canonical_json_hash(var)
        
    # Build unified payload bundle hash from all components
    bundle_components = {
        "canonical_article_hash": canonical_article_hash,
        "seo_packet_hash": seo_packet_hash,
        "platform_variant_pack_hash": platform_variant_pack_hash,
        "thread_continuation_pack_hash": thread_continuation_pack_hash,
        "draft_inspector_packet_hash": draft_inspector_packet_hash,
        "per_platform_payload_hashes": per_platform_payload_hashes
    }
    unified_payload_bundle_hash = get_canonical_json_hash(bundle_components)
    
    hash_manifest_packet = {
        "schema_version": SCHEMA_VERSION,
        "input_files": {
            "canonical_article": "docs/automation/V6_AI_PRODUCTION_CORE/sample_canonical_article_packet.json",
            "seo_packet": "docs/automation/V6_AI_PRODUCTION_CORE/sample_seo_editorial_packet.json",
            "variant_pack": "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/platform_variant_pack.json",
            "thread_pack": "docs/automation/V6_PLATFORM_CONTENT_GENERATORS/thread_continuation_pack.json",
            "draft_inspector": "docs/automation/V6_DRAFT_INSPECTOR_V2/draft_inspector_v2_packet.json"
        },
        "canonical_article_hash": canonical_article_hash,
        "seo_packet_hash": seo_packet_hash,
        "platform_variant_pack_hash": platform_variant_pack_hash,
        "thread_continuation_pack_hash": thread_continuation_pack_hash,
        "draft_inspector_packet_hash": draft_inspector_packet_hash,
        "per_platform_payload_hashes": per_platform_payload_hashes,
        "unified_payload_bundle_hash": unified_payload_bundle_hash
    }
    
    Path(out_dir / "unified_payload_hash_manifest.json").write_text(
        json.dumps(hash_manifest_packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
