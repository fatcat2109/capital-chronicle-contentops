from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from live_contentops.newsroom_assignment_scheduler_v1 import (
    build_universal_v2_newsroom_schedule,
    evaluate_universal_v2_window_decision,
)
from live_contentops.universal_news_candidate_fabric_v2 import (
    CLAIM_CAPABILITIES,
    CANDIDATE_SCHEMA,
    ClaimCapabilityV2,
    adapt_v1_candidate,
    breaking_qualification,
    build_candidate,
    build_claim,
    build_pool,
    classify_update_relationship,
    logical_hash,
    score_candidate,
    validate_candidate,
    validate_claim,
    validate_pool,
)


SOURCE_RECORD = {
    "source_family_id": "fixture_official_document",
    "authority_class": "OFFICIAL_VERIFIED",
    "permission_ceiling": "REPORTING_ALLOWED",
    "evidence_state": "exact",
    "enabled": True,
}
SOURCE_REGISTRY = {SOURCE_RECORD["source_family_id"]: SOURCE_RECORD}
CUTOFF = "2026-07-14T00:00:00Z"


def _citation():
    return [{"source_document_id": "doc:1", "url": "https://example.test/doc"}]


def _claim(claim_type="official_action", **overrides):
    values = {
        "claim_id": f"claim:{claim_type}:1",
        "claim_type": claim_type,
        "statement": "The governed source records the action.",
        "structured_payload": {"action_type": "published_notice"},
        "source_document_ids": ["doc:1"],
        "evidence_refs": ["evidence:1"],
        "authority_class": "OFFICIAL_VERIFIED",
        "permission_state": "REPORTING_ALLOWED",
        "event_time_utc": "2026-07-13T10:00:00Z",
        "published_at_utc": "2026-07-13T10:00:00Z",
        "known_at_utc": "2026-07-13T10:05:00Z",
        "citations": _citation(),
        "entities": ["entity:1"],
        "geographies": ["geo:1"],
    }
    values.update(overrides)
    return build_claim(**values)


def _candidate(
    claim=None,
    *,
    profile="official_action",
    reporting_allowed=True,
    evidence_state="exact",
    blockers=(),
    ranking_inputs=None,
):
    claim = claim or _claim()
    values = {
        "candidate_id": "cc-candidate-fixture-1",
        "story_id": "cc-story-fixture-1",
        "cluster_id": "cc-cluster-fixture-1",
        "update_chain_id": "cc-update-chain-fixture-1",
        "source_native_ids": ["native:1"],
        "source_family_ids": ["fixture_official_document"],
        "evidence_requirement_profile_id": profile,
        "capabilities": {
            "claim_capabilities": [claim["claim_type"]],
            "numeric_evidence_required": profile == "numeric_economic_release",
            "nonnumeric_evidence_supported": profile != "numeric_economic_release",
        },
        "title": "Governed event",
        "summary": "A source-backed candidate.",
        "relationship": "initial_event",
        "claims": [claim],
        "source_documents": [{
            "document_id": "doc:1",
            "source_url": "https://example.test/doc",
        }],
        "entities": ["entity:1"],
        "geographies": ["geo:1"],
        "evidence_refs": list(claim["evidence_refs"]),
        "authority_state": "OFFICIAL_VERIFIED",
        "reporting_allowed": reporting_allowed,
        "evidence_state": evidence_state,
        "event_time_utc": "2026-07-13T10:00:00Z",
        "observation_time_utc": (
            "2026-07-13T10:00:00Z" if profile == "numeric_economic_release" else None
        ),
        "published_at_utc": "2026-07-13T10:00:00Z",
        "known_at_utc": "2026-07-13T10:05:00Z",
        "revision_at_utc": None,
        "cutoff_time_utc": CUTOFF,
        "evidence_completeness": {"availability": "AVAILABLE", "value": 1.0},
        "freshness": {"availability": "AVAILABLE", "value": 0},
        "ranking_inputs": ranking_inputs or {},
        "limitations": ["fixture_only"],
        "blockers": list(blockers),
        "publication_authority": False,
        "public_write_allowed": False,
        "global_dqr_override": False,
    }
    return build_candidate(values)


def _pool(candidate):
    return build_pool(
        candidates=[candidate],
        source_family_records=[SOURCE_RECORD],
        generated_at_utc=CUTOFF,
        cutoff_time_utc=CUTOFF,
        upstream_binding={"repository": "fixture", "observed_head": "a" * 40},
        category_blockers={},
    )


def _window():
    return {"window_id": "window-1", "target_cutoff_utc": "12:00:00"}


def test_nonnumeric_candidate_is_valid_without_numeric_claim():
    candidate = _candidate()
    assert candidate["numeric_claims"] == []
    assert validate_candidate(
        candidate,
        cutoff_utc=CUTOFF,
        source_family_registry=SOURCE_REGISTRY,
    ) == []


def test_numeric_profile_requires_numeric_claim():
    candidate = _candidate(profile="numeric_economic_release")
    blockers = validate_candidate(
        candidate,
        cutoff_utc=CUTOFF,
        source_family_registry=SOURCE_REGISTRY,
    )
    assert "candidate_numeric_claim_required" in blockers


def test_numeric_claim_requires_metric_value_unit_transformation_and_authority():
    claim = _claim(
        "numeric_observation",
        numeric={
            "metric": "metric:1",
            "value": 0,
            "unit": "units",
            "transformation": "source_native_value",
            "numeric_authority_class": "official_source",
        },
        observed_at_utc="2026-07-13T10:00:00Z",
    )
    assert validate_claim(claim, cutoff_utc=CUTOFF) == []
    for field in ("metric", "value", "unit", "transformation", "numeric_authority_class"):
        broken = copy.deepcopy(claim)
        broken["numeric"][field] = None
        broken["logical_hash"] = logical_hash({k: v for k, v in broken.items() if k != "logical_hash"})
        assert f"numeric_claim_{field}_missing" in validate_claim(broken, cutoff_utc=CUTOFF)


@pytest.mark.parametrize(
    "claim_type",
    [
        "official_action",
        "legal_or_regulatory_action",
        "corporate_filing_fact",
        "event_occurrence",
        "entity_relationship",
        "correction_or_revision",
    ],
)
def test_nonnumeric_claim_capabilities_validate(claim_type):
    assert validate_claim(_claim(claim_type), cutoff_utc=CUTOFF) == []


def test_market_reaction_requires_separate_market_evidence():
    claim = _claim("market_reaction")
    assert "market_reaction_separate_evidence_missing" in validate_claim(claim, cutoff_utc=CUTOFF)
    valid = _claim(
        "market_reaction",
        evidence_refs=["event:evidence", "market:evidence"],
        market_evidence_refs=["market:evidence"],
        structured_payload={
            "instrument_id": "instrument:1",
            "observation_time_utc": "2026-07-13T10:00:00Z",
            "evidence_relationship": "exact",
        },
    )
    assert validate_claim(valid, cutoff_utc=CUTOFF) == []


def test_model_assisted_claim_requires_evidence_bound_hashed_judgment():
    missing = _claim("model_assisted_judgment")
    assert "model_judgment_record_missing" in validate_claim(missing, cutoff_utc=CUTOFF)
    judgment = {
        "schema_version": "contentops.model_assisted_judgment.v1",
        "judgment_id": "judgment:1",
        "evidence_refs": ["evidence:1"],
        "score": 42,
    }
    judgment["logical_hash"] = logical_hash(judgment)
    valid = _claim("model_assisted_judgment", judgment_record=judgment)
    assert validate_claim(valid, cutoff_utc=CUTOFF) == []


def test_claim_registry_is_versioned_and_extensible():
    extension = dict(CLAIM_CAPABILITIES)
    extension["additional_structured_fact"] = ClaimCapabilityV2(
        "additional_structured_fact", True, True
    )
    claim = _claim("additional_structured_fact")
    assert validate_claim(claim, cutoff_utc=CUTOFF, registry=extension) == []
    assert "claim_type_not_registered" in validate_claim(claim, cutoff_utc=CUTOFF)


def test_source_family_registry_accepts_versioned_extension():
    extended = dict(SOURCE_REGISTRY)
    extended["additional_official_family"] = {
            "source_family_id": "additional_official_family",
            "authority_class": "OFFICIAL_VERIFIED",
            "permission_ceiling": "REPORTING_ALLOWED",
        "enabled": True,
    }
    candidate = _candidate()
    candidate["source_family_ids"] = ["additional_official_family"]
    candidate = build_candidate(candidate)
    assert validate_candidate(candidate, cutoff_utc=CUTOFF, source_family_registry=extended) == []


def test_future_known_at_is_rejected():
    claim = _claim(known_at_utc="2026-07-14T01:00:00Z")
    assert "claim_known_at_utc_after_cutoff" in validate_claim(claim, cutoff_utc=CUTOFF)


def test_candidate_reporting_cannot_upgrade_context_only_claim():
    claim = _claim(permission_state="CONTEXT_ONLY")
    candidate = _candidate(claim=claim, reporting_allowed=True)
    assert "candidate_reporting_permission_upgrade" in validate_candidate(
        candidate,
        cutoff_utc=CUTOFF,
        source_family_registry=SOURCE_REGISTRY,
    )


def test_candidate_authority_cannot_upgrade_claim_or_source_family():
    claim = _claim(authority_class="CONTEXT_ONLY")
    candidate = _candidate(claim=claim)
    assert "candidate_authority_upgrade" in validate_candidate(
        candidate,
        cutoff_utc=CUTOFF,
        source_family_registry=SOURCE_REGISTRY,
    )
    restricted_registry = {
        "fixture_official_document": {
            **SOURCE_RECORD,
            "authority_class": "CONTEXT_ONLY",
            "permission_ceiling": "CONTEXT_ONLY",
        }
    }
    blockers = validate_candidate(
        _candidate(),
        cutoff_utc=CUTOFF,
        source_family_registry=restricted_registry,
    )
    assert "candidate_authority_exceeds_source_family_ceiling" in blockers
    assert "claim_permission_exceeds_source_family_ceiling" in blockers


def test_numeric_claims_are_a_compatibility_projection():
    claim = _claim(
        "numeric_observation",
        numeric={
            "metric": "metric:1",
            "value": 0,
            "unit": "units",
            "transformation": "source_native_value",
            "numeric_authority_class": "official_source",
        },
        observed_at_utc="2026-07-13T10:00:00Z",
    )
    candidate = _candidate(claim=claim, profile="numeric_economic_release")
    assert candidate["numeric_claims"] == [claim]
    assert validate_candidate(
        candidate,
        cutoff_utc=CUTOFF,
        source_family_registry=SOURCE_REGISTRY,
    ) == []


def test_v1_numeric_candidate_compatibility_adapter():
    v1 = {
        "candidate_id": "cc-candidate-11111111111111111111",
        "story_id": "cc-story-11111111111111111111",
        "cluster_id": "cc-cluster-11111111111111111111",
        "update_chain_id": "cc-update-chain-11111111111111111111",
        "source_packet_id": "packet:1",
        "evidence_hash": "a" * 64,
        "title": "Numeric release",
        "summary": "Official value.",
        "relationship": "new_phase",
        "event_time_utc": "2026-07-13T00:00:00Z",
        "known_at_utc": "2026-07-13T01:00:00Z",
        "claim_permissions": {"reporting_allowed": True},
        "source_documents": [{
            "document_id": "doc:1",
            "source_url": "https://example.test/doc",
        }],
        "citation_map": {"metric:1": ["https://example.test/doc"]},
        "numeric_claims": [{
            "claim_id": "metric:1",
            "metric": "Official metric",
            "value": 0,
            "unit": "units",
            "source_authority": "official_source",
            "public_claim_allowed": True,
            "observation_time_utc": "2026-07-13T00:00:00Z",
            "known_at_utc": "2026-07-13T01:00:00Z",
        }],
    }
    candidate = adapt_v1_candidate(v1, source_family_id="fixture_official_document")
    assert len(candidate["claims"]) == 1
    assert candidate["claims"][0]["numeric"]["value"] == 0
    assert candidate["numeric_claims"] == candidate["claims"]
    assert candidate["publication_authority"] is False


@pytest.mark.parametrize(
    ("signal", "expected"),
    [
        ("correction", "correction"),
        ("contradiction", "contradiction"),
        ("confirmation", "confirmation"),
        ("new_phase", "new_phase"),
        ("material_delta", "material_update"),
    ],
)
def test_governed_update_relationship_signals(signal, expected):
    previous = _candidate()
    current = copy.deepcopy(previous)
    current["candidate_id"] = "cc-candidate-fixture-2"
    current["delta_signals"] = {signal: True}
    assert classify_update_relationship(previous, current) == expected


def test_duplicate_and_incremental_update_classification():
    previous = _candidate()
    duplicate = copy.deepcopy(previous)
    assert classify_update_relationship(previous, duplicate) == "duplicate"
    incremental = copy.deepcopy(previous)
    incremental["claims"].append(_claim("factual_text", claim_id="claim:factual:2"))
    assert classify_update_relationship(previous, incremental) == "incremental_update"


def test_unavailable_and_explicit_zero_are_distinct_in_ranking():
    candidate = _candidate(ranking_inputs={
        "surprise": {
            "availability": "EXPLICIT_ZERO",
            "score": 0,
            "reason_codes": ["governed_zero"],
            "evidence_refs": ["evidence:1"],
        },
        "audience_relevance": {
            "availability": "UNAVAILABLE",
            "score": None,
            "reason_codes": ["not_measured"],
            "evidence_refs": [],
        },
    })
    score = score_candidate(candidate)
    assert score["dimensions"]["surprise"]["score"] == 0
    assert score["dimensions"]["surprise"]["availability"] == "EXPLICIT_ZERO"
    assert score["dimensions"]["audience_relevance"]["score"] is None
    assert score["available_dimension_count"] == 1


def test_model_assisted_ranking_score_requires_candidate_bound_evidence():
    judgment = {
        "judgment_id": "judgment:ranking:1",
        "evidence_refs": ["other:evidence"],
        "score": 50,
    }
    judgment["logical_hash"] = logical_hash(judgment)
    candidate = _candidate(ranking_inputs={
        "materiality": {
            "availability": "AVAILABLE",
            "score": 50,
            "reason_codes": ["model_assisted"],
            "evidence_refs": ["evidence:1"],
            "model_assisted_judgment": judgment,
        }
    })
    assert "model_judgment_evidence_not_bound:materiality" in score_candidate(candidate)["blockers"]
    judgment["evidence_refs"] = ["evidence:1"]
    judgment["logical_hash"] = logical_hash(
        {key: value for key, value in judgment.items() if key != "logical_hash"}
    )
    candidate = _candidate(ranking_inputs={
        "materiality": {
            "availability": "AVAILABLE",
            "score": 50,
            "reason_codes": ["model_assisted"],
            "evidence_refs": ["evidence:1"],
            "model_assisted_judgment": judgment,
        }
    })
    assert score_candidate(candidate)["blockers"] == []


def test_valid_nonnumeric_candidate_reaches_assignment_without_numeric_blocker():
    candidate = _candidate(ranking_inputs={
        "source_authority": {
            "availability": "AVAILABLE",
            "score": 100,
            "reason_codes": ["official"],
            "evidence_refs": ["evidence:1"],
        },
    })
    pool = _pool(candidate)
    result = evaluate_universal_v2_window_decision(
        window=_window(),
        schedule_date="2026-07-13",
        pool=pool,
        previously_assigned=[],
    )
    assert result["selected_candidate_id"] == candidate["candidate_id"]
    assert result["decision"] == "ASSIGN_INTERNAL_NO_PUBLICATION_TASK_BOUNDARY"
    assert result["publication_authority"] is False


def test_context_only_candidate_is_held_for_permission_not_numeric_absence():
    claim = _claim(permission_state="CONTEXT_ONLY")
    candidate = _candidate(
        claim=claim,
        reporting_allowed=False,
        evidence_state="context",
        blockers=["context_only_evidence"],
    )
    pool = _pool(candidate)
    result = evaluate_universal_v2_window_decision(
        window=_window(),
        schedule_date="2026-07-13",
        pool=pool,
        previously_assigned=[],
    )
    blockers = result["held_candidates"][0]["blockers"]
    assert "reporting_permission_not_granted" in blockers
    assert all("numeric_claim" not in value for value in blockers)


def test_deterministic_blockers_override_maximum_ranking_scores():
    claim = _claim(permission_state="CONTEXT_ONLY")
    inputs = {
        name: {
            "availability": "AVAILABLE",
            "score": 100,
            "reason_codes": ["fixture"],
            "evidence_refs": ["evidence:1"],
        }
        for name in (
            "materiality",
            "source_authority",
            "freshness",
            "evidence_completeness",
            "portfolio_diversity",
        )
    }
    candidate = _candidate(
        claim=claim,
        reporting_allowed=False,
        evidence_state="context",
        blockers=["context_only_evidence"],
        ranking_inputs=inputs,
    )
    result = evaluate_universal_v2_window_decision(
        window=_window(),
        schedule_date="2026-07-13",
        pool=_pool(candidate),
        previously_assigned=[],
    )
    assert result["selected_candidate_id"] is None
    assert "context_only_evidence" in result["held_candidates"][0]["blockers"]


def test_breaking_requires_bound_governed_event_or_material_update_evidence():
    candidate = _candidate(ranking_inputs={
        "materiality": {
            "availability": "AVAILABLE",
            "score": 100,
            "reason_codes": ["governed_event"],
            "evidence_refs": ["evidence:1"],
        },
    })
    assert breaking_qualification(candidate)["qualified"] is False
    candidate["breaking_event_evidence_ref"] = "evidence:1"
    assert breaking_qualification(candidate)["qualified"] is True
    candidate["relationship"] = "duplicate"
    assert breaking_qualification(candidate)["qualified"] is False


def test_five_window_schedule_is_deterministic_and_no_publication():
    pool = _pool(_candidate())
    windows = [
        {"window_id": f"window-{index}", "target_cutoff_utc": f"{hour:02d}:00:00"}
        for index, hour in enumerate((11, 12, 13, 14, 15), start=1)
    ]
    first = build_universal_v2_newsroom_schedule(
        schedule_date="2026-07-13", pool=pool, windows=windows
    )
    second = build_universal_v2_newsroom_schedule(
        schedule_date="2026-07-13", pool=pool, windows=windows
    )
    assert first == second
    assert first["summary"]["publication_count"] == 0
    assert first["summary"]["public_write_count"] == 0
    assert first["publication_authority"] is False


def test_pool_count_or_hash_tampering_fails_closed():
    pool = _pool(_candidate())
    assert validate_pool(pool) == []
    broken = copy.deepcopy(pool)
    broken["counts"]["claims"] += 1
    broken["logical_hash"] = logical_hash({k: v for k, v in broken.items() if k != "logical_hash"})
    assert "pool_counts_mismatch" in validate_pool(broken)


def test_generic_core_contains_no_source_or_topic_name_routing():
    path = Path(__file__).parents[1] / "live_contentops" / "universal_news_candidate_fabric_v2.py"
    text = path.read_text(encoding="utf-8").lower()
    prohibited = (
        "microsoft",
        "apple",
        "fomc",
        "ofac",
        "usgs",
        "federal register",
        "sanctions program",
        "election name",
        "war name",
    )
    assert not [value for value in prohibited if value in text]


def test_universal_pool_schema_accepts_valid_fixture():
    jsonschema = pytest.importorskip("jsonschema")
    root = Path(__file__).parents[1]
    schema = json.loads(
        (root / "schemas" / "ContentOpsUniversalNewsCandidatePoolV2.schema.json").read_text(
            encoding="utf-8"
        )
    )
    jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    ).validate(_pool(_candidate()))


def test_contract_schema_versions_are_explicit():
    candidate = _candidate()
    assert candidate["schema_version"] == CANDIDATE_SCHEMA
    assert candidate["claims"][0]["schema_version"] == "contentops.universal_news_claim.v2"
