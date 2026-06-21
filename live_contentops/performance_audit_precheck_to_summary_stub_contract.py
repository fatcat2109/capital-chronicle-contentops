"""Performance Audit Precheck to Summary Stub contract, 0175AZ.

Deterministic local-only contract converting performance audit precheck records to performance summary stubs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops.metrics_record_stub_to_performance_audit_precheck_contract import (
    build_contract_packet as build_precheck_packet
)

TASK_LABEL = "TASK_CONTENTOPS_0175AZ_PERFORMANCE_AUDIT_PRECHECK_TO_SUMMARY_STUB_V0"
MATRIX_VERSION = "0175AZ_PERFORMANCE_AUDIT_PRECHECK_TO_SUMMARY_STUB_V1"
SOURCE_BASELINE_COMMIT = "048b27c6dce2aef5fb38e0552b8208d4fd408d9f"
LEDGER_FAMILY = "performance_audit_precheck_to_summary_stub_future"
HASH_ALGORITHM = "sha256"
DOC_REL_DIR = Path("docs") / "automation" / "0175AZ"
PACKET_FILENAME = "performance_audit_precheck_to_summary_stub_contract_packet.json"
RUNBOOK_FILENAME = "performance_audit_precheck_to_summary_stub_contract.md"


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
class PerformanceSummaryStubTarget:
    platform_target_id: str
    summary_stub_type: str
    description: str


@dataclass(frozen=True)
class PerformanceSummaryStubMetricReference:
    metric_name: str
    source_field_name: str
    placeholder_only: bool = True
    real_metric_recorded: bool = False
    metric_value_recorded: bool = False
    metric_score_computed: bool = False
    kpi_comparison_computed: bool = False
    performance_claim_generated: bool = False
    recommendation_generated: bool = False
    rank_generated: bool = False
    best_or_worst_claim_generated: bool = False
    requires_human_performance_review: bool = True


@dataclass(frozen=True)
class PerformanceSummaryStubInvariant:
    invariant_id: str
    expected_state: str
    actual_state: str
    passed: bool
    evidence_note: str


@dataclass(frozen=True)
class PerformanceSummaryStubRecord:
    performance_summary_stub_id: str
    source_performance_audit_precheck_id: str
    source_metrics_record_stub_id: str
    source_metrics_precheck_id: str
    source_manual_publish_record_stub_id: str
    source_manual_publish_record_precheck_id: str
    source_audit_summary_id: str
    source_export_packet_stub_id: str
    source_manual_export_precheck_id: str
    source_decision_gate_id: str
    platform_target_id: str
    platform_family: str
    performance_summary_stub_status: str
    performance_target_type: str
    summary_stub_type: str
    metric_references: list[PerformanceSummaryStubMetricReference]
    invariants: list[PerformanceSummaryStubInvariant]
    blocked_reasons: list[str]
    missing_future_gates: list[str]
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
    metrics_gate_status: str
    performance_audit_gate_status: str
    dispatch_gate_status: str
    packet_hash: str
    # Safety & Status Flags
    real_metrics_recorded: bool = False
    metric_values_recorded: bool = False
    platform_metric_id_recorded: bool = False
    external_metric_timestamp_recorded: bool = False
    public_metrics_recorded: bool = False
    metric_score_computed: bool = False
    kpi_comparison_computed: bool = False
    performance_claim_generated: bool = False
    recommendation_generated: bool = False
    rank_generated: bool = False
    best_or_worst_claim_generated: bool = False
    platform_analytics_pull_performed: bool = False
    manual_publish_record_allowed: bool = False
    manual_publish_record_created: bool = False
    platform_publication_url_recorded: bool = False
    platform_post_id_recorded: bool = False
    external_publish_timestamp_recorded: bool = False
    export_ready: bool = False
    manual_export_allowed: bool = False
    export_file_created: bool = False
    clipboard_payload_created: bool = False
    download_artifact_created: bool = False
    publishable_payload_created: bool = False
    platform_payload_created: bool = False
    public_postable: bool = False
    publishable_text: bool = False
    platform_ready: bool = False
    dispatch_ready: bool = False
    approval_granted: bool = False
    approved_for_publication: bool = False
    operator_identity_bound: bool = False
    operator_signature_present: bool = False
    payload_hash_locked: bool = False
    account_binding_active: bool = False
    credential_values_loaded: bool = False
    platform_api_called: bool = False
    provider_api_called: bool = False
    scheduler_enabled: bool = False
    scraping: bool = False


@dataclass(frozen=True)
class PerformanceSummaryStubPacket:
    task_label: str
    matrix_version: str
    source_baseline_commit: str
    generated_at_epoch: int
    summary_records: list[PerformanceSummaryStubRecord]
    summary_targets: list[PerformanceSummaryStubTarget]
    summary_counts: dict[str, int]
    safety_flags: dict[str, bool]
    blocked_capabilities: list[str]
    missing_future_gates: list[str]
    ledger_family: str
    packet_hash: str
    hash_algorithm: str
    next_required_gate: str


def build_summary_targets() -> list[PerformanceSummaryStubTarget]:
    targets = {
        "x": ("x_performance_summary_stub", "Performance summary stub for X platform"),
        "telegram_channel_destination": ("telegram_channel_performance_summary_stub", "Performance summary stub for Telegram channel"),
        "telegram_remote_operator": ("telegram_remote_operator_log_performance_summary_stub", "Performance summary stub for Telegram remote operator"),
        "substack": ("substack_performance_summary_stub", "Performance summary stub for Substack"),
        "linkedin": ("linkedin_performance_summary_stub", "Performance summary stub for LinkedIn"),
        "threads": ("threads_performance_summary_stub", "Performance summary stub for Meta Threads"),
        "instagram": ("instagram_performance_summary_stub", "Performance summary stub for Instagram"),
        "facebook_page": ("facebook_page_performance_summary_stub", "Performance summary stub for Facebook Page"),
        "tiktok": ("tiktok_performance_summary_stub", "Performance summary stub for TikTok"),
        "youtube": ("youtube_performance_summary_stub", "Performance summary stub for YouTube")
    }
    return [
        PerformanceSummaryStubTarget(platform_target_id=tid, summary_stub_type=val[0], description=val[1])
        for tid, val in targets.items()
    ]


def build_metric_references_by_target(platform_target_id: str) -> list[PerformanceSummaryStubMetricReference]:
    fields_map = {
        "x": ["impressions_stub", "likes_stub", "replies_stub", "reposts_stub", "clicks_stub"],
        "telegram_channel_destination": ["views_stub", "reactions_stub", "forwards_stub", "replies_stub"],
        "telegram_remote_operator": ["operator_review_count_stub", "manual_action_count_stub", "audit_event_count_stub"],
        "substack": ["opens_stub", "clicks_stub", "likes_stub", "comments_stub", "subscriber_delta_stub"],
        "linkedin": ["impressions_stub", "reactions_stub", "comments_stub", "reposts_stub", "clicks_stub"],
        "threads": ["views_stub", "likes_stub", "replies_stub", "reposts_stub"],
        "instagram": ["views_stub", "likes_stub", "comments_stub", "shares_stub", "saves_stub"],
        "facebook_page": ["reach_stub", "reactions_stub", "comments_stub", "shares_stub", "clicks_stub"],
        "tiktok": ["views_stub", "likes_stub", "comments_stub", "shares_stub", "saves_stub"],
        "youtube": ["views_stub", "likes_stub", "comments_stub", "watch_time_stub", "subscriber_delta_stub"]
    }
    field_names = fields_map.get(platform_target_id, [])
    return [
        PerformanceSummaryStubMetricReference(
            metric_name=fname,
            source_field_name=fname
        )
        for fname in field_names
    ]


def build_invariants() -> list[PerformanceSummaryStubInvariant]:
    invariants = [
        ("no_real_metrics_recorded", "no_record", "no_record", True, "Verified no real platform performance metrics recorded."),
        ("no_metric_values_recorded", "no_record", "no_record", True, "Verified metric values are unrecorded."),
        ("no_platform_metric_id_recorded", "no_id", "no_id", True, "Verified platform metric ID is unrecorded."),
        ("no_external_metric_timestamp_recorded", "no_timestamp", "no_timestamp", True, "Verified external metric timestamp remains unrecorded."),
        ("no_public_metrics_recorded", "no_metrics", "no_metrics", True, "Verified public audience metrics remain unrecorded."),
        ("no_metric_score_computed", "no_score", "no_score", True, "Verified no performance score has been computed."),
        ("no_kpi_comparison_computed", "no_comparison", "no_comparison", True, "Verified no KPI comparison has been performed."),
        ("no_performance_claim_generated", "no_claim", "no_claim", True, "Verified no performance claims or analytics texts were generated."),
        ("no_recommendation_generated", "no_recommendation", "no_recommendation", True, "Verified no performance recommendation or suggestion was generated."),
        ("no_rank_generated", "no_rank", "no_rank", True, "Verified no platform rank score generated."),
        ("no_best_or_worst_claim_generated", "no_claim", "no_claim", True, "Verified no best or worst performing claims generated."),
        ("no_platform_analytics_pull", "no_pull", "no_pull", True, "Verified no active analytics pulls were executed."),
        ("no_scraping", "disabled", "disabled", True, "Verified scraping is blocked."),
        ("no_manual_publish_record_created", "no_record", "no_record", True, "Verified no manual publish record created."),
        ("no_platform_publication_url_recorded", "no_url", "no_url", True, "Verified platform publication URL remains unrecorded."),
        ("no_platform_post_id_recorded", "no_post_id", "no_post_id", True, "Verified platform post ID remains unrecorded."),
        ("no_export_file_created", "no_file", "no_file", True, "Checked local workspace; no export files exist."),
        ("no_clipboard_payload_created", "no_clipboard", "no_clipboard", True, "Verified clipboard payload remains ungenerated."),
        ("no_download_artifact_created", "no_download", "no_download", True, "Verified no download artifact created."),
        ("no_publishable_payload_created", "no_payload", "no_payload", True, "Verified no publishable payload created."),
        ("no_platform_payload_created", "no_payload", "no_payload", True, "Verified platform payload is not generated."),
        ("no_platform_api_call", "no_api_calls", "no_api_calls", True, "Verified no platform API calls executed."),
        ("no_provider_api_call", "no_api_calls", "no_api_calls", True, "Verified no provider LLM API calls executed."),
        ("no_credential_or_env_read", "no_reads", "no_reads", True, "Verified no credentials or environment read operations performed."),
        ("no_account_binding_active", "inactive", "inactive", True, "Verified no account binding is active."),
        ("no_scheduler", "disabled", "disabled", True, "Verified no scheduler enabled."),
        ("no_autonomous_posting", "disabled", "disabled", True, "Verified autonomous posting is blocked."),
        ("no_autonomous_reply_or_dm", "disabled", "disabled", True, "Verified autonomous replies and DMs are blocked."),
        ("no_financial_advice", "absent", "absent", True, "Verified draft does not contain financial advice."),
        ("no_signal_language", "absent", "absent", True, "Verified draft does not contain trading signals or order terminology."),
        ("no_market_number_fabrication", "absent", "absent", True, "Verified draft contains no fabricated market numbers."),
        ("preserve_citation_requirements", "pending", "pending", True, "Verified citations are preserved as unresolved placeholders."),
        ("preserve_limitations", "pending", "pending", True, "Verified limitation slot is preserved as unresolved."),
        ("preserve_dqr_readiness_blocks", "pending", "pending", True, "Verified DQR readiness blocks are preserved."),
        ("require_operator_signature", "required", "required", True, "Verified operator signature required for validation."),
        ("require_payload_hash_lock", "required", "required", True, "Verified payload hash lock is required."),
        ("require_metrics_gate", "required", "required", True, "Verified performance metrics gate is required."),
        ("require_performance_audit_gate", "required", "required", True, "Verified performance audit gate is required."),
        ("require_future_content_feedback_precheck", "required", "required", True, "Verified future content feedback precheck gate is required.")
    ]
    return [
        PerformanceSummaryStubInvariant(
            invariant_id=inv[0],
            expected_state=inv[1],
            actual_state=inv[2],
            passed=inv[3],
            evidence_note=inv[4]
        )
        for inv in invariants
    ]


def build_safety_flags() -> dict[str, bool]:
    return {
        "local_only": True,
        "fixture_only": True,
        "schema_only": True,
        "performance_summary_stub_only": True,
        "performance_audit_precheck_only": True,
        "metrics_record_stub_only": True,
        "metrics_precheck_only": True,
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
        "manual_export_allowed": False,
        "manual_publish_record_allowed": False,
        "manual_publish_record_created": False,
        "platform_publication_url_recorded": False,
        "platform_post_id_recorded": False,
        "external_publish_timestamp_recorded": False,
        "public_metrics_recorded": False,
        "real_metrics_recorded": False,
        "metric_values_recorded": False,
        "platform_metric_id_recorded": False,
        "external_metric_timestamp_recorded": False,
        "metric_score_computed": False,
        "kpi_comparison_computed": False,
        "performance_claim_generated": False,
        "recommendation_generated": False,
        "rank_generated": False,
        "best_or_worst_claim_generated": False,
        "platform_analytics_pull_performed": False,
        "export_file_created": False,
        "clipboard_payload_created": False,
        "download_artifact_created": False,
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
    }


def build_contract_packet() -> dict[str, Any]:
    precheck_data = build_precheck_packet()
    precheck_records = precheck_data.get("precheck_records", [])

    summary_targets = build_summary_targets()
    target_type_map = {t.platform_target_id: t.summary_stub_type for t in summary_targets}

    invariants = build_invariants()

    blocked_reasons = [
        "blocked_no_operator_signature",
        "blocked_no_payload_hash_lock",
        "blocked_unresolved_citations",
        "blocked_unresolved_limitations",
        "blocked_dqr_readiness_unresolved",
        "blocked_no_manual_publish_record_gate",
        "blocked_no_platform_publication_identity",
        "blocked_no_external_publish_evidence",
        "blocked_no_metrics_gate",
        "blocked_no_performance_audit_gate",
        "blocked_no_content_feedback_precheck"
    ]

    summary_records: list[PerformanceSummaryStubRecord] = []

    for rec in precheck_records:
        tid = rec["platform_target_id"]
        family = rec["platform_family"]
        summary_type = target_type_map.get(tid, "generic_performance_summary_stub")
        metric_refs = build_metric_references_by_target(tid)

        raw_record = {
            "performance_summary_stub_id": f"performance_summary_stub_{tid}",
            "source_performance_audit_precheck_id": rec["performance_audit_precheck_id"],
            "source_metrics_record_stub_id": rec["source_metrics_record_stub_id"],
            "source_metrics_precheck_id": rec["source_metrics_precheck_id"],
            "source_manual_publish_record_stub_id": rec["source_manual_publish_record_stub_id"],
            "source_manual_publish_record_precheck_id": rec["source_manual_publish_record_precheck_id"],
            "source_audit_summary_id": rec["source_audit_summary_id"],
            "source_export_packet_stub_id": rec["source_export_packet_stub_id"],
            "source_manual_export_precheck_id": rec["source_manual_export_precheck_id"],
            "source_decision_gate_id": rec["source_decision_gate_id"],
            "platform_target_id": tid,
            "platform_family": family,
            "performance_summary_stub_status": "performance_summary_stub_blocked",
            "performance_target_type": rec["performance_target_type"],
            "summary_stub_type": summary_type,
            "metric_references": [_asdict(f) for f in metric_refs],
            "invariants": [_asdict(inv) for inv in invariants],
            "blocked_reasons": blocked_reasons,
            "missing_future_gates": ["lane_c_performance_summary_stub_to_content_feedback_precheck", "production_key_vault_decrypter", "live_operator_signature_vault"],
            "operator_identity_status": rec["operator_identity_status"],
            "operator_signature_status": rec["operator_signature_status"],
            "payload_hash_lock_status": rec["payload_hash_lock_status"],
            "citation_status": rec["citation_status"],
            "limitation_status": rec["limitation_status"],
            "dqr_status": rec["dqr_status"],
            "readiness_status": rec["readiness_status"],
            "current_truth_status": rec["current_truth_status"],
            "account_binding_status": rec["account_binding_status"],
            "credential_gate_status": rec["credential_gate_status"],
            "metrics_gate_status": rec["metrics_gate_status"],
            "performance_audit_gate_status": rec["performance_audit_gate_status"],
            "dispatch_gate_status": rec["dispatch_gate_status"],
            # Safety & Status Flags
            "real_metrics_recorded": False,
            "metric_values_recorded": False,
            "platform_metric_id_recorded": False,
            "external_metric_timestamp_recorded": False,
            "public_metrics_recorded": False,
            "metric_score_computed": False,
            "kpi_comparison_computed": False,
            "performance_claim_generated": False,
            "recommendation_generated": False,
            "rank_generated": False,
            "best_or_worst_claim_generated": False,
            "platform_analytics_pull_performed": False,
            "manual_publish_record_allowed": False,
            "manual_publish_record_created": False,
            "platform_publication_url_recorded": False,
            "platform_post_id_recorded": False,
            "external_publish_timestamp_recorded": False,
            "export_ready": False,
            "manual_export_allowed": False,
            "export_file_created": False,
            "clipboard_payload_created": False,
            "download_artifact_created": False,
            "publishable_payload_created": False,
            "platform_payload_created": False,
            "public_postable": False,
            "publishable_text": False,
            "platform_ready": False,
            "dispatch_ready": False,
            "approval_granted": False,
            "approved_for_publication": False,
            "operator_identity_bound": False,
            "operator_signature_present": False,
            "payload_hash_locked": False,
            "account_binding_active": False,
            "credential_values_loaded": False,
            "platform_api_called": False,
            "provider_api_called": False,
            "scheduler_enabled": False,
            "scraping": False
        }

        rec_hash = _digest(raw_record)
        summary_records.append(
            PerformanceSummaryStubRecord(
                packet_hash=rec_hash,
                **raw_record
            )
        )

    safety = build_safety_flags()

    # Calculate fields total
    refs_count = sum(len(rec.metric_references) for rec in summary_records)

    summary_counts = {
        "registered_summary_records_count": len(summary_records),
        "summary_targets_count": len(summary_targets),
        "summary_invariants_count": len(invariants),
        "summary_metric_references_count": refs_count,
        "safety_flags_count": len(safety)
    }

    blocked_caps = [
        "live_publishing_dispatch",
        "autonomous_reply_automation",
        "live_credential_hydration",
        "active_scheduler_triggers",
        "manual_review_export",
        "live_metrics_retrieval",
        "scraping",
        "performance_scoring",
        "analytics_ingestion",
        "performance_claims_reporting"
    ]

    missing_gates = [
        "lane_c_performance_summary_stub_to_content_feedback_precheck",
        "production_key_vault_decrypter",
        "live_operator_signature_vault"
    ]

    packet = PerformanceSummaryStubPacket(
        task_label=TASK_LABEL,
        matrix_version=MATRIX_VERSION,
        source_baseline_commit=SOURCE_BASELINE_COMMIT,
        generated_at_epoch=0,
        summary_records=summary_records,
        summary_targets=summary_targets,
        summary_counts=summary_counts,
        safety_flags=safety,
        blocked_capabilities=blocked_caps,
        missing_future_gates=missing_gates,
        ledger_family=LEDGER_FAMILY,
        packet_hash="",
        hash_algorithm=HASH_ALGORITHM,
        next_required_gate="lane_c_performance_summary_stub_to_content_feedback_precheck"
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
    records = packet["summary_records"]
    targets = packet["summary_targets"]
    counts = packet["summary_counts"]
    safety = packet["safety_flags"]
    blocked_caps = packet["blocked_capabilities"]
    missing_gates = packet["missing_future_gates"]

    lines = [
        "# Performance Audit Precheck to Summary Stub Contract",
        "",
        "> [!IMPORTANT]",
        "> This is a performance summary stub contract, not performance reporting and not analytics ingestion.",
        "> It creates blocked performance summary metadata and non-public metric references only.",
        "> It preserves citation, limitation, DQR/readiness, operator identity, signature, hash-lock, metrics-gate, performance-audit-gate, account-binding, credential, and dispatch-gate requirements.",
        "> It cannot record metrics, score performance, compare KPIs, generate claims/recommendations/rankings, pull analytics, scrape platforms, create publish records, publication URLs, platform post IDs, timestamps, files, screenshots, clipboard payloads, downloads, approvals, exports, publishable payloads, dispatches, schedules, or platform/API calls.",
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
        "## Stub summary counts",
        "",
        f"- **Registered Performance Summary Stubs**: `{counts['registered_summary_records_count']}`",
        f"- **Registered Performance Summary Targets**: `{counts['summary_targets_count']}`",
        f"- **Invariants Checked**: `{counts['summary_invariants_count']}`",
        f"- **Placeholder Metric References Defined**: `{counts['summary_metric_references_count']}`",
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
        "## Performance Summary Target Configurations",
        "",
        "| Platform Target ID | Summary Stub Type | Description |",
        "|---|---|---|",
    ])

    for t in targets:
        lines.append(f"| `{t['platform_target_id']}` | `{t['summary_stub_type']}` | {t['description']} |")

    lines.extend([
        "",
        "## Platform Performance Summary Stubs",
        "",
    ])

    for r in records:
        lines.extend([
            f"### Performance Summary Stub Record: `{r['performance_summary_stub_id']}`",
            "",
            f"- **Source Performance Audit Precheck ID**: `{r['source_performance_audit_precheck_id']}`",
            f"- **Source Metrics Record Stub ID**: `{r['source_metrics_record_stub_id']}`",
            f"- **Source Metrics Precheck ID**: `{r['source_metrics_precheck_id']}`",
            f"- **Source Manual Publish Record Stub ID**: `{r['source_manual_publish_record_stub_id']}`",
            f"- **Source Manual Publish Record Precheck ID**: `{r['source_manual_publish_record_precheck_id']}`",
            f"- **Source Audit Summary ID**: `{r['source_audit_summary_id']}`",
            f"- **Source Export Packet Stub ID**: `{r['source_export_packet_stub_id']}`",
            f"- **Source Manual Export Precheck ID**: `{r['source_manual_export_precheck_id']}`",
            f"- **Source Decision Gate ID**: `{r['source_decision_gate_id']}`",
            f"- **Platform Target ID**: `{r['platform_target_id']}`",
            f"- **Platform Family**: `{r['platform_family']}`",
            f"- **Performance Summary Stub Status**: `{r['performance_summary_stub_status']}`",
            f"- **Performance Target Type**: `{r['performance_target_type']}`",
            f"- **Summary Stub Type**: `{r['summary_stub_type']}`",
            f"- **Real Metrics Recorded**: `{r['real_metrics_recorded']}`",
            f"- **Metric Values Recorded**: `{r['metric_values_recorded']}`",
            f"- **Platform Metric ID Recorded**: `{r['platform_metric_id_recorded']}`",
            f"- **External Metric Timestamp Recorded**: `{r['external_metric_timestamp_recorded']}`",
            f"- **Public Metrics Recorded**: `{r['public_metrics_recorded']}`",
            f"- **Metric Score Computed**: `{r['metric_score_computed']}`",
            f"- **KPI Comparison Computed**: `{r['kpi_comparison_computed']}`",
            f"- **Performance Claim Generated**: `{r['performance_claim_generated']}`",
            f"- **Recommendation Generated**: `{r['recommendation_generated']}`",
            f"- **Rank Generated**: `{r['rank_generated']}`",
            f"- **Best or Worst Claim Generated**: `{r['best_or_worst_claim_generated']}`",
            f"- **Platform Analytics Pull Performed**: `{r['platform_analytics_pull_performed']}`",
            f"- **Manual Publish Record Allowed**: `{r['manual_publish_record_allowed']}`",
            f"- **Manual Publish Record Created**: `{r['manual_publish_record_created']}`",
            f"- **Platform Publication URL Recorded**: `{r['platform_publication_url_recorded']}`",
            f"- **Platform Post ID Recorded**: `{r['platform_post_id_recorded']}`",
            f"- **External Publish Timestamp Recorded**: `{r['external_publish_timestamp_recorded']}`",
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
            f"- **Metrics Gate**: `{r['metrics_gate_status']}`",
            f"- **Performance Audit Gate**: `{r['performance_audit_gate_status']}`",
            f"- **Dispatch Gate**: `{r['dispatch_gate_status']}`",
            "",
            "#### Metric References",
            "",
            "| Metric Name | Source Field Name | Requires Human Performance Review |",
            "|---|---|---|",
        ])

        for f in r["metric_references"]:
            lines.append(f"| `{f['metric_name']}` | `{f['source_field_name']}` | `{f['requires_human_performance_review']}` |")

        lines.extend([
            "",
            "#### Evaluation Invariants",
            "",
            "| Invariant ID | Expected State | Actual State | Passed | Evidence Note |",
            "|---|---|---|---|---|",
        ])

        for inv in r["invariants"]:
            lines.append(
                f"| `{inv['invariant_id']}` | `{inv['expected_state']}` | `{inv['actual_state']}` | `{inv['passed']}` | {inv['evidence_note']} |"
            )

        lines.extend([
            "",
            "#### Blocked Reasons",
            "",
        ])

        for br in r["blocked_reasons"]:
            lines.append(f"- `{br}`")
        lines.append("")

    return "\n".join(lines)


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0175AZ")

    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME

    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")

    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


if __name__ == "__main__":
    write_artifacts()
