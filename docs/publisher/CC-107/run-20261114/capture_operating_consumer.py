"""Read held event inputs through the installed Publisher source consumers."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.contentops_editorial_desk_v1 import preview_preparation_research
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE, read_records
from live_contentops.v1_simple_gemini_newsroom_v1 import _source_pack

HERE = Path(__file__).resolve().parent
now = datetime.now(timezone.utc).isoformat()
store = ContentOpsDurableStore(PRODUCTION_STORE, auto_migrate=False)
background = preview_preparation_research(store, event_id="bls-emsit-20261106", cutoff_utc=now, article_type="EVENT_REVIEW")
research = RetainedSourceResearch(LIVE / "docs/publisher/CC-124/run-20261106-2050/source",
    editions_root=LIVE / "docs/publisher/CC-107/run-20261114/source")
assert not research.gaps
primary = "cc107-nfp-dated-review-20261114"
research.records[primary]["supporting_headline_ids"] += list(background.records)
research.records.update(background.records)
evidence = research.evidence({"headline_ids": [primary]}, cutoff_utc=now)
pack = _source_pack(evidence["evidence_documents"])
assert any("matrix Brier score 0.02" in d["canonical_content_text"] for d in pack)
assert any("XAUUSD observed changes" in d["canonical_content_text"] for d in pack)
assert any(d["document_id"] == "bls-october-release" for d in pack)
assert all(sha256(d["canonical_content_text"].encode()).hexdigest() == d["canonical_content_sha256"] for d in pack)
rows = [r for r in read_records(DEFAULT_FEED) if any(o.get("url") in {
    "https://capitalchronicle.substack.com/p/nfp-preview-why-a-payroll-beat-needs",
    "https://capitalchronicle.substack.com/p/if-october-core-cpi-is-03-or-higher"} for o in r["outlets"])]
code = ["live_contentops/main_report_projection_source_v1.py", "live_contentops/contentops_source_research_v1.py",
    "live_contentops/contentops_editorial_desk_v1.py", "live_contentops/v1_simple_gemini_newsroom_v1.py"]
result = {"observed_at_utc": now, "installed_root": str(LIVE), "status": "OPERATING_SOURCE_CONSUMER_PASS",
    "source_count": len(pack), "main_computed_reaction_and_scores_consumed": True,
    "official_release_and_background_consumed": True, "every_delivered_text_hash_matches": True,
    "already_published_previews": [{"content_id": r["content_id"], "type": r["type"], "published_at_utc": r["published_at_utc"],
        "canonicals": [o["url"] for o in r["outlets"] if o["name"] == "substack"]} for r in rows],
    "installed_code": [{"path": str(LIVE / p), "sha256": sha256((LIVE / p).read_bytes()).hexdigest()} for p in code],
    "new_review_published": False, "digest_send_performed": False, "schedule_changed": False,
    "store_mode": "READ_ONLY_CONNECTIONS_NO_MIGRATIONS"}
(HERE / "operating-consumer-readback.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps({k:result[k] for k in ["status","source_count","new_review_published","digest_send_performed"]}))
