"""V6 Canonical Draft Operator Source Pack Review UI and Approval Coordinator.

Runs the local-only UI mockup and validation suite under the V6 Operating Profile.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import operator_source_pack_approval_checklist_v6 as checklist_builder
from live_contentops import operator_source_pack_review_packet_v6 as packet_builder
from live_contentops import operator_source_pack_review_validator_v6 as validator

TASK_LABEL = "TASK_CONTENTOPS_V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_IMPORT_UI_AND_APPROVAL_REVIEW_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_CANONICAL_DRAFT_OPERATOR_SOURCE_PACK_REVIEW")


def load_json_or_fallback(path: str | Path, default_val: Any) -> Any:
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default_val


def make_local_mock_html(
    checklist: list[dict[str, Any]],
    claim_scaffold: list[dict[str, Any]],
    blockers: list[str]
) -> str:
    """Generates the static, inline-CSS review UI HTML mockup."""
    checklist_rows = []
    for item in checklist:
        checklist_rows.append(f"""
        <tr>
            <td>{item['source_requirement_id']}</td>
            <td>{item['required_source_type']}</td>
            <td>{item['current_status']}</td>
            <td>{", ".join(item.get("bound_claim_ids", []))}</td>
        </tr>
        """)
    checklist_tbody = "\n".join(checklist_rows)

    claims_rows = []
    for c in claim_scaffold:
        claims_rows.append(f"""
        <li>
            <strong>[Claim {c.get('claim_id')}]</strong>: {c.get('claim_text_draft')} 
            (Refs: {", ".join(c.get('source_requirement_refs', []))})
        </li>
        """)
    claims_ul = "\n".join(claims_rows)

    blockers_rows = []
    for b in blockers:
        blockers_rows.append(f"<li><code>{b}</code></li>")
    blockers_ul = "\n".join(blockers_rows)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Operator Source Pack Review UI</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0d1117;
            color: #c9d1d9;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 24px;
        }}
        .banner {{
            background-color: #8b1c1c;
            color: #ffffff;
            padding: 12px;
            border-radius: 4px;
            text-align: center;
            font-weight: bold;
            margin-bottom: 20px;
        }}
        .notice {{
            background-color: #382c0c;
            border-left: 4px solid #d29922;
            padding: 12px;
            margin-bottom: 20px;
            border-radius: 0 4px 4px 0;
        }}
        h1, h2, h3 {{
            color: #f0f6fc;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            text-align: left;
            padding: 8px;
            border: 1px solid #30363d;
        }}
        th {{
            background-color: #21262d;
        }}
        .btn {{
            display: inline-block;
            background-color: #21262d;
            color: #8b949e;
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: bold;
            border: 1px solid #30363d;
            cursor: not-allowed;
            margin-right: 10px;
        }}
        .disabled-info {{
            color: #f85149;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        .blockers-panel {{
            background-color: #21262d;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="banner">
            TEST-ONLY / NOT RUNTIME TRUTH
        </div>

        <h1>Operator Source Pack Review UI</h1>
        
        <div class="notice">
            <strong>V6 operating profile alert</strong>: Positive-path logic has been proven in unit-test dry-runs,
            but real runtime source verification and operator signatures are still missing.
        </div>

        <div class="blockers-panel">
            <h2>Active Blockers</h2>
            <ul>
                {blockers_ul}
            </ul>
        </div>

        <h2>Required Evidence Checklist</h2>
        <table>
            <thead>
                <tr>
                    <th>Requirement ID</th>
                    <th>Source Type</th>
                    <th>Status</th>
                    <th>Bound Claims</th>
                </tr>
            </thead>
            <tbody>
                {checklist_tbody}
            </tbody>
        </table>

        <h2>Claim Ledger Scaffolding</h2>
        <ul>
            {claims_ul}
        </ul>

        <h2>Approval Action Panel</h2>
        <div>
            <span class="btn">Import Real Source Pack Manually</span>
            <span class="btn">Operator Signature Required</span>
            <span class="btn">Draft Generation Blocked</span>
            <span class="btn">Publication Blocked</span>
            <p class="disabled-info">All buttons are disabled: Operator signature must be submitted to the CLI validator to unblock.</p>
        </div>
    </div>
</body>
</html>
"""
    return html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Canonical Draft Operator Source Pack Review Coordinator")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load scaffolds
    research_checklist = load_json_or_fallback(
        "docs/automation/V6_SOURCE_PACK_VERIFICATION_UI/operator_research_checklist.json",
        []
    )
    claim_scaffold = load_json_or_fallback(
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_claim_ledger_scaffold.json",
        []
    )

    # 2. Build packets and templates
    review_packet = packet_builder.make_operator_source_pack_review_packet()
    checklist = checklist_builder.make_review_checklist(research_checklist, claim_scaffold)
    approval_template = checklist_builder.make_operator_approval_template()

    # 3. Create mock HTML
    # We must validate first to gather blockers
    # We can pass a dummy html_content first, then build the actual html content and re-validate
    dummy_html = "<html></html>"
    _, initial_blockers = validator.validate_operator_source_pack_review(
        review_packet, checklist, approval_template, dummy_html
    )

    mock_html = make_local_mock_html(checklist, claim_scaffold, initial_blockers)

    # Re-run validation with the actual mock HTML
    validation_report, blockers = validator.validate_operator_source_pack_review(
        review_packet, checklist, approval_template, mock_html
    )

    # 4. Screenshot manifest (always false for mock/offline UI)
    screenshot_manifest = {
        "screenshot_created": False,
        "screenshot_required_later": True,
        "screenshot_review_required_by_chatgpt": True,
        "visual_pass_claimed": False,
        "external_domain_opened": False,
        "real_browser_profile_used": False,
        "source_fetch_performed": False
    }

    # 5. Write JSON files
    artifacts = {
        "operator_source_pack_review_packet.json": review_packet,
        "operator_source_pack_review_checklist.json": checklist,
        "operator_source_pack_approval_template.json": approval_template,
        "operator_source_pack_review_validation_report.json": validation_report,
        "operator_source_pack_review_screenshot_manifest.json": screenshot_manifest
    }

    for name, data in artifacts.items():
        Path(out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    # 6. Write HTML file
    Path(out_dir / "operator_source_pack_review_local_mock.html").write_text(mock_html, encoding="utf-8")

    # 7. Write Markdown files
    # Blocker report
    blocker_bullets = "\n".join(f"- `{b}`" for b in blockers)
    blocker_md = f"""# Operator Source Pack Review Blocker Report

- **Task Label**: {TASK_LABEL}
- **Active Blockers Count**: {len(blockers)}

## Active Blockers
{blocker_bullets}
"""
    Path(out_dir / "operator_source_pack_review_blocker_report.md").write_text(blocker_md, encoding="utf-8")

    # Runbook
    runbook_md = """# Operator Source Pack Review Runbook

This guide describes how to review and approve manual source pack submissions.

## Instructions
1. Load `operator_source_pack_review_local_mock.html` locally.
2. Confirm the unverified research checkpoints.
3. Once facts are confirmed, run the next approval signature step.
"""
    Path(out_dir / "operator_source_pack_review_runbook.md").write_text(runbook_md, encoding="utf-8")

    # Implementation report
    impl_md = f"""# Operator Review UI Implementation Report

- **Task Label**: {TASK_LABEL}
- **Safety posture**: offline review mockups staged; all publication/dispatch gates remain BLOCKED.
"""
    Path(out_dir / "implementation_report.md").write_text(impl_md, encoding="utf-8")

    # Next task pointer
    next_task_pointer_md = """# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_REAL_SOURCE_PACK_MANUAL_IMPORT_FIXTURE_SCHEMA_AND_HASH_REVIEW_DRY_RUN_HEAVY_BATCH_V0`
"""
    Path(out_dir / "next_task_pointer.md").write_text(next_task_pointer_md, encoding="utf-8")

    print(json.dumps({
        "review_status": review_packet["review_status"],
        "blockers": blockers
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
