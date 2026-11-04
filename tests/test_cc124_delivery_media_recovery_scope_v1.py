"""Delivery of a distinct article must not retry or inherit an older unknown post."""
import pytest

from test_publication_coordinator_v1 import (
    FixtureTransport, _coordinator, _plan, _quality_plan,
    DISPATCH_CONFIRMED, RECONCILED_CONFIRMED, UNKNOWN_WRITE,
)


@pytest.mark.parametrize("unknown_scope", [
    "same_article_linkedin", "other_article_instagram", "same_article_instagram",
])
def test_delivery_consumer_uses_media_while_exact_unknown_stays_unretried(tmp_path, unknown_scope):
    unknown_work = "old-work" if unknown_scope == "other_article_instagram" else "work-1"
    unknown_destination = "linkedin" if unknown_scope == "same_article_linkedin" else "instagram_business"

    class Transport(FixtureTransport):
        def __init__(self):
            super().__init__()
            self.prepare_calls = []

        def prepare_delivery_media(self, **kwargs):
            self.prepare_calls.append(kwargs)
            return {"status": "CLOUDINARY_DELIVERY_MEDIA_READY"}

        def readback(self, *, destination, intent, **kwargs):
            if destination == unknown_destination and intent["work_item_id"] == unknown_work:
                return {"status": "AMBIGUOUS", "verified": False}
            return super().readback(destination=destination, intent=intent, **kwargs)

    transport = Transport()
    store, _, coordinator = _coordinator(tmp_path, runtime=transport)
    plan = _quality_plan()
    next(r for r in plan["destinations"] if r["destination"] == "instagram_business")["delivery_media_required"] = True
    registered = coordinator.register_plan("work-1", plan)["registered"]
    canonical = next(r for r in registered if r["destination"] == "substack")
    store.register_platform_dispatch(
        dispatch_id=canonical["dispatch_id"], message_id=canonical["message_id"],
        platform="substack", status=DISPATCH_CONFIRMED,
        public_object_id="canonical-object", public_object_url="https://capitalchronicle.substack.com/p/cc124-test",
    )
    store.set_outbox_status(canonical["message_id"], DISPATCH_CONFIRMED)
    store.register_reconciliation(reconciliation_id=canonical["reconciliation_id"],
                                  work_item_id="work-1", status=RECONCILED_CONFIRMED)
    if unknown_work == "old-work":
        store.create_work_item(story_id="old-story", title="Old distinct article",
            target_surface="MULTI_PLATFORM", work_item_id=unknown_work,
            actor_ref="controlled_test", correlation_id="old-correlation")
        unknown = coordinator.register_plan(unknown_work, _plan(unknown_destination))["registered"][0]
    else:
        unknown = next(r for r in registered if r["destination"] == unknown_destination)
    store.register_platform_dispatch(dispatch_id=unknown["dispatch_id"],
        message_id=unknown["message_id"], platform=unknown_destination, status=UNKNOWN_WRITE)
    store.set_outbox_status(unknown["message_id"], UNKNOWN_WRITE)

    coordinator.recover_pending()

    assert store.get_platform_dispatch(unknown["dispatch_id"])["status"] == UNKNOWN_WRITE
    if unknown_scope == "same_article_instagram":
        assert "instagram_business" not in transport.publish_calls
    else:
        assert "instagram_business" in transport.publish_calls
        assert transport.prepare_calls[0]["work_item_id"] == "work-1"
        assert transport.prepare_calls[0]["preconditions"]["unknown_write_count"] == 0
        current = next(r for r in registered if r["destination"] == "instagram_business")
        assert store.get_platform_dispatch(current["dispatch_id"])["status"] == DISPATCH_CONFIRMED
    if unknown_destination == "linkedin":
        assert "linkedin" not in transport.publish_calls
