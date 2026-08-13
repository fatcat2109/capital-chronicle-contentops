from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from PIL import Image

from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_V2_CREATIVE_EDITOR,
    ROLE_V2_CREATIVE_REVISION_AUTHOR,
    ROLE_V2_MOTION_CODE_AUTHOR,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    V2_CREATIVE_MODEL_POOL,
    model_pool_for_role,
    retry_budget_for_role,
)
from live_contentops.retention_native_concrete_first_v2 import (
    AssetCandidate,
    CreativeBible,
    VisualGroundingContract,
    broker_assets,
    build_segment_prompt,
    compile_chart_plan,
    compile_document_plan,
    compile_map_plan,
    enforce_must_use_assets,
    evaluate_comprehension_gate,
    validate_segment_graph,
    visual_mix_summary,
    zero_public_write_manifest,
)
from live_contentops.retention_native_creative_brain_v2 import (
    CodexLocalBrain,
    parse_director_output_with_telemetry,
    validate_director_output,
    validate_motion_output,
    validate_segment_output,
)
from live_contentops.retention_native_motion_sandbox_v2 import (
    validate_generated_motion_files,
    validate_revision_accounting,
)
from live_contentops.retention_native_replacement_runner_v2 import (
    minimal_raw_director_retry_budget,
)
from live_contentops.retention_native_storyboard_v2 import (
    contact_sheet,
    render_native_chart,
    render_native_document,
    render_native_map,
    render_storyboard_frame,
)


def _bible() -> dict:
    return {
        "core_viewer_promise": "Understand what reopened Hormuz flows change.",
        "hook": "A real chokepoint reopened, but price is not proof.",
        "central_question": "Can physical supply normalize?",
        "narrative_arc": "Place to mechanism to forecast to checkpoints.",
        "tone": "urgent, sober, explanatory",
        "pacing_profile": "fast context, measured evidence, clear payoff",
        "evidence_hierarchy": ["EIA release", "governed article", "FRED observation"],
        "concrete_visual_strategy": "Concrete documentary context before abstraction.",
        "documentary_broll_strategy": "Use recognizable shipping and oil infrastructure.",
        "data_document_strategy": "Native charts and readable EIA excerpts.",
        "abstraction_policy": "Only explain invisible causality after concrete context.",
        "audio_intent": "Restrained newsroom urgency.",
        "short_strategy": "One mechanism and one confirmation loop.",
        "midform_strategy": "Build geography, mechanism, forecast, and falsifiers.",
        "forbidden_motifs_repetition": ["generic cards", "unexplained geometry"],
    }


def _segments() -> list[dict]:
    common = {
        "allowed_claim_ids": ["claim-a"],
        "allowed_evidence_ids": ["evidence-a"],
        "viewer_knowledge_leaving": ["new knowledge"],
        "open_loops": [],
        "target_timing_envelope": {
            "short_9x16": {"min_seconds": 5, "max_seconds": 15},
            "midform_16x9": {"min_seconds": 10, "max_seconds": 30},
        },
        "asset_needs": ["recognizable Hormuz geography"],
        "continuity_constraints": ["preserve EIA forecast boundary"],
    }
    return [
        {
            **common,
            "segment_id": "place",
            "purpose": "establish the real place",
            "narrative_question": "Where is the chokepoint?",
            "dependencies": [],
            "viewer_knowledge_entering": [],
            "payoff_rehook_responsibility": "open physical-flow question",
        },
        {
            **common,
            "segment_id": "mechanism",
            "purpose": "explain supply recovery",
            "narrative_question": "What changed physically?",
            "dependencies": ["place"],
            "viewer_knowledge_entering": ["Hormuz is a real chokepoint"],
            "payoff_rehook_responsibility": "pay place loop and open forecast loop",
        },
    ]


def _grounding(**overrides) -> dict:
    row = {
        "beat_id": "b1",
        "viewer_takeaway": "Hormuz is a real shipping chokepoint.",
        "narration_intent": "Name the location and change.",
        "primary_visual_type": "documentary_context",
        "recognizable_subject": "oil tanker crossing the Strait of Hormuz",
        "required_asset_ids": ["tanker"],
        "preferred_asset_ids": ["gulf-map"],
        "abstract_substitution_allowed": False,
        "recognition_deadline_seconds": 1.0,
        "captions_hidden_takeaway": "Oil ships pass through a narrow real strait.",
        "aspect_ratio": "9:16",
        "claim_ids": ["claim-a"],
        "evidence_ids": ["evidence-a"],
        "continuity_role": "hook",
    }
    row.update(overrides)
    return row


def _asset(asset_id: str, purpose: str, width: int, height: int) -> AssetCandidate:
    return AssetCandidate.from_mapping(
        {
            "asset_id": asset_id,
            "visual_class": "documentary_context",
            "source_url": "https://example.gov/asset.jpg",
            "rights_status": "PUBLIC_DOMAIN",
            "license_or_terms": "U.S. government work",
            "attribution": "Source: Example agency",
            "sha256": hashlib.sha256(asset_id.encode()).hexdigest(),
            "width": width,
            "height": height,
            "semantic_purposes": [purpose],
            "recognizable_focal_object": purpose,
            "documentary": True,
            "illustrative": False,
            "crop_suitability": {"short_9x16": 0.9, "midform_16x9": 0.8},
        }
    )


def test_creative_roles_start_xhigh_and_fallback_only_within_gpt56() -> None:
    for role in (
        ROLE_V2_CREATIVE_EDITOR,
        ROLE_V2_MOTION_CODE_AUTHOR,
        ROLE_V2_CREATIVE_REVISION_AUTHOR,
    ):
        assert model_pool_for_role(role) == V2_CREATIVE_MODEL_POOL
        assert V2_CREATIVE_MODEL_POOL == (
            "new/gpt-5.6-sol-xhigh",
            "new/gpt-5.6-sol-high",
            "new/gpt-5.6-sol-medium",
        )
        budget = retry_budget_for_role(role_task_id=role, logical_invocation_id="inv")
        assert budget.max_total_provider_attempts == 3
        assert budget.max_same_model_retries == 0


def test_minimal_raw_director_experiment_is_exactly_one_xhigh_attempt() -> None:
    budget = minimal_raw_director_retry_budget("inv_v2_director_test")
    assert budget.max_total_provider_attempts == 1
    assert budget.max_fallback_transitions == 0
    assert budget.max_same_model_retries == 0
    assert budget.max_structured_output_repair_attempts == 0
    assert budget.per_model_max_attempts == (1, 0, 0)


def test_codex_local_brain_is_inert() -> None:
    assert CodexLocalBrain.active is False
    with pytest.raises(RuntimeError, match="INERT"):
        CodexLocalBrain().author()


def test_creative_bible_freeze_is_stable_and_concrete() -> None:
    first = CreativeBible.from_mapping(_bible()).freeze()
    second = CreativeBible.from_mapping(_bible()).freeze()
    assert first == second
    assert first["immutable"] is True


def test_segment_graph_is_dynamic_and_dependency_ordered() -> None:
    graph = validate_segment_graph(_segments())
    assert [row.segment_id for row in graph] == ["place", "mechanism"]
    invalid = list(reversed(_segments()))
    with pytest.raises(ValueError, match="dependency_not_prior"):
        validate_segment_graph(invalid)


def test_deterministic_child_prompt_is_bounded_and_hash_stable() -> None:
    bible = CreativeBible.from_mapping(_bible()).freeze()
    segment = validate_segment_graph(_segments())[0]
    evidence = {
        "claims": {"claim-a": {"value": "bound"}, "claim-b": {"value": "excluded"}},
        "evidence": {"evidence-a": {"sha256": "a"}, "evidence-b": {"sha256": "b"}},
    }
    first = build_segment_prompt(
        creative_bible_frozen=bible,
        segment=segment,
        governed_evidence=evidence,
        continuity_state={},
        available_assets=[{"asset_id": "tanker"}],
        previous_summary=None,
        next_summary="mechanism",
    )
    second = build_segment_prompt(
        creative_bible_frozen=bible,
        segment=segment,
        governed_evidence=evidence,
        continuity_state={},
        available_assets=[{"asset_id": "tanker"}],
        previous_summary=None,
        next_summary="mechanism",
    )
    assert first == second
    assert set(first["payload"]["governed_evidence"]["claims"]) == {"claim-a"}
    assert set(first["payload"]["governed_evidence"]["evidence"]) == {"evidence-a"}


def test_required_real_asset_cannot_allow_abstract_substitution() -> None:
    with pytest.raises(ValueError, match="cannot_allow_abstract"):
        VisualGroundingContract.from_mapping(
            _grounding(abstract_substitution_allowed=True)
        )


def test_must_use_asset_enforcement_blocks_silent_substitution() -> None:
    contract = VisualGroundingContract.from_mapping(_grounding())
    assert enforce_must_use_assets([contract], {"b1": ["tanker"]})["status"] == "PASS"
    blocked = enforce_must_use_assets([contract], {"b1": ["generic-svg"]})
    assert blocked["status"] == "BLOCK"
    assert blocked["silent_abstraction_substitution"] is True


def test_asset_broker_prefers_semantic_relevance_and_viable_crop() -> None:
    candidates = [
        _asset("tanker", "oil tanker shipping", 2400, 1600),
        _asset("refinery", "oil refinery", 1200, 800),
    ]
    ranked = broker_assets(
        candidates, semantic_need="recognizable oil tanker shipping", variant_id="short_9x16"
    )
    assert ranked[0]["asset_id"] == "tanker"


def test_native_compilers_reject_landscape_drop_and_generic_map() -> None:
    chart = compile_chart_plan(
        {"points": [{"x": "June", "y": 85}, {"x": "Q3", "y": 74}], "source_label": "EIA"},
        "short_9x16",
    )
    assert chart["composition"] == "portrait_stacked_direct_labels"
    assert chart["letterboxed_landscape_source"] is False
    with pytest.raises(ValueError, match="recognizable_geography"):
        compile_map_plan({"labels": ["Strait of Hormuz"], "geography_source": "EIA"}, "short_9x16")
    map_plan = compile_map_plan(
        {
            "labels": ["Persian Gulf", "Strait of Hormuz", "Gulf of Oman"],
            "geography_source": "Natural Earth plus EIA place binding",
        },
        "short_9x16",
    )
    assert map_plan["generic_geometry_forbidden"] is True
    document = compile_document_plan(
        {
            "document_asset_id": "eia-release",
            "source_label": "U.S. EIA",
            "source_date": "2026-07-07",
            "governed_excerpt": "EIA expects continued inventory builds.",
        },
        "short_9x16",
    )
    assert document["focus_mode"] == "portrait_sentence_crop"


def test_comprehension_gate_is_blocking() -> None:
    all_pass = {
        "first_second_context": True,
        "concrete_recognition": True,
        "semantic_continuity": True,
        "captions_hidden_story_reconstruction": True,
        "asset_plan_compliance": True,
        "abstract_only_run": True,
    }
    concepts = [
        "oil_and_hormuz",
        "shipping_supply_changed",
        "eia_forecast_source",
        "production_inventories_demand_matter",
        "price_not_proof",
        "future_confirmation_points",
    ]
    assert evaluate_comprehension_gate(assessments=all_pass, reconstructed_concepts=concepts)[
        "motion_code_authorized"
    ] is True
    all_pass["first_second_context"] = False
    assert evaluate_comprehension_gate(assessments=all_pass, reconstructed_concepts=concepts)[
        "status"
    ] == "BLOCK"


def test_visual_mix_blocks_abstract_dominance() -> None:
    passing = visual_mix_summary(
        [
            {"primary_visual_type": "documentary_context", "duration_seconds": 8},
            {"primary_visual_type": "primary_document", "duration_seconds": 5},
            {"primary_visual_type": "pure_abstraction", "duration_seconds": 2},
        ]
    )
    assert passing["status"] == "PASS"
    assert visual_mix_summary(
        [{"primary_visual_type": "pure_abstraction", "duration_seconds": 10}]
    )["status"] == "BLOCK"


def test_director_and_segment_validators_accept_contract_shape() -> None:
    director = {"creative_bible": _bible(), "segment_graph": _segments()}
    ok, failure, parsed, _ = validate_director_output(__import__("json").dumps(director))
    assert ok is True and failure is None and parsed
    beat = {
        **_grounding(),
        "narration": "This is the Strait of Hormuz.",
        "storyboard_frame": "Full-bleed tanker and labeled geographic inset.",
        "focal_object": "tanker bow",
        "source_label": "NASA / EIA",
        "duration_seconds": 7,
        "asset_ids": ["tanker"],
        "asset_placement": "full_bleed",
        "crop_anchor": "center",
        "motion_intent": "restrained forward reframe",
        "transition_intent": "hard cut",
        "timing_easing": "linear hold then ease-out reframe",
        "audio_state": "cold_open",
        "sfx_kind": "none",
        "sfx_at_fraction": 0,
    }
    segment = {
        "segment_summary": "Place established.",
        "continuity_state_leaving": ["viewer knows location"],
        "short_9x16_beats": [beat],
        "midform_16x9_beats": [{**beat, "beat_id": "m1", "aspect_ratio": "16:9"}],
    }
    assert validate_segment_output(__import__("json").dumps(segment))[0] is True


def test_director_deterministic_repair_records_only_mechanical_operations() -> None:
    raw = (
        "Leading transport prose that is not creative content.\n```json\n"
        + __import__("json").dumps(
            {"creative_bible": _bible(), "segment_graph": _segments()}, indent=2
        )[:-2]
        + ",\n}\n```"
    )
    parsed, telemetry = parse_director_output_with_telemetry(raw)
    assert parsed["creative_bible"]["core_viewer_promise"] == (
        "Understand what reopened Hormuz flows change."
    )
    assert telemetry["route"] == "DETERMINISTIC_REPAIR"
    assert telemetry["operations"] == [
        "strip_trailing_commas_outside_strings",
        "extract_json_object_span",
    ]
    assert telemetry["creative_meaning_changed"] is False


def test_motion_validator_and_sandbox_block_unsafe_source() -> None:
    payload = {
        "batch_id": "batch-1",
        "beat_ids": ["b1"],
        "files": [
            {
                "path": "src/generated/batch_1.tsx",
                "source": "import React from 'react'; export const B=()=> <div data-beat='b1'/>;",
            }
        ],
    }
    assert validate_motion_output(__import__("json").dumps(payload))[0] is True
    assert validate_generated_motion_files(payload["files"], expected_beat_ids=["b1"])[
        "status"
    ] == "PASS"
    unsafe = [{"path": "src/generated/x.tsx", "source": "fetch('https://x'); // b1"}]
    assert validate_generated_motion_files(unsafe, expected_beat_ids=["b1"])["status"] == "BLOCK"


def test_revision_accounting_and_public_safety() -> None:
    rows = [
        {"kind": "MECHANICAL"},
        {
            "kind": "SYSTEMIC_STORYBOARD",
            "effective_model": "new/gpt-5.6-sol-xhigh",
            "receipt_sha256": "a",
        },
        {
            "kind": "RENDERED_LOCALIZED",
            "effective_model": "new/gpt-5.6-sol-xhigh",
            "receipt_sha256": "b",
        },
    ]
    assert validate_revision_accounting(rows)["status"] == "PASS"
    safety = zero_public_write_manifest()
    assert safety["public_write_authority"] is False
    assert safety["uploads"] == safety["v1_store_mutations"] == 0


def test_native_compilers_and_storyboard_render_real_pixels(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    Image.new("RGB", (800, 600), (34, 88, 112)).save(source)
    chart_plan = compile_chart_plan(
        {
            "points": [
                {"x": "June", "y": 85, "label": "$85"},
                {"x": "Q3", "y": 74, "label": "$74"},
            ],
            "source_label": "Source: EIA",
        },
        "short_9x16",
    )
    chart = render_native_chart(
        chart_plan, output_path=tmp_path / "chart.png", width=540, height=800
    )
    map_plan = compile_map_plan(
        {
            "labels": ["Persian Gulf", "Strait of Hormuz", "Gulf of Oman"],
            "geography_source": "U.S. EIA",
        },
        "short_9x16",
    )
    map_row = render_native_map(
        map_plan,
        source_path=source,
        output_path=tmp_path / "map.png",
        width=540,
        height=960,
    )
    document_plan = compile_document_plan(
        {
            "document_asset_id": "eia-release",
            "source_label": "U.S. EIA",
            "source_date": "July 7, 2026",
            "governed_excerpt": "Trade flows may return near pre-conflict levels.",
        },
        "short_9x16",
    )
    document = render_native_document(
        document_plan,
        output_path=tmp_path / "document.png",
        width=540,
        height=800,
    )
    beat = {
        **_grounding(required_asset_ids=["source"], preferred_asset_ids=[]),
        "asset_ids": ["source"],
        "narration": "This is the Strait of Hormuz.",
        "source_label": "Source: EIA",
        "asset_placement": "full_bleed",
        "crop_anchor": "center",
        "onscreen_label": "Oil moves through a real chokepoint",
    }
    frame = render_storyboard_frame(
        beat,
        asset_paths={"source": str(source)},
        output_path=tmp_path / "frame.jpg",
        width=540,
        height=960,
    )
    sheet = contact_sheet([frame], output_path=tmp_path / "sheet.jpg", columns=1)
    for row in (chart, map_row, document, frame, sheet):
        assert Path(row["path"]).is_file()
        assert len(row["sha256"]) == 64
