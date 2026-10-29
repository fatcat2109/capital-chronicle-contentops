"""App-binding fixtures, not natural-window or publication evidence."""
# ruff: noqa: F811
import json
from datetime import datetime
from pathlib import Path

import pytest

import live_contentops.native_desktop_schedule_binding_v1 as schedule
from live_contentops.native_brief_windows_v1 import BRIEF_WINDOWS, native_opportunities, record_quota_stop
from live_contentops.daily_app_supervisor_v1 import build_bootstrap_editorial_window_policy, owner_locked_editorial_opportunities
from live_contentops.native_newsroom_volume_v1 import window_progress
from live_contentops.codex_desktop_newsroom_operator_v1 import four_task_setup_packet, volume_task_setup_packet
from test_native_scheduled_continuity_v1 import rollout, terminal_abstention  # noqa: F401,F811 - pytest fixture


def at(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_tonight_full_window_identities_and_prompts_are_preserved():
    policy = build_bootstrap_editorial_window_policy()
    args = {"reference_utc":"2026-10-29T00:00:00Z", "through_utc":"2026-10-29T18:59:59Z"}
    assert native_opportunities(policy, **args) == owner_locked_editorial_opportunities(policy, **args)
    existing = four_task_setup_packet()
    future = volume_task_setup_packet()
    assert len(existing["tasks"]) == 4 and len(future["tasks"]) == 7
    for original, revised in zip(existing["tasks"], future["tasks"]):
        assert original["id"] == revised["id"] and original["rrule"] == revised["rrule"]
    assert all(t["status"] == "PAUSED" for t in future["tasks"][4:])


def test_revised_brief_binds_once_and_cannot_run_before_effective_day(rollout):
    auto = next(iter(BRIEF_WINDOWS))
    early = schedule.scheduled_binding(rollout, auto, now=at("2026-10-29T02:00:00Z"))
    assert early["classification"] == "OUTSIDE_EXACT_NATIVE_WINDOW"
    current = schedule.scheduled_binding(rollout, auto, now=at("2026-10-30T02:00:00Z"))
    binding = json.loads(Path(current["binding_path"]).read_bytes())
    assert binding["volume_policy"]["brief_only"] and binding["volume_policy"]["max_articles"] == 1
    again = schedule.scheduled_binding(rollout, auto, now=at("2026-10-30T02:00:00Z"))
    assert again["binding_path"] == current["binding_path"]


def test_full_revised_window_has_two_article_ceiling_and_shared_budget_binding(rollout, monkeypatch):
    auto = "v1-newsroom-london-1700"
    first = schedule.scheduled_binding(rollout, auto, now=at("2026-10-30T10:00:00Z"))
    binding = json.loads(Path(first["binding_path"]).read_bytes())
    assert first["capacity"] == 6 and binding["volume_policy"]["max_articles"] == 2
    terminal_abstention(rollout, binding)
    original_progress = window_progress
    def complete_progress(store, issued):
        value = original_progress(store, issued)
        if issued:
            value.update(published_article_count=2)
        return value
    monkeypatch.setattr(schedule, "window_progress", complete_progress)
    result = schedule.scheduled_binding(rollout, auto, now=at("2026-10-30T10:10:00Z"), continue_after=first["run_id"])
    assert result["classification"] == "NATIVE_WINDOW_COMPLETE"
    assert len(list(Path(rollout["editorial_output_root"]).glob("**/native_operation_binding.json"))) == 1


def test_observed_quota_cuts_only_added_briefs(rollout):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    # A controlled existing observation is saved in an isolated store; no live quota claim.
    store = ContentOpsDurableStore(rollout["store_path"])
    work = "cc-opportunity-" + sha256_of("quota-controlled")
    store.create_work_item(work_item_id=work, story_id=work, title="Controlled quota", target_surface="TEST")
    # Use a past production-day observation and test that day's guard directly.
    record_quota_stop(store, {"run_id":"quota-controlled"}, {"cause":"CODEX_QUOTA_STOP", "lane":"CONTENTOPS_BUILDER",
        "observed_at_utc":"2026-10-29T03:00:00+00:00", "source_identity":"CONTROLLED_TEST_NOT_LIVE_QUOTA",
        "observation_source":"CONTROLLED_FIXTURE"})
    from live_contentops.native_brief_windows_v1 import observed_quota_stop
    assert observed_quota_stop(store, cutoff_utc="2026-10-29T08:00:00Z")
    assert observed_quota_stop(store, cutoff_utc="2026-10-30T08:00:00Z") is None
    assert len(four_task_setup_packet()["tasks"]) == 4


def test_quota_stop_compares_instants_and_rejects_missing_timezones(rollout):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.native_brief_windows_v1 import observed_quota_stop
    store = ContentOpsDurableStore(rollout["store_path"])
    work = "cc-opportunity-" + sha256_of("quota-offset-controlled")
    store.create_work_item(work_item_id=work, story_id=work, title="Controlled offset", target_surface="TEST")
    observation = {"cause": "CODEX_QUOTA_STOP", "lane": "CONTENTOPS_BUILDER",
        "observed_at_utc": "2026-10-29T03:00:00+07:00", "source_identity": "CONTROLLED_TEST_NOT_LIVE_QUOTA",
        "observation_source": "CONTROLLED_FIXTURE"}
    record_quota_stop(store, {"run_id": "quota-offset-controlled"}, observation)
    assert observed_quota_stop(store, cutoff_utc="2026-10-28T20:00:00Z")["source_identity"] == observation["source_identity"]
    assert observed_quota_stop(store, cutoff_utc="2026-10-28T19:59:59Z") is None
    with pytest.raises(ValueError, match="UTC_OFFSET_REQUIRED"):
        record_quota_stop(store, {"run_id": "quota-offset-controlled"},
            {**observation, "observed_at_utc": "2026-10-29T03:00:00"})
    with pytest.raises(ValueError, match="FUTURE_QUOTA"):
        record_quota_stop(store, {"run_id": "quota-offset-controlled"},
            {**observation, "observed_at_utc": "2099-01-01T00:00:00Z"})
