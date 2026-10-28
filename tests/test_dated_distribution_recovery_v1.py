"""Disposable contract fixtures; synthetic MAX responses are never visual product proof."""
import copy
import json
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone
from hashlib import sha256

import pytest
from PIL import Image

from live_contentops.native_desktop_editorial_v1 import (
    DesktopInputRequired, NativeDesktopTurn, build_dated_distribution_recovery,
    dated_distribution_recovery_view, final_visual_binding, request_final_visual_review,
    FINAL_VISUAL_LAYOUT_CHECKS, FINAL_VISUAL_DATA_CHECKS, FINAL_VISUAL_PHOTO_CHECKS,
    DATED_DISTRIBUTION_DESTINATIONS,
    dated_distribution_destinations,
)
from live_contentops.native_desktop_publication_v1 import _prepared_packet, NativeReviewedPublication
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, NativeNeoInputRequired
from test_native_desktop_publication_v1 import seeded
from test_publication_coordinator_v1 import FixtureTransport

CANONICAL = "https://capitalchronicle.substack.com/p/controlled-dated-brief"


class PayloadTransport(FixtureTransport):
    def __init__(self):
        super().__init__()
        self.sent, self.observed = [], []

    def publish(self, **kwargs):
        self.sent.append(copy.deepcopy(kwargs["intent"]))
        return super().publish(**kwargs)

    def readback(self, **kwargs):
        self.observed.append(copy.deepcopy(kwargs["intent"]))
        return super().readback(**kwargs)


def setup_recovery(tmp_path, monkeypatch):
    store, binding, _, result, _ = seeded(tmp_path, monkeypatch)
    runtime = PayloadTransport()
    co = DurablePublicationCoordinator(store=store, transport_runtime=runtime,
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"},
        clock=lambda: datetime.now(timezone.utc) + timedelta(days=365))
    _, plan, _ = _prepared_packet(store, binding)
    store.create_work_item(story_id=binding["run_id"], work_item_id=binding["run_id"], title="Controlled dated distribution", target_surface="TEST")
    co.register_plan(binding["run_id"], plan)
    ids = co._ids(binding["run_id"], plan["plan_hash"], "substack")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"], platform="substack",
        status="DISPATCH_CONFIRMED", public_object_id="CONTROLLED", public_object_url=CANONICAL)
    store.register_reconciliation(reconciliation_id=ids["reconciliation_id"], work_item_id=binding["run_id"], status="RECONCILED_CONFIRMED")
    for destination in DATED_DISTRIBUTION_DESTINATIONS:
        ids = co._ids(binding["run_id"], plan["plan_hash"], destination)
        message = store.get_outbox_message(ids["message_id"])
        intent = json.loads(message["payload"])
        intent["canonical_url"] = CANONICAL
        store.finalize_outbox_payload_before_dispatch(message_id=ids["message_id"], payload=json.dumps(intent), status="READY")
        store.set_outbox_status(ids["message_id"], "DERIVATIVE_EXPIRED_STALE_NO_WRITE")
        if destination != "youtube":
            store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"], platform=destination,
                status="DERIVATIVE_EXPIRED_STALE_NO_WRITE")
            store.register_reconciliation(reconciliation_id=ids["reconciliation_id"], work_item_id=binding["run_id"], status="RECONCILED_ABSENT_SAFE_TO_RETRY")
    monkeypatch.setattr("live_contentops._eight_platform_substack_first_pipeline_impl_v1._durable_intent_inputs",
        lambda intent: {"payloads": {intent["destination_plan"]["destination"]: {
            "text": "Controlled attributed brief. " + CANONICAL, "platform_limit": 2000,
            "media_asset_ids": [a["asset_id"] for a in result["media_assets"]]}}})
    recovery = build_dated_distribution_recovery(store, run_id=binding["run_id"], owner_authority_ref="human:CONTROLLED_APPROVAL")
    return store, binding, result, co, runtime, recovery


def accepted_recovery(store, binding, result, recovery, tmp_path, *, model=None, missing_render=False):
    view = dated_distribution_recovery_view(store, run_id=binding["run_id"], result=result, recovery=recovery)
    variants = final_visual_binding(view, renders=None, destinations=dated_distribution_destinations(recovery))["variants"]
    markup = tmp_path / "CONTROLLED_NOT_REAL_RENDER.html"
    markup.write_text("Synthetic contract render, no viewer-facing inspection proof.")
    source = {"path": str(markup), "sha256": sha256(markup.read_bytes()).hexdigest()}
    renders = []
    for viewport, width in [("desktop", 1280), ("mobile", 390)]:
        path = tmp_path / (viewport + ".png")
        Image.new("RGB", (width, 200), "white").save(path)
        for destination, variant in variants.items():
            renders.append({"destination": destination, "viewport": viewport, "render_id": destination+viewport,
                "path": str(path), "sha256": sha256(path.read_bytes()).hexdigest(), "render_source": source,
                "variant_sha256": variant})
    if missing_render:
        renders.pop()
    turn = NativeDesktopTurn(store, run_id=binding["run_id"], output_dir=binding["output_dir"], owner_manual_validation=True)
    with pytest.raises(DesktopInputRequired) as pending:
        request_final_visual_review(turn, renders=renders, distribution_recovery=recovery)
    request = pending.value.request
    bound = request["governed_input"]["binding"]
    observation = copy.deepcopy(turn._get("write", "response")["invocation_observation"])
    if model:
        observation["model"] = model
    output = {"decision": "ACCEPT", "asset_findings": [], "render_findings": []}
    for asset in bound["assets"]:
        keys = (*FINAL_VISUAL_LAYOUT_CHECKS, *(FINAL_VISUAL_DATA_CHECKS if asset["modality"] == "source_backed_chart" else FINAL_VISUAL_PHOTO_CHECKS))
        output["asset_findings"].append({"asset_id": asset["asset_id"], "asset_sha256": asset["sha256"],
            "pixels_inspected": True, "checks": dict.fromkeys(keys, "PASS"), "findings": [],
            "evidence_notes": "Synthetic test acceptance only; not actual MAX visual evidence."})
    for render in bound["renders"]:
        output["render_findings"].append({"render_id": render["render_id"], "sha256": render["sha256"],
            "pixels_inspected": True, "checks": dict.fromkeys(FINAL_VISUAL_LAYOUT_CHECKS, "PASS"), "findings": [],
            "evidence_notes": "Synthetic test viewport coverage; not actual rendered-product inspection."})
    turn.submit(request["stage"], {"request_sha256": request["request_sha256"], "invocation_observation": observation, "output": output})
    return {"stage": request["stage"], "request_sha256": request["request_sha256"], "output_dir": str(turn.root)}


@pytest.mark.parametrize("destination", ["facebook_page", "instagram_business", "youtube"])
def test_dated_amendment_retains_original_bytes_and_one_exact_send(tmp_path, monkeypatch, destination):
    store, binding, result, co, runtime, recovery = setup_recovery(tmp_path, monkeypatch)
    ref = accepted_recovery(store, binding, result, recovery, tmp_path)
    ids = co._ids(binding["run_id"], recovery["plan_hash"], destination)
    before = store.get_outbox_message(ids["message_id"])["payload"]
    if destination != "youtube":
        assert co.complete_derivative_after_transport_correction(ids["dispatch_id"], correction_id="CONTROLLED")["status"] == "CORRECTION_BLOCKED_DERIVATIVE_STALE"
    co.complete_dated_distribution_recovery(ids["message_id"], review_reference=ref)
    assert runtime.publish_calls == [destination]
    assert store.get_outbox_message(ids["message_id"])["payload"] == before
    effective = json.loads(co._dated_distribution_message(store.get_outbox_message(ids["message_id"]))["payload"])
    assert effective["native_payload"]["text"].startswith(recovery["date_label"])
    assert effective["canonical_url"] == CANONICAL
    assert runtime.sent[0]["native_payload"] == recovery["payloads"][destination]
    co.readback_existing_dispatch(ids["dispatch_id"])
    assert runtime.observed[-1]["native_payload"] == recovery["payloads"][destination]
    assert co.complete_dated_distribution_recovery(ids["message_id"], review_reference=ref)["publish_called"] is False
    assert runtime.publish_calls == [destination]


def test_unknown_destination_never_retries_under_dated_approval(tmp_path, monkeypatch):
    store, binding, result, co, runtime, recovery = setup_recovery(tmp_path, monkeypatch)
    ref = accepted_recovery(store, binding, result, recovery, tmp_path)
    ids = co._ids(binding["run_id"], recovery["plan_hash"], "facebook_page")
    store.set_dispatch_status(ids["dispatch_id"], "UNKNOWN_WRITE")
    assert co.complete_dated_distribution_recovery(ids["message_id"], review_reference=ref)["publish_called"] is False
    assert runtime.publish_calls == []


def test_changed_dates_or_channel_copy_fail_closed(tmp_path, monkeypatch):
    store, binding, result, _, _, recovery = setup_recovery(tmp_path, monkeypatch)
    changed = copy.deepcopy(recovery)
    changed["payloads"]["facebook_page"]["text"] = "Fresh news today"
    with pytest.raises(ValueError, match="SOURCE_OR_PAYLOAD_CHANGED"):
        dated_distribution_recovery_view(store, run_id=binding["run_id"], result=result, recovery=changed)
    assert recovery["source_cutoff_utc"] == binding["cutoff_utc"]


def test_six_affected_viewports_are_required(tmp_path, monkeypatch):
    store, binding, result, _, _, recovery = setup_recovery(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="DESKTOP_MOBILE_COVERAGE_REQUIRED"):
        accepted_recovery(store, binding, result, recovery, tmp_path, missing_render=True)


def test_wrong_model_cannot_accept_dated_recovery(tmp_path, monkeypatch):
    store, binding, result, _, runtime, recovery = setup_recovery(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="MODEL_MISMATCH|ACTUAL_SAME_SOL61_MAX"):
        accepted_recovery(store, binding, result, recovery, tmp_path, model="gpt-6-luna")
    assert runtime.publish_calls == []


def test_missing_review_or_other_destination_cannot_send(tmp_path, monkeypatch):
    store, binding, _, co, runtime, recovery = setup_recovery(tmp_path, monkeypatch)
    ids = co._ids(binding["run_id"], recovery["plan_hash"], "telegram")
    with pytest.raises(ValueError, match="ORIGINAL_DESTINATION_REQUIRED"):
        co.complete_dated_distribution_recovery(ids["message_id"], review_reference={})
    ids = co._ids(binding["run_id"], recovery["plan_hash"], "youtube")
    with pytest.raises((ValueError, KeyError)):
        co.complete_dated_distribution_recovery(ids["message_id"], review_reference={})
    assert runtime.publish_calls == []


@pytest.mark.parametrize("invalid", [None, "missing_return", "different_intent"])
def test_completed_native_write_survives_stale_marker_without_another_publish(tmp_path, monkeypatch, invalid):
    store, binding, _, co, runtime, recovery = setup_recovery(tmp_path, monkeypatch)
    ids = co._ids(binding["run_id"], recovery["plan_hash"], "youtube")
    intent = json.loads(store.get_outbox_message(ids["message_id"])["payload"])
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"], platform="youtube", status="NATIVE_NEO_TOOL_PENDING")
    executor = NativeNeoExecutor(store, operation_id=binding["run_id"], output_dir=tmp_path/"neo", native_invocation_id="CONTROLLED", allow_publish=True)
    monkeypatch.setattr(executor, "readiness", lambda _: {"authenticated": True, "native_executor_bound": True})
    runtime._neo_transport = SimpleNamespace(native_executor=executor)
    request = {"action": "PUBLISH", "destination": "youtube", "surface": "YOUTUBE_COMMUNITY_POST",
        "expected_identity": "@CapitalChronicleYouTube", "work_item_id": binding["run_id"],
        "dispatch_attempt_identity": ids["dispatch_id"], "intent_sha256": sha256_of(intent) if invalid != "different_intent" else "changed",
        "content_binding": {"expected_text_segments": ["Controlled completed write"]}}
    request["request_sha256"] = sha256_of(request)
    with pytest.raises(NativeNeoInputRequired) as pending:
        executor(request)
    packet = pending.value.request
    executor.begin(request["request_sha256"])
    store.set_dispatch_status(ids["dispatch_id"], "DERIVATIVE_EXPIRED_STALE_NO_WRITE")
    if invalid != "missing_return":
        response = {"tool_request_sha256": packet["tool_request_sha256"],
            "tool_observation": {"tool_name": "mcp__browseros_neo__run", "native_invocation_id": "CONTROLLED",
                "surface": "CODEX_DESKTOP_CONVERSATION", "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                "observation_source": "Synthetic disposable native-return fixture; no public write occurred."},
            "result": {"request_sha256": request["request_sha256"], "status": "SUCCESS", "observed_identity": "@CapitalChronicleYouTube",
                "public_object_id": "UgControlled", "public_object_url": "https://www.youtube.com/post/UgControlled"}}
        if invalid:
            executor.submit(request["request_sha256"], response)
        else:
            rollout = {"schema_version": "contentops.native_desktop_rollout.v1", "store_path": str(store.db_path),
                "editorial_output_root": str(tmp_path/"editorial"), "public_write_authority": True}
            publication = NativeReviewedPublication(store, binding, native_invocation_id="CONTROLLED",
                rollout=rollout, coordinator=co, executor=executor)
            submitted = publication.tool("submit", request_hash=request["request_sha256"], response=response)
            assert submitted["completed_write_reconciliation"]["publish_called"] is False
    if invalid:
        with pytest.raises(ValueError, match="EXACT_COMPLETED_NATIVE_PUBLISH_RETURN_REQUIRED"):
            co.reconcile_completed_native_publish(ids["dispatch_id"], request_hash=request["request_sha256"])
        assert store.get_platform_dispatch(ids["dispatch_id"])["public_object_id"] is None
    else:
        for _ in range(2):
            actual = co.reconcile_completed_native_publish(ids["dispatch_id"], request_hash=request["request_sha256"])
            assert actual["reconciliation_status"] == "RECONCILED_CONFIRMED" and actual["publish_called"] is False
        assert store.get_platform_dispatch(ids["dispatch_id"])["public_object_id"] == "UgControlled"
    assert runtime.publish_calls == []
