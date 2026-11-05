"""Reuse exact held federal-source captures in the existing source owner."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import csv
import json
import shutil
import sys

LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch

RUN = Path(__file__).resolve().parent
OP = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-nfp-us500-preview-20261105-g")
ROOT = OP / "source-editions-jobs-treasury"
BASE = OP.parent
ROOT.mkdir(exist_ok=True)
records = []
sources = [
    ("jobs", BASE / "cc124-next-article-20261104-a" / "source-recovery-september-employment",
     {"cc124-bls-september-employment-original"}),
    ("treasury", BASE / "cc124-gold-yields-20261105-e" / "source-editions-treasury",
     {"cc124-treasury-nominal-20261104", "cc124-bls-november-calendar"}),
]
for prefix, origin, ids in sources:
    target = ROOT / prefix
    target.mkdir(exist_ok=True)
    specs = json.loads((origin / "index.json").read_bytes())["records"]
    for source in specs:
        if source["headline_id"] not in ids:
            continue
        record = deepcopy(source)
        for key in ("capture_path", "original_capture_path", "loader_result_path", "policy_capture_path"):
            if key in record:
                name = record[key]
                shutil.copy2(origin / name, target / name)
                assert (origin / name).read_bytes() == (target / name).read_bytes()
                record[key] = prefix + "/" + name
        if prefix == "jobs":
            document = json.loads((origin / "admission.json").read_bytes())["official_source_documents"][0]
            text = document["canonical_content_text"]
            # Select held official narrative, wages/revisions and B-1 components.
            # No source content or clocks are changed.
            wages = text.index("In September, average hourly earnings")
            end = text.index("The Employment Situation", wages)
            record["context_spans"] = [[4716, 5350], [wages, end], [80489, 81030], [85095, 85187]]
        records.append(record)
shutil.copy2(sources[1][1] / "nominal.csv", ROOT / "treasury" / "nominal.csv")
shutil.copy2(sources[1][1] / "nominal.csv", ROOT / "nominal.csv")
(ROOT / "index.json").write_text(json.dumps({"schema_version": "contentops.retained_source_research.v1",
    "records": records}, indent=2) + "\n", encoding="utf-8")
research = RetainedSourceResearch(ROOT)
assert not research.gaps, research.gaps
assert len(research.records) == 3
pending = json.loads((OP / "source_preparation_required.json").read_bytes())
selection = json.loads((OP / "desktop_request_select.json").read_bytes())
walk = OP / "simple_gemini_evidence_v1.json"
walk_value = json.loads(walk.read_bytes())
requests = []
for issued in pending["source_requests"]:
    record = next(r for r in research.records.values() if r["document"]["source_url"] == issued["url"])
    spec = next(r for r in records if r["headline_id"] == record["document"]["document_id"])
    capture = ROOT / spec["capture_path"]
    if sha256(capture.read_bytes()).hexdigest() != record["source_capture_sha256"]:
        # Browser-rendered envelopes bind the visible original separately.
        prefix, origin, _ = next(s for s in sources if spec["capture_path"].startswith(s[0] + "/"))
        original = next(q for q in origin.iterdir() if q.is_file()
            and sha256(q.read_bytes()).hexdigest() == record["source_capture_sha256"])
        capture = ROOT / prefix / original.name
        shutil.copy2(original, capture)
    requests.append({**issued, "non_chargeable": True, "observed_at_utc": record["retrieval_time_utc"],
        "capture_path": str(capture), "capture_sha256": sha256(capture.read_bytes()).hexdigest(),
        "clock_basis": "Exact held original acquisition reused; no network reacquisition or clock refresh"})
value = {"within_bound_live_budget": True,
    "expected_selection_request_sha256": selection["request_sha256"],
    "expected_source_request_sha256": pending["request_sha256"],
    "expected_evidence_sha256": sha256(walk.read_bytes()).hexdigest(),
    "candidate_id": walk_value["selected_candidate_id"], "research_root": str(ROOT),
    "supporting_headline_ids": list(research.records), "additional_source_requests": requests,
    "owner_instruction": "Use September BLS release dated October 2 as prior context, official November 6 schedule, and Treasury yields through November 4 as dated background. No current US500/US10Y spot, payroll result, forecast, consensus or directional call is supplied. Distinct daily US500 rates-versus-growth question; do not replace the CC216/CC107 event preview. Treat mechanisms as conditional. Source publication and acquisition clocks remain original. Parent independently checked both BLS public pages in Neo at 15:50-15:53Z November5."}
(RUN / "source-recovery-input.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
rows = list(csv.DictReader((ROOT / "treasury" / "nominal.csv").read_text(encoding="utf-8-sig").splitlines()))
rows.sort(key=lambda r: datetime.strptime(r["Date"], "%m/%d/%Y"))
latest = rows[-1]
assert datetime.strptime(latest["Date"], "%m/%d/%Y").date().isoformat() == "2026-11-04"
summary = {"prepared_at_utc": datetime.now(timezone.utc).isoformat(), "source_root": str(ROOT),
    "verified_source_ids": list(research.records), "gaps": research.gaps,
    "latest_treasury": {"date": latest["Date"], "10_year_percent": latest["10 Yr"]},
    "retained_text": {k: r["permitted_source_text"] for k, r in research.records.items()},
    "rights": {k: r["source_permissions"] for k, r in research.records.items()}}
(RUN / "official-data-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"verified_sources": list(research.records), "gaps": research.gaps,
    "latest_treasury": summary["latest_treasury"], "recovery_input": str(RUN / "source-recovery-input.json")}))
