"""V5 adapter codegen/check guardrail for operator feedback backlog v6.

Reads committed local/manual-only JSON packets only. No network, env,
credential, browser, provider, public URL, platform API, or live platform action
is performed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "docs/automation/V6_OPERATOR_SUPPLIED_FEEDBACK_INTAKE_AND_BACKLOG"
INTAKE_PACKET = PACKET_DIR / "operator_supplied_feedback_intake_packet.json"
BACKLOG_PACKET = PACKET_DIR / "operator_feedback_backlog_summary_packet.json"
ADAPTER_PATH = ROOT / "ui/contentops_v5/src/data/operatorFeedbackBacklogAdapter.ts"

FORBIDDEN_SECRET_VALUE_PATTERNS = (
    "secret=",
    "token=",
    "password=",
    "credential=",
    "cookie=",
    "session=",
)

HEADER = """// V6 Operator-supplied feedback backlog adapter.
// Generated from committed local/manual-only packets; no network/env/browser/provider access.

"""


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_no_secret_looking_values(payload: Any) -> None:
    if isinstance(payload, dict):
        for value in payload.values():
            _assert_no_secret_looking_values(value)
    elif isinstance(payload, list):
        for item in payload:
            _assert_no_secret_looking_values(item)
    elif isinstance(payload, str):
        lowered = payload.lower()
        if any(pattern in lowered for pattern in FORBIDDEN_SECRET_VALUE_PATTERNS):
            raise ValueError("secret-looking string value is not allowed in adapter data")


def _to_ts_const(name: str, payload: dict[str, Any]) -> str:
    _assert_no_secret_looking_values(payload)
    return f"export const {name} = " + json.dumps(payload, indent=2) + " as const;\n"


def build_operator_feedback_backlog_v5_adapter_text() -> str:
    """Return deterministic V5 adapter text from committed feedback packets only."""
    intake = _load_json(INTAKE_PACKET)
    backlog = _load_json(BACKLOG_PACKET)
    return (
        HEADER
        + _to_ts_const("operatorSuppliedFeedbackIntakePacket", intake)
        + "\n"
        + _to_ts_const("operatorFeedbackBacklogSummaryPacket", backlog)
    )


def check_operator_feedback_backlog_v5_adapter_in_sync() -> dict[str, Any]:
    """Return deterministic booleans describing committed V5 adapter sync status."""
    expected = build_operator_feedback_backlog_v5_adapter_text()
    observed = ADAPTER_PATH.read_text(encoding="utf-8")
    intake = _load_json(INTAKE_PACKET)
    backlog = _load_json(BACKLOG_PACKET)
    return {
        "adapter_path": str(ADAPTER_PATH.relative_to(ROOT)).replace("\\", "/"),
        "intake_packet_path": str(INTAKE_PACKET.relative_to(ROOT)).replace("\\", "/"),
        "backlog_packet_path": str(BACKLOG_PACKET.relative_to(ROOT)).replace("\\", "/"),
        "adapter_in_sync": observed == expected,
        "intake_packet_id": intake["feedback_intake_packet_id"],
        "intake_packet_hash": intake["exact_payload_hash"],
        "backlog_summary_packet_id": backlog["backlog_summary_packet_id"],
        "backlog_summary_hash": backlog["exact_payload_hash"],
        "intake_hash_matches": backlog["feedback_intake_hash"] == intake["exact_payload_hash"],
        "backlog_hash_matches": backlog["backlog_summary_packet_id"].endswith(backlog["exact_payload_hash"][:16]),
        "summary_method": backlog["summary_method"],
        "backlog_status": backlog["backlog_status"],
        "llm_provider_call_made": False,
        "provider_call_made": False,
        "platform_api_used": False,
        "public_url_fetch_made": False,
        "browser_session_used": False,
        "env_value_read_made": False,
        "credential_read_made": False,
        "live_publish_performed_by_contentops": False,
    }


if __name__ == "__main__":
    status = check_operator_feedback_backlog_v5_adapter_in_sync()
    print(json.dumps(status, indent=2, sort_keys=True))
    raise SystemExit(0 if status["adapter_in_sync"] else 1)
