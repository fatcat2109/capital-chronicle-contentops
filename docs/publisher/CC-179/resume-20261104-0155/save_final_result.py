"""Save bounded readbacks for CC-179's three existing operations."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import re
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

root = Path(__file__).resolve().parent
store = ContentOpsDurableStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3", auto_migrate=False)
runs = ["cc074-retro-fomc-20261028-v1", "cc107-midterm-preview-20261103-v1", "cc124-prepare-20261103-a"]
observed_at = datetime.now(timezone.utc).isoformat()
entries, timings = [], {}
for run in runs:
    command = ["python", "scripts/run_native_desktop_editorial.py", "publication-status", "--binding",
        str(Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual") / run / "binding.json")]
    response = subprocess.run(command, cwd=repo, capture_output=True, text=True)
    if response.returncode:
        raise RuntimeError("FINAL_STATUS_READBACK_FAILED:" + run)
    projection = json.loads(response.stdout)
    (root / (run + "-final-projection.json")).write_text(json.dumps(projection, indent=2) + "\n")
    timings[run] = projection.get("timing", {})
    for destination in projection["destinations"]:
        d = destination["destination"]
        item = {"run_id": run, **destination, "observed_at_utc": observed_at,
            "public_publication_at_utc": None,
            "clock_limit": "Dispatch creation, actual adapter calls, native observations and public publication are separate. A null publication clock stays unknown."}
        dispatch = store.get_platform_dispatch(destination["dispatch_id"]) or {}
        item["dispatch_record_created_at_utc"] = dispatch.get("created_at")
        item["readback_observation_clocks"] = [r["read_at"] for r in store.list_readbacks_for_dispatch(destination["dispatch_id"])]
        if destination.get("public_object_id") and destination["status"] == "DISPATCH_CONFIRMED":
            item.update(outcome="RETAINED_CONFIRMED_PUBLIC_IDENTITY", next_owner=None, next_action=None)
            if destination.get("reconciliation_status") != "RECONCILED_CONFIRMED":
                cause = ("READBACK_UNAVAILABLE" if d == "telegram" else
                    "FAILED_DISCORD_STRICT_READBACK" if d == "discord" else
                    "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE")
                item.update(content_readback_limit=cause, next_owner="Publisher existing exact-object readback owner",
                    next_action="Keep this public identity; resolve the current content readback limit on the same object without reposting.")
        elif destination.get("reconciliation_status") == "RECONCILED_ABSENT_SAFE_TO_RETRY":
            cause = ("DEFINITE_NO_WRITE_AFTER_ONE_MEDIA_TRANSPORT_CORRECTION" if run == runs[2] else destination["status"])
            item.update(outcome="CONFIRMED_ABSENT", unresolved_cause=cause,
                next_owner="Publisher existing explicit dated-distribution owner",
                next_action="Retain confirmed absence. Do not automatically send again; any later correction must use the existing explicit recovery and its exact reviewed packet.")
        elif d == "linkedin" and destination.get("dispatch_recorded"):
            item.update(outcome="UNRESOLVED_EXACT_ATTEMPT_READBACK", unresolved_cause="UNIDENTIFIED_UNKNOWN_WRITE_RECONCILIATION_PENDING",
                next_owner="Jim for a post-attempt URL or fresh absence report; Publisher for exact coordinator reconciliation",
                next_action="Identify this attempt's exact public object or supply a new post-attempt absence observation. FOMC's one authorized retry is spent; never reuse the earlier absence report or send blindly.")
        elif run == runs[1]:
            item.update(outcome="NOT_DISPATCHED_RIGHTS_HOLD", unresolved_cause="EDITORIAL_CHART_FACT_RIGHTS_UNBOUND",
                next_owner="Source/media rights owner and Jim",
                next_action="Resolve chart-fact reuse for the retained PollCheck figures or bind a lawful replacement through the existing editorial owner; keep the canonical and separately approved AOC photograph.")
        elif d == "threads":
            item.update(outcome="NOT_DISPATCHED_AUTHORIZATION_HOLD", unresolved_cause="THREADS_AUTH_INVALID",
                next_owner="Jim for existing-account authorization; Publisher for normal destination readback",
                next_action="Restore the existing Threads authorization, verify the same identity, and resume the existing operation.")
        else:
            item.update(outcome="UNRESOLVED_EXACT_ATTEMPT_READBACK", unresolved_cause="UNIDENTIFIED_NATIVE_ATTEMPT_NO_EXACT_OBJECT_IN_LOADED_PROFILE",
                next_owner="Publisher exact-object readback owner; Jim if an external object or absence observation is needed",
                next_action="Resolve the existing X or YouTube attempt from an exact public ID or conclusive absence evidence. Actual Neo observations are submitted; no blind retry.")
        entries.append(item)
assert len(entries) == 27
assert len({(d["run_id"], d["destination"]) for d in entries}) == 27
counts = dict(Counter(d["outcome"] for d in entries))
summary = {"item": "CC-179", "status": "BUILT_UNMERGED", "observed_at_utc": observed_at,
    "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
    "operating_root_commit": subprocess.check_output(["git", "-C", r"A:\Capital Chronicle\ContentOps", "rev-parse", "HEAD"], text=True).strip(),
    "new_confirmed_posts": 0, "integration_performed": False,
    "configuration": json.loads((root / "launch-record.json").read_bytes()),
    "cpi_retained_max_review_bound": True, "cpi_channel_media_delivery_bound": True,
    "cpi_instagram_adapter_calls": 2, "cpi_instagram_confirmed_public_objects": 0,
    "cpi_instagram_explicit_media_correction_budget_spent": True,
    "cpi_unselected_canonical_component_limit": "public_object_hash_match_missing:cpi-september-effects-r2",
    "cpi_unselected_component_next_action": "Publisher verifies or repairs the third chart on exact canonical 223246940; passing annual/monthly social media remain independently bound.",
    "midterm_rights_fields_invented": False, "confirmed_objects_reposted": False,
    "actual_native_neo_readback_returns_submitted": ["x", "youtube"],
    "fomc_linkedin_extra_retries": 0, "messages_to_chats": 0, "schedules_changed": 0,
    "native_desktop_control_used": False, "native_file_dialog_opened": False,
    "counts": counts, "all_27_intended_destinations_accounted_for": True,
    "timing": timings, "destinations": entries,
    "verification": {"frozen_copy_regressions": "67 passed", "review_and_native_regressions": "56 passed",
        "final_channel_media_regressions": "75 passed",
        "coordinator_regression_run": "118 passed; one new test assertion failed and was corrected; the corrected file passed in the 56- and 75-test runs",
        "earlier_source_recovery_selection": "27 passed, 4 pre-existing source-recovery fixture failures observed before the source changes; recovery-regressions.txt retains exact evidence",
        "counts_overlap": True, "whole_suite_claimed": False}}
(root / "final-run-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
for item in entries:
    if item["outcome"] != "RETAINED_CONFIRMED_PUBLIC_IDENTITY":
        assert item.get("unresolved_cause") and item.get("next_owner") and item.get("next_action")
artifacts = []
for path in root.rglob("*"):
    if not path.is_file() or path.name == "validation.json":
        continue
    data = path.read_bytes()
    if re.search(br"data:image/[^;\s\"]+;base64,[A-Za-z0-9+/]{128}", data):
        raise ValueError("EMBEDDED_IMAGE_BYTES_EXCLUDED:" + str(path))
    artifacts.append({"path": str(path.relative_to(root)), "bytes": len(data), "sha256": sha256(data).hexdigest()})
(root / "validation.json").write_text(json.dumps({"status": "PASS", "observed_at_utc": observed_at,
    "destinations": len(entries), "distinct_operations": len(runs), "counts": counts,
    "artifacts": artifacts, "image_bytes_printed_or_committed": False}, indent=2) + "\n")
print(json.dumps({"status": summary["status"], "destinations": len(entries), "counts": counts,
    "new_confirmed_posts": 0, "evidence": str(root / "final-run-summary.json")}))
