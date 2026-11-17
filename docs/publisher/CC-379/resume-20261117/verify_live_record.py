"""Verify the installed weekly source/reader with Main's current public export.

This saves source evidence, not an authored article or publication request.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
sys.path.insert(0, str(LIVE))

from live_contentops import weekly_scored_calls_v1 as weekly
from live_contentops.plan_status_posts_v1 import _utc, read_export
from live_contentops import v1_simple_gemini_newsroom_v1 as newsroom


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def info(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


now = datetime.now(timezone.utc)
export = read_export()
record = weekly.project(export, cutoff_utc=now.isoformat())
assert record["week_start_et"] == "2026-11-09T00:00:00-05:00"
assert record["week_end_exclusive_et"] == "2026-11-14T00:00:00-05:00"
start, end = weekly.week_window(now.isoformat())
expected = {
    p["plan_id"]: p for p in export["status"]["plans"]
    if p.get("outcome", {}).get("state") == "SCORED"
    and start <= _utc(p["outcome"]["score"]["resolved_at_utc"]) < end
    and _utc(p["outcome"]["score"]["scored_at_utc"]) <= now
}
actual = {r["plan_id"]: r for r in record["rows"] if r["scored"]}
assert actual.keys() == expected.keys()
for identity, source in expected.items():
    row = actual[identity]
    assert row["result"] == source["outcome"]["result"]
    assert row["market"] == source["asset_id"]
    assert row["direction"].upper() == source["direction"]
    assert row["zone"] == source["zone"]
    assert row["outcome_id"] == source["outcome"]["outcome_id"]
    assert row["score_hash"] == source["outcome"]["score"]["content_hash"]

doc = weekly.document(record, "SOURCE_1")
article = {"title": "Weekly source verification", "substack_body_markdown": record["text"]}
binding = weekly.validate_article(article, [doc])
article["weekly_scored_calls"] = binding
reader = newsroom._reader_safe_native_article(article, article_mode="STANDARD_NEWS_ANALYSIS")
assert reader["weekly_scored_calls"] == binding
assert all(row["line"] in reader["substack_body_markdown"] for row in record["rows"])
assert all(record["text"].count(row["line"]) == 1 for row in record["rows"])
save("weekly-call-record.json", record)
(HERE / "weekly-call-source.md").write_text(record["text"] + "\n", encoding="utf-8")

feed = RUNTIME / "published_content_v1.jsonl"
published = [json.loads(line) for line in feed.read_text(encoding="utf-8").splitlines() if line]
recent = [{k: row.get(k) for k in ("content_id", "title", "published_at_utc", "outlets")}
          for row in published if _utc(row["published_at_utc"]) >= start]
assessment = json.loads((HERE / "source-check/source-assessment.json").read_bytes())
inventory = json.loads((HERE / "source-check/inventory-result.json").read_bytes())
latest = assessment["latest_completed_analysis"]
assert inventory["eligible_completed_sources"] == 0
assert latest["publication_clock_cause"].startswith("ARTICLE_DATA_CUTOFF_EXPIRED:")

preserved = json.loads((HERE / "source-check/preserved-work.json").read_bytes())
for row in preserved:
    assert info(Path(row["path"]))["sha256"] == row["sha256"], row["path"]
before = json.loads((HERE / "source-check/installed-consumers.json").read_bytes())["publication_feed_before"]
assert info(feed) == before
save("installed-verification.json", {
    "observed_at_utc": now.isoformat(),
    "operating_root": str(LIVE),
    "operating_head": subprocess.check_output(["git", "-C", str(LIVE), "rev-parse", "HEAD"], text=True).strip(),
    "source_consumer": info(Path(weekly.__file__)),
    "record": info(HERE / "weekly-call-record.json"),
    "source_document_sha256": doc["canonical_content_sha256"],
    "counts": record["counts"], "cumulative_export_scored_calls": record["export_scored_call_count"],
    "exact_scored_membership_and_outcomes": True,
    "complete_record_validated_by_installed_article_owner": True,
    "all_rows_consumed_by_installed_reader": True,
    "authored_article_created": False, "editorial_model_calls": 0,
    "publication_feed": info(feed), "recent_publications": recent,
    "source_assessment": info(HERE / "source-check/source-assessment.json"),
    "completed_main_reports": inventory["completed_source_count"],
    "eligible_main_reports": inventory["eligible_completed_sources"],
    "latest_main_source": {k: latest.get(k) for k in (
        "path", "sha256", "capture_known_at_utc", "publication_clock_cause", "publication_deadline_utc")},
    "remaining_acceptance": "Substack weekly review containing every 9-13 November row and count; no such wrap observed.",
    "first_current_cause": "NO_TIMELY_MAIN_WRAP_SOURCE",
    "reason_to_restrict_fresh_publication": "JIM_DECISION_114 / CC-403 original data cutoff +60 minutes",
    "next_action": "Publisher includes this complete dated record through the existing weekly source hook when the next timely Main wrap source arrives; preserve the actual later publication date and missed original deadline.",
    "inherited_modified_files_verified_unchanged": len(preserved),
    "public_writes": 0, "schedule_changes": 0, "chat_messages": 0,
})
print(json.dumps({"counts": record["counts"], "rows": len(record["rows"]),
    "installed_reader_consumed_all": True, "latest_main_source_cause": latest["publication_clock_cause"],
    "eligible_main_reports": inventory["eligible_completed_sources"], "inherited_files_unchanged": len(preserved)}))
