from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from live_contentops import _eight_platform_substack_first_pipeline_impl_v1 as pipeline
from live_contentops.continuous_headline_ingest_v1 import (
    MAX_INTERVAL_SECONDS,
    run_ingestion_housekeeping_iteration,
)
from live_contentops.daily_app_supervisor_v1 import (
    ContentOpsDailyAppSupervisor,
    build_bootstrap_editorial_window_policy,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.editorial_portfolio_v1 import PublishedArticleRef
from live_contentops.preselection_canary_v1 import _bounded_canary_candidates
from live_contentops.preselection_intelligence_v1 import apply_preselection_intelligence
from live_contentops.published_corpus_read_model_v1 import load_published_corpus

NOW = datetime(2026, 8, 11, 3, 0, tzinfo=timezone.utc)


def _store(tmp_path: Path) -> ContentOpsDurableStore:
    return ContentOpsDurableStore(tmp_path / "contentops.sqlite3")


def _insert_lifecycle_article(
    store: ContentOpsDurableStore,
    output_dir: Path,
    *,
    work_item_id: str = "work-article-1",
    include_body: bool = True,
) -> str:
    body = "# Canonical article\n\nExact body bytes used by the canonical article payload."
    output_dir.mkdir(parents=True, exist_ok=True)
    if include_body:
        (output_dir / "article_manifest_v1.json").write_text(
            json.dumps({
                "title": "Canonical lifecycle article",
                "substack_body_markdown": body,
                "resolved_article_mode": "FOLLOW_UP_UPDATE",
                "update_chain_identity": "rolling-x-global-cluster-existing",
            }),
            encoding="utf-8",
        )
        (output_dir / "idea_selection_v1.json").write_text(
            json.dumps({
                "cluster_id": "rolling-x-global-cluster-existing",
                "update_chain_identity": "rolling-x-global-cluster-existing",
                "entities_topics": ["Federal Reserve", "inflation"],
            }),
            encoding="utf-8",
        )
    store.create_work_item(
        story_id="rolling-x-global-cluster-existing",
        title="Canonical lifecycle article",
        target_surface="daily_app_editorial_window",
        work_item_id=work_item_id,
    )
    destinations = (
        "substack", "telegram", "discord", "x", "linkedin", "facebook_page",
        "instagram_business", "threads", "youtube",
    )
    with store.get_connection() as conn:
        for index, destination in enumerate(destinations):
            suffix = f"article1-{index}"
            intent = {
                "schema_version": "contentops.prewrite_intent.v1",
                "work_item_id": work_item_id,
                "story_identity": "rolling-x-global-cluster-existing",
                "update_chain_identity": "rolling-x-global-cluster-existing",
                "article_identity": hashlib.sha256(body.encode("utf-8")).hexdigest(),
                "resolved_article_mode": "FOLLOW_UP_UPDATE",
                "output_dir": str(output_dir),
            }
            public_url = (
                "https://capitalchronicle.substack.com/p/canonical-lifecycle-article"
                if destination == "substack"
                else f"https://example.invalid/{destination}/{index}"
            )
            conn.execute(
                "INSERT INTO outbox_messages VALUES (?,?,?,?,?,?)",
                (
                    f"outbox_{suffix}", work_item_id, destination,
                    json.dumps(intent, sort_keys=True), "DISPATCH_CONFIRMED",
                    f"2026-08-11T02:{index:02d}:00Z",
                ),
            )
            conn.execute(
                "INSERT INTO platform_dispatches "
                "(dispatch_id,message_id,platform,status,dispatched_at,public_object_id,public_object_url,public_object_url_hash) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (
                    f"dispatch_{suffix}", f"outbox_{suffix}", destination,
                    "DISPATCH_CONFIRMED", f"2026-08-11T02:{index:02d}:30Z",
                    f"object-{index}", public_url,
                    hashlib.sha256(f"url-{index}".encode()).hexdigest(),
                ),
            )
            conn.execute(
                "INSERT INTO reconciliations VALUES (?,?,?,?)",
                (
                    f"reconciliation_{suffix}", work_item_id,
                    "RECONCILED_CONFIRMED", f"2026-08-11T02:{index:02d}:45Z",
                ),
            )
    return body


def test_corpus_uses_real_lifecycle_dedupes_fanout_and_recovers_exact_body(tmp_path):
    store = _store(tmp_path)
    body = _insert_lifecycle_article(store, tmp_path / "outputs" / "work-article-1")

    corpus = load_published_corpus(store)

    assert corpus["article_count"] == 1
    assert corpus["lifecycle_confirmed_derivative_count"] == 9
    article = corpus["articles"][0]
    assert article.full_text == body
    assert article.content_hash == hashlib.sha256(body.encode("utf-8")).hexdigest()
    assert article.content_status == "CONTENT_AVAILABLE"
    assert article.update_chain_identity == "rolling-x-global-cluster-existing"
    assert article.article_mode == "FOLLOW_UP_UPDATE"
    assert len(article.derivative_public_objects) == 9


def test_corpus_rejects_reconciled_substack_without_valid_canonical_url(tmp_path):
    store = _store(tmp_path)
    _insert_lifecycle_article(store, tmp_path / "outputs" / "work-article-1")
    with store.get_connection() as conn:
        conn.execute(
            "UPDATE platform_dispatches SET public_object_url=? WHERE platform='substack'",
            ("https://example.invalid/not-the-canonical-article",),
        )

    corpus = load_published_corpus(store)

    assert corpus["article_count"] == 0
    assert corpus["canonical_groups_without_substack_count"] == 1


def test_corpus_rejects_ui_display_string_and_marks_missing_content_unavailable(tmp_path):
    store = _store(tmp_path)
    _insert_lifecycle_article(
        store, tmp_path / "missing-body", work_item_id="work-missing", include_body=False
    )
    store.create_work_item(
        story_id="display-only", title="Display only", target_surface="test",
        work_item_id="work-display",
    )
    with store.get_connection() as conn:
        conn.execute(
            "INSERT INTO outbox_messages VALUES ('display-msg','work-display','substack','{}','READY','2026-08-11T00:00:00Z')"
        )
        conn.execute(
            "INSERT INTO platform_dispatches (dispatch_id,message_id,platform,status,dispatched_at,public_object_id) "
            "VALUES ('display-dispatch','display-msg','substack','REAL_PUBLICATION_CONFIRMED','2026-08-11T00:01:00Z','display-object')"
        )

    corpus = load_published_corpus(store)

    assert corpus["article_count"] == 1
    article = corpus["articles"][0]
    assert article.content_status == "CONTENT_UNAVAILABLE"
    assert article.full_text is None
    assert article.content_hash is None


def _published(
    identity: str,
    entities: tuple[str, ...],
    published_at: str,
    chain: str,
) -> PublishedArticleRef:
    return PublishedArticleRef(
        story_identity=identity,
        title=f"Prior {identity}",
        published_at_utc=published_at,
        public_object_id=f"object-{identity}",
        canonical_url_hash="url-hash",
        content_hash=hashlib.sha256(identity.encode()).hexdigest(),
        entities=entities,
        update_chain_identity=chain,
        article_mode="BREAKING_BRIEF",
        article_identity=f"article-{identity}",
        canonical_url=f"https://example.invalid/{identity}",
        full_text=f"Full prior body for {identity}",
        content_status="CONTENT_AVAILABLE",
    )


def test_supervisor_records_published_memory_before_after_and_canonical_observation(tmp_path):
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "memory-proof.sqlite3",
        output_root=tmp_path / "outputs",
        newsroom_cycle=lambda **_kwargs: {"classification": "NO_PUBLICATION"},
    )
    article = replace(
        _published(
            "new-story", ("Agency",), "2026-08-11T03:00:00Z", "chain-new"
        ),
        canonical_url="https://capitalchronicle.substack.com/p/new-story",
        source_work_item_id="window-proof-1",
    )
    proof = supervisor._record_published_memory_cycle_proof(
        output_dir=tmp_path / "outputs" / "window-proof-1",
        window={"window_id": "window-proof-1", "trigger_kind": "SCHEDULED"},
        before_runtime={
            "published_corpus": {
                "articles": [], "article_count": 0, "content_hash_coverage": 0,
            }
        },
        after_corpus={"articles": [article], "article_count": 1},
        cycle_evidence={
            "classification": "PASS_PUBLICATION_PLAN_READY",
            "article": {"resolved_article_mode": "BREAKING_BRIEF"},
            "ranked_viability": {
                "selected_cluster": {
                    "cluster_id": "new-story",
                    "update_chain_identity": "chain-new",
                    "resolved_article_mode": "BREAKING_BRIEF",
                    "portfolio_concentration_penalty": 0.0,
                }
            },
        },
        portfolio_context={"portfolio_state": {"published_today_count": 0}},
        novelty_decision={
            "decision": "BREAKING_NEW_STORY",
            "best_prior_article": None,
            "update_chain_match": False,
            "material_delta_signals": 0,
        },
        lifecycle={
            "canonical_article_status": "REAL_PUBLISHED",
            "canonical_publication_status": (
                "CANONICAL_PUBLISHED_DISTRIBUTION_PARTIAL"
            ),
            "canonical_url": article.canonical_url,
            "unknown_write_detected": False,
        },
    )

    assert proof["corpus_before_count"] == 0
    assert proof["corpus_after_count"] == 1
    assert proof["corpus_count_delta"] == 1
    assert proof["canonical_article_observed_after_lifecycle"]["story_identity"] == (
        "new-story"
    )
    assert proof["canonical_article_observed_after_lifecycle"]["content_hash"]
    assert proof["publication_lifecycle"]["canonical_article_status"] == "REAL_PUBLISHED"
    assert proof["proof_sha256"]
    persisted = json.loads(
        (tmp_path / "outputs" / "window-proof-1" / "published_memory_cycle_proof_v1.json")
        .read_text(encoding="utf-8")
    )
    assert persisted["proof_sha256"] == proof["proof_sha256"]


def test_supervisor_memory_proof_records_unchanged_no_publication_cycle(tmp_path):
    supervisor = ContentOpsDailyAppSupervisor(
        store_path=tmp_path / "memory-no-publication.sqlite3",
        output_root=tmp_path / "outputs",
        newsroom_cycle=lambda **_kwargs: {"classification": "NO_PUBLICATION"},
    )
    prior = _published(
        "prior-story", ("Agency",), "2026-08-11T02:00:00Z", "chain-prior"
    )
    corpus = {"articles": [prior], "article_count": 1, "content_hash_coverage": 1}

    proof = supervisor._record_published_memory_cycle_proof(
        output_dir=tmp_path / "outputs" / "window-proof-2",
        window={"window_id": "window-proof-2", "trigger_kind": "OPERATOR_REQUESTED"},
        before_runtime={"published_corpus": corpus},
        after_corpus=corpus,
        cycle_evidence={"classification": "NO_PUBLICATION"},
        portfolio_context={"portfolio_state": {"published_today_count": 1}},
        novelty_decision=None,
        lifecycle=None,
    )

    assert proof["corpus_before_count"] == proof["corpus_after_count"] == 1
    assert proof["corpus_count_delta"] == 0
    assert proof["no_publication_cycle"] is True
    assert proof["canonical_article_observed_after_lifecycle"] is None


def test_four_candidate_preselection_classifies_filters_and_changes_order(monkeypatch):
    corpus = [
        _published("fed-low", ("Federal Reserve", "rates"), "2026-08-11T01:00:00Z", "chain-low"),
        _published("cpi-follow", ("CPI", "inflation"), "2026-08-11T01:10:00Z", "chain-follow"),
        _published("treasury-old", ("Treasury", "auctions"), "2026-07-01T00:00:00Z", "chain-old"),
    ]
    clusters = [
        {"cluster_id": "breaking", "rank": 1, "headline_ids": ["h-break"], "entities_topics": ["OPEC", "oil"], "leaf_summaries": ["unexpected production decision"], "official_source_urls": []},
        {"cluster_id": "low", "update_chain_identity": "chain-low", "rank": 2, "headline_ids": ["h-low"], "entities_topics": ["Federal Reserve", "rates"], "leaf_summaries": ["same commentary again"], "official_source_urls": []},
        {"cluster_id": "follow", "update_chain_identity": "chain-follow", "rank": 3, "headline_ids": ["h-follow"], "entities_topics": ["CPI", "inflation"], "leaf_summaries": ["agency released new data and updated the estimate"], "official_source_urls": ["https://official.invalid/cpi"]},
        {"cluster_id": "deepen", "rank": 4, "headline_ids": ["h-deepen"], "entities_topics": ["Treasury", "auctions"], "leaf_summaries": ["historical structure angle"], "official_source_urls": []},
    ]

    def context(_catalog, entities):
        deep = "Treasury" in entities
        return {
            "cc_context_richness": 0.95 if deep else 0.0,
            "matched_store_ids": ["treasury_history"] if deep else [],
            "matched_store_count": 1 if deep else 0,
            "matches": [{"store_id": "treasury_history"}] if deep else [],
            "grants_factual_or_numeric_authority": False,
        }

    monkeypatch.setattr(
        "live_contentops.preselection_intelligence_v1.query_story_scoped_cc_context",
        context,
    )
    result = apply_preselection_intelligence(
        clusters,
        published_corpus=corpus,
        cc_catalog={"store_count_discovered": 14, "discovery_complete": True},
        now=NOW,
    )

    decisions = {
        row["cluster_id"]: row["editorial_classification"]
        for row in [*result["ranked_clusters"], *result["held_clusters"]]
    }
    assert decisions == {
        "breaking": "BREAKING_NEW_STORY",
        "low": "LOW_DELTA_REPEAT",
        "follow": "MATERIAL_FOLLOW_UP",
        "deepen": "DEEPEN_EXISTING_STORY",
    }
    assert [row["cluster_id"] for row in result["held_clusters"]] == ["low"]
    assert result["ranking_order_changed"] is True
    assert result["reranked_order"][0] == "deepen"
    modes = {row["cluster_id"]: row["resolved_article_mode"] for row in result["ranked_clusters"]}
    assert modes["breaking"] == "BREAKING_BRIEF"
    assert modes["follow"] == "FOLLOW_UP_UPDATE"
    assert modes["deepen"] == "CAPITAL_CHRONICLE_DEEP_DIVE"
    follow = next(row for row in result["ranked_clusters"] if row["cluster_id"] == "follow")
    delta = follow["material_follow_up_context"]
    assert delta["previous_story_identity"] == "cpi-follow"
    assert delta["previous_body_sha256"]
    assert delta["previous_full_text"] == "Full prior body for cpi-follow"
    assert delta["new_headline_ids"] == ["h-follow"]
    assert delta["material_delta_reason_codes"]
    assert result["occurs_before_targeted_evidence"] is True
    assert result["occurs_before_article_generation"] is True
    assert result["llm_or_provider_calls"] == 0


def test_material_event_priority_reranks_matching_eligible_update_without_new_authority(
    monkeypatch,
):
    monkeypatch.setattr(
        "live_contentops.preselection_intelligence_v1.query_story_scoped_cc_context",
        lambda _catalog, _entities: {
            "cc_context_richness": 0.0,
            "matched_store_ids": [],
            "matched_store_count": 0,
            "matches": [],
            "grants_factual_or_numeric_authority": False,
        },
    )
    clusters = [
        {
            "cluster_id": "normally-first", "rank": 1,
            "headline_ids": ["headline-normal"], "entities_topics": ["Rates"],
            "leaf_summaries": ["new official decision"],
        },
        {
            "cluster_id": "priority-chain", "update_chain_identity": "chain-priority",
            "rank": 2, "headline_ids": ["headline-priority"],
            "entities_topics": ["Inflation"],
            "leaf_summaries": ["new agency update"],
        },
    ]

    result = apply_preselection_intelligence(
        clusters,
        published_corpus=[],
        cc_catalog={"stores": []},
        material_event_priority={
            "priority_ids": ["material-priority-1"],
            "headline_ids": ["headline-priority"],
            "update_chain_identities": ["chain-priority"],
        },
        now=NOW,
    )

    assert result["reranked_order"] == ["priority-chain", "normally-first"]
    prioritized = result["ranked_clusters"][0]
    assert prioritized["material_event_priority_match"] is True
    assert prioritized["material_event_priority_bonus"] == 80.0
    assert prioritized["material_event_priority_ids"] == ["material-priority-1"]
    assert prioritized["material_event_priority_changes_eligibility_gates"] is False
    assert prioritized["material_event_priority_grants_factual_or_numeric_authority"] is False
    assert result["publication_authority_granted"] is False


def test_duplicate_corpus_rows_still_hold_repeat_and_allow_material_follow_up(
    monkeypatch,
):
    low_prior = _published(
        "fed-low", ("Federal Reserve", "rates"),
        "2026-08-11T01:00:00Z", "chain-low",
    )
    follow_prior = _published(
        "cpi-follow", ("CPI", "inflation"),
        "2026-08-11T01:10:00Z", "chain-follow",
    )
    monkeypatch.setattr(
        "live_contentops.preselection_intelligence_v1.query_story_scoped_cc_context",
        lambda _catalog, _entities: {
            "cc_context_richness": 0.0,
            "matched_store_ids": [],
            "matched_store_count": 0,
            "matches": [],
            "grants_factual_or_numeric_authority": False,
        },
    )

    result = apply_preselection_intelligence(
        [
            {
                "cluster_id": "low",
                "update_chain_identity": "chain-low",
                "rank": 1,
                "headline_ids": ["h-low"],
                "entities_topics": ["Federal Reserve", "rates"],
                "leaf_summaries": ["same commentary again"],
            },
            {
                "cluster_id": "follow",
                "update_chain_identity": "chain-follow",
                "rank": 2,
                "headline_ids": ["h-follow"],
                "entities_topics": ["CPI", "inflation"],
                "leaf_summaries": ["agency released new data and updated the estimate"],
                "official_source_urls": ["https://official.invalid/cpi"],
            },
        ],
        published_corpus=[low_prior, low_prior, follow_prior, follow_prior],
        cc_catalog={"stores": []},
        now=NOW,
    )

    assert [row["cluster_id"] for row in result["held_clusters"]] == ["low"]
    assert [row["cluster_id"] for row in result["ranked_clusters"]] == ["follow"]
    follow = result["ranked_clusters"][0]
    assert follow["editorial_classification"] == "MATERIAL_FOLLOW_UP"
    assert follow["resolved_article_mode"] == "FOLLOW_UP_UPDATE"
    assert follow["material_follow_up_context"]["previous_story_identity"] == (
        "cpi-follow"
    )


def test_read_only_canary_builds_bounded_distinct_real_candidate_projection():
    rows = [{
        "headline_id": f"headline-{index}",
        "source_timestamp_utc": f"2026-08-11T02:0{index}:00Z",
        "external_content": {
            "headline_text": text,
            "official_source_urls": [],
        },
    } for index, text in enumerate([
        "Treasury announces a new auction calendar update",
        "OPEC announces an unexpected production decision",
        "Federal Reserve publishes updated policy minutes",
        "Commerce Department releases a revised trade notice",
        "Congress schedules a new regulatory hearing",
    ])]
    candidates = _bounded_canary_candidates(rows, limit=4)
    assert len(candidates) == 4
    assert len({row["cluster_id"] for row in candidates}) == 4
    assert candidates[0]["headline_ids"] == ["headline-4"]
    assert all(row["canary_candidate_only"] is True for row in candidates)


def test_intake_delta_builds_stable_zero_llm_material_event(tmp_path):
    store = _store(tmp_path)

    def run(moment):
        return run_ingestion_housekeeping_iteration(
            store,
            now=moment,
            force=True,
            state_fn=lambda: {"state": "READY"},
            session_fn=lambda: {"session_state": "READY"},
            capture_fn=lambda **_kwargs: {
                "capture_state": "CAPTURED",
                "new_headlines": 2,
                "new_headline_ids": ["h2", "h1"],
                "new_headline_source_refs": [
                    {"headline_id": "h1", "headline_timestamp": "2026-08-11T02:00:00Z"},
                    {"headline_id": "h2", "headline_timestamp": "2026-08-11T02:01:00Z"},
                ],
            },
        )

    first = run(NOW)
    second = run(NOW + timedelta(minutes=1))
    assert first["material_event_due"] is True
    assert first["new_material_event_identity"] == second["new_material_event_identity"]
    assert first["llm_or_provider_calls"] == 0
    assert MAX_INTERVAL_SECONDS <= 300


def test_intake_delta_does_not_wake_for_out_of_window_source_event(tmp_path):
    result = run_ingestion_housekeeping_iteration(
        _store(tmp_path),
        now=NOW,
        force=True,
        state_fn=lambda: {"state": "READY"},
        session_fn=lambda: {"session_state": "READY"},
        capture_fn=lambda **_kwargs: {
            "capture_state": "CAPTURED",
            "new_headlines": 1,
            "new_headline_ids": ["stale-headline"],
            "new_headline_source_refs": [{
                "headline_id": "stale-headline",
                "headline_timestamp": "2026-08-01T00:00:00Z",
            }],
        },
    )
    assert result["material_event_due"] is False
    assert result["new_material_event_count"] == 0
    assert result["material_event_detail"] == "NO_SOURCE_EVENT_TIME_VALID_NEW_HEADLINES"


def _empty_runtime():
    return {
        "published_corpus": {
            "articles": [], "article_count": 0, "content_hash_coverage": 0,
            "full_text_article_count": 0, "content_unavailable_count": 0,
        },
        "cc_catalog": {
            "stores": [], "store_count_discovered": 0, "store_count_total": 0,
            "stores_omitted": 0, "discovery_complete": True, "root_exists": False,
        },
    }


def test_material_event_priority_is_durable_but_never_wakes_llm_across_kill_switch(tmp_path):
    store = _store(tmp_path)
    control = store.get_operating_control()
    store.update_operating_control(
        expected_state_version=control["state_version"],
        operating_mode="KILL_SWITCH",
        control_source="CONTROLLED_TEST",
    )
    event = {
        "lane_state": "RUNNING",
        "material_event_due": True,
        "new_material_event_count": 1,
        "new_material_event_identity": "headline-delta-stable-identity",
        "llm_or_provider_calls": 0,
    }
    policy = replace(build_bootstrap_editorial_window_policy(), core_windows=())
    calls: list[dict] = []
    first = ContentOpsDailyAppSupervisor(
        store_path=store.db_path,
        output_root=tmp_path / "outputs",
        store=store,
        operating_mode="KILL_SWITCH",
        policy=policy,
        intake_housekeeping=lambda *_args, **_kwargs: event,
        newsroom_cycle=lambda **kwargs: calls.append(kwargs) or {
            "classification": "NO_PUBLICATION", "public_write_performed": False,
            "unknown_write_detected": False,
        },
    )
    first._load_editorial_intelligence_runtime = _empty_runtime  # type: ignore[method-assign]
    report = first.tick(now=NOW)
    assert report["kill_switch_active"] is True
    assert report["material_event_wake"]["durable_idempotency"] is True
    assert calls == []

    control = store.get_operating_control()
    store.update_operating_control(
        expected_state_version=control["state_version"],
        operating_mode="AUTONOMOUS_DEFAULT",
        control_source="CONTROLLED_TEST",
    )
    second = ContentOpsDailyAppSupervisor(
        store_path=store.db_path,
        output_root=tmp_path / "outputs",
        store=store,
        operating_mode="AUTONOMOUS_DEFAULT",
        policy=policy,
        intake_housekeeping=lambda *_args, **_kwargs: {
            "lane_state": "RUNNING", "material_event_due": False,
            "llm_or_provider_calls": 0,
        },
        newsroom_cycle=lambda **kwargs: calls.append(kwargs) or {
            "classification": "NO_PUBLICATION", "public_write_performed": False,
            "unknown_write_detected": False,
        },
    )
    second._load_editorial_intelligence_runtime = _empty_runtime  # type: ignore[method-assign]
    resumed = second.tick(now=NOW + timedelta(minutes=1))
    repeated = second.tick(
        now=NOW + timedelta(minutes=2), materiality_metadata=event
    )
    assert resumed["newsroom_cycle_invocations"] == 0
    assert repeated["newsroom_cycle_invocations"] == 0
    assert len(calls) == 0
    queued = store.get_work_item(report["material_event_wake"]["window_id"])
    assert queued["current_state"] == "DISCOVERED"


def _shadow_article_and_media(tmp_path: Path):
    asset_ids = ("event_record", "timeline", "geography")
    assets = []
    for index, asset_id in enumerate(asset_ids):
        path = tmp_path / f"{asset_id}.png"
        path.write_bytes(f"fixture-{index}".encode())
        assets.append({
            "asset_id": asset_id, "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "caption": f"Fixture evidence visual {asset_id}.",
            "alt_text": f"Fixture visual {asset_id}",
            "source_label": "Controlled official fixture",
            "source_page_url": f"https://official.invalid/{asset_id}",
            "provenance_status": "VERIFIED",
        })
    body = "\n\n".join([
        "Controlled official evidence establishes a fixture event and its bounded context.",
        "[[VISUAL:event_record]]",
        "## What changed\nThe controlled record establishes the event facts.",
        "[[VISUAL:timeline]]",
        "## Why it matters\nThe controlled timeline explains the implementation path.",
        "[[VISUAL:geography]]",
        "## Limits\nThis is explicit fixture evidence, not a real-world claim.",
        "## What comes next\nA controlled official update is the next fixture catalyst.",
    ])
    article = {
        "title": "Controlled Official Fixture Update",
        "subtitle": "Fixture evidence demonstrates the governed article path without a public write.",
        "seo_title": "Controlled Official Fixture Update",
        "slug": "controlled-official-fixture-update",
        "meta_description": "Controlled official fixture evidence demonstrates the governed article and package path without any public write.",
        "substack_body_markdown": body,
        "market_mechanism": "The fixture timeline demonstrates the controlled mechanism.",
        "policy_context": "The fixture record defines the controlled implementation sequence.",
        "cross_asset_implications": "No real market implication is asserted by this fixture.",
        "cluster_id": "shadow-cluster",
        "headline_ids": ["shadow-headline"],
        "evidence_document_ids": ["fixture-doc"],
        "x_content_grants_factual_authority": False,
        "canonical_url": "https://capitalchronicle.substack.com/p/pending-publication",
        "social_lede": "Controlled fixture evidence establishes the update.",
        "social_mechanism_summary": "The fixture timeline explains the mechanism.",
        "social_policy_summary": "The controlled record defines the scope.",
        "social_cross_asset_summary": "No real market reaction is asserted.",
    }
    return article, {"assets": assets}


def test_full_canonical_shadow_reaches_article_review_and_platform_package(monkeypatch, tmp_path):
    assignment = {
        "schema_version": "capital_chronicle.rolling_x_newsroom_assignment.v1",
        "status": "SUCCESS",
        "decision": "SELECT_STORY",
        "ranked_clusters": [{
            "cluster_id": "shadow-cluster", "rank": 1,
            "headline_ids": ["shadow-headline"], "leaf_cluster_ids": [],
            "article_mode": "breaking", "story_mode": "breaking",
            "market_sensitive": False, "needed_evidence": ["official document"],
            "why_now": "Controlled fixture now.", "selection_case": "Controlled fixture.",
            "seo_intent": "controlled fixture", "visual_strategy": "controlled visuals",
        }],
        "leaf_clusters": [],
    }
    monkeypatch.setattr(
        "live_contentops.newsroom_assignment_scheduler_v1.assign_rolling_x_headlines_with_nine_router",
        lambda **_kwargs: assignment,
    )
    monkeypatch.setattr(
        "live_contentops.tier1_editorial_quality_v1.audit_tier1_article",
        lambda article, media_assets=(): {"classification": "PASS"},
    )
    article, media = _shadow_article_and_media(tmp_path)
    readiness = {
        "fixture_bound": True,
        "all_required_destinations_ready": True,
        "destinations": {
            "substack": {"write_eligible": True, "status": "READY_AUTHENTICATED"},
            "x": {"write_eligible": True, "status": "READY_AUTHENTICATED"},
            "threads": {"write_eligible": True, "status": "READY_NON_BROWSER_BINDING"},
        },
    }

    result = pipeline._run_rolling_x_newsroom_cycle(
        run_id="controlled-shadow-closeout",
        output_dir=tmp_path,
        cutoff_utc="2026-08-11T03:00:00Z",
        rolling_input={
            "schema_version": "capital_chronicle.rolling_x_headline_input.v1",
            "headlines": [],
        },
        story_type_by_cluster={"shadow-cluster": "regulatory_fiscal_event"},
        evidence_acquirer=lambda request: {
            "status": "PASS",
            "cluster_id": request["cluster_id"],
            "headline_ids": request["headline_ids"],
            "provided_evidence_capabilities": list(request["required_evidence_capabilities"]),
            "evidence_documents": [{
                "evidence_id": "fixture-doc",
                "source_url": "https://official.invalid/fixture-doc",
                "canonical_content_text": "Controlled fixture evidence only.",
            }],
                "capital_chronicle_authority_verified": False,
                "claim_evidence_contract": {
                    "status": "PASS", "supported_claim_count": 1,
                    "fabricated_claim_count": 0,
                    "supported_claims": [{"claim_id": "fixture-claim", "claim_text": "Controlled fixture evidence only.", "support_status": "SUPPORTED_PRIMARY"}],
                    "omitted_unsupported_claims": [],
                },
                "publication_authority": False,
        },
        article_builder=lambda _viability: {"article": article, "media": media},
        editorial_reviewer=lambda _article: {
            "status": "SUCCESS", "decision": "PASS", "mode": "straight_news",
            "issues": [], "publication_authority": False,
        },
        article_reviser=lambda value, _review, _round: value,
        publication_enabled=False,
        operating_mode="SHADOW_ONLY",
        published_corpus=[],
        cc_catalog={
            "stores": [], "store_count_discovered": 0,
            "discovery_complete": True, "root_exists": False,
        },
        destination_readiness_override=readiness,
    )

    assert result["classification"] == "NO_PUBLICATION"
    assert result["operating_mode"] == "SHADOW_ONLY"
    assert result["article"] is not None
    assert result["editorial_cycle"]["status"] == "PASS"
    assert result["platform_package_generated"] is True
    assert result["shadow_package_ready"] is True
    assert (tmp_path / "native_payloads_rehearsal_v1.json").is_file()
    assert result["publishing_adapter_called"] is False
    assert result["public_write_performed"] is False
    assert "publication_lifecycle_plan" not in result
    assert result["preselection_intelligence"]["occurs_before_targeted_evidence"] is True
