from __future__ import annotations

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
from live_contentops.v1_simple_publication_handoff_v1 import (
    PLAN_FILENAME,
    SimplePublicationHandoffV1,
)
from scripts import run_v1_simple_gemini_scheduler as runner


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


def _derivative_intents(article_identity: str) -> list[dict]:
    return [
        {
            "destination": destination,
            "dispatch_state": "UNDISPATCHED",
            "article_identity": article_identity,
        }
        for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
    ]


def _persist_qualified(
    output_dir: Path,
    *,
    cutoff_utc: str,
    run_id: str,
    story_identity: str,
) -> dict:
    article = {
        "title": f"Qualified {story_identity}",
        "dek": "A controlled deterministic test article.",
        "search_title": f"Qualified {story_identity}",
        "meta_description": "Controlled deterministic article metadata.",
        "social_hook": "Controlled deterministic article hook.",
        "substack_body_markdown": f"Body for {story_identity}",
    }
    identity = __import__("hashlib").sha256(
        article["substack_body_markdown"].encode("utf-8")
    ).hexdigest()
    record = build_current_zero_write_qualified_article_record(
        production_day_id=newsroom_production_day_id(cutoff_utc),
        parent_window_id=run_id,
        attempt_run_id=run_id,
        article=article,
        story_identity=story_identity,
        update_chain_identity=story_identity,
        resolved_article_mode="BREAKING_BRIEF",
        accepted_evidence_documents=[
            {
                "document_id": f"doc-{story_identity}",
                "source_url": f"https://example.com/{story_identity}",
                "canonical_content_sha256": "a" * 64,
                "published_at_utc": cutoff_utc,
                "published_at_source": "CONTROLLED",
            }
        ],
        editorial_provider="9router",
        editorial_model="vx/gemini-3.5-flash(high)",
        editorial_reasoning_effort="HIGH",
        logical_model_invocation_count=2,
        derivative_package_intents=_derivative_intents(identity),
    )
    persist_qualified_article_record(output_dir, record)
    return record


def _controlled_operation(calls: list[dict], outcomes: list[str]):
    def run(**kwargs):
        index = len(calls)
        calls.append(dict(kwargs))
        outcome = outcomes[index] if index < len(outcomes) else "ABSTAIN"
        if outcome == "PASS":
            record = _persist_qualified(
                Path(kwargs["output_dir"]),
                cutoff_utc=kwargs["cutoff_utc"],
                run_id=kwargs["run_id"],
                story_identity=f"story-{index + 1}",
            )
            return {
                "classification": "PASS_V1_SIMPLE_GEMINI_ZERO_WRITE_ARTICLE",
                "candidate_count": 32,
                "candidate_limit": 32,
                "source_request_count": 2,
                "logical_model_invocation_count": 2,
                "provider_attempt_count": 2,
                "revision_performed": False,
                "article_identity": record["article_identity"],
                "publication_lifecycle_plan": {"plan_hash": f"plan-{index + 1}"},
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
            "source_request_count": 1,
            "logical_model_invocation_count": 1,
            "provider_attempt_count": 1,
            "qualified_article_count": 0,
            "codex_runtime_model_call_count": 0,
            "public_write_performed": False,
            "provider_publication_writes": 0,
            "unknown_write_count": 0,
        }

    return run


class FakePublicationHandoff:
    def __init__(self, *, backlog: int = 0, publish_state: str = "PUBLISHED") -> None:
        self.backlog = backlog
        self.publish_state = publish_state
        self.preflight_calls = 0
        self.publish_calls: list[dict] = []
        self.resume_calls: list[dict] = []

    def recover_preflight(self):
        self.preflight_calls += 1
        return {
            "backlog_remaining": self.backlog,
            "backlog_blocking_new_publication": bool(self.backlog),
            "publish_calls": 0,
        }

    def _result(self, slot_id: str):
        published = self.publish_state == "PUBLISHED"
        return {
            "state": self.publish_state,
            "work_item_id": slot_id,
            "plan_hash": f"plan:{slot_id}",
            "article_identity": "a" * 64,
            "canonical_article_real_published": published,
            "canonical_url": (
                f"https://capitalchronicle.substack.com/p/{slot_id}"
                if published
                else None
            ),
            "distribution_status": (
                "FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED"
                if published
                else "BLOCKED_SAFE_RECOVERY_BACKLOG_REMAINS"
            ),
            "derivative_confirmed_count": 8 if published else 0,
            "derivative_attempted_count": 8 if published else 0,
            "publication_coordinator_dispatched": True,
            "public_write_performed": published,
            "provider_publication_writes": 9 if published else 0,
            "unknown_write_detected": not published,
            "unknown_write_count": 0 if published else 1,
            "bridge_model_call_count": 0,
            "bridge_source_get_count": 0,
        }

    def publish(self, *, slot_id, slot_output_dir, returned_plan):
        self.publish_calls.append(
            {
                "slot_id": slot_id,
                "slot_output_dir": str(slot_output_dir),
                "returned_plan": returned_plan,
            }
        )
        return self._result(slot_id)

    def resume(self, *, slot_id, slot_output_dir):
        self.resume_calls.append(
            {"slot_id": slot_id, "slot_output_dir": str(slot_output_dir)}
        )
        return self._result(slot_id)


def test_due_qualified_slot_dispatches_once_and_abstention_never_dispatches(tmp_path):
    calls: list[dict] = []
    handoff = FakePublicationHandoff()
    scheduler = SimpleGeminiLocalScheduler(
        scheduler_root=tmp_path,
        simple_operation=_controlled_operation(calls, ["PASS", "ABSTAIN"]),
        published_memory_loader=_memory_loader(),
        publication_handoff=handoff,
    )

    result = scheduler.tick(now="2026-08-28T10:00:00Z")

    assert result["classification"] == "TERMINAL_PUBLISHED"
    assert result["simple_operation_invocation_count"] == 2
    assert len(handoff.publish_calls) == 1
    assert handoff.publish_calls[0]["slot_id"] == calls[0]["run_id"]
    assert result["publication_coordinator_dispatched"] is True
    assert result["public_write_performed"] is True
    assert result["unknown_write_count"] == 0
    assert [row["state"] for row in result["slots"]] == ["PUBLISHED", "ABSTAINED"]


def test_due_abstention_performs_zero_publication_handoff(tmp_path):
    calls: list[dict] = []
    handoff = FakePublicationHandoff()
    scheduler = SimpleGeminiLocalScheduler(
        scheduler_root=tmp_path,
        simple_operation=_controlled_operation(calls, ["ABSTAIN", "ABSTAIN"]),
        published_memory_loader=_memory_loader(),
        publication_handoff=handoff,
    )

    result = scheduler.tick(now="2026-08-28T10:00:00Z")

    assert result["classification"] == "TERMINAL_NO_PUBLICATION"
    assert len(calls) == 2
    assert handoff.publish_calls == []
    assert handoff.resume_calls == []
    assert result["publication_coordinator_dispatched"] is False


def test_recovery_backlog_blocks_new_simple_semantic_work_before_model_or_source(tmp_path):
    calls: list[dict] = []
    handoff = FakePublicationHandoff(backlog=1)
    scheduler = SimpleGeminiLocalScheduler(
        scheduler_root=tmp_path,
        simple_operation=_controlled_operation(calls, ["PASS"]),
        published_memory_loader=_memory_loader(),
        publication_handoff=handoff,
    )

    result = scheduler.tick(now="2026-08-28T10:00:00Z")

    assert result["classification"] == "PUBLICATION_RECOVERY_PENDING"
    assert handoff.preflight_calls == 1
    assert calls == []
    assert result["simple_operation_invocation_count"] == 0
    assert result["source_get_count"] == 0
    assert result["gemini_logical_call_count"] == 0


def test_interrupted_post_qualification_handoff_resumes_without_rerunning_simple(tmp_path):
    seed_dir = tmp_path / "seed"
    _persist_qualified(
        seed_dir,
        cutoff_utc="2026-08-28T09:00:00Z",
        run_id="seed-slot",
        story_identity="seed-story",
    )
    calls: list[dict] = []
    first_handoff = FakePublicationHandoff(
        publish_state="PUBLICATION_RECOVERY_REQUIRED"
    )
    first = SimpleGeminiLocalScheduler(
        scheduler_root=tmp_path,
        simple_operation=_controlled_operation(calls, ["PASS"]),
        published_memory_loader=_memory_loader(),
        publication_handoff=first_handoff,
    )
    interrupted = first.tick(now="2026-08-28T10:00:00Z")
    # A qualified-only seed is not live published output, so the first routine slot retains
    # bounded capacity needed to reach the published target.
    assert interrupted["slot_capacity"] == 2
    assert interrupted["classification"] == "PUBLICATION_RECOVERY_PENDING"
    assert len(calls) == 1
    assert len(first_handoff.publish_calls) == 1

    resume_handoff = FakePublicationHandoff(publish_state="PUBLISHED")
    restarted = SimpleGeminiLocalScheduler(
        scheduler_root=tmp_path,
        simple_operation=lambda **_kwargs: pytest.fail(
            "Simple semantic/model work must not rerun during publication recovery"
        ),
        published_memory_loader=_memory_loader(),
        publication_handoff=resume_handoff,
    )
    recovered = restarted.tick(now="2026-08-30T04:30:00Z")

    assert recovered["classification"] == "IDLE_NOT_DUE"
    assert recovered["simple_operation_invocation_count"] == 0
    assert recovered["publication_resume"]["resume_attempt_count"] == 1
    assert recovered["publication_resume"]["resumed_published_count"] == 1
    assert len(resume_handoff.resume_calls) == 1
    assert resume_handoff.publish_calls == []


def _artifact_fixture(root: Path, *, slot_id: str) -> tuple[dict, dict]:
    article = {
        "title": "Controlled publication handoff",
        "dek": "A deterministic publication-handoff fixture.",
        "search_title": "Controlled publication handoff",
        "meta_description": "A deterministic handoff fixture.",
        "social_hook": "A deterministic handoff fixture.",
        "substack_body_markdown": "Controlled publication handoff body.",
    }
    record = _persist_qualified(
        root,
        cutoff_utc="2026-08-28T10:00:00Z",
        run_id=slot_id,
        story_identity="story-controlled-handoff",
    )
    # Keep the public article bytes aligned to the already-qualified body identity.
    article["title"] = record["title"]
    article["substack_body_markdown"] = "Body for story-controlled-handoff"
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
    plan = _build_simple_publication_lifecycle_plan(
        run_id=slot_id,
        output_dir=root,
        selected_candidate={"story_identity": record["story_identity"]},
        selected_plan_entry={"article_mode": record["resolved_article_mode"]},
        article=article,
        article_identity=record["article_identity"],
        native_previews=previews,
        qualified_record=record,
        epistemic_state=record.get("epistemic_state") or {},
    )
    return record, plan


def test_handoff_reconstructs_same_plan_and_creates_deterministic_work_item_before_coordinator(tmp_path):
    slot_id = "simple-gemini-slot-controlled"
    root = tmp_path / slot_id
    root.mkdir(parents=True)
    _record, expected_plan = _artifact_fixture(root, slot_id=slot_id)
    store = ContentOpsDurableStore(tmp_path / "disposable.sqlite3")

    class Coordinator:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        def recover_pending(self):
            return {"backlog_remaining": 0, "publish_calls": 0}

        def publish_plan(self, work_item_id, plan):
            item = store.get_work_item(work_item_id)
            assert item["work_item_id"] == slot_id
            assert item["story_id"] == expected_plan["story_identity"]
            self.calls.append((work_item_id, dict(plan)))
            return {
                "canonical_article_real_published": True,
                "canonical_url": "https://capitalchronicle.substack.com/p/controlled",
                "distribution_status": "FULL_V1_NINE_SURFACE_PUBLICATION_CONFIRMED",
                "derivative_confirmed_count": 8,
                "derivative_attempted_count": 8,
                "public_write_performed": False,
                "unknown_write_detected": False,
                "per_destination": {},
            }

    coordinator = Coordinator()
    handoff = SimplePublicationHandoffV1(store=store, coordinator=coordinator)
    reconstructed = handoff.ensure_plan(slot_id=slot_id, slot_output_dir=root)
    assert reconstructed["plan_hash"] == expected_plan["plan_hash"]
    assert (root / PLAN_FILENAME).is_file()

    outcome = handoff.publish(
        slot_id=slot_id,
        slot_output_dir=root,
        returned_plan=reconstructed,
    )
    assert outcome["state"] == "PUBLISHED"
    assert len(coordinator.calls) == 1
    assert coordinator.calls[0][0] == slot_id
    assert coordinator.calls[0][1]["plan_hash"] == expected_plan["plan_hash"]


def test_runner_injects_canonical_handoff_into_actual_scheduler(monkeypatch, tmp_path, capsys):
    sentinel = object()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        runner,
        "build_canonical_simple_publication_handoff",
        lambda *, store_path: captured.setdefault("store_path", store_path) and sentinel,
    )

    class StubScheduler:
        def __init__(self, **kwargs):
            captured.update(kwargs)

        def tick(self, *, now=None):
            return {
                "classification": "CONTROLLED",
                "tick_at_utc": now,
                "public_write_performed": False,
            }

    monkeypatch.setattr(runner, "SimpleGeminiLocalScheduler", StubScheduler)
    rc = runner.main(
        [
            "--scheduler-root",
            str(tmp_path / "scheduler"),
            "--published-memory-store",
            str(tmp_path / "store.sqlite3"),
            "--published-memory-output-root",
            str(tmp_path / "output"),
            "--tick-utc",
            "2026-08-30T04:30:00Z",
        ]
    )
    assert rc == 0
    assert captured["publication_handoff"] is sentinel
    assert captured["store_path"] == str(tmp_path / "store.sqlite3")
    assert "CONTROLLED" in capsys.readouterr().out
