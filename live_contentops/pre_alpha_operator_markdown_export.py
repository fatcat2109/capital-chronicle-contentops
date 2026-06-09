"""Local-only operator readable markdown export (Task 0121).

Renders the deterministic pre-alpha content run and templates into human-readable Markdown.
It never publishes, calls APIs, scrapes, or implies public-postable status.
"""

from live_contentops import pre_alpha_daily_operator_content_run
from live_contentops import pre_alpha_platform_manual_templates
from live_contentops import pre_alpha_manual_publish_record
from live_contentops import pre_alpha_manual_performance_record
from live_contentops import pre_alpha_content_performance_review

def generate_markdown_export():
    """Generate the Operator Workbench Markdown export string."""
    run_packet = pre_alpha_daily_operator_content_run.build_from_config_file()
    tmpl_packet = pre_alpha_platform_manual_templates.build_from_config_file()
    pub_packet = pre_alpha_manual_publish_record.build_from_config_file()
    perf_packet = pre_alpha_manual_performance_record.build_from_config_file()
    rev_packet = pre_alpha_content_performance_review.build_from_config_file()

    # Determine overall safety
    is_safe = True
    for p in [run_packet, tmpl_packet, pub_packet, perf_packet, rev_packet]:
        if p.get("packet_status") == "blocked":
            is_safe = False

    lines = []
    lines.append("# Capital Chronicle ContentOps Daily Operator Workbench")
    lines.append("")
    if not is_safe:
        lines.append("## WARNING: ONE OR MORE PACKETS BLOCKED OR NOT READY")
        lines.append("Some components of the workflow are blocked. Review the Blocked or Not Ready section.")
        lines.append("")

    lines.append("## Safety Header")
    lines.append("- Local-only/manual-only")
    lines.append("- Operator final check required")
    lines.append("- Not public-postable by default")
    lines.append("- No platform API payload")
    lines.append("- No scheduler")
    lines.append("- No scraping")
    lines.append("- No automatic metrics ingestion")
    lines.append("- No inferred publication or metrics")
    lines.append("")

    lines.append("## Run Summary")
    lines.append(f"- packet_status: {run_packet.get('packet_status')}")
    lines.append(f"- ready_for_operator_copy_paste_count: {run_packet.get('ready_for_operator_copy_paste_count')}")
    lines.append(f"- blocked_or_not_ready_count: {run_packet.get('blocked_or_not_ready_count')}")
    lines.append(f"- unsafe_flag_count: {run_packet.get('safety_audit', {}).get('unsafe_flag_count')}")
    demo_status = run_packet.get('dashboard_summary', {}).get('pipeline_demo_status')
    if demo_status:
        lines.append(f"- current fixture/demo status: {demo_status}")
    lines.append("")

    lines.append("## Ready for Operator Review")
    templates = tmpl_packet.get('platform_template_records', [])
    if not templates:
        lines.append("No ready items.")
    for t in templates:
        lines.append(f"### Item: {t.get('draft_id') or t.get('manual_export_packet_id')}")
        lines.append(f"- **Platform Family:** {t.get('platform_family')}")
        lines.append(f"- **Content Type:** {t.get('content_type', 'unknown')}")
        srcs = t.get('source_artifact_ids', [])
        if t.get('is_general_process_content'):
            lines.append("- **Source:** general/product/process marker")
        elif srcs:
            lines.append(f"- **Source:** {', '.join(srcs)}")
        
        limits = t.get('limitations', [])
        if limits:
            lines.append("- **Limitations/Freshness:** " + " | ".join(limits))
        
        lines.append("\n**Copy/Paste Text Block:**")
        lines.append("```")
        lines.append(t.get('copy_paste_text', ''))
        lines.append("```")
        lines.append("\n**Final Check Checklist:**")
        for ck in tmpl_packet.get('operator_final_checklist', []):
            lines.append(f"- [ ] {ck}")
        lines.append("")

    lines.append("## Blocked or Not Ready")
    blocked_items = run_packet.get('blocked_content_report', [])
    if not blocked_items:
        lines.append("None.")
    for b in blocked_items:
        ref = b.get('draft_id') or b.get('seed_id') or b.get('manual_export_packet_id') or 'unknown'
        reason = b.get('reason') or b.get('decision_status') or 'blocked'
        lines.append(f"- **Stage:** {b.get('stage')} | **Item/Ref:** {ref} | **Reason:** {reason}")
        lines.append("  - *Required Operator Action:* Manually resolve blocking issues in source.")
    lines.append("")

    lines.append("## Platform Manual Templates")
    if not templates:
        lines.append("No platform templates generated.")
    for t in templates:
        lines.append(f"### {str(t.get('platform_family')).upper()} Template")
        lines.append("```")
        lines.append(t.get('copy_paste_text', ''))
        lines.append("```")
        lines.append("**Formatting Notes:**")
        for fn in t.get('formatting_notes', []):
            lines.append(f"- {fn}")
        lines.append("- No current platform spec verification claim.")
        lines.append("")

    lines.append("## Manual Publish Record Reminder")
    not_recorded = pub_packet.get('not_recorded_count', 0)
    lines.append(f"- Status: {not_recorded} no record yet / {pub_packet.get('recorded_publish_count', 0)} recorded / {pub_packet.get('blocked_record_count', 0)} blocked")
    lines.append("- Reminder: Manual URL/timestamp required after external posting.")
    lines.append("- Reminder: No inferred publication allowed.")
    lines.append("")

    lines.append("## Manual Performance Record Reminder")
    lines.append("- Reminder: optional post-publish manual entry.")
    lines.append("- Reminder: operator-entered metrics only.")
    lines.append("- Reminder: missing metrics remain missing/null.")
    lines.append("")

    lines.append("## Content Performance Review")
    lines.append("- Reminder: optional local-only review.")
    lines.append("- Reminder: conservative findings only.")
    if rev_packet.get('insufficient_sample'):
        lines.append("- Warning: insufficient sample warnings triggered.")
    for finding in rev_packet.get('conservative_findings', []):
        lines.append(f"- Finding: {finding}")
    lines.append("- Reminder: no statistical significance claimed.")
    lines.append("")

    lines.append("## Next Operator Actions")
    actions = run_packet.get('operator_action_queue', [])
    if not actions:
        lines.append("No actions pending.")
    for act in actions:
        lines.append(f"- {act}")
    lines.append("- Exact recommended next manual actions: complete review, never auto-post.")

    return "\n".join(lines), is_safe
