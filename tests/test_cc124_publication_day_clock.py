"""A fresh readback must not turn an old publication into today's article."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import DESTINATION
from live_contentops.native_finished_publication_v1 import confirmed_canonicals
from live_contentops.native_newsroom_volume_v1 import persist_native_day_measurement, volume_policy
from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator


def test_publication_feed_clock_drives_day_and_window_counts_after_late_readback(tmp_path, monkeypatch):
    import live_contentops.published_content_v1 as feed
    store = ContentOpsDurableStore(tmp_path / "day.sqlite3")
    now = datetime.now(timezone.utc)
    day = newsroom_production_day_id(now)
    records, bindings = [], []
    for run, object_id, published in (("older", "123", now - timedelta(days=2)),
                                       ("current", "456", now)):
        work = "cc-opportunity-" + sha256_of(run)
        for identity in (run, work):
            store.create_work_item(work_item_id=identity, story_id=identity,
                title="Controlled publication clock", target_surface="TEST")
        root = tmp_path / day / "window" / run
        root.mkdir(parents=True)
        binding = {"run_id": run, "cutoff_utc": now.isoformat(), "output_dir": str(root),
            "window_id": "window", "volume_policy": volume_policy(now.isoformat())}
        bindings.append(binding)
        store.register_outbox_message(message_id="native-operation-binding-" + sha256_of(run),
            work_item_id=work, destination="internal:native-desktop-editorial",
            payload=json.dumps(binding), status="EDITORIAL_INTERNAL")
        store.register_outbox_message(message_id="prepared-" + run, work_item_id=run,
            destination=DESTINATION, payload=json.dumps({"run_id": run, "plan_hash": "plan"}),
            status="EDITORIAL_INTERNAL")
        ids = DurablePublicationCoordinator._ids(run, "plan", "substack")
        url = "https://capitalchronicle.substack.com/p/" + run
        store.register_outbox_message(message_id=ids["message_id"], work_item_id=run,
            destination="substack", payload=json.dumps({"plan_hash": "plan"}), status="DISPATCH_CONFIRMED")
        store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
            platform="substack", status="DISPATCH_CONFIRMED", public_object_id=object_id, public_object_url=url)
        store.register_reconciliation(reconciliation_id=ids["reconciliation_id"], work_item_id=run,
            status="RECONCILED_CONFIRMED")
        store.register_readback(readback_id="read-" + run, dispatch_id=ids["dispatch_id"],
            readback_data=json.dumps({"readback": {"verified": True}}))
        records.append({"content_id": "substack:" + object_id, "published_at_utc": published.isoformat(),
            "outlets": [{"name": "substack", "url": url}]})
    monkeypatch.setattr(feed, "read_records", lambda path: records)
    observed = {r["run_id"]: r for r in confirmed_canonicals(store)}
    assert newsroom_production_day_id(observed["older"]["first_readback_utc"]) == day
    assert observed["older"]["published_at_utc"] == now - timedelta(days=2)
    path = persist_native_day_measurement(store, bindings[-1])
    measurement = json.loads(Path(path).read_bytes())["native_volume_measurement"]
    assert measurement["distinct_canonical_items_published"] == 1
    assert measurement["windows"]["window"]["distinct_canonical_published"] == 1
