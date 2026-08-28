from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from live_contentops import v1_simple_gemini_scheduler_v1 as scheduler_module
from live_contentops.daily_app_supervisor_v1 import (
    build_bootstrap_editorial_window_policy,
)
from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)
from live_contentops.newsroom_production_day_v1 import (
    build_current_zero_write_qualified_article_record,
    load_qualified_article_records,
    newsroom_production_day_id,
    persist_qualified_article_record,
)
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    MAX_LOGICAL_MODEL_INVOCATIONS,
    MAX_REVISION_ROUNDS,
    MAX_SELECTION_CANDIDATES,
    MAX_SOURCE_REQUESTS,
)
from live_contentops.v1_simple_gemini_scheduler_v1 import (
    SimpleGeminiLocalScheduler,
    SimpleGeminiSchedulerCheckpointError,
    SimpleGeminiSchedulerSafetyError,
    _NonBlockingFileLock,
    simple_gemini_slot_id,
)


def _memory_loader(calls: list[dict] | None = None):
    def load():
        if calls is not None:
            calls.append({"loaded": True})
        return [], {
            "schema_version": "contentops.v1_simple_published_memory_access.v1",
            "canonical_reconciled_article_count": 0,
            "store_access_mode": "SQLITE_MODE_RO_QUERY_ONLY",
            "auto_migrate": False,
            "production_store_unchanged_during_projection": True,
            "second_publication_store_created": False,
        }

    return load


def _intents(article_identity: str) -> list[dict]:
    return [
        {
            "destination": str(destination),
            "dispatch_state": "UNDISPATCHED",
            "article_identity": article_identity,
        }
        for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
    ]


def _persist_qualified(
    output_dir: Path,
    *,
    cutoff_utc: str,
    run_id: str,
    story_identity: str,
) -> dict:
    article = {
        "title": f"Qualified {story_identity}",
        "substack_body_markdown": f"Body for {story_identity}",
    }
    record = build_current_zero_write_qualified_article_record(
        production_day_id=newsroom_production_day_id(cutoff_utc),
        parent_window_id=run_id,
        attempt_run_id=run_id,
        article=article,
        story_identity=story_identity,
        update_chain_identity=story_identity,
        resolved_article_mode="BREAKING_BRIEF",
        accepted_evidence_documents=[
            {
                "document_id": f"doc-{story_identity}",
                "source_url": f"https://example.com/{story_identity}",
                "canonical_content_sha256": "a" * 64,
                "published_at_utc": cutoff_utc,
                "published_at_source": "CONTROLLED",
            }
        ],
        editorial_provider="9router",
        editorial_model="vx/gemini-3.5-flash(high)",
        editorial_reasoning_effort="HIGH",
        logical_model_invocation_count=2,
        derivative_package_intents=_intents(story_identity),
    )
    persist_qualified_article_record(output_dir, record)
    return record


def _controlled_operation(calls: list[dict], outcomes: list[str] | None = None):
    planned = list(outcomes or [])

    def run(**kwargs):
        call_number = len(calls) + 1
        memory_ids = [
            str(
                getattr(row, "story_identity", "")
                or getattr(row, "article_identity", "")
            )
            for row in kwargs["published_memory"]
        ]
        calls.append({**kwargs, "published_memory_ids": memory_ids})
        outcome = planned[call_number - 1] if call_number <= len(planned) else "PASS"
        if outcome == "PASS":
            story_identity = f"story-{call_number}"
            record = _persist_qualified(
                Path(kwargs["output_dir"]),
                cutoff_utc=kwargs["cutoff_utc"],
                run_id=kwargs["run_id"],
                story_identity=story_identity,
            )
            return {
                "classification": "PASS_V1_SIMPLE_GEMINI_ZERO_WRITE_ARTICLE",
                "candidate_count": 32,
                "candidate_limit": 32,
                "source_request_count": 2,
                "source_request_limit": 6,
                "logical_model_invocation_count": 2,
                "logical_model_invocation_limit": 3,
                "provider_attempt_count": 2,
                "revision_performed": False,
                "qualified_article_count": 1,
                "article_identity": record["article_identity"],
                "codex_runtime_model_call_count": 0,
                "public_write_performed": False,
                "provider_publication_writes": 0,
                "unknown_write_count": 0,
            }
        if outcome == "UNSAFE":
            return {
                "classification": "BLOCKED",
                "candidate_limit": 32,
                "logical_model_invocation_count": 1,
                "codex_runtime_model_call_count": 0,
                "public_write_performed": True,
                "provider_publication_writes": 1,
                "unknown_write_count": 1,
            }
        return {
            "classification": "NO_PUBLICATION",
            "exact_next_blocker": "CONTROLLED_ABSTENTION",
            "candidate_count": 32,
            "candidate_limit": 32,
            "source_request_count": 1,
            "logical_model_invocation_count": 1,
            "provider_attempt_count": 1,
            "qualified_article_count": 0,
            "codex_runtime_model_call_count": 0,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
        }

    return run


def _scheduler(tmp_path: Path, calls: list[dict], outcomes: list[str] | None = None):
    memory_calls: list[dict] = []
    return (
        SimpleGeminiLocalScheduler(
            scheduler_root=tmp_path,
            simple_operation=_controlled_operation(calls, outcomes),
            published_memory_loader=_memory_loader(memory_calls),
        ),
        memory_calls,
    )


def test_exact_four_window_calendar_cross_midnight_identity_and_stable_slot_ids():
    policy = build_bootstrap_editorial_window_policy(
        effective_at_utc="2026-08-28T00:00:00Z"
    )
    assert [
        (row.start_hour_utc, row.end_hour_utc, row.session)
        for row in policy.core_windows
    ] == [
        (10, 11, "london_1700_bangkok"),
        (14, 15, "new_york_2100_bangkok"),
        (16, 17, "new_york_2300_bangkok"),
        (18, 19, "new_york_0100_bangkok"),
    ]
    day_id = newsroom_production_day_id("2026-08-28T18:00:00Z")
    assert day_id == "newsroom-production-day-2026-08-28-bangkok"
    first = simple_gemini_slot_id(
        production_day_id=day_id,
        window_id="window-1",
        slot_ordinal=1,
    )
    assert first == simple_gemini_slot_id(
        production_day_id=day_id,
        window_id="window-1",
        slot_ordinal=1,
    )
    assert first != simple_gemini_slot_id(
        production_day_id=day_id,
        window_id="window-1",
        slot_ordinal=2,
    )


def test_idle_tick_performs_zero_memory_model_provider_or_source_work(tmp_path):
    calls: list[dict] = []
    scheduler, memory_calls = _scheduler(tmp_path, calls)
    result = scheduler.tick(now="2026-08-30T04:30:00Z")
    assert result["classification"] == "IDLE_NOT_DUE"
    assert result["exactly_one_routine_editorial_owner"] is True
    assert result["routine_editorial_owner"] == "SIMPLE_GEMINI_RUNTIME"
    assert result["due_window_count"] == 0
    assert result["simple_operation_invocation_count"] == 0
    assert result["published_memory_refresh_count"] == 0
    assert result["gemini_logical_call_count"] == 0
    assert result["source_get_count"] == 0
    assert result["codex_runtime_model_call_count"] == 0
    assert result["native_desktop_routine_invocation_count"] == 0
    assert result["legacy_rolling_x_routine_invocation_count"] == 0
    assert result["public_write_performed"] is False
    assert result["provider_publication_writes"] == 0
    assert result["publication_coordinator_dispatched"] is False
    assert result["unknown_write_count"] == 0
    assert calls == []
    assert memory_calls == []


def test_due_window_runs_independent_slots_and_refreshes_memory_after_pass(tmp_path):
    calls: list[dict] = []
    scheduler, memory_calls = _scheduler(tmp_path, calls)
    result = scheduler.tick(now="2026-08-28T10:00:00Z")
    assert result["session"] == "london_1700_bangkok"
    assert result["slot_capacity"] == 2
    assert result["slot_terminal_count"] == 2
    assert result["simple_operation_invocation_count"] == 2
    assert result["published_memory_refresh_count"] == 2
    assert len(memory_calls) == 2
    assert calls[0]["published_memory_ids"] == []
    assert calls[1]["published_memory_ids"] == ["story-1"]
    assert len({call["run_id"] for call in calls}) == 2
    assert result["gemini_logical_call_count"] == 4
    assert result["source_get_count"] == 4
    assert result["codex_runtime_model_call_count"] == 0
    assert result["public_write_performed"] is False
    assert result["provider_publication_writes"] == 0
    assert result["unknown_write_count"] == 0
    assert all(slot["state"] == "QUALIFIED" for slot in result["slots"])


def test_duplicate_tick_and_process_restart_suppress_all_semantic_work(tmp_path):
    calls: list[dict] = []
    scheduler, _ = _scheduler(tmp_path, calls)
    first = scheduler.tick(now="2026-08-28T10:00:00Z")
    assert first["simple_operation_invocation_count"] == 2

    duplicate = scheduler.tick(now="2026-08-28T10:00:00Z")
    assert duplicate["classification"] == "WINDOW_ALREADY_TERMINAL"
    assert duplicate["simple_operation_invocation_count"] == 0
    assert duplicate["published_memory_refresh_count"] == 0
    assert len(calls) == 2

    def forbidden_loader():
        raise AssertionError("published memory must not reload for a terminal window")

    restarted = SimpleGeminiLocalScheduler(
        scheduler_root=tmp_path,
        simple_operation=lambda **_kwargs: pytest.fail(
            "Simple operation reinvoked after restart"
        ),
        published_memory_loader=forbidden_loader,
    )
    after_restart = restarted.tick(now="2026-08-28T10:00:00Z")
    assert after_restart["classification"] == "WINDOW_ALREADY_TERMINAL"
    assert after_restart["simple_operation_invocation_count"] == 0
    assert after_restart["source_get_count"] == 0
    assert after_restart["gemini_logical_call_count"] == 0


def test_abstained_slots_terminalize_without_false_qualification(tmp_path):
    calls: list[dict] = []
    scheduler, _ = _scheduler(tmp_path, calls, ["ABSTAIN", "ABSTAIN"])
    result = scheduler.tick(now="2026-08-28T10:00:00Z")
    day_id = newsroom_production_day_id("2026-08-28T10:00:00Z")
    assert result["classification"] == "TERMINAL_NO_PUBLICATION"
    assert [slot["state"] for slot in result["slots"]] == ["ABSTAINED", "ABSTAINED"]
    assert load_qualified_article_records(tmp_path, production_day_id=day_id) == []


def test_later_window_allocates_bounded_extra_slots_to_keep_five_reachable(tmp_path):
    day_id = newsroom_production_day_id("2026-08-28T16:00:00Z")
    _persist_qualified(
        tmp_path / "seed" / "one",
        cutoff_utc="2026-08-28T10:00:00Z",
        run_id="seed-one",
        story_identity="seed-story",
    )
    calls: list[dict] = []
    scheduler, _ = _scheduler(tmp_path, calls)
    result = scheduler.tick(now="2026-08-28T16:00:01Z")
    assert result["newsroom_production_day_id"] == day_id
    assert result["session"] == "new_york_2300_bangkok"
    assert result["slot_capacity"] == 3
    assert result["simple_operation_invocation_count"] == 3
    assert len(load_qualified_article_records(tmp_path, production_day_id=day_id)) == 4


def test_following_0100_window_uses_prior_production_day(tmp_path):
    calls: list[dict] = []
    scheduler, _ = _scheduler(tmp_path, calls, ["ABSTAIN"] * 5)
    result = scheduler.tick(now="2026-08-28T18:00:00Z")
    assert result["session"] == "new_york_0100_bangkok"
    assert result["newsroom_production_day_id"] == (
        "newsroom-production-day-2026-08-28-bangkok"
    )
    assert all(
        slot["slot_id"].startswith("simple-gemini-slot-") for slot in result["slots"]
    )


def test_following_0100_late_grace_clamps_cutoff_inside_prior_production_day(tmp_path):
    calls: list[dict] = []
    scheduler, _ = _scheduler(tmp_path, calls, ["PASS"] * 5)
    result = scheduler.tick(now="2026-08-28T19:30:00Z")
    expected = "newsroom-production-day-2026-08-28-bangkok"
    assert result["newsroom_production_day_id"] == expected
    assert {call["cutoff_utc"] for call in calls} == {"2026-08-28T18:59:59.999999Z"}
    assert (
        len(load_qualified_article_records(tmp_path, production_day_id=expected)) == 5
    )
    assert (
        load_qualified_article_records(
            tmp_path,
            production_day_id="newsroom-production-day-2026-08-29-bangkok",
        )
        == []
    )


def test_scheduler_preserves_simple_32_6_3_1_limits_and_fails_closed_on_write(tmp_path):
    assert (MAX_SELECTION_CANDIDATES, MAX_SOURCE_REQUESTS) == (32, 6)
    assert (MAX_LOGICAL_MODEL_INVOCATIONS, MAX_REVISION_ROUNDS) == (3, 1)
    calls: list[dict] = []
    scheduler, _ = _scheduler(tmp_path, calls, ["UNSAFE"])
    with pytest.raises(SimpleGeminiSchedulerSafetyError) as exc:
        scheduler.tick(now="2026-08-28T10:00:00Z")
    assert set(exc.value.blockers) == {
        "public_write_detected",
        "provider_publication_write_detected",
        "unknown_write_detected",
    }
    checkpoints = list(tmp_path.glob("**/slots/*.json"))
    assert len(checkpoints) == 1
    checkpoint = json.loads(checkpoints[0].read_text(encoding="utf-8"))
    assert checkpoint["state"] == "SAFETY_BLOCKED"
    assert checkpoint["terminal"] is True


def test_default_scheduler_route_calls_only_the_canonical_simple_operation(
    tmp_path, monkeypatch
):
    scheduler = SimpleGeminiLocalScheduler(
        scheduler_root=tmp_path,
        published_memory_loader=_memory_loader(),
    )
    operations: list[str] = []

    def execute(operation, **_kwargs):
        operations.append(operation)
        return {
            "classification": "NO_PUBLICATION",
            "exact_next_blocker": "CONTROLLED",
            "candidate_limit": 32,
            "codex_runtime_model_call_count": 0,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
        }

    monkeypatch.setattr(scheduler._orchestrator, "execute", execute)
    scheduler.tick(now="2026-08-28T10:00:00Z")
    assert operations == ["run_v1_simple_gemini_newsroom"] * 2


def test_invalid_existing_checkpoint_fails_closed_without_reexecution(tmp_path):
    calls: list[dict] = []
    scheduler, _ = _scheduler(tmp_path, calls)
    scheduler.tick(now="2026-08-28T10:00:00Z")
    window_path = next(tmp_path.glob("**/window_v1.json"))
    window_path.write_text("{}\n", encoding="utf-8")

    restarted_calls: list[dict] = []
    restarted, _ = _scheduler(tmp_path, restarted_calls)
    with pytest.raises(SimpleGeminiSchedulerCheckpointError):
        restarted.tick(now="2026-08-28T10:00:00Z")
    assert restarted_calls == []


def test_concurrent_process_lock_suppresses_duplicate_window_claim(tmp_path):
    calls: list[dict] = []
    scheduler, memory_calls = _scheduler(tmp_path, calls)
    due = scheduler._currently_due_windows(
        datetime.fromisoformat("2026-08-28T10:00:00+00:00")
    )[0]
    day_id = newsroom_production_day_id(due["start_utc"])
    window_path = scheduler._window_checkpoint_path(day_id, due["opportunity_id"])
    held = _NonBlockingFileLock(window_path.with_name("window.lock"))
    assert held.acquire() is True
    try:
        result = scheduler.tick(now="2026-08-28T10:00:00Z")
    finally:
        held.release()
    assert result["classification"] == "WINDOW_ACTIVE_OTHER_PROCESS"
    assert result["simple_operation_invocation_count"] == 0
    assert result["published_memory_refresh_count"] == 0
    assert calls == []
    assert memory_calls == []


def test_acquired_window_lock_releases_unconditionally_when_checkpoint_load_raises(
    tmp_path, monkeypatch
):
    calls: list[dict] = []
    scheduler, _ = _scheduler(tmp_path, calls)
    moment = datetime.fromisoformat("2026-08-28T10:00:00+00:00")
    due = scheduler._currently_due_windows(moment)[0]
    day_id = newsroom_production_day_id(due["start_utc"])
    window_path = scheduler._window_checkpoint_path(day_id, due["opportunity_id"])

    def injected_failure(*_args, **_kwargs):
        raise SimpleGeminiSchedulerCheckpointError("injected_checkpoint_failure")

    monkeypatch.setattr(scheduler_module, "_load_checkpoint", injected_failure)
    with pytest.raises(
        SimpleGeminiSchedulerCheckpointError, match="injected_checkpoint_failure"
    ):
        scheduler.tick(now=moment)

    reacquired = _NonBlockingFileLock(window_path.with_name("window.lock"))
    assert reacquired.acquire() is True
    reacquired.release()
    assert calls == []


def test_run_forever_idle_polling_and_max_ticks_are_deterministic(tmp_path):
    calls: list[dict] = []
    scheduler, memory_calls = _scheduler(tmp_path, calls)
    scheduler._clock = lambda: datetime.fromisoformat("2026-08-30T04:30:00+00:00")
    reports: list[dict] = []
    ticks = scheduler.run_forever(
        poll_seconds=0.001,
        max_ticks=3,
        on_tick=lambda value: reports.append(dict(value)),
    )
    assert ticks == 3
    assert [row["classification"] for row in reports] == ["IDLE_NOT_DUE"] * 3
    assert all(row["gemini_logical_call_count"] == 0 for row in reports)
    assert all(row["source_get_count"] == 0 for row in reports)
    assert calls == []
    assert memory_calls == []


def test_run_forever_terminal_window_stays_cheap_and_idempotent(tmp_path):
    calls: list[dict] = []
    scheduler, memory_calls = _scheduler(tmp_path, calls, ["ABSTAIN", "ABSTAIN"])
    fixed = datetime.fromisoformat("2026-08-28T10:00:00+00:00")
    scheduler.tick(now=fixed)
    assert len(calls) == 2
    assert len(memory_calls) == 2
    scheduler._clock = lambda: fixed
    reports: list[dict] = []
    ticks = scheduler.run_forever(
        poll_seconds=0.001,
        max_ticks=2,
        on_tick=lambda value: reports.append(dict(value)),
    )
    assert ticks == 2
    assert [row["classification"] for row in reports] == [
        "WINDOW_ALREADY_TERMINAL",
        "WINDOW_ALREADY_TERMINAL",
    ]
    assert all(row["simple_operation_invocation_count"] == 0 for row in reports)
    assert len(calls) == 2
    assert len(memory_calls) == 2


def test_run_forever_checkpoint_error_propagates_without_blind_retry(tmp_path):
    calls: list[dict] = []
    scheduler, _ = _scheduler(tmp_path, calls)
    fixed = datetime.fromisoformat("2026-08-28T10:00:00+00:00")
    scheduler.tick(now=fixed)
    window_path = next(tmp_path.glob("**/window_v1.json"))
    window_path.write_text("{}\n", encoding="utf-8")
    scheduler._clock = lambda: fixed
    with pytest.raises(SimpleGeminiSchedulerCheckpointError):
        scheduler.run_forever(poll_seconds=0.001, max_ticks=3)
    assert len(calls) == 2


def test_run_forever_safety_error_propagates_without_semantic_retry(tmp_path):
    calls: list[dict] = []
    scheduler, _ = _scheduler(tmp_path, calls, ["UNSAFE"])
    scheduler._clock = lambda: datetime.fromisoformat("2026-08-28T10:00:00+00:00")
    with pytest.raises(SimpleGeminiSchedulerSafetyError):
        scheduler.run_forever(poll_seconds=0.001, max_ticks=3)
    assert len(calls) == 1


def test_scheduler_source_contains_no_codex_automation_or_publication_dispatch_route():
    source = Path("live_contentops/v1_simple_gemini_scheduler_v1.py").read_text(
        encoding="utf-8"
    )
    assert "codex_desktop_newsroom_operator_v1" not in source
    assert "DurablePublicationCoordinator" not in source
    assert "scheduler_v6" not in source
    assert "fast_one_cycle" not in source
