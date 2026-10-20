"""One native Desktop opportunity; no timer, model API, activation or publishing.

In a Desktop chat: advance -> read pending request -> reason -> submit -> advance.
All phases may run in the SAME turn. Binding is explicit and immutable per opportunity.
"""
from __future__ import annotations

import argparse
import json
import sys
import subprocess
from datetime import datetime, timezone
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
DEFAULT_PROFILE = Path(__file__).resolve().parents[1] / "config/native_desktop_operator_profile_v1.json"


def resolve_owner_operation(profile, *, operation_id, request=None, now=None, report_only=False):
    """Resolve one explicit owner operation; frozen binding survives quota/restarts.

    This is an entry to the existing outbox/opportunity, not a queue or scheduler.
    The Desktop agent handles native roles and returns, never the human operator.
    """
    if profile.get("schema_version") != "contentops.native_desktop_operator_profile.v1":
        raise ValueError("NATIVE_OPERATOR_PROFILE_INVALID")
    if not operation_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in operation_id):
        raise ValueError("EXPLICIT_OPERATION_ID_REQUIRED")
    root = Path(profile["editorial_output_root"]).resolve() / operation_id
    path = root / "binding.json"
    if path.is_file():
        binding = validate_binding(json.loads(path.read_bytes()))
        if request is not None and request != binding.get("editorial_request"):
            raise ValueError("OWNER_REQUEST_CHANGED_USE_NEW_OPERATION")
        # A profile edit cannot redirect an existing claimed opportunity.
        for key in ("store_path", "feed_pointer_path", "published_memory_store", "published_memory_output_root"):
            if Path(profile[key]).resolve() != Path(binding[key]).resolve():
                raise ValueError("OWNER_PROFILE_BINDING_CHANGED:" + key)
    else:
        if not isinstance(request, str) or not 20 <= len(request.strip()) <= 6000:
            raise ValueError("NORMAL_LANGUAGE_EDITORIAL_REQUEST_REQUIRED")
        binding = {k: profile[k] for k in ("store_path", "feed_pointer_path", "published_memory_store", "published_memory_output_root")}
        binding.update(schema_version=BINDING_SCHEMA, run_id=operation_id, output_dir=str(root),
            owner_manual_validation=True, editorial_request=request,
            cutoff_utc=(now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z"))
        if report_only:
            binding["rolling_input_path"] = str(DEFAULT_PROFILE.with_name("native_desktop_report_only_input_v1.json"))
        elif profile.get("rolling_input_path"):
            binding["rolling_input_path"] = profile["rolling_input_path"]
        validate_binding(binding)
        root.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_bytes(binding))
    return path, binding


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
    if command == "media":
        from live_contentops.native_desktop_editorial_v1 import bind_editorial_media
        return bind_editorial_media(store, run_id=binding["run_id"], **response)
    if command == "recover-sources":
        pending = turn.frozen_request("write")
        if (not pending or pending["request_sha256"] != response.get("expected_request_sha256")
                or turn._get("write", "response") or (Path(binding["output_dir"]) / "qualified_article_record_v1.json").exists()):
            raise ValueError("EXACT_UNANSWERED_WRITER_REQUEST_REQUIRED")
        from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
        pointer = json.loads(Path(binding["feed_pointer_path"]).read_bytes())
        research = RetainedSourceResearch(pointer["research_root"])
        ids = response.get("supporting_headline_ids", [])
        if not 1 <= len(ids) <= 3 or any(h not in research.records for h in ids):
            raise ValueError("EXACT_ADMITTED_RETAINED_SOURCE_IDS_REQUIRED")
        recovery = {"request_sha256": pending["request_sha256"], "supporting_headline_ids": ids,
            "research_revision": research.revision, "public_write_performed": False}
        archive = Path(binding["output_dir"]) / "source-recovery-history" / pending["request_sha256"]
        archive.mkdir(parents=True, exist_ok=True)
        for name in ("desktop_request_write.json", "simple_gemini_evidence_v1.json", "simple_gemini_editorial_edge_v1.json", "simple_epistemic_state_v1.json"):
            path = Path(binding["output_dir"]) / name
            if path.exists():
                path.replace(archive / name)
        store.register_outbox_message(message_id="native-source-recovery-" + sha256_of(recovery),
            work_item_id=work, destination="internal:native-desktop-source-recovery",
            payload=canonical_bytes(recovery).decode(), status="EDITORIAL_INTERNAL")
        return {"classification": "RETAINED_SOURCE_RECOVERY_PREPARED", "retained_selection": True,
            "next_operation": "advance same binding", "public_write_performed": False}
    # Retain failed deterministic attempts while resuming the same frozen selection.
    # Qualified output and started/returned writers are never replaced by this path.
    root = Path(binding["output_dir"])
    receipt_path = root / "simple_gemini_newsroom_receipt_v1.json"
    if receipt_path.is_file() and not (root / "qualified_article_record_v1.json").exists():
        failed = json.loads(receipt_path.read_bytes())
        if (failed.get("qualified_article_count") == 0
                and failed.get("exact_next_blocker") == "ALL_ADMITTED_CANDIDATES_SOURCE_RETRIEVAL_BLOCKED"
                and turn._get("write", "response") is None):
            history = root / "blocked-attempts" / sha256_of(failed)
            history.mkdir(parents=True, exist_ok=True)
            for name in ("simple_gemini_evidence_v1.json", "simple_gemini_newsroom_receipt_v1.json"):
                source = root / name
                if source.is_file():
                    target = history / name
                    if target.exists() and target.read_bytes() != source.read_bytes():
                        raise ValueError("BLOCKED_ATTEMPT_HISTORY_CONFLICT")
                    if not target.exists():
                        source.replace(target)
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
        if binding.get("editorial_request"):
            kwargs["editorial_request"] = binding["editorial_request"]
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
    parser.add_argument("command", choices=("newsroom", "desk", "advance", "submit", "status", "scheduled", "review", "handoff", "media", "recover-sources"))
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--operation-id")
    parser.add_argument("--request", help="Owner's ordinary-language editorial question; metadata only")
    parser.add_argument("--request-file", type=Path, help="UTF-8 ordinary-language request")
    parser.add_argument("--report-only", action="store_true", help="Explicit Main/research trigger: no new X intake or fabricated filter work")
    parser.add_argument("--binding", type=Path)
    parser.add_argument("--rollout", type=Path)
    parser.add_argument("--automation-id")
    parser.add_argument("--response", type=Path)
    parser.add_argument("--stage", help="select/write/revise or exact pending filter-<batch sha256>")
    args = parser.parse_args(argv)
    if args.command == "desk":
        from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
        profile = json.loads(args.profile.read_bytes())
        # Read-only projection; no migrations, background owner or production binding.
        import sqlite3
        with sqlite3.connect(Path(profile["store_path"]).resolve().as_uri() + "?mode=ro", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute("SELECT * FROM outbox_messages ORDER BY rowid")]
            reviews = [dict(r) for r in conn.execute("SELECT * FROM review_records ORDER BY rowid")]
        projection = report_workspace_projection(rows, review_records=reviews)
        root = Path(profile["editorial_output_root"]) / "desk"
        root.mkdir(parents=True, exist_ok=True)
        (root / "workspace.json").write_bytes(canonical_bytes(projection))
        renderer = Path(__file__).resolve().parents[1] / "ui/contentops_v5/scripts/render-report-workspace.mjs"
        subprocess.run(["node", str(renderer), str(root / "workspace.json"), str(root / "index.html")], check=True)
        return 0
    if args.command == "newsroom":
        try:
            request = args.request_file.read_text(encoding="utf-8") if args.request_file else args.request
            path, binding = resolve_owner_operation(json.loads(args.profile.read_bytes()),
                operation_id=args.operation_id, request=request, report_only=args.report_only)
            result = operation(binding)
            print(json.dumps({**result, "binding_path": str(path),
                "agent_instruction": "Continue assigned native roles, existing source tools, review, previews and prepared handoff in this same opportunity. Jim does not assemble CLI/claim/return JSON. No dispatch."}, ensure_ascii=True))
            return 0
        except (ValueError, OSError, KeyError, TypeError) as exc:
            print(json.dumps({"classification": "NATIVE_DESKTOP_BLOCKED", "blocker": str(exc)}))
            return 2
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
