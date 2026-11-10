"""One bounded CC-124 source/readback check; writes only this run's evidence."""
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
MAIN = Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-research")
TOWER = Path(r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower")
sys.path.insert(0, str(LIVE))
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.plan_status_posts_v1 import read_export
from live_contentops.published_content_v1 import read_records
from live_contentops.published_images_v1 import PublishedImages, daily_limit, day_of


def save(name, value):
    target = HERE / name
    assert not target.exists(), "Preserve the first observation: " + str(target)
    target.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def file_info(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
            "modified_at_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()}


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


now = datetime.now(timezone.utc)
now_utc = now.isoformat().replace("+00:00", "Z")
release = datetime(2026, 11, 10, 13, 30, tzinfo=timezone.utc)
assert now < release, "Use a new observation after the release; never backdate this check."

preserved_path = HERE / "preserved-work.json"
if preserved_path.exists():
    preserved = json.loads(preserved_path.read_bytes())
else:
    preserved = []
    for root in (BUILDER, LIVE):
        for name in git(root, "diff", "--name-only").splitlines():
            preserved.append({"root": str(root), "relative_path": name, **file_info(root / name)})
    save("preserved-work.json", preserved)

operation = RUNTIME / "daily_app_outputs/owner-manual/cc338-cpi-preview-20261110-v1"
request_path = operation / "desktop_request_write.json"
request = json.loads(request_path.read_bytes())
assert request["request_sha256"] == sha256_of({k: v for k, v in request.items() if k != "request_sha256"})
binding_path = operation / "binding.json"
binding = json.loads(binding_path.read_bytes())
research_source = next(s for s in request["governed_input"]["source_pack"] if s.get("report_lineage"))
lineage = research_source["report_lineage"]
assert sha256(Path(lineage["source_path"]).read_bytes()).hexdigest() == lineage["source_sha256"]

daily_root = MAIN / "daily-research-portfolio-279805139/requests"
daily = sorted(daily_root.glob("*/owner-native.json"), key=lambda p: p.stat().st_mtime, reverse=True)
cpi_root = MAIN / "20261110-cpi"
cpi = sorted(cpi_root.glob("*/owner-native.json"), key=lambda p: p.stat().st_mtime, reverse=True)
assert daily and cpi
preview_publication = datetime.fromisoformat("2026-11-10T12:09:49.251+00:00")
main_rows = [{"kind": kind, **file_info(path)} for kind, paths in (("daily", daily[:6]), ("CPI dossier", cpi)) for path in paths]
for row in main_rows:
    row["modified_after_preview_publication"] = datetime.fromisoformat(row["modified_at_utc"]) > preview_publication
assert not any(r["modified_after_preview_publication"] for r in main_rows)

other_roots = [
    MAIN / "brain-runs", MAIN / "t2-runs",
    Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-events-20261029"),
    BUILDER / "data/research", LIVE / "data/research",
    Path(r"A:\Capital Chronicle\Worktrees\codex-data-backlog\data/research"),
]
other_rows = []
for root in other_roots:
    files = []
    if root.exists():
        for pattern in ("*/owner-native.json", "*/*/owner-native.json", "t2-*/t2-output.json", "*cpi*", "*CPI*"):
            files.extend(p for p in root.glob(pattern) if p.is_file())
    selected = sorted(set(files), key=lambda p: p.stat().st_mtime, reverse=True)[:6]
    other_rows.append({"root": str(root), "exists": root.exists(), "selected_files": [file_info(p) for p in selected]})

backlog_search = []
for name in ("BACKLOG.md", "BACKLOG_ARCHIVE.md"):
    path = TOWER / name
    lines = path.read_text(encoding="utf-8").splitlines()
    matches = [{"line": i + 1, "text": line[:800]} for i, line in enumerate(lines)
               if ("CPI" in line or "CC-124" in line) and any(term in line.lower() for term in ("review", "report", "wrap", "decision 89", "decision 98"))]
    backlog_search.append({"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest(),
                           "match_count": len(matches), "matches": matches[-20:]})

export = read_export()
plans = export["status"]["plans"]
latest_plans = {}
for plan in plans:
    asset = plan.get("asset_id")
    if asset not in latest_plans or plan.get("registered_at_utc", "") > latest_plans[asset].get("registered_at_utc", ""):
        latest_plans[asset] = plan
plan_summary = [{"asset_id": asset, "registered_at_utc": p.get("registered_at_utc"),
                 "base_probability_pct": (p.get("scenario_analysis", {}).get("base_case") or {}).get("probability_pct"),
                 "alternative_probability_pct": (p.get("scenario_analysis", {}).get("main_alternative") or {}).get("probability_pct"),
                 "scenario_first_cause": p.get("scenario_first_cause")}
                for asset, p in sorted(latest_plans.items(), key=lambda row: str(row[0]))]

feed_path = RUNTIME / "published_content_v1.jsonl"
feed_before = file_info(feed_path)
feed = read_records(feed_path)
preview = next(r for r in feed if r["content_id"] == "substack:224293572")
register = PublishedImages(RUNTIME / "published_images_v1.jsonl", published_feed=feed_path)
articles = sorted(register._daily_pieces(register.records(), now))
with sqlite3.connect((RUNTIME / "contentops_daily_app_v1.sqlite3").as_uri() + "?mode=ro", uri=True) as conn:
    conn.row_factory = sqlite3.Row
    leases = [dict(r) for r in conn.execute("SELECT lease_id,lease_key,status,expires_at FROM leases WHERE status='ACTIVE' AND expires_at>?", (now_utc,))]
assert not leases

command = [sys.executable, "scripts/run_native_desktop_editorial.py", "publication-status", "--binding", str(binding_path), "--rollout", "config/native_desktop_rollout_v1.json"]
observed = subprocess.run(command, cwd=LIVE, text=True, capture_output=True, timeout=45)
assert observed.returncode == 0, "Read-only publication-status failed: " + observed.stderr[-400:]
status = json.loads(observed.stdout)
if status.get("classification") == "TOOL_OUTPUT_IN_FILE":
    reference = status["output"]
    full_output = Path(reference["path"]).read_bytes()
    assert sha256(full_output).hexdigest() == reference["sha256"]
    status = json.loads(full_output)
allowed = ("classification", "run_id", "article_identity", "publication_state", "status", "destinations", "channel_states", "first_blocking_cause", "unknown_write_count", "pending_native_requests", "pending_tool_requests", "channels")
status_summary = {k: status[k] for k in allowed if k in status}
save("publication-status.json", status_summary)

source = {"observed_at_utc": now_utc, "latest_daily_and_cpi_reports": main_rows,
          "additional_held_outputs_searched": other_rows, "backlog_search": backlog_search,
          "published_preview": {k: preview.get(k) for k in ("content_id", "title", "published_at_utc")},
          "preview_research_binding": lineage, "preview_writer_request": file_info(request_path),
          "preview_binding": file_info(binding_path), "main_export_generated_at_utc": export["status"]["generated_at_utc"],
          "latest_public_plan_scenarios": plan_summary,
          "interpretation": "The newest daily and CPI dossier returns precede the published preview. CPI is still in the future at this observation; no post-release Main review can yet describe its outcome. Older pre-release analysis remains usable, with its original date, and was considered for this choice."}
save("source-comparison.json", source)

verified = {"operating_modules": {name: str(sys.modules[name].__file__) for name in (
    "live_contentops.plan_status_posts_v1", "live_contentops.published_content_v1", "live_contentops.published_images_v1")},
    "preview_request_hash_valid": True, "preview_research_hash_valid": True,
    "publication_status_cli_succeeded": True, "new_operations": 0, "model_calls": 0,
    "public_writes": 0, "test_processes": 0, "chat_messages": 0, "schedule_changes": 0,
    "feed_unchanged": file_info(feed_path)["sha256"] == feed_before["sha256"],
    "inherited_work_unchanged": all(file_info(Path(r["path"]))["sha256"] == r["sha256"] for r in preserved)}
assert verified["feed_unchanged"] and verified["inherited_work_unchanged"]
save("verification.json", verified)

result = {"item": "CC-124", "observed_at_utc": now_utc, "new_articles": 0,
    "production_date": day_of(now), "daily_article_limit": daily_limit(now), "published_canonicals": articles,
    "active_leases": leases, "operating_head": git(LIVE, "rev-parse", "HEAD"),
    "builder_head_before_evidence": git(BUILDER, "rev-parse", "HEAD"), "remote_default_head": git(BUILDER, "rev-parse", "origin/master"),
    "configured_launch": {"process_id": 22544, "model": "gpt-6.1-sol", "effort": "max", "state": "CONFIGURED_NOT_OBSERVED"},
    "choice": "Today's CPI preview already serves as the decision-98 wrap. Choose the next useful piece as a Main-sourced post-CPI review rather than a second pre-release wrap; decision 89 requires Main reports and no filler.",
    "first_cause": "CPI_NOT_RELEASED_AND_POST_RELEASE_MAIN_REVIEW_NOT_YET_AVAILABLE",
    "authority": ["JIM_DECISION_89", "JIM_DECISION_98"], "release_time_utc": release.isoformat(),
    "standing_status": "OPEN", "next_due_gmt7": "11 Nov 2026 02:14 GMT+7",
    "next_action": "At the next eligible run, consume the Main post-CPI report through the existing source-review and publication owners; keep the two-article cap and the published preview's exact identity.",
    "acceptance": "This source-check sub-step is verified; no new published article or CC-124 publication acceptance is claimed.",
    "tests": "No tests started during the 10 November 18:30-22:30 GMT+7 blackout. No runtime code changed."}
save("result.json", result)
print(json.dumps({k: result[k] for k in ("new_articles", "production_date", "daily_article_limit", "published_canonicals", "first_cause", "next_due_gmt7")}))
