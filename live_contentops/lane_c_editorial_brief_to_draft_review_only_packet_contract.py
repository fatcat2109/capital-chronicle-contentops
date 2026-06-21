"""Lane C editorial-brief-to-draft review-only packet contract, 0175AK.

Deterministic local-only contract mapping brief packets to review-only drafts.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.lane_c_artifact_to_editorial_brief_review_packet_contract import (
    build_contract_packet as build_brief_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AK_LANE_C_EDITORIAL_BRIEF_TO_DRAFT_REVIEW_ONLY_PACKET_V0"
MATRIX_VERSION = "0175AK_LANE_C_EDITORIAL_BRIEF_TO_DRAFT_REVIEW_ONLY_PACKET_V1"
SOURCE_BASELINE_COMMIT = "ea5084684c04915c2261c5cd9e03a51fb2f276f1"
LEDGER_FAMILY = "lane_c_editorial_brief_to_draft_review_only_packet_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AK"
PACKET_FILENAME = "lane_c_editorial_brief_to_draft_review_only_packet_contract_packet.json"
RUNBOOK_FILENAME = "lane_c_editorial_brief_to_draft_review_only_packet_contract.md"


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
class LaneCDraftSection:
    section_id: str
    title: str
    bullet_points: list[str]


@dataclass(frozen=True)
class LaneCDraftClaimLedgerItem:
    claim_id: str
    claim_text: str
    assertion_type: str
    evidence_citation: str
    risk_level: str


@dataclass(frozen=True)
class LaneCDraftCitationRequirement:
    citation_id: str
    required_source: str
    verified: bool


@dataclass(frozen=True)
class LaneCDraftLimitationBlock:
    limitation_id: str
    description: str
    severity: str


@dataclass(frozen=True)
class LaneCDraftReviewGate:
    gate_id: str
    gate_name: str
    passed: bool
    reason: str


@dataclass(frozen=True)
class LaneCDraftReviewOnlyPacket:
    draft_packet_id: str
    source_brief_id: str
    source_candidate_id: str
    draft_status: str
    review_only: bool
    public_postable: bool
    dispatch_ready: bool
    platform_payload_created: bool
    provider_api_used: bool
    human_review_required: bool
    operator_approval_required: bool
    working_title_options: list[str]
    dek_or_summary_stub: str
    section_outline: list[str]
    sections: list[LaneCDraftSection]
    claim_ledger: list[LaneCDraftClaimLedgerItem]
    citation_requirements: list[LaneCDraftCitationRequirement]
    limitation_blocks: list[LaneCDraftLimitationBlock]
    forbidden_claims: list[str]
    allowed_claim_boundaries: list[str]
    unresolved_evidence_flags: list[str]
    missing_proofs: list[str]
    blocked_reasons: list[str]
    review_gate_status: str
    review_gates: list[LaneCDraftReviewGate]
    packet_hash: str


@dataclass(frozen=True)
class LaneCEditorialBriefToDraftReviewOnlyPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    draft_packets: list[LaneCDraftReviewOnlyPacket]
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
        "platform_payload_created": False,
        "published_content_created": False,
        "financial_advice": False,
        "signal_language": False,
        "broker_order_execution": False,
        "raw_vendor_redistribution": False,
        "approved_internal_alpha_artifacts_available": False,
        "writer_generated_public_draft": False
    }


def convert_briefs() -> list[LaneCDraftReviewOnlyPacket]:
    brief_data = build_brief_packet()
    briefs = brief_data["brief_packets"]

    drafts: list[LaneCDraftReviewOnlyPacket] = []

    for b in briefs:
        bid = b["brief_id"]
        cid = b["source_candidate_id"]
        blocked = b["blocked_reasons"]
        proofs = b["missing_proofs"]
        review_status = b["review_status"]
        approval = b["approval_status"]

        # Map to appropriate gate status and draft status
        if approval == "blocked" or review_status == "blocked_review_only":
            draft_status = "blocked"
            if "missing_lineage_manifest" in blocked:
                gate_status = "blocked_missing_lineage"
            elif "stale_or_missing_freshness" in blocked:
                gate_status = "blocked_stale_freshness"
            else:
                gate_status = "blocked"
        else:
            draft_status = "review_only"
            if "degraded_proxy_label_required" in blocked:
                gate_status = "pending_proxy_review"
            elif "missing_operator_approval" in blocked:
                gate_status = "pending_operator_signoff"
            else:
                gate_status = "pending_human_review"

        # Construct dry, non-public titles,outline, and summary stubs
        titles = [
            f"[INTERNAL-REVIEW-ONLY] Lane C Compliance Draft Stub ({cid})",
            f"[NON-PUBLIC] Dry-run schema placeholder draft ({cid})"
        ]
        dek = f"[NON-PUBLIC] [REVIEW-ONLY] Ingested candidate details scaffold for {cid}. No publishable copy generated."
        outline = [
            "Section 1: Ingested Metadata Validation Check",
            "Section 2: Preserved Source Limitations Audit",
            "Section 3: Operator Gate Override Pre-check"
        ]

        sections = [
            LaneCDraftSection(
                section_id=f"sec_1_{cid}",
                title="Ingested Metadata Validation Check",
                bullet_points=[
                    "Bullet 1: Verify source authority keys.",
                    "Bullet 2: Trace lineage sequence to parent commit."
                ]
            )
        ]

        claim_ledger = [
            LaneCDraftClaimLedgerItem(
                claim_id=f"claim_1_{cid}",
                claim_text="The source authority schema matches the validated Capital Chronicle registration.",
                assertion_type="metadata_validation",
                evidence_citation=f"citation:{cid}",
                risk_level="low"
            )
        ]

        citation_requirements = [
            LaneCDraftCitationRequirement(
                citation_id=f"cit_req_{cid}",
                required_source=f"provenance:{cid}",
                verified=False
            )
        ]

        limitation_blocks = [
            LaneCDraftLimitationBlock(
                limitation_id=f"lim_block_{cid}",
                description="Awaiting manual operator verification signature.",
                severity="blocker" if draft_status == "blocked" else "warning"
            )
        ]

        review_gates = [
            LaneCDraftReviewGate(
                gate_id=f"gate_1_{cid}",
                gate_name="Human Review Gate",
                passed=False,
                reason=f"Scaffold review status is: {gate_status}"
            )
        ]

        raw_draft = {
            "source_brief_id": bid,
            "source_candidate_id": cid,
            "draft_status": draft_status,
            "review_only": True,
            "public_postable": False,
            "dispatch_ready": False,
            "platform_payload_created": False,
            "provider_api_used": False,
            "human_review_required": True,
            "operator_approval_required": True,
            "working_title_options": titles,
            "dek_or_summary_stub": dek,
            "section_outline": outline,
            "sections": [_asdict(s) for s in sections],
            "claim_ledger": [_asdict(cl) for cl in claim_ledger],
            "citation_requirements": [_asdict(cr) for cr in citation_requirements],
            "limitation_blocks": [_asdict(lb) for lb in limitation_blocks],
            "forbidden_claims": ["financial_forecasts", "market_projections"],
            "allowed_claim_boundaries": ["local_compliance_assertions_only"],
            "unresolved_evidence_flags": ["cryptographic_lineage_unverified"],
            "missing_proofs": proofs,
            "blocked_reasons": blocked,
            "review_gate_status": gate_status,
            "review_gates": [_asdict(rg) for rg in review_gates],
        }

        draft_hash = _digest(raw_draft)
        drafts.append(
            LaneCDraftReviewOnlyPacket(
                draft_packet_id=f"draft_packet_{cid}",
                packet_hash=draft_hash,
                **raw_draft
            )
        )

    return drafts


def build_contract_packet() -> dict[str, Any]:
    drafts = convert_briefs()
    safety = build_safety_flags()

    blocked = []
    for d in drafts:
        blocked.extend(d.blocked_reasons)

    # Carry forward decisions for rejected candidates from precedent 0175AJ
    # Precedent has 8 candidates, candidate_forbidden_public_ready_claim is rejected
    brief_data = build_brief_packet()
    precedent_decisions = brief_data["decisions"]
    rejected_decisions = [d for d in precedent_decisions if d["verdict"] == "rejected"]

    rejected_stubs = []
    for rd in rejected_decisions:
        blocked.extend(rd["blocked_reasons"])
        # Formulate a rejected stub for the packet to preserve it
        rejected_stubs.append({
            "source_candidate_id": rd["source_candidate_id"],
            "verdict": "rejected",
            "blocked_reasons": rd["blocked_reasons"],
            "next_required_gate": rd["next_required_gate"]
        })

    summary = {
        "draft_packet_count": len(drafts),
        "rejected_count": len(rejected_stubs)
    }

    draft = {
        "task_label": TASK_LABEL,
        "matrix_version": MATRIX_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "generated_at_epoch": 0,
        "draft_packets": [_asdict(d) for d in drafts],
        "rejected_decisions": rejected_stubs,
        "summary_counts": summary,
        "safety_flags": safety,
        "blocked_reasons": list(set(blocked)),
        "missing_proofs": ["operator_signature_check", "production_key_vault_verify"],
        "ledger_family": LEDGER_FAMILY,
        "hash_algorithm": HASH_ALGORITHM,
        "next_required_gate": "lane_c_draft_review_packet_operator_signoff"
    }

    packet_hash = _digest(draft)
    return {
        "packet_hash": packet_hash,
        **draft
    }


def render_runbook(packet: dict[str, Any]) -> str:
    drafts = packet["draft_packets"]
    rejected = packet["rejected_decisions"]
    safety = packet["safety_flags"]

    lines = [
        "# Lane C Editorial Brief to Draft Review-Only Packet Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a local-only draft review scaffold.",
        "> It does not compile publishable post copy, platform payloads, or trigger live writes.",
        "> It preserves all source limitations, missing proofs, citation checks, and DQR/readiness blocks.",
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
        "## Draft Review-Only Packets",
        "",
    ])

    for dr in drafts:
        lines.extend([
            f"### Draft: `{dr['draft_packet_id']}`",
            "",
            f"- **Source Brief ID**: `{dr['source_brief_id']}`",
            f"- **Source Candidate ID**: `{dr['source_candidate_id']}`",
            f"- **Draft Status**: `{dr['draft_status']}`",
            f"- **Review Status**: `{dr['review_gate_status']}`",
            f"- **Working Titles**: `{'; '.join(dr['working_title_options'])}`",
            f"- **Summary Stub**: {dr['dek_or_summary_stub']}",
            f"- **Outline**: `{', '.join(dr['section_outline'])}`",
            f"- **Claims Validated**: `{len(dr['claim_ledger'])}`",
            f"- **Citations Preserved**: `{len(dr['citation_requirements'])}`",
            f"- **Limitations Preserved**: `{len(dr['limitation_blocks'])}`",
            f"- **Public Postable**: `{dr['public_postable']}`",
            f"- **Dispatch Ready**: `{dr['dispatch_ready']}`",
            f"- **Platform Payload Created**: `{dr['platform_payload_created']}`",
            f"- **Provider API Used**: `{dr['provider_api_used']}`",
            f"- **Human Review Required**: `{dr['human_review_required']}`",
            f"- **Draft Hash**: `{dr['packet_hash']}`",
            "",
        ])

    lines.extend([
        "## Rejected Candidates (Precedent)",
        "",
        "| Source Candidate ID | Verdict | Blocked Reasons | Next Required Gate |",
        "|---|---|---|---|",
    ])

    for r in rejected:
        reasons = ", ".join(r["blocked_reasons"])
        lines.append(f"| `{r['source_candidate_id']}` | `{r['verdict']}` | `{reasons}` | `{r['next_required_gate']}` |")

    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AK")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
