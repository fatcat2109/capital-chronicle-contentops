from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)
from live_contentops.editorial_portfolio_v1 import PublishedArticleRef
from live_contentops.newsroom_production_day_v1 import (
    STATE_DEFICIT_RECOVERABLE,
    STATE_DEGRADED_DAILY_OUTPUT_DEFICIT,
    STATE_FLOOR_MET,
    STATE_HARD_EXTERNAL_BLOCK,
    STATE_ON_TRACK,
    bounded_deficit_work_needed,
    build_production_day_snapshot,
    load_production_day_discovery_accounting,
    load_qualified_article_records,
    newsroom_production_day_id,
    persist_qualified_article_record,
    qualify_zero_write_article,
    remaining_future_routine_windows,
    routine_progress_target,
    routine_session_ordinal,
)


def test_production_day_discovery_accounting_loads_latest_cumulative_receipt(
    tmp_path: Path,
):
    day_id = "newsroom-production-day-2026-08-23-bangkok"
    for index, requests in enumerate((10, 30), start=1):
        _write_json(
            tmp_path
            / f"frontier-{index}"
            / "rolling_x_newsroom_cycle_evidence_v1.json",
            {
                "quota_efficient_source_discovery": {
                    "schema_version": (
                        "contentops.quota_efficient_source_discovery.v1"
                    ),
                    "newsroom_production_day_id": day_id,
                    "total_discovery_turns": index,
                    "accounted_discovery_tokens": index * 100,
                    "deterministic_network_requests": requests,
                }
            },
        )
    _write_json(
        tmp_path / "other-day" / "rolling_x_newsroom_cycle_evidence_v1.json",
        {
            "quota_efficient_source_discovery": {
                "schema_version": "contentops.quota_efficient_source_discovery.v1",
                "newsroom_production_day_id": (
                    "newsroom-production-day-2026-08-22-bangkok"
                ),
                "total_discovery_turns": 4,
                "accounted_discovery_tokens": 2_000_000,
                "deterministic_network_requests": 96,
            }
        },
    )

    accounting = load_production_day_discovery_accounting(
        tmp_path, production_day_id=day_id
    )

    assert accounting["total_discovery_turns"] == 2
    assert accounting["deterministic_network_requests"] == 30


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _qualified_artifacts(root: Path, *, suffix: str = "1") -> dict:
    body = f"# Governed article {suffix}\n\nEvidence-bound final analysis."
    identity = hashlib.sha256(body.encode("utf-8")).hexdigest()
    governed_hash = hashlib.sha256(f"governed-{suffix}".encode()).hexdigest()
    article = {
        "title": f"Governed article {suffix}",
        "substack_body_markdown": body,
        "resolved_article_mode": "STANDARD_NEWS_ANALYSIS",
        "institutional_edge_editorial_validation": {"classification": "PASS"},
    }
    _write_json(root / "article_manifest_v1.json", article)
    _write_json(
        root / "grounded_support_v1.json",
        {
            "status": "PASS",
            "targeted_evidence": {
                "evidence_documents": [{"evidence_id": f"evidence-{suffix}"}]
            },
        },
    )
    _write_json(root / "media_manifest_v1.json", {"status": "PASS"})
    _write_json(root / "editorial_quality_gate_v1.json", {"classification": "PASS"})
    _write_json(
        root / "native_payloads_rehearsal_v1.json",
        {destination: {"text": destination} for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS},
    )
    _write_json(
        root / "release_candidate_lock_v1.json",
        {
            "article_body_sha256": identity,
            "source_packet_sha256": hashlib.sha256(f"source-{suffix}".encode()).hexdigest(),
            "payload_sha256": {
                destination: hashlib.sha256(destination.encode()).hexdigest()
                for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
            },
            "public_write_performed": False,
        },
    )
    _write_json(
        root / "no_write_rehearsal_v1.json",
        {"classification": "PASS_TEXT_IMAGE_RELEASE_CANDIDATE_REHEARSAL"},
    )
    _write_json(
        root / "rolling_x_grounded_article_media_v1.json",
        {
            "editorial_worker_receipt": {
                "model": "gpt-5.6-sol",
                "reasoning_effort": "HIGH",
                "fresh": True,
                "isolated": True,
                "resume_existing": False,
                "governed_input_hash": governed_hash,
                "bounded_revision_count": 0,
                "public_write_attempted": False,
            },
            "editorial_worker_validation": {"coordinator_resumes": True},
        },
    )
    return {
        "schema_version": "contentops.test_cycle.v1",
        "run_id": f"run-{suffix}",
        "classification": "PASS_PUBLICATION_PLAN_READY",
        "public_write_performed": False,
        "unknown_write_detected": False,
        "editorial_worker_routing": {"governed_input_hash": governed_hash},
        "publication_lifecycle_plan": {
            "article_identity": identity,
            "story_identity": f"story-{suffix}",
            "update_chain_identity": f"chain-{suffix}",
            "resolved_article_mode": "STANDARD_NEWS_ANALYSIS",
            "required_derivative_destinations": list(V1_REQUIRED_DERIVATIVE_DESTINATIONS),
            "destinations": [
                {"destination": "substack"},
                *[
                    {"destination": destination}
                    for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
                ],
            ],
        },
    }


def _record(root: Path, *, suffix: str, day_id: str) -> dict:
    output = root / suffix
    result = _qualified_artifacts(output, suffix=suffix)
    record = qualify_zero_write_article(
        result=result,
        output_dir=output,
        production_day_id=day_id,
        parent_window_id=f"window-{suffix}",
    )
    assert record["qualified"] is True
    persist_qualified_article_record(output, record)
    return record


def test_bangkok_production_day_groups_following_0100_then_rolls_afterward():
    expected = "newsroom-production-day-2026-08-21-bangkok"
    assert newsroom_production_day_id("2026-08-21T10:00:00Z") == expected  # 17:00
    assert newsroom_production_day_id("2026-08-21T14:00:00Z") == expected  # 21:00
    assert newsroom_production_day_id("2026-08-21T16:00:00Z") == expected  # 23:00
    assert newsroom_production_day_id("2026-08-21T18:00:00Z") == expected  # next 01:00
    assert newsroom_production_day_id("2026-08-21T19:00:00Z") == (
        "newsroom-production-day-2026-08-22-bangkok"
    )


def test_qualification_counts_exact_article_once_and_rejects_nonqualifying_output(tmp_path):
    day_id = newsroom_production_day_id("2026-08-21T14:00:00Z")
    record = _record(tmp_path, suffix="one", day_id=day_id)
    duplicate_dir = tmp_path / "duplicate"
    duplicate_dir.mkdir()
    persist_qualified_article_record(duplicate_dir, record)
    rejected_dir = tmp_path / "rejected"
    rejected_result = _qualified_artifacts(rejected_dir, suffix="rejected")
    rejected_result["unknown_write_detected"] = True
    rejected = qualify_zero_write_article(
        result=rejected_result,
        output_dir=rejected_dir,
        production_day_id=day_id,
        parent_window_id="window-rejected",
    )
    assert rejected["qualified"] is False
    assert "unknown_write_detected" in rejected["qualification_blockers"]
    assert len(load_qualified_article_records(tmp_path, production_day_id=day_id)) == 1
    assert load_qualified_article_records(
        tmp_path, production_day_id="newsroom-production-day-2026-08-20-bangkok"
    ) == []


def test_floor_states_and_bounded_catchup_are_deterministic(tmp_path):
    reference = "2026-08-21T14:00:00Z"
    day_id = newsroom_production_day_id(reference)
    empty = build_production_day_snapshot(
        reference=reference, output_root=tmp_path, routine_opportunities_used_override=0
    )
    assert empty.production_day_state == STATE_ON_TRACK
    assert bounded_deficit_work_needed(
        session="new_york_2300_bangkok", qualified_articles_today=1
    ) == 3
    _record(tmp_path, suffix="one", day_id=day_id)
    lagging = build_production_day_snapshot(
        reference=reference, output_root=tmp_path, routine_opportunities_used_override=2
    )
    assert lagging.production_day_state == STATE_DEFICIT_RECOVERABLE
    # Rebuild, rather than mutate persisted truth, to prove the terminal state calculation.
    depleted = build_production_day_snapshot(
        reference=reference, output_root=tmp_path, routine_opportunities_used_override=4
    )
    assert depleted.production_day_state == STATE_DEGRADED_DAILY_OUTPUT_DEFICIT
    exhausted = build_production_day_snapshot(
        reference=reference,
        output_root=tmp_path,
        routine_opportunities_used_override=2,
        bounded_useful_universe_exhausted=True,
    )
    assert exhausted.production_day_state == STATE_DEGRADED_DAILY_OUTPUT_DEFICIT
    assert exhausted.routine_opportunities_remaining == 2
    assert exhausted.bounded_useful_universe_exhausted is True
    blocked = build_production_day_snapshot(
        reference=reference,
        output_root=tmp_path,
        routine_opportunities_used_override=2,
        hard_external_block_reason="SOURCE_UNIVERSE_UNAVAILABLE",
    )
    assert blocked.production_day_state == STATE_HARD_EXTERNAL_BLOCK
    for suffix in ("two", "three", "four"):
        _record(tmp_path, suffix=suffix, day_id=day_id)
    floor = build_production_day_snapshot(
        reference=reference, output_root=tmp_path, routine_opportunities_used_override=3
    )
    assert floor.qualified_articles_today == 4
    assert floor.remaining_build_deficit == 0
    assert floor.production_day_state == STATE_FLOOR_MET


def test_final_minimum_reachability_never_starves_a_routine_opportunity():
    assert bounded_deficit_work_needed(
        session="new_york_2100_bangkok", qualified_articles_today=2
    ) >= 1
    assert bounded_deficit_work_needed(
        session="new_york_2300_bangkok", qualified_articles_today=2
    ) >= 2
    assert bounded_deficit_work_needed(
        session="new_york_0100_bangkok", qualified_articles_today=4
    ) >= 1
    # The build floor is telemetry; it cannot suppress work below the final minimum.
    assert bounded_deficit_work_needed(
        session="new_york_0100_bangkok", qualified_articles_today=4
    ) == 1
    # At 5-8, quota pressure disappears but one normal useful-story walk remains available.
    assert bounded_deficit_work_needed(
        session="new_york_2300_bangkok", qualified_articles_today=5
    ) == 1


def test_routine_opportunity_accounting_is_independent_from_article_pacing():
    assert routine_session_ordinal("london_1700_bangkok") == 1
    assert routine_session_ordinal("new_york_2100_bangkok") == 2
    assert routine_session_ordinal("new_york_2300_bangkok") == 3
    assert routine_session_ordinal("new_york_0100_bangkok") == 4
    assert remaining_future_routine_windows("new_york_2300_bangkok") == 1
    assert routine_progress_target("new_york_2300_bangkok") == 3
    assert bounded_deficit_work_needed(
        session="new_york_2300_bangkok", qualified_articles_today=2
    ) == 2
    assert bounded_deficit_work_needed(
        session="not-a-routine-window", qualified_articles_today=0
    ) == 0


def test_published_article_count_uses_canonical_article_identity_not_derivative_count(tmp_path):
    reference = "2026-08-21T14:00:00Z"
    article = PublishedArticleRef(
        story_identity="story-1",
        title="Canonical article",
        published_at_utc="2026-08-21T13:59:00Z",
        public_object_id="substack-object",
        canonical_url_hash="canonical-url-hash",
        content_hash="content-hash",
        article_identity="article-1",
        update_chain_identity="chain-1",
        article_mode="STANDARD_NEWS_ANALYSIS",
        entities=(),
    )
    duplicate_surface_readback = replace(article, public_object_id="derivative-object")
    prior_day = replace(
        article,
        article_identity="article-prior",
        published_at_utc="2026-08-20T13:59:00Z",
    )
    snapshot = build_production_day_snapshot(
        reference=reference,
        output_root=tmp_path,
        published_corpus=[article, duplicate_surface_readback, prior_day],
        routine_opportunities_used_override=0,
    )
    assert snapshot.published_articles_today == 1
