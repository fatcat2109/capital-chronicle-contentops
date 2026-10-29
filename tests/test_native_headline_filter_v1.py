"""Controlled lifecycle checks, not evidence of native model quality."""
import json
import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired, NativeDesktopTurn


def _turn(tmp_path, run="filter-test"):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title="test", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    return NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)


def _rows(count=65):
    return {"headlines": [{"headline_id": str(i), "source_timestamp_utc": "2026-10-20T00:00:00Z",
        "external_content": {"headline_text": "retained controlled item " + str(i),
                             "url_or_source_ref": "https://x.com/test/status/" + str(i)}} for i in range(count)]}


def _answer(turn, request, *, effort="max", model="gpt-6-luna"):
    decisions = [{"input_sha256": r["input_sha256"], "headline_id": r["original_record"]["headline_id"],
                  "decision": "KEEP", "reason": "controlled relevant item", "group_key": "test", "novelty": "new"}
                 for r in request["governed_input"]["records"]]
    return turn.submit(request["stage"], {"request_sha256": request["request_sha256"],
        "output": {"schema_version": "contentops.native_headline_filter.v1", "decisions": decisions,
                   "public_write_attempted": False},
        "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "invocation_id": "controlled-test-only",
            "observation_source": "UNIT_TEST_NOT_MODEL_PROOF", "model": model, "reasoning_effort": effort}})


def _finish(turn, rows):
    requests = []
    while True:
        try:
            result = turn.filter_headlines(rows)
            return result, requests
        except DesktopInputRequired as pending:
            requests.append(pending.request)
            _answer(turn, pending.request)


def test_all_backlog_beyond_32_resume_and_correction_only(tmp_path):
    rows = _rows()
    (filtered, receipt), requests = _finish(_turn(tmp_path), rows)
    assert [len(r["governed_input"]["records"]) for r in requests] == [24, 24, 17]
    assert receipt["seen"] == receipt["kept"] == len(filtered["headlines"]) == 65
    assert receipt["remaining_unprocessed"] == 0
    before = len(_turn(tmp_path).store.list_outbox_messages())
    replay, no_requests = _finish(_turn(tmp_path), rows)
    assert no_requests == [] and replay == (filtered, receipt)
    assert len(_turn(tmp_path).store.list_outbox_messages()) == before
    # Different opportunity reuses exact decisions; one corrected record requests only itself.
    rows["headlines"][0]["correction_of"] = "retained-original"
    rows["headlines"][0]["external_content"]["headline_text"] += " correction"
    (_, corrected), requests = _finish(_turn(tmp_path, "next-opportunity"), rows)
    assert len(requests) == 1 and len(requests[0]["governed_input"]["records"]) == 1
    assert corrected["seen"] == 65


def test_three_frozen_batches_ready_together_and_all_returns_still_required(tmp_path):
    turn=_turn(tmp_path)
    with pytest.raises(DesktopInputRequired) as first:
        turn.filter_headlines(_rows(97))
    requests=first.value.request["parallel_requests"]
    assert len(requests)==3 and first.value.request["filter_progress"]["remaining_unprocessed"]==97
    for request in reversed(requests):
        _answer(turn,request)
    with pytest.raises(DesktopInputRequired) as next_batch:
        turn.filter_headlines(_rows(97))
    assert next_batch.value.request["filter_progress"]["accepted_records"]==72
    assert next_batch.value.request["filter_progress"]["remaining_unprocessed"]==25
    for request in next_batch.value.request["parallel_requests"]:
        _answer(turn,request)
    (_,receipt),requests=_finish(turn,_rows(97))
    assert requests==[] and receipt["seen"]==97 and receipt["remaining_unprocessed"]==0


def test_role_model_effort_fail_closed(tmp_path):
    turn = _turn(tmp_path)
    with pytest.raises(DesktopInputRequired) as pending:
        turn.filter_headlines(_rows(1))
    with pytest.raises(ValueError, match="EFFORT_MISMATCH"):
        _answer(turn, pending.value.request, effort="low")
    with pytest.raises(ValueError, match="MODEL_MISMATCH"):
        _answer(turn, pending.value.request, model="gpt-6.1-sol")


def test_pending_scheduled_filter_resumes_canonical_pool_without_replacing_request(tmp_path, monkeypatch):
    from live_contentops import llm_operator_control_v1 as control
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes
    monkeypatch.setattr(control, "assert_llm_operator_execution_enabled", lambda: None)
    turn = _turn(tmp_path, "scheduled-pending")
    turn.owner_manual_validation = False
    rows = _rows(3)
    with pytest.raises(DesktopInputRequired) as first:
        turn.filter_headlines(rows)
    request = first.value.request
    original_bytes = (tmp_path / ("desktop_request_" + request["stage"] + ".json")).read_bytes()
    # The actual scheduled pool round-trip changes insertion order, not values.
    restarted_rows = json.loads(canonical_bytes(rows))
    with pytest.raises(DesktopInputRequired) as resumed:
        turn.filter_headlines(restarted_rows)
    assert resumed.value.request == request
    assert (tmp_path / ("desktop_request_" + request["stage"] + ".json")).read_bytes() == original_bytes
    _answer(turn, request)
    _, receipt = turn.filter_headlines(restarted_rows)
    assert receipt["seen"] == 3 and receipt["remaining_unprocessed"] == 0
    # A corrupted saved prompt still fails against its immutable request hash.
    key = turn._key(request["stage"], "request")
    changed = turn.frozen_request(request["stage"])
    changed["prompt"] += " changed"
    with turn.store.get_connection() as connection:
        connection.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?", (canonical_bytes(changed).decode(), key))
    with pytest.raises(ValueError, match="IMMUTABLE_RETURN_CONFLICT"):
        turn.filter_headlines(restarted_rows)


def test_accepted_batch_recovers_interruption_before_decision_materialization(tmp_path, monkeypatch):
    turn = _turn(tmp_path)
    with pytest.raises(DesktopInputRequired) as pending:
        turn.filter_headlines(_rows(3))
    _answer(turn, pending.value.request)
    # Accepted native return exists; zero per-record rows exist yet.
    assert not any(r["message_id"].startswith("native-filter-decision-") for r in turn.store.list_outbox_messages())
    (_, receipt), requests = _finish(_turn(tmp_path), _rows(3))
    assert requests == [] and receipt["seen"] == 3
    observations = _turn(tmp_path).telemetry()
    assert observations["semantic_response_count"] == 1
    assert observations["observed_models"] == ["gpt-6-luna"]
    assert observations["cost_usd"] is None


def test_explicit_correction_survives_intake_and_published_title_dedupe(tmp_path):
    from live_contentops.newsroom_assignment_scheduler_v1 import load_rolling_x_headline_sidecars
    from live_contentops.v1_simple_gemini_newsroom_v1 import _candidate_universe, _selection_candidate
    source = {"headline_id": "original", "tweet_id": "123", "headline_timestamp": "2026-10-20T00:00:00Z",
              "headline_text": "Controlled attributed macro development", "tweet_url": "https://x.com/test/status/123"}
    correction = {**source, "correction_of": "original", "revision_id": "correction-1",
                  "revision_at_utc": "2026-10-20T00:30:00Z", "update_chain_identity": "same-story"}
    path = tmp_path / "sidecar.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in [source, source, correction]))
    result = load_rolling_x_headline_sidecars(cutoff_utc="2026-10-20T01:00:00Z", sidecar_glob=str(path))
    assert len(result["headlines"]) == 2 and result["counts"]["duplicates"] == 1
    candidates = _candidate_universe(result, [{"title": source["headline_text"]}])
    assert len(candidates) == 1
    selected = _selection_candidate(candidates[0])
    assert selected["correction_of"] == "original" and selected["update_chain_identity"] == "same-story"
    ordinary = {**result["headlines"][0], "revision_at_utc": "2026-10-20T00:30:00Z"}
    assert _candidate_universe({"headlines": [ordinary]}, [{"title": source["headline_text"]}]) == []


def test_repair_requires_the_same_actual_writer_invocation(tmp_path):
    turn = _turn(tmp_path)
    turn._put("write", "response", {"invocation_observation": {"invocation_id": "actual-writer"}})
    turn._put("revise", "request", {"request_sha256": "exact-request"})
    with pytest.raises(ValueError, match="SAME_WRITER"):
        turn.submit("revise", {"request_sha256": "exact-request", "output": {},
            "invocation_observation": {"surface": "CODEX_NATIVE_SUBAGENT", "model": "gpt-6.1-sol",
                "reasoning_effort": "max", "invocation_id": "different-writer", "observation_source": "CONTROLLED_TEST"}})
