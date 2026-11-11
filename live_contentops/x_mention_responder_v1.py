"""Decision 122: summoned X replies through the sole publication coordinator.

CC-455 owns selection, source binding and native drafting. This adapter owns
official OAuth requests and a conservative prepaid-credit budget in the existing
store. It starts no timer, browser, model, account setup or payment operation.
"""
from __future__ import annotations

import base64
from collections import Counter
from dataclasses import replace
from datetime import timedelta
import hashlib
import hmac
import json
from pathlib import Path
import re
import secrets
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

from live_contentops import x_reply_pack_v1 as packs
from live_contentops.secret_store_v1 import read_secret
from live_contentops.sourced_replies_v1 import clock, digest

KEY_NAMES = ("X_API_KEY", "X_API_KEY_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")
HANDLE = "Capitalnicle"
API_ROOT = "https://api.x.com"
ROOT = packs.PACK_ROOT / "api"
DAILY_LIMIT_MICRO_USD = 500_000
POST_READ = 5_000
USER_READ = 10_000
SUMMONED_WRITE = 10_000
WRITE_CEILING = 15_000
URL_WRITE = 200_000
OPT_OUT_COPY = "Reply STOP to opt out."
POST_FIELDS = "post.fields"  # Current official Get Mentions reference, read 11 Nov 2026.
COSTS = "internal:x-api-cost"
SETTLEMENTS = "internal:x-api-cost-result"
MENTIONS = "internal:x-api-mentions"
CURSORS = "internal:x-api-mention-cursor"
OPTOUTS = "internal:x-api-mention-opt-out"
WARNINGS = "internal:x-api-mention-warning"
ID = re.compile(r"[0-9]{1,19}")
OPT_OUT = re.compile(r"\b(?:stop|unsubscribe|opt[ -]?out|do not reply|don't reply|no more replies)\b", re.I)


class ApiError(ValueError):
    """Only a fixed safe cause leaves the credential/HTTP boundary."""


def _values(store, destination):
    return [json.loads(r["payload"]) for r in store.list_outbox_messages(destination=destination)]


def _save(store, destination, key, value, status="RECORDED"):
    store.create_work_item(story_id=key, title="X API mention responder", target_surface="PRIVATE", work_item_id=key)
    store.register_outbox_message(message_id=key, work_item_id=key, destination=destination,
                                  payload=json.dumps(value, sort_keys=True), status=status)
    return key


def budget(store, *, now=None):
    now = now or packs.utcnow()
    day = now.astimezone(packs.LOCAL).date().isoformat()
    settled = {v["request_id"]: v for v in _values(store, SETTLEMENTS)}
    rows = [v for v in _values(store, COSTS) if v["spend_day_gmt7"] == day]
    upper = sum(settled.get(v["request_id"], v)["upper_bound_micro_usd"] for v in rows)
    estimate = sum(settled[v["request_id"]]["estimated_micro_usd"] for v in rows if v["request_id"] in settled)
    return {"spend_day_gmt7": day, "daily_limit_usd": 0.50,
            "cost_upper_bound_usd": upper / 1_000_000, "estimated_cost_usd": estimate / 1_000_000,
            "unresolved_request_count": sum(v["request_id"] not in settled for v in rows),
            "remaining_micro_usd": DAILY_LIMIT_MICRO_USD - upper,
            "invoice_cost_usd": None, "basis": "Published rates; no deduplication or Owned Read discount assumed for the cap"}


def _reserve_cost(store, method, path, ceiling, now):
    if not isinstance(ceiling, int) or not 0 < ceiling <= DAILY_LIMIT_MICRO_USD:
        raise ApiError("X_API_INVALID_COST_CEILING")
    request_id = "x-api-request-" + uuid4().hex
    lease = store.acquire_lease("x-api-prepaid-budget", request_id, ttl_seconds=30)
    try:
        state = budget(store, now=now)
        if ceiling > state["remaining_micro_usd"]:
            raise ApiError("X_API_DAILY_050_USD_CAP")
        _save(store, COSTS, request_id, {"request_id": request_id, "method": method, "path": path,
              "reserved_at_utc": now.isoformat(), "spend_day_gmt7": state["spend_day_gmt7"],
              "upper_bound_micro_usd": ceiling}, "RESERVED")
    finally:
        store.release_lease(lease["lease_id"], request_id, lease["fencing_token"])
    return request_id


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _wire(method, url, headers, body):
    request = Request(url, data=body, headers=headers, method=method)
    with build_opener(_NoRedirect()).open(request, timeout=15) as response:
        raw = response.read(1_048_577)
    if len(raw) > 1_048_576:
        raise ApiError("X_API_RESPONSE_TOO_LARGE")
    return json.loads(raw)


def oauth_header(method, url, params, keys, *, nonce, timestamp):
    """OAuth 1.0a HMAC-SHA1. Secrets stay in this in-memory request boundary."""
    def enc(value):
        return quote(str(value), safe="~")
    oauth = {"oauth_consumer_key": keys[0], "oauth_token": keys[2], "oauth_nonce": nonce,
             "oauth_signature_method": "HMAC-SHA1", "oauth_timestamp": str(timestamp), "oauth_version": "1.0"}
    normalized = "&".join(f"{k}={v}" for k, v in sorted((enc(k), enc(v)) for k, v in {**params, **oauth}.items()))
    base = "&".join(enc(v) for v in (method, url, normalized))
    signing_key = enc(keys[1]) + "&" + enc(keys[3])
    oauth["oauth_signature"] = base64.b64encode(hmac.new(signing_key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    return "OAuth " + ", ".join(f'{enc(k)}="{enc(v)}"' for k, v in sorted(oauth.items()))


class XApiClient:
    def __init__(self, store, *, secret_reader=None, wire=None, now=None):
        self.store = store
        self._secret_reader = secret_reader or read_secret
        self._wire = wire or _wire
        self.now = now or packs.utcnow
        self._account = None
        self.first_api_call = None
        self.network_calls = 0

    def request(self, method, path, *, params=None, body=None, max_posts=0, max_users=0,
                summoned=False):
        if not ((method == "GET" and re.fullmatch(r"/2/(?:users/me|users/[0-9]{1,19}/(?:mentions|tweets)|tweets/[0-9]{1,19})", path))
                or (method == "POST" and path == "/2/tweets" and summoned is True)):
            raise ApiError("X_API_ROUTE_OUTSIDE_MENTION_RESPONDER")
        params = params or {}
        self.first_api_call = self.first_api_call or {"method": method, "path": path}
        try:
            keys = tuple(self._secret_reader(name) for name in KEY_NAMES)
        except Exception:
            raise ApiError("X_API_SECRET_STORE_UNAVAILABLE") from None
        if not all(keys):
            raise ApiError("X_API_KEYS_NOT_SET")
        now = self.now()
        has_url = bool(body and re.search(r"https?://", body.get("text", "")))
        ceiling = (URL_WRITE if has_url else WRITE_CEILING) if method == "POST" else max_posts * POST_READ + max_users * USER_READ
        request_id = _reserve_cost(self.store, method, path, ceiling, now)
        url = API_ROOT + path
        headers = {"Authorization": oauth_header(method, url, params, keys,
                   nonce=secrets.token_hex(16), timestamp=int(now.timestamp())),
                   "Content-Type": "application/json", "Accept": "application/json"}
        payload = json.dumps(body).encode() if body is not None else None
        try:
            self.network_calls += 1
            value = self._wire(method, url + ("?" + urlencode(params) if params else ""), headers, payload)
            if not isinstance(value, dict) or value.get("errors"):
                raise ApiError("X_API_PARTIAL_OR_INVALID_RESPONSE")
            if method == "POST":
                upper, estimate = ceiling, URL_WRITE if has_url else SUMMONED_WRITE
                counts = {"writes": 1}
            else:
                data = value.get("data") or []
                data = [data] if isinstance(data, dict) else data
                includes = value.get("includes") or {}
                users = len(data) if path == "/2/users/me" else len(includes.get("users", []))
                posts = 0 if path == "/2/users/me" else len(data) + len(includes.get("tweets", []))
                if posts > max_posts or users > max_users:
                    raise ApiError("X_API_RESPONSE_EXCEEDS_RESERVED_RESOURCE_BOUND")
                upper = estimate = posts * POST_READ + users * USER_READ
                counts = {"posts": posts, "users": users}
            _save(self.store, SETTLEMENTS, request_id + "-result", {"request_id": request_id,
                  "upper_bound_micro_usd": upper, "estimated_micro_usd": estimate,
                  "resource_counts": counts, "observed_at_utc": self.now().isoformat(),
                  "invoice_cost_usd": None})
            return value
        except HTTPError as exc:
            raise ApiError("X_API_HTTP_" + str(exc.code)) from None
        except ApiError:
            raise
        except Exception as exc:
            raise ApiError("X_API_TRANSPORT_" + type(exc).__name__) from None

    def account(self):
        if self._account is None:
            data = self.request("GET", "/2/users/me", params={"user.fields": "username"}, max_users=1).get("data") or {}
            if str(data.get("username", "")).casefold() != HANDLE.casefold() or not ID.fullmatch(str(data.get("id", ""))):
                raise ApiError("X_API_WRONG_ACCOUNT_EXPECTED_CAPITALNICLE")
            self._account = data
        return self._account

    def post(self, post_id):
        if not ID.fullmatch(str(post_id)):
            raise ApiError("X_API_INVALID_POST_ID")
        return self.request("GET", "/2/tweets/" + str(post_id), max_posts=1,
                            params={POST_FIELDS: "author_id,created_at,entities,referenced_tweets"}).get("data") or {}


def _eligibility(client, post):
    account = client.account()
    if (not ID.fullmatch(str(post.get("id", ""))) or not ID.fullmatch(str(post.get("author_id", "")))
            or str(post["author_id"]) == str(account["id"])):
        raise ApiError("X_API_TARGET_IDENTITY_INVALID")
    references = post.get("referenced_tweets") or []
    if any(r.get("type") == "retweeted" for r in references):
        raise ApiError("X_API_RETWEET_NOT_AN_INTERACTION")
    mentions = (post.get("entities") or {}).get("mentions") or []
    if any((str(m.get("id")) == str(account["id"]) if m.get("id") else
            str(m.get("username", "")).casefold() == HANDLE.casefold()) for m in mentions):
        return {"kind": "mention", "account_id": account["id"]}
    for ref in references:
        if ref.get("type") == "quoted":
            quoted = client.post(ref["id"])
            if str(quoted.get("id")) == str(ref["id"]) and str(quoted.get("author_id")) == str(account["id"]):
                return {"kind": "quote", "account_id": account["id"], "quoted_post_id": ref["id"]}
    raise ApiError("X_API_TARGET_DID_NOT_MENTION_OR_QUOTE_ACCOUNT")


def _opted_out(store, author_id):
    return any(str(v["author_id"]) == str(author_id) for v in _values(store, OPTOUTS))


def fallback_pack(*, feed_path, mentions_path=None):
    """The installed manual pack remains usable; this function never posts."""
    feed = packs.read_json(feed_path)
    selected, causes = packs.select_posts(feed, handles=set(),
                                          mentions=packs.read_json(mentions_path) if mentions_path else None)
    stem = "reply-pack-" + packs.utcnow().astimezone(packs.LOCAL).strftime("%Y%m%d")
    return {"route": "CC455_JIM_CLICK", "mention_count_in_held_feed": len(selected),
            "pack_path": str(packs.PACK_ROOT / (stem + ".json")),
            "html_path": str(packs.PACK_ROOT / (stem + ".html")), "selection_causes": causes,
            "next_action": "Use pack-prepare/pack-build with the held mentions feed; Jim reviews and posts each intent"}


def poll(store, *, feed_path, output_root=ROOT, client=None, mentions_path=None, now=None):
    now = now or packs.utcnow()
    client = client or XApiClient(store)
    result = {"started_at_utc": now.isoformat(), "public_write_performed": False,
              "manual_fallback": fallback_pack(feed_path=feed_path, mentions_path=mentions_path)}
    try:
        account = client.account()  # The no-key acceptance reaches this real request boundary.
        cursors = _values(store, CURSORS)
        cursor = cursors[-1] if cursors else {}
        params = {"max_results": "5", POST_FIELDS: "author_id,created_at,entities,referenced_tweets",
                  "expansions": "author_id", "user.fields": "username"}
        query = cursor.get("query") or ({"since_id": cursor["since_id"]} if cursor.get("since_id") else
                                       {"start_time": (now - timedelta(minutes=60)).isoformat()})
        params.update(query)
        if cursor.get("pagination_token"):
            params["pagination_token"] = cursor["pagination_token"]
        value = client.request("GET", f"/2/users/{account['id']}/mentions", params=params, max_posts=5, max_users=5)
        users = {str(u["id"]): u for u in (value.get("includes") or {}).get("users", [])}
        rows, causes = [], Counter()
        for post in value.get("data") or []:
            try:
                proof = _eligibility(client, post)
                author_id = str(post["author_id"])
                if OPT_OUT.search(post["text"]):
                    if not _opted_out(store, author_id):
                        _save(store, OPTOUTS, "x-api-opt-out-" + author_id,
                              {"author_id": author_id, "post_id": post["id"], "observed_at_utc": now.isoformat()}, "OPTED_OUT")
                    raise ApiError("X_API_AUTHOR_OPTED_OUT")
                if _opted_out(store, author_id):
                    raise ApiError("X_API_AUTHOR_OPTED_OUT")
                handle = users.get(author_id, {}).get("username", "")
                if not re.fullmatch(r"[A-Za-z0-9_]{1,15}", handle):
                    raise ApiError("X_API_TARGET_AUTHOR_NOT_RESOLVED")
                rows.append({"tweet_id": str(post["id"]), "url": f"https://x.com/{handle}/status/{post['id']}",
                             "handle": handle, "posted_utc": post["created_at"], "text": post["text"],
                             "author_id": author_id, "is_retweet": False, "api_interaction": proof,
                             **({"quoted_author_handle": HANDLE} if proof["kind"] == "quote" else {})})
            except (ApiError, KeyError) as exc:
                causes[str(exc) if isinstance(exc, ApiError) else "X_API_MENTION_FIELDS_MISSING"] += 1
        feed = {"generated_at_utc": now.isoformat(), "rows": rows, "account_id": account["id"],
                "source": "X_OFFICIAL_API", "selection_causes": dict(causes)}
        source_id = "x-api-mentions-" + digest(feed)
        _save(store, MENTIONS, source_id, feed)
        feed = {**feed, "api_source_message_id": source_id}
        path = Path(output_root) / (source_id + ".json")
        packs.save_json(path, feed)
        meta = value.get("meta") or {}
        newest = max([int(v) for v in (cursor.get("newest_id"), meta.get("newest_id"), cursor.get("since_id")) if v], default=0)
        next_cursor = {"observed_at_utc": now.isoformat(), "newest_id": str(newest) if newest else None,
                       "pagination_token": meta.get("next_token"), "query": query if meta.get("next_token") else None,
                       "since_id": cursor.get("since_id") if meta.get("next_token") else str(newest) if newest else None}
        _save(store, CURSORS, "x-api-cursor-" + digest(next_cursor), next_cursor)
        preparation = packs.prepare(store, feed_path=feed_path, mentions_path=path,
                                    automated_mentions=True, output_root=packs.PACK_ROOT, now=now)
        result.update(status="MENTIONS_PREPARED", mentions_feed_path=str(path),
                      api_source_message_id=source_id, mention_count=len(rows),
                      selection_causes=dict(causes), editorial=preparation)
    except ApiError as exc:
        result.update(status=str(exc), first_api_call=client.first_api_call)
    result.update(network_calls=client.network_calls, cost=budget(store, now=now), completed_at_utc=packs.utcnow().isoformat())
    key = "x-api-run-" + digest(result)
    _save(store, "internal:x-api-mention-run", key, result, result["status"])
    path = Path(output_root) / (key + ".json")
    packs.save_json(path, result)
    return {**result, "run_record": str(path), "run_message_id": key}


def api_registration():
    from live_contentops.destination_transport_registry_v1 import registration_for_destination
    return replace(registration_for_destination("x"), transport_type="X_OFFICIAL_API")


def validate_row(row, *, store):
    if store is None or row.get("platform") != "x" or row.get("authority_ref") != "JIM_DECISION_122_CC456":
        raise ApiError("X_API_EXACT_MENTION_BINDING_REQUIRED")
    message = store.get_outbox_message(row["x_api_mention"])
    if not message or message["destination"] != MENTIONS:
        raise ApiError("X_API_OFFICIAL_MENTION_SOURCE_REQUIRED")
    feed = json.loads(message["payload"])
    target = next((r for r in feed["rows"] if r["tweet_id"] == row["target_id"]), None)
    if not target or target != row["api_target"] or row["target_url"] != target["url"]:
        raise ApiError("X_API_MENTION_TARGET_CHANGED")
    source = row["source"]
    options = {"desk_message_id" if source["kind"] == "MAIN_PUBLIC_DESK_FIELD" else "call_message_id": source["store_message_id"],
               "include_desk": source["kind"] == "MAIN_PUBLIC_DESK_FIELD", "include_calls": source["kind"] == "FROZEN_PUBLIC_CALL"}
    actual = next((v for v in packs.held_sources(store, **options) if v["source_id"] == source["source_id"]), None)
    if actual != source:
        raise ApiError("REPLY_SOURCE_BINDING_CHANGED")
    post = {"post_text": target["text"]}
    packs.validate_draft(row["draft"], post, actual, now=clock(row["created_at_utc"]),
                         published_urls={d["public_object_url"] for d in store.list_platform_dispatches()
                                         if d["platform"] == "substack" and d["status"] == "DISPATCH_CONFIRMED"})
    if row["text"] != row["draft"]["draft_text"] or OPT_OUT_COPY not in row["text"]:
        raise ApiError("X_API_OPT_OUT_COPY_REQUIRED")
    return row


def stage_from_pack(store, *, request_path, response_path, mentions_path, pack_path,
                    x_approval_ref=None, now=None):
    now = now or packs.utcnow()
    request, response = packs.read_json(request_path), packs.read_json(response_path)
    expected = digest({k: v for k, v in request.items() if k != "request_sha256"})
    if request.get("request_sha256") != expected or response.get("request_sha256") != expected:
        raise ApiError("REPLY_PACK_REQUEST_CHANGED")
    pack = packs.read_json(pack_path)
    if pack.get("request_sha256") != expected or pack.get("response_sha256") != digest(response):
        raise ApiError("X_API_EXACT_BUILT_PACK_REQUIRED")
    feed = packs.read_json(mentions_path)
    staged = []
    for item in pack["items"]:
        if item["kind"] != "mention":
            continue
        target = next((v for v in feed["rows"] if v["tweet_id"] == item["post_id"]), None)
        if not target:
            continue  # Browser-held mentions still go to Jim, never to this API adapter.
        draft = next(v for v in response["items"] if str(v["post_id"]) == item["post_id"])
        source = next(v for v in request["sources"] if v["source_id"] == draft["source_id"])
        source = {k: v for k, v in source.items() if k != "public_timestamp"}
        key = "reply-x-api-mention-" + item["post_id"]
        prior = store.get_outbox_message(key)
        if prior:
            staged.append(json.loads(prior["payload"]))
            continue
        row = {"key": key, "kind": "reply", "platform": "x", "target_id": item["post_id"],
               "target_url": item["post_url"], "target_author": item["author_handle"],
               "text": item["draft_text"], "point": item["point"], "image": None,
               "x_api_mention": feed["api_source_message_id"], "api_target": target,
               "draft": draft, "source": source, "editorial_call": response.get("editorial_call", {}),
               "created_at_utc": now.isoformat(), "authority_ref": "JIM_DECISION_122_CC456",
               "x_approval_ref": x_approval_ref}
        validate_row(row, store=store)
        from live_contentops.sourced_replies_v1 import DESTINATION
        _save(store, DESTINATION, key, row, "READY_FOR_PUBLISHER")
        staged.append(row)
    return staged


def require_publishable(store, row, now):
    validate_row(row, store=store)
    if not row.get("x_approval_ref"):
        raise ApiError("X_AI_REPLY_PRIOR_WRITTEN_APPROVAL_REQUIRED")
    age = (now - clock(row["api_target"]["posted_utc"])).total_seconds()
    if not 0 <= age < 90 * 60:
        raise ApiError("X_API_MENTION_DRAFT_STALE")
    if _opted_out(store, row["api_target"]["author_id"]):
        raise ApiError("X_API_AUTHOR_OPTED_OUT")
    if any(v.get("parent_post_id") == row["target_id"] for v in _values(store, packs.READBACK_DESTINATION)):
        raise ApiError("X_API_INTERACTION_ALREADY_ANSWERED_BY_JIM")
    if _values(store, WARNINGS):
        raise ApiError("X_API_MENTION_ROUTE_WARNING_STOP")


class XApiMentionTransport:
    """A scoped transport bound to DurablePublicationCoordinator, never a publisher."""
    def __init__(self, store, client=None):
        self.store = store
        self.client = client or XApiClient(store)

    def publish(self, *, destination, intent, authorization_context):
        from live_contentops.sourced_replies_v1 import validate_intent
        row = validate_intent(self.store, intent)
        if (destination != "x" or not row.get("x_api_mention") or
                authorization_context.get("work_item_id") != row["key"] or
                not authorization_context.get("dispatch_attempt_identity")):
            raise ApiError("SOLE_COORDINATOR_MENTION_AUTHORIZATION_REQUIRED")
        try:
            require_publishable(self.store, row, self.client.now())
            current = self.client.post(row["target_id"])
            _eligibility(self.client, current)
            if current.get("author_id") != row["api_target"]["author_id"] or current.get("text") != row["api_target"]["text"]:
                raise ApiError("X_API_MENTION_TARGET_CHANGED")
            cost = URL_WRITE if re.search(r"https?://", row["text"]) else WRITE_CEILING
            if budget(self.store, now=self.client.now())["remaining_micro_usd"] < cost + POST_READ:
                raise ApiError("X_API_DAILY_050_USD_CAP")
        except ApiError as exc:
            return {"status": "DEFINITE_NO_WRITE", "definite_no_write": True, "safe_error_classification": str(exc)}
        try:
            value = self.client.request("POST", "/2/tweets", body={"text": row["text"],
                                        "reply": {"in_reply_to_tweet_id": row["target_id"]}}, summoned=True)
        except ApiError as exc:
            cause = str(exc)
            if cause.startswith("X_API_HTTP_") and cause.rsplit("_", 1)[-1] in {"400", "401", "402", "403", "404", "429"}:
                if cause.endswith(("403", "429")):
                    _save(self.store, WARNINGS, "x-api-mention-warning-" + uuid4().hex,
                          {"cause": cause, "observed_at_utc": self.client.now().isoformat()})
                return {"status": "DEFINITE_NO_WRITE", "definite_no_write": True, "safe_error_classification": cause}
            raise  # A timeout or invalid return remains UNKNOWN_WRITE under the coordinator.
        post_id = str((value.get("data") or {}).get("id", ""))
        if not ID.fullmatch(post_id):
            raise ApiError("X_API_WRITE_RETURN_ID_MISSING")
        return {"status": "SUCCESS", "public_object_id": post_id,
                "public_object_url": f"https://x.com/{HANDLE}/status/{post_id}"}

    def readback(self, *, destination, intent, public_object_id, public_object_url):
        from live_contentops.sourced_replies_v1 import validate_intent
        row = validate_intent(self.store, intent)
        if destination != "x" or not row.get("x_api_mention"):
            raise ApiError("X_API_EXACT_MENTION_BINDING_REQUIRED")
        account = self.client.account()
        if public_object_id:
            posts = [self.client.post(public_object_id)]
        else:
            # A bounded account read can find a lost return; a miss never proves absence.
            value = self.client.request("GET", f"/2/users/{account['id']}/tweets", max_posts=5,
                                        params={"max_results": "5", POST_FIELDS: "author_id,created_at,entities,referenced_tweets"})
            posts = value.get("data") or []
        matches = []
        for post in posts:
            text = post.get("text", "")
            for link in (post.get("entities") or {}).get("urls", []):
                text = text.replace(link["url"], link.get("expanded_url") or link["url"])
            if (str(post.get("author_id")) == str(account["id"]) and text == row["text"]
                    and any(r.get("type") == "replied_to" and str(r.get("id")) == row["target_id"] for r in post.get("referenced_tweets", []))
                    and (not public_object_id or str(post.get("id")) == str(public_object_id))
                    and clock(post.get("created_at")) >= clock(row["created_at_utc"])):
                matches.append(post)
        if len(matches) != 1:
            return {"status": "UNKNOWN_WRITE", "verified": False}
        post = matches[0]
        return {"status": "SUCCESS", "verified": True, "write_exists": True,
                "public_object_id": post["id"], "public_object_url": f"https://x.com/{HANDLE}/status/{post['id']}",
                "published_at_utc": post["created_at"], "content_binding_checks": {
                    "text_match": True, "thread_match": True, "account_match": True}}


def bind_coordinator(store, *, client=None):
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    transport = XApiMentionTransport(store, client)
    def readiness(destination):
        if destination != "x":
            raise ApiError("X_API_ROUTE_OUTSIDE_MENTION_RESPONDER")
        account = transport.client.account()
        return {"readiness_state": "READY_NON_BROWSER_BINDING", "identity": account["username"]}
    return DurablePublicationCoordinator(store=store, transport_runtime=transport, readiness_provider=readiness)


def publish_from_request(store, *, request_path, response_path, feed_path, mentions_path,
                         output_root=ROOT, x_approval_ref=None, client=None, now=None):
    """Consume the actual native return; retain Jim's pack and use the same publisher."""
    from live_contentops.sourced_replies_v1 import publish
    now = now or packs.utcnow()
    built = packs.build(store, request_path=request_path, response_path=response_path,
                        feed_path=feed_path, mentions_path=mentions_path, now=now)
    rows = stage_from_pack(store, request_path=request_path, response_path=response_path,
                           mentions_path=mentions_path, pack_path=built["pack_path"],
                           x_approval_ref=x_approval_ref, now=now)
    client = client or XApiClient(store)
    coordinator = bind_coordinator(store, client=client)
    outcomes = []
    for row in rows:
        try:
            outcome = publish(store, row["key"], coordinator=coordinator, root=output_root, now=now)
            outcomes.append({"key": row["key"], **outcome})
        except ApiError as exc:
            outcomes.append({"key": row["key"], "status": str(exc)})
    result = {"status": "MENTION_PUBLICATION_RUN", "pack": built, "replies": outcomes,
              "cost": budget(store, now=now), "completed_at_utc": packs.utcnow().isoformat()}
    key = "x-api-publish-run-" + digest(result)
    _save(store, "internal:x-api-mention-run", key, result)
    path = Path(output_root) / (key + ".json")
    packs.save_json(path, result)
    return {**result, "run_record": str(path), "run_message_id": key}
