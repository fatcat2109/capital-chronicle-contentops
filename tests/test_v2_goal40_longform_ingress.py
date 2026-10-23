import json

import pytest

from video.freeform_chapter_pipeline_v1 import native_narrative
from video.freeform_chapter_pipeline_v1.pipeline import (
    FreeformChapterPipeline,
    PipelineError,
)
from video.unattended_core_factory_v1.creative import hash_file, hash_value


def fixture(tmp_path, monkeypatch, duration=410):
    root = tmp_path / "repo"
    root.mkdir()
    source = root / "source.txt"
    source.write_text("explicit primary-source fixture")
    request = {
        "kind": "LONGFORM_SOURCE_NARRATIVE",
        "bindings": {"source": {"path": str(source), "sha256": hash_file(source)}},
    }
    request_path = root / "request.json"
    request_path.write_text(json.dumps(request))
    artifact = dict(
        source_documents=[
            dict(
                saved_extract_path="source.txt", saved_extract_sha256=hash_file(source)
            )
        ],
        source_manifest=dict(path="source.txt", sha256=hash_file(source)),
        asset_registry=[],
        governed_fact_anchors=[dict(claim_id="GF01")],
        qualified_analysis=[dict(analysis_id="QA01")],
        current_news_claim=False,
        chapters=[
            dict(
                chapter_id="CH01",
                narration="A source-bound fixture.",
                claim_bindings=["GF01", "QA01"],
            )
        ],
    )
    returned = dict(
        kind=request["kind"],
        request_sha256=hash_value(request),
        requested_model="gpt-5.6-sol",
        requested_reasoning_effort="xhigh",
        provenance_limit="ASSIGNED_ROLE_NOT_INDEPENDENT_RUNTIME_ATTESTATION",
        native_task_id="/root/fixture",
        artifact=artifact,
    )
    return_path = root / "return.json"
    return_path.write_text(json.dumps(returned))
    calls = []

    def synthesize(**kwargs):
        calls.append(kwargs)
        return dict(duration_seconds=duration, placements=[], external_cost_usd=0)

    monkeypatch.setattr(native_narrative, "synthesize_narration", synthesize)
    spec = dict(
        request_path=request_path,
        return_path=return_path,
        repo_root=root,
        model_path=root / "model",
        voices_path=root / "voices",
        output_dir=root / "runtime",
    )
    return spec, calls


def test_longform_duration_uses_actual_audio_and_never_pads_short_script(
    tmp_path, monkeypatch
):
    spec, calls = fixture(tmp_path, monkeypatch, duration=41)
    result = native_narrative.lock_native_narrative(**spec)
    assert result["result"] == "HOLD_LONGFORM_DURATION_OUTSIDE_CONTRACT"
    assert result["picture_duration_seconds"] < 42
    assert calls[0]["editor"]["audio_intent"]["speed"] == 1.06
    assert result["narration_hearing"] == "NOT_VERIFIED"


def test_longform_rejects_source_drift_before_audio(tmp_path, monkeypatch):
    spec, calls = fixture(tmp_path, monkeypatch)
    (spec["repo_root"] / "source.txt").write_text("changed")
    with pytest.raises(ValueError, match="source bytes drift"):
        native_narrative.lock_native_narrative(**spec)
    assert calls == []


def test_current_runtime_manifest_resolves_explicit_repo_and_rejects_escape(tmp_path):
    repo = tmp_path / "repo"
    manifest = repo / ".task-runtime/current/film.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"project_root": ".task-runtime/current/project", "chapters": []})
    )
    owner = FreeformChapterPipeline(manifest, repo_root=repo)
    assert owner.project_root == repo / ".task-runtime/current/project"
    manifest.write_text(json.dumps({"project_root": "../other", "chapters": []}))
    with pytest.raises(PipelineError, match="Project root must remain"):
        FreeformChapterPipeline(manifest, repo_root=repo)


def chapter_fixture(tmp_path, monkeypatch):
    from video.unattended_core_factory_v1 import media

    repo = tmp_path / "repo"
    project = repo / ".task-runtime/project"
    (project / "src").mkdir(parents=True)
    source = project / "src/index.tsx"
    source.write_text("import React from 'react'; export const Film = () => null;")
    document = repo / "source.txt"
    document.write_text("immutable source fixture")
    snapshot = repo / "request-owner.py"
    snapshot.write_text("# exact original engineering snapshot\n")
    dependency = repo / "deps/node_modules"
    dependency.mkdir(parents=True)
    (dependency.parent / "package-lock.json").write_text("{}")
    request = dict(
        kind="LONGFORM_CHAPTER_MOTION",
        bindings={
            "source": dict(path=str(document), sha256=hash_file(document)),
            "existing_chapter_owner": dict(
                path=str(native_narrative.__file__).replace(
                    "native_narrative.py", "pipeline.py"
                ),
                sha256=hash_file(snapshot),
            ),
        },
    )
    request_path = repo / "request.json"
    request_path.write_text(json.dumps(request))
    returned = dict(
        kind="LONGFORM_CHAPTER_MOTION",
        request_sha256=hash_value(request),
        model="gpt-5.6-sol",
        reasoning_effort="xhigh",
        native_task_id="/root/fixture",
        provenance_limit="ASSIGNED_ROLE_NOT_INDEPENDENT_RUNTIME_ATTESTATION",
        artifact=dict(
            project_root=".task-runtime/project",
            source_files=["src/index.tsx"],
            source_file_seals=[dict(path="src/index.tsx", sha256=hash_file(source))],
            asset_byte_verification=[],
            chapter_manifest=dict(
                project_root=".task-runtime/project", entry="src/index.tsx", chapters=[]
            ),
        ),
    )
    return_path = repo / "return.json"
    return_path.write_text(json.dumps(returned))
    monkeypatch.setattr(media, "prepare_project", lambda **_: None)
    monkeypatch.setattr(media, "typecheck_project", lambda *_: dict(result="fixture"))
    monkeypatch.setattr(
        media, "resolve_remotion_browser_executable", lambda _: repo / "browser"
    )
    monkeypatch.setattr(
        FreeformChapterPipeline, "validate", lambda _: dict(result="fixture")
    )
    return dict(
        request_path=request_path,
        return_path=return_path,
        repo_root=repo,
        dependency_root=dependency,
        scaffold_root=repo / "scaffold",
        output_dir=repo / ".task-runtime/admitted",
        request_owner_snapshot=snapshot,
    )


def test_chapter_snapshot_preserves_original_and_records_current_execution_owner(
    tmp_path, monkeypatch
):
    spec = chapter_fixture(tmp_path, monkeypatch)
    receipt = native_narrative.admit_native_chapters(**spec)
    identity = receipt["identity"]
    assert identity["request_bindings"]["existing_chapter_owner"][
        "checked_path"
    ] == str(spec["request_owner_snapshot"])
    assert identity["execution_owner"]["sha256"] != hash_file(
        spec["request_owner_snapshot"]
    )
    assert receipt["rendered"] is False
    spec["request_owner_snapshot"].write_text("changed snapshot")
    with pytest.raises(ValueError, match="input bytes drift"):
        native_narrative.admit_native_chapters(**spec)


def test_chapter_engineering_snapshot_cannot_bypass_factual_source_drift(
    tmp_path, monkeypatch
):
    spec = chapter_fixture(tmp_path, monkeypatch)
    (spec["repo_root"] / "source.txt").write_text("changed source")
    with pytest.raises(ValueError, match="input bytes drift"):
        native_narrative.admit_native_chapters(**spec)


@pytest.mark.parametrize("target", ["source", "manifest"])
def test_chapter_drift_is_rejected_before_renderer_or_cache(
    tmp_path, monkeypatch, target
):
    spec = chapter_fixture(tmp_path, monkeypatch)
    receipt = native_narrative.admit_native_chapters(**spec)
    from pathlib import Path

    changed = (
        (spec["repo_root"] / ".task-runtime/project/src/index.tsx")
        if target == "source"
        else Path(receipt["manifest"])
    )
    changed.write_text("changed after admission")
    monkeypatch.setattr(
        FreeformChapterPipeline,
        "render_chapter",
        lambda *_a, **_k: pytest.fail("renderer must not run"),
    )
    with pytest.raises(ValueError, match="drift"):
        native_narrative.render_native_chapter(
            manifest_path=Path(receipt["manifest"]),
            repo_root=spec["repo_root"],
            chapter_id="CH01",
            output_dir=spec["output_dir"],
        )


def test_canonical_chapter_launch_has_exactly_one_crf(tmp_path, monkeypatch):
    from video.unattended_core_factory_v1 import media

    repo = tmp_path / "repo"
    repo.mkdir()
    manifest = repo / "film.json"
    manifest.write_text(
        json.dumps(
            dict(
                project_root="project",
                entry="src/index.tsx",
                runtime_paths=dict(
                    dependency_root=str(repo / "deps"),
                    browser_executable=str(repo / "browser"),
                ),
                chapters=[dict(id="CH01", composition="CH01", duration_frames=1500)],
            )
        )
    )
    monkeypatch.setattr(
        media,
        "remotion_launch_geometry",
        lambda **_: dict(command=["remotion", "render", "--crf=14"]),
    )
    owner = FreeformChapterPipeline(manifest, repo_root=repo)
    command = owner.render_command(
        "CH01", repo / "out.mp4", profile="lock", concurrency=2
    )
    assert len([v for v in command if v.startswith("--crf")]) == 1
