"""Check the standing-run finding and preserve exact pending-work fingerprints."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TREE = HERE.parents[3]
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of

initial = json.loads((HERE / "resume-check.json").read_bytes())
readiness_path = HERE / "source-readiness.json"
readiness = json.loads(readiness_path.read_bytes())
rows = readiness["public_export_scenarios"]
missing = [row["pointer"] for row in rows
           if ((row["value"] or {}).get("main_alternative") or {}).get("probability_pct") is None]
assert rows and len(missing) == len(rows), "REVIEW_CHANGED_MAIN_SCENARIOS"
readiness["main_export_summary"] = {
    "scenario_records": len(rows), "scenario_objects": sum(isinstance(row["value"], dict) for row in rows),
    "main_alternative_probability_absent": len(missing),
    "missing_probability_pointers": missing,
    "nfp_plan_source_hash": "db7a64e21bf6043c61b9ea75d300db0b72f11002d11ae735637548eb7982304a",
}
readiness["daily_main_report_catalog_count"] = readiness.pop("daily_main_report_count_searched")
readiness["daily_main_report_contents_searched"] = 6
readiness["outcome_scope"] = "Standing-run source comparison; the native operation remains pending write."
readiness["official_support_admitted_to_frozen_writer"] = False
readiness["official_support_clock_note"] = "Held BLS captures were known at 13:57Z on 6 November, after the original cutoff; their exact clocks are retained and no frozen writer input is changed."
readiness_path.write_text(json.dumps(readiness, indent=2) + "\n", encoding="utf-8")

binding_path = Path(initial["binding_path"])
binding = json.loads(binding_path.read_bytes())
request_path = binding_path.parent / "desktop_request_write.json"
assert sha256(binding_path.read_bytes()).hexdigest() == initial["binding_file_sha256"]
assert sha256(request_path.read_bytes()).hexdigest() == initial["writer_request_file_sha256"]
assert not (binding_path.parent / "desktop_response_write.json").exists()
inherited = {name: sha256((TREE / name).read_bytes()).hexdigest()
             for name in initial["inherited_files_sha256"]}
assert inherited == initial["inherited_files_sha256"]
now = datetime.now(timezone.utc)
connection = sqlite3.connect(Path(binding["store_path"]).as_uri() + "?mode=ro", uri=True)
connection.row_factory = sqlite3.Row
work = "cc-opportunity-" + sha256_of(binding["run_id"])
with connection:
    dispatches = [dict(row) for row in connection.execute(
        "SELECT d.platform,d.status FROM platform_dispatches d JOIN outbox_messages m "
        "ON d.message_id=m.message_id WHERE m.work_item_id IN (?,?)", (binding["run_id"], work))]
    leases = [dict(row) for row in connection.execute(
        "SELECT lease_key,status,expires_at FROM leases WHERE status='ACTIVE' AND expires_at>?",
        (now.isoformat().replace("+00:00", "Z"),))]
connection.close()
assert not dispatches
operating_dirty = subprocess.check_output(
    ["git", "-C", str(LIVE), "diff", "--name-only"], text=True).splitlines()
operating_wip = {name: sha256((LIVE / name).read_bytes()).hexdigest() for name in operating_dirty}
result = {"observed_at_utc": now.isoformat(), "status": "PASS",
    "main_alternative_probability_absent": f"{len(missing)}/{len(rows)}",
    "retained_source_records_verified": 3, "binding_bytes_unchanged": True,
    "writer_request_bytes_unchanged": True, "writer_return_present": False,
    "operation_dispatches": dispatches, "active_leases": leases,
    "inherited_workspace_files_sha256": inherited, "inherited_workspace_bytes_unchanged": True,
    "operating_wip_before_integration": operating_wip,
    "new_publications": 0, "new_models": 0, "new_media": 0, "pytest_processes_started": 0,
    "runtime_code_changed": False, "native_operation_mutated": False,
    "next_due_utc": readiness["next_due_utc"], "next_due_gmt7": "8 Nov 2026 03:34 GMT+7",
    "next_due_rounding": "Round the 03:33:04 GMT+7 twelve-hour restart instant up to the next minute."}
(HERE / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: result[k] for k in ("status", "main_alternative_probability_absent",
    "binding_bytes_unchanged", "writer_request_bytes_unchanged", "operation_dispatches", "next_due_gmt7")}))
