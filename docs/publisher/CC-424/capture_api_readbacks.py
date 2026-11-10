"""One bounded CC-424 observation; reads existing exact objects and never sends.

Run from the Publisher checkout. Only selected public evidence fields leave the
existing adapters. Credentials stay with their existing secret owner.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

WORK_ITEMS = (
    "cc338-cpi-preview-20261110-v1",
    "plan-status-post-c51f9acb2106e2410ebdadb5b1da39c4",
    "plan-result-post-5cedcd8aef91e5ceec503ff30b81f946",
)
API_DESTINATIONS = {"discord", "facebook_page", "instagram_business", "threads"}
PUBLIC_FIELDS = {
    "status", "verified", "platform", "post_id", "media_id", "public_url",
    "public_object_id", "body_text_visible", "visible_body_text",
    "account_identity_verified", "destination_identity", "substack_url_visible",
    "canonical_url_exact", "canonical_link_visible", "meaningful_media_visible",
    "media_verified", "image_hash_match", "visual_similarity",
    "visual_similarity_to_expected", "parent_verified", "error_class",
    "write_absent", "write_exists", "text_verified", "media_visible",
}


def observe(row):
    # This router performs GET readbacks for these four API destinations only.
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import (
        _readback_one_destination_from_durable_intent,
    )

    intent = json.loads(row["payload"])
    start = datetime.now(timezone.utc).isoformat()
    try:
        value = _readback_one_destination_from_durable_intent(
            destination=row["destination"], public_object_id=row["public_object_id"],
            public_object_url=row["public_object_url"], intent=intent,
        )
        observed = {k: v for k, v in value.items() if k in PUBLIC_FIELDS}
    except Exception as error:
        # Exception messages can contain credential-bearing URLs; keep class only.
        observed = {"status": "READBACK_EXCEPTION", "error_class": type(error).__name__}
    return {
        "work_item_id": row["work_item_id"], "destination": row["destination"],
        "object_id": row["public_object_id"], "recorded_url": row["public_object_url"],
        "dispatch_status": row["dispatch_status"], "dispatched_at_utc": row["dispatched_at"],
        "observed_start_utc": start,
        "observed_end_utc": datetime.now(timezone.utc).isoformat(),
        "expected_public_text": intent.get("native_payload", {}).get("text", ""),
        "observation": observed,
    }


def main():
    connection = sqlite3.connect(
        "file:A:/Capital Chronicle/Runtime/ContentOps/contentops_daily_app_v1.sqlite3?mode=ro",
        uri=True, timeout=3,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    jobs = []
    dispatches = []
    for work_item in WORK_ITEMS:
        rows = connection.execute(
            "SELECT o.work_item_id,o.destination,o.status,d.status dispatch_status,"
            "d.public_object_id,d.public_object_url,d.dispatched_at,o.payload "
            "FROM outbox_messages o JOIN platform_dispatches d ON o.message_id=d.message_id "
            "WHERE o.work_item_id=? ORDER BY d.rowid", (work_item,),
        ).fetchall()
        for row in rows:
            dispatches.append({k: row[k] for k in row.keys() if k != "payload"})
            if row["destination"] in API_DESTINATIONS and row["public_object_id"]:
                jobs.append(dict(row))
    connection.close()
    # Independent network reads; no pytest, no model calls, no background worker.
    with ThreadPoolExecutor(max_workers=4) as pool:
        observations = list(pool.map(observe, jobs))
    result = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "store_open_mode": "ro; PRAGMA query_only=ON", "publication_calls": 0,
        "api_destination_allowlist": sorted(API_DESTINATIONS),
        "x_readback": "X_API_READBACK_UNAVAILABLE; CC-424 forbids a browser read",
        "linkedin_readback": "NO_CONFIRMED_LINKEDIN_OBJECT_ID; retained definite no-write, not a new attempt",
        "dispatches": dispatches, "observations": observations,
    }
    output = Path(__file__).with_name("api-readbacks.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"artifact": str(output), "observations": len(observations),
        "results": [{"work_item_id": r["work_item_id"], "destination": r["destination"],
            "status": r["observation"].get("status"), "verified": r["observation"].get("verified")}
            for r in observations]}))


if __name__ == "__main__":
    main()
