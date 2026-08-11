"""Persistent operator cost-safety control for ContentOps text-model traffic.

The marker is deliberately outside the repository so it survives process restarts and source
updates.  Marker existence is authoritative; malformed contents therefore still fail closed.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "contentops.llm_operator_control.v1"
RUNTIME_CONTROL_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\control")
LLM_OPERATOR_PAUSE_FILENAME = "llm_operator_pause.flag"
LLM_OPERATOR_PAUSED = "LLM_OPERATOR_PAUSED"


class LLMOperatorPausedError(RuntimeError):
    """Raised before network I/O when the persistent operator fuse is active."""

    def __init__(self) -> None:
        super().__init__(LLM_OPERATOR_PAUSED)


def operator_pause_path(control_root: str | Path | None = None) -> Path:
    """Return the canonical marker path (an override is accepted for isolated tests only)."""
    root = Path(control_root) if control_root is not None else RUNTIME_CONTROL_ROOT
    return root / LLM_OPERATOR_PAUSE_FILENAME


def llm_operator_pause_active(control_root: str | Path | None = None) -> bool:
    return operator_pause_path(control_root).is_file()


def assert_llm_operator_execution_enabled(
    control_root: str | Path | None = None,
) -> None:
    """Fail before a provider attempt whenever the persistent operator fuse is active."""
    if llm_operator_pause_active(control_root):
        raise LLMOperatorPausedError()


def activate_llm_operator_pause(
    control_root: str | Path | None = None,
    *,
    activated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Atomically activate the fuse without storing credentials or session material."""
    marker = operator_pause_path(control_root)
    marker.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "state": "PAUSED_BY_OPERATOR",
        "reason": "EMERGENCY_COST_SAFETY_STOP",
        "activated_at_utc": activated_at_utc
        or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "contains_secrets": False,
    }
    temporary = marker.with_name(f"{marker.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, marker)
    return payload


def resume_llm_operator_execution(control_root: str | Path | None = None) -> bool:
    """Clear only the exact pause marker; this never starts a process."""
    marker = operator_pause_path(control_root)
    try:
        marker.unlink()
        return True
    except FileNotFoundError:
        return False

