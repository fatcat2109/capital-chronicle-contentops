"""Bounded acceptance replay: production backup, existing coordinator/Neo, fake tool returns."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from live_contentops.destination_transport_registry_v1 import required_derivative_destinations
from live_contentops.published_content_v1 import PRODUCTION_STORE
from test_publication_coordinator_v1 import FixtureTransport, _quality_plan, _set_mode
from live_contentops import publication_coordinator_v1 as publication


def main():
    copy_path = Path(tempfile.mkdtemp(prefix="cc431-copied-store-")) / "copied.sqlite3"
    with sqlite3.connect(f"file:{PRODUCTION_STORE}?mode=ro", uri=True) as source, sqlite3.connect(copy_path) as target:
        source.backup(target)
    store = ContentOpsDurableStore(copy_path, auto_migrate=False)
    work = "cc431-copied-store-seven-derivatives"
    store.create_work_item(story_id=work, work_item_id=work, title="CC-431 controlled acceptance replay",
                           target_surface="MULTI_PLATFORM")
    requests = []
    def observed(request):
        assert request["destination"] == "x"
        requests.append({k: request.get(k) for k in ("destination", "action", "request_sha256", "surface")})
        return {"status": "SUCCESS", "request_sha256": request["request_sha256"],
            "observed_identity": "@Capitalnicle", "authenticated": True,
            "public_object_id": "4310000000000000000",
            "public_object_url": "https://x.com/Capitalnicle/status/4310000000000000000",
            "observed_text": "\n".join(request["content_binding"]["expected_text_segments"]),
            "observed_media_sha256": [], "content_verified": True, "verified": True, "write_exists": True}
    class Runtime(FixtureTransport):
        def __init__(self):
            super().__init__()
            self._neo_transport = NeoDestinationHandoff(native_executor=observed, store=store)
        def publish(self, **kwargs):
            if kwargs["destination"] != "x":
                return super().publish(**kwargs)
            self.publish_calls.append("x")
            return self._neo_transport.publish(**kwargs)
        def readback(self, **kwargs):
            if kwargs["destination"] != "x":
                return super().readback(**kwargs)
            self.readback_calls.append("x")
            return self._neo_transport.readback(**kwargs)
    runtime = Runtime()
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda destination: {"readiness_state": "READY_AUTHENTICATED", "identity_match": True})
    plan = _quality_plan()
    for item in plan["destinations"]:
        item["payload"] = item["payload"].replace("/p/test", "/p/fixture-article-1")
        item["payload_hash"] = hashlib.sha256(item["payload"].encode()).hexdigest()
    plan.update(story_identity=work, article_identity=work, package_identity=work)
    plan["plan_hash"] = hashlib.sha256(work.encode()).hexdigest()
    coordinator.recovery_scope = {"work_item_id": work, "plan": plan, "exact_work_item_only": True}
    _set_mode(store, "AUTONOMOUS_DEFAULT")
    # Keep the copied incidents intact. Controlled delivery takes place on the
    # next ET day, beyond the real day's destination failure cooldowns.
    class ReplayClock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 11, 11, 12, tzinfo=timezone.utc)
    publication.datetime = ReplayClock
    result = coordinator.execute_plan(work, plan)
    state = coordinator.publication_state(work, plan)
    assert state["derivative_confirmed_count"] == 7 and not state["recovery_required_destinations"], state
    assert not state["readback_limitation_destinations"], state
    assert [r["action"] for r in requests] == ["PUBLISH", "READBACK"]
    before = list(runtime.publish_calls)
    coordinator.execute_plan(work, plan)
    assert runtime.publish_calls == before
    output = {"store_copy": str(copy_path), "source": str(PRODUCTION_STORE),
        "method": "Read-only SQLite backup; real coordinator and NeoDestinationHandoff; controlled tool returns",
        "simulated_clock_utc": "2026-11-11T12:00:00Z",
        "required_derivatives": list(required_derivative_destinations()),
        "confirmed_count": state["derivative_confirmed_count"], "distribution_status": state["distribution_status"],
        "x_requests": requests, "publish_calls": runtime.publish_calls,
        "duplicate_resume_created_no_write": runtime.publish_calls == before,
        "source_store_mutated": False, "external_calls": 0, "live_publication_proof": False}
    (Path(__file__).parent / "copied-store-seven-replay.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=1))


if __name__ == "__main__":
    main()
