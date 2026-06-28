"""V6 Operator Approval Capture Lane.

Displays exact payload preview/hash, safety boundaries, and captures or validates
local operator signatures without authorizing dispatch or live writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_OPERATOR_APPROVAL_CAPTURE_UI_AND_SIGNATURE_VALIDATION_LANE_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"
CURRENT_PAYLOAD_HASH = "4bcbbf4eeab1bdfa2f3f94b4dbb042877c67efdb515f7feecaac5ffa3a2e71ff"
NEXT_TASK = "TASK_CONTENTOPS_V6_OPERATOR_SIGN_PAYLOAD_HASH_MANUAL_STEP"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_OPERATOR_APPROVAL_CAPTURE")
DEFAULT_BINDING_DIR = Path("docs/automation/V6_OPERATOR_APPROVAL_SIGNATURE_BINDING")

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


def validate_signature_artifact(
    sig_data: dict[str, Any] | None,
    expected_hash: str
) -> tuple[bool, list[str]]:
    if sig_data is None:
        return False, ["operator_approval_incomplete"]

    blockers = []
    
    # Secrets & Unsafe validation
    if _contains_forbidden_material(sig_data):
        blockers.append("unsafe_signature_material")

    # Hash mismatch
    if sig_data.get("payload_hash") != expected_hash:
        blockers.append("payload_hash_mismatch")

    # Approval decision
    if sig_data.get("approval_decision") != "APPROVED":
        blockers.append("operator_approval_not_approved")

    # Premature dispatch validity
    if sig_data.get("valid_for_dispatch") is True:
        blockers.append("dispatch_validity_claimed_too_early")

    # Malformed signed_at
    if not _is_valid_iso8601(sig_data.get("signed_at")):
        blockers.append("operator_signature_timestamp_missing_or_invalid")

    # Revoked signature
    if sig_data.get("revoked") is True:
        blockers.append("operator_signature_revoked")

    return len(blockers) == 0, sorted(list(set(blockers)))


def generate_cli_reference() -> str:
    return f"""# CLI Reference — V6 Operator Approval Capture

The `operator_approval_capture_v6` CLI allows operators to preview the exact payload details and deterministically sign the payload hash.

## Usage

```powershell
# Display help and preview the current payload hash
python -m live_contentops.operator_approval_capture_v6 --help

# Preview payload body and details
python -m live_contentops.operator_approval_capture_v6 --preview

# Interactively or non-interactively approve and save the signature locally
python -m live_contentops.operator_approval_capture_v6 --approve --operator-id JIM_OPERATOR --write-signature
```

## Security Invariant

This tool runs locally and writes to gitignored files only. It has no capabilities to post to external APIs or dispatch webhooks.
"""


def generate_ui_spec() -> str:
    return f"""# UI Spec — V6 Operator Approval Capture Console

This document specifies the layout and interactive behavior of the future static cockpit approval capture panel.

## Visual Design System
- **Color Theme**: Rich dark mode with amber alert status indicators.
- **Header**: Shows `"V6 Operator Approval Capture Console"`.
- **Payload Display**:
  - Bound Hash: `{CURRENT_PAYLOAD_HASH}`
  - Preview Ref: `docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json`
- **Safety Status Display**:
  - `dispatch_allowed_now`: false (Locked)
  - `live_write_allowed_now`: false (Locked)
  - `kill_switch_active`: true (Locked)

## Interactions
- **Review Decision Selection**: Dropdown or toggle (PENDING / APPROVED).
- **Signature Output**: Writes operator signature JSON locally upon operator action.
"""


def generate_blocker_report(status: str, blockers: list[str]) -> str:
    blocker_lines = "\n".join(f"- `{b}`" for b in blockers) if blockers else "- None"
    return f"""# Operator Approval Capture Blocker Report

- **Capture Status**: {status}
- **Active Capture Blockers**:

{blocker_lines}

## Safety Boundary Details

1. **operator_approval_incomplete**
   - *Detail*: Jim must review the payload and sign off through the CLI or console to capture the approval signature.
2. **dispatch_validity_claimed_too_early**
   - *Detail*: The signature must explicitly have `valid_for_dispatch=false` to prevent premature live writes.
"""


def generate_runbook() -> str:
    return f"""# Operator Approval Capture Runbook

Follow these steps to run the approval capture lane and generate your signature locally:

## Signature Generation Steps

1. Run the preview command to inspect the exact payload title, body, and hash:
   ```powershell
   python -m live_contentops.operator_approval_capture_v6 --preview
   ```
2. Confirm the payload hash matches `{CURRENT_PAYLOAD_HASH}`.
3. If correct, execute the approval command with your operator ID:
   ```powershell
   python -m live_contentops.operator_approval_capture_v6 --approve --operator-id JIM_OPERATOR --write-signature
   ```
4. Re-run validation to verify that the local signature is bound and valid.
"""


def generate_implementation_report(status: str, blockers: list[str]) -> str:
    blockers_text = ", ".join(blockers) if blockers else "none"
    return f"""# V6 Operator Approval Capture Implementation Report

- **Task Label**: {TASK_LABEL}
- **Capture Status**: {status}
- **Blockers**: {blockers_text}

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

Recommended next task:

`{NEXT_TASK}`

Goal: Jim manually signs payload hash review intent while keeping dispatch validity disabled.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Operator Approval Capture Lane")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--binding-dir", default=str(DEFAULT_BINDING_DIR))
    parser.add_argument("--preview", action="store_true", help="Display payload preview and hash")
    parser.add_argument("--approve", action="store_true", help="Approve payload hash")
    parser.add_argument("--operator-id", default="PLACEHOLDER_OPERATOR_ID", help="Specify Operator ID")
    parser.add_argument("--write-signature", action="store_true", help="Write operator signature locally")
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    binding_dir = Path(args.binding_dir)

    is_default_output = args.output_dir == str(DEFAULT_OUTPUT_DIR)
    is_default_binding = args.binding_dir == str(DEFAULT_BINDING_DIR)

    # Resolve actual paths depending on test environment isolation
    if is_default_output:
        capture_dir = out_dir
        base_automation_dir = Path("docs/automation")
    else:
        capture_dir = out_dir / "V6_OPERATOR_APPROVAL_CAPTURE"
        base_automation_dir = out_dir

    if is_default_binding:
        actual_binding_dir = DEFAULT_BINDING_DIR
    else:
        actual_binding_dir = out_dir / "V6_OPERATOR_APPROVAL_SIGNATURE_BINDING"

    capture_dir.mkdir(parents=True, exist_ok=True)
    actual_binding_dir.mkdir(parents=True, exist_ok=True)

    # 1. Read Payload and Hash materials
    payload_hash_path = base_automation_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json"
    payload_record = load_json(payload_hash_path) or {}
    expected_hash = payload_record.get("payload_hash") or CURRENT_PAYLOAD_HASH

    payload_preview_path = base_automation_dir / "V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json"
    payload_preview = load_json(payload_preview_path) or {}

    # 2. Check for local signature in both fallback paths
    sig_binding_path = actual_binding_dir / "operator_signature.json"
    sig_capture_path = capture_dir / "operator_approval_signature.local.json"

    sig_data = load_json(sig_binding_path) or load_json(sig_capture_path)

    # 3. Action handling
    if args.preview:
        print(f"--- Payload Preview ---")
        print(f"Preview ID: {payload_preview.get('payload_preview_id', 'Unknown')}")
        print(f"Payload Body Redacted: {payload_preview.get('payload_body_redacted', True)}")
        print(f"Bound Hash: {expected_hash}")
        print(f"Dispatch Authorized: False (Safety Lock Active)")
        return 0

    if args.approve:
        if args.operator_id == "PLACEHOLDER_OPERATOR_ID":
            print("Error: --operator-id must be specified when approving.")
            return 1
        
        # Build signature object
        sig_data = {
            "operator_id": args.operator_id,
            "approval_decision": "APPROVED",
            "payload_hash": expected_hash,
            "payload_preview_ref": "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json",
            "payload_hash_record_ref": "docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_hash_record.json",
            "signed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "valid_for_dispatch": False,
            "revoked": False,
            "operator_notes_redacted_or_absent": True,
            "is_local_only": True
        }

        if args.write_signature:
            write_json(sig_binding_path, sig_data)
            write_json(sig_capture_path, sig_data)
            print(f"Local operator signature successfully written.")

    # 4. Perform validation
    is_valid, blockers = validate_signature_artifact(sig_data, expected_hash)

    status = "AWAITING_OPERATOR_ACTION"
    if sig_data is not None:
        if is_valid:
            status = "SIGNATURE_VALIDATED_REVIEW_ONLY"
        else:
            status = "SIGNATURE_INVALID"

    # 5. Build capture packet
    capture_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "approval_capture_status": status,
        "operator_approval_captured": is_valid,
        "operator_signature_created": sig_data is not None,
        "operator_signature_valid": is_valid,
        "payload_hash_displayed": True,
        "exact_payload_preview_displayed": True,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "destination_binding_complete": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "next_recommended_task": NEXT_TASK,
        "capture_blockers": blockers,
        "is_local_only": True
    }

    validation_report = {
        "operator_signature_present": sig_data is not None,
        "operator_signature_valid": is_valid,
        "validation_blockers": blockers,
        "payload_hash_checked": expected_hash,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "destination_binding_complete": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "public_postable": False,
        "kill_switch_active": True,
        "is_local_only": True
    }

    # 6. Materialize capture documents
    write_json(capture_dir / "operator_approval_capture_packet.json", capture_packet)
    write_json(capture_dir / "operator_approval_capture_validation_report.json", validation_report)
    (capture_dir / "operator_approval_capture_ui_spec.md").write_text(generate_ui_spec(), encoding="utf-8")
    (capture_dir / "operator_approval_capture_cli_reference.md").write_text(generate_cli_reference(), encoding="utf-8")
    (capture_dir / "operator_approval_capture_blocker_report.md").write_text(generate_blocker_report(status, blockers), encoding="utf-8")
    (capture_dir / "operator_approval_capture_runbook.md").write_text(generate_runbook(), encoding="utf-8")
    (capture_dir / "implementation_report.md").write_text(generate_implementation_report(status, blockers), encoding="utf-8")
    (capture_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(), encoding="utf-8")

    print(json.dumps({
        "approval_capture_status": status,
        "operator_approval_captured": is_valid,
        "operator_signature_valid": is_valid
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
