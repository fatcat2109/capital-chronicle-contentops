"""One-shot CC-135 export from the existing read-only publication lifecycle.

Run without --apply first. Original dates/URL enrichment must be observed on the
exact confirmed public objects, never synthesized from dispatch or event clocks.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.native_publication_promotion_v1 import ReadOnlyStore  # noqa: E402
from live_contentops.published_content_v1 import (  # noqa: E402
    DEFAULT_FEED, PRODUCTION_STORE, append_record, article_metadata, load_json,
    record_from_corpus, utc,
)
from live_contentops.published_corpus_read_model_v1 import load_published_corpus  # noqa: E402


def backfill(store_path, feed_path, observations, *, apply=False, now=None):
    now = now or datetime.now(timezone.utc).isoformat()
    utc(now)
    store = ReadOnlyStore(store_path)
    corpus = load_published_corpus(store)
    observed = {}
    for item in observations:
        if (not isinstance(item, dict) or item.get("canonical_url") in observed
                or item.get("observation_source") != "BROWSEROS_NEO_EXACT_PUBLIC_PAGE"
                or not item.get("public_object_id")
                or not utc(item["published_at_utc"]) <= utc(item["observation_recorded_at_utc"]) <= utc(now)):
            raise ValueError("EXACT_ORIGINAL_PUBLICATION_OBSERVATION_REQUIRED")
        observed[item["canonical_url"]] = item
    records = []
    for article in corpus["articles"]:
        original = observed.get(article.canonical_url)
        if original is None or original["public_object_id"] != article.public_object_id:
            raise ValueError("CONFIRMED_POST_ORIGINAL_DATE_OBSERVATION_REQUIRED")
        with store.get_read_only_connection() as conn:
            row = conn.execute("SELECT m.payload FROM platform_dispatches d JOIN outbox_messages m "
                "ON m.message_id=d.message_id WHERE d.platform='substack' AND d.public_object_id=? "
                "AND m.work_item_id=?", (article.public_object_id, article.source_work_item_id)).fetchone()
        metadata = article_metadata(load_json(row["payload"]), require_notice=False)
        records.append(record_from_corpus(article, metadata, published_at_utc=original["published_at_utc"],
            recorded_at_utc=now, outlet_urls=original.get("outlet_urls")))
    # Validate every input first. An invalid later piece must not partially backfill.
    records.sort(key=lambda r: (r["published_at_utc"], r["content_id"]))
    results = [append_record(feed_path, r) if apply else {
        "status": "READY_NO_WRITE", "content_id": r["content_id"], "outlet_count": len(r["outlets"])
    } for r in records]
    return {"status": "BACKFILL_APPLIED" if apply else "BACKFILL_READY_NO_WRITE",
            "pieces": results, "piece_count": len(records),
            "feed_sha256": sha256(Path(feed_path).read_bytes()).hexdigest() if apply else None,
            "source_store_access": "SQLITE_MODE_RO_QUERY_ONLY", "provider_writes": 0,
            "recorded_at_utc": now}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    parser.add_argument("--feed", type=Path, default=DEFAULT_FEED)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = backfill(args.store, args.feed, load_json(args.observations.read_bytes()), apply=args.apply)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "BACKFILL_BLOCKED", "error_class": type(exc).__name__,
                          "cause": str(exc) if isinstance(exc, ValueError) else "INPUT_OR_OUTPUT_UNAVAILABLE"}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
