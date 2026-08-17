"""Historical compatibility names for the rejected CLI creative seam.

The active V2 factory is driven by a fresh Codex Desktop App task/session through
``desktop_session.py`` and ``supervisor.py``. Importing an old name is allowed so historical
callers get a precise terminal classification; construction or invocation always fails closed
before process, model, provider, or network activity.
"""

from __future__ import annotations

from typing import Any

from .creative import CreativeContractError


CODEX_MODEL = "gpt-5.6-sol"
CODEX_REASONING_EFFORT = "xhigh"
EXECUTION_PLANE = "NON_CANONICAL_CLI_SEAM_DISABLED"
NO_CREATIVE_FALLBACK = True
TERMINAL_CLASSIFICATION = "CODEX_CLI_NOT_V2_CREATIVE_AUTHORITY"


class CodexJobBrainError(CreativeContractError):
    def __init__(self, message: str = TERMINAL_CLASSIFICATION, **_: Any) -> None:
        super().__init__(message)
        self.safe_receipt = {
            "schema": "contentops.v2.noncanonical_creative_runtime_rejection.v1",
            "result": TERMINAL_CLASSIFICATION,
            "execution_plane": EXECUTION_PLANE,
            "creative_invocation_attempted": False,
            "nine_router_route": None,
            "fallback_allowed": False,
            "fallback_count": 0,
            "public_write_authority": False,
        }


class CodexCliExecutor:
    def __init__(self, *_: Any, **__: Any) -> None:
        raise CodexJobBrainError()


class CodexJobBrain:
    def __init__(self, *_: Any, **__: Any) -> None:
        raise CodexJobBrainError()
