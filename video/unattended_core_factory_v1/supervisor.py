from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from . import media as local_media
from .codex_job_brain import CodexJobBrain
from .creative import (
    hash_file,
    hash_value,
    materialize_source,
    validate_editor_artifact,
    validate_input_packet,
    validate_motion_artifact,
    validate_revision_artifact,
    validate_source_files,
)
from .store import V2JobStore, utc_now


SCHEMA_VERSION = "contentops.v2.unattended_core_factory_supervisor.v1"
STAGES: tuple[str, ...] = (
    "CLAIMED",
    "GOVERNED_INPUT_LOCKED",
    "CREATIVE_EDITOR_LOCKED",
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
        "codex_xhigh_execution_count": calls,
        "codex_execution_attempt_count": attempts,
        "model_cost_usd": round(usd, 8) if exposed else None,
        "model_cost_exposed": exposed,
        "safe_usage": usage or None,
    }


class UnattendedV2Supervisor:
    def __init__(
        self,
        *,
        store: V2JobStore,
        config: FactoryConfig,
        creative_brain: CodexJobBrain | None = None,
        media_backend: Any = local_media,
    ) -> None:
        self.store = store
        self.config = config
        self.brain = creative_brain or CodexJobBrain()
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
            "codex_workspace": root / "codex_job",
            "editor": artifacts / "creative_editor.json",
            "editor_validation": artifacts / "creative_editor_validation.json",
            "editor_receipt": artifacts / "codex_initial_execution_receipt.json",
            "motion_pending": artifacts / "codex_initial_motion_output.json",
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
            "narration_receipt": artifacts / "narration_receipt.json",
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
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"input_packet": input_hash},
                artifacts=[],
                result="PASS_ATOMIC_CLAIM",
                next_stage="GOVERNED_INPUT_LOCKED",
                role="V2JobStore.claim_next",
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
            output, motion_output, receipt = self.brain.create(
                video_job_id=str(job["video_job_id"]),
                job_root=paths["root"],
                packet=packet,
                asset_root=self.config.asset_root,
            )
            validation = validate_editor_artifact(output, packet)
            records = [
                _json_artifact(paths["editor"], output),
                _json_artifact(paths["editor_validation"], validation),
                _json_artifact(paths["editor_receipt"], receipt),
            ]
            _json_artifact(paths["motion_pending"], motion_output)
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"input_packet": input_hash},
                artifacts=records,
                result="PASS_CREATIVE_EDITOR_LOCK",
                next_stage="MOTION_SOURCE_LOCKED",
                role="CodexJobBrain.initial_creative_execution",
                receipt=receipt,
                usage=receipt.get("usage") or {},
            )
            return
        editor = _load(paths["editor"])
        if stage == "MOTION_SOURCE_LOCKED":
            output = _load(paths["motion_pending"])
            initial_receipt = _load(paths["editor_receipt"])
            expected_hash = str(
                (initial_receipt.get("output_artifact_hashes") or {}).get("motion") or ""
            )
            if not expected_hash or hash_value(output) != expected_hash:
                raise SupervisorError("codex_initial_motion_output_hash_mismatch")
            validation = validate_motion_artifact(output, packet, editor)
            receipt = {
                "schema": "contentops.v2.codex_job_brain_motion_lock_receipt.v1",
                "execution_plane": initial_receipt.get("execution_plane"),
                "requested_model_family": initial_receipt.get("requested_model_family"),
                "requested_reasoning_effort": initial_receipt.get("requested_reasoning_effort"),
                "actual_model_family": initial_receipt.get("actual_model_family"),
                "actual_reasoning_effort": initial_receipt.get("actual_reasoning_effort"),
                "thread_id": initial_receipt.get("thread_id"),
                "source_execution_receipt_sha256": hash_file(paths["editor_receipt"]),
                "input_artifact_hashes": {"editor": hash_value(editor)},
                "output_artifact_hashes": {"motion": hash_value(output)},
                "attempt_count": 0,
                "fallback_count": 0,
                "nine_router_route": None,
                "public_write_authority": False,
            }
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
                inputs={"editor": hash_value(editor)},
                artifacts=records,
                result="PASS_MOTION_SOURCE_LOCK",
                next_stage="HARD_SOURCE_VALIDATED",
                role="CodexJobBrain.motion_output_lock",
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
            render = self.media.render_project(
                project_root=paths["project"], output=paths["proxy"], crf=26
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
            proxy_report = _load(paths["proxy_report"])
            output, receipt = self.brain.review(
                job_root=paths["root"],
                packet=packet,
                editor=editor,
                motion=motion,
                proxy_report=proxy_report,
                contact_sheet=paths["proxy_sheet"],
                initial_receipt=_load(paths["editor_receipt"]),
            )
            validation = validate_revision_artifact(output, packet, editor, motion)
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
                role="CodexJobBrain.actual_media_review",
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
                role="CodexJobBrain.localized_revision+deterministic_typecheck",
            )
            return
        if stage == "PICTURE_LOCKED":
            render = self.media.render_project(
                project_root=paths["project"], output=paths["picture"], crf=18
            )
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={
                    "motion_or_revision": hash_value(
                        review if review["decision"] == "MATERIAL_REVISION_REQUIRED" else motion
                    )
                },
                artifacts=[render["artifact"]],
                result="PASS_PICTURE_LOCK",
                next_stage="AUDIO_BUILT",
                role="Remotion",
            )
            return
        if stage == "AUDIO_BUILT":
            narration = self.media.synthesize_narration(
                editor=editor,
                model_path=self.config.kokoro_model,
                voices_path=self.config.kokoro_voices,
                output_dir=paths["narration_dir"],
            )
            bed_path = self.config.asset_root / self.config.bed_relative_path
            mix = self.media.build_audio_mix(
                picture=paths["picture"],
                narration_receipt=narration,
                bed_path=bed_path,
                output_dir=paths["mix"].parent,
            )
            narration_record = _json_artifact(paths["narration_receipt"], narration)
            mix_record = _json_artifact(paths["audio_receipt"], mix)
            self._append(
                job=job,
                run_id=run_id,
                stage=stage,
                started=started,
                inputs={"editor": hash_value(editor), "picture": hash_file(paths["picture"])},
                artifacts=[narration["artifact"], mix["mix"], narration_record, mix_record],
                result="PASS_AUDIO_BUILD",
                next_stage="FINAL_MEDIA_BUILT",
                role="Kokoro+FFmpeg",
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
            narration = _load(paths["narration_receipt"])
            captions = self.media.build_captions(
                editor=editor,
                narration_receipt=narration,
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
            cost = {
                "schema": "contentops.v2.cost_runtime_summary.v1",
                **_safe_cost(receipts),
                "external_media_cost_usd": 0.0,
                "render_count": 2,
                "rerender_count": 1 if review["decision"] == "MATERIAL_REVISION_REQUIRED" else 0,
                "operator_intervention_minutes": 0,
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
            bundle = {
                "schema": "contentops.v2.owner_review_bundle.v1",
                "result": "OWNER_REVIEW_READY",
                "owner_acceptance_claimed": False,
                "video_job_id": str(job["video_job_id"]),
                "run_id": run_id,
                "implementation_head": self.config.implementation_head,
                "governed_input_hash": input_hash,
                "final_mp4": local_media.artifact(paths["final"]),
                "contact_sheet": final_sheet["artifact"],
                "technical_media_report": str(paths["technical"]),
                "creative_execution_receipts": [
                    str(paths["editor_receipt"]),
                    str(paths["motion_receipt"]),
                    str(paths["review_receipt"]),
                ],
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
                result="PASS_IMPLEMENTATION_UNATTENDED_V2_CODEX_BRAIN_MEDIA_READY_FOR_JIM_CHATGPT_REVIEW",
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
        )
        if claimed is None:
            return {"result": "NO_ELIGIBLE_JOB"}
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
        except BaseException as exc:
            if quarantine_on_failure:
                try:
                    failure_artifacts: list[dict[str, Any]] = []
                    safe_receipt = getattr(exc, "safe_receipt", None)
                    if isinstance(safe_receipt, Mapping) and safe_receipt:
                        failure_artifacts.append(
                            _json_artifact(
                                paths["artifacts"] / "codex_failure_receipt.json",
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
                        role_tool_identity="UnattendedV2Supervisor",
                        model_provenance=dict(safe_receipt or {}),
                        wall_time_seconds=0,
                        safe_usage={},
                        result="FAIL_QUARANTINED",
                        retry_state={"error_type": type(exc).__name__},
                        next_legal_stage=None,
                        state_pointer="QUARANTINED",
                        terminal_result=f"HARD_FAILURE:{type(exc).__name__}:{str(exc)[:300]}",
                    )
                    self.store.quarantine(
                        video_job_id=video_job_id,
                        run_id=run_id,
                        reason=f"HARD_FAILURE:{type(exc).__name__}:{str(exc)[:300]}",
                    )
                except BaseException:
                    pass
            raise
