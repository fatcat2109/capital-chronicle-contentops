"""Deterministic V1 newsroom production-day accounting.

This module is a read/projection layer over the canonical durable store and the existing
newsroom output artifacts.  It is not a scheduler, store, newsroom, or publisher.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence
from zoneinfo import ZoneInfo

from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)
from live_contentops.editorial_portfolio_v1 import PublishedArticleRef

BANGKOK_TIMEZONE = ZoneInfo("Asia/Bangkok")
BUILD_QUALIFIED_FLOOR = 4
FINAL_PUBLISHED_TARGET_MIN = 5
FINAL_PUBLISHED_TARGET_MAX = 8
ROUTINE_OPPORTUNITY_LIMIT = 4

STATE_ON_TRACK = "ON_TRACK"
STATE_DEFICIT_RECOVERABLE = "DEFICIT_RECOVERABLE"
STATE_FLOOR_MET = "FLOOR_MET"
STATE_DEGRADED_DAILY_OUTPUT_DEFICIT = "DEGRADED_DAILY_OUTPUT_DEFICIT"
STATE_HARD_EXTERNAL_BLOCK = "HARD_EXTERNAL_BLOCK"

PRODUCTION_DAY_STATES = frozenset(
    {
        STATE_ON_TRACK,
        STATE_DEFICIT_RECOVERABLE,
        STATE_FLOOR_MET,
        STATE_DEGRADED_DAILY_OUTPUT_DEFICIT,
        STATE_HARD_EXTERNAL_BLOCK,
    }
)

ROUTINE_SESSION_ORDINAL = {
    "london_1700_bangkok": 1,
    "new_york_2100_bangkok": 2,
    "new_york_2300_bangkok": 3,
    "new_york_0100_bangkok": 4,
}

QUALIFIED_ARTICLE_RECORD = "qualified_article_record_v1.json"
PRODUCTION_DAY_RECORD = "newsroom_production_day_v1.json"


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, ensure_ascii=True, separators=(",", ":"), sort_keys=True, default=str
        ).encode("utf-8")
    ).hexdigest()


def newsroom_production_date(reference: datetime | str) -> date:
    """Return the Bangkok production date for an arbitrary instant.

    The 01:00 Bangkok opportunity belongs to the prior date.  The next production-day
    identity becomes active at 02:00, after the prior day's final opportunity ends.
    """
    local = _parse_datetime(reference).astimezone(BANGKOK_TIMEZONE)
    return local.date() - timedelta(days=1) if local.hour < 2 else local.date()


def newsroom_production_day_id(reference: datetime | str) -> str:
    return f"newsroom-production-day-{newsroom_production_date(reference).isoformat()}-bangkok"


def newsroom_production_day_bounds(reference: datetime | str) -> tuple[datetime, datetime]:
    production_date = newsroom_production_date(reference)
    start_local = datetime.combine(
        production_date, time(hour=17), tzinfo=BANGKOK_TIMEZONE
    )
    end_local = datetime.combine(
        production_date + timedelta(days=1), time(hour=2), tzinfo=BANGKOK_TIMEZONE
    )
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def routine_progress_target(session: str) -> int:
    """Historical 4/32 telemetry checkpoint; never an editorial skip condition."""
    if session not in ROUTINE_SESSION_ORDINAL:
        return 0
    return min(BUILD_QUALIFIED_FLOOR, ROUTINE_SESSION_ORDINAL[session])


def routine_session_ordinal(session: str) -> int:
    """Return the independent 1..4 routine-opportunity position for ``session``."""
    return int(ROUTINE_SESSION_ORDINAL.get(session, 0))


def remaining_future_routine_windows(session: str) -> int:
    """Return later routine windows in the same deterministic production day."""
    ordinal = routine_session_ordinal(session)
    return max(0, ROUTINE_OPPORTUNITY_LIMIT - ordinal) if ordinal else 0


def bounded_deficit_work_needed(*, session: str, qualified_articles_today: int) -> int:
    """Allocate bounded article slots without allowing quota pacing to starve a window.

    Every valid routine opportunity gets at least one real candidate walk.  Below the final
    five-article minimum, extra capacity is allocated when needed to keep that minimum reachable
    through the later routine windows.  Qualification still depends on the normal governed
    candidate, evidence, truth, and authority gates; this is capacity, never a filler quota.
    """
    if routine_session_ordinal(session) == 0:
        return 0
    qualified = max(0, int(qualified_articles_today))
    if qualified >= FINAL_PUBLISHED_TARGET_MIN:
        return 1
    return max(
        1,
        FINAL_PUBLISHED_TARGET_MIN
        - qualified
        - remaining_future_routine_windows(session),
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _article_body(article: Mapping[str, Any]) -> str:
    return str(
        article.get("substack_body_markdown")
        or article.get("rendered_body")
        or ""
    ).strip()


def _worker_receipt(output_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    built = _read_json(output_dir / "rolling_x_grounded_article_media_v1.json")
    receipt = dict(built.get("editorial_worker_receipt") or {})
    validation = dict(built.get("editorial_worker_validation") or {})
    return receipt, validation


def qualify_zero_write_article(
    *,
    result: Mapping[str, Any],
    output_dir: str | Path,
    production_day_id: str,
    parent_window_id: str,
) -> dict[str, Any]:
    """Validate and build one countable zero-write article record.

    The record is deliberately strict.  A draft, package-only artifact, legacy writer,
    missing HIGH-worker receipt, missing accepted evidence, or any public/unknown write cannot count.
    """
    root = Path(output_dir)
    blockers: list[str] = []
    article = _read_json(root / "article_manifest_v1.json")
    support = _read_json(root / "grounded_support_v1.json")
    media = _read_json(root / "media_manifest_v1.json")
    editorial_gate = _read_json(root / "editorial_quality_gate_v1.json")
    payloads = _read_json(root / "native_payloads_rehearsal_v1.json")
    lock = _read_json(root / "release_candidate_lock_v1.json")
    rehearsal = _read_json(root / "no_write_rehearsal_v1.json")
    receipt, worker_validation = _worker_receipt(root)
    plan = dict(result.get("publication_lifecycle_plan") or {})

    body = _article_body(article)
    article_identity = str(plan.get("article_identity") or lock.get("article_body_sha256") or "")
    if not str(article.get("title") or "").strip() or not body:
        blockers.append("actual_final_article_missing")
    if not article_identity or article_identity != hashlib.sha256(body.encode("utf-8")).hexdigest():
        blockers.append("stable_article_identity_missing_or_mismatched")
    if support.get("status") != "PASS" or not support.get("targeted_evidence"):
        blockers.append("accepted_evidence_binding_missing")
    institutional = dict(article.get("institutional_edge_editorial_validation") or {})
    if institutional.get("classification") != "PASS":
        blockers.append("institutional_edge_validation_not_pass")
    if editorial_gate.get("classification") != "PASS":
        blockers.append("editorial_validation_not_pass")
    if media.get("status") != "PASS":
        blockers.append("rights_or_media_validation_not_pass")
    if rehearsal.get("classification") != "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL":
        blockers.append("release_candidate_rehearsal_not_pass")
    required = tuple(str(value) for value in V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    if set(payloads) != set(required) or len(payloads) != 8:
        blockers.append("exactly_eight_derivative_packages_not_persisted")
    if tuple(str(value) for value in plan.get("required_derivative_destinations") or ()) != required:
        blockers.append("publication_plan_derivative_contract_mismatch")
    destinations = [
        dict(row) for row in plan.get("destinations") or [] if isinstance(row, Mapping)
    ]
    derivative_rows = [row for row in destinations if row.get("destination") != "substack"]
    if {str(row.get("destination") or "") for row in derivative_rows} != set(required):
        blockers.append("derivative_intent_set_mismatch")
    if bool(result.get("public_write_performed")) or bool(lock.get("public_write_performed")):
        blockers.append("public_write_performed")
    if bool(result.get("unknown_write_detected")) or int(result.get("unknown_write_count") or 0):
        blockers.append("unknown_write_detected")
    route = dict(result.get("editorial_worker_routing") or {})
    expected_hash = str(route.get("governed_input_hash") or "")
    if (
        not expected_hash
        or str(receipt.get("governed_input_hash") or "") != expected_hash
        or str(receipt.get("model") or "") != "gpt-5.6-sol"
        or str(receipt.get("reasoning_effort") or "").upper() != "HIGH"
        or receipt.get("fresh") is not True
        or receipt.get("isolated") is not True
        or receipt.get("resume_existing") not in {False, None}
        or bool(receipt.get("public_write_attempted"))
    ):
        blockers.append("fresh_isolated_xhigh_receipt_missing_or_invalid")
    if worker_validation.get("coordinator_resumes") is not True:
        blockers.append("xhigh_return_deterministic_validation_missing")
    evidence = support.get("targeted_evidence") or {}
    documents = (
        list(evidence.get("evidence_documents") or [])
        if isinstance(evidence, Mapping)
        else []
    )
    evidence_ids = sorted(
        {
            str(
                row.get("evidence_id")
                or row.get("document_id")
                or row.get("source_url")
                or row.get("url")
                or ""
            )
            for row in documents
            if isinstance(row, Mapping)
        }
        - {""}
    )
    if not evidence_ids:
        blockers.append("accepted_evidence_identity_missing")

    record_core = {
        "schema_version": "contentops.newsroom_qualified_article.v1",
        "newsroom_production_day_id": production_day_id,
        "parent_window_id": parent_window_id,
        "attempt_run_id": str(result.get("run_id") or root.name),
        "article_identity": article_identity,
        "story_identity": str(plan.get("story_identity") or ""),
        "update_chain_identity": str(plan.get("update_chain_identity") or ""),
        "title": str(article.get("title") or ""),
        "resolved_article_mode": str(
            plan.get("resolved_article_mode") or article.get("resolved_article_mode") or ""
        ),
        "article_path": str((root / "article_manifest_v1.json").resolve()),
        "article_body_sha256": article_identity,
        "accepted_evidence_ids": evidence_ids,
        "accepted_evidence_sha256": str(lock.get("source_packet_sha256") or ""),
        "editorial_worker": {
            "model": receipt.get("model"),
            "reasoning_effort": str(receipt.get("reasoning_effort") or "").upper(),
            "fresh": receipt.get("fresh"),
            "isolated": receipt.get("isolated"),
            "resume_existing": bool(receipt.get("resume_existing")),
            "governed_input_hash": receipt.get("governed_input_hash"),
            "bounded_revision_count": int(receipt.get("bounded_revision_count") or 0),
            "public_write_attempted": False,
        },
        "derivative_package_intents": [
            {
                "destination": destination,
                "payload_sha256": str((lock.get("payload_sha256") or {}).get(destination) or ""),
                "dispatch_state": "UNDISPATCHED",
            }
            for destination in required
        ],
        "derivative_package_intent_count": 8,
        "public_write_performed": False,
        "unknown_write_count": 0,
        "qualification_blockers": sorted(set(blockers)),
        "qualified": not blockers,
    }
    return {**record_core, "record_sha256": _logical_hash(record_core)}


def persist_qualified_article_record(output_dir: str | Path, record: Mapping[str, Any]) -> Path:
    if record.get("qualified") is not True:
        raise ValueError("unqualified_article_record_cannot_be_persisted")
    path = Path(output_dir) / QUALIFIED_ARTICLE_RECORD
    payload = dict(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if _read_json(path) != payload:
            raise ValueError("qualified_article_record_identity_conflict")
        return path
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _valid_record(record: Mapping[str, Any]) -> bool:
    material = {key: value for key, value in record.items() if key != "record_sha256"}
    return bool(
        record.get("schema_version") == "contentops.newsroom_qualified_article.v1"
        and record.get("qualified") is True
        and not record.get("qualification_blockers")
        and record.get("public_write_performed") is False
        and int(record.get("unknown_write_count") or 0) == 0
        and int(record.get("derivative_package_intent_count") or 0) == 8
        and len(record.get("derivative_package_intents") or []) == 8
        and str(record.get("record_sha256") or "") == _logical_hash(material)
    )


def load_qualified_article_records(
    output_root: str | Path, *, production_day_id: str
) -> list[dict[str, Any]]:
    by_identity: dict[str, dict[str, Any]] = {}
    for path in Path(output_root).glob(f"**/{QUALIFIED_ARTICLE_RECORD}"):
        record = _read_json(path)
        identity = str(record.get("article_identity") or "")
        if (
            not identity
            or record.get("newsroom_production_day_id") != production_day_id
            or not _valid_record(record)
        ):
            continue
        by_identity.setdefault(identity, record)
    return [by_identity[key] for key in sorted(by_identity)]


def qualified_records_as_published_memory(
    records: Sequence[Mapping[str, Any]], *, reference: datetime | str
) -> list[PublishedArticleRef]:
    timestamp = _iso_utc(_parse_datetime(reference))
    return [
        PublishedArticleRef(
            story_identity=str(record.get("story_identity") or record["article_identity"]),
            title=str(record.get("title") or record["article_identity"]),
            published_at_utc=timestamp,
            public_object_id=None,
            canonical_url_hash=None,
            content_hash=str(record.get("article_body_sha256") or "") or None,
            entities=(),
            article_identity=str(record["article_identity"]),
            update_chain_identity=str(record.get("update_chain_identity") or "") or None,
            article_mode=str(record.get("resolved_article_mode") or "") or None,
            content_status="CONTENT_AVAILABLE",
            full_text=None,
            source_work_item_id=str(record.get("parent_window_id") or "") or None,
        )
        for record in records
    ]


def routine_opportunities_used(
    output_root: str | Path,
    *,
    production_day_id: str,
    terminal_work_item_ids: Optional[Iterable[str]] = None,
) -> int:
    terminal = set(str(value) for value in terminal_work_item_ids or [])
    sessions: set[str] = set()
    for path in Path(output_root).glob("*/editorial_opportunity_v1.json"):
        checkpoint = _read_json(path)
        window_id = str(checkpoint.get("window_id") or "")
        if terminal and window_id not in terminal:
            continue
        if str(checkpoint.get("trigger") or "") != "SCHEDULED":
            continue
        session = str(checkpoint.get("session") or "")
        if session not in ROUTINE_SESSION_ORDINAL:
            continue
        try:
            checkpoint_day_id = newsroom_production_day_id(str(checkpoint["start_utc"]))
        except (KeyError, TypeError, ValueError):
            continue
        if checkpoint_day_id == production_day_id:
            sessions.add(session)
    return min(ROUTINE_OPPORTUNITY_LIMIT, len(sessions))


def _published_count(
    published_corpus: Sequence[Any], *, production_day_id: str
) -> int:
    identities: set[str] = set()
    for value in published_corpus:
        published_at = getattr(value, "published_at_utc", None)
        identity = getattr(value, "article_identity", None) or getattr(
            value, "story_identity", None
        )
        if not published_at or not identity:
            continue
        try:
            if newsroom_production_day_id(str(published_at)) == production_day_id:
                identities.add(str(identity))
        except ValueError:
            continue
    return len(identities)


@dataclass(frozen=True)
class NewsroomProductionDaySnapshot:
    newsroom_production_day_id: str
    build_qualified_floor: int
    final_published_target_min: int
    final_published_target_max: int
    qualified_articles_today: int
    published_articles_today: int
    remaining_build_deficit: int
    production_day_state: str
    hard_external_block_reason: Optional[str]
    routine_opportunities_used: int
    routine_opportunities_remaining: int
    bounded_useful_universe_exhausted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_production_day_snapshot(
    *,
    reference: datetime | str,
    output_root: str | Path,
    published_corpus: Sequence[Any] = (),
    routine_opportunities_used_override: Optional[int] = None,
    terminal_work_item_ids: Optional[Iterable[str]] = None,
    hard_external_block_reason: Optional[str] = None,
    bounded_useful_universe_exhausted: bool = False,
) -> NewsroomProductionDaySnapshot:
    day_id = newsroom_production_day_id(reference)
    qualified = len(
        load_qualified_article_records(output_root, production_day_id=day_id)
    )
    published = _published_count(published_corpus, production_day_id=day_id)
    used = (
        int(routine_opportunities_used_override)
        if routine_opportunities_used_override is not None
        else routine_opportunities_used(
            output_root,
            production_day_id=day_id,
            terminal_work_item_ids=terminal_work_item_ids,
        )
    )
    used = min(ROUTINE_OPPORTUNITY_LIMIT, max(0, used))
    remaining = ROUTINE_OPPORTUNITY_LIMIT - used
    deficit = max(0, BUILD_QUALIFIED_FLOOR - qualified)
    reason = str(hard_external_block_reason or "").strip() or None
    if deficit == 0:
        state = STATE_FLOOR_MET
        reason = None
    elif reason:
        state = STATE_HARD_EXTERNAL_BLOCK
    elif bounded_useful_universe_exhausted or remaining == 0:
        state = STATE_DEGRADED_DAILY_OUTPUT_DEFICIT
    elif qualified >= used:
        state = STATE_ON_TRACK
    else:
        state = STATE_DEFICIT_RECOVERABLE
    return NewsroomProductionDaySnapshot(
        newsroom_production_day_id=day_id,
        build_qualified_floor=BUILD_QUALIFIED_FLOOR,
        final_published_target_min=FINAL_PUBLISHED_TARGET_MIN,
        final_published_target_max=FINAL_PUBLISHED_TARGET_MAX,
        qualified_articles_today=qualified,
        published_articles_today=published,
        remaining_build_deficit=deficit,
        production_day_state=state,
        hard_external_block_reason=reason,
        routine_opportunities_used=used,
        routine_opportunities_remaining=remaining,
        bounded_useful_universe_exhausted=bool(bounded_useful_universe_exhausted),
    )


def persist_production_day_snapshot(
    output_dir: str | Path, snapshot: NewsroomProductionDaySnapshot
) -> Path:
    path = Path(output_dir) / PRODUCTION_DAY_RECORD
    payload = {
        "schema_version": "contentops.newsroom_production_day.v1",
        **snapshot.to_dict(),
    }
    payload["record_sha256"] = _logical_hash(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_production_day_discovery_accounting(
    output_root: str | Path, *, production_day_id: str
) -> dict[str, Any]:
    """Load cumulative quota state from existing production-day cycle artifacts."""
    candidates: list[dict[str, Any]] = []
    for path in Path(output_root).glob("**/rolling_x_newsroom_cycle_evidence_v1.json"):
        cycle = _read_json(path)
        accounting = cycle.get("quota_efficient_source_discovery")
        if (
            not isinstance(accounting, Mapping)
            or accounting.get("schema_version")
            != "contentops.quota_efficient_source_discovery.v1"
            or str(accounting.get("newsroom_production_day_id") or "")
            != str(production_day_id)
        ):
            continue
        candidates.append(dict(accounting))
    if not candidates:
        return {}
    candidates.sort(
        key=lambda row: (
            int(row.get("total_discovery_turns") or 0),
            int(row.get("accounted_discovery_tokens") or 0),
            int(row.get("deterministic_network_requests") or 0),
        )
    )
    return candidates[-1]
