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


def test_checkpoint_roundtrip_and_low_frequency_cadence(tmp_path):
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
    assert intake.next_due_interval_seconds(0) == 1800
    assert intake.next_due_interval_seconds(
        last_outcome_code=intake.OUTCOME_CAPTURED_NEW, hot_followup_pending=True
    ) == 900
    assert intake.next_due_interval_seconds(
        last_outcome_code=intake.OUTCOME_CAPTURED_NONE
    ) == 3600
    assert intake.next_due_interval_seconds(
        last_outcome_code=intake.OUTCOME_CAPTURE_FAILED
    ) >= 1800
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


def test_fake_clock_proves_30m_15m_one_shot_and_60m_cadence(tmp_path):
    store = _store(tmp_path)
    outcomes = iter((
        {"capture_state": "CAPTURED", "new_headlines": 2},
        {"capture_state": "CAPTURED", "new_headlines": 1},
        {"capture_state": "CAPTURED_NO_NEW_HEADLINES", "new_headlines": 0},
        {"capture_state": "CAPTURED_NO_NEW_HEADLINES", "new_headlines": 0},
    ))
    calls = []

    def capture_due(**kwargs):
        calls.append(kwargs)
        return next(outcomes)

    kwargs = {
        "state_fn": lambda: {"state": "READY"},
        "session_fn": lambda: {"session_state": "READY"},
        "capture_fn": capture_due,
    }
    first = intake.run_ingestion_housekeeping_iteration(store, now=FIXED_NOW, **kwargs)
    assert first["cadence_state"] == "HOT_FOLLOWUP"
    assert first["next_eligible_capture_utc"] == (
        FIXED_NOW + timedelta(seconds=900)
    ).isoformat().replace("+00:00", "Z")

    # Run Now/force is not browser-budget authority.
    early_hot = intake.run_ingestion_housekeeping_iteration(
        store, now=FIXED_NOW + timedelta(seconds=899), force=True, **kwargs
    )
    assert early_hot["detail"] == "not_due"
    assert len(calls) == 1

    followup = intake.run_ingestion_housekeeping_iteration(
        store, now=FIXED_NOW + timedelta(seconds=900), **kwargs
    )
    assert followup["cadence_state"] == "NORMAL"
    assert intake.read_ingestion_checkpoint(store)["hot_followup_pending"] is False

    early_normal = intake.run_ingestion_housekeeping_iteration(
        store, now=FIXED_NOW + timedelta(seconds=2699), **kwargs
    )
    assert early_normal["detail"] == "not_due"
    empty = intake.run_ingestion_housekeeping_iteration(
        store, now=FIXED_NOW + timedelta(seconds=2700), **kwargs
    )
    assert empty["cadence_state"] == "EMPTY_BACKOFF"

    early_empty = intake.run_ingestion_housekeeping_iteration(
        store, now=FIXED_NOW + timedelta(seconds=6299), **kwargs
    )
    assert early_empty["detail"] == "not_due"
    repeated_empty = intake.run_ingestion_housekeeping_iteration(
        store, now=FIXED_NOW + timedelta(seconds=6300), **kwargs
    )
    assert repeated_empty["cadence_state"] == "EMPTY_BACKOFF"
    assert len(calls) == 4


def test_capture_exception_persists_30m_transient_retry_boundary(tmp_path):
    store = _store(tmp_path)
    capture_calls = []

    def capture_fails(**kwargs):
        capture_calls.append(kwargs)
        raise RuntimeError("sanitized capture failure")

    first = intake.run_ingestion_housekeeping_iteration(
        store,
        now=FIXED_NOW,
        state_fn=lambda: {"state": "READY"},
        session_fn=lambda: {"session_state": "READY"},
        capture_fn=capture_fails,
    )

    assert first["lane_state"] == "DEGRADED"
    assert first["cadence_state"] == "TRANSIENT_RETRY"
    assert first["detail"] == "CAPTURE_FAILED:OTHER_CAPTURE_FAILURE"
    assert first["failure_class"] == "OTHER_CAPTURE_FAILURE"
    assert first["failure_detail"] == "CAPTURE_CALL_FAILED:RUNTIMEERROR"
    assert first["attempt_detail_persisted"] is True
    assert first["next_eligible_capture_utc"] == (
        FIXED_NOW + timedelta(seconds=1800)
    ).isoformat().replace("+00:00", "Z")
    checkpoint = intake.read_ingestion_checkpoint(store)
    assert checkpoint["last_attempt_epoch"] == FIXED_NOW.timestamp()
    assert checkpoint["last_outcome_code"] == intake.OUTCOME_CAPTURE_FAILED
    assert checkpoint["last_attempt_detail"]["failure_class"] == "OTHER_CAPTURE_FAILURE"
    assert checkpoint["last_attempt_detail"]["eligibility_reason"] == "NO_PRIOR_ATTEMPT"
    assert checkpoint["last_attempt_detail"]["browser_role"] == "CHROME_CDP_9222_INGESTION_ONLY"

    early = intake.run_ingestion_housekeeping_iteration(
        store,
        now=FIXED_NOW + timedelta(seconds=1799),
        state_fn=lambda: pytest.fail("transient retry inspected browser process state early"),
        session_fn=lambda: pytest.fail("transient retry attached CDP early"),
        capture_fn=lambda **_kwargs: pytest.fail("transient retry captured X early"),
    )
    assert early["detail"] == "not_due"
    assert len(capture_calls) == 1


def test_sanitized_capture_failure_detail_is_bounded_durable_and_restart_safe(tmp_path):
    store_path = tmp_path / "store.sqlite3"
    store = ContentOpsDurableStore(store_path)
    result = intake.run_ingestion_housekeeping_iteration(
        store,
        now=FIXED_NOW,
        state_fn=lambda: {"state": "READY"},
        session_fn=lambda: {"session_state": "READY"},
        capture_fn=lambda **_kwargs: {
            "capture_state": "CAPTURE_FAILED",
            "capture_phase": "RELOAD",
            "timeline_responses_observed": 0,
            "new_headlines": 0,
            "failure_class": "PLAYWRIGHT_TRANSPORT_FAILURE",
            "failure_detail": "RELOAD_TRANSPORT_CLOSED:Error",
        },
    )
    assert result["detail"] == "CAPTURE_FAILED:PLAYWRIGHT_TRANSPORT_FAILURE"
    assert result["attempt_detail_persisted"] is True
    detail_path = tmp_path / "headline_ingestion" / intake.ATTEMPT_DETAIL_FILENAME
    raw = detail_path.read_bytes()
    assert len(raw) <= intake.ATTEMPT_DETAIL_MAX_BYTES
    assert b"cookie" not in raw.lower()
    assert b"token" not in raw.lower()

    reopened = ContentOpsDurableStore(store_path)
    detail = intake.read_ingestion_checkpoint(reopened)["last_attempt_detail"]
    assert detail["failure_class"] == "PLAYWRIGHT_TRANSPORT_FAILURE"
    assert detail["failure_detail"] == "RELOAD_TRANSPORT_CLOSED:ERROR"
    assert detail["capture_phase"] == "RELOAD"
    assert detail["chrome_9222_readiness"] == "READY"
    assert detail["auth_classification"] == "READY"
    assert detail["rows_captured"] == 0
    assert detail["next_eligible_capture_utc"] == (
        FIXED_NOW + timedelta(seconds=1800)
    ).isoformat().replace("+00:00", "Z")


def test_capture_exception_classifier_never_returns_raw_sensitive_message():
    failure_class, failure_detail = capture.classify_capture_exception(
        RuntimeError("EPIPE authorization=Bearer token-secret-cookie"), phase="RELOAD"
    )
    assert failure_class == "PLAYWRIGHT_TRANSPORT_FAILURE"
    assert failure_detail == "RELOAD_TRANSPORT_CLOSED:RuntimeError"
    assert "token" not in failure_detail.casefold()
    assert "cookie" not in failure_detail.casefold()


def test_bounded_x_capture_classifies_no_timeline_response_without_raw_browser_data(
    tmp_path, monkeypatch,
):
    class Page:
        url = capture.TARGET_LIST_URL

        def on(self, *_args):
            return None

        def remove_listener(self, *_args):
            return None

        def reload(self, **_kwargs):
            return None

        def wait_for_timeout(self, _milliseconds):
            return None

        def evaluate(self, _script):
            return None

    page = Page()
    browser = type("Browser", (), {"contexts": [type("Context", (), {"pages": [page]})()]})()
    chromium = type("Chromium", (), {"connect_over_cdp": lambda self, *_args, **_kwargs: browser})()
    driver = type("Driver", (), {"chromium": chromium})()

    class DriverContext:
        def __enter__(self):
            return driver

        def __exit__(self, *_args):
            return False

    module = type("Module", (), {"SIDECAR_DIR": str(tmp_path / "sidecars")})()
    monkeypatch.setattr(capture, "load_data_ingestion_module", lambda: module)
    result = capture.run_bounded_x_list_capture(
        max_seconds=1,
        max_empty_scrolls=1,
        playwright=DriverContext(),
    )
    assert result["capture_state"] == "CAPTURE_FAILED"
    assert result["failure_class"] == "MALFORMED_EMPTY_CAPTURE_RESPONSE"
    assert result["failure_detail"] == "NO_TIMELINE_RESPONSE_OBSERVED_AFTER_RELOAD"
    assert result["timeline_responses_observed"] == 0
    assert result["capture_phase"] == "EXTRACTION_SCROLL"


def test_kill_switch_suppresses_even_forced_x_capture(tmp_path):
    store = _store(tmp_path)
    control = store.get_operating_control()
    store.update_operating_control(
        expected_state_version=control["state_version"],
        operating_mode="KILL_SWITCH",
        control_source="CONTROLLED_TEST",
    )

    result = intake.run_ingestion_housekeeping_iteration(
        store,
        now=FIXED_NOW,
        force=True,
        state_fn=lambda: pytest.fail("KILL_SWITCH inspected browser process state"),
        session_fn=lambda: pytest.fail("KILL_SWITCH attached CDP"),
        capture_fn=lambda **_kwargs: pytest.fail("KILL_SWITCH captured X"),
    )

    assert result["lane_state"] == "PAUSED_KILL_SWITCH"
    assert result["capture_attempted"] is False
    assert result["cadence_state"] == "KILL_SWITCH"


def test_parallel_x_capture_is_suppressed(tmp_path):
    store = _store(tmp_path)
    assert intake._INGESTION_CAPTURE_LOCK.acquire(blocking=False)
    try:
        result = intake.run_ingestion_housekeeping_iteration(
            store,
            now=FIXED_NOW,
            state_fn=lambda: {"state": "READY"},
            session_fn=lambda: pytest.fail("parallel capture attached CDP"),
            capture_fn=lambda **_kwargs: pytest.fail("parallel capture ran"),
        )
    finally:
        intake._INGESTION_CAPTURE_LOCK.release()
    assert result["detail"] == "parallel_capture_suppressed"
    assert result["capture_attempted"] is False


def test_x_capture_prefers_existing_exact_locked_list_tab():
    class Page:
        def __init__(self, url):
            self.url = url

    other = Page("https://x.com/home")
    exact = Page(f"https://x.com/i/lists/{capture.TARGET_LIST_ID}")
    context = type("Context", (), {"pages": [other, exact]})()

    assert capture.select_reusable_x_page(context) is exact


def test_direct_cdp_target_selection_ignores_unrelated_and_prefers_exact_list():
    targets = [
        {"type": "page", "url": "https://example.test", "webSocketDebuggerUrl": "ws://example"},
        {"type": "page", "url": "https://x.com/home", "webSocketDebuggerUrl": "ws://home"},
        {
            "type": "page",
            "url": capture.TARGET_LIST_URL,
            "webSocketDebuggerUrl": "ws://exact",
        },
    ]

    assert capture.select_reusable_x_target(targets)["webSocketDebuggerUrl"] == "ws://exact"


def test_direct_target_cdp_capture_reuses_canonical_extractor_without_browser_wide_attach(
    tmp_path, monkeypatch,
):
    sidecar_dir = tmp_path / "sidecars"
    sidecar_dir.mkdir()
    module = type("Module", (), {
        "SIDECAR_DIR": str(sidecar_dir),
        "archive_raw_payload": staticmethod(
            lambda _payload, _url: {"raw_payload_ref": "raw", "raw_payload_sha256": "a" * 64}
        ),
        "recursive_tweet_extractor": staticmethod(
            lambda _payload: [{"tweet_id": "7", "timestamp": "2026-08-14", "text": "headline"}]
        ),
    })()
    monkeypatch.setattr(capture, "load_data_ingestion_module", lambda: module)
    monkeypatch.setattr(
        capture,
        "list_cdp_page_targets",
        lambda **_kwargs: [{
            "type": "page",
            "url": capture.TARGET_LIST_URL,
            "webSocketDebuggerUrl": "ws://exact",
        }],
    )
    monkeypatch.setattr(capture, "RELOAD_SETTLE_MS", 10)
    monkeypatch.setattr(capture, "SCROLL_WAIT_MS", 10)

    def append_rows(_module, _tweets, _raw, summaries):
        (sidecar_dir / "step1_headline_sidecar_2026_08_14.jsonl").write_text(
            '{"headline_id":"headline-7"}\n', encoding="utf-8"
        )
        summaries.append({
            "headline_id": "headline-7",
            "dedup_key": "tweet_id:7",
            "headline_timestamp": "2026-08-14",
            "source_platform": "x_cdp_list_latest_tweets_timeline",
        })
        return 1

    monkeypatch.setattr(capture, "append_deduped_sidecar_rows", append_rows)

    clients = []

    class Client:
        def __init__(self, websocket_url, **_kwargs):
            self.websocket_url = websocket_url
            self.commands = []
            self.events = [
                {
                    "method": "Network.responseReceived",
                    "params": {
                        "requestId": "request-1",
                        "response": {
                            "url": f"https://x.com/graphql/{capture.TIMELINE_RESPONSE_MARKER}",
                            "status": 200,
                        },
                    },
                },
                {"method": "Network.loadingFinished", "params": {"requestId": "request-1"}},
            ]
            clients.append(self)

        def command(self, method, _params=None, **_kwargs):
            self.commands.append(method)
            if method == "Network.getResponseBody":
                return {"body": '{"data":{"timeline":[]}}', "base64Encoded": False}
            return {}

        def event(self, **_kwargs):
            return self.events.pop(0) if self.events else None

        def close(self):
            return None

    result = capture._run_direct_cdp_capture(
        max_seconds=0.1,
        max_empty_scrolls=1,
        cdp_url="http://127.0.0.1:9222",
        client_factory=Client,
    )

    assert result["capture_state"] == capture.CAPTURE_STATE_CAPTURED
    assert result["cdp_transport"] == "TARGET_SCOPED_DIRECT_CDP"
    assert result["timeline_responses_observed"] == 1
    assert result["new_headlines"] == 1
    assert clients[0].websocket_url == "ws://exact"
    assert "Page.reload" in clients[0].commands
    assert "Network.getResponseBody" in clients[0].commands


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
            "INSERT INTO platform_dispatches (dispatch_id,message_id,platform,status,dispatched_at,public_object_id,public_object_url)"
            " VALUES ('disp1','msg1','substack','DISPATCH_CONFIRMED','2026-08-10T09:05:00Z','object-123','https://capitalchronicle.substack.com/p/fed-decision-day-recap')"
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
    assert state["publication_minimum"] == 5
    assert state["build_qualified_floor"] == 4
    assert state["final_published_target_min"] == 5
    assert state["final_published_target_max"] == 8


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


def test_bootstrap_policy_locks_four_window_daily_output_contract():
    policy = bootstrap_portfolio_policy()
    assert policy["daily_target_band"] == [5, 8]
    assert policy["publication_minimum"] == 5
    assert policy["build_qualified_floor"] == 4
    assert policy["final_published_target_min"] == 5
    assert policy["final_published_target_max"] == 8
    assert policy["core_decision_opportunities_per_day"] == 4
    assert policy["material_event_wakeups_enabled"] is False
    assert policy["material_event_priority_next_scheduled_opportunity"] is True
    assert policy["automatic_schedule_scaling_enabled"] is False
    assert policy["schedule_owner_locked"] is True
    assert policy["filler_fabrication_permitted"] is False
    assert policy["weakened_factual_or_numeric_authority_permitted"] is False

    from live_contentops.daily_app_supervisor_v1 import build_bootstrap_editorial_window_policy

    window_policy = build_bootstrap_editorial_window_policy()
    assert len(window_policy.core_windows) == 4
    assert window_policy.policy_version == "autonomous_daily_output_four_window.v1"
    assert window_policy.daily_publication_target_band == (5, 8)
    assert window_policy.publication_minimum == 5
    assert window_policy.build_qualified_floor == 4
    assert window_policy.material_event_override_enabled is True
    assert window_policy.automatic_schedule_scaling_enabled is False
    assert window_policy.schedule_owner_locked is True
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
