"""Explicit retained-source engineering probe through current media owners.

This is a bounded evidence command, not a native return, scheduler, alternate
factory, current-news qualification, or fresh creative execution.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from video.unattended_core_factory_v1 import media
from video.unattended_core_factory_v1.caption_revision import revise_caption_layout
from video.unattended_core_factory_v1.creative import (
    hash_file,
    hash_value,
    materialize_source,
    validate_editor_artifact,
    validate_motion_artifact,
    validate_narration_timing_lock,
    CreativeContractError,
)
from video.unattended_core_factory_v1.transcript import build_transcript_derived_seo


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=["prepare", "render", "package", "reuse"])
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = load(args.config)
    repo = Path(__file__).resolve().parents[4]
    root = repo / ".task-runtime/goal39/retained-media"
    # One explicitly permitted dated retained case; no discovery or mutable V1 reads.
    retained = Path(
        "A:/Capital Chronicle/ContentOps-wt-v2-winlaunch/.task-runtime/v2-windows-process-launch-geometry-owner-override-recovery-v1"
    )
    old = retained / "jobs/v2_recovery2_us_retail_july_2026"
    source_paths = {
        "packet": retained / "inputs/us_retail_july_2026.json",
        "editor": old / "artifacts/creative_editor.json",
        "motion": old / "artifacts/motion_source.json",
        "timing": old / "artifacts/actual_narration_timing_lock.json",
    }
    packet, editor, motion, timing = (
        load(source_paths[k]) for k in ("packet", "editor", "motion", "timing")
    )
    project = root / "project"
    picture = root / "picture.mp4"
    final = root / "retained-current-media.mp4"
    root.mkdir(parents=True, exist_ok=True)
    if args.phase == "prepare":
        if (root / "admission.json").exists():
            raise ValueError("Probe admission already exists; use saved stages")
        try:
            timing_check = validate_narration_timing_lock(
                timing,
                video_job_id=timing["video_job_id"],
                run_id=timing["run_id"],
                governed_input_hash=hash_value(packet),
                editor=editor,
            )
        except CreativeContractError as exc:
            # Preserve historical bytes. This technical replay cannot satisfy the
            # current factory's audio/transcript gate and never enters its jobs.
            timing_check = {
                "result": "HOLD_RETAINED_TRANSCRIPT_CURRENT_CONTRACT",
                "reason": str(exc),
            }
        checks = {
            "editor": validate_editor_artifact(editor, packet),
            "timing": timing_check,
            "motion": validate_motion_artifact(motion, packet, editor, timing),
        }
        assets = dict(
            packet,
            rights_assets=packet["rights_assets"]
            + motion["asset_selection"]["selected_assets"],
        )
        checks["assets"] = media.validate_assets(assets, Path(config["asset_root"]))
        checks["scaffold"] = media.prepare_project(
            project_root=project,
            scaffold_root=Path(config["scaffold_root"]),
            dependency_root=Path(config["dependency_root"]),
            asset_root=Path(config["asset_root"]),
        )
        materialize_source(motion["files"], project)
        checks["typecheck"] = media.typecheck_project(
            project, Path(config["dependency_root"])
        )
        save(
            root / "admission.json",
            {
                "classification": "DATED_RETAINED_CREATIVE_AND_WAVEFORM_REPLAY_CURRENT_MEDIA_OWNERS",
                "current_factory_acceptance": "NOT_ESTABLISHED_TECHNICAL_REPLAY_ONLY",
                "source_bindings": {
                    k: {"path": str(v), "sha256": hash_file(v)}
                    for k, v in source_paths.items()
                },
                "fresh_native_creative_count": 0,
                "fresh_source_crawl_count": 0,
                "historical_discovery_fields_scope": "RETAINED_ONLY_NOT_PERFORMED_IN_GOAL39",
                "checks": checks,
                "public_write_authority": False,
            },
        )
        print("Retained source admitted; no fresh creativity claimed")
        return
    admission = load(root / "admission.json")
    for spec in admission["source_bindings"].values():
        if hash_file(spec["path"]) != spec["sha256"]:
            raise ValueError("Retained source drift")
    if args.phase == "render":
        result = media.render_project(
            project_root=project,
            dependency_root=Path(config["dependency_root"]),
            output=picture,
            crf=26,
            browser_executable=media.resolve_remotion_browser_executable(
                Path(config["dependency_root"])
            ),
            public_root=Path(config["asset_root"]),
        )
        save(root / "current_render.json", result)
        save(
            root / "contact_sheet.json",
            media.contact_sheet(picture, root / "contact_sheet.jpg"),
        )
        print(
            json.dumps(
                {
                    k: result[k]
                    for k in ("result", "reused", "wall_seconds", "output_sha256")
                }
            )
        )
    elif args.phase == "package":
        if (root / "package/manifest.json").exists():
            raise ValueError("Sealed probe package already exists")
        mix = media.build_audio_mix(
            picture=picture,
            timing_lock=timing,
            bed_path=Path(config["asset_root"])
            / "assets/audio/sound/chapter_02_bed.m4a",
            output_dir=root / "audio",
        )
        mux = media.mux_final_media(
            picture=picture, mix=Path(mix["mix"]["path"]), output=final
        )
        captions = media.build_captions(
            timing_lock=timing,
            media_duration_seconds=motion["duration_seconds"],
            output_dir=root / "package/captions",
        )
        seo = build_transcript_derived_seo(
            transcript=timing["canonical_spoken_transcript"], editor=editor
        )
        assets = packet["rights_assets"] + motion["asset_selection"]["selected_assets"]
        package = media.build_neutral_package(
            story_id=packet["story_id"],
            run_id="goal39-retained-current-media",
            final_media=final,
            audio=Path(mix["mix"]["path"]),
            captions=captions,
            rights_refs=[a["sha256"] for a in assets],
            evidence_refs=[a["source_ref"] for a in packet["anchors"]],
            input_hash=hash_value(packet),
            timing_lock=timing,
            seo_package=seo,
            output=root / "package/manifest.json",
        )
        technical = media.technical_media_report(final, root / "technical.json")
        media.contact_sheet(final, root / "final_contact_sheet.jpg")
        save(
            root / "package_receipt.json",
            {
                "result": "RETAINED_CURRENT_MEDIA_PRIVATE_PACKAGE_BUILT",
                "classification": admission["classification"],
                "package_id": package["package_id"],
                "mix": mix["mix"],
                "mux": mux["final_media"],
                "technical": technical,
                "fresh_native_creative_count": 0,
                "new_picture_render_count": 1,
                "retained_narration_reused": True,
                "new_audio_mix_count": 1,
                "audio_hearing": "NOT_VERIFIED",
                "rights_release": "NOT_GRANTED",
                "final_av_acceptance": "NOT_GRANTED",
                "public_write_authority": False,
                "current_factory_acceptance": admission["current_factory_acceptance"],
                "current_transcript_gate": admission["checks"]["timing"],
            },
        )
        print(package["package_id"])
    else:
        print(
            json.dumps(
                revise_caption_layout(
                    root / "package/manifest.json", root / "caption-revision", width=32
                )
            )
        )


if __name__ == "__main__":
    main()
