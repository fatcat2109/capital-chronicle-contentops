from __future__ import annotations

import subprocess
from pathlib import Path

TEST_PATH = Path("tests/test_native_llm_first_daily_app_supervisor_v1.py")
EXPECTED_BLOB = "b038c655a13496409aa1e3eb898e9c459150c05b"


def replace_between(text: str, start: str, end: str, replacement: str) -> str:
    start_index = text.find(start)
    if start_index < 0:
        raise SystemExit(f"start marker missing: {start}")
    end_index = text.find(end, start_index)
    if end_index < 0:
        raise SystemExit(f"end marker missing: {end}")
    return text[:start_index] + replacement + text[end_index:]


def main() -> None:
    actual = subprocess.check_output(["git", "hash-object", str(TEST_PATH)], text=True).strip()
    if actual != EXPECTED_BLOB:
        raise SystemExit(f"test blob drift: {actual} != {EXPECTED_BLOB}")
    text = TEST_PATH.read_text(encoding="utf-8")
    text = replace_between(
        text,
        "def test_primary_only_selection_still_narrows_canonical_prepare(tmp_path: Path):\n",
        "def test_high_admitted_fallback_shortlist_preserves_candidate_continuation(tmp_path: Path):\n",
        '''def test_primary_only_selection_stops_before_canonical_evidence_and_requests_high_worker(\n    tmp_path: Path,\n):\n    cycle_calls = []\n    prevalidation_results = []\n\n    def canonical_cycle(**kwargs):\n        cycle_calls.append(kwargs)\n        return {\n            "classification": "SHOULD_NOT_RUN_BEFORE_WORKER",\n            "public_write_performed": False,\n            "unknown_write_detected": False,\n        }\n\n    supervisor = _supervisor(tmp_path, canonical_cycle)\n    probe = supervisor.prepare_native_desktop_scheduled_opportunity(\n        automation_id="v1-newsroom-london-1700", now=NOW\n    )\n\n    def execute_window(_window, _moment, **_kwargs):\n        result = supervisor._newsroom_cycle(\n            run_id=WINDOW["window_id"],\n            output_dir=tmp_path,\n            cutoff_utc="2026-08-26T11:00:00Z",\n            native_desktop_prepare=True,\n            prepared_candidate_state={"full_frontier_should_not_survive": True},\n            assignment_override=None,\n            story_type_by_cluster=None,\n            publication_enabled=False,\n            operating_mode="SHADOW_ONLY",\n        )\n        prevalidation_results.append(dict(result))\n        return {"executed": True, **dict(result)}\n\n    supervisor._execute_window = execute_window\n    result = supervisor.prepare_native_desktop_scheduled_opportunity(\n        automation_id="v1-newsroom-london-1700",\n        now=NOW + timedelta(minutes=5),\n        coordinator_selection=_selection_from_probe(probe),\n    )\n\n    assert result["classification"] == "NO_PUBLICATION"\n    assert result["public_write_performed"] is False\n    assert result["unknown_write_detected"] is False\n    assert cycle_calls == []\n    assert len(prevalidation_results) == 1\n    prepared = prevalidation_results[0]\n    assert prepared["exact_next_blocker"] == "EDITORIAL_WORKER_UNAVAILABLE_OR_INVALID"\n    assert prepared["native_llm_first_assignment_override_reused"] is True\n    assert prepared["full_universe_semantic_assignment_on_critical_path"] is False\n    assert prepared["evidence_acquisition_requests"] == 0\n    assert prepared["grounded_locator_model_invocations"] == 0\n    assert prepared["native_llm_first_prevalidation"][\n        "worker_precedes_evidence_acquisition"\n    ] is True\n    route = prepared["editorial_worker_routing"]\n    assert route["native_llm_first"] is True\n    assert route["actual_reasoning_effort"] == "HIGH"\n    worker_request = route["worker_request"]\n    assert worker_request["candidate_cluster_id"] == "cluster-b"\n    assert worker_request["fresh"] is True\n    assert worker_request["isolated"] is True\n    assert worker_request["resume_existing"] is False\n    assert worker_request["reasoning_effort"] == "high"\n    assignment = prepared["assignment"]\n    assert assignment["selected_cluster_id"] == "cluster-b"\n    assert assignment["selected_cluster_ids"] == ["cluster-b"]\n    assert assignment["selected_headline_ids"] == ["headline-b"]\n    assert [row["cluster_id"] for row in assignment["ranked_clusters"]] == ["cluster-b"]\n    assert prepared["intake"]["unique_headline_ids"] == ["headline-b"]\n    assert (tmp_path / "native_llm_first_prevalidation_v1.json").is_file()\n\n\n''',
    )
    text = replace_between(
        text,
        "def test_complete_phase_reuses_narrow_assignment_and_drops_old_semantic_checkpoints(tmp_path: Path):\n",
        "def test_native_pending_handoff_uses_assignment_resume_not_probe_semantic_checkpoint(\n",
        '''def test_complete_phase_requires_post_generation_verified_external_provider(\n    tmp_path: Path,\n):\n    cycle_calls = []\n    supervisor = _supervisor(\n        tmp_path,\n        lambda **kwargs: cycle_calls.append(kwargs)\n        or {"classification": "PASS_PUBLICATION_PLAN_READY"},\n    )\n    state = _pool_valid_prepared_state()\n    artifact = supervisor._build_selection_artifact(\n        task_id="v1-newsroom-london-1700",\n        session="london_1700_bangkok",\n        moment=NOW,\n        window=WINDOW,\n        prepared_state=state,\n    )\n    request = artifact["coordinator_request"]\n    selection = supervisor._validate_selection_return(\n        {\n            "schema_version": SELECTION_RETURN_SCHEMA_VERSION,\n            "canonical_opportunity_id": WINDOW["window_id"],\n            "selection_request_logical_hash": request["selection_request_logical_hash"],\n            "selected_cluster_id": "cluster-b",\n            "article_mode": "STANDARD_NEWS_ANALYSIS",\n            "selection_rationale": "B is useful.",\n            "fallback_candidates": [],\n            "model": COORDINATOR_MODEL,\n            "reasoning_effort": "HIGH",\n            "public_write_attempted": False,\n        },\n        artifact,\n    )\n    binding = supervisor._selected_assignment_binding(artifact=artifact, selection=selection)\n    token = supervisor._native_selection_binding.set({**binding, "phase": "COMPLETE"})\n    try:\n        with pytest.raises(\n            ValueError, match="native_llm_first_external_provider_required_for_complete"\n        ):\n            supervisor._native_llm_first_newsroom_cycle(\n                run_id="resume",\n                output_dir=tmp_path,\n                cutoff_utc="2026-08-26T11:00:00Z",\n                rolling_input=binding["rolling_input_override"],\n                prepared_candidate_state={"must": "drop"},\n                leaf_checkpoints={"old": {"must": "drop"}},\n                global_checkpoint={"old": "must_drop"},\n                story_type_by_cluster={"wrong": "value"},\n                publication_enabled=False,\n            )\n    finally:\n        supervisor._native_selection_binding.reset(token)\n    assert cycle_calls == []\n\n\n''',
    )
    TEST_PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
