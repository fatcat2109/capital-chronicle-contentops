"""Read-only V1 opportunity intake and the durable V2 daily shadow operator spine."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from live_contentops.daily_app_performance_v1 import qualified_engagement_score
from live_contentops.published_corpus_read_model_v1 import load_published_corpus

from .unattended_core_factory_v1.store import V2JobStore


SCHEMA = "contentops.v2.v1_readonly_daily_operator.v1"
QUALIFICATION_POLICY_VERSION = "contentops.v2.v1_readonly_candidate_qualification.v1"
TARGET_FORMAT = "SHORT_9_16_1080X1920_30FPS"
MAX_FRESH_CALENDAR_DAYS = 4
MIN_CONTENT_WORDS = 350
MIN_EVIDENCE_REFS = 2
MIN_VIEWER_VALUE_SCORE = 0.60
MAX_DAILY_QUALIFIED = 1
PARENT_MODEL = "gpt-5.6-sol"
PARENT_REASONING_EFFORT = "high"


class DailyOperatorError(RuntimeError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash(value: Any) -> str:
    return hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


def _parse_time(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _write_immutable_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        existing = _load_object(path)
        if _hash(existing) != _hash(dict(value)):
            raise DailyOperatorError(f"immutable_artifact_conflict:{path}")
        return
    path.write_text(
        json.dumps(dict(value), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class _ReadOnlyV1Store:
    """The one method needed by the canonical published-corpus read model."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).resolve()
        if not self.path.is_file():
            raise DailyOperatorError(f"v1_store_not_found:{self.path}")

    @contextmanager
    def get_read_only_connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            f"file:{self.path.as_posix()}?mode=ro",
            uri=True,
            timeout=30,
            isolation_level=None,
            cached_statements=0,
        )
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA query_only=ON")
            connection.execute("PRAGMA foreign_keys=ON")
            yield connection
        finally:
            connection.close()


def _evidence_values(value: Any, *, key: str = "") -> Iterator[str]:
    keys = {
        "source_ref",
        "source_refs",
        "source_url",
        "source_page_url",
        "url",
        "evidence_document_id",
        "evidence_document_ids",
        "evidence_id",
        "evidence_ids",
        "document_id",
        "document_ids",
        "source_id",
        "source_ids",
    }
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            yield from _evidence_values(child, key=str(child_key))
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for child in value:
            yield from _evidence_values(child, key=key)
        return
    if key in keys and isinstance(value, (str, int, float)):
        text = " ".join(str(value).split())[:1000]
        if text:
            yield text


def _article_evidence_refs(body_source: str | None) -> list[str]:
    if not body_source:
        return []
    output_dir = Path(body_source).resolve().parent
    refs: set[str] = set()
    for name in (
        "grounded_support_v1.json",
        "article_manifest_v1.json",
        "idea_selection_v1.json",
        "run_context_v1.json",
    ):
        for value in _evidence_values(_load_object(output_dir / name)):
            refs.add(value)
            if len(refs) >= 64:
                break
        if len(refs) >= 64:
            break
    return sorted(refs)


def _performance_projection(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    eligible: list[dict[str, Any]] = []
    for raw in rows:
        row = dict(raw)
        if int(row.get("learning_eligible") or 0) != 1:
            continue
        try:
            metrics = json.loads(str(row.get("metrics_native_json") or "{}"))
            availability = json.loads(str(row.get("metric_availability_json") or "{}"))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        if not isinstance(metrics, Mapping) or not isinstance(availability, Mapping):
            continue
        score = qualified_engagement_score(metrics, availability)
        eligible.append(
            {
                "observation_id": str(row.get("observation_id") or ""),
                "observation_hash": str(row.get("observation_hash") or ""),
                "observation_window": str(row.get("observation_window") or ""),
                "collection_status": str(row.get("collection_status") or ""),
                "qualified_engagement_score": score,
                "performance_is_priority_only": True,
                "grants_factual_or_numeric_authority": False,
            }
        )
    eligible.sort(
        key=lambda item: (
            item["qualified_engagement_score"] is not None,
            float(item["qualified_engagement_score"] or 0.0),
            item["observation_id"],
        ),
        reverse=True,
    )
    scores = [
        float(item["qualified_engagement_score"])
        for item in eligible
        if item["qualified_engagement_score"] is not None
    ]
    return {
        "observations": eligible,
        "observation_count": len(eligible),
        "best_qualified_engagement_score": max(scores) if scores else None,
        "performance_is_priority_only": True,
        "grants_factual_or_numeric_authority": False,
    }


def read_v1_opportunities(
    store_path: str | Path,
    *,
    output_root: str | Path | None = None,
) -> dict[str, Any]:
    """Read the canonical V1 lifecycle and performance surfaces through SQLite RO mode."""
    store = _ReadOnlyV1Store(store_path)
    before = store.path.stat()
    with store.get_read_only_connection() as audit_connection:
        query_only = int(audit_connection.execute("PRAGMA query_only").fetchone()[0])
        data_version_before = int(
            audit_connection.execute("PRAGMA data_version").fetchone()[0]
        )
        required_tables = {
            "work_items",
            "outbox_messages",
            "platform_dispatches",
            "reconciliations",
            "performance_observations",
        }
        present_tables = {
            str(row[0])
            for row in audit_connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        missing = sorted(required_tables - present_tables)
        if missing:
            raise DailyOperatorError("v1_required_read_tables_missing:" + ",".join(missing))
        table_counts = {
            table: int(
                audit_connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            )
            for table in sorted(required_tables)
        }

        corpus = load_published_corpus(store, output_root=output_root)
        performance_rows = [
            dict(row)
            for row in audit_connection.execute(
                "SELECT * FROM performance_observations ORDER BY scheduled_for_utc,observation_id"
            ).fetchall()
        ]
        total_changes = int(audit_connection.total_changes)
        data_version_after = int(
            audit_connection.execute("PRAGMA data_version").fetchone()[0]
        )
    after = store.path.stat()

    observations_by_work_item: dict[str, list[dict[str, Any]]] = {}
    for row in performance_rows:
        observations_by_work_item.setdefault(str(row.get("work_item_id") or ""), []).append(row)

    articles: list[dict[str, Any]] = []
    for article in corpus.get("articles") or []:
        value = article.to_dict()
        work_item_id = str(value.get("source_work_item_id") or "")
        value["evidence_refs"] = _article_evidence_refs(value.get("body_source"))
        value["performance"] = _performance_projection(
            observations_by_work_item.get(work_item_id, [])
        )
        articles.append(value)
    articles.sort(
        key=lambda item: (str(item.get("published_at_utc") or ""), str(item.get("story_identity") or "")),
        reverse=True,
    )

    snapshot_material = {
        "canonical_read_model_schema": corpus.get("schema_version"),
        "canonical_publication_contract": corpus.get("canonical_publication_contract"),
        "articles": [
            {
                "story_identity": row.get("story_identity"),
                "article_identity": row.get("article_identity"),
                "source_work_item_id": row.get("source_work_item_id"),
                "published_at_utc": row.get("published_at_utc"),
                "content_hash": row.get("content_hash"),
                "evidence_refs": row.get("evidence_refs"),
                "performance_observation_hashes": [
                    item.get("observation_hash")
                    for item in row["performance"]["observations"]
                ],
            }
            for row in articles
        ],
        "table_counts": table_counts,
    }
    snapshot_hash = _hash(snapshot_material)
    return {
        "schema": "contentops.v2.v1_readonly_opportunity_snapshot.v1",
        "store_path": str(store.path),
        "read_surface": (
            "published_corpus_read_model_v1.load_published_corpus + "
            "performance_observations(query_only)"
        ),
        "canonical_publication_contract": corpus.get("canonical_publication_contract"),
        "article_count": len(articles),
        "articles": articles,
        "snapshot_hash": snapshot_hash,
        "read_only_proof": {
            "sqlite_uri_mode": "ro",
            "pragma_query_only": query_only,
            "connection_total_changes": total_changes,
            "write_api_exposed": False,
            "data_version_before": data_version_before,
            "data_version_after": data_version_after,
            "data_version_stable_during_read": data_version_before == data_version_after,
            "database_size_before": before.st_size,
            "database_size_after": after.st_size,
            "database_mtime_ns_before": before.st_mtime_ns,
            "database_mtime_ns_after": after.st_mtime_ns,
            "database_stat_stable_during_read": (
                before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns
            ),
            "v1_write_count": 0,
        },
        "table_counts": table_counts,
        "second_v1_store_created": False,
        "v1_mutation_authority": False,
    }


def _freshness(article: Mapping[str, Any], *, now: datetime) -> dict[str, Any]:
    published = _parse_time(article.get("published_at_utc"))
    if published is None:
        return {
            "status": "PUBLISHED_TIME_UNAVAILABLE",
            "published_at_utc": article.get("published_at_utc"),
            "evaluation_day_utc": now.date().isoformat(),
            "fresh": False,
        }
    cutoff = datetime.combine(
        now.date() - timedelta(days=MAX_FRESH_CALENDAR_DAYS),
        datetime.min.time(),
        tzinfo=timezone.utc,
    )
    return {
        "status": "FRESH" if cutoff <= published <= now + timedelta(minutes=5) else "STALE",
        "published_at_utc": published.isoformat().replace("+00:00", "Z"),
        "evaluation_day_utc": now.date().isoformat(),
        "age_calendar_days": (now.date() - published.date()).days,
        "fresh": cutoff <= published <= now + timedelta(minutes=5),
        "future_timestamp": published > now + timedelta(minutes=5),
        "maximum_fresh_calendar_days": MAX_FRESH_CALENDAR_DAYS,
    }


def _candidate_identity(article: Mapping[str, Any]) -> tuple[str, str]:
    identity = str(
        article.get("article_identity")
        or article.get("source_work_item_id")
        or article.get("story_identity")
        or ""
    )
    content_hash = str(article.get("content_hash") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", content_hash):
        content_hash = _hash(
            {
                "identity": identity,
                "published_at_utc": article.get("published_at_utc"),
                "canonical_url_hash": article.get("canonical_url_hash"),
            }
        )
    return "v1cand_" + _hash({"identity": identity, "content_hash": content_hash})[:32], content_hash


def _evaluate_candidate(article: Mapping[str, Any], *, now: datetime) -> dict[str, Any]:
    candidate_key, source_content_hash = _candidate_identity(article)
    evidence_refs = sorted(set(str(value) for value in article.get("evidence_refs") or [] if str(value)))
    full_text = str(article.get("full_text") or "")
    word_count = len(re.findall(r"\b\w+\b", full_text, flags=re.UNICODE))
    entity_count = len(set(str(value) for value in article.get("entities") or [] if str(value)))
    performance = dict(article.get("performance") or {})
    best_performance = performance.get("best_qualified_engagement_score")
    performance_component = (
        min(1.0, max(0.0, float(best_performance)) / 10.0) * 0.10
        if isinstance(best_performance, (int, float)) and not isinstance(best_performance, bool)
        else 0.0
    )
    viewer_value_score = round(
        min(1.0, word_count / 900.0) * 0.35
        + min(1.0, len(evidence_refs) / 4.0) * 0.35
        + min(1.0, entity_count / 4.0) * 0.20
        + performance_component,
        6,
    )
    freshness = _freshness(article, now=now)
    qualification_inputs = {
        "policy_version": QUALIFICATION_POLICY_VERSION,
        "truth": {
            "lifecycle_confirmed_by_canonical_read_model": True,
            "content_status": article.get("content_status"),
            "content_hash": article.get("content_hash"),
        },
        "evidence": {
            "reference_count": len(evidence_refs),
            "minimum_reference_count": MIN_EVIDENCE_REFS,
        },
        "rights": {
            "candidate_transfer_scope": "V1_APPROVED_TEXT_AND_EVIDENCE_REFERENCES_ONLY",
            "visual_assets_transferred": False,
            "fresh_rights_safe_asset_discovery_required_before_storyboard": True,
            "known_rights_blockers": [],
        },
        "viewer_value": {
            "score": viewer_value_score,
            "minimum_score": MIN_VIEWER_VALUE_SCORE,
            "word_count": word_count,
            "entity_count": entity_count,
            "performance_priority_component": round(performance_component, 6),
        },
        "performance": performance,
        "priority_order": ["TRUTH", "EVIDENCE", "RIGHTS", "VIEWER_VALUE", "ABSTAIN"],
    }
    reasons: list[str] = []
    internal_decision = "ELIGIBLE"
    if freshness.get("future_timestamp"):
        internal_decision = "ABSTAIN"
        reasons.append("published_timestamp_in_future")
    elif not freshness.get("fresh"):
        internal_decision = "ABSTAIN"
        reasons.append("candidate_outside_freshness_window")
    elif article.get("content_status") != "CONTENT_AVAILABLE" or not re.fullmatch(
        r"[0-9a-f]{64}", str(article.get("content_hash") or "")
    ):
        internal_decision = "DEFERRED"
        reasons.append("approved_content_unavailable")
    elif len(evidence_refs) < MIN_EVIDENCE_REFS:
        internal_decision = "DEFERRED"
        reasons.append("insufficient_governed_evidence_references")
    elif word_count < MIN_CONTENT_WORDS:
        internal_decision = "DEFERRED"
        reasons.append("approved_content_too_thin_for_video_qualification")
    elif viewer_value_score < MIN_VIEWER_VALUE_SCORE:
        internal_decision = "DEFERRED"
        reasons.append("viewer_value_below_deterministic_threshold")
    else:
        reasons.append("truth_evidence_rights_boundary_and_viewer_value_eligible")

    version_material = {
        "candidate_key": candidate_key,
        "source_content_hash": source_content_hash,
        "evaluation_day_utc": freshness.get("evaluation_day_utc"),
        "evidence_refs": evidence_refs,
        "performance_observation_hashes": [
            item.get("observation_hash") for item in performance.get("observations") or []
        ],
        "freshness_status": freshness.get("status"),
        "future_timestamp": freshness.get("future_timestamp"),
        "policy_version": QUALIFICATION_POLICY_VERSION,
    }
    return {
        "candidate_key": candidate_key,
        "candidate_version_id": "v1candver_" + _hash(version_material)[:32],
        "source_content_hash": source_content_hash,
        "internal_decision": internal_decision,
        "decision": internal_decision,
        "reason_codes": reasons,
        "freshness": freshness,
        "evidence_refs": evidence_refs,
        "qualification_inputs": qualification_inputs,
        "rank_key": (
            viewer_value_score,
            float(best_performance or 0.0),
            str(article.get("published_at_utc") or ""),
            candidate_key,
        ),
    }


def _source_identity(article: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "story_identity": article.get("story_identity"),
        "article_identity": article.get("article_identity"),
        "update_chain_identity": article.get("update_chain_identity"),
        "source_work_item_id": article.get("source_work_item_id"),
        "canonical_public_object_id": article.get("public_object_id"),
        "canonical_url_hash": article.get("canonical_url_hash"),
        "content_hash": article.get("content_hash"),
        "published_at_utc": article.get("published_at_utc"),
        "canonical_read_model": "published_corpus_read_model_v1.load_published_corpus",
    }


def _trigger_packet(
    article: Mapping[str, Any],
    evaluation: Mapping[str, Any],
    *,
    v1_snapshot_hash: str,
) -> dict[str, Any]:
    return {
        "schema": "contentops.v2.v1_readonly_trigger_packet.v1",
        "candidate_key": evaluation["candidate_key"],
        "candidate_version_id": evaluation["candidate_version_id"],
        "source_v1_identity": _source_identity(article),
        "candidate_source": {
            "title": article.get("title"),
            "article_mode": article.get("article_mode"),
            "entities": list(article.get("entities") or []),
            "approved_content": {
                "content_hash": article.get("content_hash"),
                "content_status": article.get("content_status"),
                "body_source": article.get("body_source"),
                "full_text": article.get("full_text"),
            },
        },
        "qualification": {
            "decision": evaluation["decision"],
            "reason_codes": evaluation["reason_codes"],
            "freshness": evaluation["freshness"],
            "inputs": evaluation["qualification_inputs"],
        },
        "evidence_refs": evaluation["evidence_refs"],
        "v1_read_snapshot_hash": v1_snapshot_hash,
        "factory_entry_state": "HIGH_GOVERNED_INPUT_EXPANSION_REQUIRED",
        "required_order": [
            "INSTITUTIONAL_ANALYTICAL_MAP",
            "EVIDENCE_EXPANSION",
            "VISUAL_ENTITY_AND_ASSET_NEEDS",
            "FRESH_RIGHTS_SAFE_ASSET_DISCOVERY",
            "CANDIDATE_ASSET_BOARD",
            "ASSET_VISUAL_FIT",
            "FRESH_XHIGH_EDITORIAL_AND_VISUAL_AUTHORSHIP",
            "HIGH_DETERMINISTIC_FACTORY_AND_QA",
        ],
        "hard_boundaries": {
            "public_write_authority": False,
            "v1_mutation_authority": False,
            "v1_scheduler_mutation_authority": False,
            "platform_adapter_authority": False,
            "performance_factual_or_numeric_authority": False,
            "model_factual_or_numeric_authority": False,
            "generated_real_person_documentary_media": False,
            "owner_acceptance_claimed": False,
        },
    }


def run_daily_operator(
    *,
    v1_store_path: str | Path,
    runtime_root: str | Path,
    operator_run_id: str,
    implementation_head: str,
    parent_session_label: str,
    parent_task_id: str | None = None,
    v1_output_root: str | Path | None = None,
    now: datetime | None = None,
    max_qualified: int = MAX_DAILY_QUALIFIED,
) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", operator_run_id):
        raise DailyOperatorError("operator_run_id_invalid")
    if not re.fullmatch(r"[0-9a-f]{40}", implementation_head):
        raise DailyOperatorError("implementation_head_must_be_exact_commit")
    if not parent_session_label.strip():
        raise DailyOperatorError("parent_session_label_required")
    if max_qualified < 0 or max_qualified > 2:
        raise DailyOperatorError("max_qualified_out_of_bounds")
    evaluated_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    runtime = Path(runtime_root).resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    store = V2JobStore(runtime / "v2_daily_operator_shadow.sqlite3")
    snapshot = read_v1_opportunities(v1_store_path, output_root=v1_output_root)

    evaluated = [
        (dict(article), _evaluate_candidate(article, now=evaluated_at))
        for article in snapshot["articles"]
    ]
    eligible = sorted(
        (item for item in evaluated if item[1]["internal_decision"] == "ELIGIBLE"),
        key=lambda item: item[1]["rank_key"],
        reverse=True,
    )
    selected = {item[1]["candidate_version_id"] for item in eligible[:max_qualified]}

    recorded: list[dict[str, Any]] = []
    created_job_count = 0
    for article, evaluation in evaluated:
        if evaluation["internal_decision"] == "ELIGIBLE":
            if evaluation["candidate_version_id"] in selected:
                evaluation["decision"] = "QUALIFIED"
                evaluation["reason_codes"] = [
                    "truth_evidence_rights_boundary_and_viewer_value_qualified"
                ]
            else:
                evaluation["decision"] = "DEFERRED"
                evaluation["reason_codes"] = ["daily_shadow_capacity_reached"]
        packet = _trigger_packet(
            article,
            evaluation,
            v1_snapshot_hash=str(snapshot["snapshot_hash"]),
        )
        packet_path = runtime / "candidate_packets" / f"{evaluation['candidate_version_id']}.json"
        _write_immutable_json(packet_path, packet)
        packet_hash = _hash(packet)
        source_identity = _source_identity(article)
        job_id = (
            "v2_" + str(evaluation["candidate_key"]).removeprefix("v1cand_")
            if evaluation["decision"] == "QUALIFIED"
            else None
        )
        priority = 1000 + int(
            round(float(evaluation["qualification_inputs"]["viewer_value"]["score"]) * 100)
        )
        decision_row = store.record_candidate_decision(
            candidate_version_id=str(evaluation["candidate_version_id"]),
            candidate_key=str(evaluation["candidate_key"]),
            operator_run_id=operator_run_id,
            candidate_source={
                "title": article.get("title"),
                "article_mode": article.get("article_mode"),
                "approved_content_hash": article.get("content_hash"),
                "approved_content_body_source": article.get("body_source"),
            },
            qualification_inputs=evaluation["qualification_inputs"],
            decision=str(evaluation["decision"]),
            reason_codes=list(evaluation["reason_codes"]),
            freshness=evaluation["freshness"],
            evidence_refs=list(evaluation["evidence_refs"]),
            source_v1_identity=source_identity,
            trigger_packet_path=packet_path,
            trigger_packet_hash=packet_hash,
            source_content_hash=str(evaluation["source_content_hash"]),
            video_job_id=job_id,
            target_format=TARGET_FORMAT,
            priority=priority,
        )
        created_job_count += int(bool(decision_row["job_created"]))
        recorded.append(
            {
                "candidate_version_id": evaluation["candidate_version_id"],
                "candidate_key": evaluation["candidate_key"],
                "decision": evaluation["decision"],
                "reason_codes": evaluation["reason_codes"],
                "freshness": evaluation["freshness"],
                "evidence_ref_count": len(evaluation["evidence_refs"]),
                "viewer_value_score": evaluation["qualification_inputs"]["viewer_value"]["score"],
                "source_v1_identity": source_identity,
                "trigger_packet_path": str(packet_path),
                "trigger_packet_hash": packet_hash,
                "video_job_id": decision_row.get("video_job_id"),
                "job_created": bool(decision_row["job_created"]),
                "idempotent_replay": bool(decision_row["idempotent_replay"]),
                "public_write_authority": False,
            }
        )

    qualified_count = sum(item["decision"] == "QUALIFIED" for item in recorded)
    result = (
        "QUALIFIED_JOB_WAITING_GOVERNED_INPUT"
        if qualified_count
        else "NO_GENUINE_QUALIFIED_CANDIDATE_NO_VIDEO"
    )
    review_queue = store.daily_review_queue()
    summary = {
        "schema": SCHEMA,
        "operator_run_id": operator_run_id,
        "implementation_head": implementation_head,
        "evaluated_at_utc": evaluated_at.isoformat().replace("+00:00", "Z"),
        "parent": {
            "runtime": "CODEX_DESKTOP_APP_STANDALONE_SCHEDULED_TASK",
            "session_label": parent_session_label,
            "task_id": parent_task_id,
            "model": PARENT_MODEL,
            "reasoning_effort": PARENT_REASONING_EFFORT,
            "provenance_source": "CODEX_DESKTOP_APP_AUTOMATION_CONFIGURATION",
        },
        "v1_read": {
            key: snapshot[key]
            for key in (
                "store_path",
                "read_surface",
                "canonical_publication_contract",
                "article_count",
                "snapshot_hash",
                "read_only_proof",
                "table_counts",
                "second_v1_store_created",
                "v1_mutation_authority",
            )
        },
        "qualification_policy_version": QUALIFICATION_POLICY_VERSION,
        "candidate_decisions": recorded,
        "decision_count": len(recorded),
        "qualified_count": qualified_count,
        "deferred_count": sum(item["decision"] == "DEFERRED" for item in recorded),
        "abstain_count": sum(item["decision"] == "ABSTAIN" for item in recorded),
        "created_job_count": created_job_count,
        "review_queue": review_queue,
        "result": result,
        "next_action": (
            "HIGH_EXPAND_GOVERNED_INPUT_THEN_CREATE_FRESH_ISOLATED_XHIGH_CHILD"
            if qualified_count
            else "NO_VIDEO_SHADOW_ISOLATION_PROBE_ALLOWED"
        ),
        "fresh_xhigh_child_created": False,
        "zero_write": {
            "v1_write_count": 0,
            "platform_public_write_count": 0,
            "v1_scheduler_mutation_count": 0,
            "publication_adapter_invocation_count": 0,
            "creative_cli_invocation_count": 0,
            "creative_sdk_api_invocation_count": 0,
            "creative_9router_invocation_count": 0,
            "public_write_authority": False,
        },
    }
    store.record_operator_run(
        operator_run_id=operator_run_id,
        summary=summary,
        parent_model=PARENT_MODEL,
        parent_reasoning_effort=PARENT_REASONING_EFFORT,
        parent_task_id=parent_task_id,
        v1_read_snapshot_hash=str(snapshot["snapshot_hash"]),
        decision_count=len(recorded),
        qualified_count=qualified_count,
        created_job_count=created_job_count,
        result=result,
    )
    receipt_path = runtime / "runs" / operator_run_id / "daily_operator_result.json"
    _write_immutable_json(receipt_path, summary)
    summary["receipt_path"] = str(receipt_path)
    summary["receipt_hash"] = _hash(_load_object(receipt_path))
    return summary
