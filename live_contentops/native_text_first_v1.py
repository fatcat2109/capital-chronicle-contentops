"""Decision 37 B2 policy over the existing native writer, compiler and publisher.

No source acquisition, model, store, scheduler or transport owner lives here.
"""
from __future__ import annotations

import json
import re

from live_contentops.capital_chronicle_latest_report_consumer_v1 import _private, sha256_of

POLICY_ID = "JIM_DECISION_37_B2_TEXT_FIRST"
BRIEF_MODES = {"BREAKING_BRIEF", "FOLLOW_UP_UPDATE"}
DESTINATIONS = {"substack", "x", "telegram", "discord", "threads", "linkedin"}
MAX_WORDS = 500
SKIPPED_IMAGE = "SKIPPED_TEXT_FIRST_INSTAGRAM_IMAGE_REQUIRED"
SKIPPED_CHANNEL = "SKIPPED_TEXT_FIRST_CHANNEL_NOT_SELECTED"


def writer_policy(governed):
    if governed.get("article_mode") not in BRIEF_MODES or not governed.get("source_pack"):
        return None
    return {"policy_id": POLICY_ID, "article_mode": governed["article_mode"],
        "source_pack_sha256": sha256_of(governed["source_pack"])}


def _check_copy(article):
    from live_contentops.v1_simple_gemini_newsroom_v1 import _public_copy
    copy = _public_copy(article)
    if (article.get("news_item_kind") not in {"NEWS", "POLICY"}
            or not 1 <= len(str(article.get("substack_body_markdown") or "").split()) <= MAX_WORDS):
        raise ValueError("TEXT_FIRST_SHORT_NEWS_POLICY_REQUIRED")
    if (_private(article) or re.search(
            r"\b(?:demo|mt5|guardian|account\s+(?:id|balance)|entry\s+(?:price|at)|stop[- ]loss|take[- ]profit|position\s+size)\b"
            r"|\b(?:buy|sell|go\s+long|go\s+short)\s+(?:at|above|below|now)\b",
            copy, re.I)):
        raise ValueError("TEXT_FIRST_PUBLIC_OUTPUT_GUARD")
    if "Analysis, not financial advice. Readers decide whether to trade." not in copy:
        raise ValueError("TEXT_FIRST_PUBLIC_ANALYSIS_NOTICE_REQUIRED")
    return copy


def bind_validated_article(article, *, request, source_pack, validation, optional_input_gaps=()):
    """Only code after the ordinary source/claim check can attach this marker."""
    policy = request.get("governed_input", {}).get("text_first_policy")
    if not policy:
        return article
    expected = writer_policy(request["governed_input"])
    if (policy != expected or policy["source_pack_sha256"] != sha256_of(source_pack)
            or validation.get("status") != "PASS" or validation.get("unsupported_material_claim_count") != 0):
        raise ValueError("TEXT_FIRST_FACT_CHECK_REQUIRED")
    copy = _check_copy(article)
    return {**article, "text_first": {**policy, "story_kind": article["news_item_kind"],
        "writer_request_sha256": request["request_sha256"], "public_copy_sha256": sha256_of(copy),
        "validation_sha256": sha256_of(validation), "optional_input_gaps": list(optional_input_gaps)}}


def text_first_brief(result):
    article = result.get("article") or result
    marker = article.get("text_first")
    if not marker:
        return False
    mode = article.get("resolved_article_mode") or article.get("effective_article_mode") or marker.get("article_mode")
    if (marker.get("policy_id") != POLICY_ID or marker.get("article_mode") != mode
            or mode not in BRIEF_MODES or marker.get("story_kind") not in {"NEWS", "POLICY"}):
        raise ValueError("TEXT_FIRST_POLICY_BINDING_INVALID")
    return True


def skipped_destinations(*, has_image=False):
    return [{"destination": destination, "status": status, "disposition": status, "reason": reason}
        for destination, status, reason in (
            ("instagram_business", SKIPPED_CHANNEL if has_image else SKIPPED_IMAGE,
             "Instagram is outside the six text-first destinations." if has_image else
             "Instagram requires an image; this text-first item has no admitted image."),
            ("facebook_page", SKIPPED_CHANNEL, "Facebook Page is outside the six text-first destinations."),
            ("youtube", SKIPPED_CHANNEL, "YouTube Community is outside the six text-first destinations."))]


def permitted_skips(plan):
    if not plan.get("text_first") or not text_first_brief(plan):
        return set()
    expected = skipped_destinations(has_image=bool(plan.get("media_asset_count")))
    actual = plan.get("skipped_derivative_destinations") or []
    if sorted(actual, key=lambda s: s["destination"]) != sorted(expected, key=lambda s: s["destination"]):
        return set()
    return {s["destination"] for s in expected}


def fact_checked_acceptance(store, *, run_id, result):
    """Recheck the exact native return at every fresh write; no pixels are asserted."""
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
    from live_contentops.native_desktop_workspace_v1 import resolve_workspace_path
    from live_contentops.v1_simple_gemini_newsroom_v1 import (
        _normalize_relay_attribution, _validate_article_against_source_pack, _public_copy,
        SimpleGeminiNewsroomError,
    )
    row = store.get_outbox_message("native-operation-binding-" + sha256_of(run_id))
    binding = json.loads(row["payload"]) if row else {}
    turn = NativeDesktopTurn(store, run_id=run_id,
        output_dir=resolve_workspace_path(binding["output_dir"]), owner_manual_validation=True)
    request = turn.frozen_request("write")
    stage = "revise" if result.get("simple_result", {}).get("revision_performed") else "write"
    response = turn._get(stage, "response")
    if not request or not response or response["request_sha256"] != turn.frozen_request(stage)["request_sha256"]:
        raise ValueError("TEXT_FIRST_EXACT_NATIVE_WRITER_REQUIRED")
    governed = request["governed_input"]
    output, _ = _normalize_relay_attribution(response["output"], governed.get("epistemic_state"))
    try:
        article, validation = _validate_article_against_source_pack(output, governed["source_pack"],
            selected_candidate=governed.get("selected_candidate"), article_mode=governed["article_mode"],
            epistemic_state=governed.get("epistemic_state"))
    except SimpleGeminiNewsroomError as exc:
        raise ValueError("TEXT_FIRST_FACT_CHECK_FAILED:" + str(exc)) from exc
    checked = bind_validated_article(article, request=request, source_pack=governed["source_pack"],
        validation=validation, optional_input_gaps=result["article"]["text_first"].get("optional_input_gaps", []))
    if (checked.get("text_first") != result["article"]["text_first"]
            or _public_copy(checked) != _public_copy(result["article"])
            or sha256_of(result.get("evidence")) != sha256_of(governed["source_pack"])):
        raise ValueError("TEXT_FIRST_FACT_CHECK_BINDING_CHANGED")
    _check_copy(result["article"])
    return {"review_type": "TEXT_FIRST_FACT_CHECKED_NO_RENDER_REVIEW", "policy_id": POLICY_ID,
        "public_copy_sha256": checked["text_first"]["public_copy_sha256"], "pixels_inspected": False}
