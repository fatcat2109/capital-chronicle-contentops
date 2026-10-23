"""Bind current native localization to existing local audio and locale owners.

No model invocation, provider fallback, picture rendering or platform transport.
Translation judgment is an explicit native input; deterministic checks bind source
identity, measured phrase timing, voice route, artifacts and same-picture output.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import soundfile as sf

from video.unattended_core_factory_v1.creative import hash_file, hash_value
from video.unattended_core_factory_v1 import media
from video.locale_activation_hardening_v1 import factory as locale_owner
from .package_factory import write_caption_artifacts, build_publication_package


def build_current_locale(
    *,
    return_path: Path,
    request_path: Path,
    source_package_path: Path,
    model_path: Path,
    voices_path: Path,
    output_dir: Path,
    registry_path: Path,
    bed_path: Path,
) -> dict:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    value = json.loads(return_path.read_text(encoding="utf-8"))
    if (
        request.get("kind") != "LOCALIZED_EDITORIAL"
        or value.get("request_sha256") != hash_value(request)
        or request.get("requested_model") != "gpt-5.6-sol"
        or request.get("requested_reasoning_effort") != "xhigh"
        or value.get("bindings") != request.get("bindings")
        or request.get("public_write_authority") is not False
    ):
        raise ValueError("Exact immutable native localization request required")
    if (
        value.get("kind"),
        value.get("model"),
        value.get("reasoning_effort"),
        value.get("provenance_limit"),
    ) != (
        "LOCALIZED_EDITORIAL",
        "gpt-5.6-sol",
        "xhigh",
        "ASSIGNED_ROLE_NOT_INDEPENDENT_RUNTIME_ATTESTATION",
    ) or not value.get("native_task_id"):
        raise ValueError("Exact native localization role required")
    for binding in request["bindings"].values():
        if hash_file(binding["path"]) != binding["sha256"]:
            raise ValueError("Native localization source bytes drift")
    if (
        Path(value["bindings"]["current_package"]["path"]).resolve()
        != source_package_path.resolve()
    ):
        raise ValueError("Localization current package identity mismatch")
    package = json.loads(source_package_path.read_text(encoding="utf-8"))
    for record in package["artifacts"].values():
        if record and hash_file(record["path"]) != record["sha256"]:
            raise ValueError("Localization package artifact drift")
    timing = json.loads(
        Path(value["bindings"]["timing_lock"]["path"]).read_text(encoding="utf-8")
    )
    source = timing["canonical_spoken_transcript"]
    if (
        package.get("canonical_transcript_hash") != source["canonical_transcript_hash"]
        or package.get("narration_timing_lock_hash") != timing["timing_lock_hash"]
    ):
        raise ValueError("Localization timing lock is not current package timing")
    localized = value["artifact"]
    governed = json.loads(
        Path(value["bindings"]["governed_input"]["path"]).read_text(encoding="utf-8")
    )
    if governed["story_id"] != package["source_story_id"]:
        raise ValueError("Locale governed source story mismatch")
    if (
        localized.get("source_story_id") != package["source_story_id"]
        or localized.get("source_film_id") != package["source_film_id"]
    ):
        raise ValueError("Localization story/run identity mismatch")
    language = localized["locale"]
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    # This current local demonstration is bounded to the retained Spanish route.
    if language != "es" or localized["voice_route"] != registry["entries"][language]:
        raise ValueError("Existing exact Spanish voice candidate required")
    route = registry["entries"][language]
    if (
        route["provider"] != "kokoro-onnx"
        or route["voice_identity"] != "ef_dora"
        or route["settings"]["short_speed"] != 1.45
    ):
        raise ValueError("Unapproved locale voice or speed")
    if (
        localized["source_package_id"] != package["package_id"]
        or localized["source_canonical_transcript_hash"]
        != source["canonical_transcript_hash"]
    ):
        raise ValueError("Localized transcript/package source mismatch")
    translated = localized["segments"]
    if [s["segment_id"] for s in translated] != [
        s["segment_id"] for s in source["segments"]
    ]:
        raise ValueError("Localized segment identity/order mismatch")
    for a, b in zip(source["segments"], translated, strict=True):
        if a["text"] != b["original_text"] or b["source_text_sha256"] != hash_value(
            a["text"]
        ):
            raise ValueError("Localized segment text source mismatch")
        if " ".join(p["text"] for p in b["phrases"]) != b["translated_text"]:
            raise ValueError("Localized phrases do not preserve translated wording")
        if any(
            len(p["caption_text"].splitlines()) > 2 or not p["spoken_text"].strip()
            for p in b["phrases"]
        ):
            raise ValueError("Localized phrase/caption contract invalid")
        allowed_anchors = {anchor["anchor_id"] for anchor in governed["anchors"]}
        if any(
            binding.get("source_anchor_id") is not None
            and binding["source_anchor_id"] not in allowed_anchors
            for binding in b["anchor_bindings"]
        ):
            raise ValueError("Locale anchor is outside governed source")
    # Values are required independently of the native role's semantic self-report.
    anchors = {a["anchor_id"]: a for s in translated for a in s["anchor_bindings"]}
    expected_values = {
        "RET001.TOTAL_SALES": (763600, "million_USD"),
        "RET001.MONTH_OVER_MONTH": (-0.6, "percent"),
        "RET001.YEAR_OVER_YEAR": (5.0, "percent"),
        "RET003.MONTH_OVER_MONTH": (-1.8, "percent"),
        "RET004.MONTH_OVER_MONTH": (-2.2, "percent"),
        "RET005.MONTH_OVER_MONTH": (0.5, "percent"),
        "RET001.REPORT_MONTH": ("2026-07", "calendar_month"),
        "RET001.COMPARISON_MONTH": ("2025-07", "calendar_month"),
    }
    for key, expected in expected_values.items():
        if (
            key not in anchors
            or (anchors[key]["numeric_value"], anchors[key]["unit"]) != expected
        ):
            raise ValueError("Localized numeric value/unit mismatch:" + key)
    if not {
        "price_change_adjustment_negation_preserved",
        "trading_day_adjustment_preserved",
    } <= set(anchors["RET006.ADJUSTMENT_BOUNDARY"]["qualifiers"]):
        raise ValueError("Localized methodology negation/qualifier missing")
    output_dir.mkdir(parents=True, exist_ok=True)
    identity = dict(
        native_request_sha256=hash_file(request_path),
        native_return_sha256=hash_file(return_path),
        source_package_sha256=hash_file(source_package_path),
        model_sha256=hash_file(model_path),
        voices_sha256=hash_file(voices_path),
        registry_sha256=hash_file(registry_path),
    )
    seal = output_dir / "source_identity.json"
    if seal.exists() and json.loads(seal.read_text(encoding="utf-8")) != identity:
        raise ValueError("Changed locale source requires distinct revision")
    seal.write_text(json.dumps(identity, sort_keys=True) + "\n", encoding="utf-8")
    receipt_path = output_dir / "locale_receipt.json"
    if receipt_path.exists():
        prior = json.loads(receipt_path.read_text(encoding="utf-8"))
        if prior["result"] == "PRIVATE_CURRENT_LOCALE_PACKAGE_BUILT":
            manifest = json.loads(Path(prior["manifest"]).read_text(encoding="utf-8"))
            for record in manifest["artifacts"].values():
                if record and hash_file(record["path"]) != record["sha256"]:
                    raise ValueError("Current locale artifact drift")
            return dict(prior, idempotent_replay=True)
    from kokoro_onnx import Kokoro
    from .localized_audio import synthesize

    engine = Kokoro(str(model_path), str(voices_path))
    phrases, caption_texts, holds, measurements = [], {}, [], []
    picture = Path(package["artifacts"]["canonical_picture"]["path"])
    picture_identity = locale_owner.inspect_picture(picture)
    duration = picture_identity["video_duration_seconds"]
    for index, (original, segment) in enumerate(
        zip(source["segments"], translated, strict=True)
    ):
        total = 0.0
        for ordinal, phrase in enumerate(segment["phrases"]):
            cue_id = f"{segment['segment_id']}-{ordinal + 1:02d}"
            cache_id = hash_value(
                dict(
                    spoken=phrase["spoken_text"],
                    route=route,
                    model=identity["model_sha256"],
                    voices=identity["voices_sha256"],
                )
            )
            path = output_dir / (cache_id + ".wav")
            cache_seal = path.with_suffix(".identity.json")
            if path.exists():
                if not cache_seal.exists() or json.loads(cache_seal.read_text())[
                    "audio_sha256"
                ] != hash_file(path):
                    raise ValueError("Localized phrase cache drift")
                audio, rate = sf.read(path, dtype="float32")
                if rate != locale_owner.SAMPLE_RATE:
                    raise ValueError("Locale cache sample rate mismatch")
            else:
                audio = synthesize(
                    engine,
                    phrase["spoken_text"],
                    voice="ef_dora",
                    speed=1.45,
                    lang="es",
                )
                sf.write(path, audio, locale_owner.SAMPLE_RATE, subtype="PCM_24")
                cache_seal.write_text(
                    json.dumps(dict(audio_sha256=hash_file(path), cache_id=cache_id))
                    + "\n"
                )
            measured = len(audio) / locale_owner.SAMPLE_RATE
            total += measured
            phrases.append(
                locale_owner.SynthesizedPhrase(
                    cue_id,
                    segment["segment_id"],
                    phrase["text"],
                    phrase["spoken_text"],
                    0.0,
                    measured,
                    str(path.resolve()),
                    hash_file(path),
                )
            )
            caption_texts[cue_id] = phrase["caption_text"]
        start = float(original["timeline_start_seconds"])
        end = (
            float(source["segments"][index + 1]["timeline_start_seconds"])
            if index + 1 < len(source["segments"])
            else duration - locale_owner.FINAL_HEADROOM_SECONDS
        )
        total += locale_owner.BETWEEN_PHRASES_SECONDS * max(
            0, len(segment["phrases"]) - 1
        )
        measurements.append(
            dict(
                segment_id=segment["segment_id"],
                measured_seconds=total,
                available_seconds=end - start,
            )
        )
        if total > end - start + 0.001:
            holds.append(measurements[-1])
    receipt = dict(
        result="HOLD_LOCALE_WINDOW_OVERFLOW" if holds else "LOCALE_MEASURED",
        holds=holds,
        measurements=measurements,
        native_task_id=value["native_task_id"],
        identity=identity,
        voice_candidate_status=route["acceptance_status"],
        hearing="NOT_VERIFIED",
        translation_semantic_review="NATIVE_ASSIGNED_ROLE_PLUS_EXACT_SOURCE_NUMERIC_BINDING_CHECKS",
        public_write_authority=False,
        picture_render_count=0,
        external_cost_usd=0,
        speed_changed_from_registry=False,
    )
    if not holds:
        aligned, alignment = locale_owner.align_phrases_to_source_windows(
            locale=language,
            phrases=phrases,
            source_segments=source["segments"],
            picture_duration=duration,
        )
        narration = locale_owner._write_aligned_audio_program(
            locale=language,
            phrases=aligned,
            output=output_dir / "narration.wav",
            picture_duration=duration,
        )
        speech = locale_owner.meaningful_speech_bounds(Path(narration["path"]))
        alignment.update(
            meaningful_speech_start_seconds=speech["speech_start_seconds"],
            meaningful_speech_end_seconds=speech["speech_end_seconds"],
        )
        alignment.pop("timeline_alignment_hash", None)
        alignment["timeline_alignment_hash"] = hash_value(alignment)
        validation = locale_owner.validate_timeline_alignment(
            alignment,
            source_segments=source["segments"],
            picture_duration=duration,
            strict_inside_windows=True,
        )
        captions = write_caption_artifacts(
            dict(
                schema="contentops.v2.timed_captions.v1",
                language=language,
                media_duration_seconds=duration,
                cues=[
                    dict(
                        cue_id=p.cue_id,
                        start_seconds=p.start_seconds,
                        end_seconds=p.start_seconds + p.duration_seconds,
                        text=caption_texts[p.cue_id],
                        source_audio_sha256=p.audio_sha256,
                    )
                    for p in aligned
                ],
            ),
            output_dir / "captions",
        )
        mix = media.build_audio_mix(
            picture=picture,
            timing_lock=dict(
                actual_total_narration_duration_seconds=speech["speech_end_seconds"],
                locked_narration_audio=narration,
            ),
            bed_path=bed_path,
            output_dir=output_dir / "audio",
        )
        mux = locale_owner.mux_picture_identical_locale(
            picture=picture,
            audio=Path(mix["mix"]["path"]),
            output=output_dir / "locale.es.mp4",
            source_picture=picture_identity,
        )
        spec = {
            k: v
            for k, v in package.items()
            if k
            not in {
                "artifacts",
                "package_id",
                "generation_timestamp_utc",
                "transport",
                "publication_state",
            }
        }
        spec.update(
            language=language,
            canonical_picture=str(output_dir / "locale.es.mp4"),
            audio=mix["mix"]["path"],
            burned_caption_video=None,
            **{"caption_" + k: v["path"] for k, v in captions.items()},
            metadata={k: localized[k] for k in ("title", "description", "social_copy")},
            chapters=[],
            generation_version="goal40-current-native-locale-es",
        )
        # New locale identity may not inherit English narration/SEO claims.
        for key in (
            "canonical_transcript_identity",
            "seo_derivation",
            "canonical_transcript_hash",
            "voiceover_qa_hash",
            "narration_timing_lock_hash",
            "seo_package_hash",
            "final_mux",
            "final_audio",
        ):
            spec.pop(key, None)
        localized_package = build_publication_package(spec)
        manifest = output_dir / "manifest.json"
        manifest.write_text(
            json.dumps(localized_package, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        for filename, payload in (
            ("alignment.json", alignment),
            (
                "localized_transcript.json",
                dict(
                    language=language,
                    source_transcript_hash=source["canonical_transcript_hash"],
                    phrases=[asdict(p) for p in aligned],
                ),
            ),
            ("editorial.json", localized),
        ):
            (output_dir / filename).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        receipt.update(
            result="PRIVATE_CURRENT_LOCALE_PACKAGE_BUILT",
            manifest=str(manifest.resolve()),
            package_id=localized_package["package_id"],
            picture_identity=mux,
            alignment_validation=validation,
        )
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt
