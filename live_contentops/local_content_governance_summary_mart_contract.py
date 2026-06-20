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

from live_contentops import content_idea_intent_parser_contract as u4
from live_contentops import editorial_brief_ai_writer_output_contract as u5
from live_contentops import idea_to_multi_platform_draft_dry_run_contract as u6
from live_contentops import capital_chronicle_ingestion_headline_idea_connector_precheck as u7
from live_contentops import internal_alpha_artifact_intake_content_eligibility_contract as u8
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit  # U9
from live_contentops import approval_ledger_revocation_expiration_contract as ua
from live_contentops import dispatch_outbox_revalidation_gate_contract as ub
from live_contentops import manual_publish_record_metrics_ledger_contract as uc
from live_contentops import content_performance_review_editorial_feedback_contract as ud

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
class ContentPipelineSummaryRow:
    summary_row_id: str
    source_manual_publish_record_id: str
    source_manual_metrics_record_id: str
    source_performance_review_id: str
    source_feedback_loop_packet_id: str
    source_payload_hash: str
    platform_id: str
    payload_class_id: str
    content_lane: str
    idea_state: str
    brief_state: str
    writer_state: str
    preview_state: str
    substack_export_state: str
    dry_run_state: str
    artifact_eligibility_state: str
    approval_state: str
    revalidation_state: str
    manual_publish_state: str
    metrics_state: str
    performance_review_state: str
    editorial_feedback_state: str
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


ContentGovernanceSummaryRow = ContentPipelineSummaryRow


@dataclass(frozen=True)
class PlatformGovernanceSummaryRow:
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


PlatformGovernanceSummary = PlatformGovernanceSummaryRow


@dataclass(frozen=True)
class EvidenceGovernanceSummaryRow:
    evidence_family: str
    evidence_ref_count: int
    retained_evidence_refs: tuple[str, ...]
    audit_ledger_entry_count: int
    all_records_redacted: bool
    u9_unknown_or_blocked_entry_count: int
    u9_unknown_or_blocked_soft_caveat: bool


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
    hard_blockers: tuple[str, ...] = ()
    soft_caveats: tuple[str, ...] = ()


@dataclass(frozen=True)
class LocalContentGovernanceSummaryMartPacket:
    packet_id: str
    summary_rows: tuple[ContentPipelineSummaryRow, ...]
    pipeline_rows: tuple[ContentPipelineSummaryRow, ...]
    platform_summaries: tuple[PlatformGovernanceSummaryRow, ...]
    evidence_summaries: tuple[EvidenceGovernanceSummaryRow, ...]
    evidence_summary: EvidenceGovernanceSummary
    blocker_summaries: tuple[GovernanceBlockerSummary, ...]
    packet_hash: str
    packet_hash_algorithm: str
    mart_status: str
    overall_status: str
    all_rows_review_only: bool
    all_records_redacted: bool
    public_postable_count: int
    dispatch_ready_count: int
    approval_ready_count: int
    current_truth_promoted_count: int
    dqr_cleared_count: int
    readiness_cleared_count: int
    no_api_verification: bool
    no_scraping: bool
    no_auto_generation: bool
    no_auto_publish: bool
    no_dispatch: bool
    no_public_claim_authorized: bool
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
    hard_blockers: tuple[str, ...]
    soft_caveats: tuple[str, ...]
    next_required_gate: str


LocalContentGovernanceSummaryMart = LocalContentGovernanceSummaryMartPacket


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


def _soft_caveats(entries: tuple[audit.RedactedAuditLedgerEntry, ...] | list[dict[str, Any]], blockers: tuple[str, ...] = ()) -> tuple[str, ...]:
    caveats: list[str] = []
    # Check entries which might be dicts or dataclasses
    for entry in entries:
        family = entry.get("entry_family") if isinstance(entry, dict) else getattr(entry, "entry_family", None)
        model = entry.get("source_model") if isinstance(entry, dict) else getattr(entry, "source_model", None)
        if family == "unknown_or_blocked" and model == "0174UD":
            caveats.append(SOFT_CAVEAT_0174UD_U9_UNKNOWN)
    if any(blocker in UPSTREAM_PRESERVED_BLOCKERS for blocker in blockers):
        caveats.append(SOFT_CAVEAT_UPSTREAM_FUTURE_SEND)
    return _unique(caveats)


def _hard_blockers(blockers: tuple[str, ...]) -> tuple[str, ...]:
    return _unique(blocker for blocker in blockers if blocker not in UPSTREAM_PRESERVED_BLOCKERS)


def detect_forged_states(*packets: Any) -> list[str]:
    blockers: list[str] = []
    checks = {
        "public_postable": "forged_public_postable_blocked",
        "dispatch_ready": "forged_dispatch_ready_blocked",
        "can_dispatch": "forged_can_dispatch_blocked",
        "can_approve": "forged_can_approve_blocked",
        "can_create_approval": "forged_can_approve_blocked",
        "approval_granted": "forged_can_approve_blocked",
        "current_truth_promoted": "forged_current_truth_promoted_blocked",
        "dqr_cleared": "forged_dqr_cleared_blocked",
        "readiness_cleared": "forged_readiness_cleared_blocked",
        "public_claim_authorized": "forged_public_claim_authorized_blocked",
        "approved_for_public_claim": "forged_public_claim_authorized_blocked",
    }
    visited: set[int] = set()

    def scan(item: Any):
        if item is None:
            return
        ref_id = id(item)
        if ref_id in visited:
            return
        visited.add(ref_id)

        if isinstance(item, (str, int, float, bool)):
            return
        if isinstance(item, (list, tuple)):
            for val in item:
                scan(val)
            return
        if isinstance(item, dict):
            for k, v in item.items():
                if k in checks and v is True:
                    blockers.append(checks[k])
                scan(v)
            return
        if hasattr(item, "__dataclass_fields__"):
            for field in item.__dataclass_fields__:
                val = getattr(item, field)
                if field in checks and val is True:
                    blockers.append(checks[field])
                scan(val)
            return
        # General object traversal
        for attr in dir(item):
            if attr.startswith("_"):
                continue
            try:
                val = getattr(item, attr)
                if attr in checks and val is True:
                    blockers.append(checks[attr])
                if not callable(val):
                    scan(val)
            except Exception:
                pass

    for p in packets:
        scan(p)
    return list(dict.fromkeys(blockers))


def build_summary_row(
    publish: uc.ManualPublishRecord,
    metrics: uc.ManualMetricsRecord,
    review: ud.ContentPerformanceReviewPacket,
    loop: ud.EditorialFeedbackLoopPacket,
    *,
    soft_caveats: tuple[str, ...] = (),
    forged_blockers: tuple[str, ...] = (),
    u4_data: dict[str, Any] | None = None,
    u5_data: dict[str, Any] | None = None,
    u6_data: Any = None,
    u8_data: dict[str, Any] | None = None,
    ua_data: Any = None,
    ub_data: Any = None,
) -> ContentPipelineSummaryRow:
    u4_data = u4_data or {}
    u5_data = u5_data or {}
    u8_data = u8_data or {}

    idea_state = u4_data.get("sample_idea_packet", {}).get("readiness_state", "idea_ready_for_review")
    brief_state = u5_data.get("sample_editorial_brief", {}).get("output_status", "review_only")
    writer_state = u5_data.get("sample_ai_writer_output", {}).get("writer_mode", "deterministic_fixture")

    preview_state = "preview_only"
    if u6_data and hasattr(u6_data, "preview_bundle") and u6_data.preview_bundle and u6_data.preview_bundle.previews:
        preview_state = "platform_payload_preview"

    substack_export_state = "manual_export_only"
    if u6_data and hasattr(u6_data, "substack_exports") and u6_data.substack_exports:
        substack_export_state = "substack_manual_export"

    dry_run_state = "review_only_dry_run_valid"
    if u6_data and hasattr(u6_data, "validation") and u6_data.validation:
        dry_run_state = u6_data.validation.validation_status

    artifact_eligibility_state = u8_data.get("eligibility_report", {}).get("source_requirement_status", "source_provided_context_only")

    approval_state = "approval_ledger_fact"
    if ua_data and hasattr(ua_data, "validity_assessments") and ua_data.validity_assessments:
        assessment = ua_data.validity_assessments[0]
        approval_state = assessment.blocked_reasons[0] if assessment.blocked_reasons else "approval_still_valid"

    revalidation_state = "locally_revalidated_but_dispatch_future_gate"
    if ub_data and hasattr(ub_data, "revalidation_results") and ub_data.revalidation_results:
        revalidation_state = ub_data.revalidation_results[0].revalidation_status

    upstream_blockers = _unique(
        tuple(publish.blocked_reasons) + tuple(metrics.blocked_reasons) +
        tuple(review.blocked_reasons) + tuple(loop.blocked_reasons) + forged_blockers
    )
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
    return ContentPipelineSummaryRow(
        summary_row_id="content_governance_summary_row_" + _digest(material)[:24],
        source_manual_publish_record_id=publish.manual_publish_record_id,
        source_manual_metrics_record_id=metrics.manual_metrics_record_id,
        source_performance_review_id=review.performance_review_id,
        source_feedback_loop_packet_id=loop.feedback_loop_packet_id,
        source_payload_hash=publish.source_payload_hash,
        platform_id=publish.platform_id,
        payload_class_id=publish.payload_class_id,
        content_lane=review.content_lane,
        idea_state=idea_state,
        brief_state=brief_state,
        writer_state=writer_state,
        preview_state=preview_state,
        substack_export_state=substack_export_state,
        dry_run_state=dry_run_state,
        artifact_eligibility_state=artifact_eligibility_state,
        approval_state=approval_state,
        revalidation_state=revalidation_state,
        manual_publish_state=publish.manual_publish_record_status,
        metrics_state=metrics.metric_source_class,
        performance_review_state=review.metric_quality_class,
        editorial_feedback_state=loop.feedback_loop_status,
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


def _platform_summaries(rows: tuple[ContentPipelineSummaryRow, ...]) -> tuple[PlatformGovernanceSummaryRow, ...]:
    platforms = (
        "x", "telegram_remote_operator", "telegram_channel_destination",
        "substack_newsletter", "linkedin", "threads", "instagram",
        "facebook_page", "tiktok", "youtube"
    )
    out: list[PlatformGovernanceSummaryRow] = []
    for platform_id in platforms:
        group = tuple(row for row in rows if row.platform_id == platform_id)
        out.append(PlatformGovernanceSummaryRow(
            platform_id=platform_id,
            summary_row_count=len(group),
            manual_publish_record_count=len({row.source_manual_publish_record_id for row in group if row.source_manual_publish_record_id}),
            manual_metrics_record_count=len({row.source_manual_metrics_record_id for row in group if row.source_manual_metrics_record_id}),
            performance_review_count=len({row.source_performance_review_id for row in group if row.source_performance_review_id}),
            public_postable_count=sum(1 for row in group if row.public_postable),
            dispatch_ready_count=sum(1 for row in group if row.can_dispatch),
            review_only_count=sum(1 for row in group if row.governance_status == STATUS_LOCAL_SUMMARY_READY),
            blocked_count=sum(1 for row in group if row.governance_status == STATUS_BLOCKED),
            soft_caveats=_unique(caveat for row in group for caveat in row.soft_caveats),
        ))
    return tuple(out)


def _evidence_summaries(
    u4_data: dict[str, Any], u5_data: dict[str, Any], u6_data: Any,
    u7_data: dict[str, Any], u8_data: dict[str, Any], u9_data: dict[str, Any],
    ua_data: Any, ub_data: Any, uc_data: Any, ud_data: Any
) -> tuple[EvidenceGovernanceSummaryRow, ...]:
    families = (
        "idea_intent", "editorial_writer", "dry_run_preview", "ingestion_context",
        "artifact_eligibility", "redacted_audit_ledger", "approval_validity",
        "dispatch_revalidation", "manual_publish_metrics", "performance_feedback"
    )

    u9_entries = u9_data.get("ledger_chain", {}).get("entries", [])

    family_to_entry_families = {
        "idea_intent": ("raw_operator_input", "content_idea", "local_intent"),
        "editorial_writer": ("editorial_brief", "ai_writer_output", "draft_variant"),
        "dry_run_preview": ("platform_payload_preview", "substack_manual_export", "multi_platform_dry_run"),
        "ingestion_context": ("ingestion_context_candidate", "headline_context_packet"),
        "artifact_eligibility": ("internal_alpha_artifact_intake", "content_eligibility_assessment", "artifact_idea_seed"),
        "redacted_audit_ledger": ("unknown_or_blocked",),
        "approval_validity": ("approval_ledger_fact",),
        "dispatch_revalidation": ("dispatch_outbox_fact",),
        "manual_publish_metrics": ("manual_publish_record_future_gate", "metrics_record_future_gate"),
        "performance_feedback": ("content_performance_review", "editorial_feedback_signal", "editorial_feedback_loop", "content_performance_validation"),
    }

    out: list[EvidenceGovernanceSummaryRow] = []
    for fam in families:
        refs: tuple[str, ...] = ()
        if fam == "idea_intent":
            refs = _unique(u4_data.get("sample_idea_packet", {}).get("evidence_refs", ()))
        elif fam == "editorial_writer":
            refs = _unique(u5_data.get("sample_editorial_brief", {}).get("evidence_refs", ()))
        elif fam == "dry_run_preview":
            refs = ()
            if u6_data:
                refs_list = []
                for attr in ("raw_input", "idea_packet", "intent_packet", "editorial_brief", "writer_output"):
                    if hasattr(u6_data, attr):
                        sub_obj = getattr(u6_data, attr)
                        if hasattr(sub_obj, "evidence_refs"):
                            refs_list.extend(sub_obj.evidence_refs)
                refs = _unique(refs_list)
        elif fam == "ingestion_context":
            refs = _unique(u7_data.get("precheck_report", {}).get("evidence_refs", ()))
        elif fam == "artifact_eligibility":
            refs = _unique(u8_data.get("eligibility_report", {}).get("evidence_refs", ()))
        elif fam == "redacted_audit_ledger":
            refs = _unique(u9_data.get("validation_result", {}).get("evidence_refs", ()))
        elif fam == "approval_validity":
            refs = _unique(ua_data.evidence_refs if ua_data and hasattr(ua_data, "evidence_refs") else ())
        elif fam == "dispatch_revalidation":
            refs = _unique(ub_data.evidence_refs if ub_data and hasattr(ub_data, "evidence_refs") else ())
        elif fam == "manual_publish_metrics":
            refs = _unique(uc_data.evidence_refs if uc_data and hasattr(uc_data, "evidence_refs") else ())
        elif fam == "performance_feedback":
            refs = _unique(ud_data.evidence_refs if ud_data and hasattr(ud_data, "evidence_refs") else ())

        mapped_families = family_to_entry_families.get(fam, ())
        matching_entries = [e for e in u9_entries if e.get("entry_family") in mapped_families]

        if fam == "performance_feedback":
            ud_entries = ud_data.audit_ledger_entries if hasattr(ud_data, "audit_ledger_entries") else ud_data.get("audit_ledger_entries", ())
            matching_entries = [
                _asdict(e) if hasattr(e, "__dataclass_fields__") else e
                for e in ud_entries
                if (_asdict(e) if hasattr(e, "__dataclass_fields__") else e).get("entry_family") in mapped_families
                or (_asdict(e) if hasattr(e, "__dataclass_fields__") else e).get("entry_family") == "unknown_or_blocked"
            ]
        elif fam == "redacted_audit_ledger":
            matching_entries = list(u9_entries)

        u9_unknown_count = sum(1 for e in matching_entries if e.get("entry_family") == "unknown_or_blocked")
        ud_soft = (fam == "performance_feedback" and u9_unknown_count > 0)

        out.append(EvidenceGovernanceSummaryRow(
            evidence_family=fam,
            evidence_ref_count=len(refs),
            retained_evidence_refs=refs,
            audit_ledger_entry_count=len(matching_entries),
            all_records_redacted=all(e.get("redacted_summary", True) for e in matching_entries),
            u9_unknown_or_blocked_entry_count=u9_unknown_count,
            u9_unknown_or_blocked_soft_caveat=ud_soft
        ))
    return tuple(out)


def _blocker_summaries(rows: tuple[ContentPipelineSummaryRow, ...], hard_blockers: tuple[str, ...], soft_caveats: tuple[str, ...]) -> tuple[GovernanceBlockerSummary, ...]:
    reasons = sorted({reason for row in rows for reason in row.blocked_reasons})
    return tuple(
        GovernanceBlockerSummary(
            blocked_reason=reason,
            occurrence_count=sum(1 for row in rows if reason in row.blocked_reasons),
            source_row_ids=tuple(row.summary_row_id for row in rows if reason in row.blocked_reasons),
            hard_blockers=hard_blockers,
            soft_caveats=soft_caveats
        )
        for reason in reasons
    )


def build_mart(
    u4_packet: dict[str, Any] | None = None,
    u5_packet: dict[str, Any] | None = None,
    u6_packet: u6.MultiPlatformDraftDryRunPacket | None = None,
    u7_packet: dict[str, Any] | None = None,
    u8_packet: dict[str, Any] | None = None,
    u9_packet: dict[str, Any] | None = None,
    ua_packet: ua.ApprovalRevocationExpirationLedgerPacket | None = None,
    ub_packet: ub.DispatchOutboxRevalidationGatePacket | None = None,
    uc_packet: uc.ManualPublishMetricsLedgerPacket | None = None,
    ud_packet: ud.ContentPerformanceReviewLedgerPacket | None = None,
) -> LocalContentGovernanceSummaryMartPacket:
    u4_data = u4_packet or u4.build_contract_packet()
    u5_data = u5_packet or u5.build_contract_packet()
    u6_data = u6_packet or u6.build_dry_run_from_text("Draft an X thread and Substack newsletter about source trust during manual review. Limitation: review-only local dry run.")
    u7_data = u7_packet or u7.build_contract_packet(".")
    u8_data = u8_packet or u8.build_contract_packet()
    u9_data = u9_packet or audit.build_contract_packet()
    ua_data = ua_packet or ua.build_ledger_packet()
    ub_data = ub_packet or ub.build_revalidation_gate_packet()
    uc_data = uc_packet or uc.build_contract_packet()
    ud_data = ud_packet or ud.build_contract_packet()

    all_packets = (u4_data, u5_data, u6_data, u7_data, u8_data, u9_data, ua_data, ub_data, uc_data, ud_data)
    forged_blockers = tuple(detect_forged_states(*all_packets))

    pub_records = uc_data.manual_publish_records if hasattr(uc_data, "manual_publish_records") else uc_data.get("manual_publish_records", ())
    ud_entries = ud_data.audit_ledger_entries if hasattr(ud_data, "audit_ledger_entries") else ud_data.get("audit_ledger_entries", ())
    upstream_blockers = _unique(
        tuple(uc_data.blocked_reasons if hasattr(uc_data, "blocked_reasons") else uc_data.get("blocked_reasons", ()))
        + tuple(ud_data.blocked_reasons if hasattr(ud_data, "blocked_reasons") else ud_data.get("blocked_reasons", ()))
        + forged_blockers
    )
    caveats = _soft_caveats(ud_entries, upstream_blockers)
    hard_blockers_list = _hard_blockers(upstream_blockers)

    rows = tuple(
        build_summary_row(publish, metrics, review, loop, soft_caveats=caveats, forged_blockers=forged_blockers,
                          u4_data=u4_data, u5_data=u5_data, u6_data=u6_data, u8_data=u8_data, ua_data=ua_data, ub_data=ub_data)
        for publish, metrics, review, loop in zip(
            pub_records,
            uc_data.manual_metrics_records if hasattr(uc_data, "manual_metrics_records") else uc_data.get("manual_metrics_records", ()),
            ud_data.performance_reviews if hasattr(ud_data, "performance_reviews") else ud_data.get("performance_reviews", ()),
            ud_data.feedback_loop_packets if hasattr(ud_data, "feedback_loop_packets") else ud_data.get("feedback_loop_packets", ()),
            strict=True,
        )
    )

    evidence_refs = _unique(
        tuple(ref for row in rows for ref in row.evidence_refs)
        + tuple(uc_data.evidence_refs if hasattr(uc_data, "evidence_refs") else uc_data.get("evidence_refs", ()))
        + tuple(ud_data.evidence_refs if hasattr(ud_data, "evidence_refs") else ud_data.get("evidence_refs", ()))
        + (f"{DOC_REL_DIR.as_posix()}/{RUNBOOK_FILENAME}",)
    )

    all_audit_entries = tuple(uc_data.audit_ledger_entries if hasattr(uc_data, "audit_ledger_entries") else uc_data.get("audit_ledger_entries", ())) + tuple(ud_entries)
    evidence_summary = EvidenceGovernanceSummary(
        evidence_ref_count=len(evidence_refs),
        audit_ledger_entry_count=len(all_audit_entries),
        all_records_redacted=all(entry.redacted_summary if hasattr(entry, "redacted_summary") else entry.get("redacted_summary", True) for entry in all_audit_entries),
        u9_unknown_or_blocked_entry_count=sum(1 for entry in ud_entries if (entry.entry_family if hasattr(entry, "entry_family") else entry.get("entry_family")) == "unknown_or_blocked"),
        u9_unknown_or_blocked_soft_caveat=SOFT_CAVEAT_0174UD_U9_UNKNOWN in caveats,
        retained_evidence_refs=evidence_refs,
    )

    evidence_summaries_list = _evidence_summaries(u4_data, u5_data, u6_data, u7_data, u8_data, u9_data, ua_data, ub_data, uc_data, ud_data)

    public_postable_count = sum(1 for row in rows if row.public_postable)
    dispatch_ready_count = sum(1 for row in rows if row.can_dispatch)
    approval_ready_count = 0
    current_truth_promoted_count = 0
    dqr_cleared_count = 0
    readiness_cleared_count = 0

    mart_status = STATUS_LOCAL_SUMMARY_READY if rows and public_postable_count == 0 and dispatch_ready_count == 0 and not hard_blockers_list else STATUS_BLOCKED

    draft = {
        "summary_rows": rows,
        "pipeline_rows": rows,
        "platform_summaries": _platform_summaries(rows),
        "evidence_summaries": evidence_summaries_list,
        "evidence_summary": evidence_summary,
        "blocker_summaries": _blocker_summaries(rows, hard_blockers_list, caveats),
        "mart_status": mart_status,
        "overall_status": mart_status,
        "all_rows_review_only": all(row.human_review_required and not row.public_postable for row in rows),
        "all_records_redacted": evidence_summary.all_records_redacted,
        "public_postable_count": public_postable_count,
        "dispatch_ready_count": dispatch_ready_count,
        "approval_ready_count": approval_ready_count,
        "current_truth_promoted_count": current_truth_promoted_count,
        "dqr_cleared_count": dqr_cleared_count,
        "readiness_cleared_count": readiness_cleared_count,
        "no_api_verification": (uc_data.no_api_verification if hasattr(uc_data, "no_api_verification") else uc_data.get("no_api_verification", True)) and (ud_data.no_api_verification if hasattr(ud_data, "no_api_verification") else ud_data.get("no_api_verification", True)),
        "no_scraping": (uc_data.no_scraping if hasattr(uc_data, "no_scraping") else uc_data.get("no_scraping", True)) and (ud_data.no_scraping if hasattr(ud_data, "no_scraping") else ud_data.get("no_scraping", True)),
        "no_auto_generation": ud_data.no_auto_generation if hasattr(ud_data, "no_auto_generation") else ud_data.get("no_auto_generation", True),
        "no_auto_publish": ud_data.no_auto_publish if hasattr(ud_data, "no_auto_publish") else ud_data.get("no_auto_publish", True),
        "no_dispatch": (uc_data.no_dispatch if hasattr(uc_data, "no_dispatch") else uc_data.get("no_dispatch", True)) and (ud_data.no_dispatch if hasattr(ud_data, "no_dispatch") else ud_data.get("no_dispatch", True)) and dispatch_ready_count == 0,
        "no_public_claim_authorized": (uc_data.no_public_claim_authorized if hasattr(uc_data, "no_public_claim_authorized") else uc_data.get("no_public_claim_authorized", True)) and (ud_data.no_public_claim_authorized if hasattr(ud_data, "no_public_claim_authorized") else ud_data.get("no_public_claim_authorized", True)) and public_postable_count == 0,
        "evidence_refs": evidence_refs,
        "safety_flags": safety_flags(),
        "blocked_reasons": hard_blockers_list,
        "hard_blockers": hard_blockers_list,
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
        "evidence_summaries": len(packet.evidence_summaries),
        "public_postable_count": packet.public_postable_count,
        "dispatch_ready_count": packet.dispatch_ready_count,
        "approval_ready_count": packet.approval_ready_count,
        "current_truth_promoted_count": packet.current_truth_promoted_count,
        "dqr_cleared_count": packet.dqr_cleared_count,
        "readiness_cleared_count": packet.readiness_cleared_count,
        "blocked_reasons": packet.blocked_reasons,
        "hard_blockers": packet.hard_blockers,
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
        "- Mart aggregates local U4 through UD contract packets.",
        "- Rows are review-only governance summaries, not UI state or publish truth.",
        "- Public postable, dispatch-ready, auto-generation, approval, and public claim authority remain false.",
        "- Explicit U9 performance-feedback audit families prevent default `unknown_or_blocked` caveats for current 0174UD packets.", "",
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
