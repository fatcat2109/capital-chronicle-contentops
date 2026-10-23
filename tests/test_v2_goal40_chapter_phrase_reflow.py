import json

import numpy as np
import pytest
import soundfile as sf

from video.freeform_chapter_pipeline_v1.native_narrative import (
    reflow_native_chapter_phrases,
)
from video.unattended_core_factory_v1.creative import hash_file, hash_value


def fixture(tmp_path):
    def write(name, value):
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value), encoding="utf-8")
        return p

    text = "A measured phrase preserves the source words."
    original = tmp_path / "original.wav"
    sf.write(original, np.ones(24000, dtype=np.float32) * 0.1, 24000, subtype="PCM_24")
    cache = tmp_path / "cache"
    cache.mkdir()
    cache_identity = dict(
        phrase_geometry=dict(width=43, max_words=14),
        model_sha256="a" * 64,
        voices_sha256="b" * 64,
    )
    write("cache/source_identity.json", cache_identity)
    key = hash_value(
        dict(
            text=text,
            route=("af_heart", 1.06, "en-us"),
            engine="kokoro-v1.0",
            model_sha256="a" * 64,
            voices_sha256="b" * 64,
        )
    )
    wave = cache / (key + ".wav")
    sf.write(wave, np.ones(48000, dtype=np.float32) * 0.1, 24000, subtype="PCM_24")
    write(
        "cache/" + key + ".identity.json",
        dict(identity=key, audio_sha256=hash_file(wave)),
    )
    measured = write(
        "cache/phrase_revision_receipt.json",
        dict(result="HOLD_PHRASE_AUDIO_WINDOW_OVERFLOW"),
    )
    lock = write(
        "lock.json",
        dict(
            identity=dict(normalized_chapters=[dict(chapter_id="CH01", narration=text)])
        ),
    )
    audio = write(
        "audio.json",
        dict(
            actual_narration=dict(
                sample_rate_hz=24000,
                voice="af_heart",
                speed=1.06,
                lang="en-us",
                placements=[
                    dict(
                        segment_id="CH01",
                        segment_text_sha256=hash_value(text),
                        audio=dict(path=str(original), sha256=hash_file(original)),
                    )
                ],
            )
        ),
    )
    returned = write(
        "return.json",
        dict(
            kind="LONGFORM_CHAPTER_TIMING_CORRECTION",
            artifact=dict(
                chapter_manifest=dict(
                    format_contract=dict(duration_seconds=300),
                    chapters=[dict(id="CH01", duration_frames=9000)],
                ),
                chapter_timing_records=[
                    dict(
                        chapter_id="CH01",
                        global_start_frame=0,
                        duration_frames=9000,
                        narration_start_seconds=0.18,
                        actual_phrase_duration_seconds=2,
                        source_narration_text_sha256=hash_value(text),
                        original_narration_audio_sha256=hash_file(original),
                    )
                ],
            ),
        ),
    )
    inventory = write(
        "inventory.json",
        dict(
            phrases=[
                dict(
                    phrase_id="CH01-01",
                    text=text,
                    synthesis_text=text,
                    cache_key=key,
                    path=str(wave),
                    sha256=hash_file(wave),
                    frames=48000,
                    sample_rate_hz=24000,
                    duration_seconds=2,
                )
            ]
        ),
    )
    write(
        "chapter_source_admission.json",
        dict(
            native_return=dict(path=str(returned), sha256=hash_file(returned)),
            identity=dict(
                request_bindings={
                    k: dict(checked_path=str(p), request_sha256=hash_file(p))
                    for k, p in dict(
                        source_narrative_lock=lock,
                        actual_narration=audio,
                        measured_phrases=measured,
                        complete_phrase_inventory=inventory,
                    ).items()
                }
            ),
        ),
    )
    return dict(output_dir=tmp_path), wave, text, returned


def test_reflow_preserves_words_and_uses_actual_cached_audio_without_synthesis(
    tmp_path,
):
    spec, wave, text, _ = fixture(tmp_path)
    result = reflow_native_chapter_phrases(**spec)
    assert result["result"] == "MEASURED_PHRASE_NARRATION_READY"
    assert result["actual_synthesis_count"] == 0
    assert result["segments"][0]["text"] == text
    assert result["segments"][0]["actual_audio_duration_seconds"] == 2
    assert result["segments"][0]["timeline_start_seconds"] == 0.18
    assert result["segments"][0]["source_audio_sha256"] == hash_file(wave)
    assert result["voice_speed_changed"] is False
    assert reflow_native_chapter_phrases(**spec)["audio"] == result["audio"]
    wave.write_bytes(b"changed audio")
    with pytest.raises(ValueError, match="audio drift"):
        reflow_native_chapter_phrases(**spec)


def test_reflow_rejects_changed_native_return_before_writing_media(tmp_path):
    spec, _, _, returned = fixture(tmp_path)
    returned.write_text("changed timing")
    with pytest.raises(ValueError, match="timing return drift"):
        reflow_native_chapter_phrases(**spec)
    assert not (tmp_path / "reflowed_phrases").exists()


def test_reflow_rejects_wave_and_colocated_sidecar_replaced_together(tmp_path):
    spec, wave, _, _ = fixture(tmp_path)
    sf.write(wave, np.ones(48000, dtype=np.float32) * 0.2, 24000, subtype="PCM_24")
    sidecar = wave.with_suffix(".identity.json")
    seal = json.loads(sidecar.read_text())
    seal["audio_sha256"] = hash_file(wave)
    sidecar.write_text(json.dumps(seal))
    with pytest.raises(ValueError, match="inventory mismatch or audio drift"):
        reflow_native_chapter_phrases(**spec)
    assert not (tmp_path / "reflowed_phrases").exists()
