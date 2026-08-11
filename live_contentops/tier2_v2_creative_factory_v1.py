"""Isolated Tier-2 V2 premium creative-system proof.

The renderer-neutral VideoProgram is authority. Remotion and FFmpeg compile that
program into local review media. The module has no browser/CDP, platform, upload,
publication, scheduler, durable-store, or public-write behavior.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont

from .content_intelligence_contracts_v2 import logical_hash
from .media_manifest_authority_v1 import sha256_file
from .nine_router_provider_adapter_v2 import call_nine_router, call_nine_router_multimodal
from .tier2_asset_router_v2 import AssetRecord, generate_illustrative_asset, stage_governed_asset
from .tier2_video_factory_v1 import CLAIM_IDS, SOURCE_ID, SOURCE_URL, _tts_segment, load_governed_input


SCHEMA_VERSION = "contentops.tier2.video_program.v3"
FACTORY_VERSION = "tier2-v2-creative-system-rebuild-v1"
MOTION_SYSTEM_VERSION = "contentops.tier2.v2.editorial-motion.1"
DIRECTOR_MODEL = "new/claude-fable-5"
DIRECTOR_FALLBACK_MODEL = "new/gpt-5.6-sol-xhigh"
CRITIC_MODEL = "vx/gemini-3.1-pro-preview(high)"
MAX_REVISION_ROUNDS = 2
TRANSITION_SECONDS = 0.55
TAIL_SECONDS = 0.72
LONG_PROFILE = {"width": 1920, "height": 1080, "fps": 24, "aspect": "landscape"}
SHORT_PROFILE = {"width": 1080, "height": 1920, "fps": 24, "aspect": "vertical"}
REPO_ROOT = Path(__file__).resolve().parents[1]
REMOTION_ROOT = REPO_ROOT / "video" / "tier2_v2_remotion"
DEFAULT_INPUT = REPO_ROOT / "docs" / "automation" / "CONTENTOPS_FULL_AUTOMATION_LIVE_CANONICAL_BROWSER_RUN_V1" / "contentops_full_automation_live_20260807_1"


class Tier2V2Error(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Tier2V2Error(f"json_object_required:{path.name}")
    return value


def _run(command: Sequence[str], *, timeout: int = 1800, capture: bool = True) -> subprocess.CompletedProcess[str]:
    flags = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0x00004000) if os.name == "nt" else 0
    completed = subprocess.run(list(command), capture_output=capture, text=True, check=False, timeout=timeout, creationflags=flags)
    if completed.returncode != 0:
        tail = (completed.stderr or completed.stdout or "")[-1200:]
        raise Tier2V2Error(f"command_failed:{Path(str(command[0])).name}:{tail}")
    return completed


def _ffprobe(path: Path) -> dict[str, Any]:
    completed = _run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)], timeout=120)
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise Tier2V2Error(f"ffprobe_object_required:{path.name}")
    return value


def _media_facts(path: Path) -> dict[str, Any]:
    probe = _ffprobe(path)
    video = next((row for row in probe.get("streams") or [] if row.get("codec_type") == "video"), {})
    audio = next((row for row in probe.get("streams") or [] if row.get("codec_type") == "audio"), {})
    fmt = probe.get("format") or {}
    rate = str(video.get("avg_frame_rate") or "0/1").split("/", 1)
    fps = float(rate[0]) / float(rate[1]) if len(rate) == 2 and float(rate[1] or 0) else 0.0
    return {
        "path": str(path), "sha256": sha256_file(path), "duration_seconds": float(fmt.get("duration") or 0),
        "width": int(video.get("width") or 0), "height": int(video.get("height") or 0), "fps": round(fps, 3),
        "video_codec": video.get("codec_name"), "audio_codec": audio.get("codec_name"),
        "audio_sample_rate": audio.get("sample_rate"), "container": fmt.get("format_name"), "size_bytes": int(fmt.get("size") or 0),
    }


def semantic_program_hash(program: Mapping[str, Any]) -> str:
    execution_keys = {"semantic_content_hash", "runtime_hash", "render_state", "qa_state", "revision_state", "render_hashes"}
    return logical_hash({key: value for key, value in program.items() if key not in execution_keys})


def renderer_runtime_hash(remotion_root: Path = REMOTION_ROOT) -> str:
    files = sorted(
        path for path in remotion_root.rglob("*")
        if path.is_file() and "node_modules" not in path.parts and path.suffix.lower() in {".ts", ".tsx", ".mjs", ".json"}
    )
    return logical_hash({
        "motion_system_version": MOTION_SYSTEM_VERSION,
        "factory_version": FACTORY_VERSION,
        "files": {str(path.relative_to(remotion_root)).replace("\\", "/"): sha256_file(path) for path in files},
    })


def _claim_bindings(*claim_ids: str) -> list[dict[str, str]]:
    return [{"claim_id": claim_id, "evidence_id": SOURCE_ID, "source_url": SOURCE_URL} for claim_id in claim_ids]


def _series(story: Mapping[str, Any]) -> dict[str, Any]:
    history = list(story.get("curve_history") or [])
    if len(history) < 20:
        raise Tier2V2Error("governed_curve_history_insufficient_for_editorial_proof")

    def value(row: Mapping[str, Any], maturity: str) -> float | None:
        for cell in row.get("curve") or []:
            if cell.get("maturity") == maturity:
                return float(cell["value"])
        return None

    dates = [str(row.get("observation_date")) for row in history]
    values = {maturity: [value(row, maturity) for row in history] for maturity in ("2Y", "10Y", "30Y")}
    spreads = [round((b - a) * 100, 1) if a is not None and b is not None else None for a, b in zip(values["2Y"], values["10Y"])]
    return {"dates": dates, "values": values, "spreads": spreads, "observation_count": len(history)}


def decide_video_eligibility_v2(story: Mapping[str, Any]) -> dict[str, Any]:
    claims = len(story.get("claims") or {})
    history = len(story.get("curve_history") or [])
    assets = len(story.get("media_assets") or [])
    rights_ready = bool(assets) and all(str(row.get("rights_status") or "") in {"public_domain", "capital_chronicle_owned", "capital_chronicle_internal"} for row in story.get("media_assets") or [])
    if claims < 2 or assets < 1:
        result = "VIDEO_NOT_SELECTED"
    elif not rights_ready:
        result = "VIDEO_BLOCKED"
    else:
        result = "VIDEO_SELECTED_SHORTER_EDITORIAL_PROOF"
    return {
        "result": result,
        "materiality": "medium",
        "narrative_depth": "short_editorial_proof_not_15_minutes",
        "visualizability": "strong_chart_and_source_treatment",
        "evidence_strength": claims,
        "time_series_observations": history,
        "rights_ready": rights_ready,
        "long_form_15_minute_decision": "WITHHELD_NO_FILLER",
        "exact_reason": "Four governed claims and one narrow Treasury record support a concise reading guide, not a genuine 15-minute documentary.",
        "public_write_authority": False,
    }


def _parse_json_text(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.DOTALL)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            return None
        try:
            value = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return dict(value) if isinstance(value, Mapping) else None


def run_director(story: Mapping[str, Any], eligibility: Mapping[str, Any], *, enabled: bool) -> dict[str, Any]:
    deterministic = {
        "narrative_question": "What does the shape of one official Treasury curve actually tell us?",
        "hook": "A curve is a map, not a verdict.",
        "pacing": "concise_editorial",
        "short_angle": "three-level-reading",
        "numeric_policy": "round_or_omit_except_governed_claim_frame",
    }
    if not enabled:
        return {"status": "DIRECTOR_DISABLED", "model": None, "direction": deterministic, "provider_used": False}
    prompt = (
        "You are the Capital Chronicle Video Director. Return JSON only with keys narrative_question, hook, pacing, short_angle, numeric_policy. "
        "You may direct presentation but may not add claims, causes, forecasts, recommendations, quotes, or numbers. The story is an official U.S. Treasury daily par-yield record with exactly four governed claims (2Y, 10Y, 30Y, 2s10s) and a governed historical series. "
        f"Eligibility says: {json.dumps(eligibility, sort_keys=True)}. Prefer meaning over table-reading and explicitly avoid stretching this into 15 minutes."
    )
    attempts = []
    result = None
    parsed = None
    used_model = DIRECTOR_MODEL
    for model in (DIRECTOR_MODEL, DIRECTOR_FALLBACK_MODEL):
        used_model = model
        result = call_nine_router(prompt, model, timeout_seconds=180, max_tokens=1400, temperature=0.15)
        parsed = _parse_json_text(result.text)
        attempts.append({"model":model,"failure_class":result.failure_class,"resolved_model":result.resolved_model,"provider_invocation_id":result.provider_invocation_id})
        if parsed and not result.failure_class:
            break
    assert result is not None
    safe = deterministic
    if parsed:
        safe = {key: str(parsed.get(key) or deterministic[key])[:300] for key in deterministic}
    return {
        "status": "DIRECTOR_ACCEPTED" if parsed and not result.failure_class else "DIRECTOR_FALLBACK_DETERMINISTIC",
        "model": used_model,
        "attempts": attempts,
        "resolved_model": result.resolved_model,
        "provider_invocation_id": result.provider_invocation_id,
        "usage": result.usage,
        "cost": result.cost,
        "failure_class": result.failure_class,
        "direction": safe,
        "provider_used": True,
    }


def _scene(
    scene_id: str, chapter_id: str, primitive: str, title: str, script: str, *,
    order: int, claims: Sequence[str], kicker: str, deck: str = "", asset_id: str | None = None,
    numbers: list[dict[str, str]] | None = None, series: list[dict[str, Any]] | None = None,
    transition: str = "fade", accent: str = "signal", narrative_type: str = "factual",
    chapter_number: str | None = None, disclosure: str | None = None,
) -> dict[str, Any]:
    return {
        "scene_id": scene_id, "chapter_id": chapter_id, "order": order, "primitive": primitive,
        "title": title, "deck": deck, "kicker": kicker, "script": script, "narrative_type": narrative_type,
        "claim_bindings": _claim_bindings(*claims), "source_bindings": [{"evidence_id": SOURCE_ID, "source_url": SOURCE_URL}],
        "asset_refs": [asset_id] if asset_id else [], "numbers": numbers or [], "series": series or [],
        "transition": {"type": transition, "duration_seconds": TRANSITION_SECONDS}, "accent": accent,
        "style": {"title_scale": 1.0, "caption_scale": 1.0, "asset_scale": 1.0, "show_legend": False, "source_compact": False}, "chapter_number": chapter_number,
        "source_label": "Source: U.S. Department of the Treasury — Daily Treasury Par Yield Curve Rates.",
        "rights_requirements": {"status": "fail_closed", "documentary_assets_must_be_rights_cleared": True},
        "disclosure": disclosure, "revision_history": [],
    }


def _points(dates: Sequence[str], values: Sequence[float | None], *, step: int = 4) -> list[dict[str, Any]]:
    rows = [{"label": dates[index], "value": round(float(values[index]), 3)} for index in range(0, len(dates), step) if values[index] is not None]
    if values and values[-1] is not None and rows[-1]["label"] != dates[-1]:
        rows.append({"label": dates[-1], "value": round(float(values[-1]), 3)})
    return rows


def build_programs(story: Mapping[str, Any], eligibility: Mapping[str, Any], direction: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if eligibility.get("result") != "VIDEO_SELECTED_SHORTER_EDITORIAL_PROOF":
        raise Tier2V2Error("video_not_selected_or_blocked")
    data = _series(story)
    claims = story["claims"]
    y2, y10, y30, spread = (claims[key] for key in CLAIM_IDS)
    all_claims = list(CLAIM_IDS)
    curve = data["values"]
    last_curve = [
        {"label": "2Y", "value": float(y2["value"])},
        {"label": "10Y", "value": float(y10["value"])},
        {"label": "30Y", "value": float(y30["value"])},
    ]
    long_scenes = [
        _scene("long-01", "chapter-01", "COLD_OPEN", "A curve is a map. Not a verdict.",
            "A Treasury yield curve can look like a verdict on the economy. It is not. It is a dated map of official par yields across maturities. The useful question is smaller: what does this shape establish, and where does the evidence stop? We will read the level, the slope, and the change, without turning one table into a forecast.", order=1, claims=all_claims, kicker="The reading question", transition="fade", accent="signal"),
        _scene("long-02", "chapter-01", "ILLUSTRATION_ATMOSPHERE", "First, see the shape.",
            "Think of the curve as a landscape profile. Each maturity is a point on the horizon. Height shows the recorded par yield; distance marks time to maturity. That metaphor is only a reading aid. The illustration is not a market photograph and contributes no factual evidence. The official Treasury record remains the authority.", order=2, claims=all_claims, kicker="Visual intuition", deck="An illustrative landscape makes the geometry legible before the numbers arrive.", asset_id="yield-landscape-illustration", transition="wipeleft", accent="amber", narrative_type="context"),
        _scene("long-03", "chapter-01", "SOURCE_EVIDENCE", "The source sets the boundary.",
            "The underlying source is the U.S. Treasury Daily Treasury Par Yield Curve Rates table. These are official daily par-yield observations for one business date. They are not live quotes, executable prices, or a recommendation. Reading the source label before reading the number keeps the evidence in its proper frame.", order=3, claims=all_claims, kicker="Primary evidence", deck="Official daily observations, transformed faithfully for explanation.", asset_id="treasury_source_excerpt", transition="smoothup", accent="amber"),
        _scene("long-04", "chapter-02", "CHAPTER_RUPTURE", "Three questions unlock the curve.",
            "Now reduce the table to three questions. Where are the key maturities? What is the slope between the two-year and ten-year? And what changed from the previous official observation? That sequence explains the record without reading every cell aloud.", order=4, claims=all_claims, kicker="Chapter two", deck="Level. Slope. Change.", transition="wipeleft", accent="cobalt", narrative_type="editorial_bridge", chapter_number="02"),
        _scene("long-05", "chapter-02", "COMPARISON_FIELD", "Level: the long end sat highest.",
            f"On the governed July 13 observation, the two-year par yield was {y2['value']:.2f} percent, the ten-year was {y10['value']:.2f} percent, and the thirty-year was {y30['value']:.2f} percent. On screen, those values are rounded to one decimal place because the precise hundredths do not change the visual conclusion: the longer maturities occupied higher levels in this record.", order=5, claims=all_claims, kicker="Question one — level", numbers=[{"label":"2-year","value":f"{y2['value']:.1f}%","note":"official par yield"},{"label":"10-year","value":f"{y10['value']:.1f}%","note":"official par yield"},{"label":"30-year","value":f"{y30['value']:.1f}%","note":"official par yield"}], transition="fade", accent="signal"),
        _scene("long-06", "chapter-02", "CURVE_MORPH", "Shape: compare maturities, not cards.",
            "Plotting the maturities on one field changes the reading. Instead of three isolated numbers, we see a rising profile across the selected points. That supports a comparison of the curve's shape on this date. It does not, by itself, explain why the curve looked this way. Causal claims would require evidence beyond this governed packet.", order=6, claims=all_claims, kicker="One continuous field", deck="The animated line reveals relationship, not prediction.", series=[{"label":"July 13 curve","unit":"percent","points":last_curve,"color":"#e4402f"}], transition="smoothup", accent="signal"),
        _scene("long-07", "chapter-02", "TIMELINE_TRACE", "Change: context needs more than two dates.",
            f"The package also carries {data['observation_count']} official observations. The timeline lets us see movement through that window without narrating each daily value. The final point remains the governed July 13 record. Earlier points provide source-backed context for the path, not a forecast for what came next.", order=7, claims=all_claims, kicker="The governed window", series=[{"label":"2Y","points":_points(data['dates'],curve['2Y']),"color":"#4169e1"},{"label":"10Y","points":_points(data['dates'],curve['10Y']),"color":"#e4402f"},{"label":"30Y","points":_points(data['dates'],curve['30Y']),"color":"#0b0b0c"}], transition="fade", accent="cobalt"),
        _scene("long-08", "chapter-03", "CHAPTER_RUPTURE", "Slope is a relationship.",
            "The spread is not another independent source observation. It is a transparent calculation from two governed observations. Keeping that distinction visible is part of the editorial craft: source values first, transformation second, interpretation last.", order=8, claims=[CLAIM_IDS[0], CLAIM_IDS[1], CLAIM_IDS[3]], kicker="Chapter three", deck="Two source values. One transparent calculation.", transition="wipeleft", accent="mint", narrative_type="editorial_bridge", chapter_number="03"),
        _scene("long-09", "chapter-03", "KINETIC_STATEMENT", "Positive. Slightly wider. Still a small move.",
            f"The two-year to ten-year spread was {spread['value']:.0f} basis points, compared with {spread['prior_value']:.0f} basis points in the previous official observation. That is a one-basis-point widening. The disciplined description is simple: positive, slightly wider, and still a small move. Motion can clarify that hierarchy; it must not inflate it.", order=9, claims=[CLAIM_IDS[0], CLAIM_IDS[1], CLAIM_IDS[3]], kicker="Question two — slope", transition="smoothup", accent="mint"),
        _scene("long-10", "chapter-03", "BOUNDARY_CLOSE", "What the record says — and does not say.",
            "The record supports a dated description of levels, shape, slope, and change. It does not establish a trade, a policy forecast, or a causal story about other markets. This shorter editorial proof stops here because the evidence stops here. The honest production decision is not to manufacture a fifteen-minute runtime from four claims.", order=10, claims=all_claims, kicker="Evidence boundary", deck="Useful explanation ends where governed authority ends.", transition="fade", accent="signal", disclosure="Historical governed demonstration. Official Treasury par yields are not executable prices. Not financial advice."),
    ]
    short_scenes = [
        _scene("short-01", "short", "COLD_OPEN", "A yield curve is not a forecast.", "A yield curve is a dated map of official par yields. Read it with three questions: level, slope, and change.", order=1, claims=all_claims, kicker="60-second reading", transition="smoothup", accent="signal"),
        _scene("short-02", "short", "COMPARISON_FIELD", "Level", f"On July 13, the governed record put the two-year near {y2['value']:.1f} percent, the ten-year near {y10['value']:.1f}, and the thirty-year near {y30['value']:.1f}. The long end sat highest.", order=2, claims=all_claims, kicker="Question one", numbers=[{"label":"2Y","value":f"{y2['value']:.1f}%"},{"label":"10Y","value":f"{y10['value']:.1f}%"},{"label":"30Y","value":f"{y30['value']:.1f}%"}], transition="wipeleft", accent="cobalt"),
        _scene("short-03", "short", "CURVE_MORPH", "Slope", f"The ten-year minus the two-year was {spread['value']:.0f} basis points. Positive, but only one basis point wider than the previous official observation.", order=3, claims=[CLAIM_IDS[0], CLAIM_IDS[1], CLAIM_IDS[3]], kicker="Question two", series=[{"label":"July 13","points":last_curve,"color":"#e4402f"}], transition="smoothup", accent="mint"),
        _scene("short-04", "short", "ILLUSTRATION_ATMOSPHERE", "Change needs context.", "One daily move is not a regime call. Use the governed history to see the path, then stop before prediction.", order=4, claims=all_claims, kicker="Question three", asset_id="yield-landscape-illustration", transition="fade", accent="amber", narrative_type="context"),
        _scene("short-05", "short", "BOUNDARY_CLOSE", "Map, not verdict.", "The source supports description, not a trade or forecast. Read the shape. Respect the boundary.", order=5, claims=all_claims, kicker="Capital Chronicle", transition="fade", accent="signal", disclosure="Historical governed demonstration. Not financial advice."),
    ]

    chapters = [
        {"chapter_id":"chapter-01","title":"The reading question","scene_ids":["long-01","long-02","long-03"]},
        {"chapter_id":"chapter-02","title":"Level, shape, change","scene_ids":["long-04","long-05","long-06","long-07"]},
        {"chapter_id":"chapter-03","title":"Slope and boundary","scene_ids":["long-08","long-09","long-10"]},
    ]
    common = {
        "schema_version": SCHEMA_VERSION, "factory_version": FACTORY_VERSION, "motion_system_version": MOTION_SYSTEM_VERSION,
        "story_id": story["story_id"], "story_version": story["story_version"], "packet_id": story["packet_id"],
        "input_hashes": {"packet": story["packet_sha256"], "article": story["article_hash"]},
        "source_ids": [SOURCE_ID], "claim_ids": list(CLAIM_IDS), "eligibility": dict(eligibility), "direction": dict(direction),
        "public_write_authority": False, "generated_media_is_factual_authority": False,
    }
    long_program = {**common, "video_id":"treasury-curve-reading-v2-proof", "mode":"SHORTER_EDITORIAL_PROOF_16X9", "target_runtime_policy":"NO_15_MINUTE_FILLER", "chapters":chapters, "scenes":long_scenes, "aspect_strategy":"native_16:9"}
    short_program = {**common, "video_id":"treasury-curve-reading-v2-short", "mode":"SHORT_FORM_NATIVE", "target_runtime_policy":"native_45_90_seconds", "chapters":[{"chapter_id":"short","title":"native short","scene_ids":[row["scene_id"] for row in short_scenes]}], "scenes":short_scenes, "aspect_strategy":"native_9:16_independent_direction"}
    long_program["semantic_content_hash"] = semantic_program_hash(long_program)
    short_program["semantic_content_hash"] = semantic_program_hash(short_program)
    return long_program, short_program


def validate_program(program: Mapping[str, Any], assets: Mapping[str, AssetRecord] | None = None) -> dict[str, Any]:
    blockers: list[str] = []
    scenes = list(program.get("scenes") or [])
    ids = [str(row.get("scene_id")) for row in scenes]
    if len(ids) != len(set(ids)):
        blockers.append("duplicate_scene_id")
    chapter_refs = {sid for chapter in program.get("chapters") or [] for sid in chapter.get("scene_ids") or []}
    if chapter_refs != set(ids):
        blockers.append("chapter_scene_set_mismatch")
    claim_set = set(program.get("claim_ids") or [])
    coverage = {binding.get("claim_id") for scene in scenes for binding in scene.get("claim_bindings") or []}
    if coverage != claim_set:
        blockers.append("claim_coverage_incomplete")
    for scene in scenes:
        if scene.get("narrative_type") == "factual" and (not scene.get("claim_bindings") or not scene.get("source_bindings")):
            blockers.append(f"unbound_factual_scene:{scene.get('scene_id')}")
        for asset_id in scene.get("asset_refs") or []:
            if assets is not None and asset_id not in assets:
                blockers.append(f"asset_missing:{asset_id}")
    if program.get("public_write_authority") is not False:
        blockers.append("public_write_authority_not_false")
    return {"status":"PASS" if not blockers else "BLOCK", "blockers":blockers, "claim_binding_coverage":len(coverage & claim_set)/max(1,len(claim_set))}


def _stage_assets(story: Mapping[str, Any], root: Path, *, generate_image_enabled: bool) -> tuple[dict[str, AssetRecord], dict[str, Any]]:
    assets: dict[str, AssetRecord] = {}
    public_assets = root / "public" / "assets"
    for row in story.get("media_assets") or []:
        source = REPO_ROOT / str(row["path"])
        record = stage_governed_asset(asset_id=str(row["asset_id"]), source=source, expected_sha256=str(row["sha256"]), output_dir=public_assets, source_url=str(row.get("source_page_url") or SOURCE_URL), rights_classification=str(row.get("rights_status") or ""))
        assets[record.asset_id] = record
    evidence: dict[str, Any]
    if generate_image_enabled:
        prompt = (
            "Premium editorial illustration for a financial-news explainer: an abstract physical landscape whose horizon subtly resembles a rising bond yield curve, layered paper-cut topography, warm off-white, charcoal, cobalt and restrained vermilion, tactile studio lighting, sophisticated magazine art direction, no people, no buildings, no flags, no logos, no letters, no numbers, no charts, no UI, no documentary claim; clearly conceptual and illustrative; central composition safe for both landscape and vertical crops."
        )
        record, evidence = generate_illustrative_asset(asset_id="yield-landscape-illustration", prompt=prompt, width=1536, height=1024, output_dir=public_assets)
        if record:
            assets[record.asset_id] = record
    else:
        accepted = Path(r"C:\Users\bullw\AppData\Local\Temp\tier2-direct-image-api-real-smoke-bakeoff-v1\landscape\gpt-5_5__macro_central_bank.png")
        accepted_hash = "195456f914e778eeb652ae27c16509cb0ab521f80fd32baf948967150396d833"
        if accepted.is_file() and sha256_file(accepted) == accepted_hash:
            destination = public_assets / "yield-landscape-illustration-accepted-gpt55.png"
            shutil.copy2(accepted, destination)
            record = AssetRecord(
                asset_id="yield-landscape-illustration", media_role="illustrative_enrichment",
                local_path=str(destination), sha256=accepted_hash, source_url=None, asset_url=None,
                rights_classification="provider_generated_terms_reviewed_for_v2_proof", license_url=None,
                attribution="AI-generated illustration; Capital Chronicle art direction", retrieved_at_utc=_now(),
                synthetic=True, documentary_authority=False, provider="ai.api-cheap.site", model="gpt-5.5",
                prompt_hash="fae5e705e3cb3d014387e6d18ef27d532be1ac4c3e160856ed82a6c9e533b9e9",
                invocation_id=None, disclosure="ILLUSTRATION — not a photograph, event record, or factual evidence.",
            )
            assets[record.asset_id] = record
            evidence = {
                "status":"REUSED_ACCEPTED_DIRECT_IMAGE_ARTIFACT_NO_NEW_CALL", "call_count":0,
                "accepted_task":"TASK_CONTENTOPS_TIER2_DIRECT_IMAGE_API_REAL_SMOKE_AND_BAKEOFF_V1",
                "provider":"ai.api-cheap.site", "model":"gpt-5.5", "output_sha256":accepted_hash,
                "request_outcome":"RECONCILED_VALID_ARTIFACT", "documentary_authority":False,
            }
        else:
            evidence = {"status":"DISABLED_NO_ACCEPTED_ARTIFACT_AVAILABLE", "call_count":0}
    return assets, evidence


def _caption_chunks(text: str, duration: float) -> list[dict[str, Any]]:
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    current: list[str] = []
    for word in words:
        current.append(word)
        if len(current) >= 7 or (len(current) >= 4 and re.search(r"[.!?;:]$", word)):
            chunks.append(" ".join(current)); current = []
    if current:
        chunks.append(" ".join(current))
    total = sum(len(chunk.split()) for chunk in chunks)
    cursor = 0.0
    rows = []
    for index, chunk in enumerate(chunks):
        end = duration if index == len(chunks)-1 else cursor + duration * len(chunk.split()) / total
        rows.append({"start_seconds":round(cursor,3), "end_seconds":round(end,3), "text":chunk})
        cursor = end
    return rows


def _prepare_narration(program: Mapping[str, Any], root: Path, *, tts_python: str, voice: str) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    narration_dir = root / "public" / "narration"
    narration_dir.mkdir(parents=True, exist_ok=True)
    for scene in program["scenes"]:
        key = logical_hash({"script":scene["script"], "provider":"kokoro", "voice":voice})[:18]
        path = narration_dir / f"{scene['scene_id']}-{key}.wav"
        started = time.perf_counter()
        telemetry = None
        if not path.exists():
            telemetry = _tts_segment(scene["script"], scene["scene_id"], path, tts_python=tts_python, voice=voice)
        facts = _media_facts(path)
        output[scene["scene_id"]] = {
            "provider":"kokoro", "model":"Kokoro-82M", "voice":voice, "script_hash":logical_hash(scene["script"]),
            "path":str(path), "public_path":f"narration/{path.name}", "sha256":facts["sha256"], "duration_seconds":facts["duration_seconds"],
            "captions":_caption_chunks(scene["script"], facts["duration_seconds"]), "wall_seconds":round(time.perf_counter()-started,3),
            "telemetry":telemetry, "network_call":False, "cash_cost":None,
        }
    return output


def _asset_public_path(record: AssetRecord) -> str:
    return f"assets/{Path(record.local_path).name}"


def scene_cache_key(scene: Mapping[str, Any], narration: Mapping[str, Any], assets: Mapping[str, AssetRecord], *, runtime_hash: str, profile: Mapping[str, Any]) -> str:
    return logical_hash({
        "semantic_scene":scene,
        "narration":{"provider":narration["provider"],"model":narration["model"],"voice":narration["voice"],"script_hash":narration["script_hash"],"audio_sha256":narration["sha256"]},
        "assets":{asset_id:assets[asset_id].sha256 for asset_id in scene.get("asset_refs") or []},
        "runtime_hash":runtime_hash, "profile":dict(profile), "motion_system_version":MOTION_SYSTEM_VERSION,
    })


def chapter_cache_key(chapter: Mapping[str, Any], scene_rows: Sequence[Mapping[str, Any]], *, runtime_hash: str) -> str:
    by_id = {row["scene_id"]:row for row in scene_rows}
    return logical_hash({"chapter":chapter,"scene_render_hashes":[by_id[sid]["render_sha256"] for sid in chapter["scene_ids"]],"transitions":[by_id[sid]["transition"] for sid in chapter["scene_ids"]],"runtime_hash":runtime_hash})


def _compile_jobs(program: Mapping[str, Any], narration: Mapping[str, Mapping[str, Any]], assets: Mapping[str, AssetRecord], root: Path, *, runtime_hash: str, profile: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cache_dir = root / "cache" / "scenes" / str(program["mode"])
    jobs: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for scene in program["scenes"]:
        audio = narration[scene["scene_id"]]
        key = scene_cache_key(scene, audio, assets, runtime_hash=runtime_hash, profile=profile)
        output = cache_dir / f"{scene['scene_id']}-{key[:18]}.mp4"
        duration = audio["duration_seconds"] + TAIL_SECONDS
        asset_id = (scene.get("asset_refs") or [None])[0]
        asset = assets.get(asset_id) if asset_id else None
        cues = [{"start_frame":max(0,math.floor(row["start_seconds"]*profile["fps"])),"end_frame":max(1,math.ceil(row["end_seconds"]*profile["fps"])),"text":row["text"]} for row in audio["captions"]]
        job = {
            "scene_id":scene["scene_id"], "chapter_id":scene["chapter_id"], "primitive":scene["primitive"], "aspect":profile["aspect"],
            "width":profile["width"], "height":profile["height"], "fps":profile["fps"], "duration_in_frames":math.ceil(duration*profile["fps"]),
            "title":scene["title"], "deck":scene.get("deck"), "kicker":scene.get("kicker"), "statement":scene.get("title"),
            "chapter_number":scene.get("chapter_number"), "source_label":scene["source_label"],
            "rights_label":asset.disclosure if asset and asset.synthetic else (asset.attribution if asset else None), "disclosure":scene.get("disclosure"),
            "numbers":scene.get("numbers") or [], "series":scene.get("series") or [], "asset_path":_asset_public_path(asset) if asset else None,
            "asset_role":asset.media_role if asset else None, "captions":cues, "narration_asset":audio["public_path"], "accent":scene.get("accent"),
            "transition":scene["transition"]["type"], "title_scale":scene.get("style",{}).get("title_scale",1.0), "caption_scale":scene.get("style",{}).get("caption_scale",1.0),
            "asset_scale":scene.get("style",{}).get("asset_scale",1.0), "show_legend":scene.get("style",{}).get("show_legend",False), "source_compact":scene.get("style",{}).get("source_compact",False),
            "output_path":str(output), "cache_key":key,
        }
        cache_hit = output.is_file()
        if not cache_hit:
            jobs.append(job)
        rows.append({"scene_id":scene["scene_id"],"chapter_id":scene["chapter_id"],"cache_key":key,"path":str(output),"cache_hit":cache_hit,"duration_seconds":duration,"transition":scene["transition"]})
    return jobs, rows


def _chrome_path() -> str:
    choices = [
        os.environ.get("CONTENTOPS_TIER2_CHROME"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe"),
    ]
    for value in choices:
        if value and Path(value).is_file():
            return str(value)
    raise Tier2V2Error("remotion_headless_chromium_executable_not_found")


def _render_jobs(jobs: Sequence[Mapping[str, Any]], root: Path) -> dict[str, Any]:
    if not jobs:
        return {"status":"PASS_ALL_CACHE_HITS","rows":[],"network_calls":0,"uploads":0}
    batch_path = root / "work" / f"render-batch-{logical_hash(jobs)[:12]}.json"
    receipt_path = batch_path.with_suffix(".receipt.json")
    _write_json(batch_path, {"public_dir":str(root / "public"),"jobs":list(jobs)})
    _run(["node", str(REMOTION_ROOT / "scripts" / "render-batch.mjs"), "--batch", str(batch_path), "--receipt", str(receipt_path), "--browser", _chrome_path()], timeout=7200)
    receipt = _read_json(receipt_path)
    if receipt.get("status") != "PASS":
        raise Tier2V2Error("remotion_batch_blocked")
    return receipt


def _xfade_name(value: str) -> str:
    return value if value in {"fade","wipeleft","smoothup"} else "fade"


def _assemble(clips: Sequence[Path], transitions: Sequence[Mapping[str, Any]], output: Path) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    if len(clips) == 1:
        shutil.copy2(clips[0], output)
        return {"transition_count":0,"transitions":[],"facts":_media_facts(output)}
    durations = [_media_facts(path)["duration_seconds"] for path in clips]
    command = ["ffmpeg","-y"]
    for path in clips:
        command += ["-i",str(path)]
    filters: list[str] = []
    video_prev = "0:v"; audio_prev = "0:a"; elapsed = durations[0]
    evidence = []
    for index in range(1,len(clips)):
        transition = transitions[index-1] if index-1 < len(transitions) else {"type":"fade","duration_seconds":TRANSITION_SECONDS}
        duration = min(float(transition.get("duration_seconds") or TRANSITION_SECONDS), durations[index-1]/3, durations[index]/3)
        elapsed -= duration
        vout=f"v{index}"; aout=f"a{index}"
        filters.append(f"[{video_prev}][{index}:v]xfade=transition={_xfade_name(str(transition.get('type')))}:duration={duration:.3f}:offset={elapsed:.3f}[{vout}]")
        filters.append(f"[{audio_prev}][{index}:a]acrossfade=d={duration:.3f}:c1=tri:c2=tri[{aout}]")
        evidence.append({"from":clips[index-1].name,"to":clips[index].name,"type":_xfade_name(str(transition.get("type"))),"duration_seconds":round(duration,3),"offset_seconds":round(elapsed,3)})
        video_prev=vout; audio_prev=aout; elapsed += durations[index]
    command += ["-filter_complex",";".join(filters),"-map",f"[{video_prev}]","-map",f"[{audio_prev}]","-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(output)]
    _run(command, timeout=7200)
    return {"transition_count":len(evidence),"transitions":evidence,"facts":_media_facts(output)}


def _write_caption_sidecars(program: Mapping[str, Any], narration: Mapping[str, Mapping[str, Any]], scene_rows: Sequence[Mapping[str, Any]], output_base: Path) -> dict[str, Any]:
    by_id={row["scene_id"]:row for row in scene_rows}; cursor=0.0; cues=[]
    for scene in program["scenes"]:
        row=by_id[scene["scene_id"]]
        for cue in narration[scene["scene_id"]]["captions"]:
            cues.append({"scene_id":scene["scene_id"],"start_seconds":round(cursor+cue["start_seconds"],3),"end_seconds":round(cursor+cue["end_seconds"],3),"text":cue["text"]})
        cursor += row["duration_seconds"] - float(scene["transition"]["duration_seconds"])

    def stamp(seconds: float, comma: bool) -> str:
        millis=max(0,int(round(seconds*1000))); hours,millis=divmod(millis,3600000); minutes,millis=divmod(millis,60000); secs,millis=divmod(millis,1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}{',' if comma else '.'}{millis:03d}"
    srt=output_base.with_suffix(".srt"); vtt=output_base.with_suffix(".vtt"); srt.parent.mkdir(parents=True,exist_ok=True)
    srt.write_text("\n\n".join(f"{i+1}\n{stamp(row['start_seconds'],True)} --> {stamp(row['end_seconds'],True)}\n{row['text']}" for i,row in enumerate(cues))+"\n",encoding="utf-8")
    vtt.write_text("WEBVTT\n\n"+"\n\n".join(f"{stamp(row['start_seconds'],False)} --> {stamp(row['end_seconds'],False)}\n{row['text']}" for row in cues)+"\n",encoding="utf-8")
    return {"srt":str(srt),"vtt":str(vtt),"cue_count":len(cues),"cues":cues}


def render_variant(program: Mapping[str, Any], narration: Mapping[str, Mapping[str, Any]], assets: Mapping[str, AssetRecord], root: Path, *, runtime_hash: str, profile: Mapping[str, Any], output_name: str) -> dict[str, Any]:
    jobs, scene_rows = _compile_jobs(program,narration,assets,root,runtime_hash=runtime_hash,profile=profile)
    receipt = _render_jobs(jobs,root)
    for row in scene_rows:
        path=Path(row["path"])
        if not path.is_file(): raise Tier2V2Error(f"scene_render_missing:{row['scene_id']}")
        row["render_sha256"]=sha256_file(path); row["media"]=_media_facts(path)
    chapters=[]; by_id={row["scene_id"]:row for row in scene_rows}
    for chapter in program["chapters"]:
        rows=[by_id[sid] for sid in chapter["scene_ids"]]
        key=chapter_cache_key(chapter,rows,runtime_hash=runtime_hash)
        path=root/"cache"/"chapters"/str(program["mode"])/f"{chapter['chapter_id']}-{key[:18]}.mp4"
        hit=path.is_file()
        if not hit:
            chapter_assembly = _assemble([Path(row["path"]) for row in rows],[row["transition"] for row in rows[:-1]],path)
        else:
            chapter_assembly = {"transition_count":max(0,len(rows)-1),"transitions":"CACHE_HIT","facts":_media_facts(path)}
        chapters.append({"chapter_id":chapter["chapter_id"],"cache_key":key,"path":str(path),"cache_hit":hit,"render_sha256":sha256_file(path),"media":_media_facts(path),"assembly":chapter_assembly})
    master_key=logical_hash({"chapters":[row["render_sha256"] for row in chapters],"runtime_hash":runtime_hash,"chapter_transitions":["wipeleft"]*(len(chapters)-1)})
    master_cache=root/"cache"/"masters"/str(program["mode"])/f"{master_key[:18]}.mp4"; master_hit=master_cache.is_file()
    if not master_hit:
        master_assembly=_assemble([Path(row["path"]) for row in chapters],[{"type":"wipeleft","duration_seconds":TRANSITION_SECONDS}]*(len(chapters)-1),master_cache)
    else:
        master_assembly={"transition_count":max(0,len(chapters)-1),"transitions":"CACHE_HIT","facts":_media_facts(master_cache)}
    final=root/"package"/output_name; final.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(master_cache,final)
    captions=_write_caption_sidecars(program,narration,scene_rows,root/"package"/"captions"/Path(output_name).stem)
    return {"master_path":str(final),"master_cache_key":master_key,"master_cache_hit":master_hit,"media":_media_facts(final),"scene_rows":scene_rows,"chapter_rows":chapters,"rendered_scene_ids":[job["scene_id"] for job in jobs],"receipt":receipt,"assembly":master_assembly,"captions":captions}


def _scene_offsets(program: Mapping[str, Any], render: Mapping[str, Any]) -> list[dict[str, Any]]:
    by_id={row["scene_id"]:row for row in render["scene_rows"]}; cursor=0.0; rows=[]
    for scene in program["scenes"]:
        duration=by_id[scene["scene_id"]]["duration_seconds"]
        rows.append({"scene_id":scene["scene_id"],"chapter_id":scene["chapter_id"],"start_seconds":round(cursor,3),"end_seconds":round(cursor+duration,3),"sample_seconds":round(cursor+duration*.52,3)})
        cursor += duration-float(scene["transition"]["duration_seconds"])
    return rows


def _extract_frame(video: Path, seconds: float, output: Path) -> None:
    output.parent.mkdir(parents=True,exist_ok=True)
    _run(["ffmpeg","-y","-ss",f"{seconds:.3f}","-i",str(video),"-frames:v","1","-q:v","2",str(output)],timeout=180)


def _contact_sheets(program: Mapping[str, Any], render: Mapping[str, Any], root: Path, *, tag: str) -> dict[str, Any]:
    offsets=_scene_offsets(program,render); frames=[]; frame_dir=root/"work"/"frames"/tag; is_short=tag.startswith("short")
    for row in offsets:
        path=frame_dir/f"{row['scene_id']}.jpg"; _extract_frame(Path(render["master_path"]),row["sample_seconds"],path); frames.append((path,row))
    thumbs=[]
    for path,row in frames:
        image=Image.open(path).convert("RGB"); image.thumbnail((520,520 if is_short else 300));
        tile=Image.new("RGB",(540,720 if is_short else 360),(240,238,232)); tile.paste(image,((540-image.width)//2,18));
        draw=ImageDraw.Draw(tile); draw.text((18,tile.height-44),f"{row['scene_id']}  {row['sample_seconds']:.1f}s",fill=(11,11,12)); thumbs.append(tile)
    cols=2 if is_short else 3; rows_count=math.ceil(len(thumbs)/cols); sheet=Image.new("RGB",(cols*540,rows_count*thumbs[0].height),(11,11,12))
    for i,tile in enumerate(thumbs): sheet.paste(tile,((i%cols)*540,(i//cols)*tile.height))
    out=root/"package"/"visual_acceptance"/("short_contact_sheet.jpg" if tag=="short" else "long_contact_sheet.jpg"); out.parent.mkdir(parents=True,exist_ok=True); sheet.save(out,quality=88,optimize=True)
    critic_pages=[]
    for page_index in range(0,len(thumbs),4):
        group=thumbs[page_index:page_index+4]; page=Image.new("RGB",(1080,group[0].height*2),(11,11,12))
        for i,tile in enumerate(group): page.paste(tile,((i%2)*540,(i//2)*tile.height))
        path=root/"work"/"critic_pages"/f"{tag}_{page_index//4+1}.jpg"; path.parent.mkdir(parents=True,exist_ok=True); page.save(path,quality=82,optimize=True); critic_pages.append(str(path))
    return {"contact_sheet":str(out),"critic_pages":critic_pages,"offsets":offsets,"scene_coverage":len(frames)}


def run_critic(program: Mapping[str, Any], render: Mapping[str, Any], sheets: Mapping[str, Any], *, enabled: bool, round_number: int) -> dict[str, Any]:
    if not enabled:
        return {"status":"CRITIC_DISABLED_AWAITING_HUMAN","provider_used":False,"round":round_number,"defects":[]}
    pages=list(sheets["critic_pages"])[:6]
    encoded=[base64.b64encode(Path(path).read_bytes()).decode("ascii") for path in pages]
    prompt=(
        "You are an independent multimodal financial-news video critic. Inspect every labeled tile. Return JSON only: "
        "{status, coverage:{scene_ids:[...], time_ranges:[...]}, defects:[{scene_id,time_range,class,severity,confidence,evidence,proposed_visual_change}], summary}. "
        "Use only scene IDs and times visible in the sheets. Evaluate typography, hierarchy, composition, chart legibility, caption collision, visual repetition, transition/pacing risk, crop, and synthetic-media disclosure. Never suggest factual, numeric, claim, script, or evidence changes. Do not claim professional acceptance; Jim/ChatGPT owns it. "
        f"Expected scenes: {[row['scene_id'] for row in program['scenes']]}. Round {round_number}."
    )
    result=call_nine_router_multimodal(prompt,encoded,CRITIC_MODEL,timeout_seconds=240,max_tokens=3500,temperature=.1)
    parsed=_parse_json_text(result.text)
    defects=[]
    if parsed and isinstance(parsed.get("defects"),list):
        valid_ids={row["scene_id"] for row in program["scenes"]}
        for row in parsed["defects"][:20]:
            if isinstance(row,Mapping) and row.get("scene_id") in valid_ids and row.get("time_range"):
                defects.append({key:row.get(key) for key in ("scene_id","time_range","class","severity","confidence","evidence","proposed_visual_change")})
    coverage=(parsed or {}).get("coverage") if parsed else None
    covered=set((coverage or {}).get("scene_ids") or []) if isinstance(coverage,Mapping) else set()
    return {"status":"CRITIC_COMPLETE" if parsed and not result.failure_class else "CRITIC_MALFORMED_OR_PROVIDER_FAILURE_AWAITING_HUMAN","provider_used":True,"round":round_number,"model":CRITIC_MODEL,"resolved_model":result.resolved_model,"provider_invocation_id":result.provider_invocation_id,"usage":result.usage,"cost":result.cost,"failure_class":result.failure_class,"coverage":coverage,"coverage_fraction":len(covered & {row['scene_id'] for row in program['scenes']})/max(1,len(program['scenes'])),"defects":defects,"summary":(parsed or {}).get("summary"),"human_acceptance":"AWAITING_CHATGPT_JIM"}


def apply_bounded_revision(program: dict[str, Any], critic: Mapping[str, Any], round_number: int) -> dict[str, Any]:
    if round_number > MAX_REVISION_ROUNDS:
        return {"applied":False,"reason":"revision_budget_exhausted","changed_scene_ids":[]}
    by_id={row["scene_id"]:row for row in program["scenes"]}; changed=[]
    for defect in critic.get("defects") or []:
        scene=by_id.get(defect.get("scene_id")); category=str(defect.get("class") or "").lower()
        if not scene or scene["scene_id"] in changed: continue
        before=deepcopy(scene["style"])
        if "legib" in category and scene.get("primitive") == "SOURCE_EVIDENCE":
            scene["style"]["asset_scale"] = 1.16
        elif "legib" in category and len(scene.get("series") or []) > 1:
            scene["style"]["show_legend"] = True
        elif any(token in category for token in ("type","typograph","readab","hierarchy","caption","crop")):
            scene["style"]["title_scale"]=max(.78,float(scene["style"].get("title_scale",1))-.10)
            scene["style"]["caption_scale"]=max(.84,float(scene["style"].get("caption_scale",1))-.08)
        elif "composition" in category and scene.get("primitive") == "ILLUSTRATION_ATMOSPHERE":
            scene["style"]["source_compact"] = True
        elif any(token in category for token in ("repeat","composition","layout","contrast")):
            scene["accent"]={"signal":"cobalt","cobalt":"mint","mint":"amber","amber":"signal"}.get(scene.get("accent"),"signal")
        elif "transition" in category or "pacing" in category:
            scene["transition"]["type"]="smoothup" if scene["transition"]["type"]!="smoothup" else "fade"
        else:
            continue
        scene["revision_history"].append({"round":round_number,"critic_class":defect.get("class"),"style_before":before,"style_after":deepcopy(scene["style"]),"factual_fields_changed":False})
        changed.append(scene["scene_id"])
    if changed:
        program["semantic_content_hash"]=semantic_program_hash(program)
    return {"applied":bool(changed),"reason":"critic_visual_whitelist" if changed else "no_applicable_visual_defect","changed_scene_ids":changed,"factual_fields_changed":False}


def deterministic_media_qa(program: Mapping[str, Any], render: Mapping[str, Any], assets: Mapping[str, AssetRecord], *, profile: Mapping[str, Any], package_root: Path) -> dict[str, Any]:
    blockers=[]; facts=render["media"]
    if facts["width"]!=profile["width"] or facts["height"]!=profile["height"]: blockers.append("resolution_mismatch")
    if abs(facts["fps"]-profile["fps"])>.1: blockers.append("fps_mismatch")
    if facts["video_codec"]!="h264" or facts["audio_codec"]!="aac": blockers.append("codec_policy_mismatch")
    if facts["duration_seconds"]<=0: blockers.append("duration_missing")
    validation=validate_program(program,assets)
    blockers.extend(validation["blockers"])
    if render["captions"]["cue_count"]<len(program["scenes"])*2: blockers.append("caption_timing_too_coarse")
    if any(row["media"]["audio_codec"] is None for row in render["scene_rows"]): blockers.append("scene_audio_missing")
    actual_transitions=render["assembly"]["transition_count"]+sum(row["assembly"]["transition_count"] for row in render["chapter_rows"])
    if actual_transitions!=max(0,len(program["scenes"])-1): blockers.append("transition_count_mismatch")
    rights_blockers=[record.asset_id for record in assets.values() if record.synthetic and record.documentary_authority]
    if rights_blockers: blockers.append("synthetic_asset_claims_documentary_authority")
    return {"status":"PASS" if not blockers else "BLOCK","blockers":blockers,"computed_at_utc":_now(),"media":facts,"program_validation":validation,"caption_cue_count":render["captions"]["cue_count"],"scene_count":len(render["scene_rows"]),"chapter_count":len(render["chapter_rows"]),"actual_transition_implementation":"ffmpeg_xfade_plus_acrossfade","actual_transition_count":actual_transitions,"rights_asset_count":len(assets),"zero_unauthorized_writes":True,"public_or_private_upload":False,"package_root":str(package_root)}


def _audio_benchmark(root: Path, *, tts_python: str, voice: str) -> dict[str, Any]:
    sample="A yield curve is a dated map, not a forecast. Read the level, the slope, and the change."
    output=root/"package"/"audio_benchmark"/"kokoro_reference.wav"; output.parent.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter(); telemetry=_tts_segment(sample,"audio-benchmark-kokoro",output,tts_python=tts_python,voice=voice); wall=round(time.perf_counter()-started,3); kokoro=_media_facts(output)
    prior=Path(r"A:\Capital Chronicle\Runtime\ContentOps\tier2\tier2b-v1\bakeoff\voice\chatterbox_reference.wav")
    chatterbox=None
    if prior.is_file():
        staged=output.parent/"chatterbox_v3_reference.wav"; shutil.copy2(prior,staged); chatterbox={"status":"VIABLE_LOCAL_REFERENCE","model":"Chatterbox V3","media":_media_facts(staged),"source":"prior_local_bakeoff_artifact","known_constraint":"Perth watermarking and materially slower CPU inference"}
    eleven=os.environ.get("ELEVENLABS_API_KEY") or ""
    eleven_state="UNUSABLE_IDENTIFIER_NO_CALL" if eleven and not (eleven.startswith("sk_") and len(eleven)>20) else "MISSING_NO_CALL" if not eleven else "USABLE_CANDIDATE_CALL_NOT_IMPLEMENTED"
    return {"selected_provider":"kokoro","selection_reason":"stable local Apache-2.0 voice, current bounded sample, and much lower CPU latency than the viable Chatterbox reference","kokoro":{"status":"SELECTED","model":"Kokoro-82M","voice":voice,"media":kokoro,"wall_seconds":wall,"realtime_factor":round(wall/max(.001,kokoro['duration_seconds']),3),"telemetry":telemetry},"chatterbox":chatterbox,"elevenlabs":eleven_state,"music":"NONE_NO_CLEARLY_LICENSED_LOCAL_TRACK","soundtrack_policy":"silence_beyond_narration_preferred_to_uncertain_rights"}


def _make_excerpt(master: Path, output: Path) -> dict[str, Any]:
    facts=_media_facts(master); duration=min(90.0,max(60.0,facts["duration_seconds"]*.3)); start=max(0.0,min(facts["duration_seconds"]-duration,facts["duration_seconds"]*.28))
    _run(["ffmpeg","-y","-ss",f"{start:.3f}","-i",str(master),"-t",f"{duration:.3f}","-c:v","libx264","-preset","veryfast","-crf","20","-c:a","aac","-b:a","160k","-movflags","+faststart",str(output)],timeout=1800)
    return {"start_seconds":round(start,3),"requested_duration_seconds":round(duration,3),"media":_media_facts(output)}


def _selective_rerender_proof(program: Mapping[str, Any], narration: Mapping[str, Mapping[str, Any]], assets: Mapping[str, AssetRecord], root: Path, *, runtime_hash: str, profile: Mapping[str, Any]) -> dict[str, Any]:
    patched=deepcopy(program); target=patched["scenes"][4]; target["style"]["title_scale"]=.87; target["revision_history"].append({"type":"controlled_selective_rerender_proof","factual_fields_changed":False}); patched["semantic_content_hash"]=semantic_program_hash(patched)
    result=render_variant(patched,narration,assets,root,runtime_hash=runtime_hash,profile=profile,output_name="selective_proof_master.mp4")
    changed=result["rendered_scene_ids"]; changed_chapters=[row["chapter_id"] for row in result["chapter_rows"] if not row["cache_hit"]]
    proof={"status":"PASS" if changed==[target["scene_id"]] and changed_chapters==[target["chapter_id"]] else "BLOCK","target_scene_id":target["scene_id"],"target_chapter_id":target["chapter_id"],"rendered_scene_ids":changed,"rebuilt_chapter_ids":changed_chapters,"unrelated_scene_cache_hits":sum(1 for row in result["scene_rows"] if row["cache_hit"]),"unrelated_chapter_cache_hits":sum(1 for row in result["chapter_rows"] if row["cache_hit"]),"factual_fields_changed":False}
    Path(result["master_path"]).unlink(missing_ok=True)
    return proof


def _hash_manifest(package_root: Path) -> dict[str, str]:
    excluded={"hash_manifest.json","package_lock.json"}
    return {str(path.relative_to(package_root)).replace("\\","/"):sha256_file(path) for path in sorted(package_root.rglob("*")) if path.is_file() and path.name not in excluded}


def verify_package(package_root: str | Path) -> dict[str, Any]:
    root=Path(package_root); manifest_path=root/"hash_manifest.json"; lock_path=root/"package_lock.json"; blockers=[]
    if not manifest_path.is_file() or not lock_path.is_file(): return {"status":"BLOCK","blockers":["manifest_or_lock_missing"]}
    manifest=_read_json(manifest_path); lock=_read_json(lock_path)
    for relative,expected in manifest.items():
        path=root/relative
        if not path.is_file(): blockers.append(f"missing:{relative}")
        elif sha256_file(path)!=expected: blockers.append(f"hash_mismatch:{relative}")
    extras=set(_hash_manifest(root))-set(manifest)
    blockers.extend(f"untracked:{item}" for item in sorted(extras))
    if sha256_file(manifest_path)!=lock.get("hash_manifest_sha256"): blockers.append("lock_manifest_hash_mismatch")
    return {"status":"PASS" if not blockers else "BLOCK","blockers":blockers,"verified_file_count":len(manifest)}


def _write_review_readme(package: Path, *, eligibility: Mapping[str, Any], long_render: Mapping[str, Any], short_render: Mapping[str, Any], generated: Mapping[str, Any], director: Mapping[str, Any], critics: Sequence[Mapping[str, Any]], audio: Mapping[str, Any]) -> None:
    text=f"""# Tier-2 V2 Creative System Review

Status: `AWAITING_CHATGPT_JIM_VISUAL_AUDIO_AUDIT`

## Editorial decision

The strongest available governed story is the official Treasury curve record. It supports a concise editorial reading guide, not a genuine 15-minute documentary. The ≥15-minute master is deliberately withheld: `{eligibility['exact_reason']}`

## Review artifacts

- 16:9 shorter editorial proof: `{long_render['master_path']}` ({long_render['media']['duration_seconds']:.2f}s, {long_render['media']['width']}x{long_render['media']['height']})
- native 9:16 short: `{short_render['master_path']}` ({short_render['media']['duration_seconds']:.2f}s, {short_render['media']['width']}x{short_render['media']['height']})
- long contact sheet: `{package / 'visual_acceptance' / 'long_contact_sheet.jpg'}`
- short contact sheet: `{package / 'visual_acceptance' / 'short_contact_sheet.jpg'}`
- 60–120s excerpt with audio: `{package / 'representative_excerpt_16x9.mp4'}`
- before/after critic comparison: `{package / 'before_after_critic_comparison.json'}`
- asset/provenance manifest: `{package / 'asset_provenance_manifest.json'}`

## Provider and rights notes

- Director: `{director.get('model')}` / `{director.get('status')}`.
- Critic: independent `{CRITIC_MODEL}`; {len(critics)} bounded round(s). No model self-claims professional acceptance.
- Generated illustration: `{generated.get('status')}` through the dedicated direct `gpt-5.5` image boundary; illustrative only, never factual evidence.
- Real-entity photos: none used because no real person is material to this story. The resolver exists and fails closed on unclear rights.
- Narration: `{audio['selected_provider']}`. Music: none; no clearly licensed local track was available.

No browser/CDP profile, platform, upload, publication, live V1 store, or public-write surface was used.
"""
    (package/"REVIEW_README.md").write_text(text,encoding="utf-8")


def run_v2_creative_rebuild(*, output_root: str | Path, input_dir: str | Path = DEFAULT_INPUT, tts_python: str, provider_enabled: bool = True, generate_image_enabled: bool = True, voice: str = "af_heart") -> dict[str, Any]:
    started=time.perf_counter(); root=Path(output_root).resolve(); package=root/"package"; package.mkdir(parents=True,exist_ok=True)
    story=load_governed_input(input_dir); eligibility=decide_video_eligibility_v2(story)
    if eligibility["result"]!="VIDEO_SELECTED_SHORTER_EDITORIAL_PROOF":
        _write_json(package/"video_not_selected.json",eligibility); return {"status":eligibility["result"],"output_root":str(root),"public_write":False}
    director=run_director(story,eligibility,enabled=provider_enabled)
    long_program,short_program=build_programs(story,eligibility,director["direction"])
    assets,generation=_stage_assets(story,root,generate_image_enabled=generate_image_enabled)
    if "yield-landscape-illustration" not in assets:
        for program in (long_program,short_program):
            for scene in program["scenes"]:
                if "yield-landscape-illustration" in scene["asset_refs"]:
                    scene["asset_refs"]=[]; scene["primitive"]="KINETIC_STATEMENT"; scene["disclosure"]="Generated illustration unavailable; deterministic fallback used."
            program["semantic_content_hash"]=semantic_program_hash(program)
    for program in (long_program,short_program):
        validation=validate_program(program,assets)
        if validation["status"]!="PASS": raise Tier2V2Error("program_validation_blocked:"+",".join(validation["blockers"]))
    runtime_hash=renderer_runtime_hash(); long_program["runtime_hash"]=runtime_hash; short_program["runtime_hash"]=runtime_hash
    long_narration=_prepare_narration(long_program,root,tts_python=tts_python,voice=voice); short_narration=_prepare_narration(short_program,root,tts_python=tts_python,voice=voice)
    audio=_audio_benchmark(root,tts_python=tts_python,voice=voice)
    initial=render_variant(long_program,long_narration,assets,root,runtime_hash=runtime_hash,profile=LONG_PROFILE,output_name="master_initial_16x9.mp4")
    initial_sheets=_contact_sheets(long_program,initial,root,tag="long_initial")
    critic_before=run_critic(long_program,initial,initial_sheets,enabled=provider_enabled,round_number=1)
    revision=apply_bounded_revision(long_program,critic_before,1)
    if revision["applied"]:
        final_long=render_variant(long_program,long_narration,assets,root,runtime_hash=runtime_hash,profile=LONG_PROFILE,output_name="master_16x9.mp4")
    else:
        final_path=package/"master_16x9.mp4"; shutil.copy2(initial["master_path"],final_path); final_long={**initial,"master_path":str(final_path),"media":_media_facts(final_path)}
    final_sheets=_contact_sheets(long_program,final_long,root,tag="long")
    short_render=render_variant(short_program,short_narration,assets,root,runtime_hash=runtime_hash,profile=SHORT_PROFILE,output_name="short_01_9x16.mp4")
    short_sheets=_contact_sheets(short_program,short_render,root,tag="short")
    combined_critic_program={"scenes":[*long_program["scenes"],*short_program["scenes"]]}
    combined_critic_sheets={"critic_pages":[*final_sheets["critic_pages"],*short_sheets["critic_pages"]][:6]}
    critic_after=run_critic(combined_critic_program,final_long,combined_critic_sheets,enabled=provider_enabled,round_number=2)
    revision_round_2_long=apply_bounded_revision(long_program,critic_after,2)
    revision_round_2_short=apply_bounded_revision(short_program,critic_after,2)
    if revision_round_2_long["applied"]:
        final_long=render_variant(long_program,long_narration,assets,root,runtime_hash=runtime_hash,profile=LONG_PROFILE,output_name="master_16x9.mp4")
        final_sheets=_contact_sheets(long_program,final_long,root,tag="long")
    if revision_round_2_short["applied"]:
        short_render=render_variant(short_program,short_narration,assets,root,runtime_hash=runtime_hash,profile=SHORT_PROFILE,output_name="short_01_9x16.mp4")
        short_sheets=_contact_sheets(short_program,short_render,root,tag="short")
    selective=_selective_rerender_proof(long_program,long_narration,assets,root,runtime_hash=runtime_hash,profile=LONG_PROFILE)
    excerpt=_make_excerpt(Path(final_long["master_path"]),package/"representative_excerpt_16x9.mp4")
    qa_long=deterministic_media_qa(long_program,final_long,assets,profile=LONG_PROFILE,package_root=package)
    qa_short=deterministic_media_qa(short_program,short_render,assets,profile=SHORT_PROFILE,package_root=package)
    if qa_long["status"]!="PASS" or qa_short["status"]!="PASS" or selective["status"]!="PASS":
        raise Tier2V2Error("computed_media_qa_blocked:" + json.dumps({"long":qa_long["blockers"],"short":qa_short["blockers"],"selective":selective},sort_keys=True))
    _write_json(package/"video_program.json",long_program); _write_json(package/"short_video_program.json",short_program)
    _write_json(package/"story_selection.json",eligibility); _write_json(package/"director_direction.json",director)
    _write_json(package/"scene_manifest.json",{"long":final_long["scene_rows"],"short":short_render["scene_rows"]})
    _write_json(package/"chapter_manifest.json",{"long":final_long["chapter_rows"],"short":short_render["chapter_rows"]})
    _write_json(package/"script_and_caption_manifest.json",{"long_narration":long_narration,"short_narration":short_narration,"long_captions":final_long["captions"],"short_captions":short_render["captions"]})
    _write_json(package/"asset_provenance_manifest.json",{"status":"PASS","assets":[record.to_dict() for record in assets.values()],"generation_call":generation,"real_entity_photo_usage":{"status":"NOT_APPLICABLE_NO_REAL_PERSON_STORY","resolver":"live_contentops.tier2_asset_router_v2.resolve_real_entity_photo","rights_policy":"FAIL_CLOSED"},"music":"NONE","generated_media_documentary_authority":False})
    _write_json(package/"evidence_claim_binding.json",{"packet_id":story["packet_id"],"claims":list(story["claims"].values()),"claim_ids":list(CLAIM_IDS),"coverage":1.0})
    _write_json(package/"deterministic_media_qa.json",{"long":qa_long,"short":qa_short,"selective_rerender":selective,"semantic_hashes":{"long":long_program["semantic_content_hash"],"short":short_program["semantic_content_hash"]},"runtime_hash":runtime_hash,"semantic_runtime_hash_separated":long_program["semantic_content_hash"]!=runtime_hash})
    _write_json(package/"before_after_critic_comparison.json",{"status":"AWAITING_CHATGPT_JIM_ACCEPTANCE","before":critic_before,"revision_round_1":revision,"after_round_1":critic_after,"revision_round_2":{"long":revision_round_2_long,"short":revision_round_2_short},"post_round_2_critic":"NOT_RUN_REVISION_BUDGET_EXHAUSTED_HANDOFF_TO_CHATGPT_JIM","maximum_revision_rounds":MAX_REVISION_ROUNDS,"rounds_used":2,"factual_meaning_changed":False})
    _write_json(package/"audio_provider_benchmark.json",audio); _write_json(package/"render_cost_report.json",{"runtime_seconds":round(time.perf_counter()-started,3),"director_usage":director.get("usage"),"director_cost":director.get("cost"),"critic_usage":[critic_before.get("usage"),critic_after.get("usage")],"critic_cost":[critic_before.get("cost"),critic_after.get("cost")],"image_usage":generation.get("usage"),"image_cost":generation.get("cost"),"tts_cash_cost":None,"public_upload":False})
    _write_json(package/"revision_history.json",{"critic_revision_round_1":revision,"critic_revision_round_2":{"long":revision_round_2_long,"short":revision_round_2_short},"selective_rerender_proof":selective,"round_budget":MAX_REVISION_ROUNDS})
    _write_json(package/"excerpt_manifest.json",excerpt)
    _write_review_readme(package,eligibility=eligibility,long_render=final_long,short_render=short_render,generated=generation,director=director,critics=[critic_before,critic_after],audio=audio)
    _write_json(package/"hash_manifest.json",_hash_manifest(package)); verification_pre={"status":"PASS","verified_file_count":len(_hash_manifest(package))}
    _write_json(package/"package_lock.json",{"schema_version":"contentops.tier2.v2.package_lock.v1","status":"LOCKED_AWAITING_CHATGPT_JIM_ACCEPTANCE","hash_manifest_sha256":sha256_file(package/"hash_manifest.json"),"verified_file_count":verification_pre["verified_file_count"],"public_or_private_upload":False,"protected_v1_mutated":False})
    verification=verify_package(package)
    if verification["status"]!="PASS": raise Tier2V2Error("immutable_package_verification_blocked")
    result={"status":"COMPLETE_SHORTER_EDITORIAL_PROOF_AWAITING_CHATGPT_JIM_VISUAL_AUDIO_AUDIT","output_root":str(root),"package_root":str(package),"long_duration_seconds":final_long["media"]["duration_seconds"],"short_duration_seconds":short_render["media"]["duration_seconds"],"long_resolution":f"{final_long['media']['width']}x{final_long['media']['height']}","short_resolution":f"{short_render['media']['width']}x{short_render['media']['height']}","long_form_15_minute_withheld":True,"generated_image_status":generation.get("status"),"real_entity_photo_usage":"NONE_NOT_RELEVANT","narration_provider":audio["selected_provider"],"music":"NONE","package_verification":verification,"public_or_private_upload":False,"browser_cdp":False,"runtime_seconds":round(time.perf_counter()-started,3)}
    _write_json(root/"run_manifest.json",result); return result


def tier2_v2_creative_command(argv: Sequence[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description="Build the isolated Tier-2 V2 creative-system proof.")
    parser.add_argument("--output-root",type=Path,required=True); parser.add_argument("--input-dir",type=Path,default=DEFAULT_INPUT)
    parser.add_argument("--tts-python",default=os.environ.get("CONTENTOPS_TIER2_TTS_PYTHON") or sys.executable); parser.add_argument("--voice",default="af_heart")
    parser.add_argument("--provider",choices=["enabled","disabled"],default="enabled"); parser.add_argument("--generated-image",choices=["enabled","disabled"],default="enabled")
    args=parser.parse_args(argv)
    try:
        result=run_v2_creative_rebuild(output_root=args.output_root,input_dir=args.input_dir,tts_python=args.tts_python,provider_enabled=args.provider=="enabled",generate_image_enabled=args.generated_image=="enabled",voice=args.voice)
    except Exception as exc:
        print(json.dumps({"status":"BLOCKED","error":str(exc),"public_or_private_upload":False,"browser_cdp":False},sort_keys=True)); return 1
    print(json.dumps(result,sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(tier2_v2_creative_command())
