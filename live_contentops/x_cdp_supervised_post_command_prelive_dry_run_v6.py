"""Supervised X CDP pre-live post command dry run.

Builds local operator-review evidence only. It never launches a browser, probes CDP,
reads session stores, clicks, publishes, fetches public URLs, or appends live
publication registry rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.platform_publication_identity_registry_v6 import is_x_status_url
from live_contentops.x_cdp_profile_guard_v6 import DEFAULT_EXPECTED_PROFILE_ROOT, build_guard_report

TASK_LABEL = "TASK_CONTENTOPS_V6_X_CDP_SUPERVISED_POST_COMMAND_PRELIVE_DRY_RUN_V0"
PACKET_KIND = "x_cdp_supervised_post_command_prelive_dry_run_v0"
X_TEXT_LIMIT = 280
HASH_ALGORITHM = "sha256_text_v6"
DEFAULT_ACCOUNT_HANDLE = "Capitalnicle"
DEFAULT_DESTINATION_BINDING_REF = "destination_x_capital_chronicle_main"
DEFAULT_ACCOUNT_BINDING_REF = "account_x_capital_chronicle_main"
FORBIDDEN_SECRET_PATTERNS = (
    r"https://discord(?:app)?\.com/api/webhooks/",
    r"sk-[A-Za-z0-9]",
    r"xox[baprs]-",
    r"ghp_[A-Za-z0-9]",
    r"bearer\s+[A-Za-z0-9._-]{12,}",
    r"cookie\s*[:=]",
    r"localstorage\s*[:=]",
    r"sessionstorage\s*[:=]",
    r"browser session data\s*[:=]",
)
FORBIDDEN_ADVICE = ("financial advice", "trading signal", "signal service", "price target", "target price", "buy", "sell", "hold")
FALSE_SAFETY_FLAGS = {
    "browser_launch_performed": False,
    "browser_or_cdp_probe_performed": False,
    "cookie_read_performed": False,
    "local_storage_read_performed": False,
    "session_storage_read_performed": False,
    "token_or_header_read_performed": False,
    "dom_read_performed": False,
    "raw_secret_output": False,
    "network_call_made": False,
    "public_url_fetch_made": False,
    "x_api_used": False,
    "paid_api_used": False,
    "provider_call_made": False,
    "env_value_read_made": False,
    "credential_read_made": False,
    "approval_ledger_entry_created": False,
    "publication_registry_record_appended": False,
    "live_click_performed": False,
    "live_publish_performed": False,
    "scheduler_enabled": False,
    "retry_enabled": False,
}


class XPreliveDryRunError(ValueError):
    pass


def stable_payload_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _assert_safe_payload(text: str) -> None:
    stripped = (text or "").strip()
    if not stripped:
        raise XPreliveDryRunError("payload_text_required")
    if len(stripped) > X_TEXT_LIMIT:
        raise XPreliveDryRunError("payload_text_over_x_limit")
    lower = stripped.lower()
    for pattern in FORBIDDEN_SECRET_PATTERNS:
        if re.search(pattern, stripped, flags=re.I):
            raise XPreliveDryRunError("forbidden_secret_or_session_material")
    for phrase in FORBIDDEN_ADVICE:
        if re.search(r"\b" + re.escape(phrase) + r"\b", lower):
            raise XPreliveDryRunError("forbidden_financial_advice:" + phrase)


def _blocked_packet(reason: str, payload_text: str, guard_report: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload_hash = stable_payload_hash(payload_text.strip()) if payload_text and payload_text.strip() else None
    safe_payload_text = "[redacted_forbidden_payload]" if reason == "forbidden_secret_or_session_material" else payload_text
    return {
        "task_label": TASK_LABEL,
        "packet_kind": PACKET_KIND,
        "prelive_status": "BLOCKED_PRELIVE_X_POST",
        "blocked_reason": reason,
        "payload_text": safe_payload_text,
        "payload_hash": payload_hash,
        "hash_algorithm": HASH_ALGORITHM,
        "ready_for_operator_review": False,
        "blocked_before_live_click": True,
        "live_click_allowed": False,
        "future_live_go_phrase_required": True,
        "profile_guard_report": dict(guard_report or {}),
        **FALSE_SAFETY_FLAGS,
    }


def build_prelive_post_packet(
    *,
    payload_text: str,
    cdp_port: int = 9222,
    command_line: str | None = None,
    expected_profile_root: str | Path = DEFAULT_EXPECTED_PROFILE_ROOT,
    account_handle: str = DEFAULT_ACCOUNT_HANDLE,
    account_binding_ref: str = DEFAULT_ACCOUNT_BINDING_REF,
    destination_binding_ref: str = DEFAULT_DESTINATION_BINDING_REF,
    source_approval_id: str | None = None,
    source_outbox_entry_id: str | None = None,
    expected_parent_public_url: str | None = None,
) -> dict[str, Any]:
    try:
        _assert_safe_payload(payload_text)
    except XPreliveDryRunError as exc:
        return _blocked_packet(str(exc), payload_text)

    guard = build_guard_report(cdp_port=cdp_port, command_line=command_line, expected_profile_root=expected_profile_root)
    if guard["profile_guard_status"] != "contentops_profile_ok":
        return _blocked_packet("profile_guard_not_ready:" + str(guard["profile_guard_status"]), payload_text, guard)
    if expected_parent_public_url and not is_x_status_url(expected_parent_public_url):
        return _blocked_packet("expected_parent_public_url_must_be_x_status_url", payload_text, guard)

    text = payload_text.strip()
    payload_hash = stable_payload_hash(text)
    registry_expectation = {
        "platform": "x",
        "account_handle_expected": account_handle,
        "account_binding_ref": account_binding_ref,
        "destination_binding_ref": destination_binding_ref,
        "payload_hash": payload_hash,
        "parent_public_url_expected": expected_parent_public_url,
        "capture_method_expected_after_future_click": "x_cdp_post_detail_after_click",
        "public_url_capture_required_after_future_click": True,
        "registry_append_allowed_now": False,
    }
    packet = {
        "task_label": TASK_LABEL,
        "packet_kind": PACKET_KIND,
        "prelive_status": "PRELIVE_X_POST_READY_FOR_OPERATOR_REVIEW",
        "ready_for_operator_review": True,
        "dry_run_only": True,
        "platform": "x",
        "payload_text": text,
        "payload_character_count": len(text),
        "payload_limit": X_TEXT_LIMIT,
        "payload_hash": payload_hash,
        "hash_algorithm": HASH_ALGORITHM,
        "source_approval_id": source_approval_id,
        "source_outbox_entry_id": source_outbox_entry_id,
        "profile_guard_report": guard,
        "registry_identity_expectation": registry_expectation,
        "operator_review_required": True,
        "future_live_go_phrase_required": True,
        "blocked_before_live_click": False,
        "live_click_allowed": False,
        "live_click_allowed_after_future_go_phrase_only": guard["live_click_allowed"] is True,
        **FALSE_SAFETY_FLAGS,
    }
    packet_id_seed = json.dumps({"kind": PACKET_KIND, "payload_hash": payload_hash, "guard": guard["profile_guard_status"]}, sort_keys=True)
    packet["prelive_packet_id"] = "x_prelive_" + hashlib.sha256(packet_id_seed.encode("utf-8")).hexdigest()[:16]
    return packet


def build_fixture_evidence_bundle() -> dict[str, Any]:
    expected = DEFAULT_EXPECTED_PROFILE_ROOT
    approved_cmd = rf'msedge.exe --remote-debugging-port=9223 --user-data-dir="{expected}"'
    payload = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
    cases = {
        "approved_contentops_profile_valid_payload": build_prelive_post_packet(payload_text=payload, cdp_port=9223, command_line=approved_cmd),
        "antigravity_profile_blocked": build_prelive_post_packet(payload_text=payload, command_line=r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\.gemini\antigravity-browser-profile"),
        "builtin_profile_blocked": build_prelive_post_packet(payload_text=payload, command_line=r"msedge.exe --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\AppData\Local\Microsoft\Edge\User Data\Default"),
        "unknown_profile_blocked": build_prelive_post_packet(payload_text=payload, command_line=r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\tmp\other-profile"),
        "missing_cdp_metadata_blocked": build_prelive_post_packet(payload_text=payload, command_line=None),
        "overlength_payload_blocked": build_prelive_post_packet(payload_text="x" * (X_TEXT_LIMIT + 1), cdp_port=9223, command_line=approved_cmd),
        "forbidden_material_blocked": build_prelive_post_packet(payload_text="bearer abcdefghijklmnop", cdp_port=9223, command_line=approved_cmd),
    }
    return {
        "task_label": TASK_LABEL,
        "packet_kind": "x_cdp_supervised_post_command_prelive_dry_run_evidence_bundle_v0",
        "case_count": len(cases),
        "cases": cases,
        "approved_case_ready": cases["approved_contentops_profile_valid_payload"]["ready_for_operator_review"] is True,
        "all_blocked_cases_blocked_before_click": all(
            case["blocked_before_live_click"] is True for name, case in cases.items() if name != "approved_contentops_profile_valid_payload"
        ),
        "safety_boundary": FALSE_SAFETY_FLAGS,
        "live_action_performed": False,
    }


def write_fixture_evidence(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_fixture_evidence_bundle(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run supervised X CDP pre-live post command. No browser launch/probe/click.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--payload-text", default="")
    parser.add_argument("--cdp-port", type=int, default=9222)
    parser.add_argument("--expected-profile-root", type=Path, default=DEFAULT_EXPECTED_PROFILE_ROOT)
    parser.add_argument("--command-line", default=None)
    parser.add_argument("--fixture-bundle", action="store_true")
    args = parser.parse_args(argv)
    if not args.dry_run:
        print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_allowed": False}, sort_keys=True))
        return 2
    result = build_fixture_evidence_bundle() if args.fixture_bundle else build_prelive_post_packet(
        payload_text=args.payload_text,
        cdp_port=args.cdp_port,
        command_line=args.command_line,
        expected_profile_root=args.expected_profile_root,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ready_for_operator_review") is True or args.fixture_bundle else 2


if __name__ == "__main__":
    raise SystemExit(main())
