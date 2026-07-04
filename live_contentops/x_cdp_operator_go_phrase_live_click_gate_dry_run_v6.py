"""X CDP operator GO-phrase live-click gate dry run.

Validates local pre-live evidence and an exact operator phrase before any future
supervised X click. It never launches/probes browsers, reads browser/session
state, calls a provider, appends registries, clicks, or publishes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.x_cdp_supervised_post_command_prelive_dry_run_v6 import (
    DEFAULT_ACCOUNT_BINDING_REF,
    DEFAULT_ACCOUNT_HANDLE,
    DEFAULT_DESTINATION_BINDING_REF,
    FALSE_SAFETY_FLAGS,
    HASH_ALGORITHM,
    PACKET_KIND as PRELIVE_PACKET_KIND,
    build_prelive_post_packet,
    stable_payload_hash,
)

TASK_LABEL = "TASK_CONTENTOPS_V6_X_CDP_OPERATOR_GO_PHRASE_LIVE_CLICK_GATE_DRY_RUN_V0"
PACKET_KIND = "x_cdp_operator_go_phrase_live_click_gate_dry_run_v0"
EXPECTED_GO_PHRASE = "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY"
GO_PHRASE_HASH_ALGORITHM = "sha256_trimmed_go_phrase_v6"
PASS_STATUS = "GO_PHRASE_GATE_READY_FOR_SEPARATE_LIVE_TASK"
BLOCKED_STATUS = "BLOCKED_GO_PHRASE_GATE_BEFORE_LIVE_CLICK"


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def go_phrase_hash(phrase: str) -> str:
    return hashlib.sha256((phrase or "").strip().encode("utf-8")).hexdigest()


def expected_go_phrase_hash() -> str:
    return go_phrase_hash(EXPECTED_GO_PHRASE)


def recompute_prelive_packet_id(packet: Mapping[str, Any]) -> str | None:
    payload_hash = packet.get("payload_hash")
    guard = packet.get("profile_guard_report")
    if not payload_hash or not isinstance(guard, Mapping):
        return None
    seed = json.dumps({"kind": PRELIVE_PACKET_KIND, "payload_hash": payload_hash, "guard": guard.get("profile_guard_status")}, sort_keys=True)
    return "x_prelive_" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _load_json_arg(raw: str | None, path: str | Path | None) -> dict[str, Any] | None:
    if raw:
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("prelive_packet_json_must_be_object")
        return value
    if path:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("prelive_packet_path_must_contain_object")
        return value
    return None


def build_go_phrase_gate_packet(
    *,
    prelive_packet: Mapping[str, Any],
    operator_go_phrase: str,
    expected_prelive_packet_id: str | None = None,
    expected_payload_hash: str | None = None,
    expected_account_handle: str = DEFAULT_ACCOUNT_HANDLE,
    expected_account_binding_ref: str = DEFAULT_ACCOUNT_BINDING_REF,
    expected_destination_binding_ref: str = DEFAULT_DESTINATION_BINDING_REF,
) -> dict[str, Any]:
    registry = prelive_packet.get("registry_identity_expectation")
    guard = prelive_packet.get("profile_guard_report")
    payload_text = str(prelive_packet.get("payload_text") or "")
    payload_hash = str(prelive_packet.get("payload_hash") or "")
    supplied_phrase_hash = go_phrase_hash(operator_go_phrase)
    expected_phrase_hash = expected_go_phrase_hash()
    recomputed_packet_id = recompute_prelive_packet_id(prelive_packet)
    checks = {
        "prelive_packet_kind_match": prelive_packet.get("packet_kind") == PRELIVE_PACKET_KIND,
        "prelive_status_ready": prelive_packet.get("prelive_status") == "PRELIVE_X_POST_READY_FOR_OPERATOR_REVIEW",
        "ready_for_operator_review": prelive_packet.get("ready_for_operator_review") is True,
        "hash_algorithm_match": prelive_packet.get("hash_algorithm") == HASH_ALGORITHM,
        "payload_hash_recomputed_match": bool(payload_text.strip()) and payload_hash == stable_payload_hash(payload_text.strip()),
        "prelive_packet_id_recomputed_match": bool(recomputed_packet_id) and prelive_packet.get("prelive_packet_id") == recomputed_packet_id,
        "expected_prelive_packet_id_match": expected_prelive_packet_id in (None, prelive_packet.get("prelive_packet_id")),
        "expected_payload_hash_match": expected_payload_hash in (None, payload_hash),
        "profile_guard_status_match": isinstance(guard, Mapping) and guard.get("profile_guard_status") == "contentops_profile_ok",
        "profile_guard_future_click_signal_match": isinstance(guard, Mapping) and guard.get("live_click_allowed") is True,
        "registry_expectation_present": isinstance(registry, Mapping),
        "registry_platform_match": isinstance(registry, Mapping) and registry.get("platform") == "x",
        "registry_account_handle_match": isinstance(registry, Mapping) and registry.get("account_handle_expected") == expected_account_handle,
        "registry_account_binding_match": isinstance(registry, Mapping) and registry.get("account_binding_ref") == expected_account_binding_ref,
        "registry_destination_binding_match": isinstance(registry, Mapping) and registry.get("destination_binding_ref") == expected_destination_binding_ref,
        "registry_payload_hash_match": isinstance(registry, Mapping) and registry.get("payload_hash") == payload_hash,
        "registry_append_still_blocked_now": isinstance(registry, Mapping) and registry.get("registry_append_allowed_now") is False,
        "go_phrase_exact_match": supplied_phrase_hash == expected_phrase_hash,
    }
    blockers = [name for name, ok in checks.items() if ok is not True]
    passed = not blockers
    packet = {
        "task_label": TASK_LABEL,
        "packet_kind": PACKET_KIND,
        "go_packet_status": PASS_STATUS if passed else BLOCKED_STATUS,
        "blocked_reasons": blockers,
        "prelive_packet_id": prelive_packet.get("prelive_packet_id"),
        "recomputed_prelive_packet_id": recomputed_packet_id,
        "payload_hash": payload_hash or None,
        "expected_payload_hash": expected_payload_hash,
        "hash_algorithm": HASH_ALGORITHM,
        "go_phrase_hash_algorithm": GO_PHRASE_HASH_ALGORITHM,
        "expected_go_phrase_hash": expected_phrase_hash,
        "supplied_go_phrase_hash": supplied_phrase_hash,
        "raw_go_phrase_stored": False,
        "go_phrase_value_redacted": True,
        "checks": checks,
        "profile_guard_status": guard.get("profile_guard_status") if isinstance(guard, Mapping) else None,
        "registry_identity_expectation": dict(registry) if isinstance(registry, Mapping) else None,
        "future_live_click_eligible_after_separate_live_task": passed,
        "operator_review_required": True,
        "separate_live_task_required": True,
        "blocked_before_live_click": True,
        "live_click_allowed": False,
        "live_click_performed": False,
        "live_publish_performed": False,
        "publication_registry_record_appended": False,
        **FALSE_SAFETY_FLAGS,
    }
    packet["go_gate_packet_id"] = "x_go_gate_" + _sha({"kind": PACKET_KIND, "prelive": packet["prelive_packet_id"], "payload_hash": payload_hash, "passed": passed})[:16]
    return packet


def build_fixture_evidence_bundle() -> dict[str, Any]:
    expected_profile = r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
    approved_cmd = rf'msedge.exe --remote-debugging-port=9223 --user-data-dir="{expected_profile}"'
    payload = "Capital Chronicle educational briefing: supervised pre-live X payload validation."
    approved = build_prelive_post_packet(payload_text=payload, cdp_port=9223, command_line=approved_cmd)
    cases = {
        "approved_prelive_exact_phrase": build_go_phrase_gate_packet(prelive_packet=approved, operator_go_phrase=EXPECTED_GO_PHRASE),
        "go_phrase_mismatch_blocked": build_go_phrase_gate_packet(prelive_packet=approved, operator_go_phrase="not approved"),
        "prelive_packet_id_mismatch_blocked": build_go_phrase_gate_packet(prelive_packet=dict(approved, prelive_packet_id="x_prelive_mismatch"), operator_go_phrase=EXPECTED_GO_PHRASE),
        "payload_hash_mismatch_blocked": build_go_phrase_gate_packet(prelive_packet=dict(approved, payload_hash="0" * 64), operator_go_phrase=EXPECTED_GO_PHRASE),
        "profile_guard_blocked": build_go_phrase_gate_packet(prelive_packet=build_prelive_post_packet(payload_text=payload, command_line=r"chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\.gemini\antigravity-browser-profile"), operator_go_phrase=EXPECTED_GO_PHRASE),
        "registry_identity_mismatch_blocked": build_go_phrase_gate_packet(prelive_packet=dict(approved, registry_identity_expectation={**approved["registry_identity_expectation"], "destination_binding_ref": "wrong_destination"}), operator_go_phrase=EXPECTED_GO_PHRASE),
    }
    return {
        "task_label": TASK_LABEL,
        "packet_kind": "x_cdp_operator_go_phrase_live_click_gate_dry_run_evidence_bundle_v0",
        "case_count": len(cases),
        "cases": cases,
        "approved_case_future_eligible": cases["approved_prelive_exact_phrase"]["future_live_click_eligible_after_separate_live_task"] is True,
        "all_cases_blocked_before_click": all(case["blocked_before_live_click"] is True for case in cases.values()),
        "raw_go_phrase_stored_anywhere": False,
        "safety_boundary": FALSE_SAFETY_FLAGS,
        "live_action_performed": False,
    }


def write_fixture_evidence(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_fixture_evidence_bundle(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run X CDP operator GO-phrase gate. No browser probe or live click.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fixture-bundle", action="store_true")
    parser.add_argument("--prelive-packet-json", default=None)
    parser.add_argument("--prelive-packet-path", type=Path, default=None)
    parser.add_argument("--operator-go-phrase", default="")
    parser.add_argument("--expected-prelive-packet-id", default=None)
    parser.add_argument("--expected-payload-hash", default=None)
    parser.add_argument("--payload-text", default="")
    parser.add_argument("--cdp-port", type=int, default=9222)
    parser.add_argument("--expected-profile-root", type=Path, default=Path(r"A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"))
    parser.add_argument("--command-line", default=None)
    args = parser.parse_args(argv)
    if not args.dry_run:
        print(json.dumps({"status": "blocked_dry_run_flag_required", "live_click_allowed": False}, sort_keys=True))
        return 2
    if args.fixture_bundle:
        result = build_fixture_evidence_bundle()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    try:
        packet = _load_json_arg(args.prelive_packet_json, args.prelive_packet_path)
    except ValueError as exc:
        print(json.dumps({"status": "blocked_invalid_prelive_packet", "reason": str(exc), "live_click_allowed": False}, sort_keys=True))
        return 2
    if packet is None:
        packet = build_prelive_post_packet(payload_text=args.payload_text, cdp_port=args.cdp_port, command_line=args.command_line, expected_profile_root=args.expected_profile_root)
    result = build_go_phrase_gate_packet(prelive_packet=packet, operator_go_phrase=args.operator_go_phrase, expected_prelive_packet_id=args.expected_prelive_packet_id, expected_payload_hash=args.expected_payload_hash)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["future_live_click_eligible_after_separate_live_task"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
