"""Canonical execution framework definitions and validation for ContentOps.

Authority: ``CONTENTOPS_MAIN_CODEX_AND_ANTIGRAVITY_SUBFRAMEWORK_OWNER_OVERRIDE_V1``
Status: ``OWNER_OVERRIDE_ACTIVE``

ContentOps has two execution frameworks:
1. ``MAIN_CODEX`` (Default): Primary execution framework whenever Codex quota/capacity is available.
2. ``SUB_ANTIGRAVITY`` (Explicit Fallback): Fallback framework used strictly when Codex quota/capacity
   is unavailable. The active Antigravity model performs all model-driven roles without Sol/XHIGH spoofing.
"""
from __future__ import annotations

from typing import Any, Mapping

SCHEMA_VERSION = "contentops.execution_framework.v1"

FRAMEWORK_MAIN_CODEX = "MAIN_CODEX"
FRAMEWORK_SUB_ANTIGRAVITY = "SUB_ANTIGRAVITY"
DEFAULT_EXECUTION_FRAMEWORK = FRAMEWORK_MAIN_CODEX
RECOGNIZED_FRAMEWORKS = frozenset({FRAMEWORK_MAIN_CODEX, FRAMEWORK_SUB_ANTIGRAVITY})

MAIN_COORDINATOR_MODEL = "gpt-5.6-sol"
MAIN_COORDINATOR_REASONING_EFFORT = "HIGH"
MAIN_EDITORIAL_WORKER_MODEL = "gpt-5.6-sol"
MAIN_EDITORIAL_WORKER_REASONING_EFFORT = "XHIGH"

DISALLOWED_SUB_MODEL_SPOOFS = frozenset({
    "gpt-5.6-sol",
    "gpt-5.6-sol-high",
    "gpt-5.6-sol-xhigh",
    "gpt-5.6-sol / high",
    "gpt-5.6-sol / xhigh",
    "cx/gpt-5.6-sol(xhigh)",
    "codex desktop",
})


def validate_execution_framework(
    framework: str | None = None,
    *,
    sub_model_identity: str | None = None,
) -> dict[str, Any]:
    """Validate and normalize the execution framework configuration.

    Fails closed if the framework identity is unrecognized, if SUB_ANTIGRAVITY lacks an
    explicit actual model identity, or if SUB_ANTIGRAVITY attempts to spoof MAIN/Codex models.
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
            "coordinator_model": MAIN_COORDINATOR_MODEL,
            "coordinator_reasoning_effort": MAIN_COORDINATOR_REASONING_EFFORT,
            "editorial_worker_model": MAIN_EDITORIAL_WORKER_MODEL,
            "editorial_worker_reasoning_effort": MAIN_EDITORIAL_WORKER_REASONING_EFFORT,
            "requires_fresh_isolated_worker": True,
            "public_write_authority": False,
        }

    # SUB_ANTIGRAVITY validation
    clean_sub_model = str(sub_model_identity or "").strip()
    if not clean_sub_model:
        raise ValueError("sub_antigravity_model_identity_required")

    if clean_sub_model.casefold() in DISALLOWED_SUB_MODEL_SPOOFS:
        raise ValueError("sub_antigravity_cannot_spoof_main_model_identity")

    return {
        "schema_version": SCHEMA_VERSION,
        "framework": FRAMEWORK_SUB_ANTIGRAVITY,
        "is_main": False,
        "is_sub": True,
        "coordinator_model": clean_sub_model,
        "coordinator_reasoning_effort": "NOT_APPLICABLE_SUB_FRAMEWORK",
        "editorial_worker_model": clean_sub_model,
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
