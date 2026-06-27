"""V6 Platform Adapter Selection Policy and CDP Preference Layer.

Codifies adapter selection rules, preferring official APIs when free and practical,
and supervised browser/CDP/manual fallback otherwise, enforcing strict governance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_PLATFORM_ADAPTER_SELECTION_POLICY_AND_CDP_PREFERENCE_REFRESH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_PLATFORM_ADAPTER_SELECTION_POLICY")

PLATFORM_ADAPTER_PREFERENCES = [
    {
        "platform": "Discord webhooks",
        "has_free_practical_api": True,
        "api_restrictions": [],
        "preferred_adapter": "webhook_adapter",
        "rationale": "Free and practical webhook API for community channel delivery."
    },
    {
        "platform": "Telegram channel",
        "has_free_practical_api": True,
        "api_restrictions": [],
        "preferred_adapter": "official_api_adapter",
        "rationale": "Free and highly practical official broadcast API."
    },
    {
        "platform": "Substack publication",
        "has_free_practical_api": False,
        "api_restrictions": ["unavailable", "no_free_publishing_api"],
        "preferred_adapter": "supervised_browser_cdp_adapter",
        "rationale": "No public free publishing API is provided. Supervised browser CDP is the preferred lane."
    },
    {
        "platform": "X (Twitter)",
        "has_free_practical_api": False,
        "api_restrictions": ["paid", "quota_gated"],
        "preferred_adapter": "manual_fallback_adapter",
        "rationale": "Official API is paid and quota-gated. Prefer manual or supervised fallback."
    },
    {
        "platform": "Meta Graph / Facebook Page",
        "has_free_practical_api": False,
        "api_restrictions": ["review_heavy", "restricted"],
        "preferred_adapter": "supervised_browser_cdp_adapter",
        "rationale": "Official API requires high-friction app review. Prefer supervised browser automation."
    },
    {
        "platform": "LinkedIn organization",
        "has_free_practical_api": False,
        "api_restrictions": ["review_heavy", "restricted"],
        "preferred_adapter": "supervised_browser_cdp_adapter",
        "rationale": "Official API is heavily review-gated. Prefer supervised browser automation."
    }
]


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_preferred_adapter(has_free_api: bool, api_restrictions: list[str]) -> str:
    if has_free_api and not any(r in api_restrictions for r in ["paid", "review_heavy", "restricted", "unstable", "unavailable"]):
        return "official_api_adapter"
    if "manual_only" in api_restrictions:
        return "manual_fallback_adapter"
    return "supervised_browser_cdp_adapter"


def generate_policy_markdown() -> str:
    return """# Platform Adapter Selection Policy

This document establishes repo-wide policies for choosing between official APIs, supervised browser/CDP automation, and manual fallbacks.

## Selection Core Preference Rule
> Except for social platforms that provide a practical free official API for direct post/edit/comment workflows, prefer supervised browser/CDP adapters for paid-API platforms, overly restrictive platforms, high-friction app-review platforms, or platforms where official API automation is not worth the cost/complexity.

## CDP/Browser Governance & Strict Safeguards
CDP (Chrome DevTools Protocol) and browser automation must remain strictly supervised:
* **Cannot Bypass Checkpoints**:
  * Exact Preview
  * Payload Hash Verification
  * Destination Channel Binding
  * Jim's Approval Signature
  * Outbox Revalidation
  * Redacted Audit Logging
  * Idempotency Checks
  * Kill Switch Locks
  * Manual Fallback Routing
* **Strict Prohibitions**:
  * Selfbot behavior
  * Hidden posting or stealth activity
  * Direct Messaging (DMs)
  * Scraping third-party users/content
  * Automatic account switching
  * Cookie / localStorage / sessionStorage extraction
  * Raw token persistence in code/logs
  * Approval gate bypass
"""


def generate_next_task_pointer() -> str:
    return """# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0`

Goal: Proceed with the manual evidence fixture validator and source submission refresh.
"""


def generate_implementation_report() -> str:
    return f"""# V6 Platform Adapter Selection Policy Implementation Report

- **Task Label**: {TASK_LABEL}
- **Status**: PASS

- **Compliance Rules**:
  - No secret output: `true`
  - No webhook URLs or tokens printed: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
  - No browser/CDP session launched: `true`
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Platform Adapter Selection Policy")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write selection matrix
    write_json(out_dir / "adapter_selection_matrix.json", PLATFORM_ADAPTER_PREFERENCES)

    # Write policy packet
    packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "policy_name": "V6 Platform Adapter Selection Policy",
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "cdp_governance_rules": {
          "bypass_forbidden_checkpoints": [
            "exact_preview",
            "payload_hash",
            "destination_binding",
            "jim_approval",
            "outbox_revalidation",
            "redacted_audit",
            "idempotency",
            "kill_switch",
            "manual_fallback"
          ],
          "prohibited_actions": [
            "selfbot_behavior",
            "hidden_posting",
            "dms",
            "scraping",
            "account_switching",
            "cookie_extraction",
            "localstorage_extraction",
            "sessionstorage_extraction",
            "token_extraction",
            "raw_token_persistence",
            "approval_bypass"
          ]
        },
        "raw_secret_output": False,
        "webhook_url_printed": False
    }
    write_json(out_dir / "platform_adapter_selection_policy_packet.json", packet)

    # Write text markdown policies
    (out_dir / "platform_adapter_selection_policy.md").write_text(generate_policy_markdown(), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(), encoding="utf-8")
    (out_dir / "implementation_report.md").write_text(generate_implementation_report(), encoding="utf-8")

    print(json.dumps({
        "policy_name": packet["policy_name"],
        "dispatch_allowed_now": packet["dispatch_allowed_now"],
        "live_write_allowed_now": packet["live_write_allowed_now"]
    }))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
