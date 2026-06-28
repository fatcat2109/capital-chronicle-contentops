"""V6 Destination Binding and Outbox Draft Lane.

Prepares a review-only outbox draft and destination binding after operator signature
intent is validated, keeping all live writes and dispatching disabled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DESTINATION_BINDING_AND_OUTBOX_DRAFT_LANE_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"
CURRENT_PAYLOAD_HASH = "4bcbbf4eeab1bdfa2f3f94b4dbb042877c67efdb515f7feecaac5ffa3a2e71ff"
NEXT_TASK_PENDING = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_CAPTURE_LOCAL_RUN_STEP"
NEXT_TASK_SIGNED = "TASK_CONTENTOPS_V6_SUPERVISED_DISPATCH_READINESS_REVALIDATION_LANE_HEAVY_BATCH_V0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_DESTINATION_BINDING_OUTBOX_DRAFT")

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


def validate_local_signature(sig: dict[str, Any] | None, expected_hash: str) -> list[str]:
    if not sig:
        return ["operator_signature_missing"]

    blockers = []
    if _contains_forbidden_material(sig):
        blockers.append("unsafe_signature_material")
    if sig.get("payload_hash") != expected_hash:
        blockers.append("payload_hash_mismatch")
    if sig.get("approval_decision") != "APPROVED":
        blockers.append("operator_approval_not_approved")
    if sig.get("valid_for_dispatch") is True:
        blockers.append("dispatch_validity_claimed_too_early")
    if not _is_valid_iso8601(sig.get("signed_at")):
        blockers.append("operator_signature_timestamp_missing_or_invalid")
    if sig.get("revoked") is True:
        blockers.append("operator_signature_revoked")

    return sorted(list(set(blockers)))


def generate_blocker_report(status: str, blockers: list[str]) -> str:
    blocker_lines = "\n".join(f"- `{b}`" for b in blockers) if blockers else "- None"
    return f"""# Destination Binding Blocker Report

- **Status**: {status}
- **Active Blockers**:

{blocker_lines}

## Safety Notes
- Destination is operator review only, live dispatch is blocked.
- Valid operator signature is required to advance.
"""


def generate_runbook() -> str:
    return f"""# Destination Binding & Outbox Draft Runbook

Follow these steps to progress destination binding and prepare outbox draft review:

1. Confirm operator signature capture validation succeeds.
2. Verify candidate review-only destination config matrix.
3. Review generated inert outbox draft.
"""


def generate_implementation_report(status: str, blockers: list[str]) -> str:
    blockers_text = ", ".join(blockers) if blockers else "none"
    return f"""# V6 Destination Binding & Outbox Draft Implementation Report

- **Task Label**: {TASK_LABEL}
- **Status**: {status}
- **Blockers**: {blockers_text}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Destination Binding and Outbox Draft")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    is_default = args.output_dir == str(DEFAULT_OUTPUT_DIR)

    if is_default:
        dest_dir = out_dir
        base_automation_dir = Path("docs/automation")
    else:
        dest_dir = out_dir / "V6_DESTINATION_BINDING_OUTBOX_DRAFT"
        base_automation_dir = out_dir

    dest_dir.mkdir(parents=True, exist_ok=True)

    # 1. Read Payload and Hash Record
    payload_hash_path = base_automation_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json"
    payload_record = load_json(payload_hash_path) or {}
    expected_hash = payload_record.get("payload_hash") or CURRENT_PAYLOAD_HASH

    payload_preview_path = base_automation_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json"
    payload_preview = load_json(payload_preview_path) or {}

    # 2. Check for local signature in both paths
    sig_binding_path = base_automation_dir / "V6_OPERATOR_APPROVAL_SIGNATURE_BINDING/operator_signature.json"
    sig_capture_path = base_automation_dir / "V6_OPERATOR_APPROVAL_CAPTURE/operator_approval_signature.local.json"

    sig_data = load_json(sig_binding_path) or load_json(sig_capture_path)

    # 3. Validation
    blockers = validate_local_signature(sig_data, expected_hash)
    operator_signature_valid = (sig_data is not None and not blockers)

    destination_binding_complete = operator_signature_valid
    outbox_draft_created = operator_signature_valid

    status = "BLOCKED_AWAITING_OPERATOR_SIGNATURE"
    if sig_data is not None:
        if operator_signature_valid:
            status = "OUTBOX_DRAFT_READY_FOR_REVIEW"
        else:
            status = "SIGNATURE_INVALID_OUTBOX_BLOCKED"

    # Destination binding model
    review_matrix = [
        {
            "platform_family": "telegram",
            "destination_class": "operator_review_only",
            "live_destination_bound": False,
            "destination_identifier_redacted_or_absent": True,
            "credential_handle_required_later": True,
            "credential_hydrated": False,
            "dispatch_adapter_class": "not_enabled",
            "manual_fallback_required": True,
            "official_docs_required_before_live": True,
            "account_binding_required_before_live": True
        }
    ]

    # Outbox draft model
    if outbox_draft_created:
        draft_preview = {
            "outbox_draft_created": True,
            "dispatchable": False,
            "task_label": TASK_LABEL,
            "payload_hash": expected_hash,
            "draft_details": {
                "platform_family": "telegram",
                "destination_class": "operator_review_only",
                "body_preview": payload_preview.get("payload_preview_id", "Unknown")
            }
        }
    else:
        draft_preview = {
            "outbox_draft_created": False,
            "dispatchable": False,
            "blockers": blockers
        }

    # Validation report
    validation_report = {
        "operator_signature_valid": operator_signature_valid,
        "destination_binding_complete": destination_binding_complete,
        "outbox_draft_created": outbox_draft_created,
        "validation_blockers": blockers,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "destination_binding_complete": destination_binding_complete,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "is_local_only": True
    }

    # Main packet
    next_task = NEXT_TASK_SIGNED if operator_signature_valid else NEXT_TASK_PENDING
    packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "destination_outbox_status": status,
        "operator_signature_valid": operator_signature_valid,
        "destination_binding_complete": destination_binding_complete,
        "outbox_draft_created": outbox_draft_created,
        "outbox_entry_created": False,
        "outbox_dispatchable": False,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "next_recommended_task": next_task,
        "blockers": blockers,
        "is_local_only": True
    }

    # Write files
    write_json(dest_dir / "destination_binding_outbox_draft_packet.json", packet)
    write_json(dest_dir / "destination_binding_review_matrix.json", review_matrix)
    write_json(dest_dir / "outbox_draft_preview_packet.json", draft_preview)
    write_json(dest_dir / "outbox_draft_validation_report.json", validation_report)
    (dest_dir / "destination_binding_blocker_report.md").write_text(generate_blocker_report(status, blockers), encoding="utf-8")
    (dest_dir / "destination_binding_runbook.md").write_text(generate_runbook(), encoding="utf-8")
    (dest_dir / "implementation_report.md").write_text(generate_implementation_report(status, blockers), encoding="utf-8")
    (dest_dir / "next_task_pointer.md").write_text(
        f"# Next Task Pointer\n\nRecommended next task:\n\n`{next_task}`\n", encoding="utf-8"
    )

    print(json.dumps({
        "destination_outbox_status": status,
        "operator_signature_valid": operator_signature_valid,
        "outbox_draft_created": outbox_draft_created
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
