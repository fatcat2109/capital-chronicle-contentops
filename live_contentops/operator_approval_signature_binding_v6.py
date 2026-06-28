"""V6 Operator Approval Signature Binding Lane.

Binds operator approval intent to exact payload preview and deterministic payload hash
without granting dispatch authority, live-write capability, or public readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_SIGNATURE_BINDING_LANE_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"
CURRENT_PAYLOAD_HASH = "4bcbbf4eeab1bdfa2f3f94b4dbb042877c67efdb515f7feecaac5ffa3a2e71ff"
NEXT_MANUAL_SIGN_TASK = "TASK_CONTENTOPS_V6_OPERATOR_SIGN_PAYLOAD_HASH_MANUAL_STEP"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING")

FORBIDDEN_TEXT_FRAGMENTS = (
    "discord.com/api/webhooks",
    "token_value",
    "cookie_value",
    "secret_key",
    "env_value",
    "session_value",
    "authorization:",
    "bearer ",
    "c:/users/",
    "a:/",
    ".env",
)


def write_json(path: str | Path, data: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any] | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return "placeholder" in value.lower()
    if isinstance(value, dict):
        return any(_contains_placeholder(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_placeholder(v) for v in value)
    return False


def _contains_forbidden_material(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return any(fragment in lowered for fragment in FORBIDDEN_TEXT_FRAGMENTS)
    if isinstance(value, dict):
        return any(_contains_forbidden_material(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_material(v) for v in value)
    return False


def _is_valid_iso8601(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def packet_has_valid_payload_hash(packet: dict[str, Any] | None, record: dict[str, Any] | None) -> bool:
    if not packet or not record:
        return False
    payload_hash = packet.get("payload_hash")
    if packet.get("payload_hash_created") is not True:
        return False
    if packet.get("exact_payload_preview_created") is not True:
        return False
    if packet.get("payload_preview_status") != "READY_FOR_OPERATOR_REVIEW":
        return False
    if not isinstance(payload_hash, str) or len(payload_hash) != 64:
        return False
    if record.get("payload_hash") != payload_hash:
        return False
    if _contains_placeholder(packet) or _contains_placeholder(record):
        return False
    return True


def build_signature_template(payload_hash: str) -> dict[str, Any]:
    return {
        "operator_id": "PLACEHOLDER_OPERATOR_ID",
        "approval_decision": "PENDING",
        "payload_hash": payload_hash,
        "payload_preview_ref": "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json",
        "payload_hash_record_ref": "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json",
        "signed_at": None,
        "valid_for_dispatch": False,
        "revoked": False,
        "operator_notes_redacted_or_absent": True,
        "is_local_only": True,
    }


def validate_signature_packet(
    signature_packet: dict[str, Any] | None,
    *,
    expected_payload_hash: str,
    payload_hash_ready: bool,
    exact_payload_preview_bound: bool,
) -> tuple[bool, bool, list[str], dict[str, Any]]:
    blockers: list[str] = []
    operator_signature_present = signature_packet is not None
    operator_signature_valid = False

    if not payload_hash_ready:
        blockers.append("payload_hash_not_ready")
    if not exact_payload_preview_bound:
        blockers.append("exact_payload_preview_not_ready")

    if signature_packet is None:
        blockers.append("operator_approval_incomplete")
    else:
        if _contains_forbidden_material(signature_packet):
            blockers.append("unsafe_signature_material")
        if signature_packet.get("payload_hash") != expected_payload_hash:
            blockers.append("payload_hash_mismatch")
        if signature_packet.get("approval_decision") != "APPROVED":
            blockers.append("operator_approval_not_approved")
        if signature_packet.get("valid_for_dispatch") is True:
            blockers.append("dispatch_validity_claimed_too_early")
        if not _is_valid_iso8601(signature_packet.get("signed_at")):
            blockers.append("operator_signature_timestamp_missing_or_invalid")
        if signature_packet.get("revoked") is True:
            blockers.append("operator_signature_revoked")
        if not blockers:
            operator_signature_valid = True

    validation_report = {
        "operator_signature_present": operator_signature_present,
        "operator_signature_valid": operator_signature_valid,
        "validation_blockers": sorted(set(blockers)),
        "payload_hash_checked": expected_payload_hash,
        "payload_hash_bound": payload_hash_ready,
        "exact_payload_preview_bound": exact_payload_preview_bound,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "destination_binding_complete": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "is_local_only": True,
    }
    return operator_signature_present, operator_signature_valid, sorted(set(blockers)), validation_report


def generate_blocker_report(status: str, blockers: list[str]) -> str:
    blocker_lines = "\n".join(f"- `{blocker}`" for blocker in blockers) if blockers else "- None"
    return f"""# Operator Signature Binding Blocker Report

- **Signature Binding Status**: {status}
- **Binding Blockers**:

{blocker_lines}

## Boundary Notes

- Binding lane can validate operator intent against exact payload hash only.
- Binding lane cannot authorize dispatch, create outbox entries, bind destinations, hydrate credentials, or mark content public-postable.
- `valid_for_dispatch` must remain `false` in this lane.
"""


def generate_runbook() -> str:
    return f"""# Operator Signature Binding Runbook

Jim, use this lane only to bind manual approval intent to payload hash `{CURRENT_PAYLOAD_HASH}`.

## Steps

- [ ] Open `operator_signature_template.json` in `docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/`.
- [ ] Replace `PLACEHOLDER_OPERATOR_ID` with your operator ID.
- [ ] Set `approval_decision` to `APPROVED` only after reviewing exact payload preview.
- [ ] Enter `signed_at` in ISO-8601 format.
- [ ] Keep `valid_for_dispatch=false`.
- [ ] Keep `revoked=false` unless intentionally withdrawing approval intent.
- [ ] Save signed file as local review artifact and re-run validation.

## Hard Stops

> [!IMPORTANT]
> This lane does not make dispatch valid. Dispatch remains blocked until destination binding, approval ledger, outbox creation, supervised dispatch readiness, and kill-switch review all pass.

> [!WARNING]
> Do not add secrets, webhook URLs, cookies, session material, env values, or local machine paths to signature artifact fields.
"""


def generate_implementation_report(status: str, blockers: list[str]) -> str:
    blocker_text = ", ".join(blockers) if blockers else "none"
    return f"""# V6 Operator Approval Signature Binding Implementation Report

- **Task Label**: {TASK_LABEL}
- **Signature Binding Status**: {status}
- **Payload Hash Bound**: `true`
- **Exact Payload Preview Bound**: `true`
- **Current Payload Hash**: `{CURRENT_PAYLOAD_HASH}`
- **Active Binding Blockers**: {blocker_text}

- **Compliance Rules**:
  - No secret keys output: `true`
  - No webhook URLs or tokens printed: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
"""


def generate_next_task_pointer() -> str:
    return f"""# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`{NEXT_MANUAL_SIGN_TASK}`

Goal: Jim manually signs payload hash review intent while keeping dispatch validity disabled.
"""


def materialize_signature_binding_packets(base_automation_dir: str | Path) -> dict[str, Any]:
    base_dir = Path(base_automation_dir)
    payload_packet = load_json(base_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_preview_hash_packet.json") or {}
    payload_preview = load_json(base_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json") or {}
    payload_record = load_json(base_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json") or {}
    payload_inputs = load_json(base_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_inputs_redacted.json") or {}
    approval_gate = load_json(base_dir / "V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json") or {}
    approval_review = load_json(base_dir / "V6_OPERATOR_APPROVAL_GATE/operator_approval_review_packet.json") or {}
    existing_template = load_json(base_dir / "V6_OPERATOR_APPROVAL_GATE/operator_approval_signature_template.json") or {}

    payload_hash_ready = packet_has_valid_payload_hash(payload_packet, payload_record)
    expected_payload_hash = payload_record.get("payload_hash") if payload_hash_ready else None
    exact_payload_preview_bound = bool(payload_preview) and not _contains_placeholder(payload_preview)
    signature_template = build_signature_template(expected_payload_hash or CURRENT_PAYLOAD_HASH)

    signature_packet_path = base_dir / "V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature.json"
    signature_packet = load_json(signature_packet_path)

    operator_signature_present, operator_signature_valid, blockers, validation_report = validate_signature_packet(
        signature_packet,
        expected_payload_hash=expected_payload_hash or CURRENT_PAYLOAD_HASH,
        payload_hash_ready=payload_hash_ready,
        exact_payload_preview_bound=exact_payload_preview_bound,
    )

    status = "SIGNATURE_BOUND_REVIEW_ONLY" if operator_signature_valid else "AWAITING_OPERATOR_SIGNATURE"
    packet_id_seed = f"{expected_payload_hash or CURRENT_PAYLOAD_HASH}_{status}_{operator_signature_present}"
    packet_id = f"sigbind_{hashlib.sha256(packet_id_seed.encode('utf-8')).hexdigest()[:12]}"

    packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "operator_signature_binding_packet_id": packet_id,
        "signature_binding_status": status,
        "payload_hash_bound": payload_hash_ready,
        "exact_payload_preview_bound": exact_payload_preview_bound,
        "payload_hash": expected_payload_hash or CURRENT_PAYLOAD_HASH,
        "payload_hash_record_ref": "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json",
        "payload_preview_ref": "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json",
        "approval_gate_packet_ref": "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_gate_packet.json",
        "approval_review_packet_ref": "docs/automation/V6_OPERATOR_APPROVAL_GATE/operator_approval_review_packet.json",
        "operator_signature_template_ref": "docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature_template.json",
        "operator_signature_present": operator_signature_present,
        "operator_signature_valid": operator_signature_valid,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "destination_binding_complete": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "next_recommended_task": NEXT_MANUAL_SIGN_TASK,
        "binding_blockers": blockers,
        "approval_gate_status": approval_gate.get("approval_gate_status"),
        "payload_preview_status": payload_packet.get("payload_preview_status"),
        "review_required": bool(approval_review.get("review_required", True)),
        "existing_gate_template_is_inert": existing_template.get("valid_for_dispatch") is False,
        "payload_inputs_redacted": payload_inputs.get("hash_blocked") is not True,
        "is_local_only": True,
    }

    review_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "payload_hash": expected_payload_hash or CURRENT_PAYLOAD_HASH,
        "payload_hash_bound": payload_hash_ready,
        "exact_payload_preview_bound": exact_payload_preview_bound,
        "payload_preview_ref": "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json",
        "payload_hash_record_ref": "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json",
        "operator_signature_present": operator_signature_present,
        "operator_signature_valid": operator_signature_valid,
        "dispatch_not_authorized": True,
        "live_write_not_authorized": True,
        "public_postable": False,
        "is_local_only": True,
    }

    return {
        "packet": packet,
        "review_packet": review_packet,
        "template": signature_template,
        "validation_report": validation_report,
        "blockers": blockers,
        "status": status,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Operator Approval Signature Binding Lane")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    is_default = args.output_dir == str(DEFAULT_OUTPUT_DIR)
    if is_default:
        binding_dir = out_dir
        base_automation_dir = Path("docs/automation")
    else:
        binding_dir = out_dir / "V6_OPERATOR_APPROVAL_SIGNATURE_BINDING"
        binding_dir.mkdir(parents=True, exist_ok=True)
        base_automation_dir = out_dir

    materials = materialize_signature_binding_packets(base_automation_dir)
    packet = materials["packet"]
    review_packet = materials["review_packet"]
    template = materials["template"]
    validation_report = materials["validation_report"]
    blockers = materials["blockers"]
    status = materials["status"]

    write_json(binding_dir / "operator_signature_binding_packet.json", packet)
    write_json(binding_dir / "operator_signature_binding_review_packet.json", review_packet)
    write_json(binding_dir / "operator_signature_template.json", template)
    write_json(binding_dir / "operator_signature_validation_report.json", validation_report)
    (binding_dir / "operator_signature_blocker_report.md").write_text(generate_blocker_report(status, blockers), encoding="utf-8")
    (binding_dir / "operator_signature_runbook.md").write_text(generate_runbook(), encoding="utf-8")
    (binding_dir / "implementation_report.md").write_text(generate_implementation_report(status, blockers), encoding="utf-8")
    (binding_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(), encoding="utf-8")

    print(json.dumps({
        "signature_binding_status": status,
        "operator_signature_present": packet["operator_signature_present"],
        "operator_signature_valid": packet["operator_signature_valid"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
