"""Project only CC-341's supplied public draft through the existing Main source owner."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch

HERE = Path(__file__).resolve().parent
SOURCE = Path(r"A:\Capital Chronicle\control-tower-reporting-closeout-20261018\docs\project_control_tower\report_upgrade_review_20261105\strategy\WEEKEND_WRAP_20261109.md")
raw = SOURCE.read_bytes()
text = raw.decode("utf-8-sig")
start = text.index("## Public-ready draft") + len("## Public-ready draft")
public = text[start:].strip()
fragments = []
for match in re.finditer(r"\S[\s\S]*?(?=\n\s*\n|\Z)", text[start:]):
    a, b = start + match.start(), start + match.end()
    # Each source fragment is bounded by the established projection contract.
    while b - a > 1800:
        split = text.rfind(" ", a, a + 1800)
        fragments.append({"start": a, "end": split})
        a = split + 1
    fragments.append({"start": a, "end": b})

spec = {
    "authority_ref": "JIM_DECISION_89",
    "authorship_class": "CAPITAL_CHRONICLE_MAIN_REPORT_PROJECTION",
    "source_url": "urn:cc-public-report:cc341:weekend-wrap:20261109",
    "headline_id": "cc341-weekend-wrap-20261109",
    "headline_text": "Tanker strikes, US strikes on Iran and a softer word from Trump: what markets carry into Monday and a CPI week",
    "known_at_utc": "2026-11-08T18:20:00Z",
    "revision_at_utc": datetime.now(timezone.utc).isoformat(),
    "candidate_catalyst_tags": ["weekend-wrap", "Hormuz", "CPI-week", "six-market"],
    "passages": [{"source_path": str(SOURCE), "source_sha256": sha256(raw).hexdigest(),
                  "fragments": fragments[i:i + 12]} for i in range(0, len(fragments), 12)],
}
folder = HERE / "source"
folder.mkdir(exist_ok=True)
index = folder / "index.json"
if index.exists():
    previous = json.loads(index.read_bytes())
    assert previous["records"][0]["passages"][0]["source_sha256"] == sha256(raw).hexdigest(), "Source revision changed; preserve this edition and prepare a new one."
else:
    index.write_text(json.dumps({
        "schema_version": "contentops.retained_source_research.v1", "records": [spec]}, indent=2) + "\n", encoding="utf-8")
research = RetainedSourceResearch(folder)
assert not research.gaps, research.gaps
record = research.records[spec["headline_id"]]
assert " ".join(record["permitted_source_text"].split()) == " ".join(public.split())
assert "Our capture:" not in record["permitted_source_text"]
result = {"source_path": str(SOURCE), "source_sha256": sha256(raw).hexdigest(),
          "consumer": "live_contentops.contentops_source_research_v1.RetainedSourceResearch",
          "consumer_module": str(sys.modules[RetainedSourceResearch.__module__].__file__),
          "research_revision": research.revision, "document_id": spec["headline_id"],
          "public_text_sha256": record["document"]["canonical_content_sha256"],
          "fragments": len(fragments), "gaps": research.gaps,
          "public_draft_only": True, "public_write_performed": False}
(HERE / "source-verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result))
