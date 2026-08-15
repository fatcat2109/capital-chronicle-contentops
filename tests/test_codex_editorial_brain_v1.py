import json
from pathlib import Path

import pytest

from live_contentops import codex_editorial_brain_v1 as brain


def _governed_input(*, cluster_id="cluster-1"):
    return {
        "schema_version": "contentops.rolling_x_grounded_article_media_builder.v1",
        "cluster_id": cluster_id,
        "headline_ids": ["headline-1"],
        "effective_article_mode": "BREAKING_BRIEF",
        "evidence_documents": [
            {
                "source_handle": "SOURCE_1",
                "document_id": "document-1",
                "title": "Retail sales report",
                "publisher": "Reuters",
                "canonical_content_text": "Retail sales rose in July while one category weakened.",
            }
        ],
        "supported_claims": [
            {
                "claim_id": "fact-1",
                "claim_text": "Retail sales rose in July while one category weakened.",
                "evidence_document_ids": ["document-1"],
            }
        ],
        "omitted_unsupported_claims": [],
        "visual_asset_ids": [],
        "evidence_substance": {"enough_for_useful_article": True},
    }


def _job(*, cluster_id="cluster-1"):
    return brain.build_codex_article_job(
        governed_input=_governed_input(cluster_id=cluster_id),
        work_item_id="work-1",
        candidate_rank=1,
        evaluation_cutoff="2026-08-15T12:00:00Z",
    )


def _output(*, body=None, handle="SOURCE_1", document_id="document-1"):
    body = body if body is not None else (
        f"Retail sales rose in July, [[SOURCE:{handle}]] reported, while one category weakened. "
        "That split is the useful detail: the headline direction was positive, but the underlying "
        "report did not describe uniform strength.\n\n"
        "The result matters because it distinguishes a broad monthly increase from a claim that "
        "every category improved. The supplied report leaves the next monthly reading unresolved."
    )
    return {
        "title": "Retail Sales Rose in July, but the Detail Was Uneven",
        "subtitle": "The report showed a positive headline with a weaker category underneath.",
        "seo_title": "Retail Sales Rose in July",
        "meta_description": "Retail sales rose in July, while the report showed uneven detail.",
        "market_mechanism": "",
        "policy_context": "",
        "cross_asset_implications": "",
        "social_lede": "Retail sales rose in July, but the detail was uneven.",
        "social_mechanism_summary": "",
        "social_policy_summary": "",
        "social_cross_asset_summary": "",
        "substack_body_markdown": body,
        "source_handles_used": [handle],
        "evidence_document_ids": [document_id],
        "explicit_inferences": [],
        "self_review_summary": "States the news once, uses one bound source, and avoids unsupported numbers.",
        "abstain_reason": None,
    }


def _execution(output, *, execution_id="exec-1", classification="SUCCESS", exit_code=0):
    return {
        "exit_classification": classification,
        "exit_code": exit_code,
        "wall_time_seconds": 1.25,
        "timeout_seconds": 10.0,
        "fresh_execution_id": execution_id,
        "effective_model": None,
        "usage": {"input_tokens": 100, "output_tokens": 50},
        "tool_event_counts": {
            "command_executions": 0,
            "web_searches": 0,
            "mcp_tool_calls": 0,
            "file_changes": 0,
            "browser_calls": 0,
        },
        "output": output,
    }


def _pass_validator(_output):
    return {
        "classification": "PASS",
        "editorial_failure_codes": [],
        "forbidden_failure_codes": [],
    }


def test_job_is_hash_bound_url_free_and_output_schema_is_strict():
    governed = _governed_input()
    governed["nested_source_metadata"] = {
        "reader_source_url": "https://example.invalid/not-for-codex"
    }
    job = brain.build_codex_article_job(
        governed_input=governed,
        work_item_id="work-1",
        candidate_rank=1,
        evaluation_cutoff="2026-08-15T12:00:00Z",
    )

    assert job["job_id"].startswith("codex-editorial-")
    assert job["allowed_source_handles"] == ["SOURCE_1"]
    assert job["allowed_evidence_document_ids"] == ["document-1"]
    assert "url" not in json.dumps(job["governed_writer_input"]).casefold()
    schema = brain.article_output_json_schema()
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == set(schema["properties"])


def test_job_rejects_url_embedded_in_non_url_evidence_text() -> None:
    governed = _governed_input()
    governed["evidence_documents"][0]["canonical_content_text"] += (
        " See https://example.invalid/not-for-codex."
    )

    with pytest.raises(brain.CodexEditorialBrainError, match="CODEX_JOB_URL_FREE_CONTRACT_FAILED"):
        brain.build_codex_article_job(
            governed_input=governed,
            work_item_id="work-1",
            candidate_rank=1,
        )


def test_completed_job_is_reused_without_duplicate_execution(tmp_path):
    calls = []

    def adapter(request):
        calls.append(request)
        return _execution(_output())

    kwargs = {
        "job": _job(),
        "opportunity_output_dir": tmp_path / "opportunity",
        "runtime_root": tmp_path / "runtime",
        "deterministic_validator": _pass_validator,
        "execution_adapter": adapter,
        "timeout_seconds": 10,
    }
    first = brain.run_codex_editorial_brain_job(**kwargs)
    second = brain.run_codex_editorial_brain_job(**kwargs)

    assert len(calls) == 1
    assert first["completed_receipt_reused"] is False
    assert second["completed_receipt_reused"] is True
    assert first["receipt"]["governed_input_sha256"] == _job()["governed_input_sha256"]
    assert first["receipt"]["revision_count"] == 0
    assert calls[0].requested_model == "gpt-5.6-sol"
    assert calls[0].requested_reasoning_effort == "xhigh"
    assert first["receipt"]["requested_model"] == "gpt-5.6-sol"
    assert first["receipt"]["requested_reasoning_effort"] == "xhigh"


def test_effective_model_or_effort_mismatch_blocks_without_substitution(tmp_path):
    def adapter(_request):
        execution = _execution(_output())
        execution["effective_model"] = "gpt-5.4"
        execution["effective_reasoning_effort"] = "high"
        return execution

    with pytest.raises(
        brain.CodexEditorialBrainError,
        match=brain.AUTONOMOUS_SEAM_BLOCKER,
    ):
        brain.run_codex_editorial_brain_job(
            job=_job(),
            opportunity_output_dir=tmp_path / "opportunity",
            runtime_root=tmp_path / "runtime",
            deterministic_validator=_pass_validator,
            execution_adapter=adapter,
        )


def test_second_job_for_same_opportunity_is_blocked(tmp_path):
    first_job = _job()
    second_job = brain.build_codex_article_job(
        governed_input=_governed_input(cluster_id="cluster-2"),
        work_item_id="work-1",
        candidate_rank=2,
    )
    calls = []

    def adapter(request):
        calls.append(request)
        return _execution(_output())

    brain.run_codex_editorial_brain_job(
        job=first_job,
        opportunity_output_dir=tmp_path / "opportunity",
        runtime_root=tmp_path / "runtime",
        deterministic_validator=_pass_validator,
        execution_adapter=adapter,
    )
    with pytest.raises(brain.CodexEditorialBrainError, match="SECOND_CODEX_EDITORIAL_JOB_BLOCKED"):
        brain.run_codex_editorial_brain_job(
            job=second_job,
            opportunity_output_dir=tmp_path / "opportunity",
            runtime_root=tmp_path / "runtime",
            deterministic_validator=_pass_validator,
            execution_adapter=adapter,
        )
    assert len(calls) == 1


def test_one_editorial_revision_is_allowed_and_no_more(tmp_path):
    calls = []
    schema_invalid = _output(body="")
    schema_invalid["source_handles_used"] = []
    schema_invalid["evidence_document_ids"] = []
    outputs = [schema_invalid, _output()]

    def adapter(request):
        calls.append(request)
        return _execution(outputs.pop(0), execution_id=f"exec-{len(calls)}")

    result = brain.run_codex_editorial_brain_job(
        job=_job(),
        opportunity_output_dir=tmp_path / "opportunity",
        runtime_root=tmp_path / "runtime",
        deterministic_validator=_pass_validator,
        execution_adapter=adapter,
    )

    assert len(calls) == 2
    assert result["receipt"]["revision_count"] == 1
    assert "single permitted revision" in calls[1].prompt


def test_evidence_qualified_abstention_receives_the_one_revision(tmp_path):
    calls = []
    abstention = _output(body="")
    abstention.update(
        {
            "source_handles_used": [],
            "evidence_document_ids": ["document-1"],
            "abstain_reason": "The extract is short.",
        }
    )
    outputs = [abstention, _output()]

    def adapter(request):
        calls.append(request)
        return _execution(outputs.pop(0), execution_id=f"exec-{len(calls)}")

    result = brain.run_codex_editorial_brain_job(
        job=_job(),
        opportunity_output_dir=tmp_path / "opportunity",
        runtime_root=tmp_path / "runtime",
        deterministic_validator=_pass_validator,
        execution_adapter=adapter,
    )

    assert len(calls) == 2
    assert result["receipt"]["revision_count"] == 1
    assert "CODEX_OUTPUT_ABSTAINED" in calls[1].prompt


def test_forbidden_source_or_url_failure_gets_no_revision(tmp_path):
    calls = []
    invalid = _output(
        body="Retail sales rose, [[SOURCE:SOURCE_9]] said. https://example.invalid/new",
        handle="SOURCE_9",
        document_id="invented-document",
    )

    def adapter(request):
        calls.append(request)
        return _execution(invalid)

    with pytest.raises(brain.CodexEditorialBrainError, match="CODEX_EDITORIAL_OUTPUT_REJECTED") as raised:
        brain.run_codex_editorial_brain_job(
            job=_job(),
            opportunity_output_dir=tmp_path / "opportunity",
            runtime_root=tmp_path / "runtime",
            deterministic_validator=_pass_validator,
            execution_adapter=adapter,
        )

    assert len(calls) == 1
    assert raised.value.receipt["revision_count"] == 0
    assert raised.value.receipt["validation_result"]["classification"] == "FAIL_FORBIDDEN"


def test_url_or_unknown_source_inside_inference_is_forbidden(tmp_path):
    invalid = _output()
    invalid["explicit_inferences"] = [{
        "label": "INFERENCE",
        "text": "See https://example.invalid/new for an unsupported extension.",
        "source_handles": ["SOURCE_9"],
        "evidence_document_ids": ["invented-document"],
    }]
    calls = []

    def adapter(request):
        calls.append(request)
        return _execution(invalid)

    with pytest.raises(brain.CodexEditorialBrainError, match="CODEX_EDITORIAL_OUTPUT_REJECTED") as raised:
        brain.run_codex_editorial_brain_job(
            job=_job(),
            opportunity_output_dir=tmp_path / "opportunity",
            runtime_root=tmp_path / "runtime",
            deterministic_validator=_pass_validator,
            execution_adapter=adapter,
        )

    assert len(calls) == 1
    failures = raised.value.receipt["validation_result"]["forbidden_failure_codes"]
    assert "CODEX_OUTPUT_INVENTED_URL" in failures
    assert "CODEX_OUTPUT_UNKNOWN_SOURCE_HANDLE" in failures
    assert "CODEX_OUTPUT_UNKNOWN_EVIDENCE_DOCUMENT_ID" in failures


def test_timeout_is_terminal_and_restart_does_not_duplicate(tmp_path):
    calls = []

    def adapter(request):
        calls.append(request)
        return _execution(None, classification="TIMEOUT", exit_code=None)

    kwargs = {
        "job": _job(),
        "opportunity_output_dir": tmp_path / "opportunity",
        "runtime_root": tmp_path / "runtime",
        "deterministic_validator": _pass_validator,
        "execution_adapter": adapter,
    }
    with pytest.raises(brain.CodexEditorialBrainError, match="CODEX_EDITORIAL_EXECUTION_FAILED"):
        brain.run_codex_editorial_brain_job(**kwargs)
    with pytest.raises(brain.CodexEditorialBrainError, match="CODEX_JOB_ALREADY_TERMINAL_OR_INCOMPLETE"):
        brain.run_codex_editorial_brain_job(**kwargs)
    assert len(calls) == 1


def test_failed_output_can_be_revalidated_without_a_new_codex_execution(tmp_path):
    calls = []

    def adapter(request):
        calls.append(request)
        return _execution(_output())

    def stale_validator(_output):
        return {
            "classification": "FAIL_FORBIDDEN",
            "editorial_failure_codes": [],
            "forbidden_failure_codes": ["STALE_VALIDATOR_FALSE_POSITIVE"],
        }

    kwargs = {
        "job": _job(),
        "opportunity_output_dir": tmp_path / "opportunity",
        "runtime_root": tmp_path / "runtime",
        "execution_adapter": adapter,
    }
    with pytest.raises(brain.CodexEditorialBrainError, match="CODEX_EDITORIAL_OUTPUT_REJECTED"):
        brain.run_codex_editorial_brain_job(
            **kwargs, deterministic_validator=stale_validator
        )
    recovered = brain.run_codex_editorial_brain_job(
        **kwargs, deterministic_validator=_pass_validator
    )

    assert len(calls) == 1
    assert recovered["completed_receipt_reused"] is True
    assert recovered["receipt"]["deterministic_revalidation_only"] is True
    assert recovered["receipt"]["new_codex_execution_during_revalidation"] is False
    assert len(recovered["receipt"]["executions"]) == 1


def test_packaged_cli_can_be_materialized_to_runtime_cache(monkeypatch, tmp_path):
    source = tmp_path / "package" / "codex.exe"
    source.parent.mkdir()
    source.write_bytes(b"official-codex-cli-bytes")

    def probe(path: Path):
        return ("cli_cache" in path.parts, "codex-cli test")

    monkeypatch.setattr(brain, "_probe_executable", probe)
    executable, receipt = brain.resolve_codex_executable(
        runtime_root=tmp_path / "runtime", explicit_path=source
    )

    assert executable.read_bytes() == source.read_bytes()
    assert receipt["materialized_runtime_copy"] is True
    assert receipt["sha256"] == brain._sha256_file(source)


def test_child_environment_does_not_inherit_provider_secrets(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-leak")
    monkeypatch.setenv("NINE_ROUTER_API_KEY", "must-not-leak")
    monkeypatch.setenv("PATH", "safe-path")

    child = brain._safe_child_environment()

    assert child["PATH"] == "safe-path"
    assert "OPENAI_API_KEY" not in child
    assert "NINE_ROUTER_API_KEY" not in child
