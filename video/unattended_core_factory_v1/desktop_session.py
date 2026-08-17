from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .creative import CreativeContractError, hash_value


PARENT_RUNTIME = "CODEX_DESKTOP_APP_PARENT_TASK_SESSION"
PARENT_EXECUTION_PLANE = "CODEX_DESKTOP_APP_TASK_SESSION"
CREATIVE_RUNTIME = "CODEX_DESKTOP_APP_BOUNDED_VIDEO_CREATIVE_REASONING"
CREATIVE_EXECUTION_PLANE = "CODEX_DESKTOP_APP_BOUNDED_REASONING"
CODEX_MODEL = "gpt-5.6-sol"
PARENT_REASONING_EFFORT = "high"
CREATIVE_REASONING_EFFORT = "xhigh"
NO_CREATIVE_FALLBACK = True


class DesktopSessionContractError(CreativeContractError):
    pass


@dataclass(frozen=True)
class ParentSessionProvenance:
    """Non-secret provenance for the ordinary HIGH Desktop parent/task session."""

    session_label: str
    model_family: str = CODEX_MODEL
    reasoning_effort: str = PARENT_REASONING_EFFORT
    provenance_source: str = "OWNER_TASK_MODE_DECLARATION"

    def validate(self) -> None:
        if not self.session_label.strip():
            raise DesktopSessionContractError("parent_session_label_required")
        if self.model_family != CODEX_MODEL:
            raise DesktopSessionContractError("parent_session_model_mismatch")
        if self.reasoning_effort != PARENT_REASONING_EFFORT:
            raise DesktopSessionContractError("parent_session_reasoning_effort_mismatch")
        if self.provenance_source not in {
            "OWNER_TASK_MODE_DECLARATION",
            "CODEX_DESKTOP_APP_EXPOSED_CONTEXT",
        }:
            raise DesktopSessionContractError("parent_session_provenance_source_invalid")

    @property
    def continuity_key(self) -> str:
        self.validate()
        return hash_value(
            {
                "parent_runtime": PARENT_RUNTIME,
                "parent_execution_plane": PARENT_EXECUTION_PLANE,
                "session_label": self.session_label,
                "model_family": self.model_family,
                "reasoning_effort": self.reasoning_effort,
            }
        )


@dataclass(frozen=True)
class BoundedCreativeProvenance:
    """Provenance for one bounded XHIGH video-creative execution."""

    parent: ParentSessionProvenance
    execution_label: str
    native_child_task_id: str | None = None
    model_family: str = CODEX_MODEL
    reasoning_effort: str = CREATIVE_REASONING_EFFORT
    provenance_source: str = "OWNER_TASK_MODE_DECLARATION"

    def validate(self) -> None:
        self.parent.validate()
        if not self.execution_label.strip():
            raise DesktopSessionContractError("creative_execution_label_required")
        if self.model_family != CODEX_MODEL:
            raise DesktopSessionContractError("creative_execution_model_mismatch")
        if self.reasoning_effort != CREATIVE_REASONING_EFFORT:
            raise DesktopSessionContractError("creative_execution_reasoning_effort_mismatch")
        if self.provenance_source not in {
            "OWNER_TASK_MODE_DECLARATION",
            "CODEX_DESKTOP_APP_EXPOSED_CONTEXT",
        }:
            raise DesktopSessionContractError("creative_execution_provenance_source_invalid")
        if self.native_child_task_id is not None and not self.native_child_task_id.strip():
            raise DesktopSessionContractError("creative_native_child_task_id_empty")


def build_parent_session_receipt(
    *,
    provenance: ParentSessionProvenance,
    video_job_id: str,
    run_id: str,
) -> dict[str, Any]:
    provenance.validate()
    if not video_job_id or not run_id:
        raise DesktopSessionContractError("parent_session_job_identity_required")
    return {
        "schema": "contentops.v2.parent_high_session_receipt.v1",
        "parent_runtime": PARENT_RUNTIME,
        "parent_execution_plane": PARENT_EXECUTION_PLANE,
        "video_job_id": video_job_id,
        "run_id": run_id,
        "parent_session_label": provenance.session_label,
        "parent_session_continuity_key": provenance.continuity_key,
        "parent_model_family": provenance.model_family,
        "parent_reasoning_effort": provenance.reasoning_effort,
        "provenance_source": provenance.provenance_source,
        "parent_task_session_id_exposed": False,
        "session_database_inspected": False,
        "coordination_scope": [
            "REPOSITORY_AND_EVIDENCE_WORK",
            "DETERMINISTIC_DIAGNOSTICS",
            "RENDER_AUDIO_PACKAGE_ORCHESTRATION",
            "TESTS_WAITS_RECOVERY",
            "DURABLE_STAGE_COORDINATION",
        ],
        "all_session_xhigh": False,
        "bounded_xhigh_video_creative_required": True,
        "public_write_authority": False,
    }


def build_bounded_creative_receipt(
    *,
    provenance: BoundedCreativeProvenance,
    execution_kind: str,
    video_job_id: str,
    run_id: str,
    input_artifact_hashes: Mapping[str, str],
    output_artifact_hashes: Mapping[str, str],
) -> dict[str, Any]:
    provenance.validate()
    if execution_kind not in {"INITIAL_CREATIVE", "ACTUAL_MEDIA_REVIEW"}:
        raise DesktopSessionContractError("creative_execution_kind_invalid")
    if not video_job_id or not run_id:
        raise DesktopSessionContractError("creative_execution_job_identity_required")
    job_continuity_key = hash_value(
        {
            "parent_session_continuity_key": provenance.parent.continuity_key,
            "video_job_id": video_job_id,
            "run_id": run_id,
        }
    )
    scope = (
        [
            "INSTITUTIONAL_VIDEO_ANALYSIS",
            "NARRATIVE_AND_NARRATION_AUTHORSHIP",
            "VIEWER_FACING_REMOTION_AUTHORSHIP",
            "VISUAL_MOTION_AND_SOUND_EDIT_INTENT",
        ]
        if execution_kind == "INITIAL_CREATIVE"
        else ["ACTUAL_MEDIA_CREATIVE_REVIEW", "BOUNDED_SAME_VIDEO_CREATIVE_REVISION"]
    )
    return {
        "schema": "contentops.v2.bounded_xhigh_video_creative_receipt.v1",
        "parent_runtime": PARENT_RUNTIME,
        "parent_execution_plane": PARENT_EXECUTION_PLANE,
        "parent_session_label": provenance.parent.session_label,
        "parent_session_continuity_key": provenance.parent.continuity_key,
        "parent_model_family": provenance.parent.model_family,
        "parent_reasoning_effort": provenance.parent.reasoning_effort,
        "creative_runtime": CREATIVE_RUNTIME,
        "creative_execution_plane": CREATIVE_EXECUTION_PLANE,
        "execution_kind": execution_kind,
        "execution_label": provenance.execution_label,
        "video_job_id": video_job_id,
        "run_id": run_id,
        "same_video_job_continuity_key": job_continuity_key,
        "declared_creative_model_family": provenance.model_family,
        "declared_creative_reasoning_effort": provenance.reasoning_effort,
        "provenance_source": provenance.provenance_source,
        "native_child_task_id": provenance.native_child_task_id,
        "native_child_task_id_exposed": provenance.native_child_task_id is not None,
        "parent_task_session_id_exposed": False,
        "session_database_inspected": False,
        "bounded_video_creative_execution": True,
        "all_session_xhigh": False,
        "same_video_job_followup": execution_kind == "ACTUAL_MEDIA_REVIEW",
        "hidden_chat_memory_state_authority": False,
        "authorized_creative_scope": scope,
        "mechanical_work_performed": False,
        "mechanical_work_categories": [],
        "input_artifact_hashes": dict(input_artifact_hashes),
        "output_artifact_hashes": dict(output_artifact_hashes),
        "usage": None,
        "cost": None,
        "nine_router_route": None,
        "cli_invocation_count": 0,
        "sdk_api_invocation_count": 0,
        "headless_creative_invocation_count": 0,
        "provider_creative_invocation_count": 0,
        "fallback_allowed": False,
        "fallback_count": 0,
        "attempt_count": 1,
        "public_write_authority": False,
    }


def validate_bounded_creative_receipt(
    receipt: Mapping[str, Any],
    *,
    execution_kind: str,
    video_job_id: str,
    run_id: str,
    initial_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    expected = {
        "schema": "contentops.v2.bounded_xhigh_video_creative_receipt.v1",
        "parent_runtime": PARENT_RUNTIME,
        "parent_execution_plane": PARENT_EXECUTION_PLANE,
        "parent_model_family": CODEX_MODEL,
        "parent_reasoning_effort": PARENT_REASONING_EFFORT,
        "creative_runtime": CREATIVE_RUNTIME,
        "creative_execution_plane": CREATIVE_EXECUTION_PLANE,
        "execution_kind": execution_kind,
        "video_job_id": video_job_id,
        "run_id": run_id,
        "declared_creative_model_family": CODEX_MODEL,
        "declared_creative_reasoning_effort": CREATIVE_REASONING_EFFORT,
        "bounded_video_creative_execution": True,
        "all_session_xhigh": False,
        "mechanical_work_performed": False,
        "mechanical_work_categories": [],
        "nine_router_route": None,
        "fallback_allowed": False,
        "fallback_count": 0,
        "public_write_authority": False,
        "session_database_inspected": False,
        "cli_invocation_count": 0,
        "sdk_api_invocation_count": 0,
        "headless_creative_invocation_count": 0,
        "provider_creative_invocation_count": 0,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise DesktopSessionContractError(f"bounded_creative_receipt_mismatch:{key}")
    parent_key = str(receipt.get("parent_session_continuity_key") or "")
    job_key = str(receipt.get("same_video_job_continuity_key") or "")
    if not parent_key or not job_key:
        raise DesktopSessionContractError("creative_continuity_key_missing")
    if initial_receipt is not None:
        if parent_key != str(initial_receipt.get("parent_session_continuity_key") or ""):
            raise DesktopSessionContractError("parent_session_continuity_mismatch")
        if job_key != str(initial_receipt.get("same_video_job_continuity_key") or ""):
            raise DesktopSessionContractError("same_video_job_continuity_mismatch")
    if receipt.get("same_video_job_followup") is not (execution_kind == "ACTUAL_MEDIA_REVIEW"):
        raise DesktopSessionContractError("creative_followup_marker_mismatch")
    return {
        "result": "PASS_HIGH_PARENT_BOUNDED_XHIGH_CREATIVE_PROVENANCE",
        "execution_kind": execution_kind,
        "parent_session_continuity_key": parent_key,
        "same_video_job_continuity_key": job_key,
        "parent_runtime": PARENT_RUNTIME,
        "creative_runtime": CREATIVE_RUNTIME,
    }
