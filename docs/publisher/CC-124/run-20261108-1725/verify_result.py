"""Check the due source comparison using bounded read-only state queries."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of

pre = json.loads((HERE / "preflight.json").read_bytes())
source = json.loads((HERE / "source-readiness.json").read_bytes())
compare = json.loads((HERE / "source-comparison.json").read_bytes())
prior = json.loads((HERE.parent / "run-20261108-0352/source-readiness.json").read_bytes())
operation = Path(source["binding_path"]).parent
binding = json.loads((operation / "binding.json").read_bytes())
now = datetime.now(timezone.utc)
con = sqlite3.connect(Path(binding["store_path"]).as_uri() + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
leases = [dict(r) for r in con.execute(
    "SELECT lease_id,lease_key,status,expires_at FROM leases "
    "WHERE status='ACTIVE' AND expires_at>?", (now.isoformat().replace("+00:00", "Z"),)
)]
work = "cc-opportunity-" + sha256_of(binding["run_id"])
dispatches = [dict(r) for identity in (work, binding["run_id"]) for r in con.execute(
    "SELECT d.platform,d.status FROM platform_dispatches d "
    "JOIN outbox_messages m ON m.message_id=d.message_id "
    "WHERE m.work_item_id=? ORDER BY d.dispatch_id", (identity,)
)]
con.close()
wip = {root: {p: sha256((Path(root) / p).read_bytes()).hexdigest()
              for p in data["tracked_modified_sha256"]}
       for root, data in pre["trees"].items()}
backlog = Path(r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018"
               r"\docs\project_control_tower\BACKLOG.md").read_text(encoding="utf-8")
a = backlog.index("## CC-124 ")
z = backlog.index("\n## ", a + 1)
item = backlog[a:z]
fixed = lambda value: "\n".join(line for line in value.splitlines()
                               if not line.startswith(("- Owner:", "- Branch:")))
checks = {
    "binding_bytes_unchanged_since_prior_run": sha256((operation / "binding.json").read_bytes()).hexdigest()
        == source["binding_file_sha256"] == prior["binding_file_sha256"],
    "writer_request_bytes_unchanged_since_prior_run": sha256((operation / "desktop_request_write.json").read_bytes()).hexdigest()
        == source["writer_request_file_sha256"] == prior["writer_request_file_sha256"],
    "writer_return_absent": not (operation / "desktop_response_write.json").exists(),
    "operation_dispatches_absent": dispatches == source["operation_dispatches"] == [],
    "no_active_newsroom_lease": leases == source["active_leases"] == [],
    "all_eight_inherited_modified_files_preserved": all(
        wip[root] == data["tracked_modified_sha256"] for root, data in pre["trees"].items()
    ) and sum(len(paths) for paths in wip.values()) == 8,
    "installed_research_reader_verified_three_records": not source["source_adapter"]["gaps"]
        and len(source["source_adapter"]["records"]) == 3,
    "installed_export_reader_observes_missing_alternative_probabilities":
        compare["export_scenarios"] == compare["export_missing_main_alternative_probability"] == 40,
    "all_fourteen_full_report_hashes_unchanged": len(compare["searched_native_reports"]) == 14
        and all(r["same_bytes_as_previous_search"] for r in compare["searched_native_reports"]),
    "latest_daily_report_unchanged": compare["latest_complete_daily_report_unchanged"],
    "weekend_article_capacity_available": source["daily_article_limit"] == 1
        and source["occupied_article_slots"] == 0,
    "item_contract_preserved": pre["item_contract_unchanged"] and fixed(item) == fixed(pre["start_item"]),
}
assert all(checks.values()), checks
start = datetime.fromisoformat(pre["worker"]["created_at_utc"].replace("Z", "+00:00"))
reset = datetime(2026, 11, 8, 18, 0, tzinfo=timezone.utc)
due = min(start + timedelta(hours=12), max(reset, start + timedelta(hours=6)))
local = due.astimezone(timezone(timedelta(hours=7)))
result = {
    "observed_at_utc": now.isoformat(), "status": "PASS", "checks": checks,
    "first_cause": compare["first_cause"],
    "next_due_utc": due.isoformat(),
    "next_due_gmt7": f"{local.day} Nov 2026 {local:%H:%M} GMT+7",
    "next_due_rule": "Decision 94 ends at 9 Nov 01:00 GMT+7; the six-hour interval since this start has already elapsed then.",
    "next_actor": compare["next_actor"], "next_action": compare["next_action"],
    "configured_model": pre["worker"]["configured_model"],
    "configured_effort": pre["worker"]["configured_effort"],
    "model_provenance": pre["worker"]["telemetry"],
    "new_publications": 0, "new_editorial_model_calls": 0,
    "new_source_requests": 0, "new_media": 0, "new_destination_drafts": 0,
    "pytest_processes_started": 0, "runtime_code_changed": False,
    "schedules_changed": False, "chat_messages_sent": False,
    "desktop_control_used": False, "inherited_wip_sha256": wip,
    "publication_feed_sha256": sha256((LIVE.parent / "Runtime/ContentOps/published_content_v1.jsonl").read_bytes()).hexdigest(),
    "reader_implementation_sha256": {str(p): sha256(p.read_bytes()).hexdigest() for p in (
        LIVE / "live_contentops/contentops_source_research_v1.py",
        LIVE / "live_contentops/plan_status_posts_v1.py",
    )},
}
(HERE / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": "PASS", "checks": len(checks),
                  "first_cause": result["first_cause"], "next_due": result["next_due_gmt7"]}))
