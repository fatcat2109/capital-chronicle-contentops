"""Codegen for V5 Discord supervised live-dispatch dry-run gate adapter."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "docs" / "automation" / "V6_DISCORD_SUPERVISED_LIVE_DISPATCH_DRY_RUN_GATE"
PACKET_FILE = PACKET_DIR / "discord_supervised_live_dispatch_dry_run_gate_packet.json"
ENVELOPE_FILE = PACKET_DIR / "dry_run_request_envelope_preview.json"
SAFETY_FILE = PACKET_DIR / "dry_run_safety_signature.json"
TS_ADAPTER_FILE = ROOT / "ui" / "contentops_v5" / "src" / "data" / "discordSupervisedLiveDispatchDryRunGateAdapter.ts"


def _load(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json_object_required:{path}")
    return data


def generate_dry_run_gate_adapter(verify_only: bool = False) -> dict:
    packet = _load(PACKET_FILE)
    envelope = _load(ENVELOPE_FILE)
    safety = _load(SAFETY_FILE)
    code = f"""// Capital Chronicle ContentOps V5 — Discord Live-Dispatch Dry-Run Gate Adapter.
// Generated from local fail-closed dry-run gate artifacts. Do not manually edit.

export const discordSupervisedLiveDispatchDryRunGatePacket = {json.dumps(packet, indent=2)};

export const discordDryRunRequestEnvelopePreview = {json.dumps(envelope, indent=2)};

export const discordDryRunSafetySignature = {json.dumps(safety, indent=2)};
"""
    if verify_only:
        if not TS_ADAPTER_FILE.exists():
            return {"adapter_in_sync": False, "reason": "Adapter file missing"}
        in_sync = TS_ADAPTER_FILE.read_text(encoding="utf-8").strip() == code.strip()
        return {"adapter_in_sync": in_sync, "packet_hash_matches": in_sync}
    TS_ADAPTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    TS_ADAPTER_FILE.write_text(code, encoding="utf-8")
    return {"adapter_written": True}


if __name__ == "__main__":
    print(f"Dry-run gate codegen response: {generate_dry_run_gate_adapter()}")
