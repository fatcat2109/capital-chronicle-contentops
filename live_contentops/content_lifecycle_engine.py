"""Content Lifecycle Spine and Operator Review Read Model.

Part of TASK_CONTENTOPS_0175BE_CONTRACT_CHAIN_LIFECYCLE_SPINE_AND_OPERATOR_REVIEW_READ_MODEL_PRECHECK_V0.
This module consolidates the 16 content lifecycle stages into a single inspectable state engine.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_0175BE_CONTRACT_CHAIN_LIFECYCLE_SPINE_AND_OPERATOR_REVIEW_READ_MODEL_PRECHECK_V0"
MATRIX_VERSION = "0175BE_CONTENT_LIFECYCLE_SPINE_V1"
SOURCE_BASELINE_COMMIT = "158c85467dfd1877f43e3bdea78bb15dba051c05"
LEDGER_FAMILY = "content_lifecycle_spine_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175BE"
PACKET_FILENAME = "content_lifecycle_spine_operator_review_read_model_packet.json"
RUNBOOK_FILENAME = "content_lifecycle_spine_operator_review_read_model.md"


@dataclass(frozen=True)
class LifecycleStage:
    stage_id: str
    stage_order: int
    stage_name: str
    lifecycle_phase: str
    source_task_label: str
    source_module: str
    source_packet_path: str
    upstream_stage_ids: list[str]
    downstream_stage_ids: list[str]
    platform_scope: str
    evidence_refs: list[str]
    blocker_codes: list[str]
    required_future_gate: str | None
    state: str  # e.g., "COMPLETED", "PENDING", "BLOCKED"
    operator_action_required: bool
    public_postable: bool = False
    dispatch_ready: bool = False
    live_api_called: bool = False
    provider_api_called: bool = False
    env_read: bool = False
    credential_hydrated: bool = False
    scheduler_enabled: bool = False
    scraping_performed: bool = False
    autonomous_reply_or_dm_enabled: bool = False
    dqr_cleared_by_contentops: bool = False
    readiness_cleared_by_contentops: bool = False
    current_truth_promoted: bool = False


@dataclass(frozen=True)
class OperatorReviewSummary:
    total_stage_count: int
    blocked_stage_count: int
    dispatch_ready_count: int = 0
    public_postable_count: int = 0
    live_api_call_count: int = 0
    provider_api_call_count: int = 0
    credential_hydration_count: int = 0
    env_read_count: int = 0
    all_safety_locks_active: bool = True
    current_lifecycle_position: str = "artifact_or_brief_intake"
    next_blocker: str | None = None
    next_recommended_task: str = "TASK_CONTENTOPS_0175BF_OPERATOR_REVIEW_READ_MODEL_TO_V5_QUEUE_BINDING_V0"


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


def list_lifecycle_stages() -> list[LifecycleStage]:
    """Returns the canonical ordered list of the 16 content lifecycle stages."""
    return [
        LifecycleStage(
            stage_id="artifact_or_brief_intake",
            stage_order=1,
            stage_name="Artifact or Brief Intake",
            lifecycle_phase="Ingestion",
            source_task_label="TASK_CONTENTOPS_0175AF_LANE_C_ARTIFACT_INTAKE_VALIDATION_V0",
            source_module="live_contentops/lane_c_artifact_intake_validation_contract.py",
            source_packet_path="docs/automation/0175AF/lane_c_artifact_intake_validation_contract_packet.json",
            upstream_stage_ids=[],
            downstream_stage_ids=["content_intent"],
            platform_scope="all",
            evidence_refs=["lane_c_artifact_schema_check"],
            blocker_codes=[],
            required_future_gate=None,
            state="COMPLETED",
            operator_action_required=False,
        ),
        LifecycleStage(
            stage_id="content_intent",
            stage_order=2,
            stage_name="Content Intent Parser",
            lifecycle_phase="Ingestion",
            source_task_label="TASK_CONTENTOPS_0174U4_CONTENT_IDEA_INTAKE_V0",
            source_module="live_contentops/content_idea_intent_parser_contract.py",
            source_packet_path="docs/automation/0174U4/content_idea_intent_parser_contract_packet.json",
            upstream_stage_ids=["artifact_or_brief_intake"],
            downstream_stage_ids=["draft_or_render"],
            platform_scope="all",
            evidence_refs=["intent_parsed_stub"],
            blocker_codes=[],
            required_future_gate=None,
            state="COMPLETED",
            operator_action_required=False,
        ),
        LifecycleStage(
            stage_id="draft_or_render",
            stage_order=3,
            stage_name="Draft Composition and Platform Rendering",
            lifecycle_phase="Composition",
            source_task_label="TASK_CONTENTOPS_0174U5_EDITORIAL_BRIEF_AI_WRITER_V0",
            source_module="live_contentops/editorial_brief_ai_writer_output_contract.py",
            source_packet_path="docs/automation/0174U5/editorial_brief_ai_writer_output_contract_packet.json",
            upstream_stage_ids=["content_intent"],
            downstream_stage_ids=["operator_review_bundle"],
            platform_scope="all",
            evidence_refs=["draft_composed_stub"],
            blocker_codes=[],
            required_future_gate=None,
            state="COMPLETED",
            operator_action_required=False,
        ),
        LifecycleStage(
            stage_id="operator_review_bundle",
            stage_order=4,
            stage_name="Operator Review Queue Bundle Intake",
            lifecycle_phase="Review",
            source_task_label="TASK_CONTENTOPS_0174UY_V5_OPERATOR_REVIEW_QUEUE_V0",
            source_module="live_contentops/v5_operator_review_queue_manual_pilot_trail_contract.py",
            source_packet_path="docs/automation/0174UY/v5_operator_review_queue_manual_pilot_trail_contract_packet.json",
            upstream_stage_ids=["draft_or_render"],
            downstream_stage_ids=["approval_gate"],
            platform_scope="all",
            evidence_refs=["operator_review_bundle_stub"],
            blocker_codes=[],
            required_future_gate=None,
            state="PENDING",
            operator_action_required=True,
        ),
        LifecycleStage(
            stage_id="approval_gate",
            stage_order=5,
            stage_name="Operator Approval Gate",
            lifecycle_phase="Approval",
            source_task_label="TASK_CONTENTOPS_0174UW_V5_APPROVAL_QUEUE_V0",
            source_module="live_contentops/approval_queue.py",
            source_packet_path="docs/automation/0174UW/v5_manual_export_pilot_verification_contract_packet.json",
            upstream_stage_ids=["operator_review_bundle"],
            downstream_stage_ids=["manual_export"],
            platform_scope="all",
            evidence_refs=["approval_queue_stub"],
            blocker_codes=["blocked_no_operator_signature"],
            required_future_gate="live_operator_signature_vault",
            state="BLOCKED",
            operator_action_required=True,
        ),
        LifecycleStage(
            stage_id="manual_export",
            stage_order=6,
            stage_name="Manual Platform Export",
            lifecycle_phase="Dispatch",
            source_task_label="TASK_CONTENTOPS_0174UW_V5_MANUAL_EXPORT_PILOT_V0",
            source_module="live_contentops/v5_manual_export_pilot_verification_contract.py",
            source_packet_path="docs/automation/0174UW/v5_manual_export_pilot_verification_contract_packet.json",
            upstream_stage_ids=["approval_gate"],
            downstream_stage_ids=["operator_audit_summary"],
            platform_scope="all",
            evidence_refs=["manual_export_ready"],
            blocker_codes=["blocked_no_operator_signature", "blocked_no_payload_hash_lock"],
            required_future_gate="production_key_vault_decrypter",
            state="BLOCKED",
            operator_action_required=True,
        ),
        LifecycleStage(
            stage_id="operator_audit_summary",
            stage_order=7,
            stage_name="Operator Audit Summary",
            lifecycle_phase="Dispatch",
            source_task_label="TASK_CONTENTOPS_0175AT_EXPORT_PACKET_STUB_TO_OPERATOR_AUDIT_SUMMARY_V0",
            source_module="live_contentops/export_packet_stub_to_operator_audit_summary_contract.py",
            source_packet_path="docs/automation/0175AT/export_packet_stub_to_operator_audit_summary_contract_packet.json",
            upstream_stage_ids=["manual_export"],
            downstream_stage_ids=["manual_publish_record_precheck"],
            platform_scope="all",
            evidence_refs=["audit_summary_stub"],
            blocker_codes=["blocked_no_operator_signature", "blocked_no_payload_hash_lock"],
            required_future_gate="production_key_vault_decrypter",
            state="BLOCKED",
            operator_action_required=True,
        ),
        LifecycleStage(
            stage_id="manual_publish_record_precheck",
            stage_order=8,
            stage_name="Manual Publish Record Precheck",
            lifecycle_phase="Dispatch",
            source_task_label="TASK_CONTENTOPS_0175AU_OPERATOR_AUDIT_SUMMARY_TO_MANUAL_PUBLISH_RECORD_PRECHECK_V0",
            source_module="live_contentops/operator_audit_summary_to_manual_publish_record_precheck_contract.py",
            source_packet_path="docs/automation/0175AU/operator_audit_summary_to_manual_publish_record_precheck_contract_packet.json",
            upstream_stage_ids=["operator_audit_summary"],
            downstream_stage_ids=["manual_publish_record_stub"],
            platform_scope="all",
            evidence_refs=["publish_record_precheck"],
            blocker_codes=["blocked_no_manual_publish_record_gate"],
            required_future_gate="production_key_vault_decrypter",
            state="BLOCKED",
            operator_action_required=True,
        ),
        LifecycleStage(
            stage_id="manual_publish_record_stub",
            stage_order=9,
            stage_name="Manual Publish Record Stub",
            lifecycle_phase="Dispatch",
            source_task_label="TASK_CONTENTOPS_0175AV_MANUAL_PUBLISH_RECORD_PRECHECK_TO_RECORD_STUB_V0",
            source_module="live_contentops/manual_publish_record_precheck_to_record_stub_contract.py",
            source_packet_path="docs/automation/0175AV/manual_publish_record_precheck_to_record_stub_contract_packet.json",
            upstream_stage_ids=["manual_publish_record_precheck"],
            downstream_stage_ids=["metrics_precheck"],
            platform_scope="all",
            evidence_refs=["publish_record_stub"],
            blocker_codes=["blocked_no_platform_publication_identity", "blocked_no_external_publish_evidence"],
            required_future_gate="production_key_vault_decrypter",
            state="BLOCKED",
            operator_action_required=True,
        ),
        LifecycleStage(
            stage_id="metrics_precheck",
            stage_order=10,
            stage_name="Metrics Record Precheck",
            lifecycle_phase="Metrics",
            source_task_label="TASK_CONTENTOPS_0175AW_MANUAL_PUBLISH_RECORD_STUB_TO_METRICS_PRECHECK_V0",
            source_module="live_contentops/manual_publish_record_stub_to_metrics_precheck_contract.py",
            source_packet_path="docs/automation/0175AW/manual_publish_record_stub_to_metrics_precheck_contract_packet.json",
            upstream_stage_ids=["manual_publish_record_stub"],
            downstream_stage_ids=["metrics_record_stub"],
            platform_scope="all",
            evidence_refs=["metrics_precheck"],
            blocker_codes=["blocked_no_metrics_gate"],
            required_future_gate="production_key_vault_decrypter",
            state="BLOCKED",
            operator_action_required=True,
        ),
        LifecycleStage(
            stage_id="metrics_record_stub",
            stage_order=11,
            stage_name="Metrics Record Stub",
            lifecycle_phase="Metrics",
            source_task_label="TASK_CONTENTOPS_0175AX_METRICS_PRECHECK_TO_METRICS_RECORD_STUB_V0",
            source_module="live_contentops/metrics_precheck_to_metrics_record_stub_contract.py",
            source_packet_path="docs/automation/0175AX/metrics_precheck_to_metrics_record_stub_contract_packet.json",
            upstream_stage_ids=["metrics_precheck"],
            downstream_stage_ids=["performance_audit_precheck"],
            platform_scope="all",
            evidence_refs=["metrics_record_stub"],
            blocker_codes=["blocked_no_metrics_gate"],
            required_future_gate="production_key_vault_decrypter",
            state="BLOCKED",
            operator_action_required=True,
        ),
        LifecycleStage(
            stage_id="performance_audit_precheck",
            stage_order=12,
            stage_name="Performance Audit Precheck",
            lifecycle_phase="Metrics",
            source_task_label="TASK_CONTENTOPS_0175AY_METRICS_RECORD_STUB_TO_PERFORMANCE_AUDIT_PRECHECK_V0",
            source_module="live_contentops/metrics_record_stub_to_performance_audit_precheck_contract.py",
            source_packet_path="docs/automation/0175AY/metrics_record_stub_to_performance_audit_precheck_contract_packet.json",
            upstream_stage_ids=["metrics_record_stub"],
            downstream_stage_ids=["performance_summary_stub"],
            platform_scope="all",
            evidence_refs=["performance_audit_precheck"],
            blocker_codes=["blocked_no_performance_audit_gate"],
            required_future_gate="production_key_vault_decrypter",
            state="BLOCKED",
            operator_action_required=True,
        ),
        LifecycleStage(
            stage_id="performance_summary_stub",
            stage_order=13,
            stage_name="Performance Summary Stub",
            lifecycle_phase="Metrics",
            source_task_label="TASK_CONTENTOPS_0175AZ_PERFORMANCE_AUDIT_PRECHECK_TO_SUMMARY_STUB_V0",
            source_module="live_contentops/performance_audit_precheck_to_summary_stub_contract.py",
            source_packet_path="docs/automation/0175AZ/performance_audit_precheck_to_summary_stub_contract_packet.json",
            upstream_stage_ids=["performance_audit_precheck"],
            downstream_stage_ids=["content_feedback_precheck"],
            platform_scope="all",
            evidence_refs=["performance_summary_stub"],
            blocker_codes=["blocked_no_performance_audit_gate"],
            required_future_gate="production_key_vault_decrypter",
            state="BLOCKED",
            operator_action_required=True,
        ),
        LifecycleStage(
            stage_id="content_feedback_precheck",
            stage_order=14,
            stage_name="Content Feedback Precheck",
            lifecycle_phase="Feedback",
            source_task_label="TASK_CONTENTOPS_0175BA_PERFORMANCE_SUMMARY_STUB_TO_CONTENT_FEEDBACK_PRECHECK_V0",
            source_module="live_contentops/performance_summary_stub_to_content_feedback_precheck_contract.py",
            source_packet_path="docs/automation/0175BA/performance_summary_stub_to_content_feedback_precheck_contract_packet.json",
            upstream_stage_ids=["performance_summary_stub"],
            downstream_stage_ids=["content_feedback_stub"],
            platform_scope="all",
            evidence_refs=["content_feedback_precheck"],
            blocker_codes=["blocked_no_content_feedback_gate"],
            required_future_gate="production_key_vault_decrypter",
            state="BLOCKED",
            operator_action_required=True,
        ),
        LifecycleStage(
            stage_id="content_feedback_stub",
            stage_order=15,
            stage_name="Content Feedback Stub",
            lifecycle_phase="Feedback",
            source_task_label="TASK_CONTENTOPS_0175BB_CONTENT_FEEDBACK_PRECHECK_TO_FEEDBACK_STUB_V0",
            source_module="live_contentops/content_feedback_precheck_to_feedback_stub_contract.py",
            source_packet_path="docs/automation/0175BB/content_feedback_precheck_to_feedback_stub_contract_packet.json",
            upstream_stage_ids=["content_feedback_precheck"],
            downstream_stage_ids=["operator_review_brief_precheck"],
            platform_scope="all",
            evidence_refs=["content_feedback_stub"],
            blocker_codes=["blocked_no_content_feedback_gate"],
            required_future_gate="production_key_vault_decrypter",
            state="BLOCKED",
            operator_action_required=True,
        ),
        LifecycleStage(
            stage_id="operator_review_brief_precheck",
            stage_order=16,
            stage_name="Operator Review Brief Precheck",
            lifecycle_phase="Review",
            source_task_label="TASK_CONTENTOPS_0175BC_FEEDBACK_STUB_TO_OPERATOR_REVIEW_BRIEF_PRECHECK_V0",
            source_module="live_contentops/feedback_stub_to_operator_review_brief_precheck_contract.py",
            source_packet_path="docs/automation/0175BC/feedback_stub_to_operator_review_brief_precheck_contract_packet.json",
            upstream_stage_ids=["content_feedback_stub"],
            downstream_stage_ids=[],
            platform_scope="all",
            evidence_refs=["operator_review_brief_precheck"],
            blocker_codes=["blocked_no_operator_review_brief_gate"],
            required_future_gate="lane_c_operator_review_brief_precheck_to_brief_stub",
            state="BLOCKED",
            operator_action_required=True,
        ),
    ]


def build_lifecycle_read_model(stages: list[LifecycleStage] | None = None) -> list[dict[str, Any]]:
    """Builds the dictionary representation of the lifecycle stages read model."""
    if stages is None:
        stages = list_lifecycle_stages()
    return [_asdict(stage) for stage in sorted(stages, key=lambda s: s.stage_order)]


def build_operator_review_summary(stages: list[LifecycleStage] | None = None) -> OperatorReviewSummary:
    """Builds the OperatorReviewSummary status object based on current stage states."""
    if stages is None:
        stages = list_lifecycle_stages()

    sorted_stages = sorted(stages, key=lambda s: s.stage_order)
    total_stages = len(sorted_stages)
    blocked_count = sum(1 for s in sorted_stages if s.state == "BLOCKED" or len(s.blocker_codes) > 0)

    # Invariants safety check
    safety_locks_active = True
    for s in sorted_stages:
        # Check safety flags
        safety_fields = [
            s.public_postable,
            s.dispatch_ready,
            s.live_api_called,
            s.provider_api_called,
            s.env_read,
            s.credential_hydrated,
            s.scheduler_enabled,
            s.scraping_performed,
            s.autonomous_reply_or_dm_enabled,
            s.dqr_cleared_by_contentops,
            s.readiness_cleared_by_contentops,
            s.current_truth_promoted,
        ]
        if any(safety_fields):
            safety_locks_active = False
            break

    # Determine current lifecycle position (first blocked or pending stage)
    current_position = "artifact_or_brief_intake"
    for s in sorted_stages:
        if s.state != "COMPLETED":
            current_position = s.stage_id
            break

    # Next blocker
    next_blocker = None
    for s in sorted_stages:
        if s.state == "BLOCKED" or len(s.blocker_codes) > 0:
            next_blocker = s.stage_id
            break

    return OperatorReviewSummary(
        total_stage_count=total_stages,
        blocked_stage_count=blocked_count,
        dispatch_ready_count=0,
        public_postable_count=0,
        live_api_call_count=0,
        provider_api_call_count=0,
        credential_hydration_count=0,
        env_read_count=0,
        all_safety_locks_active=safety_locks_active,
        current_lifecycle_position=current_position,
        next_blocker=next_blocker,
    )


def validate_lifecycle_invariants(stages: list[LifecycleStage], raise_exception: bool = True) -> tuple[bool, list[str]]:
    """Validates the structure, links, and safety properties of the stages list.

    Returns:
        (passed, errors)
    """
    errors = []
    stage_ids = {s.stage_id for s in stages}

    # Order check
    orders = [s.stage_order for s in stages]
    if len(orders) != len(set(orders)):
        errors.append("Duplicate stage_order found.")

    for s in stages:
        # Invalid stage lookup
        if not s.stage_id:
            errors.append("Stage missing stage_id.")
            continue

        # Missing upstream refs
        for up_id in s.upstream_stage_ids:
            if up_id not in stage_ids:
                errors.append(f"Stage '{s.stage_id}' references missing upstream ID '{up_id}'.")

        # Missing downstream refs
        for down_id in s.downstream_stage_ids:
            if down_id not in stage_ids:
                errors.append(f"Stage '{s.stage_id}' references missing downstream ID '{down_id}'.")

        # Safety flag checks (fail closed: any safety flag being True causes validation failure)
        safety_violations = []
        if s.public_postable:
            safety_violations.append("public_postable")
        if s.dispatch_ready:
            safety_violations.append("dispatch_ready")
        if s.live_api_called:
            safety_violations.append("live_api_called")
        if s.provider_api_called:
            safety_violations.append("provider_api_called")
        if s.env_read:
            safety_violations.append("env_read")
        if s.credential_hydrated:
            safety_violations.append("credential_hydrated")
        if s.scheduler_enabled:
            safety_violations.append("scheduler_enabled")
        if s.scraping_performed:
            safety_violations.append("scraping_performed")
        if s.autonomous_reply_or_dm_enabled:
            safety_violations.append("autonomous_reply_or_dm_enabled")
        if s.dqr_cleared_by_contentops:
            safety_violations.append("dqr_cleared_by_contentops")
        if s.readiness_cleared_by_contentops:
            safety_violations.append("readiness_cleared_by_contentops")
        if s.current_truth_promoted:
            safety_violations.append("current_truth_promoted")

        if safety_violations:
            errors.append(f"Stage '{s.stage_id}' has safety lock violation flags: {', '.join(safety_violations)}")

    passed = len(errors) == 0
    if not passed and raise_exception:
        raise ValueError(f"Content lifecycle validation failed: {'; '.join(errors)}")

    return passed, errors


def build_contract_packet() -> dict[str, Any]:
    """Generates the full deterministic contract packet dict."""
    stages = list_lifecycle_stages()
    validate_lifecycle_invariants(stages, raise_exception=True)
    summary = build_operator_review_summary(stages)
    read_model = build_lifecycle_read_model(stages)

    safety_flags = {
        "all_safety_locks_active": summary.all_safety_locks_active,
        "live_api_called": any(s.live_api_called for s in stages),
        "provider_api_called": any(s.provider_api_called for s in stages),
        "env_read": any(s.env_read for s in stages),
        "credential_hydrated": any(s.credential_hydrated for s in stages),
        "scheduler_enabled": any(s.scheduler_enabled for s in stages),
        "scraping_performed": any(s.scraping_performed for s in stages),
        "autonomous_reply_or_dm_enabled": any(s.autonomous_reply_or_dm_enabled for s in stages),
        "public_postable": any(s.public_postable for s in stages),
        "dispatch_ready": any(s.dispatch_ready for s in stages),
    }

    raw_packet = {
        "task_label": TASK_LABEL,
        "matrix_version": MATRIX_VERSION,
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "generated_at_epoch": 0,
        "stages": read_model,
        "summary": _asdict(summary),
        "safety_flags": safety_flags,
        "ledger_family": LEDGER_FAMILY,
        "hash_algorithm": HASH_ALGORITHM,
        "next_required_gate": "lane_c_operator_review_brief_precheck_to_brief_stub",
    }

    packet_hash = _digest(raw_packet)

    return {
        "packet_hash": packet_hash,
        **raw_packet,
    }


def render_runbook(packet: dict[str, Any]) -> str:
    """Renders the markdown report representation of the contract packet."""
    stages = packet["stages"]
    summary = packet["summary"]
    safety = packet["safety_flags"]

    lines = [
        "# Content Lifecycle Spine and Operator Review Read Model",
        "",
        "> [!IMPORTANT]",
        "> This is the consolidated content lifecycle spine and operator review read model.",
        "> It maps all 16 micro-contract stages into a single coherent state machine.",
        "> Safety locks are active, and no platform, provider, env, or publish writes are allowed.",
        "",
        f"- **Task Label**: `{packet['task_label']}`",
        f"- **Matrix Version**: `{packet['matrix_version']}`",
        f"- **Source Baseline Commit**: `{packet['source_baseline_commit']}`",
        f"- **Packet Hash**: `{packet['packet_hash']}`",
        f"- **Ledger Family**: `{packet['ledger_family']}`",
        f"- **Next Required Gate**: `{packet['next_required_gate']}`",
        "",
        "## Summary Metrics",
        "",
        f"- **Total Stages Registered**: `{summary['total_stage_count']}`",
        f"- **Blocked Stages**: `{summary['blocked_stage_count']}`",
        f"- **Current Lifecycle Position**: `{summary['current_lifecycle_position']}`",
        f"- **Next Blocker Stage**: `{summary['next_blocker']}`",
        f"- **Next Recommended Task**: `{summary['next_recommended_task']}`",
        "",
        "## Invariant Validation Safety Flags",
        "",
        "| Safety Lock | State | Status |",
        "|---|---|---|",
    ]

    for k, v in safety.items():
        lines.append(f"| `{k}` | `{v}` | {'✅' if not v or k == 'all_safety_locks_active' else '❌'} |")

    lines.extend([
        "",
        "## Canonical Stages Inventory",
        "",
        "| ID | Order | Name | Phase | Task Label | State | Blocker Codes | Future Gate |",
        "|---|---|---|---|---|---|---|---|",
    ])

    for s in stages:
        blockers = ", ".join(s["blocker_codes"]) if s["blocker_codes"] else "None"
        gate = s["required_future_gate"] if s["required_future_gate"] else "None"
        lines.append(
            f"| `{s['stage_id']}` | `{s['stage_order']}` | {s['stage_name']} | {s['lifecycle_phase']} | "
            f"`{s['source_task_label']}` | `{s['state']}` | `{blockers}` | `{gate}` |"
        )

    lines.extend([
        "",
        "## Detailed Stages Breakdown",
        "",
    ])

    for s in stages:
        lines.extend([
            f"### Stage: `{s['stage_id']}`",
            "",
            f"- **Name**: {s['stage_name']}",
            f"- **Lifecycle Phase**: {s['lifecycle_phase']}",
            f"- **Source Module**: `{s['source_module']}`",
            f"- **Source Packet**: `{s['source_packet_path']}`",
            f"- **Platform Scope**: `{s['platform_scope']}`",
            f"- **Upstream Stages**: `{s['upstream_stage_ids']}`",
            f"- **Downstream Stages**: `{s['downstream_stage_ids']}`",
            f"- **Evidence Refs**: `{s['evidence_refs']}`",
            f"- **Blocker Codes**: `{s['blocker_codes']}`",
            f"- **Required Future Gate**: `{s['required_future_gate']}`",
            f"- **State**: `{s['state']}`",
            f"- **Operator Action Required**: `{s['operator_action_required']}`",
            "",
        ])

    return "\n".join(lines)


def write_contract_artifacts(repo_root: str | Path = ".") -> dict[str, Any]:
    """Writes the JSON packet and Markdown runbook to the docs/automation/0175BE/ directory."""
    root = Path(repo_root).resolve()
    out = (root / DOC_REL_DIR).resolve()
    out.mkdir(parents=True, exist_ok=True)

    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {
        "packet": packet,
        "packet_path": str(packet_path),
        "runbook_path": str(runbook_path),
    }


if __name__ == "__main__":
    write_contract_artifacts()
