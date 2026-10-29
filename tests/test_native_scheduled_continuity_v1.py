"""Disposable native schedule controls, never actual model or publication evidence."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import live_contentops.native_desktop_schedule_binding_v1 as schedule
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore, LeaseConflictError
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, DesktopInputRequired

AUTO = "v1-newsroom-new-york-2100"


def at(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


@pytest.fixture
def rollout(tmp_path, monkeypatch):
    monkeypatch.setattr(schedule, "llm_operator_pause_active", lambda: False)
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.llm_operator_pause_active", lambda *_: False)
    monkeypatch.setattr(schedule, "load_canonical_published_memory_read_only", lambda **_: ([], {}))
    return {"schema_version": schedule.SCHEMA, "store_path": str(tmp_path / "state.sqlite3"),
            "published_output_root": str(tmp_path / "published"), "editorial_output_root": str(tmp_path / "out"),
            "feed_pointer_path": str(tmp_path / "feed.json"), "public_write_authority": False}


def start(rollout, when="2026-10-26T14:05:00Z"):
    reply = schedule.scheduled_binding(rollout, AUTO, now=at(when))
    path = Path(reply["binding_path"])
    return reply, json.loads(path.read_bytes()), path


def terminal_abstention(rollout, binding):
    store = ContentOpsDurableStore(Path(rollout["store_path"]))
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled abstention", target_surface="TEST")
    store.register_outbox_message(message_id="cc-editorial-final-" + sha256_of(binding["run_id"]),
        work_item_id=work, destination="internal:cc-report-simple-result", status="EDITORIAL_INTERNAL",
        payload=canonical_bytes({"qualified_article_count": 0, "classification": "CONTROLLED_SOURCE_ABSTENTION",
            "candidate_attempt_history": [{"candidate_id": "controlled-blocked", "status": "SOURCE_BLOCKED"}]}).decode())
    return store


@pytest.mark.parametrize("when", ["2026-10-26T14:00:00Z", "2026-10-26T15:59:00Z", "2026-10-26T16:00:00Z"])
def test_eligible_start_and_existing_one_hour_grace_keep_nominal_cutoff(rollout, when):
    reply, binding, path = start(rollout, when)
    assert reply["classification"] == "NATIVE_WINDOW_SLOT_READY"
    assert reply["resumed_existing_binding"] is False
    assert binding["cutoff_utc"] == "2026-10-26T14:00:00Z"
    assert binding["owner_manual_validation"] is False
    again = schedule.scheduled_binding(rollout, AUTO, now=at(when))
    assert again["binding_path"] == str(path) and again["slot_ordinal"] == 1
    assert len(list(Path(rollout["editorial_output_root"]).glob("**/native_operation_binding.json"))) == 1


def test_interrupted_pending_native_request_is_discovered_after_expiry_without_new_source_work(rollout, monkeypatch):
    _, binding, path = start(rollout)
    store = ContentOpsDurableStore(Path(rollout["store_path"]))
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled pending", target_surface="TEST")
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"])
    args = dict(logical_invocation_id=binding["run_id"] + ":select", prompt="Controlled pending request",
                governed_input={"controlled_source_cutoff": binding["cutoff_utc"]},
                validator=lambda raw: (True, None, json.loads(raw), None))
    with pytest.raises(DesktopInputRequired) as original:
        turn(**args)
    request_path = Path(binding["output_dir"]) / "desktop_request_select.json"
    before_binding, before_request = path.read_bytes(), request_path.read_bytes()
    before_rows = len(store.list_outbox_messages())
    monkeypatch.setattr(schedule, "load_canonical_published_memory_read_only", lambda **_: pytest.fail("resume read new sources"))
    # A prompt-only rollout change cannot invalidate the frozen operation. Its
    # source/store/path/cutoff identity is still compared with the issued binding.
    changed_prompt = {**rollout, "tasks": [{"prompt": "New lean startup prose"}]}
    resumed = schedule.scheduled_binding(changed_prompt, AUTO, now=at("2026-10-27T06:00:00Z"))
    assert resumed["binding_path"] == str(path) and resumed["resumed_existing_binding"] is True
    assert resumed["model_invocations"] == resumed["source_requests"] == 0
    with pytest.raises(DesktopInputRequired) as pending:
        NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"])(**args)
    assert pending.value.request["request_sha256"] == original.value.request["request_sha256"]
    assert path.read_bytes() == before_binding and request_path.read_bytes() == before_request
    assert len(store.list_outbox_messages()) == before_rows


def test_completed_duplicate_callback_replays_without_another_slot_or_source_work(rollout, monkeypatch):
    _, binding, path = start(rollout)
    store = terminal_abstention(rollout, binding)
    before = len(store.list_outbox_messages())
    monkeypatch.setattr(schedule, "load_canonical_published_memory_read_only", lambda **_: pytest.fail("completed callback fetched sources"))
    for when in ("2026-10-26T14:06:00Z", "2026-10-27T06:00:00Z"):
        reply = schedule.scheduled_binding(rollout, AUTO, now=at(when))
        assert reply["classification"] == "NATIVE_WINDOW_OPERATION_COMPLETE"
        assert reply["binding_path"] == str(path) and reply["source_requests"] == reply["model_invocations"] == 0
    assert len(list(Path(rollout["editorial_output_root"]).glob("**/native_operation_binding.json"))) == 1
    assert len(store.list_outbox_messages()) == before


def test_deliberate_next_slot_is_bounded_idempotent_and_cannot_be_allocated_after_grace(rollout):
    _, binding, path = start(rollout)
    terminal_abstention(rollout, binding)
    next_slot = schedule.scheduled_binding(rollout, AUTO, now=at("2026-10-26T14:15:00Z"), continue_after=binding["run_id"])
    again = schedule.scheduled_binding(rollout, AUTO, now=at("2026-10-26T14:16:00Z"), continue_after=binding["run_id"])
    assert next_slot["slot_ordinal"] == 2 and next_slot["binding_path"] == again["binding_path"]
    second = json.loads(Path(next_slot["binding_path"]).read_bytes())
    assert second["attempted_candidate_ids"] == ["controlled-blocked"]
    terminal_abstention(rollout, second)
    expired = schedule.scheduled_binding(rollout, AUTO, now=at("2026-10-26T16:00:01Z"), continue_after=second["run_id"])
    assert expired["classification"] == "OUTSIDE_EXACT_NATIVE_WINDOW"
    assert len(list(path.parent.parent.glob("*/native_operation_binding.json"))) == 2


def test_expired_never_bound_0100_has_no_store_or_artifact_side_effect(rollout, tmp_path, monkeypatch):
    monkeypatch.setattr(schedule, "load_canonical_published_memory_read_only", lambda **_: pytest.fail("expired window fetched sources"))
    result = schedule.scheduled_binding(rollout, "v1-newsroom-new-york-0100", now=at("2026-10-26T20:31:49Z"))
    assert result["classification"] == "OUTSIDE_EXACT_NATIVE_WINDOW"
    assert "binding_path" not in result and result["public_write_performed"] is False
    assert result["next_calendar_opportunity"]["session"] == "new_york_0100_bangkok"
    assert result["next_calendar_opportunity"]["start_utc"] == "2026-10-27T18:00:00Z"
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("change", ["cutoff", "slot", "corrupt_json", "missing_registered", "feed", "output_root"])
def test_changed_or_corrupt_issued_binding_is_rejected_without_replacement(rollout, change):
    _, binding, path = start(rollout)
    store = ContentOpsDurableStore(Path(rollout["store_path"]))
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled identity", target_surface="TEST")
    store.register_outbox_message(message_id="native-operation-binding-" + sha256_of(binding["run_id"]),
        work_item_id=work, destination="internal:native-desktop-editorial", status="EDITORIAL_INTERNAL",
        payload=canonical_bytes(binding).decode())
    if change == "corrupt_json":
        path.write_bytes(b"{broken")
    elif change == "missing_registered":
        path.unlink()
    elif change in {"feed", "output_root"}:
        rollout["feed_pointer_path" if change == "feed" else "editorial_output_root"] += ".changed"
    else:
        binding["cutoff_utc" if change == "cutoff" else "slot_ordinal"] = "changed"
        path.write_bytes(canonical_bytes(binding))
    before = path.read_bytes() if path.exists() else None
    with pytest.raises(ValueError):
        schedule.scheduled_binding(rollout, AUTO, now=at("2026-10-27T06:00:00Z"))
    assert (path.read_bytes() if path.exists() else None) == before


def test_new_window_start_respects_existing_store_lease(rollout):
    from live_contentops.daily_app_supervisor_v1 import build_bootstrap_editorial_window_policy, owner_locked_editorial_opportunities
    now = at("2026-10-26T14:05:00Z")
    window = next(w for w in owner_locked_editorial_opportunities(build_bootstrap_editorial_window_policy(),
        reference_utc=now, through_utc=now) if w["session"] == "new_york_2100_bangkok")
    store = ContentOpsDurableStore(Path(rollout["store_path"]))
    lease = store.acquire_lease("internal:native-window:" + window["opportunity_id"], "controlled-other-callback", ttl_seconds=60)
    try:
        with pytest.raises(LeaseConflictError):
            schedule.scheduled_binding(rollout, AUTO, now=now)
        assert not list(Path(rollout["editorial_output_root"]).glob("**/native_operation_binding.json"))
    finally:
        store.release_lease(lease["lease_id"], "controlled-other-callback", lease["fencing_token"])


def test_completed_previous_day_does_not_suppress_next_legitimate_calendar_window(rollout):
    _, binding, _ = start(rollout)
    terminal_abstention(rollout, binding)
    new, next_binding, _ = start(rollout, "2026-10-27T14:05:00Z")
    assert new["resumed_existing_binding"] is False
    assert next_binding["run_id"] != binding["run_id"] and next_binding["slot_ordinal"] == 1
    assert next_binding["cutoff_utc"] == "2026-10-27T14:00:00Z"


def test_pending_previous_day_does_not_suppress_next_due_window_and_both_bindings_survive(rollout):
    _, old, old_path = start(rollout)
    before = old_path.read_bytes()
    new, binding, path = start(rollout, "2026-10-27T14:00:01Z")
    assert binding["cutoff_utc"] == "2026-10-27T14:00:00Z" and binding["run_id"] != old["run_id"]
    assert new["resumed_existing_binding"] is False and old_path.read_bytes() == before
    repeated = schedule.scheduled_binding(rollout, AUTO, now=at("2026-10-27T14:00:02Z"))
    assert repeated["binding_path"] == str(path) and repeated["resumed_existing_binding"] is True
    assert len(list(Path(rollout["editorial_output_root"]).glob("**/native_operation_binding.json"))) == 2


def test_2300_early_app_delivery_binds_nominal_identity_and_records_actual_clock(rollout):
    # Deterministic reproduction of the observed13-second-early callback; not a live run.
    moment = at("2026-10-27T15:59:46.891127Z")
    result = schedule.scheduled_binding(rollout, "v1-newsroom-new-york-2300", now=moment)
    binding = json.loads(Path(result["binding_path"]).read_bytes())
    assert binding["cutoff_utc"] == "2026-10-27T16:00:00Z"
    assert binding["input_known_at_cutoff_utc"] == moment.isoformat()
    store = ContentOpsDurableStore(Path(rollout["store_path"]), auto_migrate=False)
    checkpoint = schedule._latest_window(store, "new_york_2300_bangkok")
    assert checkpoint["actual_entry_utc"] == moment.isoformat()
    assert checkpoint["early_delivery_seconds"] == pytest.approx(13.108873)
    at_boundary = schedule.scheduled_binding(rollout, "v1-newsroom-new-york-2300", now=at("2026-10-27T16:00:00Z"))
    assert at_boundary["binding_path"] == result["binding_path"]


def test_delivery_before_bounded_jitter_does_not_manufacture_a_window(rollout, tmp_path):
    result = schedule.scheduled_binding(rollout, "v1-newsroom-new-york-2300", now=at("2026-10-27T15:54:59Z"))
    assert result["classification"] == "OUTSIDE_EXACT_NATIVE_WINDOW"
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("auto,old_time,early,nominal", [
    ("v1-newsroom-london-1700", "2026-10-27T10:00:00Z", "2026-10-29T09:56:57Z", "2026-10-29T10:00:00Z"),
    ("v1-newsroom-brief-us-1900", "2026-10-30T12:00:00Z", "2026-11-02T11:55:15Z", "2026-11-02T12:00:00Z"),
])
def test_observed_five_minute_early_callback_prefers_own_window_over_old_pending(rollout, auto, old_time, early, nominal):
    old = schedule.scheduled_binding(rollout, auto, now=at(old_time))
    old_path = Path(old["binding_path"])
    old_bytes = old_path.read_bytes()
    result = schedule.scheduled_binding(rollout, auto, now=at(early))
    binding = json.loads(Path(result["binding_path"]).read_bytes())
    assert result["resumed_existing_binding"] is False and result["run_id"] != old["run_id"]
    assert binding["cutoff_utc"] == nominal and binding["input_known_at_cutoff_utc"] == at(early).isoformat()
    assert result["actual_entry_utc"] == at(early).isoformat()
    assert old_path.read_bytes() == old_bytes
    again = schedule.scheduled_binding(rollout, auto, now=at(nominal))
    assert again["binding_path"] == result["binding_path"]
    assert json.loads(Path(again["binding_path"]).read_bytes()) == binding


def test_early_input_excludes_later_captures_even_when_publication_precedes_cutoff(tmp_path):
    from live_contentops.newsroom_assignment_scheduler_v1 import load_rolling_x_headline_sidecars
    path = tmp_path / "sidecar.jsonl"
    rows = [dict(headline_text="Controlled item " + str(i), tweet_id=str(i),
        headline_timestamp="2026-10-29T09:50:00Z", **clocks) for i, clocks in enumerate([
            {"captured_at_utc": "2026-10-29T09:55:00Z"},
            {"captured_at_utc": "2026-10-29T09:57:00Z"}, {},
            {"known_at_utc": "2026-10-29T09:58:00Z", "captured_at_utc": "2026-10-29T09:55:00Z"},
            {"known_at_utc": "2026-10-29T09:55:00Z", "captured_at_utc": "2026-10-29T09:58:00Z"},
            {"known_at_utc": "2026-10-29T09:55:00Z", "revision_at_utc": "2026-10-29T09:59:00Z"}])]
    path.write_text("\n".join(json.dumps(r) for r in rows))
    result = load_rolling_x_headline_sidecars(cutoff_utc="2026-10-29T09:56:57Z",
        known_at_cutoff_utc="2026-10-29T09:56:57Z", sidecar_glob=str(path))
    assert len(result["headlines"]) == 1
    assert result["rejection_counts"]["known_after_input_cutoff"] == 4
    assert result["rejection_counts"]["known_at_timestamp_unavailable"] == 1
    unchanged = load_rolling_x_headline_sidecars(cutoff_utc="2026-10-29T09:56:57Z", sidecar_glob=str(path))
    assert len(unchanged["headlines"]) == 6


def test_controlled_next_production_day_all_four_sessions_bind_despite_prior_pending_slots(rollout):
    for day in ("2026-10-27", "2026-10-28"):
        for auto, hour in [("v1-newsroom-london-1700", 10), (AUTO, 14),
                           ("v1-newsroom-new-york-2300", 16), ("v1-newsroom-new-york-0100", 18)]:
            reply = schedule.scheduled_binding(rollout, auto, now=at(f"{day}T{hour:02d}:00:01Z"))
            assert reply["classification"] == "NATIVE_WINDOW_SLOT_READY" and reply["slot_ordinal"] == 1
            assert reply["cutoff_utc"] == f"{day}T{hour:02d}:00:00Z"
    assert len(list(Path(rollout["editorial_output_root"]).glob("**/native_operation_binding.json"))) == 8


def test_actual_cli_uses_completed_discovery_without_advancing_or_allocating(rollout, monkeypatch, tmp_path, capsys):
    from scripts import run_native_desktop_editorial as cli
    _, binding, path = start(rollout)
    terminal_abstention(rollout, binding)
    config = tmp_path / "rollout.json"
    config.write_bytes(canonical_bytes(rollout))
    original = schedule.scheduled_binding
    monkeypatch.setattr(schedule, "scheduled_binding", lambda *args, **kwargs:
        original(*args, **kwargs, now=at("2026-10-27T06:00:00Z")))
    monkeypatch.setattr(cli, "operation", lambda *_args, **_kwargs: pytest.fail("completed discovery advanced work"))
    assert cli.main(["scheduled", "--automation-id", AUTO, "--rollout", str(config)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["classification"] == "NATIVE_WINDOW_OPERATION_COMPLETE" and result["binding_path"] == str(path)
    assert result["model_invocations"] == result["source_requests"] == 0


def test_task_startup_precedes_full_context_without_changing_roles_or_calendar():
    from live_contentops.codex_desktop_newsroom_operator_v1 import four_task_setup_packet
    packet = four_task_setup_packet()
    assert len(packet["tasks"]) == 4 and packet["model"] == "gpt-6.1-sol" and packet["reasoning_effort"] == "low"
    for task in packet["tasks"]:
        prompt = task["prompt"]
        assert prompt.startswith("STARTUP FIRST:")
        assert prompt.index("scheduled --automation-id") < prompt.index("lengthy context reads")
        assert "never backdates a never-bound window" in prompt and "--continue-after" in prompt
        assert "gpt-6-luna/max" in prompt and "gpt-6.1-sol/max" in prompt
        assert "UNKNOWN writes" in prompt and "same writer" in prompt
