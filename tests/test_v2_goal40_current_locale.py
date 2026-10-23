import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from video.freeform_chapter_pipeline_v1.current_locale import build_current_locale
from video.unattended_core_factory_v1.creative import hash_value
from video.unattended_core_factory_v1.media import artifact
from video.unattended_core_factory_v1.store import V2JobStore
from video.unattended_core_factory_v1.supervisor import DesktopSessionV2Factory


def locale_fixture(tmp_path):
    def write(name, value):
        path = tmp_path / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    picture = tmp_path / "picture.fixture"
    picture.write_bytes(b"explicit non-media guard fixture; never rendered")
    source_text = "A dated source sentence."
    source_hash = "a" * 64
    lock = write(
        "timing.json",
        dict(
            timing_lock_hash="b" * 64,
            canonical_spoken_transcript=dict(
                canonical_transcript_hash=source_hash,
                segments=[dict(segment_id="one", text=source_text)],
            ),
        ),
    )
    package = write(
        "package.json",
        dict(
            package_id="pkg_fixture",
            source_story_id="fixture",
            source_film_id="run_fixture",
            canonical_transcript_hash=source_hash,
            narration_timing_lock_hash="b" * 64,
            artifacts={"canonical_picture": artifact(picture)},
        ),
    )
    registry_path = (
        Path(__file__).resolve().parents[1]
        / "video/freeform_chapter_pipeline_v1/voice_registry.json"
    )
    voice = json.loads(registry_path.read_text())["entries"]["es"]
    governed = write("governed.json", dict(story_id="fixture", anchors=[]))
    returned = dict(
        kind="LOCALIZED_EDITORIAL",
        model="gpt-5.6-sol",
        reasoning_effort="xhigh",
        native_task_id="/root/fixture",
        provenance_limit="ASSIGNED_ROLE_NOT_INDEPENDENT_RUNTIME_ATTESTATION",
        bindings={
            "current_package": artifact(package),
            "timing_lock": artifact(lock),
            "governed_input": artifact(governed),
        },
        artifact=dict(
            locale="es",
            source_package_id="pkg_fixture",
            source_story_id="fixture",
            source_film_id="run_fixture",
            source_canonical_transcript_hash=source_hash,
            voice_route=copy.deepcopy(voice),
            segments=[
                dict(
                    segment_id="one",
                    original_text=source_text,
                    source_text_sha256=hash_value(source_text),
                    translated_text="Una frase fechada.",
                    phrases=[
                        dict(
                            text="Una frase fechada.",
                            caption_text="Una frase fechada.",
                            spoken_text="Una frase fechada.",
                        )
                    ],
                )
            ],
        ),
    )
    request = dict(
        kind="LOCALIZED_EDITORIAL",
        requested_model="gpt-5.6-sol",
        requested_reasoning_effort="xhigh",
        bindings=copy.deepcopy(returned["bindings"]),
        public_write_authority=False,
    )
    request_path = write("request.json", request)
    returned["request_sha256"] = hash_value(request)
    returned_path = write("native.json", returned)
    spec = dict(
        return_path=returned_path,
        request_path=request_path,
        source_package_path=package,
        model_path=tmp_path / "not-needed-model",
        voices_path=tmp_path / "not-needed-voices",
        output_dir=tmp_path / "output",
        registry_path=registry_path,
        bed_path=tmp_path / "not-needed-bed",
    )
    return spec, returned


def test_current_locale_rejects_return_rebinding_without_exact_request(tmp_path):
    spec, returned = locale_fixture(tmp_path)
    returned["request_sha256"] = "c" * 64
    spec["return_path"].write_text(json.dumps(returned))
    with pytest.raises(ValueError, match="immutable native localization request"):
        build_current_locale(**spec)
    assert not spec["output_dir"].exists()


@pytest.mark.parametrize(
    "mutation,error",
    [
        ("voice", "Existing exact Spanish voice candidate"),
        ("timing", "immutable native localization request"),
        ("text", "segment text source mismatch"),
        ("binding", "source bytes drift"),
    ],
)
def test_current_locale_rejects_voice_source_and_timing_drift_before_synthesis(
    tmp_path, mutation, error
):
    spec, returned = locale_fixture(tmp_path)
    if mutation == "voice":
        returned["artifact"]["voice_route"]["settings"]["short_speed"] = 1.8
    elif mutation == "timing":
        returned["artifact"]["source_canonical_transcript_hash"] = "c" * 64
        # Bind exact bytes of another timing vintage, despite an otherwise valid return.
        path = Path(returned["bindings"]["timing_lock"]["path"])
        timing = json.loads(path.read_text())
        timing["canonical_spoken_transcript"]["canonical_transcript_hash"] = "c" * 64
        path.write_text(json.dumps(timing))
        returned["bindings"]["timing_lock"] = artifact(path)
    elif mutation == "text":
        returned["artifact"]["segments"][0]["original_text"] = (
            "Another source sentence."
        )
    else:
        spec["source_package_path"].write_text("Changed after native return")
    spec["return_path"].write_text(json.dumps(returned), encoding="utf-8")
    with pytest.raises(ValueError, match=error):
        build_current_locale(**spec)
    assert not spec["output_dir"].exists()


def test_locale_descendant_preserves_sealed_job_state_and_deduplicates(tmp_path):
    owner = object.__new__(DesktopSessionV2Factory)
    owner.store = V2JobStore(tmp_path / "jobs.sqlite3")
    owner.config = SimpleNamespace(runtime_root=tmp_path)
    owner.store.seed_job(
        video_job_id="source",
        input_packet_path=tmp_path / "input.json",
        input_packet_hash="a" * 64,
        target_format="SHORT",
    )
    job = owner.store.claim_next(worker_id="test", implementation_head="b" * 40)
    owner.store.finalize(
        video_job_id="source",
        run_id=job["run_id"],
        result="PRIVATE_ENGINEERING_PACKAGE_REVIEW_REQUIRED",
        state="OWNER_REVIEW_READY",
    )
    root = tmp_path / "jobs/source/revisions/es"
    root.mkdir(parents=True)
    manifest = root / "manifest.json"
    manifest.write_text(
        json.dumps(
            dict(
                schema="contentops.v2.platform_neutral_publication_package.v1",
                language="es",
                source_film_id=job["run_id"],
                artifacts={},
            )
        )
    )
    receipt = dict(
        result="PRIVATE_CURRENT_LOCALE_PACKAGE_BUILT",
        manifest=str(manifest),
        identity={"source_package_sha256": "c" * 64},
    )
    for name in ("locale_receipt.json", "alignment.json", "localized_transcript.json"):
        (root / name).write_text(
            json.dumps(receipt if name == "locale_receipt.json" else {"fixture": True})
        )
    owner.accept_current_locale_package(video_job_id="source", receipt=receipt)
    after = owner.store.job("source")
    assert after["state"] == after["last_valid_checkpoint"] == "OWNER_REVIEW_READY"
    assert after["run_id"] == job["run_id"]
    count = len(owner.store.events("source"))
    replay = owner.accept_current_locale_package(video_job_id="source", receipt=receipt)
    assert replay["ledger_idempotent_replay"] is True
    assert len(owner.store.events("source")) == count
    assert owner.current_locale_package_path("source", "es") == manifest
