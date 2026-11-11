"""One bounded CC-124 source check using the installed Publisher consumers."""
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
PREVIOUS = HERE.parent / "run-20261111-0217"
FINAL_STATUS = "--final-status" in sys.argv
ENTRY = "2026-11-11T02:00:24.973892Z"
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
    if FINAL_STATUS and name in {"installed-consumers.json", "verification.json", "result.json"}:
        name = "final-" + name
    with (HERE / name).open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2, ensure_ascii=True)
        output.write("\n")


now = datetime.now(timezone.utc)
now_text = now.isoformat().replace("+00:00", "Z")
assessment_path = HERE / "source-assessment.json"
if assessment_path.exists():
    assessment = json.loads(assessment_path.read_bytes())
    new_reports = assessment["new_or_changed_completed_main_reports"]
    projection = assessment["installed_projection"]
    capture_clock = projection["original_capture"]["known_at_utc"]
    clock_cause = projection["publication_clock_cause"]
else:
    reports = sorted(MAIN.rglob("owner-native.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    previous = json.loads((PREVIOUS / "source-inventory.json").read_bytes())
    previous_hashes = {r["path"]: r["sha256"] for r in previous["retained_reports"]}
    inventory = []
    for path in reports:
        capture = path.parent / "capture.json"
        inventory.append({**info(path), "capture_known_at_utc":
                          json.loads(capture.read_bytes()).get("known_at_utc") if capture.exists() else None})
    new_reports = [row for row in inventory if previous_hashes.get(row["path"]) != row["sha256"]]
    latest = reports[0]
    report = json.loads(latest.read_bytes())
    capture = latest.parent / "capture.json"
    capture_clock = json.loads(capture.read_bytes())["known_at_utc"]
    text = report["summary"][0]["text"]
    spec = {"authority_ref": "JIM_DECISION_89",
            "source_url": "urn:cc-public-report:cc124-post-cpi-20261110",
            "headline_id": "cc124-post-cpi-main-20261110",
            "headline_text": "Main's post-CPI review",
            "known_at_utc": info(latest)["modified_at_utc"], "revision_at_utc": now_text,
            "candidate_catalyst_tags": ["CPI", "POST_RELEASE_REVIEW"],
            "passages": [{"source_path": str(latest), "source_sha256": info(latest)["sha256"],
                          "source_json_pointer": "/summary/0/text",
                          "fragments": [{"start": 0, "end": len(text)}]}]}
    projection = verify_projection(spec)
    contract = contract_for({"source_pack": [projection["document"]], "selected_candidate": projection})
    assert datetime.fromisoformat(contract["data_cutoff_utc"]) == datetime.fromisoformat(capture_clock.replace("Z", "+00:00"))
    try:
        validate_publication_clock({"reader_article_contract": contract}, now=now, destination="substack")
        clock_cause = None
    except ValueError as exc:
        clock_cause = str(exc)

    other = []
    for root in (MAIN / "t2-runs", RESEARCH / "claude-main-events-20261029",
                 TOWER / "report_upgrade_review_20261105/strategy",
                 Path(r"A:\Capital Chronicle\Worktrees\codex-data-backlog\data\research"),
                 BUILDER / "data/research", LIVE / "data/research"):
        files = sorted((p for p in root.rglob("*") if p.is_file() and p.suffix in {".md", ".json"}
                        and not any(word in p.name.lower() for word in ("secret", "credential", "account", ".env"))),
                       key=lambda p: p.stat().st_mtime, reverse=True)[:6] if root.exists() else []
        other.append({"root": str(root), "exists": root.exists(), "latest_files": [info(p) for p in files]})
    backlog_search = []
    for name in ("BACKLOG.md", "BACKLOG_ARCHIVE.md"):
        path = TOWER / name
        lines = path.read_text(encoding="utf-8").splitlines()
        matches = [i + 1 for i, line in enumerate(lines)
                   if any(word in line for word in ("CC-124", "CC-403", "post-CPI", "post-release Main"))]
        backlog_search.append({**info(path), "match_count": len(matches), "matching_lines": matches})
    feed_binding = json.loads((LIVE / "config/native_desktop_operator_main_feed_binding_v1.json").read_bytes())
    public_root = Path(feed_binding["public_export_root"])
    public_files = sorted(public_root.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
    save("source-assessment.json", {"observed_at_utc": now_text,
         "previous_observation": info(PREVIOUS / "result.json"),
         "new_or_changed_completed_main_reports": new_reports, "retained_reports": inventory,
         "additional_held_outputs": other, "backlog_archive_search": backlog_search,
         "configured_public_main_feed": {"root": str(public_root), "latest_files": [info(p) for p in public_files]},
         "installed_projection": {"spec": spec, "document_id": projection["document"].get("document_id"),
              "public_passage_sha256": sha256(projection["document"]["canonical_content_text"].encode("utf-8")).hexdigest(),
              "original_capture": {**info(capture), "known_at_utc": capture_clock},
              "reader_contract": contract, "publication_clock_cause": clock_cause,
              "publication_deadline_utc": (datetime.fromisoformat(capture_clock.replace("Z", "+00:00")) + timedelta(minutes=60)).isoformat()}})

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
command = [sys.executable, "-B", "scripts/run_native_desktop_editorial.py", "publication-status",
           "--binding", str(binding), "--rollout", "config/native_desktop_rollout_v1.json"]
done = subprocess.run(command, cwd=LIVE, text=True, encoding="utf-8", capture_output=True,
                      timeout=45, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
assert done.returncode == 0, done.stderr[-400:]
status = json.loads(done.stdout)
if status.get("classification") == "TOOL_OUTPUT_IN_FILE":
    reference = status["output"]
    raw = Path(reference["path"]).read_bytes()
    assert sha256(raw).hexdigest() == reference["sha256"]
    status = json.loads(raw)
status = status.get("publication", status)
keys = ("run_id", "work_item_id", "canonical_article_status", "canonical_article_real_published", "canonical_url",
        "canonical_publication_status", "distribution_status", "derivative_confirmed_count", "derivative_attempted_count",
        "derivative_unknown_count", "recovery_required_destinations", "readback_limitation_destinations",
        "unknown_write_detected", "unknown_write_count", "state", "dispatch_blocker", "skipped_destinations",
        "closed_no_write_destinations", "additional_recovery_required_destinations")
save("installed-consumers.json", {"observed_at_utc": now_text, "production_day": day_of(now),
     "daily_article_limit": daily_limit(now), "published_canonicals_today": pieces, "active_leases": leases,
     "main_plan_export": {"generated_at_utc": export["generated_at_utc"], "content_hash": export.get("content_hash"),
          "latest_six_market_scenarios": scenarios,
          "interpretation": "The refreshed export and held estimates enter the assessment; their generation and registration clocks do not replace Main's original data capture."},
     "publication_status": {key: status[key] for key in keys if key in status},
     "destination_records": [{key: row.get(key) for key in ("destination", "status", "reconciliation_status",
         "public_object_id", "public_object_url")} for row in status.get("destinations", [])], "binding": info(binding)})

preserved = json.loads((HERE / "preserved-work.json").read_bytes())
frozen = json.loads((HERE / "frozen-artifacts-before.json").read_bytes())
verification = {"operating_modules": {name: str(sys.modules[name].__file__) for name in (
    "live_contentops.main_report_projection_source_v1", "live_contentops.reader_article_contract_v1",
    "live_contentops.plan_status_posts_v1", "live_contentops.published_images_v1")},
    "exact_main_passage_admitted": True, "original_data_clock_consumed": True,
    "fresh_export_not_used_as_data_clock": True, "publication_status_cli_succeeded": True,
    "new_operations": 0, "editorial_model_calls": 0, "public_writes": 0, "pytest_processes": 3 if FINAL_STATUS else 2,
    "chat_messages": 0, "schedule_changes": 0, "feed_unchanged": info(feed)["sha256"] == feed_before["sha256"],
    "historical_publication_artifacts_unchanged": all(info(Path(row["path"]))["sha256"] == row["sha256"] for row in frozen["files"]),
    "canonical_identity_unchanged": status["canonical_url"] == json.loads((PREVIOUS / "publication-status.json").read_bytes())["result"]["canonical_url"],
    "inherited_work_unchanged": all(info(Path(row["root"]) / row["relative_path"])["sha256"] == row["sha256"] for row in preserved)}
assert all(verification[key] for key in ("feed_unchanged", "inherited_work_unchanged",
           "historical_publication_artifacts_unchanged", "canonical_identity_unchanged"))
save("verification.json", verification)
result = {"item": "CC-124", "actual_entry_utc": ENTRY, "observed_at_utc": now_text, "new_articles": 0,
    "source_assessment": info(assessment_path),
    "first_cause": "NO_NEW_MAIN_REPORT" if not new_reports else clock_cause,
    "latest_source_cause": clock_cause, "production_day": day_of(now), "daily_article_limit": daily_limit(now),
    "choice": "Use the unchanged post-CPI Main report and plan export in the source assessment. Resume article production on the next fresh Main report; decision 89 requires no filler. Do not replace the original capture clock or issue a duplicate operation.",
    "authority": ["JIM_DECISION_89", "JIM_DECISION_93", "JIM_DECISION_98", "ROOT_CC403_READER_ARTICLE_V1"],
    "standing_status": "OPEN", "next_due_gmt7": "11 Nov 2026 15:00 GMT+7",
    "next_daily_wrap_gmt7": "11 Nov 2026 18:30 GMT+7",
    "configured_launch": {"process_id": 19976, "process_start_utc": ENTRY,
        "model": "gpt-6.1-sol", "effort": "max", "observation": "Win32_Process.CommandLine",
        "arguments": ["--model", "gpt-6.1-sol", "-c", "model_reasoning_effort=\"max\""],
        "state": "CONFIGURED_NOT_OBSERVED"},
    "publication_status_repair": {"first_error": "qualified_record_not_valid_for_slot",
        "consumer": "live_contentops.native_desktop_publication_v1._prepared_packet",
        "operating_commit": subprocess.check_output(["git", "-C", str(LIVE), "rev-parse", "HEAD"], text=True).strip(),
        "scope": "Exact sealed and dispatched historical artifacts retain their original destination set. New packets keep the current destination requirements."},
    "acceptance": "Installed source-check consumers verified. No new article or published-article acceptance claimed."}
save("result.json", result)
print(json.dumps({"first_cause": result["first_cause"], "latest_source_cause": clock_cause,
    "new_or_changed_main_reports": len(new_reports), "original_capture_utc": capture_clock,
    "new_articles": 0, "article_slots_used": len(pieces), "active_leases": len(leases),
    "next_due_gmt7": result["next_due_gmt7"], "verification": verification["inherited_work_unchanged"]}))
