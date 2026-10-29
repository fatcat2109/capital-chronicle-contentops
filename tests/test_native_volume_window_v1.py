"""Isolated revised-window controls; no fixture is a live publication/model proof."""
import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired, NativeDesktopTurn
from live_contentops.native_newsroom_volume_v1 import (
    configure_volume_turn, volume_policy, window_progress, persist_native_day_measurement,
)
from live_contentops.v1_simple_evidence_resolver_v1 import SimpleFirstPartyAwareEvidenceResolver
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _validate_selection_text, run_v1_simple_gemini_newsroom,
)
from test_v1_simple_gemini_newsroom_v1 import _headlines, _selection, _evidence_result

CUTOFF = "2026-10-30T10:00:00Z"


def test_production_boundary_keeps_tonight_and_frozen_operations_unchanged():
    assert volume_policy("2026-10-29T18:00:00Z") is None  # 01:00 on 30 Oct, prior day
    assert volume_policy("2026-10-29T18:59:59Z") is None
    assert volume_policy("2026-10-29T19:00:00Z")["max_articles"] == 2
    assert volume_policy(CUTOFF)["max_admitted_candidates"] == 6
    assert volume_policy(CUTOFF, brief_only=True)["max_articles"] == 1
    assert volume_policy(CUTOFF, brief_only=True)["brief_only"] is True


def test_six_admissions_are_policy_bound_and_brief_cannot_be_analysis():
    value = _selection(*(str(i) for i in range(6)))
    text = json.dumps(value)
    assert not _validate_selection_text(text, candidate_ids={str(i) for i in range(6)})[0]
    assert _validate_selection_text(text, candidate_ids={str(i) for i in range(6)}, max_admitted=6)[0]
    assert not _validate_selection_text(json.dumps(_selection("a")), candidate_ids={"a"},
        max_admitted=3, brief_only=True)[0]


def test_ten_request_resolver_requires_non_chargeable_route_and_carries_usage():
    with pytest.raises(ValueError):
        SimpleFirstPartyAwareEvidenceResolver(evaluation_as_of_utc=CUTOFF, max_requests=10)
    resolver = SimpleFirstPartyAwareEvidenceResolver(evaluation_as_of_utc=CUTOFF,
        max_requests=10, non_chargeable_only=True)
    resolver.resume_request_count(8)
    assert resolver.request_count == 8
    with pytest.raises(ValueError):
        resolver.resume_request_count(0)
    with pytest.raises(ValueError):
        resolver.resume_request_count(11)


def make_turn(store, root, run, **extra):
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(work_item_id=work, story_id=work, title="Controlled revised window",
        target_surface="CONTENTOPS_EDITORIAL_ONLY")
    root.mkdir(exist_ok=True)
    turn = NativeDesktopTurn(store, run_id=run, output_dir=root, owner_manual_validation=True)
    binding = {"run_id": run, "output_dir": str(root), "cutoff_utc": CUTOFF,
        "volume_policy": volume_policy(CUTOFF), **extra}
    configure_volume_turn(turn, binding)
    return turn, binding


def test_real_source_walk_then_hold_resumes_next_original_admission_without_budget_reset(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    first, binding = make_turn(store, tmp_path / "first", "first")
    rolling = _headlines(6)
    for row in rolling["headlines"]:
        row["source_timestamp_utc"] = "2026-10-30T09:00:00Z"
    calls = []
    def loader(request):
        calls.append(request["cluster_id"])
        if len(calls) == 1:
            return _evidence_result(request_count=3, status="BLOCKED", blocker="publisher_unavailable")
        return _evidence_result(request_count=2)
    def run(turn):
        return run_v1_simple_gemini_newsroom(output_dir=turn.root, cutoff_utc=CUTOFF,
            run_id=turn.run_id, rolling_input=rolling, llm_invoke=turn, evidence_loader=loader)
    with pytest.raises(DesktopInputRequired) as pending:
        run(first)
    request = pending.value.request
    ids = [c["candidate_id"] for c in request["governed_input"]["candidates"]]
    selection = _selection(*ids)
    for plan in selection["ordered_candidate_plan"]:
        plan.update(angle="Specific current question", primary_reader_question="What does this report establish?",
            evidence_plan="Use the existing free primary source route and retain missing facts.")
    observation = {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol", "reasoning_effort": "low",
        "invocation_id": "/root/CONTROLLED_NOT_MODEL_PROOF", "observation_source": "CONTROLLED_TEST_ONLY"}
    first.submit("select", {"request_sha256": request["request_sha256"],
        "output": selection, "invocation_observation": observation})
    with pytest.raises(DesktopInputRequired) as media:
        run(first)
    assert media.value.request["stage"] == "media-plan"
    walk = json.loads((first.root / "simple_gemini_evidence_v1.json").read_bytes())
    assert walk["request_count"] == 5 and walk["request_limit"] == 10
    assert calls == ids[:2]
    with pytest.raises(DesktopInputRequired) as review:
        first(logical_invocation_id="first:visual-edit", prompt="Controlled editorial review",
            governed_input={"source_pack": walk["selected_source_pack"]},
            validator=lambda raw: (True, None, json.loads(raw), None))
    first.submit("visual-edit", {"request_sha256": review.value.request["request_sha256"],
        "output": {"schema_version": "contentops.native_pre_writer_outcome.v1", "outcome": "HOLD",
            "candidate_id": ids[1], "primary_cause": "SOURCE_AMBIGUITY",
            "reason": "The source does not resolve whether this describes a forecast or a current decision.",
            "source_request_count": 5, "source_request_limit": 10, "public_write_attempted": False},
        "invocation_observation": {**observation, "reasoning_effort": "max"}})
    terminal = first.advance_story_outcomes()
    assert terminal["classification"] == "NATIVE_PRE_WRITER_EDITION_COMPLETE"
    assert terminal["remaining_candidate_ids"] == ids[2:]
    progress = window_progress(store, [(binding, first.root / "native_operation_binding.json")])
    assert progress["source_request_count"] == 5
    assert set(progress["attempted_candidate_ids"]) == set(ids[:2])
    second, _ = make_turn(store, tmp_path / "second", "second", source_request_count_at_start=5,
        attempted_candidate_ids=progress["attempted_candidate_ids"], selection_origin_run_id="first")
    with pytest.raises(DesktopInputRequired) as next_media:
        run(second)
    assert next_media.value.request["stage"] == "media-plan"  # genuinely reached next qualified story
    assert calls == ids[:3]
    later = json.loads((second.root / "simple_gemini_evidence_v1.json").read_bytes())
    assert later["selected_candidate_id"] == ids[2] and later["request_count"] == 7
    reused = second._get("select", "response")
    assert reused["reused_native_selection"]["new_model_invocation"] is False
    assert reused["invocation_observation"] == observation
    assert second.telemetry()["reused_native_selection_count"] == 1
    assert json.loads((first.root / "native_desktop_result.json").read_bytes()) == terminal
    assert store.list_platform_dispatches() == []


def test_day_measurement_keeps_unknown_readers_and_original_count_separate(tmp_path):
    from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id, build_production_day_snapshot
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    day = newsroom_production_day_id(CUTOFF)
    root = tmp_path / day / "window" / "run"
    root.mkdir(parents=True)
    _, binding = make_turn(store, root, "run", window_id="window")
    store.register_outbox_message(message_id="native-operation-binding-" + sha256_of("run"),
        work_item_id="cc-opportunity-" + sha256_of("run"), destination="internal:native-desktop-editorial",
        payload=json.dumps(binding), status="EDITORIAL_INTERNAL")
    path = persist_native_day_measurement(store, binding)
    measurement = json.loads(Path(path).read_bytes())["native_volume_measurement"]
    assert measurement["distinct_canonical_items_published"] == 0
    assert measurement["reader_counts"] is None and measurement["reader_counts_availability"] == "UNAVAILABLE"
    assert measurement["confirmed_copies_by_channel"] == {"substack": 0}
    revised = build_production_day_snapshot(reference=CUTOFF, output_root=tmp_path)
    old = build_production_day_snapshot(reference="2026-10-29T18:00:00Z", output_root=tmp_path)
    assert revised.final_published_target_min == 8 and old.final_published_target_min == 5


def test_cross_window_or_unbound_budget_carry_is_rejected(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    turn, binding = make_turn(store, tmp_path / "turn", "current")
    with pytest.raises(ValueError, match="BOUND_VOLUME_POLICY"):
        configure_volume_turn(turn, {"cutoff_utc": "2026-10-29T18:00:00Z", "source_request_count_at_start": 5})
    with pytest.raises(ValueError, match="BINDING_INVALID"):
        configure_volume_turn(turn, {**binding, "cutoff_utc": "2026-10-29T18:00:00Z"})
    with pytest.raises(ValueError, match="BUDGET_CARRY_INVALID"):
        configure_volume_turn(turn, {**binding, "source_request_count_at_start": 11})


def test_day_measurement_includes_only_same_day_saved_quota_stops(tmp_path):
    from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id
    store = ContentOpsDurableStore(tmp_path / "quota-state.sqlite3")
    day = newsroom_production_day_id(CUTOFF)
    root = tmp_path / day / "window" / "run"
    root.mkdir(parents=True)
    _, binding = make_turn(store, root, "run", window_id="window")
    work = "cc-opportunity-" + sha256_of("run")
    store.register_outbox_message(message_id="native-operation-binding-" + sha256_of("run"),
        work_item_id=work, destination="internal:native-desktop-editorial",
        payload=json.dumps(binding), status="EDITORIAL_INTERNAL")
    for date in ("2026-10-29", "2026-10-30"):
        event = {"cause": "CODEX_QUOTA_STOP", "lane": "CONTENTOPS_BUILDER", "production_date": date,
            "observed_at_utc": date + "T09:00:00Z", "source_identity": "CONTROLLED_TEST_NOT_LIVE_QUOTA",
            "observation_source": "CONTROLLED_FIXTURE"}
        store.register_outbox_message(message_id="native-quota-stop-" + sha256_of(event),
            work_item_id=work, destination="internal:native-quota-stop", payload=json.dumps(event), status="EDITORIAL_INTERNAL")
    path = persist_native_day_measurement(store, binding)
    measurement = json.loads(Path(path).read_bytes())["native_volume_measurement"]
    assert len(measurement["quota_stops"]) == 1
    assert measurement["quota_stops"][0]["production_date"] == "2026-10-30"
    assert measurement["distinct_canonical_items_published"] == 0
