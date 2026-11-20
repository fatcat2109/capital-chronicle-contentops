"""CC-639: a read-only projection for the existing evening digest consumer.

No coordinator, browser, account session, model, store migration or retry is used.
Only the evening report files are written, by write_report().
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, timezone
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sqlite3
from subprocess import TimeoutExpired
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from live_contentops.channel_engagement_v1 import CHANNELS, engagement_readback_basis, piece_engagement
from live_contentops.agy_decision_metrics_v1 import daily_metrics
from live_contentops.daily_app_performance_v1 import current_metrics_capability_matrix
from live_contentops.public_decision_checks_v1 import DecisionChecks, public_link, wrap_kind
from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE, PublishedContentError, read_records

LOCAL = timezone(timedelta(hours=7))
DECISION_CHECKS_NAME = "decision_checks.json"
ROUTES = ("substack", "substack_notes", "telegram", "x", "discord", "linkedin",
          "linkedin_company", "facebook_page", "instagram_business", "threads", "youtube")
REPLY_PREFIX = "internal:x-reply-bot-"
PRIVATE_KEY = re.compile(r"chat|token|secret|webhook|phone|user_id|binding", re.I)
CODE = re.compile(r"[A-Z][A-Z0-9_]{1,159}\Z")
MAX_PAGE_BYTES = 2 * 1024 * 1024
PLAN_DELIVERY_TARGET_SECONDS = 300


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
    for key in ("first_cause", "first_blocking_cause", "reason_code", "cause", "error_code", "safe_error_classification"):
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


def _with_class_prefix(nodes, prefix):
    return (node for node in nodes if any(
        name.startswith(prefix) for name in (node.attrs.get("class") or "").split()))


def _first_text_line(text):
    return next((line.strip() for line in text.splitlines() if line.strip()), None)


def check_public_text(platform, html, *, expected_text="", expected_title="", page_url="", decision_copy=None):
    """Inspect the post body, never a menu, script, metadata or another post."""
    nodes = list(_HTML(html).root.walk())
    body = None
    attachments = ()
    if platform == "telegram":
        # Reply embeds show the quoted parent before the reply's own text.
        body = next((n for n in reversed(nodes)
                     if "tgme_widget_message_text" in (n.attrs.get("class") or "").split()), None)
    elif platform == "substack_notes":
        # Substack's public permalink scopes the root Note separately from replies.
        permalink = next(_with_class_prefix(nodes, "feedPermalinkUnit-"), None)
        if permalink is not None:
            body = next(_with_class_prefix(permalink.walk(), "feedCommentBody-"), None)
            attachments = tuple(_with_class_prefix(permalink.walk(), "postAttachment-"))
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
    first = expected_title or _first_text_line(expected_text)
    first_matches = (_contains_in_order(_tokens(first), _tokens(headings + " " + text)) if first else None)
    complete = _contains_in_order(_tokens(expected_text), _tokens(headings + " " + text)) if expected_text else None
    found_links = _links(text)
    for part in (body, *attachments):
        found_links.extend(n.attrs["href"] for n in part.walk() if n.tag == "a" and "href" in n.attrs)
    if decision_copy is not None:
        decision_copy.public_text = " ".join(filter(None, (headings, text)))
        decision_copy.public_links = tuple(urljoin(page_url, link) for link in found_links)
        if platform != "telegram":
            decision_copy.image_visible = any(
                node.tag in {"img", "picture"} for part in (body, *attachments) for node in part.walk())
        # A Telegram reply's scoped text and media are siblings. A photo
        # elsewhere on the page could belong to the quoted parent.
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


def report_window(run_dir, *, since=None, until=None, now=None, run_result=None):
    run_dir = Path(run_dir)
    result_path = run_dir / "result.json"
    result = run_result
    if result is None:
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


def _piece_heading(group, expected, end):
    # Prefer copy from dispatched routes in clock order, then other held public copy.
    sources = []
    for row in group:
        dispatched_at = utc(row["dispatched_at"]) if row["dispatched_at"] else None
        has_dispatch = dispatched_at is not None and dispatched_at <= end
        clock = dispatched_at if has_dispatch else utc(row["created_at"])
        sources.append((not has_dispatch, clock, row["message_id"]))
    sources.sort()
    first_line = next((line for _, _, message_id in sources
                       if (line := _first_text_line(expected[message_id][0]))), None)
    undispatched, first_clock, _ = sources[0]
    return first_line, None if undispatched else iso(first_clock)


def _public_rows(conn, window, feed):
    marks = ",".join("?" for _ in ROUTES)
    base = ("SELECT m.message_id,m.work_item_id,m.destination,m.status AS outbox_status,m.created_at,m.payload,"
            "d.dispatch_id,d.status,d.dispatched_at,d.public_object_id,d.public_object_url "
            "FROM outbox_messages m LEFT JOIN platform_dispatches d ON m.message_id=d.message_id ")
    span = (window["since_utc"], window["until_utc"])
    # Select clocks and owner IDs before loading frozen payloads. In particular,
    # a native reply is a single time-range scan, not a probe for every old post.
    work_ids = {row[0] for row in conn.execute(f"""
        SELECT work_item_id FROM outbox_messages
        WHERE destination IN ({marks}, 'internal:native-neo-tool')
          AND julianday(created_at) > julianday(?) AND julianday(created_at) <= julianday(?)
        UNION
        SELECT o.work_item_id FROM platform_dispatches d
        JOIN outbox_messages o ON o.message_id=d.message_id
        WHERE julianday(d.dispatched_at) > julianday(?) AND julianday(d.dispatched_at) <= julianday(?)
        UNION
        SELECT o.work_item_id FROM readbacks r JOIN platform_dispatches d ON d.dispatch_id=r.dispatch_id
        JOIN outbox_messages o ON o.message_id=d.message_id
        WHERE julianday(r.read_at) > julianday(?) AND julianday(r.read_at) <= julianday(?)
        UNION
        SELECT work_item_id FROM reconciliations
        WHERE julianday(reconciled_at) > julianday(?) AND julianday(reconciled_at) <= julianday(?)
        """, (*ROUTES, *span, *span, *span, *span))}
    urls = [o["url"] for f in feed for o in f["outlets"] if o["name"] == "substack"]
    for url in urls:
        work_ids.update(row[0] for row in conn.execute("""
            SELECT o.work_item_id FROM platform_dispatches d JOIN outbox_messages o ON o.message_id=d.message_id
            WHERE d.public_object_url=? AND o.destination='substack'""", (url,)))
    # A continuation can arrive in a later window than its root.
    work_ids.update(work.rsplit("-part-", 1)[0] for work in tuple(work_ids)
                    if work.startswith("plan-") and re.search(r"-part-\d+$", work))
    by_id = {}
    end = utc(window["until_utc"])
    for work_id in sorted(work_ids):
        for row in conn.execute(base + f"WHERE m.work_item_id=? AND m.destination IN ({marks})", (work_id, *ROUTES)):
            # Don't turn an outbox created after a historical report's end into that day's post.
            if utc(row["created_at"]) <= end:
                by_id[(row["message_id"], row["dispatch_id"])] = dict(row)
    return list(by_id.values())


def _readback_histories(conn, dispatch_ids, end):
    ids = list(dict.fromkeys(dispatch_id for dispatch_id in dispatch_ids if dispatch_id))
    histories = defaultdict(list)
    if ids:
        # The store's readbacks index is keyed by readback ID. Select the whole
        # report cohort in one scan instead of scanning once for every copy.
        for row in conn.execute("""SELECT dispatch_id,read_at,readback_data FROM readbacks
            WHERE dispatch_id IN (SELECT value FROM json_each(?))
            AND julianday(read_at) <= julianday(?) ORDER BY read_at,readback_id""",
            (json.dumps(ids), iso(end))):
            if utc(row["read_at"]) <= end:
                histories[row["dispatch_id"]].append((row["read_at"], json.loads(row["readback_data"])))
    return histories


def _decision_source(conn, work_id, end, expected=""):
    parent_id = work_id.rsplit("-part-", 1)[0] if re.search(r"-part-\d+$", work_id) else work_id
    if parent_id.startswith(("plan-status-post-", "plan-result-post-", "plan-update-post-")):
        row = conn.execute("""SELECT payload,created_at FROM outbox_messages WHERE message_id=?
            AND destination='internal:plan-status-post' AND julianday(created_at) <= julianday(?)""",
            (parent_id, end)).fetchone()
        return {**json.loads(row["payload"]), "decision_source_created_at_utc": row["created_at"]} if row else {}
    if not work_id.startswith("plan-analysis-"):
        return {}
    rows = conn.execute("""SELECT payload FROM outbox_messages
        WHERE work_item_id=? AND destination IN
            ('internal:plan-analysis-page','internal:plan-analysis-revision')
        AND julianday(created_at) <= julianday(?) ORDER BY created_at DESC,message_id""", (work_id, end))
    for row in rows:
        source = json.loads(row["payload"])
        if source.get("page_id") == work_id and (not expected or _expected(source) == expected):
            return source
    return {}


def _confirmed_analysis_urls(conn, copies, end):
    urls = {}
    ids = {copy.source.get("plan_id") for copy in copies}
    for plan_id in sorted(p for p in ids if isinstance(p, str) and re.fullmatch(r"plan_[a-zA-Z0-9_-]+", p)):
        for row in conn.execute("""SELECT d.public_object_url FROM outbox_messages o
            JOIN platform_dispatches d ON d.message_id=o.message_id
            WHERE o.work_item_id=? AND o.destination='substack' AND d.status='DISPATCH_CONFIRMED'
            AND julianday(d.dispatched_at) <= julianday(?) ORDER BY d.dispatched_at,d.dispatch_id""",
            ("plan-analysis-" + plan_id, end)):
            url = safe_url(row["public_object_url"])
            if public_link(url):
                urls[plan_id] = url
    return urls


def _read_plan_export(plan_export_dir):
    from live_contentops import plan_status_posts_v1 as posts

    try:
        return posts.read_export(plan_export_dir or posts.EXPORT_DIR), None
    except posts.PlanExportContractError as exc:
        return None, exc.cause
    except posts.PlanPostError as exc:
        return None, code(str(exc).replace(":", "_")) or "MAIN_PLAN_EXPORT_UNREADABLE"
    except (OSError, ValueError, KeyError, TimeoutExpired) as exc:
        return None, "MAIN_PLAN_EXPORT_" + type(exc).__name__.upper()


def _confirmed_plan_announcements(conn, export, end):
    if not export:
        return set()
    plans = [plan["plan_id"] for plan in export["status"]["plans"]]
    routes = ",".join("?" for _ in ROUTES)
    return {row[0] for row in conn.execute(f"""SELECT DISTINCT json_extract(plan.payload,'$.plan_id')
        FROM outbox_messages plan JOIN outbox_messages post ON post.work_item_id=plan.message_id
        JOIN platform_dispatches d ON d.message_id=post.message_id
        WHERE plan.destination='internal:plan-status-post' AND json_extract(plan.payload,'$.kind')='setup'
        AND json_extract(plan.payload,'$.plan_id') IN (SELECT value FROM json_each(?))
        AND post.destination IN ({routes}) AND d.status='DISPATCH_CONFIRMED'
        AND d.public_object_id IS NOT NULL AND d.public_object_url IS NOT NULL
        AND julianday(d.dispatched_at) <= julianday(?)""", (json.dumps(plans), *ROUTES, end))}


def _earlier_wrap_copies(conn, checks, known_ids):
    """Include a wrap sent before the evening window opens on the same due day."""
    since = iso(checks.start - timedelta(days=2))
    end = checks.window["until_utc"]
    marks = ",".join("?" for _ in ROUTES)
    for work in conn.execute("""SELECT work_item_id,title FROM work_items
        WHERE julianday(created_at) > julianday(?) AND julianday(created_at) <= julianday(?)
        AND (lower(title) LIKE '%wrap%' OR lower(title) LIKE '%recap%' OR lower(title) LIKE '%weekend%')
        ORDER BY work_item_id""", (since, end)):
        if work["work_item_id"] in known_ids or not wrap_kind(work["title"] or "", None):
            continue
        rows = [dict(row) for row in conn.execute(f"""SELECT o.*, d.dispatch_id,d.status AS dispatch_status,
            d.dispatched_at,d.public_object_id,d.public_object_url FROM outbox_messages o
            LEFT JOIN platform_dispatches d ON d.message_id=o.message_id
            WHERE o.work_item_id=? AND o.destination IN ({marks}) AND julianday(o.created_at) <= julianday(?)""",
            (work["work_item_id"], *ROUTES, end))]
        histories = _readback_histories(conn, (row["dispatch_id"] for row in rows), checks.end)
        for row in rows:
            intent = json.loads(row["payload"])
            row["status"] = row["dispatch_status"]
            checks.add(work["work_item_id"], row["destination"], safe_url(row["public_object_url"]), work["title"],
                       _expected(intent), intent, row, histories[row["dispatch_id"]], {})


def _route_engagement(conn, row, route, history, *, as_of, source_exists, collector_states):
    entry = {"platform": route["platform"], "public_url": route["public_url"],
             "metrics": {}, "missing_metrics": {}, "first_cause": None}
    if route["status"] != "DISPATCH_CONFIRMED":
        entry["first_cause"] = route["first_cause"] or code(route["status"]) or "NO_CONFIRMED_PUBLIC_OBJECT"
        return entry
    dispatch_id = row["dispatch_id"]
    if not dispatch_id:
        entry["first_cause"] = "NO_CONFIRMED_PUBLIC_OBJECT"
        return entry
    dispatch = {**row, "platform": route["platform"]}
    reconciliation = conn.execute("""SELECT status FROM reconciliations WHERE reconciliation_id=?
        AND julianday(reconciled_at) <= julianday(?)""",
        ("reconciliation_" + dispatch_id.removeprefix("dispatch_"), iso(as_of))).fetchone()
    readbacks = [{"dispatch_id": dispatch_id, "readback_data": data} for clock, data in history if utc(clock) <= as_of]
    basis = engagement_readback_basis(dispatch, reconciliation["status"] if reconciliation else None, readbacks)
    if not basis:
        entry["first_cause"] = "NO_EXACT_CONFIRMED_READBACK_BY_CUTOFF"
    elif not source_exists:
        entry["first_cause"] = "ENGAGEMENT_EXPORT_SOURCE_UNAVAILABLE"
    else:
        rows = conn.execute("""SELECT dispatch_id, platform, public_object_id, collected_at_utc, scheduled_for_utc,
            collection_status, learning_eligible, metrics_native_json, metric_availability_json
            FROM performance_observations WHERE dispatch_id=? ORDER BY observation_id""", (dispatch_id,))
        values, missing, cause = piece_engagement(dispatch, basis, (dict(r) for r in rows), as_of=as_of)
        entry["metrics"] = values
        entry["missing_metrics"] = {metric: code(reason) or "METRIC_UNAVAILABLE" for metric, reason in missing.items()}
        entry["first_cause"] = cause
        if cause == "NO_COLLECTED_OBSERVATION_BY_CUTOFF" and route["platform"] in collector_states:
            entry["collector_state"] = collector_states[route["platform"]]
    return entry


def _complete_engagement(piece):
    actual = {row["platform"] for row in piece["engagement"]}
    for route in piece["platforms"]:
        if route["platform"] not in actual:
            piece["engagement"].append({"platform": route["platform"], "public_url": route["public_url"],
                "metrics": {}, "missing_metrics": {}, "first_cause": route["first_cause"]})
            actual.add(route["platform"])
    for platform in CHANNELS:
        if platform not in actual:
            piece["engagement"].append({"platform": platform, "public_url": None, "metrics": {},
                "missing_metrics": {}, "first_cause": "NO_PUBLICATION_ROUTE_RECORDED"})


def _native_observations(conn, work_id, until):
    """Reuse stored request/return diagnostics when a dispatch has no readback yet."""
    requests, returns = {}, []
    for row in conn.execute("""SELECT created_at,
        json_extract(payload,'$.request.request_sha256') AS request_hash,
        json_extract(payload,'$.request.destination') AS platform,
        json_extract(payload,'$.result.request_sha256') AS response_hash,
        json_extract(payload,'$.result.status') AS status,
        json_extract(payload,'$.result.reason_code') AS reason_code,
        json_extract(payload,'$.result.first_cause') AS first_cause,
        json_extract(payload,'$.result.safe_error_classification') AS safe_error_classification
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
                "reason_code": code(row["reason_code"]), "first_cause": code(row["first_cause"]),
                "safe_error_classification": code(row["safe_error_classification"])}))
    return by_platform


def _dispatch_outcomes(conn, work_id, dispatch_id, until):
    if not dispatch_id:
        return []
    outcomes = []
    for row in conn.execute("""SELECT severity, description, created_at FROM incidents
        WHERE work_item_id=? AND severity IN ('DISPATCH_OUTCOME','RESOLVED_LOCAL_PREWRITE')
        AND julianday(created_at) <= julianday(?) ORDER BY created_at,incident_id""", (work_id, until)):
        value = json.loads(row["description"])
        if value.get("dispatch_id") != dispatch_id:
            continue
        if (row["severity"] == "RESOLVED_LOCAL_PREWRITE"
                and value.get("cause") == "CC467_UNREGISTERED_SURFACE_AFTER_BEGIN_CLAIM"):
            for _, outcome in outcomes:
                if outcome.get("safe_error_classification") == "KeyError":
                    outcome["first_cause"] = value["cause"]
                    break
        else:
            outcomes.append((value.get("attempt_started_at_utc") or row["created_at"], value))
    return outcomes


def _unsent_quote_cause(conn, work_id, quote, until, store_path):
    """Project the retained exact quote run, including coordinator refusals before a dispatch exists."""
    root = (Path(store_path).resolve().parent / "daily_app_outputs/heavy_news_quotes").resolve()
    for row in conn.execute("""SELECT json_extract(payload,'$.artifact_dir') AS folder FROM outbox_messages
        WHERE destination='internal:heavy-news-quote-editorial' AND json_extract(payload,'$.post.target_id')=?
        AND julianday(created_at) <= julianday(?) ORDER BY created_at,message_id""", (quote.get("public_object_id"), until)):
        folder = Path(row["folder"] or "").resolve()
        if folder.parent != root or not re.fullmatch(r"editorial-[0-9a-f]{16}", folder.name):
            continue
        path = folder / "result.json"
        try:
            if path.stat().st_size > 256_000:
                continue
            value = json.loads(path.read_bytes())
        except (OSError, ValueError):
            continue
        result = value.get("result") or {}
        if value.get("status") != "QUOTE_PUBLICATION" or (result.get("reply") or {}).get("key") != work_id:
            continue
        publication = result.get("publication") or {}
        for projection in (publication, publication.get("recovery_preflight") or {}):
            if cause := first_cause((projection.get("per_destination") or {}).get("x")):
                return cause
    if quote.get("deadline_at_utc") and utc(quote["deadline_at_utc"]) <= utc(until):
        return "CC467_SOURCE_OUTSIDE_FIVE_MINUTES"
    return None


def _digest(conn, run_dir, result):
    digest_id = result.get("digest_id")
    packet = {}
    if digest_id:
        row = conn.execute("SELECT message_id,payload FROM outbox_messages WHERE destination=? AND work_item_id=?",
                           ("internal:substack-daily-digest", digest_id)).fetchone()
        if row:
            packet = json.loads(row["payload"])
    state = code(result.get("route_state")) or code(result.get("final_route_state"))
    summary = {"digest_id": digest_id, "state": state or "RUN_RESULT_UNAVAILABLE",
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
        FROM outbox_messages WHERE destination >= ? AND destination < ?
        AND julianday(created_at) > julianday(?) AND julianday(created_at) <= julianday(?)
        ORDER BY created_at,message_id"""
    # The destination index bounds this literal prefix without scanning other owners' payloads.
    prefix_end = REPLY_PREFIX.removesuffix("-") + "."
    for row in conn.execute(query, (REPLY_PREFIX, prefix_end, window["since_utc"], window["until_utc"])):
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


def _plan_copy_queue(conn, now, store_path):
    from live_contentops import plan_call_cards_v1 as cards, plan_status_posts_v1 as posts
    from live_contentops.native_neo_executor_v1 import PENDING as NATIVE_NEO_PENDING

    root = Path(store_path).parent / "daily_app_outputs" / "plan-status-posts"
    pending, overdue = 0, []
    for plan in conn.execute("""SELECT message_id,payload,created_at FROM outbox_messages
        WHERE destination=? AND status IN (?, 'PUBLISHING')""", (posts.DESTINATION, posts.READY)):
        row = json.loads(plan["payload"])
        if row.get("format") != cards.FORMAT:
            continue
        settled = cards.read_settled_destinations(conn, row)
        unavailable = {d["destination"] for d in cards._skipped_images(root, row)}
        copies = {r["destination"]: r for r in conn.execute("""SELECT o.destination,o.created_at,
            COALESCE(d.status,o.status) AS status FROM outbox_messages o
            LEFT JOIN platform_dispatches d ON o.message_id=d.message_id
            WHERE o.work_item_id=?""", (plan["message_id"],))}
        for destination in cards.destinations_for(row):
            if destination in settled or destination in unavailable:
                continue
            copy = copies.get(destination)
            status = copy["status"] if copy else "WAITING"
            if not (status in {"READY", NATIVE_NEO_PENDING} or status.startswith("WAITING")):
                continue
            queued_at = utc(copy["created_at"] if copy else plan["created_at"])
            age = (now - queued_at).total_seconds()
            pending += 1
            if age > PLAN_DELIVERY_TARGET_SECONDS:
                overdue.append({"plan_post": plan["message_id"], "platform": destination,
                    "status": status, "queued_at_utc": iso(queued_at), "age_seconds": round(age, 1)})
    return {"observed_at_utc": iso(now), "ready_or_waiting": pending,
            "over_five_minutes": sorted(overdue, key=lambda r: (-r["age_seconds"], r["platform"]))}


def _plan_minute_causes(root, needed, start, end):
    """Read the existing minute records for copies with no durable cause."""
    causes = {}
    day = start.date()
    while needed and day <= end.date():
        path = root / day.strftime("runs-%Y%m%d.jsonl")
        if path.is_file():
            with path.open(encoding="utf-8") as log:
                for line in log:
                    try:
                        tick = json.loads(line)
                        if not start <= utc(tick["at_utc"]) <= end:
                            continue
                    except (ValueError, KeyError, TypeError):
                        continue
                    for post in tick.get("posts") or []:
                        key = post.get("key")
                        destinations = needed.get(key)
                        if not destinations:
                            continue
                        local = {d["destination"]: d.get("cause") for d in post.get("deferred_destinations", [])}
                        local.update(post.get("destination_causes") or {})
                        for destination in destinations:
                            cause = _plan_cause(local.get(destination)) or _plan_cause(post.get("cause"))
                            if cause:
                                causes.setdefault((key, destination), cause)
        day += timedelta(days=1)
    return causes


def _plan_cause(value):
    if not isinstance(value, str):
        return None
    for reason in value.split(";"):
        if all(code(part) for part in reason.split(":")):
            return reason
    return None


def _plan_copy_clocks(history):
    verified_at = None
    for read_at, value in history:
        proof = value.get("readback", value)
        if proof.get("verified") is not True:
            continue
        verified_at = verified_at or utc(read_at)
        if published_at := proof.get("observed_published_at_utc"):
            return utc(published_at), verified_at
    return None, verified_at


def _plan_delivery(conn, window, store_path):
    """Account for every named copy, even when its public intent was never registered."""
    from live_contentops import plan_call_cards_v1 as cards, plan_status_posts_v1 as posts
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator

    start, end = utc(window["since_utc"]), utc(window["until_utc"])
    runtime = Path(store_path).parent
    root = runtime / "daily_app_outputs" / "plan-status-posts"
    selected = []
    for plan in conn.execute("""SELECT p.message_id,p.payload,p.status,p.created_at FROM outbox_messages p
        WHERE p.destination=? AND julianday(p.created_at) <= julianday(?)
        AND (julianday(p.created_at) > julianday(?) OR p.status IN (?, 'PUBLISHING')
             OR p.message_id IN (
                SELECT o.work_item_id FROM outbox_messages o
                LEFT JOIN platform_dispatches d ON d.message_id=o.message_id
                WHERE julianday(o.created_at) <= julianday(?)
                  AND (julianday(o.created_at) > julianday(?)
                       OR julianday(d.dispatched_at) > julianday(?)
                       OR d.status IN ('UNKNOWN_WRITE', 'DISPATCH_ATTEMPT_STARTED'))))
        ORDER BY p.created_at,p.message_id""",
        (posts.DESTINATION, iso(end), iso(start), posts.READY, iso(end), iso(start), iso(start))):
        row = json.loads(plan["payload"])
        if row.get("kind") not in {"setup", "update", "result"}:
            continue
        key = plan["message_id"]
        named = cards.destinations_for(row) if row.get("format") == cards.FORMAT else posts.POST_DESTINATIONS
        routes = {}
        plan_hash = sha256(("plan-status-post:" + key).encode()).hexdigest()
        for route in conn.execute("""SELECT o.destination,o.status AS outbox_status,o.created_at,
            o.message_id,d.status,d.dispatch_id,d.dispatched_at,d.public_object_id,d.public_object_url
            FROM outbox_messages o LEFT JOIN platform_dispatches d ON o.message_id=d.message_id
            WHERE o.work_item_id=? AND julianday(o.created_at) <= julianday(?)
            ORDER BY o.created_at,o.message_id""", (key, iso(end))):
            destination = route["destination"]
            if destination in ROUTES and route["message_id"] == DurablePublicationCoordinator._ids(
                    key, plan_hash, destination)["message_id"]:
                routes[destination] = route
        selected.append((plan, row, tuple(dict.fromkeys((*named, *routes))), routes))

    histories = _readback_histories(conn, (route["dispatch_id"] for _, _, _, routes in selected
                                           for route in routes.values()), end)
    plan_rows, copies, need_cause = [], [], defaultdict(set)
    for plan, row, named, routes in selected:
        key = plan["message_id"]
        settled = cards.read_settled_destinations(conn, row)
        skipped = {d["destination"]: d["cause"] for d in cards._skipped_images(root, row)}
        native = _native_observations(conn, key, iso(end))
        try:
            source_at = utc(row["at_utc"])
        except (KeyError, ValueError):
            source_at = None
        observed, clocks, in_window = [], [], []
        for destination in named:
            route = routes.get(destination)
            dispatch_at = utc(route["dispatched_at"]) if route and route["dispatched_at"] else None
            status = "WAITING"
            if route:
                status = (route["status"] or route["outbox_status"]) if not dispatch_at or dispatch_at <= end else "READY"
            confirmed = bool(dispatch_at and status == "DISPATCH_CONFIRMED" and route["public_object_id"])
            retry, cause = False, None
            published_at, verified_at = None, None
            closed_at = None
            if route and route["dispatch_id"]:
                dispatch_id = route["dispatch_id"]
                retry_id = DurablePublicationCoordinator._retry_incident_id(dispatch_id)
                retry = conn.execute("""SELECT 1 FROM incidents
                    WHERE incident_id=? AND julianday(created_at) <= julianday(?)""",
                    (retry_id, iso(end))).fetchone() is not None
                history = histories.get(dispatch_id, [])
                diagnostics = _dispatch_outcomes(conn, key, dispatch_id, iso(end)) + native.get(destination, []) + history
                cause = next((c for _, value in sorted(diagnostics, key=lambda item: utc(item[0]))
                              if (c := first_cause(value) or _plan_cause(value.get("safe_error_classification")))), None)
                if confirmed:
                    published_at, verified_at = _plan_copy_clocks(history)
            if not confirmed:
                closure = settled.get(destination) or {}
                if closure and (not closure.get("recorded_at_utc") or utc(closure["recorded_at_utc"]) <= end):
                    closed_at = utc(closure["recorded_at_utc"]) if closure.get("recorded_at_utc") else None
                    status = status if status in {"UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED"} else cards.SETTLED_POST
                    cause = cause or _plan_cause(closure.get("cause"))
                if destination in skipped:
                    status, cause = cards.SETTLED_POST, cause or _plan_cause(skipped[destination])
                if not cause:
                    need_cause[key].add(destination)
            ready_at = utc(route["created_at"] if route else plan["created_at"])
            pending = (not confirmed and status not in {cards.SETTLED_POST, posts.STALE, posts.SUPERSEDED}
                       and (plan["status"] in {posts.READY, "PUBLISHING"} or status in {
                           "UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED"}
                           or bool(dispatch_at and dispatch_at > end)))
            in_window.append(pending or any(at and start < at <= end for at in
                (ready_at, dispatch_at, published_at, verified_at, closed_at)))
            observed.append({"plan_post": key, "platform": destination, "status": status,
                "confirmed": confirmed, "retry_recorded": retry, "first_cause": cause,
                 "source_at_utc": iso(source_at) if source_at else None,
                "confirmed_dispatch_at_utc": iso(dispatch_at) if confirmed else None,
                "observed_published_at_utc": iso(published_at) if published_at else None,
                "first_verified_readback_at_utc": iso(verified_at) if verified_at else None,
                 "source_to_published_seconds": (published_at - source_at).total_seconds()
                     if source_at and published_at else None,
                 "source_to_first_verified_seconds": (verified_at - source_at).total_seconds()
                     if source_at and verified_at else None,
                "public_url": safe_url(route["public_object_url"]) if confirmed else None,
                "x_ready_over_five_minutes": destination == "x" and status == "READY"
                     and (end - ready_at).total_seconds() > PLAN_DELIVERY_TARGET_SECONDS})
            clocks.append(published_at or verified_at or (dispatch_at if confirmed else None))
        first = min((clock for clock in clocks if clock is not None), default=None)
        for copy, clock in zip(observed, clocks, strict=True):
            finish = clock or end
            lag = round((finish - first).total_seconds(), 1) if first else None
            copy["seconds_after_first_confirmed"] = lag
            copy["behind_over_ten_minutes"] = lag is not None and lag > 600
        if any(in_window):
            copies.extend(copy for copy, include in zip(observed, in_window, strict=True) if include)
            plan_rows.append((key, plan["status"], all(r["confirmed"] for r in observed)))

    fallback = _plan_minute_causes(runtime / posts.RUN_RECORD_FOLDER, need_cause, start, end)
    states = {key: state for key, state, _ in plan_rows}
    for copy in copies:
        if copy["confirmed"] or copy["first_cause"]:
            continue
        key = copy["plan_post"]
        cause = fallback.get((key, copy["platform"]))
        if states[key] in {posts.STALE, posts.SUPERSEDED} and copy["status"] in {"READY", "WAITING"}:
            copy["status"] = states[key]
            cause = cause or "PLAN_POST_" + states[key]
        copy["first_cause"] = cause or {
            "READY": "DESTINATION_INTENT_READY_WITHOUT_DISPATCH",
            "WAITING": "DESTINATION_INTENT_NOT_REGISTERED",
        }.get(copy["status"], "FIRST_CAUSE_NOT_RECORDED")

    total = len(plan_rows)
    complete = sum(confirmed for _, _, confirmed in plan_rows)
    return {"plan_posts": total, "all_destinations_confirmed": complete,
            "all_destinations_confirmed_pct": round(100 * complete / total, 2) if total else None,
            "copies": copies}


def build_report(run_dir, *, store_path=PRODUCTION_STORE, feed_path=DEFAULT_FEED,
                 since=None, until=None, now=None, fetcher=fetch_public, run_result=None, plan_export_dir=None):
    now = now or datetime.now(timezone.utc)
    window, result = report_window(run_dir, since=since, until=until, now=now, run_result=run_result)
    report = {"schema_version": "contentops.day_readback.v1", "observed_at_utc": iso(now),
              "window": window, "pieces": [], "exceptions": [],
              "store_open_mode": "ro", "public_writes": 0, "browser_opens": 0, "model_calls": 0}
    start, end = utc(window["since_utc"]), utc(window["until_utc"])
    engagement_cutoff = min(now, end)
    report["engagement"] = {"source": "performance_observations", "cutoff_utc": iso(engagement_cutoff)}
    collector_states = {row["destination"]: row["collector_state"] for row in current_metrics_capability_matrix()}
    cache, expected = {}, {}
    decision_copies = {}
    checks = DecisionChecks(window, Path(store_path).parent)
    plan_export, plan_source_error = None, None
    live_plan_audit = until is None and Path(store_path).resolve() == PRODUCTION_STORE.resolve()
    plan_cutoff = end
    if plan_export_dir is not None or live_plan_audit:
        plan_export, plan_source_error = _read_plan_export(plan_export_dir)
        if plan_export and live_plan_audit:
            captured = utc(plan_export["status"]["generated_at_utc"])
            # Step 8 runs after the digest result is written. Keep that result's
            # report window and use Main's newer observation for live plans.
            if end < captured <= now:
                plan_cutoff = captured

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

    def http_check(platform, url, text="", title="", decision_copy=None):
        target = public_get_url(platform, url)
        if not target or fetcher is None:
            return None
        if target not in cache:
            cache[target] = {**fetcher(platform, target), "checked_at_utc": iso(datetime.now(timezone.utc))}
        response = cache[target]
        status = response.get("http_status")
        cause = code(response.get("first_cause"))
        checked = {"checked_at_utc": response["checked_at_utc"], "http_status": status}
        if decision_copy is not None:
            decision_copy.public_http_status = status
        if cause or status != 200:
            return {**checked, "first_cause": cause or "HTTP_" + str(status),
                    "first_line_matches": None, "text_complete": None, "links_match": None,
                    "exceptions": [cause or "PUBLIC_HTTP_UNAVAILABLE"]}
        return {**checked, **check_public_text(platform, response.get("html", ""),
                                               expected_text=text, expected_title=title, page_url=target,
                                               decision_copy=decision_copy)}

    with closing(sqlite3.connect(Path(store_path).resolve().as_uri() + "?mode=ro", uri=True, timeout=5)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        engagement_source_exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='performance_observations'").fetchone() is not None
        rows = _public_rows(conn, window, feed)
        histories = _readback_histories(conn, (row["dispatch_id"] for row in rows), end)
        groups = defaultdict(list)
        for row in rows:
            groups[row["work_item_id"]].append(row)
        feed_by_url = {o["url"]: f for f in feed for o in f["outlets"] if o["name"] == "substack"}
        consumed = set()
        quote_causes = {}
        for work_id, group in sorted(groups.items()):
            sealed = next((feed_by_url[r["public_object_url"]] for r in group
                           if r["destination"] == "substack" and r["public_object_url"] in feed_by_url), None)
            if sealed:
                consumed.add(sealed["content_id"])
            piece_id = sealed["content_id"] if sealed else work_id
            piece = {"piece_id": piece_id, "title": sealed["title"] if sealed else None,
                     "published_at_utc": sealed["published_at_utc"] if sealed else None, "platforms": [], "engagement": []}
            required = {o["name"] for o in sealed["outlets"]} if sealed else set()
            actual = set()
            native = _native_observations(conn, work_id, window["until_utc"])
            registered = conn.execute("SELECT title FROM work_items WHERE work_item_id=? "
                                      "AND julianday(created_at) <= julianday(?)",
                                      (work_id, window["until_utc"])).fetchone()
            work_title = sealed["title"] if sealed else (registered["title"] if registered else "")
            source = _decision_source(conn, work_id, window["until_utc"])
            for row in group:
                platform = row["destination"]
                actual.add(platform)
                intent = json.loads(row["payload"])
                if platform == "substack" and not piece["title"]:
                    native_payload = intent.get("native_payload")
                    title = native_payload.get("title") if isinstance(native_payload, dict) else None
                    if isinstance(title, str):
                        piece["title"] = _first_text_line(title)
                required.update(d for key in ("required_publication_destinations", "required_derivative_destinations")
                                for d in intent.get(key, []) if d in ROUTES)
                history = histories.get(row["dispatch_id"], [])
                text = _expected(intent)
                native_title = (intent.get("native_payload") or {}).get("title")
                if platform == "substack" and intent.get("plan_analysis_page"):
                    source = _decision_source(conn, work_id, window["until_utc"], expected=text) or source
                decision_copies[(row["message_id"], row["dispatch_id"])] = checks.add(
                    piece_id, platform, safe_url(row["public_object_url"]), native_title or work_title or "",
                    text, intent, row, history, source)
                if work_id == result.get("digest_id"):
                    continue  # This run's digest has its own packet/page/delivery section.
                quote = intent.get("quote_parent") if platform == "x" and work_id.startswith("heavy-quote-") else None
                diagnostics = history + native.get(platform, [])
                if quote:
                    diagnostics += _dispatch_outcomes(conn, work_id, row["dispatch_id"], window["until_utc"])
                diagnostics.sort(key=lambda item: utc(item[0]))
                cause = next((c for _, value in diagnostics if (c := first_cause(value))), None)
                status = row["status"] or row["outbox_status"]
                if quote:
                    if cause == "NEO_COMPOSER_PREPARATION_FAILED":
                        cause = next((value["safe_error_classification"] for _, value in diagnostics
                                      if value.get("reason_code") == cause and code(value.get("safe_error_classification"))), cause)
                    if not cause and status == "READY":
                        cause = _unsent_quote_cause(conn, work_id, quote, window["until_utc"], store_path)
                    if cause:
                        quote_causes[work_id] = cause
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
                elif quote and status == "READY" and cause:
                    exception(cause, piece_id, platform, row, status)
                prior_failures = set()
                for clock, value in diagnostics:
                    if start < utc(clock) and _failure(value.get("status")) and value.get("status") != status:
                        failure = (value["status"], first_cause(value) or "FIRST_CAUSE_NOT_RECORDED")
                        if failure not in prior_failures:
                            exception(failure[1], piece_id, platform, row, failure[0])
                            prior_failures.add(failure)
                expected[row["message_id"]] = (text, sealed["title"] if sealed and platform == "substack" else "")
                route["public_readback"] = None
                piece["platforms"].append(route)
                piece["engagement"].append(_route_engagement(conn, row, route, history, as_of=engagement_cutoff,
                    source_exists=engagement_source_exists, collector_states=collector_states))
            if work_id == result.get("digest_id"):
                continue
            piece["first_line"], piece["first_dispatch_at_utc"] = _piece_heading(group, expected, end)
            if not piece["title"] and ("substack" in actual or not piece["first_line"]):
                if registered:
                    piece["title"] = _first_text_line(registered["title"])
            for platform in sorted(required - actual):
                piece["platforms"].append({"platform": platform, "status": "MISSING_ROW", "first_cause": "EXPECTED_PLATFORM_ROW_MISSING",
                                           "public_url": None, "store_readback": None, "public_readback": None})
                exception("EXPECTED_PLATFORM_ROW_MISSING", piece_id, platform, status="MISSING_ROW")
            _complete_engagement(piece)
            report["pieces"].append(piece)
        for sealed in feed:
            if sealed["content_id"] not in consumed:
                piece = {"piece_id": sealed["content_id"], "title": sealed["title"],
                         "published_at_utc": sealed["published_at_utc"], "first_line": None,
                         "first_dispatch_at_utc": None, "platforms": [], "engagement": []}
                for outlet in sealed["outlets"]:
                    route = {"platform": outlet["name"], "status": "MISSING_ROW", "first_cause": "SEALED_OUTLET_STORE_ROW_MISSING",
                             "public_url": safe_url(outlet["url"]), "store_readback": None, "public_readback": None}
                    piece["platforms"].append(route)
                    exception("SEALED_OUTLET_STORE_ROW_MISSING", sealed["content_id"], outlet["name"], route, status="MISSING_ROW")
                _complete_engagement(piece)
                report["pieces"].append(piece)
        report["digest"], digest_copy = _digest(conn, run_dir, result)
        report["reply_bot"] = _reply_bot(conn, window)
        report["plan_copy_queue"] = _plan_copy_queue(conn, now, store_path)
        report["plan_delivery"] = _plan_delivery(conn, window, store_path)
        _earlier_wrap_copies(conn, checks, groups)
        analysis_urls = _confirmed_analysis_urls(conn, checks.copies, window["until_utc"])
        announced = _confirmed_plan_announcements(conn, plan_export, iso(plan_cutoff))
        seen = {(e["message_id"], e["status"]) for e in report["exceptions"]}
        # A contradictory outbox status, or an uncertain private reply delivery,
        # is still an exception even when it has no public dispatch row.
        # Restrict candidate identities before accessing payloads in the main table.
        for row in conn.execute("""SELECT message_id,work_item_id,destination,status,
            json_extract(payload,'$.reason_code') AS reason_code,
            json_extract(payload,'$.cause') AS cause
            FROM outbox_messages WHERE (status IN ('UNKNOWN_WRITE','DEFINITE_NO_WRITE')
            OR status LIKE 'RECONCILED_ABSENT%') AND message_id IN (
                SELECT message_id FROM outbox_messages WHERE julianday(created_at) > julianday(?)
                AND julianday(created_at) <= julianday(?)) ORDER BY created_at,message_id""",
            (window["since_utc"], window["until_utc"])):
            if (row["message_id"], row["status"]) not in seen:
                exception(first_cause(dict(row)) or quote_causes.get(row["work_item_id"]) or "FIRST_CAUSE_NOT_RECORDED", row["work_item_id"],
                          row["destination"] if row["destination"] in ROUTES else "internal", dict(row), row["status"])
    # Release the SQLite snapshot before doing any HTTP. A slow page cannot keep
    # the production reader transaction open throughout the network pass.
    for piece in report["pieces"]:
        for route in piece["platforms"]:
            text, title = expected.get(route.get("message_id"), ("", piece["title"] or ""))
            copy = decision_copies.get((route.get("message_id"), route.get("dispatch_id")))
            route["public_readback"] = http_check(route["platform"], route["public_url"], text, title, copy)
            if route["public_readback"]:
                for issue in route["public_readback"]["exceptions"]:
                    exception(issue, piece["piece_id"], route["platform"], route, route["status"])
    digest_observation = next((copy for copy in decision_copies.values()
        if copy.platform == "substack" and copy.url == report["digest"]["public_url"]), None)
    report["digest"]["public_readback"] = http_check("substack", report["digest"]["public_url"],
        digest_copy.get("body_markdown", ""), digest_copy.get("title", ""), digest_observation)
    if report["digest"]["public_readback"]:
        for issue in report["digest"]["public_readback"]["exceptions"]:
            exception(issue, report["digest"]["digest_id"], "substack", report["digest"], report["digest"]["state"])
    report["decision_checks"] = checks.finish(report["plan_delivery"], analysis_urls,
        plan_export=plan_export, announced=announced, plan_source_error=plan_source_error,
        plan_cutoff=plan_cutoff)
    report["decision_checks"]["antigravity"] = daily_metrics(
        Path(store_path).parent, window, checks.estimated_jobs(report["plan_delivery"]),
        {Path(copy.intent["output_dir"]).resolve() for copy in checks.copies if copy.intent.get("output_dir")})
    report["exceptions"].extend({
        **item, "message_id": None, "dispatch_id": None,
        "first_cause": f"{item['decision']} {item['first_cause']}"
        + (f" ({item['delivery_cause']})" if item.get("delivery_cause") else ""),
    } for item in report["decision_checks"]["issues"] if item["status"] == "FAIL")
    report["exception_count"] = len(report["exceptions"])
    return report


def markdown(report):
    def local(value):
        return utc(value).astimezone(LOCAL).strftime("%d %b %Y %H:%M GMT+7")
    def plain(value):
        return " ".join(str(value).split()).replace("|", "/")
    def heading(piece):
        return plain(piece["title"] or piece.get("first_line") or piece["piece_id"])
    lines = [f"Day readback: {local(report['window']['since_utc'])} to {local(report['window']['until_utc'])}.",
             f"Store observed: {local(report['observed_at_utc'])}; public HTTP observed at report time."]
    for piece in report["pieces"]:
        platforms = "; ".join(f"{r['platform']}={r['status']}" for r in piece["platforms"])
        clock = piece.get("first_dispatch_at_utc")
        dispatch = local(clock) if clock else "dispatch time unrecorded"
        lines.append(f"- {heading(piece)} ({dispatch}): {platforms or 'store rows missing'}.")
    digest = report["digest"]
    lines.append(f"Digest: {digest['state']}; recipients {digest['recipients'] if digest['recipients'] is not None else 'unknown'}; "
                 f"opens {digest['opens'] if digest['opens'] is not None else 'unknown'}; {digest['public_url'] or 'page unrecorded'}.")
    lines.append(f"Reply bot: {report['reply_bot']['delivered_count']} delivered drafts; "
                 + json.dumps(report["reply_bot"]["counts_by_kind_and_status"], sort_keys=True) + ".")
    if queue := report.get("plan_copy_queue"):
        overdue = queue["over_five_minutes"]
        lines.append(f"{len(overdue)} of {queue['ready_or_waiting']} ready or waiting plan copies "
                     f"were older than five minutes at {local(queue['observed_at_utc'])}.")
        for row in overdue:
            lines.append(f"- {row['plan_post']} / {row['platform']} was {row['status']} "
                         f"for {row['age_seconds']:.1f} seconds.")
    if delivery := report.get("plan_delivery"):
        lines.extend(["", "## Plan post delivery", ""])
        lines.append(f"{delivery['all_destinations_confirmed']} of {delivery['plan_posts']} plan posts "
                     "reached every named platform.")
        if delivery["copies"]:
            lines.extend(["", "| Plan post | Platform | State | Retry | First cause | Timing |",
                          "| --- | --- | --- | --- | --- | --- |"])
        for row in delivery["copies"]:
            timing = []
            publish_delay = row.get("source_to_published_seconds")
            verify_delay = row.get("source_to_first_verified_seconds")
            if row.get("observed_published_at_utc"):
                timing.append(f"Published at {local(row['observed_published_at_utc'])}")
            if row.get("first_verified_readback_at_utc"):
                timing.append(f"Verified at {local(row['first_verified_readback_at_utc'])}")
            if publish_delay is not None and publish_delay > PLAN_DELIVERY_TARGET_SECONDS:
                timing.append(f"Published {publish_delay:.1f}s after Main change (over 5 min)")
            if publish_delay is None and verify_delay is not None and verify_delay > PLAN_DELIVERY_TARGET_SECONDS:
                timing.append("First verified over 5 min after Main change. Publication time unrecorded.")
            if row["behind_over_ten_minutes"]:
                timing.append("Over 10 min behind first confirmed copy")
            if row["x_ready_over_five_minutes"]:
                timing.append("X READY over 5 min")
            state = row["status"]
            if row["public_url"]:
                state = f"[{state}]({row['public_url']})"
            retry = "Recorded" if row["retry_recorded"] else "—"
            lines.append(f"| {row['plan_post']} | {row['platform']} | {state} | {retry} | "
                         f"{row['first_cause'] or '—'} | {' · '.join(timing) or '—'} |")
    lines.extend(["", "## Engagement", "", f"Latest available cumulative counters through {local(report['engagement']['cutoff_utc'])}."])
    if not report["pieces"]:
        lines.append("No pieces in this window.")
    for piece in report["pieces"]:
        lines.append(f"- {heading(piece)}")
        unrecorded = []
        multiplicity = Counter(row["platform"] for row in piece["engagement"])
        for row in piece["engagement"]:
            platform = row["platform"]
            if row["first_cause"] == "NO_PUBLICATION_ROUTE_RECORDED":
                unrecorded.append(platform)
                continue
            if multiplicity[platform] > 1 and row["public_url"]:
                platform = f"[{platform}]({row['public_url']})"
            if cause := row["first_cause"]:
                collector = row.get("collector_state")
                detail = f"{cause} ({collector})" if collector else cause
                lines.append(f"  - **{platform}** · {detail}")
                continue
            metrics = [f"{m['value']} {m['source_metric'].replace('_', ' ')} ({local(m['collected_at_utc'])})"
                       for m in row["metrics"].values()]
            gaps = [f"{name} unavailable ({cause})" for name, cause in row["missing_metrics"].items()]
            lines.append(f"  - **{platform}** · " + " · ".join(metrics + gaps))
        if unrecorded:
            lines.append(f"  - {', '.join(unrecorded)} · NO_PUBLICATION_ROUTE_RECORDED")
    lines.append("")
    lines.append(f"Exceptions: {report['exception_count']}.")
    for item in report["exceptions"]:
        lines.append(f"- {plain(item['piece_id'])} / {item['platform'] or 'all'}: {item['status'] or 'readback'}; "
                     f"{item['first_cause']}; {item['public_url'] or 'no public URL'}.")
    if decisions := report.get("decision_checks"):
        lines.extend(["", "## Decision checks", "",
                      f"{decisions['failure_count']} failures and {decisions['unverified_count']} unverified checks."])
        for item in decisions["issues"]:
            url = f" · {item['public_url']}" if item["public_url"] else ""
            cause = f" ({item['delivery_cause']})" if item.get("delivery_cause") else ""
            gaps = item.get("missing_layers") or {}
            if gaps:
                cause += " (" + ", ".join(f"{key}={value}" for key, value in gaps.items()) + ")"
            lines.append(f"- {item['decision']} · {plain(item['piece_id'])} / {item['platform']} · "
                         f"{item['status']} · {item['first_cause']}{cause}{url}")
        for copy in decisions.get("plan_analysis", []):
            unavailable = [f"{key}={item['cause']}" for key, item in copy["layers"].items()
                           if item["state"] == "UNAVAILABLE"]
            if unavailable:
                lines.append(f"- 113 · {plain(copy['piece_id'])} / {copy['platform']} · "
                             f"Unavailable in the frozen plan ({', '.join(unavailable)})")
        if assist := decisions.get("antigravity"):
            lines.extend(["", "### Antigravity", "",
                          "| Job | Due | Calls | Code pass rate | Empty | Timeouts | Code / Codex fallback | Hours without call |",
                          "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"])
            for job in assist["jobs"]:
                rate = job["code_pass_rate_pct"]
                rate_text = f"{rate:.2f}%" if rate is not None else "—"
                if job["code_pass_rate_meets_90_pct"] is False:
                    rate_text += " (below 90%)"
                elif job["unchecked_returns"] or job["calls_incomplete_at_cutoff"]:
                    rate_text += " (incomplete evidence)"
                lines.append(f"| {job['job']} | {job['posts_due']} | {job['calls']} | {rate_text} | "
                             f"{job['empty_answers']} | {job['timeouts']} | "
                             f"{job['code_fallbacks']} / {job['codex_takeovers']} | {job['hours_without_recorded_call']:.3f} |")
            lines.append("Quota-free idle time awaits retained rate-limit coverage.")
    return "\n".join(lines) + "\n"


def _check_report(value):
    # A fixed projection, never a recursively redacted dump of private store data.
    if isinstance(value, dict):
        for key, item in value.items():
            if PRIVATE_KEY.search(key):
                raise ValueError("PRIVATE_FIELD_IN_REPORT")
            _check_report(item)
    elif isinstance(value, list):
        for item in value:
            _check_report(item)


def write_decision_checks(run_dir, decisions):
    _check_report(decisions)
    path = Path(run_dir) / DECISION_CHECKS_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix=".decision-checks-", delete=False,
                                mode="w", encoding="utf-8") as stream:
            temporary = Path(stream.name)
            json.dump(decisions, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        temporary.replace(path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    return path


def write_report(run_dir, report):
    _check_report(report)
    folder = Path(run_dir)
    folder.mkdir(parents=True, exist_ok=True)
    paths = (folder / "day_readback.json", folder / "day_readback.md")
    paths[0].write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    paths[1].write_text(markdown(report), encoding="utf-8")
    if "decision_checks" in report:
        write_decision_checks(folder, report["decision_checks"])
    return paths
