from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(r"A:\Capital Chronicle\tools\cc-live-contentops")
ARTIFACT = Path(r"C:\Users\bullw\.gemini\antigravity-ide\brain\3b41c2a4-3160-4a9b-bf7f-e4224da537fe")
ARCHIVE = ROOT / "docs" / "archive" / "_repo_cleanup_2026-07-03-pass4_post_task_scripts"

status = ROOT / "docs" / "status" / "current_project_status.json"
data = json.loads(status.read_text(encoding="utf-8"))
data["last_updated_by_task"] = "TASK_CONTENTOPS_V6_AUDIT_BACKED_DISTRIBUTION_RECORD_TO_FEEDBACK_BACKLOG_V0"
data["current_product_phase"] = "Audit-backed distribution record to feedback backlog bridge added"
data["current_product_lane"] = "Jim north-star final loop; audit/outcome evidence feeds operator feedback backlog and next article brief; live actions locked"
data["accepted_baseline_summary"] = "The local-only audit-backed feedback backlog bridge connects safe distribution identity/audit context to operator-supplied feedback intake, deterministic backlog summary, and review-only next article brief candidate. It performs no live write, network/API/webhook/provider/browser/CDP/env/credential/session/scraping/comment/DM/reaction/retry/scheduler action and does not verify public URLs."
data["dispatch_live_status"] = "Dispatch/live write remains locked. Audit-backed feedback packets are local planning/evidence records only, not executable outbox entries, dispatch attempts, scraping jobs, bot commands, or public URL verification."
data["provider_env_credential_status"] = "No provider/API/browser/network/env/credential action is authorized or required for the audit-backed feedback backlog bridge task."
blockers = data.get("active_blockers", [])
blockers.append("Audit-backed feedback bridge is local planning evidence only; real community feedback capture must be operator-supplied unless a future exact approved live task authorizes another source.")
data["active_blockers"] = list(dict.fromkeys(blockers))
data["latest_accepted_task"] = "TASK_CONTENTOPS_V6_AUDIT_BACKED_DISTRIBUTION_RECORD_TO_FEEDBACK_BACKLOG_V0"
data["latest_accepted_task_result"] = "audit_backed_feedback_backlog_bridge_added"
data["latest_changed_areas"] = [
    "live_contentops/audit_backed_feedback_backlog_bridge_v6.py",
    "tests/test_audit_backed_feedback_backlog_bridge_v6.py",
    "docs/automation/V6_AUDIT_BACKED_FEEDBACK_BACKLOG/audit_backed_feedback_backlog_packet.json",
    "docs/automation/V6_AUDIT_BACKED_FEEDBACK_BACKLOG/implementation_report.md",
    "docs/CURRENT_CONTEXT.md",
    "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md",
    "docs/status/current_project_status.json",
]
data["next_recommended_task"] = "TASK_CONTENTOPS_V6_CAMPAIGN_OBJECT_AND_FINAL_LOOP_INTEGRATION_V0: batch Task 22 campaign object with audit-backed feedback packet references, final loop status from idea to next idea, and release-readiness inputs; local/read-only first, no live/provider/browser/network/env/credential action."
status.write_text(json.dumps(data, indent=2), encoding="utf-8")

ARCHIVE.mkdir(parents=True, exist_ok=True)
for stale in [
    ARTIFACT / "scratch" / "apply_identity_outcome_link.py",
    ARTIFACT / "scratch" / "probe3.txt",
    ARTIFACT / "scratch" / "apply_audit_backed_feedback_bridge.py",
]:
    if stale.exists():
        shutil.move(str(stale), str(ARCHIVE / stale.name))
print("status updated and stale scratch archived")
