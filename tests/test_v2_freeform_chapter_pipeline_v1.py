from __future__ import annotations

import json
from pathlib import Path

import pytest

from video.freeform_chapter_pipeline_v1.pipeline import (
    FreeformChapterPipeline,
    PipelineError,
)


REPO = Path(__file__).resolve().parents[1]
MANIFEST = (
    REPO
    / "video"
    / "freeform_chapter_pipeline_v1"
    / "frozen_without_breaking.manifest.json"
)


def test_frozen_manifest_enforces_owner_hard_contract() -> None:
    result = FreeformChapterPipeline(MANIFEST).validate()

    assert result["result"] == "PASS_HARD_CONTRACT"
    assert result["duration_seconds"] >= 300
    assert result["duration_seconds"] <= 2700
    assert result["public_write_authority"] is False
    assert result["v1_mutation_authority"] is False
    assert result["allow_4k"] is False


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        (("format_contract", "width"), 3840, "1920x1080"),
        (("format_contract", "duration_seconds"), 299, "5:00-45:00"),
        (("model_orchestration", "parent"), "gpt-5.6-sol/ultra", "HIGH"),
        (("model_orchestration", "creative_workers"), "gpt-5.6-sol/high", "XHIGH"),
        (("hard_boundaries", "video_public_write_authority"), True, "ZERO_VIDEO_PUBLIC_WRITE"),
        (("hard_boundaries", "allow_4k"), True, "4K"),
    ],
)
def test_owner_hard_contract_rejects_forbidden_mutations(
    tmp_path: Path, path: tuple[str, str], value: object, message: str
) -> None:
    repo = tmp_path / "repo"
    manifest_dir = repo / "video" / "freeform_chapter_pipeline_v1"
    project = repo / "video" / "projects" / "frozen_without_breaking_v1"
    manifest_dir.mkdir(parents=True)
    project.mkdir(parents=True)
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data[path[0]][path[1]] = value
    data["chapters"] = []
    data["format_contract"]["duration_seconds"] = (
        value if path == ("format_contract", "duration_seconds") else 300
    )
    (project / "src").mkdir()
    (project / "src" / "index.ts").write_text("export {};\n", encoding="utf-8")
    manifest_path = manifest_dir / "film.json"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(PipelineError, match=message):
        FreeformChapterPipeline(manifest_path).validate()


def test_dirty_range_command_is_local_picture_only_1080_or_720() -> None:
    pipeline = FreeformChapterPipeline(MANIFEST)
    result = pipeline.render_range(
        "Chapter04",
        1200,
        1410,
        REPO / ".task-runtime" / "test-range.mp4",
        profile="fast",
        concurrency=4,
        dry_run=True,
    )

    command = result["command"]
    assert result["kind"] == "dirty_range"
    assert result["frames"] == [1200, 1410]
    assert "--frames" in command
    assert "1200-1410" in command
    assert "--muted" in command
    assert "1280" in command and "720" in command
    assert "3840" not in command and "2160" not in command
    assert not any("generate_narration" in item for item in command)


def test_dirty_range_can_reuse_one_prepared_bundle() -> None:
    pipeline = FreeformChapterPipeline(MANIFEST)
    bundle = REPO / ".task-runtime" / "prepared-bundle"
    result = pipeline.render_range(
        "Chapter02",
        0,
        30,
        REPO / ".task-runtime" / "bundle-range.mp4",
        bundle=bundle,
        dry_run=True,
    )

    command = result["command"]
    assert str(bundle.resolve()) in command
    assert pipeline.manifest["entry"] not in command
    assert "--frames" in command
    assert "--muted" in command


def test_hardware_review_profile_requires_nvenc_without_crf() -> None:
    pipeline = FreeformChapterPipeline(MANIFEST)
    result = pipeline.render_range(
        "Chapter02",
        0,
        30,
        REPO / ".task-runtime" / "hardware-range.mp4",
        profile="fast-hw",
        dry_run=True,
    )

    command = result["command"]
    assert command[command.index("--hardware-acceleration") + 1] == "required"
    assert "--crf" not in command
    assert "1280" in command and "720" in command


def test_video_only_chapter_render_never_regenerates_audio() -> None:
    pipeline = FreeformChapterPipeline(MANIFEST)
    result = pipeline.render_chapter("Chapter05", dry_run=True, force=True)

    assert result["kind"] == "chapter_lock"
    assert "--muted" in result["command"]
    assert all("python" not in item.lower() for item in result["command"])
    assert all("audio" not in item.lower() for item in result["command"])


def test_audio_only_build_never_invokes_remotion(tmp_path: Path) -> None:
    stem = tmp_path / "narration.wav"
    stem.write_bytes(b"placeholder")
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "duration_seconds": 12,
                "stems": [
                    {
                        "path": str(stem),
                        "timeline_start_seconds": 0,
                        "duration_seconds": 12,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = FreeformChapterPipeline(MANIFEST).mix_audio(
        plan, tmp_path / "mix.wav", dry_run=True
    )

    assert result["kind"] == "audio_only_build"
    assert result["video_render_invoked"] is False
    assert result["command"][0] == "ffmpeg"
    assert not any("remotion" in item.lower() for item in result["command"])


def test_chapter_cache_identity_changes_with_creative_source(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    manifest_dir = repo / "video" / "freeform_chapter_pipeline_v1"
    project = repo / "video" / "projects" / "film"
    manifest_dir.mkdir(parents=True)
    (project / "src").mkdir(parents=True)
    (project / "public").mkdir()
    (project / "src" / "index.ts").write_text("export {};\n", encoding="utf-8")
    creative = project / "src" / "Chapter.tsx"
    creative.write_text("export const Chapter = 1;\n", encoding="utf-8")
    asset = project / "public" / "asset.bin"
    asset.write_bytes(b"asset-v1")
    (project / "package-lock.json").write_text("{}\n", encoding="utf-8")
    manifest = {
        "schema": "contentops.v2.freeform_chapter_film.v1",
        "project_root": "video/projects/film",
        "entry": "src/index.ts",
        "format_contract": {
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "duration_seconds": 300,
            "color": "bt709_limited_yuv420p",
        },
        "model_orchestration": {
            "parent": "gpt-5.6-sol/high",
            "creative_workers": "gpt-5.6-sol/xhigh",
            "forbidden_modes": ["max", "ultra"],
        },
        "hard_boundaries": {
            "video_public_write_authority": False,
            "v1_mutation_authority": False,
            "allow_4k": False,
        },
        "shared_source_files": ["src/index.ts"],
        "chapters": [
            {
                "id": "Chapter",
                "composition": "Chapter",
                "duration_frames": 9000,
                "source_files": ["src/Chapter.tsx"],
                "asset_files": ["public/asset.bin"],
            }
        ],
    }
    manifest_path = manifest_dir / "film.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    pipeline = FreeformChapterPipeline(manifest_path)
    before = pipeline.chapter_cache_key("Chapter")

    creative.write_text("export const Chapter = 2;\n", encoding="utf-8")
    after_source = pipeline.chapter_cache_key("Chapter")
    asset.write_bytes(b"asset-v2")
    after_asset = pipeline.chapter_cache_key("Chapter")

    assert before != after_source
    assert after_source != after_asset


def test_new_path_does_not_import_fixed_professional_compositor() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPO / "video" / "projects" / "frozen_without_breaking_v1" / "src").rglob("*.tsx")
    )

    assert "architectureProof" not in source
    assert "SceneRenderer" not in source
    assert "layout enum" not in source.lower()
