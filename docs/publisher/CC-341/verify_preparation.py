"""Verify preparation and the actual outstanding source requirement; no public write."""
from datetime import datetime, timezone
from hashlib import sha256
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=HERE / "verification.json")
args = parser.parse_args()
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.article_scenarios_v1 import validate_article_scenarios
from live_contentops.article_publication_quality_v1 import validate_snapshot_asset

editor = json.loads((HERE / "editorial-pass.json").read_bytes())
prepared = (HERE / "prepared-body.md").read_text(encoding="utf-8")
draft = (HERE / "supplied-draft.md").read_text(encoding="utf-8").strip()
source = Path(editor["inputs"]["source"]["path"])
assert sha256(source.read_bytes()).hexdigest() == editor["inputs"]["source"]["sha256"]
assert sha256((HERE / "prepared-body.md").read_bytes()).hexdigest() == editor["prepared_copy"]["sha256"]
assert draft == source.read_text(encoding="utf-8-sig").split("## Public-ready draft", 1)[1].strip()
normalize = lambda value: " ".join(value.split())
paragraphs = draft.rsplit("\n\n", 1)[0].split("\n\n")
assert all(normalize(paragraph) in normalize(prepared) for paragraph in paragraphs)
assert draft.rsplit("\n\n", 1)[1] not in prepared
assert prepared.rstrip().endswith("Analysis, not financial advice. Capital Chronicle may hold positions in the markets it covers.")
assert all(s["probability"] is None for s in editor["scenario_analysis"])
assert not editor["prepared_copy"]["rendered_review_or_publication_approval"]

research = RetainedSourceResearch(LIVE / "docs/publisher/CC-341/source")
assert not research.gaps, research.gaps
record = research.records["cc341-weekend-wrap-20261109"]
assert normalize(record["permitted_source_text"]) == normalize(draft)
asset = json.loads((HERE / "tradingview-asset.json").read_bytes())
validate_snapshot_asset(asset, market="USOIL", now=datetime.now(timezone.utc))
assert sha256((LIVE / "docs/publisher/CC-341/media" / Path(asset["path"]).name).read_bytes()).hexdigest() == asset["sha256"]

# Exercise the real decision-93 reader with the real, still-absent probabilities.
# This is evidence of an outstanding requirement, not publication acceptance.
article = {"substack_body_markdown": prepared, "scenario_analysis": [
    {"name": s["name"], "role": "base_case" if i == 0 else "alternative", "probability": s["probability"]}
    for i, s in enumerate(editor["scenario_analysis"])]}
try:
    validate_article_scenarios(article, [record["document"]])
except ValueError as exc:
    actual_requirement = str(exc)
else:
    raise AssertionError("The absent Main probabilities unexpectedly passed publication validation")
assert actual_requirement == "SCENARIO_PROBABILITY_REQUIRED", actual_requirement
result = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "preparation_checks": "PASS",
          "original_paragraphs_preserved": len(paragraphs), "source_consumer": str(Path(sys.modules[RetainedSourceResearch.__module__].__file__)),
          "source_consumer_read": "PASS", "snapshot_and_integrated_bytes": "PASS",
          "actual_remaining_requirement": actual_requirement, "reason": "JIM_DECISION_93",
          "three_geopolitical_probabilities": [s["probability"] for s in editor["scenario_analysis"]],
          "publication_acceptance_passed": False, "public_write_performed": False,
          "editorial_artifact_sha256": sha256((HERE / "editorial-pass.json").read_bytes()).hexdigest(),
          "prepared_body_sha256": sha256((HERE / "prepared-body.md").read_bytes()).hexdigest()}
args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
