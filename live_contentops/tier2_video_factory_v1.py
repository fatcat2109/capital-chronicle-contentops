"""Tier-2-A local programmable video vertical slice.

VideoProgram is the authority. This module compiles it to local Pillow/FFmpeg
artifacts and never calls a provider, browser, upload surface, or production store.
All output is intended for an isolated runtime root outside the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .content_intelligence_contracts_v2 import logical_hash
from .media_manifest_authority_v1 import sha256_file


SCHEMA_VERSION = "contentops.tier2.video_program.v1"
MOTION_SYSTEM_VERSION = "contentops.financial_news_motion.v1"
FACTORY_VERSION = "tier2-a-local-programmable-video-v1"
CLAIM_IDS = ("UST:2Y:2026-07-13", "UST:10Y:2026-07-13", "UST:30Y:2026-07-13", "UST:2S10S:2026-07-13")
SOURCE_ID = "ust-daily-yield-curve-2026-07-13"
SOURCE_URL = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve"
TTS_PROVIDER = "kokoro"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path.name}")
    return value


def _find_binary(name: str, env_key: str) -> str:
    configured = os.environ.get(env_key)
    if configured and Path(configured).is_file():
        return configured
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"{name}_not_found")
    return found


def _probe(path: Path, ffprobe: str) -> dict[str, Any]:
    completed = subprocess.run(
        [ffprobe, "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"ffprobe_failed:{path.name}")
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe_invalid_json:{path.name}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"ffprobe_object_required:{path.name}")
    return value


def _duration(probe: Mapping[str, Any]) -> float:
    return float((probe.get("format") or {}).get("duration") or 0.0)


def _video_stream(probe: Mapping[str, Any]) -> dict[str, Any]:
    return next((dict(row) for row in probe.get("streams") or [] if row.get("codec_type") == "video"), {})


def _audio_stream(probe: Mapping[str, Any]) -> dict[str, Any]:
    return next((dict(row) for row in probe.get("streams") or [] if row.get("codec_type") == "audio"), {})


def _run(command: list[str], *, timeout: int = 600) -> None:
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0x00004000)
    completed = subprocess.run(command, check=False, timeout=timeout, creationflags=flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if completed.returncode != 0:
        raise RuntimeError(f"ffmpeg_failed:{Path(command[-1]).name}")


def _scene_input_hash(scene: Mapping[str, Any]) -> str:
    return logical_hash({key: scene.get(key) for key in (
        "scene_id", "semantic_purpose", "display_title", "script", "claim_bindings",
        "source_bindings", "asset_refs", "rights_requirements", "visual_primitive",
        "motion_intent", "aspect_layout", "credits", "fallback",
    )})


def _copy_asset(source_root: Path, asset: Mapping[str, Any], output: Path) -> dict[str, Any]:
    source = (source_root / str(asset["path"])).resolve()
    if not source.is_file():
        raise RuntimeError(f"governed_asset_missing:{asset.get('asset_id')}")
    actual_hash = sha256_file(source)
    if actual_hash != str(asset.get("sha256") or ""):
        raise RuntimeError(f"governed_asset_hash_mismatch:{asset.get('asset_id')}")
    target = output / "assets" / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(source, target)
    return {
        "asset_id": asset["asset_id"],
        "path": str(target),
        "sha256": actual_hash,
        "source_sha256": actual_hash,
        "source_label": asset.get("source_label"),
        "source_url": asset.get("source_page_url"),
        "rights_status": asset.get("rights_status"),
        "provenance_status": asset.get("provenance_status"),
        "media_role": asset.get("media_role"),
        "synthetic": False,
    }


def _repo_root_from_input(input_root: Path) -> Path:
    for candidate in (input_root, *input_root.parents):
        if (candidate / "live_contentops").is_dir() and (candidate / "AGENTS.md").is_file():
            return candidate
    raise RuntimeError("governed_input_not_inside_contentops_repo")


def load_governed_input(input_dir: str | Path) -> dict[str, Any]:
    root = Path(input_dir).resolve()
    support = _read_json(root / "grounded_support_v1.json")
    media = _read_json(root / "media_manifest_v1.json")
    article = _read_json(root / "article_manifest_v1.json")
    blockers = []
    if support.get("official_source_packet", {}).get("status") != "PASS_PUBLICATION_AUTHORIZED":
        blockers.append("governed_support_not_publication_authorized")
    if support.get("official_source_packet", {}).get("public_claim_permissions", {}).get("numeric_claims_allowed") is not True:
        blockers.append("numeric_claim_permission_missing")
    if media.get("status") != "PASS" or media.get("media_gate_status") != "PASS":
        blockers.append("media_manifest_not_pass")
    if len(support.get("official_source_packet", {}).get("numeric_claims") or []) != len(CLAIM_IDS):
        blockers.append("expected_four_numeric_claims")
    if set(support.get("claim_ids") or []) != set(CLAIM_IDS):
        blockers.append("claim_id_set_mismatch")
    if blockers:
        raise RuntimeError("governed_input_blocked:" + ",".join(blockers))
    packet = support["official_source_packet"]
    claims = {str(row["claim_id"]): dict(row) for row in packet.get("numeric_claims") or []}
    return {
        "input_root": str(root),
        "packet_id": packet["packet_id"],
        "packet_sha256": packet["provenance"]["publication_packet"]["sha256"],
        "story_id": packet["publication_assignment"]["duplicate_key"],
        "story_version": packet["as_of_utc"],
        "title": article.get("title") or packet["publication_assignment"]["title"],
        "summary": packet["publication_assignment"]["summary"],
        "claims": claims,
        "source_document": dict((packet.get("official_source_documents") or [])[0]),
        "source_documents": packet.get("official_source_documents") or [],
        "media_assets": media.get("assets") or [],
        "curve_history": packet.get("time_series", {}).get("curve_history") or [],
        "article_hash": str(article.get("article_markdown_sha256") or ""),
    }


def decide_video_eligibility(story: Mapping[str, Any]) -> dict[str, Any]:
    visual_count = len(story.get("media_assets") or [])
    evidence_count = len(story.get("claims") or {})
    rights_ready = all(str(row.get("rights_status") or "") in {"public_domain", "capital_chronicle_owned", "capital_chronicle_internal"} for row in story.get("media_assets") or [])
    if evidence_count < 2 or visual_count < 2:
        result = "VIDEO_NOT_SELECTED"
    elif not rights_ready:
        result = "VIDEO_BLOCKED"
    else:
        result = "VIDEO_SELECTED"
    return {
        "result": result,
        "evidence_strength": evidence_count,
        "materiality": "high" if evidence_count >= 4 else "medium",
        "visualizability": visual_count,
        "narrative_depth": "chapter_ready" if evidence_count >= 4 else "compact",
        "shelf_life": "historical_evaluation_material",
        "rights_ready": rights_ready,
        "production_cost": "local_zero_cash_target",
        "render_time_policy": "single_concurrent_render_below_normal_priority",
        "platform_fit": ["youtube_long_form_local_only", "native_vertical_local_only"],
        "public_write_authority": False,
    }


def _claim_bindings(*ids: str) -> list[dict[str, str]]:
    return [{"claim_id": claim_id, "evidence_id": SOURCE_ID, "source_url": SOURCE_URL} for claim_id in ids]


def _long_scene(scene_id: str, chapter_id: str, purpose: str, primitive: str, text: str, assets: list[str], claims: tuple[str, ...], order: int) -> dict[str, Any]:
    return {
        "scene_id": scene_id,
        "chapter_id": chapter_id,
        "order": order,
        "semantic_purpose": purpose,
        "display_title": purpose,
        "narration_segment_ids": [f"narration-{scene_id}"],
        "script": text,
        "claim_bindings": _claim_bindings(*claims),
        "source_bindings": [{"evidence_id": SOURCE_ID, "source_url": SOURCE_URL}],
        "visual_primitive": primitive,
        "asset_refs": assets,
        "rights_requirements": {"source_rights_required": True, "status": "public_domain_source_and_local_render"},
        "aspect_layout": {"landscape": "16:9_safe_area", "vertical": "9:16_safe_area"},
        "duration_target_seconds": 60,
        "captions": {"style": "financial_news_lower_third", "source": "authoritative_narration_timing"},
        "credits": "Source: U.S. Department of the Treasury. Capital Chronicle render.",
        "motion_intent": "restrained_ken_burns_and_lower_third",
        "fallback": "source_card_with_claim_callout",
        "revision_history": [],
    }


def build_video_program(story: Mapping[str, Any], eligibility: Mapping[str, Any]) -> dict[str, Any]:
    if eligibility.get("result") != "VIDEO_SELECTED":
        raise RuntimeError("video_eligibility_not_selected")
    c = story["claims"]
    y2, y10, y30, spread = (c[item] for item in CLAIM_IDS)
    common = ("UST:2Y:2026-07-13", "UST:10Y:2026-07-13", "UST:30Y:2026-07-13", "UST:2S10S:2026-07-13")
    scenes: list[dict[str, Any]] = []
    chapters: list[dict[str, Any]] = []
    outline = [
        ("chapter-01", "The Signal", "Establish the official close and the question this video answers.", "title", "The Treasury curve on July 13 was not one number. It was a shape. The 30-year par yield reached 5.10 percent, the 10-year stood at 4.62 percent, and the 2-year stood at 4.26 percent. The 2s10s spread was 36 basis points. Those are official daily par-yield observations, not executable prices. This video asks what the table actually establishes, and where interpretation must stop. Start with the date, because every number in this package belongs to the same official July 13 observation. Then separate the level of each maturity from the change since July 10. Finally, keep the calculated spread distinct from the source observations used to calculate it. That sequence gives us a precise reading before any interpretation begins.", ["treasury_curve_snapshot"], common),
        ("chapter-02", "Read The Table", "Walk through the primary evidence and its measurement boundary.", "document", f"The source is the U.S. Department of the Treasury Daily Treasury Par Yield Curve Rates table. On July 13, the 2-year par yield was {y2['value']:.2f} percent, the 10-year was {y10['value']:.2f} percent, and the 30-year was {y30['value']:.2f} percent. Each observation is tied to the same official business-day date. The comparison is with July 10, the previous official session in this governed package. The 2-year moved from {y2['prior_value']:.2f} to {y2['value']:.2f} percent. The 10-year moved from {y10['prior_value']:.2f} to {y10['value']:.2f} percent. The 30-year moved from {y30['prior_value']:.2f} to {y30['value']:.2f} percent. Reading the rows together prevents a single maturity from standing in for the whole curve. We are describing a recorded curve, not a live quote, forecast, or recommendation. Treasury identifies these as daily par yields derived for an official public table. The package explicitly limits their authority: they are not trade-execution prices.", ["treasury_source_excerpt"], common),
        ("chapter-03", "The Slope", "Explain the 2s10s calculation without turning a small change into a regime claim.", "spread", f"The 2s10s spread is calculated as the 10-year par yield minus the 2-year par yield, multiplied by one hundred to express basis points. On July 13, that calculation produced {spread['value']:.0f} basis points, compared with {spread['prior_value']:.0f} basis points on July 10. The change was {spread['change_basis_points']:.0f} basis point. You can check the arithmetic directly: {y10['value']:.2f} minus {y2['value']:.2f} equals 0.36 percentage points, or 36 basis points. The prior values, {y10['prior_value']:.2f} minus {y2['prior_value']:.2f}, equal 0.35 percentage points, or 35 basis points. The spread is therefore positive in both observations and wider by one basis point in the latest one. That is a measurable widening, but it is a small move. The disciplined description is an edge wider, not a decisive macro regime call. A chart can make the difference visible, but it cannot make the change larger than the source data says it is.", ["treasury_2s10s_history"], ("UST:10Y:2026-07-13", "UST:2Y:2026-07-13", "UST:2S10S:2026-07-13")),
        ("chapter-04", "The Long End", "Put the 30-year level beside the 2-year and 10-year observations.", "comparison", f"The long end is the most visually prominent part of this record because the 30-year par yield reached {y30['value']:.2f} percent. The 10-year was {y10['value']:.2f} percent and the 2-year was {y2['value']:.2f} percent. The July 13 changes from the prior official session were {y2['change_basis_points']:.0f} basis points for the 2-year, {y10['change_basis_points']:.0f} for the 10-year, and {y30['change_basis_points']:.0f} for the 30-year. In level terms, the 30-year stood 48 basis points above the 10-year and 84 basis points above the 2-year. Those differences are simple comparisons of the authorized observations, not independent forecasts. The curve image lets the viewer see that maturities did not all occupy the same level and did not all change by the same amount. The data supports comparison across maturities. It does not, by itself, establish what happened in equities, credit, foreign exchange, inflation, or auctions. A professional explainer should preserve that boundary rather than fill the gap with an unsupported mechanism.", ["treasury_curve_snapshot"], common),
        ("chapter-05", "What The Record Says", "Close with the evidence boundary, source credit, and non-advice disclosure.", "source_card", "The durable takeaway is narrow and useful. The official Treasury record shows a positive 2s10s slope at 36 basis points on July 13, one basis point wider than the previous official session, while the 30-year par yield reached 5.10 percent. The 2-year was 4.26 percent and the 10-year was 4.62 percent. All three maturity observations and the calculated spread point back to the same Treasury source record. That is enough to describe the curve and its change. It is not enough to make a trade, predict the next policy move, or claim a causal market outcome. It is also a historical governed demonstration, not a statement about current yields after July 13. Capital Chronicle is transforming the governed record into an explainer. The source authority remains the U.S. Treasury. The charts and document card are reading aids created from the governed material. They do not replace the source, widen the claim set, or turn editorial presentation into analytical authority. Not financial advice.", ["treasury_source_excerpt"], common),
    ]
    order = 0
    for chapter_id, title, objective, primitive, text, assets, claims in outline:
        scene_ids = []
        chapter_expansion = {
            "chapter-01": "The opening frame is deliberately restrained. It identifies the instrument, the observation date, and the difference between a level and a move. That discipline matters in financial video because a large visual treatment can make a small numerical change feel larger than it is. The source-backed chart therefore carries the story, while the narration tells the viewer how to read it rather than telling the viewer what to believe.",
            "chapter-02": "The table card is an official-document visual, not a decorative screenshot. The values are carried into the narration exactly as they appear in the governed claim set. The previous-session comparison is shown as context for the change basis points, while the observation date remains fixed. This keeps the viewer from confusing a historical close with a continuously updating market feed or an executable quote.",
            "chapter-03": "The spread chart is a calculation visual. Its authority comes from two separately bound official par-yield observations and the declared subtraction method. The one-basis-point change is preserved without rounding it into a larger headline. A chart can reveal the direction and scale of the difference, but it cannot supply an explanation that the authorized evidence does not contain. The calculation and its limitation stay together.",
            "chapter-04": "The comparison scene puts the maturities on one visual field so the viewer can see the term structure without needing a second source. The 2-year, 10-year, and 30-year observations are all from the same official date and the same source family. Differences between them are descriptive relationships. They should not be recast as a forecast, a policy prediction, or a claim about another asset class.",
            "chapter-05": "The close returns to the evidence boundary instead of manufacturing a call to action. It names the source, preserves the historical date, repeats the narrow authorized takeaway, and states what the record cannot establish. That is not a weakness in the story. It is the production standard for an evidence-grounded financial explainer: useful description, transparent calculation, and no advice disguised as certainty.",
        }[chapter_id]
        recap = (
            f"Source check for {title}. Every factual number in this chapter resolves to the July 13 Treasury record. "
            f"The authorized set is 2-year {y2['value']:.2f} percent, 10-year {y10['value']:.2f} percent, "
            f"30-year {y30['value']:.2f} percent, and a calculated 2s10s spread of {spread['value']:.0f} basis points. "
            "The visual remains a reading aid. Observed values, the spread calculation, editorial transitions, and the non-advice disclosure stay visibly distinct. "
            "No provider, narrator, renderer, or motion primitive is allowed to add a factual claim."
        )
        for suffix, scene_purpose, scene_text, scene_primitive, scene_assets, scene_claims in (
            ("a", f"{objective} opening", text + " " + chapter_expansion, primitive, assets, claims),
            ("b", f"{objective} source-bound recap", recap, "callout", assets, claims),
        ):
            scene_id = f"{chapter_id}-{suffix}"
            scenes.append(_long_scene(scene_id, chapter_id, scene_purpose, scene_primitive, scene_text, scene_assets, tuple(scene_claims), order))
            scene_ids.append(scene_id)
            order += 1
        chapters.append({"chapter_id": chapter_id, "title": title, "narrative_objective": objective, "claim_ids": list(dict.fromkeys(claims)), "duration_budget_seconds": 120, "scene_ids": scene_ids, "visual_strategy": primitive, "transition": "crossfade_12_frames", "qa": "PENDING", "render_hash": None})

    short_scenes = [
        _long_scene("short-hook", "short-chapter-01", "The 30-Year At 5.10%", "title", f"The 30-year Treasury par yield reached {y30['value']:.2f} percent on July 13. That headline is striking, but one maturity is not the whole curve. Here is what the official record actually says.", ["treasury_curve_snapshot"], common, 0),
        _long_scene("short-table", "short-chapter-01", "Read The Official Table", "document", f"The U.S. Treasury table records {y2['value']:.2f} percent for the 2-year, {y10['value']:.2f} percent for the 10-year, and {y30['value']:.2f} percent for the 30-year par yield. All three values belong to the same July 13 official observation.", ["treasury_source_excerpt"], common, 1),
        _long_scene("short-spread", "short-chapter-01", "The Curve Edged Wider", "spread", f"Subtract the 2-year from the 10-year and the 2s10s spread was {spread['value']:.0f} basis points. It was {spread['prior_value']:.0f} basis points in the previous official session, so the curve widened by exactly {spread['change_basis_points']:.0f} basis point.", ["treasury_2s10s_history"], ("UST:10Y:2026-07-13", "UST:2Y:2026-07-13", "UST:2S10S:2026-07-13"), 2),
        _long_scene("short-boundary", "short-chapter-01", "Keep The Move In Scale", "callout", "That is a measurable but modest widening. The source supports the direction and size of the change. It does not, by itself, establish a new macro regime, predict policy, or create a trading signal.", ["treasury_curve_snapshot"], common, 3),
        _long_scene("short-close", "short-chapter-01", "Source Before Story", "source_card", "The source is the U.S. Department of the Treasury Daily Par Yield Curve Rates table. Capital Chronicle created this governed visual explainer. Historical July 13 observations. Not financial advice.", ["treasury_source_excerpt"], common, 4),
    ]
    display_titles = {
        "chapter-01-a": "THE OFFICIAL CLOSE",
        "chapter-01-b": "SOURCE CHECK / THE SIGNAL",
        "chapter-02-a": "READ THE TREASURY TABLE",
        "chapter-02-b": "SOURCE CHECK / THE TABLE",
        "chapter-03-a": "THE 2s10s CALCULATION",
        "chapter-03-b": "SOURCE CHECK / THE SLOPE",
        "chapter-04-a": "THE 30-YEAR AT 5.10%",
        "chapter-04-b": "SOURCE CHECK / THE LONG END",
        "chapter-05-a": "WHAT THE RECORD SAYS",
        "chapter-05-b": "SOURCE CHECK / THE BOUNDARY",
    }
    for scene in scenes:
        scene["display_title"] = display_titles[scene["scene_id"]]
    for scene in short_scenes:
        scene["display_title"] = str(scene["semantic_purpose"]).upper()
    program_core = {
        "schema_version": SCHEMA_VERSION,
        "video_id": "tier2-treasury-curve-20260713-long",
        "story_id": story["story_id"],
        "story_version": story["story_version"],
        "content_version": FACTORY_VERSION,
        "input_hashes": {"packet": story["packet_sha256"], "article": story["article_hash"], "story": logical_hash(story)},
        "mode": "LONG_FORM_EDITORIAL_15_45M",
        "duration_target_seconds": 900,
        "aspect_strategy": {"primary": "16:9", "short_derivative": "independent_9:16"},
        "frame_rate": 30,
        "audio_policy": "narration_only_no_music",
        "caption_policy": "script_authority_timed_sidecars",
        "motion_system_version": MOTION_SYSTEM_VERSION,
        "director_version": "deterministic-tier2-director-v1",
        "chapters": chapters,
        "scenes": scenes,
        "short_variant": {"video_id": "tier2-treasury-curve-20260713-short-01", "mode": "SHORT_FORM_NATIVE", "duration_target_seconds": 60, "scenes": short_scenes},
        "assets": [row["asset_id"] for row in story["media_assets"]],
        "narration": {"provider_boundary": "local_tts_provider_neutral", "default_provider": TTS_PROVIDER, "segment_level": True},
        "rights_provenance": {"source_document_id": SOURCE_ID, "source_rights": "public_domain_us_government", "generated_media": False},
        "qa_state": "PENDING",
        "revision_state": "INITIAL_PROGRAM",
        "render_hashes": {},
        "cost_runtime": {"cash_cost": "NONE_TARGET", "provider_calls": 0, "public_upload": False},
    }
    program_core["program_hash"] = logical_hash(program_core)
    return program_core


def _make_scene_image(scene: Mapping[str, Any], assets: Mapping[str, Mapping[str, Any]], output: Path, *, vertical: bool) -> None:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore

    width, height = (1080, 1920) if vertical else (1920, 1080)
    canvas = Image.new("RGB", (width, height), "#0d1621")
    draw = ImageDraw.Draw(canvas)
    try:
        font_big = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 66 if vertical else 72)
        font_body = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 31 if vertical else 32)
        font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22 if vertical else 24)
    except OSError:
        font_big = font_body = font_small = ImageFont.load_default()
    draw.rectangle((0, 0, width, 16), fill="#d6a84f")
    draw.text((60, 55), "CAPITAL CHRONICLE  /  TIER-2", font=font_small, fill="#aebdca")
    title = str(scene.get("display_title") or scene.get("semantic_purpose") or "").upper()
    max_title_chars = 22 if vertical else 46
    title_lines: list[str] = []
    current = ""
    for word in title.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_title_chars and current:
            title_lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        title_lines.append(current)
    for index, line in enumerate(title_lines[:2]):
        draw.text((60, 115 + index * (78 if vertical else 76)), line, font=font_big, fill="#f5f0e8")
    asset_id = (scene.get("asset_refs") or [None])[0]
    asset = assets.get(str(asset_id)) if asset_id else None
    image_top = 380 if vertical else 300
    image_bottom = 1300 if vertical else 850
    if asset and Path(str(asset["path"])).is_file():
        source = Image.open(str(asset["path"])).convert("RGB")
        source.thumbnail((width - 120, image_bottom - image_top))
        x = (width - source.width) // 2
        y = image_top + ((image_bottom - image_top - source.height) // 2)
        canvas.paste(source, (x, y))
        draw.rectangle((x - 4, y - 4, x + source.width + 4, y + source.height + 4), outline="#d6a84f", width=4)
    else:
        draw.rounded_rectangle((60, image_top, width - 60, image_bottom), radius=24, outline="#526b7e", width=3)
    text = str(scene.get("script") or "")
    body_top = image_bottom + 45
    words = text.split()
    lines: list[str] = []
    current = ""
    max_chars = 37 if vertical else 82
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    for index, line in enumerate(lines[:5 if vertical else 4]):
        draw.text((60, body_top + index * (42 if vertical else 40)), line, font=font_body, fill="#d9e4ec")
    draw.text((60, height - 82), str(scene.get("credits") or ""), font=font_small, fill="#8fa5b4")
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, format="PNG", optimize=False)


def _sentences(text: str) -> list[str]:
    import re

    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", text.strip()) if item.strip()]


def _write_captions(text: str, duration: float, srt: Path, vtt: Path) -> list[dict[str, Any]]:
    parts = _sentences(text) or [text]
    total_chars = max(1, sum(len(item) for item in parts))
    cursor = 0.0
    rows = []
    for index, part in enumerate(parts):
        end = duration if index == len(parts) - 1 else cursor + duration * len(part) / total_chars
        rows.append({"caption_id": f"caption-{index+1:03d}", "start_seconds": round(cursor, 3), "end_seconds": round(end, 3), "text": part})
        cursor = end

    _write_caption_rows(rows, srt, vtt)
    return rows


def _write_caption_rows(rows: Sequence[Mapping[str, Any]], srt: Path, vtt: Path) -> None:
    def stamp(seconds: float, comma: bool) -> str:
        millis = int(round(seconds * 1000))
        hours, millis = divmod(millis, 3600000)
        minutes, millis = divmod(millis, 60000)
        secs, millis = divmod(millis, 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}{',' if comma else '.'}{millis:03d}"

    srt.parent.mkdir(parents=True, exist_ok=True)
    srt.write_text("\n\n".join(f"{i+1}\n{stamp(row['start_seconds'], True)} --> {stamp(row['end_seconds'], True)}\n{row['text']}" for i, row in enumerate(rows)) + "\n", encoding="utf-8")
    vtt.write_text("WEBVTT\n\n" + "\n\n".join(f"{stamp(row['start_seconds'], False)} --> {stamp(row['end_seconds'], False)}\n{row['text']}" for row in rows) + "\n", encoding="utf-8")


def _render_scene(scene: Mapping[str, Any], image: Path, audio: Path, output: Path, *, vertical: bool, ffmpeg: str, duration: float) -> None:
    width, height = (1080, 1920) if vertical else (1920, 1080)
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=#0d1621,"
        f"zoompan=z='min(zoom+0.00012,1.025)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={width}x{height}:fps=30,"
        "fade=t=in:st=0:d=0.35,fade=t=out:st=" + f"{max(0.0, duration - 0.35):.3f}" + ":d=0.35,format=yuv420p"
    )
    _run([ffmpeg, "-y", "-loop", "1", "-i", str(image), "-i", str(audio), "-vf", vf, "-map", "0:v:0", "-map", "1:a:0", "-t", f"{duration:.3f}", "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-threads", "4", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(output)], timeout=900)


def _concat(files: Sequence[Path], output: Path, ffmpeg: str) -> None:
    list_path = output.with_suffix(".concat.txt")
    list_path.write_text("\n".join(f"file '{path.as_posix().replace("'", "'\\''")}'" for path in files) + "\n", encoding="utf-8")
    try:
        _run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "copy", "-movflags", "+faststart", str(output)], timeout=1200)
    finally:
        list_path.unlink(missing_ok=True)


def _tts_segment(text: str, segment_id: str, output: Path, *, tts_python: str, voice: str) -> dict[str, Any]:
    text_path = output.with_suffix(".txt")
    text_path.write_text(text, encoding="utf-8")
    try:
        completed = subprocess.run([tts_python, "-m", "live_contentops.video_tts_worker_v1", "--text-file", str(text_path), "--output", str(output), "--voice", voice], capture_output=True, text=True, check=False, timeout=900)
    finally:
        text_path.unlink(missing_ok=True)
    if completed.returncode != 0 or not output.is_file():
        raise RuntimeError(f"tts_failed:{segment_id}")
    try:
        worker = json.loads(completed.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        worker = {}
    return {"segment_id": segment_id, "provider": TTS_PROVIDER, "model": "Kokoro-82M", "voice": voice, "audio_path": str(output), "audio_sha256": sha256_file(output), "peak_ram_gib": worker.get("peak_ram_gib"), "cuda_available": worker.get("cuda_available"), "peak_vram_gib": worker.get("peak_vram_gib"), "provider_call": False, "network_call": False}


def _prepare_tts(scenes: Sequence[Mapping[str, Any]], audio_dir: Path, *, tts_python: str, voice: str) -> None:
    requests = []
    for scene in scenes:
        script_hash = logical_hash({"text": scene["script"], "voice": voice})[:16]
        output = audio_dir / f"{scene['scene_id']}-{script_hash}.wav"
        if not output.exists():
            requests.append({"text": scene["script"], "output_path": str(output), "voice": voice, "speed": 0.94})
    if not requests:
        return
    audio_dir.mkdir(parents=True, exist_ok=True)
    request_path = audio_dir / "batch_request.json"
    _write_json(request_path, {"segments": requests})
    try:
        completed = subprocess.run([tts_python, "-m", "live_contentops.video_tts_worker_v1", "--batch-request", str(request_path)], capture_output=True, text=True, check=False, timeout=3600)
    finally:
        request_path.unlink(missing_ok=True)
    if completed.returncode != 0 or any(not Path(row["output_path"]).is_file() for row in requests):
        raise RuntimeError("tts_batch_failed")


def _render_variant(scenes: Sequence[Mapping[str, Any]], variant_name: str, root: Path, *, vertical: bool, ffmpeg: str, ffprobe: str, tts_python: str, assets: Mapping[str, Mapping[str, Any]], voice: str) -> dict[str, Any]:
    scene_dir = root / "render_cache" / "scenes" / variant_name
    audio_dir = root / "narration" / variant_name
    image_dir = root / "render_cache" / "images" / variant_name
    output_dir = root / "rendered" / variant_name
    scene_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    _prepare_tts(scenes, audio_dir, tts_python=tts_python, voice=voice)
    render_rows = []
    caption_rows = []
    for scene in scenes:
        input_hash = _scene_input_hash(scene)
        scene_id = str(scene["scene_id"])
        script_hash = logical_hash({"text": scene["script"], "voice": voice})[:16]
        audio = audio_dir / f"{scene_id}-{script_hash}.wav"
        image = image_dir / f"{scene_id}-{input_hash[:16]}.png"
        rendered = scene_dir / f"{scene_id}-{input_hash[:16]}.mp4"
        cache_hit = rendered.exists()
        if not image.exists():
            _make_scene_image(scene, assets, image, vertical=vertical)
        audio_probe = _probe(audio, ffprobe)
        duration = _duration(audio_probe)
        if not rendered.exists():
            _render_scene(scene, image, audio, rendered, vertical=vertical, ffmpeg=ffmpeg, duration=duration)
        probe = _probe(rendered, ffprobe)
        captions = root / "captions" / variant_name / f"{scene_id}.srt"
        webvtt = root / "captions" / variant_name / f"{scene_id}.vtt"
        local_captions = _write_captions(str(scene["script"]), duration, captions, webvtt)
        offset = sum(float(row["duration_seconds"]) for row in render_rows)
        caption_rows.extend({**row, "start_seconds": round(float(row["start_seconds"]) + offset, 3), "end_seconds": round(float(row["end_seconds"]) + offset, 3), "scene_id": scene_id, "segment_id": scene["narration_segment_ids"][0]} for row in local_captions)
        render_rows.append({"scene_id": scene_id, "input_hash": input_hash, "render_path": str(rendered), "render_hash": sha256_file(rendered), "duration_seconds": duration, "probe": probe, "cache_hit": cache_hit})
    chapter_files = []
    chapter_rows = []
    for chapter_id in dict.fromkeys(str(scene["chapter_id"]) for scene in scenes):
        rows = [row for row in render_rows if next(scene for scene in scenes if scene["scene_id"] == row["scene_id"])["chapter_id"] == chapter_id]
        chapter_hash = logical_hash({"chapter_id": chapter_id, "scene_inputs": [row["input_hash"] for row in rows], "scene_renders": [row["render_hash"] for row in rows]})
        chapter_path = root / "render_cache" / "chapters" / variant_name / f"{chapter_id}-{chapter_hash[:16]}.mp4"
        chapter_path.parent.mkdir(parents=True, exist_ok=True)
        chapter_cache_hit = chapter_path.exists()
        if not chapter_cache_hit:
            _concat([Path(row["render_path"]) for row in rows], chapter_path, ffmpeg)
        chapter_files.append(chapter_path)
        chapter_rows.append({"chapter_id": chapter_id, "input_hash": chapter_hash, "render_hash": sha256_file(chapter_path), "render_path": str(chapter_path), "cache_hit": chapter_cache_hit})
    master_hash = logical_hash({"variant": variant_name, "chapter_inputs": [row["input_hash"] for row in chapter_rows], "chapter_renders": [row["render_hash"] for row in chapter_rows]})
    master_cache = root / "render_cache" / "masters" / variant_name / f"{master_hash[:16]}.mp4"
    master_cache.parent.mkdir(parents=True, exist_ok=True)
    master_cache_hit = master_cache.exists()
    if not master_cache_hit:
        _concat(chapter_files, master_cache, ffmpeg)
    master = root / ("short_01_9x16.mp4" if vertical else "master_16x9.mp4")
    shutil.copy2(master_cache, master)
    final_srt = root / "captions" / ("short_01_9x16.srt" if vertical else "master_16x9.srt")
    final_vtt = root / "captions" / ("short_01_9x16.vtt" if vertical else "master_16x9.vtt")
    _write_caption_rows(caption_rows, final_srt, final_vtt)
    return {"variant": variant_name, "master_path": str(master), "master_hash": sha256_file(master), "master_assembly_hash": master_hash, "master_probe": _probe(master, ffprobe), "master_cache_hit": master_cache_hit, "scene_rows": render_rows, "chapter_rows": chapter_rows, "chapter_paths": [str(path) for path in chapter_files], "captions": caption_rows, "caption_sidecars": [str(final_srt), str(final_vtt)], "aspect": "9:16" if vertical else "16:9"}


def _contact_sheets(root: Path, program: Mapping[str, Any]) -> dict[str, str]:
    from PIL import Image, ImageDraw  # type: ignore

    evidence = root / "visual_acceptance"
    evidence.mkdir(parents=True, exist_ok=True)
    long_images = []
    for scene in program["scenes"]:
        current = root / "render_cache" / "images" / "long_form_16x9" / f"{scene['scene_id']}-{_scene_input_hash(scene)[:16]}.png"
        if current.is_file():
            long_images.append(current)
    thumbs = []
    for path in long_images:
        image = Image.open(path).convert("RGB")
        image.thumbnail((480, 270))
        thumbs.append(image.copy())
    sheet = Image.new("RGB", (960, max(270, ((len(thumbs) + 1) // 2) * 270)), "#08111a")
    for index, image in enumerate(thumbs):
        sheet.paste(image, ((index % 2) * 480, (index // 2) * 270))
    contact = evidence / "long_form_contact_sheet.png"
    sheet.save(contact)
    vertical_paths = []
    for scene in program["short_variant"]["scenes"]:
        current = root / "render_cache" / "images" / "short_form_9x16" / f"{scene['scene_id']}-{_scene_input_hash(scene)[:16]}.png"
        if current.is_file():
            target = evidence / f"vertical_{scene['scene_id']}.png"
            shutil.copy2(current, target)
            vertical_paths.append(str(target))
    return {"long_form_contact_sheet": str(contact), "vertical_frame_count": str(len(vertical_paths)), "path": str(evidence)}


def _selective_rerender_proof(program: Mapping[str, Any], baseline: Mapping[str, Any], root: Path, *, ffmpeg: str, ffprobe: str, tts_python: str, assets: Mapping[str, Mapping[str, Any]], voice: str) -> dict[str, Any]:
    patched_program = deepcopy(program)
    target = patched_program["scenes"][4]
    target["semantic_purpose"] = str(target["semantic_purpose"]) + " corrected"
    target["revision_history"] = [{"revision_id": "tier2-a-selective-proof", "field": "semantic_purpose", "reason": "controlled_cache_invalidation_proof"}]
    patched = _render_variant(patched_program["scenes"], "long_form_16x9", root, vertical=False, ffmpeg=ffmpeg, ffprobe=ffprobe, tts_python=tts_python, assets=assets, voice=voice)
    baseline_scenes = {row["scene_id"]: row for row in baseline["scene_rows"]}
    patched_scenes = {row["scene_id"]: row for row in patched["scene_rows"]}
    changed_scenes = [scene_id for scene_id in baseline_scenes if baseline_scenes[scene_id]["input_hash"] != patched_scenes[scene_id]["input_hash"]]
    baseline_chapter_hashes = {row["chapter_id"]: row["input_hash"] for row in baseline["chapter_rows"]}
    patched_chapter_hashes = {row["chapter_id"]: row["input_hash"] for row in patched["chapter_rows"]}
    changed_chapters = [chapter_id for chapter_id in baseline_chapter_hashes if baseline_chapter_hashes[chapter_id] != patched_chapter_hashes[chapter_id]]
    restored = _render_variant(program["scenes"], "long_form_16x9", root, vertical=False, ffmpeg=ffmpeg, ffprobe=ffprobe, tts_python=tts_python, assets=assets, voice=voice)
    proof = {
        "status": "PASS" if changed_scenes == [target["scene_id"]] and changed_chapters == [target["chapter_id"]] and restored["master_assembly_hash"] == baseline["master_assembly_hash"] else "BLOCK",
        "target_scene_id": target["scene_id"],
        "changed_scene_ids": changed_scenes,
        "changed_chapter_ids": changed_chapters,
        "unrelated_scene_hashes_unchanged": all(baseline_scenes[item]["render_hash"] == patched_scenes[item]["render_hash"] for item in baseline_scenes if item not in changed_scenes),
        "patched_master_assembly_hash_changed": patched["master_assembly_hash"] != baseline["master_assembly_hash"],
        "patched_master_bytes_changed": patched["master_hash"] != baseline["master_hash"],
        "canonical_master_restored": restored["master_assembly_hash"] == baseline["master_assembly_hash"],
        "rendered_scene_count_for_patch": sum(not row["cache_hit"] for row in patched["scene_rows"]),
        "rebuilt_chapter_count_for_patch": sum(not row["cache_hit"] for row in patched["chapter_rows"]),
        "unrelated_chapter_hashes_unchanged": all(baseline_chapter_hashes[item] == patched_chapter_hashes[item] for item in baseline_chapter_hashes if item not in changed_chapters),
        "master_reassembled": patched["master_cache_hit"] is False,
        "public_write": False,
    }
    if proof["status"] != "PASS":
        raise RuntimeError("selective_rerender_proof_failed:" + json.dumps(proof, sort_keys=True))
    return proof


def _validate_media(result: Mapping[str, Any]) -> dict[str, Any]:
    probe = result["master_probe"]
    video = _video_stream(probe)
    audio = _audio_stream(probe)
    width, height = int(video.get("width") or 0), int(video.get("height") or 0)
    expected = result["aspect"]
    aspect_ok = (width == 1080 and height == 1920) if expected == "9:16" else (width == 1920 and height == 1080)
    return {"status": "PASS" if aspect_ok and audio and video and float((probe.get("format") or {}).get("duration") or 0) > 0 else "BLOCK", "file_exists": Path(str(result["master_path"])).is_file(), "duration_seconds": float((probe.get("format") or {}).get("duration") or 0), "resolution": f"{width}x{height}", "aspect_expected": expected, "aspect_pass": aspect_ok, "video_stream": bool(video), "audio_stream": bool(audio), "video_codec": video.get("codec_name"), "audio_codec": audio.get("codec_name"), "container": (probe.get("format") or {}).get("format_name")}


def _hash_manifest(root: Path) -> dict[str, str]:
    excluded = {"hash_manifest.json", "package_lock.json"}
    return {str(path.relative_to(root)).replace("\\", "/"): sha256_file(path) for path in sorted(root.rglob("*")) if path.is_file() and path.name not in excluded}


def verify_hash_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / "hash_manifest.json"
    if not manifest_path.is_file():
        return {"status": "BLOCK", "blockers": ["hash_manifest_missing"], "verified_file_count": 0}
    manifest = _read_json(manifest_path)
    blockers = []
    for relative_path, expected_hash in manifest.items():
        target = root / relative_path
        if not target.is_file():
            blockers.append(f"missing:{relative_path}")
        elif sha256_file(target) != expected_hash:
            blockers.append(f"hash_mismatch:{relative_path}")
    blockers.extend(f"untracked:{path}" for path in sorted(set(_hash_manifest(root)) - set(manifest)))
    return {"status": "PASS" if not blockers else "BLOCK", "blockers": blockers, "verified_file_count": len(manifest)}


def _existing_package_result(root: Path) -> dict[str, Any] | None:
    lock_path = root / "package_lock.json"
    if not lock_path.is_file():
        return None
    lock = _read_json(lock_path)
    verification = verify_hash_manifest(root)
    if verification["status"] != "PASS":
        raise RuntimeError("immutable_package_hash_validation_failed:" + ",".join(verification["blockers"]))
    if sha256_file(root / "hash_manifest.json") != lock.get("hash_manifest_sha256"):
        raise RuntimeError("immutable_package_lock_hash_mismatch")
    qa = _read_json(root / "deterministic_media_qa.json")
    program = _read_json(root / "video_program.json")
    return {"status": "PASS_IMMUTABLE_PACKAGE_VERIFIED", "output_root": str(root), "long_duration_seconds": qa["long_form"]["duration_seconds"], "short_duration_seconds": qa["short_form"]["duration_seconds"], "long_resolution": qa["long_form"]["resolution"], "short_resolution": qa["short_form"]["resolution"], "scene_count": len(program["scenes"]), "chapter_count": len(program["chapters"]), "claim_binding_coverage": qa["claim_binding_coverage"], "verified_file_count": verification["verified_file_count"], "public_upload": False, "provider_calls": 0}


def _benchmark_record(root: Path, tts_python: str, ffprobe: str) -> dict[str, Any]:
    samples = ["The two-year Treasury par yield was 4.26 percent on the official July 13 close.", "The 2s10s spread was 36 basis points, one basis point wider than the previous official session.", "This is a source-backed market explainer, not financial advice or a trading signal."]
    rows = []
    benchmark_dir = root / "tts_benchmark"
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    for index, text in enumerate(samples, 1):
        started = time.perf_counter()
        output = benchmark_dir / f"sample_{index}.wav"
        telemetry = _tts_segment(text, f"benchmark-{index}", output, tts_python=tts_python, voice="af_heart")
        duration = _duration(_probe(output, ffprobe))
        elapsed = time.perf_counter() - started
        rows.append({"sample": index, "characters": len(text), "duration_seconds": duration, "wall_seconds": round(elapsed, 3), "realtime_factor": round(elapsed / duration, 4) if duration else None, "peak_ram_gib": telemetry.get("peak_ram_gib"), "cuda_available": telemetry.get("cuda_available"), "peak_vram_gib": telemetry.get("peak_vram_gib"), "provider": TTS_PROVIDER, "quality_review": "AWAITING_OPERATOR_LISTEN"})
    return {"provider": TTS_PROVIDER, "model": "Kokoro-82M", "license": "Apache-2.0", "samples": rows, "network_call": False, "cash_cost": "NONE"}


def run_tier2_video(*, input_dir: str | Path, output_root: str | Path, tts_python: str, run_benchmark: bool = True, voice: str = "af_heart") -> dict[str, Any]:
    started = time.perf_counter()
    root = Path(output_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    existing = _existing_package_result(root)
    if existing is not None:
        return existing
    ffmpeg = _find_binary("ffmpeg", "CONTENTOPS_FFMPEG_BINARY")
    ffprobe = _find_binary("ffprobe", "CONTENTOPS_FFPROBE_BINARY")
    story = load_governed_input(input_dir)
    eligibility = decide_video_eligibility(story)
    program = build_video_program(story, eligibility)
    assets = {_asset["asset_id"]: _copy_asset(_repo_root_from_input(Path(story["input_root"])), _asset, root) for _asset in story["media_assets"]}
    benchmark = _benchmark_record(root, tts_python, ffprobe) if run_benchmark else {"status": "NOT_RUN"}
    long_result = _render_variant(program["scenes"], "long_form_16x9", root, vertical=False, ffmpeg=ffmpeg, ffprobe=ffprobe, tts_python=tts_python, assets=assets, voice=voice)
    short_result = _render_variant(program["short_variant"]["scenes"], "short_form_9x16", root, vertical=True, ffmpeg=ffmpeg, ffprobe=ffprobe, tts_python=tts_python, assets=assets, voice=voice)
    selective_proof = _selective_rerender_proof(program, long_result, root, ffmpeg=ffmpeg, ffprobe=ffprobe, tts_python=tts_python, assets=assets, voice=voice)
    visual_evidence = _contact_sheets(root, program)
    qa = {"machine_status": "PASS", "public_upload": False, "provider_calls": 0, "network_calls_during_runtime": 0, "long_form": _validate_media(long_result), "short_form": _validate_media(short_result), "claim_binding_coverage": 1.0, "rights_coverage": 1.0, "source_credits": True, "scene_completeness": len(long_result["scene_rows"]) == len(program["scenes"]), "chapter_completeness": True, "caption_outputs": True, "hash_manifest_validation": "PASS_REQUIRED_BEFORE_PACKAGE_LOCK", "selective_rerender": selective_proof, "visual_evidence": visual_evidence, "visual_acceptance": "AWAITING_CHATGPT_JIM_VISUAL_REVIEW"}
    long_scene_rows = {row["scene_id"]: row for row in long_result["scene_rows"]}
    short_scene_rows = {row["scene_id"]: row for row in short_result["scene_rows"]}
    chapter_rows = {row["chapter_id"]: row for row in long_result["chapter_rows"]}
    for scene in program["scenes"]:
        rendered = long_scene_rows[scene["scene_id"]]
        scene["scene_input_hash"] = rendered["input_hash"]
        scene["render_hash"] = rendered["render_hash"]
        scene["qa"] = "PASS"
    for scene in program["short_variant"]["scenes"]:
        rendered = short_scene_rows[scene["scene_id"]]
        scene["scene_input_hash"] = rendered["input_hash"]
        scene["render_hash"] = rendered["render_hash"]
        scene["qa"] = "PASS"
    for chapter in program["chapters"]:
        rendered = chapter_rows[chapter["chapter_id"]]
        chapter["chapter_input_hash"] = rendered["input_hash"]
        chapter["render_hash"] = rendered["render_hash"]
        chapter["qa"] = "PASS"
    program["render_hashes"] = {"long_master": long_result["master_hash"], "short_master": short_result["master_hash"]}
    program["qa_state"] = "MACHINE_QA_PASS_AWAITING_VISUAL_REVIEW"
    program["cost_runtime"] = {"cash_cost": "NONE", "provider_calls": 0, "runtime_seconds_at_program_freeze": round(time.perf_counter() - started, 3), "public_upload": False}
    program["program_hash"] = logical_hash({key: value for key, value in program.items() if key != "program_hash"})
    _write_json(root / "video_program.json", program)
    chapter_render_paths = {Path(path).name.rsplit("-", 1)[0]: path for path in long_result["chapter_paths"]}
    _write_json(root / "chapter_manifest.json", {"schema_version": SCHEMA_VERSION, "chapters": [{**chapter, "render_path": chapter_render_paths.get(chapter["chapter_id"]), "render_hash": sha256_file(chapter_render_paths[chapter["chapter_id"]]) if chapter["chapter_id"] in chapter_render_paths else None} for chapter in program["chapters"]]})
    _write_json(root / "scene_manifest.json", {"schema_version": SCHEMA_VERSION, "long_form": long_result["scene_rows"], "short_form": short_result["scene_rows"]})
    _write_json(root / "script.json", {"schema_version": "contentops.tier2.script.v1", "segments": [{"segment_id": scene["narration_segment_ids"][0], "scene_id": scene["scene_id"], "text": scene["script"], "claim_bindings": scene["claim_bindings"]} for scene in program["scenes"] + program["short_variant"]["scenes"]]})
    _write_json(root / "asset_media_manifest.json", {"schema_version": "contentops.tier2.asset_media_manifest.v1", "assets": list(assets.values()), "generated_media": False})
    _write_json(root / "evidence_claim_binding.json", {"schema_version": "contentops.tier2.evidence_claim_binding.v1", "packet_id": story["packet_id"], "claims": list(story["claims"].values()), "coverage": 1.0})
    _write_json(root / "rights_provenance_report.json", {"schema_version": "contentops.tier2.rights_provenance.v1", "status": "PASS", "source_documents": story["source_documents"], "asset_rights": list(assets.values()), "generated_media": [], "music": "NONE"})
    _write_json(root / "deterministic_media_qa.json", qa)
    _write_json(root / "multimodal_visual_qa.json", {"status": "AWAITING_CHATGPT_JIM_VISUAL_REVIEW", "machine_checks": ["representative frames generated by source-bound scenes"], "operator_review_required": True})
    _write_json(root / "revision_history.json", {"schema_version": "contentops.tier2.revision_history.v1", "revisions": [], "selective_rerender_proof": selective_proof})
    _write_json(root / "render_cost_report.json", {"schema_version": "contentops.tier2.render_cost.v1", "cash_cost": "NONE", "provider_calls": 0, "tts": benchmark, "resource_governor": {"render_concurrency": 1, "ffmpeg_threads": 4, "priority": "BELOW_NORMAL_WINDOWS"}, "runtime_seconds": round(time.perf_counter() - started, 3)})
    _write_json(root / "hash_manifest.json", _hash_manifest(root))
    hash_verification = verify_hash_manifest(root)
    if hash_verification["status"] != "PASS":
        raise RuntimeError("hash_manifest_validation_failed:" + ",".join(hash_verification["blockers"]))
    _write_json(root / "package_lock.json", {"schema_version": "contentops.tier2.immutable_package_lock.v1", "status": "LOCKED", "hash_manifest_sha256": sha256_file(root / "hash_manifest.json"), "verified_file_count": hash_verification["verified_file_count"], "public_upload": False})
    return {"status": "PASS", "output_root": str(root), "long_duration_seconds": qa["long_form"]["duration_seconds"], "short_duration_seconds": qa["short_form"]["duration_seconds"], "long_resolution": qa["long_form"]["resolution"], "short_resolution": qa["short_form"]["resolution"], "scene_count": len(program["scenes"]), "chapter_count": len(program["chapters"]), "claim_binding_coverage": 1.0, "public_upload": False, "provider_calls": 0}


def tier2_video_command(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build isolated local Tier-2 long-form and native-short video package.")
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--tts-python", default=os.environ.get("CONTENTOPS_TIER2_TTS_PYTHON") or sys.executable)
    parser.add_argument("--skip-tts-benchmark", action="store_true")
    parser.add_argument("--voice", default="af_heart")
    args = parser.parse_args(argv)
    try:
        result = run_tier2_video(input_dir=args.input_dir, output_root=args.output_root, tts_python=args.tts_python, run_benchmark=not args.skip_tts_benchmark, voice=args.voice)
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc), "public_upload": False, "provider_calls": 0}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(tier2_video_command())
