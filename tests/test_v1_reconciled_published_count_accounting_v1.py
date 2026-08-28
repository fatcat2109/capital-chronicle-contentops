from __future__ import annotations

from pathlib import Path

from live_contentops.editorial_portfolio_v1 import PublishedArticleRef
from live_contentops.newsroom_production_day_v1 import (
    LIVE_OUTPUT_COUNT_BASIS,
    STATE_DEFICIT_RECOVERABLE,
    STATE_FLOOR_MET,
    bounded_deficit_work_needed,
    build_current_zero_write_qualified_article_record,
    build_production_day_snapshot,
    newsroom_production_day_id,
    persist_qualified_article_record,
)
from live_contentops.published_corpus_read_model_v1 import (
    CANONICAL_PUBLICATION_CONTRACT,
    is_countable_canonical_published_article,
)
from live_contentops.v1_simple_gemini_scheduler_v1 import SimpleGeminiLocalScheduler

REFERENCE = "2026-08-28T16:00:00Z"


def _published(index: int, *, published_at: str = REFERENCE) -> PublishedArticleRef:
    return PublishedArticleRef(
        story_identity=f"published-story-{index}",
        title=f"Published story {index}",
        published_at_utc=published_at,
        public_object_id=f"substack-post-{index}",
        canonical_url_hash=f"hash-{index}",
        content_hash=None,
        entities=(),
        update_chain_identity=f"published-story-{index}",
        article_mode="BREAKING_BRIEF",
        article_identity=f"published-article-{index}",
        canonical_url=f"https://capitalchronicle.substack.com/p/published-{index}",
        source_work_item_id=f"work-{index}",
    )


def _qualified(root: Path, index: int) -> None:
    article = {
        "title": f"Qualified {index}",
        "substack_body_markdown": f"Qualified body {index}",
    }
    record = build_current_zero_write_qualified_article_record(
        production_day_id=newsroom_production_day_id(REFERENCE),
        parent_window_id=f"window-{index}",
        attempt_run_id=f"attempt-{index}",
        article=article,
        story_identity=f"qualified-story-{index}",
        update_chain_identity=f"qualified-story-{index}",
        resolved_article_mode="BREAKING_BRIEF",
        accepted_evidence_documents=[
            {
                "document_id": f"doc-{index}",
                "source_url": f"https://example.com/{index}",
                "canonical_content_sha256": "a" * 64,
                "published_at_utc": REFERENCE,
                "published_at_source": "CONTROLLED",
            }
        ],
        editorial_provider="9router",
        editorial_model="vx/gemini-3.5-flash(high)",
        editorial_reasoning_effort="HIGH",
        logical_model_invocation_count=2,
        derivative_package_intents=[],
    )
    persist_qualified_article_record(root / f"qualified-{index}", record)


def test_four_qualified_zero_published_is_not_live_floor_met(tmp_path):
    for index in range(4):
        _qualified(tmp_path, index)
    snapshot = build_production_day_snapshot(
        reference=REFERENCE,
        output_root=tmp_path,
        published_corpus=[],
        routine_opportunities_used_override=3,
    )
    assert snapshot.qualified_articles_today == 4
    assert snapshot.published_articles_today == 0
    assert snapshot.remaining_build_deficit == 0
    assert snapshot.remaining_published_deficit == 5
    assert snapshot.production_day_state == STATE_DEFICIT_RECOVERABLE
    assert snapshot.live_output_count_basis == CANONICAL_PUBLICATION_CONTRACT
    assert snapshot.to_dict()["remaining_published_deficit"] == 5


def test_five_strict_canonical_publications_meet_live_floor_without_using_qualified_count(tmp_path):
    snapshot = build_production_day_snapshot(
        reference=REFERENCE,
        output_root=tmp_path,
        published_corpus=[_published(index) for index in range(5)],
        routine_opportunities_used_override=4,
    )
    assert snapshot.qualified_articles_today == 0
    assert snapshot.remaining_build_deficit == 4
    assert snapshot.published_articles_today == 5
    assert snapshot.remaining_published_deficit == 0
    assert snapshot.production_day_state == STATE_FLOOR_MET
    assert snapshot.live_output_count_basis == LIVE_OUTPUT_COUNT_BASIS


def test_partial_or_noncanonical_projection_cannot_enter_live_count(tmp_path):
    valid = _published(1)
    invalid_url = PublishedArticleRef(
        **{
            **valid.__dict__,
            "article_identity": "invalid-url",
            "canonical_url": "https://example.com/p/not-canonical",
        }
    )
    missing_work_item = PublishedArticleRef(
        **{
            **valid.__dict__,
            "article_identity": "missing-work-item",
            "source_work_item_id": None,
        }
    )
    assert is_countable_canonical_published_article(valid) is True
    assert is_countable_canonical_published_article(invalid_url) is False
    assert is_countable_canonical_published_article(missing_work_item) is False
    snapshot = build_production_day_snapshot(
        reference=REFERENCE,
        output_root=tmp_path,
        published_corpus=[valid, invalid_url, missing_work_item],
        routine_opportunities_used_override=1,
    )
    assert snapshot.published_articles_today == 1
    assert snapshot.remaining_published_deficit == 4


def test_deficit_capacity_uses_published_count_not_qualified_telemetry():
    assert bounded_deficit_work_needed(
        session="new_york_2300_bangkok", published_articles_today=0
    ) == 4
    assert bounded_deficit_work_needed(
        session="new_york_2300_bangkok", published_articles_today=2
    ) == 2
    assert bounded_deficit_work_needed(
        session="new_york_2300_bangkok", published_articles_today=5
    ) == 1


def test_simple_scheduler_uses_strict_published_memory_for_slot_capacity(tmp_path):
    published = [_published(1), _published(2)]
    memory_calls: list[int] = []
    semantic_calls: list[str] = []

    def memory_loader():
        memory_calls.append(1)
        return published, {
            "schema_version": "contentops.v1_simple_published_memory_access.v1",
            "canonical_reconciled_article_count": 2,
            "canonical_publication_contract": CANONICAL_PUBLICATION_CONTRACT,
            "derived_from_existing_durable_truth": True,
            "store_access_mode": "SQLITE_MODE_RO_QUERY_ONLY",
            "auto_migrate": False,
            "production_store_unchanged_during_projection": True,
            "second_publication_store_created": False,
        }

    def abstain(**kwargs):
        semantic_calls.append(kwargs["run_id"])
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

    scheduler = SimpleGeminiLocalScheduler(
        scheduler_root=tmp_path,
        simple_operation=abstain,
        published_memory_loader=memory_loader,
    )
    result = scheduler.tick(now=REFERENCE)
    assert result["session"] == "new_york_2300_bangkok"
    assert result["published_articles_before_window"] == 2
    assert result["published_accounting_refresh_count"] == 1
    assert result["slot_capacity"] == 2
    assert len(semantic_calls) == 2
    assert len(memory_calls) == 3
