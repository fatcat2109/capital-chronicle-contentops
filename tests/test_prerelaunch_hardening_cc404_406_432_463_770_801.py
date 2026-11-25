"""Pre-relaunch hardening & regression tests for CC-404, CC-406, CC-432, CC-463, CC-770, and CC-801.

Strictly offline and hermetic (tmp_path + fakes only; zero network calls, zero
live Chrome/Neo/BrowserOS actions, zero writes to A:\\, zero public posts).
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import sys

from PIL import Image
import pytest

from live_contentops import agy_editorial_assist_v1 as assist
from live_contentops import agy_neo_answerer_v1 as answerer
from live_contentops import event_pack_v1 as event_packs
from live_contentops import event_public_record_v1 as event_records
from live_contentops import event_timestamp_v1 as ots
from live_contentops import light_model_caller_v1 as light
from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import publication_image_contract_v1 as img_contract
from live_contentops import tradingview_snapshot_v1 as tv
from live_contentops import vietnamese_gold_note_v1 as gold
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from tests.test_event_pack_cc404 import REVIEW as EVENT_REVIEW_TIME, packet as event_packet, write as write_json
from tests.test_plan_analysis_pages_cc432 import source as plan_page_source  # noqa: F401
from tests.test_publication_image_contract_cc463 import message_with
from tests.test_tradingview_snapshot_cc314 import FIXTURE as TV_FIXTURE
from tests.test_vietnamese_gold_note_cc406 import TEXT as GOLD_TEXT, fixture_context as gold_fixture_context


# ---------------------------------------------------------------------------
# CC-406: Vietnamese gold note post-Nov-13 copy guard hardening
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_addition,cause", [
    ("Theo CME FedWatch, xác suất giữ nguyên là 0.4%.", "PREDICTION_MARKET_NUMBER"),
    ("Kalshi định giá 0.4% cho đợt tăng này.", "PREDICTION_MARKET_NUMBER"),
    ("Polymarket đặt 0.3% cho kịch bản hạ lãi suất.", "PREDICTION_MARKET_NUMBER"),
    ("Bản tin do Claude và Fable tổng hợp.", "BRAND_INTERNAL_LABEL"),
    ("Phân tích do Codex tạo tự động.", "BRAND_INTERNAL_LABEL"),
    ("Ghi chú từ Antigravity.", "BRAND_INTERNAL_LABEL"),
    ("Nguồn từ X-list riêng.", "BRAND_INTERNAL_LABEL"),
    ("Xem thêm tại fatcat2109.github.io/note.", "PREVIEW_HOST_LINK_FORBIDDEN"),
    ("Bản xem trước ở example.pages.dev.", "PREVIEW_HOST_LINK_FORBIDDEN"),
    ("Mục tiêu giá vàng ở mức cao hơn.", "PRIVATE_DETAIL_OR_PERSONAL_ADVICE"),
    ("Take-profit nếu vàng hồi mạnh.", "PRIVATE_DETAIL_OR_PERSONAL_ADVICE"),
])
def test_cc406_gold_note_rejects_fedwatch_ai_labels_preview_links_and_targets(
    tmp_path, monkeypatch, bad_addition, cause
):
    context, _ = gold_fixture_context(tmp_path, monkeypatch)
    body = GOLD_TEXT.replace(gold.NOTICE, f"{bad_addition}\n\n{gold.NOTICE}")
    with pytest.raises(ValueError, match=cause):
        gold.validate_note({"text": body, "fact_ids": ["headline", "core"]}, context)


def test_cc406_gold_note_still_accepts_qualitative_rate_futures_without_numbers(tmp_path, monkeypatch):
    context, _ = gold_fixture_context(tmp_path, monkeypatch)
    note = GOLD_TEXT.replace(
        "Lạm phát dai dẳng có thể giữ lãi suất cao, gây bất lợi cho vàng.",
        "Hợp đồng lãi suất nghiêng về khả năng giữ lãi suất cao, gây bất lợi cho vàng.",
    )
    assert gold.validate_note({"text": note, "fact_ids": ["headline", "core"]}, context)["fact_ids"] == [
        "headline", "core",
    ]


# ---------------------------------------------------------------------------
# CC-404: Event pack Decision 157 target guard, MANAGED_EXIT wording, preview
# host link refusal, and ledger .ots digest cross-check
# ---------------------------------------------------------------------------

def test_cc404_event_review_renders_managed_exit_in_reader_words_not_internal_enum(tmp_path):
    inputs = event_packet(tmp_path)
    status = json.loads(Path(inputs["plan_status_record"]["path"]).read_bytes())
    status.pop("content_hash")
    status["scored_calls"] = [{"public_call_id": "call-a", "result": "MANAGED_EXIT"}]
    inputs["plan_status_record"] = write_json(tmp_path, "managed-exit-status.json", status, seal=True)

    view = event_packs.compose(inputs, "review", now=EVENT_REVIEW_TIME)
    assert "Closed by its plan rule" in view["body_markdown"]
    assert "MANAGED_EXIT" not in view["body_markdown"]
    assert view["review_rows"][0]["result_text"] == "Closed by its plan rule"


def test_cc404_post_nov22_event_pack_refuses_profit_target_while_historical_keeps_bytes(tmp_path):
    inputs = event_packet(tmp_path)
    dec_release = "2026-12-04T13:30:00Z"
    dec_frozen = "2026-12-03T12:00:00Z"
    dec_preview = datetime(2026, 12, 4, 10, 0, tzinfo=timezone.utc)

    doc = json.loads(Path(inputs["frozen_public_record"]["path"]).read_bytes())
    doc["event_time_utc"] = dec_release
    doc["frozen_at_utc"] = dec_frozen
    doc["reaction_map"][0]["horizon"] = "price target 4,100 over 24 hours"
    inputs["frozen_public_record"] = write_json(tmp_path, "dec-freeze.json", doc)
    inputs["planned_release_utc"] = dec_release
    inputs.pop("calls_ledger_record", None)

    with pytest.raises(ValueError, match="SCENARIO_VOICE_TARGET_FORBIDDEN|PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"):
        event_packs.compose(inputs, "preview", now=dec_preview)


def test_cc404_derivative_payloads_refuse_preview_host_canonical_url(tmp_path):
    inputs = event_packet(tmp_path)
    view = event_packs.compose(inputs, "preview", now=datetime(2026, 11, 6, 10, tzinfo=timezone.utc))
    parent = {
        "native_payload": {k: view[k] for k in ("title", "subtitle", "body_markdown")},
        "media_assets": [],
        "inputs": inputs,
    }
    with pytest.raises(ValueError, match="PREVIEW_HOST_LINK_FORBIDDEN"):
        event_packs.derivative_payloads(parent, "https://fatcat2109.github.io/p/event", None)


def test_cc404_ledger_ots_attachment_refuses_file_digest_mismatch(tmp_path, monkeypatch):
    inputs = event_packet(tmp_path)
    freeze_spec = inputs["frozen_public_record"]
    ledger_spec = inputs["calls_ledger_record"]
    ts_root = tmp_path / "ots-root"

    # Write valid freeze timestamp metadata + proof
    freeze_dir = ts_root / inputs["event_id"] / freeze_spec["sha256"]
    freeze_dir.mkdir(parents=True)
    freeze_proof = freeze_dir / "frozen-public.json.ots"
    freeze_proof.write_bytes(b"freeze-proof")
    (freeze_dir / "timestamp.json").write_text(
        json.dumps({"path": freeze_spec["path"], "proof_path": str(freeze_proof)}), encoding="utf-8"
    )

    # Write ledger timestamp metadata whose inspected file_sha256 disagrees with ledger_spec["sha256"]
    ledger_dir = ts_root / (inputs["event_id"] + "-ledger") / ledger_spec["sha256"]
    ledger_dir.mkdir(parents=True)
    ledger_proof = ledger_dir / "ledger.json.ots"
    ledger_proof.write_bytes(b"ledger-proof")
    (ledger_dir / "timestamp.json").write_text(
        json.dumps({"path": ledger_spec["path"], "proof_path": str(ledger_proof)}), encoding="utf-8"
    )

    def fake_inspect(source, proof):
        if Path(proof) == freeze_proof:
            return {"file_sha256": freeze_spec["sha256"], "proof_sha256": sha256(b"freeze-proof").hexdigest()}
        return {"file_sha256": "0" * 64, "proof_sha256": sha256(b"ledger-proof").hexdigest()}

    monkeypatch.setattr(ots, "inspect", fake_inspect)
    article = {
        "article_type": "EVENT_PREVIEW",
        "event_pack_stage": "preview",
        "frozen_public_record": {
            "event_id": inputs["event_id"],
            "event_time_utc": inputs["planned_release_utc"],
            "frozen_at_utc": json.loads(Path(freeze_spec["path"]).read_bytes())["frozen_at_utc"],
            "path": freeze_spec["path"],
            "sha256": freeze_spec["sha256"],
        },
        "calls_ledger_record": ledger_spec,
    }
    with pytest.raises(ValueError, match="OTS_PROOF_FILE_DIGEST_MISMATCH"):
        event_records.attachments_for_article(article, media_dir=tmp_path / "media", timestamp_root=ts_root)


# ---------------------------------------------------------------------------
# CC-432: Decision 113 model-label parity & USTEC full-analysis page check
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("model_label", [
    "Drafted by Fable 5.2.",
    "Prepared with Codex.",
    "Reviewed by Anthropic models.",
    "Built with OpenAI tooling.",
    "Summarized by Sonnet.",
    "Checked by Haiku.",
])
def test_cc432_public_filter_rejects_all_model_and_vendor_names(model_label):
    with pytest.raises(ValueError, match="PLAN_ANALYSIS_DESK_AI_LABEL_FORBIDDEN"):
        pages.public_filter(model_label)


def test_cc432_public_filter_allows_ai_as_market_theme_and_renders_ustec_page(plan_page_source, tmp_path):
    assert pages.public_filter("AI spending lifts chipmaker earnings across the Nasdaq 100.")["status"] == "PASS"
    root, folder, plan, manuscript = plan_page_source
    plan["asset_id"] = "USTEC"
    manuscript["title"] = "Nasdaq 100: conditional AI spending and yields view"
    packet = pages.render(plan, manuscript, run_root=root, output_dir=tmp_path / "ustec-page")
    body = packet["native_payload"]["body_markdown"]
    assert all(title in body for _, title in pages.SECTIONS)
    assert "USTEC" not in body
    assert len(packet["numeric_bindings"]) == 7


# ---------------------------------------------------------------------------
# CC-463: USTEC & 7-market image contract, closed-market clock, IG 4:5, audit
# ---------------------------------------------------------------------------

def test_cc463_closed_market_comparison_clock_covers_ustec_cash_fx_and_btc():
    # Wednesday 25 Nov 2026 15:00Z = 10:00 AM ET (US cash open)
    cash_open = datetime(2026, 11, 25, 15, 0, tzinfo=timezone.utc)
    assert img_contract.comparison_clock("USTEC", cash_open) == (cash_open, False)
    assert img_contract.comparison_clock("US500", cash_open) == (cash_open, False)
    assert img_contract.comparison_clock("BTCUSD", cash_open) == (cash_open, False)

    # Wednesday 25 Nov 2026 22:00Z = 5:00 PM ET (US cash closed -> 16:00 ET = 21:00Z)
    after_hours = datetime(2026, 11, 25, 22, 0, tzinfo=timezone.utc)
    expected_close = datetime(2026, 11, 25, 21, 0, tzinfo=timezone.utc)
    assert img_contract.comparison_clock("USTEC", after_hours) == (expected_close, True)
    assert img_contract.comparison_clock("XAUUSD", after_hours) == (after_hours, False)

    # Saturday 28 Nov 2026 15:00Z (weekend: BTC open; FX/Gold/Oil frozen at Fri 17:00 ET = 22:00Z)
    saturday = datetime(2026, 11, 28, 15, 0, tzinfo=timezone.utc)
    fri_17_et = datetime(2026, 11, 27, 22, 0, tzinfo=timezone.utc)
    assert img_contract.comparison_clock("BTCUSD", saturday) == (saturday, False)
    assert img_contract.comparison_clock("XAUUSD", saturday) == (fri_17_et, True)
    assert img_contract.comparison_clock("EURUSD", saturday) == (fri_17_et, True)


def test_cc463_ustec_refuses_drawn_card_and_off_scale_chart_and_padded_ig(tmp_path):
    now = datetime(2026, 11, 25, 15, 0, tzinfo=timezone.utc)

    def _ustec_message(folder, assets):
        store, rt, coord, msg = message_with(folder, assets)
        intent = json.loads(msg["payload"])
        ctx_path = Path(intent["output_dir"]) / "run_context_v1.json"
        ctx = json.loads(ctx_path.read_bytes())
        ctx["article"]["market_asset"] = "USTEC"
        ctx_path.write_text(json.dumps(ctx), encoding="utf-8")
        return store, rt, coord, msg

    # 1. Wrong type (drawn card) on USTEC -> DEFINITE_NO_WRITE
    drawn_path = tmp_path / "drawn.png"
    Image.new("RGB", (800, 450), "navy").save(drawn_path)
    drawn = {
        "asset_id": "drawn-ustec",
        "path": str(drawn_path),
        "sha256": sha256(drawn_path.read_bytes()).hexdigest(),
        "modality": "source_bound_data_card",
    }
    _, runtime, coordinator, message = _ustec_message(tmp_path / "run-drawn", [drawn])
    coordinator._clock = lambda: now
    res = coordinator._dispatch_message(message, canonical_url=None)
    assert res["status"] == "DEFINITE_NO_WRITE"
    assert res["reason_code"] == "TRADINGVIEW_FIRST_IMAGE_WRONG_TYPE"
    assert runtime.publish_calls == []

    # 2. Off-scale USTEC chart (> 0.15%) -> TRADINGVIEW_PRICE_SCALE_MISMATCH
    snap = {
        "path": str(TV_FIXTURE),
        "sha256": sha256(TV_FIXTURE.read_bytes()).hexdigest(),
        "tv_symbol": tv.SYMBOLS["USTEC"],
        "interval": "240",
        "interval_label": "4h",
        "chart_url": tv.chart_url(tv.SYMBOLS["USTEC"], "240"),
        "page_title": "NDX 25,200.00",
        "captured_at_utc": now.isoformat(),
        "capture_ratio": "16:9",
    }
    bad_quote = {
        "market": "USTEC",
        "instrument": "USTEC",
        "price": 25000.0,
        "quoted_at_utc": now.isoformat(),
        "known_at_utc": now.isoformat(),
        "source_path": "controlled.json",
        "source_sha256": "a" * 64,
        "price_basis": "plan_feed",
    }
    with pytest.raises(img_contract.ImageContractError, match="TRADINGVIEW_PRICE_SCALE_MISMATCH"):
        img_contract.compare_scale("USTEC", snap, bad_quote)

    # 3. Non-4:5 chart on instagram_business -> INSTAGRAM_NATIVE_4X5_CHART_REQUIRED
    good_quote = {**bad_quote, "price": 25200.0}
    bound_snap = img_contract.bind_scale("USTEC", snap, quote=good_quote)
    asset = {
        **tv.snapshot_asset("USTEC", "Nasdaq 100", bound_snap, tmp_path / "media-ig"),
        "article_inclusion": True,
        "canonical_article_media": True,
    }
    _, _, coord_ig, msg_ig = _ustec_message(tmp_path / "run-ig", [asset])
    coord_ig._clock = lambda: now
    intent = json.loads(msg_ig["payload"])
    with pytest.raises(img_contract.ImageContractError, match="INSTAGRAM_NATIVE_4X5_CHART_REQUIRED"):
        img_contract.validate_write(coord_ig, intent, "instagram_business")


def test_cc463_auditor_accepts_ustec_clean_week_and_identifies_ig_4x5(tmp_path):
    auditor = runpy.run_path(str(Path(__file__).parents[1] / "scripts/audit_publication_images_cc463.py"))
    start = datetime(2026, 12, 1, 16, 0, tzinfo=timezone.utc)
    rows = []
    for i in range(8):
        rows.append({
            "schema_version": "contentops.published_images.v1",
            "record_id": f"rec-{i}",
            "piece_id": f"piece-{i}",
            "state": "PUBLISHED",
            "day": (start + timedelta(days=i)).date().isoformat(),
            "published_at_utc": (start + timedelta(days=i)).isoformat(),
            "publication_clock_basis": "OBSERVED_PUBLICATION_CLOCK",
            "market": "USTEC",
            "image_contract": img_contract.POLICY,
            "text_fallback": None,
            "destination": "instagram_business",
            "lead_asset_id": "lead",
            "images": [{"asset_id": "lead", "image_type": "TRADINGVIEW_MARKET_CHART",
                        "sha256": "b" * 64, "width": 1088, "height": 1360}],
        })
    reg = tmp_path / "published_images_v1.jsonl"
    reg.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    day_res = auditor["audit"](reg, "2026-12-01", now=start + timedelta(days=1))
    assert day_res["status"] == "PASS" and day_res["instagram_4x5_dimension_candidates"] == ["rec-0"]
    week_res = auditor["audit_window"](reg, "2026-12-01", now=start + timedelta(days=9))
    assert week_res["status"] == "PASS" and week_res["completed_following_days"] == 7


# ---------------------------------------------------------------------------
# CC-801 + CC-770: AGY_TERMS_BLOCK even if routes file names AGY, and isolated
# restore_contentops.py guard contract verification (zero live touches)
# ---------------------------------------------------------------------------

def test_cc801_agy_terms_block_supersedes_cc798_routes_file_without_starting_agy(tmp_path, monkeypatch):
    def forbid_popen(*a, **k):
        pytest.fail("agy process was started despite AGY_TERMS_BLOCK")

    monkeypatch.setattr(subprocess, "Popen", forbid_popen)
    routes_file = tmp_path / "agy_neo_routes.json"
    routes_file.write_text(json.dumps({"x": answerer.ROUTE_AGY}), encoding="utf-8")
    assert answerer.platform_routes(routes_file)["x"] == answerer.ROUTE_AGY
    runner = answerer.AgyRunner(scratch_root=tmp_path / "scratch")
    assert runner("synthetic publish prompt") == {
        "runner_status": "NOT_STARTED",
        "cause": assist.AGY_TERMS_BLOCK,
    }
    assert light.CODEX_MODEL == "gpt-6.2-sol"


def test_cc770_restore_script_contract_enforces_relaunch_clock_and_keeps_other_suspensions(tmp_path):
    """Test an isolated copy of restore_contentops.py against a synthetic pause folder (never touches A:\\)."""
    live_script = Path(r"A:\Capital Chronicle\Runtime\ContentOps\control\pause-20261123\restore_contentops.py")
    if not live_script.is_file():
        pytest.skip("live pause script absent on this host")

    pause_dir = tmp_path / "pause-test"
    pause_dir.mkdir()
    script_copy = pause_dir / "restore_contentops.py"
    script_copy.write_bytes(live_script.read_bytes())

    routes_file = tmp_path / "suspended_routes.json"
    stop_file = tmp_path / "runner-publisher.stop"
    stop_file.write_text("paused\n", encoding="utf-8")

    (pause_dir / "suspended_routes_before.json").write_text(
        json.dumps({"linkedin": "PRIOR_SUSPENSION"}), encoding="utf-8"
    )
    routes_file.write_text(
        json.dumps({
            "linkedin": "PRIOR_SUSPENSION",
            "x": "JIM_PAUSE_TEST",
            "youtube": "PLATFORM_RESTRICTION_DURING_PAUSE",
        }),
        encoding="utf-8",
    )
    future_resume = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat().replace("+00:00", "Z")
    manifest = {
        "cause": "JIM_PAUSE_TEST",
        "resume_at_utc": future_resume,
        "routes_file": str(routes_file),
        "tasks": [{"name": "Fake-Disabled-Task", "state_before": "Disabled"}],
        "stop_files": [{"path": str(stop_file), "existed_before": False}],
    }
    (pause_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def run(*args):
        return subprocess.run(
            [sys.executable, "-I", "-B", str(script_copy), *args],
            capture_output=True, text=True, timeout=15,
        )

    # 1. Without --relaunch: refuses with exit code 3 (NO_RELAUNCH_FLAG) and leaves stop file intact.
    no_flag = run()
    assert no_flag.returncode == 3 and "NO_RELAUNCH_FLAG" in no_flag.stdout
    assert stop_file.is_file() and not (pause_dir / "restored.json").exists()

    # 2. With --relaunch before resume_at_utc: refuses with exit code 2 (TOO_EARLY).
    too_early = run("--relaunch")
    assert too_early.returncode == 2 and "TOO_EARLY" in too_early.stdout
    assert stop_file.is_file() and not (pause_dir / "restored.json").exists()

    # 3. --dry-run succeeds at any time, preserves pause-period non-pause suspensions, changes nothing on disk.
    dry = run("--dry-run")
    assert dry.returncode == 0
    payload = json.loads(dry.stdout[dry.stdout.index("{"):])
    assert payload["dry_run"] is True
    assert payload["routes"]["restored"] == {
        "linkedin": "PRIOR_SUSPENSION",
        "youtube": "PLATFORM_RESTRICTION_DURING_PAUSE",
    }
    assert "x" not in payload["routes"]["restored"]
    assert payload["stop_files"][str(stop_file)] == "REMOVED"
    assert stop_file.is_file() and not (pause_dir / "restored.json").exists()

    # 4. If restored.json already exists: idempotent exit code 0 (ALREADY_RESTORED).
    (pause_dir / "restored.json").write_text("{}", encoding="utf-8")
    already = run("--relaunch")
    assert already.returncode == 0 and "ALREADY_RESTORED" in already.stdout
