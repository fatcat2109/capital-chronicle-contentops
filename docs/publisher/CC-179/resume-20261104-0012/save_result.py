"""Save this run's bounded evidence from the existing publication projection."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib, json, os, re, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication

root = Path(__file__).resolve().parent
store = ContentOpsDurableStore(r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3", auto_migrate=False)
rollout = json.loads(Path("config/native_desktop_rollout_v1.json").read_bytes())
now = datetime.now(timezone.utc).isoformat()
all_destinations = []
runs = ["cc074-retro-fomc-20261028-v1", "cc107-midterm-preview-20261103-v1", "cc124-prepare-20261103-a"]
for run in runs:
    binding = json.loads((Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual") / run / "binding.json").read_bytes())
    owner = NativeReviewedPublication(store, binding, native_invocation_id=os.environ["CODEX_THREAD_ID"], rollout=rollout)
    projection = owner.projection()
    (root / (run + "-final-projection.json")).write_text(json.dumps(projection, indent=2) + "\n")
    assert len(projection["destinations"]) == 9
    for destination in projection["destinations"]:
        entry = {"run_id": run, **destination, "observed_at_utc": now}
        status = entry["status"]
        if status == "DISPATCH_CONFIRMED":
            entry.update(outcome="EXISTING_CONFIRMED_PUBLIC_IDENTITY", next_owner=None, next_action=None)
            if entry.get("reconciliation_status") == "RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE":
                entry.update(unresolved_cause="CONTENT_VERIFICATION_INCOMPLETE", next_owner="Publisher existing editorial/reconciliation owner",
                    next_action="Inspect and correct the exact canonical object without reposting.")
        elif status == "UNKNOWN_WRITE":
            entry.update(outcome="UNRESOLVED_READBACK_OWED", unresolved_cause="UNIDENTIFIED_UNKNOWN_WRITE_RECONCILIATION_PENDING",
                next_owner="Jim for a new post-retry observation; Publisher for exact coordinator reconciliation" if run == runs[0] else "Publisher and Jim",
                next_action="Supply this attempt's public URL/ID or an explicit absence observation after the latest attempt; read back and reconcile. No retry.")
        elif run == runs[1]:
            entry.update(outcome="NO_NEW_DISPATCH", unresolved_cause="EDITORIAL_CHART_FACT_RIGHTS_UNBOUND",
                next_owner="Ops and Publisher source/media owner",
                next_action="Resolve original-source chart fact-reuse scope and bind genuine missing rights evidence; preserve the confirmed canonical and AOC photo approval.")
        elif run == runs[2]:
            entry.update(outcome="NO_NEW_DISPATCH", unresolved_cause="ANALYSIS_OFFICIAL_HISTORY_CHARTS_REQUIRED; SAME_MAX_DERIVATIVE_SELECTION_AND_REVIEW_REQUIRED",
                next_owner="Publisher engineering and designated /root/cpi_max_writer",
                next_action="Use cpi-derivative-amendment-input.json; obtain actual same-writer channel selection/review and extend the existing amendment consumer. Preserve original intents; read back unknowns before any send; edit confirmed objects only.")
        elif entry.get("reconciliation_status") == "RECONCILED_ABSENT_SAFE_TO_RETRY":
            entry.update(outcome="CONFIRMED_ABSENT_NO_NEW_SEND", unresolved_cause=status,
                next_owner="Publisher existing dated-distribution editorial owner",
                next_action="Retain confirmed absence; the stale/exhausted copy needs the existing reviewed dated-distribution path before a new authorized attempt.")
        else:
            entry.update(outcome="NO_NEW_DISPATCH", unresolved_cause="THREADS_AUTH_INVALID" if entry["destination"] == "threads" else status,
                next_owner="Jim for account reauthorization; Publisher for normal destination validation" if entry["destination"] == "threads" else "Publisher",
                next_action="Restore the existing destination authorization, then verify identity through its normal owner; do not switch account or transport." if entry["destination"] == "threads" else "Resolve the exact saved destination cause through its existing owner.")
        all_destinations.append(entry)
timing = []
for row in store.list_outbox_messages():
    if row["work_item_id"] == runs[0] and row["message_id"].startswith("native-dispatch-timing-"):
        value = json.loads(row["payload"])
        if value.get("dispatch_id") == "dispatch_9b8a57d1a3c6794c5a999966b9bd28c2": timing.append(value)
summary = {"item": "CC-179", "status": "BLOCKED", "observed_at_utc": now,
    "live_code_commit": "eeab4631", "live_tag": "contentops-live-20261104-cc179-retry-clock",
    "configured_model": "gpt-6.1-sol", "configured_effort": "high", "configuration_status": "CONFIGURED_NOT_OBSERVED",
    "new_confirmed_posts": 0, "authorized_linkedin_retry_calls": 1,
    "linkedin_absence_before_retry_confirmed": True, "linkedin_after_retry": "UNKNOWN_WRITE_READBACK_OWED_NO_MORE_RETRIES",
    "latest_linkedin_api_attempt_timing": timing, "all_27_intended_destinations_accounted_for": len(all_destinations) == 27,
    "counts": dict(Counter(d["outcome"] for d in all_destinations)),
    "cpi_amendment_state": "REVIEW_INPUT_PREPARED_NOT_ACCEPTED_NOT_BOUND_NOT_WIRED_TO_SOCIAL_CONSUMER",
    "same_native_writer_available": False, "available_native_agents": ["/root"],
    "source_rights_invented": False, "confirmed_objects_reposted": False,
    "messages_sent_to_chats": 0, "schedules_changed": 0, "native_desktop_control_used": False,
    "destinations": all_destinations}
assert summary["all_27_intended_destinations_accounted_for"]
assert len({(d["run_id"], d["destination"]) for d in all_destinations}) == 27
assert all(d.get("public_object_id") or d.get("public_object_url") or d.get("unresolved_cause") for d in all_destinations)
(root / "final-run-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
files = []
for path in sorted(root.iterdir()):
    if not path.is_file() or path.name == "validation.json": continue
    data = path.read_bytes()
    if (re.search(rb"data:image/[a-z]+;base64,[A-Za-z0-9+/]{256}", data)
            or re.search(rb'"content_base64"\s*:\s*"[A-Za-z0-9+/]{256}', data)):
        raise ValueError("EMBEDDED_IMAGE_BYTES_EXCLUDED:" + path.name)
    files.append({"path": path.name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
(root / "validation.json").write_text(json.dumps({"state": "PASS_BOUNDED_EVIDENCE_VALIDATION", "observed_at_utc": now,
    "destinations": 27, "no_embedded_image_bytes": True, "files": files}, indent=2) + "\n")
print(json.dumps({k:summary[k] for k in ("status", "counts", "new_confirmed_posts", "authorized_linkedin_retry_calls", "all_27_intended_destinations_accounted_for")}))
