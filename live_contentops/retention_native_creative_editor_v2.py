"""Bounded GPT-5.6 Creative Editor diagnostic and authorship boundary.

This module owns no factual, publication, browser, or platform authority.  It binds a
creative request to an already-governed article packet and routes it through the canonical
9Router seam under the exact V2 Creative Editor role.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from live_contentops.llm_cost_governor_v1 import llm_cycle_budget_scope
from live_contentops.nine_router_llm_seam_v2 import (
    ROLE_V2_CREATIVE_EDITOR,
    routed_llm_invocation,
)
from live_contentops.nine_router_ordered_model_router_v2 import RetryBudget


SCHEMA_VERSION = "contentops.retention_native.creative_editor_diagnostic.v2"
BLUEPRINT_SCHEMA_VERSION = "contentops.retention_native.creative_blueprint.v2"
LEGACY_SHORT_BEATS = tuple(f"short_{index:02d}" for index in range(1, 19))
LEGACY_MIDFORM_BEATS = tuple(f"midform_{index:02d}" for index in range(1, 38))
REQUIRED_BEAT_KEYS = frozenset(
    {
        "beat_id",
        "start_seconds",
        "end_seconds",
        "narration",
        "claim_ids",
        "evidence_ids",
        "asset_ids",
        "visual_concept",
        "motion_concept",
        "on_screen_text",
        "transition_in",
        "transition_out",
        "sound_design",
        "retention_purpose",
    }
)
REQUIRED_HYPOTHESIS_KEYS = frozenset(
    {
        "shot_id",
        "duration_seconds",
        "visual_concept",
        "motion_concept",
        "typography_action",
        "asset_ids",
        "claim_ids",
        "evidence_ids",
        "transition",
        "sound_design",
    }
)


def _logical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_governed_story_packet(repo_root: Path) -> dict[str, Any]:
    packet_root = repo_root / (
        "docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/"
        "contentops_v1_0_rc_20260711_1"
    )
    article = json.loads(
        (packet_root / "article_manifest_v1.json").read_text(encoding="utf-8")
    )
    support = json.loads(
        (packet_root / "grounded_support_v1.json").read_text(encoding="utf-8")
    )
    run_context = json.loads(
        (packet_root / "run_context_v1.json").read_text(encoding="utf-8")
    )
    official = support["official_source_packet"]
    media = run_context["media"]
    facts = official["facts"]
    claims = [
        {"claim_id": f"eia:{key}", "value": value, "evidence_id": "eia-release-press590"}
        for key, value in sorted(facts.items())
    ]
    evidence = [
        {
            "evidence_id": "eia-release-press590",
            "title": official["source_title"],
            "url": official["source_url"],
            "sha256": official["source_text_sha256"],
        },
        {
            "evidence_id": "governed-article",
            "title": article["title"],
            "url": article["canonical_url"],
            "sha256": article["article_markdown_sha256"],
        },
    ]
    return {
        "story_id": article["slug"],
        "story_version": article["created_at"],
        "title": article["title"],
        "subtitle": article["subtitle"],
        "article_body": article["rendered_body"],
        "article_sha256": article["article_markdown_sha256"],
        "canonical_url": article["canonical_url"],
        "market_mechanism": article["market_mechanism"],
        "policy_context": article["policy_context"],
        "cross_asset_implications": article["cross_asset_implications"],
        "named_catalysts": article["named_catalyst_terms"],
        "official_source": {
            "title": official["source_title"],
            "url": official["source_url"],
            "sha256": official["source_text_sha256"],
            "facts": official["facts"],
            "supporting_sources": official["supporting_source_retrievals"],
        },
        "claims": claims,
        "evidence": evidence,
        "assets": [
            {
                "asset_id": row["asset_id"],
                "path": row["path"],
                "sha256": row["sha256"],
                "media_class": row["media_class"],
                "caption": row["caption"],
                "source_page_url": row["source_page_url"],
            }
            for row in media["assets"]
        ],
        "authority": {
            "factual_authority": "governed_input_only",
            "generated_illustration_is_documentary_evidence": False,
            "public_write": False,
            "publication_authority": False,
        },
    }


def build_compact_hierarchical_prompt(governed: Mapping[str, Any]) -> str:
    """Request one coherent whole-story blueprint without a 55-row expanded schema."""
    shape = {
        "schema_version": BLUEPRINT_SCHEMA_VERSION,
        "story_id": governed["story_id"],
        "creative_thesis": "string",
        "shared_visual_language": {
            "editorial_metaphor": "string",
            "typography": "string",
            "color_system": "string",
            "texture_system": "string",
            "transition_grammar": "string",
        },
        "variants": {
            "short_9x16": {
                "duration_seconds": "number 45..75",
                "hook": "string",
                "payoff_seconds": "number <=12",
                "narration_script": "complete string",
                "sequences": [
                    {
                        "sequence_id": "short_seq_N",
                        "start_seconds": "number",
                        "end_seconds": "number",
                        "editorial_purpose": "string",
                        "narration_excerpt": "string",
                        "visual_hypotheses": [
                            {key: "required" for key in sorted(REQUIRED_HYPOTHESIS_KEYS)}
                        ],
                    }
                ],
            },
            "midform_16x9": {
                "duration_seconds": "number 180..360",
                "hook": "string",
                "payoff_seconds": "number 30..60",
                "narration_script": "complete string",
                "sequences": [
                    {
                        "sequence_id": "midform_seq_N",
                        "start_seconds": "number",
                        "end_seconds": "number",
                        "editorial_purpose": "string",
                        "narration_excerpt": "string",
                        "visual_hypotheses": [
                            {key: "required" for key in sorted(REQUIRED_HYPOTHESIS_KEYS)}
                        ],
                    }
                ],
            },
        },
        "music_direction": "string",
        "sfx_palette": ["string"],
        "rights_and_truth_notes": ["string"],
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    }
    instructions = {
        "role": "Capital Chronicle V2 Creative Editor",
        "task": (
            "Author one coherent, premium, asset-rich editorial film system for a short "
            "vertical cut and a deeper midform cut. Own the hook, narration, screenplay, "
            "visual rhythm, shot hypotheses, typography, transitions, music, and SFX."
        ),
        "design_direction": [
            "Avoid generic template motion, repetitive cards, and numeric-list narration.",
            "Use a distinctive editorial metaphor that evolves across the story.",
            "Treat charts as designed scenes: crop, trace, mask, compare, and transition them.",
            "Use scene-specific code-capable motion ideas, not stock-footage directions.",
            "Make the vertical cut fast and legible; make midform breathe without static holds.",
            "Use as many visual hypotheses as the story needs; do not pad to a quota.",
        ],
        "truth_and_safety": [
            "Every factual statement must bind to supplied claim_ids and evidence_ids.",
            "Only use supplied asset_ids for documentary/source-backed visual claims.",
            "Generated illustration may be proposed only as non-documentary editorial metaphor.",
            "Never invent a quote, number, event, forecast, source, or real-person image.",
            "No browser, platform, upload, publication, or public-write authority exists.",
        ],
        "output": [
            "Return exactly one JSON object and no Markdown.",
            "Populate the compact hierarchical shape; do not repeat global fields per shot.",
            "Sequence times must be ordered, contiguous, and end at variant duration.",
            "Use unique sequence and shot IDs within each variant.",
        ],
        "required_shape": shape,
    }
    return (
        "CREATIVE_EDITOR_REQUEST\n"
        + json.dumps(instructions, ensure_ascii=False, sort_keys=True)
        + "\nGOVERNED_STORY_PACKET\n"
        + json.dumps(governed, ensure_ascii=False, sort_keys=True)
    )


def validate_compact_blueprint(
    text: str,
) -> tuple[bool, str | None, Any, str | None]:
    parsed, diagnostic = _parse_single_json_object(text)
    if parsed is None:
        return False, "structured_output_malformed", None, diagnostic
    required_top = {
        "schema_version",
        "story_id",
        "creative_thesis",
        "shared_visual_language",
        "variants",
        "music_direction",
        "sfx_palette",
        "rights_and_truth_notes",
        "public_write",
        "publication_authority",
        "factual_authority",
    }
    if not required_top.issubset(parsed):
        return False, "structured_output_schema_invalid", None, "schema_missing_top_level"
    if parsed.get("schema_version") != BLUEPRINT_SCHEMA_VERSION:
        return False, "structured_output_schema_invalid", None, "schema_version_invalid"
    if any(
        parsed.get(key) is not False
        for key in ("public_write", "publication_authority", "factual_authority")
    ):
        return False, "structured_output_schema_invalid", None, "authority_boundary_invalid"
    variants = parsed.get("variants")
    if not isinstance(variants, dict) or set(variants) != {"short_9x16", "midform_16x9"}:
        return False, "structured_output_schema_invalid", None, "variant_set_invalid"
    all_asset_ids: set[str] = set()
    all_claim_ids: set[str] = set()
    all_evidence_ids: set[str] = set()
    for variant_id, duration_bounds, payoff_bounds in (
        ("short_9x16", (45.0, 75.0), (0.0, 12.0)),
        ("midform_16x9", (180.0, 360.0), (30.0, 60.0)),
    ):
        variant = variants.get(variant_id)
        if not isinstance(variant, dict):
            return False, "structured_output_schema_invalid", None, "variant_shape_invalid"
        try:
            duration = float(variant["duration_seconds"])
            payoff = float(variant["payoff_seconds"])
        except (KeyError, TypeError, ValueError):
            return False, "structured_output_schema_invalid", None, "duration_or_payoff_invalid"
        if not duration_bounds[0] <= duration <= duration_bounds[1]:
            return False, "structured_output_schema_invalid", None, "duration_or_payoff_invalid"
        if not payoff_bounds[0] <= payoff <= payoff_bounds[1]:
            return False, "structured_output_schema_invalid", None, "duration_or_payoff_invalid"
        if not isinstance(variant.get("narration_script"), str) or not variant["narration_script"].strip():
            return False, "structured_output_schema_invalid", None, "narration_missing"
        sequences = variant.get("sequences")
        if not isinstance(sequences, list) or len(sequences) < 3:
            return False, "structured_output_schema_invalid", None, "sequence_shape_invalid"
        prior_end = 0.0
        seen_sequence_ids: set[str] = set()
        seen_shot_ids: set[str] = set()
        for sequence in sequences:
            if not isinstance(sequence, dict):
                return False, "structured_output_schema_invalid", None, "sequence_shape_invalid"
            try:
                sequence_id = str(sequence["sequence_id"])
                start = float(sequence["start_seconds"])
                end = float(sequence["end_seconds"])
            except (KeyError, TypeError, ValueError):
                return False, "structured_output_schema_invalid", None, "sequence_timing_invalid"
            if sequence_id in seen_sequence_ids or abs(start - prior_end) > 0.25 or end <= start:
                return False, "structured_output_schema_invalid", None, "sequence_timing_invalid"
            seen_sequence_ids.add(sequence_id)
            prior_end = end
            hypotheses = sequence.get("visual_hypotheses")
            if not isinstance(hypotheses, list) or not hypotheses:
                return False, "structured_output_schema_invalid", None, "hypothesis_shape_invalid"
            for hypothesis in hypotheses:
                if not isinstance(hypothesis, dict) or not REQUIRED_HYPOTHESIS_KEYS.issubset(hypothesis):
                    return False, "structured_output_schema_invalid", None, "hypothesis_shape_invalid"
                shot_id = str(hypothesis["shot_id"])
                if shot_id in seen_shot_ids:
                    return False, "structured_output_schema_invalid", None, "shot_id_duplicate"
                seen_shot_ids.add(shot_id)
                for key, aggregate in (
                    ("asset_ids", all_asset_ids),
                    ("claim_ids", all_claim_ids),
                    ("evidence_ids", all_evidence_ids),
                ):
                    values = hypothesis.get(key)
                    if not isinstance(values, list):
                        return False, "structured_output_schema_invalid", None, "hypothesis_binding_invalid"
                    aggregate.update(str(value) for value in values)
        if abs(prior_end - duration) > 0.25:
            return False, "structured_output_schema_invalid", None, "sequence_timing_invalid"
    return True, None, parsed, None


def compact_blueprint_validator(governed: Mapping[str, Any]):
    allowed_assets = {str(row["asset_id"]) for row in governed.get("assets") or []}
    allowed_claims = {str(row["claim_id"]) for row in governed.get("claims") or []}
    allowed_evidence = {str(row["evidence_id"]) for row in governed.get("evidence") or []}

    def validate(text: str) -> tuple[bool, str | None, Any, str | None]:
        ok, failure, parsed, diagnostic = validate_compact_blueprint(text)
        if not ok:
            return ok, failure, parsed, diagnostic
        if parsed.get("story_id") != governed.get("story_id"):
            return False, "structured_output_schema_invalid", None, "story_binding_invalid"
        for variant in parsed["variants"].values():
            for sequence in variant["sequences"]:
                for hypothesis in sequence["visual_hypotheses"]:
                    if not set(map(str, hypothesis["asset_ids"])).issubset(allowed_assets):
                        return False, "structured_output_schema_invalid", None, "asset_binding_invalid"
                    if not set(map(str, hypothesis["claim_ids"])).issubset(allowed_claims):
                        return False, "structured_output_schema_invalid", None, "claim_binding_invalid"
                    if not set(map(str, hypothesis["evidence_ids"])).issubset(allowed_evidence):
                        return False, "structured_output_schema_invalid", None, "evidence_binding_invalid"
        return True, None, parsed, None

    return validate


def build_legacy_monolithic_prompt(governed: Mapping[str, Any]) -> str:
    """Reproduce the rejected 55-beat request shape for one diagnostic call."""
    contract = {
        "schema_version": BLUEPRINT_SCHEMA_VERSION,
        "story_id": governed["story_id"],
        "creative_thesis": "string",
        "shared_visual_language": {
            "typography": "string",
            "color_system": "string",
            "texture_system": "string",
            "transition_grammar": "string",
        },
        "variants": {
            "short_9x16": {
                "duration_seconds": "45..75",
                "hook": "string",
                "payoff_seconds": "<=12",
                "beats": [
                    {key: "required" for key in sorted(REQUIRED_BEAT_KEYS)}
                    for _ in LEGACY_SHORT_BEATS
                ],
            },
            "midform_16x9": {
                "duration_seconds": "180..360",
                "hook": "string",
                "payoff_seconds": "30..60",
                "beats": [
                    {key: "required" for key in sorted(REQUIRED_BEAT_KEYS)}
                    for _ in LEGACY_MIDFORM_BEATS
                ],
            },
        },
        "music_direction": "string",
        "sfx_cues": ["string"],
        "rights_and_truth_notes": ["string"],
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    }
    instructions = {
        "role": "Capital Chronicle V2 Creative Editor",
        "task": (
            "Author the complete story, hook, narration, screenplay, edit rhythm, shot "
            "concepts, transitions, typography, music direction, and sound design for both "
            "variants. Make every beat visually specific and retention-native."
        ),
        "exact_beat_ids": {
            "short_9x16": list(LEGACY_SHORT_BEATS),
            "midform_16x9": list(LEGACY_MIDFORM_BEATS),
        },
        "constraints": [
            "Return exactly one JSON object and no Markdown.",
            "Use every exact beat id once and preserve its variant prefix.",
            "Populate every field in every beat; do not use placeholders.",
            "Keep short duration 45-75 seconds and payoff at or before 12 seconds.",
            "Keep midform duration 180-360 seconds and payoff from 30-60 seconds.",
            "Bind factual narration only to supplied governed claims/evidence/assets.",
            "Do not invent documentary images, quotes, facts, prices, forecasts, or analysis.",
            "Generated illustration may be editorial illustration only, never evidence.",
            "No browser, upload, publication, or public-write authority exists.",
        ],
        "required_shape": contract,
    }
    return (
        "CREATIVE_EDITOR_REQUEST\n"
        + json.dumps(instructions, ensure_ascii=False, sort_keys=True)
        + "\nGOVERNED_STORY_PACKET\n"
        + json.dumps(governed, ensure_ascii=False, sort_keys=True)
    )


def _parse_single_json_object(text: str) -> tuple[dict[str, Any] | None, str | None]:
    stripped = text.strip()
    if not stripped:
        return None, "json_empty"
    decoder = json.JSONDecoder()
    try:
        parsed, end = decoder.raw_decode(stripped)
    except json.JSONDecodeError:
        return None, "json_decode_error"
    if stripped[end:].strip():
        return None, "json_trailing_content"
    if not isinstance(parsed, dict):
        return None, "schema_top_level_not_object"
    return parsed, None


def validate_legacy_blueprint(
    text: str,
) -> tuple[bool, str | None, Any, str | None]:
    parsed, diagnostic = _parse_single_json_object(text)
    if parsed is None:
        return False, "structured_output_malformed", None, diagnostic
    required_top = {
        "schema_version",
        "story_id",
        "creative_thesis",
        "shared_visual_language",
        "variants",
        "music_direction",
        "sfx_cues",
        "rights_and_truth_notes",
        "public_write",
        "publication_authority",
        "factual_authority",
    }
    if not required_top.issubset(parsed):
        return False, "structured_output_schema_invalid", None, "schema_missing_top_level"
    if parsed.get("schema_version") != BLUEPRINT_SCHEMA_VERSION:
        return False, "structured_output_schema_invalid", None, "schema_version_invalid"
    if parsed.get("public_write") is not False or parsed.get("publication_authority") is not False:
        return False, "structured_output_schema_invalid", None, "authority_boundary_invalid"
    if parsed.get("factual_authority") is not False:
        return False, "structured_output_schema_invalid", None, "authority_boundary_invalid"
    variants = parsed.get("variants")
    if not isinstance(variants, dict) or set(variants) != {"short_9x16", "midform_16x9"}:
        return False, "structured_output_schema_invalid", None, "variant_set_invalid"
    for variant_id, exact_ids in (
        ("short_9x16", LEGACY_SHORT_BEATS),
        ("midform_16x9", LEGACY_MIDFORM_BEATS),
    ):
        variant = variants.get(variant_id)
        if not isinstance(variant, dict):
            return False, "structured_output_schema_invalid", None, "variant_shape_invalid"
        beats = variant.get("beats")
        if not isinstance(beats, list):
            return False, "structured_output_schema_invalid", None, "beats_not_array"
        if [row.get("beat_id") if isinstance(row, dict) else None for row in beats] != list(exact_ids):
            return False, "structured_output_schema_invalid", None, "exact_beat_ids_invalid"
        for row in beats:
            if not isinstance(row, dict) or not REQUIRED_BEAT_KEYS.issubset(row):
                return False, "structured_output_schema_invalid", None, "beat_shape_invalid"
            if not isinstance(row.get("claim_ids"), list) or not isinstance(
                row.get("evidence_ids"), list
            ):
                return False, "structured_output_schema_invalid", None, "beat_binding_invalid"
    return True, None, parsed, None


def sanitized_diagnostic(summary: Mapping[str, Any], governed: Mapping[str, Any]) -> dict[str, Any]:
    attempts = []
    for row in summary.get("attempts") or []:
        attempts.append(
            {
                key: row.get(key)
                for key in (
                    "attempt_number_global",
                    "requested_model",
                    "resolved_model",
                    "model_identity_provider_verified",
                    "provider_invocation_id",
                    "provider_status_class",
                    "provider_finish_reason",
                    "provider_truncation_indicated",
                    "latency_seconds",
                    "usage",
                    "cost",
                    "output_present",
                    "output_character_length",
                    "output_utf8_byte_length",
                    "output_hash",
                    "structured_validation_result",
                    "structured_validation_failure_class",
                    "structured_validation_diagnostic_code",
                    "parser_or_schema_failure_category",
                    "failure_class",
                    "disposition",
                )
            }
        )
    last = attempts[-1] if attempts else {}
    if last.get("provider_truncation_indicated") is True:
        diagnosis = "PROVEN_PROVIDER_OUTPUT_TRUNCATION"
    elif last.get("structured_validation_diagnostic_code") in {
        "schema_missing_top_level",
        "schema_version_invalid",
        "authority_boundary_invalid",
        "variant_set_invalid",
        "variant_shape_invalid",
        "beats_not_array",
        "exact_beat_ids_invalid",
        "beat_shape_invalid",
        "beat_binding_invalid",
        "duration_or_payoff_invalid",
        "narration_missing",
        "sequence_shape_invalid",
        "sequence_timing_invalid",
        "hypothesis_shape_invalid",
        "shot_id_duplicate",
        "hypothesis_binding_invalid",
        "story_binding_invalid",
        "asset_binding_invalid",
        "claim_binding_invalid",
        "evidence_binding_invalid",
    }:
        diagnosis = "PROVEN_DETERMINISTIC_SCHEMA_CONTRACT_MISMATCH"
    elif last.get("structured_validation_diagnostic_code") in {
        "json_empty",
        "json_decode_error",
        "json_trailing_content",
        "schema_top_level_not_object",
    }:
        diagnosis = "STRUCTURED_OUTPUT_PARSE_FAILURE_TRUNCATION_NOT_PROVIDER_PROVEN"
    elif summary.get("terminal_disposition") == "ACCEPTED":
        diagnosis = "LEGACY_MONOLITHIC_CONTRACT_ACCEPTED"
    else:
        diagnosis = "PROVIDER_OR_IDENTITY_FAILURE"
    return {
        "schema_version": SCHEMA_VERSION,
        "status": summary.get("terminal_disposition"),
        "diagnosis": diagnosis,
        "request_shape": "legacy_monolithic_exact_55_beats",
        "governed_story_id": governed["story_id"],
        "governed_story_hash": _logical_hash(governed),
        "role": ROLE_V2_CREATIVE_EDITOR,
        "prompt_template": "retention_native_creative_editor_legacy_55_beat_diagnostic",
        "prompt_version": "v2.0-diagnostic",
        "terminal_disposition": summary.get("terminal_disposition"),
        "selected_model": summary.get("selected_model"),
        "models_attempted_in_order": summary.get("models_attempted_in_order"),
        "total_attempts": summary.get("total_attempts"),
        "total_fallback_transitions": summary.get("total_fallback_transitions"),
        "total_structured_repair_attempts": summary.get("total_structured_repair_attempts"),
        "total_usage": summary.get("total_usage"),
        "total_cost": summary.get("total_cost"),
        "attempts": attempts,
        "raw_rejected_output_persisted": False,
        "browser_or_cdp_actions": 0,
        "uploads": 0,
        "public_writes": 0,
        "publication_authority": False,
        "factual_authority": False,
    }


def run_legacy_diagnostic(
    *, repo_root: Path, control_root: Path, evidence_path: Path
) -> dict[str, Any]:
    governed = load_governed_story_packet(repo_root)
    prompt = build_legacy_monolithic_prompt(governed)
    logical_id = "v2-creative-editor-legacy-55-beat-diagnostic-v1"
    budget = RetryBudget(
        logical_invocation_id=logical_id,
        max_total_provider_attempts=1,
        max_fallback_transitions=0,
        max_same_model_retries=0,
        max_structured_output_repair_attempts=0,
        wall_clock_budget_seconds=900.0,
        per_model_max_attempts=(1,),
    )
    with llm_cycle_budget_scope(
        "v2-creative-editor-legacy-55-beat-diagnostic-v1",
        control_root=control_root,
    ):
        summary = routed_llm_invocation(
            prompt=prompt,
            role_task_id=ROLE_V2_CREATIVE_EDITOR,
            logical_invocation_id=logical_id,
            work_item_id=governed["story_id"],
            timeout_seconds=900.0,
            validator=validate_legacy_blueprint,
            governed_input=governed,
            prompt_template="retention_native_creative_editor_legacy_55_beat_diagnostic",
            prompt_version="v2.0-diagnostic",
            budget=budget,
        )
    evidence = sanitized_diagnostic(summary, governed)
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if summary.get("terminal_disposition") == "ACCEPTED":
        accepted_path = evidence_path.with_name("diagnostic_accepted_blueprint_v2.json")
        accepted_path.write_text(
            json.dumps(summary["output"], indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        evidence["accepted_blueprint_path"] = str(accepted_path)
    return evidence


def run_compact_authorship(
    *, repo_root: Path, control_root: Path, evidence_path: Path
) -> dict[str, Any]:
    governed = load_governed_story_packet(repo_root)
    prompt = build_compact_hierarchical_prompt(governed)
    logical_id = "v2-creative-editor-compact-blueprint-v1"
    # Retry transient provider failures up to the creative-role ceiling. A deterministic
    # parser/schema failure receives no identical blind retry; the contract must be repaired.
    budget = RetryBudget(
        logical_invocation_id=logical_id,
        max_total_provider_attempts=4,
        max_fallback_transitions=0,
        max_same_model_retries=3,
        max_structured_output_repair_attempts=0,
        wall_clock_budget_seconds=900.0,
        per_model_max_attempts=(4,),
    )
    with llm_cycle_budget_scope(
        "v2-creative-editor-compact-blueprint-v1",
        control_root=control_root,
    ):
        summary = routed_llm_invocation(
            prompt=prompt,
            role_task_id=ROLE_V2_CREATIVE_EDITOR,
            logical_invocation_id=logical_id,
            work_item_id=governed["story_id"],
            timeout_seconds=900.0,
            validator=compact_blueprint_validator(governed),
            governed_input=governed,
            prompt_template="retention_native_creative_editor_compact_hierarchical",
            prompt_version="v2.1",
            budget=budget,
        )
    evidence = sanitized_diagnostic(summary, governed)
    evidence.update(
        {
            "schema_version": "contentops.retention_native.creative_editor_authorship.v2",
            "request_shape": "compact_hierarchical_whole_story",
            "prompt_template": "retention_native_creative_editor_compact_hierarchical",
            "prompt_version": "v2.1",
        }
    )
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    if summary.get("terminal_disposition") == "ACCEPTED":
        blueprint_path = evidence_path.with_name("creative_blueprint_v2.json")
        blueprint_path.write_text(
            json.dumps(summary["output"], indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        evidence["accepted_blueprint_path"] = str(blueprint_path)
        evidence["accepted_blueprint_sha256"] = hashlib.sha256(
            blueprint_path.read_bytes()
        ).hexdigest()
    evidence_path.write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("legacy-diagnostic", "compact-authorship"), default="legacy-diagnostic"
    )
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--control-root", type=Path, required=True)
    parser.add_argument("--evidence-path", type=Path, required=True)
    args = parser.parse_args(argv)
    runner = (
        run_legacy_diagnostic
        if args.mode == "legacy-diagnostic"
        else run_compact_authorship
    )
    evidence = runner(
        repo_root=args.repo_root.resolve(),
        control_root=args.control_root.resolve(),
        evidence_path=args.evidence_path.resolve(),
    )
    print(json.dumps(evidence, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
