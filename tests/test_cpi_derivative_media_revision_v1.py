"""CC-179 isolated continuation contracts; fixtures never touch production."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_release_chart_revision_v1 import chart_revision, archive, revised  # noqa: F401
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.destination_transport_registry_v1 import registration_for_destination
from live_contentops.native_desktop_editorial_v1 import (
    build_reader_presentation_revision, reader_presentation_revision_view,
)
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from live_contentops.release_chart_revision_v1 import (
    DERIVATIVE_POLICY, SOCIAL_DESTINATIONS, derivative_missing_intent,
)


@pytest.fixture
def social(chart_revision, tmp_path, monkeypatch):  # noqa: F811
    store, run, result, proposal = chart_revision
    parent = build_reader_presentation_revision(store, run_id=run, proposal=proposal,
        owner_authority_ref="human:JIM_DECISIONS_20261030_DECISION_41_CC142")
    accepted = reader_presentation_revision_view(store, run_id=run, result=result, revision=parent)
    parent_ref = {"stage": "CONTROLLED_CANONICAL", "request_sha256": "a" * 64, "output_dir": str(tmp_path)}
    from live_contentops.native_desktop_editorial_v1 import native_review_revision
    parent_acceptance = {"article_revision": native_review_revision(accepted)}
    monkeypatch.setattr("live_contentops.native_desktop_editorial_v1.reader_presentation_acceptance",
        lambda *a, **kw: (parent, deepcopy(accepted), parent_acceptance))
    canonical_row = store.get_outbox_message(parent["objects"]["substack"]["message_id"])
    canonical = json.loads(canonical_row["payload"])
    canonical["output_dir"] = str(tmp_path / "sealed")
    Path(canonical["output_dir"]).mkdir()
    plan = {"plan_hash": canonical["plan_hash"], "destinations": [{"destination": d,
        "surface": registration_for_destination(d).surface,
        "transport_type": registration_for_destination(d).transport_type} for d in SOCIAL_DESTINATIONS]}
    (Path(canonical["output_dir"]) / "publication_lifecycle_plan_v1.json").write_text(json.dumps(plan))
    # This is an isolated fixture database, never an operational write mechanism.
    with store.get_connection() as conn:
        conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?",
            (json.dumps(canonical), canonical_row["message_id"]))
    objects, originals, missing, payloads, selections = {"substack": parent["objects"]["substack"]}, {}, {}, {}, {}
    for preview in accepted["previews"]:
        d = preview["destination"]
        ids = DurablePublicationCoordinator._ids(run, canonical["plan_hash"], d)
        original = derivative_missing_intent(canonical, d, preview["payload"])
        if d == "instagram_business":
            missing[d], originals[d] = original, None
        else:
            store.register_outbox_message(message_id=ids["message_id"], work_item_id=run, destination=d,
                payload=json.dumps(original), status="READY")
            originals[d] = sha256_of(original)
        objects[d] = {"message_id": ids["message_id"], "dispatch_id": ids["dispatch_id"], "platform": d,
            "public_object_id": None, "public_object_url": None}
        selections[d] = [accepted["media_assets"][0]["asset_id"]]
        payloads[d] = {**deepcopy(preview["payload"]), "media_asset_ids": selections[d]}
    proposal = {"policy": DERIVATIVE_POLICY, "run_id": run, "article_identity": result["article_identity"],
        "canonical_review_reference": parent_ref, "accepted_canonical_revision": parent_acceptance["article_revision"],
        "article": deepcopy(accepted["article"]), "plan_hash": canonical["plan_hash"], "objects": objects,
        "original_intent_sha256": originals, "missing_intents": missing, "payloads": payloads,
        "channel_media": selections, "amendment_writer": deepcopy(proposal["amendment_writer"])}
    proposal["amendment_writer"]["invocation_observation"]["surface"] = "CODEX_EXEC"
    response_path = Path(proposal["amendment_writer"]["response_path"])
    response = json.loads(response_path.read_bytes())
    response["channel_media"] = selections
    response_path.write_text(json.dumps(response))
    proposal["amendment_writer"]["response_sha256"] = sha256(response_path.read_bytes()).hexdigest()
    revision = build_reader_presentation_revision(store, run_id=run, proposal=proposal,
        owner_authority_ref="human:BACKLOG_CC179")
    return store, run, result, revision, parent_ref


def test_social_revision_preserves_sources_canonical_copy_and_original_intents(social):
    store, run, result, revision, _ = social
    original_rows = {r["message_id"]: r["payload"] for r in store.list_outbox_messages()}
    view = reader_presentation_revision_view(store, run_id=run, result=result, revision=revision)
    assert view["article"]["substack_body_markdown"] == revision["article"]["substack_body_markdown"]
    assert len(view["media_assets"]) == 3
    assert len(view["evidence"]) > len(result["evidence"])
    assert all(p["payload"]["media_asset_ids"] == revision["channel_media"][p["destination"]] for p in view["previews"])
    assert original_rows == {r["message_id"]: r["payload"] for r in store.list_outbox_messages()}


@pytest.mark.parametrize("fault", ["copy", "media", "target", "parent", "intent", "missing_transport", "writer"])
def test_social_revision_rejects_stale_or_unbound_material(social, fault):
    store, run, result, revision, _ = social
    bad = deepcopy(revision)
    if fault == "copy":
        bad["payloads"]["telegram"]["text"] += " Unsupported new fact."
    elif fault == "media":
        bad["channel_media"]["telegram"] = ["UNREVIEWED_ASSET"]
    elif fault == "target":
        bad["objects"]["telegram"]["message_id"] = "OTHER_ACCOUNT_OR_MESSAGE"
    elif fault == "parent":
        bad["accepted_canonical_revision"] = "f" * 64
    elif fault == "intent":
        bad["original_intent_sha256"]["telegram"] = "f" * 64
    elif fault == "missing_transport":
        bad["missing_intents"]["instagram_business"]["destination_plan"]["transport_type"] = "OTHER_ACCOUNT"
    else:
        bad["amendment_writer"]["response_sha256"] = "f" * 64
    with pytest.raises(ValueError, match="REVISION_"):
        reader_presentation_revision_view(store, run_id=run, result=result, revision=bad)


def continuation(social, monkeypatch):
    store, run, result, revision, parent_ref = social
    view = reader_presentation_revision_view(store, run_id=run, result=result, revision=revision)
    reference = {"stage": "CONTROLLED_SOCIAL_REVIEW", "request_sha256": "b" * 64}
    monkeypatch.setattr("live_contentops.native_desktop_editorial_v1.reader_presentation_acceptance",
        lambda *a, **kw: (revision, view, {"article_revision": sha256_of(view)}))
    key = "native-reader-presentation-" + sha256_of(revision["objects"]["substack"]["message_id"])
    store.register_outbox_message(message_id=key, work_item_id=run, destination="internal:native-reader-presentation",
        payload=json.dumps({"review_reference": parent_ref}), status="PRESENTATION_EDIT_CONFIRMED")
    return DurablePublicationCoordinator(store=store, transport_runtime=None), reference


def test_first_send_uses_amendment_and_repeat_does_not_repost(social, monkeypatch):
    store, run, _, revision, _ = social
    co, ref = continuation(social, monkeypatch)
    calls = []
    def dispatch(message, **kwargs):
        effective = co._effective_message(message)
        calls.append(json.loads(effective["payload"]))
        target = revision["objects"]["instagram_business"]
        store.register_platform_dispatch(**{**target, "public_object_id": "CONTROLLED_NEW_ID"}, status="DISPATCH_CONFIRMED")
        return {"status": "DISPATCH_CONFIRMED", "publish_called": True}
    monkeypatch.setattr(co, "_dispatch_message", dispatch)
    out = co.continue_reader_derivative(work_item_id=run, destination="instagram_business", review_reference=ref)
    assert out["publish_called"] is True and len(calls) == 1
    assert calls[0]["media_assets"] and calls[0]["native_payload"]["media_asset_ids"]
    assert calls[0]["reader_presentation_review"] == ref
    again = co.continue_reader_derivative(work_item_id=run, destination="instagram_business", review_reference=ref)
    assert again["publish_called"] is False and len(calls) == 1


@pytest.mark.parametrize("status", ["UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED", "NATIVE_NEO_TOOL_PENDING"])
def test_uncertain_attempt_is_readback_only_without_media_overlay(social, monkeypatch, status):
    store, run, _, revision, _ = social
    co, ref = continuation(social, monkeypatch)
    identity = revision["objects"]["linkedin"]
    store.register_platform_dispatch(**identity, status=status)
    before = store.get_outbox_message(identity["message_id"])["payload"]
    calls = []
    monkeypatch.setattr(co, "readback_existing_dispatch", lambda dispatch: calls.append(dispatch) or {"publish_called": False})
    out = co.continue_reader_derivative(work_item_id=run, destination="linkedin", review_reference=ref)
    assert out["amendment_bound"] is False and calls == [identity["dispatch_id"]]
    assert store.get_outbox_message(identity["message_id"])["payload"] == before
    assert store.get_outbox_message("native-reader-presentation-" + sha256_of(identity["message_id"])) is None


def test_confirmed_object_is_edited_and_old_absence_is_not_retried(social, monkeypatch):
    store, run, _, revision, _ = social
    co, ref = continuation(social, monkeypatch)
    identity = revision["objects"]["telegram"]
    store.register_platform_dispatch(**{**identity, "public_object_id": "CONTROLLED_EXISTING"}, status="DISPATCH_CONFIRMED")
    edits = []
    monkeypatch.setattr(co, "amend_reader_presentation", lambda dispatch, **kw: edits.append(dispatch) or {"new_post_calls": 0})
    assert co.continue_reader_derivative(work_item_id=run, destination="telegram", review_reference=ref)["new_post_calls"] == 0
    assert edits == [identity["dispatch_id"]]
    store.set_dispatch_status(identity["dispatch_id"], "RECONCILED_ABSENT_SAFE_TO_RETRY")
    assert co.continue_reader_derivative(work_item_id=run, destination="telegram", review_reference=ref)["publish_called"] is False


@pytest.mark.parametrize("claimed", [False, True])
def test_only_unclaimed_old_native_request_can_be_superseded(social, monkeypatch, tmp_path, claimed):
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
    store, run, _, revision, _ = social
    co, ref = continuation(social, monkeypatch)
    target = revision["objects"]["x"]
    store.register_platform_dispatch(**target, status="NATIVE_NEO_TOOL_PENDING")
    executor = NativeNeoExecutor(store, operation_id=run, output_dir=tmp_path, native_invocation_id="CONTROLLED")
    request_hash = "d" * 64
    key = executor._key(request_hash, "request")
    store.register_outbox_message(message_id=key, work_item_id=run, destination="internal:native-neo-tool",
        payload=json.dumps({"request": {"action": "PUBLISH", "request_sha256": request_hash}}), status="NATIVE_NEO_INTERNAL")
    monkeypatch.setattr(executor, "pending", lambda: [{"request": {"action": "PUBLISH",
        "dispatch_attempt_identity": target["dispatch_id"], "request_sha256": request_hash}, "action_claimed": claimed}])
    co.transport_runtime = SimpleNamespace(_neo_transport=SimpleNamespace(native_executor=executor))
    actions = []
    monkeypatch.setattr(co, "_dispatch_message", lambda *a, **kw: actions.append("new-revision") or {"publish_called": False})
    monkeypatch.setattr(co, "readback_existing_dispatch", lambda *a: actions.append("readback") or {"publish_called": False})
    co.continue_reader_derivative(work_item_id=run, destination="x", review_reference=ref)
    assert actions == (["readback"] if claimed else ["new-revision"])
    if not claimed:
        assert store.get_outbox_message(key)["status"] == "NATIVE_NEO_SUPERSEDED"
        with pytest.raises(ValueError, match="STALE_PUBLISH_REVISION"):
            executor.begin(request_hash)
    else:
        assert store.get_outbox_message(key)["status"] == "NATIVE_NEO_INTERNAL"


def test_unchanged_confirmed_text_is_read_back_without_an_edit(social, monkeypatch):
    store, run, _, revision, _ = social
    co, ref = continuation(social, monkeypatch)
    target = revision["objects"]["telegram"]
    store.register_platform_dispatch(**{**target, "public_object_id": "CONTROLLED_EXISTING"}, status="DISPATCH_CONFIRMED")
    message = store.get_outbox_message(target["message_id"])
    revision["payloads"]["telegram"] = json.loads(message["payload"])["native_payload"]
    actions = []
    monkeypatch.setattr(co, "readback_existing_dispatch", lambda *a: actions.append("readback") or {"publish_called": False})
    out = co.continue_reader_derivative(work_item_id=run, destination="telegram", review_reference=ref)
    assert actions == ["readback"] and out["edit_called"] is False


def test_lost_or_changed_review_cannot_bind_or_dispatch(social, monkeypatch):
    store, run, _, _, _ = social
    co, ref = continuation(social, monkeypatch)
    before = store.list_outbox_messages()
    def stale(*a, **kw):
        raise ValueError("FINAL_VISUAL_REVIEW_REVISION_CHANGED")
    monkeypatch.setattr("live_contentops.native_desktop_editorial_v1.reader_presentation_acceptance", stale)
    with pytest.raises(ValueError, match="REVISION_CHANGED"):
        co.continue_reader_derivative(work_item_id=run, destination="x", review_reference=ref)
    assert store.list_outbox_messages() == before


def test_current_unclaimed_native_request_resumes_without_superseding_itself(social, monkeypatch, tmp_path):
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
    from live_contentops.neo_destination_handoff_v1 import _payload_binding
    store, run, _, revision, _ = social
    co, ref = continuation(social, monkeypatch)
    target = revision["objects"]["x"]
    store.register_platform_dispatch(**target, status="NATIVE_NEO_TOOL_PENDING")
    executor = NativeNeoExecutor(store, operation_id=run, output_dir=tmp_path, native_invocation_id="CONTROLLED")
    current, _, _, _ = co._reader_presentation_intent(store.get_outbox_message(target["message_id"]), ref)
    payload, content = _payload_binding(current, "x")
    request_hash = "e" * 64
    key = executor._key(request_hash, "request")
    store.register_outbox_message(message_id=key, work_item_id=run, destination="internal:native-neo-tool",
        payload="{}", status="NATIVE_NEO_INTERNAL")
    monkeypatch.setattr(executor, "pending", lambda: [{"request": {"action": "PUBLISH",
        "dispatch_attempt_identity": target["dispatch_id"], "request_sha256": request_hash,
        "native_payload": payload, "content_binding": content}, "action_claimed": False}])
    co.transport_runtime = SimpleNamespace(_neo_transport=SimpleNamespace(native_executor=executor))
    actions = []
    monkeypatch.setattr(co, "_dispatch_message", lambda *a, **kw: actions.append("resume") or {"publish_called": False})
    for _ in range(2):
        co.continue_reader_derivative(work_item_id=run, destination="x", review_reference=ref)
    assert actions == ["resume", "resume"]
    assert store.get_outbox_message(key)["status"] == "NATIVE_NEO_INTERNAL"


def test_transport_resolves_current_reviewed_bytes_instead_of_old_context(tmp_path, monkeypatch):
    import live_contentops._eight_platform_substack_first_pipeline_impl_v1 as impl
    old = tmp_path / "old.png"
    new = tmp_path / "new.png"
    old.write_bytes(b"CONTROLLED_OLD"); new.write_bytes(b"CONTROLLED_NEW")
    (tmp_path / "run_context_v1.json").write_text(json.dumps({"article": {"title": "Old"},
        "media": {"assets": [{"asset_id": "old", "path": str(old)}]}}))
    monkeypatch.setattr(impl, "build_native_derivative_payloads", lambda **kw: {"telegram": {"text": "Unchanged"}})
    monkeypatch.setattr("live_contentops.v1_simple_gemini_newsroom_v1.canonical_photo_attribution_payload", lambda payload, **kw: payload)
    intent = {"output_dir": str(tmp_path), "canonical_url": "https://capitalchronicle.substack.com/p/controlled",
        "destination_plan": {"destination": "telegram"}, "reader_presentation_review": {"stage": "CONTROLLED"},
        "reader_presentation_article": {"title": "Accepted correction"},
        "media_assets": [{"asset_id": "new", "path": str(new), "sha256": sha256(new.read_bytes()).hexdigest()}],
        "native_payload": {"text": "Unchanged", "media_asset_ids": ["new"]}}
    data = impl._durable_intent_inputs(intent)
    assert data["article"]["title"] == "Accepted correction"
    assert data["local_media"] == str(new) and [a["asset_id"] for a in data["media_assets"]] == ["new"]


@pytest.mark.parametrize("destination", ["instagram_business", "threads"])
def test_reviewed_markdown_social_copy_needs_no_legacy_structured_prose(tmp_path, destination):
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
    chart = tmp_path / "accepted-chart.png"
    chart.write_bytes(b"CONTROLLED_REVIEWED_CHART")
    (tmp_path / "run_context_v1.json").write_text(json.dumps({
        "article": {"title": "Original article"}, "selection": {}, "media": {"assets": []}}))
    payload = {"text": "Reviewed dated CPI copy. https://capitalchronicle.substack.com/p/controlled",
        "media_asset_ids": ["accepted-chart"]}
    accepted_article = {"title": "Accepted correction", "substack_body_markdown": "Unchanged accepted facts."}
    intent = {"output_dir": str(tmp_path), "canonical_url": "https://capitalchronicle.substack.com/p/controlled",
        "destination_plan": {"destination": destination}, "reader_presentation_review": {"stage": "CONTROLLED"},
        "reader_presentation_article": accepted_article,
        "media_assets": [{"asset_id": "accepted-chart", "modality": "source_backed_chart", "path": str(chart)}],
        "native_payload": payload}
    before = deepcopy(intent)
    resolved = _durable_intent_inputs(intent)
    assert resolved["payloads"][destination] == payload
    assert resolved["article"] == accepted_article and resolved["selection"] == {}
    assert resolved["local_media"] == str(chart)
    assert intent == before


def test_actual_dispatch_keeps_original_intent_and_does_not_retry_absence(social, monkeypatch):
    from live_contentops.publication_coordinator_v1 import CanonicalDestinationTransportRuntimeV1
    store, run, _, revision, _ = social
    co, ref = continuation(social, monkeypatch)
    runtime = CanonicalDestinationTransportRuntimeV1(linkedin_transport=SimpleNamespace(), neo_transport=SimpleNamespace())
    calls = []
    runtime.publish = lambda **kw: calls.append(kw) or {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True}
    co.transport_runtime = runtime
    monkeypatch.setattr(co, "_readiness", lambda *a: "READY_AUTHENTICATED")
    identity = revision["objects"]["instagram_business"]
    expected = deepcopy(revision["missing_intents"]["instagram_business"])
    co.continue_reader_derivative(work_item_id=run, destination="instagram_business", review_reference=ref)
    assert len(calls) == 1 and calls[0]["intent"]["native_payload"] == revision["payloads"]["instagram_business"]
    assert json.loads(store.get_outbox_message(identity["message_id"])["payload"]) == expected
    out = co.continue_reader_derivative(work_item_id=run, destination="instagram_business", review_reference=ref)
    assert out["publish_called"] is False and len(calls) == 1


@pytest.mark.parametrize("selected_delivered", [False, True])
def test_delivery_uses_only_the_exact_reviewed_channel_asset(tmp_path, selected_delivered):
    from live_contentops._eight_platform_substack_first_pipeline_impl_v1 import _durable_intent_inputs
    selected = tmp_path / "selected.png"
    selected.write_bytes(b"CONTROLLED_SELECTED")
    digest = sha256(selected.read_bytes()).hexdigest()
    (tmp_path / "run_context_v1.json").write_text(json.dumps({"article": {}, "media": {"assets": []}}))
    other = {"media_asset_id": "other", "sha256": "a" * 64, "public_delivery_sha256": "a" * 64,
        "local_public_hash_continuity": True, "verified_public_delivery_url": "https://example.org/other.png"}
    matching = {"media_asset_id": "selected", "sha256": digest, "public_delivery_sha256": digest,
        "local_public_hash_continuity": True, "verified_public_delivery_url": "https://example.org/selected.png"}
    (tmp_path / "delivery_media_manifest_v1.json").write_text(json.dumps({
        "assets": [other] + ([matching] if selected_delivered else [])}))
    intent = {"output_dir": str(tmp_path), "canonical_url": "https://capitalchronicle.substack.com/p/controlled",
        "destination_plan": {"destination": "threads"}, "reader_presentation_review": {"stage": "CONTROLLED"},
        "reader_presentation_article": {"title": "Unchanged"},
        "media_assets": [{"asset_id": "selected", "modality": "source_backed_chart", "sha256": digest, "path": str(selected)}],
        "native_payload": {"text": "Reviewed copy.", "media_asset_ids": ["selected"]}}
    resolved = _durable_intent_inputs(intent)
    assert resolved["public_image_url"] == (matching["verified_public_delivery_url"] if selected_delivered else "")
    assert resolved["primary_media"] == (matching if selected_delivered else {})


@pytest.mark.parametrize("fault", [None, "copy", "media", "target", "origin"])
def test_exact_older_finalization_replays_without_accepting_changed_bytes(social, monkeypatch, fault):
    import live_contentops.native_desktop_editorial_v1 as editorial
    from live_contentops.publication_coordinator_v1 import CanonicalDestinationTransportRuntimeV1
    store, run, result, revision, _ = social
    parent_acceptance = editorial.reader_presentation_acceptance
    co, ref = continuation(social, monkeypatch)
    monkeypatch.setattr(co, "_dispatch_message", lambda *a, **kw: {"publish_called": False})
    co.continue_reader_derivative(work_item_id=run, destination="instagram_business", review_reference=ref)
    identity = revision["objects"]["instagram_business"]
    message = store.get_outbox_message(identity["message_id"])
    runtime = CanonicalDestinationTransportRuntimeV1(linkedin_transport=SimpleNamespace(), neo_transport=SimpleNamespace())
    finalized = runtime.finalize_intent(destination="instagram_business",
        intent=json.loads(co._effective_message(message)["payload"]),
        canonical_url=revision["objects"]["substack"]["public_object_url"])
    if fault == "copy":
        finalized["native_payload"]["text"] += " Unsupported sentence."
    elif fault == "media":
        finalized["media_assets"][0]["sha256"] = "f" * 64
    elif fault == "target":
        finalized["destination_plan"]["surface"] = "OTHER_ACCOUNT"
    elif fault == "origin":
        finalized["reader_presentation_review"] = {"stage": "UNBOUND"}
    store.finalize_outbox_payload_before_dispatch(message_id=identity["message_id"], payload=json.dumps(finalized))
    monkeypatch.setattr(editorial, "reader_presentation_acceptance", parent_acceptance)
    if fault:
        with pytest.raises(ValueError, match="ORIGINAL_INTENT_CHANGED"):
            reader_presentation_revision_view(store, run_id=run, result=result, revision=revision)
    else:
        view = reader_presentation_revision_view(store, run_id=run, result=result, revision=revision)
        assert view["article"]["substack_body_markdown"] == revision["article"]["substack_body_markdown"]
        assert view["article"]["visual_editorial_decision"]["channel_media"] == revision["channel_media"]
