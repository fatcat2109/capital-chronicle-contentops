"""A confirmed canonical reaches its reader while a social write stays unknown."""
from live_contentops.published_content_v1 import read_records, utc
from live_contentops.v1_simple_publication_handoff_v1 import SimplePublicationHandoffV1
from test_publication_coordinator_v1 import FixtureTransport, _quality_plan
from test_published_content_v1 import lifecycle, ORIGINAL


def test_recovery_resume_exports_confirmed_article_once_without_republishing(tmp_path, monkeypatch):
    class Transport(FixtureTransport):
        def publish(self, *, destination, **kwargs):
            if destination == "x":
                self.publish_calls.append(destination)
                raise TimeoutError("response lost before public identity was observed")
            return super().publish(destination=destination, **kwargs)

        def readback(self, *, destination, **kwargs):
            if destination == "x":
                return {"status": "AMBIGUOUS", "verified": False}
            result = {**super().readback(destination=destination, **kwargs),
                      "published_at_utc": ORIGINAL}
            if destination == "discord":
                result["public_object_url"] = "https://discord.com/channels/111/222/333"
            return result

    store, transport, coordinator, plan, _, root = lifecycle(tmp_path, transport=Transport())
    plan.update(_quality_plan())
    feed = coordinator.published_content_path
    coordinator.published_content_path = None
    result = coordinator.execute_plan("work-1", plan)
    assert result["canonical_article_real_published"]
    coordinator.published_content_path = feed
    handoff = SimplePublicationHandoffV1(store=store, coordinator=coordinator)
    monkeypatch.setattr(handoff, "ensure_plan", lambda **_: plan)
    calls = list(transport.publish_calls)

    resumed = handoff.resume(slot_id="work-1", slot_output_dir=root)

    assert resumed["state"] == "PUBLICATION_RECOVERY_REQUIRED"
    assert resumed["published_content_record"]["status"] == "APPENDED", resumed["published_content_record"]
    rows = read_records(feed)
    assert len(rows) == 1
    assert rows[0]["content_id"] == "substack:substack-object-1"
    assert utc(rows[0]["published_at_utc"]) == utc(ORIGINAL)
    assert "x" not in {o["name"] for o in rows[0]["outlets"]}
    sealed = feed.read_bytes()
    again = handoff.resume(slot_id="work-1", slot_output_dir=root)
    assert again["published_content_record"]["status"] == "ALREADY_RECORDED"
    assert feed.read_bytes() == sealed
    assert transport.publish_calls == calls


def test_export_keeps_unknown_canonical_out_of_reader(tmp_path):
    store, _, coordinator, plan, _, _ = lifecycle(tmp_path, transport=FixtureTransport(ambiguous=True))
    coordinator.execute_plan("work-1", plan)
    assert coordinator.sync_published_content("work-1")["status"] == "CANONICAL_NOT_CONFIRMED_NO_RECORD"
    assert not coordinator.published_content_path.exists()
