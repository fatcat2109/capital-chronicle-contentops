"""Deterministic controls for the V2 breaking-news crisp-master proof.

Creative decisions remain in the story-specific Remotion source.  This module
owns evidence, rights, audio provenance, technical media QA, durable recovery,
and the zero-public-write boundary.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any, Mapping, Sequence


TASK_ID = "TASK_CONTENTOPS_V2_BREAKING_NEWS_OWNER_DEFECT_REPAIR_V2"
BANNED_VOICE_IDS = frozenset({"pNInz6obpgDQGcFmaJgB"})
STAGES = (
    "DISCOVERED", "QUALIFIED", "EVIDENCE_LOCKED", "EDITORIAL_READY",
    "RIGHTS_READY", "DOCUMENT_GEOMETRY_READY", "AUDIO_AUDITION_READY", "AUDIO_READY",
    "STORYBOARD_READY", "PROXY_READY", "MASTER_READY", "OWNER_REVIEW",
)
STAGE_INDEX = {stage: index for index, stage in enumerate(STAGES)}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def logical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


class BreakingNewsLedger:
    """Small restart-safe stage ledger; repeated identical checkpoints reuse."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
              job_id TEXT PRIMARY KEY, state TEXT NOT NULL, updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS stages (
              id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL,
              stage TEXT NOT NULL, input_hash TEXT NOT NULL, output_hash TEXT NOT NULL,
              output_json TEXT NOT NULL, runtime_seconds REAL NOT NULL,
              created_at REAL NOT NULL
            );
            """
        )
        self.db.commit()

    def create(self, job_id: str) -> None:
        self.db.execute("INSERT OR IGNORE INTO jobs VALUES(?,?,?)", (job_id, "DISCOVERED", time.time()))
        self.db.commit()

    def checkpoint(self, job_id: str, stage: str, input_hash: str,
                   output: Mapping[str, Any], runtime_seconds: float = 0, *, allow_rework: bool = False) -> dict[str, Any]:
        if stage not in STAGE_INDEX:
            raise ValueError(f"unknown_stage:{stage}")
        current = self.db.execute("SELECT state FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if current is None:
            raise KeyError(job_id)
        output_hash = logical_hash(output)
        row = self.db.execute(
            "SELECT id FROM stages WHERE job_id=? AND stage=? AND input_hash=? AND output_hash=?",
            (job_id, stage, input_hash, output_hash),
        ).fetchone()
        if row:
            return {"status": "REUSED", "id": int(row["id"])}
        is_rework = STAGE_INDEX[stage] < STAGE_INDEX[str(current["state"])]
        if is_rework and not allow_rework:
            raise ValueError(f"stage_regression:{current['state']}->{stage}")
        now = time.time()
        cursor = self.db.execute(
            "INSERT INTO stages(job_id,stage,input_hash,output_hash,output_json,runtime_seconds,created_at) VALUES(?,?,?,?,?,?,?)",
            (job_id, stage, input_hash, output_hash, canonical_json(output), runtime_seconds, now),
        )
        next_state = str(current["state"]) if is_rework else stage
        self.db.execute("UPDATE jobs SET state=?,updated_at=? WHERE job_id=?", (next_state, now, job_id))
        self.db.commit()
        return {"status": "WRITTEN", "id": int(cursor.lastrowid)}

    def rows(self, job_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.db.execute("SELECT * FROM stages WHERE job_id=? ORDER BY id", (job_id,))]

    def close(self) -> None:
        self.db.close()


def validate_breaking_event(event: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for key in ("event_id", "published_at", "primary_source_url", "observed_at", "concrete_change"):
        if not event.get(key):
            errors.append(f"missing_event_field:{key}")
    if event.get("urgency_fabricated") is not False:
        errors.append("urgency_not_grounded")
    if event.get("market_reaction_status") not in {"GOVERNED_EXACT", "OMITTED_NO_GOVERNED_MARKET_DATA"}:
        errors.append("market_reaction_policy_invalid")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def validate_claim_bindings(packet: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    source_ids = {str(row.get("source_id")) for row in packet.get("sources", [])}
    for claim in packet.get("claims", []):
        if claim.get("source_id") not in source_ids:
            errors.append(f"unbound_claim:{claim.get('claim_id')}")
        if claim.get("kind") not in {"OBSERVATION", "DERIVED", "ANALYSIS"}:
            errors.append(f"invalid_claim_kind:{claim.get('claim_id')}")
        if claim.get("kind") == "DERIVED" and not claim.get("derivation"):
            errors.append(f"missing_derivation:{claim.get('claim_id')}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "claim_count": len(packet.get("claims", []))}


def validate_authority_clip(receipt: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    decision = receipt.get("decision")
    if decision not in {"SELECTED", "SKIP_NO_SAFE_HIGH_VALUE_CLIP"}:
        errors.append("invalid_clip_decision")
    if receipt.get("broadcaster_scrape_attempted") is not False:
        errors.append("broadcaster_scrape_forbidden")
    if receipt.get("synthetic_real_official") is not False:
        errors.append("synthetic_real_official_forbidden")
    if decision == "SELECTED":
        for key in ("source_url", "license", "local_path", "sha256", "exact_quote"):
            if not receipt.get(key):
                errors.append(f"missing_clip_rights_field:{key}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def validate_editorial(editorial: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for layer in ("truth", "analysis", "engagement"):
        if not editorial.get("layers", {}).get(layer):
            errors.append(f"missing_layer:{layer}")
    used = [row for row in editorial.get("wit_candidates", []) if row.get("decision") == "ACCEPTED"]
    if len(used) > 2:
        errors.append("too_many_wit_lines")
    for row in used:
        if not all(row.get(key) is True for key in ("fact_safe", "relevant", "market_literate", "non_advice")):
            errors.append(f"unsafe_wit:{row.get('candidate_id')}")
    if editorial.get("format") != "BREAKING_NATIVE":
        errors.append("deep_dive_grammar_forbidden")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "accepted_wit": len(used)}


def validate_audio_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    audition = contract.get("audition", {})
    identity = audition.get("identity_search", {})
    candidates = identity.get("stage_a_candidates", [])
    finalists = identity.get("stage_b_finalists", [])
    if not 6 <= len(candidates) <= 10:
        errors.append("voice_identity_search_not_bounded")
    if not 2 <= len(finalists) <= 3:
        errors.append("voice_finalist_search_not_bounded")
    voice_ids = {str(row.get("voice_id")) for row in [*candidates, *finalists]}
    if BANNED_VOICE_IDS.intersection(voice_ids):
        errors.append("banned_voice_in_search")
    if audition.get("selected_voice_id") in BANNED_VOICE_IDS:
        errors.append("banned_voice_selected")
    if not audition.get("selected_model_id"):
        errors.append("audition_selection_missing")
    if not audition.get("selected_voice_id"):
        errors.append("voice_identity_selection_missing")
    segments = contract.get("segments", [])
    if len(segments) < 6:
        errors.append("semantic_segments_missing")
    for row in segments:
        for key in ("segment_id", "text_sha256", "model_id", "voice_id", "settings", "duration_seconds", "audio_sha256"):
            if row.get(key) in (None, ""):
                errors.append(f"segment_provenance_missing:{row.get('segment_id')}:{key}")
    if contract.get("global_atempo_used") is not False:
        errors.append("global_atempo_forbidden")
    if float(contract.get("maximum_segment_time_correction_percent", 999)) > 3:
        errors.append("segment_time_correction_excessive")
    if contract.get("api_key_serialized") is not False:
        errors.append("api_key_disclosure")
    if contract.get("professional_audio_eligibility") != "ELEVENLABS_API_ELIGIBLE":
        errors.append("professional_audio_not_eligible")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def _rect(value: Sequence[float]) -> tuple[float, float, float, float]:
    if len(value) != 4:
        raise ValueError("bbox_requires_four_coordinates")
    x0, y0, x1, y1 = (float(number) for number in value)
    if x1 <= x0 or y1 <= y0:
        raise ValueError("bbox_has_no_area")
    return x0, y0, x1, y1


def _area(rect: Sequence[float]) -> float:
    x0, y0, x1, y1 = _rect(rect)
    return (x1 - x0) * (y1 - y0)


def _intersection(left: Sequence[float], right: Sequence[float]) -> float:
    lx0, ly0, lx1, ly1 = _rect(left)
    rx0, ry0, rx1, ry1 = _rect(right)
    width = max(0.0, min(lx1, rx1) - max(lx0, rx0))
    height = max(0.0, min(ly1, ry1) - max(ly0, ry0))
    return width * height


def _normalise(rect: Sequence[float], width: float, height: float) -> tuple[float, float, float, float]:
    x0, y0, x1, y1 = _rect(rect)
    return x0 / width, y0 / height, x1 / width, y1 / height


def validate_annotation_geometry(record: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed when a document annotation is not bound to measured text geometry."""

    errors: list[str] = []
    for key in (
        "source_document_sha256", "source_page", "exact_target_text", "document_target_bbox",
        "rendered_target_bbox", "annotation_bbox", "annotation_padding", "transform_identity",
        "settled_frames",
    ):
        if record.get(key) in (None, "", []):
            errors.append(f"missing_geometry_field:{key}")
    if errors:
        return {"status": "FAIL", "errors": errors}

    target = _rect(record["rendered_target_bbox"])
    annotation = _rect(record["annotation_bbox"])
    target_area = _area(target)
    containment = _intersection(target, annotation) / target_area
    if containment < 0.995:
        errors.append(f"target_not_contained:{containment:.6f}")
    overreach = _area(annotation) / target_area
    if overreach > 1.55:
        errors.append(f"annotation_overreach:{overreach:.6f}")

    width, height = (float(value) for value in record.get("frame_size", [0, 0]))
    ax0, ay0, ax1, ay1 = annotation
    if width <= 0 or height <= 0 or ax0 < 0 or ay0 < 0 or ax1 > width or ay1 > height:
        errors.append("annotation_outside_frame")

    for box in record.get("unrelated_glyph_bboxes", []):
        overlap = _intersection(annotation, box["bbox"]) / _area(box["bbox"])
        if overlap > 0.01:
            errors.append(f"annotation_intersects_unrelated_glyphs:{box.get('label')}:{overlap:.6f}")

    frames = record.get("settled_frames", {})
    small = frames.get("1080x1920", {})
    large = frames.get("2160x3840", {})
    if small and large:
        small_norm = _normalise(small["annotation_bbox"], 1080, 1920)
        large_norm = _normalise(large["annotation_bbox"], 2160, 3840)
        if max(abs(a - b) for a, b in zip(small_norm, large_norm)) > 0.002:
            errors.append("annotation_aspect_parity_failed")

    if record.get("transform_identity", {}).get("kind") not in {"IDENTITY", "AFFINE"}:
        errors.append("transform_identity_invalid")
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "target_containment_fraction": containment,
        "annotation_to_target_area_ratio": overreach,
    }


def validate_microbeat_timeline(timeline: Mapping[str, Any]) -> dict[str, Any]:
    """Reject unexplained static holds while leaving editorial beat count unconstrained."""

    errors: list[str] = []
    beats = timeline.get("beats", [])
    if not beats:
        errors.append("microbeats_missing")
    previous_end = 0.0
    for beat in beats:
        start = float(beat.get("start_seconds", -1))
        end = float(beat.get("end_seconds", -1))
        if start < previous_end - 0.02 or end <= start:
            errors.append(f"microbeat_order_invalid:{beat.get('beat_id')}")
        duration = end - start
        if duration > 3.25 and not beat.get("hold_justification"):
            errors.append(f"unexplained_static_hold:{beat.get('beat_id')}:{duration:.3f}")
        if not beat.get("evidence_function"):
            errors.append(f"microbeat_without_evidence_function:{beat.get('beat_id')}")
        previous_end = max(previous_end, end)
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "beat_count": len(beats)}


def validate_import_manifest(manifest: Mapping[str, Any], repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    for row in manifest.get("files", []):
        destination = (repo_root / str(row.get("destination", ""))).resolve()
        if not destination.is_file():
            errors.append(f"import_destination_missing:{row.get('destination')}")
            continue
        actual = sha256_file(destination)
        if actual != row.get("after_import_sha256") or actual != row.get("source_sha256"):
            errors.append(f"import_hash_mismatch:{row.get('destination')}")
    if not manifest.get("files"):
        errors.append("import_files_missing")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "file_count": len(manifest.get("files", []))}


def validate_creative_source(source: Path, project_root: Path) -> dict[str, Any]:
    if project_root.resolve() not in source.resolve().parents:
        raise ValueError("source_outside_project")
    text = source.read_text(encoding="utf-8")
    errors: list[str] = []
    for label, pattern in {
        "network": r"\b(fetch|XMLHttpRequest|WebSocket)\b",
        "environment": r"process\.env", "filesystem": r"\b(node:fs|child_process)\b",
        "browser": r"\b(playwright|puppeteer|cdp)\b", "css_blur": r"(backdrop-filter|filter:\s*blur)",
        "fixed_compositor": r"\bSceneRenderer\b",
    }.items():
        if re.search(pattern, text, re.IGNORECASE):
            errors.append(f"forbidden_source:{label}")
    for token in ("BreakingRetailSales", "CODEX_VIEWER_FACING_AUTHORSHIP", "segments"):
        if token not in text:
            errors.append(f"missing_creative_marker:{token}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "source": str(source.resolve()), "sha256": sha256_file(source)}


def probe_media(path: Path) -> dict[str, Any]:
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size,bit_rate,format_name:stream=index,codec_type,codec_name,profile,width,height,avg_frame_rate,pix_fmt,color_range,color_space,color_transfer,color_primaries,bit_rate",
        "-of", "json", str(path),
    ], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def video_stream(probe: Mapping[str, Any]) -> Mapping[str, Any]:
    return next(row for row in probe["streams"] if row.get("codec_type") == "video")


def validate_crisp_master(path: Path, *, expected_width: int, expected_height: int,
                          minimum_bitrate: int, proxy_lineage: bool,
                          source_assets: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    probe = probe_media(path)
    stream = video_stream(probe)
    bitrate = int(probe.get("format", {}).get("bit_rate") or stream.get("bit_rate") or 0)
    errors: list[str] = []
    if (stream.get("width"), stream.get("height")) != (expected_width, expected_height):
        errors.append("resolution_mismatch")
    if stream.get("avg_frame_rate") != "30/1":
        errors.append("frame_rate_mismatch")
    if bitrate < minimum_bitrate:
        errors.append(f"bitrate_below_gate:{bitrate}")
    if stream.get("codec_name") != "h264" or str(stream.get("profile", "")).lower() != "high":
        errors.append("delivery_codec_not_h264_high")
    if stream.get("pix_fmt") != "yuv420p":
        errors.append("pixel_format_not_yuv420p")
    if stream.get("color_range") not in {"tv", "mpeg"}:
        errors.append("color_range_not_limited")
    for key in ("color_space", "color_transfer", "color_primaries"):
        if stream.get(key) != "bt709":
            errors.append(f"{key}_not_bt709")
    if proxy_lineage:
        errors.append("proxy_lineage_forbidden")
    for asset in source_assets:
        if int(asset.get("native_width", 0)) < int(asset.get("minimum_width", 0)):
            errors.append(f"source_resolution_below_gate:{asset.get('asset_id')}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "actual_bitrate": bitrate, "probe": probe}


def validate_material_audit(report: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if float(report.get("pixels_below_luma_64_fraction", 1)) >= 0.65:
        errors.append("too_dark_against_qh1_benchmark")
    if int(report.get("material_family_count", 0)) < 5:
        errors.append("material_diversity_below_gate")
    if int(report.get("max_equivalent_dark_run", 99)) > 1:
        errors.append("equivalent_dark_scene_run")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def validate_zero_public_write(manifest: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if manifest.get("public_write_authority") is not False:
        errors.append("public_write_authority")
    for key in ("uploads", "platform_drafts", "browser_publication_calls", "v1_mutations", "v2_02_runs", "mode_bakeoff_runs"):
        if int(manifest.get(key, -1)) != 0:
            errors.append(key)
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def zero_public_write_manifest() -> dict[str, Any]:
    return {"public_write_authority": False, "uploads": 0, "platform_drafts": 0,
            "browser_publication_calls": 0, "v1_mutations": 0, "v2_02_runs": 0,
            "mode_bakeoff_runs": 0, "heygen_used": False}


def codex_execution_plane_manifest() -> dict[str, Any]:
    return {
        "creative_author": "Codex current task session",
        "model": "not_exposed",
        "reasoning_effort": "not_exposed",
        "nine_router_route": None,
    }
