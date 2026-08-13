"""Selective captions-hidden proxy rerender for bounded creative revisions."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence

from live_contentops.media_manifest_authority_v1 import sha256_file
from live_contentops.retention_native_video_factory_v2 import (
    _compile_jobs,
    _find_binary,
    _render_jobs,
    _renderer_source_manifest,
    build_director_bundle,
    hydrate_assets,
    load_governed_oil_story,
)


def run_selective_preview(
    *, input_dir: Path, director_source: Path, renderer_root: Path,
    output_root: Path, shot_ids: Sequence[str], sample_phases: Sequence[float],
    captions_visible: bool = False,
) -> dict[str, Any]:
    exact_ids = tuple(dict.fromkeys(str(value) for value in shot_ids))
    phases = tuple(float(value) for value in sample_phases)
    if not exact_ids or any(value <= 0.0 or value >= 1.0 for value in phases):
        raise ValueError("selective_preview_scope_invalid")
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "contracts").mkdir(parents=True, exist_ok=True)
    (output_root / "receipts").mkdir(parents=True, exist_ok=True)
    story = load_governed_oil_story(input_dir)
    source = json.loads(director_source.read_text(encoding="utf-8"))
    bundle = build_director_bundle(source, story)
    renderer_manifest = _renderer_source_manifest(renderer_root)
    public_dir = output_root / "render_public"
    _, assets, asset_network_calls = hydrate_assets(
        bundle,
        repo_root=input_dir.parents[3],
        public_dir=public_dir,
        source_cache=output_root / "source_cache",
        governed_evidence=story["evidence"],
    )
    variant_plans = {row.variant_id: row for row in bundle.platform_variant_plan.variants}
    narration: dict[str, dict[str, Any]] = {}
    for graph in bundle.beat_graphs:
        fps = variant_plans[graph.variant_id].fps
        for beat in graph.beats:
            narration[beat.beat_id] = {
                "duration_in_frames": max(1, int(round(beat.target_duration_seconds * fps))),
                "sha256": "0" * 64,
            }
    jobs = _compile_jobs(
        bundle,
        narration=narration,
        assets=assets,
        output_root=output_root,
        renderer_source_fingerprint=str(renderer_manifest["renderer_source_fingerprint"]),
        proxy=True,
        captions_visible=captions_visible,
    )
    indexed = {
        str(row["beat_id"]): row for rows in jobs.values() for row in rows
        if str(row["beat_id"]) in exact_ids
    }
    if tuple(indexed) != exact_ids:
        raise RuntimeError("selective_preview_shot_coverage_invalid")
    selected = [indexed[shot_id] for shot_id in exact_ids]
    node = _find_binary("node", "CONTENTOPS_NODE_BINARY")
    ffmpeg = _find_binary("ffmpeg", "CONTENTOPS_FFMPEG_BINARY")
    ffprobe = _find_binary("ffprobe", "CONTENTOPS_FFPROBE_BINARY")
    render_receipt = _render_jobs(
        selected,
        renderer_root=renderer_root,
        public_dir=public_dir,
        output_root=output_root,
        node=node,
        ffprobe=ffprobe,
        receipt_name="selective_revision_preview",
    )
    review_dir = output_root / "review" / "selective_revision"
    review_dir.mkdir(parents=True, exist_ok=True)
    still_rows: list[dict[str, Any]] = []
    for row in selected:
        video_path = Path(str(row["output_path"]))
        duration = float(row["duration_in_frames"]) / float(row["fps"])
        for phase in phases:
            still_path = review_dir / f"{row['beat_id']}_phase_{phase:.2f}.jpg"
            subprocess.run(
                [
                    ffmpeg, "-y", "-v", "error", "-ss", f"{duration * phase:.6f}",
                    "-i", str(video_path), "-frames:v", "1", "-q:v", "2",
                    str(still_path),
                ],
                check=True,
                timeout=180,
            )
            still_rows.append({
                "shot_id": row["beat_id"],
                "phase": phase,
                "path": str(still_path.resolve()),
                "sha256": sha256_file(still_path),
            })
    sheet_path = review_dir / "selective_revision_contact_sheet.jpg"
    concat_path = review_dir / "selective_revision.ffconcat"
    concat_path.write_text(
        "\n".join(f"file '{Path(row['path']).as_posix()}'" for row in still_rows) + "\n",
        encoding="utf-8",
    )
    plan = variant_plans[str(selected[0]["variant_id"])]
    scale = "360:640" if plan.height > plan.width else "640:360"
    tile = f"{min(3, len(still_rows))}x{(len(still_rows) + 2) // 3}"
    subprocess.run(
        [
            ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0",
            "-i", str(concat_path), "-vf",
            f"scale={scale}:force_original_aspect_ratio=decrease,"
            f"pad={scale}:x=(ow-iw)/2:y=(oh-ih)/2,tile={tile}",
            "-frames:v", "1", "-q:v", "2", str(sheet_path),
        ],
        check=True,
        timeout=180,
    )
    result = {
        "schema_version": "contentops.retention_native.selective_revision_preview.v2",
        "status": "PASS",
        "shot_ids": list(exact_ids),
        "sample_phases": list(phases),
        "renderer_source_fingerprint": renderer_manifest["renderer_source_fingerprint"],
        "render_receipt": render_receipt,
        "stills": still_rows,
        "contact_sheet": {
            "path": str(sheet_path.resolve()),
            "sha256": sha256_file(sheet_path),
        },
        "asset_network_calls": asset_network_calls,
        "captions_visible": captions_visible,
        "public_write": False,
        "uploads": 0,
        "browser_profile_used": False,
    }
    receipt_path = output_root / "selective_revision_preview_receipt_v2.json"
    receipt_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--director-source", type=Path, required=True)
    parser.add_argument("--renderer-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--shot-id", action="append", required=True)
    parser.add_argument("--sample-phase", action="append", type=float)
    parser.add_argument("--captions-visible", action="store_true")
    args = parser.parse_args(argv)
    result = run_selective_preview(
        input_dir=args.input_dir.resolve(),
        director_source=args.director_source.resolve(),
        renderer_root=args.renderer_root.resolve(),
        output_root=args.output_root.resolve(),
        shot_ids=args.shot_id,
        sample_phases=args.sample_phase or (0.2, 0.5, 0.8),
        captions_visible=args.captions_visible,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
