"""CC-247 feeds unchanged source-bound media into the existing live intent owner."""
from copy import deepcopy
import pytest

from test_cpi_derivative_media_revision_v1 import social, chart_revision, archive, revised  # noqa: F401
from live_contentops.native_desktop_editorial_v1 import reader_presentation_revision_view
from live_contentops.release_chart_revision_v1 import MEDIA_REPAIR_POLICY


@pytest.fixture
def repair(social, monkeypatch):
    store, run, result, prior, _ = social
    monkeypatch.setattr("live_contentops.release_chart_revision_v1.MEDIA_REPAIR_RUN_IDS", {run})
    from live_contentops.native_desktop_editorial_v1 import reader_presentation_acceptance
    _, base, _ = reader_presentation_acceptance(store, run_id=run, reference=prior["canonical_review_reference"])
    revision = deepcopy(prior)
    revision.update(policy=MEDIA_REPAIR_POLICY, owner_authority_ref="human:BACKLOG_CC247",
        media_assets=base["media_assets"])
    decision = {**base["visual_editorial_decision"], "channel_media": revision["channel_media"]}
    revision["article"] = {**base["article"], "visual_editorial_decision": decision}
    # This isolated fixture omitted Instagram's original; CC-247 repairs existing objects.
    import json
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    missing = revision["missing_intents"]["instagram_business"]
    store.register_outbox_message(message_id=revision["objects"]["instagram_business"]["message_id"],
        work_item_id=run, destination="instagram_business", payload=json.dumps(missing), status="READY")
    revision["original_intent_sha256"]["instagram_business"] = sha256_of(missing)
    return store, run, result, revision


def test_media_repair_reaches_coordinator_intent_with_exact_source_and_copy(repair, monkeypatch):
    store, run, result, revision = repair
    view = reader_presentation_revision_view(store, run_id=run, result=result, revision=revision)
    monkeypatch.setattr("live_contentops.native_desktop_editorial_v1.reader_presentation_acceptance",
        lambda *a, **kw: (revision, view, {}))
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    co = DurablePublicationCoordinator(store=store, transport_runtime=None)
    message = store.get_outbox_message(revision["objects"]["discord"]["message_id"])
    intent, *_ = co._reader_presentation_intent(message, {"request_sha256": "a" * 64})
    assert intent["native_payload"] == revision["payloads"]["discord"]
    assert intent["media_assets"] == view["media_assets"]
    assert intent["native_payload"]["media_asset_ids"] == revision["channel_media"]["discord"]
    assert view["article"]["substack_body_markdown"] == revision["article"]["substack_body_markdown"]


@pytest.mark.parametrize("fault", ["source", "article", "copy", "asset", "account", "authority"])
def test_media_repair_rejects_fact_rights_copy_or_identity_drift(repair, fault):
    store, run, result, revision = repair
    bad = deepcopy(revision)
    if fault == "source": bad["source_sha256"] = "f" * 64
    elif fault == "article": bad["article"]["substack_body_markdown"] += " New unsupported assertion."
    elif fault == "copy": bad["payloads"]["telegram"]["text"] += " New unsupported assertion."
    elif fault == "asset": bad["media_assets"][0]["sha256"] = "f" * 64
    elif fault == "account": bad["objects"]["telegram"]["message_id"] = "wrong-account"
    else: bad["owner_authority_ref"] = "human:OTHER"
    with pytest.raises(ValueError, match="MEDIA_REPAIR_"):
        reader_presentation_revision_view(store, run_id=run, result=result, revision=bad)
