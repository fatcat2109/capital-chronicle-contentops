from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.newsroom_production_day_v1 import (
    build_current_zero_write_qualified_article_record,
    newsroom_production_day_id,
    persist_qualified_article_record,
)
from live_contentops.v1_simple_gemini_newsroom_v1 import (
    _build_simple_publication_lifecycle_plan,
)
from live_contentops.v1_simple_gemini_scheduler_v1 import SimpleGeminiLocalScheduler
from live_contentops.v1_simple_publication_handoff_v1 import SimplePublicationHandoffV1

CUTOFF = "2026-08-28T10:00:00Z"


def _memory_loader():
    return lambda: (
        [],
        {
            "schema_version": "contentops.v1_simple_published_memory_access.v1",
            "canonical_reconciled_article_count": 0,
            "store_access_mode": "SQLITE_MODE_RO_QUERY_ONLY",
            "auto_migrate": False,
            "production_store_unchanged_during_projection": True,
            "second_publication_store_created": False,
        },
    )


def _qualified_artifacts(root: Path, *, slot_id: str) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    story_identity = "story-crash-boundary"
    article = {
        "title": "Controlled crash-boundary publication",
        "dek": "A deterministic test article for publication recovery.",
        "search_title": "Controlled crash-boundary publication",
        "meta_description": "Deterministic publication recovery fixture.",
        "social_hook": "Deterministic publication recovery fixture.",
        "substack_body_markdown": "Body for controlled crash-boundary publication.",
    }
    article_identity = hashlib.sha256(
        article["substack_body_markdown"].encode("utf-8")
    ).hexdigest()
    intents = [
        {
            "destination": destination,
            "dispatch_state": "UNDISPATCHED",
            "article_identity": article_identity,
        }
        for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
    ]
    record = build_current_zero_write_qualified_article_record(
        production_day_id=newsroom_production_day_id(CUTOFF),
        parent_window_id=slot_id,
        attempt_run_id=slot_id,
        article=article,
        story_identity=story_identity,
        update_chain_identity=story_identity,
        resolved_article_mode="BREAKING_BRIEF",
        accepted_evidence_documents=[
            {
                "document_id": "doc-crash-boundary",
                "source_url": "https://example.com/crash-boundary",
                "canonical_content_sha256": "a" * 64,
                "published_at_utc": CUTOFF,
                "published_at_source": "CONTROLLED",
            }
        ],
        editorial_provider="9router",
        editorial_model="vx/gemini-3.5-flash(high)",
        editorial_reasoning_effort="HIGH",
        logical_model_invocation_count=2,
        derivative_package_intents=intents,
    )
    persist_qualified_article_record(root, record)
    (root / "article_manifest_v1.json").write_text(
        json.dumps(article, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    previews = {
        "packages": {
            destination: {"text": f"preview:{destination}"}
            for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
        }
    }
    (root / "native_derivative_previews_v1.json").write_text(
        json.dumps(previews, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return _build_simple_publication_lifecycle_plan(
        run_id=slot_id,
        output_dir=root,
        selected_candidate={"story_identity": story_identity},
        selected_plan_entry={"article_mode": "BREAKING_BRIEF"},
        article=article,
        article_identity=record["article_identity"],
        native_previews=previews,
        qualified_record=record,
        epistemic_state=record.get("epistemic_state") or {},
    )


def test_pre_registration_crash_resume_recovers_then_registers_same_work_item_before_publish(tmp_path):
    slot_id = "simple-gemini-slot-pre-registration-crash"
    root = tmp_path / slot_id
    plan = _qualified_artifacts(root, slot_id=slot_id)
    store = ContentOpsDurableStore(tmp_path / "disposable.sqlite3")
    events: list[str] = []

    class Coordinator:
        def recover_pending(self):
            events.append("recover")
            return {"backlog_remaining": 0, "publish_calls": 0}

        def register_plan(self, work_item_id, received_plan):
            events.append("register")
            item = store.get_work_item(work_item_id)
            assert item is not None
            assert item["work_item_id"] == slot_id
            assert item["story_id"] == plan["story_identity"]
            assert received_plan["plan_hash"] == plan["plan_hash"]
            return []

        def publish_plan(self, work_item_id, received_plan):
            events.append("publish")
            assert work_item_id == slot_id
            assert received_plan["plan_hash"] == plan["plan_hash"]
            return {
                "canonical_article_real_published": True,
                "canonical_url": "https://capitalchronicle.substack.com/p/crash-boundary",
                "distribution_status": "FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED",
                "derivative_confirmed_count": 8,
                "derivative_attempted_count": 8,
                "public_write_performed": False,
                "unknown_write_detected": False,
            }

    handoff = SimplePublicationHandoffV1(store=store, coordinator=Coordinator())
    result = handoff.resume(slot_id=slot_id, slot_output_dir=root)

    assert events == ["recover", "register", "publish"]
    assert result["state"] == "PUBLISHED"
    assert result["work_item_id"] == slot_id
    assert result["plan_hash"] == plan["plan_hash"]
    assert result["bridge_model_call_count"] == 0
    assert result["bridge_source_get_count"] == 0


def test_ambiguous_or_unresolved_recovery_backlog_never_registers_or_republishes_current_intent(tmp_path):
    slot_id = "simple-gemini-slot-ambiguous-write"
    root = tmp_path / slot_id
    plan = _qualified_artifacts(root, slot_id=slot_id)
    store = ContentOpsDurableStore(tmp_path / "disposable.sqlite3")
    events: list[str] = []

    class Coordinator:
        def recover_pending(self):
            events.append("recover")
            return {"backlog_remaining": 1, "publish_calls": 0}

        def register_plan(self, *_args, **_kwargs):
            pytest.fail("unresolved recovery backlog must block current-plan registration")

        def publish_plan(self, *_args, **_kwargs):
            pytest.fail("unresolved recovery backlog must never blind-republish")

    handoff = SimplePublicationHandoffV1(store=store, coordinator=Coordinator())
    result = handoff.resume(slot_id=slot_id, slot_output_dir=root)

    assert events == ["recover"]
    assert result["state"] == "PUBLICATION_RECOVERY_REQUIRED"
    assert result["plan_hash"] == plan["plan_hash"]
    assert result["publication_coordinator_dispatched"] is False
    assert result["bridge_model_call_count"] == 0
    assert result["bridge_source_get_count"] == 0


def test_terminal_window_duplicate_tick_never_reinvokes_simple_or_publication_handoff(tmp_path):
    semantic_calls: list[str] = []
    publication_calls: list[str] = []

    def semantic(**kwargs):
        semantic_calls.append(kwargs["run_id"])
        if len(semantic_calls) == 1:
            record_root = Path(kwargs["output_dir"])
            _qualified_artifacts(record_root, slot_id=kwargs["run_id"])
            return {
                "classification": "PASS_V1_SIMPLE_GEMINI_ZERO_WRITE_ARTICLE",
                "candidate_count": 32,
                "candidate_limit": 32,
                "source_request_count": 1,
                "logical_model_invocation_count": 2,
                "provider_attempt_count": 2,
                "revision_performed": False,
                "article_identity": "a" * 64,
                "publication_lifecycle_plan": {
                    "plan_hash": "returned-plan-hash-not-used-by-fake"
                },
                "codex_runtime_model_call_count": 0,
                "public_write_performed": False,
                "provider_publication_writes": 0,
                "unknown_write_count": 0,
            }
        return {
            "classification": "NO_PUBLICATION",
            "exact_next_blocker": "CONTROLLED_ABSTENTION",
            "candidate_count": 32,
            "candidate_limit": 32,
            "source_request_count": 0,
            "logical_model_invocation_count": 1,
            "provider_attempt_count": 1,
            "revision_performed": False,
            "codex_runtime_model_call_count": 0,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
        }

    class Handoff:
        def recover_preflight(self):
            return {
                "backlog_remaining": 0,
                "backlog_blocking_new_publication": False,
                "publish_calls": 0,
            }

        def publish(self, *, slot_id, slot_output_dir, returned_plan):
            del slot_output_dir, returned_plan
            publication_calls.append(slot_id)
            return {
                "state": "PUBLISHED",
                "work_item_id": slot_id,
                "plan_hash": f"plan:{slot_id}",
                "article_identity": "a" * 64,
                "canonical_article_real_published": True,
                "canonical_url": f"https://capitalchronicle.substack.com/p/{slot_id}",
                "distribution_status": "FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED",
                "derivative_confirmed_count": 8,
                "derivative_attempted_count": 8,
                "publication_coordinator_dispatched": True,
                "public_write_performed": True,
                "provider_publication_writes": 9,
                "unknown_write_detected": False,
                "unknown_write_count": 0,
                "bridge_model_call_count": 0,
                "bridge_source_get_count": 0,
            }

        def resume(self, **_kwargs):
            pytest.fail("terminal duplicate tick must not enter publication recovery")

    scheduler = SimpleGeminiLocalScheduler(
        scheduler_root=tmp_path,
        simple_operation=semantic,
        published_memory_loader=_memory_loader(),
        publication_handoff=Handoff(),
    )
    first = scheduler.tick(now=CUTOFF)
    assert first["classification"] == "TERMINAL_PUBLISHED"
    semantic_count = len(semantic_calls)
    publication_count = len(publication_calls)

    second = scheduler.tick(now=CUTOFF)

    assert second["classification"] == "WINDOW_ALREADY_TERMINAL"
    assert len(semantic_calls) == semantic_count
    assert len(publication_calls) == publication_count == 1
