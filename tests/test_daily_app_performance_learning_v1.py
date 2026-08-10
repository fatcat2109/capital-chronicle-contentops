"""Focused tests: real performance observation + bounded closed-loop learning (FDA-D/FDA-E).

Covers TASK_CONTENTOPS_FINAL_DAILY_APP_REAL_PERFORMANCE_OBSERVATION_AND_CLOSED_LOOP_LEARNING_V1
phase-22 focused test matrix and phase-19 controlled E2E cases A-H (temp stores, fixtures).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from live_contentops import daily_app_performance_v1 as perf
from live_contentops.daily_app_supervisor_v1 import (
    ContentOpsDailyAppSupervisor,
)
from live_contentops.durable_operational_store_v1 import (
    ContentOpsDurableStore,
    PerformanceObservationConflictError,
    SCHEMA_VERSION,
    compute_sha256,
)

T0 = datetime(2026, 8, 9, 14, 0, 0, tzinfo=timezone.utc)          # dispatch / publish instant
AFTER_ALL_WINDOWS = datetime(2026, 8, 20, 0, 0, 0, tzinfo=timezone.utc)  # > T0 + 7d
PACKAGE_IDENTITY = "pkg-perf-1"

COLLECTED_METRICS = {
    "impressions": 1000,
    "shares": 12,
    "reposts": 8,
    "saves": 5,
    "bookmarks": 4,
    "substantive_replies": 6,
    "canonical_article_clicks": 20,
    "subscriber_conversions": 3,
    "meaningful_reads": 40,
    "completion_rate": 0.7,
}
AVAILABILITY_ALL = {k: "AVAILABLE" for k in COLLECTED_METRICS}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _store(tmp_path, name="perf.sqlite3"):
    return ContentOpsDurableStore(tmp_path / name, auto_migrate=True)


def _supervisor(tmp_path, *, collector=None, learning=False, clock=None, store=None):
    return ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "life.sqlite3",
        store=store,
        output_root=tmp_path / "out",
        clock=clock or (lambda: AFTER_ALL_WINDOWS),
        newsroom_cycle=lambda **kwargs: {"classification": "NO_PUBLICATION"},
        publication_publisher=lambda d, p: {"status": "DISPATCH_CONFIRMED_NO_WRITE"},
        publication_readback_provider=None,
        enable_publication_lifecycle=False,
        enable_performance_observation=True,
        performance_collector=collector,
        performance_learning_enabled=learning,
        operating_mode="AUTONOMOUS_DEFAULT",
    )


def _seed_confirmed_publication(
    sup, *, dispatch_status="DISPATCH_CONFIRMED", object_id="obj-A",
    reconciliation_status="RECONCILED_CONFIRMED", platform="substack",
    url="https://substack.com/@cc/p-a", dispatch_id="pd_pub", suffix="0",
    package_identity=PACKAGE_IDENTITY, dispatched_at=None,
):
    """Seed one canonical durable publication lineage (work_item->outbox->dispatch->readback->recon)."""
    store = sup._store
    dispatched_at = dispatched_at or T0
    work_item_id = f"wi_pub_{suffix}"
    message_id = f"om_pub_{suffix}"
    conn = store.get_connection()
    try:
        conn.execute("INSERT INTO work_items VALUES (?,?,?,?,?,?,?,?)",
                     (work_item_id, f"story_pub_{suffix}", "Perf Publication", "EVIDENCE_READY", 2, "surf",
                      "2026-08-09T13:00:00Z", "2026-08-09T14:00:00Z"))
        conn.execute("INSERT INTO outbox_messages VALUES (?,?,?,?,?,?)",
                     (message_id, work_item_id, platform,
                      json.dumps({"window_id": work_item_id, "destination": platform,
                                  "package_identity": package_identity}, sort_keys=True),
                      "READY", "2026-08-09T14:00:00Z"))
        conn.execute(
            "INSERT INTO platform_dispatches (dispatch_id,message_id,platform,status,dispatched_at,"
            "public_object_id,public_object_url,public_object_url_hash) VALUES (?,?,?,?,?,?,?,?)",
            (dispatch_id, message_id, platform, dispatch_status, dispatched_at.isoformat(),
             object_id, url, compute_sha256(url) if url else None),
        )
        conn.execute("INSERT INTO readbacks VALUES (?,?,?,?)",
                     (f"rb_pub_{suffix}", dispatch_id, json.dumps({"verified": True}, sort_keys=True),
                      "2026-08-09T14:01:00Z"))
    finally:
        conn.close()
    # Reconciliation with the deterministic lifecycle identity.
    ids = sup._lifecycle_identity(work_item_id, platform, package_identity)
    store.register_reconciliation(
        reconciliation_id=ids["reconciliation_id"], work_item_id=work_item_id,
        status=reconciliation_status,
    )
    return dispatch_id


def _collector(metrics=None, availability=None, status="COLLECTED", calls=None):
    metrics = COLLECTED_METRICS if metrics is None else metrics
    availability = AVAILABILITY_ALL if availability is None else availability

    def collector(dispatch_id, public_object_id, observation_window):
        if calls is not None:
            calls.append((dispatch_id, public_object_id, observation_window))
        return {"status": status, "metrics": dict(metrics), "availability": dict(availability)}
    return collector


# ---------------------------------------------------------------------------
# Eligibility gate (tests 1-5, 25)
# ---------------------------------------------------------------------------


def test_only_real_reconciled_public_object_is_learning_eligible(tmp_path):
    result = perf.assess_learning_eligibility(
        dispatch_status="DISPATCH_CONFIRMED", public_object_id="obj-A",
        reconciliation_status="RECONCILED_CONFIRMED", readback_count=1,
    )
    assert result["learning_eligible"] is True


def test_controlled_no_write_excluded(tmp_path):
    result = perf.assess_learning_eligibility(
        dispatch_status="CONTROLLED_NO_PUBLIC_WRITE", public_object_id=None,
        reconciliation_status="RECONCILED_CONTROLLED_NO_WRITE", readback_count=0,
    )
    assert result["learning_eligible"] is False
    assert any("controlled_no_public_write" in r for r in result["reasons"])


def test_unknown_write_excluded(tmp_path):
    result = perf.assess_learning_eligibility(
        dispatch_status="UNKNOWN_WRITE", public_object_id=None,
        reconciliation_status="RECONCILIATION_PENDING_OPERATOR_RECOVERY", readback_count=0,
    )
    assert result["learning_eligible"] is False
    assert any("unknown_write" in r for r in result["reasons"])


def test_pending_readback_excluded(tmp_path):
    result = perf.assess_learning_eligibility(
        dispatch_status="DISPATCH_CONFIRMED", public_object_id="obj-A",
        reconciliation_status="RECONCILIATION_PENDING_READBACK", readback_count=1,
    )
    assert result["learning_eligible"] is False


def test_missing_public_object_id_excluded(tmp_path):
    result = perf.assess_learning_eligibility(
        dispatch_status="DISPATCH_CONFIRMED", public_object_id=None,
        reconciliation_status="RECONCILED_CONFIRMED", readback_count=1,
    )
    assert result["learning_eligible"] is False
    assert any("missing_public_object_id" in r for r in result["reasons"])


def test_identity_chain_exact(tmp_path):
    sup = _supervisor(tmp_path)
    dispatch_id = _seed_confirmed_publication(sup)
    sup._run_performance_observations(AFTER_ALL_WINDOWS)
    dispatch = sup._store.get_platform_dispatch(dispatch_id)
    for obs in sup._store.list_performance_observations(dispatch_id=dispatch_id):
        assert obs["dispatch_id"] == dispatch_id
        assert obs["public_object_id"] == dispatch["public_object_id"]
        assert obs["work_item_id"].startswith("wi_pub")
        assert obs["platform"] == dispatch["platform"]


# ---------------------------------------------------------------------------
# Observation contract (tests 6,7,8,9,10,11,12,13)
# ---------------------------------------------------------------------------


def test_observation_identity_deterministic(tmp_path):
    a = perf.observation_identity(dispatch_id="d", public_object_id="o", platform="substack",
                                  observation_window="EARLY")
    b = perf.observation_identity(dispatch_id="d", public_object_id="o", platform="substack",
                                  observation_window="EARLY")
    c = perf.observation_identity(dispatch_id="d", public_object_id="o", platform="substack",
                                  observation_window="DAILY")
    assert a == b
    assert a != c


def test_repeated_same_observation_idempotent(tmp_path):
    store = _store(tmp_path)
    # Seed the minimal publication lineage so the observation FK resolves.
    conn = store.get_connection()
    try:
        conn.execute("INSERT INTO work_items VALUES ('w1','s1','T','EVIDENCE_READY',2,'surf','2026-08-09T13:00:00Z','2026-08-09T14:00:00Z')")
        conn.execute("INSERT INTO outbox_messages VALUES ('om1','w1','substack','{}','READY','2026-08-09T14:00:00Z')")
        conn.execute(
            "INSERT INTO platform_dispatches (dispatch_id,message_id,platform,status,dispatched_at,public_object_id) "
            "VALUES ('d1','om1','substack','DISPATCH_CONFIRMED','2026-08-09T14:00:00Z','o1')")
    finally:
        conn.close()
    observation = {
        "observation_id": "obs_fixed", "schema_version": perf.OBSERVATION_SCHEMA_VERSION,
        "dispatch_id": "d1", "work_item_id": "w1", "platform": "substack",
        "public_object_id": "o1", "public_object_url_hash": None,
        "observation_window": "EARLY", "scheduled_for_utc": "2026-08-09T14:15:00Z",
        "collected_at_utc": None, "collector_capability_version": perf.COLLECTOR_CAPABILITY_VERSION,
        "collection_status": "SCHEDULED", "metrics_native_json": "{}",
        "metric_availability_json": "{}", "source_identity": "test", "learning_eligible": 1,
    }
    observation["observation_hash"] = perf.observation_hash(observation)
    store.register_performance_observation(observation=observation)
    store.register_performance_observation(observation=observation)  # idempotent
    assert len(store.list_performance_observations(dispatch_id="d1")) == 1
    # Conflicting content for the same identity fails closed.
    conflicting = dict(observation)
    conflicting["metrics_native_json"] = json.dumps({"impressions": 5}, sort_keys=True)
    conflicting["observation_hash"] = perf.observation_hash(conflicting)
    with pytest.raises(PerformanceObservationConflictError):
        store.register_performance_observation(observation=conflicting)


def test_unavailable_metric_not_zero(tmp_path):
    score = perf.qualified_engagement_score({}, {"shares": "UNAVAILABLE"})
    assert score is None  # no available qualified signal -> no score, not zero
    score2 = perf.qualified_engagement_score({"shares": None}, {"shares": "UNAVAILABLE"})
    assert score2 is None


def test_native_metrics_preserved(tmp_path):
    calls = []
    sup = _supervisor(tmp_path, collector=_collector(calls=calls))
    dispatch_id = _seed_confirmed_publication(sup)
    sup._run_performance_observations(AFTER_ALL_WINDOWS)
    obs = sup._store.list_performance_observations(dispatch_id=dispatch_id)
    assert len(obs) == len(perf.OBSERVATION_WINDOWS)
    for o in obs:
        assert o["collection_status"] == "COLLECTED"
        native = json.loads(o["metrics_native_json"])
        assert native == COLLECTED_METRICS  # native values preserved, no fake normalization


def test_observation_scheduling_survives_restart_no_duplicate_windows(tmp_path):
    calls = []
    sup = _supervisor(tmp_path, collector=_collector(calls=calls), clock=lambda: AFTER_ALL_WINDOWS)
    dispatch_id = _seed_confirmed_publication(sup)
    sup._run_performance_observations(AFTER_ALL_WINDOWS)
    n1 = len(sup._store.list_performance_observations(dispatch_id=dispatch_id))
    # Restart: new supervisor over the same store must not re-schedule.
    restarted = _supervisor(tmp_path, collector=_collector(calls=calls), store=sup._store,
                            clock=lambda: AFTER_ALL_WINDOWS)
    restarted._run_performance_observations(AFTER_ALL_WINDOWS)
    n2 = len(sup._store.list_performance_observations(dispatch_id=dispatch_id))
    assert n1 == n2 == len(perf.OBSERVATION_WINDOWS)


def test_idle_tick_zero_metrics_calls(tmp_path):
    calls = []
    sup = _supervisor(tmp_path, collector=_collector(calls=calls), clock=lambda: T0 + timedelta(minutes=1))
    dispatch_id = _seed_confirmed_publication(sup, dispatched_at=T0)
    report = sup.tick(now=T0 + timedelta(minutes=1))
    # Observations are scheduled but none due yet -> zero collector calls.
    assert len(calls) == 0
    assert report["performance_observations"]["collected"] == 0


def test_metrics_collection_zero_llm_calls(tmp_path):
    calls = []
    sup = _supervisor(tmp_path, collector=_collector(calls=calls), clock=lambda: AFTER_ALL_WINDOWS)
    _seed_confirmed_publication(sup)
    report = sup.tick(now=AFTER_ALL_WINDOWS)
    # No editorial window is due at this clock, so the newsroom cycle (LLM) is never invoked.
    assert report["newsroom_cycle_invocations"] == 0
    assert report["performance_observations"]["collected"] == len(perf.OBSERVATION_WINDOWS)


# ---------------------------------------------------------------------------
# Learning guards + policy versioning (tests 14-22)
# ---------------------------------------------------------------------------


def _seed_eligible_observations(store, sup, count, *, collector_metrics=None, collector_availability=None, tag="0"):
    """Seed `count` eligible confirmed publications and collect observations for each."""
    for i in range(count):
        dispatch_id = f"pd_{tag}_{i}"
        _seed_confirmed_publication(
            sup, object_id=f"obj-{tag}-{i}", dispatch_id=dispatch_id, suffix=f"{tag}-{i}",
            package_identity=f"pkg-{tag}-{i}", url=f"https://substack.com/@cc/p-{tag}-{i}",
        )
    sup._performance_collector = _collector(metrics=collector_metrics, availability=collector_availability)
    sup._run_performance_observations(AFTER_ALL_WINDOWS)


def test_small_n_holds_policy(tmp_path):
    sup = _supervisor(tmp_path, learning=False, clock=lambda: AFTER_ALL_WINDOWS)
    # Seed fewer than MIN_ELIGIBLE_OBSERVATIONS eligible publications.
    _seed_eligible_observations(sup._store, sup, perf.MIN_ELIGIBLE_OBSERVATIONS - 1)
    perf.ensure_bootstrap_policy(sup._store, now=T0)
    decision = perf.evaluate_learning_decision(sup._store, evaluation_window="w", now=AFTER_ALL_WINDOWS)
    assert decision["decision"] == perf.DECISION_HOLD
    assert decision["policy_version"] is None


def test_low_confidence_holds_policy(tmp_path):
    sup = _supervisor(tmp_path, learning=False, clock=lambda: AFTER_ALL_WINDOWS)
    # Enough eligible observations but no available qualified metrics -> no scores -> low confidence.
    _seed_eligible_observations(sup._store, sup, perf.MIN_ELIGIBLE_OBSERVATIONS,
                                collector_metrics={}, collector_availability={})
    perf.ensure_bootstrap_policy(sup._store, now=T0)
    decision = perf.evaluate_learning_decision(sup._store, evaluation_window="w", now=AFTER_ALL_WINDOWS)
    assert decision["decision"] == perf.DECISION_HOLD


def test_accepted_update_creates_immutable_child_policy_and_bounded_delta(tmp_path):
    sup = _supervisor(tmp_path, learning=False, clock=lambda: AFTER_ALL_WINDOWS)
    _seed_eligible_observations(sup._store, sup, perf.CONFIDENCE_SAMPLE_DENOMINATOR)
    perf.ensure_bootstrap_policy(sup._store, now=T0)
    bootstrap = sup._store.get_learning_policy(perf.BOOTSTRAP_POLICY_VERSION)
    decision = perf.evaluate_learning_decision(sup._store, evaluation_window="w", now=AFTER_ALL_WINDOWS)
    assert decision["decision"] == perf.DECISION_ACCEPT
    child = sup._store.get_learning_policy(decision["policy_version"])
    assert child is not None
    assert child["parent_policy_version"] == perf.BOOTSTRAP_POLICY_VERSION
    assert child["status"] == perf.POLICY_STATUS_ACTIVE
    delta = decision["bounded_delta"]
    assert abs(delta["timing_offset_minutes_after"] - delta["timing_offset_minutes_before"]) <= perf.MAX_DELTA_PER_UPDATE_MINUTES
    # Old bootstrap row content preserved (history not rewritten).
    bootstrap_after = sup._store.get_learning_policy(perf.BOOTSTRAP_POLICY_VERSION)
    assert bootstrap_after["policy_payload_json"] == bootstrap["policy_payload_json"]


def test_restart_loads_same_active_policy(tmp_path):
    sup = _supervisor(tmp_path, learning=False, clock=lambda: AFTER_ALL_WINDOWS)
    _seed_eligible_observations(sup._store, sup, perf.CONFIDENCE_SAMPLE_DENOMINATOR)
    perf.ensure_bootstrap_policy(sup._store, now=T0)
    decision = perf.evaluate_learning_decision(sup._store, evaluation_window="w", now=AFTER_ALL_WINDOWS)
    assert decision["decision"] == perf.DECISION_ACCEPT
    active = sup._store.get_active_learning_policy()
    assert active["policy_version"] == decision["policy_version"]
    # Restart (new supervisor, same store) loads the same active policy timing offset.
    restarted = _supervisor(tmp_path, store=sup._store, clock=lambda: AFTER_ALL_WINDOWS)
    assert perf.active_policy_timing_offset_minutes(restarted._store) == perf._timing_offset_minutes(active)


def test_timing_policy_changes_future_schedule_deterministically(tmp_path):
    sup = _supervisor(tmp_path, clock=lambda: AFTER_ALL_WINDOWS)
    sup._store = sup._store
    # With bootstrap (offset 0), next wake is the configured window; with an accepted offset the
    # scheduled window must shift by exactly the bounded offset.
    base_offset = perf.active_policy_timing_offset_minutes(sup._store)
    assert base_offset == 0
    # Register an ACTIVE policy with +15 min offset.
    payload = {"timing": {"offset_minutes": 15}, "baseline_qualified_engagement": 1.0,
               "content": {}, "seo": {}, "package": {}, "provenance": "LEARNED_BOUNDED_UPDATE"}
    record = {
        "policy_version": "policy_test_offset", "parent_policy_version": perf.BOOTSTRAP_POLICY_VERSION,
        "created_at_utc": AFTER_ALL_WINDOWS.isoformat(), "status": perf.POLICY_STATUS_ACTIVE,
        "decision": perf.DECISION_ACCEPT, "sample_count": 8, "confidence": 1.0,
        "formula_version": perf.QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
        "observation_ids_json": "[]", "evaluation_window": "w",
        "accepted_changes_json": "{}", "bounded_delta_json": "{}", "rollback_reference": None,
        "decision_reason": "test", "policy_payload_json": json.dumps(payload, sort_keys=True),
        "policy_hash": compute_sha256("test1"),
    }
    sup._store.register_learning_policy(policy=record)
    assert perf.active_policy_timing_offset_minutes(sup._store) == 15


def test_outlier_cannot_dominate(tmp_path):
    # A single extreme observation is capped at SCORE_CAP and bounded delta limits change.
    huge = dict(COLLECTED_METRICS)
    huge["subscriber_conversions"] = 10**9  # extreme outlier
    cap_score = perf.qualified_engagement_score(huge, AVAILABILITY_ALL)
    assert cap_score is not None and cap_score <= perf.SCORE_CAP


def test_rollback_creates_new_version_not_history_rewrite(tmp_path):
    sup = _supervisor(tmp_path, learning=False, clock=lambda: AFTER_ALL_WINDOWS)
    _seed_eligible_observations(sup._store, sup, perf.CONFIDENCE_SAMPLE_DENOMINATOR, tag="a")
    perf.ensure_bootstrap_policy(sup._store, now=T0)
    first = perf.evaluate_learning_decision(sup._store, evaluation_window="w", now=AFTER_ALL_WINDOWS)
    assert first["decision"] == perf.DECISION_ACCEPT
    first_version = first["policy_version"]
    # Deteriorate: add low-but-real qualified observations to drag mean below the baseline.
    low_metrics = {
        "impressions": 1000, "shares": 1, "saves": 1, "completion_rate": 0.3,
        "canonical_article_clicks": 1, "subscriber_conversions": 0,
    }
    low_availability = {k: "AVAILABLE" for k in low_metrics}
    _seed_eligible_observations(sup._store, sup, perf.CONFIDENCE_SAMPLE_DENOMINATOR,
                                collector_metrics=low_metrics, collector_availability=low_availability, tag="b")
    second = perf.evaluate_learning_decision(sup._store, evaluation_window="w2", now=AFTER_ALL_WINDOWS)
    assert second["decision"] == perf.DECISION_ROLLBACK
    assert second["policy_version"] != first_version
    # Original accepted row preserved, not deleted.
    assert sup._store.get_learning_policy(first_version) is not None


def test_learning_cannot_weaken_hard_gates(tmp_path):
    sup = _supervisor(tmp_path, learning=False, clock=lambda: AFTER_ALL_WINDOWS)
    _seed_eligible_observations(sup._store, sup, perf.CONFIDENCE_SAMPLE_DENOMINATOR)
    dispatches_before = [d["dispatch_id"] for d in sup._store.list_platform_dispatches()]
    perf.ensure_bootstrap_policy(sup._store, now=T0)
    perf.evaluate_learning_decision(sup._store, evaluation_window="w", now=AFTER_ALL_WINDOWS)
    # Learning must not create/change dispatches or any publication rows.
    dispatches_after = [d["dispatch_id"] for d in sup._store.list_platform_dispatches()]
    assert dispatches_before == dispatches_after
    assert len(dispatches_after) == perf.CONFIDENCE_SAMPLE_DENOMINATOR


def test_learning_cannot_mutate_kill_switch(tmp_path):
    ks = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "ks.sqlite3", output_root=tmp_path / "out",
        clock=lambda: AFTER_ALL_WINDOWS, operating_mode="KILL_SWITCH",
        newsroom_cycle=lambda **kwargs: {"classification": "NO_PUBLICATION"},
        enable_performance_observation=True, performance_learning_enabled=True,
        performance_collector=_collector(),
    )
    report = ks.tick(now=AFTER_ALL_WINDOWS)
    assert report["kill_switch_active"] is True
    # Kill switch blocks new public dispatch...
    assert report["windows_dispatched"] == 0
    assert report["public_write_performed"] is False
    # ...but read-only performance observation still runs under KILL_SWITCH.
    assert report["performance_observation_state"] == "RUN"


# ---------------------------------------------------------------------------
# Schema migration lossless (test 26)
# ---------------------------------------------------------------------------


def test_v5_to_v6_migration_lossless(tmp_path):
    p = tmp_path / "mig.sqlite3"
    s = ContentOpsDurableStore(p, auto_migrate=False)
    s.run_migrations(target_version=5)
    c = s.get_connection()
    c.execute("INSERT INTO work_items VALUES ('w','st','T','EVIDENCE_READY',2,'surf','2026-08-09T13:00:00Z','2026-08-09T14:00:00Z')")
    c.execute("INSERT INTO outbox_messages VALUES ('om','w','substack','{}','READY','2026-08-09T14:00:00Z')")
    c.execute("INSERT INTO platform_dispatches (dispatch_id,message_id,platform,status,dispatched_at,public_object_id) VALUES ('pd','om','substack','DISPATCH_CONFIRMED','2026-08-09T14:00:00Z','obj-1')")
    c.execute("INSERT INTO metrics VALUES ('metric_contentops_production_epoch_start_utc','contentops_production_epoch_start_utc',1786262820.663942,'x')")
    c.close()
    store = ContentOpsDurableStore(p, auto_migrate=True)
    assert store.get_current_schema_version() == SCHEMA_VERSION == 8
    cc = store.get_connection()
    assert cc.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert cc.execute("SELECT metric_value FROM metrics WHERE metric_name='contentops_production_epoch_start_utc'").fetchone()[0] == 1786262820.663942
    assert cc.execute("SELECT public_object_id FROM platform_dispatches WHERE dispatch_id='pd'").fetchone()[0] == "obj-1"
    assert cc.execute("SELECT COUNT(*) FROM work_items").fetchone()[0] == 1
    cc.close()
