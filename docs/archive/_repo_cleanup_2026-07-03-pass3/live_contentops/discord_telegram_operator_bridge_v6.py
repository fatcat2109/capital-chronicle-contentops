"""V6 Discord and Telegram Operator Bridge.

Orchestrates redacted status packet creation and operator message preview formatting.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import redacted_operator_status_v6 as redacted_status
from live_contentops import operator_bridge_message_preview_v6 as message_preview
from live_contentops import operator_bridge_capability_matrix_v6 as capability_matrix

TASK_LABEL = "TASK_CONTENTOPS_V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE_AND_REDACTED_STATUS_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_DISCORD_TELEGRAM_OPERATOR_BRIDGE")


def load_json_or_fallback(path_str: str, default_data: dict[str, Any]) -> dict[str, Any]:
    path = Path(path_str)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default_data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Discord Telegram Operator Bridge")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--contract-packet", default="docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/unified_payload_contract_packet.json")
    parser.add_argument("--hash-manifest", default="docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/unified_payload_hash_manifest.json")
    args = parser.parse_args(argv)
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Load upstream data
    contract_data = load_json_or_fallback(args.contract_packet, {})
    hash_data = load_json_or_fallback(args.hash_manifest, {})
    
    # Bundle hashes in contract data for downstream generators
    contract_data["hash_manifest"] = hash_data
    
    # Generate reports
    redacted_report = redacted_status.generate_redacted_status(contract_data)
    
    # Previews
    discord_prev = message_preview.generate_discord_preview(redacted_report)
    telegram_prev = message_preview.generate_telegram_preview(redacted_report)
    
    # Run self-validation checks to detect secrets/executable controls
    blockers = redacted_report.get("blockers", [])
    
    # Check previews content
    for prev in [discord_prev, telegram_prev]:
        prev_blockers = message_preview.validate_preview_content(prev["content_body"])
        for pb in prev_blockers:
            if pb not in blockers:
                blockers.append(pb)
                
    blockers = sorted(list(set(blockers)))
    redacted_report["blockers"] = blockers
    redacted_report["blocker_count"] = len(blockers)
    
    # Capability matrix
    matrix = capability_matrix.generate_capability_matrix()
    
    # Write files
    Path(out_dir / "redacted_status_packet.json").write_text(
        json.dumps(redacted_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    Path(out_dir / "discord_operator_message_preview.json").write_text(
        json.dumps(discord_prev, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    Path(out_dir / "telegram_operator_message_preview.json").write_text(
        json.dumps(telegram_prev, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    Path(out_dir / "operator_bridge_capability_matrix.json").write_text(
        json.dumps(matrix, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # Bridge Packet
    bridge_packet = {
        "operator_bridge_status": "READY_FOR_REVIEW_ONLY_REDACTED_STATUS",
        "discord_status_preview_created": True,
        "telegram_status_preview_created": True,
        "live_discord_webhook_call_performed": False,
        "live_telegram_api_call_performed": False,
        "platform_api_call_performed": False,
        "provider_call_performed": False,
        "env_read_performed": False,
        "credentials_hydrated": False,
        "browser_session_started": False,
        "approval_valid_for_dispatch": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "outbox_entry_created": False,
        "public_postable": False,
        "kill_switch_active": True,
        "human_review_required": True,
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "next_recommended_task": "TASK_CONTENTOPS_V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN_AND_BROWSER_SAFETY_QA_HEAVY_BATCH_V0",
        "blockers": blockers
    }
    
    Path(out_dir / "operator_bridge_packet.json").write_text(
        json.dumps(bridge_packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # Runbook
    Path(out_dir / "operator_bridge_runbook.md").write_text(
        "# Operator Bridge Runbook\n\nRuns bridge and formats review-only status notification previews.\n",
        encoding="utf-8"
    )
    
    # Blocker report
    blocker_str = ", ".join(f"`{b}`" for b in blockers) if blockers else "None"
    Path(out_dir / "operator_bridge_blocker_report.md").write_text(
        f"# Operator Bridge Blocker Report\n\n- **Blockers**: {blocker_str}\n",
        encoding="utf-8"
    )
    
    # Implementation report
    Path(out_dir / "implementation_report.md").write_text(
        f"# Operator Bridge Implementation Report\n\n- **Task Label**: {TASK_LABEL}\n- **Status**: READY_FOR_REVIEW_ONLY_REDACTED_STATUS\n",
        encoding="utf-8"
    )
    
    # Next task pointer
    Path(out_dir / "next_task_pointer.md").write_text(
        f"# Next Task Pointer\n\nRecommended next task:\n\n`{bridge_packet['next_recommended_task']}`\n",
        encoding="utf-8"
    )
    
    print(json.dumps({
        "operator_bridge_status": bridge_packet["operator_bridge_status"],
        "blockers": bridge_packet["blockers"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
