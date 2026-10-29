"""Disposable native-return controls; these fixtures are not model/publication proof."""
import json

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import (
    DesktopInputRequired, NativeDesktopTurn, PRE_WRITER_OUTCOME_SCHEMA,
    PreWriterOutcomeReturned, validate_visual_decision,
)


def fixture_turn(tmp_path, candidates=("a",), *, stage="visual-edit"):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    work = "cc-opportunity-" + sha256_of("controlled")
    store.create_work_item(story_id=work, work_item_id=work, title="Controlled refusal", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    turn = NativeDesktopTurn(store, run_id="controlled", output_dir=tmp_path, owner_manual_validation=True)
    args = dict(logical_invocation_id="controlled:select", prompt="CONTROLLED_TEST_NOT_MODEL_PROOF",
        governed_input={"candidates": [{"candidate_id": c} for c in candidates]},
        validator=lambda raw: (True, None, json.loads(raw), None))
    with pytest.raises(DesktopInputRequired) as pending:
        turn(**args)
    observation = dict(surface="CODEX_NATIVE_SUBAGENT", invocation_id="/root/controlled_fixture",
        model="gpt-6.1-sol", reasoning_effort="low", observation_source="CONTROLLED_TEST_NOT_MODEL_PROOF")
    if stage != "select":
        turn.submit("select", {"request_sha256": pending.value.request["request_sha256"],
            "output": {"ordered_candidate_plan": [{"candidate_id": c} for c in candidates]},
            "invocation_observation": observation})
        args.update(logical_invocation_id="controlled:visual-edit", governed_input={"CONTROLLED_TEST_ONLY": True})
        with pytest.raises(DesktopInputRequired) as pending:
            turn(**args)
        observation = {**observation, "reasoning_effort": "max"}
    return turn, pending.value.request, observation, args


def refusal(outcome="HOLD", *, candidate="a", used=6):
    return {"schema_version": PRE_WRITER_OUTCOME_SCHEMA, "outcome": outcome,
        "candidate_id": candidate, "primary_cause": "SOURCE_AMBIGUITY",
        "reason": "The admitted source does not resolve whether the claim is a forecast or a policy decision.",
        "source_request_count": used, "source_request_limit": 6, "public_write_attempted": False}


@pytest.mark.parametrize("outcome", ["HOLD", "SOURCE_BLOCKED", "REJECT", "NO_STORY"])
def test_negative_native_return_is_resumable_with_zero_media(tmp_path, outcome):
    stage = "select" if outcome == "NO_STORY" else "visual-edit"
    turn, request, observation, args = fixture_turn(tmp_path, stage=stage)
    response = {"request_sha256": request["request_sha256"],
        "output": refusal(outcome, candidate=None if outcome == "NO_STORY" else "a"),
        "invocation_observation": observation}
    accepted = turn.submit(stage, response)
    assert accepted["outcome"] == outcome and not accepted["public_write_performed"]
    result = turn.advance_story_outcomes()
    assert result["classification"] == "NATIVE_PRE_WRITER_EDITION_COMPLETE"
    assert result["qualified_article_count"] == result["derivative_intent_count"] == 0
    assert result["outcome_counts"] == {outcome: 1}
    before = len(turn.store.list_outbox_messages())
    restarted = NativeDesktopTurn(turn.store, run_id="controlled", output_dir=tmp_path, owner_manual_validation=True)
    assert restarted.submit(stage, response) == accepted
    assert restarted.advance_story_outcomes() == result
    assert len(turn.store.list_outbox_messages()) == before
    with pytest.raises(PreWriterOutcomeReturned):
        restarted(**args)
    assert not list(tmp_path.glob("desktop_request_write*"))
    assert turn.store.list_platform_dispatches() == []


def test_remaining_candidate_keeps_budget_and_does_not_repeat_semantics_or_acquisition(tmp_path):
    turn, request, observation, _ = fixture_turn(tmp_path, candidates=("a", "b"))
    turn.submit("visual-edit", {"request_sha256": request["request_sha256"],
        "output": refusal(used=3), "invocation_observation": observation})
    before = len(turn.store.list_outbox_messages())
    for _ in range(2):
        result = turn.advance_story_outcomes()
        assert result["classification"] == "NATIVE_NEXT_CANDIDATE_REQUIRED" and result["candidate_id"] == "b"
        assert result["source_request_count"] == 3 and result["source_request_limit"] == 6
    assert len(turn.store.list_outbox_messages()) == before
    assert turn.telemetry()["semantic_response_count"] == 2


def test_exhausted_budget_closes_only_unqualified_candidates_and_preserves_causes(tmp_path):
    turn, request, observation, _ = fixture_turn(tmp_path, candidates=("a", "b", "c"))
    (tmp_path / "simple_gemini_evidence_v1.json").write_text(json.dumps({"request_count": 3,
        "candidate_attempt_history": [{"candidate_id": "a", "status": "SOURCE_BLOCKED", "blockers": ["no_accepted_document"]}]}))
    turn.submit("visual-edit", {"request_sha256": request["request_sha256"],
        "output": refusal(candidate="b"), "invocation_observation": observation})
    result = turn.advance_story_outcomes()
    assert result["cause_counts"] == {"SOURCE_MISSING": 1, "SOURCE_AMBIGUITY": 1, "BUDGET_OR_RETRY_CAP": 1}
    assert result["outcome_counts"] == {"SOURCE_BLOCKED": 2, "HOLD": 1}
    assert result["source_request_count"] == 6
    assert turn.store.list_platform_dispatches() == []


def test_exhausted_budget_does_not_discard_an_already_admitted_cached_pack(tmp_path):
    turn, request, observation, _ = fixture_turn(tmp_path, candidates=("a", "b"))
    (tmp_path / "simple_gemini_evidence_v1.json").write_text(json.dumps({"request_count": 3,
        "candidate_attempt_history": [{"candidate_id": "b", "status": "SOURCE_QUALIFIED", "source_pack": [{"document_id": "existing"}]}]}))
    turn.submit("visual-edit", {"request_sha256": request["request_sha256"],
        "output": refusal(), "invocation_observation": observation})
    result = turn.advance_story_outcomes()
    assert result["classification"] == "NATIVE_NEXT_CANDIDATE_REQUIRED"
    assert result["admitted_cached_source_pack"] == [{"document_id": "existing"}]


def test_refusal_cannot_replace_positive_return_or_smuggle_publication_and_missing_identity(tmp_path):
    turn, request, observation, _ = fixture_turn(tmp_path)
    response = {"request_sha256": request["request_sha256"], "output": refusal(),
        "invocation_observation": observation}
    for broken in ({**refusal(), "article": {"body": "not a refusal"}},
                   {**refusal(), "public_write_attempted": True}, {**refusal(), "source_request_count": 7}):
        with pytest.raises(ValueError):
            turn.submit("visual-edit", {**response, "output": broken})
    with pytest.raises(ValueError, match="INVOCATION_OBSERVATION_REQUIRED"):
        turn.submit("visual-edit", {**response, "invocation_observation": {**observation, "invocation_id": None}})
    assert turn.story_outcomes() == []
    turn._put("write", "response", {"request_sha256": "controlled-written", "output": {"article": {}},
                                   "invocation_observation": observation})
    with pytest.raises(ValueError, match="CANNOT_REPLACE_WRITTEN_ARTICLE"):
        turn.submit("visual-edit", response)


def test_decision_does_not_require_instagram_image_but_keeps_editorial_chart_contract():
    value = {"reader_first_version": "DATA_JOURNALISM_V1", "story_kind": "POLICY", "editorial_thesis": "Narrow report",
        "charts": [], "exception_reason": "No quantitative series is admitted for this narrow policy report.",
        "channel_media": {c: [] for c in ("telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube")}}
    assert validate_visual_decision(value) == value
    with pytest.raises(ValueError, match="ANALYSIS_REQUIRES"):
        validate_visual_decision({**value, "story_kind": "ANALYSIS"})


def test_actual_operation_resumes_terminal_return_before_any_source_or_media_work(tmp_path, monkeypatch):
    from scripts import run_native_desktop_editorial as cli
    turn, request, observation, _ = fixture_turn(tmp_path)
    turn.submit("visual-edit", {"request_sha256": request["request_sha256"],
        "output": refusal(), "invocation_observation": observation})
    binding = {"schema_version": cli.BINDING_SCHEMA, "run_id": "controlled",
        "store_path": str(tmp_path / "state.sqlite3"), "output_dir": str(tmp_path),
        "feed_pointer_path": str(tmp_path / "must-not-read.json"),
        "published_memory_store": str(tmp_path / "state.sqlite3"),
        "published_memory_output_root": str(tmp_path), "cutoff_utc": "2026-10-28T08:01:00Z",
        "owner_manual_validation": True}
    monkeypatch.setattr(cli, "load_canonical_published_memory_read_only", lambda **_: pytest.fail("reopened source work"))
    first = cli.operation(binding)
    count = len(turn.store.list_outbox_messages())
    assert cli.operation(binding) == cli.operation(binding, command="media-plan") == first
    assert first["classification"] == "NATIVE_PRE_WRITER_EDITION_COMPLETE"
    assert len(turn.store.list_outbox_messages()) == count
    assert first["source_request_count"] == 6 and not first["public_write_performed"]


def test_typed_hold_can_be_returned_during_selection_without_a_positive_plan(tmp_path):
    turn, request, observation, _ = fixture_turn(tmp_path, stage="select")
    accepted = turn.submit("select", {"request_sha256": request["request_sha256"],
        "output": refusal(), "invocation_observation": observation})
    assert accepted["outcome"] == "HOLD"
    assert turn.advance_story_outcomes()["outcome_counts"] == {"HOLD": 1}
