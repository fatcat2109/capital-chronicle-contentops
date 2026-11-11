"""CC-455: the existing sourced-reply runner's pack for Jim (decision 122).

The feed and public desk/frozen-call records are inputs. Native editorial work
authors the response. This module saves files and internal store records; it has
no browser, provider, model, coordinator or public-write call.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from live_contentops.event_article_guard_v1 import (
    CONFLICTS_NOTICE, NAMED_NUMBER, PUBLIC_NOTICE, check_publication_copy,
)
from live_contentops.preview_link_guard_v1 import find_forbidden_link
from live_contentops.public_time_v1 import public_timestamp, require_public_time
from live_contentops.sourced_replies_v1 import clock, digest
from tools.product.desk_record_projection_v1 import (
    MODEL_ESTIMATE_LABEL, PRIVATE_ONLY_RIGHTS, public_text_problems,
)

PACK_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\x_reply_pack")
TARGETS = Path(__file__).resolve().parents[1] / "docs/publisher/CC-455/target-accounts.json"
PACK_DESTINATION = "internal:x-reply-pack"
READBACK_DESTINATION = "internal:x-manual-reply-readback"
LOCAL = ZoneInfo("Asia/Bangkok")  # CC-457's private desk day; public prose uses ET.
BUILD_WINDOW_SECONDS = 120 * 60  # Decision 123: Jim checks every three to four hours.
TAB_LIFETIME_SECONDS = 6 * 60 * 60
NUMBER = re.compile(r"(?<![A-Za-z0-9])[+-]?\d+(?:[.,]\d+)*%?")
POST = re.compile(r"https://(?:www\.)?x\.com/([A-Za-z0-9_]+)/status/(\d+)")
TOPIC = re.compile(
    r"\b(?:gold|silver|oil|wti|brent|bitcoin|btc|crypto|dollar|eur|yen|fx|forex|"
    r"treasur\w*|bonds?|yields?|rates?|fed|fomc|ecb|boj|cpi|ppi|pce|payrolls?|"
    r"inflation|jobs|gdp|s&p|nasdaq|stocks?|equities|indices|index)\b", re.I,
)


def utcnow():
    return datetime.now(timezone.utc)


def read_json(path):
    return json.loads(Path(path).read_bytes())


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def target_handles(path=TARGETS):
    config = read_json(path)
    base = read_json(Path(__file__).resolve().parents[1] / config["reuse_target_research"])
    return {str(row["x_author"]).lstrip("@").casefold() for row in base["targets"]} | {
        str(handle).lstrip("@").casefold() for handle in config["additional_x_handles"]
    }


def select_posts(feed, *, handles, mentions=None, now=None):
    """Age/topic/identity checks, retaining original text for private drafting."""
    now = now or utcnow()
    selected, causes, seen = [], Counter(), set()
    for row in [*feed.get("rows", []), *(mentions or {}).get("rows", [])]:
        handle = str(row.get("handle", "")).lstrip("@")
        text = str(row.get("text", ""))
        kind = "mention" if (
            re.search(r"(?<!\w)@Capitalnicle\b", text, re.I)
            or str(row.get("quoted_author_handle", "")).lstrip("@").casefold() == "capitalnicle"
        ) else "target"
        if kind == "target" and handle.casefold() not in handles:
            continue
        post_id = str(row.get("tweet_id", ""))
        match = POST.fullmatch(str(row.get("url", "")))
        if not match or match[1].casefold() != handle.casefold() or match[2] != post_id:
            causes["POST_IDENTITY_MISMATCH"] += 1
            continue
        if post_id in seen:
            continue
        seen.add(post_id)
        try:
            posted = clock(row["posted_utc"])
        except (ValueError, KeyError, TypeError):
            causes["POST_TIME_INVALID"] += 1
            continue
        age = (now - posted).total_seconds()
        if not 0 <= age <= BUILD_WINDOW_SECONDS:
            causes["POST_OUTSIDE_120_MINUTE_BUILD_WINDOW"] += 1
        elif row.get("is_retweet") or text.startswith("RT @"):
            causes["RETWEET_NOT_ORIGINAL_TARGET"] += 1
        elif kind == "target" and not TOPIC.search(text):
            causes["NO_SIX_MARKET_OR_MACRO_TOPIC"] += 1
        elif handle.casefold() == "capitalnicle":
            causes["OWN_POST_NOT_REPLY_TARGET"] += 1
        else:
            selected.append({
                "kind": kind, "post_id": post_id, "post_url": row["url"],
                "author_handle": handle, "post_time_utc": posted.isoformat(),
                "post_text": text, "post_age_seconds_at_build": age,
            })
    selected.sort(key=lambda row: (row["kind"] != "mention", row["post_age_seconds_at_build"]))
    return selected, dict(causes)


def held_sources(store, *, desk_message_id=None, call_message_id=None, include_desk=True, include_calls=True):
    """Reuse the source owner's public projection and our frozen public calls."""
    sources = []
    rows = (([store.get_outbox_message(desk_message_id)] if desk_message_id else
             store.list_outbox_messages(destination="internal:cc-report-feed")) if include_desk else [])
    rows = [r for r in rows if r and r["destination"] == "internal:cc-report-feed"]
    if rows:
        row = rows[-1]
        data = json.loads(row["payload"])
        for record in data.get("desk_record_sources", []):
            binding = record["binding"]
            if binding.get("fixture"):
                continue
            for field in binding["fields"]:
                value = field.get("value")
                if (value is None or isinstance(value, (dict, list, bool))
                        or field.get("rights_class") in PRIVATE_ONLY_RIGHTS):
                    continue
                display = field["display"]
                if not NUMBER.search(display):
                    continue
                sources.append({
                    "source_id": row["message_id"] + "#" + field["citation"],
                    "kind": "MAIN_PUBLIC_DESK_FIELD", "label": record["title"],
                    "known_at_utc": record["known_at_utc"], "excerpt": display,
                    "rights_class": field["rights_class"], "field": field,
                    "context": [{"path": f["field_path"], "display": f["display"]}
                                for f in binding["fields"] if f["value"] is not None
                                and not isinstance(f["value"], (list, dict))],
                    "source_attribution": binding["sources"],
                    "store_message_id": row["message_id"],
                    "store_payload_sha256": digest(data),
                })
    calls = (([store.get_outbox_message(call_message_id)] if call_message_id else
              store.list_outbox_messages(destination="internal:plan-status-post")) if include_calls else [])
    for row in calls:
        if not row or row["destination"] != "internal:plan-status-post":
            continue
        data = json.loads(row["payload"])
        # These are the source owner's public, frozen setup calls, not fills or account data.
        if data.get("kind") != "setup" or not data.get("text"):
            continue
        sources.append({
            "source_id": row["message_id"], "kind": "FROZEN_PUBLIC_CALL",
            "label": "Capital Chronicle frozen " + str(data.get("symbol", "")) + " call",
            "known_at_utc": data.get("at_utc") or data.get("registered_at_utc") or row["created_at"],
            "excerpt": data["text"],
            "rights_class": "CC_OWN_ANALYSIS", "store_message_id": row["message_id"],
            "store_payload_sha256": digest(data), "plan_id": data.get("plan_id"),
        })
    return sources


def prepare(store, *, feed_path, output_root=PACK_ROOT, targets=TARGETS, mentions_path=None, now=None,
            automated_mentions=False):
    now = now or utcnow()
    feed = read_json(feed_path)
    posts, causes = select_posts(feed, handles=target_handles(targets), now=now,
                                mentions=read_json(mentions_path) if mentions_path else None)
    sources = held_sources(store)
    request = {
        "schema_version": "contentops.x_reply_pack_request.v1", "prepared_at_utc": now.isoformat(),
        "feed_generated_at_utc": feed["generated_at_utc"], "feed_sha256": digest(feed),
        "candidates": posts, "selection_causes": causes, "sources": sources,
        "audience_feedback": report_manual_replies(store, now=now),
        "instructions": (
            "Author English replies for Jim to review and post himself (decisions 122 and 123). "
            "Choose 3-5 useful target posts, at most one per target author, plus every useful mention. "
            "Never pad. Each draft is <=280 characters, contains one exact sourced number/fact and its "
            "public_timestamp, and adds an invalidation, priced-in comparison or dated pre-event view. "
            "Copy no third-party post into the reply. Use only the public desk fields or frozen calls here. "
            "No advice, AI label, account, execution or model-position wording. Include PUBLIC_NOTICE. "
            "Return request_sha256, editorial_call (actual model/effort when observed; configured values "
            "otherwise), items [{post_id, source_id, fact_text (exact source excerpt in the reply), "
            "draft_text, addition (in the draft), point, reply_shape}], and omissions [{post_id, cause}]. "
            "Use the same operation's native editorial route; never call Claude or a paid model API. "
            "No link unless it is our confirmed published Substack page."
            " Use audience_feedback for selection: after its fourteen-day review is due, "
            "drop targets and reply shapes with measured zero views; prefer those earning views "
            "and drafts Jim actually posted. Uncaptured metrics stay unknown. Audience numbers "
            "are private selection feedback, never source facts for the reply."
        ),
        "PUBLIC_NOTICE": PUBLIC_NOTICE,
        "public_write_performed": False,
    }
    if automated_mentions:
        request["instructions"] += (
            " Mention drafts can also be used by decision 122's official API responder. "
            "Include 'Reply STOP to opt out.' within the 280-character limit on those drafts. "
            "A browser-held mention without an official API binding stays for Jim's click."
        )
    for source in sources:
        source["public_timestamp"] = public_timestamp(source["known_at_utc"])
    request["request_sha256"] = digest(request)
    path = Path(output_root) / ("reply-pack-request-" + request["request_sha256"][:16] + ".json")
    save_json(path, request)
    return {"request_path": str(path), "request_sha256": request["request_sha256"],
            "candidate_count": len(posts), "source_count": len(sources), "selection_causes": causes,
            "public_write_performed": False}


def validate_draft(draft, post, source, *, now, published_urls=()):
    text = draft["draft_text"]
    if not text.strip() or len(text) > 280:
        raise ValueError("REPLY_PLATFORM_LENGTH_EXCEEDED")
    if any(char.isalpha() and not ("a" <= char.lower() <= "z") for char in text):
        raise ValueError("REPLY_ENGLISH_REQUIRED")
    if clock(source["known_at_utc"]) > now:
        raise ValueError("REPLY_SOURCE_KNOWN_AFTER_PREPARATION")
    fact = draft.get("fact_text", "")
    if not fact or not NUMBER.search(fact) or fact not in source["excerpt"] or fact not in text:
        raise ValueError("REPLY_EXACT_SOURCE_FACT_REQUIRED")
    stamp = public_timestamp(source["known_at_utc"])
    if stamp not in text:
        raise ValueError("REPLY_SOURCE_TIME_REQUIRED")
    remainder = text.replace(stamp, "")
    remainder = re.sub(r"https?://\S+", "", NAMED_NUMBER.sub(" ", remainder))
    if {n.rstrip("%") for n in NUMBER.findall(remainder)} - {n.rstrip("%") for n in NUMBER.findall(fact)}:
        raise ValueError("REPLY_UNBOUND_OR_CHANGED_NUMBER")
    if not draft.get("point") or not draft.get("addition") or draft["addition"] not in text:
        raise ValueError("REPLY_THREAD_SPECIFIC_POINT_REQUIRED")
    if draft["addition"].casefold() in post["post_text"].casefold():
        raise ValueError("REPLY_ADDS_NOTHING_TO_TARGET")
    if find_forbidden_link(text):
        raise ValueError("PREVIEW_HOST_LINK_FORBIDDEN")
    require_public_time(text)
    for url in re.findall(r"(?:https?://|www\.)\S+|(?<![\w@])[a-zA-Z0-9.-]+\.(?:com|net|org|io|app|dev|co)\b\S*", text):
        if url.rstrip(".,)") not in published_urls:
            raise ValueError("REPLY_LINK_NOT_OWN_CONFIRMED_PAGE")
    if re.search(r"\b(?:AI[- ]?(?:generated|written|run)|as an AI|follow us|buy now|CFDs?)\b", text, re.I):
        raise ValueError("REPLY_PROMOTION_OR_AI_LABEL_FORBIDDEN")
    if public_text_problems(text):
        raise ValueError("REPLY_PRIVATE_OR_RAW_TEXT")
    check_publication_copy({"reply": text})
    if PUBLIC_NOTICE not in text:
        raise ValueError("PUBLIC_ANALYSIS_NOTICE_REQUIRED")
    if source["rights_class"] == "CC_MODEL_ESTIMATE" and (
        MODEL_ESTIMATE_LABEL not in text or CONFLICTS_NOTICE not in text
    ):
        raise ValueError("REPLY_MODEL_ESTIMATE_NOTICES_REQUIRED")
    return text


def render_html(pack):
    cards = []
    for item in pack["items"]:
        sources = "; ".join(escape(s["label"]) + " · " +
                            clock(s["known_at_utc"]).astimezone(LOCAL).strftime("%d %b %Y %H:%M GMT+7")
                            for s in item["sources"])
        cards.append(
            '<article data-post-time="' + escape(item["post_time_utc"], quote=True) + '">'
            '<h2><a href="' + escape(item["post_url"], quote=True) + '">@' + escape(item["author_handle"]) + '</a></h2>'
            '<p class="age"></p><blockquote>' + escape(item["post_text"]) + '</blockquote>'
            '<textarea readonly aria-label="Reply draft">' + escape(item["draft_text"]) + '</textarea>'
            '<p class="sources">' + sources + '</p><a class="intent" href="' + escape(item["intent_url"], quote=True)
            + '" rel="noopener noreferrer">Review reply on X</a></article>'
        )
    built = clock(pack["built_at_utc"]).astimezone(LOCAL).strftime("%d %b %Y %H:%M GMT+7")
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Capital Chronicle · Reply pack</title><style>
body{font:17px/1.5 system-ui;margin:2rem auto;padding:0 1rem;max-width:800px;background:#f5f4ef;color:#17212b}
article{background:white;padding:1.3rem;border:1px solid #ccd3d5;border-radius:10px;margin:1rem 0}h1{line-height:1.2}
h2{font-size:1.15rem}a{color:#075d75}blockquote{margin:1rem 0;padding-left:1rem;border-left:3px solid #c7d2d7;white-space:pre-wrap}
textarea{box-sizing:border-box;width:100%;min-height:145px;padding:.8rem;font:inherit;resize:vertical}.sources,.age{font-size:.85rem;color:#53616a}
.intent{display:inline-block;background:#075d75;color:white;padding:.6rem 1rem;border-radius:6px}.stale .intent{display:none}.stale{opacity:.65}
</style><h1>Your X reply pack</h1><p>Read, edit and post each reply yourself. Drafts expire 6 hours after the original post.</p>
<p>Built ''' + escape(built) + '</p><p>' + escape(pack.get("none_reason") or pack.get("short_reason") or "") + '</p>' + "".join(cards) + '''
<script>function ages(){for(const card of document.querySelectorAll('article[data-post-time]')){
const age=Math.max(0,(Date.now()-Date.parse(card.dataset.postTime))/60000);const stale=age>=360;
card.classList.toggle('stale',stale);card.querySelector('.age').textContent=Math.floor(age)+' minutes old'+(stale?' · STALE':'');}}
ages();setInterval(ages,30000);</script></html>'''


def build(store, *, request_path, response_path, feed_path, output_root=PACK_ROOT,
          targets=TARGETS, mentions_path=None, now=None):
    now = now or utcnow()
    request, response = read_json(request_path), read_json(response_path)
    expected = digest({k: v for k, v in request.items() if k != "request_sha256"})
    if expected != request.get("request_sha256") or response.get("request_sha256") != expected:
        raise ValueError("REPLY_PACK_REQUEST_CHANGED")
    feed = read_json(feed_path)
    current, causes = select_posts(feed, handles=target_handles(targets), now=now,
                                  mentions=read_json(mentions_path) if mentions_path else None)
    live = {r["post_id"]: r for r in current}
    frozen = {r["post_id"]: r for r in request["candidates"]}
    # Resolve every source again from its owning immutable outbox, rather than trusting a response's metadata.
    sources = {}
    for bound in request["sources"]:
        if bound["source_id"] not in {d.get("source_id") for d in response.get("items", [])}:
            continue
        options = {"desk_message_id" if bound["kind"] == "MAIN_PUBLIC_DESK_FIELD" else "call_message_id":
                   bound["store_message_id"], "include_desk": bound["kind"] == "MAIN_PUBLIC_DESK_FIELD",
                   "include_calls": bound["kind"] == "FROZEN_PUBLIC_CALL"}
        sources.update({s["source_id"]: s for s in held_sources(store, **options)})
    published_urls = {d["public_object_url"] for d in store.list_platform_dispatches()
                      if d["platform"] == "substack" and d["status"] == "DISPATCH_CONFIRMED"
                      and d.get("public_object_url")}
    items, omitted, authors, seen = [], list(response.get("omissions", [])), set(), set()
    for draft in response.get("items", []):
        post_id = str(draft.get("post_id", ""))
        try:
            post, original = live.get(post_id), frozen.get(post_id)
            if not post or not original:
                raise ValueError("POST_NO_LONGER_IN_FRESH_HELD_INPUT")
            if any(post[k] != original[k] for k in ("post_url", "author_handle", "post_time_utc", "post_text", "kind")):
                raise ValueError("REPLY_TARGET_BYTES_CHANGED")
            if post_id in seen:
                raise ValueError("REPLY_POST_SELECTED_TWICE")
            if post["kind"] == "mention":
                from live_contentops.x_mention_responder_v1 import interaction_status
                if interaction_status(store, post_id):
                    raise ValueError("X_API_INTERACTION_ANSWERED_OR_READBACK_PENDING")
            source = sources.get(draft.get("source_id"))
            bound = next((s for s in request["sources"] if s["source_id"] == draft.get("source_id")), None)
            if not source or not bound or source["store_payload_sha256"] != bound["store_payload_sha256"]:
                raise ValueError("REPLY_SOURCE_BINDING_CHANGED")
            text = validate_draft(draft, post, source, now=now, published_urls=published_urls)
            author = post["author_handle"].casefold()
            if post["kind"] == "target" and (author in authors or len(authors) >= 5):
                raise ValueError("TARGET_AUTHOR_ALREADY_SELECTED_OR_FIVE_TARGETS_REACHED")
            seen.add(post_id)
            if post["kind"] == "target":
                authors.add(author)
            items.append({
                **post, "draft_text": text,
                "intent_url": "https://x.com/intent/post?" + urlencode({"in_reply_to": post_id, "text": text}),
                "stale_at_utc": (clock(post["post_time_utc"]) + timedelta(seconds=TAB_LIFETIME_SECONDS)).isoformat(),
                "sources": [{k: source[k] for k in ("source_id", "label", "known_at_utc", "rights_class",
                                                    "store_message_id", "store_payload_sha256")}],
                "point": draft["point"], "reply_shape": draft.get("reply_shape"),
                "editorial_call": response.get("editorial_call", {}),
            })
        except (ValueError, KeyError) as exc:
            omitted.append({"post_id": post_id, "cause": str(exc)})
    for post_id, post in live.items():
        if post["kind"] == "mention" and post_id not in seen and not any(o.get("post_id") == post_id for o in omitted):
            omitted.append({"post_id": post_id, "cause": "MENTION_NEEDS_NATIVE_SOURCED_DRAFT"})
    reason = None
    if not items:
        reason = ("No fresh target or mention matched the age, identity and market rules. " + json.dumps(causes, sort_keys=True)
                  if not current else "No source-bound native draft was usable. "
                  + "; ".join(sorted({o["cause"] for o in omitted}) or ["Native drafts not supplied."]))
    short = None if len(authors) >= 3 else (
        f"{len(authors)} target replies: no padding. "
        + ("; ".join(sorted({o["cause"] for o in omitted})) or "Fewer eligible authored additions in this build.")
    )
    pack = {
        "schema_version": "contentops.x_reply_pack.v1", "built_at_utc": now.isoformat(),
        "valid_until_utc": max((clock(i["stale_at_utc"]) for i in items), default=now + timedelta(seconds=TAB_LIFETIME_SECONDS)).isoformat(),
        "none_reason": reason, "short_reason": short, "items": items, "omissions": omitted,
        "selection_causes": causes, "request_sha256": expected, "response_sha256": digest(response),
        "feed_generated_at_utc": feed["generated_at_utc"], "feed_sha256": digest(feed),
        "editorial_call": response.get("editorial_call", {}), "public_write_performed": False,
        "publication_actor": "Jim", "schedule_changed": False,
    }
    stem = "reply-pack-" + now.astimezone(LOCAL).strftime("%Y%m%d")
    path = Path(output_root) / (stem + ".json")
    key = "x-reply-pack-" + digest(pack)
    store.create_work_item(story_id=key, title="Jim's X reply pack", target_surface="PRIVATE", work_item_id=key)
    store.register_outbox_message(message_id=key, work_item_id=key, destination=PACK_DESTINATION,
                                  payload=json.dumps(pack, sort_keys=True), status="PREPARED_FOR_JIM")
    save_json(path, pack)
    path.with_suffix(".html").write_text(render_html(pack), encoding="utf-8")
    return {"pack_path": str(path), "html_path": str(path.with_suffix(".html")), "store_message_id": key,
            "item_count": len(items), "none_reason": reason, "short_reason": short,
            "public_write_performed": False}


def read_pack(path, *, now=None):
    """The installed CLI/HTML consumer reads the exact file CC-457 consumes."""
    pack = read_json(path)
    now = now or utcnow()
    return {"pack_path": str(path), "built_at_utc": pack["built_at_utc"],
            "valid_until_utc": pack["valid_until_utc"], "none_reason": pack["none_reason"],
            "item_count": len(pack["items"]), "items": [
                {"post_id": i["post_id"], "author_handle": i["author_handle"],
                 "age_seconds": (now - clock(i["post_time_utc"])).total_seconds(),
                 "stale": now >= clock(i["stale_at_utc"]), "intent_url": i["intent_url"]}
                for i in pack["items"]], "public_write_performed": False}


def observe_manual_replies(store, *, reply_feed_path, now=None):
    """Join exact own-account reply edges from the held signed-in reader.

    Jim may edit a draft. The observed text is retained separately; neither text
    similarity nor a matching number is evidence of a reply edge. Metrics use
    the existing dispatch/readback/performance tables that CC-402 consumes.
    """
    from live_contentops import daily_app_performance_v1 as perf

    now = now or utcnow()
    feed = read_json(reply_feed_path)
    packs = [(r["message_id"], json.loads(r["payload"]))
             for r in store.list_outbox_messages(destination=PACK_DESTINATION)]
    observed, causes = [], Counter()
    for row in feed.get("rows", []):
        if str(row.get("handle", "")).lstrip("@").casefold() != "capitalnicle":
            continue
        match = POST.fullmatch(str(row.get("url", "")))
        post_id = str(row.get("tweet_id", ""))
        parent = str(row.get("in_reply_to_status_id") or row.get("in_reply_to_id") or "")
        if not match or match[1].casefold() != "capitalnicle" or match[2] != post_id or not parent.isdigit():
            causes["MANUAL_REPLY_EXACT_AUTHOR_IDENTITY_AND_PARENT_REQUIRED"] += 1
            continue
        try:
            posted = clock(row["posted_utc"])
        except (ValueError, KeyError, TypeError):
            causes["MANUAL_REPLY_POST_CLOCK_INVALID"] += 1
            continue
        if posted > now:
            causes["MANUAL_REPLY_POST_CLOCK_IN_FUTURE"] += 1
            continue
        candidates = [(key, pack, item) for key, pack in packs for item in pack["items"]
                      if item["post_id"] == parent and clock(pack["built_at_utc"]) <= posted]
        if not candidates:
            continue
        key, pack, item = max(candidates, key=lambda c: clock(c[1]["built_at_utc"]))
        text = str(row.get("text", ""))
        if not text or public_text_problems(text):
            causes["MANUAL_REPLY_EMPTY_OR_PRIVATE_TEXT"] += 1
            continue
        message_id = "manual-x-reply-" + post_id
        dispatch_id = "dispatch_" + message_id
        prior = store.get_outbox_message(message_id)
        if prior:
            value = json.loads(prior["payload"])
            if any(value[k] != expected for k, expected in (
                ("post_url", row["url"]), ("parent_post_id", parent), ("posted_at_utc", posted.isoformat())
            )):
                raise ValueError("MANUAL_REPLY_OBSERVED_IDENTITY_CHANGED")
        else:
            value = {
                "kind": "manual_x_reply_readback", "pack_message_id": key,
                "parent_post_id": parent, "target_author": item["author_handle"],
                "post_id": post_id, "post_url": row["url"], "text": text,
                "posted_at_utc": posted.isoformat(), "observed_at_utc": now.isoformat(),
                "post_to_reply_minutes": (posted - clock(item["post_time_utc"])).total_seconds() / 60,
                "pack_built_at_utc": pack["built_at_utc"], "reply_shape": item.get("reply_shape"),
                "draft_edited": text != item["draft_text"],
                "posted_after_draft_expired": posted >= clock(item["stale_at_utc"]),
                "reader_feed_path": str(reply_feed_path), "reader_feed_sha256": digest(feed),
                "public_write_performed": False, "publication_route": "JIM_MANUAL_DECISION_122",
            }
            store.create_work_item(story_id=message_id, title="Jim's observed X reply", target_surface="PRIVATE",
                                   work_item_id=message_id)
            store.register_outbox_message(message_id=message_id, work_item_id=message_id,
                                          destination=READBACK_DESTINATION, payload=json.dumps(value, sort_keys=True),
                                          status="READBACK_CONFIRMED")
        dispatch = store.register_platform_dispatch(
            dispatch_id=dispatch_id, message_id=message_id, platform="x", status="DISPATCH_CONFIRMED",
            public_object_id=post_id, public_object_url=row["url"], observed_dispatched_at_utc=posted.isoformat(),
        )
        store.register_readback(readback_id="readback_" + message_id, dispatch_id=dispatch_id,
                                readback_data=json.dumps(value, sort_keys=True))
        store.register_reconciliation(reconciliation_id="reconciliation_" + message_id,
                                      work_item_id=message_id, status="RECONCILED_CONFIRMED")
        daily = next(o for o in perf.build_scheduled_observations(
            dispatch=dispatch, work_item_id=message_id, dispatched_at=posted, learning_eligible=True,
        ) if o["observation_window"] == "DAILY")
        store.register_performance_observation(observation=daily)
        if now >= posted + timedelta(hours=24):
            # Only a reader capture at/after the due time can supply the 24-hour metrics.
            capture = row.get("metrics_observed_at_utc")
            if capture and posted + timedelta(hours=24) <= clock(capture) <= now:
                metrics, availability = {}, {}
                supplied = row.get("metrics", {})
                for name in ("views", "likes", "profile_visits"):
                    value_ = supplied.get(name)
                    if type(value_) in (int, float) and value_ >= 0 and value_ < float("inf"):
                        metrics[name], availability[name] = value_, "AVAILABLE"
                    else:
                        availability[name] = "NOT_EXPOSED" if name == "profile_visits" else "NOT_CAPTURED"
                store.mark_performance_observation_collected(
                    observation_id=daily["observation_id"], collection_status="COLLECTED" if metrics else "UNAVAILABLE",
                    collected_at_utc=clock(capture).isoformat(), metrics_native_json=json.dumps(metrics, sort_keys=True),
                    metric_availability_json=json.dumps(availability, sort_keys=True),
                    source_identity="contentops.x_feed_reader.manual_reply.v1",
                )
        observed.append({"post_id": post_id, "parent_post_id": parent, "target_author": item["author_handle"],
                         "readback_message_id": message_id, "dispatch_id": dispatch_id,
                         "daily_observation_id": daily["observation_id"]})
    return {"observed": observed, "causes": dict(causes), "public_write_performed": False,
            "reader_followup": {"own_replies_url": "https://x.com/Capitalnicle/with_replies",
                                "mentions_url": "https://x.com/notifications/mentions",
                                "action": "Use the existing signed-in reader's next bounded visit; pass its exact reply-edge rows with --reply-feed. No agent posts."}}


def report_manual_replies(store, *, now=None):
    """Fourteen-day cohorts by target, authored reply shape and actual ET build time."""
    now = now or utcnow()
    since = now - timedelta(days=14)
    cohorts, packs, first_built = {}, {}, None
    latency = {name: {"reply_count": 0, "collected_24h": 0, "views": None}
               for name in ("under_2h", "2_to_6h", "over_6h")}
    for row in store.list_outbox_messages(destination=PACK_DESTINATION):
        pack = json.loads(row["payload"])
        built = clock(pack["built_at_utc"])
        if built <= now:
            first_built = min(first_built, built) if first_built else built
        if not since <= built <= now:
            continue
        packs[row["message_id"]] = pack
        for item in pack["items"]:
            cohort = (item["author_handle"], item.get("reply_shape") or "unspecified",
                      clock(pack["built_at_utc"]).astimezone(ZoneInfo("America/New_York")).strftime("%H:%M ET"))
            group = cohorts.setdefault(cohort, {"target_author": cohort[0], "reply_shape": cohort[1],
                "build_time_et": cohort[2], "drafts": 0, "posted": 0,
                "views": None, "likes": None, "profile_visits": None, "collected_24h": 0})
            group["drafts"] += 1
    for row in store.list_outbox_messages(destination=READBACK_DESTINATION):
        value = json.loads(row["payload"])
        pack = packs.get(value["pack_message_id"])
        if not pack:
            continue
        cohort = (value["target_author"], value.get("reply_shape") or "unspecified",
                  clock(pack["built_at_utc"]).astimezone(ZoneInfo("America/New_York")).strftime("%H:%M ET"))
        group = cohorts[cohort]
        group["posted"] += 1
        target = next(i for i in pack["items"] if i["post_id"] == value["parent_post_id"])
        minutes = (clock(value["posted_at_utc"]) - clock(target["post_time_utc"])).total_seconds() / 60
        band = latency["under_2h" if minutes < 120 else "2_to_6h" if minutes <= 360 else "over_6h"]
        band["reply_count"] += 1
        for observation in store.list_performance_observations(dispatch_id="dispatch_" + row["message_id"]):
            if observation["observation_window"] != "DAILY" or observation["collection_status"] != "COLLECTED":
                continue
            group["collected_24h"] += 1
            band["collected_24h"] += 1
            metrics, available = json.loads(observation["metrics_native_json"]), json.loads(observation["metric_availability_json"])
            for name in ("views", "likes", "profile_visits"):
                if available.get(name) == "AVAILABLE" and name in metrics:
                    group[name] = (group[name] or 0) + metrics[name]
                    if name == "views":
                        band["views"] = (band["views"] or 0) + metrics[name]
    review_due = first_built + timedelta(days=14) if first_built else None
    return {"from_utc": since.isoformat(), "to_utc": now.isoformat(),
            "review_due_at_utc": review_due.isoformat() if review_due else None,
            "review_due": now >= review_due if review_due else False,
            "post_to_reply_latency": latency,
            "cohorts": sorted(cohorts.values(), key=lambda c: (-(c["views"] or 0), c["target_author"])),
            "public_write_performed": False}
