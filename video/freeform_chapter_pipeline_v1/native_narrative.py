"""Native longform source/narrative ingress for the existing chapter pipeline.

This binds a saved creative return and measures local narration. It neither
invokes a model nor authors a compositor, and does not certify factual or audio
quality from provenance metadata.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from video.unattended_core_factory_v1.creative import hash_file, hash_value
from video.unattended_core_factory_v1.media import synthesize_narration


def admit_native_chapters(
    *,
    request_path: Path,
    return_path: Path,
    repo_root: Path,
    dependency_root: Path,
    scaffold_root: Path,
    output_dir: Path,
    request_owner_snapshot: Path | None = None,
) -> dict:
    """Seal native source for the existing chapter owner; no creative rewriting."""
    from video.unattended_core_factory_v1 import media
    from video.unattended_core_factory_v1.creative import (
        FORBIDDEN_SOURCE_PATTERNS,
        ALLOWED_IMPORTS,
    )
    from .pipeline import FreeformChapterPipeline
    import re
    import shutil

    request = json.loads(request_path.read_text(encoding="utf-8"))
    returned = json.loads(return_path.read_text(encoding="utf-8"))
    if (
        request.get("kind")
        not in {"LONGFORM_CHAPTER_MOTION", "LONGFORM_CHAPTER_TIMING_CORRECTION"}
        or returned.get("kind") != request.get("kind")
        or returned.get("request_sha256") != hash_value(request)
    ):
        raise ValueError("Exact native chapter request binding required")
    if (
        returned.get("model"),
        returned.get("reasoning_effort"),
        returned.get("provenance_limit"),
    ) != (
        "gpt-5.6-sol",
        "xhigh",
        "ASSIGNED_ROLE_NOT_INDEPENDENT_RUNTIME_ATTESTATION",
    ) or not returned.get("native_task_id"):
        raise ValueError("Assigned native chapter role required")
    repo_root = repo_root.resolve()
    verified_bindings = {}
    for name, binding in request["bindings"].items():
        original = Path(binding["path"])
        original = (repo_root / original).resolve()
        checked = original
        if name == "existing_chapter_owner" and request_owner_snapshot is not None:
            # Creative provenance stays pinned to the bytes the author received.
            # A separate execution owner may add engineering mechanics afterward.
            checked = request_owner_snapshot.resolve()
            if original != Path(__file__).with_name("pipeline.py").resolve():
                raise ValueError("Unexpected chapter execution owner")
        if (
            not checked.is_relative_to(repo_root)
            or hash_file(checked) != binding["sha256"]
        ):
            raise ValueError("Native chapter input bytes drift")
        verified_bindings[name] = dict(
            requested_path=str(original),
            checked_path=str(checked),
            request_sha256=binding["sha256"],
        )
    execution_owner = Path(__file__).with_name("pipeline.py").resolve()
    artifact = returned["artifact"]
    repo_root = repo_root.resolve()
    project = (repo_root / artifact["project_root"]).resolve()
    if not project.is_relative_to(repo_root / ".task-runtime"):
        raise ValueError("Native chapter project escape")
    seals = artifact["source_file_seals"]
    if {s["path"] for s in seals} != set(artifact["source_files"]):
        raise ValueError("Native source seals incomplete")
    for seal in [*seals, *artifact["asset_byte_verification"]]:
        path = (project / seal["path"]).resolve()
        if not path.is_relative_to(project) or hash_file(path) != seal["sha256"]:
            raise ValueError("Native chapter source/asset drift or escape")
        if seal in seals:
            source = path.read_text(encoding="utf-8")
            if any(
                re.search(pattern, source, re.I | re.M)
                for pattern, _ in FORBIDDEN_SOURCE_PATTERNS
            ) or re.search(r"\bAudio\b", source):
                raise ValueError("Native chapter source sandbox violation")
            for imported in re.findall(
                r"(?:from\s+|import\s*)['\"]([^'\"]+)['\"]", source
            ):
                if (
                    imported not in ALLOWED_IMPORTS
                    and not imported.startswith("./")
                    and not imported.startswith("../")
                ):
                    raise ValueError("Native chapter unsupported import")
                if imported.startswith(".") and not (
                    path.parent / imported
                ).resolve().is_relative_to(project / "src"):
                    raise ValueError("Native chapter import escape")
    output_dir.mkdir(parents=True, exist_ok=True)
    identity = dict(
        request_sha256=hash_value(request),
        native_return_sha256=hash_file(return_path),
        native_task_id=returned["native_task_id"],
        source_seals=seals,
        assets=artifact["asset_byte_verification"],
        request_bindings=verified_bindings,
        execution_owner=dict(
            path=str(execution_owner), sha256=hash_file(execution_owner)
        ),
    )
    admission = output_dir / "chapter_source_admission.json"
    if admission.exists() and json.loads(admission.read_text())["identity"] != identity:
        raise ValueError("Changed chapter source requires distinct admission revision")
    media.prepare_project(
        project_root=project,
        scaffold_root=scaffold_root,
        dependency_root=dependency_root,
        asset_root=project / "public",
    )
    lock = project / "package-lock.json"
    if not lock.exists():
        shutil.copy2(dependency_root.parent / "package-lock.json", lock)
    typecheck = media.typecheck_project(project, dependency_root)
    manifest = dict(artifact["chapter_manifest"])
    manifest["runtime_paths"] = dict(
        dependency_root=str(dependency_root.resolve()),
        browser_executable=str(
            media.resolve_remotion_browser_executable(dependency_root)
        ),
    )
    path = output_dir / "chapter_manifest.json"
    if path.exists() and json.loads(path.read_text()) != manifest:
        raise ValueError("Current chapter manifest changed")
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    owner = FreeformChapterPipeline(
        path, workspace=output_dir / "chapter_pipeline", repo_root=repo_root
    )
    contract = owner.validate()
    receipt = dict(
        result="NATIVE_CHAPTER_SOURCE_ADMITTED",
        identity=identity,
        manifest=str(path.resolve()),
        native_return=dict(
            path=str(return_path.resolve()), sha256=hash_file(return_path)
        ),
        manifest_sha256=hash_file(path),
        project_root=str(project),
        typecheck=typecheck,
        format_validation=contract,
        rendered=False,
        visual_acceptance=False,
        public_write_authority=False,
    )
    admission.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def render_native_chapter(
    *, manifest_path: Path, repo_root: Path, chapter_id: str, output_dir: Path
) -> dict:
    from .pipeline import FreeformChapterPipeline

    admission = json.loads(
        (output_dir / "chapter_source_admission.json").read_text(encoding="utf-8")
    )
    identity = admission["identity"]
    project = Path(admission["project_root"])
    for seal in [*identity["source_seals"], *identity["assets"]]:
        source = (project / seal["path"]).resolve()
        if not source.is_relative_to(project) or hash_file(source) != seal["sha256"]:
            raise ValueError("Admitted chapter source/asset drift before render")
    for binding in identity["request_bindings"].values():
        if hash_file(binding["checked_path"]) != binding["request_sha256"]:
            raise ValueError("Admitted chapter request input drift before render")
    execution = identity["execution_owner"]
    if (
        hash_file(execution["path"]) != execution["sha256"]
        or hash_file(manifest_path) != admission["manifest_sha256"]
    ):
        raise ValueError("Admitted chapter execution owner/manifest drift")
    owner = FreeformChapterPipeline(
        manifest_path, workspace=output_dir / "chapter_pipeline", repo_root=repo_root
    )
    receipt = owner.render_chapter(chapter_id, profile="lock", concurrency=2)
    (output_dir / (chapter_id + "_render_receipt.json")).write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def measure_native_chapter_captions(
    *,
    output_dir: Path,
    model_path: Path,
    voices_path: Path,
    caption_revision: str = "measured_phrases",
    phrase_geometry_by_segment: dict | None = None,
) -> dict:
    """Measure narration phrases against the already authored chapter windows.

    Words, voice speed and picture timing remain fixed. Overflow returns a HOLD.
    This uses the existing phrase and caption owners, without an ASR claim.
    """
    from video.unattended_core_factory_v1.caption_alignment import (
        measured_phrase_narration,
    )

    import re

    if not re.fullmatch(r"[A-Za-z0-9_-]+", caption_revision):
        raise ValueError("Safe chapter caption revision required")
    admission = json.loads(
        (output_dir / "chapter_source_admission.json").read_text(encoding="utf-8")
    )
    bindings = admission["identity"]["request_bindings"]
    for binding in bindings.values():
        if hash_file(binding["checked_path"]) != binding["request_sha256"]:
            raise ValueError("Native chapter caption input drift")
    locked = json.loads(
        Path(bindings["source_narrative_lock"]["checked_path"]).read_text(
            encoding="utf-8"
        )
    )
    measured = json.loads(
        Path(bindings["actual_narration"]["checked_path"]).read_text(encoding="utf-8")
    )
    chapters = locked["identity"]["normalized_chapters"]
    authored = [
        dict(segment_id=c["chapter_id"], text=c["narration"], pronunciation_notes=[])
        for c in chapters
    ]
    placements = measured["actual_narration"]["placements"]
    segments = []
    for text, placement in zip(authored, placements, strict=True):
        if (
            text["segment_id"] != placement["segment_id"]
            or hash_value(text["text"]) != placement["segment_text_sha256"]
            or hash_file(placement["audio"]["path"]) != placement["audio"]["sha256"]
        ):
            raise ValueError("Native chapter caption segment drift")
        segments.append(dict(placement, text=text["text"]))
    transcript = dict(
        segments=segments, plain_text=" ".join(c["text"] for c in authored)
    )
    transcript["source_narrative_transcript_hash"] = hash_value(transcript)
    timing = dict(
        voice=measured["actual_narration"]["voice"],
        speed=measured["actual_narration"]["speed"],
        lang=measured["actual_narration"]["lang"],
        source_narrative_transcript=transcript,
    )
    return measured_phrase_narration(
        timing_lock=timing,
        editor=dict(narration_segments=authored),
        model_path=model_path,
        voices_path=voices_path,
        output_dir=output_dir / caption_revision,
        media_duration_seconds=measured["picture_duration_seconds"],
        caption_width=43,
        max_phrase_words=14,
        phrase_geometry_by_segment=phrase_geometry_by_segment,
    )


def reflow_native_chapter_phrases(*, output_dir: Path) -> dict:
    """Place verified cached phrase waves in native-corrected chapter windows.

    Reuses measured speech without synthesis, speed changes or inferred alignment.
    """
    import textwrap
    import numpy as np
    import soundfile as sf
    from video.unattended_core_factory_v1.caption_alignment import phrase_groups
    from video.unattended_core_factory_v1.transcript import synthesis_text_for_segment
    from .package_factory import validate_caption_set, write_caption_artifacts

    admission = json.loads(
        (output_dir / "chapter_source_admission.json").read_text(encoding="utf-8")
    )
    native = admission["native_return"]
    if hash_file(native["path"]) != native["sha256"]:
        raise ValueError("Native corrected timing return drift")
    returned = json.loads(Path(native["path"]).read_text(encoding="utf-8"))
    if returned["kind"] != "LONGFORM_CHAPTER_TIMING_CORRECTION":
        raise ValueError("Explicit native chapter timing correction required")
    bindings = admission["identity"]["request_bindings"]
    for binding in bindings.values():
        if hash_file(binding["checked_path"]) != binding["request_sha256"]:
            raise ValueError("Native timing source input drift")
    source_lock = json.loads(
        Path(bindings["source_narrative_lock"]["checked_path"]).read_text(
            encoding="utf-8"
        )
    )
    original_audio = json.loads(
        Path(bindings["actual_narration"]["checked_path"]).read_text(encoding="utf-8")
    )["actual_narration"]
    cache_root = Path(bindings["measured_phrases"]["checked_path"]).parent
    cache_identity = json.loads(
        (cache_root / "source_identity.json").read_text(encoding="utf-8")
    )
    inventory_binding = bindings.get("complete_phrase_inventory")
    if not inventory_binding:
        raise ValueError("Exact complete phrase inventory request binding required")
    inventory = json.loads(
        Path(inventory_binding["checked_path"]).read_text(encoding="utf-8")
    )
    expected_inventory = {r["phrase_id"]: r for r in inventory["phrases"]}
    if len(expected_inventory) != len(inventory["phrases"]):
        raise ValueError("Duplicate phrase inventory identity")
    if cache_identity.get("phrase_geometry") != dict(width=43, max_words=14):
        raise ValueError("Unknown measured chapter phrase geometry")
    duration = returned["artifact"]["chapter_manifest"]["format_contract"][
        "duration_seconds"
    ]
    rate = original_audio["sample_rate_hz"]
    route = (original_audio["voice"], original_audio["speed"], original_audio["lang"])
    if route != ("af_heart", 1.06, "en-us") or rate != 24000:
        raise ValueError("Unapproved corrected chapter voice route")
    bus = np.zeros(round(duration * rate), dtype=np.float32)
    segments, records, holds, cues = [], [], [], []
    source_chapters = source_lock["identity"]["normalized_chapters"]
    timings = returned["artifact"]["chapter_timing_records"]
    manifest_chapters = returned["artifact"]["chapter_manifest"]["chapters"]
    frame_cursor = 0
    for chapter, placement, timing, manifest in zip(
        source_chapters,
        original_audio["placements"],
        timings,
        manifest_chapters,
        strict=True,
    ):
        cid, text = chapter["chapter_id"], chapter["narration"]
        if (
            cid != timing["chapter_id"]
            or cid != placement["segment_id"]
            or cid != manifest["id"]
            or hash_value(text) != timing["source_narration_text_sha256"]
            or hash_value(text) != placement["segment_text_sha256"]
            or placement["audio"]["sha256"] != timing["original_narration_audio_sha256"]
            or hash_file(placement["audio"]["path"]) != placement["audio"]["sha256"]
            or timing["global_start_frame"] != frame_cursor
            or timing["duration_frames"] != manifest["duration_frames"]
        ):
            raise ValueError("Corrected chapter source/timing identity mismatch")
        chapter_end = (frame_cursor + timing["duration_frames"]) / 30
        start = timing["narration_start_seconds"]
        if start < frame_cursor / 30:
            raise ValueError("Corrected narration starts before its chapter")
        cursor = start
        groups = phrase_groups(text, width=43, max_words=14)
        for index, group in enumerate(groups):
            spoken = synthesis_text_for_segment(
                dict(text=group, pronunciation_notes=[])
            )
            key = hash_value(
                dict(
                    text=spoken,
                    route=route,
                    engine="kokoro-v1.0",
                    model_sha256=cache_identity["model_sha256"],
                    voices_sha256=cache_identity["voices_sha256"],
                )
            )
            wave = cache_root / (key + ".wav")
            expected = expected_inventory.get(f"{cid}-{index + 1:02d}")
            if (
                not expected
                or expected["text"] != group
                or expected["synthesis_text"] != spoken
                or expected["cache_key"] != key
                or Path(expected["path"]).resolve() != wave.resolve()
                or hash_file(wave) != expected["sha256"]
            ):
                raise ValueError(
                    "Request-bound phrase inventory mismatch or audio drift"
                )
            seal = json.loads(
                wave.with_suffix(".identity.json").read_text(encoding="utf-8")
            )
            if seal != dict(identity=key, audio_sha256=hash_file(wave)):
                raise ValueError("Cached corrected phrase audio drift")
            audio, observed_rate = sf.read(wave, dtype="float32")
            if observed_rate != rate:
                raise ValueError("Cached phrase sample rate mismatch")
            seconds = len(audio) / rate
            if (
                expected["frames"] != len(audio)
                or expected["sample_rate_hz"] != rate
                or abs(expected["duration_seconds"] - seconds) > 0.000001
            ):
                raise ValueError("Request-bound phrase inventory measurement mismatch")
            end = cursor + seconds
            if end > chapter_end + 0.00001:
                holds.append(
                    dict(
                        chapter_id=cid,
                        phrase=index + 1,
                        speech_end_seconds=end,
                        chapter_end_seconds=chapter_end,
                    )
                )
            sample = round(cursor * rate)
            if sample < 0 or sample + len(audio) > len(bus):
                raise ValueError("Corrected phrase exceeds film duration")
            bus[sample : sample + len(audio)] += audio
            cue_id = f"{cid}-{index + 1:02d}"
            caption = textwrap.fill(
                group, width=43, break_long_words=False, break_on_hyphens=False
            )
            segments.append(
                dict(
                    cue_id=cue_id,
                    segment_id=cid,
                    text=group,
                    caption_text=caption,
                    timeline_start_seconds=cursor,
                    actual_audio_duration_seconds=seconds,
                    audio_path=str(wave.resolve()),
                    source_audio_sha256=seal["audio_sha256"],
                )
            )
            cues.append(
                dict(
                    cue_id=cue_id,
                    start_seconds=cursor,
                    end_seconds=end,
                    text=caption,
                    speaker="NARRATOR",
                    source_audio_sha256=seal["audio_sha256"],
                )
            )
            cursor = end + 0.045
        actual = cursor - 0.045 - start
        if abs(actual - timing["actual_phrase_duration_seconds"]) > 0.00001:
            raise ValueError("Corrected timing differs from measured phrase audio")
        records.append(
            dict(
                chapter_id=cid,
                measured_speech_seconds=actual,
                narration_start_seconds=start,
                chapter_end_seconds=chapter_end,
            )
        )
        frame_cursor += timing["duration_frames"]
    if (
        " ".join(s["text"] for s in segments).split()
        != " ".join(c["narration"] for c in source_chapters).split()
    ):
        raise ValueError("Corrected chapter phrases changed narrated words")
    if set(expected_inventory) != {s["cue_id"] for s in segments}:
        raise ValueError("Request-bound phrase inventory coverage mismatch")
    if holds:
        return dict(
            result="HOLD_CORRECTED_CHAPTER_PHRASE_OVERFLOW",
            holds=holds,
            public_write_authority=False,
        )
    captions = dict(
        schema="contentops.v2.timed_captions.v1",
        language="en",
        media_duration_seconds=duration,
        timing_basis="ACTUAL_CACHED_PHRASE_WAVES_IN_NATIVE_CORRECTED_CHAPTER_WINDOWS",
        cues=cues,
    )
    if (
        any(len(c["text"].splitlines()) > 2 for c in cues)
        or validate_caption_set(captions)["result"] != "PASS_CAPTIONS"
    ):
        raise ValueError("Corrected chapter captions invalid")
    root = output_dir / "reflowed_phrases"
    root.mkdir(parents=True, exist_ok=True)
    identity = dict(
        native_return_sha256=native["sha256"],
        complete_phrase_inventory_sha256=inventory_binding["request_sha256"],
        cache_identity_sha256=hash_file(cache_root / "source_identity.json"),
        phrase_waves=[
            dict(path=s["audio_path"], sha256=s["source_audio_sha256"])
            for s in segments
        ],
    )
    source_seal = root / "source_identity.json"
    if (
        source_seal.exists()
        and json.loads(source_seal.read_text(encoding="utf-8")) != identity
    ):
        raise ValueError("Changed corrected phrase source requires distinct revision")
    source_seal.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
    wave = root / "phrase_narration.wav"
    sf.write(wave, bus, rate, subtype="PCM_24")
    receipt = dict(
        result="MEASURED_PHRASE_NARRATION_READY",
        holds=[],
        audio=dict(path=str(wave.resolve()), sha256=hash_file(wave)),
        artifacts=write_caption_artifacts(captions, root / "captions"),
        segments=segments,
        phrase_records=records,
        identity=identity,
        actual_synthesis_count=0,
        voice_speed_changed=False,
        picture_render_count=0,
        hearing="NOT_VERIFIED",
        public_write_authority=False,
    )
    (root / "phrase_revision_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def package_native_chapters(
    *, output_dir: Path, repo_root: Path, caption_revision: str
) -> dict:
    """Assemble admitted chapter locks and measured audio through existing owners."""
    import html
    import re
    from .pipeline import FreeformChapterPipeline
    from .package_factory import (
        build_publication_package,
        validate_caption_set,
        validate_media_probe,
    )
    from video.unattended_core_factory_v1 import media
    from video.locale_activation_hardening_v1.factory import inspect_picture

    if not re.fullmatch(r"[A-Za-z0-9_-]+", caption_revision):
        raise ValueError("Safe caption revision required")
    admission = json.loads(
        (output_dir / "chapter_source_admission.json").read_text(encoding="utf-8")
    )
    identity = admission["identity"]
    project = Path(admission["project_root"])
    manifest = output_dir / "chapter_manifest.json"
    if (
        hash_file(manifest) != admission["manifest_sha256"]
        or hash_file(identity["execution_owner"]["path"])
        != identity["execution_owner"]["sha256"]
    ):
        raise ValueError("Longform package execution owner drift")
    for seal in [*identity["source_seals"], *identity["assets"]]:
        path = (project / seal["path"]).resolve()
        if not path.is_relative_to(project) or hash_file(path) != seal["sha256"]:
            raise ValueError("Longform package source/asset drift")
    for binding in identity["request_bindings"].values():
        if hash_file(binding["checked_path"]) != binding["request_sha256"]:
            raise ValueError("Longform package input drift")
    phrases = output_dir / caption_revision
    measured_path = phrases / "phrase_revision_receipt.json"
    measured = json.loads(measured_path.read_text(encoding="utf-8"))
    if measured["result"] != "MEASURED_PHRASE_NARRATION_READY" or measured["holds"]:
        return dict(
            result="HOLD_LONGFORM_MEASURED_CAPTIONS",
            holds=measured["holds"],
            public_write_authority=False,
        )
    for item in [measured["audio"], *measured["artifacts"].values()]:
        if hash_file(item["path"]) != item["sha256"]:
            raise ValueError("Longform measured caption/audio drift")
    owner = FreeformChapterPipeline(
        manifest, workspace=output_dir / "chapter_pipeline", repo_root=repo_root
    )
    owner.validate()
    chapter_files, chapter_records = [], []
    for chapter in owner.chapters:
        record = json.loads(
            (output_dir / (chapter["id"] + "_render_receipt.json")).read_text(
                encoding="utf-8"
            )
        )
        path = Path(record["output"])
        if hash_file(path) != record["sha256"] or record[
            "key"
        ] != owner.chapter_cache_key(chapter["id"], "lock", 2):
            raise ValueError("Longform chapter receipt or source cache drift")
        if inspect_picture(path)["frame_count"] != chapter["duration_frames"]:
            raise ValueError("Longform chapter actual frame count mismatch")
        chapter_files.append(path)
        chapter_records.append(dict(id=chapter["id"], sha256=record["sha256"]))
    package_root = output_dir / ("package_" + caption_revision)
    package_root.mkdir(parents=True, exist_ok=True)
    source_identity = dict(
        admission_sha256=hash_file(output_dir / "chapter_source_admission.json"),
        measured_phrases_sha256=hash_file(measured_path),
        chapters=chapter_records,
    )
    seal_path = package_root / "source_identity.json"
    if (
        seal_path.exists()
        and json.loads(seal_path.read_text(encoding="utf-8")) != source_identity
    ):
        raise ValueError("Changed longform package requires distinct revision")
    seal_path.write_text(json.dumps(source_identity, indent=2) + "\n", encoding="utf-8")

    def cached_step(name, output, invoke):
        seal = package_root / (name + "_receipt.json")
        if seal.exists():
            record = json.loads(seal.read_text(encoding="utf-8"))
            if hash_file(output) != record["sha256"]:
                raise ValueError("Longform cached media drift")
            return record
        if output.exists():
            raise ValueError("Unsealed longform output requires reconciliation")
        record = invoke()
        seal.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return record

    picture = package_root / "picture_lock.mp4"
    assembly = cached_step(
        "assembly", picture, lambda: owner.assemble(chapter_files, picture)
    )
    duration = owner.manifest["format_contract"]["duration_seconds"]
    plan = package_root / "audio_plan.json"
    plan.write_text(
        json.dumps(
            dict(
                duration_seconds=duration,
                stems=[
                    dict(
                        path=measured["audio"]["path"],
                        timeline_start_seconds=0,
                        gain_db=0,
                    )
                ],
            ),
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    audio = package_root / "final_mix.wav"
    mix = cached_step("mix", audio, lambda: owner.mix_audio(plan, audio))
    clean = package_root / "clean.mp4"
    mux = cached_step("mux", clean, lambda: owner.mux(picture, audio, clean))
    probe = media.probe_media(clean)
    technical = validate_media_probe("LONGFORM_16_9", probe)
    if (
        technical["errors"]
        or inspect_picture(clean)["frame_count"]
        != owner.manifest["format_contract"]["duration_frames"]
    ):
        raise ValueError("Longform final media contract failed")
    captions = json.loads(
        Path(measured["artifacts"]["json"]["path"]).read_text(encoding="utf-8")
    )
    if validate_caption_set(captions)["errors"]:
        raise ValueError("Longform captions invalid")
    source_lock = json.loads(
        Path(
            identity["request_bindings"]["source_narrative_lock"]["checked_path"]
        ).read_text(encoding="utf-8")
    )
    narrative = json.loads(
        Path(
            identity["request_bindings"]["source_narrative_return"]["checked_path"]
        ).read_text(encoding="utf-8")
    )["artifact"]
    chapters, frame_cursor = [], 0
    for c, n in zip(
        owner.chapters, source_lock["identity"]["normalized_chapters"], strict=True
    ):
        chapters.append(
            dict(chapter_id=c["id"], title=n["title"], start_seconds=frame_cursor / 30)
        )
        frame_cursor += c["duration_frames"]
    spec = dict(
        source_story_id="goal40-number-before-story",
        source_film_id=identity["native_task_id"],
        format="LONGFORM_16_9",
        language="en",
        canonical_picture=str(clean),
        audio=str(audio),
        caption_json=measured["artifacts"]["json"]["path"],
        caption_srt=measured["artifacts"]["srt"]["path"],
        caption_vtt=measured["artifacts"]["vtt"]["path"],
        metadata=dict(
            title=narrative["title"],
            description=narrative["subtitle"]
            + ". Dated educational analysis of retained 2026 releases; not current news or a market forecast.",
        ),
        chapters=chapters,
        rights_provenance_refs=[str(a) for a in narrative["asset_registry"]],
        factual_evidence_refs=[str(d) for d in narrative["source_documents"]],
        intended_future_surfaces=[],
        delivery_policy=dict(
            picture_render_scope="ONCE_PER_EDITORIAL_FORMAT",
            locale_picture_render_default=False,
            burned_captions="OPTIONAL_ONLY_EXACT_AUTHORITY_REQUIRED",
            recurring_locale_creative_xhigh=False,
        ),
        hard_boundaries=dict(
            video_public_write_authority=False,
            v1_mutation_authority=False,
            scheduler_mutation_authority=False,
            allow_4k=False,
        ),
        generation_version="goal40-native-chapter-private",
    )
    package = build_publication_package(spec)
    package_path = package_root / "manifest.json"
    package_path.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    cue_json = json.dumps(captions["cues"], ensure_ascii=True).replace("<", "\\u003c")
    chapter_html = "".join(
        f'<li><button data-time="{c["start_seconds"]}">{html.escape(c["title"])}</button></li>'
        for c in chapters
    )
    review = package_root / "review.html"
    review.write_text(
        f'''<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(narrative["title"])}</title>
<style>body{{background:#101b23;color:#eee;font:18px system-ui;margin:20px}}main{{max-width:1100px;margin:auto}}video{{width:min(100%,960px)}}.phone video{{max-width:360px}}#caption{{font-size:19px;max-width:62ch;min-height:3.2em;white-space:pre-line;background:#071018;padding:16px}}button,a{{color:#70d4cf}}button{{background:#162936;border:1px solid #46616b;padding:8px;margin:4px;text-align:left}}</style>
<main><h1>{html.escape(narrative["title"])}</h1><p>Dated educational film · {duration:.2f} seconds · seven chapters · private engineering review</p>
<button id="size">Phone / desktop display size</button><p><video controls preload="metadata" src="clean.mp4"></video></p><div id="caption" aria-live="off"></div>
<p>Captions below the picture use actual measured phrase audio timing. They preserve every narrated word. No listening, voice, final AV or rights-release acceptance is implied.</p><ol>{chapter_html}</ol>
<p><a href="manifest.json">Package, sources and image credits</a> · <a href="{Path(spec["caption_vtt"]).as_uri()}">Timed VTT</a> · <a href="clean.mp4">Clean film</a></p></main>
<script>const cues={cue_json};const v=document.querySelector('video');v.addEventListener('timeupdate',()=>{{const c=cues.find(c=>v.currentTime>=c.start_seconds&&v.currentTime<c.end_seconds);document.getElementById('caption').textContent=c?c.text:'';}});document.getElementById('size').onclick=()=>document.body.classList.toggle('phone');document.querySelectorAll('[data-time]').forEach(b=>b.onclick=()=>{{v.currentTime=Number(b.dataset.time);}});</script>''',
        encoding="utf-8",
    )
    receipt = dict(
        result="PRIVATE_NATIVE_LONGFORM_PACKAGE_BUILT",
        manifest=str(package_path.resolve()),
        review_entry=str(review.resolve()),
        package_id=package["package_id"],
        duration_seconds=duration,
        chapters=len(chapters),
        caption_cues=len(captions["cues"]),
        assembly=assembly,
        mix=mix,
        mux=mux,
        technical=technical,
        source_identity=source_identity,
        hearing="NOT_VERIFIED",
        continuous_picture_review="REQUIRED",
        rights_release="NOT_GRANTED",
        public_write_authority=False,
    )
    (package_root / "package_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def lock_native_narrative(
    *,
    request_path: Path,
    return_path: Path,
    repo_root: Path,
    model_path: Path,
    voices_path: Path,
    output_dir: Path,
) -> dict:
    repo_root = repo_root.resolve()
    request = json.loads(request_path.read_text(encoding="utf-8"))
    returned = json.loads(return_path.read_text(encoding="utf-8"))
    if (
        request.get("kind") != "LONGFORM_SOURCE_NARRATIVE"
        or returned.get("kind") != request["kind"]
        or returned.get("request_sha256") != hash_value(request)
    ):
        raise ValueError("Exact native longform request binding required")
    if (
        returned.get("requested_model"),
        returned.get("requested_reasoning_effort"),
        returned.get("provenance_limit"),
    ) != (
        "gpt-5.6-sol",
        "xhigh",
        "ASSIGNED_ROLE_NOT_INDEPENDENT_RUNTIME_ATTESTATION",
    ) or not returned.get("native_task_id"):
        raise ValueError("Assigned native role and truthful provenance limit required")

    def verify(path, digest):
        item = (repo_root / path).resolve()
        if (
            not item.is_relative_to(repo_root)
            or not item.is_file()
            or hash_file(item) != digest
        ):
            raise ValueError("Longform source bytes drift or escape")
        return {"path": str(item), "sha256": digest}

    bindings = [verify(v["path"], v["sha256"]) for v in request["bindings"].values()]
    artifact = returned["artifact"]
    sources = [
        verify(d["saved_extract_path"], d["saved_extract_sha256"])
        for d in artifact["source_documents"]
    ]
    sources.append(
        verify(
            artifact["source_manifest"]["path"], artifact["source_manifest"]["sha256"]
        )
    )
    assets = [verify(a["path"], a["sha256"]) for a in artifact["asset_registry"]]
    facts = {a["claim_id"] for a in artifact["governed_fact_anchors"]}
    analyses = {a["analysis_id"] for a in artifact["qualified_analysis"]}
    if not facts or not analyses or artifact.get("current_news_claim") is not False:
        raise ValueError("Dated source and qualified analysis required")
    chapters, corrections = [], []
    for chapter in artifact["chapters"]:
        if (
            not chapter.get("claim_bindings")
            or not set(chapter["claim_bindings"]) <= facts | analyses
        ):
            raise ValueError("Unknown chapter claim binding")
        text = chapter["narration"]
        # Mechanical UTF-8 repair is recorded; immutable native bytes stay intact.
        if "\u00e2\u20ac\u201d" in text:
            text = text.replace("\u00e2\u20ac\u201d", " - ")
            corrections.append(
                dict(
                    chapter_id=chapter["chapter_id"],
                    correction="MOJIBAKE_EM_DASH_TO_ASCII_SEPARATOR",
                )
            )
        if "\ufffd" in text:
            raise ValueError("Unresolved narration encoding corruption")
        chapters.append(dict(chapter, narration=text))
    if len({c["chapter_id"] for c in chapters}) != len(chapters) or not chapters:
        raise ValueError("Unique substantive chapters required")
    output_dir.mkdir(parents=True, exist_ok=True)
    identity = dict(
        request_sha256=hash_file(request_path),
        native_return_sha256=hash_file(return_path),
        sources=sources,
        request_bindings=bindings,
        assets=assets,
        normalized_chapters=chapters,
        corrections=corrections,
    )
    seal = output_dir / "source_narrative_lock.json"
    if (
        seal.exists()
        and json.loads(seal.read_text(encoding="utf-8"))["identity"] != identity
    ):
        raise ValueError("Changed longform input requires distinct revision")
    if not seal.exists():
        seal.write_text(
            json.dumps(
                dict(
                    schema="contentops.v2.native_longform_source_lock.v1",
                    identity=identity,
                    native_task_id=returned["native_task_id"],
                    provenance_limit=returned["provenance_limit"],
                    factual_review="REQUIRED_EXACT_CLAIM_SOURCE_REVIEW",
                    public_write_authority=False,
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    editor = {
        "audio_intent": {"narration_voice": "af_heart", "speed": 1.06, "lang": "en-us"},
        "narration_segments": [
            dict(
                segment_id=c["chapter_id"], text=c["narration"], pronunciation_notes=[]
            )
            for c in chapters
        ],
    }
    audio = synthesize_narration(
        editor=editor,
        model_path=model_path,
        voices_path=voices_path,
        output_dir=output_dir / "narration",
    )
    duration = float(audio["duration_seconds"])
    frames = math.ceil((duration + 0.2) * 30)
    result = dict(
        result="NATIVE_LONGFORM_NARRATION_MEASURED"
        if 300 <= frames / 30 <= 2700
        else "HOLD_LONGFORM_DURATION_OUTSIDE_CONTRACT",
        source_lock={"path": str(seal.resolve()), "sha256": hash_file(seal)},
        native_task_id=returned["native_task_id"],
        word_count=sum(len(c["narration"].split()) for c in chapters),
        actual_narration=audio,
        fps=30,
        width=1920,
        height=1080,
        duration_frames=frames,
        picture_duration_seconds=frames / 30,
        narration_hearing="NOT_VERIFIED",
        picture="AWAITING_FRESH_NATIVE_CHAPTER_CREATIVE",
        public_write_authority=False,
    )
    (output_dir / "measured_narrative.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    return result
