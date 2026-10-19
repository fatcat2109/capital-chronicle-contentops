"""One bounded draft-only opportunity and governed headline export, no publication/runtime."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    LatestReportDeliveryTracker,
)
from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
from live_contentops.contentops_main_headline_projection_v1 import (
    MainHeadlineExporter,
    permitted_report_headlines,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_dir
from live_contentops.published_corpus_read_model_v1 import (
    load_canonical_published_memory_read_only,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pointer", type=Path, required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--opportunity-id", required=True)
    parser.add_argument("--scan-only", action="store_true")
    parser.add_argument("--research-root", type=Path)
    parser.add_argument(
        "--headline-root", type=Path, default=canonical_headline_sidecar_dir()
    )
    parser.add_argument(
        "--published-memory-store",
        type=Path,
        default=Path(
            r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3"
        ),
    )
    parser.add_argument(
        "--published-memory-output-root",
        type=Path,
        default=Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs"),
    )
    args = parser.parse_args(argv)
    if (
        args.store.resolve()
        == Path(
            r"A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3"
        ).resolve()
    ):
        parser.error(
            "Manual integration proof requires an isolated store; production hook uses its existing owner."
        )
    cutoff = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    tracker = LatestReportDeliveryTracker(ContentOpsDurableStore(args.store))
    paths = sorted(args.headline_root.glob("step1_headline_sidecar_*.jsonl"))[-4:]
    pointer = json.loads(args.pointer.read_bytes())
    if args.research_root:
        pointer["research_root"] = str(args.research_root.resolve())
    feed = MainReportFeed(tracker, pointer, headline_paths=paths)
    scan = feed.poll(cutoff_utc=cutoff)
    memory, proof = load_canonical_published_memory_read_only(
        store_path=args.published_memory_store,
        output_root=args.published_memory_output_root,
    )
    result = (
        None
        if args.scan_only
        else feed.opportunity(
            output_dir=args.output_dir / "article",
            cutoff_utc=cutoff,
            run_id=args.opportunity_id,
            published_memory=memory,
        )
    )
    export = MainHeadlineExporter(tracker.store, research=feed.retained_research).export(
        batch_id=args.opportunity_id,
        paths=paths,
        cutoff_utc=cutoff,
        permitted_rows=permitted_report_headlines(tracker),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in (
        ("main_headline_projection.json", export),
        ("feed_scan.json", scan),
    ):
        (args.output_dir / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    with (args.output_dir / "main_headline_rows.jsonl").open(
        "w", encoding="utf-8", newline="\n"
    ) as stream:
        for row in export["rows"]:
            stream.write(json.dumps(row, sort_keys=True) + "\n")
    receipt = {
        "schema_version": "contentops.goal19.manual_intelligence_loop_receipt.v1",
        "observed_at_utc": cutoff,
        "counts": tracker.counts(),
        "headline_rows_scanned": export["source_rows_scanned"],
        "headline_rows_eligible": export["eligible_rows"],
        "headline_rows_missing": export["missing_rows"],
        "independent_items": export["independent_items"],
        "main_origin_recirculated_items": export["main_origin_recirculated_items"],
        "published_memory_proof": proof,
        "exact_next_blocker": (result or {}).get("exact_next_blocker"),
        "public_writes": 0,
        "schedule_activated": False,
        "result_classification": (result or {}).get("classification"),
    }
    (args.output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
