"""Admit exact Main prose for the decision-98 pre-US wrap; keep originals private."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys

HERE = Path(__file__).resolve().parent
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.plan_status_posts_v1 import read_export
from live_contentops.published_images_v1 import PublishedImages, daily_limit, day_of

NOW = datetime.now(timezone.utc)
RUNTIME = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
MAIN = Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-research\daily-research-portfolio-279805139\requests\request-91a0ed68b1eb799e\owner-native.json")
SCENARIOS = Path(r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower\report_upgrade_review_20261105\strategy\WEEKEND_WRAP_20261109_R2_SCENARIOS.md")


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def fragments(text, start=0, end=None):
    end = len(text) if end is None else end
    result = []
    while end - start > 1700:
        at = text.rfind(" ", start, start + 1700)
        result.append({"start": start, "end": at})
        start = at + 1
    if end > start:
        result.append({"start": start, "end": end})
    return result


raw = MAIN.read_bytes()
report = json.loads(raw)
digest = sha256(raw).hexdigest()
passages = []
for index in range(6):
    value = report["candidates"][index]["rationale"]
    # The first paragraph is analytical prose. Execution outcomes and trade geometry
    # remain outside the admitted source; no position or account fields are copied.
    end = value.index("\n")
    passages.append({"source_path": str(MAIN), "source_sha256": digest,
                     "source_json_pointer": f"/candidates/{index}/rationale",
                     "fragments": fragments(value, end=end)})
    # The explicitly authored alternative belongs to this market, not a joint
    # six-market probability. Preserve that distinction in the writer request.
    marker = value.find("Main alternative (")
    if marker >= 0:
        passages.append({"source_path": str(MAIN), "source_sha256": digest,
                         "source_json_pointer": f"/candidates/{index}/rationale",
                         "fragments": fragments(value, start=marker)})
for index in range(4):
    value = report["causal_alternatives"][index]["text"]
    passages.append({"source_path": str(MAIN), "source_sha256": digest,
                     "source_json_pointer": f"/causal_alternatives/{index}/text",
                     "fragments": fragments(value)})
for index in (0,):
    value = report["priced_in"][index]["text"]
    passages.append({"source_path": str(MAIN), "source_sha256": digest,
                     "source_json_pointer": f"/priced_in/{index}/text",
                     "fragments": fragments(value)})

base = {"authority_ref": "JIM_DECISION_89",
        "authorship_class": "CAPITAL_CHRONICLE_MAIN_REPORT_PROJECTION",
        "revision_at_utc": NOW.isoformat(),
        "candidate_catalyst_tags": ["pre-US-wrap", "CPI-week", "six-market"]}
records = [{**base, "headline_id": "cc124-pre-us-main-20261109",
            "headline_text": "Pre-US wrap: Monday's weaker dollar and fading oil premium leave gold and US stocks waiting for CPI",
            "source_url": "urn:cc-public-report:cc124:pre-us-main:20261109",
            "known_at_utc": datetime.fromtimestamp(MAIN.stat().st_mtime, timezone.utc).isoformat(),
            "passages": passages}]

scenario_raw = SCENARIOS.read_bytes()
scenario_text = scenario_raw.decode("utf-8-sig")
start, end = scenario_text.index("## 2."), scenario_text.index("## 6.")
parts = []
for match in re.finditer(r"[^|\n]+", scenario_text[start:end]):
    a, b = start + match.start(), start + match.end()
    if scenario_text[a:b].strip(" -:"):
        parts.extend(fragments(scenario_text, start=a, end=b))
records.append({**base, "headline_id": "cc124-pre-us-opus-scenarios-20261109",
                "headline_text": "Dated weekly geopolitical scenarios: model estimates set Sun 8 Nov, horizon through Fri 13 Nov",
                "source_url": "urn:cc-public-report:cc124:pre-us-opus-scenarios:20261109",
                "known_at_utc": "2026-11-08T23:26:00Z",
                "passages": [{"source_path": str(SCENARIOS), "source_sha256": sha256(scenario_raw).hexdigest(),
                              "fragments": parts[i:i+12]} for i in range(0, len(parts), 12)]})
source_dir = HERE / "source"
source_dir.mkdir(exist_ok=True)
index_path = source_dir / "index.json"
assert not (HERE / "source-admission.json").exists(), "Preserve admitted edition; do not replace it."
index_path.write_text(json.dumps({"schema_version": "contentops.retained_source_research.v1", "records": records}, indent=2) + "\n", encoding="utf-8")
research = RetainedSourceResearch(source_dir)
assert not research.gaps, research.gaps
assert len(research.records) == 2

profile = json.loads((LIVE / "config/native_desktop_operator_profile_v1.json").read_bytes())
profile["research_editions_root"].append(str(source_dir))
save("profile.json", profile)
export = read_export()
plans = [p for p in export["status"]["plans"] if p.get("registered_at_utc", "").startswith("2026-11-09")]
save("current-public-plans.json", {"generated_at_utc": export["status"]["generated_at_utc"],
    "consumer": "live_contentops.plan_status_posts_v1.read_export", "plans": [
        {k: p.get(k) for k in ("asset_id", "registered_at_utc", "scenario_analysis", "scenario_first_cause")}
        for p in plans]})
register = PublishedImages(RUNTIME / "published_images_v1.jsonl", published_feed=RUNTIME / "published_content_v1.jsonl")
pieces = register._daily_pieces(register.records(), NOW)
connection = sqlite3.connect((RUNTIME / "contentops_daily_app_v1.sqlite3").as_uri() + "?mode=ro", uri=True)
connection.row_factory = sqlite3.Row
leases = [dict(r) for r in connection.execute("SELECT lease_id,lease_key,status,expires_at FROM leases WHERE status='ACTIVE' AND expires_at>?", (NOW.isoformat().replace("+00:00", "Z"),))]
connection.close()
assert not leases, leases
assert len(pieces) < daily_limit(NOW)
result = {"observed_at_utc": NOW.isoformat(), "operating_head": subprocess.check_output(["git", "-C", str(LIVE), "rev-parse", "HEAD"], text=True).strip(),
          "production_date": str(day_of(NOW)), "daily_article_limit": daily_limit(NOW), "published_canonicals": sorted(pieces),
          "active_leases": leases, "source_hashes": {str(MAIN): digest, str(SCENARIOS): sha256(scenario_raw).hexdigest()},
          "research_revision": research.revision, "document_ids": list(research.records), "gaps": research.gaps,
          "current_public_plan_rows": len(plans), "source_consumer": str(sys.modules[RetainedSourceResearch.__module__].__file__),
          "configured_launch": {"process_id": 37008, "model": "gpt-6.1-sol", "effort": "max", "observation": "CONFIGURED_NOT_OBSERVED"},
          "choice": "Use new Monday Main analytical paragraphs and their market-specific estimates; dated Opus weekly scenarios remain explicitly dated, never silently recalibrated or treated as joint probabilities from separate market estimates."}
save("source-admission.json", result)
print(json.dumps({k: result[k] for k in ("production_date", "daily_article_limit", "published_canonicals", "active_leases", "document_ids", "gaps", "current_public_plan_rows")}))
