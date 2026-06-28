"""V6 Source Pack Verification UI Coordinator.

Main coordinator assembling verification checklists, entry templates, draft packages, static HTML mock workflows, and validation reports.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import operator_research_checklist_v6 as checklist_module
from live_contentops import source_evidence_entry_template_v6 as template_module
from live_contentops import source_pack_draft_validator_v6 as validator_module
from live_contentops import source_pack_verification_runbook_v6 as runbook_module

TASK_LABEL = "TASK_CONTENTOPS_V6_SOURCE_PACK_VERIFICATION_UI_AND_OPERATOR_RESEARCH_CHECKLIST_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_SOURCE_PACK_VERIFICATION_UI")


def load_json_or_fallback(path: str | Path, default_val: Any) -> Any:
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default_val


def render_static_html(
    title: str,
    checklist: list[dict[str, Any]],
    blockers: list[str]
) -> str:
    """Renders the static, local-only UI HTML dashboard."""
    blocker_li = "".join(f"<li><code>{b}</code></li>" for b in blockers)

    checklist_tr = []
    for item in checklist:
        checklist_tr.append(f"""
        <tr>
            <td>{item['source_requirement_id']}</td>
            <td>{item['required_source_type']}</td>
            <td>{item['source_name_placeholder']}</td>
            <td>{item['research_question']}</td>
            <td><span class="badge missing">missing</span></td>
        </tr>
        """)
    checklist_rows = "\n".join(checklist_tr)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Source Pack Verification Operator Control Tower</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0d1117;
            color: #c9d1d9;
            margin: 40px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #161b22;
            padding: 30px;
            border-radius: 8px;
            border: 1px solid #30363d;
        }}
        h1 {{
            color: #58a6ff;
            border-bottom: 1px solid #21262d;
            padding-bottom: 10px;
        }}
        .banner {{
            background-color: rgba(240, 135, 0, 0.15);
            border: 1px solid #f08700;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            color: #f08700;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #30363d;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #21262d;
            color: #f0f6fc;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .badge.missing {{
            background-color: #da3637;
            color: #f0f6fc;
        }}
        .button {{
            display: inline-block;
            background-color: #21262d;
            color: #8b949e;
            padding: 10px 20px;
            border-radius: 6px;
            text-decoration: none;
            cursor: not-allowed;
            border: 1px solid #30363d;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="banner">
            <strong>OFFLINE CONTROL TOWER: REVIEW-ONLY PREVIEW</strong>
        </div>
        <h1>Source Pack Verification Desk</h1>
        <p><strong>Planning Target</strong>: {title}</p>

        <h3>Compliance Blockers</h3>
        <ul>
            {blocker_li}
        </ul>

        <h3>Research Checklist</h3>
        <table>
            <thead>
                <tr>
                    <th>Requirement ID</th>
                    <th>Category</th>
                    <th>Target Source</th>
                    <th>Research Objective</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {checklist_rows}
            </tbody>
        </table>

        <h3>Manual Verification Desk</h3>
        <p>Interactive verification entry is disabled. Please prepare files manually using the template.</p>
        <a href="#" class="button">Manual Entry Required</a>
        <a href="#" class="button">Source Verification Missing</a>
        <a href="#" class="button">Draft Generation Blocked</a>
    </div>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Source Pack Verification Coordinator")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load outstanding planning inputs
    packet = load_json_or_fallback(
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/next_canonical_article_packet.json",
        {}
    )
    requirements = load_json_or_fallback(
        "docs/automation/V6_NEXT_CANONICAL_ARTICLE_FROM_BACKLOG/article_research_requirements.json",
        []
    )

    # 2. Assemble verification UI packet
    ui_packet = {
        "source_pack_verification_ui_status": "READY_FOR_REVIEW_ONLY_OPERATOR_RESEARCH",
        "real_source_fetch_performed": False,
        "browser_session_started": False,
        "env_read_performed": False,
        "provider_call_performed": False,
        "credentials_hydrated": False,
        "source_pack_verified": False,
        "source_pack_complete": False,
        "draft_generation_allowed": False,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "human_review_required": True,
        "source_verification_required": True,
        "kill_switch_active": True
    }

    # 3. Generate checklist
    checklist_data = checklist_module.generate_operator_research_checklist(requirements)

    # 4. Generate entry templates
    blank_entries = []
    entry_templates = {}
    for r in requirements:
        req_id = r["research_requirement_id"]
        source_type = r["required_source_type"]
        entry = template_module.generate_source_evidence_entry_template(req_id, source_type)
        blank_entries.append(entry)
        entry_templates[req_id] = entry

    # 5. Generate source pack draft template
    draft_template = {
        "source_pack_draft_status": "OPERATOR_INPUT_REQUIRED",
        "source_pack_complete": False,
        "all_required_sources_verified": False,
        "all_claims_bound_to_sources": False,
        "verified_source_pack_status": "MISSING_REQUIRED_SOURCE_VERIFICATION",
        "source_entries": blank_entries,
        "source_claim_binding_pending": True,
        "allowed_for_article_use": False,
        "draft_generation_allowed": False,
        "human_review_required": True
    }

    # 6. Run compliance validator
    validation_report, all_blockers = validator_module.validate_source_pack_draft(draft_template)

    draft_template["blockers"] = all_blockers

    # 7. Render local html tower
    title = packet.get("title_candidate", "Macroeconomic Providence Study")
    static_html = render_static_html(title, checklist_data, all_blockers)
    Path(out_dir / "source_pack_verification_local_mock.html").write_text(static_html, encoding="utf-8")

    # 8. Write remaining JSON artifacts
    artifacts = {
        "source_pack_verification_ui_packet.json": ui_packet,
        "operator_research_checklist.json": checklist_data,
        "source_evidence_entry_template.json": entry_templates,
        "source_pack_draft_template.json": draft_template,
        "source_pack_draft_validation_report.json": validation_report
    }

    for name, data in artifacts.items():
        Path(out_dir / name).write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )

    # Write screenshot manifest
    screenshot_manifest = {
        "screenshot_created": False,
        "screenshot_required_later": True,
        "target": "local_mock_only",
        "real_browser_profile_used": False,
        "external_domain_opened": False,
        "source_fetch_performed": False,
        "screenshot_review_required_by_chatgpt": True
    }
    Path(out_dir / "source_pack_ui_screenshot_manifest.json").write_text(
        json.dumps(screenshot_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )

    # 9. Write Markdown guides
    # blocker report
    blockers_bullets = "\n".join(f"- `{b}`" for b in all_blockers)
    blocker_md = f"""# Source Pack Verification Blocker Report

- **Task Label**: {TASK_LABEL}
- **Blocker Count**: {len(all_blockers)}

## Active Blockers
{blockers_bullets}
"""
    Path(out_dir / "source_pack_verification_blocker_report.md").write_text(blocker_md, encoding="utf-8")

    # operator workflow
    workflow_md = """# Source Pack Operator Workflow

Outlines step-by-step instructions for completing verification checklists.

1. Review operator_research_checklist.json.
2. Formulate manual queries to treasury yield series databases.
3. Prepare manual entries matching source_evidence_entry_template.json.
4. Avoid submitting faked placeholders to draft validations.
"""
    Path(out_dir / "source_pack_operator_workflow.md").write_text(workflow_md, encoding="utf-8")

    # implementation report
    implementation = f"""# Source Pack UI Implementation Report

- **Task Label**: {TASK_LABEL}
- **Safety posture**: offline UI templates compiled successfully; validator status remains FAILED_WITH_BLOCKERS.
"""
    Path(out_dir / "implementation_report.md").write_text(implementation, encoding="utf-8")

    # next task pointer
    next_pointer = """# Next Task Pointer

Recommended next task:

`TASK_CONTENTOPS_V6_VERIFIED_SOURCE_PACK_IMPORT_AND_REVALIDATION_DRY_RUN_HEAVY_BATCH_V0`
"""
    Path(out_dir / "next_task_pointer.md").write_text(next_pointer, encoding="utf-8")

    print(json.dumps({
        "source_pack_verification_ui_status": ui_packet["source_pack_verification_ui_status"],
        "blockers": all_blockers
    }, indent=2))

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
