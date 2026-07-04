"""Final X CDP pre-click rehearsal dry run.

Composes the local X pre-live, GO-gate, and authorization packets into a final
operator rehearsal. It never launches/probes browsers, reads session state,
clicks, publishes, fetches public URLs, appends registries, schedules, retries,
or calls providers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 import (
    EXPECTED_GO_PHRASE,
    build_go_phrase_gate_packet,
    recompute_prelive_packet_id,
)
from live_contentops.x_cdp_separate_live_click_authorization_packet_dry_run_v6 import (
    PACKET_KIND as AUTH_PACKET_KIND,
    PASS_STATUS as AUTH_PASS_STATUS,
    build_live_click_authorization_packet,
    default_kill_switch_snapshot,
    default_rollback_checklist,
    recompute_go_gate_packet_id,
)
from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import (
    DEFAULT_ACCOUNT_BINDING_REF,
    DEFAULT_ACCOUNT_HANDLE,
    DEFAULT_DESTINATION_BINDING_REF,
    FALSE_SAFETY_FLAGS,
    build_prelive_post_packet,
    stable_payload_hash,
)

TASK_LABEL = "TASK_CONTENTOPS_V6_X_CDP_FINAL_PRE_CLICK_REHEARSAL_DRY_RUN_V0"
PACKET_KIND = "x_cdp_final_pre_click_rehearsal_dry_run_v0"
PASS_STATUS = "FINAL_PRE_CLICK_REHEARSAL_READY_FOR_SEPARATE_EXACT_LIVE_TASK"
BLOCKED_STATUS = "BLOCKED_FINAL_PRE_CLICK_REHEARSAL_BEFORE_LIVE_CLICK"
DEFAULT_EVIDENCE_PATH = Path(
    "docs/automation/X_SUPERVISED_CDP_FINAL_PRE_CLICK_REHEARSAL/"
    "task_contentops_v6_x_cdp_final_pre_click_rehearsal_dry_run_evidence.json"
)


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def recompute_authorization_packet_id(packet: Mapping[str, Any]) -> str:
    passed = packet.get("ready_for_exact_separate_live_task") is True
    seed = {
        "kind": AUTH_PACKET_KIND,
        "prelive": packet.get("prelive_packet_id"),
        "go": packet.get("go_gate_packet_id"),
        "payload_hash": packet.get("payload_hash") or "",
        "passed": passed,
    }
    return "x_live_click_auth_" + _sha(seed)[:16]


def final_operator_stop_conditions() -> list[dict[str, str]]:
    return [
        {"condition_id": "stop_001", "condition": "payload_hash_or_packet_id_changed", "operator_action": "stop_and_regenerate_rehearsal"},
        {"condition_id": "stop_002", "condition": "profile_or_destination_uncertain", "operator_action": "stop_and_rerun_profile_guard"},
        {"condition_id": "stop_003", "condition": "x_ui_differs_from_expected_compose_surface", "operator_action": "stop_without_click"},
        {"condition_id": "stop_004", "condition": "post_click_capture_unavailable_in_future_live_task", "operator_action": "do_not_append_registry_record"},
    ]


def build_final_pre_click_rehearsal_packet(
    *,
    prelive_packet: Mapping[str, Any],
    go_gate_packet: Mapping[str, Any],
    authorization_packet: Mapping[str, Any],
    expected_account_handle: str = DEFAULT_ACCOUNT_HANDLE,
    expected_account_binding_ref: str = DEFAULT_ACCOUNT_BINDING_REF,
    expected_destination_binding_ref: str = DEFAULT_DESTINATION_BINDING_REF,
) -> dict[str, Any]:
    payload_text = str(prelive_packet.get("payload_text") or "")
    payload_hash = str(prelive_packet.get("payload_hash") or "")
    registry = prelive_packet.get("registry_identity_expectation")
    auth_capture = authorization_packet.get("post_click_capture_plan")
    auth_kill_switch = authorization_packet.get("kill_switch_snapshot")
    auth_rollback = authorization_packet.get("rollback_checklist")

    checks = {
        "prelive_packet_id_recomputed_match": prelive_packet.get("prelive_packet_id") == recompute_prelive_packet_id(prelive_packet),
        "payload_hash_recomputed_match": bool(payload_text.strip()) and payload_hash == stable_payload_hash(payload_text.strip()),
        "go_gate_packet_id_recomputed_match": go_gate_packet.get("go_gate_packet_id") == recompute_go_gate_packet_id(go_gate_packet),
        "go_gate_references_prelive_packet": go_gate_packet.get("prelive_packet_id") == prelive_packet.get("prelive_packet_id"),
        "go_gate_references_payload_hash": go_gate_packet.get("payload_hash") == payload_hash,
        "go_gate_ready_for_separate_live_task": go_gate_packet.get("future_live_click_eligible_after_separate_live_task") is True,
        "authorization_packet_kind_match": authorization_packet.get("packet_kind") == AUTH_PACKET_KIND,
        "authorization_packet_status_ready": authorization_packet.get("authorization_packet_status") == AUTH_PASS_STATUS,
        "authorization_packet_id_recomputed_match": authorization_packet.get("authorization_packet_id") == recompute_authorization_packet_id(authorization_packet),
        "authorization_references_prelive_packet": authorization_packet.get("prelive_packet_id") == prelive_packet.get("prelive_packet_id"),
        "authorization_references_go_gate_packet": authorization_packet.get("go_gate_packet_id") == go_gate_packet.get("go_gate_packet_id"),
        "authorization_references_payload_hash": authorization_packet.get("payload_hash") == payload_hash,
        "authorization_still_non_executable": authorization_packet.get("live_click_allowed") is False
        and authorization_packet.get("live_click_performed") is False
        and authorization_packet.get("publication_registry_record_appended") is False
        and authorization_packet.get("public_url_capture_performed") is False,
        "registry_identity_present": isinstance(registry, Mapping),
        "registry_account_handle_match": isinstance(registry, Mapping) and registry.get("account_handle_expected") == expected_account_handle,
        "registry_account_binding_match": isinstance(registry, Mapping) and registry.get("account_binding_ref") == expected_account_binding_ref,
        "registry_destination_binding_match": isinstance(registry, Mapping) and registry.get("destination_binding_ref") == expected_destination_binding_ref,
        "kill_switch_blocks_live_click_now": isinstance(auth_kill_switch, Mapping)
        and auth_kill_switch.get("kill_switch_active_for_live_click_until_exact_live_task") is True
        and auth_kill_switch.get("live_click_enabled_now") is False,
        "rollback_checklist_present": isinstance(auth_rollback, Sequence) and len(auth_rollback) >= 3,
        "post_click_capture_plan_present": isinstance(auth_capture, Mapping),
        "post_click_capture_plan_matches_payload_hash": isinstance(auth_capture, Mapping) and auth_capture.get("expected_payload_hash") == payload_hash,
        "post_click_capture_plan_requires_future_public_url": isinstance(auth_capture, Mapping)
        and auth_capture.get("public_url_capture_required_after_future_click") is True
        and auth_capture.get("registry_append_requires_future_captured_public_url") is True,
        "post_click_capture_plan_non_executable_now": isinstance(auth_capture, Mapping)
        and auth_capture.get("registry_append_allowed_now") is False
        and auth_capture.get("public_url_fetch_allowed") is False,
    }
    blockers = [name for name, ok in checks.items() if ok is not True]
    passed = not blockers
    packet = {
        "task_label": TASK_LABEL,
        "packet_kind": PACKET_KIND,
        "final_rehearsal_status": PASS_STATUS if passed else BLOCKED_STATUS,
        "blocked_reasons": blockers,
        "prelive_packet_id": prelive_packet.get("prelive_packet_id"),
        "go_gate_packet_id": go_gate_packet.get("go_gate_packet_id"),
        "authorization_packet_id": authorization_packet.get("authorization_packet_id"),
        "payload_hash": payload_hash or None,
        "checks": checks,
        "operator_stop_conditions": final_operator_stop_conditions(),
        "post_click_capture_plan": dict(auth_capture) if isinstance(auth_capture, Mapping) else None,
        "registry_identity_expectation": dict(registry) if isinstance(registry, Mapping) else None,
        "ready_for_separate_exact_live_task": passed,
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
        "raw_go_phrase_stored": False,
        **FALSE_SAFETY_FLAGS,
    }
    packet["final_rehearsal_packet_id"] = "x_final_pre_click_" + _sha(
        {"kind": PACKET_KIND, "prelive": packet["prelive_packet_id"], "go": packet["go_gate_packet_id"], "auth": packet["authorization_packet_id"], "payload_hash": payload_hash, "passed": passed}
    )[:16]
    return packet


def _approved_chain() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    expected_profile = r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
    cmd = rf'msedge.exe --remote-debugging-port=9223 --user-data-dir="{expected_profile}"'
    payload = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
    prelive = build_prelive_post_packet(payload_text=payload, cdp_port=9223, command_line=cmd)
    gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=EXPECTED_GO_PHRASE)
    auth = build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist())
    return prelive, gate, auth


def build_fixture_evidence_bundle() -> dict[str, Any]:
    prelive, gate, auth = _approved_chain()
    broken_auth_capture = {**auth, "post_click_capture_plan": {**auth["post_click_capture_plan"], "expected_payload_hash": "0" * 64}}
    cases = {
        "approved_chain_rehearsal_ready": build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth),
        "authorization_packet_mismatch_blocked": build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet={**auth, "authorization_packet_id": "x_live_click_auth_mismatch"}),
        "prelive_packet_mismatch_blocked": build_final_pre_click_rehearsal_packet(prelive_packet={**prelive, "prelive_packet_id": "x_prelive_mismatch"}, go_gate_packet=gate, authorization_packet=auth),
        "go_gate_packet_mismatch_blocked": build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet={**gate, "go_gate_packet_id": "x_go_gate_mismatch"}, authorization_packet=auth),
        "missing_capture_plan_blocked": build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet={**auth, "post_click_capture_plan": None}),
        "kill_switch_disabled_blocked": build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet={**auth, "kill_switch_snapshot": {**auth["kill_switch_snapshot"], "live_click_enabled_now": True}}),
        "registry_capture_inconsistency_blocked": build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=broken_auth_capture),
    }
    return {
        "task_label": TASK_LABEL,
        "packet_kind": "x_cdp_final_pre_click_rehearsal_dry_run_evidence_bundle_v0",
        "case_count": len(cases),
        "cases": cases,
        "approved_case_ready_for_separate_exact_live_task": cases["approved_chain_rehearsal_ready"]["ready_for_separate_exact_live_task"] is True,
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
    parser = argparse.ArgumentParser(description="Dry-run final X CDP pre-click rehearsal. No browser probe or click.")
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
    auth = build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist())
    result = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ready_for_separate_exact_live_task"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
