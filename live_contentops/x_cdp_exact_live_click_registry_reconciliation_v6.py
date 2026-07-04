"""X CDP exact live-click registry reconciliation.

Reconciles an operator-supplied exact live-click execution outcome into the local
publication identity registry. This module does not launch browsers, probe CDP,
read session state, call APIs, fetch public URLs, dispatch, retry, comment, DM,
react, or publish.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.platform_publication_identity_registry_v6 import (
    DEFAULT_REGISTRY_PATH,
    EXACT_LIVE_CLICK_CAPTURE_METHOD,
    extract_x_status_identity,
    validate_exact_live_click_execution_for_registry,
    validate_registry_record,
)
from live_contentops.x_cdp_exact_live_click_execution_v6 import (
    EXECUTED_STATUS,
    build_fixture_evidence_bundle as build_execution_fixture_evidence_bundle,
)

TASK_LABEL = "TASK_CONTENTOPS_V6_X_CDP_EXACT_LIVE_CLICK_REGISTRY_RECONCILIATION_V0"
PACKET_KIND = "x_cdp_exact_live_click_registry_reconciliation_v0"
APPENDED_STATUS = "APPENDED_PUBLICATION_REGISTRY_ROW"
RECONCILED_EXISTING_STATUS = "RECONCILED_EXISTING_PUBLICATION_REGISTRY_ROW"
BLOCKED_STATUS = "BLOCKED_PUBLICATION_REGISTRY_RECONCILIATION"
DEFAULT_EVIDENCE_PATH = Path(
    "docs/automation/X_SUPERVISED_CDP_EXACT_LIVE_CLICK_REGISTRY_RECONCILIATION/"
    "task_contentops_v6_x_cdp_exact_live_click_registry_reconciliation_evidence.json"
)

NO_LIVE_ACTION_FLAGS = {
    "browser_launch_performed": False,
    "browser_or_cdp_probe_performed": False,
    "cookie_read_performed": False,
    "local_storage_read_performed": False,
    "session_storage_read_performed": False,
    "token_or_header_read_performed": False,
    "dom_read_performed": False,
    "x_api_used": False,
    "provider_call_made": False,
    "public_url_fetch_made": False,
    "scheduler_enabled": False,
    "retry_enabled": False,
    "network_call_made": False,
    "credential_read_made": False,
    "env_value_read_made": False,
    "live_publish_performed": False,
}


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _payload_hash_valid(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(dict(row), ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(payload, encoding="utf-8")


def stable_registry_row_id(*, public_url: str, payload_hash: str, exact_live_execution_id: str) -> str:
    return "pubid_x_exact_" + _sha({
        "platform": "x",
        "public_url": public_url,
        "payload_hash": payload_hash,
        "exact_live_execution_id": exact_live_execution_id,
    })[:16]


def build_registry_row(execution_packet: Mapping[str, Any]) -> dict[str, Any]:
    validate_exact_live_click_execution_for_registry(dict(execution_packet))
    public_url = str(execution_packet["captured_public_x_url"])
    payload_hash = str(execution_packet["payload_hash"])
    exact_live_execution_id = str(execution_packet["exact_live_execution_id"])
    identity = extract_x_status_identity(public_url)
    row = {
        "registry_record_id": stable_registry_row_id(
            public_url=identity["public_url"],
            payload_hash=payload_hash,
            exact_live_execution_id=exact_live_execution_id,
        ),
        "platform": "x",
        "payload_hash": payload_hash,
        "public_url": identity["public_url"],
        "source_host": identity["source_host"],
        "handle": identity["handle"],
        "platform_publication_id": identity["platform_publication_id"],
        "thread_root_url": identity["public_url"],
        "capture_method": EXACT_LIVE_CLICK_CAPTURE_METHOD,
        "confirmation_class": "local_reconciled_from_exact_live_click_execution_packet",
        "dispatch_attempt_id": exact_live_execution_id,
        "approval_id": execution_packet.get("exact_live_authorization_id"),
        "exact_live_execution_id": exact_live_execution_id,
        "execution_prep_id": execution_packet.get("execution_prep_id"),
        "source_execution_packet_kind": execution_packet.get("packet_kind"),
        "source_execution_status": execution_packet.get("execution_status"),
        "operator_confirmed_account_destination_hash": execution_packet.get("operator_confirmed_account_destination_hash"),
        "no_paid_api_used": True,
        "cookie_read_performed": False,
        "local_storage_read_performed": False,
        "session_storage_read_performed": False,
        "token_or_header_read_performed": False,
        "raw_secret_output": False,
    }
    validate_registry_record(row)
    return row


def _find_matching_row(rows: Sequence[Mapping[str, Any]], row: Mapping[str, Any]) -> Mapping[str, Any] | None:
    for existing in rows:
        if existing.get("registry_record_id") == row.get("registry_record_id"):
            return existing
        if (
            existing.get("platform") == "x"
            and existing.get("public_url") == row.get("public_url")
            and existing.get("payload_hash") == row.get("payload_hash")
            and existing.get("exact_live_execution_id") == row.get("exact_live_execution_id")
        ):
            return existing
    return None


def reconcile_registry(
    execution_packet: Mapping[str, Any],
    *,
    registry_path: Path | str = DEFAULT_REGISTRY_PATH,
    append_registry: bool = False,
) -> dict[str, Any]:
    checks = {
        "execution_status_executed": execution_packet.get("execution_status") == EXECUTED_STATUS,
        "registry_append_ready": execution_packet.get("registry_append_ready") is True,
        "registry_not_already_appended": execution_packet.get("publication_registry_record_appended") is False,
        "payload_hash_shape_valid": _payload_hash_valid(str(execution_packet.get("payload_hash") or "")),
        "operator_account_destination_hash_present": bool(execution_packet.get("operator_confirmed_account_destination_hash")),
    }
    for key, expected in NO_LIVE_ACTION_FLAGS.items():
        if key in execution_packet:
            checks[f"no_{key}"] = execution_packet.get(key) is expected
    row: dict[str, Any] | None = None
    validation_error: str | None = None
    try:
        row = build_registry_row(execution_packet)
    except ValueError as exc:
        validation_error = str(exc)
        checks["execution_packet_registry_validation"] = False
    else:
        checks["execution_packet_registry_validation"] = True

    blockers = [name for name, ok in checks.items() if ok is not True]
    path = Path(registry_path)
    rows = _load_jsonl(path)
    existing = _find_matching_row(rows, row) if row else None
    status = BLOCKED_STATUS
    rows_written = 0
    if not blockers and row:
        if existing is not None:
            status = RECONCILED_EXISTING_STATUS
        elif append_registry:
            rows.append(row)
            _write_jsonl(path, rows)
            rows_written = 1
            status = APPENDED_STATUS
        else:
            status = APPENDED_STATUS

    packet = {
        "task_label": TASK_LABEL,
        "packet_kind": PACKET_KIND,
        "reconciliation_status": status,
        "blocked_reasons": blockers,
        "validation_error": validation_error,
        "registry_path": str(path),
        "append_registry_requested": append_registry,
        "registry_rows_seen_before": len(rows) - rows_written,
        "registry_rows_written": rows_written,
        "idempotent_existing_match": existing is not None,
        "registry_row": row if not blockers else None,
        "source_exact_live_execution_id": execution_packet.get("exact_live_execution_id"),
        "payload_hash": execution_packet.get("payload_hash"),
        "captured_public_x_url": execution_packet.get("captured_public_x_url"),
        "checks": checks,
        "local_registry_reconciliation_only": True,
        "public_url_verified_externally": False,
        **NO_LIVE_ACTION_FLAGS,
    }
    packet["reconciliation_id"] = "x_registry_reconcile_" + _sha({
        "kind": PACKET_KIND,
        "status": status,
        "execution_id": packet["source_exact_live_execution_id"],
        "payload_hash": packet["payload_hash"],
        "url": packet["captured_public_x_url"],
    })[:16]
    return packet


def _ready_execution_case() -> dict[str, Any]:
    bundle = build_execution_fixture_evidence_bundle()
    return dict(bundle["cases"]["operator_confirmed_click_with_captured_public_url"])


def build_fixture_evidence_bundle() -> dict[str, Any]:
    ready = _ready_execution_case()
    cases = {
        "ready_case_appends_registry_row": reconcile_registry(ready),
        "payload_hash_mismatch_blocked": reconcile_registry({**ready, "operator_confirmed_payload_hash": "0" * 64}),
        "invalid_public_url_blocked": reconcile_registry({**ready, "captured_public_x_url": "https://x.com/capitalchronicle"}),
        "prior_registry_append_blocked": reconcile_registry({**ready, "publication_registry_record_appended": True}),
        "not_ready_execution_blocked": reconcile_registry({**ready, "execution_status": "BLOCKED_EXACT_LIVE_CLICK_EXECUTION", "registry_append_ready": False}),
    }
    return {
        "task_label": TASK_LABEL,
        "packet_kind": "x_cdp_exact_live_click_registry_reconciliation_evidence_bundle_v0",
        "case_count": len(cases),
        "cases": cases,
        "ready_case_registry_reconciled": cases["ready_case_appends_registry_row"]["reconciliation_status"] == APPENDED_STATUS,
        "blocked_cases_blocked": all(
            case["reconciliation_status"] == BLOCKED_STATUS
            for name, case in cases.items()
            if name != "ready_case_appends_registry_row"
        ),
        "local_registry_reconciliation_only": True,
        "public_url_verified_externally": False,
        **NO_LIVE_ACTION_FLAGS,
    }


def write_fixture_evidence(path: Path = DEFAULT_EVIDENCE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_fixture_evidence_bundle(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reconcile exact X live-click outcome into local registry. No browser/API/public fetch.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fixture-bundle", action="store_true")
    parser.add_argument("--append-registry", action="store_true")
    parser.add_argument("--registry-path", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--write-evidence", type=Path, default=None)
    args = parser.parse_args(argv)
    if not args.dry_run:
        print(json.dumps({"status": "blocked_dry_run_flag_required", "publication_registry_record_appended": False}, sort_keys=True))
        return 2
    result = build_fixture_evidence_bundle() if args.fixture_bundle else reconcile_registry(
        _ready_execution_case(),
        registry_path=args.registry_path,
        append_registry=args.append_registry,
    )
    if args.write_evidence:
        args.write_evidence.parent.mkdir(parents=True, exist_ok=True)
        args.write_evidence.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    blocked = result.get("reconciliation_status") == BLOCKED_STATUS
    return 2 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
