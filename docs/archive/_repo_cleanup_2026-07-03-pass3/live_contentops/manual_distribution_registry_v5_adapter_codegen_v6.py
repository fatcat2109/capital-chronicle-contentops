"""V5 adapter codegen/check guardrail for Manual Distribution Registry v6.

Reads committed local JSON packets only. No network, env, credential, browser,
provider, public URL, or live platform action is performed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "docs/automation/V6_MANUAL_DISTRIBUTION_EVIDENCE_REGISTRY"
REGISTRY_PACKET = PACKET_DIR / "manual_distribution_evidence_registry_packet.json"
AUDIT_INDEX_PACKET = PACKET_DIR / "manual_distribution_registry_audit_index_packet.json"
ADAPTER_PATH = ROOT / "ui/contentops_v5/src/data/manualDistributionEvidenceRegistryAdapter.ts"

FORBIDDEN_SECRET_KEYS = ("secret", "token", "password", "credential", "cookie", "session")

HEADER = """// V6 Manual Distribution Evidence Registry adapter.
// Generated from committed fixture-only registry packet; no network/env/browser access.

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
        forbidden_value_patterns = ("secret=", "token=", "password=", "credential=", "cookie=", "session=")
        if any(pattern in lowered for pattern in forbidden_value_patterns):
            raise ValueError("secret-looking string value is not allowed in adapter data")


def _to_ts_const(name: str, payload: dict[str, Any]) -> str:
    _assert_no_secret_looking_values(payload)
    return f"export const {name} = " + json.dumps(payload, indent=2) + " as const;\n"


def build_manual_distribution_registry_v5_adapter_text() -> str:
    """Return deterministic V5 adapter text from committed registry packets only."""
    registry = _load_json(REGISTRY_PACKET)
    audit_index = _load_json(AUDIT_INDEX_PACKET)
    return (
        HEADER
        + _to_ts_const("manualDistributionEvidenceRegistry", registry)
        + "\nexport const manualDistributionRegistryPlatforms = manualDistributionEvidenceRegistry.platforms;\n\n\n"
        + _to_ts_const("manualDistributionRegistryAuditIndex", audit_index)
    )


def check_manual_distribution_registry_v5_adapter_in_sync() -> dict[str, Any]:
    """Return deterministic booleans describing committed V5 adapter sync status."""
    expected = build_manual_distribution_registry_v5_adapter_text()
    observed = ADAPTER_PATH.read_text(encoding="utf-8")
    registry = _load_json(REGISTRY_PACKET)
    audit_index = _load_json(AUDIT_INDEX_PACKET)
    return {
        "adapter_path": str(ADAPTER_PATH.relative_to(ROOT)).replace("\\", "/"),
        "registry_packet_path": str(REGISTRY_PACKET.relative_to(ROOT)).replace("\\", "/"),
        "audit_index_packet_path": str(AUDIT_INDEX_PACKET.relative_to(ROOT)).replace("\\", "/"),
        "adapter_in_sync": observed == expected,
        "registry_hash": registry["registry_hash"],
        "audit_index_packet_id": audit_index["audit_index_packet_id"],
        "audit_index_hash": audit_index["exact_payload_hash"],
        "readiness_status": audit_index["registry_readiness_status"],
        "non_readiness_claims_all_false": all(value is False for value in audit_index["non_readiness_claims"].values()),
        "enabled_live_controls": bool(audit_index["enabled_publish_send_dispatch_approve_controls"]),
        "network_call_made": False,
        "provider_call_made": False,
        "env_value_read_made": False,
        "credential_read_made": False,
        "browser_session_used": False,
        "public_url_fetch_made": False,
        "live_publish_performed_by_contentops": False,
    }


if __name__ == "__main__":
    status = check_manual_distribution_registry_v5_adapter_in_sync()
    print(json.dumps(status, indent=2, sort_keys=True))
    raise SystemExit(0 if status["adapter_in_sync"] else 1)
