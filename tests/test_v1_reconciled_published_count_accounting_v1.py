from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

from live_contentops.destination_transport_registry_v1 import (
    V1_REQUIRED_DERIVATIVE_DESTINATIONS,
)
from live_contentops.editorial_portfolio_v1 import PublishedArticleRef
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.newsroom_production_day_v1 import (
    LIVE_OUTPUT_COUNT_BASIS,
    STATE_DEFICIT_RECOVERABLE,
    STATE_FLOOR_MET,
    bounded_deficit_work_needed,
    build_current_zero_write_qualified_article_record,
    build_production_day_snapshot,
    count_reconciled_published_articles,
    newsroom_production_day_id,
    persist_qualified_article_record,
)
from live_contentops.published_corpus_read_model_v1 import (
    CANONICAL_PUBLICATION_CONTRACT,
    DISPATCH_CONFIRMED,
    RECONCILED_CONFIRMED,
    is_countable_canonical_published_article,
    load_published_corpus,
)
from live_contentops.v1_simple_gemini_scheduler_v1 import SimpleGeminiLocalScheduler

REFERENCE = "2026-08-28T16:00:00Z"


def _canonical_row(
    index: int,
    *,
    public_object_id: str | None = None,
    canonical_url: str | None = None,
    canonical_url_hash: str | None = None,
    dispatch_status: str = DISPATCH_CONFIRMED,
    reconciliation_status: str = RECONCILED_CONFIRMED,
) -> dict:
    object_id = f"substack-post-{index}" if public_object_id is None else public_object_id
    url = (
        f"https://capitalchronicle.substack.com/p/published-{index}"
        if canonical_url is None
        else canonical_url
    )
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    if canonical_url_hash is not None:
        url_hash = canonical_url_hash
    return {
        "destination": "substack",
        "dispatch_id": f"dispatch-substack-{index}",
        "public_object_id": object_id,
        "public_object_url": url,
        "public_object_url_hash": url_hash,
        "dispatch_status": dispatch_status,
        "reconciliation_status": reconciliation_status,
    }


def _published(
    index: int,
    *,
    published_at: str = REFERENCE,
    article_identity: str | None = None,
    public_object_id: str | None = None,
    canonical_url: str | None = None,
    canonical_url_hash: str | None = None,
    source_work_item_id: str | None = None,
    dispatch_status: str = DISPATCH_CONFIRMED,
    reconciliation_status: str = RECONCILED_CONFIRMED,
    include_derivatives: bool = True,
) -> PublishedArticleRef:
    row = _canonical_row(
        index,
        public_object_id=public_object_id,
        canonical_url=canonical_url,
        canonical_url_hash=canonical_url_hash,
        dispatch_status=dispatch_status,
        reconciliation_status=reconciliation_status,
    )
    derivatives = [row]
    if include_derivatives:
        derivatives.extend(
            {
                "destination": destination,
                "dispatch_id": f"dispatch-{destination}-{index}",
                "public_object_id": f"{destination}-post-{index}",
                "public_object_url": f"https://public.example/{destination}/{index}",
                "public_object_url_hash": hashlib.sha256(
                    f"https://public.example/{destination}/{index}".encode()
                ).hexdigest(),
                "dispatch_status": DISPATCH_CONFIRMED,
                "reconciliation_status": RECONCILED_CONFIRMED,
            }
            for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
        )
    return PublishedArticleRef(
        story_identity=f"published-story-{index}",
        title=f"Published story {index}",
        published_at_utc=published_at,
        public_object_id=row["public_object_id"],
        canonical_url_hash=row["public_object_url_hash"],
        content_hash=None,
        entities=(),
        update_chain_identity=f"published-story-{index}",
        article_mode="BREAKING_BRIEF",
        article_identity=(
            f"published-article-{index}" if article_identity is None else article_identity
        ),
        canonical_url=row["public_object_url"],
        source_work_item_id=(f"work-{index}" if source_work_item_id is None else source_work_item_id),
        derivative_public_objects=tuple(derivatives),
    )


def _qualified(root: Path, index: int) -> None:
    article = {
        "title": f"Qualified {index}",
        "substack_body_markdown": f"Qualified body {index}",
    }
    body_hash = hashlib.sha256(article["substack_body_markdown"].encode()).hexdigest()
    intents = [
        {
            "destination": destination,
            "dispatch_state": "UNDISPATCHED",
            "article_identity": body_hash,
        }
        for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS
    ]
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
        derivative_package_intents=intents,
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


def test_five_strict_canonical_publications_meet_live_floor_without_qualified_count(tmp_path):
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


def test_invalid_or_incomplete_canonical_lifecycle_never_counts(tmp_path):
    valid = _published(1)
    invalid = [
        _published(2, canonical_url="https://example.com/p/not-canonical"),
        _published(3, canonical_url="https://capitalchronicle.substack.com/p/pending-publication-abc"),
        _published(4, public_object_id=""),
        _published(5, canonical_url_hash=""),
        _published(6, canonical_url_hash="not-the-url-hash"),
        _published(7, source_work_item_id=""),
        _published(8, dispatch_status="UNKNOWN_WRITE"),
        _published(9, reconciliation_status="RECONCILIATION_PENDING"),
        _published(10, reconciliation_status="RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE"),
        _published(
            11,
            reconciliation_status="RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE",
            include_derivatives=False,
        ),
    ]
    assert is_countable_canonical_published_article(valid) is True
    assert all(not is_countable_canonical_published_article(row) for row in invalid)
    snapshot = build_production_day_snapshot(
        reference=REFERENCE,
        output_root=tmp_path,
        published_corpus=[valid, *invalid],
        routine_opportunities_used_override=1,
    )
    assert snapshot.published_articles_today == 1


def _seed_durable_publication(
    store: ContentOpsDurableStore,
    *,
    suffix: str,
    article_identity: str,
    destination: str = "substack",
    dispatch_status: str = DISPATCH_CONFIRMED,
    reconciliation_status: str | None = RECONCILED_CONFIRMED,
    public_object_id: str | None = None,
    public_object_url: str | None = None,
) -> None:
    work_item_id = f"work-{suffix}"
    message_id = f"outbox-{suffix}"
    dispatch_id = f"dispatch_{suffix}"
    store.create_work_item(
        story_id=f"story-{suffix}",
        title=f"Story {suffix}",
        target_surface="MULTI_PLATFORM",
        work_item_id=work_item_id,
    )
    store.register_outbox_message(
        message_id=message_id,
        work_item_id=work_item_id,
        destination=destination,
        payload=json.dumps(
            {
                "schema_version": "contentops.prewrite_intent.v1",
                "work_item_id": work_item_id,
                "story_identity": f"story-{suffix}",
                "article_identity": article_identity,
            },
            sort_keys=True,
        ),
        status="READY",
    )
    store.register_platform_dispatch(
        dispatch_id=dispatch_id,
        message_id=message_id,
        platform=destination,
        status=dispatch_status,
        public_object_id=public_object_id,
        public_object_url=public_object_url,
    )
    if reconciliation_status is not None:
        store.register_reconciliation(
            reconciliation_id="reconciliation_" + suffix,
            work_item_id=work_item_id,
            status=reconciliation_status,
        )


def test_durable_read_model_is_the_only_count_source_and_rejects_partial_rows(tmp_path):
    store = ContentOpsDurableStore(tmp_path / "disposable.sqlite3")
    canonical_url = "https://capitalchronicle.substack.com/p/durable-canonical"
    _seed_durable_publication(
        store,
        suffix="canonical",
        article_identity="article-canonical",
        public_object_id="substack-canonical-id",
        public_object_url=canonical_url,
    )
    for destination in V1_REQUIRED_DERIVATIVE_DESTINATIONS:
        _seed_durable_publication(
            store,
            suffix="canonical-" + destination,
            article_identity="article-canonical",
            destination=destination,
            public_object_id=f"{destination}-id",
            public_object_url=f"https://public.example/{destination}/1",
        )
    _seed_durable_publication(
        store,
        suffix="unreconciled",
        article_identity="article-unreconciled",
        reconciliation_status="RECONCILIATION_PENDING",
        public_object_id="substack-unreconciled-id",
        public_object_url=(
            "https://capitalchronicle.substack.com/p/unreconciled"
        ),
    )
    _seed_durable_publication(
        store,
        suffix="partial",
        article_identity="article-partial",
        reconciliation_status="RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE",
        public_object_id="substack-partial-id",
        public_object_url="https://capitalchronicle.substack.com/p/partial",
    )
    _seed_durable_publication(
        store,
        suffix="unknown",
        article_identity="article-unknown",
        dispatch_status="UNKNOWN_WRITE",
        reconciliation_status="RECONCILIATION_PENDING",
        public_object_id="substack-unknown-id",
        public_object_url="https://capitalchronicle.substack.com/p/unknown",
    )
    _seed_durable_publication(
        store,
        suffix="controlled-no-write",
        article_identity="article-controlled-no-write",
        dispatch_status="CONTROLLED_NO_PUBLIC_WRITE",
        reconciliation_status="RECONCILED_CONTROLLED_NO_WRITE",
    )
    _seed_durable_publication(
        store,
        suffix="pending-placeholder",
        article_identity="article-pending-placeholder",
        public_object_id="substack-pending-id",
        public_object_url=(
            "https://capitalchronicle.substack.com/p/pending-publication-fixture"
        ),
    )

    corpus = load_published_corpus(store)

    assert corpus["article_count"] == 1
    assert corpus["articles"][0].article_identity == "article-canonical"
    assert len(corpus["articles"][0].derivative_public_objects) == 9
    assert corpus["canonical_publication_contract"] == CANONICAL_PUBLICATION_CONTRACT
    assert corpus["derived_from_existing_durable_truth"] is True
    assert corpus["second_publication_store_created"] is False
    assert [path.name for path in tmp_path.glob("*.sqlite3")] == [
        "disposable.sqlite3"
    ]


def test_derivatives_never_inflate_and_article_identity_dedupes_deterministically():
    first = _published(1, article_identity="same-article")
    duplicate = _published(2, article_identity="same-article")
    assert len(first.derivative_public_objects) == 9
    assert count_reconciled_published_articles(
        [first, duplicate],
        production_day_id=newsroom_production_day_id(REFERENCE),
    ) == 1


def test_bangkok_cross_midnight_published_count_semantics_are_unchanged(tmp_path):
    following_0100 = _published(1, published_at="2026-08-28T18:00:00Z")
    next_production_day = _published(2, published_at="2026-08-28T19:00:00Z")
    snapshot = build_production_day_snapshot(
        reference="2026-08-28T18:30:00Z",
        output_root=tmp_path,
        published_corpus=[following_0100, next_production_day],
        routine_opportunities_used_override=4,
    )
    assert snapshot.newsroom_production_day_id == "newsroom-production-day-2026-08-28-bangkok"
    assert snapshot.published_articles_today == 1


def test_deficit_capacity_uses_published_count_not_qualified_telemetry():
    assert bounded_deficit_work_needed(session="new_york_2300_bangkok", published_articles_today=0) == 4
    assert bounded_deficit_work_needed(session="new_york_2300_bangkok", published_articles_today=2) == 2
    assert bounded_deficit_work_needed(session="new_york_2300_bangkok", published_articles_today=5) == 1


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
            "logical_model_invocation_count": 0,
            "provider_attempt_count": 0,
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
    assert result["live_output_count_basis"] == LIVE_OUTPUT_COUNT_BASIS
    assert result["slot_capacity"] == 2
    assert result["routine_editorial_owner"] == "SIMPLE_GEMINI_RUNTIME"
    assert result["native_desktop_routine_invocation_count"] == 0
    assert result["legacy_rolling_x_routine_invocation_count"] == 0
    assert result["gemini_logical_call_count"] == 0
    assert result["source_get_count"] == 0
    assert result["provider_publication_writes"] == 0
    assert result["public_write_performed"] is False
    assert result["unknown_write_count"] == 0
    assert len(semantic_calls) == 2
    assert len(memory_calls) == 3


def test_qualified_memory_remains_duplicate_suppression_only(tmp_path):
    _qualified(tmp_path, 1)
    qualified_only = replace(
        _published(1),
        public_object_id=None,
        canonical_url=None,
        canonical_url_hash=None,
        source_work_item_id=None,
        derivative_public_objects=(),
    )
    assert is_countable_canonical_published_article(qualified_only) is False
    snapshot = build_production_day_snapshot(
        reference=REFERENCE,
        output_root=tmp_path,
        published_corpus=[qualified_only],
        routine_opportunities_used_override=1,
    )
    assert snapshot.qualified_articles_today == 1
    assert snapshot.published_articles_today == 0
