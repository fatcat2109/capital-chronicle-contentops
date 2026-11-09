"""Locate exact held Main scenario fields without exporting account records."""
from hashlib import sha256
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-research\20261106-nfp\dossier-20261106T093133Z")
NAMES = ("primary-native.json", "critical-native.json", "owner-native.json", "native-hybrid-decision.json", "integrated-qualitative-evaluation.json")
KEY = re.compile(r"scenario|probabil|invalidation|countercase|market_implication|^p_|confidence", re.I)

def walk(value, pointer=""):
    if isinstance(value, dict):
        for key, child in value.items():
            at = pointer + "/" + str(key)
            if KEY.search(key):
                yield {"pointer": at, "value": child}
            else:
                yield from walk(child, at)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, pointer + "/" + str(index))

results = []
sources = [ROOT / name for name in NAMES]
daily = Path(r"A:\Capital Chronicle\ResearchRuns\claude-main-research\daily-research-portfolio-279805139\requests")
sources.extend(sorted(daily.glob("*/owner-native.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:6])
for source in sources:
    data = source.read_bytes()
    hits = list(walk(json.loads(data)))
    parsed = json.loads(data)
    results.append({"source": str(source), "sha256": sha256(data).hexdigest(), "matches": hits,
                    "candidate_fields": [sorted(c) for c in parsed.get("candidates", [])]})
(HERE / "main-scenario-search.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
for row in results:
    print(json.dumps({"source": row["source"], "sha256": row["sha256"], "match_count": len(row["matches"]),
                      "probability_fields": [hit for hit in row["matches"] if re.search(r"probabil|/p_", hit["pointer"])],
                      "candidate_fields": row["candidate_fields"][:1]}, ensure_ascii=True))

exports = Path(r"A:\Capital Chronicle\Runtime\MainPublicReports-v1")
latest = json.loads((exports / "latest-manifest.json").read_bytes())
manifest = json.loads((exports / latest["path"]).read_bytes())
print(json.dumps({"public_manifest_path": str(exports / latest["path"]),
                  "emitted_at_utc": manifest["emitted_at_utc"], "entry_count": len(manifest["entries"])}))
