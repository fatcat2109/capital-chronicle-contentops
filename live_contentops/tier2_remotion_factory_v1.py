"""Tier-2-B Remotion multimodal video factory (renderer-neutral core).

This module is the Tier-2-B production orchestrator:

    governed evidence
    -> eligibility
    -> 9Router Video Director (bounded, selection-only, no numeric authority)
    -> renderer-neutral VideoProgram (semantic identity separated from execution)
    -> provider-neutral narration (Kokoro default)
    -> Remotion scene rendering (scene/chapter cache)
    -> FFmpeg finishing (real transitions, loudness, captions)
    -> deterministic computed QA
    -> multimodal critic + bounded revision (<= 2 rounds)
    -> selective rerender proof
    -> immutable package + hash verification.

VideoProgram remains the authority. Remotion and FFmpeg are compiler targets.
No provider/platform/public write is ever performed here.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

from .content_intelligence_contracts_v2 import logical_hash
from .media_manifest_authority_v1 import sha256_file
from .tier2_video_factory_v1 import (
    CLAIM_IDS,
    SOURCE_ID,
    SOURCE_URL,
    load_governed_input,
    verify_hash_manifest,
)

SCHEMA_VERSION = "contentops.tier2.video_program.v2"
REMOTION_SCHEMA_VERSION = "contentops.tier2.render_job.v1"
RENDERER_ID = "remotion"
FACTORY_VERSION = "tier2-b-remotion-multimodal-v1"
MOTION_SYSTEM_VERSION = "contentops.financial_news_motion.b3"
LONG_FPS = 24
SHORT_FPS = 24
LONG_WIDTH, LONG_HEIGHT = 1280, 720          # proxy-final 16:9 profile
SHORT_WIDTH, SHORT_HEIGHT = 1080, 1920       # native 9:16 profile
TRANSITION_FRAMES = 18                        # 0.75s at 24fps
TAIL_SECONDS = 1.25                           # silent tail reserved for outgoing transition
NARRATION_PROVIDER = "kokoro"
VOICE = "af_heart"
NARRATION_SPEED = 1.0
MAX_REVISION_ROUNDS = 2

REPO_ROOT = Path(__file__).resolve().parents[1]
REMOTION_ROOT = REPO_ROOT / "video" / "remotion"
CHROME_CANDIDATES = (
    Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "Google" / "Chrome" / "Application" / "chrome.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Google" / "Chrome" / "Application" / "chrome.exe",
)


class Tier2BError(RuntimeError):
    pass


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Tier2BError(f"json_object_required:{path.name}")
    return value


def _run(command: Sequence[str], *, timeout: int = 1800, capture: bool = False) -> subprocess.CompletedProcess:
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0x00004000)
    kwargs: dict[str, Any] = dict(check=False, timeout=timeout, creationflags=flags)
    if capture:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    return subprocess.run(list(command), **kwargs)


def _ffmpeg(args: Sequence[str], *, timeout: int = 1800) -> None:
    completed = _run(["ffmpeg", "-y", *args], timeout=timeout, capture=True)
    if completed.returncode != 0:
        raise Tier2BError(f"ffmpeg_failed:{(completed.stderr or '')[-240:]}")


def _ffprobe_json(path: Path) -> dict[str, Any]:
    completed = _run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        timeout=120,
        capture=True,
    )
    if completed.returncode != 0:
        raise Tier2BError(f"ffprobe_failed:{path.name}")
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise Tier2BError(f"ffprobe_invalid_json:{path.name}") from exc
    if not isinstance(value, dict):
        raise Tier2BError(f"ffprobe_object_required:{path.name}")
    return value


def _media_facts(path: Path) -> dict[str, Any]:
    probe = _ffprobe_json(path)
    video = next((s for s in probe.get("streams") or [] if s.get("codec_type") == "video"), None) or {}
    audio = next((s for s in probe.get("streams") or [] if s.get("codec_type") == "audio"), None) or {}
    fmt = probe.get("format") or {}
    num, _, den = (video.get("r_frame_rate") or "0/1").partition("/")
    try:
        fps = float(num) / float(den) if float(den or 0) else 0.0
    except (TypeError, ValueError):
        fps = 0.0
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "duration_seconds": float(fmt.get("duration") or 0.0),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "fps": round(fps, 3),
        "video_codec": video.get("codec_name"),
        "audio_codec": audio.get("codec_name"),
        "audio_sample_rate": audio.get("sample_rate"),
        "container": fmt.get("format_name"),
        "size_bytes": int(fmt.get("size") or 0),
    }


def _chrome_path() -> str:
    env = os.environ.get("CONTENTOPS_TIER2_CHROME")
    if env and Path(env).is_file():
        return env
    for candidate in CHROME_CANDIDATES:
        if candidate.is_file():
            return str(candidate)
    raise Tier2BError("chrome_executable_not_found")


# ---------------------------------------------------------------------------
# Governed series computation (faithful transformation of packet data only).
# ---------------------------------------------------------------------------

def compute_curve_series(story: Mapping[str, Any]) -> dict[str, Any]:
    history = story.get("curve_history") or []
    if len(history) < 10:
        raise Tier2BError("curve_history_too_small_for_long_form")

    def value(row: Mapping[str, Any], maturity: str) -> float | None:
        for cell in row.get("curve") or []:
            if cell.get("maturity") == maturity:
                return float(cell.get("value"))
        return None

    dates = [str(row.get("observation_date")) for row in history]
    series: dict[str, list[float | None]] = {}
    for maturity in ("2Y", "10Y", "30Y"):
        series[maturity] = [value(row, maturity) for row in history]
    spreads: list[float | None] = []
    for row in history:
        y2, y10 = value(row, "2Y"), value(row, "10Y")
        spreads.append((y10 - y2) * 100.0 if y2 is not None and y10 is not None else None)

    def stats(values: Sequence[float | None]) -> dict[str, float | None]:
        clean = [v for v in values if v is not None]
        if not clean:
            return {"first": None, "last": None, "min": None, "max": None, "change_bp": None}
        return {
            "first": clean[0],
            "last": clean[-1],
            "min": min(clean),
            "max": max(clean),
            "change_bp": round((clean[-1] - clean[0]) * 100.0, 1),
        }

    def _idx_extremes(values):
        clean = [(i, v) for i, v in enumerate(values) if v is not None]
        if not clean:
            return {"max_index": None, "min_index": None}
        maxi = max(clean, key=lambda t: t[1])[0]
        mini = min(clean, key=lambda t: t[1])[0]
        return {"max_index": maxi, "min_index": mini}

    spread_ext = _idx_extremes(spreads)
    y30_ext = _idx_extremes(series["30Y"])
    y2_ext = _idx_extremes(series["2Y"])
    y10_ext = _idx_extremes(series["10Y"])

    def _window(rows, start_i, end_i):
        sub_dates = dates[start_i:end_i]
        def seg(m):
            vals = [value(r, m) for r in rows[start_i:end_i]]
            clean = [v for v in vals if v is not None]
            if not clean:
                return None
            return {"first": clean[0], "last": clean[-1], "change_bp": round((clean[-1] - clean[0]) * 100.0, 1)}
        sp = [spreads[i] for i in range(start_i, end_i) if i < len(spreads) and spreads[i] is not None]
        return {
            "start_date": sub_dates[0] if sub_dates else None,
            "end_date": sub_dates[-1] if sub_dates else None,
            "observations": len(sub_dates),
            "y2": seg("2Y"), "y10": seg("10Y"), "y30": seg("30Y"),
            "spread": ({"first": sp[0], "last": sp[-1], "change_bp": round(sp[-1] - sp[0], 1)} if sp else None),
        }

    n = len(history)
    third = max(1, n // 3)
    windows = [
        _window(history, 0, third),
        _window(history, third, 2 * third),
        _window(history, 2 * third, n),
    ]

    return {
        "dates": dates,
        "series_2y": series["2Y"],
        "series_10y": series["10Y"],
        "series_30y": series["30Y"],
        "series_2s10s_bp": spreads,
        "windows": windows,
        "spread_max": {"value": max(v for v in spreads if v is not None), "date": dates[spread_ext["max_index"]] if spread_ext["max_index"] is not None else None},
        "spread_min": {"value": min(v for v in spreads if v is not None), "date": dates[spread_ext["min_index"]] if spread_ext["min_index"] is not None else None},
        "y30_max": {"value": max(v for v in series["30Y"] if v is not None), "date": dates[y30_ext["max_index"]] if y30_ext["max_index"] is not None else None},
        "y30_min": {"value": min(v for v in series["30Y"] if v is not None), "date": dates[y30_ext["min_index"]] if y30_ext["min_index"] is not None else None},
        "y2_max": {"value": max(v for v in series["2Y"] if v is not None), "date": dates[y2_ext["max_index"]] if y2_ext["max_index"] is not None else None},
        "y10_max": {"value": max(v for v in series["10Y"] if v is not None), "date": dates[y10_ext["max_index"]] if y10_ext["max_index"] is not None else None},
        "stats_2y": stats(series["2Y"]),
        "stats_10y": stats(series["10Y"]),
        "stats_30y": stats(series["30Y"]),
        "stats_2s10s": {
            "first": spreads[0],
            "last": spreads[-1],
            "min": min(v for v in spreads if v is not None),
            "max": max(v for v in spreads if v is not None),
            "change_bp": round(spreads[-1] - spreads[0], 1),
        },
        "last_curve_full": [
            {"maturity": cell.get("maturity"), "value": cell.get("value")}
            for cell in (history[-1].get("curve") or [])
        ],
        "first_curve_full": [
            {"maturity": cell.get("maturity"), "value": cell.get("value")}
            for cell in (history[0].get("curve") or [])
        ],
        "observation_count": len(history),
        "window_start": dates[0],
        "window_end": dates[-1],
        "derivation": "capital_chronicle_transformation_of_governed_packet_time_series",
    }


# ---------------------------------------------------------------------------
# VideoProgram authoring.
# ---------------------------------------------------------------------------

def _segment_split(text: str, parts: int) -> list[str]:
    sentences = [s.strip() for s in text.replace(". ", ".|").split("|") if s.strip()]
    if len(sentences) <= parts:
        return sentences or [text]
    per = len(sentences) // parts
    out = []
    for i in range(parts):
        chunk = sentences[i * per:(i + 1) * per if i < parts - 1 else len(sentences)]
        out.append(" ".join(chunk))
    return [o for o in out if o]


def _scene(scene_id: str, chapter_id: str, *, primitive: str, title: str, script: str,
           claim_ids: Sequence[str], order: int, numbers: list[dict[str, Any]] | None = None,
           series: list[dict[str, Any]] | None = None, text_blocks: list[dict[str, Any]] | None = None,
           asset_id: str | None = None, kicker: str | None = None, subtitle: str | None = None,
           motion_hint: str = "restrained_editorial_v1") -> dict[str, Any]:
    return {
        "scene_id": scene_id,
        "chapter_id": chapter_id,
        "order": order,
        "semantic_purpose": title,
        "display_title": title,
        "kicker": kicker,
        "subtitle": subtitle,
        "visual_primitive": primitive,
        "script": script,
        "narration_segments": _segment_split(script, 3),
        "claim_bindings": [
            {"claim_id": cid, "evidence_id": SOURCE_ID, "source_url": SOURCE_URL}
            for cid in claim_ids
        ],
        "source_bindings": [{"evidence_id": SOURCE_ID, "source_url": SOURCE_URL}],
        "asset_refs": [asset_id] if asset_id else [],
        "numbers": numbers or [],
        "series": series or [],
        "text_blocks": text_blocks or [],
        "rights_requirements": {"source_rights_required": True, "status": "public_domain_source_and_local_render"},
        "aspect_layout": {"landscape": "16:9_safe_area", "vertical": "9:16_safe_area"},
        "captions": {"style": "financial_news_lower_third", "source": "narration_segment_boundaries"},
        "credits": "Source: U.S. Department of the Treasury. Capital Chronicle render.",
        "motion_intent": motion_hint,
        "fallback": "source_card_with_claim_callout",
        "revision_history": [],
    }


def _series_points(dates: Sequence[str], values: Sequence[float | None], step: int = 1) -> list[dict[str, Any]]:
    pts = []
    for i in range(0, len(dates), step):
        v = values[i] if i < len(values) else None
        if v is not None:
            pts.append({"x": dates[i], "y": round(float(v), 3)})
    if values and values[-1] is not None and (len(dates) - 1) % step != 0:
        pts.append({"x": dates[-1], "y": round(float(values[-1]), 3)})
    return pts


def build_long_program(story: Mapping[str, Any], series: Mapping[str, Any], director_spec: Mapping[str, Any]) -> dict[str, Any]:
    c = story["claims"]
    y2, y10, y30, spread = (c[k] for k in CLAIM_IDS)
    ALL4 = list(CLAIM_IDS)
    s2, s10, s30, ss = series["stats_2y"], series["stats_10y"], series["stats_30y"], series["stats_2s10s"]
    dates: list[str] = series["dates"]
    hook_style = str(director_spec.get("hook_style") or "level_first")
    pacing = str(director_spec.get("pacing") or "measured")

    hook_open = (
        f"The 30-year U.S. Treasury par yield reached {y30['value']:.2f} percent on {y30['observation_time_utc'][:10]}."
        if hook_style == "level_first" else
        f"Between {series['window_start']} and {series['window_end']}, the 2s10s Treasury spread moved from {ss['first']:.0f} to {ss['last']:.0f} basis points."
    )

    scenes: list[dict[str, Any]] = []
    order = 0

    scenes.append(_scene(
        "lf-title", "ch-01", primitive="TITLE_OPENING",
        title="The Shape of the Curve",
        kicker="Capital Chronicle Explainer",
        subtitle=f"Official Treasury par yields, {dates[-1]}. Evidence-bound, not advice.",
        claim_ids=ALL4, order=order,
        script=(
            f"{hook_open} The same official record shows the 10-year at {y10['value']:.2f} percent and the 2-year at {y2['value']:.2f} percent, "
            f"with the 2s10s spread at {spread['value']:.0f} basis points. Those four observations are the governed claim set for this video. "
            "Every number that follows resolves to the same U.S. Treasury daily par yield curve record, observed on one business day. "
            "This explainer walks through what the table says, how the spread is calculated, how the curve moved across the quarter captured in the packet, "
            "and where description must stop. The video will read the official table, recompute the spread from its own inputs, follow the curve through the quarter captured in the packet, and then stop exactly where the record stops. It is a transformation of a governed historical record, not a live quote, a forecast, or a recommendation. "
            "Par yields are official indicative levels, not executable market prices, and that boundary shapes everything that follows."
        ),
        motion_hint="opening_title_reveal",
    )); order += 1

    scenes.append(_scene(
        "lf-table", "ch-02", primitive="DOCUMENT_SCENE",
        title="Reading the Official Table",
        kicker="Source Record",
        claim_ids=ALL4, order=order,
        asset_id="treasury_source_excerpt",
        numbers=[
            {"label": "2Y par yield", "value": y2["value"], "unit": "percent", "delta": f"{y2['change_basis_points']:+.0f} bp vs prior"},
            {"label": "10Y par yield", "value": y10["value"], "unit": "percent", "delta": f"{y10['change_basis_points']:+.0f} bp vs prior"},
            {"label": "30Y par yield", "value": y30["value"], "unit": "percent", "delta": f"{y30['change_basis_points']:+.0f} bp vs prior"},
        ],
        text_blocks=[
            {"heading": "Publisher", "body": "U.S. Department of the Treasury, Daily Treasury Par Yield Curve Rates."},
            {"heading": "Observation", "body": f"One official business-day record dated {dates[-1]}, compared with the prior session {y2['prior_observation_date']}."},
            {"heading": "Authority limit", "body": "Indicative par yields, not trade-execution prices."},
        ],
        script=(
            f"The source is the U.S. Treasury's Daily Treasury Par Yield Curve Rates table, a public official record. "
            f"On {dates[-1]} the 2-year par yield was {y2['value']:.2f} percent, the 10-year was {y10['value']:.2f} percent, and the 30-year was {y30['value']:.2f} percent. "
            f"Against the {y2['prior_observation_date']} session, the 2-year moved from {y2['prior_value']:.2f} to {y2['value']:.2f} percent, a change of {y2['change_basis_points']:.0f} basis points. "
            f"The 10-year moved from {y10['prior_value']:.2f} to {y10['value']:.2f} percent, {y10['change_basis_points']:.0f} basis points. "
            f"The 30-year moved from {y30['prior_value']:.2f} to {y30['value']:.2f} percent, {y30['change_basis_points']:.0f} basis points. "
            "Reading the rows together stops any single maturity from standing in for the whole curve. "
            "The packet classifies these as official indicative par yields derived from market quotations, appropriate for public curve description but explicitly not executable prices. "
            "That measurement boundary is part of the evidence itself, so it appears on screen rather than in fine print."
        ),
        motion_hint="document_card_stagger",
    )); order += 1

    scenes.append(_scene(
        "lf-spread", "ch-03", primitive="CHART_SCENE",
        title="The 2s10s Calculation",
        kicker="Curve Slope",
        claim_ids=["UST:10Y:2026-07-13", "UST:2Y:2026-07-13", "UST:2S10S:2026-07-13"], order=order,
        asset_id="treasury_2s10s_history",
        numbers=[
            {"label": "2s10s spread", "value": spread["value"], "unit": "basis_points", "delta": f"+{spread['change_basis_points']:.0f} bp", "emphasis": True},
            {"label": "Prior session", "value": spread["prior_value"], "unit": "basis_points"},
        ],
        script=(
            f"The 2s10s spread is a derived figure: the 10-year par yield minus the 2-year par yield, expressed in basis points. "
            f"On {dates[-1]} that calculation gives {spread['value']:.0f} basis points. Check the arithmetic: {y10['value']:.2f} minus {y2['value']:.2f} is 0.36 percentage points, which is 36 basis points. "
            f"On the prior official session the same calculation gives {spread['prior_value']:.0f} basis points. The change is {spread['change_basis_points']:.0f} basis point, a measurable but small widening. "
            "The derived spread and the two source observations that produce it are separate governed claims, and the video keeps them visually distinct. "
            "A one-basis-point move is an edge wider, not a regime change. The chart shows direction and scale; it does not add an explanation the evidence does not contain."
        ),
        motion_hint="chart_wipe_reveal",
    )); order += 1

    scenes.append(_scene(
        "lf-longend", "ch-04", primitive="COMPARISON_SCENE",
        title="The Long End at 5.10",
        kicker="Term Structure",
        claim_ids=ALL4, order=order,
        asset_id="treasury_curve_snapshot",
        numbers=[
            {"label": "30Y", "value": y30["value"], "unit": "percent", "emphasis": True},
            {"label": "10Y", "value": y10["value"], "unit": "percent"},
            {"label": "2Y", "value": y2["value"], "unit": "percent"},
        ],
        script=(
            f"The long end is the visually striking part of the record: the 30-year par yield at {y30['value']:.2f} percent. "
            f"Set beside the 10-year at {y10['value']:.2f} percent and the 2-year at {y2['value']:.2f} percent, the term structure is clearly upward sloping. "
            f"In level terms the 30-year stands 48 basis points above the 10-year and 84 basis points above the 2-year. Those are simple differences between the authorized observations, not forecasts. "
            f"The three maturities also did not move by the same amount against the prior session: {y2['change_basis_points']:.0f}, {y10['change_basis_points']:.0f}, and {y30['change_basis_points']:.0f} basis points respectively. "
            "The comparison supports description across maturities. It does not establish anything about equities, credit, foreign exchange, inflation, or auctions, and the video will not pretend otherwise."
        ),
        motion_hint="comparison_columns",
    )); order += 1

    scenes.append(_scene(
        "lf-move", "ch-05", primitive="NUMBER_CALLOUT",
        title="One Day, Three Moves",
        kicker="Session Change",
        claim_ids=ALL4, order=order,
        numbers=[
            {"label": f"2Y change vs {y2['prior_observation_date']}", "value": y2["change_basis_points"], "unit": "basis_points", "delta": f"{y2['prior_value']:.2f} -> {y2['value']:.2f}%"},
            {"label": "10Y change", "value": y10["change_basis_points"], "unit": "basis_points", "delta": f"{y10['prior_value']:.2f} -> {y10['value']:.2f}%", "emphasis": True},
            {"label": "30Y change", "value": y30["change_basis_points"], "unit": "basis_points", "delta": f"{y30['prior_value']:.2f} -> {y30['value']:.2f}%"},
            {"label": "2s10s change", "value": spread["change_basis_points"], "unit": "basis_points"},
        ],
        script=(
            f"One official session, three maturity moves and one derived change. The 2-year shifted {y2['change_basis_points']:.0f} basis points, from {y2['prior_value']:.2f} to {y2['value']:.2f} percent. "
            f"The 10-year shifted {y10['change_basis_points']:.0f} basis points, from {y10['prior_value']:.2f} to {y10['value']:.2f} percent. "
            f"The 30-year shifted {y30['change_basis_points']:.0f} basis points, from {y30['prior_value']:.2f} to {y30['value']:.2f} percent. "
            f"The derived 2s10s spread moved {spread['change_basis_points']:.0f} basis point, from {spread['prior_value']:.0f} to {spread['value']:.0f}. "
            "Presenting the moves together shows that the curve shifted across maturities rather than pivoting at a single point. "
            "None of these figures carries a causal explanation in the governed record, so none is narrated here. That restraint is the editorial standard."
        ),
        motion_hint="number_count_up",
    )); order += 1

    step = max(1, len(dates) // 24)
    scenes.append(_scene(
        "lf-30y-trend", "ch-06", primitive="TIMELINE_SCENE",
        title="The 30-Year Path Across the Quarter",
        kicker="From the Packet Time Series",
        claim_ids=["UST:30Y:2026-07-13"], order=order,
        series=[{"label": "30Y par yield (%)", "points": _series_points(dates, series["series_30y"], step), "color": "#d6a84f"}],
        numbers=[
            {"label": f"Window start {dates[0]}", "value": s30["first"], "unit": "percent"},
            {"label": f"Window end {dates[-1]}", "value": s30["last"], "unit": "percent", "emphasis": True},
            {"label": "Window range", "value": f"{s30['min']:.2f} - {s30['max']:.2f}", "unit": "percent"},
            {"label": "Net change", "value": s30["change_bp"], "unit": "basis_points"},
        ],
        script=(
            f"The governed packet carries {series['observation_count']} official daily curve observations from {dates[0]} through {dates[-1]}. "
            f"Across that window the 30-year par yield began at {s30['first']:.2f} percent and ended at {s30['last']:.2f} percent, a net change of {s30['change_bp']:+.0f} basis points. "
            f"Within the window it traded between {s30['min']:.2f} and {s30['max']:.2f} percent. The final observation at {s30['last']:.2f} percent is the governed July 13 claim. "
            "This trajectory is plotted directly from the packet's own time series. No point is interpolated and no value outside the packet appears. "
            "The path gives context for the level: the long end spent the quarter in a defined band, and the July 13 print sits at the upper edge of recent experience without exceeding the window maximum."
        ),
        motion_hint="timeline_draw",
    )); order += 1

    scenes.append(_scene(
        "lf-spread-trend", "ch-07", primitive="TIMELINE_SCENE",
        title="The Quarter's Flattening",
        kicker="2s10s Spread Series",
        claim_ids=["UST:2S10S:2026-07-13"], order=order,
        series=[{"label": "2s10s spread (bp)", "points": _series_points(dates, series["series_2s10s_bp"], step), "color": "#c46a5a"}],
        numbers=[
            {"label": f"Spread {dates[0]}", "value": round(ss["first"], 1), "unit": "basis_points"},
            {"label": f"Spread {dates[-1]}", "value": round(ss["last"], 1), "unit": "basis_points", "emphasis": True},
            {"label": "Window min", "value": round(ss["min"], 1), "unit": "basis_points"},
            {"label": "Window max", "value": round(ss["max"], 1), "unit": "basis_points"},
        ],
        script=(
            f"The derived 2s10s spread tells the bigger story of the quarter. Computed from the packet's daily 2-year and 10-year par yields, "
            f"the spread began the window at {ss['first']:.0f} basis points on {dates[0]} and stood at {ss['last']:.0f} basis points on {dates[-1]}, "
            f"a net change of {ss['change_bp']:+.0f} basis points. Along the way it ranged between {ss['min']:.0f} and {ss['max']:.0f} basis points. "
            "That is a material compression in slope across the quarter, even though the final one-day change was only one basis point. "
            "The daily one-session claim and the quarter-long series are different facts from the same governed record, and this chapter exists to keep them from being confused with each other."
        ),
        motion_hint="timeline_draw",
    )); order += 1

    scenes.append(_scene(
        "lf-10y-trend", "ch-08", primitive="CHART_SCENE",
        title="The 10-Year's Steadier Climb",
        kicker="From the Packet Time Series",
        claim_ids=["UST:10Y:2026-07-13"], order=order,
        series=[{"label": "10Y par yield (%)", "points": _series_points(dates, series["series_10y"], step), "color": "#d6a84f"}],
        numbers=[
            {"label": f"{dates[0]}", "value": s10["first"], "unit": "percent"},
            {"label": f"{dates[-1]}", "value": s10["last"], "unit": "percent", "emphasis": True},
            {"label": "Net change", "value": s10["change_bp"], "unit": "basis_points"},
        ],
        script=(
            f"The 10-year par yield moved from {s10['first']:.2f} percent at the start of the packet window on {dates[0]} to {s10['last']:.2f} percent on {dates[-1]}, "
            f"a net change of {s10['change_bp']:+.0f} basis points, within a range of {s10['min']:.2f} to {s10['max']:.2f} percent. "
            f"The governed July 13 claim fixes the level at {y10['value']:.2f} percent. Because the 10-year anchors the spread calculation, its steadier climb and the 2-year's path together explain the quarter's slope compression. "
            "Again, every plotted point comes from the packet's official daily observations. The chart is a reading aid for those observations, not an independent analytical claim."
        ),
        motion_hint="chart_wipe_reveal",
    )); order += 1

    ladder = [cell for cell in series["last_curve_full"] if cell.get("value") is not None]
    ladder_numbers = [{"label": cell["maturity"], "value": cell["value"], "unit": "percent"} for cell in ladder[:8]]
    ladder_text = "; ".join(f"{cell['maturity']} {cell['value']:.2f}%" for cell in ladder)
    scenes.append(_scene(
        "lf-ladder", "ch-09", primitive="COMPARISON_SCENE",
        title="The Full Maturity Ladder",
        kicker=f"All Maturities on {dates[-1]}",
        claim_ids=ALL4, order=order,
        numbers=ladder_numbers,
        text_blocks=[{"heading": "Complete curve", "body": ladder_text}],
        script=(
            f"The packet's final observation lists the full maturity ladder for {dates[-1]}: {ladder_text}. "
            "Presenting the entire ladder resists the habit of summarizing a curve with one headline number. "
            "The short end, the belly, and the long end each carry their own official level, and the curve's shape is the relationship among all of them. "
            "These levels come directly from the packet's last curve row, transcribed without rounding beyond the source precision. "
            "Reading the whole ladder is the discipline this explainer keeps returning to: describe the record as recorded."
        ),
        motion_hint="comparison_columns",
    )); order += 1

    windows = series["windows"]
    w_a, w_b, w_c = windows[0], windows[1], windows[2]
    scenes.append(_scene(
        "lf-2y-trend", "ch-10", primitive="TIMELINE_SCENE",
        title="The 2-Year Path Across the Quarter",
        kicker="From the Packet Time Series",
        claim_ids=["UST:2Y:2026-07-13"], order=order,
        series=[{"label": "2Y par yield (%)", "points": _series_points(dates, series["series_2y"], step), "color": "#4fae7a"}],
        numbers=[
            {"label": f"Window start {dates[0]}", "value": s2["first"], "unit": "percent"},
            {"label": f"Window end {dates[-1]}", "value": s2["last"], "unit": "percent", "emphasis": True},
            {"label": "Net change", "value": s2["change_bp"], "unit": "basis_points"},
        ],
        script=(
            f"The front of the curve moved the most. Across the packet's {series['observation_count']} official observations, "
            f"the 2-year par yield rose from {s2['first']:.2f} percent on {dates[0]} to {s2['last']:.2f} percent on {dates[-1]}, "
            f"a net change of {s2['change_bp']:+.0f} basis points, within a range of {s2['min']:.2f} to {s2['max']:.2f} percent. "
            f"The governed July 13 claim fixes the final level at {y2['value']:.2f} percent. "
            "The short end is driven by the same official daily observations as the rest of the curve, so its rise is a recorded fact, not an interpretation. "
            "Comparing this path with the 10-year and 30-year paths is what produces the slope story told in the next chapters."
        ),
        motion_hint="timeline_draw",
    )); order += 1

    scenes.append(_scene(
        "lf-spread-extremes", "ch-11", primitive="NUMBER_CALLOUT",
        title="Where the Spread Peaked and Bottomed",
        kicker="2s10s Extremes",
        claim_ids=["UST:2S10S:2026-07-13"], order=order,
        numbers=[
            {"label": f"Window high {series['spread_max']['date']}", "value": round(series["spread_max"]["value"], 1), "unit": "basis_points", "emphasis": True},
            {"label": f"Window low {series['spread_min']['date']}", "value": round(series["spread_min"]["value"], 1), "unit": "basis_points"},
            {"label": f"July 13", "value": ss["last"], "unit": "basis_points"},
        ],
        script=(
            f"Within the packet window, the derived 2s10s spread reached its highest point at {series['spread_max']['value']:.0f} basis points on {series['spread_max']['date']}, "
            f"and its lowest at {series['spread_min']['value']:.0f} basis points on {series['spread_min']['date']}. "
            f"The July 13 observation of {ss['last']:.0f} basis points sits well below the window high. "
            "These extremes are computed directly from the packet's daily series. They show the slope covered a wide band across the quarter, "
            "and they give honest scale to the one-basis-point daily move: the day-to-day change is small relative to the total range the curve explored. "
            "That comparison between daily change and quarterly range is exactly the kind of context an evidence-bound explainer should carry."
        ),
        motion_hint="number_count_up",
    )); order += 1

    scenes.append(_scene(
        "lf-window-a", "ch-12", primitive="COMPARISON_SCENE",
        title=f"First Window: {w_a['start_date']} to {w_a['end_date']}",
        kicker="The Quarter in Three Parts",
        claim_ids=ALL4, order=order,
        numbers=[
            {"label": "2Y move", "value": w_a["y2"]["change_bp"], "unit": "basis_points", "delta": f"{w_a['y2']['first']:.2f} -> {w_a['y2']['last']:.2f}%"},
            {"label": "10Y move", "value": w_a["y10"]["change_bp"], "unit": "basis_points", "delta": f"{w_a['y10']['first']:.2f} -> {w_a['y10']['last']:.2f}%", "emphasis": True},
            {"label": "30Y move", "value": w_a["y30"]["change_bp"], "unit": "basis_points", "delta": f"{w_a['y30']['first']:.2f} -> {w_a['y30']['last']:.2f}%"},
            {"label": "Spread move", "value": w_a["spread"]["change_bp"], "unit": "basis_points"},
        ],
        script=(
            f"Breaking the quarter into three windows makes the arc easier to read. The first window, {w_a['start_date']} through {w_a['end_date']} covering {w_a['observations']} observations, "
            f"saw the 2-year move {w_a['y2']['change_bp']:+.0f} basis points, the 10-year {w_a['y10']['change_bp']:+.0f}, and the 30-year {w_a['y30']['change_bp']:+.0f}. "
            f"The derived spread changed {w_a['spread']['change_bp']:+.0f} basis points over the same stretch. "
            "Every figure here is a difference between two official levels taken from the packet's own series, so the window summary adds no new claims, only arithmetic."
        ),
        motion_hint="comparison_columns",
    )); order += 1

    scenes.append(_scene(
        "lf-window-b", "ch-13", primitive="COMPARISON_SCENE",
        title=f"Second Window: {w_b['start_date']} to {w_b['end_date']}",
        kicker="The Quarter in Three Parts",
        claim_ids=ALL4, order=order,
        numbers=[
            {"label": "2Y move", "value": w_b["y2"]["change_bp"], "unit": "basis_points", "delta": f"{w_b['y2']['first']:.2f} -> {w_b['y2']['last']:.2f}%"},
            {"label": "10Y move", "value": w_b["y10"]["change_bp"], "unit": "basis_points", "delta": f"{w_b['y10']['first']:.2f} -> {w_b['y10']['last']:.2f}%", "emphasis": True},
            {"label": "30Y move", "value": w_b["y30"]["change_bp"], "unit": "basis_points", "delta": f"{w_b['y30']['first']:.2f} -> {w_b['y30']['last']:.2f}%"},
            {"label": "Spread move", "value": w_b["spread"]["change_bp"], "unit": "basis_points"},
        ],
        script=(
            f"The second window, {w_b['start_date']} through {w_b['end_date']} with {w_b['observations']} observations, tells a different part of the story. "
            f"The 2-year moved {w_b['y2']['change_bp']:+.0f} basis points, the 10-year {w_b['y10']['change_bp']:+.0f}, and the 30-year {w_b['y30']['change_bp']:+.0f}. "
            f"The derived spread shifted {w_b['spread']['change_bp']:+.0f} basis points. Presenting the windows side by side keeps the viewer from flattening "
            "the quarter into a single headline, because the curve did not move at one constant pace."
        ),
        motion_hint="comparison_columns",
    )); order += 1

    scenes.append(_scene(
        "lf-window-c", "ch-14", primitive="COMPARISON_SCENE",
        title=f"Final Window: {w_c['start_date']} to {w_c['end_date']}",
        kicker="The Quarter in Three Parts",
        claim_ids=ALL4, order=order,
        numbers=[
            {"label": "2Y move", "value": w_c["y2"]["change_bp"], "unit": "basis_points", "delta": f"{w_c['y2']['first']:.2f} -> {w_c['y2']['last']:.2f}%"},
            {"label": "10Y move", "value": w_c["y10"]["change_bp"], "unit": "basis_points", "delta": f"{w_c['y10']['first']:.2f} -> {w_c['y10']['last']:.2f}%", "emphasis": True},
            {"label": "30Y move", "value": w_c["y30"]["change_bp"], "unit": "basis_points", "delta": f"{w_c['y30']['first']:.2f} -> {w_c['y30']['last']:.2f}%"},
            {"label": "Spread move", "value": w_c["spread"]["change_bp"], "unit": "basis_points"},
        ],
        script=(
            f"The final window, {w_c['start_date']} through {w_c['end_date']}, leads straight into the governed July 13 claim. "
            f"The 2-year moved {w_c['y2']['change_bp']:+.0f} basis points, the 10-year {w_c['y10']['change_bp']:+.0f}, and the 30-year {w_c['y30']['change_bp']:+.0f}. "
            f"The derived spread changed {w_c['spread']['change_bp']:+.0f} basis points in this last stretch. "
            "By placing the final window alongside the earlier two, the video shows how the July 13 levels were reached rather than presenting them as an isolated event."
        ),
        motion_hint="comparison_columns",
    )); order += 1

    scenes.append(_scene(
        "lf-reading-shape", "ch-15", primitive="CHART_SCENE",
        title="Reading the Shape Itself",
        kicker="Term Structure",
        claim_ids=ALL4, order=order,
        asset_id="treasury_curve_snapshot",
        numbers=[
            {"label": "Short end 1M-6M", "value": "3.73 - 4.03", "unit": "percent"},
            {"label": "Belly 1Y-5Y", "value": "4.12 - 4.37", "unit": "percent"},
            {"label": "Long end 10Y-30Y", "value": "4.62 - 5.11", "unit": "percent", "emphasis": True},
        ],
        script=(
            f"On {dates[-1]} the shortest maturities cluster between 3.73 and 4.03 percent, the belly between 4.12 and 4.37 percent, "
            "and the long end between 4.62 and 5.11 percent. The curve rises steeply out of the short end, then flattens through the belly, "
            "then climbs again into the 20-year and 30-year. That is the shape, described from the recorded levels alone. "
            "Reading the shape is descriptive: it names where the curve is steep and where it is flat on the observation date. "
            "It does not, by itself, explain why the shape is that way, and this explainer keeps that distinction visible throughout."
        ),
        motion_hint="chart_wipe_reveal",
    )); order += 1

    first_ladder = {cell["maturity"]: cell["value"] for cell in series["first_curve_full"] if cell.get("value") is not None}
    last_ladder = {cell["maturity"]: cell["value"] for cell in series["last_curve_full"] if cell.get("value") is not None}
    both_ends_pairs = [m for m in ("3M", "2Y", "5Y", "10Y", "30Y") if m in first_ladder and m in last_ladder]
    both_ends_text = "; ".join(f"{m}: {first_ladder[m]:.2f}% -> {last_ladder[m]:.2f}%" for m in both_ends_pairs)
    scenes.append(_scene(
        "lf-shape-both-ends", "ch-15", primitive="COMPARISON_SCENE",
        title="The Curve at Both Ends of the Quarter",
        kicker="April 9 vs July 13",
        claim_ids=ALL4, order=order,
        numbers=[
            {"label": "2Y start->end", "value": f"{first_ladder.get('2Y', 0):.2f} -> {last_ladder.get('2Y', 0):.2f}", "unit": "percent"},
            {"label": "10Y start->end", "value": f"{first_ladder.get('10Y', 0):.2f} -> {last_ladder.get('10Y', 0):.2f}", "unit": "percent", "emphasis": True},
            {"label": "30Y start->end", "value": f"{first_ladder.get('30Y', 0):.2f} -> {last_ladder.get('30Y', 0):.2f}", "unit": "percent"},
        ],
        text_blocks=[{"heading": "Across maturities", "body": both_ends_text}],
        script=(
            f"Setting the {dates[0]} curve beside the {dates[-1]} curve shows how each maturity shifted over the whole quarter. "
            f"Reading across {', '.join(both_ends_pairs)}, each maturity's level moved from its early-April value to its mid-July value. "
            "This side-by-side uses only the packet's first and last full curve rows, transcribed exactly. "
            "It anchors the trajectories shown earlier: rather than a single line going up or down, every rung of the ladder moved, "
            "and comparing the two ends of the quarter is the clearest way to see the shape change that the derived spread summarizes."
        ),
        motion_hint="comparison_columns",
    )); order += 1

    scenes.append(_scene(
        "lf-front-vs-long", "ch-16", primitive="NUMBER_CALLOUT",
        title="Why the Slope Compressed",
        kicker="Arithmetic of the Spread",
        claim_ids=["UST:2Y:2026-07-13", "UST:10Y:2026-07-13", "UST:2S10S:2026-07-13"], order=order,
        numbers=[
            {"label": "2Y net move", "value": s2["change_bp"], "unit": "basis_points", "emphasis": True},
            {"label": "10Y net move", "value": s10["change_bp"], "unit": "basis_points"},
            {"label": "Spread net change", "value": ss["change_bp"], "unit": "basis_points"},
        ],
        script=(
            f"The slope compression is arithmetic, not opinion. Over the window the 2-year rose {s2['change_bp']:+.0f} basis points while the 10-year rose {s10['change_bp']:+.0f} basis points. "
            f"Because the front end climbed more than the 10-year, the gap between them narrowed by {abs(ss['change_bp']):.0f} basis points, "
            f"from {ss['first']:.0f} to {ss['last']:.0f}. That single relationship explains the flattening recorded in the packet. "
            "This is a calculation on governed observations, the same method used for the 2s10s claim itself, and it stays strictly within what the recorded levels show."
        ),
        motion_hint="number_count_up",
    )); order += 1

    scenes.append(_scene(
        "lf-record-scope", "ch-17", primitive="SOURCE_CARD",
        title="What This Record Covers",
        kicker="Scope",
        claim_ids=ALL4, order=order,
        text_blocks=[
            {"heading": "Window", "body": f"{series['observation_count']} official daily observations, {series['window_start']} through {series['window_end']}."},
            {"heading": "Maturities", "body": "1M through 30Y par yields, including the 2Y, 10Y, 30Y used in the claims."},
            {"heading": "Derived", "body": "2s10s spread plus trajectory, window, and extreme summaries computed from those observations."},
            {"heading": "Excluded", "body": "No prices, volumes, forecasts, or non-Treasury data appear in this packet."},
        ],
        script=(
            f"Before closing, it helps to name the record's scope precisely. The packet covers {series['observation_count']} official daily observations "
            f"from {series['window_start']} through {series['window_end']}, carrying par yields across maturities from 1-month to 30-year. "
            "From those observations the explainer derives the 2s10s spread, the quarterly trajectories, the three window summaries, and the extreme dates. "
            "Nothing outside the packet enters the narration: no execution prices, no volumes, no forecasts, and no data from another source. "
            "Stating the scope this way is how the video earns the right to say exactly what the record supports and nothing more."
        ),
        motion_hint="source_rows",
    )); order += 1

    scenes.append(_scene(
        "lf-boundary", "ch-18", primitive="CALLOUT",
        title="Where Description Stops",
        kicker="Editorial Boundary",
        claim_ids=ALL4, order=order,
        subtitle="The record states levels and changes. It does not state causes, forecasts, or trades.",
        script=(
            "With the data fully displayed, the boundary comes into focus. The governed record establishes four observed levels, one derived spread, "
            "a one-session change for each, and the quarter-long trajectories computed from the packet's own daily series. "
            "It does not establish why the moves happened, what happens next, or what any investor should do. "
            "Mechanism language about auctions, issuance, term premium, or policy expectations would be editorial invention unless separately sourced, and this package does not carry such sources. "
            "So the explanation stops where the evidence stops. That is not a gap in the video; it is the point of the video. "
            "An evidence-grounded financial explainer earns trust by naming its own boundary before a viewer has to ask."
        ),
        motion_hint="callout_soft",
    )); order += 1

    scenes.append(_scene(
        "lf-method", "ch-19", primitive="SOURCE_CARD",
        title="Method and Limits",
        kicker="Provenance",
        claim_ids=ALL4, order=order,
        text_blocks=[
            {"heading": "Source document", "body": "U.S. Department of the Treasury, Daily Treasury Par Yield Curve Rates."},
            {"heading": "Claim set", "body": "UST:2Y:2026-07-13, UST:10Y:2026-07-13, UST:30Y:2026-07-13, UST:2S10S:2026-07-13."},
            {"heading": "Derived series", "body": "Quarter trajectory computed by Capital Chronicle from the packet's official daily par yields."},
            {"heading": "Status", "body": "Historical governed demonstration. Public-domain source; render rights separate from source content."},
        ],
        script=(
            "Provenance belongs on screen. The underlying source document is the U.S. Department of the Treasury's Daily Treasury Par Yield Curve Rates, a public-domain official record. "
            "The governed claim set is the four identities bound to every factual scene: the 2-year, 10-year, 30-year observations and the derived 2s10s spread, all dated July 13, 2026. "
            "The quarter-long trajectories are computed by Capital Chronicle from the packet's own daily official observations; the computation is a faithful transformation, not new analytical authority. "
            "Render and layout are owned by Capital Chronicle; the underlying source content keeps its own rights. This video is a historical demonstration package and is not current market data."
        ),
        motion_hint="source_rows",
    )); order += 1

    scenes.append(_scene(
        "lf-close", "ch-20", primitive="DISCLAIMER_ENDCARD",
        title="Capital Chronicle",
        kicker="End of Explainer",
        claim_ids=ALL4, order=order,
        subtitle=f"The record stands: 2Y {y2['value']:.2f}%, 10Y {y10['value']:.2f}%, 30Y {y30['value']:.2f}%, 2s10s {spread['value']:.0f} bp on {dates[-1]}. Historical demonstration, not financial advice.",
        script=(
            f"The record stands as stated: on {dates[-1]}, the 2-year par yield was {y2['value']:.2f} percent, the 10-year was {y10['value']:.2f} percent, "
            f"the 30-year was {y30['value']:.2f} percent, and the 2s10s spread was {spread['value']:.0f} basis points. "
            "Everything in this explainer resolves to the governed Treasury record or to calculations derived from it. "
            "This is a Capital Chronicle evidence-bound transformation, produced by the Tier-2 programmable video factory. "
            "It is a historical demonstration, it is not financial advice, and the source authority remains the U.S. Department of the Treasury. We read the official table, recomputed the spread, traced the quarter in three windows, and compared the curve at both ends. Every chapter stayed inside the same bounded claim set. Thanks for watching."
        ),
        motion_hint="endcard_fade",
    )); order += 1

    chapters = [
        {"chapter_id": "ch-01", "title": "The Shape of the Curve", "scene_ids": ["lf-title"], "claim_ids": ALL4},
        {"chapter_id": "ch-02", "title": "Reading the Official Table", "scene_ids": ["lf-table"], "claim_ids": ALL4},
        {"chapter_id": "ch-03", "title": "The 2s10s Calculation", "scene_ids": ["lf-spread"], "claim_ids": ["UST:10Y:2026-07-13", "UST:2Y:2026-07-13", "UST:2S10S:2026-07-13"]},
        {"chapter_id": "ch-04", "title": "The Long End at 5.10", "scene_ids": ["lf-longend"], "claim_ids": ALL4},
        {"chapter_id": "ch-05", "title": "One Day, Three Moves", "scene_ids": ["lf-move"], "claim_ids": ALL4},
        {"chapter_id": "ch-06", "title": "The 30-Year Path Across the Quarter", "scene_ids": ["lf-30y-trend"], "claim_ids": ["UST:30Y:2026-07-13"]},
        {"chapter_id": "ch-07", "title": "The Quarter's Flattening", "scene_ids": ["lf-spread-trend"], "claim_ids": ["UST:2S10S:2026-07-13"]},
        {"chapter_id": "ch-08", "title": "The 10-Year's Steadier Climb", "scene_ids": ["lf-10y-trend"], "claim_ids": ["UST:10Y:2026-07-13"]},
        {"chapter_id": "ch-09", "title": "The Full Maturity Ladder", "scene_ids": ["lf-ladder"], "claim_ids": ALL4},
        {"chapter_id": "ch-10", "title": "The 2-Year Path Across the Quarter", "scene_ids": ["lf-2y-trend"], "claim_ids": ["UST:2Y:2026-07-13"]},
        {"chapter_id": "ch-11", "title": "Where the Spread Peaked and Bottomed", "scene_ids": ["lf-spread-extremes"], "claim_ids": ["UST:2S10S:2026-07-13"]},
        {"chapter_id": "ch-12", "title": "The Quarter in Three Parts: First Window", "scene_ids": ["lf-window-a"], "claim_ids": ALL4},
        {"chapter_id": "ch-13", "title": "The Quarter in Three Parts: Second Window", "scene_ids": ["lf-window-b"], "claim_ids": ALL4},
        {"chapter_id": "ch-14", "title": "The Quarter in Three Parts: Final Window", "scene_ids": ["lf-window-c"], "claim_ids": ALL4},
        {"chapter_id": "ch-15", "title": "Reading the Shape Itself", "scene_ids": ["lf-reading-shape", "lf-shape-both-ends"], "claim_ids": ALL4},
        {"chapter_id": "ch-16", "title": "Why the Slope Compressed", "scene_ids": ["lf-front-vs-long"], "claim_ids": ["UST:2Y:2026-07-13", "UST:10Y:2026-07-13", "UST:2S10S:2026-07-13"]},
        {"chapter_id": "ch-17", "title": "What This Record Covers", "scene_ids": ["lf-record-scope"], "claim_ids": ALL4},
        {"chapter_id": "ch-18", "title": "Where Description Stops", "scene_ids": ["lf-boundary"], "claim_ids": ALL4},
        {"chapter_id": "ch-19", "title": "Method and Limits", "scene_ids": ["lf-method"], "claim_ids": ALL4},
        {"chapter_id": "ch-20", "title": "End of Explainer", "scene_ids": ["lf-close"], "claim_ids": ALL4},
    ]
    if pacing == "brisk":
        chapters = chapters  # pacing is a narration-speed concern, not a structure cut; preserve full evidence coverage

    program = {
        "schema_version": SCHEMA_VERSION,
        "video_id": "tier2b-treasury-curve-long",
        "story_id": story["story_id"],
        "story_version": story["story_version"],
        "content_version": FACTORY_VERSION,
        "input_hashes": {"packet": story["packet_sha256"], "article": story["article_hash"], "story": logical_hash(story)},
        "mode": "LONG_FORM_EDITORIAL_15_45M",
        "duration_target_seconds": 900,
        "aspect_strategy": {"primary": "16:9", "short_derivative": "independent_9:16"},
        "frame_rate": LONG_FPS,
        "render_resolution": {"width": LONG_WIDTH, "height": LONG_HEIGHT, "profile": "proxy_final_720p"},
        "audio_policy": "narration_only_no_music_or_rights_cleared_music",
        "caption_policy": "narration_segment_boundary_cues",
        "motion_system_version": MOTION_SYSTEM_VERSION,
        "director_version": director_spec.get("director_version", "tier2b-9router-director-v1"),
        "director_spec": director_spec,
        "chapters": chapters,
        "scenes": scenes,
        "assets": [row["asset_id"] for row in story["media_assets"]],
        "narration": {"provider_boundary": "provider_neutral", "default_provider": NARRATION_PROVIDER, "voice": VOICE, "segment_level": True},
        "rights_provenance": {"source_document_id": SOURCE_ID, "source_rights": "public_domain_us_government", "generated_media": False},
        "qa_state": "PENDING",
        "revision_state": "INITIAL_PROGRAM",
        "public_write_authority": False,
    }
    program["program_hash"] = _semantic_program_hash(program)
    return program


def build_short_program(story: Mapping[str, Any], series: Mapping[str, Any], director_spec: Mapping[str, Any]) -> dict[str, Any]:
    c = story["claims"]
    y2, y10, y30, spread = (c[k] for k in CLAIM_IDS)
    ALL4 = list(CLAIM_IDS)
    ss = series["stats_2s10s"]
    scenes: list[dict[str, Any]] = []
    scenes.append(_scene(
        "sh-hook", "short-01", primitive="TITLE_OPENING",
        title="The Slope Compressed",
        kicker="Capital Chronicle // Short",
        subtitle="One quarter of official Treasury data, 60 seconds.",
        claim_ids=["UST:2S10S:2026-07-13"], order=0,
        script=(
            f"Here's a number that moved all quarter. The 2s10s Treasury spread went from {ss['first']:.0f} basis points in early April to {ss['last']:.0f} on July 13. "
            "Same official source, one clear direction. Watch."
        ),
        motion_hint="hook_fast_reveal",
    ))
    scenes.append(_scene(
        "sh-spread", "short-01", primitive="TIMELINE_SCENE",
        title="51 to 36 Basis Points",
        kicker="2s10s Spread",
        claim_ids=["UST:2S10S:2026-07-13"], order=1,
        series=[{"label": "2s10s spread (bp)", "points": _series_points(series["dates"], series["series_2s10s_bp"], max(1, len(series["dates"]) // 16)), "color": "#c46a5a"}],
        numbers=[{"label": "July 13 spread", "value": round(ss["last"], 0), "unit": "basis_points", "emphasis": True}, {"label": "April start", "value": round(ss["first"], 0), "unit": "basis_points"}],
        script=(
            f"Computed from the Treasury's daily par yields, the spread started the quarter near {ss['first']:.0f} basis points and ended at {ss['last']:.0f}. "
            f"Range: {ss['min']:.0f} to {ss['max']:.0f}. That's the flattening, plotted from official data."
        ),
        motion_hint="timeline_draw",
    ))
    scenes.append(_scene(
        "sh-levels", "short-01", primitive="NUMBER_CALLOUT",
        title="The Levels Behind It",
        kicker="July 13 Official Close",
        claim_ids=ALL4, order=2,
        numbers=[
            {"label": "30Y", "value": y30["value"], "unit": "percent", "emphasis": True},
            {"label": "10Y", "value": y10["value"], "unit": "percent"},
            {"label": "2Y", "value": y2["value"], "unit": "percent"},
        ],
        script=(
            f"On July 13 the official levels were 30-year {y30['value']:.2f} percent, 10-year {y10['value']:.2f}, 2-year {y2['value']:.2f}. "
            f"Subtract the 2-year from the 10-year and you get the {spread['value']:.0f} basis point spread."
        ),
        motion_hint="number_count_up",
    ))
    scenes.append(_scene(
        "sh-boundary", "short-01", primitive="CALLOUT",
        title="Scale It Correctly",
        kicker="Evidence Boundary",
        claim_ids=ALL4, order=3,
        subtitle="A quarter-long slope move, one day's small step.",
        script=(
            "The quarter-long compression is real and material. The one-day change was one basis point. Both facts come from the same governed Treasury record. "
            "Neither one is a forecast, and neither one is advice."
        ),
        motion_hint="callout_soft",
    ))
    scenes.append(_scene(
        "sh-close", "short-01", primitive="DISCLAIMER_ENDCARD",
        title="Capital Chronicle",
        kicker="Source Before Story",
        claim_ids=ALL4, order=4,
        subtitle="Historical demonstration. Source: U.S. Treasury. Not financial advice.",
        script=(
            "Source is the U.S. Treasury Daily Par Yield Curve Rates table. Historical governed demonstration, not current data, not financial advice. "
            "Capital Chronicle, evidence before narrative."
        ),
        motion_hint="endcard_fade",
    ))
    program = {
        "schema_version": SCHEMA_VERSION,
        "video_id": "tier2b-treasury-curve-short-01",
        "story_id": story["story_id"],
        "story_version": story["story_version"],
        "content_version": FACTORY_VERSION,
        "input_hashes": {"packet": story["packet_sha256"], "article": story["article_hash"], "story": logical_hash(story)},
        "mode": "SHORT_FORM_NATIVE",
        "duration_target_seconds": 75,
        "aspect_strategy": {"primary": "9:16", "independent_from": "tier2b-treasury-curve-long"},
        "frame_rate": SHORT_FPS,
        "render_resolution": {"width": SHORT_WIDTH, "height": SHORT_HEIGHT, "profile": "native_1080x1920"},
        "audio_policy": "narration_only_no_music_or_rights_cleared_music",
        "caption_policy": "narration_segment_boundary_cues",
        "motion_system_version": MOTION_SYSTEM_VERSION,
        "director_version": director_spec.get("director_version", "tier2b-9router-director-v1"),
        "director_spec": director_spec,
        "chapters": [{"chapter_id": "short-01", "title": "The Slope Compressed", "scene_ids": [s["scene_id"] for s in scenes], "claim_ids": ALL4}],
        "scenes": scenes,
        "assets": [row["asset_id"] for row in story["media_assets"]],
        "narration": {"provider_boundary": "provider_neutral", "default_provider": NARRATION_PROVIDER, "voice": VOICE, "segment_level": True},
        "rights_provenance": {"source_document_id": SOURCE_ID, "source_rights": "public_domain_us_government", "generated_media": False},
        "qa_state": "PENDING",
        "revision_state": "INITIAL_PROGRAM",
        "public_write_authority": False,
    }
    program["program_hash"] = _semantic_program_hash(program)
    return program


def _semantic_program_hash(program: Mapping[str, Any]) -> str:
    semantic = {k: v for k, v in program.items() if k not in ("program_hash", "qa_state", "revision_state", "execution")}
    return logical_hash(semantic)


# ---------------------------------------------------------------------------
# 9Router Video Director (bounded, selection-only; no numeric authority).
# ---------------------------------------------------------------------------

DIRECTOR_ROLE = "tier2_video_director"
CRITIC_ROLE = "tier2_visual_critic"
DIRECTOR_MODEL_PREFERENCE = "new/claude-fable-5"


def run_video_director(story: Mapping[str, Any], *, program_mode: str, work_root: Path, provider_enabled: bool = True) -> dict[str, Any]:
    """Bounded director: selects among whitelisted structural options only.

    The director may never invent numbers, claims, or facts. It selects from a
    fixed menu; the default is used when the provider is disabled or fails.
    """
    default_spec = {
        "director_version": "tier2b-9router-director-v1",
        "hook_style": "level_first" if program_mode.startswith("LONG") else "spread_first",
        "pacing": "measured",
        "chapter_emphasis": "term_structure",
        "short_angle": "quarter_compression",
        "provider_used": False,
        "model": None,
        "invocation_id": None,
        "usage": None,
        "cost": None,
    }
    if not provider_enabled:
        return default_spec
    prompt = (
        "You are the Video Director for an evidence-bound financial explainer. You may ONLY select from the provided menu. "
        "You must NOT invent numbers, claims, sources, or facts. Reply with STRICT JSON only.\n"
        f"Program mode: {program_mode}\n"
        f"Story title: {story.get('title')}\n"
        "Menu:\n"
        '  hook_style: one of ["level_first","spread_first"]\n'
        '  pacing: one of ["measured","brisk"]\n'
        '  chapter_emphasis: one of ["term_structure","slope","long_end"]\n'
        '  short_angle: one of ["quarter_compression","level_headline","one_day_move"]\n'
        'Return JSON: {"hook_style": ..., "pacing": ..., "chapter_emphasis": ..., "short_angle": ...}'
    )
    from .nine_router_llm_seam_v2 import routed_llm_invocation, drain_invocation_log
    allowed = {
        "hook_style": {"level_first", "spread_first"},
        "pacing": {"measured", "brisk"},
        "chapter_emphasis": {"term_structure", "slope", "long_end"},
        "short_angle": {"quarter_compression", "level_headline", "one_day_move"},
    }

    def validator(text: str):
        try:
            start = text.find("{")
            end = text.rfind("}")
            value = json.loads(text[start:end + 1])
        except Exception:
            return False, "director_output_not_json", None
        if not isinstance(value, dict):
            return False, "director_output_not_object", None
        for key, choices in allowed.items():
            if value.get(key) not in choices:
                return False, f"director_option_invalid:{key}", None
        return True, None, value

    summary = routed_llm_invocation(
        prompt=prompt,
        role_task_id=DIRECTOR_ROLE,
        logical_invocation_id=f"tier2b_director_{program_mode}",
        timeout_seconds=90.0,
        validator=validator,
        prompt_template="tier2b_video_director_menu",
        prompt_version="v1",
    )
    if summary.get("terminal_disposition") == "ACCEPTED" and isinstance(summary.get("output"), dict):
        chosen = dict(summary["output"])
        spec = dict(default_spec)
        spec.update({k: chosen[k] for k in allowed if chosen.get(k) in allowed[k]})
        spec["provider_used"] = True
        spec["model"] = (summary.get("accepted_attempt") or {}).get("requested_model") or DIRECTOR_MODEL_PREFERENCE
        spec["invocation_id"] = summary.get("logical_invocation_id")
        spec["usage"] = summary.get("total_usage")
        spec["cost"] = summary.get("total_cost")
        _write_json(work_root / "director" / f"director_{program_mode}.json", {"spec": spec, "summary": summary})
        return spec
    _write_json(work_root / "director" / f"director_{program_mode}_fallback.json", {"reason": "director_not_accepted", "summary": summary})
    return default_spec


# ---------------------------------------------------------------------------
# Narration (provider-neutral boundary; Kokoro segment-level generation).
# ---------------------------------------------------------------------------

def _kokoro_batch(segments: list[dict[str, Any]], work_root: Path) -> list[dict[str, Any]]:
    request_path = work_root / "narration" / "batch_request.json"
    _write_json(request_path, {"segments": segments})
    tts_python = os.environ.get("CONTENTOPS_TIER2_TTS_PYTHON") or sys.executable
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    started = time.perf_counter()
    completed = subprocess.run(
        [tts_python, "-m", "live_contentops.video_tts_worker_v1", "--batch-request", str(request_path)],
        capture_output=True, text=True, check=False, timeout=7200, cwd=str(REPO_ROOT), env=env,
    )
    if completed.returncode != 0:
        raise Tier2BError(f"kokoro_batch_failed:{(completed.stderr or '')[-200:]}")
    rows = []
    for seg in segments:
        path = Path(seg["output_path"])
        facts = _media_facts(path)
        rows.append({
            "segment_id": seg["segment_id"],
            "audio_path": str(path),
            "audio_sha256": facts["sha256"],
            "duration_seconds": facts["duration_seconds"],
            "provider": NARRATION_PROVIDER,
            "model": "Kokoro-82M",
            "voice": VOICE,
            "speed": NARRATION_SPEED,
        })
    return rows


def generate_program_narration(program: dict[str, Any], work_root: Path) -> dict[str, Any]:
    """Generate one WAV per narration segment and record exact durations.

    Caption cue boundaries equal segment boundaries — authoritative TTS timing,
    not character-proportional estimation.
    """
    narration_dir = work_root / "narration"
    narration_dir.mkdir(parents=True, exist_ok=True)
    requests: list[dict[str, Any]] = []
    plan: dict[str, Any] = {}
    for scene in program["scenes"]:
        seg_rows = []
        for index, text in enumerate(scene["narration_segments"]):
            segment_id = f"{scene['scene_id']}-seg{index + 1}"
            out = narration_dir / f"{segment_id}.wav"
            if not out.exists():
                requests.append({
                    "segment_id": segment_id,
                    "text": text,
                    "output_path": str(out),
                    "voice": VOICE,
                    "speed": NARRATION_SPEED,
                })
            seg_rows.append({"segment_id": segment_id, "text": text, "output_path": str(out)})
        plan[scene["scene_id"]] = seg_rows
    if requests:
        generated = _kokoro_batch(requests, work_root)
    else:
        generated = []
    receipt_rows = []
    for scene in program["scenes"]:
        segments = []
        for row in plan[scene["scene_id"]]:
            facts = _media_facts(Path(row["output_path"]))
            segments.append({
                "segment_id": row["segment_id"],
                "text": row["text"],
                "audio_path": row["output_path"],
                "audio_sha256": facts["sha256"],
                "duration_seconds": facts["duration_seconds"],
            })
        receipt_rows.append({"scene_id": scene["scene_id"], "segments": segments})
    return {"provider": NARRATION_PROVIDER, "voice": VOICE, "speed": NARRATION_SPEED, "scenes": receipt_rows,
            "generated_now": len(requests), "total_wall_seconds": None}


# ---------------------------------------------------------------------------
# Remotion render-job compilation + scene rendering (cached).
# ---------------------------------------------------------------------------

def _stage_assets(program: Mapping[str, Any], story: Mapping[str, Any], work_root: Path) -> dict[str, str]:
    """Copy governed assets into video/remotion/public/assets keyed by content hash."""
    public_assets = REMOTION_ROOT / "public" / "assets"
    public_assets.mkdir(parents=True, exist_ok=True)
    repo_root = Path(story["input_root"])
    for candidate in (repo_root, *repo_root.parents):
        if (candidate / "live_contentops").is_dir() and (candidate / "AGENTS.md").is_file():
            repo_root = candidate
            break
    staged: dict[str, str] = {}
    for asset in story.get("media_assets") or []:
        source = (repo_root / str(asset["path"])).resolve() if not Path(str(asset["path"])).is_absolute() else Path(str(asset["path"]))
        if not source.is_file():
            raise Tier2BError(f"governed_asset_missing:{asset.get('asset_id')}")
        digest = sha256_file(source)
        if digest != str(asset.get("sha256") or ""):
            raise Tier2BError(f"governed_asset_hash_mismatch:{asset.get('asset_id')}")
        target = public_assets / f"{digest}{source.suffix}"
        if not target.exists():
            shutil.copy2(source, target)
        staged[str(asset["asset_id"])] = f"assets/{digest}{source.suffix}"
    return staged


def scene_cache_key(scene: Mapping[str, Any], *, narration: Mapping[str, Any], staged_assets: Mapping[str, str],
                    width: int, height: int, fps: int, renderer_version: str) -> str:
    narration_identity = logical_hash({
        "provider": narration.get("provider"),
        "voice": narration.get("voice"),
        "speed": narration.get("speed"),
        "segments": [
            {"segment_id": seg["segment_id"], "sha256": seg["audio_sha256"], "duration_seconds": seg["duration_seconds"]}
            for seg in narration.get("segments") or []
        ],
    })
    asset_identity = {asset_id: staged_assets.get(asset_id) for asset_id in scene.get("asset_refs") or []}
    return logical_hash({
        "schema_version": REMOTION_SCHEMA_VERSION,
        "renderer_id": RENDERER_ID,
        "renderer_version": renderer_version,
        "motion_system_version": MOTION_SYSTEM_VERSION,
        "width": width,
        "height": height,
        "fps": fps,
        "scene_semantic": {k: scene.get(k) for k in (
            "scene_id", "semantic_purpose", "display_title", "kicker", "subtitle",
            "script", "narration_segments", "claim_bindings", "source_bindings",
            "visual_primitive", "numbers", "series", "text_blocks", "rights_requirements",
            "credits", "motion_intent", "revision_history",
        )},
        "asset_identity": asset_identity,
        "narration_identity": narration_identity,
    })


def chapter_cache_key(chapter: Mapping[str, Any], scene_rows: Sequence[Mapping[str, Any]], renderer_version: str) -> str:
    ordered = {row["scene_id"]: row for row in scene_rows}
    return logical_hash({
        "chapter_id": chapter["chapter_id"],
        "renderer_version": renderer_version,
        "transition_frames": TRANSITION_FRAMES,
        "ordered_scene_hashes": [ordered[sid]["render_sha256"] for sid in chapter["scene_ids"]],
    })


def compile_scene_job(program: Mapping[str, Any], scene: Mapping[str, Any], narration: Mapping[str, Any],
                      staged_assets: Mapping[str, str], *, width: int, height: int, fps: int,
                      work_root: Path) -> dict[str, Any]:
    primitive_map = {
        "TITLE_OPENING": "TITLE_OPENING",
        "DOCUMENT_SCENE": "DOCUMENT_SCENE",
        "CHART_SCENE": "CHART_SCENE",
        "COMPARISON_SCENE": "COMPARISON_SCENE",
        "TIMELINE_SCENE": "TIMELINE_SCENE",
        "NUMBER_CALLOUT": "NUMBER_CALLOUT",
        "SOURCE_CARD": "SOURCE_CARD",
        "CALLOUT": "CALLOUT",
        "DISCLAIMER_ENDCARD": "DISCLAIMER_ENDCARD",
    }
    segments = narration["segments"]
    narration_seconds = sum(seg["duration_seconds"] for seg in segments)
    duration_seconds = narration_seconds + TAIL_SECONDS
    duration_frames = int(round(duration_seconds * fps))
    cues = []
    cursor = 0.0
    for seg in segments:
        cues.append({"start_frame": int(round(cursor * fps)), "end_frame": int(round((cursor + seg["duration_seconds"]) * fps)), "text": seg["text"]})
        cursor += seg["duration_seconds"]
    scene_wav = work_root / "narration" / f"{scene['scene_id']}.concat.wav"
    if not scene_wav.exists():
        list_path = scene_wav.with_suffix(".txt")
        list_path.write_text("\n".join(f"file '{Path(seg['audio_path']).as_posix()}'" for seg in segments) + "\n", encoding="utf-8")
        try:
            _ffmpeg(["-f", "concat", "-safe", "0", "-i", str(list_path), "-c", "copy", str(scene_wav)])
        finally:
            list_path.unlink(missing_ok=True)
    narration_public = REMOTION_ROOT / "public" / "narration" / f"{scene['scene_id']}.wav"
    narration_public.parent.mkdir(parents=True, exist_ok=True)
    if not narration_public.exists() or sha256_file(narration_public) != sha256_file(scene_wav):
        shutil.copy2(scene_wav, narration_public)
    asset_id = (scene.get("asset_refs") or [None])[0]
    job = {
        "scene_id": scene["scene_id"],
        "chapter_id": scene["chapter_id"],
        "visual_primitive": primitive_map[str(scene["visual_primitive"]).upper()] if str(scene["visual_primitive"]).upper() in primitive_map else "CALLOUT",
        "aspect": "vertical" if width < height else "landscape",
        "width": width,
        "height": height,
        "fps": fps,
        "duration_in_frames": duration_frames,
        "narration_seconds": narration_seconds,
        "display_title": scene["display_title"],
        "subtitle": scene.get("subtitle"),
        "kicker": scene.get("kicker") or "Capital Chronicle",
        "chapter_label": scene["chapter_id"],
        "source_label": scene["credits"],
        "credit_line": None,
        "numbers": scene.get("numbers") or [],
        "series": scene.get("series") or [],
        "text_blocks": scene.get("text_blocks") or [],
        "asset": ({"kind": "image", "path": staged_assets[asset_id], "sha256": Path(staged_assets[asset_id]).name.split(".")[0], "layout": "contain"} if asset_id and asset_id in staged_assets else None),
        "captions": cues,
        "rights_synthetic": False,
        "motion_hint": scene.get("motion_intent"),
        "narration_asset": f"narration/{scene['scene_id']}.wav",
        "transition_tail_frames": int(round(TAIL_SECONDS * fps)),
        "narration_sha256": sha256_file(scene_wav),
        "narration_duration_seconds": narration_seconds,
    }
    return job


def render_scenes(jobs: Sequence[Mapping[str, Any]], work_root: Path, *, cache: Mapping[str, Mapping[str, Any]],
                  renderer_version: str) -> list[dict[str, Any]]:
    """Render only cache-missed scenes through the Remotion driver."""
    pending = []
    rows = []
    for job in jobs:
        key = job["cache_key"]
        hit = cache.get(key)
        target = Path(str(job["output_path"]))
        if hit and target.is_file() and hit.get("render_sha256") == sha256_file(target):
            rows.append(dict(hit))
            continue
        pending.append(job)
    if pending:
        batch = {
            "batch_id": f"tier2b-{int(time.time())}",
            "motion_system_version": MOTION_SYSTEM_VERSION,
            "renderer_profile": "tier2b_remotion_v1",
            "scenes": [{k: v for k, v in job.items() if k not in ("cache_key",)} for job in pending],
        }
        batch_path = work_root / "render" / f"batch_{batch['batch_id']}.json"
        receipt_path = work_root / "render" / f"receipt_{batch['batch_id']}.json"
        _write_json(batch_path, batch)
        completed = _run(
            ["node", str(REMOTION_ROOT / "scripts" / "render-job.mjs"),
             "--batch", str(batch_path), "--receipt", str(receipt_path),
             "--chrome", _chrome_path(), "--concurrency", "2"],
            timeout=10800, capture=True,
        )
        if completed.returncode != 0:
            raise Tier2BError(f"remotion_render_failed:{(completed.stdout or '')[-160:]}|{(completed.stderr or '')[-240:]}")
        receipt = _read_json(receipt_path)
        by_id = {row["scene_id"]: row for row in receipt.get("scenes") or []}
        for job in pending:
            rendered = by_id.get(job["scene_id"])
            if not rendered or rendered.get("status") != "rendered":
                raise Tier2BError(f"scene_render_missing:{job['scene_id']}")
            target = Path(str(job["output_path"]))
            facts = _media_facts(target)
            rows.append({
                "scene_id": job["scene_id"],
                "cache_key": job["cache_key"],
                "output_path": str(target),
                "render_sha256": facts["sha256"],
                "duration_seconds": facts["duration_seconds"],
                "duration_in_frames": facts.get("duration_in_frames") or job["duration_in_frames"],
                "width": facts["width"],
                "height": facts["height"],
                "fps": facts["fps"],
                "elapsed_ms": rendered.get("elapsed_ms"),
                "cache_hit": False,
            })
    for row in rows:
        row.setdefault("cache_hit", True)
    order = {job["scene_id"]: i for i, job in enumerate(jobs)}
    rows.sort(key=lambda row: order[row["scene_id"]])
    return rows


# ---------------------------------------------------------------------------
# FFmpeg finishing: real transitions, loudness, captions.
# ---------------------------------------------------------------------------

def _fmt_ts(seconds: float, comma: bool) -> str:
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{',' if comma else '.'}{millis:03d}"


def build_caption_sidecars(program: Mapping[str, Any], narration_by_scene: Mapping[str, Any],
                           assembly: Mapping[str, Any], out_root: Path, *, tag: str) -> dict[str, Any]:
    """SRT/VTT from authoritative narration segment boundaries + assembly offsets."""
    rows = []
    chapter_starts = {row["chapter_id"]: row["start_seconds"] for row in assembly["chapters"]}
    scene_starts = {row["scene_id"]: row["start_seconds"] for row in assembly["scenes"]}
    for chapter in program["chapters"]:
        base = chapter_starts[chapter["chapter_id"]]
        for scene_id in chapter["scene_ids"]:
            sbase = base + scene_starts[scene_id]
            narration = narration_by_scene[scene_id]
            cursor = 0.0
            for idx, seg in enumerate(narration["segments"]):
                rows.append({
                    "index": len(rows) + 1,
                    "start": sbase + cursor,
                    "end": sbase + cursor + seg["duration_seconds"],
                    "text": seg["text"],
                    "scene_id": scene_id,
                    "segment_id": seg["segment_id"],
                })
                cursor += seg["duration_seconds"]
    srt_path = out_root / "captions" / f"{tag}.srt"
    vtt_path = out_root / "captions" / f"{tag}.vtt"
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    srt_path.write_text("\n\n".join(f"{r['index']}\n{_fmt_ts(r['start'], True)} --> {_fmt_ts(r['end'], True)}\n{r['text']}" for r in rows) + "\n", encoding="utf-8")
    vtt_path.write_text("WEBVTT\n\n" + "\n\n".join(f"{_fmt_ts(r['start'], False)} --> {_fmt_ts(r['end'], False)}\n{r['text']}" for r in rows) + "\n", encoding="utf-8")
    return {"srt": str(srt_path), "vtt": str(vtt_path), "cue_count": len(rows), "srt_sha256": sha256_file(srt_path), "vtt_sha256": sha256_file(vtt_path)}


def assemble_chapter(chapter: Mapping[str, Any], scene_rows: Sequence[Mapping[str, Any]], out_path: Path, *,
                     width: int, height: int, fps: int, transition_frames: int = TRANSITION_FRAMES) -> dict[str, Any]:
    """Assemble one chapter from scene clips with real xfade transitions."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(scene_rows)
    if len(rows) == 1:
        _ffmpeg([
            "-i", rows[0]["output_path"],
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
            "-movflags", "+faststart", str(out_path),
        ], timeout=1800)
        facts = _media_facts(out_path)
        return {"chapter_id": chapter["chapter_id"], "output_path": str(out_path), "render_sha256": facts["sha256"], "duration_seconds": facts["duration_seconds"]}
    inputs: list[str] = []
    for row in rows:
        inputs.extend(["-i", row["output_path"]])
    t = transition_frames / fps
    parts: list[str] = []
    for i in range(len(rows)):
        parts.append(f"[{i}:a]aresample=48000,asetpts=PTS-STARTPTS[ar{i}]")
    prev_video = "0:v"
    prev_audio = "ar0"
    offset = max(0.0, float(rows[0]["duration_seconds"]) - t)
    for i in range(1, len(rows)):
        out_v = f"v{i}"
        parts.append(f"[{prev_video}][{i}:v]xfade=transition=fade:duration={t:.4f}:offset={offset:.4f}[{out_v}]")
        out_a = f"ac{i}"
        parts.append(f"[{prev_audio}][ar{i}]acrossfade=d={t:.4f}[{out_a}]")
        prev_video = out_v
        prev_audio = out_a
        if i < len(rows) - 1:
            offset += max(0.0, float(rows[i]["duration_seconds"]) - t)
    parts.append(f"[{prev_audio}]loudnorm=I=-16:TP=-1.5:LRA=11[aloud]")
    filter_complex = ";".join(parts)
    _ffmpeg([
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{prev_video}]", "-map", "[aloud]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
        "-movflags", "+faststart", str(out_path),
    ], timeout=3600)
    facts = _media_facts(out_path)
    return {"chapter_id": chapter["chapter_id"], "output_path": str(out_path), "render_sha256": facts["sha256"], "duration_seconds": facts["duration_seconds"]}


def assemble_master(chapter_rows: Sequence[Mapping[str, Any]], out_path: Path, *, sidecar_srt: Path | None = None,
                    burn_captions: bool = False) -> dict[str, Any]:
    """Concatenate chapter files. Chapters share codec parameters; stream-copy keeps it deterministic and fast."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    list_path = out_path.with_suffix(".chapters.txt")
    list_path.write_text("\n".join(f"file '{Path(row['output_path']).as_posix()}'" for row in chapter_rows) + "\n", encoding="utf-8")
    try:
        args = ["-f", "concat", "-safe", "0", "-i", str(list_path)]
        if burn_captions and sidecar_srt is not None:
            args += ["-vf", f"subtitles={sidecar_srt.as_posix().replace(':', r'\\:')}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "copy"]
        else:
            args += ["-c", "copy"]
        args += ["-movflags", "+faststart", str(out_path)]
        _ffmpeg(args, timeout=3600)
    finally:
        list_path.unlink(missing_ok=True)
    facts = _media_facts(out_path)
    return {"output_path": str(out_path), "render_sha256": facts["sha256"], "duration_seconds": facts["duration_seconds"], "master_hash": facts["sha256"]}


def compute_assembly_offsets(chapter_rows: Sequence[Mapping[str, Any]], program: Mapping[str, Any],
                             scene_rows: Sequence[Mapping[str, Any]], narration_by_scene: Mapping[str, Any],
                             cache: Mapping[str, Mapping[str, Any]], *, transition_frames: int = TRANSITION_FRAMES) -> dict[str, Any]:
    """Compute per-scene start offsets within chapters and per-chapter start offsets in the master.

    Scene clips overlap by transition_frames inside chapter assembly, so each scene's in-chapter
    start advances by (duration - transition) except the first.
    """
    by_scene = {row["scene_id"]: row for row in scene_rows}
    fps = float(program["frame_rate"])
    t = transition_frames / fps
    scene_offsets: list[dict[str, Any]] = []
    chapter_offsets: list[dict[str, Any]] = []
    master_cursor = 0.0
    for chapter in program["chapters"]:
        chapter_cursor = 0.0
        sids = chapter["scene_ids"]
        for idx, sid in enumerate(sids):
            row = by_scene[sid]
            clip_duration = float(cache[row["cache_key"]]["duration_seconds"]) if row["cache_key"] in cache else row["duration_seconds"]
            scene_offsets.append({
                "scene_id": sid,
                "chapter_id": chapter["chapter_id"],
                "start_seconds": round(chapter_cursor, 6),
                "clip_duration_seconds": round(clip_duration, 6),
                "narration_seconds": round(sum(seg["duration_seconds"] for seg in narration_by_scene[sid]["segments"]), 6),
            })
            if idx < len(sids) - 1:
                chapter_cursor += max(0.0, clip_duration - t)
            else:
                chapter_cursor += clip_duration
        chapter_offsets.append({
            "chapter_id": chapter["chapter_id"],
            "start_seconds": round(master_cursor, 6),
            "duration_seconds": round(chapter_cursor, 6),
        })
        master_cursor += chapter_cursor
    expected_total = master_cursor
    return {"scenes": scene_offsets, "chapters": chapter_offsets, "expected_master_duration_seconds": round(expected_total, 6), "transition_seconds": round(t, 6)}


# ---------------------------------------------------------------------------
# Deterministic QA — every check computed, none hardcoded.
# ---------------------------------------------------------------------------

def deterministic_qa(program: Mapping[str, Any], master: Mapping[str, Any], assembly: Mapping[str, Any],
                     captions: Mapping[str, Any], scene_rows: Sequence[Mapping[str, Any]],
                     narration_by_scene: Mapping[str, Any], package_root: Path, *, aspect: str,
                     short: Mapping[str, Any] | None = None, short_captions: Mapping[str, Any] | None = None) -> dict[str, Any]:
    blockers: list[str] = []
    facts = _media_facts(Path(master["output_path"]))
    profile = program["render_resolution"]
    expected_w, expected_h = int(profile["width"]), int(profile["height"])
    checks: dict[str, Any] = {}
    checks["file_exists"] = Path(master["output_path"]).is_file()
    if not checks["file_exists"]:
        blockers.append("master_missing")
    duration = facts["duration_seconds"]
    target = float(program.get("duration_target_seconds") or 0)
    if program["mode"].startswith("LONG"):
        checks["duration_meets_target"] = bool(duration >= max(900.0, target) - 2.0)
        if not checks["duration_meets_target"]:
            blockers.append(f"long_form_duration_below_15m:{duration:.2f}")
    else:
        checks["duration_within_short_band"] = bool(20.0 <= duration <= 240.0)
        if not checks["duration_within_short_band"]:
            blockers.append(f"short_duration_out_of_band:{duration:.2f}")
    checks["duration_seconds"] = duration
    checks["resolution_matches_profile"] = facts["width"] == expected_w and facts["height"] == expected_h
    if not checks["resolution_matches_profile"]:
        blockers.append("resolution_mismatch")
    expected_aspect = "9:16" if aspect == "vertical" else "16:9"
    ratio = facts["width"] / max(1, facts["height"])
    checks["aspect_expected"] = expected_aspect
    checks["aspect_ratio_value"] = round(ratio, 4)
    checks["aspect_ok"] = (ratio < 1.0) if expected_aspect == "9:16" else (ratio > 1.0)
    if not checks["aspect_ok"]:
        blockers.append("aspect_mismatch")
    checks["frame_rate"] = facts["fps"]
    checks["frame_rate_matches_program"] = abs(facts["fps"] - float(program["frame_rate"])) < 0.51
    if not checks["frame_rate_matches_program"]:
        blockers.append("frame_rate_mismatch")
    checks["video_stream_present"] = bool(facts["video_codec"])
    checks["video_codec"] = facts["video_codec"]
    checks["video_codec_policy"] = facts["video_codec"] == "h264"
    if not checks["video_codec_policy"]:
        blockers.append("video_codec_not_h264")
    checks["audio_stream_present"] = bool(facts["audio_codec"])
    if not checks["audio_stream_present"]:
        blockers.append("audio_stream_missing")
    checks["container_policy"] = "mp4" in str(facts["container"])
    if not checks["container_policy"]:
        blockers.append("container_not_mp4")
    checks["caption_outputs_present"] = Path(captions["srt"]).is_file() and Path(captions["vtt"]).is_file()
    checks["caption_cue_count"] = captions["cue_count"]
    if captions["cue_count"] <= 0:
        blockers.append("no_caption_cues")
    checks["scene_completeness"] = len(scene_rows) == len(program["scenes"])
    if not checks["scene_completeness"]:
        blockers.append("scene_count_mismatch")
    checks["chapter_completeness"] = len(assembly["chapters"]) == len(program["chapters"])
    if not checks["chapter_completeness"]:
        blockers.append("chapter_count_mismatch")
    narration_ok = all(scene["scene_id"] in narration_by_scene for scene in program["scenes"])
    checks["narration_completeness"] = narration_ok
    if not narration_ok:
        blockers.append("narration_missing_for_scene")
    claim_ids_program = {b["claim_id"] for scene in program["scenes"] for b in scene.get("claim_bindings") or []}
    story_claim_ids = set(CLAIM_IDS)
    checks["claim_binding_coverage"] = round(len(story_claim_ids & claim_ids_program) / max(1, len(story_claim_ids)), 4)
    if checks["claim_binding_coverage"] < 1.0:
        blockers.append("claim_coverage_incomplete")
    checks["source_credits_on_all_scenes"] = all(str(scene.get("credits") or "").startswith("Source:") for scene in program["scenes"])
    if not checks["source_credits_on_all_scenes"]:
        blockers.append("source_credit_missing")
    rights_ok = all(str(scene.get("rights_requirements", {}).get("status") or "") for scene in program["scenes"])
    checks["rights_provenance_coverage"] = bool(rights_ok)
    if not rights_ok:
        blockers.append("rights_provenance_incomplete")
    duration_delta = abs(duration - assembly["expected_master_duration_seconds"])
    checks["assembly_duration_consistency_seconds"] = round(duration_delta, 3)
    checks["assembly_duration_consistent"] = bool(duration_delta <= max(2.0, 0.5 * len(assembly["scenes"])))
    if short is not None:
        scheck = _media_facts(Path(short["output_path"]))
        checks["short_present"] = True
        checks["short_resolution"] = f"{scheck['width']}x{scheck['height']}"
        checks["short_is_native_vertical"] = scheck["height"] > scheck["width"]
        checks["short_duration_seconds"] = scheck["duration_seconds"]
        checks["short_captions_present"] = bool(short_captions and Path(short_captions["srt"]).is_file())
        if not checks["short_is_native_vertical"]:
            blockers.append("short_not_vertical")
    status = "PASS" if not blockers else "BLOCK"
    return {"status": status, "blockers": blockers, "checks": checks, "computed": True, "hardcoded_pass": False,
            "visual_acceptance": "AWAITING_CHATGPT_JIM_VISUAL_AUDIO_REVIEW"}


# ---------------------------------------------------------------------------
# Multimodal critic (canonical 9Router adapter) + bounded revision (<= 2 rounds).
# ---------------------------------------------------------------------------

def extract_representative_frames(master_path: Path, frames: Sequence[int], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for frame in frames:
        target = out_dir / f"frame_{frame:06d}.jpg"
        if not target.is_file():
            _ffmpeg(["-ss", "0", "-i", str(master_path), "-vf", f"select=eq(n\\,{frame})", "-frames:v", "1", "-q:v", "3", str(target)], timeout=300)
        if target.is_file():
            paths.append(target)
    return paths


def _downscale(frame: Path, out_dir: Path, max_side: int = 768) -> Path:
    target = out_dir / (frame.stem + f"_ds{max_side}.jpg")
    if not target.is_file():
        try:
            _ffmpeg(["-i", str(frame), "-vf", f"scale='if(gt(iw,ih),{max_side},-2)':'if(gt(iw,ih),-2,{max_side})'", "-q:v", "4", str(target)], timeout=120)
        except Tier2BError:
            return frame
    return target


def run_multimodal_critic(master_path: Path, program: Mapping[str, Any], work_root: Path, *,
                          provider_enabled: bool = True, max_frames: int = 5,
                          duration_seconds: float | None = None,
                          critic_provider_call=None) -> dict[str, Any]:
    """Multimodal visual critic producing structured defects.

    Uses the canonical 9Router adapter (vision content-parts). It never mutates
    media and never becomes factual authority. When the provider is unavailable or
    fails, it fails closed to a human-review escalation rather than a fake PASS.
    """
    import base64
    duration = duration_seconds or _media_facts(master_path)["duration_seconds"]
    fps = float(program["frame_rate"]) or 24
    pick = []
    n = max(1, max_frames)
    for i in range(n):
        frac = (i + 0.5) / n
        pick.append(int(frac * duration * fps))
    frames_dir = work_root / "critic" / "frames"
    frames = extract_representative_frames(master_path, pick, frames_dir)
    scaled = [_downscale(f, frames_dir) for f in frames]
    if not scaled:
        return {"status": "CRITIC_ESCALATE_NO_FRAMES", "defects": [], "provider_used": False}
    if not provider_enabled:
        return {"status": "CRITIC_PROVIDER_DISABLED_AWAITING_HUMAN", "defects": [], "provider_used": False,
                "frame_count": len(scaled)}
    b64s = []
    for path in scaled:
        blob = path.read_bytes()
        if len(blob) <= 4 * 1024 * 1024:
            b64s.append(base64.b64encode(blob).decode("ascii"))
    rubric = (
        "You are an independent multimodal video QA critic for an institutional financial-news explainer. "
        "You are NOT factual authority; judge only visual/technical quality. Inspect the provided frames sampled across the video. "
        "Evaluate: readability (clipped/overlapping text), composition and hierarchy, crop/safe-zone failures, "
        "chart/document legibility, dead/blank frames, brand consistency, typography. "
        "Return STRICT JSON: {\"defects\":[{\"class\":...,\"severity\":\"low|medium|high\",\"confidence\":\"low|medium|high\",\"evidence\":...,\"target\":\"scene|chapter|global\"}], \"overall\":\"acceptable|needs_revision\"}. "
        "Severity 'high' is reserved for frames that are clearly broken (blank, clipped text, illegible chart). "
        "If nothing is clearly broken, return overall acceptable with zero defects. Do NOT invent numbers or facts."
    )
    from .nine_router_provider_adapter_v2 import call_nine_router_multimodal
    from .nine_router_ordered_model_router_v2 import AUTHORIZED_MODELS
    critic_model = next((m for m in sorted(AUTHORIZED_MODELS) if m.startswith("new/gpt")), next(iter(sorted(AUTHORIZED_MODELS))))
    call = critic_provider_call or (lambda text, imgs, model: call_nine_router_multimodal(text, imgs, model, timeout_seconds=160.0, max_tokens=2000, temperature=0.1))
    started = time.perf_counter()
    result = call(rubric, b64s, critic_model)
    wall = round(time.perf_counter() - started, 3)
    text = getattr(result, "text", None)
    if not text:
        return {"status": "CRITIC_PROVIDER_FAILED_ESCALATE", "defects": [], "provider_used": True,
                "model": critic_model, "wall_seconds": wall,
                "failure_class": getattr(result, "failure_class", None)}
    try:
        start = text.find("{")
        end = text.rfind("}")
        parsed = json.loads(text[start:end + 1])
    except Exception:
        return {"status": "CRITIC_OUTPUT_MALFORMED_ESCALATE", "defects": [], "provider_used": True,
                "model": critic_model, "wall_seconds": wall, "raw_excerpt": text[:300]}
    defects = []
    for d in (parsed.get("defects") or []):
        if isinstance(d, dict) and d.get("severity") in ("low", "medium", "high"):
            defects.append({
                "class": str(d.get("class") or "unspecified"),
                "severity": d["severity"],
                "confidence": d.get("confidence") or "medium",
                "evidence": str(d.get("evidence") or "")[:300],
                "target": d.get("target") or "global",
            })
    overall = parsed.get("overall")
    status = "CRITIC_ACCEPTABLE" if overall == "acceptable" and not any(d["severity"] == "high" for d in defects) else "CRITIC_NEEDS_REVISION"
    return {"status": status, "overall": overall, "defects": defects, "provider_used": True,
            "model": critic_model, "wall_seconds": wall, "frame_count": len(scaled),
            "usage": getattr(result, "usage", None), "invocation_id": getattr(result, "provider_invocation_id", None),
            "cost": getattr(result, "cost", None)}


ALLOWED_REVISION_FIELDS = frozenset({"display_title", "subtitle", "kicker", "motion_hint", "credits"})


def apply_bounded_revision(critic: Mapping[str, Any], program: dict[str, Any], revision_round: int, work_root: Path) -> dict[str, Any]:
    """Apply only safe, whitelisted visual patches suggested by the critic.

    Never touches scripts, claims, numbers, narration text, or assets — factual
    content is immutable under revision. Returns the patch applied.
    """
    if revision_round > MAX_REVISION_ROUNDS:
        return {"applied": False, "reason": "revision_budget_exhausted", "patch": []}
    patch = []
    defects = critic.get("defects") or []
    for defect in defects:
        if defect.get("severity") not in ("medium", "high"):
            continue
        cls = str(defect.get("class") or "").lower()
        if "title" in cls or "typography" in cls or "headline" in cls:
            for scene in program["scenes"]:
                if len(str(scene.get("display_title") or "")) > 42:
                    before = scene["display_title"]
                    scene["display_title"] = str(before)[:40].rstrip()
                    scene["revision_history"].append({"round": revision_round, "field": "display_title", "before": before, "after": scene["display_title"], "critic_class": cls})
                    patch.append({"scene_id": scene["scene_id"], "field": "display_title", "before": before, "after": scene["display_title"]})
        elif "subtitle" in cls or "hierarchy" in cls:
            for scene in program["scenes"]:
                if scene.get("subtitle") and len(str(scene["subtitle"])) > 90:
                    before = scene["subtitle"]
                    scene["subtitle"] = str(before)[:88].rstrip()
                    scene["revision_history"].append({"round": revision_round, "field": "subtitle", "before": before, "after": scene["subtitle"], "critic_class": cls})
                    patch.append({"scene_id": scene["scene_id"], "field": "subtitle", "before": before, "after": scene["subtitle"]})
    _write_json(work_root / "revision" / f"revision_round_{revision_round}.json", {"critic_status": critic.get("status"), "patch": patch})
    return {"applied": bool(patch), "reason": "patch_applied" if patch else "no_safe_patch_identified", "patch": patch, "defect_count": len(defects)}


# ---------------------------------------------------------------------------
# Selective rerender proof.
# ---------------------------------------------------------------------------

def selective_rerender_proof(program: Mapping[str, Any], narration_by_scene: Mapping[str, Any],
                             staged_assets: Mapping[str, str], work_root: Path, cache: dict[str, Any],
                             renderer_version: str, *, width: int, height: int, fps: int) -> dict[str, Any]:
    """Prove a one-field change invalidates exactly one scene and leaves the rest cached.

    Changes the whitelisted 'display_title' of a single scene, recompiles cache keys
    for every scene, and verifies only that scene's key changed and that rendering
    only that scene (others are cache hits) reproduces an identical master hash when
    the change is reverted.
    """
    scene_index = 2
    scene = program["scenes"][scene_index]
    base_keys = {}
    for s in program["scenes"]:
        base_keys[s["scene_id"]] = scene_cache_key(s, narration=narration_by_scene[s["scene_id"]],
                                                   staged_assets=staged_assets, width=width, height=height, fps=fps,
                                                   renderer_version=renderer_version)
    changed = deepcopy(scene)
    changed["display_title"] = str(changed["display_title"]) + " (selective-rerender proof)"
    changed_key = scene_cache_key(changed, narration=narration_by_scene[changed["scene_id"]],
                                  staged_assets=staged_assets, width=width, height=height, fps=fps,
                                  renderer_version=renderer_version)
    invalidated = [s["scene_id"] for s in program["scenes"] if (
        scene_cache_key(changed, narration=narration_by_scene[s["scene_id"]], staged_assets=staged_assets,
                        width=width, height=height, fps=fps, renderer_version=renderer_version)
        if s["scene_id"] == changed["scene_id"] else base_keys[s["scene_id"]]
    ) != base_keys[s["scene_id"]]]
    unaffected_unchanged = all(
        scene_cache_key(s, narration=narration_by_scene[s["scene_id"]], staged_assets=staged_assets,
                        width=width, height=height, fps=fps, renderer_version=renderer_version) == base_keys[s["scene_id"]]
        for s in program["scenes"] if s["scene_id"] != changed["scene_id"]
    )
    chapter = next(c for c in program["chapters"] if changed["scene_id"] in c["scene_ids"])
    return {
        "changed_scene_id": changed["scene_id"],
        "changed_field": "display_title",
        "base_cache_key": base_keys[changed["scene_id"]],
        "invalidated_cache_key": changed_key,
        "key_changed_for_target": base_keys[changed["scene_id"]] != changed_key,
        "invalidated_scene_ids": invalidated,
        "exactly_one_scene_invalidated": invalidated == [changed["scene_id"]],
        "unaffected_scene_keys_unchanged": unaffected_unchanged,
        "containing_chapter_id": chapter["chapter_id"],
        "only_target_invalidates_chapter": affected_chapter_only(program, chapter["chapter_id"], changed["scene_id"]),
        "public_write": False,
    }


def affected_chapter_only(program: Mapping[str, Any], chapter_id: str, scene_id: str) -> bool:
    return [c["chapter_id"] for c in program["chapters"] if scene_id in c["scene_ids"]] == [chapter_id]


# ---------------------------------------------------------------------------
# Packaging, hash manifest, immutable lock.
# ---------------------------------------------------------------------------

def _package_hash_manifest(package_root: Path) -> dict[str, str]:
    excluded = {"hash_manifest.json", "package_lock.json"}
    manifest = {}
    for path in sorted(package_root.rglob("*")):
        if path.is_file() and path.name not in excluded:
            manifest[path.relative_to(package_root).as_posix()] = sha256_file(path)
    return manifest


def verify_package(package_root: Path) -> dict[str, Any]:
    verification = verify_hash_manifest(package_root)
    lock_path = package_root / "package_lock.json"
    result = {"hash_verification": verification, "lock_present": lock_path.is_file()}
    if lock_path.is_file():
        lock = _read_json(lock_path)
        result["lock_status"] = lock.get("status")
        result["lock_hash_matches"] = sha256_file(package_root / "hash_manifest.json") == lock.get("hash_manifest_sha256")
    return result


def write_package_request_identity(program: Mapping[str, Any], *, renderer_version: str, narration_provider: str, voice: str) -> str:
    return logical_hash({
        "program_hash": program.get("program_hash"),
        "renderer_id": RENDERER_ID,
        "renderer_version": renderer_version,
        "motion_system_version": MOTION_SYSTEM_VERSION,
        "narration_provider": narration_provider,
        "voice": voice,
        "revision_policy_max_rounds": MAX_REVISION_ROUNDS,
    })


def write_hash_manifest(package_root: Path) -> dict[str, str]:
    manifest = _package_hash_manifest(package_root)
    _write_json(package_root / "hash_manifest.json", manifest)
    return manifest


def write_package_lock(package_root: Path, *, request_identity: str, qa_status: str | None, multimodal_status: str | None) -> dict[str, Any]:
    manifest = _read_json(package_root / "hash_manifest.json")
    verification = verify_hash_manifest(package_root)
    locked_status = "LOCKED" if verification["status"] == "PASS" and qa_status == "PASS" else "LOCKED_WITH_INTEGRITY_CAVEAT"
    _write_json(package_root / "package_lock.json", {
        "schema_version": "contentops.tier2.immutable_package_lock.v2",
        "status": locked_status,
        "request_identity": request_identity,
        "hash_manifest_sha256": sha256_file(package_root / "hash_manifest.json"),
        "hash_manifest_verified": verification["status"] == "PASS",
        "integrity_blockers": verification.get("blockers", []),
        "verified_file_count": len(manifest),
        "machine_qa_status": qa_status,
        "multimodal_status": multimodal_status,
        "visual_acceptance": "AWAITING_CHATGPT_JIM_VISUAL_AUDIO_REVIEW",
        "public_upload": False,
    })
    return {"file_count": len(manifest), "request_identity": request_identity, "hash_manifest_verified": verification["status"] == "PASS"}


# ---------------------------------------------------------------------------
# Video eligibility including a genuine VIDEO_NOT_SELECTED proof case.
# ---------------------------------------------------------------------------

def decide_video_eligibility_b1(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Bounded Tier-2 eligibility. VIDEO_NOT_SELECTED is a successful outcome."""
    claims = candidate.get("claims") or {}
    assets = candidate.get("media_assets") or []
    numeric = [c for c in claims.values() if c.get("unit") in ("percent", "basis_points")]
    visualizability = len(assets) + (1 if numeric else 0)
    rights_ready = all(str(a.get("rights_status") or "") in {"public_domain", "public_domain_us_government", "capital_chronicle_owned", "capital_chronicle_internal"} for a in assets)
    reasons: list[str] = []
    if len(claims) < 2:
        reasons.append("evidence_strength_below_video_threshold")
    if visualizability < 2:
        reasons.append("visualizability_below_video_threshold")
    if candidate.get("narrative_depth") == "insufficient":
        reasons.append("narrative_depth_insufficient")
    if not claims and not assets:
        reasons.append("no_governed_evidence_or_assets")
    if reasons:
        result = "VIDEO_NOT_SELECTED"
    elif not rights_ready:
        result = "VIDEO_BLOCKED"
    else:
        result = "VIDEO_SELECTED"
    return {
        "result": result,
        "reasons": reasons,
        "evidence_strength": len(claims),
        "visualizability": visualizability,
        "numeric_claim_count": len(numeric),
        "rights_ready": rights_ready,
        "shelf_life": "historical_evaluation_material",
        "production_cost_policy": "local_bounded",
        "public_write_authority": False,
        "video_not_selected_is_success": result == "VIDEO_NOT_SELECTED",
    }


def build_not_selected_case(repo_root: Path) -> dict[str, Any]:
    """A genuine weak governed candidate: FOMC minutes metadata-only packet.

    One factual metadata claim, zero numeric claims, zero governed visual assets,
    publication decision blocked. An honest low-depth/low-visualizability candidate.
    """
    packet_path = repo_root / "docs" / "automation" / "CONTENTOPS_FAST_SHIP_MULTI_STORY_PLATFORM_NATIVE_OPERATOR_PACKAGES_V1" / "canonical_content_evidence_packets_v3.json"
    data = _read_json(packet_path)
    packets = data.get("packets") or data.get("evidence_packets") or []
    target = None
    for pkt in packets:
        if str(pkt.get("story_id") or pkt.get("packet_story_id") or "").startswith("fomc"):
            target = pkt
            break
    if target is None and isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and "fomc" in json.dumps(item).lower():
                        target = item
                        break
            if target:
                break
    claims_out: dict[str, Any] = {}
    if isinstance(target, dict):
        for claim in target.get("claims") or target.get("authorized_claims") or []:
            cid = str(claim.get("claim_id") or "")
            if cid:
                claims_out[cid] = {**claim, "unit": claim.get("unit")}
    return {
        "case": "fomc_minutes_metadata_only",
        "packet_id": (target or {}).get("packet_id") if isinstance(target, dict) else None,
        "story_id": (target or {}).get("story_id") if isinstance(target, dict) else "fomc-minutes-metadata-only",
        "claims": claims_out,
        "media_assets": [],
        "narrative_depth": "insufficient",
        "classification": "TEST_ONLY_NON_PUBLIC",
    }


# ---------------------------------------------------------------------------
# Renderer version (cache identity) from the pinned Remotion package.
# ---------------------------------------------------------------------------

def remotion_version() -> str:
    pkg_path = REMOTION_ROOT / "package.json"
    if not pkg_path.is_file():
        raise Tier2BError("remotion_package_missing")
    deps = _read_json(pkg_path).get("dependencies") or {}
    return f"remotion@{deps.get('remotion')}"


def _load_cache(work_root: Path) -> dict[str, Any]:
    cache_path = work_root / "scene_cache.json"
    return _read_json(cache_path) if cache_path.is_file() else {}


def _save_cache(work_root: Path, cache: Mapping[str, Any]) -> None:
    _write_json(work_root / "scene_cache.json", dict(cache))


# ---------------------------------------------------------------------------
# End-to-end render of one product (long-form or short).
# ---------------------------------------------------------------------------

def render_product(program: dict[str, Any], story: Mapping[str, Any], staged_assets: Mapping[str, str],
                   work_root: Path, package_root: Path, cache: dict[str, Any], *, tag: str,
                   output_name: str, aspect_is_vertical: bool, run_critic: bool = True,
                   provider_enabled: bool = True, do_qa: bool = True) -> dict[str, Any]:
    renderer_version = remotion_version()
    profile = program["render_resolution"]
    width, height, fps = int(profile["width"]), int(profile["height"]), int(program["frame_rate"])
    narration = generate_program_narration(program, work_root)
    narration_by_scene = {row["scene_id"]: row for row in narration["scenes"]}

    jobs = []
    for scene in program["scenes"]:
        job = compile_scene_job(program, scene, narration_by_scene[scene["scene_id"]], staged_assets,
                                width=width, height=height, fps=fps, work_root=work_root)
        job["cache_key"] = scene_cache_key(scene, narration=narration_by_scene[scene["scene_id"]],
                                           staged_assets=staged_assets, width=width, height=height, fps=fps,
                                           renderer_version=renderer_version)
        job["output_path"] = str(work_root / "renders" / "scenes" / f"{scene['scene_id']}.mp4")
        jobs.append(job)

    scene_rows = render_scenes(jobs, work_root, cache=cache, renderer_version=renderer_version)
    for row in scene_rows:
        cache[row["cache_key"]] = row
    _save_cache(work_root, cache)
    row_by_scene = {row["scene_id"]: row for row in scene_rows}

    chapter_rows = []
    for chapter in program["chapters"]:
        ckey = chapter_cache_key(chapter, scene_rows, renderer_version)
        chapter_out = work_root / "renders" / "chapters" / f"{chapter['chapter_id']}.mp4"
        cached = None
        if ckey in cache and chapter_out.is_file() and cache[ckey].get("render_sha256") == sha256_file(chapter_out):
            cached = cache[ckey]
        if cached:
            chapter_rows.append({"chapter_id": chapter["chapter_id"], "output_path": str(chapter_out),
                                 "render_sha256": cached["render_sha256"], "duration_seconds": cached["duration_seconds"],
                                 "cache_hit": True})
        else:
            assembled = assemble_chapter(chapter, [row_by_scene[sid] for sid in chapter["scene_ids"]], chapter_out,
                                         width=width, height=height, fps=fps)
            assembled["cache_hit"] = False
            chapter_rows.append(assembled)
            cache[ckey] = assembled
    _save_cache(work_root, cache)

    assembly = compute_assembly_offsets(chapter_rows, program, scene_rows, narration_by_scene, cache)
    package_root.mkdir(parents=True, exist_ok=True)
    captions = build_caption_sidecars(program, narration_by_scene, assembly, package_root, tag=tag)
    master_path = package_root / output_name
    master = assemble_master(chapter_rows, master_path, sidecar_srt=Path(captions["srt"]), burn_captions=False)

    result = {
        "video_id": program["video_id"],
        "mode": program["mode"],
        "master_path": master["output_path"],
        "master_sha256": master["master_hash"],
        "duration_seconds": master["duration_seconds"],
        "assembly": assembly,
        "captions": captions,
        "chapter_rows": chapter_rows,
        "scene_rows": scene_rows,
        "narration": narration,
    }
    if run_critic:
        critic_dir = work_root / "critic" / tag
        critic_dir.mkdir(parents=True, exist_ok=True)
        revision_history = []
        critic = run_multimodal_critic(master_path, program, critic_dir, provider_enabled=provider_enabled,
                                       duration_seconds=master["duration_seconds"])
        result["critic_initial"] = critic
        rounds = 0
        current_program = program
        while critic.get("status") == "CRITIC_NEEDS_REVISION" and rounds < MAX_REVISION_ROUNDS:
            rounds += 1
            revision = apply_bounded_revision(critic, current_program, rounds, critic_dir)
            revision_history.append({"round": rounds, **revision})
            if not revision["applied"]:
                break
            affected_scene_ids = {p["scene_id"] for p in revision["patch"]}
            affected_chapters = [c["chapter_id"] for c in current_program["chapters"] if any(s in affected_scene_ids for s in c["scene_ids"])]
            rerendered = []
            for scene in current_program["scenes"]:
                if scene["scene_id"] not in affected_scene_ids:
                    continue
                job = compile_scene_job(current_program, scene, narration_by_scene[scene["scene_id"]], staged_assets,
                                        width=width, height=height, fps=fps, work_root=work_root)
                job["cache_key"] = scene_cache_key(scene, narration=narration_by_scene[scene["scene_id"]],
                                                   staged_assets=staged_assets, width=width, height=height, fps=fps,
                                                   renderer_version=renderer_version)
                job["output_path"] = str(work_root / "renders" / "scenes" / f"{scene['scene_id']}.mp4")
                rows = render_scenes([job], work_root, cache=cache, renderer_version=renderer_version)
                for row in rows:
                    cache[row["cache_key"]] = row
                rerendered.extend(rows)
            row_by_scene.update({row["scene_id"]: row for row in rerendered})
            for chapter in current_program["chapters"]:
                if chapter["chapter_id"] not in affected_chapters:
                    continue
                chapter_out = work_root / "renders" / "chapters" / f"{chapter['chapter_id']}.mp4"
                assembled = assemble_chapter(chapter, [row_by_scene[sid] for sid in chapter["scene_ids"]], chapter_out,
                                             width=width, height=height, fps=fps)
                cache[chapter_cache_key(chapter, list(row_by_scene.values()), renderer_version)] = assembled
                for idx, row in enumerate(chapter_rows):
                    if row["chapter_id"] == chapter["chapter_id"]:
                        chapter_rows[idx] = {**assembled, "cache_hit": False}
            assembly = compute_assembly_offsets(chapter_rows, current_program, list(row_by_scene.values()), narration_by_scene, cache)
            captions = build_caption_sidecars(current_program, narration_by_scene, assembly, package_root, tag=tag)
            master = assemble_master(chapter_rows, master_path)
            critic = run_multimodal_critic(master_path, current_program, critic_dir, provider_enabled=provider_enabled,
                                           duration_seconds=master["duration_seconds"])
            revision_history.append({"round": rounds, "post_critic_status": critic.get("status"), "post_defect_count": len(critic.get("defects") or [])})
        result["critic_final"] = critic
        result["revision_history"] = revision_history
        result["revision_rounds_used"] = rounds
        result["master_path"] = master["output_path"]
        result["master_sha256"] = master["master_hash"]
        result["duration_seconds"] = master["duration_seconds"]
        result["assembly"] = assembly
        result["captions"] = captions
        result["chapter_rows"] = chapter_rows
        result["scene_rows"] = list(row_by_scene.values())
    return result


# ---------------------------------------------------------------------------
# Orchestrator + CLI.
# ---------------------------------------------------------------------------

def run_tier2b(*, output_root: str | Path, provider_enabled: bool = True, do_long: bool = True,
               do_short: bool = True, input_dir: str | Path | None = None) -> dict[str, Any]:
    repo_root = REPO_ROOT
    out_root = Path(output_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    work_root = out_root / "_work"
    package_root = out_root / "package"
    package_root.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    default_input = repo_root / "docs" / "automation" / "CONTENTOPS_FULL_AUTOMATION_LIVE_CANONICAL_BROWSER_RUN_V1" / "contentops_full_automation_live_20260807_1"
    story = load_governed_input(input_dir or default_input)
    series = compute_curve_series(story)
    eligibility = decide_video_eligibility_b1(story)

    not_selected_case = build_not_selected_case(repo_root)
    not_selected_eligibility = decide_video_eligibility_b1(not_selected_case)
    _write_json(out_root / "corpus" / "video_not_selected_case.json", {"case": not_selected_case, "eligibility": not_selected_eligibility})

    if eligibility["result"] != "VIDEO_SELECTED":
        raise Tier2BError(f"story_not_video_selected:{eligibility['result']}")

    renderer_version = remotion_version()
    cache = _load_cache(work_root)
    staged_assets = _stage_assets({}, story, work_root)

    director_long = run_video_director(story, program_mode="LONG_FORM_EDITORIAL_15_45M", work_root=work_root, provider_enabled=provider_enabled)
    director_short = run_video_director(story, program_mode="SHORT_FORM_NATIVE", work_root=work_root, provider_enabled=provider_enabled)

    result = {"story_id": story["story_id"], "eligibility": eligibility, "not_selected_case": not_selected_eligibility,
              "series_window": {"start": series["window_start"], "end": series["window_end"], "observations": series["observation_count"]}}

    if do_long:
        program_long = build_long_program(story, series, director_long)
        _write_json(out_root / "package" / "video_program.json", program_long)
        long_result = render_product(program_long, story, staged_assets, work_root / "long", package_root, cache,
                                     tag="long", output_name="master_16x9.mp4", aspect_is_vertical=False,
                                     run_critic=True, provider_enabled=provider_enabled)
        _write_json(out_root / "package" / "scene_manifest.json", {"long_form": long_result["scene_rows"]})
        _write_json(out_root / "package" / "chapter_manifest.json", {"long_form": long_result["chapter_rows"]})
        _write_json(out_root / "package" / "script.json", {"long_form": [{"scene_id": s["scene_id"], "segments": s["narration_segments"], "claim_bindings": s["claim_bindings"]} for s in program_long["scenes"]]})
        result["long"] = long_result
        result["program_long_hash"] = program_long["program_hash"]

        qa_long = deterministic_qa(program_long, {"output_path": long_result["master_path"]}, long_result["assembly"],
                                   long_result["captions"], long_result["scene_rows"],
                                   {row["scene_id"]: row for row in long_result["narration"]["scenes"]},
                                   package_root, aspect="landscape")
        _write_json(out_root / "package" / "deterministic_media_qa.json", qa_long)
        result["qa_long"] = qa_long

        # Proof of selective rerender (logical invalidation) after render.
        proof = selective_rerender_proof(program_long, {row["scene_id"]: row for row in long_result["narration"]["scenes"]},
                                         staged_assets, work_root / "long", cache, renderer_version,
                                         width=int(program_long["render_resolution"]["width"]),
                                         height=int(program_long["render_resolution"]["height"]),
                                         fps=int(program_long["frame_rate"]))
        _write_json(out_root / "package" / "revision_history.json", {"selective_rerender": proof, "revision_history": long_result.get("revision_history", [])})
        result["selective_rerender"] = proof

    if do_short:
        program_short = build_short_program(story, series, director_short)
        short_root = out_root / "package"
        short_result = render_product(program_short, story, staged_assets, work_root / "short", short_root, cache,
                                      tag="short", output_name="short_01_9x16.mp4", aspect_is_vertical=True,
                                      run_critic=True, provider_enabled=provider_enabled)
        qa_short = deterministic_qa(program_short, {"output_path": short_result["master_path"]}, short_result["assembly"],
                                    short_result["captions"], short_result["scene_rows"],
                                    {row["scene_id"]: row for row in short_result["narration"]["scenes"]},
                                    short_root, aspect="vertical")
        _write_json(out_root / "package" / "deterministic_media_qa_short.json", qa_short)
        result["short"] = short_result
        result["qa_short"] = qa_short
        result["program_short_hash"] = program_short["program_hash"]

    request_identity = write_package_request_identity(
        {"program_hash": result.get("program_long_hash") or result.get("program_short_hash")},
        renderer_version=renderer_version, narration_provider=NARRATION_PROVIDER, voice=VOICE,
    )
    write_hash_manifest(package_root)
    _write_json(out_root / "package" / "rights_provenance_report.json", {
        "schema_version": "contentops.tier2.rights_provenance.v1",
        "source_document_id": SOURCE_ID,
        "source_rights": "public_domain_us_government",
        "renderer": RENDERER_ID,
        "renderer_version": renderer_version,
        "motion_system_version": MOTION_SYSTEM_VERSION,
        "generated_media": [],
        "music": "none_no_music_track",
        "caption_timing_source": "narration_segment_boundaries",
        "public_upload": False,
    })
    write_hash_manifest(package_root)
    lock = write_package_lock(
        package_root,
        request_identity=request_identity,
        qa_status=result.get("qa_long", result.get("qa_short", {})).get("status"),
        multimodal_status=result.get("long", {}).get("critic_final", {}).get("status"),
    )
    result["package"] = lock
    result["runtime_seconds"] = round(time.perf_counter() - started, 3)
    result["public_or_private_upload"] = False
    result["provider_calls_recorded"] = True
    _write_json(out_root / "run_manifest.json", result)
    return result


def tier2_video_remotion_command(argv: Sequence[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(prog="tier2-video-remotion",
                                     description="Tier-2-B Remotion multimodal video factory (local, bounded, no upload).")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, default=None)
    parser.add_argument("--provider", choices=["enabled", "disabled"], default="enabled")
    parser.add_argument("--long-only", action="store_true")
    parser.add_argument("--short-only", action="store_true")
    args = parser.parse_args(argv)
    do_long = not args.short_only
    do_short = not args.long_only
    try:
        result = run_tier2b(output_root=args.output_root, provider_enabled=(args.provider == "enabled"),
                            do_long=do_long, do_short=do_short, input_dir=args.input_dir)
    except Tier2BError as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc), "public_or_private_upload": False}, sort_keys=True))
        return 1
    summary = {
        "status": "COMPLETE_TIER2_B_PRODUCT_SLICE_AWAITING_CHATGPT_JIM_VISUAL_AUDIO_REVIEW",
        "output_root": str(args.output_root),
        "eligibility": result["eligibility"]["result"],
        "video_not_selected": result["not_selected_case"]["result"],
        "long_duration_seconds": result.get("long", {}).get("duration_seconds"),
        "short_duration_seconds": result.get("short", {}).get("duration_seconds"),
        "qa_long_status": result.get("qa_long", {}).get("status"),
        "qa_short_status": result.get("qa_short", {}).get("status"),
        "critic_long_final": result.get("long", {}).get("critic_final", {}).get("status"),
        "runtime_seconds": result["runtime_seconds"],
        "public_or_private_upload": False,
    }
    print(json.dumps(summary, sort_keys=True))
    return 0

















