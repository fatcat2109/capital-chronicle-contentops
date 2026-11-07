"""Use the installed source and Main-export consumers for this retained piece."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))

from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.plan_status_posts_v1 import read_export

def find(value, key, pointer=""):
    if isinstance(value, dict):
        for name, child in value.items():
            at = pointer + "/" + name
            if name == key:
                yield {"pointer": at, "value": child}
            else:
                yield from find(child, key, at)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from find(child, key, pointer + "/" + str(index))

now = datetime.now(timezone.utc)
research = RetainedSourceResearch(LIVE / "docs/publisher/CC-124/run-20261106-2050/source")
assert not research.gaps and len(research.records) == 3
check = json.loads((HERE / "resume-check.json").read_bytes())
sources = [{"headline_id": key, "known_at_utc": value["known_at_utc"],
            "revision_at_utc": value["revision_at_utc"],
            "content_sha256": value["document"]["canonical_content_sha256"],
            "public_claim_allowed": value["document"]["public_claim_allowed"]}
           for key, value in research.records.items()]
export = read_export()
scenarios = list(find(export, "scenario_analysis"))
trace_path = Path(r"A:\Capital Chronicle\Worktrees\codex-main-exec-b\tests\evidence\cc-330\scenarios-20261106.json")
trace = json.loads(trace_path.read_bytes())
trace_scenarios = list(find(trace, "scenario_analysis"))
native_path = Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-research\20261106-nfp\dossier-20261106T093133Z\owner-native.json")
native = json.loads(native_path.read_bytes())
conditional_estimates = []
for candidate in native["candidates"]:
    text = candidate["rationale"]
    match = re.search(r"Base case, conditional on (STRONG|WEAK):.*?hence STARTER\.", text)
    assert match
    conditional_estimates.append({"candidate_id": candidate["candidate_id"],
        "source_pointer": "/candidates/" + str(len(conditional_estimates)) + "/rationale",
        "support_excerpt": match.group(),
        "interpretation": "Conditional direction assessment; not the probability of that release outcome."})
daily_root = Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-research\daily-research-portfolio-279805139\requests")
daily_paths = sorted(daily_root.glob("*/owner-native.json"), key=lambda p: p.stat().st_mtime, reverse=True)
latest = daily_paths[0]
launch = check["configured_launch"]
next_due = datetime.fromisoformat(launch["started_utc"].replace("Z", "+00:00")) + timedelta(hours=12)
result = {
    "observed_at_utc": now.isoformat(), "item": "CC-124",
    "classification": "SOURCE_BLOCKED", "first_cause": "JIM_DECISION_93_MAIN_SCENARIOS_INCOMPLETE",
    "restriction_reason": "no-red-tape 2d: Jim decision 93 explicitly requires Main-supplied scenario probabilities and six-market implications; rule 8 forbids invented values.",
    "choice": "Retain the NFP operation and all accepted work; prepare the held source comparison and make no incomplete public post.",
    "source_adapter": {"root": str(research.root), "revision": research.revision, "gaps": research.gaps, "verified_records": sources},
    "installed_main_export_consumer": "live_contentops.plan_status_posts_v1.read_export",
    "public_export_scenarios": scenarios,
    "main_lane_trace": {"path": str(trace_path), "sha256": sha256(trace_path.read_bytes()).hexdigest(), "scenarios": trace_scenarios},
    "full_nfp_report": {"path": str(native_path), "sha256": sha256(native_path.read_bytes()).hexdigest(),
                        "conditional_direction_estimates": conditional_estimates,
                        "scenario_assumptions": native["scenario_assumptions"]},
    "latest_daily_main_report": {"path": str(latest), "sha256": sha256(latest.read_bytes()).hexdigest(),
                                 "file_modified_at_utc": datetime.fromtimestamp(latest.stat().st_mtime, timezone.utc).isoformat()},
    "daily_main_report_count_searched": len(daily_paths),
    "searched": ["Full NFP dossier, Primary, Critical, Synthesis and integrated decision",
                 "Current accepted daily Main requests and six latest complete owner-native reports",
                 "Current Main public-report export manifest and live plan-status export",
                 "Main CC-330 scenario evidence in codex-main-exec-b",
                 "ContentOps held Main/official release/sector research and recent Main-only article sources",
                 "BACKLOG.md and BACKLOG_ARCHIVE.md", "ContentOps data/research (absent)"],
    "binding_path": check["binding_path"], "binding_file_sha256": check["binding_file_sha256"],
    "writer_request_sha256": check["writer_request_sha256"],
    "writer_request_file_sha256": check["writer_request_file_sha256"],
    "production_date": check["production_date"], "daily_article_limit": check["article_limit"],
    "occupied_article_slots": check["occupied_article_slots"],
    "new_publications": 0, "new_model_calls": 0, "new_source_requests": 0,
    "new_media": 0, "test_runs": 0,
    "next_due_utc": next_due.isoformat(),
    "next_action": "Main supplies the post-release base case and main alternative with explicit scenario probabilities and six-market implications; Publisher consumes the dated version at the next eligible standing run. Do not convert conditional trade-direction assessments or weights into release-scenario probabilities.",
    "next_actor": "Main report producer; then Codex Publisher",
    "schedules_changed": False, "chat_messages_sent": False, "desktop_control_used": False,
}
(HERE / "source-readiness.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"classification": result["classification"], "first_cause": result["first_cause"],
                  "verified_source_records": len(sources), "export_scenario_records": len(scenarios),
                  "conditional_direction_estimates": conditional_estimates, "next_due_utc": result["next_due_utc"]}))
