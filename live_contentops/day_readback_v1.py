"""CC-639: a read-only projection for the existing evening digest consumer.

No coordinator, browser, account session, model, store migration or retry is used.
Only the two day_readback files are written, by write_report().
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE, PublishedContentError, read_records

LOCAL = timezone(timedelta(hours=7))
ROUTES = ("substack", "substack_notes", "telegram", "x", "discord", "linkedin",
          "linkedin_company", "facebook_page", "instagram_business", "threads", "youtube")
REPLY_PREFIX = "internal:x-reply-bot-"
PRIVATE_KEY = re.compile(r"chat|token|secret|webhook|phone|user_id|binding", re.I)
CODE = re.compile(r"[A-Z][A-Z0-9_]{1,159}\Z")
MAX_PAGE_BYTES = 2 * 1024 * 1024


def utc(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("EXPLICIT_CLOCK_REQUIRED")
    return parsed.astimezone(timezone.utc)


def iso(value):
    return value.astimezone(timezone.utc).isoformat()


def code(value):
    return value if isinstance(value, str) and CODE.fullmatch(value) else None


def first_cause(value):
    """Keep fixed diagnostics, never serialize arbitrary exception or private text."""
    if not isinstance(value, dict):
        return None
    for key in ("first_cause", "first_blocking_cause", "reason_code", "cause", "error_code"):
        if result := code(value.get(key)):
            return result
    for key in ("causes", "selection_causes"):
        if isinstance(value.get(key), dict):
            for cause, count in value[key].items():
                if count and code(cause):
                    return cause
    for key in ("result", "readback", "delivery"):
        if result := first_cause(value.get(key)):
            return result
    return None


def safe_url(value):
    """Only public object URLs, with no credentials or arbitrary query fields."""
    if not isinstance(value, str):
        return None
    try:
        u = urlsplit(value)
        host = (u.hostname or "").lower()
        allowed = (host.endswith(".substack.com") or host in {
            "substack.com", "t.me", "x.com", "www.x.com", "discord.com",
            "www.linkedin.com", "linkedin.com", "www.facebook.com", "facebook.com",
            "www.instagram.com", "instagram.com", "www.threads.com", "threads.com",
            "www.threads.net", "threads.net", "www.youtube.com", "youtube.com"})
        if (not allowed or u.scheme != "https" or u.username or u.password
                or u.port not in (None, 443) or any(c.isspace() for c in value)):
            return None
        if any(PRIVATE_KEY.search(k) or k not in {"lb", "id", "story_fbid", "embed"}
               for k, _ in parse_qsl(u.query)):
            return None
        if host == "t.me" and not re.fullmatch(r"/CapitalChronicle/\d+", u.path, re.I):
            return None
        if host == "discord.com" and not re.fullmatch(r"/channels/\d+/\d+/\d+", u.path):
            return None
        return urlunsplit((u.scheme, u.netloc, u.path, u.query, ""))
    except ValueError:
        return None


def public_get_url(platform, value):
    value = safe_url(value)
    if not value:
        return None
    u = urlsplit(value)
    if (platform == "telegram" and u.hostname == "t.me"
            and re.fullmatch(r"/CapitalChronicle/\d+", u.path, re.I)):
        return urlunsplit(("https", "t.me", u.path, "embed=1", ""))
    if platform == "substack" and u.hostname == "capitalchronicle.substack.com" and u.path.startswith("/p/"):
        return value
    if platform == "substack_notes" and u.hostname in {"substack.com", "capitalchronicle.substack.com"}:
        if re.fullmatch(r"/(?:@capitalchronicle/)?note/c-[\w-]+", u.path):
            return value
    return None


class _PublicRedirects(HTTPRedirectHandler):
    def __init__(self, platform):
        self.platform = platform

    def redirect_request(self, req, fp, status, msg, headers, newurl):
        # Do not follow a public URL to sign-in, Telegram Web, X or an arbitrary host.
        allowed = public_get_url(self.platform, newurl)
        if not allowed:
            raise HTTPError(req.full_url, status, "PUBLIC_REDIRECT_NOT_ALLOWED", headers, fp)
        return super().redirect_request(req, fp, status, msg, headers, allowed)


def fetch_public(platform, url, *, timeout=8):
    target = public_get_url(platform, url)
    if not target:
        return {"http_status": None, "first_cause": "PUBLIC_GET_NOT_ALLOWED"}
    request = Request(target, headers={"User-Agent": "CapitalChronicle-DayReadback/1.0",
                                      "Accept": "text/html"}, method="GET")
    try:
        with build_opener(_PublicRedirects(platform)).open(request, timeout=timeout) as response:
            raw = response.read(MAX_PAGE_BYTES + 1)
            if len(raw) > MAX_PAGE_BYTES:
                return {"http_status": response.status, "first_cause": "PUBLIC_PAGE_TOO_LARGE"}
            return {"http_status": response.status,
                    "html": raw.decode(response.headers.get_content_charset() or "utf-8", errors="replace")}
    except HTTPError as exc:
        exc.close()
        return {"http_status": exc.code, "first_cause": "HTTP_" + str(exc.code)}
    except (TimeoutError, URLError, OSError, ValueError) as exc:
        return {"http_status": None, "first_cause": "HTTP_TIMEOUT" if isinstance(exc, TimeoutError)
                else "PUBLIC_HTTP_UNAVAILABLE"}


@dataclass
class _Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def hidden(self):
        return (self.tag in {"script", "style", "noscript"} or "hidden" in self.attrs
                or self.attrs.get("aria-hidden") == "true"
                or re.search(r"display\s*:\s*none|visibility\s*:\s*hidden", self.attrs.get("style", ""), re.I))

    def text(self):
        if self.hidden():
            return ""
        return " ".join(c.text() if isinstance(c, _Node) else c for c in self.children)

    def walk(self):
        if self.hidden():
            return
        yield self
        for child in self.children:
            if isinstance(child, _Node):
                yield from child.walk()


class _HTML(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = _Node("root")
        self.stack = [self.root]
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if not any(n.tag in {"script", "style", "noscript"} for n in self.stack):
            self.stack[-1].children.append(data)


def _plain(value):
    value = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", value or "")
    value = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", value)
    value = _HTML(value).root.text() if "<" in value else value
    return " ".join(re.sub(r"[*_`#]+", "", unescape(value)).split())


def _tokens(value):
    # A link can render with a descriptive label; its target is checked separately.
    return re.findall(r"\w+", re.sub(r"https?://\S+", " ", _plain(value)).casefold())


def _contains_in_order(needle, haystack):
    remaining = iter(haystack)
    return all(any(word == candidate for candidate in remaining) for word in needle)


def _links(value):
    without_images = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", value or "")
    links = re.findall(
        r"\[[^\]\n]+\]\((https?://[^)\s]+)\)|(https?://[^\s<>\"']+)",
        unescape(without_images),
    )
    return sorted({markdown_target or bare_url for markdown_target, bare_url in links})


def _link_identity(value, base_url=""):
    try:
        u = urlsplit(urljoin(base_url, value.rstrip(".,;:)")))
        if u.scheme in {"http", "https"} and u.hostname:
            query = tuple(sorted((k, v) for k, v in parse_qsl(u.query)
                                 if not k.startswith("utm_") and k not in {"fbclid", "gclid"}))
            return u.netloc.lower(), u.path.rstrip("/"), query
    except ValueError:
        pass
    return None


def check_public_text(platform, html, *, expected_text="", expected_title="", page_url=""):
    """Inspect the post body, never a menu, script, metadata or another post."""
    nodes = list(_HTML(html).root.walk())
    body = None
    if platform == "telegram":
        body = next((n for n in nodes if "tgme_widget_message_text" in n.attrs.get("class", "").split()), None)
    elif platform == "substack_notes":
        # Substack's public permalink scopes the root Note separately from replies.
        permalink = next((n for n in nodes if any(
            name.startswith("feedPermalinkUnit-") for name in n.attrs.get("class", "").split())), None)
        if permalink is not None:
            body = next((n for n in permalink.walk() if any(
                name.startswith("feedCommentBody-") for name in n.attrs.get("class", "").split())), None)
        else:
            body = next((n for n in nodes if {"comment-body", "note-body"}.intersection(n.attrs.get("class", "").split())
                         or n.attrs.get("data-testid") in {"comment-body", "note-body"}), None)
    else:
        body = next((n for n in nodes if n.tag == "article"), None)
        if body is None:
            classes = {"available-content", "markup", "comment-body", "note-body"}
            body = next((n for n in nodes if classes.intersection(n.attrs.get("class", "").split())
                         or n.attrs.get("data-testid") in {"comment-body", "note-body"}), None)
    if body is None:
        return {"first_line_matches": None, "text_complete": None, "links_match": None,
                "first_cause": "PUBLIC_POST_TEXT_UNAVAILABLE", "exceptions": ["PUBLIC_POST_TEXT_UNAVAILABLE"]}
    text = body.text()
    headings = " ".join(n.text() for n in nodes if n.tag == "h1") if platform == "substack" else ""
    first = expected_title or next((line for line in expected_text.splitlines() if line.strip()), "")
    first_matches = (_contains_in_order(_tokens(first), _tokens(headings + " " + text)) if first else None)
    complete = _contains_in_order(_tokens(expected_text), _tokens(headings + " " + text)) if expected_text else None
    found_links = [n.attrs["href"] for n in body.walk() if n.tag == "a" and "href" in n.attrs]
    found_links.extend(_links(text))
    expected_links = {_link_identity(u) for u in _links(expected_text)}
    actual_links = {_link_identity(u, page_url) for u in found_links}
    missing = len(expected_links - actual_links)
    exceptions = []
    if first_matches is False:
        exceptions.append("PUBLIC_TEXT_MISMATCH")
    elif complete is False:
        exceptions.append("PUBLIC_TEXT_CUT_OFF")
    if missing:
        exceptions.append("PUBLIC_LINK_MISSING")
    if first_matches is None:
        exceptions.append("STORED_PUBLIC_TEXT_UNAVAILABLE")
    return {"first_line_matches": first_matches, "text_complete": complete,
            "links_match": not missing if expected_links else None, "missing_link_count": missing,
            "first_cause": next(iter(exceptions), None), "exceptions": exceptions}


def report_window(run_dir, *, since=None, until=None, now=None):
    run_dir = Path(run_dir)
    result_path = run_dir / "result.json"
    result = json.loads(result_path.read_bytes()) if result_path.is_file() else {}
    now = now or datetime.now(timezone.utc)
    end = utc(until) if until else utc(result["recorded_at_utc"]) if result.get("recorded_at_utc") else now
    try:
        entry = datetime.strptime(run_dir.name, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        entry = end
    previous = []
    if not since:
        for folder in run_dir.parent.iterdir():
            if folder.is_dir() and folder != run_dir and (folder / "result.json").is_file():
                try:
                    clock = datetime.strptime(folder.name, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
                    if clock < entry:
                        previous.append(clock)
                except ValueError:
                    continue
    if since:
        start, source = utc(since), "EXPLICIT"
    elif previous:
        start, source = max(previous), "PREVIOUS_RUN_FOLDER_ENTRY"
    else:
        local = entry.astimezone(LOCAL)
        start = datetime.combine(local.date() - timedelta(days=1), time(19, 15), LOCAL)
        source = "PREVIOUS_SCHEDULED_1915_NO_PREVIOUS_RUN_RETAINED"
    if start >= end:
        raise ValueError("REPORT_WINDOW_EMPTY_OR_REVERSED")
    return {"since_utc": iso(start), "until_utc": iso(end), "cut_source": source}, result


def _failure(status):
    return status in {"UNKNOWN_WRITE", "DEFINITE_NO_WRITE"} or str(status).startswith("RECONCILED_ABSENT")


def _expected(intent):
    native = intent.get("native_payload") or {}
    if isinstance(native, dict):
        for key in ("full_text", "text", "body_markdown"):
            if isinstance(native.get(key), str):
                return native[key]
    return intent.get("payload") if isinstance(intent.get("payload"), str) else ""


def _public_rows(conn, window, feed):
    marks = ",".join("?" for _ in ROUTES)
    base = ("SELECT m.message_id,m.work_item_id,m.destination,m.status AS outbox_status,m.created_at,m.payload,"
            "d.dispatch_id,d.status,d.dispatched_at,d.public_object_id,d.public_object_url "
            "FROM outbox_messages m LEFT JOIN platform_dispatches d ON m.message_id=d.message_id ")
    span = (window["since_utc"], window["until_utc"])
    rows = conn.execute(base + f"WHERE m.destination IN ({marks}) AND ("
        "julianday(m.created_at) > julianday(?) AND julianday(m.created_at) <= julianday(?) OR "
        "julianday(d.dispatched_at) > julianday(?) AND julianday(d.dispatched_at) <= julianday(?) OR "
        "EXISTS (SELECT 1 FROM readbacks r WHERE r.dispatch_id=d.dispatch_id AND "
        "julianday(r.read_at) > julianday(?) AND julianday(r.read_at) <= julianday(?)) OR "
        "EXISTS (SELECT 1 FROM reconciliations r WHERE r.work_item_id=m.work_item_id AND "
        "julianday(r.reconciled_at) > julianday(?) AND julianday(r.reconciled_at) <= julianday(?)) OR "
        "EXISTS (SELECT 1 FROM outbox_messages n WHERE n.work_item_id=m.work_item_id "
        "AND n.destination='internal:native-neo-tool' AND julianday(n.created_at) > julianday(?) "
        "AND julianday(n.created_at) <= julianday(?)))",
        (*ROUTES, *span, *span, *span, *span, *span)).fetchall()
    urls = [o["url"] for f in feed for o in f["outlets"] if o["name"] == "substack"]
    for url in urls:
        rows.extend(conn.execute(base + "WHERE d.public_object_url=? AND m.destination='substack'", (url,)))
    work_ids = {r["work_item_id"] for r in rows}
    by_id = {}
    for work_id in sorted(work_ids):
        for row in conn.execute(base + f"WHERE m.work_item_id=? AND m.destination IN ({marks})", (work_id, *ROUTES)):
            # Don't turn an outbox created after a historical report's end into that day's post.
            if utc(row["created_at"]) <= utc(window["until_utc"]):
                by_id[(row["message_id"], row["dispatch_id"])] = dict(row)
    return list(by_id.values())


def _native_observations(conn, work_id, until):
    """Reuse stored request/return diagnostics when a dispatch has no readback yet."""
    requests, returns = {}, []
    for row in conn.execute("""SELECT created_at,
        json_extract(payload,'$.request.request_sha256') AS request_hash,
        json_extract(payload,'$.request.destination') AS platform,
        json_extract(payload,'$.result.request_sha256') AS response_hash,
        json_extract(payload,'$.result.status') AS status,
        json_extract(payload,'$.result.reason_code') AS reason_code,
        json_extract(payload,'$.result.first_cause') AS first_cause
        FROM outbox_messages WHERE work_item_id=? AND destination='internal:native-neo-tool'
        AND julianday(created_at) <= julianday(?) ORDER BY created_at,message_id""", (work_id, until)):
        if row["request_hash"] and row["platform"] in ROUTES:
            requests[row["request_hash"]] = row["platform"]
        if row["response_hash"] and row["status"]:
            returns.append(dict(row))
    by_platform = defaultdict(list)
    for row in returns:
        platform = requests.get(row["response_hash"])
        if platform:
            by_platform[platform].append((row["created_at"], {"status": row["status"],
                "reason_code": code(row["reason_code"]), "first_cause": code(row["first_cause"])}))
    return by_platform


def _digest(conn, run_dir, result):
    digest_id = result.get("digest_id")
    packet = {}
    if digest_id:
        row = conn.execute("SELECT message_id,payload FROM outbox_messages WHERE destination=? AND work_item_id=?",
                           ("internal:substack-daily-digest", digest_id)).fetchone()
        if row:
            packet = json.loads(row["payload"])
    summary = {"digest_id": digest_id, "state": code(result.get("final_route_state")) or "RUN_RESULT_UNAVAILABLE",
               "first_cause": first_cause(result),
               "packet_message_id": row["message_id"] if digest_id and packet else None,
               "packet_present": bool(packet), "article_count": len(packet.get("articles", [])),
               "cutoff_utc": packet.get("cutoff_utc"), "public_url": safe_url(result.get("public_object_url")),
               "recipients": None, "opens": None, "open_rate_percent": None, "email_confirmed": None,
               "metrics_observed_at_utc": None}
    # The retained dashboard observation, never Gmail or an account/credential file.
    for path in sorted(Path(run_dir).glob("*readback-observation.json")):
        if not path.resolve().is_relative_to(Path(run_dir).resolve()):
            continue
        observed = json.loads(path.read_bytes())
        if (observed.get("public_page") or {}).get("url") != summary["public_url"]:
            continue
        email = observed.get("email") or {}
        summary["email_confirmed"] = email.get("email_delivery_confirmed")
        for read in email.get("reads", []):
            shown = read.get("shown", "")
            for key, pattern in (("recipients", r"Recipients\s+([\d,]+)"),
                                 ("opens", r"([\d,]+)\s+opens?\b"),
                                 ("open_rate_percent", r"Open rate\s+([\d.]+)%")):
                match = re.search(pattern, shown, re.I)
                if match:
                    number = match[1].replace(",", "")
                    summary[key] = float(number) if "." in number else int(number)
            summary["metrics_observed_at_utc"] = read.get("at_utc") or observed.get("observed_at_utc")
    return summary, packet.get("native_payload", {})


def _reply_bot(conn, window):
    counts, causes, delivered = defaultdict(Counter), Counter(), {}
    # JSON projections avoid loading draft text, personal identifiers or the large tick payloads.
    query = """SELECT destination,status,created_at,
        json_extract(payload,'$.cause') AS cause,
        json_extract(payload,'$.first_cause') AS first_cause,
        json_extract(payload,'$.causes') AS causes,
        json_extract(payload,'$.selection_causes') AS selection_causes,
        json_extract(payload,'$.delivery.causes') AS delivery_causes,
        json_extract(payload,'$.post_id') AS post_id,
        json_extract(payload,'$.kind') AS kind,
        json_extract(payload,'$.delivered_at_utc') AS delivered_at_utc
        FROM outbox_messages WHERE destination LIKE 'internal:x-reply-bot-%'
        AND julianday(created_at) > julianday(?) AND julianday(created_at) <= julianday(?)
        ORDER BY created_at,message_id"""
    for row in conn.execute(query, (window["since_utc"], window["until_utc"])):
        kind = row["destination"].removeprefix(REPLY_PREFIX)
        status = code(row["status"]) or "UNRECOGNIZED_STATUS"
        counts[kind][status] += 1
        value = {key: row[key] for key in ("cause", "first_cause")}
        for key in ("causes", "selection_causes", "delivery_causes"):
            if row[key]:
                value["causes" if key == "delivery_causes" else key] = json.loads(row[key])
        if cause := first_cause(value):
            causes[cause] += 1
        post = str(row["post_id"] or "")
        if post.isdigit() and (kind == "delivery" and status == "DELIVERED"
                              or row["kind"] == "private_draft_delivered"):
            delivered.setdefault(post, {"post_id": post, "status": "DELIVERED", "delivered_at_utc": None})
            if row["delivered_at_utc"]:
                delivered[post]["delivered_at_utc"] = row["delivered_at_utc"]
    # Codes are values, not dynamic JSON keys: e.g. a named credentials cause must
    # not create a key containing a forbidden private-field word.
    return {"counts_by_kind_and_status": [{"kind": kind, "status": status, "count": count}
                for kind, values in sorted(counts.items()) for status, count in sorted(values.items())],
            "counts_by_first_cause": [{"first_cause": cause, "count": count} for cause, count in sorted(causes.items())],
            "delivered_count": len(delivered),
            "delivered_drafts": list(delivered.values())}


def build_report(run_dir, *, store_path=PRODUCTION_STORE, feed_path=DEFAULT_FEED,
                 since=None, until=None, now=None, fetcher=fetch_public):
    now = now or datetime.now(timezone.utc)
    window, result = report_window(run_dir, since=since, until=until, now=now)
    report = {"schema_version": "contentops.day_readback.v1", "observed_at_utc": iso(now),
              "window": window, "pieces": [], "exceptions": [],
              "store_open_mode": "ro", "public_writes": 0, "browser_opens": 0, "model_calls": 0}
    start, end = utc(window["since_utc"]), utc(window["until_utc"])
    cache, expected = {}, {}

    def exception(cause, piece, platform=None, row=None, status=None):
        report["exceptions"].append({"piece_id": piece, "platform": platform,
            "message_id": row.get("message_id") if row else None,
            "dispatch_id": row.get("dispatch_id") if row else None,
            "status": status, "first_cause": cause,
            "public_url": safe_url(row.get("public_object_url") or row.get("public_url")) if row else None})

    try:
        feed = [r for r in read_records(feed_path) if start < utc(r["published_at_utc"]) <= end
                and utc(r["recorded_at_utc"]) <= end]
    except (OSError, PublishedContentError) as exc:
        # A broken export does not hide the public identities/readbacks held in the store.
        feed = []
        exception(code(str(exc)) or "PUBLICATION_FEED_UNREADABLE", "publication_feed")

    def http_check(platform, url, text="", title=""):
        target = public_get_url(platform, url)
        if not target:
            return None
        if target not in cache:
            cache[target] = {**fetcher(platform, target), "checked_at_utc": iso(datetime.now(timezone.utc))}
        response = cache[target]
        status = response.get("http_status")
        cause = code(response.get("first_cause"))
        checked = {"checked_at_utc": response["checked_at_utc"], "http_status": status}
        if cause or status != 200:
            return {**checked, "first_cause": cause or "HTTP_" + str(status),
                    "first_line_matches": None, "text_complete": None, "links_match": None,
                    "exceptions": [cause or "PUBLIC_HTTP_UNAVAILABLE"]}
        return {**checked, **check_public_text(platform, response.get("html", ""),
                                               expected_text=text, expected_title=title, page_url=target)}

    with closing(sqlite3.connect(Path(store_path).resolve().as_uri() + "?mode=ro", uri=True, timeout=5)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        rows = _public_rows(conn, window, feed)
        groups = defaultdict(list)
        for row in rows:
            groups[row["work_item_id"]].append(row)
        feed_by_url = {o["url"]: f for f in feed for o in f["outlets"] if o["name"] == "substack"}
        consumed = set()
        for work_id, group in sorted(groups.items()):
            if work_id == result.get("digest_id"):
                continue  # This run's digest has its own packet/page/delivery section.
            sealed = next((feed_by_url[r["public_object_url"]] for r in group
                           if r["destination"] == "substack" and r["public_object_url"] in feed_by_url), None)
            if sealed:
                consumed.add(sealed["content_id"])
            piece_id = sealed["content_id"] if sealed else work_id
            piece = {"piece_id": piece_id, "title": sealed["title"] if sealed else None,
                     "published_at_utc": sealed["published_at_utc"] if sealed else None, "platforms": []}
            required = {o["name"] for o in sealed["outlets"]} if sealed else set()
            actual = set()
            native = _native_observations(conn, work_id, window["until_utc"])
            for row in group:
                platform = row["destination"]
                actual.add(platform)
                intent = json.loads(row["payload"])
                required.update(d for key in ("required_publication_destinations", "required_derivative_destinations")
                                for d in intent.get(key, []) if d in ROUTES)
                history = []
                if row["dispatch_id"]:
                    for read in conn.execute("SELECT readback_data,read_at FROM readbacks WHERE dispatch_id=? ORDER BY read_at,readback_id",
                                             (row["dispatch_id"],)):
                        if utc(read["read_at"]) <= end:
                            history.append((read["read_at"], json.loads(read["readback_data"])))
                diagnostics = sorted(history + native.get(platform, []), key=lambda item: utc(item[0]))
                cause = next((c for _, value in diagnostics if (c := first_cause(value))), None)
                status = row["status"] or row["outbox_status"]
                route = {"platform": platform, "message_id": row["message_id"], "dispatch_id": row["dispatch_id"],
                         "status": status, "outbox_status": row["outbox_status"], "first_cause": cause,
                         "public_url": safe_url(row["public_object_url"]), "store_readback": None}
                if history:
                    observed = history[-1][1].get("readback", history[-1][1])
                    route["store_readback"] = {"read_at_utc": history[-1][0],
                        **{k: observed[k] for k in ("verified", "write_exists", "write_absent", "source_status") if k in observed}}
                if _failure(status):
                    route["first_cause"] = cause or "FIRST_CAUSE_NOT_RECORDED"
                    exception(route["first_cause"], piece_id, platform, row, status)
                prior_failures = set()
                for clock, value in diagnostics:
                    if start < utc(clock) and _failure(value.get("status")) and value.get("status") != status:
                        failure = (value["status"], first_cause(value) or "FIRST_CAUSE_NOT_RECORDED")
                        if failure not in prior_failures:
                            exception(failure[1], piece_id, platform, row, failure[0])
                            prior_failures.add(failure)
                expected[row["message_id"]] = (_expected(intent), sealed["title"] if sealed and platform == "substack" else "")
                route["public_readback"] = None
                piece["platforms"].append(route)
            for platform in sorted(required - actual):
                piece["platforms"].append({"platform": platform, "status": "MISSING_ROW", "first_cause": "EXPECTED_PLATFORM_ROW_MISSING",
                                           "public_url": None, "store_readback": None, "public_readback": None})
                exception("EXPECTED_PLATFORM_ROW_MISSING", piece_id, platform, status="MISSING_ROW")
            report["pieces"].append(piece)
        for sealed in feed:
            if sealed["content_id"] not in consumed:
                piece = {"piece_id": sealed["content_id"], "title": sealed["title"],
                         "published_at_utc": sealed["published_at_utc"], "platforms": []}
                for outlet in sealed["outlets"]:
                    route = {"platform": outlet["name"], "status": "MISSING_ROW", "first_cause": "SEALED_OUTLET_STORE_ROW_MISSING",
                             "public_url": safe_url(outlet["url"]), "store_readback": None, "public_readback": None}
                    piece["platforms"].append(route)
                    exception("SEALED_OUTLET_STORE_ROW_MISSING", sealed["content_id"], outlet["name"], route, status="MISSING_ROW")
                report["pieces"].append(piece)
        report["digest"], digest_copy = _digest(conn, run_dir, result)
        report["reply_bot"] = _reply_bot(conn, window)
        seen = {(e["message_id"], e["status"]) for e in report["exceptions"]}
        # A contradictory outbox status, or an uncertain private reply delivery,
        # is still an exception even when it has no public dispatch row.
        for row in conn.execute("""SELECT message_id,work_item_id,destination,status,
            json_extract(payload,'$.reason_code') AS reason_code,
            json_extract(payload,'$.cause') AS cause
            FROM outbox_messages WHERE (status IN ('UNKNOWN_WRITE','DEFINITE_NO_WRITE')
            OR status LIKE 'RECONCILED_ABSENT%') AND julianday(created_at) > julianday(?)
            AND julianday(created_at) <= julianday(?) ORDER BY created_at,message_id""",
            (window["since_utc"], window["until_utc"])):
            if (row["message_id"], row["status"]) not in seen:
                exception(first_cause(dict(row)) or "FIRST_CAUSE_NOT_RECORDED", row["work_item_id"],
                          row["destination"] if row["destination"] in ROUTES else "internal", dict(row), row["status"])
    # Release the SQLite snapshot before doing any HTTP. A slow page cannot keep
    # the production reader transaction open throughout the network pass.
    for piece in report["pieces"]:
        for route in piece["platforms"]:
            text, title = expected.get(route.get("message_id"), ("", piece["title"] or ""))
            route["public_readback"] = http_check(route["platform"], route["public_url"], text, title)
            if route["public_readback"]:
                for issue in route["public_readback"]["exceptions"]:
                    exception(issue, piece["piece_id"], route["platform"], route, route["status"])
    report["digest"]["public_readback"] = http_check("substack", report["digest"]["public_url"],
        digest_copy.get("body_markdown", ""), digest_copy.get("title", ""))
    if report["digest"]["public_readback"]:
        for issue in report["digest"]["public_readback"]["exceptions"]:
            exception(issue, report["digest"]["digest_id"], "substack", report["digest"], report["digest"]["state"])
    report["exception_count"] = len(report["exceptions"])
    return report


def markdown(report):
    def local(value):
        return utc(value).astimezone(LOCAL).strftime("%d %b %Y %H:%M GMT+7")
    def plain(value):
        return " ".join(str(value).split()).replace("|", "/")
    lines = [f"Day readback: {local(report['window']['since_utc'])} to {local(report['window']['until_utc'])}.",
             f"Store observed: {local(report['observed_at_utc'])}; public HTTP observed at report time."]
    for piece in report["pieces"]:
        platforms = "; ".join(f"{r['platform']}={r['status']}" for r in piece["platforms"])
        lines.append(f"- {plain(piece['title'] or piece['piece_id'])}: {platforms or 'store rows missing'}.")
    digest = report["digest"]
    lines.append(f"Digest: {digest['state']}; recipients {digest['recipients'] if digest['recipients'] is not None else 'unknown'}; "
                 f"opens {digest['opens'] if digest['opens'] is not None else 'unknown'}; {digest['public_url'] or 'page unrecorded'}.")
    lines.append(f"Reply bot: {report['reply_bot']['delivered_count']} delivered drafts; "
                 + json.dumps(report["reply_bot"]["counts_by_kind_and_status"], sort_keys=True) + ".")
    lines.append(f"Exceptions: {report['exception_count']}.")
    for item in report["exceptions"]:
        lines.append(f"- {plain(item['piece_id'])} / {item['platform'] or 'all'}: {item['status'] or 'readback'}; "
                     f"{item['first_cause']}; {item['public_url'] or 'no public URL'}.")
    return "\n".join(lines) + "\n"


def write_report(run_dir, report):
    # A fixed projection, never a recursively redacted dump of private store data.
    def check(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if PRIVATE_KEY.search(key):
                    raise ValueError("PRIVATE_FIELD_IN_REPORT")
                check(item)
        elif isinstance(value, list):
            for item in value:
                check(item)
    check(report)
    folder = Path(run_dir)
    folder.mkdir(parents=True, exist_ok=True)
    paths = (folder / "day_readback.json", folder / "day_readback.md")
    paths[0].write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    paths[1].write_text(markdown(report), encoding="utf-8")
    return paths
