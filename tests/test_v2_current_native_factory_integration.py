import json
import shutil
import subprocess

import pytest

from video.freeform_chapter_pipeline_v1 import pipeline
from video.unattended_core_factory_v1.store import V2JobStore
from video.unattended_core_factory_v1.desktop_session import (
    ParentSessionProvenance,
    build_parent_session_receipt,
)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg runtime unavailable")
def test_final_mux_preserves_all_picture_frames_with_short_audio(tmp_path):
    from video.unattended_core_factory_v1.media import mux_final_media
    from video.locale_activation_hardening_v1.factory import inspect_picture

    picture, audio, output = (
        tmp_path / "picture.mp4",
        tmp_path / "short.wav",
        tmp_path / "final.mp4",
    )
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=160x284:r=30:d=2",
            "-an",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(picture),
        ],
        check=True,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=1.9",
            str(audio),
        ],
        check=True,
    )
    receipt = mux_final_media(picture=picture, mix=audio, output=output)
    before, after = inspect_picture(picture), inspect_picture(output)
    assert before["frame_count"] == after["frame_count"] == 60
    assert before["video_stream_sha256"] == after["video_stream_sha256"]
    assert receipt["ffmpeg_shortest_used"] is False


def test_exact_job_claim_does_not_take_another_story(tmp_path):
    store = V2JobStore(tmp_path / "jobs.sqlite3")
    for job, digest in (("first", "a"), ("requested", "b")):
        store.seed_job(
            video_job_id=job,
            input_packet_path=tmp_path / (job + ".json"),
            input_packet_hash=digest * 64,
            target_format="SHORT",
        )
    actual = store.claim_next(
        worker_id="test", implementation_head="c" * 40, video_job_id="requested"
    )
    assert actual["video_job_id"] == "requested"
    assert store.job("first")["state"] == "QUEUED"


def test_reopen_and_duplicate_admission_preserve_job_and_run(tmp_path):
    path = tmp_path / "jobs.sqlite3"
    store = V2JobStore(path)
    spec = dict(
        input_packet_path=tmp_path / "packet.json",
        input_packet_hash="b" * 64,
        target_format="SHORT",
    )
    store.seed_job(video_job_id="original", **spec)
    run = store.claim_next(worker_id="test", implementation_head="c" * 40)
    store.release_claim(video_job_id="original", worker_id="test")
    reopened = V2JobStore(path)
    assert (
        reopened.seed_job(video_job_id="duplicate", **spec)["video_job_id"]
        == "original"
    )
    resumed = reopened.claim_next(worker_id="test", implementation_head="c" * 40)
    assert resumed["run_id"] == run["run_id"]
    assert len(reopened.jobs()) == 1
    assert resumed["public_write_authority"] == 0


def test_shared_render_cache_reuse_drift_and_changed_input(tmp_path, monkeypatch):
    source = tmp_path / "Short.tsx"
    source.write_text("first")
    output = tmp_path / "picture.mp4"
    calls = []

    def render(*args):
        calls.append(args)
        output.write_bytes(b"test media fixture")
        return {"wall_seconds": 1.0}

    monkeypatch.setattr(pipeline, "_run", render)
    spec = dict(
        command=["fixture"],
        cwd=tmp_path,
        output=output,
        source_files=[source],
        identity={"crf": 26},
    )
    assert not pipeline.render_native_project(**spec)["reused"]
    assert pipeline.render_native_project(**spec)["reused"]
    assert len(calls) == 1
    source.write_text("changed")
    with pytest.raises(pipeline.PipelineError, match="input changed"):
        pipeline.render_native_project(**spec)
    source.write_text("first")
    output.write_bytes(b"drift")
    with pytest.raises(pipeline.PipelineError, match="picture drift"):
        pipeline.render_native_project(**spec)


def test_unsealed_picture_is_not_adopted(tmp_path):
    source = tmp_path / "Short.tsx"
    source.write_text("source")
    output = tmp_path / "picture.mp4"
    output.write_bytes(b"unsealed")
    with pytest.raises(pipeline.PipelineError, match="reconciliation"):
        pipeline.render_native_project(
            command=["unused"],
            cwd=tmp_path,
            output=output,
            source_files=[source],
            identity={},
        )


def test_picture_dependencies_exclude_unreferenced_audio_and_story_assets(tmp_path):
    from video.unattended_core_factory_v1.media import picture_dependencies

    project, public, deps = tmp_path / "project", tmp_path / "public", tmp_path / "deps"
    (project / "src").mkdir(parents=True)
    (public / "assets").mkdir(parents=True)
    (project / "src/Short.tsx").write_text("staticFile('assets/selected.jpg')")
    for name in ["selected.jpg", "unrelated.jpg", "separate_audio.wav"]:
        (public / "assets" / name).write_bytes(name.encode())
    selected = picture_dependencies(project, public, deps)
    assert public / "assets/selected.jpg" in selected
    assert public / "assets/unrelated.jpg" not in selected
    assert public / "assets/separate_audio.wav" not in selected
    assert project / "tsconfig.json" in selected
    (project / "src/Short.tsx").write_text("staticFile('../../outside.jpg')")
    with pytest.raises(RuntimeError, match="escape"):
        picture_dependencies(project, public, deps)


def test_requested_parent_role_does_not_attest_actual_runtime():
    receipt = build_parent_session_receipt(
        provenance=ParentSessionProvenance("test"), video_job_id="job", run_id="run"
    )
    assert receipt["observed_runtime_model"] is None
    assert receipt["observed_runtime_reasoning_effort"] is None
    assert receipt["public_write_authority"] is False


def test_caption_revision_changes_package_preserves_media_and_rejects_drift(tmp_path):
    from video.unattended_core_factory_v1.caption_revision import revise_caption_layout
    from video.freeform_chapter_pipeline_v1.package_factory import (
        build_publication_package,
        write_caption_artifacts,
    )

    # Artifact bytes are explicit fixtures; this checks package closure, not media QA.
    picture, audio = tmp_path / "picture.mp4", tmp_path / "audio.wav"
    picture.write_bytes(b"picture fixture")
    audio.write_bytes(b"audio fixture")
    text = "These caption words must remain exactly bound to the spoken transcript across every whitespace layout revision."
    cues = {
        "schema": "contentops.v2.timed_captions.v1",
        "language": "en",
        "media_duration_seconds": 10,
        "cues": [{"cue_id": "one", "start_seconds": 0, "end_seconds": 9, "text": text}],
    }
    captions = write_caption_artifacts(cues, tmp_path / "original-captions")
    spec = dict(
        source_story_id="fixture",
        source_film_id="fixture",
        format="SHORT_9_16",
        language="en",
        canonical_picture=str(picture),
        audio=str(audio),
        burned_caption_video=None,
        **{"caption_" + k: v["path"] for k, v in captions.items()},
        metadata={"title": "Fixture", "description": "Explicit unit fixture"},
        rights_provenance_refs=["fixture"],
        factual_evidence_refs=["fixture"],
        delivery_policy={
            "picture_render_scope": "ONCE_PER_EDITORIAL_FORMAT",
            "locale_picture_render_default": False,
            "burned_captions": "OPTIONAL_ONLY_EXACT_AUTHORITY_REQUIRED",
            "recurring_locale_creative_xhigh": False,
        },
        hard_boundaries={
            "video_public_write_authority": False,
            "v1_mutation_authority": False,
            "scheduler_mutation_authority": False,
            "allow_4k": False,
        },
    )
    package = build_publication_package(spec)
    manifest = tmp_path / "original.json"
    manifest.write_text(json.dumps(package))
    receipt = revise_caption_layout(manifest, tmp_path / "revision")
    revised = json.loads((tmp_path / "revision/captions/captions.en.json").read_text())
    assert revised["cues"][0]["text"].split() == text.split()
    assert revised["cues"][0]["end_seconds"] == 9
    assert receipt["parent_package_id"] != receipt["package_id"]
    assert (
        receipt["picture_sha256"] == package["artifacts"]["canonical_picture"]["sha256"]
    )
    assert receipt["audio_sha256"] == package["artifacts"]["audio"]["sha256"]
    assert receipt["caption_sha256_before"] != receipt["caption_sha256_after"]
    assert receipt["picture_render_count"] == receipt["audio_synthesis_count"] == 0
    with pytest.raises(ValueError, match="distinct"):
        revise_caption_layout(manifest, tmp_path / "revision")
    audio.write_bytes(b"drift")
    with pytest.raises(ValueError, match="drift"):
        revise_caption_layout(manifest, tmp_path / "second")
