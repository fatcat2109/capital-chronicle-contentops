"""Versioned, nonsecret Final Daily App UI projection over the canonical store.

This module is read-model code only.  It opens the existing ContentOps durable store in
SQLite query-only mode and never calls a newsroom, publisher, provider, platform, browser,
or credential seam.  Missing state remains explicit rather than being converted to zero or
fixture success.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional
from urllib.parse import urlsplit

from live_contentops.daily_app_supervisor_v1 import (
    OPERATING_MODES,
    RECONCILE_CONFIRMED,
    RECONCILE_CONTROLLED_NO_WRITE,
    RECONCILE_PENDING_OPERATOR,
    RECONCILE_PENDING_READBACK,
    RECONCILE_PUBLIC_OBJECT_CONTENT_INCOMPLETE,
    STATUS_CONTROLLED_NO_WRITE,
    STATUS_DISPATCH_CONFIRMED,
    STATUS_UNKNOWN_WRITE,
    TRIGGER_SCHEDULED,
    build_bootstrap_editorial_window_policy,
    editorial_window_id,
)
from live_contentops.durable_operational_store_v1 import (
    ContentOpsDurableStore,
    OperatingModeConflictError,
    OperatorTriggerAlreadyPendingError,
)
from live_contentops.publishing_profile_registry_v1 import (
    CANONICAL_BROWSER_FAMILY,
    CANONICAL_PROFILE_ID,
    REGISTRY_VERSION as PUBLISHING_REGISTRY_VERSION,
)
from live_contentops.destination_transport_registry_v1 import (
    DESTINATION_TO_SURFACE,
    READY_STATES,
    REGISTRY_VERSION as TRANSPORT_REGISTRY_VERSION,
)
from live_contentops.daily_app_performance_v1 import (
    QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
    _normalized_policy_payload,
    qualified_engagement_score,
)
from live_contentops.contentops_observation_read_model_v1 import (
    build_observation_read_model,
)

SNAPSHOT_SCHEMA_VERSION = "contentops.daily_app_ui_snapshot.v1"
REQUIRED_STORE_SCHEMA_VERSION = 9
FRESH_SECONDS = 300
HEARTBEAT_TTL_SECONDS = 120

RUN_NOW_ENDPOINT = "/api/daily-app/control/run-now"
RUN_NOW_MODE_CONSEQUENCES = {
    "AUTONOMOUS_DEFAULT": (
        "Runs one governed editorial cycle now. A publishable package may be published "
        "automatically if every canonical gate passes."
    ),
    "SUPERVISED_OPERATOR_GATE": (
        "Runs one governed editorial cycle now; publication stays held under the existing "
        "supervised gate."
    ),
    "SHADOW_ONLY": "Runs one governed editorial cycle now with zero public writes.",
    "KILL_SWITCH": (
        "New manual cycles are not accepted while the kill switch is active. New public writes "
        "remain blocked; the kill switch is never cleared by this control."
    ),
}

TIER1_DESTINATIONS = (
    ("substack", "Substack", "BROWSER_AUTHENTICATED"),
    ("telegram", "Telegram", "NON_BROWSER_BINDING"),
    ("discord", "Discord", "NON_BROWSER_BINDING"),
    ("x", "X", "BROWSER_AUTHENTICATED"),
    ("linkedin", "LinkedIn", "OFFICIAL_MEMBER_API"),
    ("facebook_page", "Facebook Page", "NON_BROWSER_BINDING"),
    ("instagram_business", "Instagram Business", "NON_BROWSER_BINDING"),
    ("threads", "Threads", "NON_BROWSER_BINDING"),
    ("youtube", "YouTube Community", "BROWSER_AUTHENTICATED"),
)

_SECRET_KEY = re.compile(
    r"(^|_)(token|secret|password|authorization|cookie|private_key|webhook)(_|$)",
    re.IGNORECASE,
)


class DailyAppReadModelError(RuntimeError):
    """The canonical store could not be projected safely."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _json(value: Any, fallback: Any) -> Any:
    try:
        parsed = json.loads(str(value))
        return parsed
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _rows(conn: Any, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(sql, tuple(params)).fetchall()]


def _latest_time(rows: Iterable[Mapping[str, Any]], fields: Iterable[str]) -> Optional[datetime]:
    values = [
        parsed
        for row in rows
        for field in fields
        if (parsed := _parse_time(row.get(field))) is not None
    ]
    return max(values) if values else None


def _policy_provenance(
    row: Mapping[str, Any], payload: Mapping[str, Any]
) -> str:
    """Classify policy origin from durable lineage, never from ACTIVE status.

    The bootstrap row is an active policy because it schedules real windows, but it is
    still configured authority rather than measured learning.  A learned policy must carry
    parent lineage under the current durable contract.  Explicit bootstrap/default markers
    remain fail-closed even if a malformed row also claims lineage.
    """
    decision = str(row.get("decision") or "").upper()
    payload_provenance = str(payload.get("provenance") or "").upper()
    policy_version = str(row.get("policy_version") or "").lower()
    if (
        decision == "BOOTSTRAP"
        or payload_provenance == "CONFIGURED_DEFAULT"
        or ("bootstrap" in policy_version and not row.get("parent_policy_version"))
    ):
        return "CONFIGURED_DEFAULT"
    return "LEARNED" if row.get("parent_policy_version") else "CONFIGURED_DEFAULT"


def _policy_timing_offset_minutes(payload: Mapping[str, Any]) -> int:
    """Read the current nested timing contract with bounded legacy-flat compatibility."""
    timing = payload.get("timing")
    raw = timing.get("offset_minutes") if isinstance(timing, Mapping) else None
    if raw is None:
        raw = payload.get("timing_offset_minutes")
    try:
        return int(raw or 0)
    except (TypeError, ValueError):
        return 0


def _next_windows(
    now: datetime,
    active_policy: Optional[Mapping[str, Any]],
    *,
    consumed_window_ids: Iterable[str] = (),
) -> list[dict[str, Any]]:
    policy = build_bootstrap_editorial_window_policy()
    consumed = {str(value) for value in consumed_window_ids}
    # The four native Desktop schedules are owner authority. Learning can be shown as a
    # recommendation, but it cannot move a scheduled opportunity automatically.
    offset = 0
    active_provenance = str(active_policy.get("provenance") or "") if active_policy else ""
    windows: list[dict[str, Any]] = []
    for day_offset in range(0, 8):
        day = (now + timedelta(days=day_offset)).date()
        for window in policy.core_windows:
            if day.weekday() not in set(window.eligible_weekdays_utc):
                continue
            start = datetime(
                day.year, day.month, day.day, int(window.start_hour_utc),
                tzinfo=timezone.utc,
            ) + timedelta(minutes=offset)
            end = datetime(
                day.year, day.month, day.day, int(window.end_hour_utc),
                tzinfo=timezone.utc,
            ) + timedelta(minutes=offset)
            if end <= start:
                end += timedelta(days=1)
            if end > now:
                window_id = editorial_window_id(
                    policy_version=policy.policy_version,
                    window_start_utc=start,
                    window_end_utc=end,
                    session=window.session,
                    trigger_kind=TRIGGER_SCHEDULED,
                )
                if window_id in consumed:
                    continue
                windows.append({
                    "window_start_utc": _iso(start),
                    "window_end_utc": _iso(end),
                    "editorial_session": window.session,
                    "policy_version": (
                        str(active_policy["policy_version"]) if active_policy else policy.policy_version
                    ),
                    "provenance": (
                        "LEARNED_ACTIVE_POLICY"
                        if active_provenance == "LEARNED"
                        else "CONFIGURED_DEFAULT"
                    ),
                })
    return sorted(windows, key=lambda item: item["window_start_utc"])[:4]


def _dispatch_classification(dispatch: Mapping[str, Any]) -> str:
    status = str(dispatch.get("dispatch_status") or dispatch.get("status") or "")
    object_id = str(dispatch.get("public_object_id") or "")
    reconciliation = str(dispatch.get("reconciliation_status") or "")
    if status == STATUS_UNKNOWN_WRITE or "UNKNOWN_WRITE" in status:
        return "UNKNOWN_WRITE"
    if status in {STATUS_CONTROLLED_NO_WRITE, "DISPATCH_CONFIRMED_NO_WRITE"} or "NO_WRITE" in status:
        return "CONTROLLED_NO_PUBLIC_WRITE"
    if status == STATUS_DISPATCH_CONFIRMED and object_id and reconciliation == RECONCILE_CONFIRMED:
        return "REAL_PUBLICATION_CONFIRMED"
    if (
        status == STATUS_DISPATCH_CONFIRMED
        and object_id
        and reconciliation == RECONCILE_PUBLIC_OBJECT_CONTENT_INCOMPLETE
    ):
        return "CONFIRMED_PUBLICATION_CONTENT_INCOMPLETE"
    if status == STATUS_DISPATCH_CONFIRMED and object_id:
        return "CONFIRMED_DISPATCH_PENDING_READBACK"
    return "NOT_A_CONFIRMED_PUBLICATION"


def _assert_nonsecret(value: Any, path: str = "snapshot") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _SECRET_KEY.search(str(key)):
                raise DailyAppReadModelError(f"secret-shaped key blocked:{path}.{key}")
            _assert_nonsecret(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_nonsecret(child, f"{path}[{index}]")


_COCKPIT_STAGE_TO_STATE = {
    "HEADLINE_INGESTION": "INGESTING",
    "CANDIDATE_SELECTION": "PREPARING",
    "CC_CONTEXT": "PREPARING",
    "GROUNDED_RESEARCH": "RESEARCHING",
    "ARTICLE_WRITING": "WRITING",
    "FACTUAL_CHECK": "WRITING",
    "READER_VALUE_CHECK": "WRITING",
    "VISUAL_DISCOVERY": "MEDIA_BUILDING",
    "MEDIA_BUILD": "MEDIA_BUILDING",
    "PACKAGE_BUILD": "PACKAGING",
    "PUBLICATION_JIT": "PUBLISHING",
    "CANONICAL_DISPATCH": "PUBLISHING",
    "DERIVATIVE_DISPATCH": "PUBLISHING",
    "CANONICAL_READBACK": "READING_BACK",
    "RECONCILIATION": "RECONCILING",
}
_COCKPIT_TIMELINE = (
    ("HEADLINE_INGESTION", "Intake"),
    ("CANDIDATE_SELECTION", "Select"),
    ("CC_CONTEXT", "CC context"),
    ("GROUNDED_RESEARCH", "Research"),
    ("ARTICLE_WRITING", "Write"),
    ("MEDIA_BUILD", "Media"),
    ("FACTUAL_CHECK", "Fact check"),
    ("READER_VALUE_CHECK", "Reader value"),
    ("PACKAGE_BUILD", "Package"),
    ("PUBLICATION_JIT", "JIT ready"),
    ("CANONICAL_DISPATCH", "Publish"),
    ("CANONICAL_READBACK", "Readback"),
    ("DERIVATIVE_DISPATCH", "Derivatives"),
    ("RECONCILIATION", "Reconcile"),
)
_EDITORIAL_SURFACES = frozenset({
    "daily_app_editorial_window", "daily_app_material_event_window",
})


def _safe_substack_public_url(value: Any) -> Optional[str]:
    """Expose only Capital Chronicle canonical article URLs, never arbitrary/raw URLs."""
    try:
        parsed = urlsplit(str(value or "").strip())
    except ValueError:
        return None
    slug = parsed.path.rstrip("/").removeprefix("/p/")
    if not (
        parsed.scheme == "https"
        and (parsed.hostname or "").casefold() == "capitalchronicle.substack.com"
        and parsed.path.rstrip("/").startswith("/p/")
        and slug
        and slug != "pending-publication"
        and not parsed.username
        and not parsed.password
        and not parsed.query
        and not parsed.fragment
    ):
        return None
    return f"https://capitalchronicle.substack.com/p/{slug}"


def _bounded_operator_text(value: Any, *, limit: int = 160) -> Optional[str]:
    from live_contentops.runtime_activity_projection_v1 import safe_operator_label

    return safe_operator_label(value, limit=limit)


def _cycle_display_summary(output_dir: Path) -> dict[str, Any]:
    """Extract only bounded operator-facing facts from canonical cycle artifacts."""
    evidence = _read_json_file(output_dir / "rolling_x_newsroom_cycle_evidence_v1.json")
    viability = evidence.get("ranked_viability")
    viability = viability if isinstance(viability, Mapping) else {}
    selected = viability.get("selected_cluster")
    selected = selected if isinstance(selected, Mapping) else {}
    article = evidence.get("article")
    article = article if isinstance(article, Mapping) else {}
    selected_evidence = viability.get("selected_evidence")
    selected_evidence = selected_evidence if isinstance(selected_evidence, Mapping) else {}
    candidate_walk = evidence.get("candidate_walk")
    candidate_walk = candidate_walk if isinstance(candidate_walk, Mapping) else {}
    walk_attempts = [
        row
        for row in (candidate_walk.get("candidate_attempts") or [])
        if isinstance(row, Mapping)
    ]
    selected_publication = candidate_walk.get("selected_publication_candidate")
    selected_publication = (
        selected_publication if isinstance(selected_publication, Mapping) else {}
    )
    ranked = evidence.get("ranked_assignment")
    ranked = ranked if isinstance(ranked, Mapping) else {}
    story_label = (
        _bounded_operator_text(article.get("title"))
        or _bounded_operator_text(selected.get("selection_case"))
        or _bounded_operator_text(selected.get("why_now"))
    )
    return {
        "story_label": story_label,
        "candidate_rank": selected_publication.get("rank") or viability.get("selected_rank"),
        "candidate_count": int(
            candidate_walk.get("ranked_candidate_count")
            or viability.get("ranked_candidate_count")
            or len(ranked.get("ranked_clusters") or [])
        ),
        "candidates_attempted": int(candidate_walk.get("attempted_candidate_count") or 0),
        "candidate_terminal_reasons": [
            {
                "rank": int(row.get("rank") or 0),
                "title": _bounded_operator_text(
                    row.get("article_title") or row.get("candidate_title"), limit=120
                ),
                "terminal_reason": _bounded_operator_text(
                    row.get("terminal_reason"), limit=180
                ),
            }
            for row in walk_attempts[:12]
        ],
        "selected_publication_candidate": {
            "rank": selected_publication.get("rank"),
            "title": _bounded_operator_text(
                selected_publication.get("candidate_title"), limit=120
            ),
        }
        if selected_publication
        else None,
        "opportunity_terminal_reason": _bounded_operator_text(
            candidate_walk.get("opportunity_terminal_reason"), limit=180
        ),
        "grounding": (
            "source-bound evidence"
            if selected_evidence.get("status") == "PASS"
            else "grounding unavailable"
        ),
        "research_result": str(
            selected_evidence.get("status")
            or evidence.get("exact_next_blocker")
            or "NOT_RECORDED"
        ),
        "classification": str(evidence.get("classification") or "NOT_RECORDED"),
        "exact_reason": _bounded_operator_text(evidence.get("exact_next_blocker"), limit=180),
    }


def _runtime_sha_short(store_path: Path) -> str:
    identity = _read_json_file(
        store_path.parent / "one_click_launcher" / "runtime_identity_v1.json"
    )
    source_sha = str(identity.get("source_sha") or "").strip().lower()
    return source_sha[:12] if re.fullmatch(r"[0-9a-f]{7,64}", source_sha) else "UNAVAILABLE"


def _duration_seconds(start: Any, end: Any) -> Optional[int]:
    started = _parse_time(start)
    finished = _parse_time(end)
    if started is None or finished is None:
        return None
    return max(0, int((finished - started).total_seconds()))


def build_daily_app_snapshot(
    store_path: str | Path,
    *,
    now: Optional[datetime] = None,
    runtime_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Project one truthful UI snapshot from the configured canonical durable store."""
    generated = (now or _utc_now()).astimezone(timezone.utc)
    path = Path(store_path).resolve()
    if not path.is_file():
        raise DailyAppReadModelError("configured durable store does not exist")
    store = ContentOpsDurableStore(path, auto_migrate=False)
    hourly_audit = _read_json_file(path.parent / "hourly_audit" / "latest.json")
    if not hourly_audit:
        hourly_audit = {
            "schema_version": "contentops.hourly_runtime_audit.latest_pointer.v1",
            "status": "AUDIT_NOT_YET_AVAILABLE",
            "classification": "UNKNOWN",
            "generated_at_utc": None,
        }
    try:
        with store.get_read_only_connection() as conn:
            if str(conn.execute("PRAGMA integrity_check").fetchone()[0]).lower() != "ok":
                raise DailyAppReadModelError("durable store integrity check failed")
            schema = int(conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] or 0)
            if schema != REQUIRED_STORE_SCHEMA_VERSION:
                raise DailyAppReadModelError(
                    f"durable store schema mismatch:expected={REQUIRED_STORE_SCHEMA_VERSION}:actual={schema}"
                )
            controls = dict(conn.execute(
                "SELECT * FROM operating_controls WHERE singleton_id=1"
            ).fetchone() or {})
            if not controls or controls.get("operating_mode") not in OPERATING_MODES:
                raise DailyAppReadModelError("canonical operating control missing or invalid")

            work_items = _rows(conn, "SELECT * FROM work_items ORDER BY updated_at DESC, work_item_id")
            transitions = _rows(conn, "SELECT event_id,work_item_id,event_kind,event_seq,from_state,to_state,reason_code,policy_version,model_version,timestamp_utc,event_hash FROM transition_events ORDER BY timestamp_utc DESC,event_id DESC")
            heartbeats = _rows(conn, "SELECT heartbeat_id,worker_id,last_seen_at,status FROM heartbeats ORDER BY last_seen_at DESC")
            invocations = _rows(conn, "SELECT invocation_id,work_item_id,model_id,prompt_tokens,completion_tokens,invoked_at FROM model_invocations ORDER BY invoked_at DESC")
            outbox = {row["message_id"]: row for row in _rows(conn, "SELECT message_id,work_item_id,destination,status,created_at FROM outbox_messages")}
            dispatch_rows = _rows(conn, "SELECT * FROM platform_dispatches ORDER BY dispatched_at DESC,dispatch_id DESC")
            readbacks = _rows(conn, "SELECT readback_id,dispatch_id,readback_data,read_at FROM readbacks ORDER BY read_at DESC")
            reconciliations = _rows(conn, "SELECT * FROM reconciliations ORDER BY reconciled_at DESC")
            incident_rows = _rows(conn, "SELECT * FROM incidents ORDER BY created_at DESC")
            observations = _rows(conn, "SELECT * FROM performance_observations ORDER BY scheduled_for_utc DESC,observation_id")
            policies = _rows(conn, "SELECT * FROM learning_policy_versions ORDER BY created_at_utc DESC,policy_version DESC")
            metrics = _rows(conn, "SELECT metric_id,metric_name,metric_value,recorded_at FROM metrics")
            readiness_rows = _rows(conn, "SELECT * FROM destination_readiness ORDER BY platform,surface")
            operator_trigger_rows = _rows(conn, "SELECT * FROM operator_cycle_triggers ORDER BY requested_at_utc DESC, trigger_id DESC")
            review_count = int(conn.execute("SELECT COUNT(*) FROM review_records").fetchone()[0])
            artifact_count = int(conn.execute("SELECT COUNT(*) FROM artifact_references").fetchone()[0])
            event_count = len(transitions)
    except DailyAppReadModelError:
        raise
    except Exception as exc:
        raise DailyAppReadModelError(f"durable store projection failed:{type(exc).__name__}") from exc

    latest_operator_trigger = (
        _sanitize_operator_trigger(operator_trigger_rows[0]) if operator_trigger_rows else None
    )
    try:
        active_cycle_windows = list(store.active_editorial_cycle_window_ids())
    except Exception:  # noqa: BLE001 - an unreadable lease view stays explicit, never invented
        active_cycle_windows = []

    recon_by_suffix = {
        str(row["reconciliation_id"]).removeprefix("reconciliation_"): row
        for row in reconciliations
    }
    readbacks_by_dispatch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in readbacks:
        parsed = _json(row.get("readback_data"), {})
        readbacks_by_dispatch[str(row["dispatch_id"])].append({
            "readback_id": row["readback_id"],
            "read_at_utc": row["read_at"],
            "verified": parsed.get("verified") if isinstance(parsed, Mapping) else None,
            "status": (
                parsed.get("readback_status") if isinstance(parsed, Mapping) else "UNAVAILABLE"
            ) or "STATUS_NOT_RECORDED",
        })

    publications: list[dict[str, Any]] = []
    for dispatch in dispatch_rows:
        message = outbox.get(dispatch["message_id"], {})
        suffix = str(dispatch["dispatch_id"]).removeprefix("dispatch_")
        reconciliation = recon_by_suffix.get(suffix, {})
        row = {
            "work_item_id": message.get("work_item_id"),
            "story_id": next((w["story_id"] for w in work_items if w["work_item_id"] == message.get("work_item_id")), None),
            "platform": dispatch["platform"],
            "destination": message.get("destination") or dispatch["platform"],
            "dispatch_id": dispatch["dispatch_id"],
            "public_object_id": dispatch.get("public_object_id"),
            "public_object_url_hash": dispatch.get("public_object_url_hash"),
            "canonical_public_url": (
                _safe_substack_public_url(dispatch.get("public_object_url"))
                if str(dispatch.get("platform") or "") == "substack" else None
            ),
            "dispatch_status": dispatch.get("status"),
            "readback_status": (
                readbacks_by_dispatch[str(dispatch["dispatch_id"])][0]["status"]
                if readbacks_by_dispatch[str(dispatch["dispatch_id"])] else "NO_READBACK_RECORDED"
            ),
            "readback_count": len(readbacks_by_dispatch[str(dispatch["dispatch_id"])]),
            "reconciliation_status": reconciliation.get("status") or "NO_RECONCILIATION_RECORDED",
            "dispatched_at_utc": dispatch.get("dispatched_at"),
            "observation_schedule": [
                obs["scheduled_for_utc"] for obs in observations
                if obs["dispatch_id"] == dispatch["dispatch_id"]
            ],
            "learning_eligible": any(
                bool(obs.get("learning_eligible")) for obs in observations
                if obs["dispatch_id"] == dispatch["dispatch_id"]
            ),
        }
        row["lifecycle_classification"] = _dispatch_classification(row)
        publications.append(row)

    observation_models: list[dict[str, Any]] = []
    for row in observations:
        native = _json(row.get("metrics_native_json"), {})
        availability = _json(row.get("metric_availability_json"), {})
        score = qualified_engagement_score(
            native if isinstance(native, Mapping) else {},
            availability if isinstance(availability, Mapping) else {},
        )
        observation_models.append({
            "observation_id": row["observation_id"],
            "platform": row["platform"],
            "dispatch_id": row["dispatch_id"],
            "public_object_id": row["public_object_id"],
            "public_object_url_hash": row["public_object_url_hash"],
            "observation_window": row["observation_window"],
            "scheduled_for_utc": row["scheduled_for_utc"],
            "collected_at_utc": row["collected_at_utc"],
            "collection_status": row["collection_status"],
            "native_metrics": native if isinstance(native, Mapping) else {},
            "metric_availability": availability if isinstance(availability, Mapping) else {},
            "learning_eligible": bool(row["learning_eligible"]),
            "collector_capability_version": row["collector_capability_version"],
            "source_identity": row["source_identity"],
            "qualified_engagement_score": score if score is not None else "NO_SCORE",
            "qualified_engagement_formula_version": QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
            "limitations": [
                str(key) for key, state in (availability.items() if isinstance(availability, Mapping) else [])
                if str(state).upper() not in {"AVAILABLE", "SUPPORTED"}
            ],
        })

    policy_models: list[dict[str, Any]] = []
    for row in policies:
        payload = _json(row.get("policy_payload_json"), {})
        payload = _normalized_policy_payload(payload if isinstance(payload, Mapping) else {})
        policy_models.append({
            "policy_version": row["policy_version"],
            "parent_policy_version": row["parent_policy_version"],
            "status": row["status"],
            "decision": row["decision"],
            "provenance": _policy_provenance(row, payload),
            "sample_count": row["sample_count"],
            "confidence": row["confidence"],
            "formula_version": row["formula_version"],
            "timing_offset_minutes": _policy_timing_offset_minutes(payload),
            "timing_recommendations": dict(payload.get("timing") or {}),
            "content_recommendations": dict(payload.get("content") or {}),
            "seo_recommendations": dict(payload.get("seo") or {}),
            "package_recommendations": dict(payload.get("package") or {}),
            "schedule_owner_locked": bool(
                (payload.get("timing") or {}).get("owner_locked")
            ),
            "recommendations": _json(row.get("accepted_changes_json"), {}),
            "bounded_delta": _json(row.get("bounded_delta_json"), {}),
            "rollback_reference": row["rollback_reference"],
            "decision_reason": row["decision_reason"],
            "observation_ids": _json(row.get("observation_ids_json"), []),
            "created_at_utc": row["created_at_utc"],
            "evaluation_window": row["evaluation_window"],
        })
    active_policy = next((row for row in policy_models if row["status"] == "ACTIVE"), None)
    future_windows = _next_windows(
        generated,
        active_policy,
        consumed_window_ids=(row.get("work_item_id") for row in work_items),
    )

    latest_heartbeat = heartbeats[0] if heartbeats else None
    heartbeat_time = _parse_time(latest_heartbeat.get("last_seen_at") if latest_heartbeat else None)
    heartbeat_age = (generated - heartbeat_time).total_seconds() if heartbeat_time else None
    controller_health = (
        "HEALTHY" if heartbeat_age is not None and heartbeat_age <= HEARTBEAT_TTL_SECONDS
        and latest_heartbeat.get("status") == "ALIVE" else "OFFLINE"
    )
    all_state_rows = [
        *heartbeats, *work_items, *dispatch_rows, *readbacks, *reconciliations,
        *observations, *policies, *readiness_rows,
    ]
    source_updated = _latest_time(
        all_state_rows,
        ("last_seen_at", "updated_at", "created_at", "dispatched_at", "read_at", "reconciled_at", "collected_at_utc", "created_at_utc", "probed_at_utc"),
    )
    source_age = (generated - source_updated).total_seconds() if source_updated else None
    freshness_state = (
        "LIVE_CURRENT" if source_age is not None and source_age <= FRESH_SECONDS
        else "STALE" if source_age is not None else "UNAVAILABLE"
    )

    real_publications = [p for p in publications if p["lifecycle_classification"] == "REAL_PUBLICATION_CONFIRMED"]
    controlled = [p for p in publications if p["lifecycle_classification"] == "CONTROLLED_NO_PUBLIC_WRITE"]
    unknown = [p for p in publications if p["lifecycle_classification"] == "UNKNOWN_WRITE"]
    pending_recovery = [
        p for p in publications
        if p["lifecycle_classification"] == "CONFIRMED_DISPATCH_PENDING_READBACK"
        or p["reconciliation_status"] in {
            RECONCILE_PENDING_READBACK,
            RECONCILE_PENDING_OPERATOR,
        }
    ]
    latest_cycle = work_items[0] if work_items else None
    current_publications = [
        row for row in publications
        if latest_cycle and row["work_item_id"] == latest_cycle["work_item_id"]
    ]
    if any(row["lifecycle_classification"] == "UNKNOWN_WRITE" for row in current_publications):
        cycle_outcome = "UNKNOWN_WRITE"
    elif any(row["lifecycle_classification"] == "REAL_PUBLICATION_CONFIRMED" for row in current_publications):
        cycle_outcome = "PUBLISHED"
    elif any(row["lifecycle_classification"] == "CONTROLLED_NO_PUBLIC_WRITE" for row in current_publications):
        cycle_outcome = "CONTROLLED_NO_PUBLIC_WRITE"
    elif latest_cycle and latest_cycle["current_state"] in {"REJECTED", "EVIDENCE_BLOCKED"}:
        cycle_outcome = "NO_PUBLICATION"
    elif latest_cycle:
        cycle_outcome = str(latest_cycle["current_state"])
    else:
        cycle_outcome = "NO_CYCLE_RECORDED"

    terminal_work_states = {"CLOSED", "REJECTED", "COMPLETE"}
    work_state_by_id = {
        str(row["work_item_id"]): str(row["current_state"]) for row in work_items
    }
    durable_incident_history: list[dict[str, Any]] = []
    for row in incident_rows:
        linked_work_item = str(row.get("work_item_id") or "")
        current_actionable = bool(
            linked_work_item
            and linked_work_item in work_state_by_id
            and work_state_by_id[linked_work_item] not in terminal_work_states
        )
        durable_incident_history.append({
            "incident_id": row["incident_id"],
            "severity": row["severity"],
            "what_happened": row["description"],
            "safe_now": "New public writes remain governed by canonical gates.",
            "automatic_action": "The supervisor continues bounded readback and recovery when available.",
            "operator_action": "Inspect the linked lifecycle and follow the exact recovery state.",
            "work_item_id": row["work_item_id"],
            "created_at_utc": row["created_at"],
            "source": "durable.incidents",
            "current_actionable": current_actionable,
            "lifecycle_state": work_state_by_id.get(linked_work_item),
        })
    incidents: list[dict[str, Any]] = [
        dict(row) for row in durable_incident_history if row["current_actionable"]
    ]
    readiness_operator_action = {
        "REAUTH_REQUIRED": "Sign in again in the canonical destination session.",
        "AUTH_INVALID": "Renew or correct the configured destination authorization.",
        "IDENTITY_MISMATCH": "Restore the exact configured Capital Chronicle destination identity.",
        "PERMISSION_MISSING": "Grant the required provider-side destination permission.",
        "TRANSPORT_UNAVAILABLE": "Restore the locked destination transport; do not substitute a fallback.",
        "SESSION_UNAVAILABLE": "Configure or restore the exact destination binding.",
        "TRANSIENT_DEGRADED": "Allow bounded automatic health checks; inspect the provider if degradation persists.",
        "CAPABILITY_UNSUPPORTED": "Do not publish to this surface from the Tier-1 runtime.",
        "TOKEN_EXPIRING": "Reauthorize LinkedIn before the displayed expiry time.",
        "AUTH_UNAVAILABLE": "Complete the bounded LinkedIn official-member OAuth flow.",
    }
    for row in readiness_rows:
        state = str(row["readiness_state"])
        row_detail = _json(row.get("sanitized_detail_json"), {})
        if str(row["surface"]) == "LINKEDIN_POST" and (
            str(row.get("transport_type") or "") != "OFFICIAL_MEMBER_API"
            or str(row.get("probe_kind") or "") != "OFFICIAL_MEMBER_API_LOCAL_AUTH_METADATA"
        ):
            # Historical browser readiness is never authority after the official API cutover.
            state = "AUTH_UNAVAILABLE"
        elif str(row["surface"]) == "LINKEDIN_POST":
            state = str(row_detail.get("official_api_state") or "AUTH_UNAVAILABLE")
        if state in READY_STATES:
            continue
        incidents.append({
            "incident_id": f"derived:readiness:{row['surface']}",
            "severity": "HIGH" if state in {"REAUTH_REQUIRED", "AUTH_INVALID", "AUTH_UNAVAILABLE", "IDENTITY_MISMATCH", "PERMISSION_MISSING"} else "MEDIUM",
            "what_happened": state,
            "safe_now": "This destination is excluded from new writes; other exact READY destinations remain independent.",
            "automatic_action": (
                "No periodic LinkedIn browser navigation or automated login is performed."
                if str(row["surface"]) == "LINKEDIN_POST"
                else "The Daily App continues bounded read-only health checks and safe recovery."
            ),
            "operator_action": (
                "Run the bounded LinkedIn official-member OAuth helper and authorize Jim Pham."
                if str(row["surface"]) == "LINKEDIN_POST"
                and state in {"REAUTH_REQUIRED", "TOKEN_EXPIRING", "AUTH_UNAVAILABLE"}
                else readiness_operator_action.get(state, "Inspect the exact destination readiness state.")
            ),
            "work_item_id": None,
            "created_at_utc": row["probed_at_utc"],
            "source": "derived.destination_readiness",
        })
    for row in unknown:
        incidents.append({
            "incident_id": f"derived:{row['dispatch_id']}:unknown-write",
            "severity": "CRITICAL",
            "what_happened": "UNKNOWN_WRITE",
            "safe_now": "Automatic retry is stopped.",
            "automatic_action": "Read back and reconcile the exact dispatch identity.",
            "operator_action": "Recover only from the Incidents lifecycle; do not retry blindly.",
            "work_item_id": row["work_item_id"],
            "created_at_utc": row["dispatched_at_utc"],
            "source": "derived.platform_dispatches",
        })
    for row in pending_recovery:
        incidents.append({
            "incident_id": f"derived:{row['dispatch_id']}:pending-reconciliation",
            "severity": "HIGH",
            "what_happened": row["reconciliation_status"],
            "safe_now": "No retry is authorized while lifecycle truth is pending.",
            "automatic_action": "The supervisor will retry bounded readback after cooldown.",
            "operator_action": "Intervene only if the state becomes pending operator recovery.",
            "work_item_id": row["work_item_id"],
            "created_at_utc": row["dispatched_at_utc"],
            "source": "derived.reconciliations",
        })
    if controller_health == "OFFLINE" and controls["operating_mode"] != "KILL_SWITCH":
        incidents.append({
            "incident_id": "derived:controller-offline",
            "severity": "HIGH",
            "what_happened": "No current supervisor heartbeat is available.",
            "safe_now": "The console remains read-only; durable lifecycle state is preserved.",
            "automatic_action": "No autonomous recovery can be claimed while the controller is offline.",
            "operator_action": "Verify the Daily App supervisor process and configured store binding.",
            "work_item_id": None,
            "created_at_utc": latest_heartbeat.get("last_seen_at") if latest_heartbeat else None,
            "source": "derived.heartbeats",
        })

    dispatch_by_platform: dict[str, dict[str, Any]] = {}
    for row in publications:
        # ``publications`` is newest-first; retain the first durable dispatch per platform.
        dispatch_by_platform.setdefault(str(row["platform"]), row)
    from live_contentops.daily_app_performance_v1 import current_metrics_capability_matrix
    metrics_capability_by_destination = {
        str(row["destination"]): row for row in current_metrics_capability_matrix()
    }
    readiness_by_surface = {str(row["surface"]): row for row in readiness_rows}
    platform_models = []
    for platform_id, display_name, binding_class in TIER1_DESTINATIONS:
        aliases = {platform_id}
        if platform_id == "youtube": aliases.add("youtube_community")
        last = next((dispatch_by_platform[a] for a in aliases if a in dispatch_by_platform), None)
        readiness = readiness_by_surface.get(DESTINATION_TO_SURFACE.get(platform_id, ""), {})
        readiness_state = str(readiness.get("readiness_state") or "READINESS_NOT_PROBED")
        if platform_id == "linkedin" and readiness and (
            str(readiness.get("transport_type") or "") != "OFFICIAL_MEMBER_API"
            or str(readiness.get("probe_kind") or "") != "OFFICIAL_MEMBER_API_LOCAL_AUTH_METADATA"
        ):
            readiness_state = "AUTH_UNAVAILABLE"
            readiness = {
                **readiness,
                "destination_identity": None,
                "identity_match": False,
                "probe_kind": "OFFICIAL_MEMBER_API_LOCAL_AUTH_METADATA",
                "transport_type": "OFFICIAL_MEMBER_API",
                "sanitized_detail_json": "{}",
            }
        sanitized_detail = _json(readiness.get("sanitized_detail_json"), {})
        if platform_id == "linkedin" and readiness:
            readiness_state = str(sanitized_detail.get("official_api_state") or "AUTH_UNAVAILABLE")
        platform_observations = [
            row for row in observation_models if str(row.get("platform") or "") in aliases
        ]
        platform_observations.sort(
            key=lambda row: str(row.get("scheduled_for_utc") or ""), reverse=True
        )
        next_observation = min(
            (
                row for row in platform_observations
                if row.get("collection_status") == "SCHEDULED"
            ),
            key=lambda row: str(row.get("scheduled_for_utc") or ""),
            default=None,
        )
        capability = metrics_capability_by_destination.get(platform_id, {})
        platform_models.append({
            "platform_id": platform_id,
            "display_name": display_name,
            "readiness": readiness_state,
            "write_eligible": readiness_state in READY_STATES,
            "binding_class": binding_class,
            "safe_identity": readiness.get("destination_identity") or (
                CANONICAL_PROFILE_ID if binding_class == "BROWSER_AUTHENTICATED"
                else "NONSECRET_BINDING_IDENTITY_UNAVAILABLE"
            ),
            "identity_match": bool(readiness.get("identity_match")) if readiness else None,
            "probe_kind": readiness.get("probe_kind"),
            "probed_at_utc": readiness.get("probed_at_utc"),
            "transport_type": readiness.get("transport_type"),
            "authenticated": bool(sanitized_detail.get("authenticated")) if platform_id == "linkedin" else None,
            "auth_expiry_at_utc": sanitized_detail.get("expiry_at_utc") if platform_id == "linkedin" else None,
            "auth_days_remaining": sanitized_detail.get("days_remaining") if platform_id == "linkedin" else None,
            "readback_capability": sanitized_detail.get("readback_capability") if platform_id == "linkedin" else None,
            "last_dispatch_state": last["lifecycle_classification"] if last else "NO_DISPATCH_RECORDED",
            "last_successful_readback_at_utc": (
                max((rb["read_at_utc"] for rb in readbacks_by_dispatch[str(last["dispatch_id"])]), default=None)
                if last else None
            ),
            "pending_incident": bool(last and last["lifecycle_classification"] == "UNKNOWN_WRITE"),
            "collector_capability": capability.get(
                "collector_state", "UNSUPPORTED_CURRENT_AUTHORIZED_RUNTIME"
            ),
            "observation_history": platform_observations,
            "observation_history_count": len(platform_observations),
            "metrics_supported": capability.get("metrics", []),
            "interaction_capability": capability.get(
                "interaction_text_observation", "UNSUPPORTED"
            ),
            "search_capability": capability.get(
                "search_console_channel", "OPERATOR_SETUP_REQUIRED"
            ),
            "next_observation_at_utc": (
                next_observation.get("scheduled_for_utc") if next_observation else None
            ),
            "next_metric_availability": "UNAVAILABLE_NOT_ZERO",
            "readiness_authority": TRANSPORT_REGISTRY_VERSION,
        })

    scheduled_observations = [o for o in observation_models if o["collection_status"] == "SCHEDULED"]
    queue_items = [
        {
            "queue_id": f"window:{window['window_start_utc']}",
            "kind": "EDITORIAL_WINDOW",
            "urgency": "UPCOMING",
            "title": window["editorial_session"],
            "due_at_utc": window["window_start_utc"],
            "state": window["provenance"],
            "detail": f"Policy {window['policy_version']}",
        }
        for window in future_windows
    ]
    queue_items.extend({
        "queue_id": f"observation:{row['observation_id']}",
        "kind": "PERFORMANCE_OBSERVATION",
            "urgency": "DUE" if (
                _parse_time(row["scheduled_for_utc"]) is not None
                and _parse_time(row["scheduled_for_utc"]) <= generated
            ) else "UPCOMING",
        "title": f"{row['platform']} · {row['observation_window']}",
        "due_at_utc": row["scheduled_for_utc"],
        "state": row["collection_status"],
        "detail": row["collector_capability_version"],
    } for row in scheduled_observations)
    queue_items.extend({
        "queue_id": f"recovery:{row['dispatch_id']}",
        "kind": "LIFECYCLE_RECOVERY",
        "urgency": "IMMEDIATE",
        "title": f"{row['platform']} readback / reconciliation",
        "due_at_utc": row["dispatched_at_utc"],
        "state": row["reconciliation_status"],
        "detail": "STOP RETRY → READ BACK → RECONCILE",
    } for row in pending_recovery)

    epoch = next((row for row in metrics if row["metric_id"] == "metric_contentops_production_epoch_start_utc"), None)
    production_epoch = (
        _iso(datetime.fromtimestamp(float(epoch["metric_value"]), tz=timezone.utc)) if epoch else None
    )
    latest_transition = transitions[0] if transitions else None
    prompt_tokens = sum(int(row.get("prompt_tokens") or 0) for row in invocations)
    completion_tokens = sum(int(row.get("completion_tokens") or 0) for row in invocations)

    headline_ingestion_state = {
        "lane_state": "UNAVAILABLE",
        "last_ingest_utc": None,
        "latest_capture_at_utc": None,
        "latest_capture_result": "UNAVAILABLE",
        "rows_last_iteration": 0,
        "newest_source_event_at_utc": None,
        "newest_source_event_age_seconds": None,
        "failure_class": None,
        "failure_detail": None,
        "eligibility_reason": None,
        "browser_role": "CHROME_CDP_9222_INGESTION_ONLY",
        "chrome_9222_readiness": "UNAVAILABLE",
        "auth_classification": "UNAVAILABLE",
    }
    rolling_24h_unique_headlines: Optional[int] = None
    try:
        from live_contentops.continuous_headline_ingest_v1 import (
            OUTCOME_BROWSER_BINDING_MISSING,
            OUTCOME_CAPTURED_NEW,
            OUTCOME_CAPTURED_NONE,
            OUTCOME_CAPTURE_FAILED,
            OUTCOME_CDP_UNAVAILABLE,
            OUTCOME_PORT_OWNER_UNPROVEN,
            OUTCOME_REAUTH_REQUIRED,
            ingestion_lane_state,
            next_due_interval_seconds,
            read_ingestion_checkpoint,
        )

        checkpoint = read_ingestion_checkpoint(store)
        last_epoch = checkpoint["last_success_epoch"]
        last_attempt = checkpoint["last_attempt_epoch"]
        interval = next_due_interval_seconds(
            checkpoint["consecutive_empty"],
            last_outcome_code=checkpoint["last_outcome_code"],
            hot_followup_pending=checkpoint["hot_followup_pending"],
        )
        lane_state = ingestion_lane_state(checkpoint["last_outcome_code"])
        outcome_label = {
            OUTCOME_CAPTURED_NEW: "CAPTURED_NEW",
            OUTCOME_CAPTURED_NONE: "CAPTURED_NO_NEW_HEADLINES",
            OUTCOME_REAUTH_REQUIRED: "REAUTH_REQUIRED",
            OUTCOME_CDP_UNAVAILABLE: "CDP_UNAVAILABLE",
            OUTCOME_CAPTURE_FAILED: "CAPTURE_FAILED",
            OUTCOME_BROWSER_BINDING_MISSING: "BROWSER_BINDING_MISSING",
            OUTCOME_PORT_OWNER_UNPROVEN: "PORT_OWNER_UNPROVEN",
        }.get(checkpoint["last_outcome_code"], "UNAVAILABLE")
        attempt_detail = checkpoint.get("last_attempt_detail") or {}
        headline_ingestion_state = {
            "lane_state": lane_state,
            "last_ingest_utc": (
                _iso(datetime.fromtimestamp(float(last_epoch), tz=timezone.utc)) if last_epoch else None
            ),
            "latest_capture_at_utc": (
                _iso(datetime.fromtimestamp(float(last_attempt), tz=timezone.utc))
                if last_attempt is not None else None
            ),
            "latest_capture_result": outcome_label,
            "rows_last_iteration": checkpoint["rows_last_iteration"],
            "next_eligible_capture_utc": (
                _iso(datetime.fromtimestamp(float(last_attempt) + interval, tz=timezone.utc))
                if last_attempt is not None and checkpoint["last_outcome_code"] != 2.0 else None
            ),
            "cadence_state": (
                "REAUTH_REQUIRED" if checkpoint["last_outcome_code"] == 2.0 else
                "HOT_FOLLOWUP_15M" if checkpoint["hot_followup_pending"] else
                "EMPTY_BACKOFF_60M" if checkpoint["last_outcome_code"] == 1.0 else
                "TRANSIENT_BACKOFF_30M_PLUS"
                if checkpoint["last_outcome_code"] in {3.0, 4.0, 5.0, 6.0}
                else "NORMAL_30M"
            ),
            "failure_class": attempt_detail.get("failure_class"),
            "failure_detail": attempt_detail.get("failure_detail"),
            "eligibility_reason": attempt_detail.get("eligibility_reason"),
            "browser_role": attempt_detail.get("browser_role") or "CHROME_CDP_9222_INGESTION_ONLY",
            "chrome_9222_readiness": attempt_detail.get("chrome_9222_readiness") or "UNAVAILABLE",
            "auth_classification": attempt_detail.get("auth_classification") or "UNAVAILABLE",
            "capture_phase": attempt_detail.get("capture_phase"),
            "timeline_responses_observed": int(attempt_detail.get("timeline_responses_observed") or 0),
            "attempt_detail_schema_version": attempt_detail.get("schema_version"),
        }
        if controls["operating_mode"] == "KILL_SWITCH":
            headline_ingestion_state["checkpoint_lane_state"] = headline_ingestion_state["lane_state"]
            headline_ingestion_state["lane_state"] = "PAUSED_KILL_SWITCH"
            headline_ingestion_state["pause_reason"] = "OPERATOR_KILL_SWITCH_NO_BACKGROUND_BROWSER_NAVIGATION"
        from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_glob
        from live_contentops.newsroom_assignment_scheduler_v1 import (
            load_rolling_x_headline_sidecars,
        )

        intake = load_rolling_x_headline_sidecars(
            cutoff_utc=generated,
            sidecar_glob=canonical_headline_sidecar_glob(),
            window_hours=24.0,
        )
        intake_headlines = list(intake.get("headlines") or [])
        rolling_24h_unique_headlines = len(intake_headlines)
        newest_source_time = max(
            (_parse_time(row.get("source_timestamp_utc")) for row in intake_headlines),
            default=None,
        )
        headline_ingestion_state["newest_source_event_at_utc"] = (
            _iso(newest_source_time) if newest_source_time else None
        )
        headline_ingestion_state["newest_source_event_age_seconds"] = (
            max(0, int((generated - newest_source_time).total_seconds()))
            if newest_source_time else None
        )
    except Exception:  # noqa: BLE001 - truth stays explicit when intelligence is unavailable
        rolling_24h_unique_headlines = None

    from live_contentops.browser_interaction_budget_v1 import browser_interaction_summary
    browser_automation = browser_interaction_summary(
        path.parent / "control" / "browser_interaction_budget_v1", now=generated
    )

    capital_chronicle_read_model_state = "UNAVAILABLE"
    try:
        from live_contentops.capital_chronicle_data_catalog_v1 import (
            DEFAULT_CC_ROOT,
        )

        capital_chronicle_read_model_state = "READY" if DEFAULT_CC_ROOT.is_dir() else "UNAVAILABLE"
    except Exception:  # noqa: BLE001
        capital_chronicle_read_model_state = "UNAVAILABLE"

    published_today_count = 0
    published_corpus_count = 0
    daily_target_band = [0, 4]
    try:
        from live_contentops.editorial_portfolio_v1 import DAILY_TARGET_BAND
        from live_contentops.published_corpus_read_model_v1 import load_published_corpus

        corpus = load_published_corpus(store)
        published_corpus_count = corpus["article_count"]
        daily_target_band = list(DAILY_TARGET_BAND)
        for article in corpus["articles"]:
            try:
                published_dt = datetime.fromisoformat(str(article.published_at_utc).replace("Z", "+00:00"))
                if published_dt.tzinfo is None:
                    published_dt = published_dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            published_utc = published_dt.astimezone(timezone.utc)
            if generated.date() == published_utc.date():
                published_today_count += 1
    except Exception:  # noqa: BLE001
        published_corpus_count = 0

    latest_editorial_classification = "UNAVAILABLE"
    latest_article_update_mode = "UNAVAILABLE"
    latest_cc_matched_store_count: Optional[int] = None
    latest_prior_related_article_title: Optional[str] = None
    latest_prior_related_article_identity: Optional[str] = None
    latest_material_delta_status = "UNAVAILABLE"
    latest_decision_reason = "NO_GOVERNED_CYCLE_RECORDED"
    latest_stage_stopped = "NOT_STARTED"
    if latest_cycle:
        cycle_output = path.parent / "daily_app_outputs" / str(latest_cycle["work_item_id"])
        cycle_evidence = _read_json_file(
            cycle_output / "rolling_x_newsroom_cycle_evidence_v1.json"
        )
        selected = (cycle_evidence.get("ranked_viability") or {}).get("selected_cluster")
        if not isinstance(selected, Mapping):
            preselection = _read_json_file(cycle_output / "preselection_intelligence_v1.json")
            candidates = [
                row for row in [
                    *(preselection.get("ranked_clusters") or []),
                    *(preselection.get("held_clusters") or []),
                ] if isinstance(row, Mapping)
            ]
            selected = candidates[0] if candidates else {}
        latest_editorial_classification = str(
            selected.get("editorial_classification") or "UNAVAILABLE"
        )
        latest_article_update_mode = str(
            selected.get("resolved_article_mode") or "UNAVAILABLE"
        )
        cc_context = selected.get("capital_chronicle_context")
        if isinstance(cc_context, Mapping):
            latest_cc_matched_store_count = int(
                cc_context.get("matched_store_count") or 0
            )
        novelty = selected.get("preselection_novelty")
        novelty = novelty if isinstance(novelty, Mapping) else {}
        latest_prior_related_article_title = (
            str(novelty.get("best_prior_title")) if novelty.get("best_prior_title") else None
        )
        latest_prior_related_article_identity = (
            str(novelty.get("best_prior_article"))
            if novelty.get("best_prior_article") else None
        )
        delta = novelty.get("material_delta_evaluation")
        if isinstance(delta, Mapping):
            latest_material_delta_status = str(
                delta.get("delta_summary") or "NO_EXPLICIT_MATERIAL_DELTA"
            )
        cycle_classification = str(cycle_evidence.get("classification") or "")
        if latest_editorial_classification == "UNAVAILABLE" and (
            cycle_classification == "NO_PUBLICATION"
            or latest_cycle.get("current_state") in {"REJECTED", "EVIDENCE_BLOCKED"}
        ):
            latest_editorial_classification = "NO_PUBLICATION"
        latest_decision_reason = str(
            cycle_evidence.get("exact_next_blocker")
            or (
                latest_transition.get("reason_code")
                if latest_transition
                and latest_transition.get("work_item_id") == latest_cycle.get("work_item_id")
                else latest_cycle.get("current_state")
            )
            or "UNAVAILABLE"
        )
        if (cycle_output / "native_payloads_rehearsal_v1.json").is_file():
            latest_stage_stopped = "PLATFORM_PACKAGE"
        elif cycle_evidence.get("editorial_cycle"):
            latest_stage_stopped = "SEMANTIC_REVIEW"
        elif cycle_evidence.get("article"):
            latest_stage_stopped = "ARTICLE_GENERATION"
        elif cycle_evidence.get("ranked_viability"):
            latest_stage_stopped = "TARGETED_EVIDENCE"
        elif (cycle_output / "rolling_x_assignment_v1.json").is_file():
            latest_stage_stopped = "ASSIGNMENT"
        elif (cycle_output / "rolling_x_intake_v1.json").is_file():
            latest_stage_stopped = "INTAKE"
        elif latest_cycle.get("current_state") == "EVIDENCE_PENDING":
            latest_stage_stopped = "CANONICAL_CYCLE_IN_PROGRESS"

    pending_material_events = [
        row for row in work_items
        if row.get("target_surface") == "daily_app_material_event_window"
        and row.get("current_state") == "DISCOVERED"
    ]
    material_event_wake_state = (
        "PENDING_DURABLE_MATERIAL_EVENT"
        if pending_material_events
        else "READY_NO_PENDING_MATERIAL_EVENT"
    )
    shutdown_blockers: list[str] = []
    if active_cycle_windows:
        shutdown_blockers.append("ACTIVE_EDITORIAL_CYCLE")
    if latest_operator_trigger and str(latest_operator_trigger.get("state") or "").upper() == "PENDING":
        shutdown_blockers.append("OPERATOR_TRIGGER_PENDING")
    if unknown:
        shutdown_blockers.append("UNKNOWN_WRITE_PRESENT")
    if pending_recovery:
        shutdown_blockers.append("PENDING_READBACK_OR_LIFECYCLE_RECOVERY_PRESENT")

    # V1 cockpit projection: current-stage telemetry is accepted only when the durable store
    # says the exact editorial work item has an active lease. Everything else below comes from
    # canonical durable rows or bounded, already-written local artifacts.
    editorial_items = [
        row for row in work_items if str(row.get("target_surface") or "") in _EDITORIAL_SURFACES
    ]
    active_editorial_id = active_cycle_windows[0] if active_cycle_windows else None
    active_editorial_item = next(
        (row for row in editorial_items if row.get("work_item_id") == active_editorial_id),
        None,
    )
    from live_contentops.runtime_activity_projection_v1 import (
        ACTIVITY_FILE_NAME,
        load_runtime_activity,
    )

    active_activity: dict[str, Any] = {}
    active_cycle_summary: dict[str, Any] = {}
    if active_editorial_item:
        active_output = path.parent / "daily_app_outputs" / str(active_editorial_id)
        candidate_activity = load_runtime_activity(active_output / ACTIVITY_FILE_NAME)
        if (
            str(candidate_activity.get("work_item_id") or "") == str(active_editorial_id)
            and candidate_activity.get("active") is True
        ):
            active_activity = candidate_activity
        active_cycle_summary = _cycle_display_summary(active_output)

    browser_state = str(browser_automation.get("state") or "IDLE")
    current_stage = str(active_activity.get("current_stage") or "") or None
    heartbeat_status = str(latest_heartbeat.get("status") or "") if latest_heartbeat else ""
    pending_trigger = bool(
        latest_operator_trigger
        and str(latest_operator_trigger.get("state") or "").upper() == "PENDING"
    )
    if unknown or any(
        row.get("reconciliation_status") == RECONCILE_PENDING_OPERATOR
        for row in pending_recovery
    ):
        cockpit_primary_state = "ACTION_REQUIRED"
    elif controller_health == "OFFLINE":
        cockpit_primary_state = "STOPPED"
    elif heartbeat_status and heartbeat_status != "ALIVE":
        cockpit_primary_state = "STARTING"
    elif active_editorial_item:
        cockpit_primary_state = _COCKPIT_STAGE_TO_STATE.get(current_stage or "", "PREPARING")
    elif browser_state == "PUBLICATION_ACTIVE":
        cockpit_primary_state = "PUBLISHING"
    elif browser_state == "RECONCILIATION_ACTIVE":
        cockpit_primary_state = "RECONCILING"
    elif browser_state == "INGESTION_ACTIVE":
        cockpit_primary_state = "INGESTING"
    elif pending_recovery:
        cockpit_primary_state = "RECONCILING"
    elif controls["operating_mode"] == "KILL_SWITCH" or pending_trigger:
        cockpit_primary_state = "ACTION_REQUIRED"
    elif str(headline_ingestion_state.get("lane_state") or "") in {
        "DEGRADED", "UNAVAILABLE", "REAUTH_REQUIRED",
    }:
        cockpit_primary_state = "DEGRADED"
    else:
        cockpit_primary_state = "RUNNING_IDLE"

    completed_stages = {
        str(stage) for stage in (active_activity.get("completed_stages") or [])
    }
    cockpit_timeline = [
        {
            "stage": stage,
            "label": label,
            "state": (
                "current" if stage == current_stage
                else "completed" if stage in completed_stages
                else "pending"
            ),
        }
        for stage, label in _COCKPIT_TIMELINE
    ] if active_editorial_item else []

    publication_by_work_item: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for publication in publications:
        publication_by_work_item[str(publication.get("work_item_id") or "")].append(publication)

    def editorial_history_row(item: Mapping[str, Any]) -> dict[str, Any]:
        item_id = str(item.get("work_item_id") or "")
        summary = _cycle_display_summary(path.parent / "daily_app_outputs" / item_id)
        item_publications = publication_by_work_item.get(item_id, [])
        canonical = next(
            (
                row for row in item_publications
                if row.get("destination") == "substack" and row.get("canonical_public_url")
            ),
            None,
        )
        result = (
            str(canonical.get("lifecycle_classification")) if canonical
            else str(summary.get("classification") or "NOT_RECORDED")
        )
        if result == "NOT_RECORDED":
            result = str(item.get("current_state") or "NOT_RECORDED")
        return {
            "activity_type": "EDITORIAL_CYCLE",
            "work_item_id": item_id,
            "started_at_utc": item.get("created_at"),
            "completed_at_utc": item.get("updated_at"),
            "duration_seconds": _duration_seconds(item.get("created_at"), item.get("updated_at")),
            "story_label": summary.get("story_label"),
            "candidate_rank": summary.get("candidate_rank"),
            "candidate_count": summary.get("candidate_count"),
            "candidates_attempted": summary.get("candidates_attempted"),
            "candidate_terminal_reasons": summary.get("candidate_terminal_reasons"),
            "selected_publication_candidate": summary.get(
                "selected_publication_candidate"
            ),
            "opportunity_terminal_reason": summary.get(
                "opportunity_terminal_reason"
            ),
            "grounding": summary.get("grounding"),
            "research_result": summary.get("research_result"),
            "result": result,
            "exact_reason": summary.get("exact_reason"),
            "canonical_public_url": canonical.get("canonical_public_url") if canonical else None,
        }

    completed_editorial_items = [
        row for row in editorial_items
        if row.get("work_item_id") != active_editorial_id
        and str(row.get("current_state") or "") not in {"DISCOVERED", "EVIDENCE_PENDING"}
    ]
    last_completed_editorial = (
        editorial_history_row(completed_editorial_items[0])
        if completed_editorial_items else None
    )
    recent_activity = [editorial_history_row(row) for row in completed_editorial_items[:9]]
    if headline_ingestion_state.get("latest_capture_at_utc"):
        recent_activity.append({
            "activity_type": "X_INTAKE",
            "work_item_id": None,
            "started_at_utc": headline_ingestion_state.get("latest_capture_at_utc"),
            "completed_at_utc": headline_ingestion_state.get("latest_capture_at_utc"),
            "duration_seconds": None,
            "story_label": "Rolling X headline intake",
            "candidate_rank": None,
            "candidate_count": rolling_24h_unique_headlines,
            "grounding": "discovery and ranking only",
            "research_result": None,
            "result": headline_ingestion_state.get("latest_capture_result"),
            "exact_reason": headline_ingestion_state.get("failure_class"),
            "canonical_public_url": None,
        })
    recent_activity.sort(
        key=lambda row: str(row.get("completed_at_utc") or row.get("started_at_utc") or ""),
        reverse=True,
    )
    recent_activity = recent_activity[:10]

    active_public_write = browser_state == "PUBLICATION_ACTIVE"
    next_window = future_windows[0] if future_windows else None
    cockpit_current_activity = None
    if active_editorial_item:
        cockpit_current_activity = {
            "work_item_id": active_editorial_id,
            "cycle_started_at_utc": (
                active_activity.get("cycle_started_at_utc")
                or active_editorial_item.get("created_at")
            ),
            "stage_started_at_utc": active_activity.get("stage_started_at_utc"),
            "current_stage": current_stage or "DURABLE_CYCLE_CLAIMED",
            "story_label": (
                active_activity.get("safe_story_label")
                or active_cycle_summary.get("story_label")
            ),
            "candidate_rank": (
                active_activity.get("candidate_rank")
                or active_cycle_summary.get("candidate_rank")
            ),
            "candidate_count": (
                active_activity.get("candidate_count")
                or active_cycle_summary.get("candidate_count")
            ),
            "grounding": (
                active_activity.get("grounding")
                or active_cycle_summary.get("grounding")
            ),
            "destination": active_activity.get("destination"),
            "trigger": active_activity.get("trigger"),
            "instrumentation_state": (
                "EXPLICIT_STAGE_RECORDED" if current_stage else "DURABLE_ACTIVE_LEASE_ONLY"
            ),
        }

    cockpit = {
        "schema_version": "contentops.daily_app_runtime_cockpit.v1",
        "primary_state": cockpit_primary_state,
        "supervisor_state": (
            "STOPPED" if controller_health == "OFFLINE"
            else "STARTING" if cockpit_primary_state == "STARTING"
            else "RUNNING"
        ),
        "controller_health": controller_health,
        "publication_runtime_health": (
            "STOPPED" if controller_health == "OFFLINE"
            else "ACTION_REQUIRED" if unknown
            else "HEALTHY"
        ),
        "operating_mode": controls["operating_mode"],
        "runtime_sha_short": _runtime_sha_short(path),
        "local_timezone": "Asia/Ho_Chi_Minh",
        "current_time_utc": _iso(generated),
        "heartbeat_age_seconds": (
            max(0, int(heartbeat_age)) if heartbeat_age is not None else None
        ),
        "current_activity": cockpit_current_activity,
        "timeline": cockpit_timeline,
        "schedule": {
            "idle_healthy": cockpit_primary_state == "RUNNING_IDLE",
            "next_editorial_wake_utc": next_window.get("window_start_utc") if next_window else None,
            "next_editorial_wake_reason": (
                str(next_window.get("editorial_session") or "SCHEDULED_EDITORIAL_WINDOW")
                if next_window else "NO_EDITORIAL_WINDOW_AVAILABLE"
            ),
            "operator_trigger_pending": pending_trigger,
            "next_x_eligible_capture_utc": headline_ingestion_state.get("next_eligible_capture_utc"),
            "x_cadence_state": headline_ingestion_state.get("cadence_state") or "UNAVAILABLE",
        },
        "last_completed_editorial": last_completed_editorial,
        "intake": {
            **headline_ingestion_state,
            "rolling_24h_unique_headlines": rolling_24h_unique_headlines,
        },
        "safety": {
            "active_public_write": active_public_write,
            "pending_reconciliation_count": len(pending_recovery),
            "pending_readback_recovery_count": len(pending_recovery),
            "unknown_write_count": len(unknown),
            "kill_switch_active": controls["operating_mode"] == "KILL_SWITCH",
            "new_public_writes_blocked": controls["operating_mode"] in {
                "SUPERVISED_OPERATOR_GATE", "SHADOW_ONLY", "KILL_SWITCH",
            },
        },
        "browser": {
            "state": browser_state,
            "external_browser_activity_active": browser_state != "IDLE",
            "last_active_at_utc": browser_automation.get("last_active_browser_interaction_at_utc"),
            "last_reason": browser_automation.get("last_reason"),
            "last_destination": browser_automation.get("last_destination"),
        },
        "recent_activity": recent_activity,
        "projection_authority": {
            "durable_store_authoritative": True,
            "stage_file_presentation_only": True,
            "grants_publication_authority": False,
            "browser_interaction_performed": False,
        },
    }

    snapshot = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "generated_at_utc": _iso(generated),
        "freshness": {
            "state": freshness_state,
            "source_last_updated_at_utc": _iso(source_updated) if source_updated else None,
            "source_age_seconds": round(source_age, 3) if source_age is not None else None,
            "fresh_threshold_seconds": FRESH_SECONDS,
            "provenance": "canonical durable store timestamps",
        },
        "runtime": {
            "app_identity": "Capital Chronicle ContentOps V1 — Daily App",
            "operating_mode": controls["operating_mode"],
            "mode_state_version": controls["state_version"],
            "mode_updated_at_utc": controls["updated_at_utc"],
            "mode_control_source": controls["control_source"],
            "kill_switch_active": controls["operating_mode"] == "KILL_SWITCH",
            "controller_health": controller_health,
            "latest_heartbeat_at_utc": latest_heartbeat.get("last_seen_at") if latest_heartbeat else None,
            "production_epoch_start_utc": production_epoch,
            "operator_cycle_trigger": latest_operator_trigger,
            "active_editorial_cycle_window_id": active_cycle_windows[0] if active_cycle_windows else None,
            "last_tick_state": latest_transition.get("to_state") if latest_transition else "NO_TICK_RECORDED",
            "last_tick_at_utc": latest_transition.get("timestamp_utc") if latest_transition else None,
            "next_wake_utc": future_windows[0]["window_start_utc"] if future_windows else None,
            "next_editorial_window": future_windows[0] if future_windows else None,
            "headline_freshness": "HEADLINE_FRESHNESS_METADATA_UNAVAILABLE",
            "headline_ingestion": headline_ingestion_state,
            "browser_automation": browser_automation,
            "rolling_24h_unique_headlines": rolling_24h_unique_headlines,
            "capital_chronicle_read_model": capital_chronicle_read_model_state,
            "provider_invocation_count": len(invocations),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_metadata": "COST_METADATA_UNAVAILABLE",
            "operator_cockpit": cockpit,
        },
        "today": {
            "published_today_count": published_today_count,
            "published_corpus_count": published_corpus_count,
            "daily_target_band": daily_target_band,
            "latest_editorial_classification": latest_editorial_classification,
            "latest_article_update_mode": latest_article_update_mode,
            "latest_cc_matched_store_count": latest_cc_matched_store_count,
            "latest_prior_related_article_title": latest_prior_related_article_title,
            "latest_prior_related_article_identity": latest_prior_related_article_identity,
            "latest_material_delta_status": latest_material_delta_status,
            "latest_decision_reason": latest_decision_reason,
            "latest_stage_stopped": latest_stage_stopped,
            "current_cycle": ({
                "work_item_id": latest_cycle["work_item_id"],
                "state": latest_cycle["current_state"],
                "state_version": latest_cycle["state_version"],
                "updated_at_utc": latest_cycle["updated_at"],
                "outcome": cycle_outcome,
                "selected_story": None,
                "selected_story_state": "SELECTED_STORY_METADATA_UNAVAILABLE",
                "evidence_status": latest_cycle["current_state"],
                "article_stage": "ARTICLE_STAGE_METADATA_UNAVAILABLE",
                "review_stage": "REVIEW_STAGE_METADATA_UNAVAILABLE",
                "package_stage": "PACKAGE_STAGE_METADATA_UNAVAILABLE",
                "publication_state": cycle_outcome,
            } if latest_cycle else None),
            "pending_lifecycle_recovery_count": len(pending_recovery),
            "immediate_incident_count": len(incidents),
        },
        "queue": {
            "items": sorted(queue_items, key=lambda item: ({"IMMEDIATE": 0, "DUE": 1, "UPCOMING": 2}.get(item["urgency"], 3), item.get("due_at_utc") or "")),
            "upcoming_editorial_windows": future_windows,
            "material_event_wake_state": material_event_wake_state,
            "pending_material_event_count": len(pending_material_events),
            "active_or_held_work_count": sum(1 for row in work_items if row["current_state"] not in {"CLOSED", "REJECTED", "COMPLETE"}),
            "pending_readback_count": len(pending_recovery),
            "due_performance_observation_count": sum(
                1 for row in scheduled_observations
                if _parse_time(row["scheduled_for_utc"]) is not None
                and _parse_time(row["scheduled_for_utc"]) <= generated
            ),
        },
        "published": {
            "objects": publications,
            "real_publication_count": len(real_publications),
            "controlled_no_public_write_count": len(controlled),
            "unknown_write_count": len(unknown),
            "pending_readback_count": len(pending_recovery),
            "empty_reason": "NO_REAL_PUBLICATIONS_YET" if not real_publications else None,
        },
        "performance": {
            "observations": observation_models,
            "collector_capabilities": list(metrics_capability_by_destination.values()),
            "scheduled_observation_count": len(scheduled_observations),
            "collected_observation_count": sum(
                row.get("collection_status") == "COLLECTED" for row in observation_models
            ),
            "real_observation_count": len(observation_models),
            "empty_reason": "NO_REAL_PERFORMANCE_OBSERVATIONS_YET" if not observation_models else None,
            "empty_detail": "No real confirmed public object is eligible for observation." if not observation_models and not real_publications else None,
        },
        "learning": {
            "active_policy": active_policy,
            "policy_history": policy_models,
            "empty_reason": "NO_LEARNING_UPDATE_YET" if not policy_models else None,
            "configured_default": ({
                "policy_version": build_bootstrap_editorial_window_policy().policy_version,
                "provenance": "CONFIGURED_DEFAULT",
                "sample_count": 0,
                "confidence": "BOOTSTRAP_NOT_LEARNED",
                "decision": "HOLD_NO_POLICY_CHANGE",
            } if not policy_models else None),
        },
        "platforms": {"destinations": platform_models},
        "incidents": {
            "items": incidents,
            "active_count": len(incidents),
            "empty_reason": "NO_ACTIVE_INCIDENTS" if not incidents else None,
            "recent_history": durable_incident_history,
            "history_count": len(durable_incident_history),
        },
        "hourly_audit": hourly_audit,
        "controls": {
            "current_mode": controls["operating_mode"],
            "state_version": controls["state_version"],
            "updated_at_utc": controls["updated_at_utc"],
            "control_source": controls["control_source"],
            "allowed_modes": sorted(OPERATING_MODES),
            "write_endpoint": "/api/daily-app/control/mode",
            "run_now_endpoint": RUN_NOW_ENDPOINT,
            "run_now_allowed": controls["operating_mode"] != "KILL_SWITCH",
            "run_now_mode_consequence": RUN_NOW_MODE_CONSEQUENCES[controls["operating_mode"]],
            "shutdown_endpoint": "/api/daily-app/control/shutdown-all-background",
            "shutdown_allowed": not shutdown_blockers,
            "shutdown_blockers": shutdown_blockers,
            "background_logs_endpoint": "/api/daily-app/background-logs",
            "background_log_streams": [
                {"stream": "supervisor_stdout", "label": "Supervisor stdout"},
                {"stream": "supervisor_stderr", "label": "Supervisor stderr"},
                {"stream": "v5_ui", "label": "V5 UI server"},
                {"stream": "launcher", "label": "One-click launcher"},
                {"stream": "operator_shutdown", "label": "Operator shutdown"},
                {"stream": "hourly_audit", "label": "Hourly runtime audit"},
            ],
            "hourly_audit_endpoint": "/api/daily-app/hourly-audit/latest",
            "semantics": {
                "AUTONOMOUS_DEFAULT": "Routine automation; every public write still requires every canonical gate.",
                "SUPERVISED_OPERATOR_GATE": "Pause before new public writes; recovery continues.",
                "SHADOW_ONLY": "Run the workflow with zero public writes.",
                "KILL_SWITCH": "Block new public writes; preserve readback, reconciliation, metrics, and recovery.",
            },
            "unsafe_controls_available": False,
        },
        "authority": {
            "store_schema_version": schema,
            "store_binding": "EXPLICIT_CONFIGURED_CANONICAL_STORE",
            "snapshot_mutates_lifecycle": False,
            "fixture_fallback": False,
            "publishing_registry_version": PUBLISHING_REGISTRY_VERSION,
            "canonical_publishing_profile_id": CANONICAL_PROFILE_ID,
            "canonical_publishing_browser_family": CANONICAL_BROWSER_FAMILY,
            "readiness_eligible_statuses": ["READY_AUTHENTICATED", "READY_NON_BROWSER_BINDING"],
            "readiness_probe_performed": bool(readiness_rows),
            "browser_or_cdp_action_performed": False,
            "provider_or_platform_action_performed": False,
        },
        "audit": {
            "work_item_count": len(work_items),
            "transition_event_count": event_count,
            "artifact_reference_count": artifact_count,
            "review_record_count": review_count,
            "recent_events": transitions[:25],
            "state_counts": dict(Counter(str(row["current_state"]) for row in work_items)),
            "provenance": "ContentOpsDurableStore read-only projection",
        },
    }
    snapshot["observation"] = build_observation_read_model(
        conn=conn,
        runtime_root=runtime_root or path.parent,
        now=generated,
        cockpit_data=cockpit,
        daily_snapshot_data=snapshot,
    )
    _assert_nonsecret(snapshot)
    return snapshot


def update_daily_app_mode(
    store_path: str | Path,
    *,
    expected_state_version: int,
    operating_mode: str,
) -> dict[str, Any]:
    """Perform the FDA-F write class: one canonical CAS mode update."""
    store = ContentOpsDurableStore(Path(store_path), auto_migrate=False)
    if store.get_current_schema_version() != REQUIRED_STORE_SCHEMA_VERSION:
        raise DailyAppReadModelError("mode control requires canonical schema v9")
    try:
        return store.update_operating_control(
            expected_state_version=expected_state_version,
            operating_mode=operating_mode,
            control_source="LOCAL_DAILY_APP_UI",
        )
    except (OperatingModeConflictError, ValueError):
        raise
    except Exception as exc:
        raise DailyAppReadModelError(
            f"canonical operating control update failed:{type(exc).__name__}"
        ) from exc


def _sanitize_operator_trigger(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "trigger_id": row.get("trigger_id"),
        "trigger_kind": row.get("trigger_kind"),
        "requested_at_utc": row.get("requested_at_utc"),
        "requested_mode": row.get("requested_mode"),
        "state": row.get("state"),
        "consumed_at_utc": row.get("consumed_at_utc"),
        "consumed_window_id": row.get("consumed_window_id"),
        "consumption_detail": row.get("consumption_detail"),
        "grants_publication_authority": False,
    }


def request_operator_cycle(
    store_path: str | Path,
    *,
    expected_state_version: int,
) -> dict[str, Any]:
    """Record one durable OPERATOR_REQUESTED cycle trigger through the canonical store.

    This control never executes the newsroom pipeline, never claims publication, and never
    changes operating mode. The persistent supervisor consumes the durable trigger on its normal
    cheap loop and runs it through the exact same canonical gates as a scheduled window.
    """
    from uuid import uuid4

    from live_contentops.ingestion_bootstrap_v1 import passive_canonical_ingestion_readiness

    store = ContentOpsDurableStore(Path(store_path), auto_migrate=False)
    if store.get_current_schema_version() != REQUIRED_STORE_SCHEMA_VERSION:
        raise DailyAppReadModelError("run-now control requires canonical schema v9")
    control = store.get_operating_control()
    if int(control["state_version"]) != int(expected_state_version):
        raise OperatingModeConflictError(
            f"run_now_control_state_conflict:expected={int(expected_state_version)}"
            f":actual={int(control['state_version'])}"
        )
    mode = str(control["operating_mode"])
    if mode == "KILL_SWITCH":
        return {
            "status": "KILL_SWITCH_ACTIVE_PUBLIC_WRITES_BLOCKED",
            "governed_cycle_requested": False,
            "operating_mode": mode,
            "publication_claimed": False,
            "note": RUN_NOW_MODE_CONSEQUENCES["KILL_SWITCH"],
        }
    pending = store.fetch_pending_operator_trigger()
    if pending is not None:
        return {
            "status": "OPERATOR_TRIGGER_ALREADY_PENDING",
            "governed_cycle_requested": True,
            "operating_mode": mode,
            "publication_claimed": False,
            "trigger": _sanitize_operator_trigger(pending),
        }
    if store.active_editorial_cycle_window_ids():
        return {
            "status": "CYCLE_ALREADY_ACTIVE",
            "governed_cycle_requested": False,
            "operating_mode": mode,
            "publication_claimed": False,
            "note": "A canonical editorial cycle is executing; no parallel cycle is started.",
        }
    # Run Now is editorial-window authority only. Its control path is passive and cannot launch,
    # attach, navigate, reload, or capture X. The supervisor's normal due-cadence intake seam may
    # refresh later; the cycle can still consume the durable rolling headline universe.
    readiness = passive_canonical_ingestion_readiness()
    chrome_state = str(readiness.get("chrome_9222_ingestion") or "UNAVAILABLE")
    trigger_id = "operator-trigger-" + uuid4().hex[:24]
    try:
        record = store.record_operator_cycle_trigger(
            trigger_id=trigger_id,
            trigger_kind="OPERATOR_REQUESTED",
            requested_mode=mode,
            control_state_version=int(control["state_version"]),
        )
    except OperatorTriggerAlreadyPendingError:
        existing = store.fetch_pending_operator_trigger()
        return {
            "status": "OPERATOR_TRIGGER_ALREADY_PENDING",
            "governed_cycle_requested": True,
            "operating_mode": mode,
            "publication_claimed": False,
            "trigger": _sanitize_operator_trigger(existing) if existing else None,
        }
    return {
        "status": "OPERATOR_TRIGGER_ACCEPTED",
        "governed_cycle_requested": True,
        "operating_mode": mode,
        "publication_claimed": False,
        "ingestion_state_at_request": chrome_state,
        "ingestion_browser_interaction_performed": False,
        "note": (
            "One governed editorial cycle was requested. It bypasses only the wait for the "
            "scheduled window; every evidence/review/readiness/publication gate remains "
            "unchanged. This response does not claim any publication."
        ),
        "trigger": _sanitize_operator_trigger(record),
    }
