from __future__ import annotations

import json
import math
import re
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


SOURCE_FILES = frozenset({"src/index.tsx", "src/Root.tsx", "src/Short.tsx"})
FORBIDDEN_SOURCE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bprocess\s*\.\s*env\b", "env_read"),
    (r"\bimport\s*\(\s*[^'\"]", "dynamic_import"),
    (r"\brequire\s*\(", "commonjs_require"),
    (r"\bfetch\s*\(", "network_fetch"),
    (r"\bXMLHttpRequest\b", "network_xhr"),
    (r"\bWebSocket\b", "network_websocket"),
    (r"\bchild_process\b", "child_process"),
    (r"\bnode:fs\b|\bfrom\s+['\"]fs['\"]", "filesystem"),
    (r"\bnode:os\b|\bfrom\s+['\"]os['\"]", "os_access"),
    (r"\bnode:path\b|\bfrom\s+['\"]path['\"]", "path_access"),
    (r"\bexec(?:File|Sync)?\s*\(|\bspawn(?:Sync)?\s*\(", "shell_execution"),
    (r"https?://", "render_time_network_literal"),
    (r"\bnpm\b|\byarn\b|\bpnpm\b", "package_install"),
    (r"\bselenium\b|\bplaywright\b|\bpuppeteer\b", "browser_access"),
    (r"\btiktok\b|\byoutube\b|\binstagram\b|\bfacebook\b", "platform_operation"),
)
ALLOWED_IMPORTS = frozenset({"react", "remotion"})
SHORT_FPS = 30
SHORT_MAX_SECONDS = 60.0
MINIMUM_PICTURE_TAIL_ROOM_SECONDS = 0.15
ACTUAL_MEDIA_REVIEW_CHECKS = frozenset(
    {
        "real_contextual_material_density",
        "exact_or_near_asset_reuse",
        "visual_family_and_layout_repetition",
        "phone_readability",
        "chart_document_stability",
        "captions_hidden_comprehension",
        "stronger_concrete_media_replacement_opportunity",
    }
)


class CreativeContractError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def hash_value(value: Any) -> str:
    if isinstance(value, bytes):
        return sha256(value).hexdigest()
    if isinstance(value, str):
        return sha256(value.encode("utf-8")).hexdigest()
    return sha256(canonical_bytes(value)).hexdigest()


def hash_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json_text(raw: str) -> Any:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def _anchor_map(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(item["anchor_id"]): item for item in packet.get("anchors", [])}


def _analysis_map(packet: Mapping[str, Any]) -> dict[str, str]:
    return {
        str(item["analysis_id"]): str(item["statement"])
        for item in packet.get("permitted_analysis", [])
    }


def validate_input_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    required = {
        "schema",
        "story_id",
        "authority_version",
        "anchors",
        "permitted_analysis",
        "forbidden_claims",
        "rights_assets",
        "hard_boundaries",
    }
    missing = sorted(required - set(packet))
    if missing:
        raise CreativeContractError(f"input_packet_missing:{','.join(missing)}")
    boundaries = packet["hard_boundaries"]
    for key in (
        "public_write_authority",
        "v1_read_authority",
        "v1_mutation_authority",
        "scheduler_mutation_authority",
    ):
        if boundaries.get(key) is not False:
            raise CreativeContractError(f"hard_boundary_must_be_false:{key}")
    anchors = _anchor_map(packet)
    if not anchors or len(anchors) != len(packet["anchors"]):
        raise CreativeContractError("anchor_identity_invalid")
    for anchor_id, anchor in anchors.items():
        if not anchor.get("statement") or not anchor.get("source_ref"):
            raise CreativeContractError(f"anchor_incomplete:{anchor_id}")
    for asset in packet["rights_assets"]:
        if not re.fullmatch(r"[0-9a-f]{64}", str(asset.get("sha256", ""))):
            raise CreativeContractError(f"asset_hash_invalid:{asset.get('asset_id')}")
        path = PurePosixPath(str(asset.get("relative_path", "")))
        if path.is_absolute() or ".." in path.parts:
            raise CreativeContractError(f"asset_path_invalid:{asset.get('asset_id')}")
    pronunciation_lexicon = packet.get("pronunciation_lexicon", [])
    if not isinstance(pronunciation_lexicon, list):
        raise CreativeContractError("pronunciation_lexicon_not_list")
    seen_pronunciations: set[tuple[str, str]] = set()
    for item in pronunciation_lexicon:
        if not isinstance(item, Mapping):
            raise CreativeContractError("pronunciation_lexicon_entry_not_object")
        surface = str(item.get("surface", "")).strip()
        spoken_as = str(item.get("spoken_as", "")).strip()
        pair = (surface, spoken_as)
        if not surface or not spoken_as or pair in seen_pronunciations:
            raise CreativeContractError("pronunciation_lexicon_entry_invalid")
        seen_pronunciations.add(pair)
    return {
        "result": "PASS_GOVERNED_INPUT",
        "anchor_count": len(anchors),
        "asset_count": len(packet["rights_assets"]),
        "input_packet_hash": hash_value(packet),
    }


def validate_editor_artifact(
    artifact: Mapping[str, Any], packet: Mapping[str, Any]
) -> dict[str, Any]:
    if artifact.get("schema") != "contentops.v2.codex_job_editorial.v3":
        raise CreativeContractError("editor_schema_invalid")
    if "duration_seconds" in artifact or "shots" in artifact:
        raise CreativeContractError("editor_cannot_lock_motion_timing")
    anchors = _anchor_map(packet)
    analysis = _analysis_map(packet)
    segments = artifact.get("narration_segments")
    if not isinstance(segments, list) or not segments:
        raise CreativeContractError("editor_narration_segments_invalid")
    seen: set[str] = set()
    fact_count = 0
    for segment in segments:
        segment_id = str(segment.get("segment_id", ""))
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", segment_id) or segment_id in seen:
            raise CreativeContractError("editor_segment_identity_invalid")
        seen.add(segment_id)
        kind = str(segment.get("kind", ""))
        text = str(segment.get("text", "")).strip()
        anchor_ids = [str(value) for value in segment.get("anchor_ids", [])]
        analysis_id = str(segment.get("analysis_id", ""))
        if not text:
            raise CreativeContractError(f"editor_empty_segment:{segment_id}")
        if kind == "FACT":
            fact_count += 1
            if len(anchor_ids) != 1 or anchor_ids[0] not in anchors:
                raise CreativeContractError(f"editor_fact_binding_invalid:{segment_id}")
            if text != str(anchors[anchor_ids[0]]["statement"]):
                raise CreativeContractError(f"editor_fact_not_exact_anchor:{segment_id}")
        elif kind == "ANALYSIS":
            if anchor_ids or analysis.get(analysis_id) != text:
                raise CreativeContractError(f"editor_analysis_not_authorized:{segment_id}")
        elif kind == "ENGAGEMENT":
            if anchor_ids or analysis_id or re.search(r"\d", text):
                raise CreativeContractError(f"editor_engagement_claim_like:{segment_id}")
            if len(text.split()) > 24:
                raise CreativeContractError(f"editor_engagement_too_long:{segment_id}")
        else:
            raise CreativeContractError(f"editor_segment_kind_invalid:{segment_id}")
    forbidden = [str(item).lower() for item in packet.get("forbidden_claims", [])]
    full_text = " ".join(str(item.get("text", "")) for item in segments).lower()
    for phrase in forbidden:
        if phrase and phrase in full_text:
            raise CreativeContractError("editor_forbidden_claim_present")
    from .transcript import TranscriptContractError, validate_editor_transcript_fields

    try:
        transcript_fields = validate_editor_transcript_fields(artifact)
    except TranscriptContractError as exc:
        raise CreativeContractError(str(exc)) from exc
    allowed_pronunciations = {
        (str(item["surface"]), str(item["spoken_as"]))
        for item in packet.get("pronunciation_lexicon", [])
    }
    for segment in segments:
        for note in segment.get("pronunciation_notes", []):
            if (str(note["surface"]), str(note["spoken_as"])) not in allowed_pronunciations:
                raise CreativeContractError(
                    f"pronunciation_not_governed:{segment['segment_id']}"
                )
    return {
        "result": "PASS_FACTUAL_ANCHORS",
        "fact_segment_count": fact_count,
        "narration_segment_count": len(segments),
        "word_count_estimate_only": sum(
            len(str(item["text"]).split()) for item in segments
        ),
        "timing_authority": "ACTUAL_KOKORO_WAVEFORM_ONLY",
        "transcript_fields": transcript_fields,
    }


def validate_narration_timing_lock(
    artifact: Mapping[str, Any],
    *,
    video_job_id: str,
    run_id: str,
    governed_input_hash: str,
    editor: Mapping[str, Any],
) -> dict[str, Any]:
    if artifact.get("schema") != "contentops.v2.actual_narration_timing_lock.v2":
        raise CreativeContractError("narration_timing_lock_schema_invalid")
    expected_identity = {
        "video_job_id": video_job_id,
        "run_id": run_id,
        "governed_input_hash": governed_input_hash,
        "editorial_narration_hash": hash_value(editor),
    }
    for key, value in expected_identity.items():
        if artifact.get(key) != value:
            raise CreativeContractError(f"narration_timing_lock_identity_mismatch:{key}")
    if (
        artifact.get("provider"),
        artifact.get("model"),
        artifact.get("voice"),
        round(float(artifact.get("speed", 0)), 2),
        artifact.get("lang"),
        int(artifact.get("sample_rate_hz", 0)),
    ) != ("kokoro-onnx", "kokoro-v1.0", "af_heart", 1.06, "en-us", 24_000):
        raise CreativeContractError("narration_timing_lock_voice_route_mismatch")
    segments = artifact.get("segments")
    if not isinstance(segments, list) or len(segments) != len(editor["narration_segments"]):
        raise CreativeContractError("narration_timing_lock_segment_count_mismatch")
    cursor = float(artifact.get("initial_silence_seconds", -1))
    if cursor < 0:
        raise CreativeContractError("narration_timing_lock_initial_silence_invalid")
    for locked, authored in zip(segments, editor["narration_segments"]):
        segment_id = str(authored["segment_id"])
        text = str(authored["text"])
        if locked.get("segment_id") != segment_id:
            raise CreativeContractError("narration_timing_lock_segment_identity_mismatch")
        if locked.get("segment_text_sha256") != hash_value(text):
            raise CreativeContractError(f"narration_timing_lock_text_hash_mismatch:{segment_id}")
        audio = locked.get("audio") or {}
        audio_path = Path(str(audio.get("path", "")))
        if not audio_path.is_file() or hash_file(audio_path) != str(audio.get("sha256", "")):
            raise CreativeContractError(f"narration_timing_lock_audio_hash_mismatch:{segment_id}")
        start = float(locked.get("timeline_start_seconds", -1))
        duration = float(locked.get("actual_audio_duration_seconds", 0))
        end = float(locked.get("timeline_end_seconds", -1))
        pause = float(locked.get("pause_after_seconds", -1))
        if abs(start - cursor) > 0.00001 or duration <= 0 or pause < 0:
            raise CreativeContractError(f"narration_timing_lock_placement_invalid:{segment_id}")
        if abs(end - (start + duration)) > 0.00001:
            raise CreativeContractError(f"narration_timing_lock_end_invalid:{segment_id}")
        cursor = end + pause
    total = float(artifact.get("actual_total_narration_duration_seconds", 0))
    if abs(cursor - total) > 0.00001:
        raise CreativeContractError("narration_timing_lock_total_mismatch")
    narration = artifact.get("locked_narration_audio") or {}
    narration_path = Path(str(narration.get("path", "")))
    if not narration_path.is_file() or hash_file(narration_path) != str(
        narration.get("sha256", "")
    ):
        raise CreativeContractError("narration_timing_lock_composite_hash_mismatch")
    if total + MINIMUM_PICTURE_TAIL_ROOM_SECONDS > SHORT_MAX_SECONDS + 0.00001:
        raise CreativeContractError("narration_timing_lock_outside_short_contract")
    from .transcript import (
        TranscriptContractError,
        build_voiceover_qa,
        validate_canonical_spoken_transcript,
    )

    transcript = artifact.get("canonical_spoken_transcript")
    if not isinstance(transcript, Mapping):
        raise CreativeContractError("canonical_spoken_transcript_missing")
    try:
        transcript_validation = validate_canonical_spoken_transcript(
            transcript,
            video_job_id=video_job_id,
            run_id=run_id,
            governed_input_hash=governed_input_hash,
            editor=editor,
            locked_narration_audio=narration,
        )
        expected_voiceover_qa = build_voiceover_qa(transcript=transcript, editor=editor)
    except TranscriptContractError as exc:
        raise CreativeContractError(str(exc)) from exc
    if artifact.get("voiceover_qa") != expected_voiceover_qa:
        raise CreativeContractError("narration_timing_lock_voiceover_qa_mismatch")
    for canonical_segment, placement in zip(transcript["segments"], segments):
        for key in (
            "segment_id",
            "segment_text_sha256",
            "synthesis_text_sha256",
            "timeline_start_seconds",
            "actual_audio_duration_seconds",
            "timeline_end_seconds",
            "pause_after_seconds",
            "audio_path",
            "audio",
            "synthesis_action",
        ):
            if canonical_segment.get(key) != placement.get(key):
                raise CreativeContractError(
                    f"canonical_transcript_placement_mismatch:{key}"
                )
    lock_payload = dict(artifact)
    observed_hash = str(lock_payload.pop("timing_lock_hash", ""))
    if not observed_hash or hash_value(lock_payload) != observed_hash:
        raise CreativeContractError("narration_timing_lock_hash_mismatch")
    return {
        "result": "PASS_ACTUAL_NARRATION_TIMING_LOCK",
        "timing_lock_hash": observed_hash,
        "actual_total_narration_duration_seconds": total,
        "segment_count": len(segments),
        "canonical_transcript_hash": transcript_validation[
            "canonical_transcript_hash"
        ],
        "voiceover_qa_hash": expected_voiceover_qa["voiceover_qa_hash"],
    }


def validate_post_transcript_asset_selection(
    selection: Mapping[str, Any],
    packet: Mapping[str, Any],
    editor: Mapping[str, Any],
    timing_lock: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the immutable asset board selected after narration is waveform-locked."""
    if selection.get("schema") != "contentops.v2.post_transcript_asset_selection.v1":
        raise CreativeContractError("asset_selection_schema_invalid")
    transcript = timing_lock.get("canonical_spoken_transcript") or {}
    expected_identity = {
        "governed_input_hash": timing_lock.get("governed_input_hash"),
        "editorial_narration_hash": timing_lock.get("editorial_narration_hash"),
        "narration_timing_lock_hash": timing_lock.get("timing_lock_hash"),
        "canonical_transcript_hash": transcript.get("canonical_transcript_hash"),
    }
    for key, value in expected_identity.items():
        if selection.get(key) != value:
            raise CreativeContractError(f"asset_selection_identity_mismatch:{key}")
    if selection.get("prior_creative_source_reused_as_input") is not False:
        raise CreativeContractError("asset_selection_prior_creative_source_forbidden")
    if selection.get("fresh_web_discovery_performed") is not True:
        raise CreativeContractError("asset_selection_fresh_discovery_required")

    transcript_segment_ids = {
        str(item["segment_id"]) for item in transcript.get("segments", [])
    }
    editor_segment_ids = {
        str(item["segment_id"]) for item in editor.get("narration_segments", [])
    }
    if not transcript_segment_ids or transcript_segment_ids != editor_segment_ids:
        raise CreativeContractError("asset_selection_transcript_segment_identity_invalid")
    visual_needs = selection.get("visual_needs")
    if not isinstance(visual_needs, list) or not visual_needs:
        raise CreativeContractError("asset_selection_visual_needs_missing")
    need_ids: set[str] = set()
    for need in visual_needs:
        need_id = str(need.get("need_id", ""))
        segment_ids = set(map(str, need.get("transcript_segment_ids", [])))
        if (
            not re.fullmatch(r"[A-Za-z0-9_.-]+", need_id)
            or need_id in need_ids
            or not str(need.get("visual_purpose", "")).strip()
            or not segment_ids
            or not segment_ids.issubset(transcript_segment_ids)
        ):
            raise CreativeContractError("asset_selection_visual_need_invalid")
        need_ids.add(need_id)

    governed_assets = {
        str(item["asset_id"]): item for item in packet.get("rights_assets", [])
    }
    selected_existing = list(map(str, selection.get("selected_existing_asset_ids", [])))
    if len(selected_existing) != len(set(selected_existing)) or not set(
        selected_existing
    ).issubset(governed_assets):
        raise CreativeContractError("asset_selection_existing_asset_invalid")

    selected_assets = selection.get("selected_assets")
    if not isinstance(selected_assets, list):
        raise CreativeContractError("asset_selection_selected_assets_not_list")
    new_assets: dict[str, Mapping[str, Any]] = {}
    new_paths: set[str] = set()
    for asset in selected_assets:
        asset_id = str(asset.get("asset_id", ""))
        relative_path = str(asset.get("relative_path", ""))
        path = PurePosixPath(relative_path)
        required_text = (
            "source_url",
            "rights_basis",
            "visual_family",
            "semantic_purpose",
        )
        if (
            not re.fullmatch(r"[A-Za-z0-9_.-]+", asset_id)
            or asset_id in governed_assets
            or asset_id in new_assets
            or path.is_absolute()
            or ".." in path.parts
            or not relative_path
            or relative_path in new_paths
            or not re.fullmatch(r"[0-9a-f]{64}", str(asset.get("sha256", "")))
            or any(not str(asset.get(key, "")).strip() for key in required_text)
        ):
            raise CreativeContractError(f"asset_selection_new_asset_invalid:{asset_id}")
        new_assets[asset_id] = asset
        new_paths.add(relative_path)

    selected_ids = set(selected_existing) | set(new_assets)
    if not selected_ids:
        raise CreativeContractError("asset_selection_requires_selected_asset")
    board = selection.get("candidate_board")
    if not isinstance(board, list) or not board:
        raise CreativeContractError("asset_selection_candidate_board_missing")
    candidate_ids: set[str] = set()
    candidate_need_ids: set[str] = set()
    board_selected_ids: set[str] = set()
    for candidate in board:
        candidate_id = str(candidate.get("candidate_id", ""))
        need_id = str(candidate.get("need_id", ""))
        source_url = str(candidate.get("source_url", ""))
        selected_asset_id = str(candidate.get("selected_asset_id", ""))
        if (
            not re.fullmatch(r"[A-Za-z0-9_.-]+", candidate_id)
            or candidate_id in candidate_ids
            or need_id not in need_ids
            or not re.fullmatch(r"https://[^\s]+", source_url)
            or not str(candidate.get("rights_basis", "")).strip()
            or not str(candidate.get("visual_fit_assessment", "")).strip()
        ):
            raise CreativeContractError("asset_selection_candidate_invalid")
        candidate_ids.add(candidate_id)
        candidate_need_ids.add(need_id)
        if selected_asset_id:
            if selected_asset_id not in selected_ids or selected_asset_id in board_selected_ids:
                raise CreativeContractError("asset_selection_candidate_selected_id_invalid")
            if selected_asset_id in new_assets and source_url != str(
                new_assets[selected_asset_id]["source_url"]
            ):
                raise CreativeContractError("asset_selection_candidate_source_mismatch")
            board_selected_ids.add(selected_asset_id)
        elif not str(candidate.get("rejection_reason", "")).strip():
            raise CreativeContractError("asset_selection_rejection_reason_required")
    if board_selected_ids != selected_ids:
        raise CreativeContractError("asset_selection_board_does_not_cover_selection")
    if candidate_need_ids != need_ids:
        raise CreativeContractError("asset_selection_board_does_not_cover_visual_needs")

    observed_hash = str(selection.get("asset_selection_hash", ""))
    hash_basis = dict(selection)
    hash_basis.pop("asset_selection_hash", None)
    if observed_hash != hash_value(hash_basis):
        raise CreativeContractError("asset_selection_hash_mismatch")
    return {
        "result": "PASS_POST_TRANSCRIPT_ASSET_SELECTION",
        "asset_selection_hash": observed_hash,
        "visual_need_count": len(visual_needs),
        "candidate_count": len(board),
        "selected_existing_asset_count": len(selected_existing),
        "selected_new_asset_count": len(new_assets),
    }


def governed_assets_for_motion(
    packet: Mapping[str, Any], motion: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Return the governed base assets plus immutable post-transcript additions."""
    combined = [dict(item) for item in packet.get("rights_assets", [])]
    selection = motion.get("asset_selection") or {}
    combined.extend(dict(item) for item in selection.get("selected_assets", []))
    return combined


def validate_motion_artifact(
    artifact: Mapping[str, Any],
    packet: Mapping[str, Any],
    editor: Mapping[str, Any],
    timing_lock: Mapping[str, Any],
) -> dict[str, Any]:
    if artifact.get("schema") != "contentops.v2.codex_job_motion_source.v1":
        raise CreativeContractError("motion_schema_invalid")
    if artifact.get("composition_id") != "ContentOpsV2Short":
        raise CreativeContractError("motion_composition_id_invalid")
    if artifact.get("narration_timing_lock_hash") != timing_lock.get("timing_lock_hash"):
        raise CreativeContractError("motion_narration_timing_lock_mismatch")
    selection = artifact.get("asset_selection")
    if not isinstance(selection, Mapping):
        raise CreativeContractError("motion_post_transcript_asset_selection_missing")
    asset_validation = validate_post_transcript_asset_selection(
        selection, packet, editor, timing_lock
    )
    picture_timing = artifact.get("picture_timing")
    if not isinstance(picture_timing, Mapping):
        raise CreativeContractError("motion_picture_timing_missing")
    fps = int(picture_timing.get("fps", 0))
    head_room = float(picture_timing.get("authored_head_room_seconds", -1))
    tail_room = float(picture_timing.get("authored_tail_room_seconds", -1))
    frames = int(picture_timing.get("duration_frames", 0))
    actual = float(timing_lock["actual_total_narration_duration_seconds"])
    if fps != SHORT_FPS or abs(head_room - float(timing_lock["initial_silence_seconds"])) > 0.00001:
        raise CreativeContractError("motion_picture_timing_basis_invalid")
    if tail_room < MINIMUM_PICTURE_TAIL_ROOM_SECONDS:
        raise CreativeContractError("motion_picture_tail_room_too_short")
    expected_frames = math.ceil((actual + tail_room) * fps - 0.0000001)
    duration = frames / fps
    if frames != expected_frames or not 30 <= duration <= SHORT_MAX_SECONDS:
        raise CreativeContractError("motion_picture_duration_not_waveform_derived")
    if abs(float(artifact.get("duration_seconds", 0)) - duration) > 0.00001:
        raise CreativeContractError("motion_duration_not_frame_locked")
    files = artifact.get("files")
    if not isinstance(files, Mapping) or set(files) != SOURCE_FILES:
        raise CreativeContractError("motion_source_file_set_invalid")
    if not all(isinstance(value, str) and value.strip() for value in files.values()):
        raise CreativeContractError("motion_source_file_empty")
    editor_segments = {
        str(item["segment_id"]): str(item["text"])
        for item in editor["narration_segments"]
    }
    bindings = artifact.get("source_claim_bindings")
    if not isinstance(bindings, list):
        raise CreativeContractError("motion_claim_bindings_missing")
    bound_display_text: set[str] = set()
    for binding in bindings:
        segment_id = str(binding.get("segment_id", ""))
        display_text = str(binding.get("text", ""))
        if not display_text or display_text not in editor_segments.get(segment_id, ""):
            raise CreativeContractError("motion_claim_not_bound_to_editor")
        bound_display_text.add(display_text)
    combined_assets = governed_assets_for_motion(packet, artifact)
    selected_assets = set(map(str, selection.get("selected_existing_asset_ids", []))) | {
        str(item["asset_id"]) for item in selection.get("selected_assets", [])
    }
    valid_assets = {str(item["asset_id"]) for item in combined_assets}
    if not set(map(str, artifact.get("asset_ids", []))).issubset(valid_assets):
        raise CreativeContractError("motion_asset_not_governed")
    if not set(map(str, artifact.get("asset_ids", []))).issubset(selected_assets):
        raise CreativeContractError("motion_asset_not_post_transcript_selected")
    source = "\n".join(str(value) for value in files.values())
    root_source = str(files["src/Root.tsx"])
    if not re.search(rf"durationInFrames=\{{{frames}\}}", root_source):
        raise CreativeContractError("motion_source_duration_frames_mismatch")
    if not re.search(r"fps=\{30\}", root_source):
        raise CreativeContractError("motion_source_fps_mismatch")
    for display_text in bound_display_text:
        if display_text not in source:
            raise CreativeContractError("motion_bound_claim_missing_from_source")
    allowed_paths = {
        str(item["relative_path"]): str(item["asset_id"])
        for item in combined_assets
    }
    referenced_paths = set(
        re.findall(r"staticFile\(\s*['\"]([^'\"]+)['\"]\s*\)", source)
    )
    if not referenced_paths or not referenced_paths.issubset(allowed_paths):
        raise CreativeContractError("motion_static_asset_binding_invalid")
    expected_asset_ids = {allowed_paths[path] for path in referenced_paths}
    if expected_asset_ids != set(map(str, artifact.get("asset_ids", []))):
        raise CreativeContractError("motion_asset_ids_do_not_match_source")
    allowed_numeric_strings = (
        set(bound_display_text)
        | referenced_paths
        | {str(artifact["composition_id"])}
    )
    literals = []
    for match in re.finditer(
        r"'((?:\\.|[^'\\\r\n])*)'|\"((?:\\.|[^\"\\\r\n])*)\"",
        source,
    ):
        literals.append(match.group(1) if match.group(1) is not None else match.group(2))
    for literal in (value for value in literals if re.search(r"\d", value)):
        if re.fullmatch(r"#[0-9A-Fa-f]{3,8}", literal):
            continue
        if literal not in allowed_numeric_strings:
            raise CreativeContractError(f"motion_unbound_numeric_string:{literal[:80]}")
    sandbox = validate_source_files(files)
    return {
        "result": "PASS_MOTION_SOURCE_CONTRACT",
        "source_file_count": len(files),
        "claim_binding_count": len(bindings),
        "duration_frames": frames,
        "duration_seconds": duration,
        "timing_lock_hash": timing_lock["timing_lock_hash"],
        "asset_selection_hash": asset_validation["asset_selection_hash"],
        "sandbox": sandbox,
    }


def validate_revision_artifact(
    artifact: Mapping[str, Any],
    packet: Mapping[str, Any],
    editor: Mapping[str, Any],
    motion: Mapping[str, Any],
    timing_lock: Mapping[str, Any],
) -> dict[str, Any]:
    if artifact.get("schema") != "contentops.v2.codex_actual_media_review.v1":
        raise CreativeContractError("revision_schema_invalid")
    decision = str(artifact.get("decision", ""))
    if decision not in {"NO_MATERIAL_REVISION", "MATERIAL_REVISION_REQUIRED"}:
        raise CreativeContractError("revision_decision_invalid")
    review_checks = artifact.get("review_checks")
    if not isinstance(review_checks, Mapping) or set(review_checks) != ACTUAL_MEDIA_REVIEW_CHECKS:
        raise CreativeContractError("actual_media_review_checks_incomplete")
    if not all(str(value).strip() for value in review_checks.values()):
        raise CreativeContractError("actual_media_review_check_empty")
    files = artifact.get("replacement_files") or {}
    if decision == "MATERIAL_REVISION_REQUIRED":
        if not isinstance(files, Mapping) or set(files) != SOURCE_FILES:
            raise CreativeContractError("revision_replacement_file_set_invalid")
        revised_motion = dict(motion)
        revised_motion["files"] = dict(files)
        revised_motion["source_claim_bindings"] = list(
            artifact.get("source_claim_bindings", [])
        )
        validate_motion_artifact(revised_motion, packet, editor, timing_lock)
    elif files:
        raise CreativeContractError("revision_files_without_material_decision")
    allowed_segments = {
        str(item["segment_id"]): str(item["text"])
        for item in editor["narration_segments"]
    }
    for binding in artifact.get("source_claim_bindings", []):
        display_text = str(binding.get("text", ""))
        if not display_text or display_text not in allowed_segments.get(
            str(binding.get("segment_id", "")), ""
        ):
            raise CreativeContractError("revision_claim_not_bound")
    return {
        "result": "PASS_ACTUAL_MEDIA_REVIEW_CONTRACT",
        "decision": decision,
        "defect_count": len(artifact.get("defects", [])),
    }


def validate_source_files(files: Mapping[str, str]) -> dict[str, Any]:
    violations: list[str] = []
    for relative, source in files.items():
        if relative not in SOURCE_FILES:
            violations.append(f"path:{relative}")
            continue
        for pattern, code in FORBIDDEN_SOURCE_PATTERNS:
            if re.search(pattern, source, flags=re.I | re.M):
                violations.append(f"{relative}:{code}")
        for match in re.finditer(
            r"(?:from\s+|import\s*)['\"]([^'\"]+)['\"]", source
        ):
            imported = match.group(1)
            if not imported.startswith("./") and imported not in ALLOWED_IMPORTS:
                violations.append(f"{relative}:import:{imported}")
    if violations:
        raise CreativeContractError("sandbox_violation:" + ",".join(sorted(set(violations))))
    return {
        "result": "PASS_CREATIVE_CODE_SANDBOX",
        "allowed_imports": sorted(ALLOWED_IMPORTS),
        "source_file_count": len(files),
    }


def materialize_source(files: Mapping[str, str], project_root: Path) -> list[dict[str, Any]]:
    validate_source_files(files)
    artifacts: list[dict[str, Any]] = []
    for relative, source in sorted(files.items()):
        destination = (project_root / PurePosixPath(relative)).resolve()
        if project_root.resolve() not in destination.parents:
            raise CreativeContractError(f"source_destination_escape:{relative}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.rstrip() + "\n", encoding="utf-8")
        artifacts.append(
            {
                "path": str(destination),
                "sha256": hash_file(destination),
                "size_bytes": destination.stat().st_size,
            }
        )
    return artifacts
