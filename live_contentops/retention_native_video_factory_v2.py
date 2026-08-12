"""Local, zero-public-write retention-native V2 video vertical slice.

The factory consumes a governed story package plus a renderer-neutral Director
source.  Director decisions control beats, edits, assets, captions, and audio
intent; Remotion and FFmpeg only compile those decisions into review media.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Sequence

from .content_intelligence_contracts_v2 import logical_hash
from .media_manifest_authority_v1 import sha256_file
from .retention_native_audio_score_v2 import SCORE_GENERATOR_VERSION, render_owned_score
from .nine_router_ordered_model_router_v2 import (
    MULTIMODAL_VIDEO_CRITIC_MODEL_POOL,
    MULTIMODAL_VIDEO_CRITIC_ROLE,
    SKIP_SAME_MODEL_RETRY_CLASSES,
    STRUCTURED_OUTPUT_CLASSES,
    is_fallback_eligible,
    is_retryable,
    is_terminal,
    retry_budget_for_role,
)
from .retention_native_video_critic_v2 import (
    CANONICAL_CRITIC_PROMPT,
    PROMPT_TEMPLATE as CRITIC_PROMPT_TEMPLATE,
    PROMPT_VERSION as CRITIC_PROMPT_VERSION,
    canonical_critic_repair_prompt,
    validate_critic_output,
)
from .retention_native_video_contracts_v2 import (
    AssetPlan,
    AssetSpec,
    AudioPlan,
    DirectorBundle,
    EditDecision,
    EditDecisionGraph,
    EngagementBrief,
    NarrativeBeat,
    NarrativeBeatGraph,
    PlatformVariant,
    PlatformVariantPlan,
    RetentionDiagnostics,
    SelectionStatus,
    StoryMode,
    VideoOpportunity,
    director_bundle_from_dict,
)


FACTORY_VERSION = "contentops.retention_native.factory.v2.1"
RENDERER_VERSION = "contentops.retention_native.remotion.v2.1"
RENDERER_COMPONENT_REVISIONS = {
    "KINETIC_TEXT": "contentops.retention_native.kinetic.v2.2",
    "PAYOFF_REVEAL": "contentops.retention_native.kinetic.v2.2",
    "CHART_TRACE": "contentops.retention_native.chart.v2.2",
    "POINT_ANNOTATION": "contentops.retention_native.chart.v2.2",
    "MECHANISM_FLOW": "contentops.retention_native.mechanism.v2.2",
}
RENDERER_SOURCE_FILES = (
    "package.json",
    "package-lock.json",
    "tsconfig.json",
    "scripts/render-batch.mjs",
    "src/index.ts",
    "src/root.tsx",
    "src/types.ts",
    "src/beat.tsx",
)
DEFAULT_STORY_INPUT = Path("docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/contentops_v1_0_rc_20260711_1")
DEFAULT_DIRECTOR_SOURCE = Path("video/retention_native_v2/proofs/eia_hormuz_v1/director_source_v1.json")
DEFAULT_RENDERER_ROOT = Path("video/retention_native_v2")
NASA_RIGHTS_URL = "https://www.nasa.gov/nasa-brand-center/images-and-media/"
EIA_RIGHTS_URL = "https://www.eia.gov/about/copyrights_reuse.php"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path.name}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _find_binary(name: str, env_key: str) -> str:
    configured = os.environ.get(env_key)
    if configured and Path(configured).is_file():
        return configured
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"{name}_not_found")
    return found


def _renderer_source_manifest(renderer_root: str | Path) -> dict[str, Any]:
    root = Path(renderer_root).resolve()
    files: list[dict[str, Any]] = []
    for relative in RENDERER_SOURCE_FILES:
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise RuntimeError(f"renderer_source_outside_root:{relative}") from exc
        if not path.is_file():
            raise RuntimeError(f"renderer_source_missing:{relative}")
        files.append({
            "path": relative.replace("\\", "/"),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
        })
    fingerprint = logical_hash({"renderer_version": RENDERER_VERSION, "files": files})
    return {
        "schema_version": "contentops.retention_native.renderer_source_manifest.v2",
        "status": "PASS",
        "renderer_root": str(root),
        "renderer_version": RENDERER_VERSION,
        "renderer_source_fingerprint": fingerprint,
        "files": files,
        "public_write": False,
    }


def _run(
    command: Sequence[str],
    *,
    timeout: int = 1800,
    capture: bool = False,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0x00004000)
    completed = subprocess.run(
        list(command),
        check=False,
        timeout=timeout,
        creationflags=flags,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "")[-1600:] if capture else ""
        raise RuntimeError(f"command_failed:{Path(command[0]).name}:{completed.returncode}:{message}")
    return completed


def _run_binary(command: Sequence[str], *, timeout: int = 1800) -> bytes:
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0x00004000)
    completed = subprocess.run(
        list(command),
        check=False,
        timeout=timeout,
        creationflags=flags,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        message = completed.stderr[-1600:].decode("utf-8", errors="replace")
        raise RuntimeError(f"command_failed:{Path(command[0]).name}:{completed.returncode}:{message}")
    return completed.stdout


def _probe(path: Path, ffprobe: str) -> dict[str, Any]:
    result = _run(
        [ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture=True,
        timeout=90,
    )
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise RuntimeError(f"ffprobe_object_required:{path.name}")
    return value


def _duration(path: Path, ffprobe: str) -> float:
    return float((_probe(path, ffprobe).get("format") or {}).get("duration") or 0.0)


def load_governed_oil_story(input_dir: str | Path) -> dict[str, Any]:
    """Read the existing governed package without mutating its historical evidence."""
    root = Path(input_dir).resolve()
    support_path = root / "grounded_support_v1.json"
    article_path = root / "article_manifest_v1.json"
    media_path = root / "media_manifest_v1.json"
    quality_path = root / "editorial_quality_gate_v1.json"
    support = _read_json(support_path)
    article = _read_json(article_path)
    media = _read_json(media_path)
    quality = _read_json(quality_path)
    blockers: list[str] = []
    packet = support.get("official_source_packet") or {}
    if not str(packet.get("status") or "").startswith("PASS_"):
        blockers.append("official_source_packet_not_pass")
    if support.get("support_status") != "GROUNDED_REPO_INPUTS_AND_SOURCE_BACKED_MEDIA":
        blockers.append("governed_support_status_not_pass")
    if media.get("media_gate_status") != "PASS" or media.get("blockers"):
        blockers.append("media_manifest_not_pass")
    if (quality.get("combined_gate") or {}).get("classification") != "PASS":
        blockers.append("editorial_quality_gate_not_pass")
    if article.get("financial_advice_detected") is not False:
        blockers.append("financial_advice_state_not_safe")
    if article.get("forbidden_secret_material_detected") is not False:
        blockers.append("forbidden_secret_state_not_safe")
    facts = packet.get("facts") or {}
    required_facts = {
        "release_date",
        "global_output_near_pre_conflict_by_year_end",
        "most_shut_in_output_restored_by",
        "brent_june_average_usd_per_barrel",
        "brent_q3_2026_forecast_usd_per_barrel",
        "brent_2027_forecast_usd_per_barrel",
        "gasoline_q3_2026_forecast_usd_per_gallon",
        "gasoline_q4_2026_forecast_usd_per_gallon",
    }
    missing_facts = sorted(required_facts - set(facts))
    if missing_facts:
        blockers.append("governed_facts_missing:" + ",".join(missing_facts))
    assets: list[dict[str, Any]] = []
    for row in media.get("assets") or []:
        source = (_repo_root_from_path(root) / str(row.get("path") or "")).resolve()
        if not source.is_file():
            blockers.append(f"governed_asset_missing:{row.get('asset_id')}")
            continue
        actual = sha256_file(source)
        if actual != str(row.get("sha256") or ""):
            blockers.append(f"governed_asset_hash_mismatch:{row.get('asset_id')}")
        assets.append({**dict(row), "resolved_path": str(source), "sha256": actual})
    if blockers:
        raise RuntimeError("governed_story_blocked:" + ";".join(blockers))

    article_body = str(article.get("rendered_body") or "")
    claim_values = {
        "eia:release_date": facts["release_date"],
        "eia:hormuz_traffic_mou": "EIA reported increased Hormuz traffic following the June 18 U.S.-Iran memorandum.",
        "eia:pre_conflict_year_end": bool(facts["global_output_near_pre_conflict_by_year_end"]),
        "eia:shut_in_2027_q1": facts["most_shut_in_output_restored_by"],
        "eia:brent_june_85": float(facts["brent_june_average_usd_per_barrel"]),
        "eia:brent_q3_74": float(facts["brent_q3_2026_forecast_usd_per_barrel"]),
        "eia:brent_2027_65": float(facts["brent_2027_forecast_usd_per_barrel"]),
        "eia:gasoline_q3_3_80": float(facts["gasoline_q3_2026_forecast_usd_per_gallon"]),
        "eia:gasoline_q4_3_40": float(facts["gasoline_q4_2026_forecast_usd_per_gallon"]),
        "eia:gasoline_forecast": "EIA Q3/Q4 2026 gasoline forecast",
        "eia:forecast_boundary": "EIA values after the release date are forecasts, not certainties.",
        "eia:inventory_builds": "EIA expects continued inventory builds to pressure crude prices lower.",
        "eia:named_catalysts": [facts.get("next_weekly_petroleum_status_report_date"), facts.get("next_steo_release_date")],
        "fred:wti_2026_07_06_69_60": float(next(row["latest_observation_value"] for row in assets if row["asset_id"] == "primary")),
        "article:mechanism": article.get("market_mechanism"),
        "article:price_not_proof": "The manifest-bound WTI observation does not prove the EIA forecast.",
        "article:policy_boundary": article.get("policy_context"),
        "article:cross_asset_implications": article.get("cross_asset_implications"),
        "article:historical_context": "A forecast decline can still leave oil above prior-cycle averages.",
        "article:confirmation_conditions": _sentence_containing(article_body, "Confirmation would come"),
        "article:challenge_conditions": _sentence_containing(article_body, "The thesis would be challenged"),
        "article:evidence_boundary": "The governed package distinguishes forecasts, observations, implications, and non-advice boundaries.",
    }
    evidence = {
        "eia-release-press590": {
            "source_url": packet["source_url"],
            "source_title": packet["source_title"],
            "sha256": packet["source_text_sha256"],
            "retrieved_at": packet.get("retrieved_at"),
        },
        "fred-dcoilwtico-manifest": {
            "source_url": "https://fred.stlouisfed.org/series/DCOILWTICO",
            "sha256": sha256_file(media_path),
            "asset_hashes": [row["sha256"] for row in assets],
        },
        "governed-article": {
            "source_url": article.get("canonical_url"),
            "sha256": article.get("article_markdown_sha256"),
            "manifest_sha256": sha256_file(article_path),
        },
        "fomc-june-statement": {
            "source_url": "https://www.federalreserve.gov/newsevents/pressreleases/monetary20260617a.htm",
            "governed_source_trail_manifest_sha256": sha256_file(article_path),
        },
    }
    return {
        "input_root": str(root),
        "story_id": article["slug"],
        "story_version": article["created_at"],
        "title": article["title"],
        "article_hash": article["article_markdown_sha256"],
        "official_source_hash": packet["source_text_sha256"],
        "claims": {key: {"claim_id": key, "value": value} for key, value in claim_values.items()},
        "evidence": evidence,
        "media_assets": assets,
        "source_trail": article.get("source_trail") or [],
        "historical_governed_package": True,
        "public_write_authority": False,
    }


def _sentence_containing(text: str, marker: str) -> str:
    for sentence in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")):
        if marker.lower() in sentence.lower():
            return sentence.strip()
    raise RuntimeError(f"governed_article_sentence_missing:{marker}")


def _repo_root_from_path(path: Path) -> Path:
    for candidate in (path, *path.parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / "live_contentops").is_dir():
            return candidate
    raise RuntimeError("contentops_repo_root_not_found")


def build_director_bundle(source: Mapping[str, Any], story: Mapping[str, Any]) -> DirectorBundle:
    if source.get("schema_version") != "contentops.retention_native.director_source.v1":
        raise ValueError("director_source_schema_unsupported")
    opportunity_value = source["opportunity"]
    opportunity = VideoOpportunity(
        video_id=opportunity_value["video_id"],
        story_id=opportunity_value["story_id"],
        story_version=opportunity_value["story_version"],
        title=opportunity_value["title"],
        story_mode=StoryMode(opportunity_value["story_mode"]),
        selection_status=SelectionStatus(opportunity_value["selection_status"]),
        evidence_hashes=tuple(opportunity_value.get("evidence_hashes") or ()),
        eligible_formats=tuple(opportunity_value.get("eligible_formats") or ()),
        scores=dict(opportunity_value.get("scores") or {}),
        selection_reasons=tuple(opportunity_value.get("selection_reasons") or ()),
        estimated_production_cost=opportunity_value["estimated_production_cost"],
        public_write_authority=False,
        test_only_non_public=bool(opportunity_value.get("test_only_non_public", False)),
    )
    if opportunity.story_id != story["story_id"] or opportunity.story_version != story["story_version"]:
        raise ValueError("director_story_identity_does_not_match_governed_package")
    brief_value = source["engagement_brief"]
    brief = EngagementBrief(
        video_id=brief_value["video_id"],
        target_audience=brief_value["target_audience"],
        viewer_question=brief_value["viewer_question"],
        why_now=brief_value["why_now"],
        core_promise=brief_value["core_promise"],
        hook=brief_value["hook"],
        pattern_interrupt=brief_value["pattern_interrupt"],
        central_tension=brief_value["central_tension"],
        open_loops=tuple(brief_value.get("open_loops") or ()),
        payoff_checkpoints=tuple(brief_value.get("payoff_checkpoints") or ()),
        rehooks=tuple(brief_value.get("rehooks") or ()),
        pacing_map=tuple(brief_value.get("pacing_map") or ()),
        emotional_register=brief_value["emotional_register"],
        prohibited_overclaims=tuple(brief_value.get("prohibited_overclaims") or ()),
        cta=brief_value["cta"],
        binge_target=brief_value["binge_target"],
        platform_hooks=dict(brief_value.get("platform_hooks") or {}),
    )
    beat_graphs: list[NarrativeBeatGraph] = []
    edit_graphs: list[EditDecisionGraph] = []
    platform_variants: list[PlatformVariant] = []
    asset_usage: dict[str, list[str]] = {}
    for variant_value in source.get("variants") or []:
        beats: list[NarrativeBeat] = []
        decisions: list[EditDecision] = []
        for order, beat_value in enumerate(variant_value.get("beats") or []):
            decision_ids: list[str] = []
            for index, edit_value in enumerate(beat_value.get("edits") or (), 1):
                decision_id = f"{beat_value['beat_id']}-d{index:02d}"
                decision_ids.append(decision_id)
                decisions.append(EditDecision(
                    decision_id=decision_id,
                    beat_id=beat_value["beat_id"],
                    at_seconds=float(edit_value.get("at_seconds", 0)),
                    operation=edit_value["operation"],
                    asset_id=edit_value.get("asset_id"),
                    narrative_purpose=edit_value["narrative_purpose"],
                    primary_visual_change=bool(edit_value.get("primary_visual_change", True)),
                    parameters=dict(edit_value.get("parameters") or {}),
                ))
            asset_ids = tuple(beat_value.get("asset_ids") or ())
            for asset_id in asset_ids:
                asset_usage.setdefault(asset_id, []).append(beat_value["beat_id"])
            beats.append(NarrativeBeat(
                beat_id=beat_value["beat_id"],
                scene_id=beat_value["scene_id"],
                chapter_id=beat_value["chapter_id"],
                variant_id=variant_value["variant_id"],
                order=order,
                narrative_role=beat_value["narrative_role"],
                narration_text=beat_value["narration_text"],
                claim_ids=tuple(beat_value.get("claim_ids") or ()),
                evidence_ids=tuple(beat_value.get("evidence_ids") or ()),
                viewer_takeaway=beat_value["viewer_takeaway"],
                visual_purpose=beat_value["visual_purpose"],
                asset_ids=asset_ids,
                edit_decision_ids=tuple(decision_ids),
                audio_state=beat_value["audio_state"],
                transition_intent=beat_value["transition_intent"],
                target_duration_seconds=float(beat_value["target_duration_seconds"]),
                open_loop_id=beat_value.get("open_loop_id"),
                payoff_for=tuple(beat_value.get("payoff_for") or ()),
            ))
        graph = NarrativeBeatGraph(video_id=opportunity.video_id, variant_id=variant_value["variant_id"], beats=tuple(beats))
        beat_graphs.append(graph)
        edit_graphs.append(EditDecisionGraph(video_id=opportunity.video_id, variant_id=variant_value["variant_id"], decisions=tuple(decisions)))
        platform_variants.append(PlatformVariant(
            variant_id=variant_value["variant_id"],
            platform=variant_value["platform"],
            aspect_ratio=variant_value["aspect_ratio"],
            width=int(variant_value["width"]),
            height=int(variant_value["height"]),
            fps=int(variant_value["fps"]),
            min_duration_seconds=float(variant_value["min_duration_seconds"]),
            max_duration_seconds=float(variant_value["max_duration_seconds"]),
            beat_ids=tuple(row.beat_id for row in beats),
            caption_safe_zone=dict(variant_value["caption_safe_zone"]),
            caption_max_lines=int(variant_value["caption_max_lines"]),
            hook_copy=variant_value["hook_copy"],
        ))
    assets = tuple(AssetSpec(
        asset_id=row["asset_id"],
        asset_class=row["asset_class"],
        editorial_purpose=row["editorial_purpose"],
        source_label=row["source_label"],
        source_url=row["source_url"],
        rights_status=row["rights_status"],
        license_or_terms=row["license_or_terms"],
        attribution=row["attribution"],
        sha256=row.get("sha256"),
        source_path=row.get("source_path"),
        beat_ids=tuple(asset_usage.get(row["asset_id"], ())),
        synthetic=bool(row.get("synthetic", False)),
        documentary=bool(row.get("documentary", True)),
        contains_real_person=bool(row.get("contains_real_person", False)),
    ) for row in source["asset_plan"].get("assets") or ())
    audio_value = source["audio_plan"]
    audio = AudioPlan(
        video_id=audio_value["video_id"],
        narrator_provider=audio_value["narrator_provider"],
        narrator_model=audio_value["narrator_model"],
        narrator_voice=audio_value["narrator_voice"],
        narrator_license=audio_value["narrator_license"],
        pronunciation_overrides=dict(audio_value.get("pronunciation_overrides") or {}),
        prosody_by_variant=dict(audio_value.get("prosody_by_variant") or {}),
        music=dict(audio_value.get("music") or {}),
        sfx_cues=tuple(audio_value.get("sfx_cues") or ()),
        ducking=dict(audio_value.get("ducking") or {}),
        integrated_lufs_target=float(audio_value["integrated_lufs_target"]),
        true_peak_dbtp_max=float(audio_value["true_peak_dbtp_max"]),
    )
    bundle = DirectorBundle(
        schema_version="contentops.retention_native.director_bundle.v2",
        opportunity=opportunity,
        engagement_brief=brief,
        beat_graphs=tuple(beat_graphs),
        edit_graphs=tuple(edit_graphs),
        asset_plan=AssetPlan(video_id=opportunity.video_id, assets=assets),
        audio_plan=audio,
        platform_variant_plan=PlatformVariantPlan(video_id=opportunity.video_id, variants=tuple(platform_variants)),
        director_identity=dict(source.get("director_identity") or {}),
        public_write_authority=False,
    )
    bundle.validate()
    _validate_story_bindings(bundle, story)
    return bundle


def _validate_story_bindings(bundle: DirectorBundle, story: Mapping[str, Any]) -> None:
    known_claims = set(story["claims"])
    known_evidence = set(story["evidence"])
    missing_claims = sorted({item for graph in bundle.beat_graphs for beat in graph.beats for item in beat.claim_ids} - known_claims)
    missing_evidence = sorted({item for graph in bundle.beat_graphs for beat in graph.beats for item in beat.evidence_ids} - known_evidence)
    if missing_claims:
        raise ValueError("director_claims_not_governed:" + ",".join(missing_claims))
    if missing_evidence:
        raise ValueError("director_evidence_not_governed:" + ",".join(missing_evidence))


def hydrate_assets(
    bundle: DirectorBundle,
    *,
    repo_root: Path,
    public_dir: Path,
    source_cache: Path,
    governed_evidence: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], int]:
    repo_root = repo_root.resolve()
    public_assets = public_dir / "assets"
    public_assets.mkdir(parents=True, exist_ok=True)
    source_cache.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    network_calls = 0
    for asset in bundle.asset_plan.assets:
        source: Path | None = None
        if asset.source_path:
            relative_source = Path(asset.source_path)
            if relative_source.is_absolute():
                raise RuntimeError(f"asset_source_path_must_be_relative:{asset.asset_id}")
            source = (repo_root / relative_source).resolve()
            try:
                source.relative_to(repo_root)
            except ValueError as exc:
                raise RuntimeError(f"asset_source_outside_repository:{asset.asset_id}") from exc
            if not source.is_file():
                raise RuntimeError(f"asset_source_missing:{asset.asset_id}")
        elif asset.asset_id == "nasa-persian-gulf-iss069-e-92132":
            source = source_cache / "ISS069-E-92132.JPG"
            retrieval_sidecar = source_cache / "ISS069-E-92132.retrieval.json"
            source_exists = source.is_file()
            sidecar_exists = retrieval_sidecar.is_file()
            if source_exists != sidecar_exists:
                raise RuntimeError("nasa_asset_cache_partial_state")
            if not source_exists:
                if not str(asset.source_url or "").startswith("https://eol.jsc.nasa.gov/"):
                    raise RuntimeError("nasa_asset_source_url_not_authorized")
                request = urllib.request.Request(asset.source_url, headers={"User-Agent": "CapitalChronicleContentOps/2.0 editorial-media-proof"})
                with urllib.request.urlopen(request, timeout=90) as response:
                    payload = response.read(20_000_000)
                if not payload.startswith(b"\xff\xd8"):
                    raise RuntimeError("nasa_asset_not_jpeg")
                source.write_bytes(payload)
                network_calls += 1
                _write_json(retrieval_sidecar, {
                    "schema_version": "contentops.retention_native.asset_retrieval_receipt.v2",
                    "asset_id": asset.asset_id,
                    "source_url": asset.source_url,
                    "retrieved_at": _now(),
                    "sha256": sha256_file(source),
                    "network_calls": 1,
                    "public_write": False,
                    "browser_profile_used": False,
                })
            receipt = _read_json(retrieval_sidecar)
            cached_hash = sha256_file(source)
            with source.open("rb") as cached_file:
                cached_header = cached_file.read(2)
            if (
                receipt.get("schema_version") != "contentops.retention_native.asset_retrieval_receipt.v2"
                or receipt.get("asset_id") != asset.asset_id
                or receipt.get("source_url") != asset.source_url
                or receipt.get("sha256") != cached_hash
                or cached_header != b"\xff\xd8"
            ):
                raise RuntimeError("nasa_asset_cache_receipt_invalid")
        render_identity_hash = logical_hash({"asset": asdict(asset), "renderer": RENDERER_VERSION})
        verification_method: str
        governed_evidence_id: str | None = None
        if source is not None:
            actual_hash = sha256_file(source)
            verification_method = "hydrated_source_bytes_sha256"
        elif asset.documentary:
            if not asset.sha256 or not governed_evidence:
                raise RuntimeError(f"documentary_asset_governed_hash_binding_missing:{asset.asset_id}")
            for evidence_id, evidence in governed_evidence.items():
                if (
                    evidence.get("source_url") == asset.source_url
                    and evidence.get("sha256") == asset.sha256
                ):
                    governed_evidence_id = str(evidence_id)
                    break
            if governed_evidence_id is None:
                raise RuntimeError(f"documentary_asset_governed_hash_binding_invalid:{asset.asset_id}")
            actual_hash = asset.sha256
            verification_method = "governed_evidence_source_hash_binding"
        else:
            actual_hash = render_identity_hash
            verification_method = "deterministic_renderer_identity_hash"
        if source and asset.sha256 and actual_hash != asset.sha256:
            raise RuntimeError(f"asset_hash_mismatch:{asset.asset_id}")
        relative_public_path: str | None = None
        hydrated_path: str | None = None
        if source:
            suffix = source.suffix.lower() or ".bin"
            target = public_assets / f"{asset.asset_id}{suffix}"
            if not target.is_file() or sha256_file(target) != actual_hash:
                shutil.copy2(source, target)
            relative_public_path = f"assets/{target.name}"
            hydrated_path = str(target)
        row = {
            **asdict(asset),
            "sha256": actual_hash,
            "render_identity_sha256": render_identity_hash,
            "hydrated_path": hydrated_path,
            "relative_public_path": relative_public_path,
            "hash_verified": True,
            "hash_verification_method": verification_method,
            "governed_evidence_id": governed_evidence_id,
            "rights_reference_url": NASA_RIGHTS_URL if asset.rights_status == "NASA_MEDIA_GUIDELINES_EDITORIAL" else EIA_RIGHTS_URL if "GOVERNMENT" in asset.rights_status else None,
        }
        rows.append(row)
    return rows, {row["asset_id"]: row for row in rows}, network_calls


def _apply_pronunciation_overrides(text: str, overrides: Mapping[str, str]) -> str:
    rendered = text
    for source, replacement in sorted(overrides.items(), key=lambda row: -len(row[0])):
        rendered = re.sub(rf"\b{re.escape(source)}\b", replacement, rendered)
    return rendered


def _audio_cache_attestation_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".cache-attestation.json")


def _audio_stream_metadata(
    path: Path,
    *,
    ffprobe: str,
    expected_sample_rate: int,
    expected_channels: int,
    expected_duration_seconds: float | None = None,
) -> dict[str, Any]:
    probe = _probe(path, ffprobe)
    audio = next((row for row in probe.get("streams") or () if row.get("codec_type") == "audio"), None)
    if not isinstance(audio, Mapping):
        raise RuntimeError(f"audio_cache_stream_missing:{path.name}")
    sample_rate = int(audio.get("sample_rate") or 0)
    channels = int(audio.get("channels") or 0)
    duration = float((probe.get("format") or {}).get("duration") or 0.0)
    if sample_rate != expected_sample_rate or channels != expected_channels or duration <= 0:
        raise RuntimeError(f"audio_cache_media_mismatch:{path.name}")
    if expected_duration_seconds is not None and abs(duration - expected_duration_seconds) > 0.08:
        raise RuntimeError(f"audio_cache_duration_mismatch:{path.name}:{duration}:{expected_duration_seconds}")
    return {
        "duration_seconds": round(duration, 6),
        "sample_rate": sample_rate,
        "channels": channels,
        "codec_name": audio.get("codec_name"),
    }


def _write_audio_cache_attestation(
    path: Path,
    *,
    kind: str,
    cache_key: str,
    binding: Mapping[str, Any],
    ffprobe: str,
    expected_sample_rate: int,
    expected_channels: int,
    expected_duration_seconds: float | None = None,
) -> dict[str, Any]:
    media = _audio_stream_metadata(
        path,
        ffprobe=ffprobe,
        expected_sample_rate=expected_sample_rate,
        expected_channels=expected_channels,
        expected_duration_seconds=expected_duration_seconds,
    )
    attestation = {
        "schema_version": "contentops.retention_native.audio_cache_attestation.v2",
        "kind": kind,
        "cache_key": cache_key,
        "binding_sha256": logical_hash(dict(binding)),
        "output_path": str(path),
        "output_sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        **media,
        "network_calls": 0,
        "public_write": False,
    }
    _write_json(_audio_cache_attestation_path(path), attestation)
    return attestation


def _validated_audio_cache_hit(
    path: Path,
    *,
    kind: str,
    cache_key: str,
    binding: Mapping[str, Any],
    ffprobe: str,
    expected_sample_rate: int,
    expected_channels: int,
    expected_duration_seconds: float | None = None,
) -> dict[str, Any] | None:
    attestation_path = _audio_cache_attestation_path(path)
    if not path.is_file() or not attestation_path.is_file():
        return None
    try:
        attestation = _read_json(attestation_path)
        expected = {
            "schema_version": "contentops.retention_native.audio_cache_attestation.v2",
            "kind": kind,
            "cache_key": cache_key,
            "binding_sha256": logical_hash(dict(binding)),
            "output_path": str(path),
        }
        if any(attestation.get(key) != value for key, value in expected.items()):
            return None
        if int(attestation.get("size_bytes") or 0) != path.stat().st_size:
            return None
        if attestation.get("output_sha256") != sha256_file(path):
            return None
        _audio_stream_metadata(
            path,
            ffprobe=ffprobe,
            expected_sample_rate=expected_sample_rate,
            expected_channels=expected_channels,
            expected_duration_seconds=expected_duration_seconds,
        )
        return attestation
    except (OSError, TypeError, ValueError, RuntimeError):
        return None


def generate_narration(
    bundle: DirectorBundle,
    *,
    output_root: Path,
    repo_root: Path,
    tts_python: str,
    ffprobe: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Render each factual beat once through the isolated local Kokoro worker."""
    cache_dir = output_root / "render_cache" / "narration"
    cache_dir.mkdir(parents=True, exist_ok=True)
    segments: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    variants = {row.variant_id: row for row in bundle.platform_variant_plan.variants}
    for graph in bundle.beat_graphs:
        speed = float(bundle.audio_plan.prosody_by_variant[graph.variant_id].get("speed") or 1.0)
        variant = variants[graph.variant_id]
        for beat in graph.beats:
            spoken_text = _apply_pronunciation_overrides(
                beat.narration_text,
                bundle.audio_plan.pronunciation_overrides,
            )
            cache_binding = {
                "provider": bundle.audio_plan.narrator_provider,
                "model": bundle.audio_plan.narrator_model,
                "voice": bundle.audio_plan.narrator_voice,
                "speed": speed,
                "text": spoken_text,
                "worker": "live_contentops.video_tts_worker_v1",
            }
            cache_key = logical_hash(cache_binding)
            path = cache_dir / f"{cache_key}.wav"
            cache_attestation = _validated_audio_cache_hit(
                path,
                kind="kokoro_narration_segment",
                cache_key=cache_key,
                binding=cache_binding,
                ffprobe=ffprobe,
                expected_sample_rate=24000,
                expected_channels=1,
            )
            row = {
                "beat_id": beat.beat_id,
                "variant_id": graph.variant_id,
                "narration_text": beat.narration_text,
                "spoken_text": spoken_text,
                "voice": bundle.audio_plan.narrator_voice,
                "speed": speed,
                "cache_key": cache_key,
                "path": str(path),
                "cache_hit": cache_attestation is not None,
                "cache_binding": cache_binding,
                "fps": variant.fps,
                "target_duration_seconds": beat.target_duration_seconds,
            }
            segments.append(row)
            by_id[beat.beat_id] = row
    missing = [row for row in segments if not row["cache_hit"]]
    worker_telemetry: dict[str, Any] = {
        "provider": bundle.audio_plan.narrator_provider,
        "model": bundle.audio_plan.narrator_model,
        "segment_count": len(segments),
        "generated_segment_count": 0,
        "network_call_performed": False,
        "public_write_performed": False,
    }
    if missing:
        request_path = output_root / "contracts" / "kokoro_batch_request_v2.json"
        _write_json(request_path, {
            "schema_version": "contentops.retention_native.kokoro_batch_request.v2",
            "segments": [
                {
                    "beat_id": row["beat_id"],
                    "text": row["spoken_text"],
                    "voice": row["voice"],
                    "speed": row["speed"],
                    "output_path": row["path"],
                }
                for row in missing
            ],
        })
        started = time.perf_counter()
        completed = _run(
            [tts_python, "-m", "live_contentops.video_tts_worker_v1", "--batch-request", str(request_path)],
            cwd=repo_root,
            capture=True,
            timeout=5400,
        )
        response_lines = [line for line in completed.stdout.splitlines() if line.strip().startswith("{")]
        response = json.loads(response_lines[-1]) if response_lines else {}
        worker_telemetry = {
            **worker_telemetry,
            **response,
            "generated_segment_count": len(missing),
            "wall_seconds": round(time.perf_counter() - started, 3),
        }
    for row in segments:
        path = Path(row["path"])
        if not path.is_file():
            raise RuntimeError(f"narration_missing_after_generation:{row['beat_id']}")
        cache_attestation = _validated_audio_cache_hit(
            path,
            kind="kokoro_narration_segment",
            cache_key=str(row["cache_key"]),
            binding=dict(row["cache_binding"]),
            ffprobe=ffprobe,
            expected_sample_rate=24000,
            expected_channels=1,
        )
        if cache_attestation is None:
            cache_attestation = _write_audio_cache_attestation(
                path,
                kind="kokoro_narration_segment",
                cache_key=str(row["cache_key"]),
                binding=dict(row["cache_binding"]),
                ffprobe=ffprobe,
                expected_sample_rate=24000,
                expected_channels=1,
            )
        audio_seconds = _duration(path, ffprobe)
        pause = float(bundle.audio_plan.prosody_by_variant[row["variant_id"]].get("pause_after_payoff_seconds") or 0.18)
        duration_seconds = max(float(row["target_duration_seconds"]), audio_seconds + pause)
        duration_frames = int(math.ceil(duration_seconds * int(row["fps"])))
        row.update({
            "audio_duration_seconds": round(audio_seconds, 6),
            "duration_in_frames": duration_frames,
            "duration_seconds": round(duration_frames / int(row["fps"]), 6),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "cache_attestation_path": str(_audio_cache_attestation_path(path)),
            "cache_attestation_sha256": sha256_file(_audio_cache_attestation_path(path)),
            "network_calls": 0,
            "provider_calls": 0,
            "local_model_inference": True,
            "local_model_inference_this_run": not bool(row["cache_hit"]),
        })
    worker_telemetry.update({
        "schema_version": "contentops.retention_native.narration_receipt.v2",
        "status": "PASS",
        "voice": bundle.audio_plan.narrator_voice,
        "license": bundle.audio_plan.narrator_license,
        "segment_count": len(segments),
        "local_inference_segment_count": len(segments),
        "local_inference_segment_count_this_run": len(missing),
        "cache_hit_segment_count_this_run": len(segments) - len(missing),
        "network_calls": 0,
        "provider_calls": 0,
        "public_write": False,
    })
    return by_id, worker_telemetry


def _caption_lines(words: Sequence[str], max_chars: int) -> list[str]:
    if not words:
        return []
    text = " ".join(words)
    if len(text) <= max_chars:
        return [text]
    best: tuple[int, list[str]] | None = None
    for split in range(1, len(words)):
        candidate = [" ".join(words[:split]), " ".join(words[split:])]
        overflow = max(len(candidate[0]), len(candidate[1]))
        if overflow <= max_chars:
            balance = abs(len(candidate[0]) - len(candidate[1]))
            if best is None or balance < best[0]:
                best = (balance, candidate)
    if best:
        return best[1]
    midpoint = max(1, len(words) // 2)
    return [" ".join(words[:midpoint]), " ".join(words[midpoint:])]


def _caption_cues(text: str, *, duration_frames: int, fps: int, portrait: bool) -> list[dict[str, Any]]:
    words = text.split()
    if not words:
        return []
    max_words = 5 if portrait else 8
    max_chars = 25 if portrait else 42
    chunks: list[list[str]] = []
    cursor = 0
    while cursor < len(words):
        take = min(max_words, len(words) - cursor)
        while take > 2 and max(len(line) for line in _caption_lines(words[cursor:cursor + take], max_chars)) > max_chars:
            take -= 1
        chunks.append(words[cursor:cursor + take])
        cursor += take
    narration_end = max(1, duration_frames - max(3, int(0.12 * fps)))
    total_words = sum(len(row) for row in chunks)
    consumed = 0
    cues: list[dict[str, Any]] = []
    for index, chunk in enumerate(chunks):
        start = int(round(narration_end * consumed / total_words))
        consumed += len(chunk)
        end = int(round(narration_end * consumed / total_words)) if index < len(chunks) - 1 else narration_end
        cues.append({
            "start_frame": start,
            "end_frame": max(start + 1, end),
            "lines": _caption_lines(chunk, max_chars)[:2],
        })
    return cues


def _compile_jobs(
    bundle: DirectorBundle,
    *,
    narration: Mapping[str, Mapping[str, Any]],
    assets: Mapping[str, Mapping[str, Any]],
    output_root: Path,
    renderer_source_fingerprint: str | None = None,
    captions_visible: bool = True,
    proxy: bool = False,
    selected_beat_ids: set[str] | None = None,
    edit_overrides: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    if renderer_source_fingerprint is None:
        renderer_source_fingerprint = str(
            _renderer_source_manifest(DEFAULT_RENDERER_ROOT)["renderer_source_fingerprint"]
        )
    if not re.fullmatch(r"[0-9a-f]{64}", renderer_source_fingerprint):
        raise RuntimeError("renderer_source_fingerprint_invalid")
    edits_by_variant = {row.variant_id: row for row in bundle.edit_graphs}
    variants = {row.variant_id: row for row in bundle.platform_variant_plan.variants}
    compiled: dict[str, list[dict[str, Any]]] = {}
    for graph in bundle.beat_graphs:
        variant = variants[graph.variant_id]
        portrait = variant.height > variant.width
        rows: list[dict[str, Any]] = []
        decisions_by_beat: dict[str, list[EditDecision]] = {}
        for decision in edits_by_variant[graph.variant_id].decisions:
            decisions_by_beat.setdefault(decision.beat_id, []).append(decision)
        for beat in graph.beats:
            if selected_beat_ids is not None and beat.beat_id not in selected_beat_ids:
                continue
            audio = narration[beat.beat_id]
            width = variant.width // 2 if proxy else variant.width
            height = variant.height // 2 if proxy else variant.height
            states: list[dict[str, Any]] = []
            for decision in sorted(decisions_by_beat[beat.beat_id], key=lambda row: (row.at_seconds, row.decision_id)):
                asset_id = decision.asset_id or beat.asset_ids[0]
                asset = assets.get(asset_id)
                parameters = dict(decision.parameters)
                if edit_overrides and decision.decision_id in edit_overrides:
                    parameters.update(dict(edit_overrides[decision.decision_id]))
                at_frame = int(round(decision.at_seconds * variant.fps))
                if at_frame >= int(audio["duration_in_frames"]):
                    raise RuntimeError(f"edit_after_beat_end:{decision.decision_id}")
                states.append({
                    "decision_id": decision.decision_id,
                    "at_frame": at_frame,
                    "operation": decision.operation,
                    "asset_id": asset_id,
                    "asset_class": asset.get("asset_class") if asset else None,
                    "asset_path": asset.get("relative_public_path") if asset else None,
                    "attribution": asset.get("attribution") if asset else None,
                    "primary_visual_change": decision.primary_visual_change,
                    "narrative_purpose": decision.narrative_purpose,
                    "parameters": parameters,
                })
            job_core = {
                "video_id": bundle.opportunity.video_id,
                "beat_id": beat.beat_id,
                "scene_id": beat.scene_id,
                "chapter_id": beat.chapter_id,
                "variant_id": graph.variant_id,
                "narrative_role": beat.narrative_role,
                "viewer_takeaway": beat.viewer_takeaway,
                "visual_purpose": beat.visual_purpose,
                "narration_text": beat.narration_text,
                "source_label": "Sources: EIA, FRED, and the governed Capital Chronicle story package",
                "duration_in_frames": int(audio["duration_in_frames"]),
                "fps": variant.fps,
                "width": width,
                "height": height,
                "captions_visible": captions_visible,
                "caption_safe_zone": dict(variant.caption_safe_zone),
                "caption_layout": {
                    "left": max(float(variant.caption_safe_zone["left"]), 0.07 if portrait else 0.14),
                    "right": max(float(variant.caption_safe_zone["right"]), 0.07 if portrait else 0.14),
                    "bottom": float(variant.caption_safe_zone["bottom"]) + (0.005 if portrait else 0.0),
                    "estimated_max_height_px": 154 if portrait else 110,
                },
                "proxy": proxy,
                "caption_cues": _caption_cues(
                    beat.narration_text,
                    duration_frames=int(audio["duration_in_frames"]),
                    fps=variant.fps,
                    portrait=portrait,
                ) if captions_visible else [],
                "edit_states": states,
                "narration_sha256": audio["sha256"],
                "asset_hashes": {asset_id: assets[asset_id]["sha256"] for asset_id in beat.asset_ids},
                "renderer_version": RENDERER_VERSION,
                "renderer_source_fingerprint": renderer_source_fingerprint,
            }
            component_revisions = {
                operation: RENDERER_COMPONENT_REVISIONS[operation]
                for operation in sorted({state["operation"] for state in states})
                if operation in RENDERER_COMPONENT_REVISIONS
            }
            if component_revisions:
                job_core["renderer_component_revisions"] = component_revisions
            cache_key = logical_hash(job_core)
            family = "review_proxy" if proxy else "beats"
            output = output_root / "render_cache" / family / graph.variant_id / f"{beat.beat_id}-{cache_key[:20]}.mp4"
            job = {**job_core, "cache_key": cache_key, "output_path": str(output)}
            rows.append(job)
        compiled[graph.variant_id] = rows
    return compiled


def _render_cache_attestation_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".cache-attestation.json")


def _measured_video_frame_rate(video: Mapping[str, Any], *, label: str) -> float:
    values: list[float] = []
    for key in ("avg_frame_rate", "r_frame_rate"):
        raw = str(video.get(key) or "")
        if not raw or raw in {"0/0", "N/A"}:
            raise RuntimeError(f"video_frame_rate_missing:{label}:{key}")
        try:
            value = float(Fraction(raw))
        except (ValueError, ZeroDivisionError) as exc:
            raise RuntimeError(f"video_frame_rate_invalid:{label}:{key}:{raw}") from exc
        if not math.isfinite(value) or value <= 0:
            raise RuntimeError(f"video_frame_rate_invalid:{label}:{key}:{raw}")
        values.append(value)
    if max(values) - min(values) > 0.001:
        raise RuntimeError(f"video_frame_rate_fields_disagree:{label}")
    return values[0]


def _validate_render_media(path: Path, job: Mapping[str, Any], ffprobe: str) -> dict[str, Any]:
    probe = _probe(path, ffprobe)
    video = next((row for row in probe.get("streams") or () if row.get("codec_type") == "video"), None)
    if not isinstance(video, Mapping):
        raise RuntimeError(f"render_cache_video_stream_missing:{job['beat_id']}")
    if int(video.get("width") or 0) != int(job["width"]) or int(video.get("height") or 0) != int(job["height"]):
        raise RuntimeError(f"render_cache_dimensions_mismatch:{job['beat_id']}")
    duration = float((probe.get("format") or {}).get("duration") or 0.0)
    expected = int(job["duration_in_frames"]) / float(job["fps"])
    if abs(duration - expected) > max(0.12, 2.0 / float(job["fps"])):
        raise RuntimeError(f"render_cache_duration_mismatch:{job['beat_id']}:{duration}:{expected}")
    measured_fps = _measured_video_frame_rate(video, label=str(job["beat_id"]))
    expected_fps = float(job["fps"])
    if abs(measured_fps - expected_fps) > 0.001:
        raise RuntimeError(f"render_cache_frame_rate_mismatch:{job['beat_id']}:{measured_fps}:{expected_fps}")
    raw_frame_count = video.get("nb_frames")
    if raw_frame_count in (None, "", "N/A"):
        raise RuntimeError(f"render_cache_frame_count_missing:{job['beat_id']}")
    try:
        frame_count = int(raw_frame_count)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"render_cache_frame_count_invalid:{job['beat_id']}") from exc
    if abs(frame_count - int(job["duration_in_frames"])) > 1:
        raise RuntimeError(
            f"render_cache_frame_count_mismatch:{job['beat_id']}:{frame_count}:{job['duration_in_frames']}"
        )
    return {
        "duration_seconds": round(duration, 6),
        "video_codec": video.get("codec_name"),
        "frame_rate_fps": round(measured_fps, 6),
        "frame_count": frame_count,
    }


def _write_render_cache_attestation(path: Path, job: Mapping[str, Any], ffprobe: str) -> dict[str, Any]:
    media = _validate_render_media(path, job, ffprobe)
    attestation = {
        "schema_version": "contentops.retention_native.render_cache_attestation.v2",
        "beat_id": job["beat_id"],
        "variant_id": job["variant_id"],
        "cache_key": job["cache_key"],
        "renderer_version": job["renderer_version"],
        "output_path": str(path),
        "output_sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "duration_in_frames": int(job["duration_in_frames"]),
        "fps": int(job["fps"]),
        "width": int(job["width"]),
        "height": int(job["height"]),
        **media,
        "network_calls": 0,
        "public_write": False,
    }
    _write_json(_render_cache_attestation_path(path), attestation)
    return attestation


def _validated_render_cache_hit(path: Path, job: Mapping[str, Any], ffprobe: str) -> dict[str, Any] | None:
    attestation_path = _render_cache_attestation_path(path)
    if not path.is_file() or not attestation_path.is_file():
        return None
    try:
        attestation = _read_json(attestation_path)
        expected = {
            "schema_version": "contentops.retention_native.render_cache_attestation.v2",
            "beat_id": job["beat_id"],
            "variant_id": job["variant_id"],
            "cache_key": job["cache_key"],
            "renderer_version": job["renderer_version"],
            "output_path": str(path),
            "duration_in_frames": int(job["duration_in_frames"]),
            "fps": int(job["fps"]),
            "width": int(job["width"]),
            "height": int(job["height"]),
        }
        if any(attestation.get(key) != value for key, value in expected.items()):
            return None
        if int(attestation.get("size_bytes") or 0) != path.stat().st_size:
            return None
        if attestation.get("output_sha256") != sha256_file(path):
            return None
        _validate_render_media(path, job, ffprobe)
        return attestation
    except (OSError, TypeError, ValueError, RuntimeError):
        return None


def _validate_raw_renderer_receipt_binding(
    binding: Any,
    normalized_receipt: Mapping[str, Any],
    *,
    receipts_root: Path,
    label: str,
) -> dict[str, Any]:
    if not isinstance(binding, Mapping) or not binding.get("path") or not binding.get("sha256"):
        raise RuntimeError(f"{label}_raw_renderer_receipt_binding_missing")
    raw_path = Path(str(binding["path"])).resolve()
    try:
        raw_path.relative_to(receipts_root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"{label}_raw_renderer_receipt_outside_receipts_root") from exc
    if not raw_path.is_file() or sha256_file(raw_path) != binding["sha256"]:
        raise RuntimeError(f"{label}_raw_renderer_receipt_hash_mismatch")
    raw = _read_json(raw_path)
    raw_rows = raw.get("rows")
    normalized_rows = [
        row for row in normalized_receipt.get("rows") or ()
        if isinstance(row, Mapping) and row.get("status") == "RENDERED"
    ]
    if (
        raw.get("status") != "PASS"
        or raw.get("renderer") != "remotion"
        or raw.get("renderer_version") != "4.0.507"
        or raw.get("network_calls") != 0
        or raw.get("uploads") != 0
        or raw.get("browser_profile_used") is not False
        or not isinstance(raw_rows, list)
        or len(raw_rows) != len(normalized_rows)
    ):
        raise RuntimeError(f"{label}_raw_renderer_receipt_invalid")
    normalized_by_beat = {str(row.get("beat_id")): row for row in normalized_rows}
    if {str(row.get("beat_id")) for row in raw_rows if isinstance(row, Mapping)} != set(normalized_by_beat):
        raise RuntimeError(f"{label}_raw_renderer_receipt_coverage_mismatch")
    compared_keys = (
        "beat_id",
        "scene_id",
        "variant_id",
        "output_path",
        "cache_key",
        "captions_visible",
        "status",
    )
    for raw_row in raw_rows:
        if not isinstance(raw_row, Mapping):
            raise RuntimeError(f"{label}_raw_renderer_receipt_row_invalid")
        if (
            not all(isinstance(raw_row.get(key), str) and bool(raw_row.get(key)) for key in (
                "beat_id", "scene_id", "variant_id", "output_path", "cache_key"
            ))
            or type(raw_row.get("captions_visible")) is not bool
            or raw_row.get("status") != "RENDERED"
        ):
            raise RuntimeError(f"{label}_raw_renderer_receipt_row_invalid")
        normalized = normalized_by_beat[str(raw_row.get("beat_id"))]
        if any(raw_row.get(key) != normalized.get(key) for key in compared_keys):
            raise RuntimeError(f"{label}_raw_renderer_receipt_row_binding_mismatch:{raw_row.get('beat_id')}")
    return raw


def _render_jobs(
    jobs: Sequence[Mapping[str, Any]],
    *,
    renderer_root: Path,
    public_dir: Path,
    output_root: Path,
    node: str,
    ffprobe: str,
    receipt_name: str,
) -> dict[str, Any]:
    existing_rows = []
    missing = []
    for job in jobs:
        path = Path(str(job["output_path"]))
        attestation = _validated_render_cache_hit(path, job, ffprobe)
        if attestation is not None:
            existing_rows.append({
                "beat_id": job["beat_id"],
                "variant_id": job["variant_id"],
                "output_path": str(path),
                "cache_key": job["cache_key"],
                "captions_visible": job["captions_visible"],
                "status": "CACHE_HIT",
                "elapsed_ms": 0,
                "output_sha256": attestation["output_sha256"],
                "size_bytes": attestation["size_bytes"],
                "cache_attestation_path": str(_render_cache_attestation_path(path)),
            })
        else:
            missing.append(dict(job))
    rendered_rows: list[dict[str, Any]] = []
    runtime_ms = 0
    raw_renderer_receipt_binding: dict[str, str] | None = None
    if missing:
        if not (renderer_root / "node_modules" / "remotion").is_dir():
            raise RuntimeError("remotion_dependencies_missing_run_npm_install")
        batch_path = output_root / "contracts" / f"{receipt_name}_batch.json"
        receipt_path = output_root / "receipts" / f"{receipt_name}.json"
        _write_json(batch_path, {
            "schema_version": "contentops.retention_native.remotion_batch.v2",
            "public_dir": str(public_dir),
            "jobs": missing,
        })
        started = time.perf_counter()
        _run(
            [node, "scripts/render-batch.mjs", "--batch", str(batch_path), "--receipt", str(receipt_path)],
            cwd=renderer_root,
            capture=True,
            timeout=7200,
        )
        runtime_ms = int(round((time.perf_counter() - started) * 1000))
        receipt = _read_json(receipt_path)
        raw_renderer_receipt_binding = {
            "path": str(receipt_path.resolve()),
            "sha256": sha256_file(receipt_path),
        }
        if receipt.get("status") != "PASS":
            raise RuntimeError(f"remotion_batch_blocked:{receipt_name}")
        raw_rows = {str(row.get("beat_id")): dict(row) for row in receipt.get("rows") or ()}
        if set(raw_rows) != {str(job["beat_id"]) for job in missing}:
            raise RuntimeError(f"remotion_receipt_job_coverage_mismatch:{receipt_name}")
        for job in missing:
            row = raw_rows[str(job["beat_id"])]
            if (
                row.get("status") != "RENDERED"
                or row.get("cache_key") != job["cache_key"]
                or Path(str(row.get("output_path") or "")).resolve() != Path(str(job["output_path"])).resolve()
            ):
                raise RuntimeError(f"remotion_receipt_binding_mismatch:{job['beat_id']}")
            path = Path(str(job["output_path"]))
            if not path.is_file():
                raise RuntimeError(f"remotion_render_output_missing:{job['beat_id']}")
            attestation = _write_render_cache_attestation(path, job, ffprobe)
            rendered_rows.append({
                **row,
                "output_sha256": attestation["output_sha256"],
                "size_bytes": attestation["size_bytes"],
                "cache_attestation_path": str(_render_cache_attestation_path(path)),
            })
    rows = sorted(existing_rows + rendered_rows, key=lambda row: str(row["beat_id"]))
    normalized_receipt = {
        "schema_version": "contentops.retention_native.render_receipt.v2",
        "status": "PASS",
        "receipt_name": receipt_name,
        "requested_job_count": len(jobs),
        "rendered_job_count": len(rendered_rows),
        "cache_hit_count": len(existing_rows),
        "runtime_ms": runtime_ms,
        "network_calls": 0,
        "uploads": 0,
        "browser_profile_used": False,
        "rows": rows,
    }
    if raw_renderer_receipt_binding is not None:
        normalized_receipt["raw_renderer_receipt"] = raw_renderer_receipt_binding
        _validate_raw_renderer_receipt_binding(
            raw_renderer_receipt_binding,
            normalized_receipt,
            receipts_root=output_root / "receipts",
            label=receipt_name,
        )
    return normalized_receipt


def _concat_file(paths: Sequence[Path], output: Path, ffmpeg: str, *, audio: bool = False) -> None:
    if not paths:
        raise ValueError("concat_paths_required")
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = output.with_suffix(output.suffix + ".concat.txt")
    lines = [f"file '{str(path.resolve()).replace('\\', '/').replace(chr(39), chr(39) + '\\' + chr(39) + chr(39))}'" for path in paths]
    _write_text(manifest, "\n".join(lines) + "\n")
    command = [ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(manifest)]
    if audio:
        command.extend(["-c:a", "pcm_s16le"])
    else:
        command.extend(["-c", "copy", "-movflags", "+faststart"])
    command.append(str(output))
    _run(command, timeout=1800)


def _timestamp(seconds: float, *, vtt: bool) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, millis = divmod(remainder, 1000)
    separator = "." if vtt else ","
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}{separator}{millis:03d}"


def _write_caption_sidecars(
    jobs: Sequence[Mapping[str, Any]],
    *,
    srt_path: Path,
    vtt_path: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    offset_frames = 0
    for job in jobs:
        fps = int(job["fps"])
        for cue in job.get("caption_cues") or ():
            start = (offset_frames + int(cue["start_frame"])) / fps
            end = (offset_frames + int(cue["end_frame"])) / fps
            rows.append({
                "beat_id": job["beat_id"],
                "start_seconds": round(start, 6),
                "end_seconds": round(end, 6),
                "lines": list(cue["lines"]),
            })
        offset_frames += int(job["duration_in_frames"])
    srt_lines: list[str] = []
    vtt_lines = ["WEBVTT", ""]
    for index, row in enumerate(rows, 1):
        text_value = "\n".join(row["lines"])
        srt_lines.extend([
            str(index),
            f"{_timestamp(row['start_seconds'], vtt=False)} --> {_timestamp(row['end_seconds'], vtt=False)}",
            text_value,
            "",
        ])
        vtt_lines.extend([
            f"{_timestamp(row['start_seconds'], vtt=True)} --> {_timestamp(row['end_seconds'], vtt=True)}",
            text_value,
            "",
        ])
    _write_text(srt_path, "\n".join(srt_lines))
    _write_text(vtt_path, "\n".join(vtt_lines))
    return rows


def _assemble_variant(
    variant_id: str,
    jobs: Sequence[Mapping[str, Any]],
    *,
    narration: Mapping[str, Mapping[str, Any]],
    output_root: Path,
    ffmpeg: str,
    ffprobe: str,
) -> dict[str, Any]:
    beat_paths = [Path(str(job["output_path"])) for job in jobs]
    for path in beat_paths:
        if not path.is_file():
            raise RuntimeError(f"rendered_beat_missing:{path.name}")
    video_key = logical_hash({
        "variant_id": variant_id,
        "beats": [{"cache_key": row["cache_key"], "sha256": sha256_file(Path(str(row["output_path"]))) } for row in jobs],
    })
    video_only = output_root / "render_cache" / "assembled_video" / variant_id / f"{video_key[:24]}.mp4"
    assembly_job = {
        "beat_id": f"assembled-{variant_id}",
        "variant_id": variant_id,
        "cache_key": video_key,
        "renderer_version": RENDERER_VERSION,
        "duration_in_frames": sum(int(row["duration_in_frames"]) for row in jobs),
        "fps": int(jobs[0]["fps"]),
        "width": int(jobs[0]["width"]),
        "height": int(jobs[0]["height"]),
    }
    video_cache_hit = _validated_render_cache_hit(video_only, assembly_job, ffprobe) is not None
    if not video_cache_hit:
        _concat_file(beat_paths, video_only, ffmpeg)
        _write_render_cache_attestation(video_only, assembly_job, ffprobe)

    padded_paths: list[Path] = []
    beat_timeline: list[dict[str, Any]] = []
    cursor_seconds = 0.0
    for job in jobs:
        audio = narration[str(job["beat_id"])]
        duration_seconds = int(job["duration_in_frames"]) / int(job["fps"])
        pad_binding = {
            "narration_sha256": audio["sha256"],
            "duration_seconds": duration_seconds,
            "sample_rate": 24000,
            "channels": 1,
        }
        pad_key = logical_hash(pad_binding)
        padded = output_root / "render_cache" / "padded_narration" / variant_id / f"{job['beat_id']}-{pad_key[:18]}.wav"
        padded.parent.mkdir(parents=True, exist_ok=True)
        padded_cache_hit = _validated_audio_cache_hit(
            padded,
            kind="padded_narration_segment",
            cache_key=pad_key,
            binding=pad_binding,
            ffprobe=ffprobe,
            expected_sample_rate=24000,
            expected_channels=1,
            expected_duration_seconds=duration_seconds,
        ) is not None
        if not padded_cache_hit:
            _run([
                ffmpeg, "-y", "-v", "error", "-i", str(audio["path"]),
                "-af", f"apad,atrim=0:{duration_seconds:.6f}",
                "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le", str(padded),
            ], timeout=180)
            _write_audio_cache_attestation(
                padded,
                kind="padded_narration_segment",
                cache_key=pad_key,
                binding=pad_binding,
                ffprobe=ffprobe,
                expected_sample_rate=24000,
                expected_channels=1,
                expected_duration_seconds=duration_seconds,
            )
        padded_paths.append(padded)
        beat_timeline.append({
            "beat_id": job["beat_id"],
            "scene_id": job["scene_id"],
            "chapter_id": job["chapter_id"],
            "narrative_role": job["narrative_role"],
            "start_seconds": round(cursor_seconds, 6),
            "end_seconds": round(cursor_seconds + duration_seconds, 6),
            "duration_seconds": round(duration_seconds, 6),
        })
        cursor_seconds += duration_seconds
    narration_binding = {
        "variant_id": variant_id,
        "padded": [sha256_file(path) for path in padded_paths],
        "duration_seconds": round(cursor_seconds, 6),
        "sample_rate": 24000,
        "channels": 1,
    }
    narration_key = logical_hash(narration_binding)
    narration_master = output_root / "render_cache" / "assembled_narration" / variant_id / f"{narration_key[:24]}.wav"
    narration_cache_hit = _validated_audio_cache_hit(
        narration_master,
        kind="assembled_narration",
        cache_key=narration_key,
        binding=narration_binding,
        ffprobe=ffprobe,
        expected_sample_rate=24000,
        expected_channels=1,
        expected_duration_seconds=cursor_seconds,
    ) is not None
    if not narration_cache_hit:
        _concat_file(padded_paths, narration_master, ffmpeg, audio=True)
        _write_audio_cache_attestation(
            narration_master,
            kind="assembled_narration",
            cache_key=narration_key,
            binding=narration_binding,
            ffprobe=ffprobe,
            expected_sample_rate=24000,
            expected_channels=1,
            expected_duration_seconds=cursor_seconds,
        )

    captions_dir = output_root / "captions"
    captions_dir.mkdir(parents=True, exist_ok=True)
    captions = _write_caption_sidecars(
        jobs,
        srt_path=captions_dir / f"{variant_id}.srt",
        vtt_path=captions_dir / f"{variant_id}.vtt",
    )
    video_probe = _probe(video_only, ffprobe)
    narration_probe = _probe(narration_master, ffprobe)
    return {
        "variant_id": variant_id,
        "duration_seconds": round(cursor_seconds, 6),
        "video_only_path": str(video_only),
        "video_only_sha256": sha256_file(video_only),
        "video_cache_hit": video_cache_hit,
        "video_cache_attestation_path": str(_render_cache_attestation_path(video_only)),
        "video_probe": video_probe,
        "narration_path": str(narration_master),
        "narration_sha256": sha256_file(narration_master),
        "narration_cache_hit": narration_cache_hit,
        "narration_cache_attestation_path": str(_audio_cache_attestation_path(narration_master)),
        "narration_probe": narration_probe,
        "beat_timeline": beat_timeline,
        "caption_rows": captions,
        "caption_sidecars": [str(captions_dir / f"{variant_id}.srt"), str(captions_dir / f"{variant_id}.vtt")],
        "jobs": [dict(row) for row in jobs],
    }


def _parse_loudnorm(stderr: str) -> dict[str, Any]:
    matches = re.findall(r"\{\s*\"input_i\".*?\}", stderr, flags=re.DOTALL)
    if not matches:
        raise RuntimeError("ffmpeg_loudnorm_json_missing")
    return json.loads(matches[-1])


def _loudness_measure(path: Path, ffmpeg: str) -> dict[str, Any]:
    completed = _run([
        ffmpeg, "-hide_banner", "-nostats", "-i", str(path),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "NUL" if os.name == "nt" else "/dev/null",
    ], capture=True, timeout=600)
    value = _parse_loudnorm(completed.stderr)
    def numeric(key: str) -> float | None:
        try:
            number = float(value[key])
            return number if math.isfinite(number) else None
        except (KeyError, TypeError, ValueError):
            return None
    return {
        "integrated_lufs": numeric("input_i"),
        "true_peak_dbtp": numeric("input_tp"),
        "loudness_range_lu": numeric("input_lra"),
        "threshold_lufs": numeric("input_thresh"),
        "raw": value,
    }


def _score_and_mix_variant(
    bundle: DirectorBundle,
    variant_result: Mapping[str, Any],
    *,
    graph: NarrativeBeatGraph,
    output_root: Path,
    ffmpeg: str,
) -> dict[str, Any]:
    variant_id = str(variant_result["variant_id"])
    beats = {row.beat_id: row for row in graph.beats}
    state_timeline = [
        {
            "beat_id": row["beat_id"],
            "state": beats[str(row["beat_id"])].audio_state,
            "start_seconds": row["start_seconds"],
            "end_seconds": row["end_seconds"],
        }
        for row in variant_result["beat_timeline"]
    ]
    starts = {str(row["beat_id"]): float(row["start_seconds"]) for row in variant_result["beat_timeline"]}
    sfx_cues = [
        {**dict(cue), "at_seconds": round(starts[str(cue["beat_id"])] + 0.12, 6)}
        for cue in bundle.audio_plan.sfx_cues
        if str(cue.get("beat_id") or "") in starts
    ]
    score_dir = output_root / "audio" / variant_id / "score"
    score = render_owned_score(
        duration_seconds=float(variant_result["duration_seconds"]),
        state_timeline=state_timeline,
        sfx_cues=sfx_cues,
        output_dir=score_dir,
    )
    audio_dir = output_root / "audio" / variant_id
    premaster = audio_dir / "premaster.wav"
    _run([
        ffmpeg, "-y", "-v", "error",
        "-i", str(variant_result["narration_path"]),
        "-i", str(score["music"]["path"]),
        "-i", str(score["sfx"]["path"]),
        "-filter_complex",
        "[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0[narr];"
        "[1:a]aresample=48000,volume=0.58[music];"
        "[music][narr]sidechaincompress=threshold=0.025:ratio=8:attack=20:release=260[ducked];"
        "[2:a]aresample=48000,volume=0.82[sfx];"
        "[narr][ducked][sfx]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.88[premix]",
        "-map", "[premix]", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le", str(premaster),
    ], timeout=1200)
    first_pass = _run([
        ffmpeg, "-hide_banner", "-nostats", "-i", str(premaster),
        "-af", "loudnorm=I=-16:TP=-2.0:LRA=11:print_format=json",
        "-f", "null", "NUL" if os.name == "nt" else "/dev/null",
    ], capture=True, timeout=900)
    measured = _parse_loudnorm(first_pass.stderr)
    master = audio_dir / "master.wav"
    filter_value = (
        "loudnorm=I=-16:TP=-2.0:LRA=11:"
        f"measured_I={measured['input_i']}:measured_LRA={measured['input_lra']}:"
        f"measured_TP={measured['input_tp']}:measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}:linear=true:print_format=json"
    )
    second_pass = _run([
        ffmpeg, "-y", "-hide_banner", "-nostats", "-i", str(premaster),
        "-af", filter_value, "-ar", "48000", "-ac", "2", "-c:a", "pcm_s24le", str(master),
    ], capture=True, timeout=900)
    second = _parse_loudnorm(second_pass.stderr)
    expected_sfx_cues = [cue for cue in bundle.audio_plan.sfx_cues if str(cue.get("beat_id") or "") in starts]
    execution_receipts = list(score.get("sfx_execution_receipts") or ())
    executed_sfx_cues = [
        row for row in execution_receipts
        if row.get("energy_verified") is True
        and int(row.get("frame_count") or 0) > 0
        and float(row.get("measured_mean_square_energy") or 0.0) > 0.0
    ]
    expected_sfx_ids = {str(cue.get("cue_id") or "") for cue in expected_sfx_cues}
    executed_sfx_ids = {str(cue.get("cue_id") or "") for cue in executed_sfx_cues}
    score_duration = float(score.get("duration_seconds") or 0.0)
    variant_duration = float(variant_result["duration_seconds"])
    return {
        "schema_version": "contentops.retention_native.audio_mix_receipt.v2",
        "status": "PASS",
        "variant_id": variant_id,
        "narration_path": variant_result["narration_path"],
        "score": score,
        "premaster_path": str(premaster),
        "master_path": str(master),
        "master_sha256": sha256_file(master),
        "first_pass": measured,
        "second_pass": second,
        "measurement": _loudness_measure(master, ffmpeg),
        "ducking": dict(bundle.audio_plan.ducking),
        "target_integrated_lufs": bundle.audio_plan.integrated_lufs_target,
        "processing_true_peak_dbtp": -2.0,
        "contract_true_peak_dbtp_max": bundle.audio_plan.true_peak_dbtp_max,
        "music_coverage_ratio": round(min(1.0, score_duration / variant_duration), 6) if variant_duration > 0 else 0.0,
        "sfx_plan_execution_ratio": round(len(executed_sfx_ids & expected_sfx_ids) / len(expected_sfx_ids), 6) if expected_sfx_ids else 1.0,
        "expected_sfx_cue_count": len(expected_sfx_cues),
        "executed_sfx_cue_count": len(executed_sfx_ids & expected_sfx_ids),
        "expected_sfx_cue_ids": sorted(expected_sfx_ids),
        "executed_sfx_cue_ids": sorted(executed_sfx_ids),
        "sfx_execution_receipts": execution_receipts,
        "network_calls": 0,
        "provider_calls": 0,
        "public_write": False,
    }


def _mux_variant(
    variant_result: Mapping[str, Any],
    mix: Mapping[str, Any],
    *,
    output_root: Path,
    ffmpeg: str,
    ffprobe: str,
) -> dict[str, Any]:
    variant_id = str(variant_result["variant_id"])
    output_name = "short_9x16.mp4" if variant_id == "short_9x16" else "midform_16x9.mp4"
    output = output_root / "outputs" / output_name
    output.parent.mkdir(parents=True, exist_ok=True)
    _run([
        ffmpeg, "-y", "-v", "error",
        "-i", str(variant_result["video_only_path"]),
        "-i", str(mix["master_path"]),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", str(output),
    ], timeout=1200)
    probe = _probe(output, ffprobe)
    return {
        "variant_id": variant_id,
        "path": str(output),
        "sha256": sha256_file(output),
        "size_bytes": output.stat().st_size,
        "probe": probe,
        "duration_seconds": _duration(output, ffprobe),
        "loudness": _loudness_measure(output, ffmpeg),
    }


def _stream(probe: Mapping[str, Any], kind: str) -> Mapping[str, Any]:
    return next((row for row in probe.get("streams") or () if row.get("codec_type") == kind), {})


def _analyze_frame_sequence(
    frames: Sequence[bytes],
    *,
    sample_fps: float,
    duration_seconds: float,
    motion_threshold: float = 0.012,
    event_threshold: float = 0.028,
    motion_changed_pixel_value_threshold: int = 12,
    motion_changed_pixel_fraction_threshold: float = 0.02,
    event_changed_pixel_value_threshold: int = 24,
    event_changed_pixel_fraction_threshold: float = 0.06,
) -> dict[str, Any]:
    if sample_fps <= 0 or duration_seconds <= 0 or len(frames) < 2:
        raise RuntimeError("primary_visual_frame_sequence_insufficient")
    frame_size = len(frames[0])
    if frame_size == 0 or any(len(frame) != frame_size for frame in frames):
        raise RuntimeError("primary_visual_frame_size_invalid")
    expected_frame_count = int(math.ceil(duration_seconds * sample_fps))
    if len(frames) not in {expected_frame_count - 1, expected_frame_count, expected_frame_count + 1}:
        raise RuntimeError(
            f"primary_visual_frame_count_duration_mismatch:{len(frames)}:{expected_frame_count}"
        )
    differences = [
        sum(abs(left - right) for left, right in zip(frames[index - 1], frames[index])) / (frame_size * 255.0)
        for index in range(1, len(frames))
    ]
    changed_pixel_fractions = [
        sum(
            1
            for left, right in zip(frames[index - 1], frames[index])
            if abs(left - right) > event_changed_pixel_value_threshold
        ) / frame_size
        for index in range(1, len(frames))
    ]
    step = 1.0 / sample_fps
    longest_static = 0.0
    longest_static_range = [0.0, 0.0]
    anchor = frames[0]
    anchor_index = 0
    cumulative_motion_events: list[float] = []
    for index, frame in enumerate(frames[1:], start=1):
        anchor_pixel_differences = [abs(left - right) for left, right in zip(anchor, frame)]
        cumulative_difference = sum(anchor_pixel_differences) / (frame_size * 255.0)
        cumulative_changed_fraction = (
            sum(value > motion_changed_pixel_value_threshold for value in anchor_pixel_differences) / frame_size
        )
        if (
            cumulative_difference >= motion_threshold
            or cumulative_changed_fraction >= motion_changed_pixel_fraction_threshold
        ):
            cumulative_motion_events.append(min(duration_seconds, index * step))
            anchor = frame
            anchor_index = index
            continue
        static_run = (index - anchor_index) * step
        if static_run > longest_static:
            longest_static = static_run
            longest_static_range = [round(anchor_index * step, 6), round(index * step, 6)]
    sampled_end_seconds = min(duration_seconds, (len(frames) - 1) * step)
    trailing_partial_interval_seconds = duration_seconds - sampled_end_seconds
    if trailing_partial_interval_seconds < -0.05 or trailing_partial_interval_seconds > step * 1.25:
        raise RuntimeError("primary_visual_sample_coverage_incomplete")
    trailing_static = duration_seconds - min(duration_seconds, anchor_index * step)
    if trailing_static > longest_static:
        longest_static = trailing_static
        longest_static_range = [
            round(min(duration_seconds, anchor_index * step), 6),
            round(duration_seconds, 6),
        ]
    major_adjacent_events: list[float] = []
    for index, (difference, changed_fraction) in enumerate(zip(differences, changed_pixel_fractions), start=1):
        at_seconds = min(duration_seconds, index * step)
        if (
            difference >= event_threshold
            or changed_fraction >= event_changed_pixel_fraction_threshold
        ):
            major_adjacent_events.append(at_seconds)
    events = [0.0]
    for at_seconds in sorted(set(cumulative_motion_events + major_adjacent_events)):
        if at_seconds - events[-1] >= 0.75:
            events.append(round(at_seconds, 6))
    if duration_seconds - events[-1] < 0.05:
        events[-1] = round(duration_seconds, 6)
    else:
        events.append(round(duration_seconds, 6))
    intervals = [round(second - first, 6) for first, second in zip(events, events[1:])]
    ordered = sorted(differences)
    percentile_index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * 0.95) - 1))
    ordered_changed_fractions = sorted(changed_pixel_fractions)
    changed_fraction_p95 = ordered_changed_fractions[percentile_index]
    return {
        "meaningful_visual_event_seconds": events,
        "cumulative_motion_event_seconds": [round(value, 6) for value in cumulative_motion_events],
        "major_adjacent_change_event_seconds": [round(value, 6) for value in major_adjacent_events],
        "meaningful_visual_beat_intervals_seconds": intervals,
        "longest_static_primary_visual_run_seconds": round(longest_static, 6),
        "longest_static_primary_visual_time_range_seconds": longest_static_range,
        "sample_fps": sample_fps,
        "sampled_frame_count": len(frames),
        "expected_frame_count": expected_frame_count,
        "sampled_end_seconds": round(sampled_end_seconds, 6),
        "trailing_partial_interval_seconds": round(trailing_partial_interval_seconds, 6),
        "sampled_primary_region": "top_71_percent_caption_excluded",
        "cumulative_motion_threshold_normalized_mean_absolute_difference": motion_threshold,
        "cumulative_motion_changed_pixel_value_threshold": motion_changed_pixel_value_threshold,
        "cumulative_motion_changed_pixel_fraction_threshold": motion_changed_pixel_fraction_threshold,
        "event_threshold_normalized_mean_absolute_difference": event_threshold,
        "event_changed_pixel_value_threshold": event_changed_pixel_value_threshold,
        "event_changed_pixel_fraction_threshold": event_changed_pixel_fraction_threshold,
        "difference_mean": round(sum(differences) / len(differences), 8),
        "difference_p95": round(ordered[percentile_index], 8),
        "changed_pixel_fraction_mean": round(sum(changed_pixel_fractions) / len(changed_pixel_fractions), 8),
        "changed_pixel_fraction_p95": round(changed_fraction_p95, 8),
    }


def _measure_primary_visual_motion(video: Path, *, duration_seconds: float, ffmpeg: str) -> dict[str, Any]:
    sample_fps = 2.0
    width = 160
    height = 64
    raw = _run_binary([
        ffmpeg, "-v", "error", "-i", str(video),
        "-vf", f"fps={sample_fps:g},scale=160:90:flags=area,crop={width}:{height}:0:0,format=gray",
        "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1",
    ], timeout=1200)
    frame_size = width * height
    if len(raw) % frame_size:
        raise RuntimeError("primary_visual_raw_frame_alignment_invalid")
    frames = [raw[index:index + frame_size] for index in range(0, len(raw), frame_size)]
    result = _analyze_frame_sequence(frames, sample_fps=sample_fps, duration_seconds=duration_seconds)
    result.update({
        "source_video": str(video),
        "source_video_sha256": sha256_file(video),
        "algorithm": "caption_excluded_grayscale_frame_difference_v3",
    })
    return result


def _retention_diagnostics(
    bundle: DirectorBundle,
    *,
    graph: NarrativeBeatGraph,
    variant_result: Mapping[str, Any],
    output: Mapping[str, Any],
    assets: Mapping[str, Mapping[str, Any]],
    mix: Mapping[str, Any],
    ffmpeg: str,
) -> tuple[RetentionDiagnostics, dict[str, Any]]:
    variant = next(row for row in bundle.platform_variant_plan.variants if row.variant_id == graph.variant_id)
    timeline = {str(row["beat_id"]): row for row in variant_result["beat_timeline"]}
    jobs = {str(row["beat_id"]): row for row in variant_result["jobs"]}
    duration = float(output["duration_seconds"])
    motion = _measure_primary_visual_motion(Path(str(output["path"])), duration_seconds=duration, ffmpeg=ffmpeg)
    ordered_events = list(motion["meaningful_visual_event_seconds"])
    intervals = tuple(float(value) for value in motion["meaningful_visual_beat_intervals_seconds"])
    longest_static = float(motion["longest_static_primary_visual_run_seconds"])
    payoff_beats = [beat for beat in graph.beats if beat.payoff_for]
    first_payoff = float(timeline[payoff_beats[0].beat_id]["start_seconds"]) if payoff_beats else None
    opened = {beat.open_loop_id for beat in graph.beats if beat.open_loop_id}
    paid = {loop_id for beat in graph.beats for loop_id in beat.payoff_for}
    open_loop_status = "PASS" if opened <= paid else "BLOCK"
    referenced_asset_ids = {asset_id for beat in graph.beats for asset_id in beat.asset_ids}
    asset_classes = tuple(sorted({assets[asset_id]["asset_class"] for asset_id in referenced_asset_ids}))
    captions = [cue for row in variant_result["jobs"] for cue in row.get("caption_cues") or ()]
    caption_lines = max((len(row.get("lines") or ()) for row in captions), default=0)
    loudness = output["loudness"]
    integrated = loudness.get("integrated_lufs")
    true_peak = loudness.get("true_peak_dbtp")
    blockers: list[str] = []
    if not variant.min_duration_seconds <= duration <= variant.max_duration_seconds:
        blockers.append("variant_duration_out_of_range")
    if longest_static > (4.0 if graph.variant_id == "short_9x16" else 8.0):
        blockers.append("primary_visual_static_run_too_long")
    if len(asset_classes) < 4:
        blockers.append("asset_class_diversity_below_four")
    if caption_lines > variant.caption_max_lines:
        blockers.append("caption_line_limit_exceeded")
    if open_loop_status != "PASS":
        blockers.append("open_loop_without_payoff")
    if float(mix.get("music_coverage_ratio") or 0.0) < 0.99:
        blockers.append("music_coverage_incomplete")
    if float(mix.get("sfx_plan_execution_ratio") or 0.0) < 1.0:
        blockers.append("sfx_execution_incomplete")
    if integrated is None or abs(float(integrated) - bundle.audio_plan.integrated_lufs_target) > 1.0:
        blockers.append("integrated_loudness_out_of_range")
    if true_peak is None or float(true_peak) > bundle.audio_plan.true_peak_dbtp_max:
        blockers.append("true_peak_above_ceiling")
    if first_payoff is None:
        blockers.append("payoff_missing")
    elif graph.variant_id == "short_9x16" and first_payoff > 12.0:
        blockers.append("short_first_payoff_late")
    elif graph.variant_id == "midform_16x9" and not 30.0 <= first_payoff <= 60.0:
        blockers.append("midform_first_payoff_outside_30_60_seconds")
    video_stream = _stream(output["probe"], "video")
    audio_stream = _stream(output["probe"], "audio")
    if int(video_stream.get("width") or 0) != variant.width or int(video_stream.get("height") or 0) != variant.height:
        blockers.append("output_resolution_mismatch")
    measured_fps = _measured_video_frame_rate(video_stream, label=graph.variant_id)
    if abs(measured_fps - float(variant.fps)) > 0.001:
        blockers.append("output_frame_rate_mismatch")
    raw_frame_count = video_stream.get("nb_frames")
    if raw_frame_count in (None, "", "N/A"):
        raise RuntimeError(f"output_frame_count_missing:{graph.variant_id}")
    measured_frame_count = int(raw_frame_count)
    if abs(measured_frame_count - round(duration * variant.fps)) > 1:
        blockers.append("output_frame_count_mismatch")
    if not audio_stream:
        blockers.append("output_audio_stream_missing")
    hook_beats = [beat for beat in graph.beats if beat.narrative_role == "hook"]
    hook_timing = float(timeline[hook_beats[0].beat_id]["start_seconds"]) if hook_beats else None
    all_claim_ids = {claim_id for beat in graph.beats for claim_id in beat.claim_ids}
    evidence_bound_claim_ids = {
        claim_id
        for beat in graph.beats
        if beat.evidence_ids
        for claim_id in beat.claim_ids
    }
    claim_coverage = len(evidence_bound_claim_ids) / len(all_claim_ids) if all_claim_ids else 1.0
    accepted_rights = {
        "PUBLIC_DOMAIN",
        "US_GOVERNMENT_PUBLIC_INFORMATION",
        "NASA_MEDIA_GUIDELINES_EDITORIAL",
        "CAPITAL_CHRONICLE_OWNED",
        "CAPITAL_CHRONICLE_INTERNAL",
    }
    rights_complete = {
        asset_id
        for asset_id in referenced_asset_ids
        if assets[asset_id].get("hash_verified") is True
        and assets[asset_id].get("rights_status") in accepted_rights
        and assets[asset_id].get("license_or_terms")
        and assets[asset_id].get("attribution")
    }
    rights_coverage = len(rights_complete) / len(referenced_asset_ids) if referenced_asset_ids else 0.0
    safe_zone_status = "PASS"
    for job in variant_result["jobs"]:
        safe = job.get("caption_safe_zone") or {}
        layout = job.get("caption_layout") or {}
        if any(abs(float(safe.get(key, -1)) - float(variant.caption_safe_zone[key])) > 1e-9 for key in ("top", "right", "bottom", "left")):
            safe_zone_status = "BLOCK"
            break
        if (
            float(layout.get("left", -1)) < float(safe["left"])
            or float(layout.get("right", -1)) < float(safe["right"])
            or float(layout.get("bottom", -1)) < float(safe["bottom"])
            or (variant.height - float(layout.get("bottom", 0)) * variant.height - float(layout.get("estimated_max_height_px", variant.height))) < float(safe["top"]) * variant.height
        ):
            safe_zone_status = "BLOCK"
            break
    if hook_timing is None:
        blockers.append("hook_missing")
    if safe_zone_status != "PASS":
        blockers.append("caption_safe_zone_blocked")
    if claim_coverage < 1.0:
        blockers.append("claim_evidence_coverage_incomplete")
    if rights_coverage < 1.0:
        blockers.append("rights_coverage_incomplete")
    diagnostic = RetentionDiagnostics(
        video_id=bundle.opportunity.video_id,
        variant_id=graph.variant_id,
        duration_seconds=round(duration, 6),
        hook_timing_seconds=round(hook_timing, 6) if hook_timing is not None else None,
        first_payoff_timing_seconds=round(first_payoff, 6) if first_payoff is not None else None,
        meaningful_visual_beat_intervals_seconds=intervals,
        longest_static_primary_visual_run_seconds=round(longest_static, 6),
        asset_classes=asset_classes,
        caption_max_lines=caption_lines,
        caption_safe_zone_status=safe_zone_status,
        music_coverage_ratio=float(mix["music_coverage_ratio"]),
        sfx_coverage_ratio=float(mix["sfx_plan_execution_ratio"]),
        integrated_lufs=float(integrated) if integrated is not None else None,
        true_peak_dbtp=float(true_peak) if true_peak is not None else None,
        open_loop_payoff_status=open_loop_status,
        claim_evidence_coverage_ratio=round(claim_coverage, 6),
        rights_coverage_ratio=round(rights_coverage, 6),
        status="PASS" if not blockers else "BLOCK",
        blockers=tuple(blockers),
    )
    detail = {
        "primary_visual_measurement": motion,
        "meaningful_visual_event_seconds": ordered_events,
        "first_payoff_beat_id": payoff_beats[0].beat_id if payoff_beats else None,
        "opened_loop_ids": sorted(opened),
        "paid_loop_ids": sorted(paid),
        "governed_claim_ids": sorted(all_claim_ids),
        "evidence_bound_claim_ids": sorted(evidence_bound_claim_ids),
        "referenced_asset_ids": sorted(referenced_asset_ids),
        "rights_complete_asset_ids": sorted(rights_complete),
        "resolution": f"{video_stream.get('width')}x{video_stream.get('height')}",
        "video_codec": video_stream.get("codec_name"),
        "frame_rate_fps": round(measured_fps, 6),
        "frame_count": measured_frame_count,
        "audio_codec": audio_stream.get("codec_name"),
    }
    return diagnostic, detail


def _review_frame(ffmpeg: str, video: Path, at_seconds: float, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    _run([
        ffmpeg, "-y", "-v", "error", "-ss", f"{max(0.0, at_seconds):.3f}",
        "-i", str(video), "-frames:v", "1", "-q:v", "2", str(output),
    ], timeout=180)


def _create_review_media(
    outputs: Mapping[str, Mapping[str, Any]],
    diagnostics: Mapping[str, RetentionDiagnostics],
    *,
    output_root: Path,
    ffmpeg: str,
) -> dict[str, Any]:
    review_dir = output_root / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    rows: dict[str, Any] = {}
    for variant_id, output in outputs.items():
        video = Path(str(output["path"]))
        duration = float(output["duration_seconds"])
        portrait = variant_id == "short_9x16"
        tile_count = 12 if portrait else 20
        grid = "4x3" if portrait else "5x4"
        scale = "270:480" if portrait else "384:216"
        contact = review_dir / f"{variant_id}_contact_sheet.jpg"
        _run([
            ffmpeg, "-y", "-v", "error", "-i", str(video),
            "-vf", f"fps={tile_count / max(duration, 0.1):.8f},scale={scale}:force_original_aspect_ratio=decrease,pad={scale}:x=(ow-iw)/2:y=(oh-ih)/2,tile={grid}",
            "-frames:v", "1", "-q:v", "2", str(contact),
        ], timeout=900)
        payoff = diagnostics[variant_id].first_payoff_timing_seconds or 0.0
        review_clip = review_dir / f"{variant_id}_hook_and_payoff_review.mp4"
        clip_start = max(0.0, payoff - (4.0 if portrait else 7.0)) if payoff > (18 if portrait else 25) else 0.0
        clip_duration = min(22.0 if portrait else 32.0, duration - clip_start)
        _run([
            ffmpeg, "-y", "-v", "error", "-ss", f"{clip_start:.3f}", "-i", str(video),
            "-t", f"{clip_duration:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(review_clip),
        ], timeout=900)
        review_motion_strip = review_dir / f"{variant_id}_hook_and_payoff_motion_strip.jpg"
        _run([
            ffmpeg, "-y", "-v", "error", "-i", str(review_clip),
            "-vf", f"fps={12 / max(clip_duration, 0.1):.8f},scale={scale}:force_original_aspect_ratio=decrease,pad={scale}:x=(ow-iw)/2:y=(oh-ih)/2,tile=4x3",
            "-frames:v", "1", "-q:v", "2", str(review_motion_strip),
        ], timeout=900)
        stills = []
        for name, second in (
            ("hook", min(0.7, duration / 10)),
            ("payoff", min(duration - 0.1, payoff + 0.8)),
            ("middle", duration * 0.54),
            ("close", max(0.0, duration - 1.2)),
        ):
            still = review_dir / "stills" / variant_id / f"{name}.jpg"
            _review_frame(ffmpeg, video, second, still)
            stills.append({"name": name, "at_seconds": round(second, 3), "path": str(still), "sha256": sha256_file(still)})
        rows[variant_id] = {
            "contact_sheet": str(contact),
            "contact_sheet_sha256": sha256_file(contact),
            "review_clip": str(review_clip),
            "review_clip_sha256": sha256_file(review_clip),
            "review_clip_start_seconds": round(clip_start, 3),
            "review_clip_duration_seconds": round(clip_duration, 3),
            "review_motion_strip": str(review_motion_strip),
            "review_motion_strip_sha256": sha256_file(review_motion_strip),
            "stills": stills,
        }
    return rows


def _caption_hidden_review(
    bundle: DirectorBundle,
    *,
    all_jobs: Mapping[str, Sequence[Mapping[str, Any]]],
    narration: Mapping[str, Mapping[str, Any]],
    assets: Mapping[str, Mapping[str, Any]],
    renderer_root: Path,
    public_dir: Path,
    output_root: Path,
    node: str,
    ffmpeg: str,
    ffprobe: str,
) -> dict[str, Any]:
    selected: set[str] = set()
    for graph in bundle.beat_graphs:
        payoff = next((beat for beat in graph.beats if beat.payoff_for), graph.beats[len(graph.beats) // 2])
        for beat in (graph.beats[0], payoff, graph.beats[len(graph.beats) // 2], graph.beats[-1]):
            selected.add(beat.beat_id)
    proxy_jobs = _compile_jobs(
        bundle,
        narration=narration,
        assets=assets,
        output_root=output_root,
        renderer_source_fingerprint=str(
            next(iter(all_jobs.values()))[0]["renderer_source_fingerprint"]
        ),
        captions_visible=False,
        proxy=True,
        selected_beat_ids=selected,
    )
    rows: dict[str, Any] = {}
    for variant_id, jobs in proxy_jobs.items():
        receipt = _render_jobs(
            jobs,
            renderer_root=renderer_root,
            public_dir=public_dir,
            output_root=output_root,
            node=node,
            ffprobe=ffprobe,
            receipt_name=f"caption_hidden_{variant_id}",
        )
        output = output_root / "review" / f"{variant_id}_captions_hidden_visual_evolution.mp4"
        _concat_file([Path(str(job["output_path"])) for job in jobs], output, ffmpeg)
        duration = _duration(output, ffprobe)
        portrait = variant_id == "short_9x16"
        scale = "270:480" if portrait else "384:216"
        motion_strip = output_root / "review" / f"{variant_id}_captions_hidden_motion_strip.jpg"
        _run([
            ffmpeg, "-y", "-v", "error", "-i", str(output),
            "-vf", f"fps={12 / max(duration, 0.1):.8f},scale={scale}:force_original_aspect_ratio=decrease,pad={scale}:x=(ow-iw)/2:y=(oh-ih)/2,tile=4x3",
            "-frames:v", "1", "-q:v", "2", str(motion_strip),
        ], timeout=900)
        rows[variant_id] = {
            "status": "PASS",
            "captions_visible": False,
            "proxy_resolution": f"{jobs[0]['width']}x{jobs[0]['height']}",
            "selected_beat_ids": [job["beat_id"] for job in jobs],
            "path": str(output),
            "sha256": sha256_file(output),
            "duration_seconds": round(duration, 6),
            "motion_strip_path": str(motion_strip),
            "motion_strip_sha256": sha256_file(motion_strip),
            "receipt": receipt,
        }
    return rows


def _selective_rerender_proof(
    bundle: DirectorBundle,
    *,
    baseline_jobs: Mapping[str, Sequence[Mapping[str, Any]]],
    narration: Mapping[str, Mapping[str, Any]],
    assets: Mapping[str, Mapping[str, Any]],
    renderer_root: Path,
    public_dir: Path,
    output_root: Path,
    node: str,
    ffprobe: str,
) -> dict[str, Any]:
    target_variant = "midform_16x9"
    target_job = baseline_jobs[target_variant][len(baseline_jobs[target_variant]) // 2]
    target_decision = str(target_job["edit_states"][0]["decision_id"])
    patched = _compile_jobs(
        bundle,
        narration=narration,
        assets=assets,
        output_root=output_root,
        renderer_source_fingerprint=str(target_job["renderer_source_fingerprint"]),
        edit_overrides={target_decision: {"selective_proof_marker": "controlled_one_beat_invalidation_v2"}},
    )
    baseline_keys = {job["beat_id"]: job["cache_key"] for jobs in baseline_jobs.values() for job in jobs}
    patched_keys = {job["beat_id"]: job["cache_key"] for jobs in patched.values() for job in jobs}
    changed = sorted(beat_id for beat_id in baseline_keys if baseline_keys[beat_id] != patched_keys[beat_id])
    patched_target = next(job for job in patched[target_variant] if job["beat_id"] == target_job["beat_id"])
    original_path = output_root / "receipts" / "selective_rerender_one_beat_original_v2.json"
    if original_path.is_file():
        original = _read_json(original_path)
        receipt_value = original.get("render_receipt")
        rows = receipt_value.get("rows") if isinstance(receipt_value, Mapping) else None
        row = rows[0] if isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], Mapping) else None
        if isinstance(receipt_value, Mapping):
            try:
                _validate_raw_renderer_receipt_binding(
                    original.get("raw_renderer_receipt"),
                    receipt_value,
                    receipts_root=output_root / "receipts",
                    label="selective_rerender_one_beat_proof",
                )
            except RuntimeError as exc:
                raise RuntimeError("selective_rerender_original_raw_receipt_invalid") from exc
        output_path = Path(str(patched_target["output_path"]))
        attestation = _validated_render_cache_hit(output_path, patched_target, ffprobe)
        if (
            original.get("schema_version") != "contentops.retention_native.selective_rerender_original.v2"
            or original.get("status") != "PASS"
            or original.get("target_beat_id") != patched_target["beat_id"]
            or original.get("cache_key") != patched_target["cache_key"]
            or original.get("output_path") != patched_target["output_path"]
            or not output_path.is_file()
            or original.get("output_sha256") != sha256_file(output_path)
            or not isinstance(receipt_value, Mapping)
            or receipt_value.get("schema_version") != "contentops.retention_native.render_receipt.v2"
            or receipt_value.get("status") != "PASS"
            or receipt_value.get("receipt_name") != "selective_rerender_one_beat_proof"
            or receipt_value.get("requested_job_count") != 1
            or receipt_value.get("rendered_job_count") != 1
            or receipt_value.get("cache_hit_count") != 0
            or receipt_value.get("raw_renderer_receipt") != original.get("raw_renderer_receipt")
            or row is None
            or row.get("status") != "RENDERED"
            or row.get("beat_id") != patched_target["beat_id"]
            or row.get("variant_id") != patched_target["variant_id"]
            or row.get("cache_key") != patched_target["cache_key"]
            or Path(str(row.get("output_path") or "")).resolve() != output_path.resolve()
            or row.get("output_sha256") != sha256_file(output_path)
            or attestation is None
            or row.get("output_sha256") != attestation.get("output_sha256")
        ):
            raise RuntimeError("selective_rerender_original_receipt_invalid")
        verification_receipt = _render_jobs(
            [patched_target],
            renderer_root=renderer_root,
            public_dir=public_dir,
            output_root=output_root,
            node=node,
            ffprobe=ffprobe,
            receipt_name="selective_rerender_one_beat_verification",
        )
        if verification_receipt["cache_hit_count"] != 1:
            raise RuntimeError("selective_rerender_preserved_cache_verification_failed")
        receipt = dict(receipt_value)
    else:
        if _validated_render_cache_hit(Path(str(patched_target["output_path"])), patched_target, ffprobe) is not None:
            raise RuntimeError("selective_rerender_cached_target_without_original_receipt")
        receipt = _render_jobs(
            [patched_target],
            renderer_root=renderer_root,
            public_dir=public_dir,
            output_root=output_root,
            node=node,
            ffprobe=ffprobe,
            receipt_name="selective_rerender_one_beat_proof",
        )
        if receipt["rendered_job_count"] != 1:
            raise RuntimeError("selective_rerender_did_not_execute_real_render")
        raw_renderer_receipt = receipt.get("raw_renderer_receipt")
        _validate_raw_renderer_receipt_binding(
            raw_renderer_receipt,
            receipt,
            receipts_root=output_root / "receipts",
            label="selective_rerender_one_beat_proof",
        )
        verification_receipt = receipt
        _write_json(original_path, {
            "schema_version": "contentops.retention_native.selective_rerender_original.v2",
            "status": "PASS",
            "target_beat_id": patched_target["beat_id"],
            "cache_key": patched_target["cache_key"],
            "output_path": patched_target["output_path"],
            "output_sha256": sha256_file(Path(str(patched_target["output_path"]))),
            "raw_renderer_receipt": raw_renderer_receipt,
            "render_receipt": receipt,
            "public_write": False,
        })
    patched_sha256 = sha256_file(Path(str(patched_target["output_path"])))
    if patched_sha256 != (receipt["rows"][0].get("output_sha256") or patched_sha256):
        raise RuntimeError("selective_rerender_output_hash_mismatch")
    proof = {
        "schema_version": "contentops.retention_native.selective_rerender_proof.v2",
        "status": "PASS" if changed == [target_job["beat_id"]] and receipt["rendered_job_count"] == 1 else "BLOCK",
        "target_variant_id": target_variant,
        "target_beat_id": target_job["beat_id"],
        "target_decision_id": target_decision,
        "controlled_change": {"selective_proof_marker": "controlled_one_beat_invalidation_v2"},
        "changed_beat_ids": changed,
        "unchanged_beat_count": len(baseline_keys) - len(changed),
        "unrelated_cache_keys_unchanged": all(baseline_keys[key] == patched_keys[key] for key in baseline_keys if key not in changed),
        "patched_render_path": patched_target["output_path"],
        "patched_render_sha256": patched_sha256,
        "original_render_receipt_path": str(original_path),
        "original_render_receipt_sha256": sha256_file(original_path),
        "raw_renderer_receipt": receipt.get("raw_renderer_receipt"),
        "receipt": receipt,
        "current_cache_verification_receipt": verification_receipt,
        "canonical_jobs_unchanged": True,
        "public_write": False,
    }
    if proof["status"] != "PASS":
        raise RuntimeError("selective_rerender_proof_failed")
    return proof


def _hash_manifest(root: Path) -> dict[str, str]:
    excluded = {"hash_manifest.json", "package_lock.json"}
    manifest: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        manifest[relative] = sha256_file(path)
    return manifest


def verify_hash_manifest(root: str | Path) -> dict[str, Any]:
    package = Path(root).resolve()
    path = package / "hash_manifest.json"
    if not path.is_file():
        return {"status": "BLOCK", "blockers": ["hash_manifest_missing"], "verified_file_count": 0}
    manifest = _read_json(path)
    blockers: list[str] = []
    for relative, expected in manifest.items():
        relative_path = Path(relative)
        if (
            not isinstance(relative, str)
            or not relative
            or "\\" in relative
            or relative_path.is_absolute()
            or ".." in relative_path.parts
            or relative in {"hash_manifest.json", "package_lock.json"}
            or not re.fullmatch(r"[0-9a-f]{64}", str(expected or ""))
        ):
            blockers.append(f"invalid_manifest_entry:{relative}")
            continue
        target = (package / relative_path).resolve()
        try:
            target.relative_to(package)
        except ValueError:
            blockers.append(f"outside_package:{relative}")
            continue
        if not target.is_file():
            blockers.append(f"missing:{relative}")
        elif sha256_file(target) != expected:
            blockers.append(f"hash_mismatch:{relative}")
    current = _hash_manifest(package)
    blockers.extend(f"untracked:{relative}" for relative in sorted(set(current) - set(manifest)))
    return {
        "status": "PASS" if not blockers else "BLOCK",
        "blockers": blockers,
        "verified_file_count": len(manifest),
    }


_MACHINE_GATE_VARIANTS = ("short_9x16", "midform_16x9")


def _machine_gate_require(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(f"machine_gate_bundle_invalid:{code}")


def _contained_package_file(root: Path, raw_path: Any, *, label: str) -> Path:
    _machine_gate_require(isinstance(raw_path, str) and bool(raw_path), f"{label}_path_missing")
    path = Path(str(raw_path)).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise RuntimeError(f"machine_gate_bundle_invalid:{label}_outside_package") from exc
    _machine_gate_require(path.is_file(), f"{label}_file_missing")
    return path


def _validate_bound_file(
    root: Path,
    row: Mapping[str, Any],
    *,
    path_key: str,
    hash_key: str,
    label: str,
) -> Path:
    path = _contained_package_file(root, row.get(path_key), label=label)
    digest = row.get(hash_key)
    _machine_gate_require(
        isinstance(digest, str)
        and bool(re.fullmatch(r"[0-9a-f]{64}", digest))
        and sha256_file(path) == digest,
        f"{label}_hash_mismatch",
    )
    return path


def _validate_render_receipt_gate(
    receipt: Any,
    *,
    label: str,
    rendered: int | None = None,
    cache_hits: int | None = None,
) -> Mapping[str, Any]:
    _machine_gate_require(isinstance(receipt, Mapping), f"{label}_shape_invalid")
    value = receipt
    _machine_gate_require(
        value.get("schema_version") == "contentops.retention_native.render_receipt.v2"
        and value.get("status") == "PASS",
        f"{label}_status_invalid",
    )
    requested = value.get("requested_job_count")
    rendered_count = value.get("rendered_job_count")
    cache_count = value.get("cache_hit_count")
    _machine_gate_require(
        all(type(item) is int and item >= 0 for item in (requested, rendered_count, cache_count))
        and requested == rendered_count + cache_count,
        f"{label}_counts_invalid",
    )
    if rendered is not None:
        _machine_gate_require(rendered_count == rendered, f"{label}_rendered_count_invalid")
    if cache_hits is not None:
        _machine_gate_require(cache_count == cache_hits, f"{label}_cache_count_invalid")
    _machine_gate_require(
        value.get("network_calls") == 0
        and value.get("uploads") == 0
        and value.get("browser_profile_used") is False,
        f"{label}_side_effect_invariant_invalid",
    )
    rows = value.get("rows")
    _machine_gate_require(isinstance(rows, list) and len(rows) == requested, f"{label}_rows_invalid")
    return value


def _validate_machine_gate_bundle(root: Path) -> dict[str, Any]:
    """Re-evaluate every pre-lock machine gate and its cross-file bindings."""
    package = root.resolve()
    report_names = (
        "variant_render_manifest_v2.json",
        "retention_diagnostics_v2.json",
        "deterministic_media_qa.json",
        "rights_provenance_report_v2.json",
        "selective_rerender_proof_v2.json",
        "audio_provenance_v2.json",
        "review_media_manifest_v2.json",
        "safety_boundary_report_v2.json",
        "cost_runtime_report_v2.json",
        "revision_history_v2.json",
        "renderer_source_manifest_v2.json",
        "contracts/story_binding_v2.json",
    )
    reports = {name: _read_json(package / name) for name in report_names}
    bundle_path = package / "contracts" / "director_bundle_v2.json"
    bundle_value = _read_json(bundle_path)
    bundle = director_bundle_from_dict(bundle_value)
    variants = {row.variant_id: row for row in bundle.platform_variant_plan.variants}
    expected_variants = set(_MACHINE_GATE_VARIANTS)
    _machine_gate_require(set(variants) == expected_variants, "director_variant_set_invalid")
    _machine_gate_require(bundle.public_write_authority is False, "director_public_write_authority_invalid")

    story_binding = reports["contracts/story_binding_v2.json"]
    story_claims = story_binding.get("claims")
    story_evidence = story_binding.get("evidence")
    _machine_gate_require(
        story_binding.get("schema_version") == "contentops.retention_native.story_binding.v2"
        and story_binding.get("story_id") == bundle.opportunity.story_id
        and story_binding.get("story_version") == bundle.opportunity.story_version
        and story_binding.get("historical_governed_package") is True
        and story_binding.get("public_write_authority") is False
        and float(story_binding.get("claim_evidence_coverage_ratio") or 0.0) == 1.0
        and re.fullmatch(r"[0-9a-f]{64}", str(story_binding.get("article_hash") or "")) is not None
        and re.fullmatch(r"[0-9a-f]{64}", str(story_binding.get("official_source_hash") or "")) is not None
        and story_binding.get("article_hash") in bundle.opportunity.evidence_hashes
        and story_binding.get("official_source_hash") in bundle.opportunity.evidence_hashes
        and isinstance(story_claims, Mapping)
        and bool(story_claims)
        and isinstance(story_evidence, Mapping)
        and bool(story_evidence),
        "story_binding_header_invalid",
    )
    _machine_gate_require(
        all(
            isinstance(row, Mapping) and row.get("claim_id") == claim_id
            for claim_id, row in story_claims.items()
        ),
        "story_binding_claim_map_invalid",
    )
    used_claim_ids = {
        claim_id for graph in bundle.beat_graphs for beat in graph.beats for claim_id in beat.claim_ids
    }
    used_evidence_ids = {
        evidence_id for graph in bundle.beat_graphs for beat in graph.beats for evidence_id in beat.evidence_ids
    }
    _machine_gate_require(used_claim_ids <= set(story_claims), "story_binding_claim_coverage_invalid")
    _machine_gate_require(used_evidence_ids <= set(story_evidence), "story_binding_evidence_coverage_invalid")
    for evidence_id, evidence in story_evidence.items():
        evidence_hashes = [
            value
            for key, value in evidence.items()
            if isinstance(value, str) and (key.endswith("sha256") or key == "sha256")
        ] if isinstance(evidence, Mapping) else []
        if isinstance(evidence, Mapping):
            evidence_hashes.extend(value for value in evidence.get("asset_hashes") or () if isinstance(value, str))
        _machine_gate_require(
            isinstance(evidence, Mapping)
            and isinstance(evidence.get("source_url"), str)
            and bool(evidence.get("source_url"))
            and bool(evidence_hashes)
            and all(re.fullmatch(r"[0-9a-f]{64}", value) is not None for value in evidence_hashes),
            f"story_binding_evidence_invalid:{evidence_id}",
        )

    render = reports["variant_render_manifest_v2.json"]
    _machine_gate_require(
        render.get("schema_version") == "contentops.retention_native.variant_render_manifest.v2"
        and render.get("status") == "PASS"
        and render.get("public_write_authority") is False,
        "render_manifest_header_invalid",
    )
    rendered_variants = render.get("variants")
    assemblies = render.get("assemblies")
    render_receipts = render.get("render_receipts")
    _machine_gate_require(
        isinstance(rendered_variants, Mapping)
        and set(rendered_variants) == expected_variants
        and isinstance(assemblies, Mapping)
        and set(assemblies) == expected_variants
        and isinstance(render_receipts, Mapping)
        and set(render_receipts) == expected_variants,
        "render_manifest_variant_set_invalid",
    )
    ffprobe = _find_binary("ffprobe", "CONTENTOPS_FFPROBE_BINARY")
    for variant_id in _MACHINE_GATE_VARIANTS:
        variant = variants[variant_id]
        output = rendered_variants[variant_id]
        _machine_gate_require(isinstance(output, Mapping), f"render_output_shape_invalid:{variant_id}")
        output_path = _validate_bound_file(
            package, output, path_key="path", hash_key="sha256", label=f"render_output:{variant_id}"
        )
        _machine_gate_require(
            output.get("variant_id") == variant_id
            and output.get("size_bytes") == output_path.stat().st_size,
            f"render_output_identity_invalid:{variant_id}",
        )
        duration = float(output.get("duration_seconds") or 0.0)
        _machine_gate_require(
            variant.min_duration_seconds <= duration <= variant.max_duration_seconds,
            f"render_output_duration_invalid:{variant_id}",
        )
        probe = output.get("probe")
        _machine_gate_require(isinstance(probe, Mapping), f"render_output_probe_missing:{variant_id}")
        video_stream = _stream(probe, "video")
        audio_stream = _stream(probe, "audio")
        _machine_gate_require(
            int(video_stream.get("width") or 0) == variant.width
            and int(video_stream.get("height") or 0) == variant.height
            and bool(audio_stream),
            f"render_output_streams_invalid:{variant_id}",
        )
        measured_fps = _measured_video_frame_rate(video_stream, label=variant_id)
        _machine_gate_require(abs(measured_fps - variant.fps) <= 0.001, f"render_output_fps_invalid:{variant_id}")
        raw_frame_count = video_stream.get("nb_frames")
        _machine_gate_require(raw_frame_count not in (None, "", "N/A"), f"render_output_frame_count_missing:{variant_id}")
        _machine_gate_require(
            abs(int(raw_frame_count) - round(duration * variant.fps)) <= 1,
            f"render_output_frame_count_invalid:{variant_id}",
        )
        format_duration = float((probe.get("format") or {}).get("duration") or 0.0)
        _machine_gate_require(abs(format_duration - duration) <= 0.05, f"render_output_probe_duration_invalid:{variant_id}")
        actual_probe = _probe(output_path, ffprobe)
        actual_video = _stream(actual_probe, "video")
        actual_audio = _stream(actual_probe, "audio")
        actual_fps = _measured_video_frame_rate(actual_video, label=f"actual:{variant_id}")
        actual_frame_count = actual_video.get("nb_frames")
        actual_duration = float((actual_probe.get("format") or {}).get("duration") or 0.0)
        _machine_gate_require(
            int(actual_video.get("width") or 0) == variant.width
            and int(actual_video.get("height") or 0) == variant.height
            and bool(actual_audio)
            and abs(actual_fps - variant.fps) <= 0.001
            and actual_frame_count not in (None, "", "N/A")
            and abs(int(actual_frame_count) - round(duration * variant.fps)) <= 1
            and abs(actual_duration - duration) <= 0.05
            and actual_video.get("codec_name") == video_stream.get("codec_name")
            and actual_audio.get("codec_name") == audio_stream.get("codec_name"),
            f"render_output_actual_probe_invalid:{variant_id}",
        )
        assembly = assemblies[variant_id]
        _machine_gate_require(
            isinstance(assembly, Mapping)
            and abs(float(assembly.get("duration_seconds") or 0.0) - duration) <= 0.001
            and isinstance(assembly.get("jobs"), list)
            and bool(assembly["jobs"])
            and isinstance(assembly.get("beat_timeline"), list)
            and bool(assembly["beat_timeline"]),
            f"render_assembly_invalid:{variant_id}",
        )
        _validate_render_receipt_gate(render_receipts[variant_id], label=f"baseline_receipt:{variant_id}")

    retention = reports["retention_diagnostics_v2.json"]
    _machine_gate_require(
        retention.get("schema_version") == "contentops.retention_native.retention_diagnostics.v2"
        and retention.get("status") == "PASS",
        "retention_header_invalid",
    )
    retention_variants = retention.get("variants")
    _machine_gate_require(
        isinstance(retention_variants, Mapping) and set(retention_variants) == expected_variants,
        "retention_variant_set_invalid",
    )
    for variant_id in _MACHINE_GATE_VARIANTS:
        variant = variants[variant_id]
        row = retention_variants[variant_id]
        contract = row.get("contract") if isinstance(row, Mapping) else None
        detail = row.get("detail") if isinstance(row, Mapping) else None
        _machine_gate_require(isinstance(contract, Mapping) and isinstance(detail, Mapping), f"retention_shape_invalid:{variant_id}")
        duration = float(contract.get("duration_seconds") or 0.0)
        payoff = contract.get("first_payoff_timing_seconds")
        _machine_gate_require(
            contract.get("video_id") == bundle.opportunity.video_id
            and contract.get("variant_id") == variant_id
            and contract.get("status") == "PASS"
            and contract.get("blockers") == []
            and variant.min_duration_seconds <= duration <= variant.max_duration_seconds
            and abs(duration - float(rendered_variants[variant_id]["duration_seconds"])) <= 0.001
            and isinstance(contract.get("hook_timing_seconds"), (int, float))
            and isinstance(payoff, (int, float)),
            f"retention_contract_identity_invalid:{variant_id}",
        )
        payoff_value = float(payoff)
        _machine_gate_require(
            payoff_value <= 12.0 if variant_id == "short_9x16" else 30.0 <= payoff_value <= 60.0,
            f"retention_payoff_invalid:{variant_id}",
        )
        static_limit = 4.0 if variant_id == "short_9x16" else 8.0
        _machine_gate_require(
            float(contract.get("longest_static_primary_visual_run_seconds") or math.inf) <= static_limit
            and isinstance(contract.get("asset_classes"), list)
            and len(set(contract["asset_classes"])) >= 4
            and int(contract.get("caption_max_lines") or 0) <= variant.caption_max_lines
            and contract.get("caption_safe_zone_status") == "PASS"
            and float(contract.get("music_coverage_ratio") or 0.0) >= 0.99
            and float(contract.get("sfx_coverage_ratio") or 0.0) == 1.0
            and abs(float(contract.get("integrated_lufs") or math.inf) - bundle.audio_plan.integrated_lufs_target) <= 1.0
            and float(contract.get("true_peak_dbtp") or math.inf) <= bundle.audio_plan.true_peak_dbtp_max
            and contract.get("open_loop_payoff_status") == "PASS"
            and float(contract.get("claim_evidence_coverage_ratio") or 0.0) == 1.0
            and float(contract.get("rights_coverage_ratio") or 0.0) == 1.0,
            f"retention_policy_invalid:{variant_id}",
        )
        motion = detail.get("primary_visual_measurement")
        _machine_gate_require(isinstance(motion, Mapping), f"retention_motion_missing:{variant_id}")
        motion_path = _contained_package_file(package, motion.get("source_video"), label=f"motion_source:{variant_id}")
        sample_fps = float(motion.get("sample_fps") or 0.0)
        _machine_gate_require(
            motion_path == Path(str(rendered_variants[variant_id]["path"])).resolve()
            and motion.get("source_video_sha256") == rendered_variants[variant_id]["sha256"]
            and sha256_file(motion_path) == motion.get("source_video_sha256")
            and float(motion.get("longest_static_primary_visual_run_seconds") or math.inf)
            == float(contract["longest_static_primary_visual_run_seconds"])
            and motion.get("meaningful_visual_beat_intervals_seconds")
            == contract.get("meaningful_visual_beat_intervals_seconds")
            and sample_fps > 0
            and abs(int(motion.get("sampled_frame_count") or 0) - int(motion.get("expected_frame_count") or -10)) <= 1
            and 0 <= float(motion.get("trailing_partial_interval_seconds") or 0.0) <= 1.25 / sample_fps,
            f"retention_motion_binding_invalid:{variant_id}",
        )

    qa = reports["deterministic_media_qa.json"]
    _machine_gate_require(
        qa.get("schema_version") == "contentops.retention_native.deterministic_media_qa.v2"
        and qa.get("machine_status") == "PASS"
        and qa.get("variants") == rendered_variants
        and qa.get("diagnostic_statuses") == {variant_id: "PASS" for variant_id in _MACHINE_GATE_VARIANTS}
        and qa.get("rights_status") == "PASS"
        and qa.get("selective_rerender_status") == "PASS"
        and qa.get("caption_hidden_primary_visual_review_media") is True
        and float(qa.get("source_claim_coverage_ratio") or 0.0) == 1.0
        and float(qa.get("rights_coverage_ratio") or 0.0) == 1.0
        and qa.get("visual_acceptance") == "AWAITING_INDEPENDENT_CRITIC_AND_CHATGPT_JIM"
        and qa.get("public_write") is False
        and qa.get("public_upload") is False
        and qa.get("browser_profile_used") is False,
        "deterministic_media_qa_invalid",
    )

    rights = reports["rights_provenance_report_v2.json"]
    rights_assets = rights.get("assets")
    expected_asset_ids = {row.asset_id for row in bundle.asset_plan.assets}
    accepted_rights = {
        "PUBLIC_DOMAIN",
        "US_GOVERNMENT_PUBLIC_INFORMATION",
        "NASA_MEDIA_GUIDELINES_EDITORIAL",
        "CAPITAL_CHRONICLE_OWNED",
        "CAPITAL_CHRONICLE_INTERNAL",
    }
    _machine_gate_require(
        rights.get("schema_version") == "contentops.retention_native.rights_provenance.v2"
        and rights.get("status") == "PASS"
        and rights.get("blockers") == []
        and rights.get("public_write_authority") is False
        and isinstance(rights_assets, list)
        and {row.get("asset_id") for row in rights_assets if isinstance(row, Mapping)} == expected_asset_ids
        and rights.get("generated_illustrations") == []
        and rights.get("fake_documentary_images") == []
        and rights.get("real_person_images") == [],
        "rights_report_header_invalid",
    )
    for asset in rights_assets:
        _machine_gate_require(
            isinstance(asset, Mapping)
            and asset.get("rights_gate") == "PASS"
            and asset.get("hash_verified") is True
            and asset.get("rights_status") in accepted_rights
            and bool(asset.get("license_or_terms"))
            and bool(asset.get("attribution"))
            and not (asset.get("synthetic") is True and asset.get("documentary") is True)
            and not (asset.get("synthetic") is True and asset.get("contains_real_person") is True),
            f"asset_rights_invalid:{asset.get('asset_id') if isinstance(asset, Mapping) else 'unknown'}",
        )
        if asset.get("hydrated_path"):
            hydrated = _contained_package_file(package, asset["hydrated_path"], label=f"asset:{asset['asset_id']}")
            _machine_gate_require(sha256_file(hydrated) == asset.get("sha256"), f"asset_hash_invalid:{asset['asset_id']}")
        elif asset.get("documentary") is True:
            evidence_id = asset.get("governed_evidence_id")
            governed = story_evidence.get(evidence_id) if isinstance(evidence_id, str) else None
            _machine_gate_require(
                isinstance(governed, Mapping)
                and asset.get("source_url") == governed.get("source_url")
                and asset.get("sha256") == governed.get("sha256")
                and asset.get("hash_verification_method") == "governed_evidence_source_hash_binding",
                f"documentary_asset_story_binding_invalid:{asset['asset_id']}",
            )
        elif str(asset.get("asset_class") or "").startswith("deterministic_"):
            _machine_gate_require(
                asset.get("render_identity_sha256") == asset.get("sha256"),
                f"deterministic_asset_identity_invalid:{asset['asset_id']}",
            )
    narration_rights = rights.get("narration")
    music_rights = rights.get("music_and_sfx")
    _machine_gate_require(
        isinstance(narration_rights, Mapping)
        and narration_rights.get("local_inference") is True
        and narration_rights.get("network_calls") == 0
        and isinstance(music_rights, Mapping)
        and music_rights.get("generator") == SCORE_GENERATOR_VERSION
        and music_rights.get("rights_status") == "CAPITAL_CHRONICLE_OWNED"
        and music_rights.get("source_samples") == []
        and music_rights.get("model_calls") == 0,
        "rights_audio_invalid",
    )

    selective = reports["selective_rerender_proof_v2.json"]
    changed = selective.get("changed_beat_ids")
    _machine_gate_require(
        selective.get("schema_version") == "contentops.retention_native.selective_rerender_proof.v2"
        and selective.get("status") == "PASS"
        and selective.get("public_write") is False
        and isinstance(changed, list)
        and changed == [selective.get("target_beat_id")]
        and selective.get("unrelated_cache_keys_unchanged") is True
        and selective.get("canonical_jobs_unchanged") is True
        and int(selective.get("unchanged_beat_count") or 0) > 0,
        "selective_proof_header_invalid",
    )
    patched_path = _validate_bound_file(
        package,
        selective,
        path_key="patched_render_path",
        hash_key="patched_render_sha256",
        label="selective_patched_render",
    )
    real_receipt = _validate_render_receipt_gate(selective.get("receipt"), label="selective_real_render", rendered=1, cache_hits=0)
    raw_renderer_binding = selective.get("raw_renderer_receipt")
    _machine_gate_require(
        raw_renderer_binding == real_receipt.get("raw_renderer_receipt"),
        "selective_raw_renderer_receipt_binding_invalid",
    )
    try:
        _validate_raw_renderer_receipt_binding(
            raw_renderer_binding,
            real_receipt,
            receipts_root=package / "receipts",
            label="selective_rerender_one_beat_proof",
        )
    except RuntimeError as exc:
        raise RuntimeError("machine_gate_bundle_invalid:selective_raw_renderer_receipt_invalid") from exc
    cache_receipt = _validate_render_receipt_gate(
        selective.get("current_cache_verification_receipt"),
        label="selective_cache_verification",
        rendered=0,
        cache_hits=1,
    )
    for receipt, status, label in (
        (real_receipt, "RENDERED", "selective_real_render"),
        (cache_receipt, "CACHE_HIT", "selective_cache_verification"),
    ):
        receipt_row = receipt["rows"][0]
        _machine_gate_require(
            receipt_row.get("status") == status
            and receipt_row.get("beat_id") == selective.get("target_beat_id")
            and Path(str(receipt_row.get("output_path") or "")).resolve() == patched_path
            and receipt_row.get("output_sha256") == selective.get("patched_render_sha256"),
            f"{label}_row_binding_invalid",
        )
    original_path = _contained_package_file(
        package, selective.get("original_render_receipt_path"), label="selective_original_receipt"
    )
    _machine_gate_require(
        original_path.parent == (package / "receipts").resolve()
        and selective.get("original_render_receipt_sha256") == sha256_file(original_path),
        "selective_original_receipt_hash_invalid",
    )
    original = _read_json(original_path)
    _machine_gate_require(
        original.get("schema_version") == "contentops.retention_native.selective_rerender_original.v2"
        and original.get("status") == "PASS"
        and original.get("public_write") is False
        and original.get("target_beat_id") == selective.get("target_beat_id")
        and Path(str(original.get("output_path") or "")).resolve() == patched_path
        and original.get("output_sha256") == selective.get("patched_render_sha256")
        and original.get("raw_renderer_receipt") == raw_renderer_binding
        and original.get("render_receipt") == real_receipt,
        "selective_original_receipt_binding_invalid",
    )

    audio = reports["audio_provenance_v2.json"]
    narration = audio.get("narration_receipt")
    mixes = audio.get("mixes")
    _machine_gate_require(
        audio.get("schema_version") == "contentops.retention_native.audio_provenance.v2"
        and audio.get("status") == "PASS"
        and audio.get("provider_calls") == 0
        and audio.get("network_calls") == 0
        and audio.get("public_write") is False
        and isinstance(narration, Mapping)
        and narration.get("schema_version") == "contentops.retention_native.narration_receipt.v2"
        and narration.get("status") == "PASS"
        and narration.get("provider_calls") == 0
        and narration.get("network_calls") == 0
        and narration.get("network_call_performed") is False
        and narration.get("public_write") is False
        and narration.get("public_write_performed") is False
        and narration.get("provider") == bundle.audio_plan.narrator_provider
        and narration.get("model") == bundle.audio_plan.narrator_model
        and narration.get("voice") == bundle.audio_plan.narrator_voice
        and narration.get("license") == bundle.audio_plan.narrator_license
        and isinstance(mixes, Mapping)
        and set(mixes) == expected_variants,
        "audio_provenance_header_invalid",
    )
    beat_variant = {
        beat.beat_id: graph.variant_id
        for graph in bundle.beat_graphs
        for beat in graph.beats
    }
    for variant_id in _MACHINE_GATE_VARIANTS:
        mix = mixes[variant_id]
        expected_cue_ids = sorted(
            str(cue["cue_id"])
            for cue in bundle.audio_plan.sfx_cues
            if beat_variant.get(str(cue.get("beat_id") or "")) == variant_id
        )
        _machine_gate_require(
            isinstance(mix, Mapping)
            and mix.get("schema_version") == "contentops.retention_native.audio_mix_receipt.v2"
            and mix.get("status") == "PASS"
            and mix.get("variant_id") == variant_id
            and mix.get("provider_calls") == 0
            and mix.get("network_calls") == 0
            and mix.get("public_write") is False
            and float(mix.get("target_integrated_lufs") or math.inf) == bundle.audio_plan.integrated_lufs_target
            and float(mix.get("contract_true_peak_dbtp_max") or math.inf) == bundle.audio_plan.true_peak_dbtp_max
            and float(mix.get("music_coverage_ratio") or 0.0) >= 0.99
            and float(mix.get("sfx_plan_execution_ratio") or 0.0) == 1.0
            and mix.get("expected_sfx_cue_ids") == expected_cue_ids
            and mix.get("executed_sfx_cue_ids") == expected_cue_ids
            and mix.get("expected_sfx_cue_count") == len(expected_cue_ids)
            and mix.get("executed_sfx_cue_count") == len(expected_cue_ids),
            f"audio_mix_contract_invalid:{variant_id}",
        )
        _validate_bound_file(package, mix, path_key="master_path", hash_key="master_sha256", label=f"audio_master:{variant_id}")
        measurement = mix.get("measurement")
        score = mix.get("score")
        _machine_gate_require(
            isinstance(measurement, Mapping)
            and abs(float(measurement.get("integrated_lufs") or math.inf) - bundle.audio_plan.integrated_lufs_target) <= 1.0
            and float(measurement.get("true_peak_dbtp") or math.inf) <= bundle.audio_plan.true_peak_dbtp_max
            and isinstance(score, Mapping)
            and score.get("schema_version") == "contentops.retention_native.score.v2.2"
            and score.get("status") == "PASS"
            and score.get("generator") == "deterministic_numpy_oscillators_and_seeded_noise"
            and score.get("rights_status") == "CAPITAL_CHRONICLE_OWNED"
            and score.get("source_samples") == []
            and score.get("model_calls") == 0
            and score.get("network_calls") == 0
            and score.get("requested_sfx_cue_count") == len(expected_cue_ids)
            and score.get("executed_sfx_cue_count") == len(expected_cue_ids)
            and score.get("skipped_sfx_cues") == [],
            f"audio_score_invalid:{variant_id}",
        )
        _validate_bound_file(package, score["music"], path_key="path", hash_key="sha256", label=f"music_stem:{variant_id}")
        _validate_bound_file(package, score["sfx"], path_key="path", hash_key="sha256", label=f"sfx_stem:{variant_id}")
        sfx_receipts = score.get("sfx_execution_receipts")
        _machine_gate_require(
            isinstance(sfx_receipts, list)
            and sfx_receipts == mix.get("sfx_execution_receipts")
            and len(sfx_receipts) == len(expected_cue_ids)
            and {row.get("cue_id") for row in sfx_receipts if isinstance(row, Mapping)} == set(expected_cue_ids)
            and all(
                isinstance(row, Mapping)
                and row.get("energy_verified") is True
                and int(row.get("nonzero_sample_count") or 0) > 0
                and float(row.get("measured_mean_square_energy") or 0.0) > 0
                and float(row.get("measured_peak") or 0.0) > 0
                for row in sfx_receipts
            ),
            f"audio_sfx_execution_invalid:{variant_id}",
        )
        _machine_gate_require(
            music_rights.get("variant_hashes", {}).get(variant_id) == score["music"]["sha256"],
            f"audio_rights_hash_binding_invalid:{variant_id}",
        )

    review = reports["review_media_manifest_v2.json"]
    review_variants = review.get("variants")
    hidden_variants = review.get("caption_hidden")
    _machine_gate_require(
        review.get("schema_version") == "contentops.retention_native.review_media.v2"
        and review.get("status") == "PASS"
        and isinstance(review_variants, Mapping)
        and set(review_variants) == expected_variants
        and isinstance(hidden_variants, Mapping)
        and set(hidden_variants) == expected_variants,
        "review_media_header_invalid",
    )
    for variant_id in _MACHINE_GATE_VARIANTS:
        row = review_variants[variant_id]
        for path_key, hash_key, suffix in (
            ("contact_sheet", "contact_sheet_sha256", "contact_sheet"),
            ("review_clip", "review_clip_sha256", "review_clip"),
            ("review_motion_strip", "review_motion_strip_sha256", "motion_strip"),
        ):
            _validate_bound_file(package, row, path_key=path_key, hash_key=hash_key, label=f"review:{variant_id}:{suffix}")
        stills = row.get("stills")
        _machine_gate_require(isinstance(stills, list) and bool(stills), f"review_stills_missing:{variant_id}")
        for index, still in enumerate(stills):
            _validate_bound_file(package, still, path_key="path", hash_key="sha256", label=f"review_still:{variant_id}:{index}")
        hidden = hidden_variants[variant_id]
        _machine_gate_require(
            hidden.get("status") == "PASS" and hidden.get("captions_visible") is False,
            f"caption_hidden_header_invalid:{variant_id}",
        )
        _validate_bound_file(package, hidden, path_key="path", hash_key="sha256", label=f"caption_hidden:{variant_id}")
        _validate_bound_file(
            package,
            hidden,
            path_key="motion_strip_path",
            hash_key="motion_strip_sha256",
            label=f"caption_hidden_strip:{variant_id}",
        )
        _validate_render_receipt_gate(hidden.get("receipt"), label=f"caption_hidden_receipt:{variant_id}")

    safety = reports["safety_boundary_report_v2.json"]
    _machine_gate_require(
        safety.get("schema_version") == "contentops.retention_native.safety_boundary.v2"
        and safety.get("status") == "PASS"
        and safety.get("publication_authority") is False
        and all(
            type(safety.get(key)) is int and safety.get(key) == 0
            for key in (
                "v1_mutations",
                "browser_profile_actions",
                "cdp_actions",
                "platform_actions",
                "uploads",
                "public_writes",
                "synthetic_documentary_assets",
                "generated_real_person_assets",
            )
        ),
        "safety_boundary_invalid",
    )
    cost = reports["cost_runtime_report_v2.json"]
    cash_cost = cost.get("cash_cost_usd")
    _machine_gate_require(
        cost.get("schema_version") == "contentops.retention_native.cost_runtime.v2"
        and isinstance(cash_cost, (int, float))
        and not isinstance(cash_cost, bool)
        and float(cash_cost) == 0.0
        and type(cost.get("provider_calls")) is int and cost.get("provider_calls") == 0
        and type(cost.get("renderer_network_calls")) is int and cost.get("renderer_network_calls") == 0
        and type(cost.get("public_uploads")) is int and cost.get("public_uploads") == 0
        and cost.get("browser_profile_used") is False,
        "cost_runtime_invalid",
    )
    revision = reports["revision_history_v2.json"]
    revisions = revision.get("revisions")
    _machine_gate_require(
        revision.get("schema_version") == "contentops.retention_native.revision_history.v2"
        and revision.get("status") == "PASS"
        and revision.get("public_write") is False
        and revision.get("max_structural_revisions") == 2
        and type(revision.get("structural_revision_count")) is int
        and isinstance(revisions, list)
        and revision.get("structural_revision_count") == len(revisions)
        and 0 <= len(revisions) <= 2
        and revision.get("selective_rerender_proof") == selective
        and all(
            isinstance(row, Mapping)
            and row.get("public_write") is False
            and row.get("factual_authority_changed") is False
            for row in revisions
        ),
        "revision_history_invalid",
    )

    report_hashes = {name: sha256_file(package / name) for name in report_names}
    report_hashes["contracts/director_bundle_v2.json"] = sha256_file(bundle_path)
    binding = {
        "report_sha256s": report_hashes,
        "variant_output_sha256s": {
            variant_id: rendered_variants[variant_id]["sha256"] for variant_id in _MACHINE_GATE_VARIANTS
        },
    }
    return {
        "status": "PASS",
        "report_sha256s": report_hashes,
        "variant_output_sha256s": binding["variant_output_sha256s"],
        "machine_gate_bundle_logical_sha256": logical_hash(binding),
    }


def _existing_locked_package(root: Path) -> dict[str, Any] | None:
    lock_path = root / "package_lock.json"
    if not lock_path.is_file():
        return None
    lock = _read_json(lock_path)
    lock_payload = deepcopy(lock)
    lock_payload_sha256 = lock_payload.pop("lock_payload_logical_sha256", None)
    if lock_payload_sha256 != logical_hash(lock_payload):
        raise RuntimeError("immutable_package_lock_payload_hash_mismatch")
    expected_lock_keys = {
        "schema_version",
        "status",
        "locked_at",
        "hash_manifest_sha256",
        "verified_file_count",
        "revision_count",
        "critic_report_sha256",
        "critic_execution_receipt_sha256",
        "reviewed_output_sha256s",
        "renderer_source_fingerprint",
        "machine_gate_bundle_logical_sha256",
        "public_write_authority",
        "public_upload",
        "browser_profile_used",
        "lock_payload_logical_sha256",
    }
    if set(lock) != expected_lock_keys:
        raise RuntimeError("immutable_package_lock_key_set_invalid")
    verification = verify_hash_manifest(root)
    if verification["status"] != "PASS":
        raise RuntimeError("immutable_package_hash_validation_failed:" + ",".join(verification["blockers"]))
    invariant_values = {
        "schema_version": "contentops.retention_native.immutable_package_lock.v2",
        "status": "LOCKED_AWAITING_CHATGPT_JIM_FINAL_MEDIA_ACCEPTANCE",
        "verified_file_count": verification["verified_file_count"],
        "public_write_authority": False,
        "public_upload": False,
        "browser_profile_used": False,
    }
    if any(lock.get(key) != value for key, value in invariant_values.items()):
        raise RuntimeError("immutable_package_lock_invariant_mismatch")
    if not isinstance(lock.get("locked_at"), str) or not str(lock["locked_at"]).endswith("Z"):
        raise RuntimeError("immutable_package_lock_timestamp_invalid")
    revision = _read_json(root / "revision_history_v2.json")
    revisions = revision.get("revisions")
    if (
        type(lock.get("revision_count")) is not int
        or not 0 <= int(lock["revision_count"]) <= 2
        or revision.get("schema_version") != "contentops.retention_native.revision_history.v2"
        or revision.get("status") != "PASS"
        or lock.get("revision_count") != revision.get("structural_revision_count")
        or not isinstance(revisions, list)
        or len(revisions) != revision.get("structural_revision_count")
        or revision.get("max_structural_revisions") != 2
        or revision.get("public_write") is not False
    ):
        raise RuntimeError("immutable_package_revision_invariant_mismatch")
    if sha256_file(root / "hash_manifest.json") != lock.get("hash_manifest_sha256"):
        raise RuntimeError("immutable_package_lock_hash_mismatch")
    critic_path = root / "independent_critic_report_v2.json"
    if not critic_path.is_file() or sha256_file(critic_path) != lock.get("critic_report_sha256"):
        raise RuntimeError("immutable_package_critic_hash_mismatch")
    critic_binding = _validate_critic_for_lock(root, _read_json(critic_path))
    machine_gate_binding = _validate_machine_gate_bundle(root)
    if lock.get("machine_gate_bundle_logical_sha256") != machine_gate_binding["machine_gate_bundle_logical_sha256"]:
        raise RuntimeError("immutable_package_machine_gate_binding_mismatch")
    render_manifest = _read_json(root / "variant_render_manifest_v2.json")
    renderer_manifest = _read_json(root / "renderer_source_manifest_v2.json")
    renderer_fingerprint = _validate_renderer_source_binding(root)
    assembly_jobs = [
        job
        for assembly in (render_manifest.get("assemblies") or {}).values()
        for job in assembly.get("jobs") or ()
    ]
    if (
        not re.fullmatch(r"[0-9a-f]{64}", str(renderer_fingerprint or ""))
        or lock.get("renderer_source_fingerprint") != renderer_fingerprint
        or render_manifest.get("renderer_source_fingerprint") != renderer_fingerprint
        or not assembly_jobs
        or any(job.get("renderer_source_fingerprint") != renderer_fingerprint for job in assembly_jobs)
    ):
        raise RuntimeError("immutable_package_renderer_source_binding_mismatch")
    reviewed_hashes = lock.get("reviewed_output_sha256s") or {}
    for variant_id in ("short_9x16", "midform_16x9"):
        if reviewed_hashes.get(variant_id) != render_manifest["variants"][variant_id]["sha256"]:
            raise RuntimeError(f"immutable_package_reviewed_output_hash_mismatch:{variant_id}")
    if reviewed_hashes != critic_binding["reviewed_output_sha256s"]:
        raise RuntimeError("immutable_package_critic_output_binding_mismatch")
    if lock.get("critic_execution_receipt_sha256") != critic_binding.get("critic_execution_receipt_sha256"):
        raise RuntimeError("immutable_package_critic_execution_receipt_mismatch")
    final_qa = _read_json(root / "multimodal_visual_audio_qa_v2.json")
    if (
        final_qa.get("schema_version") != "contentops.retention_native.multimodal_visual_audio_qa.v2"
        or final_qa.get("status") != "INDEPENDENT_CRITIC_PASS_AWAITING_CHATGPT_JIM_FINAL_MEDIA_ACCEPTANCE"
        or final_qa.get("machine_diagnostics_status") != "PASS"
        or final_qa.get("machine_gate_bundle_logical_sha256") != machine_gate_binding["machine_gate_bundle_logical_sha256"]
        or final_qa.get("critic_report_sha256") != lock.get("critic_report_sha256")
        or final_qa.get("critic_execution_receipt_sha256") != lock.get("critic_execution_receipt_sha256")
        or final_qa.get("reviewed_output_sha256s") != lock.get("reviewed_output_sha256s")
        or final_qa.get("renderer_source_fingerprint") != renderer_fingerprint
        or final_qa.get("revision_count") != lock.get("revision_count")
        or final_qa.get("chatgpt_jim_final_media_acceptance") != "PENDING"
        or final_qa.get("public_write_authority") is not False
    ):
        raise RuntimeError("immutable_package_final_qa_invariant_mismatch")
    qa = _read_json(root / "deterministic_media_qa.json")
    return {
        "status": "PASS_IMMUTABLE_PACKAGE_VERIFIED",
        "output_root": str(root),
        "short_path": qa["variants"]["short_9x16"]["path"],
        "midform_path": qa["variants"]["midform_16x9"]["path"],
        "short_duration_seconds": qa["variants"]["short_9x16"]["duration_seconds"],
        "midform_duration_seconds": qa["variants"]["midform_16x9"]["duration_seconds"],
        "verified_file_count": verification["verified_file_count"],
        "public_write": False,
        "provider_calls": 0,
    }


def _rights_report(
    bundle: DirectorBundle,
    assets: Sequence[Mapping[str, Any]],
    *,
    audio_mixes: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    blockers: list[str] = []
    rows = []
    for row in assets:
        accepted = row.get("rights_status") in {
            "PUBLIC_DOMAIN",
            "US_GOVERNMENT_PUBLIC_INFORMATION",
            "NASA_MEDIA_GUIDELINES_EDITORIAL",
            "CAPITAL_CHRONICLE_OWNED",
            "CAPITAL_CHRONICLE_INTERNAL",
        }
        if not accepted or not row.get("license_or_terms") or not row.get("attribution"):
            blockers.append(f"asset_rights_incomplete:{row.get('asset_id')}")
        rows.append({**dict(row), "rights_gate": "PASS" if accepted else "BLOCK"})
    return {
        "schema_version": "contentops.retention_native.rights_provenance.v2",
        "status": "PASS" if not blockers else "BLOCK",
        "blockers": blockers,
        "assets": rows,
        "generated_illustrations": [],
        "fake_documentary_images": [],
        "real_person_images": [],
        "narration": {
            "provider": bundle.audio_plan.narrator_provider,
            "model": bundle.audio_plan.narrator_model,
            "voice": bundle.audio_plan.narrator_voice,
            "license": bundle.audio_plan.narrator_license,
            "local_inference": True,
            "network_calls": 0,
        },
        "music_and_sfx": {
            "generator": SCORE_GENERATOR_VERSION,
            "rights_status": "CAPITAL_CHRONICLE_OWNED",
            "source_samples": [],
            "model_calls": 0,
            "variant_hashes": {key: value["score"]["music"]["sha256"] for key, value in audio_mixes.items()},
        },
        "public_write_authority": False,
    }


def _critic_request(
    bundle: DirectorBundle,
    *,
    outputs: Mapping[str, Mapping[str, Any]],
    diagnostics: Mapping[str, RetentionDiagnostics],
    review: Mapping[str, Any],
    caption_hidden: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "contentops.retention_native.independent_critic_request.v2",
        "status": "READY_FOR_INDEPENDENT_CRITIC",
        "critic_must_be_independent_of_director": True,
        "review_scope": [
            "hook clarity and first-second visual authority",
            "payoff timing and open-loop closure",
            "caption-hidden primary visual evolution",
            "visual hierarchy, legibility, and premium newsroom craft",
            "edit rhythm, scene-specific motion, and asset diversity",
            "narrator naturalness, pronunciation, music ducking, SFX restraint, and mix quality",
            "rights/source labels and forecast-versus-observation boundaries",
        ],
        "required_issue_shape": {
            "severity": "BLOCKER|MAJOR|MINOR|NOTE",
            "video_id": bundle.opportunity.video_id,
            "variant_id": "short_9x16|midform_16x9",
            "scene_id": "one_exact_scene_id",
            "start_seconds": "finite_nonnegative_number",
            "end_seconds": "finite_number_greater_than_or_equal_to_start",
            "beat_ids": ["one_or_more_ids"],
            "category": "hook|payoff|visual|edit|caption|audio|rights|evidence",
            "observation": "specific observable issue",
            "structural_fix": "beat/edit/asset/audio-level correction, never a vague style request",
        },
        "acceptance_rule": "PASS only with no BLOCKER or MAJOR issue; Jim/ChatGPT final media acceptance remains required.",
        "revision_limit": 2,
        "director_identity": dict(bundle.director_identity),
        "outputs": {key: {"path": value["path"], "sha256": value["sha256"], "duration_seconds": value["duration_seconds"]} for key, value in outputs.items()},
        "diagnostics": {key: asdict(value) for key, value in diagnostics.items()},
        "review_media": dict(review),
        "caption_hidden_media": dict(caption_hidden),
        "public_write_authority": False,
    }


def _review_readme(
    bundle: DirectorBundle,
    *,
    outputs: Mapping[str, Mapping[str, Any]],
    diagnostics: Mapping[str, RetentionDiagnostics],
    finalized: bool,
) -> str:
    short = diagnostics["short_9x16"]
    mid = diagnostics["midform_16x9"]
    state = "Independent critic recorded; awaiting ChatGPT/Jim final media acceptance." if finalized else "Independent critic pass still required before package lock."
    return f"""# Retention-native V2 review

Story: {bundle.opportunity.title}

This is local review media with zero publication authority. It transforms a committed governed EIA/FRED story package; it does not create new factual or analytical authority.

## Primary outputs

- `outputs/short_9x16.mp4` — {short.duration_seconds:.2f}s, 1080x1920, first payoff {short.first_payoff_timing_seconds:.2f}s.
- `outputs/midform_16x9.mp4` — {mid.duration_seconds:.2f}s, 1920x1080, first payoff {mid.first_payoff_timing_seconds:.2f}s.
- Caption sidecars are in `captions/`; review clips, stills, contact sheets, and caption-hidden evolution proofs are in `review/`.

## Review order

1. Watch both primary MP4s with audio.
2. Inspect both contact sheets for repeated visual grammar and weak scene changes.
3. Watch both caption-hidden evolution proofs; the primary visual must carry the story without text captions.
4. Read `retention_diagnostics_v2.json`, `rights_provenance_report_v2.json`, and `independent_critic_request_v2.json`.
5. Record Jim/ChatGPT's decision as `CHATGPT_JIM_TIER2_V2_RETENTION_NATIVE_VISUAL_AUDIO_AUDIT` outside this immutable proof.

Machine diagnostics: short `{short.status}`, midform `{mid.status}`. {state}

Historical boundary: the NASA image is archival 2023 geographic context, not live 2026 traffic. EIA forward values are forecasts, not certainties. This package is not financial advice.
"""


def _write_core_contracts(
    root: Path,
    bundle: DirectorBundle,
    story: Mapping[str, Any],
    assets: Sequence[Mapping[str, Any]],
) -> None:
    contracts = root / "contracts"
    _write_json(contracts / "director_bundle_v2.json", bundle.to_dict())
    _write_json(contracts / "video_opportunity_v2.json", asdict(bundle.opportunity))
    _write_json(contracts / "engagement_brief_v2.json", asdict(bundle.engagement_brief))
    _write_json(contracts / "narrative_beat_graph_v2.json", {"schema_version": "contentops.retention_native.narrative_beat_graph.v2", "graphs": [asdict(row) for row in bundle.beat_graphs]})
    _write_json(contracts / "edit_decision_graph_v2.json", {"schema_version": "contentops.retention_native.edit_decision_graph.v2", "graphs": [asdict(row) for row in bundle.edit_graphs]})
    _write_json(contracts / "asset_plan_v2.json", {"schema_version": "contentops.retention_native.asset_plan.v2", "video_id": bundle.opportunity.video_id, "assets": list(assets)})
    _write_json(contracts / "audio_plan_v2.json", asdict(bundle.audio_plan))
    _write_json(contracts / "platform_variant_plan_v2.json", asdict(bundle.platform_variant_plan))
    _write_json(contracts / "story_binding_v2.json", {
        "schema_version": "contentops.retention_native.story_binding.v2",
        "story_id": story["story_id"],
        "story_version": story["story_version"],
        "article_hash": story["article_hash"],
        "official_source_hash": story["official_source_hash"],
        "claims": story["claims"],
        "evidence": story["evidence"],
        "historical_governed_package": True,
        "claim_evidence_coverage_ratio": 1.0,
        "public_write_authority": False,
    })


def _bind_subagent_critic_execution(root: Path, critic: Mapping[str, Any]) -> dict[str, Any]:
    """Persist the exact collaboration-agent final payload plus a local capture receipt.

    The caller must supply the exact delivered agent-final object before any execution
    binding is added. This is deliberately scoped as a local delivery capture, not as
    cryptographic proof issued by the collaboration service. The lock independently
    re-hashes the preserved source payload, derived report, and every reviewed input.
    """
    value = deepcopy(dict(critic))
    value.pop("execution_receipt", None)
    identity = value.get("critic_identity")
    execution = value.get("review_execution")
    if (
        not isinstance(identity, Mapping)
        or identity.get("kind") != "codex_independent_multimodal_subagent"
        or not isinstance(execution, Mapping)
        or execution.get("report_origin") != "collaboration_agent_final"
        or execution.get("reviewer_task_name") != identity.get("task_name")
    ):
        raise RuntimeError("critic_execution_receipt_source_invalid")
    source_payload_path = (root / "receipts" / "independent_critic_agent_final_payload_v2.json").resolve()
    _write_json(source_payload_path, value)
    source_payload_sha256 = sha256_file(source_payload_path)
    delivery_envelope = {
        "message_type": "FINAL_ANSWER",
        "task_name": identity["task_name"],
        "payload_sha256": source_payload_sha256,
    }
    receipt_path = (root / "receipts" / "independent_critic_execution_v2.json").resolve()
    receipt = {
        "schema_version": "contentops.retention_native.critic_execution_receipt.v2",
        "status": "PASS",
        "captured_at": _now(),
        "capture_authority": "local_capture_of_codex_collaboration_agent_final",
        "provenance_scope": "local_attestation_bound_to_exact_agent_final_payload",
        "external_service_signed_receipt_available": False,
        "report_origin": "collaboration_agent_final",
        "reviewer_task_name": identity["task_name"],
        "source_payload_path": str(source_payload_path),
        "source_payload_sha256": source_payload_sha256,
        "delivery_envelope_logical_sha256": logical_hash(delivery_envelope),
        "critic_payload_logical_sha256": logical_hash(value),
        "review_input_binding_sha256": logical_hash({
            "input_artifacts": value.get("input_artifacts") or [],
            "input_images": value.get("input_images") or [],
        }),
        "actual_media_sampled": execution.get("actual_media_sampled") is True,
        "artifact_hashes_verified": execution.get("artifact_hashes_verified") is True,
        "files_modified": execution.get("files_modified"),
        "public_write": False,
    }
    if not (
        receipt["actual_media_sampled"]
        and receipt["artifact_hashes_verified"]
        and receipt["files_modified"] is False
    ):
        raise RuntimeError("critic_execution_receipt_attestation_invalid")
    _write_json(receipt_path, receipt)
    value["execution_receipt"] = {
        "path": str(receipt_path),
        "sha256": sha256_file(receipt_path),
    }
    return value


def _validate_renderer_source_binding(root: Path) -> str:
    manifest = _read_json(root / "renderer_source_manifest_v2.json")
    if manifest.get("schema_version") != "contentops.retention_native.renderer_source_manifest.v2":
        raise RuntimeError("renderer_source_manifest_schema_invalid")
    current = _renderer_source_manifest(Path(str(manifest.get("renderer_root") or "")))
    fingerprint = str(manifest.get("renderer_source_fingerprint") or "")
    if (
        manifest.get("status") != "PASS"
        or manifest.get("public_write") is not False
        or fingerprint != current["renderer_source_fingerprint"]
        or manifest.get("files") != current["files"]
    ):
        raise RuntimeError("renderer_source_manifest_current_bytes_mismatch")
    render_manifest = _read_json(root / "variant_render_manifest_v2.json")
    if render_manifest.get("renderer_source_fingerprint") != fingerprint:
        raise RuntimeError("renderer_manifest_source_fingerprint_mismatch")
    jobs = [
        job
        for variant in (render_manifest.get("assemblies") or {}).values()
        for job in variant.get("jobs") or ()
    ]
    if not jobs or any(job.get("renderer_source_fingerprint") != fingerprint for job in jobs):
        raise RuntimeError("render_job_source_fingerprint_mismatch")
    return fingerprint


def _router_value_sha256(value: Any) -> str:
    """Match the canonical router's deterministic digest for a validated value."""
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _canonical_critic_package_context(
    root: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Reconstruct the exact package-owned inputs supplied to the canonical critic."""
    request = _read_json(root / "independent_critic_request_v2.json")
    diagnostics = _read_json(root / "retention_diagnostics_v2.json")
    review = _read_json(root / "review_media_manifest_v2.json")
    render_manifest = _read_json(root / "variant_render_manifest_v2.json")
    opportunity = _read_json(root / "contracts" / "video_opportunity_v2.json")

    source_labels: list[str] = []
    for variant_id in ("short_9x16", "midform_16x9"):
        variant_review = review["variants"][variant_id]
        source_labels.append(f"{variant_id} contact sheet")
        source_labels.append(f"{variant_id} hook and payoff motion strip")
        for row in variant_review["stills"]:
            if row["name"] in {"hook", "payoff"}:
                source_labels.append(
                    f"{variant_id} {row['name']} still at {row['at_seconds']}s"
                )
        source_labels.append(f"{variant_id} captions-hidden motion strip")

    input_images: list[dict[str, Any]] = []
    for label in source_labels:
        safe = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        path = (root / "review" / "critic_inputs" / f"{safe}.jpg").resolve()
        if not path.is_file():
            raise RuntimeError(f"critic_canonical_input_image_missing:{safe}")
        input_images.append({"label": label, "path": str(path), "sha256": sha256_file(path)})

    input_artifacts: list[dict[str, Any]] = []
    for variant_id in ("short_9x16", "midform_16x9"):
        output = request["outputs"][variant_id]
        variant_review = review["variants"][variant_id]
        hidden = review["caption_hidden"][variant_id]
        input_artifacts.extend([
            {
                "kind": "finished_output",
                "variant_id": variant_id,
                "path": output["path"],
                "sha256": output["sha256"],
            },
            {
                "kind": "representative_review_clip",
                "variant_id": variant_id,
                "path": variant_review["review_clip"],
                "sha256": variant_review["review_clip_sha256"],
            },
            {
                "kind": "captions_hidden_motion_clip",
                "variant_id": variant_id,
                "path": hidden["path"],
                "sha256": hidden["sha256"],
            },
            {
                "kind": "captions_hidden_motion_strip",
                "variant_id": variant_id,
                "path": hidden["motion_strip_path"],
                "sha256": hidden["motion_strip_sha256"],
            },
        ])

    technical = {
        "video_id": opportunity["video_id"],
        "request_scope": request["review_scope"],
        "diagnostics": diagnostics,
        "beat_timeline": {
            variant_id: render_manifest["assemblies"][variant_id]["beat_timeline"]
            for variant_id in ("short_9x16", "midform_16x9")
        },
        "image_labels_and_hashes": [
            {"label": row["label"], "sha256": row["sha256"]} for row in input_images
        ],
        "chatgpt_jim_acceptance": "PENDING",
        "public_write_authority": False,
    }
    return technical, input_images, input_artifacts, request


def _validate_critic_for_lock(root: Path, critic: Mapping[str, Any]) -> dict[str, Any]:
    if critic.get("schema_version") != "contentops.retention_native.independent_multimodal_critic.v2":
        raise RuntimeError("critic_schema_version_invalid")
    accepted, _failure_class, _value, diagnostic = validate_critic_output(json.dumps({
        key: critic.get(key)
        for key in (
            "status",
            "summary",
            "scope",
            "issues",
            "strengths",
            "acceptance_recommendation",
        )
    }))
    if not accepted:
        raise RuntimeError(f"critic_schema_invalid:{diagnostic or 'validation_failed'}")
    if critic.get("independent_of_director") is not True:
        raise RuntimeError("critic_independence_not_attested")
    identity = critic.get("critic_identity")
    scope = critic.get("scope")
    if not isinstance(identity, Mapping) or not identity.get("kind"):
        raise RuntimeError("critic_identity_missing")
    if not isinstance(scope, Mapping) or scope.get("visual_images_reviewed") is not True or scope.get("actual_finished_media_sampled") is not True:
        raise RuntimeError("critic_actual_media_scope_not_attested")
    if scope.get("audio_listened") is not True and not scope.get("limitations"):
        raise RuntimeError("critic_audio_limitation_missing")
    authority = critic.get("authority")
    authority = authority if isinstance(authority, Mapping) else {}
    top_authority_keys = ("public_write", "publication_authority", "factual_authority")
    nested_authority_keys = (
        "public_write",
        "public_write_authority",
        "publication",
        "publication_authority",
        "factual",
        "factual_authority",
    )
    if any(key in critic and critic[key] is not False for key in top_authority_keys) or any(
        key in authority and authority[key] is not False for key in nested_authority_keys
    ):
        raise RuntimeError("critic_authority_contradiction")
    explicit_public_false = critic.get("public_write") is False or authority.get("public_write_authority") is False
    explicit_publication_false = (
        critic.get("publication_authority") is False
        or authority.get("publication_authority") is False
        or authority.get("publication") is False
    )
    explicit_factual_false = (
        critic.get("factual_authority") is False
        or authority.get("factual_authority") is False
        or authority.get("factual") is False
    )
    if not (explicit_public_false and explicit_publication_false and explicit_factual_false):
        raise RuntimeError("critic_zero_authority_attestation_missing")
    critic_execution_receipt_sha256: str | None = None
    if identity.get("kind") == "canonical_9router_multimodal_model":
        router = critic.get("router_evidence")
        if (
            not isinstance(router, Mapping)
            or router.get("terminal_disposition") != "ACCEPTED"
            or not router.get("selected_model")
            or router.get("selected_model") != identity.get("selected_model")
            or int(router.get("total_attempts") or 0) < 1
        ):
            raise RuntimeError("critic_router_acceptance_evidence_invalid")
        receipt_binding = critic.get("execution_receipt")
        if (
            not isinstance(receipt_binding, Mapping)
            or receipt_binding.get("kind") != "canonical_router"
            or not receipt_binding.get("path")
            or not receipt_binding.get("sha256")
        ):
            raise RuntimeError("critic_router_execution_receipt_binding_missing")
        receipt_path = Path(str(receipt_binding["path"])).resolve()
        try:
            receipt_path.relative_to((root / "receipts").resolve())
        except ValueError as exc:
            raise RuntimeError("critic_router_execution_receipt_outside_receipts_root") from exc
        if not receipt_path.is_file() or sha256_file(receipt_path) != receipt_binding["sha256"]:
            raise RuntimeError("critic_router_execution_receipt_hash_mismatch")
        receipt = _read_json(receipt_path)
        critic_payload = deepcopy(dict(critic))
        critic_payload.pop("execution_receipt", None)
        attempts = receipt.get("attempts")
        technical, expected_images, expected_artifacts, request = _canonical_critic_package_context(root)
        accepted_output = receipt.get("accepted_model_output")
        authored_keys = (
            "status",
            "summary",
            "scope",
            "issues",
            "strengths",
            "acceptance_recommendation",
        )
        if (
            not isinstance(accepted_output, Mapping)
            or set(accepted_output) != set(authored_keys)
            or not isinstance(accepted_output.get("scope"), Mapping)
        ):
            raise RuntimeError("critic_router_accepted_output_binding_invalid")
        expected_scope = dict(accepted_output["scope"])
        expected_scope.update({
            "visual_images_reviewed": True,
            "actual_finished_media_sampled": True,
            "finished_media_sampling_method": "contact_sheets_stills_and_ordered_motion_strips_derived_from_bound_mp4s",
            "audio_listened": False,
            "audio_technical_metrics_reviewed": True,
        })
        limitations = list(expected_scope.get("limitations") or ())
        if not limitations:
            limitations.append(
                "Audio was not auditioned; only supplied codec, loudness, peak, and coverage diagnostics were reviewed."
            )
        expected_scope["limitations"] = limitations
        router_evidence_keys = (
            "authority_id",
            "terminal_disposition",
            "selected_model",
            "models_attempted_in_order",
            "total_attempts",
            "total_fallback_transitions",
            "total_structured_repair_attempts",
            "total_usage",
            "total_cost",
            "model_identity_note",
        )
        expected_router_evidence = {
            key: receipt.get(key) for key in router_evidence_keys
        }
        expected_critic_payload = {
            key: deepcopy(accepted_output[key]) for key in authored_keys
        }
        expected_critic_payload["scope"] = expected_scope
        expected_critic_payload.update({
            "schema_version": "contentops.retention_native.independent_multimodal_critic.v2",
            "independent_of_director": True,
            "critic_identity": {
                "kind": "canonical_9router_multimodal_model",
                "selected_model": receipt.get("selected_model"),
                "gateway": receipt.get("gateway"),
                "model_identity_note": receipt.get("model_identity_note"),
            },
            "router_evidence": expected_router_evidence,
            "input_images": expected_images,
            "input_artifacts": expected_artifacts,
            "raw_image_bytes_persisted_in_report": False,
            "publication_authority": False,
            "factual_authority": False,
            "public_write": False,
        })
        expected_logical_invocation_id = f"inv_video_critic_{logical_hash(technical)[:20]}"
        expected_work_item_id = str(
            request.get("outputs", {}).get("short_9x16", {}).get("sha256")
            or "retention-native-v2"
        )[:32]
        attempt_models: list[str] = []
        model_lineage_valid = False
        prompt_lineage_valid = False
        attempt_semantics_valid = False
        observed_fallback_count = 0
        observed_repair_count = 0
        repair_transition_indexes: set[int] = set()
        if isinstance(attempts, list) and all(isinstance(row, Mapping) for row in attempts):
            for row in attempts:
                model = str(row.get("requested_model") or "")
                if model and model not in attempt_models:
                    attempt_models.append(model)
            if attempts and all(
                row.get("requested_model") in MULTIMODAL_VIDEO_CRITIC_MODEL_POOL
                for row in attempts
            ):
                model_indexes = [
                    MULTIMODAL_VIDEO_CRITIC_MODEL_POOL.index(str(row["requested_model"]))
                    for row in attempts
                ]
                observed_fallback_count = sum(
                    1 for previous, current in zip(model_indexes, model_indexes[1:])
                    if current != previous
                )
                model_lineage_valid = (
                    model_indexes[0] == 0
                    and all(
                        current in {previous, previous + 1}
                        for previous, current in zip(model_indexes, model_indexes[1:])
                    )
                    and attempt_models
                    == list(MULTIMODAL_VIDEO_CRITIC_MODEL_POOL[:len(attempt_models)])
                )
            current_prompt = CANONICAL_CRITIC_PROMPT
            prompt_lineage_valid = bool(attempts)
            for index, row in enumerate(attempts):
                current_prompt_hash = hashlib.sha256(current_prompt.encode("utf-8")).hexdigest()
                if (
                    row.get("prompt_template") != CRITIC_PROMPT_TEMPLATE
                    or row.get("prompt_version") != CRITIC_PROMPT_VERSION
                    or row.get("prompt_logical_hash") != current_prompt_hash
                ):
                    prompt_lineage_valid = False
                    break
                if index + 1 >= len(attempts):
                    continue
                next_row = attempts[index + 1]
                next_prompt_hash = next_row.get("prompt_logical_hash")
                if next_prompt_hash == current_prompt_hash:
                    continue
                repaired_prompt = canonical_critic_repair_prompt(
                    current_prompt,
                    row.get("structured_validation_diagnostic_code"),
                )
                repaired_prompt_hash = hashlib.sha256(
                    repaired_prompt.encode("utf-8")
                ).hexdigest()
                if (
                    row.get("failure_class") not in STRUCTURED_OUTPUT_CLASSES
                    or next_row.get("requested_model") != row.get("requested_model")
                    or next_prompt_hash != repaired_prompt_hash
                    or observed_repair_count >= 1
                ):
                    prompt_lineage_valid = False
                    break
                observed_repair_count += 1
                repair_transition_indexes.add(index)
                current_prompt = repaired_prompt
            critic_budget = retry_budget_for_role(
                role_task_id=MULTIMODAL_VIDEO_CRITIC_ROLE,
                logical_invocation_id=expected_logical_invocation_id,
            )
            attempt_semantics_valid = bool(attempts) and len(attempts) <= critic_budget.max_total_provider_attempts
            per_model_counts: dict[str, int] = {}
            for index, row in enumerate(attempts):
                model = str(row.get("requested_model") or "")
                if model not in MULTIMODAL_VIDEO_CRITIC_MODEL_POOL:
                    attempt_semantics_valid = False
                    break
                model_index = MULTIMODAL_VIDEO_CRITIC_MODEL_POOL.index(model)
                per_model_counts[model] = per_model_counts.get(model, 0) + 1
                model_limit = critic_budget.per_model_max_attempts[model_index]
                if (
                    row.get("attempt_number_global") != index + 1
                    or row.get("attempt_number_for_model") != per_model_counts[model]
                    or row.get("model_priority_index") != model_index
                    or per_model_counts[model] > model_limit
                ):
                    attempt_semantics_valid = False
                    break
                is_final_attempt = index + 1 == len(attempts)
                if is_final_attempt:
                    if (
                        row.get("disposition") != "accepted"
                        or row.get("failure_class") is not None
                        or row.get("structured_validation_result") != "PASS"
                        or model != receipt.get("selected_model")
                    ):
                        attempt_semantics_valid = False
                    continue
                failure_class = row.get("failure_class")
                next_row = attempts[index + 1]
                same_model = next_row.get("requested_model") == model
                if (
                    row.get("disposition") != "rejected"
                    or not isinstance(failure_class, str)
                    or not failure_class
                    or is_terminal(failure_class)
                    or (
                        failure_class in STRUCTURED_OUTPUT_CLASSES
                        and row.get("structured_validation_result") != "FAIL"
                    )
                    or (
                        failure_class not in STRUCTURED_OUTPUT_CLASSES
                        and row.get("structured_validation_result") != "NOT_EVALUATED"
                    )
                ):
                    attempt_semantics_valid = False
                    break
                if same_model:
                    same_model_retry_allowed = (
                        (
                            failure_class in STRUCTURED_OUTPUT_CLASSES
                            and index in repair_transition_indexes
                        )
                        or (
                            is_retryable(failure_class)
                            and failure_class not in SKIP_SAME_MODEL_RETRY_CLASSES
                            and next_row.get("prompt_logical_hash")
                            == row.get("prompt_logical_hash")
                        )
                    )
                    if (
                        not same_model_retry_allowed
                        or per_model_counts[model] >= model_limit
                    ):
                        attempt_semantics_valid = False
                        break
                elif not is_fallback_eligible(failure_class):
                    attempt_semantics_valid = False
                    break
                elif (
                    failure_class in STRUCTURED_OUTPUT_CLASSES
                    and observed_repair_count == 0
                    and per_model_counts[model] < model_limit
                    and index + 1 < critic_budget.max_total_provider_attempts
                ):
                    attempt_semantics_valid = False
                    break
            if (
                observed_fallback_count > critic_budget.max_fallback_transitions
                or observed_repair_count > critic_budget.max_structured_output_repair_attempts
                or any(count - 1 > critic_budget.max_same_model_retries for count in per_model_counts.values())
            ):
                attempt_semantics_valid = False
        if (
            receipt.get("schema_version") != "contentops.retention_native.canonical_critic_router_execution.v2"
            or receipt.get("status") != "PASS"
            or receipt.get("authority_id") != "CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2"
            or receipt.get("gateway") != "9router"
            or receipt.get("role_task_id") != "tier2_multimodal_video_critic"
            or receipt.get("logical_invocation_id") != expected_logical_invocation_id
            or receipt.get("work_item_id") != expected_work_item_id
            or receipt.get("terminal_disposition") != "ACCEPTED"
            or receipt.get("selected_model") != identity.get("selected_model")
            or receipt.get("selected_model") != router.get("selected_model")
            or receipt.get("gateway") != identity.get("gateway")
            or dict(router) != expected_router_evidence
            or not isinstance(attempts, list)
            or not all(isinstance(row, Mapping) for row in attempts)
            or len(attempts) != int(receipt.get("total_attempts") or 0)
            or not attempts
            or not model_lineage_valid
            or not prompt_lineage_valid
            or not attempt_semantics_valid
            or receipt.get("models_attempted_in_order") != attempt_models
            or receipt.get("total_fallback_transitions") != observed_fallback_count
            or receipt.get("total_structured_repair_attempts") != observed_repair_count
            or any(
                row.get("logical_invocation_id") != expected_logical_invocation_id
                or row.get("work_item_id") != expected_work_item_id
                or row.get("role_task_id") != "tier2_multimodal_video_critic"
                or row.get("gateway") != "9router"
                or row.get("governed_input_hash") != _router_value_sha256(technical)
                for row in attempts
            )
            or attempts[-1].get("disposition") != "accepted"
            or attempts[-1].get("structured_validation_result") != "PASS"
            or attempts[-1].get("failure_class") is not None
            or attempts[-1].get("requested_model") != identity.get("selected_model")
            or attempts[-1].get("output_hash") != receipt.get("accepted_provider_output_hash")
            or not all(isinstance(row.get("prompt_logical_hash"), str) and row.get("prompt_logical_hash") for row in attempts)
            or receipt.get("prompt_logical_hashes")
            != [row.get("prompt_logical_hash") for row in attempts]
            or receipt.get("governed_input") != technical
            or receipt.get("governed_input_hash") != logical_hash(technical)
            or receipt.get("accepted_model_output_logical_sha256")
            != logical_hash(accepted_output)
            or receipt.get("accepted_validated_output_sha256")
            != _router_value_sha256(accepted_output)
            or attempts[-1].get("validated_output_sha256")
            != receipt.get("accepted_validated_output_sha256")
            or critic_payload != expected_critic_payload
            or receipt.get("final_critic_payload_logical_sha256")
            != logical_hash(expected_critic_payload)
            or receipt.get("review_input_binding_sha256") != logical_hash({
                "input_artifacts": expected_artifacts,
                "input_images": expected_images,
            })
            or receipt.get("publication_authority") is not False
            or receipt.get("factual_authority") is not False
            or receipt.get("public_write") is not False
        ):
            raise RuntimeError("critic_router_execution_receipt_invalid")
        critic_execution_receipt_sha256 = sha256_file(receipt_path)
    elif identity.get("kind") == "codex_independent_multimodal_subagent":
        execution = critic.get("review_execution")
        if (
            not isinstance(execution, Mapping)
            or execution.get("report_origin") != "collaboration_agent_final"
            or execution.get("reviewer_task_name") != identity.get("task_name")
            or execution.get("actual_media_sampled") is not True
            or execution.get("artifact_hashes_verified") is not True
        ):
            raise RuntimeError("critic_subagent_execution_evidence_invalid")
        receipt_binding = critic.get("execution_receipt")
        if not isinstance(receipt_binding, Mapping) or not receipt_binding.get("path") or not receipt_binding.get("sha256"):
            raise RuntimeError("critic_execution_receipt_binding_missing")
        receipt_path = Path(str(receipt_binding["path"])).resolve()
        try:
            receipt_path.relative_to((root / "receipts").resolve())
        except ValueError as exc:
            raise RuntimeError("critic_execution_receipt_outside_receipts_root") from exc
        if not receipt_path.is_file() or sha256_file(receipt_path) != receipt_binding["sha256"]:
            raise RuntimeError("critic_execution_receipt_hash_mismatch")
        execution_receipt = _read_json(receipt_path)
        critic_payload = deepcopy(dict(critic))
        critic_payload.pop("execution_receipt", None)
        if (
            execution_receipt.get("schema_version") != "contentops.retention_native.critic_execution_receipt.v2"
            or execution_receipt.get("status") != "PASS"
            or execution_receipt.get("capture_authority") != "local_capture_of_codex_collaboration_agent_final"
            or execution_receipt.get("provenance_scope") != "local_attestation_bound_to_exact_agent_final_payload"
            or execution_receipt.get("external_service_signed_receipt_available") is not False
            or not isinstance(execution_receipt.get("captured_at"), str)
            or not str(execution_receipt.get("captured_at")).endswith("Z")
            or execution_receipt.get("report_origin") != "collaboration_agent_final"
            or execution_receipt.get("reviewer_task_name") != identity.get("task_name")
            or execution_receipt.get("critic_payload_logical_sha256") != logical_hash(critic_payload)
            or execution_receipt.get("review_input_binding_sha256") != logical_hash({
                "input_artifacts": critic.get("input_artifacts") or [],
                "input_images": critic.get("input_images") or [],
            })
            or execution_receipt.get("actual_media_sampled") is not True
            or execution_receipt.get("artifact_hashes_verified") is not True
            or execution_receipt.get("files_modified") is not False
            or execution_receipt.get("public_write") is not False
        ):
            raise RuntimeError("critic_execution_receipt_invalid")
        source_path = Path(str(execution_receipt.get("source_payload_path") or "")).resolve()
        try:
            source_path.relative_to((root / "receipts").resolve())
        except ValueError as exc:
            raise RuntimeError("critic_source_payload_outside_receipts_root") from exc
        source_sha256 = execution_receipt.get("source_payload_sha256")
        delivery_envelope = {
            "message_type": "FINAL_ANSWER",
            "task_name": identity.get("task_name"),
            "payload_sha256": source_sha256,
        }
        if (
            not source_path.is_file()
            or source_sha256 != sha256_file(source_path)
            or _read_json(source_path) != critic_payload
            or execution_receipt.get("delivery_envelope_logical_sha256") != logical_hash(delivery_envelope)
        ):
            raise RuntimeError("critic_source_payload_binding_invalid")
        critic_execution_receipt_sha256 = sha256_file(receipt_path)
    else:
        raise RuntimeError("critic_identity_kind_not_authorized")

    render_manifest = _read_json(root / "variant_render_manifest_v2.json")
    review_manifest = _read_json(root / "review_media_manifest_v2.json")
    director_bundle = _read_json(root / "contracts" / "director_bundle_v2.json")
    video_id = str((director_bundle.get("opportunity") or {}).get("video_id") or "")
    beat_timeline: dict[str, dict[str, Any]] = {}
    variant_durations: dict[str, float] = {}
    for variant_id in ("short_9x16", "midform_16x9"):
        assembly = render_manifest["assemblies"][variant_id]
        variant_durations[variant_id] = float(assembly["duration_seconds"])
        for row in assembly["beat_timeline"]:
            beat_timeline[str(row["beat_id"])] = {**dict(row), "variant_id": variant_id}
    for index, issue in enumerate(critic.get("issues") or ()):
        variant_id = str(issue.get("variant_id") or "")
        if issue.get("video_id") != video_id or variant_id not in variant_durations:
            raise RuntimeError(f"critic_issue_identity_binding_invalid:{index}")
        start_seconds = float(issue["start_seconds"])
        end_seconds = float(issue["end_seconds"])
        if end_seconds > variant_durations[variant_id] + 0.05:
            raise RuntimeError(f"critic_issue_time_range_outside_variant:{index}")
        rows = [beat_timeline.get(str(beat_id)) for beat_id in issue.get("beat_ids") or ()]
        if (
            not rows
            or any(row is None for row in rows)
            or any(row["variant_id"] != variant_id for row in rows if row is not None)
            or any(row["scene_id"] != issue.get("scene_id") for row in rows if row is not None)
            or any(
                end_seconds + 0.05 < float(row["start_seconds"])
                or start_seconds - 0.05 > float(row["end_seconds"])
                for row in rows
                if row is not None
            )
        ):
            raise RuntimeError(f"critic_issue_timeline_binding_invalid:{index}")
    expected: dict[str, dict[str, Any]] = {}
    for variant_id in ("short_9x16", "midform_16x9"):
        output = render_manifest["variants"][variant_id]
        hidden = review_manifest["caption_hidden"][variant_id]
        representative = review_manifest["variants"][variant_id]
        for kind, path, digest in (
            ("finished_output", output["path"], output["sha256"]),
            ("captions_hidden_motion_clip", hidden["path"], hidden["sha256"]),
            ("representative_review_clip", representative["review_clip"], representative["review_clip_sha256"]),
        ):
            expected[str(Path(str(path)).resolve())] = {"kind": kind, "variant_id": variant_id, "sha256": digest}
    artifacts = critic.get("input_artifacts")
    if not isinstance(artifacts, list):
        raise RuntimeError("critic_input_artifacts_missing")
    artifact_by_path: dict[str, Mapping[str, Any]] = {}
    for row in artifacts:
        if not isinstance(row, Mapping) or not row.get("path") or not row.get("sha256"):
            raise RuntimeError("critic_input_artifact_shape_invalid")
        resolved = Path(str(row["path"])).resolve()
        try:
            resolved.relative_to(root.resolve())
        except ValueError as exc:
            raise RuntimeError("critic_input_artifact_outside_package") from exc
        if not resolved.is_file() or sha256_file(resolved) != row["sha256"]:
            raise RuntimeError(f"critic_input_artifact_hash_mismatch:{resolved.name}")
        artifact_by_path[str(resolved)] = row
    for path, binding in expected.items():
        row = artifact_by_path.get(path)
        if (
            row is None
            or row.get("sha256") != binding["sha256"]
            or row.get("kind") != binding["kind"]
            or row.get("variant_id") != binding["variant_id"]
        ):
            raise RuntimeError(f"critic_required_artifact_binding_missing:{binding['variant_id']}:{binding['kind']}")
    for row in critic.get("input_images") or ():
        if not isinstance(row, Mapping) or not row.get("path") or not row.get("sha256"):
            raise RuntimeError("critic_input_image_shape_invalid")
        path = Path(str(row["path"])).resolve()
        try:
            path.relative_to(root.resolve())
        except ValueError as exc:
            raise RuntimeError("critic_input_image_outside_package") from exc
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise RuntimeError(f"critic_input_image_hash_mismatch:{path.name}")
    return {
        "status": "PASS",
        "bound_artifact_count": len(expected),
        "reviewed_output_sha256s": {
            variant_id: render_manifest["variants"][variant_id]["sha256"]
            for variant_id in ("short_9x16", "midform_16x9")
        },
        "critic_identity": dict(identity),
        "critic_execution_receipt_sha256": critic_execution_receipt_sha256,
    }


def _finalize_package(root: Path, critic_report_path: Path, *, revision_count: int) -> dict[str, Any]:
    if not critic_report_path.is_file():
        raise RuntimeError("critic_report_missing")
    if not 0 <= revision_count <= 2:
        raise RuntimeError("revision_count_outside_bounded_limit")
    critic = _read_json(critic_report_path)
    if critic.get("schema_version") != "contentops.retention_native.independent_multimodal_critic.v2":
        raise RuntimeError("critic_schema_version_invalid")
    if critic.get("status") not in {"PASS", "PASS_WITH_NOTES"}:
        raise RuntimeError("independent_critic_not_pass")
    issues = critic.get("issues") or []
    if any(str(row.get("severity") or "").upper() in {"BLOCKER", "MAJOR"} for row in issues):
        raise RuntimeError("independent_critic_material_issue_unresolved")
    revision_path = root / "revision_history_v2.json"
    revision = _read_json(revision_path)
    revisions = revision.get("revisions")
    if (
        revision.get("schema_version") != "contentops.retention_native.revision_history.v2"
        or revision.get("status") != "PASS"
        or revision.get("public_write") is not False
        or revision.get("max_structural_revisions") != 2
        or not isinstance(revisions, list)
        or revision.get("structural_revision_count") != len(revisions)
        or revision_count != len(revisions)
    ):
        raise RuntimeError("revision_history_count_binding_invalid")
    renderer_source_fingerprint = _validate_renderer_source_binding(root)
    critic_binding = _validate_critic_for_lock(root, critic)
    _write_json(root / "independent_critic_report_v2.json", critic)
    revision["independent_critic_status"] = critic["status"]
    _write_json(revision_path, revision)
    machine_binding = _validate_machine_gate_bundle(root)
    _write_json(root / "multimodal_visual_audio_qa_v2.json", {
        "schema_version": "contentops.retention_native.multimodal_visual_audio_qa.v2",
        "status": "INDEPENDENT_CRITIC_PASS_AWAITING_CHATGPT_JIM_FINAL_MEDIA_ACCEPTANCE",
        "machine_diagnostics_status": machine_binding["status"],
        "machine_gate_bundle_logical_sha256": machine_binding["machine_gate_bundle_logical_sha256"],
        "independent_critic_status": critic["status"],
        "critic_identity": critic.get("critic_identity"),
        "critic_scope": critic.get("scope"),
        "critic_artifact_binding": critic_binding,
        "issue_count": len(issues),
        "revision_count": revision_count,
        "critic_report_sha256": sha256_file(root / "independent_critic_report_v2.json"),
        "critic_execution_receipt_sha256": critic_binding.get("critic_execution_receipt_sha256"),
        "reviewed_output_sha256s": critic_binding["reviewed_output_sha256s"],
        "renderer_source_fingerprint": renderer_source_fingerprint,
        "revision_limit": 2,
        "chatgpt_jim_final_media_acceptance": "PENDING",
        "public_write_authority": False,
    })
    bundle = _read_json(root / "contracts" / "director_bundle_v2.json")
    diagnostics_value = _read_json(root / "retention_diagnostics_v2.json")
    diagnostic_objects = {
        key: RetentionDiagnostics(**{**row["contract"], "meaningful_visual_beat_intervals_seconds": tuple(row["contract"]["meaningful_visual_beat_intervals_seconds"]), "asset_classes": tuple(row["contract"]["asset_classes"]), "blockers": tuple(row["contract"]["blockers"])})
        for key, row in diagnostics_value["variants"].items()
    }
    _write_text(root / "REVIEW_README.md", _review_readme(
        director_bundle_from_dict(bundle),
        outputs=_read_json(root / "variant_render_manifest_v2.json")["variants"],
        diagnostics=diagnostic_objects,
        finalized=True,
    ))
    _write_json(root / "hash_manifest.json", _hash_manifest(root))
    verification = verify_hash_manifest(root)
    if verification["status"] != "PASS":
        raise RuntimeError("hash_manifest_validation_failed:" + ",".join(verification["blockers"]))
    lock_value = {
        "schema_version": "contentops.retention_native.immutable_package_lock.v2",
        "status": "LOCKED_AWAITING_CHATGPT_JIM_FINAL_MEDIA_ACCEPTANCE",
        "locked_at": _now(),
        "hash_manifest_sha256": sha256_file(root / "hash_manifest.json"),
        "verified_file_count": verification["verified_file_count"],
        "revision_count": revision_count,
        "critic_report_sha256": sha256_file(root / "independent_critic_report_v2.json"),
        "critic_execution_receipt_sha256": critic_binding.get("critic_execution_receipt_sha256"),
        "reviewed_output_sha256s": critic_binding["reviewed_output_sha256s"],
        "renderer_source_fingerprint": renderer_source_fingerprint,
        "machine_gate_bundle_logical_sha256": machine_binding["machine_gate_bundle_logical_sha256"],
        "public_write_authority": False,
        "public_upload": False,
        "browser_profile_used": False,
    }
    lock_value["lock_payload_logical_sha256"] = logical_hash(lock_value)
    _write_json(root / "package_lock.json", lock_value)
    return verification


def run_retention_native_video_factory(
    *,
    input_dir: str | Path,
    director_source: str | Path,
    renderer_root: str | Path,
    output_root: str | Path,
    tts_python: str,
    lock: bool = False,
    critic_report: str | Path | None = None,
    revision_count: int = 0,
) -> dict[str, Any]:
    started = time.perf_counter()
    root = Path(output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    existing = _existing_locked_package(root)
    if existing is not None:
        return existing
    repo_root = _repo_root_from_path(Path(input_dir).resolve())
    renderer = Path(renderer_root).resolve()
    renderer_source_manifest = _renderer_source_manifest(renderer)
    _write_json(root / "renderer_source_manifest_v2.json", renderer_source_manifest)
    ffmpeg = _find_binary("ffmpeg", "CONTENTOPS_FFMPEG_BINARY")
    ffprobe = _find_binary("ffprobe", "CONTENTOPS_FFPROBE_BINARY")
    node = _find_binary("node", "CONTENTOPS_NODE_BINARY")
    story = load_governed_oil_story(input_dir)
    source = _read_json(Path(director_source).resolve())
    bundle = build_director_bundle(source, story)
    public_dir = root / "render_public"
    asset_rows, assets, asset_network_calls = hydrate_assets(
        bundle,
        repo_root=repo_root,
        public_dir=public_dir,
        source_cache=root / "source_cache",
        governed_evidence=story["evidence"],
    )
    asset_receipt_path = root / "receipts" / "external_asset_retrieval.json"
    if asset_network_calls or not asset_receipt_path.is_file():
        _write_json(asset_receipt_path, {
            "schema_version": "contentops.retention_native.external_asset_retrieval.v2",
            "status": "PASS",
            "network_calls": asset_network_calls,
            "requested_urls": [row["source_url"] for row in asset_rows if row["asset_id"] == "nasa-persian-gulf-iss069-e-92132"],
            "retrieved_assets": [{"asset_id": row["asset_id"], "sha256": row["sha256"], "path": row["hydrated_path"]} for row in asset_rows if row["hydrated_path"]],
            "public_write": False,
            "browser_profile_used": False,
        })
    _write_core_contracts(root, bundle, story, asset_rows)
    narration, tts_receipt = generate_narration(
        bundle,
        output_root=root,
        repo_root=repo_root,
        tts_python=tts_python,
        ffprobe=ffprobe,
    )
    _write_json(root / "receipts" / "narration_receipt_v2.json", {**tts_receipt, "segments": list(narration.values())})
    jobs = _compile_jobs(
        bundle,
        narration=narration,
        assets=assets,
        output_root=root,
        renderer_source_fingerprint=str(renderer_source_manifest["renderer_source_fingerprint"]),
    )
    render_receipts: dict[str, Any] = {}
    assembled: dict[str, Any] = {}
    audio_mixes: dict[str, Any] = {}
    outputs: dict[str, Any] = {}
    diagnostics: dict[str, RetentionDiagnostics] = {}
    diagnostic_details: dict[str, Any] = {}
    graphs = {row.variant_id: row for row in bundle.beat_graphs}
    variants = {row.variant_id: row for row in bundle.platform_variant_plan.variants}
    for variant_id in ("short_9x16", "midform_16x9"):
        render_receipts[variant_id] = _render_jobs(
            jobs[variant_id],
            renderer_root=renderer,
            public_dir=public_dir,
            output_root=root,
            node=node,
            ffprobe=ffprobe,
            receipt_name=f"baseline_{variant_id}",
        )
        assembled[variant_id] = _assemble_variant(
            variant_id,
            jobs[variant_id],
            narration=narration,
            output_root=root,
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
        )
        duration = assembled[variant_id]["duration_seconds"]
        variant = variants[variant_id]
        if not variant.min_duration_seconds <= duration <= variant.max_duration_seconds:
            raise RuntimeError(f"authored_variant_duration_out_of_range:{variant_id}:{duration}")
        audio_mixes[variant_id] = _score_and_mix_variant(
            bundle,
            assembled[variant_id],
            graph=graphs[variant_id],
            output_root=root,
            ffmpeg=ffmpeg,
        )
        outputs[variant_id] = _mux_variant(
            assembled[variant_id],
            audio_mixes[variant_id],
            output_root=root,
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
        )
        diagnostics[variant_id], diagnostic_details[variant_id] = _retention_diagnostics(
            bundle,
            graph=graphs[variant_id],
            variant_result=assembled[variant_id],
            output=outputs[variant_id],
            assets=assets,
            mix=audio_mixes[variant_id],
            ffmpeg=ffmpeg,
        )
        if diagnostics[variant_id].status != "PASS":
            raise RuntimeError(f"retention_diagnostics_blocked:{variant_id}:" + ",".join(diagnostics[variant_id].blockers))
    review = _create_review_media(outputs, diagnostics, output_root=root, ffmpeg=ffmpeg)
    caption_hidden = _caption_hidden_review(
        bundle,
        all_jobs=jobs,
        narration=narration,
        assets=assets,
        renderer_root=renderer,
        public_dir=public_dir,
        output_root=root,
        node=node,
        ffmpeg=ffmpeg,
        ffprobe=ffprobe,
    )
    selective = _selective_rerender_proof(
        bundle,
        baseline_jobs=jobs,
        narration=narration,
        assets=assets,
        renderer_root=renderer,
        public_dir=public_dir,
        output_root=root,
        node=node,
        ffprobe=ffprobe,
    )
    rights = _rights_report(bundle, asset_rows, audio_mixes=audio_mixes)
    if rights["status"] != "PASS":
        raise RuntimeError("rights_gate_blocked")
    render_manifest = {
        "schema_version": "contentops.retention_native.variant_render_manifest.v2",
        "status": "PASS",
        "variants": outputs,
        "assemblies": assembled,
        "render_receipts": render_receipts,
        "renderer": "Remotion",
        "renderer_version": "4.0.507",
        "compiler_version": RENDERER_VERSION,
        "renderer_source_fingerprint": renderer_source_manifest["renderer_source_fingerprint"],
        "renderer_component_revisions": RENDERER_COMPONENT_REVISIONS,
        "public_write_authority": False,
    }
    _write_json(root / "variant_render_manifest_v2.json", render_manifest)
    _write_json(root / "retention_diagnostics_v2.json", {
        "schema_version": "contentops.retention_native.retention_diagnostics.v2",
        "status": "PASS",
        "variants": {key: {"contract": asdict(value), "detail": diagnostic_details[key]} for key, value in diagnostics.items()},
    })
    _write_json(root / "audio_provenance_v2.json", {
        "schema_version": "contentops.retention_native.audio_provenance.v2",
        "status": "PASS",
        "narration_receipt": tts_receipt,
        "mixes": audio_mixes,
        "provider_calls": 0,
        "network_calls": 0,
        "public_write": False,
    })
    _write_json(root / "rights_provenance_report_v2.json", rights)
    _write_json(root / "review_media_manifest_v2.json", {"schema_version": "contentops.retention_native.review_media.v2", "status": "PASS", "variants": review, "caption_hidden": caption_hidden})
    _write_json(root / "selective_rerender_proof_v2.json", selective)
    source_revisions = [dict(row) for row in source.get("revision_history") or ()]
    _write_json(root / "revision_history_v2.json", {
        "schema_version": "contentops.retention_native.revision_history.v2",
        "status": "PASS",
        "structural_revision_count": len(source_revisions),
        "max_structural_revisions": 2,
        "revisions": source_revisions,
        "selective_rerender_proof": selective,
        "public_write": False,
    })
    critic_request = _critic_request(bundle, outputs=outputs, diagnostics=diagnostics, review=review, caption_hidden=caption_hidden)
    _write_json(root / "independent_critic_request_v2.json", critic_request)
    _write_json(root / "deterministic_media_qa.json", {
        "schema_version": "contentops.retention_native.deterministic_media_qa.v2",
        "machine_status": "PASS",
        "variants": outputs,
        "diagnostic_statuses": {key: value.status for key, value in diagnostics.items()},
        "rights_status": rights["status"],
        "selective_rerender_status": selective["status"],
        "caption_hidden_primary_visual_review_media": True,
        "source_claim_coverage_ratio": 1.0,
        "rights_coverage_ratio": 1.0,
        "visual_acceptance": "AWAITING_INDEPENDENT_CRITIC_AND_CHATGPT_JIM",
        "public_write": False,
        "public_upload": False,
        "browser_profile_used": False,
    })
    _write_json(root / "cost_runtime_report_v2.json", {
        "schema_version": "contentops.retention_native.cost_runtime.v2",
        "cash_cost_usd": 0.0,
        "provider_calls": 0,
        "external_asset_network_calls_this_run": asset_network_calls,
        "local_tts_inference_segments_this_run": int(tts_receipt.get("local_inference_segment_count_this_run") or 0),
        "tts_cache_hit_segments_this_run": int(tts_receipt.get("cache_hit_segment_count_this_run") or 0),
        "rendered_baseline_beats_this_run": sum(row["rendered_job_count"] for row in render_receipts.values()),
        "render_cache_hits_this_run": sum(row["cache_hit_count"] for row in render_receipts.values()),
        "renderer_network_calls": 0,
        "public_uploads": 0,
        "browser_profile_used": False,
        "runtime_seconds": round(time.perf_counter() - started, 3),
    })
    _write_json(root / "safety_boundary_report_v2.json", {
        "schema_version": "contentops.retention_native.safety_boundary.v2",
        "status": "PASS",
        "v1_mutations": 0,
        "browser_profile_actions": 0,
        "cdp_actions": 0,
        "platform_actions": 0,
        "uploads": 0,
        "public_writes": 0,
        "publication_authority": False,
        "synthetic_documentary_assets": 0,
        "generated_real_person_assets": 0,
    })
    _write_text(root / "REVIEW_README.md", _review_readme(bundle, outputs=outputs, diagnostics=diagnostics, finalized=False))
    verification = None
    if lock:
        if critic_report is None:
            raise RuntimeError("critic_report_required_for_lock")
        verification = _finalize_package(root, Path(critic_report).resolve(), revision_count=revision_count)
    return {
        "status": "PASS_LOCKED" if lock else "PASS_AWAITING_INDEPENDENT_CRITIC",
        "output_root": str(root),
        "short_path": outputs["short_9x16"]["path"],
        "midform_path": outputs["midform_16x9"]["path"],
        "short_duration_seconds": outputs["short_9x16"]["duration_seconds"],
        "midform_duration_seconds": outputs["midform_16x9"]["duration_seconds"],
        "short_integrated_lufs": diagnostics["short_9x16"].integrated_lufs,
        "midform_integrated_lufs": diagnostics["midform_16x9"].integrated_lufs,
        "asset_classes": sorted(set(diagnostics["short_9x16"].asset_classes) | set(diagnostics["midform_16x9"].asset_classes)),
        "verified_file_count": verification["verified_file_count"] if verification else None,
        "provider_calls": 0,
        "public_write": False,
    }


def retention_native_video_command(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the local retention-native V2 short and midform proof package.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_STORY_INPUT)
    parser.add_argument("--director-source", type=Path, default=DEFAULT_DIRECTOR_SOURCE)
    parser.add_argument("--renderer-root", type=Path, default=DEFAULT_RENDERER_ROOT)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--tts-python", default=os.environ.get("CONTENTOPS_TIER2_TTS_PYTHON") or sys.executable)
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--critic-report", type=Path)
    parser.add_argument("--revision-count", type=int, default=0)
    args = parser.parse_args(argv)
    try:
        result = run_retention_native_video_factory(
            input_dir=args.input_dir,
            director_source=args.director_source,
            renderer_root=args.renderer_root,
            output_root=args.output_root,
            tts_python=args.tts_python,
            lock=args.lock,
            critic_report=args.critic_report,
            revision_count=args.revision_count,
        )
    except Exception as exc:
        print(json.dumps({
            "status": "BLOCKED",
            "error": str(exc),
            "provider_calls": 0,
            "public_write": False,
            "public_upload": False,
        }, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(retention_native_video_command())
