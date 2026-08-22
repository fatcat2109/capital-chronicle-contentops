from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from live_contentops.official_codex_provider_v1 import (
    AUTH_CLASSIFICATION,
    EFFORT,
    MODEL,
    TRANSPORT_SCHEMA,
    OfficialCodexEditorialSession,
    OfficialCodexEditorialArticleBuilder,
    OfficialCodexProviderError,
)


class _FakeThread:
    def __init__(self, responses, *, metadata_failure=False):
        self.id = "sensitive-thread-id-never-persisted"
        self.responses = list(responses)
        self.run_calls = []
        self.read_calls = []
        self.metadata_failure = metadata_failure

    def run(self, prompt, **kwargs):
        self.run_calls.append((prompt, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response

    def read(self, *, include_turns):
        self.read_calls.append(include_turns)
        if self.metadata_failure:
            raise RuntimeError("sanitized post-turn metadata failure")
        return SimpleNamespace(
            thread=SimpleNamespace(ephemeral=True, cli_version="0.147.0")
        )


class _FakeCodex:
    def __init__(self, responses, *, account_type="chatgpt", metadata_failure=False):
        self.thread = _FakeThread(responses, metadata_failure=metadata_failure)
        self.account_type = account_type
        self.thread_start_calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        del exc_type, exc, traceback

    def account(self, *, refresh_token):
        assert refresh_token is False
        return SimpleNamespace(
            account=SimpleNamespace(root=SimpleNamespace(type=self.account_type))
        )

    def models(self, *, include_hidden):
        assert include_hidden is False
        effort = SimpleNamespace(reasoning_effort=EFFORT)
        return SimpleNamespace(
            data=[SimpleNamespace(id=MODEL, supported_reasoning_efforts=[effort])]
        )

    def thread_start(self, **kwargs):
        self.thread_start_calls.append(kwargs)
        return self.thread


def _sdk_factory(fake):
    approval = SimpleNamespace(deny_all="deny_all")
    sandbox = SimpleNamespace(read_only="read_only")
    efforts = SimpleNamespace(xhigh="xhigh")
    return lambda: (fake, approval, sandbox, efforts, "0.147.0")


def _turn(article, *, final_response=None):
    envelope = {"article_json": json.dumps(article)}
    return SimpleNamespace(
        status="completed",
        error=None,
        final_response=final_response or json.dumps(envelope),
        items=[],
        usage=SimpleNamespace(
            total=SimpleNamespace(
                input_tokens=10,
                cached_input_tokens=1,
                cache_write_input_tokens=0,
                output_tokens=20,
                reasoning_output_tokens=5,
                total_tokens=30,
            )
        ),
        duration_ms=123,
    )


def _run(
    session,
    *,
    prompt="bounded prompt",
    role="V1_FINAL_EDITORIAL_WRITER",
    revision=False,
):
    return session.run(
        prompt=prompt,
        developer_instructions="bounded developer contract",
        governed_input_hash="a" * 64,
        evidence_hash="b" * 64,
        role=role,
        revision=revision,
    )


def test_chatgpt_auth_only_explicit_model_effort_and_read_only_ephemeral_thread(
    tmp_path,
):
    fake = _FakeCodex([_turn({"title": "Italy"})])
    session = OfficialCodexEditorialSession(
        proof_cwd=tmp_path / "cwd", sdk_factory=_sdk_factory(fake), environment={}
    )

    assert session.preflight()["auth_classification"] == AUTH_CLASSIFICATION
    result = _run(session)

    assert result.output == {"title": "Italy"}
    assert len(fake.thread_start_calls) == 1
    start = fake.thread_start_calls[0]
    assert start["ephemeral"] is True
    assert start["model"] == MODEL
    assert start["sandbox"] == "read_only"
    assert start["approval_mode"] == "deny_all"
    run_kwargs = fake.thread.run_calls[0][1]
    assert run_kwargs["effort"] == EFFORT
    assert run_kwargs["output_schema"] == TRANSPORT_SCHEMA
    assert result.receipt["api_key_fallback_calls"] == 0
    assert result.receipt["turn_result_is_primary_authority"] is True
    assert result.receipt["turn_result_usage"]["total_tokens"] == 30
    assert result.receipt["turn_result_duration_ms"] == 123
    assert fake.thread.read_calls == [False]


def test_api_key_presence_and_non_chatgpt_auth_fail_closed_without_fallback(tmp_path):
    fake = _FakeCodex([])
    with pytest.raises(OfficialCodexProviderError) as api_error:
        OfficialCodexEditorialSession(
            proof_cwd=tmp_path / "key",
            sdk_factory=_sdk_factory(fake),
            environment={"OPENAI_API_KEY": "not-inspected"},
        ).preflight()
    assert api_error.value.phase == "AUTH_PREFLIGHT"

    non_chatgpt = _FakeCodex([], account_type="apiKey")
    with pytest.raises(OfficialCodexProviderError) as auth_error:
        OfficialCodexEditorialSession(
            proof_cwd=tmp_path / "auth",
            sdk_factory=_sdk_factory(non_chatgpt),
            environment={},
        ).preflight()
    assert auth_error.value.phase == "AUTH_PREFLIGHT"
    assert "FALLBACK_FORBIDDEN" in auth_error.value.code


def test_turn_result_remains_primary_when_metadata_only_readback_fails(tmp_path):
    fake = _FakeCodex([_turn({"title": "Italy"})], metadata_failure=True)
    session = OfficialCodexEditorialSession(
        proof_cwd=tmp_path / "cwd", sdk_factory=_sdk_factory(fake), environment={}
    )

    result = _run(session)

    assert result.output["title"] == "Italy"
    assert result.receipt["turn_result_status"] == "completed"
    assert result.receipt["post_turn_metadata_phase"] == "POST_TURN_METADATA_READBACK"
    assert result.receipt["post_turn_metadata_status"] == (
        "FAILED_POST_TURN_METADATA_READBACK"
    )
    assert result.receipt["model_turn_completed"] is True
    assert fake.thread.read_calls == [False]


def test_native_strict_schema_and_structured_output_phase_fail_closed(tmp_path):
    malformed = _turn({}, final_response=json.dumps({"unexpected": "value"}))
    fake = _FakeCodex([malformed])
    session = OfficialCodexEditorialSession(
        proof_cwd=tmp_path / "cwd", sdk_factory=_sdk_factory(fake), environment={}
    )

    with pytest.raises(OfficialCodexProviderError) as caught:
        _run(session)

    assert caught.value.phase == "STRUCTURED_OUTPUT"
    assert caught.value.model_turn_completed is True
    assert fake.thread.run_calls[0][1]["output_schema"]["additionalProperties"] is False


def test_one_revision_resumes_same_thread_and_exact_duplicate_is_blocked(tmp_path):
    fake = _FakeCodex([_turn({"title": "Initial"}), _turn({"title": "Revised"})])
    session = OfficialCodexEditorialSession(
        proof_cwd=tmp_path / "cwd", sdk_factory=_sdk_factory(fake), environment={}
    )

    first = _run(session)
    second = _run(
        session,
        prompt="bounded revision prompt",
        role="V1_FINAL_EDITORIAL_REVISION",
        revision=True,
    )

    assert first.receipt["thread_id_hash"] == second.receipt["thread_id_hash"]
    assert second.receipt["same_thread_revision"] is True
    assert len(fake.thread_start_calls) == 1
    assert len(fake.thread.run_calls) == 2

    duplicate_fake = _FakeCodex([_turn({"title": "Once"})])
    duplicate_session = OfficialCodexEditorialSession(
        proof_cwd=tmp_path / "dedup",
        sdk_factory=_sdk_factory(duplicate_fake),
        environment={},
    )
    _run(duplicate_session)
    with pytest.raises(OfficialCodexProviderError) as caught:
        _run(duplicate_session)
    assert caught.value.code == "DUPLICATE_LOGICAL_PROVIDER_CALL_BLOCKED"
    assert len(duplicate_fake.thread.run_calls) == 1


def test_local_product_validation_uses_one_same_thread_repair_and_persists_receipts(
    tmp_path, monkeypatch
):
    from live_contentops import (
        rolling_x_grounded_article_media_builder_v1 as article_module,
    )

    fake = _FakeCodex([_turn({"title": "Initial"}), _turn({"title": "Revised"})])
    build_calls = []

    def fake_product_builder(viability, *, output_dir, article_generator):
        del viability, output_dir
        article = dict(article_generator("bounded article prompt"))
        build_calls.append(article["title"])
        if len(build_calls) == 1:
            raise article_module.GroundedArticleBuilderError(
                "structured_data_description_mismatch"
            )
        return {
            "article": article,
            "media": {"assets": []},
            "critical_path_telemetry": {},
        }

    monkeypatch.setattr(
        article_module,
        "build_rolling_x_grounded_article_and_media",
        fake_product_builder,
    )
    builder = OfficialCodexEditorialArticleBuilder(
        output_dir=tmp_path,
        sdk_factory=_sdk_factory(fake),
        environment={},
    )
    viability = {
        "editorial_worker_request": {
            "model": MODEL,
            "reasoning_effort": EFFORT.upper(),
            "fresh": True,
            "isolated": True,
            "governed_input_hash": "a" * 64,
            "bounded_governed_context": {
                "accepted_evidence_packet": {"status": "PASS"}
            },
        }
    }

    built = builder(viability)

    assert build_calls == ["Initial", "Revised"]
    assert len(fake.thread_start_calls) == 1
    assert len(fake.thread.run_calls) == 2
    receipt = built["editorial_worker_receipt"]
    assert receipt["bounded_revision_count"] == 1
    assert receipt["same_worker_local_validation_revision"] is True
    assert built["critical_path_telemetry"]["official_codex_direct_provider_calls"] == 2
    assert (tmp_path / "official_codex_turn_receipt_v1.json").is_file()
    assert (tmp_path / "official_codex_turn_receipt_revision_1_v1.json").is_file()


@pytest.mark.parametrize(
    ("failure", "phase"),
    [
        (TimeoutError("timeout"), "TIMEOUT"),
        (RuntimeError("rate limit"), "RATE_LIMIT"),
        (RuntimeError("context length limit"), "CONTEXT_LIMIT"),
        (ConnectionError("connection failed"), "APP_SERVER_TRANSPORT"),
    ],
)
def test_turn_failure_phase_taxonomy(tmp_path, failure, phase):
    fake = _FakeCodex([failure])
    session = OfficialCodexEditorialSession(
        proof_cwd=tmp_path / phase, sdk_factory=_sdk_factory(fake), environment={}
    )
    with pytest.raises(OfficialCodexProviderError) as caught:
        _run(session)
    assert caught.value.phase == phase
