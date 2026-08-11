from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from live_contentops import continuous_headline_ingest_v1 as intake
from live_contentops import x_list_ingest_capture_v1 as capture
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.editorial_portfolio_v1 import (
    DECISION_BREAKING_NEW_STORY,
    DECISION_DEEPEN_EXISTING_STORY,
    DECISION_LOW_DELTA_REPEAT,
    DECISION_MATERIAL_FOLLOW_UP,
    PublishedArticleRef,
    bootstrap_portfolio_policy,
    classify_story_novelty,
    concentration_penalty,
    portfolio_state_today,
)
from live_contentops.published_corpus_read_model_v1 import load_published_corpus

FIXED_NOW = datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc)


def _store(tmp_path: Path) -> ContentOpsDurableStore:
    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    assert store.get_current_schema_version() == 9
    return store


def _sidecar_row(tweet_id: str, text: str, timestamp: str) -> str:
    return json.dumps({
        "schema_version": "step1_headline_catalyst_sidecar_v1",
        "headline_id": f"h-{tweet_id}",
        "headline_text": text,
        "headline_timestamp": timestamp,
        "source_platform": "x_cdp_list_latest_tweets_timeline",
        "captured_at_utc": "2026-08-10T11:00:00Z",
        "author_handle": "watcher_guru",
        "dedup_key": f"tweet_id:{tweet_id}",
        "text_sha256": f"sha-{tweet_id}",
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _write_sidecar(directory: Path, date_key: str, rows: list[str]) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"step1_headline_sidecar_{date_key}.jsonl"
    with open(path, "a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(row + "\n")
    return path


# --- A. Continuous ingestion: multiple bounded iterations, deterministic dedupe -------------


def test_three_iterations_append_only_genuinely_new_headlines(tmp_path):
    sidecar_dir = tmp_path / "headline_ingestion" / "data" / "intake" / "headline_sidecars"
    module = capture.load_data_ingestion_module()
    module.SIDECAR_DIR = str(sidecar_dir)

    def tweet(tweet_id: str, text: str):
        return {
            "timestamp": "2026-08-10 18:00:00 GMT+7",
            "text": text,
            "tweet_id": tweet_id,
            "author_handle": "watcher_guru",
            "tweet_url": f"https://x.com/watcher_guru/status/{tweet_id}",
            "created_at_raw": "Mon Aug 10 11:00:00 +0000 2026",
        }

    first = capture.append_deduped_sidecar_rows(module, [tweet("1", "Fed holds rates"), tweet("2", "Oil slips")])
    second = capture.append_deduped_sidecar_rows(module, [tweet("1", "Fed holds rates"), tweet("2", "Oil slips"), tweet("3", "Gold rallies")])
    third = capture.append_deduped_sidecar_rows(module, [tweet("3", "Gold rallies"), tweet("4", "Dollar steadies")])
    assert (first, second, third) == (2, 1, 1)
    files = sorted(sidecar_dir.glob("*.jsonl"))
    assert len(files) == 1
    assert files[0].name.startswith("step1_headline_sidecar_")
    rows = [json.loads(line) for line in files[0].read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 4
    assert len({row["dedup_key"] for row in rows}) == 4
    assert all(row["headline_timestamp"] for row in rows)


def test_checkpoint_roundtrip_and_adaptive_backoff(tmp_path):
    store = _store(tmp_path)
    checkpoint = intake.read_ingestion_checkpoint(store)
    assert checkpoint["last_success_epoch"] is None
    assert checkpoint["consecutive_empty"] == 0
    intake.write_ingestion_checkpoint(
        store,
        now=FIXED_NOW,
        last_success_epoch=FIXED_NOW.timestamp(),
        outcome_code=intake.OUTCOME_CAPTURED_NEW,
        consecutive_empty=0,
        rows_iteration=12,
    )
    checkpoint = intake.read_ingestion_checkpoint(store)
    assert checkpoint["last_success_epoch"] == FIXED_NOW.timestamp()
    assert checkpoint["rows_last_iteration"] == 12
    assert intake.next_due_interval_seconds(0) == intake.ACTIVE_INTERVAL_SECONDS
    assert intake.next_due_interval_seconds(1) <= 300
    assert intake.next_due_interval_seconds(10) <= intake.MAX_INTERVAL_SECONDS
    assert intake.MAX_INTERVAL_SECONDS <= 300
    assert intake.ingestion_lane_state(intake.OUTCOME_REAUTH_REQUIRED) == "REAUTH_REQUIRED"
    assert intake.ingestion_lane_state(intake.OUTCOME_PORT_OWNER_UNPROVEN) == "UNAVAILABLE"
    assert intake.ingestion_lane_state(intake.OUTCOME_CAPTURED_NEW) == "RUNNING"


def test_housekeeping_iteration_not_due_skips_capture(tmp_path):
    store = _store(tmp_path)
    calls = []

    intake.write_ingestion_checkpoint(
        store,
        now=FIXED_NOW,
        last_success_epoch=(FIXED_NOW - timedelta(seconds=60)).timestamp(),
        outcome_code=intake.OUTCOME_CAPTURED_NEW,
        consecutive_empty=0,
        rows_iteration=3,
    )
    result = intake.run_ingestion_housekeeping_iteration(
        store,
        now=FIXED_NOW,
        state_fn=lambda: {"state": "READY"},
        session_fn=lambda: {"session_state": "READY"},
        capture_fn=lambda **kwargs: calls.append(kwargs) or {"capture_state": "CAPTURED", "new_headlines": 1},
    )
    assert result["detail"] == "not_due"
    assert result["capture_attempted"] is False
    assert calls == []
    assert intake.ingestion_lane_state(intake.read_ingestion_checkpoint(store)["last_outcome_code"]) == "RUNNING"


def test_housekeeping_iteration_reauth_reports_and_waits(tmp_path):
    store = _store(tmp_path)
    result = intake.run_ingestion_housekeeping_iteration(
        store,
        now=FIXED_NOW,
        force=True,
        state_fn=lambda: {"state": "READY"},
        session_fn=lambda: {"session_state": "REAUTH_REQUIRED", "detail": "LOGIN_REDIRECT_OBSERVED"},
        capture_fn=lambda **kwargs: (_ for _ in ()).throw(AssertionError("capture attempted despite reauth")),
    )
    assert result["lane_state"] == "REAUTH_REQUIRED"
    assert result["detail"] == "LOGIN_REDIRECT_OBSERVED"
    assert intake.read_ingestion_checkpoint(store)["last_outcome_code"] == intake.OUTCOME_REAUTH_REQUIRED
    second = intake.run_ingestion_housekeeping_iteration(
        store,
        now=FIXED_NOW + timedelta(seconds=60),
        state_fn=lambda: {"state": "READY"},
        session_fn=lambda: {"session_state": "REAUTH_REQUIRED"},
        capture_fn=lambda **kwargs: (_ for _ in ()).throw(AssertionError("capture attempted despite reauth")),
    )
    assert second["detail"] == "reauth_required_waiting_for_operator"


def test_housekeeping_iteration_fails_closed_on_unproven_owner(tmp_path):
    store = _store(tmp_path)
    result = intake.run_ingestion_housekeeping_iteration(
        store,
        now=FIXED_NOW,
        force=True,
        state_fn=lambda: {"state": "PORT_OWNER_UNPROVEN"},
        session_fn=lambda: {"session_state": "READY"},
        capture_fn=lambda **kwargs: {"capture_state": "CAPTURED", "new_headlines": 1},
    )
    assert result["lane_state"] == "UNAVAILABLE"
    assert result["detail"] == "PORT_OWNER_UNPROVEN_FAIL_CLOSED"
    assert result["capture_attempted"] is False
    assert intake.read_ingestion_checkpoint(store)["last_outcome_code"] == intake.OUTCOME_PORT_OWNER_UNPROVEN


def test_housekeeping_iteration_zero_llm_calls(tmp_path):
    store = _store(tmp_path)
    result = intake.run_ingestion_housekeeping_iteration(
        store,
        now=FIXED_NOW,
        force=True,
        state_fn=lambda: {"state": "READY"},
        session_fn=lambda: {"session_state": "READY"},
        capture_fn=lambda **kwargs: {"capture_state": "CAPTURED", "new_headlines": 2},
    )
    assert result["llm_or_provider_calls"] == 0
    assert result["rows_added"] == 2
    assert result["lane_state"] == "RUNNING"


# --- B. Restart safety: checkpoint durable, no duplicate headlines ---------------------------


def test_restart_reconstruction_no_duplicate_headlines(tmp_path):
    store_path = tmp_path / "store.sqlite3"
    store = ContentOpsDurableStore(store_path)
    intake.write_ingestion_checkpoint(
        store,
        now=FIXED_NOW,
        last_success_epoch=FIXED_NOW.timestamp(),
        outcome_code=intake.OUTCOME_CAPTURED_NEW,
        consecutive_empty=0,
        rows_iteration=5,
    )
    del store
    reopened = ContentOpsDurableStore(store_path)
    checkpoint = intake.read_ingestion_checkpoint(reopened)
    assert checkpoint["last_success_epoch"] == FIXED_NOW.timestamp()
    assert checkpoint["consecutive_empty"] == 0
    sidecar_dir = tmp_path / "sidecars"
    module = capture.load_data_ingestion_module()
    module.SIDECAR_DIR = str(sidecar_dir)

    def tweet(tweet_id, text):
        return {"timestamp": "2026-08-10 18:00:00 GMT+7", "text": text, "tweet_id": tweet_id, "created_at_raw": "Mon Aug 10 11:00:00 +0000 2026"}

    capture.append_deduped_sidecar_rows(module, [tweet("9", "Restart test headline")])
    capture.append_deduped_sidecar_rows(module, [tweet("9", "Restart test headline")])
    files = list(Path(module.SIDECAR_DIR).glob("*.jsonl"))
    rows = [json.loads(line) for line in files[0].read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1


# --- C. Rolling 24h universe reconstructed from ALL unique headlines ------------------------


def test_rolling_24h_reconstructs_full_universe_across_files(tmp_path, monkeypatch):
    sidecar_dir = tmp_path / "headline_ingestion" / "data" / "headline_sidecars"
    fresh_cutoff = datetime(2026, 8, 10, 12, 0, 0, tzinfo=timezone.utc)
    _write_sidecar(sidecar_dir, "2026_08_09", [
        _sidecar_row("100", "Old but within window", "2026-08-09 20:00:00 GMT+7"),
        _sidecar_row("101", "Too old for window", "2026-08-07 10:00:00 GMT+7"),
    ])
    _write_sidecar(sidecar_dir, "2026_08_10", [
        _sidecar_row("100", "Old but within window", "2026-08-09 20:00:00 GMT+7"),
        _sidecar_row("200", "Fresh morning headline", "2026-08-10 15:00:00 GMT+7"),
    ])
    from live_contentops.newsroom_assignment_scheduler_v1 import load_rolling_x_headline_sidecars

    intake_result = load_rolling_x_headline_sidecars(
        cutoff_utc=fresh_cutoff,
        sidecar_glob=str(sidecar_dir / "*.jsonl"),
        window_hours=24.0,
    )
    headlines = intake_result.get("headlines") or []
    texts = sorted(row["external_content"]["headline_text"] for row in headlines)
    assert texts == ["Fresh morning headline", "Old but within window"]
    counts = intake_result.get("counts") or {}
    assert int(counts.get("duplicates") or 0) >= 1
    assert int(counts.get("rejected") or 0) >= 1
    assert intake_result.get("complete_input_coverage") is True
    count = intake.rolling_24h_unique_headline_count(
        sidecar_glob=str(sidecar_dir / "*.jsonl"), now=fresh_cutoff
    )
    assert count == 2


# --- D. Capital Chronicle read-only catalog ---------------------------------------------------


def test_cc_catalog_is_read_only_and_compact(tmp_path):
    duckdb = pytest.importorskip("duckdb")
    db_dir = tmp_path / "Main App" / "data" / "local_db"
    db_dir.mkdir(parents=True)
    docs_dir = tmp_path / "Main App" / "docs" / "research" / "publication_evidence" / "current"
    docs_dir.mkdir(parents=True)
    (docs_dir / "CapitalChroniclePublicationEvidencePacketV1.json").write_text("{}", encoding="utf-8")
    database = duckdb.connect(str(db_dir / "event_entity_history_v1.duckdb"))
    database.execute("CREATE TABLE entity_version (entity_id INTEGER, display_name VARCHAR, known_at TIMESTAMP)")
    database.execute("INSERT INTO entity_version VALUES (1, 'Federal Reserve', '2026-08-10 01:00:00'), (2, 'OPEC', '2026-08-10 02:00:00')")
    database.close()

    from live_contentops.capital_chronicle_data_catalog_v1 import (
        discover_cc_data_estate,
        query_story_scoped_cc_context,
    )

    catalog = discover_cc_data_estate(cc_root=tmp_path / "Main App")
    assert catalog["root_exists"] is True
    assert catalog["mutated_upstream"] is False
    assert catalog["governed_surfaces"]["publication_evidence_packet"]["exists"] is True
    stores = catalog["stores"]
    assert len(stores) == 1
    assert stores[0]["store_id"] == "event_entity_history_v1"
    assert stores[0]["opened_read_only"] is True
    tables = stores[0]["tables"]
    assert tables[0]["table"] == "entity_version"
    assert tables[0]["content_rows_scanned_during_discovery"] == 0
    assert catalog["discovery_complete"] is True
    assert catalog["stores_omitted"] == 0

    context = query_story_scoped_cc_context(catalog, ["Federal Reserve", "Unknown Entity Xyz"])
    assert context["mutated_upstream"] is False
    assert context["grants_factual_or_numeric_authority"] is False
    assert context["cc_context_richness"] > 0.0
    matched_entities = {row["matched_entity"] for row in context["matches"]}
    assert "Federal Reserve" in matched_entities
    database2 = duckdb.connect(str(db_dir / "event_entity_history_v1.duckdb"), read_only=True)
    assert database2.execute("SELECT COUNT(*) FROM entity_version").fetchone()[0] == 2
    database2.close()


# --- E. Published corpus read model -----------------------------------------------------------


def test_published_corpus_derives_from_existing_durable_truth(tmp_path):
    store = _store(tmp_path)
    corpus = load_published_corpus(store, output_root=tmp_path / "outputs")
    assert corpus["article_count"] == 0
    assert corpus["derived_from_existing_durable_truth"] is True
    assert corpus["second_publication_store_created"] is False


def test_published_corpus_with_confirmed_publication(tmp_path):
    store = _store(tmp_path)
    with store.get_connection() as conn:
        conn.execute("INSERT INTO work_items (work_item_id,story_id,title,current_state,state_version,target_surface,created_at,updated_at)"
                     " VALUES ('wi-article','story-1','Fed decision day recap','COMPLETE',1,'daily_app_editorial_window','2026-08-10T09:00:00Z','2026-08-10T09:05:00Z')")
        conn.execute(
            "INSERT INTO outbox_messages (message_id, work_item_id, destination, payload, status, created_at)"
            " VALUES ('msg1','wi-article','substack','{}','READY','2026-08-10T09:00:00Z')"
        )
        conn.execute(
            "INSERT INTO platform_dispatches (dispatch_id,message_id,platform,status,dispatched_at,public_object_id)"
            " VALUES ('disp1','msg1','substack','DISPATCH_CONFIRMED','2026-08-10T09:05:00Z','object-123')"
        )
        conn.execute(
            "INSERT INTO reconciliations (reconciliation_id,work_item_id,status,reconciled_at)"
            " VALUES ('reconciliation_disp1','wi-article','RECONCILED_CONFIRMED','2026-08-10T09:06:00Z')"
        )
    corpus = load_published_corpus(store, output_root=tmp_path / "outputs")
    assert corpus["article_count"] == 1
    article = corpus["articles"][0]
    assert article.story_identity == "story-1"
    assert article.public_object_id == "object-123"
    assert article.published_at_utc == "2026-08-10T09:05:00Z"
    assert article.content_status == "CONTENT_UNAVAILABLE"
    assert article.content_hash is None
    state = portfolio_state_today(corpus["articles"], now=datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc))
    assert state["published_today_count"] == 1
    assert state["daily_target_band"] == [5, 8]


# --- F. Breaking vs follow-up classification ---------------------------------------------------


def _article(story_id="wi-prev", entities=("Federal Reserve", "rates"), published="2026-08-10T02:00:00Z", chain=None) -> PublishedArticleRef:
    return PublishedArticleRef(
        story_identity=story_id,
        title="Prior coverage",
        published_at_utc=published,
        public_object_id="obj-1",
        canonical_url_hash="url-hash",
        content_hash="content-hash",
        entities=entities,
        update_chain_identity=chain,
        article_mode=None,
    )


def test_breaking_new_story_when_corpus_has_no_overlap():
    cluster = {"entities_topics": ["OPEC", "crude output"], "leaf_summaries": [], "official_source_urls": []}
    decision = classify_story_novelty(cluster, published_corpus=[_article()], now=FIXED_NOW)
    assert decision["decision"] == DECISION_BREAKING_NEW_STORY
    assert decision["recommended_article_mode"] == "BREAKING_BRIEF"
    assert decision["grants_factual_or_numeric_authority"] is False


def test_material_follow_up_with_delta():
    cluster = {
        "entities_topics": ["Federal Reserve", "rates"],
        "leaf_summaries": ["Fed updated guidance; new data confirmed"],
        "official_source_urls": ["https://federalreserve.gov/newstatement"],
        "update_chain_identity": "chain-fed-1",
    }
    decision = classify_story_novelty(
        cluster,
        published_corpus=[_article(chain="chain-fed-1")],
        now=FIXED_NOW,
    )
    assert decision["decision"] == DECISION_MATERIAL_FOLLOW_UP
    assert decision["recommended_article_mode"] == "FOLLOW_UP_UPDATE"
    assert decision["update_chain_match"] is True


def test_low_delta_repeat_without_material_delta():
    cluster = {
        "entities_topics": ["Federal Reserve", "rates"],
        "leaf_summaries": ["same commentary again"],
        "official_source_urls": [],
        "update_chain_identity": "chain-fed-1",
    }
    decision = classify_story_novelty(
        cluster,
        published_corpus=[_article(chain="chain-fed-1")],
        now=FIXED_NOW,
    )
    assert decision["decision"] == DECISION_LOW_DELTA_REPEAT


def test_deepen_existing_story_with_cc_context():
    cluster = {
        "entities_topics": ["Federal Reserve", "rates"],
        "leaf_summaries": ["fresh angle"],
        "official_source_urls": [],
    }
    decision = classify_story_novelty(
        cluster,
        published_corpus=[_article(published="2026-08-01T02:00:00Z")],
        cc_context_richness=0.8,
        now=FIXED_NOW,
    )
    assert decision["decision"] == DECISION_DEEPEN_EXISTING_STORY
    assert decision["recommended_article_mode"] == "CAPITAL_CHRONICLE_DEEP_DIVE"


# --- G. Portfolio policy and concentration ---------------------------------------------------


def test_bootstrap_policy_supports_5_8_target():
    policy = bootstrap_portfolio_policy()
    assert policy["daily_target_band"] == [5, 8]
    assert policy["core_decision_opportunities_per_day"] == 8
    assert policy["material_event_wakeups_enabled"] is True
    assert policy["filler_fabrication_permitted"] is False
    assert policy["weakened_factual_or_numeric_authority_permitted"] is False

    from live_contentops.daily_app_supervisor_v1 import build_bootstrap_editorial_window_policy

    window_policy = build_bootstrap_editorial_window_policy()
    assert len(window_policy.core_windows) == 8
    assert window_policy.policy_version == "bootstrap.v2"
    assert window_policy.daily_publication_target_band == (5, 8)
    assert window_policy.material_event_override_enabled is True
    assert window_policy.minimum_cycle_spacing_hours <= 2.0


def test_concentration_penalty_rises_with_repeated_coverage():
    portfolio = {"entity_concentration_top": [{"entity": "federal reserve", "count": 3}]}
    low = concentration_penalty(["OPEC"], portfolio)
    high = concentration_penalty(["Federal Reserve"], portfolio)
    assert low == 0.0
    assert high > 0.5


# --- H. Run Now canonical path (shadow, no bypass) -------------------------------------------


def test_run_now_consumes_through_same_canonical_cycle_with_fallback_sync_only(tmp_path):
    from tests.test_daily_app_operator_trigger_v1 import _supervisor as supervisor_factory

    supervisor, calls = supervisor_factory(tmp_path, mode="SHADOW_ONLY")
    supervisor._store.record_operator_cycle_trigger(
        trigger_id="operator-trigger-canonical1",
        requested_mode="SHADOW_ONLY",
        control_state_version=1,
        requested_at_utc="2026-08-10T11:59:00+00:00",
    )
    intake.write_ingestion_checkpoint(
        supervisor._store,
        now=FIXED_NOW,
        last_success_epoch=(FIXED_NOW - timedelta(seconds=30)).timestamp(),
        outcome_code=intake.OUTCOME_CAPTURED_NEW,
        consecutive_empty=0,
        rows_iteration=4,
    )
    report = supervisor.tick(FIXED_NOW)
    trigger_report = report.get("operator_trigger")
    assert trigger_report is not None
    assert trigger_report["state"] == "CONSUMED"
    assert trigger_report["executed"] is True
    assert trigger_report["ingestion_capture"]["detail"] == "intake_fresh_no_sync_needed"
    assert calls[0]["publication_enabled"] is False
    assert "operator_run_now_override" not in calls[0]
    assert report["public_write_performed"] is False
    assert report["headline_ingestion"] is not None


def test_run_now_stale_intake_performs_exactly_one_bounded_forced_sync(
    monkeypatch, tmp_path
):
    from tests.test_daily_app_operator_trigger_v1 import _supervisor as supervisor_factory

    supervisor, _calls = supervisor_factory(tmp_path, mode="SHADOW_ONLY")
    sync_calls = []
    monkeypatch.setattr(intake, "intake_is_stale", lambda _store, now: True)

    def bounded_sync(_store, *, now, force=False):
        sync_calls.append({"now": now, "force": force})
        return {
            "lane_state": "CAPTURED",
            "detail": "one_bounded_stale_sync",
            "llm_or_provider_calls": 0,
        }

    monkeypatch.setattr(intake, "run_ingestion_housekeeping_iteration", bounded_sync)
    result = supervisor._run_operator_trigger_intake_sync(FIXED_NOW)

    assert sync_calls == [{"now": FIXED_NOW, "force": True}]
    assert result["detail"] == "one_bounded_stale_sync"
    assert result["llm_or_provider_calls"] == 0
