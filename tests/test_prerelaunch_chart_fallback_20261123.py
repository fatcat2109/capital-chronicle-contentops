"""Builder E, 23 Nov 2026: decision 82 when a TradingView capture fails.

The 22 Nov BTC analysis page went out text-only; the 23 Nov BTC setup post carried the plan card after
two TRADINGVIEW_SNAPSHOT_TIMEOUT attempts. A page now carries CC-290's fact card with the plan's own
numbers, and the capture defects behind both timeouts are fixed (no browser in these tests).
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import publication_image_contract_v1 as contract
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from test_plan_analysis_pages_cc432 import source  # noqa: F401


def _plan_page_source(source):
    run_root, folder, plan, manuscript = source
    freeze_path = folder / "final-decision-freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    freeze["frozen_at_utc"] = "2026-11-22T19:30:00Z"  # after CC-463, so the page takes a TradingView chart
    freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
    plan.update(direction="BEARISH", zone={"minimum": 1.1650, "maximum": 1.1680}, status="WAITING",
                registered_at_utc="2026-11-22T19:31:00Z", target=1.1500, target_level=1.1500,
                invalidation_conditions=[{"operator": "GTE", "field": "high", "threshold": 1.1720}])
    # The live page contract (CC466), as in test_plan_analysis_distribution_cc435.
    reader = {**manuscript, "reader_contract": "CC466_V1", "title": "Rates shape the euro.",
              "sections": {key: deepcopy(manuscript["sections"]["macro"]) for key, _ in pages.READER_SECTIONS}}
    for key, label in pages.READER_SECTIONS:
        reader["sections"][key]["summary"] = "The " + label.lower() + " matters."
    reader["sections"]["scenarios"]["summary"] = "Main (55%): conditions hold. Alternative (35%): conditions change."
    return run_root, plan, reader


def _failing_capture(monkeypatch, tmp_path, calls):
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")

    def capture(market, interval, out_dir, **kwargs):
        calls.append({"out_dir": Path(out_dir), **kwargs})
        raise tv.SnapshotError("TRADINGVIEW_SNAPSHOT_TIMEOUT")
    monkeypatch.setattr(tv, "capture", capture)


def _page_intent(tmp_path, packet, now):
    store = ContentOpsDurableStore(tmp_path / "page.sqlite3")
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None, clock=lambda: now,
                                                  published_content_path=tmp_path / "published.jsonl")
    packet = pages.register_page(store, packet)
    coordinator.register_plan(packet["page_id"], packet["plan"])
    row, = store.list_outbox_messages(destination="substack")
    return coordinator, json.loads(row["payload"])


def test_page_whose_capture_fails_carries_the_plan_fact_card_and_passes_the_write_boundary(source, tmp_path,
                                                                                             monkeypatch):
    from live_contentops import article_publication_quality_v1 as quality

    run_root, plan, manuscript = _plan_page_source(source)
    calls = []
    _failing_capture(monkeypatch, tmp_path, calls)
    packet = pages.render(plan, manuscript, run_root=run_root, output_dir=tmp_path / "page")

    assert len(calls) == 2 and all(call["timeout"] <= tv.PLAN_ATTEMPT_TIMEOUT_SECONDS for call in calls)
    card, = packet["media_assets"]
    assert card["modality"] == "plan_fact_card"
    assert card["plan_chart_fallback"] == {"key": "plan-analysis-plan_test", "market": "EURUSD",
                                           "ratio": "16:9", "cause": "TRADINGVIEW_SNAPSHOT_TIMEOUT"}
    facts = dict(card["data_card_packet"]["facts"])
    assert facts["Entry zone"] == "1.165–1.168"
    assert facts["Invalidation"] == "Above 1.172"
    assert facts["Status"] == "Waiting for price to reach the entry zone"
    assert facts["As of"].endswith("ET")
    shown = json.dumps([card["data_card_packet"], card["alt_text"], card["caption"]]).lower()
    assert "target" not in shown and "1.15" not in shown  # decisions 40 and 157
    assert Path(card["path"]).is_file() and card["path"] in "".join(packet["output_dir"] + card["path"])
    html = (tmp_path / "page" / "article.html").read_text(encoding="utf-8")
    assert Path(card["path"]).as_uri() in html  # in the page body, not a title on an empty page

    now = datetime.now(timezone.utc)
    coordinator, intent = _page_intent(tmp_path, packet, now)
    result = contract.validate_write(coordinator, intent, "substack")
    assert result["first_image_type"] == "DRAWN_CARD"
    assert result["plan_chart_fallback_causes"] == ["TRADINGVIEW_SNAPSHOT_TIMEOUT"]
    assert not result.get("text_fallback")
    # The plan's current state and quote are checked against Main's export just before the write (not the image).
    monkeypatch.setattr(pages, "require_current_page", lambda packet, **_: None)
    reserved = quality.before_article_write(coordinator, intent, "substack")
    assert reserved["lead_asset_id"] == card["asset_id"]


@pytest.mark.parametrize("change,cause", [
    # The page's own validator refuses changed facts when the page is registered for publication.
    (lambda card: card["data_card_packet"]["facts"].append(["Target", "1.1500"]), "PLAN_ANALYSIS_FACT_CARD_CHANGED"),
    (lambda card: card["plan_chart_fallback"].update(key="plan-analysis-other"), "PLAN_ANALYSIS_FACT_CARD_CHANGED"),
    # The write boundary binds the card to the page's own exhausted capture.
    (lambda card: card["plan_chart_fallback"].update(cause="OTHER"), "PLAN_PAGE_CHART_FALLBACK_BINDING_INVALID"),
])
def test_page_fact_card_is_refused_when_its_facts_or_binding_change(source, tmp_path, monkeypatch, change, cause):
    run_root, plan, manuscript = _plan_page_source(source)
    _failing_capture(monkeypatch, tmp_path, [])
    packet = pages.render(plan, manuscript, run_root=run_root, output_dir=tmp_path / "page")
    change(packet["media_assets"][0])
    context_path = tmp_path / "page" / "run_context_v1.json"
    context = json.loads(context_path.read_bytes())
    context["media"]["assets"] = packet["media_assets"]
    context_path.write_text(json.dumps(context), encoding="utf-8")
    with pytest.raises(ValueError, match=cause):
        coordinator, intent = _page_intent(tmp_path, packet, datetime.now(timezone.utc))
        contract.validate_write(coordinator, intent, "substack")


def test_page_fact_card_waits_for_the_bounded_capture_to_end(source, tmp_path):
    _, plan, _ = _plan_page_source(source)
    folder = tmp_path / "page"
    folder.mkdir()
    assert tv.page_fact_card(plan, folder) is None  # no capture yet
    (folder / "tradingview_capture_v1.json").write_text(json.dumps({
        "key": "plan-analysis-plan_test", "market": "EURUSD", "attempts": 1, "attempt_causes": [],
        "started_at_utc": datetime.now(timezone.utc).isoformat()}))
    assert tv.page_fact_card(plan, folder) is None  # still capturing
    (folder / "tradingview_capture_v1.json").write_text(json.dumps({
        "key": "plan-analysis-plan_test", "market": "EURUSD", "attempts": 2, "status": "TEXT_ONLY",
        "cause": "TRADINGVIEW_SNAPSHOT_TIMEOUT", "started_at_utc": datetime.now(timezone.utc).isoformat()}))
    card = tv.page_fact_card(plan, folder, status={"status": "TRIGGERED", "status_at_utc": "2026-11-23T04:00:00Z"})
    assert dict(card["data_card_packet"]["facts"])["Status"] == "Entry filled"


def _row(levels=True):
    row = {"key": "plan-analysis-plan_x", "symbol": "BTCUSD", "at_utc": datetime.now(timezone.utc).isoformat(),
           "levels": {}}
    if levels:
        row["levels"] = {"valid_until_utc": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
                         "zone_low": 60000, "zone_high": 61400}
    return row


def test_an_interrupted_attempt_is_named_and_retried_once_after_the_window(tmp_path, monkeypatch):
    """22 Nov 19:39Z: the minute job stopped during attempt 1; at 19:47 the page went TEXT_ONLY untried."""
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    folder = tmp_path / "page"
    folder.mkdir()
    started = (datetime.now(timezone.utc) - timedelta(minutes=8)).isoformat()
    (folder / "tradingview_capture_v1.json").write_text(json.dumps({
        "key": "plan-analysis-plan_x", "market": "BTCUSD", "attempts": 1, "attempt_causes": [],
        "started_at_utc": started}))
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise tv.SnapshotError("TRADINGVIEW_WORKER_STEP_TIMEOUT:download")
    assert tv.plan_snapshot(_row(), folder, snapshot=fail) is None
    state = json.loads((folder / "tradingview_capture_v1.json").read_bytes())
    # The interrupted attempt does not count: two real attempts, inside one extra bounded window.
    assert len(calls) == 2 and state["attempts"] == 3
    assert state["attempt_causes"] == [tv.CAPTURE_INTERRUPTED] + ["TRADINGVIEW_WORKER_STEP_TIMEOUT:download"] * 2
    assert state["status"] == "TEXT_ONLY" and state["cause"] == tv.CAPTURE_INTERRUPTED


def test_a_second_interruption_gets_no_further_attempt(tmp_path, monkeypatch):
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    folder = tmp_path / "page"
    folder.mkdir()
    past = datetime.now(timezone.utc) - timedelta(minutes=8)
    (folder / "tradingview_capture_v1.json").write_text(json.dumps({
        "key": "plan-analysis-plan_x", "market": "BTCUSD", "attempts": 2,
        "attempt_causes": [tv.CAPTURE_INTERRUPTED], "first_cause": tv.CAPTURE_INTERRUPTED,
        "interrupted_retry_until_utc": (past + timedelta(minutes=2)).isoformat(),
        "started_at_utc": past.isoformat()}))
    assert tv.plan_snapshot(_row(), folder, snapshot=lambda *a, **k: pytest.fail("bounded")) is None
    state = json.loads((folder / "tradingview_capture_v1.json").read_bytes())
    assert state["status"] == "TEXT_ONLY" and state["attempt_causes"] == [tv.CAPTURE_INTERRUPTED] * 2


def test_each_attempt_keeps_its_own_cause_and_the_final_cause_stays_the_first(tmp_path, monkeypatch):
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    calls = []

    def fail(*args, **kwargs):
        calls.append(1)
        raise tv.SnapshotError("first" if len(calls) == 1 else "TRADINGVIEW_WORKER_STEP_FAILED:reset_price_scale")
    assert tv.plan_snapshot(_row(), tmp_path / "one", snapshot=fail) is None
    state = json.loads((tmp_path / "one/tradingview_capture_v1.json").read_bytes())
    assert state["cause"] == "first"
    assert state["attempt_causes"] == ["first", "TRADINGVIEW_WORKER_STEP_FAILED:reset_price_scale"]


@pytest.mark.parametrize("levels,expected", [(True, 90), (False, 60)])
def test_plan_charts_get_ninety_seconds_on_every_attempt(tmp_path, monkeypatch, levels, expected):
    """23 Nov 04:01Z: the BTC portrait download landed 61 s into a 60 s first attempt."""
    calls = []
    _failing_capture(monkeypatch, tmp_path, calls)
    assert tv.plan_snapshot(_row(levels), tmp_path / "one") is None
    assert [round(call["timeout"]) for call in calls] == [expected, expected]


def test_a_wide_template_capture_no_longer_shares_the_portrait_attempt_folders(tmp_path, monkeypatch):
    calls = []
    _failing_capture(monkeypatch, tmp_path, calls)
    row = {**_row(), "key": "plan-status-post-x"}
    with pytest.raises(tv.SnapshotUnavailable):
        tv.plan_snapshot(row, tmp_path / "post", plan_post=True, image_input={"template": "plan"})
    media = (tmp_path / "post" / "media_assets").resolve()
    assert [call["out_dir"].resolve() for call in calls] == [media / "attempt-1", media / "attempt-2"]


def test_worker_waits_share_one_deadline_and_name_the_step_that_ran_out():
    clock = [0.0]
    steps = tv._StepBudget(50_000, clock=lambda: clock[0])
    granted = 0
    for name, cap in (("open_chart", 25_000), ("chart_canvas", 16_666), ("price_title", 12_500),
                      ("paint", 2_500), ("download", 20_000)):
        wait = steps.at(name).left(cap)
        granted += wait
        clock[0] += wait / 1000  # every step uses its whole wait: the slowest page
        if clock[0] >= 50:
            break
    # Before, these waits alone came to 77 s against a 52 s budget and the parent's kill at 60 s.
    assert granted == 50_000 and steps.step == "price_title"
    with pytest.raises(tv.SnapshotError, match="TRADINGVIEW_WORKER_BUDGET_SPENT:paint"):
        steps.at("paint").left(2_500)

    class TimeoutError(Exception):  # Playwright's class name
        pass
    assert steps.at("download").cause(TimeoutError("x")) == "TRADINGVIEW_WORKER_STEP_TIMEOUT:download"
    assert steps.at("reset_price_scale").cause(RuntimeError("x")) == "TRADINGVIEW_WORKER_STEP_FAILED:reset_price_scale"


def test_worker_failure_names_the_error_not_the_playwright_call_log():
    """23 Nov 04:06Z: the late BTC chart failed as 'TRADINGVIEW_SNAPSHOT_WORKER_FAILED:      - waiting 500ms'."""
    with pytest.raises(tv.SnapshotError, match="^TRADINGVIEW_WORKER_STEP_TIMEOUT:download$"):
        tv._worker_output(1, b'{"error": "TRADINGVIEW_WORKER_STEP_TIMEOUT:download"}\n', b"")
    err = (b"Traceback (most recent call last):\n  File \"x.py\", line 1\n"
           b"playwright._impl._errors.TimeoutError: Locator.dblclick: Timeout 5000ms exceeded.\n"
           b"Call log:\n  - waiting for locator\n  - retrying click action\n      - waiting 500ms\n")
    with pytest.raises(tv.SnapshotError, match="WORKER_FAILED:playwright._impl._errors.TimeoutError: Locator.dblclick"):
        tv._worker_output(1, b"", err)
    assert tv._worker_output(0, b'{"path": "a.png"}\n', b"") == {"path": "a.png"}
