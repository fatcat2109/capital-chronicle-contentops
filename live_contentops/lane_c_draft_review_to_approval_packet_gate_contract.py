"""Lane C draft-review-to-approval-packet-gate contract, 0175AL.

Deterministic local-only contract mapping draft packets to approval stubs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.lane_c_editorial_brief_to_draft_review_only_packet_contract import (
    build_contract_packet as build_draft_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AL_LEDGER_FRONTIER_REPAIR_AND_DRAFT_APPROVAL_GATE_V0"
MATRIX_VERSION = "0175AL_LANE_C_DRAFT_REVIEW_TO_APPROVAL_PACKET_GATE_V1"
SOURCE_BASELINE_COMMIT = "6ba3bac45f676de8d340b4d3e7383283c5102068"
LEDGER_FAMILY = "lane_c_draft_review_to_approval_packet_gate_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AL"
PACKET_FILENAME = "lane_c_draft_review_to_approval_packet_gate_contract_packet.json"
RUNBOOK_FILENAME = "lane_c_draft_review_to_approval_packet_gate_contract.md"


def _asdict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, tuple):
        return [_asdict(v) for v in value]
    if isinstance(value, list):
        return [_asdict(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _asdict(v) for k, v in value.items()}
    return value


def _json(value: Any) -> str:
    return json.dumps(_asdict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def _digest(value: Any) -> str:
    return sha256(_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LaneCApprovalEvidenceRef:
    evidence_id: str
    reference_uri: str
    verification_status: str


@dataclass(frozen=True)
class LaneCApprovalChecklistItem:
    item_id: str
    description: str
    status: str


@dataclass(frozen=True)
class LaneCApprovalGateDecision:
    decision_id: str
    source_candidate_id: str
    gate_status: str
    blocked_reasons: list[str]
    next_required_gate: str


@dataclass(frozen=True)
class LaneCApprovalPacketStub:
    approval_packet_id: str
    source_draft_packet_id: str
    source_brief_id: str
    source_candidate_id: str
    gate_status: str
    approval_status: str
    operator_approval_required: bool
    manual_evidence_required: bool
    public_postable: bool
    dispatch_ready: bool
    platform_payload_allowed: bool
    platform_payload_created: bool
    human_review_required: bool
    dqr_status: str
    readiness_status: str
    current_truth_status: str
    claim_ledger_status: str
    citation_requirement_status: str
    limitation_block_status: str
    missing_proofs: list[str]
    blocked_reasons: list[str]
    operator_placeholders: dict[str, str]
    evidence_refs: list[LaneCApprovalEvidenceRef]
    packet_hash: str


@dataclass(frozen=True)
class LaneCDraftReviewToApprovalGatePacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    approval_stubs: list[LaneCApprovalPacketStub]
    decisions: list[LaneCApprovalGateDecision]
    safety_flags: dict[str, bool]
    blocked_reasons: list[str]
    missing_proofs: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_safety_flags() -> dict[str, bool]:
    return {
        "local_only": True,
        "fixture_only": True,
        "network_performed": False,
        "env_read": False,
        "credential_values_loaded": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "ingestion_repo_mutated": False,
        "dqr_cleared_by_contentops": False,
        "readiness_cleared_by_contentops": False,
        "current_truth_promoted": False,
        "public_postable": False,
        "dispatch_ready": False,
        "platform_payload_allowed": False,
        "platform_payload_created": False,
        "approved_for_publication": False,
        "financial_advice": False,
        "signal_language": False,
        "broker_order_execution": False,
        "raw_vendor_redistribution": False,
        "approved_internal_alpha_artifacts_available": False
    }


def map_draft_to_approval_stub(draft: dict[str, Any]) -> LaneCApprovalPacketStub:
    cid = draft.get("source_candidate_id", "")
    pid = draft.get("draft_packet_id", "")
    bid = draft.get("source_brief_id", "")
    blocked_reasons = draft.get("blocked_reasons", [])
    missing_proofs = draft.get("missing_proofs", [])

    is_eligible = (
        draft.get("review_only") is True
        and draft.get("public_postable") is False
        and draft.get("dispatch_ready") is False
        and draft.get("platform_payload_created") is False
        and draft.get("human_review_required") is True
    )

    if not is_eligible:
        gate_status = "rejected_if_public_postable_or_dispatch_ready_requested"
        approval_status = "rejected"
    else:
        if draft.get("draft_status") == "blocked":
            if "stale_or_missing_freshness" in blocked_reasons:
                gate_status = "blocked_unresolved_limitations"
            elif "missing_lineage_manifest" in blocked_reasons:
                gate_status = "blocked_unresolved_limitations"
            else:
                gate_status = "blocked_rejected_source_candidate"
            approval_status = "blocked"
        else:
            if "missing_operator_approval" in blocked_reasons:
                gate_status = "blocked_missing_operator_approval"
            elif "degraded_proxy_label_required" in blocked_reasons:
                gate_status = "blocked_unresolved_limitations"
            elif "not_authorized_signing_authority" in blocked_reasons:
                gate_status = "blocked_missing_citation_evidence"
            else:
                gate_status = "gate_packet_created_pending_operator_review"
            approval_status = "pending_operator_review"

    placeholders = {
        "operator_id_placeholder": "operator_id_placeholder",
        "operator_review_timestamp_placeholder": "operator_review_timestamp_placeholder",
        "manual_approval_note_placeholder": "manual_approval_note_placeholder",
        "evidence_packet_ref_placeholder": "evidence_packet_ref_placeholder",
    }

    evidence_refs = [
        LaneCApprovalEvidenceRef(
            evidence_id=f"evidence_{cid}",
            reference_uri=f"provenance://{cid}",
            verification_status="pending" if approval_status != "blocked" else "failed"
        )
    ]

    raw_stub = {
        "approval_packet_id": f"approval_packet_{cid}",
        "source_draft_packet_id": pid,
        "source_brief_id": bid,
        "source_candidate_id": cid,
        "gate_status": gate_status,
        "approval_status": approval_status,
        "operator_approval_required": True,
        "manual_evidence_required": True,
        "public_postable": False,
        "dispatch_ready": False,
        "platform_payload_allowed": False,
        "platform_payload_created": False,
        "human_review_required": True,
        "dqr_status": "dqr_unresolved",
        "readiness_status": "readiness_unresolved",
        "current_truth_status": "current_truth_unpromoted",
        "claim_ledger_status": "unverified",
        "citation_requirement_status": "unverified",
        "limitation_block_status": "active_limitations_present",
        "missing_proofs": list(sorted(set(missing_proofs + ["operator_signature_check"]))),
        "blocked_reasons": blocked_reasons,
        "operator_placeholders": placeholders,
        "evidence_refs": [_asdict(er) for er in evidence_refs],
    }

    stub_hash = _digest(raw_stub)
    return LaneCApprovalPacketStub(
        packet_hash=stub_hash,
        **raw_stub
    )


def map_rejected_decision_to_approval_stub(rd: dict[str, Any]) -> LaneCApprovalPacketStub:
    cid = rd["source_candidate_id"]
    blocked_reasons = rd["blocked_reasons"]

    placeholders = {
        "operator_id_placeholder": "operator_id_placeholder",
        "operator_review_timestamp_placeholder": "operator_review_timestamp_placeholder",
        "manual_approval_note_placeholder": "manual_approval_note_placeholder",
        "evidence_packet_ref_placeholder": "evidence_packet_ref_placeholder",
    }

    evidence_refs = [
        LaneCApprovalEvidenceRef(
            evidence_id=f"evidence_{cid}",
            reference_uri=f"provenance://{cid}",
            verification_status="failed"
        )
    ]

    raw_stub = {
        "approval_packet_id": f"approval_packet_{cid}",
        "source_draft_packet_id": "none",
        "source_brief_id": "none",
        "source_candidate_id": cid,
        "gate_status": "blocked_rejected_source_candidate",
        "approval_status": "rejected",
        "operator_approval_required": True,
        "manual_evidence_required": True,
        "public_postable": False,
        "dispatch_ready": False,
        "platform_payload_allowed": False,
        "platform_payload_created": False,
        "human_review_required": True,
        "dqr_status": "dqr_unresolved",
        "readiness_status": "readiness_unresolved",
        "current_truth_status": "current_truth_unpromoted",
        "claim_ledger_status": "unverified",
        "citation_requirement_status": "unverified",
        "limitation_block_status": "active_limitations_present",
        "missing_proofs": ["operator_signature_check", "security_escalation_clearance"],
        "blocked_reasons": blocked_reasons,
        "operator_placeholders": placeholders,
        "evidence_refs": [_asdict(er) for er in evidence_refs],
    }

    stub_hash = _digest(raw_stub)
    return LaneCApprovalPacketStub(
        packet_hash=stub_hash,
        **raw_stub
    )


def build_contract_packet() -> dict[str, Any]:
    draft_data = build_draft_packet()
    drafts = draft_data["draft_packets"]
    rejected_precedents = draft_data.get("rejected_decisions", [])

    stubs: list[LaneCApprovalPacketStub] = []
    decisions: list[LaneCApprovalGateDecision] = []
    blocked_reasons: list[str] = []

    # Map drafts
    for d in drafts:
        stub = map_draft_to_approval_stub(d)
        stubs.append(stub)
        blocked_reasons.extend(stub.blocked_reasons)
        decisions.append(
            LaneCApprovalGateDecision(
                decision_id=f"approval_decision_{stub.source_candidate_id}",
                source_candidate_id=stub.source_candidate_id,
                gate_status=stub.gate_status,
                blocked_reasons=stub.blocked_reasons,
                next_required_gate="lane_c_approval_packet_operator_signoff" if stub.approval_status not in ("blocked", "rejected") else "security_escalation_review"
            )
        )

    # Map rejected precedents
    for rd in rejected_precedents:
        stub = map_rejected_decision_to_approval_stub(rd)
        stubs.append(stub)
        blocked_reasons.extend(stub.blocked_reasons)
        decisions.append(
            LaneCApprovalGateDecision(
                decision_id=f"approval_decision_{stub.source_candidate_id}",
                source_candidate_id=stub.source_candidate_id,
                gate_status=stub.gate_status,
                blocked_reasons=stub.blocked_reasons,
                next_required_gate="security_escalation_review"
            )
        )

    safety = build_safety_flags()

    packet = LaneCDraftReviewToApprovalGatePacket(
        task_label=TASK_LABEL,
        matrix_version=MATRIX_VERSION,
        source_baseline_commit=SOURCE_BASELINE_COMMIT,
        generated_at_epoch=0,
        approval_stubs=stubs,
        decisions=decisions,
        safety_flags=safety,
        blocked_reasons=list(sorted(set(blocked_reasons))),
        missing_proofs=["operator_signature_check", "production_key_vault_verify"],
        ledger_family=LEDGER_FAMILY,
        packet_hash="",
        hash_algorithm=HASH_ALGORITHM,
        next_required_gate="lane_c_approval_packet_operator_signoff"
    )

    raw_packet = _asdict(packet)
    raw_packet.pop("packet_hash")
    packet_hash = _digest(raw_packet)

    final_packet = {
        "packet_hash": packet_hash,
        **raw_packet
    }
    return final_packet


def render_runbook(packet: dict[str, Any]) -> str:
    stubs = packet["approval_stubs"]
    decisions = packet["decisions"]
    safety = packet["safety_flags"]

    lines = [
        "# Lane C Draft Review to Approval Packet Gate Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local-only Lane C Draft Review to Approval Packet Gate.",
        "> It does not approve publication, does not compile platform payloads, and does not dispatch.",
        "> It preserves all cryptographic limitations, citations, DQR/readiness blocks, and operator signatures.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Matrix Version**: `{packet['matrix_version']}`",
        f"- **Source Baseline Commit**: `{packet['source_baseline_commit']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        f"- **Next Required Gate**: `{packet['next_required_gate']}`",
        "",
        "## Invariant Validation Safety Flags",
        "",
        "| Invariant Flag | Required State | Status |",
        "|---|---|---|",
    ]

    for k, v in safety.items():
        lines.append(f"| `{k}` | `{v}` | ✅ |")

    lines.extend([
        "",
        "## Approval Packet Stubs",
        "",
    ])

    for s in stubs:
        evidence_uris = "; ".join([e["reference_uri"] for e in s["evidence_refs"]])
        placeholders_str = ", ".join([f"{k}: {v}" for k, v in s["operator_placeholders"].items()])
        lines.extend([
            f"### Approval Stub: `{s['approval_packet_id']}`",
            "",
            f"- **Source Draft Packet ID**: `{s['source_draft_packet_id']}`",
            f"- **Source Brief ID**: `{s['source_brief_id']}`",
            f"- **Source Candidate ID**: `{s['source_candidate_id']}`",
            f"- **Gate Status**: `{s['gate_status']}`",
            f"- **Approval Status**: `{s['approval_status']}`",
            f"- **Operator Approval Required**: `{s['operator_approval_required']}`",
            f"- **Manual Evidence Required**: `{s['manual_evidence_required']}`",
            f"- **Public Postable**: `{s['public_postable']}`",
            f"- **Dispatch Ready**: `{s['dispatch_ready']}`",
            f"- **Platform Payload Allowed**: `{s['platform_payload_allowed']}`",
            f"- **Platform Payload Created**: `{s['platform_payload_created']}`",
            f"- **Human Review Required**: `{s['human_review_required']}`",
            f"- **DQR Status**: `{s['dqr_status']}`",
            f"- **Readiness Status**: `{s['readiness_status']}`",
            f"- **Current Truth Status**: `{s['current_truth_status']}`",
            f"- **Claim Ledger Status**: `{s['claim_ledger_status']}`",
            f"- **Citation Requirement Status**: `{s['citation_requirement_status']}`",
            f"- **Limitation Block Status**: `{s['limitation_block_status']}`",
            f"- **Missing Proofs**: `{', '.join(s['missing_proofs'])}`",
            f"- **Blocked Reasons**: `{', '.join(s['blocked_reasons']) or 'none'}`",
            f"- **Operator Placeholders**: `{placeholders_str}`",
            f"- **Evidence Refs**: `{evidence_uris}`",
            f"- **Stub Hash**: `{s['packet_hash']}`",
            "",
        ])

    lines.extend([
        "## Draft Approval Gate Decisions",
        "",
        "| Candidate ID | Decision ID | Gate Status | Blocked Reasons | Next Required Gate |",
        "|---|---|---|---|---|",
    ])

    for d in decisions:
        reasons = ", ".join(d["blocked_reasons"])
        lines.append(f"| `{d['source_candidate_id']}` | `{d['decision_id']}` | `{d['gate_status']}` | `{reasons}` | `{d['next_required_gate']}` |")

    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AL")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
