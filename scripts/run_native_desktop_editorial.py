"""Native editorial and reviewed-publication continuation; no timer or model API.

In a Desktop chat: advance -> read pending request -> reason -> submit -> advance.
All phases may run in the SAME turn. Binding is explicit and immutable per opportunity.
Publication preparation/status are separate from authority-checked dispatch continuation.
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
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore, WorkItemNotFoundError
from live_contentops.llm_operator_control_v1 import llm_operator_pause_active
from live_contentops.native_desktop_editorial_v1 import DesktopInputRequired, NativeDesktopTurn, DESTINATION
from live_contentops.published_corpus_read_model_v1 import load_canonical_published_memory_read_only
from live_contentops.native_desktop_workspace_v1 import resolve_workspace_path

BINDING_SCHEMA = "contentops.native_desktop_operation_binding.v1"
PRODUCTION_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
DEFAULT_PROFILE = Path(__file__).resolve().parents[1] / "config/native_desktop_operator_profile_v1.json"


def resolve_owner_operation(profile, *, operation_id, request=None, now=None, report_only=False, source_review_ids=()):
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
        # A newer feed applies only to new opportunities. Resumes retain their
        # original feed and frozen packets; the profile cannot redirect storage.
        for key in ("store_path", "published_memory_store", "published_memory_output_root"):
            if resolve_workspace_path(profile[key], manifest_path=profile.get("workspace_relocation_manifest")) != resolve_workspace_path(binding[key], manifest_path=profile.get("workspace_relocation_manifest")):
                raise ValueError("OWNER_PROFILE_BINDING_CHANGED:" + key)
    else:
        if not isinstance(request, str) or not 20 <= len(request.strip()) <= 6000:
            raise ValueError("NORMAL_LANGUAGE_EDITORIAL_REQUEST_REQUIRED")
        binding = {k: profile[k] for k in ("store_path", "feed_pointer_path", "published_memory_store", "published_memory_output_root")}
        binding.update(schema_version=BINDING_SCHEMA, run_id=operation_id, output_dir=str(root),
            owner_manual_validation=True, editorial_request=request,
            cutoff_utc=(now or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z"))
        for key in ("research_editions_root", "source_review_ids"):
            if profile.get(key):
                binding[key] = profile[key]
        if report_only:
            binding["rolling_input_path"] = str(DEFAULT_PROFILE.with_name("native_desktop_report_only_input_v1.json"))
        elif profile.get("rolling_input_path"):
            binding["rolling_input_path"] = profile["rolling_input_path"]
        if source_review_ids:
            binding["source_review_ids"] = list(source_review_ids)
        validate_binding(binding)
        root.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_bytes(binding))
    return path, binding


def validate_binding(binding, *, read_or_prepare=False):
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
    elif not read_or_prepare and llm_operator_pause_active():
        raise ValueError("LLM_OPERATOR_PAUSED")
    return binding


def continue_owner_story(profile, *, source_review_id, operation_id=None, request=None):
    """Route an exact source review through the existing owner, without repeat roles."""
    from live_contentops.contentops_editorial_desk_v1 import source_review_projection
    store = ContentOpsDurableStore(profile["store_path"], auto_migrate=False)
    rows = store.list_outbox_messages()
    reviews = source_review_projection(rows)
    review = next((r for r in reviews if r["review_id"] == source_review_id), None)
    if not review:
        raise ValueError("EXACT_STORY_SOURCE_REVIEW_REQUIRED")
    latest = [r for r in reviews if r["article_identity"] == review["article_identity"]][-1]
    if latest["review_id"] != source_review_id:
        raise ValueError("SOURCE_REVIEW_SUPERSEDED_REFRESH_STORY")
    if not review["writer_required"]:
        return {"classification": "NATIVE_STORY_REUSED_NO_MODEL" if review["decision"] == "USE_UNCHANGED"
                else "NATIVE_STORY_SOURCE_GAP_NO_MODEL", "decision": review["decision"],
            "article_identity": review["article_identity"], "source_review_id": source_review_id,
            "reader_change_summary": review["reader_change_summary"], "model_invocations": 0,
            "source_requests": 0, "public_write_performed": False,
            "next_operation": "Retain the dated article; resolve only the named next source observation."}
    # Reuse an already accepted child before allocating any operation. A second
    # label cannot duplicate a source-bound completed follow-up.
    for row in rows:
        if row["destination"] != "internal:cc-report-simple-result":
            continue
        value = json.loads(row["payload"])
        if (value.get("qualified_article_count") and (value.get("article") or {}).get("source_review_id") == source_review_id):
            child = value["simple_result"]["run_id"]
            if operation_id and operation_id != child:
                raise ValueError("FOLLOWUP_ALREADY_ACCEPTED_USE_EXISTING_OPERATION:" + child)
            _, binding = resolve_owner_operation(profile, operation_id=child)
            return operation(binding)
    operation_id = operation_id or "followup-" + sha256_of(source_review_id)[:24]
    text = request or ("Continue this exact maintained story from its source-bound review. "
        "Select only the bound prior story and admitted changed evidence, or abstain. "
        "Preserve the prior article's update chain, source clocks, public-only authority and history. "
        "Explain new facts separately from changed interpretation, uncertainty and the next observation. "
        "Canonical article, SEO and all eight packages retain the existing house voice. " + review["reader_change_summary"])
    # Omitted request on resume keeps the original owner wording, including a
    # custom request. A pending binding is the authority for its frozen input.
    existing = Path(profile["editorial_output_root"]) / operation_id / "binding.json"
    revision = review["decision"] == "EDITORIAL_REVISION"
    _, binding = resolve_owner_operation(profile, operation_id=operation_id, request=request if existing.is_file() else text,
        source_review_ids=[source_review_id],
        now=datetime.fromisoformat(review["cutoff_utc"].replace("Z", "+00:00")) if revision else None)
    if binding.get("source_review_ids") != [source_review_id]:
        raise ValueError("EXACT_FOLLOWUP_OPERATION_SOURCE_BINDING_REQUIRED")
    if revision:
        original = store.get_outbox_message("native-current-input-" + sha256_of(review["run_id"]))
        if not original:
            raise ValueError("EDITORIAL_REVISION_REQUIRES_ORIGINAL_FROZEN_INPUT")
        frozen = {**json.loads(original["payload"]), "run_id": operation_id,
                  "source_review_ids": [source_review_id], "source_requests_before_writer_freeze": 0,
                  "editorial_revision_of": review["article_identity"], "new_factual_evidence": False}
        work = "cc-opportunity-" + sha256_of(operation_id)
        try:
            work_title = store.get_work_item(work)["title"]
        except WorkItemNotFoundError:
            work_title = "Main-enriched newsroom opportunity"
        store.create_work_item(story_id=work, work_item_id=work, title=work_title,
                               target_surface="CONTENTOPS_EDITORIAL_ONLY")
        store.register_outbox_message(message_id="native-current-input-" + sha256_of(operation_id), work_item_id=work,
            destination="internal:native-current-input", payload=canonical_bytes(frozen).decode(), status="EDITORIAL_INTERNAL")
    return operation(binding)


def operation(binding, *, command="advance", response=None, stage=None, rollout=None,
              native_invocation_id=None, request_hash=None):
    validate_binding(binding, read_or_prepare=command in {"publication-prepare", "publication-status"})
    store = ContentOpsDurableStore(resolve_workspace_path(binding["store_path"]), auto_migrate=command != "publication-status")
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    key = "native-operation-binding-" + sha256_of(binding["run_id"])
    previous = store.get_outbox_message(key)
    if previous and json.loads(previous["payload"]) != binding:
        raise ValueError("NATIVE_OPERATION_BINDING_CHANGED")
    if command == "publication-status":
        from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
        if not previous:
            raise ValueError("EXACT_REGISTERED_OPERATION_BINDING_REQUIRED")
        return NativeReviewedPublication(store, binding, native_invocation_id=None).projection()
    try:
        previous_work = store.get_work_item(work)
    except WorkItemNotFoundError:
        previous_work = None
    store.create_work_item(story_id=work, title=previous_work["title"] if previous_work else "Main-enriched newsroom opportunity",
                           target_surface="CONTENTOPS_EDITORIAL_ONLY", work_item_id=work)
    if not previous:
        store.register_outbox_message(message_id=key, work_item_id=work, destination=DESTINATION,
            payload=canonical_bytes(binding).decode(), status="EDITORIAL_INTERNAL")
    if command.startswith("publication-"):
        from live_contentops.native_desktop_publication_v1 import prepare_native_publication, NativeReviewedPublication
        if command == "publication-prepare":
            return prepare_native_publication(store, binding)
        continuation = NativeReviewedPublication(store, binding, native_invocation_id=native_invocation_id, rollout=rollout)
        if command == "publication-status":
            return continuation.projection()
        if not native_invocation_id:
            raise ValueError("NATIVE_NEO_ACTIVE_INVOCATION_REQUIRED")
        if command == "publication-resume":
            return continuation.resume()
        if not request_hash:
            raise ValueError("EXACT_NATIVE_NEO_REQUEST_REQUIRED")
        return continuation.tool("begin" if command == "publication-tool-begin" else "submit",
                                 request_hash=request_hash, response=response)
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
    if command == "media-plan":
        from live_contentops.native_desktop_editorial_v1 import bind_editorial_media_plan
        if response is None:
            frozen_plan = turn.frozen_request("media-plan")
            governed = (frozen_plan["governed_input"] if frozen_plan else
                json.loads((resolve_workspace_path(binding["output_dir"]) / "editorial_media_plan_required.json").read_bytes()))
            try:
                output, receipt = turn(logical_invocation_id=binding["run_id"] + ":media-plan",
                    prompt=(frozen_plan["prompt"] if frozen_plan else
                            "Return JSON {story_plan: {thesis, photo_plan, chart_plan}}. Prepare exact comparable "
                            "primary-data series and useful visual proposals; MAX decides the count, chart forms "
                            "and placement. Substantial analysis needs 2-5 distinct useful charts; genuine narrow "
                            "news/policy may justify zero internally. Plan relevant authentic "
                            "photo discovery with subject/archive caption and lawful exact license/source evidence, "
                            "using the exact source_pack. Preserve metric/unit/currency/period, "
                            "actual/estimate/forecast and missingness. No prose, new numbers, forecasts, copied charts or public action. "
                            "Code/tools retrieve exact originals and compute/validate/render admitted values. "
                            "This Light proposal is followed by actual same-context MAX visual editing and writing."),
                    governed_input=governed, validator=lambda raw: (True, None, json.loads(raw), None))
                if not turn.visual_response():
                    turn.request_visual_decision(source_packet=governed, preparation={
                        "native_plan_run_id": binding["run_id"], "native_plan_stage": "media-plan",
                        "native_plan_request_sha256": turn.frozen_request("media-plan")["request_sha256"],
                        "story_plan": output["story_plan"]})
            except DesktopInputRequired as pending:
                return {"classification": "NATIVE_DESKTOP_INPUT_REQUIRED", "stage": pending.request["stage"],
                        "request_path": pending.request["request_path"], "request_sha256": pending.request["request_sha256"],
                        "public_write_performed": False}
            return {"classification": "NATIVE_VISUAL_PLAN_RETURNED_ASSETS_REQUIRED", "output": output,
                    "request_sha256": receipt["request_sha256"], "public_write_performed": False}
        return bind_editorial_media_plan(store, run_id=binding["run_id"], output_dir=binding["output_dir"], **response)
    if command == "recover-sources":
        if response.get("expected_selection_request_sha256"):
            # A one-shot manual recovery appends verified captures; it never rewrites
            # selection, the frozen input, a started writer, or the production budget.
            from live_contentops.native_desktop_editorial_v1 import admit_pre_writer_source_recovery
            return admit_pre_writer_source_recovery(turn, binding, response)
        pending = turn.frozen_request("write")
        if (not pending or pending["request_sha256"] != response.get("expected_request_sha256")
                or turn._get("write", "response") or (resolve_workspace_path(binding["output_dir"]) / "qualified_article_record_v1.json").exists()):
            raise ValueError("EXACT_UNANSWERED_WRITER_REQUEST_REQUIRED")
        from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
        pointer = json.loads(Path(binding["feed_pointer_path"]).read_bytes())
        if binding.get("research_editions_root"):
            pointer["research_editions_root"] = binding["research_editions_root"]
        pointer["source_review_ids"] = binding.get("source_review_ids", [])
        research = RetainedSourceResearch(pointer["research_root"], editions_root=pointer.get("research_editions_root"))
        ids = response.get("supporting_headline_ids", [])
        if not 1 <= len(ids) <= 3 or any(h not in research.records for h in ids):
            raise ValueError("EXACT_ADMITTED_RETAINED_SOURCE_IDS_REQUIRED")
        recovery = {"request_sha256": pending["request_sha256"], "supporting_headline_ids": ids,
            "research_revision": research.revision, "public_write_performed": False}
        archive = resolve_workspace_path(binding["output_dir"]) / "source-recovery-history" / pending["request_sha256"]
        archive.mkdir(parents=True, exist_ok=True)
        for name in ("desktop_request_write.json", "simple_gemini_evidence_v1.json", "simple_gemini_editorial_edge_v1.json", "simple_epistemic_state_v1.json"):
            path = resolve_workspace_path(binding["output_dir"]) / name
            if path.exists():
                path.replace(archive / name)
        store.register_outbox_message(message_id="native-source-recovery-" + sha256_of(recovery),
            work_item_id=work, destination="internal:native-desktop-source-recovery",
            payload=canonical_bytes(recovery).decode(), status="EDITORIAL_INTERNAL")
        return {"classification": "RETAINED_SOURCE_RECOVERY_PREPARED", "retained_selection": True,
            "next_operation": "advance same binding", "public_write_performed": False}
    completed = store.get_outbox_message("cc-editorial-final-" + sha256_of(binding["run_id"]))
    final = json.loads(completed["payload"]) if completed else {}
    if final.get("qualified_article_count") and final.get("model_execution_state") == "NATIVE_DESKTOP_REQUEST_RETURN":
        return {"classification": "COMPLETED_NATIVE_ARTICLE_REOPENED", "article_identity": final["article_identity"],
                "qualified_article_count": 1, "new_model_invocations": 0, "new_source_requests": 0,
                "editorial_execution": turn.telemetry(), "publication_handoff_state": "EXISTING_REVIEW_NO_DISPATCH",
                "public_write_performed": False}
    # Retain failed deterministic attempts while resuming the same frozen selection.
    # Source/model outputs are never replaced. A failed compiler receipt can be
    # archived even if compilation reached the qualified file before its final receipt.
    root = resolve_workspace_path(binding["output_dir"])
    receipt_path = root / "simple_gemini_newsroom_receipt_v1.json"
    if receipt_path.is_file():
        failed = json.loads(receipt_path.read_bytes())
        source_blocked = (not (root / "qualified_article_record_v1.json").exists()
            and failed.get("exact_next_blocker") == "ALL_ADMITTED_CANDIDATES_SOURCE_RETRIEVAL_BLOCKED"
            and turn._get("write", "response") is None)
        compiler_blocked = (failed.get("exact_next_blocker") == "NATIVE_DERIVATIVE_COMPILATION_BLOCKED"
            and turn._get("write", "response") is not None)
        if (failed.get("qualified_article_count") == 0
                and (source_blocked or compiler_blocked)):
            history = root / "blocked-attempts" / sha256_of(failed)
            history.mkdir(parents=True, exist_ok=True)
            if (history / "simple_gemini_newsroom_receipt_v1.json").exists():
                history = history / ("resume-" + uuid4().hex)
                history.mkdir()
            for name in (("simple_gemini_newsroom_receipt_v1.json",) if compiler_blocked else
                    ("simple_gemini_evidence_v1.json", "simple_gemini_newsroom_receipt_v1.json")):
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
        from live_contentops.native_newsroom_learning_v1 import freeze_learning, compact_briefing
        snapshot = freeze_learning(store, source_store=(ContentOpsDurableStore(binding["published_memory_store"], auto_migrate=False)
            if resolve_workspace_path(binding["published_memory_store"]).is_file() else None),
            run_id=binding["run_id"], published_memory=memory)
        if snapshot:
            memory = snapshot["published_memory"]
            turn.audience_learning = compact_briefing(snapshot)
            memory_proof = {**memory_proof, "used_memory_sha256":snapshot["published_memory_sha256"],
                "used_memory_scope":"FROZEN_OPPORTUNITY", "live_read_is_used_memory":False}
        pointer = json.loads(Path(binding["feed_pointer_path"]).read_bytes())
        if binding.get("research_editions_root"):
            pointer["research_editions_root"] = binding["research_editions_root"]
        pointer["source_review_ids"] = binding.get("source_review_ids", [])
        admitted_research = None
        if binding.get("owner_manual_validation"):
            frozen = store.get_outbox_message("native-current-input-" + sha256_of(binding["run_id"]))
            if frozen and (research := json.loads(frozen["payload"]).get("research")):
                from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
                admitted_research = RetainedSourceResearch.from_frozen_snapshot(research)
        feed = MainReportFeed(LatestReportDeliveryTracker(store), pointer, retained_research=admitted_research)
        kwargs = {"output_dir": str(root), "cutoff_utc": binding["cutoff_utc"],
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
        root = resolve_workspace_path(binding["output_dir"])
        root.mkdir(parents=True, exist_ok=True)
        (root / "native_desktop_result.json").write_bytes(canonical_bytes(result))
        return {k: result.get(k) for k in ("classification", "qualified_article_count", "derivative_intent_count",
            "exact_next_blocker", "article_path", "native_derivative_preview_path", "publication_handoff_state", "editorial_execution")}
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("newsroom", "follow-up", "editorial-revision", "refresh", "desk", "news-export", "news-read", "advance", "submit", "status", "scheduled", "review", "handoff", "media", "media-plan", "recover-sources", "relocate-workspace", "edition",
        "publication-prepare", "publication-status", "publication-resume", "publication-tool-begin", "publication-tool-submit",
        "audience-status", "audience-observe", "audience-tool-begin", "audience-tool-submit", "audience-evaluate", "audience-feedback", "audience-follow-up"))
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--operation-id")
    parser.add_argument("--article-id", help="Exact retained News article identity; never a path")
    parser.add_argument("--asset-id", help="Exact asset belonging to that retained News article")
    parser.add_argument("--request", help="Owner's ordinary-language editorial question; metadata only")
    parser.add_argument("--request-file", type=Path, help="UTF-8 ordinary-language request")
    parser.add_argument("--report-only", action="store_true", help="Explicit Main/research trigger: no new X intake or fabricated filter work")
    parser.add_argument("--binding", type=Path)
    parser.add_argument("--rollout", type=Path)
    parser.add_argument("--automation-id")
    parser.add_argument("--continue-after", help="Exact completed scheduled run before deliberately requesting its next bounded slot")
    parser.add_argument("--native-invocation-id", help="Actual active Desktop conversation/turn identity")
    parser.add_argument("--request-sha256", help="Exact persisted native Neo request")
    parser.add_argument("--observation-id", help="Existing due canonical performance observation identity")
    parser.add_argument("--evaluation-id", help="Stable bounded learning evaluation identity")
    parser.add_argument("--response", type=Path)
    parser.add_argument("--stage", help="select/write/revise or exact pending filter-<batch sha256>")
    parser.add_argument("--source-review-id", action="append", default=[])
    parser.add_argument("--workspace-root", type=Path, help="Explicit stable destination for authorized manual-workspace relocation")
    args = parser.parse_args(argv)
    if args.command in {"news-export", "news-read"}:
        # The shared operator CLI exposes many paths for other owner operations.
        # None is accepted by this read seam, including its trusted profile override.
        allowed = {"command", "article_id", "asset_id"}
        defaults = parser.parse_args([args.command])
        if any(getattr(args, key) != getattr(defaults, key) for key in vars(args) if key not in allowed):
            parser.error("News uses its fixed configured edition; path/profile/operation overrides are unsupported")
        from live_contentops.retained_news_read_v1 import export_selected_news, local_owner_read, ARTIFACT_PATH
        if args.command == "news-export":
            if args.article_id or args.asset_id:
                parser.error("news-export uses the configured selected edition")
            result = export_selected_news()
            renderer = Path(__file__).resolve().parents[1] / "ui/contentops_v5/scripts/render-report-workspace.mjs"
            subprocess.run(["node", str(renderer), str(ARTIFACT_PATH), str(ARTIFACT_PATH.parent / "reader.html"),
                            "--retained-news"], check=True)
        else:
            if not args.article_id:
                parser.error("news-read requires --article-id")
            result = local_owner_read(args.article_id, asset_id=args.asset_id)
            if isinstance(result.get("body"), bytes):
                import base64
                result["body"] = {"content_base64": base64.b64encode(result["body"]).decode("ascii")}
        print(json.dumps(result, ensure_ascii=True))
        return 0 if result.get("status", 200) == 200 else 2
    if args.command == "editorial-revision":
        if not args.response or not args.operation_id:
            parser.error("editorial-revision requires exact prior article/reason in --response and stable --operation-id")
        from live_contentops.contentops_editorial_desk_v1 import record_story_editorial_revision
        profile = json.loads(args.profile.read_bytes())
        prior = json.loads(args.response.read_bytes())
        review = record_story_editorial_revision(ContentOpsDurableStore(profile["store_path"], auto_migrate=False),
            **prior, review_operation_id=args.operation_id)
        result = continue_owner_story(profile, source_review_id=review["review_id"], operation_id=args.operation_id,
            request=("Revise this exact retained article under CONTENTOPS_V1_EDITORIAL_MEDIA_AND_DATA_RELEASE_STANDARD_V1. "
                     "The financial facts and source dates are unchanged; this is an editorial/media revision, not fresh news. "
                     "Preserve prior identity/history, attribution, report-only uncertainty and the existing update chain. " + prior["reason"]))
        print(json.dumps(result, ensure_ascii=True))
        return 0
    if args.command == "follow-up":
        if len(args.source_review_id) != 1:
            parser.error("follow-up requires one exact --source-review-id")
        profile = json.loads(args.profile.read_bytes())
        result = continue_owner_story(profile, source_review_id=args.source_review_id[0],
            operation_id=args.operation_id, request=args.request_file.read_text(encoding="utf-8") if args.request_file else args.request)
        print(json.dumps(result, ensure_ascii=True))
        return 0
    if args.command.startswith("audience-"):
        from live_contentops.native_newsroom_learning_v1 import learning_context, NativeAudienceObservation, evaluate_native_learning, feedback_judgment
        profile = json.loads(args.profile.read_bytes())
        store = ContentOpsDurableStore(profile["published_memory_store"], auto_migrate=False)
        try:
            if args.command == "audience-follow-up":
                from live_contentops.native_newsroom_learning_v1 import retain_selection_follow_up
                if not args.operation_id or not args.response:
                    raise ValueError("EXACT_OPERATION_AND_NATIVE_FOLLOW_UP_RETURN_REQUIRED")
                result = retain_selection_follow_up(ContentOpsDurableStore(profile["store_path"], auto_migrate=False),
                    run_id=args.operation_id, response=json.loads(args.response.read_bytes()))
            elif args.command == "audience-status":
                result = {**learning_context(store), "due_observations": [o for o in store.list_performance_observations()
                    if o["collection_status"] == "SCHEDULED" and o["scheduled_for_utc"] <= datetime.now(timezone.utc).isoformat()],
                    "next_operation":"audience-observe --observation-id <one-exact-due-id> --native-invocation-id <actual-turn-id>"}
            elif args.command == "audience-feedback":
                result=feedback_judgment(store,observation_id=args.observation_id,
                    output_dir=Path(profile["editorial_output_root"])/"audience-feedback"/str(args.observation_id),
                    response=json.loads(args.response.read_bytes()) if args.response else None)
            elif args.command == "audience-evaluate":
                if not args.evaluation_id:
                    raise ValueError("STABLE_NATIVE_EVALUATION_ID_REQUIRED")
                result = evaluate_native_learning(store, evaluation_id=args.evaluation_id)
            else:
                if not args.observation_id or not args.native_invocation_id:
                    raise ValueError("EXACT_OBSERVATION_AND_NATIVE_INVOCATION_REQUIRED")
                observer = NativeAudienceObservation(store, output_dir=Path(profile["editorial_output_root"])/"audience-observations",
                    invocation_id=args.native_invocation_id)
                result = observer.advance(args.observation_id) if args.command == "audience-observe" else observer.tool(
                    "begin" if args.command == "audience-tool-begin" else "submit", observation_id=args.observation_id,
                    request_hash=args.request_sha256, response=json.loads(args.response.read_bytes()) if args.response else None)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            print(json.dumps({"classification":"NATIVE_AUDIENCE_BLOCKED","blocker":str(exc)}))
            return 2
        print(json.dumps(result, ensure_ascii=True))
        return 0
    if args.command == "edition":
        from live_contentops.contentops_editorial_desk_v1 import record_owner_edition
        if not args.response:
            parser.error("edition requires the owner's bounded edition grouping")
        profile = json.loads(args.profile.read_bytes())
        print(json.dumps(record_owner_edition(ContentOpsDurableStore(profile["store_path"]), **json.loads(args.response.read_bytes()))))
        return 0
    if args.command == "relocate-workspace":
        from live_contentops.native_desktop_workspace_v1 import relocate_owner_workspace
        if not args.workspace_root:
            parser.error("relocate-workspace requires --workspace-root")
        value = relocate_owner_workspace(args.profile, args.workspace_root)
        print(json.dumps({"classification": "MANUAL_WORKSPACE_RELOCATED", "operating_store": value["one_operating_store"],
            "manifest_sha256": value["manifest_sha256"], "historical_artifact_count": len(value["artifact_bytes"]), "production_migration": False}))
        return 0
    if args.command == "refresh":
        from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
        from live_contentops.contentops_editorial_desk_v1 import record_story_source_review
        if not args.response:
            parser.error("refresh requires exact public source comparison inputs")
        profile = json.loads(args.profile.read_bytes())
        pointer = json.loads(Path(profile["feed_pointer_path"]).read_bytes())
        research = RetainedSourceResearch(pointer["research_root"], editions_root=profile.get("research_editions_root"))
        store = ContentOpsDurableStore(profile["store_path"])
        result = record_story_source_review(store, research=research, **json.loads(args.response.read_bytes()))
        print(json.dumps(result, ensure_ascii=True))
        return 0
    if args.command == "desk":
        from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection
        profile = json.loads(args.profile.read_bytes())
        # Read-only projection; no migrations, background owner or production binding.
        import sqlite3
        with sqlite3.connect(Path(profile["store_path"]).resolve().as_uri() + "?mode=ro", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute("SELECT * FROM outbox_messages ORDER BY rowid")]
            reviews = [dict(r) for r in conn.execute("SELECT * FROM review_records ORDER BY rowid")]
            dispatches = [dict(r) for r in conn.execute("SELECT * FROM platform_dispatches ORDER BY rowid")]
            reconciliations = [dict(r) for r in conn.execute("SELECT * FROM reconciliations ORDER BY rowid")]
            readiness = [dict(r) for r in conn.execute("SELECT * FROM destination_readiness ORDER BY rowid")]
        projection = report_workspace_projection(rows, review_records=reviews, dispatches=dispatches,
            reconciliations=reconciliations, readiness=readiness)
        from live_contentops.native_newsroom_learning_v1 import learning_context
        projection["audience_learning"]["current"] = learning_context(
            ContentOpsDurableStore(profile["published_memory_store"], auto_migrate=False))
        root = Path(profile["editorial_output_root"]) / "desk"
        root.mkdir(parents=True, exist_ok=True)
        (root / "workspace.json").write_bytes(canonical_bytes(projection))
        renderer = Path(__file__).resolve().parents[1] / "ui/contentops_v5/scripts/render-report-workspace.mjs"
        subprocess.run(["node", str(renderer), str(root / "workspace.json"), str(root / "index.html"), "--owner-review"], check=True)
        print(json.dumps({"review_entry": str(root / "index.html"), "mode": "OFFLINE_READ_ONLY_OWNER_REVIEW",
                          "reopen": "Open the same HTML file in a browser; no preview server is required.",
                          "publication_authority": False}, ensure_ascii=True))
        return 0
    if args.command == "newsroom":
        try:
            request = args.request_file.read_text(encoding="utf-8") if args.request_file else args.request
            path, binding = resolve_owner_operation(json.loads(args.profile.read_bytes()),
                operation_id=args.operation_id, request=request, report_only=args.report_only, source_review_ids=args.source_review_id)
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
        from live_contentops.durable_operational_store_v1 import LeaseConflictError
        try:
            result = scheduled_binding(json.loads(args.rollout.read_bytes()), args.automation_id,
                                       continue_after=args.continue_after)
        except (ValueError, OSError, KeyError, TypeError, LeaseConflictError) as exc:
            print(json.dumps({"classification": "NATIVE_DESKTOP_BLOCKED", "blocker": str(exc)}))
            return 2
        print(json.dumps(result))
        return 0
    if not args.binding:
        parser.error("--binding is required")
    try:
        binding = json.loads(args.binding.read_bytes())
        result = operation(binding, command=args.command, stage=args.stage,
                           response=json.loads(args.response.read_bytes()) if args.response else None,
                           rollout=json.loads(args.rollout.read_bytes()) if args.rollout else None,
                           native_invocation_id=args.native_invocation_id, request_hash=args.request_sha256)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({"classification": "NATIVE_DESKTOP_BLOCKED", "blocker": str(exc)}, ensure_ascii=True))
        return 2
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
