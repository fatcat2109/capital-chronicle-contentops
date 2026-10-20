"""One native Desktop opportunity; no timer, model API, activation or publishing.

In a Desktop chat: advance -> read pending request -> reason -> submit -> advance.
All phases may run in the SAME turn. Binding is explicit and immutable per opportunity.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker, canonical_bytes, sha256_of
from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.llm_operator_control_v1 import llm_operator_pause_active
from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired, NativeDesktopTurn, DESTINATION
from live_contentops.published_corpus_read_model_v1 import load_canonical_published_memory_read_only

BINDING_SCHEMA = "contentops.native_desktop_operation_binding.v1"
PRODUCTION_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps")


def validate_binding(binding):
    if binding.get("schema_version") != BINDING_SCHEMA or not binding.get("run_id"):
        raise ValueError("NATIVE_OPERATION_BINDING_INVALID")
    for key in ("store_path", "output_dir", "feed_pointer_path", "published_memory_store", "published_memory_output_root"):
        if not Path(binding[key]).is_absolute():
            raise ValueError("ABSOLUTE_OPERATION_PATH_REQUIRED:" + key)
    isolated = bool(binding.get("owner_manual_validation"))
    if isolated:
        for key in ("store_path", "output_dir"):
            path = Path(binding[key]).resolve()
            if path == PRODUCTION_ROOT.resolve() or PRODUCTION_ROOT.resolve() in path.parents:
                raise ValueError("MANUAL_VALIDATION_MUST_USE_ISOLATED_TASK_STATE")
    elif llm_operator_pause_active():
        raise ValueError("LLM_OPERATOR_PAUSED")
    return binding


def operation(binding, *, command="advance", response=None, stage=None):
    validate_binding(binding)  # Before opening/migrating any store.
    store = ContentOpsDurableStore(Path(binding["store_path"]))
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    key = "native-operation-binding-" + sha256_of(binding["run_id"])
    previous = store.get_outbox_message(key)
    if previous and json.loads(previous["payload"]) != binding:
        raise ValueError("NATIVE_OPERATION_BINDING_CHANGED")
    store.create_work_item(story_id=work, title="Main-enriched newsroom opportunity",
                           target_surface="CONTENTOPS_EDITORIAL_ONLY", work_item_id=work)
    if not previous:
        store.register_outbox_message(message_id=key, work_item_id=work, destination=DESTINATION,
            payload=canonical_bytes(binding).decode(), status="EDITORIAL_INTERNAL")
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"],
                             owner_manual_validation=binding.get("owner_manual_validation", False))
    if command == "submit":
        return turn.submit(stage, response)
    if command == "status":
        return turn.telemetry()
    if command == "review":
        from live_contentops.contentops_editorial_desk_v1 import record_native_article_review
        return record_native_article_review(store, run_id=binding["run_id"], **response)
    if command == "handoff":
        from live_contentops.native_desktop_editorial_v1 import prepare_reviewed_handoff
        return prepare_reviewed_handoff(store, run_id=binding["run_id"], output_dir=binding["output_dir"])
    # Recover through the existing coordinator BEFORE another semantic/public intent.
    ambiguous = [d["dispatch_id"] for d in store.list_platform_dispatches()
                 if any(s in str(d.get("status", "")).upper() for s in ("UNKNOWN", "AMBIGUOUS", "STARTED", "PENDING"))]
    if ambiguous:
        return {"classification": "RECOVERY_REQUIRED", "dispatch_ids": ambiguous,
                "next_operation": "Existing DurablePublicationCoordinator readback/reconciliation; do not retry publishing",
                "public_write_performed": False}
    owner = "native-desktop-" + uuid4().hex
    lease = store.acquire_lease("internal:native-editorial:" + binding["run_id"], owner, ttl_seconds=900)
    try:
        memory, memory_proof = load_canonical_published_memory_read_only(
            store_path=binding["published_memory_store"], output_root=binding["published_memory_output_root"])
        pointer = json.loads(Path(binding["feed_pointer_path"]).read_bytes())
        feed = MainReportFeed(LatestReportDeliveryTracker(store), pointer)
        kwargs = {"output_dir": binding["output_dir"], "cutoff_utc": binding["cutoff_utc"],
                  "run_id": binding["run_id"], "published_memory": memory, "llm_invoke": turn,
                  "attempted_candidate_ids": binding.get("attempted_candidate_ids", [])}
        if binding.get("rolling_input_path"):
            kwargs["rolling_input"] = json.loads(Path(binding["rolling_input_path"]).read_bytes())
        try:
            result = feed.opportunity(**kwargs)
        except DesktopInputRequired as pending:
            return {"classification": "NATIVE_DESKTOP_INPUT_REQUIRED", "stage": pending.request["stage"],
                    "request_path": pending.request["request_path"],
                    "request_sha256": pending.request["request_sha256"],
                    "editorial_execution": turn.telemetry(), "public_write_performed": False}
        result["native_published_memory_proof"] = memory_proof
        result["publication_handoff_state"] = "REVIEW_REQUIRED_NO_DISPATCH" if result.get("qualified_article_count") else "NO_QUALIFIED_HANDOFF"
        root = Path(binding["output_dir"])
        root.mkdir(parents=True, exist_ok=True)
        (root / "native_desktop_result.json").write_bytes(canonical_bytes(result))
        return {k: result.get(k) for k in ("classification", "qualified_article_count", "derivative_intent_count",
            "exact_next_blocker", "article_path", "native_derivative_preview_path", "publication_handoff_state", "editorial_execution")}
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("advance", "submit", "status", "scheduled", "review", "handoff"))
    parser.add_argument("--binding", type=Path)
    parser.add_argument("--rollout", type=Path)
    parser.add_argument("--automation-id")
    parser.add_argument("--response", type=Path)
    parser.add_argument("--stage", help="select/write/revise or exact pending filter-<batch sha256>")
    args = parser.parse_args(argv)
    if args.command == "submit" and (not args.response or not args.stage):
        parser.error("submit requires --response and --stage")
    if args.command == "review" and not args.response:
        parser.error("review requires --response with article_identity/decision/rationale/expected_review_id")
    if args.command == "scheduled":
        if not args.rollout or not args.automation_id:
            parser.error("scheduled requires --rollout and --automation-id")
        from live_contentops.native_desktop_schedule_binding_v1 import scheduled_binding
        result = scheduled_binding(json.loads(args.rollout.read_bytes()), args.automation_id)
        print(json.dumps(result))
        return 0
    if not args.binding:
        parser.error("--binding is required")
    try:
        binding = json.loads(args.binding.read_bytes())
        result = operation(binding, command=args.command, stage=args.stage,
                           response=json.loads(args.response.read_bytes()) if args.response else None)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"classification": "NATIVE_DESKTOP_BLOCKED", "blocker": str(exc)}, ensure_ascii=True))
        return 2
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
