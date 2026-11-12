"""Assess one standing opportunity using installed consumers, without an edition."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys

HERE = Path(__file__).resolve().parent
BUILDER = HERE.parents[3]
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
RESEARCH = Path(r"A:\Capital Chronicle\ResearchRuns")
MAIN = RESEARCH / "claude-main-research"
TOWER = Path(r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower")
PREVIOUS = HERE.parent / "run-20261112-0738/source-assessment.json"
sys.path.insert(0, str(LIVE))

from live_contentops.main_report_projection_source_v1 import verify_projection
from live_contentops.plan_status_posts_v1 import read_export
from live_contentops.published_images_v1 import PublishedImages, daily_limit, day_of
from live_contentops.reader_article_contract_v1 import contract_for, validate_publication_clock


def info(path):
    digest = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest.hexdigest(),
            "modified_at_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()}


def save(name, value):
    with (HERE / name).open("x", encoding="utf-8", newline="\n") as output:
        json.dump(value, output, indent=2, ensure_ascii=True)
        output.write("\n")


def newest(root, limit=3):
    if not root.exists():
        return []
    return sorted((p for p in root.rglob("*") if p.is_file() and p.suffix in {".md", ".json", ".txt"}
                   and not any(word in p.name.lower() for word in
                               ("secret", "credential", "account", ".env", "claude-response", "prompt"))),
                  key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


now = datetime.now(timezone.utc)
feed = RUNTIME / "published_content_v1.jsonl"
feed_before = info(feed)
prior = json.loads(PREVIOUS.read_bytes())
prior_hashes = {row["path"]: row["sha256"] for row in prior["retained_reports"]}
inventory = []
for path in sorted(MAIN.rglob("owner-native.json"), key=lambda p: p.stat().st_mtime, reverse=True):
    capture = path.parent / "capture.json"
    clock = json.loads(capture.read_bytes()).get("known_at_utc") if capture.exists() else None
    age = (now - datetime.fromisoformat(clock.replace("Z", "+00:00"))).total_seconds() if clock else None
    inventory.append({**info(path), "capture_known_at_utc": clock,
                      "age_seconds": age, "within_60_minutes": 0 <= age <= 3600 if age is not None else None})
changed = [row for row in inventory if prior_hashes.get(row["path"]) != row["sha256"]]

# Re-admit the unchanged exact public passage; retrieval never changes its data clock.
spec = dict(prior["installed_projection"]["spec"])
spec.update(source_url="urn:cc-public-report:cc124-main-20261112-1339",
            headline_id="cc124-main-20261112-1339", revision_at_utc=now.isoformat())
projection = verify_projection(spec)
native_contract = contract_for({"source_pack": [projection["document"]], "selected_candidate": projection})

# A new T2 ranking is usable input. Assess its actual original capture separately.
t2_path = max((MAIN / "t2-runs").rglob("run.json"), key=lambda p: p.stat().st_mtime)
t2 = json.loads(t2_path.read_bytes())
t2_output_path = t2_path.parent / "t2-output.json"
t2_output = json.loads(t2_output_path.read_bytes())
t2_capture_path = Path(t2["t2_capture"]["request"]) / "capture.json"
t2_capture_clock = json.loads(t2_capture_path.read_bytes())["known_at_utc"]
assert t2_capture_clock == t2["capture_known_at_utc"]
t2_document = {"document_id": "latest-main-t2-ranking", "data_cutoff_utc": t2_capture_clock}
t2_contract = contract_for({"source_pack": [t2_document]})
clocks = []
for name, contract in (("latest_native_report", native_contract), ("latest_t2_ranking", t2_contract)):
    cause = None
    try:
        validate_publication_clock({"reader_article_contract": contract}, now=now, destination="substack")
    except ValueError as exc:
        cause = str(exc)
    clocks.append({"source": name, "reader_contract": contract, "publication_clock_cause": cause,
                   "publication_deadline_utc": (datetime.fromisoformat(contract["data_cutoff_utc"]) + timedelta(minutes=60)).isoformat()})

additional = []
for root in (MAIN / "horizon-runs", MAIN / "shock-trigger", RESEARCH / "claude-main-events-20261029",
             TOWER / "report_upgrade_review_20261105/strategy",
             Path(r"A:\Capital Chronicle\Worktrees\codex-data-backlog\data\research"),
             BUILDER / "data/research", LIVE / "data/research"):
    additional.append({"root": str(root), "exists": root.exists(), "latest_files": [info(p) for p in newest(root)]})
searches = []
for name in ("BACKLOG.md", "BACKLOG_ARCHIVE.md"):
    path = TOWER / name
    matches = [i + 1 for i, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines())
               if any(word in line for word in ("CC-124", "CC-403", "post-CPI", "scenario", "Main report"))]
    searches.append({**info(path), "matching_lines": matches})
binding_path = LIVE / "config/native_desktop_operator_main_feed_binding_v1.json"
binding = json.loads(binding_path.read_bytes())
public_root = Path(binding["public_export_root"])
shock_path = max((MAIN / "shock-trigger").rglob("start-result.json"), key=lambda p: p.stat().st_mtime)
shock = json.loads(shock_path.read_bytes())
shock_runs = [{k: row.get(k) for k in ("cause", "exit_code", "output", "incidents", "run_record")}
              for row in shock.get("started", [])]
assessment = {"observed_at_utc": now.isoformat(), "previous_observation": info(PREVIOUS),
              "retained_reports": inventory, "new_or_changed_completed_native_reports": changed,
              "installed_projection": {"spec": spec, "reader_contract": native_contract,
                  "public_passage_sha256": sha256(projection["document"]["canonical_content_text"].encode()).hexdigest()},
              "source_clock_checks": clocks,
              "latest_t2_selection": {"run": info(t2_path), "output": info(t2_output_path),
                  "original_capture": {**info(t2_capture_path), "known_at_utc": t2_capture_clock},
                  "output_cutoff_utc": t2_output.get("cutoff_utc"), "decision_at_utc": t2.get("decision_at_utc"),
                  "changed_since_previous_assessment": info(t2_output_path)["sha256"] != prior["latest_t2_selection"]["output"]["sha256"],
                  "thesis_count": len(t2_output.get("theses", [])), "selected_instruments": t2.get("selected_instruments"),
                  "use": "Used for candidate selection with held Main reports and plans. Original capture, output cutoff and decision clocks remain separate; the new ranking's publication deadline has elapsed."},
              "latest_shock_attempt": {"source": info(shock_path), "finished_at_utc": shock.get("finished_at_utc"),
                  "results": shock_runs, "use": "The latest return has no analytical output; its process cause does not become a new market call."},
              "additional_held_outputs": additional, "backlog_archive_search": searches,
              "configured_public_main_feed": {"binding": info(binding_path), "root": str(public_root),
                  "latest_files": [info(p) for p in newest(public_root)]}}
save("source-assessment.json", assessment)

export = read_export()["status"]
latest_registration = max((p.get("registered_at_utc") or "") for p in export["plans"])
latest_plans = {}
for plan in export["plans"]:
    asset = plan.get("asset_id")
    if asset and plan.get("registered_at_utc", "") > latest_plans.get(asset, {}).get("registered_at_utc", ""):
        latest_plans[asset] = plan
scenarios = []
for asset in ("XAUUSD", "US500", "EURUSD", "USDJPY", "USOIL", "BTCUSD"):
    plan = latest_plans.get(asset, {})
    scenario = plan.get("scenario_analysis") or {}
    scenarios.append({"asset_id": asset, "registered_at_utc": plan.get("registered_at_utc"),
                      "base_probability_pct": (scenario.get("base_case") or {}).get("probability_pct"),
                      "alternative_probability_pct": (scenario.get("main_alternative") or {}).get("probability_pct")})
register = PublishedImages(RUNTIME / "published_images_v1.jsonl", published_feed=feed)
pieces = sorted(register._daily_pieces(register.records(), now))
with sqlite3.connect((RUNTIME / "contentops_daily_app_v1.sqlite3").as_uri() + "?mode=ro", uri=True) as conn:
    conn.row_factory = sqlite3.Row
    leases = [dict(row) for row in conn.execute("SELECT lease_id,lease_key,status,expires_at FROM leases WHERE status='ACTIVE'")
              if datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")) > now]
save("installed-consumers.json", {"observed_at_utc": now.isoformat(), "production_day": day_of(now),
     "daily_article_limit": daily_limit(now), "article_slots_in_use": pieces, "active_leases": leases,
     "main_plan_export": {"generated_at_utc": export["generated_at_utc"], "content_hash": export.get("content_hash"),
         "plan_count": len(export["plans"]), "latest_plan_registration_utc": latest_registration,
         "latest_six_market_scenarios": scenarios},
     "clock_use": "Export generation and plan registration do not refresh the underlying analysis capture.",
     "publication_status_cli": "No article operation allocated; no global unknown-write count or channel readback claimed."})

assert not changed and not any(row["within_60_minutes"] for row in inventory), "New Main analysis requires assessment"
assert all(row["publication_clock_cause"] and row["publication_clock_cause"].startswith("ARTICLE_DATA_CUTOFF_EXPIRED:") for row in clocks)
assert (now - datetime.fromisoformat(latest_registration.replace("Z", "+00:00"))).total_seconds() > 3600
preserved = json.loads((HERE / "preserved-work.json").read_bytes())
verification = {"execution_python": sys.executable, "installed_modules": {name: str(sys.modules[name].__file__) for name in
                ("live_contentops.main_report_projection_source_v1", "live_contentops.reader_article_contract_v1",
                 "live_contentops.plan_status_posts_v1", "live_contentops.published_images_v1")},
     "exact_public_main_passage_admitted": True, "original_source_clocks_consumed": True,
     "new_completed_native_reports": len(changed), "new_t2_ranking_assessed": True,
     "validated_main_plan_export_consumed": True, "publication_feed_before": feed_before,
     "publication_feed_after": info(feed), "inherited_work_unchanged": all(
         info(Path(row["root"]) / row["relative_path"])["sha256"] == row["sha256"] for row in preserved),
     "new_operations": 0, "editorial_model_calls": 0, "public_writes_by_this_run": 0,
     "pytest_processes_started": 0, "chat_messages": 0, "schedule_changes": 0}
verification["publication_feed_unchanged_during_assessment"] = feed_before["sha256"] == verification["publication_feed_after"]["sha256"]
save("verification.json", verification)
result = {"item": "CC-124", "observed_at_utc": now.isoformat(), "new_articles": 0,
     "first_cause": clocks[1]["publication_clock_cause"], "standing_status": "OPEN",
     "choice": "Consume the new T2 ranking and retained Main reports/plans; issue no filler because even the new T2 original capture exceeds CC-403's 60-minute deadline. The latest shock attempt supplies no analytical output.",
     "authority": ["JIM_DECISION_89", "JIM_DECISION_93", "JIM_DECISION_98", "ROOT_CC403_READER_ARTICLE_V1"],
     "production_day": day_of(now), "article_slots_in_use": len(pieces), "daily_article_limit": daily_limit(now),
     "next_due_gmt7": "12 Nov 2026 18:30 GMT+7", "next_due_reason": "Align the next standing opportunity with the pre-US note under decision 98; no host schedule is changed.",
     "next_action": "At the pre-US note opportunity consume any new completed Main analysis through the same owners.",
     "next_actor": "Codex Publisher; Ops Live owns Main analysis production.",
     "acceptance": "Installed source, clock, plan and daily-count consumers read successfully; no new publication/readback acceptance claimed.",
     "launch_observation": json.loads((HERE / "launch-observation.json").read_bytes())}
save("result.json", result)
print(json.dumps({"new_articles": 0, "first_cause": result["first_cause"], "native_reports": len(inventory),
     "new_t2_theses": len(t2_output["theses"]), "article_slots_used": len(pieces), "active_leases": leases,
     "next_due_gmt7": result["next_due_gmt7"], "inherited_work_unchanged": verification["inherited_work_unchanged"]}))
