"""Controlled transports in disposable stores. Never browser/login/publication proof."""

import gzip
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    canonical_bytes,
    sha256_of,
)
from live_contentops.contentops_editorial_desk_v1 import record_native_article_review
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import (
    NativeReviewedPublication,
    prepare_native_publication,
    _prepared_packet,
)
from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, TOOL
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from live_contentops.publication_coordinator_v1 import (
    CanonicalDestinationTransportRuntimeV1,
    DurablePublicationCoordinator,
)
from live_contentops.v1_simple_gemini_scheduler_v1 import simple_gemini_slot_id

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018"
CANONICAL = "https://capitalchronicle.substack.com/p/controlled-goal32"


def seeded(tmp_path, monkeypatch, *, manual=False, final_visual=True):
    """Retain exact Goal31 prose/evidence/media bytes; relocate only this test packet."""
    fixture = json.loads(
        gzip.decompress((PROOF / "goal32/retained_goal31_packet.json.gz").read_bytes())
    )
    store = ContentOpsDurableStore(tmp_path / "CONTROLLED_NOT_PRODUCTION.sqlite3")
    day, window, auto = "2026-10-21", "controlled-window", "v1-newsroom-new-york-2100"
    run = simple_gemini_slot_id(production_day_id=day, window_id=window, slot_ordinal=1)
    out = tmp_path / "editorial" / day / window / run
    out.mkdir(parents=True)
    binding = {
        "schema_version": "contentops.native_desktop_operation_binding.v1",
        "run_id": run,
        "store_path": str(store.db_path),
        "output_dir": str(out),
        "feed_pointer_path": str(tmp_path / "feed.json"),
        "published_memory_store": str(store.db_path),
        "published_memory_output_root": str(tmp_path / "published"),
        "cutoff_utc": "2026-10-21T14:00:00Z",
        "owner_manual_validation": manual,
        "automation_id": auto,
        "window_id": window,
        "slot_ordinal": 1,
    }
    (out / "native_operation_binding.json").write_bytes(canonical_bytes(binding))
    result = fixture["final"]
    result["simple_result"]["run_id"] = run
    for asset in result["media_assets"]:
        source = (
            PROOF
            / "goal31/articles/goal31-company-machine-reading/media_assets/source_document_card.png"
        )
        target = out / "source_document_card.png"
        shutil.copyfile(source, target)
        asset["path"] = str(target)
    # Preserve the dated article fixture while supplying synthetic current-standard
    # assets for transport/control tests. These are not real photo/financial proof.
    from test_native_editorial_media_standard_v1 import controlled_release_packet
    controlled_source, photo, chart = controlled_release_packet(out / "CONTROLLED_RELEASE_MEDIA")
    result["evidence"].append(controlled_source)
    result["media_assets"] = [photo, chart]
    record = fixture["qualified_record"]
    record.update(
        attempt_run_id=run,
        parent_window_id=run,
        article_path=str(out / "article_manifest_v1.json"),
    )
    from live_contentops.newsroom_production_day_v1 import _logical_hash

    record["record_sha256"] = _logical_hash(
        {k: v for k, v in record.items() if k != "record_sha256"}
    )
    (out / "qualified_article_record_v1.json").write_bytes(canonical_bytes(record))
    work = "cc-opportunity-" + sha256_of(run)
    store.create_work_item(
        story_id=work,
        work_item_id=work,
        title="CONTROLLED retained Goal31",
        target_surface="TEST",
    )
    store.create_work_item(
        story_id=window,
        work_item_id=window,
        title="CONTROLLED window",
        target_surface="TEST",
    )
    for key, value, destination in [
        (
            "cc-editorial-final-" + sha256_of(run),
            result,
            "internal:cc-report-simple-result",
        ),
        (
            "native-operation-binding-" + sha256_of(run),
            binding,
            "internal:native-desktop-editorial",
        ),
    ]:
        store.register_outbox_message(
            message_id=key,
            work_item_id=work,
            destination=destination,
            payload=canonical_bytes(value).decode(),
            status="EDITORIAL_INTERNAL",
        )
    rollout = {
        "schema_version": "contentops.native_desktop_rollout.v1",
        "store_path": str(store.db_path),
        "editorial_output_root": str(tmp_path / "editorial"),
        "public_write_authority": True,
    }
    from live_contentops.daily_app_supervisor_v1 import (
        NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID,
    )

    checkpoint = {
        "production_day_id": day,
        "capacity": 1,
        "rollout_sha256": sha256_of(rollout),
        "window": {
            "opportunity_id": window,
            "session": NATIVE_DESKTOP_AUTOMATION_SESSION_BY_ID[auto],
        },
    }
    store.register_outbox_message(
        message_id="native-window-" + sha256_of(window),
        work_item_id=window,
        destination="internal:native-desktop-editorial",
        payload=canonical_bytes(checkpoint).decode(),
        status="EDITORIAL_INTERNAL",
    )
    review = record_native_article_review(
        store,
        run_id=run,
        article_identity=result["article_identity"],
        decision="KEEP",
        rationale="Controlled reuse of the exact reviewed Goal31 copy, source and media packet.",
    )
    prepare_native_publication(store, binding)
    monkeypatch.setattr(
        "live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled",
        lambda: None,
    )
    control = store.get_operating_control()
    store.update_operating_control(
        operating_mode="AUTONOMOUS_DEFAULT",
        expected_state_version=control["state_version"],
        control_source="CONTROLLED_TEST",
    )
    if final_visual:
        from native_final_visual_fixture_v1 import accept_final_visual_fixture
        review = accept_final_visual_fixture(store, binding, result, review)
        prepare_native_publication(store, binding)
    return store, binding, rollout, result, review


class ControlledTransport(CanonicalDestinationTransportRuntimeV1):
    def __init__(self, executor):
        super().__init__(neo_transport=NeoDestinationHandoff(native_executor=executor))
        self.calls, self.finalized, self.failed_once = [], {}, set()
        self.fail_destination = None

    def prepare_delivery_media(self, **kwargs):
        return {
            "status": "CLOUDINARY_DELIVERY_MEDIA_READY",
            "evidence_class": "CONTROLLED_NOT_PROVIDER_PROOF",
            "provider_calls": 0,
        }

    def finalize_intent(self, **kwargs):
        value = super().finalize_intent(**kwargs)
        self.finalized[kwargs["destination"]] = value
        return value

    def publish(self, *, destination, intent, authorization_context):
        if destination in {"substack", "x", "youtube"}:
            return super().publish(
                destination=destination,
                intent=intent,
                authorization_context=authorization_context,
            )
        self.calls.append(destination)
        if destination == self.fail_destination and destination not in self.failed_once:
            self.failed_once.add(destination)
            return {
                "status": "FAILED_BEFORE_WRITE",
                "definite_no_write": True,
                "reason_code": "CONTROLLED_LOCAL_FAILURE",
            }
        return {
            "status": "SUCCESS",
            "public_object_id": "controlled-" + destination,
            "public_object_url": "https://example.com/controlled/" + destination,
        }

    def readback(self, *, destination, intent, public_object_id, public_object_url):
        if destination in {"substack", "x", "youtube"}:
            return super().readback(
                destination=destination,
                intent=intent,
                public_object_id=public_object_id,
                public_object_url=public_object_url,
            )
        return {
            "status": "SUCCESS",
            "verified": True,
            "public_object_id": public_object_id,
            "public_object_url": public_object_url,
            "readback_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF",
        }


def composed(store, binding, rollout, monkeypatch):
    executor = NativeNeoExecutor(
        store,
        operation_id=binding["run_id"],
        output_dir=Path(binding["output_dir"]) / "native-neo",
        native_invocation_id="CONTROLLED",
        allow_publish=True,
    )
    monkeypatch.setattr(
        executor,
        "readiness",
        lambda _: {"authenticated": True, "native_executor_bound": True},
    )
    transport = ControlledTransport(executor)
    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=transport,
        readiness_provider=lambda _: {"readiness_state": "READY_AUTHENTICATED"},
    )
    # Exercise the production continuation's binder rather than a parallel publisher.
    monkeypatch.setattr(
        "live_contentops.native_desktop_publication_v1.bind_native_neo_coordinator",
        lambda *a, **k: (coordinator, executor),
    )
    return (
        NativeReviewedPublication(
            store, binding, rollout=rollout, native_invocation_id="CONTROLLED"
        ),
        executor,
        transport,
    )


def observed(packet):
    r = packet["request"]
    d = r["destination"]
    b = r["content_binding"]
    object_id = {
        "substack": "controlled-article",
        "x": "123456789",
        "youtube": "UgControlled",
    }[d]
    url = {
        "substack": CANONICAL,
        "x": "https://x.com/Capitalnicle/status/123456789",
        "youtube": "https://www.youtube.com/post/UgControlled",
    }[d]
    return {
        "tool_request_sha256": packet["tool_request_sha256"],
        "tool_observation": {
            "tool_name": TOOL,
            "native_invocation_id": "CONTROLLED",
            "surface": "CODEX_NATIVE_SUBAGENT",
            "observation_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "result": {
            "request_sha256": r["request_sha256"],
            "status": "SUCCESS",
            "observed_identity": r["expected_identity"],
            "public_object_id": object_id,
            "public_object_url": url,
            "content_verified": True,
            "observed_text": "\n\n".join(b["expected_text_segments"]),
            "observed_media_sha256": [a["sha256"] for a in b["media_manifest"]],
            "observed_thread": [
                {
                    "public_object_id": str(123456789 + i),
                    "public_object_url": "https://x.com/Capitalnicle/status/"
                    + str(123456789 + i),
                    "observed_text": text,
                }
                for i, text in enumerate(b["expected_thread_texts"])
            ],
        },
    }


def finish(operation, executor, *, limit=30):
    writes = []
    for _ in range(limit):
        value = operation.resume()
        if value["publication"]["state"] == "RECONCILED":
            return value, writes
        pending = executor.pending()
        actionable = [
            p
            for p in pending
            if not (p["action_claimed"] and p["request"]["action"] == "PUBLISH")
        ]
        if not actionable:
            return value, writes
        for packet in actionable:
            h = packet["request"]["request_sha256"]
            if not packet["action_claimed"]:
                operation.tool("begin", request_hash=h)
            if packet["request"]["action"] == "PUBLISH":
                writes.append(packet["request"]["destination"])
            operation.tool("submit", request_hash=h, response=observed(packet))
    pytest.fail("Controlled continuation did not converge within finite request budget")


def test_real_packet_preparation_manual_isolation_and_seals(tmp_path, monkeypatch):
    store, binding, rollout, result, review = seeded(tmp_path, monkeypatch, manual=True)
    operation = NativeReviewedPublication(
        store, binding, rollout=rollout, native_invocation_id="CONTROLLED"
    )
    before = len(store.list_outbox_messages())
    assert operation.projection()["state"] == "PREPARED"
    assert len(operation.projection()["destinations"]) == 9
    with pytest.raises(ValueError, match="OWNER_MANUAL"):
        operation.resume()
    assert (
        len(store.list_outbox_messages()) == before
        and not store.list_platform_dispatches()
    )
    original = (
        _prepared_packet(store, binding)[2] / "article_manifest_v1.json"
    ).read_bytes()
    assert json.loads(original) == result["article"]
    prepare_native_publication(store, binding)
    assert len(store.list_outbox_messages()) == before
    record_native_article_review(
        store,
        run_id=binding["run_id"],
        article_identity=result["article_identity"],
        decision="HOLD",
        rationale="Controlled newer review revokes the prior prepared packet.",
        expected_review_id=review["review_id"],
    )
    with pytest.raises(ValueError, match="KEEP_REVIEW_REQUIRED"):
        operation.validate()


def test_renderer_only_review_reuses_dispatched_plan_and_immutable_artifacts(tmp_path, monkeypatch):
    from native_final_visual_fixture_v1 import visual_request_fixture
    store, binding, _, result, review = seeded(tmp_path, monkeypatch, manual=True)
    packet, plan, root = _prepared_packet(store, binding)
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
    store.create_work_item(story_id=binding["run_id"], work_item_id=binding["run_id"],
        title="Controlled renderer-only existing publication", target_surface="TEST")
    coordinator.register_plan(binding["run_id"], plan)
    ids = coordinator._ids(binding["run_id"], plan["plan_hash"], "substack")
    store.register_platform_dispatch(dispatch_id=ids["dispatch_id"], message_id=ids["message_id"],
        platform="substack", status="UNKNOWN_WRITE", public_object_id="controlled-existing")
    originals = {name: (root / name).read_bytes() for name in packet["artifact_sha256"]}
    turn, request, response = visual_request_fixture(store, binding, result, revision_tag="renderer-only")
    turn.submit(request["stage"], response)
    revised = record_native_article_review(store, run_id=binding["run_id"], article_identity=result["article_identity"],
        decision="KEEP", rationale="Controlled renderer-only acceptance preserves all dispatched article package bytes.",
        expected_review_id=review["review_id"], final_visual_review={"stage": request["stage"],
            "request_sha256": request["request_sha256"], "output_dir": str(turn.root)})
    refreshed = prepare_native_publication(store, binding)
    assert refreshed["plan_hash"] == plan["plan_hash"]
    assert refreshed["review_id"] == revised["review_id"]
    assert {name: (root / name).read_bytes() for name in originals} == originals
    assert len(store.list_platform_dispatches()) == 1
    assert store.get_platform_dispatch(ids["dispatch_id"])["status"] == "UNKNOWN_WRITE"
    assert _prepared_packet(store, binding)[1]["plan_hash"] == plan["plan_hash"]


def test_compiler_change_after_keep_requires_a_new_preview_review(tmp_path, monkeypatch):
    store, binding, _, result, review = seeded(tmp_path, monkeypatch, manual=True)
    import live_contentops.v1_simple_gemini_newsroom_v1 as compiler
    bundle, _ = compiler._native_preview_bundle(article=result["article"],
        article_mode=result["article"]["resolved_article_mode"], article_identity=result["article_identity"],
        epistemic_state=result["article"].get("epistemic_state"),
        media_asset_ids=[a["asset_id"] for a in result["media_assets"]], media_assets=result["media_assets"])
    result["previews"] = [{"destination": k, "payload": v,
        "preview_id": "cc-preview-" + sha256_of([result["article_identity"], k, v]),
        "article_identity": result["article_identity"], "claim_lineage": result.get("claim_lineage", [])}
        for k, v in bundle["packages"].items()]
    result["media_preview_binding_sha256"] = sha256_of(result["previews"])
    store.finalize_outbox_payload_before_dispatch(message_id="cc-editorial-final-" + sha256_of(binding["run_id"]),
        payload=canonical_bytes(result).decode(), status="EDITORIAL_INTERNAL")
    record_native_article_review(store, run_id=binding["run_id"], article_identity=result["article_identity"], decision="KEEP",
        expected_review_id=review["review_id"], rationale="Controlled review of the unchanged article and exact compiled previews.")
    original = compiler._native_preview_bundle
    def changed(**kwargs):
        regenerated, intents = original(**kwargs)
        regenerated["packages"]["telegram"]["text"] += " Unreviewed compiler change."
        return regenerated, intents
    monkeypatch.setattr(compiler, "_native_preview_bundle", changed)
    with pytest.raises(ValueError, match="COMPILED_PREVIEW_CHANGED_REVIEW_REQUIRED"):
        prepare_native_publication(store, binding)


def test_canonical_first_real_url_eight_native_packages_restart_dedupe(
    tmp_path, monkeypatch
):
    store, binding, rollout, result, _ = seeded(tmp_path, monkeypatch)
    operation, executor, transport = composed(store, binding, rollout, monkeypatch)
    first = operation.resume()
    assert first["publication"]["state"] == "PENDING_NATIVE"
    assert transport.calls == [] and list(transport.finalized) == []
    packet = executor.pending()[0]
    assert packet["request"]["destination"] == "substack"
    # Crash before action: another owner operation returns the identical request/IDs.
    restarted = NativeReviewedPublication(
        ContentOpsDurableStore(store.db_path),
        binding,
        rollout=rollout,
        native_invocation_id="CONTROLLED",
    )
    restarted.resume()
    assert executor.pending()[0]["tool_request_sha256"] == packet["tool_request_sha256"]
    value, writes = finish(restarted, executor)
    assert value["publication"]["state"] == "RECONCILED", (value, transport.calls)
    assert writes == ["substack", "x", "youtube"]
    assert len(transport.calls) == 6 and len(set(transport.calls)) == 6
    assert len(transport.finalized) == 8
    for intent in transport.finalized.values():
        assert intent["canonical_url"] == CANONICAL
        assert "pending-publication" not in json.dumps(intent["native_payload"])
        assert (
            intent["rematerialization_model_call_count"]
            == intent["rematerialization_source_get_count"]
            == 0
        )
    assert (
        len(
            {
                json.dumps(v["native_payload"], sort_keys=True)
                for v in transport.finalized.values()
            }
        )
        == 8
    )
    before = (
        list(transport.calls),
        len(store.list_platform_dispatches()),
        len(store.list_outbox_messages()),
    )
    _, writes = finish(restarted, executor)
    assert writes == [] and before == (
        transport.calls,
        len(store.list_platform_dispatches()),
        len(store.list_outbox_messages()),
    )


def test_claimed_lost_publish_readback_before_retry_and_local_failure(
    tmp_path, monkeypatch
):
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    operation, executor, transport = composed(store, binding, rollout, monkeypatch)
    transport.fail_destination = "telegram"
    operation.resume()
    packet = executor.pending()[0]
    operation.tool("begin", request_hash=packet["request"]["request_sha256"])
    # Simulate a successful external action whose return was lost. No second PUBLISH.
    resumed = operation.resume()
    assert any(p["request"]["action"] == "READBACK" for p in executor.pending())
    assert resumed["publication"]["next_operation"] != "publication-tool-begin" or any(
        p["request"]["action"] == "READBACK" for p in executor.pending()
    )
    value, writes = finish(operation, executor)
    assert "substack" not in writes
    assert transport.calls.count("telegram") <= 2
    assert all(
        transport.calls.count(d) == 1
        for d in {
            "discord",
            "linkedin",
            "facebook_page",
            "instagram_business",
            "threads",
        }
    ), (value, transport.calls)
    # Depending on the existing bounded retry policy, only the failed derivative may remain.
    if value["publication"]["state"] != "RECONCILED":
        value, more = finish(operation, executor)
        writes += more
    assert value["publication"]["state"] == "RECONCILED"
    assert transport.calls.count("telegram") == 2
    assert len(store.list_platform_dispatches()) == 9


def test_lost_readback_projects_new_turn_begin_but_never_a_second_publish(tmp_path, monkeypatch):
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    operation, executor, _ = composed(store, binding, rollout, monkeypatch)
    operation.resume()
    publish = executor.pending()[0]
    operation.tool("begin", request_hash=publish["request"]["request_sha256"])
    operation.resume()
    readback = next(p for p in executor.pending() if p["request"]["action"] == "READBACK")
    operation.tool("begin", request_hash=readback["request"]["request_sha256"])
    restarted = NativeReviewedPublication(store, binding, rollout=rollout, native_invocation_id="RESUMED")
    projection = restarted.projection()
    assert projection["next_operation"] == "publication-tool-begin"
    assert readback["request"]["request_sha256"] in projection["next_command"]
    assert next(p for p in projection["pending_requests"] if p["request"]["action"] == "PUBLISH")["action_claimed"]
    assert not next(p for p in projection["pending_requests"] if p["request"]["action"] == "READBACK")["action_claimed"]


def test_source_and_artifact_changes_revoke_continuation_before_tool(
    tmp_path, monkeypatch
):
    store, binding, rollout, result, _ = seeded(tmp_path, monkeypatch)
    operation, executor, _ = composed(store, binding, rollout, monkeypatch)
    operation.resume()
    packet = executor.pending()[0]
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    source = {
        "article_identity": result["article_identity"],
        "invalidates_prepared_review": True,
        "decision": "MATERIAL_FOLLOW_UP",
    }
    store.register_outbox_message(
        message_id="controlled-source-change",
        work_item_id=work,
        destination="internal:native-story-source-review",
        payload=canonical_bytes(source).decode(),
        status="EDITORIAL_INTERNAL",
    )
    for action in (
        lambda: operation.resume(),
        lambda: operation.tool(
            "begin", request_hash=packet["request"]["request_sha256"]
        ),
    ):
        with pytest.raises(ValueError, match="SOURCE_CHANGED"):
            action()
    assert not executor.pending()[0]["action_claimed"]


def test_false_activation_and_forged_binding_do_not_dispatch(tmp_path, monkeypatch):
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    operation = NativeReviewedPublication(
        store,
        binding,
        rollout={**rollout, "public_write_authority": False},
        native_invocation_id="CONTROLLED",
    )
    with pytest.raises(ValueError, match="SEPARATE_OWNER"):
        operation.resume()
    operation.rollout = rollout
    with pytest.raises(ValueError, match="BINDING"):
        from live_contentops.native_desktop_publication_v1 import (
            scheduled_publication_authority,
        )

        scheduled_publication_authority(store, {**binding, "slot_ordinal": 2}, rollout)
    assert not store.list_platform_dispatches()


def test_artifact_seal_and_pause_rechecked_at_continuation(tmp_path, monkeypatch):
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    operation, executor, _ = composed(store, binding, rollout, monkeypatch)
    from live_contentops.llm_operator_control_v1 import LLMOperatorPausedError

    with monkeypatch.context() as pause:

        def paused():
            raise LLMOperatorPausedError()

        pause.setattr(
            "live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled",
            paused,
        )
        with pytest.raises(LLMOperatorPausedError):
            operation.resume()
    assert not store.list_platform_dispatches()
    operation.resume()
    packet = executor.pending()[0]
    path = (
        _prepared_packet(store, binding)[2] / "native_derivative_previews_v1.json"
    )
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="PACKET_CHANGED"):
        operation.tool("begin", request_hash=packet["request"]["request_sha256"])
    assert not executor.pending()[0]["action_claimed"]


@pytest.mark.parametrize("publication_enabled", [True, False])
def test_real_scheduler_retains_reviewed_slot_until_exact_handoff_exists(
    tmp_path, monkeypatch, publication_enabled
):
    import live_contentops.native_desktop_schedule_binding_v1 as schedule
    from live_contentops.contentops_editorial_desk_v1 import (
        record_native_article_review,
    )

    monkeypatch.setattr(schedule, "llm_operator_pause_active", lambda: False)
    monkeypatch.setattr(
        schedule, "load_canonical_published_memory_read_only", lambda **_: ([], {})
    )
    rollout = {
        "schema_version": schedule.SCHEMA,
        "store_path": str(tmp_path / "scheduled.sqlite3"),
        "published_output_root": str(tmp_path / "out"),
        "editorial_output_root": str(tmp_path / "out"),
        "feed_pointer_path": str(tmp_path / "feed.json"),
        "public_write_authority": publication_enabled,
    }
    initial = ContentOpsDurableStore(rollout["store_path"])
    control = initial.get_operating_control()
    initial.update_operating_control(
        operating_mode="AUTONOMOUS_DEFAULT" if publication_enabled else "SHADOW_ONLY",
        expected_state_version=control["state_version"],
        control_source="CONTROLLED_TEST",
    )
    now = datetime(2026, 10, 21, 14, 5, tzinfo=timezone.utc)
    first = schedule.scheduled_binding(rollout, "v1-newsroom-new-york-2100", now=now)
    binding = json.loads(Path(first["binding_path"]).read_bytes())
    store = ContentOpsDurableStore(rollout["store_path"])
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    store.create_work_item(
        story_id=work,
        work_item_id=work,
        title="CONTROLLED scheduler",
        target_surface="TEST",
    )
    original = json.loads(
        gzip.decompress((PROOF / "goal32/retained_goal31_packet.json.gz").read_bytes())
    )["final"]
    original["simple_result"]["run_id"] = binding["run_id"]
    store.register_outbox_message(
        message_id="cc-editorial-final-" + sha256_of(binding["run_id"]),
        work_item_id=work,
        destination="internal:cc-report-simple-result",
        payload=canonical_bytes(original).decode(),
        status="EDITORIAL_INTERNAL",
    )
    record_native_article_review(
        store,
        run_id=binding["run_id"],
        article_identity=original["article_identity"],
        decision="KEEP",
        rationale="Controlled scheduled review must resume the same qualified slot.",
    )
    handoff = Path(binding["output_dir"]) / "reviewed-handoff"
    handoff.mkdir()
    (handoff / "publication_lifecycle_plan_v1.json").write_text("{}")
    resumed = schedule.scheduled_binding(rollout, "v1-newsroom-new-york-2100", now=now)
    assert resumed["classification"] == "NATIVE_WINDOW_HANDOFF_REQUIRED"
    assert resumed["binding_path"] == first["binding_path"]
    assert resumed["slot_ordinal"] == first["slot_ordinal"]
    assert not store.list_platform_dispatches()


@pytest.mark.parametrize("publication_enabled", [True, False])
def test_exact_prepared_slot_replays_or_retains_the_existing_publisher_boundary(tmp_path, monkeypatch, publication_enabled):
    import live_contentops.native_desktop_schedule_binding_v1 as schedule
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    rollout["public_write_authority"] = publication_enabled
    before = len(store.list_outbox_messages())
    reply = schedule._issued_state(store, rollout, {"capacity": 3}, binding,
        Path(binding["output_dir"]) / "native_operation_binding.json")
    assert reply["classification"] == ("NATIVE_WINDOW_PUBLICATION_REQUIRED" if publication_enabled
                                         else "NATIVE_WINDOW_OPERATION_COMPLETE")
    assert reply["slot_ordinal"] == 1 and reply["model_invocations"] == reply["source_requests"] == 0
    assert len(store.list_outbox_messages()) == before and not store.list_platform_dispatches()


def test_current_identity_request_and_runtime_reuse(tmp_path, monkeypatch):
    store, binding, rollout, _, _ = seeded(tmp_path, monkeypatch)
    operation, executor, _ = composed(store, binding, rollout, monkeypatch)
    operation.resume()
    packet = executor.pending()[0]
    # Restore the real readiness protocol; begin may first need a VERIFY_IDENTITY return.
    monkeypatch.setattr(
        executor, "readiness", NativeNeoExecutor.readiness.__get__(executor)
    )
    value = operation.tool("begin", request_hash=packet["request"]["request_sha256"])
    assert value["classification"] == "NATIVE_NEO_CURRENT_IDENTITY_OBSERVATION_REQUIRED"
    assert value["native_tool_request"]["request"]["action"] == "VERIFY_IDENTITY"
    assert not executor.pending()[0]["action_claimed"]
    from live_contentops.production_runtime_v1 import FinalDailyAppProductionRuntime

    runtime = FinalDailyAppProductionRuntime(
        store,
        None,
        None,
        operation.coordinator.transport_runtime,
        operation.coordinator,
        None,
        native_neo_executor=executor,
    )
    existing = runtime.reviewed_publication(
        binding, rollout=rollout, native_invocation_id="CONTROLLED"
    )
    assert (
        existing.coordinator is operation.coordinator and existing.executor is executor
    )
