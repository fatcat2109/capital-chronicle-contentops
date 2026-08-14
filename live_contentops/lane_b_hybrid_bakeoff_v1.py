"""Durable, zero-public-write Lane B Hybrid mode-bakeoff control plane.

The module deliberately keeps creative output outside durable truth authority.  A
fresh Codex execution authors one explicit creative packet; this deterministic
boundary validates it, records immutable checkpoints, and prepares one shared
Remotion renderer input.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "contentops.lane_b_hybrid_bakeoff.v1"
BENCHMARK_ID = "EIA_HORMUZ_SHARED_MODE_BAKEOFF_V1"
ARTICLE_HASH = "4a61bb93b43a7fb1d2fd016cbec048ddf9460f1de8731e9ba81241c7a1a3cf9e"
EVIDENCE_HASH = "1e87b1815912a3fdf3a59b56a17d343c39204b3b200527fc099771563c93a44a"
REVISION_BUDGET = 1
PUBLIC_WRITE = False

MODE_MAP: Mapping[str, Mapping[str, str]] = {
    "HIGH": {"model": "gpt-5.6-sol", "reasoning_effort": "high"},
    "XHIGH": {"model": "gpt-5.6-sol", "reasoning_effort": "xhigh"},
    "ULTRA": {"model": "gpt-5.6-sol", "reasoning_effort": "ultra"},
}

ALLOWED_PRIMITIVES = frozenset(
    {
        "MAP_TO_VESSEL",
        "PHYSICAL_CHAIN",
        "DOCUMENT_EVIDENCE",
        "NATIVE_FORECAST_CHART",
        "TRANSMISSION",
        "CONSEQUENCE",
        "CONFIRM_CHALLENGE",
        "CHECKPOINT_TIMELINE",
    }
)
ACCEPTED_RIGHTS = frozenset(
    {
        "PUBLIC_DOMAIN",
        "NASA_MEDIA_GUIDELINES_EDITORIAL",
        "CREATIVE_COMMONS_ATTRIBUTION",
        "US_GOVERNMENT_PUBLIC_INFORMATION",
        "CAPITAL_CHRONICLE_OWNED",
    }
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def logical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"json_object_required:{path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class BenchmarkIdentity:
    benchmark_hash: str
    evidence_snapshot_hash: str
    asset_manifest_hash: str
    engine_version: str


class HybridLedger:
    """Small SQLite outbox/stage ledger with atomic claims and resume."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS candidates(
              candidate_id TEXT PRIMARY KEY, benchmark_hash TEXT NOT NULL,
              evidence_hash TEXT NOT NULL, asset_manifest_hash TEXT NOT NULL,
              qualification_reason TEXT NOT NULL, public_write INTEGER NOT NULL CHECK(public_write=0)
            );
            CREATE TABLE IF NOT EXISTS jobs(
              job_id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, owner_label TEXT NOT NULL,
              model TEXT NOT NULL, reasoning_effort TEXT NOT NULL, run_id TEXT NOT NULL UNIQUE,
              state TEXT NOT NULL, claimed_by TEXT, input_hash TEXT NOT NULL,
              retry_count INTEGER NOT NULL DEFAULT 0, creative_revisions INTEGER NOT NULL DEFAULT 0,
              mechanical_corrections INTEGER NOT NULL DEFAULT 0, render_count INTEGER NOT NULL DEFAULT 0,
              operator_interventions INTEGER NOT NULL DEFAULT 0, wall_clock_seconds REAL NOT NULL DEFAULT 0,
              invocation_count INTEGER NOT NULL DEFAULT 0, public_write INTEGER NOT NULL CHECK(public_write=0),
              FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
            );
            CREATE TABLE IF NOT EXISTS stages(
              job_id TEXT NOT NULL, stage TEXT NOT NULL, attempt INTEGER NOT NULL,
              input_hash TEXT NOT NULL, output_hash TEXT, status TEXT NOT NULL,
              tool_identity TEXT NOT NULL, runtime_seconds REAL NOT NULL,
              receipt_json TEXT NOT NULL, PRIMARY KEY(job_id,stage,attempt)
            );
            CREATE TABLE IF NOT EXISTS artifacts(
              job_id TEXT NOT NULL, name TEXT NOT NULL, path TEXT NOT NULL, sha256 TEXT NOT NULL,
              PRIMARY KEY(job_id,name)
            );
            """
        )
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def create_bakeoff(self, identity: BenchmarkIdentity, input_hash: str) -> list[dict[str, str]]:
        candidate_id = f"candidate-{identity.benchmark_hash[:16]}"
        self.db.execute(
            "INSERT OR IGNORE INTO candidates VALUES(?,?,?,?,?,0)",
            (candidate_id, identity.benchmark_hash, identity.evidence_snapshot_hash,
             identity.asset_manifest_hash, "institutional_depth+physical_mechanism+primary_evidence"),
        )
        rows: list[dict[str, str]] = []
        for owner_label, config in MODE_MAP.items():
            run_id = f"{owner_label.lower()}-{uuid.uuid4().hex}"
            job_id = f"{candidate_id}-{owner_label.lower()}"
            self.db.execute(
                "INSERT INTO jobs(job_id,candidate_id,owner_label,model,reasoning_effort,run_id,state,input_hash,public_write) "
                "VALUES(?,?,?,?,?,?,?, ?,0)",
                (job_id, candidate_id, owner_label, config["model"], config["reasoning_effort"],
                 run_id, "QUALIFIED", input_hash),
            )
            rows.append({"job_id": job_id, "run_id": run_id, "owner_label": owner_label})
        self.db.commit()
        return rows

    def claim(self, job_id: str, worker_id: str) -> bool:
        result = self.db.execute(
            "UPDATE jobs SET state='CLAIMED',claimed_by=? WHERE job_id=? AND state='QUALIFIED'",
            (worker_id, job_id),
        )
        self.db.commit()
        return result.rowcount == 1

    def checkpoint(self, job_id: str, stage: str, input_hash: str, output: Any,
                   tool_identity: str, runtime_seconds: float, status: str = "PASS") -> str:
        output_hash = logical_hash(output)
        attempt = int(self.db.execute(
            "SELECT COALESCE(MAX(attempt),0)+1 FROM stages WHERE job_id=? AND stage=?",
            (job_id, stage),
        ).fetchone()[0])
        receipt = {"schema_version": SCHEMA_VERSION, "public_write": False, "status": status}
        self.db.execute(
            "INSERT INTO stages VALUES(?,?,?,?,?,?,?,?,?)",
            (job_id, stage, attempt, input_hash, output_hash, status, tool_identity,
             float(runtime_seconds), canonical_json(receipt)),
        )
        self.db.execute("UPDATE jobs SET state=? WHERE job_id=?", (stage, job_id))
        self.db.commit()
        return output_hash

    def last_valid_stage(self, job_id: str) -> str | None:
        row = self.db.execute(
            "SELECT stage FROM stages WHERE job_id=? AND status='PASS' ORDER BY rowid DESC LIMIT 1",
            (job_id,),
        ).fetchone()
        return str(row[0]) if row else None


def prepare_benchmark(source_runtime: Path, runtime: Path, engine_version: str) -> tuple[BenchmarkIdentity, dict[str, Any]]:
    contracts = source_runtime / "contracts"
    evidence = read_json(contracts / "compact_evidence_v2.json")
    assets = read_json(contracts / "asset_candidate_universe_v2.json")
    if evidence.get("article_hash") != ARTICLE_HASH:
        raise ValueError("benchmark_article_hash_mismatch")
    if evidence.get("historical_governed_eia_sha256") != EVIDENCE_HASH:
        raise ValueError("benchmark_evidence_hash_mismatch")
    if evidence.get("public_write_authority") is not False or assets.get("public_write") is not False:
        raise ValueError("benchmark_public_write_must_be_false")
    for row in assets.get("candidates", []):
        if row.get("rights_status") not in ACCEPTED_RIGHTS:
            raise ValueError(f"asset_rights_not_accepted:{row.get('asset_id')}")
    immutable = {
        "schema_version": SCHEMA_VERSION,
        "benchmark_id": BENCHMARK_ID,
        "article_hash": ARTICLE_HASH,
        "evidence_hash": EVIDENCE_HASH,
        "evidence": evidence,
        "asset_manifest": assets,
        "design_system_version": "LANE_B_HYBRID_TOKENS_V1",
        "primitive_version": "LANE_B_PRIMITIVES_V1",
        "audio_policy": "WINDOWS_SAPI_LOCAL_V1|-16_LUFS|-1.5_DBTP",
        "revision_budget": REVISION_BUDGET,
        "evaluation_rubric": ["comprehension", "institutional_depth", "visual_hierarchy", "motion_craft", "truth"],
        "public_write": False,
    }
    benchmark_hash = logical_hash(immutable)
    asset_manifest_hash = logical_hash(assets)
    identity = BenchmarkIdentity(benchmark_hash, logical_hash(evidence), asset_manifest_hash, engine_version)
    packet_dir = runtime / "shared"
    write_json(packet_dir / "immutable_benchmark_packet.json", immutable)
    public_assets = runtime / "renderer_public" / "assets"
    public_assets.mkdir(parents=True, exist_ok=True)
    for row in assets["candidates"]:
        source = Path(str(row["local_path"]))
        destination = public_assets / Path(str(row["relative_public_path"])).name
        if not destination.exists():
            shutil.copy2(source, destination)
        if sha256_file(destination) != row["sha256"]:
            raise ValueError(f"asset_hash_mismatch:{row['asset_id']}")
    return identity, immutable


def build_mode_input(immutable: Mapping[str, Any], owner_label: str, run_id: str) -> dict[str, Any]:
    config = MODE_MAP[owner_label]
    return {
        "schema_version": SCHEMA_VERSION,
        "owner_label": owner_label,
        "actual_config": config,
        "run_id": run_id,
        "fresh_isolated_execution_required": True,
        "immutable_benchmark": immutable,
        "output_contract": {
            "duration_seconds": 54,
            "resolution": [1080, 1920],
            "fps": 30,
            "scene_count": [7, 9],
            "allowed_primitives": sorted(ALLOWED_PRIMITIVES),
            "clean_master": True,
            "captions": "sidecar_only",
            "revision_budget": REVISION_BUDGET,
            "public_write": False,
        },
        "anti_contamination": "Do not read any sibling mode output or critic artifact.",
    }


def validate_creative_packet(packet: Mapping[str, Any], expected_input: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for key in ("owner_label", "run_id", "input_hash"):
        if packet.get(key) != expected_input.get(key):
            errors.append(f"identity_mismatch:{key}")
    if packet.get("public_write") is not False:
        errors.append("public_write_not_false")
    layers = packet.get("layers") or {}
    if set(layers) != {"truth", "analysis", "engagement"}:
        errors.append("truth_analysis_engagement_separation_missing")
    analytical = packet.get("analytical_map") or {}
    for key in ("core_question", "physical_mechanism", "second_order_channel", "confirm", "challenge", "next_checkpoint"):
        if not analytical.get(key):
            errors.append(f"analytical_map_missing:{key}")
    scenes = packet.get("scenes") or []
    if not 7 <= len(scenes) <= 9:
        errors.append("scene_count_out_of_range")
    total = round(sum(float(row.get("duration_seconds") or 0) for row in scenes), 3)
    if not 45 <= total <= 60:
        errors.append("duration_out_of_range")
    assets = expected_input["immutable_benchmark"]["asset_manifest"]["candidates"]
    allowed_assets = {row["asset_id"]: row for row in assets}
    usage: dict[str, float] = {}
    previous_asset: str | None = None
    for index, scene in enumerate(scenes):
        primitive = str(scene.get("primitive") or "")
        if primitive not in ALLOWED_PRIMITIVES:
            errors.append(f"primitive_not_allowed:{index}:{primitive}")
        asset_id = str(scene.get("asset_id") or "")
        if asset_id not in allowed_assets:
            errors.append(f"asset_not_allowed:{index}:{asset_id}")
        if asset_id == previous_asset:
            errors.append(f"consecutive_asset_reuse:{index}:{asset_id}")
        previous_asset = asset_id
        usage[asset_id] = usage.get(asset_id, 0.0) + float(scene.get("duration_seconds") or 0)
        title = str(scene.get("title") or "")
        body = str(scene.get("body") or "")
        if len(title) > 72 or len(body) > 190:
            errors.append(f"phone_text_budget_exceeded:{index}")
        if not scene.get("source"):
            errors.append(f"source_missing:{index}")
        if scene.get("caption_visible") not in (False, None):
            errors.append(f"clean_master_caption_policy:{index}")
    if total:
        for asset_id, seconds in usage.items():
            if seconds / total > 0.18:
                errors.append(f"asset_concentration:{asset_id}:{seconds/total:.3f}")
    narration = str(packet.get("narration") or "")
    if not 95 <= len(narration.split()) <= 165:
        errors.append("narration_density_out_of_range")
    if errors:
        raise ValueError(";".join(errors))
    return {"status": "PASS", "duration_seconds": total, "scene_count": len(scenes),
            "asset_use_seconds": usage, "public_write": False}


def write_srt(packet: Mapping[str, Any], path: Path) -> None:
    lines: list[str] = []
    at = 0.0
    for index, scene in enumerate(packet["scenes"], 1):
        end = at + float(scene["duration_seconds"])
        def stamp(value: float) -> str:
            millis = int(round(value * 1000))
            return f"{millis//3600000:02}:{millis//60000%60:02}:{millis//1000%60:02},{millis%1000:03}"
        lines.extend((str(index), f"{stamp(at)} --> {stamp(end)}", str(scene["narration"]), ""))
        at = end
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def probe_media(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def zero_public_write_manifest() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "public_write": False,
        "platform_actions": [],
        "browser_cdp_actions": [],
        "v1_mutations": [],
        "authority": "ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY",
    }

