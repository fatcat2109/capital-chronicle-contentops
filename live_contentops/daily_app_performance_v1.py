"""Final Daily App V1 — real performance observation + bounded closed-loop learning.

This module is the single governed FDA-D/FDA-E production path. It is NOT a second
analytics platform, scheduler, state store, or learning architecture: it reads canonical
durable publication lineage from ``ContentOpsDurableStore``, persists observations and
immutable policy versions into the SAME store (schema v6), and is driven from the cheap
tick of ``ContentOpsDailyAppSupervisor``.

Hard boundaries enforced here:

* Only REAL canonical external publication objects may enter automatic learning
  (status DISPATCH_CONFIRMED + non-null ``public_object_id`` + exact readback +
  ``RECONCILED_CONFIRMED``). Controlled no-write, UNKNOWN_WRITE, pending reconciliation,
  missing identity, and synthetic/test objects are ``learning_eligible = false``.
* UNAVAILABLE != ZERO. Missing metrics record an explicit availability status and are
  excluded from scoring; they are never fabricated as zero.
* Observations are idempotent by exact deterministic identity; a conflicting re-collection
  fails closed and never overwrites historical numbers.
* Learning decisions are deterministic, bounded, small-sample-guarded, and produce an
  immutable, parent-retained policy version. Rollback adds a NEW version; history is never
  rewritten. Learning can never touch evidence/source/numeric/publication/kill-switch gates.
* Metrics collection performs ZERO LLM calls.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Mapping, Optional

SCHEMA_VERSION = "contentops.daily_app_performance.v1"
OBSERVATION_SCHEMA_VERSION = "contentops.performance_observation.v1"

#: Versioned qualified-engagement formula. Every derived score carries this version so a future
#: formula change is explicit and never silently rewrites history.
QUALIFIED_ENGAGEMENT_FORMULA_VERSION = "qualified_engagement.formula.v1"

COLLECTOR_CAPABILITY_VERSION = "contentops.performance_collector.v1"

# Observation windows (offset from the dispatch/publish instant). Platforms that do not expose
# useful metrics at a given window record UNAVAILABLE/NOT_EXPOSED rather than being skipped.
OBSERVATION_WINDOWS: Dict[str, int] = {
    "EARLY": 15 * 60,
    "INTERMEDIATE": 2 * 60 * 60,
    "DAILY": 24 * 60 * 60,
    "LONG_TAIL": 7 * 24 * 60 * 60,
}

# --- Learning guards (deterministic; aligned with AdaptiveLearningConfig protections) -----
MIN_ELIGIBLE_OBSERVATIONS = 5          # small-N hold below this
CONFIDENCE_SAMPLE_DENOMINATOR = 8      # confidence = eligible_collected / denominator (capped 1.0)
CONFIDENCE_THRESHOLD = 0.6             # low-confidence hold below this
SCORE_CAP = 10.0                       # per-observation cap so one outlier cannot dominate
MAX_TIMING_OFFSET_MINUTES = 60         # absolute bound on a learned timing offset
MAX_DELTA_PER_UPDATE_MINUTES = 15      # maximum bounded movement per learning update
DETERIORATION_MARGIN = 0.20            # rollback when qualified engagement falls >20% below baseline
IMPROVEMENT_MARGIN = 0.10              # accept bounded improvement only when >10% above baseline
TIMING_BASELINE_QUALIFIED = 1.0        # bootstrap baseline for qualified engagement

BOOTSTRAP_POLICY_VERSION = "policy.bootstrap.v1"
BOOTSTRAP_PROVENANCE = "CONFIGURED_DEFAULT"

DECISION_HOLD = "HOLD_NO_POLICY_CHANGE"
DECISION_ACCEPT = "ACCEPT_BOUNDED_UPDATE"
DECISION_ROLLBACK = "ROLLBACK"

POLICY_STATUS_ACTIVE = "ACTIVE"
POLICY_STATUS_SUPERSEDED = "SUPERSEDED"

#: Canonical dispatch/reconciliation values (durable truth) reused verbatim from the supervisor.
DISPATCH_CONFIRMED = "DISPATCH_CONFIRMED"
STATUS_UNKNOWN_WRITE = "UNKNOWN_WRITE"
STATUS_CONTROLLED_NO_WRITE = "CONTROLLED_NO_PUBLIC_WRITE"
RECONCILE_CONFIRMED = "RECONCILED_CONFIRMED"

#: Qualified-engagement signal weights (platform-native first; only AVAILABLE metrics are used).
QUALIFIED_SIGNAL_WEIGHTS: Dict[str, float] = {
    "shares": 1.0,
    "reposts": 1.0,
    "saves": 1.0,
    "bookmarks": 1.0,
    "substantive_replies": 0.8,
    "comments": 0.8,
    "canonical_article_clicks": 1.2,
    "subscriber_conversions": 2.0,
    "meaningful_reads": 0.6,
    "completion_rate": 0.5,
}

AVAILABLE = "AVAILABLE"
UNAVAILABLE = "UNAVAILABLE"
UNSUPPORTED = "UNSUPPORTED"
AUTH_REQUIRED = "AUTH_REQUIRED"
NOT_EXPOSED = "NOT_EXPOSED"


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


# =========================================================================
# Learning-eligibility gate
# =========================================================================


def assess_learning_eligibility(
    *,
    dispatch_status: str,
    public_object_id: Optional[str],
    reconciliation_status: Optional[str],
    readback_count: int,
) -> Dict[str, Any]:
    """Return ``{"learning_eligible": bool, "reasons": [str, ...]}``.

    Only a REAL canonical external publication object is eligible. Every condition is an
    AND; a single failure marks the object ineligible for automatic learning.
    """
    reasons: List[str] = []
    if dispatch_status != DISPATCH_CONFIRMED:
        reasons.append(f"dispatch_status_not_confirmed:{dispatch_status}")
    if dispatch_status == STATUS_CONTROLLED_NO_WRITE:
        reasons.append("controlled_no_public_write_excluded")
    if dispatch_status == STATUS_UNKNOWN_WRITE:
        reasons.append("unknown_write_excluded")
    if not public_object_id:
        reasons.append("missing_public_object_id")
    if reconciliation_status != RECONCILE_CONFIRMED:
        reasons.append(f"reconciliation_not_confirmed:{reconciliation_status}")
    if readback_count < 1:
        reasons.append("no_successful_readback")
    return {"learning_eligible": not reasons, "reasons": sorted(reasons)}


# =========================================================================
# Deterministic observation identity + scheduling
# =========================================================================


def observation_identity(
    *,
    dispatch_id: str,
    public_object_id: str,
    platform: str,
    observation_window: str,
    collector_capability_version: str = COLLECTOR_CAPABILITY_VERSION,
) -> str:
    """Deterministic identity for one exact observation.

    Identity derives from ``dispatch_id + exact public_object_id + platform +
    observation_window + collector capability version``. Repeated collection of the same
    identity is idempotent; it never duplicates or overwrites.
    """
    material = {
        "dispatch_id": dispatch_id,
        "public_object_id": public_object_id,
        "platform": platform,
        "observation_window": observation_window,
        "collector_capability_version": collector_capability_version,
    }
    return "obs_" + _logical_hash(material)[:32]


def observation_hash(observation: Mapping[str, Any]) -> str:
    """Content hash binding the observation to its exact lineage + metrics payload."""
    material = {key: observation.get(key) for key in (
        "observation_id", "schema_version", "dispatch_id", "work_item_id", "platform",
        "public_object_id", "public_object_url_hash", "observation_window",
        "scheduled_for_utc", "collector_capability_version", "collection_status",
        "metrics_native_json", "metric_availability_json", "source_identity",
    )}
    return _logical_hash(material)


def build_scheduled_observations(
    *,
    dispatch: Mapping[str, Any],
    work_item_id: str,
    dispatched_at: datetime,
    learning_eligible: bool,
) -> List[Dict[str, Any]]:
    """Return the set of SCHEDULED observation rows for one confirmed dispatch.

    No network or LLM calls. Windows are offsets from the dispatch instant; platforms that
    cannot expose metrics at a window will record UNAVAILABLE at collection time.
    """
    dispatch_id = str(dispatch["dispatch_id"])
    public_object_id = str(dispatch["public_object_id"])
    platform = str(dispatch["platform"])
    public_object_url_hash = dispatch.get("public_object_url_hash")
    rows: List[Dict[str, Any]] = []
    for window_name, offset_seconds in OBSERVATION_WINDOWS.items():
        scheduled_for = dispatched_at + _seconds_delta(offset_seconds)
        obs_id = observation_identity(
            dispatch_id=dispatch_id,
            public_object_id=public_object_id,
            platform=platform,
            observation_window=window_name,
        )
        observation = {
            "observation_id": obs_id,
            "schema_version": OBSERVATION_SCHEMA_VERSION,
            "dispatch_id": dispatch_id,
            "work_item_id": work_item_id,
            "platform": platform,
            "public_object_id": public_object_id,
            "public_object_url_hash": public_object_url_hash,
            "observation_window": window_name,
            "scheduled_for_utc": _iso_utc(scheduled_for),
            "collected_at_utc": None,
            "collector_capability_version": COLLECTOR_CAPABILITY_VERSION,
            "collection_status": "SCHEDULED",
            "metrics_native_json": json.dumps({}, sort_keys=True),
            "metric_availability_json": json.dumps({}, sort_keys=True),
            "source_identity": "contentops.daily_app_performance.v1",
            "learning_eligible": 1 if learning_eligible else 0,
        }
        observation["observation_hash"] = observation_hash(observation)
        rows.append(observation)
    return rows


def _seconds_delta(seconds: int):
    from datetime import timedelta
    return timedelta(seconds=seconds)


# =========================================================================
# Read-only collection (no LLM, no writes)
# =========================================================================


def collect_observation(
    store: Any,
    *,
    observation_id: str,
    collector: Optional[Callable[[str, str, str], Mapping[str, Any]]],
    now: datetime,
) -> Dict[str, Any]:
    """Run one bounded READ-ONLY collection for a scheduled observation and persist it.

    ``collector(dispatch_id, public_object_id, observation_window)`` must return a mapping with
    ``metrics`` (native values) and ``availability`` (metric -> AVAILABLE/UNAVAILABLE/
    UNSUPPORTED/AUTH_REQUIRED/NOT_EXPOSED). Unavailable metrics are NEVER coerced to zero.
    A missing/raising collector records capability-unavailable rather than fabricating data.
    """
    observation = store.get_performance_observation(observation_id)
    if observation is None:
        raise ValueError(f"performance_observation_not_found:{observation_id}")
    if observation["collection_status"] != "SCHEDULED":
        # Already collected; idempotent no-op (never overwrite historical numbers).
        return observation
    if not callable(collector):
        metrics: Dict[str, Any] = {}
        availability: Dict[str, str] = {}
        collection_status = "COLLECTOR_UNAVAILABLE"
    else:
        try:
            result = dict(collector(
                observation["dispatch_id"],
                observation["public_object_id"],
                observation["observation_window"],
            ))
            metrics = dict(result.get("metrics") or {})
            availability = dict(result.get("availability") or {})
            collection_status = str(result.get("status") or "COLLECTED")
        except Exception as exc:  # noqa: BLE001 - read-only collection must fail closed
            metrics = {}
            availability = {}
            collection_status = "COLLECTION_ERROR"
            _ = exc
    return store.mark_performance_observation_collected(
        observation_id=observation_id,
        collection_status=collection_status,
        collected_at_utc=_iso_utc(now),
        metrics_native_json=json.dumps(metrics, sort_keys=True),
        metric_availability_json=json.dumps(availability, sort_keys=True),
    )


# =========================================================================
# Qualified-engagement scoring (versioned; UNAVAILABLE excluded, never zero-filled)
# =========================================================================


def qualified_engagement_score(
    metrics_native: Mapping[str, Any],
    metric_availability: Mapping[str, str],
) -> Optional[float]:
    """Compute the versioned qualified-engagement score for one observation.

    Only metrics whose availability is exactly ``AVAILABLE`` contribute. Unavailable metrics are
    excluded (NOT zero-filled). Returns ``None`` when no qualified signal is available, which the
    caller treats as "no score" rather than a zero. Vanity impressions alone never count.
    """
    raw_score = 0.0
    any_available = False
    for metric, weight in QUALIFIED_SIGNAL_WEIGHTS.items():
        if metric_availability.get(metric) != AVAILABLE:
            continue
        if metric not in metrics_native:
            continue
        value = metrics_native[metric]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        any_available = True
        raw_score += float(weight) * float(value)
    if not any_available:
        return None
    score = raw_score
    # Negative-quality / clickbait penalties (only when those signals are available).
    completion = metrics_native.get("completion_rate")
    if metric_availability.get("completion_rate") == AVAILABLE and isinstance(completion, (int, float)) \
            and not isinstance(completion, bool) and float(completion) < 0.2:
        score -= 0.5
    impressions_available = metric_availability.get("impressions") == AVAILABLE
    qualified_actions = sum(
        float(metrics_native.get(m, 0) or 0)
        for m in ("shares", "reposts", "saves", "bookmarks", "substantive_replies",
                  "canonical_article_clicks", "subscriber_conversions")
        if metric_availability.get(m) == AVAILABLE and isinstance(metrics_native.get(m), (int, float))
        and not isinstance(metrics_native.get(m), bool)
    )
    if impressions_available and qualified_actions == 0:
        score -= 0.5  # high impressions with no meaningful action
    return max(0.0, min(score, SCORE_CAP))


# =========================================================================
# Learning evaluation + immutable policy versions + rollback
# =========================================================================


def _timing_offset_minutes(policy_row: Mapping[str, Any]) -> int:
    try:
        payload = json.loads(policy_row["policy_payload_json"])
        return int(payload.get("timing", {}).get("offset_minutes", 0))
    except Exception:  # noqa: BLE001 - fail closed to zero offset on malformed payload
        return 0


def _baseline_qualified(policy_row: Mapping[str, Any]) -> Optional[float]:
    try:
        payload = json.loads(policy_row["policy_payload_json"])
        baseline = payload.get("baseline_qualified_engagement")
        return float(baseline) if baseline is not None else None
    except Exception:  # noqa: BLE001
        return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _new_policy_version(parent_version: str, decision: str, payload: Mapping[str, Any], created_at: str) -> str:
    material = {
        "parent_policy_version": parent_version,
        "decision": decision,
        "policy_payload": payload,
        "created_at_utc": created_at,
        "formula_version": QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
    }
    return "policy_" + _logical_hash(material)[:24]


def evaluate_learning_decision(
    store: Any,
    *,
    evaluation_window: str,
    now: datetime,
) -> Dict[str, Any]:
    """Evaluate the durable eligible observations and produce an immutable learning decision.

    Never mutates evidence/source/numeric/publication/kill-switch gates. Either returns a
    ``HOLD_NO_POLICY_CHANGE`` decision or registers a NEW immutable policy version (bounded
    update or rollback), superseding the previous ACTIVE policy without deleting history.
    """
    current = store.get_active_learning_policy()
    observations = store.list_performance_observations()
    eligible = [
        o for o in observations
        if int(o["learning_eligible"]) == 1 and o["collection_status"] == "COLLECTED"
    ]
    # Learning sample = distinct REAL published objects (not per-window observations), so one
    # post can never dominate and the guard matches "do not overfit to 1 post".
    total_eligible = len({o["dispatch_id"] for o in eligible})
    total_observations = len(eligible)
    scored: List[float] = []
    for obs in eligible:
        try:
            metrics = json.loads(obs["metrics_native_json"])
            availability = json.loads(obs["metric_availability_json"])
        except Exception:  # noqa: BLE001 - malformed payload yields no score
            continue
        score = qualified_engagement_score(metrics, availability)
        if score is not None:
            scored.append(min(score, SCORE_CAP))

    observation_ids = [obs["observation_id"] for obs in eligible]
    common = {
        "evaluation_window": evaluation_window,
        "observation_ids": observation_ids,
        "sample_count": total_eligible,
        "formula_version": QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
    }

    # Guard 1: small-N hold (distinct real publications).
    if total_eligible < MIN_ELIGIBLE_OBSERVATIONS:
        return _decision_record(store, decision=DECISION_HOLD, reason="small_sample_hold",
                                confidence=0.0, mean_qualified=None, current=current,
                                common=common, now=now, scored_count=len(scored))

    # Confidence blends sample size with data availability (unavailable data lowers confidence).
    scored_fraction = (len(scored) / total_observations) if total_observations else 0.0
    confidence = min(1.0, total_eligible / CONFIDENCE_SAMPLE_DENOMINATOR) * scored_fraction
    # Guard 2: low-confidence hold.
    if confidence < CONFIDENCE_THRESHOLD:
        return _decision_record(store, decision=DECISION_HOLD, reason="low_confidence_hold",
                                confidence=confidence, mean_qualified=None, current=current,
                                common=common, now=now, scored_count=len(scored))

    mean_qualified = (sum(scored) / len(scored)) if scored else 0.0
    current_offset = _timing_offset_minutes(current) if current else 0
    baseline = _baseline_qualified(current) if current else None
    created_at = _iso_utc(now)

    if baseline is None:
        # First accepted learning update: bounded change + establish baseline.
        new_offset = int(_clamp(current_offset + MAX_DELTA_PER_UPDATE_MINUTES,
                                -MAX_TIMING_OFFSET_MINUTES, MAX_TIMING_OFFSET_MINUTES))
        return _accept_update(store, current=current, reason="first_bounded_update",
                              confidence=confidence, mean_qualified=mean_qualified,
                              new_offset=new_offset, common=common, created_at=created_at,
                              now=now)

    if mean_qualified < baseline * (1.0 - DETERIORATION_MARGIN):
        # Deterioration: ROLLBACK creates a NEW version pointing at the prior known-good values.
        return _rollback(store, current=current, reason="qualified_engagement_deterioration",
                         confidence=confidence, mean_qualified=mean_qualified,
                         common=common, created_at=created_at, now=now)

    if mean_qualified > baseline * (1.0 + IMPROVEMENT_MARGIN):
        new_offset = int(_clamp(current_offset + MAX_DELTA_PER_UPDATE_MINUTES,
                                -MAX_TIMING_OFFSET_MINUTES, MAX_TIMING_OFFSET_MINUTES))
        return _accept_update(store, current=current, reason="bounded_improvement",
                              confidence=confidence, mean_qualified=mean_qualified,
                              new_offset=new_offset, common=common, created_at=created_at,
                              now=now)

    return _decision_record(store, decision=DECISION_HOLD, reason="no_significant_change",
                            confidence=confidence, mean_qualified=mean_qualified,
                            current=current, common=common, now=now, scored_count=len(scored))


def _accept_update(store, *, current, reason, confidence, mean_qualified, new_offset, common, created_at, now):
    parent_version = current["policy_version"] if current else BOOTSTRAP_POLICY_VERSION
    current_offset = _timing_offset_minutes(current) if current else 0
    payload = {
        "timing": {"offset_minutes": new_offset},
        "baseline_qualified_engagement": mean_qualified,
        "content": {},
        "seo": {},
        "package": {},
        "provenance": "LEARNED_BOUNDED_UPDATE",
    }
    bounded_delta = {
        "timing_offset_minutes_before": current_offset,
        "timing_offset_minutes_after": new_offset,
        "max_delta_per_update_minutes": MAX_DELTA_PER_UPDATE_MINUTES,
    }
    accepted_changes = {"timing.offset_minutes": new_offset}
    policy_version = _new_policy_version(parent_version, DECISION_ACCEPT, payload, created_at)
    record = _policy_record(
        policy_version=policy_version, parent_policy_version=parent_version,
        created_at=created_at, status=POLICY_STATUS_ACTIVE, decision=DECISION_ACCEPT,
        sample_count=common["sample_count"], confidence=confidence,
        formula_version=common["formula_version"], observation_ids=common["observation_ids"],
        evaluation_window=common["evaluation_window"], accepted_changes=accepted_changes,
        bounded_delta=bounded_delta, rollback_reference=None, decision_reason=reason,
        payload=payload,
    )
    stored = store.register_learning_policy(policy=record)
    if current is not None:
        store.set_learning_policy_status(policy_version=parent_version, status=POLICY_STATUS_SUPERSEDED)
    return {
        "decision": DECISION_ACCEPT, "policy_version": policy_version,
        "parent_policy_version": parent_version, "confidence": confidence,
        "mean_qualified_engagement": mean_qualified, "sample_count": common["sample_count"],
        "bounded_delta": bounded_delta, "reason": reason, "stored": stored is not None,
    }


def _rollback(store, *, current, reason, confidence, mean_qualified, common, created_at, now):
    current_version = current["policy_version"] if current else BOOTSTRAP_POLICY_VERSION
    # Rollback targets the parent of the current policy (the prior known-good values).
    parent_of_current = current["parent_policy_version"] if current else None
    rollback_offset = 0
    if parent_of_current:
        parent_row = store.get_learning_policy(parent_of_current)
        if parent_row:
            rollback_offset = _timing_offset_minutes(parent_row)
    payload = {
        "timing": {"offset_minutes": rollback_offset},
        "baseline_qualified_engagement": mean_qualified,
        "content": {},
        "seo": {},
        "package": {},
        "provenance": "LEARNED_ROLLBACK",
    }
    bounded_delta = {
        "timing_offset_minutes_before": _timing_offset_minutes(current) if current else 0,
        "timing_offset_minutes_after": rollback_offset,
        "max_delta_per_update_minutes": MAX_DELTA_PER_UPDATE_MINUTES,
    }
    policy_version = _new_policy_version(current_version, DECISION_ROLLBACK, payload, created_at)
    record = _policy_record(
        policy_version=policy_version, parent_policy_version=current_version,
        created_at=created_at, status=POLICY_STATUS_ACTIVE, decision=DECISION_ROLLBACK,
        sample_count=common["sample_count"], confidence=confidence,
        formula_version=common["formula_version"], observation_ids=common["observation_ids"],
        evaluation_window=common["evaluation_window"], accepted_changes={"timing.offset_minutes": rollback_offset},
        bounded_delta=bounded_delta, rollback_reference=current_version, decision_reason=reason,
        payload=payload,
    )
    stored = store.register_learning_policy(policy=record)
    if current is not None:
        store.set_learning_policy_status(policy_version=current_version, status=POLICY_STATUS_SUPERSEDED)
    return {
        "decision": DECISION_ROLLBACK, "policy_version": policy_version,
        "parent_policy_version": current_version, "confidence": confidence,
        "mean_qualified_engagement": mean_qualified, "sample_count": common["sample_count"],
        "bounded_delta": bounded_delta, "reason": reason, "stored": stored is not None,
    }


def _decision_record(store, *, decision, reason, confidence, mean_qualified, current, common, now, scored_count):
    return {
        "decision": decision, "policy_version": None,
        "parent_policy_version": current["policy_version"] if current else None,
        "confidence": confidence, "mean_qualified_engagement": mean_qualified,
        "sample_count": common["sample_count"], "scored_count": scored_count,
        "reason": reason, "stored": False,
    }


def _policy_record(*, policy_version, parent_policy_version, created_at, status, decision,
                   sample_count, confidence, formula_version, observation_ids, evaluation_window,
                   accepted_changes, bounded_delta, rollback_reference, decision_reason, payload):
    payload_json = json.dumps(payload, sort_keys=True)
    return {
        "policy_version": policy_version,
        "parent_policy_version": parent_policy_version,
        "created_at_utc": created_at,
        "status": status,
        "decision": decision,
        "sample_count": sample_count,
        "confidence": confidence,
        "formula_version": formula_version,
        "observation_ids_json": json.dumps(sorted(observation_ids), sort_keys=True),
        "evaluation_window": evaluation_window,
        "accepted_changes_json": json.dumps(accepted_changes, sort_keys=True),
        "bounded_delta_json": json.dumps(bounded_delta, sort_keys=True),
        "rollback_reference": rollback_reference,
        "decision_reason": decision_reason,
        "policy_payload_json": payload_json,
        "policy_hash": _logical_hash({"policy_version": policy_version, "payload": payload, "created_at_utc": created_at}),
    }


# =========================================================================
# Supervisor integration helpers
# =========================================================================


def ensure_bootstrap_policy(store: Any, *, now: datetime) -> Dict[str, Any]:
    """Register the CONFIGURED_DEFAULT bootstrap policy once (never labeled LEARNED_OPTIMAL)."""
    existing = store.get_learning_policy(BOOTSTRAP_POLICY_VERSION)
    if existing is not None:
        return existing
    created_at = _iso_utc(now)
    payload = {
        "timing": {"offset_minutes": 0},
        "baseline_qualified_engagement": None,
        "content": {},
        "seo": {},
        "package": {},
        "provenance": BOOTSTRAP_PROVENANCE,
    }
    record = _policy_record(
        policy_version=BOOTSTRAP_POLICY_VERSION, parent_policy_version=None,
        created_at=created_at, status=POLICY_STATUS_ACTIVE, decision="BOOTSTRAP",
        sample_count=0, confidence=0.0, formula_version=QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
        observation_ids=[], evaluation_window="bootstrap", accepted_changes={},
        bounded_delta={}, rollback_reference=None, decision_reason="configured_default_bootstrap",
        payload=payload,
    )
    return store.register_learning_policy(policy=record)


def active_policy_timing_offset_minutes(store: Any, *, fallback: int = 0) -> int:
    """Timing offset of the latest ACTIVE policy; fails closed to ``fallback`` on any anomaly."""
    try:
        policy = store.get_active_learning_policy()
        if policy is None:
            return fallback
        return int(_clamp(_timing_offset_minutes(policy), -MAX_TIMING_OFFSET_MINUTES, MAX_TIMING_OFFSET_MINUTES))
    except Exception:  # noqa: BLE001 - malformed/unknown policy must never override bootstrap
        return fallback
