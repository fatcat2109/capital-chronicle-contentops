import json
from pathlib import Path

import numpy as np
import pytest

from video.unattended_core_factory_v1.store import V2JobStore, JobStoreError
from video.unattended_core_factory_v1.caption_alignment import measured_phrase_narration


TIMING_FAILURE = "HARD_FAILURE:TranscriptContractError:voiceover_qa_failed:retention_payoff_outside_first_30_seconds"


def quarantined(tmp_path, reason=TIMING_FAILURE):
    store = V2JobStore(tmp_path / "jobs.sqlite3")
    store.seed_job(
        video_job_id="same",
        input_packet_path=tmp_path / "input.json",
        input_packet_hash="a" * 64,
        target_format="SHORT",
    )
    job = store.claim_next(worker_id="test", implementation_head="b" * 40)
    store.quarantine(video_job_id="same", run_id=job["run_id"], reason=reason)
    return store, job


def test_timing_recovery_preserves_run_and_original_failure(tmp_path):
    store, original = quarantined(tmp_path)
    recovered = store.reopen_editorial_timing_failure(
        video_job_id="same", revision="native-correction"
    )
    assert recovered["run_id"] == original["run_id"]
    assert len(store.jobs()) == 1
    event = store.events("same")[-1]
    assert (
        json.loads(event["retry_state_json"])["original_terminal_result"]
        == TIMING_FAILURE
    )
    assert recovered["public_write_authority"] == 0
    assert (
        store.claim_next(worker_id="test", implementation_head="b" * 40)["run_id"]
        == original["run_id"]
    )
    store.quarantine(
        video_job_id="same", run_id=original["run_id"], reason=TIMING_FAILURE
    )
    with pytest.raises(JobStoreError, match="budget_or_stage_boundary"):
        store.reopen_editorial_timing_failure(video_job_id="same", revision="again")


def test_recovery_replay_repairs_setup_after_store_transaction(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from video.unattended_core_factory_v1.supervisor import DesktopSessionV2Factory
    from video.unattended_core_factory_v1 import media

    store, original = quarantined(tmp_path)
    # Reproduce a crash immediately after the store committed recovery intent.
    store.reopen_editorial_timing_failure(video_job_id="same", revision="correction")
    root = tmp_path / "jobs/same"
    audio = root / "audio/narration/segment_01_one.wav"
    audio.parent.mkdir(parents=True)
    audio.write_bytes(b"preserved original waveform fixture")
    editor = root / "editor.json"
    editor.write_text(json.dumps(dict(narration_segments=[dict(segment_id="one")])))
    failure = root / "revisions/correction/artifacts/narration_overrun.json"
    f = object.__new__(DesktopSessionV2Factory)
    f.store = store
    f.config = SimpleNamespace(worker_id="resume", implementation_head="b" * 40)
    f._paths = lambda _: dict(editor_initial=editor, narration_overrun=failure)
    f._job_root = lambda _: root
    monkeypatch.setattr(media, "probe_media", lambda _: dict(format=dict(duration=3.2)))
    result = f.reopen_editorial_timing_failure(
        video_job_id="same", revision="correction"
    )
    assert result["idempotent_replay"]
    assert json.loads(failure.read_text())["measurements"][0]["duration_seconds"] == 3.2
    assert store.job("same")["run_id"] == original["run_id"]
    assert store.job("same")["claimed_by"] == "resume"
    setup = [e for e in store.events("same") if e["stage"] == "EDITORIAL_TIMING_RECOVERY_SETUP"]
    assert len(setup) == 1
    from video.unattended_core_factory_v1.creative import hash_file
    assert json.loads(setup[0]["artifact_records_json"])[0]["sha256"] == hash_file(failure)
    before = len(store.events("same"))
    f.reopen_editorial_timing_failure(video_job_id="same", revision="correction")
    assert len(store.events("same")) == before
    store.finalize(video_job_id="same", run_id=original["run_id"],
        result="PRIVATE_ENGINEERING_PACKAGE_REVIEW_REQUIRED", state="OWNER_REVIEW_READY")
    verified = f.reopen_editorial_timing_failure(video_job_id="same", revision="correction")
    assert verified["result"] == "RECOVERY_SETUP_VERIFIED_ALREADY_OWNER_REVIEW_READY"
    assert verified["required_input"] is None
    assert store.job("same")["state"] == "OWNER_REVIEW_READY"
    tampered = json.loads(failure.read_text())
    tampered["measurements"][0]["duration_seconds"] = 999999
    failure.write_text(json.dumps(tampered))
    with pytest.raises(RuntimeError, match="immutable_session_submission_conflict"):
        f.reopen_editorial_timing_failure(video_job_id="same", revision="correction")
    assert (
        len(
            [
                e
                for e in store.events("same")
                if e["stage"] == "EDITORIAL_TIMING_RECOVERY"
            ]
        )
        == 1
    )


@pytest.mark.parametrize("stop_after", [1, 2, 3, 4])
def test_private_successor_resumes_after_every_successful_append(tmp_path, stop_after):
    from video.unattended_core_factory_v1.supervisor import DesktopSessionV2Factory

    store = V2JobStore(tmp_path / "jobs.sqlite3")
    store.seed_job(
        video_job_id="same",
        input_packet_path=tmp_path / "input",
        input_packet_hash="a" * 64,
        target_format="SHORT",
    )
    job = store.claim_next(worker_id="test", implementation_head="b" * 40)
    store.finalize(
        video_job_id="same",
        run_id=job["run_id"],
        result="PRIVATE_ENGINEERING_PACKAGE_REVIEW_REQUIRED",
        state="OWNER_REVIEW_READY",
    )
    job = store.job("same")
    f = object.__new__(DesktopSessionV2Factory)
    f.store = store
    stages = {}
    for stage in [
        "AUDIO_BUILT",
        "FINAL_MEDIA_BUILT",
        "PACKAGE_QA_PASSED",
        "OWNER_REVIEW_READY",
    ]:
        path = tmp_path / stage
        path.write_text(stage)
        stages[stage] = [path]
    spec = dict(
        job=job,
        stages=stages,
        inputs={"source": "c" * 64},
        role="fixture",
        result_prefix="PASS_SUCCESSOR_",
        revision="exact",
    )
    append = store.append_event
    count = 0

    def interrupted(**kwargs):
        nonlocal count
        result = append(**kwargs)
        if kwargs["result"].startswith("PASS"):
            count += 1
            if count == stop_after:
                raise RuntimeError("simulated process loss after committed stage")
        return result

    store.append_event = interrupted
    with pytest.raises(RuntimeError, match="simulated process loss"):
        f._record_private_successor(**spec)
    assert store.job("same")["state"] == "OWNER_REVIEW_READY"
    store.append_event = append
    f._record_private_successor(**spec)
    for stage in stages:
        assert (
            len(
                [
                    e
                    for e in store.events("same")
                    if e["stage"] == stage and e["result"].startswith("PASS")
                ]
            )
            == 1
        )
    assert f._record_private_successor(**spec)
    assert store.job("same")["run_id"] == job["run_id"]


@pytest.mark.parametrize(
    "reason",
    [
        "rights_hold",
        TIMING_FAILURE + ",critical_number_missing",
        "security:" + TIMING_FAILURE,
    ],
)
def test_recovery_cannot_reopen_other_or_mixed_hard_failures(tmp_path, reason):
    store, _ = quarantined(tmp_path, reason)
    with pytest.raises(JobStoreError, match="exact_pre_motion"):
        store.reopen_editorial_timing_failure(
            video_job_id="same", revision="not-authorized"
        )
    assert store.job("same")["state"] == "QUARANTINED"


def phrase_fixture(tmp_path, monkeypatch, *, available=3):
    import kokoro_onnx

    calls = []

    class Engine:
        def __init__(self, *args):
            pass

        def create(self, text, **kwargs):
            calls.append((text, kwargs))
            return np.ones(24000, dtype=np.float32) * 0.1, 24000

    monkeypatch.setattr(kokoro_onnx, "Kokoro", Engine)
    model, voices = tmp_path / "model", tmp_path / "voices"
    model.write_bytes(b"explicit-model-fixture")
    voices.write_bytes(b"explicit-voices-fixture")
    text = "Numbers and qualifiers stay unchanged."
    lock = dict(
        voice="af_heart",
        speed=1.06,
        lang="en-us",
        canonical_spoken_transcript=dict(
            canonical_transcript_hash="c" * 64,
            plain_text=text,
            segments=[
                dict(
                    segment_id="one",
                    text=text,
                    actual_audio_duration_seconds=available,
                    timeline_start_seconds=0.18,
                    audio={"sha256": "d" * 64},
                )
            ],
        ),
    )
    return dict(
        timing_lock=lock,
        editor={"narration_segments": [dict(segment_id="one", text=text)]},
        model_path=model,
        voices_path=voices,
        output_dir=tmp_path / "revision",
        media_duration_seconds=5,
    ), calls


def test_phrase_cues_bound_to_actual_audio_and_tamper_rejected(tmp_path, monkeypatch):
    spec, calls = phrase_fixture(tmp_path, monkeypatch)
    result = measured_phrase_narration(**spec)
    cue = result["segments"][0]
    assert cue["actual_audio_duration_seconds"] == 1
    assert cue["timeline_start_seconds"] == 0.18
    assert result["voice_speed_changed"] is False
    assert calls[0][1]["speed"] == 1.06
    replay = measured_phrase_narration(**spec)
    assert len(calls) == 1
    assert replay["audio"]["sha256"] == result["audio"]["sha256"]
    Path(cue["audio_path"]).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="cache drift"):
        measured_phrase_narration(**spec)


def test_overflow_never_creates_accepted_audio_or_changes_speed(tmp_path, monkeypatch):
    spec, calls = phrase_fixture(tmp_path, monkeypatch, available=0.4)
    result = measured_phrase_narration(**spec)
    assert result["result"] == "HOLD_PHRASE_AUDIO_WINDOW_OVERFLOW"
    assert "audio" not in result
    assert not (spec["output_dir"] / "phrase_narration.wav").exists()
    assert calls[0][1]["speed"] == 1.06
