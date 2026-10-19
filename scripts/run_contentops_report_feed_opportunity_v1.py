"""Thin manual draft runner for the existing MainReportFeed/Simple operation.

Never clears pause or invokes publication. A paused invocation exits before store
construction. Actual provider use needs a separate pause-release authorization.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.llm_operator_control_v1 import llm_operator_pause_active


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pointer", type=Path, required=True)
    p.add_argument("--store", type=Path, required=True, help="Existing configured store or new explicit isolated draft store")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--run-id", required=True, help="Stable identity; reuse the same identity to resume interrupted work")
    p.add_argument("--published-memory-store", type=Path, required=True)
    p.add_argument("--published-memory-output-root", type=Path, required=True)
    a = p.parse_args(argv)
    if llm_operator_pause_active():
        print(json.dumps({"classification": "LLM_OPERATOR_PAUSED", "provider_calls": 0,
                          "store_opened": False, "public_writes": 0, "pause_cleared": False}))
        return 2
    from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.published_corpus_read_model_v1 import load_canonical_published_memory_read_only
    pointer = json.loads(a.pointer.read_bytes())
    memory, proof = load_canonical_published_memory_read_only(store_path=a.published_memory_store,
                                                             output_root=a.published_memory_output_root)
    feed = MainReportFeed(LatestReportDeliveryTracker(ContentOpsDurableStore(a.store)), pointer)
    result = feed.opportunity(output_dir=a.output_dir, run_id=a.run_id,
                              cutoff_utc=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                              published_memory=list(memory))
    print(json.dumps({"classification": result.get("classification"), "published_memory_proof": proof,
                      "public_write_performed": False, "publication_owner": "EXISTING_DURABLE_PUBLICATION_COORDINATOR_SEPARATE"}))
    return 0 if result.get("qualified_article_count", 0) else 2


if __name__ == "__main__":
    raise SystemExit(main())
