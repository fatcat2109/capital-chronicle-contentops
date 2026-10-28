"""Isolated public-edit contracts; synthetic responses prove no real visual inspection."""
from copy import deepcopy
from hashlib import sha256
import json

from PIL import Image
import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import (
    build_reader_presentation_revision, reader_presentation_revision_view, reader_presentation_acceptance,
    NativeDesktopTurn, DesktopInputRequired, final_visual_binding, request_final_visual_review,
    FINAL_VISUAL_LAYOUT_CHECKS,
)
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, NativeNeoInputRequired
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator


@pytest.fixture
def revised(tmp_path, monkeypatch):
    store = ContentOpsDurableStore(tmp_path / "CONTROLLED.sqlite3")
    run = "controlled-reader-revision"
    store.create_work_item(story_id=run, work_item_id=run, title="CONTROLLED", target_surface="TEST")
    control = store.get_operating_control()
    store.update_operating_control(operating_mode="AUTONOMOUS_DEFAULT",
        expected_state_version=control["state_version"], control_source="CONTROLLED_TEST")
    date, label = "21 October 2026", "Reporting as of 21:00 Bangkok on 21 October 2026."
    body = "FirstSquawk, citing WSJ, reports a possible effort; no agreement is confirmed. [[SOURCE:SOURCE_1]]"
    suffix = "\n\n### Sources\n\n" + label + " [FirstSquawk](https://x.com/controlled)."
    channels = ["telegram", "discord", "x", "linkedin", "facebook_page", "instagram_business", "threads", "youtube"]
    result = {"article_identity": sha256_of(run), "qualified_article_count": 1,
        "model_execution_state": "NATIVE_DESKTOP_REQUEST_RETURN",
        "article": {"title": "Controlled attributed report", "dek": "Unconfirmed report.",
            "reader_first_version": "DATA_JOURNALISM_V1", "display_date": date + " | Reporting as of 21:00 Bangkok",
            "substack_body_markdown": body + suffix,
            "public_source_bindings": [{"source_id": "SOURCE_1", "publisher": "FirstSquawk", "url": "https://x.com/controlled"}]},
        "evidence": [{"source_id": "SOURCE_1", "canonical_content_sha256": sha256_of("CONTROLLED evidence")}],
        "media_assets": [], "previews": [{"destination": d, "payload": {"text": "Controlled report."}} for d in channels],
        "simple_result": {"run_id": run, "cutoff_utc": "2026-10-21T14:00:00Z",
            "publication_lifecycle_plan": {"plan_hash": sha256_of("CONTROLLED plan")}}}
    store.register_outbox_message(message_id="cc-editorial-final-" + sha256_of(run), work_item_id=run,
        destination="internal:cc-report-simple-result", payload=json.dumps(result), status="EDITORIAL_INTERNAL")
    destinations = ["substack", "facebook_page", "instagram_business", "youtube", "linkedin", "linkedin_company"]
    changes, objects = [], {}
    for destination in destinations:
        payload = {"text": label + "\n\nControlled report. https://capitalchronicle.substack.com/p/controlled",
            "platform_limit": 3000, "media_asset_ids": []}
        intent = {"work_item_id": run, "plan_hash": sha256_of("CONTROLLED plan"), "destination_plan": {
            "destination": destination, "payload_hash": sha256_of(payload)}, "native_payload": payload,
            "payload": payload["text"], "canonical_url": "https://capitalchronicle.substack.com/p/controlled"}
        message, dispatch = "message-" + destination, "dispatch-" + destination
        store.register_outbox_message(message_id=message, work_item_id=run, destination=destination,
            payload=json.dumps(intent), status="DISPATCH_CONFIRMED")
        objects[destination] = {"message_id": message, "dispatch_id": dispatch, "platform": destination,
            "public_object_id": "123", "public_object_url": "https://capitalchronicle.substack.com/p/controlled"}
        store.register_platform_dispatch(**objects[destination], status="DISPATCH_CONFIRMED")
        if destination != "substack":
            changes.append({"destination": destination, "existing_public_identity": objects[destination],
                "original_immutable_intent_sha256": sha256_of(intent), "before_payload": payload,
                "after_payload": {**payload, "text": date + "\n\n" + payload["text"].split("\n\n", 1)[1]}})
    monkeypatch.setattr("live_contentops._eight_platform_substack_first_pipeline_impl_v1._durable_intent_inputs",
        lambda intent: {"payloads": {intent["destination_plan"]["destination"]: intent["native_payload"]}})
    proposal = {"run_id": run, "article_identity": result["article_identity"], "derivative_amendments": changes,
        "canonical_amendment": {"governed_article_body": {"before": body + suffix, "after": body, "removed_exact_suffix": suffix},
            "display_date_if_rendered": {"before": result["article"]["display_date"], "after": date},
            "existing_public_identity": objects["substack"]}}
    revision = build_reader_presentation_revision(store, run_id=run, proposal=proposal, owner_authority_ref="human:CONTROLLED")
    return store, run, result, proposal, revision


def accept(revised, tmp_path):
    store, run, result, _, revision = revised
    view = reader_presentation_revision_view(store, run_id=run, result=result, revision=revision)
    turn = NativeDesktopTurn(store, run_id=run, output_dir=tmp_path, owner_manual_validation=True)
    store.create_work_item(story_id=turn.work, work_item_id=turn.work, title="CONTROLLED native turn", target_surface="TEST")
    observation = {"surface": "CODEX_NATIVE_SUBAGENT", "invocation_id": "CONTROLLED_NOT_REAL_MAX",
        "model": "gpt-6.1-sol", "reasoning_effort": "max", "observation_source": "CONTROLLED_TEST_NOT_PRODUCT_PROOF"}
    turn._put("write", "response", {"invocation_observation": observation})
    scope = {"substack", "facebook_page", "instagram_business", "youtube", "linkedin"}
    variants = final_visual_binding(view, renders=None, destinations=scope)["variants"]
    source = tmp_path / "CONTROLLED_NOT_REAL_RENDER.html"
    source.write_text("Synthetic contract pixels, no visual judgment.")
    renders = []
    for viewport, width in [("desktop", 1000), ("mobile", 390)]:
        pixels = tmp_path / (viewport + ".png")
        Image.new("RGB", (width, 200), "white").save(pixels)
        for destination, variant in variants.items():
            renders.append({"render_id": destination + viewport, "destination": destination, "viewport": viewport,
                "variant_sha256": variant, "path": str(pixels), "sha256": sha256(pixels.read_bytes()).hexdigest(),
                "render_source": {"path": str(source), "sha256": sha256(source.read_bytes()).hexdigest()}})
    with pytest.raises(DesktopInputRequired) as pending:
        request_final_visual_review(turn, renders=renders, reader_presentation_revision=revision)
    request = pending.value.request
    output = {"decision": "ACCEPT", "asset_findings": [], "render_findings": [{
        "render_id": r["render_id"], "sha256": r["sha256"], "pixels_inspected": True,
        "checks": dict.fromkeys(FINAL_VISUAL_LAYOUT_CHECKS, "PASS"), "findings": [],
        "evidence_notes": "Synthetic test response; not real native image inspection."} for r in renders]}
    turn.submit(request["stage"], {"request_sha256": request["request_sha256"], "output": output,
        "invocation_observation": observation})
    return {"stage": request["stage"], "request_sha256": request["request_sha256"], "output_dir": str(tmp_path)}


def test_copy_only_revision_retains_source_media_identity_and_original_rows(revised):
    store, run, result, proposal, revision = revised
    before = deepcopy(result)
    original = store.get_outbox_message("cc-editorial-final-" + sha256_of(run))["payload"]
    view = reader_presentation_revision_view(store, run_id=run, result=result, revision=revision)
    assert "### Sources" not in view["article"]["substack_body_markdown"]
    assert "no agreement is confirmed" in view["article"]["substack_body_markdown"]
    assert view["evidence"] == result["evidence"] and view["media_assets"] == result["media_assets"]
    assert result == before and store.get_outbox_message("cc-editorial-final-" + sha256_of(run))["payload"] == original
    bad = deepcopy(proposal)
    bad["canonical_amendment"]["governed_article_body"]["after"] = "An agreement is confirmed."
    with pytest.raises(ValueError, match="ONLY_DISCRETIONARY"):
        build_reader_presentation_revision(store, run_id=run, proposal=bad, owner_authority_ref="human:CONTROLLED")
    changed = deepcopy(revision)
    changed["payloads"]["linkedin"]["text"] += " New fact."
    with pytest.raises(ValueError, match="ONLY_DATED_PREFIX"):
        reader_presentation_revision_view(store, run_id=run, result=result, revision=changed)


def test_native_same_writer_review_rejects_changed_sources_and_object(revised, tmp_path):
    store, run, result, _, _ = revised
    ref = accept(revised, tmp_path)
    _, view, acceptance = reader_presentation_acceptance(store, run_id=run, reference=ref)
    from live_contentops.native_desktop_editorial_v1 import native_review_revision
    assert acceptance["article_revision"] == native_review_revision(view)
    assert acceptance["article_revision"] != native_review_revision(result)
    assert "### Sources" not in view["article"]["substack_body_markdown"]
    store.set_dispatch_status("dispatch-substack", "UNKNOWN_WRITE")
    with pytest.raises(ValueError, match="EXACT_CONFIRMED_OBJECT"):
        reader_presentation_acceptance(store, run_id=run, reference=ref)


def test_coordinator_edits_once_and_never_reposts_unknown_api_edit(revised, tmp_path):
    store, run, _, _, _ = revised
    ref = accept(revised, tmp_path)
    class Runtime:
        def __init__(self):
            self.edits = []
            self.verified = True
        def amend_reader_presentation(self, **kwargs):
            self.edits.append(kwargs["destination"])
            return {"status": "UNKNOWN_EDIT"}
        def readback(self, **kwargs):
            return {"verified": self.verified, "public_object_id": kwargs["public_object_id"]}
    runtime = Runtime()
    co = DurablePublicationCoordinator(store=store, transport_runtime=runtime)
    assert co.amend_reader_presentation("dispatch-facebook_page", review_reference=ref)["edit_called"] is False
    co.amend_reader_presentation("dispatch-substack", review_reference=ref)
    runtime.verified = False
    co.amend_reader_presentation("dispatch-facebook_page", review_reference=ref)
    runtime.verified = True
    final = co.amend_reader_presentation("dispatch-facebook_page", review_reference=ref)
    assert final["verified"] and final["new_post_calls"] == 0
    assert runtime.edits == ["substack", "facebook_page"]
    assert store.get_platform_dispatch("dispatch-facebook_page")["public_object_id"] == "123"
    assert "Reporting as of" not in json.loads(co._effective_message(store.get_outbox_message("message-facebook_page"))["payload"])["payload"]


def test_readback_requires_footer_absence_even_when_remaining_body_matches():
    value = {"work_item_id": "CONTROLLED", "payload": "Controlled article.", "reader_presentation_review": {},
        "removed_reader_text": ["Reporting as of 11:00 Bangkok on 27 October 2026."],
        "native_payload": {"body_markdown": "Controlled article."}, "destination_plan": {"payload_hash": "hash"}}
    value["reader_presentation_review"] = {"stage": "controlled"}
    def observed(request):
        return {"request_sha256": request["request_sha256"], "observed_identity": "capitalchronicle.substack.com",
            "public_object_id": "123", "public_object_url": "https://capitalchronicle.substack.com/p/controlled",
            "content_verified": True, "observed_text": "Controlled article. Reporting as of 11:00 Bangkok on 27 October 2026."}
    adapter = NeoDestinationHandoff(native_executor=observed)
    assert not adapter.readback(destination="substack", intent=value, public_object_id="123",
        public_object_url="https://capitalchronicle.substack.com/p/controlled")["verified"]


def test_native_edit_lost_return_is_never_claimed_again(revised, tmp_path, monkeypatch):
    store, run, _, _, _ = revised
    ref = accept(revised, tmp_path)
    co = DurablePublicationCoordinator(store=store, transport_runtime=None)
    message = store.get_outbox_message("message-substack")
    intent, _, _, _ = co._reader_presentation_intent(message, ref)
    auth = {"schema_version": "contentops.canonical_machine_authorization.v1", "operating_mode": "AUTONOMOUS_DEFAULT",
        "work_item_id": run, "destination": "substack", "dispatch_attempt_identity": "dispatch-substack",
        "payload_hash": intent["destination_plan"]["payload_hash"], "action": "EDIT_EXISTING"}
    request = NeoDestinationHandoff().request(destination="substack", action="EDIT_EXISTING", intent=intent,
        authorization_context=auth, public_object_id="123", public_object_url="https://capitalchronicle.substack.com/p/controlled")
    executor = NativeNeoExecutor(store, operation_id=run, output_dir=tmp_path, native_invocation_id="CONTROLLED", allow_publish=False)
    assert executor(request)["definite_no_write"] is True
    executor.allow_publish = True
    monkeypatch.setattr(executor, "readiness", lambda _: {"authenticated": True, "native_executor_bound": True})
    monkeypatch.setattr("live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled", lambda: None)
    with pytest.raises(NativeNeoInputRequired):
        executor(request)
    executor.begin(request["request_sha256"])
    assert executor(request)["status"] == "UNKNOWN_WRITE"
    with pytest.raises(ValueError, match="ALREADY_CLAIMED_READBACK_ONLY"):
        executor.begin(request["request_sha256"])
    assert store.get_platform_dispatch("dispatch-substack")["public_object_id"] == "123"


@pytest.mark.parametrize("destination,url,image", [
    ("instagram_business", "https://www.instagram.com/p/CONTROLLED/", "https://scontent.cdninstagram.com/controlled.jpg"),
    ("youtube", "https://www.youtube.com/post/CONTROLLED", "https://yt3.ggpht.com/controlled")])
def test_existing_photo_edit_readback_needs_bound_platform_comparison(destination, url, image):
    from live_contentops.neo_destination_handoff_v1 import IDENTITIES
    value = {"work_item_id": "CONTROLLED", "canonical_url": "https://capitalchronicle.substack.com/p/controlled",
        "native_payload": {"text": "Dated attributed report.", "media_asset_ids": ["photo"]},
        "media_assets": [{"asset_id": "photo", "sha256": "a" * 64}],
        "reader_presentation_review": {"stage": "CONTROLLED"}, "removed_reader_text": ["Old footer."],
        "destination_plan": {"payload_hash": "controlled"}}
    observed = {"observed_identity": IDENTITIES[destination], "public_object_id": "CONTROLLED", "public_object_url": url,
        "observed_text": "Dated attributed report.", "content_verified": True,
        "media_comparisons": [{"source_asset_sha256": "a" * 64, "platform_sha256": "b" * 64,
            "pixels_inspected": True, "source_pixels_match": True, "public_object_url": url, "public_image_url": image}]}
    adapter = NeoDestinationHandoff(native_executor=lambda request: {**observed, "request_sha256": request["request_sha256"]})
    assert adapter.readback(destination=destination, intent=value, public_object_id="CONTROLLED", public_object_url=url)["verified"]
    observed["media_comparisons"][0]["public_object_url"] = "https://example.org/unrelated"
    assert not adapter.readback(destination=destination, intent=value, public_object_id="CONTROLLED", public_object_url=url)["verified"]
