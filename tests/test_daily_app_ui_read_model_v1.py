from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from live_contentops.daily_app_supervisor_v1 import (
    TRIGGER_SCHEDULED,
    ContentOpsDailyAppSupervisor,
    build_bootstrap_editorial_window_policy,
    editorial_window_id,
)
from live_contentops.daily_app_ui_read_model_v1 import (
    DailyAppReadModelError,
    build_daily_app_snapshot,
    update_daily_app_mode,
)
from live_contentops.durable_operational_store_v1 import (
    ContentOpsDurableStore,
    OperatingModeConflictError,
)
from live_contentops.server import make_handler

NOW = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


def _store(tmp_path, name="daily.sqlite3"):
    return ContentOpsDurableStore(tmp_path / name, now_fn=lambda: NOW)


def _seed_dispatch(
    store, *, suffix, status, object_id=None, reconciliation=None, public_url=None,
    platform="substack",
):
    work_id = f"work_{suffix}"
    message_id = f"outbox_{suffix}"
    dispatch_id = f"dispatch_{suffix}"
    store.create_work_item(
        story_id=f"story_{suffix}", title=f"Story {suffix}", target_surface="substack",
        work_item_id=work_id,
    )
    store.register_outbox_message(
        message_id=message_id, work_item_id=work_id, destination=platform,
        payload="{}", status="READY",
    )
    store.register_platform_dispatch(
        dispatch_id=dispatch_id, message_id=message_id, platform=platform,
        status=status, public_object_id=object_id, public_object_url=public_url,
    )
    if reconciliation:
        store.register_reconciliation(
            reconciliation_id=f"reconciliation_{suffix}", work_item_id=work_id,
            status=reconciliation,
        )
    return dispatch_id


def _seed_policy(
    store,
    *,
    version,
    parent=None,
    status="ACTIVE",
    decision="BOOTSTRAP",
    sample_count=0,
    confidence=0.0,
    payload=None,
    created_at="2026-08-10T01:00:00Z",
):
    with store.get_connection() as conn:
        conn.execute(
            "INSERT INTO learning_policy_versions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                version,
                parent,
                created_at,
                status,
                decision,
                sample_count,
                confidence,
                "formula.v1",
                "[]",
                "rolling",
                "{}",
                "{}",
                None,
                "fixture lineage",
                json.dumps(payload or {}, sort_keys=True),
                f"hash-{version}",
            ),
        )


def _publication(snapshot, dispatch_id):
    return next(row for row in snapshot["published"]["objects"] if row["dispatch_id"] == dispatch_id)


def _lifecycle_counts(store):
    with store.get_connection() as conn:
        return {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("outbox_messages", "platform_dispatches", "readbacks", "reconciliations")
        }


def test_snapshot_healthy_idle_no_fixture_and_no_second_store(tmp_path):
    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")
    from live_contentops.continuous_headline_ingest_v1 import (
        OUTCOME_CAPTURED_NONE,
        write_ingestion_checkpoint,
    )
    write_ingestion_checkpoint(
        store, now=NOW, last_success_epoch=NOW.timestamp(),
        last_attempt_epoch=NOW.timestamp(), outcome_code=OUTCOME_CAPTURED_NONE,
        consecutive_empty=1, rows_iteration=0,
    )
    before = {path.name for path in tmp_path.iterdir()}
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    after = {path.name for path in tmp_path.iterdir()}
    assert snapshot["runtime"]["controller_health"] == "HEALTHY"
    assert snapshot["freshness"]["state"] == "LIVE_CURRENT"
    cockpit = snapshot["runtime"]["operator_cockpit"]
    assert cockpit["primary_state"] == "RUNNING_IDLE"
    assert cockpit["schedule"]["idle_healthy"] is True
    assert cockpit["schedule"]["next_editorial_wake_utc"] == "2026-08-10T14:00:00Z"
    assert cockpit["schedule"]["next_x_eligible_capture_utc"] == "2026-08-10T13:00:00Z"
    assert cockpit["schedule"]["x_cadence_state"] == "EMPTY_BACKOFF_60M"
    assert cockpit["timeline"] == []
    assert cockpit["safety"]["active_public_write"] is False
    assert cockpit["projection_authority"]["stage_file_presentation_only"] is True
    assert cockpit["projection_authority"]["grants_publication_authority"] is False
    assert cockpit["output_health"] == "ON_TRACK"
    assert snapshot["today"]["build_qualified_floor"] == 4
    assert snapshot["today"]["final_published_target_min"] == 5
    assert snapshot["today"]["final_published_target_max"] == 8
    assert snapshot["today"]["qualified_articles_today"] == 0
    assert snapshot["today"]["remaining_build_deficit"] == 4
    assert snapshot["today"]["remaining_published_deficit"] == 5
    assert snapshot["today"]["live_output_count_basis"] == (
        "SUBSTACK_DISPATCH_CONFIRMED_AND_EXACT_RECONCILIATION_CONFIRMED_"
        "AND_STABLE_PUBLIC_OBJECT_ID_AND_VALID_CANONICAL_URL_AND_EXACT_URL_HASH_"
        "AND_DURABLE_SOURCE_WORK_ITEM_AND_UNIQUE_ARTICLE_IDENTITY"
    )
    assert snapshot["automation"]["configured_intent"]["task_count"] == 4
    assert snapshot["automation"]["observed_host_state"]["state"] == (
        "AUTOMATION_STATE_UNAVAILABLE"
    )
    assert snapshot["authority"]["fixture_fallback"] is False
    assert snapshot["authority"]["snapshot_mutates_lifecycle"] is False
    # SQLite may materialize its own WAL companions while another collected test keeps a
    # connection alive; those files are part of daily.sqlite3, not a second authority store.
    assert after - before <= {"daily.sqlite3-wal", "daily.sqlite3-shm"}
    assert {name for name in after if name.endswith(".sqlite3")} == {"daily.sqlite3"}


def test_snapshot_keeps_supported_automation_observation_distinct_from_intent(tmp_path):
    from live_contentops.codex_desktop_newsroom_operator_v1 import (
        four_task_setup_packet,
        persist_supported_automation_host_observation,
    )

    store = _store(tmp_path)
    packet = four_task_setup_packet()
    persist_supported_automation_host_observation(
        tasks=[
            {
                **task,
                "status": "PAUSED",
                "timezone": packet["timezone"],
                "project": packet["project"],
                "model": packet["model"],
                "reasoning_effort": packet["reasoning_effort"].lower(),
                "prompt_sha256": "current-prompt-hash",
                "config_sha256": (
                    "ea8e1e11a82b6b600fffd791cf9e8560d0d5198905fd5da15170d50ec1f43b65"
                    if index == 0
                    else f"{index + 1:064x}"
                ),
            }
            for index, task in enumerate(packet["tasks"])
        ],
        output_path=tmp_path / "automation_observation" / "latest.json",
        observed_at_utc="2026-08-10T11:59:00Z",
    )

    automation = build_daily_app_snapshot(store.db_path, now=NOW)["automation"]

    assert automation["configured_intent"]["state"] == "CONFIGURED_INTENT"
    assert automation["observed_host_state"]["state"] == "OBSERVED_HOST_STATE"
    assert automation["observed_host_state"]["task_count"] == 4
    first_task = automation["observed_host_state"]["tasks"][0]
    assert first_task["host_config_sha256"] == (
        "ea8e1e11a82b6b600fffd791cf9e8560d0d5198905fd5da15170d50ec1f43b65"
    )
    assert first_task["observation_projection_sha256"] != first_task[
        "host_config_sha256"
    ]
    assert automation["freshness"] == "FRESH"
    assert automation["age_seconds"] == 60


def test_next_wake_skips_a_current_window_already_claimed_by_the_scheduler(tmp_path):
    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")
    policy = build_bootstrap_editorial_window_policy()
    current = next(window for window in policy.core_windows if window.start_hour_utc == 14)
    start = NOW.replace(hour=current.start_hour_utc, minute=0, second=0, microsecond=0)
    end = NOW.replace(hour=current.end_hour_utc, minute=0, second=0, microsecond=0)
    window_id = editorial_window_id(
        policy_version=policy.policy_version,
        window_start_utc=start,
        window_end_utc=end,
        session=current.session,
        trigger_kind=TRIGGER_SCHEDULED,
    )
    store.create_work_item(
        story_id=window_id, title="Claimed scheduled window",
        target_surface="daily_app_editorial_window", work_item_id=window_id,
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert snapshot["runtime"]["next_wake_utc"] == "2026-08-10T16:00:00Z"
    assert snapshot["runtime"]["operator_cockpit"]["schedule"]["next_editorial_wake_utc"] == (
        "2026-08-10T16:00:00Z"
    )


def test_degraded_capture_preserves_exact_durable_outcome_label(tmp_path):
    from live_contentops.continuous_headline_ingest_v1 import (
        OUTCOME_CAPTURE_FAILED,
        write_ingestion_checkpoint,
    )

    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")
    write_ingestion_checkpoint(
        store, now=NOW, last_success_epoch=(NOW.timestamp() - 3600),
        last_attempt_epoch=NOW.timestamp(), outcome_code=OUTCOME_CAPTURE_FAILED,
        consecutive_empty=4, rows_iteration=0,
    )
    cockpit = build_daily_app_snapshot(store.db_path, now=NOW)["runtime"]["operator_cockpit"]
    assert cockpit["primary_state"] == "DEGRADED"
    assert cockpit["intake"]["lane_state"] == "DEGRADED"
    assert cockpit["intake"]["latest_capture_result"] == "CAPTURE_FAILED"
    assert cockpit["intake"]["cadence_state"] == "TRANSIENT_BACKOFF_30M_PLUS"


def test_degraded_capture_projects_bounded_sanitized_attempt_detail(tmp_path):
    from live_contentops.continuous_headline_ingest_v1 import run_ingestion_housekeeping_iteration

    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")
    run_ingestion_housekeeping_iteration(
        store,
        now=NOW,
        state_fn=lambda: {"state": "READY"},
        session_fn=lambda: {"session_state": "READY"},
        capture_fn=lambda **_kwargs: {
            "capture_state": "CAPTURE_FAILED",
            "capture_phase": "EXTRACTION_SCROLL",
            "timeline_responses_observed": 0,
            "new_headlines": 0,
            "failure_class": "MALFORMED_EMPTY_CAPTURE_RESPONSE",
            "failure_detail": "NO_TIMELINE_RESPONSE_OBSERVED_AFTER_RELOAD",
        },
    )
    intake = build_daily_app_snapshot(store.db_path, now=NOW)["runtime"]["operator_cockpit"]["intake"]
    assert intake["latest_capture_result"] == "CAPTURE_FAILED"
    assert intake["failure_class"] == "MALFORMED_EMPTY_CAPTURE_RESPONSE"
    assert intake["failure_detail"] == "NO_TIMELINE_RESPONSE_OBSERVED_AFTER_RELOAD"
    assert intake["eligibility_reason"] == "NO_PRIOR_ATTEMPT"
    assert intake["browser_role"] == "CHROME_CDP_9222_INGESTION_ONLY"
    assert intake["chrome_9222_readiness"] == "READY"
    assert intake["auth_classification"] == "READY"
    assert intake["capture_phase"] == "EXTRACTION_SCROLL"
    assert intake["timeline_responses_observed"] == 0


def test_cockpit_active_researching_requires_exact_active_durable_cycle(tmp_path):
    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")
    work_id = "editorial-active-research"
    owner = "supervisor-test-owner"
    store.create_work_item(
        story_id=work_id, title="Daily App editorial window",
        target_surface="daily_app_editorial_window", work_item_id=work_id,
    )
    lease = store.acquire_lease(
        lease_key=work_id, owner_ref=owner, ttl_seconds=900, work_item_id=work_id,
    )
    store.transition_state(
        work_item_id=work_id, expected_from_state="DISCOVERED", to_state="EVIDENCE_PENDING",
        expected_state_version=1, actor_class="SYSTEM", actor_ref=owner,
        reason_code="EDITORIAL_WINDOW_DUE", explanation="test active research",
        lease_key=work_id, fencing_token=int(lease["fencing_token"]),
        input_artifact_ids=[], output_artifact_ids=[], correlation_id="test-active-research",
    )
    # The read model reopens the store with the real host clock, so keep this synthetic lease
    # unambiguously live across the test authority date.
    with store.get_connection() as conn:
        conn.execute(
            "UPDATE leases SET expires_at='2030-01-01T00:00:00+00:00' WHERE lease_key=?",
            (work_id,),
        )
    from live_contentops.runtime_activity_projection_v1 import RuntimeActivityRecorderV1
    RuntimeActivityRecorderV1(
        output_dir=tmp_path / "daily_app_outputs" / work_id,
        work_item_id=work_id,
        now_fn=lambda: NOW,
    ).record(
        "GROUNDED_RESEARCH", candidate_rank=1, candidate_count=6,
        story_label="Fed policy signals reshape the rate-cut path",
        grounding="latest-web source-bound evidence",
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    cockpit = snapshot["runtime"]["operator_cockpit"]
    assert cockpit["primary_state"] == "RESEARCHING"
    assert cockpit["current_activity"]["current_stage"] == "GROUNDED_RESEARCH"
    assert cockpit["current_activity"]["candidate_rank"] == 1
    assert cockpit["current_activity"]["candidate_count"] == 6
    assert cockpit["current_activity"]["story_label"] == (
        "Fed policy signals reshape the rate-cut path"
    )
    assert next(row for row in cockpit["timeline"] if row["stage"] == "GROUNDED_RESEARCH")["state"] == "current"


def test_cockpit_degraded_intake_does_not_overstate_publication_runtime(tmp_path):
    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")
    cockpit = build_daily_app_snapshot(store.db_path, now=NOW)["runtime"]["operator_cockpit"]
    assert cockpit["primary_state"] == "DEGRADED"
    assert cockpit["intake"]["lane_state"] == "DEGRADED"
    assert cockpit["publication_runtime_health"] == "HEALTHY"


def test_cockpit_browser_interaction_is_sanitized_current_truth(tmp_path):
    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")
    telemetry = tmp_path / "control" / "browser_interaction_budget_v1"
    telemetry.mkdir(parents=True)
    (telemetry / "current_state.json").write_text(
        json.dumps({
            "schema_version": "contentops.browser_interaction_telemetry.v1",
            "state": "PUBLICATION_ACTIVE",
            "reason": "EXACT_DESTINATION_PUBLICATION",
            "destination": "substack",
            "started_at_utc": "2026-08-10T11:59:30Z",
            "last_active_browser_interaction_at_utc": "2026-08-10T11:59:30Z",
        }),
        encoding="utf-8",
    )
    cockpit = build_daily_app_snapshot(store.db_path, now=NOW)["runtime"]["operator_cockpit"]
    assert cockpit["primary_state"] == "PUBLISHING"
    assert cockpit["browser"] == {
        "state": "PUBLICATION_ACTIVE",
        "external_browser_activity_active": True,
        "last_active_at_utc": "2026-08-10T11:59:30Z",
        "last_reason": "EXACT_DESTINATION_PUBLICATION",
        "last_destination": "substack",
    }


def test_cockpit_stopped_and_kill_switch_are_both_explicit(tmp_path):
    store = _store(tmp_path)
    control = store.get_operating_control()
    store.update_operating_control(
        expected_state_version=control["state_version"], operating_mode="KILL_SWITCH",
        control_source="TEST",
    )
    cockpit = build_daily_app_snapshot(store.db_path, now=NOW)["runtime"]["operator_cockpit"]
    assert cockpit["primary_state"] == "STOPPED"
    assert cockpit["supervisor_state"] == "STOPPED"
    assert cockpit["safety"]["kill_switch_active"] is True
    assert cockpit["safety"]["new_public_writes_blocked"] is True


def test_cockpit_latest_completed_no_publication_and_published_history(tmp_path):
    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")
    no_pub = "editorial-no-publication"
    published = "editorial-published"
    for work_id in (no_pub, published):
        store.create_work_item(
            story_id=work_id, title=f"Daily App editorial window {work_id}",
            target_surface="daily_app_editorial_window", work_item_id=work_id,
        )
    with store.get_connection() as conn:
        conn.execute(
            "UPDATE work_items SET current_state='REJECTED', updated_at='2026-08-10T11:59:00+00:00' WHERE work_item_id=?",
            (no_pub,),
        )
        conn.execute(
            "UPDATE work_items SET current_state='COMPLETE', updated_at='2026-08-10T11:58:00+00:00' WHERE work_item_id=?",
            (published,),
        )
    no_pub_dir = tmp_path / "daily_app_outputs" / no_pub
    no_pub_dir.mkdir(parents=True)
    (no_pub_dir / "rolling_x_newsroom_cycle_evidence_v1.json").write_text(
        json.dumps({
            "classification": "NO_PUBLICATION",
            "exact_next_blocker": "MINIMUM_TRUSTWORTHY_EVIDENCE_NOT_MET",
            "ranked_viability": {
                "selected_rank": 2,
                "selected_cluster": {"selection_case": "Held candidate topic"},
                "selected_evidence": {"status": "BLOCKED"},
            },
            "ranked_assignment": {"ranked_clusters": [{}, {}, {}]},
            "candidate_walk": {
                "ranked_candidate_count": 3,
                "attempted_candidate_count": 3,
                "candidate_attempts": [
                    {
                        "rank": 1,
                        "candidate_title": "First candidate",
                        "terminal_reason": "INSUFFICIENT_READER_VALUE",
                    },
                    {
                        "rank": 2,
                        "candidate_title": "Second candidate",
                        "terminal_reason": "EVIDENCE_BLOCKED",
                    },
                    {
                        "rank": 3,
                        "candidate_title": "Third candidate",
                        "terminal_reason": "EVIDENCE_BLOCKED",
                    },
                ],
                "selected_publication_candidate": None,
                "opportunity_terminal_reason": "ALL_BOUNDED_CANDIDATES_EXHAUSTED",
            },
        }),
        encoding="utf-8",
    )
    published_dir = tmp_path / "daily_app_outputs" / published
    published_dir.mkdir(parents=True)
    (published_dir / "rolling_x_newsroom_cycle_evidence_v1.json").write_text(
        json.dumps({
            "classification": "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL",
            "article": {"title": "Published evidence-bound story"},
            "ranked_viability": {
                "selected_rank": 1,
                "selected_cluster": {"selection_case": "Published candidate"},
                "selected_evidence": {"status": "PASS"},
            },
            "ranked_assignment": {"ranked_clusters": [{}, {}]},
        }),
        encoding="utf-8",
    )
    store.register_outbox_message(
        message_id="outbox_history", work_item_id=published, destination="substack",
        payload="{}", status="DISPATCH_CONFIRMED",
    )
    store.register_platform_dispatch(
        dispatch_id="dispatch_history", message_id="outbox_history", platform="substack",
        status="DISPATCH_CONFIRMED", public_object_id="post-history",
        public_object_url="https://capitalchronicle.substack.com/p/published-history",
    )
    store.register_reconciliation(
        reconciliation_id="reconciliation_history", work_item_id=published,
        status="RECONCILED_CONFIRMED",
    )
    cockpit = build_daily_app_snapshot(store.db_path, now=NOW)["runtime"]["operator_cockpit"]
    assert cockpit["last_completed_editorial"]["result"] == "NO_PUBLICATION"
    assert cockpit["last_completed_editorial"]["exact_reason"] == (
        "MINIMUM_TRUSTWORTHY_EVIDENCE_NOT_MET"
    )
    assert cockpit["last_completed_editorial"]["candidates_attempted"] == 3
    assert cockpit["last_completed_editorial"]["candidate_terminal_reasons"][0] == {
        "rank": 1,
        "title": "First candidate",
        "terminal_reason": "INSUFFICIENT_READER_VALUE",
    }
    assert cockpit["last_completed_editorial"]["opportunity_terminal_reason"] == (
        "ALL_BOUNDED_CANDIDATES_EXHAUSTED"
    )
    published_row = next(
        row for row in cockpit["recent_activity"] if row["work_item_id"] == published
    )
    assert published_row["result"] == "REAL_PUBLICATION_CONFIRMED"
    assert published_row["canonical_public_url"] == (
        "https://capitalchronicle.substack.com/p/published-history"
    )
    assert published_row["research_result"] == "PASS"


def test_historical_unlinked_and_terminal_incidents_are_not_active(tmp_path):
    store = _store(tmp_path)
    store.upsert_heartbeat("daily-supervisor")
    store.register_incident(
        incident_id="historical-unlinked", work_item_id=None, severity="HIGH",
        description="Historical safe failure",
    )
    store.create_work_item(
        story_id="story-terminal", title="Terminal", target_surface="substack",
        work_item_id="work-terminal",
    )
    with store.get_connection() as conn:
        conn.execute(
            "UPDATE work_items SET current_state='COMPLETE' WHERE work_item_id='work-terminal'"
        )
    store.register_incident(
        incident_id="historical-terminal", work_item_id="work-terminal", severity="MEDIUM",
        description="Resolved lifecycle incident",
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert snapshot["incidents"]["active_count"] == 0
    assert snapshot["incidents"]["items"] == []
    assert snapshot["incidents"]["history_count"] == 2
    assert all(not row["current_actionable"] for row in snapshot["incidents"]["recent_history"])


def test_linkedin_persisted_browser_readiness_is_overridden_by_official_api_auth_state(tmp_path):
    store = _store(tmp_path)
    store.upsert_destination_readiness(row={
        "surface": "LINKEDIN_POST",
        "platform": "linkedin",
        "transport_registry_version": "contentops.destination_transport_registry.v1",
        "transport_type": "EDGE_CDP",
        "readiness_state": "READY_AUTHENTICATED",
        "destination_identity": "historical-browser-identity",
        "identity_match": True,
        "write_eligible": True,
        "probe_kind": "EDGE_CDP_IDENTITY",
        "probed_at_utc": "2026-08-10T11:00:00Z",
        "sanitized_detail": {},
    })
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    linkedin = next(
        row for row in snapshot["platforms"]["destinations"]
        if row["platform_id"] == "linkedin"
    )
    assert linkedin["readiness"] == "AUTH_UNAVAILABLE"
    assert linkedin["transport_type"] == "OFFICIAL_MEMBER_API"
    assert linkedin["write_eligible"] is False
    incident = next(
        row["incident_id"] == "derived:readiness:LINKEDIN_POST"
        and row
        for row in snapshot["incidents"]["items"]
    )
    assert incident["what_happened"] == "AUTH_UNAVAILABLE"
    assert "official-member OAuth" in incident["operator_action"]


def test_linkedin_official_member_api_auth_projection_is_sanitized(tmp_path):
    store = _store(tmp_path)
    store.upsert_destination_readiness(row={
        "surface": "LINKEDIN_POST",
        "platform": "linkedin",
        "transport_registry_version": "contentops.destination_transport_registry.v2",
        "transport_type": "OFFICIAL_MEMBER_API",
        "readiness_state": "READY_NON_BROWSER_BINDING",
        "destination_identity": "Jim Pham",
        "identity_match": True,
        "write_eligible": True,
        "probe_kind": "OFFICIAL_MEMBER_API_LOCAL_AUTH_METADATA",
        "probed_at_utc": "2026-08-13T11:00:00Z",
        "sanitized_detail": {
            "authenticated": True,
            "official_api_state": "READY_OFFICIAL_MEMBER_API",
            "expiry_at_utc": "2026-10-12T11:00:00Z",
            "days_remaining": 60,
            "readback_capability": "READBACK_CAPABILITY_LIMITED",
            "secure_store_binding": "WINDOWS_DPAPI_CURRENT_USER:contentops.linkedin.member.v1",
            "cdp_navigation_performed": False,
            "network_probe_performed": False,
        },
    })
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    linkedin = next(row for row in snapshot["platforms"]["destinations"] if row["platform_id"] == "linkedin")
    assert linkedin["readiness"] == "READY_OFFICIAL_MEMBER_API"
    assert linkedin["write_eligible"] is True
    assert linkedin["authenticated"] is True
    assert linkedin["auth_expiry_at_utc"] == "2026-10-12T11:00:00Z"
    assert linkedin["auth_days_remaining"] == 60
    assert linkedin["safe_identity"] == "Jim Pham"
    assert linkedin["transport_type"] == "OFFICIAL_MEMBER_API"
    assert linkedin["readback_capability"] == "READBACK_CAPABILITY_LIMITED"


def test_publication_lifecycle_classes_are_exact(tmp_path):
    store = _store(tmp_path)
    real = _seed_dispatch(
        store, suffix="real", status="DISPATCH_CONFIRMED", object_id="public-123",
        reconciliation="RECONCILED_CONFIRMED",
    )
    pending = _seed_dispatch(
        store, suffix="pending", status="DISPATCH_CONFIRMED", object_id="public-456",
        reconciliation="RECONCILIATION_PENDING_READBACK",
    )
    incomplete = _seed_dispatch(
        store, suffix="incomplete", status="DISPATCH_CONFIRMED", object_id="public-789",
        reconciliation="RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE",
    )
    unknown = _seed_dispatch(
        store, suffix="unknown", status="UNKNOWN_WRITE",
        reconciliation="RECONCILIATION_PENDING_OPERATOR_RECOVERY",
    )
    controlled = _seed_dispatch(
        store, suffix="controlled", status="CONTROLLED_NO_PUBLIC_WRITE",
        reconciliation="RECONCILED_CONTROLLED_NO_WRITE",
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert _publication(snapshot, real)["lifecycle_classification"] == "REAL_PUBLICATION_CONFIRMED"
    assert _publication(snapshot, real)["public_object_id"] == "public-123"
    assert _publication(snapshot, pending)["lifecycle_classification"] == "CONFIRMED_DISPATCH_PENDING_READBACK"
    assert _publication(snapshot, incomplete)["lifecycle_classification"] == (
        "CONFIRMED_PUBLICATION_CONTENT_INCOMPLETE"
    )
    assert _publication(snapshot, unknown)["lifecycle_classification"] == "UNKNOWN_WRITE"
    assert _publication(snapshot, controlled)["lifecycle_classification"] == "CONTROLLED_NO_PUBLIC_WRITE"
    assert snapshot["published"]["real_publication_count"] == 1
    assert snapshot["published"]["controlled_no_public_write_count"] == 1
    # The pending dispatch and UNKNOWN_WRITE require recovery; the terminal incomplete object
    # does not.
    assert snapshot["published"]["pending_readback_count"] == 2
    assert snapshot["runtime"]["operator_cockpit"]["safety"]["unknown_write_count"] == 1
    assert snapshot["runtime"]["operator_cockpit"]["primary_state"] == "ACTION_REQUIRED"
    assert any(item["what_happened"] == "UNKNOWN_WRITE" for item in snapshot["incidents"]["items"])


def test_only_safe_canonical_substack_article_url_is_exposed(tmp_path):
    store = _store(tmp_path)
    safe = _seed_dispatch(
        store, suffix="safe-url", status="DISPATCH_CONFIRMED", object_id="public-safe",
        public_url="https://capitalchronicle.substack.com/p/a-safe-slug",
        reconciliation="RECONCILED_CONFIRMED",
    )
    unsafe = _seed_dispatch(
        store, suffix="unsafe-url", status="DISPATCH_CONFIRMED", object_id="public-unsafe",
        public_url="https://capitalchronicle.substack.com/p/unsafe?session=do-not-expose",
        reconciliation="RECONCILED_CONFIRMED",
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert _publication(snapshot, safe)["canonical_public_url"] == (
        "https://capitalchronicle.substack.com/p/a-safe-slug"
    )
    assert _publication(snapshot, unsafe)["canonical_public_url"] is None
    encoded = json.dumps(snapshot)
    assert "session=do-not-expose" not in encoded


def test_confirmed_dispatch_without_readback_is_counted_for_recovery(tmp_path):
    store = _store(tmp_path)
    pending = _seed_dispatch(
        store, suffix="no-readback", status="DISPATCH_CONFIRMED", object_id="public-pending"
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert _publication(snapshot, pending)["lifecycle_classification"] == "CONFIRMED_DISPATCH_PENDING_READBACK"
    assert snapshot["published"]["pending_readback_count"] == 1
    assert any(item["kind"] == "LIFECYCLE_RECOVERY" for item in snapshot["queue"]["items"])


def test_no_publication_and_platform_unavailable_are_truthful(tmp_path):
    store = _store(tmp_path)
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert snapshot["published"]["empty_reason"] == "NO_REAL_PUBLICATIONS_YET"
    assert snapshot["published"]["real_publication_count"] == 0
    assert {row["readiness"] for row in snapshot["platforms"]["destinations"]} == {
        "READINESS_NOT_PROBED",
    }
    assert not any(row["write_eligible"] for row in snapshot["platforms"]["destinations"])


def test_due_observation_preserves_unavailable_metric_not_zero(tmp_path):
    store = _store(tmp_path)
    dispatch = _seed_dispatch(
        store, suffix="metric", status="DISPATCH_CONFIRMED", object_id="public-metric",
        reconciliation="RECONCILED_CONFIRMED",
    )
    with store.get_connection() as conn:
        conn.execute(
            "INSERT INTO performance_observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "obs_due", "contentops.performance_observation.v1", dispatch, "work_metric",
                "substack", "public-metric", None, "EARLY", "2026-08-10T11:00:00Z",
                None, "collector.v1", "SCHEDULED", "{}",
                json.dumps({"shares": "UNAVAILABLE"}), "canonical", "hash", 1,
            ),
        )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    observation = snapshot["performance"]["observations"][0]
    assert observation["metric_availability"]["shares"] == "UNAVAILABLE"
    assert "shares" not in observation["native_metrics"]
    assert observation["qualified_engagement_score"] == "NO_SCORE"
    assert observation["qualified_engagement_formula_version"] == (
        "qualified_engagement.formula.v1"
    )
    assert snapshot["queue"]["due_performance_observation_count"] == 1


def test_observation_history_never_overwrites_current_collector_capability(tmp_path):
    store = _store(tmp_path)
    dispatch = _seed_dispatch(
        store, suffix="x-history", platform="x", status="DISPATCH_CONFIRMED",
        object_id="x-public-history", reconciliation="RECONCILED_CONFIRMED",
    )
    with store.get_connection() as conn:
        conn.execute(
            "INSERT INTO performance_observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                "obs_x_history", "contentops.performance_observation.v1", dispatch,
                "work_x-history", "x", "x-public-history", None, "DAILY",
                "2026-08-10T11:00:00Z", "2026-08-10T11:01:00Z", "collector.legacy",
                "COLLECTED", json.dumps({"likes": 4}),
                json.dumps({"likes": "AVAILABLE"}), "historical", "history-hash", 1,
            ),
        )

    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    platform = next(
        row for row in snapshot["platforms"]["destinations"]
        if row["platform_id"] == "x"
    )

    assert platform["observation_history_count"] == 1
    assert platform["observation_history"][0]["collection_status"] == "COLLECTED"
    assert platform["collector_capability"] == "NOT_EXPOSED_BY_CURRENT_AUTHORIZED_BINDING"
    assert platform["interaction_capability"] == "NOT_EXPOSED"
    assert platform["next_observation_at_utc"] is None


def test_learning_bootstrap_child_and_rollback_lineage(tmp_path):
    store = _store(tmp_path)
    rows = [
        ("bootstrap", None, "RETIRED", "HOLD_NO_POLICY_CHANGE", 0, 0.0, None),
        ("child", "bootstrap", "RETIRED", "ACCEPT_BOUNDED_UPDATE", 8, 0.9, "bootstrap"),
        ("rollback", "child", "ACTIVE", "ROLLBACK", 16, 0.95, "child"),
    ]
    with store.get_connection() as conn:
        for index, (version, parent, status, decision, sample, confidence, rollback) in enumerate(rows):
            payload = json.dumps({"timing_offset_minutes": index * 5})
            conn.execute(
                "INSERT INTO learning_policy_versions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (version, parent, f"2026-08-10T0{index}:00:00Z", status, decision, sample,
                 confidence, "formula.v1", "[]", "rolling", "{}", "{}", rollback,
                 "fixture lineage", payload, f"hash-{index}"),
            )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert snapshot["learning"]["active_policy"]["policy_version"] == "rollback"
    assert snapshot["learning"]["active_policy"]["parent_policy_version"] == "child"
    assert snapshot["learning"]["active_policy"]["rollback_reference"] == "child"
    bootstrap = next(row for row in snapshot["learning"]["policy_history"] if row["policy_version"] == "bootstrap")
    child = next(row for row in snapshot["learning"]["policy_history"] if row["policy_version"] == "child")
    assert bootstrap["provenance"] == "CONFIGURED_DEFAULT"
    assert child["provenance"] == "LEARNED"
    assert snapshot["learning"]["active_policy"]["provenance"] == "LEARNED"
    assert snapshot["runtime"]["next_editorial_window"]["provenance"] == "LEARNED_ACTIVE_POLICY"


def test_active_bootstrap_policy_remains_configured_default_everywhere(tmp_path):
    store = _store(tmp_path)
    _seed_policy(
        store,
        version="policy.bootstrap.v1",
        decision="BOOTSTRAP",
        sample_count=0,
        confidence=0.0,
        payload={
            "timing": {"offset_minutes": 0},
            "provenance": "CONFIGURED_DEFAULT",
        },
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    active = snapshot["learning"]["active_policy"]
    assert active["status"] == "ACTIVE"
    assert active["sample_count"] == 0
    assert active["confidence"] == 0.0
    assert active["provenance"] == "CONFIGURED_DEFAULT"
    assert {row["provenance"] for row in snapshot["queue"]["upcoming_editorial_windows"]} == {
        "CONFIGURED_DEFAULT"
    }
    assert {row["state"] for row in snapshot["queue"]["items"]} == {"CONFIGURED_DEFAULT"}
    assert snapshot["runtime"]["next_editorial_window"]["provenance"] == "CONFIGURED_DEFAULT"


def test_active_status_and_sample_count_cannot_create_learned_lineage(tmp_path):
    store = _store(tmp_path)
    _seed_policy(
        store,
        version="policy.configured.v2",
        status="ACTIVE",
        decision="HOLD_NO_POLICY_CHANGE",
        sample_count=99,
        confidence=0.99,
        payload={"timing": {"offset_minutes": 0}},
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    assert snapshot["learning"]["active_policy"]["provenance"] == "CONFIGURED_DEFAULT"
    assert snapshot["runtime"]["next_editorial_window"]["provenance"] == "CONFIGURED_DEFAULT"


def test_genuine_learned_child_controls_window_provenance_and_nested_offset(tmp_path):
    store = _store(tmp_path)
    _seed_policy(
        store,
        version="policy.bootstrap.v1",
        status="SUPERSEDED",
        payload={"timing": {"offset_minutes": 0}, "provenance": "CONFIGURED_DEFAULT"},
    )
    _seed_policy(
        store,
        version="policy.learned.v2",
        parent="policy.bootstrap.v1",
        decision="ACCEPT_BOUNDED_UPDATE",
        sample_count=8,
        confidence=0.9,
        payload={"timing": {"offset_minutes": 15}, "provenance": "LEARNED_BOUNDED_UPDATE"},
        created_at="2026-08-10T02:00:00Z",
    )
    snapshot = build_daily_app_snapshot(store.db_path, now=NOW)
    active = snapshot["learning"]["active_policy"]
    assert active["provenance"] == "LEARNED"
    assert active["timing_offset_minutes"] == 15
    assert snapshot["runtime"]["next_editorial_window"]["provenance"] == "LEARNED_ACTIVE_POLICY"
    assert snapshot["runtime"]["next_editorial_window"]["window_start_utc"] == "2026-08-10T14:00:00Z"


def test_kill_switch_cas_restart_and_zero_calls(tmp_path):
    store = _store(tmp_path)
    initial = store.get_operating_control()
    updated = update_daily_app_mode(
        store.db_path, expected_state_version=initial["state_version"], operating_mode="KILL_SWITCH"
    )
    assert updated["operating_mode"] == "KILL_SWITCH"
    with pytest.raises(OperatingModeConflictError):
        update_daily_app_mode(store.db_path, expected_state_version=initial["state_version"], operating_mode="SHADOW_ONLY")
    with pytest.raises(ValueError):
        update_daily_app_mode(store.db_path, expected_state_version=updated["state_version"], operating_mode="UNSAFE")

    calls = {"newsroom": 0, "publisher": 0}
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=store.db_path, output_root=tmp_path / "output", store=store,
        newsroom_cycle=lambda **_: calls.__setitem__("newsroom", calls["newsroom"] + 1),
        publication_publisher=lambda *_: calls.__setitem__("publisher", calls["publisher"] + 1),
    )
    assert supervisor.operating_mode == "KILL_SWITCH"
    result = supervisor.drive_canonical_publication_lifecycle("not-created", ["substack"], "pkg")
    assert result["kill_switch_blocked"] is True
    assert calls == {"newsroom": 0, "publisher": 0}


def test_malformed_store_fails_closed(tmp_path):
    malformed = tmp_path / "malformed.sqlite3"
    malformed.touch()
    with pytest.raises(DailyAppReadModelError):
        build_daily_app_snapshot(malformed, now=NOW)


def test_snapshot_and_mode_api_are_bounded_and_launcher_stays_quarantined(tmp_path):
    store = _store(tmp_path)
    before = _lifecycle_counts(store)
    server = HTTPServer(("127.0.0.1", 0), make_handler(store.db_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(f"{root}/api/daily-app/snapshot") as response:
            assert response.status == 200
            assert json.load(response)["authority"]["fixture_fallback"] is False
        request = Request(f"{root}/api/run-pipeline", method="POST")
        with pytest.raises(HTTPError) as blocked:
            urlopen(request)
        assert blocked.value.code == 423
        malformed = Request(
            f"{root}/api/daily-app/control/mode", method="POST", data=b'{"operating_mode":"KILL_SWITCH"}',
            headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:5173"},
        )
        with pytest.raises(HTTPError) as bad:
            urlopen(malformed)
        assert bad.value.code == 400
        valid = Request(
            f"{root}/api/daily-app/control/mode", method="POST",
            data=json.dumps({"operating_mode": "SHADOW_ONLY", "expected_state_version": 1}).encode(),
            headers={"Content-Type": "application/json", "Origin": "http://127.0.0.1:5173"},
        )
        with urlopen(valid) as changed:
            assert changed.status == 200
            assert json.load(changed)["control"]["operating_mode"] == "SHADOW_ONLY"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    after = _lifecycle_counts(store)
    assert server.server_address[0] == "127.0.0.1"
    assert before == after
    assert store.get_operating_control()["operating_mode"] == "SHADOW_ONLY"


def test_snapshot_keyspace_contains_no_secret_shapes(tmp_path):
    snapshot = build_daily_app_snapshot(_store(tmp_path).db_path, now=NOW)
    encoded = json.dumps(snapshot).lower()
    for forbidden in ('"token"', '"password"', '"cookie"', '"authorization"', 'private_key'):
        assert forbidden not in encoded
