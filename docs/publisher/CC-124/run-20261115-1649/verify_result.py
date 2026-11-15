"""Verify this bounded standing check against its installed-consumer evidence."""
from datetime import datetime, timedelta, timezone
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
BUILDER = HERE.parents[3]
LIVE = Path(r"A:\Capital Chronicle\ContentOps")


def load(name):
    return json.loads((HERE / name).read_bytes())


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


inventory = load("inventory-result.json")
sources = load("source-assessment.json")
consumers = load("installed-consumers.json")
launch = load("launch-observation.json")
completed = [row for row in sources["retained_reports"] if row["completed_output"]]
assert len(completed) == inventory["completed_source_count"] == 42
assert inventory["eligible_completed_sources"] == 0
assert inventory["changed_native_outputs_since_prior"] == 0
assert all(row["publication_clock_cause"] for row in completed)
clock_causes = Counter(row["publication_clock_cause"].split(":", 1)[0] for row in completed)
assert clock_causes == {"ARTICLE_DATA_CUTOFF_EXPIRED": 40,
                        "ARTICLE_DATA_CUTOFF_NOT_SUPPLIED_BY_SOURCE": 2}
assert sources["latest_t2_selection"]["publication_clock_cause"].startswith("ARTICLE_DATA_CUTOFF_EXPIRED:")
assert consumers["active_leases"] == []
assert consumers["article_slots_in_use"] == []
assert consumers["daily_article_limit"] == 2
feed = consumers["publication_feed_before"]
assert digest(feed["path"]) == feed["sha256"]

preserved = []
for row in load("preserved-work.json"):
    unchanged = digest(row["path"]) == row["sha256"]
    assert unchanged, row["path"]
    preserved.append({"path": row["path"], "sha256": row["sha256"], "exact_bytes_unchanged": unchanged})

base = subprocess.check_output(["git", "-C", str(LIVE), "rev-parse", "HEAD"], text=True).strip()
remote = subprocess.check_output(["git", "-C", str(BUILDER), "rev-parse", "origin/master"], text=True).strip()
assert subprocess.run(["git", "-C", str(BUILDER), "merge-base", "--is-ancestor", remote, base], check=False).returncode == 0
start = datetime.fromisoformat(launch["process_started_utc"].replace("Z", "+00:00"))
due = start + timedelta(hours=6)
due = due.replace(second=0, microsecond=0) + timedelta(minutes=1)
gmt7 = timezone(timedelta(hours=7))
now = datetime.now(timezone.utc)
result = {
    "backlog_item": "CC-124", "observed_at_utc": now.isoformat(),
    "actual_start_utc": start.isoformat(), "assessment_at_utc": inventory["observed_at_utc"],
    "classification": "NO_CURRENT_MAIN_SOURCE", "new_articles": 0,
    "first_cause": sources["latest_completed_analysis"]["publication_clock_cause"],
    "policy": ["JIM_DECISION_89: Main reports only; end immediately when nothing new",
               "CC403_READER_ARTICLE_V1: publish within 60 minutes of original data capture"],
    "latest_original_capture_utc": inventory["latest_original_capture_utc"],
    "latest_publication_deadline_utc": sources["latest_completed_analysis"]["publication_deadline_utc"],
    "completed_sources": len(completed), "eligible_completed_sources": 0,
    "source_clock_causes": dict(clock_causes),
    "changed_native_outputs_since_prior": 0,
    "production_day": consumers["production_day"], "daily_article_limit": 2,
    "article_slots_in_use": 0, "active_leases_at_assessment": 0,
    "operation_allocated": False, "native_editorial_calls": 0,
    "public_writes": 0, "browser_actions": 0, "desktop_control_actions": 0,
    "chat_messages": 0, "schedule_changes": 0,
    "channel_states": {key: "NOT_ATTEMPTED_NO_CURRENT_MAIN_SOURCE" for key in
                       ("substack", "telegram", "discord", "x", "linkedin", "facebook_page",
                        "instagram_business", "threads", "youtube")},
    "publication_feed": {**feed, "exact_bytes_unchanged": True},
    "inherited_work": preserved,
    "branch_base": base, "fresh_remote_default": remote,
    "base_reason": "Current Publisher operating HEAD contains the fetched remote default and installed Publisher fixes.",
    "configured_model": launch["configured_model"],
    "configured_reasoning_effort": launch["configured_reasoning_effort"],
    "telemetry_status": "CONFIGURED_NOT_OBSERVED",
    "verification": "Installed projection, original-clock, plan-export and daily-count consumers; all assertions passed.",
    "pytest": "Not run: no product code changed.",
    "status_after_run": "OPEN", "next_due_utc": due.isoformat(),
    "next_due_gmt7": due.astimezone(gmt7).strftime("%d %b %Y %H:%M GMT+7"),
    "next_actor": "Existing Publisher lane runner",
    "next_action": "At next due time, consume any new completed Main analysis using its original capture clock.",
    "choice": "End this bounded check without allocating an expired article; Main-only and original-clock rules apply.",
}
(HERE / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: result[key] for key in ("classification", "new_articles", "completed_sources", "next_due_gmt7")}))
