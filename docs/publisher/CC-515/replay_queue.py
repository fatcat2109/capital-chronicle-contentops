"""Replay CC-515 settlement on a small isolated projection of the retained queue."""
from datetime import datetime, timezone
from hashlib import sha256
import gc
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from time import monotonic

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from audit_store import STORE


def replay():
    started = monotonic()
    now = datetime.now(timezone.utc)
    source = sqlite3.connect(STORE.as_uri() + "?mode=ro", uri=True, timeout=5)
    source.row_factory = sqlite3.Row
    source.execute("BEGIN")
    roots = [dict(r) for r in source.execute("SELECT * FROM outbox_messages WHERE destination=?", (posts.DESTINATION,))]
    keys = {r["message_id"] for r in roots}
    message_ids = {DurablePublicationCoordinator._ids(key,
        sha256(("plan-status-post:" + key).encode()).hexdigest(), dest)["message_id"]
        for key in keys for dest in cards.DESTINATIONS}
    selected = [dict(r) for r in source.execute("SELECT * FROM platform_dispatches")
                if r["message_id"] in message_ids]
    messages = {r["message_id"]: dict(source.execute("SELECT * FROM outbox_messages WHERE message_id=?",
                (r["message_id"],)).fetchone()) for r in selected}
    source.close()
    with tempfile.TemporaryDirectory(prefix="cc515-queue-", ignore_cleanup_errors=True) as temp:
        store = ContentOpsDurableStore(Path(temp) / "queue.sqlite3")
        for row in [*roots,*messages.values()]:
            store.create_work_item(story_id=row["work_item_id"],work_item_id=row["work_item_id"],
                title="Retained queue projection",target_surface="MULTI_PLATFORM")
            store.register_outbox_message(**{k:row[k] for k in
                ("message_id","work_item_id","destination","payload","status")})
        for row in selected:
            store.register_platform_dispatch(**{k:row[k] for k in (
                "dispatch_id","message_id","platform","status","public_object_id","public_object_url")})
        pending = [r for r in roots if r["status"] in {posts.READY,"PUBLISHING"}]
        before = {r["message_id"]:sha256(r["payload"].encode()).hexdigest() for r in roots}
        dispatches_before = store.list_platform_dispatches()
        closed = []
        for outbox in pending:
            row = json.loads(outbox["payload"])
            result = cards.settle_pending(store,outbox,row,now=now)
            if result:
                closed.append(result)
        current = store.list_outbox_messages(destination=posts.DESTINATION)
        remaining = [r for r in current if r["status"] in {posts.READY,"PUBLISHING"}]
        def older(row):
            return posts._age_minutes(json.loads(row["payload"]),now)>posts.LATE_STATE_HOURS*60
        after = {r["message_id"]:sha256(r["payload"].encode()).hexdigest() for r in current}
        assert before == after
        assert dispatches_before == store.list_platform_dispatches()
        assert not any(older(r) for r in remaining)
        result = {"observed_at_utc":now.isoformat(),"source_store_access":"sqlite mode=ro",
            "replay_store":"isolated temporary projection; no publication methods invoked",
            "pending_before":len(pending),"pending_older_than_24_hours_before":sum(older(r) for r in pending),
            "pending_after":len(remaining),"pending_older_than_24_hours_after":sum(older(r) for r in remaining),
            "closed":closed,"remaining_keys":[r["message_id"] for r in remaining],
            "all_original_payloads_identical":before==after,
            "all_dispatch_states_and_public_identities_identical":dispatches_before==store.list_platform_dispatches(),
            "source_records_deleted":0,"public_write_performed":False,"production_store_writes":0,
            "elapsed_seconds":round(monotonic()-started,3)}
        del store
        gc.collect()
    return result


if __name__ == "__main__":
    output=Path(__file__).with_name("queue-replay.json")
    result=replay()
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in {"closed","remaining_keys"}},indent=2))
