"""V6 Canonical Article Studio Editor Shell Coordinator.

Orchestrates empty draft shell artifacts and enforces safety invariants.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from live_contentops import canonical_article_studio_draft_shell_packet_v6 as packet_builder
from live_contentops import canonical_article_studio_draft_slot_schema_v6 as schema_builder
from live_contentops import canonical_article_studio_editor_shell_validator_v6 as validator_module

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_CANONICAL_ARTICLE_STUDIO_EDITOR_DRAFT_SHELL")
NEXT_RECOMMENDED_TASK = "TASK_CONTENTOPS_V6_CANONICAL_ARTICLE_STUDIO_APPROVED_DRAFT_PLACEHOLDER_BINDING_DRY_RUN_HEAVY_BATCH_V0"


def write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_editor_shell_checklist() -> dict[str, Any]:
    return {
        "checklist_status": "EDITOR_SHELL_BLOCKED_PENDING_SOURCE_APPROVAL",
        "items": [
            {
                "item_id": "source_approval_required",
                "current_status": "blocked",
                "blocks_generation": True,
                "blocks_publication": True,
                "evidence_ref": "source_pack_operator_approval_gate_packet.json"
            },
            {
                "item_id": "source_binding_required",
                "current_status": "pending",
                "blocks_generation": True,
                "blocks_publication": True,
                "evidence_ref": "canonical_draft_claim_eligibility_matrix.json"
            },
            {
                "item_id": "title_generation_blocked",
                "current_status": "blocked",
                "blocks_generation": True,
                "blocks_publication": True,
                "evidence_ref": "canonical_article_studio_queue_packet.json"
            },
            {
                "item_id": "article_body_generation_blocked",
                "current_status": "blocked",
                "blocks_generation": True,
                "blocks_publication": True,
                "evidence_ref": "canonical_article_studio_queue_packet.json"
            },
            {
                "item_id": "citation_generation_blocked",
                "current_status": "blocked",
                "blocks_generation": True,
                "blocks_publication": True,
                "evidence_ref": "canonical_article_studio_queue_packet.json"
            },
            {
                "item_id": "seo_generation_blocked",
                "current_status": "blocked",
                "blocks_generation": True,
                "blocks_publication": True,
                "evidence_ref": "canonical_article_studio_queue_packet.json"
            },
            {
                "item_id": "financial_advice_scan_required",
                "current_status": "pending",
                "blocks_generation": False,
                "blocks_publication": True,
                "evidence_ref": "canonical_article_studio_editor_shell_validation_report.json"
            },
            {
                "item_id": "jim_final_review_required",
                "current_status": "pending",
                "blocks_generation": False,
                "blocks_publication": True,
                "evidence_ref": "source_pack_operator_approval_gate_packet.json"
            },
            {
                "item_id": "publication_blocked",
                "current_status": "blocked",
                "blocks_generation": False,
                "blocks_publication": True,
                "evidence_ref": "canonical_article_studio_draft_shell_packet.json"
            },
            {
                "item_id": "dispatch_blocked",
                "current_status": "blocked",
                "blocks_generation": False,
                "blocks_publication": True,
                "evidence_ref": "canonical_article_studio_draft_shell_packet.json"
            }
        ]
    }


def make_draft_shell_instance() -> dict[str, Any]:
    slots = schema_builder.make_canonical_article_studio_draft_slot_schema()
    return {
        "shell_instance_status": "EMPTY_DRAFT_SHELL_BLOCKED",
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
        "slots": slots,
        "article_copy_generated": False,
        "body_word_count": 0,
        "source_citation_count": 0,
        "evidence_excerpt_count": 0,
        "seo_metadata_generated": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "blockers": [
            "real_source_pack_not_approved",
            "runtime_operator_approval_missing",
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
    <title>Canonical Article Studio - Editor Draft Shell [BLOCKED]</title>
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
            max-width: 950px;
            width: 100%;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            padding: 40px;
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
        .header {
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 28px;
            margin: 0 0 10px 0;
            font-weight: 700;
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
        .slot-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
            margin-bottom: 30px;
        }
        .slot-card {
            background: rgba(255, 255, 255, 0.01);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
        }
        .slot-card h3 {
            font-size: 14px;
            color: var(--text-muted);
            margin: 0 0 8px 0;
            text-transform: uppercase;
        }
        .slot-card p {
            font-size: 15px;
            color: var(--accent-disabled);
            font-style: italic;
            margin: 0;
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
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="banner">
            <strong>⚠️ PIPELINE INVARIANT BLOCKER:</strong> Simulated Editor Draft Shell State. Real Jim approval signatures are completely missing. Live draft generation, publication, outbox dispatching, and browser sessions are fully deactivated in this dry-run configuration.
        </div>
        <div class="header">
            <h1>Canonical Article Studio - Editor Draft Shell <span class="badge">Blocked</span></h1>
            <p style="color: var(--text-muted); margin: 0; font-size: 14px;">Shell Status: <strong>BROWSERLESS_EDITOR_SHELL_READY_WITH_BLOCKERS</strong></p>
        </div>

        <div class="slot-grid">
            <div class="slot-card">
                <h3>Title Slot</h3>
                <p>NULL - Blocked waiting for source approval</p>
            </div>
            <div class="slot-card">
                <h3>Dek Slot</h3>
                <p>NULL - Blocked waiting for source approval</p>
            </div>
            <div class="slot-card">
                <h3>Thesis Slot</h3>
                <p>NULL - Blocked waiting for source approval</p>
            </div>
            <div class="slot-card">
                <h3>Claim Summary Slot</h3>
                <p>NULL - Blocked waiting for source approval</p>
            </div>
            <div class="slot-card">
                <h3>Evidence Placeholder</h3>
                <p>NULL - Blocked waiting for source approval</p>
            </div>
            <div class="slot-card">
                <h3>Conclusion Slot</h3>
                <p>NULL - Blocked waiting for source approval</p>
            </div>
        </div>

        <div class="actions-panel">
            <button class="btn" disabled>Generate Title</button>
            <button class="btn" disabled>Generate Draft Body</button>
            <button class="btn" disabled>Generate Citations</button>
            <button class="btn" disabled>Generate SEO Metadata</button>
            <button class="btn" disabled>Send to Review</button>
            <button class="btn" disabled>Create Outbox Entry</button>
            <button class="btn" disabled>Dispatch</button>
        </div>
    </div>
</body>
</html>
"""


def make_blocker_report_markdown(blockers: list[str]) -> str:
    lines = [
        "# V6 Canonical Article Studio Editor Draft Shell Blocker Report",
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
    return """# V6 Canonical Article Studio Editor Draft Shell Runbook

This runbook documents operator and system actions for the offline simulated Editor Draft Shell state.

## Operator Review Checklist
1. Confirm that all editor shell slots remain unpopulated (null).
2. Verify that no raw sources or signatures are leaked.
3. Confirm that all active dispatch, publication, and outbox flags are locked to false.

## Resolving Blockers
- Real Jim approval is required to clear `real_source_pack_not_approved` and `runtime_operator_approval_missing`.
"""


def make_implementation_report_markdown() -> str:
    return """# V6 Canonical Article Studio Editor Draft Shell Implementation Report

## Summary
The Canonical Article Studio Editor Draft Shell lane is established as an offline, dry-run state.

## Verified Invariants
- `shell_status` = `BROWSERLESS_EDITOR_SHELL_READY_WITH_BLOCKERS`
- `visual_pass_claimed` = `false`
- All active post/dispatch flags are hardlocked to `false`.
"""


def make_next_task_pointer_markdown() -> str:
    return f"""# Next recommended task
{NEXT_RECOMMENDED_TASK}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Canonical Article Studio Editor Draft Shell Lane")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create packet, slots, checklists, instance, HTML, manifest
    shell_packet = packet_builder.make_canonical_article_studio_draft_shell_packet()
    slot_schema = schema_builder.make_canonical_article_studio_draft_slot_schema()
    shell_instance = make_draft_shell_instance()
    editor_checklist = make_editor_shell_checklist()
    html_mock = make_local_mock_html()
    manifest = make_screenshot_manifest()

    # 2. Run validator
    report, blockers = validator_module.validate_canonical_article_studio_editor_shell(
        shell_packet, slot_schema, shell_instance, editor_checklist, html_mock, manifest
    )

    # 3. Write all 11 artifacts
    write_json(out_dir / "canonical_article_studio_draft_shell_packet.json", shell_packet)
    write_json(out_dir / "canonical_article_studio_draft_slot_schema.json", slot_schema)
    write_json(out_dir / "canonical_article_studio_draft_shell_instance.json", shell_instance)
    write_json(out_dir / "canonical_article_studio_editor_shell_checklist.json", editor_checklist)
    write_json(out_dir / "canonical_article_studio_editor_shell_validation_report.json", report)
    write_text(out_dir / "canonical_article_studio_editor_shell_local_mock.html", html_mock)
    write_json(out_dir / "canonical_article_studio_editor_shell_screenshot_manifest.json", manifest)
    write_text(out_dir / "canonical_article_studio_editor_shell_blocker_report.md", make_blocker_report_markdown(blockers))
    write_text(out_dir / "canonical_article_studio_editor_shell_runbook.md", make_runbook_markdown())
    write_text(out_dir / "implementation_report.md", make_implementation_report_markdown())
    write_text(out_dir / "next_task_pointer.md", make_next_task_pointer_markdown())

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
