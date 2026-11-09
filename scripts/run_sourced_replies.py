"""Bounded CC-386 operator entry. No schedule, discovery loop or new transport."""

from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.sourced_replies_v1 import stage, publish, report, ROOT


def main():
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["stage", "publish", "status"])
    p.add_argument("--store", required=True)
    p.add_argument("--candidate", type=Path)
    p.add_argument(
        "--feed",
        type=Path,
        default=Path(
            r"A:\Capital Chronicle\Runtime\ContentOps\x_list_feed\x_list_feed_v1.json"
        ),
    )
    p.add_argument("--key")
    p.add_argument("--native-invocation-id")
    args = p.parse_args()
    store = ContentOpsDurableStore(args.store, auto_migrate=False)
    if args.command == "stage":
        if not args.candidate:
            p.error("--candidate required")
        result = stage(
            store,
            json.loads(args.candidate.read_bytes()),
            feed=json.loads(args.feed.read_bytes()),
        )
    elif args.command == "publish":
        if not args.key or not args.native_invocation_id:
            p.error("--key and --native-invocation-id required")
        from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator

        coordinator, _ = bind_native_neo_coordinator(
            store,
            operation_id=args.key,
            output_dir=ROOT / args.key / "native-neo",
            native_invocation_id=args.native_invocation_id,
            allow_publish=True,
        )
        result = publish(store, args.key, coordinator=coordinator)
    else:
        result = report(store)
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
