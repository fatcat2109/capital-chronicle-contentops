"""Platform Review Bundle Operator Decision Gate contract, 0175AQ.

Deterministic local-only contract defining disabled decision stubs and locks for operator reviews.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.platform_preview_dry_render_to_review_bundle_contract import (
    build_contract_packet as build_review_bundle_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AQ_PLATFORM_REVIEW_BUNDLE_OPERATOR_DECISION_GATE_V0"
MATRIX_VERSION = "0175AQ_PLATFORM_REVIEW_BUNDLE_OPERATOR_DECISION_GATE_V1"
SOURCE_BASELINE_COMMIT = "ab4a851ff60121cc3c3bdd85e25ed58c07aa9766"
LEDGER_FAMILY = "platform_review_bundle_operator_decision_gate_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AQ"
PACKET_FILENAME = "platform_review_bundle_operator_decision_gate_contract_packet.json"
RUNBOOK_FILENAME = "platform_review_bundle_operator_decision_gate_contract.md"


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
class PlatformOperatorDecisionOption:
    decision_option_id: str
    enabled: bool = False
    available_now: bool = False
    requires_future_gate: bool = True
    requires_operator_identity: bool = True
    requires_operator_signature: bool = True
    requires_payload_hash_lock: bool = True
    requires_citation_clearance: bool = True
    requires_limitation_ack: bool = True
    requires_dqr_readiness_review: bool = True


@dataclass(frozen=True)
class PlatformOperatorDecisionLock:
    lock_id: str
    description: str
    active: bool = True


@dataclass(frozen=True)
class PlatformOperatorDecisionEvidenceRequirement:
    requirement_id: str
    description: str
    satisfied: bool = False


@dataclass(frozen=True)
class PlatformOperatorDecisionGateRecord:
    decision_gate_id: str
    source_bundle_item_id: str
    source_render_id: str
    platform_target_id: str
    platform_family: str
    gate_status: str
    operator_review_required: bool
    manual_decision_required: bool
    operator_identity_status: str
    operator_signature_status: str
    payload_hash_lock_status: str
    citation_status: str
    limitation_status: str
    dqr_status: str
    readiness_status: str
    current_truth_status: str
    account_binding_status: str
    credential_gate_status: str
    export_gate_status: str
    dispatch_gate_status: str
    decision_options: list[PlatformOperatorDecisionOption]
    decision_locks: list[PlatformOperatorDecisionLock]
    evidence_requirements: list[PlatformOperatorDecisionEvidenceRequirement]
    blocked_reasons: list[str]
    missing_future_gates: list[str]
    packet_hash: str
    # Safety & Status Flags
    operator_identity_bound: bool = False
    operator_signature_present: bool = False
    payload_hash_locked: bool = False
    approval_granted: bool = False
    rejection_recorded: bool = False
    revision_requested: bool = False
    export_ready: bool = False
    dispatch_ready: bool = False
    public_postable: bool = False
    publishable_text: bool = False
    platform_ready: bool = False
    platform_payload_created: bool = False
    publishable_payload_created: bool = False
    account_binding_active: bool = False
    credential_values_loaded: bool = False
    platform_api_called: bool = False
    scheduler_enabled: bool = False
    approved_for_publication: bool = False


@dataclass(frozen=True)
class PlatformOperatorDecisionGatePacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    decision_gate_records: list[PlatformOperatorDecisionGateRecord]
    summary_counts: dict[str, int]
    safety_flags: dict[str, bool]
    blocked_capabilities: list[str]
    missing_future_gates: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_decision_options() -> list[PlatformOperatorDecisionOption]:
    options = [
        "approve_for_publication",
        "reject_bundle",
        "request_revision",
        "hold_for_more_evidence",
        "export_for_manual_publish",
        "dispatch_to_platform"
    ]
    return [
        PlatformOperatorDecisionOption(decision_option_id=opt)
        for opt in options
    ]


def build_decision_locks() -> list[PlatformOperatorDecisionLock]:
    locks = {
        "lock_no_operator_identity": "Operator identity is not bound to the session.",
        "lock_no_operator_signature": "Cryptographic approval signature is missing.",
        "lock_no_payload_hash_lock": "Payload hash lock is not verified.",
        "lock_unresolved_citations": "Citations are unresolved or pending verification.",
        "lock_unresolved_limitations": "Limitations acknowledgement is pending.",
        "lock_dqr_readiness_unresolved": "DQR audit and publish readiness checks are unresolved.",
        "lock_no_account_binding": "Platform account binding is inactive.",
        "lock_no_credential_gate": "Credential gate authentication is required but locked.",
        "lock_no_export_gate": "Export gate has not been cleared.",
        "lock_no_dispatch_gate": "Dispatch gate has not cleared the post."
    }
    return [
        PlatformOperatorDecisionLock(lock_id=lid, description=desc, active=True)
        for lid, desc in locks.items()
    ]


def build_evidence_requirements() -> list[PlatformOperatorDecisionEvidenceRequirement]:
    requirements = {
        "evidence_operator_identity_verified": "Verify operator identity matches key binding registry.",
        "evidence_approval_signature_verified": "Verify cryptographic approval signature matches operator key.",
        "evidence_payload_hash_lock_confirmed": "Verify payload hash lock matches draft variant snapshot.",
        "evidence_citation_clearance_verified": "Verify citation references are validated.",
        "evidence_limitation_ack_verified": "Verify limitation acknowledgement is logged."
    }
    return [
        PlatformOperatorDecisionEvidenceRequirement(requirement_id=rid, description=desc, satisfied=False)
        for rid, desc in requirements.items()
    ]


def build_safety_flags() -> dict[str, bool]:
    return {
        "local_only": True,
        "fixture_only": True,
        "schema_only": True,
        "decision_gate_only": True,
        "review_bundle_only": True,
        "network_performed": False,
        "env_read": False,
        "credential_values_loaded": False,
        "platform_api_called": False,
        "provider_api_called": False,
        "account_binding_active": False,
        "scheduler_enabled": False,
        "autonomous_posting": False,
        "autonomous_reply_or_dm": False,
        "scraping": False,
        "ingestion_repo_mutated": False,
        "dqr_cleared_by_contentops": False,
        "readiness_cleared_by_contentops": False,
        "current_truth_promoted": False,
        "public_postable": False,
        "dispatch_ready": False,
        "platform_payload_created": False,
        "publishable_payload_created": False,
        "export_ready": False,
        "approval_granted": False,
        "approved_for_publication": False,
        "operator_approval_granted": False,
        "operator_identity_bound": False,
        "operator_signature_present": False,
        "payload_hash_locked": False,
        "financial_advice": False,
        "signal_language": False,
        "broker_order_execution": False,
        "raw_vendor_redistribution": False,
        "approved_internal_alpha_artifacts_available": False,
        "publishable_text": False,
        "platform_ready": False,
    }


def build_contract_packet() -> dict[str, Any]:
    # Consume 0175AP review bundle precedent
    bundle_data = build_review_bundle_packet()
    bundle_items = bundle_data.get("bundle_items", [])

    options = build_decision_options()
    locks = build_decision_locks()
    lock_ids = [l.lock_id for l in locks]
    evidence_reqs = build_evidence_requirements()

    gate_records: list[PlatformOperatorDecisionGateRecord] = []

    for item in bundle_items:
        tid = item["platform_target_id"]
        family = item["platform_family"]

        raw_record = {
            "decision_gate_id": f"decision_gate_{tid}",
            "source_bundle_item_id": item["bundle_item_id"],
            "source_render_id": item["source_render_id"],
            "platform_target_id": tid,
            "platform_family": family,
            "gate_status": "decision_gate_blocked",
            "operator_review_required": True,
            "manual_decision_required": True,
            "operator_identity_status": "identity_required_but_unbound",
            "operator_signature_status": "signature_required_but_missing",
            "payload_hash_lock_status": item["payload_hash_lock_status"],
            "citation_status": item["citation_slot_status"],
            "limitation_status": item["limitation_slot_status"],
            "dqr_status": item["dqr_status"],
            "readiness_status": item["readiness_status"],
            "current_truth_status": item["current_truth_status"],
            "account_binding_status": item["account_binding_status"],
            "credential_gate_status": item["credential_gate_status"],
            "export_gate_status": "export_gate_required_but_locked",
            "dispatch_gate_status": item["dispatch_gate_status"],
            "decision_options": [_asdict(opt) for opt in options],
            "decision_locks": [_asdict(lk) for lk in locks],
            "evidence_requirements": [_asdict(er) for er in evidence_reqs],
            "blocked_reasons": lock_ids,
            "missing_future_gates": ["lane_c_platform_review_bundle_operator_decision_gate", "production_key_vault_decrypter", "live_operator_signature_vault"],
            # Safety / Status flags
            "operator_identity_bound": False,
            "operator_signature_present": False,
            "payload_hash_locked": False,
            "approval_granted": False,
            "rejection_recorded": False,
            "revision_requested": False,
            "export_ready": False,
            "dispatch_ready": False,
            "public_postable": False,
            "publishable_text": False,
            "platform_ready": False,
            "platform_payload_created": False,
            "publishable_payload_created": False,
            "account_binding_active": False,
            "credential_values_loaded": False,
            "platform_api_called": False,
            "scheduler_enabled": False,
            "approved_for_publication": False,
        }

        rec_hash = _digest(raw_record)
        gate_records.append(
            PlatformOperatorDecisionGateRecord(
                packet_hash=rec_hash,
                **raw_record
            )
        )

    safety = build_safety_flags()

    summary_counts = {
        "registered_gate_records_count": len(gate_records),
        "global_safety_flags_count": len(safety),
        "global_decision_options_count": len(options),
        "global_decision_locks_count": len(locks),
        "evidence_requirements_count": len(evidence_reqs)
    }

    blocked_caps = [
        "live_publishing_dispatch",
        "autonomous_reply_automation",
        "live_credential_hydration",
        "active_scheduler_triggers",
        "manual_review_export"
    ]

    missing_gates = [
        "lane_c_platform_review_bundle_operator_decision_gate",
        "production_key_vault_decrypter",
        "live_operator_signature_vault"
    ]

    packet = PlatformOperatorDecisionGatePacket(
        task_label=TASK_LABEL,
        matrix_version=MATRIX_VERSION,
        source_baseline_commit=SOURCE_BASELINE_COMMIT,
        generated_at_epoch=0,
        decision_gate_records=gate_records,
        summary_counts=summary_counts,
        safety_flags=safety,
        blocked_capabilities=blocked_caps,
        missing_future_gates=missing_gates,
        ledger_family=LEDGER_FAMILY,
        packet_hash="",
        hash_algorithm=HASH_ALGORITHM,
        next_required_gate="lane_c_platform_review_bundle_operator_decision_gate"
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
    records = packet["decision_gate_records"]
    counts = packet["summary_counts"]
    safety = packet["safety_flags"]
    blocked_caps = packet["blocked_capabilities"]
    missing_gates = packet["missing_future_gates"]

    lines = [
        "# Platform Review Bundle Operator Decision Gate Contract",
        "",
        "> [!IMPORTANT]",
        "> This is an operator decision gate contract report for schema validation only.",
        "> It creates disabled decision options and active locks only, and is not a review UI or approval system.",
        "> It cannot approve, reject, revise, export, publish, dispatch, schedule, or call any platform APIs.",
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
        "## Decision Gate Summary Counts",
        "",
        f"- **Registered Decision Gate Records**: `{counts['registered_gate_records_count']}`",
        f"- **Decision Options Configured**: `{counts['global_decision_options_count']}`",
        f"- **Decision Locks Enforced**: `{counts['global_decision_locks_count']}`",
        f"- **Evidence Requirements Defined**: `{counts['evidence_requirements_count']}`",
        "",
        "## Blocked Capabilities & Missing Gates",
        "",
        "### Blocked Capabilities",
    ])

    for bc in blocked_caps:
        lines.append(f"- `{bc}`")

    lines.extend([
        "",
        "### Missing Future Gates",
    ])

    for mg in missing_gates:
        lines.append(f"- `{mg}`")

    lines.extend([
        "",
        "## Platform Operator Decision Gate Records",
        "",
    ])

    for r in records:
        lines.extend([
            f"### Decision Gate: `{r['decision_gate_id']}`",
            "",
            f"- **Source Bundle Item ID**: `{r['source_bundle_item_id']}`",
            f"- **Source Render ID**: `{r['source_render_id']}`",
            f"- **Platform Target ID**: `{r['platform_target_id']}`",
            f"- **Platform Family**: `{r['platform_family']}`",
            f"- **Gate Status**: `{r['gate_status']}`",
            f"- **Operator Review Required**: `{r['operator_review_required']}`",
            f"- **Manual Decision Required**: `{r['manual_decision_required']}`",
            f"- **Operator Identity Status**: `{r['operator_identity_status']}`",
            f"- **Operator Signature Status**: `{r['operator_signature_status']}`",
            f"- **Payload Hash Lock**: `{r['payload_hash_lock_status']}`",
            f"- **Citation Status**: `{r['citation_status']}`",
            f"- **Limitation Status**: `{r['limitation_status']}`",
            f"- **DQR Status**: `{r['dqr_status']}`",
            f"- **Readiness Status**: `{r['readiness_status']}`",
            f"- **Current Truth Status**: `{r['current_truth_status']}`",
            f"- **Account Binding**: `{r['account_binding_status']}`",
            f"- **Credential Gate**: `{r['credential_gate_status']}`",
            f"- **Export Gate**: `{r['export_gate_status']}`",
            f"- **Dispatch Gate**: `{r['dispatch_gate_status']}`",
            "",
            "#### Safety Invariants Status",
            "",
            f"- **Operator Identity Bound**: `{r['operator_identity_bound']}`",
            f"- **Operator Signature Present**: `{r['operator_signature_present']}`",
            f"- **Payload Hash Locked**: `{r['payload_hash_locked']}`",
            f"- **Approval Granted**: `{r['approval_granted']}`",
            f"- **Rejection Recorded**: `{r['rejection_recorded']}`",
            f"- **Revision Requested**: `{r['revision_requested']}`",
            f"- **Export Ready**: `{r['export_ready']}`",
            f"- **Dispatch Ready**: `{r['dispatch_ready']}`",
            "",
            "#### Decision Options (Disabled)",
            "",
            "| Option ID | Enabled | Available Now | Requires Future Gate |",
            "|---|---|---|---|",
        ])

        for opt in r["decision_options"]:
            lines.append(
                f"| `{opt['decision_option_id']}` | `{opt['enabled']}` | `{opt['available_now']}` | `{opt['requires_future_gate']}` |"
            )

        lines.extend([
            "",
            "#### Decision Locks (Active)",
            "",
            "| Lock ID | Description | Active Status |",
            "|---|---|---|",
        ])

        for lk in r["decision_locks"]:
            lines.append(
                f"| `{lk['lock_id']}` | {lk['description']} | `{lk['active']}` |"
            )

        lines.extend([
            "",
            "#### Evidence Requirements (Pending)",
            "",
            "| Requirement ID | Description | Satisfied |",
            "|---|---|---|",
        ])

        for er in r["evidence_requirements"]:
            lines.append(
                f"| `{er['requirement_id']}` | {er['description']} | `{er['satisfied']}` |"
            )
        lines.append("")

    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AQ")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
