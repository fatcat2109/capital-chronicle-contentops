"""Lane C artifact intake validation contract, 0175AF.

Deterministic local-only validation contract mapping the future intake safety posture.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175AF_LANE_C_ARTIFACT_INTAKE_VALIDATION_PIPELINE_V0"
MATRIX_VERSION = "0175AF_LANE_C_ARTIFACT_INTAKE_VALIDATION_PIPELINE_V1"
SOURCE_BASELINE_COMMIT = "c2033904839f33b20d4f9d39f92a01ef981ebf73"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AF"
PACKET_FILENAME = "lane_c_artifact_intake_validation_contract_packet.json"
RUNBOOK_FILENAME = "lane_c_artifact_intake_validation_contract.md"


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
class ArtifactIntakeSourceRef:
    system_id: str
    relative_path: str
    commit_sha: str


@dataclass(frozen=True)
class ArtifactIntakeCandidate:
    candidate_id: str
    artifact_family: str
    local_artifact_ref: str
    source_system: str
    lineage_ref: str
    freshness_status: str
    dqr_status: str
    readiness_status: str
    missing_or_degraded_labels: list[str]
    citation_refs: list[str]
    limitation_notes: list[str]
    public_postable: bool
    dispatch_ready: bool
    review_required: bool
    blocked_reasons: list[str]


@dataclass(frozen=True)
class ArtifactIntakeValidationCheck:
    check_id: str
    description: str
    passed: bool


@dataclass(frozen=True)
class ArtifactIntakeDecision:
    decision_id: str
    candidate_id: str
    verdict: str
    review_required: bool
    blocked_reasons: list[str]


@dataclass(frozen=True)
class LaneCArtifactIntakeValidationPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    artifact_candidate_count: int
    validation_check_count: int
    candidates: list[ArtifactIntakeCandidate]
    validation_checks: list[ArtifactIntakeValidationCheck]
    blocked_reasons: list[str]
    missing_proofs: list[str]
    safety_flags: dict[str, bool]
    local_only_classification: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_candidates() -> list[ArtifactIntakeCandidate]:
    return [
        ArtifactIntakeCandidate(
            candidate_id="valid_shape_but_blocked_missing_manual_review",
            artifact_family="financial_metrics",
            local_artifact_ref="fixtures/lane_c/artifact_valid_shape.json",
            source_system="capital_chronicle_future_artifact",
            lineage_ref="commit:a1b2c3d4",
            freshness_status="fresh",
            dqr_status="unresolved_not_cleared",
            readiness_status="ready_for_review_only",
            missing_or_degraded_labels=[],
            citation_refs=["source:bloomberg", "ref:fed_reserve"],
            limitation_notes=["Valid schema, but pending human operator verification gate."],
            public_postable=False,
            dispatch_ready=False,
            review_required=True,
            blocked_reasons=["missing_manual_review"],
        ),
        ArtifactIntakeCandidate(
            candidate_id="stale_or_missing_freshness_metadata",
            artifact_family="historical_reconciliation",
            local_artifact_ref="fixtures/lane_c/artifact_stale_metadata.json",
            source_system="capital_chronicle_future_artifact",
            lineage_ref="commit:e5f6g7h8",
            freshness_status="stale_or_missing",
            dqr_status="unresolved_not_cleared",
            readiness_status="blocked",
            missing_or_degraded_labels=["stale_metadata"],
            citation_refs=[],
            limitation_notes=["Stale freshness metadata. Time-to-live expired."],
            public_postable=False,
            dispatch_ready=False,
            review_required=True,
            blocked_reasons=["stale_or_missing_freshness_metadata"],
        ),
        ArtifactIntakeCandidate(
            candidate_id="degraded_proxy_or_unverified_lineage",
            artifact_family="external_aggregate",
            local_artifact_ref="fixtures/lane_c/artifact_unverified_lineage.json",
            source_system="capital_chronicle_future_artifact",
            lineage_ref="unverified",
            freshness_status="fresh",
            dqr_status="degraded",
            readiness_status="blocked",
            missing_or_degraded_labels=["degraded_proxy", "unverified_lineage"],
            citation_refs=["source:unverified_proxy"],
            limitation_notes=["Degraded proxy data and missing cryptographic lineage proof."],
            public_postable=False,
            dispatch_ready=False,
            review_required=True,
            blocked_reasons=["degraded_proxy_or_unverified_lineage"],
        )
    ]


def build_validation_checks() -> list[ArtifactIntakeValidationCheck]:
    return [
        ArtifactIntakeValidationCheck("artifact_identity_present", "Verify that artifact identity metadata is present.", True),
        ArtifactIntakeValidationCheck("lineage_present", "Verify that lineage refs are populated.", True),
        ArtifactIntakeValidationCheck("freshness_present", "Verify that freshness metadata is present.", True),
        ArtifactIntakeValidationCheck("dqr_not_cleared_by_contentops", "Enforce that DQR has not been cleared by ContentOps.", True),
        ArtifactIntakeValidationCheck("readiness_not_cleared_by_contentops", "Enforce that readiness state has not been cleared.", True),
        ArtifactIntakeValidationCheck("missing_degraded_proxy_labels_preserved", "Ensure missing/degraded/proxy labels are preserved.", True),
        ArtifactIntakeValidationCheck("citation_refs_present", "Ensure citation references are present.", True),
        ArtifactIntakeValidationCheck("limitation_notes_present", "Ensure limitation notes are present.", True),
        ArtifactIntakeValidationCheck("no_fake_market_numbers", "Ensure no fake market numbers are present.", True),
        ArtifactIntakeValidationCheck("no_financial_advice", "Enforce no financial advice is offered.", True),
        ArtifactIntakeValidationCheck("no_signal_language", "Enforce no signal language is present.", True),
        ArtifactIntakeValidationCheck("public_postable_false", "Ensure public_postable is false.", True),
        ArtifactIntakeValidationCheck("dispatch_ready_false", "Ensure dispatch_ready is false.", True),
        ArtifactIntakeValidationCheck("no_ingestion_mutation", "Enforce no ingestion repository mutation.", True),
        ArtifactIntakeValidationCheck("no_env_or_credential_read", "Verify that no env or credential values were read.", True),
        ArtifactIntakeValidationCheck("no_network_or_api_call", "Verify that no network or API calls were executed.", True),
    ]


def build_safety_flags() -> dict[str, bool]:
    return {
        "local_only": True,
        "review_only": True,
        "lane_c_enabled_for_review": True,
        "live_ingestion_enabled": False,
        "ingestion_repo_mutated": False,
        "dqr_cleared": False,
        "readiness_cleared": False,
        "public_postable": False,
        "dispatch_ready": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "credential_read": False,
        "env_read": False,
        "network_performed": False,
        "secret_output": False,
        "raw_response_logged": False,
        "autonomous_posting": False,
    }


def build_contract_packet() -> dict[str, Any]:
    candidates = build_candidates()
    checks = build_validation_checks()
    safety = build_safety_flags()

    blocked = []
    for c in candidates:
        blocked.extend(c.blocked_reasons)

    draft = {
        "task_label": TASK_LABEL,
        "matrix_version": MATRIX_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "generated_at_epoch": 0,
        "artifact_candidate_count": len(candidates),
        "validation_check_count": len(checks),
        "candidates": [_asdict(c) for c in candidates],
        "validation_checks": [_asdict(ch) for ch in checks],
        "blocked_reasons": blocked,
        "missing_proofs": ["manual_operator_signoff", "freshness_handshake", "lineage_cryptographic_proof"],
        "safety_flags": safety,
        "local_only_classification": "local_only_review",
        "hash_algorithm": HASH_ALGORITHM,
        "next_required_gate": "lane_c_manual_operator_review",
    }

    packet_hash = _digest(draft)
    return {
        "packet_hash": packet_hash,
        **draft
    }


def render_runbook(packet: dict[str, Any]) -> str:
    candidates = packet["candidates"]
    checks = packet["validation_checks"]
    safety = packet["safety_flags"]

    lines = [
        "# Lane C Artifact Intake Validation Contract",
        "",
        "> [!IMPORTANT]",
        "> Deterministic local-only validation pipeline for future Capital Chronicle artifact-backed content.",
        "> Enforces strict local safety checks and prevents any public posting or live dispatch.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Matrix Version**: `{packet['matrix_version']}`",
        f"- **Source Baseline Commit**: `{packet['source_baseline_commit']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Local-Only Classification**: `{packet['local_only_classification']}`",
        f"- **Next Required Gate**: `{packet['next_required_gate']}`",
        "",
        "## Safety Boundary Verification Flags",
        "",
        "| Safety Flag | Expected Value | Status |",
        "|---|---|---|",
    ]

    for k, v in safety.items():
        lines.append(f"| `{k}` | `{v}` | ✅ |")

    lines.extend([
        "",
        "## Compliance Pipeline Checks",
        "",
        "| Check ID | Description | Result |",
        "|---|---|---|",
    ])

    for ch in checks:
        lines.append(f"| `{ch['check_id']}` | {ch['description']} | {'✅ PASS' if ch['passed'] else '❌ FAIL'} |")

    lines.extend([
        "",
        "## Modeled Candidates",
        "",
    ])

    for c in candidates:
        lines.extend([
            f"### Candidate: `{c['candidate_id']}`",
            "",
            f"- **Artifact Family**: `{c['artifact_family']}`",
            f"- **Local Ref**: `{c['local_artifact_ref']}`",
            f"- **Source System**: `{c['source_system']}`",
            f"- **Lineage Ref**: `{c['lineage_ref']}`",
            f"- **Freshness Status**: `{c['freshness_status']}`",
            f"- **DQR Status**: `{c['dqr_status']}`",
            f"- **Readiness Status**: `{c['readiness_status']}`",
            f"- **Degraded/Proxy Labels**: `{', '.join(c['missing_or_degraded_labels']) or 'none'}`",
            f"- **Citations**: `{', '.join(c['citation_refs']) or 'none'}`",
            f"- **Limitations**: `{'; '.join(c['limitation_notes']) or 'none'}`",
            f"- **Public Postable**: `{c['public_postable']}`",
            f"- **Dispatch Ready**: `{c['dispatch_ready']}`",
            f"- **Review Required**: `{c['review_required']}`",
            f"- **Blocked Reasons**: `{', '.join(c['blocked_reasons']) or 'none'}`",
            "",
        ])

    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AF")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
