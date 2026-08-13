"""Concrete-first contracts and deterministic orchestration for the V2-01 proof.

This module is deliberately renderer neutral.  GPT-5.6 owns viewer-visible creative
decisions; this code validates, binds, hashes, scores, and blocks unsafe/incomprehensible
plans.  It grants no publication authority.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Any, Iterable, Mapping, Sequence

SCHEMA_VERSION = "contentops.retention_native.concrete_first.v2"
PROMPT_CONTRACT_VERSION = "concrete_first_segment_prompt.v1"
CREATIVE_MODEL = "new/gpt-5.6-sol-xhigh"

VISUAL_HIERARCHY = (
    "documentary_context",
    "primary_document",
    "native_data_visual",
    "concrete_illustration",
    "explanatory_diagram",
    "pure_abstraction",
    "typography_only",
)
ACCEPTED_RIGHTS = frozenset(
    {
        "PUBLIC_DOMAIN",
        "US_GOVERNMENT_PUBLIC_INFORMATION",
        "NASA_MEDIA_GUIDELINES_EDITORIAL",
        "CREATIVE_COMMONS_ATTRIBUTION",
        "CREATIVE_COMMONS_ATTRIBUTION_SHAREALIKE",
        "CAPITAL_CHRONICLE_OWNED",
    }
)


def logical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _required_text(row: Mapping[str, Any], key: str, owner: str) -> str:
    value = str(row.get(key) or "").strip()
    if not value:
        raise ValueError(f"{owner}_missing:{key}")
    return value


def _required_string_list(row: Mapping[str, Any], key: str, owner: str) -> tuple[str, ...]:
    value = row.get(key)
    if not isinstance(value, list) or not value or any(not str(item).strip() for item in value):
        raise ValueError(f"{owner}_invalid:{key}")
    return tuple(str(item) for item in value)


@dataclass(frozen=True)
class CreativeBible:
    core_viewer_promise: str
    hook: str
    central_question: str
    narrative_arc: str
    tone: str
    pacing_profile: str
    evidence_hierarchy: tuple[str, ...]
    concrete_visual_strategy: str
    documentary_broll_strategy: str
    data_document_strategy: str
    abstraction_policy: str
    audio_intent: str
    short_strategy: str
    midform_strategy: str
    forbidden_motifs_repetition: tuple[str, ...]

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "CreativeBible":
        owner = "creative_bible"
        value = cls(
            **{
                key: _required_text(row, key, owner)
                for key in (
                    "core_viewer_promise",
                    "hook",
                    "central_question",
                    "narrative_arc",
                    "tone",
                    "pacing_profile",
                    "concrete_visual_strategy",
                    "documentary_broll_strategy",
                    "data_document_strategy",
                    "abstraction_policy",
                    "audio_intent",
                    "short_strategy",
                    "midform_strategy",
                )
            },
            evidence_hierarchy=_required_string_list(row, "evidence_hierarchy", owner),
            forbidden_motifs_repetition=_required_string_list(
                row, "forbidden_motifs_repetition", owner
            ),
        )
        if "concrete" not in value.concrete_visual_strategy.lower():
            raise ValueError("creative_bible_concrete_first_not_explicit")
        return value

    def freeze(self) -> dict[str, Any]:
        payload = asdict(self)
        return {"value": payload, "sha256": logical_hash(payload), "immutable": True}


@dataclass(frozen=True)
class SegmentContract:
    segment_id: str
    purpose: str
    narrative_question: str
    dependencies: tuple[str, ...]
    allowed_claim_ids: tuple[str, ...]
    allowed_evidence_ids: tuple[str, ...]
    viewer_knowledge_entering: tuple[str, ...]
    viewer_knowledge_leaving: tuple[str, ...]
    open_loops: tuple[str, ...]
    payoff_rehook_responsibility: str
    target_timing_envelope: Mapping[str, Mapping[str, float]]
    asset_needs: tuple[str, ...]
    continuity_constraints: tuple[str, ...]

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "SegmentContract":
        owner = f"segment:{row.get('segment_id') or 'unknown'}"
        envelope = row.get("target_timing_envelope")
        if not isinstance(envelope, Mapping) or set(envelope) != {"short_9x16", "midform_16x9"}:
            raise ValueError(f"{owner}_timing_envelope_invalid")
        normalized: dict[str, dict[str, float]] = {}
        for variant, limits in envelope.items():
            if not isinstance(limits, Mapping):
                raise ValueError(f"{owner}_timing_envelope_invalid:{variant}")
            minimum = float(limits.get("min_seconds", 0))
            maximum = float(limits.get("max_seconds", 0))
            if minimum <= 0 or maximum < minimum:
                raise ValueError(f"{owner}_timing_envelope_invalid:{variant}")
            normalized[str(variant)] = {"min_seconds": minimum, "max_seconds": maximum}
        return cls(
            segment_id=_required_text(row, "segment_id", owner),
            purpose=_required_text(row, "purpose", owner),
            narrative_question=_required_text(row, "narrative_question", owner),
            dependencies=tuple(str(item) for item in row.get("dependencies") or ()),
            allowed_claim_ids=_required_string_list(row, "allowed_claim_ids", owner),
            allowed_evidence_ids=_required_string_list(row, "allowed_evidence_ids", owner),
            viewer_knowledge_entering=tuple(
                str(item) for item in row.get("viewer_knowledge_entering") or ()
            ),
            viewer_knowledge_leaving=_required_string_list(
                row, "viewer_knowledge_leaving", owner
            ),
            open_loops=tuple(str(item) for item in row.get("open_loops") or ()),
            payoff_rehook_responsibility=_required_text(
                row, "payoff_rehook_responsibility", owner
            ),
            target_timing_envelope=normalized,
            asset_needs=_required_string_list(row, "asset_needs", owner),
            continuity_constraints=_required_string_list(
                row, "continuity_constraints", owner
            ),
        )


def validate_segment_graph(rows: Sequence[Mapping[str, Any]]) -> tuple[SegmentContract, ...]:
    if not 2 <= len(rows) <= 8:
        raise ValueError("segment_graph_dynamic_but_bounded_2_to_8")
    graph = tuple(SegmentContract.from_mapping(row) for row in rows)
    ids = [row.segment_id for row in graph]
    if len(ids) != len(set(ids)):
        raise ValueError("segment_graph_ids_not_unique")
    known: set[str] = set()
    for row in graph:
        unknown = set(row.dependencies) - known
        if unknown:
            raise ValueError(f"segment_graph_dependency_not_prior:{row.segment_id}")
        known.add(row.segment_id)
    return graph


@dataclass(frozen=True)
class AssetCandidate:
    asset_id: str
    visual_class: str
    source_url: str
    rights_status: str
    license_or_terms: str
    attribution: str
    sha256: str
    width: int
    height: int
    semantic_purposes: tuple[str, ...]
    recognizable_focal_object: str
    documentary: bool
    illustrative: bool
    crop_suitability: Mapping[str, float]
    source_quality: float = 1.0
    duplicate_group: str = ""
    prior_use_count: int = 0

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "AssetCandidate":
        value = cls(
            asset_id=_required_text(row, "asset_id", "asset"),
            visual_class=_required_text(row, "visual_class", "asset"),
            source_url=_required_text(row, "source_url", "asset"),
            rights_status=_required_text(row, "rights_status", "asset"),
            license_or_terms=_required_text(row, "license_or_terms", "asset"),
            attribution=_required_text(row, "attribution", "asset"),
            sha256=_required_text(row, "sha256", "asset"),
            width=int(row.get("width") or 0),
            height=int(row.get("height") or 0),
            semantic_purposes=tuple(str(item) for item in row.get("semantic_purposes") or ()),
            recognizable_focal_object=_required_text(
                row, "recognizable_focal_object", "asset"
            ),
            documentary=bool(row.get("documentary")),
            illustrative=bool(row.get("illustrative")),
            crop_suitability={
                str(key): float(number)
                for key, number in dict(row.get("crop_suitability") or {}).items()
            },
            source_quality=float(row.get("source_quality", 1.0)),
            duplicate_group=str(row.get("duplicate_group") or ""),
            prior_use_count=int(row.get("prior_use_count") or 0),
        )
        value.validate()
        return value

    def validate(self) -> None:
        if self.rights_status not in ACCEPTED_RIGHTS:
            raise ValueError(f"asset_rights_not_accepted:{self.asset_id}")
        if len(self.sha256) != 64 or any(character not in "0123456789abcdef" for character in self.sha256):
            raise ValueError(f"asset_sha256_invalid:{self.asset_id}")
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"asset_dimensions_invalid:{self.asset_id}")
        if not self.semantic_purposes:
            raise ValueError(f"asset_semantic_purpose_missing:{self.asset_id}")
        if self.documentary and self.illustrative:
            raise ValueError(f"asset_role_ambiguous:{self.asset_id}")
        if set(self.crop_suitability) != {"short_9x16", "midform_16x9"}:
            raise ValueError(f"asset_crop_suitability_incomplete:{self.asset_id}")


def score_asset(
    candidate: AssetCandidate,
    *,
    semantic_need: str,
    variant_id: str,
    selected_duplicate_groups: Iterable[str] = (),
) -> float:
    words = {word for word in semantic_need.lower().replace("/", " ").split() if len(word) > 2}
    corpus = " ".join((candidate.recognizable_focal_object, *candidate.semantic_purposes)).lower()
    relevance = sum(1 for word in words if word in corpus) / max(1, len(words))
    rights = 1.0 if candidate.rights_status in ACCEPTED_RIGHTS else 0.0
    crop = max(0.0, min(1.0, float(candidate.crop_suitability.get(variant_id, 0))))
    resolution = min(1.0, math.sqrt(candidate.width * candidate.height) / 1800)
    duplicate_penalty = 0.3 if candidate.duplicate_group in set(selected_duplicate_groups) and candidate.duplicate_group else 0.0
    concentration_penalty = min(0.25, candidate.prior_use_count * 0.04)
    return round(
        max(
            0.0,
            0.34 * relevance
            + 0.22 * rights
            + 0.15 * candidate.source_quality
            + 0.16 * crop
            + 0.13 * resolution
            - duplicate_penalty
            - concentration_penalty,
        ),
        6,
    )


def broker_assets(
    candidates: Sequence[AssetCandidate], *, semantic_need: str, variant_id: str, limit: int = 5
) -> list[dict[str, Any]]:
    scored = [
        {"asset_id": row.asset_id, "score": score_asset(row, semantic_need=semantic_need, variant_id=variant_id)}
        for row in candidates
    ]
    return sorted(scored, key=lambda row: (-float(row["score"]), str(row["asset_id"])))[:limit]


@dataclass(frozen=True)
class VisualGroundingContract:
    beat_id: str
    viewer_takeaway: str
    narration_intent: str
    primary_visual_type: str
    recognizable_subject: str
    required_asset_ids: tuple[str, ...]
    preferred_asset_ids: tuple[str, ...]
    abstract_substitution_allowed: bool
    recognition_deadline_seconds: float
    captions_hidden_takeaway: str
    aspect_ratio: str
    claim_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    continuity_role: str

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "VisualGroundingContract":
        value = cls(
            beat_id=_required_text(row, "beat_id", "grounding"),
            viewer_takeaway=_required_text(row, "viewer_takeaway", "grounding"),
            narration_intent=_required_text(row, "narration_intent", "grounding"),
            primary_visual_type=_required_text(row, "primary_visual_type", "grounding"),
            recognizable_subject=_required_text(row, "recognizable_subject", "grounding"),
            required_asset_ids=tuple(str(item) for item in row.get("required_asset_ids") or ()),
            preferred_asset_ids=tuple(str(item) for item in row.get("preferred_asset_ids") or ()),
            abstract_substitution_allowed=bool(row.get("abstract_substitution_allowed")),
            recognition_deadline_seconds=float(row.get("recognition_deadline_seconds", 0)),
            captions_hidden_takeaway=_required_text(row, "captions_hidden_takeaway", "grounding"),
            aspect_ratio=_required_text(row, "aspect_ratio", "grounding"),
            claim_ids=_required_string_list(row, "claim_ids", "grounding"),
            evidence_ids=_required_string_list(row, "evidence_ids", "grounding"),
            continuity_role=_required_text(row, "continuity_role", "grounding"),
        )
        if value.primary_visual_type not in VISUAL_HIERARCHY:
            raise ValueError(f"grounding_visual_type_invalid:{value.beat_id}")
        if value.recognition_deadline_seconds <= 0 or value.recognition_deadline_seconds > 5:
            raise ValueError(f"grounding_recognition_deadline_invalid:{value.beat_id}")
        if value.required_asset_ids and value.abstract_substitution_allowed:
            raise ValueError(f"grounding_required_asset_cannot_allow_abstract_substitution:{value.beat_id}")
        return value


def enforce_must_use_assets(
    contracts: Sequence[VisualGroundingContract], actual_assets_by_beat: Mapping[str, Sequence[str]]
) -> dict[str, Any]:
    missing: dict[str, list[str]] = {}
    for contract in contracts:
        actual = set(actual_assets_by_beat.get(contract.beat_id) or ())
        absent = sorted(set(contract.required_asset_ids) - actual)
        if absent:
            missing[contract.beat_id] = absent
    return {
        "status": "PASS" if not missing else "BLOCK",
        "missing_required_assets": missing,
        "silent_abstraction_substitution": bool(missing),
    }


def compile_chart_plan(spec: Mapping[str, Any], variant_id: str) -> dict[str, Any]:
    points = spec.get("points")
    if not isinstance(points, list) or len(points) < 2:
        raise ValueError("chart_points_insufficient")
    if variant_id not in {"short_9x16", "midform_16x9"}:
        raise ValueError("chart_variant_invalid")
    portrait = variant_id == "short_9x16"
    return {
        "compiler": "native_chart.v1",
        "variant_id": variant_id,
        "composition": "portrait_stacked_direct_labels" if portrait else "landscape_focused_direct_labels",
        "direct_labels": True,
        "legend_required": False,
        "focused_range": spec.get("focused_range"),
        "highlighted_point_ids": list(spec.get("highlighted_point_ids") or ()),
        "source_label": _required_text(spec, "source_label", "chart"),
        "points": points,
        "letterboxed_landscape_source": False,
        "sha256": logical_hash({"variant_id": variant_id, "spec": spec}),
    }


def compile_map_plan(spec: Mapping[str, Any], variant_id: str) -> dict[str, Any]:
    required = {"Persian Gulf", "Strait of Hormuz", "Gulf of Oman"}
    labels = {str(item) for item in spec.get("labels") or ()}
    if not required <= labels:
        raise ValueError("map_recognizable_geography_missing")
    return {
        "compiler": "native_map.v1",
        "variant_id": variant_id,
        "geography_source": _required_text(spec, "geography_source", "map"),
        "labels": sorted(labels),
        "chokepoint": "Strait of Hormuz",
        "shipping_route_required": True,
        "generic_geometry_forbidden": True,
        "portrait_reframe": variant_id == "short_9x16",
        "sha256": logical_hash({"variant_id": variant_id, "spec": spec}),
    }


def compile_document_plan(spec: Mapping[str, Any], variant_id: str) -> dict[str, Any]:
    excerpt = _required_text(spec, "governed_excerpt", "document")
    if len(excerpt) > 420:
        raise ValueError("document_excerpt_not_compact")
    return {
        "compiler": "native_document.v1",
        "variant_id": variant_id,
        "document_asset_id": _required_text(spec, "document_asset_id", "document"),
        "source_label": _required_text(spec, "source_label", "document"),
        "source_date": _required_text(spec, "source_date", "document"),
        "governed_excerpt": excerpt,
        "focus_mode": "portrait_sentence_crop" if variant_id == "short_9x16" else "document_crop_plus_enlarged_excerpt",
        "full_page_tiny_render_forbidden": True,
        "sha256": logical_hash({"variant_id": variant_id, "spec": spec}),
    }


def build_segment_prompt(
    *,
    creative_bible_frozen: Mapping[str, Any],
    segment: SegmentContract,
    governed_evidence: Mapping[str, Any],
    continuity_state: Mapping[str, Any],
    available_assets: Sequence[Mapping[str, Any]],
    previous_summary: str | None,
    next_summary: str | None,
) -> dict[str, Any]:
    claims = dict(governed_evidence.get("claims") or {})
    evidence = dict(governed_evidence.get("evidence") or {})
    bounded = {
        "claims": {key: claims[key] for key in segment.allowed_claim_ids if key in claims},
        "evidence": {key: evidence[key] for key in segment.allowed_evidence_ids if key in evidence},
    }
    if set(bounded["claims"]) != set(segment.allowed_claim_ids):
        raise ValueError(f"segment_claim_binding_missing:{segment.segment_id}")
    if set(bounded["evidence"]) != set(segment.allowed_evidence_ids):
        raise ValueError(f"segment_evidence_binding_missing:{segment.segment_id}")
    payload = {
        "contract_version": PROMPT_CONTRACT_VERSION,
        "requested_model": CREATIVE_MODEL,
        "creative_bible": creative_bible_frozen,
        "segment": asdict(segment),
        "governed_evidence": bounded,
        "continuity_state": continuity_state,
        "available_assets": list(available_assets),
        "previous_segment_summary": previous_summary,
        "next_segment_summary": next_summary,
        "output_contract": {
            "segment_summary": "string",
            "continuity_state_leaving": ["string"],
            "short_9x16_beats": ["VisualGroundingContract plus narration and storyboard frame"],
            "midform_16x9_beats": ["VisualGroundingContract plus narration and storyboard frame"],
            "rules": [
                "concrete-first; abstraction only when explanatory",
                "use exact asset IDs and governed claim/evidence IDs",
                "do not invent facts, sources, assets, or licenses",
                "separately compose 9:16 and 16:9",
                "return JSON only",
            ],
        },
    }
    return {"payload": payload, "input_sha256": logical_hash(payload)}


COMPREHENSION_KEYS = (
    "first_second_context",
    "concrete_recognition",
    "semantic_continuity",
    "captions_hidden_story_reconstruction",
    "asset_plan_compliance",
    "abstract_only_run",
)


def evaluate_comprehension_gate(
    *, assessments: Mapping[str, bool], reconstructed_concepts: Sequence[str]
) -> dict[str, Any]:
    missing_keys = [key for key in COMPREHENSION_KEYS if key not in assessments]
    if missing_keys:
        raise ValueError("comprehension_assessments_missing:" + ",".join(missing_keys))
    required_concepts = {
        "oil_and_hormuz",
        "shipping_supply_changed",
        "eia_forecast_source",
        "production_inventories_demand_matter",
        "price_not_proof",
        "future_confirmation_points",
    }
    missing_concepts = sorted(required_concepts - set(reconstructed_concepts))
    failed = [key for key, passed in assessments.items() if not bool(passed)]
    return {
        "status": "PASS" if not failed and not missing_concepts else "BLOCK",
        "failed_dimensions": failed,
        "missing_reconstructed_concepts": missing_concepts,
        "motion_code_authorized": not failed and not missing_concepts,
    }


def visual_mix_summary(beats: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    totals = {key: 0.0 for key in VISUAL_HIERARCHY}
    for beat in beats:
        visual_class = str(beat.get("primary_visual_type") or "")
        if visual_class not in totals:
            raise ValueError(f"visual_mix_unknown_class:{visual_class}")
        totals[visual_class] += float(beat.get("duration_seconds") or 0)
    duration = sum(totals.values())
    ratios = {key: round(value / duration, 6) if duration else 0.0 for key, value in totals.items()}
    abstraction = ratios["pure_abstraction"] + ratios["typography_only"]
    return {
        "seconds": totals,
        "ratios": ratios,
        "abstract_or_typography_ratio": round(abstraction, 6),
        "pure_abstraction_intentional_minority": abstraction < 0.25,
        "status": "PASS" if duration > 0 and abstraction < 0.25 else "BLOCK",
    }


def zero_public_write_manifest() -> dict[str, Any]:
    return {
        "public_write_authority": False,
        "uploads": 0,
        "platform_writes": 0,
        "browser_or_cdp_actions": 0,
        "v1_store_mutations": 0,
        "v2_02_started": False,
        "codex_local_brain_active": False,
    }
