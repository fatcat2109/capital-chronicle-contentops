"""Local content governance summary mart contract, 0174UE.

Deterministic local-only governance mart aggregating prior contract packets into
operator-safe summary rows. No UI, API, provider, network, env, credential,
scraping, scheduler, browser, DM, dispatch, public post, current-truth, DQR,
readiness, or ingestion mutation behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from live_contentops import content_performance_review_editorial_feedback_contract as ud
from live_contentops import manual_publish_record_metrics_ledger_contract as uc
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UE_LOCAL_CONTENT_GOVERNANCE_SUMMARY_MART_CONTRACT_V0"
MODEL_VERSION = "0174UE_LOCAL_CONTENT_GOVERNANCE_SUMMARY_MART_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "b2a403607846fbc97e6cb23e5fc3170e93097351"
DOC_REL_DIR = Path("docs") / "automation" / "0174UE"
PACKET_FILENAME = "local_content_governance_summary_mart_contract_packet.json"
RUNBOOK_FILENAME = "local_content_governance_summary_mart_contract.md"
HASH_ALGORITHM = "sha256"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174UF_AUDIT_LEDGER_FAMILY_TAXONOMY_EXTENSION_V0"
STATUS_LOCAL_SUMMARY_READY = "local_governance_summary_ready_review_only"
STATUS_BLOCKED = "blocked"
SOFT_CAVEAT_0174UD_U9_UNKNOWN = "0174UD_u9_audit_family_unknown_or_blocked_soft_caveat"
UPSTREAM_PRESERVED_BLOCKERS = (
    "future_send_gate_required",
    "can_dispatch_false_by_contract",
    "dispatch_revalidation_required_future_0174UB",
)
SOFT_CAVEAT_UPSTREAM_FUTURE_SEND = "upstream_future_send_gate_preserved_soft_caveat"


@dataclass(frozen=True)
class ContentGovernanceSummaryRow:
    summary_row_id: str
    source_manual_publish_record_id: str
    source_manual_metrics_record_id: str
    source_performance_review_id: str
    source_feedback_loop_packet_id: str
    source_payload_hash: str
    platform_id: str
    payload_class_id: str
    content_lane: str
    manual_publish_record_status: str
    metric_quality_class: str
    performance_interpretation_class: str
    feedback_loop_status: str
    governance_status: str
    public_postable: bool
    can_dispatch: bool
    can_auto_generate_content: bool
    can_approve: bool
    can_publish_public_claim: bool
    human_review_required: bool
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
    soft_caveats: tuple[str, ...]


@dataclass(frozen=True)
class PlatformGovernanceSummary:
    platform_id: str
    summary_row_count: int
    manual_publish_record_count: int
    manual_metrics_record_count: int
    performance_review_count: int
    public_postable_count: int
    dispatch_ready_count: int
    review_only_count: int
    blocked_count: int
    soft_caveats: tuple[str, ...]


@dataclass(frozen=True)
class EvidenceGovernanceSummary:
    evidence_ref_count: int
    audit_ledger_entry_count: int
    all_records_redacted: bool
    u9_unknown_or_blocked_entry_count: int
    u9_unknown_or_blocked_soft_caveat: bool
    retained_evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class GovernanceBlockerSummary:
    blocked_reason: str
    occurrence_count: int
    source_row_ids: tuple[str, ...]


@dataclass(frozen=True)
class LocalContentGovernanceSummaryMartPacket:
    packet_id: str
    summary_rows: tuple[ContentGovernanceSummaryRow, ...]
    platform_summaries: tuple[PlatformGovernanceSummary, ...]
    evidence_summary: EvidenceGovernanceSummary
    blocker_summaries: tuple[GovernanceBlockerSummary, ...]
    packet_hash: str
    packet_hash_algorithm: str
    mart_status: str
    all_rows_review_only: bool
    all_records_redacted: bool
    public_postable_count: int
    dispatch_ready_count: int
    no_api_verification: bool
    no_scraping: bool
    no_auto_generation: bool
    no_auto_publish: bool
    no_dispatch: bool
    no_public_claim_authorized: bool
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
    soft_caveats: tuple[str, ...]
    next_required_gate: str


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


def _unique(values: Any) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(v) for v in values if v))


def safety_flags() -> dict[str, bool]:
    false = (
        "metrics_api_verified", "metrics_scraped", "can_auto_generate_content",
        "can_auto_publish", "can_dispatch", "dispatch_ready", "public_postable",
        "public_claim_authorized", "approval_granted", "live_dispatch_enabled",
        "platform_api_called", "telegram_api_called", "provider_api_called",
        "llm_provider_called", "credential_hydrated", "env_read",
        "network_performed", "scheduler_enabled", "autonomous_posting_allowed",
        "scraping_performed", "dm_or_reply_automation_allowed",
        "browser_session_used", "current_truth_promoted", "dqr_cleared",
        "readiness_cleared", "ingestion_repo_mutated", "ui_generated",
    )
    return {**{key: False for key in false}, "local_summary_mart_only": True, "review_only": True}


def _soft_caveats(entries: tuple[audit.RedactedAuditLedgerEntry, ...], blockers: tuple[str, ...] = ()) -> tuple[str, ...]:
    caveats: list[str] = []
    if any(entry.entry_family == "unknown_or_blocked" and entry.source_model == "0174UD" for entry in entries):
        caveats.append(SOFT_CAVEAT_0174UD_U9_UNKNOWN)
    if any(blocker in UPSTREAM_PRESERVED_BLOCKERS for blocker in blockers):
        caveats.append(SOFT_CAVEAT_UPSTREAM_FUTURE_SEND)
    return _unique(caveats)


def _hard_blockers(blockers: tuple[str, ...]) -> tuple[str, ...]:
    return _unique(blocker for blocker in blockers if blocker not in UPSTREAM_PRESERVED_BLOCKERS)


def build_summary_row(
    publish: uc.ManualPublishRecord,
    metrics: uc.ManualMetricsRecord,
    review: ud.ContentPerformanceReviewPacket,
    loop: ud.EditorialFeedbackLoopPacket,
    *,
    soft_caveats: tuple[str, ...] = (),
) -> ContentGovernanceSummaryRow:
    upstream_blockers = _unique(tuple(publish.blocked_reasons) + tuple(metrics.blocked_reasons) + tuple(review.blocked_reasons) + tuple(loop.blocked_reasons))
    blockers = _hard_blockers(upstream_blockers)
    review_only = bool(review.can_create_editorial_feedback and loop.feedback_loop_status == ud.REVIEW_STATUS)
    status = STATUS_LOCAL_SUMMARY_READY if review_only and not blockers else STATUS_BLOCKED
    material = {
        "publish": publish.manual_publish_record_id,
        "metrics": metrics.manual_metrics_record_id,
        "review": review.performance_review_id,
        "loop": loop.feedback_loop_packet_id,
        "status": status,
    }
    return ContentGovernanceSummaryRow(
        summary_row_id="content_governance_summary_row_" + _digest(material)[:24],
        source_manual_publish_record_id=publish.manual_publish_record_id,
        source_manual_metrics_record_id=metrics.manual_metrics_record_id,
        source_performance_review_id=review.performance_review_id,
        source_feedback_loop_packet_id=loop.feedback_loop_packet_id,
        source_payload_hash=publish.source_payload_hash,
        platform_id=publish.platform_id,
        payload_class_id=publish.payload_class_id,
        content_lane=review.content_lane,
        manual_publish_record_status=publish.manual_publish_record_status,
        metric_quality_class=review.metric_quality_class,
        performance_interpretation_class=review.performance_interpretation_class,
        feedback_loop_status=loop.feedback_loop_status,
        governance_status=status,
        public_postable=False,
        can_dispatch=False,
        can_auto_generate_content=False,
        can_approve=False,
        can_publish_public_claim=False,
        human_review_required=True,
        evidence_refs=_unique(tuple(publish.evidence_refs) + tuple(metrics.evidence_refs) + tuple(review.evidence_refs) + tuple(loop.evidence_refs)),
        safety_flags=safety_flags(),
        blocked_reasons=blockers,
        soft_caveats=soft_caveats,
    )


def _platform_summaries(rows: tuple[ContentGovernanceSummaryRow, ...]) -> tuple[PlatformGovernanceSummary, ...]:
    out: list[PlatformGovernanceSummary] = []
    for platform_id in sorted({row.platform_id for row in rows}):
        group = tuple(row for row in rows if row.platform_id == platform_id)
        out.append(PlatformGovernanceSummary(
            platform_id=platform_id,
            summary_row_count=len(group),
            manual_publish_record_count=len({row.source_manual_publish_record_id for row in group}),
            manual_metrics_record_count=len({row.source_manual_metrics_record_id for row in group}),
            performance_review_count=len({row.source_performance_review_id for row in group}),
            public_postable_count=sum(1 for row in group if row.public_postable),
            dispatch_ready_count=sum(1 for row in group if row.can_dispatch),
            review_only_count=sum(1 for row in group if row.governance_status == STATUS_LOCAL_SUMMARY_READY),
            blocked_count=sum(1 for row in group if row.governance_status == STATUS_BLOCKED),
            soft_caveats=_unique(caveat for row in group for caveat in row.soft_caveats),
        ))
    return tuple(out)


def _blocker_summaries(rows: tuple[ContentGovernanceSummaryRow, ...]) -> tuple[GovernanceBlockerSummary, ...]:
    blockers = sorted({reason for row in rows for reason in row.blocked_reasons})
    return tuple(
        GovernanceBlockerSummary(
            blocked_reason=reason,
            occurrence_count=sum(1 for row in rows if reason in row.blocked_reasons),
            source_row_ids=tuple(row.summary_row_id for row in rows if reason in row.blocked_reasons),
        )
        for reason in blockers
    )


def build_mart(
    uc_packet: uc.ManualPublishMetricsLedgerPacket | None = None,
    ud_packet: ud.ContentPerformanceReviewLedgerPacket | None = None,
) -> LocalContentGovernanceSummaryMartPacket:
    uc_packet = uc.build_contract_packet() if uc_packet is None else uc_packet
    ud_packet = ud.build_contract_packet() if ud_packet is None else ud_packet
    upstream_blockers = _unique(tuple(uc_packet.blocked_reasons) + tuple(ud_packet.blocked_reasons))
    caveats = _soft_caveats(ud_packet.audit_ledger_entries, upstream_blockers)
    rows = tuple(
        build_summary_row(publish, metrics, review, loop, soft_caveats=caveats)
        for publish, metrics, review, loop in zip(
            uc_packet.manual_publish_records,
            uc_packet.manual_metrics_records,
            ud_packet.performance_reviews,
            ud_packet.feedback_loop_packets,
            strict=True,
        )
    )
    evidence_refs = _unique(
        tuple(ref for row in rows for ref in row.evidence_refs)
        + tuple(uc_packet.evidence_refs)
        + tuple(ud_packet.evidence_refs)
        + (f"{DOC_REL_DIR.as_posix()}/{RUNBOOK_FILENAME}",)
    )
    all_audit_entries = tuple(uc_packet.audit_ledger_entries) + tuple(ud_packet.audit_ledger_entries)
    evidence_summary = EvidenceGovernanceSummary(
        evidence_ref_count=len(evidence_refs),
        audit_ledger_entry_count=len(all_audit_entries),
        all_records_redacted=all(entry.redacted_summary for entry in all_audit_entries),
        u9_unknown_or_blocked_entry_count=sum(1 for entry in ud_packet.audit_ledger_entries if entry.entry_family == "unknown_or_blocked"),
        u9_unknown_or_blocked_soft_caveat=SOFT_CAVEAT_0174UD_U9_UNKNOWN in caveats,
        retained_evidence_refs=evidence_refs,
    )
    blockers = _hard_blockers(
        _unique(tuple(uc_packet.blocked_reasons) + tuple(ud_packet.blocked_reasons) + tuple(reason for row in rows for reason in row.blocked_reasons))
    )
    public_postable_count = sum(1 for row in rows if row.public_postable)
    dispatch_ready_count = sum(1 for row in rows if row.can_dispatch)
    draft = {
        "summary_rows": rows,
        "platform_summaries": _platform_summaries(rows),
        "evidence_summary": evidence_summary,
        "blocker_summaries": _blocker_summaries(rows),
        "mart_status": STATUS_LOCAL_SUMMARY_READY if rows and public_postable_count == 0 and dispatch_ready_count == 0 else STATUS_BLOCKED,
        "all_rows_review_only": all(row.human_review_required and not row.public_postable for row in rows),
        "all_records_redacted": evidence_summary.all_records_redacted,
        "public_postable_count": public_postable_count,
        "dispatch_ready_count": dispatch_ready_count,
        "no_api_verification": uc_packet.no_api_verification and ud_packet.no_api_verification,
        "no_scraping": uc_packet.no_scraping and ud_packet.no_scraping,
        "no_auto_generation": ud_packet.no_auto_generation,
        "no_auto_publish": ud_packet.no_auto_publish,
        "no_dispatch": uc_packet.no_dispatch and ud_packet.no_dispatch and dispatch_ready_count == 0,
        "no_public_claim_authorized": uc_packet.no_public_claim_authorized and ud_packet.no_public_claim_authorized and public_postable_count == 0,
        "evidence_refs": evidence_refs,
        "safety_flags": safety_flags(),
        "blocked_reasons": blockers,
        "soft_caveats": caveats,
        "next_required_gate": NEXT_HEAVY_BATCH,
    }
    packet_hash = _digest(draft)
    return LocalContentGovernanceSummaryMartPacket(
        packet_id="local_content_governance_summary_mart_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft,
    )


def render_runbook(packet: LocalContentGovernanceSummaryMartPacket) -> str:
    summary = {
        "packet_id": packet.packet_id,
        "packet_hash": packet.packet_hash,
        "summary_rows": len(packet.summary_rows),
        "platform_summaries": len(packet.platform_summaries),
        "public_postable_count": packet.public_postable_count,
        "dispatch_ready_count": packet.dispatch_ready_count,
        "blocked_reasons": packet.blocked_reasons,
        "soft_caveats": packet.soft_caveats,
    }
    return "\n".join([
        "# 0174UE Local Content Governance Summary Mart Contract", "",
        f"- task_label: `{TASK_LABEL}`",
        f"- model_version: `{MODEL_VERSION}`",
        f"- source_baseline_commit: `{SOURCE_BASELINE_COMMIT}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`", "",
        "## Contract rules", "",
        "- Mart aggregates local 0174UC and 0174UD contract packets only.",
        "- Rows are review-only governance summaries, not UI state or publish truth.",
        "- Public postable, dispatch-ready, auto-generation, approval, and public claim authority remain false.",
        "- 0174UD U9 `unknown_or_blocked` audit families are preserved as soft caveats, not hard blockers.", "",
        "## Safety", "",
        "- No UI, API/provider/network/env/credential reads, scraping, browser, scheduler, DM/reply, dispatch, DQR/readiness clearing, current-truth promotion, or ingestion repo mutation.", "",
        "## Next heavy batch", "", f"`{NEXT_HEAVY_BATCH}`", "",
        "## Packet summary", "", "```json", json.dumps(summary, indent=2, sort_keys=True), "```", "",
    ])


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UE")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_mart()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


def contract_checksum() -> str:
    return build_mart().packet_hash
