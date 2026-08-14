"""Creative-Authority Hybrid control plane for the bounded V2 architecture proof.

Codex-authored React/Remotion source owns viewer-facing composition.  This module
owns only durable job state, provenance, evidence/rights binding, sandbox checks,
semantic QA, actual dependency accounting, media probes, and public-write gates.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCHEMA_VERSION = "contentops.v2.creative_authority_hybrid.v1"
TASK_ID = "TASK_CONTENTOPS_V2_CODEX_CREATIVE_AUTHORITY_RESTORE_AND_VISUAL_REPAIR_LOOP_V1"
BENCHMARK_ID = "EIA_HORMUZ_CREATIVE_AUTHORITY_ARCHITECTURE_PROOF_V1"
ARTICLE_HASH = "4a61bb93b43a7fb1d2fd016cbec048ddf9460f1de8731e9ba81241c7a1a3cf9e"
EVIDENCE_HASH = "1e87b1815912a3fdf3a59b56a17d343c39204b3b200527fc099771563c93a44a"
PUBLIC_WRITE = False
MAX_CREATIVE_REVISIONS = 4

ACTIVE_STAGES = (
    "DISCOVERED",
    "QUALIFIED",
    "CLAIMED",
    "EVIDENCE_LOCKED",
    "EDITORIAL_READY",
    "STORYBOARD_READY",
    "CREATIVE_SOURCE_READY",
    "KEYFRAMES_READY",
    "PROXY_READY",
    "VISUAL_REVIEW",
    "QA_REVISE",
    "MASTER_READY",
    "OWNER_REVIEW",
)
TERMINAL_STAGES = ("ABSTAINED", "BLOCKED", "FAILED")
ALL_STAGES = frozenset((*ACTIVE_STAGES, *TERMINAL_STAGES))
STAGE_ORDER = {stage: index for index, stage in enumerate(ACTIVE_STAGES)}

ACCEPTED_RIGHTS = frozenset(
    {
        "PUBLIC_DOMAIN",
        "NASA_MEDIA_GUIDELINES_EDITORIAL",
        "CREATIVE_COMMONS_ATTRIBUTION",
        "US_GOVERNMENT_PUBLIC_INFORMATION",
        "CAPITAL_CHRONICLE_OWNED",
    }
)
PROFESSIONAL_AUDIO_PROVIDERS = frozenset({"kokoro", "elevenlabs"})
DIAGNOSTIC_AUDIO_PROVIDERS = frozenset({"windows_sapi_local", "sapi"})
ALLOWED_GENERATED_IMPORTS = frozenset(
    {
        "react",
        "remotion",
        "../lowLevel",
        "../root",
    }
)
FORBIDDEN_SOURCE_PATTERNS = {
    "network": r"\b(fetch|XMLHttpRequest|WebSocket|EventSource)\s*\(",
    "environment": r"\b(process\.env|Deno\.env|import\.meta\.env)\b",
    "process": r"\b(child_process|spawnSync|execSync|execFile|shelljs)\b",
    "filesystem": r"\b(node:fs|require\(['\"]fs['\"]\)|writeFile|unlink|rmSync|mkdirSync)\b",
    "browser_session": r"\b(cookie|localStorage|sessionStorage|indexedDB)\b",
    "remote_code": r"\b(eval|new\s+Function|import\s*\()\b",
    "publication": r"\b(youtube|tiktok|substack|publish|upload|platform[_-]?api)\b",
}


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
class CreativeExecutionProvenance:
    execution_plane: str
    model: str
    reasoning_effort: str
    agent_run_id: str
    prompt_hash: str
    artifact_hash: str
    nine_router_route: None = None
    public_write: bool = False

    def validate(self) -> None:
        if self.execution_plane not in {
            "CODEX_APP_AGENT",
            "CODEX_HEADLESS",
            "CODEX_TASK_SESSION",
        }:
            raise ValueError("creative_execution_plane_not_codex")
        joined = "|".join((self.execution_plane, self.model, self.agent_run_id)).lower()
        if any(token in joined for token in ("new/", "cx/", "nine_router", "9router")):
            raise ValueError("nine_router_creative_provenance_forbidden")
        if self.nine_router_route is not None:
            raise ValueError("nine_router_route_must_be_null")
        if self.public_write is not False:
            raise ValueError("creative_provenance_public_write_must_be_false")
        for name, value in (
            ("model", self.model),
            ("reasoning_effort", self.reasoning_effort),
            ("agent_run_id", self.agent_run_id),
            ("prompt_hash", self.prompt_hash),
            ("artifact_hash", self.artifact_hash),
        ):
            if not value:
                raise ValueError(f"creative_provenance_missing:{name}")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "execution_plane": self.execution_plane,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "agent_run_id": self.agent_run_id,
            "prompt_hash": self.prompt_hash,
            "artifact_hash": self.artifact_hash,
            "nine_router_route": self.nine_router_route,
            "public_write": self.public_write,
        }


class CreativeAuthorityLedger:
    """SQLite job/outbox and immutable stage ledger isolated from V1 state."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS candidates(
              candidate_id TEXT PRIMARY KEY,
              benchmark_id TEXT NOT NULL,
              article_hash TEXT NOT NULL,
              evidence_hash TEXT NOT NULL,
              qualification_reason TEXT NOT NULL,
              public_write INTEGER NOT NULL CHECK(public_write=0)
            );
            CREATE TABLE IF NOT EXISTS jobs(
              job_id TEXT PRIMARY KEY,
              candidate_id TEXT NOT NULL,
              run_id TEXT NOT NULL UNIQUE,
              state TEXT NOT NULL,
              claimed_by TEXT,
              input_hash TEXT NOT NULL,
              retry_count INTEGER NOT NULL DEFAULT 0,
              revision_count INTEGER NOT NULL DEFAULT 0,
              render_count INTEGER NOT NULL DEFAULT 0,
              selective_rerender_count INTEGER NOT NULL DEFAULT 0,
              operator_interventions INTEGER NOT NULL DEFAULT 0,
              wall_clock_seconds REAL NOT NULL DEFAULT 0,
              failure_class TEXT,
              public_write INTEGER NOT NULL CHECK(public_write=0),
              FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
            );
            CREATE TABLE IF NOT EXISTS stages(
              job_id TEXT NOT NULL,
              stage TEXT NOT NULL,
              attempt INTEGER NOT NULL,
              input_hash TEXT NOT NULL,
              output_hash TEXT NOT NULL,
              status TEXT NOT NULL,
              model_or_tool TEXT NOT NULL,
              execution_plane TEXT NOT NULL,
              runtime_seconds REAL NOT NULL,
              retry_count INTEGER NOT NULL,
              revision_count INTEGER NOT NULL,
              artifact_refs_json TEXT NOT NULL,
              failure_class TEXT,
              receipt_json TEXT NOT NULL,
              PRIMARY KEY(job_id,stage,attempt),
              FOREIGN KEY(job_id) REFERENCES jobs(job_id)
            );
            CREATE TABLE IF NOT EXISTS artifacts(
              job_id TEXT NOT NULL,
              name TEXT NOT NULL,
              path TEXT NOT NULL,
              sha256 TEXT NOT NULL,
              PRIMARY KEY(job_id,name),
              FOREIGN KEY(job_id) REFERENCES jobs(job_id)
            );
            CREATE TABLE IF NOT EXISTS defects(
              job_id TEXT NOT NULL,
              defect_id TEXT NOT NULL,
              scene_id TEXT NOT NULL,
              frame_or_time TEXT NOT NULL,
              screenshot_path TEXT NOT NULL,
              defect_type TEXT NOT NULL,
              severity TEXT NOT NULL,
              expected_outcome TEXT NOT NULL,
              source_surface TEXT NOT NULL,
              repair_receipt TEXT,
              before_hash TEXT,
              after_hash TEXT,
              PRIMARY KEY(job_id,defect_id),
              FOREIGN KEY(job_id) REFERENCES jobs(job_id)
            );
            """
        )
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def create_job(self, input_hash: str) -> dict[str, str]:
        candidate_id = f"candidate-{ARTICLE_HASH[:16]}"
        run_id = f"architecture-proof-{uuid.uuid4().hex}"
        job_id = f"{candidate_id}-creative-authority"
        self.db.execute(
            "INSERT OR IGNORE INTO candidates VALUES(?,?,?,?,?,0)",
            (
                candidate_id,
                BENCHMARK_ID,
                ARTICLE_HASH,
                EVIDENCE_HASH,
                "governed_primary_evidence+physical_mechanism+institutional_video_opportunity",
            ),
        )
        existing = self.db.execute("SELECT run_id,state FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if existing:
            self.db.commit()
            return {"job_id": job_id, "run_id": str(existing["run_id"]), "state": str(existing["state"])}
        self.db.execute(
            "INSERT INTO jobs(job_id,candidate_id,run_id,state,input_hash,public_write) VALUES(?,?,?,?,?,0)",
            (job_id, candidate_id, run_id, "QUALIFIED", input_hash),
        )
        self.db.commit()
        return {"job_id": job_id, "run_id": run_id, "state": "QUALIFIED"}

    def claim(self, job_id: str, worker_id: str) -> bool:
        result = self.db.execute(
            "UPDATE jobs SET state='CLAIMED',claimed_by=? WHERE job_id=? AND state='QUALIFIED'",
            (worker_id, job_id),
        )
        self.db.commit()
        return result.rowcount == 1

    def checkpoint(
        self,
        job_id: str,
        stage: str,
        input_hash: str,
        output: Any,
        *,
        model_or_tool: str,
        execution_plane: str,
        runtime_seconds: float,
        artifact_refs: Sequence[str] = (),
        retry_count: int = 0,
        revision_count: int = 0,
        status: str = "PASS",
        failure_class: str | None = None,
    ) -> str:
        if stage not in ALL_STAGES:
            raise ValueError(f"unknown_stage:{stage}")
        current = self.db.execute("SELECT state FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if current is None:
            raise ValueError("job_not_found")
        current_state = str(current["state"])
        if stage in STAGE_ORDER and current_state in STAGE_ORDER:
            if STAGE_ORDER[stage] < STAGE_ORDER[current_state]:
                raise ValueError(f"stage_regression:{current_state}->{stage}")
        if revision_count > MAX_CREATIVE_REVISIONS:
            raise ValueError("creative_revision_budget_exceeded")
        attempt = int(
            self.db.execute(
                "SELECT COALESCE(MAX(attempt),0)+1 FROM stages WHERE job_id=? AND stage=?",
                (job_id, stage),
            ).fetchone()[0]
        )
        output_hash = logical_hash(output)
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "status": status,
            "public_write": False,
            "failure_class": failure_class,
        }
        self.db.execute(
            "INSERT INTO stages VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                job_id,
                stage,
                attempt,
                input_hash,
                output_hash,
                status,
                model_or_tool,
                execution_plane,
                float(runtime_seconds),
                int(retry_count),
                int(revision_count),
                canonical_json(list(artifact_refs)),
                failure_class,
                canonical_json(receipt),
            ),
        )
        self.db.execute(
            "UPDATE jobs SET state=?,retry_count=?,revision_count=?,failure_class=? WHERE job_id=?",
            (stage, int(retry_count), int(revision_count), failure_class, job_id),
        )
        self.db.commit()
        return output_hash

    def record_artifact(self, job_id: str, name: str, path: Path) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO artifacts VALUES(?,?,?,?)",
            (job_id, name, str(path), sha256_file(path)),
        )
        self.db.commit()

    def record_defect(self, job_id: str, defect: Mapping[str, Any]) -> None:
        required = (
            "defect_id",
            "scene_id",
            "frame_or_time",
            "screenshot_path",
            "defect_type",
            "severity",
            "expected_outcome",
            "source_surface",
        )
        missing = [key for key in required if not defect.get(key)]
        if missing:
            raise ValueError(f"defect_fields_missing:{','.join(missing)}")
        self.db.execute(
            "INSERT OR REPLACE INTO defects VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                job_id,
                defect["defect_id"],
                defect["scene_id"],
                defect["frame_or_time"],
                defect["screenshot_path"],
                defect["defect_type"],
                defect["severity"],
                defect["expected_outcome"],
                defect["source_surface"],
                defect.get("repair_receipt"),
                defect.get("before_hash"),
                defect.get("after_hash"),
            ),
        )
        self.db.commit()

    def reconcile_metrics(
        self,
        job_id: str,
        *,
        render_count: int,
        selective_rerender_count: int,
        revision_count: int,
        operator_interventions: int,
        wall_clock_seconds: float,
    ) -> None:
        """Persist measured aggregate counters without changing the current stage."""
        self.db.execute(
            """
            UPDATE jobs
               SET render_count=?, selective_rerender_count=?, revision_count=?,
                   operator_interventions=?, wall_clock_seconds=?
             WHERE job_id=?
            """,
            (
                int(render_count),
                int(selective_rerender_count),
                int(revision_count),
                int(operator_interventions),
                float(wall_clock_seconds),
                job_id,
            ),
        )
        self.db.commit()

    def job_row(self, job_id: str) -> dict[str, Any]:
        row = self.db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise ValueError("job_not_found")
        return dict(row)

    def last_valid_stage(self, job_id: str) -> str | None:
        row = self.db.execute(
            "SELECT stage FROM stages WHERE job_id=? AND status='PASS' ORDER BY rowid DESC LIMIT 1",
            (job_id,),
        ).fetchone()
        return str(row["stage"]) if row else None

    def stage_rows(self, job_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.db.execute("SELECT * FROM stages WHERE job_id=? ORDER BY rowid", (job_id,))]

    def defect_rows(self, job_id: str) -> list[dict[str, Any]]:
        return [dict(row) for row in self.db.execute("SELECT * FROM defects WHERE job_id=? ORDER BY defect_id", (job_id,))]


def validate_creative_source(source: Path, project_root: Path) -> dict[str, Any]:
    resolved = source.resolve()
    root = project_root.resolve()
    if root not in resolved.parents:
        raise ValueError("creative_source_outside_project_root")
    text = source.read_text(encoding="utf-8")
    errors: list[str] = []
    for label, pattern in FORBIDDEN_SOURCE_PATTERNS.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            errors.append(f"forbidden_source:{label}")
    imports = re.findall(r"from\s+['\"]([^'\"]+)['\"]", text)
    for imported in imports:
        if imported not in ALLOWED_GENERATED_IMPORTS:
            errors.append(f"import_not_allowed:{imported}")
    if "CODEX-AUTHORED" not in text.upper() and "CODEX TASK SESSION" not in text.upper():
        errors.append("codex_authorship_marker_missing")
    if "ArchitectureProofShort" not in text or "ArchitectureProofMidform" not in text:
        errors.append("native_short_midform_exports_missing")
    if errors:
        raise ValueError(";".join(errors))
    return {
        "status": "PASS",
        "source": str(resolved),
        "sha256": sha256_file(source),
        "imports": imports,
        "network_calls": 0,
        "environment_reads": 0,
        "process_spawns": 0,
        "filesystem_writes": 0,
        "publication_calls": 0,
        "public_write": False,
    }


def validate_semantics(editorial: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if set(editorial.get("layers") or {}) != {"truth", "analysis", "engagement"}:
        errors.append("truth_analysis_engagement_separation_missing")
    analytical = editorial.get("analytical_map") or {}
    for key in (
        "core_question",
        "what_changed",
        "what_not_changed_yet",
        "physical_mechanism",
        "second_order_channels",
        "confirm",
        "challenge",
        "next_checkpoints",
    ):
        if not analytical.get(key):
            errors.append(f"analytical_map_missing:{key}")
    for variant in ("short_9x16", "midform_16x9"):
        scenes = (editorial.get("variants") or {}).get(variant) or []
        if not scenes:
            errors.append(f"variant_scenes_missing:{variant}")
            continue
        for scene in scenes:
            intent = scene.get("semantic_intent")
            scene_id = scene.get("scene_id") or "unknown"
            visible = scene.get("visible_content") or {}
            if intent == "CONFIRM_CHALLENGE":
                if not visible.get("confirm"):
                    errors.append(f"empty_confirm:{scene_id}")
                if not visible.get("challenge"):
                    errors.append(f"empty_challenge:{scene_id}")
            if intent == "PHYSICAL_CHAIN":
                states = visible.get("states") or []
                if len(states) < 2 or any(not row.get("representation") for row in states):
                    errors.append(f"physical_chain_incomplete:{scene_id}")
            if intent == "DOCUMENT_EVIDENCE":
                if not visible.get("document_asset") or not visible.get("source_date") or not visible.get("evidence_region"):
                    errors.append(f"document_evidence_incomplete:{scene_id}")
            if intent == "FORECAST":
                if not visible.get("observation_style") or not visible.get("forecast_style"):
                    errors.append(f"forecast_boundary_not_visible:{scene_id}")
            if intent == "CHECKPOINT_TIMELINE" and not visible.get("checkpoints"):
                errors.append(f"empty_checkpoint_timeline:{scene_id}")
    if errors:
        raise ValueError(";".join(errors))
    return {"status": "PASS", "semantic_scene_count": sum(len(v) for v in editorial["variants"].values()), "errors": [], "public_write": False}


def validate_render_dependencies(
    manifest: Mapping[str, Any],
    asset_universe: Mapping[str, Any],
    creative_source: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    candidates = {str(row["asset_id"]): row for row in asset_universe.get("candidates", [])}
    source_text = creative_source.read_text(encoding="utf-8")
    source_assets = set(re.findall(r"(?:name=|asset\()['\"]([^'\"]+\.(?:png|jpg|jpeg))['\"]", source_text))
    manifest_assets: set[str] = set()
    stats: dict[str, Any] = {}
    for variant, rows in (manifest.get("variants") or {}).items():
        duration = float(manifest["durations_seconds"][variant])
        by_asset: dict[str, float] = {}
        prior: str | None = None
        for row in rows:
            asset_id = str(row["asset_id"])
            asset_file = str(row["asset_file"])
            manifest_assets.add(asset_file)
            candidate = candidates.get(asset_id)
            if not candidate:
                errors.append(f"unknown_asset:{variant}:{asset_id}")
                continue
            if candidate.get("rights_status") not in ACCEPTED_RIGHTS:
                errors.append(f"rights_not_accepted:{variant}:{asset_id}")
            if asset_file != Path(str(candidate["relative_public_path"])).name:
                errors.append(f"asset_file_mismatch:{variant}:{asset_id}")
            seconds = float(row["end_seconds"]) - float(row["start_seconds"])
            if seconds <= 0:
                errors.append(f"invalid_dependency_time:{variant}:{asset_id}")
            by_asset[asset_id] = by_asset.get(asset_id, 0.0) + seconds
            if prior == asset_id:
                errors.append(f"consecutive_asset_reuse:{variant}:{asset_id}")
            prior = asset_id
        concentration = {asset_id: seconds / duration for asset_id, seconds in by_asset.items()}
        for asset_id, share in concentration.items():
            if share > 0.151:
                errors.append(f"asset_concentration:{variant}:{asset_id}:{share:.3f}")
        stats[variant] = {
            "duration_seconds": duration,
            "asset_use_seconds": by_asset,
            "asset_concentration": concentration,
            "max_concentration": max(concentration.values(), default=0.0),
        }
    missing_manifest = source_assets - manifest_assets
    unbound_manifest = manifest_assets - source_assets
    if missing_manifest:
        errors.append(f"source_assets_missing_from_manifest:{sorted(missing_manifest)}")
    if unbound_manifest:
        errors.append(f"manifest_assets_not_in_source:{sorted(unbound_manifest)}")
    if errors:
        raise ValueError(";".join(errors))
    return {
        "status": "PASS",
        "source_asset_literals": sorted(source_assets),
        "manifest_asset_files": sorted(manifest_assets),
        "stats": stats,
        "public_write": False,
    }


def validate_visual_safety(layout_report: Mapping[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for variant, rows in (layout_report.get("variants") or {}).items():
        for row in rows:
            scene_id = row.get("scene_id") or "unknown"
            if row.get("text_overflow"):
                errors.append(f"text_overflow:{variant}:{scene_id}")
            if row.get("source_collision"):
                errors.append(f"source_collision:{variant}:{scene_id}")
            if row.get("caption_collision"):
                errors.append(f"caption_collision:{variant}:{scene_id}")
            if row.get("native_label_duplicate"):
                errors.append(f"native_label_duplicate:{variant}:{scene_id}")
            if float(row.get("min_text_px") or 0) < float(row.get("required_min_text_px") or 0):
                errors.append(f"phone_text_too_small:{variant}:{scene_id}")
            if row.get("document_region_visible") is False:
                errors.append(f"document_region_not_visible:{variant}:{scene_id}")
    if errors:
        raise ValueError(";".join(errors))
    return {"status": "PASS", "errors": [], "public_write": False}


def validate_audio_eligibility(provider: str, media_candidate: bool = True) -> dict[str, Any]:
    normalized = provider.strip().lower()
    if media_candidate and normalized in DIAGNOSTIC_AUDIO_PROVIDERS:
        raise ValueError("diagnostic_audio_not_professional_media_eligible")
    if media_candidate and normalized not in PROFESSIONAL_AUDIO_PROVIDERS:
        raise ValueError("professional_audio_provider_unavailable")
    return {"status": "PASS", "provider": normalized, "professional_media_eligible": media_candidate, "sapi_used": False}


def probe_media(path: Path) -> dict[str, Any]:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def measure_loudness(path: Path) -> dict[str, float]:
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "NUL",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    matches = list(re.finditer(r"\{\s*\"input_i\".*?\}", result.stderr, flags=re.DOTALL))
    if not matches:
        raise RuntimeError("ffmpeg_loudnorm_json_missing")
    value = json.loads(matches[-1].group(0))
    return {"integrated_lufs": float(value["input_i"]), "true_peak_dbtp": float(value["input_tp"])}


def write_srt(scenes: Sequence[Mapping[str, Any]], path: Path) -> None:
    lines: list[str] = []
    at = 0.0

    def stamp(value: float) -> str:
        millis = int(round(value * 1000))
        return f"{millis//3600000:02}:{millis//60000%60:02}:{millis//1000%60:02},{millis%1000:03}"

    for index, scene in enumerate(scenes, 1):
        end = at + float(scene["duration_seconds"])
        lines.extend((str(index), f"{stamp(at)} --> {stamp(end)}", str(scene["narration"]), ""))
        at = end
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def zero_public_write_manifest() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "authority": "ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY",
        "public_write": False,
        "platform_actions": [],
        "uploads": [],
        "browser_cdp_actions": [],
        "v1_mutations": [],
        "v2_02_started": False,
    }


def copy_governed_assets(asset_universe: Mapping[str, Any], destination: Path) -> list[dict[str, Any]]:
    destination.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, Any]] = []
    for row in asset_universe.get("candidates", []):
        if row.get("rights_status") not in ACCEPTED_RIGHTS:
            raise ValueError(f"asset_rights_not_accepted:{row.get('asset_id')}")
        source = Path(str(row["local_path"]))
        target = destination / Path(str(row["relative_public_path"])).name
        if not source.is_file():
            raise FileNotFoundError(f"governed_asset_missing:{source}")
        if not target.exists() or sha256_file(target) != str(row["sha256"]):
            shutil.copy2(source, target)
        if sha256_file(target) != str(row["sha256"]):
            raise ValueError(f"governed_asset_hash_mismatch:{row.get('asset_id')}")
        copied.append({"asset_id": row["asset_id"], "path": str(target), "sha256": row["sha256"], "rights_status": row["rights_status"]})
    return copied


def timed_stage(callable_: Any, *args: Any, **kwargs: Any) -> tuple[Any, float]:
    started = time.perf_counter()
    return callable_(*args, **kwargs), time.perf_counter() - started
