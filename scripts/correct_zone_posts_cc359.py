"""One bounded CC-359 operation; the existing coordinator owns all sends and recovery."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.published_content_v1 import PRODUCTION_STORE
from live_contentops import plan_status_correction_cc359 as correction


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["prepare", "execute", "pending", "begin", "submit", "status"])
    p.add_argument("--request")
    p.add_argument("--response", type=Path)
    p.add_argument("--invocation", required=True)
    p.add_argument("--destination")
    args = p.parse_args()
    store = ContentOpsDurableStore(str(PRODUCTION_STORE), auto_migrate=False)
    coordinator, executor = correction.bind(store, invocation=args.invocation)
    if args.action in {"prepare", "execute"}:
        plan = correction.prepare(store)
        if args.destination:
            plan = {**plan, "destinations": [d for d in plan["destinations"] if d["destination"] == args.destination]}
        result = (coordinator.execute_plan(correction.KEY, plan) if args.action == "execute"
                  else coordinator.register_plan(correction.KEY, plan))
    elif args.action == "pending":
        result = executor.pending()
    elif args.action == "begin":
        result = executor.begin(args.request)
    elif args.action == "submit":
        response = json.loads(args.response.read_text(encoding="utf-8"))
        result = executor.submit(args.request, response)
        packet = executor._get(args.request, "request")
        if packet["request"]["action"] == "PUBLISH" and response.get("result", {}).get("status") == "SUCCESS":
            result["reconciliation"] = coordinator.reconcile_completed_native_publish(
                packet["request"]["dispatch_attempt_identity"], request_hash=args.request)
    else:
        result = [{k: d.get(k) for k in ["platform", "status", "public_object_id", "public_object_url"]}
                  for d in store.get_dispatches_for_work_item(correction.KEY)]
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
