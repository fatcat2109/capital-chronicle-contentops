"""CC-135: sealed, append-only publication snapshots for the CC-014 reader.

The existing coordinator/store remain publication authority. This file is an
export of confirmed objects, never a second queue, publisher or recovery owner.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlsplit

from live_contentops.event_article_guard_v1 import (
    PUBLIC_NOTICE, check_publication_copy,
)

SCHEMA = "contentops.published_content.v1"
RUNTIME_ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
PRODUCTION_STORE = RUNTIME_ROOT / "contentops_daily_app_v1.sqlite3"
DEFAULT_FEED = RUNTIME_ROOT / "published_content_v1.jsonl"
TYPES = frozenset({"ARTICLE", "EVENT_PREVIEW", "EVENT_REVIEW", "DESK_NOTE"})
PUBLIC_RIGHTS = frozenset({"CC_OWN_ANALYSIS", "PUBLIC_FACT_IDENTITY"})
# Public link metadata observed through the existing webhook GET on 3 Nov 2026.
# The registry still owns the channel identity; a changed channel fails closed.
DISCORD_LINK_PREFIX = "https://discord.com/channels/1519310996030750782/1519311669216673802/"
KEYS = {"schema_version", "content_id", "type", "title", "standfirst", "published_at_utc",
        "recorded_at_utc", "outlets", "event_id", "conditional_calls", "rights_class",
        "visibility", "disclaimer", "conflicts_notice", "content_sha256"}


class PublishedContentError(ValueError):
    """Fixed diagnostics only; rejected private copy is never echoed."""


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PublishedContentError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _nonfinite(_value):
    raise PublishedContentError("NONFINITE_JSON_VALUE")


def load_json(raw):
    return json.loads(raw, object_pairs_hook=_object, parse_constant=_nonfinite)


def utc(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
            raise ValueError
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError, OverflowError) as exc:
        raise PublishedContentError("EXPLICIT_UTC_CLOCK_REQUIRED") from exc


def _https(value):
    if not isinstance(value, str) or any(c.isspace() for c in value):
        return False
    try:
        url = urlsplit(value)
        return (url.scheme == "https" and bool(url.hostname) and not url.username
                and not url.password and not url.query and not url.fragment)
    except ValueError:
        return False


def validate_record(row):
    if (not isinstance(row, dict) or set(row) != KEYS
            or row.get("schema_version") != SCHEMA or not isinstance(row.get("type"), str)
            or row["type"] not in TYPES):
        raise PublishedContentError("PUBLICATION_RECORD_SCHEMA_INVALID")
    for key in ("content_id", "title", "standfirst", "rights_class"):
        if not isinstance(row[key], str) or not row[key].strip():
            raise PublishedContentError("PUBLICATION_RECORD_TEXT_REQUIRED")
    if row["rights_class"] not in PUBLIC_RIGHTS or row["visibility"] != "public":
        raise PublishedContentError("PUBLIC_REUSE_RIGHTS_NOT_ADMITTED")
    if utc(row["recorded_at_utc"]) < utc(row["published_at_utc"]):
        raise PublishedContentError("RECORDING_PRECEDES_PUBLICATION")
    if row["event_id"] is not None and (not isinstance(row["event_id"], str) or not row["event_id"].strip()):
        raise PublishedContentError("EVENT_ID_INVALID")
    outlets = row["outlets"]
    if not isinstance(outlets, list) or not outlets:
        raise PublishedContentError("CONFIRMED_OUTLETS_REQUIRED")
    names, urls = set(), set()
    for outlet in outlets:
        if (not isinstance(outlet, dict) or set(outlet) != {"name", "url"}
                or not isinstance(outlet["name"], str) or not outlet["name"].strip()
                or not _https(outlet["url"])):
            raise PublishedContentError("OUTLET_IDENTITY_INVALID")
        if outlet["name"] in names or outlet["url"] in urls:
            raise PublishedContentError("DUPLICATE_OUTLET")
        names.add(outlet["name"])
        urls.add(outlet["url"])
    substack = next((o["url"] for o in outlets if o["name"] == "substack"), None)
    from live_contentops.published_corpus_read_model_v1 import _valid_canonical_substack_url
    if not _valid_canonical_substack_url(substack):
        raise PublishedContentError("CONFIRMED_CANONICAL_REQUIRED")
    check_publication_copy({k: row[k] for k in ("title", "standfirst", "disclaimer", "conflicts_notice")},
                           conditional_calls=row["conditional_calls"], require_call_text=False)
    content = {k: v for k, v in row.items() if k != "content_sha256"}
    if (not re.fullmatch(r"[0-9a-f]{64}", str(row["content_sha256"]))
            or sha256(canonical(content)).hexdigest() != row["content_sha256"]):
        raise PublishedContentError("PUBLICATION_SEAL_MISMATCH")
    return row


def _records(raw):
    if raw and not raw.endswith(b"\n"):
        raise PublishedContentError("TORN_FEED_TAIL_READBACK_REQUIRED")
    rows, identities, canonicals = [], set(), set()
    for line in raw.splitlines():
        if not line.strip():
            raise PublishedContentError("EMPTY_FEED_LINE")
        row = validate_record(load_json(line))
        url = next(o["url"] for o in row["outlets"] if o["name"] == "substack")
        if row["content_id"] in identities or url in canonicals:
            raise PublishedContentError("DUPLICATE_PUBLISHED_PIECE")
        identities.add(row["content_id"])
        canonicals.add(url)
        rows.append(row)
    return rows


def read_records(path):
    return _records(Path(path).read_bytes())


@contextmanager
def _locked_feed(path):
    """Lock the feed itself, with no side ledger, waiting loop or background job."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as handle:
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise PublishedContentError("PUBLISHED_FEED_BUSY") from exc
        try:
            yield handle
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def append_record(path, row):
    validate_record(row)
    with _locked_feed(path) as handle:
        existing = _records(handle.read())
        url = next(o["url"] for o in row["outlets"] if o["name"] == "substack")
        for prior in existing:
            prior_url = next(o["url"] for o in prior["outlets"] if o["name"] == "substack")
            if prior["content_id"] == row["content_id"] or prior_url == url:
                # Outlets are a first-recording snapshot. Later recovery never
                # rewrites it, or pretends a new outlet was in the original seal.
                ignore = {"outlets", "recorded_at_utc", "content_sha256"}
                if prior_url != url or {k: v for k, v in prior.items() if k not in ignore} != {
                        k: v for k, v in row.items() if k not in ignore}:
                    raise PublishedContentError("SEALED_PUBLICATION_IDENTITY_CONFLICT")
                return {"status": "ALREADY_RECORDED", "content_id": prior["content_id"],
                        "content_sha256": prior["content_sha256"], "outlet_count": len(prior["outlets"])}
        handle.seek(0, os.SEEK_END)
        data = canonical(row) + b"\n"
        if handle.write(data) != len(data):
            raise PublishedContentError("FEED_APPEND_INCOMPLETE_READBACK_REQUIRED")
        handle.flush()
        os.fsync(handle.fileno())
    return {"status": "APPENDED", "content_id": row["content_id"],
            "content_sha256": row["content_sha256"], "outlet_count": len(row["outlets"])}


def article_metadata(plan, *, require_notice=True):
    """Use the exact reviewed compiler artifact, never a model-authored export."""
    root = Path(plan.get("output_dir") or "")
    article = load_json((root / "article_manifest_v1.json").read_bytes())
    event = article.get("event_article_packet") or {}
    calls = article.get("conditional_calls", event.get("conditional_calls", []))
    from live_contentops.v1_simple_gemini_newsroom_v1 import _public_copy
    if sha256(_public_copy(article).encode()).hexdigest() != plan.get("article_content_sha256"):
        raise PublishedContentError("EXACT_REVIEWED_ARTICLE_HASH_REQUIRED")
    check_publication_copy({"title": article.get("title"), "standfirst": article.get("dek"),
                            "body": article.get("substack_body_markdown")},
                           conditional_calls=calls, require_notice=require_notice)
    kind = article.get("article_type") or event.get("article_type") or "ARTICLE"
    if kind not in TYPES:
        raise PublishedContentError("PUBLICATION_TYPE_INVALID")
    rights = article.get("rights_class")
    if rights is None and article.get("author_identity") == article.get("publisher_identity") == "Capital Chronicle":
        # Rights to CC's original prose, not a new licence to any source series.
        rights = "CC_OWN_ANALYSIS"
    if not isinstance(rights, str) or rights not in PUBLIC_RIGHTS:
        raise PublishedContentError("PUBLIC_REUSE_RIGHTS_NOT_ADMITTED")
    from live_contentops.event_article_guard_v1 import CONFLICTS_NOTICE
    return {"type": kind, "title": article["title"], "standfirst": article.get("dek") or article.get("subtitle"),
            "event_id": article.get("event_id") or event.get("event_id"),
            "conditional_calls": calls, "rights_class": rights,
            "disclaimer": PUBLIC_NOTICE, "conflicts_notice": CONFLICTS_NOTICE if calls else None}


def record_from_corpus(article, metadata, *, published_at_utc, recorded_at_utc, outlet_urls=None):
    """The strict existing corpus proves each outlet; URL enrichment cannot add one."""
    from live_contentops.published_corpus_read_model_v1 import is_countable_canonical_published_article
    if not is_countable_canonical_published_article(article):
        raise PublishedContentError("EXACT_CANONICAL_RECONCILIATION_REQUIRED")
    outlets = []
    for obj in article.derivative_public_objects:
        name = obj["destination"]
        url = obj["public_object_url"] or (outlet_urls or {}).get(name)
        if not obj["public_object_url"] and name == "discord":
            from live_contentops.destination_transport_registry_v1 import registration_for_destination
            channel = registration_for_destination("discord").expected_stable_id
            prefix = DISCORD_LINK_PREFIX if f"/{channel}/" in DISCORD_LINK_PREFIX else None
            expected = prefix + obj["public_object_id"] if prefix and str(obj["public_object_id"]).isdigit() else None
            if url and url != expected:
                raise PublishedContentError("CONFIRMED_OUTLET_URL_IDENTITY_MISMATCH")
            url = expected
        if not url:
            raise PublishedContentError("CONFIRMED_OUTLET_URL_REQUIRED:" + name)
        outlets.append({"name": name, "url": url})
    row = {"schema_version": SCHEMA, "content_id": "substack:" + article.public_object_id,
           **metadata, "published_at_utc": published_at_utc, "recorded_at_utc": recorded_at_utc,
           "visibility": "public", "outlets": sorted(outlets, key=lambda o: (o["name"] != "substack", o["name"]))}
    row["content_sha256"] = sha256(canonical(row)).hexdigest()
    return validate_record(row)


def sync_confirmed_piece(store, path, work_item_id, *, recorded_at_utc=None, original=None):
    """Project one confirmed piece; UNKNOWN_WRITE never becomes a record."""
    from live_contentops.published_corpus_read_model_v1 import load_published_corpus
    corpus = load_published_corpus(store)
    article = next((a for a in corpus["articles"] if a.source_work_item_id == work_item_id), None)
    if article is None:
        return {"status": "CANONICAL_NOT_CONFIRMED_NO_RECORD"}
    with store.get_read_only_connection() as conn:
        row = conn.execute("SELECT m.payload,d.dispatch_id FROM platform_dispatches d "
            "JOIN outbox_messages m ON m.message_id=d.message_id WHERE d.platform='substack' "
            "AND d.public_object_id=? AND m.work_item_id=?", (article.public_object_id, work_item_id)).fetchone()
        intent = load_json(row["payload"])
        readbacks = conn.execute("SELECT readback_data FROM readbacks WHERE dispatch_id=? ORDER BY read_at",
                                 (row["dispatch_id"],)).fetchall()
    metadata = article_metadata(intent, require_notice=False)
    if Path(path).is_file():
        for prior in read_records(path):
            if prior["content_id"] == "substack:" + article.public_object_id:
                if any(prior[k] != value for k, value in metadata.items()):
                    raise PublishedContentError("SEALED_PUBLICATION_IDENTITY_CONFLICT")
                return {"status": "ALREADY_RECORDED", "content_id": prior["content_id"],
                        "content_sha256": prior["content_sha256"], "outlet_count": len(prior["outlets"])}
    original = original or {}
    if original and (original.get("canonical_url") != article.canonical_url
                     or original.get("public_object_id") != article.public_object_id):
        raise PublishedContentError("ORIGINAL_PUBLICATION_OBSERVATION_IDENTITY_MISMATCH")
    published = original.get("published_at_utc")
    if not published:
        for readback in readbacks:
            proof = load_json(readback["readback_data"]).get("readback", {})
            if proof.get("verified") is True and proof.get("observed_published_at_utc"):
                published = proof["observed_published_at_utc"]
                break
    if not published:
        raise PublishedContentError("ORIGINAL_PUBLICATION_CLOCK_READBACK_REQUIRED")
    record = record_from_corpus(article, metadata, published_at_utc=published,
        recorded_at_utc=recorded_at_utc or datetime.now(timezone.utc).isoformat(),
        outlet_urls=original.get("outlet_urls"))
    return append_record(path, record)
