from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from live_contentops.daily_app_supervisor_v1 import (
    SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP,
)
from live_contentops.native_llm_first_daily_app_supervisor_v1 import (
    COORDINATOR_MODEL,
    COORDINATOR_REASONING_EFFORT,
    SELECTION_RETURN_SCHEMA_VERSION,
    NativeLlmFirstContentOpsDailyAppSupervisor,
)
from live_contentops.production_runtime_v1 import build_final_daily_app_production_runtime


NOW = datetime(2026, 8, 26, 10, 20, tzinfo=timezone.utc)
WINDOW = {
    "window_id": "editorial-window-native-llm-first-test",
    "trigger": "SCHEDULED",
    "start": datetime(2026, 8, 26, 10, 0, tzinfo=timezone.utc),
    "end": datetime(2026, 8, 26, 11, 0, tzinfo=timezone.utc),
    "session": "london_1700_bangkok",
    "native_desktop_automation_id": "v1-newsroom-london-1700",
    "native_desktop_zero_public_write": True,
}


def _prepared_state() -> dict:
    return {
        "prepared_candidate_logical_hash": "prepared-hash-1",
        "assignment": {
            "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
            "status": "SUCCESS",
            "decision": "SELECT_STORY",
            "assignment_method": "DETERMINISTIC_EVIDENCE_REACHABLE_FALLBACK",
            "input_binding": {
                "canonical_input_hash": "prepared-input-hash",
                "input_count": 3,
                "selected_count": 3,
                "held_count": 0,
            },
            "ranked_clusters": [
                {
                    "cluster_id": "cluster-a",
                    "headline_ids": ["headline-a"],
                    "leaf_cluster_ids": ["leaf-a"],
                    "rank": 1,
                    "article_mode": "breaking",
                    "why_now": "A is current",
                    "selection_case": "Candidate A",
                    "update_chain": {"relationship": "distinct"},
                },
                {
                    "cluster_id": "cluster-b",
                    "headline_ids": ["headline-b"],
                    "leaf_cluster_ids": ["leaf-b"],
                    "rank": 2,
                    "article_mode": "breaking",
                    "why_now": "B is more useful",
                    "selection_case": "Candidate B",
                    "update_chain": {"relationship": "distinct"},
                },
                {
                    "cluster_id": "cluster-c",
                    "headline_ids": ["headline-c"],
                    "leaf_cluster_ids": ["leaf-c"],
                    "rank": 3,
                    "article_mode": "breaking",
                    "why_now": "C is current but lower value",
                    "selection_case": "Candidate C",
                    "update_chain": {"relationship": "distinct"},
                },
            ],
            "leaf_clusters": [
                {"leaf_cluster_id": "leaf-a", "member_headline_ids": ["headline-a"]},
                {"leaf_cluster_id": "leaf-b", "member_headline_ids": ["headline-b"]},
                {"leaf_cluster_id": "leaf-c", "member_headline_ids": ["headline-c"]},
            ],
            "router_calls": [],
            "factual_or_numeric_authority_granted": False,
            "router_output_grants_publication_authority": False,
            "x_content_grants_evidence_authority": False,
        },
        "prepared_input": {
            "canonical_input_hash": "prepared-input-hash",
            "unique_headline_ids": ["headline-a", "headline-b", "headline-c"],
            "headlines": [
                {
                    "headline_id": "headline-a",
                    "source_timestamp_utc": "2026-08-26T09:50:00Z",
                    "external_content": {
                        "headline_text": "Company A publishes an update",
                        "author_handle": "source_a",
                        "url_or_source_ref": "https://x.com/source_a/status/1",
                    },
                },
                {
                    "headline_id": "headline-b",
                    "source_timestamp_utc": "2026-08-26T09:55:00Z",
                    "external_content": {
                        "headline_text": "Company B publishes a more material update",
                        "author_handle": "source_b",
                        "url_or_source_ref": "https://x.com/source_b/status/2",
                    },
                },
                {
                    "headline_id": "headline-c",
                    "source_timestamp_utc": "2026-08-26T09:58:00Z",
                    "external_content": {
                        "headline_text": "Company C publishes a lower-value update",
                        "author_handle": "source_c",
                        "url_or_source_ref": "https://x.com/source_c/status/3",
                    },
                },
            ],
        },
        "story_routing": {
            "story_type_by_cluster": {
                "cluster-a": "general_public_event",
                "cluster-b": "company_sector_event",
                "cluster-c": "company_sector_event",
            }
        },
    }


def _supervisor(tmp_path: Path, canonical_cycle):
    supervisor = object.__new__(NativeLlmFirstContentOpsDailyAppSupervisor)
    supervisor._output_root = tmp_path
    supervisor._store_path = tmp_path / "contentops.sqlite3"
    supervisor._scheduled_editorial_owner = SCHEDULED_EDITORIAL_OWNER_NATIVE_DESKTOP
    supervisor._clock = lambda: NOW
    supervisor._canonical_newsroom_cycle = canonical_cycle
    supervisor._native_selection_binding = ContextVar(
        f"test-native-selection-{id(supervisor)}", default=None
    )
    supervisor._newsroom_cycle = supervisor._native_llm_first_newsroom_cycle
    supervisor._resolve_native_desktop_due_window = lambda **kwargs: (
        "v1-newsroom-london-1700",
        "london_1700_bangkok",
        kwargs.get("now") or NOW,
        dict(WINDOW),
    )
    supervisor._load_prepared_candidate_checkpoint = lambda _cutoff: _prepared_state()
    supervisor._refresh_prepared_candidate_checkpoint = lambda _moment: {
        "status": "READY",
        "llm_or_provider_calls": 0,
    }
    return supervisor


def _selection_from_probe(
    probe: dict,
    *,
    cluster_id: str = "cluster-b",
    effort: str = "HIGH",
    fallback_candidates: list[dict] | None = None,
) -> dict:
    request = probe["coordinator_selection_request"]
    return {
        "schema_version": SELECTION_RETURN_SCHEMA_VERSION,
        "canonical_opportunity_id": probe["canonical_opportunity_id"],
        "selection_request_logical_hash": request["selection_request_logical_hash"],
        "selected_cluster_id": cluster_id,
        "article_mode": "STANDARD_NEWS_ANALYSIS",
        "selection_rationale": "B is the most useful current reader-facing story.",
        "fallback_candidates": list(fallback_candidates or []),
        "model": COORDINATOR_MODEL,
        "reasoning_effort": effort,
        "public_write_attempted": False,
    }


def _fallback(cluster_id: str, *, mode: str = "BREAKING_BRIEF") -> dict:
    return {
        "cluster_id": cluster_id,
        "article_mode": mode,
        "selection_rationale": f"{cluster_id} remains a useful bounded fallback.",
    }


def test_probe_is_zero_cycle_zero_evidence_and_hash_idempotent(tmp_path: Path):
    cycle_calls = []
    supervisor = _supervisor(tmp_path, lambda **kwargs: cycle_calls.append(kwargs) or {})

    first = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id="v1-newsroom-london-1700", now=NOW
    )
    second = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id="v1-newsroom-london-1700", now=NOW + timedelta(minutes=5)
    )

    assert first["classification"] == "HIGH_SELECTION_REQUIRED"
    assert first["newsroom_cycle_invocations"] == 0
    assert first["evidence_acquisition_requests"] == 0
    assert first["semantic_assignment_provider_calls"] == 0
    assert first["story_type_semantic_calls"] == 0
    assert first["public_write_performed"] is False
    assert first["unknown_write_detected"] is False
    assert len(first["coordinator_selection_request"]["candidates"]) == 3
    assert first["coordinator_selection_request"]["factual_or_numeric_authority_granted"] is False
    assert first["coordinator_selection_request"]["evidence_authority_granted"] is False
    assert first["coordinator_selection_request"]["publication_authority_granted"] is False
    assert second["coordinator_selection_request"]["selection_request_logical_hash"] == (
        first["coordinator_selection_request"]["selection_request_logical_hash"]
    )
    assert second["coordinator_selection_request"]["selection_as_of_utc"] == (
        first["coordinator_selection_request"]["selection_as_of_utc"]
    )
    assert cycle_calls == []


def test_published_memory_projection_supports_current_identity_sets():
    projected = NativeLlmFirstContentOpsDailyAppSupervisor._published_memory_projection(
        {
            "published_memory": {
                "story_identities": ["story-a", "story-b", "story-a"],
                "update_chain_identities": ["chain-a"],
            }
        }
    )
    assert {row.get("story_identity") for row in projected if row.get("story_identity")} == {
        "story-a",
        "story-b",
    }
    assert {
        row.get("update_chain_identity")
        for row in projected
        if row.get("update_chain_identity")
    } == {"chain-a"}


def test_selection_return_is_immutable_per_opportunity(tmp_path: Path):
    supervisor = _supervisor(tmp_path, lambda **_kwargs: {})
    probe = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id="v1-newsroom-london-1700", now=NOW
    )
    artifact = supervisor._load_selection_artifact(
        task_id="v1-newsroom-london-1700",
        session="london_1700_bangkok",
        opportunity_id=probe["canonical_opportunity_id"],
    )
    first = supervisor._validate_selection_return(_selection_from_probe(probe), artifact)
    first_path = supervisor._persist_selection_return(
        opportunity_id=probe["canonical_opportunity_id"], selection=first
    )
    assert first_path.exists()
    assert supervisor._persist_selection_return(
        opportunity_id=probe["canonical_opportunity_id"], selection=first
    ) == first_path

    second = supervisor._validate_selection_return(
        _selection_from_probe(probe, cluster_id="cluster-a"), artifact
    )
    with pytest.raises(
        ValueError, match="native_llm_first_selection_return_identity_conflict"
    ):
        supervisor._persist_selection_return(
            opportunity_id=probe["canonical_opportunity_id"], selection=second
        )


def test_primary_only_selection_still_narrows_canonical_prepare(tmp_path: Path):
    cycle_calls = []

    def canonical_cycle(**kwargs):
        cycle_calls.append(kwargs)
        return {
            "classification": "HIGH_REQUIRED",
            "exact_next_blocker": "DESKTOP_EDITORIAL_WORKER_REQUIRED",
            "public_write_performed": False,
            "unknown_write_detected": False,
        }

    supervisor = _supervisor(tmp_path, canonical_cycle)
    probe = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id="v1-newsroom-london-1700", now=NOW
    )

    def execute_window(_window, _moment, **_kwargs):
        result = supervisor._newsroom_cycle(
            run_id=WINDOW["window_id"],
            output_dir=tmp_path,
            cutoff_utc="2026-08-26T11:00:00Z",
            native_desktop_prepare=True,
            prepared_candidate_state={"full_frontier_should_not_survive": True},
            assignment_override=None,
            story_type_by_cluster=None,
            publication_enabled=False,
            operating_mode="SHADOW_ONLY",
        )
        return {"executed": True, **dict(result)}

    supervisor._execute_window = execute_window
    result = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id="v1-newsroom-london-1700",
        now=NOW + timedelta(minutes=5),
        coordinator_selection=_selection_from_probe(probe),
    )

    assert result["classification"] == "HIGH_REQUIRED"
    assert result["public_write_performed"] is False
    assert result["unknown_write_detected"] is False
    assert len(cycle_calls) == 1
    call = cycle_calls[0]
    assert call["prepared_candidate_state"] is None
    assignment = call["assignment_override"]
    assert assignment["selected_cluster_id"] == "cluster-b"
    assert assignment["selected_cluster_ids"] == ["cluster-b"]
    assert assignment["selected_headline_ids"] == ["headline-b"]
    assert [row["cluster_id"] for row in assignment["ranked_clusters"]] == ["cluster-b"]
    assert assignment["ranked_clusters"][0]["rank"] == 1
    assert assignment["ranked_clusters"][0]["resolved_article_mode"] == "STANDARD_NEWS_ANALYSIS"
    assert assignment["ranked_clusters"][0]["llm_first_validate_after_selected"] is True
    assert assignment["input_binding"]["input_ids"] == ["headline-b"]
    assert [row["leaf_cluster_id"] for row in assignment["leaf_clusters"]] == ["leaf-b"]
    assert call["story_type_by_cluster"] == {"cluster-b": "company_sector_event"}
    telemetry = result["native_llm_first_selection"]
    assert telemetry["selected_cluster_ids"] == ["cluster-b"]
    assert telemetry["high_admitted_shortlist_count"] == 1
    assert telemetry["full_prepared_frontier_reopened"] is False
    assert telemetry["semantic_assignment_provider_call_required"] is False
    assert telemetry["story_type_semantic_call_required"] is False


def test_high_admitted_fallback_shortlist_preserves_candidate_continuation(tmp_path: Path):
    cycle_calls = []
    supervisor = _supervisor(
        tmp_path,
        lambda **kwargs: cycle_calls.append(kwargs)
        or {
            "classification": "HIGH_REQUIRED",
            "public_write_performed": False,
            "unknown_write_detected": False,
        },
    )
    probe = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id="v1-newsroom-london-1700", now=NOW
    )
    artifact = supervisor._load_selection_artifact(
        task_id="v1-newsroom-london-1700",
        session="london_1700_bangkok",
        opportunity_id=probe["canonical_opportunity_id"],
    )
    selection = supervisor._validate_selection_return(
        _selection_from_probe(probe, fallback_candidates=[_fallback("cluster-a")]),
        artifact,
    )
    binding = supervisor._selected_assignment_binding(
        artifact=artifact, selection=selection
    )

    assignment = binding["assignment_override"]
    assert binding["selected_cluster_ids"] == ["cluster-b", "cluster-a"]
    assert assignment["selected_cluster_ids"] == ["cluster-b", "cluster-a"]
    assert [row["cluster_id"] for row in assignment["ranked_clusters"]] == [
        "cluster-b",
        "cluster-a",
    ]
    assert [row["rank"] for row in assignment["ranked_clusters"]] == [1, 2]
    assert all(
        row["llm_first_validate_after_selected"] is True
        for row in assignment["ranked_clusters"]
    )
    assert assignment["input_binding"]["input_ids"] == ["headline-b", "headline-a"]
    assert set(row["leaf_cluster_id"] for row in assignment["leaf_clusters"]) == {
        "leaf-a",
        "leaf-b",
    }
    assert "leaf-c" not in {
        row["leaf_cluster_id"] for row in assignment["leaf_clusters"]
    }
    assert binding["story_type_by_cluster"] == {
        "cluster-b": "company_sector_event",
        "cluster-a": "general_public_event",
    }
    assert "cluster-c" not in binding["story_type_by_cluster"]


def test_fallback_plan_rejects_duplicate_unknown_and_excess_entries(tmp_path: Path):
    supervisor = _supervisor(tmp_path, lambda **_kwargs: {})
    probe = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id="v1-newsroom-london-1700", now=NOW
    )
    artifact = supervisor._load_selection_artifact(
        task_id="v1-newsroom-london-1700",
        session="london_1700_bangkok",
        opportunity_id=probe["canonical_opportunity_id"],
    )

    with pytest.raises(ValueError, match="native_llm_first_candidate_plan_duplicate"):
        supervisor._validate_selection_return(
            _selection_from_probe(probe, fallback_candidates=[_fallback("cluster-b")]),
            artifact,
        )
    with pytest.raises(ValueError, match="native_llm_first_selected_cluster_invalid"):
        supervisor._validate_selection_return(
            _selection_from_probe(probe, fallback_candidates=[_fallback("cluster-missing")]),
            artifact,
        )
    with pytest.raises(ValueError, match="native_llm_first_fallback_candidates_invalid"):
        supervisor._validate_selection_return(
            _selection_from_probe(
                probe,
                fallback_candidates=[_fallback(f"cluster-{index}") for index in range(8)],
            ),
            artifact,
        )


def test_selection_rejects_effort_above_high_before_cycle(tmp_path: Path):
    cycle_calls = []
    supervisor = _supervisor(tmp_path, lambda **kwargs: cycle_calls.append(kwargs) or {})
    probe = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id="v1-newsroom-london-1700", now=NOW
    )

    with pytest.raises(ValueError, match="native_llm_first_coordinator_effort_invalid"):
        supervisor.prepare_native_desktop_scheduled_opportunity(
            automation_id="v1-newsroom-london-1700",
            now=NOW + timedelta(minutes=1),
            coordinator_selection=_selection_from_probe(probe, effort="XHIGH"),
        )
    assert cycle_calls == []


def test_selection_rejects_unknown_cluster_and_expired_request(tmp_path: Path):
    supervisor = _supervisor(tmp_path, lambda **_kwargs: {})
    probe = supervisor.prepare_native_desktop_scheduled_opportunity(
        automation_id="v1-newsroom-london-1700", now=NOW
    )
    with pytest.raises(ValueError, match="native_llm_first_selected_cluster_invalid"):
        supervisor.prepare_native_desktop_scheduled_opportunity(
            automation_id="v1-newsroom-london-1700",
            now=NOW,
            coordinator_selection=_selection_from_probe(probe, cluster_id="cluster-missing"),
        )

    with pytest.raises(ValueError, match="native_llm_first_selection_request_expired"):
        supervisor.prepare_native_desktop_scheduled_opportunity(
            automation_id="v1-newsroom-london-1700",
            now=WINDOW["end"] + timedelta(hours=1, seconds=1),
            coordinator_selection=_selection_from_probe(probe),
        )


def test_production_runtime_instantiates_native_llm_first_supervisor(tmp_path: Path):
    runtime = build_final_daily_app_production_runtime(
        store_path=tmp_path / "contentops.sqlite3",
        output_root=tmp_path / "outputs",
        operating_mode="SHADOW_ONLY",
        run_readiness_probes=False,
    )
    try:
        assert isinstance(runtime.supervisor, NativeLlmFirstContentOpsDailyAppSupervisor)
        snapshot = runtime.smoke_snapshot()
        assert snapshot["native_llm_first_selection_before_hydration"] is True
        assert snapshot["public_write_performed"] is False
    finally:
        runtime.close()
