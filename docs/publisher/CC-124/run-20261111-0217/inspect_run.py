"""One CC-124 observation through installed source and publication consumers."""
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
MAIN = Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-research")
TOWER = Path(r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower")
sys.path.insert(0, str(LIVE))
from live_contentops.main_report_projection_source_v1 import verify_projection
from live_contentops.plan_status_posts_v1 import read_export
from live_contentops.published_content_v1 import read_records
from live_contentops.published_images_v1 import PublishedImages, daily_limit, day_of
from live_contentops.reader_article_contract_v1 import contract_for, validate_publication_clock


def info(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha256(raw).hexdigest(),
            "modified_at_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()}


def save(name, value):
    path = HERE / name
    assert not path.exists(), "Preserve the first observation: " + str(path)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


now = datetime.now(timezone.utc)
now_text = now.isoformat().replace("+00:00", "Z")
reports = sorted(MAIN.rglob("owner-native.json"), key=lambda p: p.stat().st_mtime, reverse=True)
latest = reports[0]
assert latest.parent.parent == MAIN / "daily-research-portfolio-279805139/requests"
report = json.loads(latest.read_bytes())
capture = latest.parent / "capture.json"
capture_clock = json.loads(capture.read_bytes())["known_at_utc"]
report_clock = datetime.fromtimestamp(latest.stat().st_mtime, timezone.utc).isoformat()
text = report["summary"][0]["text"]
spec = {"authority_ref": "JIM_DECISION_89", "source_url": "urn:cc-public-report:cc124-post-cpi-20261110",
        "headline_id": "cc124-post-cpi-main-20261110", "headline_text": "Main's post-CPI review",
        "known_at_utc": report_clock, "revision_at_utc": now_text,
        "candidate_catalyst_tags": ["CPI", "POST_RELEASE_REVIEW"],
        "passages": [{"source_path": str(latest), "source_sha256": info(latest)["sha256"],
                      "source_json_pointer": "/summary/0/text", "fragments": [{"start": 0, "end": len(text)}]}]}
projection = verify_projection(spec)
contract = contract_for({"source_pack": [projection["document"]], "selected_candidate": projection})
assert datetime.fromisoformat(contract["data_cutoff_utc"]) == datetime.fromisoformat(capture_clock.replace("Z", "+00:00"))
try:
    validate_publication_clock({"reader_article_contract": contract}, now=now, destination="substack")
    clock_cause = None
except ValueError as exc:
    clock_cause = str(exc)
assert clock_cause and clock_cause.startswith("ARTICLE_DATA_CUTOFF_EXPIRED:")
save("source-projection.json", {"observed_at_utc": now_text, "spec": spec, "verified_projection": projection,
     "reader_contract": contract, "publication_clock_cause": clock_cause,
     "original_capture": {**info(capture), "known_at_utc": capture_clock},
     "publication_deadline_utc": (datetime.fromisoformat(capture_clock.replace("Z", "+00:00")) + timedelta(minutes=60)).isoformat()})

inventory = [{"kind": "Main owner return", **info(p)} for p in reports]
for p in sorted((MAIN / "t2-runs").glob("*/t2-output.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:6]:
    inventory.append({"kind": "T2 output", **info(p)})
other = []
for root in (Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-events-20261029"),
             TOWER / "report_upgrade_review_20261105/strategy",
             Path(r"A:\Capital Chronicle\Worktrees\codex-data-backlog\data\research"),
             BUILDER / "data/research", LIVE / "data/research"):
    files = sorted((p for p in root.rglob("*") if p.is_file() and p.suffix in {".md", ".json"}
                    and not any(x in p.name.lower() for x in ("secret", "credential", "account", ".env"))),
                   key=lambda p: p.stat().st_mtime, reverse=True)[:6] if root.exists() else []
    other.append({"root": str(root), "exists": root.exists(), "latest_files": [info(p) for p in files]})
search = []
for name in ("BACKLOG.md", "BACKLOG_ARCHIVE.md"):
    p = TOWER / name
    lines = p.read_text(encoding="utf-8").splitlines()
    matches = [{"line": i + 1, "text": line[:900]} for i, line in enumerate(lines)
               if any(x in line for x in ("CC-124", "CC-403", "post-CPI", "post-release Main"))]
    search.append({**info(p), "match_count": len(matches), "matches": matches[-18:]})
save("source-inventory.json", {"observed_at_utc": now_text, "retained_reports": inventory,
                              "additional_held_outputs": other, "backlog_search": search})

export = read_export()["status"]
latest_plans = {}
for plan in export["plans"]:
    asset = plan.get("asset_id")
    if asset and (asset not in latest_plans or plan.get("registered_at_utc", "") > latest_plans[asset].get("registered_at_utc", "")):
        latest_plans[asset] = plan
six = ("XAUUSD", "US500", "EURUSD", "USDJPY", "USOIL", "BTCUSD")
scenarios = []
for asset in six:
    plan = latest_plans.get(asset, {})
    scenario = plan.get("scenario_analysis") or {}
    scenarios.append({"asset_id": asset, "registered_at_utc": plan.get("registered_at_utc"),
                      "base_probability_pct": (scenario.get("base_case") or {}).get("probability_pct"),
                      "alternative_probability_pct": (scenario.get("main_alternative") or {}).get("probability_pct")})
save("scenario-reader.json", {"observed_at_utc": now_text, "export_generated_at_utc": export["generated_at_utc"],
     "export_content_hash": export.get("content_hash"), "latest_six_market_scenarios": scenarios,
     "interpretation": "Main supplied post-CPI probabilities for four markets; two rows remain pre-release. These held estimates enter the source assessment. Export generation and plan registration do not refresh the report's data capture."})

feed = RUNTIME / "published_content_v1.jsonl"
feed_before = info(feed)
register = PublishedImages(RUNTIME / "published_images_v1.jsonl", published_feed=feed)
pieces = sorted(register._daily_pieces(register.records(), now))
with sqlite3.connect((RUNTIME / "contentops_daily_app_v1.sqlite3").as_uri() + "?mode=ro", uri=True) as conn:
    conn.row_factory = sqlite3.Row
    leases = [dict(r) for r in conn.execute("SELECT lease_id,lease_key,status,expires_at FROM leases WHERE status='ACTIVE' AND expires_at>?", (now_text,))]
assert not leases
binding = RUNTIME / "daily_app_outputs/owner-manual/cc338-cpi-preview-20261110-v1/binding.json"
command = [sys.executable, "scripts/run_native_desktop_editorial.py", "publication-status", "--binding", str(binding), "--rollout", "config/native_desktop_rollout_v1.json"]
observed = subprocess.run(command, cwd=LIVE, text=True, capture_output=True, timeout=45)
assert observed.returncode == 0, observed.stderr[-400:]
status = json.loads(observed.stdout)
if status.get("classification") == "TOOL_OUTPUT_IN_FILE":
    reference = status["output"]
    raw = Path(reference["path"]).read_bytes()
    assert sha256(raw).hexdigest() == reference["sha256"]
    status = json.loads(raw)
projection_status = status.get("publication", status)
save("publication-status.json", {"observed_at_utc": now_text, "binding": info(binding), "result": status})

preserved = json.loads((HERE / "preserved-work.json").read_bytes())
verification = {"operating_modules": {name: str(sys.modules[name].__file__) for name in (
    "live_contentops.main_report_projection_source_v1", "live_contentops.reader_article_contract_v1",
    "live_contentops.plan_status_posts_v1", "live_contentops.published_images_v1")},
    "exact_main_passage_admitted": True, "original_data_clock_consumed": True,
    "fresh_export_not_used_as_data_clock": True, "publication_clock_cause": clock_cause,
    "publication_status_cli_succeeded": True, "new_operations": 0, "editorial_model_calls": 0,
    "public_writes": 0, "pytest_processes": 0, "chat_messages": 0, "schedule_changes": 0,
    "feed_unchanged": info(feed)["sha256"] == feed_before["sha256"],
    "inherited_work_unchanged": all(info(Path(r["root"]) / r["relative_path"])["sha256"] == r["sha256"] for r in preserved)}
assert verification["feed_unchanged"] and verification["inherited_work_unchanged"]
save("verification.json", verification)
result = {"item": "CC-124", "observed_at_utc": now_text, "actual_entry_utc": "2026-11-10T19:17:07.698754Z",
    "new_articles": 0, "production_day": day_of(now), "daily_article_limit": daily_limit(now),
    "published_canonicals_today": pieces, "active_leases": leases, "first_cause": clock_cause,
    "choice": "Use the new post-CPI Main report as dated context; do not start a canonical article whose original data cutoff already exceeds the root CC-403 60-minute limit. Consume the next fresh Main report through the existing owners. No second CPI-day wrap or filler.",
    "authority": ["JIM_DECISION_89", "JIM_DECISION_98", "ROOT_CC403_READER_ARTICLE_V1"],
    "standing_status": "OPEN", "next_due_gmt7": "11 Nov 2026 08:17 GMT+7",
    "next_daily_wrap_gmt7": "11 Nov 2026 18:30 GMT+7",
    "configured_launch": {"process_id": 41060, "model": "gpt-6.1-sol", "effort": "max", "state": "CONFIGURED_NOT_OBSERVED"},
    "acceptance": "Source-check sub-step verified using installed consumers; no new publication or standing-item publication acceptance claimed."}
save("result.json", result)
print(json.dumps({k: result[k] for k in ("new_articles", "production_day", "daily_article_limit", "published_canonicals_today", "first_cause", "next_due_gmt7")}))
