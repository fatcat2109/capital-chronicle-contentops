"""Compatible current-source private mode of the existing speech relay.

Acquisition and native turns are explicit inputs. This helper cannot call a provider,
fetch media, grant rights, upload, or certify that anyone heard the original audio.
"""

from __future__ import annotations
import argparse
import copy
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
import os
import math
from urllib.parse import urlsplit
from live_contentops import speech_highlight_relay_v1 as relay

FORMATS = {
    "MOMENT_CONTEXT",
    "WHAT_CHANGED",
    "CLAIM_CHECK",
    "QUESTION_ANSWER",
    "CONSEQUENCE_WATCHPOINT",
}
SCHEMA = "contentops.speech_highlight_relay.current_source_private.v1"


def digest(value):
    return hashlib.sha256(relay.canonical_json(value)).hexdigest()


def https_source(value):
    parsed = urlsplit(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.password
    )


def candidates(owner_source, stream):
    """Bound actual existing-stream rows; an explicit source receives no rights promotion."""
    rows = [dict(owner_source, input_origin="EXPLICIT_SOURCE")] if owner_source else []
    rows += [dict(row, input_origin="EXISTING_STREAM") for row in stream]
    result, seen = [], set()
    for row in rows:
        url = row.get("canonical_source_url", "")
        if not https_source(url) or not row.get("source_id"):
            raise relay.SpeechRelayError("Exact HTTPS source identity required")
        if url in seen:
            continue
        seen.add(url)
        result.append(row)
        if len(result) == 3:
            break
    return result


def atomic_json(path, value):
    temporary = path.with_name(path.name + ".partial")
    relay.write_json(temporary, value)
    os.replace(temporary, path)


def retain_return(output, name, value):
    """Freeze only a validated native return, so a rejected input cannot poison resume."""
    path = output / (name + "_return.json")
    if path.exists() and json.loads(path.read_text(encoding="utf-8")) != value:
        raise relay.SpeechRelayError("Completed native return changed")
    if not path.exists():
        atomic_json(path, value)


def stage_artifact(output, name, edit_hash, build, validate):
    """Only a sealed stage may be reused; abandoned temporary files are replaceable."""
    target = output / name
    seal = output / (name + ".stage.json")
    if seal.exists():
        record = json.loads(seal.read_text(encoding="utf-8"))
        if record != dict(edit_sha256=edit_hash, sha256=relay.sha256_file(target)):
            raise relay.SpeechRelayError("Sealed stage drift")
        validate(target)
        return
    if target.exists():
        raise relay.SpeechRelayError("Unsealed output requires reconciliation")
    temporary = output / (Path(name).stem + ".partial" + Path(name).suffix)
    if temporary.exists():
        temporary.unlink()  # exact task-owned incomplete stage only
    build(temporary)
    validate(temporary)
    os.replace(temporary, target)
    atomic_json(seal, dict(edit_sha256=edit_hash, sha256=relay.sha256_file(target)))


def validate_source(packet, root):
    if packet.get("schema") != SCHEMA or packet.get("production_eligible") is not False:
        raise relay.SpeechRelayError("Explicit current-source private mode required")
    for key in (
        "source_id",
        "publisher",
        "canonical_source_url",
        "event_date",
        "acquisition",
    ):
        if not packet.get(key):
            raise relay.SpeechRelayError("Missing source binding: " + key)
    if not https_source(packet["canonical_source_url"]):
        raise relay.SpeechRelayError("HTTPS original source required")
    source = relay._local_artifact(root, packet["media"])
    transcript = relay._local_artifact(root, packet["transcript"])
    utterances = json.loads(transcript.read_text(encoding="utf-8"))
    if not utterances or not isinstance(utterances, list):
        raise relay.SpeechRelayError("Timed original-audio utterances required")
    last = -1.0
    for u in utterances:
        a, b = u["start_seconds"], u["end_seconds"]
        if (
            not all(
                isinstance(n, (int, float))
                and not isinstance(n, bool)
                and math.isfinite(n)
                for n in (a, b, packet["media"]["duration_seconds"])
            )
            or not (0 <= a < b <= packet["media"]["duration_seconds"])
            or a < last
            or not u["text"].strip()
        ):
            raise relay.SpeechRelayError("Invalid original-audio timing")
        last = b
    rights = packet.get("rights", {})
    holds = []
    if rights.get("private_processing_basis") != "PERMITTED" or not isinstance(
        rights.get("evidence"), dict
    ):
        holds.append("PRIVATE_PROCESSING_RIGHTS_NOT_ESTABLISHED")
    else:
        relay._local_artifact(root, rights["evidence"])
        if rights.get("media_sha256") != packet["media"]["sha256"] or not rights.get(
            "limitations"
        ):
            raise relay.SpeechRelayError(
                "Source-specific rights scope and limitations required"
            )
    if packet.get("audio_review", {}).get("status") != "HEARD_REVIEWED":
        holds.append("ORIGINAL_AUDIO_LISTENING_NOT_VERIFIED")
    if packet.get("timing_review", {}).get("status") != "VERIFIED":
        holds.append("SOURCE_AUDIO_ALIGNMENT_NOT_VERIFIED")
    # External review claims need an explicit immutable record, never a boolean alone.
    for key in ("audio_review", "timing_review"):
        review = packet.get(key, {})
        if review.get("status") in {"HEARD_REVIEWED", "VERIFIED"}:
            if (
                not review.get("reviewer")
                or not review.get("method")
                or not review.get("evidence")
            ):
                raise relay.SpeechRelayError(
                    "Bound independent review evidence required"
                )
            evidence = relay._local_artifact(root, review["evidence"])
            bound = json.loads(evidence.read_text(encoding="utf-8"))
            if (
                bound.get("media_sha256") != packet["media"]["sha256"]
                or bound.get("transcript_sha256") != packet["transcript"]["sha256"]
                or bound.get("status") != review["status"]
            ):
                raise relay.SpeechRelayError(
                    "Independent review is not bound to this recording/transcript"
                )
    return source, utterances, holds


def prepare(packet, root, output, selection=None, meaning=None):
    """Resume one content-addressed job; completed media are verified and reused."""
    root, output = Path(root).resolve(), Path(output).resolve()
    if not output.is_relative_to(root / ".task-runtime" / "speech_highlight_relay_v1"):
        raise relay.SpeechRelayError("Existing isolated relay output root required")
    source, utterances, holds = validate_source(packet, root)
    output.mkdir(parents=True, exist_ok=True)
    binding = digest(packet)
    frozen = output / "current_source.json"
    if frozen.exists() and json.loads(frozen.read_text(encoding="utf-8")) != packet:
        raise relay.SpeechRelayError("Source changed; use a distinct job identity")
    if not frozen.exists():
        atomic_json(frozen, packet)
    selection_request = dict(
        schema="contentops.signal_clips.native_request.v1",
        role="SELECTION",
        model="gpt-6.1-sol",
        reasoning_effort="low",
        source_sha256=binding,
        utterances=utterances,
        formats=sorted(FORMATS),
        source=packet,
    )
    atomic_json(output / "selection_request.json", selection_request)
    if selection is None and (output / "selection_return.json").is_file():
        selection = json.loads(
            (output / "selection_return.json").read_text(encoding="utf-8")
        )
    if meaning is None and (output / "meaning_return.json").is_file():
        meaning = json.loads(
            (output / "meaning_return.json").read_text(encoding="utf-8")
        )
    if meaning is not None and selection is None:
        raise relay.SpeechRelayError("Meaning requires its exact selection")
    if not selection:
        return dict(
            stage="AWAITING_NATIVE_SELECTION", holds=holds, source_sha256=binding
        )
    for name, value, role, effort in [
        ("selection", selection, "SELECTION", "low"),
        ("meaning", meaning, "MEANING", "max"),
    ]:
        if value is None:
            continue
        if (
            value.get("source_sha256") != binding
            or value.get("role") != role
            or value.get("model") != "gpt-6.1-sol"
            or value.get("reasoning_effort") != effort
            or not value.get("native_turn_id")
        ):
            raise relay.SpeechRelayError("Exact native role/source provenance required")
    span = selection["span"]
    a, b = span["start_seconds"], span["end_seconds"]
    if not all(
        isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n)
        for n in (a, b)
    ):
        raise relay.SpeechRelayError("Finite numeric source span required")
    if not 5 <= b - a <= 120 or selection.get("format") not in FORMATS:
        raise relay.SpeechRelayError("Bounded supported format/span required")
    selected = [
        u for u in utterances if a <= u["start_seconds"] and u["end_seconds"] <= b
    ]
    if (
        not selected
        or selected[0]["start_seconds"] != a
        or selected[-1]["end_seconds"] != b
    ):
        raise relay.SpeechRelayError("Span must preserve exact utterance boundaries")
    if selection.get("exact_quote") != " ".join(u["text"] for u in selected):
        raise relay.SpeechRelayError("Original utterance wording changed")
    if not selection.get("rationale") or not selection.get("surrounding_context"):
        raise relay.SpeechRelayError(
            "Justified selection and surrounding context required"
        )
    if selection["format"] in {"WHAT_CHANGED", "QUESTION_ANSWER", "CLAIM_CHECK"}:
        if not selection.get("supporting_bindings"):
            raise relay.SpeechRelayError(
                "Comparison, question or check evidence binding required"
            )
    for spec in selection.get("supporting_bindings", []):
        for key in (
            "source_id",
            "canonical_source_url",
            "event_date",
            "relationship",
            "proposition",
        ):
            if not isinstance(spec.get(key), str) or not spec[key].strip():
                raise relay.SpeechRelayError(
                    "Explicit supporting source and meaning relationship required"
                )
        if not https_source(spec["canonical_source_url"]):
            raise relay.SpeechRelayError("HTTPS supporting source required")
        relay._local_artifact(root, spec)
    retain_return(output, "selection", selection)
    atomic_json(
        output / "meaning_request.json",
        dict(
            selection_request,
            role="MEANING",
            reasoning_effort="max",
            selection=selection,
            selection_sha256=digest(selection),
        ),
    )
    if not meaning:
        return dict(stage="AWAITING_NATIVE_MEANING", holds=holds, source_sha256=binding)
    if meaning.get("selection_sha256") != digest(selection):
        raise relay.SpeechRelayError("Meaning is not bound to this exact selection")
    if meaning.get("decision") != "KEEP":
        if meaning.get("decision") != "HOLD" or not meaning.get("reason"):
            raise relay.SpeechRelayError(
                "Explicit meaning decision and hold reason required"
            )
        retain_return(output, "meaning", meaning)
        return dict(
            stage="EDITORIAL_HOLD",
            holds=holds + [meaning.get("reason", "Meaning review held")],
        )
    for key in (
        "headline",
        "context",
        "speaker_claim",
        "independent_evidence",
        "cc_interpretation",
    ):
        if not isinstance(meaning.get(key), str) or not meaning[key].strip():
            raise relay.SpeechRelayError("Separate meaning layers required")
    retain_return(output, "meaning", meaning)
    if "PRIVATE_PROCESSING_RIGHTS_NOT_ESTABLISHED" in holds:
        return dict(stage="RIGHTS_HOLD", holds=holds)
    media_binding = digest([binding, selection, meaning])
    manifest = output / "current_package.json"
    if manifest.exists():
        old = json.loads(manifest.read_text(encoding="utf-8"))
        if old["edit_sha256"] != media_binding:
            raise relay.SpeechRelayError("Edit changed; preserve previous job")
        for name, sha in old["file_hashes"].items():
            if relay.sha256_file(output / name) != sha:
                raise relay.SpeechRelayError("Completed artifact drift")
        return old
    clip = output / "extracted_clip.mp4"
    stage_artifact(
        output,
        clip.name,
        media_binding,
        lambda target: relay.DynamicMediaClipper.extract_clip(source, a, b - a, target),
        lambda target: relay._check_media(relay.probe_media(target), b - a),
    )
    cues = [
        relay.CaptionCue(
            str(i),
            u["start_seconds"] - a,
            u["end_seconds"] - a,
            u["text"],
            packet["speaker"]["name"],
        )
        for i, u in enumerate(selected)
    ]
    render_packet = dict(
        packet, selection=dict(headline=meaning["headline"], context=meaning["context"])
    )
    for key, captions in [("clean_master", None), ("captioned_derivative", cues)]:
        target = output / relay.ARTIFACT_FILES[key]
        stage_artifact(
            output,
            target.name,
            media_binding,
            lambda path: relay._render_vertical(
                clip, path, render_packet, b - a, captions
            ),
            lambda path: relay._check_media(
                relay.probe_media(path), b - a, vertical=True
            ),
        )
    (output / "captions.srt").write_text(relay.generate_srt(cues), encoding="utf-8")
    (output / "captions.vtt").write_text(relay.generate_vtt(cues), encoding="utf-8")
    atomic_json(output / "captions.json", [asdict(c) for c in cues])
    metadata = dict(
        title=meaning["headline"],
        description=meaning["context"],
        source_url=packet["canonical_source_url"],
        event_date=packet["event_date"],
        speaker=packet["speaker"],
        format=selection["format"],
    )
    atomic_json(
        output / "destination_metadata.json",
        dict(youtube_shorts=metadata, tiktok=metadata),
    )
    atomic_json(
        output / "review_request.json",
        dict(
            schema="contentops.signal_clips.media_review_request.v1",
            source_sha256=binding,
            edit_sha256=media_binding,
            original_media=packet["media"],
            transcript=packet["transcript"],
            span=span,
            format=selection["format"],
            assets={
                name: relay.sha256_file(output / name)
                for name in relay.ARTIFACT_FILES.values()
            },
            meaning_layers={
                key: meaning[key]
                for key in (
                    "speaker_claim",
                    "independent_evidence",
                    "cc_interpretation",
                )
            },
            gates=[
                "ORIGINAL_AUDIO_LISTENING",
                "SOURCE_AUDIO_ALIGNMENT",
                "CONTEXT_AND_QUALIFIERS",
                "VISUAL_AND_CAPTION_LEGIBILITY",
                "ASSET_SPECIFIC_RIGHTS",
                "SEPARATE_PUBLICATION_AUTHORITY",
            ],
            review_state="NOT_REVIEWED",
            production_eligible=False,
        ),
    )
    files = [
        *relay.ARTIFACT_FILES.values(),
        "selection_request.json",
        "meaning_request.json",
        "extracted_clip.mp4",
        "current_source.json",
        "selection_return.json",
        "meaning_return.json",
        "destination_metadata.json",
        "review_request.json",
    ]
    result = dict(
        schema="contentops.signal_clips.private_package.v1",
        stage="PRIVATE_PREPARED_REVIEW_REQUIRED",
        source_sha256=binding,
        edit_sha256=media_binding,
        holds=holds
        + [
            "FINAL_MEDIA_REVIEW_REQUIRED",
            "ASSET_SPECIFIC_PUBLICATION_RIGHTS_NOT_CLEARED",
        ],
        production_eligible=False,
        publication_control=copy.deepcopy(relay.PUBLICATION_CONTROL),
        file_hashes={name: relay.sha256_file(output / name) for name in files},
    )
    atomic_json(manifest, result)
    return result


def command(argv=None):
    parser = argparse.ArgumentParser(
        description="Current-source private Speech Highlight Relay"
    )
    parser.add_argument("--source-config")
    parser.add_argument("--owner-source")
    parser.add_argument("--stream-file")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--selection-return")
    parser.add_argument("--meaning-return")
    parser.add_argument("--review-package", type=Path)
    parser.add_argument("--review-return", type=Path)
    parser.add_argument("--review-surface", action="store_true")
    parser.add_argument("--revision-from", type=Path)
    parser.add_argument("--revision-spec", type=Path)
    args = parser.parse_args(argv)

    def load(path):
        return json.loads(Path(path).read_text(encoding="utf-8")) if path else None

    if args.review_package or args.revision_from:
        from . import speech_highlight_review_v1 as review

        if any(
            (
                args.source_config,
                args.owner_source,
                args.stream_file,
                args.selection_return,
                args.meaning_return,
            )
        ) or (args.review_package and args.revision_from):
            parser.error(
                "Preparation, review and successor revision are separate bound operations"
            )
        if args.revision_from:
            if not args.revision_spec or not args.review_return or args.review_surface:
                parser.error("Revision requires exact spec and reviewer return")
            result = review.revise(
                args.revision_from,
                args.repo_root,
                args.output_dir,
                load(args.revision_spec),
                load(args.review_return),
            )
        else:
            if args.revision_spec or not (args.review_return or args.review_surface):
                parser.error("Review requires a return or local surface")
            result = {}
            values = [load(args.review_return)] if args.review_return else []
            if values:
                result["review"] = review.ingest_review(
                    args.review_package, args.repo_root, values[0], args.output_dir
                )
            if args.review_surface:
                result["surface"] = review.review_entry(
                    args.review_package, args.repo_root, args.output_dir, values
                )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    if args.review_return or args.review_surface or args.revision_spec:
        parser.error("Review or revision needs its exact existing package")

    if not args.source_config:
        if not (args.owner_source or args.stream_file):
            parser.error("An explicit source or existing stream is required")
        if args.selection_return or args.meaning_return:
            parser.error("Native returns require a bound source config")
        root = args.repo_root.resolve()
        output = args.output_dir.resolve()
        if not output.is_relative_to(
            root / ".task-runtime" / "speech_highlight_relay_v1"
        ):
            raise relay.SpeechRelayError("Existing isolated relay output root required")
        plan = dict(
            schema="contentops.signal_clips.discovery.v1",
            candidates=candidates(
                load(args.owner_source), load(args.stream_file) or []
            ),
            input_hashes={
                k: relay.sha256_file(Path(v))
                for k, v in (
                    ("owner_source", args.owner_source),
                    ("existing_stream", args.stream_file),
                )
                if v
            },
            publication_control=copy.deepcopy(relay.PUBLICATION_CONTROL),
        )
        output.mkdir(parents=True, exist_ok=True)
        path = output / "candidate_plan.json"
        if path.exists() and json.loads(path.read_text(encoding="utf-8")) != plan:
            raise relay.SpeechRelayError(
                "Discovery inputs changed; preserve prior plan"
            )
        if not path.exists():
            atomic_json(path, plan)
        print(json.dumps(plan, ensure_ascii=False))
        return 0
    if args.owner_source or args.stream_file:
        parser.error("Discovery and preparation are separate bound stages")
    print(
        json.dumps(
            prepare(
                load(args.source_config),
                args.repo_root,
                args.output_dir,
                load(args.selection_return),
                load(args.meaning_return),
            ),
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(command())
