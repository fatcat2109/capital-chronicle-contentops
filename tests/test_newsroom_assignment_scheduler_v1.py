from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from live_contentops.newsroom_assignment_scheduler_v1 import (
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
        "source_packet_id": "cc-packet-1",
        "source_family": "story_scoped_publication_evidence_v1",
        "story_family": "central_bank",
        "article_mode": "rapid_analysis",
        "title": "Fed announces unexpected rate cut",
        "summary": "FOMC members vote to cut rates by 50 basis points.",
        "event_time_utc": "2026-07-13T12:00:00Z",
        "known_at_utc": "2026-07-13T12:05:00Z",
        "relationship": "new_phase",
        "eligible": True,
        "blockers": [],
        "authority": {
            "story_decision": "ALLOW",
            "global_dqr": "BLOCKED",
            "global_dqr_override": False,
            "source_authorities": ["Federal Reserve Board"],
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
    # Deterministic simple hashing for test verification mock
    import hashlib
    serialized = json.dumps(core, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(serialized).hexdigest()
    return {
        **core,
        "pool_id": f"cc-newsroom-pool-{digest[:20]}",
        "logical_hash": digest,
    }


def test_score_explainability(mock_candidate):
    from datetime import datetime, timezone
    cutoff = datetime(2026, 7, 13, 13, 30, 0, tzinfo=timezone.utc)
    weights = {"urgency": 0.4, "impact": 0.4, "freshness": 0.2}
    scores = calculate_candidate_scores(mock_candidate, cutoff, weights)
    
    # Fed is an official source term -> official_bonus 15
    # central_bank (20) + rates (10) -> tag_impact 30
    # raw_impact = 40 + 30 + 15 = 85
    assert scores["impact"] == 85.0
    # raw_urgency = 35 + 30 * 1.2 + 15 = 86
    assert scores["urgency"] == 86.0
    # Freshness: age is 1h 25m = 5100s. max age is 36h = 129600s
    # decay = (1 - 5100/129600) * 100 = 96.06
    assert abs(scores["freshness"] - 96.06) < 0.1
    # total = 85 * 0.4 + 86 * 0.4 + 96.06 * 0.2 = 34 + 34.4 + 19.21 = 87.61
    assert abs(scores["total"] - 87.61) < 0.1


def test_deterministic_window_decision_publish(base_window, mock_pool):
    res = evaluate_window_decision(
        window=base_window,
        schedule_date="2026-07-13",
        pool=mock_pool,
        previously_published=[],
    )
    assert res["decision"] == "PUBLISH"
    assert res["selected_candidate"]["candidate_id"] == "cc-candidate-11111111111111111111"
    assert "Top-ranked candidate meets thresholds" in res["rationale"]


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
    assert any(b["blocked_reason"] == "update_chain_without_material_update" for b in res["backlog_candidates"])


def test_preemption_on_highly_urgent_item(base_window, mock_pool):
    # Set limit to 0 to simulate we are at/over limits
    window = copy.deepcopy(base_window)
    window["daily_portfolio_limit"] = 0
    window["preemption_allowed"] = True
    
    # Under standard rules, we shouldn't publish. But candidate urgency is high (~86 >= 80)
    # So preemption should trigger!
    res = evaluate_window_decision(
        window=window,
        schedule_date="2026-07-13",
        pool=mock_pool,
        previously_published=[{}],
    )
    assert res["decision"] == "PUBLISH"
    assert "Preempted daily portfolio limit" in res["rationale"]


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
                "daily_portfolio_limit": 2,
                "score_weights": {"urgency": 0.4, "impact": 0.4, "freshness": 0.2},
            }
        ]
    }
    windows_file = tmp_path / "windows.json"
    windows_file.write_text(json.dumps(windows_config), encoding="utf-8")
    
    schedule = build_newsroom_schedule(
        schedule_date="2026-07-13",
        pool_path=pool_file,
        windows_path=windows_file,
        output_dir=tmp_path / "out",
    )
    
    assert schedule["schema_version"] == "capital_chronicle.newsroom_schedule_decision.v1"
    assert schedule["summary"]["publications"] == 1
    assert (tmp_path / "out" / "newsroom_schedule_2026_07_13.json").exists()
