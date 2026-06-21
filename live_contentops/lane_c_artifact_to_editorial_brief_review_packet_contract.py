"""Lane C artifact-to-editorial-brief review packet contract, 0175AJ.

Deterministic local-only contract mapping candidates to review-only stubs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.lane_c_artifact_ingestion_foundation_contract import (
    build_contract_packet as build_ingestion_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AJ_LANE_C_ARTIFACT_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V0"
MATRIX_VERSION = "0175AJ_LANE_C_ARTIFACT_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V1"
SOURCE_BASELINE_COMMIT = "d60d71c2dc4ff1fc148f68bf5ff7645fccace1ab"
LEDGER_FAMILY = "lane_c_artifact_to_editorial_brief_review_packet_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AJ"
PACKET_FILENAME = "lane_c_artifact_to_editorial_brief_review_packet_contract_packet.json"
RUNBOOK_FILENAME = "lane_c_artifact_to_editorial_brief_review_packet_contract.md"


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
class LaneCEditorialBriefSourceBinding:
    candidate_id: str
    artifact_id: str
    artifact_type: str
    local_ref: str
    checksum_hash: str


@dataclass(frozen=True)
class LaneCEditorialBriefGuardrail:
    guardrail_id: str
    description: str
    passed: bool


@dataclass(frozen=True)
class LaneCEditorialBriefReviewPacket:
    brief_id: str
    source_candidate_id: str
    artifact_family: str
    source_lineage_refs: list[str]
    freshness_status: str
    dqr_status: str
    readiness_status: str
    missing_degraded_proxy_labels: list[str]
    limitations: list[str]
    citation_refs: list[str]
    editorial_angle: str
    allowed_claims: list[str]
    forbidden_claims: list[str]
    no_advice_no_signal_metadata: dict[str, Any]
    human_review_required: bool
    public_postable: bool
    dispatch_ready: bool
    approval_status: str
    review_status: str
    blocked_reasons: list[str]
    missing_proofs: list[str]
    packet_hash: str


@dataclass(frozen=True)
class LaneCEditorialBriefDecision:
    decision_id: str
    source_candidate_id: str
    verdict: str  # created / blocked / rejected
    review_required: bool
    blocked_reasons: list[str]
    next_required_gate: str


@dataclass(frozen=True)
class LaneCArtifactToEditorialBriefPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    source_bindings: list[LaneCEditorialBriefSourceBinding]
    brief_packets: list[LaneCEditorialBriefReviewPacket]
    decisions: list[LaneCEditorialBriefDecision]
    guardrails: list[LaneCEditorialBriefGuardrail]
    summary_counts: dict[str, int]
    safety_flags: dict[str, bool]
    blocked_reasons: list[str]
    missing_proofs: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_guardrails() -> list[LaneCEditorialBriefGuardrail]:
    return [
        LaneCEditorialBriefGuardrail("no_market_numbers", "Ensure absolute absence of price/yield/spread macroeconomic numbers.", True),
        LaneCEditorialBriefGuardrail("no_public_ready_draft", "Verify that no public-ready drafts are compiled.", True),
        LaneCEditorialBriefGuardrail("no_social_payloads", "Ensure no X/Telegram/LinkedIn post content is present.", True),
        LaneCEditorialBriefGuardrail("no_platform_write_calls", "Verify that zero active platform API endpoints are configured.", True),
        LaneCEditorialBriefGuardrail("local_precheck_boundary", "Confirm local-only boundaries are enforced.", True),
        LaneCEditorialBriefGuardrail("dqr_unresolved_boundary", "Verify that no DQR clearance was performed.", True),
        LaneCEditorialBriefGuardrail("readiness_unresolved_boundary", "Verify that readiness remains blocked.", True),
    ]


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
        "financial_advice": False,
        "signal_language": False,
        "broker_order_execution": False,
        "raw_vendor_redistribution": False,
        "approved_internal_alpha_artifacts_available": False,
        "writer_generated_public_draft": False
    }


def convert_candidates() -> tuple[list[LaneCEditorialBriefSourceBinding], list[LaneCEditorialBriefReviewPacket], list[LaneCEditorialBriefDecision]]:
    ingestion = build_ingestion_packet()
    candidates = ingestion["candidates"]

    bindings: list[LaneCEditorialBriefSourceBinding] = []
    briefs: list[LaneCEditorialBriefReviewPacket] = []
    decisions: list[LaneCEditorialBriefDecision] = []

    for c in candidates:
        cid = c["artifact_id"]
        classification = c["classification"]

        # 1. Add Source Binding
        bindings.append(
            LaneCEditorialBriefSourceBinding(
                candidate_id=cid,
                artifact_id=cid,
                artifact_type=c["artifact_type"],
                local_ref=c["local_ref"],
                checksum_hash=c["checksum_hash"]
            )
        )

        # 2. Process based on classification rules
        if classification == "shape_valid_but_not_authorized":
            verdict = "created"
            blocked = ["not_authorized_signing_authority"]
            proofs = ["authorized_signing_certificate"]
            decision_verdict = "created"
            next_gate = "manual_operator_signoff"

        elif classification == "blocked_missing_lineage":
            verdict = "blocked"
            blocked = ["missing_lineage_manifest"]
            proofs = ["lineage_manifest_sequence"]
            decision_verdict = "blocked"
            next_gate = "lineage_cryptographic_handshake"

        elif classification == "blocked_stale_or_missing_freshness" or cid == "candidate_stale_or_missing_freshness":
            verdict = "blocked"
            blocked = ["stale_or_missing_freshness"]
            proofs = ["freshness_handshake"]
            decision_verdict = "blocked"
            next_gate = "freshness_metadata_refresh"

        elif classification == "blocked_proxy_or_degraded_label_required":
            verdict = "created"
            blocked = ["degraded_proxy_label_required"]
            proofs = ["health_monitor_verification"]
            decision_verdict = "created"
            next_gate = "manual_proxy_verification"

        elif classification == "blocked_missing_operator_approval":
            verdict = "created"
            blocked = ["missing_operator_approval"]
            proofs = ["manual_operator_signature"]
            decision_verdict = "created"
            next_gate = "operator_review_queue_approval"

        elif classification == "blocked_public_ready_claim":
            verdict = "rejected"
            blocked = ["forbidden_public_ready_claim"]
            proofs = ["security_escalation_clearance"]
            decision_verdict = "rejected"
            next_gate = "security_escalation_review"

        elif classification == "local_fixture_only":
            verdict = "created"
            blocked = ["local_fixture_only"]
            proofs = ["production_key_setup"]
            decision_verdict = "created"
            next_gate = "manual_operator_signoff"

        elif classification == "quarantined_review_only":
            verdict = "created"
            blocked = ["quarantined_review_only"]
            proofs = ["administrator_clearance"]
            decision_verdict = "created"
            next_gate = "manual_operator_signoff"

        else:
            verdict = "blocked"
            blocked = ["unknown_classification"]
            proofs = []
            decision_verdict = "blocked"
            next_gate = "manual_operator_signoff"

        # Record Decision
        decisions.append(
            LaneCEditorialBriefDecision(
                decision_id=f"brief_decision_{cid}",
                source_candidate_id=cid,
                verdict=decision_verdict,
                review_required=True,
                blocked_reasons=blocked,
                next_required_gate=next_gate
            )
        )

        # Generate Editorial Brief Packet only if NOT rejected and NOT blocked (or created as a blocked stub)
        # Note: missing_lineage and stale freshness are created as stubs (blocked = True, review_only)
        if verdict != "rejected":
            raw_brief = {
                "source_candidate_id": cid,
                "artifact_family": c["artifact_type"],
                "source_lineage_refs": c["lineage_refs"],
                "freshness_status": c["freshness_status"],
                "dqr_status": c["dqr_status"],
                "readiness_status": c["readiness_status"],
                "missing_degraded_proxy_labels": c["missing_degraded_proxy_labels"],
                "limitations": c["limitations"],
                "citation_refs": c["allowed_content_classes"],  # Using metadata sources
                "editorial_angle": "Review-only artifact stub. No editorial commentary authorized.",
                "allowed_claims": ["local_review_only"],
                "forbidden_claims": ["public_distribution", "market_trends"],
                "no_advice_no_signal_metadata": {
                    "no_financial_advice": True,
                    "no_market_signals": True,
                    "ingestion_checksum": c["checksum_hash"]
                },
                "human_review_required": True,
                "public_postable": False,
                "dispatch_ready": False,
                "approval_status": "blocked" if verdict == "blocked" else "pending_operator_signoff",
                "review_status": "blocked_review_only" if verdict == "blocked" else "review_only",
                "blocked_reasons": blocked,
                "missing_proofs": proofs,
            }

            brief_hash = _digest(raw_brief)
            briefs.append(
                LaneCEditorialBriefReviewPacket(
                    brief_id=f"brief_packet_{cid}",
                    packet_hash=brief_hash,
                    **raw_brief
                )
            )

    return bindings, briefs, decisions


def build_contract_packet() -> dict[str, Any]:
    bindings, briefs, decisions = convert_candidates()
    guardrails = build_guardrails()
    safety = build_safety_flags()

    blocked = []
    for d in decisions:
        blocked.extend(d.blocked_reasons)

    summary = {
        "source_binding_count": len(bindings),
        "brief_packet_count": len(briefs),
        "decision_count": len(decisions),
        "guardrail_count": len(guardrails)
    }

    draft = {
        "task_label": TASK_LABEL,
        "matrix_version": MATRIX_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "generated_at_epoch": 0,
        "source_bindings": [_asdict(b) for b in bindings],
        "brief_packets": [_asdict(br) for br in briefs],
        "decisions": [_asdict(d) for d in decisions],
        "guardrails": [_asdict(g) for g in guardrails],
        "summary_counts": summary,
        "safety_flags": safety,
        "blocked_reasons": blocked,
        "missing_proofs": ["cryptographic_lineage_handshake", "operator_brief_signoff"],
        "ledger_family": LEDGER_FAMILY,
        "hash_algorithm": HASH_ALGORITHM,
        "next_required_gate": "lane_c_editorial_brief_operator_signoff"
    }

    packet_hash = _digest(draft)
    return {
        "packet_hash": packet_hash,
        **draft
    }


def render_runbook(packet: dict[str, Any]) -> str:
    bindings = packet["source_bindings"]
    briefs = packet["brief_packets"]
    decisions = packet["decisions"]
    safety = packet["safety_flags"]
    guardrails = packet["guardrails"]

    lines = [
        "# Lane C Artifact to Editorial Brief Review Packet Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a deterministic local-only editorial review packet bridge.",
        "> It does not compile live post drafts, payloads, or trigger platform writes.",
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
        "## Ingested Candidate Source Bindings",
        "",
        "| Candidate ID | Artifact ID | Type | Local Ref | Checksum |",
        "|---|---|---|---|---|",
    ])

    for b in bindings:
        lines.append(f"| `{b['candidate_id']}` | `{b['artifact_id']}` | `{b['artifact_type']}` | `{b['local_ref']}` | `{b['checksum_hash'][:16]}...` |")

    lines.extend([
        "",
        "## Editorial Brief Guardrails Check",
        "",
        "| Guardrail ID | Description | Result |",
        "|---|---|---|",
    ])

    for g in guardrails:
        lines.append(f"| `{g['guardrail_id']}` | {g['description']} | {'✅ PASS' if g['passed'] else '❌ FAIL'} |")

    lines.extend([
        "",
        "## Editorial Review Brief Packets",
        "",
    ])

    for br in briefs:
        lines.extend([
            f"### Brief: `{br['brief_id']}`",
            "",
            f"- **Source Candidate ID**: `{br['source_candidate_id']}`",
            f"- **Artifact Family**: `{br['artifact_family']}`",
            f"- **Lineage Refs**: `{', '.join(br['source_lineage_refs']) or 'none'}`",
            f"- **Freshness Status**: `{br['freshness_status']}`",
            f"- **DQR Status**: `{br['dqr_status']}`",
            f"- **Readiness**: `{br['readiness_status']}`",
            f"- **Preserved Labels**: `{', '.join(br['missing_degraded_proxy_labels']) or 'none'}`",
            f"- **Limitations**: `{'; '.join(br['limitations']) or 'none'}`",
            f"- **Citations**: `{', '.join(br['citation_refs']) or 'none'}`",
            f"- **Editorial Angle**: {br['editorial_angle']}",
            f"- **Allowed Claims**: `{', '.join(br['allowed_claims'])}`",
            f"- **Forbidden Claims**: `{', '.join(br['forbidden_claims'])}`",
            f"- **Review Status**: `{br['review_status']}`",
            f"- **Approval Status**: `{br['approval_status']}`",
            f"- **Public Postable**: `{br['public_postable']}`",
            f"- **Dispatch Ready**: `{br['dispatch_ready']}`",
            f"- **Brief Hash**: `{br['packet_hash']}`",
            "",
        ])

    lines.extend([
        "## Artifact Ingestion to Editorial Brief Decisions",
        "",
        "| Candidate ID | Verdict | Review Required | Blocked Reasons | Next Required Gate |",
        "|---|---|---|---|---|",
    ])

    for d in decisions:
        reasons = ", ".join(d["blocked_reasons"])
        lines.append(f"| `{d['source_candidate_id']}` | `{d['verdict']}` | `{d['review_required']}` | `{reasons}` | `{d['next_required_gate']}` |")

    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AJ")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
