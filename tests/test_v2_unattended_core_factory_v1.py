from __future__ import annotations

import json
import math
import os
import sys
import threading
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import run_v2_unattended_core_factory_v1 as canonical_runner
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
    MediaExecutionError,
    REMOTION_BROWSER_RELATIVE,
    _ensure_junction,
    render_project,
    resolve_remotion_browser_executable,
    typecheck_project,
    validate_dependency_root,
    validate_process_launch_geometry,
)
from video.unattended_core_factory_v1 import media as production_media
from video.unattended_core_factory_v1.supervisor import (
    DesktopSessionV2Factory,
    FactoryConfig,
    OWNED_TEXT_SURFACE_LABELS,
    SECRET_PATTERNS,
    STAGES,
    SupervisorError,
)
from video.unattended_core_factory_v1.transcript import (
    build_transcript_derived_seo,
    synthesis_text_for_segment,
    validate_transcript_derived_seo,
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
FAKE_SECRET_MARKER = "client_secret=FAKE_OWNED_SECRET_VALUE_12345"


def packet() -> dict[str, object]:
    value = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    value["pronunciation_lexicon"] = [
        {"surface": "23,000", "spoken_as": "twenty three thousand"},
        {"surface": "23,000", "spoken_as": "twenty-three thousand"},
    ]
    return value


def editor_artifact() -> dict[str, object]:
    p = packet()
    anchors = {item["anchor_id"]: item["statement"] for item in p["anchors"]}
    analysis = {item["analysis_id"]: item["statement"] for item in p["permitted_analysis"]}
    segments = [
        {"segment_id": "s1", "kind": "ENGAGEMENT", "text": "The headline moved. The market did not break.", "anchor_ids": [], "analysis_id": "", "pronunciation_notes": []},
        {"segment_id": "s2", "kind": "FACT", "text": anchors["EMP001"], "anchor_ids": ["EMP001"], "analysis_id": "", "pronunciation_notes": [{"surface": "23,000", "spoken_as": "twenty three thousand"}]},
        {"segment_id": "s3", "kind": "FACT", "text": anchors["EMP002"], "anchor_ids": ["EMP002"], "analysis_id": "", "pronunciation_notes": []},
        {"segment_id": "s4", "kind": "FACT", "text": anchors["JOL002"], "anchor_ids": ["JOL002"], "analysis_id": "", "pronunciation_notes": []},
        {"segment_id": "s5", "kind": "ANALYSIS", "text": analysis["ANALYSIS_STASIS"], "anchor_ids": [], "analysis_id": "ANALYSIS_STASIS", "pronunciation_notes": []},
        {"segment_id": "s6", "kind": "ENGAGEMENT", "text": "Watch the motion, not just the level.", "anchor_ids": [], "analysis_id": "", "pronunciation_notes": []},
    ]
    return {
        "schema": "contentops.v2.codex_job_editorial.v3",
        "title": "Frozen Without Breaking",
        "viewer_promise": "See why low motion differs from collapse.",
        "narration_segments": segments,
        "editorial_structure": ["hook", "evidence", "mechanism", "watch condition"],
        "retention_contract": {
            "promise_segment_ids": ["s1"],
            "payoff_segment_ids": ["s4"],
        },
        "search_entities": ["July", "Total nonfarm payroll employment"],
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
        "src/Root.tsx": f"import React from 'react';\nimport {{Composition}} from 'remotion';\nimport {{Short}} from './Short';\nexport const Root: React.FC=()=> <Composition id='ContentOpsV2Short' component={{Short}} durationInFrames={{{duration_frames}}} fps={{30}} width={{1080}} height={{1920}}/>;",
        "src/Short.tsx": "import React from 'react';\nimport {AbsoluteFill,OffthreadVideo,interpolate,staticFile,useCurrentFrame} from 'remotion';\nexport const Short: React.FC=()=>{const f=useCurrentFrame();const o=interpolate(f,[0,30],[0,1],{extrapolateRight:'clamp'});return <AbsoluteFill style={{background:'#071116',color:'#f5f0e6',justifyContent:'center',alignItems:'center',opacity:o,fontSize:72}}><OffthreadVideo muted src={staticFile('assets/documentary/commuters_subway_cc0_pexels_855749.mp4')}/><div>FROZEN / MOVING?</div></AbsoluteFill>};",
    }


def motion_artifact(timing_lock: dict[str, object]) -> dict[str, object]:
    actual = float(timing_lock["actual_total_narration_duration_seconds"])
    tail_room = 0.67
    frames = math.ceil((actual + tail_room) * 30 - 0.0000001)
    asset_selection = {
        "schema": "contentops.v2.post_transcript_asset_selection.v1",
        "governed_input_hash": timing_lock["governed_input_hash"],
        "editorial_narration_hash": timing_lock["editorial_narration_hash"],
        "narration_timing_lock_hash": timing_lock["timing_lock_hash"],
        "canonical_transcript_hash": timing_lock["canonical_spoken_transcript"][
            "canonical_transcript_hash"
        ],
        "prior_creative_source_reused_as_input": False,
        "fresh_web_discovery_performed": True,
        "visual_needs": [
            {
                "need_id": "need_commuter_motion",
                "transcript_segment_ids": ["s1", "s2"],
                "visual_purpose": "Show the physical distinction between motion and stasis.",
            }
        ],
        "candidate_board": [
            {
                "candidate_id": "candidate_commuter_flow",
                "need_id": "need_commuter_motion",
                "source_url": "https://www.pexels.com/video/855749/",
                "rights_basis": "Pexels reusable media terms recorded in governed input.",
                "visual_fit_assessment": "Vertical-safe real commuter motion with useful depth.",
                "selected_asset_id": "COMMUTER_FLOW",
                "rejection_reason": "",
            }
        ],
        "selected_existing_asset_ids": ["COMMUTER_FLOW"],
        "selected_assets": [],
    }
    asset_selection["asset_selection_hash"] = hash_value(asset_selection)
    return {
        "schema": "contentops.v2.codex_job_motion_source.v1",
        "composition_id": "ContentOpsV2Short",
        "duration_seconds": frames / 30,
        "narration_timing_lock_hash": timing_lock["timing_lock_hash"],
        "picture_timing": {
            "fps": 30,
            "authored_head_room_seconds": timing_lock["initial_silence_seconds"],
            "authored_tail_room_seconds": tail_room,
            "duration_frames": frames,
        },
        "asset_ids": ["COMMUTER_FLOW"],
        "asset_selection": asset_selection,
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
        "review_checks": {
            "real_contextual_material_density": "Reviewed against the actual proxy.",
            "exact_or_near_asset_reuse": "No material exact or near reuse defect.",
            "visual_family_and_layout_repetition": "No material repetition defect.",
            "phone_readability": "Primary information remains phone readable.",
            "chart_document_stability": "No unstable chart or document treatment.",
            "captions_hidden_comprehension": "The visual thesis remains comprehensible.",
            "stronger_concrete_media_replacement_opportunity": "No material replacement required.",
        },
        "replacement_files": source_files() if material else {},
    }


def _artifact(path: Path) -> dict[str, object]:
    return {"path": str(path.resolve()), "sha256": hash_file(path), "size_bytes": path.stat().st_size}


def dependency_surface(root: Path, *, browser: bool = True) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    suffix = ".cmd" if os.name == "nt" else ""
    binaries = root / ".bin"
    binaries.mkdir(parents=True, exist_ok=True)
    (binaries / f"remotion{suffix}").write_bytes(b"remotion-cli")
    (binaries / f"tsc{suffix}").write_bytes(b"typescript-cli")
    if browser:
        executable = root / REMOTION_BROWSER_RELATIVE
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_bytes(b"browser")
    return root


class FakeMedia:
    def __init__(
        self,
        *,
        fail_typecheck: bool = False,
        segment_duration: float = 5.5,
        picture_duration_override: float | None = None,
        container_duration_padding: float = 0.0,
    ) -> None:
        self.render_count = 0
        self.fail_typecheck = fail_typecheck
        self.segment_duration = segment_duration
        self.picture_duration_override = picture_duration_override
        self.container_duration_padding = container_duration_padding
        self.motion_duration = 35.0
        self.synthesis_count = 0
        self.mix_timing_lock_hash = None
        self.caption_segments = None

    def prepare_project(self, **kwargs):
        kwargs["project_root"].mkdir(parents=True, exist_ok=True)
        return {"result": "PASS_PROJECT_SCAFFOLD"}

    def validate_assets(self, packet, asset_root):
        return {"result": "PASS_ASSET_HASHES_AND_RIGHTS_BINDING", "assets": []}

    def typecheck_project(self, project_root: Path, dependency_root: Path):
        if self.fail_typecheck:
            raise RuntimeError("injected_typecheck_failure")
        return {"result": "PASS_GENERATED_SOURCE_TYPECHECK"}

    def resolve_remotion_browser_executable(self, dependency_root: Path):
        browser = dependency_root / "chrome-headless-shell.exe"
        browser.write_bytes(b"browser")
        return browser

    def render_project(self, *, project_root: Path, dependency_root: Path, output: Path, crf: int, browser_executable: Path, public_root: Path):
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
        return {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1080,
                    "height": 1920,
                    "r_frame_rate": "30/1",
                    "duration": str(duration),
                }
            ],
            "format": {"duration": str(duration + self.container_duration_padding)},
        }

    def synthesize_narration(self, *, editor, model_path, voices_path, output_dir):
        self.synthesis_count += 1
        output_dir.mkdir(parents=True, exist_ok=True)
        narration = output_dir / "narration.wav"
        narration.write_bytes(b"narration")
        placements = []
        cursor = 0.18
        for index, item in enumerate(editor["narration_segments"], start=1):
            segment = output_dir / f"segment_{index:02d}_{item['segment_id']}.wav"
            synthesis_text = synthesis_text_for_segment(item)
            segment.write_bytes(f"segment-{item['segment_id']}-{synthesis_text}".encode())
            pause = 0.16 if index < len(editor["narration_segments"]) else 0.35
            placements.append({
                "cue_id": item["segment_id"],
                "segment_id": item["segment_id"],
                "segment_text_sha256": hash_value(item["text"]),
                "synthesis_text_sha256": hash_value(synthesis_text),
                "timeline_start_seconds": round(cursor, 6),
                "actual_audio_duration_seconds": self.segment_duration,
                "timeline_end_seconds": round(cursor + self.segment_duration, 6),
                "pause_after_seconds": pause,
                "caption_text": item["text"],
                "audio_path": str(segment.resolve()),
                "audio": _artifact(segment),
                "synthesis_action": "SYNTHESIZED",
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
        self.caption_segments = timing_lock["canonical_spoken_transcript"]["segments"]
        output_dir.mkdir(parents=True, exist_ok=True)
        values = {}
        for kind in ("json", "srt", "vtt"):
            path = output_dir / f"captions.en.{kind}"
            path.write_text("{}" if kind == "json" else "caption", encoding="utf-8")
            values[kind] = _artifact(path)
        return {
            "result": "PASS_CAPTIONS",
            "canonical_transcript_hash": timing_lock["canonical_spoken_transcript"]["canonical_transcript_hash"],
            "locked_narration_audio_sha256": timing_lock["locked_narration_audio"]["sha256"],
            "artifacts": values,
        }

    def technical_media_report(self, path, output):
        result = {"artifact": _artifact(path), "probe": self.probe_media(path), "media_validation": {"result": "PASS_MEDIA_CONTRACT", "duration_seconds": 36}, "loudness": {"integrated_lufs": -16.0, "true_peak_dbfs": -1.5}}
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result), encoding="utf-8")
        result["report_artifact"] = _artifact(output)
        return result

    def build_neutral_package(self, *, output, final_media, audio, captions, timing_lock, seo_package, **kwargs):
        result = {
            "package_id": "pkg_test",
            "final_mux": _artifact(final_media),
            "final_audio": _artifact(audio),
            "artifacts": {
                "caption_json": captions["artifacts"]["json"],
                "caption_srt": captions["artifacts"]["srt"],
                "caption_vtt": captions["artifacts"]["vtt"],
            },
            "canonical_transcript_hash": timing_lock["canonical_spoken_transcript"]["canonical_transcript_hash"],
            "voiceover_qa_hash": timing_lock["voiceover_qa"]["voiceover_qa_hash"],
            "seo_package_hash": seo_package["seo_package_hash"],
        }
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
    dependency = tmp_path / "node_modules"
    assets = tmp_path / "assets-root"
    scaffold.mkdir()
    dependency_surface(dependency)
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


def owned_scan_paths(
    factory: DesktopSessionV2Factory, video_job_id: str
) -> dict[str, Path]:
    paths = factory._paths(video_job_id)
    for directory in (
        paths["artifacts"],
        paths["session_inbox"],
        paths["project"] / "src",
        paths["captions"].parent,
        paths["technical"].parent,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return paths


def test_owned_surface_secret_patterns_are_unchanged() -> None:
    assert tuple(pattern.pattern for pattern in SECRET_PATTERNS) == (
        r"(?i)authorization\s*:\s*bearer\s+\S+",
        r"\bsk-[A-Za-z0-9_-]{16,}\b",
        r"\b(?:eyJ[A-Za-z0-9_-]+\.){2}[A-Za-z0-9_-]+\b",
        r"(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[=:]\s*['\"]?[A-Za-z0-9_./+-]{12,}",
    )


@pytest.mark.parametrize(
    ("surface", "filename"),
    (
        ("artifacts", "governed_owned_artifact.json"),
        ("desktop_session_inbox", "desktop_submission.json"),
        ("generated_project_src", "OwnedSource.tsx"),
        ("package", "owned_package.json"),
        ("review", "owned_review.json"),
    ),
)
def test_fake_secret_hard_fails_every_explicit_owned_text_surface(
    tmp_path: Path, surface: str, filename: str
) -> None:
    factory, _, job_id = make_factory(tmp_path)
    paths = owned_scan_paths(factory, job_id)
    roots = dict(factory._owned_text_surfaces(paths))
    target = roots[surface] / filename
    target.write_text(FAKE_SECRET_MARKER, encoding="utf-8")

    with pytest.raises(SupervisorError) as caught:
        factory._secret_scan(paths)

    message = str(caught.value)
    assert message.startswith("secret_scan_failed:")
    assert filename in message
    assert FAKE_SECRET_MARKER not in message


def test_projected_node_modules_vendor_fixture_is_outside_owned_scan_surface(
    tmp_path: Path,
) -> None:
    factory, _, job_id = make_factory(tmp_path)
    paths = owned_scan_paths(factory, job_id)
    vendor = (
        paths["project"]
        / "node_modules"
        / "zod"
        / "src"
        / "v4"
        / "mini"
        / "tests"
        / "string.test.ts"
    )
    vendor.parent.mkdir(parents=True, exist_ok=True)
    vendor.write_text(FAKE_SECRET_MARKER, encoding="utf-8")

    receipt = factory._secret_scan(paths)

    assert receipt["result"] == "PASS_JOB_OWNED_TEXT_SECRET_SCAN"
    assert receipt["owned_surface_labels"] == list(OWNED_TEXT_SURFACE_LABELS)
    assert receipt["external_or_vendor_surface_count"] == 0


def test_external_junction_or_symlink_cannot_expand_owned_scan_scope(
    tmp_path: Path,
) -> None:
    factory, _, job_id = make_factory(tmp_path)
    paths = owned_scan_paths(factory, job_id)
    external = tmp_path / "external-not-owned"
    external.mkdir()
    (external / "not_owned.txt").write_text(FAKE_SECRET_MARKER, encoding="utf-8")
    projection = paths["artifacts"] / "external_projection"
    _ensure_junction(projection, external)

    with pytest.raises(
        SupervisorError,
        match=r"secret_scan_owned_surface_link_forbidden:artifacts/external_projection",
    ) as caught:
        factory._secret_scan(paths)

    assert "not_owned.txt" not in str(caught.value)
    assert FAKE_SECRET_MARKER not in str(caught.value)


def test_package_and_owner_ready_use_the_same_complete_owned_surface_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    factory, _, _ = make_factory(tmp_path)
    receipts: list[dict[str, object]] = []
    scan = factory._secret_scan

    def record_scan(paths: dict[str, Path]) -> dict[str, object]:
        receipt = scan(paths)
        receipts.append(receipt)
        return receipt

    monkeypatch.setattr(factory, "_secret_scan", record_scan)
    result = complete(factory)

    assert result["job"]["state"] == "OWNER_REVIEW_READY"
    assert len(receipts) == 2
    assert all(
        receipt["owned_surface_labels"] == list(OWNED_TEXT_SURFACE_LABELS)
        for receipt in receipts
    )
    assert receipts[1]["scanned_file_count"] > receipts[0]["scanned_file_count"]


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
    dependency = dependency_surface(tmp_path / "node_modules")
    browser = dependency / REMOTION_BROWSER_RELATIVE
    resolved = resolve_remotion_browser_executable(dependency)
    assert resolved == browser.resolve()
    assert "generated_project" not in str(resolved)


def test_dependency_root_preflight_rejects_project_root_and_accepts_node_modules(
    tmp_path: Path,
) -> None:
    project = tmp_path / "remotion-project"
    dependency = dependency_surface(project / "node_modules")

    with pytest.raises(
        MediaExecutionError,
        match=r"dependency_root_is_project_root:use_node_modules:.*node_modules",
    ):
        validate_dependency_root(project)

    receipt = validate_dependency_root(dependency)
    assert receipt["result"] == "PASS_REMOTION_DEPENDENCY_ROOT_PREFLIGHT"
    assert receipt["root_contract"] == "PROJECT_NODE_MODULES"
    assert Path(receipt["remotion_cli"]).is_file()
    assert Path(receipt["typescript_cli"]).is_file()
    assert Path(receipt["canonical_browser_executable"]).is_file()
    assert receipt["suitable_for_project_node_modules_projection"] is True
    assert receipt["projected_cli_execution_required"] is False
    assert receipt["launch_topology"] == (
        "CANONICAL_DEPENDENCY_ROOT_CLI_WITH_EXPLICIT_PROJECT_PATHS"
    )


def test_production_like_windows_geometry_selects_only_canonical_tool_launches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dependency = dependency_surface(tmp_path / "canonical-tool-root" / "node_modules")
    assets = tmp_path / "canonical-public-root"
    (assets / "assets").mkdir(parents=True)
    runtime = (
        tmp_path
        / "Capital Chronicle Worktrees"
        / "v2-windows-process-launch-geometry-repair-fresh-soak-retry-v1"
        / ".task-runtime"
        / "v2-unattended-production-soak-transcript-voiceover-seo-hardening-v1"
    )
    job_id = "v2_" + "long_valid_qualified_story_identity_" * 3 + "2026"
    project = runtime / "jobs" / job_id / "generated_project"
    materialize_source(source_files(), project)
    production_media.prepare_project(
        project_root=project,
        scaffold_root=REPO / "video" / "unattended_core_factory_v1" / "scaffold",
        dependency_root=dependency,
        asset_root=assets,
    )
    projected_tsc = project / "node_modules" / ".bin" / (
        "tsc.cmd" if os.name == "nt" else "tsc"
    )
    projected_remotion = project / "node_modules" / ".bin" / (
        "remotion.cmd" if os.name == "nt" else "remotion"
    )
    if os.name == "nt":
        assert len(str(projected_tsc)) > 259
        assert len(str(projected_remotion)) > 259

    output = runtime / "jobs" / job_id / "media" / "proxy.mp4"
    geometry = validate_process_launch_geometry(
        project_root=project,
        dependency_root=dependency,
        public_root=assets,
        output=output,
    )
    assert geometry["typescript"]["projected_executable_selected"] is False
    assert geometry["remotion"]["projected_executable_selected"] is False
    assert Path(geometry["typescript"]["executable"]) == (
        dependency / ".bin" / ("tsc.cmd" if os.name == "nt" else "tsc")
    ).resolve()
    assert Path(geometry["remotion"]["executable"]) == (
        dependency / ".bin" / ("remotion.cmd" if os.name == "nt" else "remotion")
    ).resolve()
    assert Path(geometry["typescript"]["cwd"]) == dependency.parent.resolve()
    assert Path(geometry["remotion"]["cwd"]) == dependency.parent.resolve()

    calls: list[tuple[list[str], Path]] = []

    def fake_run(command, *, cwd=None, timeout=1800):
        command = list(map(str, command))
        calls.append((command, Path(str(cwd))))
        if len(command) > 1 and command[1] == "render":
            rendered = Path(command[4])
            rendered.parent.mkdir(parents=True, exist_ok=True)
            rendered.write_bytes(b"rendered")
        return {
            "command": command,
            "returncode": 0,
            "wall_time_seconds": 0.01,
            "output_tail": "",
        }

    monkeypatch.setattr(production_media, "run_command", fake_run)
    checked = typecheck_project(project, dependency)
    browser = resolve_remotion_browser_executable(dependency)
    rendered = render_project(
        project_root=project,
        dependency_root=dependency,
        output=output,
        crf=26,
        browser_executable=browser,
        public_root=assets,
    )
    assert checked["result"] == "PASS_GENERATED_SOURCE_TYPECHECK"
    assert rendered["result"] == "PASS_RENDER"
    assert calls[0][0][0] == geometry["typescript"]["executable"]
    assert calls[0][0][1:3] == ["--project", str(project.resolve() / "tsconfig.json")]
    assert calls[1][0][0] == geometry["remotion"]["executable"]
    assert calls[1][0][2] == str(project.resolve() / "src" / "index.tsx")
    assert calls[0][1] == calls[1][1] == dependency.parent.resolve()


def test_dependency_root_preflight_fails_closed_for_missing_and_ambiguous_browser(
    tmp_path: Path,
) -> None:
    missing = dependency_surface(tmp_path / "missing" / "node_modules", browser=False)
    with pytest.raises(
        MediaExecutionError, match="canonical_remotion_browser_identity_invalid:0"
    ):
        validate_dependency_root(missing)

    ambiguous = dependency_surface(
        tmp_path / "ambiguous" / "node_modules", browser=False
    )
    cache = ambiguous / ".remotion" / "chrome-headless-shell"
    for variant in ("candidate-a", "candidate-b"):
        executable = cache / variant / "chrome-headless-shell.exe"
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_bytes(variant.encode())
    with pytest.raises(
        MediaExecutionError, match="canonical_remotion_browser_identity_invalid:2"
    ):
        validate_dependency_root(ambiguous)


def test_canonical_runner_rejects_invalid_dependency_root_before_claim_or_proof_epoch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = tmp_path / "runtime"
    store = V2JobStore(runtime / "v2_jobs.sqlite3")
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(packet()), encoding="utf-8")
    store.seed_job(
        video_job_id="invalid-root-job",
        input_packet_path=input_path,
        input_packet_hash=hash_value(packet()),
        target_format="SHORT_9_16_1080X1920_30FPS",
    )
    project = tmp_path / "remotion-project"
    dependency_surface(project / "node_modules")
    assets = tmp_path / "assets"
    assets.mkdir()
    model = tmp_path / "kokoro.onnx"
    voices = tmp_path / "voices.bin"
    model.write_bytes(b"model")
    voices.write_bytes(b"voices")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_v2_unattended_core_factory_v1.py",
            "--runtime-root",
            str(runtime),
            "start",
            "--dependency-root",
            str(project),
            "--asset-root",
            str(assets),
            "--kokoro-model",
            str(model),
            "--kokoro-voices",
            str(voices),
            "--implementation-head",
            "a" * 40,
            "--parent-session-label",
            "invalid-root-preflight-test",
            "--proof-run-started-at",
            "2026-08-17T00:00:00Z",
        ],
    )

    with pytest.raises(
        SupervisorError,
        match=r"dependency_root_preflight_failed:dependency_root_is_project_root",
    ):
        canonical_runner.main()

    job = store.job("invalid-root-job")
    assert job["state"] == "QUEUED"
    assert job["claimed_by"] is None
    assert job["run_id"] is None
    assert store.events("invalid-root-job") == []
    with store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM job_runs").fetchone()[0] == 0


@pytest.mark.skipif(os.name != "nt", reason="Windows CreateProcess geometry contract")
def test_process_geometry_preflight_rejects_unsupported_actual_job_before_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = tmp_path / "runtime"
    store = V2JobStore(runtime / "v2_jobs.sqlite3")
    input_path = tmp_path / "input.json"
    input_path.write_text(json.dumps(packet()), encoding="utf-8")
    job_id = "v2_" + "valid_long_job_identity_" * 3
    store.seed_job(
        video_job_id=job_id,
        input_packet_path=input_path,
        input_packet_hash=hash_value(packet()),
        target_format="SHORT_9_16_1080X1920_30FPS",
    )
    dependency = dependency_surface(tmp_path / "canonical" / "node_modules")
    assets = tmp_path / "assets"
    assets.mkdir()
    model = tmp_path / "kokoro.onnx"
    voices = tmp_path / "voices.bin"
    model.write_bytes(b"model")
    voices.write_bytes(b"voices")
    monkeypatch.setattr(
        production_media, "WINDOWS_CREATEPROCESS_COMMAND_LINE_MAX", 180
    )
    config = FactoryConfig(
        runtime_root=runtime,
        scaffold_root=tmp_path,
        dependency_root=dependency,
        asset_root=assets,
        kokoro_model=model,
        kokoro_voices=voices,
        implementation_head="a" * 40,
        worker_id="geometry-preflight-worker",
        parent_provenance=PARENT,
    )

    with pytest.raises(
        SupervisorError,
        match=r"process_launch_geometry_preflight_failed:.*serialized_command_line_too_long",
    ):
        DesktopSessionV2Factory(store=store, config=config)

    job = store.job(job_id)
    assert job["state"] == "QUEUED"
    assert job["claimed_by"] is None
    assert job["run_id"] is None
    assert store.events(job_id) == []
    with store.connect() as connection:
        assert connection.execute("SELECT COUNT(*) FROM job_runs").fetchone()[0] == 0


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
    root = factory.config.runtime_root / "jobs" / video_job_id / "artifacts"
    selection = json.loads(
        (root / "post_transcript_asset_selection.json").read_text(encoding="utf-8")
    )
    assert selection["canonical_transcript_hash"] == timing[
        "canonical_spoken_transcript"
    ]["canonical_transcript_hash"]
    assert selection["fresh_web_discovery_performed"] is True


def test_motion_rejects_asset_board_not_bound_to_canonical_transcript(
    tmp_path: Path,
) -> None:
    factory, _, _ = make_factory(tmp_path)
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
    assert pending["required_input"] == "MOTION_VISUAL_AUTHORSHIP"
    timing = locked_timing(factory, started["video_job_id"])
    motion = motion_artifact(timing)
    motion["asset_selection"]["canonical_transcript_hash"] = "0" * 64
    hash_basis = dict(motion["asset_selection"])
    hash_basis.pop("asset_selection_hash")
    motion["asset_selection"]["asset_selection_hash"] = hash_value(hash_basis)
    with pytest.raises(
        CreativeContractError,
        match="asset_selection_identity_mismatch:canonical_transcript_hash",
    ):
        factory.submit_motion_visual(
            video_job_id=started["video_job_id"],
            run_id=started["run_id"],
            motion=motion,
            provenance=MOTION_CREATIVE,
        )


def test_motion_cannot_use_governed_asset_skipped_by_post_transcript_selection(
    tmp_path: Path,
) -> None:
    factory, _, _ = make_factory(tmp_path)
    started = factory.run_once()
    factory.submit_editorial_narration(
        video_job_id=started["video_job_id"],
        run_id=started["run_id"],
        editor=editor_artifact(),
        provenance=EDITORIAL_CREATIVE,
    )
    factory.resume(video_job_id=started["video_job_id"], run_id=started["run_id"])
    motion = motion_artifact(locked_timing(factory, started["video_job_id"]))
    motion["asset_selection"]["selected_existing_asset_ids"] = [
        "ACCEPTED_AUDIO_BED"
    ]
    motion["asset_selection"]["candidate_board"][0][
        "selected_asset_id"
    ] = "ACCEPTED_AUDIO_BED"
    hash_basis = dict(motion["asset_selection"])
    hash_basis.pop("asset_selection_hash")
    motion["asset_selection"]["asset_selection_hash"] = hash_value(hash_basis)
    with pytest.raises(
        CreativeContractError, match="motion_asset_not_post_transcript_selected"
    ):
        factory.submit_motion_visual(
            video_job_id=started["video_job_id"],
            run_id=started["run_id"],
            motion=motion,
            provenance=MOTION_CREATIVE,
        )


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


def test_picture_lock_uses_video_stream_duration_not_container_audio_padding(
    tmp_path: Path,
) -> None:
    media = FakeMedia(container_duration_padding=0.053333)
    factory, _, _ = make_factory(tmp_path, media=media)
    result = complete(factory)
    assert result["job"]["state"] == "OWNER_REVIEW_READY"


def test_session_artifact_e2e_reaches_owner_review_without_live_creative_provider(tmp_path: Path) -> None:
    media = FakeMedia()
    factory, store, job_id = make_factory(tmp_path, media=media)
    result = complete(factory)
    assert result["job"]["state"] == "OWNER_REVIEW_READY"
    assert result["job"]["terminal_result"] == "PASS_V2_UNATTENDED_PRODUCTION_JOB_OWNER_REVIEW_READY"
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
    assert media.caption_segments == timing["canonical_spoken_transcript"]["segments"]
    transcript = timing["canonical_spoken_transcript"]
    assert timing["voiceover_qa"]["result"] == "PASS_TRANSCRIPT_VOICEOVER_QA"
    assert timing["voiceover_qa"]["pronunciation_changed_segment_ids"] == ["s2"]
    assert transcript["locked_narration_audio_sha256"] == timing["locked_narration_audio"]["sha256"]


def test_canonical_transcript_drives_locked_audio_captions_seo_and_package_identity(
    tmp_path: Path,
) -> None:
    factory, _, _ = make_factory(tmp_path)
    video_job_id, run_id = start_and_submit(factory)
    timing = locked_timing(factory, video_job_id)
    transcript = timing["canonical_spoken_transcript"]
    captions = production_media.build_captions(
        timing_lock=timing,
        media_duration_seconds=35.0,
        output_dir=tmp_path / "real-captions",
    )
    caption_json = json.loads(
        Path(captions["artifacts"]["json"]["path"]).read_text(encoding="utf-8")
    )
    assert caption_json["canonical_transcript_hash"] == transcript["canonical_transcript_hash"]
    assert caption_json["locked_narration_audio_sha256"] == timing["locked_narration_audio"]["sha256"]
    assert [cue["text"] for cue in caption_json["cues"]] == [
        segment["text"] for segment in transcript["segments"]
    ]
    assert [cue["source_audio_sha256"] for cue in caption_json["cues"]] == [
        segment["audio"]["sha256"] for segment in transcript["segments"]
    ]

    seo = build_transcript_derived_seo(transcript=transcript, editor=editor_artifact())
    assert validate_transcript_derived_seo(
        seo, transcript=transcript, editor=editor_artifact()
    )["result"] == "PASS_TRANSCRIPT_DERIVED_SEO"
    assert seo["invented_or_strengthened_fact_count"] == 0
    final_media = tmp_path / "owner-review.mp4"
    final_audio = tmp_path / "final-audio.wav"
    final_media.write_bytes(b"final")
    final_audio.write_bytes(b"audio")
    package = production_media.build_neutral_package(
        story_id=str(packet()["story_id"]),
        run_id=run_id,
        final_media=final_media,
        audio=final_audio,
        captions=captions,
        rights_refs=["a" * 64],
        evidence_refs=["source-ref"],
        input_hash=hash_value(packet()),
        timing_lock=timing,
        seo_package=seo,
        output=tmp_path / "package.json",
    )
    assert package["canonical_transcript_hash"] == transcript["canonical_transcript_hash"]
    assert package["seo_package_hash"] == seo["seo_package_hash"]
    assert package["canonical_transcript_identity"]["final_audio_sha256"] == hash_file(final_audio)


def test_transcript_qa_rejects_duplicate_garbled_or_invented_seo_surfaces() -> None:
    duplicate = editor_artifact()
    duplicate["narration_segments"][1]["text"] = duplicate["narration_segments"][0]["text"]
    duplicate["narration_segments"][1]["kind"] = "ENGAGEMENT"
    duplicate["narration_segments"][1]["anchor_ids"] = []
    duplicate["narration_segments"][1]["pronunciation_notes"] = []
    with pytest.raises(CreativeContractError, match="duplicate_spoken_segment"):
        validate_editor_artifact(duplicate, packet())

    garbled = editor_artifact()
    garbled["narration_segments"][0]["text"] = "\ufffd\ufffd\ufffd"
    with pytest.raises(CreativeContractError, match="garbled_or_empty_segment"):
        validate_editor_artifact(garbled, packet())

    invented_title = editor_artifact()
    invented_title["title"] = "Guaranteed recession call"
    with pytest.raises(CreativeContractError, match="title_not_transcript_derived"):
        validate_editor_artifact(invented_title, packet())


def test_kokoro_cache_resynthesizes_only_the_pronunciation_changed_segment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import numpy as np

    created: list[str] = []

    class FakeKokoro:
        def __init__(self, model: str, voices: str) -> None:
            pass

        def create(self, text: str, *, voice: str, speed: float, lang: str):
            created.append(text)
            return np.full(2400, 0.1, dtype=np.float32), 24_000

    monkeypatch.setitem(sys.modules, "kokoro_onnx", SimpleNamespace(Kokoro=FakeKokoro))
    output = tmp_path / "narration"
    base = editor_artifact()
    production_media.synthesize_narration(
        editor=base,
        model_path=tmp_path / "model.onnx",
        voices_path=tmp_path / "voices.bin",
        output_dir=output,
    )
    assert len(created) == len(base["narration_segments"])
    created.clear()
    production_media.synthesize_narration(
        editor=base,
        model_path=tmp_path / "model.onnx",
        voices_path=tmp_path / "voices.bin",
        output_dir=output,
    )
    assert created == []
    changed = editor_artifact()
    changed["narration_segments"][1]["pronunciation_notes"][0][
        "spoken_as"
    ] = "twenty-three thousand"
    production_media.synthesize_narration(
        editor=changed,
        model_path=tmp_path / "model.onnx",
        voices_path=tmp_path / "voices.bin",
        output_dir=output,
    )
    assert created == [synthesis_text_for_segment(changed["narration_segments"][1])]


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


def test_deterministic_three_job_e2e_isolates_quarantine_identity_and_aggregate_truth(
    tmp_path: Path,
) -> None:
    factory, store, first_job_id = make_factory(tmp_path)
    first = complete(factory)
    assert first["job"]["state"] == "OWNER_REVIEW_READY"

    def seed_distinct(label: str) -> str:
        value = packet()
        value["story_id"] = f"distinct_story_{label}"
        value["authority_version"] = f"test_authority_{label}"
        path = tmp_path / f"input-{label}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        job_id = f"job_{label}"
        store.seed_job(
            video_job_id=job_id,
            input_packet_path=path,
            input_packet_hash=hash_value(value),
            target_format="SHORT_9_16_1080X1920_30FPS",
        )
        return job_id

    quarantined_job_id = seed_distinct("quarantined")
    final_job_id = seed_distinct("after_quarantine")
    bad_factory = DesktopSessionV2Factory(
        store=store,
        config=factory.config,
        media_backend=FakeMedia(fail_typecheck=True),
    )
    bad_job_id, bad_run_id = start_and_submit(bad_factory)
    assert bad_job_id == quarantined_job_id
    with pytest.raises(RuntimeError, match="injected_typecheck_failure"):
        bad_factory.resume(video_job_id=bad_job_id, run_id=bad_run_id)
    assert store.job(quarantined_job_id)["state"] == "QUARANTINED"

    final = complete(factory)
    assert final["video_job_id"] == final_job_id
    assert final["job"]["state"] == "OWNER_REVIEW_READY"
    assert store.job(first_job_id)["state"] == "OWNER_REVIEW_READY"
    roots = {
        job_id: factory._paths(job_id)["root"]
        for job_id in (first_job_id, quarantined_job_id, final_job_id)
    }
    assert len({str(path) for path in roots.values()}) == 3
    first_transcript = locked_timing(factory, first_job_id)[
        "canonical_spoken_transcript"
    ]["canonical_transcript_hash"]
    final_transcript = locked_timing(factory, final_job_id)[
        "canonical_spoken_transcript"
    ]["canonical_transcript_hash"]
    assert first_transcript != final_transcript
    assert not (roots[quarantined_job_id] / "package" / "platform_neutral_package_manifest.json").exists()
    assert (roots[final_job_id] / "review" / "owner_review_bundle.json").is_file()

    summary = store.soak_summary()
    assert summary["job_count"] == summary["started_job_count"] == 3
    assert summary["owner_review_ready_count"] == 2
    assert summary["quarantined_job_count"] == 1
    assert summary["all_started_jobs_succeeded"] is False
    assert summary["public_write_authority"] is False
    assert summary["manual_source_edits_after_start"] == 0
    assert summary["manual_media_edits_after_start"] == 0
    assert summary["manual_checkpoint_edits"] == 0


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


def test_real_generated_source_typecheck_render_and_browser_when_configured(
    tmp_path: Path,
) -> None:
    dependency = os.environ.get("V2_REMOTION_DEPENDENCY_ROOT")
    assets = os.environ.get("V2_FWB_ACCEPTED_ASSET_ROOT")
    if not dependency or not assets:
        pytest.skip("real accepted V2 media roots not configured")
    from video.unattended_core_factory_v1 import media

    from scripts.run_v2_remotion_short_path_smoke_v1 import SMOKE_SOURCE

    runtime = (
        tmp_path
        / "Capital Chronicle Worktrees"
        / "v2-windows-process-launch-geometry-repair-fresh-soak-retry-v1"
        / ".task-runtime"
        / "v2-production-like-process-smoke-runtime-root"
    )
    job_id = "v2_" + "long_valid_job_identity_" * 3 + "process_smoke"
    project = runtime / "jobs" / job_id / "generated_project"
    materialize_source(SMOKE_SOURCE, project)
    media.prepare_project(
        project_root=project,
        scaffold_root=REPO / "video" / "unattended_core_factory_v1" / "scaffold",
        dependency_root=Path(dependency),
        asset_root=Path(assets),
    )
    assert media.validate_assets(packet(), Path(assets))["result"] == "PASS_ASSET_HASHES_AND_RIGHTS_BINDING"
    output = runtime / "jobs" / job_id / "media" / "process_smoke.mp4"
    geometry = media.validate_process_launch_geometry(
        project_root=project,
        dependency_root=Path(dependency),
        public_root=Path(assets),
        output=output,
    )
    assert geometry["typescript"]["projected_executable_selected"] is False
    assert geometry["remotion"]["projected_executable_selected"] is False
    assert media.typecheck_project(project, Path(dependency))["result"] == "PASS_GENERATED_SOURCE_TYPECHECK"
    browser = media.resolve_remotion_browser_executable(Path(dependency))
    render = media.render_project(
        project_root=project,
        dependency_root=Path(dependency),
        output=output,
        crf=28,
        browser_executable=browser,
        public_root=Path(assets),
        composition_id="V2RenderSmoke",
        concurrency=1,
    )
    assert render["result"] == "PASS_RENDER"
    assert output.is_file()
    assert render["browser_executable"] == str(browser)
