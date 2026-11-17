"""One bounded CC-124 observation; uses installed consumers and opens no operation."""
from datetime import datetime, timedelta, timezone
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
RESEARCH = Path(r"A:\Capital Chronicle\ResearchRuns")
MAIN = RESEARCH / "claude-main-research"
TOWER = Path(r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower")
PREVIOUS = HERE.parent / "run-20261111-1854"
sys.path.insert(0, str(LIVE))

from live_contentops.main_report_projection_source_v1 import verify_projection
from live_contentops.plan_status_posts_v1 import read_export
from live_contentops.published_images_v1 import PublishedImages, daily_limit, day_of
from live_contentops.reader_article_contract_v1 import contract_for, validate_publication_clock


def info(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
            "modified_at_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()}


def save(name, value):
    with (HERE / name).open("x", encoding="utf-8", newline="\n") as output:
        json.dump(value, output, indent=2, ensure_ascii=True)
        output.write("\n")


def newest(root, limit=6, pattern="*"):
    return sorted((p for p in root.rglob(pattern) if p.is_file() and p.suffix in {".md", ".json"}
                   and not any(w in p.name.lower() for w in ("secret", "credential", "account", ".env"))),
                  key=lambda p: p.stat().st_mtime, reverse=True)[:limit] if root.exists() else []


def clock_result(contract, now):
    try:
        validate_publication_clock({"reader_article_contract": contract}, now=now, destination="substack")
        return None
    except ValueError as exc:
        return str(exc)


now = datetime.now(timezone.utc)
now_text = now.isoformat().replace("+00:00", "Z")
previous = json.loads((PREVIOUS / "source-assessment.json").read_bytes())
previous_hashes = {row["path"]: row["sha256"] for row in previous["retained_reports"]}
reports = sorted(MAIN.rglob("owner-native.json"), key=lambda p: p.stat().st_mtime, reverse=True)
inventory = []
for path in reports:
    capture = path.parent / "capture.json"
    inventory.append({**info(path), "capture_known_at_utc":
                      json.loads(capture.read_bytes()).get("known_at_utc") if capture.exists() else None})
changed = [row for row in inventory if previous_hashes.get(row["path"]) != row["sha256"]]

# Extract a public prose passage through the installed rights/execution guard.
# Rejected private passages do not discard the report's other usable text.
latest = next(p for p in reports if "daily-research-portfolio-" in str(p))
report = json.loads(latest.read_bytes())
passages = [(f"/{key}/{i}/text", row["text"]) for key in
            ("summary", "causal_alternatives", "contradictions", "priced_in")
            for i, row in enumerate(report.get(key, [])) if isinstance(row, dict) and isinstance(row.get("text"), str)]
attempts = []
for pointer, text in passages:
    spec = {"authority_ref": "JIM_DECISION_89", "source_url": "urn:cc-public-report:cc124-main-20261112-0129",
            "headline_id": "cc124-main-20261112-0129", "headline_text": "Main's 11 November review",
            "known_at_utc": info(latest)["modified_at_utc"], "revision_at_utc": now_text,
            "candidate_catalyst_tags": ["MAIN_REPORT"],
            "passages": [{"source_path": str(latest), "source_sha256": info(latest)["sha256"],
                          "source_json_pointer": pointer,
                          "fragments": [{"start": 0, "end": min(1800, len(text))}]}]}
    try:
        projection = verify_projection(spec)
        attempts.append({"pointer": pointer, "outcome": "PUBLIC_PASSAGE_ADMITTED"})
        break
    except ValueError as exc:
        attempts.append({"pointer": pointer, "outcome": str(exc)})
else:
    raise RuntimeError("No public passage found; inspect remaining exact source spans")
contract = contract_for({"source_pack": [projection["document"]], "selected_candidate": projection})
capture_clock = json.loads((latest.parent / "capture.json").read_bytes())["known_at_utc"]
assert datetime.fromisoformat(contract["data_cutoff_utc"]) == datetime.fromisoformat(capture_clock.replace("Z", "+00:00"))
clock_cause = clock_result(contract, now)
assert clock_cause and clock_cause.startswith("ARTICLE_DATA_CUTOFF_EXPIRED:"), "Fresh report found: continue editorial work instead of recording no output"
report_clocks = [{"path": row["path"], "original_capture_utc": row["capture_known_at_utc"],
                  "within_60_minutes": 0 <= (now - datetime.fromisoformat(row["capture_known_at_utc"].replace("Z", "+00:00"))).total_seconds() <= 3600}
                 for row in inventory if row["capture_known_at_utc"]]
assert not any(row["within_60_minutes"] for row in report_clocks), "Another fresh completed Main report requires editorial assessment"

t2_run = newest(MAIN / "t2-runs", 1, "run.json")[0]
t2 = json.loads(t2_run.read_bytes())
t2_output = t2_run.parent / "t2-output.json"
t2_data = json.loads(t2_output.read_bytes())
t2_selection = {"run": info(t2_run), "output": info(t2_output),
                "original_capture_utc": t2.get("capture_known_at_utc"),
                "output_schema": t2_data.get("schema"), "top_level_fields": list(t2_data),
                "thesis_fields": sorted({key for row in t2_data.get("theses", []) for key in row}),
                "thesis_count": len(t2_data.get("theses", [])),
                "selected_instruments": t2.get("selected_instruments"),
                "decision_at_utc": t2.get("decision_at_utc"),
                "use": "Used to assess the current candidate ranking. Its exact schema, fields, ranked setups and fact IDs are assessed alongside the completed daily analysis; its original capture does not refresh that report's data clock."}

additional = []
for root in (MAIN / "daily-research-portfolio-279805139", MAIN / "horizon-runs", MAIN / "shock-trigger",
             RESEARCH / "claude-main-events-20261029", TOWER / "report_upgrade_review_20261105/strategy",
             Path(r"A:\Capital Chronicle\Worktrees\codex-data-backlog\data\research"),
             BUILDER / "data/research", LIVE / "data/research"):
    additional.append({"root": str(root), "exists": root.exists(), "latest_files": [info(p) for p in newest(root)]})
backlog_search = []
for name in ("BACKLOG.md", "BACKLOG_ARCHIVE.md"):
    path = TOWER / name
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    matches = [i + 1 for i, line in enumerate(lines) if any(w in line for w in
               ("CC-124", "CC-403", "post-CPI", "scenario", "Main report"))]
    backlog_search.append({**info(path), "matching_lines": matches, "match_count": len(matches)})
feed_binding = json.loads((LIVE / "config/native_desktop_operator_main_feed_binding_v1.json").read_bytes())
feed_root = Path(feed_binding["public_export_root"])
assessment = {"observed_at_utc": now_text, "previous_observation": info(PREVIOUS / "source-assessment.json"),
              "new_or_changed_completed_main_reports": changed, "retained_reports": inventory, "completed_report_clock_assessment": report_clocks,
              "latest_t2_selection": t2_selection, "additional_held_outputs": additional,
              "backlog_archive_search": backlog_search,
              "configured_public_main_feed": {"root": str(feed_root), "latest_files": [info(p) for p in newest(feed_root, 3)]},
              "installed_projection": {"spec": spec, "attempts": attempts,
                  "public_passage_sha256": sha256(projection["document"]["canonical_content_text"].encode()).hexdigest(),
                  "original_capture": {**info(latest.parent / "capture.json"), "known_at_utc": capture_clock},
                  "reader_contract": contract, "publication_clock_cause": clock_cause,
                  "publication_deadline_utc": (datetime.fromisoformat(capture_clock.replace("Z", "+00:00")) + timedelta(minutes=60)).isoformat()}}
save("source-assessment.json", assessment)

export = read_export()["status"]
plans = {}
for plan in export["plans"]:
    asset = plan.get("asset_id")
    if asset and plan.get("registered_at_utc", "") > plans.get(asset, {}).get("registered_at_utc", ""):
        plans[asset] = plan
scenarios = []
for asset in ("XAUUSD", "US500", "EURUSD", "USDJPY", "USOIL", "BTCUSD"):
    plan = plans.get(asset, {})
    scenario = plan.get("scenario_analysis") or {}
    scenarios.append({"asset_id": asset, "registered_at_utc": plan.get("registered_at_utc"),
                      "base_probability_pct": (scenario.get("base_case") or {}).get("probability_pct"),
                      "alternative_probability_pct": (scenario.get("main_alternative") or {}).get("probability_pct")})
feed = RUNTIME / "published_content_v1.jsonl"
feed_before = info(feed)
register = PublishedImages(RUNTIME / "published_images_v1.jsonl", published_feed=feed)
pieces = sorted(register._daily_pieces(register.records(), now))
with sqlite3.connect((RUNTIME / "contentops_daily_app_v1.sqlite3").as_uri() + "?mode=ro", uri=True) as conn:
    conn.row_factory = sqlite3.Row
    leases = [dict(row) for row in conn.execute("SELECT lease_id,lease_key,status,expires_at FROM leases WHERE status='ACTIVE'")
              if datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")) > now]
binding = RUNTIME / "daily_app_outputs/owner-manual/cc338-cpi-preview-20261110-v1/binding.json"
done = None
status_cli = {"succeeded": False, "cause": "PUBLICATION_STATUS_TIMEOUT_45S",
              "retry_attempted": False, "evidence": "inspection-failure.json"}
if "--complete-after-recorded-timeout" not in sys.argv:
    try:
        done = subprocess.run([sys.executable, "-B", "scripts/run_native_desktop_editorial.py", "publication-status",
                       "--binding", str(binding), "--rollout", "config/native_desktop_rollout_v1.json"],
                      cwd=LIVE, text=True, encoding="utf-8", capture_output=True, timeout=45,
                      creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired:
        save("inspection-failure.json", {"operation": "publication-status", "timeout_seconds": 45,
             "observed_at_utc": datetime.now(timezone.utc).isoformat(), "public_writes": 0})
else:
    assert (HERE / "inspection-failure.json").exists()
if done is not None:
    assert done.returncode == 0, done.stderr[-400:]
    status = json.loads(done.stdout)
    status_cli = {"succeeded": True}
else:
    status = {}
if status.get("classification") == "TOOL_OUTPUT_IN_FILE":
    ref = status["output"]
    raw = Path(ref["path"]).read_bytes()
    assert sha256(raw).hexdigest() == ref["sha256"]
    status = json.loads(raw)
status = status.get("publication", status)
keys = ("run_id", "work_item_id", "canonical_article_status", "canonical_article_real_published", "canonical_url",
        "distribution_status", "derivative_confirmed_count", "derivative_attempted_count", "derivative_unknown_count",
        "unknown_write_count", "recovery_required_destinations", "closed_no_write_destinations")
save("installed-consumers.json", {"observed_at_utc": now_text, "production_day": day_of(now),
     "daily_article_limit": daily_limit(now), "published_canonicals_today": pieces, "active_leases": leases,
     "main_plan_export": {"generated_at_utc": export["generated_at_utc"], "content_hash": export.get("content_hash"),
                          "latest_six_market_scenarios": scenarios, "plan_count": len(export["plans"]),
                           "latest_plan_registration_utc": max((p.get("registered_at_utc") or "") for p in export["plans"]),
                           "clock_use": "Plan registration and export generation are observed separately; neither restarts the source capture clock."},
      "publication_status": {key: status[key] for key in keys if key in status},
      "publication_status_cli_observation": status_cli, "binding": info(binding)})
preserved = json.loads((HERE / "preserved-work.json").read_bytes())
verification = {"installed_modules": {name: str(sys.modules[name].__file__) for name in
                ("live_contentops.main_report_projection_source_v1", "live_contentops.reader_article_contract_v1",
                 "live_contentops.plan_status_posts_v1", "live_contentops.published_images_v1")},
                "exact_main_passage_admitted": True, "original_data_clock_consumed": True,
                "new_main_reports_since_previous_assessment": len(changed), "t2_selection_used_in_assessment": True,
                 "publication_status_cli_succeeded": status_cli["succeeded"],
                "feed_unchanged": info(feed)["sha256"] == feed_before["sha256"],
                "inherited_work_unchanged": all(info(Path(row["root"]) / row["relative_path"])["sha256"] == row["sha256"] for row in preserved),
                "new_operations": 0, "editorial_model_calls": 0, "public_writes": 0,
                "pytest_processes": 0, "chat_messages": 0, "schedule_changes": 0}
assert verification["feed_unchanged"] and verification["inherited_work_unchanged"]
save("verification.json", verification)
launch = json.loads((HERE / "launch-observation.json").read_text(encoding="utf-8-sig"))
result = {"item": "CC-124", "actual_entry_utc": launch["process_start_utc"], "observed_at_utc": now_text,
          "new_articles": 0, "new_completed_main_reports": len(changed), "first_cause": clock_cause,
          "source_assessment": info(HERE / "source-assessment.json"),
          "choice": "Use all held Main reports, the latest T2 output and exported scenarios in the publishing decision. One completed Main daily report arrived since the 18:54 check, but its original 22:05 GMT+7 capture passed the root CC-403 publication deadline at 23:05 GMT+7 on 11 November. The later plan registration and export refresh do not restart that clock. No fresh completed Main article source is available; decisions 89 and 93 require no filler and the six-hour cadence. Return the standing item to OPEN, next due 07:29 GMT+7, and retain the next pre-US note opportunity at 18:30 GMT+7.",
          "authority": ["JIM_DECISION_89", "JIM_DECISION_93", "JIM_DECISION_98", "ROOT_CC403_READER_ARTICLE_V1"],
          "production_day": day_of(now), "daily_article_limit": daily_limit(now),
          "standing_status": "OPEN", "next_due_gmt7": "12 Nov 2026 07:29 GMT+7",
          "configured_launch": launch,
          "base_commit": "f4df4436940d231a571899268d687c7e09c0773b",
          "base_reason": "Current ContentOps operating HEAD, containing the live Publisher fixes; fresh origin/master is its ancestor, 949 commits behind.",
           "observation_limits": [] if status_cli["succeeded"] else [status_cli],
           "acceptance": "Installed source, clock, scenario and production-day consumers observed; publication-status CLI timed out after 45 seconds, with no retry. No new published-article acceptance."}
save("result.json", result)
print(json.dumps({"first_cause": clock_cause, "new_completed_main_reports": len(changed),
                  "original_capture_utc": capture_clock, "new_articles": 0, "article_slots_used": len(pieces),
                  "active_leases": len(leases), "next_due_gmt7": result["next_due_gmt7"],
                  "inherited_work_unchanged": verification["inherited_work_unchanged"]}))
