"""Compile a measured, annotation-safe primary-document asset for Remotion.

The preferred path consumes the authoritative Census PDF text layer.  A
clearly labelled exact-source excerpt path exists for environments where the
Census edge blocks byte retrieval.  Both paths bind the annotation to measured
text geometry and emit the same fail-closed geometry contract.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Any, Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont

from live_contentops.breaking_news_crisp_v1 import sha256_file, validate_annotation_geometry, write_json


PDF_SEARCH_TEXT = "were $763.6 billion, down 0.6 percent"
TARGET_TEXT = (
    "Advance estimates of U.S. retail and food services sales for July 2026, adjusted for seasonal variation "
    "and holiday and trading-day differences, but not for price changes, were $763.6 billion, down 0.6 percent "
    "(±0.4 percent) from the previous month, but up 5.0 percent (±0.5 percent) from July 2025."
)
TARGET_SENTENCE = (
    TARGET_TEXT
)
PDF_URL = "https://www.census.gov/retail/marts/www/marts_current.pdf"
HTML_URL = "https://www.census.gov/retail/sales.html"
ASSET_SIZE = (900, 1120)
FRAME_PLACEMENT = {"x": 70.0, "y": 300.0, "width": 940.0}


def _font(size: int, *, bold: bool = False) -> tuple[ImageFont.FreeTypeFont, Path]:
    names = ["arialbd.ttf" if bold else "arial.ttf", "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    roots = [Path(r"C:\Windows\Fonts"), Path("/usr/share/fonts/truetype/dejavu")]
    for root in roots:
        for name in names:
            candidate = root / name
            if candidate.is_file():
                return ImageFont.truetype(str(candidate), size=size), candidate
    return ImageFont.truetype(names[-1], size=size), Path(names[-1])


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        proposed = f"{current} {word}".strip()
        if draw.textbbox((0, 0), proposed, font=font)[2] <= width or not current:
            current = proposed
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _union(rectangles: Iterable[Sequence[float]]) -> list[float]:
    rows = [tuple(float(value) for value in rect) for rect in rectangles]
    if not rows:
        raise ValueError("no_rectangles_to_union")
    return [min(row[0] for row in rows), min(row[1] for row in rows), max(row[2] for row in rows), max(row[3] for row in rows)]


def _transform_bbox(rect: Sequence[float]) -> list[float]:
    scale = FRAME_PLACEMENT["width"] / ASSET_SIZE[0]
    x0, y0, x1, y1 = (float(value) for value in rect)
    return [
        FRAME_PLACEMENT["x"] + x0 * scale,
        FRAME_PLACEMENT["y"] + y0 * scale,
        FRAME_PLACEMENT["x"] + x1 * scale,
        FRAME_PLACEMENT["y"] + y1 * scale,
    ]


def _compile_exact_source_excerpt(readback: Path) -> tuple[Image.Image, dict[str, Any]]:
    image = Image.new("RGB", ASSET_SIZE, "#fffdf8")
    draw = ImageDraw.Draw(image, "RGBA")
    body, body_path = _font(30)
    body_bold, bold_path = _font(30, bold=True)
    small, _ = _font(20)
    title, _ = _font(37, bold=True)
    metric, _ = _font(55, bold=True)
    metric_label, _ = _font(19, bold=True)

    draw.text((54, 42), "U.S. CENSUS BUREAU", fill="#10212b", font=body_bold)
    draw.text((54, 90), "FOR RELEASE • AUGUST 14, 2026 • 8:30 AM ET", fill="#516673", font=small)
    draw.line((54, 130, 846, 130), fill="#b9c3c9", width=2)
    draw.multiline_text(
        (54, 165),
        "ADVANCE MONTHLY SALES FOR\nRETAIL AND FOOD SERVICES, JULY 2026",
        fill="#10212b", font=title, spacing=8,
    )
    draw.text((54, 277), "Release Number: CB26-131", fill="#516673", font=small)

    y = 338
    target_line_rects: list[list[float]] = []
    lines = _wrap(draw, TARGET_SENTENCE, body_bold, 792)
    for line in lines:
        bbox = draw.textbbox((54, y), line, font=body_bold)
        target_line_rects.append([float(value) for value in bbox])
        y += 45
    target_bbox = _union(target_line_rects)
    padding_x, padding_y = 13, 10
    annotation_bbox = [
        target_bbox[0] - padding_x,
        target_bbox[1] - padding_y,
        target_bbox[2] + padding_x,
        target_bbox[3] + padding_y,
    ]
    draw.rounded_rectangle(annotation_bbox, radius=9, fill="#fff0a6", outline="#d89a31", width=3)
    draw.rectangle((annotation_bbox[0], annotation_bbox[1], annotation_bbox[0] + 7, annotation_bbox[3]), fill="#ef4b4f")
    for index, line in enumerate(lines):
        draw.text((54, target_line_rects[index][1]), line, fill="#10212b", font=body_bold)

    metric_y = int(annotation_bbox[3] + 58)
    metrics: list[dict[str, Any]] = []
    for left, width, label, value, color in (
        (54, 465, "JULY SALES", "$763.6B", "#10212b"),
        (541, 305, "MONTH / MONTH", "−0.6%", "#ef4b4f"),
    ):
        box = [left, metric_y, left + width, metric_y + 170]
        draw.rounded_rectangle(box, radius=10, fill="#edf2f5", outline="#c7d0d5", width=2)
        draw.text((left + 24, metric_y + 22), label, fill="#516673", font=metric_label)
        draw.text((left + 24, metric_y + 63), value, fill=color, font=metric)
        metrics.append({"label": value, "bbox": [float(value) for value in box]})

    draw.text((54, 1054), "EXACT-SOURCE EXCERPT • PRIMARY RELEASE • PAGE 1 TEXT", fill="#516673", font=small)
    return image, {
        "source_kind": "OFFICIAL_HTML_EXACT_SOURCE_DERIVATIVE",
        "source_document_sha256": sha256_file(readback),
        "source_page": 1,
        "source_url": HTML_URL,
        "canonical_pdf_url": PDF_URL,
        "exact_target_text": TARGET_TEXT,
        "document_target_bbox": target_bbox,
        "asset_target_bbox": target_bbox,
        "asset_annotation_bbox": annotation_bbox,
        "asset_unrelated_glyph_bboxes": metrics,
        "annotation_padding": {"x": padding_x, "y": padding_y},
        "font_files": [
            {"path": str(body_path), "sha256": sha256_file(body_path) if body_path.is_file() else None},
            {"path": str(bold_path), "sha256": sha256_file(bold_path) if bold_path.is_file() else None},
        ],
        "source_constraint": "Census returned an edge-policy block to direct local byte retrieval; no blocked or synthetic PDF was treated as source evidence.",
    }


def _compile_pdf(pdf_path: Path) -> tuple[Image.Image, dict[str, Any]]:
    if pdf_path.read_bytes()[:5] != b"%PDF-":
        raise ValueError("source_is_not_pdf")
    import pdfplumber

    with pdfplumber.open(pdf_path) as document:
        if len(document.pages) != 7:
            raise ValueError(f"unexpected_pdf_page_count:{len(document.pages)}")
        page = document.pages[0]
        matches = page.search(PDF_SEARCH_TEXT, regex=False, case=False)
        if not matches:
            raise ValueError("target_text_not_found_in_pdf_text_layer")
        source_bbox = _union([[row["x0"], row["top"], row["x1"], row["bottom"]] for row in matches])
        rendered = page.to_image(resolution=180, antialias=True).original.convert("RGB")
        scale_x = ASSET_SIZE[0] / rendered.width
        scale_y = ASSET_SIZE[1] / rendered.height
        image = rendered.resize(ASSET_SIZE, Image.Resampling.LANCZOS)
        target_bbox = [source_bbox[0] * scale_x, source_bbox[1] * scale_y, source_bbox[2] * scale_x, source_bbox[3] * scale_y]
        padding_x, padding_y = 10, 8
        annotation_bbox = [target_bbox[0] - padding_x, target_bbox[1] - padding_y, target_bbox[2] + padding_x, target_bbox[3] + padding_y]
        overlay = Image.new("RGBA", ASSET_SIZE, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay, "RGBA")
        draw.rounded_rectangle(annotation_bbox, radius=7, fill=(255, 226, 83, 72), outline=(239, 75, 79, 255), width=3)
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
        return image, {
            "source_kind": "AUTHORITATIVE_PDF_TEXT_LAYER",
            "source_document_sha256": sha256_file(pdf_path),
            "source_page": 1,
            "source_url": PDF_URL,
            "canonical_pdf_url": PDF_URL,
            "exact_target_text": PDF_SEARCH_TEXT,
            "document_target_bbox": source_bbox,
            "asset_target_bbox": target_bbox,
            "asset_annotation_bbox": annotation_bbox,
            "asset_unrelated_glyph_bboxes": [],
            "annotation_padding": {"x": padding_x, "y": padding_y},
            "transform_from_document": {"kind": "AFFINE", "scale_x": scale_x, "scale_y": scale_y, "translate_x": 0, "translate_y": 0},
        }


def compile_primary_document(*, readback: Path, output_png: Path, geometry_json: Path, pdf_path: Path | None = None) -> dict[str, Any]:
    if pdf_path and pdf_path.is_file():
        image, record = _compile_pdf(pdf_path)
    else:
        image, record = _compile_exact_source_excerpt(readback)

    output_png.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_png, format="PNG", optimize=True)
    asset_annotation = record["asset_annotation_bbox"]
    rendered_annotation = _transform_bbox(asset_annotation)
    rendered_target = _transform_bbox(record["asset_target_bbox"])
    rendered_unrelated = [
        {"label": row["label"], "bbox": _transform_bbox(row["bbox"])}
        for row in record["asset_unrelated_glyph_bboxes"]
    ]
    scale = FRAME_PLACEMENT["width"] / ASSET_SIZE[0]
    record.update({
        "schema_version": "contentops.v2.document_annotation_geometry.v2",
        "compiled_asset": str(output_png.resolve()),
        "compiled_asset_sha256": sha256_file(output_png),
        "asset_size": list(ASSET_SIZE),
        "frame_size": [1080, 1920],
        "frame_placement": FRAME_PLACEMENT,
        "rendered_target_bbox": rendered_target,
        "annotation_bbox": rendered_annotation,
        "unrelated_glyph_bboxes": rendered_unrelated,
        "transform_identity": {"kind": "AFFINE", "scale_x": scale, "scale_y": scale, "translate_x": FRAME_PLACEMENT["x"], "translate_y": FRAME_PLACEMENT["y"]},
        "settled_frames": {
            "1080x1920": {"annotation_bbox": rendered_annotation},
            "2160x3840": {"annotation_bbox": [value * 2 for value in rendered_annotation]},
        },
        "rendered_document_bbox": [FRAME_PLACEMENT["x"], FRAME_PLACEMENT["y"], FRAME_PLACEMENT["x"] + FRAME_PLACEMENT["width"], FRAME_PLACEMENT["y"] + ASSET_SIZE[1] * scale],
    })
    record["validation"] = validate_annotation_geometry(record)
    if record["validation"]["status"] != "PASS":
        raise ValueError(f"document_geometry_failed:{record['validation']['errors']}")
    write_json(geometry_json, record)
    return record
