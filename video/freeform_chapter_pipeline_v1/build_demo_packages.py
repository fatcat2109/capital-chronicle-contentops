"""Build the Frozen Without Breaking platform-neutral publication packages.

The command binds already-produced media. It performs no rendering, synthesis, platform
authentication, scheduling, or public write.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

try:
    from .package_factory import ArtifactIdentity, build_publication_package
except ImportError:  # direct script execution
    from package_factory import ArtifactIdentity, build_publication_package


LOCALES = ("en", "es", "pt-BR", "ja")
CHAPTER_STARTS = (0.0, 120.5, 240.966667, 369.833333, 473.933333, 582.066667, 688.433333)
BOUNDARIES = {
    "video_public_write_authority": False,
    "v1_mutation_authority": False,
    "scheduler_mutation_authority": False,
    "allow_4k": False,
}


def _artifact_ref(path: Path) -> str:
    artifact = ArtifactIdentity.from_path(path)
    return f"sha256:{artifact.sha256}:{artifact.path}"


def _metadata(editorial: dict[str, Any], format_name: str) -> dict[str, Any]:
    payload = editorial[format_name]
    return {
        "title": payload["title"],
        "description": payload["description"],
        "social_copy": payload["social_copy"],
        "hashtags": payload.get("hashtags", []),
    }


def build_demo_packages(
    *,
    runtime_root: Path,
    locale_dir: Path,
    accepted_longform_master: Path,
    source_root: Path,
    generation_timestamp_utc: str,
) -> dict[str, Any]:
    packages_root = runtime_root / "packages"
    metadata_root = runtime_root / "metadata"
    packages_root.mkdir(parents=True, exist_ok=True)
    metadata_root.mkdir(parents=True, exist_ok=True)

    rights_refs = [
        _artifact_ref(source_root / "SOURCES.md"),
        _artifact_ref(source_root / "AUTHORITY_CLIPS.md"),
    ]
    evidence_refs = [
        _artifact_ref(source_root / "FINAL_NARRATION.md"),
        _artifact_ref(source_root / "CHAPTERS.md"),
    ]
    owner_root = runtime_root / "renders" / "owner_review"
    package_index: list[dict[str, Any]] = []
    metadata_index: dict[str, Any] = {}

    for locale in LOCALES:
        editorial_path = locale_dir / f"{locale}.json"
        editorial = json.loads(editorial_path.read_text(encoding="utf-8"))
        factual_refs = [*evidence_refs, _artifact_ref(editorial_path)]
        voice_sample = ArtifactIdentity.from_path(runtime_root / "audio" / locale / "voice_sample.wav")

        for format_name, format_kind in (("short", "SHORT_9_16"), ("longform", "LONGFORM_16_9")):
            metadata = _metadata(editorial, format_name)
            metadata_path = metadata_root / f"{format_name}.{locale}.json"
            metadata_path.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            metadata_index[f"{format_name}_{locale}"] = asdict(
                ArtifactIdentity.from_path(metadata_path)
            )

            if format_name == "short":
                clean_video = owner_root / f"Frozen_Without_Breaking_short_{locale}_clean.mp4"
                burned = (
                    owner_root / f"Frozen_Without_Breaking_short_{locale}_burned.mp4"
                    if locale != "en"
                    else None
                )
                audio_root = runtime_root / "audio" / locale / "short"
                audio = audio_root / "narration.wav"
                chapters: list[dict[str, Any]] = []
                surfaces = ["YOUTUBE_SHORTS", "TIKTOK", "INSTAGRAM_REELS"]
            else:
                clean_video = (
                    owner_root / "Frozen_Without_Breaking_es_1080p_master.mp4"
                    if locale == "es"
                    else accepted_longform_master
                )
                burned = None
                audio_root = runtime_root / "audio" / locale / "longform"
                audio = audio_root / "premaster.wav"
                chapter_titles = list(editorial["longform"]["chapter_titles"].values())
                chapters = [
                    {"start_seconds": start, "title": title}
                    for start, title in zip(CHAPTER_STARTS, chapter_titles, strict=True)
                ]
                surfaces = ["YOUTUBE_NORMAL_VIDEO"]

            caption_root = audio_root / "captions"
            spec = {
                "source_story_id": "frozen_without_breaking",
                "source_film_id": "frozen_without_breaking_owner_polish_v1",
                "format": format_kind,
                "language": locale,
                "clean_video": str(clean_video),
                "burned_caption_video": str(burned) if burned else None,
                "audio": str(audio),
                "caption_json": str(caption_root / f"captions.{locale}.json"),
                "caption_srt": str(caption_root / f"captions.{locale}.srt"),
                "caption_vtt": str(caption_root / f"captions.{locale}.vtt"),
                "metadata": metadata,
                "chapters": chapters,
                "rights_provenance_refs": rights_refs,
                "factual_evidence_refs": factual_refs,
                "intended_future_surfaces": surfaces,
                "generation_version": "native_multiformat_multilingual_factory_v1",
                "generation_timestamp_utc": generation_timestamp_utc,
                "hard_boundaries": BOUNDARIES,
            }
            package = build_publication_package(spec)
            package_path = packages_root / f"{format_name}.{locale}.{package['package_id']}.json"
            package_path.write_text(
                json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            package_index.append(
                {
                    "format": format_name,
                    "language": locale,
                    "package_id": package["package_id"],
                    "manifest": asdict(ArtifactIdentity.from_path(package_path)),
                    "metadata": metadata_index[f"{format_name}_{locale}"],
                    "voice_sample": asdict(voice_sample),
                    "human_voice_gate": "JIM_LISTENING_GATE_REQUIRED",
                }
            )

    return {
        "schema": "contentops.v2.fwb_platform_neutral_package_index.v1",
        "result": "PASS_CONTENT_ADDRESSED_PACKAGES",
        "package_count": len(package_index),
        "packages": package_index,
        "metadata": metadata_index,
        "hard_boundaries": BOUNDARIES,
        "publication_state": "PACKAGE_ONLY_ZERO_PUBLIC_WRITE",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", required=True, type=Path)
    parser.add_argument("--locale-dir", required=True, type=Path)
    parser.add_argument("--accepted-longform-master", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--generation-timestamp-utc", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = build_demo_packages(
        runtime_root=args.runtime_root.resolve(),
        locale_dir=args.locale_dir.resolve(),
        accepted_longform_master=args.accepted_longform_master.resolve(),
        source_root=args.source_root.resolve(),
        generation_timestamp_utc=args.generation_timestamp_utc,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
