from __future__ import annotations

import json
from pathlib import Path

from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
    registration_for_destination,
)
from live_contentops.daily_app_supervisor_v1 import ContentOpsDailyAppSupervisor
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import (
    FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED,
    CanonicalDestinationTransportRuntimeV1,
    DurablePublicationCoordinator,
)
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _build_simple_publication_lifecycle_plan,
    _native_preview_bundle,
)


CANONICAL_URL = "https://capitalchronicle.substack.com/p/simple-bridge-fixture"


class ControlledCanonicalFirstRuntime:
    """No-I/O transport double that exercises the coordinator's real finalize seam."""

    def __init__(self) -> None:
        self.publish_calls: list[str] = []
        self.finalized: dict[str, dict] = {}
        self.canonical_readback_confirmed = False
        self.real_public_write_count = 0
        self.provider_call_count = 0
        self.browser_call_count = 0

    def prepare_delivery_media(self, **_kwargs):
        return {
            "status": "CLOUDINARY_DELIVERY_MEDIA_NOT_REQUIRED",
            "provider_calls": 0,
            "public_write_performed": False,
        }

    def finalize_intent(self, *, destination, intent, canonical_url):
        assert self.canonical_readback_confirmed is True
        assert canonical_url == CANONICAL_URL
        finalized = dict(
            CanonicalDestinationTransportRuntimeV1.finalize_intent(
                self,
                destination=destination,
                intent=intent,
                canonical_url=canonical_url,
            )
        )
        self.finalized[destination] = finalized
        return finalized

    def publish(self, *, destination, intent, authorization_context):
        del authorization_context
        self.publish_calls.append(destination)
        if destination == "substack":
            assert self.publish_calls == ["substack"]
            return {
                "status": "SUCCESS",
                "id": "substack-fixture-object",
                "public_url": CANONICAL_URL,
            }
        assert self.canonical_readback_confirmed is True
        assert intent["canonical_url"] == CANONICAL_URL
        assert destination in self.finalized
        return {
            "status": "SUCCESS",
            "id": f"{destination}-fixture-object",
            "public_url": f"https://public.example/{destination}/fixture",
        }

    def readback(self, *, destination, public_object_id, public_object_url, intent):
        del intent
        if destination == "substack":
            self.canonical_readback_confirmed = True
        return {
            "status": "SUCCESS",
            "verified": True,
            "public_object_id": public_object_id,
            "public_object_url": public_object_url,
        }


def _set_autonomous_test_mode(store: ContentOpsDurableStore) -> None:
    control = store.get_operating_control()
    store.update_operating_control(
        expected_state_version=control["state_version"],
        operating_mode="AUTONOMOUS_DEFAULT",
        control_source="CONTROLLED_ZERO_WRITE_TEST",
    )


def _bridge_fixture(tmp_path: Path):
    epistemic_state = {
        "schema_version": "contentops.v1_simple_epistemic_state.fixture",
        "event_confirmation_state": "UNCONFIRMED",
        "reader_visible_epistemic_label": "Unconfirmed report",
        "report_proposition": "The publisher reported the development.",
        "event_proposition": "The underlying development occurred.",
    }
    article = {
        "title": "A reported financing shift changes the immediate watchlist",
        "dek": "Unconfirmed report: the financing news changes what investors should monitor.",
        "search_title": "Reported financing shift changes the watchlist",
        "meta_description": "An unconfirmed financing report sharpens the near-term watchlist.",
        "social_hook": "Unconfirmed report: the financing news sharpens the watchlist.",
        "substack_body_markdown": (
            "The publisher reported a financing shift, but the underlying event remains unconfirmed. "
            "That distinction matters because report truth is not event truth.\n\n"
            "Investors should watch for a first-party filing or statement before treating the report "
            "as settled fact. The immediate implication is a narrower, conditional watchlist."
        ),
    }
    article_identity = "a" * 64
    previews, _intents = _native_preview_bundle(
        article=article,
        article_mode="BREAKING_BRIEF",
        article_identity=article_identity,
        epistemic_state=epistemic_state,
    )
    plan = _build_simple_publication_lifecycle_plan(
        run_id="simple-bridge-fixture",
        output_dir=tmp_path,
        selected_candidate={"story_identity": "story-simple-bridge"},
        selected_plan_entry={"article_mode": "BREAKING_BRIEF"},
        article=article,
        article_identity=article_identity,
        native_previews=previews,
        qualified_record={
            "accepted_evidence_ids": ["source-fixture-1"],
            "accepted_evidence_sha256": "e" * 64,
        },
        epistemic_state=epistemic_state,
    )
    return plan, previews, epistemic_state


def test_daily_app_accepts_only_explicit_qualified_simple_bridge_plan(tmp_path: Path):
    plan, _previews, _epistemic_state = _bridge_fixture(tmp_path / "artifacts")

    class SpyCoordinator:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def publish_plan(self, work_item_id, received_plan):
            self.calls.append((work_item_id, dict(received_plan)))
            return {"status": "CONTROLLED_BRIDGE_ACCEPTED", "public_write_performed": False}

    spy = SpyCoordinator()
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "daily-app-disposable.sqlite3",
        output_root=tmp_path / "daily-app-output",
        operating_mode="SHADOW_ONLY",
        newsroom_cycle=lambda **_kwargs: {"classification": "NO_PUBLICATION"},
        enable_publication_lifecycle=True,
        publication_coordinator=spy,
    )

    accepted = supervisor._maybe_drive_publication_lifecycle(
        "work-simple-bridge", {"publication_lifecycle_plan": plan}
    )
    abstained = supervisor._maybe_drive_publication_lifecycle(
        "work-simple-abstained", {"classification": "NO_PUBLICATION"}
    )

    assert accepted == {
        "status": "CONTROLLED_BRIDGE_ACCEPTED",
        "public_write_performed": False,
    }
    assert abstained is None
    assert spy.calls == [("work-simple-bridge", plan)]


def test_simple_plan_enters_existing_canonical_first_coordinator_and_rematerializes_exactly_eight(
    tmp_path: Path,
):
    plan, previews, epistemic_state = _bridge_fixture(tmp_path / "artifacts")
    pending_url = previews["canonical_url"]
    assert pending_url.endswith("pending-publication-aaaaaaaaaaaaaaaa")
    assert plan["canonical_url_before_state"] == "PENDING_NON_DISPATCHABLE"
    assert all(
        row["canonical_url"] is None
        and row["canonical_url_state"] == "PENDING_NON_DISPATCHABLE"
        for row in plan["destinations"]
        if row["destination"] != "substack"
    )

    store = ContentOpsDurableStore(tmp_path / "disposable-store.sqlite3")
    store.create_work_item(
        story_id="story-simple-bridge",
        title="Controlled Simple bridge fixture",
        target_surface="MULTI_PLATFORM",
        work_item_id="work-simple-bridge",
        actor_ref="controlled_test",
        correlation_id="simple-bridge-fixture",
    )
    _set_autonomous_test_mode(store)
    runtime = ControlledCanonicalFirstRuntime()
    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=runtime,
        readiness_provider=lambda destination: {
            "readiness_state": (
                "READY_AUTHENTICATED"
                if registration_for_destination(destination).transport_type == "EDGE_CDP"
                else "READY_NON_BROWSER_BINDING"
            ),
            "identity_match": True,
            "write_eligible": True,
        },
    )

    result = coordinator.publish_plan("work-simple-bridge", plan)

    assert runtime.publish_calls[0] == "substack"
    assert runtime.publish_calls[1:] == sorted(V1_REQUIRED_DERIVATIVE_DESTINATIONS)
    assert result["canonical_url"] == CANONICAL_URL
    assert result["distribution_status"] == FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED
    assert result["derivative_attempted_count"] == 8
    assert result["derivative_confirmed_count"] == 8
    assert set(runtime.finalized) == set(V1_REQUIRED_DERIVATIVE_DESTINATIONS)

    for destination, intent in runtime.finalized.items():
        assert intent["article_identity"] == plan["article_identity"]
        assert intent["article_content_sha256"] == plan["article_content_sha256"]
        assert intent["compiler_input_sha256"] == plan["compiler_input_sha256"]
        assert intent["accepted_evidence_ids"] == plan["accepted_evidence_ids"]
        assert intent["accepted_evidence_sha256"] == plan["accepted_evidence_sha256"]
        assert intent["source_provenance_binding_preserved"] is True
        assert intent["epistemic_state"] == epistemic_state
        assert intent["canonical_url"] == CANONICAL_URL
        assert CANONICAL_URL in json.dumps(intent["native_payload"])
        assert pending_url not in json.dumps(intent["native_payload"])
        assert intent["rematerialization_model_call_count"] == 0
        assert intent["rematerialization_source_get_count"] == 0
        assert intent["destination_plan"]["canonical_url_state"] == (
            "RECONCILED_CANONICAL_URL_BOUND"
        )

    for destination in ("x", "threads"):
        payload = runtime.finalized[destination]["native_payload"]
        metrics = payload["quality_metrics"]
        assert metrics["sentence_boundary_pass"] is True
        assert metrics["orphan_fragment_count"] == 0
        assert metrics["hard_character_slicing_used"] is False
        assert payload["hard_truncation_used"] is False

    assert plan["bridge_model_call_count"] == 0
    assert plan["bridge_source_get_count"] == 0
    assert runtime.real_public_write_count == 0
    assert runtime.provider_call_count == 0
    assert runtime.browser_call_count == 0
    assert result["unknown_write_detected"] is False
    assert not str(store.db_path).startswith(
        r"A:\Capital Chronicle\Runtime\ContentOps"
    )
