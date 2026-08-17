from __future__ import annotations

import json
import math
import os
import threading
from dataclasses import replace
from pathlib import Path

import pytest

from live_contentops.nine_router_llm_seam_v2 import (
    RoutedInvocationError,
    routed_v2_creative_invocation,
)
from live_contentops.nine_router_ordered_model_router_v2 import (
    V1_GROUNDED_RESEARCH_MODEL_LADDER,
)
from video.unattended_core_factory_v1.codex_job_brain import (
    CodexCliExecutor,
    CodexJobBrainError,
)
from video.unattended_core_factory_v1.creative import (
    CreativeContractError,
    hash_file,
    hash_value,
    materialize_source,
    validate_editor_artifact,
    validate_input_packet,
    validate_narration_timing_lock,
    validate_source_files,
)
from video.unattended_core_factory_v1.desktop_session import (
    CODEX_MODEL,
    CREATIVE_EXECUTION_PLANE,
    CREATIVE_REASONING_EFFORT,
    CREATIVE_RUNTIME,
    PARENT_EXECUTION_PLANE,
    PARENT_REASONING_EFFORT,
    PARENT_RUNTIME,
    BoundedCreativeProvenance,
    ParentSessionProvenance,
)
from video.unattended_core_factory_v1.store import V2JobStore
from video.unattended_core_factory_v1.media import (
    REMOTION_BROWSER_RELATIVE,
    resolve_remotion_browser_executable,
)
from video.unattended_core_factory_v1.supervisor import (
    DesktopSessionV2Factory,
    FactoryConfig,
    STAGES,
    SupervisorError,
)


REPO = Path(__file__).resolve().parents[1]
PACKET_PATH = (
    REPO
    / "video"
    / "unattended_core_factory_v1"
    / "frozen_without_breaking_proof_input_v1.json"
)
PARENT = ParentSessionProvenance(session_label="test-high-parent-session")
EDITORIAL_CREATIVE = BoundedCreativeProvenance(
    parent=PARENT,
    execution_label="test-editorial-xhigh-creative",
    native_child_task_id="test-child-editorial",
)
MOTION_CREATIVE = BoundedCreativeProvenance(
    parent=PARENT,
    execution_label="test-motion-xhigh-creative",
    native_child_task_id="test-child-motion",
)
EDITORIAL_REVISION = BoundedCreativeProvenance(
    parent=PARENT,
    execution_label="test-editorial-timing-revision",
    native_child_task_id="test-child-editorial-revision",
)
MEDIA_REVIEW = BoundedCreativeProvenance(
    parent=PARENT,
    execution_label="test-xhigh-media-review",
    native_child_task_id="test-child-review",
)


def packet() -> dict[str, object]:
    return json.loads(PACKET_PATH.read_text(encoding="utf-8"))


def editor_artifact() -> dict[str, object]:
    p = packet()
    anchors = {item["anchor_id"]: item["statement"] for item in p["anchors"]}
    analysis = {item["analysis_id"]: item["statement"] for item in p["permitted_analysis"]}
    segments = [
        {"segment_id": "s1", "kind": "ENGAGEMENT", "text": "The headline moved. The market did not break.", "anchor_ids": [], "analysis_id": ""},
        {"segment_id": "s2", "kind": "FACT", "text": anchors["EMP001"], "anchor_ids": ["EMP001"], "analysis_id": ""},
        {"segment_id": "s3", "kind": "FACT", "text": anchors["EMP002"], "anchor_ids": ["EMP002"], "analysis_id": ""},
        {"segment_id": "s4", "kind": "FACT", "text": anchors["JOL002"], "anchor_ids": ["JOL002"], "analysis_id": ""},
        {"segment_id": "s5", "kind": "ANALYSIS", "text": analysis["ANALYSIS_STASIS"], "anchor_ids": [], "analysis_id": "ANALYSIS_STASIS"},
        {"segment_id": "s6", "kind": "ENGAGEMENT", "text": "Watch the motion, not just the level.", "anchor_ids": [], "analysis_id": ""},
    ]
    return {
        "schema": "contentops.v2.codex_job_editorial.v2",
        "title": "Frozen Without Breaking",
        "viewer_promise": "See why low motion differs from collapse.",
        "narration_segments": segments,
        "editorial_structure": ["hook", "evidence", "mechanism", "watch condition"],
        "audio_intent": {
            "bed_asset_id": "ACCEPTED_AUDIO_BED",
            "bed_gain_db": -27,
            "narration_voice": "af_heart",
            "speed": 1.06,
            "lang": "en-us",
        },
    }


def source_files(*, duration_frames: int = 1050) -> dict[str, str]:
    return {
        "src/index.tsx": "import {registerRoot} from 'remotion';\nimport {Root} from './Root';\nregisterRoot(Root);",
        "src/Root.tsx": f"import React from 'react';\nimport {{Composition}} from 'remotion';\nimport {{Short}} from './Short';\nexport const Root: React.FC=()=> <Composition id='FWBUnattendedShort' component={{Short}} durationInFrames={{{duration_frames}}} fps={{30}} width={{1080}} height={{1920}}/>;",
        "src/Short.tsx": "import React from 'react';\nimport {AbsoluteFill,OffthreadVideo,interpolate,staticFile,useCurrentFrame} from 'remotion';\nexport const Short: React.FC=()=>{const f=useCurrentFrame();const o=interpolate(f,[0,30],[0,1],{extrapolateRight:'clamp'});return <AbsoluteFill style={{background:'#071116',color:'#f5f0e6',justifyContent:'center',alignItems:'center',opacity:o,fontSize:72}}><OffthreadVideo muted src={staticFile('assets/documentary/commuters_subway_cc0_pexels_855749.mp4')}/><div>FROZEN / MOVING?</div></AbsoluteFill>};",
    }


def motion_artifact(timing_lock: dict[str, object]) -> dict[str, object]:
    actual = float(timing_lock["actual_total_narration_duration_seconds"])
    tail_room = 0.67
    frames = math.ceil((actual + tail_room) * 30 - 0.0000001)
    return {
        "schema": "contentops.v2.codex_job_motion_source.v1",
        "composition_id": "FWBUnattendedShort",
        "duration_seconds": frames / 30,
        "narration_timing_lock_hash": timing_lock["timing_lock_hash"],
        "picture_timing": {
            "fps": 30,
            "authored_head_room_seconds": timing_lock["initial_silence_seconds"],
            "authored_tail_room_seconds": tail_room,
            "duration_frames": frames,
        },
        "asset_ids": ["COMMUTER_FLOW"],
        "source_claim_bindings": [],
        "files": source_files(duration_frames=frames),
    }


def review_artifact(*, material: bool = False) -> dict[str, object]:
    return {
        "schema": "contentops.v2.codex_actual_media_review.v1",
        "decision": "MATERIAL_REVISION_REQUIRED" if material else "NO_MATERIAL_REVISION",
        "summary": "The proxy is coherent enough for owner review." if not material else "A material hierarchy correction is required.",
        "defects": [] if not material else [{"severity": "MAJOR", "time_range": "0-4", "description": "Hierarchy", "repair": "Clarify hook"}],
        "source_claim_bindings": [],
        "replacement_files": source_files() if material else {},
    }


def _artifact(path: Path) -> dict[str, object]:
    return {"path": str(path.resolve()), "sha256": hash_file(path), "size_bytes": path.stat().st_size}


class FakeMedia:
    def __init__(
        self,
        *,
        fail_typecheck: bool = False,
        segment_duration: float = 5.5,
        picture_duration_override: float | None = None,
    ) -> None:
        self.render_count = 0
        self.fail_typecheck = fail_typecheck
        self.segment_duration = segment_duration
        self.picture_duration_override = picture_duration_override
        self.motion_duration = 35.0
        self.synthesis_count = 0
        self.mix_timing_lock_hash = None
        self.caption_segments = None

    def prepare_project(self, **kwargs):
        kwargs["project_root"].mkdir(parents=True, exist_ok=True)
        return {"result": "PASS_PROJECT_SCAFFOLD"}

    def validate_assets(self, packet, asset_root):
        return {"result": "PASS_ASSET_HASHES_AND_RIGHTS_BINDING", "assets": []}

    def typecheck_project(self, project_root: Path):
        if self.fail_typecheck:
            raise RuntimeError("injected_typecheck_failure")
        return {"result": "PASS_GENERATED_SOURCE_TYPECHECK"}

    def resolve_remotion_browser_executable(self, dependency_root: Path):
        browser = dependency_root / "chrome-headless-shell.exe"
        browser.write_bytes(b"browser")
        return browser

    def render_project(self, *, project_root: Path, output: Path, crf: int, browser_executable: Path, public_root: Path):
        self.render_count += 1
        root_source = (project_root / "src" / "Root.tsx").read_text(encoding="utf-8")
        frames = int(root_source.split("durationInFrames={", 1)[1].split("}", 1)[0])
        self.motion_duration = frames / 30
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(f"render-{self.render_count}-crf-{crf}".encode())
        return {"result": "PASS_RENDER", "artifact": _artifact(output), "wall_time_seconds": 0.1}

    def contact_sheet(self, video: Path, output: Path):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"fake-jpeg")
        return {"result": "PASS_CONTACT_SHEET", "artifact": _artifact(output)}

    def probe_media(self, path: Path):
        duration = (
            self.picture_duration_override
            if self.picture_duration_override is not None and path.name == "picture_lock.mp4"
            else self.motion_duration
        )
        return {"streams": [{"codec_type": "video", "width": 1080, "height": 1920, "r_frame_rate": "30/1"}], "format": {"duration": str(duration)}}

    def synthesize_narration(self, *, editor, model_path, voices_path, output_dir):
        self.synthesis_count += 1
        output_dir.mkdir(parents=True, exist_ok=True)
        narration = output_dir / "narration.wav"
        narration.write_bytes(b"narration")
        placements = []
        cursor = 0.18
        for index, item in enumerate(editor["narration_segments"], start=1):
            segment = output_dir / f"segment_{index:02d}_{item['segment_id']}.wav"
            segment.write_bytes(f"segment-{item['segment_id']}-{item['text']}".encode())
            pause = 0.16 if index < len(editor["narration_segments"]) else 0.35
            placements.append({
                "cue_id": item["segment_id"],
                "segment_id": item["segment_id"],
                "segment_text_sha256": hash_value(item["text"]),
                "timeline_start_seconds": round(cursor, 6),
                "actual_audio_duration_seconds": self.segment_duration,
                "timeline_end_seconds": round(cursor + self.segment_duration, 6),
                "pause_after_seconds": pause,
                "caption_text": item["text"],
                "audio_path": str(segment.resolve()),
                "audio": _artifact(segment),
            })
            cursor += self.segment_duration + pause
        return {
            "provider": "kokoro-onnx",
            "model": "kokoro-v1.0",
            "voice": "af_heart",
            "speed": 1.06,
            "lang": "en-us",
            "sample_rate_hz": 24000,
            "duration_seconds": round(cursor, 6),
            "initial_silence_seconds": 0.18,
            "placements": placements,
            "artifact": _artifact(narration),
            "external_cost_usd": 0.0,
        }

    def build_audio_mix(self, *, picture, timing_lock, bed_path, output_dir):
        self.mix_timing_lock_hash = timing_lock["timing_lock_hash"]
        output_dir.mkdir(parents=True, exist_ok=True)
        mix = output_dir / "final_mix.wav"
        mix.write_bytes(b"mix")
        return {"result": "PASS_AUDIO_MIX", "mix": _artifact(mix)}

    def mux_final_media(self, *, picture, mix, output):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"final-media")
        return {"result": "PASS_FINAL_MUX", "final_media": _artifact(output)}

    def build_captions(self, *, timing_lock, media_duration_seconds, output_dir):
        self.caption_segments = timing_lock["segments"]
        output_dir.mkdir(parents=True, exist_ok=True)
        values = {}
        for kind in ("json", "srt", "vtt"):
            path = output_dir / f"captions.en.{kind}"
            path.write_text("{}" if kind == "json" else "caption", encoding="utf-8")
            values[kind] = _artifact(path)
        return {"result": "PASS_CAPTIONS", "artifacts": values}

    def technical_media_report(self, path, output):
        result = {"artifact": _artifact(path), "probe": self.probe_media(path), "media_validation": {"result": "PASS_MEDIA_CONTRACT", "duration_seconds": 36}, "loudness": {"integrated_lufs": -16.0, "true_peak_dbfs": -1.5}}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result), encoding="utf-8")
        result["report_artifact"] = _artifact(output)
        return result

    def build_neutral_package(self, *, output, final_media, **kwargs):
        result = {"package_id": "pkg_test", "final_mux": _artifact(final_media)}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result), encoding="utf-8")
        result["manifest_artifact"] = _artifact(output)
        return result


def make_factory(tmp_path: Path, *, media=None) -> tuple[DesktopSessionV2Factory, V2JobStore, str]:
    runtime = tmp_path / "runtime"
    store = V2JobStore(runtime / "jobs.sqlite3")
    p = packet()
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(p), encoding="utf-8")
    job_id = "job_test"
    store.seed_job(video_job_id=job_id, input_packet_path=input_path, input_packet_hash=hash_value(p), target_format="SHORT_9_16_1080X1920_30FPS")
    scaffold = tmp_path / "scaffold"
    dependency = tmp_path / "deps"
    assets = tmp_path / "assets-root"
    scaffold.mkdir()
    dependency.mkdir()
    (assets / "assets" / "audio" / "sound").mkdir(parents=True)
    (assets / "assets" / "audio" / "sound" / "chapter_02_bed.m4a").write_bytes(b"bed")
    model = tmp_path / "kokoro.onnx"
    voices = tmp_path / "voices.bin"
    model.write_bytes(b"model")
    voices.write_bytes(b"voices")
    config = FactoryConfig(runtime_root=runtime, scaffold_root=scaffold, dependency_root=dependency, asset_root=assets, kokoro_model=model, kokoro_voices=voices, implementation_head="a" * 40, worker_id="worker", parent_provenance=PARENT)
    return DesktopSessionV2Factory(store=store, config=config, media_backend=media or FakeMedia()), store, job_id


def start_and_submit(factory: DesktopSessionV2Factory) -> tuple[str, str]:
    started = factory.run_once(proof_run_started_at="2026-08-17T00:00:00Z")
    assert started["result"] == "AWAITING_CODEX_DESKTOP_SESSION_INPUT"
    assert started["required_input"] == "EDITORIAL_NARRATION"
    factory.submit_editorial_narration(
        video_job_id=started["video_job_id"],
        run_id=started["run_id"],
        editor=editor_artifact(),
        provenance=EDITORIAL_CREATIVE,
    )
    timing = factory.resume(video_job_id=started["video_job_id"], run_id=started["run_id"])
    assert timing["required_input"] == "MOTION_VISUAL_AUTHORSHIP"
    lock_path = (
        factory.config.runtime_root
        / "jobs"
        / started["video_job_id"]
        / "artifacts"
        / "actual_narration_timing_lock.json"
    )
    timing_lock = json.loads(lock_path.read_text(encoding="utf-8"))
    factory.submit_motion_visual(
        video_job_id=started["video_job_id"],
        run_id=started["run_id"],
        motion=motion_artifact(timing_lock),
        provenance=MOTION_CREATIVE,
    )
    return started["video_job_id"], started["run_id"]


def complete(factory: DesktopSessionV2Factory, *, material: bool = False) -> dict[str, object]:
    job_id, run_id = start_and_submit(factory)
    proxy = factory.resume(video_job_id=job_id, run_id=run_id)
    assert proxy["required_input"] == "ACTUAL_MEDIA_REVIEW"
    factory.submit_actual_media_review(video_job_id=job_id, run_id=run_id, review=review_artifact(material=material), provenance=MEDIA_REVIEW)
    return factory.resume(video_job_id=job_id, run_id=run_id)


def locked_timing(factory: DesktopSessionV2Factory, video_job_id: str) -> dict[str, object]:
    path = (
        factory.config.runtime_root
        / "jobs"
        / video_job_id
        / "artifacts"
        / "actual_narration_timing_lock.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_governed_packet_is_isolated_and_zero_write() -> None:
    result = validate_input_packet(packet())
    assert result["result"] == "PASS_GOVERNED_INPUT"
    assert all(value is False for value in packet()["hard_boundaries"].values())


def test_active_factory_is_high_parent_bounded_xhigh_and_has_no_external_creative_invoker() -> None:
    assert (PARENT_RUNTIME, PARENT_EXECUTION_PLANE, CODEX_MODEL, PARENT_REASONING_EFFORT) == (
        "CODEX_DESKTOP_APP_PARENT_TASK_SESSION",
        "CODEX_DESKTOP_APP_TASK_SESSION",
        "gpt-5.6-sol",
        "high",
    )
    assert (CREATIVE_RUNTIME, CREATIVE_EXECUTION_PLANE, CREATIVE_REASONING_EFFORT) == (
        "CODEX_DESKTOP_APP_BOUNDED_VIDEO_CREATIVE_REASONING",
        "CODEX_DESKTOP_APP_BOUNDED_REASONING",
        "xhigh",
    )
    for relative in (
        "scripts/run_v2_unattended_core_factory_v1.py",
        "video/unattended_core_factory_v1/desktop_session.py",
        "video/unattended_core_factory_v1/supervisor.py",
    ):
        source = (REPO / relative).read_text(encoding="utf-8")
        assert "CodexCliExecutor" not in source
        assert "routed_v2_creative_invocation" not in source
        assert "subprocess" not in source or relative.startswith("scripts/")


def test_historical_cli_creative_seam_fails_closed_before_runner_use() -> None:
    with pytest.raises(CodexJobBrainError, match="CODEX_CLI_NOT_V2_CREATIVE_AUTHORITY"):
        CodexCliExecutor()


def test_v1_research_ladder_is_unchanged_and_v2_9router_creative_fails_closed() -> None:
    assert V1_GROUNDED_RESEARCH_MODEL_LADDER == (
        "cx/gpt-5.6-terra(high)",
        "vx/gemini-3.1-pro-preview(high)",
        "vx/gemini-3.5-flash(high)",
    )
    calls = 0

    def forbidden_provider(*args, **kwargs):
        nonlocal calls
        calls += 1

    with pytest.raises(RoutedInvocationError):
        routed_v2_creative_invocation(prompt="retired", role_task_id="V2_CREATIVE_EDITOR", logical_invocation_id="retired", work_item_id="retired", provider_call=forbidden_provider)
    assert calls == 0


def test_factual_gate_and_sandbox_remain_fail_closed() -> None:
    value = editor_artifact()
    value["narration_segments"][1]["text"] = "Payrolls collapsed."
    with pytest.raises(CreativeContractError, match="not_exact_anchor"):
        validate_editor_artifact(value, packet())
    files = source_files()
    files["src/Short.tsx"] += "\nfetch('x')"
    with pytest.raises(CreativeContractError, match="sandbox_violation"):
        validate_source_files(files)


def test_remotion_browser_resolves_from_canonical_dependency_root(tmp_path: Path) -> None:
    dependency = tmp_path / "deps"
    browser = dependency / REMOTION_BROWSER_RELATIVE
    browser.parent.mkdir(parents=True)
    browser.write_bytes(b"browser")
    resolved = resolve_remotion_browser_executable(dependency)
    assert resolved == browser.resolve()
    assert "generated_project" not in str(resolved)


def test_atomic_claim_race_has_one_owner(tmp_path: Path) -> None:
    db = tmp_path / "race.sqlite3"
    store = V2JobStore(db)
    source = tmp_path / "input.json"
    source.write_text("{}", encoding="utf-8")
    store.seed_job(video_job_id="race", input_packet_path=source, input_packet_hash="f" * 64, target_format="SHORT")
    barrier = threading.Barrier(2)
    results = []

    def claim(worker: str) -> None:
        barrier.wait()
        results.append(V2JobStore(db).claim_next(worker_id=worker, implementation_head="a" * 40))

    threads = [threading.Thread(target=claim, args=(name,)) for name in ("a", "b")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert sum(item is not None for item in results) == 1


def test_parent_high_session_continuity_is_hash_locked(tmp_path: Path) -> None:
    factory, store, _ = make_factory(tmp_path)
    started = factory.run_once()
    drifted_parent = ParentSessionProvenance(session_label="different-high-parent")
    drifted = DesktopSessionV2Factory(
        store=store,
        config=replace(factory.config, parent_provenance=drifted_parent),
        media_backend=factory.media,
    )
    with pytest.raises(Exception, match="parent_high_session_continuity_mismatch"):
        drifted.submit_editorial_narration(
            video_job_id=started["video_job_id"],
            run_id=started["run_id"],
            editor=editor_artifact(),
            provenance=BoundedCreativeProvenance(
                parent=drifted_parent,
                execution_label="drifted",
            ),
        )


def test_stage_events_are_append_only(tmp_path: Path) -> None:
    factory, store, job_id = make_factory(tmp_path)
    factory.run_once()
    with store.connect() as connection, pytest.raises(Exception, match="append_only"):
        connection.execute("UPDATE stage_events SET result='tampered'")


def test_motion_before_actual_narration_timing_lock_is_rejected(tmp_path: Path) -> None:
    factory, _, _ = make_factory(tmp_path)
    started = factory.run_once()
    with pytest.raises(
        SupervisorError, match="actual_narration_timing_lock_required_before_motion"
    ):
        factory.submit_motion_visual(
            video_job_id=started["video_job_id"],
            run_id=started["run_id"],
            motion={},
            provenance=MOTION_CREATIVE,
        )


def test_timing_lock_editorial_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    factory, _, _ = make_factory(tmp_path)
    video_job_id, run_id = start_and_submit(factory)
    timing = locked_timing(factory, video_job_id)
    changed_editor = editor_artifact()
    changed_editor["narration_segments"][0]["text"] += " Changed."
    with pytest.raises(CreativeContractError, match="editorial_narration_hash"):
        validate_narration_timing_lock(
            timing,
            video_job_id=video_job_id,
            run_id=run_id,
            governed_input_hash=hash_value(packet()),
            editor=changed_editor,
        )


def test_timing_lock_segment_text_and_audio_hash_mismatches_are_rejected(
    tmp_path: Path,
) -> None:
    factory, _, _ = make_factory(tmp_path)
    video_job_id, run_id = start_and_submit(factory)
    timing = locked_timing(factory, video_job_id)
    bad_text = json.loads(json.dumps(timing))
    bad_text["segments"][0]["segment_text_sha256"] = "0" * 64
    unsigned = dict(bad_text)
    unsigned.pop("timing_lock_hash")
    bad_text["timing_lock_hash"] = hash_value(unsigned)
    with pytest.raises(CreativeContractError, match="text_hash_mismatch"):
        validate_narration_timing_lock(
            bad_text,
            video_job_id=video_job_id,
            run_id=run_id,
            governed_input_hash=hash_value(packet()),
            editor=editor_artifact(),
        )
    Path(timing["segments"][0]["audio"]["path"]).write_bytes(b"tampered")
    with pytest.raises(CreativeContractError, match="audio_hash_mismatch"):
        validate_narration_timing_lock(
            timing,
            video_job_id=video_job_id,
            run_id=run_id,
            governed_input_hash=hash_value(packet()),
            editor=editor_artifact(),
        )


def test_actual_timing_within_short_contract_locks_before_motion(tmp_path: Path) -> None:
    factory, store, _ = make_factory(tmp_path)
    video_job_id, run_id = start_and_submit(factory)
    factory.resume(video_job_id=video_job_id, run_id=run_id, max_new_stages=1)
    timing = locked_timing(factory, video_job_id)
    assert timing["actual_total_narration_duration_seconds"] < 60
    passed = [event["stage"] for event in store.events(video_job_id) if event["result"].startswith("PASS")]
    assert passed.index("ACTUAL_NARRATION_TIMING_LOCKED") < passed.index("MOTION_SOURCE_LOCKED")


def test_over_sixty_seconds_gets_one_revision_then_quarantines_before_render(
    tmp_path: Path,
) -> None:
    media = FakeMedia(segment_duration=10.0)
    factory, store, _ = make_factory(tmp_path, media=media)
    started = factory.run_once()
    factory.submit_editorial_narration(
        video_job_id=started["video_job_id"],
        run_id=started["run_id"],
        editor=editor_artifact(),
        provenance=EDITORIAL_CREATIVE,
    )
    pending = factory.resume(
        video_job_id=started["video_job_id"], run_id=started["run_id"]
    )
    assert pending["required_input"] == "EDITORIAL_TIMING_REVISION"
    assert media.render_count == 0
    factory.submit_editorial_timing_revision(
        video_job_id=started["video_job_id"],
        run_id=started["run_id"],
        editor=editor_artifact(),
        provenance=EDITORIAL_REVISION,
    )
    with pytest.raises(SupervisorError, match="still_outside_short_contract"):
        factory.resume(
            video_job_id=started["video_job_id"], run_id=started["run_id"]
        )
    assert store.job(started["video_job_id"])["state"] == "QUARANTINED"
    assert media.render_count == 0


def test_picture_cannot_end_before_locked_narration(tmp_path: Path) -> None:
    media = FakeMedia(picture_duration_override=34.0)
    factory, store, _ = make_factory(tmp_path, media=media)
    job_id, run_id = start_and_submit(factory)
    proxy = factory.resume(video_job_id=job_id, run_id=run_id)
    factory.submit_actual_media_review(
        video_job_id=job_id,
        run_id=run_id,
        review=review_artifact(),
        provenance=MEDIA_REVIEW,
    )
    with pytest.raises(SupervisorError, match="picture_ends_before_locked_narration"):
        factory.resume(video_job_id=job_id, run_id=run_id)
    assert store.job(job_id)["state"] == "QUARANTINED"
    assert proxy["required_input"] == "ACTUAL_MEDIA_REVIEW"


def test_session_artifact_e2e_reaches_owner_review_without_live_creative_provider(tmp_path: Path) -> None:
    media = FakeMedia()
    factory, store, job_id = make_factory(tmp_path, media=media)
    result = complete(factory)
    assert result["job"]["state"] == "OWNER_REVIEW_READY"
    assert result["job"]["terminal_result"] == "PASS_IMPLEMENTATION_ACTUAL_NARRATION_TIMING_LOCK_V2_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW"
    provenance = [json.loads(event["model_provenance_json"]) for event in store.events(job_id)]
    creative = [
        item
        for item in provenance
        if item.get("execution_kind") in {
            "EDITORIAL_NARRATION",
            "MOTION_VISUAL_AUTHORSHIP",
            "ACTUAL_MEDIA_REVIEW",
        }
    ]
    assert len(creative) == 3
    assert all(item["parent_reasoning_effort"] == "high" for item in creative)
    assert all(item["declared_creative_reasoning_effort"] == "xhigh" for item in creative)
    assert all(item["all_session_xhigh"] is False for item in creative)
    assert all(item["mechanical_work_performed"] is False for item in creative)
    assert all(item["cli_invocation_count"] == item["sdk_api_invocation_count"] == item["provider_creative_invocation_count"] == 0 for item in creative)
    timing = locked_timing(factory, job_id)
    assert media.synthesis_count == 1
    assert media.mix_timing_lock_hash == timing["timing_lock_hash"]
    assert media.caption_segments == timing["segments"]


def test_restart_and_checkpoint_invalidation_remain_correct(tmp_path: Path) -> None:
    factory, store, job_id = make_factory(tmp_path)
    video_job_id, run_id = start_and_submit(factory)
    partial = factory.resume(video_job_id=video_job_id, run_id=run_id, max_new_stages=1)
    assert partial["last_valid_checkpoint"] == "MOTION_SOURCE_LOCKED"
    motion_path = factory.config.runtime_root / "jobs" / job_id / "artifacts" / "motion_source.json"
    motion_path.write_text("{}", encoding="utf-8")
    result = factory.run_once()
    assert result["required_input"] == "ACTUAL_MEDIA_REVIEW"
    assert any(event["result"].startswith("INVALIDATED") and event["stage"] == "MOTION_SOURCE_LOCKED" for event in store.events(job_id))


def test_material_same_session_revision_is_bounded_and_typechecked(tmp_path: Path) -> None:
    media = FakeMedia()
    factory, _, _ = make_factory(tmp_path, media=media)
    result = complete(factory, material=True)
    assert result["job"]["state"] == "OWNER_REVIEW_READY"
    assert media.render_count == 2


def test_hard_deterministic_failure_quarantines_and_is_terminal(tmp_path: Path) -> None:
    factory, store, job_id = make_factory(tmp_path, media=FakeMedia(fail_typecheck=True))
    video_job_id, run_id = start_and_submit(factory)
    with pytest.raises(RuntimeError, match="injected_typecheck_failure"):
        factory.resume(video_job_id=video_job_id, run_id=run_id)
    assert store.job(job_id)["state"] == "QUARANTINED"
    assert factory.run_once()["result"] == "NO_ELIGIBLE_JOB"


def test_duplicate_job_run_and_terminal_execution_are_idempotent(tmp_path: Path) -> None:
    factory, store, job_id = make_factory(tmp_path)
    second = store.seed_job(video_job_id="other", input_packet_path=PACKET_PATH, input_packet_hash=hash_value(packet()), target_format="SHORT_9_16_1080X1920_30FPS")
    assert second["video_job_id"] == job_id
    complete(factory)
    count = len(store.events(job_id))
    assert factory.run_once()["result"] == "NO_ELIGIBLE_JOB"
    assert len(store.events(job_id)) == count


def test_legal_stage_order_zero_write_and_owner_bundle_truth(tmp_path: Path) -> None:
    factory, store, job_id = make_factory(tmp_path)
    complete(factory)
    passed = [event["stage"] for event in store.events(job_id) if event["result"].startswith("PASS")]
    assert passed == [stage for stage in STAGES if stage != "CREATIVE_REVISION_LOCKED"]
    assert store.job(job_id)["public_write_authority"] == 0
    assert all(event["public_write_authority"] == 0 for event in store.events(job_id))
    root = factory.config.runtime_root / "jobs" / job_id
    safety = json.loads((root / "review" / "zero_write_safety_summary.json").read_text(encoding="utf-8"))
    assert all(value == 0 or value is False for key, value in safety.items() if key != "schema")
    bundle = json.loads((root / "review" / "owner_review_bundle.json").read_text(encoding="utf-8"))
    assert bundle["owner_acceptance_claimed"] is False
    assert bundle["creative_runtime"] == CREATIVE_RUNTIME
    assert bundle["parent_runtime"] == PARENT_RUNTIME
    assert bundle["parent_reasoning_effort"] == "high"
    assert bundle["creative_reasoning_effort"] == "xhigh"
    assert bundle["all_session_xhigh"] is False
    assert bundle["xhigh_mechanical_work_execution_count"] == 0
    assert bundle["creative_cli_invocations"] == bundle["creative_sdk_api_invocations"] == bundle["creative_9router_invocations"] == 0
    assert bundle["unattended"]["manual_source_edits_after_start"] == 0


def test_real_generated_source_typecheck_and_asset_hashes_when_configured(tmp_path: Path) -> None:
    dependency = os.environ.get("V2_REMOTION_DEPENDENCY_ROOT")
    assets = os.environ.get("V2_FWB_ACCEPTED_ASSET_ROOT")
    if not dependency or not assets:
        pytest.skip("real accepted V2 media roots not configured")
    from video.unattended_core_factory_v1 import media

    project = tmp_path / "generated_project"
    materialize_source(source_files(), project)
    media.prepare_project(
        project_root=project,
        scaffold_root=REPO / "video" / "unattended_core_factory_v1" / "scaffold",
        dependency_root=Path(dependency),
        asset_root=Path(assets),
    )
    assert media.validate_assets(packet(), Path(assets))["result"] == "PASS_ASSET_HASHES_AND_RIGHTS_BINDING"
    assert media.typecheck_project(project)["result"] == "PASS_GENERATED_SOURCE_TYPECHECK"
