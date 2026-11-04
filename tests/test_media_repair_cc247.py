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


def test_company_copy_uses_same_reviewed_media_and_pinned_identity(repair, monkeypatch):
    import json
    store, run, result, revision = repair
    view = reader_presentation_revision_view(store, run_id=run, result=result, revision=revision)
    monkeypatch.setattr("live_contentops.native_desktop_editorial_v1.reader_presentation_acceptance",
        lambda *a, **kw: (revision, view, {}))
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    co = DurablePublicationCoordinator(store=store, transport_runtime=None)
    monkeypatch.setattr(co, "_confirmed_canonical_url_for_work_item", lambda *a, **kw: revision["objects"]["substack"]["public_object_url"])
    seen = []
    def send(message, **kwargs):
        intent = json.loads(co._effective_message(message)["payload"])
        registration = co._intent_registration("linkedin_company", intent)
        seen.append((intent, registration))
        return {"publish_called": True}
    monkeypatch.setattr(co, "_dispatch_message", send)
    co.publish_reviewed_linkedin_company_copy(run_id=run, review_reference={"request_sha256": "a" * 64})
    intent, registration = seen[0]
    assert registration.expected_identity == "linkedin:company:143198922"
    assert intent["native_payload"] == revision["payloads"]["linkedin"]
    assert intent["media_assets"] == view["media_assets"]


def test_media_only_social_copy_uses_confirmed_canonical_while_its_image_edit_is_pending(repair, monkeypatch):
    import json
    store, run, result, revision = repair
    view = reader_presentation_revision_view(store, run_id=run, result=result, revision=revision)
    monkeypatch.setattr("live_contentops.native_desktop_editorial_v1.reader_presentation_acceptance",
        lambda *a, **kw: (revision, view, {}))
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    co = DurablePublicationCoordinator(store=store, transport_runtime=None)
    monkeypatch.setattr(co, "_mode", lambda: "AUTONOMOUS_DEFAULT")
    seen = []
    def send(message, **kwargs):
        seen.append(json.loads(co._effective_message(message)["payload"]))
        return {"publish_called": True}
    monkeypatch.setattr(co, "_dispatch_message", send)
    outcome = co.continue_reader_derivative(work_item_id=run, destination="discord",
        review_reference={"request_sha256": "a" * 64})
    assert outcome["publish_called"] is True
    assert seen[0]["native_payload"] == revision["payloads"]["discord"]
    assert seen[0]["media_assets"] == view["media_assets"]


@pytest.mark.parametrize("claimed", [False, True])
def test_company_replaces_only_unclaimed_exact_dispatch_from_prior_operation(repair, monkeypatch, tmp_path, claimed):
    import json
    from types import SimpleNamespace
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, DESTINATION, SCHEMA
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    store, run, result, revision = repair
    view = reader_presentation_revision_view(store, run_id=run, result=result, revision=revision)
    monkeypatch.setattr("live_contentops.native_desktop_editorial_v1.reader_presentation_acceptance",
        lambda *a, **kw: (revision, view, {}))
    co = DurablePublicationCoordinator(store=store, transport_runtime=None)
    source = store.get_outbox_message(revision["objects"]["linkedin"]["message_id"])
    ids = co._ids(run, revision["plan_hash"], "linkedin_company")
    store.register_outbox_message(message_id=ids["message_id"], work_item_id=run, destination="linkedin_company",
        payload=json.dumps({**json.loads(source["payload"]), "routine_company_copy": True,
            "company_copy_of_message_id": source["message_id"]}), status="NATIVE_NEO_TOOL_PENDING")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="linkedin_company", status="NATIVE_NEO_TOOL_PENDING")
    old = NativeNeoExecutor(store, operation_id="prior-routine-operation", output_dir=tmp_path, native_invocation_id="prior")
    current = NativeNeoExecutor(store, operation_id=run, output_dir=tmp_path, native_invocation_id="current")
    monkeypatch.setattr(current, "pending", lambda: [])
    request_hash = "d" * 64
    key = old._key(request_hash, "request")
    store.register_outbox_message(message_id=key, work_item_id=run, destination=DESTINATION,
        payload=json.dumps({"schema_version": SCHEMA, "operation_id": old.operation_id,
            "request": {"action": "PUBLISH", "request_sha256": request_hash,
                "dispatch_attempt_identity": ids["dispatch_id"], "native_payload": {"old": True}}}), status="NATIVE_NEO_INTERNAL")
    if claimed:
        old._put(request_hash, "started", {"native_invocation_id": "prior"}, run)
    co.transport_runtime = SimpleNamespace(_neo_transport=SimpleNamespace(native_executor=current))
    actions = []
    monkeypatch.setattr(co, "_dispatch_message", lambda *a, **kw: actions.append("reviewed-send") or {})
    monkeypatch.setattr(co, "readback_existing_dispatch", lambda *a: actions.append("readback") or {})
    co.publish_reviewed_linkedin_company_copy(run_id=run, review_reference={"request_sha256": "a" * 64})
    assert actions == (["readback"] if claimed else ["reviewed-send"])
    assert store.get_outbox_message(key)["status"] == ("NATIVE_NEO_INTERNAL" if claimed else "NATIVE_NEO_SUPERSEDED")
