from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from live_contentops.nine_router_ordered_model_router_v2 import (
    V1_GROUNDED_RESEARCH_MODEL_LADDER,
)
from live_contentops.nine_router_llm_seam_v2 import (
    RoutedInvocationError,
    routed_v2_creative_invocation,
)
from video.unattended_core_factory_v1.codex_job_brain import (
    CODEX_MODEL,
    CODEX_REASONING_EFFORT,
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
    validate_source_files,
)
from video.unattended_core_factory_v1.store import V2JobStore
from video.unattended_core_factory_v1.supervisor import (
    FactoryConfig,
    STAGES,
    UnattendedV2Supervisor,
)


REPO = Path(__file__).resolve().parents[1]
PACKET_PATH = (
    REPO
    / "video"
    / "unattended_core_factory_v1"
    / "frozen_without_breaking_proof_input_v1.json"
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
    shots = [
        {"shot_id": "a", "start_seconds": 0, "end_seconds": 10, "viewer_takeaway": "hook", "visual_concept": "flow", "asset_ids": ["COMMUTER_FLOW"], "narration_segment_ids": ["s1", "s2"], "on_screen_segment_ids": ["s2"]},
        {"shot_id": "b", "start_seconds": 10, "end_seconds": 22, "viewer_takeaway": "paradox", "visual_concept": "counter", "asset_ids": ["EMPTY_OFFICE"], "narration_segment_ids": ["s3", "s4"], "on_screen_segment_ids": ["s3", "s4"]},
        {"shot_id": "c", "start_seconds": 22, "end_seconds": 36, "viewer_takeaway": "close", "visual_concept": "doors", "asset_ids": ["JOB_INTERVIEW"], "narration_segment_ids": ["s5", "s6"], "on_screen_segment_ids": ["s5"]},
    ]
    return {
        "schema": "contentops.v2.codex_job_editorial.v1",
        "title": "Frozen Without Breaking",
        "viewer_promise": "See why low motion differs from collapse.",
        "duration_seconds": 36,
        "narration_segments": segments,
        "shots": shots,
        "audio_intent": {
            "bed_asset_id": "ACCEPTED_AUDIO_BED",
            "bed_gain_db": -27,
            "narration_voice": "af_heart",
            "speed": 1.06,
            "lang": "en-us",
        },
    }


def source_files() -> dict[str, str]:
    return {
        "src/index.tsx": "import {registerRoot} from 'remotion';\nimport {Root} from './Root';\nregisterRoot(Root);",
        "src/Root.tsx": "import React from 'react';\nimport {Composition} from 'remotion';\nimport {Short} from './Short';\nexport const Root: React.FC=()=> <Composition id='FWBUnattendedShort' component={Short} durationInFrames={1080} fps={30} width={1080} height={1920}/>;",
        "src/Short.tsx": "import React from 'react';\nimport {AbsoluteFill,OffthreadVideo,interpolate,staticFile,useCurrentFrame} from 'remotion';\nexport const Short: React.FC=()=>{const f=useCurrentFrame();const o=interpolate(f,[0,30],[0,1],{extrapolateRight:'clamp'});return <AbsoluteFill style={{background:'#071116',color:'#f5f0e6',justifyContent:'center',alignItems:'center',opacity:o,fontSize:72}}><OffthreadVideo muted src={staticFile('assets/documentary/commuters_subway_cc0_pexels_855749.mp4')}/><div>FROZEN / MOVING?</div></AbsoluteFill>};",
    }


def motion_artifact() -> dict[str, object]:
    return {
        "schema": "contentops.v2.codex_job_motion_source.v1",
        "composition_id": "FWBUnattendedShort",
        "duration_seconds": 36,
        "asset_ids": ["COMMUTER_FLOW"],
        "source_claim_bindings": [],
        "files": source_files(),
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


class FakeCodexJobBrain:
    def __init__(self, *, material_revision: bool = False) -> None:
        self.create_count = 0
        self.review_count = 0
        self.material_revision = material_revision

    def create(self, **kwargs):
        self.create_count += 1
        editor = editor_artifact()
        motion = motion_artifact()
        return editor, motion, {
            "schema": "contentops.v2.codex_job_brain_receipt.v1",
            "execution_plane": "CODEX_CLI_EXEC_FAKE",
            "execution_kind": "INITIAL_CREATIVE",
            "requested_model_family": CODEX_MODEL,
            "requested_reasoning_effort": CODEX_REASONING_EFFORT,
            "actual_model_family": CODEX_MODEL,
            "actual_reasoning_effort": CODEX_REASONING_EFFORT,
            "thread_id": f"thread-{kwargs['video_job_id']}",
            "fresh_isolated_context": True,
            "resumed_same_job_thread": False,
            "input_artifact_hashes": {"governed_packet": hash_value(kwargs["packet"])},
            "output_artifact_hashes": {
                "editorial": hash_value(editor),
                "motion": hash_value(motion),
            },
            "attempt_count": 1,
            "fallback_count": 0,
            "nine_router_route": None,
            "usage": {"total_tokens": 100},
            "cost": None,
            "public_write_authority": False,
        }

    def review(self, **kwargs):
        self.review_count += 1
        review = review_artifact(material=self.material_revision)
        return review, {
            "schema": "contentops.v2.codex_job_brain_receipt.v1",
            "execution_plane": "CODEX_CLI_EXEC_FAKE",
            "execution_kind": "ACTUAL_MEDIA_REVIEW",
            "requested_model_family": CODEX_MODEL,
            "requested_reasoning_effort": CODEX_REASONING_EFFORT,
            "actual_model_family": CODEX_MODEL,
            "actual_reasoning_effort": CODEX_REASONING_EFFORT,
            "thread_id": kwargs["initial_receipt"]["thread_id"],
            "fresh_isolated_context": False,
            "resumed_same_job_thread": True,
            "input_artifact_hashes": {"proxy": hash_file(kwargs["contact_sheet"])},
            "output_artifact_hashes": {"review": hash_value(review)},
            "attempt_count": 1,
            "fallback_count": 0,
            "nine_router_route": None,
            "usage": {"total_tokens": 50},
            "cost": None,
            "public_write_authority": False,
        }


class FailingCodexJobBrain(FakeCodexJobBrain):
    def create(self, **kwargs):
        raise CodexJobBrainError(
            "injected_codex_failure",
            safe_receipt={
                "schema": "contentops.v2.codex_job_brain_receipt.v1",
                "execution_plane": "CODEX_CLI_EXEC_FAKE",
                "requested_model_family": CODEX_MODEL,
                "requested_reasoning_effort": CODEX_REASONING_EFFORT,
                "exit_code": 17,
                "result_classification": "FAIL_CODEX_EXEC",
                "nine_router_route": None,
                "public_write_authority": False,
            },
        )


def _artifact(path: Path) -> dict[str, object]:
    return {"path": str(path.resolve()), "sha256": hash_file(path), "size_bytes": path.stat().st_size}


class FakeMedia:
    def __init__(self, *, fail_typecheck: bool = False) -> None:
        self.render_count = 0
        self.fail_typecheck = fail_typecheck

    def prepare_project(self, **kwargs):
        kwargs["project_root"].mkdir(parents=True, exist_ok=True)
        return {"result": "PASS_PROJECT_SCAFFOLD"}

    def validate_assets(self, packet, asset_root):
        return {"result": "PASS_ASSET_HASHES_AND_RIGHTS_BINDING", "assets": []}

    def typecheck_project(self, project_root: Path):
        if self.fail_typecheck:
            raise RuntimeError("injected_typecheck_failure")
        return {"result": "PASS_GENERATED_SOURCE_TYPECHECK"}

    def render_project(self, *, project_root: Path, output: Path, crf: int):
        self.render_count += 1
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(f"render-{self.render_count}-crf-{crf}".encode())
        return {"result": "PASS_RENDER", "artifact": _artifact(output), "wall_time_seconds": 0.1}

    def contact_sheet(self, video: Path, output: Path):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"fake-jpeg")
        return {"result": "PASS_CONTACT_SHEET", "artifact": _artifact(output)}

    def probe_media(self, path: Path):
        return {"streams": [{"codec_type": "video", "width": 1080, "height": 1920, "r_frame_rate": "30/1"}], "format": {"duration": "36"}}

    def image_data_url(self, path: Path):
        return "data:image/jpeg;base64,ZmFrZQ=="

    def synthesize_narration(self, *, editor, model_path, voices_path, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        narration = output_dir / "narration.wav"
        narration.write_bytes(b"narration")
        placements = []
        cursor = 0.2
        for item in editor["narration_segments"]:
            placements.append({"cue_id": item["segment_id"], "timeline_start_seconds": cursor, "actual_audio_duration_seconds": 1.0, "caption_text": item["text"], "audio_path": str(narration)})
            cursor += 1.1
        return {"duration_seconds": cursor, "placements": placements, "artifact": _artifact(narration), "external_cost_usd": 0.0}

    def build_audio_mix(self, *, picture, narration_receipt, bed_path, output_dir):
        output_dir.mkdir(parents=True, exist_ok=True)
        mix = output_dir / "final_mix.wav"
        mix.write_bytes(b"mix")
        return {"result": "PASS_AUDIO_MIX", "mix": _artifact(mix)}

    def mux_final_media(self, *, picture, mix, output):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"final-media")
        return {"result": "PASS_FINAL_MUX", "final_media": _artifact(output)}

    def build_captions(self, *, editor, narration_receipt, output_dir):
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


def make_supervisor(tmp_path: Path, *, brain=None, media=None) -> tuple[UnattendedV2Supervisor, V2JobStore, str]:
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
    config = FactoryConfig(runtime_root=runtime, scaffold_root=scaffold, dependency_root=dependency, asset_root=assets, kokoro_model=model, kokoro_voices=voices, implementation_head="a" * 40, worker_id="worker")
    brain = brain or FakeCodexJobBrain()
    supervisor = UnattendedV2Supervisor(store=store, config=config, creative_brain=brain, media_backend=media or FakeMedia())
    return supervisor, store, job_id


def test_governed_packet_is_isolated_and_zero_write() -> None:
    result = validate_input_packet(packet())
    assert result["result"] == "PASS_GOVERNED_INPUT"
    assert packet()["creative_exclusions"] == {
        "prior_viewer_facing_react_source": True,
        "prior_final_narration": True,
        "prior_shot_choreography": True,
        "prior_layout_decisions": True,
        "prior_creative_repair": True,
    }
    assert all(value is False for value in packet()["hard_boundaries"].values())


def test_codex_job_brain_is_exact_xhigh_and_has_no_creative_fallback() -> None:
    assert CODEX_MODEL == "gpt-5.6-sol"
    assert CODEX_REASONING_EFFORT == "xhigh"
    expected = (
        "cx/gpt-5.6-terra(high)",
        "vx/gemini-3.1-pro-preview(high)",
        "vx/gemini-3.5-flash(high)",
    )
    assert V1_GROUNDED_RESEARCH_MODEL_LADDER == expected
    for relative in (
        "video/unattended_core_factory_v1/codex_job_brain.py",
        "video/unattended_core_factory_v1/creative.py",
        "video/unattended_core_factory_v1/supervisor.py",
    ):
        source = (REPO / relative).read_text(encoding="utf-8")
        assert "routed_v2_creative_invocation" not in source
        assert "new/gpt-5.6-sol-xhigh" not in source
        assert not any(model in source for model in expected)


def test_superseded_v2_9router_seam_makes_zero_provider_calls() -> None:
    calls = 0

    def forbidden_provider(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise AssertionError("provider_must_not_be_called")

    with pytest.raises(RoutedInvocationError) as exc_info:
        routed_v2_creative_invocation(
            prompt="retired",
            role_task_id="V2_CREATIVE_EDITOR",
            logical_invocation_id="retired",
            work_item_id="retired",
            provider_call=forbidden_provider,
        )
    assert calls == 0
    assert exc_info.value.summary["terminal_disposition"] == "V2_CREATIVE_9ROUTER_ROUTE_SUPERSEDED"
    assert exc_info.value.summary["nine_router_provider_calls"] == 0


def test_cli_capability_probe_requires_exact_model_and_xhigh(tmp_path: Path) -> None:
    executable = tmp_path / "codex.exe"
    executable.write_bytes(b"fake")

    def runner(args, **kwargs):
        if args[-1] == "--version":
            return SimpleNamespace(returncode=0, stdout="codex-cli test\n", stderr="")
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                [
                    {
                        "slug": "gpt-5.6-sol",
                        "supported_reasoning_levels": [
                            {"effort": "high"},
                            {"effort": "xhigh"},
                        ],
                    }
                ]
            ),
            stderr="",
        )

    capability = CodexCliExecutor(executable=executable, runner=runner).inspect_capability(tmp_path)
    assert capability.model == CODEX_MODEL
    assert capability.reasoning_effort == CODEX_REASONING_EFFORT


def test_factual_gate_rejects_unbound_or_rewritten_fact() -> None:
    value = editor_artifact()
    value["narration_segments"][1]["text"] = "Payrolls collapsed."
    with pytest.raises(CreativeContractError, match="not_exact_anchor"):
        validate_editor_artifact(value, packet())


@pytest.mark.parametrize("bad", ["process.env.KEY", "fetch('x')", "import fs from 'fs'", "import {x} from 'youtube-api'"])
def test_creative_code_sandbox_rejects_forbidden_capabilities(bad: str) -> None:
    files = source_files()
    files["src/Short.tsx"] += "\n" + bad
    with pytest.raises(CreativeContractError, match="sandbox_violation"):
        validate_source_files(files)


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


def test_stage_events_are_database_immutable(tmp_path: Path) -> None:
    supervisor, store, job_id = make_supervisor(tmp_path)
    result = supervisor.run_once(max_new_stages=1)
    assert result["last_valid_checkpoint"] == "CLAIMED"
    with store.connect() as connection, pytest.raises(Exception, match="append_only"):
        connection.execute("UPDATE stage_events SET result='tampered'")


def test_restart_after_editor_does_not_call_editor_again(tmp_path: Path) -> None:
    brain = FakeCodexJobBrain()
    supervisor, store, job_id = make_supervisor(tmp_path, brain=brain)
    first = supervisor.run_once(max_new_stages=3)
    assert first["last_valid_checkpoint"] == "CREATIVE_EDITOR_LOCKED"
    supervisor.run_once()
    assert brain.create_count == 1
    assert brain.review_count == 1
    assert store.job(job_id)["state"] == "OWNER_REVIEW_READY"


def test_codex_outputs_are_hash_bound_to_immutable_job_input(tmp_path: Path) -> None:
    brain = FakeCodexJobBrain()
    supervisor, store, job_id = make_supervisor(tmp_path, brain=brain)
    supervisor.run_once(max_new_stages=3)
    event = next(
        item for item in store.events(job_id) if item["stage"] == "CREATIVE_EDITOR_LOCKED"
    )
    provenance = json.loads(event["model_provenance_json"])
    assert provenance["fresh_isolated_context"] is True
    assert provenance["resumed_same_job_thread"] is False
    assert provenance["thread_id"] == f"thread-{job_id}"
    assert provenance["nine_router_route"] is None
    assert provenance["fallback_count"] == 0
    assert provenance["input_artifact_hashes"]["governed_packet"] == hash_value(packet())
    root = supervisor.config.runtime_root / "jobs" / job_id / "artifacts"
    assert provenance["output_artifact_hashes"]["editorial"] == hash_value(
        json.loads((root / "creative_editor.json").read_text(encoding="utf-8"))
    )
    assert provenance["output_artifact_hashes"]["motion"] == hash_value(
        json.loads((root / "codex_initial_motion_output.json").read_text(encoding="utf-8"))
    )


def test_restart_after_motion_does_not_call_motion_author_again(tmp_path: Path) -> None:
    brain = FakeCodexJobBrain()
    supervisor, _, _ = make_supervisor(tmp_path, brain=brain)
    first = supervisor.run_once(max_new_stages=4)
    assert first["last_valid_checkpoint"] == "MOTION_SOURCE_LOCKED"
    supervisor.run_once()
    assert brain.create_count == 1


def test_valid_render_artifact_is_reused_after_resume(tmp_path: Path) -> None:
    media = FakeMedia()
    supervisor, _, _ = make_supervisor(tmp_path, media=media)
    first = supervisor.run_once(max_new_stages=6)
    assert first["last_valid_checkpoint"] == "PROXY_RENDERED"
    assert media.render_count == 1
    supervisor.run_once()
    assert media.render_count == 2


def test_corrupt_motion_artifact_invalidates_only_motion_and_downstream(tmp_path: Path) -> None:
    brain = FakeCodexJobBrain()
    supervisor, store, job_id = make_supervisor(tmp_path, brain=brain)
    supervisor.run_once(max_new_stages=4)
    job_root = supervisor.config.runtime_root / "jobs" / job_id
    (job_root / "artifacts" / "motion_source.json").write_text("{}", encoding="utf-8")
    supervisor.run_once()
    assert brain.create_count == 1
    assert any(event["result"].startswith("INVALIDATED") and event["stage"] == "MOTION_SOURCE_LOCKED" for event in store.events(job_id))


def test_terminal_job_is_not_executed_twice(tmp_path: Path) -> None:
    brain = FakeCodexJobBrain()
    supervisor, store, job_id = make_supervisor(tmp_path, brain=brain)
    result = supervisor.run_once()
    assert result["job"]["state"] == "OWNER_REVIEW_READY"
    count = len(store.events(job_id))
    assert supervisor.run_once()["result"] == "NO_ELIGIBLE_JOB"
    assert len(store.events(job_id)) == count


def test_hard_failure_is_quarantined_and_not_restarted(tmp_path: Path) -> None:
    supervisor, store, job_id = make_supervisor(tmp_path, media=FakeMedia(fail_typecheck=True))
    with pytest.raises(RuntimeError, match="injected_typecheck_failure"):
        supervisor.run_once()
    assert store.job(job_id)["state"] == "QUARANTINED"
    assert supervisor.run_once()["result"] == "NO_ELIGIBLE_JOB"


def test_failed_codex_execution_quarantines_with_safe_provenance(tmp_path: Path) -> None:
    supervisor, store, job_id = make_supervisor(tmp_path, brain=FailingCodexJobBrain())
    with pytest.raises(CodexJobBrainError, match="injected_codex_failure"):
        supervisor.run_once()
    assert store.job(job_id)["state"] == "QUARANTINED"
    events = store.events(job_id)
    failure = next(event for event in events if event["stage"] == "HARD_FAILURE")
    provenance = json.loads(failure["model_provenance_json"])
    assert provenance["requested_model_family"] == CODEX_MODEL
    assert provenance["requested_reasoning_effort"] == CODEX_REASONING_EFFORT
    assert provenance["nine_router_route"] is None
    records = json.loads(failure["artifact_records_json"])
    assert len(records) == 1
    assert Path(records[0]["path"]).name == "codex_failure_receipt.json"


def test_same_identity_cannot_create_duplicate_active_job_or_run(tmp_path: Path) -> None:
    store = V2JobStore(tmp_path / "identity.sqlite3")
    source = tmp_path / "input.json"
    source.write_text("{}", encoding="utf-8")
    first = store.seed_job(video_job_id="one", input_packet_path=source, input_packet_hash="a" * 64, target_format="SHORT")
    second = store.seed_job(video_job_id="two", input_packet_path=source, input_packet_hash="a" * 64, target_format="SHORT")
    assert first["video_job_id"] == second["video_job_id"] == "one"
    claimed = store.claim_next(worker_id="w", implementation_head="b" * 40)
    assert claimed is not None
    assert store.claim_next(worker_id="x", implementation_head="b" * 40) is None


def test_public_write_authority_remains_false_through_resume_and_package(tmp_path: Path) -> None:
    supervisor, store, job_id = make_supervisor(tmp_path)
    supervisor.run_once(max_new_stages=4)
    supervisor.run_once()
    assert store.job(job_id)["public_write_authority"] == 0
    assert all(event["public_write_authority"] == 0 for event in store.events(job_id))
    safety = json.loads((supervisor.config.runtime_root / "jobs" / job_id / "review" / "zero_write_safety_summary.json").read_text(encoding="utf-8"))
    assert all(value == 0 or value is False for key, value in safety.items() if key != "schema")


def test_supervisor_uses_declared_legal_stage_order(tmp_path: Path) -> None:
    supervisor, store, job_id = make_supervisor(tmp_path)
    supervisor.run_once()
    passed = [event["stage"] for event in store.events(job_id) if event["result"].startswith("PASS")]
    expected = [stage for stage in STAGES if stage != "CREATIVE_REVISION_LOCKED"]
    assert passed == expected


def test_owner_bundle_binds_package_media_and_unattended_truth(tmp_path: Path) -> None:
    supervisor, _, job_id = make_supervisor(tmp_path)
    supervisor.run_once()
    bundle = json.loads((supervisor.config.runtime_root / "jobs" / job_id / "review" / "owner_review_bundle.json").read_text(encoding="utf-8"))
    assert bundle["result"] == "OWNER_REVIEW_READY"
    assert bundle["owner_acceptance_claimed"] is False
    assert bundle["unattended"] == {
        "manual_source_edits_after_start": 0,
        "manual_media_edits_after_start": 0,
        "manual_checkpoint_edits": 0,
        "operator_intervention_minutes": 0,
    }
    assert bundle["public_write_authority"] is False


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
