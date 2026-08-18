"""Bounded Task-2 locale audio timeline correction without TTS or picture rerender."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import soundfile as sf

from video.locale_activation_hardening_v1.factory import (
    LOCALIZED_TRANSCRIPT_SCHEMA,
    MAX_UNEXPLAINED_FINAL_TAIL_SECONDS,
    PACKAGE_SCHEMA,
    SynthesizedPhrase,
    _assert_no_forbidden_keys,
    _build_transcript_and_captions,
    _caption_lines,
    _metadata_from_transcript,
    _sample,
    _sha256_file,
    _source_segment_windows,
    _split_phrases,
    _write_aligned_audio_program,
    _write_json,
    align_phrases_to_source_windows,
    inspect_picture,
    meaningful_speech_bounds,
    mux_picture_identical_locale,
    validate_timeline_alignment,
    validate_translation_packet,
)
from video.unattended_core_factory_v1.creative import canonical_bytes, hash_value
from video.unattended_core_factory_v1.media import artifact


CORRECTION_TASK_ID = "TASK_CONTENTOPS_V2_LOCALE_AUDIO_TIMELINE_ALIGNMENT_BOUNDED_CORRECTION_V1"
CORRECTION_RESULT = "PASS_V2_LOCALE_AUDIO_TIMELINE_ALIGNMENT_CORRECTION_READY_FOR_OWNER_REVIEW"


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _recover_existing_phrases(
    *, locale: str, localized: Mapping[str, Any], prior_locale_root: Path
) -> list[SynthesizedPhrase]:
    transcript = _load(prior_locale_root / "localized_transcript.json")
    captions = _load(prior_locale_root / "captions" / f"captions.{locale}.json")
    if transcript.get("schema") != LOCALIZED_TRANSCRIPT_SCHEMA or transcript.get("locale") != locale:
        raise ValueError(f"prior_localized_transcript_identity_invalid:{locale}")
    caption_by_id = {str(value["cue_id"]): value for value in captions["cues"]}
    transcript_by_id = {str(value["segment_id"]): value for value in transcript["segments"]}
    phrases: list[SynthesizedPhrase] = []
    ordinal = 0
    for segment in localized["segments"]:
        segment_id = str(segment["segment_id"])
        expected = _split_phrases(str(segment["text"]), str(segment["synthesis_text"]))
        cue_ids = [str(value) for value in transcript_by_id[segment_id]["cue_ids"]]
        if len(cue_ids) != len(expected):
            raise ValueError(f"prior_phrase_identity_count_mismatch:{locale}:{segment_id}")
        for cue_id, (display, spoken) in zip(cue_ids, expected):
            ordinal += 1
            cue = caption_by_id[cue_id]
            audio_path = prior_locale_root / "audio" / "segments" / f"{ordinal:02d}_{segment_id}.wav"
            if not audio_path.is_file():
                raise ValueError(f"prior_synthesized_phrase_missing:{locale}:{cue_id}")
            audio_sha = _sha256_file(audio_path)
            if cue.get("source_audio_sha256") != audio_sha:
                raise ValueError(f"prior_synthesized_phrase_hash_mismatch:{locale}:{cue_id}")
            if str(cue.get("text", "")) != _caption_lines(display, locale=locale):
                raise ValueError(f"prior_caption_phrase_text_mismatch:{locale}:{cue_id}")
            phrases.append(
                SynthesizedPhrase(
                    cue_id=cue_id,
                    source_segment_id=segment_id,
                    text=display,
                    synthesis_text=spoken,
                    start_seconds=float(cue["start_seconds"]),
                    duration_seconds=round(float(sf.info(audio_path).duration), 6),
                    audio_path=str(audio_path.resolve()),
                    audio_sha256=audio_sha,
                )
            )
    return phrases


def build_existing_timing_artifact(
    *,
    locale: str,
    prior_locale_root: Path,
    source_segments: Sequence[Mapping[str, Any]],
    picture_duration: float,
) -> dict[str, Any]:
    """Derive deterministic actual placements for an unchanged Task-2 locale package."""
    transcript = _load(prior_locale_root / "localized_transcript.json")
    captions = _load(prior_locale_root / "captions" / f"captions.{locale}.json")
    package = _load(prior_locale_root / "package_manifest.json")
    audio_path = Path(str(package["localized_audio"]["path"]))
    if _sha256_file(audio_path) != package["localized_audio"]["sha256"]:
        raise ValueError(f"prior_locale_audio_hash_mismatch:{locale}")
    windows = _source_segment_windows(source_segments, picture_duration=picture_duration)
    cues = {str(value["cue_id"]): value for value in captions["cues"]}
    segments: list[dict[str, Any]] = []
    for source_window, localized_segment in zip(windows, transcript["segments"]):
        segment_id = str(localized_segment["segment_id"])
        if segment_id != source_window["source_segment_id"]:
            raise ValueError(f"prior_locale_source_segment_identity_mismatch:{locale}")
        placements = []
        for cue_id in localized_segment["cue_ids"]:
            cue = cues[str(cue_id)]
            start = float(cue["start_seconds"])
            end = float(cue["end_seconds"])
            placements.append(
                {
                    "cue_id": str(cue_id),
                    "source_segment_id": segment_id,
                    "timeline_start_seconds": round(start, 6),
                    "actual_audio_duration_seconds": round(end - start, 6),
                    "timeline_end_seconds": round(end, 6),
                    "audio_sha256": str(cue["source_audio_sha256"]),
                }
            )
        segments.append(
            {
                **source_window,
                "actual_segment_start_seconds": placements[0]["timeline_start_seconds"],
                "actual_segment_end_seconds": placements[-1]["timeline_end_seconds"],
                "actual_synthesized_duration_seconds": round(
                    sum(value["actual_audio_duration_seconds"] for value in placements), 6
                ),
                "placement_mode": "LEGACY_TASK2_SOURCE_WINDOW_OVERLAP_AUDIT",
                "placements": placements,
            }
        )
    bounds = meaningful_speech_bounds(audio_path)
    timing = {
        "schema": "contentops.v2.localized_timeline_alignment.v1",
        "locale": locale,
        "picture_duration_seconds": round(float(picture_duration), 6),
        "max_unexplained_final_tail_seconds": MAX_UNEXPLAINED_FINAL_TAIL_SECONDS,
        "segments": segments,
        "localized_audio_sha256": package["localized_audio"]["sha256"],
        "meaningful_speech_start_seconds": bounds["speech_start_seconds"],
        "meaningful_speech_end_seconds": bounds["speech_end_seconds"],
        "intentional_ending_silence": False,
    }
    timing["timeline_alignment_hash"] = hash_value(timing)
    return timing


def _corrected_tts_receipt(
    *,
    prior_receipt: Mapping[str, Any],
    audio: Mapping[str, Any],
    timing: Mapping[str, Any],
) -> dict[str, Any]:
    receipt = {
        "schema": "contentops.v2.localized_tts_receipt.v2",
        "locale": "vi",
        "provider": prior_receipt["provider"],
        "model": prior_receipt["model"],
        "voice": prior_receipt["voice"],
        "language": prior_receipt["language"],
        "speed": prior_receipt["speed"],
        "transcript_hash": prior_receipt["transcript_hash"],
        "synthesis_text_hash": prior_receipt["synthesis_text_hash"],
        "audio": dict(audio),
        "actual_spoken_end_seconds": max(
            float(segment["actual_segment_end_seconds"]) for segment in timing["segments"]
        ),
        "meaningful_speech_start_seconds": timing["meaningful_speech_start_seconds"],
        "meaningful_speech_end_seconds": timing["meaningful_speech_end_seconds"],
        "final_meaningful_speech_tail_seconds": round(
            float(timing["picture_duration_seconds"])
            - float(timing["meaningful_speech_end_seconds"]),
            6,
        ),
        "audio_program_duration_seconds": timing["picture_duration_seconds"],
        "original_synthesis_requested_characters": prior_receipt["requested_characters"],
        "correction_requested_characters": 0,
        "correction_provider_request_count": 0,
        "elevenlabs_character_counter_delta": 0,
        "external_cost_usd": 0.0,
        "cost_status": "ZERO_NEW_TTS_REUSED_SHA_BOUND_TASK2_SEGMENTS",
        "pronunciation_corrections": list(prior_receipt["pronunciation_corrections"]),
        "timeline_alignment_hash": timing["timeline_alignment_hash"],
        "segment_placements": list(timing["segments"]),
        "synthesis_reuse_action": "REUSED_ALL_EXISTING_VIETNAMESE_SEGMENT_AUDIO_NO_PROVIDER_CALL",
        "secret_material_persisted": False,
    }
    receipt["tts_receipt_hash"] = hash_value(receipt)
    return receipt


def correct_vietnamese_timeline(
    *,
    source_job_root: Path,
    translations_path: Path,
    prior_proof_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    """Produce one corrected Vietnamese package from exact existing TTS segments."""
    source_job_root = source_job_root.resolve()
    prior_proof_root = prior_proof_root.resolve()
    output_root = output_root.resolve()
    timing_lock = _load(source_job_root / "artifacts" / "actual_narration_timing_lock.json")
    source_transcript = timing_lock["canonical_spoken_transcript"]
    source_package = _load(source_job_root / "package" / "platform_neutral_package_manifest.json")
    translations = _load(translations_path)
    validate_translation_packet(translations, source_transcript)
    localized = translations["locales"]["vi"]
    prior_locale_root = prior_proof_root / "locales" / "vi"
    prior_package = _load(prior_locale_root / "package_manifest.json")
    prior_receipt = _load(prior_locale_root / "tts_receipt.json")
    picture_path = source_job_root / "media" / "picture_lock.mp4"
    picture = inspect_picture(picture_path)
    if picture["video_stream_sha256"] != prior_package["accepted_picture"]["video_stream_sha256"]:
        raise ValueError("accepted_picture_stream_identity_changed_since_task2")

    recovered = _recover_existing_phrases(
        locale="vi", localized=localized, prior_locale_root=prior_locale_root
    )
    phrases, timing = align_phrases_to_source_windows(
        locale="vi",
        phrases=recovered,
        source_segments=source_transcript["segments"],
        picture_duration=picture["video_duration_seconds"],
    )
    locale_root = output_root / "locales" / "vi"
    narration = locale_root / "audio" / "narration.vi.wav"
    audio = _write_aligned_audio_program(
        locale="vi",
        phrases=phrases,
        output=narration,
        picture_duration=picture["video_duration_seconds"],
    )
    bounds = meaningful_speech_bounds(narration)
    timing.pop("timeline_alignment_hash", None)
    timing.update(
        {
            "localized_audio_sha256": audio["sha256"],
            "meaningful_speech_start_seconds": bounds["speech_start_seconds"],
            "meaningful_speech_end_seconds": bounds["speech_end_seconds"],
            "intentional_ending_silence": False,
        }
    )
    timing["timeline_alignment_hash"] = hash_value(timing)
    timing_qa = validate_timeline_alignment(
        timing,
        source_segments=source_transcript["segments"],
        picture_duration=picture["video_duration_seconds"],
        strict_inside_windows=True,
    )
    receipt = _corrected_tts_receipt(
        prior_receipt=prior_receipt, audio=audio, timing=timing
    )
    transcript, captions, caption_artifacts = _build_transcript_and_captions(
        locale="vi",
        localized=localized,
        source_hash=source_transcript["canonical_transcript_hash"],
        receipt=receipt,
        phrases=phrases,
        picture_duration=picture["video_duration_seconds"],
        output_root=locale_root,
    )
    metadata = _metadata_from_transcript(localized, transcript, phrases)
    transcript_artifact = _write_json(locale_root / "localized_transcript.json", transcript)
    metadata_artifact = _write_json(locale_root / "localized_metadata.json", metadata)
    tts_artifact = _write_json(locale_root / "tts_receipt.json", receipt)
    timing_artifact = _write_json(locale_root / "localized_timing.json", timing)
    mux_path = locale_root / "media" / "us-retail-short.vi.mp4"
    picture_identity = mux_picture_identical_locale(
        picture=picture_path,
        audio=narration,
        output=mux_path,
        source_picture=picture,
    )
    sample = _sample(phrases, locale_root / "audio" / "listening_sample.vi.wav")
    package = {
        "schema": PACKAGE_SCHEMA,
        "locale": "vi",
        "source_story_id": source_package["source_story_id"],
        "source_canonical_transcript_hash": source_transcript["canonical_transcript_hash"],
        "localized_transcript_hash": transcript["localized_transcript_hash"],
        "timeline_alignment_hash": timing["timeline_alignment_hash"],
        "accepted_picture": picture,
        "localized_mux": artifact(mux_path),
        "picture_identity_proof": picture_identity,
        "localized_audio": audio,
        "tts_receipt": tts_artifact,
        "localized_timing": timing_artifact,
        "timeline_alignment_qa": timing_qa,
        "localized_transcript": transcript_artifact,
        "captions": caption_artifacts,
        "metadata": metadata_artifact,
        "listening_sample": sample,
        "correction_lineage": {
            "task_id": CORRECTION_TASK_ID,
            "prior_package_id": prior_package["package_id"],
            "prior_audio_sha256": prior_package["localized_audio"]["sha256"],
            "picture_changed": False,
            "tts_resynthesis_count": 0,
        },
        "future_surfaces": prior_package["future_surfaces"],
        "hard_boundaries": {
            "video_public_write_authority": False,
            "v1_mutation_authority": False,
            "scheduler_mutation_authority": False,
            "picture_rerender_count": 0,
            "burned_captions": False,
        },
        "owner_listening_acceptance_claimed": False,
    }
    _assert_no_forbidden_keys(package)
    package["package_id"] = "locale_pkg_" + hashlib.sha256(canonical_bytes(package)).hexdigest()
    package_artifact = _write_json(locale_root / "package_manifest.json", package)
    result = {
        "locale": "vi",
        "package_id": package["package_id"],
        "package_manifest": package_artifact,
        "localized_transcript_hash": transcript["localized_transcript_hash"],
        "timeline_alignment_hash": timing["timeline_alignment_hash"],
        "audio_sha256": audio["sha256"],
        "caption_sha256": {key: value["sha256"] for key, value in caption_artifacts.items()},
        "metadata_sha256": metadata_artifact["sha256"],
        "mux_sha256": package["localized_mux"]["sha256"],
        "picture_stream_sha256": picture_identity["localized_mux"]["video_stream_sha256"],
        "frame_count": picture_identity["localized_mux"]["frame_count"],
        "speech_start_seconds": timing_qa["meaningful_speech_start_seconds"],
        "speech_end_seconds": timing_qa["meaningful_speech_end_seconds"],
        "final_tail_seconds": timing_qa["final_tail_seconds"],
        "tts_character_counter_delta": 0,
        "external_cost_usd": 0.0,
        "full_audio_path": str(narration),
        "sample_path": sample["artifact"]["path"],
        "caption_srt_path": caption_artifacts["srt"]["path"],
        "caption_vtt_path": caption_artifacts["vtt"]["path"],
        "localized_transcript_path": transcript_artifact["path"],
        "localized_timing_path": timing_artifact["path"],
        "final_package_path": str(mux_path),
    }
    return result


def run_bounded_correction(
    *,
    source_job_root: Path,
    translations_path: Path,
    prior_proof_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    timing_lock = _load(source_job_root / "artifacts" / "actual_narration_timing_lock.json")
    source_segments = timing_lock["canonical_spoken_transcript"]["segments"]
    picture = inspect_picture(source_job_root / "media" / "picture_lock.mp4")

    original_vi = build_existing_timing_artifact(
        locale="vi",
        prior_locale_root=prior_proof_root / "locales" / "vi",
        source_segments=source_segments,
        picture_duration=picture["video_duration_seconds"],
    )
    original_failure = None
    try:
        validate_timeline_alignment(
            original_vi,
            source_segments=source_segments,
            picture_duration=picture["video_duration_seconds"],
            strict_inside_windows=False,
        )
    except Exception as exc:  # exact fail-closed regression evidence
        original_failure = str(exc)
    if not original_failure or "localized_unexplained_final_tail_exceeds_limit" not in original_failure:
        raise ValueError("original_vietnamese_severe_tail_fixture_did_not_fail")

    unchanged: dict[str, Any] = {}
    for locale in ("zh-Hans", "hi", "ko"):
        prior_package = _load(prior_proof_root / "locales" / locale / "package_manifest.json")
        timing = build_existing_timing_artifact(
            locale=locale,
            prior_locale_root=prior_proof_root / "locales" / locale,
            source_segments=source_segments,
            picture_duration=picture["video_duration_seconds"],
        )
        unchanged[locale] = validate_timeline_alignment(
            timing,
            source_segments=source_segments,
            picture_duration=picture["video_duration_seconds"],
            strict_inside_windows=False,
        )
        unchanged[locale]["regenerated"] = False
        unchanged[locale]["resynthesized"] = False
        unchanged[locale]["package_id"] = prior_package["package_id"]
        unchanged[locale]["audio_sha256"] = prior_package["localized_audio"]["sha256"]
        unchanged[locale]["mux_sha256"] = prior_package["localized_mux"]["sha256"]

    vietnamese = correct_vietnamese_timeline(
        source_job_root=source_job_root,
        translations_path=translations_path,
        prior_proof_root=prior_proof_root,
        output_root=output_root,
    )
    receipt = {
        "schema": "contentops.v2.locale_audio_timeline_alignment_correction_receipt.v1",
        "task_id": CORRECTION_TASK_ID,
        "result": CORRECTION_RESULT,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_job_root": str(source_job_root.resolve()),
        "prior_task2_proof_root": str(prior_proof_root.resolve()),
        "source_canonical_transcript_hash": timing_lock["canonical_spoken_transcript"][
            "canonical_transcript_hash"
        ],
        "original_vietnamese_regression": {
            "result": "PASS_EXPECTED_FAILURE",
            "failure": original_failure,
            "speech_end_seconds": original_vi["meaningful_speech_end_seconds"],
            "final_tail_seconds": round(
                picture["video_duration_seconds"]
                - original_vi["meaningful_speech_end_seconds"],
                6,
            ),
        },
        "corrected_vietnamese": vietnamese,
        "unchanged_locale_timing_qa": unchanged,
        "picture_render_count": 0,
        "remotion_invocation_count": 0,
        "tts_provider_request_count": 0,
        "elevenlabs_character_counter_delta": 0,
        "cash_spend_usd": 0.0,
        "publication_attempt_count": 0,
        "v1_mutation_count": 0,
        "scheduler_mutation_count": 0,
        "owner_listening_acceptance_claimed": False,
        "next_task_started": False,
    }
    receipt["receipt_hash"] = hash_value(receipt)
    _assert_no_forbidden_keys(receipt)
    _write_json(output_root / "locale_audio_timeline_correction_receipt.json", receipt)
    return receipt
