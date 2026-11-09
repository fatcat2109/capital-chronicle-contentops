"""Read held Main outputs for CC-341; never print execution rows or raw exports."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO))
from live_contentops.plan_status_posts_v1 import read_export

roots = [Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-events-20261029"),
         Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-research\daily-research-portfolio-279805139\requests")]
paths = list(roots[0].rglob("*.md")) + list(roots[1].glob("*/owner-native.json"))
data_roots = [REPO / "data/research", Path(r"A:\Capital Chronicle\ContentOps\data\research")]
data_inventory = []
for root in data_roots:
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".json", ".jsonl", ".md", ".txt"}]
    paths.extend(files)
    data_inventory.append({"path": str(root), "exists": root.exists(), "searched_text_files": len(files)})

rows = []
for path in sorted(set(paths)):
    if any(word in path.name.lower() for word in ("credential", "secret", ".env")):
        continue
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    relevant = list(re.finditer(r"Hormuz|Qeshm|Iran.s offer|two.day plan", text, re.I))
    probability_spans = []
    for match in relevant:
        excerpt = text[max(0, match.start() - 180):match.end() + 240]
        if re.search(r"probab|\bchance|\d{1,2}\s*%", excerpt, re.I):
            probability_spans.append({"offset": match.start(), "line": text[:match.start()].count("\n") + 1})
    rows.append({"path": str(path), "sha256": sha256(raw).hexdigest(),
                 "modified_at_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                 "relevant_geopolitical_spans": len(relevant), "possible_probability_spans": probability_spans})

def scenarios_in(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "scenario_analysis":
                yield child
            else:
                yield from scenarios_in(child)
    elif isinstance(value, list):
        for child in value:
            yield from scenarios_in(child)

print(json.dumps({"searched_held_sources": len(rows), "reading_installed_export": True}), flush=True)
scenarios = list(scenarios_in(read_export()))
backlog = []
folder = Path(r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower")
for name in ("BACKLOG.md", "BACKLOG_ARCHIVE.md"):
    path = folder / name
    raw = path.read_bytes()
    lines = raw.decode("utf-8").splitlines()
    backlog.append({"path": str(path), "sha256": sha256(raw).hexdigest(), "matching_lines": [
        i + 1 for i, line in enumerate(lines) if re.search(r"Hormuz|weekend.wrap|weekend market", line, re.I)]})

result = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "searched_sources": rows,
          "other_lane_export_consumer": "live_contentops.plan_status_posts_v1.read_export",
          "export_scenarios": len(scenarios),
          "export_null_scenarios": sum(x is None for x in scenarios),
          "export_missing_base_probability": sum(((x or {}).get("base_case") or {}).get("probability_pct") is None for x in scenarios),
          "export_missing_alternative_probability": sum(((x or {}).get("main_alternative") or {}).get("probability_pct") is None for x in scenarios),
          "data_research_paths": data_inventory, "backlog_and_archive": backlog,
          "not_substituted": ["CPI outcome-bin probabilities", "Fed December hike market odds", "direction confidence", "old scenario weights for different events"],
          "first_cause": "JIM_DECISION_93_MAIN_WEEKEND_SCENARIOS_INCOMPLETE"}
(HERE / "additional-source-search.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"sources": len(rows), "export_scenarios": len(scenarios),
                  "missing_alternative_probability": result["export_missing_alternative_probability"],
                  "data_research_paths": data_inventory}))
