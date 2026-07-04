"""X CDP exact separate live-click authorization request dry run.

Packages final pre-click rehearsal evidence into a local operator request packet.
It never launches/probes browsers, reads session state, clicks, publishes,
fetches public URLs, appends registries, schedules, retries, or calls providers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.x_cdp_final_pre_click_rehearsal_dry_run_v6 import (
    PACKET_KIND as FINAL_REHEARSAL_PACKET_KIND,
    PASS_STATUS as FINAL_REHEARSAL_PASS_STATUS,
    build_final_pre_click_rehearsal_packet,
)
from live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 import EXPECTED_GO_PHRASE, build_go_phrase_gate_packet
from live_contentops.x_cdp_separate_live_click_authorization_packet_dry_run_v6 import (
    build_live_click_authorization_packet,
    default_kill_switch_snapshot,
    default_rollback_checklist,
)
from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import (
    DEFAULT_ACCOUNT_BINDING_REF,
    DEFAULT_ACCOUNT_HANDLE,
    DEFAULT_DESTINATION_BINDING_REF,
    FALSE_SAFETY_FLAGS,
    build_prelive_post_packet,
)

TASK_LABEL = "TASK_CONTENTOPS_V6_X_CDP_EXACT_SEPARATE_LIVE_CLICK_AUTHORIZATION_REQUEST_V0"
PACKET_KIND = "x_cdp_exact_separate_live_click_authorization_request_v0"
PASS_STATUS = "EXACT_SEPARATE_LIVE_CLICK_AUTHORIZATION_REQUEST_READY_FOR_OPERATOR_REVIEW"
BLOCKED_STATUS = "BLOCKED_EXACT_SEPARATE_LIVE_CLICK_AUTHORIZATION_REQUEST_BEFORE_LIVE_CLICK"
DEFAULT_EVIDENCE_PATH = Path(
    "docs/automation/X_SUPERVISED_CDP_EXACT_LIVE_CLICK_AUTHORIZATION_REQUEST/"
    "task_contentops_v6_x_cdp_exact_live_click_authorization_request_evidence.json"
)


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def recompute_final_rehearsal_packet_id(packet: Mapping[str, Any]) -> str:
    passed = packet.get("ready_for_separate_exact_live_task") is True
    seed = {
        "kind": FINAL_REHEARSAL_PACKET_KIND,
        "prelive": packet.get("prelive_packet_id"),
        "go": packet.get("go_gate_packet_id"),
        "auth": packet.get("authorization_packet_id"),
        "payload_hash": packet.get("payload_hash") or "",
        "passed": passed,
    }
    return "x_final_pre_click_" + _sha(seed)[:16]


def future_exact_live_task_prerequisites() -> list[str]:
    return [
        "explicit_user_live_scope_approval_in_future_task",
        "payload_hash_matches_authorization_request",
        "prelive_packet_id_matches_authorization_request",
        "go_gate_packet_id_matches_authorization_request",
        "authorization_packet_id_matches_authorization_request",
        "final_rehearsal_packet_id_matches_authorization_request",
        "fresh_contentops_profile_guard_passes",
        "operator_confirms_account_and_destination_visible_in_x_ui",
        "kill_switch_reenabled_only_inside_future_exact_live_task",
        "post_click_public_url_capture_required_before_registry_append",
    ]


def future_operator_stop_conditions() -> list[dict[str, str]]:
    return [
        {"condition_id": "stop_001", "condition": "payload_or_packet_id_changed", "operator_action": "stop_without_click_and_regenerate_request"},
        {"condition_id": "stop_002", "condition": "profile_account_or_destination_uncertain", "operator_action": "stop_and_rerun_profile_guard"},
        {"condition_id": "stop_003", "condition": "x_compose_ui_or_button_uncertain", "operator_action": "stop_without_click"},
        {"condition_id": "stop_004", "condition": "post_click_public_url_capture_unavailable", "operator_action": "do_not_append_registry_record"},
        {"condition_id": "stop_005", "condition": "future_task_lacks_explicit_live_scope", "operator_action": "do_not_click"},
    ]


def build_exact_live_click_authorization_request(
    *,
    final_rehearsal_packet: Mapping[str, Any],
    expected_account_handle: str = DEFAULT_ACCOUNT_HANDLE,
    expected_account_binding_ref: str = DEFAULT_ACCOUNT_BINDING_REF,
    expected_destination_binding_ref: str = DEFAULT_DESTINATION_BINDING_REF,
) -> dict[str, Any]:
    payload_hash = str(final_rehearsal_packet.get("payload_hash") or "")
    registry = final_rehearsal_packet.get("registry_identity_expectation")
    capture = final_rehearsal_packet.get("post_click_capture_plan")
    checks = {
        "final_rehearsal_packet_kind_match": final_rehearsal_packet.get("packet_kind") == FINAL_REHEARSAL_PACKET_KIND,
        "final_rehearsal_status_ready": final_rehearsal_packet.get("final_rehearsal_status") == FINAL_REHEARSAL_PASS_STATUS,
        "final_rehearsal_packet_id_recomputed_match": final_rehearsal_packet.get("final_rehearsal_packet_id") == recompute_final_rehearsal_packet_id(final_rehearsal_packet),
        "final_rehearsal_ready_for_separate_exact_live_task": final_rehearsal_packet.get("ready_for_separate_exact_live_task") is True,
        "final_rehearsal_still_blocks_live_click_now": final_rehearsal_packet.get("live_click_allowed") is False
        and final_rehearsal_packet.get("live_click_performed") is False
        and final_rehearsal_packet.get("live_publish_performed") is False,
        "approval_and_outbox_not_created": final_rehearsal_packet.get("approval_ledger_entry_created") is False
        and final_rehearsal_packet.get("executable_outbox_entry_created") is False,
        "registry_and_public_url_not_written": final_rehearsal_packet.get("publication_registry_record_appended") is False
        and final_rehearsal_packet.get("public_url_capture_performed") is False,
        "payload_hash_shape_valid": len(payload_hash) == 64 and all(char in "0123456789abcdef" for char in payload_hash),
        "registry_identity_present": isinstance(registry, Mapping),
        "registry_account_handle_match": isinstance(registry, Mapping) and registry.get("account_handle_expected") == expected_account_handle,
        "registry_account_binding_match": isinstance(registry, Mapping) and registry.get("account_binding_ref") == expected_account_binding_ref,
        "registry_destination_binding_match": isinstance(registry, Mapping) and registry.get("destination_binding_ref") == expected_destination_binding_ref,
        "registry_payload_hash_match": isinstance(registry, Mapping) and registry.get("payload_hash") == payload_hash,
        "post_click_capture_plan_present": isinstance(capture, Mapping),
        "post_click_capture_plan_matches_payload_hash": isinstance(capture, Mapping) and capture.get("expected_payload_hash") == payload_hash,
        "post_click_capture_plan_requires_future_public_url": isinstance(capture, Mapping)
        and capture.get("public_url_capture_required_after_future_click") is True
        and capture.get("registry_append_requires_future_captured_public_url") is True,
        "post_click_capture_plan_non_executable_now": isinstance(capture, Mapping)
        and capture.get("registry_append_allowed_now") is False
        and capture.get("public_url_fetch_allowed") is False,
    }
    blockers = [name for name, ok in checks.items() if ok is not True]
    passed = not blockers
    packet = {
        "task_label": TASK_LABEL,
        "packet_kind": PACKET_KIND,
        "authorization_request_status": PASS_STATUS if passed else BLOCKED_STATUS,
        "blocked_reasons": blockers,
        "prelive_packet_id": final_rehearsal_packet.get("prelive_packet_id"),
        "go_gate_packet_id": final_rehearsal_packet.get("go_gate_packet_id"),
        "authorization_packet_id": final_rehearsal_packet.get("authorization_packet_id"),
        "final_rehearsal_packet_id": final_rehearsal_packet.get("final_rehearsal_packet_id"),
        "payload_hash": payload_hash or None,
        "checks": checks,
        "registry_identity_expectation": dict(registry) if isinstance(registry, Mapping) else None,
        "post_click_capture_plan": dict(capture) if isinstance(capture, Mapping) else None,
        "future_exact_live_task_prerequisites": future_exact_live_task_prerequisites(),
        "operator_stop_conditions": future_operator_stop_conditions(),
        "ready_for_operator_review": passed,
        "future_exact_live_task_required": True,
        "explicit_future_live_scope_required": True,
        "live_click_allowed_now": False,
        "live_click_allowed": False,
        "live_click_performed": False,
        "live_publish_performed": False,
        "approval_ledger_entry_created": False,
        "executable_outbox_entry_created": False,
        "publication_registry_record_appended": False,
        "public_url_capture_performed": False,
        "raw_go_phrase_stored": False,
        "blocked_before_live_click": True,
        **FALSE_SAFETY_FLAGS,
    }
    packet["authorization_request_id"] = "x_exact_live_request_" + _sha(
        {
            "kind": PACKET_KIND,
            "prelive": packet["prelive_packet_id"],
            "go": packet["go_gate_packet_id"],
            "auth": packet["authorization_packet_id"],
            "final": packet["final_rehearsal_packet_id"],
            "payload_hash": payload_hash,
            "passed": passed,
        }
    )[:16]
    return packet


def _approved_chain() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    expected_profile = r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
    cmd = rf'msedge.exe --remote-debugging-port=9223 --user-data-dir="{expected_profile}"'
    payload = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
    prelive = build_prelive_post_packet(payload_text=payload, cdp_port=9223, command_line=cmd)
    gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=EXPECTED_GO_PHRASE)
    auth = build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist())
    rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
    return prelive, gate, auth, rehearsal


def build_fixture_evidence_bundle() -> dict[str, Any]:
    _, _, _, rehearsal = _approved_chain()
    capture = rehearsal["post_click_capture_plan"]
    registry = rehearsal["registry_identity_expectation"]
    cases = {
        "approved_rehearsal_request_ready": build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal),
        "final_rehearsal_packet_id_mismatch_blocked": build_exact_live_click_authorization_request(final_rehearsal_packet={**rehearsal, "final_rehearsal_packet_id": "x_final_pre_click_mismatch"}),
        "final_rehearsal_not_ready_blocked": build_exact_live_click_authorization_request(final_rehearsal_packet={**rehearsal, "ready_for_separate_exact_live_task": False, "final_rehearsal_status": "BLOCKED_FINAL_PRE_CLICK_REHEARSAL_BEFORE_LIVE_CLICK"}),
        "payload_hash_mismatch_blocked": build_exact_live_click_authorization_request(final_rehearsal_packet={**rehearsal, "payload_hash": "0" * 64}),
        "missing_capture_plan_blocked": build_exact_live_click_authorization_request(final_rehearsal_packet={**rehearsal, "post_click_capture_plan": None}),
        "capture_plan_executable_now_blocked": build_exact_live_click_authorization_request(final_rehearsal_packet={**rehearsal, "post_click_capture_plan": {**capture, "registry_append_allowed_now": True}}),
        "registry_identity_mismatch_blocked": build_exact_live_click_authorization_request(final_rehearsal_packet={**rehearsal, "registry_identity_expectation": {**registry, "destination_binding_ref": "wrong_destination"}}),
    }
    return {
        "task_label": TASK_LABEL,
        "packet_kind": "x_cdp_exact_separate_live_click_authorization_request_evidence_bundle_v0",
        "case_count": len(cases),
        "cases": cases,
        "approved_case_ready_for_operator_review": cases["approved_rehearsal_request_ready"]["ready_for_operator_review"] is True,
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
    parser = argparse.ArgumentParser(description="Dry-run exact X CDP live-click authorization request. No browser probe or click.")
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
    rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
    result = build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ready_for_operator_review"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
