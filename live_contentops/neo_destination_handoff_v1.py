"""Scoped Neo native request/readback adapter used only by the durable coordinator.

No login, browser storage access, selector guessing or publication is performed by preparing
requests. A supported native MCP executor can be supplied by the active Desktop operation;
absence is a definite pre-write block. This is not an alternate publication coordinator.
"""
from __future__ import annotations

import json
import os
import re
from hashlib import sha256
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, unquote

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of, _private

SCHEMA = "contentops.neo_destination_handoff.v1"
IDENTITIES = {"substack": "capitalchronicle.substack.com", "x": "@Capitalnicle",
              "youtube": "@CapitalChronicleYouTube", "linkedin": "linkedin:jimcc",
              "linkedin_company": "linkedin:company:143198922", "instagram_business": "official.capitalchronicle",
              "telegram": "@CapitalChronicle", "threads": "official.capitalchronicle"}
ROOTS = {"substack": "https://capitalchronicle.substack.com/", "x": "https://x.com/Capitalnicle",
         "youtube": "https://www.youtube.com/@CapitalChronicleYouTube/posts",
         "linkedin": "https://www.linkedin.com/in/jimcc/recent-activity/all/",
          "linkedin_company": "https://www.linkedin.com/company/143198922/admin/page-posts/published/",
          "instagram_business": "https://www.instagram.com/official.capitalchronicle/",
          "telegram": "https://t.me/CapitalChronicle",
          "threads": "https://www.threads.com/@official.capitalchronicle"}


def _canonical(url):
    p = urlsplit(str(url or ""))
    return p.scheme == "https" and p.hostname == IDENTITIES["substack"] and p.path.startswith("/p/") and not p.query and not p.fragment


def _social_canonical(url):
    """The preview site's exact article path is also a permitted social target."""
    p = urlsplit(str(url or ""))
    return _canonical(url) or bool(p.scheme == "https" and p.hostname == "fatcat2109.github.io"
        and not p.username and not p.password and not p.query and not p.fragment
        and re.fullmatch(r"/capital-chronicle-preview/articles/[0-9a-f]{32}/", p.path))


def _public_url(destination, url, object_id=None):
    p = urlsplit(str(url or ""))
    if p.scheme != "https" or p.query or p.fragment:
        return False
    if destination == "substack":
        return _canonical(url)
    if destination == "x":
        return (p.hostname in {"x.com", "www.x.com"} and re.fullmatch(r"/Capitalnicle/status/\d+", p.path, re.I)
                and (not object_id or p.path.rsplit("/", 1)[-1] == str(object_id)))
    if destination in {"linkedin", "linkedin_company"}:
        match = re.fullmatch(r"/feed/update/(urn:li:(?:activity|share|ugcPost):\d+)/?", unquote(p.path))
        return bool(p.hostname == "www.linkedin.com" and match
            and (not object_id or match[1] == str(object_id)))
    if destination == "instagram_business":
        return p.hostname == "www.instagram.com" and bool(re.fullmatch(r"/p/[A-Za-z0-9_-]+/", p.path))
    if destination == "telegram":
        return (p.hostname == "t.me" and bool(re.fullmatch(r"/CapitalChronicle/\d+", p.path))
                and (not object_id or p.path.rsplit("/", 1)[-1] == str(object_id)))
    if destination == "threads":
        return (p.hostname in {"www.threads.com", "www.threads.net"}
                and bool(re.fullmatch(r"/@official\.capitalchronicle/post/[A-Za-z0-9_-]+/?", p.path)))
    return (p.hostname == "www.youtube.com" and p.path.startswith("/post/")
            and (not object_id or p.path.rsplit("/", 1)[-1] == str(object_id)))


def _text(value):
    # Browser rendering removes common Markdown syntax; it does not change the proposition.
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(value or ""))
    # Substack's smart punctuation changes apostrophe/quote glyphs on the same
    # published copy. Keep numbers, minus signs, words and order exact.
    value = value.translate(str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'}))
    return " ".join(re.sub(r"[#*_`]", "", value).split())


def _x_reader_text(value, links, public_object_url, canonical):
    text = _text(value)
    for link in links:
        displayed = _text(link.get("displayed_text"))
        if (displayed and displayed in text
                and re.fullmatch(r"https://t\.co/[A-Za-z0-9]+", str(link.get("short_url") or ""))
                and link.get("target_verified") is True
                and link.get("public_object_url") == public_object_url
                and link.get("target_url") == canonical and _social_canonical(canonical)):
            text = text.replace(displayed, _text(canonical))
    return text


def _x_thread_matches(binding, thread, links, canonical):
    expected = binding["expected_thread_texts"]
    if len(thread) < len(expected) or len({p.get("public_object_id") for p in thread}) != len(thread):
        return False
    # A partial reply can be completed in the same thread when the platform has
    # no edit control. Extra text must be a complete fragment of approved copy;
    # all full approved posts must still be present in their original order.
    fragments = {_text(part) for text in expected
        for part in re.split(r"\n+|(?<=[.!?])\s+", text)
        if _text(part) and _text(part) != _text(text)}
    index = 0
    for post in thread:
        url, object_id = post.get("public_object_url"), post.get("public_object_id")
        if not _public_url("x", url, object_id):
            return False
        text = _x_reader_text(post.get("observed_text"), links, url, canonical)
        if index < len(expected) and _text(expected[index]) in text:
            index += 1
        elif text not in fragments:
            return False
    return index == len(expected)


def _payload_binding(intent, destination):
    payload = intent.get("native_payload") or intent.get("payload")
    assets = list(intent.get("media_assets") or [])
    artifacts = []
    article = {}
    root = Path(str(intent.get("output_dir") or ""))
    if intent.get("output_dir") and not intent.get("reader_presentation_review"):
        from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
        resolved = _durable_intent_inputs(intent)
        article = dict(resolved.get("article") or {})
        if destination == "substack":
            payload = {"title": article.get("title"), "subtitle": article.get("subtitle"),
                       "body_markdown": article.get("substack_body_markdown")}
        else:
            payload = resolved["payloads"][destination]
        assets = resolved["media_assets"]
        for name in ("run_context_v1.json", "delivery_media_manifest_v1.json"):
            path = root / name
            if path.is_file():
                artifacts.append({"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest()})
    texts = []
    thread_texts = []
    posts = []
    if isinstance(payload, str):
        texts = [payload] if payload else []
    elif isinstance(payload, dict):
        posts = list(payload.get("posts") or [])
        texts = [str(payload[k]) for k in ("title", "subtitle", "body_markdown", "text") if payload.get(k)]
        for post in posts:
            text = post.get("text") if isinstance(post, dict) else post
            if text:
                texts.append(str(text))
                thread_texts.append(str(text))
    if destination != "substack" and isinstance(payload, dict) and (
            "media_asset_ids" in payload or any(isinstance(p, dict) and "media_asset_ids" in p for p in posts)):
        media_ids = set(payload.get("media_asset_ids") or [])
        media_ids.update(a for post in posts if isinstance(post, dict) for a in post.get("media_asset_ids") or [])
        assets = [a for a in assets if a.get("asset_id") in media_ids]
    media = [{k: a[k] for k in ("asset_id", "path", "sha256", "rights", "rights_status", "caption", "alt_text",
              "attribution", "license_url", "source_page_url", "changes_description", "article_section",
              "canonical_article_section_association", "placement_after", "modality", "public_delivery_sha256",
              "verified_public_delivery_url") if k in a}
             for a in assets if isinstance(a, dict)]
    if destination == "substack":
        # 4 Nov SEC post: the image went above the first paragraph with no caption
        # or alt text, because the request carried neither the reviewed section
        # nor the caption. The editorial decision's placement is bound here.
        placements = {str(c.get("asset_id")): c.get("placement_after")
                      for c in ((article.get("visual_editorial_decision") or {}).get("charts") or [])
                      if isinstance(c, dict) and c.get("placement_after")}
        for row in media:
            if not row.get("placement_after") and placements.get(str(row.get("asset_id"))):
                row["placement_after"] = placements[str(row["asset_id"])]
    binding = {"expected_text_segments": texts, "expected_thread_texts": thread_texts, "thread_post_count": len(posts),
               "media_manifest": media, "artifact_manifest": artifacts}
    if intent.get("reader_presentation_review"):
        binding["excluded_text_segments"] = intent["removed_reader_text"]
    return payload, binding


class NeoDestinationHandoff:
    """Coordinator-injected adapter. Every actual write requires exact authorization."""

    def __init__(self, *, native_executor=None, store=None):
        self.native_executor = native_executor
        self.store = store

    def _absence_dispatch_clock(self, intent, destination):
        """Absence must follow the latest write attempt, including a bounded API retry."""
        from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
        store = self.store or getattr(self.native_executor, "store", None)
        if store is None:
            return {}, None
        ids = DurablePublicationCoordinator._ids(intent["work_item_id"], intent["plan_hash"], destination)
        dispatch = store.get_platform_dispatch(ids["dispatch_id"]) or {}
        try:
            latest = datetime.fromisoformat(dispatch["dispatched_at"].replace("Z", "+00:00"))
            prefix = "incident_dispatch_outcome_" + sha256(ids["dispatch_id"].encode()).hexdigest()[:24] + "_%"
            with store.get_read_only_connection() as conn:
                rows = conn.execute("SELECT description FROM incidents WHERE incident_id LIKE ?", (prefix,)).fetchall()
            for row in rows:
                outcome = json.loads(row[0])
                if outcome.get("dispatch_id") == ids["dispatch_id"]:
                    attempted = datetime.fromisoformat(outcome["attempt_started_at_utc"].replace("Z", "+00:00"))
                    latest = max(latest, attempted)
            return dispatch, latest.isoformat()
        except (KeyError, ValueError, TypeError):
            return dispatch, None

    def request(self, *, destination, action, intent, authorization_context=None,
                public_object_id=None, public_object_url=None):
        if destination not in IDENTITIES or action not in {"PUBLISH", "READBACK", "EDIT_EXISTING"}:
            raise ValueError("NEO_DESTINATION_ACTION_UNSUPPORTED")
        if destination in {"telegram", "threads"} and action != "READBACK":
            raise ValueError("SOCIAL_NEO_READBACK_ONLY_API_WRITES_UNCHANGED")
        if destination == "instagram_business" and action == "PUBLISH":
            raise ValueError("INSTAGRAM_ROUTINE_API_TRANSPORT_UNCHANGED")
        if _private(intent):
            raise ValueError("PRIVATE_NEO_INTENT_EXCLUDED")
        auth = dict(authorization_context or {})
        if action in {"PUBLISH", "EDIT_EXISTING"}:
            if (auth.get("schema_version") != "contentops.canonical_machine_authorization.v1"
                    or auth.get("operating_mode") != "AUTONOMOUS_DEFAULT"
                    or auth.get("destination") != destination or not auth.get("dispatch_attempt_identity")
                    or auth.get("work_item_id") != intent.get("work_item_id")
                    or auth.get("payload_hash") != intent.get("destination_plan", {}).get("payload_hash")):
                raise ValueError("SOLE_COORDINATOR_AUTHORIZATION_REQUIRED")
            valid_canonical = (_social_canonical(intent.get("canonical_url"))
                if intent.get("distribution_policy") == "SITE_FIRST_V1" else _canonical(intent.get("canonical_url")))
            if destination != "substack" and not valid_canonical:
                raise ValueError("RECONCILED_CANONICAL_URL_REQUIRED")
        if action == "EDIT_EXISTING" and (not intent.get("reader_presentation_review")
                or not public_object_id or not _public_url(destination, public_object_url, public_object_id)
                or auth.get("action") != "EDIT_EXISTING"):
            raise ValueError("NEO_EXACT_REVIEWED_EXISTING_OBJECT_REQUIRED")
        native_payload, content_binding = _payload_binding(intent, destination)
        value = {"schema_version": SCHEMA, "destination": destination, "action": action,
            "expected_identity": IDENTITIES[destination], "entry_url": ROOTS[destination],
            "intent_sha256": sha256_of(intent), "work_item_id": intent.get("work_item_id"),
            "package_identity": intent.get("package_identity"),
            "payload_hash": intent.get("destination_plan", {}).get("payload_hash"),
            "dispatch_attempt_identity": auth.get("dispatch_attempt_identity"),
            "canonical_url": intent.get("canonical_url"),
            "public_object_id": public_object_id, "public_object_url": public_object_url,
            "native_payload": native_payload, "payload": intent.get("payload"),
            "content_binding": content_binding,
            "surface": intent.get("destination_plan", {}).get("surface") or {
                "substack": "SUBSTACK_ARTICLE", "x": "X_THREAD" if content_binding["thread_post_count"] > 1 else "X_POST",
                "linkedin": "LINKEDIN_POST", "linkedin_company": "LINKEDIN_COMPANY_POST",
                 "instagram_business": "INSTAGRAM_BUSINESS_POST",
                "telegram": "TELEGRAM_CHANNEL_POST", "threads": "THREADS_POST",
                "youtube": "YOUTUBE_COMMUNITY_POST"}[destination],
            "steps": ["name_session; list tabs, open a task-owned tab",
                "snapshot; verify current signed-in publishing identity exactly; login is an owner action",
                "bind exact approved payload/media and reconciled canonical URL; use snapshot refs only",
                 "PUBLISH or EDIT_EXISTING only under this sole-coordinator authorization; READBACK never submits or retries",
                "read back stable public object ID, exact public URL, identity and content; preserve ambiguity"],
            "substack_media_readback": "Return public_image_urls observed on the exact canonical page; the existing media owner verifies original bytes before derivative delivery.",
            "forbidden": ["login", "reauthorize", "account_switch", "cookies", "storage", "blind_retry", "bulk_x_ingestion"]}
        if destination == "substack" and action in {"PUBLISH", "EDIT_EXISTING"} and content_binding["media_manifest"]:
            value["substack_media_placement"] = (
                "Place each media_manifest image in the body where its placement_after names: after the "
                "paragraphs under the heading with that text ('introduction' or 'lead' means after the first "
                "paragraph). Never put an image above the first paragraph unless placement_after says so. Set "
                "its alt text to alt_text and its caption to caption (with the credit when attribution is "
                "present). Return public_alt_text_present and public_caption_present for each image.")
            value["steps"].insert(3, value["substack_media_placement"])
        if action == "READBACK":
            # An earlier failed observation stays immutable. A corrected readback
            # contract receives a new read-only identity, never a new write.
            value["reader_text_normalization"] = ("DIGEST_EDITOR_SUBTITLE_CAPTION_V2" if intent.get("daily_digest")
                                                   else "MARKDOWN_WHITESPACE_SMART_QUOTES_V1")
            # A failed observation is immutable, but the same native turn may
            # obtain the later readback required after the ten-minute interval.
            clock = getattr(self.native_executor, "clock", None)
            now = clock() if callable(clock) else datetime.now(timezone.utc)
            value["observation_epoch"] = int(now.timestamp()) // 600
            if not public_object_id and not public_object_url:
                _, latest_attempt = self._absence_dispatch_clock(intent, destination)
                if latest_attempt:
                    # A retry in the same epoch needs a fresh observation; the old
                    # immutable return cannot establish absence after that retry.
                    value["latest_dispatch_attempt_at_utc"] = latest_attempt
            invocation = getattr(self.native_executor, "native_invocation_id", None)
            if invocation:
                value["native_invocation_id"] = invocation
        mode = intent.get("destination_plan", {}).get("substack_delivery_mode")
        if destination == "substack" and mode and action == "PUBLISH":
            from live_contentops.substack_daily_digest_v1 import delivery_policy
            value["substack_delivery_policy"] = delivery_policy(mode)
        if destination == "substack" and intent.get("daily_digest") and action == "READBACK":
            value["digest_email_readback"] = {
                "instruction": "Read this exact post's publisher dashboard delivery status; return email_delivery_confirmed=true only for an observed sent email, with email_delivery_evidence_ref. Never read a mailbox. A public page alone does not prove email delivery.",
                "observation_hour": int(datetime.now(timezone.utc).timestamp()) // 3600,
            }
        if destination == "substack" and action == "READBACK" and intent.get("published_content_export"):
            value["publication_clock_readback"] = (
                "Return published_at_utc from the exact post's time datetime or post_date; "
                "preserve the original timestamp with a UTC offset. Never substitute a dispatch, "
                "event, retrieval, scheduled or current clock."
            )
        if destination == "substack" and action == "READBACK" and intent.get("pending_owner_screen"):
            value["pending_owner_screen"] = intent["pending_owner_screen"]
            value["owner_readback_invocation"] = intent.get("owner_readback_invocation")
            value["steps"] = ["Inspect only the same retained code tab. Never reload, navigate, type, read a mailbox or enter a code. If still on the code screen, report unverified and continue other destinations in other task tabs without waiting. Continue exact Substack readback only after this tab reaches /publish/posts/detail/.../share-center."]
        if destination == "substack" and action == "READBACK":
            from live_contentops.substack_draft_inventory_v1 import readback_scope, store_draft_ids
            value["draft_readback_scope"] = readback_scope(store_draft_ids(self.store) if self.store else set())
            value["steps"].append(value["draft_readback_scope"]["instructions"])
        if destination == "linkedin" and action == "READBACK" and not public_object_id:
            value["owner_absence_context"] = intent.get("owner_absence_context")
        if intent.get("reader_presentation_review"):
            value["reader_presentation_review"] = intent["reader_presentation_review"]
        if action == "READBACK":
            resumed = getattr(self.native_executor, "readback_request_invocations", {})
            identity = sha256_of({k: v for k, v in value.items() if k != "native_invocation_id"})
            if identity in resumed:
                if resumed[identity] is None:
                    value.pop("native_invocation_id", None)
                else:
                    value["native_invocation_id"] = resumed[identity]
            fresh_readback = getattr(self.native_executor, "fresh_readback_request", None)
            if callable(fresh_readback):
                previous = fresh_readback(value)
                if previous:
                    return previous
        value["request_sha256"] = sha256_of(value)
        return value

    def publish(self, *, destination, intent, authorization_context):
        request = self.request(destination=destination, action="PUBLISH", intent=intent,
                               authorization_context=authorization_context)
        if self.native_executor is None:
            return {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True,
                    "reason_code": "NEO_NATIVE_EXECUTOR_NOT_BOUND", "request": request,
                    "public_write_performed": False}
        result = dict(self.native_executor(request))
        if (result.get("request_sha256") == request["request_sha256"] and result.get("composed_identity") is not None
                and result.get("definite_no_write") is True and str(result.get("status")) == "FAILED_BEFORE_WRITE"
                and result.get("public_write_performed") is False
                and not (result.get("native_tool_observation") or {}).get("dispatched_at_utc")):
            # CC-283: the composed run stopped before the publish click (for example an account
            # mismatch); a definite no-write that releases the claim for a retry.
            return result
        if (result.get("request_sha256") != request["request_sha256"]
                or result.get("observed_identity") != IDENTITIES[destination]):
            return {"status": "UNKNOWN_WRITE", "reason_code": "NEO_RETURN_BINDING_OR_IDENTITY_MISMATCH"}
        policy = request.get("substack_delivery_policy")
        if policy and str(result.get("status", "")).upper() in {"SUCCESS", "PUBLISHED", "DISPATCH_CONFIRMED"}:
            observed = result.get("delivery_observation") or {}
            if (observed.get("email_send_enabled") is not policy["email_send_enabled"]
                    or observed.get("web_publish_enabled") is not True
                    or not observed.get("evidence_ref")):
                return {**result, "status": "UNKNOWN_WRITE",
                        "reason_code": "SUBSTACK_DELIVERY_MODE_NOT_VERIFIED", "retry_permitted": False}
        # Identity/readback ambiguity is left to the sole coordinator. Never retry here.
        return result

    def amend_existing(self, *, destination, intent, public_object_id, public_object_url, authorization_context):
        request = self.request(destination=destination, action="EDIT_EXISTING", intent=intent,
            public_object_id=public_object_id, public_object_url=public_object_url,
            authorization_context=authorization_context)
        if self.native_executor is None:
            return {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True, "request": request}
        result = dict(self.native_executor(request))
        if (result.get("request_sha256") != request["request_sha256"]
                or result.get("observed_identity") != IDENTITIES[destination]
                or result.get("public_object_id") != public_object_id
                or result.get("public_object_url") != public_object_url):
            return {"status": "UNKNOWN_EDIT", "retry_permitted": False}
        return result

    def readback(self, *, destination, intent, public_object_id, public_object_url):
        request = self.request(destination=destination, action="READBACK", intent=intent,
            public_object_id=public_object_id, public_object_url=public_object_url)
        if destination == "substack":
            from live_contentops.substack_draft_inventory_v1 import draft_id_from_url
            draft_id = draft_id_from_url(public_object_url)
            if draft_id and draft_id not in request["draft_readback_scope"]["referenced_draft_ids"]:
                return {"status": "SKIPPED", "verified": False, "write_absent": False,
                        "reason_code": "UNREFERENCED_SUBSTACK_DRAFT_IGNORED", "request": request}
        if self.native_executor is None:
            return {"status": "BLOCKED", "verified": False, "request": request,
                    "reason_code": "NEO_NATIVE_READBACK_EXECUTOR_NOT_BOUND"}
        result = dict(self.native_executor(request))
        binding = request["content_binding"]
        segments = binding["expected_text_segments"]
        observed_text = _text(result.get("observed_text"))
        comparison_text = observed_text
        if destination == "substack" and (intent.get("reader_presentation_review") or intent.get("daily_digest")):
            # The accepted body remains contiguous after removing only its exact
            # reviewed figure captions, which the renderer inserts between blocks.
            for asset in binding["media_manifest"]:
                caption = _text(asset.get("caption"))
                if caption:
                    comparison_text = _text(comparison_text.replace(caption, " "))
        if destination in {"linkedin", "linkedin_company"}:
            # LinkedIn rewrites displayed links. Keep raw observed copy and only
            # expand an actually verified target on this exact public object.
            canonical = str(intent.get("canonical_url") or "")
            for link in result.get("observed_link_resolutions") or []:
                short = str(link.get("displayed_url") or "")
                if (re.fullmatch(r"https://lnkd\.in/[A-Za-z0-9_-]+", short)
                        and short in str(result.get("observed_text") or "")
                        and link.get("target_verified") is True
                        and link.get("public_object_url") == public_object_url
                        and link.get("target_url") == canonical and _social_canonical(canonical)):
                    comparison_text = comparison_text.replace(_text(short), _text(canonical))
        if destination == "x":
            comparison_text = _x_reader_text(observed_text, result.get("observed_link_resolutions") or [],
                public_object_url, str(intent.get("canonical_url") or ""))
        text_match = (bool(segments) and all(_text(s) in comparison_text for s in segments)
            and all(_text(s) not in comparison_text for s in binding.get("excluded_text_segments", [])))
        if destination == "substack" and intent.get("daily_digest"):
            # A native editor may render this structured link index as paragraphs
            # or a list. Markdown list punctuation adds no reader-facing fact.
            from live_contentops.substack_daily_digest_v1 import substack_subtitle
            # Already-issued digests can carry a subtitle longer than the native
            # editor's 200-character field. Render its bounded presentation while
            # preserving the frozen packet and every full body title/summary/link.
            subtitle = (intent.get("native_payload") or {}).get("subtitle")
            digest_segments = [re.sub(r"(?m)^-\s+(?=\[)", "",
                substack_subtitle(s) if s == subtitle else s) for s in segments]
            text_match = bool(segments) and all(_text(s) in comparison_text for s in digest_segments)
            from live_contentops.substack_daily_digest_v1 import validate_digest_intent
            packet = validate_digest_intent(self.native_executor.store, intent)
            expected_links = [(_text(a["title"]), a["url"]) for a in packet["articles"]]
            observed_links = [(_text(a.get("text")), a.get("url"))
                              for a in result.get("observed_links", [])]
            text_match = text_match and observed_links == expected_links
        expected_media = {a.get("public_delivery_sha256") or a.get("sha256") for a in binding["media_manifest"]}
        expected_media.discard(None)
        media_match = expected_media <= set(result.get("observed_media_sha256") or [])
        reviewed_photo_edit = bool(intent.get("reader_presentation_review")) and destination in {"instagram_business", "youtube"}
        if (destination in {"linkedin", "linkedin_company", "x", "youtube", "threads", "telegram"} or reviewed_photo_edit) and not media_match:
            comparisons = result.get("media_comparisons") or []
            def platform_image(url):
                host = urlsplit(str(url or "")).hostname or ""
                return ((destination in {"linkedin", "linkedin_company"} and host == "media.licdn.com")
                    or (destination == "x" and host == "pbs.twimg.com"
                        and urlsplit(str(url or "")).path.startswith("/media/"))
                    or (destination == "youtube" and host == "yt3.ggpht.com")
                    or (destination == "threads" and (host.endswith(".cdninstagram.com") or host.endswith(".fbcdn.net")))
                    or (destination == "telegram" and host.endswith(".telegram-cdn.org"))
                    or (destination == "instagram_business" and (host.endswith(".cdninstagram.com") or host.endswith(".fbcdn.net"))))
            source_matches = {m.get("source_asset_sha256") for m in comparisons
                if m.get("pixels_inspected") is True and m.get("source_pixels_match") is True
                and re.fullmatch(r"[0-9a-f]{64}", str(m.get("platform_sha256") or ""))
                and m.get("public_object_url") == public_object_url
                and urlsplit(str(m.get("public_image_url") or "")).scheme == "https"
                and platform_image(m.get("public_image_url"))}
            media_match = expected_media <= source_matches
        thread = result.get("observed_thread") or result.get("thread_posts") or []
        thread_match = (binding["thread_post_count"] <= 1 or (
            len(thread) == binding["thread_post_count"]
            and all(_text(text) in _text(post.get("observed_text"))
                    and _public_url(destination, post.get("public_object_url"), post.get("public_object_id"))
                    for text, post in zip(binding["expected_thread_texts"], thread))
            and len({p.get("public_object_id") for p in thread}) == len(thread)))
        if destination == "x" and binding["thread_post_count"] > 1:
            thread_match = _x_thread_matches(binding, thread, result.get("observed_link_resolutions") or [],
                str(intent.get("canonical_url") or ""))
        verified = (result.get("request_sha256") == request["request_sha256"]
            and result.get("observed_identity") == IDENTITIES[destination]
            and (not public_object_id or result.get("public_object_id") == public_object_id)
            and (not public_object_url or result.get("public_object_url") == public_object_url)
            and _public_url(destination, result.get("public_object_url"), result.get("public_object_id"))
            and result.get("content_verified") is True and text_match and media_match and thread_match)
        identity_exists = (result.get("request_sha256") == request["request_sha256"]
            and result.get("observed_identity") == IDENTITIES[destination]
            and bool(public_object_id) and result.get("public_object_id") == public_object_id
            and result.get("public_object_url") == public_object_url
            and _public_url(destination, public_object_url, public_object_id)
            and bool(observed_text))
        # Publication and exact copy equality are separate observations. A
        # later credit/caption edit cannot unpublish an otherwise identified
        # canonical or invalidate unchanged derivative copies (CC-199 CLD-C7).
        from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
        payload = request.get("native_payload") or {}
        title = _text(payload.get("title")) if isinstance(payload, dict) else ""
        canonical_present = bool(destination == "substack" and not intent.get("daily_digest")
            and identity_exists and title and title in observed_text
            and _text(PUBLIC_NOTICE) in observed_text
            and any(_text(PUBLIC_NOTICE) in _text(s) for s in segments))
        absent = False
        if not public_object_id and not public_object_url and result.get("target_post_absent") is True:
            dispatch, latest_attempt = self._absence_dispatch_clock(intent, destination)
            observation = result.get("native_tool_observation") or {}
            try:
                observed_at = datetime.fromisoformat(observation["observed_at_utc"].replace("Z", "+00:00"))
                attempted_at = datetime.fromisoformat(latest_attempt)
                elapsed = (observed_at - attempted_at).total_seconds()
            except (KeyError, ValueError, TypeError):
                elapsed = -1
            absent = (elapsed >= 600 and result.get("authenticated") is True
                and result.get("activity_feed_loaded") is True and bool(observed_text)
                and result.get("observed_profile_url") == ROOTS[destination]
                and result.get("observed_identity") == IDENTITIES[destination]
                and result.get("request_sha256") == request["request_sha256"]
                and dispatch.get("status") in {"UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED", "NATIVE_NEO_TOOL_PENDING", "RECONCILED_ABSENT_SAFE_TO_RETRY"}
                and not any(_text(s) in comparison_text for s in segments if len(_text(s)) >= 30))
        complete_readback = getattr(self.native_executor, "complete_readback_request", None)
        if (verified or canonical_present or absent) and callable(complete_readback):
            complete_readback(request)
        return {**result, "verified": bool(verified), "status": "SUCCESS" if verified else "BLOCKED",
                "write_exists": bool(identity_exists), "write_absent": bool(absent),
                "canonical_publication_verified": canonical_present,
                "content_binding_checks": {"text_match": text_match, "media_match": media_match, "thread_match": thread_match}}


def destination_setup_projection(*, env=None, now=None, linkedin_root=None):
    """Presence only, with non-secret expiry metadata. Never decrypt or probe tokens."""
    if env is None:  # CC-297: Credential Manager, then the live user env, then the process env
        from live_contentops.secret_store_v1 import secret_environment
        env = secret_environment()
    now = now or datetime.now(timezone.utc)
    keys = {
        "telegram": (("TELEGRAM_BOT_TOKEN",), ("TELEGRAM_TARGET_CHAT_ID", "TELEGRAM_CHANNEL_ID", "TELEGRAM_CHAT_ID")),
        "discord": (("DISCORD_ANNOUNCEMENTS_WEBHOOK_URL", "DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK"),),
        "facebook_page": (("FACEBOOK_PAGE_ACCESS_TOKEN", "META_ACCESS_TOKEN"), ("FACEBOOK_PAGE_ID",)),
        "instagram_business": (("INSTAGRAM_ACCESS_TOKEN", "META_ACCESS_TOKEN"), ("INSTAGRAM_BUSINESS_ACCOUNT_ID",)),
        "threads": (("THREADS_USER_ACCESS_TOKEN",), ("THREADS_USER_ID",)),
        "linkedin": (("LINKEDIN_CLIENT_ID",), ("LINKEDIN_CLIENT_SECRET",)),
    }
    transports = {"telegram": "BOT_API", "discord": "WEBHOOK_API", "facebook_page": "META_GRAPH_API",
                  "instagram_business": "META_GRAPH_API", "threads": "THREADS_API", "linkedin": "OFFICIAL_MEMBER_API"}
    result = {}
    for destination, groups in keys.items():
        present = all(any(bool(env.get(k)) for k in group) for group in groups)
        result[destination] = {"chosen_transport": transports[destination], "configuration_present": present,
            "validity": "NOT_VERIFIED", "identity_state": "NOT_VERIFIED",
            "browser_login_needed": False,
            "owner_action": "Xác minh token và quyền bằng kiểm tra chỉ đọc khi cần dùng." if present else "Bổ sung cấu hình API cho đích này."}
    auth_root = Path(linkedin_root or r"A:\Capital Chronicle\Runtime\ContentOps\linkedin_official_member_api")
    try:
        metadata = json.loads((auth_root / "auth_metadata_v1.json").read_bytes())
        expiry = next((metadata[k] for k in ("expires_at_utc", "token_expires_at_utc", "access_token_expires_at_utc") if metadata.get(k)), None)
        if expiry and datetime.fromisoformat(expiry.replace("Z", "+00:00")) <= now:
            result["linkedin"].update(validity="EXPIRED", owner_action="Cấp lại quyền LinkedIn OAuth; đăng nhập tab đơn thuần không làm mới token.")
        result["linkedin"]["auth_expiry_at_utc"] = expiry
        result["linkedin"]["encrypted_auth_store_present"] = (auth_root / "linkedin_member_credentials.dpapi").is_file()
    except (OSError, ValueError, TypeError):
        result["linkedin"]["owner_action"] = "Kiểm tra/cấp lại LinkedIn OAuth qua luồng hiện có."
    for destination in IDENTITIES:
        if destination == "linkedin":
            # Native Neo is an explicit reviewed recovery, not the routine API default.
            continue
        result[destination] = {"chosen_transport": "BROWSEROS_NEO_MCP", "configuration_present": True,
            "validity": "NOT_VERIFIED", "identity_state": "NOT_VERIFIED", "browser_login_needed": True,
            "expected_identity": IDENTITIES[destination],
            "owner_action": "Xác minh phiên Neo đúng tài khoản; nếu thiếu, chủ tài khoản đăng nhập.",
            "integration_state": "PREPARED_NATIVE_REQUEST_READBACK_EXECUTOR_NOT_BOUND"}
    result["youtube"]["api_oauth_does_not_authorize_community"] = True
    return result
