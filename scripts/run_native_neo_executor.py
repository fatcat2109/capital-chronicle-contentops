"""Active Desktop Neo request/begin/submit/readback loop; Python never calls MCP.

This helper does not publish or save drafts. It binds the existing coordinator to an
explicit native operation. The Desktop conversation executes pending Neo requests and
submits their observed result. Recovery is readback-only, including under KILL_SWITCH.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired, bind_native_neo_coordinator

SCHEMA = "contentops.native_neo_operation_binding.v1"
PRODUCTION_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps")


def operation(binding, *, command, request_hash=None, response=None, dispatch_id=None, surface=None):
    if binding.get("schema_version") != SCHEMA or not binding.get("operation_id") or not binding.get("native_invocation_id"):
        raise ValueError("NATIVE_NEO_OPERATION_BINDING_INVALID")
    for key in ("store_path", "output_dir"):
        path = Path(binding[key])
        if not path.is_absolute():
            raise ValueError("NATIVE_NEO_ABSOLUTE_PATH_REQUIRED")
        if binding.get("owner_manual_validation") and (
                path.resolve() == PRODUCTION_ROOT.resolve() or PRODUCTION_ROOT.resolve() in path.resolve().parents):
            raise ValueError("MANUAL_NEO_VALIDATION_MUST_USE_ISOLATED_STATE")
    if binding.get("allow_publish"):
        raise ValueError("THIS_NATIVE_NEO_HELPER_IS_READBACK_ONLY")
    store = ContentOpsDurableStore(binding["store_path"])
    work = "native-neo-operation-" + sha256_of(binding["operation_id"])
    key = "native-neo-operation-binding-" + sha256_of(binding["operation_id"])
    previous = store.get_outbox_message(key)
    if previous and json.loads(previous["payload"]) != binding:
        raise ValueError("NATIVE_NEO_OPERATION_BINDING_CHANGED")
    store.create_work_item(story_id=work, work_item_id=work,
                           title="Native Neo exact identity observation", target_surface="CONTENTOPS_READ_ONLY")
    row = store.register_outbox_message(message_id=key, work_item_id=work,
        destination="internal:native-neo-tool", payload=canonical_bytes(binding).decode(), status="NATIVE_NEO_INTERNAL")
    if json.loads(row["payload"]) != binding:
        raise ValueError("NATIVE_NEO_OPERATION_BINDING_CHANGED")
    coordinator, executor = bind_native_neo_coordinator(store, operation_id=binding["operation_id"],
        output_dir=binding["output_dir"], native_invocation_id=binding["native_invocation_id"], allow_publish=False)
    try:
        if command == "status":
            result = {"pending_requests": executor.pending()}
        elif command == "begin":
            result = executor.begin(request_hash)
        elif command == "submit":
            result = executor.submit(request_hash, response)
        elif command == "verify":
            result = coordinator.readiness_manager.probe_surface(surface)
        elif command == "readback":
            result = coordinator.readback_existing_dispatch(dispatch_id)
        elif command == "recover":
            # Reuse reconciliation only. The generic recovery loop may publish an absence-
            # safe API/bot obligation, so this explicit read-only helper never invokes it.
            result = {"per_dispatch": [coordinator.readback_existing_dispatch(row["dispatch_id"])
                for row in store.list_platform_dispatches()
                if row["status"] in {"UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED"}],
                "recovery_mode": "READBACK_ONLY_NO_RETRY"}
        else:
            raise ValueError("NATIVE_NEO_COMMAND_INVALID")
    except NativeNeoInputRequired as pending:
        result = {"classification": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": pending.request}
    return {**result, "pending_requests": executor.pending(), "public_write_performed": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "begin", "submit", "verify", "readback", "recover"))
    parser.add_argument("--binding", required=True, type=Path)
    parser.add_argument("--request-sha256")
    parser.add_argument("--response", type=Path)
    parser.add_argument("--dispatch-id")
    parser.add_argument("--surface", choices=("SUBSTACK_ARTICLE", "X_POST", "X_THREAD", "YOUTUBE_COMMUNITY_POST"))
    args = parser.parse_args(argv)
    result = operation(json.loads(args.binding.read_bytes()), command=args.command,
        request_hash=args.request_sha256, response=json.loads(args.response.read_bytes()) if args.response else None,
        dispatch_id=args.dispatch_id, surface=args.surface)
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
