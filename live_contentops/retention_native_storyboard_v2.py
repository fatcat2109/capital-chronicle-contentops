"""Deterministic native compilers and cheap storyboard/animatic renderer.

Layout instructions come from accepted GPT-5.6 segment artifacts.  This module performs
mechanical composition only; it does not invent shots, labels, assets, or motion intent.
"""
from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from live_contentops.media_manifest_authority_v1 import sha256_file

FONT_REGULAR = r"C:\Windows\Fonts\segoeui.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
BACKGROUND = (8, 15, 24)
INK = (244, 247, 250)
MUTED = (185, 200, 214)
ACCENT = (63, 207, 180)
SOURCE = (184, 198, 212)


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size=size)


def _cover(image: Image.Image, size: tuple[int, int], anchor: str = "center") -> Image.Image:
    target_w, target_h = size
    ratio = max(target_w / image.width, target_h / image.height)
    resized = image.resize(
        (max(1, round(image.width * ratio)), max(1, round(image.height * ratio))),
        Image.Resampling.LANCZOS,
    )
    x = max(0, (resized.width - target_w) // 2)
    y = max(0, (resized.height - target_h) // 2)
    if anchor == "top":
        y = 0
    elif anchor == "bottom":
        y = max(0, resized.height - target_h)
    elif anchor == "left":
        x = 0
    elif anchor == "right":
        x = max(0, resized.width - target_w)
    return resized.crop((x, y, x + target_w, y + target_h))


def _fit_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    *,
    box: tuple[int, int, int, int],
    maximum: int,
    minimum: int,
    bold: bool,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    x0, y0, x1, y1 = box
    for size in range(maximum, minimum - 1, -2):
        font = _font(size, bold=bold)
        approximate = max(8, int((x1 - x0) / (size * 0.54)))
        lines = textwrap.wrap(text, width=approximate, break_long_words=False)
        line_height = int(size * 1.18)
        if lines and len(lines) * line_height <= y1 - y0:
            return font, lines
    return _font(minimum, bold=bold), textwrap.wrap(text, width=max(8, int((x1 - x0) / (minimum * 0.54))))


def render_native_chart(
    plan: Mapping[str, Any], *, output_path: str | Path, width: int, height: int
) -> dict[str, Any]:
    points = list(plan["points"])
    canvas = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    margin_x = int(width * 0.10)
    top = int(height * 0.15)
    bottom = int(height * 0.78)
    values = [float(row["y"]) for row in points]
    low, high = min(values), max(values)
    spread = max(1.0, high - low)
    xs = [margin_x + index * (width - 2 * margin_x) / max(1, len(points) - 1) for index in range(len(points))]
    ys = [bottom - (value - low) / spread * (bottom - top) for value in values]
    for index in range(len(points) - 1):
        draw.line((xs[index], ys[index], xs[index + 1], ys[index + 1]), fill=ACCENT, width=max(5, width // 180))
    label_font = _font(max(24, width // 30), bold=True)
    value_font = _font(max(30, width // 24), bold=True)
    for x, y, row in zip(xs, ys, points):
        radius = max(7, width // 90)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=INK)
        draw.text((x, y - value_font.size * 1.35), str(row.get("label") or row["y"]), font=value_font, fill=INK, anchor="mm")
        draw.text((x, bottom + label_font.size * 1.25), str(row["x"]), font=label_font, fill=MUTED, anchor="mm")
    draw.text((margin_x, int(height * 0.055)), str(plan["source_label"]), font=_font(max(20, width // 38)), fill=SOURCE)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)
    return {"path": str(path), "sha256": sha256_file(path), "width": width, "height": height}


def render_native_map(
    plan: Mapping[str, Any], *, source_path: str | Path, output_path: str | Path, width: int, height: int
) -> dict[str, Any]:
    with Image.open(source_path) as opened:
        map_image = opened.convert("RGB")
    canvas = Image.new("RGB", (width, height), (229, 235, 232))
    if width < height:
        map_height = int(height * 0.68)
        panel = _cover(map_image, (width, map_height), "center")
        canvas.paste(panel, (0, int(height * 0.16)))
        label_top = int(height * 0.055)
    else:
        panel = _cover(map_image, (width, height), "center")
        canvas.paste(panel, (0, 0))
        label_top = int(height * 0.06)
    draw = ImageDraw.Draw(canvas, "RGBA")
    title_size = max(34, width // 22)
    draw.rounded_rectangle((int(width * 0.04), label_top, int(width * 0.96), label_top + title_size * 1.8), radius=18, fill=(6, 16, 24, 222))
    draw.text((width // 2, label_top + title_size * 0.85), str(plan["chokepoint"]), font=_font(title_size, bold=True), fill=INK, anchor="mm")
    source_text = "Source: " + str(plan["geography_source"])
    draw.rectangle((0, int(height * 0.93), width, height), fill=(6, 16, 24, 230))
    draw.text((int(width * 0.05), int(height * 0.955)), source_text, font=_font(max(18, width // 48)), fill=SOURCE, anchor="lm")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)
    return {"path": str(path), "sha256": sha256_file(path), "width": width, "height": height}


def render_native_document(
    plan: Mapping[str, Any], *, output_path: str | Path, width: int, height: int
) -> dict[str, Any]:
    canvas = Image.new("RGB", (width, height), (238, 238, 232))
    draw = ImageDraw.Draw(canvas)
    margin = int(width * 0.08)
    draw.rectangle((0, 0, width, int(height * 0.16)), fill=(9, 45, 70))
    draw.text((margin, int(height * 0.055)), "U.S. ENERGY INFORMATION ADMINISTRATION", font=_font(max(24, width // 34), bold=True), fill=INK)
    draw.text((margin, int(height * 0.115)), str(plan["source_date"]), font=_font(max(20, width // 42)), fill=(188, 218, 235))
    excerpt = str(plan["governed_excerpt"])
    box = (margin, int(height * 0.25), width - margin, int(height * 0.72))
    font, lines = _fit_text(draw, excerpt, box=box, maximum=max(42, width // 16), minimum=max(26, width // 30), bold=True)
    y = box[1]
    for line in lines:
        draw.text((margin, y), line, font=font, fill=(16, 30, 40))
        y += int(font.size * 1.22)
    highlight_y = max(box[1], y - int(font.size * 1.34))
    draw.rectangle((margin - 8, highlight_y, width - margin + 8, min(int(height * 0.75), highlight_y + int(font.size * 1.35))), outline=(22, 153, 132), width=max(4, width // 250))
    draw.text((margin, int(height * 0.87)), str(plan["source_label"]), font=_font(max(22, width // 40), bold=True), fill=(22, 76, 105))
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path)
    return {"path": str(path), "sha256": sha256_file(path), "width": width, "height": height}


def render_storyboard_frame(
    beat: Mapping[str, Any],
    *,
    asset_paths: Mapping[str, str],
    output_path: str | Path,
    width: int,
    height: int,
    captions_visible: bool = False,
) -> dict[str, Any]:
    selected = [str(item) for item in beat.get("asset_ids") or ()]
    if not selected or selected[0] not in asset_paths:
        raise ValueError(f"storyboard_primary_asset_missing:{beat.get('beat_id')}")
    with Image.open(asset_paths[selected[0]]) as opened:
        primary = opened.convert("RGB")
    anchor = str(beat.get("crop_anchor") or "center")
    canvas = _cover(primary, (width, height), anchor)
    canvas = ImageEnhance.Contrast(canvas).enhance(1.03)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay, "RGBA")
    placement = str(beat.get("asset_placement") or "full_bleed")
    if len(selected) > 1 and selected[1] in asset_paths and placement in {"split", "inset", "document_crop", "data_stage"}:
        with Image.open(asset_paths[selected[1]]) as opened:
            secondary = opened.convert("RGB")
        inset_w, inset_h = int(width * 0.46), int(height * 0.36)
        inset = _cover(secondary, (inset_w, inset_h), "center")
        ix, iy = int(width * 0.50), int(height * 0.08)
        canvas.paste(inset, (ix, iy))
        odraw.rounded_rectangle((ix - 5, iy - 5, ix + inset_w + 5, iy + inset_h + 5), radius=14, outline=(255, 255, 255, 225), width=5)
    odraw.rectangle((0, int(height * 0.48), width, height), fill=(4, 10, 16, 190))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(canvas)
    margin = int(width * 0.07)
    label = str(beat.get("onscreen_label") or beat["viewer_takeaway"])
    box = (margin, int(height * 0.57), width - margin, int(height * 0.79))
    font, lines = _fit_text(draw, label, box=box, maximum=max(42, width // 14), minimum=max(28, width // 28), bold=True)
    y = box[1]
    for line in lines[:4]:
        draw.text((margin, y), line, font=font, fill=INK)
        y += int(font.size * 1.12)
    callout = str(beat.get("data_callout") or "").strip()
    if callout:
        callout_font = _font(max(28, width // 24), bold=True)
        draw.rounded_rectangle((margin, int(height * 0.47), width - margin, int(height * 0.55)), radius=16, fill=(24, 128, 112, 235))
        draw.text((width // 2, int(height * 0.51)), callout, font=callout_font, fill=INK, anchor="mm")
    source = str(beat.get("source_label") or "")
    draw.text((margin, int(height * 0.92)), source, font=_font(max(18, width // 42)), fill=SOURCE)
    if captions_visible:
        caption = str(beat.get("narration") or "")
        cfont, clines = _fit_text(draw, caption, box=(margin, int(height * 0.80), width - margin, int(height * 0.91)), maximum=max(26, width // 30), minimum=max(20, width // 44), bold=True)
        cy = int(height * 0.80)
        for line in clines[:2]:
            draw.text((width // 2, cy), line, font=cfont, fill=INK, anchor="ma")
            cy += int(cfont.size * 1.15)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(path, quality=92)
    return {
        "beat_id": str(beat["beat_id"]),
        "path": str(path),
        "sha256": sha256_file(path),
        "asset_ids": selected,
        "captions_visible": captions_visible,
        "width": width,
        "height": height,
    }


def contact_sheet(
    frames: Sequence[Mapping[str, Any]], *, output_path: str | Path, columns: int = 4
) -> dict[str, Any]:
    if not frames:
        raise ValueError("contact_sheet_frames_empty")
    thumbnails: list[Image.Image] = []
    for row in frames:
        with Image.open(str(row["path"])) as opened:
            thumb = opened.convert("RGB")
            thumb.thumbnail((420, 420), Image.Resampling.LANCZOS)
            thumbnails.append(thumb.copy())
    cell_w = max(image.width for image in thumbnails) + 28
    cell_h = max(image.height for image in thumbnails) + 72
    rows = (len(thumbnails) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * cell_w, rows * cell_h), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    for index, (image, metadata) in enumerate(zip(thumbnails, frames)):
        x = (index % columns) * cell_w + 14
        y = (index // columns) * cell_h + 42
        canvas.paste(image, (x, y))
        draw.text((x, 10 + (index // columns) * cell_h), str(metadata["beat_id"]), font=_font(22, bold=True), fill=INK)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, quality=90)
    return {"path": str(path), "sha256": sha256_file(path), "frame_count": len(frames)}


def render_animatic(
    frames: Sequence[Mapping[str, Any]], *, output_path: str | Path, ffmpeg: str
) -> dict[str, Any]:
    if not frames:
        raise ValueError("animatic_frames_empty")
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = output.with_suffix(".concat.txt")
    lines: list[str] = []
    total = 0.0
    for row in frames:
        path = Path(str(row["path"])).resolve().as_posix().replace("'", "'\\''")
        duration = float(row["duration_seconds"])
        total += duration
        lines.extend((f"file '{path}'", f"duration {duration:.6f}"))
    lines.append(f"file '{Path(str(frames[-1]['path'])).resolve().as_posix()}'")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    completed = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-v",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(manifest),
            "-r",
            "30",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "libx264",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=1800,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError("animatic_render_failed:" + completed.stderr[-1200:])
    return {
        "path": str(output),
        "sha256": sha256_file(output),
        "duration_seconds": round(total, 6),
        "captions_visible": False,
        "audio": False,
    }
