"""X CDP exact separate live-click scope decision dry run.

Records Jim/operator live-scope decision metadata for a previously built
local authorization request. It never launches/probes browsers, reads session
state, clicks, publishes, fetches public URLs, appends registries, schedules,
retries, or calls providers.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.x_cdp_exact_separate_live_click_authorization_request_v6 import (
    PACKET_KIND as AUTHORIZATION_REQUEST_PACKET_KIND,
    PASS_STATUS as AUTHORIZATION_REQUEST_PASS_STATUS,
    build_exact_live_click_authorization_request,
)
from live_contentops.x_cdp_final_pre_click_rehearsal_dry_run_v6 import build_final_pre_click_rehearsal_packet
from live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 import EXPECTED_GO_PHRASE, build_go_phrase_gate_packet
from live_contentops.x_cdp_separate_live_click_authorization_packet_dry_run_v6 import (
    build_live_click_authorization_packet,
    default_kill_switch_snapshot,
    default_rollback_checklist,
)
from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import FALSE_SAFETY_FLAGS, build_prelive_post_packet

TASK_LABEL = "TASK_CONTENTOPS_V6_X_CDP_EXACT_SEPARATE_LIVE_CLICK_SCOPE_DECISION_V0"
PACKET_KIND = "x_cdp_exact_separate_live_click_scope_decision_v0"
DENIED_STATUS = "DENIED_NO_LIVE_SCOPE"
DEFERRED_STATUS = "DEFERRED_NEEDS_OPERATOR_REVIEW"
APPROVED_FUTURE_STATUS = "APPROVED_FOR_FUTURE_EXACT_LIVE_TASK"
BLOCKED_STATUS = "BLOCKED_SCOPE_DECISION_BEFORE_LIVE_CLICK"
DEFAULT_EVIDENCE_PATH = Path(
    "docs/automation/X_SUPERVISED_CDP_EXACT_LIVE_CLICK_SCOPE_DECISION/"
    "task_contentops_v6_x_cdp_exact_live_click_scope_decision_evidence.json"
)
VALID_DECISIONS = {"deny", "defer", "approve_future_scope"}


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def recompute_authorization_request_id(packet: Mapping[str, Any]) -> str:
    passed = packet.get("ready_for_operator_review") is True
    seed = {
        "kind": AUTHORIZATION_REQUEST_PACKET_KIND,
        "prelive": packet.get("prelive_packet_id"),
        "go": packet.get("go_gate_packet_id"),
        "auth": packet.get("authorization_packet_id"),
        "final": packet.get("final_rehearsal_packet_id"),
        "payload_hash": packet.get("payload_hash") or "",
        "passed": passed,
    }
    return "x_exact_live_request_" + _sha(seed)[:16]


def _status_for_decision(decision: str) -> str:
    if decision == "deny":
        return DENIED_STATUS
    if decision == "defer":
        return DEFERRED_STATUS
    if decision == "approve_future_scope":
        return APPROVED_FUTURE_STATUS
    return BLOCKED_STATUS


def build_scope_decision_packet(*, authorization_request_packet: Mapping[str, Any], scope_decision: str) -> dict[str, Any]:
    payload_hash = str(authorization_request_packet.get("payload_hash") or "")
    capture = authorization_request_packet.get("post_click_capture_plan")
    registry = authorization_request_packet.get("registry_identity_expectation")
    prerequisites = authorization_request_packet.get("future_exact_live_task_prerequisites")
    stop_conditions = authorization_request_packet.get("operator_stop_conditions")
    checks = {
        "authorization_request_kind_match": authorization_request_packet.get("packet_kind") == AUTHORIZATION_REQUEST_PACKET_KIND,
        "authorization_request_status_ready": authorization_request_packet.get("authorization_request_status") == AUTHORIZATION_REQUEST_PASS_STATUS,
        "authorization_request_id_recomputed_match": authorization_request_packet.get("authorization_request_id") == recompute_authorization_request_id(authorization_request_packet),
        "authorization_request_ready_for_operator_review": authorization_request_packet.get("ready_for_operator_review") is True,
        "authorization_request_still_blocks_live_click_now": authorization_request_packet.get("live_click_allowed_now") is False
        and authorization_request_packet.get("live_click_allowed") is False
        and authorization_request_packet.get("live_click_performed") is False,
        "approval_and_outbox_not_created": authorization_request_packet.get("approval_ledger_entry_created") is False
        and authorization_request_packet.get("executable_outbox_entry_created") is False,
        "registry_and_public_url_not_written": authorization_request_packet.get("publication_registry_record_appended") is False
        and authorization_request_packet.get("public_url_capture_performed") is False,
        "payload_hash_shape_valid": len(payload_hash) == 64 and all(char in "0123456789abcdef" for char in payload_hash),
        "packet_ids_present": all(
            authorization_request_packet.get(key)
            for key in ("prelive_packet_id", "go_gate_packet_id", "authorization_packet_id", "final_rehearsal_packet_id")
        ),
        "future_prerequisites_present": isinstance(prerequisites, list)
        and "fresh_contentops_profile_guard_passes" in prerequisites
        and "post_click_public_url_capture_required_before_registry_append" in prerequisites,
        "operator_stop_conditions_present": isinstance(stop_conditions, list) and len(stop_conditions) >= 5,
        "registry_identity_present": isinstance(registry, Mapping),
        "registry_append_blocked_now": isinstance(registry, Mapping) and registry.get("registry_append_allowed_now") is False,
        "post_click_capture_plan_present": isinstance(capture, Mapping),
        "post_click_capture_plan_non_executable_now": isinstance(capture, Mapping)
        and capture.get("registry_append_allowed_now") is False
        and capture.get("public_url_fetch_allowed") is False,
        "scope_decision_valid": scope_decision in VALID_DECISIONS,
    }
    for flag, value in FALSE_SAFETY_FLAGS.items():
        checks[f"safety_flag_{flag}_false"] = authorization_request_packet.get(flag) is False and value is False
    blockers = [name for name, ok in checks.items() if ok is not True]
    passed = not blockers
    status = _status_for_decision(scope_decision) if passed else BLOCKED_STATUS
    future_eligible = passed and scope_decision == "approve_future_scope"
    packet = {
        "task_label": TASK_LABEL,
        "packet_kind": PACKET_KIND,
        "scope_decision_status": status,
        "scope_decision": scope_decision,
        "blocked_reasons": blockers,
        "authorization_request_id": authorization_request_packet.get("authorization_request_id"),
        "prelive_packet_id": authorization_request_packet.get("prelive_packet_id"),
        "go_gate_packet_id": authorization_request_packet.get("go_gate_packet_id"),
        "authorization_packet_id": authorization_request_packet.get("authorization_packet_id"),
        "final_rehearsal_packet_id": authorization_request_packet.get("final_rehearsal_packet_id"),
        "payload_hash": payload_hash or None,
        "checks": checks,
        "future_exact_live_task_eligible_for_consideration": future_eligible,
        "future_exact_live_task_required": True,
        "explicit_future_live_authorization_still_required": True,
        "fresh_profile_guard_required_in_future_task": True,
        "operator_visible_account_destination_recheck_required": True,
        "post_click_public_url_capture_required_before_registry_append": True,
        "approval_decision_record_created": passed,
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
    packet["scope_decision_id"] = "x_scope_decision_" + _sha(
        {
            "kind": PACKET_KIND,
            "request": packet["authorization_request_id"],
            "payload_hash": payload_hash,
            "decision": scope_decision,
            "status": status,
            "passed": passed,
        }
    )[:16]
    return packet


def _approved_request() -> dict[str, Any]:
    expected_profile = r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
    cmd = rf'msedge.exe --remote-debugging-port=9223 --user-data-dir="{expected_profile}"'
    payload = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
    prelive = build_prelive_post_packet(payload_text=payload, cdp_port=9223, command_line=cmd)
    gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=EXPECTED_GO_PHRASE)
    auth = build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist())
    rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
    return build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)


def build_fixture_evidence_bundle() -> dict[str, Any]:
    request = _approved_request()
    capture = request["post_click_capture_plan"]
    cases = {
        "denied_no_live_scope": build_scope_decision_packet(authorization_request_packet=request, scope_decision="deny"),
        "deferred_needs_operator_review": build_scope_decision_packet(authorization_request_packet=request, scope_decision="defer"),
        "approved_for_future_exact_live_task": build_scope_decision_packet(authorization_request_packet=request, scope_decision="approve_future_scope"),
        "invalid_scope_decision_blocked": build_scope_decision_packet(authorization_request_packet=request, scope_decision="approve_now_click"),
        "authorization_request_id_mismatch_blocked": build_scope_decision_packet(authorization_request_packet={**request, "authorization_request_id": "x_exact_live_request_mismatch"}, scope_decision="approve_future_scope"),
        "authorization_request_not_ready_blocked": build_scope_decision_packet(authorization_request_packet={**request, "ready_for_operator_review": False}, scope_decision="approve_future_scope"),
        "capture_plan_executable_now_blocked": build_scope_decision_packet(authorization_request_packet={**request, "post_click_capture_plan": {**capture, "public_url_fetch_allowed": True}}, scope_decision="approve_future_scope"),
    }
    return {
        "task_label": TASK_LABEL,
        "packet_kind": "x_cdp_exact_separate_live_click_scope_decision_evidence_bundle_v0",
        "case_count": len(cases),
        "cases": cases,
        "approved_future_case_eligible_for_consideration": cases["approved_for_future_exact_live_task"]["future_exact_live_task_eligible_for_consideration"] is True,
        "all_cases_blocked_before_click": all(case["blocked_before_live_click"] is True for case in cases.values()),
        "live_action_performed": False,
        "registry_append_performed": False,
        "public_url_capture_performed": False,
        "raw_go_phrase_stored_anywhere": False,
    }


def write_fixture_evidence(path: Path = DEFAULT_EVIDENCE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_fixture_evidence_bundle(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run exact X CDP live-click scope decision. No browser probe or click.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fixture-bundle", action="store_true")
    parser.add_argument("--write-evidence", type=Path, default=None)
    parser.add_argument("--scope-decision", choices=("deny", "defer", "approve_future_scope"), default="defer")
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
    request = build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)
    result = build_scope_decision_packet(authorization_request_packet=request, scope_decision=args.scope_decision)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["scope_decision_status"] != BLOCKED_STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
