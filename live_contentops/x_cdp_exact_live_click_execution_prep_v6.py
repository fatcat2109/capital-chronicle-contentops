"""X CDP exact live-click execution prep dry run.

Bridges an approved future-scope decision into the final authorization task
checklist. This module remains non-executable: no browser probe, session read,
click, registry append, public URL fetch, dispatch, or publish.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.x_cdp_exact_separate_live_click_authorization_request_v6 import build_exact_live_click_authorization_request
from live_contentops.x_cdp_exact_separate_live_click_scope_decision_v6 import (
    APPROVED_FUTURE_STATUS,
    PACKET_KIND as SCOPE_DECISION_PACKET_KIND,
    build_scope_decision_packet,
)
from live_contentops.x_cdp_final_pre_click_rehearsal_dry_run_v6 import build_final_pre_click_rehearsal_packet
from live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 import EXPECTED_GO_PHRASE, build_go_phrase_gate_packet
from live_contentops.x_cdp_separate_live_click_authorization_packet_dry_run_v6 import (
    build_live_click_authorization_packet,
    default_kill_switch_snapshot,
    default_rollback_checklist,
)
from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import FALSE_SAFETY_FLAGS, build_prelive_post_packet

TASK_LABEL = "TASK_CONTENTOPS_V6_X_CDP_EXACT_LIVE_CLICK_EXECUTION_PREP_V0"
PACKET_KIND = "x_cdp_exact_live_click_execution_prep_v0"
READY_STATUS = "READY_FOR_EXACT_LIVE_EXECUTION_AUTHORIZATION_TASK"
BLOCKED_STATUS = "BLOCKED_EXACT_LIVE_EXECUTION_PREP"
DEFAULT_EVIDENCE_PATH = Path(
    "docs/automation/X_SUPERVISED_CDP_EXACT_LIVE_CLICK_EXECUTION_PREP/"
    "task_contentops_v6_x_cdp_exact_live_click_execution_prep_evidence.json"
)


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def recompute_scope_decision_id(packet: Mapping[str, Any]) -> str:
    passed = not packet.get("blocked_reasons") and packet.get("approval_decision_record_created") is True
    seed = {
        "kind": SCOPE_DECISION_PACKET_KIND,
        "request": packet.get("authorization_request_id"),
        "payload_hash": packet.get("payload_hash") or "",
        "decision": packet.get("scope_decision"),
        "status": packet.get("scope_decision_status"),
        "passed": passed,
    }
    return "x_scope_decision_" + _sha(seed)[:16]


def build_execution_prep_packet(*, scope_decision_packet: Mapping[str, Any]) -> dict[str, Any]:
    payload_hash = str(scope_decision_packet.get("payload_hash") or "")
    checks = {
        "scope_decision_kind_match": scope_decision_packet.get("packet_kind") == SCOPE_DECISION_PACKET_KIND,
        "scope_decision_id_recomputed_match": scope_decision_packet.get("scope_decision_id") == recompute_scope_decision_id(scope_decision_packet),
        "scope_decision_status_approved_for_future": scope_decision_packet.get("scope_decision_status") == APPROVED_FUTURE_STATUS,
        "future_exact_live_task_eligible": scope_decision_packet.get("future_exact_live_task_eligible_for_consideration") is True,
        "payload_hash_shape_valid": len(payload_hash) == 64 and all(char in "0123456789abcdef" for char in payload_hash),
        "packet_ids_present": all(
            scope_decision_packet.get(key)
            for key in ("prelive_packet_id", "go_gate_packet_id", "authorization_packet_id", "authorization_request_id", "final_rehearsal_packet_id")
        ),
        "fresh_profile_guard_required": scope_decision_packet.get("fresh_profile_guard_required_in_future_task") is True,
        "account_destination_recheck_required": scope_decision_packet.get("operator_visible_account_destination_recheck_required") is True,
        "post_click_public_url_capture_required": scope_decision_packet.get("post_click_public_url_capture_required_before_registry_append") is True,
        "still_blocks_live_click_now": scope_decision_packet.get("live_click_allowed_now") is False
        and scope_decision_packet.get("live_click_allowed") is False
        and scope_decision_packet.get("live_click_performed") is False,
        "registry_and_public_url_not_written": scope_decision_packet.get("publication_registry_record_appended") is False
        and scope_decision_packet.get("public_url_capture_performed") is False,
    }
    for flag, value in FALSE_SAFETY_FLAGS.items():
        checks[f"safety_flag_{flag}_false"] = scope_decision_packet.get(flag) is False and value is False
    blockers = [name for name, ok in checks.items() if ok is not True]
    ready = not blockers
    packet = {
        "task_label": TASK_LABEL,
        "packet_kind": PACKET_KIND,
        "execution_prep_status": READY_STATUS if ready else BLOCKED_STATUS,
        "blocked_reasons": blockers,
        "scope_decision_id": scope_decision_packet.get("scope_decision_id"),
        "authorization_request_id": scope_decision_packet.get("authorization_request_id"),
        "prelive_packet_id": scope_decision_packet.get("prelive_packet_id"),
        "go_gate_packet_id": scope_decision_packet.get("go_gate_packet_id"),
        "authorization_packet_id": scope_decision_packet.get("authorization_packet_id"),
        "final_rehearsal_packet_id": scope_decision_packet.get("final_rehearsal_packet_id"),
        "payload_hash": payload_hash or None,
        "checks": checks,
        "ready_for_exact_live_execution_authorization_task": ready,
        "exact_live_authorization_task_required": True,
        "fresh_profile_guard_required_before_click": True,
        "operator_visible_account_destination_recheck_required_before_click": True,
        "kill_switch_recheck_required_before_click": True,
        "post_click_public_url_capture_required_before_registry_append": True,
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
    packet["execution_prep_id"] = "x_execution_prep_" + _sha(
        {
            "kind": PACKET_KIND,
            "scope_decision_id": packet["scope_decision_id"],
            "payload_hash": payload_hash,
            "ready": ready,
        }
    )[:16]
    return packet


def _scope_decision(scope_decision: str = "approve_future_scope") -> dict[str, Any]:
    expected_profile = r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
    cmd = rf'msedge.exe --remote-debugging-port=9223 --user-data-dir="{expected_profile}"'
    payload = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
    prelive = build_prelive_post_packet(payload_text=payload, cdp_port=9223, command_line=cmd)
    gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=EXPECTED_GO_PHRASE)
    auth = build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist())
    rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
    request = build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)
    return build_scope_decision_packet(authorization_request_packet=request, scope_decision=scope_decision)


def build_fixture_evidence_bundle() -> dict[str, Any]:
    approved = _scope_decision("approve_future_scope")
    cases = {
        "approved_future_scope_ready_for_authorization_task": build_execution_prep_packet(scope_decision_packet=approved),
        "denied_scope_blocked": build_execution_prep_packet(scope_decision_packet=_scope_decision("deny")),
        "deferred_scope_blocked": build_execution_prep_packet(scope_decision_packet=_scope_decision("defer")),
        "scope_decision_id_mismatch_blocked": build_execution_prep_packet(scope_decision_packet={**approved, "scope_decision_id": "x_scope_decision_mismatch"}),
        "live_click_flag_true_blocked": build_execution_prep_packet(scope_decision_packet={**approved, "live_click_performed": True}),
        "registry_append_true_blocked": build_execution_prep_packet(scope_decision_packet={**approved, "publication_registry_record_appended": True}),
    }
    return {
        "task_label": TASK_LABEL,
        "packet_kind": "x_cdp_exact_live_click_execution_prep_evidence_bundle_v0",
        "case_count": len(cases),
        "cases": cases,
        "approved_case_ready_for_authorization_task": cases["approved_future_scope_ready_for_authorization_task"]["ready_for_exact_live_execution_authorization_task"] is True,
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
    parser = argparse.ArgumentParser(description="Dry-run exact X CDP live-click execution prep. No browser probe or click.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fixture-bundle", action="store_true")
    parser.add_argument("--write-evidence", type=Path, default=None)
    parser.add_argument("--payload-text", default="")
    parser.add_argument("--operator-go-phrase", default="")
    parser.add_argument("--scope-decision", choices=("deny", "defer", "approve_future_scope"), default="approve_future_scope")
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
    decision = build_scope_decision_packet(authorization_request_packet=request, scope_decision=args.scope_decision)
    result = build_execution_prep_packet(scope_decision_packet=decision)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ready_for_exact_live_execution_authorization_task"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
