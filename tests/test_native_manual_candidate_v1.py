"""Isolated synthetic topology controls, never native/source/publication acceptance.

The retained real CC-042 copy replay is recorded separately in its evidence folder.
"""
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore, LeaseConflictError
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, PRE_WRITER_OUTCOME_SCHEMA
from live_contentops.native_manual_candidate_v1 import active_manual_candidate, native_artifact_key
from live_contentops.native_newsroom_volume_v1 import configure_volume_turn, volume_policy
from tests.test_native_newsroom_owner_operation_v1 import entry
from tests.test_v1_simple_gemini_newsroom_v1 import _headlines, _selection, _evidence_result

CUTOFF = "2026-10-30T23:45:33.033578Z"
OBS = {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol", "reasoning_effort": "low",
    "invocation_id": "/root/CONTROLLED_SYNTHETIC_NOT_NATIVE_PROOF", "observation_source": "SYNTHETIC_TEST_ONLY"}
# The shared window source cap of a binding issued at CUTOFF (CC-047 amendment: 20 from production day 31 Oct).
LIMIT = volume_policy(CUTOFF)["source_request_limit"]


def turn_for(store, binding):
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"], owner_manual_validation=True)
    configure_volume_turn(turn, binding)
    return turn


def intent(store, binding):
    turn = turn_for(store, binding)
    frozen = store.get_outbox_message("native-current-input-" + sha256_of(turn.run_id))
    walk = turn.root / "simple_gemini_evidence_v1.json"
    return {"binding_sha256": sha256_of(binding), "cutoff_utc": binding.get("input_known_at_cutoff_utc", binding["cutoff_utc"]),
        "selection_request_sha256": turn.frozen_request("select")["request_sha256"],
        "selection_response_sha256": sha256_of(turn._get("select", "response")),
        "frozen_input_sha256": sha256_of(json.loads(frozen["payload"])),
        "previous_transition_sha256": sha256_of(turn.manual_candidate) if turn.manual_candidate else None,
        "outcomes_sha256": sha256_of(turn.story_outcomes()),
        "evidence_sha256": sha256(walk.read_bytes()).hexdigest() if walk.is_file() else None,
        "source_request_count": max([turn.source_request_count_at_start] + [v["source_request_count"] for v in turn.story_outcomes()]
                                    + [json.loads(walk.read_bytes())["request_count"]] if walk.is_file() else [turn.source_request_count_at_start])}


def refuse(module, binding, pending, candidate, *, used=5):
    return module.operation(binding, command="submit", stage=pending["stage"], response={
        "request_sha256": pending["request_sha256"], "invocation_observation": {**OBS, "reasoning_effort": "max"},
        "output": {"schema_version": PRE_WRITER_OUTCOME_SCHEMA, "candidate_id": candidate, "outcome": "HOLD",
            "primary_cause": "SOFTWARE_PROCESS_DEFECT", "reason": "Synthetic fixture preserves the accepted original source-packet process HOLD.",
            "source_request_count": used, "source_request_limit": LIMIT, "public_write_attempted": False}})


def seed(tmp_path, monkeypatch):
    module = entry()
    class NoMainSource:
        def bundle(self, _):
            raise FileNotFoundError("CONTROLLED_NO_MAIN_REPORT")
    def feed(tracker, pointer, **kwargs):
        return MainReportFeed(tracker, {"bundles": [{"name": "CONTROLLED_NO_MAIN"}]},
            source=NoMainSource(), headline_paths=[], **kwargs)
    monkeypatch.setattr(module, "MainReportFeed", feed)
    monkeypatch.setattr(module, "load_canonical_published_memory_read_only", lambda **_: ([], {}))
    calls, budgets = [], []
    class Resolver:
        def resume_request_count(self, used):
            budgets.append(used)
        def __call__(self, request):
            calls.append(deepcopy(request))
            return deepcopy(_evidence_result(request_count=2))
    monkeypatch.setattr("live_contentops.v1_simple_gemini_newsroom_v1._default_evidence_loader", lambda *a, **k: Resolver())
    rolling = _headlines(3)
    for h in rolling["headlines"]:
        h["source_timestamp_utc"] = "2026-10-30T20:00:00Z"
    (tmp_path / "rolling.json").write_bytes(canonical_bytes(rolling))
    (tmp_path / "feed.json").write_text("{}")
    profile = {"schema_version": "contentops.native_desktop_operator_profile.v1", "editorial_output_root": str(tmp_path / "output"),
        "rolling_input_path": str(tmp_path / "rolling.json"), "feed_pointer_path": str(tmp_path / "feed.json"),
        "store_path": str(tmp_path / "store.sqlite3"), "published_memory_store": str(tmp_path / "memory.sqlite3"),
        "published_memory_output_root": str(tmp_path / "memory")}
    path, binding = module.resolve_owner_operation(profile, operation_id="retained-manual-topology",
        request="Synthetic original three-candidate retained operation; never publish.", now=datetime.fromisoformat(CUTOFF.replace("Z", "+00:00")))
    select = module.operation(binding)
    request = json.loads(Path(select["request_path"]).read_bytes())
    ids = [c["candidate_id"] for c in request["governed_input"]["candidates"]]
    selected = _selection(*ids)
    for p in selected["ordered_candidate_plan"]:
        # A BREAKING_BRIEF now takes the decision 37 B2 text-first route straight to the writer
        # (native_text_first_v1.writer_policy), and time-sensitive modes skip the MAX visual edit
        # (decision 53, native_publication_latency_v1.speed_policy). This topology covers the
        # media-plan -> visual-edit path, which long-form modes still take.
        p.update(article_mode="CAPITAL_CHRONICLE_VIEW", angle="Synthetic bounded report question", primary_reader_question="What is actually established?",
                 evidence_plan="Retain the exact publisher, frozen cutoff and rights gates; no new facts.")
    module.operation(binding, command="submit", stage="select", response={"request_sha256": select["request_sha256"],
        "output": selected, "invocation_observation": OBS})
    assert module.operation(binding)["stage"] == "media-plan"
    media = module.operation(binding, command="media-plan")
    module.operation(binding, command="submit", stage="media-plan", response={"request_sha256": media["request_sha256"],
        "output": {"story_plan": {"thesis": "Synthetic controlled Light plan"}}, "invocation_observation": OBS})
    visual = module.operation(binding, command="media-plan")
    store = ContentOpsDurableStore(binding["store_path"])
    refuse(module, binding, visual, ids[0])
    partial = module.operation(binding)
    assert partial["classification"] == "NATIVE_NEXT_CANDIDATE_REQUIRED"
    legacy = {"classification": "NATIVE_PRE_WRITER_EDITION_COMPLETE", "run_id": binding["run_id"],
        "model_execution_state": "NATIVE_DESKTOP_REQUEST_RETURN", "qualified_article_count": 0,
        "remaining_candidate_ids": ids[1:], "source_request_count": 5, "source_request_limit": LIMIT,
        "candidate_outcomes": turn_for(store, binding).story_outcomes(),
        "next_operation": "scheduled --continue-after " + binding["run_id"]}
    old_key = "cc-editorial-final-" + sha256_of(binding["run_id"])
    store.register_outbox_message(message_id=old_key, work_item_id=turn_for(store, binding).work,
        destination="internal:native-desktop-editorial", status="EDITORIAL_INTERNAL", payload=canonical_bytes(legacy).decode())
    Path(binding["output_dir"], "native_desktop_result.json").write_bytes(canonical_bytes(legacy))
    original = {r["message_id"]: (r["payload"], r["status"]) for r in store.list_outbox_messages()}
    files = {p: p.read_bytes() for p in Path(binding["output_dir"]).rglob("*") if p.is_file()}
    return module, store, binding, ids, calls, budgets, original, files


def transition(data, candidate=None, response=None):
    module, store, binding, ids, *_ = data
    return module.operation(binding, command="next-candidate", candidate_id=candidate or ids[1], response=response or intent(store, binding))


def test_preserved_partial_final_progresses_both_untouched_candidates_without_new_operation(tmp_path, monkeypatch):
    data = seed(tmp_path, monkeypatch)
    module, store, binding, ids, calls, budgets, original, files = data
    request = intent(store, binding)
    assert transition(data)["classification"] == "NATIVE_MANUAL_CANDIDATE_READY"
    count = len(store.list_outbox_messages())
    assert transition(data, response=request)["idempotent_replay"] is True
    assert len(store.list_outbox_messages()) == count
    for i, used in [(1, 7), (2, 9)]:
        pending = module.operation(binding)
        assert pending["stage"] == "media-plan" and calls[-1]["cluster_id"] == ids[i]
        assert calls[-1]["remaining_window_source_requests"] == LIMIT - (5 if i == 1 else 7)
        before = len(calls)
        assert module.operation(binding)["request_sha256"] == pending["request_sha256"]
        assert len(calls) == before
        media = module.operation(binding, command="media-plan")
        assert media["stage"] == "media-plan"
        turn = turn_for(store, binding)
        assert turn.root != Path(binding["output_dir"])
        assert Path(media["next_native_call"]["result_path"]).parent == turn.root
        module.operation(binding, command="submit", stage="media-plan", response={"request_sha256": media["request_sha256"],
            "output": {"story_plan": {"thesis": "Synthetic new candidate Light preparation"}}, "invocation_observation": OBS})
        visual = module.operation(binding, command="media-plan")
        assert visual["stage"] == "visual-edit" and visual["next_native_call"]["tool"] == "collaboration.spawn_agent"
        assert json.loads(Path(visual["request_path"]).read_bytes())["manual_candidate_id"] == ids[i]
        refuse(module, binding, visual, ids[i], used=used)
        outcome = module.operation(binding)
        if i == 1:
            assert outcome["classification"] == "NATIVE_NEXT_CANDIDATE_REQUIRED" and outcome["candidate_id"] == ids[2]
            transition(data, ids[2])
        else:
            assert outcome["classification"] == "NATIVE_PRE_WRITER_EDITION_COMPLETE"
            assert outcome["remaining_candidate_ids"] == [] and outcome["outcome_counts"] == {"HOLD": 3}
            assert outcome["source_request_count"] == 9
            assert module.operation(binding) == outcome
    assert [r["cluster_id"] for r in calls] == ids
    current = {r["message_id"]: (r["payload"], r["status"]) for r in store.list_outbox_messages()}
    assert all(current[k] == v for k, v in original.items())
    assert all(p.read_bytes() == raw for p, raw in files.items())
    assert json.loads(Path(binding["output_dir"], "binding.json").read_bytes()) == binding
    assert len([r for r in store.list_outbox_messages() if r["message_id"].startswith("native-operation-binding-")]) == 1
    assert not store.list_platform_dispatches()


@pytest.mark.parametrize("key", ["binding_sha256", "selection_request_sha256", "selection_response_sha256",
    "frozen_input_sha256", "cutoff_utc", "outcomes_sha256", "evidence_sha256", "previous_transition_sha256", "source_request_count"])
def test_stale_preconditions_cannot_change_outbox_or_open_candidate(tmp_path, monkeypatch, key):
    data = seed(tmp_path, monkeypatch)
    _, store, binding, *_ = data
    response = intent(store, binding)
    response[key] = 0 if key == "source_request_count" else "stale"
    before = store.list_outbox_messages()
    with pytest.raises(ValueError):
        transition(data, response=response)
    assert store.list_outbox_messages() == before and active_manual_candidate(store, binding["run_id"]) is None


@pytest.mark.parametrize("which", ["old_hold", "later", "unknown", "empty"])
def test_explicit_next_identity_is_required_and_old_hold_cannot_be_reopened(tmp_path, monkeypatch, which):
    data = seed(tmp_path, monkeypatch)
    module, store, binding, ids, *_ = data
    candidate = {"old_hold": ids[0], "later": ids[2], "unknown": "unknown", "empty": None}[which]
    before = store.list_outbox_messages()
    with pytest.raises(ValueError, match="NEXT_UNTOUCHED"):
        module.operation(binding, command="next-candidate", candidate_id=candidate, response=intent(store, binding))
    assert store.list_outbox_messages() == before


def test_active_candidate_cannot_be_skipped_or_accept_old_stage_return(tmp_path, monkeypatch):
    data = seed(tmp_path, monkeypatch)
    module, store, binding, ids, *_ = data
    old = turn_for(store, binding)._get("visual-edit", "response")
    transition(data)
    with pytest.raises(ValueError, match="PREDECESSOR"):
        transition(data, ids[2])
    with pytest.raises(ValueError, match="REQUEST_BINDING"):
        module.operation(binding, command="submit", stage="visual-edit", response=old)
    assert len(turn_for(store, binding).story_outcomes()) == 1


def test_operation_lease_excludes_both_transition_and_stale_submit(tmp_path, monkeypatch):
    data = seed(tmp_path, monkeypatch)
    module, store, binding, *_ = data
    lease = store.acquire_lease("internal:native-editorial:" + binding["run_id"], "competing-existing-worker", ttl_seconds=60)
    try:
        before = store.list_outbox_messages()
        with pytest.raises(LeaseConflictError):
            transition(data)
        with pytest.raises(LeaseConflictError):
            module.operation(binding, command="submit", stage="visual-edit", response={})
        assert store.list_outbox_messages() == before
    finally:
        store.release_lease(lease["lease_id"], "competing-existing-worker", lease["fencing_token"])


def test_partial_final_cannot_be_reported_as_terminal_and_original_result_stays_exact(tmp_path, monkeypatch):
    from live_contentops.native_desktop_schedule_binding_v1 import prepare_standalone_result
    data = seed(tmp_path, monkeypatch)
    _, store, binding, *_ = data
    response = {"entry_path": "newsroom", "source_context": {"source_role": "STANDALONE_TASK", "source_thread_id": "00000000-0000-4000-8000-000000000001", "source_turn_id": "CONTROLLED_TURN"}}
    before = store.list_outbox_messages()
    with pytest.raises(ValueError, match="UNFINISHED"):
        prepare_standalone_result(store, binding, response)
    assert store.list_outbox_messages() == before


def test_scheduled_binding_cannot_take_manual_transition(tmp_path, monkeypatch):
    data = seed(tmp_path, monkeypatch)
    module, _, binding, *_ = data
    with pytest.raises(ValueError):
        module.operation({**binding, "window_id": "scheduled-window"}, command="next-candidate", candidate_id="no", response={})


def test_cli_requires_candidate_and_exact_response_and_bounded_option(tmp_path, monkeypatch):
    module = entry()
    for args in [["next-candidate"], ["next-candidate", "--binding", "missing"], ["advance", "--candidate-id", "no"],
        ["next-candidate", "--binding", "missing", "--candidate-id", "candidate", "--response", "missing", "--continue-after", "prior"]]:
        with pytest.raises(SystemExit) as error:
            module.main(args)
        assert error.value.code == 2


@pytest.mark.parametrize("cause", ["unknown_write", "confirmed_write", "reconciliation", "source_started", "native_pending", "exhausted", "over_budget"])
def test_existing_ambiguity_pending_work_or_spending_prevents_transition_without_mutation(tmp_path, monkeypatch, cause):
    data = seed(tmp_path, monkeypatch)
    module, store, binding, ids, *_ = data
    turn = turn_for(store, binding)
    if cause in {"unknown_write", "confirmed_write"}:
        store.register_platform_dispatch(dispatch_id="CONTROLLED_NOT_A_REAL_SEND", message_id="native-operation-binding-" + sha256_of(turn.run_id),
            platform="substack", status="UNKNOWN_WRITE" if cause == "unknown_write" else "CONFIRMED")
    elif cause == "reconciliation":
        store.register_reconciliation(reconciliation_id="CONTROLLED_PENDING", work_item_id=turn.work, status="PENDING")
    elif cause == "source_started":
        store.register_outbox_message(message_id="controlled-unresolved-source", work_item_id=turn.work,
            destination="internal:cc-report-editorial-stage", payload=json.dumps({"stage": "source:controlled", "request_sha256": "unresolved"}))
    elif cause == "native_pending":
        turn._put("write", "request", {"stage": "write", "requested_model": "gpt-6.1-sol", "request_sha256": "unanswered-controlled"})
    else:
        store.register_outbox_message(message_id="controlled-spending", work_item_id=turn.work,
            destination="internal:native-desktop-source-recovery", payload=json.dumps({"pre_writer_source_recovery": True,
                "source_request_count": LIMIT if cause == "exhausted" else LIMIT + 1}))
    response = intent(store, binding)
    if cause == "exhausted": response["source_request_count"] = LIMIT
    before = store.list_outbox_messages()
    with pytest.raises(ValueError):
        transition(data, response=response)
    assert store.list_outbox_messages() == before and active_manual_candidate(store, binding["run_id"]) is None


@pytest.mark.parametrize("change", ["binding", "input", "selection", "outcome"])
def test_active_resume_refuses_frozen_binding_input_selection_or_prior_outcome_drift(tmp_path, monkeypatch, change):
    data = seed(tmp_path, monkeypatch)
    module, store, binding, *_ = data
    transition(data)
    if change == "binding":
        binding = {**binding, "cutoff_utc": "2026-10-31T00:00:00Z"}
    else:
        turn = turn_for(store, binding)
        key = {"input": "native-current-input-" + sha256_of(turn.run_id), "selection": turn._key("select", "response"),
               "outcome": "native-story-outcome-" + sha256_of([turn.run_id, turn.story_outcomes()[0]["candidate_id"]])}[change]
        value = json.loads(store.get_outbox_message(key)["payload"])
        value["CONTROLLED_CORRUPTION"] = True
        store.finalize_outbox_payload_before_dispatch(message_id=key, payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    before = store.list_outbox_messages()
    with pytest.raises(ValueError, match="CHANGED"):
        module.operation(binding)
    assert store.list_outbox_messages() == before


def test_candidate_scoped_qualified_article_still_needs_actual_review_and_cannot_be_skipped(tmp_path, monkeypatch):
    data = seed(tmp_path, monkeypatch)
    module, store, binding, ids, *_ = data
    transition(data)
    turn = turn_for(store, binding)
    store.register_outbox_message(message_id=native_artifact_key(store, turn.run_id, "cc-editorial-final-"), work_item_id=turn.work,
        destination="internal:cc-report-simple-result", status="EDITORIAL_INTERNAL", payload=canonical_bytes({
            "model_execution_state": "NATIVE_DESKTOP_REQUEST_RETURN", "qualified_article_count": 1,
            "article_identity": "SYNTHETIC_NOT_QUALIFIED_OR_PUBLIC", "article": {}}).decode())
    before = store.list_outbox_messages()
    with pytest.raises(ValueError, match="KEEP_REVIEW_REQUIRED"):
        module.operation(binding, command="publication-prepare")
    with pytest.raises(ValueError, match="CANNOT_SKIP_QUALIFIED"):
        transition(data, ids[2])
    assert store.list_outbox_messages() == before and not store.list_platform_dispatches()


def test_cli_accepts_only_exact_manual_candidate_command_without_issuing_a_role(tmp_path, monkeypatch, capsys):
    data = seed(tmp_path, monkeypatch)
    module, store, binding, ids, calls, *_ = data
    path = tmp_path / "intent.json"
    next_command = module.operation(binding)["next_command"]
    assert next_command["candidate_id"] == ids[1] and next_command["command"] == "next-candidate"
    path.write_bytes(canonical_bytes(next_command["response"]))
    before = len(calls)
    assert module.main(["next-candidate", "--binding", str(Path(binding["output_dir"], "binding.json")),
        "--candidate-id", ids[1], "--response", str(path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["classification"] == "NATIVE_MANUAL_CANDIDATE_READY" and len(calls) == before
    assert module.main(["next-candidate", "--binding", str(Path(binding["output_dir"], "binding.json")),
        "--candidate-id", ids[0], "--response", str(path)]) == 2
    blocked = json.loads(capsys.readouterr().out)
    assert blocked["classification"] == "NATIVE_DESKTOP_BLOCKED"


def test_budget_exhaustion_records_untouched_candidate_as_budget_refusal_and_never_refetches(tmp_path, monkeypatch):
    data = seed(tmp_path, monkeypatch)
    module, store, binding, ids, calls, *_ = data
    transition(data)
    module.operation(binding)
    media = module.operation(binding, command="media-plan")
    module.operation(binding, command="submit", stage="media-plan", response={"request_sha256": media["request_sha256"],
        "output": {"story_plan": {"thesis": "Synthetic control"}}, "invocation_observation": OBS})
    visual = module.operation(binding, command="media-plan")
    refuse(module, binding, visual, ids[1], used=LIMIT)
    result = module.operation(binding)
    assert result["classification"] == "NATIVE_PRE_WRITER_EDITION_COMPLETE" and result["remaining_candidate_ids"] == []
    untouched = next(v for v in result["candidate_outcomes"] if v["candidate_id"] == ids[2])
    assert untouched["primary_cause"] == "BUDGET_OR_RETRY_CAP"
    assert untouched["provenance"]["new_source_requests"] == 0
    assert [v["cluster_id"] for v in calls] == ids[:2]
    assert module.operation(binding) == result


def test_lost_operation_fence_refuses_append_even_after_preconditions_pass(tmp_path, monkeypatch):
    import live_contentops.native_manual_candidate_v1 as manual
    from live_contentops.durable_operational_store_v1 import StaleFencingTokenError
    data = seed(tmp_path, monkeypatch)
    _, store, binding, *_ = data
    original = manual.continue_manual_candidate
    def lost(turn, bound, **kwargs):
        with store.get_connection() as conn:
            conn.execute("UPDATE leases SET fencing_token=fencing_token+1 WHERE lease_key=?",
                ("internal:native-editorial:" + binding["run_id"],))
        return original(turn, bound, **kwargs)
    monkeypatch.setattr(manual, "continue_manual_candidate", lost)
    before = store.list_outbox_messages()
    with pytest.raises(StaleFencingTokenError):
        transition(data)
    assert store.list_outbox_messages() == before and active_manual_candidate(store, binding["run_id"]) is None


def test_active_candidate_preserves_media_writer_role_and_same_writer_guards(tmp_path, monkeypatch):
    data = seed(tmp_path, monkeypatch)
    module, store, binding, ids, *_ = data
    transition(data)
    module.operation(binding)
    media = module.operation(binding, command="media-plan")
    plan = {"thesis": "Synthetic scoped candidate plan"}
    module.operation(binding, command="submit", stage="media-plan", response={"request_sha256": media["request_sha256"],
        "output": {"story_plan": plan}, "invocation_observation": OBS})
    visual = module.operation(binding, command="media-plan")
    decision = {"reader_first_version": "DATA_JOURNALISM_V1", "story_kind": "NEWS", "editorial_thesis": "Synthetic narrow source report",
        "charts": [], "exception_reason": "Synthetic factual news fixture has no admitted quantitative series or assets.",
        "channel_media": {c: [] for c in ("telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube")}}
    response = {"request_sha256": visual["request_sha256"], "output": decision,
        "invocation_observation": {**OBS, "reasoning_effort": "max"}}
    for field, value in [("model", "gpt-6-luna"), ("reasoning_effort", "low"), ("invocation_id", None)]:
        with pytest.raises(ValueError):
            module.operation(binding, command="submit", stage="visual-edit", response={**response,
                "invocation_observation": {**response["invocation_observation"], field: value}})
    module.operation(binding, command="submit", stage="visual-edit", response=response)
    packet = {"plan": {"native_plan_run_id": binding["run_id"], "native_plan_stage": "media-plan",
        "native_plan_request_sha256": media["request_sha256"], "story_plan": plan}, "assets": []}
    assert module.operation(binding, command="media-plan", response=packet)["classification"] == "EDITORIAL_MEDIA_PLANNED_WRITER_READY"
    writer = module.operation(binding)
    assert writer["stage"] == "write"
    turn = turn_for(store, binding)
    request = turn.frozen_request("write")
    assert request["manual_candidate_id"] == ids[1]
    assert request["governed_input"]["visual_editorial_decision"] == decision
    refused = {"request_sha256": writer["request_sha256"], "invocation_observation": {**OBS, "reasoning_effort": "max", "invocation_id": "/root/WRONG_SYNTHETIC_WRITER"},
        "output": {"schema_version": PRE_WRITER_OUTCOME_SCHEMA, "candidate_id": ids[1], "outcome": "HOLD", "primary_cause": "INSUFFICIENT_READER_VALUE",
            "reason": "Synthetic writer refusal must retain the exact same MAX visual editor identity.",
            "source_request_count": 7, "source_request_limit": LIMIT, "public_write_attempted": False}}
    with pytest.raises(ValueError, match="SAME_VISUAL_EDITOR_WRITER"):
        module.operation(binding, command="submit", stage="write", response=refused)
    assert turn._get("write", "response") is None and not store.list_platform_dispatches()
