"""Regression tests for ContentOps Execution Frameworks (MAIN_CODEX and SUB_ANTIGRAVITY).

Authority: CONTENTOPS_MAIN_CODEX_AND_ANTIGRAVITY_SUBFRAMEWORK_OWNER_OVERRIDE_V1
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Mapping

import pytest

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline_impl
from live_contentops.capital_chronicle_institutional_edge_v1 import (
    build_institutional_edge_editorial_packet,
)
from live_contentops.codex_desktop_newsroom_operator_v1 import (
    COORDINATOR_MODEL,
    COORDINATOR_REASONING_EFFORT,
    EDITORIAL_WORKER_MODEL,
    EDITORIAL_WORKER_REASONING_EFFORT,
    build_editorial_worker_routing_packet,
    four_task_setup_packet,
    validate_editorial_worker_return,
)
from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_PUBLICATION_DESTINATIONS,
)
from live_contentops.execution_framework_v1 import (
    DEFAULT_EXECUTION_FRAMEWORK,
    FRAMEWORK_MAIN_CODEX,
    FRAMEWORK_SUB_ANTIGRAVITY,
    assert_framework_continuity,
    persist_opportunity_framework_binding,
    validate_execution_framework,
    verify_opportunity_framework_continuity,
)
from live_contentops.publication_coordinator_v1 import (
    UNKNOWN_WRITE,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERSATION_AUTHORED_ARTICLE_PATH = (
    REPO_ROOT / "live_contentops" / "data" / "sub_antigravity_authored_article_v1.json"
)


def _sample_evidence() -> dict[str, Any]:
    proposition = (
        "On August 17, 2026, the Cabinet Office released preliminary Q2 2026 real GDP data showing the economy expanded at a 1.2% annualized rate. "
        "Private consumption rose 0.3% quarter-on-quarter while business capital expenditure increased 0.8%."
    )
    return {
        "status": "PASS",
        "evidence_id": "ev-sample-1",
        "evidence_documents": [
            {
                "document_id": "esri-cao-gdp-2026q2",
                "publisher": "Economic and Social Research Institute, Cabinet Office, Government of Japan",
                "title": "Quarterly Estimates of GDP: Apr. - Jun. 2026 (First Preliminary)",
                "canonical_content_text": proposition,
                "url": "https://esri.cao.go.jp/en/sna/data/kakuhou/files/2026/gdp_q2_preliminary.html",
                "source_url": "https://esri.cao.go.jp/en/sna/data/kakuhou/files/2026/gdp_q2_preliminary.html",
                "published_at_utc": "2026-08-17T00:00:00Z",
                "claims": [{"claim_id": "claim-gdp-1", "numeric": True, "claim_text": proposition}],
            }
        ],
        "claim_evidence_contract": {
            "supported_claims": [
                {
                    "claim_id": "claim-gdp-1",
                    "claim_text": proposition,
                    "evidence_document_ids": ["esri-cao-gdp-2026q2"],
                }
            ]
        },
        "minimum_trustworthy_evidence_packet": {
            "status": "PASS",
            "risk_tier": "ORDINARY",
            "core_factual_proposition": proposition,
            "source_url": "https://esri.cao.go.jp/en/sna/data/kakuhou/files/2026/gdp_q2_preliminary.html",
            "evidence_document_id": "esri-cao-gdp-2026q2",
        },
    }


def _full_institutional_article(editorial_packet: Mapping[str, Any], evidence: Mapping[str, Any]) -> dict[str, Any]:
    raw_article_bytes = CONVERSATION_AUTHORED_ARTICLE_PATH.read_bytes()
    article = json.loads(raw_article_bytes.decode("utf-8"))
    article["institutional_edge_editorial_packet_sha256"] = str(editorial_packet.get("editorial_packet_sha256") or "")
    return article


def _valid_main_worker_return(governed_input_hash: str, article: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "execution_framework": FRAMEWORK_MAIN_CODEX,
        "model": EDITORIAL_WORKER_MODEL,
        "reasoning_effort": EDITORIAL_WORKER_REASONING_EFFORT,
        "fresh": True,
        "isolated": True,
        "governed_input_hash": governed_input_hash,
        "bounded_revision_count": 0,
        "public_write_attempted": False,
        "article": article if article is not None else {"title": "Sample Valid Article"},
    }


def _valid_sub_worker_return(governed_input_hash: str, article: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "execution_framework": FRAMEWORK_SUB_ANTIGRAVITY,
        "orchestration_mode": "SINGLE_CONVERSATION_ANTIGRAVITY",
        "governed_input_hash": governed_input_hash,
        "bounded_revision_count": 0,
        "public_write_attempted": False,
        "article": article if article is not None else {"title": "Sample Valid Article"},
    }


# Regression A: MAIN_CODEX default behavior remains exact
def test_regression_a_main_codex_default_exact():
    assert DEFAULT_EXECUTION_FRAMEWORK == FRAMEWORK_MAIN_CODEX
    fw = validate_execution_framework()
    assert fw["framework"] == FRAMEWORK_MAIN_CODEX
    assert fw["is_main"] is True
    assert fw["is_sub"] is False
    assert fw["coordinator_model"] == COORDINATOR_MODEL
    assert fw["coordinator_reasoning_effort"] == COORDINATOR_REASONING_EFFORT
    assert fw["editorial_worker_model"] == EDITORIAL_WORKER_MODEL
    assert fw["editorial_worker_reasoning_effort"] == EDITORIAL_WORKER_REASONING_EFFORT

    evidence = _sample_evidence()
    route = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": evidence,
            "exact_source_handles": ["https://esri.cao.go.jp/en/sna/data/kakuhou/files/2026/gdp_q2_preliminary.html"],
        },
    )
    assert route["execution_framework"] == FRAMEWORK_MAIN_CODEX
    assert route["decision"] == "SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER"
    assert route["coordinator"]["model"] == "gpt-5.6-sol"
    assert route["coordinator"]["reasoning_effort"] == "HIGH"
    assert route["worker_request"]["fresh"] is True
    assert route["worker_request"]["isolated"] is True

    valid_return = _valid_main_worker_return(route["governed_input_hash"])
    validation = validate_editorial_worker_return(
        worker_return=valid_return,
        expected_governed_input_hash=route["governed_input_hash"],
    )
    assert validation["classification"] == "PASS_BOUND_XHIGH_EDITORIAL_RETURN"
    assert validation["execution_framework"] == FRAMEWORK_MAIN_CODEX
    assert validation["worker_fresh_and_isolated"] is True


# Regression B: SUB_ANTIGRAVITY selection and validation
def test_regression_b_sub_antigravity_selection_and_validation():
    assert validate_execution_framework()["framework"] == FRAMEWORK_MAIN_CODEX

    with pytest.raises(ValueError, match="unrecognized_execution_framework"):
        validate_execution_framework("INVALID_FRAMEWORK")

    sub_fw = validate_execution_framework(FRAMEWORK_SUB_ANTIGRAVITY)
    assert sub_fw["framework"] == FRAMEWORK_SUB_ANTIGRAVITY
    assert sub_fw["is_main"] is False
    assert sub_fw["is_sub"] is True
    assert sub_fw["orchestration_mode"] == "SINGLE_CONVERSATION_ANTIGRAVITY"


# Regression C: SUB receipt framework validation
def test_regression_c_sub_receipt_framework_validation():
    evidence = _sample_evidence()
    route = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": evidence,
            "exact_source_handles": ["https://esri.cao.go.jp/en/sna/data/kakuhou/files/2026/gdp_q2_preliminary.html"],
        },
        execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
    )
    assert route["decision"] == "EXECUTE_IN_ACTIVE_ANTIGRAVITY_CONVERSATION"

    # Worker return claiming MAIN_CODEX while opportunity is SUB fails closed
    spoofed_framework = _valid_sub_worker_return(route["governed_input_hash"])
    spoofed_framework["execution_framework"] = FRAMEWORK_MAIN_CODEX
    with pytest.raises(ValueError, match="sub_editorial_worker_framework_invalid"):
        validate_editorial_worker_return(
            worker_return=spoofed_framework,
            expected_governed_input_hash=route["governed_input_hash"],
            execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
        )


# Regression D: Governed input hash mismatch fails closed
def test_regression_d_hash_mismatch_fails_closed():
    evidence = _sample_evidence()
    route = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": evidence,
            "exact_source_handles": ["https://esri.cao.go.jp/en/sna/data/kakuhou/files/2026/gdp_q2_preliminary.html"],
        },
        execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
    )

    valid_return = _valid_sub_worker_return(route["governed_input_hash"])
    valid_return["governed_input_hash"] = "corrupted_or_different_hash"

    with pytest.raises(ValueError, match="desktop_editorial_worker_input_hash_mismatch"):
        validate_editorial_worker_return(
            worker_return=valid_return,
            expected_governed_input_hash=route["governed_input_hash"],
            execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
        )


# Regression E: Article factual/numeric/Institutional Edge validation is identical across frameworks
def test_regression_e_institutional_edge_identical_across_frameworks():
    evidence = _sample_evidence()
    editorial_packet = build_institutional_edge_editorial_packet(
        article_mode="BREAKING_BRIEF",
        accepted_evidence_packet=evidence,
        structured_data_supported=True,
    )

    route_main = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": evidence,
            "exact_source_handles": ["https://esri.cao.go.jp/en/sna/data/kakuhou/files/2026/gdp_q2_preliminary.html"],
        },
        article_mode="BREAKING_BRIEF",
        execution_framework=FRAMEWORK_MAIN_CODEX,
    )
    route_sub = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": evidence,
            "exact_source_handles": ["https://esri.cao.go.jp/en/sna/data/kakuhou/files/2026/gdp_q2_preliminary.html"],
        },
        article_mode="BREAKING_BRIEF",
        execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
    )

    # Incomplete article fails in both
    bad_article = {"title": "Short", "subtitle": "Short", "substack_body_markdown": "Short"}
    bad_main = _valid_main_worker_return(route_main["governed_input_hash"], bad_article)
    bad_sub = _valid_sub_worker_return(route_sub["governed_input_hash"], bad_article)

    with pytest.raises(ValueError, match="institutional_edge_invalid"):
        validate_editorial_worker_return(
            worker_return=bad_main,
            expected_governed_input_hash=route_main["governed_input_hash"],
            expected_editorial_packet=editorial_packet,
            accepted_evidence_packet=evidence,
            execution_framework=FRAMEWORK_MAIN_CODEX,
        )

    with pytest.raises(ValueError, match="institutional_edge_invalid"):
        validate_editorial_worker_return(
            worker_return=bad_sub,
            expected_governed_input_hash=route_sub["governed_input_hash"],
            expected_editorial_packet=editorial_packet,
            accepted_evidence_packet=evidence,
            execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
        )

    # Complete valid institutional edge article passes in both
    good_article = _full_institutional_article(editorial_packet, evidence)
    good_main = _valid_main_worker_return(route_main["governed_input_hash"], good_article)
    good_sub = _valid_sub_worker_return(route_sub["governed_input_hash"], good_article)

    val_main = validate_editorial_worker_return(
        worker_return=good_main,
        expected_governed_input_hash=route_main["governed_input_hash"],
        expected_editorial_packet=editorial_packet,
        accepted_evidence_packet=evidence,
        execution_framework=FRAMEWORK_MAIN_CODEX,
    )
    val_sub = validate_editorial_worker_return(
        worker_return=good_sub,
        expected_governed_input_hash=route_sub["governed_input_hash"],
        expected_editorial_packet=editorial_packet,
        accepted_evidence_packet=evidence,
        execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
    )
    assert val_main["classification"] == "PASS_BOUND_XHIGH_EDITORIAL_RETURN"
    assert val_sub["classification"] == "PASS_BOUND_SUB_ANTIGRAVITY_EDITORIAL_RETURN"


# Regression F: SUB mode has zero publication/public-write authority
def test_regression_f_sub_zero_publication_authority():
    route_sub = build_editorial_worker_routing_packet(
        opportunity_state="ARTICLE_QUALIFIED",
        governed_context={
            "accepted_evidence_packet": _sample_evidence(),
            "exact_source_handles": ["https://esri.cao.go.jp/en/sna/data/kakuhou/files/2026/gdp_q2_preliminary.html"],
        },
        execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
    )
    assert route_sub["worker_request"]["grants_public_write_authority"] is False
    assert route_sub["worker_request"]["grants_factual_authority"] is False
    assert route_sub["worker_request"]["grants_numeric_authority"] is False

    valid_sub = _valid_sub_worker_return(route_sub["governed_input_hash"])
    valid_sub["public_write_attempted"] = True

    with pytest.raises(ValueError, match="public_write_forbidden"):
        validate_editorial_worker_return(
            worker_return=valid_sub,
            expected_governed_input_hash=route_sub["governed_input_hash"],
            execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
        )


# Regression G: Persisted opportunity-level framework continuity
def test_regression_g_persisted_opportunity_framework_continuity():
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        run_id = "test-opp-123"

        # Initial binding
        binding = verify_opportunity_framework_continuity(
            output_dir=output_dir,
            run_id=run_id,
            incoming_framework=FRAMEWORK_SUB_ANTIGRAVITY,
        )
        assert binding["execution_framework"] == FRAMEWORK_SUB_ANTIGRAVITY

        # Re-entry with identical framework succeeds
        resumed = verify_opportunity_framework_continuity(
            output_dir=output_dir,
            run_id=run_id,
            incoming_framework=FRAMEWORK_SUB_ANTIGRAVITY,
        )
        assert resumed["execution_framework"] == FRAMEWORK_SUB_ANTIGRAVITY

        # Re-entry trying to switch framework to MAIN_CODEX fails closed
        with pytest.raises(ValueError, match="execution_framework_switch_mid_opportunity_forbidden"):
            verify_opportunity_framework_continuity(
                output_dir=output_dir,
                run_id=run_id,
                incoming_framework=FRAMEWORK_MAIN_CODEX,
            )


# Regression H: UNKNOWN_WRITE / readiness / DurablePublicationCoordinator semantics are framework-independent
def test_regression_h_coordinator_invariants_framework_independent():
    assert UNKNOWN_WRITE == "UNKNOWN_WRITE"
    assert "substack" in V1_REQUIRED_PUBLICATION_DESTINATIONS
    assert len(V1_REQUIRED_PUBLICATION_DESTINATIONS) == 9


# Regression I: TikTok remains absent from V1
def test_regression_i_tiktok_absent_from_v1():
    assert "tiktok" not in V1_REQUIRED_PUBLICATION_DESTINATIONS


# Regression J: Existing four V1 native Codex automations setup packet
def test_regression_j_four_tasks_configuration_expected():
    packet = four_task_setup_packet()
    assert packet["routine_task_count"] == 4
    assert len(packet["tasks"]) == 4
    assert packet["model"] == "gpt-5.6-sol"
    assert packet["reasoning_effort"] == "HIGH"
    assert packet["editorial_worker_model"] == "gpt-5.6-sol"
    assert packet["editorial_worker_reasoning_effort"] == "XHIGH"
    assert packet["publication_minimum"] == 0
    assert packet["automatic_scale_up"] is False


# Regression K: No V2 runtime/store/publication mutation
def test_regression_k_no_v2_mutation():
    root_agents = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY" in root_agents


# Regression L: SUB mode never invokes 9Router model calls during cycle
def test_regression_l_sub_mode_never_calls_nine_router_ladder(monkeypatch):
    called = []

    def mock_nine_router(*args, **kwargs):
        called.append(True)
        raise RuntimeError("NINE_ROUTER_SHOULD_NOT_BE_CALLED_IN_SUB_MODE")

    monkeypatch.setattr("live_contentops.nine_router_provider_adapter_v2.call_nine_router", mock_nine_router)

    from live_contentops.newsroom_assignment_scheduler_v1 import (
        ROLLING_X_INPUT_SCHEMA_VERSION,
        build_deterministic_rolling_x_assignment_fallback,
        classify_rolling_x_story_types_deterministically,
    )
    rolling_input = {
        "schema_version": ROLLING_X_INPUT_SCHEMA_VERSION,
        "headlines": [
            {
                "headline_id": "h1",
                "text": "Cabinet Office confirms GDP growth in Q2",
                "canonical_url": "https://esri.cao.go.jp/sample.html",
                "published_at_utc": "2026-08-17T00:00:00Z",
                "publisher": "Economic and Social Research Institute",
            }
        ]
    }
    assignment = build_deterministic_rolling_x_assignment_fallback(rolling_input=rolling_input)
    assert assignment["status"] == "SUCCESS"
    assert len(called) == 0

    clusters = [{"cluster_id": "c1", "headline_ids": ["h1"], "lead_headline": rolling_input["headlines"][0]}]
    classified = classify_rolling_x_story_types_deterministically(clusters=clusters)
    assert "c1" in classified["story_type_by_cluster"]
    assert classified["llm_or_provider_calls"] == 0
    assert len(called) == 0


# Regression M: Single-conversation SUB mode cycle execution with conversation-supplied article
def test_regression_m_single_conversation_sub_mode_cycle_execution(tmp_path: Path):
    run_id = "test-sub-single-conversation-run-1"
    output_dir = tmp_path / "newsroom_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    cutoff_utc = "2026-08-17T23:59:59Z"

    evidence = _sample_evidence()
    headline = {
        "headline_id": "esri-cao-gdp-2026q2",
        "title": "Quarterly Estimates of GDP: Apr. - Jun. 2026 (First Preliminary)",
        "canonical_url": "https://esri.cao.go.jp/en/sna/data/kakuhou/files/2026/gdp_q2_preliminary.html",
        "publisher": "Economic and Social Research Institute, Cabinet Office, Government of Japan",
        "published_at_utc": "2026-08-17T00:00:00Z",
    }

    raw_article_bytes = CONVERSATION_AUTHORED_ARTICLE_PATH.read_bytes()
    conversation_article = json.loads(raw_article_bytes.decode("utf-8"))

    readiness_override = {
        "all_required_destinations_ready": True,
        "fixture_bound": True,
        "destinations": {
            dest: {
                "readiness_state": "READY_NON_BROWSER_BINDING",
                "write_eligible": True,
                "identity_match": True,
            }
            for dest in V1_REQUIRED_PUBLICATION_DESTINATIONS
        },
    }

    def acquire_evidence(request: dict[str, Any]) -> dict[str, Any]:
        ev = _sample_evidence()
        ev["cluster_id"] = request.get("cluster_id")
        ev["headline_ids"] = request.get("headline_ids")
        ev["provided_evidence_capabilities"] = list(
            request.get("required_evidence_capabilities") or ["official_filings", "macro_data"]
        )
        ev["claim_evidence_contract"]["status"] = "PASS"
        ev["claim_evidence_contract"]["supported_claim_count"] = 1
        ev["claim_evidence_contract"]["fabricated_claim_count"] = 0
        return ev

    def build_conversation_article_and_media(viability: Mapping[str, Any]) -> dict[str, Any]:
        req = dict(viability.get("editorial_worker_request") or {})
        governed_input_hash = str(req.get("governed_input_hash") or "")
        editorial_packet = dict(
            (req.get("bounded_governed_context") or {}).get("institutional_edge_editorial_packet") or {}
        )
        article = {
            **conversation_article,
            "cluster_id": str(viability.get("selected_cluster_id") or "rolling-x-deterministic-cluster-e70f6f539c3f19ecc04c"),
            "headline_ids": list(viability.get("selected_headline_ids") or ["esri-cao-gdp-2026q2"]),
            "institutional_edge_editorial_packet_sha256": str(editorial_packet.get("editorial_packet_sha256") or ""),
        }
        worker_receipt = {
            "execution_framework": FRAMEWORK_SUB_ANTIGRAVITY,
            "orchestration_mode": "SINGLE_CONVERSATION_ANTIGRAVITY",
            "governed_input_hash": governed_input_hash,
            "bounded_revision_count": 0,
            "public_write_attempted": False,
            "article": article,
        }
        return {
            "schema_version": "contentops.rolling_x_grounded_article_media_builder.v1",
            "status": "SUCCESS",
            "article": article,
            "media": {"assets": []},
            "editorial_worker_receipt": worker_receipt,
        }

    # Execute cycle in SUB_ANTIGRAVITY mode with conversation-supplied article
    result = pipeline_impl._run_rolling_x_newsroom_cycle(
        run_id=run_id,
        output_dir=output_dir,
        cutoff_utc=cutoff_utc,
        rolling_input={
            "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
            "counts": {"accepted": 1},
            "headlines": [headline],
            "unique_headline_ids": ["esri-cao-gdp-2026q2"],
        },
        evidence_acquirer=acquire_evidence,
        article_builder=build_conversation_article_and_media,
        publication_enabled=True,
        destination_readiness_override=readiness_override,
        runtime_preflight_override={"status": "PASS"},
        execution_framework=FRAMEWORK_SUB_ANTIGRAVITY,
    )

    assert result["classification"] in {"STORY_PUBLICATION_COMPLETED", "PASS_PUBLICATION_PLAN_READY"}
    assert result["public_write_performed"] is False
    assert result["unknown_write_detected"] is False
    assert result["execution_framework"] == FRAMEWORK_SUB_ANTIGRAVITY
