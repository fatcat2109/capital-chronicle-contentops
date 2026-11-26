"""CC-760 (decision 82): fail-closed cached TradingView chart fallback on canonical plan-page timeout.

Covers:
  - Frozen 22 Nov 2026 BTCUSD timeout replay (`TRADINGVIEW_CAPTURE_WAIT_EXPIRED`) reusing the exact
    same-plan setup TradingView chart, full attribution, HTML embed, audit provenance, and write boundary.
  - Live capture timeout (`TRADINGVIEW_SNAPSHOT_TIMEOUT`) fallback + non-timeout fail-closed behavior.
  - All 5 fail-closed invariant rejections:
      (a) symbol / feed / interval / ratio / scale mismatch
      (b) plan_id missing / mismatch / conflict
      (c) source_window / freshness cap / pre-freeze / future / post-deadline / post-close / naive clock
      (d) revision (`registration_hash`, `analysis_result_hash`, `run_id`, `freeze.immutable_hash`,
          `plan_revision`, `reader_revision`, `level_contract`) & SHA256 PNG byte tamper
      (e) public_use_rights invalid / forbidden / paid page & private-text / R-multiple / profit-target leak
  - Write-boundary tamper rejections (`validate_plan` & `publication_image_contract_v1.validate_write`).
  - `plan_reader_editorial_v1.run_due` active-plan setup_post_dir wiring.

All tests are 100% isolated under `tmp_path` (no browser, no network, zero writes under Runtime).
Operator: T3 Code, Gemini 4 Neon xhigh, antigravity_14
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

from PIL import Image
import pytest

from live_contentops import article_publication_quality_v1 as quality
from live_contentops import cc760_tv_chart_fallback_v1 as fb
from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_reader_editorial_v1 as editorial
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import publication_image_contract_v1 as contract
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator


def _write_png(path: Path, size: tuple[int, int] = (1600, 700), color: tuple[int, int, int] = (242, 245, 248)) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", size, color)
    img.save(path, format="PNG")
    return sha256(path.read_bytes()).hexdigest()


def _make_btc_plan_env(
    tmp_path: Path,
    *,
    frozen_at: datetime | None = None,
    entry_hours: int = 12,
    plan_id: str = "plan_add6d62299828744939aafc1",
    market: str = "BTCUSD",
    private_line: str = "Private X-list insider note about a confidential desk account 279805139.",
):
    """Build an isolated sealed Main run + plan + CC466 manuscript matching the 22 Nov BTCUSD shape."""
    frozen = frozen_at or datetime(2026, 11, 22, 19, 19, 27, tzinfo=timezone.utc)
    registered = frozen + timedelta(minutes=3)
    deadline = frozen + timedelta(hours=entry_hours)

    run_root = tmp_path / "runs"
    run_id = "request-4003b5d99d5beb61"
    run_folder = run_root / "requests" / run_id
    run_folder.mkdir(parents=True)

    result = {
        "native_synthesis": {
            "candidates": [
                {
                    "candidate_id": "cand_macro_btcusd",
                    "rationale": "Base chance 54%; key level 60000; alternative 46%.",
                }
            ]
        }
    }
    analysis_hash = sha256_of(result)
    reg_hash = "9989b584829e49af40c802db5de1a8e2911c775e379809386bef9ff898f424e5"
    freeze_hash = "0ca0c7481a0c67aaec478f0765cab6a1bc00744611193562d618c11ddf2bb9b1"
    plan = {
        "plan_id": plan_id,
        "registration_hash": reg_hash,
        "run_id": run_id,
        "analysis_result_hash": analysis_hash,
        "asset_id": market,
        "direction": "BEARISH",
        "status": "WAITING",
        "registered_at_utc": registered.isoformat().replace("+00:00", "Z"),
        "entry_deadline_utc": deadline.isoformat().replace("+00:00", "Z"),
        "expires_at_utc": deadline.isoformat().replace("+00:00", "Z"),
        "zone": {"minimum": 60000, "maximum": 61400},
        "invalidation_conditions": [{"operator": "GTE", "field": "high", "threshold": 68450}],
        "target": 55000,
        "target_level": 55000,
    }
    freeze = {
        "frozen_at_utc": frozen.isoformat().replace("+00:00", "Z"),
        "immutable_hash": freeze_hash,
        "qualitative_result_hash": analysis_hash,
    }
    market_context = {
        "items": [
            {"source": "JIM_X_LIST", "headline": private_line},
        ]
    }
    docs = {
        name: {}
        for name in (
            "role-pack.json",
            "critic-note.json",
            "integrated-owner-record.json",
            "plan-geometry.json",
            "options-context.json",
            "primary-native.json",
            "critical-native.json",
        )
    }
    docs.update({
        "role-evidence.json": [],
        "owner-native.json": result,
        "desktop-manual-result.json": result,
        "final-decision-freeze.json": freeze,
        "market-context.json": market_context,
    })
    for name, value in docs.items():
        (run_folder / name).write_text(json.dumps(value), encoding="utf-8")

    paragraph = {
        "text": "The base case has a 54% chance; key level is 60000. The alternative is 46%.",
        "refs": [{"file": "owner-native.json", "pointer": "/native_synthesis/candidates/0/rationale"}],
        "rights": "CAPITAL_CHRONICLE_ORIGINAL_ANALYSIS",
        "source_name": "Capital Chronicle",
    }
    manuscript = {
        "reader_contract": "CC466_V1",
        "reader_revision": 6,
        "plan_id": plan["plan_id"],
        "registration_hash": plan["registration_hash"],
        "title": "Bitcoin: bearish setup at 60,000.",
        "subtitle": "The drivers and conditions behind the plan.",
        "introduction": "Base case (54%): conditions hold.",
        "sections": {
            key: {
                "paragraphs": [deepcopy(paragraph)],
                "summary": (
                    "Main (54%): conditions hold. Alternative (46%): conditions change."
                    if key == "scenarios"
                    else f"The {label.lower()} matters."
                ),
            }
            for key, label in pages.READER_SECTIONS
        },
    }
    run = pages.load_run(plan, run_root=run_root)
    return run_root, run, plan, manuscript, frozen


def _make_bound_setup_dir(
    tmp_path: Path,
    plan: dict,
    *,
    captured_at: datetime,
    interval: str = "60",
    ratio: str = "16:9",
    tv_symbol: str | None = None,
    market: str | None = None,
    setup_key: str = "plan-status-post-b1425a186e37fa69ea897d903d88cfed",
    rights_basis: str | None = tv.RIGHTS_BASIS,
    public_use_rights=True,
    credit: str = tv.CREDIT,
    provenance_status: str = "VERIFIED_TRADINGVIEW_DOWNLOAD_IMAGE",
    record_overrides: dict | None = None,
    asset_overrides: dict | None = None,
    snap_overrides: dict | None = None,
) -> tuple[Path, dict]:
    """Create a realistic same-plan setup post directory matching live CC-465 / CC-543 layout."""
    mkt = market or plan["asset_id"]
    tv_sym = tv_symbol or tv.SYMBOLS[mkt]
    ticker = tv_sym.split(":", 1)[1]
    setup_dir = tmp_path / "daily_app_outputs" / "plan-status-posts" / setup_key
    raw_dir = setup_dir / "media_assets" / "attempt-1"
    raw_name = f"{ticker}_{captured_at:%Y-%m-%d_%H-%M-%S}.png"
    raw_path = raw_dir / raw_name
    raw_sha = _write_png(raw_path, size=(1600, 700))

    card_path = setup_dir / "media_assets" / f"{setup_key}-call-1-W.png"
    card_sha = _write_png(card_path, size=(1600, 900))

    snap = {
        "path": str(raw_path.resolve()),
        "sha256": raw_sha,
        "width": 1600,
        "height": 700,
        "capture_ratio": ratio,
        "tv_symbol": tv_sym,
        "interval": interval,
        "interval_label": tv.INTERVAL_LABELS[interval],
        "legend": f"{ticker} · {tv.INTERVAL_LABELS[interval]}",
        "page_title": f"{ticker} 60647.27 — TradingView",
        "chart_url": tv.chart_url(tv_sym, interval),
        "suggested_filename": raw_name,
        "captured_at_utc": captured_at.isoformat(),
        "seconds": 14.2,
    }
    snap["price_scale_check"] = contract.not_compared(
        mkt,
        snap,
        "TRADINGVIEW_CONTEMPORANEOUS_MAIN_QUOTE_UNAVAILABLE",
    )
    if snap_overrides:
        snap.update(snap_overrides)

    record = {
        "key": setup_key,
        "kind": "setup",
        "symbol": mkt,
        "plan_id": plan["plan_id"],
        "source_plan_registration": plan["registration_hash"],
        "source_plan": deepcopy(plan),
        "at_utc": plan["registered_at_utc"],
        "state_alert_contract": "CC543_V1",
    }
    if record_overrides:
        record.update(record_overrides)

    asset = {
        "asset_id": "cc465-" + card_sha[:24],
        "path": str(card_path.resolve()),
        "sha256": card_sha,
        "width": 1600,
        "height": 900,
        "modality": "tradingview_chart_snapshot",
        "credit": credit,
        "rights_basis": rights_basis,
        "public_use_rights": public_use_rights,
        "provenance_status": provenance_status,
        "alt_text": "TradingView 1h chart of Bitcoin.",
        "caption": "Bitcoin: 1h chart of Bitcoin / US dollar (Coinbase spot). Chart: TradingView.",
        "tradingview_snapshot": deepcopy(snap),
        "image_template": {
            "template": "call",
            "chart": True,
            "alt_text": "TradingView 1h chart of Bitcoin.",
            "texts": ["Bitcoin", "SHORT · Short-term", "Entry zone: 60,000–61,400", "Chart: TradingView"],
            "snapshot": deepcopy(snap),
            "input": {
                "market": mkt,
                "post_id": setup_key,
                "source_binding": {"record": record},
            },
        },
    }
    if asset_overrides:
        asset.update(asset_overrides)

    setup_dir.mkdir(parents=True, exist_ok=True)
    (setup_dir / "tradingview_capture_cc465_v1.json").write_text(
        json.dumps({"attempts": 1, "key": setup_key, "market": mkt, "status": "CAPTURED", "snapshot": snap}),
        encoding="utf-8",
    )
    (setup_dir / "run_context_v1.json").write_text(
        json.dumps({"plan_status_post": setup_key, "media": {"assets": [asset]}}),
        encoding="utf-8",
    )
    return setup_dir, asset


def _write_frozen_timeout(page_dir: Path, plan: dict, *, started_at: datetime, cause: str = "TRADINGVIEW_CAPTURE_WAIT_EXPIRED", attempts: int = 1, attempt_causes: list[str] | None = None) -> Path:
    page_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "key": "plan-analysis-" + plan["plan_id"],
        "market": plan["asset_id"],
        "attempts": attempts,
        "status": "TEXT_ONLY",
        "cause": cause,
        "first_cause": cause,
        "started_at_utc": started_at.isoformat(),
    }
    if attempt_causes is not None:
        state["attempt_causes"] = attempt_causes
    path = page_dir / "tradingview_capture_v1.json"
    path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    return path


def _make_direct_candidate(tmp_path: Path, plan: dict, run: dict, *, captured_at: datetime, interval: str = "60") -> dict:
    """Build a valid direct candidate dict for targeted single-invariant mutation tests."""
    mkt = plan["asset_id"]
    tv_sym = tv.SYMBOLS[mkt]
    ticker = tv_sym.split(":", 1)[1]
    raw_name = f"{ticker}_{captured_at:%Y-%m-%d_%H-%M-%S}.png"
    raw_path = tmp_path / "cached_direct" / raw_name
    raw_sha = _write_png(raw_path, size=(1600, 700))
    snap = {
        "path": str(raw_path.resolve()),
        "sha256": raw_sha,
        "width": 1600,
        "height": 700,
        "capture_ratio": "16:9",
        "tv_symbol": tv_sym,
        "interval": interval,
        "interval_label": tv.INTERVAL_LABELS[interval],
        "legend": f"{ticker} · {tv.INTERVAL_LABELS[interval]}",
        "page_title": f"{ticker} 60647.27 — TradingView",
        "chart_url": tv.chart_url(tv_sym, interval),
        "suggested_filename": raw_name,
        "captured_at_utc": captured_at.isoformat(),
        "policy": tv.POLICY,
        "levels_drawn": [],
        "target_drawn": False,
    }
    snap["price_scale_check"] = contract.not_compared(
        mkt,
        snap,
        "TRADINGVIEW_CONTEMPORANEOUS_MAIN_QUOTE_UNAVAILABLE",
    )
    return {
        "source_kind": "bound_setup_chart",
        "source_key": "plan-status-post-direct-test",
        "plan_id": plan["plan_id"],
        "symbol": mkt,
        "registration_hash": plan["registration_hash"],
        "analysis_result_hash": plan["analysis_result_hash"],
        "run_id": plan["run_id"],
        "freeze": {"immutable_hash": run["freeze"]["immutable_hash"]},
        "source_window": {
            "frozen_at_utc": run["freeze"]["frozen_at_utc"],
            "valid_until_utc": plan["entry_deadline_utc"],
            "window_id": plan["run_id"],
        },
        "rights_basis": tv.RIGHTS_BASIS,
        "public_use_rights": "PUBLIC_FREE_PAGE",
        "credit": tv.CREDIT,
        "provenance_status": "VERIFIED_TRADINGVIEW_DOWNLOAD_IMAGE",
        "caption": "Bitcoin: 1h chart of Bitcoin / US dollar (Coinbase spot). Chart: TradingView.",
        "alt_text": "TradingView 1h chart of Bitcoin / US dollar (Coinbase spot), captured 14:26 ET on 22 November 2026.",
        "snapshot": snap,
    }


# ---------------------------------------------------------------------------
# 1. Timeout Fallback PASS & End-to-End Publisher Write Boundary
# ---------------------------------------------------------------------------


def test_frozen_btcusd_timeout_reuses_exact_same_plan_setup_chart_and_passes_write_boundary(tmp_path, monkeypatch):
    """Replay the exact 22 Nov 2026 BTCUSD TRADINGVIEW_CAPTURE_WAIT_EXPIRED incident (CC-760 acceptance)."""
    outcomes = tmp_path / "outcomes.jsonl"
    monkeypatch.setattr(tv, "OUTCOMES", outcomes)
    monkeypatch.setattr(tv, "capture", lambda *a, **k: pytest.fail("frozen timeout must not start a browser"))

    run_root, _, plan, manuscript, frozen = _make_btc_plan_env(tmp_path)
    setup_captured = frozen + timedelta(minutes=7, seconds=31)  # 19:26:58Z
    capture_started = frozen + timedelta(minutes=19, seconds=35)  # 19:39:02Z
    timeout_now = frozen + timedelta(minutes=28, seconds=19)  # 19:47:46Z (20.8m old <= 60m cap)

    setup_dir, setup_asset = _make_bound_setup_dir(tmp_path, plan, captured_at=setup_captured)
    page_dir = tmp_path / "page"
    _write_frozen_timeout(page_dir, plan, started_at=capture_started, cause="TRADINGVIEW_CAPTURE_WAIT_EXPIRED", attempts=1)

    packet = pages.render(
        plan,
        manuscript,
        run_root=run_root,
        output_dir=page_dir,
        setup_post_dir=setup_dir,
        now=timeout_now,
    )

    assert len(packet["media_assets"]) == 1
    card = packet["media_assets"][0]
    assert card["modality"] == "tradingview_chart_snapshot"
    assert card["credit"] == tv.CREDIT
    assert card["rights_basis"] == tv.RIGHTS_BASIS
    assert card["provenance_status"] == "VERIFIED_TRADINGVIEW_DOWNLOAD_IMAGE"
    assert card["article_inclusion"] is True and card["canonical_article_media"] is True
    assert card["tradingview_snapshot"]["tv_symbol"] == "COINBASE:BTCUSD"
    assert card["tradingview_snapshot"]["sha256"] == setup_asset["tradingview_snapshot"]["sha256"]

    # Audit provenance recorded on asset, packet, run_context, and outcomes log.
    audit = card["cached_chart_fallback"]
    assert audit["policy"] == fb.POLICY
    assert audit["capture_cause"] == "TRADINGVIEW_CAPTURE_WAIT_EXPIRED"
    assert audit["plan_id"] == plan["plan_id"]
    assert audit["registration_hash"] == plan["registration_hash"]
    assert audit["symbol"] == "BTCUSD" and audit["tv_symbol"] == "COINBASE:BTCUSD"
    assert audit["public_use_rights_verified"] is True
    assert audit["invariants_verified"] == list(fb.INVARIANTS_VERIFIED)
    assert packet["cached_chart_fallback"] == audit

    # HTML includes exact image URI and TradingView attribution.
    html = (page_dir / "article.html").read_text(encoding="utf-8")
    assert Path(card["path"]).as_uri() in html
    assert tv.CREDIT in html

    # Capture state preserves original timeout cause; run_context marks text_fallback False.
    cap_state = json.loads((page_dir / "tradingview_capture_v1.json").read_bytes())
    assert cap_state["status"] == "TEXT_ONLY" and cap_state["cause"] == "TRADINGVIEW_CAPTURE_WAIT_EXPIRED"
    rc = json.loads((page_dir / "run_context_v1.json").read_bytes())
    assert rc["article"]["tradingview_text_fallback"] is False
    assert rc["article"]["cached_chart_fallback"] == audit

    outcome_rows = [json.loads(ln) for ln in outcomes.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert any(r["status"] == "CACHED_CHART_FALLBACK_USED" and r["cause"] == "TRADINGVIEW_CAPTURE_WAIT_EXPIRED" for r in outcome_rows)

    # Full coordinator + write boundary + decision 93 image register check.
    store = ContentOpsDurableStore(tmp_path / "page.sqlite3")
    # Seed the same-plan setup post in store so decision 93 recognizes related piece IDs.
    setup_key = setup_dir.name
    store.create_work_item(story_id=setup_key, work_item_id=setup_key, title="BTC setup", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(
        message_id=setup_key,
        work_item_id=setup_key,
        destination=posts.DESTINATION,
        payload=json.dumps({
            "key": setup_key,
            "kind": "setup",
            "state_alert_contract": "CC543_V1",
            "plan_id": plan["plan_id"],
            "source_plan_registration": plan["registration_hash"],
        }),
    )
    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=None,
        clock=lambda: timeout_now + timedelta(seconds=10),
        published_content_path=tmp_path / "published.jsonl",
    )
    registered = pages.register_page(store, packet)
    coordinator.register_plan(registered["page_id"], registered["plan"])
    row, = store.list_outbox_messages(destination="substack")
    intent = json.loads(row["payload"])

    validation = contract.validate_write(coordinator, intent, "substack")
    assert validation["first_image_type"] == "TRADINGVIEW_MARKET_CHART"
    assert validation["cached_chart_fallback_causes"] == ["TRADINGVIEW_CAPTURE_WAIT_EXPIRED"]
    assert not validation.get("text_fallback")

    monkeypatch.setattr(pages, "require_current_page", lambda pkt, **_: None)
    reserved = quality.before_article_write(coordinator, intent, "substack")
    assert reserved["lead_asset_id"] == card["asset_id"]


def test_live_capture_timeout_during_render_falls_back_to_bound_cached_chart(tmp_path, monkeypatch):
    """When live capture raises TRADINGVIEW_SNAPSHOT_TIMEOUT across bounded retries, reuse verified cached chart."""
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    calls = []

    def fail_timeout(market, interval, out_dir, **kwargs):
        calls.append(kwargs)
        raise tv.SnapshotError("TRADINGVIEW_SNAPSHOT_TIMEOUT")

    monkeypatch.setattr(tv, "capture", fail_timeout)

    now = datetime.now(timezone.utc)
    frozen = now - timedelta(minutes=15)
    run_root, _, plan, manuscript, _ = _make_btc_plan_env(tmp_path, frozen_at=frozen)
    setup_dir, setup_asset = _make_bound_setup_dir(tmp_path, plan, captured_at=now - timedelta(minutes=8))

    packet = pages.render(
        plan,
        manuscript,
        run_root=run_root,
        output_dir=tmp_path / "live_timeout_page",
        setup_post_dir=setup_dir,
    )
    assert len(calls) == 2
    card, = packet["media_assets"]
    assert card["modality"] == "tradingview_chart_snapshot"
    assert card["tradingview_snapshot"]["sha256"] == setup_asset["tradingview_snapshot"]["sha256"]
    assert card["cached_chart_fallback"]["capture_cause"] == "TRADINGVIEW_SNAPSHOT_TIMEOUT"


@pytest.mark.parametrize("cause,attempt_causes,expected_timeout", [
    ("TRADINGVIEW_CAPTURE_WAIT_EXPIRED", [], True),
    ("TRADINGVIEW_SNAPSHOT_TIMEOUT", ["TRADINGVIEW_SNAPSHOT_TIMEOUT"], True),
    ("TRADINGVIEW_WORKER_STEP_TIMEOUT:download", ["TRADINGVIEW_WORKER_STEP_TIMEOUT:download"], True),
    ("TRADINGVIEW_WORKER_BUDGET_SPENT:paint", ["TRADINGVIEW_WORKER_BUDGET_SPENT:paint"], True),
    (tv.CAPTURE_INTERRUPTED, [tv.CAPTURE_INTERRUPTED, "TRADINGVIEW_WORKER_STEP_TIMEOUT:download"], True),
    ("TRADINGVIEW_PRICE_SCALE_MISMATCH", ["TRADINGVIEW_PRICE_SCALE_MISMATCH"], False),
    ("PUBLIC_REDISTRIBUTION_NOT_LICENSED", ["PUBLIC_REDISTRIBUTION_NOT_LICENSED"], False),
    ("TRADINGVIEW_SNAPSHOT_NOT_THIS_SYMBOL", ["TRADINGVIEW_SNAPSHOT_NOT_THIS_SYMBOL"], False),
])
def test_only_timeout_or_expiry_causes_activate_cached_fallback(cause, attempt_causes, expected_timeout):
    state = {
        "key": "plan-analysis-plan_x",
        "market": "BTCUSD",
        "status": "TEXT_ONLY",
        "cause": cause,
        "first_cause": cause,
        "attempt_causes": attempt_causes,
    }
    ok, resolved = fb.is_timeout_capture_state(state, expected_key="plan-analysis-plan_x", expected_market="BTCUSD")
    assert ok is expected_timeout
    assert (resolved is not None) is expected_timeout


def test_non_timeout_capture_failure_never_substitutes_cached_chart(tmp_path, monkeypatch):
    """Non-timeout capture errors (e.g. price scale mismatch) must fail closed on cached substitution."""
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    run_root, _, plan, manuscript, frozen = _make_btc_plan_env(tmp_path)
    setup_dir, _ = _make_bound_setup_dir(tmp_path, plan, captured_at=frozen + timedelta(minutes=5))
    page_dir = tmp_path / "non_timeout_page"
    _write_frozen_timeout(
        page_dir,
        plan,
        started_at=frozen + timedelta(minutes=10),
        cause="TRADINGVIEW_PRICE_SCALE_MISMATCH",
        attempts=2,
    )
    packet = pages.render(
        plan,
        manuscript,
        run_root=run_root,
        output_dir=page_dir,
        setup_post_dir=setup_dir,
        now=frozen + timedelta(minutes=20),
    )
    # Must NOT substitute TradingView cached chart; falls through to plan fact card keeping original cause.
    card, = packet["media_assets"]
    assert card["modality"] == "plan_fact_card"
    assert "cached_chart_fallback" not in card
    assert card["plan_chart_fallback"]["cause"] == "TRADINGVIEW_PRICE_SCALE_MISMATCH"


# ---------------------------------------------------------------------------
# 2. All 5 Fail-Closed Invariant Rejections
# ---------------------------------------------------------------------------


def test_invariant_a_symbol_feed_interval_ratio_and_scale_mismatches_rejected(tmp_path):
    _, run, plan, manuscript, frozen = _make_btc_plan_env(tmp_path)
    captured = frozen + timedelta(minutes=6)
    now = frozen + timedelta(minutes=20)

    # Control: valid candidate passes.
    base = _make_direct_candidate(tmp_path, plan, run, captured_at=captured)
    assert fb.validate_cached_chart_candidate(base, plan=plan, run=run, manuscript=manuscript, now=now)["tv_symbol"] == "COINBASE:BTCUSD"

    # (a1) Cross-market symbol mismatch (XAUUSD chart for BTCUSD plan)
    bad_market = deepcopy(base)
    bad_market["symbol"] = "XAUUSD"
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_SYMBOL_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_market, plan=plan, run=run, manuscript=manuscript, now=now)

    # (a2) Wrong TradingView feed for same asset (OANDA/BITSTAMP instead of COINBASE:BTCUSD)
    bad_feed = deepcopy(base)
    bad_feed["snapshot"]["tv_symbol"] = "BITSTAMP:BTCUSD"
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_SYMBOL_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_feed, plan=plan, run=run, manuscript=manuscript, now=now)

    # (a3) Wrong chart URL
    bad_url = deepcopy(base)
    bad_url["snapshot"]["chart_url"] = "https://www.tradingview.com/chart/?symbol=FX_IDC:XAUUSD&interval=60"
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_SYMBOL_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_url, plan=plan, run=run, manuscript=manuscript, now=now)

    # (a4) Wrong suggested filename ticker
    bad_fname = deepcopy(base)
    bad_fname["snapshot"]["suggested_filename"] = "XAUUSD_2026-11-22_19-25-27.png"
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_SYMBOL_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_fname, plan=plan, run=run, manuscript=manuscript, now=now)

    # (a5) Wrong interval (4h instead of 1h)
    bad_interval = deepcopy(base)
    bad_interval["snapshot"]["interval"] = "240"
    bad_interval["snapshot"]["chart_url"] = tv.chart_url("COINBASE:BTCUSD", "240")
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_INTERVAL_OR_RATIO_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_interval, plan=plan, run=run, manuscript=manuscript, now=now)

    # (a6) Wrong aspect ratio (4:5 portrait instead of 16:9 canonical)
    bad_ratio = deepcopy(base)
    bad_ratio["snapshot"]["capture_ratio"] = "4:5"
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_INTERVAL_OR_RATIO_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_ratio, plan=plan, run=run, manuscript=manuscript, now=now)

    # (a7) Unsafe plain_price_scale_cause or missing price_scale_check
    bad_scale = deepcopy(base)
    bad_scale["snapshot"]["plain_price_scale_cause"] = tv.PRICE_SCALE_MISMATCH
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_PRICE_SCALE_INVALID"):
        fb.validate_cached_chart_candidate(bad_scale, plan=plan, run=run, manuscript=manuscript, now=now)

    no_scale = deepcopy(base)
    no_scale["snapshot"].pop("price_scale_check")
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_PRICE_SCALE_INVALID"):
        fb.validate_cached_chart_candidate(no_scale, plan=plan, run=run, manuscript=manuscript, now=now)


def test_invariant_b_plan_id_missing_mismatch_and_conflict_rejected(tmp_path):
    _, run, plan, manuscript, frozen = _make_btc_plan_env(tmp_path)
    captured = frozen + timedelta(minutes=6)
    now = frozen + timedelta(minutes=20)
    base = _make_direct_candidate(tmp_path, plan, run, captured_at=captured)

    # (b1) Missing plan_id (unbound market-only cache must fail closed)
    missing = deepcopy(base)
    missing.pop("plan_id")
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_PLAN_ID_MISSING"):
        fb.validate_cached_chart_candidate(missing, plan=plan, run=run, manuscript=manuscript, now=now)

    # (b2) Different plan_id for the exact same BTCUSD symbol
    other = deepcopy(base)
    other["plan_id"] = "plan_other_btcusd_99999999"
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_PLAN_ID_MISMATCH"):
        fb.validate_cached_chart_candidate(other, plan=plan, run=run, manuscript=manuscript, now=now)

    # (b3) Conflicting plan_id inside nested plan_binding
    conflict = deepcopy(base)
    conflict["plan_binding"] = {"plan_id": "plan_conflicting_id"}
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_PLAN_ID_MISMATCH"):
        fb.validate_cached_chart_candidate(conflict, plan=plan, run=run, manuscript=manuscript, now=now)


def test_invariant_c_source_window_and_freshness_cap_mismatches_rejected(tmp_path):
    _, run, plan, manuscript, frozen = _make_btc_plan_env(tmp_path)
    captured = frozen + timedelta(minutes=6)
    now = frozen + timedelta(minutes=20)
    base = _make_direct_candidate(tmp_path, plan, run, captured_at=captured)

    # (c1) Exceeds 60-min freshness cap (61 min old)
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_SOURCE_WINDOW_STALE"):
        fb.validate_cached_chart_candidate(
            base, plan=plan, run=run, manuscript=manuscript, now=captured + timedelta(minutes=61)
        )

    # (c2) Invalid / unbounded max_age_seconds
    for bad_cap in (0, -10, fb.MAX_ALLOWED_CACHE_AGE_SECONDS + 1):
        with pytest.raises(fb.CachedChartFallbackError, match="CC760_SOURCE_WINDOW_INVALID"):
            fb.validate_cached_chart_candidate(
                base, plan=plan, run=run, manuscript=manuscript, now=now, max_age_seconds=bad_cap
            )

    # (c3) Captured BEFORE plan freeze
    before_freeze = deepcopy(base)
    before_freeze["snapshot"]["captured_at_utc"] = (frozen - timedelta(minutes=2)).isoformat()
    before_freeze["snapshot"]["price_scale_check"]["captured_at_utc"] = before_freeze["snapshot"]["captured_at_utc"]
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_SOURCE_WINDOW_MISMATCH"):
        fb.validate_cached_chart_candidate(before_freeze, plan=plan, run=run, manuscript=manuscript, now=now)

    # (c4) Future-dated capture (captured_at > now)
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_SOURCE_WINDOW_MISMATCH"):
        fb.validate_cached_chart_candidate(
            base, plan=plan, run=run, manuscript=manuscript, now=captured - timedelta(seconds=5)
        )

    # (c5) Captured AFTER entry deadline
    after_deadline = deepcopy(base)
    late_ts = (frozen + timedelta(hours=13)).isoformat()
    after_deadline["snapshot"]["captured_at_utc"] = late_ts
    after_deadline["snapshot"]["price_scale_check"]["captured_at_utc"] = late_ts
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_SOURCE_WINDOW_MISMATCH"):
        fb.validate_cached_chart_candidate(
            after_deadline, plan=plan, run=run, manuscript=manuscript, now=frozen + timedelta(hours=13, minutes=5)
        )

    # (c6) Captured AFTER plan final close
    closed = {"status": "INVALIDATED", "status_at_utc": (captured - timedelta(seconds=30)).isoformat()}
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_SOURCE_WINDOW_MISMATCH"):
        fb.validate_cached_chart_candidate(
            base, plan=plan, run=run, manuscript=manuscript, now=now, final_status=closed
        )

    # (c7) Naive timestamp (missing timezone)
    naive = deepcopy(base)
    naive["snapshot"]["captured_at_utc"] = "2026-11-22T19:25:27"
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_SOURCE_WINDOW_INVALID"):
        fb.validate_cached_chart_candidate(naive, plan=plan, run=run, manuscript=manuscript, now=now)

    # (c8) Mismatched explicit source_window.frozen_at_utc & window_id
    bad_sw = deepcopy(base)
    bad_sw["source_window"]["frozen_at_utc"] = (frozen - timedelta(hours=1)).isoformat()
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_SOURCE_WINDOW_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_sw, plan=plan, run=run, manuscript=manuscript, now=now)

    bad_wid = deepcopy(base)
    bad_wid["source_window"]["window_id"] = "request-different-window"
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_SOURCE_WINDOW_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_wid, plan=plan, run=run, manuscript=manuscript, now=now)


def test_invariant_d_revision_and_byte_integrity_mismatches_rejected(tmp_path):
    _, run, plan, manuscript, frozen = _make_btc_plan_env(tmp_path)
    captured = frozen + timedelta(minutes=6)
    now = frozen + timedelta(minutes=20)
    base = _make_direct_candidate(tmp_path, plan, run, captured_at=captured)

    # (d1) Missing registration_hash
    missing_reg = deepcopy(base)
    missing_reg.pop("registration_hash")
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_REVISION_MISSING"):
        fb.validate_cached_chart_candidate(missing_reg, plan=plan, run=run, manuscript=manuscript, now=now)

    # (d2) Wrong registration_hash
    bad_reg = deepcopy(base)
    bad_reg["registration_hash"] = "0" * 64
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_REVISION_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_reg, plan=plan, run=run, manuscript=manuscript, now=now)

    # (d3) Wrong analysis_result_hash
    bad_res = deepcopy(base)
    bad_res["analysis_result_hash"] = "a" * 64
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_REVISION_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_res, plan=plan, run=run, manuscript=manuscript, now=now)

    # (d4) Wrong run_id
    bad_run = deepcopy(base)
    bad_run["run_id"] = "request-other-run"
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_REVISION_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_run, plan=plan, run=run, manuscript=manuscript, now=now)

    # (d5) Wrong freeze immutable_hash
    bad_freeze = deepcopy(base)
    bad_freeze["freeze"]["immutable_hash"] = "b" * 64
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_REVISION_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_freeze, plan=plan, run=run, manuscript=manuscript, now=now)

    # (d6) Wrong plan_revision & reader_revision
    plan_with_rev = {**plan, "plan_revision": "rev-2"}
    bad_rev = {**deepcopy(base), "plan_revision": "rev-1"}
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_REVISION_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_rev, plan=plan_with_rev, run=run, manuscript=manuscript, now=now)

    bad_ms_rev = {**deepcopy(base), "reader_revision": 99}
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_REVISION_MISMATCH"):
        fb.validate_cached_chart_candidate(bad_ms_rev, plan=plan, run=run, manuscript=manuscript, now=now)

    # (d7) Tampered chart PNG bytes on disk
    tampered = deepcopy(base)
    _write_png(Path(tampered["snapshot"]["path"]), size=(1600, 700), color=(200, 10, 10))
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_CHART_BYTES_MISMATCH"):
        fb.validate_cached_chart_candidate(tampered, plan=plan, run=run, manuscript=manuscript, now=now)


@pytest.mark.parametrize("mutator,expected_code", [
    (lambda c: c.update(rights_basis=""), "CC760_PUBLIC_RIGHTS_INVALID"),
    (lambda c: c.update(rights_basis="Internal research only"), "CC760_PUBLIC_RIGHTS_INVALID"),
    (lambda c: c.update(credit="Unknown chart"), "CC760_PUBLIC_RIGHTS_INVALID"),
    (lambda c: c.update(provenance_status="UNVERIFIED"), "CC760_PUBLIC_RIGHTS_INVALID"),
    (lambda c: c.update(public_use_rights=False), "CC760_PUBLIC_RIGHTS_FORBIDDEN"),
    (lambda c: c.update(public_use_rights="INTERNAL_ONLY"), "CC760_PUBLIC_RIGHTS_FORBIDDEN"),
    (lambda c: c.update(public_use_rights="PAID_ONLY"), "CC760_PUBLIC_RIGHTS_FORBIDDEN"),
    (lambda c: c.update(public_use_rights={"allowed": True, "internal_only": True}), "CC760_PUBLIC_RIGHTS_FORBIDDEN"),
    (lambda c: c.update(audience="paid_subscribers"), "CC760_PUBLIC_RIGHTS_FORBIDDEN"),
    # Private text, R-multiple, and profit-target leaks
    (lambda c: c.update(caption="Bitcoin chart for account 279805139. Chart: TradingView."), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
    (lambda c: c.update(alt_text="Exness MT5 0.5 lots chart of Bitcoin."), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
    (lambda c: c.update(caption="Chart drafted by Claude AI desk. Chart: TradingView."), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
    (lambda c: c.update(caption="Sourced from JIM_X_LIST. Chart: TradingView."), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
    (lambda c: c.update(caption="Preview at https://fatcat2109.github.io/chart. Chart: TradingView."), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
    (lambda c: c.update(caption="Captured at 14:26 GMT+7. Chart: TradingView."), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
    (lambda c: c.update(caption="Setup expects +1.8R move on Bitcoin. Chart: TradingView."), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
    (lambda c: c.update(alt_text="Bitcoin chart, closed -0.5R expectancy."), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
    (lambda c: c.update(notes=["Internal result_r +2.1R"]), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
    (lambda c: c.update(caption="Bitcoin chart with profit target 55,000. Chart: TradingView."), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
    (lambda c: c["snapshot"].update(target_drawn=True), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
    (lambda c: c["snapshot"].update(r_multiple=1.75), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
    (lambda c: c["snapshot"].update(account_id="279805139"), "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
])
def test_invariant_e_public_use_rights_and_privacy_r_multiple_leaks_rejected(tmp_path, mutator, expected_code):
    _, run, plan, manuscript, frozen = _make_btc_plan_env(tmp_path)
    captured = frozen + timedelta(minutes=6)
    now = frozen + timedelta(minutes=20)
    cand = _make_direct_candidate(tmp_path, plan, run, captured_at=captured)
    mutator(cand)
    with pytest.raises(fb.CachedChartFallbackError, match=expected_code):
        fb.validate_cached_chart_candidate(cand, plan=plan, run=run, manuscript=manuscript, now=now)


def test_invariant_e_private_x_list_run_sentence_leak_rejected(tmp_path):
    secret_line = "Private X-list insider note about a confidential desk catalyst."
    _, run, plan, manuscript, frozen = _make_btc_plan_env(tmp_path, private_line=secret_line)
    captured = frozen + timedelta(minutes=6)
    now = frozen + timedelta(minutes=20)
    cand = _make_direct_candidate(tmp_path, plan, run, captured_at=captured)
    cand["caption"] = f"Bitcoin chart: {secret_line} Chart: TradingView."
    with pytest.raises(fb.CachedChartFallbackError, match="CC760_PRIVATE_OR_R_MULTIPLE_LEAK"):
        fb.validate_cached_chart_candidate(cand, plan=plan, run=run, manuscript=manuscript, now=now)


# ---------------------------------------------------------------------------
# 3. End-to-End Fail-Closed Render & Write-Boundary Tamper Rejections
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_field,expected_refusal", [
    ("symbol", "CC760_SYMBOL_MISMATCH"),
    ("plan_id", "CC760_PLAN_ID_MISMATCH"),
    ("stale", "CC760_SOURCE_WINDOW_STALE"),
    ("revision", "CC760_REVISION_MISMATCH"),
    ("rights", "CC760_PUBLIC_RIGHTS_FORBIDDEN"),
    ("r_leak", "CC760_PRIVATE_OR_R_MULTIPLE_LEAK"),
])
def test_render_fails_closed_on_each_invariant_violation_and_keeps_capture_cause(
    tmp_path, monkeypatch, bad_field, expected_refusal
):
    """End-to-end render must refuse any invalid cached chart, record refusal cause, and keep capture cause."""
    outcomes = tmp_path / "outcomes.jsonl"
    monkeypatch.setattr(tv, "OUTCOMES", outcomes)
    run_root, _, plan, manuscript, frozen = _make_btc_plan_env(tmp_path)
    captured = frozen + timedelta(minutes=6)
    now = frozen + timedelta(minutes=20)

    kwargs = {}
    if bad_field == "symbol":
        kwargs["market"] = "XAUUSD"
    elif bad_field == "plan_id":
        kwargs["record_overrides"] = {"plan_id": "plan_different_id"}
    elif bad_field == "stale":
        now = captured + timedelta(minutes=65)
    elif bad_field == "revision":
        kwargs["record_overrides"] = {"source_plan_registration": "1" * 64}
    elif bad_field == "rights":
        kwargs["public_use_rights"] = "INTERNAL_ONLY"
    elif bad_field == "r_leak":
        kwargs["asset_overrides"] = {"caption": "Bitcoin +2.5R winner. Chart: TradingView."}

    setup_dir, _ = _make_bound_setup_dir(tmp_path, plan, captured_at=captured, **kwargs)
    page_dir = tmp_path / f"page_{bad_field}"
    _write_frozen_timeout(page_dir, plan, started_at=frozen + timedelta(minutes=12))

    packet = pages.render(
        plan,
        manuscript,
        run_root=run_root,
        output_dir=page_dir,
        setup_post_dir=setup_dir,
        now=now,
    )
    # Never publishes the rejected cached chart; falls back to CC-290 fact card with preserved capture cause.
    card, = packet["media_assets"]
    assert card["modality"] == "plan_fact_card"
    assert card["plan_chart_fallback"]["cause"] == "TRADINGVIEW_CAPTURE_WAIT_EXPIRED"
    assert "cached_chart_fallback" not in packet
    assert any(r["cause"] == expected_refusal for r in packet["cached_chart_fallback_refusals"])
    # Original capture state untouched.
    cap = json.loads((page_dir / "tradingview_capture_v1.json").read_bytes())
    assert cap["status"] == "TEXT_ONLY" and cap["cause"] == "TRADINGVIEW_CAPTURE_WAIT_EXPIRED"


@pytest.mark.parametrize("tamper,expected_error", [
    (lambda a: a["cached_chart_fallback"].update(plan_id="plan_wrong"), "CC760_PLAN_ID_MISMATCH"),
    (lambda a: a["cached_chart_fallback"].update(registration_hash="0" * 64), "CC760_REVISION_MISMATCH"),
    (lambda a: a["cached_chart_fallback"].update(symbol="XAUUSD"), "CC760_SYMBOL_MISMATCH"),
    (lambda a: a["cached_chart_fallback"].update(public_use_rights_verified=False), "CC760_FALLBACK_BINDING_INVALID"),
    (lambda a: a["cached_chart_fallback"].update(capture_cause="OTHER"), "CC760_FALLBACK_BINDING_INVALID"),
    (lambda a: a["cached_chart_fallback"].update(max_cache_age_seconds=999999), "CC760_SOURCE_WINDOW_INVALID"),
    (lambda a: a["cached_chart_fallback"].update(source_window_start_utc="2026-11-20T00:00:00+00:00"), "CC760_FALLBACK_BINDING_INVALID"),
])
def test_write_boundary_rejects_tampered_cached_fallback_metadata(tmp_path, monkeypatch, tamper, expected_error):
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    run_root, _, plan, manuscript, frozen = _make_btc_plan_env(tmp_path)
    setup_captured = frozen + timedelta(minutes=7)
    capture_started = frozen + timedelta(minutes=19)
    timeout_now = frozen + timedelta(minutes=28)
    setup_dir, _ = _make_bound_setup_dir(tmp_path, plan, captured_at=setup_captured)
    page_dir = tmp_path / "tamper_page"
    _write_frozen_timeout(page_dir, plan, started_at=capture_started)

    packet = pages.render(plan, manuscript, run_root=run_root, output_dir=page_dir, setup_post_dir=setup_dir, now=timeout_now)
    tamper(packet["media_assets"][0])
    rc_path = page_dir / "run_context_v1.json"
    rc = json.loads(rc_path.read_bytes())
    rc["media"]["assets"] = packet["media_assets"]
    rc_path.write_text(json.dumps(rc), encoding="utf-8")

    store = ContentOpsDurableStore(tmp_path / "tamper.sqlite3")
    coordinator = DurablePublicationCoordinator(
        store=store,
        transport_runtime=None,
        clock=lambda: timeout_now + timedelta(seconds=10),
        published_content_path=tmp_path / "published.jsonl",
    )
    registered = pages.register_page(store, packet)
    with pytest.raises(ValueError, match=expected_error):
        coordinator.register_plan(registered["page_id"], registered["plan"])


# ---------------------------------------------------------------------------
# 4. Active-Plan Wiring Through plan_reader_editorial_v1.run_due
# ---------------------------------------------------------------------------


def test_run_due_wires_setup_post_dir_for_active_plan_on_timeout(tmp_path, monkeypatch):
    """Verify run_due forwards setup_post_dir for an ACTIVE plan so timeout fallback works end-to-end."""
    monkeypatch.setattr(tv, "OUTCOMES", tmp_path / "outcomes.jsonl")
    run_root, _, plan, manuscript, frozen = _make_btc_plan_env(tmp_path)
    setup_captured = frozen + timedelta(minutes=7)
    capture_started = frozen + timedelta(minutes=19)
    now = frozen + timedelta(minutes=28)

    store_path = tmp_path / "contentops.sqlite3"
    store = ContentOpsDurableStore(store_path)
    setup_key = "plan-status-post-b1425a186e37fa69ea897d903d88cfed"
    setup_dir, setup_asset = _make_bound_setup_dir(tmp_path, plan, captured_at=setup_captured, setup_key=setup_key)

    setup_row = {
        "key": setup_key,
        "kind": "setup",
        "plan_id": plan["plan_id"],
        "symbol": plan["asset_id"],
        "thread_contract": editorial.reader.THREAD_CONTRACT,
        "analysis_copy_contract": editorial.reader.NINE_LAYER_COPY,
        "source_plan": plan,
        "source_plan_registration": plan["registration_hash"],
    }
    store.create_work_item(story_id=setup_key, work_item_id=setup_key, title="BTC setup", target_surface="MULTI_PLATFORM")
    store.register_outbox_message(
        message_id=setup_key,
        work_item_id=setup_key,
        destination=posts.DESTINATION,
        payload=json.dumps(setup_row),
    )

    pages_root = tmp_path / "daily_app_outputs" / "plan_analysis"
    page_dir = pages_root / ("plan-analysis-" + plan["plan_id"])
    _write_frozen_timeout(page_dir, plan, started_at=capture_started)
    (page_dir / editorial.DRAFT_MANUSCRIPT).write_text(json.dumps(manuscript), encoding="utf-8")

    # Bind run_root and now for pages.render inside cached_only run_due.
    orig_render = pages.render

    def bound_render(*args, **kwargs):
        kwargs.setdefault("run_root", run_root)
        kwargs.setdefault("now", now)
        return orig_render(*args, **kwargs)

    monkeypatch.setattr(pages, "render", bound_render)
    continued = []
    monkeypatch.setattr(
        pages,
        "continue_page",
        lambda store, pkt, **kw: continued.append(pkt["page_id"]) or {"status": "STUB_CONTINUATION"},
    )

    current_plan = {
        **plan,
        "status": "WAITING",
        "last_quote": {
            "instrument": "BTCUSD",
            "price": 60500,
            "quoted_at_utc": (now - timedelta(seconds=30)).isoformat(),
            "known_at_utc": (now - timedelta(seconds=10)).isoformat(),
            "source_hash": "a" * 64,
        },
    }
    result = editorial.run_due(
        store,
        {"status": {"plans": [current_plan]}},
        root=pages_root,
        rollout={"store_path": str(store_path)},
        now=now,
        publish=True,
        cached_only=True,
    )
    stored = editorial.publication_packet(store, plan)
    assert stored is not None, result
    assert continued == [stored["page_id"]]
    card, = stored["media_assets"]
    assert card["modality"] == "tradingview_chart_snapshot"
    assert card["tradingview_snapshot"]["sha256"] == setup_asset["tradingview_snapshot"]["sha256"]
    assert card["cached_chart_fallback"]["source_key"] == setup_key
    assert card["cached_chart_fallback"]["capture_cause"] == "TRADINGVIEW_CAPTURE_WAIT_EXPIRED"
