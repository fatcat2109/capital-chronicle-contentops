"""Durable format/audio controls for the V2 short + longform vertical slice.

Creative decisions remain in story-specific Remotion source.  This module owns
the format contract, stage ledger, immutable local-audio cache contract, and
deterministic safety checks.  It performs no publication or browser work.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.lane_b_asset_first_v1 import canonical_json, logical_hash, sha256_file

TASK_ID = "TASK_CONTENTOPS_V2_SHORT_LONGFORM_LOW_COST_AUDIO_VERTICAL_SLICE_V1"
STAGES = (
    "STORY_LOCKED", "EVIDENCE_LOCKED", "ANALYSIS_READY", "ASSET_BOARD_READY",
    "SHORT_STORYBOARD_READY", "LONGFORM_STORYBOARD_READY", "SHORT_SOURCE_READY",
    "LONGFORM_SOURCE_READY", "BUILD_AUDIO_READY", "PROXY_READY", "VISUAL_REVIEW",
    "QA_REVISE", "MASTER_READY", "OWNER_REVIEW",
)
STAGE_ORDER = {stage: index for index, stage in enumerate(STAGES)}


@dataclass(frozen=True)
class AudioBackend:
    backend_id: str
    model: str
    voice: str
    locality: str
    marginal_api_cost_usd: float
    enabled_for_build: bool
    reference_audio_allowed: bool = False

    def validate(self) -> None:
        if self.locality != "LOCAL" or self.marginal_api_cost_usd != 0:
            raise ValueError("build_audio_must_be_zero_marginal_api_cost_local")
        if self.reference_audio_allowed:
            raise ValueError("real_person_voice_clone_path_forbidden")
        if "eleven" in self.backend_id.lower() and self.enabled_for_build:
            raise ValueError("elevenlabs_build_calls_forbidden")


KOKORO_BUILD = AudioBackend("KOKORO_LOCAL_BUILD", "Kokoro-82M", "af_heart", "LOCAL", 0.0, True)
PARLER_CANDIDATE = AudioBackend("PARLER_LOCAL_CANDIDATE", "unavailable", "unavailable", "LOCAL", 0.0, False)
CHATTERBOX_CANDIDATE = AudioBackend("CHATTERBOX_CONDITIONAL_CANDIDATE", "ResembleAI/chatterbox", "default-no-reference", "LOCAL", 0.0, False)
ELEVENLABS_FINAL = {"backend_id": "ELEVENLABS_PREMIUM_FINAL", "enabled": False, "calls": 0, "reason": "OWNER_APPROVAL_REQUIRED"}


class FormatAudioLedger:
    """Append-only checkpoints with resumable, hash-addressed stages."""

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS jobs(job_id TEXT PRIMARY KEY,candidate_id TEXT NOT NULL,state TEXT NOT NULL,created_at REAL NOT NULL,updated_at REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS stages(id INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT NOT NULL,stage TEXT NOT NULL,input_hash TEXT NOT NULL,output_hash TEXT NOT NULL,output_json TEXT NOT NULL,runtime_seconds REAL NOT NULL,created_at REAL NOT NULL,UNIQUE(job_id,stage,input_hash,output_hash));
          CREATE TABLE IF NOT EXISTS artifacts(id INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT NOT NULL,kind TEXT NOT NULL,path TEXT NOT NULL,sha256 TEXT NOT NULL,bytes INTEGER NOT NULL,created_at REAL NOT NULL);
        """)
        self.db.commit()

    def create_job(self, job_id: str, candidate_id: str) -> None:
        now = time.time()
        self.db.execute("INSERT OR IGNORE INTO jobs VALUES(?,?,?,?,?)", (job_id, candidate_id, STAGES[0], now, now))
        self.db.commit()

    def checkpoint(self, job_id: str, stage: str, input_value: Any, output: Mapping[str, Any], runtime_seconds: float = 0.0) -> dict[str, Any]:
        if stage not in STAGE_ORDER:
            raise ValueError(f"unknown_stage:{stage}")
        current_row = self.db.execute("SELECT state FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if current_row is None:
            raise KeyError(job_id)
        current = str(current_row["state"])
        if STAGE_ORDER[stage] < STAGE_ORDER[current]:
            raise ValueError(f"stage_regression:{current}->{stage}")
        input_hash, output_hash = logical_hash(input_value), logical_hash(output)
        existing = self.db.execute("SELECT id FROM stages WHERE job_id=? AND stage=? AND input_hash=? AND output_hash=?", (job_id, stage, input_hash, output_hash)).fetchone()
        if existing:
            return {"status": "REUSED", "stage": stage, "stage_row_id": int(existing["id"])}
        now = time.time()
        cursor = self.db.execute("INSERT INTO stages(job_id,stage,input_hash,output_hash,output_json,runtime_seconds,created_at) VALUES(?,?,?,?,?,?,?)", (job_id, stage, input_hash, output_hash, canonical_json(output), runtime_seconds, now))
        self.db.execute("UPDATE jobs SET state=?,updated_at=? WHERE job_id=?", (stage, now, job_id))
        self.db.commit()
        return {"status": "WRITTEN", "stage": stage, "stage_row_id": int(cursor.lastrowid)}

    def add_artifact(self, job_id: str, kind: str, path: Path) -> dict[str, Any]:
        row = {"kind": kind, "path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        self.db.execute("INSERT INTO artifacts(job_id,kind,path,sha256,bytes,created_at) VALUES(?,?,?,?,?,?)", (job_id, kind, str(path), row["sha256"], row["bytes"], time.time()))
        self.db.commit()
        return row

    def stage_rows(self, job_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.db.execute("SELECT * FROM stages WHERE job_id=? ORDER BY id", (job_id,))]

    def close(self) -> None:
        self.db.close()


def segment_cache_key(text: str, backend: AudioBackend, settings: Mapping[str, Any]) -> str:
    backend.validate()
    return logical_hash({"text": text.strip(), "backend": backend.backend_id, "model": backend.model, "voice": backend.voice, "settings": dict(settings)})


def build_missing_segment_request(scenes: Sequence[Mapping[str, Any]], cache_dir: Path, *, speed: float = 1.0) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    request_rows: list[dict[str, Any]] = []
    manifest_rows: list[dict[str, Any]] = []
    for scene in scenes:
        key = segment_cache_key(str(scene["narration"]), KOKORO_BUILD, {"speed": speed, "sample_rate": 24000})
        target = cache_dir / f"{key}.wav"
        status = "REUSED" if target.is_file() else "GENERATE"
        row = {"scene_id": scene["scene_id"], "cache_key": key, "path": str(target), "status": status, "text_sha256": hashlib.sha256(str(scene["narration"]).encode()).hexdigest()}
        manifest_rows.append(row)
        if status == "GENERATE":
            request_rows.append({"text": scene["narration"], "output_path": str(target), "voice": KOKORO_BUILD.voice, "speed": speed})
    return {"segments": request_rows}, manifest_rows


def validate_format_contract(short: Sequence[Mapping[str, Any]], longform: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    if not 6 <= len(short) <= 12:
        errors.append("short_scene_count")
    if len(longform) < 14:
        errors.append("longform_scene_count")
    if [row.get("scene_id") for row in short] == [row.get("scene_id") for row in longform]:
        errors.append("formats_not_independently_authored")
    if len(" ".join(str(row.get("narration", "")) for row in longform).split()) < 850:
        errors.append("longform_narration_too_short")
    if any(not row.get("visual_kind") for row in [*short, *longform]):
        errors.append("missing_visual_kind")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "short_scenes": len(short), "longform_scenes": len(longform)}


def validate_zero_write(manifest: Mapping[str, Any]) -> dict[str, Any]:
    forbidden = ("public_writes", "uploads", "browser_profile_uses", "elevenlabs_calls", "v1_mutations")
    errors = [f"nonzero:{key}" for key in forbidden if int(manifest.get(key, 0)) != 0]
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}
