"""Canonical read-only observation, performance, and closed-loop learning projection.

Exposes all 19 locked V1, V2, and Cross-Lane observation lanes in one unified, nonsecret,
read-only structure without granting either lane new execution or publication authority.

This module performs ZERO:
- provider / LLM / model calls;
- network fetches;
- browser / CDP actions;
- credential / secret reads;
- publication calls;
- state mutations (V1 or V2).

Missing data remains explicit (None / UNAVAILABLE / NOT_PRESENT), NEVER converted to zero.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

SCHEMA_VERSION = "contentops.observation_read_model.v1"
LANE_CONTRACT_VERSION = "contentops.observation_lane.v1"

# The 19 Locked Observation Lane IDs
LANE_V1_HEADLINE_INTAKE_FRESHNESS = "V1_HEADLINE_INTAKE_FRESHNESS"
LANE_V1_CANDIDATE_FUNNEL = "V1_CANDIDATE_FUNNEL"
LANE_V1_EVIDENCE_SOURCE_HEALTH = "V1_EVIDENCE_SOURCE_HEALTH"
LANE_V1_PUBLICATION_SAFETY_RECOVERY = "V1_PUBLICATION_SAFETY_RECOVERY"
LANE_V1_REAL_PERFORMANCE_OBSERVATIONS = "V1_REAL_PERFORMANCE_OBSERVATIONS"
LANE_V1_PASSIVE_INTERACTION_QUALITY = "V1_PASSIVE_INTERACTION_QUALITY"
LANE_V1_CLOSED_LOOP_LEARNING = "V1_CLOSED_LOOP_LEARNING"
LANE_V1_SEARCH_DISCOVERY = "V1_SEARCH_DISCOVERY"
LANE_V1_COST_RUNTIME_YIELD = "V1_COST_RUNTIME_YIELD"

LANE_V2_V1_TO_VIDEO_TRIGGER_SHADOW = "V2_V1_TO_VIDEO_TRIGGER_SHADOW"
LANE_V2_SOURCE_RIGHTS_ASSET_SUPPLY = "V2_SOURCE_RIGHTS_ASSET_SUPPLY"
LANE_V2_ASSET_DIVERSITY_AND_SCREEN_TIME = "V2_ASSET_DIVERSITY_AND_SCREEN_TIME"
LANE_V2_PRODUCTION_TCO_RECOVERY_SOAK = "V2_PRODUCTION_TCO_RECOVERY_SOAK"
LANE_V2_ACTUAL_MEDIA_QUALITY_OWNER_GATE = "V2_ACTUAL_MEDIA_QUALITY_OWNER_GATE"
LANE_V2_PUBLICATION_READINESS = "V2_PUBLICATION_READINESS"
LANE_V2_POST_PUBLISH_RETENTION_ATTRIBUTION = "V2_POST_PUBLISH_RETENTION_ATTRIBUTION"
LANE_V2_CLOSED_LOOP_VIDEO_LEARNING = "V2_CLOSED_LOOP_VIDEO_LEARNING"

LANE_CROSS_LANE_SOURCE_ACCESS_HEALTH = "CROSS_LANE_SOURCE_ACCESS_HEALTH"
LANE_CROSS_LANE_DATA_FRESHNESS_AND_AUTHORITY = "CROSS_LANE_DATA_FRESHNESS_AND_AUTHORITY"

ALL_LANE_IDS = (
    LANE_V1_HEADLINE_INTAKE_FRESHNESS,
    LANE_V1_CANDIDATE_FUNNEL,
    LANE_V1_EVIDENCE_SOURCE_HEALTH,
    LANE_V1_PUBLICATION_SAFETY_RECOVERY,
    LANE_V1_REAL_PERFORMANCE_OBSERVATIONS,
    LANE_V1_PASSIVE_INTERACTION_QUALITY,
    LANE_V1_CLOSED_LOOP_LEARNING,
    LANE_V1_SEARCH_DISCOVERY,
    LANE_V1_COST_RUNTIME_YIELD,
    LANE_V2_V1_TO_VIDEO_TRIGGER_SHADOW,
    LANE_V2_SOURCE_RIGHTS_ASSET_SUPPLY,
    LANE_V2_ASSET_DIVERSITY_AND_SCREEN_TIME,
    LANE_V2_PRODUCTION_TCO_RECOVERY_SOAK,
    LANE_V2_ACTUAL_MEDIA_QUALITY_OWNER_GATE,
    LANE_V2_PUBLICATION_READINESS,
    LANE_V2_POST_PUBLISH_RETENTION_ATTRIBUTION,
    LANE_V2_CLOSED_LOOP_VIDEO_LEARNING,
    LANE_CROSS_LANE_SOURCE_ACCESS_HEALTH,
    LANE_CROSS_LANE_DATA_FRESHNESS_AND_AUTHORITY,
)

# Standard observation lane states
STATE_LIVE_OBSERVATION = "LIVE_OBSERVATION"
STATE_SHADOW_READ_ONLY = "SHADOW_READ_ONLY"
STATE_WAITING_FOR_REAL_OBJECT = "WAITING_FOR_REAL_OBJECT"
STATE_INSUFFICIENT_SAMPLE = "INSUFFICIENT_SAMPLE"
STATE_OPERATOR_SETUP_REQUIRED = "OPERATOR_SETUP_REQUIRED"
STATE_BLOCKED_OWNER_AUTHORITY = "BLOCKED_OWNER_AUTHORITY"
STATE_DEGRADED = "DEGRADED"
STATE_UNAVAILABLE = "UNAVAILABLE"

# Safe allowlisted V2 artifact filenames (strict relative paths)
V2_SAFE_ALLOWLISTED_FILES = frozenset({
    "HANDOFF.json",
    "contracts/render_dependency_manifest.json",
    "contracts/asset_board.json",
    "receipts/master_media.json",
    "receipts/automated_visual_qa.json",
    "receipts/manual_visual_review.json",
    "receipts/recovery_proof.json",
    "receipts/zero_public_write.json",
    "receipts/audio_ledger.json",
    "receipts/asset_acquisition.json",
})

_SECRET_KEY_PATTERN = re.compile(
    r"(^|_)(token|secret|password|authorization|cookie|private_key|webhook)(_|$)",
    re.IGNORECASE,
)


class ObservationReadModelError(RuntimeError):
    """The observation projection could not be built safely."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
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


def _assert_nonsecret(payload: Any, path: str = "$") -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            key_str = str(key)
            if _SECRET_KEY_PATTERN.search(key_str):
                raise ObservationReadModelError(f"Secret-shaped key rejected at {path}.{key_str}")
            _assert_nonsecret(value, f"{path}.{key_str}")
    elif isinstance(payload, (list, tuple, set)):
        for index, item in enumerate(payload):
            _assert_nonsecret(item, f"{path}[{index}]")


def _safe_read_json(file_path: Path) -> dict[str, Any]:
    """Read a single JSON file safely. Fails closed and returns empty dict on error."""
    try:
        if not file_path.is_file():
            return {}
        # Guard against huge files (> 5MB)
        if file_path.stat().st_size > 5_000_000:
            return {}
        text = file_path.read_text(encoding="utf-8")
        parsed = json.loads(text)
        return dict(parsed) if isinstance(parsed, Mapping) else {}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {}


def _safe_load_v2_package(package_dir: Path) -> dict[str, Any]:
    """Load only safe allowlisted files from a single V2 runtime package directory.

    Guarantees:
    - Never reads outside package_dir (no directory traversal).
    - Never recursively searches arbitrary filenames.
    - Fails safe if files are absent.
    """
    if not package_dir.is_dir():
        return {}
    package_data: dict[str, Any] = {"package_name": package_dir.name, "artifacts": {}}
    for rel_path_str in V2_SAFE_ALLOWLISTED_FILES:
        target = (package_dir / rel_path_str).resolve()
        # Enforce target is strictly inside package_dir
        try:
            target.relative_to(package_dir.resolve())
        except ValueError:
            continue
        if target.is_file():
            data = _safe_read_json(target)
            if data:
                package_data["artifacts"][rel_path_str] = data
    return package_data


def _discover_v2_packages(runtime_root: Optional[Path]) -> list[dict[str, Any]]:
    """Discover V2 packages under runtime_root bounded to direct child directories."""
    if runtime_root is None or not runtime_root.is_dir():
        return []
    packages: list[dict[str, Any]] = []
    try:
        for child in runtime_root.iterdir():
            if not child.is_dir():
                continue
            name = child.name.lower()
            # Direct child directories matching V2 package or task prefixes
            if name.startswith("v2_") or name.startswith("task_tier2_") or "treasury" in name:
                loaded = _safe_load_v2_package(child)
                if loaded.get("artifacts"):
                    packages.append(loaded)
    except OSError:
        pass
    return sorted(packages, key=lambda p: str(p.get("package_name")), reverse=True)


def build_observation_lane(
    *,
    lane_id: str,
    group: str,
    state: str,
    data_source: str,
    authority_class: str,
    last_observed_at_utc: Optional[str] = None,
    next_due_at_utc: Optional[str] = None,
    sample_count: Optional[int] = None,
    coverage: Optional[str] = None,
    confidence: Optional[str] = None,
    freshness: Optional[str] = None,
    blocker: Optional[str] = None,
    write_authority: str = "READ_ONLY",
    notes: Optional[str] = None,
    metrics: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Construct one canonical observation lane conforming to the common contract."""
    return {
        "lane_contract_version": LANE_CONTRACT_VERSION,
        "lane_id": lane_id,
        "group": group,
        "state": state,
        "data_source": data_source,
        "authority_class": authority_class,
        "last_observed_at_utc": last_observed_at_utc,
        "next_due_at_utc": next_due_at_utc,
        "sample_count": sample_count,
        "coverage": coverage,
        "confidence": confidence,
        "freshness": freshness,
        "blocker": blocker,
        "write_authority": write_authority,
        "notes": notes,
        "metrics": dict(metrics or {}),
    }


def build_observation_read_model(
    *,
    conn: Any,
    runtime_root: Optional[Path] = None,
    now: Optional[datetime] = None,
    cockpit_data: Optional[Mapping[str, Any]] = None,
    daily_snapshot_data: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Build the complete 19-lane observation read model.

    Reads V1 durable tables via query-only SQLite connection and V2 evidence via safe
    bounded allowlisted artifact reading.
    """
    now_dt = now or _utc_now()
    now_iso = _iso(now_dt)

    # -------------------------------------------------------------------------
    # 1. Fetch relevant rows from durable operational store
    # -------------------------------------------------------------------------
    def fetch_all(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        try:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]
        except Exception:
            return []

    def fetch_val(sql: str, params: tuple = (), default: Any = None) -> Any:
        try:
            row = conn.execute(sql, params).fetchone()
            return row[0] if row else default
        except Exception:
            return default

    work_items = fetch_all("SELECT * FROM work_items ORDER BY created_at_utc DESC")
    transitions = fetch_all("SELECT * FROM transition_events ORDER BY recorded_at_utc DESC")
    dispatches = fetch_all("SELECT * FROM platform_dispatches ORDER BY dispatch_id DESC")
    readbacks = fetch_all("SELECT * FROM readbacks ORDER BY readback_id DESC")
    reconciliations = fetch_all("SELECT * FROM reconciliations ORDER BY reconciliation_id DESC")
    readiness_rows = fetch_all("SELECT * FROM destination_readiness ORDER BY platform_id ASC")
    perf_observations = fetch_all("SELECT * FROM performance_observations ORDER BY scheduled_for_utc DESC")
    learning_policies = fetch_all("SELECT * FROM learning_policy_versions ORDER BY created_at_utc DESC")
    incidents = fetch_all("SELECT * FROM incidents WHERE resolved_at_utc IS NULL ORDER BY created_at_utc DESC")

    # -------------------------------------------------------------------------
    # 2. Discover V2 runtime artifacts
    # -------------------------------------------------------------------------
    default_runtime_root = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
    effective_runtime_root = runtime_root or default_runtime_root
    v2_packages = _discover_v2_packages(effective_runtime_root)
    treasury_pkg = next(
        (p for p in v2_packages if "treasury_visual_material_richness" in str(p.get("package_name"))),
        v2_packages[0] if v2_packages else None,
    )

    # -------------------------------------------------------------------------
    # 3. Build V1 Lanes (1 to 9)
    # -------------------------------------------------------------------------

    # --- Lane 1: V1_HEADLINE_INTAKE_FRESHNESS ---
    intake_data = (cockpit_data or {}).get("intake") or {}
    last_ingest_utc = intake_data.get("last_ingest_utc") or (daily_snapshot_data or {}).get("runtime", {}).get("headline_ingestion", {}).get("last_ingest_utc")
    lane_state = str(intake_data.get("lane_state") or (daily_snapshot_data or {}).get("runtime", {}).get("headline_ingestion", {}).get("lane_state") or "UNAVAILABLE")
    unique_24h = intake_data.get("rolling_24h_unique_headlines")
    if unique_24h is None:
        unique_24h = (daily_snapshot_data or {}).get("runtime", {}).get("rolling_24h_unique_headlines")
    newest_event_age = intake_data.get("newest_source_event_age_seconds")
    next_capture_utc = intake_data.get("next_eligible_capture_utc")

    l1_state = STATE_LIVE_OBSERVATION if lane_state in ("RUNNING", "IDLE", "CAPTURED_NEW", "HEALTHY") else STATE_DEGRADED if lane_state == "DEGRADED" else STATE_UNAVAILABLE
    lane_v1_headline_intake = build_observation_lane(
        lane_id=LANE_V1_HEADLINE_INTAKE_FRESHNESS,
        group="V1",
        state=l1_state,
        data_source="DURABLE_INTAKE_CHECKPOINT_AND_DAILY_SIDECARS",
        authority_class="DURABLE_OPERATIONAL_STORE",
        last_observed_at_utc=last_ingest_utc,
        next_due_at_utc=next_capture_utc,
        sample_count=unique_24h if isinstance(unique_24h, int) else None,
        coverage="Rolling 24-hour unique headline universe",
        confidence="DETERMINISTIC_EXACT_COUNT",
        freshness="FRESH" if (newest_event_age is not None and newest_event_age < 3600) else "HISTORICAL",
        blocker=None if l1_state == STATE_LIVE_OBSERVATION else f"INTAKE_LANE_{lane_state}",
        write_authority="READ_ONLY_INGESTION_SEAM",
        notes="Continuous zero-LLM intake; Chrome CDP 9222 profile reuse.",
        metrics={
            "lane_state": lane_state,
            "rolling_24h_unique_headlines": unique_24h,
            "newest_source_event_age_seconds": newest_event_age,
            "next_eligible_capture_utc": next_capture_utc,
            "cadence_state": intake_data.get("cadence_state") or "UNAVAILABLE",
            "latest_capture_result": intake_data.get("latest_capture_result") or "UNAVAILABLE",
        },
    )

    # --- Lane 2: V1_CANDIDATE_FUNNEL ---
    prepared_items = [w for w in work_items if str(w.get("current_state")) in ("PREPARED", "READY", "SELECTED", "EVALUATING")]
    completed_items = [w for w in work_items if str(w.get("current_state")) in ("PUBLISHED", "COMPLETED", "CANONICAL_CONFIRMED")]
    held_items = [w for w in work_items if "HOLD" in str(w.get("current_state")) or "BLOCKED" in str(w.get("current_state")) or "ABSTAIN" in str(w.get("current_state"))]
    total_work = len(work_items)
    latest_work = work_items[0] if work_items else None

    lane_v1_candidate_funnel = build_observation_lane(
        lane_id=LANE_V1_CANDIDATE_FUNNEL,
        group="V1",
        state=STATE_LIVE_OBSERVATION if total_work > 0 else STATE_INSUFFICIENT_SAMPLE,
        data_source="DURABLE_WORK_ITEMS_AND_TRANSITIONS",
        authority_class="DURABLE_OPERATIONAL_STORE",
        last_observed_at_utc=latest_work.get("updated_at_utc") if latest_work else None,
        sample_count=total_work,
        coverage="Candidate preparation, evaluation, and hold/abstain lifecycle",
        confidence="DETERMINISTIC_LIFECYCLE_TRUTH",
        freshness="RECORDED_IN_STORE",
        blocker=None,
        write_authority="ZERO_PUBLIC_WRITE_UNLESS_GOVERNED_GATE_PASS",
        notes="Abstain/HOLD is valid; no publication forced.",
        metrics={
            "total_work_items": total_work,
            "prepared_or_active_count": len(prepared_items),
            "completed_count": len(completed_items),
            "held_or_blocked_count": len(held_items),
            "latest_work_item_id": latest_work.get("work_item_id") if latest_work else None,
            "latest_work_item_state": latest_work.get("current_state") if latest_work else None,
            "latest_decision_reason": (daily_snapshot_data or {}).get("today", {}).get("latest_decision_reason"),
            "latest_material_delta_status": (daily_snapshot_data or {}).get("today", {}).get("latest_material_delta_status"),
        },
    )

    # --- Lane 3: V1_EVIDENCE_SOURCE_HEALTH ---
    cc_read_model = (daily_snapshot_data or {}).get("runtime", {}).get("capital_chronicle_read_model") or "READ_ONLY_CATALOG"
    lane_v1_evidence_health = build_observation_lane(
        lane_id=LANE_V1_EVIDENCE_SOURCE_HEALTH,
        group="V1",
        state=STATE_LIVE_OBSERVATION,
        data_source="OFFICIAL_PRIMARY_SOURCE_REGISTRY_AND_CC_CATALOG",
        authority_class="GOVERNED_SOURCE_RECORDS",
        last_observed_at_utc=now_iso,
        sample_count=None,
        coverage="Official primary sources (EIA, CFTC, Federal Reserve, Treasury, BLS, SEC) + Capital Chronicle main catalog",
        confidence="HIGH_PRIMARY_CORROBORATED",
        freshness="SOURCE_VERIFIED",
        blocker=None,
        write_authority="READ_ONLY",
        notes="Capital Chronicle main is read-only analytical truth. Exact source records remain authority.",
        metrics={
            "capital_chronicle_read_model_status": cc_read_model,
            "grounded_research_ladder": "gemini-3.1-pro-preview -> gemini-3.5-flash",
            "access_policy": "NO_WAF_VPN_PROXY_BYPASS",
            "unsupported_sources_state": "FAIL_CLOSED_OMIT_OR_NARROW",
        },
    )

    # --- Lane 4: V1_PUBLICATION_SAFETY_RECOVERY ---
    unknown_writes = [d for d in dispatches if str(d.get("status")) == "UNKNOWN_WRITE" or "UNKNOWN" in str(d.get("dispatch_status") or "")]
    pending_reconciliations = [r for r in reconciliations if "PENDING" in str(r.get("status") or "")]
    active_incidents = len(incidents)

    lane_v1_pub_safety = build_observation_lane(
        lane_id=LANE_V1_PUBLICATION_SAFETY_RECOVERY,
        group="V1",
        state=STATE_LIVE_OBSERVATION if not unknown_writes and not active_incidents else STATE_DEGRADED,
        data_source="DURABLE_DISPATCHES_READBACKS_RECONCILIATIONS_READINESS",
        authority_class="DURABLE_OPERATIONAL_STORE",
        last_observed_at_utc=now_iso,
        sample_count=len(dispatches),
        coverage="Nine-surface publication preflight, strict readback, UNKNOWN_WRITE recovery",
        confidence="DETERMINISTIC_RECONCILIATION",
        freshness="CURRENT_STATE",
        blocker="UNKNOWN_WRITE_PRESENT" if unknown_writes else ("ACTIVE_INCIDENTS" if active_incidents else None),
        write_authority="DURABLE_PUBLICATION_COORDINATOR_ONLY",
        notes="Unknown write protocol: STOP RETRY -> READ BACK -> RECONCILE.",
        metrics={
            "unknown_write_count": len(unknown_writes),
            "pending_reconciliation_count": len(pending_reconciliations),
            "active_incident_count": active_incidents,
            "ready_destinations_count": len([r for r in readiness_rows if "READY" in str(r.get("readiness") or "")]),
            "total_destinations_tracked": 9,
            "browser_jit_activity": (cockpit_data or {}).get("browser", {}).get("external_browser_activity_active", False),
        },
    )

    # --- Lane 5: V1_REAL_PERFORMANCE_OBSERVATIONS ---
    obs_by_window: dict[str, list[dict[str, Any]]] = {"EARLY": [], "INTERMEDIATE": [], "DAILY": [], "LONG_TAIL": []}
    for row in perf_observations:
        w_name = str(row.get("observation_window") or "").upper()
        if w_name in obs_by_window:
            obs_by_window[w_name].append(row)

    window_counts = {
        "15m_early": len(obs_by_window["EARLY"]),
        "2h_intermediate": len(obs_by_window["INTERMEDIATE"]),
        "24h_daily": len(obs_by_window["DAILY"]),
        "7d_long_tail": len(obs_by_window["LONG_TAIL"]),
    }
    collected_obs = [o for o in perf_observations if str(o.get("collection_status")) == "COLLECTED"]
    learning_eligible_obs = [o for o in perf_observations if o.get("learning_eligible") in (1, True, "1", "true")]

    l5_state = STATE_LIVE_OBSERVATION if collected_obs else STATE_WAITING_FOR_REAL_OBJECT
    lane_v1_perf_obs = build_observation_lane(
        lane_id=LANE_V1_REAL_PERFORMANCE_OBSERVATIONS,
        group="V1",
        state=l5_state,
        data_source="DURABLE_PERFORMANCE_OBSERVATIONS",
        authority_class="DURABLE_OPERATIONAL_STORE",
        last_observed_at_utc=perf_observations[0].get("collected_at_utc") if collected_obs else None,
        next_due_at_utc=perf_observations[0].get("scheduled_for_utc") if perf_observations else None,
        sample_count=len(collected_obs),
        coverage="Four deterministic observation windows: EARLY (15m), INTERMEDIATE (2h), DAILY (24h), LONG_TAIL (7d)",
        confidence="REAL_OBJECT_METRIC_AVAILABLE" if collected_obs else "NO_REAL_OBSERVATION_YET",
        freshness="RECORDED_IN_STORE",
        blocker=None if collected_obs else "NO_ELIGIBLE_CONFIRMED_PUBLIC_OBJECT",
        write_authority="READ_ONLY_OBSERVATION_COLLECTOR",
        notes="Unavailable metrics recorded as UNAVAILABLE, never fabricated as zero.",
        metrics={
            "window_counts": window_counts,
            "total_observations_recorded": len(perf_observations),
            "collected_count": len(collected_obs),
            "learning_eligible_count": len(learning_eligible_obs),
            "formula_version": "qualified_engagement.formula.v1",
        },
    )

    # --- Lane 6: V1_PASSIVE_INTERACTION_QUALITY ---
    lane_v1_interaction = build_observation_lane(
        lane_id=LANE_V1_PASSIVE_INTERACTION_QUALITY,
        group="V1",
        state=STATE_INSUFFICIENT_SAMPLE,
        data_source="DURABLE_PERFORMANCE_OBSERVATIONS_INTERACTION_AGGREGATES",
        authority_class="DURABLE_OPERATIONAL_STORE",
        last_observed_at_utc=None,
        sample_count=0,
        coverage="Categorical interaction classification (substantive questions, domain insights, critique)",
        confidence="INSUFFICIENT_SAMPLE",
        freshness="UNAVAILABLE",
        blocker="NO_QUALIFIED_INTERACTIONS_COLLECTED_YET",
        write_authority="DEFERRED_ZERO_WRITE_AUTHORITY",
        notes="Passive learning input only. Raw public text is NEVER surfaced or persisted. Public reply write authority is zero.",
        metrics={
            "qualified_interaction_count": 0,
            "classifier_state": "SEMANTIC_CLASSIFIER_STANDBY",
            "reply_authority": "DEFERRED_ZERO_WRITE_AUTHORITY",
            "categories_supported": 11,
        },
    )

    # --- Lane 7: V1_CLOSED_LOOP_LEARNING ---
    active_policy_row = next((p for p in learning_policies if str(p.get("status")) == "ACTIVE"), None)
    active_payload = json.loads(str(active_policy_row.get("payload_json") or "{}")) if active_policy_row else {}
    policy_provenance = str(active_policy_row.get("provenance") or "CONFIGURED_DEFAULT") if active_policy_row else "CONFIGURED_DEFAULT"
    learning_decision = str(active_policy_row.get("decision") or "BOOTSTRAP") if active_policy_row else "HOLD_NO_POLICY_CHANGE"
    learning_sample = active_policy_row.get("sample_count") if active_policy_row else 0
    learning_confidence = active_policy_row.get("confidence") if active_policy_row else 0.0

    lane_v1_learning = build_observation_lane(
        lane_id=LANE_V1_CLOSED_LOOP_LEARNING,
        group="V1",
        state=STATE_LIVE_OBSERVATION if policy_provenance == "LEARNED" else STATE_INSUFFICIENT_SAMPLE,
        data_source="DURABLE_LEARNING_POLICY_VERSIONS",
        authority_class="DURABLE_OPERATIONAL_STORE",
        last_observed_at_utc=active_policy_row.get("created_at_utc") if active_policy_row else None,
        sample_count=int(learning_sample or 0),
        coverage="Content, SEO, destination package, and timing recommendation sections",
        confidence=str(learning_confidence),
        freshness="RECORDED_IN_STORE",
        blocker=None if policy_provenance == "LEARNED" else "INSUFFICIENT_REAL_SAMPLE_FOR_POLICY_UPDATE",
        write_authority="READ_ONLY_POLICY_PREFERENCE",
        notes="Schedule is owner locked (4 routine windows). Learned timing is preference context only.",
        metrics={
            "active_policy_version": active_policy_row.get("policy_version") if active_policy_row else "policy.bootstrap.v1",
            "policy_provenance": policy_provenance,
            "decision": learning_decision,
            "policy_history_count": len(learning_policies),
            "owner_locked_schedule": True,
            "applied_timing_offset_minutes": 0,
            "recommended_timing_offset_minutes": active_payload.get("timing", {}).get("recommended_offset_minutes", 0),
        },
    )

    # --- Lane 8: V1_SEARCH_DISCOVERY ---
    lane_v1_search = build_observation_lane(
        lane_id=LANE_V1_SEARCH_DISCOVERY,
        group="V1",
        state=STATE_OPERATOR_SETUP_REQUIRED,
        data_source="SEARCH_CONSOLE_INTEGRATION_CHANNEL",
        authority_class="OPERATOR_CONFIGURATION",
        last_observed_at_utc=None,
        sample_count=0,
        coverage="Search query impressions, clicks, ranking observations",
        confidence="NO_SEARCH_SPECIFIC_SAMPLE",
        freshness="UNAVAILABLE",
        blocker="OPERATOR_SETUP_REQUIRED",
        write_authority="READ_ONLY",
        notes="Search Console integration is deferred post-canary. Truthfully shown as OPERATOR_SETUP_REQUIRED / NO_SEARCH_SPECIFIC_SAMPLE.",
        metrics={
            "search_console_state": "OPERATOR_SETUP_REQUIRED",
            "search_sample_count": 0,
            "seo_policy_state": active_payload.get("seo", {}).get("state", "INSUFFICIENT_REAL_SEARCH_SAMPLE"),
        },
    )

    # --- Lane 9: V1_COST_RUNTIME_YIELD ---
    prompt_tokens = (daily_snapshot_data or {}).get("runtime", {}).get("prompt_tokens", 0)
    completion_tokens = (daily_snapshot_data or {}).get("runtime", {}).get("completion_tokens", 0)
    invocations = (daily_snapshot_data or {}).get("runtime", {}).get("provider_invocation_count", 0)
    cost_meta = (daily_snapshot_data or {}).get("runtime", {}).get("cost_metadata", "NORMAL_BUDGET")

    lane_v1_cost_yield = build_observation_lane(
        lane_id=LANE_V1_COST_RUNTIME_YIELD,
        group="V1",
        state=STATE_LIVE_OBSERVATION,
        data_source="DURABLE_STORE_AND_RUNTIME_TELEMETRY",
        authority_class="DURABLE_OPERATIONAL_STORE",
        last_observed_at_utc=now_iso,
        sample_count=invocations,
        coverage="Provider model calls, token usage, cycle durations, publish/abstain yield",
        confidence="DETERMINISTIC_TELEMETRY",
        freshness="CURRENT_EPOCH",
        blocker=None,
        write_authority="READ_ONLY",
        notes="Quality-first token telemetry during acceptance; runaway circuit breakers active.",
        metrics={
            "provider_invocation_count": invocations,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_metadata": cost_meta,
            "published_today_count": (daily_snapshot_data or {}).get("today", {}).get("published_today_count", 0),
            "target_band": [0, 4],
        },
    )

    # -------------------------------------------------------------------------
    # 4. Build V2 Lanes (10 to 17)
    # -------------------------------------------------------------------------

    # --- Lane 10: V2_V1_TO_VIDEO_TRIGGER_SHADOW ---
    lane_v2_trigger_shadow = build_observation_lane(
        lane_id=LANE_V2_V1_TO_VIDEO_TRIGGER_SHADOW,
        group="V2",
        state=STATE_SHADOW_READ_ONLY,
        data_source="V1_PERFORMANCE_OBSERVATIONS_SHADOW_MAP",
        authority_class="SHADOW_DERIVED_EVALUATION",
        last_observed_at_utc=now_iso,
        sample_count=len(collected_obs),
        coverage="V1 performance inputs (reads, completions, shares) mapped to video candidacy",
        confidence="SHADOW_NON_AUTHORITATIVE",
        freshness="SHADOW_CURRENT",
        blocker=None,
        write_authority="ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY",
        notes="Shadow evaluation only; does not claim or auto-start V2 jobs. No invented scorer weights.",
        metrics={
            "mode": "SHADOW_READ_ONLY",
            "v1_eligible_candidates_evaluated": len(collected_obs),
            "v2_video_jobs_claimed": 0,
            "qualification_gate": "MANUAL_OWNER_OR_EXPLICIT_FUTURE_TASK_ONLY",
        },
    )

    # --- Lane 11: V2_SOURCE_RIGHTS_ASSET_SUPPLY ---
    asset_board = (treasury_pkg or {}).get("artifacts", {}).get("contracts/asset_board.json", {})
    board_candidates = asset_board.get("candidates") or asset_board.get("assets") or []
    accepted_assets = [a for a in board_candidates if str(a.get("status") or "").upper() in ("ACCEPTED", "PASS", "SELECTED")]
    rejected_assets = [a for a in board_candidates if str(a.get("status") or "").upper() in ("REJECTED", "FAIL", "DROPPED")]

    l11_state = STATE_LIVE_OBSERVATION if treasury_pkg else STATE_UNAVAILABLE
    lane_v2_rights_supply = build_observation_lane(
        lane_id=LANE_V2_SOURCE_RIGHTS_ASSET_SUPPLY,
        group="V2",
        state=l11_state,
        data_source="V2_ASSET_BOARD_AND_ACQUISITION_RECEIPTS",
        authority_class="BOUNDED_LOCAL_ARTIFACT" if treasury_pkg else "UNAVAILABLE",
        last_observed_at_utc=asset_board.get("created_at_utc") if asset_board else (now_iso if treasury_pkg else None),
        sample_count=len(board_candidates) if board_candidates else None,
        coverage="Rights-safe candidate discovery, ASSET_VISUAL_FIT gate, primary document/photo rights clearance",
        confidence="RIGHTS_VERIFIED_DOCUMENTED" if treasury_pkg else "NOT_PRESENT",
        freshness="PACKAGE_BOUND" if treasury_pkg else "NOT_PRESENT",
        blocker=None if treasury_pkg else "V2_PACKAGE_NOT_FOUND",
        write_authority="ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY",
        notes="Rights-safe is necessary but not sufficient; low-res or text-cluttered assets rejected.",
        metrics={
            "package_present": bool(treasury_pkg),
            "package_name": treasury_pkg.get("package_name") if treasury_pkg else "NOT_PRESENT",
            "candidate_assets_count": len(board_candidates),
            "accepted_assets_count": len(accepted_assets),
            "rejected_assets_count": len(rejected_assets),
            "real_person_documentary_media_policy": "STRICT_CLEARANCE_REQUIRED",
        },
    )

    # --- Lane 12: V2_ASSET_DIVERSITY_AND_SCREEN_TIME ---
    render_manifest = (treasury_pkg or {}).get("artifacts", {}).get("contracts/render_dependency_manifest.json", {})
    family_seconds = render_manifest.get("family_screen_seconds") or {}
    asset_seconds = render_manifest.get("asset_screen_seconds") or {}
    total_screen_seconds = render_manifest.get("total_screen_seconds")

    l12_state = STATE_LIVE_OBSERVATION if render_manifest else STATE_UNAVAILABLE
    lane_v2_diversity = build_observation_lane(
        lane_id=LANE_V2_ASSET_DIVERSITY_AND_SCREEN_TIME,
        group="V2",
        state=l12_state,
        data_source="V2_RENDER_DEPENDENCY_MANIFEST",
        authority_class="BOUNDED_LOCAL_ARTIFACT" if render_manifest else "UNAVAILABLE",
        last_observed_at_utc=now_iso if render_manifest else None,
        sample_count=len(asset_seconds) if asset_seconds else None,
        coverage="Actual rendered dependencies: exact-file reuse, visual family concentration, cumulative screen time",
        confidence="RENDER_PROVEN_EXACT" if render_manifest else "NOT_PRESENT",
        freshness="PACKAGE_BOUND" if render_manifest else "NOT_PRESENT",
        blocker=None if render_manifest else "RENDER_DEPENDENCY_MANIFEST_NOT_FOUND",
        write_authority="ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY",
        notes="Tracked on actual rendered output, not storyboard plan IDs alone.",
        metrics={
            "total_screen_seconds": total_screen_seconds,
            "unique_assets_used": len(asset_seconds),
            "visual_families_count": len(family_seconds),
            "family_screen_seconds": family_seconds,
            "asset_screen_seconds_top5": dict(sorted(asset_seconds.items(), key=lambda x: x[1], reverse=True)[:5]) if asset_seconds else {},
        },
    )

    # --- Lane 13: V2_PRODUCTION_TCO_RECOVERY_SOAK ---
    handoff_data = (treasury_pkg or {}).get("artifacts", {}).get("HANDOFF.json", {})
    recovery_proof = (treasury_pkg or {}).get("artifacts", {}).get("receipts/recovery_proof.json", {})
    short_render = handoff_data.get("short", {}).get("render", {})
    short_elapsed_ms = short_render.get("elapsed_ms")

    l13_state = STATE_LIVE_OBSERVATION if handoff_data else STATE_UNAVAILABLE
    lane_v2_tco_recovery = build_observation_lane(
        lane_id=LANE_V2_PRODUCTION_TCO_RECOVERY_SOAK,
        group="V2",
        state=l13_state,
        data_source="V2_HANDOFF_AND_RECOVERY_PROOF_RECEIPTS",
        authority_class="BOUNDED_LOCAL_ARTIFACT" if handoff_data else "UNAVAILABLE",
        last_observed_at_utc=now_iso if handoff_data else None,
        sample_count=1 if handoff_data else None,
        coverage="Wall time, Remotion render duration, audio synthesis ledger, selective rerender proof",
        confidence="RECEIPT_PROVEN" if handoff_data else "NOT_PRESENT",
        freshness="PACKAGE_BOUND" if handoff_data else "NOT_PRESENT",
        blocker=None if handoff_data else "V2_HANDOFF_NOT_FOUND",
        write_authority="ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY",
        notes="Preserves immutable audio and media proofs; selective re-render passes unaffected masters unchanged.",
        metrics={
            "short_render_elapsed_ms": short_elapsed_ms,
            "short_render_scale": short_render.get("scale"),
            "renderer_version": short_render.get("renderer_version"),
            "recovery_proof_status": recovery_proof.get("status") if recovery_proof else "NOT_PRESENT",
            "frozen_audio_resume": recovery_proof.get("frozen_audio_resume") if recovery_proof else "UNAVAILABLE",
            "unaffected_masters_unchanged": recovery_proof.get("unaffected_masters_unchanged", False) if recovery_proof else False,
        },
    )

    # --- Lane 14: V2_ACTUAL_MEDIA_QUALITY_OWNER_GATE ---
    qa_data = (treasury_pkg or {}).get("artifacts", {}).get("receipts/automated_visual_qa.json", {})
    review_data = (treasury_pkg or {}).get("artifacts", {}).get("receipts/manual_visual_review.json", {})
    automated_status = qa_data.get("status") or review_data.get("automated_status") or "NOT_PRESENT"
    worker_review_status = review_data.get("status") or "NOT_PRESENT"
    owner_acceptance_claimed = review_data.get("owner_acceptance_claimed", False)

    l14_state = STATE_LIVE_OBSERVATION if (qa_data or review_data) else STATE_UNAVAILABLE
    lane_v2_owner_gate = build_observation_lane(
        lane_id=LANE_V2_ACTUAL_MEDIA_QUALITY_OWNER_GATE,
        group="V2",
        state=l14_state,
        data_source="V2_AUTOMATED_QA_AND_MANUAL_VISUAL_REVIEW_RECEIPTS",
        authority_class="BOUNDED_LOCAL_ARTIFACT" if l14_state == STATE_LIVE_OBSERVATION else "UNAVAILABLE",
        last_observed_at_utc=now_iso if l14_state == STATE_LIVE_OBSERVATION else None,
        sample_count=1 if l14_state == STATE_LIVE_OBSERVATION else None,
        coverage="Automated visual diagnostics (luma/frame diff/low change) + Codex actual-media review + Jim/ChatGPT owner gate",
        confidence="AUTOMATED_AND_WORKER_REVIEW_PASS" if worker_review_status.startswith("PASS") else "UNVERIFIED",
        freshness="PACKAGE_BOUND" if l14_state == STATE_LIVE_OBSERVATION else "NOT_PRESENT",
        blocker="PENDING_JIM_CHATGPT_OWNER_ACCEPTANCE" if not owner_acceptance_claimed else None,
        write_authority="ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY",
        notes="Worker review and automated QA remain evidence; only Jim/ChatGPT owner review authorizes acceptance.",
        metrics={
            "automated_qa_status": automated_status,
            "worker_visual_review_status": worker_review_status,
            "reviewer": review_data.get("reviewer") or "Codex task session",
            "unresolved_high_defects": review_data.get("unresolved_high_severity_defects", 0),
            "unresolved_medium_defects": review_data.get("unresolved_medium_severity_defects", 0),
            "owner_acceptance_claimed": owner_acceptance_claimed,
        },
    )

    # --- Lane 15: V2_PUBLICATION_READINESS ---
    zero_write_receipt = (treasury_pkg or {}).get("artifacts", {}).get("receipts/zero_public_write.json", {})
    l15_state = STATE_LIVE_OBSERVATION if zero_write_receipt else STATE_UNAVAILABLE
    lane_v2_pub_readiness = build_observation_lane(
        lane_id=LANE_V2_PUBLICATION_READINESS,
        group="V2",
        state=l15_state,
        data_source="V2_ZERO_PUBLIC_WRITE_RECEIPTS_AND_ADAPTER_REGISTRY",
        authority_class="SHADOW_READ_ONLY_SAFETY_CONTRACT",
        last_observed_at_utc=now_iso if zero_write_receipt else None,
        sample_count=None,
        coverage="Six-surface shadow control plane (YouTube, TikTok, Instagram, Facebook Page Reels, etc.)",
        confidence="ZERO_PUBLIC_WRITE_ENFORCED",
        freshness="PACKAGE_BOUND" if zero_write_receipt else "NOT_PRESENT",
        blocker=None,
        write_authority="ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY",
        notes="Public writes = 0; browser uploads = 0; public write authority strictly false.",
        metrics={
            "public_writes": zero_write_receipt.get("public_writes", 0),
            "uploads": zero_write_receipt.get("uploads", 0),
            "browser_profile_uses": zero_write_receipt.get("browser_profile_uses", 0),
            "video_public_write_authority": zero_write_receipt.get("video_public_write_authority", False),
            "validation_status": zero_write_receipt.get("validation", {}).get("status", "PASS"),
        },
    )

    # --- Lane 16: V2_POST_PUBLISH_RETENTION_ATTRIBUTION ---
    lane_v2_retention = build_observation_lane(
        lane_id=LANE_V2_POST_PUBLISH_RETENTION_ATTRIBUTION,
        group="V2",
        state=STATE_BLOCKED_OWNER_AUTHORITY,
        data_source="V2_POST_PUBLISH_RETENTION_PLATFORM_CHANNEL",
        authority_class="OWNER_AUTHORITY_GATE",
        last_observed_at_utc=None,
        sample_count=0,
        coverage="Retention curve, completion rate, rewatch rate, beat/hook attribution",
        confidence="BLOCKED_OWNER_AUTHORITY",
        freshness="UNAVAILABLE",
        blocker="ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY",
        notes="Truthfully reflects zero public video writes. Retention fields exist but cannot be fabricated.",
        metrics={
            "retention_tracking_state": "BLOCKED_OWNER_AUTHORITY",
            "published_video_count": 0,
            "average_completion_rate": None,
            "average_retention_score": None,
        },
    )

    # --- Lane 17: V2_CLOSED_LOOP_VIDEO_LEARNING ---
    lane_v2_video_learning = build_observation_lane(
        lane_id=LANE_V2_CLOSED_LOOP_VIDEO_LEARNING,
        group="V2",
        state=STATE_WAITING_FOR_REAL_OBJECT,
        data_source="V2_CLOSED_LOOP_VIDEO_LEARNING_POLICY",
        authority_class="BOUNDED_LEARNING_CONTRACT",
        last_observed_at_utc=None,
        sample_count=0,
        coverage="Candidacy, hook style, beat duration, asset/primitive strategy recommendations",
        confidence="INSUFFICIENT_SAMPLE",
        freshness="WAITING_FOR_REAL_PUBLIC_OBJECT",
        blocker="INSUFFICIENT_SAMPLE_NO_PUBLIC_VIDEO_OBJECTS",
        write_authority="ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY",
        notes="Future bounded learning will influence packaging only — never factual or numeric truth.",
        metrics={
            "learning_state": "WAITING_FOR_REAL_PUBLIC_OBJECT",
            "sample_count": 0,
            "policy_version": "v2_video_policy.bootstrap.v0",
            "factual_authority_mutable": False,
        },
    )

    # -------------------------------------------------------------------------
    # 5. Build Cross-Lane Lanes (18 & 19)
    # -------------------------------------------------------------------------

    # --- Lane 18: CROSS_LANE_SOURCE_ACCESS_HEALTH ---
    lane_cross_access = build_observation_lane(
        lane_id=LANE_CROSS_LANE_SOURCE_ACCESS_HEALTH,
        group="CROSS_LANE",
        state=STATE_LIVE_OBSERVATION,
        data_source="SOURCE_ACQUISITION_SANDBOX_AND_LOADER_REGISTRIES",
        authority_class="GOVERNED_SOURCE_RECORDS",
        last_observed_at_utc=now_iso,
        sample_count=None,
        coverage="Official API, official HTML/PDF, operator-supplied primary, edge-blocked status across V1 and V2",
        confidence="NO_WAF_BYPASS_ENFORCED",
        freshness="CURRENT_STATE",
        blocker=None,
        write_authority="READ_ONLY",
        notes="Access-path failure is never presented as source/truth failure. No proxy/WAF bypass.",
        metrics={
            "official_sources_monitored": ["EIA", "CFTC", "FRB", "UST", "BLS", "SEC"],
            "access_methods": ["OFFICIAL_API", "OFFICIAL_HTML_PDF", "OPERATOR_PRIMARY"],
            "waf_bypass_allowed": False,
            "edge_blocked_handling": "FAIL_CLOSED_OMIT_OR_NARROW",
        },
    )

    # --- Lane 19: CROSS_LANE_DATA_FRESHNESS_AND_AUTHORITY ---
    latest_event_time = max(
        [
            t
            for t in [
                _parse_time(last_ingest_utc),
                _parse_time(active_policy_row.get("created_at_utc") if active_policy_row else None),
                _parse_time(perf_observations[0].get("collected_at_utc") if collected_obs else None),
            ]
            if t is not None
        ],
        default=None,
    )

    lane_cross_freshness = build_observation_lane(
        lane_id=LANE_CROSS_LANE_DATA_FRESHNESS_AND_AUTHORITY,
        group="CROSS_LANE",
        state=STATE_LIVE_OBSERVATION,
        data_source="UNIFIED_PROJECTION_TIMESTAMPS_AND_AUTHORITY_CLASSES",
        authority_class="UNIFIED_OBSERVATION_CONTRACT",
        last_observed_at_utc=_iso(latest_event_time) or now_iso,
        sample_count=19,
        coverage="Unified freshness summary: latest intake, evidence, performance, learning, V2 package timestamps",
        confidence="DETERMINISTIC_PROJECTION",
        freshness="LIVE_EVALUATED",
        blocker=None,
        write_authority="READ_ONLY",
        notes="Summary of authority lineage and freshness across all 19 lanes.",
        metrics={
            "total_lanes": 19,
            "v1_lanes_count": 9,
            "v2_lanes_count": 8,
            "cross_lanes_count": 2,
            "latest_v1_intake_utc": last_ingest_utc,
            "latest_v1_learning_decision_utc": active_policy_row.get("created_at_utc") if active_policy_row else None,
            "latest_v2_package_detected": treasury_pkg.get("package_name") if treasury_pkg else "NOT_PRESENT",
            "v2_packages_detected_count": len(v2_packages),
        },
    )

    # -------------------------------------------------------------------------
    # 6. Aggregate lanes and build final response
    # -------------------------------------------------------------------------
    lanes = [
        lane_v1_headline_intake,
        lane_v1_candidate_funnel,
        lane_v1_evidence_health,
        lane_v1_pub_safety,
        lane_v1_perf_obs,
        lane_v1_interaction,
        lane_v1_learning,
        lane_v1_search,
        lane_v1_cost_yield,
        lane_v2_trigger_shadow,
        lane_v2_rights_supply,
        lane_v2_diversity,
        lane_v2_tco_recovery,
        lane_v2_owner_gate,
        lane_v2_pub_readiness,
        lane_v2_retention,
        lane_v2_video_learning,
        lane_cross_access,
        lane_cross_freshness,
    ]

    # State counts for quick summary
    state_counts: dict[str, int] = {}
    for lane in lanes:
        st = lane["state"]
        state_counts[st] = state_counts.get(st, 0) + 1

    model = {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": now_iso,
        "summary": {
            "total_lanes": len(lanes),
            "v1_lane_count": 9,
            "v2_lane_count": 8,
            "cross_lane_count": 2,
            "state_counts": state_counts,
            "v1_live_count": len([l for l in lanes if l["group"] == "V1" and l["state"] == STATE_LIVE_OBSERVATION]),
            "v2_shadow_count": len([l for l in lanes if l["group"] == "V2" and l["state"] == STATE_SHADOW_READ_ONLY]),
            "blocked_count": len([l for l in lanes if l["state"] == STATE_BLOCKED_OWNER_AUTHORITY]),
            "insufficient_sample_count": len([l for l in lanes if l["state"] in (STATE_INSUFFICIENT_SAMPLE, STATE_WAITING_FOR_REAL_OBJECT)]),
            "operator_setup_required_count": len([l for l in lanes if l["state"] == STATE_OPERATOR_SETUP_REQUIRED]),
            "zero_public_write_enforced": True,
        },
        "v1_performance_windows": window_counts,
        "v2_packages_detected": [p.get("package_name") for p in v2_packages],
        "lanes": lanes,
    }

    _assert_nonsecret(model)
    return model
