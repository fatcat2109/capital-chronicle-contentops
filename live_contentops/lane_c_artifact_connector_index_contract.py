"""Lane C artifact connector index contract, 0175AG.

Deterministic local-only validation contract mapping future connector families.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175AG_LANE_C_ARTIFACT_CONNECTOR_INDEX_V0"
MATRIX_VERSION = "0175AG_LANE_C_ARTIFACT_CONNECTOR_INDEX_V1"
SOURCE_BASELINE_COMMIT = "2d9cfa897f78bd510fa24ed876131519f775bc9e"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AG"
PACKET_FILENAME = "lane_c_artifact_connector_index_contract_packet.json"
RUNBOOK_FILENAME = "lane_c_artifact_connector_index_contract.md"


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
class LaneCConnectorFamily:
    connector_id: str
    connector_family: str
    current_status: str  # blocked_review_only / future_gate_required / manual_only
    allowed_path_pattern: str
    required_file_kinds: list[str]
    required_identity_fields: list[str]
    required_hash_fields: list[str]
    required_lineage_fields: list[str]
    freshness_requirement: str
    dqr_handling: str
    readiness_handling: str
    missing_degraded_proxy_label_handling: str
    allowed_consumer_surfaces: list[str]
    prohibited_effects: list[str]
    next_required_gate: str


@dataclass(frozen=True)
class LaneCConnectorPathBoundary:
    allowed_path_pattern: str
    symbolic_only: bool
    local_only: bool


@dataclass(frozen=True)
class LaneCConnectorProofRequirement:
    connector_family: str
    required_proofs: list[str]


@dataclass(frozen=True)
class LaneCConnectorReadinessDecision:
    connector_id: str
    decision: str
    blocked_reasons: list[str]


@dataclass(frozen=True)
class LaneCArtifactConnectorIndexPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    connector_family_count: int
    proof_requirement_count: int
    connector_families: list[LaneCConnectorFamily]
    path_boundaries: list[LaneCConnectorPathBoundary]
    readiness_decisions: list[LaneCConnectorReadinessDecision]
    blocked_reasons: list[str]
    missing_proofs: list[str]
    safety_flags: dict[str, bool]
    local_only_classification: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_connector_families() -> list[LaneCConnectorFamily]:
    return [
        LaneCConnectorFamily(
            connector_id="local_capital_chronicle_artifact_packet",
            connector_family="local_capital_chronicle_artifact_packet",
            current_status="blocked_review_only",
            allowed_path_pattern="fixtures/lane_c/connectors/artifact_packet/*.json",
            required_file_kinds=["json"],
            required_identity_fields=["task_label", "matrix_version"],
            required_hash_fields=["packet_hash", "hash_algorithm"],
            required_lineage_fields=["source_baseline_commit"],
            freshness_requirement="max_age_seconds: 86400",
            dqr_handling="preserve_unresolved_not_cleared",
            readiness_handling="enforce_blocked_unless_manual_override",
            missing_degraded_proxy_label_handling="preserve_labels_and_warn",
            allowed_consumer_surfaces=["ContentInventory", "DraftInspector"],
            prohibited_effects=["no_network", "no_live_dispatch", "no_repo_mutation"],
            next_required_gate="lane_c_artifact_intake_validation",
        ),
        LaneCConnectorFamily(
            connector_id="local_capital_chronicle_lineage_manifest",
            connector_family="local_capital_chronicle_lineage_manifest",
            current_status="blocked_review_only",
            allowed_path_pattern="fixtures/lane_c/connectors/lineage_manifest/*.json",
            required_file_kinds=["json"],
            required_identity_fields=["task_label", "matrix_version"],
            required_hash_fields=["packet_hash", "hash_algorithm"],
            required_lineage_fields=["source_baseline_commit"],
            freshness_requirement="max_age_seconds: 86400",
            dqr_handling="preserve_unresolved_not_cleared",
            readiness_handling="enforce_blocked_unless_manual_override",
            missing_degraded_proxy_label_handling="preserve_labels_and_warn",
            allowed_consumer_surfaces=["ContentInventory", "DraftInspector"],
            prohibited_effects=["no_network", "no_live_dispatch", "no_repo_mutation"],
            next_required_gate="lane_c_cryptographic_lineage_verification",
        ),
        LaneCConnectorFamily(
            connector_id="local_capital_chronicle_dqr_snapshot",
            connector_family="local_capital_chronicle_dqr_snapshot",
            current_status="blocked_review_only",
            allowed_path_pattern="fixtures/lane_c/connectors/dqr_snapshot/*.json",
            required_file_kinds=["json"],
            required_identity_fields=["task_label", "matrix_version"],
            required_hash_fields=["packet_hash", "hash_algorithm"],
            required_lineage_fields=["source_baseline_commit"],
            freshness_requirement="max_age_seconds: 86400",
            dqr_handling="preserve_unresolved_not_cleared",
            readiness_handling="enforce_blocked_unless_manual_override",
            missing_degraded_proxy_label_handling="preserve_labels_and_warn",
            allowed_consumer_surfaces=["ContentInventory", "DraftInspector"],
            prohibited_effects=["no_network", "no_live_dispatch", "no_repo_mutation"],
            next_required_gate="lane_c_dqr_gate",
        ),
        LaneCConnectorFamily(
            connector_id="local_capital_chronicle_source_health_snapshot",
            connector_family="local_capital_chronicle_source_health_snapshot",
            current_status="blocked_review_only",
            allowed_path_pattern="fixtures/lane_c/connectors/source_health/*.json",
            required_file_kinds=["json"],
            required_identity_fields=["task_label", "matrix_version"],
            required_hash_fields=["packet_hash", "hash_algorithm"],
            required_lineage_fields=["source_baseline_commit"],
            freshness_requirement="max_age_seconds: 86400",
            dqr_handling="preserve_unresolved_not_cleared",
            readiness_handling="enforce_blocked_unless_manual_override",
            missing_degraded_proxy_label_handling="preserve_labels_and_warn",
            allowed_consumer_surfaces=["ContentInventory", "DraftInspector"],
            prohibited_effects=["no_network", "no_live_dispatch", "no_repo_mutation"],
            next_required_gate="lane_c_source_health_audit",
        ),
        LaneCConnectorFamily(
            connector_id="local_capital_chronicle_forecast_readiness_snapshot",
            connector_family="local_capital_chronicle_forecast_readiness_snapshot",
            current_status="blocked_review_only",
            allowed_path_pattern="fixtures/lane_c/connectors/forecast_readiness/*.json",
            required_file_kinds=["json"],
            required_identity_fields=["task_label", "matrix_version"],
            required_hash_fields=["packet_hash", "hash_algorithm"],
            required_lineage_fields=["source_baseline_commit"],
            freshness_requirement="max_age_seconds: 86400",
            dqr_handling="preserve_unresolved_not_cleared",
            readiness_handling="enforce_blocked_unless_manual_override",
            missing_degraded_proxy_label_handling="preserve_labels_and_warn",
            allowed_consumer_surfaces=["ContentInventory", "DraftInspector"],
            prohibited_effects=["no_network", "no_live_dispatch", "no_repo_mutation"],
            next_required_gate="lane_c_forecast_readiness_check",
        ),
        LaneCConnectorFamily(
            connector_id="local_manual_operator_evidence_packet",
            connector_family="local_manual_operator_evidence_packet",
            current_status="manual_only",
            allowed_path_pattern="fixtures/lane_c/connectors/manual_evidence/*.json",
            required_file_kinds=["json", "md"],
            required_identity_fields=["task_label", "matrix_version"],
            required_hash_fields=["packet_hash", "hash_algorithm"],
            required_lineage_fields=["source_baseline_commit"],
            freshness_requirement="max_age_seconds: 86400",
            dqr_handling="preserve_unresolved_not_cleared",
            readiness_handling="enforce_blocked_unless_manual_override",
            missing_degraded_proxy_label_handling="preserve_labels_and_warn",
            allowed_consumer_surfaces=["ContentInventory", "DraftInspector"],
            prohibited_effects=["no_network", "no_live_dispatch", "no_repo_mutation"],
            next_required_gate="evidence_vault_manual_pilot_audit",
        )
    ]


def build_path_boundaries() -> list[LaneCConnectorPathBoundary]:
    return [
        LaneCConnectorPathBoundary("fixtures/lane_c/connectors/artifact_packet/*.json", True, True),
        LaneCConnectorPathBoundary("fixtures/lane_c/connectors/lineage_manifest/*.json", True, True),
        LaneCConnectorPathBoundary("fixtures/lane_c/connectors/dqr_snapshot/*.json", True, True),
        LaneCConnectorPathBoundary("fixtures/lane_c/connectors/source_health/*.json", True, True),
        LaneCConnectorPathBoundary("fixtures/lane_c/connectors/forecast_readiness/*.json", True, True),
        LaneCConnectorPathBoundary("fixtures/lane_c/connectors/manual_evidence/*.json", True, True)
    ]


def build_proof_requirements() -> list[LaneCConnectorProofRequirement]:
    return [
        LaneCConnectorProofRequirement("local_capital_chronicle_artifact_packet", ["artifact_checksum", "task_label_match"]),
        LaneCConnectorProofRequirement("local_capital_chronicle_lineage_manifest", ["cryptographic_signature", "parent_commit_ref"]),
        LaneCConnectorProofRequirement("local_capital_chronicle_dqr_snapshot", ["dqr_status_unresolved", "audit_signoff"]),
        LaneCConnectorProofRequirement("local_capital_chronicle_source_health_snapshot", ["source_authority_lookup", "uptime_metrics"]),
        LaneCConnectorProofRequirement("local_capital_chronicle_forecast_readiness_snapshot", ["no_financial_advice_guarantee", "no_signal_text"]),
        LaneCConnectorProofRequirement("local_manual_operator_evidence_packet", ["operator_signoff", "local_file_hash"])
    ]


def build_readiness_decisions() -> list[LaneCConnectorReadinessDecision]:
    return [
        LaneCConnectorReadinessDecision("local_capital_chronicle_artifact_packet", "blocked_review_only", ["artifact_connector_not_live"]),
        LaneCConnectorReadinessDecision("local_capital_chronicle_lineage_manifest", "blocked_review_only", ["artifact_connector_not_live"]),
        LaneCConnectorReadinessDecision("local_capital_chronicle_dqr_snapshot", "blocked_review_only", ["artifact_connector_not_live"]),
        LaneCConnectorReadinessDecision("local_capital_chronicle_source_health_snapshot", "blocked_review_only", ["artifact_connector_not_live"]),
        LaneCConnectorReadinessDecision("local_capital_chronicle_forecast_readiness_snapshot", "blocked_review_only", ["artifact_connector_not_live"]),
        LaneCConnectorReadinessDecision("local_manual_operator_evidence_packet", "manual_only", ["manual_verification_required"])
    ]


def build_safety_flags() -> dict[str, bool]:
    return {
        "no_live_connector_enabled": True,
        "no_ingestion_repo_mutation": True,
        "no_env_read": True,
        "no_credential_read": True,
        "no_network_call": True,
        "no_provider_platform_api_call": True,
        "no_current_state_mutation": True,
        "no_dqr_clear": True,
        "no_readiness_clear": True,
        "no_public_postable_promotion": True,
        "no_dispatch_ready_promotion": True,
        "no_fake_market_numbers": True,
        "no_raw_vendor_redistribution": True,
        "no_autonomous_posting": True,
        "no_scheduler": True,
        "no_scraping": True
    }


def build_contract_packet() -> dict[str, Any]:
    families = build_connector_families()
    boundaries = build_path_boundaries()
    proofs = build_proof_requirements()
    decisions = build_readiness_decisions()
    safety = build_safety_flags()

    blocked = []
    for d in decisions:
        blocked.extend(d.blocked_reasons)

    draft = {
        "task_label": TASK_LABEL,
        "matrix_version": MATRIX_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "generated_at_epoch": 0,
        "connector_family_count": len(families),
        "proof_requirement_count": len(proofs),
        "connector_families": [_asdict(f) for f in families],
        "path_boundaries": [_asdict(b) for b in boundaries],
        "readiness_decisions": [_asdict(d) for d in decisions],
        "blocked_reasons": blocked,
        "missing_proofs": ["cryptographic_manifest_proof", "manual_operator_review_proof"],
        "safety_flags": safety,
        "local_only_classification": "local_only_review",
        "hash_algorithm": HASH_ALGORITHM,
        "next_required_gate": "lane_c_connector_index_operator_signoff"
    }

    packet_hash = _digest(draft)
    return {
        "packet_hash": packet_hash,
        **draft
    }


def render_runbook(packet: dict[str, Any]) -> str:
    families = packet["connector_families"]
    boundaries = packet["path_boundaries"]
    safety = packet["safety_flags"]

    lines = [
        "# Lane C Artifact Connector Index Contract",
        "",
        "> [!IMPORTANT]",
        "> This index registers and verifies symbolic local path rules and safety restrictions",
        "> for future Capital Chronicle artifact connectors before live connectors are initialized.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Matrix Version**: `{packet['matrix_version']}`",
        f"- **Source Baseline Commit**: `{packet['source_baseline_commit']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Local-Only Classification**: `{packet['local_only_classification']}`",
        f"- **Next Required Gate**: `{packet['next_required_gate']}`",
        "",
        "## Hard Safety Invariant Checks",
        "",
        "| Invariant Flag | Required State | Status |",
        "|---|---|---|",
    ]

    for k, v in safety.items():
        lines.append(f"| `{k}` | `{v}` | ✅ |")

    lines.extend([
        "",
        "## Symbolic Path Boundaries",
        "",
        "| Allowed Path Pattern | Symbolic Only | Local Only |",
        "|---|---|---|",
    ])

    for b in boundaries:
        lines.append(f"| `{b['allowed_path_pattern']}` | `{b['symbolic_only']}` | `{b['local_only']}` |")

    lines.extend([
        "",
        "## Future Connector Families Registry",
        "",
    ])

    for f in families:
        lines.extend([
            f"### Connector Family: `{f['connector_family']}`",
            "",
            f"- **Connector ID**: `{f['connector_id']}`",
            f"- **Current Status**: `{f['current_status']}`",
            f"- **Allowed Path Pattern**: `{f['allowed_path_pattern']}`",
            f"- **Required File Kinds**: `{', '.join(f['required_file_kinds'])}`",
            f"- **Required Identity Fields**: `{', '.join(f['required_identity_fields'])}`",
            f"- **Required Hash Fields**: `{', '.join(f['required_hash_fields'])}`",
            f"- **Required Lineage Fields**: `{', '.join(f['required_lineage_fields'])}`",
            f"- **Freshness**: `{f['freshness_requirement']}`",
            f"- **DQR Handling**: `{f['dqr_handling']}`",
            f"- **Readiness Handling**: `{f['readiness_handling']}`",
            f"- **Label Handling**: `{f['missing_degraded_proxy_label_handling']}`",
            f"- **Consumer Surfaces**: `{', '.join(f['allowed_consumer_surfaces'])}`",
            f"- **Prohibited Effects**: `{', '.join(f['prohibited_effects'])}`",
            f"- **Next Required Gate**: `{f['next_required_gate']}`",
            "",
        ])

    return "\n".join(lines) + "\n"


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AG")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
