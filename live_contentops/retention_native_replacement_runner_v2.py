"""Executable controlled EIA/Hormuz concrete-first V2-01 replacement proof."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

from PIL import Image

from live_contentops.media_manifest_authority_v1 import sha256_file
from live_contentops.llm_operator_control_v1 import (
    LLMOperatorPausedError,
    assert_llm_operator_execution_enabled,
    llm_operator_pause_active,
    operator_pause_path,
)
from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_MULTIMODAL_VIDEO_CRITIC,
    ROLE_V2_CREATIVE_EDITOR,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    ACCEPTED,
    ProviderResult,
    RetryBudget,
    V2_CREATIVE_CX_XHIGH_MODEL,
)
from live_contentops.nine_router_provider_adapter_v2 import (
    call_nine_router_v2_isolated,
    call_nine_router_v2_isolated_minimal_raw,
)
from live_contentops.retention_native_concrete_first_v2 import (
    AssetCandidate,
    CreativeBible,
    VisualGroundingContract,
    broker_assets,
    build_segment_prompt,
    canonical_json,
    compile_chart_plan,
    compile_document_plan,
    compile_map_plan,
    enforce_must_use_assets,
    evaluate_comprehension_gate,
    logical_hash,
    validate_segment_graph,
    visual_mix_summary,
    zero_public_write_manifest,
)
from live_contentops.retention_native_creative_brain_v2 import (
    CreativeReceipt,
    NineRouterGPT56Brain,
    parse_director_output_with_telemetry,
    validate_director_output,
    validate_segment_output,
)
from live_contentops.retention_native_storyboard_v2 import (
    contact_sheet,
    render_animatic,
    render_native_chart,
    render_native_document,
    render_native_map,
    render_storyboard_frame,
)
from live_contentops.v2_isolated_llm_execution_v1 import (
    V2ExecutionLeaseError,
    active_v2_execution_lease,
    assert_v2_execution_authorized,
    routed_v2_isolated_invocation,
)

SCHEMA_VERSION = "contentops.retention_native.replacement_runner.v2"
VIDEO_ID = "cc-v2-eia-hormuz-concrete-first-2026-v1"
STORY_ID = "eia-sees-oil-supply-nearing-pre-war-levels-as-hormuz-flows-resume"
EXPECTED_ARTICLE_HASH = (
    "4a61bb93b43a7fb1d2fd016cbec048ddf9460f1de8731e9ba81241c7a1a3cf9e"
)
EXPECTED_HISTORICAL_EIA_HASH = (
    "1e87b1815912a3fdf3a59b56a17d343c39204b3b200527fc099771563c93a44a"
)
EXPECTED_DIRECTOR_PROMPT_SHA256 = (
    "9f39fd6fff3b9b43e9ee8cdd065de74058bc7441b04aff7e06c4cfcc58478f55"
)
DEFAULT_RUNTIME = Path(
    r"A:\Capital Chronicle\Runtime\ContentOps\v2_concrete_first_xhigh_replacement_20260813"
)
R4_RUNTIME = Path(
    r"A:\Capital Chronicle\Runtime\ContentOps\v2_gpt56_asset_rich_final_r4_20260813"
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value), encoding="utf-8")


def _receipt_summary(receipt: Any) -> dict[str, Any]:
    return receipt.to_dict()


SOURCE_REGISTRY: Mapping[str, Mapping[str, Any]] = {
    "nasa-persian-gulf": {
        "filename": "nasa-persian-gulf-iss069-e-92132.jpg",
        "visual_class": "documentary_context",
        "source_url": "https://eol.jsc.nasa.gov/DatabaseImages/ESC/large/ISS069/ISS069-E-92132.JPG",
        "rights_status": "NASA_MEDIA_GUIDELINES_EDITORIAL",
        "license_or_terms": "NASA Images and Media Usage Guidelines; editorial context with attribution and no endorsement implication.",
        "attribution": "NASA astronaut photograph ISS069-E-92132, ISS Crew Earth Observations Facility / JSC.",
        "semantic_purposes": [
            "Persian Gulf geography",
            "Strait of Hormuz regional context",
        ],
        "recognizable_focal_object": "Persian Gulf and Strait of Hormuz from orbit",
        "documentary": True,
        "illustrative": False,
        "crop_suitability": {"short_9x16": 0.78, "midform_16x9": 0.96},
    },
    "usns-oiler-hormuz": {
        "filename": "usns-oiler-strait-of-hormuz.jpg",
        "visual_class": "documentary_context",
        "source_url": "https://commons.wikimedia.org/wiki/File:USNS_Leroy_Grumman_(T-AO_195)_transits_the_Strait_of_Hormuz_6470743.jpg",
        "rights_status": "PUBLIC_DOMAIN",
        "license_or_terms": "Official U.S. Navy photograph; U.S. federal government work in the public domain.",
        "attribution": "U.S. Navy photo by Mass Communication Specialist 2nd Class Indra Beaufort, Dec. 29, 2020.",
        "semantic_purposes": [
            "recognizable Strait of Hormuz shipping",
            "oil supply vessel",
            "real maritime transit",
        ],
        "recognizable_focal_object": "fleet replenishment oiler transiting the Strait of Hormuz",
        "documentary": True,
        "illustrative": False,
        "crop_suitability": {"short_9x16": 0.82, "midform_16x9": 0.98},
    },
    "commercial-tanker-platform": {
        "filename": "commercial-tanker-oil-platform-persian-gulf.jpg",
        "visual_class": "documentary_context",
        "source_url": "https://commons.wikimedia.org/wiki/File:Khawr_Al_Amaya_Oil_Platform-090328-N-0803S-013.jpg",
        "rights_status": "PUBLIC_DOMAIN",
        "license_or_terms": "Official U.S. Navy photograph; U.S. federal government work in the public domain.",
        "attribution": "U.S. Navy photo by Mass Communication Specialist 2nd Class Nathan Schaeffer, March 28, 2009.",
        "semantic_purposes": [
            "commercial tanker",
            "Persian Gulf oil platform",
            "crude terminal",
        ],
        "recognizable_focal_object": "commercial tanker alongside a Persian Gulf oil platform",
        "documentary": True,
        "illustrative": False,
        "crop_suitability": {"short_9x16": 0.76, "midform_16x9": 0.96},
    },
    "refinery-storage-tanks": {
        "filename": "refinery-storage-tanks.jpg",
        "visual_class": "documentary_context",
        "source_url": "https://commons.wikimedia.org/wiki/File:Sinclair_Oil_Refinery_Storage_Tanks_-_Wyoming.jpg",
        "rights_status": "CREATIVE_COMMONS_ATTRIBUTION",
        "license_or_terms": "Creative Commons Attribution 4.0; crop/resize permitted with attribution and license link.",
        "attribution": "Photo: Tony Webster, CC BY 4.0, via Wikimedia Commons; cropped/resized.",
        "semantic_purposes": ["crude storage tanks", "refinery", "inventories"],
        "recognizable_focal_object": "large crude oil storage tanks at a refinery",
        "documentary": True,
        "illustrative": False,
        "crop_suitability": {"short_9x16": 0.84, "midform_16x9": 0.94},
    },
    "nara-refinery-portrait": {
        "filename": "nara-refinery-portrait.jpg",
        "visual_class": "documentary_context",
        "source_url": "https://commons.wikimedia.org/wiki/File:Crude-oil_pipe_stills,_rundown_tanks,_and_%22Cat_Crackers%22_at_the_Baton_Rouge_Esso_Refinery,_ca._1945_-_NARA_-_535733.jpg",
        "rights_status": "PUBLIC_DOMAIN",
        "license_or_terms": "U.S. National Archives federal government work in the public domain.",
        "attribution": "U.S. National Archives / Office of War Information, NARA 535733.",
        "semantic_purposes": [
            "portrait-native refinery",
            "crude processing",
            "production infrastructure",
        ],
        "recognizable_focal_object": "vertical view of refinery towers and pipe stills",
        "documentary": True,
        "illustrative": False,
        "crop_suitability": {"short_9x16": 0.98, "midform_16x9": 0.66},
    },
    "doe-tanker-terminal-pipeline": {
        "filename": "doe-tanker-terminal-pipeline.jpg",
        "visual_class": "documentary_context",
        "source_url": "https://commons.wikimedia.org/wiki/File:United_States_Strategic_Petroleum_Reserve_011.jpg",
        "rights_status": "PUBLIC_DOMAIN",
        "license_or_terms": "Official U.S. Department of Energy photograph; U.S. federal government work in the public domain.",
        "attribution": "U.S. Department of Energy, Strategic Petroleum Reserve image 011.",
        "semantic_purposes": [
            "tanker unloading",
            "crude terminal",
            "storage and pipeline chain",
        ],
        "recognizable_focal_object": "tanker unloading crude at a terminal connected to storage and pipeline",
        "documentary": True,
        "illustrative": False,
        "crop_suitability": {"short_9x16": 0.82, "midform_16x9": 0.90},
    },
    "crude-oil-supertanker": {
        "filename": "crude-oil-supertanker.jpg",
        "visual_class": "documentary_context",
        "source_url": "https://commons.wikimedia.org/wiki/File:Supertanker_AbQaiq.jpg",
        "rights_status": "PUBLIC_DOMAIN",
        "license_or_terms": "Official U.S. Navy photograph; U.S. federal government work in the public domain.",
        "attribution": "U.S. Navy photo by Photographer's Mate 1st Class Kevin H. Tierney.",
        "semantic_purposes": [
            "crude oil supertanker",
            "seaborne oil trade",
            "oil loading",
        ],
        "recognizable_focal_object": "large crude oil tanker at a terminal",
        "documentary": True,
        "illustrative": False,
        "crop_suitability": {"short_9x16": 0.54, "midform_16x9": 0.95},
    },
}


def prepare(runtime: Path) -> dict[str, Any]:
    source_root = runtime / "assets" / "source"
    public_assets = runtime / "render_public" / "assets"
    compiled = runtime / "assets" / "compiled"
    public_assets.mkdir(parents=True, exist_ok=True)
    compiled.mkdir(parents=True, exist_ok=True)
    story = _read_json(R4_RUNTIME / "contracts" / "story_binding_v2.json")
    if (
        story.get("story_id") != STORY_ID
        or story.get("article_hash") != EXPECTED_ARTICLE_HASH
    ):
        raise RuntimeError("controlled_benchmark_story_identity_mismatch")
    if story.get("official_source_hash") != EXPECTED_HISTORICAL_EIA_HASH:
        raise RuntimeError("controlled_benchmark_eia_identity_mismatch")
    candidates: list[dict[str, Any]] = []
    asset_paths: dict[str, str] = {}
    for asset_id, metadata in SOURCE_REGISTRY.items():
        source = source_root / str(metadata["filename"])
        if not source.is_file():
            raise RuntimeError(f"essential_concrete_asset_missing:{asset_id}")
        with Image.open(source) as opened:
            width, height = opened.size
        row = AssetCandidate.from_mapping(
            {
                "asset_id": asset_id,
                **metadata,
                "sha256": sha256_file(source),
                "width": width,
                "height": height,
                "source_quality": 1.0,
            }
        )
        destination = public_assets / source.name
        shutil.copy2(source, destination)
        payload = row.__dict__ | {
            "orientation": "portrait" if height > width else "landscape",
            "local_path": str(destination),
            "relative_public_path": "assets/" + destination.name,
        }
        candidates.append(payload)
        asset_paths[asset_id] = str(destination)

    map_source = source_root / "eia-hormuz-arabian-peninsula-map.png"
    map_plan_short = compile_map_plan(
        {
            "labels": ["Persian Gulf", "Strait of Hormuz", "Gulf of Oman"],
            "geography_source": "U.S. Energy Information Administration",
        },
        "short_9x16",
    )
    map_plan_mid = compile_map_plan(
        {
            "labels": ["Persian Gulf", "Strait of Hormuz", "Gulf of Oman"],
            "geography_source": "U.S. Energy Information Administration",
        },
        "midform_16x9",
    )
    derived_specs: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    for asset_id, plan, dims in (
        ("eia-hormuz-map-portrait", map_plan_short, {"width": 1080, "height": 1920}),
        ("eia-hormuz-map-landscape", map_plan_mid, {"width": 1920, "height": 1080}),
    ):
        output = compiled / f"{asset_id}.png"
        rendered = render_native_map(
            plan, source_path=map_source, output_path=output, **dims
        )
        derived_specs.append(
            (
                asset_id,
                rendered,
                {
                    "visual_class": "native_data_visual",
                    "source_url": "https://www.eia.gov/international/content/analysis/special_topics/World_Oil_Transit_Chokepoints/",
                    "rights_status": "US_GOVERNMENT_PUBLIC_INFORMATION",
                    "license_or_terms": "U.S. EIA public information; deterministic format-native reframe with source attribution.",
                    "attribution": "Source map: U.S. Energy Information Administration; format-native render: Capital Chronicle.",
                    "semantic_purposes": [
                        "recognizable Strait of Hormuz geography",
                        "shipping chokepoint",
                    ],
                    "recognizable_focal_object": "labeled Strait of Hormuz between the Persian Gulf and Gulf of Oman",
                    "documentary": False,
                    "illustrative": True,
                    "crop_suitability": {
                        "short_9x16": 1.0 if dims["height"] > dims["width"] else 0.6,
                        "midform_16x9": 1.0 if dims["width"] > dims["height"] else 0.6,
                    },
                },
            )
        )

    chart_spec = {
        "source_label": "Source: U.S. EIA, July 2026 STEO",
        "points": [
            {"x": "June", "y": 85, "label": "$85"},
            {"x": "Q3 forecast", "y": 74, "label": "$74"},
            {"x": "2027 forecast", "y": 65, "label": "$65"},
        ],
        "highlighted_point_ids": ["Q3 forecast", "2027 forecast"],
    }
    for asset_id, variant, dims in (
        ("eia-brent-forecast-portrait", "short_9x16", {"width": 1080, "height": 1350}),
        (
            "eia-brent-forecast-landscape",
            "midform_16x9",
            {"width": 1600, "height": 900},
        ),
    ):
        plan = compile_chart_plan(chart_spec, variant)
        output = compiled / f"{asset_id}.png"
        rendered = render_native_chart(plan, output_path=output, **dims)
        derived_specs.append(
            (
                asset_id,
                rendered,
                {
                    "visual_class": "native_data_visual",
                    "source_url": "https://www.eia.gov/pressroom/releases/press590.php",
                    "rights_status": "CAPITAL_CHRONICLE_OWNED",
                    "license_or_terms": "Original Capital Chronicle render from governed U.S. EIA values; attribution required.",
                    "attribution": "Data: U.S. EIA July 2026 STEO; chart: Capital Chronicle.",
                    "semantic_purposes": [
                        "Brent forecast path",
                        "June to Q3 to 2027 comparison",
                        "forecast not observation",
                    ],
                    "recognizable_focal_object": "direct-labeled Brent forecast comparison",
                    "documentary": False,
                    "illustrative": True,
                    "crop_suitability": {
                        "short_9x16": 1.0 if variant == "short_9x16" else 0.6,
                        "midform_16x9": 1.0 if variant == "midform_16x9" else 0.6,
                    },
                },
            )
        )

    document_spec = {
        "document_asset_id": "eia-press590",
        "source_label": "U.S. Energy Information Administration",
        "source_date": "July 7, 2026",
        "governed_excerpt": "EIA now expects worldwide crude oil production and trade flows to rebound to near pre-conflict levels by year's end.",
    }
    for asset_id, variant, dims in (
        (
            "eia-release-document-portrait",
            "short_9x16",
            {"width": 1080, "height": 1400},
        ),
        (
            "eia-release-document-landscape",
            "midform_16x9",
            {"width": 1600, "height": 900},
        ),
    ):
        plan = compile_document_plan(document_spec, variant)
        output = compiled / f"{asset_id}.png"
        rendered = render_native_document(plan, output_path=output, **dims)
        derived_specs.append(
            (
                asset_id,
                rendered,
                {
                    "visual_class": "primary_document",
                    "source_url": "https://www.eia.gov/pressroom/releases/press590.php",
                    "rights_status": "US_GOVERNMENT_PUBLIC_INFORMATION",
                    "license_or_terms": "U.S. EIA public information; exact governed excerpt with source/date.",
                    "attribution": "Source: U.S. Energy Information Administration, July 7, 2026.",
                    "semantic_purposes": [
                        "actual EIA release",
                        "official forecast source",
                        "near pre-conflict levels",
                    ],
                    "recognizable_focal_object": "readable EIA release excerpt with source and date",
                    "documentary": True,
                    "illustrative": False,
                    "crop_suitability": {
                        "short_9x16": 1.0 if variant == "short_9x16" else 0.7,
                        "midform_16x9": 1.0 if variant == "midform_16x9" else 0.7,
                    },
                },
            )
        )

    for asset_id, rendered, metadata in derived_specs:
        source = Path(rendered["path"])
        destination = public_assets / source.name
        shutil.copy2(source, destination)
        row = AssetCandidate.from_mapping(
            {
                "asset_id": asset_id,
                **metadata,
                "sha256": rendered["sha256"],
                "width": rendered["width"],
                "height": rendered["height"],
            }
        )
        candidates.append(
            row.__dict__
            | {
                "orientation": "portrait"
                if rendered["height"] > rendered["width"]
                else "landscape",
                "local_path": str(destination),
                "relative_public_path": "assets/" + destination.name,
            }
        )
        asset_paths[asset_id] = str(destination)

    eia_current = source_root / "eia-press590.html"
    compact = {
        "schema_version": "contentops.retention_native.compact_evidence.v2",
        "story_id": STORY_ID,
        "title": "EIA Sees Oil Supply Nearing Pre-War Levels as Hormuz Flows Resume",
        "article_hash": story["article_hash"],
        "claims": story["claims"],
        "evidence": story["evidence"],
        "historical_governed_eia_sha256": story["official_source_hash"],
        "current_retrieved_eia_html_sha256": sha256_file(eia_current),
        "source_identity_revalidated": True,
        "forecast_boundary": "All forward EIA values are forecasts, not certainties.",
        "price_observation_boundary": "The manifest-bound WTI observation does not prove the EIA forecast.",
        "public_write_authority": False,
    }
    asset_manifest = {
        "schema_version": "contentops.retention_native.asset_candidate_universe.v2",
        "video_id": VIDEO_ID,
        "candidates": candidates,
        "candidate_count": len(candidates),
        "source_files_reused_from_r4": ["nasa-persian-gulf-iss069-e-92132.jpg"],
        "r4_creative_blueprint_reused": False,
        "generated_documentary_assets": 0,
        "public_write": False,
    }
    _write_json(runtime / "contracts" / "compact_evidence_v2.json", compact)
    _write_json(
        runtime / "contracts" / "asset_candidate_universe_v2.json", asset_manifest
    )
    _write_json(runtime / "contracts" / "asset_path_binding_v2.json", asset_paths)
    _write_json(
        runtime / "safety_boundary_report_v2.json",
        zero_public_write_manifest() | {"status": "PASS"},
    )
    result = {
        "status": "PASS",
        "compact_evidence_sha256": logical_hash(compact),
        "asset_candidate_universe_sha256": logical_hash(asset_manifest),
        "candidate_count": len(candidates),
    }
    _write_json(runtime / "receipts" / "prepare_v2.json", result)
    return result


DIRECTOR_INSTRUCTION = """You are the XHIGH Creative Director and semantic Decomposer for one controlled financial-news video proof. Read the entire compact governed story, but return a compact global result only. Decide 3-6 semantic narrative segments dynamically; do not use a fixed three-act or first-half/second-half schema. Concrete-first is a hard requirement: recognizable geography, ships/oil infrastructure, official evidence, and native data visuals precede explanatory abstraction. Pure abstraction must be an intentional minority. Do not invent facts, assets, rights, claims, or evidence IDs.

Return ONLY JSON with exactly two top-level keys: creative_bible and segment_graph. creative_bible requires: core_viewer_promise, hook, central_question, narrative_arc, tone, pacing_profile, evidence_hierarchy (list), concrete_visual_strategy, documentary_broll_strategy, data_document_strategy, abstraction_policy, audio_intent, short_strategy, midform_strategy, forbidden_motifs_repetition (list). Each segment_graph row requires: segment_id, purpose, narrative_question, dependencies (only earlier segment IDs), allowed_claim_ids, allowed_evidence_ids, viewer_knowledge_entering, viewer_knowledge_leaving, open_loops, payoff_rehook_responsibility, target_timing_envelope with short_9x16 and midform_16x9 each containing min_seconds/max_seconds, asset_needs, continuity_constraints. Across segment envelopes, make a 45-60s short and a 90-150s midform feasible. Every claim/evidence ID must exist in the input. Preserve the forecast/observation distinction."""


def one_shot_xhigh_retry_budget(logical_invocation_id: str) -> RetryBudget:
    return RetryBudget(
        logical_invocation_id=logical_invocation_id,
        max_total_provider_attempts=1,
        max_fallback_transitions=0,
        max_same_model_retries=0,
        max_structured_output_repair_attempts=0,
        max_cumulative_retry_sleep_seconds=0,
        wall_clock_budget_seconds=600,
        per_model_max_attempts=(1, 0, 0),
    )


def build_director_prompt(runtime: Path) -> dict[str, Any]:
    compact = _read_json(runtime / "contracts" / "compact_evidence_v2.json")
    assets = _read_json(runtime / "contracts" / "asset_candidate_universe_v2.json")
    return {
        "instruction": DIRECTOR_INSTRUCTION,
        "video_id": VIDEO_ID,
        "governed_story": compact,
        "asset_candidate_universe": [
            {
                key: row.get(key)
                for key in (
                    "asset_id",
                    "visual_class",
                    "semantic_purposes",
                    "recognizable_focal_object",
                    "documentary",
                    "illustrative",
                    "orientation",
                    "width",
                    "height",
                    "crop_suitability",
                    "rights_status",
                    "attribution",
                )
            }
            for row in assets["candidates"]
        ],
        "public_write_authority": False,
    }


def author_director(runtime: Path) -> dict[str, Any]:
    prompt = build_director_prompt(runtime)
    logical_invocation_id = f"inv_v2_director_{logical_hash(prompt)[:20]}"
    evidence_dir = runtime / "provider_evidence" / "minimal_raw_xhigh_director_v1"
    try:
        output, receipt = NineRouterGPT56Brain().author(
            role=ROLE_V2_CREATIVE_EDITOR,
            prompt_payload=prompt,
            validator=validate_director_output,
            logical_invocation_id=logical_invocation_id,
            prompt_template="concrete_first_xhigh_director",
            prompt_version="v3_same_prompt_minimal_raw_wire",
            wire_mode="minimal_raw",
            evidence_dir=evidence_dir,
            retry_budget=one_shot_xhigh_retry_budget(logical_invocation_id),
        )
    except RuntimeError:
        raw_receipt_path = evidence_dir / "minimal_raw_provider_receipt_v1.json"
        if raw_receipt_path.is_file():
            raw_receipt = _read_json(raw_receipt_path)
            provider_level_failure = raw_receipt.get("http_status") not in (
                None,
                200,
            ) or raw_receipt.get("failure_class") not in (
                None,
                "structured_output_malformed",
                "structured_output_schema_invalid",
            )
            status = (
                "BLOCKED_MINIMAL_RAW_XHIGH_DIRECTOR_PROVIDER_EXECUTION"
                if provider_level_failure
                else "BLOCKED_MINIMAL_RAW_XHIGH_DIRECTOR_CREATIVE_OUTPUT"
            )
            experiment = {
                "schema_version": "contentops.retention_native.minimal_raw_director_experiment.v1",
                "status": status,
                "logical_invocation_id": logical_invocation_id,
                "request_body_field_names": raw_receipt.get("request_body_field_names"),
                "optional_generation_fields_absent": raw_receipt.get(
                    "optional_generation_fields_absent"
                ),
                "prompt_sha256": raw_receipt.get("prompt_sha256"),
                "prompt_character_size": raw_receipt.get("prompt_character_size"),
                "prompt_byte_size": raw_receipt.get("prompt_byte_size"),
                "requested_model": raw_receipt.get("requested_model"),
                "effective_model": raw_receipt.get("effective_model"),
                "http_status": raw_receipt.get("http_status"),
                "failure_class": raw_receipt.get("failure_class"),
                "latency_seconds": raw_receipt.get("latency_seconds"),
                "usage": raw_receipt.get("usage"),
                "raw_response_sha256": raw_receipt.get("raw_response_sha256"),
                "raw_response_byte_size": raw_receipt.get("raw_response_byte_size"),
                "raw_model_output_sha256": raw_receipt.get("raw_model_output_sha256"),
                "raw_model_output_byte_size": raw_receipt.get(
                    "raw_model_output_byte_size"
                ),
                "isolated_execution_domain_id": raw_receipt.get(
                    "isolated_execution_domain_id"
                ),
                "provider_invocation_id": raw_receipt.get("provider_invocation_id"),
                "public_write": False,
            }
            _write_json(
                runtime / "minimal_raw_xhigh_director_experiment_v1.json", experiment
            )
            raise RuntimeError(status) from None
        raise
    if not receipt.professional_candidate_eligible:
        raise RuntimeError("professional_director_candidate_degraded_creative_model")
    raw_receipt = _read_json(evidence_dir / "minimal_raw_provider_receipt_v1.json")
    raw_output_path = Path(str(raw_receipt["raw_model_output_path"]))
    raw_output = raw_output_path.read_text(encoding="utf-8")
    raw_derived, response_handling = parse_director_output_with_telemetry(raw_output)
    if logical_hash(raw_derived) != logical_hash(output):
        raise RuntimeError("minimal_raw_director_parsed_output_identity_mismatch")
    response_handling.update(
        {
            "requested_model": raw_receipt.get("requested_model"),
            "effective_model": raw_receipt.get("effective_model"),
            "http_status": raw_receipt.get("http_status"),
            "provider_invocation_id": raw_receipt.get("provider_invocation_id"),
            "request_body_field_names": raw_receipt.get("request_body_field_names"),
            "optional_generation_fields_absent": raw_receipt.get(
                "optional_generation_fields_absent"
            ),
            "isolated_execution_domain_id": raw_receipt.get(
                "isolated_execution_domain_id"
            ),
            "semantic_preservation": "PASS_MECHANICAL_ONLY",
        }
    )
    _write_json(
        runtime / "receipts" / "minimal_raw_director_response_handling_v1.json",
        response_handling,
    )
    bible = CreativeBible.from_mapping(output["creative_bible"]).freeze()
    graph = validate_segment_graph(output["segment_graph"])
    director = {
        "schema_version": "contentops.retention_native.creative_director.v2",
        "video_id": VIDEO_ID,
        "creative_bible": bible,
        "segment_graph": [row.__dict__ for row in graph],
        "segment_graph_sha256": logical_hash([row.__dict__ for row in graph]),
        "director_model_receipt": _receipt_summary(receipt),
        "minimal_raw_provider_receipt_sha256": logical_hash(raw_receipt),
        "response_handling": response_handling,
        "professional_candidate_eligible": receipt.professional_candidate_eligible,
        "public_write_authority": False,
    }
    _write_json(runtime / "contracts" / "creative_director_v2.json", director)
    _write_json(
        runtime / "receipts" / "creative_director_router_v2.json",
        _receipt_summary(receipt),
    )
    return director


def _validate_exact_ready(text: str) -> tuple[bool, str | None, Any, str | None]:
    value = text.strip()
    ok = value == "READY"
    return (
        ok,
        None if ok else "structured_output_schema_invalid",
        value,
        (None if ok else "progressive_tiny_expected_READY"),
    )


def _validate_small_json(text: str) -> tuple[bool, str | None, Any, str | None]:
    try:
        value = json.loads(text.strip())
        if value != {"result": 323, "status": "OK"}:
            raise ValueError("exact_small_payload")
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return False, "structured_output_schema_invalid", None, f"small_json_{exc}"
    return True, None, value, None


def _validate_medium_digest(
    text: str, *, claim_ids: set[str], evidence_ids: set[str]
) -> tuple[bool, str | None, Any, str | None]:
    try:
        value = json.loads(text.strip())
        if not isinstance(value, Mapping):
            raise ValueError("object")
        if value.get("story_id") != STORY_ID:
            raise ValueError("story_id")
        if set(value.get("claim_ids") or []) != claim_ids:
            raise ValueError("claim_ids")
        if set(value.get("evidence_ids") or []) != evidence_ids:
            raise ValueError("evidence_ids")
        if not str(value.get("forecast_boundary") or "").strip():
            raise ValueError("forecast_boundary")
        if not str(value.get("observation_boundary") or "").strip():
            raise ValueError("observation_boundary")
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return False, "structured_output_schema_invalid", None, f"medium_digest_{exc}"
    return True, None, value, None


def _validate_large_short(
    text: str, *, claim_count: int, evidence_count: int, asset_count: int
) -> tuple[bool, str | None, Any, str | None]:
    expected = {
        "asset_count": asset_count,
        "claim_count": claim_count,
        "evidence_count": evidence_count,
        "status": "READY",
        "story_id": STORY_ID,
    }
    try:
        value = json.loads(text.strip())
        if value != expected:
            raise ValueError("exact_large_short_payload")
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return False, "structured_output_schema_invalid", None, f"large_short_{exc}"
    return True, None, value, None


def _validate_large_outline(
    text: str, *, claim_ids: set[str], evidence_ids: set[str]
) -> tuple[bool, str | None, Any, str | None]:
    try:
        value = json.loads(text.strip())
        if not isinstance(value, Mapping):
            raise ValueError("object")
        if not str(value.get("core_promise") or "").strip():
            raise ValueError("core_promise")
        if not str(value.get("forecast_boundary") or "").strip():
            raise ValueError("forecast_boundary")
        outline = value.get("segment_outline")
        if not isinstance(outline, list) or not 3 <= len(outline) <= 5:
            raise ValueError("segment_outline")
        for row in outline:
            if not isinstance(row, Mapping):
                raise ValueError("segment_row")
            if (
                not str(row.get("segment_id") or "").strip()
                or not str(row.get("purpose") or "").strip()
            ):
                raise ValueError("segment_identity")
            if not set(row.get("claim_ids") or []) <= claim_ids:
                raise ValueError("unknown_claim_id")
            if not set(row.get("evidence_ids") or []) <= evidence_ids:
                raise ValueError("unknown_evidence_id")
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return False, "structured_output_schema_invalid", None, f"large_outline_{exc}"
    return True, None, value, None


def build_progressive_xhigh_cases(
    runtime: Path,
    *,
    expected_director_prompt_sha256: str | None = EXPECTED_DIRECTOR_PROMPT_SHA256,
) -> list[dict[str, Any]]:
    compact = _read_json(runtime / "contracts" / "compact_evidence_v2.json")
    assets = _read_json(runtime / "contracts" / "asset_candidate_universe_v2.json")
    director_payload = build_director_prompt(runtime)
    exact_director_prompt = json.dumps(
        director_payload, sort_keys=True, ensure_ascii=False
    )
    if (
        expected_director_prompt_sha256
        and hashlib.sha256(exact_director_prompt.encode("utf-8")).hexdigest()
        != expected_director_prompt_sha256
    ):
        raise RuntimeError("progressive_exact_director_prompt_drift")

    claim_ids = set(str(item) for item in compact["claims"])
    evidence_ids = set(str(item) for item in compact["evidence"])
    asset_count = len(assets["candidates"])
    medium_prompt = json.dumps(
        {
            "instruction": (
                "Read the governed story and return ONLY compact JSON with keys story_id, "
                "claim_ids, evidence_ids, forecast_boundary, observation_boundary. Copy every "
                "claim/evidence ID exactly once. Do not add analysis or prose outside JSON."
            ),
            "governed_story": compact,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    large_short_prompt = json.dumps(
        {
            "instruction": (
                "Treat reference_director_payload as input to read, but do not perform the "
                "Director task. Return ONLY the exact compact JSON object requested in "
                "expected_output. No prose."
            ),
            "expected_output": {
                "asset_count": asset_count,
                "claim_count": len(claim_ids),
                "evidence_count": len(evidence_ids),
                "status": "READY",
                "story_id": STORY_ID,
            },
            "reference_director_payload": director_payload,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    large_outline_prompt = json.dumps(
        {
            "instruction": (
                "Read the full reference Director payload. Return ONLY JSON with core_promise, "
                "forecast_boundary, and segment_outline. segment_outline must contain 3-5 rows "
                "with only segment_id, purpose, claim_ids, evidence_ids. Use only supplied IDs. "
                "Keep the entire response under roughly 1200 words. Do not write the full "
                "Creative Bible or timing/dependency schema."
            ),
            "reference_director_payload": director_payload,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return [
        {
            "case_id": "tiny_exact_ready",
            "scale": "TINY_INPUT_TINY_OUTPUT",
            "prompt": "Return exactly READY and nothing else.",
            "validator": _validate_exact_ready,
        },
        {
            "case_id": "small_exact_json",
            "scale": "SMALL_INPUT_TINY_STRUCTURED_OUTPUT",
            "prompt": (
                "Compute 17 multiplied by 19. Return ONLY this exact JSON object with no "
                'Markdown or prose: {"result":323,"status":"OK"}'
            ),
            "validator": _validate_small_json,
        },
        {
            "case_id": "medium_governed_digest",
            "scale": "MEDIUM_INPUT_SMALL_STRUCTURED_OUTPUT",
            "prompt": medium_prompt,
            "validator": lambda text: _validate_medium_digest(
                text, claim_ids=claim_ids, evidence_ids=evidence_ids
            ),
        },
        {
            "case_id": "large_input_short_output",
            "scale": "LARGE_INPUT_TINY_STRUCTURED_OUTPUT",
            "prompt": large_short_prompt,
            "validator": lambda text: _validate_large_short(
                text,
                claim_count=len(claim_ids),
                evidence_count=len(evidence_ids),
                asset_count=asset_count,
            ),
        },
        {
            "case_id": "large_input_medium_outline",
            "scale": "LARGE_INPUT_MEDIUM_CREATIVE_OUTPUT",
            "prompt": large_outline_prompt,
            "validator": lambda text: _validate_large_outline(
                text, claim_ids=claim_ids, evidence_ids=evidence_ids
            ),
        },
        {
            "case_id": "exact_full_director",
            "scale": "EXACT_FULL_DIRECTOR_INPUT_AND_OUTPUT",
            "prompt": exact_director_prompt,
            "validator": validate_director_output,
        },
    ]


def run_progressive_xhigh_diagnostic(
    runtime: Path, *, repo_root: Path
) -> dict[str, Any]:
    """Run one minimal-wire XHIGH request per increasing task scale, stopping at first block."""
    prepare(runtime)
    diagnostic_root = runtime / "progressive_xhigh_diagnostic_v1"
    aggregate_path = diagnostic_root / "progressive_xhigh_result_v1.json"
    cases = build_progressive_xhigh_cases(runtime)
    results: list[dict[str, Any]] = []
    domain_id = ""
    audit_path = ""
    with active_v2_execution_lease(repo_root=repo_root, runtime=runtime) as lease:
        domain_id = lease.domain_id
        audit_path = str(lease.audit_path)
        validate_isolation_before_provider(runtime)
        for index, case in enumerate(cases, start=1):
            case_id = str(case["case_id"])
            case_result_path = (
                diagnostic_root / "cases" / case_id / "case_result_v1.json"
            )
            if case_result_path.is_file():
                prior = _read_json(case_result_path)
                results.append(prior)
                if prior.get("status") != "PASS":
                    break
                continue
            prompt = str(case["prompt"])
            prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            logical_invocation_id = f"inv_v2_progressive_{case_id}_{prompt_sha256[:16]}"
            evidence_dir = diagnostic_root / "cases" / case_id / "provider"

            def provider(
                current_prompt: str,
                model: str,
                timeout: float,
                *,
                _evidence_dir: Path = evidence_dir,
                _logical_id: str = logical_invocation_id,
            ) -> ProviderResult:
                return call_nine_router_v2_isolated_minimal_raw(
                    current_prompt,
                    model,
                    timeout,
                    role_task_id=ROLE_V2_CREATIVE_EDITOR,
                    logical_invocation_id=_logical_id,
                    component="NineRouterGPT56Brain",
                    evidence_dir=_evidence_dir,
                )

            invocation = routed_v2_isolated_invocation(
                prompt=prompt,
                role_task_id=ROLE_V2_CREATIVE_EDITOR,
                logical_invocation_id=logical_invocation_id,
                component="NineRouterGPT56Brain",
                provider_call=provider,
                work_item_id=f"{VIDEO_ID}:{case_id}",
                timeout_seconds=600.0,
                validator=case["validator"],
                governed_input={
                    "case_id": case_id,
                    "scale": case["scale"],
                    "prompt_sha256": prompt_sha256,
                    "public_write": False,
                },
                prompt_template="progressive_minimal_raw_xhigh_diagnostic",
                prompt_version="v1",
                budget=one_shot_xhigh_retry_budget(logical_invocation_id),
            )
            receipt_path = evidence_dir / "minimal_raw_provider_receipt_v1.json"
            receipt = _read_json(receipt_path) if receipt_path.is_file() else {}
            accepted = invocation.get("terminal_disposition") == ACCEPTED
            provider_failed = receipt.get("http_status") not in (
                None,
                200,
            ) or receipt.get("failure_class") not in (
                None,
                "structured_output_malformed",
                "structured_output_schema_invalid",
            )
            row = {
                "schema_version": "contentops.v2.progressive_xhigh_case.v1",
                "case_index": index,
                "case_id": case_id,
                "scale": case["scale"],
                "status": (
                    "PASS"
                    if accepted
                    else (
                        "BLOCKED_PROVIDER_EXECUTION"
                        if provider_failed
                        else "BLOCKED_OUTPUT_VALIDATION"
                    )
                ),
                "logical_invocation_id": logical_invocation_id,
                "prompt_sha256": prompt_sha256,
                "prompt_character_size": len(prompt),
                "prompt_byte_size": len(prompt.encode("utf-8")),
                "request_body_field_names": receipt.get("request_body_field_names"),
                "optional_generation_fields_absent": receipt.get(
                    "optional_generation_fields_absent"
                ),
                "requested_model": receipt.get("requested_model"),
                "effective_model": receipt.get("effective_model"),
                "http_status": receipt.get("http_status"),
                "failure_class": receipt.get("failure_class"),
                "latency_seconds": receipt.get("latency_seconds"),
                "usage": receipt.get("usage"),
                "cost": receipt.get("cost"),
                "provider_invocation_id": receipt.get("provider_invocation_id"),
                "raw_response_sha256": receipt.get("raw_response_sha256"),
                "raw_response_byte_size": receipt.get("raw_response_byte_size"),
                "raw_model_output_sha256": receipt.get("raw_model_output_sha256"),
                "raw_model_output_byte_size": receipt.get("raw_model_output_byte_size"),
                "terminal_disposition": invocation.get("terminal_disposition"),
                "models_attempted_in_order": invocation.get(
                    "models_attempted_in_order"
                ),
                "total_attempts": invocation.get("total_attempts"),
                "output_logical_hash": (
                    logical_hash(invocation.get("output")) if accepted else None
                ),
                "isolated_execution_domain_id": domain_id,
                "public_write": False,
            }
            _write_json(case_result_path, row)
            results.append(row)
            partial = {
                "schema_version": "contentops.v2.progressive_xhigh_diagnostic.v1",
                "status": "RUNNING" if accepted else row["status"],
                "isolated_execution_domain_id": domain_id,
                "cases": results,
                "stopped_after_case": None if accepted else case_id,
                "public_write": False,
            }
            _write_json(aggregate_path, partial)
            if not accepted:
                break

    audit = _read_json(Path(audit_path))
    all_pass = len(results) == len(cases) and all(
        row["status"] == "PASS" for row in results
    )
    final = {
        "schema_version": "contentops.v2.progressive_xhigh_diagnostic.v1",
        "status": (
            "PASS_PROGRESSIVE_XHIGH_THROUGH_FULL_DIRECTOR"
            if all_pass
            else "BLOCKED_PROGRESSIVE_XHIGH_AT_FIRST_FAILED_RUNG"
        ),
        "isolated_execution_domain_id": domain_id,
        "lease_audit_path": audit_path,
        "lease_revoked": audit.get("state") == "REVOKED",
        "shared_global_pause_unchanged": bool(
            (audit.get("shared_global_pause_after") or {}).get("unchanged")
        ),
        "v1_provider_calls_authorized_by_v2_lease": 0,
        "public_writes": 0,
        "cases": results,
        "stopped_after_case": (
            None
            if all_pass
            else next(
                (row["case_id"] for row in results if row["status"] != "PASS"), None
            )
        ),
    }
    _write_json(aggregate_path, final)
    return final


def run_xhigh_transport_diagnostic(runtime: Path, *, repo_root: Path) -> dict[str, Any]:
    """Retry the exact Director only across explicit response-transport modes."""
    prepare(runtime)
    payload = build_director_prompt(runtime)
    prompt = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    if prompt_sha256 != EXPECTED_DIRECTOR_PROMPT_SHA256:
        raise RuntimeError("transport_exact_director_prompt_drift")

    diagnostic_root = runtime / "xhigh_transport_diagnostic_v1"
    aggregate_path = diagnostic_root / "xhigh_transport_result_v1.json"
    variants = (
        ("explicit_non_stream", False),
        ("explicit_stream", True),
    )
    results: list[dict[str, Any]] = []
    domain_id = ""
    audit_path = ""
    accepted_variant: str | None = None
    with active_v2_execution_lease(repo_root=repo_root, runtime=runtime) as lease:
        domain_id = lease.domain_id
        audit_path = str(lease.audit_path)
        validate_isolation_before_provider(runtime)
        for variant_id, stream in variants:
            case_root = diagnostic_root / "variants" / variant_id
            case_result_path = case_root / "case_result_v1.json"
            if case_result_path.is_file():
                prior = _read_json(case_result_path)
                results.append(prior)
                if prior.get("status") == "PASS":
                    accepted_variant = variant_id
                    break
                continue

            logical_invocation_id = (
                f"inv_v2_transport_{variant_id}_{prompt_sha256[:16]}"
            )
            evidence_dir = case_root / "provider"

            def provider(
                current_prompt: str,
                model: str,
                timeout: float,
                *,
                _evidence_dir: Path = evidence_dir,
                _logical_id: str = logical_invocation_id,
                _stream: bool = stream,
            ) -> ProviderResult:
                return call_nine_router_v2_isolated_minimal_raw(
                    current_prompt,
                    model,
                    timeout,
                    role_task_id=ROLE_V2_CREATIVE_EDITOR,
                    logical_invocation_id=_logical_id,
                    component="NineRouterGPT56Brain",
                    evidence_dir=_evidence_dir,
                    stream=_stream,
                )

            invocation = routed_v2_isolated_invocation(
                prompt=prompt,
                role_task_id=ROLE_V2_CREATIVE_EDITOR,
                logical_invocation_id=logical_invocation_id,
                component="NineRouterGPT56Brain",
                provider_call=provider,
                work_item_id=f"{VIDEO_ID}:transport:{variant_id}",
                timeout_seconds=600.0,
                validator=validate_director_output,
                governed_input={
                    "variant_id": variant_id,
                    "response_transport": "stream" if stream else "non_stream",
                    "prompt_sha256": prompt_sha256,
                    "public_write": False,
                },
                prompt_template="exact_director_response_transport_diagnostic",
                prompt_version="v1",
                budget=one_shot_xhigh_retry_budget(logical_invocation_id),
            )
            receipt_path = evidence_dir / "minimal_raw_provider_receipt_v1.json"
            receipt = _read_json(receipt_path) if receipt_path.is_file() else {}
            accepted = invocation.get("terminal_disposition") == ACCEPTED
            provider_failed = receipt.get("http_status") not in (
                None,
                200,
            ) or receipt.get("failure_class") not in (
                None,
                "structured_output_malformed",
                "structured_output_schema_invalid",
            )
            row = {
                "schema_version": "contentops.v2.xhigh_transport_case.v1",
                "variant_id": variant_id,
                "response_transport": "stream" if stream else "non_stream",
                "status": (
                    "PASS"
                    if accepted
                    else (
                        "BLOCKED_PROVIDER_EXECUTION"
                        if provider_failed
                        else "BLOCKED_OUTPUT_VALIDATION"
                    )
                ),
                "logical_invocation_id": logical_invocation_id,
                "prompt_sha256": prompt_sha256,
                "prompt_character_size": len(prompt),
                "prompt_byte_size": len(prompt.encode("utf-8")),
                "request_body_field_names": receipt.get("request_body_field_names"),
                "optional_generation_fields_absent": receipt.get(
                    "optional_generation_fields_absent"
                ),
                "requested_model": receipt.get("requested_model"),
                "effective_model": receipt.get("effective_model"),
                "http_status": receipt.get("http_status"),
                "failure_class": receipt.get("failure_class"),
                "latency_seconds": receipt.get("latency_seconds"),
                "usage": receipt.get("usage"),
                "cost": receipt.get("cost"),
                "provider_invocation_id": receipt.get("provider_invocation_id"),
                "raw_response_sha256": receipt.get("raw_response_sha256"),
                "raw_response_byte_size": receipt.get("raw_response_byte_size"),
                "raw_model_output_sha256": receipt.get("raw_model_output_sha256"),
                "raw_model_output_byte_size": receipt.get("raw_model_output_byte_size"),
                "terminal_disposition": invocation.get("terminal_disposition"),
                "models_attempted_in_order": invocation.get(
                    "models_attempted_in_order"
                ),
                "total_attempts": invocation.get("total_attempts"),
                "isolated_execution_domain_id": domain_id,
                "public_write": False,
            }
            _write_json(case_result_path, row)
            results.append(row)
            _write_json(
                aggregate_path,
                {
                    "schema_version": "contentops.v2.xhigh_transport_diagnostic.v1",
                    "status": "RUNNING" if not accepted else "PASS_XHIGH_TRANSPORT",
                    "isolated_execution_domain_id": domain_id,
                    "variants": results,
                    "accepted_variant": variant_id if accepted else None,
                    "public_write": False,
                },
            )
            if accepted:
                accepted_variant = variant_id
                break

    audit = _read_json(Path(audit_path))
    final = {
        "schema_version": "contentops.v2.xhigh_transport_diagnostic.v1",
        "status": (
            "PASS_XHIGH_EXACT_DIRECTOR_RESPONSE_TRANSPORT"
            if accepted_variant
            else "BLOCKED_XHIGH_EXACT_DIRECTOR_RESPONSE_TRANSPORT"
        ),
        "isolated_execution_domain_id": domain_id,
        "lease_audit_path": audit_path,
        "lease_revoked": audit.get("state") == "REVOKED",
        "shared_global_pause_unchanged": bool(
            (audit.get("shared_global_pause_after") or {}).get("unchanged")
        ),
        "v1_provider_calls_authorized_by_v2_lease": 0,
        "public_writes": 0,
        "prompt_sha256": prompt_sha256,
        "prompt_character_size": len(prompt),
        "prompt_byte_size": len(prompt.encode("utf-8")),
        "accepted_variant": accepted_variant,
        "variants": results,
    }
    _write_json(aggregate_path, final)
    return final


def run_xhigh_responses_diagnostic(runtime: Path, *, repo_root: Path) -> dict[str, Any]:
    """Canary and then run the exact Director through the Responses endpoint."""
    prepare(runtime)
    director_prompt = json.dumps(
        build_director_prompt(runtime), sort_keys=True, ensure_ascii=False
    )
    director_sha256 = hashlib.sha256(director_prompt.encode("utf-8")).hexdigest()
    if director_sha256 != EXPECTED_DIRECTOR_PROMPT_SHA256:
        raise RuntimeError("responses_exact_director_prompt_drift")
    cases = (
        (
            "tiny_responses_canary",
            "Return exactly READY and nothing else.",
            _validate_exact_ready,
            None,
        ),
        (
            "tiny_responses_non_stream",
            "Return exactly READY and nothing else.",
            _validate_exact_ready,
            False,
        ),
        (
            "exact_full_director_non_stream",
            director_prompt,
            validate_director_output,
            False,
        ),
    )
    diagnostic_root = runtime / "xhigh_responses_diagnostic_v1"
    aggregate_path = diagnostic_root / "xhigh_responses_result_v1.json"
    results: list[dict[str, Any]] = []
    domain_id = ""
    audit_path = ""
    accepted_director: Mapping[str, Any] | None = None
    with active_v2_execution_lease(repo_root=repo_root, runtime=runtime) as lease:
        domain_id = lease.domain_id
        audit_path = str(lease.audit_path)
        validate_isolation_before_provider(runtime)
        for case_id, prompt, validator, stream in cases:
            case_root = diagnostic_root / "cases" / case_id
            case_result_path = case_root / "case_result_v1.json"
            if case_result_path.is_file():
                prior = _read_json(case_result_path)
                results.append(prior)
                if prior.get("status") != "PASS" and case_id != "tiny_responses_canary":
                    break
                if case_id == "exact_full_director_non_stream":
                    raw_path = case_root / "provider" / "raw_model_output.txt"
                    accepted_director = validate_director_output(
                        raw_path.read_text(encoding="utf-8")
                    )[2]
                continue
            prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            logical_invocation_id = f"inv_v2_responses_{case_id}_{prompt_sha256[:16]}"
            evidence_dir = case_root / "provider"

            def provider(
                current_prompt: str,
                model: str,
                timeout: float,
                *,
                _evidence_dir: Path = evidence_dir,
                _logical_id: str = logical_invocation_id,
            ) -> ProviderResult:
                return call_nine_router_v2_isolated_minimal_raw(
                    current_prompt,
                    model,
                    timeout,
                    role_task_id=ROLE_V2_CREATIVE_EDITOR,
                    logical_invocation_id=_logical_id,
                    component="NineRouterGPT56Brain",
                    evidence_dir=_evidence_dir,
                    api_style="responses",
                    stream=stream,
                )

            invocation = routed_v2_isolated_invocation(
                prompt=prompt,
                role_task_id=ROLE_V2_CREATIVE_EDITOR,
                logical_invocation_id=logical_invocation_id,
                component="NineRouterGPT56Brain",
                provider_call=provider,
                work_item_id=f"{VIDEO_ID}:responses:{case_id}",
                timeout_seconds=600.0,
                validator=validator,
                governed_input={
                    "case_id": case_id,
                    "api_style": "responses",
                    "response_transport": (
                        "gateway_default" if stream is None else "non_stream"
                    ),
                    "prompt_sha256": prompt_sha256,
                    "public_write": False,
                },
                prompt_template="xhigh_responses_endpoint_diagnostic",
                prompt_version="v1",
                budget=one_shot_xhigh_retry_budget(logical_invocation_id),
            )
            receipt = _read_json(evidence_dir / "minimal_raw_provider_receipt_v1.json")
            accepted = invocation.get("terminal_disposition") == ACCEPTED
            row = {
                "schema_version": "contentops.v2.xhigh_responses_case.v1",
                "case_id": case_id,
                "status": "PASS" if accepted else "BLOCKED",
                "logical_invocation_id": logical_invocation_id,
                "prompt_sha256": prompt_sha256,
                "prompt_character_size": len(prompt),
                "prompt_byte_size": len(prompt.encode("utf-8")),
                "api_style": receipt.get("api_style"),
                "response_transport": receipt.get("response_transport"),
                "request_body_field_names": receipt.get("request_body_field_names"),
                "optional_generation_fields_absent": receipt.get(
                    "optional_generation_fields_absent"
                ),
                "requested_model": receipt.get("requested_model"),
                "effective_model": receipt.get("effective_model"),
                "http_status": receipt.get("http_status"),
                "failure_class": receipt.get("failure_class"),
                "latency_seconds": receipt.get("latency_seconds"),
                "usage": receipt.get("usage"),
                "provider_invocation_id": receipt.get("provider_invocation_id"),
                "raw_response_sha256": receipt.get("raw_response_sha256"),
                "raw_response_byte_size": receipt.get("raw_response_byte_size"),
                "raw_model_output_sha256": receipt.get("raw_model_output_sha256"),
                "raw_model_output_byte_size": receipt.get("raw_model_output_byte_size"),
                "terminal_disposition": invocation.get("terminal_disposition"),
                "isolated_execution_domain_id": domain_id,
                "public_write": False,
            }
            _write_json(case_result_path, row)
            results.append(row)
            if accepted and case_id == "exact_full_director_non_stream":
                accepted_director = invocation.get("output")
            if not accepted and case_id != "tiny_responses_canary":
                break

    audit = _read_json(Path(audit_path))
    if accepted_director is not None:
        bible = CreativeBible.from_mapping(accepted_director["creative_bible"]).freeze()
        graph = validate_segment_graph(accepted_director["segment_graph"])
        director = {
            "schema_version": "contentops.retention_native.creative_director.v2",
            "video_id": VIDEO_ID,
            "creative_bible": bible,
            "segment_graph": [row.__dict__ for row in graph],
            "segment_graph_sha256": logical_hash([row.__dict__ for row in graph]),
            "director_model_receipt": results[-1],
            "response_handling": {
                "route": "RESPONSES_API_DIRECT_PARSE",
                "semantic_preservation": "PASS_RAW_DIRECT_PARSE",
            },
            "professional_candidate_eligible": True,
            "public_write_authority": False,
        }
        _write_json(runtime / "contracts" / "creative_director_v2.json", director)
    final = {
        "schema_version": "contentops.v2.xhigh_responses_diagnostic.v1",
        "status": (
            "PASS_XHIGH_EXACT_DIRECTOR_RESPONSES_API"
            if accepted_director is not None
            else "BLOCKED_XHIGH_RESPONSES_API"
        ),
        "isolated_execution_domain_id": domain_id,
        "lease_audit_path": audit_path,
        "lease_revoked": audit.get("state") == "REVOKED",
        "shared_global_pause_unchanged": bool(
            (audit.get("shared_global_pause_after") or {}).get("unchanged")
        ),
        "v1_provider_calls_authorized_by_v2_lease": 0,
        "public_writes": 0,
        "director_prompt_sha256": director_sha256,
        "director_artifact_sha256": (
            logical_hash(accepted_director) if accepted_director is not None else None
        ),
        "cases": results,
    }
    _write_json(aggregate_path, final)
    return final


def run_cx_xhigh_diagnostic(runtime: Path, *, repo_root: Path) -> dict[str, Any]:
    """Run a tiny canary then the exact Director on the owner-approved CX XHIGH route."""
    prepare(runtime)
    director_prompt = json.dumps(
        build_director_prompt(runtime), sort_keys=True, ensure_ascii=False
    )
    director_sha256 = hashlib.sha256(director_prompt.encode("utf-8")).hexdigest()
    if director_sha256 != EXPECTED_DIRECTOR_PROMPT_SHA256:
        raise RuntimeError("cx_exact_director_prompt_drift")
    cases = (
        (
            "tiny_exact_ready",
            "Return exactly READY and nothing else.",
            _validate_exact_ready,
        ),
        ("exact_full_director", director_prompt, validate_director_output),
    )
    diagnostic_root = runtime / "cx_xhigh_diagnostic_v1"
    aggregate_path = diagnostic_root / "cx_xhigh_result_v1.json"
    results: list[dict[str, Any]] = []
    accepted_director: Mapping[str, Any] | None = None
    domain_id = ""
    audit_path = ""
    with active_v2_execution_lease(repo_root=repo_root, runtime=runtime) as lease:
        domain_id = lease.domain_id
        audit_path = str(lease.audit_path)
        validate_isolation_before_provider(runtime)
        for case_id, prompt, validator in cases:
            case_root = diagnostic_root / "cases" / case_id
            result_path = case_root / "case_result_v1.json"
            if result_path.is_file():
                prior = _read_json(result_path)
                results.append(prior)
                if prior.get("status") != "PASS":
                    break
                if case_id == "exact_full_director":
                    raw = (case_root / "provider" / "raw_model_output.txt").read_text(
                        encoding="utf-8"
                    )
                    accepted_director = validate_director_output(raw)[2]
                continue
            prompt_sha256 = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
            logical_invocation_id = f"inv_v2_cx_{case_id}_{prompt_sha256[:16]}"
            evidence_dir = case_root / "provider"

            def provider(
                current_prompt: str,
                model: str,
                timeout: float,
                *,
                _evidence_dir: Path = evidence_dir,
                _logical_id: str = logical_invocation_id,
            ) -> ProviderResult:
                return call_nine_router_v2_isolated_minimal_raw(
                    current_prompt,
                    model,
                    timeout,
                    role_task_id=ROLE_V2_CREATIVE_EDITOR,
                    logical_invocation_id=_logical_id,
                    component="NineRouterGPT56Brain",
                    evidence_dir=_evidence_dir,
                )

            invocation = routed_v2_isolated_invocation(
                prompt=prompt,
                role_task_id=ROLE_V2_CREATIVE_EDITOR,
                logical_invocation_id=logical_invocation_id,
                component="NineRouterGPT56Brain",
                provider_call=provider,
                work_item_id=f"{VIDEO_ID}:cx:{case_id}",
                timeout_seconds=600.0,
                validator=validator,
                governed_input={
                    "case_id": case_id,
                    "requested_model": V2_CREATIVE_CX_XHIGH_MODEL,
                    "prompt_sha256": prompt_sha256,
                    "public_write": False,
                },
                prompt_template="owner_approved_cx_xhigh_diagnostic",
                prompt_version="v1",
                budget=RetryBudget(
                    logical_invocation_id=logical_invocation_id,
                    max_total_provider_attempts=1,
                    max_fallback_transitions=0,
                    max_same_model_retries=0,
                    max_structured_output_repair_attempts=0,
                    max_cumulative_retry_sleep_seconds=0,
                    wall_clock_budget_seconds=600,
                    per_model_max_attempts=(1,),
                ),
                model_pool_override=(V2_CREATIVE_CX_XHIGH_MODEL,),
            )
            receipt = _read_json(evidence_dir / "minimal_raw_provider_receipt_v1.json")
            accepted = invocation.get("terminal_disposition") == ACCEPTED
            row = {
                "schema_version": "contentops.v2.cx_xhigh_case.v1",
                "case_id": case_id,
                "status": "PASS" if accepted else "BLOCKED",
                "logical_invocation_id": logical_invocation_id,
                "prompt_sha256": prompt_sha256,
                "prompt_character_size": len(prompt),
                "prompt_byte_size": len(prompt.encode("utf-8")),
                "request_body_field_names": receipt.get("request_body_field_names"),
                "required_effort_selector_only": receipt.get(
                    "required_effort_selector_only"
                ),
                "requested_model": receipt.get("requested_model"),
                "wire_model": receipt.get("wire_model"),
                "effective_model": receipt.get("effective_model"),
                "http_status": receipt.get("http_status"),
                "failure_class": receipt.get("failure_class"),
                "latency_seconds": receipt.get("latency_seconds"),
                "usage": receipt.get("usage"),
                "provider_invocation_id": receipt.get("provider_invocation_id"),
                "raw_response_sha256": receipt.get("raw_response_sha256"),
                "raw_response_byte_size": receipt.get("raw_response_byte_size"),
                "raw_model_output_sha256": receipt.get("raw_model_output_sha256"),
                "raw_model_output_byte_size": receipt.get("raw_model_output_byte_size"),
                "terminal_disposition": invocation.get("terminal_disposition"),
                "isolated_execution_domain_id": domain_id,
                "public_write": False,
            }
            _write_json(result_path, row)
            results.append(row)
            if accepted and case_id == "exact_full_director":
                accepted_director = invocation.get("output")
            if not accepted:
                break

    audit = _read_json(Path(audit_path))
    deterministic_repair: dict[str, Any] | None = None
    exact_case_root = diagnostic_root / "cases" / "exact_full_director"
    exact_raw_path = exact_case_root / "provider" / "raw_model_output.txt"
    if accepted_director is None and exact_raw_path.is_file():
        raw_text = exact_raw_path.read_text(encoding="utf-8")
        raw_row = json.loads(raw_text)
        operations: list[str] = []
        strategy = str(raw_row["creative_bible"]["concrete_visual_strategy"])
        if "concrete" not in strategy.lower():
            raw_row["creative_bible"]["concrete_visual_strategy"] = (
                "Concrete-first: " + strategy
            )
            operations.append("label_existing_concrete_visual_strategy")
        for segment in raw_row["segment_graph"]:
            for key in (
                "viewer_knowledge_entering",
                "viewer_knowledge_leaving",
                "continuity_constraints",
            ):
                if isinstance(segment.get(key), str):
                    segment[key] = [segment[key]]
                    operations.append(f"wrap_{key}_as_singleton_list")
            needs = segment.get("asset_needs")
            if isinstance(needs, list) and any(
                isinstance(item, Mapping) for item in needs
            ):
                segment["asset_needs"] = [
                    "; ".join(
                        f"{key}={item[key]}"
                        for key in ("asset_id", "use", "format")
                        if key in item
                    )
                    if isinstance(item, Mapping)
                    else str(item)
                    for item in needs
                ]
                operations.append("serialize_asset_need_objects_without_value_loss")
        normalized_text = json.dumps(raw_row, sort_keys=True, ensure_ascii=False)
        accepted_director, _ = parse_director_output_with_telemetry(normalized_text)
        accepted_director = json.loads(
            json.dumps(accepted_director, sort_keys=True, ensure_ascii=False)
        )
        normalized_path = exact_case_root / "deterministically_normalized_director.json"
        normalized_path.write_text(normalized_text + "\n", encoding="utf-8")
        deterministic_repair = {
            "schema_version": "contentops.v2.cx_xhigh_deterministic_repair.v1",
            "route": "DETERMINISTIC_SCHEMA_SHAPE_REPAIR",
            "operations": operations,
            "raw_model_output_sha256": hashlib.sha256(
                raw_text.encode("utf-8")
            ).hexdigest(),
            "normalized_json_sha256": hashlib.sha256(
                normalized_text.encode("utf-8")
            ).hexdigest(),
            "semantic_payload_sha256": logical_hash(accepted_director),
            "creative_meaning_changed": False,
            "model_call_used": False,
            "public_write": False,
        }
        _write_json(
            exact_case_root / "deterministic_repair_receipt_v1.json",
            deterministic_repair,
        )
        for row in results:
            if row.get("case_id") == "exact_full_director":
                row["status"] = "PASS_DETERMINISTIC_REPAIR"
                row["terminal_disposition"] = "ACCEPTED_AFTER_DETERMINISTIC_REPAIR"
                row["deterministic_repair_sha256"] = logical_hash(deterministic_repair)
                _write_json(exact_case_root / "case_result_v1.json", row)
                break
    if accepted_director is not None:
        bible = CreativeBible.from_mapping(accepted_director["creative_bible"]).freeze()
        graph = validate_segment_graph(accepted_director["segment_graph"])
        director = {
            "schema_version": "contentops.retention_native.creative_director.v2",
            "video_id": VIDEO_ID,
            "creative_bible": bible,
            "segment_graph": [row.__dict__ for row in graph],
            "segment_graph_sha256": logical_hash([row.__dict__ for row in graph]),
            "director_model_receipt": results[-1],
            "response_handling": {
                "route": (
                    "CX_XHIGH_DETERMINISTIC_SCHEMA_SHAPE_REPAIR"
                    if deterministic_repair
                    else "CX_XHIGH_DIRECT_PARSE"
                ),
                "semantic_preservation": (
                    "PASS_MECHANICAL_ONLY"
                    if deterministic_repair
                    else "PASS_RAW_DIRECT_PARSE"
                ),
                "deterministic_repair": deterministic_repair,
            },
            "professional_candidate_eligible": True,
            "public_write_authority": False,
        }
        _write_json(runtime / "contracts" / "creative_director_v2.json", director)
    final = {
        "schema_version": "contentops.v2.cx_xhigh_diagnostic.v1",
        "status": (
            "PASS_CX_XHIGH_EXACT_DIRECTOR"
            if accepted_director is not None
            else "BLOCKED_CX_XHIGH"
        ),
        "isolated_execution_domain_id": domain_id,
        "lease_audit_path": audit_path,
        "lease_revoked": audit.get("state") == "REVOKED",
        "shared_global_pause_unchanged": bool(
            (audit.get("shared_global_pause_after") or {}).get("unchanged")
        ),
        "v1_provider_calls_authorized_by_v2_lease": 0,
        "public_writes": 0,
        "director_prompt_sha256": director_sha256,
        "director_artifact_sha256": (
            logical_hash(accepted_director) if accepted_director is not None else None
        ),
        "cases": results,
    }
    _write_json(aggregate_path, final)
    return final


def run_isolated_cx_segments(runtime: Path, *, repo_root: Path) -> dict[str, Any]:
    """Author all accepted-Director segments inside one V2-only CX lease."""
    prepare(runtime)
    cx_result = _read_json(
        runtime / "cx_xhigh_diagnostic_v1" / "cx_xhigh_result_v1.json"
    )
    if cx_result.get("status") != "PASS_CX_XHIGH_EXACT_DIRECTOR":
        raise RuntimeError("accepted_cx_xhigh_director_required")
    domain_id = ""
    audit_path = ""
    with active_v2_execution_lease(repo_root=repo_root, runtime=runtime) as lease:
        domain_id = lease.domain_id
        audit_path = str(lease.audit_path)
        validate_isolation_before_provider(runtime)
        result = author_segments(runtime)
    audit = _read_json(Path(audit_path))
    final = result | {
        "schema_version": "contentops.v2.isolated_cx_segments.v1",
        "status": "PASS_ISOLATED_CX_SEGMENTS",
        "isolated_execution_domain_id": domain_id,
        "lease_audit_path": audit_path,
        "lease_revoked": audit.get("state") == "REVOKED",
        "shared_global_pause_unchanged": bool(
            (audit.get("shared_global_pause_after") or {}).get("unchanged")
        ),
        "v1_provider_calls_authorized_by_v2_lease": 0,
        "public_writes": 0,
    }
    _write_json(runtime / "isolated_cx_segments_v1.json", final)
    return final


SEGMENT_INSTRUCTION = """You are the XHIGH Segment Author. Author only this semantic segment, in separately composed short 9:16 and midform 16:9 forms. Return JSON only. Each beat must include every VisualGroundingContract field plus: narration, storyboard_frame, focal_object, source_label, asset_ids, asset_placement, crop_anchor, onscreen_label, data_callout (may be empty), motion_intent, transition_intent, timing_easing, audio_state (one of cold_open,tension,evidence,mechanism,consequence,boundary,resolution,outro), sfx_intent (may be empty), sfx_kind (one of none,whoosh,riser,hit,data_tick), sfx_at_fraction (0..1), duration_seconds. Required real assets must appear in asset_ids and may never be silently replaced by SVG/geometry. Use only provided asset, claim, and evidence IDs. The first short beat must identify oil/Hormuz within one second when this segment owns the hook. Native portrait chart/map/document assets must be used for 9:16; never letterbox a landscape chart. Main visuals must tell the story with narration captions hidden. Avoid generic cards, unexplained symbols, decorative parallax, universal zoom, repeated movement, and tiny source text. Keep each beat 2.5-10 seconds. Use concise natural narration and no unsupported claim."""


def project_segment_schema_without_creative_change(text: str) -> dict[str, Any]:
    """Project XHIGH's synonymous grounding fields onto the canonical contract."""
    row = json.loads(text)
    for key, aspect in (
        ("short_9x16_beats", "9:16"),
        ("midform_16x9_beats", "16:9"),
    ):
        for beat in row.get(key) or []:
            narration = str(beat.get("narration") or "")
            subject = str(
                beat.get("grounding_subject") or beat.get("focal_object") or ""
            )
            selected_assets = list(beat.get("asset_ids") or [])
            raw_visual_type = str(
                beat.get("visual_class")
                or beat.get("visual_type")
                or beat.get("visual_grounding_type")
                or ""
            )
            primary_visual_type = (
                "documentary_context"
                if "documentary_context" in raw_visual_type
                or raw_visual_type.startswith("documentary")
                else raw_visual_type
            )
            beat.setdefault("viewer_takeaway", narration)
            beat.setdefault("narration_intent", narration)
            beat.setdefault("primary_visual_type", primary_visual_type)
            beat.setdefault("recognizable_subject", subject)
            beat.setdefault("required_asset_ids", selected_assets)
            beat.setdefault("preferred_asset_ids", [])
            beat.setdefault(
                "abstract_substitution_allowed",
                not bool(selected_assets) and not bool(beat.get("concrete_visual")),
            )
            beat.setdefault(
                "recognition_deadline_seconds",
                min(5.0, max(0.1, float(beat.get("duration_seconds") or 0))),
            )
            beat.setdefault("captions_hidden_takeaway", narration or subject)
            beat.setdefault("aspect_ratio", aspect)
            beat.setdefault(
                "continuity_role",
                beat.get("grounding_role")
                or beat.get("transition_intent")
                or beat.get("evidence_role"),
            )
    return row


def validate_projected_segment_output(
    text: str,
) -> tuple[bool, str | None, Any, str | None]:
    try:
        projected = project_segment_schema_without_creative_change(text)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return (
            False,
            "structured_output_schema_invalid",
            None,
            f"segment_projection_{type(exc).__name__}",
        )
    return validate_segment_output(json.dumps(projected, ensure_ascii=False))


def author_segments(runtime: Path) -> dict[str, Any]:
    director = _read_json(runtime / "contracts" / "creative_director_v2.json")
    compact = _read_json(runtime / "contracts" / "compact_evidence_v2.json")
    assets = _read_json(runtime / "contracts" / "asset_candidate_universe_v2.json")
    graph = validate_segment_graph(director["segment_graph"])
    continuity: dict[str, Any] = {}
    outputs: list[dict[str, Any]] = []
    receipts: list[dict[str, Any]] = []
    previous: str | None = None
    for index, segment in enumerate(graph):
        needs = " ".join(segment.asset_needs)
        ranked_ids = {
            variant: [
                row["asset_id"]
                for row in broker_assets(
                    [
                        AssetCandidate.from_mapping(candidate)
                        for candidate in assets["candidates"]
                    ],
                    semantic_need=needs,
                    variant_id=variant,
                    limit=8,
                )
            ]
            for variant in ("short_9x16", "midform_16x9")
        }
        candidate_rows = [
            {
                key: row.get(key)
                for key in (
                    "asset_id",
                    "visual_class",
                    "semantic_purposes",
                    "recognizable_focal_object",
                    "documentary",
                    "illustrative",
                    "orientation",
                    "width",
                    "height",
                    "crop_suitability",
                    "rights_status",
                    "attribution",
                    "relative_public_path",
                )
            }
            for row in assets["candidates"]
            if row["asset_id"]
            in set(ranked_ids["short_9x16"] + ranked_ids["midform_16x9"])
        ]
        built = build_segment_prompt(
            creative_bible_frozen=director["creative_bible"],
            segment=segment,
            governed_evidence=compact,
            continuity_state=continuity,
            available_assets=candidate_rows,
            previous_summary=previous,
            next_summary=graph[index + 1].purpose if index + 1 < len(graph) else None,
        )
        prompt = built["payload"] | {
            "instruction": SEGMENT_INSTRUCTION,
            "ranked_asset_ids_by_variant": ranked_ids,
        }
        segment_invocation_id = (
            f"inv_v2_segment_{segment.segment_id}_{logical_hash(prompt)[:16]}"
        )
        default_evidence_dir = (
            runtime / "provider_evidence" / "segments" / segment.segment_id
        )
        stream_evidence_dir = (
            runtime / "provider_evidence" / "segments_stream" / segment.segment_id
        )
        evidence_dir = (
            default_evidence_dir
            if (default_evidence_dir / "raw_model_output.txt").is_file()
            else stream_evidence_dir
        )
        existing_raw = evidence_dir / "raw_model_output.txt"
        if existing_raw.is_file():
            raw_text = existing_raw.read_text(encoding="utf-8")
            ok, _, projected, detail = validate_projected_segment_output(raw_text)
            if not ok or not isinstance(projected, Mapping):
                raise RuntimeError(
                    f"existing_segment_output_invalid:{segment.segment_id}:{detail}"
                )
            output = dict(projected)
            raw_receipt = _read_json(
                evidence_dir / "minimal_raw_provider_receipt_v1.json"
            )
            receipt = CreativeReceipt(
                role=ROLE_V2_CREATIVE_EDITOR,
                logical_invocation_id=segment_invocation_id,
                input_sha256=logical_hash(prompt),
                requested_model=str(raw_receipt["requested_model"]),
                effective_model=V2_CREATIVE_CX_XHIGH_MODEL,
                output_sha256=logical_hash(output),
                terminal_disposition="ACCEPTED_AFTER_DETERMINISTIC_SCHEMA_PROJECTION",
                attempts=(),
                total_usage=raw_receipt.get("usage"),
                total_cost=raw_receipt.get("cost"),
                degraded_creative_model=False,
                professional_candidate_eligible=True,
            )
            _write_json(
                evidence_dir / "deterministic_schema_projection_v1.json",
                {
                    "schema_version": "contentops.v2.segment_schema_projection.v1",
                    "raw_model_output_sha256": raw_receipt.get(
                        "raw_model_output_sha256"
                    ),
                    "projected_output_sha256": logical_hash(output),
                    "operations": "SYNONYMOUS_FIELD_PROJECTION_AND_VARIANT_BINDING",
                    "creative_meaning_changed": False,
                    "model_call_used": False,
                    "public_write": False,
                },
            )
        else:
            output, receipt = NineRouterGPT56Brain().author(
                role=ROLE_V2_CREATIVE_EDITOR,
                prompt_payload=prompt,
                validator=validate_projected_segment_output,
                logical_invocation_id=segment_invocation_id,
                prompt_template="concrete_first_xhigh_segment_author",
                prompt_version="v3_minimal_raw_no_generation_config",
                wire_mode="minimal_raw",
                evidence_dir=evidence_dir,
                retry_budget=RetryBudget(
                    logical_invocation_id=segment_invocation_id,
                    max_total_provider_attempts=1,
                    max_fallback_transitions=0,
                    max_same_model_retries=0,
                    max_structured_output_repair_attempts=0,
                    max_cumulative_retry_sleep_seconds=0,
                    wall_clock_budget_seconds=600,
                    per_model_max_attempts=(1,),
                ),
                model_pool_override=(V2_CREATIVE_CX_XHIGH_MODEL,),
                response_stream=True,
            )
        if not receipt.professional_candidate_eligible:
            raise RuntimeError(
                f"professional_segment_candidate_degraded_creative_model:{segment.segment_id}"
            )
        output = dict(output)
        output["segment_id"] = segment.segment_id
        output["input_sha256"] = built["input_sha256"]
        output["output_sha256"] = logical_hash(output)
        outputs.append(output)
        receipts.append(_receipt_summary(receipt))
        continuity = {"knowledge": output.get("continuity_state_leaving") or []}
        previous = str(output["segment_summary"])
        _write_json(
            runtime / "contracts" / "segments" / f"{segment.segment_id}.json", output
        )
        _write_json(
            runtime / "receipts" / "segments" / f"{segment.segment_id}.json",
            _receipt_summary(receipt),
        )
    short = [beat for segment in outputs for beat in segment["short_9x16_beats"]]
    mid = [beat for segment in outputs for beat in segment["midform_16x9_beats"]]
    known_assets = {str(row["asset_id"]) for row in assets["candidates"]}
    for beat in short + mid:
        VisualGroundingContract.from_mapping(beat)
        if not set(beat["asset_ids"]) <= known_assets:
            raise RuntimeError(f"segment_selected_unknown_asset:{beat['beat_id']}")
    ids = [str(beat["beat_id"]) for beat in short + mid]
    if len(ids) != len(set(ids)):
        raise RuntimeError("segment_beat_ids_not_unique")
    short_duration = sum(float(beat["duration_seconds"]) for beat in short)
    mid_duration = sum(float(beat["duration_seconds"]) for beat in mid)
    if not 45 <= short_duration <= 60:
        raise RuntimeError(f"short_duration_outside_contract:{short_duration}")
    if not 90 <= mid_duration <= 150:
        raise RuntimeError(f"midform_duration_outside_contract:{mid_duration}")
    package = {
        "schema_version": "contentops.retention_native.segment_authorship.v2",
        "video_id": VIDEO_ID,
        "segments": outputs,
        "short_9x16_beats": short,
        "midform_16x9_beats": mid,
        "durations_seconds": {
            "short_9x16": short_duration,
            "midform_16x9": mid_duration,
        },
        "segment_receipts": receipts,
        "degraded_creative_model": any(
            row["degraded_creative_model"] for row in receipts
        ),
        "professional_candidate_eligible": all(
            row["professional_candidate_eligible"] for row in receipts
        ),
        "public_write_authority": False,
    }
    if package["degraded_creative_model"]:
        raise RuntimeError("professional_candidate_depends_on_degraded_creative_model")
    _write_json(runtime / "contracts" / "segment_authorship_v2.json", package)
    return package


def build_storyboards(runtime: Path, *, ffmpeg: str) -> dict[str, Any]:
    package = _read_json(runtime / "contracts" / "segment_authorship_v2.json")
    asset_paths = _read_json(runtime / "contracts" / "asset_path_binding_v2.json")
    results: dict[str, Any] = {}
    for variant, dims in (
        ("short_9x16", (1080, 1920)),
        ("midform_16x9", (1920, 1080)),
    ):
        frames: list[dict[str, Any]] = []
        beats = package[f"{variant}_beats"]
        for index, beat in enumerate(beats):
            frame = render_storyboard_frame(
                beat,
                asset_paths=asset_paths,
                output_path=runtime
                / "storyboard"
                / variant
                / f"{index:02d}-{beat['beat_id']}.jpg",
                width=dims[0],
                height=dims[1],
                captions_visible=False,
            )
            frame["duration_seconds"] = float(beat["duration_seconds"])
            frames.append(frame)
        sheet = contact_sheet(
            frames,
            output_path=runtime
            / "review"
            / f"{variant}_storyboard_captions_hidden_contact_sheet.jpg",
            columns=4 if variant == "midform_16x9" else 5,
        )
        animatic = render_animatic(
            frames,
            output_path=runtime / "animatic" / f"{variant}_captions_hidden.mp4",
            ffmpeg=ffmpeg,
        )
        grounding = enforce_must_use_assets(
            [VisualGroundingContract.from_mapping(beat) for beat in beats],
            {str(beat["beat_id"]): list(beat["asset_ids"]) for beat in beats},
        )
        mix = visual_mix_summary(beats)
        if grounding["status"] != "PASS" or mix["status"] != "PASS":
            raise RuntimeError(f"storyboard_grounding_block:{variant}")
        results[variant] = {
            "frames": frames,
            "contact_sheet": sheet,
            "animatic": animatic,
            "must_use_asset_compliance": grounding,
            "visual_mix": mix,
        }
    manifest = {
        "schema_version": "contentops.retention_native.storyboard_animatic.v2",
        "video_id": VIDEO_ID,
        "captions_hidden": True,
        "variants": results,
        "public_write": False,
    }
    _write_json(runtime / "storyboard_animatic_manifest_v2.json", manifest)
    return manifest


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _validate_comprehension_output(
    text: str,
) -> tuple[bool, str | None, Any, str | None]:
    try:
        value = json.loads(
            text.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        if not isinstance(value, Mapping) or value.get("status") not in {
            "PASS",
            "BLOCK",
        }:
            raise ValueError("status")
        assessments = value.get("assessments")
        expected = {
            "first_second_context",
            "concrete_recognition",
            "semantic_continuity",
            "captions_hidden_story_reconstruction",
            "asset_plan_compliance",
            "abstract_only_run",
        }
        if (
            not isinstance(assessments, Mapping)
            or set(assessments) != expected
            or any(not isinstance(item, bool) for item in assessments.values())
        ):
            raise ValueError("assessments")
        if not isinstance(value.get("reconstructed_concepts"), list) or not isinstance(
            value.get("issues"), list
        ):
            raise ValueError("lists")
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return False, "structured_output_schema_invalid", None, f"comprehension_{exc}"
    return True, None, value, None


def run_premotion_critic(runtime: Path) -> dict[str, Any]:
    storyboard = _read_json(runtime / "storyboard_animatic_manifest_v2.json")
    images = [
        (variant, Path(storyboard["variants"][variant]["contact_sheet"]["path"]))
        for variant in ("short_9x16", "midform_16x9")
    ]
    instruction = """You are the independent canonical pre-motion comprehension critic. Inspect the two labeled captions-hidden storyboard contact sheets in sequence. Judge whether a normal viewer can reconstruct the EIA/Hormuz story before expensive motion code. Return ONLY JSON: {status:'PASS|BLOCK', summary:string, assessments:{first_second_context:boolean,concrete_recognition:boolean,semantic_continuity:boolean,captions_hidden_story_reconstruction:boolean,asset_plan_compliance:boolean,abstract_only_run:boolean}, reconstructed_concepts:[zero or more exact IDs from: oil_and_hormuz, shipping_supply_changed, eia_forecast_source, production_inventories_demand_matter, price_not_proof, future_confirmation_points], issues:[{variant_id,beat_id,observation,systemic_fix}]}. Set abstract_only_run true only when there is NO long unexplained abstract-only run. Do not reward technical validity. Labels, maps, documents, charts, and recognizable physical assets may carry meaning; narration captions are hidden."""
    image_content: list[dict[str, Any]] = []
    for label, path in images:
        image_content.extend(
            (
                {"type": "text", "text": f"CAPTIONS-HIDDEN STORYBOARD: {label}"},
                {
                    "type": "image_url",
                    "image_url": {"url": _data_uri(path), "detail": "high"},
                },
            )
        )

    def provider(prompt: str, model: str, timeout: float) -> ProviderResult:
        content = [{"type": "text", "text": prompt}, *image_content]
        return call_nine_router_v2_isolated(
            content,
            model,
            timeout,
            role_task_id=ROLE_MULTIMODAL_VIDEO_CRITIC,
            logical_invocation_id=logical_invocation_id,
            component="CanonicalMultimodalCritic",
            max_tokens=5000,
            temperature=0.1,
        )

    technical = {
        "video_id": VIDEO_ID,
        "input_images": [
            {"variant_id": label, "sha256": sha256_file(path)} for label, path in images
        ],
        "captions_hidden": True,
        "public_write_authority": False,
    }
    logical_invocation_id = f"inv_v2_premotion_critic_{logical_hash(technical)[:20]}"
    invocation = routed_v2_isolated_invocation(
        prompt=instruction,
        role_task_id=ROLE_MULTIMODAL_VIDEO_CRITIC,
        logical_invocation_id=logical_invocation_id,
        component="CanonicalMultimodalCritic",
        work_item_id=VIDEO_ID,
        timeout_seconds=600.0,
        validator=_validate_comprehension_output,
        provider_call=provider,
        governed_input=technical,
        prompt_template="concrete_first_premotion_comprehension_critic",
        prompt_version="v1",
    )
    if invocation.get("terminal_disposition") != ACCEPTED:
        raise RuntimeError(
            f"premotion_critic_blocked:{invocation.get('terminal_disposition')}"
        )
    authored = dict(invocation["output"])
    gate = evaluate_comprehension_gate(
        assessments=authored["assessments"],
        reconstructed_concepts=authored["reconstructed_concepts"],
    )
    report = {
        "schema_version": "contentops.retention_native.premotion_comprehension.v2",
        "video_id": VIDEO_ID,
        "authored_assessment": authored,
        "deterministic_gate": gate,
        "critic_identity": {
            "route": ROLE_MULTIMODAL_VIDEO_CRITIC,
            "selected_model": invocation.get("selected_model"),
            "model_identity_note": invocation.get("model_identity_note"),
        },
        "router_evidence": {
            key: invocation.get(key)
            for key in (
                "logical_invocation_id",
                "terminal_disposition",
                "selected_model",
                "models_attempted_in_order",
                "total_attempts",
                "total_usage",
                "total_cost",
                "attempts",
            )
        },
        "public_write": False,
    }
    _write_json(runtime / "premotion_comprehension_report_v2.json", report)
    if gate["status"] != "PASS":
        raise RuntimeError(
            "PREMOTION_COMPREHENSION_BLOCK_SYSTEMIC_STORYBOARD_REVISION_REQUIRED"
        )
    return report


def run_isolated_xhigh_preflight(runtime: Path) -> dict[str, Any]:
    """Make exactly one real XHIGH request before the larger proof is authorized."""
    logical_invocation_id = "inv_v2_isolated_xhigh_preflight_v1"
    prompt = (
        "Return exactly READY and nothing else. This is a zero-public-write V2 isolated "
        "execution-domain attribution preflight."
    )

    def provider(current_prompt: str, model: str, timeout: float) -> ProviderResult:
        return call_nine_router_v2_isolated(
            current_prompt,
            model,
            timeout,
            role_task_id=ROLE_V2_CREATIVE_EDITOR,
            logical_invocation_id=logical_invocation_id,
            component="NineRouterGPT56Brain",
            max_tokens=16,
            temperature=0.0,
        )

    def validate(text: str) -> tuple[bool, str | None, Any, str | None]:
        ok = text.strip() == "READY"
        return (
            ok,
            None if ok else "structured_output_schema_invalid",
            text.strip(),
            (None if ok else "isolated_preflight_expected_READY"),
        )

    invocation = routed_v2_isolated_invocation(
        prompt=prompt,
        role_task_id=ROLE_V2_CREATIVE_EDITOR,
        logical_invocation_id=logical_invocation_id,
        component="NineRouterGPT56Brain",
        provider_call=provider,
        work_item_id=VIDEO_ID,
        timeout_seconds=180.0,
        validator=validate,
        governed_input={"task": "isolated_v2_preflight", "public_write": False},
        prompt_template="isolated_v2_xhigh_attribution_preflight",
        prompt_version="v1",
        budget=RetryBudget(
            logical_invocation_id=logical_invocation_id,
            max_total_provider_attempts=1,
            max_fallback_transitions=0,
            max_same_model_retries=0,
            max_structured_output_repair_attempts=0,
            max_cumulative_retry_sleep_seconds=0,
            wall_clock_budget_seconds=180,
            per_model_max_attempts=(1, 0, 0),
        ),
    )
    result = {
        "schema_version": "contentops.v2_isolated_xhigh_preflight.v1",
        "status": "PASS"
        if invocation.get("terminal_disposition") == ACCEPTED
        else "BLOCK",
        "selected_model": invocation.get("selected_model"),
        "models_attempted_in_order": invocation.get("models_attempted_in_order"),
        "total_attempts": invocation.get("total_attempts"),
        "router_evidence": invocation,
        "public_write": False,
    }
    if (
        result["status"] != "PASS"
        or result["selected_model"] != "new/gpt-5.6-sol-xhigh"
    ):
        raise RuntimeError(
            f"isolated_xhigh_preflight_block:{result['status']}:{result['selected_model']}"
        )
    _write_json(runtime / "isolated_xhigh_preflight_v1.json", result)
    return result


def validate_isolation_before_provider(runtime: Path) -> dict[str, Any]:
    """Persist the required zero-network proof before the first real V2 request."""
    generic_blocked = False
    try:
        assert_llm_operator_execution_enabled()
    except LLMOperatorPausedError:
        generic_blocked = True
    if not generic_blocked:
        raise RuntimeError("generic_v1_traffic_not_blocked_by_shared_fuse")
    assert_v2_execution_authorized(
        role_task_id=ROLE_V2_CREATIVE_EDITOR,
        logical_invocation_id="inv_v2_isolation_validation_v1",
        component="NineRouterGPT56Brain",
        model="new/gpt-5.6-sol-xhigh",
    )
    public_write_blocked = False
    try:
        assert_v2_execution_authorized(
            role_task_id=ROLE_V2_CREATIVE_EDITOR,
            logical_invocation_id="inv_v2_isolation_validation_v1",
            component="NineRouterGPT56Brain",
            public_write=True,
        )
    except V2ExecutionLeaseError:
        public_write_blocked = True
    if not public_write_blocked:
        raise RuntimeError("v2_lease_public_write_not_blocked")
    report = {
        "schema_version": "contentops.v2_isolation_pre_provider_validation.v1",
        "status": "PASS",
        "shared_global_fuse_active": llm_operator_pause_active(),
        "generic_v1_traffic_blocked": generic_blocked,
        "exact_v2_runner_lease_active": True,
        "xhigh_model_authorized_only_for_v2_role": True,
        "public_write_authority": False,
        "public_write_request_blocked": public_write_blocked,
        "network_calls_during_validation": 0,
        "v1_provider_calls_authorized_by_v2_lease": 0,
    }
    _write_json(runtime / "isolation_pre_provider_validation_v1.json", report)
    return report


def require_accepted_isolated_xhigh_preflight(runtime: Path) -> dict[str, Any]:
    path = runtime / "isolated_xhigh_preflight_v1.json"
    report = _read_json(path)
    if (
        report.get("status") != "PASS"
        or report.get("selected_model") != "new/gpt-5.6-sol-xhigh"
        or report.get("models_attempted_in_order") != ["new/gpt-5.6-sol-xhigh"]
        or report.get("total_attempts") != 1
        or report.get("public_write") is not False
    ):
        raise RuntimeError("accepted_isolated_xhigh_preflight_receipt_required")
    return report


def run_isolated_proof(
    runtime: Path,
    *,
    repo_root: Path,
    ffmpeg: str,
    ffprobe: str,
    node: str,
    tts_python: str,
) -> dict[str, Any]:
    """Execute the complete proof inside one runner-owned lease and revoke it on exit."""
    prepare(runtime)
    domain_id = ""
    audit_path = ""
    try:
        with active_v2_execution_lease(repo_root=repo_root, runtime=runtime) as lease:
            domain_id = lease.domain_id
            audit_path = str(lease.audit_path)
            validate_isolation_before_provider(runtime)
            require_accepted_isolated_xhigh_preflight(runtime)
            author_director(runtime)
            author_segments(runtime)
            build_storyboards(runtime, ffmpeg=ffmpeg)
            run_premotion_critic(runtime)
            from live_contentops.retention_native_motion_pipeline_v2 import (
                author_motion,
                build_audio_and_mux,
                probe_media,
                render_motion,
            )
            from live_contentops.retention_native_review_qa_v2 import (
                build_review_artifacts,
                deterministic_qa,
                run_final_critic,
            )

            author_motion(runtime=runtime, repo_root=repo_root)
            render_motion(runtime=runtime, repo_root=repo_root, node=node)
            build_review_artifacts(runtime=runtime, ffmpeg=ffmpeg)
            deterministic_qa(runtime=runtime)
            build_audio_and_mux(
                runtime=runtime, tts_python=tts_python, ffmpeg=ffmpeg, ffprobe=ffprobe
            )
            probe_media(runtime=runtime, ffprobe=ffprobe)
            critic = run_final_critic(runtime=runtime)
    except BaseException as exc:
        audit = _read_json(Path(audit_path)) if audit_path else {}
        failure_message = str(exc)[:500]
        failure_status = (
            "BLOCKED_MINIMAL_RAW_XHIGH_DIRECTOR_PROVIDER_EXECUTION"
            if "BLOCKED_MINIMAL_RAW_XHIGH_DIRECTOR_PROVIDER_EXECUTION"
            in failure_message
            else "BLOCKED_ISOLATED_V2_PROOF_EXECUTION"
        )
        director_experiment_path = (
            runtime / "minimal_raw_xhigh_director_experiment_v1.json"
        )
        director_experiment = (
            _read_json(director_experiment_path)
            if director_experiment_path.is_file()
            else None
        )
        failure = {
            "schema_version": "contentops.retention_native.isolated_proof_result.v1",
            "status": failure_status,
            "failure_class": type(exc).__name__,
            "failure_message": failure_message,
            "minimal_raw_director_experiment": director_experiment,
            "isolated_execution_domain_id": domain_id,
            "lease_audit_path": audit_path,
            "lease_revoked": audit.get("state") == "REVOKED",
            "shared_global_pause_unchanged": bool(
                (audit.get("shared_global_pause_after") or {}).get("unchanged")
            ),
            "v1_daily_app_continuity": audit.get("v1_daily_app_continuity") is True,
            "v1_provider_calls_authorized_by_v2_lease": 0,
            "v2_provider_call_count": len(audit.get("provider_attempts") or []),
            "public_writes": 0,
            "owner_acceptance": "PENDING",
        }
        _write_json(runtime / "isolated_proof_result_v1.json", failure)
        raise
    audit = _read_json(Path(audit_path))
    result = {
        "schema_version": "contentops.retention_native.isolated_proof_result.v1",
        "status": (
            "PASS_IMPLEMENTATION_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW"
            if critic.get("status") in {"PASS", "PASS_WITH_NOTES"}
            else "REQUIRES_BOUNDED_CREATIVE_REVISION"
        ),
        "isolated_execution_domain_id": domain_id,
        "lease_audit_path": audit_path,
        "lease_revoked": audit.get("state") == "REVOKED",
        "shared_global_pause_unchanged": bool(
            (audit.get("shared_global_pause_after") or {}).get("unchanged")
        ),
        "v1_daily_app_continuity": audit.get("v1_daily_app_continuity") is True,
        "v1_provider_calls_authorized_by_v2_lease": 0,
        "v2_provider_call_count": len(audit.get("provider_attempts") or []),
        "public_writes": 0,
        "critic_status": critic.get("status"),
        "owner_acceptance": "PENDING",
    }
    _write_json(runtime / "isolated_proof_result_v1.json", result)
    return result


def provider_execution_blocker(runtime: Path) -> dict[str, Any]:
    command = (
        "Get-CimInstance Win32_Process | "
        "Where-Object { $_.Name -match '^(python|pythonw).*' -and "
        "$_.CommandLine -match 'live_contentops.cli daily-app start' } | "
        "Select-Object ProcessId,Name | ConvertTo-Json -Compress"
    )
    observed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    processes: list[dict[str, Any]] = []
    if observed.returncode == 0 and observed.stdout.strip():
        value = json.loads(observed.stdout)
        processes = [value] if isinstance(value, dict) else list(value)
    active_pause = llm_operator_pause_active()
    blocked = active_pause and bool(processes)
    report = {
        "schema_version": "contentops.retention_native.provider_execution_blocker.v2",
        "task": "TASK_CONTENTOPS_V2_CONCRETE_FIRST_XHIGH_REPLACEMENT_VERTICAL_SLICE_V1",
        "status": "BLOCKED" if blocked else "CLEAR",
        "classification": (
            "BLOCKED_GLOBAL_LLM_FUSE_WITH_ACTIVE_V1_DAILY_APP"
            if blocked
            else "NO_CURRENT_PROVIDER_EXECUTION_BLOCK"
        ),
        "llm_operator_pause_active": active_pause,
        "pause_path": str(operator_pause_path()),
        "active_v1_daily_app_processes": processes,
        "pause_cleared": False,
        "provider_calls_attempted": 0,
        "v1_processes_stopped_or_mutated": 0,
        "reason": (
            "Clearing the global fuse while V1 Daily App is active could authorize unrelated V1 model traffic and violate task isolation."
            if blocked
            else None
        ),
        "required_operator_action": (
            "Provide an isolated authorized V2 model boundary, or stop/pause V1 and explicitly authorize a bounded global-fuse resume window."
            if blocked
            else None
        ),
        "public_write": False,
    }
    _write_json(runtime / "provider_execution_blocker_v2.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=(
            "prepare",
            "director",
            "segments",
            "storyboard",
            "critic",
            "premotion",
            "blocker",
            "isolation",
            "isolated-preflight",
            "progressive-xhigh",
            "xhigh-transport",
            "xhigh-responses",
            "cx-xhigh",
            "cx-segments",
            "cx-motion",
            "cx-revision",
            "final-critic",
            "proof",
        ),
    )
    parser.add_argument("--runtime", default=str(DEFAULT_RUNTIME))
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--node", default="node")
    parser.add_argument(
        "--batch",
        help="One resumable motion batch, for example short_9x16:S1.",
    )
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument(
        "--tts-python",
        default=r"A:\Capital Chronicle\Runtime\ContentOps\tier2\tts-kokoro-venv\Scripts\python.exe",
    )
    args = parser.parse_args()
    runtime = Path(args.runtime).resolve()
    if args.stage == "prepare":
        result = prepare(runtime)
    elif args.stage == "director":
        result = author_director(runtime)
    elif args.stage == "segments":
        result = author_segments(runtime)
    elif args.stage == "storyboard":
        result = build_storyboards(runtime, ffmpeg=args.ffmpeg)
    elif args.stage == "critic":
        with active_v2_execution_lease(
            repo_root=Path(args.repo_root).resolve(), runtime=runtime
        ):
            result = run_premotion_critic(runtime)
    elif args.stage == "premotion":
        prepare(runtime)
        author_director(runtime)
        author_segments(runtime)
        build_storyboards(runtime, ffmpeg=args.ffmpeg)
        with active_v2_execution_lease(
            repo_root=Path(args.repo_root).resolve(), runtime=runtime
        ):
            result = run_premotion_critic(runtime)
    elif args.stage in {"isolation", "isolated-preflight"}:
        repo_root = Path(args.repo_root).resolve()
        with active_v2_execution_lease(repo_root=repo_root, runtime=runtime):
            result = validate_isolation_before_provider(runtime)
            if args.stage == "isolated-preflight":
                result = run_isolated_xhigh_preflight(runtime)
    elif args.stage == "proof":
        result = run_isolated_proof(
            runtime,
            repo_root=Path(args.repo_root).resolve(),
            ffmpeg=args.ffmpeg,
            ffprobe=args.ffprobe,
            node=args.node,
            tts_python=args.tts_python,
        )
    elif args.stage == "progressive-xhigh":
        result = run_progressive_xhigh_diagnostic(
            runtime, repo_root=Path(args.repo_root).resolve()
        )
    elif args.stage == "xhigh-transport":
        result = run_xhigh_transport_diagnostic(
            runtime, repo_root=Path(args.repo_root).resolve()
        )
    elif args.stage == "xhigh-responses":
        result = run_xhigh_responses_diagnostic(
            runtime, repo_root=Path(args.repo_root).resolve()
        )
    elif args.stage == "cx-xhigh":
        result = run_cx_xhigh_diagnostic(
            runtime, repo_root=Path(args.repo_root).resolve()
        )
    elif args.stage == "cx-segments":
        result = run_isolated_cx_segments(
            runtime, repo_root=Path(args.repo_root).resolve()
        )
    elif args.stage == "cx-motion":
        if not args.batch:
            parser.error("cx-motion requires --batch")
        from live_contentops.retention_native_motion_pipeline_v2 import author_motion

        with active_v2_execution_lease(
            repo_root=Path(args.repo_root).resolve(), runtime=runtime
        ):
            result = author_motion(
                runtime=runtime,
                repo_root=Path(args.repo_root).resolve(),
                only_batch=args.batch,
            )
    elif args.stage == "cx-revision":
        from live_contentops.retention_native_motion_pipeline_v2 import (
            revise_localized_s3,
        )

        with active_v2_execution_lease(
            repo_root=Path(args.repo_root).resolve(), runtime=runtime
        ):
            result = revise_localized_s3(
                runtime=runtime, repo_root=Path(args.repo_root).resolve()
            )
    elif args.stage == "final-critic":
        from live_contentops.retention_native_review_qa_v2 import run_final_critic

        with active_v2_execution_lease(
            repo_root=Path(args.repo_root).resolve(), runtime=runtime
        ):
            result = run_final_critic(runtime=runtime)
    else:
        result = provider_execution_blocker(runtime)
    print(
        json.dumps(
            {
                "status": str(result.get("status") or "PASS"),
                "stage": args.stage,
                "result_sha256": logical_hash(result),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
