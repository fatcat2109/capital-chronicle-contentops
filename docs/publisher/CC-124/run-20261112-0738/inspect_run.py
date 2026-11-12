"""One CC-124 source assessment through installed consumers; no edition or writes."""
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
PREVIOUS = HERE.parent / "run-20261112-0129/source-assessment.json"
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


def newest(root, limit=4):
    if not root.exists():
        return []
    return sorted((p for p in root.rglob("*") if p.is_file() and p.suffix in {".md", ".json", ".txt"}
                   and not any(w in p.name.lower() for w in
                               ("secret", "credential", "account", ".env", "claude-response", "prompt"))),
                  key=lambda p: p.stat().st_mtime, reverse=True)[:limit]


now = datetime.now(timezone.utc)
feed = RUNTIME / "published_content_v1.jsonl"
feed_before = info(feed)
prior = json.loads(PREVIOUS.read_bytes())
prior_hashes = {row["path"]: row["sha256"] for row in prior["retained_reports"]}
reports = sorted(MAIN.rglob("owner-native.json"), key=lambda p: p.stat().st_mtime, reverse=True)
inventory = []
for path in reports:
    capture = path.parent / "capture.json"
    clock = json.loads(capture.read_bytes()).get("known_at_utc") if capture.exists() else None
    age = (now - datetime.fromisoformat(clock.replace("Z", "+00:00"))).total_seconds() if clock else None
    inventory.append({**info(path), "capture_known_at_utc": clock,
                      "age_seconds": age, "within_60_minutes": 0 <= age <= 3600 if age is not None else None})
changed = [row for row in inventory if prior_hashes.get(row["path"]) != row["sha256"]]

# Use the existing public-excerpt owner, including its original capture-clock binding.
latest = next(p for p in reports if "daily-research-portfolio-" in str(p))
report = json.loads(latest.read_bytes())
attempts = []
for key in ("summary", "causal_alternatives", "contradictions", "priced_in"):
    for i, row in enumerate(report.get(key, [])):
        if not isinstance(row, dict) or not isinstance(row.get("text"), str) or not row["text"]:
            continue
        pointer = f"/{key}/{i}/text"
        spec = {"authority_ref": "JIM_DECISION_89", "source_url": "urn:cc-public-report:cc124-main-20261112-0738",
                "headline_id": "cc124-main-20261112-0738", "headline_text": "Main's latest six-market review",
                "known_at_utc": info(latest)["modified_at_utc"], "revision_at_utc": now.isoformat(),
                "candidate_catalyst_tags": ["MAIN_REPORT"],
                "passages": [{"source_path": str(latest), "source_sha256": info(latest)["sha256"],
                              "source_json_pointer": pointer,
                              "fragments": [{"start": 0, "end": min(1800, len(row["text"]))}]}]}
        try:
            projection = verify_projection(spec)
            attempts.append({"pointer": pointer, "outcome": "PUBLIC_PASSAGE_ADMITTED"})
            break
        except ValueError as exc:
            attempts.append({"pointer": pointer, "outcome": str(exc)})
    else:
        continue
    break
else:
    raise RuntimeError("Inspect remaining exact source spans: no public passage admitted")
contract = contract_for({"source_pack": [projection["document"]], "selected_candidate": projection})
capture = latest.parent / "capture.json"
capture_clock = json.loads(capture.read_bytes())["known_at_utc"]
assert datetime.fromisoformat(contract["data_cutoff_utc"]) == datetime.fromisoformat(capture_clock.replace("Z", "+00:00"))
clock_cause = None
try:
    validate_publication_clock({"reader_article_contract": contract}, now=now, destination="substack")
except ValueError as exc:
    clock_cause = str(exc)

t2_path = max((MAIN / "t2-runs").rglob("run.json"), key=lambda p: p.stat().st_mtime)
t2 = json.loads(t2_path.read_bytes())
t2_output_path = t2_path.parent / "t2-output.json"
t2_output = json.loads(t2_output_path.read_bytes())
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
feed_root = Path(binding["public_export_root"])
shock = MAIN / "shock-trigger/2026-11-12/20261112T002042Z/shock/analysis.txt"
shock_text = shock.read_text(encoding="utf-8")
assert "did not analyse or trade this shock" in shock_text and "no analysis ran, so I make no call" in shock_text
assessment = {"observed_at_utc": now.isoformat(), "previous_observation": info(PREVIOUS),
              "new_or_changed_completed_native_reports": changed, "retained_reports": inventory,
              "installed_projection": {"spec": spec, "attempts": attempts, "reader_contract": contract,
                  "original_capture": {**info(capture), "known_at_utc": capture_clock},
                  "public_passage_sha256": sha256(projection["document"]["canonical_content_text"].encode()).hexdigest(),
                  "publication_clock_cause": clock_cause,
                  "publication_deadline_utc": (datetime.fromisoformat(capture_clock.replace("Z", "+00:00")) + timedelta(minutes=60)).isoformat()},
              "latest_t2_selection": {"run": info(t2_path), "output": info(t2_output_path),
                  "original_capture_utc": t2.get("capture_known_at_utc"), "decision_at_utc": t2.get("decision_at_utc"),
                  "thesis_count": len(t2_output.get("theses", [])), "selected_instruments": t2.get("selected_instruments"),
                  "use": "Ranked setups assessed with retained reports and exported plans; no capture clock refreshed."},
              "fresh_shock_process_return": {"source": info(shock),
                  "use": "Read and assessed. The return explicitly reports no market analysis and no market call; it describes a prepare failure. It supplies no new article analysis.",
                  "first_cause_in_source": "REQUESTED_ASSET_NOT_IN_CURRENT_SCOPE:US02Y,US10Y"},
              "additional_held_outputs": additional, "backlog_archive_search": searches,
              "configured_public_main_feed": {"binding": info(binding_path), "root": str(feed_root),
                                              "latest_files": [info(p) for p in newest(feed_root, 3)]}}
save("source-assessment.json", assessment)
print(json.dumps({"source_assessment_saved": True, "new_native_reports": len(changed),
                  "reports_inventoried": len(inventory), "fresh_native_reports": sum(bool(r["within_60_minutes"]) for r in inventory),
                  "data_cutoff_utc": capture_clock, "first_cause": clock_cause}), flush=True)

# Read Main's existing validated export; no Main code, state or process is changed.
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
register = PublishedImages(RUNTIME / "published_images_v1.jsonl", published_feed=feed)
pieces = sorted(register._daily_pieces(register.records(), now))
with sqlite3.connect((RUNTIME / "contentops_daily_app_v1.sqlite3").as_uri() + "?mode=ro", uri=True) as conn:
    conn.row_factory = sqlite3.Row
    leases = [dict(row) for row in conn.execute("SELECT lease_id,lease_key,status,expires_at FROM leases WHERE status='ACTIVE'")
              if datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")) > now]
latest_registration = max((p.get("registered_at_utc") or "") for p in export["plans"])
consumers = {"observed_at_utc": now.isoformat(), "production_day": day_of(now), "daily_article_limit": daily_limit(now),
             "article_slots_in_use": pieces, "active_leases": leases,
             "main_plan_export": {"generated_at_utc": export["generated_at_utc"], "content_hash": export.get("content_hash"),
                                  "plan_count": len(export["plans"]), "latest_plan_registration_utc": latest_registration,
                                  "latest_six_market_scenarios": scenarios,
                                  "clock_use": "Generation and registration are observed separately; neither replaces a bound source capture."},
             "publication_status_cli": "Not invoked: no new article source or publication operation. No current channel readback or global unknown-write count claimed."}
save("installed-consumers.json", consumers)
assert not any(row["within_60_minutes"] for row in inventory), "Fresh completed Main report requires editorial assessment"
assert clock_cause and clock_cause.startswith("ARTICLE_DATA_CUTOFF_EXPIRED:"), "Latest report needs editorial assessment"
assert (now - datetime.fromisoformat(latest_registration.replace("Z", "+00:00"))).total_seconds() > 3600, "New Main plan requires editorial assessment"
preserved = json.loads((HERE / "preserved-work.json").read_bytes())
verification = {"installed_modules": {name: str(sys.modules[name].__file__) for name in
                ("live_contentops.main_report_projection_source_v1", "live_contentops.reader_article_contract_v1",
                 "live_contentops.plan_status_posts_v1", "live_contentops.published_images_v1")},
                "exact_public_main_passage_admitted": True, "original_capture_clock_consumed": True,
                "new_completed_native_reports": len(changed), "fresh_native_reports": 0,
                "fresh_shock_process_return_assessed": True, "validated_main_plan_export_consumed": True,
                "publication_feed_before": feed_before, "publication_feed_after": info(feed),
                "inherited_work_unchanged": all(info(Path(row["root"]) / row["relative_path"])["sha256"] == row["sha256"] for row in preserved),
                "new_operations": 0, "editorial_model_calls": 0, "public_writes": 0,
                "pytest_processes_started_by_assessment": 0,
                "targeted_test_evidence": info(HERE / "tests.json"), "chat_messages": 0, "schedule_changes": 0}
verification["publication_feed_unchanged"] = verification["publication_feed_before"]["sha256"] == verification["publication_feed_after"]["sha256"]
assert verification["inherited_work_unchanged"]
save("verification.json", verification)
launch = json.loads((HERE / "launch-observation.json").read_text(encoding="utf-8-sig"))
entry = datetime.fromisoformat(launch["process_start_utc"].replace("Z", "+00:00"))
next_due = (entry + timedelta(hours=6)).astimezone(timezone(timedelta(hours=7)))
result = {"item": "CC-124", "actual_entry_utc": entry.isoformat(), "observed_at_utc": now.isoformat(),
          "new_articles": 0, "first_cause": clock_cause,
          "choice": "Use held Main reports, T2 ranking, public plans, dated scenarios and the fresh shock return. Repair Publisher's rejection of explicit Main CLOSED states in the existing contract and consumers, without reviving an old fill or inventing a result. No fresh completed market analysis is available: the shock return says analysis did not run; the latest analytical report's original capture exceeds CC-403's deadline. Decision 89 requires no filler. No edition is allocated.",
          "authority": ["JIM_DECISION_89", "JIM_DECISION_93", "JIM_DECISION_98", "ROOT_CC403_READER_ARTICLE_V1"],
          "production_day": day_of(now), "daily_article_limit": daily_limit(now), "standing_status": "OPEN",
          "next_due_gmt7": next_due.strftime("%d %b %Y %H:%M GMT+7"),
          "pre_us_note_opportunity_gmt7": "12 Nov 2026 18:30 GMT+7", "configured_launch": launch,
          "base_commit": "b78c03b07dc8e29102031905569e612e8aa8de8a",
          "base_reason": "Current ContentOps operating HEAD; freshly fetched origin/master is its ancestor, 987 commits behind.",
          "acceptance": "Installed source, clock, plan and production-day consumers observed. No published-article acceptance or channel readback claimed.",
          "next_action": "At the next standing opportunity, consume any new completed Main analysis through the same source and publication owners; preserve the pre-US note opportunity.",
          "next_actor": "Codex Publisher at the next due run; Ops Live owns Main analysis production."}
save("result.json", result)
print(json.dumps({"new_articles": 0, "first_cause": clock_cause, "main_plan_count": len(export["plans"]),
                  "latest_plan_registration_utc": latest_registration, "article_slots_used": len(pieces),
                  "active_leases": len(leases), "production_day": day_of(now), "next_due_gmt7": result["next_due_gmt7"],
                  "inherited_work_unchanged": verification["inherited_work_unchanged"],
                  "publication_feed_unchanged": verification["publication_feed_unchanged"]}))
