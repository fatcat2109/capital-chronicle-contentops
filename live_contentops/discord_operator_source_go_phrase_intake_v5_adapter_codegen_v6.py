"""Codegen for V5 Discord operator source + GO phrase intake adapter."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "docs" / "automation" / "V6_DISCORD_OPERATOR_SOURCE_AND_GO_PHRASE_INTAKE"
PACKET_FILE = PACKET_DIR / "operator_source_go_phrase_intake_packet.json"
NORMALIZED_FILE = PACKET_DIR / "normalized_candidate" / "normalized_operator_source_go_phrase_candidate.json"
PHRASE_FILE = PACKET_DIR / "operator_go_phrase_evidence.json"
DESTINATION_FILE = PACKET_DIR / "destination_binding_proof.json"
SAFETY_FILE = PACKET_DIR / "operator_source_go_phrase_safety_signature.json"
TS_ADAPTER_FILE = ROOT / "ui" / "contentops_v5" / "src" / "data" / "discordOperatorSourceGoPhraseIntakeAdapter.ts"


def _load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json_object_required:{path}")
    return data


def generate_operator_source_go_phrase_intake_adapter(verify_only: bool = False) -> dict:
    packet = _load(PACKET_FILE)
    normalized = _load(NORMALIZED_FILE)
    phrase = _load(PHRASE_FILE)
    destination = _load(DESTINATION_FILE)
    safety = _load(SAFETY_FILE)
    code = f"""// Capital Chronicle ContentOps V5 — Discord Operator Source + GO Phrase Intake Adapter.
// Generated from local fail-closed intake artifacts. Do not manually edit.

export const discordOperatorSourceGoPhraseIntakePacket = {json.dumps(packet, indent=2)};

export const normalizedOperatorSourceGoPhraseCandidate = {json.dumps(normalized, indent=2)};

export const operatorGoPhraseEvidence = {json.dumps(phrase, indent=2)};

export const discordDestinationBindingProof = {json.dumps(destination, indent=2)};

export const operatorSourceGoPhraseSafetySignature = {json.dumps(safety, indent=2)};
"""
    if verify_only:
        if not TS_ADAPTER_FILE.exists():
            return {"adapter_in_sync": False, "reason": "Adapter file missing"}
        in_sync = TS_ADAPTER_FILE.read_text(encoding="utf-8").strip() == code.strip()
        return {"adapter_in_sync": in_sync, "packet_hash_matches": in_sync}
    TS_ADAPTER_FILE.write_text(code, encoding="utf-8")
    return {"adapter_written": True}


if __name__ == "__main__":
    print(f"Operator source GO phrase intake codegen response: {generate_operator_source_go_phrase_intake_adapter()}")
