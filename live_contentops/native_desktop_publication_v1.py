"""Native reviewed-owner composition over the existing handoff/coordinator/Neo protocol.

Preparation and projection never probe or dispatch. Registered scheduled bindings and
explicitly activated live owner operations use the same coordinator. Manual proof stays isolated.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    canonical_bytes,
    sha256_of,
)
from live_contentops.native_desktop_workspace_v1 import resolve_workspace_path
from live_contentops.native_desktop_editorial_v1 import (
    prepare_reviewed_handoff,
    validated_native_review,
)
from live_contentops.native_neo_executor_v1 import (
    NativeNeoInputRequired,
    bind_native_neo_coordinator,
)
from live_contentops.v1_simple_publication_handoff_v1 import SimplePublicationHandoffV1

DESTINATION = "internal:native-publication-binding"
ARTIFACTS = (
    "article_manifest_v1.json",
    "qualified_article_record_v1.json",
    "native_derivative_previews_v1.json",
    "publication_lifecycle_plan_v1.json",
    "run_context_v1.json",
)


def _prepared_packet(store, binding):
    result, _, review = validated_native_review(store, run_id=binding["run_id"])
    prepared = [
        json.loads(r["payload"])
        for r in store.list_outbox_messages()
        if r["destination"] == "internal:native-prepared-handoff"
        and json.loads(r["payload"]).get("run_id") == binding["run_id"]
    ]
    if not prepared or prepared[-1]["review_id"] != review["review_id"]:
        raise ValueError("CURRENT_REVIEWED_HANDOFF_REQUIRED")
    packet = prepared[-1]
    from live_contentops.native_desktop_editorial_v1 import native_review_revision
    base = resolve_workspace_path(binding["output_dir"]) / "reviewed-handoff"
    root = resolve_workspace_path(packet["output_dir"])
    if root not in {base, base / native_review_revision(result)}:
        raise ValueError("REVIEWED_HANDOFF_PATH_CHANGED")
    if not all((root / name).is_file() for name in ARTIFACTS):
        raise ValueError("REVIEWED_HANDOFF_ARTIFACT_MISSING")
    plan = SimplePublicationHandoffV1(store=store, coordinator=None).ensure_plan(
        slot_id=binding["run_id"], slot_output_dir=root
    )
    if (
        plan["plan_hash"] != packet["plan_hash"]
        or plan["article_identity"] != result["article_identity"]
    ):
        raise ValueError("REVIEWED_HANDOFF_PLAN_CHANGED")
    if json.loads((root / ARTIFACTS[0]).read_bytes()) != result["article"]:
        raise ValueError("REVIEWED_HANDOFF_COPY_CHANGED")
    return (
        {
            "schema_version": "contentops.native_publication_binding.v1",
            "run_id": binding["run_id"],
            "work_item_id": binding["run_id"],
            "article_identity": result["article_identity"],
            "review_id": review["review_id"],
            "review_notes_sha256": sha256_of(json.loads(review["notes"])),
            "prepared_handoff_sha256": sha256_of(packet),
            "plan_hash": plan["plan_hash"],
            "binding_sha256": sha256_of(binding),
            "accepted_evidence_sha256": plan["accepted_evidence_sha256"],
            "native_result_sha256": sha256_of(result),
            "artifact_sha256": {
                name: sha256((root / name).read_bytes()).hexdigest()
                for name in ARTIFACTS
            },
            "media_sha256": {
                a["asset_id"]: a["sha256"] for a in result.get("media_assets", [])
            },
            "publication_authority": False,
        },
        plan,
        root,
    )


def prepare_native_publication(store, binding):
    """Seal the exact reviewed packet in the same outbox; no publisher/readiness call."""
    from live_contentops.native_desktop_editorial_v1 import validated_native_review, validate_release_media
    result, _, _ = validated_native_review(store, run_id=binding["run_id"])
    validate_release_media(result)
    prepare_reviewed_handoff(
        store, run_id=binding["run_id"], output_dir=binding["output_dir"]
    )
    value, _, _ = _prepared_packet(store, binding)
    key = "native-publication-binding-" + sha256_of([binding["run_id"], value])
    store.register_outbox_message(
        message_id=key,
        work_item_id="cc-opportunity-" + sha256_of(binding["run_id"]),
        destination=DESTINATION,
        payload=canonical_bytes(value).decode(),
        status="EDITORIAL_INTERNAL",
    )
    return {
        "classification": "NATIVE_PUBLICATION_PREPARED_NO_DISPATCH",
        **value,
        "next_operation": "publication-status",
        "public_write_performed": False,
    }


def live_publication_policy(rollout, *, cutoff_utc=None):
    """The applied operator grant covers fresh operations, never retained proof examples."""
    authority = (rollout or {}).get("live_authority") or {}
    if (not rollout or rollout.get("schema_version") != "contentops.native_desktop_rollout.v1"
            or rollout.get("public_write_authority") is not True
            or authority.get("scope") != "V1_NATIVE_PUBLICATION"
            or not all(authority.get(k) for k in ("thread_id", "turn_id", "message_id", "not_before_utc"))):
        raise ValueError("EXPLICIT_OWNER_LIVE_ACTIVATION_REQUIRED")
    floor = datetime.fromisoformat(authority["not_before_utc"].replace("Z", "+00:00"))
    if floor.tzinfo is None or floor > datetime.now(timezone.utc):
        raise ValueError("OWNER_LIVE_ACTIVATION_CLOCK_INVALID")
    if cutoff_utc is not None:
        cutoff = datetime.fromisoformat(cutoff_utc.replace("Z", "+00:00"))
        if cutoff.tzinfo is None or cutoff < floor:
            raise ValueError("PRE_ACTIVATION_ARTICLE_REMAINS_PRIVATE")
    return authority


def scheduled_publication_authority(store, binding, rollout):
    """Registered scheduled or explicitly granted live-owner provenance, never manual proof."""
    from live_contentops.llm_operator_control_v1 import (
        assert_llm_operator_execution_enabled,
    )
    from live_contentops.daily_app_supervisor_v1 import (
        NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID,
    )
    from live_contentops.v1_simple_gemini_scheduler_v1 import simple_gemini_slot_id

    if binding.get("owner_manual_validation") is not False:
        raise ValueError("OWNER_MANUAL_PUBLICATION_NOT_AUTHORIZED")
    if not rollout or rollout.get("public_write_authority") is not True:
        raise ValueError("SEPARATE_OWNER_PUBLICATION_ACTIVATION_REQUIRED")
    registered = store.get_outbox_message(
        "native-operation-binding-" + sha256_of(binding["run_id"])
    )
    if not registered or json.loads(registered["payload"]) != binding:
        raise ValueError("EXACT_REGISTERED_OPERATION_BINDING_REQUIRED")
    if binding.get("owner_manual_live"):
        authority = live_publication_policy(rollout, cutoff_utc=binding["cutoff_utc"])
        if (binding.get("live_authority_sha256") != sha256_of(authority)
                or resolve_workspace_path(binding["store_path"]) != resolve_workspace_path(rollout["store_path"])
                or resolve_workspace_path(binding["published_memory_store"]) != resolve_workspace_path(rollout["store_path"])
                or resolve_workspace_path(binding["published_memory_output_root"]) != resolve_workspace_path(rollout["published_output_root"])
                or resolve_workspace_path(binding["output_dir"]) !=
                    resolve_workspace_path(rollout["editorial_output_root"]) / "owner-manual" / binding["run_id"]
                or "automation_id" in binding or "window_id" in binding):
            raise ValueError("EXACT_OWNER_LIVE_PUBLICATION_BINDING_REQUIRED")
        assert_llm_operator_execution_enabled()
        if store.get_operating_control()["operating_mode"] != "AUTONOMOUS_DEFAULT":
            raise ValueError("PUBLICATION_OPERATING_MODE_BLOCKED")
        return
    if rollout.get("live_authority"):
        live_publication_policy(rollout, cutoff_utc=binding["cutoff_utc"])
    if (
        not rollout
        or rollout.get("schema_version") != "contentops.native_desktop_rollout.v1"
        or binding.get("automation_id") not in NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID
        or resolve_workspace_path(binding["store_path"])
        != resolve_workspace_path(rollout["store_path"])
    ):
        raise ValueError("EXACT_SCHEDULED_PUBLICATION_BINDING_REQUIRED")
    row = store.get_outbox_message(
        "native-window-" + sha256_of(binding.get("window_id"))
    )
    window = json.loads(row["payload"]) if row else {}
    ordinal = binding.get("slot_ordinal", 0)
    day = window.get("production_day_id")
    if (
        not window
        or window["rollout_sha256"] != sha256_of(rollout)
        or window["window"]["opportunity_id"] != binding.get("window_id")
        or window["window"]["session"]
        != NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID[binding["automation_id"]]
        or not 1 <= ordinal <= window["capacity"]
        or simple_gemini_slot_id(
            production_day_id=day, window_id=binding["window_id"], slot_ordinal=ordinal
        )
        != binding["run_id"]
        or resolve_workspace_path(binding["output_dir"])
        != Path(rollout["editorial_output_root"]).resolve()
        / day
        / binding["window_id"]
        / binding["run_id"]
    ):
        raise ValueError("EXACT_SCHEDULED_PUBLICATION_BINDING_REQUIRED")
    assert_llm_operator_execution_enabled()
    if store.get_operating_control()["operating_mode"] != "AUTONOMOUS_DEFAULT":
        raise ValueError("PUBLICATION_OPERATING_MODE_BLOCKED")


def publication_projection(rows, dispatches, reconciliations, *, run_id, readiness=(), native_invocation_id=None):
    """Actual records only; no provider probes, configuration-as-login or writes."""
    operation = next(
        (
            json.loads(r["payload"])
            for r in rows
            if r["message_id"] == "native-operation-binding-" + sha256_of(run_id)
        ),
        {},
    )
    binding_path = str(
        resolve_workspace_path(operation.get("output_dir", "."))
        / (
            "binding.json"
            if operation.get("owner_manual_validation")
            else "native_operation_binding.json"
        )
    )

    def command(name):
        return (
            "python scripts/run_native_desktop_editorial.py "
            + name
            + ' --binding "'
            + binding_path
            + '"'
        )

    bindings = [
        json.loads(r["payload"])
        for r in rows
        if r["destination"] == DESTINATION
        and json.loads(r["payload"]).get("run_id") == run_id
    ]
    if not bindings:
        return {
            "state": "REVIEWED_HANDOFF_REQUIRED",
            "next_operation": "publication-prepare",
            "next_command": command("publication-prepare"),
            "destinations": [],
        }
    bound = bindings[-1]
    from live_contentops.destination_transport_registry_v1 import (
        registration_for_destination,
    )
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

    entries = []
    destinations = [
        "substack",
        "telegram",
        "discord",
        "x",
        "linkedin",
        "facebook_page",
        "instagram_business",
        "threads",
        "youtube",
    ]
    company_id = DurablePublicationCoordinator._ids(run_id, bound["plan_hash"], "linkedin_company")["message_id"]
    if any(r["message_id"] == company_id and r["work_item_id"] == run_id for r in rows):
        destinations.append("linkedin_company")
    for destination in destinations:
        ids = DurablePublicationCoordinator._ids(
            run_id, bound["plan_hash"], destination
        )
        dispatch = next(
            (d for d in dispatches if d["dispatch_id"] == ids["dispatch_id"]), {}
        )
        dispatch = DurablePublicationCoordinator.effective_dispatch(dispatch, dispatches)
        reconciliation = next(
            (
                r
                for r in reconciliations
                if r["reconciliation_id"] == "reconciliation_" + str(dispatch.get("dispatch_id", ids["dispatch_id"])).removeprefix("dispatch_")
            ),
            {},
        )
        reg = registration_for_destination(destination)
        cached = next((r for r in readiness if r["surface"] == reg.surface), {})
        entries.append(
            {
                "destination": destination,
                "transport": reg.transport_type,
                "dispatch_id": dispatch.get("dispatch_id", ids["dispatch_id"]),
                "status": dispatch.get("status", "NOT_DISPATCHED"),
                "reconciliation_status": reconciliation.get("status"),
                "public_object_id": dispatch.get("public_object_id"),
                "public_object_url": dispatch.get("public_object_url"),
                "dispatch_recorded": bool(dispatch),
                "cached_readiness": cached.get("readiness_state", "NOT_VERIFIED"),
                "blocker": None
                if reconciliation.get("status") == "RECONCILED_CONFIRMED"
                else dispatch.get(
                    "status", "CURRENT_EXTERNAL_IDENTITY_AND_READBACK_NOT_VERIFIED"
                ),
            }
        )
    pending = []
    for r in rows:
        if r["destination"] != "internal:native-neo-tool":
            continue
        p = json.loads(r["payload"])
        if (
            p.get("operation_id") == run_id
            and p.get("schema_version") == "contentops.native_neo_tool_request.v1"
        ):
            absence = p["request"].get("owner_absence_context")
            if p["request"]["action"] == "READBACK" and absence:
                prior = next((d for d in dispatches if d["dispatch_id"] == absence.get("dispatch_id")), {})
                if prior and prior.get("status") != "UNKNOWN_WRITE":
                    continue
            if (native_invocation_id and p["request"]["action"] == "VERIFY_IDENTITY"
                    and p["request"].get("native_invocation_id") not in {None, native_invocation_id}):
                continue
            key = "native-neo-" + sha256_of(
                [run_id, p["request"]["request_sha256"], "response"]
            )
            if not any(r["message_id"] == key for r in rows):
                claimed = any(
                    r["message_id"]
                    == "native-neo-"
                    + sha256_of([run_id, p["request"]["request_sha256"], "started"])
                    for r in rows
                )
                if native_invocation_id and p["request"]["action"] in {"READBACK", "VERIFY_IDENTITY"}:
                    # A later turn may reacquire a lost read-only observation, while
                    # a PUBLISH claim always remains globally fenced above.
                    claim_keys = {
                        "native-neo-" + sha256_of([run_id, p["request"]["request_sha256"], kind])
                        for kind in ("started", "started-readonly-" + sha256_of(native_invocation_id))
                    }
                    claimed = any(r["message_id"] in claim_keys
                        and json.loads(r["payload"]).get("native_invocation_id") == native_invocation_id for r in rows)
                pending.append(
                    {
                        **p,
                        "action_claimed": claimed,
                        "next_operation": "publication-resume"
                        if claimed and p["request"]["action"] == "PUBLISH"
                        else "publication-tool-submit"
                        if claimed
                        else "publication-tool-begin",
                    }
                )
    totals = DurablePublicationCoordinator.publication_totals(
        {e["destination"]: e for e in entries})
    confirmed = sum(e["reconciliation_status"] == "RECONCILED_CONFIRMED"
        and DurablePublicationCoordinator._confirmed_public_object(e, destination=e["destination"])
        for e in entries)
    state = (
        "RECONCILED"
        if confirmed == len(entries)
        else "PENDING_NATIVE"
        if pending
        else "RECOVERY_REQUIRED"
        if any(
            e["status"] in {"UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED"}
            for e in entries
        )
        else "PREPARED"
        if all(e["status"] == "NOT_DISPATCHED" for e in entries)
        else "DISTRIBUTION_INCOMPLETE"
    )
    # A lost claimed publish is never another tool-begin. Resume makes the sole
    # coordinator request readback; a still-live original tool may submit its return.
    actionable = next(
        (
            p
            for p in reversed(pending)
            if p["request"]["action"] != "PUBLISH" or not p["action_claimed"]
        ),
        None,
    )
    next_operation = (
        "none"
        if confirmed == len(entries)
        else actionable["next_operation"]
        if actionable
        else "publication-resume"
    )
    continuation_operation = next_operation
    if operation.get("owner_manual_validation") and next_operation != "none":
        next_operation = "publication-status"
    return {
        **bound,
        **totals,
        "state": state,
        "operation_scope": "OWNER_MANUAL_LIVE" if operation.get("owner_manual_live") else "OWNER_MANUAL_ISOLATED"
        if operation.get("owner_manual_validation")
        else "SCHEDULED",
        "destinations": entries,
        "pending_requests": pending,
        "dispatch_blocker": "OWNER_MANUAL_PUBLICATION_NOT_AUTHORIZED"
        if operation.get("owner_manual_validation")
        else "SEPARATE_OWNER_ACTIVATION_AND_CURRENT_DESTINATION_PROOF_REQUIRED",
        "next_operation": next_operation,
        "dispatch_continuation_operation": continuation_operation,
        "next_command": (
            "No remaining publication operation"
            if next_operation == "none"
            else command(next_operation)
        )
        + (
            " --response <observed-return.json>"
            if next_operation == "publication-tool-submit"
            else ""
        )
        + (
            " --request-sha256 " + actionable["request"]["request_sha256"]
            if actionable and "tool" in next_operation
            else ""
        )
        + (
            " --native-invocation-id <actual-turn-id> --rollout config/native_desktop_rollout_v1.json"
            if next_operation
            not in {"none", "publication-prepare", "publication-status"}
            else ""
        ),
        "external_proof": "Only actual dispatch/readback records establish publication; cached readiness may be stale.",
    }


class NativeReviewedPublication:
    """Thin continuation; the existing coordinator remains the only publication owner."""

    def __init__(
        self,
        store,
        binding,
        *,
        native_invocation_id,
        rollout=None,
        coordinator=None,
        executor=None,
    ):
        self.store, self.binding, self.rollout = store, binding, rollout
        self.coordinator, self.executor = coordinator, executor
        self.native_invocation_id = native_invocation_id

    def validate(self):
        value, plan, root = _prepared_packet(self.store, self.binding)
        recorded = [
            json.loads(r["payload"])
            for r in self.store.list_outbox_messages()
            if r["destination"] == DESTINATION
            and json.loads(r["payload"]).get("run_id") == self.binding["run_id"]
        ]
        if not recorded or recorded[-1] != value:
            raise ValueError(
                "NATIVE_PUBLICATION_REVIEW_OR_PACKET_CHANGED_PREPARE_AGAIN"
            )
        return plan, root

    def projection(self):
        value = publication_projection(
            self.store.list_outbox_messages(),
            self.store.list_platform_dispatches(),
            self.store.get_reconciliations_for_work_item(self.binding["run_id"]),
            run_id=self.binding["run_id"],
            readiness=self.store.list_destination_readiness(),
            native_invocation_id=self.native_invocation_id,
        )
        try:
            if value["state"] == "REVIEWED_HANDOFF_REQUIRED":
                validated_native_review(self.store, run_id=self.binding["run_id"])
            else:
                self.validate()
        except (ValueError, OSError) as exc:
            return {
                **value,
                "state": "INVALIDATED",
                "blocker": str(exc),
                "next_operation": "review-current-packet",
                "next_command": "Review the current source/article packet; do not begin any prior tool request.",
            }
        if (not self.binding.get("owner_manual_validation") and value["state"] not in {"REVIEWED_HANDOFF_REQUIRED", "RECONCILED"}
                and not any(e["status"] in {"UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED"}
                            for e in value.get("destinations", []))):
            from live_contentops.native_desktop_editorial_v1 import require_current_final_visual_review
            try:
                acceptance = require_current_final_visual_review(self.store, run_id=self.binding["run_id"])
                value = {**value, "final_visual_acceptance": acceptance}
            except (ValueError, OSError, KeyError, TypeError) as exc:
                value = {**value, "dispatch_blocker": str(exc), "final_visual_acceptance": None,
                    "next_operation": "final-visual-review",
                    "next_command": 'python scripts/run_native_desktop_editorial.py final-visual-review --binding "'
                        + str(resolve_workspace_path(self.binding["output_dir"]) /
                              ("binding.json" if self.binding.get("owner_manual_live") else "native_operation_binding.json")) + '"',
                    "resume_condition": "Same designated MAX editor corrects findings, re-renders affected views and records current final acceptance; preserve this operation."}
        return value

    def _authorize_and_bind(self):
        scheduled_publication_authority(self.store, self.binding, self.rollout)
        if self.coordinator is None:
            self.coordinator, self.executor = bind_native_neo_coordinator(
                self.store,
                operation_id=self.binding["run_id"],
                output_dir=resolve_workspace_path(self.binding["output_dir"])
                / "native-neo",
                native_invocation_id=self.native_invocation_id,
                allow_publish=True,
            )
        if (
            self.executor is None
            or self.executor.operation_id != self.binding["run_id"]
            or self.executor.native_invocation_id != self.native_invocation_id
            or resolve_workspace_path(self.executor.store.db_path)
            != resolve_workspace_path(self.binding["store_path"])
            or resolve_workspace_path(self.coordinator.store.db_path)
            != resolve_workspace_path(self.binding["store_path"])
        ):
            raise ValueError("EXACT_EXISTING_COORDINATOR_EXECUTOR_BINDING_REQUIRED")

    def linkedin_recovery(self, action, *, response):
        """Explicit owner recovery over the same bound publication and native executor."""
        plan, _ = self.validate()
        self._authorize_and_bind()
        if not isinstance(response, dict):
            raise ValueError("LINKEDIN_RECOVERY_OWNER_OR_REVIEW_REFERENCE_REQUIRED")
        try:
            if action == "absence":
                dispatch = self.coordinator._ids(self.binding["run_id"], plan["plan_hash"], "linkedin")["dispatch_id"]
                outcome = self.coordinator.reconcile_owner_confirmed_linkedin_absence(dispatch,
                    owner_authority_ref=response.get("owner_authority_ref"), request_hash=response.get("request_sha256"))
            elif action == "personal":
                message = self.coordinator._ids(self.binding["run_id"], plan["plan_hash"], "linkedin")["message_id"]
                outcome = self.coordinator.complete_dated_distribution_recovery(message,
                    review_reference=response["review_reference"])
            elif action == "company":
                outcome = self.coordinator.publish_reviewed_linkedin_company_copy(run_id=self.binding["run_id"],
                    review_reference=response["review_reference"])
            else:
                raise ValueError("LINKEDIN_RECOVERY_ACTION_UNSUPPORTED")
        except NativeNeoInputRequired as pending:
            outcome = {"status": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": pending.request,
                "public_write_performed": False}
        return {"classification": "NATIVE_LINKEDIN_RECOVERY", "coordinator_result": outcome,
            "publication": self.projection()}

    def resume(self):
        plan, root = self.validate()
        self._authorize_and_bind()
        try:
            from live_contentops.native_desktop_editorial_v1 import validate_release_media
            result, _, _ = validated_native_review(self.store, run_id=self.binding["run_id"])
            try:
                validate_release_media(result)
            except (ValueError, OSError) as media_error:
                # New release requirements cannot erase an existing unknown-write
                # obligation. Reconcile only exact existing attempts; never send a
                # missing article/derivative to work around the media hold.
                existing = [e for e in self.projection().get("destinations", [])
                            if e["status"] in {"UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED"}]
                if not existing:
                    raise
                summary = {"state": "MEDIA_HOLD_READBACK_ONLY", "blocker": str(media_error),
                    "readbacks": [self.coordinator.readback_existing_dispatch(e["dispatch_id"]) for e in existing],
                    "new_publish_calls": 0}
                return {"classification": "NATIVE_PUBLICATION_CONTINUATION", "coordinator_result": summary,
                        "publication": self.projection()}
            existing = [e for e in self.projection().get("destinations", [])
                        if e["status"] in {"UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED"}]
            from live_contentops.native_desktop_editorial_v1 import require_current_final_visual_review
            try:
                require_current_final_visual_review(self.store, run_id=self.binding["run_id"])
            except (ValueError, OSError) as visual_error:
                if not existing:
                    raise
                summary = {"state": "RECOVERY_READBACK_BEFORE_FINAL_VISUAL_REVIEW", "blocker": str(visual_error),
                    "readbacks": [self.coordinator.readback_existing_dispatch(e["dispatch_id"]) for e in existing],
                    "new_publish_calls": 0}
                return {"classification": "NATIVE_PUBLICATION_CONTINUATION", "coordinator_result": summary,
                        "publication": self.projection()}
            summary = SimplePublicationHandoffV1(
                store=self.store, coordinator=self.coordinator
            ).resume(slot_id=self.binding["run_id"], slot_output_dir=root)
            company = self.coordinator._ids(self.binding["run_id"], plan["plan_hash"], "linkedin_company")
            dispatch = self.store.get_platform_dispatch(company["dispatch_id"])
            message = self.store.get_outbox_message(company["message_id"])
            if message:
                # Selected company copies use their existing intent; generic continuation
                # may consume a return or read back, never select another company send.
                intent = json.loads(message["payload"])
                if not dispatch or dispatch["status"] == "NATIVE_NEO_TOOL_PENDING":
                    self.coordinator.publish_reviewed_linkedin_company_copy(run_id=self.binding["run_id"],
                        review_reference=intent["dated_distribution_recovery"])
                else:
                    self.coordinator.readback_existing_dispatch(dispatch["dispatch_id"])
        except NativeNeoInputRequired as pending:
            summary = {
                "state": "PENDING_NATIVE",
                "native_tool_request": pending.request,
            }
        summary = {**summary, **self.coordinator.publication_state(self.binding["run_id"], plan)}
        return {
            "classification": "NATIVE_PUBLICATION_CONTINUATION",
            "coordinator_result": summary,
            "publication": self.projection(),
        }

    def tool(self, command, *, request_hash, response=None):
        self.validate()
        self._authorize_and_bind()
        if command == "begin":
            packet = self.executor._get(request_hash, "request")
            if packet and packet["request"]["action"] == "PUBLISH":
                from live_contentops.native_desktop_editorial_v1 import validate_release_media, require_current_final_visual_review
                result, _, _ = validated_native_review(self.store, run_id=self.binding["run_id"])
                validate_release_media(result)
                require_current_final_visual_review(self.store, run_id=self.binding["run_id"])
            try:
                return self.executor.begin(request_hash)
            except NativeNeoInputRequired as pending:
                return {
                    "classification": "NATIVE_NEO_CURRENT_IDENTITY_OBSERVATION_REQUIRED",
                    "native_tool_request": pending.request,
                    "publication": self.projection(),
                }
        if command != "submit" or not isinstance(response, dict):
            raise ValueError("ACTUAL_NATIVE_NEO_OBSERVED_RETURN_REQUIRED")
        submitted = self.executor.submit(request_hash, response)
        packet = self.executor._get(request_hash, "request")
        result = response.get("result") or {}
        if (packet["request"]["action"] == "PUBLISH" and result.get("status") == "SUCCESS"
                and result.get("public_object_id") and result.get("public_object_url")):
            submitted["completed_write_reconciliation"] = self.coordinator.reconcile_completed_native_publish(
                packet["request"]["dispatch_attempt_identity"], request_hash=request_hash)
        return submitted
