"""Refresh this run's existing Publisher accounting; no platform or schedule calls."""
import json
from hashlib import sha256
from pathlib import Path
import sys

OPERATING = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(OPERATING))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_newsroom_volume_v1 import persist_native_day_measurement
from live_contentops.published_content_v1 import DEFAULT_FEED, read_records

ROOT = Path(__file__).resolve().parent
RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-a")
binding = json.loads((RUN / "binding.json").read_bytes())
assert binding["run_id"] == "cc124-next-article-20261105-a"
store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
operation = NativeReviewedPublication(store, binding, native_invocation_id="/root",
    rollout=json.loads((OPERATING / "config/native_desktop_rollout_v1.json").read_bytes()))
operation.validate()
operation._authorize_and_bind()
before = operation.projection()
channels = {d["destination"]: d for d in before["destinations"]}
retired = []
hashes = {"3b1cdf0585fd5e2d57cadc703b1b4834d944f80f394ef2e029088b7326addc78",
    "d5be83006bd0efe14874cb87b079c11b5614112fc83f44679d9dffdfa37a709b",
    "773c8ddb6fe5c3bfb583737e3077c37274e5a20ef23e6f4ec0f6c84e51765350"}
for request_hash in sorted(hashes):
    packet = operation.executor._get(request_hash, "request")
    request = packet["request"]
    assert not operation.executor._get(request_hash, "started")
    assert request["work_item_id"] == binding["run_id"]
    destination = request["destination"]
    current = channels[destination]
    if request["action"] == "PUBLISH":
        assert destination in {"x", "youtube"}
        assert current["status"] == "DISPATCH_CONFIRMED"
        assert current["reconciliation_status"] == "RECONCILED_CONFIRMED"
    else:
        assert destination == "linkedin" and request["action"] == "READBACK"
        assert current["status"] == "RECONCILED_ABSENT_SAFE_TO_RETRY"
        records = store.list_readbacks_for_dispatch(current["dispatch_id"])
        assert any(json.loads(r["readback_data"]).get("readback", {}).get("write_absent") is True for r in records)
    key = operation.executor._key(request_hash, "request")
    if store.get_outbox_message(key)["status"] != "NATIVE_NEO_SUPERSEDED":
        store.set_outbox_status(key, "NATIVE_NEO_SUPERSEDED")
    retired.append({"request_sha256":request_hash,"destination":destination,
        "reason":"UNCLAIMED_OLDER_REQUEST_SUPERSEDED_BY_EXACT_CURRENT_RECONCILIATION"})

day_path = Path(persist_native_day_measurement(store, binding))
day = json.loads(day_path.read_bytes())
feed = [r for r in read_records(DEFAULT_FEED) if r["content_id"] == "substack:223555673"]
assert len(feed) == 1 and feed[0]["published_at_utc"] == "2026-11-05T00:24:49.819000+00:00"
after = operation.projection()
assert not after["pending_requests"]
assert day["native_volume_measurement"]["distinct_canonical_items_published"] == 1
evidence = {"run_id":binding["run_id"],"retired_unclaimed_requests":retired,
    "canonical_feed_path":str(DEFAULT_FEED),"canonical_feed_row":feed[0],
    "production_day_path":str(day_path),"production_day_sha256":sha256(day_path.read_bytes()).hexdigest(),
    "production_day_measurement":day["native_volume_measurement"],"publication":after,
    "digest_consumer":"CC-122 reads this existing production-day record and store. The 5 Nov 07:00 run preceded this 07:24 publication; the next 07:00 digest can consume the refreshed 5 Nov record. No digest or schedule is dispatched here."}
(ROOT / "live-consumer-acceptance.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")
(ROOT / "final-publication-status-verified.json").write_text(json.dumps(after,indent=2),encoding="utf-8")
print(json.dumps({"canonical_count":len(feed),"production_day_published":day["native_volume_measurement"]["distinct_canonical_items_published"],
    "confirmed_channels":day["native_volume_measurement"]["confirmed_copies_by_channel"],"pending_requests":len(after["pending_requests"]),
    "retired_unclaimed":len(retired),"unknown_write_count":after["unknown_write_count"]}))
print(json.dumps([{"action":p["request"]["action"],"destination":p["request"]["destination"],
    "request_sha256":p["request"]["request_sha256"],"claimed":p["action_claimed"]} for p in after["pending_requests"]]))
