"""V6 Discord Community Drop and Operator Review Lane.

Consumes platform variant packets to scaffold unapproved local review docs
and safe placeholder channel bindings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_COMMUNITY_DROP_AND_OPERATOR_REVIEW_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_VARIANT_PACKET = Path("docs/automation/V6_PLATFORM_NATIVE_VARIANTS/platform_variant_packet.json")
DEFAULT_DISCORD_VARIANT_MD = Path("docs/automation/V6_PLATFORM_NATIVE_VARIANTS/discord_variant.md")

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_DISCORD_COMMUNITY_DROP")
DEFAULT_PACKET_OUTPUT = DEFAULT_OUTPUT_DIR / "discord_drop_packet.json"


def path_text(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return str(path).replace("\\", "/")


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generate_preview_markdown(packet: dict[str, Any], variant_body: str) -> str:
    status = packet.get("discord_drop_status", "unknown")
    source_mode = packet.get("source_mode", "unknown")
    missing_source_refs = packet.get("missing_source_refs", [])
    missing_str = ", ".join(f"`{r}`" for r in missing_source_refs) or "None"

    return f"""# Discord Community Drop Preview

> [!IMPORTANT]
> **NO-PUBLICATION WARNING**: This document contains a staged Discord update preview. It is not publish-ready and must not be posted or sent to any Discord webhook.

## Safety & Limitation Note
- **Source Mode**: {source_mode}
- **Staging Status**: {status}
- **Missing Source References**: {missing_str}
- **Approval/Dispatch Blocked Note**: Dispatch of this community drop is strictly blocked because `dispatch_allowed_now` is false.
- **Channel Binding Placeholder Note**: The target announcements channel family is configured as a non-sensitive mockup placeholder. No webhook URLs or authorization tokens are present.

## Discord Preview Scaffold
```
{variant_body.strip()}
```

## Evidence & Verification Reminder
- An exact payload hash verification and destination channel binding match are required.
- Do not approve or dispatch without matching signatures.
"""


def generate_operator_checklist_markdown(packet: dict[str, Any], review_packet: dict[str, Any]) -> str:
    missing_source_refs = packet.get("missing_source_refs", [])
    missing_str = ", ".join(f"`{r}`" for r in missing_source_refs) or "None"
    
    return f"""# Operator Review Checklist

## Staging Status
- **Staging Status**: {packet.get('discord_drop_status')}
- **Review Status**: {review_packet.get('review_status')}

## Verification Checklist

### 1. Evidence Gap Checklist
- [ ] Supply verified reference for missing source references: {missing_str}

### 2. Payload Hash Checklist
- [ ] Generate exact payload hash of the final content.
- [ ] Confirm `exact_payload_hash_present` is updated to true.

### 3. Destination Binding Checklist
- [ ] Confirm active target channel family: `community_announcements_placeholder`
- [ ] Confirm `destination_binding_present` is updated to true.

### 4. Safety & Environment Checks
- [ ] Verify no secrets, credentials, or webhook URLs are present in the files.
- [ ] Verify `webhook_url_present` and `webhook_url_printed` remain false.

### 5. Final Dispatch Lock
- [ ] Verify `dispatch_allowed_now` remains strictly false until all requirements are met.
- [ ] Verify `public_postable` remains strictly false.
"""


def generate_evidence_requirements_markdown(packet: dict[str, Any]) -> str:
    missing_source_refs = packet.get("missing_source_refs", [])
    missing_str = ", ".join(f"`{r}`" for r in missing_source_refs) or "None"

    return f"""# Approval Evidence Requirements

## Staging Requirements

### 1. Required Evidence Before Approval
- Human verification of all underlying technical process metrics.
- Absolute exclusion of price predictions, financial targets, and buy/sell trading signals.

### 2. Source References Required
- Mapped references for: {missing_str}

### 3. Destination Binding Requirements
- Non-sensitive channel family placeholder binding matches must be validated by the local registry layout.

### 4. Exact Payload Hash Requirements
- Verification hash matching final content must be present in the packet.

### 5. Manual Fallback & Safety Note
- **No Live Write Note**: This task is strictly local and read-only. No live writes or API executions to Discord are authorized.
"""


def materialize_drop_packets(
    variant_packet_path: str | Path = DEFAULT_VARIANT_PACKET,
    discord_variant_path: str | Path = DEFAULT_DISCORD_VARIANT_MD
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    try:
        variant_data = load_json(variant_packet_path)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        variant_data = {
            "platform_variant_packet_id": "variants_unreadable_err",
            "source_article_id": None,
            "source_intent_id": None,
            "source_mode": "unknown",
            "variant_status": "BLOCKED_BY_SOURCE_ARTICLE",
            "missing_source_refs": [],
            "source_needed": True,
            "source_evidence_required": True,
            "blocked_reasons": [f"variant_packet_unreadable:{exc.__class__.__name__}"]
        }

    try:
        variant_body = Path(discord_variant_path).read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        variant_body = "## [Discord Variant Body Missing]"

    # Status logic
    variant_status = variant_data.get("variant_status")
    missing_source_refs = list(variant_data.get("missing_source_refs", []))
    source_needed = variant_data.get("source_needed", False)
    source_evidence_required = variant_data.get("source_evidence_required", False)
    blocked_reasons = list(variant_data.get("blocked_reasons", []))

    if variant_status in ["BLOCKED_BY_SOURCE_ARTICLE", "BLOCKED_BY_RESEARCH_GROUNDING", "BLOCKED_BY_SEO_EDITORIAL"] or "variants_unreadable" in str(variant_data.get("platform_variant_packet_id")):
        status = "BLOCKED_BY_PLATFORM_VARIANT"
    elif missing_source_refs or source_needed:
        status = "DISCORD_DROP_REVIEW_READY_WITH_SOURCE_GAP"
    else:
        status = "DISCORD_DROP_REVIEW_READY"

    hasher = hashlib.sha256(f"{variant_data.get('platform_variant_packet_id')}_{status}".encode("utf-8"))
    discord_drop_packet_id = f"discord_drop_{hasher.hexdigest()[:12]}"
    channel_binding_id = f"binding_{hasher.hexdigest()[:8]}"

    # Main drop packet
    drop_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "discord_drop_packet_id": discord_drop_packet_id,
        "source_platform_variant_packet_id": variant_data.get("platform_variant_packet_id"),
        "source_article_id": variant_data.get("source_article_id"),
        "source_intent_id": variant_data.get("source_intent_id"),
        "source_mode": variant_data.get("source_mode", "unknown"),
        "source_variant_status": variant_status,
        "discord_drop_status": status,
        "discord_stage": "community_drop_staging",
        "target_platform": "discord",
        "target_channel_family": "community_announcements_placeholder",
        "channel_binding_status": "PLACEHOLDER_ONLY",
        "channel_binding_id": channel_binding_id,
        "channel_binding_secret_present": False,
        "webhook_url_present": False,
        "webhook_url_printed": False,
        "preview_file": "docs/automation/V6_DISCORD_COMMUNITY_DROP/discord_drop_preview.md",
        "operator_review_packet_file": "docs/automation/V6_DISCORD_COMMUNITY_DROP/operator_review_packet.json",
        "channel_binding_placeholder_file": "docs/automation/V6_DISCORD_COMMUNITY_DROP/channel_binding_placeholder.json",
        "approval_evidence_requirements_file": "docs/automation/V6_DISCORD_COMMUNITY_DROP/approval_evidence_requirements.md",
        "missing_source_refs": missing_source_refs,
        "source_needed": source_needed,
        "source_evidence_required": source_evidence_required,
        "public_postable": False,
        "human_review_required": True,
        "approval_required": True,
        "approval_performed": False,
        "dispatch_allowed_now": False,
        "not_approved": True,
        "not_dispatchable": True,
        "not_public_postable": True,
        "no_live_request_in_this_task": True,
        "no_env_read_in_this_task": True,
        "no_provider_call_in_this_task": True,
        "no_network_call_in_this_task": True,
        "raw_secret_output": False,
        "blocked_reasons": sorted(blocked_reasons),
        "next_recommended_task": "TASK_CONTENTOPS_V6_DISCORD_COMMUNITY_DROP_LANE_V0" if status == "BLOCKED_BY_PLATFORM_VARIANT" else "TASK_CONTENTOPS_V6_SOURCE_EVIDENCE_INTAKE_AND_APPROVAL_PREFLIGHT_HEAVY_BATCH_V0"
    }

    # Operator review packet
    review_packet_id = f"review_packet_{hasher.hexdigest()[:8]}"
    review_packet = {
        "task_label": TASK_LABEL,
        "schema_version": SCHEMA_VERSION,
        "operator_review_packet_id": review_packet_id,
        "source_discord_drop_packet_id": discord_drop_packet_id,
        "review_status": "AWAITING_OPERATOR_EVIDENCE_AND_APPROVAL",
        "exact_payload_hash_required": True,
        "exact_payload_hash_present": False,
        "destination_binding_required": True,
        "destination_binding_present": False,
        "source_evidence_required": source_evidence_required,
        "missing_source_refs": missing_source_refs,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "not_approved": True,
        "not_dispatchable": True,
        "public_postable": False,
        "checklist": [
            "Confirm underlying metrics have been verified by Jim.",
            "Verify that no signal language or financial target framing is present.",
            "Confirm that correct payload hash is calculated and matching."
        ]
    }

    # Channel binding placeholder
    channel_binding = {
        "channel_family": "community_announcements_placeholder",
        "binding_id": channel_binding_id,
        "binding_status": "PLACEHOLDER_ONLY",
        "target_platform": "discord",
        "webhook_url": None,
        "secret_keys_present": False,
        "authorized_roles_allowed": ["V6-Operator", "Admin"],
        "note": "This is a strictly non-sensitive placeholder layout. Real binding and live write authorizations must occur in a later explicit live task."
    }

    return drop_packet, review_packet, channel_binding, variant_body


def implementation_report(packet: dict[str, Any]) -> str:
    blocked_flag = "BLOCKED_FAIL_SAFE" if packet.get("blocked_reasons") else "PASS"
    return f"""# V6 Discord Community Drop

Status: `{blocked_flag}`

- No live request in this task: `true`
- No env read in this task: `true`
- No provider call in this task: `true`
- No network call in this task: `true`
- Discord community drop preview generated: `true`
- Safe placeholder channel bindings generated: `true`
- Fake public-postable content created: `false`

The Discord community announcement and staging pipeline is locked and awaiting factual evidence.
"""


def next_task_pointer(packet: dict[str, Any]) -> str:
    next_task = packet.get("next_recommended_task")
    if packet.get("blocked_reasons"):
        goal = "Resolve operator intent, source evidence, grounding, refinement, or variant block conditions."
    else:
        goal = "Unblock the Discord drop lane once real-content source evidence is supplied."
    return f"""# Next Task Pointer

Recommended next task:

`{next_task}`

Goal: {goal}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Discord Community Drop Lane")
    parser.add_argument("--variant-packet", default=str(DEFAULT_VARIANT_PACKET))
    parser.add_argument("--variant-md", default=str(DEFAULT_DISCORD_VARIANT_MD))
    parser.add_argument("--output-packet", default=str(DEFAULT_PACKET_OUTPUT))
    args = parser.parse_args(argv)

    drop, review, binding, var_body = materialize_drop_packets(args.variant_packet, args.variant_md)
    write_json(args.output_packet, drop)

    out_dir = Path(args.output_packet).parent
    write_json(out_dir / "operator_review_packet.json", review)
    write_json(out_dir / "channel_binding_placeholder.json", binding)

    # Write preview and text documents
    (out_dir / "discord_drop_preview.md").write_text(generate_preview_markdown(drop, var_body), encoding="utf-8")
    (out_dir / "operator_review_checklist.md").write_text(generate_operator_checklist_markdown(drop, review), encoding="utf-8")
    (out_dir / "approval_evidence_requirements.md").write_text(generate_evidence_requirements_markdown(drop), encoding="utf-8")

    # Write report and pointer
    (out_dir / "implementation_report.md").write_text(implementation_report(drop), encoding="utf-8")
    (out_dir / "next_task_pointer.md").write_text(next_task_pointer(drop), encoding="utf-8")

    print(json.dumps({
        "discord_drop_packet_id": drop["discord_drop_packet_id"],
        "discord_drop_status": drop["discord_drop_status"],
        "blocked_reasons": drop["blocked_reasons"]
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
