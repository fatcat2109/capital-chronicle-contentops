"""Caption layout revision on a sealed private package, without picture/audio work."""

from __future__ import annotations

import copy
import json
import textwrap
from pathlib import Path

from video.freeform_chapter_pipeline_v1.package_factory import (
    build_publication_package,
    validate_caption_set,
    write_caption_artifacts,
)

from .creative import hash_file, hash_value


def normalize_final_picture_correction(
    artifact: dict, motion: dict, prior_review: dict
) -> tuple[dict, dict]:
    """Map the saved native correction envelope without inventing a full review.

    Only CSS shorthand is expanded to equivalent numeric properties. Display text,
    geometry, native findings and all original bytes remain separately evidenced.
    """
    from hashlib import sha256
    from .creative import SOURCE_FILES, ACTUAL_MEDIA_REVIEW_CHECKS

    if (
        artifact.get("schema") != "contentops.v2.codex_final_picture_correction.v1"
        or artifact.get("decision") != "REPLACE_SOURCE_FILES"
    ):
        raise ValueError("Unsupported native final-picture correction schema")
    files = artifact["source_files"]
    if (
        set(files) != SOURCE_FILES
        or set(artifact["source_file_sha256"]) != SOURCE_FILES
    ):
        raise ValueError("Native final-picture source set incomplete")
    for path, source in files.items():
        if (
            sha256(source.encode("utf-8")).hexdigest()
            != artifact["source_file_sha256"][path]
        ):
            raise ValueError("Native final-picture source seal drift")
    preserved = artifact["preserved_contract"]
    if any(
        preserved.get(k) is not False
        for k in (
            "sequence_timing_changed",
            "narration_changed",
            "timing_lock_changed",
            "voice_changed",
            "story_values_changed",
            "story_text_changed",
            "source_claim_bindings_changed",
            "asset_ids_changed",
        )
    ):
        raise ValueError("Native final-picture correction exceeded picture-only scope")
    normalized, changes = dict(files), []
    for path, source in files.items():
        for shorthand, expansion in (
            (
                'padding: "46px 48px"',
                "paddingTop: 46, paddingBottom: 46, paddingLeft: 48, paddingRight: 48",
            ),
            (
                'padding: "28px 30px"',
                "paddingTop: 28, paddingBottom: 28, paddingLeft: 30, paddingRight: 30",
            ),
        ):
            if shorthand in source:
                changes.append(
                    dict(
                        path=path,
                        kind="CSS_PADDING_SHORTHAND_TO_EQUIVALENT_PROPERTIES",
                        before=shorthand,
                        after=expansion,
                    )
                )
                source = source.replace(shorthand, expansion)
        normalized[path] = source
    previous = prior_review["artifact"]["review_checks"]
    if set(previous) != ACTUAL_MEDIA_REVIEW_CHECKS:
        raise ValueError("Prior native review checks incomplete")
    checks = {
        k: "RETAINED_PRIOR_PROXY_REVIEW_ONLY: "
        + previous[k]
        + " Final credit-slate correction has separate native sampled findings; full final media review remains required."
        for k in previous
    }
    mapped = dict(
        schema="contentops.v2.codex_actual_media_review.v1",
        decision="MATERIAL_REVISION_REQUIRED",
        review_checks=checks,
        defects=artifact["findings"],
        replacement_files=normalized,
        source_claim_bindings=motion["source_claim_bindings"],
    )
    receipt = dict(
        source_schema=artifact["schema"],
        native_source_seals=artifact["source_file_sha256"],
        normalized_source_seals={
            k: sha256(v.encode("utf-8")).hexdigest() for k, v in normalized.items()
        },
        mechanical_changes=changes,
        native_inspection=artifact["inspected"],
        limits=artifact["limits"],
        final_review_promoted=False,
        display_text_changed=False,
        public_write_authority=False,
    )
    return mapped, receipt


def build_private_picture_revision(
    *,
    package_path: Path,
    request_path: Path,
    return_path: Path,
    input_packet: dict,
    editor: dict,
    motion: dict,
    timing_lock: dict,
    dependency_root: Path,
    scaffold_root: Path,
    asset_root: Path,
    output_dir: Path,
) -> dict:
    """Native picture-only correction using the existing renderer and package owner.

    The immutable source package, audio and timed captions are preserved. No
    narration or translation is synthesized and no platform transport is involved.
    """
    from . import media
    from .creative import materialize_source, validate_revision_artifact

    source = json.loads(package_path.read_text(encoding="utf-8"))
    for item in source["artifacts"].values():
        if item and hash_file(item["path"]) != item["sha256"]:
            raise ValueError("Picture revision source package drift")
    request = json.loads(request_path.read_text(encoding="utf-8"))
    returned = json.loads(return_path.read_text(encoding="utf-8"))
    if (
        returned.get("kind") != request.get("kind")
        or returned.get("request_sha256") != hash_value(request)
        or (
            returned.get("model"),
            returned.get("reasoning_effort"),
            returned.get("provenance_limit"),
        )
        != ("gpt-5.6-sol", "xhigh", "ASSIGNED_ROLE_NOT_INDEPENDENT_RUNTIME_ATTESTATION")
        or not returned.get("native_task_id")
    ):
        raise ValueError("Exact native final-picture return required")
    for binding in request["bindings"].values():
        if hash_file(binding["path"]) != binding["sha256"]:
            raise ValueError("Picture revision request input drift")
    # The review may bind the package before a caption-only successor; its
    # picture, audio and narrative still have to match this exact lineage.
    bound = json.loads(
        Path(request["bindings"]["current_package"]["path"]).read_text(encoding="utf-8")
    )
    for key in ("canonical_picture", "audio"):
        if bound["artifacts"][key] != source["artifacts"][key]:
            raise ValueError("Picture revision source lineage mismatch")
    review = returned["artifact"]
    normalization = None
    if review.get("schema") == "contentops.v2.codex_final_picture_correction.v1":
        prior = json.loads(
            Path(request["bindings"]["native_review"]["path"]).read_text(
                encoding="utf-8"
            )
        )
        review, normalization = normalize_final_picture_correction(
            review, motion, prior
        )
    validation = validate_revision_artifact(
        review, input_packet, editor, motion, timing_lock
    )
    if review["decision"] != "MATERIAL_REVISION_REQUIRED":
        raise ValueError("Picture revision requires material native correction")
    output_dir.mkdir(parents=True, exist_ok=True)
    if normalization is not None:
        (output_dir / "native_envelope_normalization.json").write_text(
            json.dumps(normalization, indent=2) + "\n", encoding="utf-8"
        )
    identity = dict(
        source_package_sha256=hash_file(package_path),
        request_sha256=hash_file(request_path),
        return_sha256=hash_file(return_path),
        native_task_id=returned["native_task_id"],
    )
    seal = output_dir / "source_identity.json"
    if seal.exists() and json.loads(seal.read_text(encoding="utf-8")) != identity:
        raise ValueError("Changed picture correction requires distinct revision")
    seal.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
    project = output_dir / "generated_project"
    media.prepare_project(
        project_root=project,
        scaffold_root=scaffold_root,
        dependency_root=dependency_root,
        asset_root=asset_root,
    )
    sources = materialize_source(review["replacement_files"], project)
    typecheck = media.typecheck_project(project, dependency_root)
    picture = output_dir / "picture_lock.mp4"
    picture_receipt = output_dir / "picture_render_receipt.json"
    if picture_receipt.exists():
        render = json.loads(picture_receipt.read_text(encoding="utf-8"))
        if hash_file(picture) != render["artifact"]["sha256"]:
            raise ValueError("Cached corrected picture drift")
    else:
        if picture.exists():
            raise ValueError("Unsealed corrected picture requires reconciliation")
        render = media.render_project(
            project_root=project,
            dependency_root=dependency_root,
            output=picture,
            crf=18,
            browser_executable=media.resolve_remotion_browser_executable(
                dependency_root
            ),
            public_root=asset_root,
        )
        picture_receipt.write_text(
            json.dumps(render, indent=2) + "\n", encoding="utf-8"
        )
    old_probe, new_probe = (
        media.probe_media(Path(p))
        for p in (source["artifacts"]["canonical_picture"]["path"], picture)
    )
    old_video, new_video = (
        next(s for s in p["streams"] if s["codec_type"] == "video")
        for p in (old_probe, new_probe)
    )
    if any(
        old_video[k] != new_video[k]
        for k in ("nb_frames", "width", "height", "r_frame_rate")
    ):
        raise ValueError("Picture correction changed timing or format")
    clean = output_dir / "clean.mp4"
    mux = media.mux_final_media(
        picture=picture, mix=Path(source["artifacts"]["audio"]["path"]), output=clean
    )
    technical = media.technical_media_report(clean, output_dir / "technical.json")
    spec = dict(source)
    spec.update(
        {
            key: (record["path"] if record else None)
            for key, record in source["artifacts"].items()
        }
    )
    spec.update(
        canonical_picture=str(clean),
        burned_caption_video=None,
        generation_version="goal40-private-native-picture-correction",
        factual_evidence_refs=[
            *source["factual_evidence_refs"],
            str(request_path.resolve()),
            str(return_path.resolve()),
        ],
    )
    package = build_publication_package(spec)
    for key in (
        "canonical_transcript_hash",
        "narration_timing_lock_hash",
        "voiceover_qa_hash",
        "seo_package_hash",
        "governed_input_hash",
    ):
        if key in source:
            package[key] = source[key]
    package["final_mux"] = media.artifact(clean)
    package["final_audio"] = source["artifacts"]["audio"]
    manifest = output_dir / "manifest.json"
    manifest.write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    receipt = dict(
        result="PRIVATE_NATIVE_PICTURE_PACKAGE_BUILT",
        identity=identity,
        manifest=str(manifest.resolve()),
        package_id=package["package_id"],
        validation=validation,
        typecheck=typecheck,
        sources=sources,
        picture=media.artifact(picture),
        picture_identity=mux["picture_identity"],
        technical=technical,
        audio_reused=source["artifacts"]["audio"],
        captions_reused={
            k: v for k, v in source["artifacts"].items() if k.startswith("caption_")
        },
        hearing="NOT_VERIFIED",
        viewer_review="REQUIRED",
        public_write_authority=False,
    )
    (output_dir / "revision_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def build_private_cohort_review(
    spec_path: Path, output_dir: Path, repo_root: Path
) -> dict:
    """One local entry for existing sealed packages; no job or acceptance mutation."""
    import html
    from . import media

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if (
        spec.get("public_write_authority") is not False
        or spec.get("schema") != "contentops.v2.private_cohort_review.v1"
    ):
        raise ValueError("Explicit zero-write private review specification required")
    entries, buttons = [], []
    if len(spec.get("entries", [])) != 4:
        raise ValueError("Four explicit cohort packages required")
    for entry in spec["entries"]:
        package_path = (repo_root / entry["package"]).resolve()
        review = (repo_root / entry["review"]).resolve()
        if (
            not all(
                p.is_relative_to(repo_root / ".task-runtime")
                for p in (package_path, review)
            )
            or not review.is_file()
        ):
            raise ValueError("Private cohort review path escape or missing entry")
        package = json.loads(package_path.read_text(encoding="utf-8"))
        for record in package["artifacts"].values():
            if record and hash_file(record["path"]) != record["sha256"]:
                raise ValueError("Cohort package artifact drift")
        item = dict(
            label=entry["label"],
            package=media.artifact(package_path),
            package_id=package["package_id"],
            language=package["language"],
            format=package["format"],
            review=media.artifact(review),
            clean=package["artifacts"]["canonical_picture"],
            caption_vtt=package["artifacts"]["caption_vtt"],
        )
        if entry.get("social"):
            social = (repo_root / entry["social"]).resolve()
            if not social.is_relative_to(repo_root / ".task-runtime"):
                raise ValueError("Private cohort social path escape")
            item["social"] = media.artifact(social)
        entries.append(item)
        index = len(entries) - 1
        buttons.append(
            f'<button data-entry="{index}">{html.escape(entry["label"])}</button>'
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    data = json.dumps(entries, ensure_ascii=True).replace("<", "\\u003c")
    page = output_dir / "review.html"
    page.write_text(
        f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Goal40 private media review</title>
<style>body{{font:18px system-ui;background:#101b23;color:#eee;margin:20px}}main{{max-width:1250px;margin:auto}}nav{{display:flex;gap:10px;flex-wrap:wrap}}button{{background:#1c3543;color:#9be6de;padding:12px;border:1px solid #4b707b;border-radius:6px;font:inherit}}a{{color:#9be6de}}iframe{{width:100%;height:1100px;border:1px solid #365361;background:#101b23}}.limits{{padding:16px;background:#2d2819;border-left:4px solid #d4b15f;line-height:1.5}}#links{{line-height:2}}</style>
<main><h1>Goal40 · Private media review</h1><p>Two English story shorts, one Spanish version and one seven-chapter analytical film. Retained 2026 source releases are dated explicitly.</p>
<p class="limits">Local engineering candidate. Production remains paused and no platform upload is authorized. Actual listening, voice, final audiovisual acceptance and rights release remain unverified or ungranted. Continuous visual acceptance is reported separately in the review findings.</p>
<nav>{"".join(buttons)}</nav><h2 id="selected"></h2><p id="links"></p><iframe title="Selected private media review"></iframe>
<p><a href="cohort_receipt.json">Exact package and artifact identities</a></p></main>
<script>const entries={data};const uri=p=>'file:///'+p.replace(/\\\\/g,'/');function select(i){{const e=entries[i];document.getElementById('selected').textContent=e.label;document.querySelector('iframe').src=uri(e.review.path);const links=[['Open player',e.review.path],['Clean video',e.clean.path],['Captions',e.caption_vtt.path],['Package and sources',e.package.path]];if(e.social)links.push(['Captioned social video',e.social.path]);document.getElementById('links').replaceChildren(...links.flatMap(([label,path],i)=>{{const a=document.createElement('a');a.textContent=label;a.href=uri(path);a.target='_blank';return i?[document.createTextNode(' · '),a]:[a];}}));}}document.querySelectorAll('[data-entry]').forEach(b=>b.onclick=()=>select(Number(b.dataset.entry)));select(0);</script>""",
        encoding="utf-8",
    )
    receipt = dict(
        result="PRIVATE_COHORT_REVIEW_ENTRY_BUILT",
        source_spec=media.artifact(spec_path),
        entries=entries,
        review_entry=media.artifact(page),
        acceptance="ENGINEERING_REVIEW_ONLY",
        public_write_authority=False,
    )
    (output_dir / "cohort_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def build_private_caption_review(package_path: Path, output_dir: Path) -> dict:
    """Local social caption preview from a sealed package; no platform transport."""
    import html
    from . import media

    package = json.loads(package_path.read_text(encoding="utf-8"))
    for record in package["artifacts"].values():
        if record and hash_file(record["path"]) != record["sha256"]:
            raise ValueError("Private caption preview package drift")
    output_dir.mkdir(parents=True, exist_ok=True)
    clean = Path(package["artifacts"]["canonical_picture"]["path"])
    cue_path = Path(package["artifacts"]["caption_json"]["path"])
    cues = json.loads(cue_path.read_text(encoding="utf-8"))["cues"]
    if package["format"] != "SHORT_9_16" or any(
        len(c["text"].splitlines()) > 2 for c in cues
    ):
        raise ValueError("Two-line short caption set required")

    def timestamp(seconds):
        cs = round(float(seconds) * 100)
        return f"{cs // 360000}:{cs // 6000 % 60:02}:{cs // 100 % 60:02}.{cs % 100:02}"

    ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,46,&H00FFFFFF,&H00FFFFFF,&H00201812,&HA0201812,-1,0,0,0,100,100,0,0,3,7,0,8,70,70,190,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    for cue in cues:
        text = (
            cue["text"]
            .replace("\\", "\\\\")
            .replace("{", "\\{")
            .replace("}", "\\}")
            .replace("\n", r"\N")
        )
        ass += f"Dialogue: 0,{timestamp(cue['start_seconds'])},{timestamp(cue['end_seconds'])},Default,,0,0,0,,{text}\n"
    ass_path = output_dir / "captions.ass"
    ass_path.write_text(ass, encoding="utf-8")
    identity = dict(
        package_sha256=hash_file(package_path),
        clean_sha256=hash_file(clean),
        ass_sha256=hash_file(ass_path),
        encoding="libx264_crf18_yuv420p",
        authority="GOAL40_EXPLICIT_PRIVATE_CAPTION_SOCIAL_OUTPUT",
    )
    receipt_path = output_dir / "review_receipt.json"
    social = output_dir / "social-captioned.mp4"
    reused = False
    if receipt_path.exists():
        prior = json.loads(receipt_path.read_text(encoding="utf-8"))
        if (
            prior["identity"] != identity
            or hash_file(social) != prior["captioned_video"]["sha256"]
        ):
            raise ValueError("Private caption preview drift")
        reused = True
    if social.exists() and not reused:
        raise ValueError("Unsealed social preview needs explicit reconciliation")
    if not reused:
        media.run_command(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(clean),
                "-vf",
                "ass=captions.ass",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "copy",
                "-movflags",
                "+faststart",
                str(social.resolve()),
            ],
            cwd=output_dir.resolve(),
        )
    before, after = media.probe_media(clean), media.probe_media(social)
    a, b = (
        next(s for s in p["streams"] if s["codec_type"] == "video")
        for p in (before, after)
    )
    if a["nb_frames"] != b["nb_frames"]:
        raise ValueError("Captioned preview changed picture duration")
    title = html.escape(package["metadata"]["title"])
    language = html.escape(package["language"])
    caption_note = (
        "Captions preserve the original spoken words in two lines."
        if package["language"] == "en"
        else "Localized captions summarize the measured phrases in two lines. The picture retains its original English graphics; voice acceptance requires listening review."
    )
    inline_cues = json.dumps(cues, ensure_ascii=True).replace("<", "\\u003c")
    view = output_dir / "review.html"
    view.write_text(
        f'''<!doctype html><meta charset="utf-8"><title>{title} | private review</title>
<style>body{{font:17px system-ui;background:#111b23;color:#eee;margin:24px}}main{{max-width:1100px;margin:auto}}video{{width:min(100%,360px);background:#000}}video.desktop{{width:540px}}button,a{{color:#75dbca}}article{{max-width:70ch}}.row{{display:flex;flex-wrap:wrap;gap:24px}}::cue{{font:600 15px system-ui;background:#18232ddd}}</style>
<main><h1>{title}</h1><p>Private engineering review of the dated source-bound story. Hearing, voice, final AV and rights release remain unverified.</p>
<p><button onclick="document.querySelectorAll('video').forEach(v=>v.classList.toggle('desktop'))">Phone / desktop display size</button></p>
<div class="row"><section><h2>Clean + timed sidecar</h2><video controls preload="metadata" src="{clean.as_uri()}"></video></section>
<section><h2>Private captioned social preview</h2><video controls preload="metadata" src="social-captioned.mp4"></video></section></div>
<article><h2>What changed</h2><p>The narration uses measured phrases at the existing registered voice speed. Picture windows and all {int(a["nb_frames"]):,} encoded frames are preserved in the clean output. {caption_note} The social preview burns these cues into a separate file.</p>
<p>Continuous picture review, mobile readability and actual listening remain separate acceptance checks. The social file is a local preview, with no platform upload or publication.</p>
<p><a href="{package_path.resolve().as_uri()}">Current package and provenance</a> · <a href="{cue_path.as_uri()}">Measured caption cues</a> · <a href="review_receipt.json">Preview evidence</a></p></article></main>
<script>const measuredCues={inline_cues};const player=document.querySelector('video');const track=player.addTextTrack('captions','Measured phrases ({language})','{language}');for(const c of measuredCues){{const cue=new VTTCue(c.start_seconds,c.end_seconds,c.text);cue.line=10;cue.snapToLines=false;cue.position=50;cue.size=86;cue.align='center';track.addCue(cue)}}track.mode='showing';</script>''',
        encoding="utf-8",
    )
    receipt = dict(
        result="PRIVATE_CAPTION_REVIEW_BUILT",
        identity=identity,
        package_id=package["package_id"],
        clean_video=media.artifact(clean),
        captioned_video=media.artifact(social),
        review_html=media.artifact(view),
        caption_burn_count=0 if reused else 1,
        reused_captioned_video=reused,
        remotion_render_count=0,
        frame_count=int(a["nb_frames"]),
        viewer_review="REQUIRED",
        hearing="NOT_VERIFIED",
        public_write_authority=False,
    )
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def build_phrase_audio_revision(
    *,
    package_path: Path,
    picture: Path,
    timing_lock: dict,
    editor: dict,
    model_path: Path,
    voices_path: Path,
    bed_path: Path,
    output_dir: Path,
    caption_width: int = 29,
    max_phrase_words: int = 10,
    phrase_geometry_by_segment: dict | None = None,
):
    """Use existing audio/transcript/package owners; preserve the sealed picture.

    Each cue is bound to an individually measured phrase, not an estimated word
    boundary. A fresh transcript/SEO identity follows the changed audio. Listening
    and final viewer quality remain separate review requirements.
    """
    from . import media
    from .caption_alignment import measured_phrase_narration
    from .transcript import (
        build_canonical_spoken_transcript,
        build_voiceover_qa,
        build_transcript_derived_seo,
        synthesis_text_for_segment,
    )

    original = json.loads(package_path.read_text(encoding="utf-8"))
    for item in original["artifacts"].values():
        if item and hash_file(item["path"]) != item["sha256"]:
            raise ValueError("Original package artifact drift")
    duration = float(media.probe_media(picture)["format"]["duration"])
    revised = measured_phrase_narration(
        timing_lock=timing_lock,
        editor=editor,
        model_path=model_path,
        voices_path=voices_path,
        output_dir=output_dir / "phrases",
        media_duration_seconds=duration,
        caption_width=caption_width,
        max_phrase_words=max_phrase_words,
        phrase_geometry_by_segment=phrase_geometry_by_segment,
    )
    if revised["holds"]:
        return revised
    placements = []
    for authored, source, record in zip(
        editor["narration_segments"],
        timing_lock["canonical_spoken_transcript"]["segments"],
        revised["phrase_records"],
        strict=True,
    ):
        if (
            source["segment_id"] != record["segment_id"]
            or source["segment_id"] != authored["segment_id"]
        ):
            raise ValueError("Measured segment identity mismatch")
        item = copy.deepcopy(source)
        item.update(
            audio_path=record["audio"]["path"],
            audio=record["audio"],
            actual_audio_duration_seconds=record["phrase_audio_seconds"],
            timeline_end_seconds=float(source["timeline_start_seconds"])
            + record["phrase_audio_seconds"],
            synthesis_action="SYNTHESIZED",
        )
        item["segment_text_sha256"] = hash_value(authored["text"])
        item["synthesis_text_sha256"] = hash_value(synthesis_text_for_segment(authored))
        placements.append(item)
    prior = timing_lock["canonical_spoken_transcript"]
    transcript = build_canonical_spoken_transcript(
        video_job_id=prior["video_job_id"],
        run_id=prior["run_id"],
        governed_input_hash=prior["governed_input_hash"],
        editor=editor,
        placements=placements,
        locked_narration_audio=revised["audio"],
    )
    qa = build_voiceover_qa(transcript=transcript, editor=editor)
    updated = copy.deepcopy(timing_lock)
    updated.pop("timing_lock_hash", None)
    updated.update(
        placements=placements,
        canonical_spoken_transcript=transcript,
        voiceover_qa=qa,
        locked_narration_audio=revised["audio"],
        actual_total_narration_duration_seconds=max(
            p["timeline_end_seconds"] for p in placements
        ),
        supersedes_timing_lock_hash=timing_lock["timing_lock_hash"],
        picture_windows_unchanged=True,
    )
    updated["timing_lock_hash"] = hash_value(updated)
    seo = build_transcript_derived_seo(transcript=transcript, editor=editor)
    for filename, value in (("timing_lock.json", updated), ("seo.json", seo)):
        (output_dir / filename).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )
    # Place mobile sidecar above the existing data cards; retain exact cue times.
    vtt_path = Path(revised["artifacts"]["vtt"]["path"])
    import re

    vtt_path.write_text(
        re.sub(
            r"(\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3})",
            r"\1 line:14% position:50% size:86% align:center",
            vtt_path.read_text(encoding="utf-8"),
        ),
        encoding="utf-8",
    )
    revised["artifacts"]["vtt"] = media.artifact(vtt_path)
    mix = media.build_audio_mix(
        picture=picture,
        timing_lock=updated,
        bed_path=bed_path,
        output_dir=output_dir / "audio",
    )
    mux = media.mux_final_media(
        picture=picture, mix=Path(mix["mix"]["path"]), output=output_dir / "clean.mp4"
    )
    technical = media.technical_media_report(
        output_dir / "clean.mp4", output_dir / "technical.json"
    )
    package = media.build_neutral_package(
        story_id=original["source_story_id"],
        run_id=prior["run_id"],
        final_media=output_dir / "clean.mp4",
        audio=Path(mix["mix"]["path"]),
        captions={"artifacts": revised["artifacts"]},
        rights_refs=original["rights_provenance_refs"],
        evidence_refs=original["factual_evidence_refs"],
        input_hash=prior["governed_input_hash"],
        timing_lock=updated,
        seo_package=seo,
        output=output_dir / "manifest.json",
    )
    receipt = dict(
        result="PRIVATE_MEASURED_PHRASE_AUDIO_PACKAGE_BUILT",
        parent_package_id=original["package_id"],
        source_package_sha256=hash_file(package_path),
        package_id=package["package_id"],
        manifest=str((output_dir / "manifest.json").resolve()),
        picture_render_count=0,
        voice_speed_changed=False,
        phrase_receipt=str(
            (output_dir / "phrases/phrase_revision_receipt.json").resolve()
        ),
        current_transcript_hash=transcript["canonical_transcript_hash"],
        picture_identity=mux["picture_identity"],
        mix=mix,
        technical=technical,
        hearing="NOT_VERIFIED",
        viewer_review="REQUIRED",
        public_write_authority=False,
    )
    (output_dir / "revision_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return receipt


def revise_caption_layout(
    package_path: Path,
    output_dir: Path,
    *,
    width: int = 32,
    line_percent: int | None = None,
):
    """Bind a successor package through the canonical package owner.

    Only whitespace layout changes. Transcript, timings, audio and picture remain
    exact. A distinct directory makes changed caption identities reviewable and
    prevents mutation of the accepted package or an older revision.
    """
    if not 24 <= width <= 48:
        raise ValueError("Caption width must be24..48")
    if line_percent is not None and not 5 <= line_percent <= 90:
        raise ValueError("Caption line position must be5..90 percent")
    original = json.loads(package_path.read_text(encoding="utf-8"))
    for item in original["artifacts"].values():
        if item is not None and hash_file(item["path"]) != item["sha256"]:
            raise ValueError("Original package artifact drift")
    if output_dir.exists():
        raise ValueError("Use a distinct caption revision directory")
    captions = json.loads(
        Path(original["artifacts"]["caption_json"]["path"]).read_text(encoding="utf-8")
    )
    changed = copy.deepcopy(captions)
    for cue in changed["cues"]:
        cue["text"] = textwrap.fill(
            " ".join(cue["text"].split()),
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )
    if changed == captions and line_percent is None:
        raise ValueError("Caption revision contains no layout change")
    if not all(
        a["text"].split() == b["text"].split()
        for a, b in zip(captions["cues"], changed["cues"])
    ):
        raise ValueError("Caption revision changed spoken words")
    if validate_caption_set(changed)["result"] != "PASS_CAPTIONS":
        raise ValueError("Invalid revised captions")
    artifacts = write_caption_artifacts(changed, output_dir / "captions")
    if line_percent is not None:
        import re

        vtt = Path(artifacts["vtt"]["path"])
        vtt.write_text(
            re.sub(
                r"(\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3})",
                rf"\1 line:{line_percent}% position:50% size:86% align:center",
                vtt.read_text(encoding="utf-8"),
            ),
            encoding="utf-8",
        )
        from .media import artifact

        artifacts["vtt"] = artifact(vtt)
    spec = {
        k: v
        for k, v in original.items()
        if k
        not in {
            "artifacts",
            "package_id",
            "generation_timestamp_utc",
            "transport",
            "publication_state",
        }
    }
    for key in ("canonical_picture", "burned_caption_video", "audio"):
        item = original["artifacts"][key]
        spec[key] = item["path"] if item else None
    for key in ("json", "srt", "vtt"):
        spec["caption_" + key] = artifacts[key]["path"]
    spec["generation_version"] = (
        "caption-layout-"
        + str(width)
        + ("-line-" + str(line_percent) if line_percent is not None else "")
    )
    successor = build_publication_package(spec)
    for key in (
        "canonical_transcript_identity",
        "canonical_transcript_hash",
        "narration_timing_lock_hash",
        "voiceover_qa_hash",
        "seo_derivation",
        "seo_package_hash",
        "governed_input_hash",
        "final_mux",
        "final_audio",
    ):
        if key in original:
            successor[key] = original[key]
    manifest = output_dir / "platform_neutral_package_manifest.json"
    manifest.write_text(json.dumps(successor, indent=2) + "\n", encoding="utf-8")
    receipt = {
        "result": "PRIVATE_CAPTION_LAYOUT_REVISION_BUILT",
        "parent_package_id": original["package_id"],
        "package_id": successor["package_id"],
        "source_package_sha256": hash_file(package_path),
        "picture_sha256": successor["artifacts"]["canonical_picture"]["sha256"],
        "audio_sha256": successor["artifacts"]["audio"]["sha256"],
        "caption_sha256_before": original["artifacts"]["caption_json"]["sha256"],
        "caption_sha256_after": successor["artifacts"]["caption_json"]["sha256"],
        "picture_render_count": 0,
        "audio_synthesis_count": 0,
        "timings_and_words_unchanged": True,
        "quality_review": "REQUIRED",
        "public_write_authority": False,
        "manifest": str(manifest),
        "line_percent": line_percent,
    }
    (output_dir / "reuse_receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return receipt
