"""A distinct plan-status obligation stays local when a new article is released."""
import json

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator


@pytest.mark.parametrize("registered,same_article,blocked", [(True, False, False), (False, False, True), (True, True, True)])
def test_plan_status_recovery_distinguishes_article_identity(tmp_path, registered, same_article, blocked):
    store = ContentOpsDurableStore(tmp_path / "state.sqlite3")
    key = "plan-status-post-controlled"
    store.create_work_item(story_id=key, work_item_id=key, title="Controlled", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    if registered:
        store.register_outbox_message(message_id=key, work_item_id=key, destination="internal:plan-status-post",
            payload=json.dumps({"schema_version": "contentops.plan_status_post.v1", "key": key, "symbol": "US500"}),
            status="EDITORIAL_INTERNAL")
    intent = {"work_item_id": key, "plan_status_post": key, "article_identity": key, "plan_hash": "a" * 64}
    evidence = [{"destination": "x", "payload": json.dumps(intent)}]
    recovery = {"backlog_remaining": 1, "backlog_remaining_obligations": [{"work_item_id": key, "destination": "x"}]}
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None, allow_prior_confirmed_distribution=True)
    before = store.list_outbox_messages()
    result = coordinator.recovery_blocks_new_publication(recovery, "new-event-preview",
        plan={"article_identity": key if same_article else "new-event-article"}, evidence_messages=evidence)
    assert result is blocked
    assert store.list_outbox_messages() == before
    assert recovery["backlog_remaining_obligations"] == [{"work_item_id": key, "destination": "x"}]
