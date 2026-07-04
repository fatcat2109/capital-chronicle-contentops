# Institutional Antigravity Browser QA Evidence Packet Template (After 0168)

Task label context: TASK_CONTENTOPS_0168_ANTIGRAVITY_BROWSER_QA_STRATEGY_AND_MANUAL_RUNBOOK_V0
Repo: A:\Capital Chronicle\tools\cc-live-contentops

This template defines the FINAL EVIDENCE PACKET a future operator-approved browser/
Antigravity QA task must return. It is a template only; no browser QA was executed in
0168.

## Required Evidence Packet Fields

- task_label
- result: PASS / BLOCKED / FAIL
- worker_tool (exact tool/agent used)
- repo_path
- branch
- starting_head
- final_head
- browser_or_tool_used_and_exact_tool (yes/no + exact tool)
- antigravity_run (yes/no)
- screenshots_captured (yes/no + authorization reference if yes)
- network_used (yes/no)
- env_or_credentials_read (yes/no)
- external_url_opened (yes/no)
- screens_inspected (list of the 12 screens reached)
- issues_found (visual bug list)
- disabled_control_status (all forbidden controls confirmed inactive)
- redaction_secret_status (no secrets / no raw env / no raw response confirmed)
- visual_quality_status (contrast, legibility, layout)
- safety_status (banners confirmed, no live controls)
- validation_commands_results (before/after, if any)
- git_status
- active_blockers
- exact_next_task
- confirmation: no live/API/posting/scheduling/export/evidence-mutation occurred

## Filled Example (Template — Not An Executed Run)

```
task_label: TASK_CONTENTOPS_0169_OPERATOR_APPROVED_ANTIGRAVITY_BROWSER_QA_LOCAL_STATIC_SHELL_V0
result: <PASS|BLOCKED|FAIL>
worker_tool: <exact tool>
repo_path: A:\Capital Chronicle\tools\cc-live-contentops
branch: master
starting_head: <short hash>
final_head: <short hash>
browser_or_tool_used_and_exact_tool: <yes/no + tool>
antigravity_run: <yes/no>
screenshots_captured: <yes/no + authorization ref>
network_used: no
env_or_credentials_read: no
external_url_opened: no
screens_inspected: [command_center, content_lane_control, daily_content_studio,
  draft_inspector, grounded_news_angle_lab, publish_readiness_tower,
  telegram_pilot_gate, approval_queue, content_calendar, evidence_vault,
  visual_export_studio, settings_safety_policy]
issues_found: <list or none>
disabled_control_status: <all inactive confirmed>
redaction_secret_status: <no secrets / no raw env / no raw response>
visual_quality_status: <readable/contrast OK>
safety_status: <banners present, no live controls>
validation_commands_results: <pytest/node check before-after if any>
git_status: <short>
active_blockers: <none or list>
exact_next_task: <next pointer>
confirmation: no live/API/posting/scheduling/export/evidence-mutation occurred
```

## Notes

- The evidence packet must be secret-safe: no token/chat ID, no env path, no raw
  request URL, no raw platform response, no credential value.
- Screens-inspected must cover all 12 screens for a PASS.
- Any stop condition triggers an immediate halt and a BLOCKED or FAIL classification.
