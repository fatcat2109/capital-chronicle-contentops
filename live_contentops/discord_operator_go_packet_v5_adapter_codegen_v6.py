"""Codegen for V5 Discord Operator GO Packet adapter."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "docs" / "automation" / "V6_DISCORD_OPERATOR_GO_PACKET"
PACKET_FILE = PACKET_DIR / "discord_operator_go_packet.json"
NORMALIZED_FILE = PACKET_DIR / "normalized_candidate" / "normalized_operator_go_source_candidate.json"
PHRASE_FILE = PACKET_DIR / "operator_go_phrase_validation_model.json"
SAFETY_FILE = PACKET_DIR / "safety_signature_preview.json"
TS_ADAPTER_FILE = ROOT / "ui" / "contentops_v5" / "src" / "data" / "discordOperatorGoPacketAdapter.ts"


def _load(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json_object_required:{path}")
    return data


def generate_operator_go_adapter(verify_only: bool = False) -> dict:
    packet = _load(PACKET_FILE)
    normalized = _load(NORMALIZED_FILE)
    phrase = _load(PHRASE_FILE)
    safety = _load(SAFETY_FILE)
    code = f"""// Capital Chronicle ContentOps V5 — Discord Operator GO Packet Adapter.
// Generated from local review-only GO packet artifacts. Do not manually edit.

export const discordOperatorGoPacket = {json.dumps(packet, indent=2)};

export const normalizedOperatorGoSourceCandidate = {json.dumps(normalized, indent=2)};

export const operatorGoPhraseValidationModel = {json.dumps(phrase, indent=2)};

export const operatorGoSafetySignaturePreview = {json.dumps(safety, indent=2)};
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
    print(f"Operator GO codegen response: {generate_operator_go_adapter()}")
