"""Generic creative-pacing contracts for Creative-Authority Hybrid V2 jobs.

This module deliberately stops below direction.  Codex authors semantic beats,
visual states, within-state actions, and transition reasons.  Deterministic code
only verifies coverage, truth-safe serialization, and review diagnostics.
"""
from __future__ import annotations

from collections import Counter
import re
from statistics import mean, median
from typing import Any, Mapping, Sequence


CREATIVE_MODEL = "new/gpt-5.6-sol-xhigh"
CREATIVE_ROLE_MODELS = {
    "V2_CREATIVE_EDITOR": CREATIVE_MODEL,
    "V2_MOTION_CODE_AUTHOR": CREATIVE_MODEL,
    "V2_CREATIVE_REVISION_AUTHOR": CREATIVE_MODEL,
}
CREATIVE_MODEL_RETRY_LIMIT = 3

CREATIVE_PACING_PROMPT_CONTRACT = """
CREATIVE PACING CONTRACT — CREATIVE-AUTHORITY HYBRID

You are the fresh per-video creative/editorial decision-maker. Governed truth,
numeric bindings, rights, and publication authority remain outside your role.

SEMANTIC BEAT != VISUAL STATE != WITHIN-STATE ACTION != TRANSITION EVENT.

- A semantic beat is a narration or editorial information unit.
- A visual state is the viewer's persistent context. Several semantic beats may
  share one visual state.
- A within-state action changes emphasis, annotation, selection, comparison, or
  progressive disclosure without replacing the full composition.
- A transition event is an intentional viewer-context reset. It must identify
  the materially new evidence, place, actor, mechanism, question, analytical
  phase, chapter, or emotional/reset function that earns its switching cost.

Do not reset the screen merely because narration reaches another sentence, a
minor qualifier, or another number inside the same conceptual object. Prefer a
persistent chart, map, document, mechanism, or balance sheet with progressive
disclosure. Absorb low-information title, boundary, and synthesis cards into an
existing state unless a real chapter or cognitive reset needs them.

Allocate ingestion dwell from comprehension needs: visual complexity, text,
panels, axes/legend burden, novelty, numeric density, mechanism complexity,
narration interaction, and phone readability. There is no canonical screen-
change cadence and no generic maximum visual-state duration. A sustained state
with useful reveals can be excellent; a decorative stagnant state can be poor.

Jointly optimize narration and visuals before final build-audio lock. Dense
evidence and mechanism passages should use shorter clauses, fewer stacked new
facts, deliberate pauses, and room after major claims. Simple context may move
faster. Preserve governed meaning when condensing, reordering, or removing
redundancy.

Author short and longform independently. Shorts may often move faster but must
not maximize cut count. Longform should use chapter rhythm, persistent analytical
states, deliberate re-hooks, and breathing room. Inspect actual rendered media,
including the final third; storyboard counts and machine diagnostics are not an
aesthetic pass.

Viewer-facing copy must never expose scene IDs, QA states, motion policies,
pipeline labels, semantic/visual-state terminology, or internal governance
jargon. Source identity and date are useful; implementation language is not.
""".strip()


INTERNAL_JARGON_PATTERNS: dict[str, re.Pattern[str]] = {
    "scene_id": re.compile(r"\b[LS]\d{2}(?:[_\s-][A-Z0-9_]+)?\b", re.IGNORECASE),
    "static_full_context": re.compile(r"\bSTATIC[ _-]+FULL[ _-]+CONTEXT\b", re.IGNORECASE),
    "governed_internal": re.compile(r"\bGOVERNED\b", re.IGNORECASE),
    "qa_state": re.compile(r"\b(?:QA|PASS_[A-Z0-9_]+|FAIL_[A-Z0-9_]+)\b", re.IGNORECASE),
    "pipeline": re.compile(r"\b(?:PIPELINE|MOTION[ _-]+POLICY|SEMANTIC[ _-]+BEAT|VISUAL[ _-]+STATE)\b", re.IGNORECASE),
}


def authored_visual_states(
    scene_id: str,
    semantic_beats: Sequence[Mapping[str, Any]],
    authored_specs: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Bind Codex-authored state groups to exact semantic-beat timing.

    ``authored_specs`` is story-specific creative authority.  This function does
    not infer groups from seconds, beat count, or a visual recipe.
    """
    if not semantic_beats:
        raise ValueError(f"empty_semantic_beats:{scene_id}")
    states: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    covered: list[int] = []
    for state_index, spec in enumerate(authored_specs):
        indexes = [int(value) for value in spec["semantic_beat_indexes"]]
        if not indexes or indexes != list(range(indexes[0], indexes[-1] + 1)):
            raise ValueError(f"noncontiguous_state_beats:{scene_id}:{indexes}")
        if min(indexes) < 0 or max(indexes) >= len(semantic_beats):
            raise IndexError(f"state_beat_out_of_range:{scene_id}:{indexes}")
        covered.extend(indexes)
        grouped = [dict(semantic_beats[index]) for index in indexes]
        anchor_index = int(spec.get("anchor_beat_index", indexes[0]))
        if anchor_index not in indexes:
            raise ValueError(f"anchor_outside_state:{scene_id}:{anchor_index}")
        anchor = dict(semantic_beats[anchor_index])
        start = float(grouped[0]["start_seconds"])
        end = float(grouped[-1]["end_seconds"])
        state_id = f"{scene_id}_V{state_index + 1:02d}"
        transition_id = f"{scene_id}_T{state_index + 1:02d}"
        actions: list[dict[str, Any]] = []
        for action_index, beat in enumerate(grouped):
            actions.append({
                "action_id": f"{state_id}_A{action_index + 1:02d}",
                "semantic_beat_id": beat["beat_id"],
                "at_seconds": round(float(beat["start_seconds"]) - start, 6),
                "action": "establish_context" if action_index == 0 else str(spec.get("reveal_action", "progressive_disclosure")),
                "emphasis": beat.get("label", ""),
                "utility": beat.get("detail", ""),
            })
        transition = {
            "transition_id": transition_id,
            "scene_id": scene_id,
            "to_visual_state_id": state_id,
            "from_visual_state_id": states[-1]["visual_state_id"] if states else None,
            "event_type": "chapter_entry" if state_index == 0 else "full_screen_context_reset",
            "at_seconds": round(start, 6),
            "earned_by": str(spec["transition_reason"]),
            "new_context": str(spec["context_key"]),
        }
        transitions.append(transition)
        states.append({
            "visual_state_id": state_id,
            "scene_id": scene_id,
            "start_seconds": round(start, 6),
            "end_seconds": round(end, 6),
            "duration_seconds": round(end - start, 6),
            "semantic_beat_ids": [str(beat["beat_id"]) for beat in grouped],
            "anchor_beat_id": str(anchor["beat_id"]),
            "display_layout": str(spec.get("display_layout", anchor["layout"])),
            "context_key": str(spec["context_key"]),
            "information_density": str(spec.get("information_density", "moderate")),
            "ingestion_rationale": str(spec.get("ingestion_rationale", "")),
            "progressive_disclosure": len(grouped) > 1,
            "low_information_standalone_card": bool(spec.get("low_information_standalone_card", False)),
            "within_state_actions": actions,
            "transition_in_id": transition_id,
            "stagnation_review": str(spec.get("stagnation_review", "UTILITY_CHANGES_WITH_NARRATION")),
        })
    if covered != list(range(len(semantic_beats))):
        raise ValueError(f"semantic_beat_coverage_mismatch:{scene_id}:{covered}")
    return states, transitions


def _percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def validate_visual_state_architecture(scenes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Validate representation and continuity without imposing duration ceilings."""
    errors: list[str] = []
    warnings: list[dict[str, Any]] = []
    for scene in scenes:
        scene_id = str(scene["scene_id"])
        beats = list(scene.get("material_plan", []))
        states = list(scene.get("visual_state_plan", []))
        transitions = list(scene.get("transition_events", []))
        beat_ids = [str(row["beat_id"]) for row in beats]
        mapped = [str(beat_id) for state in states for beat_id in state.get("semantic_beat_ids", [])]
        if mapped != beat_ids:
            errors.append(f"semantic_state_mapping_mismatch:{scene_id}")
        if len(transitions) != len(states):
            errors.append(f"transition_state_count_mismatch:{scene_id}")
        prior_end = 0.0
        for index, state in enumerate(states):
            start, end = float(state["start_seconds"]), float(state["end_seconds"])
            if abs(start - prior_end) > 1e-5:
                errors.append(f"visual_state_timeline_gap:{state['visual_state_id']}:{prior_end}:{start}")
            if end <= start:
                errors.append(f"nonpositive_visual_state:{state['visual_state_id']}")
            prior_end = end
            actions = list(state.get("within_state_actions", []))
            if len(actions) != len(state.get("semantic_beat_ids", [])):
                errors.append(f"within_state_action_coverage:{state['visual_state_id']}")
            if state.get("information_density") == "high" and not state.get("ingestion_rationale"):
                warnings.append({"kind": "high_information_dwell_rationale_missing", "visual_state_id": state["visual_state_id"]})
            if state.get("low_information_standalone_card"):
                warnings.append({"kind": "low_information_standalone_card", "visual_state_id": state["visual_state_id"], "duration_seconds": state["duration_seconds"]})
            if index and transitions[index].get("from_visual_state_id") != states[index - 1]["visual_state_id"]:
                errors.append(f"transition_lineage_mismatch:{transitions[index].get('transition_id')}")
        if states and abs(prior_end - float(scene["duration_seconds"])) > 1e-4:
            errors.append(f"visual_state_scene_duration_mismatch:{scene_id}:{prior_end}:{scene['duration_seconds']}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "review_flags": warnings,
        "duration_policy": "NO_GENERIC_MAXIMUM; review utility, ingestion, and unjustified stagnation instead of raw seconds",
    }


def scan_internal_jargon(values: Sequence[str]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    for value_index, value in enumerate(values):
        for label, pattern in INTERNAL_JARGON_PATTERNS.items():
            for match in pattern.finditer(value):
                findings.append({"kind": label, "value_index": value_index, "match": match.group(0)})
    return {"status": "PASS" if not findings else "FAIL", "findings": findings, "scanned_values": len(values)}


def pacing_diagnostics(variants: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
    """Create descriptive owner/Codex review surfaces, never universal gates."""
    result: dict[str, Any] = {}
    for variant, scenes in variants.items():
        semantic_beats = [beat for scene in scenes for beat in scene.get("material_plan", [])]
        states = [state for scene in scenes for state in scene.get("visual_state_plan", [])]
        transitions = [event for scene in scenes for event in scene.get("transition_events", [])]
        durations = [float(state["duration_seconds"]) for state in states]
        total = sum(float(scene["duration_seconds"]) for scene in scenes)
        full_resets = [event for event in transitions if event["event_type"] == "full_screen_context_reset"]
        progressive = [state for state in states if state.get("progressive_disclosure")]
        high_info = [state for state in states if state.get("information_density") == "high"]
        low_cards = [state for state in states if state.get("low_information_standalone_card")]
        near_identical: list[dict[str, Any]] = []
        ordered_states: list[tuple[float, Mapping[str, Any]]] = []
        cursor = 0.0
        for scene in scenes:
            for state in scene.get("visual_state_plan", []):
                ordered_states.append((cursor + float(state["start_seconds"]), state))
            cursor += float(scene["duration_seconds"])
        for (prior_time, prior), (current_time, current) in zip(ordered_states, ordered_states[1:]):
            if prior.get("context_key") == current.get("context_key") and prior.get("display_layout") == current.get("display_layout"):
                near_identical.append({
                    "from": prior["visual_state_id"], "to": current["visual_state_id"],
                    "at_seconds": round(current_time, 3), "review": "Could these remain one persistent context?",
                })
        final_start = total * 2 / 3 if total else 0
        final_states = [state for start, state in ordered_states if start >= final_start]
        chapter_rows: list[dict[str, Any]] = []
        cursor = 0.0
        for scene in scenes:
            scene_states = list(scene.get("visual_state_plan", []))
            chapter_rows.append({
                "scene_id": scene["scene_id"], "start_seconds": round(cursor, 3),
                "duration_seconds": round(float(scene["duration_seconds"]), 3),
                "semantic_beats": len(scene.get("material_plan", [])), "visual_states": len(scene_states),
                "full_screen_resets_inside_chapter": max(0, len(scene_states) - 1),
            })
            cursor += float(scene["duration_seconds"])
        result[variant] = {
            "semantic_beat_count": len(semantic_beats),
            "visual_state_count": len(states),
            "full_screen_transition_count": max(0, len(transitions) - 1),
            "semantic_beats_per_visual_state": round(len(semantic_beats) / len(states), 3) if states else 0,
            "visual_state_duration_seconds": {
                "minimum": round(min(durations), 3) if durations else 0,
                "median": round(median(durations), 3) if durations else 0,
                "mean": round(mean(durations), 3) if durations else 0,
                "p75": round(_percentile(durations, .75), 3),
                "p90": round(_percentile(durations, .90), 3),
                "maximum": round(max(durations), 3) if durations else 0,
            },
            "high_information_evidence_dwell": [{
                "visual_state_id": state["visual_state_id"], "duration_seconds": state["duration_seconds"],
                "ingestion_rationale": state["ingestion_rationale"], "semantic_beats": len(state["semantic_beat_ids"]),
            } for state in high_info],
            "progressive_disclosure": {
                "state_count": len(progressive),
                "semantic_beats_carried": sum(len(state["semantic_beat_ids"]) for state in progressive),
                "examples": [state["visual_state_id"] for state in progressive[:12]],
            },
            "repeated_near_identical_visual_state_churn": near_identical,
            "low_information_standalone_card_burden": {
                "state_count": len(low_cards),
                "screen_seconds": round(sum(float(state["duration_seconds"]) for state in low_cards), 3),
                "states": [state["visual_state_id"] for state in low_cards],
            },
            "chapter_reset_cadence": chapter_rows,
            "actual_final_third_pacing": {
                "start_seconds": round(final_start, 3), "visual_state_count": len(final_states),
                "mean_state_seconds": round(mean([float(state["duration_seconds"]) for state in final_states]), 3) if final_states else 0,
                "progressive_state_count": sum(bool(state.get("progressive_disclosure")) for state in final_states),
            },
            "diagnostic_policy": "Descriptive owner/Codex review only; no universal numerical pass threshold.",
        }
    return {"schema": "contentops.v2.creative_pacing_diagnostics.v1", "variants": result}


def viewer_copy_values(scenes: Sequence[Mapping[str, Any]]) -> list[str]:
    values: list[str] = []
    for scene in scenes:
        for key in ("headline", "dek", "caption", "source", "narration"):
            if scene.get(key):
                values.append(str(scene[key]))
        for beat in scene.get("material_plan", []):
            values.extend([str(beat.get("label", "")), str(beat.get("detail", ""))])
    return values


def summarize_prompt_contract() -> dict[str, Any]:
    return {
        "schema": "contentops.v2.creative_pacing_prompt_contract.v1",
        "role_models": dict(CREATIVE_ROLE_MODELS),
        "same_model_retry_limit": CREATIVE_MODEL_RETRY_LIMIT,
        "fallback_allowed": False,
        "contract": CREATIVE_PACING_PROMPT_CONTRACT,
    }
