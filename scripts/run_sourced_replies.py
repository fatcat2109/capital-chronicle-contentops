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
    p.add_argument("command", choices=["stage", "publish", "status", "pack-prepare", "pack-build", "pack-status", "pack-observe", "pack-report",
                                       "tabs-refresh", "tabs-status", "tabs-enable",
                                       "api-poll", "api-publish", "api-status"])
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
    p.add_argument("--request", type=Path)
    p.add_argument("--response", type=Path)
    p.add_argument("--pack", type=Path)
    p.add_argument("--output-root", type=Path)
    p.add_argument("--mentions-feed", type=Path)
    p.add_argument("--reply-feed", type=Path)
    p.add_argument("--x-approval-ref")
    args = p.parse_args()
    store = ContentOpsDurableStore(args.store, auto_migrate=False)
    if args.command.startswith("tabs-"):
        from live_contentops import x_reply_tabs_v1 as tabs
        if args.command == "tabs-refresh":
            result = tabs.refresh_due(store, force=True, feed_path=args.feed,
                                      **({"output_root": args.output_root} if args.output_root else {}))
        elif args.command == "tabs-enable":
            result = tabs.enable_cadence(store)
        else:
            result = {"state": tabs.latest_state(store), "cadence":
                      tabs.packs.read_json(tabs.CONTROL) if tabs.CONTROL.is_file() else {"enabled": False}}
    elif args.command.startswith("api-"):
        from live_contentops import x_mention_responder_v1 as api
        if args.command == "api-status":
            result = {"cost": api.budget(store), "last_run": next(reversed(api._values(store, "internal:x-api-mention-run")), None)}
        else:
            options = {"feed_path": args.feed}
            if args.output_root:
                options["output_root"] = args.output_root
            if args.command == "api-poll":
                result = api.poll(store, mentions_path=args.mentions_feed, **options)
            else:
                if not args.request or not args.response or not args.mentions_feed:
                    p.error("--request, --response and --mentions-feed required")
                result = api.publish_from_request(store, request_path=args.request, response_path=args.response,
                                                  mentions_path=args.mentions_feed, x_approval_ref=args.x_approval_ref, **options)
    elif args.command.startswith("pack-"):
        from live_contentops import x_reply_pack_v1 as packs

        if args.command == "pack-report":
            result = packs.report_manual_replies(store)
        elif args.command == "pack-observe":
            result = packs.observe_manual_replies(store, reply_feed_path=args.reply_feed or args.feed)
        elif args.command == "pack-status":
            if not args.pack:
                p.error("--pack required")
            result = packs.read_pack(args.pack)
        else:
            options = dict(store=store, feed_path=args.feed, mentions_path=args.mentions_feed)
            if args.output_root:
                options["output_root"] = args.output_root
            if args.command == "pack-prepare":
                result = packs.prepare(**options)
            else:
                if not args.request or not args.response:
                    p.error("--request and --response required")
                result = packs.build(**options, request_path=args.request, response_path=args.response)
                result["readback"] = packs.observe_manual_replies(store, reply_feed_path=args.reply_feed or args.feed)
    elif args.command == "stage":
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
