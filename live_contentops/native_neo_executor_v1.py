"""Durable tool requests for Neo executors.

The conversation path begins the exact persisted request,
executes BrowserOS Neo, submits the observed return, and resumes the same coordinator.
CC-436's minute consumer may select the endpoint transport for X and Notes; it
uses this same request/claim/return owner and records its true execution surface.
Requests, action claims and returns use the existing outbox. A claimed publish with no
return is ambiguous and can only enter the coordinator's readback/recovery path.
"""
from __future__ import annotations

import json
from hashlib import sha256
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    _private, canonical_bytes, sha256_of,
)

SCHEMA = "contentops.native_neo_tool_request.v1"
DESTINATION = "internal:native-neo-tool"
PENDING = "NATIVE_NEO_TOOL_PENDING"
TOOL = "mcp__browseros_neo__run"
# CC-283: the agent surface that ran the BrowserOS Neo step is recorded under its own true label
# with the tool name that surface actually calls; Claude is never recorded as Codex (C5). The
# request packet keeps naming TOOL, so stored requests and their hashes stay unchanged.
CODEX_SURFACES = frozenset({"CODEX_DESKTOP_CONVERSATION", "CODEX_NATIVE_SUBAGENT", "CODEX_EXEC"})
CLAUDE_CODE_SURFACE = "CLAUDE_CODE_SESSION"
SURFACE_TOOLS = {**{surface: TOOL for surface in CODEX_SURFACES}, CLAUDE_CODE_SURFACE: "mcp__browseros-neo__run"}
SURFACE_TOOLS["NEO_ENDPOINT_EXECUTOR"] = "browseros-neo/run"


def expected_posts(request: Mapping[str, Any]) -> list[str]:
    """The exact texts a composer must hold before the click: a thread's posts, else the one text."""
    payload = request.get("native_payload") or request.get("payload") or {}
    if isinstance(payload, str):
        return [payload] if payload else []
    if not isinstance(payload, Mapping):
        return []
    posts = [str(p.get("text") if isinstance(p, Mapping) else p) for p in payload.get("posts") or []
             if (p.get("text") if isinstance(p, Mapping) else p)]
    if posts:
        return posts
    return [str(payload["text"])] if payload.get("text") else []


def _post_texts(posts) -> list[str]:
    """Compare composer texts as step 3 says: whitespace collapsed, a link allowed to render shortened."""
    import re
    quotes = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})
    return [" ".join(re.sub(r"https?://\S+", "<link>", str(p).translate(quotes)).split()) for p in posts]


class NativeNeoInputRequired(Exception):
    def __init__(self, request: Mapping[str, Any]):
        self.request = dict(request)
        super().__init__(PENDING)


def _readback_absence_evidence(request, result):
    if (request.get("public_object_id") or request.get("public_object_url")
            or result.get("public_object_id") or result.get("public_object_url")
            or result.get("target_post_absent") is not True
            or result.get("authenticated") is not True or result.get("activity_feed_loaded") is not True
            or result.get("observed_profile_url") != request.get("entry_url")):
        return False
    try:
        observed = datetime.fromisoformat(result["native_tool_observation"]["observed_at_utc"].replace("Z", "+00:00"))
        attempted = datetime.fromisoformat(request["latest_dispatch_attempt_at_utc"].replace("Z", "+00:00"))
        return (observed - attempted).total_seconds() >= 600
    except (KeyError, TypeError, ValueError):
        return False


def _incomplete_readback_evidence(request, result):
    """Refresh a partial image comparison or a requested original publication clock."""
    if (request.get("owner_absence_context") and not request.get("public_object_id")
            and not request.get("public_object_url")):
        # The coordinator validates this own-activity absence observation. An
        # absent post has no delivered media; do not replace its exact return
        # with a new image-comparison request before that validation can run.
        return False
    if _readback_absence_evidence(request, result):
        return False  # An absent object has no delivered image to compare.
    if (result.get("media_check_state") == "MISSING_REQUIRED_MEDIA"
            and result.get("missing_required_media_observed") is True
            and result.get("public_object_id") and result.get("public_object_url")
            and result.get("observed_text") and not result.get("public_image_urls")):
        return False  # Decisive failed delivery, not an unfinished binary comparison.
    return (result.get("media_check_state") == "PENDING_BINARY_COMPARISON"
            or (bool((request.get("content_binding") or {}).get("attachment_manifest"))
                and not result.get("observed_attachments"))
            or (bool(request.get("publication_clock_readback"))
                and not (result.get("published_at_utc") or result.get("observed_published_at_utc")))
            or (bool((request.get("content_binding") or {}).get("media_manifest"))
                and not result.get("observed_media_sha256") and not result.get("media_comparisons")))


class NativeNeoExecutor:
    """Callable executor and readiness provider bound to one active Desktop operation."""

    native_neo_protocol = True

    def __init__(self, store, *, operation_id: str, output_dir: str | Path,
                 native_invocation_id: str, allow_publish: bool = False, clock=None,
                 identity_at_action: bool = False):
        if not operation_id or not native_invocation_id:
            raise ValueError("NATIVE_NEO_ACTIVE_INVOCATION_REQUIRED")
        self.store = store
        self.operation_id = operation_id
        self.root = Path(output_dir)
        self.native_invocation_id = native_invocation_id
        self.allow_publish = allow_publish
        # CC-283: in a publishing operation, one composed Neo run per destination checks the
        # expected account, publishes and reads back. Never outside a publishing operation.
        self.identity_at_action = bool(identity_at_action and allow_publish)
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.readback_request_invocations = {}

    def _key(self, request_hash, kind):
        return "native-neo-" + sha256_of([self.operation_id, request_hash, kind])

    def _get(self, request_hash, kind):
        row = self.store.get_outbox_message(self._key(request_hash, kind))
        return json.loads(row["payload"]) if row else None

    def _claim(self, request_hash, invocation_id):
        original = self._get(request_hash, "started")
        if original and original["native_invocation_id"] == invocation_id:
            return original
        return self._get(request_hash, "started-readonly-" + sha256_of(invocation_id))

    def _put(self, request_hash, kind, value, work):
        if _private(value):
            raise ValueError("PRIVATE_NATIVE_NEO_MATERIAL_EXCLUDED")
        previous = self._get(request_hash, kind)
        if previous is not None and previous != value:
            raise ValueError("NATIVE_NEO_IMMUTABLE_RETURN_CONFLICT")
        row = self.store.register_outbox_message(
            message_id=self._key(request_hash, kind), work_item_id=work,
            destination=DESTINATION, payload=canonical_bytes(value).decode(),
            status="NATIVE_NEO_INTERNAL",
        )
        if json.loads(row["payload"]) != value:
            raise ValueError("NATIVE_NEO_IMMUTABLE_RETURN_CONFLICT")

    def __call__(self, request):
        request = dict(request)
        request_hash = request.get("request_sha256")
        if request_hash != sha256_of({k: v for k, v in request.items() if k != "request_sha256"}):
            raise ValueError("NATIVE_NEO_REQUEST_HASH_INVALID")
        from live_contentops.destination_transport_registry_v1 import barred_browser_destinations
        if request.get("destination") in barred_browser_destinations() and request.get("action") in {"READBACK", "VERIFY_IDENTITY"}:
            response = self._get(request_hash, "response")
            if response:
                return dict(response["result"])
            return {"status": "SKIPPED", "verified": False, "write_absent": False,
                "reason_code": barred_browser_destinations()[request["destination"]], "request_sha256": request_hash}
        if request["action"] in {"PUBLISH", "EDIT_EXISTING"}:
            from live_contentops.neo_destination_handoff_v1 import _prohibited_write
            refused = _prohibited_write(request.get("destination"))
            if refused is not None:
                # Preserve existing responses/claims: an earlier attempted write
                # still belongs to readback/reconciliation, never a new no-write.
                response = self._get(request_hash, "response")
                if response:
                    return dict(response["result"])
                if self._get(request_hash, "started"):
                    return {"status": "UNKNOWN_WRITE", "request_sha256": request_hash,
                            "reason_code": "NATIVE_NEO_CLAIMED_ACTION_WITHOUT_RETURN",
                            "retry_permitted": False}
                return {**refused, "request_sha256": request_hash}
        if request["action"] in {"PUBLISH", "EDIT_EXISTING"} and not self.allow_publish:
            return {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True,
                    "request_sha256": request_hash, "observed_identity": request["expected_identity"],
                    "reason_code": "NATIVE_NEO_OPERATION_READ_ONLY", "public_write_performed": False}
        work = request["work_item_id"]
        packet = {"schema_version": SCHEMA, "operation_id": self.operation_id,
                  "required_tool": TOOL, "request": request,
                  "action_boundary": "BEGIN_BEFORE_TOOL_ACTION; SUBMIT_OBSERVED_RETURN; RESUME_COORDINATOR",
                  "public_write_authorized": request["action"] in {"PUBLISH", "EDIT_EXISTING"} and self.allow_publish}
        packet["tool_request_sha256"] = sha256_of(packet)
        self._put(request_hash, "request", packet, work)
        response = self._get(request_hash, "response")
        if response:
            return dict(response["result"])
        started = self._get(request_hash, "started")
        if started and request["action"] in {"PUBLISH", "EDIT_EXISTING"}:
            return {"status": "UNKNOWN_WRITE", "request_sha256": request_hash,
                    "observed_identity": request["expected_identity"],
                    "reason_code": "NATIVE_NEO_CLAIMED_ACTION_WITHOUT_RETURN", "retry_permitted": False}
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / (request_hash + ".request.json")
        path.write_bytes(canonical_bytes(packet))
        raise NativeNeoInputRequired({**packet, "request_path": str(path)})

    def begin(self, request_hash: str):
        """Claim once before a platform action; a restart never repeats a claimed write."""
        row = self.store.get_outbox_message(self._key(request_hash, "request"))
        if row and row["status"] == "NATIVE_NEO_SUPERSEDED":
            raise ValueError("NATIVE_NEO_STALE_PUBLISH_REVISION_SUPERSEDED")
        packet = self._get(request_hash, "request")
        if not packet:
            raise ValueError("NATIVE_NEO_REQUEST_NOT_FOUND")
        request = packet["request"]
        from live_contentops.destination_transport_registry_v1 import barred_browser_destinations
        if request.get("destination") in barred_browser_destinations() and request.get("action") in {"READBACK", "VERIFY_IDENTITY"}:
            raise ValueError(barred_browser_destinations()[request["destination"]])
        if request["action"] in {"PUBLISH", "EDIT_EXISTING"}:
            from live_contentops.neo_destination_handoff_v1 import _prohibited_write
            refused = _prohibited_write(request.get("destination"))
            if refused is not None:
                raise ValueError(refused["reason_code"])
        original = self._get(request_hash, "started")
        claim_kind = "started"
        if original:
            # Lost observations can be reacquired by a later native turn. Keep the
            # original claim immutable; a claimed public write is NEVER reclaimed.
            if request["action"] not in {"READBACK", "VERIFY_IDENTITY"} or self._claim(request_hash, self.native_invocation_id):
                raise ValueError("NATIVE_NEO_ACTION_ALREADY_CLAIMED_READBACK_ONLY")
            claim_kind = "started-readonly-" + sha256_of(self.native_invocation_id)
        if request["action"] in {"PUBLISH", "EDIT_EXISTING"}:
            from live_contentops.public_time_v1 import require_public_time, public_media_text
            require_public_time(request.get("native_payload"), request.get("payload"),
                                public_media_text(request.get("content_binding", {}).get("media_manifest")))
            from live_contentops.llm_operator_control_v1 import assert_llm_operator_execution_enabled
            assert_llm_operator_execution_enabled()
            if not self.allow_publish or self.store.get_operating_control()["operating_mode"] != "AUTONOMOUS_DEFAULT":
                raise ValueError("NATIVE_NEO_PUBLIC_WRITE_NOT_AUTHORIZED")
            dispatch = self.store.get_platform_dispatch(request["dispatch_attempt_identity"])
            expected_status = "DISPATCH_CONFIRMED" if request["action"] == "EDIT_EXISTING" else PENDING
            allowed_statuses = {expected_status}
            if request["action"] == "PUBLISH" and getattr(self, "inline_transport", False):
                # CC-436: the sole coordinator already atomically owns this
                # dispatch and is still inside its synchronous transport call.
                allowed_statuses.add("DISPATCH_ATTEMPT_STARTED")
            if not dispatch or dispatch["status"] not in allowed_statuses:
                raise ValueError("NATIVE_NEO_EXACT_COORDINATOR_PENDING_DISPATCH_REQUIRED")
            if request["action"] == "PUBLISH":
                # A pending request can outlive the first coordinator call. Apply
                # decision 93 again at the actual browser action boundary.
                from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
                from live_contentops.article_publication_quality_v1 import before_article_write
                coordinator = DurablePublicationCoordinator(store=self.store, transport_runtime=None, clock=self.clock)
                if coordinator.published_content_path is not None:
                    message = self.store.get_outbox_message(dispatch["message_id"])
                    effective = coordinator._effective_message(message)
                    intent = json.loads(effective["payload"])
                    before_article_write(coordinator, {**intent,
                        **({"native_payload": request["native_payload"]} if request.get("native_payload") else {})},
                        request["destination"])
            if request["action"] == "EDIT_EXISTING" and request.get("approved_presentation_restore"):
                from live_contentops.approved_presentation_restore_v1 import restore_intent
                from live_contentops.neo_destination_handoff_v1 import _payload_binding
                expected = restore_intent(self.store, request["dispatch_attempt_identity"])
                payload, content = _payload_binding(expected, "substack")
                if (request["destination"] != "substack"
                        or request["approved_presentation_restore"] != expected["approved_presentation_restore"]
                        or any(request.get(k) != dispatch.get(k) for k in ("public_object_id", "public_object_url"))
                        or request.get("native_payload") != payload or request.get("content_binding") != content
                        or request.get("payload_hash") != expected["destination_plan"]["payload_hash"]):
                    raise ValueError("NATIVE_NEO_APPROVED_PRESENTATION_RESTORE_CHANGED")
            elif request["action"] == "EDIT_EXISTING":
                from live_contentops.native_desktop_editorial_v1 import reader_presentation_acceptance
                revision, _, _ = reader_presentation_acceptance(self.store, run_id=request["work_item_id"],
                    reference=request.get("reader_presentation_review"))
                identity = revision["objects"][request["destination"]]
                if any(request.get(k) != identity.get(k) for k in ("public_object_id", "public_object_url")):
                    raise ValueError("NATIVE_NEO_EXACT_REVIEWED_EDIT_OBJECT_REQUIRED")
                from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
                from live_contentops.neo_destination_handoff_v1 import _payload_binding
                expected_intent, _, _, _ = DurablePublicationCoordinator(store=self.store, transport_runtime=None)._reader_presentation_intent(
                    self.store.get_outbox_message(identity["message_id"]), request["reader_presentation_review"])
                expected_payload, expected_content = _payload_binding(expected_intent, request["destination"])
                if (request.get("native_payload") != expected_payload or request.get("content_binding") != expected_content
                        or request.get("payload_hash") != sha256_of(expected_payload)):
                    raise ValueError("NATIVE_NEO_EXACT_REVIEWED_EDIT_PAYLOAD_REQUIRED")
            elif request["action"] == "PUBLISH":
                from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
                from live_contentops.neo_destination_handoff_v1 import _payload_binding
                message = self.store.get_outbox_message(dispatch["message_id"])
                if message:
                    effective = DurablePublicationCoordinator(store=self.store, transport_runtime=None)._effective_message(message)
                    intent = json.loads(effective["payload"])
                    if intent.get("reader_presentation_review"):
                        expected_payload, expected_content = _payload_binding(intent, request["destination"])
                        if request.get("native_payload") != expected_payload or request.get("content_binding") != expected_content:
                            raise ValueError("NATIVE_NEO_STALE_PUBLISH_REVISION_SUPERSEDED")
            content = request.get("content_binding") or {}
            if not content.get("expected_text_segments"):
                raise ValueError("NATIVE_NEO_EXACT_PAYLOAD_REQUIRED")
            if request["action"] == "PUBLISH":
                from live_contentops.event_public_record_v1 import require_preview_deadline
                require_preview_deadline(content.get("event_public_record") or {}, now_utc=self.clock().isoformat())
                from live_contentops.event_pack_v1 import require_action_clock
                require_action_clock(content.get("event_public_record") or {}, now=self.clock().isoformat())
            # Fresh native account proof is rechecked at the action boundary, after any
            # pending Desktop delay. A configured login/executor flag grants no write.
            # CC-283: a composed publish checks the account inside the same run, just before
            # the write; submit() then requires that observation (fresher than a 5-minute proof).
            if not self._composed(request):
                proof = self.readiness(request["surface"])
                if not proof["authenticated"] or not proof["native_executor_bound"]:
                    raise ValueError("NATIVE_NEO_CURRENT_IDENTITY_REQUIRED")
            for artifact in [*content.get("artifact_manifest", []), *content.get("media_manifest", []),
                             *content.get("attachment_manifest", [])]:
                path = Path(str(artifact.get("path") or ""))
                if not artifact.get("sha256") or not path.is_file() or sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
                    raise ValueError("NATIVE_NEO_PAYLOAD_OR_MEDIA_BYTES_CHANGED")
        claim = {"tool_request_sha256": packet["tool_request_sha256"],
                 "native_invocation_id": self.native_invocation_id,
                 "begun_at_utc": self.clock().isoformat(), "required_tool": TOOL}
        if self._composed(request):
            claim["identity_at_action"] = True
        # The unique immutable outbox key fences simultaneous Desktop claimers too.
        self._put(request_hash, claim_kind, claim, request["work_item_id"])
        # CC-401: cancellation and begin may race. A cancelled unclaimed Note
        # cannot return an action packet even if its claim arrived just afterward.
        current = self.store.get_outbox_message(self._key(request_hash, "request"))
        if current and current["status"] == "NATIVE_NEO_SUPERSEDED":
            raise ValueError("NATIVE_NEO_STALE_PUBLISH_REVISION_SUPERSEDED")
        if request["action"] == "READBACK":
            identity = sha256_of({k: v for k, v in request.items()
                if k not in {"request_sha256", "native_invocation_id"}})
            self.readback_request_invocations[identity] = request.get("native_invocation_id")
        action_packet = dict(packet)
        action_packet["browser_workspace"] = {
            "policy": "JIM_DECISION_63",
            "window": "Use the one existing BrowserOS Neo window. Create one only if none exists.",
            "tabs": "Open tabs with tabs action=new and groupId in this task's group, titled Capital Chronicle/<task>. Leave Jim's and other agents' tabs untouched.",
        }
        if request["action"] in {"PUBLISH", "EDIT_EXISTING"}:
            action_packet["upload_policy"] = {
                "method": "BROWSEROS_NEO_UPLOAD_OR_FILE_CHOOSER_INTERCEPTION",
                "source_scope": "ARTICLE_OWN_MEDIA_FOLDER",
                "bound_media_paths": [a["path"] for a in [
                    *request.get("content_binding", {}).get("media_manifest", []),
                    *request.get("content_binding", {}).get("attachment_manifest", [])]],
                "native_file_dialog": "FORBIDDEN_STOP_WITH_NATIVE_FILE_DIALOG_OPEN"}
        if request["destination"] == "substack" and request["action"] in {"PUBLISH", "EDIT_EXISTING"}:
            action_packet["substack_publish_routine"] = {
                "policy": "JIM_DECISIONS_48_52_63",
                "window": "Use the one existing BrowserOS Neo window and this task's tab group. Never create another window. Leave Jim's tabs untouched.",
                "before_publish": "Use the finished Substack draft in this task's tab group. Do not open Gmail unless Substack shows \"Check your email\". Never read a mailbox or enter an email code.",
                "email_code_dialog": "Record PENDING_JIM_EMAIL_CODE, draft_id, page_id and URL. Only now open Gmail, in one new tab of this task's group, by a run script that returns only the page id; never tabs action=new (its reply carries a snapshot) and never a snapshot, read, grep, evaluate or screenshot of Gmail or its content in any result. Leave the code tab open and untouched for Jim; continue other destinations in other task tabs. No automatic wait, reload, navigation or input on the code tab.",
                "continue_only_after": "The same tab reaches /publish/posts/detail/.../share-center; continue exact readback and dispatch recording.",
                "pending_is_dispatch": False,
                # CC-199, 5 Nov IBM: the Substack run took 6 min 8 s (claim 05:50:43Z, observed 05:56:51Z)
                # and nothing recorded which part. Timestamps only, inside this run's return.
                "step_clocks": {"return_as": "result.step_clocks",
                    "fields": ["draft_ready_utc", "images_uploaded_utc", "publish_clicked_utc",
                               "email_setting_confirmed_utc", "share_center_reached_utc"],
                    "rule": "Record each UTC time from the browser clock as the run reaches that point; leave a "
                            "point that did not happen null. No extra step or turn."},
                "email_code_return": {"status": "PENDING_JIM_EMAIL_CODE", "required_fields": ["draft_id", "page_id", "page_url"],
                    "pipeline_state": "SUBSTACK_DRAFT_AWAITING_OWNER", "automatic_wait": False,
                    "tab_policy": "Leave this tab open and untouched for Jim under decision 52; continue in other task tabs without a human-help tool wait."},
            }
            if request.get("substack_delivery_policy"):
                action_packet["substack_publish_routine"]["delivery"] = request["substack_delivery_policy"]
        if self._composed(request):
            from live_contentops.destination_transport_registry_v1 import SURFACE_REGISTRY
            action_packet["composed_run"] = {
                "policy": "CC-283",
                "one_run": "One BrowserOS Neo run script does all five steps in this order, in this task's tab. "
                           "It replaces the request's steps list: no separate identity, snapshot or binding step first.",
                "1_identity": {"expected_identity": request["expected_identity"],
                    "expected_stable_id": SURFACE_REGISTRY[request["surface"]].expected_stable_id,
                    "rule": "Read the signed-in account and compare it with the expected identity and stable id. "
                            "While in this identity or any other pre-write part, result.stage is BEFORE_PUBLISH_CLICK. "
                            "A mismatch or an unreadable identity returns FAILED_BEFORE_WRITE with definite_no_write "
                            "true, stage BEFORE_PUBLISH_CLICK and no click."},
                # 5 Nov PPI: the X thread's third reply went out without its first paragraph and needed a
                # public correction reply. Nothing checked the composer before the click.
                "2_compose": "Enter each post below in its own composer box, in order, with its bound media. For a "
                             "thread, add each next box with the composer's add-post control and wait until that box "
                             "exists and has focus; then enter the post's whole text in one operation, newlines "
                             "included. Never enter a post paragraph by paragraph, or before its box is ready.",
                "3_verify_before_click": {"posts": expected_posts(request),
                    "rule": "Before the click, read every composer box's text back and compare it with its post, with "
                            "whitespace collapsed and a link allowed to render shortened. Every post must match, in "
                            "order, with no box missing or extra. Re-enter a box that differs once and compare again. "
                            "If any post still differs, return FAILED_BEFORE_WRITE with definite_no_write true, stage "
                            "BEFORE_PUBLISH_CLICK and no click."},
                "4_publish": "Immediately BEFORE the publish click, set the observation's dispatched_at_utc and "
                             "result.stage = PUBLISH_CLICK_ATTEMPTED; then click once to publish the exact payload.",
                "5_readback": "Right after the click, in the same run, read back the published object (id, url, "
                              "text, media) and return it as composed.readback. This readback confirms the "
                              "destination: no separate readback turn follows, and the next destination's run "
                              "starts after it.",
                "return": {"result": "the publish result, as for any PUBLISH step, with its stage",
                    "composed": {"identity": ["authenticated", "observed_identity", "observed_stable_id", "observed_at_utc"],
                                 "pre_click_posts": "REQUIRED with any write: the composer texts read in "
                                                    "step 3, in order. A return without them is refused; "
                                                    "if they were not read, submit nothing",
                                 "readback": "REQUIRED with any write: the READBACK result fields (status, "
                                             "observed_identity, public_object_id, public_object_url, "
                                             "observed_text, content_verified, media) observed in this run after "
                                             "the click. A return without it is refused"}},
                "after_click": "FAILED_BEFORE_WRITE is a definite no-write only for an account mismatch or stage "
                               "BEFORE_PUBLISH_CLICK. Any other failure, including a missing stage, is UNKNOWN_WRITE; "
                               "the coordinator reads back before any retry.",
                # 5 Nov PPI: X was claimed at 00:35:16Z and clicked at 00:49:55Z, after the LinkedIn company
                # evidence work (a74b2bb8, 00:49:33Z); the X run itself took 1 min 42 s.
                "after_run": "Submit this run's return at once, then start the next destination's run. Extra checks "
                             "of a destination already read back (media comparisons, evidence files, commits) wait "
                             "until every destination has gone out.",
            }
        return action_packet

    def _composed(self, request):
        return (self.identity_at_action and request.get("action") == "PUBLISH"
                and request.get("destination") not in {"substack"})

    def publication_readiness(self, surface):
        """The readiness manager's provider. Inside a publishing operation with composed runs, a
        Neo destination without a fresh proof is ready for a run that checks the account at the
        action; anything else needs an observed identity as before."""
        from live_contentops.destination_transport_registry_v1 import SURFACE_REGISTRY
        destination = SURFACE_REGISTRY[surface].destination_key
        if self.identity_at_action and destination != "substack":
            from live_contentops.neo_destination_handoff_v1 import IDENTITIES
            fresh = self._fresh_identity_return(destination, surface, IDENTITIES[destination],
                expected_stable_id=SURFACE_REGISTRY[surface].expected_stable_id)
            if fresh is None:
                return {"identity_at_action": True, "native_executor_bound": True, "authenticated": None,
                        "proof_fresh": False, "native_invocation_id": self.native_invocation_id}
        return self.readiness(surface)

    def submit(self, request_hash: str, response: Mapping[str, Any]):
        packet = self._get(request_hash, "request")
        observation = dict(response.get("tool_observation") or {})
        claim = self._claim(request_hash, observation.get("native_invocation_id"))
        if not packet or not claim or response.get("tool_request_sha256") != packet["tool_request_sha256"]:
            raise ValueError("NATIVE_NEO_TOOL_RETURN_BINDING_REQUIRED")
        if (observation.get("surface") not in SURFACE_TOOLS
                or observation.get("tool_name") != SURFACE_TOOLS[observation["surface"]]
                or observation.get("native_invocation_id") != claim["native_invocation_id"]
                or not observation.get("observation_source") or not observation.get("observed_at_utc")):
            raise ValueError("NATIVE_NEO_ACTUAL_TOOL_OBSERVATION_REQUIRED")
        observed_at = datetime.fromisoformat(observation["observed_at_utc"].replace("Z", "+00:00"))
        begun_at = datetime.fromisoformat(claim["begun_at_utc"])
        if not begun_at <= observed_at <= self.clock() + timedelta(seconds=30):
            raise ValueError("NATIVE_NEO_OBSERVATION_TIME_INVALID")
        if observation.get("dispatched_at_utc"):
            dispatched_at = datetime.fromisoformat(observation["dispatched_at_utc"].replace("Z", "+00:00"))
            if packet["request"]["action"] != "PUBLISH" or not begun_at <= dispatched_at <= observed_at:
                raise ValueError("NATIVE_NEO_DISPATCH_TIME_INVALID")
        result = dict(response["result"])
        if result.get("request_sha256") != request_hash:
            raise ValueError("NATIVE_NEO_RETURN_REQUEST_MISMATCH")
        expected_stable_id = packet["request"].get("expected_stable_id")
        if (packet["request"]["action"] == "VERIFY_IDENTITY" and expected_stable_id
                and result.get("authenticated") is True
                and result.get("observed_stable_id") != expected_stable_id):
            # Reject an incomplete observation before the immutable return is saved,
            # so the caller can correct it on the same claimed read-only request.
            raise ValueError("NATIVE_NEO_STABLE_IDENTITY_OBSERVATION_REQUIRED")
        readback = None
        if claim.get("identity_at_action"):
            result, readback = self._composed_return(packet["request"], claim, observation, result,
                                                     dict(response.get("composed") or {}))
        result["native_tool_observation"] = observation
        result["native_tool_return_sha256"] = sha256_of(response)
        self._put(request_hash, "response", {"result": result}, packet["request"]["work_item_id"])
        if readback is not None:
            self._store_composed_readback(packet["request"], claim, result, readback, observation, response)
        return {"request_sha256": request_hash, "tool_return_sha256": sha256_of(response)}

    def _composed_return(self, request, claim, observation, result, composed):
        """CC-283: the account must be observed in the same run, between the claim and the
        publish click, and match the binding's expected identity and stable id."""
        from live_contentops.destination_transport_registry_v1 import SURFACE_REGISTRY
        identity = composed.get("identity")
        if not isinstance(identity, Mapping) or not identity.get("observed_at_utc"):
            raise ValueError("NATIVE_NEO_COMPOSED_IDENTITY_REQUIRED")
        identity = dict(identity)
        begun_at = datetime.fromisoformat(claim["begun_at_utc"])
        dispatched = observation.get("dispatched_at_utc")
        limit = datetime.fromisoformat(str(dispatched or observation["observed_at_utc"]).replace("Z", "+00:00"))
        try:
            identity_at = datetime.fromisoformat(str(identity["observed_at_utc"]).replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("NATIVE_NEO_COMPOSED_IDENTITY_REQUIRED") from None
        if not begun_at <= identity_at <= limit:
            raise ValueError("NATIVE_NEO_COMPOSED_IDENTITY_TIME_INVALID")
        expected_stable = SURFACE_REGISTRY[request["surface"]].expected_stable_id
        matched = (identity.get("authenticated") is True
                   and identity.get("observed_identity") == request["expected_identity"]
                   and (not expected_stable or identity.get("observed_stable_id") == expected_stable))
        result = dict(result)
        result["composed_identity"] = identity
        no_write = (result.get("definite_no_write") is True
                    or str(result.get("status") or "").upper() in {"FAILED_BEFORE_WRITE", "DEFINITE_NO_WRITE"})
        stage = result.get("stage")
        if no_write and (dispatched or stage == "PUBLISH_CLICK_ATTEMPTED"):
            # A failure once the click was attempted is never a definite no-write (even if the
            # script threw before recording the dispatch time); read back before any retry.
            result.update(status="UNKNOWN_WRITE", definite_no_write=False, retry_permitted=False,
                          reason_code="NATIVE_NEO_FAILURE_AFTER_PUBLISH_CLICK")
            return result, None
        if no_write and (not matched or stage == "BEFORE_PUBLISH_CLICK"):
            # Stopped before the click (the account did not match, or a pre-write failure the
            # script marked BEFORE_PUBLISH_CLICK): a definite no-write that frees the claim for a retry.
            result.update(status="FAILED_BEFORE_WRITE", definite_no_write=True, public_write_performed=False)
            if not matched:
                result.setdefault("reason_code", "NATIVE_NEO_COMPOSED_IDENTITY_MISMATCH")
            return result, None
        if no_write:
            # A failure without its stage cannot prove the click never happened.
            result.update(status="UNKNOWN_WRITE", definite_no_write=False, retry_permitted=False,
                          reason_code="NATIVE_NEO_COMPOSED_STAGE_UNKNOWN")
            return result, None
        if not matched:
            # A write without a matched account is never trusted as a confirmed post.
            result.update(status="UNKNOWN_WRITE", retry_permitted=False,
                          observed_identity=identity.get("observed_identity"),
                          reason_code="NATIVE_NEO_COMPOSED_IDENTITY_MISMATCH_AFTER_DISPATCH")
            return result, None
        # CC-283, 5 Nov IBM: the X return came back without the composer texts read before the
        # click, so nothing showed that step 3 ran. A write's return must carry them. Refused
        # before saving, so the run can resubmit the texts it read; a run that did not read them
        # submits nothing and the coordinator reads the post back (UNKNOWN_WRITE), never resends.
        posts = composed.get("pre_click_posts")
        if not isinstance(posts, list) or not posts or not all(isinstance(p, str) for p in posts):
            raise ValueError("NATIVE_NEO_PRE_CLICK_POSTS_REQUIRED: return composed.pre_click_posts, the "
                             "composer texts read before the click; if they were not read, submit nothing")
        result["pre_click_verification"] = (
            "MATCHED" if _post_texts(posts) == _post_texts(expected_posts(request)) else "DIFFERED")
        if request.get("destination") == "x" and result["pre_click_verification"] == "DIFFERED":
            from live_contentops.plan_status_posts_v1 import _x_length
            if (all(_x_length(p) <= 280 for p in posts)
                    and _post_texts([" ".join(posts)]) == _post_texts([" ".join(expected_posts(request))])):
                result["pre_click_verification"] = "MATCHED_REFLOWED_THREAD"
        if not dispatched:
            result["click_clock"] = "NOT_RETURNED"
        # CC-199, 5 Nov IBM: no browser return carried its in-run readback (step 5), so each
        # destination waited for a separate readback turn; the last landed 17 min after the last
        # click. The run's own readback confirms the destination; it is used even when the click
        # clock is missing (the post's id exists only after the click).
        readback = composed.get("readback")
        if not isinstance(readback, Mapping) or not (readback.get("public_object_id") or readback.get("status")):
            raise ValueError("NATIVE_NEO_IN_RUN_READBACK_REQUIRED: return composed.readback, the READBACK "
                             "fields observed in this run right after the click (a failed read with its status "
                             "is accepted)")
        result.setdefault("observed_identity", identity["observed_identity"])
        if _incomplete_readback_evidence(request, readback):
            # 5 Nov EIA: X's in-run readback deferred its image comparison (after_run lets media
            # checks wait until every destination is out). Reused at once, it recorded X as
            # CONTENT_INCOMPLETE, which recovery never revisits, so the image was never compared.
            # A pending media check is not a decisive readback: the coordinator asks for the full one.
            result["in_run_readback_media"] = "PENDING_BINARY_COMPARISON"
            return result, None
        return result, dict(readback)

    def _store_composed_readback(self, request, claim, published, readback, observation, response):
        """CC-283: keep the run's readback where the coordinator's 10-minute reuse
        (fresh_readback_request) finds it; the adapter still checks the content as today."""
        from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
        from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
        object_id = published.get("public_object_id") or readback.get("public_object_id")
        object_url = published.get("public_object_url") or readback.get("public_object_url")
        dispatch = self.store.get_platform_dispatch(request["dispatch_attempt_identity"])
        message = self.store.get_outbox_message(dispatch["message_id"]) if dispatch else None
        if not message or not object_id or not object_url:
            return None
        effective = DurablePublicationCoordinator(store=self.store, transport_runtime=None)._effective_message(message)
        value = NeoDestinationHandoff(native_executor=self).request(
            destination=request["destination"], action="READBACK", intent=json.loads(effective["payload"]),
            public_object_id=object_id, public_object_url=object_url)
        packet = {"schema_version": SCHEMA, "operation_id": self.operation_id, "required_tool": TOOL,
                  "request": value, "action_boundary": "BEGIN_BEFORE_TOOL_ACTION; SUBMIT_OBSERVED_RETURN; RESUME_COORDINATOR",
                  "public_write_authorized": False}
        packet["tool_request_sha256"] = sha256_of(packet)
        rb_hash, work = value["request_sha256"], value["work_item_id"]
        self._put(rb_hash, "request", packet, work)
        if self._get(rb_hash, "response") is None:
            self._put(rb_hash, "started", {"tool_request_sha256": packet["tool_request_sha256"],
                "native_invocation_id": self.native_invocation_id, "begun_at_utc": claim["begun_at_utc"],
                "required_tool": TOOL, "composed_with_publish": request["request_sha256"]}, work)
            self._put(rb_hash, "response", {"result": {**readback, "request_sha256": rb_hash,
                "public_object_id": object_id, "public_object_url": object_url,
                "observed_identity": readback.get("observed_identity") or published.get("observed_identity"),
                "composed_with_publish": request["request_sha256"],
                "native_tool_observation": observation, "native_tool_return_sha256": sha256_of(response)}}, work)
        return rb_hash

    def _fresh_identity_return(self, destination, surface, expected_identity, *, expected_stable_id=None):
        # Probe epochs deduplicate requests; actual observation time controls
        # freshness. Crossing a bucket must not discard a seconds-old proof.
        for row in reversed(self.store.list_outbox_messages(destination=DESTINATION)):
            if row["destination"] != DESTINATION:
                continue
            packet = json.loads(row["payload"])
            request = packet.get("request") or {}
            if (packet.get("schema_version") != SCHEMA or packet.get("operation_id") != self.operation_id
                    or request.get("action") != "VERIFY_IDENTITY" or request.get("destination") != destination
                    or request.get("surface") != surface or request.get("expected_identity") != expected_identity
                    or request.get("native_invocation_id") != self.native_invocation_id):
                continue
            returned = self._get(request.get("request_sha256"), "response")
            result = (returned or {}).get("result") or {}
            observation = result.get("native_tool_observation") or {}
            if (result.get("authenticated") is not True or result.get("observed_identity") != expected_identity
                    or (expected_stable_id and result.get("observed_stable_id") != expected_stable_id)
                    or observation.get("native_invocation_id") != self.native_invocation_id):
                continue
            age = self.clock() - datetime.fromisoformat(observation["observed_at_utc"].replace("Z", "+00:00"))
            if timedelta(0) <= age <= timedelta(minutes=5):
                return result
        return None

    def fresh_readback_request(self, request):
        """Keep an exact successful observation across a ten-minute bucket change."""
        ignored = {"request_sha256", "observation_epoch", "native_invocation_id", "latest_dispatch_attempt_at_utc",
                   "supersedes_incomplete_readback_sha256"}
        def public_binding(value):
            # CC-124, 5 Nov: rebuilding the derived delivery receipt changed its hash
            # and repeatedly discarded exact public readbacks. Copy, source-media
            # hashes, identities and every other artifact remain exact bindings.
            clean = json.loads(json.dumps({k: v for k, v in value.items() if k not in ignored}))
            for artifact in clean.get("content_binding", {}).get("artifact_manifest", []):
                if str(artifact.get("path", "")).replace("\\", "/").endswith("/delivery_media_manifest_v1.json"):
                    artifact.pop("sha256", None)
            return clean
        expected = public_binding(request)
        for row in reversed(self.store.list_outbox_messages(destination=DESTINATION)):
            packet = json.loads(row["payload"])
            prior = packet.get("request") or {}
            if (packet.get("schema_version") != SCHEMA or packet.get("operation_id") != self.operation_id
                    or prior.get("action") != "READBACK"
                    or public_binding(prior) != expected):
                continue
            result = (self._get(prior["request_sha256"], "response") or {}).get("result") or {}
            observation = result.get("native_tool_observation") or {}
            absent = _readback_absence_evidence(request, result)
            if (prior.get("latest_dispatch_attempt_at_utc") != request.get("latest_dispatch_attempt_at_utc")
                    and not absent):
                continue
            if (result.get("status") != "SUCCESS" or (result.get("content_verified") is not True and not absent)
                    or _incomplete_readback_evidence(prior, result)
                    or result.get("observed_identity") != request.get("expected_identity")
                    or (not absent and (not result.get("public_object_id") or not result.get("public_object_url")))
                    or (request.get("public_object_id") and result["public_object_id"] != request["public_object_id"])
                    or (request.get("public_object_url") and result["public_object_url"] != request["public_object_url"])):
                continue
            age = self.clock() - datetime.fromisoformat(observation["observed_at_utc"].replace("Z", "+00:00"))
            if timedelta(0) <= age <= timedelta(minutes=10):
                return dict(prior)
        # A deliberately partial post-click return is immutable. Once media
        # checks finish, request fresh read-only evidence immediately instead
        # of reusing that partial return until the next ten-minute bucket.
        refreshed = dict(request)
        previous = self._get(sha256_of(refreshed), "response")
        while previous and _incomplete_readback_evidence(refreshed, previous.get("result") or {}):
            refreshed["supersedes_incomplete_readback_sha256"] = sha256_of(previous)
            previous = self._get(sha256_of(refreshed), "response")
        if refreshed != request:
            refreshed["request_sha256"] = sha256_of(refreshed)
            return refreshed
        return None

    def complete_readback_request(self, request, *, write_absent=False):
        """Retire obsolete unclaimed requests after exact readback or proven absence."""
        ignored = {"request_sha256", "observation_epoch", "native_invocation_id"}
        expected = {k: v for k, v in request.items() if k not in ignored}
        delivered = bool(request.get("public_object_id") and request.get("public_object_url"))
        binding_keys = ("destination", "intent_sha256", "work_item_id", "package_identity",
                        "payload_hash", "expected_identity", "canonical_url")
        for row in self.store.list_outbox_messages(destination=DESTINATION):
            packet = json.loads(row["payload"])
            prior = packet.get("request") or {}
            request_hash = prior.get("request_sha256")
            same_read = (prior.get("action") == "READBACK"
                         and {k: v for k, v in prior.items() if k not in ignored} == expected)
            # CC-124: a newer claim can publish and verify this exact intent while
            # an older unclaimed publish or unidentified read remains in the UI.
            # Retire only that delivered intent, never a claimed write, another
            # revision/account, or a read of a different public object.
            delivered_intent = (delivered and bool(request.get("intent_sha256"))
                and prior.get("action") in {"PUBLISH", "READBACK"}
                and all(prior.get(k) == request.get(k) for k in binding_keys)
                and prior.get("public_object_id") in {None, request["public_object_id"]}
                and prior.get("public_object_url") in {None, request["public_object_url"]})
            absent_intent = (write_absent and bool(request.get("intent_sha256"))
                and prior.get("action") == "READBACK"
                and not prior.get("public_object_id") and not prior.get("public_object_url")
                and all(prior.get(k) == request.get(k) for k in binding_keys)
                and prior.get("latest_dispatch_attempt_at_utc") == request.get("latest_dispatch_attempt_at_utc"))
            if (packet.get("schema_version") != SCHEMA or packet.get("operation_id") != self.operation_id
                    or request_hash == request["request_sha256"] or not (same_read or delivered_intent or absent_intent)
                    or self._get(request_hash, "response") or self._get(request_hash, "started")):
                continue
            self.store.set_outbox_status(row["message_id"], "NATIVE_NEO_SUPERSEDED")

    def readiness(self, surface):
        from live_contentops.destination_transport_registry_v1 import SURFACE_REGISTRY
        from live_contentops.neo_destination_handoff_v1 import IDENTITIES, ROOTS
        registration = SURFACE_REGISTRY[surface]
        destination = registration.destination_key
        work = "native-neo-operation-" + sha256_of(self.operation_id)
        self.store.create_work_item(story_id=work, work_item_id=work,
                                   title="Native Neo exact identity observation", target_surface="CONTENTOPS_READ_ONLY")
        request = {"schema_version": "contentops.neo_identity_probe.v1", "destination": destination,
                   "probe_epoch": int(self.clock().timestamp()) // 300,
                   "native_invocation_id": self.native_invocation_id,
                   "action": "VERIFY_IDENTITY", "surface": surface, "expected_identity": IDENTITIES[destination],
                   "entry_url": ROOTS[destination], "work_item_id": work,
                   "forbidden": ["login", "account_switch", "public_write", "saved_draft", "private_storage"]}
        if registration.expected_stable_id:
            request["expected_stable_id"] = registration.expected_stable_id
        request["request_sha256"] = sha256_of(request)
        result = self._fresh_identity_return(destination, surface, IDENTITIES[destination],
            expected_stable_id=registration.expected_stable_id)
        if result is None:
            prior = self._get(request["request_sha256"], "response")
            while prior and prior["result"].get("authenticated") is not True:
                # An absent/incomplete read-only observation is not a five-minute
                # session failure. Preserve it and bind a fresh actual observation.
                request["prior_identity_return_sha256"] = sha256_of(prior)
                request["request_sha256"] = sha256_of({k: v for k, v in request.items()
                    if k != "request_sha256"})
                prior = self._get(request["request_sha256"], "response")
            result = self(request)
        observed = result.get("native_tool_observation") or {}
        age = self.clock() - datetime.fromisoformat(observed["observed_at_utc"].replace("Z", "+00:00"))
        current = (observed.get("native_invocation_id") == self.native_invocation_id
                   and timedelta(0) <= age <= timedelta(minutes=5))
        matched = (result.get("observed_identity") == IDENTITIES[destination]
            and (not registration.expected_stable_id or result.get("observed_stable_id") == registration.expected_stable_id))
        return {"authenticated": bool(current and matched and result.get("authenticated") is True),
                "native_executor_bound": current, "domain": result.get("observed_identity") if destination == "substack" else None,
                "public_handle": result.get("observed_identity") if destination != "substack" else None,
                "stable_id": result.get("observed_stable_id"),
                "native_invocation_id": observed.get("native_invocation_id"),
                "observation_sha256": result.get("native_tool_return_sha256"), "proof_fresh": current}

    def pending(self):
        from live_contentops.destination_transport_registry_v1 import barred_browser_destinations
        rows = []
        for row in self.store.list_outbox_messages(destination=DESTINATION):
            if row["destination"] != DESTINATION:
                continue
            if row["status"] == "NATIVE_NEO_SUPERSEDED":
                continue
            payload = json.loads(row["payload"])
            if payload.get("schema_version") != SCHEMA or payload.get("operation_id") != self.operation_id:
                continue
            if payload["request"].get("destination") in barred_browser_destinations():
                continue  # Decision 109 retires the entire X browser agent route.
            absence = payload["request"].get("owner_absence_context")
            if payload["request"]["action"] == "READBACK" and absence:
                prior = self.store.get_platform_dispatch(absence.get("dispatch_id", "")) or {}
                if prior and prior.get("status") != "UNKNOWN_WRITE":
                    continue
            if (payload["request"]["action"] == "VERIFY_IDENTITY"
                    and payload["request"].get("native_invocation_id") not in {None, self.native_invocation_id}):
                continue
            request_hash = payload["request"]["request_sha256"]
            if self._get(request_hash, "response") is None:
                claim = (self._get(request_hash, "started") if payload["request"]["action"] in {"PUBLISH", "EDIT_EXISTING"}
                         else self._claim(request_hash, self.native_invocation_id))
                rows.append({**payload, "action_claimed": claim is not None})
        return rows


def bind_native_neo_coordinator(store, *, operation_id, output_dir, native_invocation_id,
                                allow_publish=False, automatic=False, endpoint_client=None):
    """One concrete supported composition; existing API routes and sole owner are reused."""
    from live_contentops.destination_transport_registry_v1 import DestinationReadinessManager
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    from live_contentops.publication_coordinator_v1 import (
        CanonicalDestinationTransportRuntimeV1, DurablePublicationCoordinator,
    )
    executor_type = NativeNeoExecutor
    options = {}
    if automatic:
        from live_contentops.neo_endpoint_executor_v1 import EndpointNeoExecutor
        executor_type = EndpointNeoExecutor
        options["client"] = endpoint_client
    executor = executor_type(store, operation_id=operation_id, output_dir=output_dir,
                                 native_invocation_id=native_invocation_id, allow_publish=allow_publish,
                                 identity_at_action=allow_publish, **options)
    runtime = CanonicalDestinationTransportRuntimeV1(neo_transport=NeoDestinationHandoff(native_executor=executor, store=store))
    readiness = DestinationReadinessManager(store=store, neo_readiness_provider=executor.publication_readiness)
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime, readiness_manager=readiness)
    return coordinator, executor
