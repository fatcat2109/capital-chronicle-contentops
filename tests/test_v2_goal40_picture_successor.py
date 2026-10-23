import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from video.unattended_core_factory_v1 import caption_revision
from video.unattended_core_factory_v1.media import artifact
from video.unattended_core_factory_v1.store import V2JobStore
from video.unattended_core_factory_v1.supervisor import (
    DesktopSessionV2Factory,
    SupervisorError,
)


def test_native_picture_normalization_preserves_display_and_records_equivalent_css():
    from hashlib import sha256
    from video.unattended_core_factory_v1.creative import (
        SOURCE_FILES,
        ACTUAL_MEDIA_REVIEW_CHECKS,
    )

    files = {
        k: 'const display = "17 AUGUST 2026"; const style = {padding: "46px 48px"};'
        for k in SOURCE_FILES
    }
    native = dict(
        schema="contentops.v2.codex_final_picture_correction.v1",
        decision="REPLACE_SOURCE_FILES",
        source_files=files,
        source_file_sha256={
            k: sha256(v.encode()).hexdigest() for k, v in files.items()
        },
        preserved_contract={
            k: False
            for k in [
                "sequence_timing_changed",
                "narration_changed",
                "timing_lock_changed",
                "voice_changed",
                "story_values_changed",
                "story_text_changed",
                "source_claim_bindings_changed",
                "asset_ids_changed",
            ]
        },
        findings=[dict(observed="credits overlap")],
        inspected={},
        limits=dict(hearing="NOT_VERIFIED"),
    )
    prior = dict(
        artifact=dict(
            review_checks={k: "prior proxy only" for k in ACTUAL_MEDIA_REVIEW_CHECKS}
        )
    )
    mapped, receipt = caption_revision.normalize_final_picture_correction(
        native, dict(source_claim_bindings=[]), prior
    )
    assert native["source_files"] == files
    for source in mapped["replacement_files"].values():
        assert '"17 AUGUST 2026"' in source
        assert "paddingTop: 46" in source and "paddingRight: 48" in source
    assert receipt["display_text_changed"] is False
    assert receipt["final_review_promoted"] is False
    assert all(
        v.startswith("RETAINED_PRIOR_PROXY_REVIEW_ONLY")
        for v in mapped["review_checks"].values()
    )
    native["source_files"]["src/Short.tsx"] += "changed"
    with pytest.raises(ValueError, match="source seal drift"):
        caption_revision.normalize_final_picture_correction(
            native, dict(source_claim_bindings=[]), prior
        )


def test_picture_successor_keeps_one_run_reuses_audio_and_deduplicates(
    tmp_path, monkeypatch
):
    root = tmp_path / "runtime/jobs/story"
    root.mkdir(parents=True)
    source = root / "source.json"
    source.write_text(
        json.dumps(
            dict(
                schema="contentops.v2.platform_neutral_publication_package.v1",
                artifacts={},
            )
        )
    )
    base = root / "base.json"
    base.write_text("{}")
    f = object.__new__(DesktopSessionV2Factory)
    f.store = V2JobStore(tmp_path / "jobs.sqlite3")
    f.config = SimpleNamespace(
        dependency_root=tmp_path, scaffold_root=tmp_path, asset_root=tmp_path
    )
    f.store.seed_job(
        video_job_id="story",
        input_packet_path=base,
        input_packet_hash="a" * 64,
        target_format="SHORT",
    )
    job = f.store.claim_next(worker_id="test", implementation_head="b" * 40)
    f.store.release_claim(video_job_id="story", worker_id="test")

    def event(stage, files, state=None):
        f.store.append_event(
            video_job_id="story",
            run_id=job["run_id"],
            stage=stage,
            input_hashes={},
            output_hashes={},
            artifacts=[artifact(p) for p in files],
            role_tool_identity="fixture",
            model_provenance={},
            wall_time_seconds=0,
            safe_usage={},
            result="PASS_FIXTURE",
            retry_state={},
            next_legal_stage=None,
            state_pointer=state,
        )

    event("AUDIO_BUILT", [base])
    event("PACKAGE_QA_PASSED", [source])
    event("OWNER_REVIEW_READY", [base], "OWNER_REVIEW_READY")
    f._paths = lambda _: dict(root=root, editor=base, motion=base, timing_lock=base)
    request = root / "request.json"
    request.write_text(json.dumps(dict(video_job_id="story", run_id=job["run_id"])))
    returned = root / "return.json"
    returned.write_text("{}")
    calls = []

    def build(**kwargs):
        calls.append(kwargs)
        out = kwargs["output_dir"]
        for name in ["picture_lock.mp4", "clean.mp4", "technical.json"]:
            (out / name).write_bytes(b"explicit media fixture")
        manifest = out / "manifest.json"
        manifest.write_text(source.read_text())
        result = dict(
            result="PRIVATE_NATIVE_PICTURE_PACKAGE_BUILT", manifest=str(manifest)
        )
        (out / "revision_receipt.json").write_text(json.dumps(result))
        return result

    monkeypatch.setattr(caption_revision, "build_private_picture_revision", build)
    spec = dict(
        video_job_id="story",
        revision="picture-correction",
        request_path=request,
        return_path=returned,
    )
    f.revise_private_picture_package(**spec)
    before = len(f.store.events("story"))
    assert f.revise_private_picture_package(**spec)["idempotent_replay"]
    assert len(calls) == 1
    assert len(f.store.events("story")) == before
    assert len(f.store.jobs()) == 1
    assert f.store.job("story")["run_id"] == job["run_id"]
    assert f.store.job("story")["state"] == "OWNER_REVIEW_READY"
    assert (
        f.store.latest_success_by_stage("story")["AUDIO_BUILT"]["role_tool_identity"]
        == "fixture"
    )
    assert not any(
        e["stage"] == "AUDIO_BUILT" and e["result"].startswith("INVALIDATED")
        for e in f.store.events("story")
    )
    returned.write_text("changed return")
    with pytest.raises(SupervisorError, match="source_binding_drift"):
        f.revise_private_picture_package(**spec)


def test_picture_revision_rejects_source_artifact_drift_before_render(
    tmp_path, monkeypatch
):
    picture = tmp_path / "picture.mp4"
    picture.write_bytes(b"original")
    package = tmp_path / "package.json"
    package.write_text(
        json.dumps(dict(artifacts=dict(canonical_picture=artifact(picture))))
    )
    picture.write_bytes(b"drift")
    with pytest.raises(ValueError, match="source package drift"):
        caption_revision.build_private_picture_revision(
            package_path=package,
            request_path=Path("unused"),
            return_path=Path("unused"),
            input_packet={},
            editor={},
            motion={},
            timing_lock={},
            dependency_root=tmp_path,
            scaffold_root=tmp_path,
            asset_root=tmp_path,
            output_dir=tmp_path / "output",
        )
    assert not (tmp_path / "output").exists()
