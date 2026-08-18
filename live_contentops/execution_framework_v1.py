"""Canonical execution framework definitions and validation for ContentOps.

Authority: ``CONTENTOPS_MAIN_CODEX_AND_ANTIGRAVITY_SUBFRAMEWORK_OWNER_OVERRIDE_V1``
Status: ``OWNER_OVERRIDE_ACTIVE``

ContentOps has two execution frameworks:
1. ``MAIN_CODEX`` (Default): Primary multi-session execution framework whenever Codex quota/capacity is available.
2. ``SUB_ANTIGRAVITY`` (Explicit Fallback): Single-session framework where ONE already-configured
   Antigravity conversation performs all model-driven roles directly.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "contentops.execution_framework.v1"
BINDING_SCHEMA_VERSION = "contentops.rolling_x_framework_binding.v1"

FRAMEWORK_MAIN_CODEX = "MAIN_CODEX"
FRAMEWORK_SUB_ANTIGRAVITY = "SUB_ANTIGRAVITY"
DEFAULT_EXECUTION_FRAMEWORK = FRAMEWORK_MAIN_CODEX
RECOGNIZED_FRAMEWORKS = frozenset({FRAMEWORK_MAIN_CODEX, FRAMEWORK_SUB_ANTIGRAVITY})

MAIN_COORDINATOR_MODEL = "gpt-5.6-sol"
MAIN_COORDINATOR_REASONING_EFFORT = "HIGH"
MAIN_EDITORIAL_WORKER_MODEL = "gpt-5.6-sol"
MAIN_EDITORIAL_WORKER_REASONING_EFFORT = "XHIGH"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_execution_framework(
    framework: str | None = None,
) -> dict[str, Any]:
    """Validate and normalize the execution framework configuration.

    Fails closed if the framework identity is unrecognized.
    """
    raw_framework = str(framework or DEFAULT_EXECUTION_FRAMEWORK).strip().upper()
    if raw_framework not in RECOGNIZED_FRAMEWORKS:
        raise ValueError(f"unrecognized_execution_framework:{raw_framework}")

    if raw_framework == FRAMEWORK_MAIN_CODEX:
        return {
            "schema_version": SCHEMA_VERSION,
            "framework": FRAMEWORK_MAIN_CODEX,
            "is_main": True,
            "is_sub": False,
            "orchestration_mode": "MULTI_SESSION_CODEX",
            "coordinator_model": MAIN_COORDINATOR_MODEL,
            "coordinator_reasoning_effort": MAIN_COORDINATOR_REASONING_EFFORT,
            "editorial_worker_model": MAIN_EDITORIAL_WORKER_MODEL,
            "editorial_worker_reasoning_effort": MAIN_EDITORIAL_WORKER_REASONING_EFFORT,
            "requires_fresh_isolated_worker": True,
            "public_write_authority": False,
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "framework": FRAMEWORK_SUB_ANTIGRAVITY,
        "is_main": False,
        "is_sub": True,
        "orchestration_mode": "SINGLE_CONVERSATION_ANTIGRAVITY",
        "coordinator_model": "ACTIVE_ANTIGRAVITY_CONVERSATION",
        "coordinator_reasoning_effort": "NOT_APPLICABLE_SUB_FRAMEWORK",
        "editorial_worker_model": "ACTIVE_ANTIGRAVITY_CONVERSATION",
        "editorial_worker_reasoning_effort": "NOT_APPLICABLE_SUB_FRAMEWORK",
        "requires_fresh_isolated_worker": False,
        "public_write_authority": False,
    }


def assert_framework_continuity(
    opportunity_framework: str,
    incoming_framework: str,
) -> None:
    """Ensure that framework mode is never switched within a single opportunity."""
    op_norm = str(opportunity_framework or "").strip().upper()
    inc_norm = str(incoming_framework or "").strip().upper()
    if op_norm != inc_norm:
        raise ValueError(
            f"execution_framework_switch_mid_opportunity_forbidden:{op_norm}->{inc_norm}"
        )


def persist_opportunity_framework_binding(
    output_dir: Path,
    run_id: str,
    framework: str,
) -> dict[str, Any]:
    """Persist the canonical framework binding for an opportunity to guarantee continuity."""
    binding_path = output_dir / "rolling_x_framework_binding_v1.json"
    binding = {
        "schema_version": BINDING_SCHEMA_VERSION,
        "run_id": run_id,
        "execution_framework": str(framework).strip().upper(),
        "bound_at_utc": _utc_now(),
    }
    binding_path.parent.mkdir(parents=True, exist_ok=True)
    binding_path.write_text(json.dumps(binding, indent=2, sort_keys=True), encoding="utf-8")
    return binding


def verify_opportunity_framework_continuity(
    output_dir: Path,
    run_id: str,
    incoming_framework: str,
) -> dict[str, Any]:
    """Verify that an opportunity has not been switched to a different framework on re-entry/resume."""
    binding_path = output_dir / "rolling_x_framework_binding_v1.json"
    inc_fw = str(incoming_framework).strip().upper()

    if binding_path.exists():
        try:
            persisted = json.loads(binding_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise ValueError("opportunity_framework_binding_corrupted") from None

        if str(persisted.get("run_id") or "") == run_id:
            persisted_fw = str(persisted.get("execution_framework") or "").strip().upper()
            assert_framework_continuity(persisted_fw, inc_fw)
            return persisted

    # Initial binding for this opportunity
    return persist_opportunity_framework_binding(
        output_dir=output_dir,
        run_id=run_id,
        framework=inc_fw,
    )
