"""Read-only Substack draft inventory and the existing store's draft scan scope.

No browser, authentication, draft mutation, or publication lives here. The inventory
consumes allowlisted metadata captured through Neo, separately from routine readback.
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import urlsplit

HOST = "capitalchronicle.substack.com"
ID_KEYS = {"draft_id", "public_object_id", "observed_public_object_id"}
URL_KEYS = {"draft_url", "public_object_url", "observed_public_object_url", "url"}


def draft_id_from_url(url):
    parsed = urlsplit(str(url or ""))
    if parsed.scheme != "https" or parsed.hostname != HOST:
        return None
    match = re.fullmatch(r"/publish/(?:post/|posts/detail/)(\d+)(?:/.*)?", parsed.path)
    return match[1] if match else None


def _ids(value):
    """Explicit object identities only; titles, body text and generic ids are not refs."""
    result = set()
    if isinstance(value, dict):
        if value.get("destination") not in {None, "substack"}:
            return result
        for key, item in value.items():
            if key in ID_KEYS and str(item or "").isdigit():
                result.add(str(item))
            elif key in URL_KEYS:
                if draft_id := draft_id_from_url(item):
                    result.add(draft_id)
            elif isinstance(item, (dict, list)):
                result.update(_ids(item))
    elif isinstance(value, list):
        for item in value:
            result.update(_ids(item))
    return result


def referenced_draft_ids(connection):
    """Query one SQLite snapshot. Missing/broken schema raises, never marks all old."""
    result = set()
    for object_id, url in connection.execute(
        "SELECT public_object_id,public_object_url FROM platform_dispatches WHERE platform='substack'"
    ):
        result.update(_ids({"public_object_id": object_id, "public_object_url": url}))
    for (payload,) in connection.execute("SELECT payload FROM outbox_messages WHERE destination='substack'"):
        result.update(_ids(json.loads(payload)))
    for (payload,) in connection.execute(
        "SELECT r.readback_data FROM readbacks r JOIN platform_dispatches d USING(dispatch_id) "
        "WHERE d.platform='substack'"
    ):
        result.update(_ids(json.loads(payload)))
    # An interrupted publish can retain its draft id in the existing native outbox
    # before the coordinator has copied it into platform_dispatches.
    native = [json.loads(row[0]) for row in connection.execute(
        "SELECT payload FROM outbox_messages WHERE destination='internal:native-neo-tool'"
    )]
    substack_requests = set()
    for row in native:
        request = row.get("request", {})
        if request.get("destination") == "substack":
            substack_requests.update({row.get("tool_request_sha256"), request.get("request_sha256")})
    substack_requests.discard(None)
    for row in native:
        request = row.get("request", {})
        response = row.get("result", {})
        if request.get("destination") == "substack":
            result.update(_ids(request))
        if (response.get("observed_identity") == HOST
                or row.get("tool_request_sha256") in substack_requests
                or response.get("request_sha256") in substack_requests):
            result.update(_ids(row))
    return result


def store_draft_ids(store):
    with closing(store.get_read_only_connection()) as connection:
        connection.execute("BEGIN")
        return referenced_draft_ids(connection)


def filter_referenced_drafts(drafts, referenced_ids):
    """A normal scan never opens an unreferenced draft, even with a matching title."""
    return [row for row in drafts if str(row.get("id") or row.get("draft_id") or "") in referenced_ids]


def readback_scope(referenced_ids):
    ids = sorted(referenced_ids)
    return {
        "referenced_draft_ids": ids,
        "draft_urls": [f"https://{HOST}/publish/post/{draft_id}" for draft_id in ids],
        "scan_unreferenced_drafts": False,
        "instructions": "Use exact public object first. Any draft fallback or scan considers only "
                        "referenced_draft_ids; never enumerate all drafts or open an unreferenced "
                        "draft, even if its title matches. Do not edit or delete drafts. An ignored "
                        "draft is not proof of public-write absence; preserve UNKNOWN_WRITE.",
    }


def inventory_rows(batches):
    """Require complete, uncapped pagination without duplicate or published objects."""
    ordered = sorted(batches, key=lambda row: row["offset"])
    if not ordered:
        raise ValueError("DRAFT_INVENTORY_NO_PAGES")
    total = ordered[0]["total"]
    rows, seen = [], set()
    for batch in ordered:
        if batch.get("isCapped") or batch["total"] != total or batch["offset"] != len(rows):
            raise ValueError("DRAFT_INVENTORY_INCOMPLETE_OR_CHANGED")
        for row in batch["rows"]:
            draft_id = str(row["id"])
            if not draft_id.isdigit() or draft_id in seen or row.get("is_published") is not False:
                raise ValueError("DRAFT_INVENTORY_DUPLICATE_OR_NOT_DRAFT")
            seen.add(draft_id)
            rows.append(row)
    if len(rows) != total:
        raise ValueError("DRAFT_INVENTORY_INCOMPLETE_OR_CHANGED")
    return rows


def write_inventory(*, batches, store_path, output_path):
    rows = inventory_rows(batches)
    with closing(sqlite3.connect(Path(store_path).resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        references = referenced_draft_ids(connection)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=["draft_id", "title", "created_at_utc",
            "last_edited_at_utc", "store_referenced", "classification"])
        writer.writeheader()
        for row in rows:
            referenced = str(row["id"]) in references
            writer.writerow({"draft_id": row["id"], "title": row["title"],
                "created_at_utc": row.get("created_at") or "",
                "last_edited_at_utc": row.get("last_edited_at") or "",
                "store_referenced": str(referenced).lower(),
                "classification": "STORE_REFERENCED" if referenced else "OLD_UNREFERENCED"})
    referenced_count = len(filter_referenced_drafts(rows, references))
    return {"total_drafts": len(rows), "store_referenced": referenced_count,
            "old_unreferenced": len(rows) - referenced_count, "csv_path": str(output.resolve()),
            "store_path": str(Path(store_path).resolve()), "store_reference_ids": sorted(references),
            "missing_created_at": sum(not row.get("created_at") for row in rows),
            "missing_last_edited_at": sum(not row.get("last_edited_at") for row in rows),
            "draft_mutations": 0}
