"""Run one bounded audience batch through the existing store/collector, without publishing."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import json
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.audience_collection_v1 import run_collection
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.model_invocation_usage_v1 import import_native_invocations, piece_usage
from scripts.export_contentops_weekly_engagement import export_weekly_engagement


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--published-day", help="GMT+7 publication date to recover")
    parser.add_argument("--limit", type=int, default=4)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--piece")
    args = parser.parse_args()
    if not 1 <= args.limit <= 200:
        parser.error("--limit must be between 1 and 200")
    store = ContentOpsDurableStore(args.store, auto_migrate=False)
    value = {"collection": run_collection(store, limit=args.limit, published_day=args.published_day),
             "model_usage": import_native_invocations(store), "observed_at_utc": datetime.now(timezone.utc).isoformat()}
    ending = datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Bangkok")).date().isoformat()
    value["weekly_digest"] = export_weekly_engagement(args.store, ending, args.store.parent / "daily_app_outputs" / "weekly-engagement")
    if args.piece:
        value["piece"] = piece_usage(store, args.piece)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    if sys.stdout:
        print(json.dumps({k: {a: b for a, b in v.items() if a not in {"outcomes", "excluded", "invocations"}} if isinstance(v, dict) else v
                          for k, v in value.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
