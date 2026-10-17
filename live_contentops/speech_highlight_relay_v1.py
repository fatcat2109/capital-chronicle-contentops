"""Local, retained-source Speech Highlight Relay; publication stays on hold.

Selectively reconciles PR50 (85b70562): caption serializers, ffprobe inspection,
precise extraction and the FFmpeg vertical compositor. Seeded event discovery,
hardcoded quote selection, implicit provider calls and rights inference are excluded.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit


class SpeechRelayError(RuntimeError):
    """A local input, provenance, selection or package check failed."""


class PublicWriteProhibitedError(SpeechRelayError):
    """The local package cannot carry dispatch or publication authority."""


SOURCE_SCHEMA = "contentops.speech_highlight_relay.retained_source_packet.v1"
PACKAGE_SCHEMA = "contentops.speech_highlight_relay.package_manifest.v1"
PUBLICATION_CONTROL = {
    "publication_state": "PUBLICATION_HOLD",
    "write_authority": "ZERO_PUBLIC_WRITE",
    "public_writes": 0,
    "unknown_writes": 0,
    "network_calls_made": 0,
    "provider_calls": 0,
    "browser_calls": 0,
    "transport_dispatched": False,
    "destination_intents": [],
}
ARTIFACT_FILES = {
    "clean_master": "master_vertical_clean_1080x1920.mp4",
    "captioned_derivative": "derivative_vertical_captioned_1080x1920.mp4",
    "captions_srt": "captions.srt",
    "captions_vtt": "captions.vtt",
    "captions_json": "captions.json",
}
MANIFEST_FILES = {
    "source_packet.json", "source_verification.json", "rights_triage_manifest.json",
    "transcript_alignment_manifest.json", "highlight_selection_manifest.json", "render_receipt.json",
}
PRIVATE_REVIEW_PACKET_FILE = "private_review_packet.json"
REVIEW_BOUND_FILES = frozenset(
    set(ARTIFACT_FILES.values()) | MANIFEST_FILES | {"extracted_clip.mp4"}
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise SpeechRelayError(f"Required local artifact is missing: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_bytes(json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8") + b"\n")


def artifact_identity(path: Path) -> dict[str, Any]:
    return {"file": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def _binding_artifact(spec: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Keep an artifact's immutable identity while omitting its worktree-local path."""
    if spec is None:
        return None
    if not isinstance(spec, Mapping):
        raise SpeechRelayError("Artifact binding must be an object")
    return {key: value for key, value in spec.items() if key != "file"}


def source_binding(packet: dict[str, Any]) -> str:
    """Bind review and selection to this event, speaker and exact retained bytes.

    A digest checks integrity/scope, not the truth of metadata or legal permission.
    Local paths are omitted so the same retained bytes can move between worktrees.
    """
    # Bind all fields that can change source identity, clock/provenance, quote scope, rights
    # reference, or a review gate. Local artifact paths are deliberately omitted so a retained
    # packet can be verified in another checkout; their hashes remain bound.
    selection = copy.deepcopy(packet["selection"])
    selection.pop("source_binding_sha256", None)
    if isinstance(selection.get("third_party_review"), dict):
        selection["third_party_review"].pop("source_binding_sha256", None)
    rights = copy.deepcopy(packet["rights"])
    rights.pop("source_binding_sha256", None)
    rights["historical_note"] = _binding_artifact(rights.get("historical_note"))
    rights["policy_snapshot"] = _binding_artifact(rights.get("policy_snapshot"))
    transcript = copy.deepcopy(packet["transcript"])
    transcript["document"] = _binding_artifact(transcript.get("document"))
    identity = {
        "source_id": packet["source_id"],
        "publisher": packet["publisher"],
        "event_title": packet["event_title"],
        "event_date": packet["event_date"],
        "canonical_source_url": packet["canonical_source_url"],
        "player_url": packet["player_url"],
        "speaker": packet["speaker"],
        "provenance": packet["provenance"],
        "media": _binding_artifact(packet["media"]),
        "transcript": transcript,
        "rights": rights,
        "selection": selection,
        "publication_control": packet["publication_control"],
    }
    return hashlib.sha256(canonical_json(identity)).hexdigest()


@dataclass(frozen=True)
class CaptionCue:
    cue_id: str
    start_seconds: float
    end_seconds: float
    text: str
    speaker: str


def format_srt_timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, rest = divmod(milliseconds, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    secs, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt(cues: Sequence[CaptionCue]) -> str:
    return "\n\n".join(
        f"{i}\n{format_srt_timestamp(c.start_seconds)} --> {format_srt_timestamp(c.end_seconds)}\n{c.text}"
        for i, c in enumerate(cues, 1)
    ) + "\n"


def generate_vtt(cues: Sequence[CaptionCue]) -> str:
    return "WEBVTT\n\n" + "\n\n".join(
        f"{i}\n{format_srt_timestamp(c.start_seconds).replace(',', '.')} --> "
        f"{format_srt_timestamp(c.end_seconds).replace(',', '.')}\n{c.text}"
        for i, c in enumerate(cues, 1)
    ) + "\n"


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise SpeechRelayError(f"{label} must be a finite number")
    return float(value)


def _nonempty(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SpeechRelayError(f"Missing {label}")
    return value


def _local_artifact(root: Path, spec: dict[str, Any]) -> Path:
    relative = Path(_nonempty(spec.get("file"), "artifact.file"))
    path = (root / relative).resolve()
    if relative.is_absolute() or not path.is_relative_to(root.resolve()):
        raise SpeechRelayError("Retained artifact must be inside the supplied local root")
    expected = spec.get("sha256", "")
    if not re.fullmatch(r"[a-f0-9]{64}", expected) or sha256_file(path) != expected:
        raise SpeechRelayError(f"Artifact hash mismatch or missing pinned hash: {relative}")
    return path


def _run_local(command: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(
        command, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300, check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode:
        raise SpeechRelayError(f"Local {Path(command[0]).name} failed: {result.stderr[-3000:]}")
    return result.stdout


def probe_media(path: Path) -> dict[str, Any]:
    executable = shutil.which("ffprobe")
    if not executable:
        raise SpeechRelayError("ffprobe is required for local media verification")
    return json.loads(_run_local([
        executable, "-v", "error", "-protocol_whitelist", "file,pipe", "-show_entries",
        "format=duration,size:stream=codec_name,codec_type,width,height,r_frame_rate,sample_rate,channels",
        "-of", "json", str(path.resolve()),
    ]))


def _check_media(probe: dict[str, Any], duration: float, vertical: bool = False) -> None:
    video = [s for s in probe["streams"] if s["codec_type"] == "video"]
    audio = [s for s in probe["streams"] if s["codec_type"] == "audio"]
    if len(video) != 1 or len(audio) != 1:
        raise SpeechRelayError("Exactly one video and one authentic audio stream are required")
    if abs(float(probe["format"]["duration"]) - duration) > 0.12:
        raise SpeechRelayError("Media duration does not match the frozen span")
    if vertical and (
        video[0]["codec_name"] != "h264" or audio[0]["codec_name"] != "aac"
        or (video[0]["width"], video[0]["height"]) != (1080, 1920)
    ):
        raise SpeechRelayError("Expected 1080x1920 H264 video with AAC audio")


def _document_text(path: Path, spec: dict[str, Any]) -> str:
    if spec.get("format") == "PDF":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise SpeechRelayError("pypdf is required to validate a retained PDF transcript") from exc
        reader = PdfReader(path)
        page = spec.get("page_1based")
        if not isinstance(page, int) or isinstance(page, bool) or not 1 <= page <= len(reader.pages):
            raise SpeechRelayError("A valid transcript PDF page is required")
        return reader.pages[page - 1].extract_text() or ""
    if spec.get("format") == "UTF8_TEXT":
        return path.read_text(encoding="utf-8")
    raise SpeechRelayError("Unsupported retained transcript format")


def _words(text: str) -> str:
    # PDF extraction can replace curly apostrophes with U+FFFD. Normalize punctuation
    # only; preserve word order, negations, qualifiers and every numeric token.
    text = text.lower().replace("\u2019", "'").replace("\ufffd", "'")
    return " ".join(re.findall(r"[+-]?\d+(?:[.,]\d+)*%?|[a-z]+(?:'[a-z]+)*", text))


def validate_packet(packet: dict[str, Any], root: Path, *, inspect_media: bool = True) -> dict[str, Any]:
    if packet.get("schema") != SOURCE_SCHEMA:
        raise SpeechRelayError("Explicit retained source packet required; no catalog/discovery fallback")
    if canonical_json(packet.get("publication_control")) != canonical_json(PUBLICATION_CONTROL):
        raise PublicWriteProhibitedError("Exact PUBLICATION_HOLD / zero-write controls required")
    for field in ("source_id", "publisher", "event_title", "event_date"):
        _nonempty(packet.get(field), field)
    datetime.strptime(packet["event_date"], "%Y-%m-%d")
    for field in ("canonical_source_url", "player_url"):
        parsed = urlsplit(_nonempty(packet.get(field), field))
        if parsed.scheme != "https" or not parsed.hostname or parsed.query and "token=" in parsed.query.lower():
            raise SpeechRelayError(f"A public HTTPS provenance URL is required: {field}")
    speaker = _nonempty(packet["speaker"].get("name"), "speaker.name")
    _nonempty(packet["speaker"].get("identity_basis"), "speaker.identity_basis")
    provenance = packet["provenance"]
    if provenance.get("mode") != "RETAINED_SOURCE_REPLAY" or provenance.get("fresh_discovery") is not False:
        raise SpeechRelayError("Retained replay must not claim fresh or autonomous discovery")
    binding = source_binding(packet)
    media_path = _local_artifact(root, packet["media"])
    document = packet["transcript"]["document"]
    transcript_path = _local_artifact(root, document)
    transcript = packet["transcript"]
    if transcript.get("authority_class") != "OFFICIAL_TEXT_LOCALLY_ALIGNED":
        raise SpeechRelayError("This lane accepts retained text with explicit local alignment, not invented official timing")
    if transcript.get("audio_listening_status") != "NOT_VERIFIED":
        raise SpeechRelayError("An input flag cannot certify actual listening; record independent review separately")
    if transcript.get("timing_status") != "PROVISIONAL_DONOR_ALIGNMENT_REVIEW_REQUIRED":
        raise SpeechRelayError("Retained donor cue timing must keep its review-required status")
    rights = packet["rights"]
    if rights.get("triage_state") != "TRANSFORMATIVE_EDITORIAL_REVIEW_REQUIRED":
        raise SpeechRelayError("Private review only; this local lane cannot infer or accept affirmative reuse clearance")
    if rights.get("source_binding_sha256") != binding:
        raise SpeechRelayError("Rights review scope does not match this source")
    if rights.get("legal_clearance_status") != "NOT_VERIFIED" or rights.get("production_eligible") is not False:
        raise SpeechRelayError("Rights/legal or production eligibility cannot be promoted by this packet")
    _nonempty(rights.get("policy_url"), "rights.policy_url")
    _nonempty(rights.get("policy_evidence_status"), "rights.policy_evidence_status")
    if rights.get("policy_snapshot") is not None:
        _local_artifact(root, rights["policy_snapshot"])
    historical_note = _local_artifact(root, rights["historical_note"])
    if not rights.get("mandatory_restrictions"):
        raise SpeechRelayError("Explicit reuse restrictions are required")
    selection = packet["selection"]
    if selection.get("method") != "EXPLICIT_FROZEN_REPLAY_SPAN" or selection.get("is_autonomous") is not False:
        raise SpeechRelayError("An explicit frozen replay span is required; no seeded highlight fallback")
    if selection.get("source_binding_sha256") != binding:
        raise SpeechRelayError("Frozen selection does not match this event/publisher/media/transcript")
    _nonempty(selection.get("selected_by"), "selection.selected_by")
    _nonempty(selection.get("candidate_id"), "selection.candidate_id")
    span_start = _number(selection["start_seconds"], "selection.start")
    span_end = _number(selection["end_seconds"], "selection.end")
    duration = _number(packet["media"]["duration_seconds"], "media.duration")
    if not (0 <= span_start < span_end <= duration and 5 <= span_end - span_start <= 120):
        raise SpeechRelayError("Frozen span must fit the retained media and be 5..120 seconds")
    third_party = selection["third_party_review"]
    if third_party.get("source_binding_sha256") != binding:
        raise SpeechRelayError("Third-party review does not match this source")
    if (third_party.get("start_seconds"), third_party.get("end_seconds")) != (span_start, span_end):
        raise SpeechRelayError("Third-party review must cover this exact frozen span")
    if third_party.get("status") not in {"VISUAL_ONLY_REVIEW_AUDIO_PENDING", "UNKNOWN_REVIEW_REQUIRED"}:
        raise SpeechRelayError("Prohibited/present third-party material cannot inherit a safe status")
    _nonempty(third_party.get("scope"), "third-party scope")
    for field in ("headline", "context", "material_qualifiers", "context_limitations"):
        _nonempty(selection.get(field), f"selection.{field}")
    quote = _nonempty(selection.get("exact_quote"), "selection.exact_quote")
    protected = selection.get("protected_phrases")
    if not isinstance(protected, list) or not protected or any(
        not isinstance(phrase, str) or not phrase or phrase not in quote for phrase in protected
    ):
        raise SpeechRelayError("Protected qualifiers must remain verbatim in the frozen quote")
    if f" {_words(quote)} " not in f" {_words(_document_text(transcript_path, document))} ":
        raise SpeechRelayError("Quote is not a contiguous word sequence in the pinned transcript page")
    cues = []
    previous_end = span_start
    cue_ids: set[str] = set()
    for raw in selection["cues"]:
        start = _number(raw["start_seconds"], "cue.start")
        end = _number(raw["end_seconds"], "cue.end")
        cue_id = _nonempty(raw["cue_id"], "cue_id")
        if cue_id in cue_ids or not span_start <= start < end <= span_end or start < previous_end:
            raise SpeechRelayError("Cues must be unique, ordered, non-overlapping and fully contained in the span")
        if raw["speaker"] != speaker:
            raise SpeechRelayError("Caption speaker does not match source speaker")
        cue_ids.add(cue_id)
        previous_end = end
        cues.append(CaptionCue(cue_id, round(start - span_start, 3), round(end - span_start, 3),
                               _nonempty(raw["text"], "cue.text"), speaker))
    if not cues:
        raise SpeechRelayError("Timed cues are required")
    if " ".join(" ".join(c.text.split()) for c in cues) != " ".join(quote.split()):
        raise SpeechRelayError("Cue text must reconstruct the exact quote without omissions or additions")
    probe = probe_media(media_path) if inspect_media else None
    if probe:
        _check_media(probe, duration)
    return {
        "status": "INTEGRITY_AND_TEXT_CHECKED_PRIVATE_REVIEW_ONLY",
        "source_binding_sha256": binding,
        "media": artifact_identity(media_path), "transcript": artifact_identity(transcript_path),
        "historical_rights_note": artifact_identity(historical_note), "source_probe": probe,
        "clip_duration_seconds": round(span_end - span_start, 3),
        "relative_cues": [asdict(c) for c in cues],
        "audio_listening_status": "NOT_VERIFIED", "caption_timing_status": transcript["timing_status"],
        "legal_clearance_status": "NOT_VERIFIED", "production_eligible": False,
        "discovery_status": "RETAINED_REPLAY_ONLY", "selection_method": selection["method"],
    }


class DynamicMediaClipper:
    """PR50's bounded FFmpeg extraction seam, restricted to local files."""

    @staticmethod
    def extract_clip(source_media_path: Path, start_seconds: float, duration_seconds: float,
                     output_clip_path: Path) -> Path:
        executable = shutil.which("ffmpeg")
        if not executable:
            raise SpeechRelayError("ffmpeg is required for local rendering")
        _run_local([
            executable, "-v", "error", "-nostdin", "-n", "-protocol_whitelist", "file,pipe",
            "-i", str(source_media_path), "-ss", f"{start_seconds:.3f}", "-t", f"{duration_seconds:.3f}",
            "-map", "0:v:0", "-map", "0:a:0", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", str(output_clip_path),
        ])
        return output_clip_path


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpeechRelayError(f"Cannot read JSON review artifact: {path.name}") from exc
    if not isinstance(value, dict):
        raise SpeechRelayError(f"JSON review artifact must be an object: {path.name}")
    return value


def _private_review_packet_body(package_dir: Path, repo_root: Path) -> dict[str, Any]:
    """Compose the one offline review packet from the already written package bytes."""
    source_packet = _read_json(package_dir / "source_packet.json")
    expected_verification = validate_packet(source_packet, repo_root, inspect_media=False)
    source_verification = _read_json(package_dir / "source_verification.json")
    expected_without_probe = {key: value for key, value in expected_verification.items() if key != "source_probe"}
    actual_without_probe = {key: value for key, value in source_verification.items() if key != "source_probe"}
    if actual_without_probe != expected_without_probe:
        raise SpeechRelayError("Source verification differs from the current retained packet")
    verification = source_verification
    rights = _read_json(package_dir / "rights_triage_manifest.json")
    selection = _read_json(package_dir / "highlight_selection_manifest.json")
    transcript = _read_json(package_dir / "transcript_alignment_manifest.json")
    receipt = _read_json(package_dir / "render_receipt.json")
    if rights != source_packet["rights"] or selection != source_packet["selection"]:
        raise SpeechRelayError("Review manifests differ from the retained source packet")
    expected_transcript = {
        **source_packet["transcript"],
        "cues": verification["relative_cues"],
        "exact_quote": source_packet["selection"]["exact_quote"],
        "text_match_is_audio_verification": False,
    }
    if transcript != expected_transcript:
        raise SpeechRelayError("Transcript alignment manifest differs from the retained packet")

    bound_files: dict[str, str] = {}
    for filename in sorted(REVIEW_BOUND_FILES):
        path = package_dir / filename
        if not path.is_file():
            raise SpeechRelayError(f"Review packet bound file is missing: {filename}")
        bound_files[filename] = sha256_file(path)
    artifacts = {key: artifact_identity(package_dir / filename) for key, filename in ARTIFACT_FILES.items()}
    extracted_clip = artifact_identity(package_dir / "extracted_clip.mp4")
    source = {
        "source_id": source_packet["source_id"],
        "publisher": source_packet["publisher"],
        "event_title": source_packet["event_title"],
        "event_date": source_packet["event_date"],
        "canonical_source_url": source_packet["canonical_source_url"],
        "player_url": source_packet["player_url"],
        "speaker": source_packet["speaker"],
        "provenance": source_packet["provenance"],
        "media": source_packet["media"],
        "transcript": source_packet["transcript"],
        "rights_reference": source_packet["rights"],
    }
    gates = {
        "rights": {
            "triage_state": rights["triage_state"],
            "legal_clearance_status": rights["legal_clearance_status"],
            "production_eligible": rights["production_eligible"],
            "policy_url": rights["policy_url"],
            "policy_evidence_status": rights["policy_evidence_status"],
            "policy_snapshot": rights.get("policy_snapshot"),
        },
        "audio_listening": {
            "status": source_packet["transcript"]["audio_listening_status"],
            "render_status": receipt["audio_listening_status"],
        },
        "transcript_timing": {
            "authority_class": source_packet["transcript"]["authority_class"],
            "status": source_packet["transcript"]["timing_status"],
            "text_match_is_audio_verification": transcript["text_match_is_audio_verification"],
        },
        "third_party_continuity": selection["third_party_review"],
        "publication": source_packet["publication_control"],
    }
    body = {
        "schema": "contentops.speech_highlight_relay.private_review_packet.v1",
        "packet_version": 1,
        "composition_status": "IMMUTABLE_PRIVATE_REVIEW_PACKET",
        "package_id": f"{source_packet['source_id']}:{selection['candidate_id']}",
        "source_binding_sha256": verification["source_binding_sha256"],
        "source": source,
        "selection": selection,
        "gates": gates,
        "source_verification": verification,
        "render_outputs": {
            "artifacts": artifacts,
            "extracted_clip": extracted_clip,
            "render_receipt": receipt,
        },
        "bound_files": bound_files,
    }
    return body


def compose_private_review_packet(package_dir: Path, repo_root: Path) -> dict[str, Any]:
    """Write one deterministic offline packet binding source, gates and render bytes."""
    package_dir = package_dir.resolve()
    body = _private_review_packet_body(package_dir, repo_root.resolve())
    packet = {**body, "packet_sha256": hashlib.sha256(canonical_json(body)).hexdigest()}
    write_json(package_dir / PRIVATE_REVIEW_PACKET_FILE, packet)
    return packet


def verify_private_review_packet(package_dir: Path, repo_root: Path) -> dict[str, Any]:
    """Fail closed when any packet field, bound file, gate, or render identity drifts."""
    package_dir = package_dir.resolve()
    packet = _read_json(package_dir / PRIVATE_REVIEW_PACKET_FILE)
    packet_digest = packet.get("packet_sha256")
    body = {key: value for key, value in packet.items() if key != "packet_sha256"}
    if not isinstance(packet_digest, str) or hashlib.sha256(canonical_json(body)).hexdigest() != packet_digest:
        raise SpeechRelayError("Private review packet digest mismatch")
    expected = _private_review_packet_body(package_dir, repo_root.resolve())
    if body != expected:
        raise SpeechRelayError("Private review packet body does not match bound package bytes")
    publication = packet["gates"]["publication"]
    if canonical_json(publication) != canonical_json(PUBLICATION_CONTROL):
        raise PublicWriteProhibitedError("Private review packet publication gate is not zero-write")
    rights_gate = packet["gates"]["rights"]
    if (rights_gate["triage_state"] != "TRANSFORMATIVE_EDITORIAL_REVIEW_REQUIRED"
            or rights_gate["legal_clearance_status"] != "NOT_VERIFIED"
            or rights_gate["production_eligible"] is not False):
        raise SpeechRelayError("Private review packet rights gate was promoted")
    if packet["gates"]["audio_listening"]["status"] != "NOT_VERIFIED":
        raise SpeechRelayError("Private review packet audio gate was promoted")
    if packet["gates"]["transcript_timing"]["status"] != "PROVISIONAL_DONOR_ALIGNMENT_REVIEW_REQUIRED":
        raise SpeechRelayError("Private review packet timing gate was promoted")
    if packet["gates"]["third_party_continuity"]["status"] not in {
        "VISUAL_ONLY_REVIEW_AUDIO_PENDING", "UNKNOWN_REVIEW_REQUIRED",
    }:
        raise SpeechRelayError("Private review packet third-party gate was promoted")
    package_manifest_path = package_dir / "package_manifest.json"
    if not package_manifest_path.is_file():
        raise SpeechRelayError("Package manifest is required to anchor private review packet bytes")
    package_manifest = _read_json(package_manifest_path)
    if package_manifest.get("manifest_hashes", {}).get(PRIVATE_REVIEW_PACKET_FILE) != sha256_file(
        package_dir / PRIVATE_REVIEW_PACKET_FILE
    ):
        raise SpeechRelayError("Package manifest does not bind private review packet bytes")
    return {
        "status": "PASS_IMMUTABLE_PRIVATE_REVIEW_PACKET",
        "packet_sha256": packet_digest,
        "source_binding_sha256": packet["source_binding_sha256"],
        "publication_state": "PUBLICATION_HOLD",
        "public_writes": 0,
        "unknown_writes": 0,
        "legal_clearance_status": "NOT_VERIFIED",
        "audio_listening_status": "NOT_VERIFIED",
        "caption_timing_status": "PROVISIONAL_DONOR_ALIGNMENT_REVIEW_REQUIRED",
        "production_eligible": False,
    }


def _font(bold: bool = False) -> Path:
    names = (["C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
             if bold else ["C:/Windows/Fonts/arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])
    for name in names:
        if Path(name).is_file():
            return Path(name)
    raise SpeechRelayError("A local Arial or DejaVu font is required")


def _wrapped(text: str, font: Path, size: int, width: int, max_lines: int) -> str:
    from PIL import ImageFont

    measure = ImageFont.truetype(str(font), size)
    lines, line = [], ""
    for word in text.split():
        proposed = f"{line} {word}".strip()
        if measure.getlength(word) > width:
            raise SpeechRelayError("A render text token exceeds the safe width")
        if measure.getlength(proposed) > width:
            lines.append(line)
            line = word
        else:
            line = proposed
    lines.append(line)
    if len(lines) > max_lines:
        raise SpeechRelayError("Render text exceeds the reserved readable area; shorten the editorial text")
    return "\n".join(lines)


def _render_vertical(input_clip: Path, output_path: Path, packet: dict[str, Any],
                     duration: float, cues: Sequence[CaptionCue] | None) -> None:
    """Reconciled PR50 compositor: neutral framing, bounded text and honest review label."""
    executable = shutil.which("ffmpeg")
    if not executable:
        raise SpeechRelayError("ffmpeg is required")
    bold, regular = _font(True), _font()
    directory = output_path.parent
    text_specs = {
        "title": (packet["selection"]["headline"], 44, 900, 2, True),
        "speaker": (packet["speaker"]["name"], 34, 880, 1, True),
        "date": (f"{packet['speaker']['role']} | {packet['event_date']}", 22, 880, 2, False),
        "context": (packet["selection"]["context"], 32, 900, 4, False),
        "credit": (f"Source: {packet['publisher']}", 23, 900, 2, False),
    }
    if cues:
        for i, cue in enumerate(cues):
            text_specs[f"cue_{i}"] = (cue.text, 36, 880, 4, True)
    for name, (text, size, width, count, is_bold) in text_specs.items():
        (directory / f"text_{name}.txt").write_text(
            _wrapped(text, bold if is_bold else regular, size, width, count), encoding="utf-8",
        )
    fonts = {True: bold.as_posix().replace(":", "\\:"), False: regular.as_posix().replace(":", "\\:")}
    static_bold = fonts[True]

    def draw(name: str, y: int, size: int, color: str = "white", is_bold: bool = False,
             enable: str = "") -> str:
        return (f"drawtext=textfile=text_{name}.txt:expansion=none:fontfile='{fonts[is_bold]}':"
                f"fontsize={size}:fontcolor={color}:line_spacing=12:x=90:y={y}{enable}")

    filters = [
        f"color=c=0x0b1420:s=1080x1920:r=30:d={duration:.3f}[bg]",
        "[0:v]setpts=PTS-STARTPTS,scale=940:770:force_original_aspect_ratio=decrease,"
        "pad=940:770:(ow-iw)/2:(oh-ih)/2:color=0x0b1420[spk]",
        "[bg][spk]overlay=70:350,drawbox=x=70:y=1110:w=940:h=125:color=0x142638:t=fill,"
        "drawbox=x=70:y=1260:w=940:h=250:color=0x142638:t=fill,"
        "drawbox=x=70:y=1540:w=940:h=235:color=0x142638:t=fill,"
        f"drawtext=text='CAPITAL CHRONICLE':fontfile='{static_bold}':fontsize=30:fontcolor=0xf2bc66:x=90:y=75,"
        f"drawtext=text='RETAINED SPEECH EXCERPT':fontfile='{static_bold}':fontsize=22:fontcolor=0xb6c7d8:x=90:y=128,"
        f"{draw('title', 206, 44, is_bold=True)},"
        f"{draw('speaker', 1130, 34, is_bold=True)},{draw('date', 1181, 22, '0xb6c7d8')},"
        f"{draw('context', 1565, 32)},{draw('credit', 1798, 23, '0xb6c7d8')},"
        f"drawtext=text='PRIVATE REVIEW - PUBLICATION HOLD':fontfile='{static_bold}':fontsize=24:fontcolor=0xf2bc66:x=90:y=1870[base]",
    ]
    last = "base"
    for i, cue in enumerate(cues or []):
        enable = f":enable='gte(t,{cue.start_seconds:.3f})*lt(t,{cue.end_seconds:.3f})'"
        filters.append(f"[{last}]{draw(f'cue_{i}', 1290, 36, '0xffe0a6', True, enable)}[cap{i}]")
        last = f"cap{i}"
    _run_local([
        executable, "-v", "error", "-nostdin", "-n", "-protocol_whitelist", "file,pipe", "-i", str(input_clip),
        "-filter_complex", ";".join(filters), "-map", f"[{last}]", "-map", "0:a:0",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-t", f"{duration:.3f}", "-movflags", "+faststart", output_path.name,
    ], cwd=directory)


class SpeechHighlightRelayPipeline:
    """Explicit local replay only. No scheduler, store, publisher, provider or discovery owner."""

    def __init__(self, source_config: Path | str | dict[str, Any], repo_root: Path | None = None) -> None:
        self.root = (repo_root or Path.cwd()).resolve()
        self.packet = (copy.deepcopy(source_config) if isinstance(source_config, dict)
                       else json.loads(Path(source_config).read_text(encoding="utf-8")))

    def validate_source_packet(self) -> dict[str, Any]:
        try:
            return validate_packet(self.packet, self.root)
        except (KeyError, TypeError, ValueError) as exc:
            raise SpeechRelayError(f"Malformed retained packet: {exc}") from exc

    def render_package(self, output_dir: Path) -> dict[str, Any]:
        verification = self.validate_source_packet()
        target = output_dir.resolve()
        if not target.is_relative_to(self.root / ".task-runtime" / "speech_highlight_relay_v1"):
            raise SpeechRelayError("Relay outputs must remain in its isolated .task-runtime/speech_highlight_relay_v1 directory")
        if target.exists():
            raise SpeechRelayError("Use a new output directory; existing review artifacts are preserved")
        target.mkdir(parents=True)
        duration = verification["clip_duration_seconds"]
        selection = self.packet["selection"]
        source_media = _local_artifact(self.root, self.packet["media"])
        clip = target / "extracted_clip.mp4"
        if selection["start_seconds"] == 0 and selection["end_seconds"] == self.packet["media"]["duration_seconds"]:
            shutil.copyfile(source_media, clip)
            extraction = "RETAINED_EXCERPT_BYTE_COPY_NO_EXTRA_CUT"
        else:
            DynamicMediaClipper.extract_clip(source_media, selection["start_seconds"], duration, clip)
            extraction = "LOCAL_FFMPEG_SPAN_EXTRACTION"
        cues = [CaptionCue(**raw) for raw in verification["relative_cues"]]
        (target / ARTIFACT_FILES["captions_srt"]).write_text(generate_srt(cues), encoding="utf-8")
        (target / ARTIFACT_FILES["captions_vtt"]).write_text(generate_vtt(cues), encoding="utf-8")
        write_json(target / ARTIFACT_FILES["captions_json"], [asdict(c) for c in cues])
        for key, captions in (("clean_master", None), ("captioned_derivative", cues)):
            _render_vertical(clip, target / ARTIFACT_FILES[key], self.packet, duration, captions)
        write_json(target / "source_packet.json", self.packet)
        write_json(target / "source_verification.json", verification)
        write_json(target / "rights_triage_manifest.json", self.packet["rights"])
        write_json(target / "transcript_alignment_manifest.json", {
            **self.packet["transcript"], "cues": [asdict(c) for c in cues],
            "exact_quote": selection["exact_quote"], "text_match_is_audio_verification": False,
        })
        write_json(target / "highlight_selection_manifest.json", selection)
        probes = {key: probe_media(target / ARTIFACT_FILES[key]) for key in ("clean_master", "captioned_derivative")}
        for probe in probes.values():
            _check_media(probe, duration, vertical=True)
        write_json(target / "render_receipt.json", {
            "created_at": datetime.now(timezone.utc).isoformat(), "media_probes": probes,
            "extracted_clip": artifact_identity(clip), "extraction_method": extraction,
            "audio_path": "ORIGINAL_SOURCE_AUDIO_NO_SYNTHESIS",
            "visual_review": "REQUIRES_ACTUAL_ARTIFACT_INSPECTION", "audio_listening_status": "NOT_VERIFIED",
            "production_eligible": False, "publication_control": PUBLICATION_CONTROL,
        })
        compose_private_review_packet(target, self.root)
        manifest = {
            "schema": PACKAGE_SCHEMA, "source_binding_sha256": verification["source_binding_sha256"],
            "package_id": f"{self.packet['source_id']}:{selection['candidate_id']}",
            "publication_control": PUBLICATION_CONTROL, "production_eligible": False,
            "artifacts": {key: artifact_identity(target / filename) for key, filename in ARTIFACT_FILES.items()},
            "manifest_hashes": {
                name: sha256_file(target / name)
                for name in sorted(MANIFEST_FILES | {PRIVATE_REVIEW_PACKET_FILE})
            },
        }
        write_json(target / "package_manifest.json", manifest)
        return {"package_dir": str(target), **verify_speech_highlight_relay_package(target, self.root)}


def verify_speech_highlight_relay_package(package_dir: Path, repo_root: Path | None = None) -> dict[str, Any]:
    directory = package_dir.resolve()
    manifest = json.loads((directory / "package_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema") != PACKAGE_SCHEMA:
        raise SpeechRelayError("Unsupported package schema")
    if (canonical_json(manifest.get("publication_control")) != canonical_json(PUBLICATION_CONTROL)
            or manifest.get("production_eligible") is not False):
        raise PublicWriteProhibitedError("Package must preserve exact private-review / zero-write controls")
    if set(manifest.get("artifacts", {})) != set(ARTIFACT_FILES):
        raise SpeechRelayError("Package must declare exactly the expected artifacts")
    if set(manifest.get("manifest_hashes", {})) != MANIFEST_FILES | {PRIVATE_REVIEW_PACKET_FILE}:
        raise SpeechRelayError("Package must bind every required manifest")
    for name, expected in manifest["manifest_hashes"].items():
        if sha256_file(directory / name) != expected:
            raise SpeechRelayError(f"Manifest byte hash mismatch: {name}")
    for key, filename in ARTIFACT_FILES.items():
        if manifest["artifacts"][key] != artifact_identity(directory / filename):
            raise SpeechRelayError(f"Artifact identity mismatch: {key}")
    packet = json.loads((directory / "source_packet.json").read_text(encoding="utf-8"))
    checked = validate_packet(packet, (repo_root or Path.cwd()).resolve())
    if checked != json.loads((directory / "source_verification.json").read_text(encoding="utf-8")):
        raise SpeechRelayError("Source verification no longer agrees with retained input bytes")
    if manifest["source_binding_sha256"] != checked["source_binding_sha256"]:
        raise SpeechRelayError("Package source scope mismatch")
    verify_private_review_packet(directory, (repo_root or Path.cwd()).resolve())
    cues = [CaptionCue(**raw) for raw in checked["relative_cues"]]
    related = {
        "rights_triage_manifest.json": packet["rights"],
        "highlight_selection_manifest.json": packet["selection"],
        "transcript_alignment_manifest.json": {
            **packet["transcript"], "cues": [asdict(c) for c in cues],
            "exact_quote": packet["selection"]["exact_quote"], "text_match_is_audio_verification": False,
        },
    }
    for filename, expected_content in related.items():
        if json.loads((directory / filename).read_text(encoding="utf-8")) != expected_content:
            raise SpeechRelayError(f"Manifest content differs from the frozen input: {filename}")
    if (directory / "captions.srt").read_text(encoding="utf-8") != generate_srt(cues):
        raise SpeechRelayError("SRT differs from the frozen quote/timing")
    if (directory / "captions.vtt").read_text(encoding="utf-8") != generate_vtt(cues):
        raise SpeechRelayError("VTT differs from the frozen quote/timing")
    if json.loads((directory / "captions.json").read_text(encoding="utf-8")) != checked["relative_cues"]:
        raise SpeechRelayError("Caption JSON differs from the frozen quote/timing")
    receipt = json.loads((directory / "render_receipt.json").read_text(encoding="utf-8"))
    if (canonical_json(receipt.get("publication_control")) != canonical_json(PUBLICATION_CONTROL)
            or receipt.get("production_eligible") is not False or receipt.get("audio_listening_status") != "NOT_VERIFIED"):
        raise SpeechRelayError("Render receipt overstates permission or listening evidence")
    if receipt.get("extracted_clip") != artifact_identity(directory / "extracted_clip.mp4"):
        raise SpeechRelayError("Extracted clip no longer matches its receipt")
    for key in ("clean_master", "captioned_derivative"):
        probe = probe_media(directory / ARTIFACT_FILES[key])
        _check_media(probe, checked["clip_duration_seconds"], vertical=True)
        if receipt["media_probes"][key] != probe:
            raise SpeechRelayError("Rendered probe differs from its receipt")
    return {
        "status": "PASS_INTEGRITY_AND_FORMAT_PRIVATE_REVIEW_ONLY", "package_id": manifest["package_id"],
        "duration_seconds": checked["clip_duration_seconds"], "publication_state": "PUBLICATION_HOLD",
        "public_writes": 0, "unknown_writes": 0, "provider_calls": 0,
        "audio_listening_status": "NOT_VERIFIED", "caption_timing_status": packet["transcript"]["timing_status"],
        "legal_clearance_status": "NOT_VERIFIED", "production_eligible": False,
    }


def speech_highlight_relay_command(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local retained-source speech replay; PRIVATE REVIEW / PUBLICATION_HOLD")
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--source-config", type=Path, help="Explicit frozen retained-source packet; no discovery default")
    inputs.add_argument("--verify-only", type=Path, help="Verify an existing local package and its retained inputs")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.verify_only:
            result = verify_speech_highlight_relay_package(args.verify_only, args.repo_root)
        else:
            if not args.output_dir:
                parser.error("--output-dir must name a new local review directory")
            result = SpeechHighlightRelayPipeline(args.source_config, args.repo_root).render_package(args.output_dir)
        print(json.dumps(result, indent=2))
        return 0
    except (SpeechRelayError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "FAIL_LOCAL_RELAY", "error": str(exc), "publication_state": "PUBLICATION_HOLD"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(speech_highlight_relay_command())
