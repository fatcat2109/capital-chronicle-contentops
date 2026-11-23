"""Pre-relaunch (22 Nov 2026, 19:39Z): a page's TradingView capture starts only when it can finish inside
the minute job; otherwise the page waits for the next run, and its capture window is not used up."""
import json

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_reader_editorial_v1 as editorial
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import tradingview_snapshot_v1 as tv
from test_plan_analysis_pages_cc432 import source  # noqa: F401
from test_plan_page_current_cc584 import frozen_gold_reasoning, gold_18_nov  # noqa: F401


def test_a_capture_may_start_only_when_one_attempt_ends_before_the_job_limit():
    assert editorial.page_capture_allowed(None) is None
    attempt = getattr(tv, "PLAN_ATTEMPT_TIMEOUT_SECONDS", tv.PLAN_RETRY_TIMEOUT_SECONDS)
    deadline = 1000.0
    last_start = deadline - attempt - editorial.PAGE_CAPTURE_MARGIN_SECONDS
    assert editorial.page_capture_allowed(deadline, clock=lambda: last_start)() is True
    assert editorial.page_capture_allowed(deadline, clock=lambda: last_start + 1)() is False


def _page_card(raw, run, tmp_path):
    return pages._card(raw, run, tmp_path / "page", {"title": "Gold: bearish at 3,773–3,790"})


def test_no_time_left_defers_the_page_capture_without_an_attempt(gold_18_nov, frozen_gold_reasoning, tmp_path,
                                                                 monkeypatch):
    raw = {**gold_18_nov, "status": "WAITING"}
    started = []
    monkeypatch.setattr(tv, "capture", lambda *a, **k: started.append(a) or pytest.fail("capture started"))
    monkeypatch.setattr(tv, "record_outcome", lambda *a, **k: None)
    token = pages.PAGE_CAPTURE_ALLOWED.set(lambda: False)
    try:
        with pytest.raises(ValueError, match="TRADINGVIEW_CAPTURE_DEFERRED_RUN_TIME_BUDGET"):
            _page_card(raw, frozen_gold_reasoning, tmp_path)
    finally:
        pages.PAGE_CAPTURE_ALLOWED.reset(token)
    assert started == []
    [state_file] = (tmp_path / "page").glob("tradingview_capture*_v1.json")
    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state["status"] == "DEFERRED" and state["attempts"] == 0


def test_with_time_left_the_page_captures_as_before(gold_18_nov, frozen_gold_reasoning, tmp_path, monkeypatch):
    raw = {**gold_18_nov, "status": "WAITING"}
    seen = []

    def post_image(row, folder, **kwargs):
        seen.append(kwargs.get("snapshot_allowed"))
        return {"path": "chart.png"}, True

    monkeypatch.setattr(posts, "_post_image", post_image)
    check = lambda: True  # noqa: E731
    token = pages.PAGE_CAPTURE_ALLOWED.set(check)
    try:
        assert _page_card(raw, frozen_gold_reasoning, tmp_path) == {"path": "chart.png"}
    finally:
        pages.PAGE_CAPTURE_ALLOWED.reset(token)
    assert seen == [check]
    # Outside a run_due slice (tests, the CLI resume) nothing limits the capture.
    assert _page_card(raw, frozen_gold_reasoning, tmp_path) == {"path": "chart.png"}
    assert seen == [check, None]


def test_run_due_gives_its_slice_the_job_budget_and_clears_it_after(source, tmp_path, monkeypatch):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    seen = []

    def plans(*a, **k):
        seen.append(pages.PAGE_CAPTURE_ALLOWED.get())
        raise ValueError("STOP_AFTER_READING_THE_BUDGET")

    store = ContentOpsDurableStore(tmp_path / "store.sqlite3")
    monkeypatch.setattr(editorial, "_dated_plans", plans)
    with pytest.raises(ValueError, match="STOP_AFTER_READING_THE_BUDGET"):
        editorial.run_due(store, {"status": {"plans": []}}, root=tmp_path, rollout={"store_path": store.db_path},
                          now=posts._utc("2026-11-23T12:00:00Z"), cached_only=True, job_deadline=1e12)
    assert callable(seen[0]) and seen[0]() is True
    assert pages.PAGE_CAPTURE_ALLOWED.get() is None


def test_the_minute_job_passes_its_own_limit_to_the_page_slice():
    from pathlib import Path
    text = (Path(__file__).resolve().parents[1] / "scripts/plan_status_posts.py").read_text(encoding="utf-8")
    assert "job_deadline=started + PAGE_JOB_LIFETIME_SECONDS" in text
    assert editorial.PAGE_JOB_LIFETIME_SECONDS == 300
