from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .creative import CreativeContractError, hash_value


CREATIVE_RUNTIME = "CODEX_DESKTOP_APP_FRESH_TASK_SESSION"
EXECUTION_PLANE = "CODEX_DESKTOP_APP_TASK_SESSION"
CODEX_MODEL = "gpt-5.6-sol"
CODEX_REASONING_EFFORT = "xhigh"
NO_CREATIVE_FALLBACK = True


class DesktopSessionContractError(CreativeContractError):
    pass


@dataclass(frozen=True)
class DesktopSessionProvenance:
    """Non-secret provenance supplied by the current Desktop task itself."""

    session_label: str
    model_family: str = CODEX_MODEL
    reasoning_effort: str = CODEX_REASONING_EFFORT
    provenance_source: str = "OWNER_TASK_MODE_DECLARATION"

    def validate(self) -> None:
        if not self.session_label.strip():
            raise DesktopSessionContractError("desktop_session_label_required")
        if self.model_family != CODEX_MODEL:
            raise DesktopSessionContractError("desktop_session_model_mismatch")
        if self.reasoning_effort != CODEX_REASONING_EFFORT:
            raise DesktopSessionContractError("desktop_session_reasoning_effort_mismatch")
        if self.provenance_source not in {
            "OWNER_TASK_MODE_DECLARATION",
            "CODEX_DESKTOP_APP_EXPOSED_CONTEXT",
        }:
            raise DesktopSessionContractError("desktop_session_provenance_source_invalid")

    @property
    def continuity_key(self) -> str:
        self.validate()
        return hash_value(
            {
                "creative_runtime": CREATIVE_RUNTIME,
                "execution_plane": EXECUTION_PLANE,
                "session_label": self.session_label,
                "model_family": self.model_family,
                "reasoning_effort": self.reasoning_effort,
            }
        )


def build_desktop_session_receipt(
    *,
    provenance: DesktopSessionProvenance,
    execution_kind: str,
    video_job_id: str,
    run_id: str,
    input_artifact_hashes: Mapping[str, str],
    output_artifact_hashes: Mapping[str, str],
) -> dict[str, Any]:
    provenance.validate()
    if execution_kind not in {"INITIAL_CREATIVE", "ACTUAL_MEDIA_REVIEW"}:
        raise DesktopSessionContractError("desktop_session_execution_kind_invalid")
    if not video_job_id or not run_id:
        raise DesktopSessionContractError("desktop_session_job_identity_required")
    return {
        "schema": "contentops.v2.codex_desktop_session_receipt.v1",
        "creative_runtime": CREATIVE_RUNTIME,
        "execution_plane": EXECUTION_PLANE,
        "execution_kind": execution_kind,
        "video_job_id": video_job_id,
        "run_id": run_id,
        "session_label": provenance.session_label,
        "session_continuity_key": provenance.continuity_key,
        "requested_model_family": provenance.model_family,
        "requested_reasoning_effort": provenance.reasoning_effort,
        "actual_model_family": provenance.model_family,
        "actual_reasoning_effort": provenance.reasoning_effort,
        "provenance_source": provenance.provenance_source,
        "task_session_id_exposed": False,
        "session_database_inspected": False,
        "fresh_isolated_context": execution_kind == "INITIAL_CREATIVE",
        "resumed_same_job_session": execution_kind == "ACTUAL_MEDIA_REVIEW",
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


def validate_desktop_session_receipt(
    receipt: Mapping[str, Any],
    *,
    execution_kind: str,
    video_job_id: str,
    run_id: str,
    initial_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    expected = {
        "schema": "contentops.v2.codex_desktop_session_receipt.v1",
        "creative_runtime": CREATIVE_RUNTIME,
        "execution_plane": EXECUTION_PLANE,
        "execution_kind": execution_kind,
        "video_job_id": video_job_id,
        "run_id": run_id,
        "requested_model_family": CODEX_MODEL,
        "requested_reasoning_effort": CODEX_REASONING_EFFORT,
        "actual_model_family": CODEX_MODEL,
        "actual_reasoning_effort": CODEX_REASONING_EFFORT,
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
            raise DesktopSessionContractError(f"desktop_session_receipt_mismatch:{key}")
    continuity_key = str(receipt.get("session_continuity_key") or "")
    if not continuity_key:
        raise DesktopSessionContractError("desktop_session_continuity_key_missing")
    if initial_receipt is not None and continuity_key != str(
        initial_receipt.get("session_continuity_key") or ""
    ):
        raise DesktopSessionContractError("desktop_session_continuity_mismatch")
    if execution_kind == "INITIAL_CREATIVE":
        if receipt.get("fresh_isolated_context") is not True:
            raise DesktopSessionContractError("desktop_session_not_fresh")
        if receipt.get("resumed_same_job_session") is not False:
            raise DesktopSessionContractError("desktop_session_initial_marked_resumed")
    else:
        if receipt.get("fresh_isolated_context") is not False:
            raise DesktopSessionContractError("desktop_session_review_marked_fresh")
        if receipt.get("resumed_same_job_session") is not True:
            raise DesktopSessionContractError("desktop_session_review_not_same_job")
    return {
        "result": "PASS_CODEX_DESKTOP_SESSION_PROVENANCE",
        "execution_kind": execution_kind,
        "session_continuity_key": continuity_key,
        "creative_runtime": CREATIVE_RUNTIME,
        "execution_plane": EXECUTION_PLANE,
    }
