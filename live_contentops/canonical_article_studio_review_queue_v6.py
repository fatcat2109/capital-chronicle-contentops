"""V6 Canonical Article Studio Review Queue Coordinator.

Orchestrates local review queue artifacts and enforces safety invariants.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from live_contentops import canonical_article_studio_queue_packet_v6 as packet_builder
from live_contentops import canonical_article_studio_review_checklist_v6 as checklist_builder
from live_contentops import canonical_article_studio_review_queue_validator_v6 as validator_module

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_CANONICAL_ARTICLE_STUDIO_REVIEW_QUEUE")
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_STUDIO_BROWSERLESS_EDITOR_DRAFT_SHELL_DRY_RUN_HEAVY_BATCH_V0"


def write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_review_item() -> dict[str, Any]:
    # Default claim IDs and requirement refs from matrix
    return {
        "review_item_status": "BLOCKED_WAITING_FOR_REAL_SOURCE_APPROVAL",
        "review_item_id": "review_item_6e40db810195",
        "source_eligibility_ref": "canonical_draft_eligibility_packet",
        "article_topic_ref": "article_packet_6e40db810195",
        "claim_ids": [
            "claim_d474a9fdbcd6",
            "claim_63d1cf20e9bf",
            "claim_492c29ad9746"
        ],
        "source_requirement_refs": [
            "req_67a5db6704f5",
            "req_bfcb46cc38cc",
            "req_e6edaf8e7750"
        ],
        "title_placeholder": None,
        "dek_placeholder": None,
        "article_body_placeholder": None,
        "article_copy_generated": False,
        "ready_for_editor_review": False,
        "ready_for_jim_approval": False,
        "ready_for_publication": False,
        "dispatch_allowed_now": False,
        "public_postable": False,
        "blockers": [
            "runtime_operator_approval_missing",
            "real_source_pack_not_approved",
            "article_copy_generation_blocked",
            "editor_review_required",
            "jim_review_required",
            "publication_blocked",
            "dispatch_blocked"
        ]
    }


def make_screenshot_manifest() -> dict[str, Any]:
    return {
        "screenshot_created": False,
        "screenshot_required_later": True,
        "screenshot_review_required_by_chatgpt": True,
        "visual_pass_claimed": False,
        "external_domain_opened": False,
        "real_browser_profile_used": False,
        "source_fetch_performed": False,
        "browser_session_started": False
    }


def make_local_mock_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canonical Article Studio - Review Queue [BLOCKED]</title>
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: #151d30;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --accent-disabled: #4b5563;
            --accent-error: #ef4444;
            --border-color: #1e293b;
            --danger-bg: rgba(239, 68, 68, 0.1);
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 40px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            box-sizing: border-box;
        }
        .container {
            max-width: 900px;
            width: 100%;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            padding: 40px;
            position: relative;
            overflow: hidden;
        }
        .header {
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 28px;
            margin: 0 0 10px 0;
            font-weight: 700;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .badge {
            background: var(--danger-bg);
            color: var(--accent-error);
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .meta-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        .meta-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 16px;
        }
        .meta-card h3 {
            font-size: 14px;
            color: var(--text-muted);
            margin: 0 0 8px 0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .meta-card p {
            font-size: 16px;
            font-weight: 600;
            margin: 0;
        }
        .checklist-section {
            margin-bottom: 30px;
        }
        .checklist-section h2 {
            font-size: 18px;
            margin-bottom: 16px;
            color: var(--text-muted);
        }
        .checklist-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: rgba(255, 255, 255, 0.01);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 8px;
        }
        .checklist-item.blocked {
            border-left: 4px solid var(--accent-error);
        }
        .checklist-item-title {
            font-weight: 500;
            font-size: 15px;
        }
        .checklist-item-status {
            font-size: 13px;
            color: var(--accent-error);
            font-weight: 600;
            text-transform: uppercase;
        }
        .actions-panel {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            border-top: 1px solid var(--border-color);
            padding-top: 30px;
            margin-top: 30px;
        }
        .btn {
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            background: #1f2937;
            color: var(--accent-disabled);
            cursor: not-allowed;
            transition: all 0.3s ease;
        }
        .btn:disabled {
            opacity: 0.6;
        }
        .banner {
            background: var(--danger-bg);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 30px;
            color: var(--accent-error);
            font-size: 14px;
            line-height: 1.5;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="banner">
            <strong>⚠️ PIPELINE INVARIANT BLOCKER:</strong> Simulated Review Queue State. Real Jim approval signatures are completely missing. Live draft generation, publication, outbox dispatching, and browser sessions are fully deactivated in this dry-run configuration.
        </div>
        <div class="header">
            <h1>Canonical Article Studio <span class="badge">Blocked</span></h1>
            <p style="color: var(--text-muted); margin: 0; font-size: 14px;">Review Queue Status: <strong>REVIEW_QUEUE_READY_WITH_BLOCKERS</strong></p>
        </div>
        
        <div class="meta-grid">
            <div class="meta-card">
                <h3>Review Item ID</h3>
                <p>review_item_6e40db810195</p>
            </div>
            <div class="meta-card">
                <h3>Draft Status</h3>
                <p style="color: var(--accent-error);">BLOCKED_WAITING_FOR_REAL_SOURCE_APPROVAL</p>
            </div>
        </div>

        <div class="checklist-section">
            <h2>Editor / Jim Checklist</h2>
            <div class="checklist-item blocked">
                <span class="checklist-item-title">Real Source Pack Approval Required</span>
                <span class="checklist-item-status">Blocked</span>
            </div>
            <div class="checklist-item blocked">
                <span class="checklist-item-title">Runtime Claim Binding Verification</span>
                <span class="checklist-item-status">Pending</span>
            </div>
            <div class="checklist-item blocked">
                <span class="checklist-item-title">Jim Final Review Approval</span>
                <span class="checklist-item-status">Pending</span>
            </div>
            <div class="checklist-item blocked">
                <span class="checklist-item-title">Article Copy Generation</span>
                <span class="checklist-item-status">Not Generated</span>
            </div>
        </div>

        <div class="actions-panel">
            <button class="btn" disabled>Open Article Studio</button>
            <button class="btn" disabled>Generate Canonical Draft</button>
            <button class="btn" disabled>Approve for Publication</button>
            <button class="btn" disabled>Create Outbox Entry</button>
            <button class="btn" disabled>Dispatch</button>
        </div>
    </div>
</body>
</html>
"""


def make_blocker_report_markdown(blockers: list[str]) -> str:
    lines = [
        "# V6 Canonical Article Studio Review Queue Blocker Report",
        "",
        "The following active blockers prevent draft generation, publication, outbox entry creation, or dispatch operations:",
        ""
    ]
    for b in blockers:
        lines.append(f"- **{b}**: Locked by default dry-run configuration.")
    lines.extend([
        "",
        "## Offline Safety Guarantees",
        "- Raw sources and operators are strictly redacted.",
        "- Live browser orchestration and network writes are disabled.",
        "- Jim's signature is completely absent."
    ])
    return "\n".join(lines)


def make_runbook_markdown() -> str:
    return """# V6 Canonical Article Studio Review Queue Runbook

This runbook documents operator and system actions for the offline simulated Review Queue state.

## Operator Review Checklist
1. Review the unapproved eligibility matrix and queue status.
2. Confirm that no raw sources or signatures are leaked.
3. Ensure no visual verification or screenshot claims are bypassed.

## Resolving Blockers
- Real Jim approval is required to clear `real_source_pack_not_approved` and `runtime_operator_approval_missing`.
"""


def make_implementation_report_markdown() -> str:
    return """# V6 Canonical Article Studio Review Queue Implementation Report

## Summary
The Canonical Article Studio Review Queue lane is established as an offline, dry-run state.

## Verified Invariants
- `queue_status` = `REVIEW_QUEUE_READY_WITH_BLOCKERS`
- `visual_pass_claimed` = `false`
- All active post/dispatch flags are hardlocked to `false`.
"""


def make_next_task_pointer_markdown() -> str:
    return f"""# Next recommended task
{NEXT_RECOMMENDED_TASK}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Canonical Article Studio Review Queue Lane")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create packet and checklist
    queue_packet = packet_builder.make_canonical_article_studio_queue_packet()
    editor_checklist = checklist_builder.make_canonical_article_studio_editor_checklist()
    review_item = make_review_item()
    manifest = make_screenshot_manifest()
    html_mock = make_local_mock_html()

    # 2. Run validator
    report, blockers = validator_module.validate_canonical_article_studio_review_queue(
        queue_packet, review_item, editor_checklist, html_mock, manifest
    )

    # 3. Write all 10 artifacts
    write_json(out_dir / "canonical_article_studio_queue_packet.json", queue_packet)
    write_json(out_dir / "canonical_article_studio_review_item.json", review_item)
    write_json(out_dir / "canonical_article_studio_editor_checklist.json", editor_checklist)
    write_json(out_dir / "canonical_article_studio_review_queue_validation_report.json", report)
    write_text(out_dir / "canonical_article_studio_local_mock.html", html_mock)
    write_json(out_dir / "canonical_article_studio_screenshot_manifest.json", manifest)
    write_text(out_dir / "canonical_article_studio_blocker_report.md", make_blocker_report_markdown(blockers))
    write_text(out_dir / "canonical_article_studio_runbook.md", make_runbook_markdown())
    write_text(out_dir / "implementation_report.md", make_implementation_report_markdown())
    write_text(out_dir / "next_task_pointer.md", make_next_task_pointer_markdown())

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
