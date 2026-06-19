"""Manual publish record + metrics ledger contract, 0174UC.

Deterministic local-only evidence records for human manual publication and
operator-entered metrics. No platform/provider API, no network/env/credential,
no scraping/browser/scheduler/DM behavior, no dispatch, no public claim authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from live_contentops import dispatch_outbox_revalidation_gate_contract as revalidation
from live_contentops import platform_universe_registry_v2 as registry
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit

TASK_LABEL = "TASK_CONTENTOPS_0174UC_MANUAL_PUBLISH_RECORD_AND_METRICS_LEDGER_CONTRACT_V0"
MODEL_VERSION = "0174UC_MANUAL_PUBLISH_RECORD_METRICS_LEDGER_CONTRACT_V1"
SOURCE_BASELINE_COMMIT = "f11beb3ffe87509c8485a7a5eb82b6616bc6ffcd"
DOC_REL_DIR = Path("docs") / "automation" / "0174UC"
PACKET_FILENAME = "manual_publish_record_metrics_ledger_contract_packet.json"
RUNBOOK_FILENAME = "manual_publish_record_metrics_ledger_contract.md"
HASH_ALGORITHM = "sha256"
NEXT_HEAVY_BATCH = "TASK_CONTENTOPS_0174UD_CONTENT_PERFORMANCE_REVIEW_AND_EDITORIAL_FEEDBACK_LOOP_CONTRACT_V0"

MODE_OPERATOR_COPY = "operator_manual_copy_paste"
MODE_OPERATOR_SUBSTACK = "operator_manual_substack_publish"
MODE_OPERATOR_PLATFORM = "operator_manual_platform_publish"
MODE_UNKNOWN = "unknown_or_blocked"
PUBLISH_MODES = (MODE_OPERATOR_COPY, MODE_OPERATOR_SUBSTACK, MODE_OPERATOR_PLATFORM, MODE_UNKNOWN)

CLAIM_OPERATOR_ATTESTED = "operator_attested_only"
CLAIM_URL_NOT_VERIFIED = "url_recorded_not_verified"
CLAIM_FUTURE_VERIFICATION = "future_verification_required"
CLAIM_UNKNOWN = "unknown_or_blocked"
CLAIM_CLASSES = (CLAIM_OPERATOR_ATTESTED, CLAIM_URL_NOT_VERIFIED, CLAIM_FUTURE_VERIFICATION, CLAIM_UNKNOWN)

STATUS_RECORDED_REVIEW_ONLY = "recorded_review_only"
STATUS_BLOCKED_MISSING_PAYLOAD_HASH = "blocked_missing_payload_hash"
STATUS_BLOCKED_MISSING_URL_HASH = "blocked_missing_url_hash"
STATUS_BLOCKED_REVALIDATION_NOT_LOCAL_PASS = "blocked_revalidation_not_local_pass"
STATUS_BLOCKED_UNKNOWN_PLATFORM = "blocked_unknown_platform"
STATUS_BLOCKED_UNKNOWN_PUBLISH_MODE = "blocked_unknown_publish_mode"
STATUS_UNKNOWN = "unknown_or_blocked"

METRIC_SOURCE_OPERATOR = "operator_manual_entry"
METRIC_SOURCE_PLATFORM_UI = "platform_ui_manual_read"
METRIC_SOURCE_FUTURE_API_BLOCKED = "future_api_import_blocked"
METRIC_SOURCE_UNKNOWN = "unknown_or_blocked"
METRIC_SOURCE_CLASSES = (
    METRIC_SOURCE_OPERATOR, METRIC_SOURCE_PLATFORM_UI,
    METRIC_SOURCE_FUTURE_API_BLOCKED, METRIC_SOURCE_UNKNOWN,
)

BLOCK_MISSING_PAYLOAD_HASH = "missing_payload_hash"
BLOCK_MISSING_URL_HASH = "missing_url_hash"
BLOCK_UNKNOWN_PLATFORM = "unknown_platform_fail_closed"
BLOCK_UNKNOWN_PAYLOAD_CLASS = "unknown_payload_class_fail_closed"
BLOCK_UNKNOWN_PUBLISH_MODE = "unknown_manual_publish_mode_fail_closed"
BLOCK_REVALIDATION_NOT_LOCAL_PASS = "revalidation_not_local_pass"
BLOCK_FUTURE_GATE_NOT_PRESERVED = "revalidation_future_gate_not_preserved"
BLOCK_API_VERIFICATION_CLAIM = "api_verification_claim_blocked"
BLOCK_PUBLIC_CLAIM = "public_claim_authorized_blocked"
BLOCK_DISPATCH = "dispatch_or_public_postable_blocked"
BLOCK_NO_LIVE = "live_behavior_blocked"
BLOCK_PAYLOAD_HASH_MISMATCH = "metrics_payload_hash_mismatch"
BLOCK_PLATFORM_MISMATCH = "metrics_platform_mismatch"
BLOCK_METRIC_TIME_ORDER = "metric_time_order_invalid"
BLOCK_NEGATIVE_METRIC = "negative_numeric_metric"
BLOCK_FUTURE_API_IMPORT = "future_api_import_mode_blocked"
BLOCK_METRICS_NOT_ATTESTED = "metrics_not_operator_attested_only"
BLOCK_METRICS_API_VERIFIED = "metrics_api_verified_blocked"
BLOCK_METRICS_SCRAPED = "metrics_scraped_blocked"

NUMERIC_METRIC_KEYS = (
    "impressions", "views", "likes", "comments", "shares", "reposts",
    "saves", "clicks", "opens", "subscribers_delta",
)
@dataclass(frozen=True)
class ManualPublishRecord:
    manual_publish_record_id: str
    source_revalidation_result_id: str
    source_outbox_entry_id: str
    source_payload_hash: str
    platform_id: str
    payload_class_id: str
    destination_binding_id: str
    credential_handle_id: str
    operator_identity_ref: str
    manually_published_at_epoch: int
    manual_publish_url_redacted: str
    manual_publish_url_hash: str
    manual_publish_url_hash_algorithm: str
    manual_publish_mode: str
    publication_claim_class: str
    source_revalidation_status: str
    source_revalidation_future_gate_required: bool
    manual_publish_record_status: str
    human_review_required: bool
    public_claim_authorized: bool
    can_dispatch: bool
    dispatch_ready: bool
    public_postable: bool
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ManualPublishRecordValidationResult:
    validation_id: str
    source_manual_publish_record_id: str
    payload_hash_present: bool
    url_hash_present: bool
    platform_known: bool
    payload_class_known: bool
    destination_binding_present: bool
    credential_handle_present: bool
    operator_ref_present: bool
    revalidation_result_bound: bool
    revalidation_future_gate_preserved: bool
    no_api_verification_claim: bool
    no_public_claim_authorized: bool
    no_dispatch: bool
    no_live_behavior: bool
    validation_status: str
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]


@dataclass(frozen=True)
class ManualMetricsRecord:
    manual_metrics_record_id: str
    source_manual_publish_record_id: str
    source_payload_hash: str
    platform_id: str
    metric_observed_at_epoch: int
    metric_recorded_at_epoch: int
    operator_identity_ref: str
    metric_source_class: str
    metrics: dict[str, Any]
    metric_values_are_operator_attested: bool
    metric_values_are_api_verified: bool
    metric_values_are_scraped: bool
    metric_url_hash: str
    metric_notes_redacted: str
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ManualMetricsValidationResult:
    validation_id: str
    source_metrics_record_id: str
    source_publish_record_id: str
    payload_hash_match: bool
    platform_match: bool
    metric_time_order_valid: bool
    non_negative_metrics: bool
    operator_attested_only: bool
    api_verified_false: bool
    scraped_false: bool
    no_live_behavior: bool
    validation_status: str
    blocked_reasons: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]


@dataclass(frozen=True)
class ManualPublishMetricsLedgerPacket:
    packet_id: str
    manual_publish_records: tuple[ManualPublishRecord, ...]
    manual_publish_validations: tuple[ManualPublishRecordValidationResult, ...]
    manual_metrics_records: tuple[ManualMetricsRecord, ...]
    manual_metrics_validations: tuple[ManualMetricsValidationResult, ...]
    audit_ledger_entries: tuple[audit.RedactedAuditLedgerEntry, ...]
    packet_hash: str
    packet_hash_algorithm: str
    all_records_redacted: bool
    all_records_manual_only: bool
    no_api_verification: bool
    no_scraping: bool
    no_dispatch: bool
    no_public_claim_authorized: bool
    evidence_refs: tuple[str, ...]
    safety_flags: dict[str, bool]
    blocked_reasons: tuple[str, ...]
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
    return {
        "manual_record_only": True,
        "operator_attested_only": True,
        "url_verified_by_system": False,
        "metrics_api_verified": False,
        "metrics_scraped": False,
        "can_dispatch": False,
        "dispatch_ready": False,
        "public_postable": False,
        "public_claim_authorized": False,
        "approval_granted": False,
        "live_dispatch_enabled": False,
        "platform_api_called": False,
        "telegram_api_called": False,
        "provider_api_called": False,
        "llm_provider_called": False,
        "credential_hydrated": False,
        "env_read": False,
        "network_performed": False,
        "scheduler_enabled": False,
        "autonomous_posting_allowed": False,
        "scraping_performed": False,
        "dm_or_reply_automation_allowed": False,
        "browser_session_used": False,
        "current_truth_promoted": False,
        "dqr_cleared": False,
        "readiness_cleared": False,
        "ingestion_repo_mutated": False,
    }


_SECRET_PAIR_RE = re.compile(r"(?i)(token|secret|api_key|key|password|bearer|code)=([^&\s]+)")
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")


def redact_url(raw_url: str) -> str:
    value = str(raw_url or "")
    if not value:
        return ""
    base = value.split("?", 1)[0].split("#", 1)[0]
    return _SECRET_PAIR_RE.sub(r"\1=[REDACTED]", base)


def hash_url(raw_url: str) -> str:
    if not raw_url:
        return ""
    return sha256(str(raw_url).encode("utf-8")).hexdigest()


def redact_notes(notes: str) -> str:
    value = str(notes or "")
    value = _SECRET_PAIR_RE.sub(r"\1=[REDACTED]", value)
    value = _EMAIL_RE.sub("[REDACTED_EMAIL]", value)
    value = _PHONE_RE.sub("[REDACTED_PHONE]", value)
    return value


def _future_gate_required(result: revalidation.DispatchRevalidationResult) -> bool:
    return (
        result.revalidation_status == revalidation.STATUS_LOCAL_REVALIDATED_FUTURE_GATE
        and revalidation.BLOCK_FUTURE_SEND_GATE_REQUIRED in result.blocked_reasons
    )


def _publish_status(blockers: tuple[str, ...]) -> str:
    if BLOCK_MISSING_PAYLOAD_HASH in blockers:
        return STATUS_BLOCKED_MISSING_PAYLOAD_HASH
    if BLOCK_MISSING_URL_HASH in blockers:
        return STATUS_BLOCKED_MISSING_URL_HASH
    if BLOCK_REVALIDATION_NOT_LOCAL_PASS in blockers:
        return STATUS_BLOCKED_REVALIDATION_NOT_LOCAL_PASS
    if BLOCK_UNKNOWN_PLATFORM in blockers:
        return STATUS_BLOCKED_UNKNOWN_PLATFORM
    if BLOCK_UNKNOWN_PUBLISH_MODE in blockers:
        return STATUS_BLOCKED_UNKNOWN_PUBLISH_MODE
    hard = [b for b in blockers if b not in {
        revalidation.BLOCK_FUTURE_SEND_GATE_REQUIRED,
        revalidation.BLOCK_NO_DISPATCH,
        "dispatch_revalidation_required_future_0174UB",
    }]
    return STATUS_RECORDED_REVIEW_ONLY if not hard else STATUS_UNKNOWN


def _payload_class_known(payload_class_id: str) -> bool:
    return payload_class_id in registry.PAYLOAD_CLASSES_BY_ID


def _platform_known(platform_id: str) -> bool:
    return platform_id in registry.PLATFORMS_BY_ID


def _non_negative_metrics(metrics: dict[str, Any]) -> bool:
    for key in NUMERIC_METRIC_KEYS:
        if key not in metrics or metrics.get(key) is None:
            continue
        value = metrics[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if value < 0:
            return False
    return True


def build_manual_publish_record(
    *,
    revalidation_result: revalidation.DispatchRevalidationResult,
    candidate: revalidation.DispatchRevalidationCandidate,
    operator_identity_ref: str,
    manually_published_at_epoch: int,
    manual_publish_url: str,
    manual_publish_mode: str,
    publication_claim_class: str = CLAIM_OPERATOR_ATTESTED,
    evidence_refs: tuple[str, ...] = (),
) -> ManualPublishRecord:
    url_hash = hash_url(manual_publish_url)
    future_gate = _future_gate_required(revalidation_result)
    blockers = list(revalidation_result.blocked_reasons)
    if not candidate.candidate_payload_hash:
        blockers.append(BLOCK_MISSING_PAYLOAD_HASH)
    if not url_hash:
        blockers.append(BLOCK_MISSING_URL_HASH)
    if not _platform_known(candidate.platform_id):
        blockers.append(BLOCK_UNKNOWN_PLATFORM)
    if not _payload_class_known(candidate.payload_class_id):
        blockers.append(BLOCK_UNKNOWN_PAYLOAD_CLASS)
    if manual_publish_mode not in PUBLISH_MODES or manual_publish_mode == MODE_UNKNOWN:
        manual_publish_mode = MODE_UNKNOWN
        blockers.append(BLOCK_UNKNOWN_PUBLISH_MODE)
    if not future_gate:
        blockers.append(BLOCK_REVALIDATION_NOT_LOCAL_PASS)
    if publication_claim_class not in CLAIM_CLASSES or publication_claim_class == CLAIM_UNKNOWN:
        publication_claim_class = CLAIM_UNKNOWN
        blockers.append(BLOCK_API_VERIFICATION_CLAIM)
    if not operator_identity_ref:
        blockers.append("missing_operator_identity_ref")
    normalized = _unique(blockers)
    basis = {
        "source_revalidation_result_id": revalidation_result.revalidation_result_id,
        "source_outbox_entry_id": candidate.outbox_entry_id,
        "source_payload_hash": candidate.candidate_payload_hash,
        "platform_id": candidate.platform_id,
        "payload_class_id": candidate.payload_class_id,
        "destination_binding_id": candidate.destination_binding_id,
        "credential_handle_id": candidate.credential_handle_id,
        "operator_identity_ref": operator_identity_ref,
        "manually_published_at_epoch": int(manually_published_at_epoch),
        "manual_publish_url_hash": url_hash,
        "manual_publish_mode": manual_publish_mode,
        "publication_claim_class": publication_claim_class,
        "blocked_reasons": normalized,
    }
    return ManualPublishRecord(
        manual_publish_record_id="manual_publish_record_" + _digest(basis)[:24],
        source_revalidation_result_id=revalidation_result.revalidation_result_id,
        source_outbox_entry_id=candidate.outbox_entry_id,
        source_payload_hash=candidate.candidate_payload_hash,
        platform_id=candidate.platform_id,
        payload_class_id=candidate.payload_class_id,
        destination_binding_id=candidate.destination_binding_id,
        credential_handle_id=candidate.credential_handle_id,
        operator_identity_ref=operator_identity_ref,
        manually_published_at_epoch=int(manually_published_at_epoch),
        manual_publish_url_redacted=redact_url(manual_publish_url),
        manual_publish_url_hash=url_hash,
        manual_publish_url_hash_algorithm=HASH_ALGORITHM,
        manual_publish_mode=manual_publish_mode,
        publication_claim_class=publication_claim_class,
        source_revalidation_status=revalidation_result.revalidation_status,
        source_revalidation_future_gate_required=future_gate,
        manual_publish_record_status=_publish_status(normalized),
        human_review_required=True,
        public_claim_authorized=False,
        can_dispatch=False,
        dispatch_ready=False,
        public_postable=False,
        evidence_refs=_unique(tuple(candidate.evidence_refs) + tuple(revalidation_result.evidence_refs) + tuple(evidence_refs)),
        safety_flags=safety_flags(),
        blocked_reasons=normalized,
    )


def validate_manual_publish_record(
    record: ManualPublishRecord,
    revalidation_result: revalidation.DispatchRevalidationResult | None = None,
) -> ManualPublishRecordValidationResult:
    payload_hash_present = bool(record.source_payload_hash)
    url_hash_present = bool(record.manual_publish_url_hash)
    platform_known = _platform_known(record.platform_id)
    payload_class_known = _payload_class_known(record.payload_class_id)
    destination_present = bool(record.destination_binding_id)
    credential_present = bool(record.credential_handle_id)
    operator_present = bool(record.operator_identity_ref)
    bound = revalidation_result is None or (
        record.source_revalidation_result_id == revalidation_result.revalidation_result_id
        and record.source_outbox_entry_id == revalidation_result.outbox_entry_id
    )
    future_gate = bool(record.source_revalidation_future_gate_required)
    no_api_claim = record.publication_claim_class in {CLAIM_OPERATOR_ATTESTED, CLAIM_URL_NOT_VERIFIED, CLAIM_FUTURE_VERIFICATION}
    no_public = record.public_claim_authorized is False
    no_dispatch = record.can_dispatch is False and record.dispatch_ready is False and record.public_postable is False
    no_live = all(record.safety_flags.get(flag) is False for flag in (
        "platform_api_called", "telegram_api_called", "provider_api_called",
        "llm_provider_called", "credential_hydrated", "env_read",
        "network_performed", "scheduler_enabled", "scraping_performed",
        "browser_session_used", "dm_or_reply_automation_allowed",
    ))
    blockers = list(record.blocked_reasons)
    checks = (
        payload_hash_present, url_hash_present, platform_known, payload_class_known,
        destination_present, credential_present, operator_present, bound, future_gate,
        no_api_claim, no_public, no_dispatch, no_live,
    )
    if not payload_hash_present:
        blockers.append(BLOCK_MISSING_PAYLOAD_HASH)
    if not url_hash_present:
        blockers.append(BLOCK_MISSING_URL_HASH)
    if not platform_known:
        blockers.append(BLOCK_UNKNOWN_PLATFORM)
    if not payload_class_known:
        blockers.append(BLOCK_UNKNOWN_PAYLOAD_CLASS)
    if not future_gate:
        blockers.append(BLOCK_FUTURE_GATE_NOT_PRESERVED)
    if not no_api_claim:
        blockers.append(BLOCK_API_VERIFICATION_CLAIM)
    if not no_public:
        blockers.append(BLOCK_PUBLIC_CLAIM)
    if not no_dispatch:
        blockers.append(BLOCK_DISPATCH)
    if not no_live:
        blockers.append(BLOCK_NO_LIVE)
    normalized = _unique(blockers)
    hard = [b for b in normalized if b not in {
        revalidation.BLOCK_FUTURE_SEND_GATE_REQUIRED,
        revalidation.BLOCK_NO_DISPATCH,
        "dispatch_revalidation_required_future_0174UB",
    }]
    status = STATUS_RECORDED_REVIEW_ONLY if all(checks) and not hard else STATUS_UNKNOWN
    basis = {
        "record_id": record.manual_publish_record_id,
        "status": status,
        "blocked": normalized,
    }
    return ManualPublishRecordValidationResult(
        validation_id="manual_publish_validation_" + _digest(basis)[:24],
        source_manual_publish_record_id=record.manual_publish_record_id,
        payload_hash_present=payload_hash_present,
        url_hash_present=url_hash_present,
        platform_known=platform_known,
        payload_class_known=payload_class_known,
        destination_binding_present=destination_present,
        credential_handle_present=credential_present,
        operator_ref_present=operator_present,
        revalidation_result_bound=bound,
        revalidation_future_gate_preserved=future_gate,
        no_api_verification_claim=no_api_claim,
        no_public_claim_authorized=no_public,
        no_dispatch=no_dispatch,
        no_live_behavior=no_live,
        validation_status=status,
        blocked_reasons=normalized,
        evidence_refs=record.evidence_refs,
        safety_flags=safety_flags(),
    )


def build_manual_metrics_record(
    *,
    publish_record: ManualPublishRecord,
    metrics: dict[str, Any],
    metric_observed_at_epoch: int,
    metric_recorded_at_epoch: int,
    operator_identity_ref: str,
    metric_source_class: str = METRIC_SOURCE_OPERATOR,
    source_payload_hash: str | None = None,
    platform_id: str | None = None,
    metric_url: str = "",
    metric_notes: str = "",
    metric_values_are_operator_attested: bool = True,
    metric_values_are_api_verified: bool = False,
    metric_values_are_scraped: bool = False,
    evidence_refs: tuple[str, ...] = (),
) -> ManualMetricsRecord:
    payload_hash = publish_record.source_payload_hash if source_payload_hash is None else source_payload_hash
    platform = publish_record.platform_id if platform_id is None else platform_id
    metric_source = metric_source_class
    blockers: list[str] = []
    if payload_hash != publish_record.source_payload_hash:
        blockers.append(BLOCK_PAYLOAD_HASH_MISMATCH)
    if platform != publish_record.platform_id:
        blockers.append(BLOCK_PLATFORM_MISMATCH)
    if int(metric_observed_at_epoch) < publish_record.manually_published_at_epoch:
        blockers.append(BLOCK_METRIC_TIME_ORDER)
    if int(metric_recorded_at_epoch) < int(metric_observed_at_epoch):
        blockers.append(BLOCK_METRIC_TIME_ORDER)
    if not _non_negative_metrics(metrics):
        blockers.append(BLOCK_NEGATIVE_METRIC)
    if metric_source_class not in METRIC_SOURCE_CLASSES or metric_source_class == METRIC_SOURCE_UNKNOWN:
        metric_source = METRIC_SOURCE_UNKNOWN
        blockers.append(BLOCK_FUTURE_API_IMPORT)
    if metric_source_class == METRIC_SOURCE_FUTURE_API_BLOCKED:
        blockers.append(BLOCK_FUTURE_API_IMPORT)
    if not metric_values_are_operator_attested:
        blockers.append(BLOCK_METRICS_NOT_ATTESTED)
    if metric_values_are_api_verified:
        blockers.append(BLOCK_METRICS_API_VERIFIED)
    if metric_values_are_scraped:
        blockers.append(BLOCK_METRICS_SCRAPED)
    cleaned_metrics = {key: metrics.get(key) for key in NUMERIC_METRIC_KEYS if key in metrics}
    cleaned_metrics["notes"] = redact_notes(str(metrics.get("notes", "")))
    normalized = _unique(blockers)
    basis = {
        "source_manual_publish_record_id": publish_record.manual_publish_record_id,
        "source_payload_hash": payload_hash,
        "platform_id": platform,
        "metric_observed_at_epoch": int(metric_observed_at_epoch),
        "metric_recorded_at_epoch": int(metric_recorded_at_epoch),
        "operator_identity_ref": operator_identity_ref,
        "metric_source_class": metric_source,
        "metrics": cleaned_metrics,
        "metric_url_hash": hash_url(metric_url),
        "metric_notes_redacted": redact_notes(metric_notes),
        "blocked_reasons": normalized,
    }
    return ManualMetricsRecord(
        manual_metrics_record_id="manual_metrics_record_" + _digest(basis)[:24],
        source_manual_publish_record_id=publish_record.manual_publish_record_id,
        source_payload_hash=payload_hash,
        platform_id=platform,
        metric_observed_at_epoch=int(metric_observed_at_epoch),
        metric_recorded_at_epoch=int(metric_recorded_at_epoch),
        operator_identity_ref=operator_identity_ref,
        metric_source_class=metric_source,
        metrics=cleaned_metrics,
        metric_values_are_operator_attested=bool(metric_values_are_operator_attested),
        metric_values_are_api_verified=bool(metric_values_are_api_verified),
        metric_values_are_scraped=bool(metric_values_are_scraped),
        metric_url_hash=hash_url(metric_url),
        metric_notes_redacted=redact_notes(metric_notes),
        evidence_refs=_unique(tuple(publish_record.evidence_refs) + tuple(evidence_refs)),
        safety_flags=safety_flags(),
        blocked_reasons=normalized,
    )


def validate_manual_metrics_record(
    metrics_record: ManualMetricsRecord,
    publish_record: ManualPublishRecord,
) -> ManualMetricsValidationResult:
    payload_match = metrics_record.source_payload_hash == publish_record.source_payload_hash
    platform_match = metrics_record.platform_id == publish_record.platform_id
    time_order = (
        metrics_record.metric_observed_at_epoch >= publish_record.manually_published_at_epoch
        and metrics_record.metric_recorded_at_epoch >= metrics_record.metric_observed_at_epoch
    )
    non_negative = _non_negative_metrics(metrics_record.metrics)
    operator_only = bool(metrics_record.metric_values_are_operator_attested)
    api_false = metrics_record.metric_values_are_api_verified is False
    scraped_false = metrics_record.metric_values_are_scraped is False
    no_live = all(metrics_record.safety_flags.get(flag) is False for flag in (
        "platform_api_called", "telegram_api_called", "provider_api_called",
        "llm_provider_called", "credential_hydrated", "env_read",
        "network_performed", "scheduler_enabled", "scraping_performed",
        "browser_session_used", "dm_or_reply_automation_allowed",
    ))
    blockers = list(metrics_record.blocked_reasons)
    if not payload_match:
        blockers.append(BLOCK_PAYLOAD_HASH_MISMATCH)
    if not platform_match:
        blockers.append(BLOCK_PLATFORM_MISMATCH)
    if not time_order:
        blockers.append(BLOCK_METRIC_TIME_ORDER)
    if not non_negative:
        blockers.append(BLOCK_NEGATIVE_METRIC)
    if metrics_record.metric_source_class == METRIC_SOURCE_FUTURE_API_BLOCKED:
        blockers.append(BLOCK_FUTURE_API_IMPORT)
    if not operator_only:
        blockers.append(BLOCK_METRICS_NOT_ATTESTED)
    if not api_false:
        blockers.append(BLOCK_METRICS_API_VERIFIED)
    if not scraped_false:
        blockers.append(BLOCK_METRICS_SCRAPED)
    if not no_live:
        blockers.append(BLOCK_NO_LIVE)
    normalized = _unique(blockers)
    status = STATUS_RECORDED_REVIEW_ONLY if all((
        payload_match, platform_match, time_order, non_negative,
        operator_only, api_false, scraped_false, no_live,
    )) and not normalized else STATUS_UNKNOWN
    basis = {
        "metrics_id": metrics_record.manual_metrics_record_id,
        "publish_id": publish_record.manual_publish_record_id,
        "status": status,
        "blocked": normalized,
    }
    return ManualMetricsValidationResult(
        validation_id="manual_metrics_validation_" + _digest(basis)[:24],
        source_metrics_record_id=metrics_record.manual_metrics_record_id,
        source_publish_record_id=publish_record.manual_publish_record_id,
        payload_hash_match=payload_match,
        platform_match=platform_match,
        metric_time_order_valid=time_order,
        non_negative_metrics=non_negative,
        operator_attested_only=operator_only,
        api_verified_false=api_false,
        scraped_false=scraped_false,
        no_live_behavior=no_live,
        validation_status=status,
        blocked_reasons=normalized,
        evidence_refs=_unique(tuple(metrics_record.evidence_refs) + tuple(publish_record.evidence_refs)),
        safety_flags=safety_flags(),
    )


def build_revalidation_fixture() -> tuple[revalidation.DispatchRevalidationCandidate, revalidation.DispatchRevalidationResult]:
    packet = revalidation.build_revalidation_gate_packet()
    return packet.candidates[0], packet.revalidation_results[0]


def _audit_entries(
    publish: ManualPublishRecord,
    metrics: ManualMetricsRecord,
) -> tuple[audit.RedactedAuditLedgerEntry, ...]:
    publish_entry = audit.build_redacted_ledger_entry(
        entry_sequence=1,
        previous_entry_hash=audit.GENESIS_HASH,
        entry_family="manual_publish_record_future_gate",
        source_model="0174UC",
        source_model_version=MODEL_VERSION,
        payload=_asdict(publish),
        created_at_epoch=publish.manually_published_at_epoch,
    )
    metrics_entry = audit.build_redacted_ledger_entry(
        entry_sequence=2,
        previous_entry_hash=publish_entry.entry_hash,
        entry_family="metrics_record_future_gate",
        source_model="0174UC",
        source_model_version=MODEL_VERSION,
        payload=_asdict(metrics),
        created_at_epoch=metrics.metric_recorded_at_epoch,
    )
    return publish_entry, metrics_entry


def build_contract_packet() -> ManualPublishMetricsLedgerPacket:
    candidate, result = build_revalidation_fixture()
    publish = build_manual_publish_record(
        revalidation_result=result,
        candidate=candidate,
        operator_identity_ref="operator:jim:redacted",
        manually_published_at_epoch=1300,
        manual_publish_url="https://capitalchronicle.example/post/0174UC?token=raw-secret",
        manual_publish_mode=MODE_OPERATOR_PLATFORM,
        publication_claim_class=CLAIM_OPERATOR_ATTESTED,
        evidence_refs=(
            "docs/automation/0174UB/dispatch_outbox_revalidation_gate_contract_packet.json",
            "docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md",
        ),
    )
    publish_validation = validate_manual_publish_record(publish, result)
    metrics = build_manual_metrics_record(
        publish_record=publish,
        metrics={
            "impressions": 100,
            "views": 80,
            "likes": 4,
            "comments": 1,
            "shares": 2,
            "reposts": 0,
            "saves": 3,
            "clicks": 5,
            "opens": 0,
            "subscribers_delta": 0,
            "notes": "Read manually by operator; token=raw-secret",
        },
        metric_observed_at_epoch=1400,
        metric_recorded_at_epoch=1500,
        operator_identity_ref="operator:jim:redacted",
        metric_source_class=METRIC_SOURCE_PLATFORM_UI,
        metric_url="https://capitalchronicle.example/post/0174UC?token=raw-secret",
        metric_notes="Manual UI reading by operator@example.com token=raw-secret",
        evidence_refs=("docs/automation/0174UC/manual_publish_record_metrics_ledger_contract.md",),
    )

    metrics_validation = validate_manual_metrics_record(metrics, publish)
    ledger_entries = _audit_entries(publish, metrics)
    draft = {
        "manual_publish_records": (publish,),
        "manual_publish_validations": (publish_validation,),
        "manual_metrics_records": (metrics,),
        "manual_metrics_validations": (metrics_validation,),
        "audit_ledger_entries": ledger_entries,
        "all_records_redacted": all(entry.redacted_summary for entry in ledger_entries),
        "all_records_manual_only": True,
        "no_api_verification": (
            publish.publication_claim_class == CLAIM_OPERATOR_ATTESTED
            and metrics.metric_values_are_api_verified is False
        ),
        "no_scraping": metrics.metric_values_are_scraped is False,
        "no_dispatch": all(not x for x in (
            publish.can_dispatch, publish.dispatch_ready, publish.public_postable,
        )),
        "no_public_claim_authorized": publish.public_claim_authorized is False,
        "evidence_refs": _unique(
            tuple(publish.evidence_refs) + tuple(metrics.evidence_refs)
            + tuple(ref for entry in ledger_entries for ref in entry.retained_evidence_refs)
        ),
        "safety_flags": safety_flags(),
        "blocked_reasons": _unique(
            tuple(publish.blocked_reasons)
            + tuple(publish_validation.blocked_reasons)
            + tuple(metrics.blocked_reasons)
            + tuple(metrics_validation.blocked_reasons)
        ),
        "next_required_gate": NEXT_HEAVY_BATCH,
    }
    packet_hash = _digest(draft)
    return ManualPublishMetricsLedgerPacket(
        packet_id="manual_publish_metrics_packet_" + packet_hash[:24],
        packet_hash=packet_hash,
        packet_hash_algorithm=HASH_ALGORITHM,
        **draft,
    )


def render_runbook(packet: ManualPublishMetricsLedgerPacket) -> str:
    summary = {
        "packet_id": packet.packet_id,
        "packet_hash": packet.packet_hash,
        "manual_publish_records": len(packet.manual_publish_records),
        "manual_metrics_records": len(packet.manual_metrics_records),
        "no_api_verification": packet.no_api_verification,
        "no_scraping": packet.no_scraping,
        "no_dispatch": packet.no_dispatch,
        "no_public_claim_authorized": packet.no_public_claim_authorized,
        "blocked_reasons": packet.blocked_reasons,
    }
    return "\n".join([
        "# 0174UC Manual Publish Record + Metrics Ledger Contract", "",
        f"- task_label: `{TASK_LABEL}`",
        f"- model_version: `{MODEL_VERSION}`",
        f"- source_baseline_commit: `{SOURCE_BASELINE_COMMIT}`",
        f"- packet_id: `{packet.packet_id}`",
        f"- packet_hash: `{packet.packet_hash}`", "",
        "## Contract rules", "",
        "- Manual publish records are operator-attested evidence only.",
        "- Manual URLs are stored only as redacted strings plus SHA-256 hashes.",
        "- Metrics are manually entered and never API-verified or scraped.",
        "- Revalidation future-send gate remains preserved.",
        "- U9 redacted audit entries record publish and metrics facts.", "",
        "## Safety", "",
        "- No dispatch, public claim authority, API verification, scraping, browser session, env/credential read, scheduler, DM/reply, UI, or ingestion mutation.", "",
        "## Next heavy batch", "", f"`{NEXT_HEAVY_BATCH}`", "",
        "## Packet summary", "", "```json", json.dumps(summary, indent=2, sort_keys=True), "```", "",
    ])


def write_artifacts(repo_root: str | Path = ".", output_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    allowed = (root / DOC_REL_DIR).resolve()
    out = allowed if output_dir is None else Path(output_dir).resolve()
    if out != allowed:
        raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UC")
    out.mkdir(parents=True, exist_ok=True)
    packet = build_contract_packet()
    packet_path = out / PACKET_FILENAME
    runbook_path = out / RUNBOOK_FILENAME
    packet_path.write_text(
        json.dumps(_asdict(packet), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    runbook_path.write_text(render_runbook(packet), encoding="utf-8", newline="\n")
    return {"packet": packet, "packet_path": str(packet_path), "runbook_path": str(runbook_path)}


def contract_checksum() -> str:
    return build_contract_packet().packet_hash
