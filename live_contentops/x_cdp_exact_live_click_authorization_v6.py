"""X CDP exact live-click authorization packet.

Converts a ready execution-prep packet into exact, one-payload authorization
metadata. This still does not launch/probe browsers, read session state, click,
publish, fetch public URLs, append registries, schedule, retry, or call APIs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.x_cdp_exact_live_click_execution_prep_v6 import (
    PACKET_KIND as EXECUTION_PREP_PACKET_KIND,
    READY_STATUS as EXECUTION_PREP_READY_STATUS,
    build_execution_prep_packet,
)
from live_contentops.x_cdp_exact_separate_live_click_authorization_request_v6 import build_exact_live_click_authorization_request
from live_contentops.x_cdp_exact_separate_live_click_scope_decision_v6 import build_scope_decision_packet
from live_contentops.x_cdp_final_pre_click_rehearsal_dry_run_v6 import build_final_pre_click_rehearsal_packet
from live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 import EXPECTED_GO_PHRASE, build_go_phrase_gate_packet
from live_contentops.x_cdp_separate_live_click_authorization_packet_dry_run_v6 import (
    build_live_click_authorization_packet,
    default_kill_switch_snapshot,
    default_rollback_checklist,
)
from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import FALSE_SAFETY_FLAGS, build_prelive_post_packet

TASK_LABEL = "TASK_CONTENTOPS_V6_X_CDP_EXACT_LIVE_CLICK_AUTHORIZATION_V0"
PACKET_KIND = "x_cdp_exact_live_click_authorization_v0"
AUTHORIZED_STATUS = "EXACT_LIVE_CLICK_AUTHORIZED_FOR_ONE_OPERATOR_SUPERVISED_CLICK"
BLOCKED_STATUS = "BLOCKED_EXACT_LIVE_CLICK_AUTHORIZATION"
DEFAULT_EVIDENCE_PATH = Path(
    "docs/automation/X_SUPERVISED_CDP_EXACT_LIVE_CLICK_AUTHORIZATION/"
    "task_contentops_v6_x_cdp_exact_live_click_authorization_evidence.json"
)


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def recompute_execution_prep_id(packet: Mapping[str, Any]) -> str:
    ready = packet.get("ready_for_exact_live_execution_authorization_task") is True
    seed = {
        "kind": EXECUTION_PREP_PACKET_KIND,
        "scope_decision_id": packet.get("scope_decision_id"),
        "payload_hash": packet.get("payload_hash") or "",
        "ready": ready,
    }
    return "x_execution_prep_" + _sha(seed)[:16]


def required_live_execution_checks() -> list[str]:
    return [
        "operator_confirms_exact_payload_hash_visible_or_locked",
        "operator_confirms_x_account_handle_and_destination_visible",
        "fresh_contentops_profile_guard_passes_in_same_operator_session",
        "kill_switch_confirmed_available_before_click",
        "operator_clicks_only_the_single_intended_x_post_button",
        "stop_if_compose_ui_button_account_or_payload_is_uncertain",
        "capture_public_x_status_url_after_click_before_registry_append",
        "append_publication_registry_only_after_captured_public_url_matches_payload",
    ]


def build_exact_live_click_authorization(*, execution_prep_packet: Mapping[str, Any]) -> dict[str, Any]:
    payload_hash = str(execution_prep_packet.get("payload_hash") or "")
    checks = {
        "execution_prep_kind_match": execution_prep_packet.get("packet_kind") == EXECUTION_PREP_PACKET_KIND,
        "execution_prep_status_ready": execution_prep_packet.get("execution_prep_status") == EXECUTION_PREP_READY_STATUS,
        "execution_prep_id_recomputed_match": execution_prep_packet.get("execution_prep_id") == recompute_execution_prep_id(execution_prep_packet),
        "ready_for_exact_live_execution_authorization_task": execution_prep_packet.get("ready_for_exact_live_execution_authorization_task") is True,
        "payload_hash_shape_valid": len(payload_hash) == 64 and all(char in "0123456789abcdef" for char in payload_hash),
        "packet_ids_present": all(
            execution_prep_packet.get(key)
            for key in ("scope_decision_id", "authorization_request_id", "prelive_packet_id", "go_gate_packet_id", "authorization_packet_id", "final_rehearsal_packet_id")
        ),
        "fresh_profile_guard_required_before_click": execution_prep_packet.get("fresh_profile_guard_required_before_click") is True,
        "account_destination_recheck_required_before_click": execution_prep_packet.get("operator_visible_account_destination_recheck_required_before_click") is True,
        "kill_switch_recheck_required_before_click": execution_prep_packet.get("kill_switch_recheck_required_before_click") is True,
        "post_click_public_url_capture_required_before_registry_append": execution_prep_packet.get("post_click_public_url_capture_required_before_registry_append") is True,
        "no_prior_live_write_or_registry_append": execution_prep_packet.get("live_click_performed") is False
        and execution_prep_packet.get("live_publish_performed") is False
        and execution_prep_packet.get("publication_registry_record_appended") is False
        and execution_prep_packet.get("public_url_capture_performed") is False,
    }
    for flag, value in FALSE_SAFETY_FLAGS.items():
        checks[f"safety_flag_{flag}_false"] = execution_prep_packet.get(flag) is False and value is False
    blockers = [name for name, ok in checks.items() if ok is not True]
    authorized = not blockers
    packet = {
        "task_label": TASK_LABEL,
        "packet_kind": PACKET_KIND,
        "authorization_status": AUTHORIZED_STATUS if authorized else BLOCKED_STATUS,
        "blocked_reasons": blockers,
        "execution_prep_id": execution_prep_packet.get("execution_prep_id"),
        "scope_decision_id": execution_prep_packet.get("scope_decision_id"),
        "authorization_request_id": execution_prep_packet.get("authorization_request_id"),
        "prelive_packet_id": execution_prep_packet.get("prelive_packet_id"),
        "go_gate_packet_id": execution_prep_packet.get("go_gate_packet_id"),
        "authorization_packet_id": execution_prep_packet.get("authorization_packet_id"),
        "final_rehearsal_packet_id": execution_prep_packet.get("final_rehearsal_packet_id"),
        "payload_hash": payload_hash or None,
        "checks": checks,
        "exact_live_click_authorized_for_one_operator_supervised_click": authorized,
        "authorization_scope": "one_payload_one_account_one_destination_one_x_post_click",
        "required_live_execution_checks": required_live_execution_checks(),
        "live_execution_task_required": True,
        "operator_must_stop_on_any_ui_uncertainty": True,
        "registry_append_requires_captured_public_url": True,
        "raw_go_phrase_stored": False,
        **FALSE_SAFETY_FLAGS,
        "approval_ledger_entry_created": False,
        "executable_outbox_entry_created": False,
        "publication_registry_record_appended": False,
        "public_url_capture_performed": False,
        "live_click_performed": False,
        "live_publish_performed": False,
    }
    packet["exact_live_authorization_id"] = "x_exact_live_auth_" + _sha(
        {"kind": PACKET_KIND, "execution_prep_id": packet["execution_prep_id"], "payload_hash": payload_hash, "authorized": authorized}
    )[:16]
    return packet


def _execution_prep(scope_decision: str = "approve_future_scope") -> dict[str, Any]:
    expected_profile = r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
    cmd = rf'msedge.exe --remote-debugging-port=9223 --user-data-dir="{expected_profile}"'
    payload = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
    prelive = build_prelive_post_packet(payload_text=payload, cdp_port=9223, command_line=cmd)
    gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=EXPECTED_GO_PHRASE)
    auth = build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist())
    rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
    request = build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)
    decision = build_scope_decision_packet(authorization_request_packet=request, scope_decision=scope_decision)
    return build_execution_prep_packet(scope_decision_packet=decision)


def build_fixture_evidence_bundle() -> dict[str, Any]:
    ready = _execution_prep("approve_future_scope")
    cases = {
        "ready_prep_authorized_for_one_supervised_click": build_exact_live_click_authorization(execution_prep_packet=ready),
        "denied_scope_prep_blocked": build_exact_live_click_authorization(execution_prep_packet=_execution_prep("deny")),
        "deferred_scope_prep_blocked": build_exact_live_click_authorization(execution_prep_packet=_execution_prep("defer")),
        "execution_prep_id_mismatch_blocked": build_exact_live_click_authorization(execution_prep_packet={**ready, "execution_prep_id": "x_execution_prep_mismatch"}),
        "prior_live_click_flag_blocked": build_exact_live_click_authorization(execution_prep_packet={**ready, "live_click_performed": True}),
        "registry_append_flag_blocked": build_exact_live_click_authorization(execution_prep_packet={**ready, "publication_registry_record_appended": True}),
    }
    return {
        "task_label": TASK_LABEL,
        "packet_kind": "x_cdp_exact_live_click_authorization_evidence_bundle_v0",
        "case_count": len(cases),
        "cases": cases,
        "ready_case_authorized": cases["ready_prep_authorized_for_one_supervised_click"]["exact_live_click_authorized_for_one_operator_supervised_click"] is True,
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
    parser = argparse.ArgumentParser(description="Build exact X CDP live-click authorization. Does not click or probe.")
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
        print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_performed": False}, sort_keys=True))
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
    prep = build_execution_prep_packet(scope_decision_packet=decision)
    result = build_exact_live_click_authorization(execution_prep_packet=prep)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["exact_live_click_authorized_for_one_operator_supervised_click"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
