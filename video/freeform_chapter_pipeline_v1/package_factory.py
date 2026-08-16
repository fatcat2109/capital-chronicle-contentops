"""Platform-neutral multiformat and multilingual package contracts.

This extends the free-form chapter substrate without becoming a renderer, creative
director, translation engine, TTS backend, or platform transport.  It binds independently
produced picture, audio, captions, metadata, evidence, and rights artifacts into immutable
content-addressed packages and validates only hard production invariants.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


class PackageFactoryError(RuntimeError):
    """A deterministic package-boundary failure."""


FORMAT_CONTRACTS: dict[str, dict[str, Any]] = {
    "LONGFORM_16_9": {
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "minimum_seconds": 300,
        "maximum_seconds": 2700,
    },
    "SHORT_9_16": {
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "minimum_seconds": 1,
        "maximum_seconds": 60,
    },
}

FORBIDDEN_MANIFEST_KEY_PARTS = (
    "credential",
    "password",
    "secret",
    "session",
    "token",
    "cookie",
    "destination_account",
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    path = path.resolve()
    if not path.is_file():
        raise PackageFactoryError(f"Artifact is missing: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class ArtifactIdentity:
    path: str
    sha256: str
    size_bytes: int

    @classmethod
    def from_path(cls, path: Path) -> "ArtifactIdentity":
        resolved = path.resolve()
        return cls(
            path=str(resolved),
            sha256=sha256_file(resolved),
            size_bytes=resolved.stat().st_size,
        )


@dataclass(frozen=True)
class CaptionCue:
    cue_id: str
    start_seconds: float
    end_seconds: float
    text: str
    speaker: str = "NARRATOR"
    source_audio_sha256: str | None = None


def _flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return "\n".join(_flatten_text(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return "\n".join(_flatten_text(item) for item in value)
    return ""


def _normalized_for_anchor(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = normalized.replace("−", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", normalized).strip()


def validate_anchor_preservation(
    anchor_contract: Mapping[str, Any], localized_payload: Mapping[str, Any]
) -> dict[str, Any]:
    """Verify declared factual surfaces in actual localized viewer-facing text.

    Each required anchor declares locale-specific accepted surface forms.  This checks the
    emitted narration, captions, metadata, and chapter labels; it does not rewrite or grade
    prose. Direction, units, chronology, uncertainty, and authority identity are represented
    as first-class anchors rather than inferred creatively.
    """

    language = str(localized_payload.get("language", ""))
    if not language:
        raise PackageFactoryError("Localized payload must declare language")
    corpus = _normalized_for_anchor(_flatten_text(localized_payload.get("localized_fields", {})))
    results: list[dict[str, Any]] = []
    failures: list[str] = []
    seen_ids: set[str] = set()
    for anchor in anchor_contract.get("anchors", []):
        anchor_id = str(anchor.get("id", ""))
        if not anchor_id or anchor_id in seen_ids:
            raise PackageFactoryError("Anchor IDs must be non-empty and unique")
        seen_ids.add(anchor_id)
        required = bool(anchor.get("required", True))
        locale_forms = anchor.get("accepted_forms", {}).get(language)
        if locale_forms is None:
            locale_forms = anchor.get("accepted_forms", {}).get("default", [])
        forms = [_normalized_for_anchor(str(item)) for item in locale_forms if str(item).strip()]
        matched = next((form for form in forms if form in corpus), None)
        passed = (not required) or matched is not None
        if not passed:
            failures.append(anchor_id)
        results.append(
            {
                "id": anchor_id,
                "kind": anchor.get("kind"),
                "required": required,
                "matched_form": matched,
                "result": "PRESERVED" if passed else "MISSING_OR_CONFLICTING",
            }
        )
    return {
        "schema": "contentops.v2.locale_anchor_validation.v1",
        "language": language,
        "source_story_id": anchor_contract.get("source_story_id"),
        "result": "PASS_FACTUAL_ANCHORS" if not failures else "FAIL_FACTUAL_ANCHORS",
        "failures": failures,
        "anchors": results,
    }


def build_caption_cues(
    *,
    language: str,
    media_duration_seconds: float,
    segments: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build cues from placed audio segments and their measured durations."""

    cues: list[CaptionCue] = []
    previous_end = 0.0
    for index, segment in enumerate(segments, start=1):
        start = round(float(segment["timeline_start_seconds"]), 6)
        duration = round(float(segment["actual_audio_duration_seconds"]), 6)
        end = round(start + duration, 6)
        text = str(segment.get("caption_text", "")).strip()
        if not text:
            raise PackageFactoryError(f"Caption segment {index} has no text")
        if start < 0 or duration <= 0 or end > media_duration_seconds + 0.001:
            raise PackageFactoryError(f"Caption segment {index} is outside media duration")
        if start < previous_end - 0.001:
            raise PackageFactoryError(f"Caption segment {index} overlaps the previous cue")
        audio_hash = None
        if segment.get("audio_path"):
            audio_hash = sha256_file(Path(str(segment["audio_path"])))
        cues.append(
            CaptionCue(
                cue_id=str(segment.get("cue_id") or f"{language}-{index:04d}"),
                start_seconds=start,
                end_seconds=end,
                text=text,
                speaker=str(segment.get("speaker", "NARRATOR")),
                source_audio_sha256=audio_hash,
            )
        )
        previous_end = end
    return {
        "schema": "contentops.v2.timed_captions.v1",
        "language": language,
        "media_duration_seconds": round(media_duration_seconds, 6),
        "timing_basis": "ACTUAL_PLACED_AUDIO_SEGMENT_DURATIONS",
        "cues": [asdict(cue) for cue in cues],
    }


def validate_caption_set(caption_set: Mapping[str, Any]) -> dict[str, Any]:
    duration = float(caption_set.get("media_duration_seconds", 0))
    previous_end = 0.0
    errors: list[str] = []
    for cue in caption_set.get("cues", []):
        start = float(cue["start_seconds"])
        end = float(cue["end_seconds"])
        cue_id = str(cue.get("cue_id", "?"))
        if start < 0 or end <= start or end > duration + 0.001:
            errors.append(f"{cue_id}:invalid_range")
        if start < previous_end - 0.001:
            errors.append(f"{cue_id}:overlap")
        if not str(cue.get("text", "")).strip():
            errors.append(f"{cue_id}:empty")
        previous_end = max(previous_end, end)
    return {
        "result": "PASS_CAPTIONS" if not errors else "FAIL_CAPTIONS",
        "cue_count": len(caption_set.get("cues", [])),
        "errors": errors,
    }


def _timestamp(seconds: float, *, vtt: bool) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    whole_seconds, milliseconds = divmod(milliseconds, 1000)
    separator = "." if vtt else ","
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}{separator}{milliseconds:03d}"


def caption_text(caption_set: Mapping[str, Any], *, kind: str) -> str:
    validation = validate_caption_set(caption_set)
    if validation["result"] != "PASS_CAPTIONS":
        raise PackageFactoryError(f"Invalid captions: {validation['errors']}")
    kind = kind.lower()
    if kind not in {"srt", "vtt"}:
        raise PackageFactoryError("Caption kind must be srt or vtt")
    lines: list[str] = ["WEBVTT", ""] if kind == "vtt" else []
    for index, cue in enumerate(caption_set.get("cues", []), start=1):
        if kind == "srt":
            lines.append(str(index))
        lines.append(
            f"{_timestamp(float(cue['start_seconds']), vtt=kind == 'vtt')} --> "
            f"{_timestamp(float(cue['end_seconds']), vtt=kind == 'vtt')}"
        )
        lines.append(str(cue["text"]).strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_caption_artifacts(caption_set: Mapping[str, Any], output_root: Path) -> dict[str, Any]:
    output_root = output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    language = str(caption_set["language"])
    json_path = output_root / f"captions.{language}.json"
    srt_path = output_root / f"captions.{language}.srt"
    vtt_path = output_root / f"captions.{language}.vtt"
    json_path.write_text(json.dumps(caption_set, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    srt_path.write_text(caption_text(caption_set, kind="srt"), encoding="utf-8")
    vtt_path.write_text(caption_text(caption_set, kind="vtt"), encoding="utf-8")
    return {
        "json": asdict(ArtifactIdentity.from_path(json_path)),
        "srt": asdict(ArtifactIdentity.from_path(srt_path)),
        "vtt": asdict(ArtifactIdentity.from_path(vtt_path)),
    }


def _fps_value(value: Any) -> float:
    text = str(value)
    if "/" in text:
        numerator, denominator = text.split("/", 1)
        return float(numerator) / float(denominator)
    return float(text)


def validate_media_probe(format_kind: str, probe: Mapping[str, Any]) -> dict[str, Any]:
    if format_kind not in FORMAT_CONTRACTS:
        raise PackageFactoryError(f"Unsupported format: {format_kind}")
    contract = FORMAT_CONTRACTS[format_kind]
    video = next(
        (item for item in probe.get("streams", []) if item.get("codec_type") == "video"),
        None,
    )
    audio = next(
        (item for item in probe.get("streams", []) if item.get("codec_type") == "audio"),
        None,
    )
    errors: list[str] = []
    if video is None:
        errors.append("missing_video")
    else:
        if int(video.get("width", 0)) != contract["width"]:
            errors.append("wrong_width")
        if int(video.get("height", 0)) != contract["height"]:
            errors.append("wrong_height")
        if abs(_fps_value(video.get("r_frame_rate", 0)) - contract["fps"]) > 0.01:
            errors.append("wrong_fps")
        if int(video.get("width", 0)) >= 3840 or int(video.get("height", 0)) >= 2160:
            errors.append("4k_forbidden")
    if audio is None:
        errors.append("missing_audio")
    duration = float(probe.get("format", {}).get("duration", 0))
    if duration < contract["minimum_seconds"] or duration > contract["maximum_seconds"] + 0.5:
        errors.append("duration_outside_contract")
    return {
        "result": "PASS_MEDIA_CONTRACT" if not errors else "FAIL_MEDIA_CONTRACT",
        "format": format_kind,
        "duration_seconds": duration,
        "errors": errors,
    }


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key).casefold()
            yield from _walk_keys(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _walk_keys(item)


def validate_platform_neutral(spec: Mapping[str, Any]) -> None:
    key_names = list(_walk_keys(spec))
    forbidden = [
        key
        for key in key_names
        if any(part in key for part in FORBIDDEN_MANIFEST_KEY_PARTS)
    ]
    if forbidden:
        raise PackageFactoryError(f"Manifest contains credential/account-like keys: {forbidden}")
    boundaries = spec.get("hard_boundaries", {})
    if boundaries.get("video_public_write_authority") is not False:
        raise PackageFactoryError("ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY is required")
    if boundaries.get("v1_mutation_authority") is not False:
        raise PackageFactoryError("V1 mutation authority must be false")
    if boundaries.get("scheduler_mutation_authority") is not False:
        raise PackageFactoryError("Scheduler mutation authority must be false")
    if boundaries.get("allow_4k") is not False:
        raise PackageFactoryError("4K must remain disabled")


def _artifact(value: str | Path | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return asdict(ArtifactIdentity.from_path(Path(value)))


def build_publication_package(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Bind existing artifacts without rendering or platform transport."""

    validate_platform_neutral(spec)
    format_kind = str(spec.get("format"))
    if format_kind not in FORMAT_CONTRACTS:
        raise PackageFactoryError(f"Unsupported format: {format_kind}")
    language = str(spec.get("language", ""))
    if not language:
        raise PackageFactoryError("Package language is required")
    metadata = dict(spec.get("metadata", {}))
    if not str(metadata.get("title", "")).strip() or not str(metadata.get("description", "")).strip():
        raise PackageFactoryError("Localized title and description are required")

    artifacts = {
        "clean_video": _artifact(spec.get("clean_video")),
        "burned_caption_video": _artifact(spec.get("burned_caption_video")),
        "audio": _artifact(spec.get("audio")),
        "caption_json": _artifact(spec.get("caption_json")),
        "caption_srt": _artifact(spec.get("caption_srt")),
        "caption_vtt": _artifact(spec.get("caption_vtt")),
    }
    for required in ("clean_video", "audio", "caption_json", "caption_srt", "caption_vtt"):
        if artifacts[required] is None:
            raise PackageFactoryError(f"Required package artifact is missing: {required}")

    rights = [str(item) for item in spec.get("rights_provenance_refs", [])]
    evidence = [str(item) for item in spec.get("factual_evidence_refs", [])]
    if not rights or not evidence:
        raise PackageFactoryError("Rights/provenance and factual/evidence references are required")

    identity_payload = {
        "schema": "contentops.v2.platform_neutral_publication_package.v1",
        "source_story_id": spec.get("source_story_id"),
        "source_film_id": spec.get("source_film_id"),
        "format": format_kind,
        "language": language,
        "artifacts": artifacts,
        "metadata": metadata,
        "chapters": list(spec.get("chapters", [])),
        "rights_provenance_refs": rights,
        "factual_evidence_refs": evidence,
        "intended_future_surfaces": list(spec.get("intended_future_surfaces", [])),
        "generation_version": str(spec.get("generation_version", "v1")),
        "hard_boundaries": dict(spec["hard_boundaries"]),
    }
    digest = hashlib.sha256(canonical_json(identity_payload)).hexdigest()
    return {
        **identity_payload,
        "package_id": f"pkg_{digest}",
        "generation_timestamp_utc": str(
            spec.get("generation_timestamp_utc")
            or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        ),
        "transport": None,
        "publication_state": "PACKAGE_ONLY_ZERO_PUBLIC_WRITE",
    }


def load_locale_registry(path: Path) -> dict[str, Any]:
    registry = json.loads(path.read_text(encoding="utf-8"))
    locales = registry.get("locales", {})
    if not isinstance(locales, Mapping) or not locales:
        raise PackageFactoryError("Locale registry must contain configurable locale entries")
    for tag, profile in locales.items():
        if str(profile.get("tag")) != tag:
            raise PackageFactoryError(f"Locale profile tag mismatch: {tag}")
        if profile.get("support_status") not in {
            "CANONICAL_EXISTING",
            "DEMONSTRATION_REQUIRED",
            "PROOF_COMPLETE_OWNER_VOICE_REVIEW_REQUIRED",
            "VOICE_BACKEND_NOT_ACCEPTED",
        }:
            raise PackageFactoryError(f"Invalid support status for {tag}")
    return registry


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    anchor = sub.add_parser("validate-anchors")
    anchor.add_argument("contract", type=Path)
    anchor.add_argument("localized_payload", type=Path)

    captions = sub.add_parser("captions")
    captions.add_argument("segments", type=Path)
    captions.add_argument("output_root", type=Path)

    package = sub.add_parser("package")
    package.add_argument("spec", type=Path)
    package.add_argument("output", type=Path)

    locale = sub.add_parser("validate-locales")
    locale.add_argument("registry", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate-anchors":
        result = validate_anchor_preservation(
            json.loads(args.contract.read_text(encoding="utf-8")),
            json.loads(args.localized_payload.read_text(encoding="utf-8")),
        )
    elif args.command == "captions":
        payload = json.loads(args.segments.read_text(encoding="utf-8"))
        caption_set = build_caption_cues(
            language=payload["language"],
            media_duration_seconds=float(payload["media_duration_seconds"]),
            segments=payload["segments"],
        )
        result = {
            "validation": validate_caption_set(caption_set),
            "artifacts": write_caption_artifacts(caption_set, args.output_root),
        }
    elif args.command == "package":
        result = build_publication_package(json.loads(args.spec.read_text(encoding="utf-8")))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        result = load_locale_registry(args.registry)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
