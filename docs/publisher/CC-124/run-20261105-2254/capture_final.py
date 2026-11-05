"""Retain verified current consumer results and destination-local limitations."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
consumer = json.loads((ROOT / "live-consumer-acceptance.json").read_bytes())
publication = consumer["publication"]
digest = json.loads((ROOT / "digest-consumer-acceptance.json").read_bytes())
assert publication["unknown_write_count"] == 0 and not publication["pending_requests"]
assert consumer["production_day_measurement"]["distinct_canonical_items_published"] == 7
assert digest["observed_reader_result"]["state"] == "SAVED_RECORD"
assert digest["observed_reader_result"]["distinct_articles_published"] == 7
assert publication["derivative_confirmed_count"] == 7
assert publication["additional_confirmed_count"] == 1
checks = {}
for name in ("coordinator-regression.xml", "indexed-store-tests.xml", "scoped-recovery-tests.xml",
             "recovered-context-consumers.xml"):
    node = ET.parse(ROOT / name).getroot()
    suites = [node] if node.tag == "testsuite" else list(node)
    assert all(int(s.get("failures", 0)) == int(s.get("errors", 0)) == 0 for s in suites)
    checks[name] = {"tests": sum(int(s.get("tests", 0)) for s in suites), "failures": 0, "errors": 0}
head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
live_head = subprocess.run(["git", "-C", r"A:\Capital Chronicle\ContentOps", "rev-parse", "HEAD"],
    capture_output=True, text=True, check=True).stdout.strip()
assert head == live_head
outcome = {"recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    "operation_id": "cc124-nfp-us500-preview-20261105-g", "article_identity": publication["article_identity"],
    "canonical_url": publication["canonical_url"], "published_at_utc": "2026-11-05T16:48:08.853Z",
    "distinct_articles_published": 7, "daily_target": 8, "standing_item_status": "OPEN",
    "implemented_pushed_integrated_head": head, "live_consumer_state": "SAVED_RECORD",
    "confirmed_routine_derivatives": 7, "confirmed_additional_linkedin_company": 1,
    "unknown_write_count": 0, "pending_tool_requests": 0,
    "destinations": [{k: d.get(k) for k in ("destination", "status", "reconciliation_status",
        "public_object_id", "public_object_url")} for d in publication["destinations"]],
    "tests": checks, "limitations": [
        "LinkedIn personal: two official API attempts raised LinkedInAmbiguousWriteError; authenticated own-activity readbacks confirmed absence after each. RECONCILED_ABSENT_SAFE_TO_RETRY.",
        "LinkedIn-only dated Neo recovery prepared; screenshot capture returned CDP request timed out: Page.captureScreenshot. No recovery send or invented review acceptance.",
        "15-minute distribution target missed; original text approval remains 2026-11-05T16:38:22.436512+00:00."],
    "next_action": "Publisher resumes the retained LinkedIn-only Neo recovery after actual MAX review and fresh absence; never recreate the canonical article.",
    "schedule_changed": False, "chat_messages_sent": False, "unrelated_wip_preserved": True}
(ROOT / "run-outcome.json").write_text(json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"path": str(ROOT / "run-outcome.json"), "day_count": 7,
    "confirmed_routine_derivatives": 7, "additional_company_copy": 1,
    "unknown_write_count": 0, "pending_tool_requests": 0, "tests": checks}))
