"""V6 Substack Browser Compose Dry-Run Orchestrator.

Generates the local mock HTML composition mockup, validation reports, and safety configs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from live_contentops import substack_compose_payload_mapper_v6 as mapper
from live_contentops import browser_safety_policy_v6 as safety_policy
from live_contentops import browser_compose_qa_v6 as compose_qa

TASK_LABEL = "TASK_CONTENTOPS_V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN_AND_BROWSER_SAFETY_QA_HEAVY_BATCH_V0"
SCHEMA_VERSION = "6.0.0"

DEFAULT_OUTPUT_DIR = Path("docs/automation/V6_SUBSTACK_BROWSER_COMPOSE_DRY_RUN")


def load_json_or_fallback(path_str: str, default_data: dict[str, Any]) -> dict[str, Any]:
    path = Path(path_str)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default_data


def generate_mock_html(
    preview: dict[str, Any],
    blockers: list[str]
) -> str:
    """Builds a strictly local, self-contained mock compose HTML page."""
    blocker_list_html = "".join(f"<li><code>{b}</code></li>" for b in blockers)
    
    html_lines = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "  <meta charset='UTF-8'>",
        "  <title>Substack Compose Local Mock Preview</title>",
        "  <style>",
        "    body { font-family: sans-serif; padding: 20px; background-color: #fafafa; color: #333; }",
        "    .banner { background-color: #ffcccc; border: 2px solid #ff0000; padding: 15px; font-weight: bold; margin-bottom: 20px; text-align: center; }",
        "    .editor-container { border: 1px solid #ccc; padding: 20px; background-color: #fff; border-radius: 5px; margin-bottom: 20px; }",
        "    .blockers-container { background-color: #fff3cd; border: 1px solid #ffeeba; padding: 15px; margin-bottom: 20px; border-radius: 5px; }",
        "    button { padding: 10px 20px; background-color: #ccc; border: 1px solid #aaa; color: #666; font-weight: bold; border-radius: 3px; cursor: not-allowed; }",
        "    .meta-item { margin-top: 10px; font-size: 0.9em; color: #666; }",
        "  </style>",
        "</head>",
        "<body>",
        "  <div class='banner'>",
        "    [REVIEW-ONLY PREVIEW] PUBLICATION BLOCKED - SOURCE VERIFICATION REQUIRED",
        "  </div>",
        "  <div class='blockers-container'>",
        "    <h3>Active Pipeline Blockers:</h3>",
        f"    <ul>{blocker_list_html}</ul>",
        "  </div>",
        "  <div class='editor-container'>",
        f"    <h2>{preview.get('title')}</h2>",
        f"    <h4>{preview.get('subtitle')}</h4>",
        "    <hr>",
        f"    <div class='content'>{preview.get('body_markdown')}</div>",
        "    <hr>",
        f"    <p><strong>Limitations:</strong> {preview.get('limitations')}</p>",
        f"    <p><strong>Disclosure:</strong> {preview.get('disclosure')}</p>",
        "  </div>",
        "  <div class='meta-item'>",
        f"    <strong>Payload Hash:</strong> <code>{preview.get('payload_hash')}</code>",
        "  </div>",
        "  <div class='meta-item'>",
        f"    <strong>Slug Candidate:</strong> {preview.get('slug_candidate')}",
        "  </div>",
        "  <div style='margin-top: 20px;'>",
        "    <button type='button' disabled>Publish Draft</button>",
        "    <button type='button' disabled style='margin-left: 10px;'>Schedule Draft</button>",
        "  </div>",
        "</body>",
        "</html>"
    ]
    return "\n".join(html_lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 Substack Browser Compose Dry-Run Builder")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--contract-packet", default="docs/automation/V6_UNIFIED_PAYLOAD_APPROVAL_OUTBOX/unified_payload_contract_packet.json")
    args = parser.parse_args(argv)
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    contract_data = load_json_or_fallback(args.contract_packet, {})
    
    # 1. Map preview
    preview_data = mapper.map_canonical_to_preview(contract_data)
    Path(out_dir / "substack_compose_payload_preview.json").write_text(
        json.dumps(preview_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # 2. Validate preview mapper
    validation_report = mapper.validate_compose_payload(preview_data)
    Path(out_dir / "compose_payload_validation_report.json").write_text(
        json.dumps(validation_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # 3. Assemble safety policy
    policy_data = safety_policy.get_safety_policy()
    Path(out_dir / "browser_safety_policy_packet.json").write_text(
        json.dumps(policy_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # Simulate execution state parameters to validate compliance
    runtime_state = {
        "real_substack_opened": False,
        "browser_session_secret_accessed": False,
        "live_publish_control_enabled": False,
        "public_url_captured": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False
    }
    safety_report = safety_policy.validate_safety_compliance(runtime_state)
    Path(out_dir / "browser_safety_validation_report.json").write_text(
        json.dumps(safety_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # Gather unified list of active blockers
    blockers = sorted(list(set(validation_report.get("blockers", []) + safety_report.get("blockers", []))))
    
    # 4. Mock HTML page
    html_content = generate_mock_html(preview_data, blockers)
    Path(out_dir / "substack_mock_compose_page.html").write_text(html_content, encoding="utf-8")
    
    # 5. QA Checklist
    checklist_data = compose_qa.generate_qa_checklist(html_content, preview_data)
    Path(out_dir / "browser_qa_checklist.json").write_text(
        json.dumps(checklist_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # Evidence manifest
    evidence_data = compose_qa.get_screenshot_evidence(screenshot_captured=False)
    Path(out_dir / "browser_screenshot_evidence_manifest.json").write_text(
        json.dumps(evidence_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # 6. Bridge packet
    dry_run_packet = {
        "substack_compose_dry_run_status": "READY_FOR_LOCAL_MOCK_REVIEW_ONLY",
        "local_mock_compose_created": True,
        "real_substack_opened": False,
        "browser_session_started": False,
        "browser_session_secret_accessed": False,
        "screenshot_created": False,
        "screenshot_review_required_by_chatgpt": False,
        "allowed_for_publication": False,
        "public_postable": False,
        "dispatch_allowed_now": False,
        "live_write_allowed_now": False,
        "approval_valid_for_dispatch": False,
        "outbox_entry_created": False,
        "credentials_hydrated": False,
        "kill_switch_active": True,
        "human_review_required": True,
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "next_recommended_task": "TASK_CONTENTOPS_V6_COMMUNITY_FEEDBACK_INTAKE_AND_BACKLOG_LOOP_HEAVY_BATCH_V0",
        "blockers": blockers
    }
    Path(out_dir / "substack_compose_dry_run_packet.json").write_text(
        json.dumps(dry_run_packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8"
    )
    
    # Runbook
    Path(out_dir / "substack_browser_runbook.md").write_text(
        "# Substack Browser Runbook\n\nOutlines safety checks for compose review.\n",
        encoding="utf-8"
    )
    
    # Blocker report
    blocker_str = ", ".join(f"`{b}`" for b in blockers) if blockers else "None"
    Path(out_dir / "substack_browser_blocker_report.md").write_text(
        f"# Substack Browser Blocker Report\n\n- **Blockers**: {blocker_str}\n",
        encoding="utf-8"
    )
    
    # Implementation report
    Path(out_dir / "implementation_report.md").write_text(
        f"# Substack Browser Implementation Report\n\n- **Task Label**: {TASK_LABEL}\n- **Status**: READY_FOR_LOCAL_MOCK_REVIEW_ONLY\n",
        encoding="utf-8"
    )
    
    # Next task pointer
    Path(out_dir / "next_task_pointer.md").write_text(
        f"# Next Task Pointer\n\nRecommended next task:\n\n`{dry_run_packet['next_recommended_task']}`\n",
        encoding="utf-8"
    )
    
    print(json.dumps({
        "substack_compose_dry_run_status": dry_run_packet["substack_compose_dry_run_status"],
        "blockers": dry_run_packet["blockers"]
    }, indent=2))
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
