from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"A:\Capital Chronicle\tools\cc-live-contentops")

files = {
ROOT / "live_contentops" / "dispatch_outcome_identity_link_v6.py": '''"""Local-only V6 bridge from publication identity to dispatch outcome audit input.

No browser, network, API, webhook, env, credential, cookie, storage, session, token,
or header material belongs here.
"""
from __future__ import annotations

from typing import Any

from live_contentops.platform_publication_identity_registry_v6 import validate_registry_record

SAFE_FALSE_FLAGS = (
    "cookie_read_performed",
    "local_storage_read_performed",
    "session_storage_read_performed",
    "token_or_header_read_performed",
    "raw_secret_output",
)
SECRET_KEY_MARKERS = (
    "cookie",
    "token",
    "secret",
    "authorization",
    "password",
    "session",
    "localstorage",
    "sessionstorage",
    "credential_value",
    "raw_header",
)
REQUIRED_DISPATCH_CONTEXT = ("approval_id", "outbox_entry_id", "dispatch_attempt_id")


def _has_secret_like_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            key_lower = str(key).lower()
            if any(marker in key_lower for marker in SECRET_KEY_MARKERS):
                return True
            if _has_secret_like_key(child):
                return True
    if isinstance(value, list):
        return any(_has_secret_like_key(child) for child in value)
    return False


def make_dispatch_outcome_identity_link(record: dict[str, Any]) -> dict[str, Any]:
    """Build a redacted local-only dispatch outcome/audit identity link."""
    blockers: list[str] = []
    if _has_secret_like_key(record):
        blockers.append("secret_like_registry_field_blocked")
    try:
        validate_registry_record(record)
    except ValueError as exc:
        blockers.append(str(exc))

    for flag in SAFE_FALSE_FLAGS:
        if record.get(flag) is not False:
            blockers.append(f"{flag}_must_be_false")

    if record.get("platform") == "x" and record.get("no_paid_api_used") is not True:
        blockers.append("x_paid_api_flag_blocked")

    missing_context = [field for field in REQUIRED_DISPATCH_CONTEXT if not record.get(field)]
    blockers.extend(f"{field}_missing" for field in missing_context)

    unsafe = any(
        blocker == "secret_like_registry_field_blocked"
        or blocker.endswith("_must_be_false")
        or blocker == "x_paid_api_flag_blocked"
        for blocker in blockers
    )
    ready = not blockers
    if unsafe:
        status = "BLOCKED_UNSAFE_CAPTURE_CLAIM"
    elif missing_context:
        status = "REVIEW_MISSING_DISPATCH_CONTEXT"
    else:
        status = "READY_FOR_PUBLICATION_AUDIT_RECORD"

    link = {
        "link_status": status,
        "registry_record_id": record.get("registry_record_id"),
        "platform": record.get("platform"),
        "public_url": record.get("public_url"),
        "platform_publication_id": record.get("platform_publication_id"),
        "payload_hash": record.get("payload_hash"),
        "approval_id": record.get("approval_id"),
        "outbox_entry_id": record.get("outbox_entry_id"),
        "dispatch_attempt_id": record.get("dispatch_attempt_id"),
        "account_binding_ref": record.get("account_binding_ref"),
        "destination_binding_ref": record.get("destination_binding_ref"),
        "confirmation_class": record.get("confirmation_class"),
        "capture_method": record.get("capture_method"),
        "no_paid_api_used": record.get("no_paid_api_used") is True,
        "live_write_attempted": False,
        "api_request_performed": False,
        "webhook_request_performed": False,
        "browser_session_started": False,
        "credential_value_read": False,
        "cookie_read_performed": False,
        "local_storage_read_performed": False,
        "session_storage_read_performed": False,
        "token_or_header_read_performed": False,
        "raw_secret_output": False,
        "ready_for_publication_audit_record": ready,
        "blockers": blockers,
    }
    validate_dispatch_outcome_identity_link(link)
    return link


def validate_dispatch_outcome_identity_link(link: dict[str, Any]) -> None:
    """Validate the redacted local-only identity link."""
    if _has_secret_like_key(link):
        raise ValueError("secret_like_identity_link_field_blocked")
    if not link.get("platform"):
        raise ValueError("platform_required")
    if not link.get("public_url"):
        raise ValueError("public_url_required")
    if not link.get("payload_hash"):
        raise ValueError("payload_hash_required")
    for flag in (
        "live_write_attempted",
        "api_request_performed",
        "webhook_request_performed",
        "browser_session_started",
        "credential_value_read",
        *SAFE_FALSE_FLAGS,
    ):
        if link.get(flag) is not False:
            raise ValueError(f"{flag}_must_be_false")
    if link.get("ready_for_publication_audit_record") is True and link.get("blockers"):
        raise ValueError("ready_link_cannot_have_blockers")
''',
ROOT / "tests" / "test_dispatch_outcome_identity_link_v6.py": '''import pytest

from live_contentops.dispatch_outcome_identity_link_v6 import make_dispatch_outcome_identity_link
from live_contentops.platform_publication_identity_registry_v6 import make_registry_record


def _x_record(**overrides):
    record = make_registry_record(
        platform="x",
        payload_hash="sha256:abc123",
        public_url="https://x.com/CapitalChron/status/1800000000000000000",
        approval_id="approval_1",
        outbox_entry_id="outbox_1",
        dispatch_attempt_id="dispatch_1",
        account_binding_ref="acct_x_capital_chronicle",
        destination_binding_ref="dest_x_main",
        created_at_utc="2026-07-03T00:00:00+00:00",
    )
    record.update(overrides)
    return record


def test_valid_x_identity_record_produces_audit_ready_link():
    link = make_dispatch_outcome_identity_link(_x_record())

    assert link["link_status"] == "READY_FOR_PUBLICATION_AUDIT_RECORD"
    assert link["ready_for_publication_audit_record"] is True
    assert link["platform_publication_id"] == "1800000000000000000"
    assert link["no_paid_api_used"] is True
    assert link["live_write_attempted"] is False
    assert link["api_request_performed"] is False
    assert link["webhook_request_performed"] is False
    assert link["browser_session_started"] is False
    assert link["blockers"] == []


def test_missing_dispatch_context_returns_review_blockers():
    record = _x_record(approval_id=None, outbox_entry_id=None, dispatch_attempt_id=None)
    link = make_dispatch_outcome_identity_link(record)

    assert link["link_status"] == "REVIEW_MISSING_DISPATCH_CONTEXT"
    assert link["ready_for_publication_audit_record"] is False
    assert set(link["blockers"]) >= {
        "approval_id_missing",
        "outbox_entry_id_missing",
        "dispatch_attempt_id_missing",
    }


def test_manual_non_x_platform_can_link_when_safe():
    record = make_registry_record(
        platform="substack",
        payload_hash="sha256:def456",
        public_url="https://capitalchronicle.substack.com/p/example",
        platform_publication_id="substack_post_1",
        approval_id="approval_1",
        outbox_entry_id="outbox_1",
        dispatch_attempt_id="dispatch_1",
        capture_method="operator_supplied_public_url",
        confirmation_class="operator_supplied_url",
        created_at_utc="2026-07-03T00:00:00+00:00",
    )
    link = make_dispatch_outcome_identity_link(record)

    assert link["platform"] == "substack"
    assert link["link_status"] == "READY_FOR_PUBLICATION_AUDIT_RECORD"


def test_paid_api_flag_on_x_blocks():
    record = _x_record(no_paid_api_used=False)
    link = make_dispatch_outcome_identity_link(record)

    assert link["link_status"] == "BLOCKED_UNSAFE_CAPTURE_CLAIM"
    assert "x_paid_api_flag_blocked" in link["blockers"]


@pytest.mark.parametrize(
    "flag",
    [
        "cookie_read_performed",
        "local_storage_read_performed",
        "session_storage_read_performed",
        "token_or_header_read_performed",
        "raw_secret_output",
    ],
)
def test_secret_and_session_read_flags_block(flag):
    record = _x_record(**{flag: True})
    link = make_dispatch_outcome_identity_link(record)

    assert link["link_status"] == "BLOCKED_UNSAFE_CAPTURE_CLAIM"
    assert f"{flag}_must_be_false" in link["blockers"]


def test_secret_like_keys_in_record_block_without_outputting_values():
    record = _x_record()
    record["raw_secret_value"] = "do-not-print"

    link = make_dispatch_outcome_identity_link(record)

    assert link["link_status"] == "BLOCKED_UNSAFE_CAPTURE_CLAIM"
    assert "secret_like_registry_field_blocked" in link["blockers"]
    assert "raw_secret_value" not in link
    assert "do-not-print" not in str(link)


def test_output_contains_no_raw_credential_or_session_fields():
    link = make_dispatch_outcome_identity_link(_x_record())
    serialized = " ".join(link.keys()).lower()

    assert "password" not in serialized
    assert "authorization" not in serialized
    assert "localstorage" not in serialized
    assert "sessionstorage" not in serialized
''',
ROOT / "docs" / "cleanup_phase_closed_2026-07-03.md": '''# Cleanup Phase Closed — 2026-07-03

## Status

The deep repository cleaning phase is closed for current execution purposes.

Current agents should start from:

- [CURRENT_CONTEXT.md](CURRENT_CONTEXT.md)
- [CONTENTOPS_FINAL_AUTOMATION_PIPELINE_READINESS_REPORT.md](CONTENTOPS_FINAL_AUTOMATION_PIPELINE_READINESS_REPORT.md)
- [V6 final product master plan](Capital%20Chronicle%20ContentOps%20V6%20%E2%80%94%20AI-Native%20Editorial,%20Publishing,%20and%20Community%20Operating%20System%20Master%20Plan.md)
- [V6 25-task execution plan](Capital%20Chronicle%20ContentOps%20V6%20%E2%80%94%20Final%20Product%2025-Task%20Execution%20Plan.md)

## Cleanup Completed

- Removed generated caches/build outputs.
- Archived old source bundles where available.
- Archived stale Telegram, Discord, X OAuth, and V5/versioned stacks.
- Archived stale automation packet families.
- Preserved only current authority docs, current code roots, and rollback archives.

## Manifests

- [cleanup_manifest_2026-07-03-pass3.json](cleanup_manifest_2026-07-03-pass3.json)
- [pass3 archive](archive/_repo_cleanup_2026-07-03-pass3)

## Non-Blocking Residues

- `project_sources_bundle_AFTER_DISCORD_PRE_LIVE_READINESS/` is an empty locked
  Windows directory with 0 files and 0 MB.
- Large rollback archives remain under `docs/archive/` by design.

## Current Next Build Lane

```text
TASK_CONTENTOPS_V6_IDENTITY_REGISTRY_TO_DISPATCH_OUTCOME_MODEL_V0
```

Purpose: connect captured public publication identity records to a local-only
redacted dispatch outcome/audit input model, without live writes, paid APIs,
browser probes, credential reads, webhook calls, scheduler, retry, scraping, or
provider calls.
'''
}

for path, content in files.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    path.write_text(content, encoding="utf-8")

current_context = ROOT / "docs" / "CURRENT_CONTEXT.md"
text = current_context.read_text(encoding="utf-8")
text = text.replace(
    "## Current next task\n\n`TASK_CONTENTOPS_V6_IDENTITY_REGISTRY_TO_DISPATCH_OUTCOME_MODEL_V0`\n",
    "## Current next task\n\n`TASK_CONTENTOPS_V6_IDENTITY_REGISTRY_TO_DISPATCH_OUTCOME_MODEL_V0`\n\n## Cleanup closure\n\nDeep cleaning pass 1/2/3 is complete for current execution. Use [cleanup_phase_closed_2026-07-03.md](cleanup_phase_closed_2026-07-03.md) for the compact closure record. Archives are rollback/reference only.\n",
)
current_context.write_text(text, encoding="utf-8")

pointer = ROOT / "docs" / "automation" / "V6_FINAL_PRODUCT_EXECUTION_PLAN" / "next_task_pointer.md"
pointer.write_text('''# V6 Next Task Pointer

Current task: `TASK_CONTENTOPS_V6_IDENTITY_REGISTRY_TO_DISPATCH_OUTCOME_MODEL_V0`

Recommended next task:

```text
TASK_CONTENTOPS_V6_AUDIT_BACKED_DISTRIBUTION_RECORD_TO_FEEDBACK_BACKLOG_V0
```

Purpose: after captured platform publication identities are linked to local-only dispatch outcome/audit inputs, connect audit-backed distribution records and operator/community feedback input to the next content backlog item.

Do not start live writes, browser/CDP probes, Discord webhook/API calls, scheduler/retry wiring, approval ledger writes, outbox execution, credential/env value reads, public URL fetches, scraping, comments, DMs, reactions, or LLM/provider API calls unless explicitly authorized.
''', encoding="utf-8")

status = ROOT / "docs" / "status" / "current_project_status.json"
if status.exists():
    data = json.loads(status.read_text(encoding="utf-8"))
    data["last_updated_by_task"] = "TASK_CONTENTOPS_V6_IDENTITY_REGISTRY_TO_DISPATCH_OUTCOME_MODEL_V0"
    data["current_product_phase"] = "Cleanup phase closed; local-only publication identity to dispatch outcome/audit link added"
    data["current_product_lane"] = "Jim north-star final product build; local-only identity/outcome/audit linkage; live actions locked"
    data["accepted_baseline_summary"] = "Deep cleaning pass 1/2/3 is closed for current execution. The new local-only dispatch outcome identity link converts safe platform publication identity registry records into redacted audit-link readiness objects. It performs no live write, network/API/webhook/provider/browser/CDP/env/credential/session action and does not verify public URLs."
    data["dispatch_live_status"] = "Dispatch/live write remains locked. Identity links are local audit inputs only, not executable outbox entries, dispatch attempts, public URL verification, scheduler/retry, or live actions."
    data["provider_env_credential_status"] = "No provider/API/browser/network/env/credential action is authorized or required for the cleanup closure and identity-to-outcome link task."
    blockers = data.get("active_blockers", [])
    blockers.append("Identity-to-outcome link is local audit readiness only; live dispatch and public URL verification remain disabled unless a future exact approved live task clears all gates.")
    data["active_blockers"] = list(dict.fromkeys(blockers))
    data["latest_accepted_task"] = "TASK_CONTENTOPS_V6_IDENTITY_REGISTRY_TO_DISPATCH_OUTCOME_MODEL_V0"
    data["latest_accepted_task_result"] = "cleanup_closed_and_identity_outcome_link_added"
    data["latest_changed_areas"] = [
        "docs/CURRENT_CONTEXT.md",
        "docs/cleanup_phase_closed_2026-07-03.md",
        "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md",
        "docs/status/current_project_status.json",
        "live_contentops/dispatch_outcome_identity_link_v6.py",
        "tests/test_dispatch_outcome_identity_link_v6.py",
    ]
    data["next_recommended_task"] = "TASK_CONTENTOPS_V6_AUDIT_BACKED_DISTRIBUTION_RECORD_TO_FEEDBACK_BACKLOG_V0: connect audit-backed distribution records and operator/community feedback input to next content backlog; local/read-only first, no live/provider/browser/network/env/credential action."
    status.write_text(json.dumps(data, indent=2), encoding="utf-8")

print("wrote", len(files), "new files and updated context/status/pointer")
