"""CC-748: Jim's manual posting desk for the platforms he posts by hand.

One pack per piece (plan post, plan result, wrap, article), built only from the
store rows and the payloads the automatic platforms already received. Each pack
holds one checked text per hand-posted platform (X as a thread, Substack Notes,
the LinkedIn company page, the YouTube community post), each ending with the
piece's confirmed Substack link, plus the full Substack text and the chart file.

Outputs, all under one desk folder (a parameter, so tests use a temporary one):
  index.html    a static page the minute job rewrites; no server, no port
  packs.json    the current packs, with their per-platform posted state
  sent.jsonl    phone-delivery ledger: a pack version is sent once, never again
  posted.jsonl  Jim's Posted marks (piece, platform, time, optional public URL)
  inbox.jsonl   desk requests read from the private bot (/packs, Latest packs)
  desk_state.json  first release time of each pack (for the 6-hour overdue mark)

The store is opened read-only (file URI ?mode=ro and PRAGMA query_only=ON). The
private bot is CC-464's: its own private-chat check and send path. No public
write, no browser, no model call. Jim presses Post himself on every platform.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from html import escape
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from urllib.parse import quote
from zoneinfo import ZoneInfo

from . import scenario_voice_v1 as voice

DESK_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\manual_desk")
SCHEMA = "contentops.manual_desk_pack.v1"
LOCAL = ZoneInfo("Asia/Bangkok")
HAND_PLATFORMS = ("x", "substack_notes", "linkedin_company", "youtube")
LABELS = {"x": "X", "substack_notes": "Substack Notes", "linkedin_company": "LinkedIn page",
          "youtube": "YouTube community"}
CODES = {"x": "x", "substack_notes": "n", "linkedin_company": "l", "youtube": "y"}
PLATFORM_BY_CODE = {code: platform for platform, code in CODES.items()}
# Limits as the destination compilers already use them (plan_call_cards_v1,
# market_wrap_editorial_v1, plan_status_posts_v1).
LIMITS = {"x": 280, "substack_notes": 10000, "linkedin_company": 3000, "youtube": 1000}
COMPOSERS = {
    "substack_notes": "https://substack.com/notes",
    "linkedin_company": "https://www.linkedin.com/company/143198922/admin/page-posts/published/?share=true",
    "youtube": "https://www.youtube.com/@CapitalChronicleYouTube/posts",
}
X_INTENT = "https://x.com/intent/post?text="
# A hand platform without its own received row borrows the most complete copy.
FALLBACK_SOURCES = ("telegram", "linkedin_company", "linkedin", "substack_notes", "facebook_page",
                    "discord", "threads", "instagram_business", "youtube", "x")
SOURCE_DESTINATIONS = set(FALLBACK_SOURCES) | set(HAND_PLATFORMS)
PLAN_KINDS = {"setup": "plan_post", "update": "plan_post", "correction": "plan_post",
              "call_followup": "plan_post", "result": "plan_result"}
NOT_POSTED = {"SUPERSEDED_NOT_POSTED", "STALE_NOT_POSTED"}
KIND_LABELS = {"plan_post": "Plan post", "plan_result": "Plan result", "wrap": "Market wrap",
               "article": "Article"}
PAGE_WAIT = timedelta(minutes=30)
OVERDUE_AFTER = timedelta(hours=6)
LOOKBACK = timedelta(hours=72)
PUSH_WINDOW = timedelta(hours=6)       # first live run never floods the phone with history
PULL_WINDOW = timedelta(hours=48)
MAX_PUSH_PER_TICK, MAX_PULL_PACKS = 3, 5
TELEGRAM_CHUNK = 4000
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
CALLBACK_PREFIX = "dk:"
_SUBSTACK_LINK = re.compile(r"https://[a-z0-9.-]*substack\.com/p/[^\s<>\"')\]]+", re.I)
_ANY_LINK = re.compile(r"https?://[^\s<>\"')\]]+", re.I)
# Our own public post addresses, as the platform dispatches record them.
_OWN_POST = re.compile(r"^https://(?:(?:www\.)?(?:x|twitter)\.com/capitalnicle/status/\d+|"
                       r"substack\.com/@capitalchronicle/note/|"
                       r"www\.linkedin\.com/(?:feed/update/urn:li:(?:activity|share|ugcPost):\d+|company/143198922/)|"
                       r"(?:www\.)?youtube\.com/(?:post/|@CapitalChronicleYouTube/))", re.I)
_CREDIT = re.compile(r"^(?:Chart|Charts|Image):\s*TradingView\.?$", re.I)


class DeskError(ValueError):
    """A fixed cause only; never carries a payload, a chat id or a token."""


# ----------------------------------------------------------------- small files

def utcnow():
    return datetime.now(timezone.utc)


def _clock(value):
    if not value:
        return None
    value = str(value).replace("Z", "+00:00")
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _iso(moment):
    return moment.astimezone(timezone.utc).isoformat() if moment else None


def _local(moment):
    return moment.astimezone(LOCAL).strftime("%a %d %b %H:%M") + " GMT+7" if moment else ""


def _read_jsonl(path):
    path = Path(path)
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # a torn last line from an interrupted write is skipped, not fatal
    return rows


def _append_jsonl(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _write_atomic(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temp, path)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise


def _read_json(path, default):
    path = Path(path)
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def pack_id_for(piece_id):
    return "cc748-" + sha256(piece_id.encode("utf-8")).hexdigest()[:12]


def _short(pack_id):
    return pack_id.removeprefix("cc748-")


# -------------------------------------------------------------------- the store

def open_store_read_only(store_path):
    path = Path(store_path).resolve()
    uri = "file:" + quote(path.as_posix(), safe="/:") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def _payload(row):
    try:
        value = json.loads(row["payload"])
    except (TypeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _dispatches(conn, message_id):
    return [dict(r) for r in conn.execute(
        "SELECT platform, status, public_object_url, dispatched_at FROM platform_dispatches "
        "WHERE message_id = ? ORDER BY dispatched_at", (message_id,))]


def _confirmed(dispatches):
    return [d for d in dispatches if d["status"] == "DISPATCH_CONFIRMED"]


def page_link(conn, page_work_item):
    """The newest confirmed Substack page of a work item, with its confirmation time."""
    best = None
    for row in conn.execute("SELECT message_id FROM outbox_messages WHERE work_item_id = ? "
                            "AND destination = 'substack' ORDER BY created_at", (page_work_item,)):
        for dispatch in _confirmed(_dispatches(conn, row["message_id"])):
            url = dispatch.get("public_object_url") or ""
            if _SUBSTACK_LINK.fullmatch(url):
                moment = _clock(dispatch["dispatched_at"])
                if best is None or (moment and best[1] and moment > best[1]):
                    best = (url, moment, row["message_id"])
    return best


def _received_text(payload):
    native = payload.get("native_payload") if isinstance(payload.get("native_payload"), dict) else {}
    plan = payload.get("destination_plan") if isinstance(payload.get("destination_plan"), dict) else {}
    for value in (native.get("full_text"), native.get("text"), payload.get("payload"), plan.get("payload")):
        if isinstance(value, str) and value.strip():
            return value.replace("\r\n", "\n").strip()
    posts = native.get("posts")
    if isinstance(posts, list) and posts:
        return "\n\n".join(p.get("text", "") for p in posts if isinstance(p, dict)).strip() or None
    return None


def _media_ids(payload):
    native = payload.get("native_payload") if isinstance(payload.get("native_payload"), dict) else {}
    ids = list(native.get("media_asset_ids") or [])
    for post in native.get("posts") or []:
        if isinstance(post, dict):
            ids.extend(post.get("media_asset_ids") or [])
    return [i for i in ids if isinstance(i, str)]


def _resolve_image(output_dir, media_ids):
    if not output_dir or not media_ids:
        return None
    manifest = _read_json(Path(output_dir) / "delivery_media_manifest_v1.json", {})
    by_id = {a.get("media_asset_id"): a for a in manifest.get("assets", []) if isinstance(a, dict)}
    for media_id in media_ids:
        asset = by_id.get(media_id) or {}
        path = asset.get("absolute_local_source_path")
        if path and Path(path).suffix.lower() in IMAGE_SUFFIXES and Path(path).is_file():
            return str(Path(path))
    return None


def _full_substack_text(conn, page_work_item, page_message_id):
    if not page_message_id:
        return None
    row = conn.execute("SELECT payload FROM outbox_messages WHERE message_id = ?", (page_message_id,)).fetchone()
    payload = _payload(row) if row else {}
    native = payload.get("native_payload") if isinstance(payload.get("native_payload"), dict) else {}
    title, subtitle, body = native.get("title"), native.get("subtitle"), native.get("body_markdown")
    if not body and payload.get("output_dir"):
        manifest = _read_json(Path(payload["output_dir"]) / "article_manifest_v1.json", {})
        title = title or manifest.get("title")
        subtitle = subtitle or manifest.get("subtitle")
        body = manifest.get("substack_body_markdown")
    if not body:
        return None
    return "\n\n".join(str(p).strip() for p in (title, subtitle, body) if p and str(p).strip())


def collect_pieces(conn, *, now, lookback=LOOKBACK):
    """Every recent piece the automatic platforms received, keyed by its work item."""
    cutoff = _iso(now - lookback)
    pieces = {}
    for row in conn.execute("SELECT * FROM outbox_messages WHERE destination = 'internal:plan-status-post' "
                            "AND created_at >= ? ORDER BY created_at", (cutoff,)):
        value = _payload(row)
        kind = PLAN_KINDS.get(value.get("kind"))
        if not kind or row["status"] in NOT_POSTED or not value.get("plan_id"):
            continue
        piece_id = value.get("key") or row["message_id"]
        pieces[piece_id] = {"piece_id": piece_id, "kind": kind,
            "title": value.get("instrument_title") or value.get("symbol") or "Plan",
            "lead": (value.get("lead") or "").strip(), "created_at": row["created_at"],
            "page_work_item": "plan-analysis-" + value["plan_id"],
            "conditional_calls": value.get("conditional_calls") or [],
            "scenario_voice": value.get("scenario_voice"),
            "source_text": value.get("text") or ""}
    for row in conn.execute("SELECT * FROM outbox_messages WHERE destination = 'internal:market-wrap' "
                            "AND created_at >= ? ORDER BY created_at", (cutoff,)):
        value = _payload(row)
        piece_id = row["work_item_id"]
        title = value.get("title") or ("Weekend market wrap" if "weekly" in piece_id else "Market wrap")
        pieces[piece_id] = {"piece_id": piece_id, "kind": "wrap", "title": title, "lead": "",
                            "created_at": row["created_at"], "page_work_item": piece_id,
                            "conditional_calls": [], "source_text": ""}
    for row in conn.execute("SELECT * FROM outbox_messages WHERE destination = 'substack' "
                            "AND created_at >= ? ORDER BY created_at", (cutoff,)):
        piece_id = row["work_item_id"]
        if piece_id in pieces or piece_id.startswith("plan-analysis-") or not _confirmed(_dispatches(conn, row["message_id"])):
            continue
        value = _payload(row)
        native = value.get("native_payload") if isinstance(value.get("native_payload"), dict) else {}
        manifest = _read_json(Path(value["output_dir"]) / "article_manifest_v1.json", {}) if value.get("output_dir") else {}
        title = native.get("title") or manifest.get("title") or piece_id
        # An article leads with its headline; its dek follows when no platform copy exists.
        pieces[piece_id] = {"piece_id": piece_id, "kind": "article", "title": title, "lead": title.strip(),
            "dek": (native.get("subtitle") or manifest.get("subtitle") or "").strip(),
            "created_at": row["created_at"], "page_work_item": piece_id,
            "conditional_calls": manifest.get("conditional_calls") or [], "source_text": ""}
    return pieces


def _platform_rows(conn, piece_id):
    rows = {}
    for row in conn.execute("SELECT * FROM outbox_messages WHERE work_item_id = ? ORDER BY created_at", (piece_id,)):
        destination = row["destination"]
        if destination not in SOURCE_DESTINATIONS and destination != "substack":
            continue
        payload = _payload(row)
        dispatches = _dispatches(conn, row["message_id"])
        entry = {"text": _received_text(payload), "media_ids": _media_ids(payload),
                 "output_dir": payload.get("output_dir"), "confirmed": _confirmed(dispatches),
                 "created_at": row["created_at"]}
        # The newest row with text per destination is the copy the platform got.
        if entry["text"] or destination not in rows:
            rows[destination] = entry
    return rows


# ------------------------------------------------------------------ composition

def _notice():
    from .event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE
    return PUBLIC_NOTICE + " " + CONFLICTS_NOTICE


def _split_lines(text):
    """Body lines (links removed), plus the chart credit if the copy had one."""
    from .event_article_guard_v1 import CONFLICTS_NOTICE, PUBLIC_NOTICE
    body, credit = [], None
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if _CREDIT.match(line):
            credit = "Chart: TradingView"
            continue
        line = line.replace(PUBLIC_NOTICE, "").replace(CONFLICTS_NOTICE, "").strip()
        if _SUBSTACK_LINK.search(line):
            rest = _SUBSTACK_LINK.sub("", line).strip(" :-–—")
            # "Full analysis: <link>" and bare links go; a sentence keeps its words.
            line = "" if len(rest) <= 40 and not re.search(r"[.!?]$", rest) else _SUBSTACK_LINK.sub("", line).strip()
        try:
            voice.validate_copy(line)
        except ValueError:
            # The prior post keeps its bytes. A fresh pasteable copy never reuses its target line.
            continue
        if line or (body and body[-1]):
            body.append(line)
    while body and not body[-1]:
        body.pop()
    return body, credit


def _call_wordings(calls):
    from .event_article_guard_v1 import (compact_reader_conditional_call_text, conditional_call_text,
                                         reader_conditional_call_text, thread_reader_conditional_call_text)
    wordings = []
    for call in calls:
        for render in (conditional_call_text, reader_conditional_call_text,
                       compact_reader_conditional_call_text, thread_reader_conditional_call_text):
            try:
                wordings.append(render(call))
            except (KeyError, TypeError, AttributeError):
                continue
    return [w for w in wordings if w]


def _ordered_body(body, lead):
    """The call first: the lead line moves to the top; the rest keep their order."""
    if lead:
        body = [line for line in body if line != lead]
        body = [lead] + ([""] if body and body[0] else []) + body if body else [lead]
    return body


def _assemble(body, credit, link):
    parts = ["\n".join(body).strip(), _notice()]
    if credit:
        parts.append(credit)
    if link:
        parts.append("Full analysis: " + link)
    return "\n\n".join(p for p in parts if p)


def compose_text(base_text, *, lead, link, limit, calls=(), scenario_voice=False):
    """One platform text: the call first, the analysis lines, the notice, the link last."""
    body, credit = _split_lines(base_text)
    body = _ordered_body(body, lead)
    protected = {lead} | {line for line in body for w in _call_wordings(calls) if w and w in line}

    def drop_priority(line):
        leads_analysis = re.match(r"(?:Scenarios: |(?:Base|Bull|Bear) case\b|Event and cause: |"
                                  r"Macro: |Fundamentals: |Positioning and sentiment: |Priced in: )",
                                  line, re.I)
        return (not (scenario_voice and leads_analysis), len(line))

    text = _assemble(body, credit, link)
    while len(text) > limit:
        candidates = [line for line in body if line and line not in protected]
        if not candidates:
            raise DeskError("TEXT_DOES_NOT_FIT_" + str(limit))
        # Keep scenario and causal lines ahead of ancillary commentary when space is tight.
        body.remove(max(candidates, key=drop_priority))
        text = _assemble(body, credit, link)
    return text


def _sentences(line, limit):
    pieces, current = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", line):
        if len(sentence) > limit:
            words, sentence_parts = sentence.split(), []
            chunk = ""
            for word in words:
                if len((chunk + " " + word).strip()) > limit:
                    sentence_parts.append(chunk)
                    chunk = word
                else:
                    chunk = (chunk + " " + word).strip()
            sentence_parts.append(chunk)
            pieces.extend([current] if current else [])
            pieces.extend(sentence_parts[:-1])
            current = sentence_parts[-1]
            continue
        if len((current + " " + sentence).strip()) > limit:
            pieces.append(current)
            current = sentence
        else:
            current = (current + " " + sentence).strip()
    if current:
        pieces.append(current)
    return [p for p in pieces if p]


def compose_x_thread(base_text, *, lead, link, limit=LIMITS["x"]):
    """An X thread: each part within the limit, the call and credit in the root, the link last.

    A line longer than a part splits at sentence ends only; sentences of one line
    stay joined by a space inside a part, so the call wording reads as written.
    """
    body, credit = _split_lines(base_text)
    body = [line for line in _ordered_body(body, lead) if line]
    units = []  # (text, joiner to the previous unit)
    for line in body:
        pieces = _sentences(line, limit) if len(line) > limit else [line]
        units.extend((piece, "\n" if n == 0 else " ") for n, piece in enumerate(pieces))
    parts, current = [], ""
    root_extra = "\n\n" + credit if credit else ""
    for unit, joiner in units:
        extra = root_extra if not parts else ""
        if current and len(current + joiner + unit + extra) > limit:
            parts.append(current + extra)
            current = unit
        else:
            current = current + joiner + unit if current else unit
    if current:
        parts.append(current + (root_extra if not parts else ""))
    elif credit:
        parts.append(credit)
    tail = [_notice()] + (["Full analysis: " + link] if link else [])
    for unit in tail:
        for piece in (_sentences(unit, limit) if len(unit) > limit else [unit]):
            if parts and len(parts[-1] + "\n\n" + piece) <= limit:
                parts[-1] = parts[-1] + "\n\n" + piece
            else:
                parts.append(piece)
    if any(len(p) > limit for p in parts):
        raise DeskError("X_PART_OVER_LIMIT")
    return parts


def thread_as_copy(parts):
    """The thread read as one copy, with a part break read as the space it replaced."""
    return " ".join(" ".join(line for line in part.split("\n") if line) for part in parts)


def check_copy(text, *, calls, source, received, scenario_voice=False):
    """The existing public checks on one text: decisions 40/109 and the rights filter,
    then CC-466's reader check (numbers bound to the received copy, no cut sentences).

    The privacy, rights and AI-label filter (plan_analysis_pages_v1.public_filter:
    no sizes, money, accounts or model names) is enforced on every text, always.
    The two format checks guard what this desk adds: a format rule the received copy
    itself already fails, with the same cause, does not fit that piece (for example a
    measured-odds article's results in R, admitted by its own owner), so it is
    reported, not enforced, because the words are the ones the platform received.
    """
    from .event_article_guard_v1 import PublicOutputError, check_publication_copy
    from .plan_analysis_pages_v1 import public_filter
    from .plan_reader_copy_v1 import check_text
    try:
        public_filter(text)
    except ValueError as exc:
        raise DeskError("PUBLIC_FILTER_" + str(exc).split(":")[0]) from None
    try:
        notes = voice.validate_copy(text, plan=scenario_voice)
    except ValueError as exc:
        raise DeskError(str(exc)) from None
    try:
        check_publication_copy({"text": text}, conditional_calls=list(calls), require_call_text=bool(calls))
    except PublicOutputError as exc:
        try:
            check_publication_copy({"text": received}, conditional_calls=list(calls), require_call_text=False)
        except PublicOutputError as base_exc:
            if base_exc.cause != exc.cause:
                raise DeskError("PUBLIC_CHECK_" + exc.cause) from None
            notes.append("PUBLIC_CHECK_AS_RECEIVED_" + exc.cause)
        else:
            raise DeskError("PUBLIC_CHECK_" + exc.cause) from None
    try:
        check_text(text, source=source, check_numbers=True, prose=False)
    except ValueError as exc:
        cause = str(exc).split(":")[0]
        try:
            check_text(received, source=source, check_numbers=False, prose=False)
        except ValueError as base_exc:
            if str(base_exc).split(":")[0] != cause:
                raise DeskError("READER_CHECK_" + cause) from None
            notes.append("READER_CHECK_AS_RECEIVED_" + cause)
        else:
            raise DeskError("READER_CHECK_" + cause) from None
    return " ".join(notes) or "PASS"


def x_intent(text):
    return X_INTENT + quote(text, safe="")


def build_pack(conn, piece, *, now):
    rows = _platform_rows(conn, piece["piece_id"])
    confirmed = sorted(_clock(d["dispatched_at"]) for r in rows.values() for d in r["confirmed"]
                       if _clock(d["dispatched_at"]))
    if not confirmed:
        return None  # nothing went out yet: no pack before the automatic copy exists
    link = page_link(conn, piece["page_work_item"])
    first_post = confirmed[0]
    url, linked_at, page_message = link if link else (None, None, None)
    if url:
        page_state = "LINKED"
    elif now - first_post >= PAGE_WAIT:
        page_state = "PAGE_PENDING"
    else:
        page_state = "WAITING_FOR_PAGE"
    image = None
    for destination in ("telegram", "x", "linkedin_company", "substack_notes", "youtube", *FALLBACK_SOURCES):
        entry = rows.get(destination)
        if entry:
            image = _resolve_image(entry["output_dir"], entry["media_ids"])
            if image:
                break
    if not image and page_message:
        page_row = conn.execute("SELECT payload FROM outbox_messages WHERE message_id = ?", (page_message,)).fetchone()
        page_payload = _payload(page_row) if page_row else {}
        if page_payload.get("output_dir"):
            manifest = _read_json(Path(page_payload["output_dir"]) / "article_manifest_v1.json", {})
            image = _resolve_image(page_payload["output_dir"], [manifest.get("lead_image_asset_id")])
    received = {d: r["text"] for d, r in rows.items() if r.get("text") and d != "substack"}
    full_text = _full_substack_text(conn, piece["page_work_item"], page_message)
    if not received:
        fallback = "\n\n".join(dict.fromkeys(p for p in (piece["title"], piece.get("dek"), piece["lead"]) if p))
        received = {"substack": fallback}
    source = "\n".join([*received.values(), piece.get("source_text") or "", url or "", piece["title"], full_text or ""])
    platforms = {}
    scenario_voice = piece.get("scenario_voice") == voice.CONTRACT
    for platform in HAND_PLATFORMS:
        # X re-threads the complete Telegram copy: X's stored full text is its parts
        # joined, which can place the chart credit inside a sentence (seen 17 Nov).
        order = ("telegram", "x") if platform == "x" else (platform,)
        base_from = next((d for d in (*order, *FALLBACK_SOURCES, "substack") if received.get(d)), None)
        entry = {"base_source": base_from, "limit": LIMITS[platform], "label": LABELS[platform]}
        try:
            if platform == "x":
                parts = compose_x_thread(received[base_from], lead=piece["lead"], link=url)
                entry.update(parts=parts, text="\n\n".join(parts), composer_url=x_intent(parts[0]))
                # The thread is one copy for decision 40's call wording and the notice.
                entry["check"] = check_copy(thread_as_copy(parts), calls=piece["conditional_calls"],
                                            source=source, received=received[base_from], scenario_voice=scenario_voice)
            else:
                text = compose_text(received[base_from], lead=piece["lead"], link=url,
                                     limit=LIMITS[platform], calls=piece["conditional_calls"], scenario_voice=scenario_voice)
                entry.update(text=text, composer_url=COMPOSERS[platform])
                entry["check"] = check_copy(text, calls=piece["conditional_calls"], source=source,
                                            received=received[base_from], scenario_voice=scenario_voice)
            entry["chars"] = max(len(p) for p in entry["parts"]) if platform == "x" else len(entry["text"])
            entry["status"] = "READY"
        except DeskError as exc:
            entry.update(status="WITHHELD", cause=str(exc), text=None, parts=None)
        platforms[platform] = entry
    pack = {"schema_version": SCHEMA, "pack_id": pack_id_for(piece["piece_id"]), "piece_id": piece["piece_id"],
            "kind": piece["kind"], "kind_label": KIND_LABELS[piece["kind"]], "title": piece["title"],
            "lead": piece["lead"], "created_at_utc": _iso(_clock(piece["created_at"])),
            "first_post_at_utc": _iso(first_post), "substack_url": url, "page_confirmed_at_utc": _iso(linked_at),
            "page_state": page_state, "released": page_state != "WAITING_FOR_PAGE",
            "image_path": image, "full_text": full_text, "platforms": platforms,
            "public_submit_actions": 0}
    pack["content_sha256"] = sha256(json.dumps({k: pack[k] for k in ("substack_url", "platforms", "image_path")},
                                               sort_keys=True).encode("utf-8")).hexdigest()
    return pack


def build_packs(store_path, *, now=None, lookback=LOOKBACK):
    now = now or utcnow()
    conn = open_store_read_only(store_path)
    try:
        pieces = collect_pieces(conn, now=now, lookback=lookback)
        packs, causes = [], {}
        for piece in pieces.values():
            try:
                pack = build_pack(conn, piece, now=now)
            except (DeskError, KeyError, TypeError, ValueError, OSError) as exc:
                causes[piece["piece_id"]] = str(exc) if isinstance(exc, DeskError) else type(exc).__name__
                continue
            if pack:
                packs.append(pack)
    finally:
        conn.close()
    packs.sort(key=lambda p: p["first_post_at_utc"] or "", reverse=True)
    return packs, causes


# ---------------------------------------------------------------- posted state

def posted_state(desk_root):
    """{pack_id: {platform: newest record}} from posted.jsonl."""
    state = {}
    for record in _read_jsonl(Path(desk_root) / "posted.jsonl"):
        pack, platform = record.get("pack_id"), record.get("platform")
        if pack and platform in HAND_PLATFORMS:
            prior = state.setdefault(pack, {}).get(platform)
            # The first mark keeps its time; a later record with the public URL adds the link.
            if not prior:
                state[pack][platform] = dict(record)
            elif record.get("public_url") and not prior.get("public_url"):
                prior["public_url"] = record["public_url"]
    return state


def annotate(packs, *, desk_root, now):
    """Release times persist across runs; each pack gets NEW, PARTLY_POSTED, POSTED or OVERDUE."""
    root = Path(desk_root)
    saved = _read_json(root / "desk_state.json", {"packs": {}})
    saved.setdefault("packs", {})
    posted = posted_state(root)
    for pack in packs:
        entry = saved["packs"].setdefault(pack["pack_id"], {"piece_id": pack["piece_id"]})
        if pack["released"] and not entry.get("released_at_utc"):
            entry["released_at_utc"] = _iso(now)
        if pack["substack_url"] and not entry.get("linked_at_utc"):
            entry["linked_at_utc"] = _iso(now)
        pack["released_at_utc"] = entry.get("released_at_utc")
        marks = posted.get(pack["pack_id"], {})
        needed = [p for p in HAND_PLATFORMS if pack["platforms"][p]["status"] == "READY"]
        for platform in HAND_PLATFORMS:
            record = marks.get(platform)
            pack["platforms"][platform]["posted"] = bool(record)
            pack["platforms"][platform]["posted_at_utc"] = record.get("posted_at_utc") if record else None
            pack["platforms"][platform]["public_url"] = record.get("public_url") if record else None
        done = [p for p in needed if marks.get(p)]
        released = _clock(pack["released_at_utc"])
        if not pack["released"]:
            pack["state"] = "WAITING_FOR_PAGE"
        elif needed and len(done) == len(needed):
            pack["state"] = "POSTED"
        elif released and now - released >= OVERDUE_AFTER:
            pack["state"] = "OVERDUE"
        else:
            pack["state"] = "PARTLY_POSTED" if done else "NEW"
        pack["unposted_platforms"] = [p for p in needed if not marks.get(p)]
    _write_atomic(root / "desk_state.json", json.dumps(saved, sort_keys=True, indent=1))
    return packs


def overdue_packs(desk_root):
    """For the evening check: released packs still unposted after 6 hours, from packs.json."""
    value = _read_json(Path(desk_root) / "packs.json", {})
    return [{"pack_id": p["pack_id"], "piece_id": p["piece_id"], "title": p["title"],
             "unposted_platforms": p.get("unposted_platforms", [])}
            for p in value.get("packs", []) if p.get("state") == "OVERDUE"]


# ------------------------------------------------------------------- the page

_PAGE_CSS = """
:root{--bg:#f6f5f1;--card:#fff;--ink:#1d1d1b;--muted:#6b6a65;--line:#dedbd2;--accent:#1f5fa8;
--new:#1f5fa8;--ok:#2e7d4f;--late:#b3261e;--wait:#8a6d1d}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--card:#21211f;--ink:#ecebe6;--muted:#a3a29b;
--line:#3a3935;--accent:#7fb0ec;--new:#7fb0ec;--ok:#6fc28f;--late:#f08a80;--wait:#d8b860}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}h1{font-size:20px;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 16px}.pack{background:var(--card);border:1px solid var(--line);
border-radius:8px;padding:14px;margin:0 0 16px}.head{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline}
.head h2{font-size:17px;margin:0;flex:1 1 300px}.badge{font-size:12px;font-weight:600;padding:2px 8px;
border-radius:10px;border:1px solid currentColor}.NEW{color:var(--new)}.POSTED{color:var(--ok)}
.PARTLY_POSTED{color:var(--new)}.OVERDUE{color:var(--late)}.WAITING_FOR_PAGE,.PAGE_PENDING{color:var(--wait)}
.meta{color:var(--muted);font-size:13px;margin:6px 0}.links a{margin-right:14px}a{color:var(--accent)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px;margin-top:10px}
.plat{border:1px solid var(--line);border-radius:6px;padding:10px;min-width:0}
.plat h3{font-size:14px;margin:0 0 6px;display:flex;gap:8px;align-items:center}
pre{white-space:pre-wrap;word-break:break-word;font:13px/1.4 ui-monospace,Consolas,monospace;
background:var(--bg);padding:8px;border-radius:4px;margin:6px 0}
button{font:inherit;font-size:13px;padding:4px 10px;border:1px solid var(--line);border-radius:4px;
background:var(--card);color:var(--ink);cursor:pointer}button:active{transform:translateY(1px)}
.done{color:var(--ok);font-size:12px;font-weight:600}.withheld{color:var(--late);font-size:13px}
details{margin-top:10px}summary{cursor:pointer;color:var(--accent)}img{max-width:100%;height:auto;
border-radius:4px;margin-top:8px;max-height:280px}
"""

_PAGE_JS = """
document.addEventListener('click', function (e) {
  var b = e.target.closest('button[data-copy]');
  if (!b) return;
  var text = document.getElementById(b.getAttribute('data-copy')).textContent;
  function done() { var o = b.textContent; b.textContent = 'Copied'; setTimeout(function () { b.textContent = o; }, 1200); }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(done, function () { fallback(text); done(); });
  } else { fallback(text); done(); }
  function fallback(t) { var a = document.createElement('textarea'); a.value = t; document.body.appendChild(a);
    a.select(); try { document.execCommand('copy'); } catch (x) {} document.body.removeChild(a); }
});
"""


def _file_uri(path):
    return Path(path).resolve().as_uri()


def render_page(packs, *, now):
    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width,initial-scale=1">',
           '<meta http-equiv="refresh" content="60"><title>Posting desk</title>',
           "<style>" + _PAGE_CSS + "</style></head><body><main>",
           "<h1>Posting desk</h1>",
           f'<p class="sub">Rewritten {escape(_local(now))} by the minute job. Newest first. '
           "Copy a text, open the composer, press Post yourself, then tap Posted in the bot.</p>"]
    if not packs:
        out.append('<p class="sub">No packs in the last 72 hours.</p>')
    for index, pack in enumerate(packs):
        state = pack.get("state", "NEW")
        out.append('<section class="pack"><div class="head">')
        out.append(f"<h2>{escape(pack['kind_label'])}: {escape(pack['title'])}</h2>")
        out.append(f'<span class="badge {state}">{escape(state.replace("_", " ").lower())}</span>')
        if pack["page_state"] == "PAGE_PENDING":
            out.append('<span class="badge PAGE_PENDING">page pending</span>')
        out.append("</div>")
        if pack.get("lead") and pack["lead"] != pack["title"]:
            out.append(f'<div class="meta">{escape(pack["lead"])}</div>')
        out.append(f'<div class="meta">First post {escape(_local(_clock(pack["first_post_at_utc"])))}'
                   f' · piece {escape(pack["piece_id"])}</div>')
        if state == "WAITING_FOR_PAGE":
            out.append('<div class="meta">Waiting for its Substack page (up to 30 minutes after the first post).</div></section>')
            continue
        links = []
        if pack["substack_url"]:
            links.append(f'<a href="{escape(pack["substack_url"])}" target="_blank" rel="noopener">Substack page</a>')
        else:
            links.append("<span>Substack page pending: the link is added once the page is confirmed.</span>")
        if pack.get("image_path"):
            uri = escape(_file_uri(pack["image_path"]))
            links.append(f'<a href="{uri}" download>Save the chart</a>')
        out.append('<div class="links meta">' + "".join(links) + "</div>")
        if pack.get("image_path"):
            out.append(f'<img src="{escape(_file_uri(pack["image_path"]))}" alt="Chart for {escape(pack["title"])}" loading="lazy">')
        out.append('<div class="grid">')
        for platform in HAND_PLATFORMS:
            entry = pack["platforms"][platform]
            out.append(f'<div class="plat"><h3>{escape(entry["label"])}')
            if entry.get("posted"):
                when = _local(_clock(entry.get("posted_at_utc")))
                out.append(f'<span class="done">posted {escape(when)}</span>')
            out.append("</h3>")
            if entry["status"] != "READY":
                out.append(f'<div class="withheld">Withheld: {escape(entry.get("cause", ""))}</div></div>')
                continue
            texts = entry["parts"] if platform == "x" else [entry["text"]]
            for n, text in enumerate(texts):
                ident = f"t{index}-{platform}-{n}"
                label = f"Copy part {n + 1} of {len(texts)}" if len(texts) > 1 else "Copy"
                out.append(f'<pre id="{ident}">{escape(text)}</pre>'
                           f'<button type="button" data-copy="{ident}">{label}</button> ')
            name = "X composer (part 1)" if platform == "x" else entry["label"] + " composer"
            out.append(f'<a href="{escape(entry["composer_url"])}" target="_blank" rel="noopener">Open {escape(name)}</a>')
            if entry.get("public_url"):
                out.append(f' · <a href="{escape(entry["public_url"])}" target="_blank" rel="noopener">the post</a>')
            out.append("</div>")
        out.append("</div>")
        if pack.get("full_text"):
            ident = f"t{index}-full"
            out.append(f'<details><summary>Full Substack text</summary><pre id="{ident}">{escape(pack["full_text"])}</pre>'
                       f'<button type="button" data-copy="{ident}">Copy the full text</button></details>')
        out.append("</section>")
    out.append("</main><script>" + _PAGE_JS + "</script></body></html>")
    return "\n".join(out)


def write_page(packs, *, desk_root, now):
    root = Path(desk_root)
    _write_atomic(root / "index.html", render_page(packs, now=now))
    _write_atomic(root / "packs.json", json.dumps({"schema_version": SCHEMA, "written_at_utc": _iso(now),
        "packs": packs}, sort_keys=True, ensure_ascii=False, indent=1))
    return root / "index.html"


# ----------------------------------------------------------- the private bot

def _keyboard(rows):
    return {"inline_keyboard": [row for row in rows if row]}


def _chunks(text, limit=TELEGRAM_CHUNK):
    if len(text) <= limit:
        return [text]
    chunks, current = [], ""
    for line in text.split("\n"):
        if current and len(current) + 1 + len(line) > limit:
            chunks.append(current)
            current = line
        else:
            current = (current + "\n" + line) if current else line
    chunks.append(current)
    return [c for c in chunks if c]


def _pack_messages(pack, *, platforms, note=None):
    """Messages for one pack: a header, then one plain message per platform text."""
    header = [f"POSTING PACK · {pack['kind_label']}: {pack['title']}"]
    if note:
        header.append(note)
    if pack.get("lead") and pack["lead"] != pack["title"]:
        header.append(pack["lead"])
    header.append("Substack: " + pack["substack_url"] if pack["substack_url"]
                  else "Substack page pending: the link follows when the page is confirmed.")
    header.append("Each text below is its own message: long-press to copy, open the composer, "
                  "press Post yourself, then tap Posted.")
    messages = [{"platform": None, "text": "\n".join(header), "reply_markup": _keyboard([
        [{"text": "Open Substack page", "url": pack["substack_url"]}] if pack["substack_url"] else None,
        [{"text": "Latest packs", "callback_data": CALLBACK_PREFIX + "l"}]])}]
    for platform in platforms:
        entry = pack["platforms"][platform]
        if entry["status"] != "READY":
            continue
        texts = entry["parts"] if platform == "x" else _chunks(entry["text"])
        posted = {"text": "Posted on " + LABELS[platform],
                  "callback_data": f"{CALLBACK_PREFIX}p:{_short(pack['pack_id'])}:{CODES[platform]}"}
        opener = {"text": ("Open X composer" if platform == "x" else "Open " + LABELS[platform]),
                  "url": entry["composer_url"]}
        for n, text in enumerate(texts):
            markup = _keyboard([[opener, posted]]) if n == 0 else None
            messages.append({"platform": platform, "text": text, "reply_markup": markup, "part": n})
    return messages


def _ledger(desk_root):
    return _read_jsonl(Path(desk_root) / "sent.jsonl")


def send_pack(pack, *, bot, chat_id, desk_root, version_key, platforms, note=None, now):
    """Send one pack version. The SENDING line is written first: a restart never re-sends it."""
    from .x_reply_bot_v1 import BotError
    ledger = Path(desk_root) / "sent.jsonl"
    _append_jsonl(ledger, {"kind": "pack", "version_key": version_key, "pack_id": pack["pack_id"],
                           "piece_id": pack["piece_id"], "status": "SENDING", "at_utc": _iso(now)})
    sent = 0
    try:
        if pack.get("image_path") and Path(pack["image_path"]).is_file():
            try:
                photo = bot.send_photo(chat_id, pack["image_path"])
                _append_jsonl(ledger, {"kind": "message", "version_key": version_key, "pack_id": pack["pack_id"],
                                       "platform": None, "message_id": (photo or {}).get("message_id"),
                                       "image": True})
            except BotError as exc:
                _append_jsonl(ledger, {"kind": "image_unconfirmed", "version_key": version_key, "cause": str(exc)})
        for message in _pack_messages(pack, platforms=platforms, note=note):
            payload = {"chat_id": chat_id, "text": message["text"], "link_preview_options": {"is_disabled": True}}
            if message["reply_markup"]:
                payload["reply_markup"] = message["reply_markup"]
            result = bot.call("sendMessage", payload)
            sent += 1
            _append_jsonl(ledger, {"kind": "message", "version_key": version_key, "pack_id": pack["pack_id"],
                                   "platform": message["platform"], "part": message.get("part"),
                                   "message_id": (result or {}).get("message_id")})
    except BotError as exc:
        _append_jsonl(ledger, {"kind": "pack", "version_key": version_key, "pack_id": pack["pack_id"],
                               "status": "UNCERTAIN", "cause": str(exc), "messages_sent": sent})
        return {"version_key": version_key, "status": "UNCERTAIN", "cause": str(exc), "messages_sent": sent}
    _append_jsonl(ledger, {"kind": "pack", "version_key": version_key, "pack_id": pack["pack_id"],
                           "status": "SENT", "messages_sent": sent, "at_utc": _iso(utcnow())})
    return {"version_key": version_key, "status": "SENT", "messages_sent": sent}


def push_new(packs, *, bot, chat_id, desk_root, now, max_packs=MAX_PUSH_PER_TICK):
    """Push each released pack once; a page-pending pack gets one follow-up once linked."""
    started = {r["version_key"] for r in _ledger(desk_root) if r.get("kind") == "pack"}
    results = []
    for pack in sorted(packs, key=lambda p: p["first_post_at_utc"] or ""):  # oldest first, so order reads naturally
        if len(results) >= max_packs:
            break
        first = _clock(pack["first_post_at_utc"])
        if not pack["released"] or pack.get("state") == "POSTED" or not first or now - first > PUSH_WINDOW:
            continue
        pending_key, linked_key = pack["pack_id"] + ":pending", pack["pack_id"] + ":linked"
        if pack["substack_url"]:
            if linked_key in started:
                continue
            platforms = list(pack["unposted_platforms"])
            note = ("The Substack page is now live: these texts carry its link."
                    if pending_key in started else None)
            results.append(send_pack(pack, bot=bot, chat_id=chat_id, desk_root=desk_root,
                                     version_key=linked_key, platforms=platforms, note=note, now=now))
        elif pending_key not in started and linked_key not in started:
            results.append(send_pack(pack, bot=bot, chat_id=chat_id, desk_root=desk_root,
                                     version_key=pending_key, platforms=list(pack["unposted_platforms"]),
                                     note="Released after 30 minutes without a confirmed Substack page.", now=now))
    return results


def serve_pulls(packs, *, bot, chat_id, desk_root, now):
    """Answer each queued /packs or Latest packs request once, newest unposted packs first."""
    root = Path(desk_root)
    served = {r.get("update_id") for r in _ledger(root) if r.get("kind") == "pull"}
    results = []
    for request in _read_jsonl(root / "inbox.jsonl"):
        if request.get("kind") != "pull" or request.get("update_id") in served:
            continue
        _append_jsonl(root / "sent.jsonl", {"kind": "pull", "update_id": request["update_id"], "at_utc": _iso(now)})
        served.add(request["update_id"])
        waiting = [p for p in packs if p["released"] and p.get("unposted_platforms")
                   and _clock(p["first_post_at_utc"]) and now - _clock(p["first_post_at_utc"]) <= PULL_WINDOW]
        if not waiting:
            from .x_reply_bot_v1 import BotError
            try:
                bot.call("sendMessage", {"chat_id": chat_id, "text": "No packs waiting: every recent pack is marked Posted."})
                results.append({"update_id": request["update_id"], "status": "NONE_WAITING"})
            except BotError as exc:
                results.append({"update_id": request["update_id"], "status": "UNCERTAIN", "cause": str(exc)})
            continue
        for pack in waiting[:MAX_PULL_PACKS]:
            results.append(send_pack(pack, bot=bot, chat_id=chat_id, desk_root=root,
                version_key=f"pull:{request['update_id']}:{pack['pack_id']}",
                platforms=pack["unposted_platforms"], note="Not yet marked Posted.", now=now))
    return results


# ------------------------------------------------------------ the bot reader

def _known_packs(desk_root):
    value = _read_json(Path(desk_root) / "packs.json", {})
    return {_short(p["pack_id"]): p for p in value.get("packs", []) if p.get("pack_id")}


def _platform_for_url(url):
    host = url.split("/")[2].casefold() if url.count("/") >= 2 else ""
    if host.endswith("x.com") or host.endswith("twitter.com"):
        return "x"
    if host.endswith("substack.com") and "/note/" in url:
        return "substack_notes"
    if host.endswith("linkedin.com"):
        return "linkedin_company"
    if host.endswith("youtube.com") or host.endswith("youtu.be"):
        return "youtube"
    return None


def is_desk_update(update):
    callback = update.get("callback_query") or {}
    if callback:
        return str(callback.get("data", "")).startswith(CALLBACK_PREFIX)
    text = str((update.get("message") or {}).get("text") or "").strip()
    return bool(re.match(r"^/packs(?:@\w+)?$", text, re.I) or text.casefold() == "latest packs"
                or (_ANY_LINK.search(text) and _platform_for_url(_ANY_LINK.search(text).group())))


def accept_update(update, *, desk_root=DESK_ROOT, now=None):
    """Record one desk update from Jim's bound private chat. The caller checks the chat first.

    Returns a short acknowledgement, or None when the update is not for the desk.
    Every write is keyed by the Telegram update id, so a re-read update changes nothing.
    """
    if not is_desk_update(update):
        return None
    now = now or utcnow()
    root = Path(desk_root)
    update_id = update.get("update_id")
    seen = {r.get("update_id") for r in _read_jsonl(root / "posted.jsonl")} | {
        r.get("update_id") for r in _read_jsonl(root / "inbox.jsonl")}
    callback = update.get("callback_query") or {}
    message = update.get("message") or {}
    data = str(callback.get("data", ""))
    if data == CALLBACK_PREFIX + "l" or (message and not _ANY_LINK.search(str(message.get("text") or ""))):
        if update_id not in seen:
            _append_jsonl(root / "inbox.jsonl", {"kind": "pull", "update_id": update_id, "at_utc": _iso(now)})
        return "Sending the packs not yet marked Posted"
    packs = _known_packs(root)
    if data.startswith(CALLBACK_PREFIX + "p:"):
        _, _, short, code = (data.split(":") + ["", ""])[:4]
        platform, pack = PLATFORM_BY_CODE.get(code), packs.get(short)
        if not platform or not pack:
            return "Pack not found"
        if update_id not in seen:
            _append_jsonl(root / "posted.jsonl", {"pack_id": pack["pack_id"], "piece_id": pack["piece_id"],
                "platform": platform, "posted_at_utc": _iso(now), "public_url": None,
                "source": "telegram_posted_button", "update_id": update_id})
        return "Recorded: posted on " + LABELS[platform]
    url = _ANY_LINK.search(str(message.get("text") or "")).group()
    platform = _platform_for_url(url)
    target = None
    reply_to = (message.get("reply_to_message") or {}).get("message_id")
    if reply_to is not None:
        for row in _ledger(root):
            if row.get("kind") == "message" and row.get("message_id") == reply_to and row.get("platform"):
                target = packs.get(_short(row["pack_id"]))
                platform = row["platform"]
                break
    if target is None and not _OWN_POST.search(url):
        return None  # a bare link to someone else's post is not a Posted mark
    if target is None:
        # A bare link to our own post: the newest pack still missing that platform's public URL.
        state = posted_state(root)
        for pack in sorted(packs.values(), key=lambda p: p.get("first_post_at_utc") or "", reverse=True):
            if pack.get("released") and not (state.get(pack["pack_id"], {}).get(platform) or {}).get("public_url"):
                target = pack
                break
    if not target or not platform:
        return None
    if update_id not in seen:
        _append_jsonl(root / "posted.jsonl", {"pack_id": target["pack_id"], "piece_id": target["piece_id"],
            "platform": platform, "posted_at_utc": _iso(now), "public_url": url,
            "source": "telegram_reply_url", "update_id": update_id})
    return "Recorded: " + LABELS[platform] + " post link"


# ------------------------------------------------------------- the minute job

def refresh_desk(store_path, *, desk_root=DESK_ROOT, binding_path=None, bot=None, now=None, send=True):
    """Build packs, write the page, push new packs and serve queued pulls. One bounded slice."""
    now = now or utcnow()
    result = {"status": "STARTED", "at_utc": _iso(now), "public_submit_actions": 0}
    packs, causes = build_packs(store_path, now=now)
    annotate(packs, desk_root=desk_root, now=now)
    write_page(packs, desk_root=desk_root, now=now)
    result.update(packs=len(packs), released=sum(p["released"] for p in packs),
                  overdue=sum(p.get("state") == "OVERDUE" for p in packs), build_causes=causes,
                  page=str(Path(desk_root) / "index.html"))
    if not send:
        result["status"] = "PAGE_WRITTEN"
        return result
    from .x_reply_bot_v1 import BINDING, BotError, TelegramBot
    binding_path = Path(binding_path or BINDING)
    if not binding_path.is_file():
        result["status"] = "PAGE_WRITTEN_BOT_NOT_CONFIGURED"
        return result
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    if not binding.get("enabled", True) or not binding.get("bound_chat_id"):
        result["status"] = "PAGE_WRITTEN_BOT_NOT_BOUND"
        return result
    bot = bot or TelegramBot()
    try:
        chat_id = bot.private_chat(binding)
    except BotError as exc:
        result.update(status="PAGE_WRITTEN_BOT_UNAVAILABLE", cause=str(exc))
        return result
    result["pushed"] = push_new(packs, bot=bot, chat_id=chat_id, desk_root=desk_root, now=now)
    result["pulls"] = serve_pulls(packs, bot=bot, chat_id=chat_id, desk_root=desk_root, now=now)
    result["status"] = "OK"
    return result


def minute_hook(store_path, *, desk_root=DESK_ROOT, binding_path=None, bot=None, now=None):
    """The minute job's entry: any desk failure is logged in the result and never raised."""
    try:
        return refresh_desk(store_path, desk_root=desk_root, binding_path=binding_path, bot=bot, now=now)
    except Exception as exc:  # the desk never stops posting
        cause = str(exc) if isinstance(exc, DeskError) else type(exc).__name__
        try:
            _append_jsonl(Path(desk_root) / "errors.jsonl", {"at_utc": _iso(utcnow()), "cause": cause})
        except OSError:
            pass
        return {"status": "DESK_FAILED", "cause": cause, "public_submit_actions": 0}
