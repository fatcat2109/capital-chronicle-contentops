"""Codegen preflight tests for V6 Discord Supervised Live Preflight."""
from __future__ import annotations

from pathlib import Path
from live_contentops.discord_supervised_live_preflight_v5_adapter_codegen_v6 import generate_preflight_adapter

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "ui" / "contentops_v5" / "src" / "data" / "discordSupervisedLivePreflightAdapter.ts"


def test_codegen_sync_check() -> None:
    res = generate_preflight_adapter(verify_only=True)
    assert res["adapter_in_sync"] is True
    assert res["packet_hash_matches"] is True


def test_adapter_exports() -> None:
    assert ADAPTER_PATH.exists()
    content = ADAPTER_PATH.read_text(encoding="utf-8")
    assert "discordSupervisedLivePreflightPacket" in content
    assert "normalizedDiscordPayloadCandidate" in content
    assert "requestEnvelopePreview" in content
    assert "operatorLiveGoPhrase" in content
    assert "discord_supervised_live_preflight_v0" in content
