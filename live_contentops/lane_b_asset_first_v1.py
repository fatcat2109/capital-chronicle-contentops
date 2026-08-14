"""Durable controls for the V2 asset-first editorial visual proof.

Viewer-facing editorial and motion decisions live in story-specific Remotion
source.  This module deliberately owns only evidence, rights, provenance,
dependency, safety, recovery, media, and zero-public-write gates.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


TASK_ID = "TASK_CONTENTOPS_V2_ASSET_FIRST_EDITORIAL_VISUAL_QUALITY_HARDENING_VERTICAL_SLICE_V1"
BENCHMARK_ID = "US_TREASURY_CURVE_ASSET_FIRST_EDITORIAL_PROOF_V1"
ACTIVE_STAGES = (
    "DISCOVERED", "QUALIFIED", "CLAIMED", "EVIDENCE_LOCKED",
    "EVIDENCE_EXPANDED", "EDITORIAL_READY", "VISUAL_NEEDS_READY",
    "ASSET_BOARD_READY", "ASSETS_READY", "STORYBOARD_READY",
    "CREATIVE_SOURCE_READY", "KEYFRAMES_READY", "PREMOTION_REVIEW",
    "PROXY_READY", "VISUAL_REVIEW", "QA_REVISE", "MASTER_READY",
    "FINAL_REVIEW", "OWNER_REVIEW",
)
TERMINAL_STAGES = ("ABSTAINED", "BLOCKED", "FAILED")
ALL_STAGES = frozenset((*ACTIVE_STAGES, *TERMINAL_STAGES))
STAGE_ORDER = {name: index for index, name in enumerate(ACTIVE_STAGES)}
ACCEPTED_LICENSES = frozenset({"PUBLIC_DOMAIN", "CC0", "CC_BY", "CC_BY_SA", "INTERNAL_GOVERNED"})


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


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
        raise ValueError(f"expected_object:{path}")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class ExecutionProvenance:
    execution_plane: str
    model_or_tool: str
    mode: str
    task_id: str = TASK_ID
    benchmark_id: str = BENCHMARK_ID
    public_write_authority: bool = False
    browser_profile_used: bool = False
    network_publication_calls: int = 0

    def validate(self) -> None:
        if self.public_write_authority or self.browser_profile_used or self.network_publication_calls:
            raise ValueError("zero_public_write_boundary_violated")
        if self.mode.upper() in {"HIGH", "XHIGH", "EXTRA_HIGH", "ULTRA"}:
            raise ValueError("mode_bakeoff_forbidden")


class AssetFirstLedger:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
              job_id TEXT PRIMARY KEY, candidate_id TEXT NOT NULL, state TEXT NOT NULL,
              created_at REAL NOT NULL, updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS stages (
              id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, stage TEXT NOT NULL,
              input_hash TEXT NOT NULL, output_hash TEXT NOT NULL, output_json TEXT NOT NULL,
              model_or_tool TEXT NOT NULL, execution_plane TEXT NOT NULL,
              runtime_seconds REAL NOT NULL, artifact_refs_json TEXT NOT NULL,
              created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS artifacts (
              id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL, kind TEXT NOT NULL,
              path TEXT NOT NULL, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL, created_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS defects (
              defect_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, stage TEXT NOT NULL,
              severity TEXT NOT NULL, category TEXT NOT NULL, source_surface TEXT NOT NULL,
              diagnosis TEXT NOT NULL, repair TEXT NOT NULL, affected_json TEXT NOT NULL,
              resolved INTEGER NOT NULL, created_at REAL NOT NULL
            );
            """
        )
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def create_job(self, job_id: str, candidate_id: str) -> None:
        now = time.time()
        self.db.execute(
            "INSERT OR IGNORE INTO jobs(job_id,candidate_id,state,created_at,updated_at) VALUES(?,?,?,?,?)",
            (job_id, candidate_id, "DISCOVERED", now, now),
        )
        self.db.commit()

    def checkpoint(
        self, job_id: str, stage: str, input_hash: str, output: Mapping[str, Any], *,
        model_or_tool: str, execution_plane: str, runtime_seconds: float,
        artifact_refs: Sequence[str] = (),
    ) -> dict[str, Any]:
        if stage not in ALL_STAGES:
            raise ValueError(f"unknown_stage:{stage}")
        row = self.db.execute("SELECT state FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        current = str(row["state"])
        if stage in STAGE_ORDER and current in STAGE_ORDER and STAGE_ORDER[stage] < STAGE_ORDER[current]:
            raise ValueError(f"stage_regression:{current}->{stage}")
        now = time.time()
        payload = dict(output)
        output_hash = logical_hash(payload)
        existing = self.db.execute(
            "SELECT id FROM stages WHERE job_id=? AND stage=? AND input_hash=? AND output_hash=? ORDER BY id DESC LIMIT 1",
            (job_id, stage, input_hash, output_hash),
        ).fetchone()
        if existing is not None:
            return {"status": "REUSED", "stage": stage, "stage_row_id": int(existing["id"])}
        self.db.execute(
            "INSERT INTO stages(job_id,stage,input_hash,output_hash,output_json,model_or_tool,execution_plane,runtime_seconds,artifact_refs_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
            (job_id, stage, input_hash, output_hash, canonical_json(payload), model_or_tool,
             execution_plane, float(runtime_seconds), canonical_json(list(artifact_refs)), now),
        )
        self.db.execute("UPDATE jobs SET state=?,updated_at=? WHERE job_id=?", (stage, now, job_id))
        self.db.commit()
        return {"status": "WRITTEN", "stage": stage, "stage_row_id": int(self.db.execute("SELECT last_insert_rowid()").fetchone()[0])}

    def add_artifact(self, job_id: str, kind: str, path: Path) -> dict[str, Any]:
        row = {"kind": kind, "path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size}
        self.db.execute(
            "INSERT INTO artifacts(job_id,kind,path,sha256,bytes,created_at) VALUES(?,?,?,?,?,?)",
            (job_id, row["kind"], row["path"], row["sha256"], row["bytes"], time.time()),
        )
        self.db.commit()
        return row

    def add_defect(self, job_id: str, defect: Mapping[str, Any]) -> None:
        required = ("defect_id", "stage", "severity", "category", "source_surface", "diagnosis", "repair", "affected")
        if any(key not in defect for key in required):
            raise ValueError("incomplete_defect_record")
        self.db.execute(
            "INSERT OR REPLACE INTO defects(defect_id,job_id,stage,severity,category,source_surface,diagnosis,repair,affected_json,resolved,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (defect["defect_id"], job_id, defect["stage"], defect["severity"], defect["category"],
             defect["source_surface"], defect["diagnosis"], defect["repair"], canonical_json(defect["affected"]),
             int(bool(defect.get("resolved"))), time.time()),
        )
        self.db.commit()

    def rows(self, job_id: str, table: str) -> list[dict[str, Any]]:
        if table not in {"stages", "artifacts", "defects"}:
            raise ValueError(table)
        order = "id" if table in {"stages", "artifacts"} else "created_at"
        return [dict(row) for row in self.db.execute(f"SELECT * FROM {table} WHERE job_id=? ORDER BY {order}", (job_id,))]

    def last_valid_stage(self, job_id: str) -> str:
        row = self.db.execute("SELECT state FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return str(row["state"])


def validate_visual_needs(graph: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    needs = graph.get("needs") or []
    required = {"hook", "primary_evidence", "mechanism", "transmission", "consequence", "confirm_challenge"}
    found = {str(row.get("purpose")) for row in needs}
    for missing in sorted(required - found):
        errors.append(f"missing_visual_need:{missing}")
    for row in needs:
        if not row.get("need_id") or not row.get("editorial_job") or not row.get("ideal_asset"):
            errors.append(f"incomplete_visual_need:{row.get('need_id','unknown')}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "need_count": len(needs)}


def validate_asset_board(board: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    candidates = board.get("candidates") or []
    by_need: dict[str, list[Mapping[str, Any]]] = {}
    for row in candidates:
        by_need.setdefault(str(row.get("need_id")), []).append(row)
        license_id = str(row.get("license_id", ""))
        if license_id not in ACCEPTED_LICENSES:
            errors.append(f"rights_rejected:{row.get('asset_id')}:{license_id}")
        if not row.get("source_url") or not row.get("attribution"):
            errors.append(f"missing_provenance:{row.get('asset_id')}")
        if not row.get("decision") or not row.get("decision_reason"):
            errors.append(f"missing_decision:{row.get('asset_id')}")
        if row.get("decision") == "SELECTED":
            score = float(row.get("visual_fit_score", 0))
            if score < 0.72:
                errors.append(f"asset_visual_fit_below_gate:{row.get('asset_id')}:{score}")
            role = str(row.get("presentation_role", "FULL_BLEED"))
            minimum = (960, 640) if role == "SPLIT_PANEL" else (1600, 900)
            if int(row.get("width", 0)) < minimum[0] or int(row.get("height", 0)) < minimum[1]:
                errors.append(f"asset_resolution_below_gate:{row.get('asset_id')}")
            if row.get("embedded_text") not in {False, "NONE", "SOURCE_NATIVE_ONLY"}:
                errors.append(f"selected_asset_embedded_text:{row.get('asset_id')}")
            if not row.get("crop_9x16") or not row.get("crop_16x9"):
                errors.append(f"missing_crop_assessment:{row.get('asset_id')}")
    for need_id, rows in by_need.items():
        if len(rows) < 2 or len(rows) > 5:
            errors.append(f"candidate_count_out_of_range:{need_id}:{len(rows)}")
        if not any(row.get("decision") == "SELECTED" for row in rows):
            errors.append(f"no_selected_asset:{need_id}")
    return {
        "status": "PASS" if not errors else "FAIL", "gate": "ASSET_VISUAL_FIT",
        "errors": errors, "candidate_count": len(candidates),
        "selected_count": sum(1 for row in candidates if row.get("decision") == "SELECTED"),
        "needs_with_candidates": sorted(by_need),
    }


def validate_creative_source(source: Path, project_root: Path) -> dict[str, Any]:
    resolved = source.resolve()
    if project_root.resolve() not in resolved.parents:
        raise ValueError("creative_source_outside_project_root")
    text = source.read_text(encoding="utf-8")
    errors: list[str] = []
    forbidden = {
        "network": r"\b(fetch|XMLHttpRequest|WebSocket)\b", "environment": r"process\.env",
        "filesystem": r"\b(fs|node:fs|child_process)\b", "browser": r"(playwright|puppeteer|cdp)",
        "remote_import": r"from\s+['\"]https?://", "fixed_scene_renderer": r"\bSceneRenderer\b",
    }
    for label, pattern in forbidden.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            errors.append(f"forbidden_source:{label}")
    for token in ("AssetFirstTreasuryShort", "AssetFirstTreasuryMidform", "CODEX_VIEWER_FACING_AUTHORSHIP"):
        if token not in text:
            errors.append(f"missing_authorship_marker:{token}")
    imports = re.findall(r"from\s+['\"]([^'\"]+)['\"]", text)
    allowed = {"react", "remotion", "../lowLevel"}
    for module in imports:
        if module not in allowed:
            errors.append(f"unapproved_import:{module}")
    dependency_files = [source, project_root / "src" / "lowLevel.tsx", project_root / "src" / "root.tsx"]
    component_hashes: dict[str, str] = {}
    for path in dependency_files:
        if not path.is_file():
            errors.append(f"missing_creative_dependency:{path.name}")
            continue
        component_hashes[str(path.resolve())] = sha256_file(path)
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "source": str(resolved),
            "component_hashes": component_hashes, "sha256": logical_hash(component_hashes)}


def validate_dependencies(manifest: Mapping[str, Any], creative_source: Path) -> dict[str, Any]:
    errors: list[str] = []
    text = creative_source.read_text(encoding="utf-8")
    source_assets = set(re.findall(r"asset\(['\"]([^'\"]+\.(?:png|jpg|jpeg))['\"]\)", text))
    rows = manifest.get("dependencies") or []
    manifest_assets = {str(row.get("asset_id")) for row in rows}
    if source_assets - manifest_assets:
        errors.append(f"source_assets_missing_from_manifest:{sorted(source_assets-manifest_assets)}")
    if manifest_assets - source_assets:
        errors.append(f"manifest_assets_not_in_source:{sorted(manifest_assets-source_assets)}")
    for variant in ("short", "midform"):
        relevant = [row for row in rows if variant in row.get("variants", [])]
        total = float(manifest.get("variant_duration_seconds", {}).get(variant, 0))
        by_family: dict[str, float] = {}
        by_asset: dict[str, float] = {}
        for row in relevant:
            seconds = float(row.get("screen_seconds", {}).get(variant, 0))
            if seconds <= 0:
                errors.append(f"invalid_dependency_time:{variant}:{row.get('asset_id')}")
            by_family[str(row.get("family"))] = by_family.get(str(row.get("family")), 0) + seconds
            by_asset[str(row.get("asset_id"))] = by_asset.get(str(row.get("asset_id")), 0) + seconds
        if total:
            for asset_id, seconds in by_asset.items():
                if seconds / total > 0.151:
                    errors.append(f"exact_asset_concentration:{variant}:{asset_id}:{seconds/total:.3f}")
            for family, seconds in by_family.items():
                if seconds / total > 0.36:
                    errors.append(f"family_concentration:{variant}:{family}:{seconds/total:.3f}")
        ordered = [str(value) for value in manifest.get("timeline", {}).get(variant, [])]
        for left, right in zip(ordered, ordered[1:]):
            if left == right:
                errors.append(f"consecutive_exact_repeat:{variant}:{left}")
    return {
        "status": "PASS" if not errors else "FAIL", "errors": errors,
        "source_asset_literals": sorted(source_assets), "manifest_assets": sorted(manifest_assets),
        "dependency_count": len(rows),
    }


def validate_microbeats(report: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for row in report.get("scenes", []):
        changes = [float(value) for value in row.get("meaningful_changes_seconds", [])]
        duration = float(row.get("duration_seconds", 0))
        points = [0.0, *changes, duration]
        max_gap = max((b - a for a, b in zip(points, points[1:])), default=duration)
        if max_gap > 4.25 and not row.get("intentional_hold"):
            errors.append(f"microbeat_gap:{row.get('scene_id')}:{max_gap:.2f}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def validate_layout(report: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for row in report.get("frames", []):
        for field in ("overflow", "source_collision", "caption_collision", "phone_illegible", "duplicate_label"):
            if row.get(field):
                errors.append(f"{field}:{row.get('variant')}:{row.get('scene_id')}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "frame_count": len(report.get("frames", []))}


def validate_audio_provider(provider: str) -> dict[str, Any]:
    accepted = provider.lower().startswith("kokoro")
    return {"status": "PASS" if accepted else "FAIL", "provider": provider, "sapi_forbidden": True}


def probe_media(path: Path) -> dict[str, Any]:
    command = ["ffprobe", "-v", "error", "-show_entries", "format=duration,format_name,size,bit_rate", "-show_entries",
               "stream=index,codec_type,codec_name,width,height,avg_frame_rate,pix_fmt,color_range,color_space,color_transfer,color_primaries,bit_rate", "-of", "json", str(path)]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def measure_loudness(path: Path) -> dict[str, float]:
    completed = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        check=False, capture_output=True, text=True,
    )
    summary = completed.stderr.rsplit("Summary:", 1)[-1]
    integrated_match = re.search(r"Integrated loudness:\s*I:\s*(-?\d+(?:\.\d+)?) LUFS", summary, flags=re.DOTALL)
    peak_match = re.search(r"True peak:\s*Peak:\s*(-?\d+(?:\.\d+)?) dBFS", summary, flags=re.DOTALL)
    if not integrated_match or not peak_match:
        raise ValueError("loudness_measurement_missing")
    return {"integrated_lufs": float(integrated_match.group(1)), "true_peak_dbtp": float(peak_match.group(1))}


def validate_editorial_layers(editorial: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    layers = editorial.get("layers") or {}
    for name in ("truth", "analysis", "engagement"):
        if not layers.get(name):
            errors.append(f"missing_editorial_layer:{name}")
    if editorial.get("nine_router_route") is not None:
        errors.append("nine_router_creative_route_forbidden")
    if editorial.get("mode_policy") != "UNSELECTED":
        errors.append("mode_bakeoff_forbidden")
    if editorial.get("legacy_hormuz_raster_used") is not False:
        errors.append("legacy_hormuz_raster_forbidden")
    for claim in editorial.get("quantitative_claims", []):
        if not claim.get("source_id") or claim.get("status") not in {"OBSERVATION", "FORECAST", "DERIVED"}:
            errors.append(f"unbound_quantitative_claim:{claim.get('claim_id','unknown')}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def validate_zero_public_write(manifest: Mapping[str, Any]) -> dict[str, Any]:
    errors = [key for key in ("public_write_authority", "browser_profile_used") if manifest.get(key) is not False]
    for key in ("uploads", "network_publication_calls", "v1_runtime_mutations", "v1_store_mutations", "prohibited_mode_bakeoff_runs"):
        if int(manifest.get(key, -1)) != 0:
            errors.append(key)
    return {"status": "PASS" if not errors else "FAIL", "errors": errors}


def write_srt(scenes: Sequence[Mapping[str, Any]], path: Path) -> None:
    def stamp(seconds: float) -> str:
        millis = int(round(seconds * 1000)); hours, rest = divmod(millis, 3_600_000)
        minutes, rest = divmod(rest, 60_000); secs, ms = divmod(rest, 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"
    cursor = 0.0; rows: list[str] = []
    for index, scene in enumerate(scenes, 1):
        duration = float(scene["duration_seconds"]); rows.append(f"{index}\n{stamp(cursor)} --> {stamp(cursor+duration)}\n{scene['narration']}\n")
        cursor += duration
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text("\n".join(rows), encoding="utf-8")


def copy_selected_assets(board: Mapping[str, Any], destination: Path) -> list[dict[str, Any]]:
    destination.mkdir(parents=True, exist_ok=True); copied = []
    for row in board.get("candidates", []):
        if row.get("decision") != "SELECTED":
            continue
        if row.get("kind") == "NATIVE":
            copied.append({"asset_id": row["asset_id"], "path": "viewer_source_native", "sha256": row.get("source_sha256", "NATIVE")})
            continue
        source = Path(str(row["local_path"])); target = destination / str(row["asset_id"])
        if not source.is_file():
            raise FileNotFoundError(f"selected_asset_missing:{source}")
        shutil.copy2(source, target)
        copied.append({"asset_id": row["asset_id"], "path": str(target), "sha256": sha256_file(target)})
    return copied


def zero_public_write_manifest() -> dict[str, Any]:
    return {"status": "PASS", "public_write_authority": False, "uploads": 0, "network_publication_calls": 0,
            "browser_profile_used": False, "v1_runtime_mutations": 0, "v1_store_mutations": 0,
            "prohibited_mode_bakeoff_runs": 0}


def timed(callable_: Any, *args: Any, **kwargs: Any) -> tuple[Any, float]:
    started = time.perf_counter(); value = callable_(*args, **kwargs)
    return value, time.perf_counter() - started
