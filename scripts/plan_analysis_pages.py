"""One bounded CC-432 action, reusing the production store and sole coordinator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.published_content_v1 import PRODUCTION_STORE
from live_contentops.plan_status_posts_v1 import read_export


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["render", "register", "status", "resume", "begin", "submit"])
    parser.add_argument("--plan-id", required=True)
    parser.add_argument("--manuscript", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--store", type=Path, default=PRODUCTION_STORE)
    parser.add_argument("--native-invocation-id", default="")
    parser.add_argument("--request-hash")
    parser.add_argument("--response", type=Path)
    parser.add_argument("--result", type=Path, help="save full native request/result; print identifiers only")
    parser.add_argument("--rollout", type=Path, default=Path("config/native_desktop_rollout_v1.json"))
    args = parser.parse_args(argv)
    store = ContentOpsDurableStore(args.store, auto_migrate=False)
    if args.command in {"render", "register"}:
        plan = next(p for p in read_export()["status"]["plans"] if p["plan_id"] == args.plan_id)
        folder = args.output_dir or args.store.parent / "daily_app_outputs" / "owner-manual" / ("plan-analysis-" + args.plan_id)
        packet = pages.render(plan, json.loads(args.manuscript.read_bytes()), output_dir=folder)
        if args.command == "register":
            packet = pages.register_page(store, packet)
        result = {"plan_id": args.plan_id, "output_dir": str(folder), "word_count": len(packet["native_payload"]["body_markdown"].split()),
                  "paragraphs": len(packet["numeric_bindings"]), "state": "REGISTERED" if args.command == "register" else "RENDERED"}
    else:
        packet = json.loads(store.get_outbox_message("plan-analysis-" + args.plan_id)["payload"])
        if args.command == "status":
            result = pages.page_status(store, packet)
        else:
            result = pages.continue_page(store, packet, invocation_id=args.native_invocation_id,
                rollout=json.loads(args.rollout.read_bytes()), command=args.command, request_hash=args.request_hash,
                response=json.loads(args.response.read_bytes()) if args.response else None)
    if sys.stdout:
        sys.stdout.reconfigure(encoding="utf-8")
        if args.result:
            args.result.write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str),encoding="utf-8")
            requests = ([result["native_tool_request"]] if result.get("native_tool_request") else result.get("pending_requests", []))
            print(json.dumps({"result_path":str(args.result),"state":result.get("state"),"confirmed":result.get("confirmed"),
                "pending":[{"request_sha256":r["request"]["request_sha256"],"action":r["request"]["action"],
                            "path":r.get("request_path")} for r in requests]},indent=1))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
