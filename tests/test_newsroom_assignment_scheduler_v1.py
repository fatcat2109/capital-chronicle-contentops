from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from live_contentops.newsroom_assignment_scheduler_v1 import (
    EXPECTED_CANDIDATE_POOL_PRODUCER_COMMIT_SHA,
    build_newsroom_schedule,
    calculate_candidate_scores,
    evaluate_window_decision,
)


@pytest.fixture
def base_window():
    return {
        "window_id": "us_open",
        "name": "United States Open Window",
        "target_cutoff_utc": "13:30:00",
        "minimum_urgency_threshold": 60,
        "minimum_impact_threshold": 55,
        "preemption_allowed": True,
        "minimum_preemption_impact_delta": 15.0,
        "daily_portfolio_limit": 2,
        "score_weights": {
            "urgency": 0.4,
            "impact": 0.4,
            "freshness": 0.2,
        },
    }


@pytest.fixture
def mock_candidate():
    return {
        "candidate_id": "cc-candidate-11111111111111111111",
        "story_id": "cc-story-11111111111111111111",
        "cluster_id": "cc-cluster-11111111111111111111",
        "update_chain_id": "cc-update-chain-11111111111111111111",
        "source_packet_id": "cc-packet-1",
        "source_family": "story_scoped_publication_evidence_v1",
        "evidence_hash": "c" * 64,
        "source_packet_logical_hash": "d" * 64,
        "story_family": "central_bank",
        "article_mode": "rapid_analysis",
        "title": "Fed announces unexpected rate cut",
        "summary": "FOMC members vote to cut rates by 50 basis points.",
        "event_time_utc": "2026-07-13T12:00:00Z",
        "known_at_utc": "2026-07-13T12:05:00Z",
        "relationship": "new_phase",
        "eligible": True,
        "blockers": [],
        "evidence_class": "exact",
        "authority": {
            "story_decision": "ALLOW",
            "global_dqr": "BLOCKED",
            "global_dqr_override": False,
            "source_authorities": ["Federal Reserve Board"],
        },
        "claim_permissions": {
            "decision": "ALLOW",
            "reporting_allowed": True,
            "numeric_claims_allowed": True,
        },
        "source_health": {"status": "HEALTHY", "parse_status": "PASS"},
        "source_documents": [{"source_url": "https://www.federalreserve.gov/monetarypolicy.htm"}],
        "numeric_claims": [{
            "claim_id": "fed-rate-change",
            "metric": "Federal funds target range change",
            "value": -50,
            "unit": "basis_points",
            "source_url": "https://www.federalreserve.gov/monetarypolicy.htm",
            "public_claim_allowed": True,
        }],
        "citation_map": {
            "fed-rate-change": ["https://www.federalreserve.gov/monetarypolicy.htm"],
        },
        "freshness": {
            "age_hours": 1.5,
            "max_age_hours": 36.0,
            "evaluated_at_utc": "2026-07-13T13:30:00Z",
        },
        "tags": ["central_bank", "rates"],
    }


@pytest.fixture
def mock_pool(mock_candidate):
    core = {
        "schema_version": "capital_chronicle.newsroom_candidate_pool.v1",
        "producer_version": "newsroom_candidate_pool_v1.0.0",
        "generated_at_utc": "2026-07-13T23:00:00Z",
        "cutoff_time_utc": "2026-07-13T23:00:00Z",
        "candidate_only": True,
        "global_dqr_override": False,
        "database_binding": {
            "head_sha": "419caa95c90704acfd2ad2685be30317813a12b3",
            "input_logical_hash": "a" * 64,
        },
        "source_inventory": {
            "inventory_id": "NEWSROOM_CANDIDATE_SOURCES_V1",
            "logical_hash": "b" * 64,
        },
        "source_coverage": [],
        "clusters": [],
        "eligible_candidates": [mock_candidate],
        "rejected_candidates": [],
        "counts": {
            "inputs": 1,
            "eligible": 1,
            "rejected": 0,
            "clusters": 1,
        },
        "status": "PASS_CANDIDATE_POOL_READY",
    }
    # Producer binding is outside the pool's non-recursive logical identity.
    import hashlib
    serialized = json.dumps(core, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(serialized).hexdigest()
    pool_id = f"cc-newsroom-pool-{digest[:20]}"
    return {
        **core,
        "pool_id": pool_id,
        "logical_hash": digest,
        "producer_binding": {
            "upstream_repository": "fatcat2109/Headline-Raw-data-json",
            "upstream_branch": "main",
            "candidate_pool_producer_commit_sha": EXPECTED_CANDIDATE_POOL_PRODUCER_COMMIT_SHA,
            "candidate_pool_artifact_sha256": "e" * 64,
            "pool_id": pool_id,
            "pool_logical_hash": digest,
            "schema_version": core["schema_version"],
            "schema_hash": "f" * 64,
            "candidate_hashes": [mock_candidate["evidence_hash"]],
            "cutoff_time_utc": core["cutoff_time_utc"],
        },
    }


def test_score_explainability_preserves_unavailable_dimensions(mock_candidate):
    from datetime import datetime, timezone
    cutoff = datetime(2026, 7, 13, 13, 30, 0, tzinfo=timezone.utc)
    weights = {"urgency": 0.4, "impact": 0.4, "freshness": 0.2}
    scores = calculate_candidate_scores(mock_candidate, cutoff, weights)

    assert scores["ranking_model_version"] == "contentops.newsroom_ranking.v2.0.0"
    assert len(scores["dimensions"]) == 14
    assert scores["dimensions"]["materiality"] == {
        "availability": "UNAVAILABLE",
        "score": None,
        "reason_codes": ["unavailable_no_measured_change"],
        "evidence_refs": [],
    }
    assert scores["dimensions"]["source_authority"]["score"] == 100.0
    assert abs(scores["dimensions"]["freshness"]["score"] - 96.06) < 0.1
    assert scores["availability_summary"] == {
        "available": 6,
        "unavailable": 8,
        "unknown_explicit_inputs": [],
    }
    assert abs(scores["impact"] - 97.74) < 0.1
    assert abs(scores["urgency"] - 95.95) < 0.1
    assert abs(scores["total"] - 97.51) < 0.1


def test_score_is_not_changed_by_keyword_or_tag_injection(mock_candidate):
    from datetime import datetime, timezone
    cutoff = datetime(2026, 7, 13, 13, 30, 0, tzinfo=timezone.utc)
    weights = {"urgency": 0.4, "impact": 0.4, "freshness": 0.2}
    baseline = calculate_candidate_scores(mock_candidate, cutoff, weights)
    injected = copy.deepcopy(mock_candidate)
    injected["title"] = "Fed Treasury FOMC OPEC payroll inflation volatility"
    injected["tags"] = ["central_bank", "inflation", "energy", "geopolitics", "volatility"]
    assert calculate_candidate_scores(injected, cutoff, weights) == baseline


def test_deterministic_window_decision_publish(base_window, mock_pool):
    res = evaluate_window_decision(
        window=base_window,
        schedule_date="2026-07-13",
        pool=mock_pool,
        previously_published=[],
    )
    assert res["decision"] == "PUBLISH_FRESH_ANALYSIS"
    assert res["selected_candidate"]["candidate_id"] == "cc-candidate-11111111111111111111"
    assert res["breaking_qualification"]["qualified"] is False
    assert "Top-ranked fully gated candidate meets thresholds" in res["rationale"]


def test_cutoff_time_no_future_leakage(base_window, mock_pool):
    # Candidate known after window cutoff should be ignored
    pool = copy.deepcopy(mock_pool)
    pool["eligible_candidates"][0]["known_at_utc"] = "2026-07-13T14:00:00Z"
    res = evaluate_window_decision(
        window=base_window,
        schedule_date="2026-07-13",
        pool=pool,
        previously_published=[],
    )
    assert res["decision"] == "NO_PUBLICATION_THRESHOLD_NOT_MET"
    assert res["selected_candidate"] is None


def test_concentration_penalties(base_window, mock_pool):
    # Candidate story family is "central_bank", article_mode is "rapid_analysis"
    # Previously published also has "central_bank" and "rapid_analysis"
    # So we apply topic penalty (15) and mode penalty (10)
    prev = [
        {
            "story_family": "central_bank",
            "article_mode": "rapid_analysis",
            "authority": {"source_authorities": ["Federal Reserve Board"]},
        }
    ]
    res = evaluate_window_decision(
        window=base_window,
        schedule_date="2026-07-13",
        pool=mock_pool,
        previously_published=prev,
    )
    # The penalty total is 15 + 10 + 12 = 37
    # Raw total is ~87.61. Score after penalty is ~50.61.
    # Below minimum urgency (60) or impact (55), so it should hold or not meet threshold
    assert res["decision"] in ("HOLD_FOR_MORE_EVIDENCE", "NO_PUBLICATION_THRESHOLD_NOT_MET")
    assert res["score_details"]["penalty_total"] == 37.0


def test_update_chain_blocker_without_material_update(base_window, mock_pool):
    # Candidate is duplicate -> blocked from immediate window publication
    pool = copy.deepcopy(mock_pool)
    pool["eligible_candidates"][0]["relationship"] = "duplicate"
    res = evaluate_window_decision(
        window=base_window,
        schedule_date="2026-07-13",
        pool=pool,
        previously_published=[],
    )
    assert res["decision"] == "NO_PUBLICATION_THRESHOLD_NOT_MET"
    assert res["selected_candidate"] is None
    assert any(
        "update_chain_without_material_update" in row["blocked_reasons"]
        for row in res["backlog_candidates"]
    )


def test_preemption_on_highly_urgent_item(base_window, mock_pool):
    # Set limit to 0 to simulate we are at/over limits
    window = copy.deepcopy(base_window)
    window["daily_portfolio_limit"] = 0
    window["preemption_allowed"] = True
    
    previous = {
        "candidate_id": "cc-candidate-prior",
        "_schedule_window_id": "london_open",
        "_schedule_final_score": 40.0,
    }
    candidate = mock_pool["eligible_candidates"][0]
    candidate["ranking_inputs"] = {
        "materiality": {"availability": "AVAILABLE", "score": 95, "reason_codes": ["governed_material_event"]},
        "policy_economic_geopolitical_significance": {"availability": "AVAILABLE", "score": 90, "reason_codes": ["governed_significance"]},
    }
    candidate["breaking_event_evidence"] = {"event_id": "governed-breaking-event"}
    res = evaluate_window_decision(
        window=window,
        schedule_date="2026-07-13",
        pool=mock_pool,
        previously_published=[previous],
    )
    assert res["decision"] == "PUBLISH_BREAKING_OR_HIGH_IMPACT"
    contract = res["preemption_contract"]
    assert contract["preempted_window"] == "london_open"
    assert contract["selected_candidate"] == candidate["candidate_id"]
    assert contract["preempted_candidate"] == "cc-candidate-prior"
    assert contract["impact_delta"] >= base_window["minimum_preemption_impact_delta"]
    assert len(contract["decision_hash"]) == 64
    assert contract["operator_state"] == "OPERATOR_REVIEW_REQUIRED"
    assert contract["breaking_qualification"]["qualified"] is True
    assert "impact delta" in res["rationale"]


def test_preemption_blocked_if_preemption_disabled(base_window, mock_pool):
    window = copy.deepcopy(base_window)
    window["daily_portfolio_limit"] = 0
    window["preemption_allowed"] = False
    
    res = evaluate_window_decision(
        window=window,
        schedule_date="2026-07-13",
        pool=mock_pool,
        previously_published=[{}],
    )
    assert res["decision"] == "NO_PUBLICATION_THRESHOLD_NOT_MET"
    assert res["selected_candidate"] is None


def test_hard_gate_blocks_candidate_with_revoked_reporting_permission(base_window, mock_pool):
    pool = copy.deepcopy(mock_pool)
    pool["eligible_candidates"][0]["claim_permissions"]["reporting_allowed"] = False
    res = evaluate_window_decision(
        window=base_window,
        schedule_date="2026-07-13",
        pool=pool,
        previously_published=[],
    )
    assert res["selected_candidate"] is None
    assert res["score_details"]["raw_scores"] is None
    assert "reporting_permission_not_granted" in res["backlog_candidates"][0]["blocked_reasons"]


def test_hard_gate_blocks_invalid_evidence_binding(base_window, mock_pool):
    pool = copy.deepcopy(mock_pool)
    pool["eligible_candidates"][0]["evidence_hash"] = "not-a-sha256"
    res = evaluate_window_decision(
        window=base_window,
        schedule_date="2026-07-13",
        pool=pool,
        previously_published=[],
    )
    assert res["selected_candidate"] is None
    assert "evidence_hash_invalid" in res["backlog_candidates"][0]["blocked_reasons"]


def test_hard_gate_blocks_claim_known_after_cutoff(base_window, mock_pool):
    pool = copy.deepcopy(mock_pool)
    pool["eligible_candidates"][0]["numeric_claims"][0]["known_at_utc"] = "2026-07-13T14:00:00Z"
    res = evaluate_window_decision(
        window=base_window,
        schedule_date="2026-07-13",
        pool=pool,
        previously_published=[],
    )
    assert res["selected_candidate"] is None
    assert "claim_known_at_utc_after_window_cutoff" in res["backlog_candidates"][0]["blocked_reasons"]


def test_deterministic_tie_break_uses_candidate_id(base_window, mock_pool):
    pool = copy.deepcopy(mock_pool)
    second = copy.deepcopy(pool["eligible_candidates"][0])
    second["candidate_id"] = "cc-candidate-00000000000000000000"
    second["story_id"] = "cc-story-00000000000000000000"
    second["cluster_id"] = "cc-cluster-00000000000000000000"
    second["update_chain_id"] = "cc-update-chain-00000000000000000000"
    pool["eligible_candidates"] = [pool["eligible_candidates"][0], second]
    res = evaluate_window_decision(
        window=base_window,
        schedule_date="2026-07-13",
        pool=pool,
        previously_published=[],
    )
    assert res["selected_candidate"]["candidate_id"] == second["candidate_id"]


def test_same_candidate_cannot_publish_twice_even_as_new_phase(base_window, mock_pool):
    previous = copy.deepcopy(mock_pool["eligible_candidates"][0])
    previous["_schedule_window_id"] = "asia_open"
    previous["_schedule_final_score"] = 70.0
    res = evaluate_window_decision(
        window=base_window,
        schedule_date="2026-07-13",
        pool=mock_pool,
        previously_published=[previous],
    )
    assert res["selected_candidate"] is None
    assert "candidate_already_published" in res["backlog_candidates"][0]["blocked_reasons"]


def test_materiality_sixty_with_significance_unavailable_is_fresh_analysis(base_window, mock_pool):
    candidate = mock_pool["eligible_candidates"][0]
    candidate["ranking_inputs"] = {
        "materiality": {"availability": "AVAILABLE", "score": 60, "reason_codes": ["governed_modest_move"]},
        "policy_economic_geopolitical_significance": {"availability": "UNAVAILABLE", "score": None},
        "affected_market_economy_breadth": {"availability": "UNAVAILABLE", "score": None},
    }
    candidate["breaking_event_evidence"] = {"event_id": "quality-alone-is-not-impact"}
    result = evaluate_window_decision(window=base_window, schedule_date="2026-07-13", pool=mock_pool, previously_published=[])
    assert result["decision"] == "PUBLISH_FRESH_ANALYSIS"
    assert result["breaking_qualification"]["checks"]["materiality"] is False
    assert result["breaking_qualification"]["checks"]["significance_or_breadth"] is False


def test_historical_cluster_suppression_and_justified_reentry(base_window, mock_pool):
    candidate = mock_pool["eligible_candidates"][0]
    history = [{"candidate_id": "historic-id", "cluster_id": candidate["cluster_id"], "update_chain_id": candidate["update_chain_id"]}]
    unchanged = evaluate_window_decision(window=base_window, schedule_date="2026-07-13", pool=mock_pool, previously_published=history)
    assert unchanged["selected_candidate"] is None
    assert "historical_cluster_or_chain_without_justified_new_version" in unchanged["backlog_candidates"][0]["blocked_reasons"]

    candidate["relationship"] = "material_update"
    candidate["article_version_justification"] = "New governed curve observation changes the accepted analysis."
    candidate["material_update_evidence"] = {"claim_id": "fed-rate-change"}
    material_update = evaluate_window_decision(window=base_window, schedule_date="2026-07-13", pool=mock_pool, previously_published=history)
    assert material_update["selected_candidate"] is not None

    candidate["relationship"] = "new_phase"
    candidate["article_version_justification"] = "A separately timed policy phase warrants a new article version."
    candidate.pop("material_update_evidence")
    new_phase = evaluate_window_decision(window=base_window, schedule_date="2026-07-13", pool=mock_pool, previously_published=history)
    assert new_phase["selected_candidate"] is not None


def test_build_rejects_missing_or_mismatched_producer_binding(tmp_path, mock_pool):
    windows_file = tmp_path / "windows.json"
    windows_file.write_text(json.dumps({"windows": []}), encoding="utf-8")
    for mutation in ("missing", "mismatched"):
        pool = copy.deepcopy(mock_pool)
        if mutation == "missing":
            pool.pop("producer_binding")
        else:
            pool["producer_binding"]["candidate_pool_producer_commit_sha"] = "0" * 40
        pool_file = tmp_path / f"pool-{mutation}.json"
        pool_file.write_text(json.dumps(pool), encoding="utf-8")
        with pytest.raises(ValueError, match="producer_binding_candidate_pool_producer_commit_sha_missing_or_mismatched"):
            build_newsroom_schedule(schedule_date="2026-07-13", pool_path=pool_file, windows_path=windows_file, output_dir=tmp_path / mutation)


def test_full_newsroom_scheduling_flow(tmp_path, mock_pool):
    pool_file = tmp_path / "candidate_pool.json"
    pool_file.write_text(json.dumps(mock_pool), encoding="utf-8")
    
    windows_config = {
        "schema_version": "capital_chronicle.newsroom_decision_windows.v1",
        "windows": [
            {
                "window_id": "us_open",
                "name": "United States Open Window",
                "target_cutoff_utc": "13:30:00",
                "minimum_urgency_threshold": 60,
                "minimum_impact_threshold": 55,
                "preemption_allowed": True,
                "minimum_preemption_impact_delta": 15.0,
                "daily_portfolio_limit": 2,
                "score_weights": {"urgency": 0.4, "impact": 0.4, "freshness": 0.2},
            }
        ]
    }
    windows_file = tmp_path / "windows.json"
    windows_file.write_text(json.dumps(windows_config), encoding="utf-8")
    
    first_output = tmp_path / "first"
    second_output = tmp_path / "second"
    schedule = build_newsroom_schedule(
        schedule_date="2026-07-13",
        pool_path=pool_file,
        windows_path=windows_file,
        output_dir=first_output,
    )
    replay = build_newsroom_schedule(
        schedule_date="2026-07-13",
        pool_path=pool_file,
        windows_path=windows_file,
        output_dir=second_output,
    )

    first_path = first_output / "newsroom_schedule_2026_07_13.json"
    second_path = second_output / "newsroom_schedule_2026_07_13.json"
    assert schedule["schema_version"] == "capital_chronicle.newsroom_schedule_decision.v1"
    assert schedule["generated_at_utc"] == mock_pool["generated_at_utc"]
    assert schedule["summary"]["publications"] == 1
    assert schedule["decisions"][0]["decision"] == "PUBLISH_FRESH_ANALYSIS"
    assert schedule["candidate_pool_producer_binding"]["candidate_pool_producer_commit_sha"] == EXPECTED_CANDIDATE_POOL_PRODUCER_COMMIT_SHA
    assert replay == schedule
    assert first_path.read_bytes() == second_path.read_bytes()
