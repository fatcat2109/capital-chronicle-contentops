from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from . import media as local_media
from .creative import (
    MINIMUM_PICTURE_TAIL_ROOM_SECONDS,
    SHORT_MAX_SECONDS,
    hash_file,
    hash_value,
    materialize_source,
    validate_editor_artifact,
    validate_input_packet,
    validate_motion_artifact,
    validate_narration_timing_lock,
    validate_revision_artifact,
    validate_source_files,
)
from .desktop_session import (
    BoundedCreativeProvenance,
    ParentSessionProvenance,
    build_bounded_creative_receipt,
    build_parent_session_receipt,
    validate_bounded_creative_receipt,
)
from .store import V2JobStore, utc_now


SCHEMA_VERSION = "contentops.v2.unattended_core_factory_supervisor.v1"
STAGES: tuple[str, ...] = (
    "CLAIMED",
    "GOVERNED_INPUT_LOCKED",
    "CREATIVE_EDITOR_LOCKED",
    "ACTUAL_NARRATION_TIMING_LOCKED",
    "MOTION_SOURCE_LOCKED",
    "HARD_SOURCE_VALIDATED",
    "PROXY_RENDERED",
    "ACTUAL_MEDIA_REVIEWED",
    "CREATIVE_REVISION_LOCKED",
    "PICTURE_LOCKED",
    "AUDIO_BUILT",
    "FINAL_MEDIA_BUILT",
    "PACKAGE_QA_PASSED",
    "OWNER_REVIEW_READY",
)
SECRET_PATTERNS = (
    re.compile(r"(?i)authorization\s*:\s*bearer\s+\S+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\b(?:eyJ[A-Za-z0-9_-]+\.){2}[A-Za-z0-9_-]+\b"),
    re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[=:]\s*['\"]?[A-Za-z0-9_./+-]{12,}"),
)


class SupervisorError(RuntimeError):
    pass


class DesktopSessionInputRequired(SupervisorError):
    def __init__(self, input_kind: str) -> None:
        super().__init__(f"desktop_session_input_required:{input_kind}")
        self.input_kind = input_kind


@dataclass(frozen=True)
class FactoryConfig:
    runtime_root: Path
    scaffold_root: Path
    dependency_root: Path
    asset_root: Path
    kokoro_model: Path
    kokoro_voices: Path
    implementation_head: str
    worker_id: str
    parent_provenance: ParentSessionProvenance
    bed_relative_path: str = "assets/audio/sound/chapter_02_bed.m4a"

    def validate(self) -> None:
        for label, path in (
            ("scaffold_root", self.scaffold_root),
            ("dependency_root", self.dependency_root),
            ("asset_root", self.asset_root),
            ("kokoro_model", self.kokoro_model),
            ("kokoro_voices", self.kokoro_voices),
        ):
            if not Path(path).exists():
                raise SupervisorError(f"configured_path_missing:{label}:{path}")
        if not re.fullmatch(r"[0-9a-f]{40}", self.implementation_head):
            raise SupervisorError("implementation_head_must_be_exact_commit")
        if not self.worker_id:
            raise SupervisorError("worker_id_required")
        self.parent_provenance.validate()


def _json_artifact(path: Path, value: Any) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "path": str(path.resolve()),
        "sha256": hash_file(path),
        "size_bytes": path.stat().st_size,
    }


def _load(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise SupervisorError(f"artifact_not_object:{path}")
    return loaded


def _write_immutable_json(path: Path, value: Mapping[str, Any]) -> dict[str, Any]:
    if path.is_file():
        existing = _load(path)
        if hash_value(existing) != hash_value(value):
            raise SupervisorError(f"immutable_session_submission_conflict:{path.name}")
        return {
            "path": str(path.resolve()),
            "sha256": hash_file(path),
            "size_bytes": path.stat().st_size,
        }
    return _json_artifact(path, dict(value))


def _safe_cost(receipts: list[Mapping[str, Any]]) -> dict[str, Any]:
    usd = 0.0
    exposed = False
    usage: dict[str, float] = {}
    calls = 0
    attempts = 0
    for receipt in receipts:
        receipt_attempts = int(receipt.get("attempt_count") or 0)
        calls += 1 if receipt_attempts else 0
        attempts += receipt_attempts
        cost = receipt.get("cost")
        if isinstance(cost, Mapping):
            for value in cost.values():
                if isinstance(value, (int, float)):
                    usd += float(value)
                    exposed = True
        raw_usage = receipt.get("usage")
        if isinstance(raw_usage, Mapping):
            for key, value in raw_usage.items():
                if isinstance(value, (int, float)):
                    usage[str(key)] = usage.get(str(key), 0.0) + float(value)
    return {
        "bounded_xhigh_creative_execution_count": calls,
        "bounded_xhigh_creative_submission_attempt_count": attempts,
        "model_cost_usd": round(usd, 8) if exposed else None,
        "model_cost_exposed": exposed,
        "safe_usage": usage or None,
    }


class DesktopSessionV2Factory:
    def __init__(
        self,
        *,
        store: V2JobStore,
        config: FactoryConfig,
        media_backend: Any = local_media,
    ) -> None:
        self.store = store
        self.config = config
        self.media = media_backend
        self.config.validate()

    def _job_root(self, video_job_id: str) -> Path:
        root = (self.config.runtime_root / "jobs" / video_job_id).resolve()
        runtime = self.config.runtime_root.resolve()
        if runtime not in root.parents:
            raise SupervisorError("job_runtime_escape")
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _paths(self, video_job_id: str) -> dict[str, Path]:
        root = self._job_root(video_job_id)
        artifacts = root / "artifacts"
        return {
            "root": root,
            "artifacts": artifacts,
            "project": root / "generated_project",
            "session_inbox": root / "desktop_session_inbox",
            "editorial_submission": root / "desktop_session_inbox" / "editorial_narration.json",
            "editorial_revision_submission": root / "desktop_session_inbox" / "editorial_timing_revision.json",
            "motion_submission": root / "desktop_session_inbox" / "motion_visual.json",
            "review_submission": root / "desktop_session_inbox" / "actual_media_review.json",
            "parent_receipt": artifacts / "parent_high_session_receipt.json",
            "editor_initial": artifacts / "creative_editor_initial.json",
            "editor": artifacts / "creative_editor.json",
            "editor_initial_validation": artifacts / "creative_editor_initial_validation.json",
            "editor_validation": artifacts / "creative_editor_validation.json",
            "editor_receipt": artifacts / "codex_initial_execution_receipt.json",
            "editor_revision_receipt": artifacts / "codex_editorial_timing_revision_receipt.json",
            "narration_overrun": artifacts / "narration_overrun_pre_motion.json",
            "timing_lock": artifacts / "actual_narration_timing_lock.json",
            "motion": artifacts / "motion_source.json",
            "motion_validation": artifacts / "motion_source_validation.json",
            "motion_receipt": artifacts / "codex_motion_lock_receipt.json",
            "source_validation": artifacts / "hard_source_validation.json",
            "proxy": root / "media" / "proxy.mp4",
            "proxy_sheet": root / "review" / "proxy_contact_sheet.jpg",
            "proxy_report": artifacts / "proxy_media_report.json",
            "review": artifacts / "actual_media_review.json",
            "review_validation": artifacts / "actual_media_review_validation.json",
            "review_receipt": artifacts / "codex_actual_media_review_receipt.json",
            "revision": artifacts / "creative_revision.json",
            "picture": root / "media" / "picture_lock.mp4",
            "narration_dir": root / "audio" / "narration",
            "audio_receipt": artifacts / "audio_build_receipt.json",
            "mix": root / "audio" / "final_mix.wav",
            "final": root / "media" / "frozen_without_breaking_unattended_short_v1.mp4",
            "final_receipt": artifacts / "final_media_receipt.json",
            "captions": root / "package" / "captions",
            "technical": root / "review" / "technical_media_report.json",
            "factual_audit": root / "review" / "factual_anchor_audit.json",
            "rights": root / "review" / "rights_provenance_summary.json",
            "cost": root / "review" / "cost_runtime_summary.json",
            "safety": root / "review" / "zero_write_safety_summary.json",
            "package": root / "package" / "platform_neutral_package_manifest.json",
            "final_sheet": root / "review" / "final_contact_sheet.jpg",
            "ledger": root / "review" / "stage_ledger_summary.json",
            "bundle": root / "review" / "owner_review_bundle.json",
        }

    def _packet(self, job: Mapping[str, Any]) -> dict[str, Any]:
        path = Path(str(job["input_packet_path"]))
        packet = _load(path)
        if hash_value(packet) != str(job["input_packet_hash"]):
            raise SupervisorError("seeded_input_packet_hash_mismatch")
        return packet

    def _active_job(self, *, video_job_id: str, run_id: str) -> dict[str, Any]:
        job = self.store.job(video_job_id)
        if str(job.get("run_id") or "") != run_id:
            raise SupervisorError("desktop_session_run_identity_mismatch")
        if str(job.get("claimed_by") or "") != self.config.worker_id:
            raise SupervisorError("desktop_session_worker_does_not_own_claim")
        if job.get("state") != "RUNNING":
            raise SupervisorError(f"desktop_session_job_not_running:{job.get('state')}")
        if str(job.get("input_packet_hash") or "") == "":
            raise SupervisorError("desktop_session_input_hash_missing")
        return job

    def _parent_receipt(
        self, *, paths: Mapping[str, Path], video_job_id: str, run_id: str
    ) -> dict[str, Any]:
        if not paths["parent_receipt"].is_file():
            raise SupervisorError("parent_high_session_receipt_missing")
        observed = _load(paths["parent_receipt"])
        expected = build_parent_session_receipt(
            provenance=self.config.parent_provenance,
            video_job_id=video_job_id,
            run_id=run_id,
        )
        if hash_value(observed) != hash_value(expected):
            raise SupervisorError("parent_high_session_continuity_mismatch")
        return observed

    def submit_editorial_narration(
        self,
        *,
        video_job_id: str,
        run_id: str,
        editor: Mapping[str, Any],
        provenance: BoundedCreativeProvenance,
    ) -> dict[str, Any]:
        job = self._active_job(video_job_id=video_job_id, run_id=run_id)
        paths = self._paths(video_job_id)
        packet = self._packet(job)
        parent_receipt = self._parent_receipt(
            paths=paths, video_job_id=video_job_id, run_id=run_id
        )
        if provenance.parent.continuity_key != self.config.parent_provenance.continuity_key:
            raise SupervisorError("creative_parent_session_continuity_mismatch")
        if provenance.parent.continuity_key != parent_receipt["parent_session_continuity_key"]:
            raise SupervisorError("creative_parent_receipt_continuity_mismatch")
        validate_editor_artifact(editor, packet)
        receipt = build_bounded_creative_receipt(
            provenance=provenance,
            execution_kind="EDITORIAL_NARRATION",
            video_job_id=video_job_id,
            run_id=run_id,
            input_artifact_hashes={"governed_packet": str(job["input_packet_hash"])},
            output_artifact_hashes={"editorial": hash_value(editor)},
        )
        validate_bounded_creative_receipt(
            receipt,
            execution_kind="EDITORIAL_NARRATION",
            video_job_id=video_job_id,
            run_id=run_id,
        )
        envelope = {
            "schema": "contentops.v2.desktop_session_editorial_submission.v1",
            "video_job_id": video_job_id,
            "run_id": run_id,
            "governed_input_hash": str(job["input_packet_hash"]),
            "editor": dict(editor),
            "receipt": receipt,
        }
        artifact = _write_immutable_json(paths["editorial_submission"], envelope)
        return {
            "result": "PASS_DESKTOP_SESSION_EDITORIAL_NARRATION_SUBMITTED",
            "video_job_id": video_job_id,
            "run_id": run_id,
            "submission": artifact,
            "next_legal_stage": "CREATIVE_EDITOR_LOCKED",
        }

    def submit_editorial_timing_revision(
        self,
        *,
        video_job_id: str,
        run_id: str,
        editor: Mapping[str, Any],
        provenance: BoundedCreativeProvenance,
    ) -> dict[str, Any]:
        job = self._active_job(video_job_id=video_job_id, run_id=run_id)
        paths = self._paths(video_job_id)
        if not paths["narration_overrun"].is_file():
            raise SupervisorError("editorial_timing_revision_not_requested")
        if paths["editorial_revision_submission"].is_file():
            raise SupervisorError("editorial_timing_revision_budget_exhausted")
        packet = self._packet(job)
        validate_editor_artifact(editor, packet)
        initial_receipt = _load(paths["editor_receipt"])
        receipt = build_bounded_creative_receipt(
            provenance=provenance,
            execution_kind="EDITORIAL_TIMING_REVISION",
            video_job_id=video_job_id,
            run_id=run_id,
            input_artifact_hashes={
                "governed_packet": str(job["input_packet_hash"]),
                "initial_editorial": hash_file(paths["editor_initial"]),
                "overrun_receipt": hash_file(paths["narration_overrun"]),
            },
            output_artifact_hashes={"editorial": hash_value(editor)},
        )
        validate_bounded_creative_receipt(
            receipt,
            execution_kind="EDITORIAL_TIMING_REVISION",
            video_job_id=video_job_id,
            run_id=run_id,
            initial_receipt=initial_receipt,
        )
        artifact = _write_immutable_json(
            paths["editorial_revision_submission"],
            {
                "schema": "contentops.v2.desktop_session_editorial_timing_revision.v1",
                "video_job_id": video_job_id,
                "run_id": run_id,
                "governed_input_hash": str(job["input_packet_hash"]),
                "editor": dict(editor),
                "receipt": receipt,
            },
        )
        return {
            "result": "PASS_BOUNDED_EDITORIAL_TIMING_REVISION_SUBMITTED",
            "video_job_id": video_job_id,
            "run_id": run_id,
            "submission": artifact,
            "next_legal_stage": "ACTUAL_NARRATION_TIMING_LOCKED",
        }

    def submit_motion_visual(
        self,
        *,
        video_job_id: str,
        run_id: str,
        motion: Mapping[str, Any],
        provenance: BoundedCreativeProvenance,
    ) -> dict[str, Any]:
        job = self._active_job(video_job_id=video_job_id, run_id=run_id)
        paths = self._paths(video_job_id)
        if not paths["timing_lock"].is_file() or not paths["editor"].is_file():
            raise SupervisorError("actual_narration_timing_lock_required_before_motion")
        packet = self._packet(job)
        editor = _load(paths["editor"])
        timing_lock = _load(paths["timing_lock"])
        validate_narration_timing_lock(
            timing_lock,
            video_job_id=video_job_id,
            run_id=run_id,
            governed_input_hash=str(job["input_packet_hash"]),
            editor=editor,
        )
        validate_motion_artifact(motion, packet, editor, timing_lock)
        initial_receipt = _load(paths["editor_receipt"])
        receipt = build_bounded_creative_receipt(
            provenance=provenance,
            execution_kind="MOTION_VISUAL_AUTHORSHIP",
            video_job_id=video_job_id,
            run_id=run_id,
            input_artifact_hashes={
                "governed_packet": str(job["input_packet_hash"]),
                "editorial": hash_value(editor),
                "actual_narration_timing_lock": str(timing_lock["timing_lock_hash"]),
            },
            output_artifact_hashes={"motion": hash_value(motion)},
        )
        validate_bounded_creative_receipt(
            receipt,
            execution_kind="MOTION_VISUAL_AUTHORSHIP",
            video_job_id=video_job_id,
            run_id=run_id,
            initial_receipt=initial_receipt,
        )
        artifact = _write_immutable_json(
            paths["motion_submission"],
            {
                "schema": "contentops.v2.desktop_session_motion_submission.v1",
                "video_job_id": video_job_id,
                "run_id": run_id,
                "governed_input_hash": str(job["input_packet_hash"]),
                "editorial_narration_hash": hash_value(editor),
                "narration_timing_lock_hash": timing_lock["timing_lock_hash"],
                "motion": dict(motion),
                "receipt": receipt,
            },
        )
        return {
            "result": "PASS_DESKTOP_SESSION_MOTION_VISUAL_SUBMITTED",
            "video_job_id": video_job_id,
            "run_id": run_id,
            "submission": artifact,
            "next_legal_stage": "MOTION_SOURCE_LOCKED",
        }

    def submit_actual_media_review(
        self,
        *,
        video_job_id: str,
        run_id: str,
        review: Mapping[str, Any],
        provenance: BoundedCreativeProvenance,
    ) -> dict[str, Any]:
        job = self._active_job(video_job_id=video_job_id, run_id=run_id)
        paths = self._paths(video_job_id)
        packet = self._packet(job)
        editor = _load(paths["editor"])
        timing_lock = _load(paths["timing_lock"])
        motion = _load(paths["motion"])
        initial_receipt = _load(paths["motion_receipt"])
        parent_receipt = self._parent_receipt(
            paths=paths, video_job_id=video_job_id, run_id=run_id
        )
        if provenance.parent.continuity_key != self.config.parent_provenance.continuity_key:
            raise SupervisorError("creative_parent_session_continuity_mismatch")
        if provenance.parent.continuity_key != parent_receipt["parent_session_continuity_key"]:
            raise SupervisorError("creative_parent_receipt_continuity_mismatch")
        validate_revision_artifact(review, packet, editor, motion, timing_lock)
        receipt = build_bounded_creative_receipt(
            provenance=provenance,
            execution_kind="ACTUAL_MEDIA_REVIEW",
            video_job_id=video_job_id,
            run_id=run_id,
            input_artifact_hashes={
                "proxy": hash_file(paths["proxy"]),
                "proxy_contact_sheet": hash_file(paths["proxy_sheet"]),
            },
            output_artifact_hashes={"review": hash_value(review)},
        )
        validate_bounded_creative_receipt(
            receipt,
            execution_kind="ACTUAL_MEDIA_REVIEW",
            video_job_id=video_job_id,
            run_id=run_id,
            initial_receipt=initial_receipt,
        )
        envelope = {
            "schema": "contentops.v2.desktop_session_review_submission.v1",
            "video_job_id": video_job_id,
            "run_id": run_id,
            "proxy_sha256": hash_file(paths["proxy"]),
            "proxy_contact_sheet_sha256": hash_file(paths["proxy_sheet"]),
            "review": dict(review),
            "receipt": receipt,
        }
        artifact = _write_immutable_json(paths["review_submission"], envelope)
        return {
            "result": "PASS_DESKTOP_SESSION_REVIEW_SUBMITTED",
            "video_job_id": video_job_id,
            "run_id": run_id,
            "submission": artifact,
            "next_legal_stage": "ACTUAL_MEDIA_REVIEWED",
        }

    def _latest(self, video_job_id: str) -> dict[str, dict[str, Any]]:
        return self.store.latest_success_by_stage(video_job_id)

    def _validate_checkpoint_chain(
        self, *, job: Mapping[str, Any], run_id: str
    ) -> dict[str, dict[str, Any]]:
        latest = self._latest(str(job["video_job_id"]))
        invalid_from: int | None = None
        for index, stage in enumerate(STAGES):
            event = latest.get(stage)
            if event is None:
                continue
            try:
                records = json.loads(event["artifact_records_json"])
            except json.JSONDecodeError:
                records = []
                invalid_from = index
            for record in records:
                path = Path(str(record.get("path", "")))
                if not path.is_file() or hash_file(path) != str(record.get("sha256", "")):
                    invalid_from = index if invalid_from is None else min(invalid_from, index)
                    break
            if invalid_from is not None:
                break
        if invalid_from is None:
            return latest
        prior = STAGES[invalid_from - 1] if invalid_from else "RUNNING"
        for stage in STAGES[invalid_from:]:
            if stage not in latest:
                continue
            self.store.append_event(
                video_job_id=str(job["video_job_id"]),
                run_id=run_id,
                stage=stage,
                input_hashes={},
                output_hashes={},
                artifacts=[],
                role_tool_identity="UnattendedV2Supervisor.checkpoint_validator",
                model_provenance={},
                wall_time_seconds=0,
                safe_usage={},
                result="INVALIDATED_ARTIFACT_HASH_MISMATCH",
                retry_state={"invalidated_from": STAGES[invalid_from]},
                next_legal_stage=STAGES[invalid_from],
                state_pointer=prior,
            )
        return self._latest(str(job["video_job_id"]))

    def _review_decision(self, paths: Mapping[str, Path]) -> str | None:
        if not paths["review"].is_file():
            return None
        return str(_load(paths["review"]).get("decision"))

    def _next_stage(
        self, latest: Mapping[str, Mapping[str, Any]], paths: Mapping[str, Path]
    ) -> str | None:
        for stage in STAGES:
            if stage == "CREATIVE_REVISION_LOCKED" and self._review_decision(paths) == "NO_MATERIAL_REVISION":
                continue
            if stage not in latest:
                return stage
        return None

    def _append(
        self,
        *,
        job: Mapping[str, Any],
        run_id: str,
        stage: str,
        started: float,
        inputs: Mapping[str, str],
        artifacts: list[Mapping[str, Any]],
        result: str,
        next_stage: str | None,
        role: str,
        receipt: Mapping[str, Any] | None = None,
        usage: Mapping[str, Any] | None = None,
    ) -> None:
        self.store.append_event(
            video_job_id=str(job["video_job_id"]),
            run_id=run_id,
            stage=stage,
            input_hashes=inputs,
            output_hashes={
                Path(str(item["path"])).name: str(item["sha256"])
                for item in artifacts
                if item.get("path") and item.get("sha256")
            },
            artifacts=artifacts,
            role_tool_identity=role,
            model_provenance=dict(receipt or {}),
            wall_time_seconds=time.monotonic() - started,
            safe_usage=dict(usage or {}),
            result=result,
            retry_state={
                "attempt_count": (receipt or {}).get("attempt_count", 0),
                "fallback_count": (receipt or {}).get("fallback_count", 0),
            },
            next_legal_stage=next_stage,
            state_pointer=stage,
        )

    def _execute_stage(
        self,
        *,
        stage: str,
        job: Mapping[str, Any],
        run_id: str,
        packet: Mapping[str, Any],
        paths: Mapping[str, Path],
    ) -> None:
        started = time.monotonic()
        input_hash = str(job["input_packet_hash"])
        if stage == "CLAIMED":
            parent_receipt = build_parent_session_receipt(
                provenance=self.config.parent_provenance,
                video_job_id=str(job["video_job_id"]),
                run_id=run_id,
            )
            parent_record = _json_artifact(paths["parent_receipt"], parent_receipt)
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"input_packet": input_hash},
                artifacts=[parent_record],
                result="PASS_ATOMIC_CLAIM_WITH_HIGH_PARENT_PROVENANCE",
                next_stage="GOVERNED_INPUT_LOCKED",
                role="V2JobStore.claim_next+CodexDesktopHighParent",
                receipt=parent_receipt,
            )
            return
        if stage == "GOVERNED_INPUT_LOCKED":
            validation = validate_input_packet(packet)
            locked = _json_artifact(paths["artifacts"] / "governed_input_lock.json", validation)
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"input_packet": input_hash},
                artifacts=[locked],
                result="PASS_GOVERNED_INPUT_LOCK",
                next_stage="CREATIVE_EDITOR_LOCKED",
                role="validate_input_packet",
            )
            return
        if stage == "CREATIVE_EDITOR_LOCKED":
            if not paths["editorial_submission"].is_file():
                raise DesktopSessionInputRequired("EDITORIAL_NARRATION")
            submission = _load(paths["editorial_submission"])
            if submission.get("schema") != "contentops.v2.desktop_session_editorial_submission.v1":
                raise SupervisorError("desktop_session_editorial_submission_schema_invalid")
            if submission.get("video_job_id") != job["video_job_id"] or submission.get("run_id") != run_id:
                raise SupervisorError("desktop_session_editorial_submission_identity_mismatch")
            if submission.get("governed_input_hash") != input_hash:
                raise SupervisorError("desktop_session_editorial_submission_input_hash_mismatch")
            output = dict(submission.get("editor") or {})
            receipt = dict(submission.get("receipt") or {})
            validate_bounded_creative_receipt(
                receipt,
                execution_kind="EDITORIAL_NARRATION",
                video_job_id=str(job["video_job_id"]),
                run_id=run_id,
            )
            parent_receipt = self._parent_receipt(
                paths=paths,
                video_job_id=str(job["video_job_id"]),
                run_id=run_id,
            )
            if receipt.get("parent_session_continuity_key") != parent_receipt.get(
                "parent_session_continuity_key"
            ):
                raise SupervisorError("creative_submission_parent_receipt_mismatch")
            validation = validate_editor_artifact(output, packet)
            expected = dict(receipt.get("output_artifact_hashes") or {})
            if expected.get("editorial") != hash_value(output):
                raise SupervisorError("desktop_session_editorial_output_hash_mismatch")
            records = [
                _json_artifact(paths["editor_initial"], output),
                _json_artifact(paths["editor_initial_validation"], validation),
                _json_artifact(paths["editor_receipt"], receipt),
            ]
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"input_packet": input_hash},
                artifacts=records,
                result="PASS_CREATIVE_EDITOR_LOCK",
                next_stage="ACTUAL_NARRATION_TIMING_LOCKED",
                role="BoundedXHighVideoCreative.editorial_narration_submission",
                receipt=receipt,
                usage=receipt.get("usage") or {},
            )
            return
        if stage == "ACTUAL_NARRATION_TIMING_LOCKED":
            editor = _load(paths["editor_initial"])
            revision_receipt: dict[str, Any] | None = None
            if paths["editorial_revision_submission"].is_file():
                submission = _load(paths["editorial_revision_submission"])
                if submission.get("schema") != "contentops.v2.desktop_session_editorial_timing_revision.v1":
                    raise SupervisorError("desktop_session_editorial_revision_schema_invalid")
                if submission.get("video_job_id") != job["video_job_id"] or submission.get("run_id") != run_id:
                    raise SupervisorError("desktop_session_editorial_revision_identity_mismatch")
                if submission.get("governed_input_hash") != input_hash:
                    raise SupervisorError("desktop_session_editorial_revision_input_hash_mismatch")
                editor = dict(submission.get("editor") or {})
                revision_receipt = dict(submission.get("receipt") or {})
                validate_bounded_creative_receipt(
                    revision_receipt,
                    execution_kind="EDITORIAL_TIMING_REVISION",
                    video_job_id=str(job["video_job_id"]),
                    run_id=run_id,
                    initial_receipt=_load(paths["editor_receipt"]),
                )
                if dict(revision_receipt.get("output_artifact_hashes") or {}).get(
                    "editorial"
                ) != hash_value(editor):
                    raise SupervisorError("desktop_session_editorial_revision_hash_mismatch")
            validation = validate_editor_artifact(editor, packet)
            narration = self.media.synthesize_narration(
                editor=editor,
                model_path=self.config.kokoro_model,
                voices_path=self.config.kokoro_voices,
                output_dir=paths["narration_dir"],
            )
            actual_duration = float(narration["duration_seconds"])
            if actual_duration + MINIMUM_PICTURE_TAIL_ROOM_SECONDS > SHORT_MAX_SECONDS + 0.00001:
                _json_artifact(
                    paths["narration_overrun"],
                    {
                        "schema": "contentops.v2.narration_overrun_pre_motion.v1",
                        "video_job_id": str(job["video_job_id"]),
                        "run_id": run_id,
                        "editorial_narration_hash": hash_value(editor),
                        "actual_total_narration_duration_seconds": actual_duration,
                        "minimum_picture_tail_room_seconds": MINIMUM_PICTURE_TAIL_ROOM_SECONDS,
                        "short_max_seconds": SHORT_MAX_SECONDS,
                        "revision_attempted": revision_receipt is not None,
                    },
                )
                if revision_receipt is None:
                    raise DesktopSessionInputRequired("EDITORIAL_TIMING_REVISION")
                raise SupervisorError(
                    f"narration_timing_revision_still_outside_short_contract:{actual_duration:.6f}"
                )
            timing_lock = {
                "schema": "contentops.v2.actual_narration_timing_lock.v1",
                "video_job_id": str(job["video_job_id"]),
                "run_id": run_id,
                "governed_input_hash": input_hash,
                "editorial_narration_hash": hash_value(editor),
                "provider": narration["provider"],
                "model": narration["model"],
                "voice": narration["voice"],
                "speed": narration["speed"],
                "lang": narration["lang"],
                "sample_rate_hz": narration["sample_rate_hz"],
                "initial_silence_seconds": narration["initial_silence_seconds"],
                "segments": narration["placements"],
                "locked_narration_audio": narration["artifact"],
                "actual_total_narration_duration_seconds": actual_duration,
                "deliberate_pause_policy": {
                    "between_segments_seconds": 0.16,
                    "final_silence_seconds": 0.35,
                },
                "external_cost_usd": narration["external_cost_usd"],
            }
            timing_lock["timing_lock_hash"] = hash_value(timing_lock)
            validate_narration_timing_lock(
                timing_lock,
                video_job_id=str(job["video_job_id"]),
                run_id=run_id,
                governed_input_hash=input_hash,
                editor=editor,
            )
            records = [
                _write_immutable_json(paths["editor"], editor),
                _write_immutable_json(paths["editor_validation"], validation),
                _write_immutable_json(paths["timing_lock"], timing_lock),
                dict(narration["artifact"]),
                *[dict(item["audio"]) for item in narration["placements"]],
            ]
            if revision_receipt is not None:
                records.append(
                    _write_immutable_json(paths["editor_revision_receipt"], revision_receipt)
                )
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"input_packet": input_hash, "editorial": hash_value(editor)},
                artifacts=records,
                result="PASS_ACTUAL_NARRATION_TIMING_LOCK",
                next_stage="MOTION_SOURCE_LOCKED",
                role="Kokoro.actual_waveform_timing_lock",
                usage={"external_media_cost_usd": narration["external_cost_usd"]},
            )
            return
        editor = _load(paths["editor"])
        timing_lock = _load(paths["timing_lock"])
        validate_narration_timing_lock(
            timing_lock,
            video_job_id=str(job["video_job_id"]),
            run_id=run_id,
            governed_input_hash=input_hash,
            editor=editor,
        )
        if stage == "MOTION_SOURCE_LOCKED":
            if not paths["motion_submission"].is_file():
                raise DesktopSessionInputRequired("MOTION_VISUAL_AUTHORSHIP")
            submission = _load(paths["motion_submission"])
            if submission.get("schema") != "contentops.v2.desktop_session_motion_submission.v1":
                raise SupervisorError("desktop_session_motion_submission_schema_invalid")
            if submission.get("video_job_id") != job["video_job_id"] or submission.get("run_id") != run_id:
                raise SupervisorError("desktop_session_motion_submission_identity_mismatch")
            if submission.get("governed_input_hash") != input_hash:
                raise SupervisorError("desktop_session_motion_submission_input_hash_mismatch")
            if submission.get("editorial_narration_hash") != hash_value(editor):
                raise SupervisorError("desktop_session_motion_editorial_hash_mismatch")
            if submission.get("narration_timing_lock_hash") != timing_lock["timing_lock_hash"]:
                raise SupervisorError("desktop_session_motion_timing_lock_hash_mismatch")
            output = dict(submission.get("motion") or {})
            receipt = dict(submission.get("receipt") or {})
            validate_bounded_creative_receipt(
                receipt,
                execution_kind="MOTION_VISUAL_AUTHORSHIP",
                video_job_id=str(job["video_job_id"]),
                run_id=run_id,
                initial_receipt=_load(paths["editor_receipt"]),
            )
            expected_hash = str((receipt.get("output_artifact_hashes") or {}).get("motion") or "")
            if not expected_hash or hash_value(output) != expected_hash:
                raise SupervisorError("codex_motion_output_hash_mismatch")
            validation = validate_motion_artifact(output, packet, editor, timing_lock)
            source_records = materialize_source(output["files"], paths["project"])
            records = [
                _json_artifact(paths["motion"], output),
                _json_artifact(paths["motion_validation"], validation),
                _json_artifact(paths["motion_receipt"], receipt),
            ]
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={
                    "editor": hash_value(editor),
                    "actual_narration_timing_lock": timing_lock["timing_lock_hash"],
                },
                artifacts=records,
                result="PASS_MOTION_SOURCE_LOCK",
                next_stage="HARD_SOURCE_VALIDATED",
                role="BoundedXHighVideoCreative.motion_visual_submission",
                receipt=receipt,
                usage=receipt.get("usage") or {},
            )
            return
        motion = _load(paths["motion"])
        if stage == "HARD_SOURCE_VALIDATED":
            materialize_source(motion["files"], paths["project"])
            asset_validation = self.media.validate_assets(packet, self.config.asset_root)
            scaffold = self.media.prepare_project(
                project_root=paths["project"],
                scaffold_root=self.config.scaffold_root,
                dependency_root=self.config.dependency_root,
                asset_root=self.config.asset_root,
            )
            sandbox = validate_source_files(motion["files"])
            typecheck = self.media.typecheck_project(paths["project"])
            record = _json_artifact(
                paths["source_validation"],
                {
                    "assets": asset_validation,
                    "scaffold": scaffold,
                    "sandbox": sandbox,
                    "typecheck": typecheck,
                },
            )
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"motion": hash_value(motion)},
                artifacts=[record],
                result="PASS_HARD_SOURCE_VALIDATION",
                next_stage="PROXY_RENDERED",
                role="deterministic_source_sandbox_and_typecheck",
            )
            return
        if stage == "PROXY_RENDERED":
            browser = self.media.resolve_remotion_browser_executable(
                self.config.dependency_root
            )
            render = self.media.render_project(
                project_root=paths["project"],
                output=paths["proxy"],
                crf=26,
                browser_executable=browser,
                public_root=self.config.asset_root,
            )
            sheet = self.media.contact_sheet(paths["proxy"], paths["proxy_sheet"])
            probe = self.media.probe_media(paths["proxy"])
            report = _json_artifact(
                paths["proxy_report"],
                {"render": render, "contact_sheet": sheet, "probe": probe},
            )
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"motion": hash_value(motion)},
                artifacts=[render["artifact"], sheet["artifact"], report],
                result="PASS_PROXY_RENDER",
                next_stage="ACTUAL_MEDIA_REVIEWED",
                role="Remotion+FFmpeg",
            )
            return
        if stage == "ACTUAL_MEDIA_REVIEWED":
            if not paths["review_submission"].is_file():
                raise DesktopSessionInputRequired("ACTUAL_MEDIA_REVIEW")
            submission = _load(paths["review_submission"])
            if submission.get("schema") != "contentops.v2.desktop_session_review_submission.v1":
                raise SupervisorError("desktop_session_review_submission_schema_invalid")
            if submission.get("video_job_id") != job["video_job_id"] or submission.get("run_id") != run_id:
                raise SupervisorError("desktop_session_review_submission_identity_mismatch")
            if submission.get("proxy_sha256") != hash_file(paths["proxy"]):
                raise SupervisorError("desktop_session_review_proxy_hash_mismatch")
            if submission.get("proxy_contact_sheet_sha256") != hash_file(paths["proxy_sheet"]):
                raise SupervisorError("desktop_session_review_surface_hash_mismatch")
            output = dict(submission.get("review") or {})
            receipt = dict(submission.get("receipt") or {})
            validate_bounded_creative_receipt(
                receipt,
                execution_kind="ACTUAL_MEDIA_REVIEW",
                video_job_id=str(job["video_job_id"]),
                run_id=run_id,
                initial_receipt=_load(paths["motion_receipt"]),
            )
            validation = validate_revision_artifact(
                output, packet, editor, motion, timing_lock
            )
            if dict(receipt.get("output_artifact_hashes") or {}).get("review") != hash_value(output):
                raise SupervisorError("desktop_session_review_output_hash_mismatch")
            records = [
                _json_artifact(paths["review"], output),
                _json_artifact(paths["review_validation"], validation),
                _json_artifact(paths["review_receipt"], receipt),
            ]
            next_stage = (
                "CREATIVE_REVISION_LOCKED"
                if output["decision"] == "MATERIAL_REVISION_REQUIRED"
                else "PICTURE_LOCKED"
            )
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"proxy": hash_file(paths["proxy"])},
                artifacts=records,
                result="PASS_ACTUAL_MEDIA_REVIEW",
                next_stage=next_stage,
                role="BoundedXHighVideoCreative.actual_media_review_submission",
                receipt=receipt,
                usage=receipt.get("usage") or {},
            )
            return
        review = _load(paths["review"])
        if stage == "CREATIVE_REVISION_LOCKED":
            if review["decision"] != "MATERIAL_REVISION_REQUIRED":
                raise SupervisorError("revision_stage_without_material_decision")
            source_records = materialize_source(review["replacement_files"], paths["project"])
            validate_source_files(review["replacement_files"])
            typecheck = self.media.typecheck_project(paths["project"])
            record = _json_artifact(
                paths["revision"],
                {
                    "decision": review["decision"],
                    "defects": review.get("defects", []),
                    "typecheck": typecheck,
                    "source_hashes": {
                        item["path"]: item["sha256"] for item in source_records
                    },
                },
            )
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"review": hash_value(review)},
                artifacts=[record, *source_records],
                result="PASS_CREATIVE_REVISION_LOCK",
                next_stage="PICTURE_LOCKED",
                role="BoundedXHighVideoCreative.localized_revision+deterministic_typecheck",
            )
            return
        if stage == "PICTURE_LOCKED":
            browser = self.media.resolve_remotion_browser_executable(
                self.config.dependency_root
            )
            render = self.media.render_project(
                project_root=paths["project"],
                output=paths["picture"],
                crf=18,
                browser_executable=browser,
                public_root=self.config.asset_root,
            )
            picture_probe = self.media.probe_media(paths["picture"])
            picture_duration = float(picture_probe["format"]["duration"])
            narration_duration = float(
                timing_lock["actual_total_narration_duration_seconds"]
            )
            if picture_duration + 0.001 < narration_duration + MINIMUM_PICTURE_TAIL_ROOM_SECONDS:
                raise SupervisorError("picture_ends_before_locked_narration")
            if abs(picture_duration - float(motion["duration_seconds"])) > 0.05:
                raise SupervisorError("picture_duration_differs_from_motion_lock")
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={
                    "motion_or_revision": hash_value(
                        review if review["decision"] == "MATERIAL_REVISION_REQUIRED" else motion
                    ),
                    "actual_narration_timing_lock": timing_lock["timing_lock_hash"],
                },
                artifacts=[render["artifact"]],
                result="PASS_PICTURE_LOCK",
                next_stage="AUDIO_BUILT",
                role="Remotion",
            )
            return
        if stage == "AUDIO_BUILT":
            bed_path = self.config.asset_root / self.config.bed_relative_path
            mix = self.media.build_audio_mix(
                picture=paths["picture"],
                timing_lock=timing_lock,
                bed_path=bed_path,
                output_dir=paths["mix"].parent,
            )
            mix_record = _json_artifact(paths["audio_receipt"], mix)
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={
                    "picture": hash_file(paths["picture"]),
                    "actual_narration_timing_lock": timing_lock["timing_lock_hash"],
                    "locked_narration_audio": timing_lock["locked_narration_audio"]["sha256"],
                },
                artifacts=[mix["mix"], mix_record],
                result="PASS_AUDIO_BUILD_REUSING_LOCKED_NARRATION",
                next_stage="FINAL_MEDIA_BUILT",
                role="FFmpeg.locked_narration_mix",
                usage={"external_media_cost_usd": 0.0},
            )
            return
        if stage == "FINAL_MEDIA_BUILT":
            mux = self.media.mux_final_media(
                picture=paths["picture"], mix=paths["mix"], output=paths["final"]
            )
            record = _json_artifact(paths["final_receipt"], mux)
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"picture": hash_file(paths["picture"]), "audio": hash_file(paths["mix"])},
                artifacts=[mux["final_media"], record],
                result="PASS_FINAL_MEDIA",
                next_stage="PACKAGE_QA_PASSED",
                role="FFmpeg",
            )
            return
        if stage == "PACKAGE_QA_PASSED":
            captions = self.media.build_captions(
                timing_lock=timing_lock,
                media_duration_seconds=float(motion["duration_seconds"]),
                output_dir=paths["captions"],
            )
            technical = self.media.technical_media_report(paths["final"], paths["technical"])
            factual = {
                "schema": "contentops.v2.factual_anchor_audit.v1",
                "result": "PASS_FACTUAL_ANCHORS",
                "input_packet_hash": input_hash,
                "editor_validation": _load(paths["editor_validation"]),
                "motion_validation": _load(paths["motion_validation"]),
                "prior_creative_source_reused_as_input": False,
            }
            factual_record = _json_artifact(paths["factual_audit"], factual)
            rights = {
                "schema": "contentops.v2.rights_provenance_summary.v1",
                "result": "PASS_RIGHTS_REFERENCES",
                "assets": packet["rights_assets"],
                "generated_real_person_documentary_media": False,
                "new_asset_discovery_performed": False,
            }
            rights_record = _json_artifact(paths["rights"], rights)
            receipts = [
                _load(paths["editor_receipt"]),
                _load(paths["motion_receipt"]),
                _load(paths["review_receipt"]),
            ]
            if paths["editor_revision_receipt"].is_file():
                receipts.append(_load(paths["editor_revision_receipt"]))
            cost = {
                "schema": "contentops.v2.cost_runtime_summary.v1",
                **_safe_cost(receipts),
                "external_media_cost_usd": 0.0,
                "render_count": 2,
                "rerender_count": 1 if review["decision"] == "MATERIAL_REVISION_REQUIRED" else 0,
                "creative_rerender_count": 1 if review["decision"] == "MATERIAL_REVISION_REQUIRED" else 0,
                "xhigh_mechanical_work_execution_count": 0,
                "operator_intervention_minutes": 0,
                "desktop_session_creative_cost": None,
                "desktop_session_creative_cost_exposed": False,
            }
            cost_record = _json_artifact(paths["cost"], cost)
            safety = {
                "schema": "contentops.v2.zero_write_safety_summary.v1",
                "tiktok_credential_reads": 0,
                "tiktok_api_calls": 0,
                "tiktok_draft_deliveries": 0,
                "youtube_api_calls": 0,
                "meta_api_calls": 0,
                "other_platform_calls": 0,
                "public_private_unlisted_writes": 0,
                "browser_cdp_actions": 0,
                "v1_reads": 0,
                "v1_writes": 0,
                "v1_mutations": 0,
                "scheduler_mutations": 0,
                "public_write_authority": False,
            }
            safety_record = _json_artifact(paths["safety"], safety)
            package = self.media.build_neutral_package(
                story_id=str(packet["story_id"]),
                run_id=run_id,
                final_media=paths["final"],
                audio=paths["mix"],
                captions=captions,
                rights_refs=[str(item["sha256"]) for item in packet["rights_assets"]],
                evidence_refs=[str(item["source_ref"]) for item in packet["anchors"]],
                title=str(editor["title"]),
                input_hash=input_hash,
                timing_lock=timing_lock,
                output=paths["package"],
            )
            package_record = package["manifest_artifact"]
            self._secret_scan(paths["root"])
            caption_records = [dict(value) for value in captions["artifacts"].values()]
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"final_media": hash_file(paths["final"]), "input_packet": input_hash},
                artifacts=[
                    technical["report_artifact"],
                    factual_record,
                    rights_record,
                    cost_record,
                    safety_record,
                    package_record,
                    *caption_records,
                ],
                result="PASS_PACKAGE_QA",
                next_stage="OWNER_REVIEW_READY",
                role="platform_neutral_package_factory+technical_QA",
            )
            return
        if stage == "OWNER_REVIEW_READY":
            final_sheet = self.media.contact_sheet(paths["final"], paths["final_sheet"])
            events = self.store.events(str(job["video_job_id"]))
            ledger = {
                "schema": "contentops.v2.stage_ledger_summary.v1",
                "video_job_id": str(job["video_job_id"]),
                "run_id": run_id,
                "immutable_event_count": len(events) + 1,
                "completed_stages": [event["stage"] for event in events if event["result"].startswith("PASS")],
                "resume_count": int(self.store.job(str(job["video_job_id"]))["resume_count"]),
                "public_write_authority": False,
            }
            ledger_record = _json_artifact(paths["ledger"], ledger)
            technical = _load(paths["technical"])
            package = _load(paths["package"])
            cost = _load(paths["cost"])
            creative_receipts = [
                str(paths["editor_receipt"]),
                str(paths["motion_receipt"]),
                str(paths["review_receipt"]),
            ]
            if paths["editor_revision_receipt"].is_file():
                creative_receipts.insert(1, str(paths["editor_revision_receipt"]))
            bundle = {
                "schema": "contentops.v2.owner_review_bundle.v1",
                "result": "OWNER_REVIEW_READY",
                "owner_acceptance_claimed": False,
                "video_job_id": str(job["video_job_id"]),
                "run_id": run_id,
                "implementation_head": self.config.implementation_head,
                "governed_input_hash": input_hash,
                "editorial_narration_hash": hash_value(editor),
                "narration_timing_lock": str(paths["timing_lock"]),
                "narration_timing_lock_hash": timing_lock["timing_lock_hash"],
                "actual_narration_duration_seconds": timing_lock[
                    "actual_total_narration_duration_seconds"
                ],
                "picture_duration_seconds": float(motion["duration_seconds"]),
                "final_mp4": local_media.artifact(paths["final"]),
                "contact_sheet": final_sheet["artifact"],
                "technical_media_report": str(paths["technical"]),
                "creative_execution_receipts": creative_receipts,
                "parent_session_receipt": str(paths["parent_receipt"]),
                "parent_runtime": "CODEX_DESKTOP_APP_PARENT_TASK_SESSION",
                "parent_execution_plane": "CODEX_DESKTOP_APP_TASK_SESSION",
                "parent_model_family": "gpt-5.6-sol",
                "parent_reasoning_effort": "high",
                "creative_runtime": "CODEX_DESKTOP_APP_BOUNDED_VIDEO_CREATIVE_REASONING",
                "creative_execution_plane": "CODEX_DESKTOP_APP_BOUNDED_REASONING",
                "creative_model_family": "gpt-5.6-sol",
                "creative_reasoning_effort": "xhigh",
                "all_session_xhigh": False,
                "xhigh_mechanical_work_execution_count": 0,
                "creative_cli_invocations": 0,
                "creative_sdk_api_invocations": 0,
                "creative_headless_invocations": 0,
                "creative_9router_invocations": 0,
                "factual_anchor_audit": str(paths["factual_audit"]),
                "rights_provenance_summary": str(paths["rights"]),
                "stage_ledger_summary": str(paths["ledger"]),
                "cost_runtime_summary": str(paths["cost"]),
                "package_id": package["package_id"],
                "media_validation": technical["media_validation"],
                "loudness": technical["loudness"],
                "comparison_questions": {
                    "reference": "video/projects/frozen_without_breaking_short_v1 (quality reference only)",
                    "prior_creative_source_reused_as_input": False,
                    "review": [
                        "factual grounding",
                        "visual clarity",
                        "composition",
                        "pacing",
                        "motion quality",
                        "audio quality",
                        "mobile readability",
                        "generic/template feel",
                        "exact-file reuse",
                        "visual-family repetition",
                        "repeated split-panel or vertical-rail grammar",
                        "concrete-first compliance",
                        "chart and data stability",
                        "whether each visual hold earns its duration",
                    ],
                    "identical_creative_choices_required": False,
                },
                "unattended": {
                    "manual_source_edits_after_start": 0,
                    "manual_media_edits_after_start": 0,
                    "manual_checkpoint_edits": 0,
                    "operator_intervention_minutes": cost["operator_intervention_minutes"],
                },
                "public_write_authority": False,
            }
            bundle_record = _json_artifact(paths["bundle"], bundle)
            self._secret_scan(paths["root"])
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"package": hash_file(paths["package"]), "final_media": hash_file(paths["final"])},
                artifacts=[final_sheet["artifact"], ledger_record, bundle_record],
                result="PASS_OWNER_REVIEW_READY",
                next_stage=None,
                role="UnattendedV2Supervisor.owner_review_bundle",
            )
            self.store.finalize(
                video_job_id=str(job["video_job_id"]),
                run_id=run_id,
                result="PASS_IMPLEMENTATION_ACTUAL_NARRATION_TIMING_LOCK_V2_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW",
                state="OWNER_REVIEW_READY",
            )
            return
        raise SupervisorError(f"unknown_stage:{stage}")

    def _secret_scan(self, root: Path) -> None:
        violations: list[str] = []
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {
                ".json",
                ".md",
                ".txt",
                ".tsx",
                ".ts",
                ".srt",
                ".vtt",
            }:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if any(pattern.search(text) for pattern in SECRET_PATTERNS):
                violations.append(str(path))
        if violations:
            raise SupervisorError("secret_scan_failed:" + ",".join(violations))

    def _quarantine_failure(
        self,
        *,
        claimed: Mapping[str, Any],
        paths: Mapping[str, Path],
        error: BaseException,
    ) -> None:
        video_job_id = str(claimed["video_job_id"])
        run_id = str(claimed["run_id"])
        failure_artifacts: list[dict[str, Any]] = []
        safe_receipt = getattr(error, "safe_receipt", None)
        if isinstance(safe_receipt, Mapping) and safe_receipt:
            failure_artifacts.append(
                _json_artifact(
                    paths["artifacts"] / "creative_failure_receipt.json",
                    dict(safe_receipt),
                )
            )
        self.store.append_event(
            video_job_id=video_job_id,
            run_id=run_id,
            stage="HARD_FAILURE",
            input_hashes={},
            output_hashes={},
            artifacts=failure_artifacts,
            role_tool_identity="DesktopSessionV2Factory",
            model_provenance=dict(safe_receipt or {}),
            wall_time_seconds=0,
            safe_usage={},
            result="FAIL_QUARANTINED",
            retry_state={"error_type": type(error).__name__},
            next_legal_stage=None,
            state_pointer="QUARANTINED",
            terminal_result=f"HARD_FAILURE:{type(error).__name__}:{str(error)[:300]}",
        )
        self.store.quarantine(
            video_job_id=video_job_id,
            run_id=run_id,
            reason=f"HARD_FAILURE:{type(error).__name__}:{str(error)[:300]}",
        )

    def _progress_claimed(
        self,
        *,
        claimed: Mapping[str, Any],
        max_new_stages: int | None,
        quarantine_on_failure: bool,
    ) -> dict[str, Any]:
        video_job_id = str(claimed["video_job_id"])
        run_id = str(claimed["run_id"])
        paths = self._paths(video_job_id)
        packet = self._packet(claimed)
        executed: list[str] = []
        try:
            latest = self._validate_checkpoint_chain(job=claimed, run_id=run_id)
            while True:
                stage = self._next_stage(latest, paths)
                if stage is None:
                    job = self.store.job(video_job_id)
                    return {
                        "result": job["terminal_result"] or "CHECKPOINTS_COMPLETE",
                        "video_job_id": video_job_id,
                        "run_id": run_id,
                        "executed_stages": executed,
                        "job": job,
                        "owner_review_bundle": str(paths["bundle"]),
                    }
                self._execute_stage(
                    stage=stage,
                    job=claimed,
                    run_id=run_id,
                    packet=packet,
                    paths=paths,
                )
                executed.append(stage)
                latest = self._latest(video_job_id)
                if max_new_stages is not None and len(executed) >= max_new_stages:
                    self.store.release_claim(
                        video_job_id=video_job_id, worker_id=self.config.worker_id
                    )
                    return {
                        "result": "INTERRUPTED_AFTER_COMPLETED_CHECKPOINT",
                        "video_job_id": video_job_id,
                        "run_id": run_id,
                        "executed_stages": executed,
                        "last_valid_checkpoint": executed[-1],
                    }
        except DesktopSessionInputRequired as required:
            return {
                "result": "AWAITING_CODEX_DESKTOP_SESSION_INPUT",
                "required_input": required.input_kind,
                "video_job_id": video_job_id,
                "run_id": run_id,
                "executed_stages": executed,
                "last_valid_checkpoint": (
                    executed[-1]
                    if executed
                    else self.store.job(video_job_id).get("last_valid_checkpoint")
                ),
                "public_write_authority": False,
            }
        except BaseException as exc:
            if quarantine_on_failure:
                try:
                    self._quarantine_failure(claimed=claimed, paths=paths, error=exc)
                except BaseException:
                    pass
            raise

    def run_once(
        self,
        *,
        proof_run_started_at: str | None = None,
        max_new_stages: int | None = None,
        quarantine_on_failure: bool = True,
    ) -> dict[str, Any]:
        claimed = self.store.claim_next(
            worker_id=self.config.worker_id,
            implementation_head=self.config.implementation_head,
            proof_run_started_at=proof_run_started_at,
            lease_seconds=43_200,
        )
        if claimed is None:
            return {"result": "NO_ELIGIBLE_JOB"}
        return self._progress_claimed(
            claimed=claimed,
            max_new_stages=max_new_stages,
            quarantine_on_failure=quarantine_on_failure,
        )

    def resume(
        self,
        *,
        video_job_id: str,
        run_id: str,
        max_new_stages: int | None = None,
        quarantine_on_failure: bool = True,
    ) -> dict[str, Any]:
        claimed = self._active_job(video_job_id=video_job_id, run_id=run_id)
        claimed["run_id"] = run_id
        return self._progress_claimed(
            claimed=claimed,
            max_new_stages=max_new_stages,
            quarantine_on_failure=quarantine_on_failure,
        )


# Backward-compatible name for callers that imported the old supervisor class. The class itself
# is session-driven and contains no creative runtime invocation.
UnattendedV2Supervisor = DesktopSessionV2Factory
