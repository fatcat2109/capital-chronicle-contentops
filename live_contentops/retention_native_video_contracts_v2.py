"""Renderer-neutral contracts for the retention-native ContentOps V2 video lane.

These contracts carry editorial and creative authority into a renderer.  They do
not grant publication authority and deliberately contain no provider transport.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Mapping, Sequence


class StoryMode(StrEnum):
    ENTITY_EVENT = "ENTITY_EVENT"
    DOCUMENT_REVEAL = "DOCUMENT_REVEAL"
    DATA_MECHANISM = "DATA_MECHANISM"
    CONFLICT_TIMELINE = "CONFLICT_TIMELINE"
    EARNINGS_BREAKDOWN = "EARNINGS_BREAKDOWN"
    BREAKING_UPDATE = "BREAKING_UPDATE"


class SelectionStatus(StrEnum):
    VIDEO_SELECTED = "VIDEO_SELECTED"
    SHORT_ONLY = "SHORT_ONLY"
    MIDFORM_SELECTED = "MIDFORM_SELECTED"
    DEFERRED = "DEFERRED"
    VIDEO_BLOCKED = "VIDEO_BLOCKED"
    VIDEO_NOT_SELECTED = "VIDEO_NOT_SELECTED"


@dataclass(frozen=True)
class VideoOpportunity:
    video_id: str
    story_id: str
    story_version: str
    title: str
    story_mode: StoryMode
    selection_status: SelectionStatus
    evidence_hashes: tuple[str, ...]
    eligible_formats: tuple[str, ...]
    scores: Mapping[str, float]
    selection_reasons: tuple[str, ...]
    estimated_production_cost: str
    public_write_authority: bool = False
    test_only_non_public: bool = False

    def validate(self) -> None:
        _require_id("video_id", self.video_id)
        _require_id("story_id", self.story_id)
        if self.public_write_authority:
            raise ValueError("v2_vertical_slice_public_write_forbidden")
        if self.selection_status in {
            SelectionStatus.VIDEO_SELECTED,
            SelectionStatus.SHORT_ONLY,
            SelectionStatus.MIDFORM_SELECTED,
        }:
            if not self.evidence_hashes:
                raise ValueError("selected_video_requires_evidence_hashes")
            if not self.eligible_formats:
                raise ValueError("selected_video_requires_format")
        for key, value in self.scores.items():
            if not 0 <= float(value) <= 1:
                raise ValueError(f"video_opportunity_score_out_of_range:{key}")


@dataclass(frozen=True)
class EngagementBrief:
    video_id: str
    target_audience: str
    viewer_question: str
    why_now: str
    core_promise: str
    hook: str
    pattern_interrupt: str
    central_tension: str
    open_loops: tuple[Mapping[str, str], ...]
    payoff_checkpoints: tuple[Mapping[str, str], ...]
    rehooks: tuple[Mapping[str, str], ...]
    pacing_map: tuple[Mapping[str, Any], ...]
    emotional_register: str
    prohibited_overclaims: tuple[str, ...]
    cta: str
    binge_target: str
    platform_hooks: Mapping[str, str]

    def validate(self) -> None:
        _require_id("video_id", self.video_id)
        for name in ("target_audience", "viewer_question", "core_promise", "hook", "central_tension"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"engagement_brief_missing:{name}")
        loop_ids = [str(row.get("loop_id") or "") for row in self.open_loops]
        if any(not item for item in loop_ids) or len(loop_ids) != len(set(loop_ids)):
            raise ValueError("engagement_brief_open_loop_ids_invalid")


@dataclass(frozen=True)
class NarrativeBeat:
    beat_id: str
    scene_id: str
    chapter_id: str
    variant_id: str
    order: int
    narrative_role: str
    narration_text: str
    claim_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    viewer_takeaway: str
    visual_purpose: str
    asset_ids: tuple[str, ...]
    edit_decision_ids: tuple[str, ...]
    audio_state: str
    transition_intent: str
    target_duration_seconds: float
    open_loop_id: str | None = None
    payoff_for: tuple[str, ...] = ()

    def validate(self) -> None:
        for name in ("beat_id", "scene_id", "chapter_id", "variant_id"):
            _require_id(name, str(getattr(self, name)))
        if self.order < 0:
            raise ValueError(f"beat_order_invalid:{self.beat_id}")
        if not self.narration_text.strip():
            raise ValueError(f"beat_narration_missing:{self.beat_id}")
        if not self.claim_ids or not self.evidence_ids:
            raise ValueError(f"beat_factual_binding_missing:{self.beat_id}")
        if not self.asset_ids or not self.edit_decision_ids:
            raise ValueError(f"beat_creative_authority_missing:{self.beat_id}")
        if self.target_duration_seconds <= 0:
            raise ValueError(f"beat_duration_invalid:{self.beat_id}")


@dataclass(frozen=True)
class NarrativeBeatGraph:
    video_id: str
    variant_id: str
    beats: tuple[NarrativeBeat, ...]

    def validate(self) -> None:
        if not self.beats:
            raise ValueError(f"narrative_beat_graph_empty:{self.variant_id}")
        ids = [row.beat_id for row in self.beats]
        if len(ids) != len(set(ids)):
            raise ValueError(f"narrative_beat_ids_not_unique:{self.variant_id}")
        if [row.order for row in self.beats] != list(range(len(self.beats))):
            raise ValueError(f"narrative_beat_order_not_contiguous:{self.variant_id}")
        for beat in self.beats:
            beat.validate()
            if beat.variant_id != self.variant_id:
                raise ValueError(f"narrative_beat_variant_mismatch:{beat.beat_id}")


EDIT_OPERATIONS = {
    "CUT",
    "REFRAME",
    "PUNCH_IN",
    "DOCUMENT_FOCUS",
    "SOURCE_HIGHLIGHT",
    "CHART_TRACE",
    "POINT_ANNOTATION",
    "MAP_TRACE",
    "TIMELINE_STEP",
    "COMPARISON_REVEAL",
    "KINETIC_TEXT",
    "LOCATION_CUTAWAY",
    "MECHANISM_FLOW",
    "PAYOFF_REVEAL",
    "WIPE_TRANSITION",
}


@dataclass(frozen=True)
class EditDecision:
    decision_id: str
    beat_id: str
    at_seconds: float
    operation: str
    asset_id: str | None
    narrative_purpose: str
    primary_visual_change: bool
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _require_id("decision_id", self.decision_id)
        _require_id("beat_id", self.beat_id)
        if self.operation not in EDIT_OPERATIONS:
            raise ValueError(f"edit_operation_unsupported:{self.decision_id}:{self.operation}")
        if self.at_seconds < 0:
            raise ValueError(f"edit_decision_time_invalid:{self.decision_id}")
        if not self.narrative_purpose.strip():
            raise ValueError(f"edit_decision_purpose_missing:{self.decision_id}")


@dataclass(frozen=True)
class EditDecisionGraph:
    video_id: str
    variant_id: str
    decisions: tuple[EditDecision, ...]

    def validate(self, beat_graph: NarrativeBeatGraph) -> None:
        beat_ids = {row.beat_id for row in beat_graph.beats}
        decision_ids = [row.decision_id for row in self.decisions]
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError(f"edit_decision_ids_not_unique:{self.variant_id}")
        by_beat: dict[str, list[EditDecision]] = {item: [] for item in beat_ids}
        for row in self.decisions:
            row.validate()
            if row.beat_id not in beat_ids:
                raise ValueError(f"edit_decision_unknown_beat:{row.decision_id}")
            by_beat[row.beat_id].append(row)
        for beat in beat_graph.beats:
            actual = {row.decision_id for row in by_beat[beat.beat_id]}
            if actual != set(beat.edit_decision_ids):
                raise ValueError(f"edit_decision_binding_mismatch:{beat.beat_id}")
            if not any(row.primary_visual_change for row in by_beat[beat.beat_id]):
                raise ValueError(f"beat_has_no_primary_visual_change:{beat.beat_id}")


ALLOWED_RIGHTS_STATUSES = {
    "PUBLIC_DOMAIN",
    "US_GOVERNMENT_PUBLIC_INFORMATION",
    "NASA_MEDIA_GUIDELINES_EDITORIAL",
    "CAPITAL_CHRONICLE_OWNED",
    "CAPITAL_CHRONICLE_INTERNAL",
}


@dataclass(frozen=True)
class AssetSpec:
    asset_id: str
    asset_class: str
    editorial_purpose: str
    source_label: str
    source_url: str
    rights_status: str
    license_or_terms: str
    attribution: str
    sha256: str | None
    source_path: str | None
    beat_ids: tuple[str, ...]
    synthetic: bool = False
    documentary: bool = True
    contains_real_person: bool = False

    def validate(self) -> None:
        _require_id("asset_id", self.asset_id)
        if self.rights_status not in ALLOWED_RIGHTS_STATUSES:
            raise ValueError(f"asset_rights_not_accepted:{self.asset_id}")
        if not self.source_url or not self.attribution or not self.license_or_terms:
            raise ValueError(f"asset_provenance_incomplete:{self.asset_id}")
        if self.synthetic and self.documentary:
            raise ValueError(f"synthetic_asset_cannot_be_documentary:{self.asset_id}")
        if self.synthetic and self.contains_real_person:
            raise ValueError(f"generated_real_person_forbidden:{self.asset_id}")


@dataclass(frozen=True)
class AssetPlan:
    video_id: str
    assets: tuple[AssetSpec, ...]

    def validate(self, beat_graphs: Sequence[NarrativeBeatGraph]) -> None:
        ids = [row.asset_id for row in self.assets]
        if len(ids) != len(set(ids)):
            raise ValueError("asset_ids_not_unique")
        for row in self.assets:
            row.validate()
        known = set(ids)
        used = {item for graph in beat_graphs for beat in graph.beats for item in beat.asset_ids}
        missing = sorted(used - known)
        if missing:
            raise ValueError("asset_plan_missing:" + ",".join(missing))


@dataclass(frozen=True)
class AudioPlan:
    video_id: str
    narrator_provider: str
    narrator_model: str
    narrator_voice: str
    narrator_license: str
    pronunciation_overrides: Mapping[str, str]
    prosody_by_variant: Mapping[str, Mapping[str, Any]]
    music: Mapping[str, Any]
    sfx_cues: tuple[Mapping[str, Any], ...]
    ducking: Mapping[str, Any]
    integrated_lufs_target: float
    true_peak_dbtp_max: float

    def validate(self, variant_ids: set[str], beat_ids: set[str]) -> None:
        if not self.narrator_provider or not self.narrator_model or not self.narrator_license:
            raise ValueError("audio_narrator_provenance_missing")
        if set(self.prosody_by_variant) != variant_ids:
            raise ValueError("audio_prosody_variant_coverage_missing")
        if str(self.music.get("rights_status") or "") not in ALLOWED_RIGHTS_STATUSES:
            raise ValueError("audio_music_rights_not_accepted")
        for cue in self.sfx_cues:
            if str(cue.get("beat_id") or "") not in beat_ids:
                raise ValueError(f"audio_sfx_unknown_beat:{cue.get('cue_id')}")
        if not -24 <= self.integrated_lufs_target <= -10:
            raise ValueError("audio_loudness_target_invalid")
        if self.true_peak_dbtp_max > -1:
            raise ValueError("audio_true_peak_target_unsafe")


@dataclass(frozen=True)
class PlatformVariant:
    variant_id: str
    platform: str
    aspect_ratio: str
    width: int
    height: int
    fps: int
    min_duration_seconds: float
    max_duration_seconds: float
    beat_ids: tuple[str, ...]
    caption_safe_zone: Mapping[str, float]
    caption_max_lines: int
    hook_copy: str

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0 or self.fps <= 0:
            raise ValueError(f"platform_variant_media_invalid:{self.variant_id}")
        if self.min_duration_seconds <= 0 or self.max_duration_seconds < self.min_duration_seconds:
            raise ValueError(f"platform_variant_duration_invalid:{self.variant_id}")
        if self.caption_max_lines > 2:
            raise ValueError(f"platform_variant_caption_lines_unsafe:{self.variant_id}")
        for key in ("top", "right", "bottom", "left"):
            value = float(self.caption_safe_zone.get(key, -1))
            if not 0 <= value < 0.5:
                raise ValueError(f"platform_variant_safe_zone_invalid:{self.variant_id}:{key}")


@dataclass(frozen=True)
class PlatformVariantPlan:
    video_id: str
    variants: tuple[PlatformVariant, ...]

    def validate(self, beat_graphs: Sequence[NarrativeBeatGraph]) -> None:
        graphs = {row.variant_id: row for row in beat_graphs}
        ids = [row.variant_id for row in self.variants]
        if len(ids) != len(set(ids)) or set(ids) != set(graphs):
            raise ValueError("platform_variant_graph_identity_mismatch")
        for row in self.variants:
            row.validate()
            if tuple(item.beat_id for item in graphs[row.variant_id].beats) != row.beat_ids:
                raise ValueError(f"platform_variant_beat_order_mismatch:{row.variant_id}")


@dataclass(frozen=True)
class RetentionDiagnostics:
    video_id: str
    variant_id: str
    duration_seconds: float
    hook_timing_seconds: float | None
    first_payoff_timing_seconds: float | None
    meaningful_visual_beat_intervals_seconds: tuple[float, ...]
    longest_static_primary_visual_run_seconds: float
    asset_classes: tuple[str, ...]
    caption_max_lines: int
    caption_safe_zone_status: str
    music_coverage_ratio: float
    sfx_coverage_ratio: float
    integrated_lufs: float | None
    true_peak_dbtp: float | None
    open_loop_payoff_status: str
    claim_evidence_coverage_ratio: float
    rights_coverage_ratio: float
    status: str
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class DirectorBundle:
    schema_version: str
    opportunity: VideoOpportunity
    engagement_brief: EngagementBrief
    beat_graphs: tuple[NarrativeBeatGraph, ...]
    edit_graphs: tuple[EditDecisionGraph, ...]
    asset_plan: AssetPlan
    audio_plan: AudioPlan
    platform_variant_plan: PlatformVariantPlan
    director_identity: Mapping[str, Any]
    public_write_authority: bool = False

    def validate(self) -> None:
        if self.schema_version != "contentops.retention_native.director_bundle.v2":
            raise ValueError("director_bundle_schema_unsupported")
        if self.public_write_authority:
            raise ValueError("director_bundle_public_write_forbidden")
        self.opportunity.validate()
        self.engagement_brief.validate()
        if self.opportunity.video_id != self.engagement_brief.video_id:
            raise ValueError("director_bundle_video_identity_mismatch")
        variants = {row.variant_id: row for row in self.beat_graphs}
        if len(variants) != len(self.beat_graphs):
            raise ValueError("director_bundle_duplicate_beat_graph_variant")
        for graph in self.beat_graphs:
            graph.validate()
        edits = {row.variant_id: row for row in self.edit_graphs}
        if set(edits) != set(variants):
            raise ValueError("director_bundle_edit_graph_coverage_missing")
        for variant_id, graph in variants.items():
            edits[variant_id].validate(graph)
        self.asset_plan.validate(self.beat_graphs)
        beat_ids = {beat.beat_id for graph in self.beat_graphs for beat in graph.beats}
        self.audio_plan.validate(set(variants), beat_ids)
        self.platform_variant_plan.validate(self.beat_graphs)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def director_bundle_from_dict(value: Mapping[str, Any]) -> DirectorBundle:
    opportunity = VideoOpportunity(
        **{**dict(value["opportunity"]), "story_mode": StoryMode(value["opportunity"]["story_mode"]), "selection_status": SelectionStatus(value["opportunity"]["selection_status"]), "evidence_hashes": tuple(value["opportunity"].get("evidence_hashes") or ()), "eligible_formats": tuple(value["opportunity"].get("eligible_formats") or ()), "selection_reasons": tuple(value["opportunity"].get("selection_reasons") or ())}
    )
    engagement = EngagementBrief(**{
        **dict(value["engagement_brief"]),
        "open_loops": tuple(value["engagement_brief"].get("open_loops") or ()),
        "payoff_checkpoints": tuple(value["engagement_brief"].get("payoff_checkpoints") or ()),
        "rehooks": tuple(value["engagement_brief"].get("rehooks") or ()),
        "pacing_map": tuple(value["engagement_brief"].get("pacing_map") or ()),
        "prohibited_overclaims": tuple(value["engagement_brief"].get("prohibited_overclaims") or ()),
    })
    beat_graphs = tuple(NarrativeBeatGraph(
        video_id=row["video_id"],
        variant_id=row["variant_id"],
        beats=tuple(NarrativeBeat(**{
            **dict(beat),
            "claim_ids": tuple(beat.get("claim_ids") or ()),
            "evidence_ids": tuple(beat.get("evidence_ids") or ()),
            "asset_ids": tuple(beat.get("asset_ids") or ()),
            "edit_decision_ids": tuple(beat.get("edit_decision_ids") or ()),
            "payoff_for": tuple(beat.get("payoff_for") or ()),
        }) for beat in row.get("beats") or ())
    ) for row in value.get("beat_graphs") or ())
    edit_graphs = tuple(EditDecisionGraph(
        video_id=row["video_id"],
        variant_id=row["variant_id"],
        decisions=tuple(EditDecision(**decision) for decision in row.get("decisions") or ()),
    ) for row in value.get("edit_graphs") or ())
    asset_plan = AssetPlan(
        video_id=value["asset_plan"]["video_id"],
        assets=tuple(AssetSpec(**{**dict(row), "beat_ids": tuple(row.get("beat_ids") or ())}) for row in value["asset_plan"].get("assets") or ()),
    )
    audio_plan = AudioPlan(**{
        **dict(value["audio_plan"]),
        "sfx_cues": tuple(value["audio_plan"].get("sfx_cues") or ()),
    })
    platform_plan = PlatformVariantPlan(
        video_id=value["platform_variant_plan"]["video_id"],
        variants=tuple(PlatformVariant(**{**dict(row), "beat_ids": tuple(row.get("beat_ids") or ())}) for row in value["platform_variant_plan"].get("variants") or ()),
    )
    bundle = DirectorBundle(
        schema_version=str(value["schema_version"]),
        opportunity=opportunity,
        engagement_brief=engagement,
        beat_graphs=beat_graphs,
        edit_graphs=edit_graphs,
        asset_plan=asset_plan,
        audio_plan=audio_plan,
        platform_variant_plan=platform_plan,
        director_identity=dict(value.get("director_identity") or {}),
        public_write_authority=bool(value.get("public_write_authority", False)),
    )
    bundle.validate()
    return bundle


def _require_id(name: str, value: str) -> None:
    if not value or any(character.isspace() for character in value):
        raise ValueError(f"contract_id_invalid:{name}")
