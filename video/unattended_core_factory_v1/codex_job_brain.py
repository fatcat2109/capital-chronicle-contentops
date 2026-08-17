from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .creative import (
    CreativeContractError,
    hash_file,
    hash_value,
    validate_editor_artifact,
    validate_motion_artifact,
    validate_revision_artifact,
)


CODEX_MODEL = "gpt-5.6-sol"
CODEX_REASONING_EFFORT = "xhigh"
EXECUTION_PLANE = "CODEX_CLI_EXEC"
NO_CREATIVE_FALLBACK = True


class CodexJobBrainError(CreativeContractError):
    def __init__(self, message: str, *, safe_receipt: Mapping[str, Any] | None = None) -> None:
        super().__init__(message)
        self.safe_receipt = dict(safe_receipt or {})


@dataclass(frozen=True)
class CodexCapability:
    executable: Path
    cli_version: str
    model: str
    reasoning_effort: str
    catalog_sha256: str


def _safe_usage(events: Sequence[Mapping[str, Any]]) -> dict[str, int] | None:
    totals: dict[str, int] = {}

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                if key in {
                    "input_tokens",
                    "cached_input_tokens",
                    "output_tokens",
                    "reasoning_output_tokens",
                    "total_tokens",
                } and isinstance(nested, int):
                    totals[key] = max(totals.get(key, 0), nested)
                else:
                    visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    for event in events:
        visit(event)
    return totals or None


def _thread_id(events: Sequence[Mapping[str, Any]]) -> str | None:
    for event in events:
        if event.get("type") == "thread.started" and event.get("thread_id"):
            return str(event["thread_id"])
        thread = event.get("thread")
        if isinstance(thread, Mapping) and thread.get("id"):
            return str(thread["id"])
    return None


def _events(raw: str) -> list[dict[str, Any]]:
    parsed: list[dict[str, Any]] = []
    for line in raw.splitlines():
        try:
            value = json.loads(line)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            parsed.append(value)
    return parsed


class CodexCliExecutor:
    """Small non-interactive Codex CLI surface with no 9Router dependency."""

    def __init__(
        self,
        *,
        executable: str | Path | None = None,
        runner: Callable[..., Any] = subprocess.run,
        timeout_seconds: float = 1800.0,
    ) -> None:
        self.requested_executable = Path(executable).resolve() if executable else None
        self.runner = runner
        self.timeout_seconds = timeout_seconds

    def _resolve(self, runtime_root: Path) -> Path:
        candidate = self.requested_executable
        if candidate is None:
            found = shutil.which("codex.exe") or shutil.which("codex")
            if not found:
                raise CodexJobBrainError("codex_cli_not_found")
            candidate = Path(found).resolve()
        if not candidate.is_file():
            raise CodexJobBrainError(f"codex_cli_missing:{candidate}")
        # WindowsApps executables may be discoverable but not directly launchable from a
        # child process. A content-addressed task-local executable copy preserves the exact
        # installed bytes and avoids changing authentication/config state.
        if os.name == "nt" and "windowsapps" in str(candidate).casefold():
            digest = hash_file(candidate)
            suffix = candidate.suffix or ".exe"
            copied = runtime_root / "tools" / f"codex-{digest[:16]}{suffix}"
            copied.parent.mkdir(parents=True, exist_ok=True)
            if not copied.is_file() or hash_file(copied) != digest:
                shutil.copy2(candidate, copied)
            candidate = copied
        return candidate

    def _run(self, args: list[str], *, prompt: str | None = None) -> Any:
        return self.runner(
            args,
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )

    def inspect_capability(self, runtime_root: Path) -> CodexCapability:
        executable = self._resolve(runtime_root)
        version = self._run([str(executable), "--version"])
        if int(version.returncode) != 0:
            raise CodexJobBrainError("codex_cli_version_probe_failed")
        catalog = self._run([str(executable), "debug", "models", "--bundled"])
        if int(catalog.returncode) != 0:
            raise CodexJobBrainError("codex_cli_bundled_catalog_probe_failed")
        try:
            value = json.loads(catalog.stdout)
        except (TypeError, ValueError) as exc:
            raise CodexJobBrainError("codex_cli_bundled_catalog_invalid") from exc
        models = value if isinstance(value, list) else value.get("models", [])
        selected = next(
            (item for item in models if isinstance(item, Mapping) and item.get("slug") == CODEX_MODEL),
            None,
        )
        if selected is None:
            raise CodexJobBrainError(f"codex_model_not_supported:{CODEX_MODEL}")
        efforts = {
            str(item.get("effort"))
            for item in selected.get("supported_reasoning_levels", [])
            if isinstance(item, Mapping)
        }
        if CODEX_REASONING_EFFORT not in efforts:
            raise CodexJobBrainError(
                f"codex_reasoning_effort_not_supported:{CODEX_MODEL}:{CODEX_REASONING_EFFORT}"
            )
        return CodexCapability(
            executable=executable,
            cli_version=str(version.stdout).strip(),
            model=CODEX_MODEL,
            reasoning_effort=CODEX_REASONING_EFFORT,
            catalog_sha256=hash_value(value),
        )

    @staticmethod
    def _common_args(capability: CodexCapability) -> list[str]:
        return [
            "-m",
            capability.model,
            "-c",
            f'model_reasoning_effort="{capability.reasoning_effort}"',
            "-c",
            'shell_environment_policy.inherit="none"',
            "--strict-config",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--json",
        ]

    def execute_fresh(
        self,
        *,
        capability: CodexCapability,
        workspace: Path,
        prompt: str,
        images: Sequence[Path] = (),
    ) -> dict[str, Any]:
        last_message = workspace / ".codex-last-message.txt"
        args = [str(capability.executable), "exec", *self._common_args(capability)]
        args.extend(["--sandbox", "workspace-write"])
        for image in images:
            args.extend(["--image", str(image.resolve())])
        args.extend(["--output-last-message", str(last_message), "--cd", str(workspace), "-"])
        return self._execute(args=args, prompt=prompt, last_message=last_message)

    def execute_resume(
        self,
        *,
        capability: CodexCapability,
        thread_id: str,
        workspace: Path,
        prompt: str,
        images: Sequence[Path] = (),
    ) -> dict[str, Any]:
        last_message = workspace / ".codex-last-message.txt"
        args = [
            str(capability.executable),
            "exec",
            "resume",
            *self._common_args(capability),
        ]
        for image in images:
            args.extend(["--image", str(image.resolve())])
        args.extend(["--output-last-message", str(last_message), thread_id, "-"])
        return self._execute(args=args, prompt=prompt, last_message=last_message)

    def _execute(
        self,
        *,
        args: list[str],
        prompt: str,
        last_message: Path,
    ) -> dict[str, Any]:
        started_wall = time.time()
        started = time.monotonic()
        completed = self._run(args, prompt=prompt)
        events = _events(str(completed.stdout or ""))
        final_message = ""
        if last_message.is_file():
            final_message = last_message.read_text(encoding="utf-8", errors="replace")[:200]
            last_message.unlink(missing_ok=True)
        final_token = final_message.strip()
        final_classification = (
            final_token
            if final_token in {"CODEX_CREATIVE_ARTIFACTS_READY", "CODEX_ACTUAL_MEDIA_REVIEW_READY"}
            else ("NONSTANDARD_FINAL_MESSAGE" if final_token else None)
        )
        receipt = {
            "started_at_epoch_seconds": started_wall,
            "ended_at_epoch_seconds": time.time(),
            "wall_time_seconds": time.monotonic() - started,
            "exit_code": int(completed.returncode),
            "thread_id": _thread_id(events),
            "usage": _safe_usage(events),
            "cost": None,
            "event_count": len(events),
            "result_classification": "PASS_CODEX_EXEC" if int(completed.returncode) == 0 else "FAIL_CODEX_EXEC",
            "final_message_classification": final_classification,
        }
        if int(completed.returncode) != 0:
            raise CodexJobBrainError("codex_cli_execution_failed", safe_receipt=receipt)
        return receipt


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError) as exc:
        raise CodexJobBrainError(f"codex_output_invalid:{path.name}") from exc
    if not isinstance(value, dict):
        raise CodexJobBrainError(f"codex_output_not_object:{path.name}")
    return value


class CodexJobBrain:
    """Fresh per-video Codex creative brain; deterministic artifacts remain authority."""

    def __init__(self, executor: CodexCliExecutor | None = None) -> None:
        self.executor = executor or CodexCliExecutor()

    @staticmethod
    def _workspace(job_root: Path) -> Path:
        workspace = (job_root / "codex_job").resolve()
        if job_root.resolve() not in workspace.parents:
            raise CodexJobBrainError("codex_workspace_escape")
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def create(
        self,
        *,
        video_job_id: str,
        job_root: Path,
        packet: Mapping[str, Any],
        asset_root: Path,
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        workspace = self._workspace(job_root)
        output = workspace / "creative-output"
        input_path = workspace / "inputs" / "governed_packet.json"
        _write_json(input_path, packet)
        images: list[Path] = []
        board: list[dict[str, Any]] = []
        for asset in packet.get("rights_assets", []):
            source = asset_root / str(asset["relative_path"])
            if not source.is_file() or hash_file(source) != str(asset["sha256"]):
                raise CodexJobBrainError(f"codex_input_asset_hash_mismatch:{asset['asset_id']}")
            suffix = source.suffix.lower()
            if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
                copied = workspace / "inputs" / "assets" / source.name
                copied.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, copied)
            elif suffix in {".mp4", ".mov", ".mkv", ".webm"}:
                ffmpeg = shutil.which("ffmpeg")
                if not ffmpeg:
                    raise CodexJobBrainError("ffmpeg_required_for_codex_asset_board")
                copied = workspace / "inputs" / "assets" / f"{source.stem}.jpg"
                copied.parent.mkdir(parents=True, exist_ok=True)
                frame = subprocess.run(
                    [
                        ffmpeg,
                        "-y",
                        "-ss",
                        "1",
                        "-i",
                        str(source),
                        "-frames:v",
                        "1",
                        "-vf",
                        "scale=540:-2",
                        str(copied),
                    ],
                    capture_output=True,
                    timeout=60,
                    check=False,
                )
                if frame.returncode != 0 or not copied.is_file():
                    raise CodexJobBrainError(f"codex_asset_preview_failed:{asset['asset_id']}")
            else:
                continue
            images.append(copied)
            board.append(
                {
                    "asset_id": asset["asset_id"],
                    "governed_relative_path": asset["relative_path"],
                    "preview_path": str(copied),
                    "preview_sha256": hash_file(copied),
                }
            )
        board_path = workspace / "inputs" / "asset_board.json"
        _write_json(board_path, {"assets": board})
        try:
            capability = self.executor.inspect_capability(job_root)
        except CodexJobBrainError as exc:
            raise CodexJobBrainError(
                str(exc), safe_receipt=self._capability_failure_receipt("INITIAL_CREATIVE")
            ) from exc
        prompt = _initial_prompt(
            video_job_id=video_job_id,
            input_path=input_path,
            asset_board_path=board_path,
            output=output,
        )
        execution: dict[str, Any] = {}
        try:
            execution = self.executor.execute_fresh(
                capability=capability,
                workspace=workspace,
                prompt=prompt,
                images=images,
            )
            editor = _read_json(output / "editorial.json")
            manifest = _read_json(output / "source_manifest.json")
            files = {
                relative: (output / relative).read_text(encoding="utf-8")
                for relative in ("src/index.tsx", "src/Root.tsx", "src/Short.tsx")
            }
            motion = {**manifest, "files": files}
            validate_editor_artifact(editor, packet)
            validate_motion_artifact(motion, packet, editor)
        except BaseException as exc:
            safe = {**execution, **dict(getattr(exc, "safe_receipt", {}) or {})}
            safe.update(self._receipt_base(capability=capability, execution_kind="INITIAL_CREATIVE"))
            safe["input_artifact_hashes"] = {
                "governed_packet.json": hash_file(input_path),
                "asset_board.json": hash_file(board_path),
            }
            safe["result_classification"] = safe.get("result_classification") or "FAIL_CODEX_OUTPUT_VALIDATION"
            raise CodexJobBrainError(str(exc), safe_receipt=safe) from exc
        receipt = {
            **self._receipt_base(capability=capability, execution_kind="INITIAL_CREATIVE"),
            **execution,
            "fresh_isolated_context": True,
            "resumed_same_job_thread": False,
            "input_artifact_hashes": {
                "governed_packet.json": hash_file(input_path),
                "asset_board.json": hash_file(board_path),
            },
            "output_artifact_hashes": {
                "editorial": hash_value(editor),
                "motion": hash_value(motion),
            },
        }
        if not receipt.get("thread_id"):
            raise CodexJobBrainError("codex_thread_identity_not_exposed", safe_receipt=receipt)
        return editor, motion, receipt

    def review(
        self,
        *,
        job_root: Path,
        packet: Mapping[str, Any],
        editor: Mapping[str, Any],
        motion: Mapping[str, Any],
        proxy_report: Mapping[str, Any],
        contact_sheet: Path,
        initial_receipt: Mapping[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        workspace = self._workspace(job_root)
        output = workspace / "review-output"
        review_packet = workspace / "inputs" / "review_packet.json"
        _write_json(
            review_packet,
            {
                "governed_packet_hash": hash_value(packet),
                "editorial": editor,
                "motion_manifest": {key: value for key, value in motion.items() if key != "files"},
                "motion_files": motion["files"],
                "proxy_report": proxy_report,
                "proxy_contact_sheet_sha256": hash_file(contact_sheet),
            },
        )
        try:
            capability = self.executor.inspect_capability(job_root)
        except CodexJobBrainError as exc:
            raise CodexJobBrainError(
                str(exc), safe_receipt=self._capability_failure_receipt("ACTUAL_MEDIA_REVIEW")
            ) from exc
        thread_id = str(initial_receipt.get("thread_id") or "")
        if not thread_id:
            raise CodexJobBrainError("codex_review_thread_identity_missing")
        prompt = _review_prompt(review_packet=review_packet, output=output)
        execution: dict[str, Any] = {}
        try:
            execution = self.executor.execute_resume(
                capability=capability,
                thread_id=thread_id,
                workspace=workspace,
                prompt=prompt,
                images=[contact_sheet],
            )
            review = _read_json(output / "review.json")
            if review.get("decision") == "MATERIAL_REVISION_REQUIRED":
                review["replacement_files"] = {
                    relative: (output / relative).read_text(encoding="utf-8")
                    for relative in ("src/index.tsx", "src/Root.tsx", "src/Short.tsx")
                }
            else:
                review["replacement_files"] = {}
            validate_revision_artifact(review, packet, editor, motion)
        except BaseException as exc:
            safe = {**execution, **dict(getattr(exc, "safe_receipt", {}) or {})}
            safe.update(self._receipt_base(capability=capability, execution_kind="ACTUAL_MEDIA_REVIEW"))
            safe["thread_id"] = thread_id
            safe["input_artifact_hashes"] = {"review_packet.json": hash_file(review_packet)}
            safe["result_classification"] = safe.get("result_classification") or "FAIL_CODEX_OUTPUT_VALIDATION"
            raise CodexJobBrainError(str(exc), safe_receipt=safe) from exc
        receipt = {
            **self._receipt_base(capability=capability, execution_kind="ACTUAL_MEDIA_REVIEW"),
            **execution,
            "thread_id": thread_id,
            "fresh_isolated_context": False,
            "resumed_same_job_thread": True,
            "input_artifact_hashes": {"review_packet.json": hash_file(review_packet)},
            "output_artifact_hashes": {"review": hash_value(review)},
        }
        return review, receipt

    @staticmethod
    def _receipt_base(*, capability: CodexCapability, execution_kind: str) -> dict[str, Any]:
        return {
            "schema": "contentops.v2.codex_job_brain_receipt.v1",
            "execution_plane": EXECUTION_PLANE,
            "execution_kind": execution_kind,
            "requested_model_family": CODEX_MODEL,
            "requested_reasoning_effort": CODEX_REASONING_EFFORT,
            "actual_model_family": None,
            "actual_reasoning_effort": None,
            "cli_version": capability.cli_version,
            "bundled_catalog_sha256": capability.catalog_sha256,
            "local_catalog_supports_exact_selection": True,
            "nine_router_route": None,
            "fallback_allowed": False,
            "fallback_count": 0,
            "attempt_count": 1,
            "public_write_authority": False,
        }

    @staticmethod
    def _capability_failure_receipt(execution_kind: str) -> dict[str, Any]:
        return {
            "schema": "contentops.v2.codex_job_brain_receipt.v1",
            "execution_plane": EXECUTION_PLANE,
            "execution_kind": execution_kind,
            "requested_model_family": CODEX_MODEL,
            "requested_reasoning_effort": CODEX_REASONING_EFFORT,
            "actual_model_family": None,
            "actual_reasoning_effort": None,
            "result_classification": "BLOCKED_CODEX_CAPABILITY_MISMATCH",
            "nine_router_route": None,
            "fallback_allowed": False,
            "fallback_count": 0,
            "attempt_count": 0,
            "public_write_authority": False,
        }


def _initial_prompt(
    *, video_job_id: str, input_path: Path, asset_board_path: Path, output: Path
) -> str:
    return f"""You are the fresh isolated Capital Chronicle V2 CodexJobBrain for video job
{video_job_id}. Read the immutable governed packet at {input_path} and the preview-to-asset mapping
at {asset_board_path}; inspect the attached governed previews. You own viewer-facing
editorial architecture, narration, visual storytelling, asset-to-purpose decisions, typography,
layout, motion, pacing, and story-specific Remotion source. You have zero factual, numeric,
rights, permission, publication, public-write, scheduler, or evidence-mutation authority.

Create a fresh 1080x1920, 30fps, normally 30-60 second Short. Do not reuse or imitate any prior
Frozen Without Breaking narration, source, choreography, layout answer, or repair answer. Facts
must be copied byte-for-byte from one governed anchor and carry its anchor_id. Capital Chronicle
analysis must be copied byte-for-byte from one permitted_analysis entry and carry its analysis_id.
Engagement copy may add no numbers or factual assertions. Use only governed asset paths.

Write these explicit artifacts under {output}:
- editorial.json with schema contentops.v2.codex_job_editorial.v1, title, viewer_promise,
  duration_seconds, narration_segments, optional free-form shots/creative_direction, and audio_intent;
- source_manifest.json with schema contentops.v2.codex_job_motion_source.v1, composition_id exactly
  FWBUnattendedShort, duration_seconds, exact asset_ids used, and source_claim_bindings;
- src/index.tsx, src/Root.tsx, and src/Short.tsx containing fresh viewer-facing React/Remotion code.

The source may import only react and remotion. It may not read env/filesystem/network, spawn
processes, install packages, use browsers, call platforms, or mutate evidence. Every viewer-facing
factual or analytical display string must be an exact contiguous substring of its bound narration
segment and listed in source_claim_bindings. Register exactly one 1080x1920 30fps composition.
Do not add narration audio; deterministic infrastructure builds audio later. Finish with only
CODEX_CREATIVE_ARTIFACTS_READY after the files are complete.
"""


def _review_prompt(*, review_packet: Path, output: Path) -> str:
    return f"""Continue only this same video job as its XHIGH actual-media creative reviewer.
Read {review_packet} and inspect the attached proxy contact sheet. Judge taste, clarity,
composition, pacing, motion, mobile readability, novelty, and generic/template feel. This is
creative evidence, not owner acceptance. Facts, narration, evidence, assets, format, and sandbox
boundaries are locked.

Write {output / 'review.json'} with schema contentops.v2.codex_actual_media_review.v1, decision
NO_MATERIAL_REVISION or MATERIAL_REVISION_REQUIRED, summary, defects, and source_claim_bindings.
If and only if a material localized source repair is warranted, also write complete replacements
at {output / 'src/index.tsx'}, {output / 'src/Root.tsx'}, and {output / 'src/Short.tsx'} while
preserving the locked composition, duration, copy, asset universe, and sandbox. Otherwise write no
source files. Finish with only CODEX_ACTUAL_MEDIA_REVIEW_READY.
"""
