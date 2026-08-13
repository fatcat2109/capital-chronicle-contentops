"""Preview-first visual runner for the retention-native V2 proof."""
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


def run_preview(
    *, input_dir: Path, director_source: Path, renderer_root: Path, output_root: Path
) -> dict[str, Any]:
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
    variants = {row.variant_id: row for row in bundle.platform_variant_plan.variants}
    narration: dict[str, dict[str, Any]] = {}
    for graph in bundle.beat_graphs:
        fps = variants[graph.variant_id].fps
        for beat in graph.beats:
            narration[beat.beat_id] = {
                "duration_in_frames": max(1, int(round(beat.target_duration_seconds * fps))),
                "sha256": "0" * 64,
            }
    jobs = _compile_jobs(
        bundle, narration=narration, assets=assets, output_root=output_root,
        renderer_source_fingerprint=str(renderer_manifest["renderer_source_fingerprint"]),
        proxy=True, captions_visible=False,
    )
    node = _find_binary("node", "CONTENTOPS_NODE_BINARY")
    ffmpeg = _find_binary("ffmpeg", "CONTENTOPS_FFMPEG_BINARY")
    ffprobe = _find_binary("ffprobe", "CONTENTOPS_FFPROBE_BINARY")
    receipts: dict[str, Any] = {}
    contact_sheets: dict[str, Any] = {}
    for graph in bundle.beat_graphs:
        candidates = jobs[graph.variant_id]
        payoff_ids = {beat.beat_id for beat in graph.beats if beat.payoff_for}
        indexes = {0, len(candidates) // 2, len(candidates) - 1}
        indexes.update(i for i, row in enumerate(candidates) if row["beat_id"] in payoff_ids)
        selected = [candidates[i] for i in sorted(indexes)]
        receipts[graph.variant_id] = _render_jobs(
            selected, renderer_root=renderer_root, public_dir=public_dir,
            output_root=output_root, node=node, ffprobe=ffprobe,
            receipt_name=f"preview_{graph.variant_id}",
        )
        stills: list[Path] = []
        for row in selected:
            output = Path(str(row["output_path"]))
            still = output_root / "review" / f"{graph.variant_id}_{row['beat_id']}.jpg"
            still.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [ffmpeg, "-y", "-v", "error", "-ss", str(row["duration_in_frames"] / row["fps"] / 2),
                 "-i", str(output), "-frames:v", "1", "-q:v", "2", str(still)],
                check=True, timeout=180,
            )
            stills.append(still)
        sheet = output_root / "review" / f"{graph.variant_id}_preview_contact_sheet.jpg"
        manifest = output_root / "review" / f"{graph.variant_id}_preview.ffconcat"
        manifest.write_text("\n".join(f"file '{p.as_posix()}'" for p in stills) + "\n", encoding="utf-8")
        tile = "2x2" if len(stills) <= 4 else "3x2"
        scale = "360:640" if variants[graph.variant_id].height > variants[graph.variant_id].width else "640:360"
        subprocess.run(
            [ffmpeg, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(manifest),
             "-vf", f"scale={scale}:force_original_aspect_ratio=decrease,pad={scale}:x=(ow-iw)/2:y=(oh-ih)/2,tile={tile}",
             "-frames:v", "1", "-q:v", "2", str(sheet)], check=True, timeout=180,
        )
        contact_sheets[graph.variant_id] = {
            "path": str(sheet.resolve()), "sha256": sha256_file(sheet),
            "shot_ids": [row["beat_id"] for row in selected],
        }
    result = {
        "schema_version": "contentops.retention_native.preview_first.v2",
        "status": "PASS",
        "renderer_source_fingerprint": renderer_manifest["renderer_source_fingerprint"],
        "contact_sheets": contact_sheets,
        "render_receipts": receipts,
        "asset_network_calls": asset_network_calls,
        "captions_visible": False,
        "public_write": False, "uploads": 0, "browser_profile_used": False,
    }
    path = output_root / "preview_first_receipt_v2.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--director-source", type=Path, required=True)
    parser.add_argument("--renderer-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(run_preview(
        input_dir=args.input_dir.resolve(), director_source=args.director_source.resolve(),
        renderer_root=args.renderer_root.resolve(), output_root=args.output_root.resolve(),
    ), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
