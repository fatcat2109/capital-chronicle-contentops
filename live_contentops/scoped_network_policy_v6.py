"""V6 Scoped Network Policy Governance.

Defines the action classes, allows passive static resource classification,
maintains the network resource allowlist, and scans UI code for unpermitted connections.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_NETWORK_SCOPE_POLICY_REFRESH_AND_INTAKE_STUDIO_RECLASSIFICATION_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_NETWORK_SCOPE_POLICY")
UI_DIR = Path("ui/operator_evidence_intake_studio")

ACTION_CLASSES = [
    "passive_static_resource",
    "active_read_api",
    "provider_generation_api",
    "browser_cdp_readonly",
    "browser_cdp_supervised_write",
    "platform_api_supervised_write",
    "live_dispatch_write",
    "credential_presence_check",
    "credential_hydration",
    "forbidden_session_or_secret_extraction"
]

ALLOWLIST = [
    {
        "resource_family": "google_fonts",
        "domains": ["fonts.googleapis.com", "fonts.gstatic.com"],
        "purpose": "passive typography/cosmetic UI only",
        "action_class": "passive_static_resource",
        "credentials_required": False,
        "cookies_or_storage_access": False,
        "provider_api": False,
        "platform_api": False,
        "live_write": False,
        "dispatch_related": False,
        "audit_required": True,
        "fallback": "system font stack if offline"
    }
]


def write_json(path: str | Path, data: Any) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def generate_policy_markdown() -> str:
    return """# V6 Scoped Network Policy Governance

This document codifies the ContentOps network policy. Under V6, the absolute ban on remote networking is replaced with a scoped network policy.

## 1. Action Class Matrix
The following action classes partition the repository's network capabilities:
1. `passive_static_resource`: Passive assets (fonts, icons, stylesheets) loaded client-side with no state tracking.
2. `active_read_api`: Read-only queries to external public databases.
3. `provider_generation_api`: Requests to generative models.
4. `browser_cdp_readonly`: Headless browser reads and DOM checks.
5. `browser_cdp_supervised_write`: Supervised browser action sequences.
6. `platform_api_supervised_write`: Supervised platform writes (Substack, Discord).
7. `live_dispatch_write`: Direct production publication.
8. `credential_presence_check`: Checks for local token structure without reading values.
9. `credential_hydration`: Injecting tokens securely.
10. `forbidden_session_or_secret_extraction`: Unauthorized extraction of secrets (Strict Ban).

## 2. Permitted Passive Resource Rules
Passive static resources are allowed only if:
- No credentials are required.
- No cookies, localStorage, or sessionStorage are read or written.
- No auth headers are passed.
- No user accounts are bound.
- No analytics or tracking pixels are included.
- No remote executable scripts are loaded.
- No platform writes are made.
- No user data is exfiltrated.
- The domain and purpose are explicitly documented in `network_resource_allowlist.json`.

## 3. Allowed Domain Details
- **Resource**: Google Fonts
  - **Domains**: `fonts.googleapis.com`, `fonts.gstatic.com`
  - **Purpose**: Cosmetic typography only.
  - **Fallback**: System font stack (offline-ready).
"""


def generate_implementation_report(status: str) -> str:
    return f"""# V6 Scoped Network Policy Implementation Report

- **Task Label**: {TASK_LABEL}
- **Policy Compliance Status**: {status}

- **Compliance Rules**:
  - No secret keys output: `true`
  - No webhook URLs or tokens printed: `true`
  - No live request in this task: `true`
  - No env read in this task: `true`
  - No network call in this task: `true`
  - No provider call in this task: `true`
"""


def generate_next_task_pointer() -> str:
    return """# Next Task Pointer

Recommended next task at time of bundle generation (not permanent authority):

`TASK_CONTENTOPS_V6_MANUAL_EVIDENCE_FIXTURE_VALIDATOR_AND_SOURCE_SUBMISSION_REFRESH_HEAVY_BATCH_V0`

Goal: Validate the operator facts and manual evidence fixture once Jim has populated the template values.
"""


def scan_ui_files(ui_dir: Path) -> list[str]:
    violations = []
    if not ui_dir.exists():
        return violations

    url_regex = re.compile(r'https?://[^\s"\'>]+')
    allowed_domains = set()
    for entry in ALLOWLIST:
        allowed_domains.update(entry["domains"])

    for path in ui_dir.rglob("*"):
        if path.is_file() and path.suffix in [".html", ".js", ".css"]:
            try:
                content = path.read_text(encoding="utf-8")
                # Strip comments to prevent false alarms in source comments
                content_clean = re.sub(r'(?<!:)//.*|/\*[\s\S]*?\*/|<!--[\s\S]*?-->', '', content)
                urls = url_regex.findall(content_clean)
                for url in urls:
                    # Parse domain
                    match = re.match(r'https?://([^/]+)', url)
                    if match:
                        domain = match.group(1)
                        # Check if matches allowed domains or is standard w3 namespace
                        if domain != "www.w3.org" and domain not in allowed_domains:
                            violations.append(f"File '{path.name}' references unauthorized external domain: '{domain}' (URL: {url})")
            except Exception as e:
                violations.append(f"Failed to read file '{path.name}': {e}")
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Scoped Network Policy Governance")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--ui-dir", default=str(UI_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ui_dir_path = Path(args.ui_dir)

    violations = scan_ui_files(ui_dir_path)
    if violations:
        status = "POLICY_VIOLATION_UNAUTHORIZED_DOMAINS"
    else:
        status = "POLICY_COMPLIANCE_SUCCESS"

    # 1. Allowlist JSON
    write_json(out_dir / "network_resource_allowlist.json", ALLOWLIST)

    # 2. Policy Packet JSON
    hasher = hashlib.sha256(f"{status}".encode("utf-8"))
    policy_packet_id = f"policy_{hasher.hexdigest()[:12]}"
    policy_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "policy_packet_id": policy_packet_id,
        "policy_compliance_status": status,
        "action_classes": ACTION_CLASSES,
        "violations": violations,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "kill_switch_active": True
    }
    write_json(out_dir / "network_scope_policy_packet.json", policy_packet)

    # 3. Policy MD
    (out_dir / "scoped_network_policy_v6.md").write_text(generate_policy_markdown(), encoding="utf-8")

    # 4. Report & Pointer
    (out_dir / "implementation_report.md").write_text(generate_implementation_report(status), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(generate_next_task_pointer(), encoding="utf-8")

    print(json.dumps({
        "policy_packet_id": policy_packet_id,
        "policy_compliance_status": status,
        "violations_found": len(violations)
    }))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
