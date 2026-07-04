"""X CDP separate live-click authorization packet dry run.

Composes pre-live and GO-phrase evidence into a final non-executable packet.
It never launches/probes browsers, reads session state, appends registries,
clicks, publishes, fetches public URLs, schedules, retries, or calls providers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 import (
    EXPECTED_GO_PHRASE,
    PACKET_KIND as GO_GATE_PACKET_KIND,
    PASS_STATUS as GO_GATE_PASS_STATUS,
    build_go_phrase_gate_packet,
    recompute_prelive_packet_id,
)
from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import (
    DEFAULT_ACCOUNT_BINDING_REF,
    DEFAULT_ACCOUNT_HANDLE,
    DEFAULT_DESTINATION_BINDING_REF,
    FALSE_SAFETY_FLAGS,
    build_prelive_post_packet,
    stable_payload_hash,
)

TASK_LABEL = "TASK_CONTENTOPS_V6_X_CDP_SEPARATE_LIVE_CLICK_AUTHORIZATION_PACKET_DRY_RUN_V0"
PACKET_KIND = "x_cdp_separate_live_click_authorization_packet_dry_run_v0"
PASS_STATUS = "AUTHORIZATION_PACKET_READY_FOR_EXACT_SEPARATE_LIVE_TASK"
BLOCKED_STATUS = "BLOCKED_AUTHORIZATION_PACKET_BEFORE_LIVE_CLICK"
DEFAULT_EVIDENCE_PATH = Path(
    "docs/automation/X_SUPERVISED_CDP_LIVE_CLICK_AUTHORIZATION_PACKET/"
    "task_contentops_v6_x_cdp_separate_live_click_authorization_packet_dry_run_evidence.json"
)


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def recompute_go_gate_packet_id(packet: Mapping[str, Any]) -> str:
    passed = packet.get("future_live_click_eligible_after_separate_live_task") is True
    seed = {"kind": GO_GATE_PACKET_KIND, "prelive": packet.get("prelive_packet_id"), "payload_hash": packet.get("payload_hash"), "passed": passed}
    return "x_go_gate_" + _sha(seed)[:16]


def default_kill_switch_snapshot() -> dict[str, Any]:
    return {
        "kill_switch_snapshot_id": "x_kill_switch_snapshot_dry_run_v0",
        "platform": "x",
        "state": "operator_acknowledged_pre_live_hold",
        "kill_switch_active_for_live_click_until_exact_live_task": True,
        "scheduler_enabled": False,
        "retry_enabled": False,
        "live_click_enabled_now": False,
        "operator_reenable_requires_separate_exact_live_task": True,
    }


def default_rollback_checklist() -> list[dict[str, str]]:
    return [
        {"check_id": "rollback_001", "trigger": "payload_or_packet_hash_mismatch", "action": "stop_before_click_and_regenerate_prelive_packet"},
        {"check_id": "rollback_002", "trigger": "profile_or_account_uncertainty", "action": "stop_before_click_and_reopen_contentops_profile_guard"},
        {"check_id": "rollback_003", "trigger": "unexpected_network_or_browser_action", "action": "engage_kill_switch_and_quarantine_run"},
        {"check_id": "rollback_004", "trigger": "post_click_public_url_not_captured_in_future_live_task", "action": "do_not_append_registry_record_and_start_manual_reconciliation"},
    ]


def post_click_capture_plan(payload_hash: str | None) -> dict[str, Any]:
    return {
        "capture_plan_id": "x_post_click_capture_plan_dry_run_v0",
        "expected_capture_method_after_future_click": "x_cdp_post_detail_after_click",
        "expected_payload_hash": payload_hash,
        "public_url_capture_required_after_future_click": True,
        "visible_text_match_required_after_future_click": True,
        "x_status_url_required_after_future_click": True,
        "registry_append_allowed_now": False,
        "registry_append_requires_future_captured_public_url": True,
        "public_url_fetch_allowed": False,
    }


def build_live_click_authorization_packet(
    *,
    prelive_packet: Mapping[str, Any],
    go_gate_packet: Mapping[str, Any],
    kill_switch_snapshot: Mapping[str, Any] | None = None,
    rollback_checklist: Sequence[Mapping[str, Any]] | None = None,
    expected_account_handle: str = DEFAULT_ACCOUNT_HANDLE,
    expected_account_binding_ref: str = DEFAULT_ACCOUNT_BINDING_REF,
    expected_destination_binding_ref: str = DEFAULT_DESTINATION_BINDING_REF,
) -> dict[str, Any]:
    registry = prelive_packet.get("registry_identity_expectation")
    guard = prelive_packet.get("profile_guard_report")
    payload_text = str(prelive_packet.get("payload_text") or "")
    payload_hash = str(prelive_packet.get("payload_hash") or "")
    kill_switch = dict(kill_switch_snapshot or {})
    rollback = [dict(item) for item in (rollback_checklist or [])]
    capture = post_click_capture_plan(payload_hash or None)
    checks = {
        "prelive_packet_id_recomputed_match": prelive_packet.get("prelive_packet_id") == recompute_prelive_packet_id(prelive_packet),
        "payload_hash_recomputed_match": bool(payload_text.strip()) and payload_hash == stable_payload_hash(payload_text.strip()),
        "go_gate_packet_kind_match": go_gate_packet.get("packet_kind") == GO_GATE_PACKET_KIND,
        "go_gate_status_ready": go_gate_packet.get("go_packet_status") == GO_GATE_PASS_STATUS,
        "go_gate_packet_id_recomputed_match": go_gate_packet.get("go_gate_packet_id") == recompute_go_gate_packet_id(go_gate_packet),
        "go_gate_references_same_prelive_packet": go_gate_packet.get("prelive_packet_id") == prelive_packet.get("prelive_packet_id"),
        "go_gate_references_same_payload_hash": go_gate_packet.get("payload_hash") == payload_hash,
        "go_gate_future_eligible_signal_match": go_gate_packet.get("future_live_click_eligible_after_separate_live_task") is True,
        "go_gate_still_blocks_live_click_now": go_gate_packet.get("live_click_allowed") is False and go_gate_packet.get("live_click_performed") is False,
        "profile_guard_status_match": isinstance(guard, Mapping) and guard.get("profile_guard_status") == "contentops_profile_ok",
        "registry_identity_present": isinstance(registry, Mapping),
        "registry_platform_match": isinstance(registry, Mapping) and registry.get("platform") == "x",
        "registry_account_handle_match": isinstance(registry, Mapping) and registry.get("account_handle_expected") == expected_account_handle,
        "registry_account_binding_match": isinstance(registry, Mapping) and registry.get("account_binding_ref") == expected_account_binding_ref,
        "registry_destination_binding_match": isinstance(registry, Mapping) and registry.get("destination_binding_ref") == expected_destination_binding_ref,
        "registry_append_still_blocked_now": isinstance(registry, Mapping) and registry.get("registry_append_allowed_now") is False,
        "kill_switch_snapshot_present": bool(kill_switch),
        "kill_switch_blocks_live_click_now": kill_switch.get("kill_switch_active_for_live_click_until_exact_live_task") is True,
        "kill_switch_requires_separate_live_task": kill_switch.get("operator_reenable_requires_separate_exact_live_task") is True,
        "rollback_checklist_present": len(rollback) >= 3,
        "post_click_capture_plan_present": capture["public_url_capture_required_after_future_click"] is True,
        "post_click_capture_plan_non_executable": capture["registry_append_allowed_now"] is False and capture["public_url_fetch_allowed"] is False,
    }
    blockers = [name for name, ok in checks.items() if ok is not True]
    passed = not blockers
    packet = {
        "task_label": TASK_LABEL,
        "packet_kind": PACKET_KIND,
        "authorization_packet_status": PASS_STATUS if passed else BLOCKED_STATUS,
        "blocked_reasons": blockers,
        "prelive_packet_id": prelive_packet.get("prelive_packet_id"),
        "go_gate_packet_id": go_gate_packet.get("go_gate_packet_id"),
        "payload_hash": payload_hash or None,
        "checks": checks,
        "kill_switch_snapshot": kill_switch or None,
        "rollback_checklist": rollback,
        "post_click_capture_plan": capture,
        "registry_identity_expectation": dict(registry) if isinstance(registry, Mapping) else None,
        "profile_guard_status": guard.get("profile_guard_status") if isinstance(guard, Mapping) else None,
        "ready_for_exact_separate_live_task": passed,
        "operator_review_required": True,
        "separate_exact_live_task_required": True,
        "approval_ledger_entry_created": False,
        "executable_outbox_entry_created": False,
        "blocked_before_live_click": True,
        "live_click_allowed": False,
        "live_click_performed": False,
        "live_publish_performed": False,
        "publication_registry_record_appended": False,
        "public_url_capture_performed": False,
        **FALSE_SAFETY_FLAGS,
    }
    packet["authorization_packet_id"] = "x_live_click_auth_" + _sha({"kind": PACKET_KIND, "prelive": packet["prelive_packet_id"], "go": packet["go_gate_packet_id"], "payload_hash": payload_hash, "passed": passed})[:16]
    return packet


def _approved_chain() -> tuple[dict[str, Any], dict[str, Any]]:
    expected_profile = r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
    cmd = rf'msedge.exe --remote-debugging-port=9223 --user-data-dir="{expected_profile}"'
    payload = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
    prelive = build_prelive_post_packet(payload_text=payload, cdp_port=9223, command_line=cmd)
    gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=EXPECTED_GO_PHRASE)
    return prelive, gate


def build_fixture_evidence_bundle() -> dict[str, Any]:
    prelive, gate = _approved_chain()
    cases = {
        "approved_chain_ready_for_separate_live_task": build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist()),
        "go_gate_mismatch_blocked": build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=dict(gate, go_gate_packet_id="x_go_gate_mismatch"), kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist()),
        "payload_hash_mismatch_blocked": build_live_click_authorization_packet(prelive_packet=dict(prelive, payload_hash="0" * 64), go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist()),
        "kill_switch_missing_blocked": build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, rollback_checklist=default_rollback_checklist()),
        "rollback_missing_blocked": build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=[]),
        "registry_identity_mismatch_blocked": build_live_click_authorization_packet(prelive_packet=dict(prelive, registry_identity_expectation={**prelive["registry_identity_expectation"], "account_handle_expected": "WrongHandle"}), go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist()),
    }
    return {
        "task_label": TASK_LABEL,
        "packet_kind": "x_cdp_separate_live_click_authorization_packet_dry_run_evidence_bundle_v0",
        "case_count": len(cases),
        "cases": cases,
        "approved_case_ready_for_separate_live_task": cases["approved_chain_ready_for_separate_live_task"]["ready_for_exact_separate_live_task"] is True,
        "all_cases_blocked_before_click": all(case["blocked_before_live_click"] is True for case in cases.values()),
        "raw_go_phrase_stored_anywhere": False,
        "live_action_performed": False,
        "registry_append_performed": False,
        "public_url_capture_performed": False,
    }


def write_fixture_evidence(path: Path = DEFAULT_EVIDENCE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_fixture_evidence_bundle(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run X CDP separate live-click authorization packet. No browser probe or click.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fixture-bundle", action="store_true")
    parser.add_argument("--write-evidence", type=Path, default=None)
    parser.add_argument("--payload-text", default="")
    parser.add_argument("--operator-go-phrase", default="")
    parser.add_argument("--cdp-port", type=int, default=9222)
    parser.add_argument("--expected-profile-root", type=Path, default=Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"))
    parser.add_argument("--command-line", default=None)
    args = parser.parse_args(argv)
    if not args.dry_run:
        print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_allowed": False}, sort_keys=True))
        return 2
    if args.fixture_bundle:
        if args.write_evidence:
            write_fixture_evidence(args.write_evidence)
        print(json.dumps(build_fixture_evidence_bundle(), indent=2, sort_keys=True))
        return 0
    prelive = build_prelive_post_packet(payload_text=args.payload_text, cdp_port=args.cdp_port, command_line=args.command_line, expected_profile_root=args.expected_profile_root)
    gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=args.operator_go_phrase)
    result = build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ready_for_exact_separate_live_task"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
