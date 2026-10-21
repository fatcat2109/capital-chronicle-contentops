"""Isolated deterministic controls, not audience or native-model runtime evidence."""

import json
from datetime import datetime, timezone

import pytest

from live_contentops import daily_app_performance_v1 as perf
from live_contentops import native_newsroom_learning_v1 as learning
from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    sha256_of,
    canonical_bytes,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import (
    NativeDesktopTurn,
    DesktopInputRequired,
)
from test_daily_app_performance_learning_v1 import (
    _supervisor,
    _seed_confirmed_publication,
    T0,
)
from test_v1_simple_gemini_newsroom_v1 import (
    _headlines,
    _selection,
    _article_output,
    _evidence_result,
    CUTOFF,
)


def _work(store, run):
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(
        work_item_id=work,
        story_id=work,
        title="Controlled",
        target_surface="CONTENTOPS_EDITORIAL_ONLY",
    )
    return work


def _observed(tmp_path):
    sup = _supervisor(tmp_path)
    store = sup._store
    dispatch_id = _seed_confirmed_publication(sup)
    with store.get_connection() as conn:
        conn.execute(
            "UPDATE reconciliations SET reconciliation_id=?",
            ("reconciliation_" + dispatch_id.removeprefix("dispatch_"),),
        )
    dispatch = store.get_platform_dispatch(dispatch_id)
    observation = perf.build_scheduled_observations(
        dispatch=dispatch,
        work_item_id="wi_pub_0",
        dispatched_at=T0,
        learning_eligible=True,
    )[0]
    store.register_performance_observation(observation=observation)
    observer = learning.NativeAudienceObservation(
        store, output_dir=tmp_path / "neo", invocation_id="CONTROLLED_NO_TOOL"
    )
    pending = observer.advance(observation["observation_id"])["request"]
    request = pending["request"]
    observer.tool(
        "begin",
        observation_id=observation["observation_id"],
        request_hash=request["request_sha256"],
    )
    response = {
        "tool_request_sha256": pending["tool_request_sha256"],
        "tool_observation": {
            "tool_name": "mcp__browseros_neo__run",
            "native_invocation_id": "CONTROLLED_NO_TOOL",
            "surface": "CODEX_DESKTOP_CONVERSATION",
            "observation_source": "CONTROLLED_TEST_NO_BROWSER",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "result": {
            "request_sha256": request["request_sha256"],
            "public_object_id": request["public_object_id"],
            "public_object_url": request["public_object_url"],
            "identity_verified": True,
            "status": "COLLECTED",
            "source_identity": "CONTROLLED_TEST",
            "metrics": {"impressions": 7, "shares": 999},
            "availability": {"impressions": "AVAILABLE", "shares": "NOT_EXPOSED"},
            "interactions": [
                {"text": "Which exact source supports the seasonal comparison?"}
            ],
        },
    }
    return store, observer, observation, request, response


def test_native_observation_restart_nulls_identity_and_crash_recovery(tmp_path):
    store, observer, obs, request, response = _observed(tmp_path)
    with pytest.raises(ValueError, match="WRONG_PUBLIC_OBJECT"):
        observer.tool(
            "submit",
            observation_id=obs["observation_id"],
            request_hash=request["request_sha256"],
            response={
                **response,
                "result": {**response["result"], "public_object_id": "wrong"},
            },
        )
    observer.tool(
        "submit",
        observation_id=obs["observation_id"],
        request_hash=request["request_sha256"],
        response=response,
    )
    result = observer.advance(obs["observation_id"])
    assert result["metrics_model_calls"] == 0
    metrics = json.loads(result["observation"]["metrics_native_json"])
    assert metrics["shares"] is None and metrics["impressions"] == 7
    assert (
        result["feedback"]["scheduled_for_utc"]
        != result["feedback"]["collected_at_utc"]
    )
    with store.get_connection() as conn:
        conn.execute(
            "DELETE FROM outbox_messages WHERE destination=?", (learning.FEEDBACK,)
        )
    assert (
        observer.advance(obs["observation_id"])["state"]
        == "OBSERVATION_ALREADY_RECORDED"
    )
    assert len(learning._rows(store, learning.FEEDBACK)) == 1
    count = len(store.list_outbox_messages())
    observer.advance(obs["observation_id"])
    assert len(store.list_outbox_messages()) == count
    with pytest.raises(ValueError, match="EXACT_EXISTING_DISPATCH"):
        learning.eligible_dispatch(store, "unpublished-manual")


def test_empty_and_repeated_preferences_cannot_exceed_existing_ranking_cap():
    from live_contentops.preselection_intelligence_v1 import bounded_learning_preference

    preferences = [{"feature": "topic_family", "preferred_value": "energy"}] * 10
    assert (
        bounded_learning_preference({"topic_family": ["energy"]}, preferences)[0] == 6
    )
    assert (
        bounded_learning_preference(
            {"topic_family": [""]}, [{"feature": "topic_family", "preferred_value": ""}]
        )[0]
        == 0
    )


def test_supplied_intake_tags_reach_bounded_preselection_without_prose_inference():
    from live_contentops.v1_simple_gemini_newsroom_v1 import (
        _candidate_packet_and_preselection,
    )

    rolling = _headlines(2)
    for row in rolling["headlines"]:
        row["source_timestamp_utc"] = CUTOFF
    legacy, _ = _candidate_packet_and_preselection(rolling, [])
    preferred = next(
        r for r in rolling["headlines"] if r["headline_id"] == legacy[-1]["headline_id"]
    )
    preferred["topic_family"] = "energy"
    candidates, evidence = _candidate_packet_and_preselection(
        rolling,
        [],
        learning_policy={
            "policy_version": "CONTROLLED",
            "content": {
                "recommendations": [
                    {"feature": "topic_family", "preferred_value": "energy"}
                ]
            },
        },
    )
    assert candidates[0]["headline_id"] == preferred["headline_id"]
    assert _candidate_packet_and_preselection(rolling, [])[0] == legacy
    assert evidence["candidate_eligibility_changed"] is False


def test_semantic_return_validated_before_sealing_and_backlog_idempotent(tmp_path):
    store, observer, obs, request, response = _observed(tmp_path)
    observer.tool(
        "submit",
        observation_id=obs["observation_id"],
        request_hash=request["request_sha256"],
        response=response,
    )
    observer.advance(obs["observation_id"])
    pending = learning.feedback_judgment(
        store, observation_id=obs["observation_id"], output_dir=tmp_path / "feedback"
    )
    assert pending["request"]["requested_reasoning_effort"] == "low"
    output = {
        "categories": ["SUBSTANTIVE_QUESTION"],
        "follow_up_questions": [
            {
                "record_index": 0,
                "reader_question": response["result"]["interactions"][0]["text"],
            }
        ],
    }
    return_value = {
        "request_sha256": pending["request"]["request_sha256"],
        "output": output,
        "invocation_observation": {
            "surface": "CODEX_NATIVE_SUBAGENT",
            "invocation_id": "CONTROLLED_NO_MODEL",
            "model": "gpt-6.1-sol",
            "reasoning_effort": "low",
            "observation_source": "CONTROLLED_TEST",
        },
    }
    invalid = {
        **return_value,
        "output": {
            **output,
            "follow_up_questions": [
                {
                    "record_index": 0,
                    "reader_question": "Invented question not observed anywhere.",
                }
            ],
        },
    }
    with pytest.raises(ValueError, match="RETURN_SCHEMA"):
        learning.feedback_judgment(
            store,
            observation_id=obs["observation_id"],
            output_dir=tmp_path / "feedback",
            response=invalid,
        )
    result = learning.feedback_judgment(
        store,
        observation_id=obs["observation_id"],
        output_dir=tmp_path / "feedback",
        response=return_value,
    )
    assert result["semantic_judgment_is_metric_truth"] is False
    backlog = learning._rows(store, learning.BACKLOG)
    assert (
        len(backlog) == 1 and backlog[0]["source_pack_required_before_drafting"] is True
    )
    count = len(store.list_outbox_messages())
    learning.feedback_judgment(
        store, observation_id=obs["observation_id"], output_dir=tmp_path / "feedback"
    )
    assert len(store.list_outbox_messages()) == count


def test_freeze_future_policy_manual_brief_and_legacy_packets(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "manual.sqlite3")
    context = learning.learning_context(None)
    context["policy"]["policy_version"] = "policy-A"
    monkeypatch.setattr(
        learning, "learning_context", lambda _: json.loads(json.dumps(context))
    )
    _work(store, "new")
    first = learning.freeze_learning(
        store, source_store=None, run_id="new", published_memory=[{"article": "A"}]
    )
    before = canonical_bytes(first)
    context["policy"]["policy_version"] = "rollback-B"
    assert (
        canonical_bytes(
            learning.freeze_learning(
                store, source_store=None, run_id="new", published_memory=[]
            )
        )
        == before
    )
    work = _work(store, "next")
    learning._put(
        store,
        work,
        learning.BACKLOG,
        {
            "run_id": "new",
            "ranked_questions": [],
            "feedback_effect": "No demand inferred",
        },
    )
    next_context = learning.freeze_learning(
        store, source_store=None, run_id="next", published_memory=[]
    )
    assert next_context["policy"]["policy_version"] == "rollback-B"
    assert len(learning.compact_briefing(next_context)["follow_up_briefs"]) == 1
    _work(store, "legacy")
    turn = NativeDesktopTurn(
        store, run_id="legacy", output_dir=tmp_path, owner_manual_validation=True
    )
    with pytest.raises(DesktopInputRequired):
        turn(
            logical_invocation_id="legacy:select",
            prompt="original",
            governed_input={},
            validator=None,
        )
    old_bytes = canonical_bytes(turn.frozen_request("select"))
    assert (
        learning.freeze_learning(
            store, source_store=None, run_id="legacy", published_memory=[]
        )
        is None
    )
    assert canonical_bytes(turn.frozen_request("select")) == old_bytes


def test_policy_reaches_real_native_selector_writer_seo_and_eight_packages(tmp_path):
    from live_contentops.v1_simple_gemini_newsroom_v1 import (
        run_v1_simple_gemini_newsroom,
    )

    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    _work(store, "controlled")
    turn = NativeDesktopTurn(
        store, run_id="controlled", output_dir=tmp_path, owner_manual_validation=True
    )
    turn.audience_learning = {
        "snapshot_sha256": "a" * 64,
        "policy": {
            "policy_version": "controlled-policy",
            "preference_only": True,
            "content": {"recommendations": []},
            "seo": {
                "recommendations": [
                    {"feature": "title_style", "preferred_value": "question"}
                ]
            },
            "package": {
                "by_destination": {
                    "linkedin": {"recommendations": [{"preferred_value": "mechanism"}]}
                }
            },
        },
        "feedback": [],
        "follow_up_briefs": [],
    }
    args = dict(
        output_dir=tmp_path,
        cutoff_utc=CUTOFF,
        rolling_input=_headlines(1),
        llm_invoke=turn,
        evidence_loader=lambda r: _evidence_result(),
        run_id="controlled",
    )
    for stage in ("select", "write"):
        with pytest.raises(DesktopInputRequired) as caught:
            run_v1_simple_gemini_newsroom(**args)
        request = caught.value.request
        assert request["stage"] == stage
        assert request["governed_input"]["audience_learning"] == turn.audience_learning
        if stage == "select":
            output = _selection(
                request["governed_input"]["candidates"][0]["candidate_id"]
            )
            output["ordered_candidate_plan"][0].update(
                angle="Controlled source-bound financing angle",
                primary_reader_question="Which commitments remain undisclosed?",
                evidence_plan="Use retained primary spans; do not infer commitments.",
            )
        else:
            output = _article_output()
        turn.submit(
            stage,
            {
                "request_sha256": request["request_sha256"],
                "output": output,
                "invocation_observation": {
                    "surface": "CODEX_NATIVE_SUBAGENT",
                    "invocation_id": "CONTROLLED_" + stage,
                    "model": "gpt-6.1-sol",
                    "reasoning_effort": "low" if stage == "select" else "max",
                    "observation_source": "CONTROLLED_TEST_NOT_MODEL_PROOF",
                },
            },
        )
    result = run_v1_simple_gemini_newsroom(**args)
    assert (
        result["qualified_article_count"] == 1
        and result["derivative_intent_count"] == 8
    )
    for filename in (
        "article_manifest_v1.json",
        "native_derivative_previews_v1.json",
        "derivative_intents_v1.json",
    ):
        artifact = json.loads((tmp_path / filename).read_bytes())
        assert (
            artifact["audience_learning_binding"]["policy_version"]
            == "controlled-policy"
        )
    assert json.loads((tmp_path / "run_context_v1.json").read_bytes())[
        "audience_learning_binding"
    ]["preference_only"]
