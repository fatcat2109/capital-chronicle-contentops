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
from live_contentops.capital_chronicle_institutional_edge_v1 import (
    build_institutional_edge_editorial_packet,
)
from live_contentops.codex_desktop_newsroom_operator_v1 import (
    validate_editorial_worker_return,
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
    efforts = SimpleNamespace(high="high")
    return lambda: (fake, approval, sandbox, efforts, "0.147.0")


def _transport_article(**updates):
    title = "State Department Approves Possible APKWS II Sale to Italy"
    article = {
        "title": title,
        "canonical_editorial_headline": title,
        "subtitle": "The official notice describes a possible sale, not a completed transfer.",
        "dek": "The official notice describes a possible sale, not a completed transfer.",
        "seo_title": title,
        "search_title": title,
        "meta_description": "The State Department approved a possible APKWS II sale to Italy.",
        "author_identity": "Capital Chronicle",
        "publisher_identity": "Capital Chronicle",
        "canonical_slug_candidate": "state-department-apkws-ii-sale-italy",
        "primary_reader_question": "What did the State Department approve for Italy?",
        "secondary_reader_questions": [],
        "entities": ["Italy", "U.S. Department of State"],
        "topics": ["defense exports"],
        "search_freshness_class": "CURRENT",
        "internal_link_candidates": [],
        "structured_data_packet": {
            "@type": "NewsArticle",
            "headline": title,
            "description": "The State Department approved a possible APKWS II sale to Italy.",
            "datePublished": "",
            "dateModified": "",
            "publication_time_binding": (
                "COORDINATOR_MUST_BIND_EXACT_TIMESTAMP_BEFORE_EMISSION"
            ),
            "eligible_for_emission": False,
            "author": "Capital Chronicle",
            "publisher": "Capital Chronicle",
        },
        "epistemic_claims": [],
        "quote_source_records": [],
        "humor_lines": [],
        "seo_primary_keyword": "APKWS II sale to Italy",
        "institutional_edge_editorial_packet_sha256": "c" * 64,
        "market_mechanism": None,
        "policy_context": None,
        "cross_asset_implications": None,
        "substack_body_markdown": "The State Department approved the possible sale.",
        "social_lede": "The State Department approved a possible APKWS II sale to Italy.",
        "social_hook": "The State Department approved a possible APKWS II sale to Italy.",
        "social_mechanism_summary": None,
        "social_policy_summary": None,
        "social_cross_asset_summary": None,
    }
    article.update(updates)
    return article


def _turn(article, *, final_response=None):
    envelope = _transport_article(**article)
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

    assert result.output["title"] == "Italy"
    assert "market_mechanism" not in result.output
    assert len(fake.thread_start_calls) == 1
    start = fake.thread_start_calls[0]
    assert start["ephemeral"] is True
    assert start["model"] == MODEL
    assert start["sandbox"] == "read_only"
    assert start["approval_mode"] == "deny_all"
    assert start["developer_instructions"] == "bounded developer contract"
    run_kwargs = fake.thread.run_calls[0][1]
    assert run_kwargs["effort"] == EFFORT
    assert run_kwargs["output_schema"] == TRANSPORT_SCHEMA
    assert result.receipt["api_key_fallback_calls"] == 0
    assert result.receipt["turn_result_is_primary_authority"] is True
    assert result.receipt["turn_result_usage"]["total_tokens"] == 30
    assert result.receipt["turn_result_duration_ms"] == 123
    assert result.receipt["provider_input_identity"][
        "developer_instruction_sha256"
    ] == result.receipt["developer_instruction_sha256"]
    assert result.receipt["provider_input_identity_sha256"] == result.receipt["attempt_key"]
    assert result.receipt["transport_schema_top_level_property_count"] >= 30
    assert fake.thread.read_calls == [False]


def test_exact_dynamic_web_run_item_is_allowed_only_for_web_enabled_session(tmp_path):
    web_item = SimpleNamespace(
        type="dynamicToolCall", namespace="web", tool="run"
    )
    turn = _turn({"title": "Italy"})
    turn.items = [web_item]
    fake = _FakeCodex([turn])

    result = _run(
        OfficialCodexEditorialSession(
            proof_cwd=tmp_path / "allowed",
            sdk_factory=_sdk_factory(fake),
            environment={},
            allow_web_items=True,
        )
    )

    assert result.receipt["turn_result_item_types"] == ["dynamicToolCall"]


def test_non_web_dynamic_tool_remains_forbidden_when_web_items_are_allowed(tmp_path):
    tool_item = SimpleNamespace(
        type="dynamicToolCall", namespace="filesystem", tool="read_file"
    )
    turn = _turn({"title": "Italy"})
    turn.items = [tool_item]
    fake = _FakeCodex([turn])

    with pytest.raises(OfficialCodexProviderError, match="CODEX_UNEXPECTED_ACTION_ITEM"):
        _run(
            OfficialCodexEditorialSession(
                proof_cwd=tmp_path / "forbidden",
                sdk_factory=_sdk_factory(fake),
                environment={},
                allow_web_items=True,
            )
        )


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


def test_real_article_transport_schema_is_recursively_closed_and_canonical_keyed():
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
        ARTICLE_OUTPUT_CONTRACT,
    )

    assert set(TRANSPORT_SCHEMA["properties"]) == set(ARTICLE_OUTPUT_CONTRACT)
    assert TRANSPORT_SCHEMA["required"] == list(ARTICLE_OUTPUT_CONTRACT)
    assert "article_json" not in TRANSPORT_SCHEMA["properties"]

    def assert_closed(schema):
        if schema.get("type") == "object":
            assert schema["additionalProperties"] is False
            assert schema["required"] == list(schema["properties"])
            for child in schema["properties"].values():
                assert_closed(child)
        if schema.get("type") == "array":
            assert_closed(schema["items"])

    assert_closed(TRANSPORT_SCHEMA)


def test_transport_null_normalization_removes_only_declared_optional_nulls(tmp_path):
    fake = _FakeCodex([_turn({})])
    session = OfficialCodexEditorialSession(
        proof_cwd=tmp_path / "cwd", sdk_factory=_sdk_factory(fake), environment={}
    )

    result = _run(session)

    assert result.receipt["transport_nullable_fields_removed"] == [
        "cross_asset_implications",
        "market_mechanism",
        "policy_context",
        "social_cross_asset_summary",
        "social_mechanism_summary",
        "social_policy_summary",
    ]
    assert result.output["seo_primary_keyword"] == "APKWS II sale to Italy"


def test_representation_normalization_binds_only_alias_identity_packet_and_pending_dates():
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
        normalize_article_transport_representation,
    )

    raw = _transport_article(
        canonical_editorial_headline="Conflicting headline",
        dek="Conflicting dek",
        search_title="Conflicting search title",
        social_hook="Conflicting hook",
        institutional_edge_editorial_packet_sha256="model-controlled",
        structured_data_packet={
            "@type": "Article",
            "headline": "Separate prose",
            "description": "Separate prose",
            "datePublished": "invented",
            "dateModified": "invented",
            "publication_time_binding": "invented",
            "eligible_for_emission": True,
            "author": "Capital Chronicle",
            "publisher": "Capital Chronicle",
        },
    )
    repairs = []
    raw["epistemic_claims"] = [
        {
            "text": "A stale annotation absent from every public surface.",
            "layer": "OBSERVED_FACT",
            "public_treatment": "DIRECT_SOURCE_FACT",
            "source_ids": ["official-1"],
        }
    ]
    normalized = normalize_article_transport_representation(
        raw,
        context={
            "institutional_edge_editorial_packet": {
                "editorial_packet_sha256": "d" * 64
            }
        },
        repair_log=repairs,
    )

    assert normalized["canonical_editorial_headline"] == raw["title"]
    assert normalized["dek"] == raw["subtitle"]
    assert normalized["search_title"] == raw["seo_title"]
    assert normalized["social_hook"] == raw["social_lede"]
    assert normalized["slug"] == raw["canonical_slug_candidate"]
    assert normalized["institutional_edge_editorial_packet_sha256"] == "d" * 64
    assert normalized["structured_data_packet"] == {
        "@type": "NewsArticle",
        "headline": raw["title"],
        "description": raw["meta_description"],
        "datePublished": "",
        "dateModified": "",
        "publication_time_binding": (
            "COORDINATOR_MUST_BIND_EXACT_TIMESTAMP_BEFORE_EMISSION"
        ),
        "eligible_for_emission": False,
        "author": "Capital Chronicle",
        "publisher": "Capital Chronicle",
    }
    assert normalized["epistemic_claims"] == []
    assert normalized["substack_body_markdown"] == raw["substack_body_markdown"]
    assert "social_hook_social_lede_mismatch" in repairs
    assert "structured_data_description_mismatch" in repairs
    assert "epistemic_claim_not_present_in_public_copy" in repairs


def test_native_worker_return_normalizes_soft_representation_before_hard_validation():
    evidence = {
        "status": "PASS",
        "evidence_documents": [
            {
                "document_id": "official-1",
                "publisher": "U.S. Department of State",
                "title": "Possible military sale notice",
                "canonical_content_text": (
                    "The State Department approved the possible APKWS II sale to Italy."
                ),
            }
        ],
    }
    packet = build_institutional_edge_editorial_packet(
        article_mode="DATA_OR_DOCUMENT_LENS",
        accepted_evidence_packet=evidence,
    )
    article = _transport_article(
        social_hook="A conflicting transport alias.",
        institutional_edge_editorial_packet_sha256="model-controlled",
        structured_data_packet={
            "@type": "Article",
            "headline": "A separate headline",
            "description": "A separate description",
            "datePublished": "invented",
            "dateModified": "invented",
            "publication_time_binding": "invented",
            "eligible_for_emission": True,
            "author": "A model byline",
            "publisher": "A model publisher",
        },
        epistemic_claims=[
            {
                "text": "A stale annotation absent from public copy.",
                "layer": "OBSERVED_FACT",
                "public_treatment": "DIRECT_SOURCE_FACT",
                "source_ids": ["official-1"],
            }
        ],
    )
    receipt = {
        "governed_input_hash": "a" * 64,
        "model": "gpt-5.6-sol",
        "reasoning_effort": "HIGH",
        "fresh": True,
        "isolated": True,
        "bounded_revision_count": 0,
        "public_write_attempted": False,
        "article": article,
    }

    validated = validate_editorial_worker_return(
        worker_return=receipt,
        expected_governed_input_hash="a" * 64,
        expected_editorial_packet=packet,
        accepted_evidence_packet=evidence,
    )

    normalized = validated["normalized_article"]
    assert normalized["social_hook"] == normalized["social_lede"]
    assert normalized["structured_data_packet"]["description"] == normalized["meta_description"]
    assert normalized["structured_data_packet"]["eligible_for_emission"] is False
    assert normalized["epistemic_claims"] == []
    assert validated["institutional_edge_editorial_validation"]["classification"] == "PASS"
    assert {
        "social_hook_social_lede_mismatch",
        "structured_data_description_mismatch",
        "epistemic_claim_not_present_in_public_copy",
    }.issubset(validated["institutional_edge_quality_warnings"])


def test_native_worker_return_still_rejects_public_unsupported_causality():
    evidence = {
        "status": "PASS",
        "evidence_documents": [
            {
                "document_id": "official-1",
                "canonical_content_text": (
                    "The State Department approved the possible APKWS II sale to Italy."
                ),
            }
        ],
    }
    packet = build_institutional_edge_editorial_packet(
        article_mode="DATA_OR_DOCUMENT_LENS",
        accepted_evidence_packet=evidence,
    )
    article = _transport_article(
        institutional_edge_editorial_packet_sha256=packet["editorial_packet_sha256"],
        substack_body_markdown=(
            "The State Department approved the possible APKWS II sale to Italy. "
            "The notice caused a global market selloff."
        ),
    )

    with pytest.raises(ValueError, match="unsupported_causality"):
        validate_editorial_worker_return(
            worker_return={
                "governed_input_hash": "a" * 64,
                "model": "gpt-5.6-sol",
                "reasoning_effort": "HIGH",
                "fresh": True,
                "isolated": True,
                "bounded_revision_count": 0,
                "public_write_attempted": False,
                "article": article,
            },
            expected_governed_input_hash="a" * 64,
            expected_editorial_packet=packet,
            accepted_evidence_packet=evidence,
        )


def test_revision_feedback_excludes_repeated_governed_context_and_keeps_codes_hashes():
    feedback = OfficialCodexEditorialArticleBuilder._bounded_revision_feedback(
        {
            "schema_version": "contentops.same_xhigh_worker_revision_contract.v1",
            "decision": "SAME_XHIGH_WORKER_REVISION_REQUIRED",
            "governed_input_hash": "a" * 64,
            "prior_worker_return_hash": "b" * 64,
            "required_bounded_revision_count": 1,
            "maximum_bounded_revision_count": 1,
            "same_worker_required": True,
            "fresh_replacement_worker_forbidden": True,
            "deterministic_blockers": {
                "hard_editorial_blockers": ["reader_value_floor"],
                "reader_value_blockers": ["minimum_reader_substance"],
            },
            "semantic_review": {
                "failed_checks": ["reader_facing_prose"],
                "issue_codes": ["pipeline_artifacts_in_prose"],
            },
            "worker_request": {"bounded_governed_context": {"large": "excluded"}},
            "revision_contract_hash": "c" * 64,
        }
    )

    assert "worker_request" not in feedback
    assert feedback["deterministic_blocker_codes"] == [
        "minimum_reader_substance",
        "reader_value_floor",
    ]
    assert feedback["semantic_review_codes"] == [
        "pipeline_artifacts_in_prose",
        "reader_facing_prose",
    ]
    assert feedback["governed_input_hash"] == "a" * 64


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
                "institutional_edge_editorial_validation_failed:"
                "epistemic_claim_not_present_in_public_copy,"
                "epistemic_claim_layer_invalid,"
                "structured_data_description_mismatch,"
                "structured_data_dates_missing_or_unbound,"
                "structured_data_author_identity_mismatch,"
                "structured_data_publisher_identity_mismatch"
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
    assert receipt["initial_deterministic_blockers"] == [
        "epistemic_claim_not_present_in_public_copy",
        "epistemic_claim_layer_invalid",
        "structured_data_description_mismatch",
        "structured_data_dates_missing_or_unbound",
        "structured_data_author_identity_mismatch",
        "structured_data_publisher_identity_mismatch",
    ]
    assert receipt["initial_official_codex_turn_receipt"]["turn_index"] == 0
    revision_prompt = fake.thread.run_calls[1][0]
    for blocker in receipt["initial_deterministic_blockers"]:
        assert blocker in revision_prompt
    assert built["critical_path_telemetry"]["official_codex_direct_provider_calls"] == 2
    assert (tmp_path / "official_codex_turn_receipt_v1.json").is_file()
    assert (tmp_path / "official_codex_turn_receipt_revision_1_v1.json").is_file()


@pytest.mark.parametrize(
    ("failure", "phase"),
    [
        (TimeoutError("timeout"), "TIMEOUT"),
        (RuntimeError("rate limit"), "RATE_LIMIT"),
        (RuntimeError("You've hit your usage limit."), "RATE_LIMIT"),
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
