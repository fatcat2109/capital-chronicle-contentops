"""CC-172 policy over existing article reviews, outbox and transport observations.

No timer, scheduler or publication owner. Missing send observations stay unknown.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of

POLICY = "CC-172"
MAX_VISUAL_REPAIRS = 1
DISPATCH_MINUTES = 15
SPEED_POLICY = "JIM_DECISION_53"
TIME_SENSITIVE_MODES = {"BREAKING_BRIEF", "FOLLOW_UP_UPDATE", "STANDARD_NEWS_ANALYSIS", "DATA_OR_DOCUMENT_LENS"}
LONG_FORM_MODES = {"EVERGREEN_EXPLAINER", "CAPITAL_CHRONICLE_VIEW", "WHAT_THE_MARKET_IS_MISSING", "WEEK_AHEAD_OR_WATCH"}
TIMING_DESTINATION = "internal:native-publication-timing"


def text_revision(result):
    # Presentation choices must not restart the text approval clock.
    article = result["article"]
    from live_contentops.v1_simple_gemini_newsroom_v1 import _public_copy
    return sha256_of([result["article_identity"], _public_copy(article),
        {k: v for k, v in article.items() if k.startswith("social_") or k == "conditional_calls"}])


def speed_policy(governed):
    """Freeze the short path in new writer requests; preserve already-issued ones."""
    if governed.get("article_mode") in LONG_FORM_MODES:
        return None
    if governed.get("article_mode") in TIME_SENSITIVE_MODES or governed.get("selected_candidate", {}).get("event_id"):
        return {"policy": SPEED_POLICY, "dispatch_target_minutes": DISPATCH_MINUTES,
            "path": "WRITER_ONE_EDITOR_CHECK_PUBLISH", "post_text_visual_review": "AUTOMATED_LOAD_SIZE_LOG_ONCE"}
    return None


def uses_short_path(store, *, run_id, result):
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
    row = store.get_outbox_message("native-operation-binding-" + sha256_of(run_id))
    binding = json.loads(row["payload"]) if row else {}
    if not binding:
        return False
    adopted = store.get_outbox_message("native-approved-text-speed-" + sha256_of(run_id))
    if adopted:
        basis = json.loads(adopted["payload"])
        if (text_revision(result) != basis["text_revision_sha256"]
                or sha256_of(result["evidence"]) != basis["source_sha256"]):
            raise ValueError("APPROVED_TEXT_SOURCE_OR_COPY_CHANGED")
        # A reviewed media replacement keeps the first text approval. Validate
        # that approval against its original article, not new media metadata.
        from live_contentops.native_desktop_editorial_v1 import native_artifact_key
        original = store.get_outbox_message(native_artifact_key(store, run_id, "cc-editorial-final-"))
        return bool(original and _approved_text_speed_basis(store, run_id=run_id,
            result=json.loads(original["payload"])) == basis)
    turn = NativeDesktopTurn(store, run_id=run_id, output_dir=binding["output_dir"], owner_manual_validation=True)
    request = turn.frozen_request("write") or {}
    policy = request.get("governed_input", {}).get("publication_speed_policy")
    return bool(policy and policy == speed_policy(request["governed_input"]))


def _approved_text_speed_basis(store, *, run_id, result):
    """Apply the current policy to unchanged, previously accepted native text.

    Frozen writer requests and returns stay untouched. This is not new writing,
    a source refresh, or permission to accept a changed article under an old KEEP.
    """
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, validate_native_configuration, ROLE_ASSIGNMENTS
    from live_contentops.v1_simple_gemini_newsroom_v1 import _public_copy
    from live_contentops.contentops_editorial_desk_v1 import read_reviews
    binding_row = store.get_outbox_message("native-operation-binding-" + sha256_of(run_id))
    binding = json.loads(binding_row["payload"]) if binding_row else {}
    turn = NativeDesktopTurn(store, run_id=run_id, output_dir=binding["output_dir"], owner_manual_validation=True)
    stage = "revise" if result.get("simple_result", {}).get("revision_performed") else "write"
    request, response = turn.frozen_request(stage), turn._get(stage, "response")
    if not request or not response or response["request_sha256"] != request["request_sha256"]:
        raise ValueError("APPROVED_TEXT_EXACT_NATIVE_WRITER_REQUIRED")
    validate_native_configuration(response["invocation_observation"], ROLE_ASSIGNMENTS["write"])
    if stage == "revise":
        writer = turn._get("write", "response")
        if (not writer or writer["invocation_observation"].get("invocation_id")
                != response["invocation_observation"].get("invocation_id")):
            raise ValueError("APPROVED_TEXT_SAME_NATIVE_WRITER_REQUIRED")
    governed = request["governed_input"]
    event = result["article"].get("event_article")
    # A short upcoming-event NEWS preview may use the current event path without
    # rewriting its already-issued WEEK_AHEAD_OR_WATCH request or original KEEP.
    short_event_preview = (governed.get("article_mode") == "WEEK_AHEAD_OR_WATCH"
        and (governed.get("visual_editorial_decision") or {}).get("story_kind") == "NEWS"
        and result["article"].get("news_item_kind") == "NEWS"
        and len(result["article"].get("substack_body_markdown", "").split()) <= 500)
    if (governed.get("article_mode") not in TIME_SENSITIVE_MODES and not event and not short_event_preview
            or sha256_of(result["evidence"]) != sha256_of(governed["source_pack"])
            or _public_copy(response["output"]["article"]) != _public_copy(result["article"])
            or any(result["article"].get(k) != v for k, v in response["output"]["article"].items()
                   if k.startswith("social_"))):
        raise ValueError("APPROVED_TEXT_SOURCE_OR_COPY_CHANGED")
    rows = read_reviews(store)
    approved = [r for r in rows if r["reviewer_ref"] == "NATIVE_DESKTOP_ARTICLE_REVIEW"
        and (n := json.loads(r["notes"])).get("run_id") == run_id]
    if not approved or approved[-1]["decision"] != "KEEP":
        raise ValueError("APPROVED_TEXT_EXISTING_KEEP_REQUIRED")
    exact = [r for r in approved if r["decision"] == "KEEP"
        and json.loads(r["notes"]).get("article_metadata_sha256") == sha256_of(result["article"])]
    if not exact:
        raise ValueError("APPROVED_TEXT_EXISTING_EXACT_COPY_REQUIRED")
    return {"policy": SPEED_POLICY, "run_id": run_id, "base_result_sha256": sha256_of(result),
        "article_metadata_sha256": sha256_of(result["article"]), "text_revision_sha256": text_revision(result),
        "original_approval_clock_utc": min(r["reviewed_at"] for r in exact),
        "source_sha256": sha256_of(result["evidence"]), "native_writer_response_sha256": sha256_of(response),
        "public_write_performed": False}


def adopt_approved_text_speed_policy(store, *, run_id):
    from live_contentops.native_desktop_editorial_v1 import native_artifact_key
    row = store.get_outbox_message(native_artifact_key(store, run_id, "cc-editorial-final-"))
    result = json.loads(row["payload"]) if row else {}
    value = _approved_text_speed_basis(store, run_id=run_id, result=result)
    store.register_outbox_message(message_id="native-approved-text-speed-" + sha256_of(run_id),
        work_item_id=row["work_item_id"], destination="internal:native-publication-policy",
        payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")
    return value


def automated_media_check(result):
    """One local decode/dimension check logged by KEEP; never pixel judgment."""
    from PIL import Image
    from live_contentops.native_desktop_workspace_v1 import resolve_workspace_path
    checks = []
    for asset in result.get("media_assets", []):
        finding = {"asset_id": asset["asset_id"], "sha256": asset["sha256"], "pixels_inspected": False}
        try:
            with Image.open(resolve_workspace_path(asset["path"])) as image:
                size = image.size
                image.load()
            expected = (asset.get("width"), asset.get("height"))
            bound_size = all(type(v) is int and v > 0 for v in expected)
            match = bound_size and size == expected
            finding.update(loads=True, width=size[0], height=size[1], expected_dimensions=list(expected),
                right_size=match, status="PASS" if match else
                "DIMENSIONS_MISMATCH" if bound_size else "EXPECTED_DIMENSIONS_NOT_BOUND")
        except (OSError, ValueError) as exc:
            finding.update(loads=False, right_size=False, status="IMAGE_LOAD_FAILED", error_class=type(exc).__name__)
        checks.append(finding)
    return {"policy": SPEED_POLICY, "check": "IMAGE_LOAD_AND_SIZE_ONCE", "findings": checks,
        "failures_logged_no_repair_loop": sum(c["status"] != "PASS" for c in checks), "blocks_publication": False}


def short_path_acceptance(store, *, run_id, result, review):
    """The ordinary revision-bound KEEP is the one editor check."""
    note = json.loads(review["notes"])
    if note.get("publication_speed_policy", {}).get("policy") != SPEED_POLICY or not note.get("automated_media_check"):
        raise ValueError("ONE_EDITOR_CHECK_REQUIRED")
    adopted = store.get_outbox_message("native-approved-text-speed-" + sha256_of(run_id))
    if adopted:
        basis = _approved_text_speed_basis(store, run_id=run_id, result=result)
        if basis != json.loads(adopted["payload"]):
            raise ValueError("APPROVED_TEXT_POLICY_BINDING_CHANGED")
        return {"review_type": "WRITER_ONE_EDITOR_CHECK_PUBLISH", "policy_id": SPEED_POLICY,
            "review_id": review["review_id"], "text_approved_at_utc": basis["original_approval_clock_utc"],
            "automated_media_check": note["automated_media_check"], "pixels_inspected": False}
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn, validate_native_configuration, ROLE_ASSIGNMENTS
    from live_contentops.v1_simple_gemini_newsroom_v1 import (
        _normalize_relay_attribution, _validate_article_against_source_pack, _public_copy,
        SimpleGeminiNewsroomError,
    )
    row = store.get_outbox_message("native-operation-binding-" + sha256_of(run_id))
    binding = json.loads(row["payload"])
    turn = NativeDesktopTurn(store, run_id=run_id, output_dir=binding["output_dir"], owner_manual_validation=True)
    request = turn.frozen_request("write")
    stage = "revise" if result.get("simple_result", {}).get("revision_performed") else "write"
    response, exact = turn._get(stage, "response"), turn.frozen_request(stage)
    if not request or not exact or not response or response["request_sha256"] != exact["request_sha256"]:
        raise ValueError("SHORT_PATH_EXACT_NATIVE_WRITER_REQUIRED")
    validate_native_configuration(response["invocation_observation"], ROLE_ASSIGNMENTS["write"])
    governed = request["governed_input"]
    if sha256_of(result["evidence"]) != sha256_of(governed["source_pack"]):
        raise ValueError("SHORT_PATH_FACT_SOURCE_CHANGED")
    from live_contentops.native_text_first_v1 import text_first_brief, fact_checked_acceptance
    if text_first_brief(result):
        fact_checked_acceptance(store, run_id=run_id, result=result)
    else:
        output, _ = _normalize_relay_attribution(response["output"], governed.get("epistemic_state"))
        try:
            checked, _ = _validate_article_against_source_pack(output, governed["source_pack"],
                selected_candidate=governed.get("selected_candidate"), article_mode=governed["article_mode"],
                epistemic_state=governed.get("epistemic_state"))
        except SimpleGeminiNewsroomError as exc:
            raise ValueError("SHORT_PATH_FACT_CHECK_FAILED:" + str(exc)) from exc
        if _public_copy(checked) != _public_copy(result["article"]):
            raise ValueError("SHORT_PATH_FACT_CHECKED_COPY_CHANGED")
    return {"review_type": "WRITER_ONE_EDITOR_CHECK_PUBLISH", "policy_id": SPEED_POLICY,
        "review_id": review["review_id"], "text_approved_at_utc": note["text_approved_at_utc"],
        "automated_media_check": note["automated_media_check"], "pixels_inspected": False}


def validate_publication_media(store, *, run_id, result):
    from live_contentops.native_desktop_editorial_v1 import validate_release_media
    from live_contentops.rolling_x_grounded_article_media_builder_v1 import post_image_view
    from live_contentops.native_desktop_workspace_v1 import resolve_workspace_path
    short_path = uses_short_path(store, run_id=run_id, result=result)
    row = store.get_outbox_message("native-operation-binding-" + sha256_of(run_id))
    binding = json.loads(row["payload"]) if row else {}
    if binding.get("output_dir"):
        result = post_image_view(result, output_dir=resolve_workspace_path(binding["output_dir"]) / "media" / "post-images")
    return validate_release_media(result, require_pixel_review=not short_path)


def attach_photo_credits(assets):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _publication_media_metadata
    return [{**a, "canonical_photo_credit": _publication_media_metadata([a], compact=True)[1]}
        if a.get("modality") == "documentary_photo" else a for a in assets]


def text_approval(reviews, *, run_id, article_identity, revision=None):
    candidates = []
    for row in reviews:
        note = json.loads(row["notes"])
        if (row["reviewer_ref"] != "NATIVE_DESKTOP_ARTICLE_REVIEW" or row["decision"] != "KEEP"
                or note.get("run_id") != run_id or note.get("article_identity") != article_identity):
            continue
        if revision and note.get("text_revision_sha256") != revision:
            continue
        clock = note.get("text_approved_at_utc") or row.get("reviewed_at")
        if clock:
            candidates.append(clock)
    return min(candidates, key=_utc) if candidates else None


def _utc(value):
    clock = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if clock.tzinfo is None:
        raise ValueError("PUBLICATION_TIMING_UTC_REQUIRED")
    return clock.astimezone(timezone.utc)


def failed_asset_ids(output):
    return {f["asset_id"] for f in output["asset_findings"]
        if not f["pixels_inspected"] or f["findings"]
        or any(v in {"FAIL", "UNVERIFIED"} for v in f["checks"].values())}


def visual_repair_disposition(result, assets, *, response, reference, drop_failed=False):
    prior = result.get("visual_repair_disposition") or {}
    rounds = prior.get("repair_rounds", 0)
    failed = failed_asset_ids(response["output"])
    if drop_failed:
        if rounds != MAX_VISUAL_REPAIRS or not failed:
            raise ValueError("ONE_VISUAL_REPAIR_THEN_EXACT_FAILED_ASSETS_REQUIRED")
        assets = [a for a in result["media_assets"] if a["asset_id"] not in failed]
        dropped = [{"asset_id": f["asset_id"], "sha256": f["asset_sha256"],
            "findings": f["findings"], "checks": f["checks"],
            "review_request_sha256": reference["request_sha256"]}
            for f in response["output"]["asset_findings"] if f["asset_id"] in failed]
        return assets, {"policy": POLICY, "repair_rounds": rounds,
            "dropped_assets": [*prior.get("dropped_assets", []), *dropped]}
    if rounds >= MAX_VISUAL_REPAIRS:
        raise ValueError("VISUAL_REPAIR_CAP_DROP_FAILED_ASSETS_REQUIRED")
    return assets, {"policy": POLICY, "repair_rounds": rounds + 1,
        "dropped_assets": prior.get("dropped_assets", [])}


def record_api_dispatch(store, *, intent, destination, dispatch_id, started_at, status):
    """Called after the transport call, never for a merely pending Neo request."""
    if not store.get_outbox_message("native-operation-binding-" + sha256_of(intent["work_item_id"])):
        return
    value = {"policy": POLICY, "run_id": intent["work_item_id"], "destination": destination,
        "dispatch_id": dispatch_id, "attempted_at_utc": started_at,
        "returned_at_utc": datetime.now(timezone.utc).isoformat(), "status": status,
        "dispatched_at_utc": started_at if status == "DISPATCH_CONFIRMED" else None,
        "timing_basis": "API_TRANSPORT_CALL"}
    store.register_outbox_message(message_id="native-dispatch-timing-" + sha256_of(value),
        work_item_id=intent["work_item_id"], destination=TIMING_DESTINATION,
        payload=canonical_bytes(value).decode(), status="EDITORIAL_INTERNAL")


def publication_timing(rows, reviews, *, run_id, destinations, now=None):
    own = [r for r in reviews
        if r["reviewer_ref"] == "NATIVE_DESKTOP_ARTICLE_REVIEW"
        and json.loads(r["notes"]).get("run_id") == run_id]
    latest = json.loads(own[-1]["notes"]) if own and own[-1]["decision"] == "KEEP" else {}
    approved = text_approval(reviews, run_id=run_id, article_identity=latest.get("article_identity"),
        revision=latest.get("text_revision_sha256")) if latest.get("text_revision_sha256") else None
    deadline = _utc(approved) + timedelta(minutes=DISPATCH_MINUTES) if approved else None
    observations = []
    packets, claims, responses = {}, {}, {}
    for row in rows:
        if row["destination"] == TIMING_DESTINATION:
            value = json.loads(row["payload"])
            if value.get("run_id") == run_id:
                observations.append(value)
        elif row["destination"] == "internal:native-neo-tool":
            value = json.loads(row["payload"])
            if value.get("operation_id") == run_id and value.get("request", {}).get("action") == "PUBLISH":
                packets[value["request"]["request_sha256"]] = value["request"]
    for request_hash, request in packets.items():
        keys = {kind: "native-neo-" + sha256_of([run_id, request_hash, kind]) for kind in ("started", "response")}
        for row in rows:
            if row["message_id"] == keys["started"]:
                claims[request_hash] = json.loads(row["payload"])
            elif row["message_id"] == keys["response"]:
                responses[request_hash] = json.loads(row["payload"])["result"]
        claim, response = claims.get(request_hash, {}), responses.get(request_hash, {})
        observation = response.get("native_tool_observation") or {}
        sent = (observation.get("dispatched_at_utc") or observation.get("observed_at_utc")) if response.get("status") == "SUCCESS" else None
        observations.append({"destination": request["destination"],
            "attempted_at_utc": claim.get("begun_at_utc"), "dispatched_at_utc": sent,
            "status": response.get("status", "PENDING_NATIVE_RETURN"),
            "timing_basis": "NATIVE_ACTION_OBSERVED" if observation.get("dispatched_at_utc") else "NATIVE_RETURN_OBSERVED_UPPER_BOUND"})
    channels = []
    for entry in destinations:
        actual = [v for v in observations if v["destination"] == entry["destination"]]
        sent = sorted((v for v in actual if v.get("dispatched_at_utc")), key=lambda v: _utc(v["dispatched_at_utc"]))
        chosen = sent[0] if sent else actual[-1] if actual else {}
        clock = chosen.get("dispatched_at_utc")
        elapsed = (_utc(clock) - _utc(approved)).total_seconds() if clock and approved else None
        channels.append({"destination": entry["destination"], "status": entry["status"],
            "attempted_at_utc": chosen.get("attempted_at_utc"), "dispatched_at_utc": clock,
            "timing_basis": chosen.get("timing_basis"), "seconds_after_text_approval": elapsed,
            "within_target": 0 <= elapsed <= DISPATCH_MINUTES * 60 if elapsed is not None else None,
            "skipped": entry["status"].startswith("SKIPPED_")})
    required = [c for c in channels if not c["skipped"]]
    complete = bool(required) and all(c["within_target"] is True for c in required)
    overdue = bool(deadline and (now or datetime.now(timezone.utc)) > deadline and not complete)
    return {"policy": SPEED_POLICY, "target_minutes": DISPATCH_MINUTES, "text_approved_at_utc": approved,
        "dispatch_deadline_utc": deadline.isoformat() if deadline else None,
        "channels": channels, "all_channels_dispatched_within_target": complete,
        "state": "WITHIN_15_MINUTES" if complete else "OVERDUE_CONTINUE_PUBLICATION" if overdue
            else "DISPATCH_NOW" if approved else "TEXT_APPROVAL_NOT_OBSERVED"}
