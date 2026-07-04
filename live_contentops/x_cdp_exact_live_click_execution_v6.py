"""X CDP exact live-click execution outcome packet.

Records an operator-supervised one-click execution outcome from exact
authorization metadata. Repo code does not drive the browser, probe CDP, read
session state, call X APIs, fetch public URLs, append registries, schedule,
retry, comment, DM, react, or perform multi-post publishing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from live_contentops.x_cdp_exact_live_click_authorization_v6 import (
    AUTHORIZED_STATUS,
    PACKET_KIND as AUTHORIZATION_PACKET_KIND,
    build_exact_live_click_authorization,
)
from live_contentops.x_cdp_exact_live_click_execution_prep_v6 import build_execution_prep_packet
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

TASK_LABEL = "TASK_CONTENTOPS_V6_X_CDP_EXACT_LIVE_CLICK_EXECUTION_V0"
PACKET_KIND = "x_cdp_exact_live_click_execution_v0"
EXECUTED_STATUS = "EXECUTED_WITH_CAPTURED_PUBLIC_URL"
BLOCKED_STATUS = "BLOCKED_EXACT_LIVE_CLICK_EXECUTION"
DEFAULT_EVIDENCE_PATH = Path(
    "docs/automation/X_SUPERVISED_CDP_EXACT_LIVE_CLICK_EXECUTION/"
    "task_contentops_v6_x_cdp_exact_live_click_execution_evidence.json"
)


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def is_public_x_status_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or parsed.netloc.lower() not in {"x.com", "twitter.com", "www.x.com", "www.twitter.com"}:
        return False
    parts = [part for part in parsed.path.split("/") if part]
    return len(parts) >= 3 and parts[1] == "status" and parts[2].isdigit()


def recompute_authorization_id(packet: Mapping[str, Any]) -> str:
    authorized = packet.get("exact_live_click_authorized_for_one_operator_supervised_click") is True
    payload_hash = str(packet.get("payload_hash") or "")
    return "x_exact_live_auth_" + _sha(
        {
            "kind": AUTHORIZATION_PACKET_KIND,
            "execution_prep_id": packet.get("execution_prep_id"),
            "payload_hash": payload_hash,
            "authorized": authorized,
        }
    )[:16]


def build_exact_live_click_execution(
    *,
    authorization_packet: Mapping[str, Any],
    operator_confirmed_click_performed: bool,
    captured_public_x_url: str = "",
    operator_confirmed_payload_hash: str = "",
    operator_confirmed_account_destination: str = "",
    operator_confirmed_kill_switch_available_before_click: bool = False,
) -> dict[str, Any]:
    payload_hash = str(authorization_packet.get("payload_hash") or "")
    url = captured_public_x_url.strip()
    checks = {
        "authorization_kind_match": authorization_packet.get("packet_kind") == AUTHORIZATION_PACKET_KIND,
        "authorization_status_authorized": authorization_packet.get("authorization_status") == AUTHORIZED_STATUS,
        "authorization_id_recomputed_match": authorization_packet.get("exact_live_authorization_id") == recompute_authorization_id(authorization_packet),
        "exact_one_click_authorized": authorization_packet.get("exact_live_click_authorized_for_one_operator_supervised_click") is True,
        "payload_hash_shape_valid": len(payload_hash) == 64 and all(char in "0123456789abcdef" for char in payload_hash),
        "operator_payload_hash_confirmed": operator_confirmed_payload_hash == payload_hash,
        "operator_account_destination_confirmed": bool(operator_confirmed_account_destination.strip()),
        "operator_kill_switch_confirmed_before_click": operator_confirmed_kill_switch_available_before_click is True,
        "operator_click_confirmed": operator_confirmed_click_performed is True,
        "captured_public_x_url_valid": is_public_x_status_url(url),
        "prior_registry_not_appended": authorization_packet.get("publication_registry_record_appended") is False,
        "prior_public_url_not_captured_by_repo": authorization_packet.get("public_url_capture_performed") is False,
        "prior_live_click_not_performed_by_repo": authorization_packet.get("live_click_performed") is False,
        "required_execution_checks_present": all(
            item in authorization_packet.get("required_live_execution_checks", ())
            for item in (
                "operator_clicks_only_the_single_intended_x_post_button",
                "capture_public_x_status_url_after_click_before_registry_append",
                "append_publication_registry_only_after_captured_public_url_matches_payload",
            )
        ),
    }
    for flag, value in FALSE_SAFETY_FLAGS.items():
        checks[f"safety_flag_{flag}_false_before_execution"] = authorization_packet.get(flag) is False and value is False
    blockers = [name for name, ok in checks.items() if ok is not True]
    executed = not blockers
    packet = {
        "task_label": TASK_LABEL,
        "packet_kind": PACKET_KIND,
        "execution_status": EXECUTED_STATUS if executed else BLOCKED_STATUS,
        "blocked_reasons": blockers,
        "exact_live_authorization_id": authorization_packet.get("exact_live_authorization_id"),
        "execution_prep_id": authorization_packet.get("execution_prep_id"),
        "scope_decision_id": authorization_packet.get("scope_decision_id"),
        "authorization_request_id": authorization_packet.get("authorization_request_id"),
        "payload_hash": payload_hash or None,
        "operator_confirmed_payload_hash": operator_confirmed_payload_hash or None,
        "operator_confirmed_account_destination_hash": _sha(operator_confirmed_account_destination.strip()) if operator_confirmed_account_destination.strip() else None,
        "captured_public_x_url": url if executed else None,
        "checks": checks,
        "live_click_performed": executed,
        "public_url_capture_performed": executed,
        "registry_append_ready": executed,
        "publication_registry_record_appended": False,
        "registry_append_requires_captured_public_url": True,
        "registry_append_task_required": executed,
        "raw_go_phrase_stored": False,
        **{
            key: value
            for key, value in FALSE_SAFETY_FLAGS.items()
            if key not in {"live_click_performed", "publication_registry_record_appended"}
        },
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
    }
    packet["exact_live_execution_id"] = "x_exact_live_exec_" + _sha(
        {
            "kind": PACKET_KIND,
            "authorization_id": packet["exact_live_authorization_id"],
            "payload_hash": payload_hash,
            "captured_url": url if executed else "",
            "executed": executed,
        }
    )[:16]
    return packet


def _authorization(scope_decision: str = "approve_future_scope") -> dict[str, Any]:
    expected_profile = r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
    cmd = rf'msedge.exe --remote-debugging-port=9223 --user-data-dir="{expected_profile}"'
    payload = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
    prelive = build_prelive_post_packet(payload_text=payload, cdp_port=9223, command_line=cmd)
    gate = build_go_phrase_gate_packet(prelive_packet=prelive, operator_go_phrase=EXPECTED_GO_PHRASE)
    auth = build_live_click_authorization_packet(prelive_packet=prelive, go_gate_packet=gate, kill_switch_snapshot=default_kill_switch_snapshot(), rollback_checklist=default_rollback_checklist())
    rehearsal = build_final_pre_click_rehearsal_packet(prelive_packet=prelive, go_gate_packet=gate, authorization_packet=auth)
    request = build_exact_live_click_authorization_request(final_rehearsal_packet=rehearsal)
    decision = build_scope_decision_packet(authorization_request_packet=request, scope_decision=scope_decision)
    prep = build_execution_prep_packet(scope_decision_packet=decision)
    return build_exact_live_click_authorization(execution_prep_packet=prep)


def build_fixture_evidence_bundle() -> dict[str, Any]:
    ready = _authorization("approve_future_scope")
    payload_hash = str(ready["payload_hash"])
    cases = {
        "operator_confirmed_click_with_captured_public_url": build_exact_live_click_execution(
            authorization_packet=ready,
            operator_confirmed_click_performed=True,
            captured_public_x_url="https://x.com/capitalchronicle/status/1234567890123456789",
            operator_confirmed_payload_hash=payload_hash,
            operator_confirmed_account_destination="@capitalchronicle on X",
            operator_confirmed_kill_switch_available_before_click=True,
        ),
        "missing_click_confirmation_blocked": build_exact_live_click_execution(
            authorization_packet=ready,
            operator_confirmed_click_performed=False,
            captured_public_x_url="https://x.com/capitalchronicle/status/1234567890123456789",
            operator_confirmed_payload_hash=payload_hash,
            operator_confirmed_account_destination="@capitalchronicle on X",
            operator_confirmed_kill_switch_available_before_click=True,
        ),
        "missing_public_url_blocked": build_exact_live_click_execution(
            authorization_packet=ready,
            operator_confirmed_click_performed=True,
            captured_public_x_url="",
            operator_confirmed_payload_hash=payload_hash,
            operator_confirmed_account_destination="@capitalchronicle on X",
            operator_confirmed_kill_switch_available_before_click=True,
        ),
        "payload_hash_mismatch_blocked": build_exact_live_click_execution(
            authorization_packet=ready,
            operator_confirmed_click_performed=True,
            captured_public_x_url="https://x.com/capitalchronicle/status/1234567890123456789",
            operator_confirmed_payload_hash="0" * 64,
            operator_confirmed_account_destination="@capitalchronicle on X",
            operator_confirmed_kill_switch_available_before_click=True,
        ),
        "authorization_not_ready_blocked": build_exact_live_click_execution(
            authorization_packet=_authorization("deny"),
            operator_confirmed_click_performed=True,
            captured_public_x_url="https://x.com/capitalchronicle/status/1234567890123456789",
            operator_confirmed_payload_hash=payload_hash,
            operator_confirmed_account_destination="@capitalchronicle on X",
            operator_confirmed_kill_switch_available_before_click=True,
        ),
        "prior_registry_append_blocked": build_exact_live_click_execution(
            authorization_packet={**ready, "publication_registry_record_appended": True},
            operator_confirmed_click_performed=True,
            captured_public_x_url="https://x.com/capitalchronicle/status/1234567890123456789",
            operator_confirmed_payload_hash=payload_hash,
            operator_confirmed_account_destination="@capitalchronicle on X",
            operator_confirmed_kill_switch_available_before_click=True,
        ),
    }
    return {
        "task_label": TASK_LABEL,
        "packet_kind": "x_cdp_exact_live_click_execution_evidence_bundle_v0",
        "case_count": len(cases),
        "cases": cases,
        "ready_case_executed_with_captured_public_url": cases["operator_confirmed_click_with_captured_public_url"]["execution_status"] == EXECUTED_STATUS,
        "registry_append_performed": False,
        "raw_go_phrase_stored_anywhere": False,
        "browser_or_cdp_probe_performed": False,
    }


def write_fixture_evidence(path: Path = DEFAULT_EVIDENCE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_fixture_evidence_bundle(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record exact X CDP live-click execution outcome. Does not drive browser or read session state.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fixture-bundle", action="store_true")
    parser.add_argument("--write-evidence", type=Path, default=None)
    parser.add_argument("--payload-text", default="")
    parser.add_argument("--operator-go-phrase", default="")
    parser.add_argument("--scope-decision", choices=("deny", "defer", "approve_future_scope"), default="approve_future_scope")
    parser.add_argument("--cdp-port", type=int, default=9222)
    parser.add_argument("--expected-profile-root", type=Path, default=Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"))
    parser.add_argument("--command-line", default=None)
    parser.add_argument("--operator-confirmed-click-performed", action="store_true")
    parser.add_argument("--captured-public-x-url", default="")
    parser.add_argument("--operator-confirmed-payload-hash", default="")
    parser.add_argument("--operator-confirmed-account-destination", default="")
    parser.add_argument("--operator-confirmed-kill-switch-available-before-click", action="store_true")
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
    authorization = build_exact_live_click_authorization(execution_prep_packet=prep)
    result = build_exact_live_click_execution(
        authorization_packet=authorization,
        operator_confirmed_click_performed=args.operator_confirmed_click_performed,
        captured_public_x_url=args.captured_public_x_url,
        operator_confirmed_payload_hash=args.operator_confirmed_payload_hash,
        operator_confirmed_account_destination=args.operator_confirmed_account_destination,
        operator_confirmed_kill_switch_available_before_click=args.operator_confirmed_kill_switch_available_before_click,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["execution_status"] == EXECUTED_STATUS else 2


if __name__ == "__main__":
    raise SystemExit(main())
