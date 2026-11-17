"""Observe CC-403's installed consumers once; never create a publishing operation."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
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
sys.path.insert(0, str(LIVE))

from live_contentops.main_report_projection_source_v1 import verify_projection
from live_contentops.plan_status_posts_v1 import read_export
from live_contentops.published_images_v1 import PublishedImages, daily_limit, day_of
from live_contentops.reader_article_contract_v1 import contract_for, label_errors, validate_publication_clock


def info(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
            "modified_at_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()}


def save(name, value):
    with (HERE / name).open("x", encoding="utf-8", newline="\n") as output:
        json.dump(value, output, indent=2, ensure_ascii=True)
        output.write("\n")


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True, encoding="utf-8").strip()


def modified(root):
    return [{"root": str(root), "relative_path": name, **info(root / name)}
            for name in git(root, "diff", "--name-only", "--diff-filter=M").splitlines()]


def newest(root, pattern="*", count=5):
    if not root.exists():
        return []
    return sorted((p for p in root.rglob(pattern) if p.is_file() and p.suffix in {".json", ".md"}
                   and not any(w in p.name.lower() for w in ("secret", "credential", "account", ".env"))),
                  key=lambda p: p.stat().st_mtime, reverse=True)[:count]


now = datetime.now(timezone.utc)
now_text = now.isoformat().replace("+00:00", "Z")
preserved = modified(BUILDER) + modified(LIVE)
save("preserved-work.json", preserved)

# Inspect completed reports, including the other horizon lane. Public extraction
# remains the installed source owner's responsibility, not this evidence script's.
reports = newest(MAIN, "owner-native.json", count=500)
inventory = []
for report_path in reports:
    capture = report_path.parent / "capture.json"
    inventory.append({**info(report_path), "original_data_cutoff_utc":
                      json.loads(capture.read_bytes()).get("known_at_utc") if capture.exists() else None})
latest = next(p for p in reports if "daily-research-portfolio-" in str(p))
report = json.loads(latest.read_bytes())
attempts = []
for key in ("summary", "causal_alternatives", "contradictions", "priced_in"):
    for index, row in enumerate(report.get(key, [])):
        if not isinstance(row, dict) or not isinstance(row.get("text"), str) or not row["text"]:
            continue
        pointer = f"/{key}/{index}/text"
        spec = {"authority_ref": "JIM_DECISION_89", "source_url": "urn:cc-public-report:cc403-daily-20261111",
                "headline_id": "cc403-daily-20261111", "headline_text": "Our pre-US daily note",
                "known_at_utc": info(latest)["modified_at_utc"], "revision_at_utc": now_text,
                "candidate_catalyst_tags": ["MAIN_REPORT", "DAILY_NOTE"],
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
    raise RuntimeError("Inspect the exact source passages: no public passage was admitted")

contract = contract_for({"source_pack": [projection["document"]], "selected_candidate": projection})
try:
    validate_publication_clock({"reader_article_contract": contract}, now=now, destination="substack")
    clock_cause = None
except ValueError as exc:
    clock_cause = str(exc)
capture_path = latest.parent / "capture.json"
capture_clock = json.loads(capture_path.read_bytes())["known_at_utc"]
assert datetime.fromisoformat(contract["data_cutoff_utc"]) == datetime.fromisoformat(capture_clock.replace("Z", "+00:00"))

producer_path = newest(MAIN / "brain-runs", "run.json", count=1)[0]
producer = json.loads(producer_path.read_bytes())
t2_path = newest(MAIN / "t2-runs", "run.json", count=1)[0]
t2 = json.loads(t2_path.read_bytes())
t2_output_path = t2_path.parent / "t2-output.json"
t2_output = json.loads(t2_output_path.read_bytes())
searches = []
for root in (MAIN / "horizon-runs", RESEARCH / "claude-main-events-20261029",
             TOWER / "report_upgrade_review_20261105/strategy",
             Path(r"A:\Capital Chronicle\Worktrees\codex-data-backlog\data\research"),
             BUILDER / "data/research", LIVE / "data/research"):
    searches.append({"root": str(root), "exists": root.exists(), "newest_files": [info(p) for p in newest(root)]})
profile = json.loads((LIVE / "config/native_desktop_operator_profile_v1.json").read_bytes())
feed_binding_path = LIVE / "config/native_desktop_operator_main_feed_binding_v1.json"
feed_binding = json.loads(feed_binding_path.read_bytes())
for root in (Path(feed_binding["public_export_root"]), Path(feed_binding["research_root"]),
             *(Path(p) if Path(p).is_absolute() else LIVE / p for p in profile["research_editions_root"])):
    searches.append({"root": str(root), "exists": root.exists(), "newest_files": [info(p) for p in newest(root, count=2)]})
backlog_search = []
for name in ("BACKLOG.md", "BACKLOG_ARCHIVE.md"):
    path = TOWER / name
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    hits = [i + 1 for i, line in enumerate(lines) if any(word in line for word in ("CC-403", "CC-124", "scenario", "Main report"))]
    backlog_search.append({**info(path), "matching_lines": hits})
save("source-assessment.json", {"observed_at_utc": now_text, "completed_reports": inventory,
     "latest_daily_report": info(latest), "projection": {"spec": spec, "attempts": attempts,
         "public_passage_sha256": sha256(projection["document"]["canonical_content_text"].encode()).hexdigest(),
         "capture": info(capture_path), "original_data_cutoff_utc": capture_clock,
         "reader_contract": contract, "publication_clock_cause": clock_cause,
         "publication_deadline_utc": (datetime.fromisoformat(capture_clock.replace("Z", "+00:00")) + timedelta(minutes=60)).isoformat()},
     "latest_producer_run": {**info(producer_path), "outcome": producer.get("outcome"),
         "stop_reason": producer.get("stop_reason"), "stopped_at_utc": producer.get("stopped_at_utc"),
         "analysis_launched": (producer.get("analysis") or {}).get("launched")},
     "t2": {"run": info(t2_path), "output": info(t2_output_path),
         "original_capture_utc": t2.get("capture_known_at_utc"), "decision_at_utc": t2.get("decision_at_utc"),
         "thesis_count": len(t2_output.get("theses", [])),
         "thesis_fields": sorted({k for row in t2_output.get("theses", []) for k in row}),
         "use": "Current ranking and catalyst context assessed; no newly authored daily call or scenario set."},
     "additional_source_searches": searches, "backlog_search": backlog_search,
     "feed_binding": info(feed_binding_path)})

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
images = PublishedImages(RUNTIME / "published_images_v1.jsonl", published_feed=feed)
pieces = sorted(images._daily_pieces(images.records(), now))
with sqlite3.connect((RUNTIME / "contentops_daily_app_v1.sqlite3").as_uri() + "?mode=ro", uri=True) as conn:
    conn.row_factory = sqlite3.Row
    leases = [dict(row) for row in conn.execute("SELECT lease_id,lease_key,status,expires_at FROM leases WHERE status='ACTIVE'")
              if datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00")) > now]
manual_root = RUNTIME / "daily_app_outputs/owner-manual"
bindings = [info(p) for p in manual_root.glob("cc124*/binding.json")]
save("installed-consumers.json", {"observed_at_utc": now_text, "production_day": day_of(now),
     "daily_article_limit": daily_limit(now), "published_canonicals_today": pieces, "active_leases": leases,
     "main_export": {"generated_at_utc": export.get("generated_at_utc"), "content_hash": export.get("content_hash"),
                     "latest_six_market_scenarios": scenarios}, "existing_cc124_bindings": bindings,
     "installed_modules": {name: str(sys.modules[name].__file__) for name in
         ("live_contentops.main_report_projection_source_v1", "live_contentops.reader_article_contract_v1",
          "live_contentops.plan_status_posts_v1", "live_contentops.published_images_v1")},
     "internal_label_probe": label_errors("DATED CAPITAL CHRONICLE REVIEW")})
verification = {"exact_public_main_passage_admitted": True, "original_data_clock_consumed": True,
     "feed_unchanged": info(feed)["sha256"] == feed_before["sha256"],
     "inherited_modified_files_unchanged": all(info(Path(row["path"]))["sha256"] == row["sha256"] for row in preserved),
     "new_operations": 0, "editorial_model_calls": 0, "public_writes": 0, "chat_messages": 0, "schedule_changes": 0}
assert verification["feed_unchanged"] and verification["inherited_modified_files_unchanged"]
save("verification.json", verification)
print(json.dumps({"first_cause": clock_cause, "data_cutoff_utc": capture_clock,
                  "latest_main_analysis_launched": (producer.get("analysis") or {}).get("launched"),
                  "article_slots_used": len(pieces), "active_leases": len(leases),
                  "inherited_work_unchanged": verification["inherited_modified_files_unchanged"]}))
