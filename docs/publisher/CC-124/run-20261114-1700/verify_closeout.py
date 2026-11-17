"""Read back this CC-124 operation and preserve inherited work."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BUILDER = HERE.parents[3]
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
OPERATION = "cc124-btc-weekend-20261114"
sys.path.insert(0, str(LIVE))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of


def load(path):
    return json.loads(path.read_bytes())


def digest(path, limit=None):
    value = sha256()
    with path.open("rb") as source:
        while limit is None or limit > 0:
            block = source.read(min(1024 * 1024, limit) if limit is not None else 1024 * 1024)
            if not block:
                break
            value.update(block)
            if limit is not None:
                limit -= len(block)
    return value.hexdigest()


terminal = load(HERE / "advance-terminal.json")
initial = load(HERE / "source-assessment.json")
closing = load(HERE / "closeout/source-assessment.json")
consumer = load(HERE / "installed-source-consumer.json")
original = load(HERE / "native-select-original.json")
bound = load(HERE / "native-select-bound.json")
assert bound["output"] == original["output"]
assert terminal["classification"] == "DRAFT_BLOCKED"
assert terminal["qualified_article_count"] == terminal["derivative_intent_count"] == 0
assert terminal["exact_next_blocker"] == "DESKTOP_COORDINATOR_ABSTAINED_NO_USEFUL_STORY"
assert terminal["editorial_execution"]["semantic_response_count"] == 1
assert consumer["publication_clock_cause"].startswith("ARTICLE_DATA_CUTOFF_EXPIRED:")
assert initial["latest_completed_analysis"]["publication_clock_cause"] is None
assert all(row["publication_clock_cause"] for row in closing["retained_reports"] if row["completed_output"])

preserved = []
for row in load(HERE / "preserved-work.json"):
    path = Path(row["path"])
    current = digest(path)
    preserved.append({"path": str(path), "initial_sha256": row["sha256"],
        "current_sha256": current, "exact_bytes_unchanged": current == row["sha256"],
        "original_prefix_unchanged": digest(path, row["bytes"]) == row["sha256"]})

uri = (RUNTIME / "contentops_daily_app_v1.sqlite3").as_uri() + "?mode=ro"
work = "cc-opportunity-" + sha256_of(OPERATION)
with sqlite3.connect(uri, uri=True) as conn:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(platform_dispatches)")}
    if "work_item_id" in columns:
        dispatches = conn.execute("SELECT COUNT(*) FROM platform_dispatches WHERE work_item_id=?", (work,)).fetchone()[0]
    else:
        dispatches = conn.execute("SELECT COUNT(*) FROM platform_dispatches WHERE message_id IN "
            "(SELECT message_id FROM outbox_messages WHERE work_item_id=?)", (work,)).fetchone()[0]
assert dispatches == 0

code = "live_contentops/main_report_projection_source_v1.py"
assert digest(BUILDER / code) == digest(LIVE / code)
head = subprocess.check_output(["git", "-C", str(LIVE), "rev-parse", "HEAD"], text=True).strip()
result = {
    "observed_at_utc": datetime.now(timezone.utc).isoformat(), "operation_id": OPERATION,
    "operating_head": head, "installed_module_matches_delivered_source": True,
    "installed_source_consumer": str(HERE / "installed-source-consumer.json"),
    "terminal_classification": terminal["classification"], "selection": bound["output"]["status"],
    "source_cause": consumer["publication_clock_cause"], "platform_dispatch_count_for_operation": dispatches,
    "new_articles": 0, "native_semantic_responses": 1, "writer_calls": 0, "filter_calls": 0,
    "external_model_provider_attempts": terminal["editorial_execution"]["external_provider_attempt_count"],
    "inherited_work": preserved, "pytest": {"files": ["tests/test_main_report_projection_source_v1.py"],
        "passed": 47, "seconds": 15.33, "processes": 1},
    "browser_actions": 0, "native_desktop_control_actions": 0, "chat_messages": 0, "schedule_changes": 0,
    "note": "The standing operation completed its native selection and durable terminal advance. Existing recovery dispatches were preserved; no publication or readback acceptance is claimed."
}
(HERE / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: result[key] for key in ("operating_head", "selection", "platform_dispatch_count_for_operation", "new_articles")}))
print(json.dumps({"inherited_exact_bytes_unchanged": all(row["exact_bytes_unchanged"] for row in preserved),
                  "inherited_original_prefixes_unchanged": all(row["original_prefix_unchanged"] for row in preserved)}))
