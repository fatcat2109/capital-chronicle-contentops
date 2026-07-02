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
KILL_SWITCH_FILE = PACKET_DIR / "kill_switch_evidence" / "discord_kill_switch_evidence.json"
CREDENTIAL_PRESENCE_FILE = PACKET_DIR / "credential_presence_evidence" / "discord_credential_presence_evidence.json"
PRE_DISPATCH_FILE = PACKET_DIR / "pre_dispatch_readiness" / "discord_pre_dispatch_readiness.json"
SAFETY_FILE = PACKET_DIR / "operator_source_go_phrase_safety_signature.json"
LIVE_PREFLIGHT_FILE = PACKET_DIR / "live_preflight" / "discord_blocked_live_preflight.json"
OPERATOR_INPUT_CONTRACT_FILE = PACKET_DIR / "operator_input_contract" / "discord_operator_supplied_live_preflight_input_contract.json"
REDACTED_OPERATOR_REVIEW_FILE = PACKET_DIR / "redacted_operator_review" / "discord_redacted_operator_review_packet.json"
OPERATOR_REVIEW_DECISION_FILE = PACKET_DIR / "operator_review_decision" / "discord_operator_review_decision_packet.json"
DISPATCH_DECISION_READINESS_FILE = PACKET_DIR / "dispatch_decision_readiness" / "discord_dispatch_decision_readiness.json"
DISPATCH_ROUTE_PREVIEW_FILE = PACKET_DIR / "dispatch_route_preview" / "discord_dispatch_route_preview.json"
OPERATOR_SUPERVISION_CONTRACT_FILE = PACKET_DIR / "operator_supervision_contract" / "discord_operator_supervision_contract.json"
TS_ADAPTER_FILE = ROOT / "ui" / "contentops_v5" / "src" / "data" / "discordOperatorSourceGoPhraseIntakeAdapter.ts"


def _load(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"json_object_required:{path}")
    return data


def generate_operator_source_go_phrase_intake_adapter(verify_only: bool = False) -> dict:
    packet = _load(PACKET_FILE)
    normalized = _load(NORMALIZED_FILE)
    envelope = _load(PACKET_DIR / "review_only_dry_run_envelope" / "discord_review_only_dry_run_envelope_normalization.json")
    phrase = _load(PHRASE_FILE)
    destination = _load(DESTINATION_FILE)
    kill_switch = _load(KILL_SWITCH_FILE)
    credential_presence = _load(CREDENTIAL_PRESENCE_FILE)
    fixture_review = _load(PACKET_DIR / "fixture_review" / "discord_operator_source_artifact_fixture_review.json")
    pre_dispatch = _load(PRE_DISPATCH_FILE)
    live_preflight = _load(LIVE_PREFLIGHT_FILE)
    operator_input_contract = _load(OPERATOR_INPUT_CONTRACT_FILE)
    redacted_review = _load(REDACTED_OPERATOR_REVIEW_FILE)
    review_decision = _load(OPERATOR_REVIEW_DECISION_FILE)
    dispatch_decision_readiness = _load(DISPATCH_DECISION_READINESS_FILE)
    dispatch_route_preview = _load(DISPATCH_ROUTE_PREVIEW_FILE)
    operator_supervision_contract = _load(OPERATOR_SUPERVISION_CONTRACT_FILE)
    safety = _load(SAFETY_FILE)
    code = f"""// Capital Chronicle ContentOps V5 — Discord Operator Source + GO Phrase Intake Adapter.
// Generated from local fail-closed intake artifacts. Do not manually edit.

export const discordOperatorSourceGoPhraseIntakePacket = {json.dumps(packet, indent=2)};

export const normalizedOperatorSourceGoPhraseCandidate = {json.dumps(normalized, indent=2)};

export const discordReviewOnlyDryRunEnvelopeNormalization = {json.dumps(envelope, indent=2)};

export const operatorGoPhraseEvidence = {json.dumps(phrase, indent=2)};

export const discordDestinationBindingProof = {json.dumps(destination, indent=2)};

export const discordKillSwitchEvidence = {json.dumps(kill_switch, indent=2)};

export const discordCredentialPresenceEvidence = {json.dumps(credential_presence, indent=2)};

export const discordOperatorSourceArtifactFixtureReview = {json.dumps(fixture_review, indent=2)};

export const discordPreDispatchReadiness = {json.dumps(pre_dispatch, indent=2)};

export const discordLivePreflightEvidence = {json.dumps(live_preflight, indent=2)};

export const discordOperatorInputContract = {json.dumps(operator_input_contract, indent=2)};

export const discordRedactedOperatorReviewPacket = {json.dumps(redacted_review, indent=2)};

export const discordOperatorReviewDecisionPacket = {json.dumps(review_decision, indent=2)};

export const discordDispatchDecisionReadiness = {json.dumps(dispatch_decision_readiness, indent=2)};

export const discordDispatchRoutePreview = {json.dumps(dispatch_route_preview, indent=2)};

export const discordOperatorSupervisionContract = {json.dumps(operator_supervision_contract, indent=2)};

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
