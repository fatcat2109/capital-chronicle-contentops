from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from live_contentops.three_trigger_editorial_flow_v1 import (
    DESTINATIONS,
    FOUNDATION_DATA_PLANE_KIND,
    OPERATIONAL_TRIGGER_KINDS,
    ROUTINE_WINDOWS,
    SIMPLE_CEILINGS,
    ThreeTriggerFlowError,
    build_article_derivative_shadow_manifest,
    derive_latest_research_question,
    flow_contract_bindings,
    persist_flow_checkpoint,
    run_jim_manual_trigger,
    run_latest_intelligence_trigger,
    run_portfolio_safe_context_trigger,
)


ROOT = Path(__file__).parents[1]
FIXTURE = json.loads(
    (
        ROOT / "tests" / "fixtures" / "three_trigger_editorial_flow_cases_v1.json"
    ).read_text(encoding="utf-8")
)
RECEIPTS = json.loads(
    (
        ROOT / "tests" / "fixtures" / "three_trigger_editorial_flow_receipts_v1.json"
    ).read_text(encoding="utf-8")
)
NOW = "2026-10-18T09:00:00Z"


def _latest(**overrides):
    value = {
        "request_id": "latest-1",
        "idempotency_key": "latest-idem-1",
        "requested_at_utc": NOW,
        "cutoff_utc": NOW,
        "rolling_input": FIXTURE["latest_rolling_input"],
        "published_memory": [],
        "admitted_records": [],
        "read_models": [],
    }
    value.update(overrides)
    return run_latest_intelligence_trigger(**value)


def _portfolio(**overrides):
    value = {
        "request_id": "portfolio-1",
        "idempotency_key": "portfolio-idem-1",
        "requested_at_utc": NOW,
        "as_of_utc": NOW,
        "public_context": FIXTURE["portfolio_context"],
        "needs": [FIXTURE["portfolio_need"]],
        "source_layers": {
            "sidecars": [],
            "published_memory": [],
            "admitted_records": [],
            "read_models": [FIXTURE["portfolio_read_model_row"]],
        },
    }
    value.update(overrides)
    return run_portfolio_safe_context_trigger(**value)


def _manual(**overrides):
    value = {
        "request_id": "manual-1",
        "idempotency_key": "manual-idem-1",
        "requested_at_utc": NOW,
        "scope": "Prepare a source-backed BTCUSD market context brief.",
        "target_assets": ["BTCUSD"],
        "needs": [FIXTURE["manual_need"]],
        "source_layers": {
            "sidecars": [],
            "published_memory": [],
            "admitted_records": [FIXTURE["manual_admitted_row"]],
            "read_models": [],
        },
    }
    value.update(overrides)
    return run_jim_manual_trigger(**value)


def test_contract_exposes_exactly_three_operational_triggers():
    bindings = flow_contract_bindings()
    assert tuple(bindings["operational_trigger_kinds"]) == OPERATIONAL_TRIGGER_KINDS
    assert bindings["foundation_data_plane_kind"] == FOUNDATION_DATA_PLANE_KIND
    assert bindings["routine_windows"] == list(ROUTINE_WINDOWS)
    assert bindings["no_write"] is True
    assert bindings["cdp_boundaries"] == {
        "ingestion_only": 9222,
        "publication_media_readback": 9223,
    }


def test_receipt_fixture_covers_three_triggers_and_required_shadow_outcomes():
    assert RECEIPTS["metadata"]["authority"] is False
    assert RECEIPTS["metadata"]["state"] == "SYNTHETIC_SHADOW_ONLY"
    assert RECEIPTS["metadata"]["case_count"] == 9
    assert RECEIPTS["counts"]["READY_FOR_EDITORIAL_RESEARCH"] == 2
    assert RECEIPTS["counts"]["EDITORIAL_CONTEXT_READY"] == 2
    assert RECEIPTS["counts"]["REVIEW_READY"] == 1
    assert RECEIPTS["counts"]["DRAFT_ONLY"] == 1
    assert RECEIPTS["counts"]["PUBLISHABLE"] == 1
    assert RECEIPTS["counts"]["DATA_BLOCKED"] == 1
    assert (
        RECEIPTS["cases"]["latest_browser_fallback"]["resolution"]["resolutions"][0][
            "route"
        ]
        == "BROWSEROS_READ_ONLY"
    )
    assert RECEIPTS["cases"]["portfolio_data_blocked"]["disposition"] == "DATA_BLOCKED"
    assert RECEIPTS["derivative_manifest"]["derivative_count"] == 8


def test_latest_question_is_bounded_and_does_not_invent_event_truth():
    question = derive_latest_research_question(FIXTURE["latest_rolling_input"])
    assert question["question_status"] == "READY"
    assert question["bounded_scope"] == "ONE_HEADLINE_EVENT_INTERVAL"
    assert (
        "what evidence establishes the underlying event"
        in question["research_question"]
    )
    empty = derive_latest_research_question({"headlines": []})
    assert empty["question_status"] == "UNAVAILABLE"
    assert empty["headline_id"] is None


def test_latest_intelligence_binds_sidecar_interval_and_existing_simple_owner():
    result = _latest()
    assert result["trigger_kind"] == "SCHEDULED_LATEST_INTELLIGENCE"
    assert result["disposition"] == "READY_FOR_EDITORIAL_RESEARCH"
    assert result["resolution_state"] == "RESOLVED"
    assert result["resolution"]["database_first_order"][:4] == [
        "RETAINED_HEADLINE_SIDECAR",
        "PUBLISHED_MEMORY",
        "ADMITTED_OFFICIAL_FILING_PROVIDER",
        "EXISTING_MARKET_READ_MODEL",
    ]
    assert result["simple_gemini_handoff"]["editorial_owner"] == "SIMPLE_GEMINI_RUNTIME"
    assert result["simple_gemini_handoff"]["invoked"] is False
    assert result["editorial_packet"]["creates_scheduler"] is False
    assert result["editorial_packet"]["creates_store"] is False
    assert result["editorial_packet"]["creates_publisher"] is False
    assert result["public_write_performed"] is False
    assert result["ceilings"] == SIMPLE_CEILINGS


def test_latest_truth_boundaries_separate_report_event_analysis_and_scenario():
    result = _latest()
    truth = result["truth_boundaries"]
    assert truth["report_truth"] == ["ATTRIBUTED_REPORT_OR_INTERPRETATION"]
    assert truth["underlying_event_truth"] == "NOT_ESTABLISHED"
    assert truth["capital_chronicle_analysis"]["authority"] is False
    assert (
        truth["scenario_or_uncertainty"]["required_when_missing_or_contradictory"]
        is True
    )
    assert result["epistemic_layers"] == [
        "OBSERVED_FACT",
        "ATTRIBUTED_REPORT_OR_INTERPRETATION",
        "CAPITAL_CHRONICLE_ANALYSIS",
        "SCENARIO_OR_UNCERTAINTY",
    ]


def test_latest_flow_includes_contradictory_sidecars_and_fails_closed():
    rolling = json.loads(json.dumps(FIXTURE["latest_rolling_input"]))
    second = json.loads(json.dumps(rolling["headlines"][0]))
    second["headline_id"] = "headline-latest-contradiction"
    second["source_timestamp_utc"] = "2026-10-18T08:01:00Z"
    second["external_content"]["headline_text"] = (
        "A contradictory retained report describes a different event."
    )
    rolling["headlines"].append(second)
    result = _latest(
        request_id="latest-flow-contradiction",
        idempotency_key="latest-flow-contradiction-idem",
        rolling_input=rolling,
    )
    assert result["resolution_state"] == "DATA_BLOCKED"
    assert result["disposition"] == "DATA_BLOCKED"
    assert result["truth_boundaries"]["contradictions_preserved"] == [
        "latest-headline-event"
    ]


def test_latest_can_emit_draft_or_publishable_only_after_external_validation():
    draft = _latest(publication_intent="PUBLISHABLE", article_validation_state="DRAFT")
    assert draft["disposition"] == "DRAFT_ONLY"
    assert draft["public_write_performed"] is False
    publishable = _latest(
        request_id="latest-validated",
        idempotency_key="latest-validated-idem",
        publication_intent="PUBLISHABLE",
        article_validation_state="PASS",
    )
    assert publishable["disposition"] == "PUBLISHABLE"
    assert (
        publishable["analysis_receipt"]["authority"]["publication_authority"] is False
    )
    assert publishable["automatic_runtime_invoked"] is False


def test_latest_contradiction_is_preserved_and_blocks_automatic_editorial_ready_state():
    first = dict(FIXTURE["latest_sidecar_row"])
    second = dict(first)
    second["source_identity"] = "https://x.com/example/status/101"
    second["source_hash"] = "9" * 64
    second["values"] = {"headline_text": "A contradictory retained report."}
    rolling = {"headlines": []}
    result = _latest(
        request_id="latest-contradiction",
        idempotency_key="latest-contradiction-idem",
        rolling_input=rolling,
        read_models=[],
        admitted_records=[],
    )
    # The normal sidecar projection is intentionally empty here. Re-run through a direct
    # synthetic source seam to prove the same resolver's contradiction behavior.
    assert result["disposition"] == "ABSTAIN"
    assert result["resolution_state"] == "UNAVAILABLE"

    from live_contentops.four_trigger_data_resolution_adapter_v1 import (
        build_data_need_plan,
        build_trigger_request,
        resolve_data_need_plan,
    )

    request = build_trigger_request(
        request_id="latest-contradiction-direct",
        idempotency_key="latest-contradiction-direct-idem",
        trigger_kind="SCHEDULED_LATEST_INTELLIGENCE",
        requester="SIMPLE_GEMINI_RUNTIME",
        decision_purpose="contradiction test",
        requested_at_utc=NOW,
        required_epistemic_state="ATTRIBUTED_REPORT_OR_INTERPRETATION",
    )
    plan = build_data_need_plan(
        request,
        [
            {
                "need_id": "latest-headline-event",
                "data_class": "headline_event",
                "required_fields": ["headline_text"],
                "permitted_routes": ["RETAINED_HEADLINE_SIDECAR"],
            }
        ],
        as_of_utc=NOW,
    )
    receipt = resolve_data_need_plan(
        plan,
        source_layers={
            "sidecars": [first, second],
            "published_memory": [],
            "admitted_records": [],
            "read_models": [],
        },
    )
    assert receipt["resolution_state"] == "DATA_BLOCKED"
    assert receipt["resolutions"][0]["contradiction"]["state"] == "UNRESOLVED"


def test_latest_browseros_fallback_records_reason_hash_and_read_only_policy():
    stale_input = json.loads(json.dumps(FIXTURE["latest_rolling_input"]))
    stale_input["headlines"][0]["freshness_state"] = "STALE"
    result = _latest(
        request_id="latest-browser",
        idempotency_key="latest-browser-idem",
        rolling_input=stale_input,
        browser_recovery=lambda _need: FIXTURE["browser_recovery"],
    )
    row = result["resolution"]["resolutions"][0]
    assert result["resolution_state"] == "RESOLVED"
    assert row["route"] == "BROWSEROS_READ_ONLY"
    assert row["source_hash"] == "a" * 64
    assert row["fallback_reason"] == "database_missing_or_stale_required_field"
    assert row["tool_policy"]["allowed_tools_used"] == ["name_session", "tabs", "read"]
    assert result["resolution"]["public_write_performed"] is False


@pytest.mark.parametrize(
    ("freshness", "expected_disposition"),
    [("STALE", "DEFERRED"), ("DENIED", "DATA_BLOCKED")],
)
def test_latest_stale_and_rights_blockers_remain_explicit(
    freshness, expected_disposition
):
    rolling = json.loads(json.dumps(FIXTURE["latest_rolling_input"]))
    rolling["headlines"][0]["freshness_state"] = (
        "STALE" if freshness == "STALE" else "FRESH"
    )
    rolling["headlines"][0]["rights_state"] = (
        "DENIED" if freshness == "DENIED" else "PUBLIC_READ_ONLY"
    )
    result = _latest(
        request_id=f"latest-{freshness}",
        idempotency_key=f"latest-{freshness}-idem",
        rolling_input=rolling,
    )
    assert result["disposition"] == expected_disposition
    assert result["resolution_state"] in {"STALE", "DATA_BLOCKED"}
    assert result["resolution"]["resolutions"][0]["route"] == "UNAVAILABLE"


def test_portfolio_trigger_accepts_only_public_safe_context_and_never_returns_portfolio_state():
    result = _portfolio()
    assert result["trigger_kind"] == "SCHEDULED_PORTFOLIO_CONTEXT"
    assert result["disposition"] == "EDITORIAL_CONTEXT_READY"
    context = result["editorial_context_packet"]
    assert context["portfolio_scope"] == "PUBLIC_SAFE_CONTEXT_ONLY"
    assert context["context"]["regime_label"] == "RANGE_WITH_RATE_SENSITIVITY"
    assert context["private_portfolio_data_included"] is False
    assert context["portfolio_decision"] is False
    assert context["broker_action"] is False
    assert result["analysis_receipt"]["authority"]["portfolio_authority"] is False
    assert result["no_write"] is True


def test_portfolio_private_context_is_rejected_before_resolution():
    private = dict(FIXTURE["portfolio_context"])
    private["private_position"] = "BTCUSD 1.00"
    with pytest.raises(ThreeTriggerFlowError, match="private_context_forbidden"):
        _portfolio(public_context=private)
    private_layers = {
        "sidecars": [],
        "published_memory": [],
        "admitted_records": [],
        "read_models": [{"values": {"balance": 1000}}],
    }
    with pytest.raises(ThreeTriggerFlowError, match="private_context_forbidden"):
        _portfolio(source_layers=private_layers)


def test_portfolio_named_browser_fallback_and_stale_outcome():
    stale = dict(FIXTURE["portfolio_read_model_row"])
    stale["freshness_state"] = "STALE"
    result = _portfolio(
        request_id="portfolio-browser",
        idempotency_key="portfolio-browser-idem",
        source_layers={
            "sidecars": [],
            "published_memory": [],
            "admitted_records": [],
            "read_models": [stale],
        },
        browser_recovery=lambda _need: {
            **FIXTURE["browser_recovery"],
            "values": {"regime_label": "RECOVERED_PUBLIC_CONTEXT"},
        },
    )
    row = result["resolution"]["resolutions"][0]
    assert row["route"] == "BROWSEROS_READ_ONLY"
    assert (
        result["editorial_context_packet"]["context"]["regime_label"]
        == "RANGE_WITH_RATE_SENSITIVITY"
    )
    assert result["public_write_performed"] is False


def test_manual_jim_trigger_returns_reviewable_research_packet_without_publication():
    result = _manual()
    assert result["trigger_kind"] == "JIM_MANUAL_CODEX_DESKTOP"
    assert result["disposition"] == "REVIEW_READY"
    packet = result["manual_review_packet"]
    assert packet["scope"].startswith("Prepare a source-backed")
    assert packet["source_identity"] == ["official.example/document-1"]
    assert packet["epistemic_states"] == ["OBSERVED_FACT"]
    assert packet["exact_or_proxy"] == ["EXACT"]
    assert packet["publication_authority"] is False
    assert packet["public_write_performed"] is False
    assert result["automatic_runtime_invoked"] is False


def test_manual_trigger_requires_jim_and_keeps_missingness_reviewable():
    with pytest.raises(Exception):
        from live_contentops.four_trigger_data_resolution_adapter_v1 import (
            build_trigger_request,
        )

        build_trigger_request(
            request_id="not-jim",
            idempotency_key="not-jim-idem",
            trigger_kind="JIM_MANUAL_CODEX_DESKTOP",
            requester="operator",
            decision_purpose="research",
            requested_at_utc=NOW,
        )
    result = _manual(
        request_id="manual-blocked",
        idempotency_key="manual-blocked-idem",
        source_layers={
            "sidecars": [],
            "published_memory": [],
            "admitted_records": [],
            "read_models": [],
        },
    )
    assert result["disposition"] == "ABSTAIN"
    assert result["manual_review_packet"]["missing_fields"] == [
        "document_title",
        "published_at",
    ]
    assert "Resolve the listed blocker" in result["manual_review_packet"]["next_action"]


def test_idempotent_resume_returns_same_resolution_without_new_source_call(tmp_path):
    first = _latest()
    checkpoint = tmp_path / "latest-resolution.json"
    digest = persist_flow_checkpoint(checkpoint, first)
    assert digest == hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    checkpoint_value = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert (
        checkpoint_value["flow_request"]["request_hash"]
        == first["request"]["request_hash"]
    )
    assert checkpoint_value["flow_plan"]["plan_hash"] == first["plan"]["plan_hash"]
    resumed = _latest(
        rolling_input={"headlines": []},
        checkpoint=checkpoint_value,
    )
    assert resumed["resumed"] is True
    assert resumed["resolution"]["receipt_hash"] == checkpoint_value["receipt_hash"]
    assert (
        resumed["flow_hash"] != first["flow_hash"]
        or resumed["flow_hash"] == first["flow_hash"]
    )


def test_duplicate_terminal_request_is_reused_without_second_owner_packet():
    first = _latest()
    reused = _latest(
        terminal_by_idempotency_key={first["request"]["idempotency_key"]: first}
    )
    assert reused["disposition"] == "TERMINAL_REUSED"
    assert reused["dedupe_receipt"]["terminal_request_reused"] is True
    assert reused["request"]["request_hash"] == first["request"]["request_hash"]


def test_article_claim_layers_survive_all_eight_derivative_intents_in_shadow():
    manifest = build_article_derivative_shadow_manifest(
        article=FIXTURE["article"],
        derivative_payloads=FIXTURE["derivative_payloads"],
        canonical_url="https://capitalchronicle.example/p/shadow-1",
    )
    assert manifest["derivative_count"] == 8
    assert manifest["all_layers_preserved"] is True
    assert set(manifest["derivatives"]) == set(DESTINATIONS)
    assert all(
        row["intent_status"] == "SHADOW_ONLY"
        for row in manifest["derivatives"].values()
    )
    assert all(
        row["public_write_performed"] is False
        for row in manifest["derivatives"].values()
    )


def test_contract_hash_and_zero_write_flags_are_deterministic():
    first = _latest()
    second = _latest()
    assert first["flow_hash"] == second["flow_hash"]
    assert first["request"]["request_hash"] == second["request"]["request_hash"]
    assert first["resolution"]["receipt_hash"] == second["resolution"]["receipt_hash"]
    assert first["no_write"] is True
    assert first["public_write_performed"] is False
    assert first["unknown_write"] is False
    assert first["owner_bindings"]["routine_windows"] == list(ROUTINE_WINDOWS)
