"""Offline review and immutable successor edits of the existing private speech relay."""

from __future__ import annotations

import copy
import json
import math
import shutil
from pathlib import Path

from live_contentops import speech_highlight_current_source_v1 as current
from live_contentops import speech_highlight_relay_v1 as relay

DIMENSIONS = ("VISUAL", "CAPTIONS", "AUDIO", "TIMING", "CONTEXT", "RIGHTS")
STATES = {"PASS", "REVISION_REQUESTED", "NOT_VERIFIED"}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def isolated(root, path):
    root, path = Path(root).resolve(), Path(path).resolve()
    if not path.is_relative_to(root / ".task-runtime/speech_highlight_relay_v1"):
        raise relay.SpeechRelayError("Existing isolated relay root required")
    return path


def frozen(path, value):
    if path.exists():
        if read(path) != value:
            raise relay.SpeechRelayError("Immutable review/revision input changed")
    else:
        current.atomic_json(path, value)


def package(directory, root):
    directory = isolated(root, directory)
    manifest = read(directory / "current_package.json")
    if (
        manifest.get("production_eligible") is not False
        or manifest.get("publication_control") != relay.PUBLICATION_CONTROL
    ):
        raise relay.SpeechRelayError("Private zero-write package required")
    required = {
        *relay.ARTIFACT_FILES.values(),
        "current_source.json",
        "selection_return.json",
        "selection_request.json",
        "meaning_return.json",
        "meaning_request.json",
        "extracted_clip.mp4",
        "destination_metadata.json",
        "review_request.json",
    }
    if not required.issubset(manifest.get("file_hashes", {})):
        raise relay.SpeechRelayError("Incomplete private package binding")
    for name, sha in manifest["file_hashes"].items():
        path = (directory / name).resolve()
        if path.parent != directory or relay.sha256_file(path) != sha:
            raise relay.SpeechRelayError("Package artifact drift or unsafe path")
    source = read(directory / "current_source.json")
    current.validate_source(source, Path(root).resolve())
    if current.digest(source) != manifest["source_sha256"]:
        raise relay.SpeechRelayError("Package source binding mismatch")
    selection = read(directory / "selection_return.json")
    meaning = read(directory / "meaning_return.json")
    if (
        selection.get("source_sha256") != manifest["source_sha256"]
        or meaning.get("source_sha256") != manifest["source_sha256"]
        or meaning.get("selection_sha256") != current.digest(selection)
    ):
        raise relay.SpeechRelayError("Native source/selection binding mismatch")
    binding = dict(
        package_sha256=current.digest(manifest),
        source_sha256=manifest["source_sha256"],
        original_media_sha256=source["media"]["sha256"],
        transcript_sha256=source["transcript"]["sha256"],
        edit_sha256=manifest["edit_sha256"],
        affected_outputs=manifest["file_hashes"],
    )
    return directory, manifest, source, selection, meaning, binding


def review_context(directory, root):
    directory, manifest, source, selection, meaning, binding = package(directory, root)
    return dict(
        schema="contentops.signal_clips.review_context.v1",
        binding=binding,
        source=source,
        selection=selection,
        meaning=meaning,
        cues=read(directory / "captions.json"),
        holds=manifest["holds"],
        reviewer_attestation="REPORTED_IDENTITY_NOT_INDEPENDENTLY_ATTESTED",
        production_eligible=False,
        publication_control=copy.deepcopy(relay.PUBLICATION_CONTROL),
    )


def validate_review(directory, root, value):
    context = review_context(directory, root)
    if (
        value.get("schema") != "contentops.signal_clips.review_return.v1"
        or value.get("binding") != context["binding"]
    ):
        raise relay.SpeechRelayError("Stale or mismatched review binding")
    reviewer = value.get("reviewer", {})
    if not all(
        isinstance(reviewer.get(k), str) and reviewer[k].strip()
        for k in ("identity", "method", "capability", "limitations")
    ):
        raise relay.SpeechRelayError(
            "Explicit reviewer provenance and limitations required"
        )
    if reviewer.get("attestation") != "SELF_REPORTED_NOT_INDEPENDENTLY_ATTESTED":
        raise relay.SpeechRelayError("Unsupported reviewer attestation claim")
    if reviewer["capability"] not in {
        "VISUAL_ONLY",
        "CAPABLE_ORIGINAL_AUDIO_REVIEW",
        "RIGHTS_REVIEW",
    }:
        raise relay.SpeechRelayError("Unsupported reviewer capability claim")
    findings = value.get("findings", {})
    if set(findings) != set(DIMENSIONS):
        raise relay.SpeechRelayError("Every review dimension must remain explicit")
    for dimension, finding in findings.items():
        if (
            finding.get("status") not in STATES
            or not isinstance(finding.get("notes"), str)
            or not finding["notes"].strip()
        ):
            raise relay.SpeechRelayError("Explicit finding status and notes required")
        if finding["status"] == "NOT_VERIFIED":
            continue
        if not finding.get("evidence"):
            raise relay.SpeechRelayError("Observed finding requires pinned evidence")
        for spec in finding["evidence"]:
            relay._local_artifact(Path(root).resolve(), spec)
        if dimension in {"AUDIO", "TIMING"} and finding["status"] == "PASS":
            if (
                reviewer["capability"] != "CAPABLE_ORIGINAL_AUDIO_REVIEW"
                or finding.get("method") != "ORIGINAL_AND_RENDER_LISTENING"
            ):
                raise relay.SpeechRelayError("Text/playback/ASR is not audio review")
        if (
            dimension == "RIGHTS"
            and finding["status"] == "PASS"
            and finding.get("method") != "SOURCE_SPECIFIC_RIGHTS_REVIEW"
        ):
            raise relay.SpeechRelayError("Source-specific rights evidence required")
    return context


def ingest_review(directory, root, value, output):
    output = isolated(root, output)
    # Never add a review to the frozen media directory or its descendants.
    directory = Path(directory).resolve()
    if output == directory or output.is_relative_to(directory):
        raise relay.SpeechRelayError(
            "Review receipts must preserve original package directory"
        )
    context = validate_review(directory, root, value)
    output.mkdir(parents=True, exist_ok=True)
    identity = current.digest(value)
    frozen(output / (identity + ".json"), value)
    receipt = dict(
        schema="contentops.signal_clips.review_receipt.v1",
        review_sha256=identity,
        binding=context["binding"],
        decision="REVISION_REQUESTED"
        if any(f["status"] == "REVISION_REQUESTED" for f in value["findings"].values())
        else "REVIEW_RECORDED_WITH_OPEN_GATES",
        findings=value["findings"],
        reviewer=value["reviewer"],
        unresolved=[d for d, f in value["findings"].items() if f["status"] != "PASS"],
        acceptance_scope="REPORTED_FINDINGS_ONLY_NOT_AUTOMATIC_AUDIO_RIGHTS_OR_PUBLICATION_ACCEPTANCE",
        production_eligible=False,
        publication_control=copy.deepcopy(relay.PUBLICATION_CONTROL),
    )
    frozen(output / (identity + ".receipt.json"), receipt)
    return receipt


def validate_cues(cues, duration, original_quote, speaker=None):
    last = 0
    ids = set()
    for cue in cues:
        if (
            not isinstance(cue.get("cue_id"), str)
            or cue["cue_id"] in ids
            or (speaker is not None and cue.get("speaker") != speaker)
        ):
            raise relay.SpeechRelayError(
                "Exact source speaker and distinct cue identities required"
            )
        ids.add(cue["cue_id"])
        a, b = cue["start_seconds"], cue["end_seconds"]
        if (
            not all(
                isinstance(n, (int, float))
                and not isinstance(n, bool)
                and math.isfinite(n)
                for n in (a, b)
            )
            or not 0 <= a < b <= duration
            or a < last
            or not cue["text"].strip()
        ):
            raise relay.SpeechRelayError("Invalid successor cue timing")
        last = b
    if " ".join(" ".join(c["text"].split()) for c in cues) != " ".join(
        original_quote.split()
    ):
        raise relay.SpeechRelayError(
            "Caption wording correction requires separately verified source/transcript/native admission; do not rewrite speech"
        )


def revise(directory, root, output, spec, review):
    """Content-bound successor; source/clip never reacquired; no change to parent files."""
    root = Path(root).resolve()
    parent, old, source, selection, meaning, binding = package(directory, root)
    output = isolated(root, output)
    if (
        output == parent
        or output.is_relative_to(parent)
        or parent.is_relative_to(output)
    ):
        raise relay.SpeechRelayError("Distinct non-nested successor directory required")
    validate_review(parent, root, review)
    kind = spec.get("change_kind")
    if (
        spec.get("schema") != "contentops.signal_clips.revision.v1"
        or spec.get("parent_binding") != binding
        or spec.get("review_sha256") != current.digest(review)
        or kind not in {"PRESENTATION", "CAPTIONS", "SEMANTIC"}
        or not spec.get("reason")
    ):
        raise relay.SpeechRelayError(
            "Exact parent/review and warranted revision required"
        )
    dimension = {
        "PRESENTATION": "VISUAL",
        "CAPTIONS": "CAPTIONS",
        "SEMANTIC": "CONTEXT",
    }[kind]
    if review["findings"][dimension]["status"] != "REVISION_REQUESTED":
        raise relay.SpeechRelayError("Revision has no matching requested finding")
    old_presentation = (
        read(parent / "presentation.json")
        if (parent / "presentation.json").exists()
        else None
    )
    presentation = spec.get("presentation", old_presentation)
    if kind != "PRESENTATION" and presentation != old_presentation:
        raise relay.SpeechRelayError(
            "Presentation changes require their own reviewed revision"
        )
    cues = spec.get("cues", read(parent / "captions.json"))
    if kind != "CAPTIONS" and cues != read(parent / "captions.json"):
        raise relay.SpeechRelayError("Unexpected caption mutation")
    duration = selection["span"]["end_seconds"] - selection["span"]["start_seconds"]
    validate_cues(cues, duration, selection["exact_quote"], source["speaker"]["name"])
    new_meaning = spec.get("meaning_return", meaning)
    if kind != "SEMANTIC" and new_meaning != meaning:
        raise relay.SpeechRelayError("Unexpected semantic mutation")
    if kind == "SEMANTIC":
        if (
            new_meaning == meaning
            or new_meaning.get("source_sha256") != binding["source_sha256"]
            or new_meaning.get("selection_sha256") != current.digest(selection)
            or new_meaning.get("model") != "gpt-6.1-sol"
            or new_meaning.get("reasoning_effort") != "max"
            or new_meaning.get("role") != "MEANING"
            or new_meaning.get("native_turn_id") == meaning.get("native_turn_id")
            or not new_meaning.get("native_turn_id")
            or new_meaning.get("decision") != "KEEP"
        ):
            raise relay.SpeechRelayError(
                "Semantic correction requires fresh exact native meaning return"
            )
        if not all(
            isinstance(new_meaning.get(k), str) and new_meaning[k].strip()
            for k in (
                "headline",
                "context",
                "speaker_claim",
                "independent_evidence",
                "cc_interpretation",
            )
        ):
            raise relay.SpeechRelayError("Separate corrected meaning layers required")
    if kind == "PRESENTATION" and not presentation:
        raise relay.SpeechRelayError("Explicit presentation required")
    from live_contentops.speech_highlight_presentation_v1 import (
        validate_presentation,
        render,
    )

    if presentation:
        validate_presentation(presentation, duration)
    output.mkdir(parents=True, exist_ok=True)
    frozen(output / "revision.json", spec)
    frozen(output / "parent_review.json", review)
    edit = current.digest([binding, spec])
    done = output / "current_package.json"
    if done.exists():
        result = package(output, root)[1]
        if result["edit_sha256"] != edit:
            raise relay.SpeechRelayError("Successor edit changed")
        return result
    reused = []
    for name in (
        "current_source.json",
        "selection_request.json",
        "selection_return.json",
        "extracted_clip.mp4",
    ):
        src, target = parent / name, output / name
        if target.exists() and relay.sha256_file(target) != relay.sha256_file(src):
            raise relay.SpeechRelayError("Inherited stage drift")
        if not target.exists():
            shutil.copyfile(src, target)
        reused.append(name)
    frozen(output / "meaning_return.json", new_meaning)
    frozen(output / "meaning_request.json", read(parent / "meaning_request.json"))
    if kind != "SEMANTIC":
        reused.extend(["meaning_request.json", "meaning_return.json"])
    if presentation:
        frozen(output / "presentation.json", presentation)
    cue_objects = [relay.CaptionCue(**c) for c in cues]
    for key, captions in (
        ("clean_master", None),
        ("captioned_derivative", cue_objects),
    ):
        name = relay.ARTIFACT_FILES[key]
        if kind == "CAPTIONS" and key == "clean_master":
            if not (output / name).exists():
                shutil.copyfile(parent / name, output / name)
            if relay.sha256_file(output / name) != old["file_hashes"][name]:
                raise relay.SpeechRelayError("Unchanged clean stage drift")
            reused.append(name)
        else:

            def build(target, captions=captions):
                if presentation:
                    render(
                        output / "extracted_clip.mp4",
                        target,
                        source,
                        new_meaning,
                        duration,
                        presentation,
                        captions,
                    )
                else:
                    relay._render_vertical(
                        output / "extracted_clip.mp4",
                        target,
                        dict(source, selection=new_meaning),
                        duration,
                        captions,
                    )

            current.stage_artifact(
                output,
                name,
                edit,
                build,
                lambda path: relay._check_media(
                    relay.probe_media(path), duration, vertical=True
                ),
            )
    frozen(output / "captions.json", cues)
    for name, text in (
        ("captions.srt", relay.generate_srt(cue_objects)),
        ("captions.vtt", relay.generate_vtt(cue_objects)),
    ):
        path = output / name
        if path.exists() and path.read_text(encoding="utf-8") != text:
            raise relay.SpeechRelayError("Caption sidecar drift")
        if not path.exists():
            path.write_text(text, encoding="utf-8")
    metadata = copy.deepcopy(read(parent / "destination_metadata.json"))
    for value in metadata.values():
        value.update(
            title=new_meaning["headline"],
            description=new_meaning["context"],
            source_sha256=binding["source_sha256"],
            edit_sha256=edit,
            media_sha256=relay.sha256_file(
                output / relay.ARTIFACT_FILES["captioned_derivative"]
            ),
            state="PRIVATE_REVIEW_REQUIRED",
        )
    frozen(output / "destination_metadata.json", metadata)
    request = dict(
        read(parent / "review_request.json"),
        edit_sha256=edit,
        assets={
            name: relay.sha256_file(output / name)
            for name in relay.ARTIFACT_FILES.values()
        },
        meaning_layers={
            k: new_meaning[k]
            for k in ("speaker_claim", "independent_evidence", "cc_interpretation")
        },
        review_state="NOT_REVIEWED",
        previous_review_sha256=current.digest(review),
    )
    frozen(output / "review_request.json", request)
    names = [
        *relay.ARTIFACT_FILES.values(),
        "current_source.json",
        "selection_request.json",
        "selection_return.json",
        "meaning_request.json",
        "meaning_return.json",
        "extracted_clip.mp4",
        "destination_metadata.json",
        "review_request.json",
        "revision.json",
        "parent_review.json",
    ]
    if presentation:
        names.append("presentation.json")
    result = dict(
        schema=old["schema"],
        stage="PRIVATE_PREPARED_REVIEW_REQUIRED",
        source_sha256=binding["source_sha256"],
        edit_sha256=edit,
        parent_package_sha256=binding["package_sha256"],
        review_sha256=current.digest(review),
        change_kind=kind,
        reused_stages=reused,
        invalidated_stages=["MEDIA_REVIEW", "DESTINATION_METADATA"]
        + (
            ["CAPTIONED_RENDER", "CAPTION_SIDECARS"]
            if kind == "CAPTIONS"
            else ["CLEAN_RENDER", "CAPTIONED_RENDER"]
        ),
        holds=old["holds"],
        production_eligible=False,
        publication_control=copy.deepcopy(relay.PUBLICATION_CONTROL),
        file_hashes={name: relay.sha256_file(output / name) for name in names},
    )
    current.atomic_json(done, result)
    return result


def review_entry(directory, root, output, reviews=()):
    """One static local page. Playback or submitting JSON never certifies hearing."""
    directory = Path(directory).resolve()
    output = isolated(root, output)
    if output == directory or output.is_relative_to(directory):
        raise relay.SpeechRelayError("Review surface must preserve package directory")
    context = review_context(directory, root)
    for value in reviews:
        validate_review(directory, root, value)
    output.mkdir(parents=True, exist_ok=True)
    source = relay._local_artifact(Path(root).resolve(), context["source"]["media"])
    data = dict(
        context,
        reviews=list(reviews),
        source_uri=source.as_uri(),
        clean_uri=(directory / relay.ARTIFACT_FILES["clean_master"]).as_uri(),
        captioned_uri=(
            directory / relay.ARTIFACT_FILES["captioned_derivative"]
        ).as_uri(),
    )
    frozen(output / "review_context.json", data)
    template = (
        Path(__file__)
        .with_name("speech_highlight_review_v1.html")
        .read_text(encoding="utf-8")
    )
    encoded = (
        json.dumps(data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace("&", "\\u0026")
    )
    page = template.replace("__REVIEW_DATA__", encoded)
    target = output / "index.html"
    if target.exists() and target.read_text(encoding="utf-8") != page:
        raise relay.SpeechRelayError("Use a new review snapshot for changed findings")
    if not target.exists():
        target.write_text(page, encoding="utf-8")
    return dict(
        entry=target.as_uri(),
        path=str(target),
        binding=context["binding"],
        production_eligible=False,
    )
