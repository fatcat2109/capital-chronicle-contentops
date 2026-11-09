"""Verify this source check without altering newsroom or publication state."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of

read = lambda name: json.loads((HERE / name).read_bytes())
pre = read("preflight.json")
source = read("source-readiness.json")
comparison = read("source-comparison.json")
inventory = read("source-inventory.json")
prior = json.loads((HERE.parent / "run-20261108-1725/source-readiness.json").read_bytes())
now = datetime.now(timezone.utc)
operation = Path(source["binding_path"]).parent
binding = json.loads((operation / "binding.json").read_bytes())
digest = lambda p: sha256(Path(p).read_bytes()).hexdigest()
con = sqlite3.connect(Path(binding["store_path"]).as_uri() + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
leases = [dict(row) for row in con.execute(
    "SELECT lease_id,lease_key,status,expires_at FROM leases "
    "WHERE status='ACTIVE' AND expires_at>?", (now.isoformat().replace("+00:00", "Z"),)
)]
work = "cc-opportunity-" + sha256_of(binding["run_id"])
dispatches = [dict(row) for identity in (work, binding["run_id"]) for row in con.execute(
    "SELECT d.platform,d.status FROM platform_dispatches d JOIN outbox_messages m "
    "ON m.message_id=d.message_id WHERE m.work_item_id=?", (identity,)
)]
con.close()
wip = {root: {path: digest(Path(root) / path) for path in tree["tracked_modified_sha256"]}
       for root, tree in pre["trees"].items()}
backlog = Path(r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018"
               r"\docs\project_control_tower\BACKLOG.md").read_text(encoding="utf-8")
start = backlog.index("## CC-124 ")
end = backlog.index("\n## ", start + 1)
fixed = lambda text: "\n".join(line for line in text.splitlines()
                              if not line.startswith(("- Owner:", "- Branch:")))
checks = {
    "binding_and_writer_request_bytes_preserved": all(digest(path) == value
        for path, value in pre["frozen_file_sha256"].items())
        and source["binding_file_sha256"] == prior["binding_file_sha256"]
        and source["writer_request_file_sha256"] == prior["writer_request_file_sha256"],
    "writer_return_absent": not (operation / "desktop_response_write.json").exists(),
    "operation_dispatches_absent": dispatches == source["operation_dispatches"] == [],
    "newsroom_lease_available": leases == source["active_leases"] == [],
    "all_inherited_modified_files_preserved": all(wip[root] == tree["tracked_modified_sha256"]
        for root, tree in pre["trees"].items()),
    "installed_retained_reader_uses_three_verified_main_bls_records":
        not source["source_adapter"]["gaps"] and len(source["source_adapter"]["records"]) == 3,
    "installed_export_reader_observes_incomplete_alternatives":
        comparison["export_scenarios"] > 0
        and comparison["export_scenarios"] == comparison["export_missing_main_alternative_probability"],
    "fourteen_current_full_report_hashes_unchanged": len(comparison["searched_native_reports"]) == 14
        and all(row["same_bytes_as_previous_search"] for row in comparison["searched_native_reports"]),
    "expanded_twenty_five_report_inventory_still_matches_sources":
        len(inventory["expanded_report_search"]) == 25
        and all(digest(row["path"]) == row["sha256"] for row in inventory["expanded_report_search"]),
    "normal_two_article_limit_restored": source["daily_article_limit"] == 2
        and source["occupied_article_slots"] == 0,
    "publication_feed_unchanged": digest(LIVE.parent / "Runtime/ContentOps/published_content_v1.jsonl")
        == pre["publication_feed_sha256"],
    "item_outcome_and_acceptance_preserved": fixed(backlog[start:end]) == fixed(pre["start_item"]),
}
assert all(checks.values()), checks
due = datetime.fromisoformat(pre["worker"]["created_at_utc"].replace("Z", "+00:00")) + timedelta(hours=6)
local = due.astimezone(timezone(timedelta(hours=7)))
result = {
    "observed_at_utc": now.isoformat(), "status": "PASS", "checks": checks,
    "first_cause": comparison["first_cause"],
    "restriction_basis": "Jim decision 93; no new Main report under decision 89.",
    "next_due_utc": due.isoformat(),
    "next_due_gmt7": f"{local.day} Nov 2026 {local:%H:%M} GMT+7",
    "next_due_rule": "Normal six-hour cadence from this worker's actual start; no schedule change.",
    "next_actor": comparison["next_actor"], "next_action": comparison["next_action"],
    "configured_model": pre["worker"]["configured_model"],
    "configured_effort": pre["worker"]["configured_effort"],
    "model_provenance": pre["worker"]["telemetry"],
    "new_publications": 0, "new_editorial_model_calls": 0, "pytest_processes_started": 0,
    "runtime_code_changed": False, "schedules_changed": False, "chat_messages_sent": False,
    "desktop_control_used": False, "inherited_wip_sha256": wip,
    "publication_feed_sha256": pre["publication_feed_sha256"],
    "reader_implementation_sha256": {str(path): digest(path) for path in (
        LIVE / "live_contentops/contentops_source_research_v1.py",
        LIVE / "live_contentops/plan_status_posts_v1.py",
    )},
    "acceptance": "Source check verified; article publication acceptance remains unmet.",
}
(HERE / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": "PASS", "checks": len(checks), "first_cause": result["first_cause"],
                  "next_due": result["next_due_gmt7"]}))
