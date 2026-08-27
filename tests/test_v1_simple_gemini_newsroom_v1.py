from __future__ import annotations

import json
from pathlib import Path

import pytest

from live_contentops.destination_transport_registry_v1 import V1_REQUIRED_DERIVATIVE_DESTINATIONS
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.newsroom_production_day_v1 import (
    load_qualified_article_records,
    newsroom_production_day_id,
)
from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_NEWSROOM_ASSIGNMENT,
    ROLE_V1_SIMPLE_ARTICLE_WRITING,
    ROLE_V1_SIMPLE_EDITORIAL_REVISION,
    ROLE_V1_SIMPLE_SELECTION,
)
from live_contentops.nine_router_ordered_model_router_v2 import model_pool_for_role
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    ARTICLE_SCHEMA_VERSION,
    MAX_SELECTION_CANDIDATES,
    MAX_SOURCE_REQUESTS,
    SELECTION_SCHEMA_VERSION,
    SimpleGeminiNewsroomError,
    _candidate_packet,
    _default_evidence_loader,
    _evidence_request,
    _selection_prompt,
    _validate_selection_text,
    run_v1_simple_gemini_newsroom,
)
from scripts.run_v1_simple_gemini_newsroom import load_canonical_published_memory_read_only

CUTOFF = "2026-08-26T14:00:00Z"
SOURCE_URL = "https://www.reuters.com/technology/nvidia-financing-plan"
TITLE = "Nvidia financing plan leaves commitment details undisclosed"
DEK = "Nvidia described a large financing plan but did not disclose individual commitments or a deployment timetable."
SOURCE_TEXT = (
    "Nvidia financing plan leaves commitment details undisclosed. "
    "Nvidia described a large financing plan but did not disclose individual commitments or a deployment timetable. "
    "The company said the financing framework would support data centres, chip factories and power infrastructure. "
    "The disclosed aggregate scale did not include project-by-project funding schedules."
)


def _headlines(count: int = 3) -> dict[str, object]:
    return {
        "schema_version": "test.rolling_input.v1",
        "headlines": [
            {
                "headline_id": f"headline-{index}",
                "headline_text": f"Current governed business headline number {index} with useful detail",
                "source_timestamp_utc": f"2026-08-26T13:{59-index:02d}:00Z",
                "source_account": "wire",
                "source_url": f"https://www.reuters.com/world/story-{index}",
            }
            for index in range(count)
        ],
    }


def _candidate_ids(rolling_input: dict[str, object]) -> list[str]:
    return [row["candidate_id"] for row in _candidate_packet(rolling_input, [])]


def _plan_entry(candidate_id: str, *, mode: str = "STANDARD_NEWS_ANALYSIS") -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "article_mode": mode,
        "selection_rationale": "This current story is independently useful to Capital Chronicle readers.",
        "research_queries": ["current business story exact publisher reporting"],
    }


def _selection(*candidate_ids: str) -> dict[str, object]:
    return {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "status": "SELECT_CANDIDATE_PLAN",
        "ordered_candidate_plan": [_plan_entry(value) for value in candidate_ids],
        "selection_summary": "The plan is ordered by current reader value.",
        "public_write_attempted": False,
    }


def _article_output(*, bad_excerpt: bool = False) -> dict[str, object]:
    paragraph_one = DEK + " [[SOURCE:SOURCE_1]]"
    paragraph_two = (
        "The company said the financing framework would support data centres, chip factories and power infrastructure. "
        "[[SOURCE:SOURCE_1]]"
    )
    return {
        "schema_version": ARTICLE_SCHEMA_VERSION,
        "article": {
            "title": TITLE,
            "dek": DEK,
            "search_title": "Nvidia financing plan: what remains undisclosed",
            "meta_description": "The financing framework leaves individual commitments and deployment timing unclear.",
            "social_hook": "The headline number is large; the missing commitment detail matters more.",
            "substack_body_markdown": "## What was announced\n\n" + paragraph_one + "\n\n## What remains unclear\n\n" + paragraph_two,
        },
        "cited_sources": [
            {
                "source_id": "SOURCE_1",
                "url": SOURCE_URL,
                "publisher": "Reuters",
                "published_at_utc": "2026-08-26T13:20:00Z",
            }
        ],
        "material_claim_bindings": [
            {
                "claim_id": "claim-title",
                "claim_text": TITLE,
                "claim_kind": "FACT",
                "source_id": "SOURCE_1",
                "support_excerpt": TITLE,
                "attribution_required": True,
            },
            {
                "claim_id": "claim-dek",
                "claim_text": DEK,
                "claim_kind": "FACT",
                "source_id": "SOURCE_1",
                "support_excerpt": "not in source" if bad_excerpt else DEK,
                "attribution_required": True,
            },
            {
                "claim_id": "claim-infra",
                "claim_text": "The company said the financing framework would support data centres, chip factories and power infrastructure.",
                "claim_kind": "FACT",
                "source_id": "SOURCE_1",
                "support_excerpt": "The company said the financing framework would support data centres, chip factories and power infrastructure.",
                "attribution_required": True,
            },
        ],
        "public_write_attempted": False,
    }


def _evidence_result(*, request_count: int = 1, status: str = "PASS", blocker: str = "") -> dict[str, object]:
    documents = []
    if status == "PASS":
        documents = [
            {
                "document_id": "doc-reuters-nvidia",
                "publisher": "Reuters",
                "source_identity": "reuters.com",
                "source_url": SOURCE_URL,
                "reader_source_url": SOURCE_URL,
                "published_at_utc": "2026-08-26T13:20:00Z",
                "published_at_source": "PUBLISHER_BYTES_OR_HEADERS",
                "canonical_content_sha256": "a" * 64,
                "canonical_content_text": SOURCE_TEXT,
                "public_claim_allowed": True,
            }
        ]
    return {
        "status": status,
        "blockers": [blocker] if blocker else [],
        "evidence_documents": documents,
        "provenance": {"request_count_for_call": request_count},
    }


def _receipt(role: str) -> dict[str, object]:
    return {
        "schema_version": "contentops.nine_router_ordered_model_router.v2",
        "logical_invocation_id": role,
        "role_task_id": role,
        "terminal_disposition": "ACCEPTED",
        "selected_model": "vx/gemini-3.5-flash(high)",
        "models_attempted_in_order": ["vx/gemini-3.5-flash(high)"],
        "total_attempts": 1,
        "total_fallback_transitions": 0,
        "total_usage": {"total_tokens": 100},
        "total_cost": {},
        "model_identity_provider_verifiable": True,
        "public_write_attempted": False,
    }


def test_strict_selection_accepts_32_candidate_shape_and_preserves_order():
    governed = _headlines(MAX_SELECTION_CANDIDATES)
    ids = _candidate_ids(governed)
    assert len(ids) == 32
    ok, failure, parsed, diagnostic = _validate_selection_text(
        json.dumps(_selection(ids[4], ids[2], ids[9])), candidate_ids=set(ids)
    )
    assert (ok, failure, diagnostic) == (True, None, None)
    assert [row["candidate_id"] for row in parsed["ordered_candidate_plan"]] == [ids[4], ids[2], ids[9]]
    assert [row["plan_role"] for row in parsed["ordered_candidate_plan"]] == ["PRIMARY", "FALLBACK", "FALLBACK"]


@pytest.mark.parametrize(
    ("candidate_values", "diagnostic"),
    [
        (("not-governed",), "candidate_plan_id_not_governed"),
        (("duplicate", "duplicate"), "candidate_plan_id_duplicate"),
    ],
)
def test_selection_rejects_unknown_and_duplicate_candidate_ids(candidate_values, diagnostic):
    ok, failure, parsed, reason = _validate_selection_text(
        json.dumps(_selection(*candidate_values)), candidate_ids={"duplicate"}
    )
    assert ok is False
    assert failure == "malformed_business_input"
    assert parsed is None
    assert reason == diagnostic


def test_selection_rejects_enum_list_article_mode_and_prompt_is_unambiguous():
    raw = _selection("governed")
    raw["ordered_candidate_plan"][0]["article_mode"] = ["BREAKING_BRIEF"]
    assert _validate_selection_text(json.dumps(raw), candidate_ids={"governed"})[3] == "article_mode_scalar_invalid"
    prompt = _selection_prompt({"candidate_count": 32, "candidates": []})
    assert "Return exactly one JSON object" in prompt
    assert "Do not use markdown, code fences" in prompt
    assert '"article_mode": "exactly one of:' in prompt


def test_simple_roles_are_flash_only_without_changing_unrelated_assignment_role():
    for role in (ROLE_V1_SIMPLE_SELECTION, ROLE_V1_SIMPLE_ARTICLE_WRITING, ROLE_V1_SIMPLE_EDITORIAL_REVISION):
        assert model_pool_for_role(role) == ("vx/gemini-3.5-flash(high)",)
    assert model_pool_for_role(ROLE_NEWSROOM_ASSIGNMENT) == (
        "vx/gemini-3.1-pro-preview(high)",
        "vx/gemini-3.5-flash(high)",
    )


def test_default_source_loader_uses_one_first_party_aware_shared_six_get_ledger():
    loader = _default_evidence_loader(CUTOFF)
    assert loader._max_requests == MAX_SOURCE_REQUESTS
    assert loader._shared_request_budget == {"limit": MAX_SOURCE_REQUESTS, "used": 0}


def test_evidence_request_preserves_the_full_bounded_ordered_query_plan():
    candidate = _candidate_packet(_headlines(1), [])[0]
    entry = _plan_entry(candidate["candidate_id"])
    entry["research_queries"] = ["first useful query", "second useful query", "third useful query"]
    request = _evidence_request(candidate, entry)
    context = request["story_context"]
    assert context["grounded_research_queries"] == [
        "first useful query", "second useful query", "third useful query"
    ]
    assert context["planned_research_query_count"] == 3
    assert len(context["planned_research_query_set_sha256"]) == 64


def test_worker_prompt_requires_literal_false_public_write_flag():
    from live_contentops.v1_simple_gemini_newsroom_v1 import _worker_prompt

    prompt = _worker_prompt({"selected_candidate": {}, "source_pack": []})
    assert "public_write_attempted MUST be the JSON boolean false" in prompt
    assert "no publication tools" in prompt
    assert "Every claim_text and support_excerpt must be at least eight characters" in prompt


def test_primary_source_blocked_second_candidate_succeeds_without_second_selection(tmp_path: Path):
    rolling = _headlines(3)
    ids = _candidate_ids(rolling)
    roles: list[str] = []
    evidence_ids: list[str] = []

    def llm_invoke(**kwargs):
        role = kwargs["role_task_id"]
        roles.append(role)
        if role == ROLE_V1_SIMPLE_SELECTION:
            assert "published_memory" not in kwargs["governed_input"]
            assert kwargs["governed_input"]["published_memory_summary"]["full_published_corpus_in_prompt"] is False
            return _selection(ids[0], ids[1], ids[2]), _receipt(role)
        assert evidence_ids == [ids[0], ids[1]]
        return _article_output(), _receipt(role)

    def evidence_loader(request):
        evidence_ids.append(request["cluster_id"])
        if len(evidence_ids) == 1:
            return _evidence_result(request_count=3, status="BLOCKED", blocker="publisher_bytes_unavailable")
        return _evidence_result(request_count=2)

    result = run_v1_simple_gemini_newsroom(
        output_dir=tmp_path,
        cutoff_utc=CUTOFF,
        rolling_input=rolling,
        llm_invoke=llm_invoke,
        evidence_loader=evidence_loader,
        run_id="fallback-success",
    )
    assert result["classification"] == "PASS_V1_SIMPLE_GEMINI_ZERO_WRITE_ARTICLE"
    assert result["selected_candidate"]["candidate_id"] == ids[1]
    assert result["source_request_count"] == 5
    assert [row["status"] for row in result["candidate_attempt_history"]] == ["SOURCE_BLOCKED", "SOURCE_QUALIFIED"]
    assert roles == [ROLE_V1_SIMPLE_SELECTION, ROLE_V1_SIMPLE_ARTICLE_WRITING]
    assert result["logical_model_invocation_count"] == 2
    assert result["codex_runtime_model_call_count"] == 0
    assert result["qualified_article_count"] == 1
    assert result["derivative_intent_count"] == 8
    assert result["public_write_performed"] is False
    assert result["provider_publication_writes"] == 0
    assert result["unknown_write_count"] == 0
    intents = json.loads((tmp_path / "derivative_intents_v1.json").read_text())
    assert {row["destination"] for row in intents["intents"]} == set(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    assert all(row["dispatch_state"] == "UNDISPATCHED" for row in intents["intents"])
    records = load_qualified_article_records(tmp_path, production_day_id=newsroom_production_day_id(CUTOFF))
    assert len(records) == 1
    assert records[0]["editorial_worker"]["model"] == "vx/gemini-3.5-flash(high)"


def test_all_candidates_blocked_returns_complete_history_with_shared_six_get_limit(tmp_path: Path):
    rolling = _headlines(3)
    ids = _candidate_ids(rolling)
    roles: list[str] = []
    calls = 0

    def llm_invoke(**kwargs):
        roles.append(kwargs["role_task_id"])
        return _selection(*ids), _receipt(kwargs["role_task_id"])

    def evidence_loader(_request):
        nonlocal calls
        calls += 1
        return _evidence_result(
            request_count=4 if calls == 1 else 2,
            status="BLOCKED",
            blocker=f"candidate_{calls}_source_blocked",
        )

    result = run_v1_simple_gemini_newsroom(
        output_dir=tmp_path,
        cutoff_utc=CUTOFF,
        rolling_input=rolling,
        llm_invoke=llm_invoke,
        evidence_loader=evidence_loader,
        run_id="all-blocked",
    )
    assert result["classification"] == "NO_PUBLICATION"
    assert result["exact_next_blocker"] == "ALL_ADMITTED_CANDIDATES_SOURCE_RETRIEVAL_BLOCKED"
    assert result["source_request_count"] == MAX_SOURCE_REQUESTS
    assert calls == 2
    assert len(result["candidate_attempt_history"]) == 3
    assert result["candidate_attempt_history"][2]["status"] == "NOT_ATTEMPTED_SHARED_SOURCE_BUDGET_EXHAUSTED"
    assert roles == [ROLE_V1_SIMPLE_SELECTION]


def test_reported_source_budget_overrun_fails_closed_before_writer(tmp_path: Path):
    rolling = _headlines(1)
    candidate_id = _candidate_ids(rolling)[0]
    roles: list[str] = []

    def llm_invoke(**kwargs):
        roles.append(kwargs["role_task_id"])
        return _selection(candidate_id), _receipt(kwargs["role_task_id"])

    with pytest.raises(SimpleGeminiNewsroomError) as exc_info:
        run_v1_simple_gemini_newsroom(
            output_dir=tmp_path,
            cutoff_utc=CUTOFF,
            rolling_input=rolling,
            llm_invoke=llm_invoke,
            evidence_loader=lambda _request: _evidence_result(request_count=7),
            run_id="budget-overrun",
        )
    assert exc_info.value.code == "shared_source_request_budget_exceeded"
    assert roles == [ROLE_V1_SIMPLE_SELECTION]


def test_canonical_published_memory_suppresses_duplicate_and_is_opened_read_only(tmp_path: Path):
    db_path = tmp_path / "store.sqlite3"
    ContentOpsDurableStore(db_path, auto_migrate=True)
    before = (db_path.stat().st_size, db_path.stat().st_mtime_ns)
    articles, proof = load_canonical_published_memory_read_only(
        store_path=db_path,
        output_root=tmp_path / "outputs",
    )
    after = (db_path.stat().st_size, db_path.stat().st_mtime_ns)
    assert articles == []
    assert before == after
    assert proof["store_access_mode"] == "SQLITE_MODE_RO_QUERY_ONLY"
    assert proof["auto_migrate"] is False
    assert proof["production_store_unchanged_during_projection"] is True
    rolling = _headlines(2)
    title = rolling["headlines"][0]["headline_text"]
    assert [row["headline_id"] for row in _candidate_packet(rolling, [{"title": title}])] == ["headline-1"]


def test_one_validation_failure_allows_exactly_one_flash_revision(tmp_path: Path):
    rolling = _headlines(1)
    candidate_id = _candidate_ids(rolling)[0]
    roles: list[str] = []

    def llm_invoke(**kwargs):
        role = kwargs["role_task_id"]
        roles.append(role)
        if role == ROLE_V1_SIMPLE_SELECTION:
            return _selection(candidate_id), _receipt(role)
        if role == ROLE_V1_SIMPLE_ARTICLE_WRITING:
            return _article_output(bad_excerpt=True), _receipt(role)
        assert role == ROLE_V1_SIMPLE_EDITORIAL_REVISION
        assert "material_claim_excerpt_not_verified:claim-dek" in kwargs["prompt"]
        return _article_output(), _receipt(role)

    result = run_v1_simple_gemini_newsroom(
        output_dir=tmp_path,
        cutoff_utc=CUTOFF,
        rolling_input=rolling,
        llm_invoke=llm_invoke,
        evidence_loader=lambda _request: _evidence_result(),
        run_id="one-revision",
    )
    assert result["revision_performed"] is True
    assert result["logical_model_invocation_count"] == 3
    assert roles == [ROLE_V1_SIMPLE_SELECTION, ROLE_V1_SIMPLE_ARTICLE_WRITING, ROLE_V1_SIMPLE_EDITORIAL_REVISION]


def test_second_validation_failure_abstains_without_fourth_call(tmp_path: Path):
    rolling = _headlines(1)
    candidate_id = _candidate_ids(rolling)[0]
    roles: list[str] = []

    def llm_invoke(**kwargs):
        role = kwargs["role_task_id"]
        roles.append(role)
        if role == ROLE_V1_SIMPLE_SELECTION:
            return _selection(candidate_id), _receipt(role)
        return _article_output(bad_excerpt=True), _receipt(role)

    result = run_v1_simple_gemini_newsroom(
        output_dir=tmp_path,
        cutoff_utc=CUTOFF,
        rolling_input=rolling,
        llm_invoke=llm_invoke,
        evidence_loader=lambda _request: _evidence_result(),
        run_id="revision-exhausted",
    )
    assert result["classification"] == "NO_PUBLICATION"
    assert result["exact_next_blocker"] == "SINGLE_GEMINI_REVISION_EXHAUSTED"
    assert result["logical_model_invocation_count"] == 3
    assert roles.count(ROLE_V1_SIMPLE_EDITORIAL_REVISION) == 1


def test_blocked_selection_persists_safe_per_attempt_diagnostics(tmp_path: Path):
    safe = {
        "schema_version": "contentops.nine_router_ordered_model_router.v2",
        "terminal_disposition": "LLM_TERMINAL_NON_RETRYABLE_FAILURE",
        "attempt_diagnostics": [
            {
                "attempt_index": 1,
                "requested_model": "vx/gemini-3.5-flash(high)",
                "resolved_model": "gemini-3.5-flash",
                "failure_class": "structured_output_schema_invalid",
                "provider_status_class": "2xx_success",
                "validator_reason": "candidate_plan_id_not_governed",
                "accepted": False,
                "usage": {"total_tokens": 42},
            }
        ],
        "public_write_attempted": False,
    }

    def blocked(**_kwargs):
        raise SimpleGeminiNewsroomError(
            "gemini_logical_invocation_blocked",
            diagnostics={"router_receipt": safe},
        )

    result = run_v1_simple_gemini_newsroom(
        output_dir=tmp_path,
        cutoff_utc=CUTOFF,
        rolling_input=_headlines(1),
        llm_invoke=blocked,
        run_id="blocked-selection",
    )
    assert result["exact_next_blocker"] == "GEMINI_SELECTION_LOGICAL_INVOCATION_BLOCKED"
    assert result["blocked_logical_invocation"]["attempt_diagnostics"][0]["validator_reason"] == "candidate_plan_id_not_governed"
    text = json.dumps(json.loads((tmp_path / "simple_gemini_newsroom_receipt_v1.json").read_text())).casefold()
    assert "authorization" not in text
    assert "cookie" not in text
    assert "raw_output" not in text


def test_module_has_no_codex_runtime_dependency():
    path = Path(__file__).parents[1] / "live_contentops" / "v1_simple_gemini_newsroom_v1.py"
    text = path.read_text(encoding="utf-8").casefold()
    assert "official_codex" not in text
    assert "codex_desktop" not in text
    assert "officialcodexeditorialsession" not in text
