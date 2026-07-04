"""Codegen tests for explicit live scope gate adapter."""
from __future__ import annotations

from pathlib import Path
from live_contentops.explicit_live_scope_gate_source_candidate_v5_adapter_codegen_v6 import generate_or_check_gate_adapter

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "ui" / "contentops_v5" / "src" / "data" / "explicitLiveScopeGateSourceCandidateAdapter.ts"


def test_codegen_sync_check() -> None:
    res = generate_or_check_gate_adapter(verify_only=True)
    assert res["adapter_in_sync"] is True
    assert res["packet_hash_matches"] is True


def test_adapter_exports() -> None:
    assert ADAPTER_PATH.exists()
    content = ADAPTER_PATH.read_text(encoding="utf-8")
    assert "explicitLiveScopeGatePacket" in content
    assert "normalizedDispatchCandidate" in content
    assert "operator_recovery_to_explicit_live_scope_gate_source_candidate_v0" in content
