"""Export CC-338's public-call projection using the existing feed and outbox."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore  # noqa: E402
from live_contentops.public_call_scorecard_v1 import SINCE, build_scorecard, render_scorecard  # noqa: E402
from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    parser.add_argument("--feed", type=Path, default=DEFAULT_FEED)
    parser.add_argument("--since", default=SINCE)
    parser.add_argument("--as-of")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    store = ContentOpsDurableStore(str(args.store), auto_migrate=False)
    scorecard = build_scorecard(store, feed_path=args.feed, since_utc=args.since, as_of_utc=args.as_of)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "public-call-scorecard.json").write_text(
        json.dumps(scorecard, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "public-call-scorecard.md").write_text(render_scorecard(scorecard), encoding="utf-8")
    print(json.dumps({"total_calls": scorecard["total_calls"], "state_counts": scorecard["state_counts"],
                      "output_dir": str(args.output_dir)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
