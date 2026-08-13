from __future__ import annotations

import json
import math
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

import pytest

import live_contentops.retention_native_video_factory_v2 as factory
from live_contentops.content_intelligence_contracts_v2 import logical_hash
from live_contentops.retention_native_video_contracts_v2 import (
    AssetPlan,
    DirectorBundle,
    RetentionDiagnostics,
)
from live_contentops.retention_native_video_critic_v2 import validate_critic_output
from live_contentops.retention_native_video_factory_v2 import (
    DEFAULT_DIRECTOR_SOURCE,
    DEFAULT_RENDERER_ROOT,
    DEFAULT_STORY_INPUT,
    _analyze_frame_sequence,
    _bind_subagent_critic_execution,
    _caption_cues,
    _compile_jobs,
    _finalize_package,
    _hash_manifest,
    _existing_locked_package,
    _read_json,
    _render_cache_attestation_path,
    _renderer_source_manifest,
    _selective_rerender_proof,
    _validated_render_cache_hit,
    _write_json,
    build_director_bundle,
    hydrate_assets,
    load_governed_oil_story,
    sha256_file,
    verify_hash_manifest,
)


def _bundle() -> DirectorBundle:
    story = load_governed_oil_story(DEFAULT_STORY_INPUT)
    return build_director_bundle(_read_json(DEFAULT_DIRECTOR_SOURCE), story)


def _narration(bundle: DirectorBundle) -> dict[str, dict]:
    fps = {row.variant_id: row.fps for row in bundle.platform_variant_plan.variants}
    result = {}
    for graph in bundle.beat_graphs:
        for beat in graph.beats:
            frames = int(math.ceil(beat.target_duration_seconds * fps[graph.variant_id]))
            result[beat.beat_id] = {
                "beat_id": beat.beat_id,
                "variant_id": graph.variant_id,
                "duration_in_frames": frames,
                "sha256": logical_hash({"beat_id": beat.beat_id, "text": beat.narration_text}),
            }
    return result


def _assets(bundle: DirectorBundle) -> dict[str, dict]:
    return {
        row.asset_id: {
            **asdict(row),
            "sha256": row.sha256 or logical_hash(asdict(row)),
            "relative_public_path": f"assets/{row.asset_id}.png" if row.source_path else None,
        }
        for row in bundle.asset_plan.assets
    }


def test_governed_eia_story_builds_two_independent_platform_graphs() -> None:
    bundle = _bundle()
    graphs = {row.variant_id: row for row in bundle.beat_graphs}
    assert len(graphs["short_9x16"].beats) == 18
    assert len(graphs["midform_16x9"].beats) == 37
    assert graphs["short_9x16"].beats[0].narration_text != graphs["midform_16x9"].beats[0].narration_text
    assert len(bundle.asset_plan.assets) == 9
    assert len({row.asset_class for row in bundle.asset_plan.assets}) >= 7
    assert bundle.public_write_authority is False
    assert bundle.opportunity.public_write_authority is False


def test_midform_first_full_payoff_is_inside_initial_retention_window() -> None:
    graph = next(row for row in _bundle().beat_graphs if row.variant_id == "midform_16x9")
    first_payoff_index = next(index for index, beat in enumerate(graph.beats) if beat.payoff_for)
    start = sum(row.target_duration_seconds for row in graph.beats[:first_payoff_index])
    assert 30 <= start <= 60
    assert graph.beats[first_payoff_index].beat_id == "mid-b08"


def test_contract_fails_closed_for_public_authority_and_unaccepted_rights() -> None:
    bundle = _bundle()
    with pytest.raises(ValueError, match="public_write_forbidden"):
        replace(bundle, public_write_authority=True).validate()
    bad_asset = replace(bundle.asset_plan.assets[0], rights_status="UNKNOWN")
    bad_plan = AssetPlan(video_id=bundle.asset_plan.video_id, assets=(bad_asset, *bundle.asset_plan.assets[1:]))
    with pytest.raises(ValueError, match="asset_rights_not_accepted"):
        replace(bundle, asset_plan=bad_plan).validate()


def test_audio_mastering_keeps_codec_safe_true_peak_headroom(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _bundle()
    graph = next(row for row in bundle.beat_graphs if row.variant_id == "short_9x16")
    narration = tmp_path / "narration.wav"
    music = tmp_path / "music.wav"
    sfx = tmp_path / "sfx.wav"
    for path in (narration, music, sfx):
        path.write_bytes(b"audio")
    timeline = []
    cursor = 0.0
    for beat in graph.beats:
        timeline.append({
            "beat_id": beat.beat_id,
            "start_seconds": cursor,
            "end_seconds": cursor + beat.target_duration_seconds,
        })
        cursor += beat.target_duration_seconds
    cue_ids = {
        str(row["cue_id"])
        for row in bundle.audio_plan.sfx_cues
        if str(row["beat_id"]) in {beat.beat_id for beat in graph.beats}
    }
    monkeypatch.setattr(factory, "render_owned_score", lambda **_kwargs: {
        "duration_seconds": cursor,
        "music": {"path": str(music)},
        "sfx": {"path": str(sfx)},
        "sfx_execution_receipts": [
            {
                "cue_id": cue_id,
                "energy_verified": True,
                "frame_count": 1,
                "measured_mean_square_energy": 0.01,
            }
            for cue_id in sorted(cue_ids)
        ],
    })
    commands: list[list[str]] = []
    loudnorm = json.dumps({
        "input_i": "-18.0",
        "input_lra": "2.0",
        "input_tp": "-1.0",
        "input_thresh": "-28.0",
        "target_offset": "0.0",
    })

    def fake_run(command, **_kwargs):
        command = [str(value) for value in command]
        commands.append(command)
        output = Path(command[-1])
        if output.suffix == ".wav":
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(b"mastered-audio")
        return SimpleNamespace(stderr=loudnorm)

    monkeypatch.setattr(factory, "_run", fake_run)
    monkeypatch.setattr(factory, "_loudness_measure", lambda *_args, **_kwargs: {
        "integrated_lufs": -16.0,
        "true_peak_dbtp": -2.0,
    })

    result = factory._score_and_mix_variant(
        bundle,
        {
            "variant_id": graph.variant_id,
            "duration_seconds": cursor,
            "narration_path": str(narration),
            "beat_timeline": timeline,
        },
        graph=graph,
        output_root=tmp_path,
        ffmpeg="ffmpeg",
    )

    loudnorm_filters = [
        command[command.index("-af") + 1]
        for command in commands
        if "-af" in command and "loudnorm=" in command[command.index("-af") + 1]
    ]
    assert factory.MASTERING_TRUE_PEAK_DBTP == -2.5
    assert len(loudnorm_filters) == 2
    assert all("TP=-2.5" in value for value in loudnorm_filters)
    assert result["processing_true_peak_dbtp"] == -2.5
    assert result["contract_true_peak_dbtp_max"] == -1.5


def test_compiler_consumes_every_beat_and_preserves_caption_limits(tmp_path: Path) -> None:
    bundle = _bundle()
    jobs = _compile_jobs(
        bundle,
        narration=_narration(bundle),
        assets=_assets(bundle),
        output_root=tmp_path,
    )
    assert len(jobs["short_9x16"]) == 18
    assert len(jobs["midform_16x9"]) == 37
    assert all(job["width"] == 1080 and job["height"] == 1920 for job in jobs["short_9x16"])
    assert all(job["width"] == 1920 and job["height"] == 1080 for job in jobs["midform_16x9"])
    assert all(job["edit_states"] and job["edit_states"][0]["at_frame"] == 0 for rows in jobs.values() for job in rows)
    assert max(len(cue["lines"]) for rows in jobs.values() for job in rows for cue in job["caption_cues"]) <= 2
    assert all(job["captions_visible"] for rows in jobs.values() for job in rows)
    fingerprints = {job["renderer_source_fingerprint"] for rows in jobs.values() for job in rows}
    assert len(fingerprints) == 1
    assert len(next(iter(fingerprints))) == 64


def test_renderer_source_fingerprint_invalidates_every_compiled_beat(tmp_path: Path) -> None:
    bundle = _bundle()
    narration = _narration(bundle)
    assets = _assets(bundle)
    before = _compile_jobs(
        bundle,
        narration=narration,
        assets=assets,
        output_root=tmp_path,
        renderer_source_fingerprint="0" * 64,
    )
    after = _compile_jobs(
        bundle,
        narration=narration,
        assets=assets,
        output_root=tmp_path,
        renderer_source_fingerprint="1" * 64,
    )
    before_keys = {job["beat_id"]: job["cache_key"] for rows in before.values() for job in rows}
    after_keys = {job["beat_id"]: job["cache_key"] for rows in after.values() for job in rows}
    assert before_keys.keys() == after_keys.keys()
    assert all(before_keys[beat_id] != after_keys[beat_id] for beat_id in before_keys)


def test_one_edit_override_invalidates_exactly_one_beat(tmp_path: Path) -> None:
    bundle = _bundle()
    narration = _narration(bundle)
    assets = _assets(bundle)
    baseline = _compile_jobs(bundle, narration=narration, assets=assets, output_root=tmp_path)
    target = baseline["midform_16x9"][18]
    decision_id = target["edit_states"][0]["decision_id"]
    patched = _compile_jobs(
        bundle,
        narration=narration,
        assets=assets,
        output_root=tmp_path,
        edit_overrides={decision_id: {"test_marker": "one_beat_only"}},
    )
    before = {row["beat_id"]: row["cache_key"] for jobs in baseline.values() for row in jobs}
    after = {row["beat_id"]: row["cache_key"] for jobs in patched.values() for row in jobs}
    assert [beat_id for beat_id in before if before[beat_id] != after[beat_id]] == [target["beat_id"]]


def test_caption_cues_cover_text_without_more_than_two_lines() -> None:
    text = "The governed forecast changes the physical mechanism without turning a projection into a certainty."
    cues = _caption_cues(text, duration_frames=180, fps=30, portrait=True)
    assert cues[0]["start_frame"] == 0
    assert cues[-1]["end_frame"] <= 180
    assert all(1 <= len(row["lines"]) <= 2 for row in cues)
    assert " ".join(line for row in cues for line in row["lines"]).split() == text.split()


@pytest.mark.parametrize(
    ("frames", "failure"),
    [
        ([b"\x00" * 16], "primary_visual_frame_sequence_insufficient"),
        ([b"\x00" * 16, b"\x00" * 15], "primary_visual_frame_size_invalid"),
        ([b"", b""], "primary_visual_frame_size_invalid"),
    ],
    ids=("insufficient", "misaligned", "empty-corrupt"),
)
def test_frame_sequence_analysis_rejects_invalid_input(frames: list[bytes], failure: str) -> None:
    with pytest.raises(RuntimeError, match=failure):
        _analyze_frame_sequence(frames, sample_fps=2.0, duration_seconds=1.0)


def test_frame_sequence_analysis_detects_genuinely_static_run() -> None:
    frame = bytes([17]) * 1_000
    result = _analyze_frame_sequence(
        [frame, frame, frame, frame, frame, frame],
        sample_fps=2.0,
        duration_seconds=2.5,
    )
    assert result["longest_static_primary_visual_run_seconds"] == 2.5
    assert result["longest_static_primary_visual_time_range_seconds"] == [0.0, 2.5]
    assert result["difference_p95"] == 0.0


def test_frame_sequence_analysis_rejects_incomplete_duration_coverage() -> None:
    with pytest.raises(RuntimeError, match="primary_visual_frame_count_duration_mismatch"):
        _analyze_frame_sequence(
            [bytes(100), bytes(100)],
            sample_fps=2.0,
            duration_seconds=3.0,
        )


def test_frame_sequence_analysis_resets_static_run_for_small_substantial_change() -> None:
    base = bytes(1_000)
    changed = bytes([100]) * 25 + bytes(975)
    result = _analyze_frame_sequence(
        [base, base, changed, changed, changed],
        sample_fps=2.0,
        duration_seconds=2.0,
    )
    assert result["difference_p95"] < 0.012
    assert result["changed_pixel_fraction_p95"] == 0.025
    assert result["cumulative_motion_changed_pixel_fraction_threshold"] == 0.02
    assert result["longest_static_primary_visual_run_seconds"] == 1.0


def test_hydrate_assets_rejects_repository_path_escape(tmp_path: Path) -> None:
    bundle = _bundle()
    escaped = replace(bundle.asset_plan.assets[0], source_path="../outside-repository.jpg")
    bad_bundle = replace(
        bundle,
        asset_plan=AssetPlan(
            video_id=bundle.asset_plan.video_id,
            assets=(escaped, *bundle.asset_plan.assets[1:]),
        ),
    )
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    with pytest.raises(RuntimeError, match="asset_source_outside_repository"):
        hydrate_assets(
            bad_bundle,
            repo_root=repo_root,
            public_dir=tmp_path / "public",
            source_cache=tmp_path / "source-cache",
        )


@pytest.mark.parametrize(("image_exists", "sidecar_exists"), [(True, False), (False, True)])
def test_hydrate_assets_rejects_partial_nasa_cache(
    tmp_path: Path,
    image_exists: bool,
    sidecar_exists: bool,
) -> None:
    cache = tmp_path / "source-cache"
    cache.mkdir()
    if image_exists:
        (cache / "ISS069-E-92132.JPG").write_bytes(b"\xff\xd8cached")
    if sidecar_exists:
        _write_json(cache / "ISS069-E-92132.retrieval.json", {"partial": True})
    with pytest.raises(RuntimeError, match="nasa_asset_cache_partial_state"):
        hydrate_assets(
            _bundle(),
            repo_root=Path(__file__).resolve().parents[1],
            public_dir=tmp_path / "public",
            source_cache=cache,
        )


def test_hydrate_assets_rejects_tampered_nasa_cache_hash(tmp_path: Path) -> None:
    bundle = _bundle()
    nasa = bundle.asset_plan.assets[0]
    cache = tmp_path / "source-cache"
    cache.mkdir()
    (cache / "ISS069-E-92132.JPG").write_bytes(b"\xff\xd8cached")
    _write_json(cache / "ISS069-E-92132.retrieval.json", {
        "schema_version": "contentops.retention_native.asset_retrieval_receipt.v2",
        "asset_id": nasa.asset_id,
        "source_url": nasa.source_url,
        "sha256": "0" * 64,
    })
    with pytest.raises(RuntimeError, match="nasa_asset_cache_receipt_invalid"):
        hydrate_assets(
            bundle,
            repo_root=Path(__file__).resolve().parents[1],
            public_dir=tmp_path / "public",
            source_cache=cache,
        )


def test_source_less_documentary_asset_requires_governed_evidence_hash_binding(tmp_path: Path) -> None:
    bundle = _bundle()
    document = next(row for row in bundle.asset_plan.assets if row.asset_class == "official_source_document")
    document_only = replace(
        bundle,
        asset_plan=AssetPlan(video_id=bundle.asset_plan.video_id, assets=(document,)),
    )
    story = load_governed_oil_story(DEFAULT_STORY_INPUT)
    rows, _assets_by_id, _network_calls = hydrate_assets(
        document_only,
        repo_root=Path(__file__).resolve().parents[1],
        public_dir=tmp_path / "public-valid",
        source_cache=tmp_path / "cache-valid",
        governed_evidence=story["evidence"],
    )
    assert rows[0]["hash_verified"] is True
    assert rows[0]["hash_verification_method"] == "governed_evidence_source_hash_binding"
    assert rows[0]["governed_evidence_id"] == "eia-release-press590"

    with pytest.raises(RuntimeError, match="documentary_asset_governed_hash_binding_missing"):
        hydrate_assets(
            document_only,
            repo_root=Path(__file__).resolve().parents[1],
            public_dir=tmp_path / "public-missing",
            source_cache=tmp_path / "cache-missing",
        )


def test_render_cache_attestation_hash_and_probe_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "beat.mp4"
    payload = b"verified-render-cache"
    output.write_bytes(payload)
    job = {
        "beat_id": "short-b01",
        "variant_id": "short_9x16",
        "cache_key": "cache-key-v2",
        "renderer_version": "renderer-v2",
        "duration_in_frames": 90,
        "fps": 30,
        "width": 1080,
        "height": 1920,
    }
    assert _validated_render_cache_hit(output, job, "ffprobe") is None

    attestation = {
        "schema_version": "contentops.retention_native.render_cache_attestation.v2",
        "beat_id": job["beat_id"],
        "variant_id": job["variant_id"],
        "cache_key": job["cache_key"],
        "renderer_version": job["renderer_version"],
        "output_path": str(output),
        "output_sha256": sha256_file(output),
        "size_bytes": output.stat().st_size,
        "duration_in_frames": job["duration_in_frames"],
        "fps": job["fps"],
        "width": job["width"],
        "height": job["height"],
    }
    _write_json(_render_cache_attestation_path(output), attestation)
    monkeypatch.setattr(factory, "_validate_render_media", lambda *_args, **_kwargs: {"duration_seconds": 3.0})
    assert _validated_render_cache_hit(output, job, "ffprobe") == attestation

    output.write_bytes(b"tampered-render-cache")
    assert _validated_render_cache_hit(output, job, "ffprobe") is None

    output.write_bytes(payload)
    monkeypatch.setattr(
        factory,
        "_validate_render_media",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("probe rejected media")),
    )
    assert _validated_render_cache_hit(output, job, "ffprobe") is None


def test_render_media_rejects_wrong_frame_rate_and_frame_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "beat.mp4"
    output.write_bytes(b"probe-fixture")
    job = {
        "beat_id": "short-b01",
        "duration_in_frames": 90,
        "fps": 30,
        "width": 1080,
        "height": 1920,
    }
    probe = {
        "streams": [{
            "codec_type": "video",
            "codec_name": "h264",
            "width": 1080,
            "height": 1920,
            "avg_frame_rate": "15/1",
            "r_frame_rate": "15/1",
            "nb_frames": "45",
        }],
        "format": {"duration": "3.0"},
    }
    monkeypatch.setattr(factory, "_probe", lambda *_args, **_kwargs: probe)
    with pytest.raises(RuntimeError, match="render_cache_frame_rate_mismatch"):
        factory._validate_render_media(output, job, "ffprobe")

    probe["streams"][0].update({"avg_frame_rate": "30/1", "r_frame_rate": "30/1", "nb_frames": "80"})
    with pytest.raises(RuntimeError, match="render_cache_frame_count_mismatch"):
        factory._validate_render_media(output, job, "ffprobe")

    probe["streams"][0].pop("avg_frame_rate")
    with pytest.raises(RuntimeError, match="video_frame_rate_missing:short-b01:avg_frame_rate"):
        factory._validate_render_media(output, job, "ffprobe")
    probe["streams"][0]["avg_frame_rate"] = "30/1"
    probe["streams"][0]["nb_frames"] = "90"
    measured = factory._validate_render_media(output, job, "ffprobe")
    assert measured["frame_rate_fps"] == 30.0
    assert measured["frame_count"] == 90


def test_selective_rerender_proof_rejects_unproven_cache_only_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _bundle()
    narration = _narration(bundle)
    assets = _assets(bundle)
    baseline = _compile_jobs(bundle, narration=narration, assets=assets, output_root=tmp_path)
    monkeypatch.setattr(factory, "_validated_render_cache_hit", lambda *_args, **_kwargs: {"status": "CACHE_HIT"})
    monkeypatch.setattr(
        factory,
        "_render_jobs",
        lambda *_args, **_kwargs: pytest.fail("an unproven cache-only target must not be rendered as proof"),
    )
    with pytest.raises(RuntimeError, match="selective_rerender_cached_target_without_original_receipt"):
        _selective_rerender_proof(
            bundle,
            baseline_jobs=baseline,
            narration=narration,
            assets=assets,
            renderer_root=tmp_path / "renderer",
            public_dir=tmp_path / "public",
            output_root=tmp_path,
            node="node",
            ffprobe="ffprobe",
        )


def test_selective_rerender_proof_rejects_incomplete_preserved_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _bundle()
    narration = _narration(bundle)
    assets = _assets(bundle)
    baseline = _compile_jobs(bundle, narration=narration, assets=assets, output_root=tmp_path)
    target = baseline["midform_16x9"][len(baseline["midform_16x9"]) // 2]
    decision_id = target["edit_states"][0]["decision_id"]
    patched = _compile_jobs(
        bundle,
        narration=narration,
        assets=assets,
        output_root=tmp_path,
        renderer_source_fingerprint=target["renderer_source_fingerprint"],
        edit_overrides={decision_id: {"selective_proof_marker": "controlled_one_beat_invalidation_v2"}},
    )
    patched_target = next(row for row in patched["midform_16x9"] if row["beat_id"] == target["beat_id"])
    output = Path(patched_target["output_path"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"rendered-selective-proof")
    original = tmp_path / "receipts" / "selective_rerender_one_beat_original_v2.json"
    _write_json(original, {
        "schema_version": "contentops.retention_native.selective_rerender_original.v2",
        "status": "PASS",
        "target_beat_id": patched_target["beat_id"],
        "cache_key": patched_target["cache_key"],
        "output_path": str(output),
        "output_sha256": sha256_file(output),
        "render_receipt": {
            "schema_version": "contentops.retention_native.render_receipt.v2",
            "status": "BLOCK",
            "receipt_name": "selective_rerender_one_beat_proof",
            "requested_job_count": 1,
            "rendered_job_count": 1,
            "cache_hit_count": 0,
            "rows": [{
                "status": "CACHE_HIT",
                "beat_id": patched_target["beat_id"],
                "variant_id": patched_target["variant_id"],
                "cache_key": patched_target["cache_key"],
                "output_path": str(output),
                "output_sha256": sha256_file(output),
            }],
        },
    })
    monkeypatch.setattr(factory, "_validated_render_cache_hit", lambda *_args, **_kwargs: {"output_sha256": sha256_file(output)})
    with pytest.raises(RuntimeError, match="selective_rerender_original_raw_receipt_invalid"):
        _selective_rerender_proof(
            bundle,
            baseline_jobs=baseline,
            narration=narration,
            assets=assets,
            renderer_root=tmp_path / "renderer",
            public_dir=tmp_path / "public",
            output_root=tmp_path,
            node="node",
            ffprobe="ffprobe",
        )


def test_hash_manifest_detects_mutation_and_untracked_file(tmp_path: Path) -> None:
    (tmp_path / "proof.txt").write_text("accepted", encoding="utf-8")
    _write_json(tmp_path / "hash_manifest.json", _hash_manifest(tmp_path))
    assert verify_hash_manifest(tmp_path)["status"] == "PASS"
    (tmp_path / "proof.txt").write_text("changed", encoding="utf-8")
    assert verify_hash_manifest(tmp_path)["status"] == "BLOCK"
    (tmp_path / "proof.txt").write_text("accepted", encoding="utf-8")
    (tmp_path / "extra.json").write_text(json.dumps({"new": True}), encoding="utf-8")
    result = verify_hash_manifest(tmp_path)
    assert result["status"] == "BLOCK"
    assert "untracked:extra.json" in result["blockers"]


def test_independent_critic_schema_requires_material_issue_to_trigger_revision() -> None:
    issue = {
        "severity": "MAJOR",
        "video_id": _bundle().opportunity.video_id,
        "variant_id": "short_9x16",
        "scene_id": "short-proof",
        "start_seconds": 40.0,
        "end_seconds": 44.0,
        "beat_ids": ["short-b11"],
        "category": "visual",
        "observation": "Landscape chart is not legible in the vertical cut.",
        "structural_fix": "Use a portrait-native chart reframe for short-b11.",
    }
    base = {
        "summary": "A material issue remains.",
        "scope": {
            "visual_images_reviewed": True,
            "actual_finished_media_sampled": True,
            "audio_listened": False,
            "audio_technical_metrics_reviewed": True,
            "limitations": ["Audio was not auditioned."],
        },
        "issues": [issue],
        "strengths": ["The hook is clear."],
        "acceptance_recommendation": "Revise the localized chart beat.",
    }
    bad = {**base, "status": "PASS"}
    assert validate_critic_output(json.dumps(bad))[0] is False
    good = {**base, "status": "REVISE"}
    assert validate_critic_output(json.dumps(good))[0] is True


def test_independent_critic_accepts_wrapped_json_without_weakening_schema() -> None:
    value = {
        "status": "PASS_WITH_NOTES",
        "summary": "No material issue remains.",
        "scope": {
            "visual_images_reviewed": True,
            "actual_finished_media_sampled": True,
            "audio_listened": False,
            "audio_technical_metrics_reviewed": True,
            "limitations": ["Audio was not auditioned."],
        },
        "issues": [],
        "strengths": ["The primary visual evolves clearly."],
        "acceptance_recommendation": "Accept with notes.",
    }
    wrapped = "Editorial review follows.\n```json\n" + json.dumps(value) + "\n```\nEnd."
    accepted, failure_class, value, diagnostic = validate_critic_output(wrapped)
    assert accepted is True
    assert failure_class is None
    assert value["status"] == "PASS_WITH_NOTES"
    assert value["issues"] == []
    assert diagnostic is None


def test_finalize_package_rejects_minimal_fabricated_critic(tmp_path: Path) -> None:
    critic_path = tmp_path / "critic.json"
    _write_json(critic_path, {
        "status": "PASS_WITH_NOTES",
        "independent_of_director": True,
        "issues": [],
        "scope": {"audio_listened": False},
    })
    with pytest.raises(RuntimeError, match="critic_schema_version_invalid"):
        _finalize_package(tmp_path, critic_path, revision_count=2)
    assert not (tmp_path / "package_lock.json").exists()


def _machine_gate_lock_fixture(tmp_path: Path) -> tuple[DirectorBundle, dict[str, dict], dict]:
    bundle = _bundle()
    (tmp_path / "contracts").mkdir()
    _write_json(tmp_path / "contracts" / "director_bundle_v2.json", bundle.to_dict())
    diagnostic = RetentionDiagnostics(
        video_id=bundle.opportunity.video_id,
        variant_id="short_9x16",
        duration_seconds=60.0,
        hook_timing_seconds=0.0,
        first_payoff_timing_seconds=10.0,
        meaningful_visual_beat_intervals_seconds=(2.0, 3.0),
        longest_static_primary_visual_run_seconds=3.0,
        asset_classes=("deterministic_map", "deterministic_timeline", "official_source_document", "real_location_imagery"),
        caption_max_lines=2,
        caption_safe_zone_status="PASS",
        music_coverage_ratio=1.0,
        sfx_coverage_ratio=1.0,
        integrated_lufs=-16.0,
        true_peak_dbtp=-1.8,
        open_loop_payoff_status="PASS",
        claim_evidence_coverage_ratio=1.0,
        rights_coverage_ratio=1.0,
        status="PASS",
        blockers=(),
    )
    artifact_rows = []
    rendered_variants = {}
    caption_hidden = {}
    review_variants = {}
    assemblies = {}
    render_receipts = {}
    retention_rows = {}
    for variant_id in ("short_9x16", "midform_16x9"):
        duration = 60.0 if variant_id == "short_9x16" else 240.0
        width, height = (1080, 1920) if variant_id == "short_9x16" else (1920, 1080)
        prefix = "short" if variant_id == "short_9x16" else "mid"
        finished = tmp_path / "outputs" / f"{variant_id}.mp4"
        hidden = tmp_path / "review" / f"{variant_id}_captions_hidden.mp4"
        representative = tmp_path / "review" / f"{variant_id}_representative.mp4"
        contact_sheet = tmp_path / "review" / f"{variant_id}_contact_sheet.jpg"
        motion_strip = tmp_path / "review" / f"{variant_id}_motion_strip.jpg"
        for path, payload in (
            (finished, f"finished:{variant_id}".encode()),
            (hidden, f"captions-hidden:{variant_id}".encode()),
            (representative, f"representative:{variant_id}".encode()),
            (contact_sheet, f"contact:{variant_id}".encode()),
            (motion_strip, f"motion:{variant_id}".encode()),
        ):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        rendered_variants[variant_id] = {
            "variant_id": variant_id,
            "path": str(finished),
            "sha256": sha256_file(finished),
            "size_bytes": finished.stat().st_size,
            "duration_seconds": duration,
            "probe": {
                "streams": [
                    {
                        "codec_type": "video",
                        "codec_name": "h264",
                        "width": width,
                        "height": height,
                        "avg_frame_rate": "30/1",
                        "r_frame_rate": "30/1",
                        "nb_frames": str(round(duration * 30)),
                    },
                    {"codec_type": "audio", "codec_name": "aac"},
                ],
                "format": {"duration": str(duration)},
            },
            "loudness": {"integrated_lufs": -16.0, "true_peak_dbtp": -1.8},
        }
        caption_hidden[variant_id] = {
            "status": "PASS",
            "captions_visible": False,
            "path": str(hidden),
            "sha256": sha256_file(hidden),
            "motion_strip_path": str(motion_strip),
            "motion_strip_sha256": sha256_file(motion_strip),
            "receipt": {
                "schema_version": "contentops.retention_native.render_receipt.v2",
                "status": "PASS",
                "requested_job_count": 1,
                "rendered_job_count": 1,
                "cache_hit_count": 0,
                "network_calls": 0,
                "uploads": 0,
                "browser_profile_used": False,
                "rows": [{"status": "RENDERED"}],
            },
        }
        review_variants[variant_id] = {
            "review_clip": str(representative),
            "review_clip_sha256": sha256_file(representative),
            "contact_sheet": str(contact_sheet),
            "contact_sheet_sha256": sha256_file(contact_sheet),
            "review_motion_strip": str(motion_strip),
            "review_motion_strip_sha256": sha256_file(motion_strip),
            "stills": [{"name": "hook", "path": str(contact_sheet), "sha256": sha256_file(contact_sheet)}],
        }
        assemblies[variant_id] = {
            "duration_seconds": duration,
            "beat_timeline": [{
                "beat_id": f"{prefix}-b01",
                "scene_id": f"{prefix}-hook",
                "start_seconds": 0.0,
                "end_seconds": duration,
            }],
            "jobs": [],
        }
        render_receipts[variant_id] = {
            "schema_version": "contentops.retention_native.render_receipt.v2",
            "status": "PASS",
            "requested_job_count": 1,
            "rendered_job_count": 1,
            "cache_hit_count": 0,
            "network_calls": 0,
            "uploads": 0,
            "browser_profile_used": False,
            "rows": [{"status": "RENDERED"}],
        }
        variant_diagnostic = diagnostic if variant_id == "short_9x16" else replace(
            diagnostic,
            variant_id="midform_16x9",
            duration_seconds=240.0,
            first_payoff_timing_seconds=40.0,
        )
        retention_rows[variant_id] = {
            "contract": asdict(variant_diagnostic),
            "detail": {
                "primary_visual_measurement": {
                    "source_video": str(finished),
                    "source_video_sha256": sha256_file(finished),
                    "sample_fps": 2.0,
                    "sampled_frame_count": round(duration * 2),
                    "expected_frame_count": round(duration * 2),
                    "trailing_partial_interval_seconds": 0.0,
                    "longest_static_primary_visual_run_seconds": 3.0,
                    "meaningful_visual_beat_intervals_seconds": [2.0, 3.0],
                }
            },
        }
        artifact_rows.extend([
            {
                "kind": "finished_output",
                "variant_id": variant_id,
                "path": str(finished),
                "sha256": sha256_file(finished),
            },
            {
                "kind": "captions_hidden_motion_clip",
                "variant_id": variant_id,
                "path": str(hidden),
                "sha256": sha256_file(hidden),
            },
            {
                "kind": "representative_review_clip",
                "variant_id": variant_id,
                "path": str(representative),
                "sha256": sha256_file(representative),
            },
        ])
    renderer_source = _renderer_source_manifest(DEFAULT_RENDERER_ROOT)
    _write_json(tmp_path / "renderer_source_manifest_v2.json", renderer_source)
    fingerprint = renderer_source["renderer_source_fingerprint"]
    for assembly in assemblies.values():
        assembly["jobs"] = [{"renderer_source_fingerprint": fingerprint}]
    _write_json(tmp_path / "variant_render_manifest_v2.json", {
        "schema_version": "contentops.retention_native.variant_render_manifest.v2",
        "status": "PASS",
        "renderer_source_fingerprint": fingerprint,
        "variants": rendered_variants,
        "assemblies": assemblies,
        "render_receipts": render_receipts,
        "public_write_authority": False,
    })
    _write_json(tmp_path / "retention_diagnostics_v2.json", {
        "schema_version": "contentops.retention_native.retention_diagnostics.v2",
        "status": "PASS",
        "variants": retention_rows,
    })
    _write_json(tmp_path / "review_media_manifest_v2.json", {
        "schema_version": "contentops.retention_native.review_media.v2",
        "status": "PASS",
        "variants": review_variants,
        "caption_hidden": caption_hidden,
    })
    _write_json(tmp_path / "deterministic_media_qa.json", {
        "schema_version": "contentops.retention_native.deterministic_media_qa.v2",
        "machine_status": "PASS",
        "variants": rendered_variants,
        "diagnostic_statuses": {"short_9x16": "PASS", "midform_16x9": "PASS"},
        "rights_status": "PASS",
        "selective_rerender_status": "PASS",
        "caption_hidden_primary_visual_review_media": True,
        "source_claim_coverage_ratio": 1.0,
        "rights_coverage_ratio": 1.0,
        "visual_acceptance": "AWAITING_INDEPENDENT_CRITIC_AND_CHATGPT_JIM",
        "public_write": False,
        "public_upload": False,
        "browser_profile_used": False,
    })
    used_claim_ids = {
        claim_id for graph in bundle.beat_graphs for beat in graph.beats for claim_id in beat.claim_ids
    }
    used_evidence_ids = {
        evidence_id for graph in bundle.beat_graphs for beat in graph.beats for evidence_id in beat.evidence_ids
    }
    story_claims = {claim_id: {"claim_id": claim_id, "value": "fixture"} for claim_id in used_claim_ids}
    story_evidence = {
        evidence_id: {
            "source_url": f"https://example.test/{evidence_id}",
            "sha256": logical_hash({"evidence_id": evidence_id}),
        }
        for evidence_id in used_evidence_ids
    }
    asset_rows = []
    for row in bundle.asset_plan.assets:
        value = {**asdict(row), "sha256": row.sha256 or logical_hash(asdict(row))}
        value.update({
            "hash_verified": True,
            "rights_gate": "PASS",
            "render_identity_sha256": value["sha256"],
            "hydrated_path": None,
        })
        if row.source_path:
            hydrated = tmp_path / "render_public" / "assets" / f"{row.asset_id}.bin"
            hydrated.parent.mkdir(parents=True, exist_ok=True)
            hydrated.write_bytes(f"hydrated:{row.asset_id}".encode())
            value["hydrated_path"] = str(hydrated)
            value["sha256"] = sha256_file(hydrated)
        elif row.documentary:
            evidence_id = f"fixture-{row.asset_id}"
            story_evidence[evidence_id] = {
                "source_url": row.source_url,
                "sha256": value["sha256"],
            }
            value["governed_evidence_id"] = evidence_id
            value["hash_verification_method"] = "governed_evidence_source_hash_binding"
        if str(row.asset_class).startswith("deterministic_"):
            value["render_identity_sha256"] = value["sha256"]
        asset_rows.append(value)
    _write_json(tmp_path / "contracts" / "story_binding_v2.json", {
        "schema_version": "contentops.retention_native.story_binding.v2",
        "story_id": bundle.opportunity.story_id,
        "story_version": bundle.opportunity.story_version,
        "article_hash": bundle.opportunity.evidence_hashes[1],
        "official_source_hash": bundle.opportunity.evidence_hashes[0],
        "claims": story_claims,
        "evidence": story_evidence,
        "historical_governed_package": True,
        "claim_evidence_coverage_ratio": 1.0,
        "public_write_authority": False,
    })

    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    beat_variant = {beat.beat_id: graph.variant_id for graph in bundle.beat_graphs for beat in graph.beats}
    mixes = {}
    music_hashes = {}
    for variant_id in ("short_9x16", "midform_16x9"):
        cue_ids = sorted(
            str(cue["cue_id"])
            for cue in bundle.audio_plan.sfx_cues
            if beat_variant[str(cue["beat_id"])] == variant_id
        )
        master = audio_dir / f"{variant_id}-master.wav"
        music = audio_dir / f"{variant_id}-music.wav"
        sfx = audio_dir / f"{variant_id}-sfx.wav"
        for path, payload in ((master, b"master"), (music, b"music"), (sfx, b"sfx")):
            path.write_bytes(payload + variant_id.encode())
        sfx_receipts = [{
            "cue_id": cue_id,
            "energy_verified": True,
            "nonzero_sample_count": 10,
            "measured_mean_square_energy": 0.01,
            "measured_peak": 0.1,
        } for cue_id in cue_ids]
        score = {
            "schema_version": "contentops.retention_native.score.v2.2",
            "status": "PASS",
            "generator": "deterministic_numpy_oscillators_and_seeded_noise",
            "rights_status": "CAPITAL_CHRONICLE_OWNED",
            "source_samples": [],
            "model_calls": 0,
            "network_calls": 0,
            "requested_sfx_cue_count": len(cue_ids),
            "executed_sfx_cue_count": len(cue_ids),
            "skipped_sfx_cues": [],
            "music": {"path": str(music), "sha256": sha256_file(music)},
            "sfx": {"path": str(sfx), "sha256": sha256_file(sfx)},
            "sfx_execution_receipts": sfx_receipts,
        }
        music_hashes[variant_id] = score["music"]["sha256"]
        mixes[variant_id] = {
            "schema_version": "contentops.retention_native.audio_mix_receipt.v2",
            "status": "PASS",
            "variant_id": variant_id,
            "provider_calls": 0,
            "network_calls": 0,
            "public_write": False,
            "target_integrated_lufs": -16.0,
            "contract_true_peak_dbtp_max": -1.5,
            "music_coverage_ratio": 1.0,
            "sfx_plan_execution_ratio": 1.0,
            "expected_sfx_cue_ids": cue_ids,
            "executed_sfx_cue_ids": cue_ids,
            "expected_sfx_cue_count": len(cue_ids),
            "executed_sfx_cue_count": len(cue_ids),
            "master_path": str(master),
            "master_sha256": sha256_file(master),
            "measurement": {"integrated_lufs": -16.0, "true_peak_dbtp": -1.8},
            "score": score,
            "sfx_execution_receipts": sfx_receipts,
        }
    _write_json(tmp_path / "audio_provenance_v2.json", {
        "schema_version": "contentops.retention_native.audio_provenance.v2",
        "status": "PASS",
        "provider_calls": 0,
        "network_calls": 0,
        "public_write": False,
        "narration_receipt": {
            "schema_version": "contentops.retention_native.narration_receipt.v2",
            "status": "PASS",
            "provider": bundle.audio_plan.narrator_provider,
            "model": bundle.audio_plan.narrator_model,
            "voice": bundle.audio_plan.narrator_voice,
            "license": bundle.audio_plan.narrator_license,
            "provider_calls": 0,
            "network_calls": 0,
            "network_call_performed": False,
            "public_write": False,
            "public_write_performed": False,
        },
        "mixes": mixes,
    })
    _write_json(tmp_path / "rights_provenance_report_v2.json", {
        "schema_version": "contentops.retention_native.rights_provenance.v2",
        "status": "PASS",
        "blockers": [],
        "assets": asset_rows,
        "generated_illustrations": [],
        "fake_documentary_images": [],
        "real_person_images": [],
        "narration": {"local_inference": True, "network_calls": 0},
        "music_and_sfx": {
            "generator": factory.SCORE_GENERATOR_VERSION,
            "rights_status": "CAPITAL_CHRONICLE_OWNED",
            "source_samples": [],
            "model_calls": 0,
            "variant_hashes": music_hashes,
        },
        "public_write_authority": False,
    })

    patched = tmp_path / "render_cache" / "selective.mp4"
    patched.parent.mkdir()
    patched.write_bytes(b"selective-render")
    patched_hash = sha256_file(patched)
    cache_key = logical_hash({"selective": "fixture"})
    real_receipt = {
        "schema_version": "contentops.retention_native.render_receipt.v2",
        "status": "PASS",
        "requested_job_count": 1,
        "rendered_job_count": 1,
        "cache_hit_count": 0,
        "network_calls": 0,
        "uploads": 0,
        "browser_profile_used": False,
        "rows": [{
            "status": "RENDERED",
            "beat_id": "mid-b19",
            "scene_id": "mid-prices",
            "variant_id": "midform_16x9",
            "output_path": str(patched),
            "output_sha256": patched_hash,
            "cache_key": cache_key,
            "captions_visible": True,
        }],
    }
    cache_receipt = {
        **real_receipt,
        "rendered_job_count": 0,
        "cache_hit_count": 1,
        "rows": [{
            "status": "CACHE_HIT",
            "beat_id": "mid-b19",
            "scene_id": "mid-prices",
            "variant_id": "midform_16x9",
            "output_path": str(patched),
            "output_sha256": patched_hash,
            "cache_key": cache_key,
            "captions_visible": True,
        }],
    }
    raw_receipt = tmp_path / "receipts" / "selective_rerender_one_beat_proof.json"
    _write_json(raw_receipt, {
        "status": "PASS",
        "renderer": "remotion",
        "renderer_version": "4.0.507",
        "rows": [{key: real_receipt["rows"][0][key] for key in (
            "beat_id", "scene_id", "variant_id", "output_path", "cache_key", "captions_visible", "status"
        )}],
        "network_calls": 0,
        "uploads": 0,
        "browser_profile_used": False,
    })
    raw_binding = {"path": str(raw_receipt), "sha256": sha256_file(raw_receipt)}
    real_receipt["raw_renderer_receipt"] = raw_binding
    original = tmp_path / "receipts" / "selective_rerender_one_beat_original_v2.json"
    _write_json(original, {
        "schema_version": "contentops.retention_native.selective_rerender_original.v2",
        "status": "PASS",
        "target_beat_id": "mid-b19",
        "cache_key": cache_key,
        "output_path": str(patched),
        "output_sha256": patched_hash,
        "raw_renderer_receipt": raw_binding,
        "render_receipt": real_receipt,
        "public_write": False,
    })
    selective = {
        "schema_version": "contentops.retention_native.selective_rerender_proof.v2",
        "status": "PASS",
        "target_beat_id": "mid-b19",
        "changed_beat_ids": ["mid-b19"],
        "unchanged_beat_count": 54,
        "unrelated_cache_keys_unchanged": True,
        "canonical_jobs_unchanged": True,
        "patched_render_path": str(patched),
        "patched_render_sha256": patched_hash,
        "original_render_receipt_path": str(original),
        "original_render_receipt_sha256": sha256_file(original),
        "raw_renderer_receipt": raw_binding,
        "receipt": real_receipt,
        "current_cache_verification_receipt": cache_receipt,
        "public_write": False,
    }
    _write_json(tmp_path / "selective_rerender_proof_v2.json", selective)
    _write_json(tmp_path / "revision_history_v2.json", {
        "schema_version": "contentops.retention_native.revision_history.v2",
        "status": "PASS",
        "structural_revision_count": 2,
        "max_structural_revisions": 2,
        "revisions": [
            {"revision_id": "rev-01", "public_write": False, "factual_authority_changed": False},
            {"revision_id": "rev-02", "public_write": False, "factual_authority_changed": False},
        ],
        "selective_rerender_proof": selective,
        "public_write": False,
    })
    _write_json(tmp_path / "safety_boundary_report_v2.json", {
        "schema_version": "contentops.retention_native.safety_boundary.v2",
        "status": "PASS",
        "v1_mutations": 0,
        "browser_profile_actions": 0,
        "cdp_actions": 0,
        "platform_actions": 0,
        "uploads": 0,
        "public_writes": 0,
        "publication_authority": False,
        "synthetic_documentary_assets": 0,
        "generated_real_person_assets": 0,
    })
    _write_json(tmp_path / "cost_runtime_report_v2.json", {
        "schema_version": "contentops.retention_native.cost_runtime.v2",
        "cash_cost_usd": 0.0,
        "provider_calls": 0,
        "renderer_network_calls": 0,
        "public_uploads": 0,
        "browser_profile_used": False,
    })

    contact_sheet = Path(review_variants["short_9x16"]["contact_sheet"])
    critic_value = {
        "schema_version": "contentops.retention_native.independent_multimodal_critic.v2",
        "status": "PASS_WITH_NOTES",
        "summary": "No material issue remains in the bound test media.",
        "independent_of_director": True,
        "issues": [],
        "strengths": ["The test media has a bound primary visual."],
        "acceptance_recommendation": "Accept this deterministic fixture with notes.",
        "critic_identity": {
            "kind": "codex_independent_multimodal_subagent",
            "task_name": "/root/test-independent-media-critic",
        },
        "review_execution": {
            "report_origin": "collaboration_agent_final",
            "reviewer_task_name": "/root/test-independent-media-critic",
            "actual_media_sampled": True,
            "artifact_hashes_verified": True,
            "files_modified": False,
        },
        "scope": {
            "visual_images_reviewed": True,
            "actual_finished_media_sampled": True,
            "audio_listened": False,
            "audio_technical_metrics_reviewed": True,
            "limitations": ["Audio was assessed through technical measurements only."],
        },
        "input_artifacts": artifact_rows,
        "input_images": [{"path": str(contact_sheet), "sha256": sha256_file(contact_sheet)}],
        "publication_authority": False,
        "factual_authority": False,
        "public_write": False,
    }
    return bundle, rendered_variants, critic_value


def test_finalize_package_reconstructs_bundle_and_locks_bound_critic_hashes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, rendered_variants, critic_value = _machine_gate_lock_fixture(tmp_path)
    embedded_probes = {
        str(Path(row["path"]).resolve()): row["probe"] for row in rendered_variants.values()
    }
    monkeypatch.setattr(factory, "_find_binary", lambda *_args, **_kwargs: "ffprobe")
    monkeypatch.setattr(
        factory,
        "_probe",
        lambda path, _ffprobe: json.loads(json.dumps(embedded_probes[str(Path(path).resolve())])),
    )
    critic_path = tmp_path / "critic.json"

    _write_json(critic_path, critic_value)
    with pytest.raises(RuntimeError, match="critic_execution_receipt_binding_missing"):
        _finalize_package(tmp_path, critic_path, revision_count=2)

    canonical = json.loads(json.dumps(critic_value))
    canonical["critic_identity"] = {
        "kind": "canonical_9router_multimodal_model",
        "selected_model": "vx/gemini-3.5-flash(high)",
        "gateway": "9router",
    }
    canonical.pop("review_execution")
    canonical["router_evidence"] = {
        "authority_id": "contentops.nine_router_ordered_model_router.v2",
        "terminal_disposition": "ACCEPTED",
        "selected_model": "vx/gemini-3.5-flash(high)",
        "total_attempts": 1,
    }
    _write_json(critic_path, canonical)
    with pytest.raises(RuntimeError, match="critic_router_execution_receipt_binding_missing"):
        _finalize_package(tmp_path, critic_path, revision_count=2)

    contradictory_authority = json.loads(json.dumps(critic_value))
    contradictory_authority["public_write"] = 1
    _write_json(critic_path, _bind_subagent_critic_execution(tmp_path, contradictory_authority))
    with pytest.raises(RuntimeError, match="critic_authority_contradiction"):
        _finalize_package(tmp_path, critic_path, revision_count=2)

    invalid_localization = json.loads(json.dumps(critic_value))
    invalid_localization["issues"] = [{
        "severity": "NOTE",
        "video_id": bundle.opportunity.video_id,
        "variant_id": "short_9x16",
        "scene_id": "unknown-scene",
        "start_seconds": 1.0,
        "end_seconds": 2.0,
        "beat_ids": ["unknown-beat"],
        "category": "visual",
        "observation": "Synthetic localization test.",
        "structural_fix": "Bind the issue to a real scene and beat.",
    }]
    _write_json(critic_path, _bind_subagent_critic_execution(tmp_path, invalid_localization))
    with pytest.raises(RuntimeError, match="critic_issue_timeline_binding_invalid"):
        _finalize_package(tmp_path, critic_path, revision_count=2)

    _write_json(critic_path, _bind_subagent_critic_execution(tmp_path, critic_value))
    with pytest.raises(RuntimeError, match="revision_history_count_binding_invalid"):
        _finalize_package(tmp_path, critic_path, revision_count=0)

    story_path = tmp_path / "contracts" / "story_binding_v2.json"
    story_binding = _read_json(story_path)
    removed_claim_id = next(iter(story_binding["claims"]))
    removed_claim = story_binding["claims"].pop(removed_claim_id)
    _write_json(story_path, story_binding)
    with pytest.raises(RuntimeError, match="machine_gate_bundle_invalid:story_binding_claim_coverage_invalid"):
        _finalize_package(tmp_path, critic_path, revision_count=2)
    story_binding["claims"][removed_claim_id] = removed_claim
    _write_json(story_path, story_binding)

    raw_selective_path = tmp_path / "receipts" / "selective_rerender_one_beat_proof.json"
    raw_selective_bytes = raw_selective_path.read_bytes()
    raw_selective_path.write_bytes(b"{}")
    with pytest.raises(RuntimeError, match="machine_gate_bundle_invalid:selective_raw_renderer_receipt_invalid"):
        _finalize_package(tmp_path, critic_path, revision_count=2)
    raw_selective_path.write_bytes(raw_selective_bytes)

    safety_path = tmp_path / "safety_boundary_report_v2.json"
    safety = _read_json(safety_path)
    safety["public_writes"] = 1
    _write_json(safety_path, safety)
    with pytest.raises(RuntimeError, match="machine_gate_bundle_invalid:safety_boundary_invalid"):
        _finalize_package(tmp_path, critic_path, revision_count=2)
    safety["public_writes"] = 0
    _write_json(safety_path, safety)

    result = _finalize_package(tmp_path, critic_path, revision_count=2)
    assert result["status"] == "PASS"
    lock = _read_json(tmp_path / "package_lock.json")
    assert lock["status"] == "LOCKED_AWAITING_CHATGPT_JIM_FINAL_MEDIA_ACCEPTANCE"
    assert lock["critic_report_sha256"] == sha256_file(tmp_path / "independent_critic_report_v2.json")
    assert lock["reviewed_output_sha256s"] == {
        variant_id: rendered_variants[variant_id]["sha256"]
        for variant_id in ("short_9x16", "midform_16x9")
    }
    assert verify_hash_manifest(tmp_path)["status"] == "PASS"
    assert _existing_locked_package(tmp_path)["status"] == "PASS_IMMUTABLE_PACKAGE_VERIFIED"

    nested_control = tmp_path / "nested" / "package_lock.json"
    nested_control.parent.mkdir()
    nested_control.write_text("{}", encoding="utf-8")
    assert "untracked:nested/package_lock.json" in verify_hash_manifest(tmp_path)["blockers"]
    nested_control.unlink()

    original_lock = _read_json(tmp_path / "package_lock.json")
    tampered = json.loads(json.dumps(original_lock))
    tampered["public_write_authority"] = True
    _write_json(tmp_path / "package_lock.json", tampered)
    with pytest.raises(RuntimeError, match="immutable_package_lock_payload_hash_mismatch"):
        _existing_locked_package(tmp_path)
    _write_json(tmp_path / "package_lock.json", original_lock)

    safety = _read_json(safety_path)
    safety["public_writes"] = 1
    _write_json(safety_path, safety)
    manifest = _hash_manifest(tmp_path)
    _write_json(tmp_path / "hash_manifest.json", manifest)
    tampered = json.loads(json.dumps(original_lock))
    tampered["hash_manifest_sha256"] = sha256_file(tmp_path / "hash_manifest.json")
    tampered["verified_file_count"] = len(manifest)
    tampered_payload = dict(tampered)
    tampered_payload.pop("lock_payload_logical_sha256")
    tampered["lock_payload_logical_sha256"] = logical_hash(tampered_payload)
    _write_json(tmp_path / "package_lock.json", tampered)
    with pytest.raises(RuntimeError, match="machine_gate_bundle_invalid:safety_boundary_invalid"):
        _existing_locked_package(tmp_path)


def test_canonical_critic_receipt_binds_package_context_and_model_authored_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = "vx/gemini-3.5-flash(high)"
    technical = {
        "video_id": "video-1",
        "request_scope": ["visual"],
        "diagnostics": {"status": "PASS"},
        "beat_timeline": {"short_9x16": [], "midform_16x9": []},
        "image_labels_and_hashes": [],
        "chatgpt_jim_acceptance": "PENDING",
        "public_write_authority": False,
    }
    request = {"outputs": {"short_9x16": {"sha256": "1" * 64}}}
    monkeypatch.setattr(
        factory,
        "_canonical_critic_package_context",
        lambda _root: (technical, [], [], request),
    )
    accepted_output = {
        "status": "PASS",
        "summary": "Bound verdict.",
        "scope": {
            "visual_images_reviewed": True,
            "actual_finished_media_sampled": True,
            "audio_listened": False,
            "audio_technical_metrics_reviewed": True,
            "limitations": ["Audio was not auditioned."],
        },
        "issues": [],
        "strengths": ["Specific visible strength."],
        "acceptance_recommendation": "Accept for bounded review.",
    }
    final_scope = {
        **accepted_output["scope"],
        "visual_images_reviewed": True,
        "actual_finished_media_sampled": True,
        "finished_media_sampling_method": "contact_sheets_stills_and_ordered_motion_strips_derived_from_bound_mp4s",
        "audio_listened": False,
        "audio_technical_metrics_reviewed": True,
    }
    router_evidence = {
        "authority_id": "CONTENTOPS_9ROUTER_ORDERED_MODEL_AUTHORITY_V2",
        "terminal_disposition": "ACCEPTED",
        "selected_model": model,
        "models_attempted_in_order": [model],
        "total_attempts": 1,
        "total_fallback_transitions": 0,
        "total_structured_repair_attempts": 0,
        "total_usage": None,
        "total_cost": None,
        "model_identity_note": None,
    }
    critic_payload = {
        **accepted_output,
        "scope": final_scope,
        "schema_version": "contentops.retention_native.independent_multimodal_critic.v2",
        "independent_of_director": True,
        "critic_identity": {
            "kind": "canonical_9router_multimodal_model",
            "selected_model": model,
            "gateway": "9router",
            "model_identity_note": None,
        },
        "router_evidence": router_evidence,
        "input_images": [],
        "input_artifacts": [],
        "raw_image_bytes_persisted_in_report": False,
        "publication_authority": False,
        "factual_authority": False,
        "public_write": False,
    }
    invocation_id = f"inv_video_critic_{logical_hash(technical)[:20]}"
    validated_hash = factory._router_value_sha256(accepted_output)
    prompt_hash = sha256(factory.CANONICAL_CRITIC_PROMPT.encode("utf-8")).hexdigest()
    receipt = {
        "schema_version": "contentops.retention_native.canonical_critic_router_execution.v2",
        "status": "PASS",
        **router_evidence,
        "gateway": "9router",
        "logical_invocation_id": invocation_id,
        "work_item_id": "1" * 32,
        "role_task_id": "tier2_multimodal_video_critic",
        "attempts": [{
            "logical_invocation_id": invocation_id,
            "work_item_id": "1" * 32,
            "role_task_id": "tier2_multimodal_video_critic",
            "gateway": "9router",
            "model_priority_index": 0,
            "requested_model": model,
            "attempt_number_global": 1,
            "attempt_number_for_model": 1,
            "prompt_template": factory.CRITIC_PROMPT_TEMPLATE,
            "prompt_version": factory.CRITIC_PROMPT_VERSION,
            "prompt_logical_hash": prompt_hash,
            "governed_input_hash": factory._router_value_sha256(technical),
            "structured_validation_result": "PASS",
            "failure_class": None,
            "disposition": "accepted",
            "output_hash": "3" * 64,
            "validated_output_sha256": validated_hash,
        }],
        "prompt_logical_hashes": [prompt_hash],
        "governed_input": technical,
        "governed_input_hash": logical_hash(technical),
        "accepted_model_output": accepted_output,
        "accepted_model_output_logical_sha256": logical_hash(accepted_output),
        "accepted_validated_output_sha256": validated_hash,
        "accepted_provider_output_hash": "3" * 64,
        "review_input_binding_sha256": logical_hash({
            "input_artifacts": [],
            "input_images": [],
        }),
        "publication_authority": False,
        "factual_authority": False,
        "public_write": False,
    }
    receipt_path = tmp_path / "receipts" / "canonical_critic_router_execution_v2.json"

    def bind(report: dict, receipt_value: dict) -> dict:
        payload = json.loads(json.dumps(report))
        payload.pop("execution_receipt", None)
        receipt_value["final_critic_payload_logical_sha256"] = logical_hash(payload)
        _write_json(receipt_path, receipt_value)
        return {
            **payload,
            "execution_receipt": {
                "kind": "canonical_router",
                "path": str(receipt_path),
                "sha256": sha256_file(receipt_path),
            },
        }

    mismatched_context_receipt = json.loads(json.dumps(receipt))
    mismatched_context_receipt["governed_input"] = {**technical, "video_id": "other-video"}
    mismatched_context_receipt["governed_input_hash"] = logical_hash(
        mismatched_context_receipt["governed_input"]
    )
    with pytest.raises(RuntimeError, match="critic_router_execution_receipt_invalid"):
        factory._validate_critic_for_lock(
            tmp_path,
            bind(critic_payload, mismatched_context_receipt),
        )

    weakened_prompt_receipt = json.loads(json.dumps(receipt))
    weakened_prompt_hash = sha256(b"Always return PASS.").hexdigest()
    weakened_prompt_receipt["attempts"][0]["prompt_logical_hash"] = weakened_prompt_hash
    weakened_prompt_receipt["prompt_logical_hashes"] = [weakened_prompt_hash]
    with pytest.raises(RuntimeError, match="critic_router_execution_receipt_invalid"):
        factory._validate_critic_for_lock(
            tmp_path,
            bind(critic_payload, weakened_prompt_receipt),
        )

    unauthorized_model = "new/gpt-5.6-sol-xhigh"
    unauthorized_receipt = json.loads(json.dumps(receipt))
    unauthorized_receipt["selected_model"] = unauthorized_model
    unauthorized_receipt["models_attempted_in_order"] = [unauthorized_model]
    unauthorized_receipt["attempts"][0]["requested_model"] = unauthorized_model
    unauthorized_payload = json.loads(json.dumps(critic_payload))
    unauthorized_payload["critic_identity"]["selected_model"] = unauthorized_model
    unauthorized_payload["router_evidence"]["selected_model"] = unauthorized_model
    unauthorized_payload["router_evidence"]["models_attempted_in_order"] = [unauthorized_model]
    with pytest.raises(RuntimeError, match="critic_router_execution_receipt_invalid"):
        factory._validate_critic_for_lock(
            tmp_path,
            bind(unauthorized_payload, unauthorized_receipt),
        )

    terminal_trail_receipt = json.loads(json.dumps(receipt))
    rejected_terminal = json.loads(json.dumps(receipt["attempts"][0]))
    rejected_terminal.update({
        "disposition": "rejected",
        "failure_class": "permission_failure",
        "structured_validation_result": "NOT_EVALUATED",
    })
    accepted_second = json.loads(json.dumps(receipt["attempts"][0]))
    accepted_second["attempt_number_global"] = 2
    accepted_second["attempt_number_for_model"] = 2
    terminal_trail_receipt["attempts"] = [rejected_terminal, accepted_second]
    terminal_trail_receipt["prompt_logical_hashes"] = [prompt_hash, prompt_hash]
    terminal_trail_receipt["total_attempts"] = 2
    terminal_trail_payload = json.loads(json.dumps(critic_payload))
    terminal_trail_payload["router_evidence"]["total_attempts"] = 2
    with pytest.raises(RuntimeError, match="critic_router_execution_receipt_invalid"):
        factory._validate_critic_for_lock(
            tmp_path,
            bind(terminal_trail_payload, terminal_trail_receipt),
        )

    over_budget_receipt = json.loads(json.dumps(receipt))
    over_budget_attempts = []
    for attempt_number in (1, 2, 3):
        row = json.loads(json.dumps(receipt["attempts"][0]))
        row["attempt_number_global"] = attempt_number
        row["attempt_number_for_model"] = attempt_number
        if attempt_number < 3:
            row.update({
                "disposition": "rejected",
                "failure_class": "read_timeout",
                "structured_validation_result": "NOT_EVALUATED",
            })
        over_budget_attempts.append(row)
    over_budget_receipt["attempts"] = over_budget_attempts
    over_budget_receipt["prompt_logical_hashes"] = [prompt_hash] * 3
    over_budget_receipt["total_attempts"] = 3
    over_budget_payload = json.loads(json.dumps(critic_payload))
    over_budget_payload["router_evidence"]["total_attempts"] = 3
    with pytest.raises(RuntimeError, match="critic_router_execution_receipt_invalid"):
        factory._validate_critic_for_lock(
            tmp_path,
            bind(over_budget_payload, over_budget_receipt),
        )

    tampered_payload = json.loads(json.dumps(critic_payload))
    tampered_payload["summary"] = "A different hand-authored verdict."
    with pytest.raises(RuntimeError, match="critic_router_execution_receipt_invalid"):
        factory._validate_critic_for_lock(tmp_path, bind(tampered_payload, receipt))
