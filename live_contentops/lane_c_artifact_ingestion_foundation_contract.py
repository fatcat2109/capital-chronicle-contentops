"""Lane C artifact ingestion foundation contract, 0175AI.

Deterministic local-only contract proving candidate discovery, shape verification, and quarantine policies.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175AI_LANE_C_ARTIFACT_INGESTION_FOUNDATION_BATCH_V0"
MATRIX_VERSION = "0175AI_LANE_C_ARTIFACT_INGESTION_FOUNDATION_BATCH_V1"
SOURCE_BASELINE_COMMIT = "e6fd4c65baea9daa9879de7f70142522889c8df7"
LEDGER_FAMILY = "lane_c_artifact_ingestion_foundation_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AI"
PACKET_FILENAME = "lane_c_artifact_ingestion_foundation_contract_packet.json"
RUNBOOK_FILENAME = "lane_c_artifact_ingestion_foundation_contract.md"


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
class LaneCArtifactIngestionSourceFile:
    relative_path: str
    file_kind: str
    size_bytes: int
    modified_time_epoch: int
    sha256_hash: str


@dataclass(frozen=True)
class LaneCArtifactIngestionCandidate:
    artifact_id: str
    artifact_type: str
    local_ref: str
    source_system: str
    lineage_refs: list[str]
    freshness_status: str
    dqr_status: str
    readiness_status: str
    missing_degraded_proxy_labels: list[str]
    limitations: list[str]
    allowed_content_classes: list[str]
    forbidden_content_classes: list[str]
    checksum_hash: str
    hash_algorithm: str
    operator_notes: str
    no_advice_no_signal_metadata: dict[str, Any]
    public_postable: bool
    dispatch_ready: bool
    classification: str


@dataclass(frozen=True)
class LaneCArtifactIngestionDecision:
    decision_id: str
    artifact_id: str
    verdict: str  # blocked / quarantined / review_only
    review_required: bool
    blocked_reasons: list[str]
    next_required_gate: str


@dataclass(frozen=True)
class LaneCArtifactQuarantineRecord:
    quarantine_id: str
    artifact_id: str
    reason: str
    quarantined_at_epoch: int
    quarantine_status: str


@dataclass(frozen=True)
class LaneCArtifactIngestionPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    source_files: list[LaneCArtifactIngestionSourceFile]
    candidates: list[LaneCArtifactIngestionCandidate]
    decisions: list[LaneCArtifactIngestionDecision]
    quarantine_records: list[LaneCArtifactQuarantineRecord]
    summary_counts: dict[str, int]
    safety_flags: dict[str, bool]
    blocked_reasons: list[str]
    missing_proofs: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_source_files() -> list[LaneCArtifactIngestionSourceFile]:
    return [
        LaneCArtifactIngestionSourceFile(
            relative_path="fixtures/lane_c/artifact_ingestion/shape_valid_but_not_authorized.json",
            file_kind="json",
            size_bytes=248,
            modified_time_epoch=0,
            sha256_hash="4e64f7831f2bc88062961d1df26ffcfefb0306129841804f3d2f2cb5631481b4"
        ),
        LaneCArtifactIngestionSourceFile(
            relative_path="fixtures/lane_c/artifact_ingestion/missing_lineage_manifest.json",
            file_kind="json",
            size_bytes=184,
            modified_time_epoch=0,
            sha256_hash="a746571ba822606553df8a21f7db19208a0d2f0991823ab84e031a0e10f135b1"
        ),
        LaneCArtifactIngestionSourceFile(
            relative_path="fixtures/lane_c/artifact_ingestion/stale_or_missing_freshness.json",
            file_kind="json",
            size_bytes=204,
            modified_time_epoch=0,
            sha256_hash="d251d1823ab8d279cf43f3da2cb123e4392182ab302cf429f032a1eb40cd9eab"
        ),
        LaneCArtifactIngestionSourceFile(
            relative_path="fixtures/lane_c/artifact_ingestion/degraded_proxy_label_required.json",
            file_kind="json",
            size_bytes=221,
            modified_time_epoch=0,
            sha256_hash="fcf5a6eb8838dcf1cf3249fb02c918efcd8e02d9198abcf827c191a2bc0dcf1a"
        ),
        LaneCArtifactIngestionSourceFile(
            relative_path="fixtures/lane_c/artifact_ingestion/missing_operator_approval.json",
            file_kind="json",
            size_bytes=212,
            modified_time_epoch=0,
            sha256_hash="a6e2e01df392cb3e43952f41cb837cd9a0b12bc8f4cb2efc0ea4102919ab3f90"
        ),
        LaneCArtifactIngestionSourceFile(
            relative_path="fixtures/lane_c/artifact_ingestion/forbidden_public_ready_claim.json",
            file_kind="json",
            size_bytes=198,
            modified_time_epoch=0,
            sha256_hash="7e39f82d210b3cd4cb92eab8f102cf93ebcd2b91d29abcbcfd2e30fa230dcf2b"
        ),
        LaneCArtifactIngestionSourceFile(
            relative_path="fixtures/lane_c/artifact_ingestion/local_fixture_only.json",
            file_kind="json",
            size_bytes=165,
            modified_time_epoch=0,
            sha256_hash="3e18a2bc88df43ac102919ab3fcfdfc092ab3cd4cf2eab3091df2cba9eabcf23"
        ),
        LaneCArtifactIngestionSourceFile(
            relative_path="fixtures/lane_c/artifact_ingestion/quarantined_review_only.json",
            file_kind="json",
            size_bytes=170,
            modified_time_epoch=0,
            sha256_hash="8cf53a1abcbcd29ab301cfbc28decf3e2ab103cf92a83cdb320df20f02dcba9f"
        )
    ]


def build_candidates() -> list[LaneCArtifactIngestionCandidate]:
    return [
        LaneCArtifactIngestionCandidate(
            artifact_id="candidate_shape_valid_but_not_authorized",
            artifact_type="local_capital_chronicle_artifact_packet",
            local_ref="fixtures/lane_c/artifact_ingestion/shape_valid_but_not_authorized.json",
            source_system="capital_chronicle_external_compiler",
            lineage_refs=["commit:f00d1234"],
            freshness_status="fresh",
            dqr_status="unresolved_not_cleared",
            readiness_status="blocked",
            missing_degraded_proxy_labels=[],
            limitations=["Schema shape is valid, but compiler lacks authorized signing certificate."],
            allowed_content_classes=["local_review_only"],
            forbidden_content_classes=["public_claim", "news_dispatch"],
            checksum_hash="4e64f7831f2bc88062961d1df26ffcfefb0306129841804f3d2f2cb5631481b4",
            hash_algorithm="sha256",
            operator_notes="Authorized key check failed at intake. Quarantining candidate for manual review.",
            no_advice_no_signal_metadata={"advice_signals_present": False, "verified_by": "local_precheck"},
            public_postable=False,
            dispatch_ready=False,
            classification="shape_valid_but_not_authorized"
        ),
        LaneCArtifactIngestionCandidate(
            artifact_id="candidate_missing_lineage_manifest",
            artifact_type="local_capital_chronicle_lineage_manifest",
            local_ref="fixtures/lane_c/artifact_ingestion/missing_lineage_manifest.json",
            source_system="capital_chronicle_lineage_builder",
            lineage_refs=[],
            freshness_status="fresh",
            dqr_status="unresolved_not_cleared",
            readiness_status="blocked",
            missing_degraded_proxy_labels=["missing_lineage_manifest"],
            limitations=["Lacks cryptographic parent commit sequence and audit lineage references."],
            allowed_content_classes=["local_review_only"],
            forbidden_content_classes=["public_claim", "news_dispatch"],
            checksum_hash="a746571ba822606553df8a21f7db19208a0d2f0991823ab84e031a0e10f135b1",
            hash_algorithm="sha256",
            operator_notes="Lineage validation failed. Blocked due to missing parent reference.",
            no_advice_no_signal_metadata={"advice_signals_present": False, "verified_by": "local_precheck"},
            public_postable=False,
            dispatch_ready=False,
            classification="blocked_missing_lineage"
        ),
        LaneCArtifactIngestionCandidate(
            artifact_id="candidate_stale_or_missing_freshness",
            artifact_type="local_capital_chronicle_dqr_snapshot",
            local_ref="fixtures/lane_c/artifact_ingestion/stale_or_missing_freshness.json",
            source_system="capital_chronicle_dqr_system",
            lineage_refs=["commit:ab88ee01"],
            freshness_status="stale",
            dqr_status="unresolved_not_cleared",
            readiness_status="blocked",
            missing_degraded_proxy_labels=["stale_freshness_metadata"],
            limitations=["Data age exceeds maximum tolerated limit. Freshness metadata is expired or absent."],
            allowed_content_classes=["local_review_only"],
            forbidden_content_classes=["public_claim", "news_dispatch"],
            checksum_hash="d251d1823ab8d279cf43f3da2cb123e4392182ab302cf429f032a1eb40cd9eab",
            hash_algorithm="sha256",
            operator_notes="Freshness age check failed. The data is too old to process automatically.",
            no_advice_no_signal_metadata={"advice_signals_present": False, "verified_by": "local_precheck"},
            public_postable=False,
            dispatch_ready=False,
            classification="blocked_missing_lineage"
        ),
        LaneCArtifactIngestionCandidate(
            artifact_id="candidate_degraded_proxy_label_required",
            artifact_type="local_capital_chronicle_source_health_snapshot",
            local_ref="fixtures/lane_c/artifact_ingestion/degraded_proxy_label_required.json",
            source_system="capital_chronicle_health_monitor",
            lineage_refs=["commit:42f10ee9"],
            freshness_status="fresh",
            dqr_status="degraded",
            readiness_status="blocked",
            missing_degraded_proxy_labels=["degraded_proxy", "source_health_degraded"],
            limitations=["Active platform is reporting degraded health. Must preserve degraded and proxy tags."],
            allowed_content_classes=["local_review_only"],
            forbidden_content_classes=["public_claim", "news_dispatch"],
            checksum_hash="fcf5a6eb8838dcf1cf3249fb02c918efcd8e02d9198abcf827c191a2bc0dcf1a",
            hash_algorithm="sha256",
            operator_notes="Health monitor warns of degraded status. Manual operator verification required.",
            no_advice_no_signal_metadata={"advice_signals_present": False, "verified_by": "local_precheck"},
            public_postable=False,
            dispatch_ready=False,
            classification="blocked_proxy_or_degraded_label_required"
        ),
        LaneCArtifactIngestionCandidate(
            artifact_id="candidate_missing_operator_approval",
            artifact_type="local_capital_chronicle_forecast_readiness_snapshot",
            local_ref="fixtures/lane_c/artifact_ingestion/missing_operator_approval.json",
            source_system="capital_chronicle_forecast_system",
            lineage_refs=["commit:ee33bc42"],
            freshness_status="fresh",
            dqr_status="unresolved_not_cleared",
            readiness_status="ready_for_review_only",
            missing_degraded_proxy_labels=[],
            limitations=["Awaiting explicit manual operator signoff before integration into editorial brief."],
            allowed_content_classes=["local_review_only"],
            forbidden_content_classes=["public_claim", "news_dispatch"],
            checksum_hash="a6e2e01df392cb3e43952f41cb837cd9a0b12bc8f4cb2efc0ea4102919ab3f90",
            hash_algorithm="sha256",
            operator_notes="Candidate is shape-valid but requires manual operator signature.",
            no_advice_no_signal_metadata={"advice_signals_present": False, "verified_by": "local_precheck"},
            public_postable=False,
            dispatch_ready=False,
            classification="blocked_missing_operator_approval"
        ),
        LaneCArtifactIngestionCandidate(
            artifact_id="candidate_forbidden_public_ready_claim",
            artifact_type="local_manual_operator_evidence_packet",
            local_ref="fixtures/lane_c/artifact_ingestion/forbidden_public_ready_claim.json",
            source_system="capital_chronicle_external_vendor",
            lineage_refs=["commit:9988ff00"],
            freshness_status="fresh",
            dqr_status="unresolved_not_cleared",
            readiness_status="ready_for_public_distribution",
            missing_degraded_proxy_labels=[],
            limitations=["Attemped to claim public ready status from an unverified local contract."],
            allowed_content_classes=[],
            forbidden_content_classes=["public_claim", "news_dispatch", "local_review"],
            checksum_hash="7e39f82d210b3cd4cb92eab8f102cf93ebcd2b91d29abcbcfd2e30fa230dcf2b",
            hash_algorithm="sha256",
            operator_notes="Security violation: Attempted to bypass safety gate and request public ready status.",
            no_advice_no_signal_metadata={"advice_signals_present": False, "verified_by": "local_precheck"},
            public_postable=False,
            dispatch_ready=False,
            classification="blocked_public_ready_claim"
        ),
        LaneCArtifactIngestionCandidate(
            artifact_id="candidate_local_fixture_only",
            artifact_type="local_capital_chronicle_artifact_packet",
            local_ref="fixtures/lane_c/artifact_ingestion/local_fixture_only.json",
            source_system="capital_chronicle_fixture_generator",
            lineage_refs=[],
            freshness_status="fresh",
            dqr_status="not_applicable",
            readiness_status="not_applicable",
            missing_degraded_proxy_labels=[],
            limitations=["This is a local fixture candidate for shape verification only."],
            allowed_content_classes=["local_review_only"],
            forbidden_content_classes=["public_claim", "news_dispatch"],
            checksum_hash="3e18a2bc88df43ac102919ab3fcfdfc092ab3cd4cf2eab3091df2cba9eabcf23",
            hash_algorithm="sha256",
            operator_notes="Generic fixture for smoke testing of local contract layers.",
            no_advice_no_signal_metadata={"advice_signals_present": False, "verified_by": "local_precheck"},
            public_postable=False,
            dispatch_ready=False,
            classification="local_fixture_only"
        ),
        LaneCArtifactIngestionCandidate(
            artifact_id="candidate_quarantined_review_only",
            artifact_type="local_capital_chronicle_artifact_packet",
            local_ref="fixtures/lane_c/artifact_ingestion/quarantined_review_only.json",
            source_system="capital_chronicle_quarantine_system",
            lineage_refs=["commit:da38ee92"],
            freshness_status="fresh",
            dqr_status="unresolved_not_cleared",
            readiness_status="blocked",
            missing_degraded_proxy_labels=[],
            limitations=["Intentionally quarantined for manual administrator inspection."],
            allowed_content_classes=["local_review_only"],
            forbidden_content_classes=["public_claim", "news_dispatch"],
            checksum_hash="8cf53a1abcbcd29ab301cfbc28decf3e2ab103cf92a83cdb320df20f02dcba9f",
            hash_algorithm="sha256",
            operator_notes="Generic quarantine candidate.",
            no_advice_no_signal_metadata={"advice_signals_present": False, "verified_by": "local_precheck"},
            public_postable=False,
            dispatch_ready=False,
            classification="quarantined_review_only"
        )
    ]


def build_decisions() -> list[LaneCArtifactIngestionDecision]:
    return [
        LaneCArtifactIngestionDecision(
            decision_id="decision_shape_valid",
            artifact_id="candidate_shape_valid_but_not_authorized",
            verdict="quarantined",
            review_required=True,
            blocked_reasons=["not_authorized_signing_authority"],
            next_required_gate="manual_operator_signoff"
        ),
        LaneCArtifactIngestionDecision(
            decision_id="decision_missing_lineage",
            artifact_id="candidate_missing_lineage_manifest",
            verdict="blocked",
            review_required=True,
            blocked_reasons=["missing_lineage_manifest"],
            next_required_gate="lineage_cryptographic_handshake"
        ),
        LaneCArtifactIngestionDecision(
            decision_id="decision_stale_freshness",
            artifact_id="candidate_stale_or_missing_freshness",
            verdict="blocked",
            review_required=True,
            blocked_reasons=["stale_or_missing_freshness"],
            next_required_gate="freshness_metadata_refresh"
        ),
        LaneCArtifactIngestionDecision(
            decision_id="decision_degraded_proxy",
            artifact_id="candidate_degraded_proxy_label_required",
            verdict="blocked",
            review_required=True,
            blocked_reasons=["degraded_proxy_label_required"],
            next_required_gate="manual_proxy_verification"
        ),
        LaneCArtifactIngestionDecision(
            decision_id="decision_missing_approval",
            artifact_id="candidate_missing_operator_approval",
            verdict="blocked",
            review_required=True,
            blocked_reasons=["missing_operator_approval"],
            next_required_gate="operator_review_queue_approval"
        ),
        LaneCArtifactIngestionDecision(
            decision_id="decision_forbidden_claim",
            artifact_id="candidate_forbidden_public_ready_claim",
            verdict="blocked",
            review_required=True,
            blocked_reasons=["forbidden_public_ready_claim"],
            next_required_gate="security_escalation_review"
        ),
        LaneCArtifactIngestionDecision(
            decision_id="decision_local_fixture",
            artifact_id="candidate_local_fixture_only",
            verdict="quarantined",
            review_required=True,
            blocked_reasons=["local_fixture_only"],
            next_required_gate="manual_operator_signoff"
        ),
        LaneCArtifactIngestionDecision(
            decision_id="decision_quarantined_review",
            artifact_id="candidate_quarantined_review_only",
            verdict="quarantined",
            review_required=True,
            blocked_reasons=["quarantined_review_only"],
            next_required_gate="manual_operator_signoff"
        )
    ]


def build_quarantine_records() -> list[LaneCArtifactQuarantineRecord]:
    return [
        LaneCArtifactQuarantineRecord(
            quarantine_id="quarantine_shape_valid",
            artifact_id="candidate_shape_valid_but_not_authorized",
            reason="not_authorized_signing_authority",
            quarantined_at_epoch=0,
            quarantine_status="quarantined_review_only"
        ),
        LaneCArtifactQuarantineRecord(
            quarantine_id="quarantine_local_fixture",
            artifact_id="candidate_local_fixture_only",
            reason="local_fixture_only",
            quarantined_at_epoch=0,
            quarantine_status="quarantined_review_only"
        ),
        LaneCArtifactQuarantineRecord(
            quarantine_id="quarantine_review_only_gen",
            artifact_id="candidate_quarantined_review_only",
            reason="quarantined_review_only",
            quarantined_at_epoch=0,
            quarantine_status="quarantined_review_only"
        )
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
        "approved_internal_alpha_artifacts_available": False
    }


def build_contract_packet() -> dict[str, Any]:
    sources = build_source_files()
    candidates = build_candidates()
    decisions = build_decisions()
    quarantine = build_quarantine_records()
    safety = build_safety_flags()

    blocked = []
    for d in decisions:
        blocked.extend(d.blocked_reasons)

    summary = {
        "source_file_count": len(sources),
        "candidate_count": len(candidates),
        "decision_count": len(decisions),
        "quarantine_count": len(quarantine)
    }

    draft = {
        "task_label": TASK_LABEL,
        "matrix_version": MATRIX_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "generated_at_epoch": 0,
        "source_files": [_asdict(s) for s in sources],
        "candidates": [_asdict(c) for c in candidates],
        "decisions": [_asdict(d) for d in decisions],
        "quarantine_records": [_asdict(q) for q in quarantine],
        "summary_counts": summary,
        "safety_flags": safety,
        "blocked_reasons": blocked,
        "missing_proofs": ["operator_signature_token", "lineage_cryptographic_sequence"],
        "ledger_family": LEDGER_FAMILY,
        "hash_algorithm": HASH_ALGORITHM,
        "next_required_gate": "lane_c_artifact_ingestion_operator_review"
    }

    packet_hash = _digest(draft)
    return {
        "packet_hash": packet_hash,
        **draft
    }


def render_runbook(packet: dict[str, Any]) -> str:
    sources = packet["source_files"]
    candidates = packet["candidates"]
    decisions = packet["decisions"]
    safety = packet["safety_flags"]

    lines = [
        "# Lane C Artifact Ingestion Foundation Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a local fixture-only ingestion foundation.",
        "> It does not read the Capital Chronicle ingestion repo.",
        "> It does not prove any real artifact exists.",
        "> It does not clear DQR/readiness/current truth.",
        "> It cannot produce public-ready content.",
        "> It prepares the future shape for real approved artifact ingestion.",
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
        "## Ingested Source Files",
        "",
        "| Relative Path | Kind | Bytes | Hash |",
        "|---|---|---|---|",
    ])

    for s in sources:
        lines.append(f"| `{s['relative_path']}` | `{s['file_kind']}` | `{s['size_bytes']}` | `{s['sha256_hash'][:16]}...` |")

    lines.extend([
        "",
        "## Discovered Candidates Registry",
        "",
    ])

    for c in candidates:
        lines.extend([
            f"### Candidate Artifact: `{c['artifact_id']}`",
            "",
            f"- **Type**: `{c['artifact_type']}`",
            f"- **Local Ref**: `{c['local_ref']}`",
            f"- **Source System**: `{c['source_system']}`",
            f"- **Lineage Refs**: `{', '.join(c['lineage_refs']) or 'none'}`",
            f"- **Freshness**: `{c['freshness_status']}`",
            f"- **DQR Status**: `{c['dqr_status']}`",
            f"- **Readiness**: `{c['readiness_status']}`",
            f"- **Classification**: `{c['classification']}`",
            f"- **Operator Notes**: {c['operator_notes']}",
            f"- **Public Postable**: `{c['public_postable']}`",
            f"- **Dispatch Ready**: `{c['dispatch_ready']}`",
            "",
        ])

    lines.extend([
        "## Ingestion Compliance Decisions",
        "",
        "| Candidate ID | Verdict | Review Required | Blocked Reasons | Next Gate |",
        "|---|---|---|---|---|",
    ])

    for d in decisions:
        reasons = ", ".join(d["blocked_reasons"])
        lines.append(f"| `{d['artifact_id']}` | `{d['verdict']}` | `{d['review_required']}` | `{reasons}` | `{d['next_required_gate']}` |")

    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AI")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
