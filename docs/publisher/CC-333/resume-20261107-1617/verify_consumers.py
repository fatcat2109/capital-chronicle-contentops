"""Read installed CC-333 consumers and compare the retained Main source evidence."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TREE = HERE.parents[3]
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
PRIOR = TREE / "docs/publisher/CC-124/run-20261107-1533"
sys.path.insert(0, str(LIVE))

from live_contentops import article_publication_quality_v1 as quality
from live_contentops import article_scenarios_v1 as scenarios
from live_contentops import published_images_v1 as images
from live_contentops import tradingview_snapshot_v1 as tradingview
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.native_publication_promotion_v1 import ReadOnlyStore
from live_contentops.plan_status_posts_v1 import read_export
from live_contentops.published_content_v1 import read_records


def file_hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def fields(value, key, pointer=""):
    if isinstance(value, dict):
        for name, child in value.items():
            at = pointer + "/" + name
            if name == key:
                yield at, child
            else:
                yield from fields(child, key, at)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from fields(child, key, pointer + "/" + str(index))


now = datetime.now(timezone.utc)
prior = json.loads((PRIOR / "source-readiness.json").read_bytes())
source_checks = []
for source in json.loads((PRIOR / "main-scenario-search.json").read_bytes()):
    actual = file_hash(source["source"])
    source_checks.append({"path": source["source"], "sha256": actual,
                          "unchanged_since_due_run": actual == source["sha256"]})
assert all(row["unchanged_since_due_run"] for row in source_checks), "MAIN_SOURCE_CHANGED_REQUIRES_REVIEW"

daily_root = Path(prior["latest_daily_main_report"]["path"]).parents[1]
daily = sorted(daily_root.glob("*/owner-native.json"), key=lambda p: p.stat().st_mtime, reverse=True)
assert str(daily[0]) == prior["latest_daily_main_report"]["path"], "NEW_MAIN_REPORT_REQUIRES_REVIEW"
assert file_hash(daily[0]) == prior["latest_daily_main_report"]["sha256"]
research = RetainedSourceResearch(LIVE / "docs/publisher/CC-124/run-20261106-2050/source")
assert not research.gaps and len(research.records) == 3

export = read_export()
export_scenarios = list(fields(export, "scenario_analysis"))
missing_alternative = [pointer for pointer, value in export_scenarios
                       if not isinstance(value, dict)
                       or (value.get("main_alternative") or {}).get("probability_pct") is None]
assert export_scenarios and len(missing_alternative) == len(export_scenarios), "MAIN_SCENARIO_EXPORT_CHANGED_REQUIRES_REVIEW"

operation = RUNTIME / "daily_app_outputs/owner-manual/cc124-nfp-arrival-review-20261106-v1"
binding_path = operation / "binding.json"
request_path = operation / "desktop_request_write.json"
binding = json.loads(binding_path.read_bytes())
request = json.loads(request_path.read_bytes())
assert file_hash(binding_path) == prior["binding_file_sha256"]
assert file_hash(request_path) == prior["writer_request_file_sha256"]
assert request["request_sha256"] == sha256_of({k: v for k, v in request.items() if k != "request_sha256"})

feed_path = RUNTIME / "published_content_v1.jsonl"
feed = read_records(feed_path)
register = images.PublishedImages(RUNTIME / "published_images_v1.jsonl", published_feed=feed_path)
registered = register.records()
occupied = register._daily_pieces(registered, now)
store = ReadOnlyStore(RUNTIME / "contentops_daily_app_v1.sqlite3")
dispatches = [{"platform": d["platform"], "status": d["status"]}
              for identity in (binding["run_id"], "cc-opportunity-" + sha256_of(binding["run_id"]))
              for d in store.get_dispatches_for_work_item(identity)]
post_policy = [row for row in feed if datetime.fromisoformat(row["published_at_utc"].replace("Z", "+00:00")) >= quality.EFFECTIVE_FROM]
assert not post_policy and not dispatches

modules = [quality, scenarios, images, tradingview]
installed = []
live_tag = "contentops-live-20261107-cc333-r2"
for module in modules:
    path = Path(module.__file__)
    relative = path.relative_to(LIVE).as_posix()
    actual = file_hash(path)
    # Git stores LF while a Windows checkout can contain CRLF. Retain both raw
    # file hashes and verify each through Git's normal newline conversion.
    live_blob = git(LIVE, "hash-object", str(path))
    builder_blob = git(TREE, "hash-object", str(TREE / relative))
    tag_blob = git(LIVE, "rev-parse", live_tag + ":" + relative)
    assert live_blob == tag_blob == builder_blob
    installed.append({"path": relative, "sha256": actual, "builder_sha256": file_hash(TREE / relative), "git_blob": live_blob,
                      "matches_live_tag_and_builder": True})

baseline = json.loads((TREE / "docs/publisher/CC-333/resume-20261107/integration-before.json").read_bytes())
wip = {}
for root, state in baseline["roots"].items():
    wip[root] = {relative: {"sha256": file_hash(Path(root) / relative),
                           "unchanged": file_hash(Path(root) / relative) == value["sha256"]}
                 for relative, value in state["dirty"].items()}
assert all(value["unchanged"] for rows in wip.values() for value in rows.values())

launch_path = Path(r"A:\Capital Chronicle\ResearchRuns\claude-ops-integrations\codex-exec\publisher-cc-333-20261107T0916\launch.json")
launch = json.loads(launch_path.read_bytes())
result = {
    "item": "CC-333", "observed_at_utc": now.isoformat(), "verification": "PASS",
    "operating_head": git(LIVE, "rev-parse", "HEAD"), "builder_head": git(TREE, "rev-parse", "HEAD"),
    "live_tag": live_tag, "rollback_tag": "contentops-rollback-20261107-cc333-r2",
    "installed_modules": installed,
    "verification_comparison_repair": "Git-normalized blob comparison replaces raw LF/CRLF equality; both raw file hashes are retained. No runtime check was changed.",
    "production_date": images.day_of(now), "daily_article_limit": images.daily_limit(now),
    "occupied_article_slots": len(occupied), "remaining_capacity": max(0, images.daily_limit(now) - len(occupied)),
    "publication_feed": str(feed_path), "feed_sha256": file_hash(feed_path), "feed_articles": len(feed),
    "latest_canonical_publication_utc": max(row["published_at_utc"] for row in feed),
    "image_register": str(register.path), "image_observation_records": len(registered),
    "post_policy_public_pieces": len(post_policy), "required_public_piece_readbacks": 2,
    "new_public_piece_readbacks": 0, "operation_dispatches": dispatches,
    "verified_held_source_records": len(research.records), "held_source_revision": research.revision,
    "main_export_scenario_records": len(export_scenarios),
    "main_alternative_probability_absent": len(missing_alternative), "missing_probability_pointers": missing_alternative,
    "held_main_source_checks": source_checks, "completed_daily_reports_in_catalog": len(daily),
    "latest_daily_main_report": prior["latest_daily_main_report"],
    "source_comparison_evidence": str(PRIOR / "source-readiness.json"),
    "operation_id": binding["run_id"], "binding_file_sha256": file_hash(binding_path),
    "pending_writer_request_sha256": request["request_sha256"], "writer_request_file_sha256": file_hash(request_path),
    "writer_return_present": (operation / "desktop_response_write.json").exists(),
    "first_cause": "JIM_DECISION_93_MAIN_SCENARIOS_INCOMPLETE",
    "restriction_reason": "no-red-tape 2d: decision 93 requires Main-supplied probabilities, confirmation, six-market implications and invalidation for 2-3 scenarios; host rule 8 forbids invented values.",
    "choice": "Retain the existing NFP operation; use its held facts for source comparison and do not invent the missing scenario probabilities or a complement.",
    "next_actor": "Main report producer, then Codex Publisher at the next eligible CC-124 run",
    "next_action": "Main supplies a dated complete base/alternative scenario set; Publisher consumes it through the existing editorial/publication owners and retains exact Substack/social readbacks for the next two compliant pieces.",
    "next_cc124_due_gmt7": "8 Nov 2026 03:34 GMT+7",
    "configured_launch": {"path": str(launch_path), "model": launch["model"],
                          "effort": launch["reasoning_effort"], "provenance": "CONFIGURED_NOT_OBSERVED"},
    "inherited_files": wip, "editorial_model_calls": 0, "new_public_writes": 0,
    "pytest_runs": 0, "runtime_code_changed": False, "schedules_changed": False,
    "chat_messages_sent": False, "native_desktop_control_used": False,
}
(HERE / "consumer-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: result[key] for key in ("verification", "operating_head", "remaining_capacity",
    "main_export_scenario_records", "main_alternative_probability_absent", "post_policy_public_pieces", "first_cause")}))
