"""V5 Adapter Codegen for Canonical Draft Final Review and Platform Variant Preview."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = ROOT / "docs/automation/V6_CANONICAL_DRAFT_FINAL_REVIEW_TO_PLATFORM_VARIANT_PREVIEW/canonical_draft_final_review_to_platform_variant_preview_packet.json"
ADAPTER_PATH = ROOT / "ui/contentops_v5/src/data/canonicalDraftFinalReviewVariantPreviewAdapter.ts"


def generate_or_check_adapter(verify_only: bool = False) -> dict[str, bool]:
    """Generates the TypeScript adapter or verifies if it matches the packet."""
    if not PACKET_PATH.exists():
        raise FileNotFoundError(f"Packet file not found at {PACKET_PATH}")

    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    
    header = (
        "// V6 Canonical draft final review and platform variant preview adapter.\n"
        "// Generated from committed local/manual-only packet; no network/env/browser/provider access.\n\n"
    )
    content = f"{header}export const canonicalDraftFinalReviewVariantPreviewPacket = {json.dumps(packet, indent=2, sort_keys=True)} as const;\n"

    if verify_only:
        if not ADAPTER_PATH.exists():
            return {"adapter_in_sync": False, "packet_hash_matches": False}
        existing = ADAPTER_PATH.read_text(encoding="utf-8")
        in_sync = (existing == content)
        return {"adapter_in_sync": in_sync, "packet_hash_matches": in_sync}

    # Write to target path
    ADAPTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    ADAPTER_PATH.write_text(content, encoding="utf-8")
    return {"adapter_in_sync": True, "packet_hash_matches": True}


if __name__ == "__main__":
    res = generate_or_check_adapter(verify_only=False)
    print(json.dumps(res, indent=2))
