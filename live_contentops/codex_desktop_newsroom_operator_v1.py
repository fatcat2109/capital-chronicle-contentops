"""Read-only continuity view for one native Codex Desktop V1 editorial opportunity.

This module is deliberately not a scheduler, newsroom, state store, publisher, model bridge, or
CLI.  It reconstructs the latest terminal editorial cutoff from the existing durable store and
cycle artifacts, filters current intake by durable identities, refreshes the read-only Capital
Chronicle estate, and returns a bounded zero-write briefing for a fresh Desktop task.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence
from urllib.parse import urlsplit
from uuid import UUID

from live_contentops.capital_chronicle_data_catalog_v1 import (
    DEFAULT_CC_ROOT,
    discover_cc_data_estate,
    inspect_governed_cc_surfaces,
    query_story_scoped_cc_context,
)
from live_contentops.daily_app_launcher_v1 import (
    CANONICAL_PRODUCTION_OUTPUT_ROOT,
    CANONICAL_PRODUCTION_STORE_PATH,
)
from live_contentops.destination_transport_registry_v1 import (
    V1_QUALITY_PROBATION_POLICY_ID,
)
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_glob
from live_contentops.newsroom_assignment_scheduler_v1 import (
    PREPARED_CANDIDATE_LIMIT,
    build_prepared_rolling_x_candidate_state,
    load_rolling_x_headline_sidecars,
    validate_prepared_rolling_x_candidate_state,
)

SCHEMA_VERSION = "contentops.codex_desktop_newsroom_operator_continuity.v1"
REHEARSAL_SCHEMA_VERSION = "contentops.codex_desktop_newsroom_operator_rehearsal.v1"
MATERIAL_RELATIONSHIPS = frozenset(
    {"material_update", "correction", "contradiction", "new_phase"}
)
TERMINAL_EDITORIAL_STATES = frozenset(
    {
        "REJECTED",
        "REVIEW_BLOCKED",
        "DISPATCH_BLOCKED",
        "PARTIAL_SUCCESS",
        "DISPATCH_COMPLETE",
        "COMPLETE",
        "DEAD_LETTER",
        "OPERATOR_RECOVERY_REQUIRED",
        "CLOSED",
    }
)
CANONICAL_SUBSTACK_HOST = "capitalchronicle.substack.com"
QUALITY_PROBATION_POLICY_ID = V1_QUALITY_PROBATION_POLICY_ID
COORDINATOR_MODEL = "gpt-5.6-sol"
COORDINATOR_REASONING_EFFORT = "HIGH"
EDITORIAL_WORKER_MODEL = "gpt-5.6-sol"
CONTENTOPS_CODEX_MAX_REASONING_EFFORT = "HIGH"
EDITORIAL_WORKER_REASONING_EFFORT = CONTENTOPS_CODEX_MAX_REASONING_EFFORT
MAX_EDITORIAL_REVISIONS = 1
FAKE_OR_UNBOUND_QUOTE_REPAIR_INSTRUCTION = (
    "The SAME fresh isolated editorial worker must make the single bounded revision and choose "
    "exactly one safe outcome for each fake_or_unbound_quote_presentation blocker: (A) remove "
    "quotation-mark presentation when the phrase is merely a publication or document title; or "
    "(B) when it is genuinely quoted source text, return an exact quote_source_record whose "
    "quote_text matches the presented quotation and whose source_ids bind only to accepted "
    "evidence source IDs. Do not fabricate a quote record, invent a source binding, or alter the "
    "governed input hash."
)
AUTOMATION_HOST_OBSERVATION_SCHEMA_VERSION = (
    "contentops.codex_automation_host_observation.v1"
)
HYBRID_EDITORIAL_RUN_IDENTITY_SCHEMA_VERSION = (
    "contentops.hybrid_editorial_run_identity.v1"
)
HYBRID_EDITORIAL_ARBITRATION_SCHEMA_VERSION = (
    "contentops.hybrid_editorial_arbitration.v1"
)
EXACT_V1_AUTOMATION_IDS = (
    "v1-newsroom-london-1700",
    "v1-newsroom-new-york-2100",
    "v1-newsroom-new-york-2300",
    "v1-newsroom-new-york-0100",
)
NO_EDITORIAL_WORKER_PATHS = frozenset(
    {
        "NO_NEW_HEADLINE",
        "DUPLICATE_ONLY",
        "NO_QUALIFIED_CANDIDATE",
        "EVIDENCE_BLOCKED",
        "FULL_DISTRIBUTION_READINESS_BLOCKED",
        "RECOVERY_ONLY",
        "HOUSEKEEPING_ONLY",
        "METRICS_LEARNING_HOUSEKEEPING_ONLY",
    }
)
BOUNDED_EDITORIAL_CONTEXT_KEYS = frozenset(
    {
        "accepted_evidence_packet",
        "exact_source_handles",
        "governed_capital_chronicle_context",
        "active_bounded_learning_policy",
        "material_update_context",
        "rights_cleared_media_candidates",
        "governed_chart_inputs",
        "destination_package_constraints",
        "institutional_edge_editorial_packet",
    }
)
SUBAGENT_COMPLETION_AUTHORITY = (
    "Jim's personal instructions V3, 29 October 2026, and Claude L1 decision A1 "
    "in argon_event_operating_review_20261029/09_CLAUDE_L1_FINAL_SYNTHESIS_AND_DECISION_20261029.md"
)
SUBAGENT_COMPLETION_RULE = (
    "NATIVE ROLE RESULTS: follow docs/automation/CONTENTOPS_BUILDER_SUBAGENT_COMPLETION_HANDOFF_RULE_V1.md. "
    "Native Luna/Light/MAX roles belong to this operation, not separate Builder chats. "
    "Before each spawn/follow-up, append native_subagent_completion_prompt with the actual operation_id, "
    "bounded assignment_id, result_path and expected_return (exact stage/request hash or deliverable). "
    "Scheduled roles use their issued automation_id/window_id/binding_path; no separate engineering goal "
    "or parent UUID is required. A new child's invocation identity is obtained AFTER spawn from its actual "
    "tool result/context, never invented as a spawn prerequisite. Save the exact result before "
    "returning it through the platform's supported native final result. The Builder consumes that return or "
    "saved artifact once by assignment/stage/result identity and continues the SAME operation inside its active "
    "turn, without Jim relaying completion. Never tell a child to message its ancestor; that call is rejected. "
    "Do not pause the parent merely because its own native child owns the next stage. A completed finite task, "
    "HOLD or REPAIR_REQUIRED review is usable; partial batches/turns/quota interruptions are not completion. "
    "Record actual native invocation identity from the assigned agent/context and result, not settings or invented "
    "IDs; historical unobserved identity stays unknown. "
    "Native identity comes only from the supported spawn/context result, never environment variables, "
    "credentials, session files or process diagnostics. If absent in the child context, return the saved "
    "output with that gap so the coordinator can bind its actual spawn observation before submit. "
    "If the active turn cannot continue, retain the exact stage/artifact/platform limit and report the unattended gap. Use the supported "
    "native final return or artifact in this same operation; no polling/sleep, "
    "heartbeat, relay chats, alternate callback, GUI workaround, acknowledgement chain or watcher. "
    "Only after genuinely completing the WHOLE goal may L3 send its one L2 completion notice. "
    "Authority: " + SUBAGENT_COMPLETION_AUTHORITY + ". "
)


def native_subagent_completion_prompt(
    *, operation_id: str, assignment_id: str, result_path: str, expected_return: str,
    parent_thread_id: str | None = None, parent_host_id: str | None = None,
    goal_id: str | None = None, native_invocation_id: str | None = None,
    automation_id: str | None = None, window_id: str | None = None,
    binding_path: str | None = None,
) -> str:
    """Bind an in-operation role result; never send messages or supervise a child."""
    fields = dict(operation_id=operation_id, assignment_id=assignment_id,
        result_path=result_path, expected_return=expected_return)
    optional = dict(parent_thread_id=parent_thread_id, parent_host_id=parent_host_id,
        goal_id=goal_id, native_invocation_id=native_invocation_id,
        automation_id=automation_id, window_id=window_id, binding_path=binding_path)
    fields.update({k: v for k, v in optional.items() if v is not None})
    for name, value in fields.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError("NATIVE_CHILD_COMPLETION_ASSIGNMENT_REQUIRED:" + name)
    if parent_thread_id is not None:
        try:
            UUID(parent_thread_id)
        except ValueError as exc:
            raise ValueError("EXACT_PARENT_BUILDER_THREAD_REQUIRED") from exc
    if automation_id is not None and (not window_id or not binding_path):
        raise ValueError("EXACT_SCHEDULED_NATIVE_BINDING_REQUIRED")
    return (SUBAGENT_COMPLETION_RULE + "\nEXACT CHILD ASSIGNMENT:\n"
        + json.dumps(fields, ensure_ascii=False, sort_keys=True)
        + "\nSave actual results at result_path and return the assignment/operation/stage, exact path/hash, "
          "findings, verification, limits and next action in your native final result. Do not send a chat message. "
          "The Builder reads the actual result and continues the same operation. Preserve incomplete/quota work "
          "and distinguish it from a completed bounded assignment.")


def native_role_call(request, binding, *, binding_path, same_writer_invocation=None):
    """Describe the next real platform call; this function invokes no model."""
    from live_contentops.native_desktop_editorial_v1 import ROLE_ASSIGNMENTS, native_role
    stage = request["stage"]
    role = native_role(stage)
    target = ROLE_ASSIGNMENTS["select" if role == "feedback" else role]
    if (request.get("run_id") != binding["run_id"]
            or request.get("requested_model") != target["model"]
            or request.get("requested_reasoning_effort") != target["reasoning_effort"]):
        raise ValueError("EXACT_NATIVE_ROLE_REQUEST_REQUIRED")
    if (role in {"revise", "final-visual"} or stage == "visual-edit-amend") and not same_writer_invocation:
        raise ValueError("ACTUAL_SAME_MAX_CONTINUATION_ID_REQUIRED")
    result_path = str(Path(binding["output_dir"]) / ("desktop_response_" + stage + ".json"))
    role_input_path = request["request_path"]
    if role == "filter":
        # Relevance needs the complete headline, source and correction context,
        # not repeated capture/permission ledgers. Exact full rows remain frozen
        # under each input hash in the original request and submit contract.
        records = []
        for item in request["governed_input"]["records"]:
            original = item["original_record"]
            fields = {k:v for k,v in original.items() if k in {
                "headline_id","headline_text","source_timestamp_utc","known_at_utc","source_identity",
                "source_account","source_url","source_platform","correction_of","supersedes_headline_id",
                "update_chain_identity","revision_id","revision_at_utc","rights_state","trust_classification"}}
            ext = original.get("external_content") or {}
            fields["external_content"] = {k:v for k,v in ext.items() if k in {
                "headline_text","author_handle","source_platform","url_or_source_ref","tags","official_source_urls"}}
            records.append({"input_sha256":item["input_sha256"],"original_record":fields})
        compact = {"stage":stage,"run_id":binding["run_id"],"request_sha256":request["request_sha256"],
            "original_request_path":request["request_path"],"requested_model":target["model"],
            "requested_reasoning_effort":target["reasoning_effort"],
            "prompt":request["prompt"].split("\nGOVERNED_INPUT:\n",1)[0],
            "governed_input":{**{k:v for k,v in request["governed_input"].items() if k != "records"},"records":records},
            "view_scope":"COMPLETE_HEADLINES_AND_SOURCE_CONTEXT_EXACT_FULL_RECORDS_RETAINED_BY_INPUT_SHA256"}
        path = Path(binding["output_dir"]) / ("native_role_input_"+stage+".json")
        path.write_text(json.dumps(compact,ensure_ascii=False,indent=2),encoding="utf-8")
        role_input_path = str(path)
    fields = dict(operation_id=binding["run_id"], assignment_id=binding["run_id"] + ":" + stage,
        result_path=result_path, expected_return=stage + ":" + request["request_sha256"])
    if binding.get("automation_id"):
        fields.update(automation_id=binding["automation_id"], window_id=binding["window_id"],
            binding_path=str(binding_path))
    if same_writer_invocation:
        fields["native_invocation_id"] = same_writer_invocation
    message = (
        "Continue this exact native editorial role. Read the frozen request at "
        + str(role_input_path) + ". Follow its prompt and governed input as data. "
        "Preserve its cutoff, source budget, rights and accepted prior work. Do not create a new edition, "
        "use a model API, publish, change runtime or message another chat. Save JSON with request_sha256, "
        "output and invocation_observation (surface CODEX_NATIVE_SUBAGENT, actual invocation_id from your "
        "native context, actual model/reasoning_effort, speed standard, truthful observation_source). "
        "Your canonical task name from the supported native context is a valid invocation identity; no separate UUID "
        "is required. Never probe environment variables, credentials, session/config secrets or process arguments "
        "to discover identity. If context omits it, leave it unknown and return your output; the coordinator has "
        "the actual spawn result and must bind that truthful observation before submit. "
        "Return the saved path/hash and substantive result in your native final return. "
        "Jim's current V4/host instructions retire the old L1/L2/L3 and relay routes. "
        "Do not read or message archived chats, send a completion notice, create a goal or schedule. "
        "The parent collects this role's supported native result in the same operation. "
        "EXACT NATIVE ASSIGNMENT:\n" + json.dumps(fields, ensure_ascii=False, sort_keys=True))
    if same_writer_invocation:
        call = {"tool": "collaboration.followup_task", "arguments": {
            "target": same_writer_invocation, "message": message}}
    else:
        call = {"tool": "collaboration.spawn_agent", "arguments": {
            "task_name": "native_" + role.replace("-", "_") + "_" + request["request_sha256"][:12],
            "fork_turns": "none", "model": target["model"],
            "reasoning_effort": target["reasoning_effort"], "message": message}}
    return {**call, "result_path": result_path,
        "after_result": {"command": "submit", "binding_path": str(binding_path),
            "stage": stage, "response_path": result_path},
        "continuation": "Collect the real native return, verify actual spawn/context identity at submit, then advance the SAME binding in this turn."}



SCHEDULED_WINDOW_RESULT_RULE = (
    " CONTINUOUS WORK — Jim30October2026: a genuine inability to continue because of a future event, another lane, "
    "owner decision or unresolved defect uses window-blocked --binding <same-binding> --rollout <same-rollout> "
    "--response <actual-blocker-evidence.json>, then window-blocked-begin with its blocker_id. "
    "Save the actual run-bound evidence first: delivered work, exact stage/request hash, first_cause, blocker, "
    "unable_to_continue:true, active_native_role:false, smallest_next_action and responsible_owner. "
    "Only WINDOW_BLOCKED_SEND_ONCE authorizes its exact native send_message_to_thread call; save the actual result "
    "with window-blocked-record (blocker_id and tool_result). Existing window records dedupe each distinct blocker. "
    "This is BLOCKED, never completion. Quota, turn-end, guard, early/duplicate callbacks and a functioning pending "
    "child send nothing; keep collecting/advancing actual native results. No repeated notice, retry or acknowledgement. "
    " SCHEDULED WINDOW RESULT — Jim approved 29 October 2026: this scheduled chat is a separate task. "
    "Preserve the exact first scheduled CLI result and actual_entry_utc in this task's existing memory and a saved startup-result JSON. "
    "After all admitted candidates/eligible slots are terminal, run window-result --binding <exact-last-binding> "
    "--rollout config/native_desktop_rollout_v1.json --response <JSON containing startup_result, actual source_context "
    "(source_thread_id/source_turn_id when observed) and optional terminal_failure>. "
    "A terminal_failure must name the exact run-bound CLI error artifact_path/operation, substantive why_terminal and continuation_possible:false; "
    "a routine repairable blocker is not terminal. "
    "A candidate HOLD is not window completion while another admitted candidate or slot remains eligible; continue the existing owner first. "
    "The command must save the aggregate terminal result before any notice. If WINDOW_RESULT_SAVED, run window-notice-begin "
    "with the same binding/rollout; only WINDOW_NOTICE_SEND_ONCE authorizes ONE existing send_message_to_thread tool call "
    "with its exact returned arguments, threadId 01a1657e-f5d0-76a1-b52b-ec6c78b6fe35 and hostId local. "
    "Then save the ACTUAL tool result and run window-notice-record --binding <same-binding> --rollout config/native_desktop_rollout_v1.json "
    "--response <actual-tool-result.json>. Record success only when the returned target and tool success are verified. "
    "On transport failure, save the actual failure and stop; no retry loop, acknowledgement, new ledger, scheduler, relay or watcher. "
    "Notice fields: automation/production-day/window/run, actual outcome, distinct canonical items, confirmed/skipped/failed channels, "
    "first blocking cause, exact durable artifact and concrete next action; Jim-facing times use GMT+7. "
    "NOT_YET_EFFECTIVE (including the 29 October Europe brief), stale/duplicate callbacks, partial stages, unfinished native children, "
    "unchanged progress and quota interruptions never send a completion notice. This clause changes reporting only: retain policies, "
    "budgets, roles, calendars, frozen identities and the 02:00-on-30-October guard. This scheduled-window exception supersedes "
    "the blanket whole-goal-only wording ONLY for these seven task chats; engineering Builder completion still requires its whole goal. "
    "Native subagents never message their ancestor. L2 may review material results/repair routine failures; Claude remains Jim-triggered."
)

DESKTOP_TASK_PROMPT = (
    "STARTUP FIRST: read the current V1 execution override in AGENTS.md and check the existing "
    "LLM_OPERATOR_PAUSED boundary, then promptly run python scripts/run_native_desktop_editorial.py "
    "scheduled --automation-id {automation_id} --rollout config/native_desktop_rollout_v1.json. "
    "Obtain the existing binding before lengthy context reads; reuse the already-admitted strategic "
    "read and finish the required current role/source context before semantic work. Do not repeat "
    "whole-project onboarding on each callback. A currently eligible window binds independently of older pending slots; "
    "the scheduled entry otherwise discovers the latest issued binding even after its original due/grace interval; "
    "it never backdates a never-bound window. Bounded five-minute early App delivery retains the nominal cutoff "
    "and freezes input at actual early entry separately; a more premature or expired unbound callback stays missed. "
    "On NATIVE_WINDOW_OPERATION_COMPLETE reuse the accepted result/review/preparation without "
    "refiltering, source requests or model turns. A duplicate callback is not another article. "
    "OUTSIDE_EXACT_NATIVE_WINDOW with no binding means a missed/expired opportunity: record the "
    "actual native start and result in existing automation memory, then stop without a manual "
    "replacement, sleep, monitor, timer or retry loop. Quota before binding is an external capacity "
    "limit; do not claim editorial completion. Routine owner NATIVE_CODEX_DESKTOP; "
    "the coordinator uses gpt-6.1-sol/low (Light), standard speed, within this SAME opportunity. "
    "Follow CONTENTOPS_NATIVE_DESKTOP_EDITORIAL_ROLE_POLICY_V2: native gpt-6-luna/max filters; "
    "gpt-6.1-sol/low selects content and prepares evidence; native gpt-6.1-sol/max writes and repairs. "
    "Use fresh native subagents for the assigned MAX roles; keep the same writer for useful repair and all necessary concrete final-media corrections. "
    "No Gemini/9Router, SDK/App-Server/API fallback, paid speed, permanent fleet or source/rights weakening. "
    "Jim's27October V1 live grant is applied through the current rollout/control owners; publish only reviewed fresh operations under those exact guards. "
    "Run python scripts/run_native_desktop_editorial.py scheduled --automation-id {automation_id} "
    "--rollout config/native_desktop_rollout_v1.json. Respect LLM_OPERATOR_PAUSED before any store write. "
    "The command resolves this existing four-window slot and the frozen operation binding. "
    "When it returns binding_path, run python scripts/run_native_desktop_editorial.py advance "
    "--binding <binding_path> immediately to obtain the next request or final result. "
    "If pending, read its exact desktop_request JSON and obey its requested role/model/effort. "
    "NATIVE_DESKTOP_INPUT_REQUIRED is a continuation boundary, not a terminal result: execute its "
    "next_native_call in this SAME turn, collect the supported native final/artifact, submit and advance "
    "until the whole window is terminal. Reuse the SAME actual MAX via followup for writing/final pixels/repairs. "
    "If next_native_calls lists independent Luna batches, dispatch at most three concurrently, collect every real "
    "return and submit each once before the next advance. Each compact role input retains complete headline text "
    "and exact source/correction context, bound to the unchanged full request and input hashes. "
    "There is no four-batch or elapsed-turn stopping rule. Read filter_progress/remaining_unprocessed and "
    "continue every prepared native batch; accepted earlier batches are reused. Do not end merely to save a partial "
    "checkpoint when the next call is executable. If a genuine unfixable blocker prevents continuation, use the "
    "separate BLOCKED owner, never a fabricated terminal result. "
    "If an exec returns a live session/cell with initially empty output, consume that exact handle's completion "
    "once; never label the command pending after it completed or issue a duplicate advance. A real quota/tool "
    "failure is a software/capacity interruption with its actual error, never an editorial HOLD. "
    "For owner-manual normal-language work, use the same protocol through newsroom --operation-id "
    "<stable-id> --request-file <UTF-8 question> and config/native_desktop_operator_profile_v1.json; "
    "the agent handles CLI/claims/returns. Resume completed outputs with the same binding. "
    "After unchanged bulk X CDP ingestion and exact dedupe, process ALL unprocessed admissible headlines "
    "through bounded resumable MAX-filter batches with exact IDs, input/output hashes, cursor and "
    "seen/kept/rejected/deferred counts and reasons. Never truncate to newest-32 and call all filtered. "
    "Retain headline/correction/update identities; invalidate only affected inputs. "
    "Then Light chooses <=32 downstream candidates using Main public reports, reviewed retained research, "
    "prior-story/missing-dimension context and reconciled memory; it owns angle, mode, audience question "
    "and an evidence plan. Code/tools retrieve, parse, compute and validate permitted data; no DB backfill. "
    "Submit each response with the actual native invocation_id from the returned agent/context and a truthful "
    "observation source; never submit null or invent a UUID from settings. Model/effort may remain null only "
    "when genuinely unobserved. A missing invocation identity is a software/process gap, not a source HOLD. "
    "Then advance using returned binding_path. "
    "Use python scripts/run_native_desktop_editorial.py submit --binding <binding_path> --stage "
    "<exact-returned-stage> --response <authored-response.json>, then advance --binding <binding_path>. "
    "The MAX writer receives the compact source/claim/prior-story packet plus the exact hash-bound "
    "institutional_edge_editorial_packet and current voice/humor/SEO contracts. It owns canonical prose, "
    "SEO and article-bound native passages: defensible thesis, mechanism, countercase, uncertainty and reader utility. "
    "Titles/dek/description/slug/links/supported structured data must express the same evidenced proposition. "
    "Humor is optional; no manufactured certainty, filler or word quota. "
    "Stay in this opportunity through selection, bounded existing evidence retrieval, writing, deterministic "
    "validation and useful repair. Necessary targeted final-media corrections have no arbitrary one-repair cutoff. Never copy a template as model output. "
    "Continue existing bounded deficit slots only when command reports next_slot_eligible and useful work, "
    "by scheduled --automation-id {automation_id} --rollout config/native_desktop_rollout_v1.json "
    "--continue-after <exact-completed-run-id>. This explicit continuation is idempotent and cannot "
    "allocate after the existing due/grace limit. Pending or delayed work always retains its binding; "
    "4/32 is telemetry, never a reason to stop below five. Source limit six shared requests per article; "
    "primary plus <=2 useful fallback candidates. Preserve report/event certainty and Main numeric ownership. "
    "HOLD, SOURCE_BLOCKED, REJECT and NO_STORY are valid typed pre-writer outcomes requiring zero media. "
    "Submit the exact outcome to its pending native stage with the real first cause and retained source budget, "
    "then advance the same binding to the next admitted candidate or terminal edition result. "
    "Do not hide software/process or late-awareness failures inside an editorial HOLD. "
    "Recover existing UNKNOWN writes before fresh work: STOP RETRY -> READ BACK -> RECONCILE. "
    "Inspect actual prose and eight native previews, keep revision-bound review and reuse unchanged media. "
    "Before a new MAX writer freezes, the mandatory media-plan stage retains one relevant lawful documentary photo. "
    "Under DATA_JOURNALISM_V1, Light proposes primary-data comparisons; the same MAX visual editor/final writer "
    "chooses the argument, chart forms, count and placement. Substantial analysis needs 2-5 distinct useful "
    "source-bound charts; genuine narrow news/policy may justify zero with an explicit editorial reason. "
    "Use media-plan --binding <binding_path> to obtain the native Light plan request, submit its exact stage, "
    "then complete the actual MAX visual decision in the same writer context and use Neo and existing media/data tools. Bind plan/request/source identities "
    "and inspected hash-bound assets with media-plan --response <asset-plan.json>; advance the same operation. "
    "After writing, bind those exact assets with media before review. A gap notice or fact card cannot replace useful analysis. "
    "READER POLICY CONTENTOPS_V1_READER_ATTRIBUTION_AND_TIMEZONE_POLICY_V1: omit discretionary Sources/References "
    "lists, repeated citation links and ritual cutoff footers by default. Retain natural relay/claim attribution and "
    "uncertainty, mandatory quotation/photo/reuse credits and meaningful chart metric/unit/period/context. Useful exact "
    "public times use America/New_York with date-correct EDT/EST or UTC; internal UTC and Bangkok calendars stay exact. "
    "PERMANENT FINAL PRODUCT RULE CONTENTOPS_V1_FINAL_MEDIA_REVIEW_AND_REPAIR_RULE_V1: after final assembly, "
    "the SAME actual designated strongest native editor/writer (currently gpt-6.1-sol/max) must inspect actual "
    "canonical and all affected channel rendered pixels at desktop/mobile. Use final-visual-review --binding "
    "<binding_path> to obtain exact render targets, then --response <render-manifest.json> to issue its existing "
    "native request. Same MAX inspects every chart's admitted values, sign/zero baseline/scale/rounding/periods/units, "
    "labels/legend/readability/crops and each photograph's identity/context/rights/credit/alt/placement. "
    "Submit its actual request-bound final-visual-* return and include that exact reference as final_visual_review "
    "in the existing revision-bound review. No missing/stale/wrong-model acceptance or unresolved finding can send. "
    "The SAME MAX directly repairs concrete defects with existing media/source/code tools, preserves valid work, "
    "re-renders only affected views and rechecks the corrected revision. The earlier one-useful-repair wording "
    "never caps necessary targeted correction: do not discard the article, change stories or restart intake. "
    "Changed render/media/copy invalidates affected acceptance; reuse unchanged valid assets and views. "
    "A later approved stronger editor may replace the active assignment consistently; the obligation is permanent. "
    "Record review --binding <binding_path> --response <review.json> with exact article_identity, "
    "decision KEEP/REVISE/HOLD, rationale and expected_review_id for a revision; KEEP can then "
    "prepare handoff --binding <binding_path> "
    "through the existing sole DurablePublicationCoordinator plan. Neither command publishes. "
    "Then publication-prepare and publication-resume --binding <binding_path> --rollout config/native_desktop_rollout_v1.json "
    "--native-invocation-id <actual-active-turn-id> use the existing sole coordinator. For each returned native request, "
    "publication-tool-begin its exact request hash, execute the actual Neo identity/publish/readback action, "
    "and publication-tool-submit the observed bound return; resume that same coordinator. "
    "Readback of the real canonical Substack /p/ URL precedes derivative rematerialization and sends. "
    "Never publish retained pre-activation examples or owner-removed objects. A claimed uncertain write permits only readback. "
    "Missing access is destination-local; continue available admitted channels. Preserve exact identities and source/media rights. "
    "Browser path Neo; bulk X ingestion stays CDP. Do not edit source, run tests/CodeGraph or alter schedules/pause during routine work. "
    + SUBAGENT_COMPLETION_RULE + SCHEDULED_WINDOW_RESULT_RULE
)
STANDALONE_TASK_HANDOFF_RULE = (
    " STANDALONE TASK HANDOFF — Jim30October2026: only a separate triggered task chat outside L1/L2/L3 uses "
    "task-result --binding <same-binding> --response <JSON containing entry_path newsroom/follow-up/editorial-revision, "
    "actual source_context with source_role:STANDALONE_TASK and source_thread_id/source_turn_id, actual_entry_gmt7, "
    "next_action and next_actor>. Save the actual terminal run result first; typed HOLD/NO_STORY/NO_CHANGE are "
    "valid results, never product success. After WINDOW_RESULT_SAVED use task-notice-begin, execute its ONE returned "
    "send_message_to_thread to L2 ContentOps01a1657e-f5d0-76a1-b52b-ec6c78b6fe35 host local, then task-notice-record "
    "with the ACTUAL tool result. Genuine inability to continue uses task-blocked/task-blocked-begin/task-blocked-record "
    "with the same exact first-cause evidence contract as windows; it does not fence a later terminal handoff. "
    "Existing run/outbox records dedupe; failed/uncertain sends are recorded, with no retry or acknowledgement chain. "
    "Guard/duplicate/progress/quota/turn-end interruptions send nothing. Continue functioning native children, which "
    "return inside this operation and never message an ancestor. Engineering Builders retain whole-goal completion "
    "and one distinct real BLOCKED handoff, not per-article completion messages. A deterministic API/script cannot "
    "invoke native chat tools; record its unsupported delivery hook and keep the durable result readable, with no "
    "bridge, watcher, schedule or GUI workaround."
)

MANUAL_GO_PROMPT = (
    "Use contentops-newsroom and scripts/run_native_desktop_editorial.py newsroom with the current "
    "config/native_desktop_operator_profile_v1.json, a stable operation-id and Jim's normal-language request. "
    "Resolve/resume the exact existing owner-manual binding in the editorial workspace isolated from production; the agent handles request/claim/return details. "
    "Luna MAX filters the full unprocessed admissible backlog in resumable batches; Sol Light selects/prepares "
    "evidence; Sol MAX writes the exact institutional-edge/SEO package and at most one same-writer repair. "
    "Advance, read each exact pending request, use its assigned native role and submit observed provenance; "
    "validate and inspect the article and eight native previews. No production pause release "
    "or schedule mutation; no publication. "
    + SUBAGENT_COMPLETION_RULE + STANDALONE_TASK_HANDOFF_RULE
)



def volume_task_setup_packet() -> dict[str, Any]:
    """Stage only; App updates are applied at the authorized production boundary."""
    from live_contentops.native_brief_windows_v1 import BRIEF_WINDOWS
    from live_contentops.native_newsroom_volume_v1 import CONFIG_PATH
    policy = json.loads(CONFIG_PATH.read_bytes())
    packet = four_task_setup_packet()
    directions = (
        " NEXT-PRODUCTION-DAY VOLUME: Apply only to new bindings from production day 30 October 2026, boundary 02:00 Asia/Saigon. "
        "The 01:00 on 30 October belongs to 29 October and retains its old limits. Obey the binding's volume_policy. "
        "Admit up to six useful full-window candidates ranked first by free source resolvability across Tier 1 assets/macro events. "
        "Use the SAME original admission plan across fallbacks; HOLD/SOURCE_BLOCKED advances via scheduled --continue-after <completed-run>. "
        "Carry the existing shared ten non-chargeable source requests across all candidates/slots; never reset after a refusal. "
        "Full windows may publish at most two distinct useful canonical articles; keep current roles and final MAX rendered review/repair. "
        "Source-sufficient NEWS/POLICY briefs may omit photos, with Instagram explicitly skipped; ANALYSIS retains photo/charts. "
        "For a photo-less brief, submit media-plan with assets:[] after actual Light/MAX planning, then write, render/review and publish through the sole coordinator. "
        "Measure actual funnel/first causes/confirmed canonical IDs/channel copies/time-to-readback/interventions and unknown reader counts in the existing day record. "
        "If an actual Codex quota stop affects this Builder or an authorized Database observation, record quota-stop with the exact source/time/lane in the same binding. "
        "Use supported App automation_update to PAUSE the three added brief tasks first, retaining their fields and all four full tasks. "
        "Do not poll Database or create a replacement child, callback, watcher, fetcher, ledger, timer or model API fallback."
    )
    def revised_prompt(prompt):
        return (prompt.replace("Source limit six shared requests per article; primary plus <=2 useful fallback candidates.",
            "A full window shares ten non-chargeable requests across up to six candidates and two canonical articles.")
            .replace("Before a new MAX writer freezes, the mandatory media-plan stage retains one relevant lawful documentary photo.",
                "Before MAX writing, complete the exact media plan; dated NEWS/POLICY briefs may use assets:[] while ANALYSIS retains its lawful photo.") + directions)
    tasks = [{**task, "prompt": revised_prompt(task["prompt"])} for task in packet["tasks"]]
    for task_id, (session, hour) in BRIEF_WINDOWS.items():
        local_hour = hour + 7
        tasks.append({"id": task_id, "name": "V1 Newsroom — " + session.replace('_', ' '),
            "rrule": f"RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR={local_hour};BYMINUTE=0",
            "status": "PAUSED", "model": "gpt-6.1-sol", "reasoning_effort": "low",
            "prompt": (
                "BRIEF ENTRY FIRST: run python scripts/run_native_desktop_editorial.py scheduled --automation-id "
                + task_id + " --rollout config/native_desktop_rollout_v1.json before source acquisition or native role delegation. "
                "If classification is NOT_YET_EFFECTIVE, record that exact result and actual entry in this task's existing memory, "
                "then exit immediately with zero source requests and no publication. Do not call advance or allocate a child. "
                "The executable in-run guard becomes eligible at 02:00 Asia/Saigon on 30 October 2026. "
                "If a binding is returned, continue that SAME binding through the protocol below. "
                + revised_prompt(DESKTOP_TASK_PROMPT.replace("{automation_id}", task_id))) +
                " BRIEF-ONLY WINDOW: one useful NEWS/POLICY brief, up to three admissions, same ten free requests. Do not relabel ANALYSIS. If no useful admissible item, retain a typed NO_STORY/HOLD without media."})
    return {"schema_version": "contentops.native_volume_task_setup.v1", "effective_production_date": policy["effective_production_date"],
        "activate_not_before_utc": "2026-10-29T19:00:00Z", "application_state": "STAGED_NOT_APPLIED",
        "tasks": tasks, "additional_brief_tasks": list(BRIEF_WINDOWS), "existing_full_tasks_unchanged_until_boundary": True}


def four_task_setup_packet() -> dict[str, Any]:
    """The same four active Light coordinators; actual authority/control guards own sends."""
    from live_contentops.native_desktop_editorial_v1 import ROLE_ASSIGNMENTS

    tasks = [
        {
            "id": EXACT_V1_AUTOMATION_IDS[0],
            "name": "V1 Newsroom — London 1700",
            "days": "Monday-Friday",
            "time": "17:00",
            "rrule": "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=17;BYMINUTE=0",
        },
        {
            "id": EXACT_V1_AUTOMATION_IDS[1],
            "name": "V1 Newsroom — New York 2100",
            "days": "Monday-Friday",
            "time": "21:00",
            "rrule": "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=21;BYMINUTE=0",
        },
        {
            "id": EXACT_V1_AUTOMATION_IDS[2],
            "name": "V1 Newsroom — New York 2300",
            "days": "Monday-Friday",
            "time": "23:00",
            "rrule": "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=23;BYMINUTE=0",
        },
        {
            "id": EXACT_V1_AUTOMATION_IDS[3],
            "name": "V1 Newsroom — New York 0100",
            "days": "Tuesday-Saturday",
            "time": "01:00",
            "rrule": "RRULE:FREQ=WEEKLY;BYDAY=TU,WE,TH,FR,SA;BYHOUR=1;BYMINUTE=0",
        },
    ]
    return {
        "schema_version": "contentops.desktop_four_task_setup.v1",
        "policy_id": QUALITY_PROBATION_POLICY_ID,
        "project": r"A:\Capital Chronicle\ContentOps",
        "timezone": "Asia/Bangkok",
        "model": "gpt-6.1-sol",
        "reasoning_effort": "low",
        "editorial_worker_model": "gpt-6.1-sol",
        "editorial_worker_reasoning_effort": "max",
        "editorial_worker_is_fresh_and_isolated": True,
        "editorial_worker_only_when_article_warranted": True,
        "one_coherent_desktop_turn": True,
        "subagents_only_for_independent_need": False,
        "subagents_for_assigned_native_roles": True,
        "editorial_role_policy": "CONTENTOPS_NATIVE_DESKTOP_EDITORIAL_ROLE_POLICY_V2",
        "editorial_roles": {role: dict(settings) for role, settings in ROLE_ASSIGNMENTS.items()},
        "role_settings_state": "CONFIGURED_TARGET_NOT_INVOCATION_PROOF",
        "target_status": "ACTIVE",
        "speed": "standard",
        "tasks": [{**task, "status": "ACTIVE", "model": "gpt-6.1-sol", "reasoning_effort": "low",
                   "prompt": DESKTOP_TASK_PROMPT.replace("{automation_id}", task["id"])} for task in tasks],
        "routine_task_count": len(tasks),
        "build_qualified_floor": 4,
        "final_published_target_min": 5,
        "final_published_target_max": 8,
        "publication_minimum": 5,
        "newsroom_production_day_timezone": "Asia/Bangkok",
        "following_0100_belongs_to_prior_production_day": True,
        "bounded_later_window_deficit_catch_up": True,
        "automatic_scale_up": False,
        "material_event_creates_extra_task": False,
        "manual_go_is_explicit_exception": True,
        "prompt": DESKTOP_TASK_PROMPT,
    }


def persist_supported_automation_host_observation(
    *,
    tasks: Sequence[Mapping[str, Any]],
    output_path: str | Path,
    observed_at_utc: datetime | str,
    observation_source: str = "SUPPORTED_CODEX_APP_AUTOMATION_VIEW_AND_CONFIG",
) -> dict[str, Any]:
    """Persist a bounded non-secret readback of the four supported App automations."""
    expected = four_task_setup_packet()
    intended_by_id = {str(row["id"]): row for row in expected["tasks"]}
    safe_tasks: list[dict[str, Any]] = []
    for task in tasks:
        task_id = str(task.get("id") or "")
        if task_id not in intended_by_id:
            raise ValueError(f"unexpected_automation_id:{task_id or 'missing'}")
        safe = {
            key: task.get(key)
            for key in (
                "id",
                "name",
                "status",
                "rrule",
                "timezone",
                "project",
                "project_id",
                "model",
                "reasoning_effort",
                "prompt_sha256",
            )
        }
        host_config_sha256 = str(
            task.get("host_config_sha256") or task.get("config_sha256") or ""
        ).strip()
        if len(host_config_sha256) != 64 or any(
            character not in "0123456789abcdefABCDEF"
            for character in host_config_sha256
        ):
            raise ValueError(f"host_config_sha256_invalid:{task_id}")
        safe["host_config_sha256"] = host_config_sha256.lower()
        safe["observation_projection_sha256"] = _logical_hash(safe)
        safe_tasks.append(safe)
    if tuple(sorted(str(row["id"]) for row in safe_tasks)) != tuple(
        sorted(EXACT_V1_AUTOMATION_IDS)
    ):
        raise ValueError("exact_four_automation_ids_not_observed")
    observed = (
        observed_at_utc
        if isinstance(observed_at_utc, datetime)
        else datetime.fromisoformat(str(observed_at_utc).replace("Z", "+00:00"))
    )
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    payload = {
        "schema_version": AUTOMATION_HOST_OBSERVATION_SCHEMA_VERSION,
        "observed_at_utc": observed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "observation_source": observation_source,
        "configured_intent_prompt_sha256": hashlib.sha256(
            expected["prompt"].encode("utf-8")
        ).hexdigest(),
        "task_count": 4,
        "all_exact_ids_present": True,
        "no_fifth_task_created": True,
        "all_paused": all(str(row.get("status") or "").upper() == "PAUSED" for row in safe_tasks),
        "all_model_match": all(
            str(row.get("model") or "") == expected["model"] for row in safe_tasks
        ),
        "all_reasoning_effort_match": all(
            str(row.get("reasoning_effort") or "").upper()
            == expected["reasoning_effort"].upper()
            for row in safe_tasks
        ),
        "all_prompt_match_configured_intent": all(
            str(row.get("prompt_sha256") or "")
            == hashlib.sha256(intended_by_id[row["id"]]["prompt"].encode("utf-8")).hexdigest()
            for row in safe_tasks
        ),
        "supported_automation_operations_observed": [
            "CREATE", "DELETE", "UPDATE", "VIEW"
        ],
        "supported_run_now_operation_observed": False,
        "automation_configuration_mutated": False,
        "automation_enabled": False,
        "secrets_cookies_tokens_or_session_material_read": False,
        "public_write_performed": False,
        "unknown_write_count": 0,
        "tasks": sorted(safe_tasks, key=lambda row: str(row["id"])),
    }
    payload["observation_sha256"] = _logical_hash(payload)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return payload


def _logical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def build_hybrid_editorial_run_identity(
    *,
    runtime_run_id: str,
    production_day_id: str,
    opportunity_id: str,
    story_identity: str,
    governed_input_hash: str,
) -> dict[str, Any]:
    """Bind both editorial providers to one existing runtime opportunity and evidence packet."""
    values = {
        "runtime_run_id": str(runtime_run_id or "").strip(),
        "production_day_id": str(production_day_id or "").strip(),
        "opportunity_id": str(opportunity_id or "").strip(),
        "story_identity": str(story_identity or "").strip(),
        "governed_input_hash": str(governed_input_hash or "").strip().lower(),
    }
    missing = sorted(key for key, value in values.items() if not value)
    if missing:
        raise ValueError("hybrid_editorial_run_identity_missing:" + ",".join(missing))
    evidence_hash = values["governed_input_hash"]
    if len(evidence_hash) != 64 or any(
        character not in "0123456789abcdef" for character in evidence_hash
    ):
        raise ValueError("hybrid_editorial_governed_input_hash_invalid")
    identity = {
        "schema_version": HYBRID_EDITORIAL_RUN_IDENTITY_SCHEMA_VERSION,
        **values,
    }
    identity["canonical_run_identity"] = _logical_hash(identity)
    return identity


def _validate_hybrid_run_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    supplied = dict(identity)
    canonical = str(supplied.pop("canonical_run_identity", "") or "")
    if supplied.get("schema_version") != HYBRID_EDITORIAL_RUN_IDENTITY_SCHEMA_VERSION:
        raise ValueError("hybrid_editorial_run_identity_schema_invalid")
    if not canonical or _logical_hash(supplied) != canonical:
        raise ValueError("hybrid_editorial_run_identity_hash_mismatch")
    return {**supplied, "canonical_run_identity": canonical}


def arbitrate_hybrid_editorial_execution(
    *,
    run_identity: Mapping[str, Any],
    observed_at_utc: datetime | str,
    valid_window_ends_at_utc: datetime | str,
    desktop_primary_receipt: Mapping[str, Any] | None = None,
    sdk_fallback_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Choose one editorial owner without adding a scheduler, store, queue, or publisher.

    Desktop is the routine primary.  The SDK can begin only after an observable primary failure or
    missed valid window.  Once fallback starts, a late Desktop completion is retained as evidence
    but cannot become a second canonical article or public object.
    """
    identity = _validate_hybrid_run_identity(run_identity)
    observed = _parse_utc(observed_at_utc)
    window_end = _parse_utc(valid_window_ends_at_utc)
    if observed is None or window_end is None:
        raise ValueError("hybrid_editorial_arbitration_time_invalid")
    canonical_id = identity["canonical_run_identity"]

    desktop = dict(desktop_primary_receipt or {})
    fallback = dict(sdk_fallback_receipt or {})
    for label, receipt in (("desktop", desktop), ("sdk", fallback)):
        receipt_identity = str(receipt.get("canonical_run_identity") or "")
        if receipt_identity and receipt_identity != canonical_id:
            raise ValueError(f"hybrid_editorial_{label}_run_identity_mismatch")

    desktop_state = str(desktop.get("state") or "NOT_OBSERVED").strip().upper()
    fallback_state = str(fallback.get("state") or "NOT_STARTED").strip().upper()
    valid_desktop_states = {
        "NOT_OBSERVED", "PENDING", "ACCEPTED", "MISSED_VALID_WINDOW",
        "FAILED_PRIMARY", "TERMINAL_NO_ARTICLE",
    }
    valid_fallback_states = {"NOT_STARTED", "STARTED", "ACCEPTED", "FAILED"}
    if desktop_state not in valid_desktop_states:
        raise ValueError("hybrid_editorial_desktop_state_invalid")
    if fallback_state not in valid_fallback_states:
        raise ValueError("hybrid_editorial_sdk_state_invalid")

    late_desktop = False
    if desktop_state == "ACCEPTED":
        desktop_completed = _parse_utc(desktop.get("completed_at_utc"))
        if desktop_completed is None:
            raise ValueError("hybrid_editorial_desktop_completion_time_required")
        late_desktop = desktop_completed > window_end

    fallback_has_started = fallback_state != "NOT_STARTED"
    if fallback_has_started:
        if fallback_state == "ACCEPTED":
            decision = "ACCEPT_SDK_FALLBACK"
            owner = "SDK_FALLBACK"
            reason = "SDK_FALLBACK_ALREADY_ACCEPTED"
        elif fallback_state == "FAILED":
            decision = "SDK_FALLBACK_FAILED_NO_DESKTOP_REENTRY"
            owner = "NONE"
            reason = "SDK_FALLBACK_TERMINAL"
        else:
            decision = "SDK_FALLBACK_ALREADY_IN_FLIGHT"
            owner = "SDK_FALLBACK"
            reason = "SDK_FALLBACK_ALREADY_STARTED"
        late_desktop = late_desktop or desktop_state == "ACCEPTED"
    elif desktop_state == "ACCEPTED" and not late_desktop:
        decision = "ACCEPT_DESKTOP_PRIMARY"
        owner = "DESKTOP_PRIMARY"
        reason = "DESKTOP_PRIMARY_ACCEPTED_WITHIN_VALID_WINDOW"
    elif desktop_state == "TERMINAL_NO_ARTICLE":
        decision = "TERMINAL_NO_ARTICLE_NO_PROVIDER_FALLBACK"
        owner = "NONE"
        reason = "CANONICAL_CONTENT_OR_SAFETY_GATE_TERMINAL"
    elif desktop_state in {"MISSED_VALID_WINDOW", "FAILED_PRIMARY"}:
        decision = "START_SDK_FALLBACK"
        owner = "SDK_FALLBACK"
        reason = f"DESKTOP_PRIMARY_{desktop_state}"
    elif late_desktop:
        decision = "START_SDK_FALLBACK"
        owner = "SDK_FALLBACK"
        reason = "DESKTOP_PRIMARY_COMPLETED_AFTER_VALID_WINDOW"
    elif observed > window_end:
        decision = "START_SDK_FALLBACK"
        owner = "SDK_FALLBACK"
        reason = "DESKTOP_PRIMARY_VALID_WINDOW_EXPIRED"
    else:
        decision = "WAIT_FOR_DESKTOP_PRIMARY"
        owner = "NONE"
        reason = "DESKTOP_PRIMARY_VALID_WINDOW_OPEN"

    receipt = {
        "schema_version": HYBRID_EDITORIAL_ARBITRATION_SCHEMA_VERSION,
        "run_identity": identity,
        "canonical_run_identity": canonical_id,
        "runtime_run_id": identity["runtime_run_id"],
        "observed_at_utc": _iso_utc(observed),
        "valid_window_ends_at_utc": _iso_utc(window_end),
        "desktop_primary_state": desktop_state,
        "sdk_fallback_state": fallback_state,
        "decision": decision,
        "reason": reason,
        "canonical_article_owner": owner,
        "desktop_is_primary_for_routine_opportunities": True,
        "sdk_roles": ["BOUNDED_FALLBACK", "DIRECT_EVENT_PATH", "BENCHMARK"],
        "sdk_fallback_start_authorized": decision == "START_SDK_FALLBACK",
        "late_desktop_completion_suppressed": bool(late_desktop),
        "duplicate_article_or_public_object_authorized": False,
        "scheduler_created": False,
        "store_created": False,
        "publisher_created": False,
        "publication_authority": False,
        "public_write_performed": False,
    }
    receipt["arbitration_logical_hash"] = _logical_hash(receipt)
    return receipt


def validate_hybrid_editorial_arbitration_receipt(
    receipt: Mapping[str, Any], *, expected_runtime_run_id: str | None = None
) -> dict[str, Any]:
    """Validate an arbitration receipt before the facade constructs an SDK fallback."""
    supplied = dict(receipt)
    supplied_hash = str(supplied.pop("arbitration_logical_hash", "") or "")
    if supplied.get("schema_version") != HYBRID_EDITORIAL_ARBITRATION_SCHEMA_VERSION:
        raise ValueError("hybrid_editorial_arbitration_schema_invalid")
    if not supplied_hash or _logical_hash(supplied) != supplied_hash:
        raise ValueError("hybrid_editorial_arbitration_hash_mismatch")
    identity = supplied.get("run_identity")
    if not isinstance(identity, Mapping):
        raise ValueError("hybrid_editorial_arbitration_run_identity_missing")
    validated_identity = _validate_hybrid_run_identity(identity)
    if supplied.get("canonical_run_identity") != validated_identity["canonical_run_identity"]:
        raise ValueError("hybrid_editorial_arbitration_identity_binding_mismatch")
    if expected_runtime_run_id is not None and supplied.get("runtime_run_id") != str(
        expected_runtime_run_id
    ):
        raise ValueError("hybrid_editorial_arbitration_runtime_run_id_mismatch")
    return {**supplied, "arbitration_logical_hash": supplied_hash}


def prepared_candidate_continuity_binding(
    *,
    continuity: Mapping[str, Any],
    evaluated_headline_ids: Sequence[str],
    reentry_headline_ids: Sequence[str],
) -> dict[str, Any]:
    """Build the shared durable-continuity binding for canonical frontier preparation."""
    evaluated = sorted(str(value) for value in evaluated_headline_ids if str(value))
    reentry = sorted(str(value) for value in reentry_headline_ids if str(value))
    return {
        "terminal_window_id": continuity.get("terminal_window_id"),
        "last_terminal_cutoff_utc": continuity.get("last_terminal_cutoff_utc"),
        "evaluated_headline_count": len(evaluated),
        "evaluated_headline_ids_hash": _logical_hash(evaluated),
        "material_reentry_headline_count": len(reentry),
        "material_reentry_headline_ids_hash": _logical_hash(reentry),
        "continuity_logical_hash": continuity.get("continuity_logical_hash"),
    }


def build_editorial_worker_routing_packet(
    *,
    opportunity_state: str,
    governed_context: Mapping[str, Any] | None = None,
    readiness_checked_before_editorial: bool = False,
    readiness_state: str = "UNKNOWN",
    article_mode: str = "STANDARD_ANALYSIS",
) -> dict[str, Any]:
    """Return a deterministic Desktop routing decision without spawning or calling a model.

    The native HIGH coordinator consumes this contract. The actual fresh child is created by the
    Desktop task only at the editorial boundary; this function is not a Desktop bridge.
    """
    state = str(opportunity_state or "").strip().upper()
    current_readiness = str(readiness_state or "UNKNOWN").strip().upper()
    if state not in NO_EDITORIAL_WORKER_PATHS and state != "ARTICLE_QUALIFIED":
        raise ValueError("desktop_editorial_opportunity_state_unknown")

    base = {
        "schema_version": "contentops.desktop_editorial_worker_routing.v1",
        "coordinator": {
            "model": COORDINATOR_MODEL,
            "reasoning_effort": COORDINATOR_REASONING_EFFORT,
            "owns_deterministic_validation_after_return": True,
            "owns_publication_coordination": True,
        },
        "opportunity_state": state,
        "readiness_checked_before_editorial": bool(readiness_checked_before_editorial),
        "readiness_state": current_readiness,
        "readiness_is_publication_diagnostic_only": state == "ARTICLE_QUALIFIED",
        "desktop_bridge_created": False,
        "scheduler_or_queue_created": False,
        "public_write_performed": False,
    }
    if state in NO_EDITORIAL_WORKER_PATHS:
        result = {
            **base,
            "decision": "HIGH_ONLY_NO_EDITORIAL_WORKER",
            "xhigh_worker_count_requested": 0,
            "worker_request": None,
            "governed_input_hash": None,
        }
        result["routing_logical_hash"] = _logical_hash(result)
        return result

    if not isinstance(governed_context, Mapping):
        raise ValueError("desktop_editorial_governed_context_required")
    extra_keys = sorted(set(governed_context).difference(BOUNDED_EDITORIAL_CONTEXT_KEYS))
    if extra_keys:
        raise ValueError("desktop_editorial_context_unbounded_keys:" + ",".join(extra_keys))
    bounded_context = {
        key: governed_context[key]
        for key in sorted(BOUNDED_EDITORIAL_CONTEXT_KEYS)
        if key in governed_context
    }
    if not bounded_context.get("accepted_evidence_packet"):
        raise ValueError("desktop_editorial_accepted_evidence_packet_required")
    if not bounded_context.get("exact_source_handles"):
        raise ValueError("desktop_editorial_exact_source_handles_required")
    from live_contentops.capital_chronicle_institutional_edge_v1 import (
        build_institutional_edge_editorial_packet,
        validate_institutional_edge_packet,
    )

    supplied_editorial_packet = bounded_context.get("institutional_edge_editorial_packet")
    editorial_packet = build_institutional_edge_editorial_packet(
        article_mode=article_mode,
        accepted_evidence_packet=bounded_context.get("accepted_evidence_packet"),
        structured_data_supported=True,
    )
    if supplied_editorial_packet is not None and supplied_editorial_packet != editorial_packet:
        raise ValueError("desktop_editorial_authority_packet_override_forbidden")
    packet_blockers = validate_institutional_edge_packet(editorial_packet)
    if packet_blockers:
        raise ValueError("desktop_editorial_authority_packet_invalid:" + ",".join(packet_blockers))
    bounded_context["institutional_edge_editorial_packet"] = editorial_packet
    governed_input_hash = _logical_hash(bounded_context)
    exact_source_identities = [
        str(value) for value in bounded_context.get("exact_source_handles") or []
        if str(value)
    ]
    exact_source_markers = [
        f"[[SOURCE:SOURCE_{index}]]"
        for index in range(1, len(exact_source_identities) + 1)
    ]
    result = {
        **base,
        "decision": "SPAWN_ONE_FRESH_ISOLATED_XHIGH_EDITORIAL_WORKER",
        "xhigh_worker_count_requested": 1,
        "governed_input_hash": governed_input_hash,
        "worker_request": {
            "model": EDITORIAL_WORKER_MODEL,
            "reasoning_effort": EDITORIAL_WORKER_REASONING_EFFORT,
            "fresh": True,
            "isolated": True,
            "resume_existing": False,
            "governed_input_hash": governed_input_hash,
            "bounded_governed_context": bounded_context,
            "exact_source_marker_contract": {
                "required_for_source_bound_factual_copy": True,
                "copy_exact_supplied_markers_only": True,
                "exact_supplied_markers": exact_source_markers,
                "source_identity_order": exact_source_identities,
                "marker_format": "[[SOURCE:SOURCE_N]]",
                "deterministic_marker_injection_after_authorship": False,
                "invent_urls_handles_source_ids_evidence_ids_or_facts": False,
            },
            "max_bounded_editorial_revisions": MAX_EDITORIAL_REVISIONS,
            "deterministic_validator_revision_contract": {
                "same_worker_required": True,
                "fresh_replacement_worker_forbidden": True,
                "maximum_revision_count": MAX_EDITORIAL_REVISIONS,
                "validator_bypass_forbidden": True,
                "blocker_instructions": {
                    "fake_or_unbound_quote_presentation": (
                        FAKE_OR_UNBOUND_QUOTE_REPAIR_INSTRUCTION
                    ),
                },
            },
            "grants_factual_authority": False,
            "grants_numeric_authority": False,
            "grants_capital_chronicle_authority": False,
            "grants_permission_authority": False,
            "grants_public_write_authority": False,
        },
    }
    result["routing_logical_hash"] = _logical_hash(result)
    return result


def _sanitized_review_codes(value: Any) -> list[str]:
    """Keep only stable review-code identifiers in a worker continuation contract."""
    codes: set[str] = set()
    for row in value or []:
        if isinstance(row, Mapping):
            candidate = str(row.get("code") or "")
        else:
            candidate = str(row or "")
        if candidate:
            codes.add(candidate)
    return sorted(codes)


def build_same_xhigh_worker_revision_contract(
    *,
    worker_return: Mapping[str, Any],
    worker_validation: Mapping[str, Any],
    worker_request: Mapping[str, Any],
    deterministic_review: Mapping[str, Any],
    semantic_review: Mapping[str, Any],
) -> dict[str, Any]:
    """Issue one exact same-worker revision request without creating an author fallback.

    The original worker was fresh and isolated.  A revision therefore resumes that same bounded
    worker; it is neither a new XHIGH worker nor a 9Router article-writing request.  The full
    governed context is retained only in the runtime request, while review feedback is reduced to
    stable deterministic/sanitized codes.
    """
    governed_input_hash = str(worker_validation.get("governed_input_hash") or "")
    bounded_context = worker_request.get("bounded_governed_context")
    if not governed_input_hash or not isinstance(bounded_context, Mapping):
        raise ValueError("same_xhigh_revision_governed_context_required")
    if str(worker_request.get("governed_input_hash") or "") != governed_input_hash:
        raise ValueError("same_xhigh_revision_worker_request_hash_mismatch")
    if _logical_hash(dict(bounded_context)) != governed_input_hash:
        raise ValueError("same_xhigh_revision_governed_context_hash_mismatch")
    revision_count = int(worker_return.get("bounded_revision_count") or 0)
    if revision_count < 0 or revision_count >= MAX_EDITORIAL_REVISIONS:
        raise ValueError("same_xhigh_revision_budget_exhausted")
    return_hash = str(worker_validation.get("worker_return_hash") or "")
    if not return_hash:
        raise ValueError("same_xhigh_revision_prior_return_hash_required")
    if _logical_hash(worker_return) != return_hash:
        raise ValueError("same_xhigh_revision_prior_return_binding_mismatch")
    accepted_evidence = dict(bounded_context.get("accepted_evidence_packet") or {})
    evidence_identity = sorted(
        {
            str(row.get("document_id") or row.get("evidence_id") or "")
            for row in accepted_evidence.get("evidence_documents") or []
            if isinstance(row, Mapping)
            and str(row.get("document_id") or row.get("evidence_id") or "")
        }
    )
    contract = {
        "schema_version": "contentops.same_xhigh_worker_revision_contract.v1",
        "decision": "SAME_XHIGH_WORKER_REVISION_REQUIRED",
        "governed_input_hash": governed_input_hash,
        "prior_worker_return_hash": return_hash,
        "prior_bounded_revision_count": revision_count,
        "required_bounded_revision_count": revision_count + 1,
        "maximum_bounded_revision_count": MAX_EDITORIAL_REVISIONS,
        "same_worker_required": True,
        "fresh_replacement_worker_forbidden": True,
        "router_final_writer_forbidden": True,
        "worker_request": {
            "model": EDITORIAL_WORKER_MODEL,
            "reasoning_effort": EDITORIAL_WORKER_REASONING_EFFORT,
            "resume_same_isolated_worker": True,
            "fresh_worker_creation": False,
            "governed_input_hash": governed_input_hash,
            "bounded_governed_context": dict(bounded_context),
            "exact_source_marker_contract": dict(
                worker_request.get("exact_source_marker_contract") or {}
            ),
            "max_bounded_editorial_revisions": MAX_EDITORIAL_REVISIONS,
        },
        "immutable_evidence_identity": {
            "evidence_document_ids": evidence_identity,
            "exact_source_handles": [
                str(value)
                for value in bounded_context.get("exact_source_handles") or []
                if str(value)
            ],
        },
        "deterministic_blockers": {
            "hard_editorial_blockers": _sanitized_review_codes(
                deterministic_review.get("hard_editorial_blockers")
            ),
            "editorial_blockers": _sanitized_review_codes(
                deterministic_review.get("editorial_blockers")
            ),
            "reader_value_blockers": _sanitized_review_codes(
                (deterministic_review.get("reader_value_gate") or {}).get("blockers")
                if isinstance(deterministic_review.get("reader_value_gate"), Mapping)
                else []
            ),
        },
        "semantic_review": {
            "decision": str(semantic_review.get("decision") or "NEEDS_REVISION"),
            "failed_checks": _sanitized_review_codes(
                semantic_review.get("failed_checks")
            ),
            "material_failed_checks": _sanitized_review_codes(
                semantic_review.get("material_failed_checks")
            ),
            "issue_codes": _sanitized_review_codes(semantic_review.get("issues")),
        },
        "public_write_authority": False,
        "publication_authority": False,
    }
    contract["revision_contract_hash"] = _logical_hash(contract)
    return contract


def validate_same_xhigh_worker_revision_return(
    *,
    worker_return: Mapping[str, Any],
    revision_contract: Mapping[str, Any],
    expected_editorial_packet: Mapping[str, Any] | None = None,
    accepted_evidence_packet: Mapping[str, Any] | None = None,
    acceptance_profile: str | None = None,
) -> dict[str, Any]:
    """Validate the one permitted same-worker revision against its original receipt."""
    if revision_contract.get("decision") != "SAME_XHIGH_WORKER_REVISION_REQUIRED":
        raise ValueError("same_xhigh_revision_contract_invalid")
    supplied_contract = dict(revision_contract)
    supplied_contract_hash = str(supplied_contract.pop("revision_contract_hash", "") or "")
    if not supplied_contract_hash or _logical_hash(supplied_contract) != supplied_contract_hash:
        raise ValueError("same_xhigh_revision_contract_hash_mismatch")
    if worker_return.get("same_worker_revision_of_return_hash") != revision_contract.get(
        "prior_worker_return_hash"
    ):
        raise ValueError("same_xhigh_revision_prior_return_hash_mismatch")
    if int(worker_return.get("bounded_revision_count") or 0) != int(
        revision_contract.get("required_bounded_revision_count") or -1
    ):
        raise ValueError("same_xhigh_revision_count_mismatch")
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
        resolve_article_transport_envelope,
    )

    resolved_article = resolve_article_transport_envelope(worker_return)
    article_evidence_ids = {
        str(value)
        for value in resolved_article.get("evidence_document_ids") or []
        if str(value)
    }
    immutable_evidence_ids = {
        str(value)
        for value in (
            revision_contract.get("immutable_evidence_identity") or {}
        ).get("evidence_document_ids") or []
        if str(value)
    }
    if article_evidence_ids and article_evidence_ids != immutable_evidence_ids:
        raise ValueError("same_xhigh_revision_evidence_identity_mismatch")
    validated = validate_editorial_worker_return(
        worker_return=worker_return,
        expected_governed_input_hash=str(revision_contract.get("governed_input_hash") or ""),
        expected_editorial_packet=expected_editorial_packet,
        accepted_evidence_packet=accepted_evidence_packet,
        acceptance_profile=acceptance_profile,
    )
    return {
        **validated,
        "same_xhigh_worker_revision": True,
        "same_xhigh_worker_revision_contract_hash": str(
            revision_contract.get("revision_contract_hash") or ""
        ),
    }


def validate_editorial_worker_return(
    *,
    worker_return: Mapping[str, Any],
    expected_governed_input_hash: str,
    expected_editorial_packet: Mapping[str, Any] | None = None,
    accepted_evidence_packet: Mapping[str, Any] | None = None,
    acceptance_profile: str | None = None,
) -> dict[str, Any]:
    """Bind one XHIGH result to its exact input and return control to the HIGH coordinator."""
    if str(worker_return.get("governed_input_hash") or "") != expected_governed_input_hash:
        raise ValueError("desktop_editorial_worker_input_hash_mismatch")
    if str(worker_return.get("model") or "") != EDITORIAL_WORKER_MODEL:
        raise ValueError("desktop_editorial_worker_model_invalid")
    if str(worker_return.get("reasoning_effort") or "").upper() != EDITORIAL_WORKER_REASONING_EFFORT:
        raise ValueError("desktop_editorial_worker_reasoning_effort_invalid")
    if worker_return.get("fresh") is not True or worker_return.get("isolated") is not True:
        raise ValueError("desktop_editorial_worker_fresh_isolated_receipt_required")
    revision_count = int(worker_return.get("bounded_revision_count") or 0)
    if revision_count < 0 or revision_count > MAX_EDITORIAL_REVISIONS:
        raise ValueError("desktop_editorial_worker_revision_limit_exceeded")
    if bool(worker_return.get("public_write_attempted")):
        raise ValueError("desktop_editorial_worker_public_write_forbidden")
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
        normalize_article_transport_representation,
        resolve_article_transport_envelope,
    )

    article = resolve_article_transport_envelope(worker_return)
    if not isinstance(article, Mapping) or not str(article.get("title") or "").strip():
        raise ValueError("desktop_editorial_worker_article_invalid")
    representation_repairs: list[str] = []
    article = normalize_article_transport_representation(
        article,
        context={
            "institutional_edge_editorial_packet": dict(expected_editorial_packet or {})
        },
        repair_log=representation_repairs,
    )
    editorial_validation: dict[str, Any] | None = None
    if expected_editorial_packet is not None:
        from live_contentops.capital_chronicle_institutional_edge_v1 import (
            validate_institutional_edge_article,
        )

        editorial_validation = validate_institutional_edge_article(
            article,
            editorial_packet=expected_editorial_packet,
            accepted_evidence_packet=accepted_evidence_packet,
        )
        institutional_quality_warnings: list[str] = list(representation_repairs)
        if acceptance_profile:
            from live_contentops.mvp_canary_acceptance_v1 import (
                institutional_edge_hard_gate,
                is_mvp_canary_profile,
            )

            if is_mvp_canary_profile(acceptance_profile):
                canary_institutional = institutional_edge_hard_gate(editorial_validation)
                institutional_quality_warnings = sorted(
                    set(institutional_quality_warnings).union(
                        canary_institutional.get("quality_warnings") or []
                    )
                )
                if canary_institutional.get("classification") != "PASS":
                    raise ValueError(
                        "desktop_editorial_worker_institutional_edge_invalid:"
                        + ",".join(canary_institutional.get("hard_gate_blockers") or [])
                    )
            elif editorial_validation.get("classification") != "PASS":
                raise ValueError(
                    "desktop_editorial_worker_institutional_edge_invalid:"
                    + ",".join(editorial_validation.get("blockers") or [])
                )
        elif editorial_validation.get("classification") != "PASS":
            raise ValueError(
                "desktop_editorial_worker_institutional_edge_invalid:"
                + ",".join(editorial_validation.get("blockers") or [])
            )
        institutional_quality_warnings = sorted(
            set(institutional_quality_warnings).union(
                editorial_validation.get("soft_warnings") or []
            )
        )
    else:
        institutional_quality_warnings = list(representation_repairs)
    return_hash = _logical_hash(worker_return)
    return {
        "schema_version": "contentops.desktop_editorial_worker_return_validation.v1",
        "classification": "PASS_BOUND_XHIGH_EDITORIAL_RETURN",
        "governed_input_hash": expected_governed_input_hash,
        "worker_return_hash": return_hash,
        "worker_model": EDITORIAL_WORKER_MODEL,
        "worker_reasoning_effort": EDITORIAL_WORKER_REASONING_EFFORT,
        "worker_fresh_and_isolated": True,
        "bounded_revision_count": revision_count,
        "xhigh_publication_authority": False,
        "coordinator_resumes": True,
        "coordinator_model": COORDINATOR_MODEL,
        "coordinator_reasoning_effort": COORDINATOR_REASONING_EFFORT,
        "deterministic_validation_required": True,
        "institutional_edge_editorial_validation": editorial_validation,
        "normalized_article": article,
        "article_transport_representation_repairs": representation_repairs,
        "acceptance_profile": acceptance_profile,
        "institutional_edge_quality_warnings": institutional_quality_warnings,
        "publication_coordinator_remains_sole_public_writer": True,
        "public_write_performed": False,
    }


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, TypeError):
        return None
    return dict(value) if isinstance(value, Mapping) else None


def _parse_utc(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso_utc(value: datetime) -> str:
    moment = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@contextmanager
def _read_only_store(path: Path) -> Iterator[sqlite3.Connection]:
    resolved = path.resolve()
    connection = sqlite3.connect(
        f"file:{resolved.as_posix()}?mode=ro",
        uri=True,
        isolation_level=None,
        cached_statements=0,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    try:
        yield connection
    finally:
        connection.close()


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row["name"])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def _canonical_public_substack_url(value: Any) -> bool:
    try:
        parsed = urlsplit(str(value or ""))
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and (parsed.hostname or "").casefold() == CANONICAL_SUBSTACK_HOST
        and parsed.path.startswith("/p/")
        and len(parsed.path) > 3
    )


def _published_memory_from_store(connection: sqlite3.Connection) -> dict[str, Any]:
    required = {
        "work_items", "outbox_messages", "platform_dispatches", "reconciliations"
    }
    if not required.issubset(_table_names(connection)):
        return {
            "confirmed_canonical_count": 0,
            "story_identities": [],
            "update_chain_identities": [],
            "state": "REQUIRED_TABLES_UNAVAILABLE",
        }
    rows = connection.execute(
        "SELECT w.story_id,o.payload,d.public_object_url,r.status AS reconciliation_status "
        "FROM work_items w JOIN outbox_messages o ON o.work_item_id=w.work_item_id "
        "JOIN platform_dispatches d ON d.message_id=o.message_id "
        "JOIN reconciliations r ON r.work_item_id=w.work_item_id "
        "WHERE o.destination='substack' AND d.platform='substack' "
        "AND r.status='RECONCILED_CONFIRMED'"
    ).fetchall()
    story_ids: set[str] = set()
    chain_ids: set[str] = set()
    object_urls: set[str] = set()
    for row in rows:
        public_url = str(row["public_object_url"] or "")
        if not _canonical_public_substack_url(public_url):
            continue
        object_urls.add(public_url)
        payload: Mapping[str, Any] = {}
        try:
            parsed_payload = json.loads(str(row["payload"] or "{}"))
            if isinstance(parsed_payload, Mapping):
                payload = parsed_payload
        except (TypeError, ValueError):
            pass
        story_identity = str(payload.get("story_identity") or "").strip()
        update_chain_identity = str(payload.get("update_chain_identity") or "").strip()
        if story_identity:
            story_ids.add(story_identity)
        if update_chain_identity:
            chain_ids.add(update_chain_identity)
    return {
        "confirmed_canonical_count": len(object_urls),
        "story_identities": sorted(story_ids),
        "update_chain_identities": sorted(chain_ids),
        "canonical_url_hashes": sorted(
            hashlib.sha256(value.encode("utf-8")).hexdigest() for value in object_urls
        ),
        "state": "READ_ONLY_DURABLE_RECONCILED_SUBSTACK_MEMORY",
    }


def _active_learning_policy_from_store(connection: sqlite3.Connection) -> dict[str, Any]:
    from live_contentops.daily_app_performance_v1 import (
        BOOTSTRAP_POLICY_VERSION,
        QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
        _bootstrap_policy_payload,
        _normalized_policy_payload,
    )

    if "learning_policy_versions" not in _table_names(connection):
        payload = _bootstrap_policy_payload()
        return {
            "policy_version": BOOTSTRAP_POLICY_VERSION,
            "decision": "CONFIGURED_DEFAULT",
            "sample_count": 0,
            "confidence": 0.0,
            "formula_version": QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
            "timing": payload["timing"],
            "content": payload["content"],
            "seo": payload["seo"],
            "package": payload["package"],
            "grants_factual_or_numeric_authority": False,
            "grants_publication_authority": False,
        }
    row = connection.execute(
        "SELECT * FROM learning_policy_versions WHERE status='ACTIVE' "
        "ORDER BY created_at_utc DESC,policy_version DESC LIMIT 1"
    ).fetchone()
    if row is None:
        payload = _bootstrap_policy_payload()
        return {
            "policy_version": BOOTSTRAP_POLICY_VERSION,
            "decision": "CONFIGURED_DEFAULT",
            "sample_count": 0,
            "confidence": 0.0,
            "formula_version": QUALIFIED_ENGAGEMENT_FORMULA_VERSION,
            "timing": payload["timing"],
            "content": payload["content"],
            "seo": payload["seo"],
            "package": payload["package"],
            "grants_factual_or_numeric_authority": False,
            "grants_publication_authority": False,
        }
    try:
        payload = _normalized_policy_payload(
            dict(json.loads(str(row["policy_payload_json"] or "{}")))
        )
    except (TypeError, ValueError):
        payload = _bootstrap_policy_payload()
    return {
        "policy_version": str(row["policy_version"]),
        "parent_policy_version": row["parent_policy_version"],
        "decision": str(row["decision"]),
        "decision_reason": str(row["decision_reason"]),
        "sample_count": int(row["sample_count"]),
        "confidence": float(row["confidence"]),
        "formula_version": str(row["formula_version"]),
        "timing": dict(payload.get("timing") or {}),
        "content": dict(payload.get("content") or {}),
        "seo": dict(payload.get("seo") or {}),
        "package": dict(payload.get("package") or {}),
        "grants_factual_or_numeric_authority": False,
        "grants_publication_authority": False,
    }


def load_terminal_editorial_continuity(
    *,
    store_path: str | Path = CANONICAL_PRODUCTION_STORE_PATH,
    output_root: str | Path = CANONICAL_PRODUCTION_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Reconstruct cutoff/evaluated/publication memory without modifying the canonical store."""
    store = Path(store_path)
    outputs = Path(output_root)
    base: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "store_path": str(store.resolve()),
        "output_root": str(outputs.resolve()),
        "store_open_mode": "SQLITE_URI_MODE_RO_QUERY_ONLY",
        "database_writes_performed": False,
        "filesystem_writes_performed": False,
        "parallel_state_authority_created": False,
    }
    if not store.is_file():
        from live_contentops.daily_app_performance_v1 import (
            BOOTSTRAP_POLICY_VERSION,
            _bootstrap_policy_payload,
        )
        bootstrap_payload = _bootstrap_policy_payload()
        result = {
            **base,
            "state": "CANONICAL_STORE_MISSING",
            "last_terminal_cutoff_utc": None,
            "terminal_window_id": None,
            "terminal_records": [],
            "evaluated_headline_ids": [],
            "evaluated_update_chain_identities": [],
            "published_memory": {
                "confirmed_canonical_count": 0,
                "story_identities": [],
                "update_chain_identities": [],
                "state": "CANONICAL_STORE_MISSING",
            },
            "active_learning_policy": {
                "policy_version": BOOTSTRAP_POLICY_VERSION,
                "decision": "CONFIGURED_DEFAULT",
                "sample_count": 0,
                "confidence": 0.0,
                "timing": bootstrap_payload["timing"],
                "content": bootstrap_payload["content"],
                "seo": bootstrap_payload["seo"],
                "package": bootstrap_payload["package"],
                "grants_factual_or_numeric_authority": False,
                "grants_publication_authority": False,
            },
            "prior_cc_catalog_fingerprint": None,
            "material_event_priority": {
                "priority_ids": [], "headline_ids": [], "update_chain_identities": [],
                "priority_count": 0, "grants_evidence_or_publication_authority": False,
            },
        }
        result["continuity_logical_hash"] = _logical_hash(result)
        return result

    with _read_only_store(store) as connection:
        tables = _table_names(connection)
        if "work_items" not in tables:
            raise ValueError("desktop_continuity_work_items_table_missing")
        placeholders = ",".join("?" for _ in TERMINAL_EDITORIAL_STATES)
        rows = connection.execute(
            "SELECT work_item_id,current_state,updated_at FROM work_items "
            "WHERE target_surface IN "
            "('daily_app_editorial_window','daily_app_material_event_window') "
            f"AND current_state IN ({placeholders}) "
            "ORDER BY updated_at DESC,work_item_id DESC",
            tuple(sorted(TERMINAL_EDITORIAL_STATES)),
        ).fetchall()
        published_memory = _published_memory_from_store(connection)
        active_learning_policy = _active_learning_policy_from_store(connection)
        pending_material_rows = connection.execute(
            "SELECT work_item_id FROM work_items "
            "WHERE target_surface='daily_app_material_event_window' "
            "AND current_state='DISCOVERED' ORDER BY work_item_id"
        ).fetchall()

    material_priorities: list[dict[str, Any]] = []
    for pending in pending_material_rows:
        priority = _read_json_object(
            outputs / str(pending["work_item_id"]) / "material_event_priority_v1.json"
        )
        if priority:
            material_priorities.append(priority)
    material_event_priority = {
        "priority_ids": sorted({str(row.get("priority_id") or "") for row in material_priorities if str(row.get("priority_id") or "")}),
        "headline_ids": sorted({str(value) for row in material_priorities for value in (row.get("headline_ids") or []) if str(value)}),
        "update_chain_identities": sorted({str(value) for row in material_priorities for value in (row.get("update_chain_identities") or []) if str(value)}),
        "priority_count": len(material_priorities),
        "grants_evidence_or_publication_authority": False,
    }

    evaluated_ids: set[str] = set()
    evaluated_chains: set[str] = set()
    terminal_records: list[dict[str, Any]] = []
    published_story_ids = set(published_memory.get("story_identities") or [])
    published_chain_ids = set(published_memory.get("update_chain_identities") or [])
    for row in rows:
        window_id = str(row["work_item_id"])
        output_dir = outputs / window_id
        intake = _read_json_object(output_dir / "rolling_x_intake_v1.json")
        evidence = _read_json_object(
            output_dir / "rolling_x_newsroom_cycle_evidence_v1.json"
        )
        if not intake or not evidence:
            continue
        cutoff = _parse_utc(intake.get("cutoff_time_utc"))
        if cutoff is None:
            continue
        assignment = _read_json_object(output_dir / "rolling_x_assignment_v1.json") or {}
        prepared = _read_json_object(
            output_dir / "rolling_x_prepared_candidate_state_v1.json"
        ) or {}
        clusters_by_id = {
            str(cluster.get("cluster_id") or ""): dict(cluster)
            for cluster in assignment.get("ranked_clusters") or []
            if isinstance(cluster, Mapping) and str(cluster.get("cluster_id") or "")
        }
        attempted_cluster_ids = {
            str(attempt.get("cluster_id") or "")
            for attempt in (
                *((evidence.get("candidate_walk") or {}).get("candidate_attempts") or []),
                *((evidence.get("ranked_viability") or {}).get("rank_attempts") or []),
            )
            if isinstance(attempt, Mapping) and str(attempt.get("cluster_id") or "")
        }
        if attempted_cluster_ids:
            evaluated_clusters = [
                clusters_by_id[cluster_id]
                for cluster_id in sorted(attempted_cluster_ids)
                if cluster_id in clusters_by_id
            ]
            headline_ids = {
                str(value)
                for cluster in evaluated_clusters
                for value in cluster.get("headline_ids") or []
                if str(value)
            }
            evaluated_identity_source = "CANDIDATE_WALK_ATTEMPTS"
        elif prepared:
            headline_ids = {
                str(value)
                for value in (
                    (prepared.get("prepared_frontier") or {}).get(
                        "selected_headline_ids"
                    )
                    or (prepared.get("prepared_input") or {}).get(
                        "unique_headline_ids"
                    )
                    or []
                )
                if str(value)
            }
            evaluated_clusters = [
                cluster for cluster in clusters_by_id.values()
                if set(str(value) for value in cluster.get("headline_ids") or []).intersection(
                    headline_ids
                )
            ]
            evaluated_identity_source = "PREPARED_FRONTIER"
        else:
            # Legacy cycles may lack candidate-walk telemetry. The ranked assignment is the
            # narrowest durable proof of consideration; the full intake universe is not.
            evaluated_clusters = list(clusters_by_id.values())
            headline_ids = {
                str(value)
                for cluster in evaluated_clusters
                for value in cluster.get("headline_ids") or []
                if str(value)
            }
            evaluated_identity_source = "LEGACY_RANKED_ASSIGNMENT"
        evaluated_ids.update(headline_ids)
        for cluster in evaluated_clusters:
            if not isinstance(cluster, Mapping):
                continue
            chain = str(
                cluster.get("update_chain_identity") or cluster.get("cluster_id") or ""
            ).strip()
            if chain:
                evaluated_chains.add(chain)
        memory_proof = _read_json_object(
            output_dir / "published_memory_cycle_proof_v1.json"
        ) or {}
        observed = memory_proof.get("canonical_article_observed_after_lifecycle") or {}
        if isinstance(observed, Mapping):
            story_identity = str(observed.get("story_identity") or "").strip()
            update_chain_identity = str(
                observed.get("update_chain_identity") or ""
            ).strip()
            if story_identity:
                published_story_ids.add(story_identity)
            if update_chain_identity:
                published_chain_ids.add(update_chain_identity)
        portfolio = _read_json_object(output_dir / "editorial_portfolio_context_v1.json") or {}
        cc_model = portfolio.get("capital_chronicle_read_model") or {}
        terminal_records.append({
            "window_id": window_id,
            "terminal_state": str(row["current_state"]),
            "updated_at_utc": str(row["updated_at"]),
            "cutoff_utc": _iso_utc(cutoff),
            "classification": evidence.get("classification"),
            "evaluated_headline_count": len(headline_ids),
            "evaluated_identity_source": evaluated_identity_source,
            "cc_catalog_fingerprint": cc_model.get("catalog_fingerprint")
            if isinstance(cc_model, Mapping) else None,
        })
    terminal_records.sort(
        key=lambda value: (
            _parse_utc(value.get("cutoff_utc")) or datetime.min.replace(tzinfo=timezone.utc),
            str(value.get("window_id") or ""),
        ),
        reverse=True,
    )
    latest = terminal_records[0] if terminal_records else None
    published_memory = {
        **published_memory,
        "story_identities": sorted(published_story_ids),
        "update_chain_identities": sorted(published_chain_ids),
    }
    result = {
        **base,
        "state": "READY" if latest else "NO_PRIOR_TERMINAL_EDITORIAL_WINDOW",
        "last_terminal_cutoff_utc": latest.get("cutoff_utc") if latest else None,
        "terminal_window_id": latest.get("window_id") if latest else None,
        "terminal_state": latest.get("terminal_state") if latest else None,
        "terminal_classification": latest.get("classification") if latest else None,
        "terminal_record_count": len(terminal_records),
        "terminal_records": terminal_records,
        "evaluated_headline_ids": sorted(evaluated_ids),
        "evaluated_headline_count": len(evaluated_ids),
        "evaluated_update_chain_identities": sorted(evaluated_chains),
        "published_memory": published_memory,
        "active_learning_policy": active_learning_policy,
        "prior_cc_catalog_fingerprint": latest.get("cc_catalog_fingerprint")
        if latest else None,
        "material_event_priority": material_event_priority,
    }
    result["continuity_logical_hash"] = _logical_hash(result)
    return result


def _cluster_relationship(cluster: Mapping[str, Any]) -> str:
    for container in (
        cluster.get("update_chain"),
        cluster.get("duplicate_update_chain"),
    ):
        if isinstance(container, Mapping) and container.get("relationship"):
            return str(container["relationship"]).casefold()
    return str(cluster.get("relationship") or "distinct").casefold()


def classify_desktop_candidate_universe(
    *,
    current_headlines: Sequence[Mapping[str, Any]],
    current_clusters: Sequence[Mapping[str, Any]],
    continuity: Mapping[str, Any],
) -> dict[str, Any]:
    """Include unseen identity or governed material delta; hold unchanged/published repeats."""
    rows_by_id: dict[str, dict[str, Any]] = {}
    duplicate_current_ids: set[str] = set()
    for value in current_headlines:
        headline_id = str(value.get("headline_id") or "")
        if not headline_id:
            raise ValueError("desktop_candidate_headline_id_missing")
        if headline_id in rows_by_id:
            duplicate_current_ids.add(headline_id)
            continue
        rows_by_id[headline_id] = dict(value)
    evaluated_ids = {
        str(value) for value in (continuity.get("evaluated_headline_ids") or [])
    }
    published = continuity.get("published_memory") or {}
    published_story_ids = {
        str(value) for value in (published.get("story_identities") or [])
    }
    published_chain_ids = {
        str(value) for value in (published.get("update_chain_identities") or [])
    }
    last_cutoff = _parse_utc(continuity.get("last_terminal_cutoff_utc"))
    priority = dict(continuity.get("material_event_priority") or {})
    priority_headline_ids = {str(value) for value in (priority.get("headline_ids") or [])}
    priority_update_chains = {
        str(value) for value in (priority.get("update_chain_identities") or [])
    }
    included: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    assigned_ids: set[str] = set()
    for position, value in enumerate(current_clusters, start=1):
        cluster = dict(value)
        cluster_id = str(cluster.get("cluster_id") or f"desktop-cluster-{position}")
        headline_ids = [str(item) for item in (cluster.get("headline_ids") or [])]
        if not headline_ids or any(item not in rows_by_id for item in headline_ids):
            raise ValueError("desktop_candidate_cluster_binding_invalid")
        if assigned_ids.intersection(headline_ids):
            raise ValueError("desktop_candidate_headline_assigned_twice")
        assigned_ids.update(headline_ids)
        relationship = _cluster_relationship(cluster)
        material_update = relationship in MATERIAL_RELATIONSHIPS
        unseen_ids = sorted(set(headline_ids) - evaluated_ids)
        chain_identity = str(
            cluster.get("update_chain_identity") or cluster_id
        )
        published_match = (
            cluster_id in published_story_ids or chain_identity in published_chain_ids
        )
        material_priority_match = bool(
            set(headline_ids).intersection(priority_headline_ids)
            or chain_identity in priority_update_chains
        )
        source_times = [
            _parse_utc(rows_by_id[item].get("source_timestamp_utc"))
            for item in headline_ids
        ]
        late_unseen = sorted(
            item for item in unseen_ids
            if last_cutoff is not None
            and (_parse_utc(rows_by_id[item].get("source_timestamp_utc")) or last_cutoff)
            <= last_cutoff
        )
        record = {
            "cluster_id": cluster_id,
            "update_chain_identity": chain_identity,
            "relationship": relationship,
            "headline_ids": headline_ids,
            "unseen_headline_ids": unseen_ids,
            "late_arriving_unseen_headline_ids": late_unseen,
            "published_memory_match": published_match,
            "material_event_priority_match": material_priority_match,
            "material_event_priority_ids": list(priority.get("priority_ids") or [])
            if material_priority_match else [],
            "source_timestamp_max_utc": _iso_utc(max(
                value for value in source_times if value is not None
            )) if any(value is not None for value in source_times) else None,
            "rank": int(cluster.get("rank") or position),
            "entities_topics": list(cluster.get("entities_topics") or []),
        }
        if published_match and not material_update:
            record["decision"] = "EXCLUDE_PUBLISHED_WITHOUT_MATERIAL_DELTA"
            excluded.append(record)
        elif material_update:
            record["decision"] = "INCLUDE_MATERIAL_UPDATE_CHAIN"
            included.append(record)
        elif material_priority_match:
            record["decision"] = "INCLUDE_MATERIAL_EVENT_PRIORITY"
            included.append(record)
        elif unseen_ids:
            record["decision"] = "INCLUDE_UNSEEN_HEADLINE_IDENTITY"
            included.append(record)
        else:
            record["decision"] = "EXCLUDE_UNCHANGED_PREVIOUSLY_EVALUATED"
            excluded.append(record)
    included.sort(key=lambda value: (
        0 if value.get("material_event_priority_match") else 1,
        0 if value["decision"] == "INCLUDE_MATERIAL_UPDATE_CHAIN" else 1,
        int(value["rank"]),
        str(value["cluster_id"]),
    ))
    result = {
        "schema_version": "contentops.codex_desktop_candidate_universe.v1",
        "current_unique_headline_count": len(rows_by_id),
        "current_duplicate_headline_ids": sorted(duplicate_current_ids),
        "evaluated_headline_count": len(evaluated_ids),
        "included_clusters": included,
        "excluded_clusters": excluded,
        "included_cluster_count": len(included),
        "material_update_cluster_count": sum(
            row["decision"] == "INCLUDE_MATERIAL_UPDATE_CHAIN" for row in included
        ),
        "unseen_headline_ids": sorted({
            item for row in included for item in row["unseen_headline_ids"]
        }),
        "late_arriving_unseen_headline_ids": sorted({
            item for row in included for item in row["late_arriving_unseen_headline_ids"]
        }),
        "unchanged_or_published_excluded_count": len(excluded),
        "timestamp_only_filter_used": False,
        "material_event_priority": priority,
        "material_event_priority_changes_truth_or_publication_authority": False,
        "publication_authority_granted": False,
    }
    result["candidate_universe_logical_hash"] = _logical_hash(result)
    return result


def _executed_editorial_window_ids(
    store_path: Path,
    opportunity_ids: Sequence[str],
    *,
    executed_states: frozenset[str],
) -> set[str]:
    identifiers = sorted({str(value) for value in opportunity_ids if str(value)})
    if not identifiers or not store_path.exists():
        return set()
    try:
        with _read_only_store(store_path) as connection:
            if "work_items" not in _table_names(connection):
                return set()
            placeholders = ",".join("?" for _value in identifiers)
            rows = connection.execute(
                f"SELECT work_item_id, current_state FROM work_items "
                f"WHERE work_item_id IN ({placeholders})",
                identifiers,
            ).fetchall()
    except (OSError, sqlite3.Error):
        return set()
    return {
        str(row["work_item_id"])
        for row in rows
        if str(row["current_state"] or "") in executed_states
    }


def _continuous_prepared_checkpoint(
    *,
    output_root: Path,
    checkpoint_name: str,
) -> tuple[Path, dict[str, Any] | None]:
    path = output_root / "_continuous_newsroom" / checkpoint_name
    return path, _read_json_object(path)


def _checkpoint_matches_live_authority(
    state: Mapping[str, Any],
    *,
    current_input: Mapping[str, Any],
    continuity: Mapping[str, Any],
    opportunities: Sequence[Mapping[str, Any]],
) -> bool:
    frontier = state.get("prepared_frontier") or {}
    binding = state.get("continuity_binding") or {}
    selected_ids = {
        str(value) for value in frontier.get("selected_headline_ids") or [] if str(value)
    }
    current_rows = {
        str(row.get("headline_id") or ""): {
            key: value for key, value in row.items() if key != "source_locator"
        }
        for row in current_input.get("headlines") or []
        if isinstance(row, Mapping) and str(row.get("headline_id") or "")
    }
    prepared_rows = {
        str(row.get("headline_id") or ""): {
            key: value for key, value in row.items() if key != "source_locator"
        }
        for row in (state.get("prepared_input") or {}).get("headlines") or []
        if isinstance(row, Mapping) and str(row.get("headline_id") or "")
    }
    expected_binding = prepared_candidate_continuity_binding(
        continuity=continuity,
        evaluated_headline_ids=continuity.get("evaluated_headline_ids") or [],
        reentry_headline_ids=(
            continuity.get("material_event_priority") or {}
        ).get("headline_ids") or [],
    )
    expected_target = dict(opportunities[0]) if opportunities else None
    target = frontier.get("target_editorial_opportunity")
    return bool(
        frontier.get("opportunity_schedule_derived_from_policy") is True
        and target == expected_target
        and set(prepared_rows) == selected_ids
        and all(current_rows.get(headline_id) == prepared_rows[headline_id] for headline_id in selected_ids)
        and binding == expected_binding
    )


def build_live_zero_write_rehearsal(
    *,
    cutoff_utc: datetime | str | None = None,
    store_path: str | Path = CANONICAL_PRODUCTION_STORE_PATH,
    output_root: str | Path = CANONICAL_PRODUCTION_OUTPUT_ROOT,
    sidecar_glob: str = canonical_headline_sidecar_glob(),
    cc_root: str | Path = DEFAULT_CC_ROOT,
    current_clusters: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build one real-state, bounded, read-only opportunity rehearsal; never execute a write."""
    if cutoff_utc is None:
        cutoff = datetime.now(timezone.utc)
    elif isinstance(cutoff_utc, datetime):
        cutoff = cutoff_utc
    else:
        cutoff = _parse_utc(cutoff_utc)
        if cutoff is None:
            raise ValueError("desktop_rehearsal_cutoff_invalid")
    if cutoff.tzinfo is None:
        cutoff = cutoff.replace(tzinfo=timezone.utc)
    cutoff = cutoff.astimezone(timezone.utc)
    continuity = load_terminal_editorial_continuity(
        store_path=store_path, output_root=output_root
    )
    current_input = load_rolling_x_headline_sidecars(
        cutoff_utc=cutoff,
        sidecar_glob=sidecar_glob,
        window_hours=24.0,
    )
    headlines = list(current_input.get("headlines") or [])
    if current_clusters is None:
        ordered = sorted(
            headlines,
            key=lambda row: (
                str(row.get("source_timestamp_utc") or ""),
                str(row.get("headline_id") or ""),
            ),
            reverse=True,
        )
        clusters = [
            {
                "cluster_id": "desktop-unclustered-" + str(row["headline_id"]),
                "rank": index,
                "headline_ids": [str(row["headline_id"])],
                "relationship": "distinct",
                "entities_topics": [],
            }
            for index, row in enumerate(ordered, start=1)
        ]
    else:
        clusters = [dict(value) for value in current_clusters]
    universe = classify_desktop_candidate_universe(
        current_headlines=headlines,
        current_clusters=clusters,
        continuity=continuity,
    )
    material_reentry_ids = sorted({
        str(headline_id)
        for row in universe.get("included_clusters") or []
        if str(row.get("relationship") or "").casefold() in MATERIAL_RELATIONSHIPS
        for headline_id in row.get("headline_ids") or []
        if str(headline_id)
    })
    excluded_ids = {
        str(headline_id)
        for row in universe.get("excluded_clusters") or []
        for headline_id in row.get("headline_ids") or []
        if str(headline_id)
    }
    continuity_evaluated_ids = {
        str(value) for value in continuity.get("evaluated_headline_ids") or [] if str(value)
    }
    from live_contentops.daily_app_supervisor_v1 import (
        PREPARED_CANDIDATE_CHECKPOINT_NAME,
        WINDOW_EXECUTED_STATES,
        build_bootstrap_editorial_window_policy,
        owner_locked_editorial_opportunities,
    )

    evaluated_ids = sorted(continuity_evaluated_ids.union(excluded_ids))
    priority_reentry_ids = {
        str(value)
        for value in (continuity.get("material_event_priority") or {}).get("headline_ids") or []
        if str(value)
    }
    reentry_ids = sorted(set(material_reentry_ids).union(priority_reentry_ids))
    policy = build_bootstrap_editorial_window_policy(
        effective_at_utc=_iso_utc(cutoff)
    )
    opportunities = owner_locked_editorial_opportunities(
        policy,
        reference_utc=cutoff,
        through_utc=cutoff + timedelta(
            hours=float(current_input.get("window_hours") or 24.0)
        ),
        capacity=PREPARED_CANDIDATE_LIMIT,
    )
    executed_ids = _executed_editorial_window_ids(
        Path(store_path),
        [str(row.get("opportunity_id") or "") for row in opportunities],
        executed_states=WINDOW_EXECUTED_STATES,
    )
    opportunities = [
        row for row in opportunities
        if str(row.get("opportunity_id") or "") not in executed_ids
    ]
    checkpoint_path, prior_prepared_state = _continuous_prepared_checkpoint(
        output_root=Path(output_root),
        checkpoint_name=PREPARED_CANDIDATE_CHECKPOINT_NAME,
    )
    prepared_preview: dict[str, Any] | None = None
    prepared_state_source = "REBUILT_FROM_CANONICAL_FRONTIER_INPUTS"
    if prior_prepared_state is not None:
        try:
            validated = validate_prepared_rolling_x_candidate_state(
                prior_prepared_state,
                publication_cutoff_utc=cutoff,
            )
            if _checkpoint_matches_live_authority(
                validated,
                current_input=current_input,
                continuity=continuity,
                opportunities=opportunities,
            ):
                prepared_preview = validated
                prepared_state_source = "REUSED_VALID_CONTINUOUS_CHECKPOINT"
        except (TypeError, ValueError):
            prepared_preview = None
    if prepared_preview is None:
        prepared_preview = build_prepared_rolling_x_candidate_state(
            rolling_input=current_input,
            prepared_at_utc=cutoff,
            evaluated_headline_ids=evaluated_ids,
            reentry_headline_ids=reentry_ids,
            editorial_opportunities=opportunities,
            prior_prepared_state=prior_prepared_state,
            autonomous_source_discovery_available=True,
            continuity_binding=prepared_candidate_continuity_binding(
                continuity=continuity,
                evaluated_headline_ids=evaluated_ids,
                reentry_headline_ids=reentry_ids,
            ),
        )
    catalog = discover_cc_data_estate(cc_root=cc_root, use_cache=False)
    governed = inspect_governed_cc_surfaces(catalog)
    selected_frontier_ids = {
        str(value)
        for value in (prepared_preview.get("prepared_frontier") or {}).get(
            "selected_headline_ids"
        ) or []
        if str(value)
    }
    selected_assignment = next(
        iter((prepared_preview.get("assignment") or {}).get("ranked_clusters") or []),
        None,
    )
    selected_headline_ids = [
        str(value)
        for value in (selected_assignment or {}).get("headline_ids") or []
        if str(value) in selected_frontier_ids
    ]
    selected = (
        {
            "cluster_id": (selected_assignment or {}).get("cluster_id"),
            "headline_ids": selected_headline_ids,
            "relationship": "prepared_frontier",
        }
        if selected_assignment and selected_headline_ids
        else None
    )
    raw_selected = next(
        (
            row for row in universe.get("included_clusters") or []
            if selected_headline_ids
            and selected_headline_ids[0] in {
                str(value) for value in row.get("headline_ids") or []
            }
        ),
        None,
    )
    entities: list[str] = []
    if selected:
        entities = [str(value) for value in (raw_selected or {}).get("entities_topics") or []]
        if not entities:
            selected_id = next(iter(selected.get("headline_ids") or []), None)
            selected_row = next(
                (row for row in headlines if row.get("headline_id") == selected_id), {}
            )
            headline_text = str(
                (selected_row.get("external_content") or {}).get("headline_text") or ""
            ).strip()
            if headline_text:
                entities = [headline_text]
    cc_context = query_story_scoped_cc_context(catalog, entities) if entities else {
        "schema_version": "contentops.story_scoped_cc_context.v2",
        "queried_entities": [],
        "matches": [],
        "catalog_fingerprint": catalog.get("catalog_fingerprint"),
        "grants_factual_or_numeric_authority": False,
        "mutated_upstream": False,
    }
    prior_fingerprint = continuity.get("prior_cc_catalog_fingerprint")
    current_fingerprint = catalog.get("catalog_fingerprint")
    result = {
        "schema_version": REHEARSAL_SCHEMA_VERSION,
        "cutoff_utc": _iso_utc(cutoff),
        "continuity": continuity,
        "current_intake": {
            "canonical_input_hash": current_input.get("canonical_input_hash"),
            "headline_count": int((current_input.get("counts") or {}).get("accepted") or 0),
            "deduplicated_input_count": int(
                (current_input.get("counts") or {}).get("duplicates") or 0
            ),
        },
        "candidate_universe": universe,
        "prepared_candidate_state_preview": prepared_preview,
        "prepared_candidate_state_source": prepared_state_source,
        "prepared_candidate_checkpoint_path": str(checkpoint_path.resolve()),
        "prepared_checkpoint_written_by_rehearsal": False,
        "prepared_candidate_count": int(
            prepared_preview.get("prepared_candidate_count") or 0
        ),
        "deferred_candidate_count": int(
            (prepared_preview.get("prepared_frontier") or {}).get(
                "deferred_identity_count"
            )
            or 0
        ),
        "prepared_frontier_is_continuity_bound": True,
        "active_learning_policy": continuity.get("active_learning_policy"),
        "material_event_priority": continuity.get("material_event_priority"),
        "material_event_priority_consumed_by_briefing": bool(
            (continuity.get("material_event_priority") or {}).get("priority_count")
        ),
        "learning_policy_consumed_by_next_opportunity": True,
        "learning_policy_grants_factual_or_numeric_authority": False,
        "candidate_or_abstention": (
            {
                "decision": "CANDIDATE_FOR_DESKTOP_EDITORIAL_JUDGMENT",
                "cluster_id": selected.get("cluster_id"),
                "headline_ids": selected.get("headline_ids"),
                "relationship": selected.get("relationship"),
                "prepared_frontier_bound": True,
            }
            if selected else {"decision": "ABSTAIN_NO_CURRENT_UNSEEN_OR_MATERIAL_UPDATE"}
        ),
        "capital_chronicle": {
            "root": str(Path(cc_root).resolve()),
            "store_count_total": catalog.get("store_count_total"),
            "store_count_discovered": catalog.get("store_count_discovered"),
            "discovery_complete": catalog.get("discovery_complete"),
            "connection_mode": catalog.get("connection_mode"),
            "catalog_fingerprint": current_fingerprint,
            "prior_terminal_catalog_fingerprint": prior_fingerprint,
            "catalog_changed_since_prior_terminal": (
                None if not prior_fingerprint else prior_fingerprint != current_fingerprint
            ),
            "cache_state": (catalog.get("cache") or {}).get("state"),
            "governed_surfaces": governed,
            "story_scoped_context": cc_context,
            "arbitrary_database_context_grants_authority": False,
        },
        "next_terminal_cutoff_constructible": True,
        "next_terminal_cutoff_utc": _iso_utc(cutoff),
        "database_writes_performed": False,
        "filesystem_writes_performed": False,
        "provider_or_model_calls": 0,
        "model_calls": 0,
        "provider_calls": 0,
        "public_requests": 0,
        "public_writes": 0,
        "unknown_write_detected": False,
        "publication_coordinator_sole_public_writer_unchanged": True,
        "v2_mutations": 0,
    }
    result["rehearsal_logical_hash"] = _logical_hash(result)
    return result
