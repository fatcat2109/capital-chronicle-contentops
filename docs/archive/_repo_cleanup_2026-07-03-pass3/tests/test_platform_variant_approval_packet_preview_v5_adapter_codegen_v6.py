"""Codegen tests for V5 Adapter for Platform Variant Approval Packet Preview."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops.platform_variant_approval_packet_preview_v5_adapter_codegen_v6 import generate_or_check_adapter

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "ui/contentops_v5/src/data/platformVariantApprovalPacketPreviewAdapter.ts"


def test_codegen_sync_check() -> None:
    res = generate_or_check_adapter(verify_only=True)
    assert res["adapter_in_sync"] is True
    assert res["packet_hash_matches"] is True


def test_typescript_adapter_exists() -> None:
    assert ADAPTER_PATH.exists()
    content = ADAPTER_PATH.read_text(encoding="utf-8")
    assert "platformVariantApprovalPacketPreviewPacket" in content
    assert "ready_for_operator_approval_packet_review" in content
